#!/usr/bin/env python3
"""Generate and validate continuity, closure, and later-action evidence."""

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from state_authority import (
    APPROVAL_MODE_POLICIES,
    approval_mode_policy,
    validate_state_authority,
)


CONTINUITY_SCHEMA = "implementation-continuity-evidence/v1"
CONTINUATION_AUTHORIZATION_SCHEMA = "implementation-continuation-authorization/v1"
RECONCILIATION_SCHEMA = "implementation-closure-reconciliation/v1"
CLOSURE_PACKET_SCHEMA = "implementation-closure-packet/v1"
EXPLICIT_SKILL_INVOCATION = "$implementing-staged-plans"

APPROVAL_MODES = frozenset(APPROVAL_MODE_POLICIES)
CONVERSATION_SUITABILITY_PREDICATES = (
    "program-part-boundary",
    "risk-or-architecture-domain",
    "workspace-or-base",
    "superseded-discussion",
    "evidence-or-expertise",
    "lossless-summary",
)
OPTIONAL_CONTEXT_FIELDS = frozenset(
    {
        "integration_checkpoint",
        "notable_risk",
        "non_goal",
        "design_decision",
        "sequencing_reason",
        "repository_drift",
    }
)
REQUIREMENT_DISPOSITIONS = frozenset(
    {"implemented", "amended", "deferred", "rejected", "not-applicable"}
)
LATER_ACTIONS = (
    "create-draft-pull-request",
    "merge",
    "publish",
    "release",
    "deploy",
    "migrate",
    "destructive-operation",
    "modify-provider-state",
    "modify-external-state",
)
RECOVERY_REQUIRED_ACTIONS = frozenset(
    {
        "deploy",
        "migrate",
        "destructive-operation",
        "modify-provider-state",
        "modify-external-state",
    }
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")
_SECRET_LIKE = re.compile(
    r"(?i)(?:token|password|secret|api[_ -]?key)\s*[:=]\s*\S+"
)
_AUTHORIZING_TEXT = re.compile(
    r"(?i)(?:you are authorized|permission (?:is )?granted|approval (?:is )?granted|authorized to (?:create|merge|release|deploy|migrate|publish|modify|delete))"
)
_COPIED_POLICY = re.compile(
    r"(?i)(?:TDD procedures?|review-role definitions?|hard-stop catalogues?|full repository-inspection instructions?|evidence-refresh rules?|pull-request, merge, release, or deployment prohibitions?)"
)


@dataclass(frozen=True)
class LeanBrief:
    schema_version: str
    program_id: str
    program_revision: int
    increment_id: str
    title: str
    outcome: str
    requirement_ids: tuple[str, ...]
    acceptance: str
    approval_mode: str
    workspace_path: str
    workspace_branch: str
    workspace_base_commit: str
    workspace_head_commit: str
    status_path: str
    status_sha256: str
    handoff_path: str
    handoff_sha256: str
    unresolved_user_decision: str
    optional_context: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class HandoffRecord:
    schema_version: str
    program_id: str
    program_revision: int
    current_increment_id: str
    current_increment_state: str
    approval_mode: str
    workspace_path: str
    workspace_branch: str
    base_commit: str
    head_commit: str
    accepted_increments: tuple[str, ...]
    verification_status: str
    accepted_review_packet_path: str
    accepted_review_packet_sha256: str
    accepted_handoff_addendum_path: str
    accepted_handoff_addendum_sha256: str
    accepted_status_sequence: int
    accepted_status_sha256: str
    amendments: tuple[str, ...]
    unresolved_risks: tuple[str, ...]
    next_legal_action: str
    first_read_files: tuple[str, ...]


@dataclass(frozen=True)
class ConversationAssessment:
    schema_version: str
    approval_mode: str
    same_conversation: bool
    predicate_evidence: tuple[tuple[str, bool, str], ...]
    submitted_brief_sha256: str
    expected_brief_sha256: str
    explicit_renewed_authority: bool


@dataclass(frozen=True)
class ResumeContext:
    schema_version: str
    program_id: str
    program_revision: int
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    workspace_path: str
    workspace_branch: str
    workspace_base_commit: str
    workspace_head_commit: str
    status_sha256: str
    status_sequence: int
    brief_sha256: str
    handoff_sha256: str
    accepted_review_packet_sha256: str
    accepted_handoff_addendum_sha256: str
    conflicted_paths: tuple[str, ...]
    active_git_operation: str | None
    matching_authorization_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClosureRequirementDisposition:
    requirement_id: str
    disposition: str
    evidence_paths: tuple[str, ...]
    owner: str
    approval_reference: str
    later_invalidation_checked: bool


@dataclass(frozen=True)
class ClosureReconciliation:
    schema_version: str
    program_id: str
    program_revision: int
    final_increment_id: str
    expected_requirement_ids: tuple[str, ...]
    requirement_dispositions: tuple[ClosureRequirementDisposition, ...]
    accepted_increment_ids: tuple[str, ...]
    accepted_artifact_bindings: tuple[tuple[str, str], ...]
    approved_amendment_ids: tuple[str, ...]
    resolved_amendment_ids: tuple[str, ...]
    decision_ids: tuple[str, ...]
    deferrals: tuple[tuple[str, str, str], ...]
    unresolved_material_findings: int
    program_command_results: tuple[tuple[str, int, str], ...]
    latest_contributing_evidence_at: str
    later_invalidation_checks: tuple[str, ...]
    architecture_assessment: str
    documentation_assessment: str
    operations_assessment: str
    recovery_assessment: str


@dataclass(frozen=True)
class ClosurePacket:
    schema_version: str
    program_id: str
    program_revision: int
    final_increment_id: str
    final_increment_accepted: bool
    reconciliation_sha256: str
    current_program_state: str
    requirement_summary: tuple[str, ...]
    amendment_and_deferral_summary: tuple[str, ...]
    accepted_packet_integrity: tuple[str, ...]
    program_verification: tuple[str, ...]
    architecture_documentation_operations_recovery: tuple[str, ...]
    findings_and_dispositions: tuple[str, ...]
    residual_risks: tuple[str, ...]
    closure_approval_request: str
    next_action: str


@dataclass(frozen=True)
class ContinuityWriteReceipt:
    completed_writes: tuple[tuple[str, str], ...]
    failed_path: str | None
    requires_fresh_resume: bool


@dataclass(frozen=True)
class RemoteHeadObservation:
    provider: str
    repository: str
    base_ref: str
    head_ref: str
    head_commit: str
    remote_ref_exists: bool
    requires_push: bool
    draft: bool


@dataclass(frozen=True)
class DraftPullRequestConsumptionReceipt:
    request_id: str
    authorization_id: str
    provider: str
    repository: str
    base_ref: str
    head_ref: str
    head_commit: str
    consumed_at: str


@dataclass(frozen=True)
class DraftPullRequestPreflight:
    request_id: str
    authorization_id: str
    checked_at: str
    valid_until: str
    remote_head: RemoteHeadObservation
    prior_consumptions: tuple[DraftPullRequestConsumptionReceipt, ...]


@dataclass(frozen=True)
class DraftPullRequestAuthority:
    request_id: str
    provider: str
    repository: str
    base_ref: str
    head_ref: str
    head_commit: str
    draft: bool
    push_requested: bool


@dataclass(frozen=True)
class LaterActionDecision:
    authorized: bool
    authorization_id: str | None
    issues: tuple[str, ...]
    action: str | None = None
    scope: str | None = None
    draft_pull_request: DraftPullRequestAuthority | None = None
    authorization_expires_at: str | None = None


@dataclass(frozen=True)
class LaterActionRoutingDecision:
    may_execute_same_turn: bool
    must_stop: bool
    authorization_id: str | None
    issues: tuple[str, ...]
    consumption_receipt: DraftPullRequestConsumptionReceipt | None = None


class _UsageError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value)) and value != "0" * 64


def _is_commit(value: object) -> bool:
    return isinstance(value, str) and bool(_COMMIT.fullmatch(value)) and value != "0" * len(value)


def _tuple_strings(value: object, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, tuple)
        and (allow_empty or bool(value))
        and all(_nonempty(item) for item in value)
    )


def _timestamp(value: object) -> datetime | None:
    if not _nonempty(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _title(value: str) -> str:
    return value.replace("_", " ").capitalize()


def _construct(record_type: type, value: object, *, nested: dict[str, Any] | None = None):
    if not isinstance(value, Mapping):
        raise ValueError(f"{record_type.__name__} must be an object")
    allowed = {field.name for field in fields(record_type)}
    if set(value) != allowed:
        missing = sorted(allowed - set(value))
        unknown = sorted(set(value) - allowed)
        raise ValueError(
            f"{record_type.__name__} fields mismatch; missing={missing!r}; unknown={unknown!r}"
        )
    converted = dict(value)
    for field in fields(record_type):
        if field.name in (nested or {}):
            converted[field.name] = nested[field.name](converted[field.name])
        elif isinstance(converted[field.name], list):
            entries = converted[field.name]
            converted[field.name] = tuple(
                tuple(item) if isinstance(item, list) else item for item in entries
            )
    try:
        return record_type(**converted)
    except TypeError as error:
        raise ValueError(f"invalid {record_type.__name__}: {error}") from error


def lean_brief_from_mapping(value: object) -> LeanBrief:
    return _construct(LeanBrief, value)


def handoff_from_mapping(value: object) -> HandoffRecord:
    return _construct(HandoffRecord, value)


def conversation_assessment_from_mapping(value: object) -> ConversationAssessment:
    return _construct(ConversationAssessment, value)


def resume_context_from_mapping(value: object) -> ResumeContext:
    return _construct(ResumeContext, value)


def closure_reconciliation_from_mapping(value: object) -> ClosureReconciliation:
    def dispositions(entries: object) -> tuple[ClosureRequirementDisposition, ...]:
        if not isinstance(entries, (list, tuple)):
            raise ValueError("requirement_dispositions must be a list")
        return tuple(
            _construct(ClosureRequirementDisposition, entry) for entry in entries
        )

    return _construct(
        ClosureReconciliation,
        value,
        nested={"requirement_dispositions": dispositions},
    )


def closure_packet_from_mapping(value: object) -> ClosurePacket:
    return _construct(ClosurePacket, value)


def validate_increment_brief(candidate: LeanBrief) -> list[str]:
    issues: list[str] = []
    if candidate.schema_version != CONTINUITY_SCHEMA:
        issues.append("unsupported brief schema")
    for label, value in (
        ("program_id", candidate.program_id),
        ("increment_id", candidate.increment_id),
        ("title", candidate.title),
        ("outcome", candidate.outcome),
        ("acceptance", candidate.acceptance),
        ("workspace_path", candidate.workspace_path),
        ("workspace_branch", candidate.workspace_branch),
        ("status_path", candidate.status_path),
        ("handoff_path", candidate.handoff_path),
        ("unresolved_user_decision", candidate.unresolved_user_decision),
    ):
        if not _nonempty(value):
            issues.append(f"brief {label} is required")
    if not _is_int(candidate.program_revision) or candidate.program_revision < 1:
        issues.append("brief program_revision must be a positive integer")
    if candidate.approval_mode not in APPROVAL_MODES:
        issues.append("brief approval_mode is unsupported")
    if not _tuple_strings(candidate.requirement_ids):
        issues.append("brief requirement_ids must be a non-empty string tuple")
    for label, value in (
        ("workspace_base_commit", candidate.workspace_base_commit),
        ("workspace_head_commit", candidate.workspace_head_commit),
    ):
        if not _is_commit(value):
            issues.append(f"brief {label} is invalid or stale")
    for label, value in (
        ("status_sha256", candidate.status_sha256),
        ("handoff_sha256", candidate.handoff_sha256),
    ):
        if not _is_sha256(value):
            issues.append(f"brief {label} is invalid or stale")
    if not isinstance(candidate.optional_context, tuple):
        issues.append("brief optional_context must be a tuple")
    else:
        keys: list[str] = []
        for item in candidate.optional_context:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not all(_nonempty(part) for part in item)
            ):
                issues.append("brief optional context entries must be key/value pairs")
                continue
            key, _ = item
            keys.append(key)
            if key not in OPTIONAL_CONTEXT_FIELDS:
                issues.append(f"brief optional context field {key!r} is not approved")
        if len(keys) != len(set(keys)):
            issues.append("brief optional context fields must be unique")
    all_text = " ".join(
        str(value)
        for value in (
            candidate.outcome,
            candidate.acceptance,
            candidate.unresolved_user_decision,
            candidate.optional_context,
        )
    )
    if _COPIED_POLICY.search(all_text):
        issues.append("brief copies canonical workflow policy")
    if _SECRET_LIKE.search(all_text):
        issues.append("brief contains secret-like material")
    return sorted(set(issues))


def _render_legacy_increment_brief(candidate: LeanBrief) -> str:
    """Render accepted v1 brief bytes without the copy-ready invocation wrapper."""
    issues = validate_increment_brief(candidate)
    if issues:
        raise ValueError("; ".join(issues))
    requirements = ", ".join(f"`{value}`" for value in candidate.requirement_ids)
    lines = [
        f"Resume `{candidate.program_id}` revision `{candidate.program_revision}` and execute `{candidate.increment_id} — {candidate.title}` under `{candidate.approval_mode}`.",
        "",
        f"**Outcome:** {candidate.outcome}",
        f"**Advances:** {requirements}",
        f"**Acceptance:** {candidate.acceptance}",
        (
            f"**Navigation:** Workspace `{candidate.workspace_path}` on `{candidate.workspace_branch}` "
            f"at base `{candidate.workspace_base_commit}` and head `{candidate.workspace_head_commit}`; "
            f"status `{candidate.status_path}` (`{candidate.status_sha256}`); "
            f"handoff `{candidate.handoff_path}` (`{candidate.handoff_sha256}`)."
        ),
        f"**Blocked decision:** {candidate.unresolved_user_decision}",
    ]
    if candidate.optional_context:
        context = "; ".join(
            f"{_title(key)}: {value}" for key, value in candidate.optional_context
        )
        lines.append(f"**Context:** {context}")
    return "\n".join(lines) + "\n"


def render_increment_brief(candidate: LeanBrief) -> str:
    """Render a copy-ready next-increment or new-conversation prompt."""
    return (
        f"{EXPLICIT_SKILL_INVOCATION}\n\n"
        f"{_render_legacy_increment_brief(candidate)}"
    )


def _matches_supported_increment_brief(
    candidate: LeanBrief,
    brief_markdown: str,
) -> bool:
    return brief_markdown in {
        _render_legacy_increment_brief(candidate),
        render_increment_brief(candidate),
    }


def validate_handoff(candidate: HandoffRecord) -> list[str]:
    issues: list[str] = []
    if candidate.schema_version != CONTINUITY_SCHEMA:
        issues.append("unsupported handoff schema")
    for label, value in (
        ("program_id", candidate.program_id),
        ("current_increment_id", candidate.current_increment_id),
        ("current_increment_state", candidate.current_increment_state),
        ("workspace_path", candidate.workspace_path),
        ("workspace_branch", candidate.workspace_branch),
        ("verification_status", candidate.verification_status),
        ("accepted_review_packet_path", candidate.accepted_review_packet_path),
        ("accepted_handoff_addendum_path", candidate.accepted_handoff_addendum_path),
        ("next_legal_action", candidate.next_legal_action),
    ):
        if not _nonempty(value):
            issues.append(f"handoff {label} is required")
    if not _is_int(candidate.program_revision) or candidate.program_revision < 1:
        issues.append("handoff program_revision must be a positive integer")
    if candidate.approval_mode not in APPROVAL_MODES:
        issues.append("handoff approval_mode is unsupported")
    if candidate.current_increment_state not in {"accepted", "awaiting-diff-approval"}:
        issues.append("handoff current increment state is unsupported")
    if not _is_commit(candidate.base_commit) or not _is_commit(candidate.head_commit):
        issues.append("handoff base/head binding is invalid or stale")
    for label, value in (
        ("accepted_review_packet_sha256", candidate.accepted_review_packet_sha256),
        ("accepted_handoff_addendum_sha256", candidate.accepted_handoff_addendum_sha256),
        ("accepted_status_sha256", candidate.accepted_status_sha256),
    ):
        if not _is_sha256(value):
            issues.append(f"handoff {label} is invalid or stale")
    if not _is_int(candidate.accepted_status_sequence) or candidate.accepted_status_sequence < 0:
        issues.append("handoff accepted_status_sequence must be a non-negative integer")
    for label, value in (
        ("accepted_increments", candidate.accepted_increments),
        ("amendments", candidate.amendments),
        ("unresolved_risks", candidate.unresolved_risks),
        ("first_read_files", candidate.first_read_files),
    ):
        if not _tuple_strings(value):
            issues.append(f"handoff {label} must be a non-empty string tuple")
    all_text = " ".join(str(value) for value in asdict(candidate).values())
    if _SECRET_LIKE.search(all_text):
        issues.append("handoff contains secret-like material")
    if _AUTHORIZING_TEXT.search(candidate.next_legal_action):
        issues.append("handoff must navigate but cannot authorize an action")
    return sorted(set(issues))


def render_handoff(candidate: HandoffRecord) -> str:
    issues = validate_handoff(candidate)
    if issues:
        raise ValueError("; ".join(issues))
    joined = lambda values: ", ".join(
        f"`{value}`" if "/" in value or value in candidate.accepted_increments else value
        for value in values
    )
    return "\n".join(
        (
            f"# {_title(candidate.program_id.replace('-', ' '))} handoff",
            "",
            f"- Program revision: `{candidate.program_id}` revision `{candidate.program_revision}`",
            f"- Current increment: `{candidate.current_increment_id}`",
            f"- Current increment state: `{candidate.current_increment_state}`",
            f"- Approval mode: `{candidate.approval_mode}`",
            f"- Workspace: `{candidate.workspace_path}` on `{candidate.workspace_branch}`",
            f"- Base/head: `{candidate.base_commit}` / `{candidate.head_commit}`",
            f"- Accepted increments: {joined(candidate.accepted_increments)}",
            f"- Verification status: {candidate.verification_status}",
            f"- Accepted review packet: `{candidate.accepted_review_packet_path}` (`{candidate.accepted_review_packet_sha256}`)",
            f"- Accepted handoff addendum: `{candidate.accepted_handoff_addendum_path}` (`{candidate.accepted_handoff_addendum_sha256}`)",
            f"- Accepted status: sequence `{candidate.accepted_status_sequence}` (`{candidate.accepted_status_sha256}`)",
            f"- Amendments: {joined(candidate.amendments)}",
            f"- Unresolved risks: {joined(candidate.unresolved_risks)}",
            f"- Next legal action: {candidate.next_legal_action}",
            f"- Files to inspect first: {', '.join(f'`{value}`' for value in candidate.first_read_files)}",
            "",
        )
    )


def evaluate_continuation(candidate: ConversationAssessment) -> tuple[bool, tuple[str, ...]]:
    issues: list[str] = []
    if candidate.schema_version != CONTINUITY_SCHEMA:
        issues.append("unsupported conversation assessment schema")
    try:
        policy = approval_mode_policy(candidate.approval_mode)
    except ValueError:
        policy = None
        issues.append("unsupported approval mode")
    if not isinstance(candidate.same_conversation, bool):
        issues.append("same_conversation must be boolean")
    if not isinstance(candidate.explicit_renewed_authority, bool):
        issues.append("explicit_renewed_authority must be boolean")
    names: list[str] = []
    if not isinstance(candidate.predicate_evidence, tuple):
        issues.append("predicate evidence must be a tuple")
    else:
        for item in candidate.predicate_evidence:
            if (
                not isinstance(item, tuple)
                or len(item) != 3
                or not _nonempty(item[0])
                or not isinstance(item[1], bool)
                or not _nonempty(item[2])
            ):
                issues.append("predicate evidence entry is invalid")
                continue
            names.append(item[0])
            if not item[1]:
                issues.append(f"handoff required: {item[0]} is not suitable")
        if tuple(names) != CONVERSATION_SUITABILITY_PREDICATES:
            issues.append("each conversation suitability predicate is required exactly once in order")
    if policy is not None and not policy.automatic_continuation:
        issues.append("one-increment approval mode requires a stop")
    if not _is_sha256(candidate.submitted_brief_sha256) or not _is_sha256(candidate.expected_brief_sha256):
        issues.append("conversation brief binding is invalid")
    if not candidate.same_conversation:
        if candidate.submitted_brief_sha256 != candidate.expected_brief_sha256:
            issues.append("new conversation submitted brief does not match")
        if not candidate.explicit_renewed_authority:
            issues.append("new conversation requires explicit renewed authority")
    return (not issues, tuple(sorted(set(issues))))


def validate_resume_context(
    observed: ResumeContext,
    expected: ResumeContext,
    *,
    program_root: Path | None = None,
    observation: object | None = None,
) -> list[str]:
    issues = validate_resume_record(observed)
    compared = tuple(
        field.name
        for field in fields(ResumeContext)
        if field.name
        not in {"conflicted_paths", "active_git_operation", "matching_authorization_ids"}
    )
    for name in compared:
        if getattr(observed, name) != getattr(expected, name):
            issues.append(f"resume {name} mismatch")
    if (program_root is None) != (observation is None):
        issues.append("resume state composition requires both program root and observation")
    elif program_root is not None and observation is not None:
        issues.extend(validate_state_authority(Path(program_root), observation))
    return sorted(set(issues))


def validate_resume_record(observed: ResumeContext) -> list[str]:
    """Validate submitted resume evidence without claiming repository comparison."""
    issues: list[str] = []
    if observed.schema_version != CONTINUITY_SCHEMA:
        issues.append("unsupported resume schema")
    if not _is_int(observed.program_revision) or observed.program_revision < 1:
        issues.append("resume program_revision must be a positive integer")
    if not _is_int(observed.status_sequence) or observed.status_sequence < 0:
        issues.append("resume status_sequence must be a non-negative integer")
    sha_fields = (
        "source_sha256",
        "program_sha256",
        "semantic_requirements_sha256",
        "status_sha256",
        "brief_sha256",
        "handoff_sha256",
        "accepted_review_packet_sha256",
        "accepted_handoff_addendum_sha256",
    )
    for name in sha_fields:
        if not _is_sha256(getattr(observed, name)):
            issues.append(f"resume {name} is invalid")
    for name in ("workspace_base_commit", "workspace_head_commit"):
        if not _is_commit(getattr(observed, name)):
            issues.append(f"resume {name} is invalid")
    if not isinstance(observed.conflicted_paths, tuple):
        issues.append("resume conflicted_paths must be a tuple")
    elif observed.conflicted_paths:
        issues.append("resume repository has conflicted paths")
    if observed.active_git_operation is not None:
        issues.append("resume repository has an active git operation")
    if len(observed.matching_authorization_ids) != 1:
        issues.append("resume requires exactly one matching renewed authorization")
    elif not _nonempty(observed.matching_authorization_ids[0]):
        issues.append("resume authorization id is invalid")
    return sorted(set(issues))


_CONTINUATION_BINDING_FIELDS = tuple(
    field.name
    for field in fields(ResumeContext)
    if field.name
    not in {
        "schema_version",
        "conflicted_paths",
        "active_git_operation",
        "matching_authorization_ids",
    }
)


def _continuation_binding(context: ResumeContext) -> dict[str, object]:
    return {
        "resume_schema_version": context.schema_version,
        **{
            field_name: getattr(context, field_name)
            for field_name in _CONTINUATION_BINDING_FIELDS
        },
    }


def build_continuation_authorization(
    context: ResumeContext,
    *,
    authorization_id: str,
    user_request_id: str,
    requested_action: str,
    requested_scope: str,
    issued_at: str,
    expires_at: str,
) -> dict[str, object]:
    """Materialize one explicit request without granting any broader action."""
    issues = validate_resume_record(context)
    if issues:
        raise ValueError("; ".join(issues))
    for label, value in (
        ("authorization id", authorization_id),
        ("user request id", user_request_id),
        ("requested action", requested_action),
        ("requested scope", requested_scope),
    ):
        if not _nonempty(value):
            raise ValueError(f"continuation {label} is required")
    if context.matching_authorization_ids != (authorization_id,):
        raise ValueError("resume context authorization id does not match the request")
    issued_time = _timestamp(issued_at)
    expiry_time = _timestamp(expires_at)
    if issued_time is None or expiry_time is None:
        raise ValueError("continuation timestamps must be timezone-aware ISO timestamps")
    if issued_time >= expiry_time:
        raise ValueError("continuation authorization requires a valid issuance interval")
    return {
        "schema_version": CONTINUATION_AUTHORIZATION_SCHEMA,
        "authorization_id": authorization_id,
        "decision": "authorized",
        "revoked": False,
        "user_request_id": user_request_id,
        "requested_action": requested_action,
        "requested_scope": requested_scope,
        "issued_at": issued_at,
        "expires_at": expires_at,
        **_continuation_binding(context),
    }


def validate_continuation_authority(
    observed: ResumeContext,
    expected: ResumeContext,
    records: Sequence[Mapping[str, object]],
    *,
    user_request_id: str,
    requested_action: str,
    requested_scope: str,
    program_root: Path | None = None,
    observation: object | None = None,
) -> list[str]:
    """Require one live request-bound receipt in addition to full resume validation."""
    issues = validate_resume_context(
        observed,
        expected,
        program_root=program_root,
        observation=observation,
    )
    if not all(
        _nonempty(value)
        for value in (user_request_id, requested_action, requested_scope)
    ):
        issues.append("continuation request identity, action, and scope are required")
    expected_binding = _continuation_binding(expected)

    def binding_matches(record: Mapping[str, object]) -> bool:
        return all(
            record.get(field_name) == value
            for field_name, value in expected_binding.items()
        )

    bound_records = [
        record
        for record in records
        if record.get("schema_version") == CONTINUATION_AUTHORIZATION_SCHEMA
        and record.get("user_request_id") == user_request_id
        and record.get("requested_action") == requested_action
        and record.get("requested_scope") == requested_scope
        and binding_matches(record)
    ]
    current: list[Mapping[str, object]] = []
    temporal_invalid = False
    current_time = datetime.now(timezone.utc)
    for record in bound_records:
        issued_at = record.get("issued_at")
        expires_at = record.get("expires_at")
        parsed_issuance = _timestamp(issued_at)
        parsed_expiry = _timestamp(expires_at)
        is_current_interval = (
            parsed_issuance is not None
            and parsed_expiry is not None
            and parsed_issuance <= current_time < parsed_expiry
        )
        if (
            record.get("decision") == "authorized"
            and record.get("revoked") is not True
            and is_current_interval
        ):
            current.append(record)
        elif record.get("decision") == "authorized" and record.get("revoked") is not True:
            temporal_invalid = True
    if any(
        record.get("decision") != "authorized" or record.get("revoked") is True
        for record in bound_records
    ):
        issues.append("conflicting continuation authorization records")
    if temporal_invalid:
        issues.append("continuation authorization is not currently valid")
    if len(current) != 1:
        issues.append("exactly one current continuation authorization")
    else:
        authorization_id = current[0].get("authorization_id")
        if not _nonempty(authorization_id):
            issues.append("continuation authorization id is invalid")
        elif observed.matching_authorization_ids != (authorization_id,):
            issues.append("resume authorization id does not match the current request")
    return sorted(set(issues))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def apply_increment_rollover(
    root: Path,
    *,
    handoff_relative_path: str,
    handoff_record: HandoffRecord,
    handoff_markdown: str,
    brief_relative_path: str,
    brief_record: LeanBrief,
    brief_markdown: str,
    manifest_relative_path: str,
    expected_manifest_sha256: str,
    manifest_value: Mapping[str, object],
    status_relative_path: str,
    expected_status_sha256: str,
    status_value: Mapping[str, object],
    current_increment_state: str,
    current_increment_id: str,
    expected_current_increment_id: str,
    next_increment_id: str,
    next_increment_dependencies: tuple[str, ...],
    matching_authorization_ids: tuple[str, ...],
    fail_after_writes: int | None = None,
) -> ContinuityWriteReceipt:
    raise ValueError(
        "legacy-rollover-upgrade-required: caller-authored rollover persistence is disabled"
    )


def validate_closure_reconciliation(candidate: ClosureReconciliation) -> list[str]:
    issues: list[str] = []
    if candidate.schema_version != RECONCILIATION_SCHEMA:
        issues.append("unsupported closure reconciliation schema")
    for label, value in (
        ("program_id", candidate.program_id),
        ("final_increment_id", candidate.final_increment_id),
        ("architecture_assessment", candidate.architecture_assessment),
        ("documentation_assessment", candidate.documentation_assessment),
        ("operations_assessment", candidate.operations_assessment),
        ("recovery_assessment", candidate.recovery_assessment),
    ):
        if not _nonempty(value):
            issues.append(f"reconciliation {label} is required")
    if not _is_int(candidate.program_revision) or candidate.program_revision < 1:
        issues.append("reconciliation program_revision must be a positive integer")
    if not _tuple_strings(candidate.expected_requirement_ids):
        issues.append("expected_requirement_ids must be a non-empty string tuple")
    expected = candidate.expected_requirement_ids
    actual = tuple(item.requirement_id for item in candidate.requirement_dispositions)
    if len(actual) != len(set(actual)) or set(actual) != set(expected) or len(actual) != len(expected):
        issues.append("every expected requirement must have exactly one disposition")
    for item in candidate.requirement_dispositions:
        if item.disposition not in REQUIREMENT_DISPOSITIONS:
            issues.append(f"requirement {item.requirement_id} has an unsupported disposition")
        if not _tuple_strings(item.evidence_paths):
            issues.append(f"requirement {item.requirement_id} requires evidence")
        if not isinstance(item.later_invalidation_checked, bool) or not item.later_invalidation_checked:
            issues.append(f"requirement {item.requirement_id} lacks a later-invalidation check")
        if item.disposition == "deferred" and (not _nonempty(item.owner) or item.owner == "none"):
            issues.append(f"deferred requirement {item.requirement_id} requires an owner")
        if item.disposition in {"amended", "rejected", "not-applicable"} and (
            not _nonempty(item.approval_reference) or item.approval_reference == "none"
        ):
            issues.append(f"requirement {item.requirement_id} requires an approval reference")
    if not _tuple_strings(candidate.accepted_increment_ids):
        issues.append("accepted_increment_ids must be a non-empty string tuple")
    if set(candidate.later_invalidation_checks) != set(candidate.accepted_increment_ids):
        issues.append("later-invalidation checks must cover every accepted increment")
    if not isinstance(candidate.accepted_artifact_bindings, tuple) or not candidate.accepted_artifact_bindings:
        issues.append("accepted artifact bindings are required")
    else:
        for item in candidate.accepted_artifact_bindings:
            if not isinstance(item, tuple) or len(item) != 2 or not _nonempty(item[0]) or not _is_sha256(item[1]):
                issues.append("accepted artifact binding is invalid")
        labels = [item[0] for item in candidate.accepted_artifact_bindings if isinstance(item, tuple) and len(item) == 2]
        review_packet_labels = {
            f"{increment_id}:review-packet"
            for increment_id in candidate.accepted_increment_ids
        }
        packet_and_addendum_labels = {
            f"{increment_id}:{role}"
            for increment_id in candidate.accepted_increment_ids
            for role in ("review-packet", "handoff-addendum")
        }
        label_set = frozenset(labels)
        if (
            len(labels) != len(label_set)
            or label_set
            not in {frozenset(review_packet_labels), frozenset(packet_and_addendum_labels)}
        ):
            issues.append(
                "review-packet bindings, with optional complete addendum coverage, "
                "must cover every accepted increment exactly"
            )
    if set(candidate.approved_amendment_ids) != set(candidate.resolved_amendment_ids):
        issues.append("every approved amendment must be resolved exactly")
    for item in candidate.deferrals:
        if not isinstance(item, tuple) or len(item) != 3 or not all(_nonempty(value) for value in item):
            issues.append("every deferral requires identity, owner, and disposition")
    deferred = {
        item.requirement_id: item.owner
        for item in candidate.requirement_dispositions
        if item.disposition == "deferred"
    }
    deferral_owners = {
        item[0]: item[1]
        for item in candidate.deferrals
        if isinstance(item, tuple) and len(item) == 3
    }
    if deferral_owners != deferred:
        issues.append("owned deferrals must exactly match deferred requirements")
    if not _is_int(candidate.unresolved_material_findings) or candidate.unresolved_material_findings != 0:
        issues.append("unresolved material findings must be zero")
    evidence_time = _timestamp(candidate.latest_contributing_evidence_at)
    if evidence_time is None:
        issues.append("latest contributing evidence timestamp is invalid")
    if not isinstance(candidate.program_command_results, tuple) or not candidate.program_command_results:
        issues.append("fresh program command results are required")
    else:
        for item in candidate.program_command_results:
            if not isinstance(item, tuple) or len(item) != 3 or not _nonempty(item[0]):
                issues.append("program command result is invalid")
                continue
            _, exit_code, completed_at = item
            if not _is_int(exit_code):
                issues.append("program command exit code must be an integer")
            elif exit_code != 0:
                issues.append("program command did not pass")
            completed = _timestamp(completed_at)
            if completed is None:
                issues.append("program command completion timestamp is invalid")
            elif evidence_time is not None and completed <= evidence_time:
                issues.append("program command evidence is stale")
    return sorted(set(issues))


def validate_closure_packet(candidate: ClosurePacket, expected_reconciliation_sha256: str) -> list[str]:
    issues: list[str] = []
    if candidate.schema_version != CLOSURE_PACKET_SCHEMA:
        issues.append("unsupported closure packet schema")
    if not _nonempty(candidate.program_id) or not _nonempty(candidate.final_increment_id):
        issues.append("closure packet program and final increment identities are required")
    if not _is_int(candidate.program_revision) or candidate.program_revision < 1:
        issues.append("closure packet program_revision must be a positive integer")
    if candidate.final_increment_accepted is not True:
        issues.append("closure packet requires final increment acceptance")
    if not _is_sha256(candidate.reconciliation_sha256) or candidate.reconciliation_sha256 != expected_reconciliation_sha256:
        issues.append("closure packet reconciliation digest mismatch")
    if candidate.current_program_state != "active":
        issues.append("closure packet must be produced while the program remains active")
    for label, value in (
        ("requirement_summary", candidate.requirement_summary),
        ("amendment_and_deferral_summary", candidate.amendment_and_deferral_summary),
        ("accepted_packet_integrity", candidate.accepted_packet_integrity),
        ("program_verification", candidate.program_verification),
        (
            "architecture_documentation_operations_recovery",
            candidate.architecture_documentation_operations_recovery,
        ),
        ("findings_and_dispositions", candidate.findings_and_dispositions),
        ("residual_risks", candidate.residual_risks),
    ):
        if not _tuple_strings(value):
            issues.append(f"closure packet {label} is required")
    if not _nonempty(candidate.closure_approval_request) or "closure" not in candidate.closure_approval_request.lower() or "approve" not in candidate.closure_approval_request.lower():
        issues.append("closure packet must request explicit closure approval")
    if _AUTHORIZING_TEXT.search(candidate.closure_approval_request) or "pull request" in candidate.closure_approval_request.lower():
        issues.append("closure approval request cannot authorize a later action")
    if not _nonempty(candidate.next_action) or "stop" not in candidate.next_action.lower() or "closure approval" not in candidate.next_action.lower():
        issues.append("closure packet next action must stop for closure approval")
    return sorted(set(issues))


def _markdown_list(values: tuple[str, ...]) -> str:
    return "\n".join(f"- {value}" for value in values)


def render_closure_packet(candidate: ClosurePacket) -> str:
    issues = validate_closure_packet(candidate, candidate.reconciliation_sha256)
    if issues:
        raise ValueError("; ".join(issues))
    accepted = "accepted" if candidate.final_increment_accepted else "not accepted"
    sections = (
        ("Requirement summary", candidate.requirement_summary),
        ("Amendments and deferrals", candidate.amendment_and_deferral_summary),
        ("Accepted packet integrity", candidate.accepted_packet_integrity),
        ("Program verification", candidate.program_verification),
        (
            "Architecture, documentation, operations, and recovery",
            candidate.architecture_documentation_operations_recovery,
        ),
        ("Findings and dispositions", candidate.findings_and_dispositions),
        ("Residual risks", candidate.residual_risks),
    )
    lines = [
        f"# {_title(candidate.program_id.replace('-', ' '))} closure packet",
        "",
        f"- Program revision: `{candidate.program_id}` revision `{candidate.program_revision}`",
        f"- Final increment: `{candidate.final_increment_id}` ({accepted})",
        f"- Reconciliation: `{candidate.reconciliation_sha256}`",
        f"- Current program state: `{candidate.current_program_state}`",
    ]
    for heading, values in sections:
        lines.extend(("", f"## {heading}", "", _markdown_list(values)))
    lines.extend(
        (
            "",
            "## Closure approval request",
            "",
            candidate.closure_approval_request,
            "",
            "## Next action",
            "",
            candidate.next_action,
            "",
        )
    )
    return "\n".join(lines)


def decide_later_action(
    *,
    program_state: str,
    action: str,
    scope: str,
    reconciliation_sha256: str,
    closure_packet_sha256: str,
    closure_approvals: Sequence[Mapping[str, object]],
    action_authorizations: Sequence[Mapping[str, object]],
    recovery_evidence: str,
    authority_context: Mapping[str, object],
    draft_pull_request: DraftPullRequestAuthority | None = None,
) -> LaterActionDecision:
    issues: list[str] = []
    if program_state != "closed":
        issues.append("program is not closed")
    if action not in LATER_ACTIONS:
        issues.append("unsupported later action")
    if not _nonempty(scope):
        issues.append("later action scope is required")
    if not _is_sha256(reconciliation_sha256) or not _is_sha256(closure_packet_sha256):
        issues.append("closure evidence digest is invalid")
    context_fields = {
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
    }
    if set(authority_context) != context_fields:
        issues.append("later action authority context fields are incomplete")
    if draft_pull_request is not None:
        if action != "create-draft-pull-request":
            issues.append("draft pull request binding requires the draft action")
        for label, value in (
            ("request id", draft_pull_request.request_id),
            ("provider", draft_pull_request.provider),
            ("repository", draft_pull_request.repository),
            ("base ref", draft_pull_request.base_ref),
            ("head ref", draft_pull_request.head_ref),
        ):
            if not _nonempty(value):
                issues.append(f"draft pull request {label} is required")
        if not _is_commit(draft_pull_request.head_commit):
            issues.append("draft pull request head commit is invalid")
        if draft_pull_request.draft is not True:
            issues.append("same-turn pull request authority must require a draft")
        if draft_pull_request.push_requested is not False:
            issues.append("same-turn pull request authority cannot request a push")
        workspace = authority_context.get("workspace")
        workspace_head = (
            workspace.get("head_commit") if isinstance(workspace, Mapping) else None
        )
        if draft_pull_request.head_commit != workspace_head:
            issues.append(
                "draft pull request authority head does not match the closed workspace"
            )

    def context_matches(record: Mapping[str, object]) -> bool:
        return set(authority_context) == context_fields and all(
            record.get(field) == authority_context.get(field)
            for field in context_fields
        )

    bound_approvals = [
        record
        for record in closure_approvals
        if record.get("schema_version") == "implementation-approval/v1"
        and record.get("type") == "program-closure-approval"
        and record.get("closure_reconciliation_sha256") == reconciliation_sha256
        and record.get("closure_packet_sha256") == closure_packet_sha256
        and context_matches(record)
    ]
    matching_approvals = [
        record for record in bound_approvals if record.get("decision") == "approved"
    ]
    if len(matching_approvals) != 1:
        issues.append("exactly one closure approval must match the evidence digests")
    if any(record.get("decision") != "approved" for record in bound_approvals):
        issues.append("conflicting exact closure approval records")
    bound_grants = [
        record
        for record in action_authorizations
        if record.get("schema_version") == "implementation-action-authorization/v1"
        and isinstance(record.get("actions"), list)
        and action in record["actions"]
        and isinstance(record.get("scope"), list)
        and scope in record["scope"]
        and record.get("closure_reconciliation_sha256") == reconciliation_sha256
        and record.get("closure_packet_sha256") == closure_packet_sha256
        and context_matches(record)
        and (
            draft_pull_request is None
            or (
                record.get("user_request_id") == draft_pull_request.request_id
                and record.get("remote_provider") == draft_pull_request.provider
                and record.get("remote_repository")
                == draft_pull_request.repository
                and record.get("base_ref") == draft_pull_request.base_ref
                and record.get("head_ref") == draft_pull_request.head_ref
                and record.get("head_commit") == draft_pull_request.head_commit
                and record.get("draft") is draft_pull_request.draft
                and record.get("push_requested")
                is draft_pull_request.push_requested
            )
        )
    ]
    matching_grants = [
        record
        for record in bound_grants
        if record.get("decision") == "authorized" and record.get("revoked") is not True
    ]
    if any(
        record.get("decision") != "authorized" or record.get("revoked") is True
        for record in bound_grants
    ):
        issues.append("conflicting exact later-action authorization records")
    current_grants = []
    current_time = datetime.now(timezone.utc)
    for record in matching_grants:
        expires = record.get("expires_at")
        parsed = _timestamp(expires) if expires is not None else None
        if draft_pull_request is not None and expires is None:
            continue
        if expires is None or (parsed is not None and parsed > current_time):
            current_grants.append(record)
    if draft_pull_request is not None and any(
        record.get("expires_at") is None
        or _timestamp(record.get("expires_at")) is None
        for record in matching_grants
    ):
        issues.append("same-turn draft grant requires bounded expiry")
    if len(current_grants) != 1:
        issues.append("exactly one current action authorization must match action, scope, and closure evidence")
    if action in RECOVERY_REQUIRED_ACTIONS and (
        not _nonempty(recovery_evidence) or recovery_evidence == "none required"
    ):
        issues.append("applicable recovery evidence is required")
    authorization_id = (
        current_grants[0].get("authorization_id") if len(current_grants) == 1 else None
    )
    if authorization_id is not None and not _nonempty(authorization_id):
        issues.append("later action authorization id is invalid")
        authorization_id = None
    authorization_expires_at = (
        current_grants[0].get("expires_at")
        if len(current_grants) == 1
        and _nonempty(current_grants[0].get("expires_at"))
        else None
    )
    return LaterActionDecision(
        not issues,
        authorization_id,
        tuple(sorted(set(issues))),
        action,
        scope,
        draft_pull_request,
        authorization_expires_at,
    )


def route_later_action(
    decision: LaterActionDecision,
    *,
    action: str,
    scope: str,
    current_request_id: str,
    current_request_action: str,
    current_request_scope: str,
    authority_context: Mapping[str, object],
    preflight: DraftPullRequestPreflight | None,
    routed_at: str,
) -> LaterActionRoutingDecision:
    """Route only a no-push draft PR; this function performs no external action."""
    issues = list(decision.issues)
    if not decision.authorized or not _nonempty(decision.authorization_id):
        issues.append("later action is not authorized")
    if action != "create-draft-pull-request":
        issues.append("mandatory stop")
        return LaterActionRoutingDecision(
            False,
            True,
            decision.authorization_id,
            tuple(sorted(set(issues))),
            None,
        )
    if not _nonempty(scope):
        issues.append("draft pull request scope is required")
    if decision.action != action or decision.scope != scope:
        issues.append("routed action and scope do not match the authorization decision")
    draft_authority = decision.draft_pull_request
    routed_time = _timestamp(routed_at)
    grant_expiry = _timestamp(decision.authorization_expires_at)
    if draft_authority is None:
        issues.append("draft pull request decision lacks exact request and remote authority")
    elif current_request_id != draft_authority.request_id:
        issues.append("current request identity does not match draft authority")
    if grant_expiry is None or routed_time is None or routed_time >= grant_expiry:
        issues.append("draft pull request grant is not current")
    if current_request_action != decision.action or current_request_scope != decision.scope:
        issues.append("current request does not match the authorized action and scope")
    remote_head: RemoteHeadObservation | None = None
    if preflight is None:
        issues.append("request-bound draft pull request preflight is required")
    else:
        if preflight.request_id != current_request_id:
            issues.append("draft pull request preflight request mismatch")
        if preflight.authorization_id != decision.authorization_id:
            issues.append("draft pull request preflight authorization mismatch")
        checked_at = _timestamp(preflight.checked_at)
        valid_until = _timestamp(preflight.valid_until)
        if checked_at is None or valid_until is None or routed_time is None:
            issues.append("draft pull request preflight timestamps are invalid")
        elif not (checked_at <= routed_time < valid_until):
            issues.append("draft pull request preflight is not current")
        if not isinstance(preflight.prior_consumptions, tuple) or any(
            not isinstance(receipt, DraftPullRequestConsumptionReceipt)
            for receipt in preflight.prior_consumptions
        ):
            issues.append("draft pull request consumption evidence is invalid")
        elif any(
            receipt.request_id == current_request_id
            or receipt.authorization_id == decision.authorization_id
            for receipt in preflight.prior_consumptions
        ):
            issues.append("draft pull request request was already consumed")
        if isinstance(preflight.remote_head, RemoteHeadObservation):
            remote_head = preflight.remote_head
        else:
            issues.append("fresh remote head observation is required")
    workspace = authority_context.get("workspace")
    current_workspace_head = (
        workspace.get("head_commit") if isinstance(workspace, Mapping) else None
    )
    if (
        draft_authority is not None
        and current_workspace_head != draft_authority.head_commit
    ):
        issues.append("current workspace head no longer matches draft authority")
    if remote_head is None:
        issues.append("fresh remote head observation is required")
    elif draft_authority is not None:
        if (
            remote_head.provider != draft_authority.provider
            or remote_head.repository != draft_authority.repository
            or remote_head.base_ref != draft_authority.base_ref
            or remote_head.head_ref != draft_authority.head_ref
        ):
            issues.append("remote identity or ref binding mismatch")
        if remote_head.remote_ref_exists is not True:
            issues.append("exact remote head ref does not exist")
        if remote_head.requires_push is not False:
            issues.append("same-turn draft pull request cannot require a push")
        if remote_head.draft is not True:
            issues.append("same-turn pull request must remain a draft")
        if (
            not _is_commit(remote_head.head_commit)
            or remote_head.head_commit != draft_authority.head_commit
        ):
            issues.append("remote head commit does not match the closed workspace")
    consumption_receipt = None
    if not issues and draft_authority is not None and decision.authorization_id is not None:
        consumption_receipt = DraftPullRequestConsumptionReceipt(
            request_id=current_request_id,
            authorization_id=decision.authorization_id,
            provider=draft_authority.provider,
            repository=draft_authority.repository,
            base_ref=draft_authority.base_ref,
            head_ref=draft_authority.head_ref,
            head_commit=draft_authority.head_commit,
            consumed_at=routed_at,
        )
    return LaterActionRoutingDecision(
        may_execute_same_turn=not issues,
        must_stop=bool(issues),
        authorization_id=decision.authorization_id,
        issues=tuple(sorted(set(issues))),
        consumption_receipt=consumption_receipt,
    )


def validate_continuity_bundle(
    evidence: object,
    *,
    brief_markdown: str,
    handoff_markdown: str,
    reconciliation_mapping: object | None = None,
    closure_packet_markdown: str | None = None,
    reconciliation_sha256: str | None = None,
    closure_packet_sha256: str | None = None,
) -> list[str]:
    if not isinstance(evidence, Mapping):
        return ["continuity evidence must be an object"]
    required = {"schema_version", "brief", "handoff", "conversation", "resume", "negative_scenarios"}
    optional = {"closure_packet", "later_action"}
    if set(evidence) - required - optional or required - set(evidence):
        return ["continuity evidence fields do not match the supported schema"]
    issues: list[str] = []
    if evidence.get("schema_version") != CONTINUITY_SCHEMA:
        issues.append("unsupported continuity bundle schema")
    try:
        brief_record = lean_brief_from_mapping(evidence.get("brief"))
        handoff_record = handoff_from_mapping(evidence.get("handoff"))
        conversation = conversation_assessment_from_mapping(evidence.get("conversation"))
        resume = resume_context_from_mapping(evidence.get("resume"))
    except ValueError as error:
        return [str(error)]
    issues.extend(validate_increment_brief(brief_record))
    issues.extend(validate_handoff(handoff_record))
    continuation_allowed, continuation_issues = evaluate_continuation(conversation)
    if conversation.approval_mode == "approval:full":
        if not continuation_allowed:
            issues.extend(continuation_issues)
    elif continuation_allowed:
        issues.append("one-increment mode cannot continue automatically")
    else:
        issues.extend(
            issue
            for issue in continuation_issues
            if issue != "one-increment approval mode requires a stop"
        )
    issues.extend(validate_resume_record(resume))
    bundle_resume_bindings = {
        "program_id": handoff_record.program_id,
        "program_revision": handoff_record.program_revision,
        "workspace_path": handoff_record.workspace_path,
        "workspace_branch": handoff_record.workspace_branch,
        "workspace_base_commit": handoff_record.base_commit,
        "workspace_head_commit": handoff_record.head_commit,
        "accepted_review_packet_sha256": handoff_record.accepted_review_packet_sha256,
        "accepted_handoff_addendum_sha256": handoff_record.accepted_handoff_addendum_sha256,
    }
    for name, expected_value in bundle_resume_bindings.items():
        if getattr(resume, name) != expected_value:
            issues.append(f"resume {name} mismatch")
    if not issues:
        if not _matches_supported_increment_brief(brief_record, brief_markdown):
            issues.append("rendered brief does not match the bound Markdown")
        if render_handoff(handoff_record) != handoff_markdown:
            issues.append("rendered handoff does not match the bound Markdown")
    if reconciliation_mapping is not None:
        try:
            reconciliation = closure_reconciliation_from_mapping(reconciliation_mapping)
        except ValueError as error:
            issues.append(str(error))
            reconciliation = None
        if reconciliation is not None:
            issues.extend(validate_closure_reconciliation(reconciliation))
        packet_mapping = evidence.get("closure_packet")
        if packet_mapping is None or closure_packet_markdown is None:
            issues.append("closure reconciliation requires a closure packet and Markdown")
        else:
            try:
                packet = closure_packet_from_mapping(packet_mapping)
            except ValueError as error:
                issues.append(str(error))
                packet = None
            if packet is not None:
                expected_reconciliation = reconciliation_sha256 or packet.reconciliation_sha256
                issues.extend(validate_closure_packet(packet, expected_reconciliation))
                if not validate_closure_packet(packet, expected_reconciliation) and render_closure_packet(packet) != closure_packet_markdown:
                    issues.append("rendered closure packet does not match the bound Markdown")
    later_action = evidence.get("later_action")
    if later_action is not None:
        if not isinstance(later_action, Mapping):
            issues.append("later_action must be an object")
        else:
            try:
                decision = decide_later_action(**later_action)
            except TypeError as error:
                issues.append(f"invalid later_action fields: {error}")
            else:
                if not decision.authorized:
                    issues.extend(decision.issues)
                if closure_packet_sha256 is not None and later_action.get("closure_packet_sha256") != closure_packet_sha256:
                    issues.append("later action closure packet digest mismatch")
    scenarios = evidence.get("negative_scenarios")
    expected_scenarios = {
        "overloaded-continuation",
        "stale-handoff",
        "premature-closure",
        "inferred-later-authority",
    }
    if not isinstance(scenarios, list) or {
        item.get("name") for item in scenarios if isinstance(item, Mapping)
    } != expected_scenarios:
        issues.append("continuity negative scenarios are incomplete")
    return sorted(set(issues))


def _regular_input(path_text: str, label: str) -> Path:
    path = Path(path_text)
    if not path.exists():
        raise _UsageError(f"{label} does not exist")
    if path.is_symlink() or not path.is_file():
        raise _UsageError(f"{label} must be a regular non-symlink file")
    return path


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: invalid JSON: {error}") from error


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(prog="continuity_closure.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-bundle")
    validate.add_argument("evidence")
    validate.add_argument("--brief", required=True)
    validate.add_argument("--handoff", required=True)
    validate.add_argument("--reconciliation")
    validate.add_argument("--closure-packet")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        arguments = parser.parse_args(argv)
        evidence_path = _regular_input(arguments.evidence, "evidence")
        brief_path = _regular_input(arguments.brief, "brief")
        handoff_path = _regular_input(arguments.handoff, "handoff")
        if bool(arguments.reconciliation) != bool(arguments.closure_packet):
            raise _UsageError("reconciliation and closure packet must be supplied together")
        reconciliation_path = (
            _regular_input(arguments.reconciliation, "reconciliation")
            if arguments.reconciliation
            else None
        )
        packet_path = (
            _regular_input(arguments.closure_packet, "closure packet")
            if arguments.closure_packet
            else None
        )
    except _UsageError as error:
        print(parser.format_usage().strip())
        print(f"error: {error}")
        return 2
    try:
        issues = validate_continuity_bundle(
            _load_json(evidence_path),
            brief_markdown=brief_path.read_text(encoding="utf-8"),
            handoff_markdown=handoff_path.read_text(encoding="utf-8"),
            reconciliation_mapping=(
                _load_json(reconciliation_path) if reconciliation_path else None
            ),
            closure_packet_markdown=(
                packet_path.read_text(encoding="utf-8") if packet_path else None
            ),
            reconciliation_sha256=(
                _sha256_file(reconciliation_path) if reconciliation_path else None
            ),
            closure_packet_sha256=(
                _sha256_file(packet_path) if packet_path else None
            ),
        )
    except (OSError, UnicodeError, ValueError) as error:
        print(str(error))
        return 1
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("Continuity and closure validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
