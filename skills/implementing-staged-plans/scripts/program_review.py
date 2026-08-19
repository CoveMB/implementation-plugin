#!/usr/bin/env python3
"""Build, persist, and recover the current increment's review transaction."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from program_activation import (
    _canonical_json_bytes,
    _create_or_adopt_bytes,
    _identifier,
    _replace_or_adopt_status,
    _without_owned_program_paths,
)
from program_authority import load_json_object, resolve_managed_path, sha256_file
from repository_preparation import (
    _section_body,
    execution_baseline_from_value,
    inspect_repository,
    parse_exact_file_map,
    validate_execution_workspace,
)
from review_coordination import (
    PACKET_FIELDS,
    RAW_REVIEW_REPORT_SCHEMA,
    REVIEW_EVIDENCE_SCHEMA,
    REVIEW_PACKET_SCHEMA,
    CommandResult,
    FinalVerification,
    ReviewFinding,
    ReviewPacket,
    ReviewReport,
    ReviewRiskPredicate,
    load_raw_review_report,
    render_review_packet,
    select_review_scopes,
    validate_review_bundle,
    validate_review_reports,
)
from state_authority import (
    RepositoryObservation,
    TransitionRequest,
    apply_state_transition,
    atomic_replace_json,
    validate_state_authority,
)


REVIEW_PREPARATION_SCHEMA = "implementation-review-preparation/v1"
REVIEW_REMEDIATION_SCHEMA = "implementation-review-remediation/v1"


@dataclass(frozen=True)
class ReviewPreparationCandidate:
    evidence_bytes: bytes
    packet_bytes: bytes
    evidence_sha256: str
    packet_sha256: str
    verified_status_bytes: bytes
    awaiting_diff_status_bytes: bytes
    evidence_path: Path
    packet_path: Path
    verified_status: dict[str, object]
    awaiting_diff_status: dict[str, object]


@dataclass(frozen=True)
class ReviewPreparationReceipt:
    evidence_sha256: str
    packet_sha256: str
    increment_state: str
    status_sha256: str
    recovered: bool


@dataclass(frozen=True)
class ReviewRemediationCandidate:
    remediating_status: dict[str, object]
    remediating_status_bytes: bytes
    product_delta_sha256: str
    unresolved_finding_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReviewRemediationReceipt:
    increment_state: str
    status_sha256: str
    product_delta_sha256: str
    unresolved_finding_ids: tuple[str, ...]
    recovered: bool


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _resolve_increment_paths(
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
            require_file=key in {"plan", "baseline"},
        )
        if path is None:
            raise ValueError("; ".join(issues))
        result[key] = path
    return result


def _raw_report_paths(markdown: str) -> dict[str, str]:
    body = _section_body(markdown, "Review scopes and specialist predicates")
    matches = re.findall(
        r"^- (requirements|architecture|test-evidence): `([^`]+)`\s*$",
        body,
        flags=re.MULTILINE,
    )
    if tuple(scope for scope, _path in matches) != (
        "requirements",
        "architecture",
        "test-evidence",
    ):
        raise ValueError(
            "exact plan must name one ordered requirements, architecture, and test-evidence raw report"
        )
    paths = [path for _scope, path in matches]
    if len(set(paths)) != len(paths):
        raise ValueError("exact plan raw review report paths must be distinct")
    return dict(matches)


def _status_prior(
    status_path: Path, status: dict[str, object]
) -> tuple[str, int]:
    state = status.get("current_increment_state")
    if state == "reviewing":
        return sha256_file(status_path), int(status["state_sequence"])
    binding = status.get("review_preparation_binding")
    if (
        state not in {"verified", "awaiting-diff-approval"}
        or not isinstance(binding, dict)
    ):
        raise ValueError("review preparation requires reviewing or its exact persisted prefix")
    return str(binding["prior_status_sha256"]), int(binding["prior_status_sequence"])


def _load_current_report_inputs(
    workspace: Path,
    raw_paths: dict[str, str],
    candidate_sha256: str,
    program_id: str,
    program_revision: int,
    increment_id: str,
) -> tuple[
    dict[str, dict[str, object]],
    tuple[ReviewReport, ...],
    tuple[ReviewFinding, ...],
]:
    raw_values: dict[str, dict[str, object]] = {}
    reports: list[ReviewReport] = []
    findings: list[ReviewFinding] = []
    for scope in ("requirements", "architecture", "test-evidence"):
        relative = raw_paths[scope]
        path = workspace / relative
        value = load_raw_review_report(path, scope)
        if (
            value.get("program_id") != program_id
            or value.get("program_revision") != program_revision
            or value.get("increment_id") != increment_id
        ):
            raise ValueError(f"raw {scope} report is replayed from another program or increment")
        raw_values[scope] = value
        report_id = str(value.get("report_id", f"{scope}-initial"))
        follow_up_for_finding_ids = tuple(
            str(item) for item in value.get("follow_up_for_finding_ids", ())
        )
        scope_findings = [ReviewFinding(**item) for item in value["findings"]]
        if any(item.report_id != report_id or item.scope != scope for item in scope_findings):
            raise ValueError(f"raw {scope} findings do not bind their report")
        findings.extend(scope_findings)
        reports.append(
            ReviewReport(
                report_id=report_id,
                scope=scope,
                reviewer_role=str(value["reviewer_role"]),
                independent=value["independent"],
                reduced_assurance=value["reduced_assurance"],
                raw_report_path=relative,
                raw_report_sha256=sha256_file(path),
                persisted_at=str(value["persisted_at"]),
                reconciled_at=str(value["reconciled_at"]),
                finding_ids=tuple(item.finding_id for item in scope_findings),
                follow_up_for_finding_ids=follow_up_for_finding_ids,
                reviewed_candidate_sha256=candidate_sha256,
                review_basis=str(value["review_basis"]),
                prior_conclusions_withheld=value["prior_conclusions_withheld"],
            )
        )
    return raw_values, tuple(reports), tuple(findings)


def _stored_review_reports(value: object) -> tuple[ReviewReport, ...]:
    if not isinstance(value, list):
        raise ValueError("review remediation initial reports are invalid")
    try:
        return tuple(
            ReviewReport(
                **{
                    **item,
                    "finding_ids": tuple(item["finding_ids"]),
                    "follow_up_for_finding_ids": tuple(
                        item["follow_up_for_finding_ids"]
                    ),
                }
            )
            for item in value
            if isinstance(item, dict)
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("review remediation initial reports are invalid") from error


def _stored_review_findings(value: object) -> tuple[ReviewFinding, ...]:
    if not isinstance(value, list):
        raise ValueError("review remediation initial findings are invalid")
    try:
        return tuple(
            ReviewFinding(**item) for item in value if isinstance(item, dict)
        )
    except (TypeError, ValueError) as error:
        raise ValueError("review remediation initial findings are invalid") from error


def _reconciled_review_history(
    remediation_binding: dict[str, object] | None,
    current_reports: tuple[ReviewReport, ...],
    current_findings: tuple[ReviewFinding, ...],
) -> tuple[tuple[ReviewReport, ...], tuple[ReviewFinding, ...]]:
    if remediation_binding is None:
        return current_reports, current_findings
    if remediation_binding.get("schema_version") != REVIEW_REMEDIATION_SCHEMA:
        raise ValueError("review remediation binding has unsupported schema")
    initial_reports = _stored_review_reports(
        remediation_binding.get("initial_reports")
    )
    initial_findings = _stored_review_findings(
        remediation_binding.get("initial_findings")
    )
    unresolved_value = remediation_binding.get("unresolved_finding_ids")
    if not isinstance(unresolved_value, list) or not unresolved_value or not all(
        isinstance(item, str) and item for item in unresolved_value
    ):
        raise ValueError("review remediation unresolved finding ids are invalid")
    unresolved = set(unresolved_value)
    follow_up_reports = tuple(
        report for report in current_reports if report.follow_up_for_finding_ids
    )
    referenced = {
        finding_id
        for report in follow_up_reports
        for finding_id in report.follow_up_for_finding_ids
    }
    if not referenced.issubset(unresolved):
        raise ValueError("review follow-up references an unknown initial finding")
    findings_by_id = {finding.finding_id: finding for finding in initial_findings}
    if not unresolved.issubset(findings_by_id):
        raise ValueError("review remediation initial findings are incomplete")
    follow_up_report_ids = {report.report_id for report in follow_up_reports}
    replacements: dict[str, ReviewFinding] = {}
    for finding in current_findings:
        if finding.finding_id not in referenced:
            if finding.report_id in follow_up_report_ids:
                raise ValueError(
                    "review follow-up report declares an unreferenced finding"
                )
            continue
        if (
            finding.report_id not in follow_up_report_ids
            or finding.disposition != "repaired"
        ):
            raise ValueError("review follow-up must record a repaired finding")
        if finding.finding_id in replacements:
            raise ValueError("review follow-up finding is duplicated")
        initial = findings_by_id[finding.finding_id]
        if initial.classification != "material" or initial.disposition != "open":
            raise ValueError("review remediation initial finding is not open material")
        expected_follow_up = replace(
            initial,
            report_id=finding.report_id,
            disposition="repaired",
        )
        if finding != expected_follow_up:
            raise ValueError(
                "review follow-up does not match initial finding"
            )
        replacements[finding.finding_id] = replace(
            initial, disposition="repaired"
        )
    if set(replacements) != unresolved:
        raise ValueError("initial material findings lack repaired follow-up")
    findings_by_id.update(replacements)
    return (
        (*initial_reports, *follow_up_reports),
        tuple(findings_by_id[key] for key in sorted(findings_by_id)),
    )


def _build_report_bundle(
    workspace: Path,
    raw_paths: dict[str, str],
    candidate_sha256: str,
    product_paths: tuple[str, ...],
    program_id: str,
    program_revision: int,
    increment_id: str,
    remediation_binding: dict[str, object] | None = None,
) -> tuple[dict[str, object], ReviewPacket]:
    raw_values, current_reports, current_findings = _load_current_report_inputs(
        workspace,
        raw_paths,
        candidate_sha256,
        program_id,
        program_revision,
        increment_id,
    )
    reports, findings = _reconciled_review_history(
        remediation_binding, current_reports, current_findings
    )

    architecture = raw_values["architecture"]
    predicates = [ReviewRiskPredicate(**item) for item in architecture["risk_predicates"]]
    test_evidence = raw_values["test-evidence"]
    final_value = test_evidence["final_verification"]
    if not isinstance(final_value, dict):
        raise ValueError("raw test-evidence final_verification must be an object")
    commands = tuple(CommandResult(**item) for item in final_value.get("commands", []))
    unresolved = sum(
        item.classification == "material" and item.disposition == "open"
        for item in findings
    )
    verification = FinalVerification(
        candidate_sha256=candidate_sha256,
        verified_at=str(final_value.get("verified_at", "")),
        commands=commands,
        unresolved_material_findings=unresolved,
        verified_paths=product_paths,
        required_commands=tuple(final_value.get("required_commands", ())),
        baseline_failures=tuple(final_value.get("baseline_failures", ())),
    )
    names = [
        {
            "surface": path,
            "surface_kind": "path",
            "context": "status-current reviewed product delta",
            "intention": "deliver one exact-plan-declared changed path",
            "planning_term_basis": "none",
            "basis_owner": "none",
            "compatibility_class": "private",
            "compatibility_disposition": "exact-plan-declared change",
            "status": "accepted",
            "finding_id": "none",
        }
        for path in product_paths
    ]
    finding_lines = (
        tuple(f"{item.finding_id}: {item.disposition}" for item in findings)
        or ("no material findings",)
    )
    command_lines = tuple(
        f"{item.command} | exit {item.exit_code} | {item.result}"
        for item in commands
    )
    report_roles = tuple(
        f"{item.report_id}: {item.reviewer_role}; "
        f"{'independent' if item.independent else 'non-independent'}; "
        f"{'reduced assurance' if item.reduced_assurance else 'full assurance'}"
        for item in reports
    )
    packet = ReviewPacket(
        schema_version=REVIEW_PACKET_SCHEMA,
        candidate_sha256=candidate_sha256,
        identity_and_outcome=(f"reviewed candidate {candidate_sha256}",),
        changes_and_rationale=tuple(f"reviewed {path}" for path in product_paths),
        program_context=("status-current first-increment review transaction",),
        changed_files_by_purpose=tuple(
            f"{path}: exact-plan-declared product or review input" for path in product_paths
        ),
        human_review_order=("requirements", "architecture", "test-evidence"),
        requirements_and_acceptance=("all required raw review scopes reconciled",),
        exact_commands_and_results=command_lines,
        baseline_failures=tuple(final_value.get("baseline_failures", ())),
        execution_evidence=("raw test evidence is preserved in the review evidence",),
        reviewer_roles_findings_dispositions=(*report_roles, *finding_lines),
        repairs_and_renewed_verification=(
            "none"
            if not test_evidence["remediation_cycles"]
            else "; ".join(
                str(item.get("cycle_id"))
                for item in test_evidence["remediation_cycles"]
            ),
        ),
        deviations_and_amendments=("none recorded",),
        human_judgment=("review identity and quality remain human judgments",),
        edge_cases_and_manual_checks=("raw paths, digests, findings, and verification were validated",),
        implications=("local deterministic evidence does not prove external behavior",),
        residual_risks_and_deferred_work=("independent review is not claimed",),
        recovery=("preserve exact prefixes and retry only identical bytes",),
        workspace_and_logical_boundaries=("no staging, commit, or external action is authorized",),
        current_state_and_next_action=(
            "awaiting-diff-approval; present the exact diff disposition prompt",
        ),
    )
    bundle = {
        "schema_version": REVIEW_EVIDENCE_SCHEMA,
        "risk_predicates": [asdict(item) for item in predicates],
        "reports": [asdict(item) for item in reports],
        "findings": [asdict(item) for item in findings],
        "semantic_surfaces": [
            {"surface": path, "surface_kind": "path"} for path in product_paths
        ],
        "semantic_naming": names,
        "remediation_cycles": test_evidence["remediation_cycles"],
        "test_first_evidence": test_evidence["test_first_evidence"],
        "alternative_verification": test_evidence["alternative_verification"],
        "recovery_domains": test_evidence["recovery_domains"],
        "final_verification": asdict(verification),
        "review_packet": asdict(packet),
    }
    return bundle, packet


def _review_transaction_context(
    program_root: Path,
    observation: RepositoryObservation,
    *,
    assessment_state: str | None,
) -> tuple[
    RepositoryObservation,
    dict[str, object],
    dict[str, object],
    Path,
    dict[str, Path],
    dict[str, str],
    object,
]:
    root = Path(program_root)
    fresh = inspect_repository(Path(observation.path), observation.base_commit)
    normalized = _without_owned_program_paths(root, fresh.observation)
    if asdict(normalized) != asdict(
        _without_owned_program_paths(root, observation)
    ):
        raise ValueError("workspace observation changed before review transaction")
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
    increment_id = str(status["current_increment_id"])
    paths = _resolve_increment_paths(root, manifest, increment_id)
    plan_markdown = paths["plan"].read_text(encoding="utf-8")
    file_map = parse_exact_file_map(plan_markdown)
    workspace = Path(normalized.path)
    evidence_relative = paths["evidence"].resolve(strict=False).relative_to(
        workspace.resolve()
    ).as_posix()
    packet_relative = paths["packet"].resolve(strict=False).relative_to(
        workspace.resolve()
    ).as_posix()
    if evidence_relative not in file_map.create or packet_relative not in file_map.create:
        raise ValueError("review evidence and packet require exact-plan Create allocation")
    raw_paths = _raw_report_paths(plan_markdown)
    undeclared = sorted(set(raw_paths.values()).difference(file_map.create))
    if undeclared:
        raise ValueError(
            "raw review report is not declared by the exact plan: "
            + ", ".join(undeclared)
        )
    baseline_value, baseline_issues = load_json_object(paths["baseline"])
    if baseline_value is None:
        raise ValueError("; ".join(baseline_issues))
    baseline = execution_baseline_from_value(baseline_value)
    effective_assessment_state = assessment_state or str(
        status["current_increment_state"]
    )
    assessment = validate_execution_workspace(
        root,
        baseline,
        replace(fresh, observation=normalized),
        increment_state=effective_assessment_state,
    )
    if not assessment.valid:
        raise ValueError("; ".join(assessment.issues))
    return (
        normalized,
        manifest,
        status,
        status_path,
        paths,
        raw_paths,
        assessment,
    )


def build_review_remediation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewRemediationCandidate:
    """Build a typed status-only transition for unresolved material findings."""
    root = Path(program_root)
    (
        normalized,
        _manifest,
        status,
        status_path,
        _paths,
        raw_paths,
        assessment,
    ) = _review_transaction_context(
        root,
        observation,
        assessment_state=None,
    )
    state = status.get("current_increment_state")
    if state == "remediating":
        binding = status.get("review_remediation_binding")
        initial_product_delta_sha256 = (
            binding.get("initial_product_delta_sha256")
            if isinstance(binding, dict)
            else None
        )
        if (
            not isinstance(binding, dict)
            or binding.get("schema_version") != REVIEW_REMEDIATION_SCHEMA
            or not isinstance(binding.get("unresolved_finding_ids"), list)
            or not isinstance(initial_product_delta_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", initial_product_delta_sha256)
            is None
        ):
            raise ValueError("review-remediation-recovery-required: status binding differs")
        state_issues = validate_state_authority(root, normalized)
        if state_issues:
            raise ValueError("; ".join(state_issues))
        return ReviewRemediationCandidate(
            remediating_status=status,
            remediating_status_bytes=_canonical_json_bytes(status),
            product_delta_sha256=initial_product_delta_sha256,
            unresolved_finding_ids=tuple(binding["unresolved_finding_ids"]),
        )
    if state != "reviewing":
        raise ValueError("review remediation requires reviewing status")
    state_issues = validate_state_authority(root, normalized)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    transition = status.get("execution_transition_binding")
    if (
        not isinstance(transition, dict)
        or transition.get("target_increment_state") != "reviewing"
        or transition.get("product_delta_sha256")
        != assessment.product_delta_sha256
    ):
        raise ValueError("review product delta does not match reviewing status")
    workspace = Path(normalized.path)
    raw_values, reports, findings = _load_current_report_inputs(
        workspace,
        raw_paths,
        assessment.product_delta_sha256,
        str(status["program_id"]),
        int(status["program_revision"]),
        str(status["current_increment_id"]),
    )
    if any(report.follow_up_for_finding_ids for report in reports):
        raise ValueError("initial review remediation requires initial reports")
    predicates = tuple(
        ReviewRiskPredicate(**item)
        for item in raw_values["architecture"]["risk_predicates"]
    )
    try:
        selected_scopes = select_review_scopes(predicates)
    except ValueError as error:
        raise ValueError(str(error)) from error
    report_issues = validate_review_reports(reports, selected_scopes, findings)
    if report_issues:
        raise ValueError("; ".join(report_issues))
    unresolved = tuple(
        sorted(
            finding.finding_id
            for finding in findings
            if finding.classification == "material"
            and finding.disposition == "open"
        )
    )
    if not unresolved:
        raise ValueError("review remediation requires open material findings")
    prior_sha256 = sha256_file(status_path)
    prior_sequence = int(status["state_sequence"])
    raw_bindings = [
        {
            "scope": report.scope,
            "path": report.raw_report_path,
            "sha256": report.raw_report_sha256,
        }
        for report in reports
    ]
    binding = {
        "schema_version": REVIEW_REMEDIATION_SCHEMA,
        "prior_status_sha256": prior_sha256,
        "prior_status_sequence": prior_sequence,
        "initial_product_delta_sha256": assessment.product_delta_sha256,
        "initial_reports": [asdict(report) for report in reports],
        "initial_findings": [asdict(finding) for finding in findings],
        "raw_report_bindings": raw_bindings,
        "unresolved_finding_ids": list(unresolved),
    }
    authorization_id = status["execution_authorization"]["authorization_id"]
    event_id = _identifier("review-remediation", binding)
    remediating = dict(status)
    remediating.update(
        state_sequence=prior_sequence + 1,
        current_increment_state="remediating",
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": prior_sequence,
            "status_sha256": prior_sha256,
        },
        transition_authority={
            "kind": "action-authorization",
            "event_id": event_id,
            "authorization_id": authorization_id,
        },
        review_binding={
            "schema_version": REVIEW_REMEDIATION_SCHEMA,
            "candidate_sha256": assessment.product_delta_sha256,
            "unresolved_material_findings": len(unresolved),
            "finding_ids": list(unresolved),
        },
        review_remediation_binding=binding,
    )
    return ReviewRemediationCandidate(
        remediating_status=remediating,
        remediating_status_bytes=_canonical_json_bytes(remediating),
        product_delta_sha256=assessment.product_delta_sha256,
        unresolved_finding_ids=unresolved,
    )


def persist_review_remediation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewRemediationReceipt:
    """Persist or adopt the typed reviewing-to-remediating status."""
    root = Path(program_root)
    candidate = build_review_remediation(root, observation)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    status_path, status_path_issues = resolve_managed_path(
        root,
        manifest["logical_roles"]["status"],
        role="logical role status",
    )
    if status_path is None:
        raise ValueError("; ".join(status_path_issues))
    binding = candidate.remediating_status["review_remediation_binding"]
    recovered = _replace_or_adopt_status(
        status_path,
        candidate.remediating_status,
        str(binding["prior_status_sha256"]),
        "review-remediation",
    )
    _after_persist("remediating-status")
    return ReviewRemediationReceipt(
        increment_state="remediating",
        status_sha256=sha256_file(status_path),
        product_delta_sha256=candidate.product_delta_sha256,
        unresolved_finding_ids=candidate.unresolved_finding_ids,
        recovered=recovered,
    )


def return_review_to_reviewing(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewRemediationReceipt:
    """Validate repaired evidence and refreeze the candidate in reviewing."""
    root = Path(program_root)
    (
        normalized,
        _manifest,
        status,
        status_path,
        _paths,
        raw_paths,
        assessment,
    ) = _review_transaction_context(
        root, observation, assessment_state="reviewing"
    )
    binding = status.get("review_remediation_binding")
    if not isinstance(binding, dict) or binding.get(
        "schema_version"
    ) != REVIEW_REMEDIATION_SCHEMA:
        raise ValueError("review remediation binding is required")
    unresolved = tuple(str(item) for item in binding["unresolved_finding_ids"])
    state = status.get("current_increment_state")
    transition = status.get("execution_transition_binding")
    if (
        state == "reviewing"
        and isinstance(transition, dict)
        and transition.get("prior_increment_state") == "remediating"
        and transition.get("product_delta_sha256")
        == assessment.product_delta_sha256
    ):
        state_issues = validate_state_authority(root, normalized)
        if state_issues:
            raise ValueError("; ".join(state_issues))
        return ReviewRemediationReceipt(
            increment_state="reviewing",
            status_sha256=sha256_file(status_path),
            product_delta_sha256=assessment.product_delta_sha256,
            unresolved_finding_ids=unresolved,
            recovered=True,
        )
    if state != "remediating":
        raise ValueError("review return requires remediating status")
    state_issues = validate_state_authority(root, normalized)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    product_paths = tuple(str(item["path"]) for item in assessment.product_delta)
    bundle, packet = _build_report_bundle(
        Path(normalized.path),
        raw_paths,
        assessment.product_delta_sha256,
        product_paths,
        str(status["program_id"]),
        int(status["program_revision"]),
        str(status["current_increment_id"]),
        binding,
    )
    packet_text = render_review_packet(packet)
    review_issues = validate_review_bundle(bundle, packet_text)
    if review_issues:
        raise ValueError("; ".join(review_issues))
    authorization_id = status["execution_authorization"]["authorization_id"]
    prior_sha256 = sha256_file(status_path)
    prior_sequence = int(status["state_sequence"])
    remediation_sha256 = _sha256_bytes(_canonical_json_bytes(binding))
    event_seed = {
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "increment_id": status["current_increment_id"],
        "prior_status_sha256": prior_sha256,
        "prior_increment_state": "remediating",
        "target_increment_state": "reviewing",
        "product_delta_sha256": assessment.product_delta_sha256,
        "authorization_id": authorization_id,
        "review_remediation_sha256": remediation_sha256,
    }
    event_id = _identifier("execution-transition", event_seed)
    reviewing = dict(status)
    reviewing.update(
        state_sequence=prior_sequence + 1,
        current_increment_state="reviewing",
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": prior_sequence,
            "status_sha256": prior_sha256,
        },
        transition_authority={
            "kind": "action-authorization",
            "event_id": event_id,
            "authorization_id": authorization_id,
        },
        execution_transition_binding={
            "schema_version": "implementation-execution-transition/v1",
            "event_id": event_id,
            "authorization_id": authorization_id,
            "prior_increment_state": "remediating",
            "target_increment_state": "reviewing",
            "prior_status_sha256": prior_sha256,
            "product_delta_sha256": assessment.product_delta_sha256,
            "review_remediation_sha256": remediation_sha256,
        },
        review_binding={
            "schema_version": REVIEW_REMEDIATION_SCHEMA,
            "candidate_sha256": assessment.product_delta_sha256,
            "unresolved_material_findings": 0,
            "finding_ids": list(unresolved),
        },
    )
    atomic_replace_json(status_path, reviewing, prior_sha256)
    _after_persist("reviewing-after-remediation-status")
    final_issues = validate_state_authority(root, normalized)
    if final_issues:
        raise ValueError("; ".join(final_issues))
    return ReviewRemediationReceipt(
        increment_state="reviewing",
        status_sha256=sha256_file(status_path),
        product_delta_sha256=assessment.product_delta_sha256,
        unresolved_finding_ids=unresolved,
        recovered=False,
    )


def build_review_preparation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewPreparationCandidate:
    """Build and validate the complete current review transaction in memory."""
    root = Path(program_root)
    fresh = inspect_repository(Path(observation.path), observation.base_commit)
    normalized = _without_owned_program_paths(root, fresh.observation)
    if asdict(normalized) != asdict(
        _without_owned_program_paths(root, observation)
    ):
        raise ValueError("workspace observation changed before review preparation")
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
    prior_sha256, prior_sequence = _status_prior(status_path, status)
    state_issues = validate_state_authority(root, normalized)
    if state_issues:
        raise ValueError("; ".join(state_issues))
    increment_id = str(status["current_increment_id"])
    paths = _resolve_increment_paths(root, manifest, increment_id)
    plan_markdown = paths["plan"].read_text(encoding="utf-8")
    file_map = parse_exact_file_map(plan_markdown)
    workspace = Path(normalized.path)
    evidence_relative = paths["evidence"].resolve(strict=False).relative_to(
        workspace.resolve()
    ).as_posix()
    packet_relative = paths["packet"].resolve(strict=False).relative_to(
        workspace.resolve()
    ).as_posix()
    if evidence_relative not in file_map.create or packet_relative not in file_map.create:
        raise ValueError("review evidence and packet require exact-plan Create allocation")
    raw_paths = _raw_report_paths(plan_markdown)
    undeclared = sorted(set(raw_paths.values()).difference(file_map.create))
    if undeclared:
        raise ValueError("raw review report is not declared by the exact plan: " + ", ".join(undeclared))

    baseline_value, baseline_issues = load_json_object(paths["baseline"])
    if baseline_value is None:
        raise ValueError("; ".join(baseline_issues))
    baseline = execution_baseline_from_value(baseline_value)
    assessment = validate_execution_workspace(
        root,
        baseline,
        replace(fresh, observation=normalized),
        increment_state="reviewing",
    )
    if not assessment.valid:
        raise ValueError("; ".join(assessment.issues))
    transition = status.get("execution_transition_binding")
    if (
        not isinstance(transition, dict)
        or transition.get("target_increment_state") != "reviewing"
        or transition.get("product_delta_sha256") != assessment.product_delta_sha256
    ):
        raise ValueError("review product delta does not match reviewing status")
    product_paths = tuple(str(item["path"]) for item in assessment.product_delta)
    bundle, packet = _build_report_bundle(
        workspace,
        raw_paths,
        assessment.product_delta_sha256,
        product_paths,
        str(status["program_id"]),
        int(status["program_revision"]),
        increment_id,
        (
            status["review_remediation_binding"]
            if isinstance(status.get("review_remediation_binding"), dict)
            else None
        ),
    )
    packet_text = render_review_packet(packet)
    review_issues = validate_review_bundle(bundle, packet_text)
    if review_issues:
        raise ValueError("; ".join(review_issues))
    evidence_bytes = _canonical_json_bytes(bundle)
    packet_bytes = packet_text.encode("utf-8")
    evidence_sha256 = _sha256_bytes(evidence_bytes)
    packet_sha256 = _sha256_bytes(packet_bytes)
    seed = {
        "schema_version": REVIEW_PREPARATION_SCHEMA,
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "increment_id": increment_id,
        "prior_status_sha256": prior_sha256,
        "prior_status_sequence": prior_sequence,
        "product_delta_sha256": assessment.product_delta_sha256,
        "evidence_sha256": evidence_sha256,
        "packet_sha256": packet_sha256,
    }
    binding = {
        **seed,
        "evidence_path": paths["evidence"].relative_to(root).as_posix(),
        "packet_path": paths["packet"].relative_to(root).as_posix(),
    }
    authorization_id = status["execution_authorization"]["authorization_id"]
    verified_event = _identifier("review-verified", seed)
    verified = dict(status)
    verified.update(
        state_sequence=prior_sequence + 1,
        current_increment_state="verified",
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": prior_sequence,
            "status_sha256": prior_sha256,
        },
        transition_authority={
            "kind": "action-authorization",
            "event_id": verified_event,
            "authorization_id": authorization_id,
        },
        review_preparation_binding=binding,
        review_evidence_binding={
            "path": binding["evidence_path"],
            "sha256": evidence_sha256,
            "candidate_sha256": assessment.product_delta_sha256,
        },
        review_packet_binding={
            "path": binding["packet_path"],
            "sha256": packet_sha256,
            "candidate_sha256": assessment.product_delta_sha256,
        },
    )
    verified_bytes = _canonical_json_bytes(verified)
    awaiting_event = _identifier(
        "awaiting-diff", {**seed, "verified_status_sha256": _sha256_bytes(verified_bytes)}
    )
    awaiting = dict(verified)
    awaiting.update(
        state_sequence=prior_sequence + 2,
        current_increment_state="awaiting-diff-approval",
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": prior_sequence + 1,
            "status_sha256": _sha256_bytes(verified_bytes),
        },
        transition_authority={
            "kind": "action-authorization",
            "event_id": awaiting_event,
            "authorization_id": authorization_id,
        },
    )
    awaiting_bytes = _canonical_json_bytes(awaiting)
    return ReviewPreparationCandidate(
        evidence_bytes=evidence_bytes,
        packet_bytes=packet_bytes,
        evidence_sha256=evidence_sha256,
        packet_sha256=packet_sha256,
        verified_status_bytes=verified_bytes,
        awaiting_diff_status_bytes=awaiting_bytes,
        evidence_path=paths["evidence"],
        packet_path=paths["packet"],
        verified_status=verified,
        awaiting_diff_status=awaiting,
    )


def _after_persist(_label: str) -> None:
    """Test seam after one durable review transaction prefix."""


def persist_review_preparation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewPreparationReceipt:
    """Create/adopt review files, then persist verified and diff-gate status."""
    root = Path(program_root)
    candidate = build_review_preparation(root, observation)
    recovered = _create_or_adopt_bytes(
        candidate.evidence_path, candidate.evidence_bytes, "review-preparation"
    )
    _after_persist("review-evidence")
    recovered = (
        _create_or_adopt_bytes(
            candidate.packet_path, candidate.packet_bytes, "review-preparation"
        )
        or recovered
    )
    _after_persist("review-packet")
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    roles = manifest["logical_roles"]
    status_path, status_path_issues = resolve_managed_path(
        root, roles["status"], role="logical role status"
    )
    if status_path is None:
        raise ValueError("; ".join(status_path_issues))
    binding = candidate.verified_status["review_preparation_binding"]
    verified_sha256 = _sha256_bytes(candidate.verified_status_bytes)
    awaiting_sha256 = _sha256_bytes(candidate.awaiting_diff_status_bytes)
    current = status_path.read_bytes()
    if current == candidate.awaiting_diff_status_bytes:
        recovered = True
    else:
        if current != candidate.verified_status_bytes:
            atomic_replace_json(
                status_path,
                candidate.verified_status,
                str(binding["prior_status_sha256"]),
            )
            _after_persist("verified-status")
        else:
            recovered = True
        refreshed = build_review_preparation(root, observation)
        if refreshed.awaiting_diff_status_bytes != candidate.awaiting_diff_status_bytes:
            raise ValueError("review-preparation-recovery-required: refreshed candidate differs")
        _replace_or_adopt_status(
            status_path,
            candidate.awaiting_diff_status,
            verified_sha256,
            "review-preparation",
        )
        _after_persist("awaiting-diff-status")
    final_issues = validate_state_authority(
        root,
        _without_owned_program_paths(
            root,
            inspect_repository(Path(observation.path), observation.base_commit).observation,
        ),
    )
    if final_issues:
        raise ValueError("; ".join(final_issues))
    return ReviewPreparationReceipt(
        evidence_sha256=candidate.evidence_sha256,
        packet_sha256=candidate.packet_sha256,
        increment_state="awaiting-diff-approval",
        status_sha256=awaiting_sha256,
        recovered=recovered,
    )
