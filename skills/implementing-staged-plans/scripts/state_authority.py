#!/usr/bin/env python3
"""Validate and atomically persist implementation lifecycle authority."""

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from program_authority import (
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
    validate_program_authority,
)


STATUS_SCHEMA = "implementation-program-status/v1"
WORKSPACE_SCHEMA = "implementation-workspace/v1"
APPROVAL_SCHEMA = "implementation-approval/v1"
ACTION_AUTHORIZATION_SCHEMA = "implementation-action-authorization/v1"

PROGRAM_TRANSITIONS = {
    "captured": frozenset(
        {"awaiting-program-approval", "blocked", "superseded"}
    ),
    "awaiting-program-approval": frozenset({"active", "blocked", "superseded"}),
    "active": frozenset({"blocked", "awaiting-closure-approval", "superseded"}),
    "blocked": frozenset(),
    "awaiting-closure-approval": frozenset(
        {"active", "blocked", "closed", "superseded"}
    ),
    "closed": frozenset(),
    "superseded": frozenset(),
}

INCREMENT_TRANSITIONS = {
    "not-started": frozenset({"preparing", "blocked", "superseded"}),
    "preparing": frozenset(
        {"awaiting-plan-approval", "authorized", "blocked", "superseded"}
    ),
    "awaiting-plan-approval": frozenset(
        {"authorized", "change-requested", "blocked", "superseded"}
    ),
    "authorized": frozenset({"implementing", "blocked", "superseded"}),
    "implementing": frozenset({"reviewing", "blocked", "superseded"}),
    "reviewing": frozenset({"remediating", "verified", "blocked", "superseded"}),
    "remediating": frozenset({"reviewing", "blocked", "superseded"}),
    "verified": frozenset(
        {"awaiting-diff-approval", "accepted", "blocked", "superseded"}
    ),
    "awaiting-diff-approval": frozenset(
        {"accepted", "change-requested", "blocked", "superseded"}
    ),
    "accepted": frozenset(),
    "change-requested": frozenset({"preparing", "blocked", "superseded"}),
    "blocked": frozenset(),
    "superseded": frozenset(),
}


@dataclass(frozen=True)
class ApprovalModePolicy:
    mode: str
    scope: str
    routine_plan_pause: bool
    interruptions: tuple[str, ...]
    diff_acceptance: str
    automatic_continuation: bool


APPROVAL_MODE_POLICIES = {
    "approval:standard": ApprovalModePolicy(
        mode="approval:standard",
        scope="one-increment",
        routine_plan_pause=True,
        interruptions=("material-decision", "contradiction", "hard-stop"),
        diff_acceptance="user",
        automatic_continuation=False,
    ),
    "approval:pre-approve": ApprovalModePolicy(
        mode="approval:pre-approve",
        scope="one-increment",
        routine_plan_pause=False,
        interruptions=(
            "user-owned-decision",
            "program-amendment",
            "contradiction",
            "hard-stop",
        ),
        diff_acceptance="user",
        automatic_continuation=False,
    ),
    "approval:full-increment": ApprovalModePolicy(
        mode="approval:full-increment",
        scope="one-increment",
        routine_plan_pause=False,
        interruptions=("hard-stop",),
        diff_acceptance="user",
        automatic_continuation=False,
    ),
    "approval:full-diff": ApprovalModePolicy(
        mode="approval:full-diff",
        scope="one-increment",
        routine_plan_pause=False,
        interruptions=("hard-stop",),
        diff_acceptance="automatic-after-verification-and-packet",
        automatic_continuation=False,
    ),
    "approval:full": ApprovalModePolicy(
        mode="approval:full",
        scope="conversation-bounded-multiple-increments",
        routine_plan_pause=False,
        interruptions=("hard-stop",),
        diff_acceptance="automatic-after-verification-and-packet",
        automatic_continuation=True,
    ),
}

ACTION_NAMES = frozenset(
    {
        "write-program-artifact",
        "create-workspace",
        "modify-workspace",
        "run-local-verification",
        "create-local-commit",
        "create-draft-pull-request",
        "merge",
        "publish",
        "release",
        "deploy",
        "migrate",
        "destructive-operation",
        "modify-provider-state",
        "modify-external-state",
    }
)


@dataclass(frozen=True)
class RepositoryObservation:
    repository: str
    path: str
    branch: str
    base_commit: str
    head_commit: str
    staged_paths: tuple[str, ...]
    modified_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]
    conflicted_paths: tuple[str, ...]
    active_git_operation: str | None


@dataclass(frozen=True)
class ApprovalBinding:
    event_type: str
    program_id: str
    program_revision: int
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    increment_id: str
    brief_sha256: str
    exact_file_plan_sha256: str
    approval_mode: str
    workspace_path: str
    workspace_branch: str
    workspace_base_commit: str
    workspace_head_commit: str
    source_id: str | None = None
    closure_reconciliation_sha256: str | None = None
    closure_packet_sha256: str | None = None


@dataclass(frozen=True)
class ActionBinding:
    action: str
    scope: str
    program_id: str
    program_revision: int
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    increment_id: str
    brief_sha256: str
    exact_file_plan_sha256: str
    approval_mode: str
    workspace_path: str
    workspace_branch: str
    workspace_base_commit: str
    workspace_head_commit: str
    source_id: str | None = None


@dataclass(frozen=True)
class AuthorizationDecision:
    authorized: bool
    authorization_id: str | None
    issues: tuple[str, ...]


@dataclass(frozen=True)
class TransitionDecision:
    allowed: bool
    issues: tuple[str, ...]


@dataclass(frozen=True)
class TransitionRequest:
    expected_status_sha256: str
    expected_state_sequence: int
    target_program_state: str
    target_increment_id: str
    target_increment_state: str
    transition_event_id: str
    action_authorization_id: str
    evidence: dict[str, object]


@dataclass(frozen=True)
class StateTransitionReceipt:
    prior_sha256: str
    current_sha256: str
    state_sequence: int
    program_state: str
    increment_id: str
    increment_state: str


@dataclass(frozen=True)
class AtomicWriteReceipt:
    prior_sha256: str
    current_sha256: str


@dataclass(frozen=True)
class WorkspaceSelection:
    selected_at: str
    observation: RepositoryObservation
    approval_event_id: str
    action_authorization_id: str


@dataclass(frozen=True)
class WorkspaceSelectionReceipt:
    prior_sha256: str
    current_sha256: str
    path: str


class _UsageError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def approval_mode_policy(
    mode: str | None, *, creating: bool = False
) -> ApprovalModePolicy:
    """Resolve an approval mode without defaulting persisted state."""
    if mode is None:
        if creating:
            return APPROVAL_MODE_POLICIES["approval:standard"]
        raise ValueError("persisted approval mode is required")
    try:
        return APPROVAL_MODE_POLICIES[mode]
    except KeyError as error:
        raise ValueError(f"unsupported approval mode: {mode}") from error


def is_program_transition_allowed(
    current: str,
    target: str,
    *,
    blocked_context: dict[str, object] | None = None,
) -> bool:
    if current not in PROGRAM_TRANSITIONS or target not in PROGRAM_TRANSITIONS:
        return False
    if current == "blocked":
        return (
            isinstance(blocked_context, dict)
            and blocked_context.get("resume_program_state") == target
            and target not in {"blocked", "closed", "superseded"}
        )
    return target in PROGRAM_TRANSITIONS[current]


def is_increment_transition_allowed(
    current: str,
    target: str,
    *,
    blocked_context: dict[str, object] | None = None,
) -> bool:
    if current not in INCREMENT_TRANSITIONS or target not in INCREMENT_TRANSITIONS:
        return False
    if current == "blocked":
        return (
            isinstance(blocked_context, dict)
            and blocked_context.get("resume_increment_state") == target
            and target not in {"blocked", "accepted", "superseded"}
        )
    return target in INCREMENT_TRANSITIONS[current]


def _workspace_parts(workspace: dict[str, object]) -> tuple[dict[str, Any], dict[str, Any]]:
    selected = workspace.get("implementation_workspace")
    existing = workspace.get("pre_existing_work_at_selection")
    if not isinstance(existing, dict):
        existing = workspace.get("pre_existing_work_at_revision_activation")
    return (
        selected if isinstance(selected, dict) else {},
        existing if isinstance(existing, dict) else {},
    )


def validate_workspace_selection(
    workspace: dict[str, object], observation: RepositoryObservation
) -> list[str]:
    """Compare a persisted selection with explicit caller-supplied facts."""
    issues: list[str] = []
    if workspace.get("schema_version") != WORKSPACE_SCHEMA:
        issues.append("unsupported workspace schema")
    repository = workspace.get("repository")
    repository_identity = (
        repository.get("identity") if isinstance(repository, dict) else None
    )
    selected, existing = _workspace_parts(workspace)
    selected_head = selected.get(
        "head_commit_at_selection",
        selected.get("head_commit_at_revision_activation"),
    )
    expected = {
        "repository identity": (repository_identity, observation.repository),
        "workspace path": (selected.get("path"), observation.path),
        "workspace branch": (selected.get("branch"), observation.branch),
        "workspace base commit": (selected.get("base_commit"), observation.base_commit),
    }
    if not isinstance(selected_head, str) or not selected_head:
        issues.append("workspace selected head commit is required")
    if selected_head == observation.head_commit:
        expected.update(
            {
                "staged paths": (
                    existing.get("staged_paths"),
                    list(observation.staged_paths),
                ),
                "modified paths": (
                    existing.get("modified_paths"),
                    list(observation.modified_paths),
                ),
                "untracked paths": (
                    existing.get("untracked_paths"),
                    list(observation.untracked_paths),
                ),
                "conflicted paths": (
                    existing.get("conflicted_paths"),
                    list(observation.conflicted_paths),
                ),
            }
        )
    if observation.active_git_operation is not None:
        issues.append(
            f"active git operation mismatch: expected None, found {observation.active_git_operation!r}"
        )
    for label, (actual, wanted) in expected.items():
        if actual != wanted:
            issues.append(f"{label} mismatch: expected {wanted!r}, found {actual!r}")
    return sorted(set(issues))


def validate_brief_binding(
    program_root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    workspace_sha256: str,
    observation: RepositoryObservation,
) -> list[str]:
    issues: list[str] = []
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return ["manifest logical_roles must be an object"]
    binding = status.get("brief_binding")
    if not isinstance(binding, dict):
        return ["status brief_binding must be an object"]
    expected_path = logical_roles.get("current_increment_brief")
    if binding.get("path") != expected_path:
        issues.append("brief path mismatch")
    brief_path, path_issues = resolve_managed_path(
        program_root, expected_path, role="logical role current_increment_brief"
    )
    issues.extend(path_issues)
    if brief_path is not None and binding.get("sha256") != sha256_file(brief_path):
        issues.append("brief digest mismatch")
    if binding.get("workspace_sha256") != workspace_sha256:
        issues.append("brief workspace digest mismatch")
    if binding.get("head_commit") != observation.head_commit:
        issues.append("brief head commit mismatch")
    return sorted(set(issues))


def validate_state(
    program_root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    observation: RepositoryObservation,
) -> list[str]:
    """Validate status fields and their current artifact bindings."""
    issues: list[str] = []
    if status.get("schema_version") != STATUS_SCHEMA:
        issues.append("unsupported status schema")
    sequence = status.get("state_sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        issues.append("state sequence must be a non-negative integer")
    if status.get("program_id") != manifest.get("program_id"):
        issues.append("status program_id mismatch")
    if status.get("program_revision") != manifest.get("program_revision"):
        issues.append("status program_revision mismatch")
    if status.get("program_state") not in PROGRAM_TRANSITIONS:
        issues.append("unknown program state")
    if status.get("current_increment_state") not in INCREMENT_TRANSITIONS:
        issues.append("unknown increment state")
    try:
        approval_mode_policy(status.get("approval_mode"))
    except ValueError as error:
        issues.append(str(error))

    source = manifest.get("source_binding")
    status_source = status.get("source_binding")
    if not isinstance(source, dict) or not isinstance(status_source, dict):
        issues.append("source binding must be an object")
    else:
        if status_source.get("source_id") != source.get("source_id"):
            issues.append("status source_id mismatch")
        if status_source.get("sha256") != source.get("sha256"):
            issues.append("status source digest mismatch")

    program = manifest.get("program_binding")
    status_program = status.get("program_binding")
    if not isinstance(program, dict) or not isinstance(status_program, dict):
        issues.append("program binding must be an object")
    else:
        if status_program.get("sha256") != program.get("sha256"):
            issues.append("status program digest mismatch")
        traceability_path = program_root / str(program.get("traceability_path", ""))
        traceability, traceability_issues = load_json_object(traceability_path)
        issues.extend(traceability_issues)
        semantic = None
        if traceability is not None:
            coverage = traceability.get("coverage_assertion")
            if isinstance(coverage, dict):
                semantic = coverage.get("semantic_requirements_sha256")
        if status_program.get("semantic_requirements_sha256") != semantic:
            issues.append("status semantic requirements digest mismatch")

    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return sorted(set([*issues, "manifest logical_roles must be an object"]))
    workspace_path, workspace_path_issues = resolve_managed_path(
        program_root,
        logical_roles.get("workspace"),
        role="logical role workspace",
    )
    issues.extend(workspace_path_issues)
    if workspace_path is not None:
        issues.extend(
            validate_brief_binding(
                program_root,
                manifest,
                status,
                sha256_file(workspace_path),
                observation,
            )
        )

    current_increment = manifest.get("current_increment")
    if isinstance(current_increment, dict):
        if current_increment.get("increment_id") != status.get("current_increment_id"):
            issues.append("manifest current increment mismatch")

    workspace_binding = manifest.get("workspace_binding")
    if not isinstance(workspace_binding, dict):
        issues.append("manifest workspace_binding must be an object")
    else:
        for label, actual, expected_value in (
            ("manifest workspace path", workspace_binding.get("path"), observation.path),
            (
                "manifest workspace branch",
                workspace_binding.get("branch"),
                observation.branch,
            ),
            (
                "manifest workspace base commit",
                workspace_binding.get("base_commit"),
                observation.base_commit,
            ),
            (
                "manifest workspace head commit",
                workspace_binding.get("head_at_preparation"),
                observation.head_commit,
            ),
        ):
            if actual != expected_value:
                issues.append(
                    f"{label} mismatch: expected {expected_value!r}, found {actual!r}"
                )

    plan_path, plan_path_issues = resolve_managed_path(
        program_root,
        logical_roles.get("current_exact_file_plan"),
        role="logical role current_exact_file_plan",
    )
    issues.extend(plan_path_issues)
    if plan_path is not None:
        actual_plan_sha256 = sha256_file(plan_path)
        pending = status.get("pending_exact_file_plan_sha256")
        approved = status.get("approved_exact_file_plan_sha256")
        if actual_plan_sha256 not in {pending, approved}:
            issues.append("plan digest mismatch")
        if isinstance(current_increment, dict):
            manifest_plan = current_increment.get("exact_file_plan_sha256")
            if manifest_plan is not None and manifest_plan != actual_plan_sha256:
                issues.append("manifest plan digest mismatch")

    previous = status.get("previous_state")
    if previous is not None:
        if not isinstance(previous, dict):
            issues.append("previous_state must be an object")
        else:
            if previous.get("schema_version") != STATUS_SCHEMA:
                issues.append("previous state schema mismatch")
            prior_sequence = previous.get("state_sequence")
            if (
                not isinstance(prior_sequence, int)
                or isinstance(prior_sequence, bool)
                or not isinstance(sequence, int)
                or prior_sequence != sequence - 1
            ):
                issues.append("previous state sequence mismatch")
            digest = previous.get("status_sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                issues.append("previous state digest invalid")
    return sorted(set(issues))


def _workspace_matches(record: dict[str, Any], binding: object) -> bool:
    workspace = record.get("workspace")
    return isinstance(workspace, dict) and workspace == {
        "path": getattr(binding, "workspace_path"),
        "branch": getattr(binding, "workspace_branch"),
        "base_commit": getattr(binding, "workspace_base_commit"),
        "head_commit": getattr(binding, "workspace_head_commit"),
    }


def _common_binding_matches(record: dict[str, Any], binding: object) -> bool:
    common_matches = (
        record.get("program_id") == getattr(binding, "program_id")
        and record.get("program_revision") == getattr(binding, "program_revision")
        and (
            getattr(binding, "source_id", None) is None
            or record.get("source_id") == getattr(binding, "source_id")
        )
        and record.get("source_sha256") == getattr(binding, "source_sha256")
        and record.get("program_sha256") == getattr(binding, "program_sha256")
        and record.get("semantic_requirements_sha256")
        == getattr(binding, "semantic_requirements_sha256")
        and record.get("increment_id") == getattr(binding, "increment_id")
        and record.get("brief_sha256") == getattr(binding, "brief_sha256")
        and record.get("exact_file_plan_sha256")
        == getattr(binding, "exact_file_plan_sha256")
        and record.get("approval_mode") == getattr(binding, "approval_mode")
        and _workspace_matches(record, binding)
    )
    if not common_matches:
        return False
    for field in ("closure_reconciliation_sha256", "closure_packet_sha256"):
        required = getattr(binding, field, None)
        if required is not None and record.get(field) != required:
            return False
    return True


def _validate_closure_readiness(
    root: Path,
    manifest: dict[str, Any],
    status: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    if status.get("current_increment_state") != "accepted":
        issues.append("closure requires the final increment to be accepted")
    binding = status.get("closure_binding")
    if not isinstance(binding, dict):
        return [*issues, "closure binding must be an object"]
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return [*issues, "manifest logical_roles must be an object"]
    role_fields = (
        (
            "closure_reconciliation",
            "reconciliation_path",
            "reconciliation_sha256",
        ),
        ("closure_packet", "closure_packet_path", "closure_packet_sha256"),
    )
    for role, path_field, digest_field in role_fields:
        role_value = logical_roles.get(role)
        if binding.get(path_field) != role_value:
            issues.append(f"closure {path_field} mismatch")
        path, path_issues = resolve_managed_path(
            root, role_value, role=f"logical role {role}"
        )
        issues.extend(path_issues)
        if path is not None and binding.get(digest_field) != sha256_file(path):
            issues.append(f"closure {digest_field} mismatch")
    if binding.get("final_increment_id") != status.get("current_increment_id"):
        issues.append("closure final increment binding mismatch")
    if binding.get("readiness_validated") is not True:
        issues.append("closure readiness evidence is not validated")
    for field in (
        "unresolved_requirements",
        "unresolved_amendments",
        "unowned_deferrals",
        "unresolved_material_findings",
    ):
        value = binding.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value != 0:
            issues.append(f"closure {field} must be zero")
    return sorted(set(issues))


def validate_approval_binding(
    records: list[dict[str, object]], required: ApprovalBinding
) -> list[str]:
    bound_records = [
        record
        for record in records
        if record.get("schema_version") == APPROVAL_SCHEMA
        and record.get("type") == required.event_type
        and _common_binding_matches(record, required)
    ]
    matching = [
        record for record in bound_records if record.get("decision") == "approved"
    ]
    if not matching:
        return ["no exact approved event matches the required approval binding"]
    if any(record.get("decision") != "approved" for record in bound_records):
        return ["conflicting approval records"]
    if len(matching) > 1:
        return ["multiple matching approvals"]
    scope = matching[0].get("scope")
    if not isinstance(scope, list) or not scope or not all(
        isinstance(item, str) and item for item in scope
    ):
        return ["matching approval scope must be a non-empty string list"]
    return []


def _is_expired(value: object) -> bool:
    if value is None:
        return False
    if not isinstance(value, str):
        return True
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    if parsed.tzinfo is None:
        return True
    return parsed <= datetime.now(timezone.utc)


def decide_action_authorization(
    records: list[dict[str, object]], required: ActionBinding
) -> AuthorizationDecision:
    if required.action not in ACTION_NAMES:
        return AuthorizationDecision(False, None, ("unsupported action",))
    bound_records = [
        record
        for record in records
        if record.get("schema_version") == ACTION_AUTHORIZATION_SCHEMA
        and isinstance(record.get("actions"), list)
        and required.action in record["actions"]
        and isinstance(record.get("scope"), list)
        and required.scope in record["scope"]
        and _common_binding_matches(record, required)
    ]
    matching = [
        record
        for record in bound_records
        if record.get("decision") == "authorized"
        and record.get("revoked") is not True
        and not _is_expired(record.get("expires_at"))
    ]
    if not matching:
        return AuthorizationDecision(
            False, None, ("no exact action authorization matches the required binding",)
        )
    if any(
        record.get("decision") != "authorized" or record.get("revoked") is True
        for record in bound_records
    ):
        return AuthorizationDecision(
            False, None, ("conflicting action authorization records",)
        )
    if len(matching) > 1:
        return AuthorizationDecision(
            False, None, ("multiple matching authorizations",)
        )
    authorization_id = matching[0].get("authorization_id")
    if not isinstance(authorization_id, str) or not authorization_id:
        return AuthorizationDecision(False, None, ("authorization id is required",))
    return AuthorizationDecision(True, authorization_id, ())


def validate_state_authority(
    program_root: Path, observation: RepositoryObservation
) -> list[str]:
    """Validate program authority plus selected workspace and lifecycle state."""
    root = Path(program_root)
    issues = list(validate_program_authority(root))
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    issues.extend(manifest_issues)
    if manifest is None:
        return sorted(set(issues))
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return sorted(set([*issues, "manifest logical_roles must be an object"]))
    status_path, status_path_issues = resolve_managed_path(
        root, logical_roles.get("status"), role="logical role status"
    )
    workspace_path, workspace_path_issues = resolve_managed_path(
        root, logical_roles.get("workspace"), role="logical role workspace"
    )
    issues.extend(status_path_issues)
    issues.extend(workspace_path_issues)
    if status_path is None or workspace_path is None:
        return sorted(set(issues))
    status, status_issues = load_json_object(status_path)
    workspace, workspace_issues = load_json_object(workspace_path)
    issues.extend(status_issues)
    issues.extend(workspace_issues)
    if status is not None:
        issues.extend(validate_state(root, manifest, status, observation))
    if workspace is not None:
        if workspace.get("program_id") != manifest.get("program_id"):
            issues.append("workspace program_id mismatch")
        if workspace.get("program_revision") != manifest.get("program_revision"):
            issues.append("workspace program_revision mismatch")
        issues.extend(validate_workspace_selection(workspace, observation))
    return sorted(set(issues))


def evaluate_increment_transition(
    status: dict[str, object],
    target: str,
    *,
    packet_sha256: str | None = None,
    conversation_suitable: bool = False,
) -> TransitionDecision:
    current = status.get("current_increment_state")
    blocked_context = status.get("blocked_context")
    if not isinstance(current, str) or not is_increment_transition_allowed(
        current,
        target,
        blocked_context=blocked_context if isinstance(blocked_context, dict) else None,
    ):
        return TransitionDecision(False, (f"illegal increment transition {current!r} -> {target!r}",))
    issues: list[str] = []
    mode = status.get("approval_mode")
    try:
        policy = approval_mode_policy(mode if isinstance(mode, str) else None)
    except ValueError as error:
        return TransitionDecision(False, (str(error),))
    if current == "verified" and target == "accepted":
        verification = status.get("verification_binding")
        fresh = (
            isinstance(verification, dict)
            and verification.get("state_sequence") == status.get("state_sequence")
            and verification.get("review_packet_sha256") == packet_sha256
            and verification.get("unresolved_material_findings") == 0
        )
        if policy.diff_acceptance != "automatic-after-verification-and-packet":
            issues.append("approval mode requires user diff acceptance")
        if not fresh:
            issues.append("fresh verification")
        if not conversation_suitable:
            issues.append("current conversation is not suitable for automatic acceptance")
    if current == "verified" and target == "awaiting-diff-approval":
        if policy.diff_acceptance != "user":
            issues.append("automatic diff mode does not use awaiting-diff-approval")
    if current == "awaiting-diff-approval" and target == "accepted":
        verification = status.get("verification_binding")
        verified_sequence = (
            verification.get("verified_state_sequence")
            if isinstance(verification, dict)
            else None
        )
        fresh = (
            isinstance(verified_sequence, int)
            and not isinstance(verified_sequence, bool)
            and verified_sequence <= status.get("state_sequence", -1)
            and verification.get("review_packet_sha256") == packet_sha256
            and verification.get("unresolved_material_findings") == 0
        )
        if policy.diff_acceptance != "user":
            issues.append("approval mode does not use user diff acceptance")
        if not fresh:
            issues.append("fresh verification")
    if current == "reviewing" and target == "verified":
        verification = status.get("verification_binding")
        if not isinstance(verification, dict) or verification.get(
            "unresolved_material_findings"
        ) != 0:
            issues.append("fresh verification with no material findings is required")
    if current == "reviewing" and target == "remediating":
        review = status.get("review_binding")
        if not isinstance(review, dict) or not review.get("unresolved_material_findings"):
            issues.append("unresolved material findings are required")
    return TransitionDecision(not issues, tuple(sorted(set(issues))))


def may_start_next_increment(
    mode: str,
    *,
    renewed_user_authority: bool,
    conversation_suitable: bool,
) -> bool:
    if renewed_user_authority:
        return True
    policy = approval_mode_policy(mode)
    return policy.automatic_continuation and conversation_suitable


def _canonical_json_bytes(value: dict[str, object]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _validate_atomic_target(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"{path}: symlink targets are not allowed")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise ValueError(f"{path}: parent must be a regular directory")


def _atomic_replace_bytes(
    path: Path, payload: bytes, expected_sha256: str
) -> AtomicWriteReceipt:
    _validate_atomic_target(path)
    if not path.is_file():
        raise ValueError(f"{path}: target must be an existing regular file")
    prior_sha256 = sha256_file(path)
    if prior_sha256 != expected_sha256:
        raise ValueError(
            f"{path}: digest changed; expected {expected_sha256}, found {prior_sha256}"
        )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
    return AtomicWriteReceipt(prior_sha256, sha256_file(path))


def atomic_replace_json(
    path: Path, value: dict[str, object], expected_sha256: str
) -> AtomicWriteReceipt:
    return _atomic_replace_bytes(Path(path), _canonical_json_bytes(value), expected_sha256)


def atomic_append_json_line(
    path: Path, value: dict[str, object], expected_sha256: str
) -> AtomicWriteReceipt:
    path = Path(path)
    _validate_atomic_target(path)
    prior = path.read_bytes()
    if prior and not prior.endswith(b"\n"):
        raise ValueError(f"{path}: JSON Lines file must end with a trailing newline")
    records, issues = load_json_lines(path)
    if records is None:
        raise ValueError("; ".join(issues))
    identifiers = {
        record.get("event_id", record.get("authorization_id")) for record in records
    }
    identifier = value.get("event_id", value.get("authorization_id"))
    if not isinstance(identifier, str) or not identifier:
        raise ValueError("record identifier is required")
    if identifier in identifiers:
        raise ValueError(f"duplicate record identifier: {identifier}")
    line = (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    return _atomic_replace_bytes(path, prior + line, expected_sha256)


def _load_role(
    root: Path, manifest: dict[str, Any], role: str, *, json_lines: bool = False
) -> tuple[Any, Path]:
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    path, issues = resolve_managed_path(root, logical_roles.get(role), role=f"logical role {role}")
    if path is None:
        raise ValueError("; ".join(issues))
    value, load_issues = load_json_lines(path) if json_lines else load_json_object(path)
    if value is None:
        raise ValueError("; ".join(load_issues))
    return value, path


def _binding_from_state(
    manifest: dict[str, Any],
    status: dict[str, Any],
    observation: RepositoryObservation,
    *,
    event_type: str,
) -> ApprovalBinding:
    brief = status["brief_binding"]
    program = status["program_binding"]
    source = status["source_binding"]
    plan = status.get("pending_exact_file_plan_sha256") or status.get(
        "approved_exact_file_plan_sha256"
    )
    closure = status.get("closure_binding")
    closure_reconciliation_sha256 = None
    closure_packet_sha256 = None
    if event_type == "program-closure-approval" and isinstance(closure, dict):
        closure_reconciliation_sha256 = closure.get("reconciliation_sha256")
        closure_packet_sha256 = closure.get("closure_packet_sha256")
    return ApprovalBinding(
        event_type=event_type,
        program_id=manifest["program_id"],
        program_revision=manifest["program_revision"],
        source_sha256=source["sha256"],
        program_sha256=program["sha256"],
        semantic_requirements_sha256=program["semantic_requirements_sha256"],
        increment_id=status["current_increment_id"],
        brief_sha256=brief["sha256"],
        exact_file_plan_sha256=plan,
        approval_mode=status["approval_mode"],
        workspace_path=observation.path,
        workspace_branch=observation.branch,
        workspace_base_commit=observation.base_commit,
        workspace_head_commit=observation.head_commit,
        source_id=source["source_id"],
        closure_reconciliation_sha256=closure_reconciliation_sha256,
        closure_packet_sha256=closure_packet_sha256,
    )


def _action_binding_from_approval(
    approval: ApprovalBinding, action: str, scope: str
) -> ActionBinding:
    values = asdict(approval)
    values.pop("event_type")
    values.pop("closure_reconciliation_sha256")
    values.pop("closure_packet_sha256")
    return ActionBinding(action=action, scope=scope, **values)


def _atomic_create_json(path: Path, value: dict[str, object]) -> AtomicWriteReceipt:
    _validate_atomic_target(path)
    if path.exists():
        raise ValueError(f"{path}: target appeared before creation")
    payload = _canonical_json_bytes(value)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        if path.exists():
            raise ValueError(f"{path}: target appeared before creation")
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
    return AtomicWriteReceipt("", sha256_file(path))


def select_workspace(
    program_root: Path,
    selection: WorkspaceSelection,
    expected_sha256: str | None,
) -> WorkspaceSelectionReceipt:
    """Persist one explicitly approved workspace selection without running Git."""
    root = Path(program_root)
    program_issues = validate_program_authority(root)
    if program_issues:
        raise ValueError("; ".join(program_issues))
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, _ = _load_role(root, manifest, "status")
    approvals, _ = _load_role(root, manifest, "approvals", json_lines=True)
    authorizations, _ = _load_role(
        root, manifest, "action_authorizations", json_lines=True
    )
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    workspace_path, workspace_issues = resolve_managed_path(
        root,
        logical_roles.get("workspace"),
        role="logical role workspace",
        require_file=expected_sha256 is not None,
    )
    if workspace_path is None:
        raise ValueError("; ".join(workspace_issues))

    approval = _binding_from_state(
        manifest,
        status,
        selection.observation,
        event_type="workspace-selection-approval",
    )
    approval_issues = validate_approval_binding(approvals, approval)
    matching_approval_ids = {
        record.get("event_id")
        for record in approvals
        if record.get("schema_version") == APPROVAL_SCHEMA
        and record.get("type") == approval.event_type
        and record.get("decision") == "approved"
        and _common_binding_matches(record, approval)
    }
    if selection.approval_event_id not in matching_approval_ids:
        approval_issues.append("workspace selection event id does not match approved event")
    if approval_issues:
        raise ValueError("; ".join(sorted(set(approval_issues))))

    action = _action_binding_from_approval(
        approval, "create-workspace", "select the bound implementation workspace"
    )
    authorization = decide_action_authorization(authorizations, action)
    if not authorization.authorized:
        raise ValueError("; ".join(authorization.issues))
    if authorization.authorization_id != selection.action_authorization_id:
        raise ValueError("workspace action authorization id mismatch")

    observation = selection.observation
    workspace: dict[str, object] = {
        "schema_version": WORKSPACE_SCHEMA,
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "selected_at": selection.selected_at,
        "repository": {"identity": observation.repository},
        "implementation_workspace": {
            "path": observation.path,
            "branch": observation.branch,
            "base_commit": observation.base_commit,
            "head_commit_at_selection": observation.head_commit,
        },
        "pre_existing_work_at_selection": {
            "staged_paths": list(observation.staged_paths),
            "modified_paths": list(observation.modified_paths),
            "untracked_paths": list(observation.untracked_paths),
            "conflicted_paths": list(observation.conflicted_paths),
            "active_git_operation": observation.active_git_operation,
        },
        "selection_approval_event_id": selection.approval_event_id,
        "action_authorization_id": selection.action_authorization_id,
    }
    if expected_sha256 is None:
        receipt = _atomic_create_json(workspace_path, workspace)
    else:
        workspace["prior_workspace_sha256"] = expected_sha256
        receipt = atomic_replace_json(workspace_path, workspace, expected_sha256)
    return WorkspaceSelectionReceipt(
        prior_sha256=receipt.prior_sha256,
        current_sha256=receipt.current_sha256,
        path=str(workspace_path),
    )


def apply_state_transition(
    program_root: Path,
    request: TransitionRequest,
    observation: RepositoryObservation,
) -> StateTransitionReceipt:
    root = Path(program_root)
    issues = validate_state_authority(root, observation)
    if issues:
        raise ValueError("; ".join(issues))
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, status_path = _load_role(root, manifest, "status")
    approvals, _ = _load_role(root, manifest, "approvals", json_lines=True)
    authorizations, _ = _load_role(
        root, manifest, "action_authorizations", json_lines=True
    )
    prior_sha256 = sha256_file(status_path)
    if prior_sha256 != request.expected_status_sha256:
        raise ValueError("status digest changed")
    if status.get("state_sequence") != request.expected_state_sequence:
        raise ValueError("status sequence changed")
    current_program = status.get("program_state")
    if request.target_program_state != current_program and not is_program_transition_allowed(
        current_program, request.target_program_state, blocked_context=status.get("blocked_context")
    ):
        raise ValueError("illegal program transition")
    if request.target_increment_id != status.get("current_increment_id"):
        raise ValueError("state transition cannot change increment identity")
    increment_changes = (
        request.target_increment_state != status.get("current_increment_state")
    )
    program_changes = request.target_program_state != current_program
    if not increment_changes and not program_changes:
        raise ValueError("state transition must change program or increment state")
    closure_transition = (
        current_program == "active"
        and request.target_program_state == "awaiting-closure-approval"
    ) or (
        current_program == "awaiting-closure-approval"
        and request.target_program_state == "closed"
    )
    if closure_transition:
        closure_issues = _validate_closure_readiness(root, manifest, status)
        if closure_issues:
            raise ValueError("; ".join(closure_issues))
    if increment_changes:
        packet_sha256 = None
        logical_roles = manifest.get("logical_roles")
        if isinstance(logical_roles, dict) and logical_roles.get("current_review_packet"):
            packet_path, _ = resolve_managed_path(
                root,
                logical_roles.get("current_review_packet"),
                role="logical role current_review_packet",
            )
            if packet_path is not None:
                packet_sha256 = sha256_file(packet_path)
        decision = evaluate_increment_transition(
            status,
            request.target_increment_state,
            packet_sha256=packet_sha256,
            conversation_suitable=bool(
                request.evidence.get("conversation_suitable", False)
            ),
        )
        if not decision.allowed:
            raise ValueError("; ".join(decision.issues))

    current_increment_state = status.get("current_increment_state")
    approval_type = None
    if (
        current_increment_state == "awaiting-plan-approval"
        and request.target_increment_state == "authorized"
    ):
        approval_type = "exact-file-plan-approval"
    elif (
        current_increment_state == "awaiting-diff-approval"
        and request.target_increment_state == "accepted"
    ):
        approval_type = "increment-diff-approval"
    elif (
        current_program == "awaiting-program-approval"
        and request.target_program_state == "active"
    ):
        approval_type = "program-approval"
    elif (
        current_program == "awaiting-closure-approval"
        and request.target_program_state == "closed"
    ):
        approval_type = "program-closure-approval"

    approval = _binding_from_state(
        manifest,
        status,
        observation,
        event_type=approval_type or "state-transition",
    )
    if approval_type is not None:
        approval_issues = validate_approval_binding(approvals, approval)
        matching_approval_ids = {
            record.get("event_id")
            for record in approvals
            if record.get("schema_version") == APPROVAL_SCHEMA
            and record.get("type") == approval.event_type
            and record.get("decision") == "approved"
            and _common_binding_matches(record, approval)
        }
        if request.transition_event_id not in matching_approval_ids:
            approval_issues.append("transition event id does not match approved event")
        if approval_issues:
            raise ValueError("; ".join(sorted(set(approval_issues))))

    action_scope = request.evidence.get("action_scope")
    if not isinstance(action_scope, str) or not action_scope:
        raise ValueError("transition evidence action_scope is required")
    action = _action_binding_from_approval(
        approval, "modify-workspace", action_scope
    )
    authorization = decide_action_authorization(authorizations, action)
    if not authorization.authorized:
        raise ValueError("; ".join(authorization.issues))
    if authorization.authorization_id != request.action_authorization_id:
        raise ValueError("action authorization id mismatch")

    new_status = dict(status)
    new_status.update(
        state_sequence=request.expected_state_sequence + 1,
        program_state=request.target_program_state,
        current_increment_id=request.target_increment_id,
        current_increment_state=request.target_increment_state,
        previous_state={
            "schema_version": status["schema_version"],
            "status_sha256": prior_sha256,
            "state_sequence": status["state_sequence"],
            "program_state": status["program_state"],
            "current_increment_id": status["current_increment_id"],
            "current_increment_state": status["current_increment_state"],
            "transition_event_id": request.transition_event_id,
        },
        transition_authorization={
            "event_id": request.transition_event_id,
            "action_authorization_id": request.action_authorization_id,
        },
    )
    if (
        status.get("current_increment_state") == "awaiting-plan-approval"
        and request.target_increment_state == "authorized"
    ):
        new_status["approved_exact_file_plan_sha256"] = status.get(
            "pending_exact_file_plan_sha256"
        )
        new_status["pending_exact_file_plan_sha256"] = None
    if request.evidence:
        new_status["transition_evidence"] = request.evidence
    receipt = atomic_replace_json(status_path, new_status, prior_sha256)
    return StateTransitionReceipt(
        prior_sha256=receipt.prior_sha256,
        current_sha256=receipt.current_sha256,
        state_sequence=new_status["state_sequence"],
        program_state=new_status["program_state"],
        increment_id=new_status["current_increment_id"],
        increment_state=new_status["current_increment_state"],
    )


def _repository_observation(arguments: argparse.Namespace) -> RepositoryObservation:
    return RepositoryObservation(
        repository=arguments.repository,
        path=arguments.path or arguments.program_root,
        branch=arguments.branch,
        base_commit=arguments.base,
        head_commit=arguments.head,
        staged_paths=tuple(arguments.staged_path),
        modified_paths=tuple(arguments.modified_path),
        untracked_paths=tuple(arguments.untracked_path),
        conflicted_paths=tuple(arguments.conflicted_path),
        active_git_operation=arguments.active_git_operation,
    )


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(prog="state_authority.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-state")
    validate.add_argument("program_root")
    validate.add_argument("--repository", required=True)
    validate.add_argument("--branch", required=True)
    validate.add_argument("--base", required=True)
    validate.add_argument("--head", required=True)
    validate.add_argument("--path")
    validate.add_argument("--staged-path", action="append", default=[])
    validate.add_argument("--modified-path", action="append", default=[])
    validate.add_argument("--untracked-path", action="append", default=[])
    validate.add_argument("--conflicted-path", action="append", default=[])
    validate.add_argument("--active-git-operation")
    for command in ("check-action", "select-workspace", "transition-state"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("program_root")
        command_parser.add_argument("--request", required=True)
    return parser


def _load_request(path: str) -> dict[str, Any]:
    request, issues = load_json_object(Path(path))
    if request is None:
        raise ValueError("; ".join(issues))
    return request


def _observation_from_mapping(value: object) -> RepositoryObservation:
    if not isinstance(value, dict):
        raise ValueError("request observation must be an object")
    converted = dict(value)
    for field in (
        "staged_paths",
        "modified_paths",
        "untracked_paths",
        "conflicted_paths",
    ):
        entries = converted.get(field, [])
        if not isinstance(entries, list):
            raise ValueError(f"request observation {field} must be a list")
        converted[field] = tuple(entries)
    try:
        return RepositoryObservation(**converted)
    except TypeError as error:
        raise ValueError(f"invalid repository observation: {error}") from error


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        arguments = parser.parse_args(argv)
    except _UsageError as error:
        print(parser.format_usage().strip())
        print(f"error: {error}")
        return 2
    if arguments.command == "validate-state":
        issues = validate_state_authority(
            Path(arguments.program_root), _repository_observation(arguments)
        )
        if issues:
            for issue in sorted(set(issues)):
                print(issue)
            return 1
        print("State authority validation passed")
        return 0
    try:
        request = _load_request(arguments.request)
        root = Path(arguments.program_root)
        if arguments.command == "check-action":
            manifest, manifest_issues = load_json_object(root / "manifest.json")
            if manifest is None:
                raise ValueError("; ".join(manifest_issues))
            records, _ = _load_role(
                root, manifest, "action_authorizations", json_lines=True
            )
            try:
                binding = ActionBinding(**request)
            except TypeError as error:
                raise ValueError(f"invalid action request: {error}") from error
            decision = decide_action_authorization(records, binding)
            if not decision.authorized:
                for issue in decision.issues:
                    print(issue)
                return 1
            print(f"Authorized by {decision.authorization_id}")
            return 0
        if arguments.command == "select-workspace":
            observation = _observation_from_mapping(request.get("observation"))
            selection = WorkspaceSelection(
                selected_at=request["selected_at"],
                observation=observation,
                approval_event_id=request["approval_event_id"],
                action_authorization_id=request["action_authorization_id"],
            )
            receipt = select_workspace(
                root, selection, request.get("expected_workspace_sha256")
            )
            print(json.dumps(asdict(receipt), sort_keys=True))
            return 0
        if arguments.command == "transition-state":
            observation = _observation_from_mapping(request.get("observation"))
            transition_value = request.get("transition")
            if not isinstance(transition_value, dict):
                raise ValueError("request transition must be an object")
            transition = TransitionRequest(**transition_value)
            receipt = apply_state_transition(root, transition, observation)
            print(json.dumps(asdict(receipt), sort_keys=True))
            return 0
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(str(error))
        return 1
    print("unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
