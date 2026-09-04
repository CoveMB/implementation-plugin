#!/usr/bin/env python3
"""Persist or recover one prompt-bound new-program activation transaction."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from program_authority import (
    SETUP_PROGRAM_MANIFEST_SCHEMA,
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
)
from program_setup import (
    SETUP_ACTIVATION_SCHEMA,
    STATUS_SCHEMA_V3,
    SOURCE_GATE_SATISFACTION_SCHEMA,
    derive_identifier,
    render_increment_start_handoff,
    setup_semantic_identity,
    source_gate_satisfaction,
    validate_increment_start_intent,
    validate_setup_activation_authority,
    validate_setup_decision,
    value_sha256,
)
from program_launch import (
    render_program_launch_prompt,
    validate_submitted_program_launch_prompt,
)
from repository_preparation import (
    REQUIRED_PLAN_SECTIONS,
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
INCREMENT_GRANT_SCHEMA_V2 = "implementation-increment-grant/v2"
APPROVAL_SCHEMA_V2 = "implementation-approval/v2"
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
    increment_grant_id: str | None
    recovered: bool
    handoff: str | None = None


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
                in {
                    "implementation-proposal-publication-owner/v1",
                    "implementation-proposal-publication-owner/v2",
                }
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


def _preload_activation_dependencies() -> None:
    """Resolve lazy sibling dependencies before activation persists anything."""
    if "program_rollover" in sys.modules:
        return
    try:
        importlib.import_module("program_rollover")
        return
    except ModuleNotFoundError as error:
        if error.name != "program_rollover":
            raise

    module_path = Path(__file__).with_name("program_rollover.py")
    spec = importlib.util.spec_from_file_location("program_rollover", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load activation dependency from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(spec.name) is module:
            del sys.modules[spec.name]
        raise


def _activate_legacy_program(
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
    _preload_activation_dependencies()
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


def _require_fresh_program_observation(
    root: Path,
    supplied: RepositoryObservation,
    fresh: RepositoryObservation,
    drift_message: str,
) -> RepositoryObservation:
    normalized_supplied = _without_owned_program_paths(root, supplied)
    normalized_fresh = _without_owned_program_paths(root, fresh)
    if asdict(normalized_fresh) != asdict(normalized_supplied):
        raise ValueError(drift_message)
    return normalized_fresh


def _fresh_setup_observation(
    root: Path, supplied: RepositoryObservation
) -> RepositoryObservation:
    fresh = inspect_repository(Path(supplied.path), supplied.base_commit).observation
    normalized_fresh = _require_fresh_program_observation(
        root,
        supplied,
        fresh,
        "workspace observation changed before setup transaction",
    )
    if normalized_fresh.conflicted_paths or normalized_fresh.active_git_operation:
        raise ValueError("workspace observation is not stable for setup transaction")
    return normalized_fresh


def _v3_setup_role_path(
    root: Path, manifest: dict[str, object], role: str, *, require_file: bool
) -> Path:
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    path, issues = resolve_managed_path(
        root,
        logical_roles.get(role),
        role=f"logical role {role}",
        require_file=require_file,
    )
    if path is None:
        raise ValueError("; ".join(issues))
    return path


def _v3_workspace_matches(
    root: Path,
    manifest: dict[str, object],
    observation: RepositoryObservation,
) -> tuple[dict[str, object], Path]:
    workspace_path = _v3_setup_role_path(root, manifest, "workspace", require_file=True)
    workspace, issues = load_json_object(workspace_path)
    if workspace is None:
        raise ValueError("; ".join(issues))
    expected = _expected_workspace({}, observation)
    expected["schema_version"] = "implementation-workspace-proposal/v1"
    expected["program_id"] = manifest["program_id"]
    expected["program_revision"] = manifest["program_revision"]
    if workspace != expected:
        raise ValueError("workspace observation does not match setup proposal")
    return workspace, workspace_path


def _build_v3_setup_record(
    root: Path,
    manifest: dict[str, object],
    decision: dict[str, object],
    observation: RepositoryObservation,
    proposal_status_sha256: str,
    proposal_status_sequence: int,
) -> dict[str, object]:
    source = manifest.get("source_binding")
    program = manifest.get("program_binding")
    semantics = manifest.get("setup_semantics")
    if not all(isinstance(value, dict) for value in (source, program, semantics)):
        raise ValueError("setup proposal bindings are incomplete")
    receipt_seed = {
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "semantic_decision_identity": setup_semantic_identity(manifest),
        "setup_adapter_id": decision["adapter_id"],
        "proposal_status_sha256": proposal_status_sha256,
        "proposal_status_sequence": proposal_status_sequence,
    }
    program_approval_event_id = _identifier("program-approval", receipt_seed)
    workspace_approval_event_id = _identifier(
        "workspace-approval",
        {
            **receipt_seed,
            "program_approval_event_id": program_approval_event_id,
        },
    )
    base: dict[str, object] = {
        "schema_version": SETUP_ACTIVATION_SCHEMA,
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "source_binding": source,
        "program_binding": program,
        "semantic_decision_identity": setup_semantic_identity(manifest),
        "operation_envelope_sha256": value_sha256(
            semantics["operation_envelope"]
        ),
        "source_gate_definitions_sha256": manifest[
            "source_gate_definitions_sha256"
        ],
        "recap_checkpoint": decision["recap_checkpoint"],
        "presented_integrity_identity": decision[
            "presented_integrity_identity"
        ],
        "decision": "approved",
        "provenance_class": decision["provenance_class"],
        "setup_adapter_id": decision["adapter_id"],
        "setup_adapter_sha256": value_sha256(decision),
        "workspace_observation": _observation_value(observation),
        "integrity_drift_classification": "visible-decision-unchanged",
        "program_approval_event_id": program_approval_event_id,
        "workspace_approval_event_id": workspace_approval_event_id,
        "proposal_status_sha256": proposal_status_sha256,
        "proposal_status_sequence": proposal_status_sequence,
    }
    base["decision_id"] = derive_identifier("setup-activation-decision", base)
    return base


def _v3_activation_candidates(
    root: Path,
    manifest: dict[str, object],
    setup_record: dict[str, object],
    setup_record_sha256: str,
    gate_satisfaction: dict[str, object],
    workspace_path: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    semantics = manifest["setup_semantics"]
    source = manifest["source_binding"]
    program = manifest["program_binding"]
    common = {
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "program_sha256": program["sha256"],
        "semantic_requirements_sha256": semantics["bindings"]["program"][
            "semantic_requirements_sha256"
        ],
        "approval_mode": manifest["approval_mode"],
        "setup_activation_decision_id": setup_record["decision_id"],
        "setup_activation_decision_sha256": setup_record_sha256,
        "source_gate_satisfaction": gate_satisfaction,
        "increment_grant_id": None,
        "exact_file_plan_sha256": None,
        "execution_baseline_sha256": None,
    }
    program_approval = {
        "schema_version": APPROVAL_SCHEMA_V2,
        "event_id": setup_record["program_approval_event_id"],
        "type": "program-approval",
        "decision": "approved",
        "scope": ["approve the visible bound implementation program setup"],
        **common,
    }
    workspace, workspace_issues = load_json_object(workspace_path)
    if workspace is None:
        raise ValueError("; ".join(workspace_issues))
    workspace_approval = {
        "schema_version": APPROVAL_SCHEMA_V2,
        "event_id": setup_record["workspace_approval_event_id"],
        "type": "workspace-selection-approval",
        "decision": "approved",
        "scope": ["select the setup-approved implementation workspace"],
        "workspace": workspace["implementation_workspace"],
        "workspace_proposal_sha256": sha256_file(workspace_path),
        **common,
    }
    program_approval_sha256 = _sha256_bytes(_canonical_json_line(program_approval))
    workspace_approval_sha256 = _sha256_bytes(_canonical_json_line(workspace_approval))
    active_status = {
        "schema_version": STATUS_SCHEMA_V3,
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "state_sequence": 1,
        "program_state": "active",
        "current_increment_id": semantics["first_increment_id"],
        "current_increment_state": "awaiting-first-increment",
        "approval_mode": manifest["approval_mode"],
        "source_binding": source,
        "program_binding": {
            "sha256": program["sha256"],
            "semantic_requirements_sha256": semantics["bindings"]["program"][
                "semantic_requirements_sha256"
            ],
        },
        "setup_activation_binding": {
            "schema_version": "implementation-setup-activation-status-binding/v1",
            "setup_activation_decision_id": setup_record["decision_id"],
            "setup_activation_decision_sha256": setup_record_sha256,
            "program_approval_event_id": program_approval["event_id"],
            "program_approval_sha256": program_approval_sha256,
            "workspace_approval_event_id": workspace_approval["event_id"],
            "workspace_approval_sha256": workspace_approval_sha256,
            "source_gate_satisfaction": gate_satisfaction,
        },
        "previous_state": {
            "schema_version": STATUS_SCHEMA_V3,
            "state_sequence": setup_record["proposal_status_sequence"],
            "status_sha256": setup_record["proposal_status_sha256"],
            "program_state": "awaiting-program-approval",
            "current_increment_id": semantics["first_increment_id"],
            "current_increment_state": "not-started",
        },
    }
    return program_approval, workspace_approval, active_status


def _activate_setup_program(
    root: Path,
    submitted_decision: object,
    supplied_observation: RepositoryObservation,
) -> ActivationReceipt:
    if not isinstance(submitted_decision, dict):
        raise ValueError("v3 setup activation requires a typed setup decision")
    decision_issues = validate_setup_decision(root, submitted_decision)
    if decision_issues:
        raise ValueError("; ".join(decision_issues))
    observation = _fresh_setup_observation(root, supplied_observation)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    _workspace, workspace_path = _v3_workspace_matches(root, manifest, observation)
    status_path = _v3_setup_role_path(root, manifest, "status", require_file=True)
    status, status_issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(status_issues))
    setup_path = _v3_setup_role_path(
        root, manifest, "setup_activation_decision", require_file=False
    )
    existing_setup = None
    if setup_path.exists() or setup_path.is_symlink():
        existing_setup, existing_issues = load_json_object(setup_path)
        if existing_setup is None:
            raise ValueError("; ".join(existing_issues))
        proposal_status_sha256 = existing_setup.get("proposal_status_sha256")
        proposal_status_sequence = existing_setup.get("proposal_status_sequence")
    else:
        if not (
            status.get("schema_version") == STATUS_SCHEMA_V3
            and status.get("state_sequence") == 0
            and status.get("program_state") == "awaiting-program-approval"
            and status.get("current_increment_state") == "not-started"
        ):
            raise ValueError("v3 setup activation requires the sequence-zero proposal")
        proposal_status_sha256 = sha256_file(status_path)
        proposal_status_sequence = status["state_sequence"]
    if not isinstance(proposal_status_sha256, str) or proposal_status_sequence != 0:
        raise ValueError("setup activation proposal status binding is invalid")
    setup_record = _build_v3_setup_record(
        root,
        manifest,
        submitted_decision,
        observation,
        proposal_status_sha256,
        int(proposal_status_sequence),
    )
    setup_bytes = _canonical_json_bytes(setup_record)
    recovered = _create_or_adopt_bytes(
        setup_path, setup_bytes, "setup-activation"
    )
    _after_persist("setup-activation-decision")
    setup_record_sha256 = _sha256_bytes(setup_bytes)
    gate_satisfaction = source_gate_satisfaction(
        root,
        "before-program-activation",
        f"program:{manifest['program_id']}",
    )
    program_approval, workspace_approval, active_status = _v3_activation_candidates(
        root,
        manifest,
        setup_record,
        setup_record_sha256,
        gate_satisfaction,
        workspace_path,
    )
    approvals_path = _v3_setup_role_path(root, manifest, "approvals", require_file=True)
    recovered = (
        _append_or_adopt_record(
            approvals_path,
            program_approval,
            "event_id",
            "setup-activation",
            require_tail=False,
        )
        or recovered
    )
    _after_persist("program-approval")
    recovered = (
        _append_or_adopt_record(
            approvals_path,
            workspace_approval,
            "event_id",
            "setup-activation",
            require_tail=False,
        )
        or recovered
    )
    _after_persist("workspace-approval")
    recovered = (
        _replace_or_adopt_status(
            status_path,
            active_status,
            proposal_status_sha256,
            "setup-activation",
        )
        or recovered
    )
    _after_persist("active-waiting-status")
    handoff = render_increment_start_handoff(root)
    return ActivationReceipt(
        program_id=str(manifest["program_id"]),
        increment_id=str(active_status["current_increment_id"]),
        increment_state="awaiting-first-increment",
        status_sha256=sha256_file(status_path),
        program_approval_event_id=str(program_approval["event_id"]),
        workspace_approval_event_id=str(workspace_approval["event_id"]),
        increment_grant_id=None,
        recovered=recovered,
        handoff=handoff,
    )


def start_first_increment(
    program_root: Path,
    start_intent: dict[str, object],
    supplied_observation: RepositoryObservation,
) -> ActivationReceipt:
    root = Path(program_root)
    observation = _fresh_setup_observation(root, supplied_observation)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None or manifest.get("schema_version") != SETUP_PROGRAM_MANIFEST_SCHEMA:
        raise ValueError(
            "; ".join(manifest_issues)
            if manifest is None
            else "first-increment start requires manifest v3"
        )
    _workspace, workspace_path = _v3_workspace_matches(root, manifest, observation)
    status_path = _v3_setup_role_path(root, manifest, "status", require_file=True)
    status, status_issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(status_issues))
    if status.get("current_increment_state") not in {
        "awaiting-first-increment",
        "preparing",
    }:
        raise ValueError("program is not at the first-increment start boundary")
    setup_authority_issues = validate_setup_activation_authority(root)
    if setup_authority_issues:
        raise ValueError(
            "setup activation authority is invalid: "
            + "; ".join(setup_authority_issues)
        )
    intent_issues = validate_increment_start_intent(root, start_intent)
    if intent_issues:
        raise ValueError("; ".join(intent_issues))
    setup_path = _v3_setup_role_path(
        root, manifest, "setup_activation_decision", require_file=True
    )
    setup_record, setup_issues = load_json_object(setup_path)
    if setup_record is None:
        raise ValueError("; ".join(setup_issues))
    approvals_path = _v3_setup_role_path(root, manifest, "approvals", require_file=True)
    approvals, approval_issues = load_json_lines(approvals_path)
    if approvals is None:
        raise ValueError("; ".join(approval_issues))
    workspace_approval = next(
        (
            record
            for record in approvals
            if record.get("schema_version") == APPROVAL_SCHEMA_V2
            and record.get("type") == "workspace-selection-approval"
            and record.get("event_id") == setup_record.get("workspace_approval_event_id")
        ),
        None,
    )
    if workspace_approval is None:
        raise ValueError("first-increment start lacks workspace approval authority")
    gate_satisfaction = source_gate_satisfaction(
        root,
        "before-increment-start",
        f"increment:{status['current_increment_id']}",
        expected_boundary_authority=start_intent,
    )
    waiting_status_sha256 = str(start_intent["waiting_status_sha256"])
    grant_base: dict[str, object] = {
        "schema_version": INCREMENT_GRANT_SCHEMA_V2,
        "grant_kind": "first-increment-start",
        "decision": "granted",
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "increment_id": status["current_increment_id"],
        "approval_mode": manifest["approval_mode"],
        "setup_activation_decision_id": setup_record["decision_id"],
        "setup_activation_decision_sha256": sha256_file(setup_path),
        "start_intent": start_intent,
        "start_intent_sha256": value_sha256(start_intent),
        "waiting_status_sha256": waiting_status_sha256,
        "waiting_status_sequence": 1,
        "brief_binding": start_intent["brief_binding"],
        "workspace_approval_event_id": workspace_approval["event_id"],
        "workspace_approval_sha256": _sha256_bytes(
            _canonical_json_line(workspace_approval)
        ),
        "workspace_proposal_sha256": sha256_file(workspace_path),
        "source_gate_satisfaction": gate_satisfaction,
        "allowed_conditional_actions": [],
    }
    grant_base["grant_id"] = _identifier("increment-grant", grant_base)
    grant_sha256 = _sha256_bytes(_canonical_json_line(grant_base))
    setup_binding = status.get("setup_activation_binding")
    if not isinstance(setup_binding, dict):
        raise ValueError("waiting status lacks setup activation binding")
    preparing_status = {
        **status,
        "state_sequence": 2,
        "current_increment_state": "preparing",
        "brief_binding": start_intent["brief_binding"],
        "current_increment_authority_binding": {
            "schema_version": "implementation-current-increment-authority-binding/v2",
            "kind": "increment-grant",
            "grant_kind": "first-increment-start",
            "increment_id": status["current_increment_id"],
            "grant_id": grant_base["grant_id"],
            "grant_sha256": grant_sha256,
            "start_intent_id": start_intent["intent_id"],
            "start_intent_sha256": value_sha256(start_intent),
            "source_gate_satisfaction": gate_satisfaction,
        },
        "previous_state": {
            "schema_version": STATUS_SCHEMA_V3,
            "state_sequence": 1,
            "status_sha256": waiting_status_sha256,
            "program_state": "active",
            "current_increment_id": status["current_increment_id"],
            "current_increment_state": "awaiting-first-increment",
        },
    }
    grants_path = _v3_setup_role_path(
        root, manifest, "increment_grants", require_file=True
    )
    recovered = _append_or_adopt_record(
        grants_path, grant_base, "grant_id", "first-increment-start"
    )
    _after_persist("first-increment-grant")
    recovered = (
        _replace_or_adopt_status(
            status_path,
            preparing_status,
            waiting_status_sha256,
            "first-increment-start",
        )
        or recovered
    )
    _after_persist("first-increment-status")
    return ActivationReceipt(
        program_id=str(manifest["program_id"]),
        increment_id=str(status["current_increment_id"]),
        increment_state="preparing",
        status_sha256=sha256_file(status_path),
        program_approval_event_id=str(setup_record["program_approval_event_id"]),
        workspace_approval_event_id=str(setup_record["workspace_approval_event_id"]),
        increment_grant_id=str(grant_base["grant_id"]),
        recovered=recovered,
    )


def activate_program(
    program_root: Path,
    submitted_value: object,
    observation: RepositoryObservation,
) -> ActivationReceipt:
    """Route legacy prompt activation or the manifest-v3 setup transaction."""
    root = Path(program_root)
    manifest, issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(issues))
    _preload_activation_dependencies()
    if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA:
        return _activate_setup_program(root, submitted_value, observation)
    if not isinstance(submitted_value, str):
        raise ValueError("legacy activation requires the exact launch prompt text")
    return _activate_legacy_program(root, submitted_value, observation)


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
) -> RepositoryObservation:
    fresh = inspect_repository(Path(supplied.path), supplied.base_commit)
    return _require_fresh_program_observation(
        root,
        supplied,
        fresh.observation,
        "workspace observation changed before exact-plan preparation",
    )


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
    *,
    inherited_paths: Sequence[str] = (),
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
            if relative in inherited_paths:
                continue
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
    fields = [
        "schema_version",
        "program_id",
        "program_revision",
        "program_state",
        "current_increment_id",
        "approval_mode",
        "source_binding",
        "program_binding",
        "brief_binding",
        "current_increment_authority_binding",
    ]
    if status.get("schema_version") == STATUS_SCHEMA_V3:
        fields.append("setup_activation_binding")
    else:
        fields.append("activation_binding")
    stable = {field: status[field] for field in fields}
    for field in ("rollover_binding", "inherited_workspace_binding"):
        if field in status:
            stable[field] = status[field]
    return stable


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
    is_setup_program = (
        manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
    )
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
    if isinstance(status.get("rollover_binding"), dict):
        from program_rollover import validated_inherited_paths

        inherited_paths = validated_inherited_paths(root, status, observation)
    else:
        inherited_paths = ()
    inherited_set = set(inherited_paths)
    envelope_issues: list[str] = []
    if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA:
        semantics = manifest.get("setup_semantics")
        envelope = (
            semantics.get("operation_envelope")
            if isinstance(semantics, dict)
            else None
        )
        allocations = (
            envelope.get("allocations") if isinstance(envelope, dict) else None
        )
        if not isinstance(allocations, list):
            envelope_issues.append("v3 operation envelope allocations are missing")
        else:
            managed = {
                (requirement.path, requirement.disposition)
                for requirement in required
            }
            for operation, paths in (
                ("Create", file_map.create),
                ("Modify", file_map.modify),
                ("Preserve", file_map.preserve),
            ):
                for path in paths:
                    if (path, operation) in managed:
                        continue
                    matches = [
                        allocation
                        for allocation in allocations
                        if isinstance(allocation, dict)
                        and allocation.get("operation") == operation
                        and status["current_increment_id"]
                        in allocation.get("increment_ids", [])
                        and (
                            allocation.get("path") == path
                            if allocation.get("kind") == "exact-path"
                            else allocation.get("kind") == "bounded-path-class"
                            and isinstance(allocation.get("path"), str)
                            and (
                                path == allocation["path"]
                                or path.startswith(str(allocation["path"]) + "/")
                            )
                        )
                    ]
                    if len(matches) != 1:
                        envelope_issues.append(
                            f"{operation} path is outside the setup-approved operation envelope: {path}"
                        )
                        continue
                    allocation = matches[0]
                    workspace_path = Path(observation.path) / path
                    if workspace_path.is_symlink():
                        actual_facts = ("symlink", "symlink", None, "existing")
                    elif not workspace_path.exists():
                        actual_facts = ("absent", "none", None, "none")
                    elif workspace_path.is_file():
                        file_status = workspace_path.stat()
                        actual_facts = (
                            "regular-file",
                            "hard-link" if file_status.st_nlink > 1 else "none",
                            "100755" if file_status.st_mode & 0o111 else "100644",
                            (
                                "accepted-predecessor"
                                if path in inherited_set
                                else "existing"
                            ),
                        )
                    else:
                        actual_facts = ("unsupported", "none", None, "existing")
                    expected_facts = (
                        allocation.get("file_kind"),
                        allocation.get("link_kind"),
                        allocation.get("mode"),
                        allocation.get("collision"),
                    )
                    unsafe_ownership = operation in {"Create", "Modify"} and (
                        allocation.get("ownership") != "program"
                        or allocation.get("protected") is not False
                        or allocation.get("user_work") is not False
                    )
                    if actual_facts != expected_facts or unsafe_ownership:
                        envelope_issues.append(
                            f"{operation} path no longer matches its setup-approved "
                            f"operation envelope observation: {path}"
                        )
    content_issues = _validate_plan_candidate_text(
        markdown, manifest, status, observation, file_map
    )
    if managed_issues or content_issues or envelope_issues:
        raise ValueError(
            "; ".join(
                sorted(set([*managed_issues, *content_issues, *envelope_issues]))
            )
        )

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

    user_work_baselines = _user_work_baselines(
        root,
        observation,
        file_map,
        inherited_paths=inherited_paths,
    )
    path_baselines = _path_baselines(root, Path(observation.path), file_map)
    baseline_observation = replace(
        observation,
        staged_paths=tuple(
            path for path in observation.staged_paths if path not in inherited_set
        ),
        modified_paths=tuple(
            path for path in observation.modified_paths if path not in inherited_set
        ),
        untracked_paths=tuple(
            path for path in observation.untracked_paths if path not in inherited_set
        ),
        conflicted_paths=tuple(
            path for path in observation.conflicted_paths if path not in inherited_set
        ),
    )
    baseline = {
        "schema_version": EXECUTION_BASELINE_SCHEMA,
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "increment_id": status["current_increment_id"],
        "exact_file_plan_sha256": plan_sha256,
        "current_increment_authority_binding": status[
            "current_increment_authority_binding"
        ],
        "workspace_observation": _observation_value(baseline_observation),
        "file_map": asdict(file_map),
        "path_baselines": path_baselines,
        "user_work_baselines": user_work_baselines,
        "inherited_paths": list(inherited_paths),
    }
    execution_baseline_from_value(baseline)
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
    if is_setup_program:
        setup_path = _v3_setup_role_path(
            root, manifest, "setup_activation_decision", require_file=True
        )
        setup_record, setup_issues = load_json_object(setup_path)
        if setup_record is None:
            raise ValueError("; ".join(setup_issues))
        current_authority = status.get("current_increment_authority_binding")
        if not isinstance(current_authority, dict):
            raise ValueError("v3 plan requires current increment grant authority")
        try:
            action_gate_satisfaction = source_gate_satisfaction(
                root,
                "before-action-authorization",
                f"increment:{status['current_increment_id']}",
            )
        except ValueError as error:
            if "is not durably satisfied" not in str(error):
                raise
            action_gate_satisfaction = None
        common.update(
            setup_activation_decision_id=setup_record["decision_id"],
            setup_activation_decision_sha256=sha256_file(setup_path),
            increment_grant_id=current_authority["grant_id"],
            increment_grant_sha256=current_authority["grant_sha256"],
        )
    else:
        action_gate_satisfaction = None
    action_record = {
        "schema_version": (
            "implementation-action-authorization/v2"
            if is_setup_program
            else ACTION_AUTHORIZATION_SCHEMA
        ),
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
    if action_gate_satisfaction is not None:
        action_record["source_gate_satisfaction"] = action_gate_satisfaction
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
        "plan_approval_event_id": approval_event_id,
        "file_map_sha256": file_map_sha256,
    }
    if not is_setup_program:
        preparation_binding["action_authorization_sha256"] = action_sha256
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
            **(
                {"authorization_sha256": action_sha256}
                if is_setup_program
                else {}
            ),
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
    if action_gate_satisfaction is not None:
        authorized_status["source_gate_satisfaction"] = action_gate_satisfaction
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
            **common,
        }
        if not is_setup_program:
            prompt_command["authorized_status_sha256"] = _sha256_bytes(
                _canonical_json_bytes(authorized_status)
            )
        plan_prompt = render_exact_prompt(prompt_command)
        approval_record = {
            "schema_version": (
                APPROVAL_SCHEMA_V2 if is_setup_program else APPROVAL_SCHEMA
            ),
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
    path: Path,
    record: dict[str, object],
    identifier_field: str,
    label: str,
    *,
    require_tail: bool = True,
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
            or (
                require_tail
                and not path.read_bytes().endswith(_canonical_json_line(record))
            )
        ):
            raise ValueError(f"{label}-recovery-required: conflicting record")
        return True
    if identifier_field == "event_id":
        semantic_fields = (
            "type",
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
    normalized = _fresh_plan_observation(root, observation)
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
    if (
        manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
        and "source_gate_satisfaction" not in candidate.action_record
    ):
        raise ValueError(
            "source gate before-action-authorization is not durably satisfied"
        )
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
    normalized = _fresh_plan_observation(root, observation)
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
    normalized = _require_fresh_program_observation(
        root,
        observation,
        fresh.observation,
        "workspace observation changed before execution transition",
    )
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
    transition_gate_satisfaction = None
    if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA:
        trigger = (
            "before-product-execution"
            if target_increment_state == "implementing"
            else "before-review"
        )
        transition_gate_satisfaction = source_gate_satisfaction(
            root,
            trigger,
            f"increment:{status['current_increment_id']}",
        )
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
    if transition_gate_satisfaction is not None:
        new_status["source_gate_satisfaction"] = transition_gate_satisfaction
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
