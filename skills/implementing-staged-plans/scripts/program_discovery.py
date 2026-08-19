#!/usr/bin/env python3
"""Discover repository-backed implementation programs without modifying them."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path, PurePosixPath
from typing import Callable

from program_activation import (
    _build_plan_candidate,
    _without_owned_program_paths,
    build_activation_transaction,
)
from program_authority import (
    APPROVED_VALIDATION_MODE,
    NEW_PROGRAM_MANIFEST_SCHEMA,
    PROPOSAL_VALIDATION_MODE,
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
    validate_program_authority,
)
from program_launch import (
    render_program_launch_prompt,
    validate_submitted_program_launch_prompt,
)
from program_review import build_review_preparation
from diff_disposition import build_diff_acceptance_candidate
from program_closure import (
    build_closure_command_candidate,
    build_closure_preparation,
)
from repository_preparation import inspect_repository
from state_authority import (
    INCREMENT_TRANSITIONS,
    STATUS_SCHEMA,
    WORKSPACE_SCHEMA,
    RepositoryObservation,
    validate_state_authority,
)


RESUMABLE_PROGRAM_STATES = frozenset({"active", "blocked"})
SUPPORTED_PROGRAM_STATES = frozenset({*RESUMABLE_PROGRAM_STATES, "closed"})
PLAN_A_DISCOVERY_DISPOSITIONS = frozenset(
    {
        "new-program-bootstrap-ready",
        "proposal-publication-retry-ready",
        "program-activation-ready",
        "program-activation-retry-ready",
        "plan-preparation-retry-ready",
        "plan-materialization-retry-ready",
        "review-preparation-retry-ready",
        "increment-acceptance-retry-ready",
        "closure-preparation-retry-ready",
        "closure-approval-retry-ready",
        "resume",
        "accepted-stop",
        "closure-approval-ready",
        "terminal-programs",
    }
)
PLAN_A_ROUTE_DETAILS = {
    "proposal-publication-retry-ready": (
        None,
        "Resubmit the same proposal-publication request to adopt the valid prefix.",
        False,
    ),
    "proposal-publication-recovery-required": (
        "proposal-publication-prefix-recovery",
        "Preserve the publication prefix and resolve its divergence before retrying.",
        True,
    ),
    "program-activation-ready": (
        None,
        "Render and submit the exact program-launch prompt.",
        False,
    ),
    "program-activation-retry-ready": (
        None,
        "Resubmit the same exact program-launch prompt to adopt the valid prefix.",
        False,
    ),
    "program-activation-recovery-required": (
        "activation-prefix-recovery",
        "Preserve the activation prefix and resolve its divergence before retrying.",
        True,
    ),
    "plan-preparation-retry-ready": (
        None,
        "Resubmit the same exact plan-preparation operation to adopt the valid prefix.",
        False,
    ),
    "plan-materialization-retry-ready": (
        None,
        "Resubmit the same exact plan-materialization operation to adopt the valid prefix.",
        False,
    ),
    "plan-preparation-recovery-required": (
        "plan-preparation-prefix-recovery",
        "Preserve the exact-plan preparation prefix and resolve its divergence before retrying.",
        True,
    ),
    "plan-materialization-recovery-required": (
        "plan-materialization-prefix-recovery",
        "Preserve the exact-plan materialization prefix and resolve its divergence before retrying.",
        True,
    ),
    "review-preparation-retry-ready": (
        None,
        "Resubmit the same exact review-preparation operation to adopt the valid prefix.",
        False,
    ),
    "review-preparation-recovery-required": (
        "review-preparation-prefix-recovery",
        "Preserve the review prefix and resolve its divergence before retrying.",
        True,
    ),
    "increment-acceptance-retry-ready": (
        None,
        "Resubmit the same exact increment-acceptance prompt to adopt the valid prefix.",
        False,
    ),
    "increment-acceptance-recovery-required": (
        "increment-acceptance-prefix-recovery",
        "Preserve the diff-acceptance prefix and resolve its divergence before retrying.",
        True,
    ),
    "closure-preparation-retry-ready": (
        None,
        "Resubmit the same exact closure-preparation operation to adopt the valid prefix.",
        False,
    ),
    "closure-approval-retry-ready": (
        None,
        "Resubmit the same exact closure-approval prompt to adopt the valid prefix.",
        False,
    ),
    "closure-preparation-recovery-required": (
        "closure-preparation-prefix-recovery",
        "Preserve the closure preparation prefix and resolve its divergence before retrying.",
        True,
    ),
    "closure-approval-recovery-required": (
        "closure-approval-prefix-recovery",
        "Preserve the closure approval prefix and resolve its divergence before retrying.",
        True,
    ),
    "execution-transition-recovery-required": (
        "execution-transition-recovery",
        "Preserve the execution status and resolve its divergence before retrying.",
        True,
    ),
    "resume": (None, "Resume from the selected manifest and persisted state.", False),
    "accepted-stop": (
        "later-continuation-or-closure-intent",
        "Stop after acceptance; a later prompt must choose continuation or closure.",
        True,
    ),
    "closure-approval-ready": (
        "program-closure-approval",
        "Present the exact closure approval prompt and wait for direct approval.",
        True,
    ),
    "continuation-recovery-required": (
        "plan-b-continuation-recovery",
        "Preserve the successor prefix and use the Plan B continuation recovery workflow.",
        True,
    ),
    "blocked-recovery-required": (
        "plan-b-blocked-recovery",
        "Preserve the blocked prefix and use the Plan B blocked recovery workflow.",
        True,
    ),
    "legacy-rollover-upgrade-required": (
        "legacy-rollover-upgrade",
        "Stop before successor writes; the accepted legacy program requires an explicit upgrade workflow.",
        True,
    ),
}
NEW_PROGRAM_STATES = frozenset(
    {
        "awaiting-program-approval",
        "active",
        "blocked",
        "awaiting-closure-approval",
        "closed",
        "superseded",
    }
)
SUPPORTED_PROGRAM_OPERATIONS = frozenset({"create", "activate", "continue"})
UNSUPPORTED_LIVE_PROGRAM_MUTATIONS = frozenset({"revise", "supersede", "cancel"})


@dataclass(frozen=True)
class ProgramCandidate:
    manifest_path: str
    program_root: str
    program_id: str
    program_revision: int
    program_state: str
    status_path: str
    status_sha256: str
    status_sequence: int


@dataclass(frozen=True)
class ResumeExpectations:
    manifest_path: str
    manifest_sha256: str
    status_path: str
    status_sha256: str
    status_sequence: int
    program_id: str
    program_revision: int
    program_state: str
    source_id: str
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    approval_mode: str
    workspace_path: str
    workspace_branch: str
    workspace_base_commit: str
    workspace_head_commit: str
    staged_paths: tuple[str, ...]
    modified_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]
    conflicted_paths: tuple[str, ...]
    active_git_operation: str | None
    current_increment_id: str
    current_increment_state: str
    brief_path: str
    brief_sha256: str
    exact_file_plan_sha256: str


@dataclass(frozen=True)
class ProgramDiscoveryResult:
    disposition: str
    required_input: str | None
    source_plan_path: str | None
    candidates: tuple[ProgramCandidate, ...]
    closed_programs: tuple[ProgramCandidate, ...]
    resume_expectations: ResumeExpectations | None
    issues: tuple[str, ...]
    next_action: str
    stop_required: bool


def classify_requested_program_operation(
    discovery: ProgramDiscoveryResult,
    requested_operation: str,
) -> ProgramDiscoveryResult:
    """Quarantine unsupported live mutations without changing repository state."""
    if not isinstance(discovery, ProgramDiscoveryResult):
        raise TypeError("discovery must be a ProgramDiscoveryResult")
    if requested_operation in SUPPORTED_PROGRAM_OPERATIONS:
        return discovery
    if (
        requested_operation in {"revise", "supersede"}
        and discovery.candidates
    ):
        disposition = "program-revision-workflow-required"
        next_action = (
            "Stop. A typed program-revision workflow is required before changing "
            "or superseding a live program."
        )
    else:
        disposition = "unsupported-program-mutation"
        next_action = "Stop. This program mutation is not supported by Plan A."
    return replace(
        discovery,
        disposition=disposition,
        required_input=None,
        issues=(*discovery.issues, disposition),
        next_action=next_action,
        stop_required=True,
    )


ObservationProvider = Callable[[Path, str], RepositoryObservation]


def _canonical_json_line(value: dict[str, object]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _exact_activation_prefix(
    root: Path,
    manifest: dict[str, object],
    ledgers: dict[str, list[dict[str, object]]],
) -> bool:
    """Rebuild the launch transaction and compare every persisted prefix byte."""
    try:
        prompt = render_program_launch_prompt(root)
        command = validate_submitted_program_launch_prompt(root, prompt)
        workspace = command["workspace"]
        repository = workspace["repository"]
        selected = workspace["implementation_workspace"]
        existing = workspace["pre_existing_work_at_selection"]
        observation = RepositoryObservation(
            repository=repository["identity"],
            path=selected["path"],
            branch=selected["branch"],
            base_commit=selected["base_commit"],
            head_commit=selected["head_commit_at_selection"],
            staged_paths=tuple(existing["staged_paths"]),
            modified_paths=tuple(existing["modified_paths"]),
            untracked_paths=tuple(existing["untracked_paths"]),
            conflicted_paths=tuple(existing["conflicted_paths"]),
            active_git_operation=existing["active_git_operation"],
        )
        program_approval, workspace_approval, grant, _status = (
            build_activation_transaction(command, prompt, observation)
        )
        logical_roles = manifest["logical_roles"]
        approvals_path, approval_issues = resolve_managed_path(
            root, logical_roles["approvals"], role="logical role approvals"
        )
        grants_path, grant_issues = resolve_managed_path(
            root,
            logical_roles["increment_grants"],
            role="logical role increment_grants",
        )
        if approval_issues or grant_issues or approvals_path is None or grants_path is None:
            return False
        approval_prefixes = {
            b"",
            _canonical_json_line(program_approval),
            _canonical_json_line(program_approval)
            + _canonical_json_line(workspace_approval),
        }
        grant_prefixes = {b"", _canonical_json_line(grant)}
        approval_bytes = approvals_path.read_bytes()
        grant_bytes = grants_path.read_bytes()
        return (
            approval_bytes in approval_prefixes
            and grant_bytes in grant_prefixes
            and (
                not grant_bytes
                or approval_bytes
                == _canonical_json_line(program_approval)
                + _canonical_json_line(workspace_approval)
            )
            and not ledgers.get("action_authorizations")
        )
    except (KeyError, OSError, TypeError, ValueError):
        return False


def _inspect_transaction_files(
    root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
) -> tuple[dict[str, bool], list[str]]:
    """Inspect allocated future files without inventing or modifying any path."""
    increment_id = status.get("current_increment_id")
    if (
        not isinstance(increment_id, str)
        or not increment_id
        or "/" in increment_id
        or "\\" in increment_id
        or increment_id in {".", ".."}
    ):
        return {}, ["status current_increment_id must be one safe path segment"]

    allocated: list[tuple[str, str]] = []
    increment_storage = manifest.get("increment_storage")
    closure_storage = manifest.get("closure_storage")
    if not isinstance(increment_storage, dict) or not isinstance(closure_storage, dict):
        return {}, ["new-program storage descriptors must be objects"]
    increment_root = increment_storage.get("root")
    closure_root = closure_storage.get("root")
    if not isinstance(increment_root, str) or not isinstance(closure_root, str):
        return {}, ["new-program storage roots must be strings"]
    for field in (
        "brief_filename",
        "exact_file_plan_filename",
        "execution_baseline_filename",
        "review_evidence_filename",
        "review_packet_filename",
        "handoff_filename",
    ):
        filename = increment_storage.get(field)
        if isinstance(filename, str):
            allocated.append(
                (field, f"{increment_root}/{increment_id}/{filename}")
            )
    for field in ("reconciliation_filename", "packet_filename"):
        filename = closure_storage.get(field)
        if isinstance(filename, str):
            allocated.append((field, f"{closure_root}/{filename}"))

    presence: dict[str, bool] = {}
    issues: list[str] = []
    for field, relative_path in allocated:
        path, path_issues = resolve_managed_path(
            root,
            relative_path,
            role=f"allocated transaction file {field}",
            require_file=False,
        )
        issues.extend(path_issues)
        if path is None:
            continue
        exists = path.exists()
        presence[field] = exists
        if not exists:
            continue
        if path.is_symlink() or not path.is_file():
            issues.append(f"allocated transaction file {field} must be a regular file")
            continue
        if path.suffix == ".json":
            _value, json_issues = load_json_object(path)
            issues.extend(json_issues)
        else:
            try:
                if not path.read_bytes():
                    issues.append(f"allocated transaction file {field} must not be empty")
            except OSError as error:
                issues.append(f"allocated transaction file {field} could not be read: {error}")

    if presence.get("exact_file_plan_filename"):
        plan_path = next(
            (
                root / relative_path
                for field, relative_path in allocated
                if field == "exact_file_plan_filename"
            ),
            None,
        )
        expected_digest = status.get("pending_exact_file_plan_sha256")
        if expected_digest is None:
            expected_digest = status.get("approved_exact_file_plan_sha256")
        if (
            plan_path is not None
            and plan_path.is_file()
            and not plan_path.is_symlink()
            and isinstance(expected_digest, str)
            and sha256_file(plan_path) != expected_digest
        ):
            issues.append("exact-file plan prefix digest does not match controlling status")
    return presence, sorted(set(issues))


def _exact_plan_prefix_disposition(
    root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    ledgers: dict[str, list[dict[str, object]]],
    presence: dict[str, bool],
) -> str | None:
    """Classify only byte-exact current-increment plan transaction prefixes."""
    state = status.get("current_increment_state")
    if state not in {"preparing", "awaiting-plan-approval", "authorized"}:
        return None
    plan_present = presence.get("exact_file_plan_filename", False)
    baseline_present = presence.get("execution_baseline_filename", False)
    plan_approvals = [
        record
        for record in ledgers.get("approvals", [])
        if record.get("type") == "exact-file-plan-approval"
    ]
    actions = ledgers.get("action_authorizations", [])
    material_prefix = bool(plan_approvals or baseline_present or actions)
    recovery = (
        "plan-materialization-recovery-required"
        if material_prefix
        else "plan-preparation-recovery-required"
    )
    if not plan_present:
        return recovery if material_prefix or state != "preparing" else None
    try:
        storage = manifest["increment_storage"]
        plan_path, plan_path_issues = resolve_managed_path(
            root,
            f"{storage['root']}/{status['current_increment_id']}/"
            f"{storage['exact_file_plan_filename']}",
            role="status-current exact-file plan",
        )
        if plan_path is None:
            return recovery
        roles = manifest["logical_roles"]
        workspace_path, workspace_path_issues = resolve_managed_path(
            root, roles["workspace"], role="logical role workspace"
        )
        if workspace_path is None:
            return recovery
        workspace, workspace_issues = load_json_object(workspace_path)
        if workspace is None:
            return recovery
        selected = workspace["implementation_workspace"]
        inspection = inspect_repository(Path(selected["path"]), selected["base_commit"])
        observation = _without_owned_program_paths(root, inspection.observation)
        candidate = _build_plan_candidate(root, plan_path.read_bytes(), observation)
    except (KeyError, OSError, TypeError, ValueError):
        return recovery
    if plan_path_issues or workspace_path_issues or workspace_issues:
        return recovery
    expected_approvals = (
        []
        if candidate.plan_approval_record is None
        else [candidate.plan_approval_record]
    )
    if plan_approvals not in ([], expected_approvals):
        return "plan-materialization-recovery-required"
    if actions not in ([], [candidate.action_record]):
        return "plan-materialization-recovery-required"
    if baseline_present:
        try:
            if candidate.baseline_path.read_bytes() != candidate.baseline_bytes:
                return "plan-materialization-recovery-required"
        except OSError:
            return "plan-materialization-recovery-required"
    if actions and not baseline_present:
        return "plan-materialization-recovery-required"
    if candidate.plan_approval_record is not None and (
        baseline_present or actions
    ) and not plan_approvals:
        return "plan-materialization-recovery-required"
    if candidate.plan_approval_record is None and plan_approvals:
        return "plan-materialization-recovery-required"
    if state == "authorized":
        if not baseline_present or actions != [candidate.action_record]:
            return "plan-materialization-recovery-required"
        if candidate.plan_approval_record is not None and plan_approvals != expected_approvals:
            return "plan-materialization-recovery-required"
        if _canonical_json_bytes(status) != _canonical_json_bytes(
            candidate.authorized_status
        ):
            return "plan-materialization-recovery-required"
        return None
    if state == "preparing" and not material_prefix:
        return "plan-preparation-retry-ready"
    if state == "awaiting-plan-approval" and not material_prefix:
        if (
            candidate.awaiting_status is None
            or _canonical_json_bytes(status)
            != _canonical_json_bytes(candidate.awaiting_status)
        ):
            return "plan-preparation-recovery-required"
        return "plan-preparation-retry-ready"
    return "plan-materialization-retry-ready"


def _exact_review_prefix_disposition(
    root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    presence: dict[str, bool],
) -> str | None:
    state = status.get("current_increment_state")
    evidence_present = presence.get("review_evidence_filename", False)
    packet_present = presence.get("review_packet_filename", False)
    if state not in {"reviewing", "verified", "awaiting-diff-approval"}:
        return None
    if state == "reviewing" and not evidence_present and not packet_present:
        return None
    try:
        roles = manifest["logical_roles"]
        workspace_path, workspace_path_issues = resolve_managed_path(
            root, roles["workspace"], role="logical role workspace"
        )
        if workspace_path is None:
            return "review-preparation-recovery-required"
        workspace, workspace_issues = load_json_object(workspace_path)
        if workspace is None or workspace_path_issues or workspace_issues:
            return "review-preparation-recovery-required"
        selected = workspace["implementation_workspace"]
        observation = inspect_repository(
            Path(selected["path"]), selected["base_commit"]
        ).observation
        candidate = build_review_preparation(root, observation)
    except (KeyError, OSError, TypeError, ValueError):
        return "review-preparation-recovery-required"
    if packet_present and not evidence_present:
        return "review-preparation-recovery-required"
    if evidence_present and candidate.evidence_path.read_bytes() != candidate.evidence_bytes:
        return "review-preparation-recovery-required"
    if packet_present and candidate.packet_path.read_bytes() != candidate.packet_bytes:
        return "review-preparation-recovery-required"
    if state == "reviewing":
        return "review-preparation-retry-ready"
    status_bytes = _canonical_json_bytes(status)
    if state == "verified":
        if (
            not evidence_present
            or not packet_present
            or status_bytes != candidate.verified_status_bytes
        ):
            return "review-preparation-recovery-required"
        return "review-preparation-retry-ready"
    if (
        not evidence_present
        or not packet_present
        or status_bytes != candidate.awaiting_diff_status_bytes
    ):
        return "review-preparation-recovery-required"
    return "resume"


def _exact_acceptance_prefix_disposition(
    root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    ledgers: dict[str, list[dict[str, object]]],
) -> str | None:
    state = status.get("current_increment_state")
    if (
        status.get("program_state") != "active"
        or state not in {"awaiting-diff-approval", "accepted"}
    ):
        return None
    approvals = [
        record
        for record in ledgers.get("approvals", [])
        if record.get("type") == "increment-diff-approval"
    ]
    if state == "awaiting-diff-approval" and not approvals:
        return None
    try:
        roles = manifest["logical_roles"]
        workspace_path, workspace_path_issues = resolve_managed_path(
            root, roles["workspace"], role="logical role workspace"
        )
        if workspace_path is None:
            return "increment-acceptance-recovery-required"
        workspace, workspace_issues = load_json_object(workspace_path)
        if workspace is None or workspace_path_issues or workspace_issues:
            return "increment-acceptance-recovery-required"
        selected = workspace["implementation_workspace"]
        observation = inspect_repository(
            Path(selected["path"]), selected["base_commit"]
        ).observation
        candidate = build_diff_acceptance_candidate(root, observation)
    except (KeyError, OSError, TypeError, ValueError):
        return "increment-acceptance-recovery-required"
    if approvals != [candidate.approval_record]:
        return "increment-acceptance-recovery-required"
    if state == "awaiting-diff-approval":
        return "increment-acceptance-retry-ready"
    if _canonical_json_bytes(status) != candidate.accepted_status_bytes:
        return "increment-acceptance-recovery-required"
    return "accepted-stop"


def _exact_closure_prefix_disposition(
    root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    ledgers: dict[str, list[dict[str, object]]],
    presence: dict[str, bool],
) -> str | None:
    """Classify only byte-exact closure preparation and approval prefixes."""
    program_state = status.get("program_state")
    increment_state = status.get("current_increment_state")
    reconciliation_present = presence.get("reconciliation_filename", False)
    packet_present = presence.get("packet_filename", False)
    closure_approvals = [
        record
        for record in ledgers.get("approvals", [])
        if record.get("type") == "program-closure-approval"
    ]
    if program_state == "active" and increment_state == "accepted":
        disposition = status.get("diff_disposition_binding")
        if (
            not isinstance(disposition, dict)
            or disposition.get("schema_version")
            != "implementation-diff-disposition-binding/v1"
            or not isinstance(disposition.get("base_seed_sha256"), str)
        ):
            return None
        if not reconciliation_present and not packet_present and not closure_approvals:
            return None
        recovery = "closure-preparation-recovery-required"
        if closure_approvals:
            return recovery
        try:
            roles = manifest["logical_roles"]
            workspace_path, workspace_path_issues = resolve_managed_path(
                root, roles["workspace"], role="logical role workspace"
            )
            if workspace_path is None or workspace_path_issues:
                return recovery
            workspace, workspace_issues = load_json_object(workspace_path)
            if workspace is None or workspace_issues:
                return recovery
            selected = workspace["implementation_workspace"]
            observation = inspect_repository(
                Path(selected["path"]), selected["base_commit"]
            ).observation
            prepared = build_closure_preparation(root, observation)
        except (KeyError, OSError, TypeError, ValueError):
            return recovery
        if packet_present and not reconciliation_present:
            return recovery
        if (
            reconciliation_present
            and prepared.reconciliation_path.read_bytes()
            != prepared.reconciliation_bytes
        ):
            return recovery
        if packet_present and prepared.packet_path.read_bytes() != prepared.packet_bytes:
            return recovery
        return "closure-preparation-retry-ready"

    if program_state not in {"awaiting-closure-approval", "closed"}:
        return None
    preparation = status.get("closure_preparation_binding")
    if (
        not isinstance(preparation, dict)
        or preparation.get("schema_version")
        != "implementation-closure-preparation/v1"
    ):
        return None
    recovery = (
        "closure-approval-recovery-required"
        if program_state == "closed" or closure_approvals
        else "closure-preparation-recovery-required"
    )
    if not reconciliation_present or not packet_present:
        return recovery
    try:
        roles = manifest["logical_roles"]
        workspace_path, workspace_path_issues = resolve_managed_path(
            root, roles["workspace"], role="logical role workspace"
        )
        if workspace_path is None or workspace_path_issues:
            return recovery
        workspace, workspace_issues = load_json_object(workspace_path)
        if workspace is None or workspace_issues:
            return recovery
        selected = workspace["implementation_workspace"]
        observation = inspect_repository(
            Path(selected["path"]), selected["base_commit"]
        ).observation
        command = build_closure_command_candidate(root, observation)
    except (KeyError, OSError, TypeError, ValueError):
        return recovery
    if closure_approvals not in ([], [command.approval_record]):
        return "closure-approval-recovery-required"
    if program_state == "awaiting-closure-approval":
        return (
            "closure-approval-retry-ready"
            if closure_approvals
            else "closure-approval-ready"
        )
    if closure_approvals != [command.approval_record]:
        return "closure-approval-recovery-required"
    if _canonical_json_bytes(status) != command.closed_status_bytes:
        return "closure-approval-recovery-required"
    return "terminal-programs"


def _load_new_candidate(
    repository: Path,
    manifest_path: Path,
) -> tuple[ProgramCandidate | None, str | None, tuple[str, ...]]:
    """Inspect status and typed prefixes before strict v2 authority validation."""
    display_path = _display_path(repository, manifest_path)
    issues = _path_issues(repository, manifest_path, f"manifest {display_path}")
    if issues:
        return None, None, tuple(sorted(set(issues)))
    root = manifest_path.parent
    manifest, manifest_issues = load_json_object(manifest_path)
    if manifest is None:
        return None, None, tuple(
            f"{display_path}: {issue}" for issue in manifest_issues
        )
    roles = manifest.get("logical_roles")
    if not isinstance(roles, dict):
        return None, None, (f"{display_path}: manifest logical_roles must be an object",)
    status_path, status_path_issues = resolve_managed_path(
        root, roles.get("status"), role="logical role status"
    )
    if status_path is None:
        return None, None, tuple(
            f"{display_path}: {issue}" for issue in status_path_issues
        )
    status, status_issues = load_json_object(status_path)
    if status is None:
        return None, None, tuple(f"{display_path}: {issue}" for issue in status_issues)

    program_state = status.get("program_state")
    increment_state = status.get("current_increment_state")
    sequence = status.get("state_sequence")
    if status.get("schema_version") != "implementation-program-status/v2":
        issues.append("unsupported new-program status schema")
    if program_state not in NEW_PROGRAM_STATES:
        issues.append(f"unsupported controlling program state {program_state!r}")
    if increment_state not in INCREMENT_TRANSITIONS:
        issues.append(f"unknown increment state {increment_state!r}")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        issues.append("status state_sequence is invalid")
    for field in ("program_id", "program_revision"):
        if status.get(field) != manifest.get(field):
            issues.append(f"status {field} does not match manifest")
    if status.get("approval_mode") != manifest.get("approval_mode"):
        issues.append("status approval mode mismatch")
    if status.get("source_binding") != manifest.get("source_binding"):
        issues.append("status source binding mismatch")
    manifest_program = manifest.get("program_binding")
    status_program = status.get("program_binding")
    if not isinstance(manifest_program, dict) or not isinstance(status_program, dict):
        issues.append("program binding must be an object")
    elif status_program.get("sha256") != manifest_program.get("sha256"):
        issues.append("status program digest mismatch")

    ledgers: dict[str, list[dict[str, object]]] = {}
    for role in (
        "approvals",
        "action_authorizations",
        "increment_grants",
        "rollovers",
        "block_resolutions",
    ):
        path, path_issues = resolve_managed_path(
            root, roles.get(role), role=f"logical role {role}"
        )
        issues.extend(path_issues)
        if path is None:
            continue
        records, record_issues = load_json_lines(path)
        issues.extend(record_issues)
        if records is not None:
            ledgers[role] = records
    if issues:
        return None, None, tuple(
            f"{display_path}: {issue}" for issue in sorted(set(issues))
        )

    candidate = ProgramCandidate(
        manifest_path=display_path,
        program_root=_relative_path(repository, root),
        program_id=str(manifest["program_id"]),
        program_revision=int(manifest["program_revision"]),
        program_state=str(program_state),
        status_path=_relative_path(repository, status_path),
        status_sha256=sha256_file(status_path),
        status_sequence=int(sequence),
    )

    has_rollover_prefix = bool(ledgers.get("rollovers"))
    has_blocked_prefix = bool(ledgers.get("block_resolutions")) or program_state == "blocked"

    if program_state == "awaiting-program-approval":
        if has_rollover_prefix or has_blocked_prefix:
            return candidate, None, (
                f"{display_path}: proposal contains a deferred lifecycle prefix",
            )
        if not _exact_activation_prefix(root, manifest, ledgers):
            return candidate, "program-activation-recovery-required", ()
        approvals = ledgers.get("approvals", [])
        grants = ledgers.get("increment_grants", [])
        actions = ledgers.get("action_authorizations", [])
        approval_types = tuple(record.get("type") for record in approvals)
        ordered_prefix = (
            not actions
            and len(grants) <= 1
            and approval_types
            in (
                (),
                ("program-approval",),
                ("program-approval", "workspace-selection-approval"),
            )
            and (not grants or len(approvals) == 2)
            and (
                not grants
                or grants[0].get("schema_version")
                == "implementation-increment-grant/v1"
            )
        )
        if not ordered_prefix:
            return candidate, None, (
                f"{display_path}: activation records are not an ordered transaction prefix",
            )
        has_activation_prefix = bool(approvals or grants)
        mode = APPROVED_VALIDATION_MODE if approvals else PROPOSAL_VALIDATION_MODE
        authority_issues = validate_program_authority(root, validation_mode=mode)
        if authority_issues:
            return candidate, None, tuple(
                f"{display_path}: {issue}" for issue in authority_issues
            )
        if sequence != 0 or increment_state != "not-started":
            return candidate, None, (
                f"{display_path}: proposal status is not the sequence-zero initial state",
            )
        return (
            candidate,
            "program-activation-retry-ready"
            if has_activation_prefix
            else "program-activation-ready",
            (),
        )

    authority_issues = validate_program_authority(
        root, validation_mode=APPROVED_VALIDATION_MODE
    )
    if authority_issues:
        return candidate, None, tuple(
            f"{display_path}: {issue}" for issue in authority_issues
        )
    if has_rollover_prefix:
        return candidate, "continuation-recovery-required", ()
    if has_blocked_prefix:
        return candidate, "blocked-recovery-required", ()
    transaction_files, transaction_issues = _inspect_transaction_files(
        root, manifest, status
    )
    plan_prefix_disposition = _exact_plan_prefix_disposition(
        root, manifest, status, ledgers, transaction_files
    )
    if plan_prefix_disposition is not None:
        return candidate, plan_prefix_disposition, ()
    closure_prefix_disposition = _exact_closure_prefix_disposition(
        root, manifest, status, ledgers, transaction_files
    )
    if closure_prefix_disposition is not None:
        return candidate, closure_prefix_disposition, ()
    acceptance_prefix_disposition = _exact_acceptance_prefix_disposition(
        root, manifest, status, ledgers
    )
    if acceptance_prefix_disposition is not None:
        return candidate, acceptance_prefix_disposition, ()
    review_prefix_disposition = _exact_review_prefix_disposition(
        root, manifest, status, transaction_files
    )
    if review_prefix_disposition is not None:
        return candidate, review_prefix_disposition, ()
    if transaction_issues:
        return candidate, None, tuple(
            f"{display_path}: {issue}" for issue in transaction_issues
        )

    try:
        workspace_path, workspace_path_issues = resolve_managed_path(
            root, roles.get("workspace"), role="logical role workspace"
        )
        if workspace_path is None or workspace_path_issues:
            raise ValueError("workspace binding is unavailable")
        workspace, workspace_issues = load_json_object(workspace_path)
        if workspace is None or workspace_issues:
            raise ValueError("workspace binding is invalid")
        selected = workspace["implementation_workspace"]
        inspection = inspect_repository(
            Path(selected["path"]), selected["base_commit"]
        )
        fresh_observation = _without_owned_program_paths(
            root, inspection.observation
        )
        state_issues = validate_state_authority(root, fresh_observation)
    except (KeyError, OSError, TypeError, ValueError) as error:
        return candidate, None, (
            f"{display_path}: fresh state validation failed: {error}",
        )
    if state_issues:
        state_issue_set = set(state_issues)
        recovery_route = None
        if (program_state, increment_state) == ("active", "preparing") and all(
            "activation" in issue or "status-current increment grant" in issue
            for issue in state_issue_set
        ):
            recovery_route = "program-activation-recovery-required"
        elif (program_state, increment_state) == ("active", "authorized") and all(
            "plan" in issue or "execution authorization" in issue
            for issue in state_issue_set
        ):
            recovery_route = "plan-materialization-recovery-required"
        elif (program_state, increment_state) in {
            ("active", "implementing"),
            ("active", "reviewing"),
        } and state_issue_set <= {
            "execution transition binding is invalid",
            "reviewed product delta differs from its status binding",
        }:
            recovery_route = "execution-transition-recovery-required"
        if recovery_route is not None:
            return candidate, recovery_route, ()
        return candidate, None, tuple(
            f"{display_path}: {issue}" for issue in state_issues
        )

    plan_present = transaction_files.get("exact_file_plan_filename", False)
    baseline_present = transaction_files.get("execution_baseline_filename", False)
    review_prefix = any(
        transaction_files.get(field, False)
        for field in ("review_evidence_filename", "review_packet_filename")
    )
    closure_prefix = any(
        transaction_files.get(field, False)
        for field in ("reconciliation_filename", "packet_filename")
    )
    approval_types = tuple(
        record.get("type") for record in ledgers.get("approvals", [])
    )
    action_prefix = bool(ledgers.get("action_authorizations"))

    if program_state in {"closed", "superseded"}:
        return candidate, "terminal-programs", ()
    if program_state == "awaiting-closure-approval":
        closure_approvals = [
            record
            for record in ledgers.get("approvals", [])
            if record.get("type") == "program-closure-approval"
        ]
        return (
            candidate,
            "closure-approval-retry-ready"
            if closure_approvals
            else "closure-approval-ready",
            (),
        )
    if closure_prefix:
        if increment_state != "accepted":
            return candidate, None, (
                f"{display_path}: closure prefix is not controlled by accepted status",
            )
        return candidate, "closure-preparation-retry-ready", ()
    if review_prefix:
        if increment_state not in {
            "reviewing",
            "verified",
            "awaiting-diff-approval",
        }:
            return candidate, None, (
                f"{display_path}: review prefix is not controlled by reviewing or verified status",
            )
        return candidate, "review-preparation-retry-ready", ()
    if increment_state == "awaiting-diff-approval" and (
        "increment-diff-approval" in approval_types
    ):
        return candidate, "increment-acceptance-retry-ready", ()
    if increment_state == "accepted":
        binding = status.get("diff_disposition_binding")
        if (
            isinstance(binding, dict)
            and binding.get("schema_version")
            == "implementation-diff-disposition-binding/v1"
            and binding.get("decision") == "accept-stop"
        ):
            return candidate, "accepted-stop", ()
        return candidate, "increment-acceptance-retry-ready", ()
    if increment_state == "verified":
        return candidate, "review-preparation-retry-ready", ()
    if increment_state in {
        "not-started",
        "preparing",
        "awaiting-plan-approval",
        "authorized",
        "implementing",
        "reviewing",
        "awaiting-diff-approval",
        "change-requested",
        "remediating",
    }:
        return candidate, "resume", ()
    return candidate, None, (
        f"{display_path}: unsupported Plan A state combination",
    )


def validate_resume_evidence(
    observed: ResumeExpectations,
    expected: ResumeExpectations,
) -> list[str]:
    """Compare submitted resume evidence with independently discovered expectations."""
    if not isinstance(observed, ResumeExpectations) or not isinstance(
        expected, ResumeExpectations
    ):
        return ["resume evidence and expectations must use ResumeExpectations"]
    return [
        f"resume {field.name} mismatch"
        for field in fields(ResumeExpectations)
        if getattr(observed, field.name) != getattr(expected, field.name)
    ]


def _default_observation_provider(
    workspace_path: Path, base_commit: str
) -> RepositoryObservation:
    return inspect_repository(workspace_path, base_commit).observation


def _relative_path(repository: Path, path: Path) -> str:
    return path.relative_to(repository).as_posix()


def _display_path(repository: Path, path: Path) -> str:
    try:
        return _relative_path(repository, path)
    except ValueError:
        return path.as_posix()


def _absolute_input_path(repository: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = repository / path
    return Path(os.path.abspath(path))


def _safe_owner_inventory_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        return None
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    return value


def _publication_tree_issue(
    root: Path,
    expected: dict[str, str],
    owner_bytes: bytes,
) -> str | None:
    if root.is_symlink() or not root.is_dir():
        return "publication prefix root must be a regular non-symlink directory"
    present: set[str] = set()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            return f"publication prefix contains an unsafe entry: {relative}"
        if path.is_file():
            present.add(relative)
    allowed = {*expected, ".publication-owner.json"}
    unexpected = present.difference(allowed)
    if unexpected:
        return "publication prefix contains unexpected paths: " + ", ".join(
            sorted(unexpected)
        )
    owner_path = root / ".publication-owner.json"
    if owner_path.is_symlink() or not owner_path.is_file():
        return "publication owner receipt is missing"
    if owner_path.read_bytes() != owner_bytes:
        return "publication owner receipt differs"
    for relative in sorted(present.difference({".publication-owner.json"})):
        if sha256_file(root / relative) != expected[relative]:
            return f"publication prefix digest differs: {relative}"
    return None


def _bootstrap_prefix_disposition(repository: Path) -> tuple[str | None, tuple[str, ...]]:
    staging_roots = tuple(
        path
        for path in sorted(repository.glob(".implementation-program-*"))
        if path.name.startswith(".implementation-program-")
    )
    if not staging_roots:
        return None, ()
    if len(staging_roots) != 1:
        return (
            "proposal-publication-recovery-required",
            ("multiple proposal-publication staging roots require recovery",),
        )
    staging = staging_roots[0]
    owner_path = staging / ".publication-owner.json"
    owner, owner_issues = load_json_object(owner_path)
    if owner is None:
        return "proposal-publication-recovery-required", tuple(owner_issues)
    canonical_owner_bytes = (
        json.dumps(owner, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    if owner_path.read_bytes() != canonical_owner_bytes:
        return (
            "proposal-publication-recovery-required",
            ("proposal-publication owner receipt is not canonical",),
        )
    owner_token = owner.get("owner_token")
    program_id = owner.get("program_id")
    target_value = owner.get("target")
    inventory_value = owner.get("inventory")
    if (
        owner.get("schema_version")
        != "implementation-proposal-publication-owner/v1"
        or not isinstance(owner_token, str)
        or len(owner_token) != 16
        or not isinstance(program_id, str)
        or not program_id
        or "/" in program_id
        or "\\" in program_id
        or program_id in {".", ".."}
        or target_value != f"implementation-programs/{program_id}"
        or staging.name != f".implementation-program-{program_id}-{owner_token}"
        or not isinstance(inventory_value, list)
    ):
        return (
            "proposal-publication-recovery-required",
            ("proposal-publication owner receipt is invalid",),
        )
    expected: dict[str, str] = {}
    for item in inventory_value:
        if not isinstance(item, dict):
            return (
                "proposal-publication-recovery-required",
                ("proposal-publication inventory entry is invalid",),
            )
        relative = _safe_owner_inventory_path(item.get("path"))
        digest = item.get("sha256")
        if (
            relative is None
            or relative in expected
            or not isinstance(digest, str)
            or len(digest) != 64
        ):
            return (
                "proposal-publication-recovery-required",
                ("proposal-publication inventory entry is invalid",),
            )
        expected[relative] = digest
    if "manifest.json" not in expected:
        return (
            "proposal-publication-recovery-required",
            ("proposal-publication inventory omits manifest.json",),
        )
    owner_bytes = canonical_owner_bytes
    staging_issue = _publication_tree_issue(staging, expected, owner_bytes)
    if staging_issue is not None:
        return "proposal-publication-recovery-required", (staging_issue,)
    target = repository / str(target_value)
    manifest = target / "manifest.json"
    manifest_committed = (
        manifest.is_file()
        and not manifest.is_symlink()
        and sha256_file(manifest) == expected["manifest.json"]
        and all(
            (target / relative).is_file()
            and not (target / relative).is_symlink()
            for relative in expected
        )
    )
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_dir():
            return (
                "proposal-publication-recovery-required",
                ("proposal-publication target is unsafe",),
            )
        activation_started = False
        if manifest_committed:
            committed_manifest, committed_manifest_issues = load_json_object(manifest)
            if committed_manifest is None:
                return (
                    "proposal-publication-recovery-required",
                    tuple(committed_manifest_issues),
                )
            logical_roles = committed_manifest.get("logical_roles")
            if not isinstance(logical_roles, dict):
                return (
                    "proposal-publication-recovery-required",
                    ("published manifest logical_roles must be an object",),
                )
            status_path, status_path_issues = resolve_managed_path(
                target,
                logical_roles.get("status"),
                role="logical role status",
            )
            approvals_path, approvals_path_issues = resolve_managed_path(
                target,
                logical_roles.get("approvals"),
                role="logical role approvals",
            )
            role_issues = (*status_path_issues, *approvals_path_issues)
            if status_path is None or approvals_path is None or role_issues:
                return (
                    "proposal-publication-recovery-required",
                    tuple(role_issues),
                )
            status, status_issues = load_json_object(status_path)
            if status is None:
                return (
                    "proposal-publication-recovery-required",
                    tuple(status_issues),
                )
            activation_started = (
                isinstance(status, dict)
                and status.get("current_increment_state") != "not-started"
            ) or (
                approvals_path.is_file()
                and not approvals_path.is_symlink()
                and bool(approvals_path.read_bytes())
            )
            target_owner = target / ".publication-owner.json"
            if (
                target_owner.is_symlink()
                or not target_owner.is_file()
                or target_owner.read_bytes() != owner_bytes
            ):
                return (
                    "proposal-publication-recovery-required",
                    ("publication owner receipt differs",),
                )
        if any(target.iterdir()) and not activation_started:
            target_issue = _publication_tree_issue(target, expected, owner_bytes)
            if target_issue is not None:
                return "proposal-publication-recovery-required", (target_issue,)
    return (
        (None, ())
        if manifest_committed
        else ("proposal-publication-retry-ready", ())
    )


def _path_issues(repository: Path, path: Path, label: str) -> list[str]:
    issues: list[str] = []
    try:
        relative = _absolute_input_path(repository, path).relative_to(repository)
    except ValueError:
        return [f"{label} escapes the repository"]
    current = repository
    if repository.is_symlink() or not repository.is_dir():
        return ["repository root must be a regular non-symlink directory"]
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            issues.append(f"{label} traverses a symlink: {_relative_path(repository, current)}")
            break
    if not path.is_file():
        issues.append(f"{label} must be a regular file")
    return issues


def _validate_persisted_bindings(
    program_root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
) -> list[str]:
    issues: list[str] = []
    if status.get("schema_version") != STATUS_SCHEMA:
        issues.append("unsupported status schema")
    if status.get("current_increment_state") not in INCREMENT_TRANSITIONS:
        issues.append("unknown increment state")
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return ["manifest logical_roles must be an object"]
    resolved_roles: dict[str, Path] = {}
    for role, raw_path in sorted(logical_roles.items()):
        path, path_issues = resolve_managed_path(
            program_root,
            raw_path,
            role=f"logical role {role}",
        )
        issues.extend(path_issues)
        if path is not None:
            resolved_roles[str(role)] = path

    source_binding = manifest.get("source_binding")
    status_source = status.get("source_binding")
    if not isinstance(source_binding, dict) or not isinstance(status_source, dict):
        issues.append("source binding must be an object")
    else:
        for field in ("source_id", "sha256"):
            if status_source.get(field) != source_binding.get(field):
                issues.append(f"status source {field} mismatch")

    program_binding = manifest.get("program_binding")
    status_program = status.get("program_binding")
    if not isinstance(program_binding, dict) or not isinstance(status_program, dict):
        issues.append("program binding must be an object")
    else:
        if status_program.get("sha256") != program_binding.get("sha256"):
            issues.append("status program digest mismatch")
        traceability_path = resolved_roles.get("traceability")
        if traceability_path is not None:
            traceability, traceability_issues = load_json_object(traceability_path)
            issues.extend(traceability_issues)
            if traceability is not None:
                coverage = traceability.get("coverage_assertion")
                semantic_sha256 = (
                    coverage.get("semantic_requirements_sha256")
                    if isinstance(coverage, dict)
                    else None
                )
                if (
                    status_program.get("semantic_requirements_sha256")
                    != semantic_sha256
                ):
                    issues.append("status semantic requirements digest mismatch")

    if status.get("approval_mode") != manifest.get("approval_mode"):
        issues.append("status approval mode mismatch")
    current_increment = manifest.get("current_increment")
    if not isinstance(current_increment, dict):
        issues.append("manifest current_increment must be an object")
    else:
        if current_increment.get("increment_id") != status.get("current_increment_id"):
            issues.append("manifest current increment mismatch")
        if current_increment.get("state") != status.get("current_increment_state"):
            issues.append("manifest current increment state mismatch")

    brief_binding = status.get("brief_binding")
    brief_path = resolved_roles.get("current_increment_brief")
    if not isinstance(brief_binding, dict):
        issues.append("status brief_binding must be an object")
    elif brief_path is not None:
        if brief_binding.get("path") != logical_roles.get("current_increment_brief"):
            issues.append("brief path mismatch")
        if brief_binding.get("sha256") != sha256_file(brief_path):
            issues.append("brief digest mismatch")

    plan_path = resolved_roles.get("current_exact_file_plan")
    if plan_path is not None:
        plan_sha256 = sha256_file(plan_path)
        if plan_sha256 not in {
            status.get("pending_exact_file_plan_sha256"),
            status.get("approved_exact_file_plan_sha256"),
        }:
            issues.append("plan digest mismatch")
        if (
            isinstance(current_increment, dict)
            and current_increment.get("exact_file_plan_sha256") != plan_sha256
        ):
            issues.append("manifest plan digest mismatch")

    workspace_path = resolved_roles.get("workspace")
    if workspace_path is not None:
        workspace, workspace_issues = load_json_object(workspace_path)
        issues.extend(workspace_issues)
        if workspace is not None:
            if workspace.get("schema_version") != WORKSPACE_SCHEMA:
                issues.append("unsupported workspace schema")
            for field in ("program_id", "program_revision"):
                if workspace.get(field) != manifest.get(field):
                    issues.append(f"workspace {field} mismatch")
            selected = workspace.get("implementation_workspace")
            workspace_binding = manifest.get("workspace_binding")
            if not isinstance(selected, dict) or not isinstance(
                workspace_binding, dict
            ):
                issues.append("workspace selection and manifest binding are required")
            else:
                persisted_pairs = (
                    ("path", selected.get("path"), workspace_binding.get("path")),
                    ("branch", selected.get("branch"), workspace_binding.get("branch")),
                    (
                        "base commit",
                        selected.get("base_commit"),
                        workspace_binding.get("base_commit"),
                    ),
                )
                for label, persisted, manifest_value in persisted_pairs:
                    if persisted != manifest_value:
                        issues.append(f"workspace {label} binding mismatch")
                selected_head = selected.get(
                    "head_commit_at_selection",
                    selected.get("head_commit_at_revision_activation"),
                )
                if not isinstance(selected_head, str) or not selected_head:
                    issues.append("workspace selected head is required")
            if (
                isinstance(brief_binding, dict)
                and brief_binding.get("workspace_sha256")
                != sha256_file(workspace_path)
            ):
                issues.append("brief workspace digest mismatch")
    return sorted(set(issues))


def _load_candidate(
    repository: Path,
    manifest_path: Path,
    observation_provider: ObservationProvider,
) -> tuple[ProgramCandidate | None, ResumeExpectations | None, tuple[str, ...]]:
    display_path = _display_path(repository, manifest_path)
    issues = _path_issues(repository, manifest_path, f"manifest {display_path}")
    if issues:
        return None, None, tuple(sorted(set(issues)))
    program_root = manifest_path.parent
    authority_issues = validate_program_authority(program_root)
    if authority_issues:
        return None, None, tuple(
            f"{display_path}: {issue}" for issue in authority_issues
        )
    manifest, manifest_issues = load_json_object(manifest_path)
    if manifest is None:
        return None, None, tuple(f"{display_path}: {issue}" for issue in manifest_issues)
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return None, None, (f"{display_path}: manifest logical_roles must be an object",)
    status_path, status_path_issues = resolve_managed_path(
        program_root,
        logical_roles.get("status"),
        role="logical role status",
    )
    if status_path is None:
        return None, None, tuple(f"{display_path}: {issue}" for issue in status_path_issues)
    status, status_issues = load_json_object(status_path)
    if status is None:
        return None, None, tuple(f"{display_path}: {issue}" for issue in status_issues)

    program_state = status.get("program_state")
    issues.extend(_validate_persisted_bindings(program_root, manifest, status))
    for label, actual, expected in (
        ("program_id", status.get("program_id"), manifest.get("program_id")),
        ("program_revision", status.get("program_revision"), manifest.get("program_revision")),
        ("program_state", program_state, manifest.get("program_status")),
    ):
        if actual != expected:
            issues.append(f"{display_path}: status {label} does not match manifest")
    if program_state not in SUPPORTED_PROGRAM_STATES:
        issues.append(f"{display_path}: unsupported controlling program state {program_state!r}")
    sequence = status.get("state_sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        issues.append(f"{display_path}: status state_sequence is invalid")
    if issues:
        return None, None, tuple(sorted(set(issues)))

    candidate = ProgramCandidate(
        manifest_path=display_path,
        program_root=_relative_path(repository, program_root),
        program_id=str(manifest["program_id"]),
        program_revision=int(manifest["program_revision"]),
        program_state=str(program_state),
        status_path=_relative_path(repository, status_path),
        status_sha256=sha256_file(status_path),
        status_sequence=sequence,
    )
    if program_state == "closed":
        return candidate, None, ()

    workspace_binding = manifest.get("workspace_binding")
    if not isinstance(workspace_binding, dict):
        return None, None, (f"{display_path}: manifest workspace_binding must be an object",)
    workspace_path = workspace_binding.get("path")
    base_commit = workspace_binding.get("base_commit")
    if not isinstance(workspace_path, str) or not workspace_path:
        issues.append(f"{display_path}: manifest workspace path is required")
    if not isinstance(base_commit, str) or not base_commit:
        issues.append(f"{display_path}: manifest workspace base commit is required")
    if issues:
        return None, None, tuple(sorted(set(issues)))
    try:
        observation = observation_provider(Path(workspace_path), base_commit)
    except (OSError, TypeError, ValueError) as error:
        return None, None, (f"{display_path}: repository observation failed: {error}",)
    state_issues = validate_state_authority(program_root, observation)
    if state_issues:
        return None, None, tuple(f"{display_path}: {issue}" for issue in state_issues)

    source_binding = manifest["source_binding"]
    program_binding = status["program_binding"]
    brief_binding = status["brief_binding"]
    exact_file_plan_sha256 = status.get("approved_exact_file_plan_sha256")
    if not isinstance(exact_file_plan_sha256, str):
        exact_file_plan_sha256 = status.get("pending_exact_file_plan_sha256")
    expectations = ResumeExpectations(
        manifest_path=display_path,
        manifest_sha256=sha256_file(manifest_path),
        status_path=candidate.status_path,
        status_sha256=candidate.status_sha256,
        status_sequence=candidate.status_sequence,
        program_id=candidate.program_id,
        program_revision=candidate.program_revision,
        program_state=candidate.program_state,
        source_id=str(source_binding["source_id"]),
        source_sha256=str(source_binding["sha256"]),
        program_sha256=str(program_binding["sha256"]),
        semantic_requirements_sha256=str(
            program_binding["semantic_requirements_sha256"]
        ),
        approval_mode=str(status["approval_mode"]),
        workspace_path=observation.path,
        workspace_branch=observation.branch,
        workspace_base_commit=observation.base_commit,
        workspace_head_commit=observation.head_commit,
        staged_paths=observation.staged_paths,
        modified_paths=observation.modified_paths,
        untracked_paths=observation.untracked_paths,
        conflicted_paths=observation.conflicted_paths,
        active_git_operation=observation.active_git_operation,
        current_increment_id=str(status["current_increment_id"]),
        current_increment_state=str(status["current_increment_state"]),
        brief_path=str(brief_binding["path"]),
        brief_sha256=str(brief_binding["sha256"]),
        exact_file_plan_sha256=str(exact_file_plan_sha256),
    )
    return candidate, expectations, ()


def discover_programs(
    repository_root: Path,
    *,
    explicit_manifest_path: str | Path | None = None,
    instruction_manifest_paths: Sequence[str | Path] = (),
    authoritative_source_plan_path: str | Path | None = None,
    observation_provider: ObservationProvider = _default_observation_provider,
) -> ProgramDiscoveryResult:
    """Discover convention-owned manifests and return one deterministic route."""
    repository = Path(repository_root).absolute()
    if repository.is_symlink() or not repository.is_dir():
        return ProgramDiscoveryResult(
            disposition="invalid",
            required_input=None,
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=("repository root must be a regular non-symlink directory",),
            next_action="Use the exact regular repository path and rerun discovery.",
            stop_required=True,
        )
    publication_disposition, publication_issues = _bootstrap_prefix_disposition(
        repository
    )
    if publication_disposition is not None:
        required_input, next_action, stop_required = PLAN_A_ROUTE_DETAILS[
            publication_disposition
        ]
        return ProgramDiscoveryResult(
            disposition=publication_disposition,
            required_input=required_input,
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=publication_issues,
            next_action=next_action,
            stop_required=stop_required,
        )
    conventional_root = repository / "implementation-programs"
    if explicit_manifest_path is not None:
        manifests = (
            _absolute_input_path(repository, explicit_manifest_path),
        )
    elif conventional_root.is_symlink():
        return ProgramDiscoveryResult(
            disposition="invalid",
            required_input=None,
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=("implementation-programs root must not be a symlink",),
            next_action="Replace the controlling symlink with an instruction-declared regular path.",
            stop_required=True,
        )
    else:
        declared = tuple(
            _absolute_input_path(repository, path)
            for path in instruction_manifest_paths
        )
        conventional = (
            tuple(conventional_root.glob("*/manifest.json"))
            if conventional_root.is_dir()
            else ()
        )
        manifests = tuple(
            sorted(
                {*declared, *conventional},
                key=lambda path: path.as_posix(),
            )
        )
    if manifests:
        candidates: list[ProgramCandidate] = []
        closed: list[ProgramCandidate] = []
        expectations: list[ResumeExpectations] = []
        routes: dict[str, str] = {}
        issues: list[str] = []
        has_new_terminal = False
        for manifest_path in manifests:
            manifest, _manifest_issues = load_json_object(manifest_path)
            if (
                manifest is not None
                and manifest.get("schema_version") == NEW_PROGRAM_MANIFEST_SCHEMA
            ):
                candidate, route, candidate_issues = _load_new_candidate(
                    repository, manifest_path
                )
                resume = None
            else:
                candidate, resume, candidate_issues = _load_candidate(
                    repository, manifest_path, observation_provider
                )
                route = (
                    "legacy-rollover-upgrade-required"
                    if resume is not None
                    and resume.current_increment_state == "accepted"
                    and resume.approval_mode
                    in {"approval:full-diff", "approval:full"}
                    else None
                )
            issues.extend(candidate_issues)
            if candidate is None:
                continue
            if route == "terminal-programs" or (
                manifest is not None
                and manifest.get("schema_version") != NEW_PROGRAM_MANIFEST_SCHEMA
                and candidate.program_state == "closed"
            ):
                closed.append(candidate)
                has_new_terminal = has_new_terminal or route == "terminal-programs"
            else:
                candidates.append(candidate)
                if route is not None:
                    routes[candidate.manifest_path] = route
                if resume is not None:
                    expectations.append(resume)
        if issues:
            return ProgramDiscoveryResult(
                disposition="invalid",
                required_input=None,
                source_plan_path=None,
                candidates=tuple(candidates),
                closed_programs=tuple(closed),
                resume_expectations=None,
                issues=tuple(sorted(set(issues))),
                next_action="Correct the invalid controlling path or binding and rerun discovery.",
                stop_required=True,
            )
        if len(candidates) == 1:
            route = routes.get(candidates[0].manifest_path, "resume")
            required_input, next_action, stop_required = PLAN_A_ROUTE_DETAILS[route]
            return ProgramDiscoveryResult(
                disposition=route,
                required_input=required_input,
                source_plan_path=None,
                candidates=tuple(candidates),
                closed_programs=tuple(closed),
                resume_expectations=expectations[0] if expectations else None,
                issues=(),
                next_action=next_action,
                stop_required=stop_required,
            )
        if len(candidates) > 1:
            return ProgramDiscoveryResult(
                disposition="selection-required",
                required_input="program-manifest-selection",
                source_plan_path=None,
                candidates=tuple(candidates),
                closed_programs=tuple(closed),
                resume_expectations=None,
                issues=(),
                next_action="Select exactly one candidate manifest and rerun discovery explicitly.",
                stop_required=True,
            )
        terminal_disposition = "terminal-programs" if has_new_terminal else "closed-programs"
        return ProgramDiscoveryResult(
            disposition=terminal_disposition,
            required_input=(
                "new-program-or-terminal-program-inspection-intent"
                if has_new_terminal
                else "new-program-or-closed-program-inspection-intent"
            ),
            source_plan_path=None,
            candidates=(),
            closed_programs=tuple(closed),
            resume_expectations=None,
            issues=(),
            next_action=(
                "State explicit new-program intent or name a terminal manifest for inspection."
                if has_new_terminal
                else "State explicit new-program intent or name a closed manifest for inspection."
            ),
            stop_required=True,
        )
    if authoritative_source_plan_path is None:
        return ProgramDiscoveryResult(
            disposition="new-program-bootstrap-possible",
            required_input="authoritative-source-plan-path",
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=(),
            next_action="Supply the authoritative source-plan path before any program write.",
            stop_required=True,
        )
    source_plan = Path(os.path.abspath(Path(authoritative_source_plan_path)))
    if source_plan.is_symlink() or not source_plan.is_file():
        source_issue = (
            "authoritative source-plan path must be a regular non-symlink file"
        )
        return ProgramDiscoveryResult(
            disposition="invalid",
            required_input=None,
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=(source_issue,),
            next_action="Supply the exact regular authoritative source-plan path.",
            stop_required=True,
        )
    return ProgramDiscoveryResult(
        disposition="new-program-bootstrap-ready",
        required_input=None,
        source_plan_path=str(source_plan),
        candidates=(),
        closed_programs=(),
        resume_expectations=None,
        issues=(),
        next_action="Route the validated source plan to the program-authority bootstrap gate.",
        stop_required=False,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="program_discovery.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    discover = subparsers.add_parser("discover")
    discover.add_argument("repository_root")
    discover.add_argument("--manifest")
    discover.add_argument("--instruction-manifest", action="append", default=[])
    discover.add_argument("--source-plan")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(
        list(sys.argv[1:] if argv is None else argv)
    )
    result = discover_programs(
        Path(arguments.repository_root),
        explicit_manifest_path=arguments.manifest,
        instruction_manifest_paths=arguments.instruction_manifest,
        authoritative_source_plan_path=arguments.source_plan,
    )
    print(json.dumps(asdict(result), sort_keys=True))
    return 1 if result.stop_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
