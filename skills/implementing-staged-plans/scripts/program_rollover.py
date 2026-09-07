#!/usr/bin/env python3
"""Persist prompt-bound successor rollover authority with status last."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from program_activation import (
    CURRENT_INCREMENT_AUTHORITY_SCHEMA,
    INCREMENT_GRANT_SCHEMA,
    _canonical_json_bytes,
    _canonical_json_line,
    _create_or_adopt_bytes,
    _identifier,
    _require_fresh_program_observation,
    _replace_or_adopt_status,
)
from program_authority import (
    NEW_PROGRAM_MANIFEST_SCHEMA,
    SETUP_PROGRAM_MANIFEST_SCHEMA,
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
)
from program_setup import source_gate_satisfaction
from repository_preparation import (
    EXECUTION_BASELINE_SCHEMA_V2,
    PRODUCT_PATH_STATES_SCHEMA_V2,
    ExactFileMap,
    execution_baseline_from_value,
    execution_baseline_v2_from_value,
    inspect_repository,
    product_path_states_v2_from_value,
)
from state_authority import (
    ACTION_AUTHORIZATION_SCHEMA,
    ManagedWriteRequirement,
    RepositoryObservation,
    atomic_append_json_line,
    classify_delete_quarantine_recovery,
    inspect_workspace_path,
    required_future_lifecycle_writes,
    validate_state_authority,
)


ROLLOVER_RECORD_SCHEMA = "implementation-increment-rollover/v1"
ROLLOVER_BINDING_SCHEMA = "implementation-increment-rollover-binding/v1"
INHERITED_WORKSPACE_SCHEMA = "implementation-inherited-workspace/v1"
ROLLOVER_RECORD_SCHEMA_V2 = "implementation-increment-rollover/v2"
ROLLOVER_BINDING_SCHEMA_V2 = "implementation-increment-rollover-binding/v2"
INHERITED_WORKSPACE_SCHEMA_V2 = "implementation-inherited-workspace/v2"
ACTION_AUTHORIZATION_SCHEMA_V3 = "implementation-action-authorization/v3"
SETUP_V2_ROLLOVER_ACTION_FIELDS = (
    "schema_version", "authorization_id", "decision", "actions", "scope",
    "constraints", "excluded", "program_id", "program_revision",
    "source_id", "source_sha256", "program_sha256",
    "semantic_requirements_sha256", "current_increment_id",
    "successor_increment_id", "continuation_domain",
    "continuation_checkpoint_id", "accepted_status_sha256",
    "accepted_status_sequence", "product_result_schema_version",
    "product_result_sha256", "workspace", "submitted_prompt_sha256",
    "setup_activation_decision_id", "setup_activation_decision_sha256",
    "increment_grant_id", "increment_grant_sha256",
    "source_gate_satisfaction",
)


@dataclass(frozen=True)
class IncrementRolloverReceipt:
    prior_status_sha256: str
    current_status_sha256: str
    current_increment_id: str
    successor_increment_id: str
    rollover_authorization_id: str
    successor_grant_id: str
    created_steps: tuple[str, ...]
    adopted_steps: tuple[str, ...]
    status_replaced: bool
    requires_retry: bool


@dataclass(frozen=True)
class IncrementRolloverInspection:
    continuation_domain: str | None
    disposition: str | None
    completed_steps: tuple[str, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class _RolloverCandidate:
    continuation_domain: str
    prior_status_sha256: str
    prior_status_sequence: int
    current_increment_id: str
    successor_increment_id: str
    rollover_authorization_id: str
    successor_grant_id: str
    action_record: dict[str, object]
    action_bytes: bytes
    action_sha256: str
    grant_record: dict[str, object]
    grant_bytes: bytes
    grant_sha256: str
    handoff_path: Path
    handoff_bytes: bytes
    successor_brief_path: Path
    successor_brief_bytes: bytes
    rollover_record: dict[str, object]
    rollover_bytes: bytes
    rollover_sha256: str
    successor_status: dict[str, object]
    successor_status_bytes: bytes
    action_path: Path
    grant_path: Path
    rollover_path: Path
    status_path: Path


class _UsageError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fresh_observation(
    root: Path,
    supplied: RepositoryObservation,
) -> RepositoryObservation:
    fresh = inspect_repository(Path(supplied.path), supplied.base_commit).observation
    return _require_fresh_program_observation(
        root,
        supplied,
        fresh,
        "workspace observation changed before increment rollover",
    )


def _load_role_path(
    root: Path,
    manifest: dict[str, object],
    role: str,
) -> Path:
    roles = manifest.get("logical_roles")
    if not isinstance(roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    path, issues = resolve_managed_path(
        root, roles.get(role), role=f"logical role {role}"
    )
    if path is None:
        raise ValueError("; ".join(issues))
    return path


def _load_role_object(
    root: Path,
    manifest: dict[str, object],
    role: str,
) -> tuple[dict[str, object], Path]:
    path = _load_role_path(root, manifest, role)
    value, issues = load_json_object(path)
    if value is None:
        raise ValueError("; ".join(issues))
    return value, path


def _increment_paths(
    root: Path,
    manifest: dict[str, object],
    current_increment_id: str,
    successor_increment_id: str,
) -> tuple[Path, Path]:
    storage = manifest.get("increment_storage")
    if not isinstance(storage, dict):
        raise ValueError("manifest increment_storage must be an object")
    relative_paths = (
        (
            f"{storage.get('root')}/{current_increment_id}/"
            f"{storage.get('handoff_filename')}"
        ),
        (
            f"{storage.get('root')}/{successor_increment_id}/"
            f"{storage.get('brief_filename')}"
        ),
    )
    resolved: list[Path] = []
    for label, relative in zip(
        ("current handoff", "successor brief"), relative_paths, strict=True
    ):
        path, issues = resolve_managed_path(
            root, relative, role=label, require_file=False
        )
        if path is None:
            raise ValueError("; ".join(issues))
        resolved.append(path)
    return resolved[0], resolved[1]


def required_increment_rollover_writes(
    program_root: Path,
    workspace_root: Path,
    successor_increment_id: str,
) -> tuple[ManagedWriteRequirement, ...]:
    """Return Plan A's full managed allocation for the bound successor boundary."""
    return _required_increment_rollover_writes(
        program_root,
        workspace_root,
        successor_increment_id,
        allow_unbound_rollover_suffix=False,
    )


def _required_increment_rollover_writes(
    program_root: Path,
    workspace_root: Path,
    successor_increment_id: str,
    *,
    allow_unbound_rollover_suffix: bool,
) -> tuple[ManagedWriteRequirement, ...]:
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, _ = _load_role_object(root, manifest, "status")
    from program_continuation import _build_continuation_extension
    from diff_disposition import build_diff_acceptance_candidate

    workspace, _ = _load_role_object(root, manifest, "workspace")
    selected = workspace["implementation_workspace"]
    observation = inspect_repository(
        Path(selected["path"]), selected["base_commit"]
    ).observation
    acceptance = build_diff_acceptance_candidate(root, observation)
    extension = _build_continuation_extension(
        root,
        acceptance,
        observation,
        allow_unbound_rollover_suffix=allow_unbound_rollover_suffix,
    )
    if extension is None or extension.successor_increment_id != successor_increment_id:
        raise ValueError("requested successor is not uniquely allocated and satisfied")
    return required_future_lifecycle_writes(
        root, Path(workspace_root), str(status["current_increment_id"])
    )


def _validate_rollover_file_map(
    file_map: ExactFileMap,
    required: Sequence[ManagedWriteRequirement],
) -> None:
    actual = {
        path: disposition
        for disposition, paths in (
            ("Create", file_map.create),
            ("Modify", file_map.modify),
            ("Preserve", file_map.preserve),
        )
        for path in paths
    }
    issues = [
        f"rollover allocation {item.path} must be {item.disposition}"
        for item in required
        if actual.get(item.path) != item.disposition
    ]
    if issues:
        raise ValueError("; ".join(issues))


def _render_handoff(
    *,
    program_id: str,
    program_revision: int,
    current_increment_id: str,
    successor_increment_id: str,
    accepted_status_sha256: str,
    rollover_authorization_id: str,
    successor_grant_id: str,
) -> bytes:
    return (
        "# Accepted increment handoff\n\n"
        f"- Program: `{program_id}` revision `{program_revision}`\n"
        f"- Accepted increment: `{current_increment_id}`\n"
        f"- Successor increment: `{successor_increment_id}`\n"
        f"- Accepted status: `{accepted_status_sha256}`\n"
        f"- Rollover action: `{rollover_authorization_id}`\n"
        f"- Successor grant: `{successor_grant_id}`\n"
        "- Next legal action: prepare the successor exact-file plan from status-current authority.\n"
        "- Authority: this handoff is navigation only and grants no action.\n"
    ).encode("utf-8")


def _continuation_candidate(
    root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> tuple[
    str,
    dict[str, object],
    object,
    str,
    str,
    str,
]:
    from diff_disposition import (
        _render_accept_continue_envelope,
        build_diff_acceptance_candidate,
    )
    from program_continuation import (
        _build_continuation_extension,
        _validate_submitted_continuation_prompt_for_rollover_retry,
        build_accept_continue_candidate,
    )

    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, _status_path = _load_role_object(root, manifest, "status")
    if status.get("current_increment_state") != "accepted":
        raise ValueError("increment rollover requires an accepted current increment")
    binding = status.get("diff_disposition_binding")
    if not isinstance(binding, dict):
        raise ValueError("accepted status diff disposition binding is required")
    acceptance = build_diff_acceptance_candidate(root, observation)
    extension = _build_continuation_extension(
        root,
        acceptance,
        observation,
        allow_unbound_rollover_suffix=True,
    )
    if extension is None:
        raise ValueError("no uniquely satisfied successor is available")
    decision = binding.get("decision")
    if decision == "accept-continue":
        continued = build_accept_continue_candidate(acceptance, extension)
        expected_prompt = _render_accept_continue_envelope(
            extension.successor_increment_id, continued.prompt
        )
        if submitted_prompt != expected_prompt:
            raise ValueError("submitted immediate continuation prompt is stale")
        if _canonical_json_bytes(status) != continued.accepted_status_bytes:
            raise ValueError("accepted continuation status differs from prompt binding")
        domain = "immediate"
        checkpoint_id = extension.checkpoint_id
        authorization_id = extension.rollover_authorization_id
        grant_id = extension.successor_grant_id
    elif decision == "accept-stop":
        command = _validate_submitted_continuation_prompt_for_rollover_retry(
            root, submitted_prompt
        )
        if command.successor_increment_id != extension.successor_increment_id:
            raise ValueError("accepted-state successor changed")
        domain = "accepted-state"
        checkpoint_id = command.checkpoint_id
        authorization_id = command.rollover_authorization_id
        grant_id = command.successor_grant_id
    else:
        raise ValueError("accepted status has an unsupported diff decision")
    return (
        domain,
        status,
        extension,
        checkpoint_id,
        authorization_id,
        grant_id,
    )


def _build_rollover_candidate(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> _RolloverCandidate:
    root = Path(program_root)
    normalized = _fresh_observation(root, observation)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    if manifest.get("schema_version") not in {
        NEW_PROGRAM_MANIFEST_SCHEMA,
        SETUP_PROGRAM_MANIFEST_SCHEMA,
    }:
        raise ValueError("increment rollover requires a new-model manifest")
    is_setup_program = (
        manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
    )
    (
        domain,
        status,
        extension,
        checkpoint_id,
        authorization_id,
        grant_id,
    ) = _continuation_candidate(root, submitted_prompt, normalized)
    status_path = _load_role_path(root, manifest, "status")
    action_path = _load_role_path(root, manifest, "action_authorizations")
    grant_path = _load_role_path(root, manifest, "increment_grants")
    rollover_path = _load_role_path(root, manifest, "rollovers")
    _workspace, workspace_path = _load_role_object(root, manifest, "workspace")
    current_increment_id = str(status["current_increment_id"])
    successor_increment_id = extension.successor_increment_id
    handoff_path, successor_brief_path = _increment_paths(
        root, manifest, current_increment_id, successor_increment_id
    )
    baseline_binding = status.get("execution_baseline_binding")
    if not isinstance(baseline_binding, dict):
        raise ValueError("accepted status execution baseline binding is required")
    baseline_path, baseline_path_issues = resolve_managed_path(
        root, baseline_binding.get("path"), role="accepted execution baseline"
    )
    if baseline_path is None:
        raise ValueError("; ".join(baseline_path_issues))
    baseline_value, baseline_issues = load_json_object(baseline_path)
    if baseline_value is None:
        raise ValueError("; ".join(baseline_issues))
    is_v2_result = baseline_value.get("schema_version") == EXECUTION_BASELINE_SCHEMA_V2
    baseline = (
        execution_baseline_v2_from_value(baseline_value)
        if is_v2_result
        else execution_baseline_from_value(baseline_value)
    )
    required = _required_increment_rollover_writes(
        root,
        Path(normalized.path),
        successor_increment_id,
        allow_unbound_rollover_suffix=True,
    )
    _validate_rollover_file_map(baseline.file_map, required)

    prompt_sha256 = _sha256_bytes(submitted_prompt.encode("utf-8"))
    prior_status_sha256 = sha256_file(status_path)
    prior_status_sequence = int(status["state_sequence"])
    projection = dict(extension.successor_projection)
    if domain == "accepted-state":
        from program_continuation import (
            _validate_submitted_continuation_prompt_for_rollover_retry,
        )

        accepted_command = _validate_submitted_continuation_prompt_for_rollover_retry(
            root, submitted_prompt
        )
        selected_workspace = dict(accepted_command.selected_workspace)
        inherited_workspace = dict(accepted_command.inherited_workspace)
        if is_v2_result:
            accepted_product_result = dict(
                accepted_command.accepted_product_result
            )
            accepted_product_sha256 = accepted_command.product_result_sha256
        else:
            accepted_product_delta_sha256 = (
                accepted_command.accepted_product_delta_sha256
            )
        allowed_actions = list(
            accepted_command.allowed_conditional_action_ceiling
        )
    else:
        selected_workspace = dict(projection["selected_workspace"])
        if is_v2_result:
            inherited_workspace = dict(extension.inherited_workspace)
            accepted_product_result = dict(extension.accepted_product_result)
            accepted_product_sha256 = str(projection["product_result_sha256"])
        else:
            inherited_workspace = {
                "selected_workspace": selected_workspace,
                "accepted_product_delta": [
                    asdict(item) for item in extension.accepted_product_delta
                ],
                "accepted_product_delta_sha256": projection[
                    "accepted_product_delta_sha256"
                ],
            }
            accepted_product_delta_sha256 = str(
                projection["accepted_product_delta_sha256"]
            )
        allowed_actions = list(projection["allowed_conditional_action_ceiling"])

    if is_v2_result:
        parsed_product_result = product_path_states_v2_from_value(
            accepted_product_result
        )
        if parsed_product_result.sha256 != accepted_product_sha256:
            raise ValueError("rollover product result binding is invalid")
        from diff_disposition import build_diff_acceptance_candidate
        from program_continuation import _accepted_v2_diff_binding

        accepted_diff_binding = _accepted_v2_diff_binding(
            root,
            build_diff_acceptance_candidate(root, normalized),
            status,
            accepted_product_result,
            require_persisted_approval=True,
        )

    source = status["source_binding"]
    program = status["program_binding"]
    action_gate_satisfaction = None
    increment_gate_satisfaction = None
    if is_setup_program:
        action_gate_satisfaction = source_gate_satisfaction(
            root,
            "before-action-authorization",
            f"increment:{current_increment_id}",
        )
        try:
            increment_gate_satisfaction = source_gate_satisfaction(
                root,
                "before-increment-start",
                f"increment:{successor_increment_id}",
            )
        except ValueError as error:
            if "is not durably satisfied" not in str(error):
                raise
            increment_gate_satisfaction = None
        setup_binding = status.get("setup_activation_binding")
        prior_authority = status.get("current_increment_authority_binding")
        if not isinstance(setup_binding, dict) or not isinstance(
            prior_authority, dict
        ):
            raise ValueError("v3 rollover authority is incomplete")
    action_record = {
        "schema_version": (
            ACTION_AUTHORIZATION_SCHEMA_V3
            if is_v2_result
            else (
                "implementation-action-authorization/v2"
                if is_setup_program
                else ACTION_AUTHORIZATION_SCHEMA
            )
        ),
        "authorization_id": authorization_id,
        "decision": "authorized",
        "actions": ["rollover-increment"],
        "scope": ["roll over the accepted increment to the bound successor"],
        "constraints": ["persist authority first and successor status last"],
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
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "program_sha256": program["sha256"],
        "semantic_requirements_sha256": program[
            "semantic_requirements_sha256"
        ],
        "current_increment_id": current_increment_id,
        "successor_increment_id": successor_increment_id,
        "continuation_domain": domain,
        "continuation_checkpoint_id": checkpoint_id,
        "accepted_status_sha256": prior_status_sha256,
        "accepted_status_sequence": prior_status_sequence,
        **(
            {
                "product_result_schema_version": PRODUCT_PATH_STATES_SCHEMA_V2,
                "product_result_sha256": accepted_product_sha256,
            }
            if is_v2_result
            else {
                "accepted_product_delta_sha256": accepted_product_delta_sha256
            }
        ),
        "workspace": selected_workspace,
        "submitted_prompt_sha256": prompt_sha256,
    }
    if is_setup_program:
        action_record.update(
            setup_activation_decision_id=setup_binding[
                "setup_activation_decision_id"
            ],
            setup_activation_decision_sha256=setup_binding[
                "setup_activation_decision_sha256"
            ],
            increment_grant_id=prior_authority["grant_id"],
            increment_grant_sha256=prior_authority["grant_sha256"],
            source_gate_satisfaction=action_gate_satisfaction,
        )
    action_bytes = (
        (
            json.dumps(
                action_record,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=False,
            )
            + "\n"
        ).encode("utf-8")
        if is_v2_result
        else _canonical_json_line(action_record)
    )
    action_sha256 = _sha256_bytes(action_bytes)
    brief_binding = {
        "path": successor_brief_path.relative_to(root).as_posix(),
        "sha256": _sha256_bytes(extension.successor_brief_bytes),
    }
    if is_setup_program:
        brief_binding.update(
            workspace_sha256=sha256_file(workspace_path),
            head_commit=normalized.head_commit,
        )
    grant_record = {
        "schema_version": (
            "implementation-increment-grant/v2"
            if is_setup_program
            else INCREMENT_GRANT_SCHEMA
        ),
        "grant_id": grant_id,
        "decision": "granted",
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "increment_id": successor_increment_id,
        "approval_mode": projection["successor_approval_mode"],
        "continuation_domain": domain,
        "continuation_checkpoint_id": checkpoint_id,
        "rollover_authorization_id": authorization_id,
        "brief_binding": brief_binding,
        "workspace_selection_sha256": sha256_file(workspace_path),
        "allowed_conditional_actions": allowed_actions,
        "submitted_prompt_sha256": prompt_sha256,
        **(
            {
                "product_result_schema_version": PRODUCT_PATH_STATES_SCHEMA_V2,
                "product_result_sha256": accepted_product_sha256,
                "delete_quarantine_bindings": accepted_product_result[
                    "delete_quarantine_bindings"
                ],
                "inherited_path_states_sha256": inherited_workspace[
                    "inherited_path_states_sha256"
                ],
            }
            if is_v2_result
            else {}
        ),
    }
    if is_setup_program:
        grant_record.update(
            grant_kind="successor-rollover",
            setup_activation_decision_id=setup_binding[
                "setup_activation_decision_id"
            ],
            setup_activation_decision_sha256=setup_binding[
                "setup_activation_decision_sha256"
            ],
            predecessor_increment_authority_binding=prior_authority,
            predecessor_status_sha256=prior_status_sha256,
            predecessor_status_sequence=prior_status_sequence,
            rollover_authorization_sha256=action_sha256,
        )
        if increment_gate_satisfaction is not None:
            grant_record["source_gate_satisfaction"] = increment_gate_satisfaction
    grant_bytes = _canonical_json_line(grant_record)
    grant_sha256 = _sha256_bytes(grant_bytes)
    handoff_bytes = _render_handoff(
        program_id=str(status["program_id"]),
        program_revision=int(status["program_revision"]),
        current_increment_id=current_increment_id,
        successor_increment_id=successor_increment_id,
        accepted_status_sha256=prior_status_sha256,
        rollover_authorization_id=authorization_id,
        successor_grant_id=grant_id,
    )
    rollover_id = _identifier(
        "increment-rollover",
        {
            "continuation_domain": domain,
            "continuation_checkpoint_id": checkpoint_id,
            "accepted_status_sha256": prior_status_sha256,
            "rollover_authorization_id": authorization_id,
            "successor_grant_id": grant_id,
        },
    )
    rollover_record = {
        "schema_version": (
            ROLLOVER_RECORD_SCHEMA_V2 if is_v2_result else ROLLOVER_RECORD_SCHEMA
        ),
        "rollover_id": rollover_id,
        "continuation_domain": domain,
        "continuation_checkpoint_id": checkpoint_id,
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "current_increment_id": current_increment_id,
        "successor_increment_id": successor_increment_id,
        "accepted_status_sha256": prior_status_sha256,
        "accepted_status_sequence": prior_status_sequence,
        "submitted_prompt_sha256": prompt_sha256,
        "rollover_authorization_id": authorization_id,
        "rollover_authorization_sha256": action_sha256,
        "successor_grant_id": grant_id,
        "successor_grant_sha256": grant_sha256,
        "handoff_binding": {
            "path": handoff_path.relative_to(root).as_posix(),
            "sha256": _sha256_bytes(handoff_bytes),
        },
        "successor_brief_binding": brief_binding,
        **(
            {
                "review_evidence_binding": dict(
                    status["review_evidence_binding"]
                ),
                "review_packet_binding": dict(status["review_packet_binding"]),
                "execution_baseline_binding": dict(baseline_binding),
                "accepted_diff_binding": accepted_diff_binding,
                "product_result_schema_version": PRODUCT_PATH_STATES_SCHEMA_V2,
                "product_result_sha256": accepted_product_sha256,
                "accepted_product_result": accepted_product_result,
                "delete_quarantine_bindings": accepted_product_result[
                    "delete_quarantine_bindings"
                ],
                "inherited_path_states_sha256": inherited_workspace[
                    "inherited_path_states_sha256"
                ],
            }
            if is_v2_result
            else {
                "accepted_product_delta": [
                    asdict(item) for item in extension.accepted_product_delta
                ],
                "accepted_product_delta_sha256": accepted_product_delta_sha256,
            }
        ),
        "selected_workspace": selected_workspace,
        "inherited_workspace": inherited_workspace,
        "prior_increment_authority_binding": status[
            "current_increment_authority_binding"
        ],
    }
    rollover_bytes = _canonical_json_line(rollover_record)
    rollover_sha256 = _sha256_bytes(rollover_bytes)
    if not is_v2_result:
        prior_inherited_binding = status.get("inherited_workspace_binding", {})
        if not isinstance(prior_inherited_binding, Mapping):
            raise ValueError("prior inherited workspace inventory is invalid")
        prior_inherited = prior_inherited_binding.get("inherited_paths", [])
        if not isinstance(prior_inherited, list) or not all(
            isinstance(item, str) for item in prior_inherited
        ):
            raise ValueError("prior inherited workspace inventory is invalid")
        cumulative_inherited_paths = sorted(
            {
                *prior_inherited,
                *(item.path for item in extension.accepted_product_delta),
            }
        )
    successor_status = dict(status)
    for field in (
        "approved_exact_file_plan_sha256",
        "pending_exact_file_plan_sha256",
        "plan_preparation_binding",
        "execution_authorization",
        "execution_baseline_binding",
        "execution_transition_binding",
        "review_preparation_binding",
        "review_evidence_binding",
        "review_packet_binding",
        "review_remediation_binding",
        "diff_disposition_binding",
        "closure_preparation_binding",
        "closure_binding",
    ):
        successor_status.pop(field, None)
    successor_status.update(
        state_sequence=prior_status_sequence + 1,
        program_state="active",
        current_increment_id=successor_increment_id,
        current_increment_state="preparing",
        approval_mode=projection["successor_approval_mode"],
        brief_binding={
            **brief_binding,
            "workspace_sha256": sha256_file(workspace_path),
            "head_commit": normalized.head_commit,
        },
        current_increment_authority_binding={
            "schema_version": (
                "implementation-current-increment-authority-binding/v2"
                if is_setup_program
                else "implementation-current-increment-authority-binding/v1"
            ),
            "kind": "increment-grant",
            **({"grant_kind": "successor-rollover"} if is_setup_program else {}),
            "increment_id": successor_increment_id,
            "grant_id": grant_id,
            "grant_sha256": grant_sha256,
            **(
                {"source_gate_satisfaction": increment_gate_satisfaction}
                if is_setup_program
                else {}
            ),
        },
        rollover_binding={
            "schema_version": (
                ROLLOVER_BINDING_SCHEMA_V2
                if is_v2_result
                else ROLLOVER_BINDING_SCHEMA
            ),
            "rollover_id": rollover_id,
            "rollover_sha256": rollover_sha256,
            "continuation_domain": domain,
            "continuation_checkpoint_id": checkpoint_id,
            "prior_status_sha256": prior_status_sha256,
            "prior_status_sequence": prior_status_sequence,
            "current_increment_id": current_increment_id,
            "successor_increment_id": successor_increment_id,
            "rollover_authorization_id": authorization_id,
            "rollover_authorization_sha256": action_sha256,
            "successor_grant_id": grant_id,
            "successor_grant_sha256": grant_sha256,
            "submitted_prompt_sha256": prompt_sha256,
            **(
                {
                    "product_result_schema_version": PRODUCT_PATH_STATES_SCHEMA_V2,
                    "product_result_sha256": accepted_product_sha256,
                    "delete_quarantine_bindings": accepted_product_result[
                        "delete_quarantine_bindings"
                    ],
                    "inherited_path_states_sha256": inherited_workspace[
                        "inherited_path_states_sha256"
                    ],
                }
                if is_v2_result
                else {}
            ),
        },
        inherited_workspace_binding=(
            inherited_workspace
            if is_v2_result
            else {
                "schema_version": INHERITED_WORKSPACE_SCHEMA,
                "workspace_selection_sha256": sha256_file(workspace_path),
                "accepted_product_delta_sha256": accepted_product_delta_sha256,
                "inherited_paths": cumulative_inherited_paths,
            }
        ),
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": prior_status_sequence,
            "status_sha256": prior_status_sha256,
        },
        transition_authority={
            "kind": "action-authorization",
            "authorization_id": authorization_id,
            "event_id": rollover_id,
            "checkpoint_id": checkpoint_id,
        },
    )
    if increment_gate_satisfaction is not None:
        successor_status["source_gate_satisfaction"] = increment_gate_satisfaction
    return _RolloverCandidate(
        continuation_domain=domain,
        prior_status_sha256=prior_status_sha256,
        prior_status_sequence=prior_status_sequence,
        current_increment_id=current_increment_id,
        successor_increment_id=successor_increment_id,
        rollover_authorization_id=authorization_id,
        successor_grant_id=grant_id,
        action_record=action_record,
        action_bytes=action_bytes,
        action_sha256=action_sha256,
        grant_record=grant_record,
        grant_bytes=grant_bytes,
        grant_sha256=grant_sha256,
        handoff_path=handoff_path,
        handoff_bytes=handoff_bytes,
        successor_brief_path=successor_brief_path,
        successor_brief_bytes=extension.successor_brief_bytes,
        rollover_record=rollover_record,
        rollover_bytes=rollover_bytes,
        rollover_sha256=rollover_sha256,
        successor_status=successor_status,
        successor_status_bytes=_canonical_json_bytes(successor_status),
        action_path=action_path,
        grant_path=grant_path,
        rollover_path=rollover_path,
        status_path=status_path,
    )


def _append_or_adopt_record(
    path: Path,
    record: dict[str, object],
    *,
    identifier_field: str,
    label: str,
    preserve_field_order: bool = False,
) -> bool:
    records, issues = load_json_lines(path)
    if records is None:
        raise ValueError("; ".join(issues))
    identifier = record[identifier_field]
    matches = [item for item in records if item.get(identifier_field) == identifier]
    if matches:
        if len(matches) != 1 or matches[0] != record:
            raise ValueError(f"continuation-recovery-required: divergent {label}")
        return True
    atomic_append_json_line(
        path,
        record,
        sha256_file(path),
        preserve_field_order=preserve_field_order,
    )
    return False


def _after_persist(_label: str) -> None:
    """Test seam after each durable rollover transaction step."""


def _completed_receipt(
    root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    submitted_prompt: str,
) -> IncrementRolloverReceipt | None:
    binding = status.get("rollover_binding")
    if not isinstance(binding, dict):
        return None
    if status.get("current_increment_state") != "preparing":
        return None
    prompt_sha256 = _sha256_bytes(submitted_prompt.encode("utf-8"))
    if binding.get("submitted_prompt_sha256") != prompt_sha256:
        raise ValueError("continuation-recovery-required: submitted prompt differs")
    rollover_path = _load_role_path(root, manifest, "rollovers")
    rollovers, issues = load_json_lines(rollover_path)
    if rollovers is None:
        raise ValueError("; ".join(issues))
    matches = [
        record
        for record in rollovers
        if record.get("rollover_id") == binding.get("rollover_id")
    ]
    if (
        len(matches) != 1
        or _sha256_bytes(_canonical_json_line(matches[0]))
        != binding.get("rollover_sha256")
        or matches[0].get("successor_increment_id")
        != status.get("current_increment_id")
    ):
        raise ValueError("continuation-recovery-required: rollover binding differs")
    return IncrementRolloverReceipt(
        prior_status_sha256=str(binding["prior_status_sha256"]),
        current_status_sha256=sha256_file(_load_role_path(root, manifest, "status")),
        current_increment_id=str(status["current_increment_id"]),
        successor_increment_id=str(status["current_increment_id"]),
        rollover_authorization_id=str(binding["rollover_authorization_id"]),
        successor_grant_id=str(binding["successor_grant_id"]),
        created_steps=(),
        adopted_steps=(
            "action-authorization",
            "successor-grant",
            "handoff",
            "successor-brief",
            "rollover-record",
            "successor-status",
        ),
        status_replaced=False,
        requires_retry=False,
    )


def _preflight_rollover_history(
    root: Path,
    status: Mapping[str, object],
    candidate: _RolloverCandidate,
    observation: RepositoryObservation,
) -> None:
    completed = _validated_completed_rollover_records(
        root,
        status,
        allow_unbound_suffix=True,
    )
    records, issues = load_json_lines(candidate.rollover_path)
    if records is None:
        raise ValueError("; ".join(issues))
    suffix = records[len(completed) :]
    if suffix and suffix != [candidate.rollover_record]:
        raise ValueError(
            "continuation-recovery-required: divergent rollover history"
        )
    inherited_paths = _validated_inherited_paths(
        root,
        status,
        observation,
        allow_unbound_suffix=True,
    )
    if isinstance(status.get("rollover_binding"), Mapping):
        inherited = status.get("inherited_workspace_binding")
        if not isinstance(inherited, Mapping):
            raise ValueError("rollover inherited workspace inventory mismatch")
        if inherited.get("schema_version") == INHERITED_WORKSPACE_SCHEMA_V2:
            if (
                not completed
                or inherited != completed[-1].get("inherited_workspace")
                or [
                    item.get("path")
                    for item in inherited.get("inherited_path_states", [])
                    if isinstance(item, Mapping)
                ]
                != list(inherited_paths)
            ):
                raise ValueError("rollover inherited workspace inventory mismatch")
        elif inherited.get("inherited_paths") != list(inherited_paths):
            raise ValueError("rollover inherited workspace inventory mismatch")
    candidate_inherited = candidate.successor_status.get(
        "inherited_workspace_binding"
    )
    if (
        isinstance(candidate_inherited, Mapping)
        and candidate_inherited.get("schema_version")
        == INHERITED_WORKSPACE_SCHEMA_V2
    ):
        cumulative = {
            "inherited_path_states": candidate_inherited.get(
                "inherited_path_states"
            ),
            "delete_quarantine_bindings": candidate_inherited.get(
                "delete_quarantine_bindings"
            ),
        }
        if (
            not isinstance(cumulative["inherited_path_states"], list)
            or not isinstance(cumulative["delete_quarantine_bindings"], list)
            or candidate_inherited.get("inherited_path_states_sha256")
            != _sha256_bytes(_canonical_json_bytes(cumulative))
        ):
            raise ValueError("rollover candidate inherited workspace is invalid")
        return
    current_delta = candidate.rollover_record.get("accepted_product_delta")
    if not isinstance(candidate_inherited, Mapping) or not isinstance(
        current_delta, list
    ):
        raise ValueError("rollover candidate inherited workspace is invalid")
    expected_cumulative = sorted(
        {
            *inherited_paths,
            *(
                item["path"]
                for item in current_delta
                if isinstance(item, Mapping) and isinstance(item.get("path"), str)
            ),
        }
    )
    if candidate_inherited.get("inherited_paths") != expected_cumulative:
        raise ValueError("rollover candidate inherited workspace inventory mismatch")


def persist_increment_rollover(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> IncrementRolloverReceipt:
    """Persist or adopt the authority-first, status-last rollover transaction."""
    root = Path(program_root)
    normalized = _fresh_observation(root, observation)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, _ = _load_role_object(root, manifest, "status")
    completed = _completed_receipt(root, manifest, status, submitted_prompt)
    if completed is not None:
        issues = validate_state_authority(root, normalized)
        if issues:
            raise ValueError("; ".join(issues))
        return completed
    candidate = _build_rollover_candidate(root, submitted_prompt, normalized)
    _preflight_rollover_history(root, status, candidate, normalized)
    created: list[str] = []
    adopted: list[str] = []

    def record(label: str, was_adopted: bool) -> None:
        (adopted if was_adopted else created).append(label)
        _after_persist(label)

    record(
        "action-authorization",
        _append_or_adopt_record(
            candidate.action_path,
            candidate.action_record,
            identifier_field="authorization_id",
            label="rollover action authorization",
            preserve_field_order=(
                candidate.action_record.get("schema_version")
                == ACTION_AUTHORIZATION_SCHEMA_V3
            ),
        ),
    )
    if (
        manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
        and "source_gate_satisfaction" not in candidate.grant_record
    ):
        raise ValueError(
            "source gate before-increment-start is not durably satisfied"
        )
    record(
        "successor-grant",
        _append_or_adopt_record(
            candidate.grant_path,
            candidate.grant_record,
            identifier_field="grant_id",
            label="successor grant",
        ),
    )
    record(
        "handoff",
        _create_or_adopt_bytes(
            candidate.handoff_path,
            candidate.handoff_bytes,
            "continuation",
        ),
    )
    record(
        "successor-brief",
        _create_or_adopt_bytes(
            candidate.successor_brief_path,
            candidate.successor_brief_bytes,
            "continuation",
        ),
    )
    record(
        "rollover-record",
        _append_or_adopt_record(
            candidate.rollover_path,
            candidate.rollover_record,
            identifier_field="rollover_id",
            label="rollover record",
        ),
    )
    status_adopted = _replace_or_adopt_status(
        candidate.status_path,
        candidate.successor_status,
        candidate.prior_status_sha256,
        "continuation",
    )
    record("successor-status", status_adopted)
    final_issues = validate_state_authority(root, _fresh_observation(root, normalized))
    if final_issues:
        raise ValueError("; ".join(final_issues))
    return IncrementRolloverReceipt(
        prior_status_sha256=candidate.prior_status_sha256,
        current_status_sha256=sha256_file(candidate.status_path),
        current_increment_id=candidate.successor_increment_id,
        successor_increment_id=candidate.successor_increment_id,
        rollover_authorization_id=candidate.rollover_authorization_id,
        successor_grant_id=candidate.successor_grant_id,
        created_steps=tuple(created),
        adopted_steps=tuple(adopted),
        status_replaced=not status_adopted,
        requires_retry=False,
    )


def _candidate_prefix_inspection(candidate: _RolloverCandidate) -> IncrementRolloverInspection:
    steps: list[str] = []
    checks = (
        (
            "action-authorization",
            candidate.action_path,
            "authorization_id",
            candidate.rollover_authorization_id,
            candidate.action_record,
        ),
        (
            "successor-grant",
            candidate.grant_path,
            "grant_id",
            candidate.successor_grant_id,
            candidate.grant_record,
        ),
    )
    for label, path, identifier_field, identifier, expected in checks:
        records, issues = load_json_lines(path)
        if records is None:
            return IncrementRolloverInspection(
                candidate.continuation_domain,
                None,
                tuple(steps),
                tuple(issues),
            )
        matches = [item for item in records if item.get(identifier_field) == identifier]
        if not matches:
            break
        if len(matches) != 1 or matches[0] != expected:
            return IncrementRolloverInspection(
                candidate.continuation_domain,
                _recovery_disposition(candidate.continuation_domain),
                tuple(steps),
                (f"divergent {label}",),
            )
        steps.append(label)
    else:
        for label, path, expected in (
            ("handoff", candidate.handoff_path, candidate.handoff_bytes),
            (
                "successor-brief",
                candidate.successor_brief_path,
                candidate.successor_brief_bytes,
            ),
        ):
            if not path.exists() and not path.is_symlink():
                break
            if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
                return IncrementRolloverInspection(
                    candidate.continuation_domain,
                    _recovery_disposition(candidate.continuation_domain),
                    tuple(steps),
                    (f"divergent {label}",),
                )
            steps.append(label)
        else:
            records, issues = load_json_lines(candidate.rollover_path)
            if records is None:
                return IncrementRolloverInspection(
                    candidate.continuation_domain, None, tuple(steps), tuple(issues)
                )
            matches = [
                item
                for item in records
                if item.get("rollover_id")
                == candidate.rollover_record.get("rollover_id")
            ]
            if matches:
                if len(matches) != 1 or matches[0] != candidate.rollover_record:
                    return IncrementRolloverInspection(
                        candidate.continuation_domain,
                        _recovery_disposition(candidate.continuation_domain),
                        tuple(steps),
                        ("divergent rollover-record",),
                    )
                steps.append("rollover-record")
    if not steps:
        return IncrementRolloverInspection(
            candidate.continuation_domain, None, (), ()
        )
    early = len(steps) <= 2
    if candidate.continuation_domain == "immediate":
        disposition = (
            "increment-continuation-retry-ready"
            if early
            else "increment-rollover-retry-ready"
        )
    else:
        disposition = (
            "accepted-state-continuation-retry-ready"
            if early
            else "accepted-state-rollover-retry-ready"
        )
    return IncrementRolloverInspection(
        candidate.continuation_domain, disposition, tuple(steps), ()
    )


def _recovery_disposition(domain: str) -> str:
    return (
        "accepted-state-continuation-recovery-required"
        if domain == "accepted-state"
        else "continuation-recovery-required"
    )


def inspect_increment_rollover(
    program_root: Path,
    observation: RepositoryObservation,
) -> IncrementRolloverInspection:
    """Classify an exact rollover prefix without modifying it."""
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        return IncrementRolloverInspection(None, None, (), tuple(manifest_issues))
    status, _ = _load_role_object(root, manifest, "status")
    if (
        status.get("current_increment_state") != "accepted"
        and isinstance(status.get("rollover_binding"), dict)
    ):
        binding = status["rollover_binding"]
        domain = str(binding.get("continuation_domain", "immediate"))
        try:
            _validated_inherited_paths(
                root,
                status,
                observation,
                allow_unbound_suffix=False,
            )
        except (KeyError, OSError, TypeError, ValueError) as error:
            return IncrementRolloverInspection(
                domain,
                _recovery_disposition(domain),
                ("successor-status",),
                (str(error),),
            )
        return IncrementRolloverInspection(
            domain,
            (
                "resume"
                if status.get("current_increment_state") == "preparing"
                else None
            ),
            ("successor-status",),
            (),
        )
    if status.get("current_increment_state") != "accepted":
        return IncrementRolloverInspection(None, None, (), ())
    binding = status.get("diff_disposition_binding")
    if not isinstance(binding, dict) or binding.get("decision") not in {
        "accept-stop",
        "accept-continue",
    }:
        return IncrementRolloverInspection(None, None, (), ())
    try:
        if binding["decision"] == "accept-continue":
            from program_continuation import _render_accept_continue_prompt

            prompt = _render_accept_continue_prompt(
                root,
                allow_unbound_rollover_suffix=True,
            )
        else:
            from program_continuation import (
                _render_accepted_state_continuation_prompt,
            )

            prompt = _render_accepted_state_continuation_prompt(
                root,
                allow_unbound_rollover_suffix=True,
            )
        candidate = _build_rollover_candidate(root, prompt, observation)
    except (KeyError, OSError, TypeError, ValueError) as error:
        action_path = _load_role_path(root, manifest, "action_authorizations")
        grant_path = _load_role_path(root, manifest, "increment_grants")
        rollover_path = _load_role_path(root, manifest, "rollovers")
        actions, _ = load_json_lines(action_path)
        grants, _ = load_json_lines(grant_path)
        rollovers, _ = load_json_lines(rollover_path)
        rollover_records = rollovers or []
        completed_rollovers: list[dict[str, object]] = []
        prior_rollover = status.get("rollover_binding")
        if isinstance(prior_rollover, dict):
            bound_indices = [
                index
                for index, record in enumerate(rollover_records)
                if record.get("rollover_id") == prior_rollover.get("rollover_id")
            ]
            if len(bound_indices) == 1:
                completed_rollovers = rollover_records[: bound_indices[0] + 1]
        completed_action_ids = {
            record.get("rollover_authorization_id")
            for record in completed_rollovers
        }
        completed_grant_ids = {
            record.get("successor_grant_id") for record in completed_rollovers
        }
        rollover_actions = [
            record
            for record in actions or []
            if record.get("actions") == ["rollover-increment"]
            and record.get("authorization_id") not in completed_action_ids
        ]
        continuation_grants = [
            record
            for record in grants or []
            if record.get("continuation_domain") in {"immediate", "accepted-state"}
            and record.get("grant_id") not in completed_grant_ids
        ]
        active_rollovers = rollover_records[len(completed_rollovers) :]
        domains = [
            record.get("continuation_domain")
            for record in (
                *rollover_actions,
                *continuation_grants,
                *active_rollovers,
            )
        ]
        if domains:
            domain = (
                "accepted-state"
                if domains[-1] == "accepted-state"
                else "immediate"
            )
            return IncrementRolloverInspection(
                domain, _recovery_disposition(domain), (), (str(error),)
            )
        return IncrementRolloverInspection(None, None, (), ())
    return _candidate_prefix_inspection(candidate)


def validated_inherited_paths(
    program_root: Path,
    status: Mapping[str, object],
    observation: RepositoryObservation,
) -> tuple[str, ...]:
    """Validate the canonical rollover chain and return latest accepted paths."""
    return _validated_inherited_paths(
        program_root,
        status,
        observation,
        allow_unbound_suffix=False,
    )


def _validate_rollover_file_binding(
    root: Path,
    binding: object,
    *,
    label: str,
) -> Path:
    if not isinstance(binding, Mapping):
        raise ValueError(f"rollover {label} binding is invalid")
    path, path_issues = resolve_managed_path(
        root,
        binding.get("path"),
        role=f"rollover {label}",
    )
    if path is None:
        raise ValueError("; ".join(path_issues))
    if binding.get("sha256") != sha256_file(path):
        raise ValueError(f"rollover {label} digest changed")
    return path


def _validated_completed_rollover_records(
    program_root: Path,
    status: Mapping[str, object],
    *,
    allow_unbound_suffix: bool,
) -> tuple[dict[str, object], ...]:
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    rollover_path = _load_role_path(root, manifest, "rollovers")
    records, record_issues = load_json_lines(rollover_path)
    if records is None:
        raise ValueError("; ".join(record_issues))
    binding = status.get("rollover_binding")
    if not isinstance(binding, Mapping):
        if records and not allow_unbound_suffix:
            raise ValueError("unbound rollover history is not lifecycle authority")
        if len(records) > 1:
            raise ValueError("rollover history contains multiple unbound records")
        return ()
    bound_indices = [
        index
        for index, record in enumerate(records)
        if record.get("rollover_id") == binding.get("rollover_id")
        and _sha256_bytes(_canonical_json_line(record))
        == binding.get("rollover_sha256")
    ]
    if len(bound_indices) != 1:
        raise ValueError("status rollover binding does not identify one record")
    bound_index = bound_indices[0]
    suffix = records[bound_index + 1 :]
    if suffix and not allow_unbound_suffix:
        raise ValueError("unbound rollover history is not lifecycle authority")
    if len(suffix) > 1:
        raise ValueError("rollover history contains multiple unbound records")
    completed = records[: bound_index + 1]
    if not completed:
        raise ValueError("successor status requires a canonical rollover chain")

    grant_path = _load_role_path(root, manifest, "increment_grants")
    action_path = _load_role_path(root, manifest, "action_authorizations")
    approval_path = _load_role_path(root, manifest, "approvals")
    grants, grant_issues = load_json_lines(grant_path)
    actions, action_issues = load_json_lines(action_path)
    approvals, approval_issues = load_json_lines(approval_path)
    if grants is None:
        raise ValueError("; ".join(grant_issues))
    if actions is None:
        raise ValueError("; ".join(action_issues))
    if approvals is None:
        raise ValueError("; ".join(approval_issues))
    is_setup_program = status.get("schema_version") == "implementation-program-status/v3"
    setup_semantics = manifest.get("setup_semantics")
    setup_envelope = (
        setup_semantics.get("operation_envelope")
        if isinstance(setup_semantics, Mapping)
        else None
    )
    is_setup_v2 = (
        is_setup_program
        and isinstance(setup_semantics, Mapping)
        and setup_semantics.get("schema_version")
        == "implementation-program-setup-semantics/v2"
        and isinstance(setup_envelope, Mapping)
        and setup_envelope.get("schema_version")
        == "implementation-operation-envelope/v2"
    )
    activation = (
        status.get("setup_activation_binding")
        if is_setup_program
        else status.get("activation_binding")
    )
    if not isinstance(activation, Mapping):
        raise ValueError("rollover chain activation authority is required")
    genesis_grants = [
        grant
        for grant in grants
        if (
            grant.get("grant_kind") == "first-increment-start"
            if is_setup_program
            else grant.get("grant_id") == activation.get("increment_grant_id")
        )
    ]
    if len(genesis_grants) != 1:
        raise ValueError("rollover chain genesis grant must exist exactly once")
    genesis_grant = genesis_grants[0]
    if (
        genesis_grant.get("schema_version")
        != (
            "implementation-increment-grant/v2"
            if is_setup_program
            else INCREMENT_GRANT_SCHEMA
        )
        or genesis_grant.get("decision") != "granted"
        or genesis_grant.get("program_id") != status.get("program_id")
        or genesis_grant.get("program_revision")
        != status.get("program_revision")
        or (
            is_setup_program
            and genesis_grant.get("setup_activation_decision_id")
            != activation.get("setup_activation_decision_id")
        )
        or (
            not is_setup_program
            and (
                genesis_grant.get("launch_checkpoint_id")
                != activation.get("launch_checkpoint_id")
                or genesis_grant.get("program_approval_event_id")
                != activation.get("program_approval_event_id")
                or genesis_grant.get("workspace_approval_event_id")
                != activation.get("workspace_approval_event_id")
            )
        )
    ):
        raise ValueError("rollover chain genesis grant authority is invalid")
    expected_authority: dict[str, object] = {
        "schema_version": (
            "implementation-current-increment-authority-binding/v2"
            if is_setup_program
            else CURRENT_INCREMENT_AUTHORITY_SCHEMA
        ),
        "kind": "increment-grant",
        **({"grant_kind": "first-increment-start"} if is_setup_program else {}),
        "increment_id": genesis_grant.get("increment_id"),
        "grant_id": genesis_grant.get("grant_id"),
        "grant_sha256": _sha256_bytes(_canonical_json_line(genesis_grant)),
    }
    if is_setup_program:
        start_intent = genesis_grant.get("start_intent")
        expected_authority.update(
            start_intent_id=(
                start_intent.get("intent_id")
                if isinstance(start_intent, dict)
                else None
            ),
            start_intent_sha256=genesis_grant.get("start_intent_sha256"),
            source_gate_satisfaction=genesis_grant.get(
                "source_gate_satisfaction"
            ),
        )
    expected_current: str | None = None
    for index, record in enumerate(completed):
        record_is_v2 = record.get("schema_version") == ROLLOVER_RECORD_SCHEMA_V2
        if record.get("schema_version") != (
            ROLLOVER_RECORD_SCHEMA_V2 if is_setup_v2 else ROLLOVER_RECORD_SCHEMA
        ):
            raise ValueError("rollover chain contains an unsupported record")
        current = record.get("current_increment_id")
        successor = record.get("successor_increment_id")
        if (
            not isinstance(current, str)
            or not isinstance(successor, str)
            or not current
            or not successor
            or current == successor
            or current != expected_authority.get("increment_id")
            or record.get("program_id") != status.get("program_id")
            or record.get("program_revision") != status.get("program_revision")
        ):
            raise ValueError("rollover chain increment authority is invalid")
        if index and current != expected_current:
            raise ValueError("rollover chain is not contiguous")
        if record.get("prior_increment_authority_binding") != expected_authority:
            raise ValueError("rollover chain prior increment authority is invalid")
        matching_actions = [
            action
            for action in actions
            if action.get("authorization_id")
            == record.get("rollover_authorization_id")
        ]
        if len(matching_actions) != 1:
            raise ValueError("rollover chain action authority must exist exactly once")
        action = matching_actions[0]
        if (
            action.get("schema_version")
            != (
                ACTION_AUTHORIZATION_SCHEMA_V3
                if is_setup_v2
                else (
                    "implementation-action-authorization/v2"
                    if is_setup_program
                    else ACTION_AUTHORIZATION_SCHEMA
                )
            )
            or action.get("decision") != "authorized"
            or action.get("actions") != ["rollover-increment"]
            or action.get("program_id") != status.get("program_id")
            or action.get("program_revision") != status.get("program_revision")
            or action.get("current_increment_id") != current
            or action.get("successor_increment_id") != successor
            or _sha256_bytes(
                (
                    (
                        json.dumps(
                            action,
                            ensure_ascii=False,
                            separators=(",", ":"),
                            sort_keys=False,
                        )
                        + "\n"
                    ).encode("utf-8")
                    if record_is_v2
                    else _canonical_json_line(action)
                )
            )
            != record.get("rollover_authorization_sha256")
        ):
            raise ValueError("rollover chain action authority is invalid")
        if record_is_v2 and (
            tuple(action) != SETUP_V2_ROLLOVER_ACTION_FIELDS
            or action.get("product_result_schema_version")
            != PRODUCT_PATH_STATES_SCHEMA_V2
            or action.get("product_result_sha256")
            != record.get("product_result_sha256")
            or action.get("continuation_domain")
            != record.get("continuation_domain")
            or action.get("continuation_checkpoint_id")
            != record.get("continuation_checkpoint_id")
            or action.get("accepted_status_sha256")
            != record.get("accepted_status_sha256")
            or action.get("accepted_status_sequence")
            != record.get("accepted_status_sequence")
            or action.get("workspace") != record.get("selected_workspace")
            or action.get("submitted_prompt_sha256")
            != record.get("submitted_prompt_sha256")
            or action.get("increment_grant_id")
            != expected_authority.get("grant_id")
            or action.get("increment_grant_sha256")
            != expected_authority.get("grant_sha256")
            or "accepted_product_delta_sha256" in action
        ):
            raise ValueError("rollover chain action v3 binding is invalid")
        matching_grants = [
            grant
            for grant in grants
            if grant.get("grant_id") == record.get("successor_grant_id")
        ]
        if len(matching_grants) != 1:
            raise ValueError("rollover chain successor grant must exist exactly once")
        grant = matching_grants[0]
        grant_sha256 = _sha256_bytes(_canonical_json_line(grant))
        if (
            grant.get("schema_version")
            != (
                "implementation-increment-grant/v2"
                if is_setup_program
                else INCREMENT_GRANT_SCHEMA
            )
            or grant.get("decision") != "granted"
            or grant.get("program_id") != status.get("program_id")
            or grant.get("program_revision") != status.get("program_revision")
            or grant.get("increment_id") != successor
            or grant_sha256 != record.get("successor_grant_sha256")
        ):
            raise ValueError("rollover chain successor grant authority is invalid")
        if record_is_v2:
            try:
                result = product_path_states_v2_from_value(
                    record["accepted_product_result"]
                )
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("rollover chain product result is invalid") from error
            inherited = record.get("inherited_workspace")
            evidence_path = _validate_rollover_file_binding(
                root,
                record.get("review_evidence_binding"),
                label="review evidence",
            )
            packet_path = _validate_rollover_file_binding(
                root,
                record.get("review_packet_binding"),
                label="review packet",
            )
            _validate_rollover_file_binding(
                root,
                record.get("execution_baseline_binding"),
                label="execution baseline",
            )
            _validate_rollover_file_binding(
                root,
                record.get("handoff_binding"),
                label="handoff",
            )
            _validate_rollover_file_binding(
                root,
                record.get("successor_brief_binding"),
                label="successor brief",
            )
            evidence, evidence_issues = load_json_object(evidence_path)
            if evidence is None:
                raise ValueError("; ".join(evidence_issues))
            try:
                packet_markdown = packet_path.read_text(encoding="utf-8")
                from review_coordination import validate_review_bundle

                bundle_issues = validate_review_bundle(evidence, packet_markdown)
            except (OSError, UnicodeError, TypeError, ValueError) as error:
                raise ValueError("rollover review evidence is invalid") from error
            if bundle_issues:
                raise ValueError(
                    "rollover review evidence is invalid: "
                    + "; ".join(bundle_issues)
                )
            accepted_diff = record.get("accepted_diff_binding")
            if not isinstance(accepted_diff, Mapping) or set(accepted_diff) != {
                "diff_disposition_binding",
                "diff_approval_binding",
                "execution_transition_binding",
                "review_evidence_binding",
                "review_packet_binding",
            }:
                raise ValueError("rollover accepted diff binding is invalid")
            disposition = accepted_diff.get("diff_disposition_binding")
            approval_binding = accepted_diff.get("diff_approval_binding")
            transition = accepted_diff.get("execution_transition_binding")
            if (
                accepted_diff.get("review_evidence_binding")
                != record.get("review_evidence_binding")
                or accepted_diff.get("review_packet_binding")
                != record.get("review_packet_binding")
                or not isinstance(disposition, Mapping)
                or disposition.get("schema_version")
                != "implementation-diff-disposition-binding/v2"
                or disposition.get("decision")
                not in {"accept-stop", "accept-continue"}
                or disposition.get("product_result_schema_version")
                != PRODUCT_PATH_STATES_SCHEMA_V2
                or disposition.get("product_result_sha256") != result.sha256
                or "accepted_product_delta_sha256" in disposition
                or not isinstance(transition, Mapping)
                or transition.get("schema_version")
                != "implementation-execution-transition/v2"
                or transition.get("product_path_states")
                != record.get("accepted_product_result")
                or transition.get("product_path_states_sha256") != result.sha256
                or not isinstance(approval_binding, Mapping)
                or approval_binding.get("event_id")
                != disposition.get("approval_event_id")
            ):
                raise ValueError("rollover accepted diff binding is invalid")
            matching_approvals = [
                approval
                for approval in approvals
                if approval.get("event_id") == approval_binding.get("event_id")
                and approval.get("type") == "increment-diff-approval"
            ]
            if len(matching_approvals) != 1:
                raise ValueError("rollover diff approval must exist exactly once")
            approval = matching_approvals[0]
            from diff_disposition import (
                APPROVAL_SCHEMA_V3,
                SETUP_V2_DIFF_APPROVAL_FIELDS,
            )
            from program_continuation import SETUP_V2_CONTINUE_APPROVAL_FIELDS

            approval_sha256 = _sha256_bytes(
                (
                    json.dumps(
                        approval,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=False,
                    )
                    + "\n"
                ).encode("utf-8")
            )
            if (
                approval.get("schema_version") != APPROVAL_SCHEMA_V3
                or tuple(approval)
                != (
                    SETUP_V2_CONTINUE_APPROVAL_FIELDS
                    if disposition.get("decision") == "accept-continue"
                    else SETUP_V2_DIFF_APPROVAL_FIELDS
                )
                or approval.get("diff_decision")
                != disposition.get("decision")
                or approval.get("base_seed_sha256")
                != disposition.get("base_seed_sha256")
                or approval.get("product_result_schema_version")
                != PRODUCT_PATH_STATES_SCHEMA_V2
                or approval.get("product_result_sha256") != result.sha256
                or approval_sha256 != approval_binding.get("sha256")
                or "accepted_product_delta_sha256" in approval
            ):
                raise ValueError("rollover diff approval binding is invalid")
            if disposition.get("decision") == "accept-continue":
                projection = disposition.get("successor_authority_projection")
                if (
                    not isinstance(projection, Mapping)
                    or disposition.get("successor_increment_id") != successor
                    or approval.get("successor_increment_id") != successor
                    or approval.get("successor_authority_projection_sha256")
                    != _sha256_bytes(_canonical_json_bytes(dict(projection)))
                ):
                    raise ValueError("rollover diff approval projection is invalid")
            cumulative = {
                "inherited_path_states": (
                    inherited.get("inherited_path_states")
                    if isinstance(inherited, Mapping)
                    else None
                ),
                "delete_quarantine_bindings": (
                    inherited.get("delete_quarantine_bindings")
                    if isinstance(inherited, Mapping)
                    else None
                ),
            }
            if (
                result.sha256 != record.get("product_result_sha256")
                or record.get("product_result_schema_version")
                != PRODUCT_PATH_STATES_SCHEMA_V2
                or record.get("delete_quarantine_bindings")
                != list(result.delete_quarantine_bindings)
                or not isinstance(inherited, Mapping)
                or inherited.get("schema_version")
                != INHERITED_WORKSPACE_SCHEMA_V2
                or inherited.get("product_result_sha256") != result.sha256
                or inherited.get("accepted_product_result")
                != record.get("accepted_product_result")
                or inherited.get("inherited_path_states_sha256")
                != _sha256_bytes(_canonical_json_bytes(cumulative))
                or record.get("inherited_path_states_sha256")
                != inherited.get("inherited_path_states_sha256")
                or grant.get("product_result_sha256") != result.sha256
                or grant.get("delete_quarantine_bindings")
                != list(result.delete_quarantine_bindings)
                or grant.get("inherited_path_states_sha256")
                != inherited.get("inherited_path_states_sha256")
                or grant.get("continuation_domain")
                != record.get("continuation_domain")
                or grant.get("continuation_checkpoint_id")
                != record.get("continuation_checkpoint_id")
                or grant.get("rollover_authorization_id")
                != record.get("rollover_authorization_id")
                or grant.get("predecessor_increment_authority_binding")
                != record.get("prior_increment_authority_binding")
                or grant.get("predecessor_status_sha256")
                != record.get("accepted_status_sha256")
                or grant.get("predecessor_status_sequence")
                != record.get("accepted_status_sequence")
                or grant.get("submitted_prompt_sha256")
                != record.get("submitted_prompt_sha256")
                or "handoff_addendum_binding" in record
            ):
                raise ValueError("rollover chain v2 result binding is invalid")
        expected_authority = {
            "schema_version": (
                "implementation-current-increment-authority-binding/v2"
                if is_setup_program
                else CURRENT_INCREMENT_AUTHORITY_SCHEMA
            ),
            "kind": "increment-grant",
            **({"grant_kind": "successor-rollover"} if is_setup_program else {}),
            "increment_id": successor,
            "grant_id": grant.get("grant_id"),
            "grant_sha256": grant_sha256,
        }
        if is_setup_program:
            expected_authority["source_gate_satisfaction"] = grant.get(
                "source_gate_satisfaction"
            )
        expected_current = successor
    if (
        expected_current != status.get("current_increment_id")
        or status.get("current_increment_authority_binding") != expected_authority
    ):
        raise ValueError("rollover chain does not reach status-current authority")
    latest = completed[-1]
    if latest.get("schema_version") == ROLLOVER_RECORD_SCHEMA_V2:
        expected_binding = {
            "schema_version": ROLLOVER_BINDING_SCHEMA_V2,
            "rollover_id": latest.get("rollover_id"),
            "rollover_sha256": _sha256_bytes(_canonical_json_line(latest)),
            "continuation_domain": latest.get("continuation_domain"),
            "continuation_checkpoint_id": latest.get("continuation_checkpoint_id"),
            "prior_status_sha256": latest.get("accepted_status_sha256"),
            "prior_status_sequence": latest.get("accepted_status_sequence"),
            "current_increment_id": latest.get("current_increment_id"),
            "successor_increment_id": latest.get("successor_increment_id"),
            "rollover_authorization_id": latest.get("rollover_authorization_id"),
            "rollover_authorization_sha256": latest.get(
                "rollover_authorization_sha256"
            ),
            "successor_grant_id": latest.get("successor_grant_id"),
            "successor_grant_sha256": latest.get("successor_grant_sha256"),
            "submitted_prompt_sha256": latest.get("submitted_prompt_sha256"),
            "product_result_schema_version": latest.get(
                "product_result_schema_version"
            ),
            "product_result_sha256": latest.get("product_result_sha256"),
            "delete_quarantine_bindings": latest.get(
                "delete_quarantine_bindings"
            ),
            "inherited_path_states_sha256": latest.get(
                "inherited_path_states_sha256"
            ),
        }
        if binding != expected_binding:
            raise ValueError("status rollover v2 binding is invalid")
    return tuple(completed)


def _validated_inherited_paths(
    program_root: Path,
    status: Mapping[str, object],
    observation: RepositoryObservation,
    *,
    allow_unbound_suffix: bool,
) -> tuple[str, ...]:
    records = _validated_completed_rollover_records(
        program_root,
        status,
        allow_unbound_suffix=allow_unbound_suffix,
    )
    if not records:
        return ()
    root = Path(program_root).resolve()
    if records[-1].get("schema_version") == ROLLOVER_RECORD_SCHEMA_V2:
        inherited = status.get("inherited_workspace_binding")
        if (
            not isinstance(inherited, Mapping)
            or inherited.get("schema_version") != INHERITED_WORKSPACE_SCHEMA_V2
            or inherited != records[-1].get("inherited_workspace")
        ):
            raise ValueError("status inherited workspace v2 binding is invalid")
        states = inherited.get("inherited_path_states")
        receipts = inherited.get("delete_quarantine_bindings")
        if not isinstance(states, list) or not isinstance(receipts, list):
            raise ValueError("inherited workspace v2 inventory is invalid")
        state_paths = [
            item.get("path") if isinstance(item, Mapping) else None
            for item in states
        ]
        receipt_paths = [
            item.get("path") if isinstance(item, Mapping) else None
            for item in receipts
        ]
        if (
            any(not isinstance(path, str) or not path for path in state_paths)
            or len(set(state_paths)) != len(state_paths)
            or any(not isinstance(path, str) or not path for path in receipt_paths)
            or len(set(receipt_paths)) != len(receipt_paths)
        ):
            raise ValueError("inherited workspace v2 inventory is duplicated")
        cumulative = {
            "inherited_path_states": states,
            "delete_quarantine_bindings": receipts,
        }
        if inherited.get("inherited_path_states_sha256") != _sha256_bytes(
            _canonical_json_bytes(cumulative)
        ):
            raise ValueError("inherited workspace v2 digest mismatch")

        workspace = Path(observation.path).resolve()
        program_relative = Path(os.path.relpath(root, workspace)).as_posix()
        protected_paths = (
            (program_relative,)
            if program_relative not in {"", "."}
            else ()
        )
        current_operations: dict[str, str] = {}
        current_baseline_binding = status.get("execution_baseline_binding")
        if isinstance(current_baseline_binding, Mapping):
            current_baseline_path, current_baseline_path_issues = (
                resolve_managed_path(
                    root,
                    current_baseline_binding.get("path"),
                    role="current execution baseline",
                )
            )
            if current_baseline_path is None:
                raise ValueError("; ".join(current_baseline_path_issues))
            if current_baseline_binding.get("sha256") != sha256_file(
                current_baseline_path
            ):
                raise ValueError("current execution baseline digest mismatch")
            current_baseline_value, current_baseline_issues = load_json_object(
                current_baseline_path
            )
            if current_baseline_value is None:
                raise ValueError("; ".join(current_baseline_issues))
            current_baseline = execution_baseline_v2_from_value(
                current_baseline_value
            )
            current_operations = {
                path: operation
                for operation, paths in (
                    ("Create", current_baseline.file_map.create),
                    ("Modify", current_baseline.file_map.modify),
                    ("Delete", current_baseline.file_map.delete),
                    ("Preserve", current_baseline.file_map.preserve),
                )
                for path in paths
            }
        active_receipts = {
            str(item["path"]): item
            for item in receipts
            if isinstance(item, Mapping)
        }
        for item in states:
            if not isinstance(item, Mapping) or set(item) != {
                "path",
                "exists",
                "sha256",
                "mode",
                "device",
                "inode",
                "link_count",
            }:
                raise ValueError("inherited workspace v2 path state is invalid")
            relative = str(item["path"])
            observed = inspect_workspace_path(
                workspace,
                relative,
                protected_paths=protected_paths,
            )
            expected = {
                "path": relative,
                "exists": item["exists"],
                "sha256": item["sha256"],
                "mode": item["mode"],
                "device": item["device"],
                "inode": item["inode"],
                "link_count": item["link_count"],
            }
            operation = current_operations.get(relative)
            change_is_explicitly_owned = (
                item["exists"] and operation in {"Modify", "Delete"}
            ) or (not item["exists"] and operation == "Create")
            if not change_is_explicitly_owned and asdict(observed) != expected:
                raise ValueError(
                    f"inherited accepted product bytes changed: {relative}"
                )
            if not item["exists"] and relative not in active_receipts:
                raise ValueError(
                    f"inherited Delete receipt binding is missing: {relative}"
                )

        for record in records:
            if record.get("schema_version") != ROLLOVER_RECORD_SCHEMA_V2:
                continue
            baseline_binding = record.get("execution_baseline_binding")
            if not isinstance(baseline_binding, Mapping):
                raise ValueError("rollover execution baseline binding is invalid")
            baseline_path, baseline_path_issues = resolve_managed_path(
                root,
                baseline_binding.get("path"),
                role="rollover execution baseline",
            )
            if baseline_path is None:
                raise ValueError("; ".join(baseline_path_issues))
            if baseline_binding.get("sha256") != sha256_file(baseline_path):
                raise ValueError("rollover execution baseline digest mismatch")
            baseline_value, baseline_issues = load_json_object(baseline_path)
            if baseline_value is None:
                raise ValueError("; ".join(baseline_issues))
            baseline = execution_baseline_v2_from_value(baseline_value)
            baseline_states = {
                str(item["path"]): item["snapshot"]
                for item in baseline.path_baselines
            }
            baseline_deletes = {
                str(item["path"]): item
                for item in baseline.delete_quarantine_bindings
            }
            result = product_path_states_v2_from_value(
                record.get("accepted_product_result")
            )
            for receipt_binding in result.delete_quarantine_bindings:
                relative = str(receipt_binding["path"])
                snapshot = baseline_states.get(relative)
                allocation = baseline_deletes.get(relative)
                if snapshot is None or allocation is None:
                    raise ValueError("rollover Delete baseline binding is invalid")
                receipt_snapshot = inspect_workspace_path(
                    root,
                    str(receipt_binding["receipt_path"]),
                )
                quarantine_snapshot = inspect_workspace_path(
                    root,
                    str(allocation["entry_path"]),
                )
                if (
                    not receipt_snapshot.exists
                    or receipt_snapshot.sha256
                    != receipt_binding["receipt_sha256"]
                    or not quarantine_snapshot.exists
                    or quarantine_snapshot.sha256 != snapshot.sha256
                    or quarantine_snapshot.mode != snapshot.mode
                    or quarantine_snapshot.device != snapshot.device
                    or quarantine_snapshot.inode != snapshot.inode
                    or quarantine_snapshot.link_count != 1
                ):
                    raise ValueError(
                        f"rollover Delete quarantine binding changed: {relative}"
                    )
                recovery = classify_delete_quarantine_recovery(
                    root,
                    workspace,
                    relative,
                    {
                        "increment_id": baseline.increment_id,
                        **asdict(snapshot),
                        **allocation,
                        "quarantine_root_path": allocation["root_path"],
                        "quarantine_root_device": allocation["root_device"],
                        "quarantine_root_inode": allocation["root_inode"],
                        "quarantine_root_mode": allocation["root_mode"],
                        "quarantine_root_owner": allocation["root_owner"],
                    },
                    protected_paths=protected_paths,
                    require_status_current=False,
                )
                if recovery.issues or recovery.receipt is None:
                    raise ValueError(
                        f"rollover Delete quarantine receipt is invalid: {relative}"
                    )
        return tuple(str(path) for path in state_paths)

    latest: dict[str, str] = {}
    for record in records:
        delta = record.get("accepted_product_delta")
        if not isinstance(delta, list):
            raise ValueError("rollover accepted product delta is invalid")
        for item in delta:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("path"), str)
                or not isinstance(item.get("sha256"), str)
            ):
                raise ValueError("rollover accepted product entry is invalid")
            latest[item["path"]] = item["sha256"]
    if status.get("current_increment_state") in {
        "preparing",
        "awaiting-plan-approval",
        "authorized",
    }:
        workspace = Path(observation.path)
        for relative, expected_sha256 in latest.items():
            path = workspace / relative
            if (
                path.is_symlink()
                or not path.is_file()
                or sha256_file(path) != expected_sha256
            ):
                raise ValueError(
                    f"inherited accepted product bytes changed: {relative}"
                )
    return tuple(sorted(latest))


def build_argument_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="program_rollover.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("program_root")
    apply_parser.add_argument("--prompt-file", required=True)
    apply_parser.add_argument("--repository", required=True)
    apply_parser.add_argument("--base-commit", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = build_argument_parser().parse_args(
            list(sys.argv[1:] if argv is None else argv)
        )
        prompt_path = Path(arguments.prompt_file)
        if prompt_path.is_symlink() or not prompt_path.is_file():
            raise ValueError("prompt file must be a regular non-symlink file")
        inspection = inspect_repository(
            Path(arguments.repository), arguments.base_commit
        )
        receipt = persist_increment_rollover(
            Path(arguments.program_root),
            prompt_path.read_text(encoding="utf-8"),
            inspection.observation,
        )
    except (_UsageError, OSError, TypeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2 if isinstance(error, _UsageError) else 1
    print(json.dumps(asdict(receipt), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
