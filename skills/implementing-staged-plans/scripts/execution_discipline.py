#!/usr/bin/env python3
"""Validate execution evidence and boundaries without mutating a repository."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from repository_preparation import (
    AmendmentProposal,
    RepositoryObservation,
    SemanticNameRecord,
    classify_plan_amendment,
    validate_plan_overlap,
    validate_semantic_naming_inventory,
)
from state_authority import (
    APPROVAL_MODE_POLICIES,
    ActionBinding,
    AuthorizationDecision,
    decide_action_authorization,
)


EXECUTION_EVIDENCE_SCHEMA = "implementation-execution-evidence/v1"
ALTERNATIVE_VERIFICATION_KINDS = frozenset(
    {"declaration", "documentation", "fixture", "manifest", "reference"}
)
OWNERSHIP_DISPOSITIONS = frozenset(
    {"create", "extend", "preserve", "managed", "generated", "application-owned"}
)
EXECUTION_SURFACE_CHANGES = frozenset({"created", "renamed", "existing"})
RECOVERY_DOMAINS = (
    "source-code",
    "persistent-data",
    "deployment",
    "provider-or-external-state",
)
RECOVERY_ACTIONS = MappingProxyType(
    {
        "source-code": frozenset(
            {"create-local-commit", "destructive-operation", "modify-workspace"}
        ),
        "persistent-data": frozenset(
            {"destructive-operation", "migrate", "modify-external-state"}
        ),
        "deployment": frozenset({"deploy", "modify-external-state", "release"}),
        "provider-or-external-state": frozenset(
            {"modify-external-state", "modify-provider-state"}
        ),
    }
)

_STABLE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_COMMIT_MESSAGE = re.compile(
    r"^(?:build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test): [a-z0-9].+$"
)


@dataclass(frozen=True)
class TestFirstEvidence:
    schema_version: str
    slice_id: str
    purpose: str
    red_command: str
    expected_failure: str
    observed_failure: str
    red_exit_code: int
    observed_before_production_change: bool
    intended_reason_match: bool
    green_command: str
    observed_green: str
    green_exit_code: int
    evidence_order: tuple[str, ...]


@dataclass(frozen=True)
class AlternativeVerificationContract:
    schema_version: str
    surface_kind: str
    reason_tdd_is_artificial: str
    command: str
    expected_evidence: str
    observed_evidence: str
    exit_code: int
    relevant_inputs: tuple[str, ...]
    residual_limitation: str
    behavioral_test_available: bool


@dataclass(frozen=True)
class OwnershipBoundary:
    path: str
    disposition: str
    owner: str
    accepted_overlap: bool
    pre_write_fingerprint: str
    post_write_fingerprint: str
    owning_mechanism: str
    verification_command: str


@dataclass(frozen=True)
class ExecutionSurface:
    surface: str
    surface_kind: str
    change_kind: str


@dataclass(frozen=True)
class ExecutionAmendmentDecision:
    classification: str
    may_proceed: bool
    requires_exact_plan_approval: bool
    requires_program_revision: bool
    renewed_review_required: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CommitBoundary:
    boundary_id: str
    purpose: str
    message: str
    paths: tuple[str, ...]
    depends_on: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryDomainPlan:
    domain: str
    touched: bool
    disposition: str
    mechanism: str
    verification: str
    limitation: str
    required_authority: str
    authority_granted: bool


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_sequence(value: object) -> bool:
    return (
        isinstance(value, (tuple, list))
        and bool(value)
        and all(_nonempty(item) for item in value)
    )


def _tuple_string_sequence(value: object, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, tuple)
        and (allow_empty or bool(value))
        and all(_nonempty(item) for item in value)
    )


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_execution_evidence(
    test_first_records: Sequence[TestFirstEvidence],
    alternative_records: Sequence[AlternativeVerificationContract],
) -> list[str]:
    """Validate observed RED/GREEN evidence or a non-behavioral alternative."""
    issues: list[str] = []
    if not test_first_records and not alternative_records:
        issues.append("execution requires test-first or alternative verification evidence")
    slice_ids: set[str] = set()
    for record in test_first_records:
        label = record.slice_id or "<missing>"
        if record.schema_version != EXECUTION_EVIDENCE_SCHEMA:
            issues.append(f"test-first slice {label!r} has unsupported schema")
        if not _nonempty(record.slice_id) or _STABLE_IDENTIFIER.fullmatch(record.slice_id) is None:
            issues.append("test-first slice identifier must be stable lower-kebab-case")
        elif record.slice_id in slice_ids:
            issues.append(f"test-first slice {record.slice_id!r} is duplicated")
        slice_ids.add(record.slice_id)
        for field in (
            "purpose",
            "red_command",
            "expected_failure",
            "observed_failure",
            "green_command",
            "observed_green",
        ):
            if not _nonempty(getattr(record, field)):
                issues.append(f"test-first slice {label!r} {field} must be non-empty")
        if not _integer(record.red_exit_code) or record.red_exit_code == 0:
            issues.append(f"test-first slice {label!r} RED exit must be a nonzero integer")
        if type(record.observed_before_production_change) is not bool or not record.observed_before_production_change:
            issues.append(f"test-first slice {label!r} RED must precede production change")
        if type(record.intended_reason_match) is not bool or not record.intended_reason_match:
            issues.append(f"test-first slice {label!r} RED did not fail for the intended reason")
        if (
            _nonempty(record.expected_failure)
            and _nonempty(record.observed_failure)
            and record.expected_failure != record.observed_failure
        ):
            issues.append(f"test-first slice {label!r} observed failure does not match expectation")
        if not _integer(record.green_exit_code) or record.green_exit_code != 0:
            issues.append(f"test-first slice {label!r} GREEN exit must be integer zero")
        if not isinstance(record.evidence_order, tuple):
            issues.append(f"test-first slice {label!r} evidence order must be immutable")
        elif record.evidence_order != ("red", "green"):
            issues.append(f"test-first slice {label!r} evidence order must be RED then GREEN")

    for index, record in enumerate(alternative_records, start=1):
        label = f"alternative verification {index}"
        if record.schema_version != EXECUTION_EVIDENCE_SCHEMA:
            issues.append(f"{label} has unsupported schema")
        if record.surface_kind not in ALTERNATIVE_VERIFICATION_KINDS:
            issues.append(f"{label} is not a supported non-behavioral surface")
        for field in (
            "reason_tdd_is_artificial",
            "command",
            "expected_evidence",
            "observed_evidence",
            "residual_limitation",
        ):
            if not _nonempty(getattr(record, field)):
                issues.append(f"{label} {field} must be non-empty")
        if not _integer(record.exit_code) or record.exit_code != 0:
            issues.append(f"{label} exit must be integer zero")
        if not _tuple_string_sequence(record.relevant_inputs):
            issues.append(f"{label} relevant_inputs must be a non-empty immutable string sequence")
        if type(record.behavioral_test_available) is not bool:
            issues.append(f"{label} behavioral_test_available must be boolean")
        elif record.behavioral_test_available:
            issues.append(f"{label} cannot bypass an available behavioral test")
    return sorted(set(issues))


def validate_execution_ownership(
    planned_paths: Sequence[str],
    actual_changed_paths: Sequence[str],
    boundaries: Sequence[OwnershipBoundary],
    pre_write_observation: RepositoryObservation,
    accepted_existing_paths: Sequence[str],
) -> list[str]:
    """Require exact planned changes and explicit ownership dispositions."""
    issues: list[str] = []
    planned = set(planned_paths)
    actual = set(actual_changed_paths)
    if len(planned) != len(tuple(planned_paths)):
        issues.append("planned paths contain duplicates")
    if len(actual) != len(tuple(actual_changed_paths)):
        issues.append("actual changed paths contain duplicates")
    if planned != actual:
        missing = sorted(planned.difference(actual))
        extra = sorted(actual.difference(planned))
        issues.append(
            "actual changed paths do not match planned paths"
            f"; missing={missing!r}; extra={extra!r}"
        )

    by_path: dict[str, OwnershipBoundary] = {}
    duplicate_paths: set[str] = set()
    for boundary in boundaries:
        if boundary.path in by_path:
            duplicate_paths.add(boundary.path)
        else:
            by_path[boundary.path] = boundary
        if not _nonempty(boundary.path):
            issues.append("ownership path must be non-empty")
        if boundary.disposition not in OWNERSHIP_DISPOSITIONS:
            issues.append(f"ownership path {boundary.path!r} has unknown disposition")
        if not _nonempty(boundary.owner):
            issues.append(f"ownership path {boundary.path!r} needs an exact owner")
        if type(boundary.accepted_overlap) is not bool:
            issues.append(f"ownership path {boundary.path!r} accepted_overlap must be boolean")
        if boundary.disposition == "preserve":
            if boundary.pre_write_fingerprint != boundary.post_write_fingerprint:
                issues.append(f"ownership path {boundary.path!r} preserve fingerprint changed")
        elif boundary.path not in planned:
            issues.append(f"unplanned ownership path {boundary.path!r} is not preserve-only")
        if boundary.disposition in {"managed", "generated", "application-owned"}:
            if not _nonempty(boundary.owning_mechanism) or boundary.owning_mechanism == "none":
                issues.append(f"ownership path {boundary.path!r} needs an owning mechanism")
            if not _nonempty(boundary.verification_command):
                issues.append(f"ownership path {boundary.path!r} needs a verification command")
    for path in sorted(duplicate_paths):
        issues.append(f"duplicate ownership boundary for {path!r}")
    for path in sorted(actual.difference(by_path)):
        issues.append(f"actual changed path {path!r} has no ownership boundary")

    accepted = set(accepted_existing_paths)
    for boundary in boundaries:
        expected_overlap = boundary.path in accepted
        if (
            type(boundary.accepted_overlap) is bool
            and boundary.accepted_overlap != expected_overlap
        ):
            issues.append(
                f"ownership path {boundary.path!r} accepted_overlap disagrees with controlling inputs"
            )
    dispositions = {
        boundary.path: boundary.disposition
        for boundary in boundaries
        if boundary.path in planned
    }
    managed = tuple(
        boundary.path
        for boundary in boundaries
        if boundary.disposition in {"managed", "generated", "application-owned"}
    )
    managed_owners = {
        boundary.path: (
            f"{boundary.owning_mechanism}; {boundary.verification_command}"
            if _nonempty(boundary.owning_mechanism)
            and boundary.owning_mechanism != "none"
            and _nonempty(boundary.verification_command)
            else ""
        )
        for boundary in boundaries
    }
    issues.extend(
        validate_plan_overlap(
            tuple(planned),
            pre_write_observation,
            tuple(accepted),
            dispositions,
            managed_paths=managed,
            managed_owners=managed_owners,
        )
    )
    return sorted(set(issues))


def validate_execution_surfaces(
    surfaces: Sequence[ExecutionSurface],
    naming_records: Sequence[SemanticNameRecord],
) -> list[str]:
    """Require one contextual naming record per created or renamed surface."""
    issues: list[str] = []
    surface_counts: dict[str, int] = {}
    for item in surfaces:
        surface_counts[item.surface] = surface_counts.get(item.surface, 0) + 1
        if not _nonempty(item.surface):
            issues.append("execution surface must be non-empty")
        if item.change_kind not in EXECUTION_SURFACE_CHANGES:
            issues.append(f"execution surface {item.surface!r} has unknown change kind")
    for name, count in surface_counts.items():
        if count > 1:
            issues.append(f"execution surface {name!r} is duplicated")

    changed = {
        (item.surface, item.surface_kind)
        for item in surfaces
        if item.change_kind in {"created", "renamed"}
    }
    inventoried = {(record.surface, record.surface_kind) for record in naming_records}
    if changed != inventoried:
        issues.append(
            "created and renamed execution surface kind pairs do not match semantic naming inventory"
            f"; missing={sorted(changed.difference(inventoried))!r}"
            f"; extra={sorted(inventoried.difference(changed))!r}"
        )
    issues.extend(validate_semantic_naming_inventory(naming_records))
    return sorted(set(issues))


def decide_execution_amendment(
    proposal: AmendmentProposal,
    approval_mode: str,
    *,
    affected_surfaces: Sequence[str],
    recovery_or_reversal: str,
    renewed_review: bool,
) -> ExecutionAmendmentDecision:
    """Apply program-dominant classification before mode-bounded autonomy."""
    assessment = classify_plan_amendment(proposal)
    reasons: list[str] = []
    requires_exact_plan_approval = False
    renewed_review_required = (
        assessment.classification == "bounded-implementation-amendment"
    )

    if approval_mode not in APPROVAL_MODE_POLICIES:
        reasons.append("unknown approval mode")
    if assessment.classification in {
        "authoritative-contradiction",
        "program-amendment",
    }:
        reasons.extend(assessment.reasons)
        return ExecutionAmendmentDecision(
            assessment.classification,
            False,
            False,
            True,
            renewed_review_required,
            tuple(sorted(set(reasons))),
        )
    if not assessment.may_proceed_under_current_mode:
        reasons.extend(assessment.reasons)
    if not _string_sequence(affected_surfaces):
        reasons.append("execution amendment needs affected surfaces")
    if not _nonempty(recovery_or_reversal):
        reasons.append("execution amendment needs reversal or recovery")
    if type(renewed_review) is not bool:
        reasons.append("renewed_review must be boolean")
    elif renewed_review_required and not renewed_review:
        reasons.append("bounded implementation amendment needs renewed review")

    if (
        assessment.classification == "bounded-implementation-amendment"
        and approval_mode == "approval:standard"
        and not reasons
    ):
        requires_exact_plan_approval = True
        reasons.append("approval:standard requires renewed exact-plan approval")
    allowed = not reasons
    return ExecutionAmendmentDecision(
        assessment.classification,
        allowed,
        requires_exact_plan_approval,
        False,
        renewed_review_required,
        tuple(sorted(set(reasons)))
        if reasons
        else ("bounded execution record is complete",),
    )


def decide_commit_authorization(
    records: list[dict[str, object]], required: ActionBinding
) -> AuthorizationDecision:
    """Reuse exact state authority for the separate local-commit action."""
    if required.action != "create-local-commit":
        return AuthorizationDecision(
            False,
            None,
            ("commit authority check requires create-local-commit action",),
        )
    return decide_action_authorization(records, required)


def validate_commit_boundaries(
    *,
    actual_changed_paths: Sequence[str],
    planned_paths: Sequence[str],
    protected_paths: Sequence[str],
    boundaries: Sequence[CommitBoundary],
    commit_authorization: AuthorizationDecision,
) -> list[str]:
    """Validate logical partitions and separately report absent commit authority."""
    issues: list[str] = []
    actual = set(actual_changed_paths)
    planned = set(planned_paths)
    protected = set(protected_paths)
    if len(actual) != len(tuple(actual_changed_paths)):
        issues.append("actual changed paths contain duplicates")
    if len(planned) != len(tuple(planned_paths)):
        issues.append("planned paths contain duplicates")
    if actual != planned:
        issues.append("logical commit inputs do not match the exact planned path set")
    if not boundaries:
        issues.append("at least one logical commit boundary is required")

    identifiers: set[str] = set()
    assigned: dict[str, str] = {}
    for index, item in enumerate(boundaries):
        if not _nonempty(item.boundary_id) or _STABLE_IDENTIFIER.fullmatch(item.boundary_id) is None:
            issues.append("logical commit boundary identifier must be stable lower-kebab-case")
        elif item.boundary_id in identifiers:
            issues.append(f"logical commit boundary {item.boundary_id!r} is duplicated")
        if not _nonempty(item.purpose):
            issues.append(f"logical commit boundary {item.boundary_id!r} needs a purpose")
        if not _nonempty(item.message) or _COMMIT_MESSAGE.fullmatch(item.message) is None:
            issues.append(f"logical commit boundary {item.boundary_id!r} message is not normal form")
        if not _tuple_string_sequence(item.paths):
            issues.append(
                f"logical commit boundary {item.boundary_id!r} needs non-empty immutable paths"
            )
        elif len(set(item.paths)) != len(tuple(item.paths)):
            issues.append(f"logical commit boundary {item.boundary_id!r} repeats a path")
        if not _tuple_string_sequence(item.depends_on, allow_empty=True):
            issues.append(
                f"logical commit boundary {item.boundary_id!r} dependencies must be immutable strings"
            )
        known_before = set(boundary.boundary_id for boundary in boundaries[:index])
        for dependency in item.depends_on:
            if dependency not in identifiers.union(
                boundary.boundary_id for boundary in boundaries[index + 1 :]
            ):
                issues.append(
                    f"logical commit boundary {item.boundary_id!r} has unknown dependency {dependency!r}"
                )
            elif dependency not in known_before:
                issues.append(
                    f"logical commit boundary {item.boundary_id!r} depends on a later boundary {dependency!r}"
                )
        for path in item.paths:
            if path in assigned:
                issues.append(
                    f"logical commit path {path!r} is assigned to multiple boundaries"
                )
            else:
                assigned[path] = item.boundary_id
            if path not in actual:
                issues.append(f"logical commit path {path!r} is not an actual changed path")
            if path not in planned:
                issues.append(f"logical commit path {path!r} is unplanned")
            if path in protected:
                issues.append(f"protected path {path!r} appears in a logical commit boundary")
        identifiers.add(item.boundary_id)
    missing = actual.difference(assigned)
    if missing:
        issues.append(f"actual changed paths are missing logical boundaries: {sorted(missing)!r}")
    extra = set(assigned).difference(actual)
    if extra:
        issues.append(f"logical boundaries contain extra paths: {sorted(extra)!r}")
    if (
        type(commit_authorization.authorized) is not bool
        or not commit_authorization.authorized
        or not _nonempty(commit_authorization.authorization_id)
        or bool(commit_authorization.issues)
    ):
        issues.append("create-local-commit action is not authorized")
    return sorted(set(issues))


def validate_recovery_domains(
    plans: Sequence[RecoveryDomainPlan],
) -> list[str]:
    """Keep source, data, deployment, and provider recovery independent."""
    issues: list[str] = []
    counts: dict[str, int] = {}
    for plan in plans:
        counts[plan.domain] = counts.get(plan.domain, 0) + 1
        if plan.domain not in RECOVERY_DOMAINS:
            issues.append(f"unknown recovery domain {plan.domain!r}")
        if type(plan.touched) is not bool:
            issues.append(f"recovery domain {plan.domain!r} touched must be boolean")
        if type(plan.authority_granted) is not bool:
            issues.append(
                f"recovery domain {plan.domain!r} authority_granted must be boolean"
            )
        if plan.touched is True:
            if plan.disposition != "recoverable":
                issues.append(
                    f"touched recovery domain {plan.domain!r} needs recoverable disposition"
                )
            for field in ("mechanism", "verification", "limitation", "required_authority"):
                if not _nonempty(getattr(plan, field)):
                    issues.append(f"touched recovery domain {plan.domain!r} needs {field}")
            if plan.required_authority == "none":
                issues.append(
                    f"touched recovery domain {plan.domain!r} needs consequential action authority"
                )
            elif (
                plan.domain in RECOVERY_ACTIONS
                and plan.required_authority not in RECOVERY_ACTIONS[plan.domain]
            ):
                issues.append(
                    f"recovery domain {plan.domain!r} authority is not valid for that domain"
                )
            if plan.authority_granted is not True:
                issues.append(
                    f"touched recovery domain {plan.domain!r} lacks required authority"
                )
            if (
                plan.domain != "source-code"
                and "git" in plan.mechanism.lower()
            ):
                issues.append(
                    f"Git rollback cannot recover {plan.domain!r}"
                )
        elif plan.touched is False:
            if plan.disposition != "not-touched":
                issues.append(
                    f"untouched recovery domain {plan.domain!r} needs not-touched disposition"
                )
            if plan.authority_granted:
                issues.append(
                    f"untouched recovery domain {plan.domain!r} must not claim authority"
                )
            if plan.mechanism != "none":
                issues.append(
                    f"untouched recovery domain {plan.domain!r} mechanism must be none"
                )
            if plan.required_authority != "none":
                issues.append(
                    f"untouched recovery domain {plan.domain!r} required_authority must be none"
                )
            for field in ("verification", "limitation"):
                if not _nonempty(getattr(plan, field)):
                    issues.append(f"untouched recovery domain {plan.domain!r} needs {field}")

    for domain in RECOVERY_DOMAINS:
        if counts.get(domain, 0) != 1:
            issues.append(f"recovery domain {domain!r} must appear exactly once")
    return sorted(set(issues))


def _tuple_fields(value: Mapping[str, object], fields: Sequence[str]) -> dict[str, object]:
    converted = dict(value)
    for field in fields:
        item = converted.get(field)
        if isinstance(item, list):
            converted[field] = tuple(item)
    return converted


def validate_execution_bundle(scenario: Mapping[str, object]) -> list[str]:
    """Compose one caller-supplied prepared execution scenario without mutation."""
    issues: list[str] = []
    try:
        test_first = tuple(
            TestFirstEvidence(**_tuple_fields(record, ("evidence_order",)))
            for record in scenario["test_first_evidence"]
        )
        alternatives = tuple(
            AlternativeVerificationContract(
                **_tuple_fields(record, ("relevant_inputs",))
            )
            for record in scenario["alternative_verification"]
        )
        observation_value = _tuple_fields(
            scenario["pre_write_observation"],
            ("staged_paths", "modified_paths", "untracked_paths", "conflicted_paths"),
        )
        pre_write_observation = RepositoryObservation(**observation_value)
        ownership = tuple(
            OwnershipBoundary(**record) for record in scenario["ownership_boundaries"]
        )
        surfaces = tuple(
            ExecutionSurface(**record) for record in scenario["execution_surfaces"]
        )
        names = tuple(
            SemanticNameRecord(**record) for record in scenario["semantic_names"]
        )
        amendment_value = scenario["amendment"]
        proposal = AmendmentProposal(
            **_tuple_fields(
                amendment_value["proposal"], ("changed_dimensions", "evidence")
            )
        )
        commit_boundaries = tuple(
            CommitBoundary(**_tuple_fields(record, ("paths", "depends_on")))
            for record in scenario["commit_boundaries"]
        )
        authorization_value = _tuple_fields(
            scenario["commit_authorization"], ("issues",)
        )
        commit_authorization = AuthorizationDecision(**authorization_value)
        recovery_plans = tuple(
            RecoveryDomainPlan(**record) for record in scenario["recovery_domains"]
        )
    except (KeyError, TypeError, ValueError):
        return ["execution bundle is structurally invalid"]

    issues.extend(validate_execution_evidence(test_first, alternatives))
    issues.extend(
        validate_execution_ownership(
            scenario["planned_paths"],
            scenario["actual_changed_paths"],
            ownership,
            pre_write_observation,
            scenario["accepted_existing_paths"],
        )
    )
    issues.extend(validate_execution_surfaces(surfaces, names))
    amendment_decision = decide_execution_amendment(
        proposal,
        amendment_value["approval_mode"],
        affected_surfaces=amendment_value["affected_surfaces"],
        recovery_or_reversal=amendment_value["recovery_or_reversal"],
        renewed_review=amendment_value["renewed_review"],
    )
    if not amendment_decision.may_proceed:
        issues.extend(amendment_decision.reasons)
    commit_issues = validate_commit_boundaries(
        actual_changed_paths=scenario["actual_changed_paths"],
        planned_paths=scenario["planned_paths"],
        protected_paths=tuple(
            boundary.path
            for boundary in ownership
            if boundary.disposition == "preserve"
        ),
        boundaries=commit_boundaries,
        commit_authorization=commit_authorization,
    )
    if scenario["commit_requested"] is False:
        if commit_authorization.authorized:
            commit_issues.append(
                "commit authorization must remain absent when no commit is requested"
            )
        else:
            commit_issues = [
                issue
                for issue in commit_issues
                if issue != "create-local-commit action is not authorized"
            ]
    issues.extend(commit_issues)
    issues.extend(validate_recovery_domains(recovery_plans))
    return sorted(set(issues))
