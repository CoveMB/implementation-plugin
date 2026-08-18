#!/usr/bin/env python3
"""Prepare and persist exact new-model program closure transactions."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from continuity_closure import (
    CLOSURE_PACKET_SCHEMA,
    RECONCILIATION_SCHEMA,
    ClosurePacket,
    ClosureReconciliation,
    ClosureRequirementDisposition,
    render_closure_packet,
    validate_closure_packet,
    validate_closure_reconciliation,
)
from program_activation import (
    _canonical_json_bytes,
    _canonical_json_line,
    _create_or_adopt_bytes,
    _identifier,
    _replace_or_adopt_status,
    _without_owned_program_paths,
)
from program_authority import (
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    resolve_program_closure_paths,
    sha256_file,
)
from repository_preparation import (
    execution_baseline_from_value,
    inspect_repository,
    parse_exact_file_map,
    validate_execution_workspace,
)
from review_coordination import validate_review_bundle
from state_authority import (
    APPROVAL_SCHEMA,
    RepositoryObservation,
    TransitionRequest,
    _traceability_successor,
    apply_state_transition,
    atomic_append_json_line,
    validate_state_authority,
)
from task_prompt import parse_exact_prompt, render_exact_prompt


CLOSURE_PREPARATION_SCHEMA = "implementation-closure-preparation/v1"
CLOSURE_COMMAND_SCHEMA = "implementation-program-closure-command/v1"
CLOSURE_COMMAND_BINDING_SCHEMA = "implementation-program-closure-command-binding/v1"


@dataclass(frozen=True)
class ClosurePreparationCandidate:
    reconciliation_bytes: bytes
    packet_bytes: bytes
    reconciliation_sha256: str
    packet_sha256: str
    reconciliation_path: Path
    packet_path: Path
    awaiting_status_bytes: bytes
    awaiting_status: dict[str, object]


@dataclass(frozen=True)
class ClosurePreparationReceipt:
    reconciliation_sha256: str
    closure_packet_sha256: str
    program_state: str
    status_sha256: str
    recovered: bool


@dataclass(frozen=True)
class ClosureCommandCandidate:
    base_seed_sha256: str
    checkpoint_id: str
    approval_event_id: str
    prompt: str
    approval_bytes: bytes
    approval_record: dict[str, object]
    closed_status_bytes: bytes
    closed_status: dict[str, object]


@dataclass(frozen=True)
class ClosureReceipt:
    approval_event_id: str
    program_state: str
    status_sha256: str
    recovered: bool


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fresh_observation(
    root: Path, supplied: RepositoryObservation
) -> RepositoryObservation:
    fresh = inspect_repository(Path(supplied.path), supplied.base_commit).observation
    normalized = _without_owned_program_paths(root, fresh)
    if asdict(normalized) != asdict(_without_owned_program_paths(root, supplied)):
        raise ValueError("workspace observation changed before program closure")
    return normalized


def _load_role(
    root: Path, manifest: dict[str, object], role: str
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


def _increment_paths(
    root: Path, manifest: dict[str, object], increment_id: str
) -> dict[str, Path]:
    storage = manifest.get("increment_storage")
    if not isinstance(storage, dict):
        raise ValueError("manifest increment_storage must be an object")
    result: dict[str, Path] = {}
    for key, field in (
        ("plan", "exact_file_plan_filename"),
        ("baseline", "execution_baseline_filename"),
        ("evidence", "review_evidence_filename"),
        ("packet", "review_packet_filename"),
    ):
        path, issues = resolve_managed_path(
            root,
            f"{storage.get('root')}/{increment_id}/{storage.get(field)}",
            role=f"status-current {key}",
            require_file=True,
        )
        if path is None:
            raise ValueError("; ".join(issues))
        result[key] = path
    return result


def _closure_preconditions(
    *,
    successor_id: str | None,
    paths_allocated: bool,
    unresolved_requirements: int,
    unresolved_material_findings: int,
    unresolved_amendments: int,
    unowned_deferrals: int,
    verification_is_fresh: bool,
) -> dict[str, object]:
    """Return the complete fail-closed closure readiness projection."""
    return {
        "successor_id": successor_id,
        "paths_allocated": paths_allocated,
        "unresolved_requirements": unresolved_requirements,
        "unresolved_material_findings": unresolved_material_findings,
        "unresolved_amendments": unresolved_amendments,
        "unowned_deferrals": unowned_deferrals,
        "verification_is_fresh": verification_is_fresh,
    }


def _validate_preconditions(value: dict[str, object]) -> None:
    issues: list[str] = []
    if value.get("successor_id") is not None:
        issues.append("accepted increment is nonfinal because traceability allocates a successor")
    if value.get("paths_allocated", True) is not True:
        issues.append("manifest-owned closure paths lack exact-plan Create allocation")
    for field, label in (
        ("unresolved_requirements", "requirements"),
        ("unresolved_material_findings", "material findings"),
        ("unresolved_amendments", "amendments"),
        ("unowned_deferrals", "unowned deferrals"),
    ):
        count = value.get(field, 0)
        if not isinstance(count, int) or isinstance(count, bool) or count != 0:
            issues.append(f"closure has unresolved {label}")
    if value.get("verification_is_fresh", True) is not True:
        issues.append("program verification is stale")
    if issues:
        raise ValueError("; ".join(sorted(set(issues))))


def _review_context(
    root: Path,
    status: dict[str, object],
    paths: dict[str, Path],
) -> tuple[dict[str, object], str, tuple[str, ...], tuple[tuple[str, int, str], ...], str]:
    evidence_binding = status.get("review_evidence_binding")
    packet_binding = status.get("review_packet_binding")
    if not isinstance(evidence_binding, dict) or not isinstance(packet_binding, dict):
        raise ValueError("accepted status review bindings are incomplete")
    if evidence_binding.get("sha256") != sha256_file(paths["evidence"]):
        raise ValueError("accepted review evidence digest changed")
    if packet_binding.get("sha256") != sha256_file(paths["packet"]):
        raise ValueError("accepted review packet digest changed")
    evidence, evidence_issues = load_json_object(paths["evidence"])
    if evidence is None:
        raise ValueError("; ".join(evidence_issues))
    packet_text = paths["packet"].read_text(encoding="utf-8")
    review_issues = validate_review_bundle(evidence, packet_text)
    if review_issues:
        raise ValueError("; ".join(review_issues))
    verification = evidence.get("final_verification")
    reports = evidence.get("reports")
    findings = evidence.get("findings")
    if (
        not isinstance(verification, dict)
        or not isinstance(reports, list)
        or not isinstance(findings, list)
    ):
        raise ValueError("accepted review evidence is incomplete")
    commands_value = verification.get("commands")
    if not isinstance(commands_value, list) or not commands_value:
        raise ValueError("closure requires fresh program command evidence")
    commands: list[tuple[str, int, str]] = []
    for item in commands_value:
        if not isinstance(item, dict):
            raise ValueError("program command evidence must be an object")
        command = item.get("command")
        exit_code = item.get("exit_code")
        completed_at = item.get("completed_at")
        if (
            not isinstance(command, str)
            or not command
            or not isinstance(exit_code, int)
            or isinstance(exit_code, bool)
            or not isinstance(completed_at, str)
            or not completed_at
        ):
            raise ValueError("program command evidence is invalid")
        commands.append((command, exit_code, completed_at))
    reconciled_at = [
        item.get("reconciled_at")
        for item in reports
        if isinstance(item, dict) and isinstance(item.get("reconciled_at"), str)
    ]
    if len(reconciled_at) != len(reports) or not reconciled_at:
        raise ValueError("review reconciliation timestamps are incomplete")
    unresolved = sum(
        item.get("classification") == "material" and item.get("disposition") == "open"
        for item in findings
        if isinstance(item, dict)
    )
    finding_summaries = tuple(
        f"{item.get('finding_id')}: {item.get('disposition')}"
        for item in findings
        if isinstance(item, dict)
    ) or ("No material findings were reported.",)
    return evidence, packet_text, finding_summaries, tuple(commands), max(reconciled_at)


def _traceability_context(
    traceability: dict[str, object], increment_id: str
) -> tuple[
    tuple[str, ...],
    tuple[ClosureRequirementDisposition, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[tuple[str, str, str], ...],
    int,
    int,
]:
    requirements = traceability.get("atomic_requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("traceability atomic_requirements must be a non-empty list")
    identifiers: list[str] = []
    dispositions: list[ClosureRequirementDisposition] = []
    unresolved = 0
    for item in requirements:
        if not isinstance(item, dict):
            raise ValueError("traceability requirement must be an object")
        requirement_id = item.get("id")
        assigned = item.get("assigned_increments")
        if (
            not isinstance(requirement_id, str)
            or not requirement_id
            or not isinstance(assigned, list)
            or not all(isinstance(value, str) and value for value in assigned)
        ):
            raise ValueError("traceability requirement identity or allocation is invalid")
        if requirement_id in identifiers:
            raise ValueError("traceability requirement identities must be unique")
        identifiers.append(requirement_id)
        current_disposition = item.get("current_disposition")
        if increment_id not in assigned or current_disposition in {
            "blocked",
            "deferred",
            "unresolved",
        }:
            unresolved += 1
        dispositions.append(
            ClosureRequirementDisposition(
                requirement_id=requirement_id,
                disposition="implemented",
                evidence_paths=(),
                owner=increment_id,
                approval_reference="none",
                later_invalidation_checked=True,
            )
        )
    approved = traceability.get("approved_amendment_ids", [])
    resolved = traceability.get("resolved_amendment_ids", [])
    deferrals_value = traceability.get("deferrals", [])
    if not isinstance(approved, list) or not all(isinstance(item, str) and item for item in approved):
        raise ValueError("approved amendment identities must be strings")
    if not isinstance(resolved, list) or not all(isinstance(item, str) and item for item in resolved):
        raise ValueError("resolved amendment identities must be strings")
    if not isinstance(deferrals_value, list):
        raise ValueError("traceability deferrals must be a list")
    deferrals: list[tuple[str, str, str]] = []
    unowned = 0
    for item in deferrals_value:
        if not isinstance(item, dict):
            raise ValueError("traceability deferral must be an object")
        identity = item.get("id")
        owner = item.get("owner")
        disposition = item.get("disposition")
        if not all(isinstance(value, str) and value for value in (identity, owner, disposition)):
            unowned += 1
            continue
        deferrals.append((identity, owner, disposition))
    unresolved_amendments = len(set(approved).symmetric_difference(resolved))
    return (
        tuple(identifiers),
        tuple(dispositions),
        tuple(approved),
        tuple(resolved),
        tuple(deferrals),
        unresolved,
        unowned,
    )


def build_closure_preparation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ClosurePreparationCandidate:
    """Build and validate canonical closure artifacts before any write."""
    root = Path(program_root)
    normalized = _fresh_observation(root, observation)
    state_issues = validate_state_authority(root, normalized)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, status_path = _load_role(root, manifest, "status")
    if status.get("current_increment_state") != "accepted" or status.get(
        "program_state"
    ) not in {"active", "awaiting-closure-approval"}:
        raise ValueError("closure preparation requires an accepted active final increment")
    increment_id = str(status["current_increment_id"])
    paths = _increment_paths(root, manifest, increment_id)
    closure_paths = resolve_program_closure_paths(root)
    file_map = parse_exact_file_map(paths["plan"].read_text(encoding="utf-8"))
    workspace = Path(normalized.path).resolve()
    closure_relatives = tuple(
        path.resolve(strict=False).relative_to(workspace).as_posix()
        for path in closure_paths.values()
    )
    paths_allocated = all(path in file_map.create for path in closure_relatives)

    traceability, _traceability_path = _load_role(root, manifest, "traceability")
    successor_id = _traceability_successor(traceability, increment_id)
    (
        requirement_ids,
        bare_dispositions,
        approved_amendments,
        resolved_amendments,
        deferrals,
        unresolved_requirements,
        unowned_deferrals,
    ) = _traceability_context(traceability, increment_id)

    baseline_value, baseline_issues = load_json_object(paths["baseline"])
    if baseline_value is None:
        raise ValueError("; ".join(baseline_issues))
    baseline = execution_baseline_from_value(baseline_value)
    inspection = inspect_repository(Path(normalized.path), normalized.base_commit)
    assessment = validate_execution_workspace(
        root,
        baseline,
        replace(inspection, observation=normalized),
        increment_state="accepted",
    )
    if not assessment.valid:
        raise ValueError("; ".join(assessment.issues))
    diff_binding = status.get("diff_disposition_binding")
    if (
        not isinstance(diff_binding, dict)
        or diff_binding.get("decision") != "accept-stop"
        or diff_binding.get("accepted_product_delta_sha256")
        != assessment.product_delta_sha256
    ):
        raise ValueError("accepted product delta no longer matches the accepted status")

    evidence, _packet_text, finding_summaries, commands, latest_evidence = _review_context(
        root, status, paths
    )
    final_verification = evidence["final_verification"]
    unresolved_findings = final_verification.get("unresolved_material_findings")
    if not isinstance(unresolved_findings, int) or isinstance(unresolved_findings, bool):
        raise ValueError("review unresolved material finding count is invalid")
    verification_is_fresh = all(completed_at > latest_evidence for _, _, completed_at in commands)
    preconditions = _closure_preconditions(
        successor_id=successor_id,
        paths_allocated=paths_allocated,
        unresolved_requirements=unresolved_requirements,
        unresolved_material_findings=unresolved_findings,
        unresolved_amendments=len(
            set(approved_amendments).symmetric_difference(resolved_amendments)
        ),
        unowned_deferrals=unowned_deferrals,
        verification_is_fresh=verification_is_fresh,
    )
    _validate_preconditions(preconditions)

    evidence_paths = tuple(
        dict.fromkeys(
            (
                paths["packet"].relative_to(root).as_posix(),
                *(str(item["path"]) for item in assessment.product_delta),
            )
        )
    )
    dispositions = tuple(
        ClosureRequirementDisposition(
            requirement_id=item.requirement_id,
            disposition=item.disposition,
            evidence_paths=evidence_paths,
            owner=item.owner,
            approval_reference=item.approval_reference,
            later_invalidation_checked=item.later_invalidation_checked,
        )
        for item in bare_dispositions
    )
    decision_id = str(diff_binding["approval_event_id"])
    reconciliation = ClosureReconciliation(
        schema_version=RECONCILIATION_SCHEMA,
        program_id=str(status["program_id"]),
        program_revision=int(status["program_revision"]),
        final_increment_id=increment_id,
        expected_requirement_ids=requirement_ids,
        requirement_dispositions=dispositions,
        accepted_increment_ids=(increment_id,),
        accepted_artifact_bindings=((f"{increment_id}:review-packet", sha256_file(paths["packet"])),),
        approved_amendment_ids=approved_amendments,
        resolved_amendment_ids=resolved_amendments,
        decision_ids=(decision_id,),
        deferrals=deferrals,
        unresolved_material_findings=unresolved_findings,
        program_command_results=commands,
        latest_contributing_evidence_at=latest_evidence,
        later_invalidation_checks=(increment_id,),
        architecture_assessment="The accepted review found no unresolved architecture finding.",
        documentation_assessment="The manifest-owned closure packet records the final local state.",
        operations_assessment="No external, provider, publication, or deployment action was performed.",
        recovery_assessment="Exact durable prefixes are adopted; divergent bytes require recovery.",
    )
    reconciliation_issues = validate_closure_reconciliation(reconciliation)
    if reconciliation_issues:
        raise ValueError("; ".join(reconciliation_issues))
    reconciliation_bytes = _canonical_json_bytes(asdict(reconciliation))
    reconciliation_sha256 = _sha256_bytes(reconciliation_bytes)
    packet = ClosurePacket(
        schema_version=CLOSURE_PACKET_SCHEMA,
        program_id=str(status["program_id"]),
        program_revision=int(status["program_revision"]),
        final_increment_id=increment_id,
        final_increment_accepted=True,
        reconciliation_sha256=reconciliation_sha256,
        current_program_state="active",
        requirement_summary=tuple(
            f"{requirement_id} is implemented with accepted review and product evidence."
            for requirement_id in requirement_ids
        ),
        amendment_and_deferral_summary=(
            "No unresolved amendments or unowned deferrals remain.",
        ),
        accepted_packet_integrity=(
            f"The accepted review packet matches {sha256_file(paths['packet'])}.",
        ),
        program_verification=tuple(
            f"{command} completed with exit {exit_code} at {completed_at}."
            for command, exit_code, completed_at in commands
        ),
        architecture_documentation_operations_recovery=(
            reconciliation.architecture_assessment,
            reconciliation.documentation_assessment,
            reconciliation.operations_assessment,
            reconciliation.recovery_assessment,
        ),
        findings_and_dispositions=finding_summaries,
        residual_risks=(
            "Deterministic local evidence does not prove external or production behavior.",
        ),
        closure_approval_request=(
            "Approve closure of this exact reconciled program and no later action."
        ),
        next_action="Stop for explicit closure approval.",
    )
    packet_issues = validate_closure_packet(packet, reconciliation_sha256)
    if packet_issues:
        raise ValueError("; ".join(packet_issues))
    packet_bytes = render_closure_packet(packet).encode("utf-8")
    packet_sha256 = _sha256_bytes(packet_bytes)

    state = str(status["program_state"])
    if state == "active":
        prior_sha256 = sha256_file(status_path)
        prior_sequence = int(status["state_sequence"])
        preparation_binding = {
            "schema_version": CLOSURE_PREPARATION_SCHEMA,
            "prior_status_sha256": prior_sha256,
            "prior_status_sequence": prior_sequence,
            "accepted_product_delta_sha256": assessment.product_delta_sha256,
            "review_evidence_sha256": status["review_evidence_binding"]["sha256"],
            "review_packet_sha256": status["review_packet_binding"]["sha256"],
            "reconciliation_sha256": reconciliation_sha256,
            "closure_packet_sha256": packet_sha256,
        }
        awaiting_status = dict(status)
        awaiting_status.update(
            state_sequence=prior_sequence + 1,
            program_state="awaiting-closure-approval",
            previous_state={
                "schema_version": status["schema_version"],
                "state_sequence": prior_sequence,
                "status_sha256": prior_sha256,
            },
            transition_authority={
                "kind": "action-authorization",
                "event_id": _identifier("closure-preparation", preparation_binding),
                "authorization_id": status["execution_authorization"]["authorization_id"],
            },
            closure_preparation_binding=preparation_binding,
            closure_binding={
                "final_increment_id": increment_id,
                "reconciliation_path": closure_paths["reconciliation"].relative_to(root).as_posix(),
                "reconciliation_sha256": reconciliation_sha256,
                "closure_packet_path": closure_paths["packet"].relative_to(root).as_posix(),
                "closure_packet_sha256": packet_sha256,
                "readiness_validated": True,
                "unresolved_requirements": 0,
                "unresolved_amendments": 0,
                "unowned_deferrals": 0,
                "unresolved_material_findings": 0,
            },
        )
    else:
        preparation_binding = status.get("closure_preparation_binding")
        closure_binding = status.get("closure_binding")
        if (
            not isinstance(preparation_binding, dict)
            or preparation_binding.get("schema_version") != CLOSURE_PREPARATION_SCHEMA
            or preparation_binding.get("reconciliation_sha256") != reconciliation_sha256
            or preparation_binding.get("closure_packet_sha256") != packet_sha256
            or not isinstance(closure_binding, dict)
            or closure_binding.get("reconciliation_sha256") != reconciliation_sha256
            or closure_binding.get("closure_packet_sha256") != packet_sha256
        ):
            raise ValueError("closure-preparation-recovery-required: status binding diverges")
        awaiting_status = status
    return ClosurePreparationCandidate(
        reconciliation_bytes=reconciliation_bytes,
        packet_bytes=packet_bytes,
        reconciliation_sha256=reconciliation_sha256,
        packet_sha256=packet_sha256,
        reconciliation_path=closure_paths["reconciliation"],
        packet_path=closure_paths["packet"],
        awaiting_status_bytes=_canonical_json_bytes(awaiting_status),
        awaiting_status=awaiting_status,
    )


def _after_persist(_label: str) -> None:
    """Test seam after one durable closure transaction boundary."""


def prepare_program_closure(
    program_root: Path,
    observation: RepositoryObservation,
) -> ClosurePreparationReceipt:
    """Create/adopt reconciliation and packet, then persist gate status last."""
    root = Path(program_root)
    candidate = build_closure_preparation(root, observation)
    recovered = _create_or_adopt_bytes(
        candidate.reconciliation_path,
        candidate.reconciliation_bytes,
        "closure-preparation",
    )
    _after_persist("reconciliation")
    recovered = (
        _create_or_adopt_bytes(
            candidate.packet_path, candidate.packet_bytes, "closure-preparation"
        )
        or recovered
    )
    _after_persist("packet")
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    _status, status_path = _load_role(root, manifest, "status")
    binding = candidate.awaiting_status["closure_preparation_binding"]
    recovered = (
        _replace_or_adopt_status(
            status_path,
            candidate.awaiting_status,
            str(binding["prior_status_sha256"]),
            "closure-preparation",
        )
        or recovered
    )
    _after_persist("awaiting-closure-status")
    final_issues = validate_state_authority(root, _fresh_observation(root, observation))
    if final_issues:
        raise ValueError("; ".join(final_issues))
    return ClosurePreparationReceipt(
        reconciliation_sha256=candidate.reconciliation_sha256,
        closure_packet_sha256=candidate.packet_sha256,
        program_state="awaiting-closure-approval",
        status_sha256=sha256_file(status_path),
        recovered=recovered,
    )


def _command_base(status: dict[str, object], status_sha256: str) -> dict[str, object]:
    closure = status.get("closure_binding")
    preparation = status.get("closure_preparation_binding")
    if not isinstance(closure, dict) or not isinstance(preparation, dict):
        raise ValueError("closure command requires exact preparation bindings")
    return {
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "increment_id": status["current_increment_id"],
        "prior_status_sha256": status_sha256,
        "prior_status_sequence": status["state_sequence"],
        "reconciliation_sha256": closure["reconciliation_sha256"],
        "closure_packet_sha256": closure["closure_packet_sha256"],
        "accepted_product_delta_sha256": preparation[
            "accepted_product_delta_sha256"
        ],
        "decision": "approve-closure-stop",
    }


def build_closure_command_candidate(
    program_root: Path,
    observation: RepositoryObservation,
) -> ClosureCommandCandidate:
    """Build the exact closure prompt, approval record, and closed status."""
    root = Path(program_root)
    normalized = _fresh_observation(root, observation)
    state_issues = validate_state_authority(root, normalized)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status, status_path = _load_role(root, manifest, "status")
    state = status.get("program_state")
    if state not in {"awaiting-closure-approval", "closed"}:
        raise ValueError("closure approval requires awaiting-closure-approval status")
    closure = status.get("closure_binding")
    if not isinstance(closure, dict):
        raise ValueError("closure binding is missing")
    closure_paths = resolve_program_closure_paths(root)
    for key, digest_field in (
        ("reconciliation", "reconciliation_sha256"),
        ("packet", "closure_packet_sha256"),
    ):
        if closure.get(digest_field) != sha256_file(closure_paths[key]):
            raise ValueError("closure artifact changed after preparation")

    if state == "awaiting-closure-approval":
        prior_sha256 = sha256_file(status_path)
        base = _command_base(status, prior_sha256)
        base_seed_sha256 = _sha256_bytes(_canonical_json_bytes(base))
        checkpoint_id = _identifier(
            "closure-checkpoint", {"base_seed_sha256": base_seed_sha256}
        )
        approval_event_id = _identifier(
            "closure-approval",
            {
                "base_seed_sha256": base_seed_sha256,
                "checkpoint_id": checkpoint_id,
            },
        )
        command_binding = {
            "schema_version": CLOSURE_COMMAND_BINDING_SCHEMA,
            **base,
            "base_seed_sha256": base_seed_sha256,
            "checkpoint_id": checkpoint_id,
            "approval_event_id": approval_event_id,
        }
        closed_status = dict(status)
        closed_status.update(
            state_sequence=int(status["state_sequence"]) + 1,
            program_state="closed",
            previous_state={
                "schema_version": status["schema_version"],
                "state_sequence": status["state_sequence"],
                "status_sha256": prior_sha256,
            },
            transition_authority={
                "kind": "approval-event",
                "event_id": approval_event_id,
                "checkpoint_id": checkpoint_id,
            },
            closure_command_binding=command_binding,
        )
        closed_status_bytes = _canonical_json_bytes(closed_status)
    else:
        command_binding = status.get("closure_command_binding")
        if (
            not isinstance(command_binding, dict)
            or command_binding.get("schema_version") != CLOSURE_COMMAND_BINDING_SCHEMA
        ):
            raise ValueError("closure-approval-recovery-required: command binding diverges")
        base = {
            key: command_binding[key]
            for key in (
                "program_id",
                "program_revision",
                "increment_id",
                "prior_status_sha256",
                "prior_status_sequence",
                "reconciliation_sha256",
                "closure_packet_sha256",
                "accepted_product_delta_sha256",
                "decision",
            )
        }
        base_seed_sha256 = _sha256_bytes(_canonical_json_bytes(base))
        checkpoint_id = _identifier(
            "closure-checkpoint", {"base_seed_sha256": base_seed_sha256}
        )
        approval_event_id = _identifier(
            "closure-approval",
            {
                "base_seed_sha256": base_seed_sha256,
                "checkpoint_id": checkpoint_id,
            },
        )
        if (
            command_binding.get("base_seed_sha256") != base_seed_sha256
            or command_binding.get("checkpoint_id") != checkpoint_id
            or command_binding.get("approval_event_id") != approval_event_id
            or status.get("transition_authority")
            != {
                "kind": "approval-event",
                "event_id": approval_event_id,
                "checkpoint_id": checkpoint_id,
            }
        ):
            raise ValueError("closure-approval-recovery-required: command identity diverges")
        closed_status = status
        closed_status_bytes = _canonical_json_bytes(status)

    command = {
        "schema_version": CLOSURE_COMMAND_SCHEMA,
        **base,
        "base_seed_sha256": base_seed_sha256,
        "checkpoint_id": checkpoint_id,
        "approval_event_id": approval_event_id,
        "closed_status_sha256": _sha256_bytes(closed_status_bytes),
    }
    prompt = "Approve program closure and stop.\n\n" + render_exact_prompt(command)
    source = status["source_binding"]
    program = status["program_binding"]
    brief = status["brief_binding"]
    approval_record = {
        "schema_version": APPROVAL_SCHEMA,
        "event_id": approval_event_id,
        "type": "program-closure-approval",
        "decision": "approved",
        "scope": ["close the exact reconciled program and stop"],
        "checkpoint_id": checkpoint_id,
        "base_seed_sha256": base_seed_sha256,
        "submitted_prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "program_sha256": program["sha256"],
        "semantic_requirements_sha256": program[
            "semantic_requirements_sha256"
        ],
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
        "closure_reconciliation_sha256": closure["reconciliation_sha256"],
        "closure_packet_sha256": closure["closure_packet_sha256"],
        "accepted_product_delta_sha256": command_binding[
            "accepted_product_delta_sha256"
        ],
    }
    return ClosureCommandCandidate(
        base_seed_sha256=base_seed_sha256,
        checkpoint_id=checkpoint_id,
        approval_event_id=approval_event_id,
        prompt=prompt,
        approval_bytes=_canonical_json_line(approval_record),
        approval_record=approval_record,
        closed_status_bytes=closed_status_bytes,
        closed_status=closed_status,
    )


def render_program_closure_prompt(program_root: Path) -> str:
    """Render the exact closure-only approval prompt."""
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    workspace, _workspace_path = _load_role(root, manifest, "workspace")
    selected = workspace["implementation_workspace"]
    observation = inspect_repository(
        Path(selected["path"]), selected["base_commit"]
    ).observation
    return build_closure_command_candidate(root, observation).prompt


def _append_or_adopt_approval(path: Path, candidate: ClosureCommandCandidate) -> bool:
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
            raise ValueError("closure-approval-recovery-required: conflicting approval")
        return True
    if any(
        record.get("type") == "program-closure-approval"
        and record.get("program_id") == candidate.approval_record.get("program_id")
        and record.get("program_revision")
        == candidate.approval_record.get("program_revision")
        for record in records
    ):
        raise ValueError("closure-approval-recovery-required: conflicting approval")
    atomic_append_json_line(path, candidate.approval_record, sha256_file(path))
    return False


def persist_program_closure(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> ClosureReceipt:
    """Append/adopt closure approval, then persist closed status last."""
    root = Path(program_root)
    candidate = build_closure_command_candidate(root, observation)
    if submitted_prompt != candidate.prompt:
        raise ValueError("submitted program closure prompt does not match current bytes")
    parse_exact_prompt(
        candidate.prompt.removeprefix("Approve program closure and stop.\n\n"),
        CLOSURE_COMMAND_SCHEMA,
    )
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    roles = manifest["logical_roles"]
    approvals_path, approval_issues = resolve_managed_path(
        root, roles["approvals"], role="logical role approvals"
    )
    _status, status_path = _load_role(root, manifest, "status")
    if approvals_path is None:
        raise ValueError("; ".join(approval_issues))
    recovered = _append_or_adopt_approval(approvals_path, candidate)
    _after_persist("closure-approval")
    binding = candidate.closed_status["closure_command_binding"]
    recovered = (
        _replace_or_adopt_status(
            status_path,
            candidate.closed_status,
            str(binding["prior_status_sha256"]),
            "closure-approval",
        )
        or recovered
    )
    _after_persist("closed-status")
    final_issues = validate_state_authority(root, _fresh_observation(root, observation))
    if final_issues:
        raise ValueError("; ".join(final_issues))
    return ClosureReceipt(
        approval_event_id=candidate.approval_event_id,
        program_state="closed",
        status_sha256=sha256_file(status_path),
        recovered=recovered,
    )
