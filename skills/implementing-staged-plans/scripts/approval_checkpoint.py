#!/usr/bin/env python3
"""Build explicit compound authority checkpoints without parsing user prose."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from program_authority import (
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
)
from state_authority import (
    ACTION_NAMES,
    RepositoryObservation,
    STATUS_SCHEMA_V2,
    StateTransitionReceipt,
    TransitionRequest,
    apply_state_transition,
    atomic_append_json_line,
    validate_state_authority,
)


AUTHORITY_ACTIONS = tuple(sorted(ACTION_NAMES))

_COMMON_BINDING_FIELDS = (
    "program_id",
    "program_revision",
    "source_id",
    "source_sha256",
    "program_sha256",
    "semantic_requirements_sha256",
    "increment_id",
    "brief_sha256",
    "exact_file_plan_sha256",
    "approval_mode",
    "workspace",
)
_RISK_CLASSES = {
    "write-program-artifact": "routine-local",
    "modify-workspace": "routine-local",
    "run-local-verification": "routine-local",
    "create-workspace": "explicit-local",
    "create-local-commit": "explicit-local",
    "create-draft-pull-request": "bounded-external",
    "merge": "high-consequence",
    "publish": "high-consequence",
    "release": "high-consequence",
    "deploy": "high-consequence",
    "migrate": "high-consequence",
    "destructive-operation": "high-consequence",
    "modify-provider-state": "high-consequence",
    "modify-external-state": "high-consequence",
}
_RISK_ORDER = {
    "routine-local": 0,
    "explicit-local": 1,
    "bounded-external": 2,
    "high-consequence": 3,
}


@dataclass(frozen=True)
class AuthorityRequirement:
    requirement_id: str
    kind: str
    summary: str
    record: dict[str, object]
    prerequisites: tuple[str, ...] = ()


@dataclass(frozen=True)
class CheckpointItem:
    requirement_id: str
    kind: str
    summary: str
    state: str
    risk_class: str
    issues: tuple[str, ...]
    record: dict[str, object]


@dataclass(frozen=True)
class CompoundCheckpoint:
    binding_sha256: str | None
    items: tuple[CheckpointItem, ...]
    pending_requirement_ids: tuple[str, ...]
    blocked_requirement_ids: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedCheckpoint:
    approval_records: tuple[dict[str, object], ...]
    action_records: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class RecordPersistenceReceipt:
    record_identifier: str
    prior_sha256: str
    current_sha256: str
    adopted: bool


@dataclass(frozen=True)
class CheckpointPersistenceRequest:
    checkpoint_id: str
    approval_record: dict[str, object]
    action_records: tuple[dict[str, object], ...]
    expected_approvals_sha256: str
    expected_authorizations_sha256: str
    expected_previous_program_state: str
    expected_previous_increment_id: str
    expected_previous_increment_state: str
    transition: TransitionRequest


@dataclass(frozen=True)
class CheckpointPersistenceReceipt:
    checkpoint_id: str
    completed_steps: tuple[str, ...]
    approval_receipt: RecordPersistenceReceipt | None
    transition_receipt: StateTransitionReceipt | None
    transition_adopted: bool
    action_receipts: tuple[RecordPersistenceReceipt, ...]
    failed_step: str | None
    requires_retry: bool


class CheckpointPersistenceError(RuntimeError):
    def __init__(self, message: str, receipt: CheckpointPersistenceReceipt) -> None:
        super().__init__(message)
        self.receipt = receipt


def action_risk_class(action: str) -> str:
    try:
        return _RISK_CLASSES[action]
    except KeyError as error:
        raise ValueError(f"unsupported action: {action}") from error


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _record_identifier(kind: str, record: dict[str, object]) -> str | None:
    field = "event_id" if kind == "approval" else "authorization_id"
    value = record.get(field)
    return value if _nonempty(value) else None


def _binding(record: dict[str, object]) -> tuple[object, ...] | None:
    values: list[object] = []
    for field in _COMMON_BINDING_FIELDS:
        value = record.get(field)
        if field == "program_revision":
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                return None
        elif field == "workspace":
            if not isinstance(value, dict) or set(value) != {
                "path",
                "branch",
                "base_commit",
                "head_commit",
            }:
                return None
            if not all(_nonempty(item) for item in value.values()):
                return None
            value = tuple((key, value[key]) for key in sorted(value))
        elif not _nonempty(value):
            return None
        values.append(value)
    return tuple(values)


def _positive_record(requirement: AuthorityRequirement) -> dict[str, object]:
    decision = "approved" if requirement.kind == "approval" else "authorized"
    return {**requirement.record, "decision": decision}


def _record_shape_issues(requirement: AuthorityRequirement) -> list[str]:
    issues: list[str] = []
    record = requirement.record
    if requirement.kind not in {"approval", "action"}:
        return ["unsupported requirement kind"]
    expected_schema = (
        "implementation-approval/v1"
        if requirement.kind == "approval"
        else "implementation-action-authorization/v1"
    )
    if record.get("schema_version") != expected_schema:
        issues.append("unsupported authority record schema")
    if _record_identifier(requirement.kind, record) is None:
        issues.append("record identifier is required")
    if not _nonempty(requirement.requirement_id):
        issues.append("requirement identifier is required")
    if not _nonempty(requirement.summary):
        issues.append("requirement summary is required")
    if "decision" in record:
        issues.append("checkpoint candidate must not preselect a decision")
    scope = record.get("scope")
    if not isinstance(scope, list) or not scope or not all(_nonempty(item) for item in scope):
        issues.append("authority scope must be a non-empty string list")
    if _binding(record) is None:
        issues.append("authority binding is incomplete")
    if requirement.kind == "approval":
        if not _nonempty(record.get("type")):
            issues.append("approval type is required")
    else:
        actions = record.get("actions")
        if not isinstance(actions, list) or not actions or not all(
            _nonempty(action) for action in actions
        ):
            issues.append("action list must be a non-empty string list")
        else:
            for action in actions:
                try:
                    risk_class = action_risk_class(action)
                except ValueError:
                    issues.append(f"unsupported action: {action}")
                else:
                    if risk_class == "high-consequence":
                        issues.append(
                            f"high-consequence action cannot be authorized in a checkpoint: {action}"
                        )
    return sorted(set(issues))


def _risk_class(requirement: AuthorityRequirement) -> str:
    if requirement.kind == "approval":
        return "approval"
    actions = requirement.record.get("actions")
    if not isinstance(actions, list) or not actions:
        return "high-consequence"
    classes = [action_risk_class(action) for action in actions]
    return max(classes, key=_RISK_ORDER.__getitem__)


def _existing_state(
    requirement: AuthorityRequirement,
    records: tuple[dict[str, object], ...],
) -> tuple[str, tuple[str, ...]]:
    identifier_field = (
        "event_id" if requirement.kind == "approval" else "authorization_id"
    )
    identifier = _record_identifier(requirement.kind, requirement.record)
    semantic_candidate = {
        key: value
        for key, value in requirement.record.items()
        if key != identifier_field
    }
    equivalent_identifiers = {
        _record_identifier(requirement.kind, record)
        for record in records
        if _record_identifier(requirement.kind, record) != identifier
        and all(record.get(key) == value for key, value in semantic_candidate.items())
    }
    if equivalent_identifiers:
        return "blocked", ("equivalent authority record uses another identifier",)
    same_identifier = [
        record
        for record in records
        if _record_identifier(requirement.kind, record) == identifier
    ]
    if not same_identifier:
        return "pending", ()
    if len(same_identifier) == 1 and same_identifier[0] == _positive_record(requirement):
        return "satisfied", ()
    return "blocked", ("record identifier conflict",)


def build_checkpoint(
    requirements: tuple[AuthorityRequirement, ...],
    approvals: tuple[dict[str, object], ...],
    authorizations: tuple[dict[str, object], ...],
) -> CompoundCheckpoint:
    identifiers = [requirement.requirement_id for requirement in requirements]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("checkpoint requirement identifiers must be unique")

    checkpoint_binding: tuple[object, ...] | None = None
    binding_sha256: str | None = None
    items: list[CheckpointItem] = []
    states: dict[str, str] = {}
    known_identifiers = set(identifiers)
    for requirement in requirements:
        issues = _record_shape_issues(requirement)
        current_binding = _binding(requirement.record)
        if checkpoint_binding is None and current_binding is not None and not issues:
            checkpoint_binding = current_binding
            plan_digest = requirement.record.get("exact_file_plan_sha256")
            binding_sha256 = plan_digest if isinstance(plan_digest, str) else None
        elif (
            checkpoint_binding is not None
            and current_binding is not None
            and current_binding != checkpoint_binding
        ):
            issues.append("checkpoint binding mismatch")

        unknown_prerequisites = sorted(set(requirement.prerequisites) - known_identifiers)
        if unknown_prerequisites:
            issues.append("checkpoint prerequisite is unknown")
        if any(states.get(prerequisite) == "blocked" for prerequisite in requirement.prerequisites):
            issues.append("checkpoint prerequisite is blocked")

        records = approvals if requirement.kind == "approval" else authorizations
        state = "blocked" if issues else "pending"
        if not issues:
            state, existing_issues = _existing_state(requirement, records)
            issues.extend(existing_issues)
        states[requirement.requirement_id] = state
        items.append(
            CheckpointItem(
                requirement_id=requirement.requirement_id,
                kind=requirement.kind,
                summary=requirement.summary,
                state=state,
                risk_class=_risk_class(requirement),
                issues=tuple(sorted(set(issues))),
                record=dict(requirement.record),
            )
        )

    return CompoundCheckpoint(
        binding_sha256=binding_sha256,
        items=tuple(items),
        pending_requirement_ids=tuple(
            item.requirement_id for item in items if item.state == "pending"
        ),
        blocked_requirement_ids=tuple(
            item.requirement_id for item in items if item.state == "blocked"
        ),
    )


def resolve_checkpoint(
    checkpoint: CompoundCheckpoint, decisions: dict[str, str]
) -> ResolvedCheckpoint:
    if checkpoint.blocked_requirement_ids:
        raise ValueError("blocked checkpoint cannot be resolved")
    approval_records: list[dict[str, object]] = []
    action_records: list[dict[str, object]] = []
    for item in checkpoint.items:
        if item.state != "pending":
            continue
        reconstructed = AuthorityRequirement(
            requirement_id=item.requirement_id,
            kind=item.kind,
            summary=item.summary,
            record=dict(item.record),
        )
        reconstruction_issues = _record_shape_issues(reconstructed)
        recomputed_risk = _risk_class(reconstructed)
        if reconstruction_issues:
            raise ValueError("; ".join(reconstruction_issues))
        if item.risk_class != recomputed_risk:
            raise ValueError(
                f"checkpoint risk class mismatch for {item.requirement_id}"
            )
        if recomputed_risk == "high-consequence":
            raise ValueError(
                f"high-consequence checkpoint item cannot be resolved: {item.requirement_id}"
            )
        choice = decisions.get(item.requirement_id)
        if choice is None:
            raise ValueError(f"decision is required for {item.requirement_id}")
        if item.kind == "approval":
            if choice not in {"approve", "reject"}:
                raise ValueError(f"invalid approval decision for {item.requirement_id}")
            approval_records.append(
                {**item.record, "decision": "approved" if choice == "approve" else "rejected"}
            )
        else:
            if choice not in {"authorize", "deny"}:
                raise ValueError(f"invalid action decision for {item.requirement_id}")
            action_records.append(
                {**item.record, "decision": "authorized" if choice == "authorize" else "denied"}
            )
    unknown = sorted(set(decisions) - set(checkpoint.pending_requirement_ids))
    if unknown:
        raise ValueError("decision supplied for a non-pending requirement")
    return ResolvedCheckpoint(tuple(approval_records), tuple(action_records))


def append_exact_record_or_adopt(
    path: Path, record: dict[str, object], expected_sha256: str
) -> RecordPersistenceReceipt:
    target = Path(path)
    records, issues = load_json_lines(target)
    if records is None:
        raise ValueError("; ".join(issues))
    identifier = record.get("event_id", record.get("authorization_id"))
    if not _nonempty(identifier):
        raise ValueError("record identifier is required")
    matching = [
        existing
        for existing in records
        if existing.get("event_id", existing.get("authorization_id")) == identifier
    ]
    current_sha256 = sha256_file(target)
    if matching:
        if len(matching) == 1 and matching[0] == record:
            return RecordPersistenceReceipt(
                record_identifier=identifier,
                prior_sha256=current_sha256,
                current_sha256=current_sha256,
                adopted=True,
            )
        raise ValueError(f"record identifier conflict: {identifier}")
    receipt = atomic_append_json_line(target, record, expected_sha256)
    return RecordPersistenceReceipt(
        record_identifier=identifier,
        prior_sha256=receipt.prior_sha256,
        current_sha256=receipt.current_sha256,
        adopted=False,
    )


def _managed_authority_paths(program_root: Path) -> tuple[Path, Path, Path]:
    root = Path(program_root)
    manifest, issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(issues))
    roles = manifest.get("logical_roles")
    if not isinstance(roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    resolved: list[Path] = []
    for role in ("approvals", "status", "action_authorizations"):
        path, path_issues = resolve_managed_path(
            root,
            roles.get(role),
            role=f"logical role {role}",
        )
        if path is None:
            raise ValueError("; ".join(path_issues))
        resolved.append(path)
    return resolved[0], resolved[1], resolved[2]


def _preflight_live_plan_approval(
    program_root: Path,
    status_path: Path,
    status: dict[str, object],
    request: CheckpointPersistenceRequest,
    observation: RepositoryObservation,
) -> None:
    state_issues = validate_state_authority(Path(program_root), observation)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    manifest, manifest_issues = load_json_object(Path(program_root) / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    if _adopted_transition(status_path, request) is not None:
        return
    transition = request.transition
    current_program_state = status.get("program_state")
    current_increment_id = status.get("current_increment_id")
    current_increment_state = status.get("current_increment_state")
    if (
        current_program_state != request.expected_previous_program_state
        or current_increment_id != request.expected_previous_increment_id
        or current_increment_state != request.expected_previous_increment_state
    ):
        raise ValueError("checkpoint expected previous state does not match live status")
    if (
        sha256_file(status_path) != transition.expected_status_sha256
        or status.get("state_sequence") != transition.expected_state_sequence
    ):
        raise ValueError("checkpoint transition does not match the live status version")
    if (
        current_increment_state != "awaiting-plan-approval"
        or transition.target_program_state != current_program_state
        or transition.target_increment_id != current_increment_id
        or transition.target_increment_state != "authorized"
        or request.approval_record.get("type") != "exact-file-plan-approval"
    ):
        raise ValueError("checkpoint persistence requires the live plan-approval edge")
    source = status.get("source_binding")
    program = status.get("program_binding")
    brief = status.get("brief_binding")
    pending_plan = status.get("pending_exact_file_plan_sha256")
    if not all(isinstance(value, dict) for value in (source, program, brief)):
        raise ValueError("live checkpoint binding is incomplete")
    expected_binding = {
        "program_id": manifest.get("program_id"),
        "program_revision": manifest.get("program_revision"),
        "source_id": source.get("source_id"),
        "source_sha256": source.get("sha256"),
        "program_sha256": program.get("sha256"),
        "semantic_requirements_sha256": program.get(
            "semantic_requirements_sha256"
        ),
        "increment_id": current_increment_id,
        "brief_sha256": brief.get("sha256"),
        "exact_file_plan_sha256": pending_plan,
        "approval_mode": status.get("approval_mode"),
        "workspace": {
            "path": observation.path,
            "branch": observation.branch,
            "base_commit": observation.base_commit,
            "head_commit": observation.head_commit,
        },
    }
    if _binding(request.approval_record) != _binding(expected_binding):
        raise ValueError("checkpoint approval does not match the live plan binding")


def _validate_persistence_request(request: CheckpointPersistenceRequest) -> None:
    if not _nonempty(request.checkpoint_id):
        raise ValueError("checkpoint identifier is required")
    if not all(
        _nonempty(value)
        for value in (
            request.expected_previous_program_state,
            request.expected_previous_increment_id,
            request.expected_previous_increment_state,
        )
    ):
        raise ValueError("checkpoint expected previous state is incomplete")
    transition = request.transition
    if transition.checkpoint_id != request.checkpoint_id:
        raise ValueError("transition checkpoint identifier mismatch")
    if request.approval_record.get("decision") != "approved":
        raise ValueError("checkpoint persistence requires one approved record")
    if request.approval_record.get("event_id") != transition.transition_event_id:
        raise ValueError("approval event does not match the transition")
    approval_binding = _binding(request.approval_record)
    if approval_binding is None:
        raise ValueError("checkpoint approval binding is incomplete")
    action_identifiers: set[str] = set()
    for record in request.action_records:
        if record.get("decision") != "authorized":
            raise ValueError("checkpoint action record must be authorized")
        identifier = record.get("authorization_id")
        if not _nonempty(identifier) or identifier in action_identifiers:
            raise ValueError("checkpoint action identifiers must be unique")
        action_identifiers.add(identifier)
        if _binding(record) != approval_binding:
            raise ValueError("checkpoint action binding mismatch")
        actions = record.get("actions")
        if not isinstance(actions, list) or any(
            action_risk_class(action) == "high-consequence"
            for action in actions
        ):
            raise ValueError(
                "high-consequence action cannot be persisted through a checkpoint"
            )
    if transition.execution_authorization_id not in action_identifiers:
        raise ValueError("expected execution authorization is not in the checkpoint")
    if transition.authority_kind != "approval-event":
        raise ValueError("checkpoint transition requires approval-event authority")
    if transition.action_authorization_id is not None:
        raise ValueError("checkpoint governance transition cannot claim action authority")
    action_scope = transition.evidence.get("action_scope")
    if not _nonempty(action_scope):
        raise ValueError("checkpoint transition action scope is required")
    execution_records = [
        record
        for record in request.action_records
        if record.get("authorization_id") == transition.execution_authorization_id
    ]
    if len(execution_records) != 1:
        raise ValueError("checkpoint requires one exact execution authorization")
    execution_record = execution_records[0]
    if (
        not isinstance(execution_record.get("actions"), list)
        or "modify-workspace" not in execution_record["actions"]
        or not isinstance(execution_record.get("scope"), list)
        or action_scope not in execution_record["scope"]
    ):
        raise ValueError(
            "checkpoint execution authorization must grant the bound workspace action and scope"
        )


def _preflight_existing_record(
    kind: str,
    record: dict[str, object],
    existing: tuple[dict[str, object], ...],
) -> None:
    candidate = {key: value for key, value in record.items() if key != "decision"}
    identifier = _record_identifier(kind, candidate)
    requirement = AuthorityRequirement(
        requirement_id=f"persist-{identifier}",
        kind=kind,
        summary="Persist an explicitly resolved checkpoint record.",
        record=candidate,
    )
    shape_issues = _record_shape_issues(requirement)
    if shape_issues:
        raise ValueError("; ".join(shape_issues))
    state, state_issues = _existing_state(requirement, existing)
    if state == "blocked":
        raise ValueError("; ".join(state_issues))


def _adopted_transition(
    status_path: Path,
    request: CheckpointPersistenceRequest,
) -> StateTransitionReceipt | None:
    status, issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(issues))
    transition_authority = status.get("transition_authority")
    expected_transition_authority = {
        "kind": "approval-event",
        "event_id": request.transition.transition_event_id,
        "checkpoint_id": request.checkpoint_id,
    }
    expected_execution_authorization = {
        "authorization_id": request.transition.execution_authorization_id,
        "scope": request.transition.evidence.get("action_scope"),
    }
    previous = status.get("previous_state")
    matches = (
        status.get("schema_version") == "implementation-program-status/v2"
        and status.get("state_sequence")
        == request.transition.expected_state_sequence + 1
        and status.get("program_state") == request.transition.target_program_state
        and status.get("current_increment_id")
        == request.transition.target_increment_id
        and status.get("current_increment_state")
        == request.transition.target_increment_state
        and transition_authority == expected_transition_authority
        and status.get("execution_authorization")
        == expected_execution_authorization
        and status.get("transition_evidence") == request.transition.evidence
        and status.get("approved_exact_file_plan_sha256")
        == request.approval_record.get("exact_file_plan_sha256")
        and status.get("pending_exact_file_plan_sha256") is None
        and isinstance(previous, dict)
        and previous.get("schema_version") == STATUS_SCHEMA_V2
        and previous.get("status_sha256")
        == request.transition.expected_status_sha256
        and previous.get("state_sequence")
        == request.transition.expected_state_sequence
        and previous.get("program_state")
        == request.expected_previous_program_state
        and previous.get("current_increment_id")
        == request.expected_previous_increment_id
        and previous.get("current_increment_state")
        == request.expected_previous_increment_state
        and previous.get("transition_event_id")
        == request.transition.transition_event_id
    )
    if not matches:
        return None
    return StateTransitionReceipt(
        prior_sha256=request.transition.expected_status_sha256,
        current_sha256=sha256_file(status_path),
        state_sequence=int(status["state_sequence"]),
        program_state=str(status["program_state"]),
        increment_id=str(status["current_increment_id"]),
        increment_state=str(status["current_increment_state"]),
    )


def persist_checkpoint(
    program_root: Path,
    request: CheckpointPersistenceRequest,
    observation: RepositoryObservation,
) -> CheckpointPersistenceReceipt:
    """Persist one v2 checkpoint in a retry-safe, fail-closed order."""
    _validate_persistence_request(request)
    approvals_path, status_path, authorizations_path = _managed_authority_paths(
        Path(program_root)
    )
    completed: list[str] = []
    approval_receipt: RecordPersistenceReceipt | None = None
    transition_receipt: StateTransitionReceipt | None = None
    transition_adopted = False
    action_receipts: list[RecordPersistenceReceipt] = []
    failed_step: str | None = None
    try:
        failed_step = "preflight"
        status, status_issues = load_json_object(status_path)
        if status is None:
            raise ValueError("; ".join(status_issues))
        if status.get("schema_version") != STATUS_SCHEMA_V2:
            raise ValueError("compound checkpoint persistence requires a v2 status")
        _preflight_live_plan_approval(
            Path(program_root),
            status_path,
            status,
            request,
            observation,
        )
        approvals, approval_issues = load_json_lines(approvals_path)
        if approvals is None:
            raise ValueError("; ".join(approval_issues))
        authorizations, authorization_issues = load_json_lines(authorizations_path)
        if authorizations is None:
            raise ValueError("; ".join(authorization_issues))
        _preflight_existing_record(
            "approval",
            request.approval_record,
            tuple(approvals),
        )
        for record in request.action_records:
            _preflight_existing_record(
                "action",
                record,
                tuple(authorizations),
            )

        approval_identifier = str(request.approval_record["event_id"])
        failed_step = f"approval:{approval_identifier}"
        approval_receipt = append_exact_record_or_adopt(
            approvals_path,
            request.approval_record,
            request.expected_approvals_sha256,
        )
        completed.append(failed_step)

        failed_step = "transition"
        transition_receipt = _adopted_transition(status_path, request)
        if transition_receipt is None:
            transition_receipt = apply_state_transition(
                Path(program_root), request.transition, observation
            )
        else:
            transition_adopted = True
        completed.append(failed_step)

        expected_authorizations_sha256 = request.expected_authorizations_sha256
        for record in request.action_records:
            action_identifier = str(record["authorization_id"])
            failed_step = f"action:{action_identifier}"
            action_receipt = append_exact_record_or_adopt(
                authorizations_path,
                record,
                expected_authorizations_sha256,
            )
            action_receipts.append(action_receipt)
            expected_authorizations_sha256 = action_receipt.current_sha256
            completed.append(failed_step)
    except (OSError, TypeError, ValueError) as error:
        receipt = CheckpointPersistenceReceipt(
            checkpoint_id=request.checkpoint_id,
            completed_steps=tuple(completed),
            approval_receipt=approval_receipt,
            transition_receipt=transition_receipt,
            transition_adopted=transition_adopted,
            action_receipts=tuple(action_receipts),
            failed_step=failed_step,
            requires_retry=True,
        )
        raise CheckpointPersistenceError(str(error), receipt) from error
    return CheckpointPersistenceReceipt(
        checkpoint_id=request.checkpoint_id,
        completed_steps=tuple(completed),
        approval_receipt=approval_receipt,
        transition_receipt=transition_receipt,
        transition_adopted=transition_adopted,
        action_receipts=tuple(action_receipts),
        failed_step=None,
        requires_retry=False,
    )
