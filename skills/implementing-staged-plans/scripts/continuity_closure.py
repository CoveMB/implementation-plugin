#!/usr/bin/env python3
"""Generate and validate continuity, closure, and later-action evidence."""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from state_authority import (
    APPROVAL_MODE_POLICIES,
    approval_mode_policy,
    atomic_replace_json,
    validate_state_authority,
)


CONTINUITY_SCHEMA = "implementation-continuity-evidence/v1"
RECONCILIATION_SCHEMA = "implementation-closure-reconciliation/v1"
CLOSURE_PACKET_SCHEMA = "implementation-closure-packet/v1"

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
class LaterActionDecision:
    authorized: bool
    authorization_id: str | None
    issues: tuple[str, ...]


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


def render_increment_brief(candidate: LeanBrief) -> str:
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
    compared = tuple(
        field.name
        for field in fields(ResumeContext)
        if field.name
        not in {"conflicted_paths", "active_git_operation", "matching_authorization_ids"}
    )
    for name in compared:
        if getattr(observed, name) != getattr(expected, name):
            issues.append(f"resume {name} mismatch")
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
    if (program_root is None) != (observation is None):
        issues.append("resume state composition requires both program root and observation")
    elif program_root is not None and observation is not None:
        issues.extend(validate_state_authority(Path(program_root), observation))
    return sorted(set(issues))


def _safe_path(root: Path, relative_path: str) -> Path:
    if not _nonempty(relative_path):
        raise ValueError("managed relative path is required")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("managed path must stay beneath the root")
    if not root.is_dir() or root.is_symlink():
        raise ValueError("managed root must be a regular non-symlink directory")
    target = root / relative
    parent = root
    for part in relative.parts[:-1]:
        parent = parent / part
        if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
            raise ValueError("managed path traverses a symlink or non-directory")
    return target


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_create_text(path: Path, value: str) -> str:
    if path.exists() or path.is_symlink():
        raise ValueError(f"{path}: target already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(value)
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
    return _sha256_file(path)


def _replace_json_through_state_authority(
    path: Path, value: Mapping[str, object], expected_sha256: str
) -> str:
    return atomic_replace_json(
        path, dict(value), expected_sha256
    ).current_sha256


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
    if len(matching_authorization_ids) != 1 or not _nonempty(
        matching_authorization_ids[0]
    ):
        raise ValueError("exactly one rollover action authorization is required")
    if current_increment_state != "accepted":
        raise ValueError("current increment must be accepted before rollover")
    if not _nonempty(expected_current_increment_id) or not _nonempty(next_increment_id):
        raise ValueError("current and next increment ids are required")
    if current_increment_id != expected_current_increment_id:
        raise ValueError("current increment binding changed")
    if expected_current_increment_id == next_increment_id:
        raise ValueError("rollover must advance to a different increment")
    if expected_current_increment_id not in next_increment_dependencies:
        raise ValueError("next increment dependency does not include the accepted increment")
    if fail_after_writes is not None and (
        not _is_int(fail_after_writes) or fail_after_writes < 0
    ):
        raise ValueError("fail_after_writes must be a non-negative integer")
    handoff_issues = validate_handoff(handoff_record)
    brief_issues = validate_increment_brief(brief_record)
    if handoff_issues or brief_issues:
        raise ValueError("; ".join([*handoff_issues, *brief_issues]))
    if render_handoff(handoff_record) != handoff_markdown:
        raise ValueError("handoff Markdown does not match the validated record")
    if render_increment_brief(brief_record) != brief_markdown:
        raise ValueError("brief Markdown does not match the validated record")
    root = Path(root)
    paths = (
        _safe_path(root, handoff_relative_path),
        _safe_path(root, brief_relative_path),
        _safe_path(root, manifest_relative_path),
        _safe_path(root, status_relative_path),
    )
    if not _nonempty(handoff_markdown) or not _nonempty(brief_markdown):
        raise ValueError("validated handoff and brief markdown are required")
    for path, expected_sha256 in (
        (paths[2], expected_manifest_sha256),
        (paths[3], expected_status_sha256),
    ):
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"{path}: expected a regular non-symlink file")
        if _sha256_file(path) != expected_sha256:
            raise ValueError(f"{path}: digest changed")
    navigation_exists = tuple(path.exists() or path.is_symlink() for path in paths[:2])
    if navigation_exists == (False, False):
        navigation_writes = (
            (handoff_relative_path, lambda: _atomic_create_text(paths[0], handoff_markdown)),
            (brief_relative_path, lambda: _atomic_create_text(paths[1], brief_markdown)),
        )
    elif navigation_exists == (True, True):
        expected_navigation = (
            (paths[0], handoff_markdown.encode("utf-8")),
            (paths[1], brief_markdown.encode("utf-8")),
        )
        for path, expected_bytes in expected_navigation:
            if path.is_symlink() or not path.is_file():
                raise ValueError("existing rollover navigation must be regular non-symlink files")
            try:
                actual_bytes = path.read_bytes()
            except OSError as error:
                raise ValueError(
                    f"existing rollover navigation could not be read: {error.__class__.__name__}"
                ) from error
            if actual_bytes != expected_bytes:
                raise ValueError("existing rollover navigation does not match validated bytes")
        navigation_writes = ()
    else:
        raise ValueError("rollover navigation targets must both be absent or both be exact")
    writes = (
        *navigation_writes,
        (manifest_relative_path, lambda: _replace_json_through_state_authority(paths[2], manifest_value, expected_manifest_sha256)),
        (status_relative_path, lambda: _replace_json_through_state_authority(paths[3], status_value, expected_status_sha256)),
    )
    completed: list[tuple[str, str]] = []
    for index, (relative_path, writer) in enumerate(writes):
        if fail_after_writes is not None and index >= fail_after_writes:
            return ContinuityWriteReceipt(tuple(completed), relative_path, True)
        try:
            completed.append((relative_path, writer()))
        except (OSError, ValueError):
            return ContinuityWriteReceipt(tuple(completed), relative_path, True)
    return ContinuityWriteReceipt(tuple(completed), None, False)


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
        expected_labels = {
            f"{increment_id}:{role}"
            for increment_id in candidate.accepted_increment_ids
            for role in ("review-packet", "handoff-addendum")
        }
        if len(labels) != len(set(labels)) or set(labels) != expected_labels:
            issues.append("packet and addendum bindings must cover every accepted increment exactly")
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
    for record in matching_grants:
        expires = record.get("expires_at")
        parsed = _timestamp(expires) if expires is not None else None
        if expires is None or (parsed is not None and parsed > datetime.now(timezone.utc)):
            current_grants.append(record)
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
    return LaterActionDecision(not issues, authorization_id, tuple(sorted(set(issues))))


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
    issues.extend(validate_resume_context(resume, resume))
    if not issues:
        if render_increment_brief(brief_record) != brief_markdown:
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
