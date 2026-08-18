#!/usr/bin/env python3
"""Render and persist the first-increment accept-stop disposition."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from program_activation import (
    _canonical_json_bytes,
    _canonical_json_line,
    _identifier,
    _replace_or_adopt_status,
    _without_owned_program_paths,
)
from program_authority import load_json_lines, load_json_object, resolve_managed_path, sha256_file
from repository_preparation import inspect_repository
from state_authority import (
    APPROVAL_SCHEMA,
    RepositoryObservation,
    TransitionRequest,
    apply_state_transition,
    atomic_append_json_line,
    validate_state_authority,
)
from task_prompt import parse_exact_prompt, render_exact_prompt


DIFF_DISPOSITION_BINDING_SCHEMA = "implementation-diff-disposition-binding/v1"
DIFF_DISPOSITION_COMMAND_SCHEMA = "implementation-diff-disposition-command/v1"


@dataclass(frozen=True)
class DiffAcceptanceCandidate:
    base_seed_sha256: str
    checkpoint_id: str
    approval_event_id: str
    decision: str
    approval_bytes: bytes
    accepted_status_bytes: bytes
    prompt: str
    approval_record: dict[str, object]
    accepted_status: dict[str, object]


@dataclass(frozen=True)
class DiffDispositionReceipt:
    decision: str
    approval_event_id: str
    increment_state: str
    status_sha256: str
    recovered: bool


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _status_prior(
    status_path: Path, status: dict[str, object]
) -> tuple[str, int]:
    state = status.get("current_increment_state")
    if state == "awaiting-diff-approval":
        return sha256_file(status_path), int(status["state_sequence"])
    binding = status.get("diff_disposition_binding")
    if (
        state != "accepted"
        or not isinstance(binding, dict)
        or binding.get("decision") != "accept-stop"
    ):
        raise ValueError("accept-stop requires awaiting-diff-approval or its exact accepted status")
    return str(binding["prior_status_sha256"]), int(binding["prior_status_sequence"])


def _fresh_observation(
    root: Path, supplied: RepositoryObservation
) -> RepositoryObservation:
    fresh = inspect_repository(Path(supplied.path), supplied.base_commit).observation
    normalized = _without_owned_program_paths(root, fresh)
    if asdict(normalized) != asdict(_without_owned_program_paths(root, supplied)):
        raise ValueError("workspace observation changed before diff disposition")
    return normalized


def build_diff_acceptance_candidate(
    program_root: Path,
    observation: RepositoryObservation,
) -> DiffAcceptanceCandidate:
    """Derive the acyclic accept-stop approval, prompt, and status bytes."""
    root = Path(program_root)
    normalized = _fresh_observation(root, observation)
    state_issues = validate_state_authority(root, normalized)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    roles = manifest.get("logical_roles")
    if not isinstance(roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    status_path, status_path_issues = resolve_managed_path(
        root, roles.get("status"), role="logical role status"
    )
    if status_path is None:
        raise ValueError("; ".join(status_path_issues))
    status, status_issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(status_issues))
    prior_status_sha256, prior_sequence = _status_prior(status_path, status)
    evidence_binding = status.get("review_evidence_binding")
    packet_binding = status.get("review_packet_binding")
    baseline_binding = status.get("execution_baseline_binding")
    execution_transition = status.get("execution_transition_binding")
    if not all(
        isinstance(item, dict)
        for item in (
            evidence_binding,
            packet_binding,
            baseline_binding,
            execution_transition,
        )
    ):
        raise ValueError("diff disposition bindings are incomplete")
    evidence_path, evidence_path_issues = resolve_managed_path(
        root, evidence_binding.get("path"), role="review evidence binding"
    )
    if evidence_path is None:
        raise ValueError("; ".join(evidence_path_issues))
    evidence, evidence_issues = load_json_object(evidence_path)
    if evidence is None:
        raise ValueError("; ".join(evidence_issues))
    verification = evidence.get("final_verification")
    if not isinstance(verification, dict):
        raise ValueError("review evidence final verification is missing")
    verification_sha256 = _sha256_bytes(_canonical_json_bytes(verification))
    accepted_product_delta_sha256 = execution_transition.get(
        "product_delta_sha256"
    )
    base_seed = {
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "increment_id": status["current_increment_id"],
        "prior_status_sha256": prior_status_sha256,
        "prior_status_sequence": prior_sequence,
        "decision": "accept-stop",
        "review_evidence_sha256": evidence_binding["sha256"],
        "review_packet_sha256": packet_binding["sha256"],
        "verification_sha256": verification_sha256,
        "exact_file_plan_sha256": status["approved_exact_file_plan_sha256"],
        "execution_baseline_sha256": baseline_binding["sha256"],
        "accepted_product_delta_sha256": accepted_product_delta_sha256,
    }
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
    disposition_binding = {
        "schema_version": DIFF_DISPOSITION_BINDING_SCHEMA,
        **base_seed,
        "base_seed_sha256": base_seed_sha256,
        "checkpoint_id": checkpoint_id,
        "approval_event_id": approval_event_id,
    }
    accepted_status = dict(status)
    accepted_status.update(
        state_sequence=prior_sequence + 1,
        current_increment_state="accepted",
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": prior_sequence,
            "status_sha256": prior_status_sha256,
        },
        transition_authority={
            "kind": "approval-event",
            "event_id": approval_event_id,
            "checkpoint_id": checkpoint_id,
        },
        diff_disposition_binding=disposition_binding,
    )
    accepted_status_bytes = _canonical_json_bytes(accepted_status)
    command = {
        "schema_version": DIFF_DISPOSITION_COMMAND_SCHEMA,
        "decision": "accept-stop",
        "base_seed_sha256": base_seed_sha256,
        "checkpoint_id": checkpoint_id,
        "approval_event_id": approval_event_id,
        "accepted_status_sha256": _sha256_bytes(accepted_status_bytes),
        **base_seed,
    }
    prompt = render_exact_prompt(command)
    source = status["source_binding"]
    program = status["program_binding"]
    brief = status["brief_binding"]
    approval_record = {
        "schema_version": APPROVAL_SCHEMA,
        "event_id": approval_event_id,
        "type": "increment-diff-approval",
        "decision": "approved",
        "scope": ["accept the bound current increment and stop"],
        "diff_decision": "accept-stop",
        "checkpoint_id": checkpoint_id,
        "base_seed_sha256": base_seed_sha256,
        "submitted_prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "program_sha256": program["sha256"],
        "semantic_requirements_sha256": program["semantic_requirements_sha256"],
        "increment_id": status["current_increment_id"],
        "brief_sha256": brief["sha256"],
        "exact_file_plan_sha256": status["approved_exact_file_plan_sha256"],
        "approval_mode": status["approval_mode"],
        "workspace": {
            "path": normalized.path,
            "branch": normalized.branch,
            "base_commit": normalized.base_commit,
            "head_commit": normalized.head_commit,
        },
        "review_evidence_sha256": evidence_binding["sha256"],
        "review_packet_sha256": packet_binding["sha256"],
        "verification_sha256": verification_sha256,
        "execution_baseline_sha256": baseline_binding["sha256"],
        "accepted_product_delta_sha256": accepted_product_delta_sha256,
    }
    approval_bytes = _canonical_json_line(approval_record)
    return DiffAcceptanceCandidate(
        base_seed_sha256=base_seed_sha256,
        checkpoint_id=checkpoint_id,
        approval_event_id=approval_event_id,
        decision="accept-stop",
        approval_bytes=approval_bytes,
        accepted_status_bytes=accepted_status_bytes,
        prompt=prompt,
        approval_record=approval_record,
        accepted_status=accepted_status,
    )


def render_diff_disposition_prompt(program_root: Path) -> str:
    """Render the one currently supported diff decision."""
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    roles = manifest["logical_roles"]
    workspace_path, workspace_path_issues = resolve_managed_path(
        root, roles["workspace"], role="logical role workspace"
    )
    if workspace_path is None:
        raise ValueError("; ".join(workspace_path_issues))
    workspace, workspace_issues = load_json_object(workspace_path)
    if workspace is None:
        raise ValueError("; ".join(workspace_issues))
    selected = workspace["implementation_workspace"]
    observation = inspect_repository(
        Path(selected["path"]), selected["base_commit"]
    ).observation
    candidate = build_diff_acceptance_candidate(root, observation)
    return "Accept and stop.\n\n" + candidate.prompt


def _append_or_adopt_approval(
    path: Path, candidate: DiffAcceptanceCandidate
) -> bool:
    records, issues = load_json_lines(path)
    if records is None:
        raise ValueError("; ".join(issues))
    matches = [
        record
        for record in records
        if record.get("event_id") == candidate.approval_event_id
    ]
    if matches:
        if (
            len(matches) != 1
            or matches[0] != candidate.approval_record
            or not path.read_bytes().endswith(candidate.approval_bytes)
        ):
            raise ValueError("increment-acceptance-recovery-required: conflicting approval")
        return True
    if any(
        record.get("type") == "increment-diff-approval"
        and record.get("program_id") == candidate.approval_record.get("program_id")
        and record.get("program_revision")
        == candidate.approval_record.get("program_revision")
        and record.get("increment_id")
        == candidate.approval_record.get("increment_id")
        for record in records
    ):
        raise ValueError("increment-acceptance-recovery-required: conflicting approval")
    atomic_append_json_line(path, candidate.approval_record, sha256_file(path))
    return False


def _after_persist(_label: str) -> None:
    """Test seam after a durable accept-stop transaction prefix."""


def persist_accept_stop(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> DiffDispositionReceipt:
    """Append/adopt exact diff approval, then write accepted status last."""
    root = Path(program_root)
    candidate = build_diff_acceptance_candidate(root, observation)
    expected_prompt = "Accept and stop.\n\n" + candidate.prompt
    if submitted_prompt != expected_prompt:
        raise ValueError("submitted diff disposition prompt does not match current bytes")
    parse_exact_prompt(candidate.prompt, DIFF_DISPOSITION_COMMAND_SCHEMA)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    roles = manifest["logical_roles"]
    approvals_path, approval_issues = resolve_managed_path(
        root, roles["approvals"], role="logical role approvals"
    )
    status_path, status_issues = resolve_managed_path(
        root, roles["status"], role="logical role status"
    )
    if approvals_path is None or status_path is None:
        raise ValueError("; ".join([*approval_issues, *status_issues]))
    recovered = _append_or_adopt_approval(approvals_path, candidate)
    _after_persist("diff-approval")
    binding = candidate.accepted_status["diff_disposition_binding"]
    recovered = (
        _replace_or_adopt_status(
            status_path,
            candidate.accepted_status,
            str(binding["prior_status_sha256"]),
            "increment-acceptance",
        )
        or recovered
    )
    _after_persist("accepted-status")
    final_issues = validate_state_authority(root, _fresh_observation(root, observation))
    if final_issues:
        raise ValueError("; ".join(final_issues))
    return DiffDispositionReceipt(
        decision="accept-stop",
        approval_event_id=candidate.approval_event_id,
        increment_state="accepted",
        status_sha256=sha256_file(status_path),
        recovered=recovered,
    )
