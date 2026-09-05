#!/usr/bin/env python3
"""Validate and atomically persist implementation lifecycle authority."""

import argparse
import ctypes as _ctypes
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from contextvars import ContextVar
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - exercised by the Windows backend
    _fcntl = None

_WINDOWS = os.name == "nt"
_kernel32 = None
if _WINDOWS:  # pragma: no cover - configured and exercised on Windows
    _kernel32 = _ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateMutexW.argtypes = [
        _ctypes.c_void_p,
        _ctypes.c_int,
        _ctypes.c_wchar_p,
    ]
    _kernel32.CreateMutexW.restype = _ctypes.c_void_p
    _kernel32.WaitForSingleObject.argtypes = [_ctypes.c_void_p, _ctypes.c_ulong]
    _kernel32.WaitForSingleObject.restype = _ctypes.c_ulong
    _kernel32.ReleaseMutex.argtypes = [_ctypes.c_void_p]
    _kernel32.ReleaseMutex.restype = _ctypes.c_int
    _kernel32.CloseHandle.argtypes = [_ctypes.c_void_p]
    _kernel32.CloseHandle.restype = _ctypes.c_int

from program_authority import (
    APPROVED_VALIDATION_MODE,
    NEW_PROGRAM_MANIFEST_SCHEMA,
    PROPOSAL_VALIDATION_MODE,
    SETUP_PROGRAM_MANIFEST_SCHEMA,
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    resolve_program_closure_paths,
    sha256_file,
    validate_program_authority,
)


STATUS_SCHEMA = "implementation-program-status/v1"
STATUS_SCHEMA_V2 = "implementation-program-status/v2"
STATUS_SCHEMA_V3 = "implementation-program-status/v3"
STATUS_SCHEMAS = frozenset({STATUS_SCHEMA, STATUS_SCHEMA_V2, STATUS_SCHEMA_V3})
WORKSPACE_SCHEMA = "implementation-workspace/v1"
WORKSPACE_SCHEMA_V2 = "implementation-workspace/v2"
WORKSPACE_SCHEMAS = frozenset({WORKSPACE_SCHEMA, WORKSPACE_SCHEMA_V2})
APPROVAL_SCHEMA = "implementation-approval/v1"
ACTION_AUTHORIZATION_SCHEMA = "implementation-action-authorization/v1"
SETUP_ONLY_STATUS_SCHEMAS = frozenset(
    {
        STATUS_SCHEMA_V3,
        "implementation-approval/v2",
        "implementation-action-authorization/v2",
        "implementation-current-increment-authority-binding/v2",
        "implementation-increment-grant/v2",
        "implementation-setup-activation-status-binding/v1",
        "setup-activation-decision/v1",
        "source-gate-decision/v1",
        "source-gate-satisfaction/v1",
    }
)
LEGACY_ONLY_STATUS_SCHEMAS = frozenset(
    {
        STATUS_SCHEMA,
        STATUS_SCHEMA_V2,
        "implementation-program-activation-binding/v1",
        "implementation-current-increment-authority-binding/v1",
    }
)

_INSPECTING_UNBOUND_ROLLOVER_SUFFIX = ContextVar(
    "inspecting_unbound_rollover_suffix",
    default=False,
)

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
        scope="one-increment",
        routine_plan_pause=False,
        interruptions=("hard-stop",),
        diff_acceptance="automatic-after-verification-and-packet",
        automatic_continuation=False,
    ),
}

ACTION_NAMES = frozenset(
    {
        "write-program-artifact",
        "rollover-increment",
        "resume-blocked-program",
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
class ManagedWriteRequirement:
    path: str
    disposition: str


@dataclass(frozen=True)
class ExactFileMap:
    create: tuple[str, ...]
    modify: tuple[str, ...]
    preserve: tuple[str, ...]


def _workspace_relative_path(workspace_root: Path, path: Path) -> str:
    workspace = Path(workspace_root).resolve()
    resolved = Path(path).resolve(strict=False)
    try:
        return resolved.relative_to(workspace).as_posix()
    except ValueError as error:
        raise ValueError(f"managed lifecycle path escapes workspace: {path}") from error


def _nested_schema_versions(value: object) -> set[str]:
    schemas: set[str] = set()
    if isinstance(value, dict):
        schema = value.get("schema_version")
        if isinstance(schema, str):
            schemas.add(schema)
        for nested in value.values():
            schemas.update(_nested_schema_versions(nested))
    elif isinstance(value, list):
        for nested in value:
            schemas.update(_nested_schema_versions(nested))
    return schemas


def _traceability_successor(
    traceability: dict[str, object], increment_id: str
) -> str | None:
    atomic_requirements = traceability.get("atomic_requirements")
    if not isinstance(atomic_requirements, list):
        raise ValueError("traceability atomic_requirements must be a list")
    current_found = False
    candidates: set[str] = set()
    for requirement in atomic_requirements:
        assigned = (
            requirement.get("assigned_increments")
            if isinstance(requirement, dict)
            else None
        )
        if (
            not isinstance(assigned, list)
            or not assigned
            or not all(isinstance(candidate, str) and candidate for candidate in assigned)
            or len(assigned) != len(set(assigned))
        ):
            raise ValueError(
                "traceability assigned_increments must be unique strings"
            )
        if increment_id not in assigned:
            continue
        current_found = True
        successor_index = assigned.index(increment_id) + 1
        if successor_index < len(assigned):
            candidates.add(assigned[successor_index])
    if not current_found:
        raise ValueError("current increment is absent from traceability allocation")
    return next(iter(candidates)) if len(candidates) == 1 else None


def required_future_lifecycle_writes(
    program_root: Path,
    workspace_root: Path,
    increment_id: str,
) -> tuple[ManagedWriteRequirement, ...]:
    """Derive disposition-aware current and future control-plane allocations."""
    if (
        not isinstance(increment_id, str)
        or not increment_id
        or "/" in increment_id
        or "\\" in increment_id
        or increment_id in {".", ".."}
    ):
        raise ValueError("increment_id must be one safe path segment")
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    logical_roles = manifest.get("logical_roles")
    increment_storage = manifest.get("increment_storage")
    closure_storage = manifest.get("closure_storage")
    if not isinstance(logical_roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    if not isinstance(increment_storage, dict) or not isinstance(closure_storage, dict):
        raise ValueError("manifest lifecycle storage descriptors must be objects")

    requirements: list[ManagedWriteRequirement] = []
    for role in (
        "approvals",
        "status",
        "action_authorizations",
        "increment_grants",
        "rollovers",
        "block_resolutions",
    ):
        path, path_issues = resolve_managed_path(
            root, logical_roles.get(role), role=f"logical role {role}"
        )
        if path is None:
            raise ValueError("; ".join(path_issues))
        requirements.append(
            ManagedWriteRequirement(
                _workspace_relative_path(workspace_root, path), "Modify"
            )
        )
    if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA:
        for role, disposition in (
            ("setup_activation_decision", "Preserve"),
            ("source_gate_decisions", "Modify"),
        ):
            path, path_issues = resolve_managed_path(
                root, logical_roles.get(role), role=f"logical role {role}"
            )
            if path is None:
                raise ValueError("; ".join(path_issues))
            requirements.append(
                ManagedWriteRequirement(
                    _workspace_relative_path(workspace_root, path), disposition
                )
            )

    increment_root = increment_storage.get("root")
    if not isinstance(increment_root, str):
        raise ValueError("increment storage root must be a string")

    def allocated_increment_file(target_increment: str, field: str) -> Path:
        filename = increment_storage.get(field)
        if not isinstance(filename, str):
            raise ValueError(f"increment storage {field} must be a string")
        path, path_issues = resolve_managed_path(
            root,
            f"{increment_root}/{target_increment}/{filename}",
            role=f"allocated increment {field}",
            require_file=False,
        )
        if path is None:
            raise ValueError("; ".join(path_issues))
        return path

    for field in (
        "execution_baseline_filename",
        "review_evidence_filename",
        "review_packet_filename",
    ):
        requirements.append(
            ManagedWriteRequirement(
                _workspace_relative_path(
                    workspace_root, allocated_increment_file(increment_id, field)
                ),
                "Create",
            )
        )

    traceability_path, path_issues = resolve_managed_path(
        root, logical_roles.get("traceability"), role="logical role traceability"
    )
    if traceability_path is None:
        raise ValueError("; ".join(path_issues))
    traceability, traceability_issues = load_json_object(traceability_path)
    if traceability is None:
        raise ValueError("; ".join(traceability_issues))
    successor = _traceability_successor(traceability, increment_id)
    if successor is not None:
        requirements.extend(
            (
                ManagedWriteRequirement(
                    _workspace_relative_path(
                        workspace_root,
                        allocated_increment_file(increment_id, "handoff_filename"),
                    ),
                    "Create",
                ),
                ManagedWriteRequirement(
                    _workspace_relative_path(
                        workspace_root,
                        allocated_increment_file(successor, "brief_filename"),
                    ),
                    "Create",
                ),
            )
        )
    else:
        closure_root = closure_storage.get("root")
        if not isinstance(closure_root, str):
            raise ValueError("closure storage root must be a string")
        for field in ("reconciliation_filename", "packet_filename"):
            filename = closure_storage.get(field)
            if not isinstance(filename, str):
                raise ValueError(f"closure storage {field} must be a string")
            path, path_issues = resolve_managed_path(
                root,
                f"{closure_root}/{filename}",
                role=f"allocated closure {field}",
                require_file=False,
            )
            if path is None:
                raise ValueError("; ".join(path_issues))
            requirements.append(
                ManagedWriteRequirement(
                    _workspace_relative_path(workspace_root, path), "Create"
                )
            )
    return tuple(sorted(requirements, key=lambda item: (item.path, item.disposition)))


def validate_required_managed_file_map(
    file_map: ExactFileMap,
    required: Sequence[ManagedWriteRequirement],
) -> list[str]:
    """Require every manifest-derived path under its exact disposition."""
    declared = {
        "Create": set(file_map.create),
        "Modify": set(file_map.modify),
        "Preserve": set(file_map.preserve),
    }
    issues: list[str] = []
    for requirement in required:
        if requirement.disposition not in declared:
            issues.append(
                f"unsupported managed-write disposition {requirement.disposition!r}"
            )
            continue
        if requirement.path not in declared[requirement.disposition]:
            actual = next(
                (
                    disposition
                    for disposition, paths in declared.items()
                    if requirement.path in paths
                ),
                None,
            )
            if actual is None:
                issues.append(
                    f"required {requirement.disposition} path is missing: {requirement.path}"
                )
            else:
                issues.append(
                    f"required path {requirement.path} is {actual}, expected {requirement.disposition}"
                )
    return sorted(set(issues))


def validate_required_managed_writes(
    managed_paths: Sequence[str], required_paths: Sequence[str]
) -> list[str]:
    """Compatibility wrapper treating legacy managed paths as Modify entries."""
    file_map = ExactFileMap((), tuple(managed_paths), ())
    required = tuple(
        ManagedWriteRequirement(path, "Modify") for path in required_paths
    )
    return validate_required_managed_file_map(file_map, required)


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
    action_authorization_id: str | None
    evidence: dict[str, object]
    authority_kind: str = "action-authorization"
    execution_authorization_id: str | None = None
    checkpoint_id: str | None = None


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
    action_authorization_id: str | None
    authority_kind: str = "action-authorization"


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
            return APPROVAL_MODE_POLICIES["approval:full-increment"]
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


def transition_authority_policy(
    current_program_state: str,
    target_program_state: str,
    current_increment_state: str,
    target_increment_state: str,
) -> str:
    """Classify every transition edge without granting authority itself."""
    program_changed = current_program_state != target_program_state
    increment_changed = current_increment_state != target_increment_state
    if not program_changed and not increment_changed:
        raise ValueError("transition authority policy requires a state change")
    approval_program_edges = {
        ("awaiting-program-approval", "active"),
        ("awaiting-closure-approval", "closed"),
    }
    approval_increment_edges = {
        ("awaiting-plan-approval", "authorized"),
        ("awaiting-diff-approval", "accepted"),
    }
    if (
        program_changed
        and not increment_changed
        and (current_program_state, target_program_state) in approval_program_edges
    ):
        return "approval-event"
    if (
        increment_changed
        and not program_changed
        and (current_increment_state, target_increment_state)
        in approval_increment_edges
    ):
        return "approval-event"
    return "action-authorization"


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
    workspace_schema = workspace.get("schema_version")
    if workspace_schema not in WORKSPACE_SCHEMAS:
        issues.append("unsupported workspace schema")
    if workspace_schema == WORKSPACE_SCHEMA_V2:
        selection_authority = workspace.get("selection_authority")
        if (
            not isinstance(selection_authority, dict)
            or selection_authority.get("kind") != "approval-event"
            or not isinstance(selection_authority.get("event_id"), str)
            or not selection_authority.get("event_id")
            or "action_authorization_id" in workspace
        ):
            issues.append("v2 workspace selection authority is invalid")
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


def _canonical_json_line_sha256(record: dict[str, object]) -> str:
    payload = (
        json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _derived_identifier(label: str, seed: dict[str, object]) -> str:
    digest = _canonical_json_line_sha256(
        {"identifier_domain": label, "seed": seed}
    )
    return f"{label.upper()}-{digest[:24]}"


def _rollover_history_authority_issues(
    program_root: Path,
    status: dict[str, object],
    observation: RepositoryObservation,
) -> list[str]:
    try:
        from program_rollover import (
            _validated_completed_rollover_records,
            inspect_increment_rollover,
        )

        _validated_completed_rollover_records(
            program_root,
            status,
            allow_unbound_suffix=False,
        )
    except (ImportError, KeyError, OSError, TypeError, ValueError) as error:
        if str(error) != "unbound rollover history is not lifecycle authority":
            return [str(error)]
    else:
        return []

    if _INSPECTING_UNBOUND_ROLLOVER_SUFFIX.get():
        return []
    token = _INSPECTING_UNBOUND_ROLLOVER_SUFFIX.set(True)
    try:
        inspection = inspect_increment_rollover(program_root, observation)
    except (ImportError, KeyError, OSError, TypeError, ValueError):
        return ["unbound rollover history is not lifecycle authority"]
    finally:
        _INSPECTING_UNBOUND_ROLLOVER_SUFFIX.reset(token)
    if (
        not inspection.issues
        and inspection.disposition
        in {
            "increment-rollover-retry-ready",
            "accepted-state-rollover-retry-ready",
        }
        and inspection.completed_steps
        == (
            "action-authorization",
            "successor-grant",
            "handoff",
            "successor-brief",
            "rollover-record",
        )
    ):
        return []
    return ["unbound rollover history is not lifecycle authority"]


def _validate_new_program_state(
    program_root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    observation: RepositoryObservation,
) -> list[str]:
    """Validate status-owned v2 lifecycle bindings without mutable manifest roles."""
    issues: list[str] = []
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return ["manifest logical_roles must be an object"]
    workspace_path, workspace_issues = resolve_managed_path(
        program_root, logical_roles.get("workspace"), role="logical role workspace"
    )
    issues.extend(workspace_issues)
    workspace_sha256 = sha256_file(workspace_path) if workspace_path is not None else None

    activation = status.get("activation_binding")
    required_activation_fields = (
        "launch_checkpoint_id",
        "program_approval_event_id",
        "workspace_approval_event_id",
        "increment_grant_id",
        "submitted_prompt_sha256",
        "prior_status_sha256",
    )
    if (
        not isinstance(activation, dict)
        or activation.get("schema_version")
        != "implementation-program-activation-binding/v1"
        or activation.get("prior_status_sequence") != 0
        or any(
            not isinstance(activation.get(field), str) or not activation.get(field)
            for field in required_activation_fields
        )
    ):
        issues.append("v2 activation binding is invalid")

    authority = status.get("current_increment_authority_binding")
    if (
        not isinstance(authority, dict)
        or authority.get("schema_version")
        != "implementation-current-increment-authority-binding/v1"
        or authority.get("kind") != "increment-grant"
        or authority.get("increment_id") != status.get("current_increment_id")
        or not isinstance(authority.get("grant_id"), str)
        or not authority.get("grant_id")
        or not isinstance(authority.get("grant_sha256"), str)
        or len(str(authority.get("grant_sha256"))) != 64
    ):
        issues.append("v2 current increment authority binding is invalid")
    else:
        grants_path, grant_path_issues = resolve_managed_path(
            program_root,
            logical_roles.get("increment_grants"),
            role="logical role increment_grants",
        )
        issues.extend(grant_path_issues)
        if grants_path is not None:
            grants, grant_issues = load_json_lines(grants_path)
            issues.extend(grant_issues)
            matches = (
                []
                if grants is None
                else [
                    record
                    for record in grants
                    if record.get("grant_id") == authority.get("grant_id")
                ]
            )
            if len(matches) != 1:
                issues.append("status-current increment grant must exist exactly once")
            elif (
                matches[0].get("schema_version")
                != "implementation-increment-grant/v1"
                or matches[0].get("program_id") != manifest.get("program_id")
                or matches[0].get("program_revision")
                != manifest.get("program_revision")
                or matches[0].get("increment_id") != status.get("current_increment_id")
                or matches[0].get("approval_mode") != status.get("approval_mode")
                or _canonical_json_line_sha256(matches[0])
                != authority.get("grant_sha256")
            ):
                issues.append("status-current increment grant binding mismatch")
            else:
                grant_brief = matches[0].get("brief_binding")
                status_brief = status.get("brief_binding")
                if (
                    not isinstance(grant_brief, dict)
                    or not isinstance(status_brief, dict)
                    or any(
                        status_brief.get(field) != grant_brief.get(field)
                        for field in ("path", "sha256")
                    )
                ):
                    issues.append(
                        "status-current increment grant brief binding mismatch"
                    )

    issues.extend(
        _rollover_history_authority_issues(program_root, status, observation)
    )
    rollover = status.get("rollover_binding")
    if rollover is not None:
        inherited = status.get("inherited_workspace_binding")
        transition = status.get("transition_authority")
        increment_state = status.get("current_increment_state")
        rollover_transition_valid = (
            isinstance(rollover, dict)
            and (
                increment_state != "preparing"
                or (
                    isinstance(transition, dict)
                    and transition.get("kind") == "action-authorization"
                    and transition.get("authorization_id")
                    == rollover.get("rollover_authorization_id")
                    and transition.get("event_id") == rollover.get("rollover_id")
                    and transition.get("checkpoint_id")
                    == rollover.get("continuation_checkpoint_id")
                )
            )
        )
        rollover_valid = (
            isinstance(rollover, dict)
            and rollover.get("schema_version")
            == "implementation-increment-rollover-binding/v1"
            and status.get("program_state") == "active"
            and increment_state
            in {
                "preparing",
                "awaiting-plan-approval",
                "authorized",
                "implementing",
                "reviewing",
                "remediating",
                "verified",
                "awaiting-diff-approval",
                "accepted",
            }
            and rollover.get("successor_increment_id")
            == status.get("current_increment_id")
            and rollover.get("current_increment_id")
            != rollover.get("successor_increment_id")
            and rollover_transition_valid
            and isinstance(inherited, dict)
            and inherited.get("schema_version")
            == "implementation-inherited-workspace/v1"
        )
        if not rollover_valid:
            issues.append("successor rollover binding is invalid")
        else:
            try:
                from program_rollover import _validated_inherited_paths

                inherited_paths = _validated_inherited_paths(
                    program_root,
                    status,
                    observation,
                    allow_unbound_suffix=True,
                )
            except (ImportError, KeyError, OSError, TypeError, ValueError) as error:
                issues.append(str(error))
            else:
                if inherited.get("inherited_paths") != list(inherited_paths):
                    issues.append("inherited workspace inventory mismatch")

            rollover_path, rollover_path_issues = resolve_managed_path(
                program_root,
                logical_roles.get("rollovers"),
                role="logical role rollovers",
            )
            action_path, action_path_issues = resolve_managed_path(
                program_root,
                logical_roles.get("action_authorizations"),
                role="logical role action_authorizations",
            )
            issues.extend((*rollover_path_issues, *action_path_issues))
            rollover_records = None
            action_records = None
            if rollover_path is not None:
                rollover_records, load_issues = load_json_lines(rollover_path)
                issues.extend(load_issues)
            if action_path is not None:
                action_records, load_issues = load_json_lines(action_path)
                issues.extend(load_issues)
            rollover_matches = (
                []
                if rollover_records is None
                else [
                    record
                    for record in rollover_records
                    if record.get("rollover_id") == rollover.get("rollover_id")
                ]
            )
            action_matches = (
                []
                if action_records is None
                else [
                    record
                    for record in action_records
                    if record.get("authorization_id")
                    == rollover.get("rollover_authorization_id")
                ]
            )
            if len(rollover_matches) != 1:
                issues.append("status-current rollover must exist exactly once")
            else:
                record = rollover_matches[0]
                delta = record.get("accepted_product_delta")
                delta_paths = (
                    sorted(item.get("path") for item in delta)
                    if isinstance(delta, list)
                    and all(
                        isinstance(item, dict)
                        and isinstance(item.get("path"), str)
                        for item in delta
                    )
                    else None
                )
                inherited_inventory = inherited.get("inherited_paths")
                if (
                    record.get("schema_version")
                    != "implementation-increment-rollover/v1"
                    or _canonical_json_line_sha256(record)
                    != rollover.get("rollover_sha256")
                    or record.get("current_increment_id")
                    != rollover.get("current_increment_id")
                    or record.get("successor_increment_id")
                    != rollover.get("successor_increment_id")
                    or record.get("rollover_authorization_id")
                    != rollover.get("rollover_authorization_id")
                    or record.get("rollover_authorization_sha256")
                    != rollover.get("rollover_authorization_sha256")
                    or record.get("successor_grant_id")
                    != rollover.get("successor_grant_id")
                    or record.get("successor_grant_sha256")
                    != rollover.get("successor_grant_sha256")
                    or record.get("accepted_status_sha256")
                    != rollover.get("prior_status_sha256")
                    or record.get("accepted_status_sequence")
                    != rollover.get("prior_status_sequence")
                    or record.get("submitted_prompt_sha256")
                    != rollover.get("submitted_prompt_sha256")
                    or inherited.get("accepted_product_delta_sha256")
                    != record.get("accepted_product_delta_sha256")
                    or delta_paths is None
                    or not isinstance(inherited_inventory, list)
                    or not all(
                        isinstance(item, str) for item in inherited_inventory
                    )
                    or not set(delta_paths).issubset(
                        set(inherited_inventory)
                    )
                ):
                    issues.append("status-current rollover record binding mismatch")
            if len(action_matches) != 1:
                issues.append("rollover action authorization must exist exactly once")
            elif (
                action_matches[0].get("schema_version")
                != ACTION_AUTHORIZATION_SCHEMA
                or action_matches[0].get("decision") != "authorized"
                or action_matches[0].get("actions") != ["rollover-increment"]
                or action_matches[0].get("current_increment_id")
                != rollover.get("current_increment_id")
                or action_matches[0].get("successor_increment_id")
                != rollover.get("successor_increment_id")
                or _canonical_json_line_sha256(action_matches[0])
                != rollover.get("rollover_authorization_sha256")
            ):
                issues.append("rollover action authorization binding mismatch")
            if isinstance(authority, dict) and (
                authority.get("grant_id") != rollover.get("successor_grant_id")
                or authority.get("grant_sha256")
                != rollover.get("successor_grant_sha256")
                or (
                    isinstance(activation, dict)
                    and authority.get("grant_id")
                    == activation.get("increment_grant_id")
                )
            ):
                issues.append("successor grant must be distinct and rollover-bound")

    brief = status.get("brief_binding")
    if not isinstance(brief, dict):
        issues.append("status brief_binding must be an object")
    else:
        brief_path, brief_issues = resolve_managed_path(
            program_root, brief.get("path"), role="status brief binding"
        )
        issues.extend(brief_issues)
        if brief_path is not None and brief.get("sha256") != sha256_file(brief_path):
            issues.append("brief digest mismatch")
        if brief.get("workspace_sha256") != workspace_sha256:
            issues.append("brief workspace digest mismatch")
        if brief.get("head_commit") != observation.head_commit:
            issues.append("brief head commit mismatch")

    storage = manifest.get("increment_storage")
    increment_id = status.get("current_increment_id")
    if not isinstance(storage, dict) or not isinstance(increment_id, str):
        issues.append("v2 increment storage binding is incomplete")
    else:
        relative_plan = (
            f"{storage.get('root')}/{increment_id}/"
            f"{storage.get('exact_file_plan_filename')}"
        )
        plan_path, plan_path_issues = resolve_managed_path(
            program_root,
            relative_plan,
            role="status-current exact-file plan",
            require_file=False,
        )
        issues.extend(plan_path_issues)
        if plan_path is not None and plan_path.exists():
            if plan_path.is_symlink() or not plan_path.is_file():
                issues.append("status-current exact-file plan must be a regular file")
            else:
                actual = sha256_file(plan_path)
                if actual not in {
                    status.get("pending_exact_file_plan_sha256"),
                    status.get("approved_exact_file_plan_sha256"),
                }:
                    issues.append("plan digest mismatch")
        elif status.get("current_increment_state") not in {"not-started", "preparing"}:
            issues.append("status-current exact-file plan is missing")

    previous = status.get("previous_state")
    sequence = status.get("state_sequence")
    if not isinstance(previous, dict):
        issues.append("v2 active status requires previous_state")
    elif (
        not isinstance(sequence, int)
        or isinstance(sequence, bool)
        or previous.get("schema_version") != STATUS_SCHEMA_V2
        or previous.get("state_sequence") != sequence - 1
        or not isinstance(previous.get("status_sha256"), str)
        or len(previous.get("status_sha256", "")) != 64
    ):
        issues.append("v2 previous state binding is invalid")
    return sorted(set(issues))


def _validate_setup_program_state(
    program_root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
) -> list[str]:
    """Validate the two v3 bootstrap states and their exact authority family."""
    issues: list[str] = []
    sequence = status.get("state_sequence")
    program_state = status.get("program_state")
    increment_state = status.get("current_increment_state")
    blocked_context = status.get("blocked_context")
    is_blocked = (
        program_state == "blocked"
        and increment_state == "blocked"
        and isinstance(blocked_context, dict)
    )
    effective_program_state = (
        blocked_context.get("prior_program_state") if is_blocked else program_state
    )
    effective_increment_state = (
        blocked_context.get("prior_increment_state") if is_blocked else increment_state
    )
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return ["manifest logical_roles must be an object"]
    if sequence == 0:
        if (program_state, increment_state) != (
            "awaiting-program-approval",
            "not-started",
        ):
            issues.append("v3 sequence-zero status is not the setup proposal")
        return issues
    if sequence == 1:
        if (program_state, increment_state) != (
            "active",
            "awaiting-first-increment",
        ):
            issues.append("v3 sequence-one status is not awaiting first increment")
        setup_binding = status.get("setup_activation_binding")
        if (
            not isinstance(setup_binding, dict)
            or setup_binding.get("schema_version")
            != "implementation-setup-activation-status-binding/v1"
        ):
            issues.append("v3 setup activation status binding is invalid")
        return issues
    if not isinstance(sequence, int) or sequence < 2:
        return ["v3 state sequence is invalid"]
    if effective_program_state != "active" and not (
        effective_increment_state == "accepted"
        and effective_program_state in {"awaiting-closure-approval", "closed"}
    ):
        issues.append("v3 executable bootstrap state must be active")
    authority = status.get("current_increment_authority_binding")
    if (
        not isinstance(authority, dict)
        or authority.get("schema_version")
        != "implementation-current-increment-authority-binding/v2"
        or authority.get("kind") != "increment-grant"
        or authority.get("grant_kind")
        not in {"first-increment-start", "successor-rollover"}
        or authority.get("increment_id") != status.get("current_increment_id")
    ):
        issues.append("v3 current increment authority binding is invalid")
        return issues
    grants_path, path_issues = resolve_managed_path(
        program_root,
        logical_roles.get("increment_grants"),
        role="logical role increment_grants",
    )
    issues.extend(path_issues)
    if grants_path is None:
        return issues
    grants, grant_issues = load_json_lines(grants_path)
    issues.extend(grant_issues)
    matches = (
        []
        if grants is None
        else [
            record
            for record in grants
            if record.get("grant_id") == authority.get("grant_id")
        ]
    )
    if len(matches) != 1:
        issues.append("status-current increment grant must exist exactly once")
    else:
        grant = matches[0]
        if (
            grant.get("schema_version") != "implementation-increment-grant/v2"
            or grant.get("grant_kind") != authority.get("grant_kind")
            or grant.get("program_id") != manifest.get("program_id")
            or grant.get("program_revision") != manifest.get("program_revision")
            or grant.get("increment_id") != status.get("current_increment_id")
            or _canonical_json_line_sha256(grant) != authority.get("grant_sha256")
        ):
            issues.append("v3 status-current increment grant binding mismatch")
        else:
            grant_brief = grant.get("brief_binding")
            status_brief = status.get("brief_binding")
            try:
                from program_setup import _increment_brief_binding

                expected_brief = _increment_brief_binding(
                    program_root, manifest, status
                )
            except (ImportError, ValueError) as error:
                issues.append(str(error))
                expected_brief = None
            if grant_brief != expected_brief or status_brief != expected_brief:
                issues.append("v3 status-current increment grant brief binding mismatch")
    if authority.get("grant_kind") == "successor-rollover" and not isinstance(
        status.get("rollover_binding"), dict
    ):
        issues.append("v3 successor grant requires rollover binding")
    approved_plan = status.get("approved_exact_file_plan_sha256")
    pending_plan = status.get("pending_exact_file_plan_sha256")
    if status.get("approval_mode") == "approval:standard" and isinstance(
        approved_plan, str
    ):
        approvals_path, approval_path_issues = resolve_managed_path(
            program_root,
            logical_roles.get("approvals"),
            role="logical role approvals",
        )
        issues.extend(approval_path_issues)
        if approvals_path is not None:
            approvals, approval_issues = load_json_lines(approvals_path)
            issues.extend(approval_issues)
            preparation = status.get("plan_preparation_binding")
            approval_id = (
                preparation.get("plan_approval_event_id")
                if isinstance(preparation, dict)
                else None
            )
            approval_matches = (
                []
                if approvals is None
                else [
                    record
                    for record in approvals
                    if record.get("schema_version")
                    == "implementation-approval/v2"
                    and record.get("type") == "exact-file-plan-approval"
                    and record.get("event_id") == approval_id
                    and record.get("exact_file_plan_sha256") == approved_plan
                    and record.get("increment_grant_id")
                    == authority.get("grant_id")
                ]
            )
            if len(approval_matches) != 1:
                issues.append("v3 approved plan requires one exact v2 plan approval")
    executable_states = {
        "authorized",
        "implementing",
        "reviewing",
        "remediating",
        "verified",
        "awaiting-diff-approval",
        "accepted",
    }
    if effective_increment_state in executable_states:
        try:
            from program_setup import source_gate_satisfaction
        except ImportError as error:
            issues.append(str(error))
            source_gate_satisfaction = None
        baseline_binding = status.get("execution_baseline_binding")
        preparation = status.get("plan_preparation_binding")
        execution_authority = status.get("execution_authorization")
        if not all(
            isinstance(value, dict)
            for value in (baseline_binding, preparation, execution_authority)
        ):
            issues.append("v3 executable state requires plan and baseline authority")
        else:
            baseline_path, baseline_path_issues = resolve_managed_path(
                program_root,
                baseline_binding.get("path"),
                role="status execution baseline binding",
            )
            issues.extend(baseline_path_issues)
            if baseline_path is not None:
                if baseline_binding.get("sha256") != sha256_file(baseline_path):
                    issues.append("execution baseline digest mismatch")
                baseline, baseline_issues = load_json_object(baseline_path)
                issues.extend(baseline_issues)
                if baseline is not None and baseline.get(
                    "current_increment_authority_binding"
                ) != authority:
                    issues.append("execution baseline grant binding mismatch")
            action_path, action_path_issues = resolve_managed_path(
                program_root,
                logical_roles.get("action_authorizations"),
                role="logical role action_authorizations",
            )
            issues.extend(action_path_issues)
            if action_path is not None:
                actions, action_issues = load_json_lines(action_path)
                issues.extend(action_issues)
                authorization_id = execution_authority.get("authorization_id")
                action_matches = (
                    []
                    if actions is None
                    else [
                        record
                        for record in actions
                        if record.get("authorization_id") == authorization_id
                    ]
                )
                gate_satisfaction = None
                if source_gate_satisfaction is not None:
                    try:
                        gate_satisfaction = source_gate_satisfaction(
                            program_root,
                            "before-action-authorization",
                            f"increment:{status.get('current_increment_id')}",
                        )
                    except ValueError as error:
                        issues.append(str(error))
                if len(action_matches) != 1:
                    issues.append(
                        "v3 status-current execution authorization must exist exactly once"
                    )
                else:
                    action = action_matches[0]
                    if (
                        action.get("schema_version")
                        != "implementation-action-authorization/v2"
                        or action.get("exact_file_plan_sha256") != approved_plan
                        or action.get("execution_baseline_sha256")
                        != baseline_binding.get("sha256")
                        or action.get("increment_grant_id")
                        != authority.get("grant_id")
                        or action.get("source_gate_satisfaction")
                        != gate_satisfaction
                        or _canonical_json_line_sha256(action)
                        != execution_authority.get("authorization_sha256")
                    ):
                        issues.append(
                            "v3 status-current execution authorization binding mismatch"
                        )
                status_trigger = {
                    "authorized": "before-action-authorization",
                    "implementing": "before-product-execution",
                    "reviewing": "before-review",
                }.get(str(effective_increment_state))
                if (
                    status_trigger is not None
                    and source_gate_satisfaction is not None
                ):
                    try:
                        expected_status_gate = source_gate_satisfaction(
                            program_root,
                            status_trigger,
                            f"increment:{status.get('current_increment_id')}",
                        )
                    except ValueError as error:
                        issues.append(str(error))
                    else:
                        if status.get("source_gate_satisfaction") != expected_status_gate:
                            issues.append("v3 status source-gate satisfaction mismatch")
        if effective_increment_state == "accepted":
            disposition = status.get("diff_disposition_binding")
            approvals: list[dict[str, Any]] | None = None
            diff_gate = None
            if source_gate_satisfaction is not None:
                try:
                    diff_gate = source_gate_satisfaction(
                        program_root,
                        "before-diff-disposition",
                        f"increment:{status.get('current_increment_id')}",
                    )
                except ValueError as error:
                    issues.append(str(error))
            if not isinstance(disposition, dict):
                issues.append("v3 accepted status lacks diff disposition binding")
            else:
                approvals_path, approval_path_issues = resolve_managed_path(
                    program_root,
                    logical_roles.get("approvals"),
                    role="logical role approvals",
                )
                issues.extend(approval_path_issues)
                if approvals_path is not None:
                    approvals, approval_issues = load_json_lines(approvals_path)
                    issues.extend(approval_issues)
                    diff_matches = (
                        []
                        if approvals is None
                        else [
                            record
                            for record in approvals
                            if record.get("event_id")
                            == disposition.get("approval_event_id")
                            and record.get("type") == "increment-diff-approval"
                        ]
                    )
                    if len(diff_matches) != 1 or (
                        diff_matches
                        and (
                            diff_matches[0].get("schema_version")
                            != "implementation-approval/v2"
                            or diff_matches[0].get("source_gate_satisfaction")
                            != diff_gate
                            or diff_matches[0].get("increment_grant_id")
                            != authority.get("grant_id")
                        )
                    ):
                        issues.append("v3 diff approval authority binding mismatch")
            if effective_program_state == "closed":
                command = status.get("closure_command_binding")
                closure_gate = None
                if source_gate_satisfaction is not None:
                    try:
                        closure_gate = source_gate_satisfaction(
                            program_root,
                            "before-program-closure",
                            f"program:{manifest.get('program_id')}",
                        )
                    except ValueError as error:
                        issues.append(str(error))
                closure_matches = (
                    []
                    if not isinstance(command, dict) or approvals is None
                    else [
                        record
                        for record in approvals
                        if record.get("event_id") == command.get("approval_event_id")
                        and record.get("type") == "program-closure-approval"
                    ]
                )
                if len(closure_matches) != 1 or (
                    closure_matches
                    and (
                        closure_matches[0].get("schema_version")
                        != "implementation-approval/v2"
                        or closure_matches[0].get("source_gate_satisfaction")
                        != closure_gate
                        or status.get("source_gate_satisfaction") != closure_gate
                    )
                ):
                    issues.append("v3 closure approval authority binding mismatch")
    elif approved_plan is not None or (
        effective_increment_state != "awaiting-plan-approval"
        and pending_plan is not None
    ):
        issues.append("v3 pre-authorization plan binding is inconsistent")
    previous = status.get("previous_state")
    if (
        not isinstance(previous, dict)
        or previous.get("schema_version") != STATUS_SCHEMA_V3
        or previous.get("state_sequence") != sequence - 1
        or not isinstance(previous.get("status_sha256"), str)
        or len(previous.get("status_sha256", "")) != 64
    ):
        issues.append("v3 previous state binding is invalid")
    return sorted(set(issues))


def validate_state(
    program_root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    observation: RepositoryObservation,
) -> list[str]:
    """Validate status fields and their current artifact bindings."""
    issues: list[str] = []
    if status.get("schema_version") not in STATUS_SCHEMAS:
        issues.append("unsupported status schema")
    manifest_schema = manifest.get("schema_version")
    status_schema = status.get("schema_version")
    foreign_schemas = (
        LEGACY_ONLY_STATUS_SCHEMAS
        if manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA
        else SETUP_ONLY_STATUS_SCHEMAS
    )
    for schema in sorted(_nested_schema_versions(status) & foreign_schemas):
        issues.append(
            f"manifest family rejects foreign authority schema {schema}"
        )
    if manifest_schema == NEW_PROGRAM_MANIFEST_SCHEMA and status_schema != STATUS_SCHEMA_V2:
        issues.append("manifest v2 requires status v2")
    if manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA and status_schema != STATUS_SCHEMA_V3:
        issues.append("manifest v3 requires status v3")
    if manifest_schema not in {
        NEW_PROGRAM_MANIFEST_SCHEMA,
        SETUP_PROGRAM_MANIFEST_SCHEMA,
    } and status_schema == STATUS_SCHEMA_V3:
        issues.append("pre-v2 manifest rejects status v3")
    sequence = status.get("state_sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        issues.append("state sequence must be a non-negative integer")
    if status.get("program_id") != manifest.get("program_id"):
        issues.append("status program_id mismatch")
    if status.get("program_revision") != manifest.get("program_revision"):
        issues.append("status program_revision mismatch")
    if status.get("program_state") not in PROGRAM_TRANSITIONS:
        issues.append("unknown program state")
    if status.get("current_increment_state") not in INCREMENT_TRANSITIONS and not (
        manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA
        and status.get("current_increment_state") == "awaiting-first-increment"
    ):
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

    if status.get("schema_version") == STATUS_SCHEMA_V2:
        transition_authority = status.get("transition_authority")
        approved_plan = status.get("approved_exact_file_plan_sha256")
        if (
            isinstance(approved_plan, str)
            and approved_plan
            and transition_authority is None
        ):
            issues.append("v2 approved state requires transition authority")
        if transition_authority is not None:
            authority_kind = (
                transition_authority.get("kind")
                if isinstance(transition_authority, dict)
                else None
            )
            event_id = (
                transition_authority.get("event_id")
                if isinstance(transition_authority, dict)
                else None
            )
            checkpoint_id = (
                transition_authority.get("checkpoint_id")
                if isinstance(transition_authority, dict)
                else None
            )
            authorization_id = (
                transition_authority.get("authorization_id")
                if isinstance(transition_authority, dict)
                else None
            )
            authority_invalid = (
                authority_kind
                not in {
                    "approval-event",
                    "action-authorization",
                    "blocked-context",
                }
                or not isinstance(event_id, str)
                or not event_id
                or (
                    checkpoint_id is not None
                    and (not isinstance(checkpoint_id, str) or not checkpoint_id)
                )
                or (
                    authority_kind == "approval-event"
                    and authorization_id is not None
                )
                or (
                    authority_kind == "blocked-context"
                    and authorization_id is not None
                )
                or (
                    authority_kind == "action-authorization"
                    and (
                        not isinstance(authorization_id, str)
                        or not authorization_id
                    )
                )
            )
            if authority_invalid:
                issues.append("v2 transition authority is invalid")
        execution_authorization = status.get("execution_authorization")
        if execution_authorization is not None and (
            not isinstance(execution_authorization, dict)
            or not isinstance(execution_authorization.get("authorization_id"), str)
            or not execution_authorization.get("authorization_id")
            or not isinstance(execution_authorization.get("scope"), str)
            or not execution_authorization.get("scope")
        ):
            issues.append("v2 execution authorization binding is invalid")

    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return sorted(set([*issues, "manifest logical_roles must be an object"]))
    if manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA:
        if status.get("program_state") == "blocked" or status.get(
            "current_increment_state"
        ) == "blocked":
            try:
                from blocked_recovery import validate_blocked_context

                issues.extend(
                    validate_blocked_context(program_root, status, observation)
                )
            except ImportError as error:
                issues.append(str(error))
        if status.get("block_resolution_binding") is not None:
            try:
                from blocked_recovery import validate_block_resolution_history

                issues.extend(
                    validate_block_resolution_history(
                        program_root, status, observation
                    )
                )
            except ImportError as error:
                issues.append(str(error))
        issues.extend(_validate_setup_program_state(program_root, manifest, status))
        return sorted(set(issues))
    if manifest.get("schema_version") == NEW_PROGRAM_MANIFEST_SCHEMA:
        if status.get("program_state") == "blocked" or status.get(
            "current_increment_state"
        ) == "blocked":
            try:
                from blocked_recovery import validate_blocked_context

                issues.extend(
                    validate_blocked_context(program_root, status, observation)
                )
            except ImportError as error:
                issues.append(str(error))
        if status.get("block_resolution_binding") is not None:
            try:
                from blocked_recovery import validate_block_resolution_history

                issues.extend(
                    validate_block_resolution_history(
                        program_root, status, observation
                    )
                )
            except ImportError as error:
                issues.append(str(error))
        issues.extend(
            _validate_new_program_state(
                program_root, manifest, status, observation
            )
        )
        return sorted(set(issues))
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
            if previous.get("schema_version") not in STATUS_SCHEMAS:
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
    if "closure_storage" in manifest:
        try:
            closure_paths = resolve_program_closure_paths(root)
        except ValueError as error:
            issues.append(str(error))
            closure_paths = {}
        path_fields = (
            ("reconciliation", "reconciliation_path", "reconciliation_sha256"),
            ("packet", "closure_packet_path", "closure_packet_sha256"),
        )
        for path_key, path_field, digest_field in path_fields:
            path = closure_paths.get(path_key)
            if path is None:
                continue
            relative_path = path.relative_to(root).as_posix()
            if binding.get(path_field) != relative_path:
                issues.append(f"closure {path_field} mismatch")
            if not path.is_file() or path.is_symlink():
                issues.append(f"closure {path_field} must be a regular file")
            elif binding.get(digest_field) != sha256_file(path):
                issues.append(f"closure {digest_field} mismatch")
    else:
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
    issues: list[str] = []
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
    validation_mode = APPROVED_VALIDATION_MODE
    if (
        manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
        and status is not None
        and status.get("schema_version") == STATUS_SCHEMA_V3
        and status.get("state_sequence") == 0
    ):
        validation_mode = PROPOSAL_VALIDATION_MODE
    issues.extend(
        validate_program_authority(root, validation_mode=validation_mode)
    )
    execution_workspace_validated = False
    if status is not None:
        issues.extend(validate_state(root, manifest, status, observation))
        approved_plan = status.get("approved_exact_file_plan_sha256")
        if (
            status.get("schema_version") == STATUS_SCHEMA_V2
            and status.get("approval_mode") == "approval:standard"
            and isinstance(approved_plan, str)
            and approved_plan
        ):
            approvals_path, approval_path_issues = resolve_managed_path(
                root,
                logical_roles.get("approvals"),
                role="logical role approvals",
            )
            issues.extend(approval_path_issues)
            if approvals_path is not None:
                approvals, approval_load_issues = load_json_lines(approvals_path)
                issues.extend(approval_load_issues)
                if approvals is not None:
                    try:
                        plan_approval = _binding_from_state(
                            manifest,
                            status,
                            observation,
                            event_type="exact-file-plan-approval",
                        )
                    except (KeyError, TypeError, ValueError):
                        issues.append("v2 approved plan binding is incomplete")
                    else:
                        if validate_approval_binding(approvals, plan_approval):
                            issues.append(
                                "v2 approved plan requires exact plan approval"
                            )
        baseline_states = {
            "authorized",
            "implementing",
            "reviewing",
            "remediating",
            "verified",
            "awaiting-diff-approval",
            "accepted",
        }
        if (
            (
                status.get("schema_version"),
                manifest.get("schema_version"),
            )
            in {
                (STATUS_SCHEMA_V2, NEW_PROGRAM_MANIFEST_SCHEMA),
                (STATUS_SCHEMA_V3, SETUP_PROGRAM_MANIFEST_SCHEMA),
            }
            and status.get("current_increment_state") in baseline_states
        ):
            baseline_binding = status.get("execution_baseline_binding")
            baseline_path = None
            if not isinstance(baseline_binding, dict):
                issues.append("v2 executable state requires execution baseline binding")
            else:
                baseline_path, baseline_path_issues = resolve_managed_path(
                    root,
                    baseline_binding.get("path"),
                    role="status execution baseline binding",
                )
                issues.extend(baseline_path_issues)
                if (
                    baseline_path is not None
                    and baseline_binding.get("sha256") != sha256_file(baseline_path)
                ):
                    issues.append("execution baseline digest mismatch")
            if baseline_path is not None:
                baseline_value, baseline_issues = load_json_object(baseline_path)
                issues.extend(baseline_issues)
                if baseline_value is not None:
                    try:
                        from repository_preparation import (
                            REPOSITORY_INSPECTION_SCHEMA,
                            RepositoryInspection,
                            execution_baseline_from_value,
                            validate_execution_workspace,
                        )

                        baseline = execution_baseline_from_value(baseline_value)
                    except (ImportError, ValueError) as error:
                        issues.append(str(error))
                    else:
                        if baseline.program_id != manifest.get("program_id"):
                            issues.append("execution baseline program_id mismatch")
                        if baseline.program_revision != manifest.get("program_revision"):
                            issues.append("execution baseline program_revision mismatch")
                        if baseline.increment_id != status.get("current_increment_id"):
                            issues.append("execution baseline increment_id mismatch")
                        if baseline.exact_file_plan_sha256 != status.get(
                            "approved_exact_file_plan_sha256"
                        ):
                            issues.append("execution baseline plan digest mismatch")
                        if baseline.current_increment_authority_binding != status.get(
                            "current_increment_authority_binding"
                        ):
                            issues.append("execution baseline grant binding mismatch")
                        inspection = RepositoryInspection(
                            schema_version=REPOSITORY_INSPECTION_SCHEMA,
                            observation=observation,
                            git_directory="",
                            git_common_directory="",
                            selected_base_is_ancestor=True,
                            status_format="porcelain-v2-z",
                        )
                        assessment = validate_execution_workspace(
                            root,
                            baseline,
                            inspection,
                            increment_state=str(status["current_increment_state"]),
                        )
                        issues.extend(assessment.issues)
                        execution_transition = status.get(
                            "execution_transition_binding"
                        )
                        current_increment_state = status.get(
                            "current_increment_state"
                        )
                        if current_increment_state in {
                            "implementing",
                            "reviewing",
                            "remediating",
                            "verified",
                            "awaiting-diff-approval",
                            "accepted",
                        }:
                            expected_target = (
                                "implementing"
                                if current_increment_state == "implementing"
                                else "reviewing"
                            )
                            allowed_prior_states = (
                                {"authorized"}
                                if expected_target == "implementing"
                                else {"implementing", "remediating"}
                            )
                            execution_authorization = status.get(
                                "execution_authorization"
                            )
                            authorization_id = (
                                execution_authorization.get("authorization_id")
                                if isinstance(execution_authorization, dict)
                                else None
                            )
                            transition_valid = (
                                isinstance(execution_transition, dict)
                                and execution_transition.get("schema_version")
                                == "implementation-execution-transition/v1"
                                and execution_transition.get(
                                    "prior_increment_state"
                                )
                                in allowed_prior_states
                                and execution_transition.get(
                                    "target_increment_state"
                                )
                                == expected_target
                                and execution_transition.get("authorization_id")
                                == authorization_id
                                and isinstance(
                                    execution_transition.get("prior_status_sha256"),
                                    str,
                                )
                                and len(execution_transition["prior_status_sha256"])
                                == 64
                                and isinstance(
                                    execution_transition.get(
                                        "product_delta_sha256"
                                    ),
                                    str,
                                )
                                and len(
                                    execution_transition["product_delta_sha256"]
                                )
                                == 64
                                and (
                                    current_increment_state
                                    in {"implementing", "remediating"}
                                    or execution_transition.get(
                                        "product_delta_sha256"
                                    )
                                    == assessment.product_delta_sha256
                                )
                            )
                            if transition_valid:
                                event_seed = {
                                    "program_id": status["program_id"],
                                    "program_revision": status[
                                        "program_revision"
                                    ],
                                    "increment_id": status[
                                        "current_increment_id"
                                    ],
                                    "prior_status_sha256": execution_transition[
                                        "prior_status_sha256"
                                    ],
                                    "prior_increment_state": execution_transition[
                                        "prior_increment_state"
                                    ],
                                    "target_increment_state": expected_target,
                                    "product_delta_sha256": execution_transition[
                                        "product_delta_sha256"
                                    ],
                                    "authorization_id": authorization_id,
                                }
                                if (
                                    execution_transition.get(
                                        "prior_increment_state"
                                    )
                                    == "remediating"
                                ):
                                    event_seed["review_remediation_sha256"] = (
                                        execution_transition.get(
                                            "review_remediation_sha256"
                                        )
                                    )
                                expected_event_id = _derived_identifier(
                                    "execution-transition", event_seed
                                )
                                transition_valid = execution_transition.get(
                                    "event_id"
                                ) == expected_event_id
                            if not transition_valid:
                                issues.append(
                                    "execution transition binding is invalid"
                                )
                        if (
                            status.get("current_increment_state")
                            in {
                                "reviewing",
                                "verified",
                                "awaiting-diff-approval",
                                "accepted",
                            }
                            and isinstance(execution_transition, dict)
                            and execution_transition.get("target_increment_state")
                            == "reviewing"
                            and execution_transition.get("product_delta_sha256")
                            != assessment.product_delta_sha256
                        ):
                            issues.append(
                                "reviewed product delta differs from its status binding"
                            )
                        remediation_history = status.get(
                            "review_remediation_binding"
                        )
                        post_remediation_transition = (
                            isinstance(execution_transition, dict)
                            and execution_transition.get("prior_increment_state")
                            == "remediating"
                        )
                        if (
                            current_increment_state
                            in {
                                "reviewing",
                                "verified",
                                "awaiting-diff-approval",
                                "accepted",
                            }
                            and (
                                post_remediation_transition
                                or remediation_history is not None
                            )
                        ):
                            remediation_history_valid = (
                                post_remediation_transition
                                and isinstance(remediation_history, dict)
                                and remediation_history.get("schema_version")
                                == "implementation-review-remediation/v1"
                                and execution_transition.get(
                                    "review_remediation_sha256"
                                )
                                == hashlib.sha256(
                                    _canonical_json_bytes(remediation_history)
                                ).hexdigest()
                            )
                            if not remediation_history_valid:
                                issues.append(
                                    "review remediation history binding is invalid"
                                )
                        if current_increment_state == "remediating":
                            remediation = status.get("review_remediation_binding")
                            review_binding = status.get("review_binding")
                            transition_authority = status.get(
                                "transition_authority"
                            )
                            unresolved_finding_ids = (
                                remediation.get("unresolved_finding_ids")
                                if isinstance(remediation, dict)
                                else None
                            )
                            initial_product_delta_sha256 = (
                                remediation.get("initial_product_delta_sha256")
                                if isinstance(remediation, dict)
                                else None
                            )
                            remediation_valid = (
                                isinstance(remediation, dict)
                                and remediation.get("schema_version")
                                == "implementation-review-remediation/v1"
                                and isinstance(
                                    initial_product_delta_sha256, str
                                )
                                and len(initial_product_delta_sha256) == 64
                                and all(
                                    character in "0123456789abcdef"
                                    for character in initial_product_delta_sha256
                                )
                                and isinstance(unresolved_finding_ids, list)
                                and bool(unresolved_finding_ids)
                                and all(
                                    isinstance(finding_id, str) and finding_id
                                    for finding_id in unresolved_finding_ids
                                )
                                and isinstance(review_binding, dict)
                                and review_binding.get("schema_version")
                                == "implementation-review-remediation/v1"
                                and review_binding.get("candidate_sha256")
                                == initial_product_delta_sha256
                                and review_binding.get(
                                    "unresolved_material_findings"
                                )
                                == len(unresolved_finding_ids)
                                and review_binding.get("finding_ids")
                                == unresolved_finding_ids
                            )
                            if not remediation_valid:
                                issues.append(
                                    "remediating state requires an exact review "
                                    "remediation binding"
                                )
                            remediation_authority_valid = (
                                isinstance(remediation, dict)
                                and isinstance(transition_authority, dict)
                                and transition_authority.get("kind")
                                == "action-authorization"
                                and transition_authority.get("authorization_id")
                                == authorization_id
                                and transition_authority.get("event_id")
                                == _derived_identifier(
                                    "review-remediation", remediation
                                )
                            )
                            if not remediation_authority_valid:
                                issues.append(
                                    "review remediation transition authority is invalid"
                                )
                        execution_workspace_validated = True
            execution_authorization = status.get("execution_authorization")
            preparation = status.get("plan_preparation_binding")
            if not isinstance(execution_authorization, dict) or not isinstance(
                preparation, dict
            ):
                issues.append("v2 executable state requires plan-bound action authority")
            else:
                authorization_id = execution_authorization.get("authorization_id")
                if authorization_id != preparation.get("action_authorization_id"):
                    issues.append("execution authorization id mismatch")
                actions_path, action_path_issues = resolve_managed_path(
                    root,
                    logical_roles.get("action_authorizations"),
                    role="logical role action_authorizations",
                )
                issues.extend(action_path_issues)
                if actions_path is not None:
                    actions, action_issues = load_json_lines(actions_path)
                    issues.extend(action_issues)
                    matches = (
                        []
                        if actions is None
                        else [
                            record
                            for record in actions
                            if record.get("authorization_id") == authorization_id
                        ]
                    )
                    if len(matches) != 1:
                        issues.append(
                            "status-current execution authorization must exist exactly once"
                        )
                    elif (
                        _canonical_json_line_sha256(matches[0])
                        != (
                            execution_authorization.get("authorization_sha256")
                            if status.get("schema_version") == STATUS_SCHEMA_V3
                            else preparation.get("action_authorization_sha256")
                        )
                        or matches[0].get("exact_file_plan_sha256")
                        != status.get("approved_exact_file_plan_sha256")
                        or matches[0].get("execution_baseline_sha256")
                        != (
                            baseline_binding.get("sha256")
                            if isinstance(baseline_binding, dict)
                            else None
                        )
                    ):
                        issues.append("status-current execution authorization binding mismatch")
            if status.get("current_increment_state") in {
                "verified",
                "awaiting-diff-approval",
                "accepted",
            }:
                review_preparation = status.get("review_preparation_binding")
                evidence_binding = status.get("review_evidence_binding")
                packet_binding = status.get("review_packet_binding")
                if not all(
                    isinstance(item, dict)
                    for item in (
                        review_preparation,
                        evidence_binding,
                        packet_binding,
                    )
                ):
                    issues.append("verified state requires review preparation bindings")
                else:
                    storage = manifest.get("increment_storage")
                    if not isinstance(storage, dict):
                        issues.append("review storage descriptor is missing")
                    else:
                        expected_paths = {
                            "evidence": (
                                f"{storage.get('root')}/{status.get('current_increment_id')}/"
                                f"{storage.get('review_evidence_filename')}"
                            ),
                            "packet": (
                                f"{storage.get('root')}/{status.get('current_increment_id')}/"
                                f"{storage.get('review_packet_filename')}"
                            ),
                        }
                        for label, binding in (
                            ("evidence", evidence_binding),
                            ("packet", packet_binding),
                        ):
                            if binding.get("path") != expected_paths[label]:
                                issues.append(f"review {label} path is not manifest-derived")
                                continue
                            path, path_issues = resolve_managed_path(
                                root,
                                binding.get("path"),
                                role=f"status review {label} binding",
                            )
                            issues.extend(path_issues)
                            if path is not None and binding.get("sha256") != sha256_file(path):
                                issues.append(f"review {label} digest mismatch")
                            if binding.get("candidate_sha256") != review_preparation.get(
                                "product_delta_sha256"
                            ):
                                issues.append(f"review {label} candidate binding mismatch")
            if status.get("current_increment_state") == "accepted":
                disposition = status.get("diff_disposition_binding")
                transition_authority = status.get("transition_authority")
                program_state = status.get("program_state")
                diff_transition_is_current = program_state == "active"
                if (
                    not isinstance(disposition, dict)
                    or disposition.get("schema_version")
                    != "implementation-diff-disposition-binding/v1"
                    or disposition.get("decision") != "accept-stop"
                    or disposition.get("exact_file_plan_sha256")
                    != status.get("approved_exact_file_plan_sha256")
                    or disposition.get("execution_baseline_sha256")
                    != (
                        baseline_binding.get("sha256")
                        if isinstance(baseline_binding, dict)
                        else None
                    )
                    or disposition.get("accepted_product_delta_sha256")
                    != (
                        status.get("execution_transition_binding", {}).get(
                            "product_delta_sha256"
                        )
                        if isinstance(status.get("execution_transition_binding"), dict)
                        else None
                    )
                    or (
                        diff_transition_is_current
                        and (
                            not isinstance(transition_authority, dict)
                            or transition_authority.get("kind") != "approval-event"
                            or transition_authority.get("event_id")
                            != disposition.get("approval_event_id")
                            or transition_authority.get("checkpoint_id")
                            != disposition.get("checkpoint_id")
                        )
                    )
                ):
                    issues.append("accepted status diff disposition binding is invalid")
                else:
                    approvals_path, approval_path_issues = resolve_managed_path(
                        root,
                        logical_roles.get("approvals"),
                        role="logical role approvals",
                    )
                    issues.extend(approval_path_issues)
                    if approvals_path is not None:
                        approvals, approval_issues = load_json_lines(approvals_path)
                        issues.extend(approval_issues)
                        matches = (
                            []
                            if approvals is None
                            else [
                                record
                                for record in approvals
                                if record.get("event_id")
                                == disposition.get("approval_event_id")
                                and record.get("type") == "increment-diff-approval"
                                and record.get("decision") == "approved"
                                and record.get("diff_decision") == "accept-stop"
                                and record.get("base_seed_sha256")
                                == disposition.get("base_seed_sha256")
                            ]
                        )
                        if len(matches) != 1:
                            issues.append(
                                "accepted status requires one exact diff approval"
                            )
                if program_state in {"awaiting-closure-approval", "closed"}:
                    issues.extend(_validate_closure_readiness(root, manifest, status))
                    preparation = status.get("closure_preparation_binding")
                    if (
                        not isinstance(preparation, dict)
                        or preparation.get("schema_version")
                        != "implementation-closure-preparation/v1"
                    ):
                        issues.append("closure preparation binding is invalid")
                    else:
                        closure = status.get("closure_binding")
                        if (
                            not isinstance(closure, dict)
                            or preparation.get("reconciliation_sha256")
                            != closure.get("reconciliation_sha256")
                            or preparation.get("closure_packet_sha256")
                            != closure.get("closure_packet_sha256")
                        ):
                            issues.append("closure preparation binding is invalid")
                    if program_state == "awaiting-closure-approval":
                        if (
                            not isinstance(transition_authority, dict)
                            or transition_authority.get("kind")
                            != "action-authorization"
                        ):
                            issues.append(
                                "awaiting closure status requires typed preparation authority"
                            )
                    else:
                        command = status.get("closure_command_binding")
                        if (
                            not isinstance(command, dict)
                            or command.get("schema_version")
                            != "implementation-program-closure-command-binding/v1"
                            or not isinstance(transition_authority, dict)
                            or transition_authority.get("kind") != "approval-event"
                            or transition_authority.get("event_id")
                            != command.get("approval_event_id")
                            or transition_authority.get("checkpoint_id")
                            != command.get("checkpoint_id")
                        ):
                            issues.append("closed status closure command binding is invalid")
    workspace_observation = observation
    if status is not None and isinstance(status.get("rollover_binding"), dict):
        try:
            from program_rollover import validated_inherited_paths

            inherited_paths = set(
                validated_inherited_paths(root, status, observation)
            )
        except (ImportError, KeyError, OSError, TypeError, ValueError) as error:
            issues.append(str(error))
            inherited_paths = set()
        if inherited_paths:
            workspace_observation = replace(
                observation,
                staged_paths=tuple(
                    path
                    for path in observation.staged_paths
                    if path not in inherited_paths
                ),
                modified_paths=tuple(
                    path
                    for path in observation.modified_paths
                    if path not in inherited_paths
                ),
                untracked_paths=tuple(
                    path
                    for path in observation.untracked_paths
                    if path not in inherited_paths
                ),
                conflicted_paths=tuple(
                    path
                    for path in observation.conflicted_paths
                    if path not in inherited_paths
                ),
            )
    if (
        status is not None
        and status.get("program_state") == "blocked"
        and isinstance(status.get("blocked_context"), dict)
    ):
        try:
            from blocked_recovery import blocked_workspace_paths

            blocked_paths = set(blocked_workspace_paths(root, status))
        except (ImportError, KeyError, OSError, TypeError, ValueError) as error:
            issues.append(str(error))
            blocked_paths = set()
        if blocked_paths:
            workspace_observation = replace(
                workspace_observation,
                staged_paths=tuple(
                    path
                    for path in workspace_observation.staged_paths
                    if path not in blocked_paths
                ),
                modified_paths=tuple(
                    path
                    for path in workspace_observation.modified_paths
                    if path not in blocked_paths
                ),
                untracked_paths=tuple(
                    path
                    for path in workspace_observation.untracked_paths
                    if path not in blocked_paths
                ),
                conflicted_paths=tuple(
                    path
                    for path in workspace_observation.conflicted_paths
                    if path not in blocked_paths
                ),
            )
    if workspace is not None:
        if workspace.get("program_id") != manifest.get("program_id"):
            issues.append("workspace program_id mismatch")
        if workspace.get("program_revision") != manifest.get("program_revision"):
            issues.append("workspace program_revision mismatch")
        if (
            manifest.get("schema_version")
            in {NEW_PROGRAM_MANIFEST_SCHEMA, SETUP_PROGRAM_MANIFEST_SCHEMA}
            and workspace.get("schema_version")
            == "implementation-workspace-proposal/v1"
        ):
            observable_workspace = dict(workspace)
            observable_workspace["schema_version"] = WORKSPACE_SCHEMA
            if not execution_workspace_validated:
                issues.extend(
                    validate_workspace_selection(
                        observable_workspace, workspace_observation
                    )
                )
            activation = status.get("activation_binding") if status is not None else None
            if isinstance(activation, dict):
                approvals_path, approval_path_issues = resolve_managed_path(
                    root,
                    logical_roles.get("approvals"),
                    role="logical role approvals",
                )
                issues.extend(approval_path_issues)
                if approvals_path is not None:
                    approvals, approval_issues = load_json_lines(approvals_path)
                    issues.extend(approval_issues)
                    if approvals is not None:
                        expected = (
                            (
                                "program-approval",
                                activation.get("program_approval_event_id"),
                            ),
                            (
                                "workspace-selection-approval",
                                activation.get("workspace_approval_event_id"),
                            ),
                        )
                        for event_type, event_id in expected:
                            matches = [
                                record
                                for record in approvals
                                if record.get("type") == event_type
                                and record.get("event_id") == event_id
                                and record.get("decision") == "approved"
                                and record.get("submitted_prompt_sha256")
                                == activation.get("submitted_prompt_sha256")
                            ]
                            if len(matches) != 1:
                                issues.append(
                                    f"activation {event_type} record must exist exactly once"
                                )
        elif not execution_workspace_validated:
            issues.extend(
                validate_workspace_selection(workspace, workspace_observation)
            )
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


def _fsync_directory(path: Path) -> None:
    if _WINDOWS:
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _windows_mutex_name(path: Path) -> str:
    normalized = os.path.normcase(os.path.abspath(path))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"Local\\implementation-staged-plans-{digest}"


def _windows_api_error(operation: str) -> OSError:
    error_code = _ctypes.get_last_error()
    return OSError(error_code, f"{operation}: {_ctypes.FormatError(error_code)}")


def _acquire_advisory_lock(path: Path) -> object:
    if _WINDOWS:
        if _kernel32 is None:
            raise OSError("Windows file locking is unavailable")
        handle = _kernel32.CreateMutexW(None, False, _windows_mutex_name(path))
        if not handle:
            raise _windows_api_error("CreateMutexW failed")
        wait_result = _kernel32.WaitForSingleObject(handle, 0xFFFFFFFF)
        if wait_result in {0x00000000, 0x00000080}:
            return handle
        _kernel32.CloseHandle(handle)
        raise OSError(f"WaitForSingleObject failed with result {wait_result}")
    if _fcntl is None:
        raise OSError("POSIX file locking is unavailable")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        _fcntl.flock(descriptor, _fcntl.LOCK_EX)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _release_advisory_lock(lock: object) -> None:
    if _WINDOWS:
        if _kernel32 is None:
            raise OSError("Windows file locking is unavailable")
        released = _kernel32.ReleaseMutex(lock)
        closed = _kernel32.CloseHandle(lock)
        if not released:
            raise _windows_api_error("ReleaseMutex failed")
        if not closed:
            raise _windows_api_error("CloseHandle failed")
        return
    if _fcntl is None:
        raise OSError("POSIX file locking is unavailable")
    descriptor = int(lock)
    try:
        _fcntl.flock(descriptor, _fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _atomic_replace_bytes(
    path: Path, payload: bytes, expected_sha256: str
) -> AtomicWriteReceipt:
    _validate_atomic_target(path)
    if not path.is_file():
        raise ValueError(f"{path}: target must be an existing regular file")
    advisory_lock = _acquire_advisory_lock(path)
    try:
        if _WINDOWS:
            target_descriptor = os.open(
                path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            )
            try:
                target_stat = os.fstat(target_descriptor)
            finally:
                os.close(target_descriptor)
        else:
            target_stat = os.fstat(int(advisory_lock))
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
            current_stat = path.stat(follow_symlinks=False)
            current_sha256 = sha256_file(path)
            if (
                (current_stat.st_dev, current_stat.st_ino)
                != (target_stat.st_dev, target_stat.st_ino)
                or current_sha256 != expected_sha256
            ):
                raise ValueError(
                    f"{path}: digest changed; expected {expected_sha256}, "
                    f"found {current_sha256}"
                )
            os.replace(temporary_path, path)
            temporary_path = None
            _fsync_directory(path.parent)
            written_sha256 = hashlib.sha256(payload).hexdigest()
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
    finally:
        _release_advisory_lock(advisory_lock)
    return AtomicWriteReceipt(prior_sha256, written_sha256)


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
    identifier_fields = (
        "event_id",
        "authorization_id",
        "grant_id",
        "rollover_id",
        "resolution_id",
        "decision_id",
    )

    def record_identifier(record: dict[str, object]) -> object:
        return next(
            (record.get(field) for field in identifier_fields if field in record),
            None,
        )

    identifiers = {record_identifier(record) for record in records}
    identifier = record_identifier(value)
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

    status_schema = status.get("schema_version")
    if status_schema == STATUS_SCHEMA_V2:
        if selection.authority_kind != "approval-event":
            raise ValueError("v2 workspace selection requires approval-event authority")
        if selection.action_authorization_id is not None:
            raise ValueError("v2 governance selection cannot claim workspace creation authority")
    else:
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
        "schema_version": (
            WORKSPACE_SCHEMA_V2 if status_schema == STATUS_SCHEMA_V2 else WORKSPACE_SCHEMA
        ),
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
    }
    if status_schema == STATUS_SCHEMA_V2:
        workspace["selection_authority"] = {
            "kind": "approval-event",
            "event_id": selection.approval_event_id,
        }
    else:
        workspace["action_authorization_id"] = selection.action_authorization_id
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
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, status_path = _load_role(root, manifest, "status")
    if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA:
        raise ValueError(
            "typed-v3-lifecycle-transition-required: use the owning v3 transaction"
        )
    if manifest.get("schema_version") == NEW_PROGRAM_MANIFEST_SCHEMA:
        current_program = status.get("program_state")
        current_increment = status.get("current_increment_state")
        if (
            current_program == "blocked"
            or current_increment == "blocked"
            or request.target_program_state == "blocked"
            or request.target_increment_state == "blocked"
        ):
            raise ValueError(
                "blocked-transaction-required: generic blocked transitions are disabled"
            )
        if (
            request.target_program_state == "superseded"
            or request.target_increment_state == "superseded"
        ):
            raise ValueError(
                "program-revision-workflow-required: generic supersession is disabled"
            )
    if (
        manifest.get("schema_version") == NEW_PROGRAM_MANIFEST_SCHEMA
        and status.get("current_increment_state") == "reviewing"
        and request.target_increment_state == "verified"
    ):
        raise ValueError(
            "review-preparation-required: use the typed review evidence and packet sink"
        )
    if (
        manifest.get("schema_version") == NEW_PROGRAM_MANIFEST_SCHEMA
        and (
            (
                status.get("current_increment_state") == "reviewing"
                and request.target_increment_state == "remediating"
            )
            or (
                status.get("current_increment_state") == "remediating"
                and request.target_increment_state == "reviewing"
            )
        )
    ):
        raise ValueError(
            "typed-review-remediation-required: use the typed review remediation sink"
        )
    if (
        manifest.get("schema_version") == NEW_PROGRAM_MANIFEST_SCHEMA
        and status.get("current_increment_state") == "awaiting-diff-approval"
        and request.target_increment_state == "accepted"
    ):
        raise ValueError(
            "typed-diff-disposition-required: use the exact prompt-bound accept-stop sink"
        )
    if (
        manifest.get("schema_version") == NEW_PROGRAM_MANIFEST_SCHEMA
        and (
            (
                status.get("program_state") == "active"
                and request.target_program_state == "awaiting-closure-approval"
            )
            or (
                status.get("program_state") == "awaiting-closure-approval"
                and request.target_program_state == "closed"
            )
        )
    ):
        raise ValueError(
            "typed-program-closure-required: use the exact closure preparation or approval sink"
        )
    issues = validate_state_authority(root, observation)
    if issues:
        raise ValueError("; ".join(issues))
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
    status_schema = status.get("schema_version")
    authority_kind = transition_authority_policy(
        str(current_program),
        request.target_program_state,
        str(current_increment_state),
        request.target_increment_state,
    )
    if status_schema == STATUS_SCHEMA_V2 and request.authority_kind != authority_kind:
        raise ValueError(f"transition requires {authority_kind} authority")
    if status_schema != STATUS_SCHEMA_V2 or authority_kind == "action-authorization":
        action = _action_binding_from_approval(
            approval, "modify-workspace", action_scope
        )
        authorization = decide_action_authorization(authorizations, action)
        if not authorization.authorized:
            raise ValueError("; ".join(authorization.issues))
        if authorization.authorization_id != request.action_authorization_id:
            raise ValueError("action authorization id mismatch")
    elif request.action_authorization_id is not None:
        raise ValueError("approval-driven governance transition cannot claim action authority")
    if (
        status_schema == STATUS_SCHEMA_V2
        and current_increment_state == "awaiting-plan-approval"
        and request.target_increment_state == "authorized"
        and (
            not isinstance(request.execution_authorization_id, str)
            or not request.execution_authorization_id
        )
    ):
        raise ValueError("v2 plan approval requires an expected execution authorization id")

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
    )
    if status_schema == STATUS_SCHEMA_V2:
        transition_authority: dict[str, object] = {
            "kind": authority_kind,
            "event_id": request.transition_event_id,
        }
        if request.checkpoint_id is not None:
            transition_authority["checkpoint_id"] = request.checkpoint_id
        if authority_kind == "action-authorization":
            transition_authority["authorization_id"] = request.action_authorization_id
        new_status["transition_authority"] = transition_authority
        if request.execution_authorization_id is not None:
            new_status["execution_authorization"] = {
                "authorization_id": request.execution_authorization_id,
                "scope": action_scope,
            }
    else:
        new_status["transition_authorization"] = {
            "event_id": request.transition_event_id,
            "action_authorization_id": request.action_authorization_id,
        }
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
                action_authorization_id=request.get("action_authorization_id"),
                authority_kind=request.get("authority_kind", "action-authorization"),
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
