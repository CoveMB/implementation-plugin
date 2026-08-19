#!/usr/bin/env python3
"""Persist or recover one prompt-bound new-program activation transaction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from program_authority import (
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
)
from program_launch import (
    render_program_launch_prompt,
    validate_submitted_program_launch_prompt,
)
from repository_preparation import (
    REQUIRED_PLAN_SECTIONS,
    RepositoryInspection,
    _section_body,
    _validate_plan_naming_table,
    execution_baseline_from_value,
    inspect_repository,
    parse_exact_file_map,
    validate_execution_workspace,
)
from state_authority import (
    ACTION_AUTHORIZATION_SCHEMA,
    APPROVAL_SCHEMA,
    ExactFileMap,
    RepositoryObservation,
    atomic_append_json_line,
    atomic_replace_json,
    required_future_lifecycle_writes,
    validate_required_managed_file_map,
    validate_state_authority,
)
from task_prompt import parse_exact_prompt, render_exact_prompt


INCREMENT_GRANT_SCHEMA = "implementation-increment-grant/v1"
ACTIVATION_BINDING_SCHEMA = "implementation-program-activation-binding/v1"
CURRENT_INCREMENT_AUTHORITY_SCHEMA = (
    "implementation-current-increment-authority-binding/v1"
)
EXECUTION_BASELINE_SCHEMA = "implementation-execution-baseline/v1"
PLAN_PREPARATION_SCHEMA = "implementation-exact-plan-preparation/v1"
EXECUTION_TRANSITION_SCHEMA = "implementation-execution-transition/v1"


@dataclass(frozen=True)
class ActivationReceipt:
    program_id: str
    increment_id: str
    increment_state: str
    status_sha256: str
    program_approval_event_id: str
    workspace_approval_event_id: str
    increment_grant_id: str
    recovered: bool


@dataclass(frozen=True)
class ExactPlanPreparationReceipt:
    plan_path: str
    plan_sha256: str
    increment_state: str
    plan_prompt: str | None
    recovered: bool


@dataclass(frozen=True)
class ExecutionMaterializationReceipt:
    plan_sha256: str
    baseline_sha256: str
    authorization_id: str
    increment_state: str
    status_sha256: str
    recovered: bool


@dataclass(frozen=True)
class ExecutionTransitionReceipt:
    prior_state: str
    increment_state: str
    status_sha256: str
    product_delta_sha256: str
    recovered: bool


@dataclass(frozen=True)
class _PlanCandidate:
    plan_path: Path
    plan_bytes: bytes
    plan_sha256: str
    baseline_path: Path
    baseline: dict[str, object]
    baseline_bytes: bytes
    baseline_sha256: str
    action_record: dict[str, object]
    action_sha256: str
    plan_approval_record: dict[str, object] | None
    awaiting_status: dict[str, object] | None
    authorized_status: dict[str, object]
    plan_prompt: str | None
    checkpoint_id: str
    authorization_id: str


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _canonical_json_line(value: dict[str, object]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _after_persist(label: str) -> None:
    """Private causal test seam called after each durable activation boundary."""
    del label


def _resolve_role(root: Path, manifest: dict[str, object], role: str) -> Path:
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    path, issues = resolve_managed_path(
        root, logical_roles.get(role), role=f"logical role {role}"
    )
    if path is None:
        raise ValueError("; ".join(issues))
    return path


def _expected_workspace(
    command: dict[str, object], observation: RepositoryObservation
) -> dict[str, object]:
    return {
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
    }


def _without_owned_program_paths(
    root: Path, observation: RepositoryObservation
) -> RepositoryObservation:
    """Remove only owner-proven publication paths from fresh Git facts."""
    try:
        owned_prefix = root.resolve().relative_to(Path(observation.path).resolve()).as_posix()
    except ValueError:
        return observation
    owned_prefixes = {owned_prefix}
    owner_path = root / ".publication-owner.json"
    if owner_path.is_file() and not owner_path.is_symlink():
        try:
            owner = json.loads(owner_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            owner = None
        if isinstance(owner, dict):
            owner_token = owner.get("owner_token")
            program_id = owner.get("program_id")
            staging = Path(observation.path) / (
                f".implementation-program-{program_id}-{owner_token}"
            )
            staging_owner = staging / ".publication-owner.json"
            if (
                owner.get("schema_version")
                == "implementation-proposal-publication-owner/v1"
                and owner.get("target") == owned_prefix
                and isinstance(program_id, str)
                and program_id == root.name
                and isinstance(owner_token, str)
                and len(owner_token) == 16
                and staging_owner.is_file()
                and not staging_owner.is_symlink()
                and staging_owner.read_bytes() == owner_path.read_bytes()
            ):
                owned_prefixes.add(staging.relative_to(Path(observation.path)).as_posix())
    untracked = tuple(
        path
        for path in observation.untracked_paths
        if not any(
            path == prefix or path.startswith(prefix + "/")
            for prefix in owned_prefixes
        )
    )
    return replace(observation, untracked_paths=untracked)


def build_activation_transaction(
    command: dict[str, object],
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    expected_workspace = _expected_workspace(command, observation)
    if command.get("workspace") != expected_workspace:
        raise ValueError("workspace observation does not match the launch prompt")
    if observation.conflicted_paths or observation.active_git_operation is not None:
        raise ValueError("workspace observation is not stable for activation")

    prompt_sha256 = _sha256_bytes(submitted_prompt.encode("utf-8"))
    source = command.get("source_binding")
    brief = command.get("brief_binding")
    if not isinstance(source, dict) or not isinstance(brief, dict):
        raise ValueError("launch command source and brief bindings are required")
    common = {
        "program_id": command["program_id"],
        "program_revision": command["program_revision"],
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "program_sha256": command["program_sha256"],
        "semantic_requirements_sha256": command[
            "semantic_requirements_sha256"
        ],
        "approval_mode": command["approval_mode"],
        "launch_checkpoint_id": command["launch_checkpoint_id"],
        "submitted_prompt_sha256": prompt_sha256,
    }
    program_approval = {
        "schema_version": APPROVAL_SCHEMA,
        "event_id": command["program_approval_event_id"],
        "type": "program-approval",
        "decision": "approved",
        "scope": ["approve the bound implementation program"],
        **common,
    }
    workspace_approval = {
        "schema_version": APPROVAL_SCHEMA,
        "event_id": command["workspace_approval_event_id"],
        "type": "workspace-selection-approval",
        "decision": "approved",
        "scope": ["select the bound implementation workspace"],
        "workspace": expected_workspace["implementation_workspace"],
        "workspace_proposal_sha256": command["workspace_proposal_sha256"],
        **common,
    }
    grant = {
        "schema_version": INCREMENT_GRANT_SCHEMA,
        "grant_id": command["increment_grant_id"],
        "decision": "granted",
        "program_id": command["program_id"],
        "program_revision": command["program_revision"],
        "increment_id": command["increment_id"],
        "approval_mode": command["approval_mode"],
        "launch_checkpoint_id": command["launch_checkpoint_id"],
        "program_approval_event_id": command["program_approval_event_id"],
        "workspace_approval_event_id": command["workspace_approval_event_id"],
        "brief_binding": brief,
        "workspace_proposal_sha256": command["workspace_proposal_sha256"],
        "allowed_conditional_actions": command["allowed_conditional_actions"],
        "submitted_prompt_sha256": prompt_sha256,
    }
    grant_sha256 = _sha256_bytes(_canonical_json_line(grant))
    status = {
        "schema_version": "implementation-program-status/v2",
        "program_id": command["program_id"],
        "program_revision": command["program_revision"],
        "state_sequence": 1,
        "program_state": "active",
        "current_increment_id": command["increment_id"],
        "current_increment_state": "preparing",
        "approval_mode": command["approval_mode"],
        "source_binding": source,
        "program_binding": {
            "sha256": command["program_sha256"],
            "semantic_requirements_sha256": command[
                "semantic_requirements_sha256"
            ],
        },
        "brief_binding": {
            **brief,
            "workspace_sha256": command["workspace_proposal_sha256"],
            "head_commit": observation.head_commit,
        },
        "activation_binding": {
            "schema_version": ACTIVATION_BINDING_SCHEMA,
            "launch_checkpoint_id": command["launch_checkpoint_id"],
            "program_approval_event_id": command["program_approval_event_id"],
            "workspace_approval_event_id": command["workspace_approval_event_id"],
            "increment_grant_id": command["increment_grant_id"],
            "submitted_prompt_sha256": prompt_sha256,
            "prior_status_sha256": command["proposal_status_sha256"],
            "prior_status_sequence": command["proposal_status_sequence"],
        },
        "current_increment_authority_binding": {
            "schema_version": CURRENT_INCREMENT_AUTHORITY_SCHEMA,
            "kind": "increment-grant",
            "increment_id": command["increment_id"],
            "grant_id": command["increment_grant_id"],
            "grant_sha256": grant_sha256,
        },
        "previous_state": {
            "schema_version": "implementation-program-status/v2",
            "state_sequence": command["proposal_status_sequence"],
            "status_sha256": command["proposal_status_sha256"],
        },
    }
    return program_approval, workspace_approval, grant, status


def _valid_prefix_index(actual: bytes, records: Sequence[dict[str, object]]) -> int:
    expected = b""
    if actual == expected:
        return 0
    for index, record in enumerate(records, start=1):
        expected += _canonical_json_line(record)
        if actual == expected:
            return index
    return -1


def _append_or_adopt(
    path: Path,
    record: dict[str, object],
    *,
    present: bool,
) -> bool:
    if present:
        return True
    expected_sha256 = sha256_file(path)
    try:
        atomic_append_json_line(path, record, expected_sha256)
    except ValueError as error:
        raise ValueError(f"program-activation-recovery-required: {error}") from error
    return False


def activate_program(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> ActivationReceipt:
    """Persist/adopt approval, workspace approval, grant, and status in order."""
    root = Path(program_root)
    observation = _without_owned_program_paths(root, observation)
    command = validate_submitted_program_launch_prompt(root, submitted_prompt)
    program_approval, workspace_approval, grant, active_status = build_activation_transaction(
        command, submitted_prompt, observation
    )
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    approvals_path = _resolve_role(root, manifest, "approvals")
    grants_path = _resolve_role(root, manifest, "increment_grants")
    status_path = _resolve_role(root, manifest, "status")

    approval_prefix = _valid_prefix_index(
        approvals_path.read_bytes(), (program_approval, workspace_approval)
    )
    grant_prefix = _valid_prefix_index(grants_path.read_bytes(), (grant,))
    if (
        approval_prefix < 0
        or grant_prefix < 0
        or (grant_prefix == 1 and approval_prefix != 2)
    ):
        raise ValueError(
            "program-activation-recovery-required: divergent activation ledger prefix"
        )
    recovered = approval_prefix > 0 or grant_prefix > 0

    adopted = _append_or_adopt(
        approvals_path, program_approval, present=approval_prefix >= 1
    )
    recovered = recovered or adopted
    _after_persist("program-approval")
    adopted = _append_or_adopt(
        approvals_path, workspace_approval, present=approval_prefix >= 2
    )
    recovered = recovered or adopted
    _after_persist("workspace-approval")
    adopted = _append_or_adopt(grants_path, grant, present=grant_prefix >= 1)
    recovered = recovered or adopted
    _after_persist("increment-grant")

    active_bytes = _canonical_json_bytes(active_status)
    current_status_bytes = status_path.read_bytes()
    if current_status_bytes == active_bytes:
        recovered = True
    elif sha256_file(status_path) == command["proposal_status_sha256"]:
        try:
            atomic_replace_json(
                status_path, active_status, str(command["proposal_status_sha256"])
            )
        except ValueError as error:
            raise ValueError(
                f"program-activation-recovery-required: {error}"
            ) from error
    else:
        raise ValueError(
            "program-activation-recovery-required: divergent activation status"
        )
    _after_persist("active-status")

    state_issues = validate_state_authority(root, observation)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    return ActivationReceipt(
        program_id=str(command["program_id"]),
        increment_id=str(command["increment_id"]),
        increment_state="preparing",
        status_sha256=sha256_file(status_path),
        program_approval_event_id=str(command["program_approval_event_id"]),
        workspace_approval_event_id=str(command["workspace_approval_event_id"]),
        increment_grant_id=str(command["increment_grant_id"]),
        recovered=recovered,
    )


def _identifier(label: str, seed: dict[str, object]) -> str:
    digest = _sha256_bytes(
        _canonical_json_line({"identifier_domain": label, "seed": seed})
    )
    return f"{label.upper()}-{digest[:24]}"


def _observation_value(observation: RepositoryObservation) -> dict[str, object]:
    return {
        "repository": observation.repository,
        "path": observation.path,
        "branch": observation.branch,
        "base_commit": observation.base_commit,
        "head_commit": observation.head_commit,
        "staged_paths": list(observation.staged_paths),
        "modified_paths": list(observation.modified_paths),
        "untracked_paths": list(observation.untracked_paths),
        "conflicted_paths": list(observation.conflicted_paths),
        "active_git_operation": observation.active_git_operation,
    }


def _fresh_plan_observation(
    root: Path, supplied: RepositoryObservation
) -> tuple[RepositoryObservation, RepositoryInspection]:
    fresh = inspect_repository(Path(supplied.path), supplied.base_commit)
    normalized_fresh = _without_owned_program_paths(root, fresh.observation)
    normalized_supplied = _without_owned_program_paths(root, supplied)
    if _observation_value(normalized_fresh) != _observation_value(
        normalized_supplied
    ):
        raise ValueError("workspace observation changed before exact-plan preparation")
    return normalized_fresh, fresh


def _plan_storage_paths(
    root: Path, manifest: dict[str, object], increment_id: str
) -> tuple[Path, Path]:
    storage = manifest.get("increment_storage")
    if not isinstance(storage, dict):
        raise ValueError("manifest increment_storage must be an object")
    resolved: list[Path] = []
    for field in ("exact_file_plan_filename", "execution_baseline_filename"):
        relative = f"{storage.get('root')}/{increment_id}/{storage.get(field)}"
        path, issues = resolve_managed_path(
            root,
            relative,
            role=f"allocated increment {field}",
            require_file=False,
        )
        if path is None:
            raise ValueError("; ".join(issues))
        resolved.append(path)
    return resolved[0], resolved[1]


def _validate_plan_candidate_text(
    markdown: str,
    manifest: dict[str, object],
    status: dict[str, object],
    observation: RepositoryObservation,
    file_map: ExactFileMap,
) -> list[str]:
    issues: list[str] = []
    if len([line for line in markdown.splitlines() if line.startswith("# ")]) != 1:
        issues.append("exact-file plan must contain exactly one H1")
    for section in REQUIRED_PLAN_SECTIONS:
        if not _section_body(markdown, section):
            issues.append(f"exact-file plan section {section!r} is missing or empty")
    issues.extend(_validate_plan_naming_table(markdown))
    source = status.get("source_binding")
    program = status.get("program_binding")
    if not isinstance(source, dict) or not isinstance(program, dict):
        return sorted(set([*issues, "status source and program bindings are required"]))
    expected = (
        str(manifest.get("program_id")),
        str(manifest.get("program_revision")),
        str(status.get("current_increment_id")),
        str(source.get("sha256")),
        str(program.get("sha256")),
        str(program.get("semantic_requirements_sha256")),
        observation.path,
        observation.branch,
        observation.base_commit,
        observation.head_commit,
    )
    for value in expected:
        if value not in markdown:
            issues.append(f"exact-file plan binding is missing: {value}")
    if not file_map.create or not file_map.modify or not file_map.preserve:
        issues.append("exact-file plan dispositions must be non-empty")
    return sorted(set(issues))


def _path_baselines(
    root: Path, workspace_root: Path, file_map: ExactFileMap
) -> list[dict[str, object]]:
    workspace = Path(workspace_root).resolve()
    try:
        control_prefix = root.resolve().relative_to(workspace).as_posix()
    except ValueError as error:
        raise ValueError("program root must be inside the selected workspace") from error
    baselines: list[dict[str, object]] = []
    for disposition, paths in (
        ("Create", file_map.create),
        ("Modify", file_map.modify),
        ("Preserve", file_map.preserve),
    ):
        for relative in paths:
            if relative == control_prefix or relative.startswith(control_prefix + "/"):
                continue
            path = workspace / relative
            if path.is_symlink():
                raise ValueError(f"planned path must not be a symlink: {relative}")
            if path.exists() and not path.is_file():
                raise ValueError(f"planned path must be a regular file: {relative}")
            if disposition == "Create" and path.exists():
                raise ValueError(f"Create path already exists: {relative}")
            if disposition in {"Modify", "Preserve"} and not path.is_file():
                raise ValueError(f"{disposition} path is missing: {relative}")
            baselines.append(
                {
                    "path": relative,
                    "disposition": disposition,
                    "sha256": sha256_file(path) if path.is_file() else None,
                }
            )
    return baselines


def _user_work_baselines(
    root: Path,
    observation: RepositoryObservation,
    file_map: ExactFileMap,
) -> list[dict[str, object]]:
    workspace = Path(observation.path).resolve()
    try:
        control_prefix = root.resolve().relative_to(workspace).as_posix()
    except ValueError as error:
        raise ValueError("program root must be inside the selected workspace") from error
    categories: dict[str, set[str]] = {}
    for category, paths in (
        ("staged", observation.staged_paths),
        ("modified", observation.modified_paths),
        ("untracked", observation.untracked_paths),
        ("conflicted", observation.conflicted_paths),
    ):
        for relative in paths:
            if relative == control_prefix or relative.startswith(control_prefix + "/"):
                continue
            categories.setdefault(relative, set()).add(category)
    claimed = set(file_map.create) | set(file_map.modify)
    overlap = claimed & set(categories)
    if overlap:
        raise ValueError(
            "exact-file plan cannot claim pre-existing user work as Create or Modify: "
            + ", ".join(sorted(overlap))
        )
    baselines: list[dict[str, object]] = []
    for relative in sorted(categories):
        path = workspace / relative
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"pre-existing user work path is unsafe: {relative}")
        baselines.append(
            {
                "path": relative,
                "categories": sorted(categories[relative]),
                "sha256": sha256_file(path) if path.is_file() else None,
            }
        )
    return baselines


def _stable_status_fields(status: dict[str, object]) -> dict[str, object]:
    fields = (
        "schema_version",
        "program_id",
        "program_revision",
        "program_state",
        "current_increment_id",
        "approval_mode",
        "source_binding",
        "program_binding",
        "brief_binding",
        "activation_binding",
        "current_increment_authority_binding",
    )
    return {field: status[field] for field in fields}


def _build_plan_candidate(
    root: Path,
    plan_bytes: bytes,
    observation: RepositoryObservation,
) -> _PlanCandidate:
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status_path = _resolve_role(root, manifest, "status")
    status, status_issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(status_issues))
    increment_state = status.get("current_increment_state")
    if increment_state not in {"preparing", "awaiting-plan-approval", "authorized"}:
        raise ValueError("exact-plan transaction requires preparing or plan-bound status")
    plan_path, baseline_path = _plan_storage_paths(
        root, manifest, str(status["current_increment_id"])
    )
    state_issues = validate_state_authority(root, observation)
    if (
        increment_state == "preparing"
        and plan_path.is_file()
        and not plan_path.is_symlink()
        and plan_path.read_bytes() == plan_bytes
    ):
        state_issues = [issue for issue in state_issues if issue != "plan digest mismatch"]
    if state_issues:
        raise ValueError("; ".join(state_issues))
    try:
        markdown = plan_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("exact-file plan must be UTF-8") from error
    file_map = parse_exact_file_map(markdown)
    required = required_future_lifecycle_writes(
        root, Path(observation.path), str(status["current_increment_id"])
    )
    managed_issues = validate_required_managed_file_map(file_map, required)
    content_issues = _validate_plan_candidate_text(
        markdown, manifest, status, observation, file_map
    )
    if managed_issues or content_issues:
        raise ValueError("; ".join(sorted(set([*managed_issues, *content_issues]))))

    plan_sha256 = _sha256_bytes(plan_bytes)
    preparation = status.get("plan_preparation_binding")
    if increment_state == "preparing":
        prior_status_sha256 = sha256_file(status_path)
        prior_status_sequence = int(status["state_sequence"])
    elif isinstance(preparation, dict):
        prior_status_sha256 = str(preparation.get("prior_status_sha256"))
        prior_status_sequence = int(preparation.get("prior_status_sequence"))
        if preparation.get("exact_file_plan_sha256") != plan_sha256:
            raise ValueError("exact-file plan digest differs from persisted preparation")
    else:
        raise ValueError("plan-bound status lacks preparation binding")

    user_work_baselines = _user_work_baselines(root, observation, file_map)
    path_baselines = _path_baselines(root, Path(observation.path), file_map)
    baseline = {
        "schema_version": EXECUTION_BASELINE_SCHEMA,
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "increment_id": status["current_increment_id"],
        "exact_file_plan_sha256": plan_sha256,
        "current_increment_authority_binding": status[
            "current_increment_authority_binding"
        ],
        "workspace_observation": _observation_value(observation),
        "file_map": asdict(file_map),
        "path_baselines": path_baselines,
        "user_work_baselines": user_work_baselines,
        "inherited_paths": [],
    }
    baseline_bytes = _canonical_json_bytes(baseline)
    baseline_sha256 = _sha256_bytes(baseline_bytes)
    file_map_sha256 = _sha256_bytes(_canonical_json_bytes(asdict(file_map)))
    seed = {
        "schema_domain": PLAN_PREPARATION_SCHEMA,
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "increment_id": status["current_increment_id"],
        "approval_mode": status["approval_mode"],
        "prior_status_sha256": prior_status_sha256,
        "prior_status_sequence": prior_status_sequence,
        "exact_file_plan_sha256": plan_sha256,
        "execution_baseline_sha256": baseline_sha256,
        "file_map_sha256": file_map_sha256,
        "current_increment_authority_binding": status[
            "current_increment_authority_binding"
        ],
    }
    checkpoint_id = _identifier("plan-checkpoint", seed)
    approval_event_id = _identifier(
        "plan-approval", {"seed": seed, "checkpoint_id": checkpoint_id}
    )
    authorization_id = _identifier(
        "plan-action",
        {
            "seed": seed,
            "checkpoint_id": checkpoint_id,
            "approval_event_id": approval_event_id,
        },
    )
    brief = status["brief_binding"]
    source = status["source_binding"]
    program = status["program_binding"]
    scope = "implement the bound exact-file plan"
    common = {
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "program_sha256": program["sha256"],
        "semantic_requirements_sha256": program[
            "semantic_requirements_sha256"
        ],
        "increment_id": status["current_increment_id"],
        "brief_sha256": brief["sha256"],
        "exact_file_plan_sha256": plan_sha256,
        "approval_mode": status["approval_mode"],
        "workspace": {
            "path": observation.path,
            "branch": observation.branch,
            "base_commit": observation.base_commit,
            "head_commit": observation.head_commit,
        },
    }
    action_record = {
        "schema_version": ACTION_AUTHORIZATION_SCHEMA,
        "authorization_id": authorization_id,
        "decision": "authorized",
        "actions": ["modify-workspace", "run-local-verification"],
        "scope": [scope],
        "constraints": ["write only exact-file-plan paths"],
        "excluded": [
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
        ],
        "plan_checkpoint_id": checkpoint_id,
        "execution_baseline_sha256": baseline_sha256,
        **common,
    }
    action_sha256 = _sha256_bytes(_canonical_json_line(action_record))
    preparation_binding = {
        "schema_version": PLAN_PREPARATION_SCHEMA,
        "checkpoint_id": checkpoint_id,
        "prior_status_sha256": prior_status_sha256,
        "prior_status_sequence": prior_status_sequence,
        "exact_file_plan_path": plan_path.relative_to(root).as_posix(),
        "exact_file_plan_sha256": plan_sha256,
        "execution_baseline_path": baseline_path.relative_to(root).as_posix(),
        "execution_baseline_sha256": baseline_sha256,
        "action_authorization_id": authorization_id,
        "action_authorization_sha256": action_sha256,
        "plan_approval_event_id": approval_event_id,
        "file_map_sha256": file_map_sha256,
    }
    status_base = _stable_status_fields(status)
    awaiting_status: dict[str, object] | None = None
    if status["approval_mode"] == "approval:standard":
        awaiting_status = {
            **status_base,
            "state_sequence": prior_status_sequence + 1,
            "current_increment_state": "awaiting-plan-approval",
            "pending_exact_file_plan_sha256": plan_sha256,
            "approved_exact_file_plan_sha256": None,
            "plan_preparation_binding": preparation_binding,
            "previous_state": {
                "schema_version": status["schema_version"],
                "state_sequence": prior_status_sequence,
                "status_sha256": prior_status_sha256,
            },
        }
        authorized_prior = _sha256_bytes(_canonical_json_bytes(awaiting_status))
        authorized_sequence = prior_status_sequence + 2
    else:
        authorized_prior = prior_status_sha256
        authorized_sequence = prior_status_sequence + 1
    authorized_status = {
        **status_base,
        "state_sequence": authorized_sequence,
        "current_increment_state": "authorized",
        "pending_exact_file_plan_sha256": None,
        "approved_exact_file_plan_sha256": plan_sha256,
        "plan_preparation_binding": preparation_binding,
        "execution_baseline_binding": {
            "path": baseline_path.relative_to(root).as_posix(),
            "sha256": baseline_sha256,
        },
        "execution_authorization": {
            "authorization_id": authorization_id,
            "scope": scope,
        },
        "transition_authority": (
            {
                "kind": "approval-event",
                "event_id": approval_event_id,
                "checkpoint_id": checkpoint_id,
            }
            if status["approval_mode"] == "approval:standard"
            else {
                "kind": "action-authorization",
                "event_id": checkpoint_id,
                "checkpoint_id": checkpoint_id,
                "authorization_id": authorization_id,
            }
        ),
        "previous_state": {
            "schema_version": status["schema_version"],
            "state_sequence": authorized_sequence - 1,
            "status_sha256": authorized_prior,
        },
    }
    plan_prompt: str | None = None
    approval_record: dict[str, object] | None = None
    if status["approval_mode"] == "approval:standard":
        prompt_command = {
            "schema_version": PLAN_PREPARATION_SCHEMA,
            "decision": "approve-exact-plan",
            "checkpoint_id": checkpoint_id,
            "plan_approval_event_id": approval_event_id,
            "action_authorization_id": authorization_id,
            "exact_file_plan_sha256": plan_sha256,
            "execution_baseline_sha256": baseline_sha256,
            "authorized_status_sha256": _sha256_bytes(
                _canonical_json_bytes(authorized_status)
            ),
            **common,
        }
        plan_prompt = render_exact_prompt(prompt_command)
        approval_record = {
            "schema_version": APPROVAL_SCHEMA,
            "event_id": approval_event_id,
            "type": "exact-file-plan-approval",
            "decision": "approved",
            "scope": ["approve the bound exact-file plan"],
            "plan_checkpoint_id": checkpoint_id,
            "execution_baseline_sha256": baseline_sha256,
            "submitted_prompt_sha256": _sha256_bytes(plan_prompt.encode("utf-8")),
            **common,
        }
    return _PlanCandidate(
        plan_path=plan_path,
        plan_bytes=plan_bytes,
        plan_sha256=plan_sha256,
        baseline_path=baseline_path,
        baseline=baseline,
        baseline_bytes=baseline_bytes,
        baseline_sha256=baseline_sha256,
        action_record=action_record,
        action_sha256=action_sha256,
        plan_approval_record=approval_record,
        awaiting_status=awaiting_status,
        authorized_status=authorized_status,
        plan_prompt=plan_prompt,
        checkpoint_id=checkpoint_id,
        authorization_id=authorization_id,
    )


def _create_or_adopt_bytes(path: Path, payload: bytes, label: str) -> bool:
    current = path.parent
    ancestors: list[Path] = []
    while not current.exists():
        ancestors.append(current)
        current = current.parent
    if current.is_symlink() or not current.is_dir():
        raise ValueError(f"{label}-recovery-required: unsafe parent")
    for directory in reversed(ancestors):
        directory.mkdir()
        _fsync_directory(directory.parent)
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise ValueError(f"{label}-recovery-required: divergent {path}")
        return True
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written == 0:
                raise OSError(f"short write while creating {path}")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)
    return False


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _append_or_adopt_record(
    path: Path, record: dict[str, object], identifier_field: str, label: str
) -> bool:
    records, issues = load_json_lines(path)
    if records is None:
        raise ValueError("; ".join(issues))
    identifier = record[identifier_field]
    matching = [item for item in records if item.get(identifier_field) == identifier]
    if matching:
        if (
            len(matching) != 1
            or matching[0] != record
            or not path.read_bytes().endswith(_canonical_json_line(record))
        ):
            raise ValueError(f"{label}-recovery-required: conflicting record")
        return True
    if identifier_field == "event_id":
        semantic_conflicts = [
            item for item in records if item.get("type") == record.get("type")
        ]
    else:
        semantic_fields = (
            "schema_version",
            "program_id",
            "program_revision",
            "increment_id",
            "exact_file_plan_sha256",
        )
        semantic_conflicts = [
            item
            for item in records
            if all(item.get(field) == record.get(field) for field in semantic_fields)
        ]
    if semantic_conflicts:
        raise ValueError(f"{label}-recovery-required: conflicting record")
    atomic_append_json_line(path, record, sha256_file(path))
    return False


def _replace_or_adopt_status(
    path: Path,
    value: dict[str, object],
    expected_prior_sha256: str,
    label: str,
) -> bool:
    expected_bytes = _canonical_json_bytes(value)
    if path.read_bytes() == expected_bytes:
        return True
    if sha256_file(path) != expected_prior_sha256:
        raise ValueError(f"{label}-recovery-required: divergent status")
    atomic_replace_json(path, value, expected_prior_sha256)
    return False


def prepare_exact_plan(
    program_root: Path,
    exact_plan_bytes: bytes,
    observation: RepositoryObservation,
) -> ExactPlanPreparationReceipt:
    """Persist/adopt a validated exact plan and route its approval mode."""
    root = Path(program_root)
    normalized, _inspection = _fresh_plan_observation(root, observation)
    candidate = _build_plan_candidate(root, exact_plan_bytes, normalized)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status_path = _resolve_role(root, manifest, "status")
    status, issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(issues))
    recovered = _create_or_adopt_bytes(
        candidate.plan_path, candidate.plan_bytes, "plan-preparation"
    )
    _after_persist("exact-plan")
    if candidate.awaiting_status is not None:
        preparation = candidate.awaiting_status["plan_preparation_binding"]
        prior_sha256 = preparation["prior_status_sha256"]
        recovered = (
            _replace_or_adopt_status(
                status_path,
                candidate.awaiting_status,
                str(prior_sha256),
                "plan-preparation",
            )
            or recovered
        )
        _after_persist("awaiting-plan-status")
        return ExactPlanPreparationReceipt(
            plan_path=str(candidate.plan_path),
            plan_sha256=candidate.plan_sha256,
            increment_state="awaiting-plan-approval",
            plan_prompt=candidate.plan_prompt,
            recovered=recovered,
        )
    materialized = _materialize_candidate(
        root, candidate, None, normalized
    )
    return ExactPlanPreparationReceipt(
        plan_path=str(candidate.plan_path),
        plan_sha256=candidate.plan_sha256,
        increment_state=materialized.increment_state,
        plan_prompt=None,
        recovered=recovered or materialized.recovered,
    )


def _materialize_candidate(
    root: Path,
    candidate: _PlanCandidate,
    submitted_plan_prompt: str | None,
    observation: RepositoryObservation,
) -> ExecutionMaterializationReceipt:
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    approvals_path = _resolve_role(root, manifest, "approvals")
    actions_path = _resolve_role(root, manifest, "action_authorizations")
    status_path = _resolve_role(root, manifest, "status")
    recovered = False
    if candidate.plan_prompt is not None:
        if submitted_plan_prompt != candidate.plan_prompt:
            raise ValueError("submitted exact-plan prompt does not match current bytes")
        parse_exact_prompt(submitted_plan_prompt, PLAN_PREPARATION_SCHEMA)
        if candidate.plan_approval_record is None:
            raise ValueError("standard plan approval record is missing")
        recovered = _append_or_adopt_record(
            approvals_path,
            candidate.plan_approval_record,
            "event_id",
            "plan-materialization",
        )
        _after_persist("plan-approval")
    elif submitted_plan_prompt is not None:
        raise ValueError("automatic plan mode does not accept a plan-approval prompt")

    recovered = (
        _create_or_adopt_bytes(
            candidate.baseline_path,
            candidate.baseline_bytes,
            "plan-materialization",
        )
        or recovered
    )
    _after_persist("execution-baseline")
    recovered = (
        _append_or_adopt_record(
            actions_path,
            candidate.action_record,
            "authorization_id",
            "plan-materialization",
        )
        or recovered
    )
    _after_persist("plan-action-authorization")
    current_status, status_issues = load_json_object(status_path)
    if current_status is None:
        raise ValueError("; ".join(status_issues))
    if candidate.awaiting_status is not None:
        expected_prior = _sha256_bytes(_canonical_json_bytes(candidate.awaiting_status))
    else:
        binding = candidate.authorized_status["plan_preparation_binding"]
        expected_prior = str(binding["prior_status_sha256"])
    recovered = (
        _replace_or_adopt_status(
            status_path,
            candidate.authorized_status,
            expected_prior,
            "plan-materialization",
        )
        or recovered
    )
    _after_persist("authorized-status")
    state_issues = validate_state_authority(root, observation)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    return ExecutionMaterializationReceipt(
        plan_sha256=candidate.plan_sha256,
        baseline_sha256=candidate.baseline_sha256,
        authorization_id=candidate.authorization_id,
        increment_state="authorized",
        status_sha256=sha256_file(status_path),
        recovered=recovered,
    )


def materialize_exact_plan(
    program_root: Path,
    submitted_plan_prompt: str | None,
    observation: RepositoryObservation,
) -> ExecutionMaterializationReceipt:
    """Persist/adopt approval when required, baseline, action, and status last."""
    root = Path(program_root)
    normalized, _inspection = _fresh_plan_observation(root, observation)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, status_issues = load_json_object(_resolve_role(root, manifest, "status"))
    if status is None:
        raise ValueError("; ".join(status_issues))
    plan_path, _baseline_path = _plan_storage_paths(
        root, manifest, str(status["current_increment_id"])
    )
    if plan_path.is_symlink() or not plan_path.is_file():
        raise ValueError("status-current exact-file plan is missing")
    candidate = _build_plan_candidate(root, plan_path.read_bytes(), normalized)
    return _materialize_candidate(
        root, candidate, submitted_plan_prompt, normalized
    )


def advance_execution_state(
    program_root: Path,
    target_increment_state: str,
    observation: RepositoryObservation,
) -> ExecutionTransitionReceipt:
    """Advance authorized execution through implementing and reviewing."""
    root = Path(program_root)
    fresh = inspect_repository(Path(observation.path), observation.base_commit)
    normalized = _without_owned_program_paths(root, fresh.observation)
    if _observation_value(normalized) != _observation_value(
        _without_owned_program_paths(root, observation)
    ):
        raise ValueError("workspace observation changed before execution transition")
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status_path = _resolve_role(root, manifest, "status")
    status, status_issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(status_issues))
    current_state = str(status.get("current_increment_state"))
    allowed = {"authorized": "implementing", "implementing": "reviewing"}
    if target_increment_state not in {"implementing", "reviewing"}:
        raise ValueError("execution transition target must be implementing or reviewing")

    baseline_binding = status.get("execution_baseline_binding")
    if not isinstance(baseline_binding, dict):
        raise ValueError("execution baseline binding is required")
    baseline_path, baseline_path_issues = resolve_managed_path(
        root,
        baseline_binding.get("path"),
        role="status execution baseline binding",
    )
    if baseline_path is None:
        raise ValueError("; ".join(baseline_path_issues))
    if sha256_file(baseline_path) != baseline_binding.get("sha256"):
        raise ValueError("execution baseline digest mismatch")
    baseline_value, baseline_issues = load_json_object(baseline_path)
    if baseline_value is None:
        raise ValueError("; ".join(baseline_issues))
    baseline = execution_baseline_from_value(baseline_value)
    assessment = validate_execution_workspace(
        root,
        baseline,
        replace(fresh, observation=normalized),
        increment_state=target_increment_state,
    )
    if not assessment.valid:
        raise ValueError("; ".join(assessment.issues))

    if current_state == target_increment_state:
        transition = status.get("execution_transition_binding")
        if (
            not isinstance(transition, dict)
            or transition.get("schema_version") != EXECUTION_TRANSITION_SCHEMA
            or transition.get("target_increment_state") != target_increment_state
            or transition.get("product_delta_sha256")
            != assessment.product_delta_sha256
        ):
            raise ValueError("execution-transition-recovery-required: status binding differs")
        return ExecutionTransitionReceipt(
            prior_state=str(transition["prior_increment_state"]),
            increment_state=target_increment_state,
            status_sha256=sha256_file(status_path),
            product_delta_sha256=assessment.product_delta_sha256,
            recovered=True,
        )
    if allowed.get(current_state) != target_increment_state:
        raise ValueError(
            f"illegal execution transition {current_state!r} -> {target_increment_state!r}"
        )
    state_issues = validate_state_authority(root, normalized)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    execution_authorization = status.get("execution_authorization")
    if not isinstance(execution_authorization, dict):
        raise ValueError("execution authorization binding is required")
    authorization_id = execution_authorization.get("authorization_id")
    if not isinstance(authorization_id, str) or not authorization_id:
        raise ValueError("execution authorization id is required")
    prior_sha256 = sha256_file(status_path)
    event_id = _identifier(
        "execution-transition",
        {
            "program_id": status["program_id"],
            "program_revision": status["program_revision"],
            "increment_id": status["current_increment_id"],
            "prior_status_sha256": prior_sha256,
            "prior_increment_state": current_state,
            "target_increment_state": target_increment_state,
            "product_delta_sha256": assessment.product_delta_sha256,
            "authorization_id": authorization_id,
        },
    )
    new_status = dict(status)
    new_status.update(
        state_sequence=int(status["state_sequence"]) + 1,
        current_increment_state=target_increment_state,
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": status["state_sequence"],
            "status_sha256": prior_sha256,
        },
        transition_authority={
            "kind": "action-authorization",
            "event_id": event_id,
            "authorization_id": authorization_id,
        },
        execution_transition_binding={
            "schema_version": EXECUTION_TRANSITION_SCHEMA,
            "event_id": event_id,
            "authorization_id": authorization_id,
            "prior_increment_state": current_state,
            "target_increment_state": target_increment_state,
            "prior_status_sha256": prior_sha256,
            "product_delta_sha256": assessment.product_delta_sha256,
        },
    )
    atomic_replace_json(status_path, new_status, prior_sha256)
    _after_persist(f"{target_increment_state}-status")
    validation_issues = validate_state_authority(root, normalized)
    if validation_issues:
        raise ValueError("; ".join(validation_issues))
    return ExecutionTransitionReceipt(
        prior_state=current_state,
        increment_state=target_increment_state,
        status_sha256=sha256_file(status_path),
        product_delta_sha256=assessment.product_delta_sha256,
        recovered=False,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="program_activation.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    apply = subparsers.add_parser("apply")
    apply.add_argument("program_root")
    apply.add_argument("--prompt-file", required=True)
    apply.add_argument("--repository", required=True)
    apply.add_argument("--base-commit", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(
        list(sys.argv[1:] if argv is None else argv)
    )
    prompt_path = Path(arguments.prompt_file)
    if prompt_path.is_symlink() or not prompt_path.is_file():
        print("prompt file must be a regular non-symlink file", file=sys.stderr)
        return 1
    try:
        observation = inspect_repository(
            Path(arguments.repository), arguments.base_commit
        ).observation
        receipt = activate_program(
            Path(arguments.program_root),
            prompt_path.read_text(encoding="utf-8"),
            observation,
        )
    except (OSError, UnicodeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(asdict(receipt), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
