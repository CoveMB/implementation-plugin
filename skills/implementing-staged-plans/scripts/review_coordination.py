#!/usr/bin/env python3
"""Validate review evidence and human packets without mutating a repository."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType

from execution_discipline import (
    AlternativeVerificationContract,
    RecoveryDomainPlan,
    TestFirstEvidence,
    validate_execution_evidence,
    validate_recovery_domains,
)
from repository_preparation import (
    SemanticNameRecord,
    validate_semantic_naming_inventory,
)


REVIEW_EVIDENCE_SCHEMA = "implementation-review-evidence/v1"
REVIEW_PACKET_SCHEMA = "implementation-review-packet/v1"
RAW_REVIEW_REPORT_SCHEMA = "implementation-raw-review-report/v1"
REQUIRED_REVIEW_SCOPES = ("requirements", "architecture", "test-evidence")
RISK_REVIEW_SCOPES = MappingProxyType(
    {
        "security-privacy": "specialist-security-privacy",
        "public-api-compatibility": "specialist-compatibility",
        "concurrency-reliability-distributed-state": "specialist-reliability",
        "persistent-data-migrations": "specialist-persistent-data",
        "accessibility": "specialist-accessibility",
        "platform-deployment-infrastructure": "specialist-platform",
        "payments-financial-state": "specialist-financial",
        "performance": "specialist-performance",
        "provider-external-state": "specialist-provider",
    }
)
FINDING_CLASSIFICATIONS = frozenset(
    {"material", "non-material", "speculative", "invalid"}
)
FINDING_DISPOSITIONS = frozenset(
    {"open", "repaired", "accepted-risk", "deferred", "dismissed", "not-actionable"}
)
FINDING_CONFIDENCE = frozenset({"low", "medium", "high"})
SEMANTIC_STATUSES = frozenset({"accepted", "finding"})
PACKET_FIELDS = (
    "identity_and_outcome",
    "changes_and_rationale",
    "program_context",
    "changed_files_by_purpose",
    "human_review_order",
    "requirements_and_acceptance",
    "exact_commands_and_results",
    "baseline_failures",
    "execution_evidence",
    "reviewer_roles_findings_dispositions",
    "repairs_and_renewed_verification",
    "deviations_and_amendments",
    "human_judgment",
    "edge_cases_and_manual_checks",
    "implications",
    "residual_risks_and_deferred_work",
    "recovery",
    "workspace_and_logical_boundaries",
    "current_state_and_next_action",
)
PACKET_HEADINGS = MappingProxyType(
    {
        "identity_and_outcome": "Identity and outcome",
        "changes_and_rationale": "Changes and rationale",
        "program_context": "Program context",
        "changed_files_by_purpose": "Changed files by purpose",
        "human_review_order": "Human review order",
        "requirements_and_acceptance": "Requirements and acceptance",
        "exact_commands_and_results": "Exact commands and results",
        "baseline_failures": "Baseline failures",
        "execution_evidence": "Execution evidence",
        "reviewer_roles_findings_dispositions": "Reviewer roles, findings, and dispositions",
        "repairs_and_renewed_verification": "Repairs and renewed verification",
        "deviations_and_amendments": "Deviations and amendments",
        "human_judgment": "Human judgment",
        "edge_cases_and_manual_checks": "Edge cases and manual checks",
        "implications": "Implications",
        "residual_risks_and_deferred_work": "Residual risks and deferred work",
        "recovery": "Recovery",
        "workspace_and_logical_boundaries": "Workspace and logical boundaries",
        "current_state_and_next_action": "Current state and next action",
    }
)
BUNDLE_FIELDS = frozenset(
    {
        "schema_version",
        "risk_predicates",
        "reports",
        "findings",
        "semantic_surfaces",
        "semantic_naming",
        "remediation_cycles",
        "test_first_evidence",
        "alternative_verification",
        "recovery_domains",
        "final_verification",
        "review_packet",
    }
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STABLE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class ReviewRiskPredicate:
    predicate: str
    touched: bool
    specialist_scope: str
    evidence: str
    rationale: str


@dataclass(frozen=True)
class ReviewReport:
    report_id: str
    scope: str
    reviewer_role: str
    independent: bool
    reduced_assurance: bool
    raw_report_path: str
    raw_report_sha256: str
    persisted_at: str
    reconciled_at: str
    finding_ids: tuple[str, ...]
    follow_up_for_finding_ids: tuple[str, ...]
    reviewed_candidate_sha256: str
    review_basis: str
    prior_conclusions_withheld: bool


@dataclass(frozen=True)
class ReviewFinding:
    finding_id: str
    report_id: str
    scope: str
    classification: str
    summary: str
    evidence: str
    impact: str
    confidence: str
    remediation: str
    disposition: str
    affected_requirement_or_invariant: str
    severity: str
    inspection_path: str
    decision_reference: str


@dataclass(frozen=True)
class SemanticNamingDisposition:
    surface: str
    surface_kind: str
    context: str
    intention: str
    planning_term_basis: str
    basis_owner: str
    compatibility_class: str
    compatibility_disposition: str
    status: str
    finding_id: str


@dataclass(frozen=True)
class RemediationCycle:
    cycle_id: str
    finding_ids: tuple[str, ...]
    started_at: str
    completed_at: str
    regression_command: str
    intended_failure: str
    observed_failure: str
    repair: str
    verification_command: str
    verification_result: str
    renewed_report_ids: tuple[str, ...]
    changed_paths: tuple[str, ...]
    affected_scopes: tuple[str, ...]


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_code: int
    result: str
    completed_at: str
    expected_result: str
    relevant_inputs: tuple[str, ...]


@dataclass(frozen=True)
class FinalVerification:
    candidate_sha256: str
    verified_at: str
    commands: tuple[CommandResult, ...]
    unresolved_material_findings: int
    verified_paths: tuple[str, ...]
    required_commands: tuple[str, ...]
    baseline_failures: tuple[str, ...]


@dataclass(frozen=True)
class ReviewPacket:
    schema_version: str
    candidate_sha256: str
    identity_and_outcome: tuple[str, ...]
    changes_and_rationale: tuple[str, ...]
    program_context: tuple[str, ...]
    changed_files_by_purpose: tuple[str, ...]
    human_review_order: tuple[str, ...]
    requirements_and_acceptance: tuple[str, ...]
    exact_commands_and_results: tuple[str, ...]
    baseline_failures: tuple[str, ...]
    execution_evidence: tuple[str, ...]
    reviewer_roles_findings_dispositions: tuple[str, ...]
    repairs_and_renewed_verification: tuple[str, ...]
    deviations_and_amendments: tuple[str, ...]
    human_judgment: tuple[str, ...]
    edge_cases_and_manual_checks: tuple[str, ...]
    implications: tuple[str, ...]
    residual_risks_and_deferred_work: tuple[str, ...]
    recovery: tuple[str, ...]
    workspace_and_logical_boundaries: tuple[str, ...]
    current_state_and_next_action: tuple[str, ...]


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_raw_review_report(path: Path, expected_scope: str) -> dict[str, object]:
    """Load one status-current raw report without accepting caller-selected shape."""
    report_path = Path(path)
    if report_path.is_symlink() or not report_path.is_file():
        raise ValueError(f"raw {expected_scope} report must be a regular non-symlink file")
    try:
        value = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"raw {expected_scope} report is invalid") from error
    if not isinstance(value, dict):
        raise ValueError(f"raw {expected_scope} report must be an object")
    allowed = {
        "schema_version",
        "scope",
        "program_id",
        "program_revision",
        "increment_id",
        "reviewer_role",
        "independent",
        "reduced_assurance",
        "persisted_at",
        "reconciled_at",
        "review_basis",
        "prior_conclusions_withheld",
        "findings",
        "risk_predicates",
        "test_first_evidence",
        "alternative_verification",
        "recovery_domains",
        "final_verification",
        "remediation_cycles",
    }
    if set(value).difference(allowed):
        raise ValueError(f"raw {expected_scope} report has unknown fields")
    required = {
        "schema_version",
        "scope",
        "program_id",
        "program_revision",
        "increment_id",
        "reviewer_role",
        "independent",
        "reduced_assurance",
        "persisted_at",
        "reconciled_at",
        "review_basis",
        "prior_conclusions_withheld",
        "findings",
    }
    missing = required.difference(value)
    if missing:
        raise ValueError(f"raw {expected_scope} report is missing required fields")
    if value.get("schema_version") != RAW_REVIEW_REPORT_SCHEMA:
        raise ValueError(f"raw {expected_scope} report has unsupported schema")
    if value.get("scope") != expected_scope:
        raise ValueError(f"raw report scope is not {expected_scope}")
    if not isinstance(value.get("findings"), list):
        raise ValueError(f"raw {expected_scope} report findings must be a list")
    if expected_scope == "architecture" and not isinstance(
        value.get("risk_predicates"), list
    ):
        raise ValueError("raw architecture report must classify every risk predicate")
    if expected_scope == "test-evidence":
        for field in (
            "test_first_evidence",
            "alternative_verification",
            "recovery_domains",
            "final_verification",
            "remediation_cycles",
        ):
            if field not in value:
                raise ValueError(f"raw test-evidence report is missing {field}")
    return value


def _tuple_strings(value: object, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, tuple)
        and (allow_empty or bool(value))
        and all(_nonempty(item) for item in value)
    )


def _parse_timestamp(value: object) -> datetime | None:
    if not _nonempty(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def select_review_scopes(
    predicates: Sequence[ReviewRiskPredicate],
) -> tuple[str, ...]:
    """Return required scopes followed by evidence-triggered specialist scopes."""
    issues: list[str] = []
    counts: dict[str, int] = {}
    by_name: dict[str, ReviewRiskPredicate] = {}
    for record in predicates:
        counts[record.predicate] = counts.get(record.predicate, 0) + 1
        by_name.setdefault(record.predicate, record)
        expected_scope = RISK_REVIEW_SCOPES.get(record.predicate)
        if expected_scope is None:
            issues.append(f"unknown risk predicate {record.predicate!r}")
        elif record.specialist_scope != expected_scope:
            issues.append(
                f"risk predicate {record.predicate!r} has the wrong specialist scope"
            )
        if type(record.touched) is not bool:
            issues.append(f"risk predicate {record.predicate!r} touched must be boolean")
        if not _nonempty(record.evidence):
            issues.append(f"risk predicate {record.predicate!r} needs evidence")
        if not _nonempty(record.rationale):
            issues.append(f"risk predicate {record.predicate!r} needs rationale")
    for predicate in RISK_REVIEW_SCOPES:
        if counts.get(predicate, 0) != 1:
            issues.append(f"risk predicate {predicate!r} must appear exactly once")
    if issues:
        raise ValueError("; ".join(sorted(set(issues))))
    selected = list(REQUIRED_REVIEW_SCOPES)
    for predicate, scope in RISK_REVIEW_SCOPES.items():
        if by_name[predicate].touched:
            selected.append(scope)
    return tuple(selected)


def validate_findings(findings: Sequence[ReviewFinding]) -> list[str]:
    """Require evidence-complete material findings and explicit dispositions."""
    issues: list[str] = []
    counts: dict[str, int] = {}
    for item in findings:
        label = item.finding_id or "<missing>"
        counts[item.finding_id] = counts.get(item.finding_id, 0) + 1
        for field in (
            "finding_id",
            "report_id",
            "scope",
            "summary",
            "affected_requirement_or_invariant",
            "severity",
            "inspection_path",
        ):
            if not _nonempty(getattr(item, field)):
                issues.append(f"finding {label!r} {field} must be non-empty")
        if _nonempty(item.finding_id) and _STABLE_IDENTIFIER.fullmatch(item.finding_id) is None:
            issues.append(f"finding {label!r} identifier is not stable")
        if item.classification not in FINDING_CLASSIFICATIONS:
            issues.append(f"finding {label!r} has unsupported classification")
        if not isinstance(item.confidence, str) or item.confidence not in FINDING_CONFIDENCE:
            issues.append(f"finding {label!r} confidence must be low, medium, or high")
        if item.disposition not in FINDING_DISPOSITIONS:
            issues.append(f"finding {label!r} has unsupported disposition")
        if item.severity not in {"low", "medium", "high", "critical"}:
            issues.append(f"finding {label!r} has unsupported severity")
        if item.classification == "material":
            for field in ("evidence", "impact", "confidence", "remediation", "disposition"):
                if not _nonempty(getattr(item, field)):
                    issues.append(f"material finding {label!r} {field} must be non-empty")
        elif item.disposition == "open":
            issues.append(f"non-material finding {label!r} cannot remain open")
        if item.disposition in {"accepted-risk", "deferred"} and (
            not _nonempty(item.decision_reference) or item.decision_reference == "none"
        ):
            issues.append(
                f"finding {label!r} accepted or deferred risk needs a decision reference"
            )
    for identifier, count in counts.items():
        if count > 1:
            issues.append(f"finding {identifier!r} is duplicated")
    return sorted(set(issues))


def validate_review_reports(
    reports: Sequence[ReviewReport],
    selected_scopes: Sequence[str],
    findings: Sequence[ReviewFinding],
) -> list[str]:
    """Validate distinct raw reports and truthful reviewer independence."""
    issues = validate_findings(findings)
    finding_by_id = {item.finding_id: item for item in findings}
    report_ids: set[str] = set()
    initial_counts = {scope: 0 for scope in selected_scopes}
    independent_roles: list[str] = []
    referenced_findings: set[str] = set()
    initial_candidates: set[str] = set()
    initial_paths: list[str] = []
    initial_digests: list[str] = []
    for item in reports:
        label = item.report_id or "<missing>"
        if not _nonempty(item.report_id) or _STABLE_IDENTIFIER.fullmatch(item.report_id) is None:
            issues.append(f"review report {label!r} identifier is not stable")
        elif item.report_id in report_ids:
            issues.append(f"review report {label!r} is duplicated")
        report_ids.add(item.report_id)
        for field in ("scope", "reviewer_role", "raw_report_path"):
            if not _nonempty(getattr(item, field)):
                issues.append(f"review report {label!r} {field} must be non-empty")
        if item.scope not in selected_scopes:
            issues.append(f"review report {label!r} has an unselected scope")
        if _SHA256.fullmatch(item.raw_report_sha256 or "") is None:
            issues.append(f"review report {label!r} raw report digest is invalid")
        if _SHA256.fullmatch(item.reviewed_candidate_sha256 or "") is None:
            issues.append(f"review report {label!r} reviewed candidate digest is invalid")
        persisted = _parse_timestamp(item.persisted_at)
        reconciled = _parse_timestamp(item.reconciled_at)
        if persisted is None or reconciled is None:
            issues.append(f"review report {label!r} timestamps must be timezone-aware")
        elif persisted >= reconciled:
            issues.append(f"review report {label!r} must be persisted before reconciliation")
        if type(item.independent) is not bool or type(item.reduced_assurance) is not bool:
            issues.append(f"review report {label!r} assurance flags must be boolean")
        elif item.reviewer_role == "controller-self-review" and item.independent:
            issues.append("controller self-review cannot claim independence")
        elif not item.independent and not item.reduced_assurance:
            issues.append(f"non-independent review report {label!r} needs reduced assurance")
        if type(item.prior_conclusions_withheld) is not bool:
            issues.append(f"review report {label!r} withheld-conclusions flag must be boolean")
        if item.independent:
            if not _nonempty(item.review_basis) or "bounded" not in item.review_basis.lower():
                issues.append(f"independent review report {label!r} needs a concrete bounded basis")
            if item.prior_conclusions_withheld is not True:
                issues.append(f"independent review report {label!r} needs withheld conclusions")
        else:
            if not _nonempty(item.review_basis):
                issues.append(f"non-independent review report {label!r} needs a truthful basis")
            if item.prior_conclusions_withheld is not False:
                issues.append(f"non-independent review report {label!r} cannot claim withheld conclusions")
        if item.independent and item.reviewer_role not in independent_roles:
            independent_roles.append(item.reviewer_role)
        if not _tuple_strings(item.finding_ids, allow_empty=True):
            issues.append(f"review report {label!r} finding ids must be immutable strings")
        if not _tuple_strings(item.follow_up_for_finding_ids, allow_empty=True):
            issues.append(f"review report {label!r} follow-up ids must be immutable strings")
        if not item.follow_up_for_finding_ids:
            if item.scope in initial_counts:
                initial_counts[item.scope] += 1
            initial_paths.append(item.raw_report_path)
            initial_digests.append(item.raw_report_sha256)
            if _SHA256.fullmatch(item.reviewed_candidate_sha256 or "") is not None:
                initial_candidates.add(item.reviewed_candidate_sha256)
        for finding_id in (*item.finding_ids, *item.follow_up_for_finding_ids):
            finding_item = finding_by_id.get(finding_id)
            if finding_item is None:
                issues.append(f"review report {label!r} references unknown finding {finding_id!r}")
                continue
            referenced_findings.add(finding_id)
            if finding_item.scope != item.scope:
                issues.append(f"review report {label!r} finding scope does not match")
        for finding_id in item.follow_up_for_finding_ids:
            finding_item = finding_by_id.get(finding_id)
            if finding_item is not None and finding_item.classification != "material":
                issues.append(f"review report {label!r} follow-up is not for a material finding")
    for scope, count in initial_counts.items():
        if count != 1:
            issues.append(f"selected scope {scope!r} must have exactly one initial report")
    if len(set(initial_paths)) != len(initial_paths):
        issues.append("initial reports must have distinct raw paths")
    if len(set(initial_digests)) != len(initial_digests):
        issues.append("initial reports must have distinct raw digests")
    if len(initial_candidates) != 1:
        issues.append("all initial review reports must bind one reviewed candidate digest")
    for item in findings:
        if item.finding_id not in referenced_findings:
            issues.append(f"finding {item.finding_id!r} is not linked from a review report")
        if item.report_id not in report_ids:
            issues.append(f"finding {item.finding_id!r} references an unknown report")
    if len(independent_roles) > 1:
        allowed_role = independent_roles[0]
        for item in reports:
            if item.independent and item.reviewer_role != allowed_role:
                material_follow_up = all(
                    finding_by_id.get(identifier) is not None
                    and finding_by_id[identifier].classification == "material"
                    for identifier in item.follow_up_for_finding_ids
                )
                if not item.follow_up_for_finding_ids or not material_follow_up:
                    issues.append(
                        "a second independent reviewer requires material-defect follow-up"
                    )
    return sorted(set(issues))


def validate_semantic_naming_review(
    expected_surfaces: Sequence[tuple[str, str]],
    dispositions: Sequence[SemanticNamingDisposition],
    findings: Sequence[ReviewFinding],
) -> list[str]:
    """Require contextual dispositions for every named implementation surface."""
    issues: list[str] = []
    expected = set(expected_surfaces)
    actual = {(item.surface, item.surface_kind) for item in dispositions}
    if len(expected) != len(tuple(expected_surfaces)) or len(actual) != len(dispositions):
        issues.append("semantic naming surface kind pairs must be unique")
    if expected != actual:
        issues.append(
            "semantic naming surface kind pairs do not match expected surfaces"
            f"; missing={sorted(expected.difference(actual))!r}"
            f"; extra={sorted(actual.difference(expected))!r}"
        )
    semantic_records = tuple(
        SemanticNameRecord(
            surface=item.surface,
            surface_kind=item.surface_kind,
            origin="new",
            context=item.context,
            intention=item.intention,
            planning_term_basis=item.planning_term_basis,
            basis_owner=item.basis_owner,
            compatibility_class=item.compatibility_class,
            compatibility_disposition=item.compatibility_disposition,
        )
        for item in dispositions
    )
    issues.extend(validate_semantic_naming_inventory(semantic_records))
    material_ids = {
        item.finding_id for item in findings if item.classification == "material"
    }
    for item in dispositions:
        if item.status not in SEMANTIC_STATUSES:
            issues.append(f"semantic naming surface {item.surface!r} has unknown status")
        elif item.status == "finding" and item.finding_id not in material_ids:
            issues.append(
                f"semantic naming surface {item.surface!r} needs a linked material finding"
            )
        elif item.status == "accepted" and item.finding_id != "none":
            issues.append(
                f"accepted semantic naming surface {item.surface!r} must not claim a finding"
            )
    return sorted(set(issues))


def validate_remediation_cycles(
    findings: Sequence[ReviewFinding],
    cycles: Sequence[RemediationCycle],
    reports: Sequence[ReviewReport],
) -> list[str]:
    """Require regression evidence, focused repair, and renewed affected review."""
    issues: list[str] = []
    finding_by_id = {item.finding_id: item for item in findings}
    report_by_id = {item.report_id: item for item in reports}
    cycle_ids: set[str] = set()
    covered: dict[str, int] = {}
    for cycle in cycles:
        label = cycle.cycle_id or "<missing>"
        if not _nonempty(cycle.cycle_id) or _STABLE_IDENTIFIER.fullmatch(cycle.cycle_id) is None:
            issues.append(f"remediation cycle {label!r} identifier is not stable")
        elif cycle.cycle_id in cycle_ids:
            issues.append(f"remediation cycle {label!r} is duplicated")
        cycle_ids.add(cycle.cycle_id)
        if not _tuple_strings(cycle.finding_ids):
            issues.append(f"remediation cycle {label!r} needs immutable finding ids")
        if not _tuple_strings(cycle.renewed_report_ids):
            issues.append(f"remediation cycle {label!r} needs renewed report ids")
        if not _tuple_strings(cycle.changed_paths):
            issues.append(f"remediation cycle {label!r} needs exact changed paths")
        if not _tuple_strings(cycle.affected_scopes):
            issues.append(f"remediation cycle {label!r} needs affected scopes")
        for field in (
            "regression_command",
            "intended_failure",
            "observed_failure",
            "repair",
            "verification_command",
            "verification_result",
        ):
            if not _nonempty(getattr(cycle, field)):
                issues.append(f"remediation cycle {label!r} {field} must be non-empty")
        started = _parse_timestamp(cycle.started_at)
        completed = _parse_timestamp(cycle.completed_at)
        if started is None or completed is None:
            issues.append(f"remediation cycle {label!r} timestamps must be timezone-aware")
        elif started >= completed:
            issues.append(f"remediation cycle {label!r} completion must follow its start")
        result = cycle.verification_result.lower()
        if not any(term in result for term in ("pass", "exit 0", "succeed")):
            issues.append(f"remediation cycle {label!r} verification did not pass")
        cycle_findings = set(cycle.finding_ids)
        expected_scopes: set[str] = set()
        for finding_id in cycle.finding_ids:
            covered[finding_id] = covered.get(finding_id, 0) + 1
            item = finding_by_id.get(finding_id)
            if item is None or item.classification != "material":
                issues.append(
                    f"remediation cycle {label!r} references a non-material or unknown finding"
                )
            else:
                expected_scopes.add(item.scope)
        if set(cycle.affected_scopes) != expected_scopes:
            issues.append(f"remediation cycle {label!r} affected scopes do not match findings")
        for report_id in cycle.renewed_report_ids:
            report_item = report_by_id.get(report_id)
            if report_item is None:
                issues.append(f"remediation cycle {label!r} references an unknown renewed report")
                continue
            if not cycle_findings.intersection(report_item.follow_up_for_finding_ids):
                issues.append(f"remediation cycle {label!r} renewed report is not affected")
            report_time = _parse_timestamp(report_item.persisted_at)
            if completed is not None and report_time is not None and report_time <= completed:
                issues.append(f"remediation cycle {label!r} renewed report must follow the repair")
    for item in findings:
        expected = item.classification == "material" and item.disposition == "repaired"
        count = covered.get(item.finding_id, 0)
        if expected and count != 1:
            issues.append(
                f"repaired material finding {item.finding_id!r} must have exactly one remediation cycle"
            )
        if not expected and count:
            issues.append(
                f"finding {item.finding_id!r} cannot have a completed remediation cycle"
            )
    return sorted(set(issues))


def _latest_timestamp(values: Sequence[str]) -> datetime | None:
    parsed = tuple(item for value in values if (item := _parse_timestamp(value)) is not None)
    return max(parsed) if parsed else None


def validate_final_verification(
    verification: FinalVerification,
    cycles: Sequence[RemediationCycle],
    reports: Sequence[ReviewReport],
) -> list[str]:
    """Require a successful verification receipt newer than repairs and review."""
    issues: list[str] = []
    if _SHA256.fullmatch(verification.candidate_sha256 or "") is None:
        issues.append("final verification candidate digest is invalid")
    verified_at = _parse_timestamp(verification.verified_at)
    if verified_at is None:
        issues.append("final verification timestamp must be timezone-aware")
    if not isinstance(verification.commands, tuple) or not verification.commands:
        issues.append("final verification commands must be a non-empty immutable sequence")
    if not _tuple_strings(verification.required_commands):
        issues.append("final verification required command set must be non-empty and immutable")
    if not _tuple_strings(verification.baseline_failures):
        issues.append("final verification baseline failures must be explicit and immutable")
    if not _tuple_strings(verification.verified_paths):
        issues.append("final verification paths must be a non-empty immutable sequence")
    elif len(set(verification.verified_paths)) != len(verification.verified_paths):
        issues.append("final verification paths are duplicated")
    if (
        not isinstance(verification.unresolved_material_findings, int)
        or isinstance(verification.unresolved_material_findings, bool)
        or verification.unresolved_material_findings != 0
    ):
        issues.append("final verification has unresolved material findings")
    latest_repair = _latest_timestamp(tuple(item.completed_at for item in cycles))
    latest_review = _latest_timestamp(tuple(item.reconciled_at for item in reports))
    threshold_candidates = tuple(
        item for item in (latest_repair, latest_review) if item is not None
    )
    freshness_threshold = max(threshold_candidates) if threshold_candidates else None
    seen_commands: set[str] = set()
    sensitive = re.compile(r"(?i)(?:password|token|secret|api[_-]?key)\s*[:=]")
    for item in verification.commands:
        if not _nonempty(item.command):
            issues.append("final verification command must be non-empty")
        elif item.command in seen_commands:
            issues.append(f"final verification command {item.command!r} is duplicated")
        seen_commands.add(item.command)
        if not isinstance(item.exit_code, int) or isinstance(item.exit_code, bool) or item.exit_code != 0:
            issues.append(f"final verification command {item.command!r} exit must be integer zero")
        if not _nonempty(item.result):
            issues.append(f"final verification command {item.command!r} result must be non-empty")
        elif sensitive.search(item.result):
            issues.append(f"final verification command {item.command!r} result contains sensitive data")
        if not _nonempty(item.expected_result):
            issues.append(f"final verification command {item.command!r} expected result must be non-empty")
        if not _tuple_strings(item.relevant_inputs):
            issues.append(f"final verification command {item.command!r} relevant inputs must be non-empty and immutable")
        completed = _parse_timestamp(item.completed_at)
        if completed is None:
            issues.append(f"final verification command {item.command!r} timestamp is invalid")
        else:
            if freshness_threshold is not None and completed <= freshness_threshold:
                issues.append("final verification commands must complete after remediation and review")
            if verified_at is not None and completed > verified_at:
                issues.append("final verification command completes after the receipt")
    if verified_at is not None and freshness_threshold is not None and verified_at <= freshness_threshold:
        issues.append("final verification receipt must be after remediation and review")
    if tuple(item.command for item in verification.commands) != verification.required_commands:
        issues.append("final verification observed commands do not match the required command set")
    return sorted(set(issues))


def _command_summaries(verification: FinalVerification) -> tuple[str, ...]:
    return tuple(
        f"{item.command} | exit {item.exit_code} | {item.result}"
        for item in verification.commands
    )


def _validate_packet_shape(packet: ReviewPacket) -> list[str]:
    issues: list[str] = []
    if packet.schema_version != REVIEW_PACKET_SCHEMA:
        issues.append("review packet has unsupported schema")
    if _SHA256.fullmatch(packet.candidate_sha256 or "") is None:
        issues.append("review packet candidate binding is invalid")
    for field in PACKET_FIELDS:
        if not _tuple_strings(getattr(packet, field)):
            issues.append(f"review packet canonical field {field!r} must be non-empty and immutable")
    return sorted(set(issues))


def validate_review_packet(
    packet: ReviewPacket,
    verification: FinalVerification,
    reports: Sequence[ReviewReport],
    findings: Sequence[ReviewFinding],
    cycles: Sequence[RemediationCycle],
) -> list[str]:
    """Cross-check all canonical packet fields against structured evidence."""
    issues = _validate_packet_shape(packet)
    if packet.candidate_sha256 != verification.candidate_sha256:
        issues.append("review packet candidate binding does not match final verification")
    if packet.exact_commands_and_results != _command_summaries(verification):
        issues.append("review packet exact commands and results do not match final verification")
    role_text = " ".join(packet.reviewer_roles_findings_dispositions).lower().replace("-", " ")
    if any(not item.independent for item in reports) and "non independent" not in role_text:
        issues.append("review packet omits non-independent reviewer status")
    if any(item.reduced_assurance for item in reports) and "reduced assurance" not in role_text:
        issues.append("review packet omits reduced assurance")
    for item in findings:
        if item.finding_id not in " ".join(packet.reviewer_roles_findings_dispositions):
            issues.append(f"review packet omits finding {item.finding_id!r}")
        if item.disposition not in " ".join(packet.reviewer_roles_findings_dispositions):
            issues.append(f"review packet omits finding disposition {item.disposition!r}")
    repair_text = " ".join(packet.repairs_and_renewed_verification)
    for cycle in cycles:
        if cycle.cycle_id not in repair_text:
            issues.append(f"review packet omits remediation cycle {cycle.cycle_id!r}")
    if packet.current_state_and_next_action and not any(
        "awaiting-diff-approval" in item for item in packet.current_state_and_next_action
    ):
        issues.append("review packet current state is not awaiting-diff-approval")
    return sorted(set(issues))


def render_review_packet(packet: ReviewPacket) -> str:
    """Render one validated packet data object in stable field order."""
    issues = _validate_packet_shape(packet)
    if issues:
        raise ValueError("; ".join(issues))
    sections = ["# Review Packet"]
    for field in PACKET_FIELDS:
        bullets = "\n".join(f"- {item}" for item in getattr(packet, field))
        sections.append(f"## {PACKET_HEADINGS[field]}\n\n{bullets}")
    return "\n\n".join(sections) + "\n"


def _tuple_fields(value: Mapping[str, object], fields: Sequence[str]) -> dict[str, object]:
    converted = dict(value)
    for field in fields:
        if isinstance(converted.get(field), list):
            converted[field] = tuple(converted[field])
    return converted


def validate_review_bundle(
    bundle: Mapping[str, object], packet_markdown: str
) -> list[str]:
    """Compose review, execution, recovery, verification, and packet validation."""
    issues: list[str] = []
    if bundle.get("schema_version") != REVIEW_EVIDENCE_SCHEMA:
        issues.append("review evidence has unsupported schema")
    unknown_fields = sorted(set(bundle).difference(BUNDLE_FIELDS))
    missing_fields = sorted(BUNDLE_FIELDS.difference(bundle))
    if unknown_fields:
        issues.append(f"review evidence has unknown fields: {unknown_fields!r}")
    if missing_fields:
        issues.append(f"review evidence is missing fields: {missing_fields!r}")
    try:
        predicates = tuple(ReviewRiskPredicate(**item) for item in bundle["risk_predicates"])
        reports = tuple(
            ReviewReport(**_tuple_fields(item, ("finding_ids", "follow_up_for_finding_ids")))
            for item in bundle["reports"]
        )
        findings = tuple(ReviewFinding(**item) for item in bundle["findings"])
        expected_surfaces = tuple(
            (item["surface"], item["surface_kind"])
            for item in bundle["semantic_surfaces"]
        )
        names = tuple(
            SemanticNamingDisposition(**item) for item in bundle["semantic_naming"]
        )
        cycles = tuple(
            RemediationCycle(
                **_tuple_fields(
                    item,
                    (
                        "finding_ids",
                        "renewed_report_ids",
                        "changed_paths",
                        "affected_scopes",
                    ),
                )
            )
            for item in bundle["remediation_cycles"]
        )
        test_first = tuple(
            TestFirstEvidence(**_tuple_fields(item, ("evidence_order",)))
            for item in bundle["test_first_evidence"]
        )
        alternatives = tuple(
            AlternativeVerificationContract(**_tuple_fields(item, ("relevant_inputs",)))
            for item in bundle["alternative_verification"]
        )
        recovery = tuple(RecoveryDomainPlan(**item) for item in bundle["recovery_domains"])
        verification_value = bundle["final_verification"]
        commands = tuple(
            CommandResult(**_tuple_fields(item, ("relevant_inputs",)))
            for item in verification_value["commands"]
        )
        verification = FinalVerification(
            **_tuple_fields(
                {**verification_value, "commands": commands},
                ("verified_paths", "required_commands", "baseline_failures"),
            )
        )
        packet_value = _tuple_fields(bundle["review_packet"], PACKET_FIELDS)
        packet = ReviewPacket(**packet_value)
    except (KeyError, TypeError, ValueError):
        issues.append("review bundle is structurally invalid")
        return sorted(set(issues))
    try:
        selected_scopes = select_review_scopes(predicates)
    except ValueError as error:
        issues.extend(str(error).split("; "))
        selected_scopes = ()
    issues.extend(validate_review_reports(reports, selected_scopes, findings))
    issues.extend(validate_semantic_naming_review(expected_surfaces, names, findings))
    issues.extend(validate_remediation_cycles(findings, cycles, reports))
    issues.extend(validate_execution_evidence(test_first, alternatives))
    issues.extend(validate_recovery_domains(recovery))
    issues.extend(validate_final_verification(verification, cycles, reports))
    follow_up_reports = tuple(item for item in reports if item.follow_up_for_finding_ids)
    final_reports = follow_up_reports if cycles else reports
    if {item.reviewed_candidate_sha256 for item in final_reports} != {
        verification.candidate_sha256
    }:
        issues.append("final review reports and final verification bind different candidates")
    issues.extend(validate_review_packet(packet, verification, reports, findings, cycles))
    try:
        rendered = render_review_packet(packet)
    except ValueError as error:
        issues.extend(str(error).split("; "))
    else:
        if rendered != packet_markdown:
            issues.append("persisted review packet does not equal deterministic rendering")
    return sorted(set(issues))


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _regular_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular non-symlink file")


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="review_coordination.py")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-bundle")
    validate.add_argument("evidence")
    validate.add_argument("--packet", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        arguments = parser.parse_args(argv)
    except ValueError as error:
        print(f"usage error: {error}")
        return 2
    if arguments.command != "validate-bundle":
        return 2
    evidence_path = Path(arguments.evidence)
    packet_path = Path(arguments.packet)
    try:
        _regular_file(evidence_path, "review evidence")
        _regular_file(packet_path, "review packet")
        bundle = json.loads(evidence_path.read_text(encoding="utf-8"))
        if not isinstance(bundle, dict):
            raise TypeError("review evidence must be a JSON object")
        packet_markdown = packet_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"usage error: {error}")
        return 2
    issues = validate_review_bundle(bundle, packet_markdown)
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("Review bundle validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
