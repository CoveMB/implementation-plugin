#!/usr/bin/env python3
"""Derive prompt-bound immediate and accepted-state continuation authority."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from diff_disposition import (
    DIFF_DISPOSITION_BINDING_SCHEMA,
    DIFF_DISPOSITION_COMMAND_SCHEMA,
    DiffAcceptanceCandidate,
)
from continuity_closure import select_unique_satisfied_successor
from program_activation import (
    _canonical_json_bytes,
    _canonical_json_line,
    _identifier,
    _without_owned_program_paths,
)
from program_authority import (
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
)
from repository_preparation import (
    execution_baseline_from_value,
    inspect_repository,
    validate_execution_workspace,
)
from state_authority import RepositoryObservation
from task_prompt import parse_exact_prompt, render_exact_prompt


SUCCESSOR_PROJECTION_SCHEMA = "implementation-successor-authority-projection/v1"
ACCEPTED_STATE_CONTINUATION_SCHEMA = (
    "implementation-accepted-state-continuation-binding/v1"
)


@dataclass(frozen=True)
class ProductDeltaPath:
    path: str
    disposition: str
    sha256: str


@dataclass(frozen=True)
class ContinuationExtension:
    successor_increment_id: str
    successor_brief_bytes: bytes
    accepted_product_delta: tuple[ProductDeltaPath, ...]
    checkpoint_id: str
    rollover_authorization_id: str
    successor_grant_id: str
    successor_projection: Mapping[str, object]


@dataclass(frozen=True)
class ContinuationCommand:
    schema_version: str
    base_seed_sha256: str
    checkpoint_id: str
    rollover_authorization_id: str
    successor_grant_id: str
    accepted_status_sha256: str
    accepted_status_sequence: int
    program_id: str
    program_revision: int
    current_increment_id: str
    successor_increment_id: str
    successor_brief_sha256: str
    accepted_product_delta_sha256: str
    successor_approval_mode: str
    selected_workspace: Mapping[str, object]
    inherited_workspace: Mapping[str, object]
    allowed_conditional_action_ceiling: tuple[str, ...]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_role(
    root: Path,
    manifest: dict[str, object],
    role: str,
) -> tuple[dict[str, object], Path]:
    roles = manifest.get("logical_roles")
    if not isinstance(roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    path, path_issues = resolve_managed_path(
        root, roles.get(role), role=f"logical role {role}"
    )
    if path is None:
        raise ValueError("; ".join(path_issues))
    value, value_issues = load_json_object(path)
    if value is None:
        raise ValueError("; ".join(value_issues))
    return value, path


def _accepted_increment_ids(
    root: Path,
    status: Mapping[str, object],
    *,
    allow_unbound_rollover_suffix: bool,
) -> set[str]:
    current_increment_id = status.get("current_increment_id")
    if not isinstance(current_increment_id, str) or not current_increment_id:
        raise ValueError("status current increment is required")
    from program_rollover import _validated_completed_rollover_records

    completed = _validated_completed_rollover_records(
        root,
        status,
        allow_unbound_suffix=allow_unbound_rollover_suffix,
    )
    accepted = {current_increment_id}
    accepted.update(str(record["current_increment_id"]) for record in completed)
    return accepted


def _successor_selection(
    root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
    *,
    allow_unbound_rollover_suffix: bool = False,
) -> tuple[str | None, str]:
    traceability, _ = _load_role(root, manifest, "traceability")
    requirements = traceability.get("atomic_requirements")
    if not isinstance(requirements, list):
        raise ValueError("traceability atomic_requirements must be a list")
    current = status.get("current_increment_id")
    if not isinstance(current, str) or not current:
        raise ValueError("status current increment is required")
    for requirement in requirements:
        assigned = requirement.get("assigned_increments") if isinstance(requirement, dict) else None
        if not isinstance(assigned, list):
            raise ValueError("traceability assigned_increments must be a list")
    accepted = _accepted_increment_ids(
        root,
        status,
        allow_unbound_rollover_suffix=allow_unbound_rollover_suffix,
    )
    return select_unique_satisfied_successor(requirements, current, accepted)


def continuation_unavailability_reason(
    program_root: Path,
    acceptance: DiffAcceptanceCandidate,
) -> str:
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    successor, reason = _successor_selection(root, manifest, acceptance.accepted_status)
    return "" if successor is not None else reason


def _live_product_delta(
    root: Path,
    status: dict[str, object],
    observation: RepositoryObservation,
) -> tuple[tuple[ProductDeltaPath, ...], str]:
    baseline_binding = status.get("execution_baseline_binding")
    if not isinstance(baseline_binding, dict):
        raise ValueError("execution baseline binding is required")
    baseline_path, path_issues = resolve_managed_path(
        root,
        baseline_binding.get("path"),
        role="execution baseline binding",
    )
    if baseline_path is None:
        raise ValueError("; ".join(path_issues))
    baseline_value, baseline_issues = load_json_object(baseline_path)
    if baseline_value is None:
        raise ValueError("; ".join(baseline_issues))
    baseline = execution_baseline_from_value(baseline_value)
    inspection = inspect_repository(Path(observation.path), observation.base_commit)
    inspection = replace(
        inspection,
        observation=_without_owned_program_paths(root, inspection.observation),
    )
    assessment = validate_execution_workspace(
        root,
        baseline,
        inspection,
        increment_state=str(status.get("current_increment_state")),
    )
    if not assessment.valid:
        raise ValueError("; ".join(assessment.issues))
    expected = status.get("execution_transition_binding")
    expected_sha256 = (
        expected.get("product_delta_sha256") if isinstance(expected, dict) else None
    )
    if assessment.product_delta_sha256 != expected_sha256:
        raise ValueError("live accepted product delta changed")
    product_delta = tuple(
        ProductDeltaPath(
            path=str(item["path"]),
            disposition=str(item["disposition"]),
            sha256=str(item["sha256"]),
        )
        for item in assessment.product_delta
    )
    return product_delta, assessment.product_delta_sha256


def _successor_brief_bytes(
    traceability: dict[str, object],
    status: dict[str, object],
    successor_increment_id: str,
    selected_workspace: Mapping[str, object],
) -> bytes:
    requirements = [
        requirement
        for requirement in traceability.get("atomic_requirements", [])
        if isinstance(requirement, dict)
        and successor_increment_id in requirement.get("assigned_increments", [])
    ]
    if not requirements:
        raise ValueError("successor has no traceability-allocated requirements")
    lines = [
        f"# {successor_increment_id} increment brief",
        "",
        f"- Program: `{status['program_id']}` revision `{status['program_revision']}`",
        f"- Increment: `{successor_increment_id}`",
        f"- Approval mode: `{status['approval_mode']}`",
        (
            "- Workspace: "
            f"`{selected_workspace['path']}` on `{selected_workspace['branch']}`"
        ),
        "- Requirements:",
    ]
    for requirement in sorted(requirements, key=lambda item: str(item["id"])):
        criteria = "; ".join(str(item) for item in requirement["acceptance_criteria"])
        lines.append(
            f"  - `{requirement['id']}`: {requirement['normalized_requirement']} "
            f"Acceptance: {criteria}"
        )
    lines.extend(
        (
            "- Authority: navigation only until the successor grant is status-current.",
            "",
        )
    )
    return "\n".join(lines).encode("utf-8")


def _continuation_inputs(
    root: Path,
    acceptance: DiffAcceptanceCandidate,
    observation: RepositoryObservation,
    *,
    allow_unbound_rollover_suffix: bool,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    str,
    bytes,
    tuple[ProductDeltaPath, ...],
    str,
    dict[str, object],
    tuple[str, ...],
]:
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, _ = _load_role(root, manifest, "status")
    workspace, workspace_path = _load_role(root, manifest, "workspace")
    traceability, _ = _load_role(root, manifest, "traceability")
    successor, reason = _successor_selection(
        root,
        manifest,
        status,
        allow_unbound_rollover_suffix=allow_unbound_rollover_suffix,
    )
    if successor is None:
        raise ValueError(reason)
    selected = workspace.get("implementation_workspace")
    if not isinstance(selected, dict):
        raise ValueError("workspace selection is incomplete")
    selected_workspace = {
        "path": observation.path,
        "branch": observation.branch,
        "base_commit": observation.base_commit,
        "head_commit": observation.head_commit,
    }
    selected_pairs = (
        ("path", selected.get("path"), observation.path),
        ("branch", selected.get("branch"), observation.branch),
        ("base_commit", selected.get("base_commit"), observation.base_commit),
    )
    if any(persisted != observed for _label, persisted, observed in selected_pairs):
        raise ValueError("selected workspace changed before continuation")
    product_delta, product_delta_sha256 = _live_product_delta(
        root, status, observation
    )
    inherited_workspace = {
        "selected_workspace": selected_workspace,
        "accepted_product_delta": [asdict(item) for item in product_delta],
        "accepted_product_delta_sha256": product_delta_sha256,
    }
    authority = status.get("current_increment_authority_binding")
    if not isinstance(authority, dict):
        raise ValueError("status-current increment authority is required")
    roles = manifest.get("logical_roles")
    if not isinstance(roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    grants_path, grant_path_issues = resolve_managed_path(
        root, roles.get("increment_grants"), role="logical role increment_grants"
    )
    if grants_path is None:
        raise ValueError("; ".join(grant_path_issues))
    grants, grant_issues = load_json_lines(grants_path)
    if grants is None:
        raise ValueError("; ".join(grant_issues))
    matching = [
        record for record in grants if record.get("grant_id") == authority.get("grant_id")
    ]
    if len(matching) != 1:
        raise ValueError("status-current increment grant must exist exactly once")
    allowed = matching[0].get("allowed_conditional_actions")
    if not isinstance(allowed, list) or not all(
        isinstance(item, str) and item for item in allowed
    ):
        raise ValueError("current grant conditional-action ceiling is invalid")
    brief_bytes = _successor_brief_bytes(
        traceability, status, successor, selected_workspace
    )
    return (
        manifest,
        status,
        workspace,
        successor,
        brief_bytes,
        product_delta,
        product_delta_sha256,
        inherited_workspace,
        tuple(allowed),
    )


def _immediate_base_seed(
    acceptance: DiffAcceptanceCandidate,
    *,
    successor_increment_id: str,
    successor_brief_sha256: str,
    accepted_product_delta_sha256: str,
    successor_approval_mode: str,
    selected_workspace: Mapping[str, object],
    workspace_selection_sha256: str,
    inherited_workspace_sha256: str,
    allowed_conditional_action_ceiling: tuple[str, ...],
) -> dict[str, object]:
    binding = acceptance.accepted_status["diff_disposition_binding"]
    return {
        "schema_domain": SUCCESSOR_PROJECTION_SCHEMA,
        "program_id": binding["program_id"],
        "program_revision": binding["program_revision"],
        "current_increment_id": binding["increment_id"],
        "successor_increment_id": successor_increment_id,
        "prior_status_sha256": binding["prior_status_sha256"],
        "prior_status_sequence": binding["prior_status_sequence"],
        "decision": "accept-continue",
        "review_evidence_sha256": binding["review_evidence_sha256"],
        "review_packet_sha256": binding["review_packet_sha256"],
        "verification_sha256": binding["verification_sha256"],
        "exact_file_plan_sha256": binding["exact_file_plan_sha256"],
        "execution_baseline_sha256": binding["execution_baseline_sha256"],
        "accepted_product_delta_sha256": accepted_product_delta_sha256,
        "successor_brief_sha256": successor_brief_sha256,
        "successor_approval_mode": successor_approval_mode,
        "selected_workspace": dict(selected_workspace),
        "workspace_selection_sha256": workspace_selection_sha256,
        "inherited_workspace_sha256": inherited_workspace_sha256,
        "allowed_conditional_action_ceiling": list(
            allowed_conditional_action_ceiling
        ),
    }


def _build_continuation_extension(
    program_root: Path,
    acceptance: DiffAcceptanceCandidate,
    observation: RepositoryObservation,
    *,
    allow_unbound_rollover_suffix: bool,
) -> ContinuationExtension | None:
    """Derive a continuation extension only for one satisfied successor."""
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    successor, _reason = _successor_selection(
        root,
        manifest,
        acceptance.accepted_status,
        allow_unbound_rollover_suffix=allow_unbound_rollover_suffix,
    )
    if successor is None:
        return None
    (
        _manifest,
        status,
        _workspace,
        successor,
        brief_bytes,
        product_delta,
        product_delta_sha256,
        inherited_workspace,
        allowed,
    ) = _continuation_inputs(
        root,
        acceptance,
        observation,
        allow_unbound_rollover_suffix=allow_unbound_rollover_suffix,
    )
    roles = manifest["logical_roles"]
    workspace_path, workspace_path_issues = resolve_managed_path(
        root, roles.get("workspace"), role="logical role workspace"
    )
    if workspace_path is None:
        raise ValueError("; ".join(workspace_path_issues))
    selected_workspace = inherited_workspace["selected_workspace"]
    brief_sha256 = _sha256_bytes(brief_bytes)
    inherited_sha256 = _sha256_bytes(_canonical_json_bytes(inherited_workspace))
    base_seed = _immediate_base_seed(
        acceptance,
        successor_increment_id=successor,
        successor_brief_sha256=brief_sha256,
        accepted_product_delta_sha256=product_delta_sha256,
        successor_approval_mode=str(status["approval_mode"]),
        selected_workspace=selected_workspace,
        workspace_selection_sha256=sha256_file(workspace_path),
        inherited_workspace_sha256=inherited_sha256,
        allowed_conditional_action_ceiling=allowed,
    )
    base_seed_sha256 = _sha256_bytes(_canonical_json_bytes(base_seed))
    checkpoint_id = _identifier(
        "diff-checkpoint", {"base_seed_sha256": base_seed_sha256}
    )
    approval_event_id = _identifier(
        "diff-approval",
        {
            "base_seed_sha256": base_seed_sha256,
            "checkpoint_id": checkpoint_id,
        },
    )
    rollover_authorization_id = _identifier(
        "rollover-action",
        {
            "base_seed_sha256": base_seed_sha256,
            "checkpoint_id": checkpoint_id,
            "approval_event_id": approval_event_id,
        },
    )
    successor_grant_id = _identifier(
        "successor-grant",
        {
            "base_seed_sha256": base_seed_sha256,
            "checkpoint_id": checkpoint_id,
            "approval_event_id": approval_event_id,
            "rollover_authorization_id": rollover_authorization_id,
        },
    )
    projection = {
        "schema_version": SUCCESSOR_PROJECTION_SCHEMA,
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "current_increment_id": status["current_increment_id"],
        "successor_increment_id": successor,
        "prior_status_sha256": base_seed["prior_status_sha256"],
        "prior_status_sequence": base_seed["prior_status_sequence"],
        "checkpoint_id": checkpoint_id,
        "approval_event_id": approval_event_id,
        "successor_brief_sha256": brief_sha256,
        "accepted_product_delta_sha256": product_delta_sha256,
        "successor_approval_mode": status["approval_mode"],
        "selected_workspace": selected_workspace,
        "workspace_selection_sha256": sha256_file(workspace_path),
        "inherited_workspace_sha256": inherited_sha256,
        "allowed_conditional_action_ceiling": list(allowed),
        "rollover_authorization_id": rollover_authorization_id,
        "successor_grant_id": successor_grant_id,
    }
    return ContinuationExtension(
        successor_increment_id=successor,
        successor_brief_bytes=brief_bytes,
        accepted_product_delta=product_delta,
        checkpoint_id=checkpoint_id,
        rollover_authorization_id=rollover_authorization_id,
        successor_grant_id=successor_grant_id,
        successor_projection=projection,
    )


def build_continuation_extension(
    program_root: Path,
    acceptance: DiffAcceptanceCandidate,
    observation: RepositoryObservation,
) -> ContinuationExtension | None:
    """Derive a continuation extension only for one satisfied successor."""
    try:
        return _build_continuation_extension(
            program_root,
            acceptance,
            observation,
            allow_unbound_rollover_suffix=False,
        )
    except ValueError as error:
        if str(error) != "unbound rollover history is not lifecycle authority":
            raise
        from program_rollover import inspect_increment_rollover

        inspection = inspect_increment_rollover(program_root, observation)
        if (
            inspection.issues
            or inspection.disposition
            not in {
                "increment-rollover-retry-ready",
                "accepted-state-rollover-retry-ready",
            }
            or inspection.completed_steps
            != (
                "action-authorization",
                "successor-grant",
                "handoff",
                "successor-brief",
                "rollover-record",
            )
        ):
            raise error
        return _build_continuation_extension(
            program_root,
            acceptance,
            observation,
            allow_unbound_rollover_suffix=True,
        )


def successor_projection_sha256(projection: Mapping[str, object]) -> str:
    return _sha256_bytes(_canonical_json_bytes(dict(projection)))


def build_accept_continue_candidate(
    acceptance: DiffAcceptanceCandidate,
    extension: ContinuationExtension | None,
) -> DiffAcceptanceCandidate:
    """Extend a validated Plan A acceptance without changing its stop candidate."""
    if extension is None:
        raise ValueError("accept-continue requires one satisfied successor")
    projection = dict(extension.successor_projection)
    base_seed = _immediate_base_seed(
        acceptance,
        successor_increment_id=extension.successor_increment_id,
        successor_brief_sha256=str(projection["successor_brief_sha256"]),
        accepted_product_delta_sha256=str(
            projection["accepted_product_delta_sha256"]
        ),
        successor_approval_mode=str(projection["successor_approval_mode"]),
        selected_workspace=projection["selected_workspace"],
        workspace_selection_sha256=str(projection["workspace_selection_sha256"]),
        inherited_workspace_sha256=str(projection["inherited_workspace_sha256"]),
        allowed_conditional_action_ceiling=tuple(
            str(item) for item in projection["allowed_conditional_action_ceiling"]
        ),
    )
    base_seed_sha256 = _sha256_bytes(_canonical_json_bytes(base_seed))
    checkpoint_id = extension.checkpoint_id
    approval_event_id = str(projection["approval_event_id"])
    binding = {
        "schema_version": DIFF_DISPOSITION_BINDING_SCHEMA,
        **{
            key: value
            for key, value in acceptance.accepted_status[
                "diff_disposition_binding"
            ].items()
            if key
            not in {
                "schema_version",
                "decision",
                "base_seed_sha256",
                "checkpoint_id",
                "approval_event_id",
            }
        },
        "decision": "accept-continue",
        "base_seed_sha256": base_seed_sha256,
        "checkpoint_id": checkpoint_id,
        "approval_event_id": approval_event_id,
        "successor_increment_id": extension.successor_increment_id,
        "successor_brief_sha256": projection["successor_brief_sha256"],
        "rollover_action_authorization_id": extension.rollover_authorization_id,
        "successor_grant_id": extension.successor_grant_id,
        "inherited_product_delta_sha256": projection[
            "accepted_product_delta_sha256"
        ],
        "successor_authority_projection": projection,
    }
    accepted_status = dict(acceptance.accepted_status)
    accepted_status["transition_authority"] = {
        "kind": "approval-event",
        "event_id": approval_event_id,
        "checkpoint_id": checkpoint_id,
    }
    accepted_status["diff_disposition_binding"] = binding
    accepted_status_bytes = _canonical_json_bytes(accepted_status)
    command = {
        "schema_version": DIFF_DISPOSITION_COMMAND_SCHEMA,
        "decision": "accept-continue",
        "base_seed_sha256": base_seed_sha256,
        "checkpoint_id": checkpoint_id,
        "approval_event_id": approval_event_id,
        "accepted_status_sha256": _sha256_bytes(accepted_status_bytes),
        "successor_authority_projection": projection,
    }
    prompt = render_exact_prompt(command)
    approval_record = {
        **acceptance.approval_record,
        "event_id": approval_event_id,
        "scope": [
            "accept the bound current increment and continue to the bound successor"
        ],
        "diff_decision": "accept-continue",
        "base_seed_sha256": base_seed_sha256,
        "checkpoint_id": checkpoint_id,
        "submitted_prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
        "successor_increment_id": extension.successor_increment_id,
        "successor_authority_projection_sha256": successor_projection_sha256(
            projection
        ),
    }
    return DiffAcceptanceCandidate(
        base_seed_sha256=base_seed_sha256,
        checkpoint_id=checkpoint_id,
        approval_event_id=approval_event_id,
        decision="accept-continue",
        approval_bytes=_canonical_json_line(approval_record),
        accepted_status_bytes=accepted_status_bytes,
        prompt=prompt,
        approval_record=approval_record,
        accepted_status=accepted_status,
    )


def _render_accept_continue_prompt(
    program_root: Path,
    *,
    allow_unbound_rollover_suffix: bool = False,
) -> str:
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    workspace, _ = _load_role(root, manifest, "workspace")
    selected = workspace["implementation_workspace"]
    observation = inspect_repository(
        Path(selected["path"]), selected["base_commit"]
    ).observation
    from diff_disposition import build_diff_acceptance_candidate

    acceptance = build_diff_acceptance_candidate(root, observation)
    extension = _build_continuation_extension(
        root,
        acceptance,
        observation,
        allow_unbound_rollover_suffix=allow_unbound_rollover_suffix,
    )
    if extension is None:
        raise ValueError(continuation_unavailability_reason(root, acceptance))
    candidate = build_accept_continue_candidate(acceptance, extension)
    return (
        f"Accept and continue to `{extension.successor_increment_id}`.\n\n"
        f"{candidate.prompt}"
    )


def render_accept_continue_prompt(program_root: Path) -> str:
    return _render_accept_continue_prompt(program_root)


def _build_accepted_state_command(
    program_root: Path,
    *,
    allow_unbound_rollover_suffix: bool = False,
) -> ContinuationCommand:
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, status_path = _load_role(root, manifest, "status")
    binding = status.get("diff_disposition_binding")
    if (
        status.get("program_state") != "active"
        or status.get("current_increment_state") != "accepted"
        or not isinstance(binding, dict)
        or binding.get("decision") != "accept-stop"
    ):
        raise ValueError("accepted-state continuation requires exact accept-stop status")
    workspace, workspace_path = _load_role(root, manifest, "workspace")
    selected = workspace["implementation_workspace"]
    observation = inspect_repository(
        Path(selected["path"]), selected["base_commit"]
    ).observation
    from diff_disposition import build_diff_acceptance_candidate

    acceptance = build_diff_acceptance_candidate(root, observation)
    extension = _build_continuation_extension(
        root,
        acceptance,
        observation,
        allow_unbound_rollover_suffix=allow_unbound_rollover_suffix,
    )
    if extension is None:
        raise ValueError(continuation_unavailability_reason(root, acceptance))
    projection = dict(extension.successor_projection)
    selected_workspace = projection["selected_workspace"]
    inherited_workspace = {
        "selected_workspace": selected_workspace,
        "accepted_product_delta": [asdict(item) for item in extension.accepted_product_delta],
        "accepted_product_delta_sha256": projection[
            "accepted_product_delta_sha256"
        ],
    }
    base_seed = {
        "schema_domain": ACCEPTED_STATE_CONTINUATION_SCHEMA,
        "accepted_status_sha256": sha256_file(status_path),
        "accepted_status_sequence": status["state_sequence"],
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "current_increment_id": status["current_increment_id"],
        "successor_increment_id": extension.successor_increment_id,
        "successor_brief_sha256": projection["successor_brief_sha256"],
        "accepted_product_delta_sha256": projection[
            "accepted_product_delta_sha256"
        ],
        "successor_approval_mode": projection["successor_approval_mode"],
        "selected_workspace": selected_workspace,
        "workspace_selection_sha256": sha256_file(workspace_path),
        "inherited_workspace": inherited_workspace,
        "allowed_conditional_action_ceiling": projection[
            "allowed_conditional_action_ceiling"
        ],
    }
    base_seed_sha256 = _sha256_bytes(_canonical_json_bytes(base_seed))
    checkpoint_id = _identifier(
        "accepted-continuation-checkpoint",
        {"base_seed_sha256": base_seed_sha256},
    )
    rollover_authorization_id = _identifier(
        "accepted-rollover-action",
        {
            "base_seed_sha256": base_seed_sha256,
            "checkpoint_id": checkpoint_id,
        },
    )
    successor_grant_id = _identifier(
        "accepted-successor-grant",
        {
            "base_seed_sha256": base_seed_sha256,
            "checkpoint_id": checkpoint_id,
            "rollover_authorization_id": rollover_authorization_id,
        },
    )
    return ContinuationCommand(
        schema_version=ACCEPTED_STATE_CONTINUATION_SCHEMA,
        base_seed_sha256=base_seed_sha256,
        checkpoint_id=checkpoint_id,
        rollover_authorization_id=rollover_authorization_id,
        successor_grant_id=successor_grant_id,
        accepted_status_sha256=sha256_file(status_path),
        accepted_status_sequence=int(status["state_sequence"]),
        program_id=str(status["program_id"]),
        program_revision=int(status["program_revision"]),
        current_increment_id=str(status["current_increment_id"]),
        successor_increment_id=extension.successor_increment_id,
        successor_brief_sha256=str(projection["successor_brief_sha256"]),
        accepted_product_delta_sha256=str(
            projection["accepted_product_delta_sha256"]
        ),
        successor_approval_mode=str(projection["successor_approval_mode"]),
        selected_workspace=selected_workspace,
        inherited_workspace=inherited_workspace,
        allowed_conditional_action_ceiling=tuple(
            str(item) for item in projection["allowed_conditional_action_ceiling"]
        ),
    )


def _render_accepted_state_continuation_prompt(
    program_root: Path,
    *,
    allow_unbound_rollover_suffix: bool = False,
) -> str:
    command = _build_accepted_state_command(
        program_root,
        allow_unbound_rollover_suffix=allow_unbound_rollover_suffix,
    )
    return render_exact_prompt(asdict(command))


def render_accepted_state_continuation_prompt(program_root: Path) -> str:
    return _render_accepted_state_continuation_prompt(program_root)


def validate_submitted_continuation_prompt(
    program_root: Path,
    submitted_prompt: str,
) -> ContinuationCommand:
    parse_exact_prompt(submitted_prompt, ACCEPTED_STATE_CONTINUATION_SCHEMA)
    expected = _build_accepted_state_command(program_root)
    if render_exact_prompt(asdict(expected)) != submitted_prompt:
        raise ValueError("submitted accepted-state continuation prompt is stale")
    return expected


def _validate_submitted_continuation_prompt_for_rollover_retry(
    program_root: Path,
    submitted_prompt: str,
) -> ContinuationCommand:
    parse_exact_prompt(submitted_prompt, ACCEPTED_STATE_CONTINUATION_SCHEMA)
    expected = _build_accepted_state_command(
        program_root,
        allow_unbound_rollover_suffix=True,
    )
    if render_exact_prompt(asdict(expected)) != submitted_prompt:
        raise ValueError("submitted accepted-state continuation prompt is stale")
    return expected


class _UsageError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="program_continuation.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("program_root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = build_argument_parser().parse_args(
            list(sys.argv[1:] if argv is None else argv)
        )
        prompt = render_accepted_state_continuation_prompt(
            Path(arguments.program_root)
        )
    except (_UsageError, OSError, TypeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2 if isinstance(error, _UsageError) else 1
    sys.stdout.write(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
