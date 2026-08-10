import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "review_coordination.py"
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "tests/fixtures/review-coordination/portable-archive-run"
)
FIXTURE_EVIDENCE = FIXTURE_ROOT / "review-evidence.json"
FIXTURE_PACKET = FIXTURE_ROOT / "review-packet.md"

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC = importlib.util.spec_from_file_location("review_coordination", SCRIPT_PATH)
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load review coordination from {SCRIPT_PATH}")
    REVIEW = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = REVIEW
    SPEC.loader.exec_module(REVIEW)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def risk_predicates(**overrides):
    touched = {
        "security-privacy": True,
        "public-api-compatibility": True,
        "concurrency-reliability-distributed-state": True,
    }
    scopes = {
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
    records = []
    for predicate, scope in scopes.items():
        values = {
            "predicate": predicate,
            "touched": touched.get(predicate, False),
            "specialist_scope": scope,
            "evidence": f"bounded evidence for {predicate}",
            "rationale": "review when touched" if touched.get(predicate, False) else "not touched by this change",
        }
        values.update(overrides.get(predicate, {}))
        records.append(REVIEW.ReviewRiskPredicate(**values))
    return tuple(records)


def finding(**overrides):
    values = {
        "finding_id": "F-001",
        "report_id": "requirements-initial",
        "scope": "requirements",
        "classification": "material",
        "summary": "stale evidence could be accepted",
        "evidence": "verification timestamp precedes the repair timestamp",
        "impact": "a repaired candidate could retain pre-repair verification",
        "confidence": "high",
        "remediation": "require every final command to complete after repair",
        "disposition": "repaired",
    }
    if "affected_requirement_or_invariant" in REVIEW.ReviewFinding.__dataclass_fields__:
        values.update(
            affected_requirement_or_invariant="fresh evidence invariant",
            severity="high",
            inspection_path="compare verification and repair timestamps",
            decision_reference="none",
        )
    values.update(overrides)
    return REVIEW.ReviewFinding(**values)


def report(scope="requirements", **overrides):
    values = {
        "report_id": f"{scope}-initial",
        "scope": scope,
        "reviewer_role": "controller-self-review",
        "independent": False,
        "reduced_assurance": True,
        "raw_report_path": f"reviews/{scope}.md",
        "raw_report_sha256": {
            "requirements": "a" * 64,
            "architecture": "b" * 64,
            "test-evidence": "c" * 64,
        }.get(scope, "d" * 64),
        "persisted_at": "2026-08-09T10:00:00Z",
        "reconciled_at": "2026-08-09T11:00:00Z",
        "finding_ids": (),
        "follow_up_for_finding_ids": (),
    }
    if "reviewed_candidate_sha256" in REVIEW.ReviewReport.__dataclass_fields__:
        values.update(
            reviewed_candidate_sha256="b" * 64,
            review_basis="controller self-review without dispatch",
            prior_conclusions_withheld=False,
        )
    values.update(overrides)
    return REVIEW.ReviewReport(**values)


def required_reports(**overrides):
    return tuple(
        report(scope, **overrides)
        for scope in ("requirements", "architecture", "test-evidence")
    )


def semantic_disposition(**overrides):
    values = {
        "surface": "ReviewReport",
        "surface_kind": "symbol",
        "context": "review evidence validation",
        "intention": "represent one raw review report",
        "planning_term_basis": "none",
        "basis_owner": "none",
        "compatibility_class": "private",
        "compatibility_disposition": "new internal surface",
        "status": "accepted",
        "finding_id": "none",
    }
    values.update(overrides)
    return REVIEW.SemanticNamingDisposition(**values)


def remediation_cycle(**overrides):
    values = {
        "cycle_id": "repair-stale-evidence",
        "finding_ids": ("F-001",),
        "started_at": "2026-08-09T11:10:00Z",
        "completed_at": "2026-08-09T11:20:00Z",
        "regression_command": "python3 -m unittest tests.test_review_coordination.FinalVerificationTests",
        "intended_failure": "pre-repair success is rejected",
        "observed_failure": "pre-repair success was accepted",
        "repair": "compare every command completion with the latest repair",
        "verification_command": "python3 -m unittest tests.test_review_coordination.FinalVerificationTests",
        "verification_result": "tests passed",
        "renewed_report_ids": ("requirements-follow-up",),
    }
    if "changed_paths" in REVIEW.RemediationCycle.__dataclass_fields__:
        values.update(
            changed_paths=("skills/implementing-staged-plans/scripts/review_coordination.py",),
            affected_scopes=("requirements",),
        )
    values.update(overrides)
    return REVIEW.RemediationCycle(**values)


def command_result(**overrides):
    values = {
        "command": "python3 -m unittest tests.test_review_coordination",
        "exit_code": 0,
        "result": "24 tests passed",
        "completed_at": "2026-08-09T12:00:00Z",
    }
    if "expected_result" in REVIEW.CommandResult.__dataclass_fields__:
        values.update(
            expected_result="exit zero with focused tests passing",
            relevant_inputs=("tests/test_review_coordination.py",),
        )
    values.update(overrides)
    return REVIEW.CommandResult(**values)


def final_verification(**overrides):
    values = {
        "candidate_sha256": "b" * 64,
        "verified_at": "2026-08-09T12:05:00Z",
        "commands": (command_result(),),
        "unresolved_material_findings": 0,
        "verified_paths": (
            "skills/implementing-staged-plans/scripts/review_coordination.py",
            "tests/test_review_coordination.py",
        ),
    }
    if "required_commands" in REVIEW.FinalVerification.__dataclass_fields__:
        values.update(
            required_commands=("python3 -m unittest tests.test_review_coordination",),
            baseline_failures=("none",),
        )
    values.update(overrides)
    return REVIEW.FinalVerification(**values)


PACKET_VALUES = {
    "identity_and_outcome": ("portable archive review coordination is verified",),
    "changes_and_rationale": ("added deterministic review evidence validation",),
    "program_context": ("bounded local implementation with no external action",),
    "changed_files_by_purpose": ("module: review validation", "tests: contract protection"),
    "human_review_order": ("requirements", "architecture", "test evidence"),
    "requirements_and_acceptance": ("distinct scopes and evidence-complete findings",),
    "exact_commands_and_results": (
        "python3 -m unittest tests.test_review_coordination | exit 0 | 24 tests passed",
    ),
    "baseline_failures": ("none",),
    "execution_evidence": ("test-first RED preceded production GREEN",),
    "reviewer_roles_findings_dispositions": (
        "controller self-review; non-independent; reduced assurance",
        "F-001: repaired",
    ),
    "repairs_and_renewed_verification": ("repair-stale-evidence: material finding repaired and affected scope reviewed again",),
    "deviations_and_amendments": ("none",),
    "human_judgment": ("independence and review quality remain human judgments",),
    "edge_cases_and_manual_checks": ("stale timestamps and unsupported schemas rejected",),
    "implications": ("static validation does not prove production behavior",),
    "residual_risks_and_deferred_work": ("actual reviewer identity is outside this validator",),
    "recovery": ("restore exact source bytes under separate authority",),
    "workspace_and_logical_boundaries": ("no staging or commit requested",),
    "current_state_and_next_action": ("awaiting-diff-approval; obtain exact diff approval",),
}


def packet(**overrides):
    values = {"schema_version": "implementation-review-packet/v1", **PACKET_VALUES}
    if "candidate_sha256" in REVIEW.ReviewPacket.__dataclass_fields__:
        values["candidate_sha256"] = "b" * 64
    values.update(overrides)
    return REVIEW.ReviewPacket(**values)


class ReviewScopeTests(unittest.TestCase):
    def test_required_and_touched_specialist_scopes_are_distinct(self) -> None:
        self.assertEqual(
            REVIEW.select_review_scopes(risk_predicates()),
            (
                "requirements",
                "architecture",
                "test-evidence",
                "specialist-security-privacy",
                "specialist-compatibility",
                "specialist-reliability",
            ),
        )

    def test_predicates_fail_closed_when_missing_duplicated_or_misbound(self) -> None:
        records = risk_predicates()
        with self.assertRaisesRegex(ValueError, "exactly once"):
            REVIEW.select_review_scopes(records[:-1])
        with self.assertRaisesRegex(ValueError, "exactly once"):
            REVIEW.select_review_scopes((*records, records[0]))
        changed = tuple(
            replace(item, specialist_scope="specialist-performance")
            if item.predicate == "security-privacy"
            else item
            for item in records
        )
        with self.assertRaisesRegex(ValueError, "specialist scope"):
            REVIEW.select_review_scopes(changed)

    def test_risk_predicates_are_frozen_and_evidence_complete(self) -> None:
        record = risk_predicates()[0]
        with self.assertRaises(FrozenInstanceError):
            record.touched = False
        invalid = tuple(
            replace(item, evidence="") if item.predicate == "performance" else item
            for item in risk_predicates()
        )
        with self.assertRaisesRegex(ValueError, "evidence"):
            REVIEW.select_review_scopes(invalid)


class ReviewReportTests(unittest.TestCase):
    def test_distinct_initial_reports_cover_every_selected_scope(self) -> None:
        self.assertEqual(
            REVIEW.validate_review_reports(
                required_reports(),
                ("requirements", "architecture", "test-evidence"),
                (),
            ),
            [],
        )
        issues = REVIEW.validate_review_reports(
            (report("requirements"), report("requirements", report_id="requirements-copy")),
            ("requirements", "architecture", "test-evidence"),
            (),
        )
        self.assertTrue(any("initial report" in issue for issue in issues))

    def test_self_review_cannot_claim_independence(self) -> None:
        invalid = report(independent=True, reduced_assurance=False)
        issues = REVIEW.validate_review_reports(
            (invalid, report("architecture"), report("test-evidence")),
            ("requirements", "architecture", "test-evidence"),
            (),
        )
        self.assertTrue(any("self-review cannot claim independence" in issue for issue in issues))

    def test_non_independent_review_requires_reduced_assurance(self) -> None:
        invalid = report(reduced_assurance=False)
        issues = REVIEW.validate_review_reports(
            (invalid, report("architecture"), report("test-evidence")),
            ("requirements", "architecture", "test-evidence"),
            (),
        )
        self.assertTrue(any("reduced assurance" in issue for issue in issues))

    def test_raw_report_must_precede_reconciliation(self) -> None:
        invalid = report(persisted_at="2026-08-09T11:00:00Z", reconciled_at="2026-08-09T10:00:00Z")
        issues = REVIEW.validate_review_reports(
            (invalid, report("architecture"), report("test-evidence")),
            ("requirements", "architecture", "test-evidence"),
            (),
        )
        self.assertTrue(any("before reconciliation" in issue for issue in issues))

    def test_initial_raw_paths_and_digests_are_distinct(self) -> None:
        reports = tuple(
            report(scope, raw_report_path="reviews/shared.md", raw_report_sha256="a" * 64)
            for scope in ("requirements", "architecture", "test-evidence")
        )
        issues = REVIEW.validate_review_reports(
            reports, ("requirements", "architecture", "test-evidence"), ()
        )
        self.assertTrue(any("distinct raw" in issue for issue in issues))

    def test_independent_review_requires_bounded_basis_and_withheld_conclusions(self) -> None:
        independent = report(
            reviewer_role="independent-final-reviewer",
            independent=True,
            reduced_assurance=False,
        )
        issues = REVIEW.validate_review_reports(
            (independent, report("architecture"), report("test-evidence")),
            ("requirements", "architecture", "test-evidence"),
            (),
        )
        self.assertTrue(any("bounded basis" in issue for issue in issues))
        self.assertTrue(any("withheld conclusions" in issue for issue in issues))

    def test_all_reports_bind_one_reviewed_candidate(self) -> None:
        reports = list(required_reports())
        if "reviewed_candidate_sha256" in REVIEW.ReviewReport.__dataclass_fields__:
            reports[1] = replace(reports[1], reviewed_candidate_sha256="f" * 64)
        issues = REVIEW.validate_review_reports(
            tuple(reports), ("requirements", "architecture", "test-evidence"), ()
        )
        self.assertTrue(any("reviewed candidate" in issue for issue in issues))

    def test_follow_up_reports_may_bind_the_repaired_candidate(self) -> None:
        material = finding()
        initial = tuple(
            replace(
                report(scope),
                reviewed_candidate_sha256="a" * 64,
                finding_ids=("F-001",) if scope == "requirements" else (),
            )
            for scope in ("requirements", "architecture", "test-evidence")
        )
        follow_up = report(
            report_id="requirements-follow-up",
            reviewed_candidate_sha256="b" * 64,
            follow_up_for_finding_ids=("F-001",),
            persisted_at="2026-08-09T11:21:00Z",
            reconciled_at="2026-08-09T11:30:00Z",
        )
        self.assertEqual(
            REVIEW.validate_review_reports(
                (*initial, follow_up),
                ("requirements", "architecture", "test-evidence"),
                (material,),
            ),
            [],
        )

    def test_second_independent_reviewer_requires_material_follow_up(self) -> None:
        material = finding(disposition="open")
        initial = report(
            reviewer_role="independent-final-reviewer",
            independent=True,
            reduced_assurance=False,
            review_basis="independent bounded final review",
            prior_conclusions_withheld=True,
            finding_ids=("F-001",),
        )
        second = report(
            "requirements",
            report_id="requirements-follow-up",
            reviewer_role="second-independent-reviewer",
            independent=True,
            reduced_assurance=False,
            review_basis="independent bounded material-defect follow-up",
            prior_conclusions_withheld=True,
            follow_up_for_finding_ids=(),
            persisted_at="2026-08-09T11:10:00Z",
            reconciled_at="2026-08-09T11:20:00Z",
        )
        reports = (initial, report("architecture"), report("test-evidence"), second)
        issues = REVIEW.validate_review_reports(
            reports, ("requirements", "architecture", "test-evidence"), (material,)
        )
        self.assertTrue(any("second independent reviewer" in issue for issue in issues))
        allowed = replace(second, follow_up_for_finding_ids=("F-001",))
        self.assertEqual(
            REVIEW.validate_review_reports(
                (*reports[:-1], allowed),
                ("requirements", "architecture", "test-evidence"),
                (material,),
            ),
            [],
        )


class FindingTests(unittest.TestCase):
    def test_material_finding_requires_complete_contract(self) -> None:
        self.assertEqual(REVIEW.validate_findings((finding(),)), [])
        for field in ("evidence", "impact", "confidence", "remediation", "disposition"):
            with self.subTest(field=field):
                issues = REVIEW.validate_findings((replace(finding(), **{field: ""}),))
                self.assertTrue(issues)

    def test_findings_reject_duplicates_unknown_classes_and_boolean_confidence(self) -> None:
        issues = REVIEW.validate_findings(
            (
                finding(),
                finding(),
                finding(finding_id="F-002", classification="preference"),
                finding(finding_id="F-003", confidence=True),
            )
        )
        self.assertTrue(any("duplicated" in issue for issue in issues))
        self.assertTrue(any("classification" in issue for issue in issues))
        self.assertTrue(any("confidence" in issue for issue in issues))

    def test_non_material_preferences_cannot_remain_open(self) -> None:
        invalid = finding(
            classification="speculative",
            evidence="not demonstrated",
            impact="none demonstrated",
            confidence="low",
            remediation="none",
            disposition="open",
        )
        self.assertTrue(REVIEW.validate_findings((invalid,)))

    def test_accepted_or_deferred_material_risk_requires_decision_reference(self) -> None:
        invalid = finding(disposition="accepted-risk")
        issues = REVIEW.validate_findings((invalid,))
        self.assertTrue(any("decision reference" in issue for issue in issues))


class SemanticNamingReviewTests(unittest.TestCase):
    def test_complete_contextual_disposition_matches_surface(self) -> None:
        self.assertEqual(
            REVIEW.validate_semantic_naming_review(
                (("ReviewReport", "symbol"),),
                (semantic_disposition(),),
                (),
            ),
            [],
        )

    def test_semantic_finding_requires_context_intention_and_specific_basis(self) -> None:
        material = finding(
            finding_id="F-NAME",
            report_id="architecture-initial",
            scope="architecture",
        )
        invalid = semantic_disposition(
            surface="Task 9 output",
            context="",
            intention="",
            planning_term_basis="implementation-governance",
            basis_owner="none",
            status="finding",
            finding_id="F-NAME",
        )
        issues = REVIEW.validate_semantic_naming_review(
            (("Task 9 output", "symbol"),), (invalid,), (material,)
        )
        self.assertTrue(any("stable context" in issue for issue in issues))
        self.assertTrue(any("intention" in issue for issue in issues))
        self.assertTrue(any("specific governance" in issue or "basis owner" in issue for issue in issues))

    def test_flagged_name_must_reference_a_material_finding(self) -> None:
        invalid = semantic_disposition(status="finding", finding_id="F-MISSING")
        issues = REVIEW.validate_semantic_naming_review(
            (("ReviewReport", "symbol"),), (invalid,), ()
        )
        self.assertTrue(any("material finding" in issue for issue in issues))

    def test_surface_kind_pairs_are_exact_and_unique(self) -> None:
        records = (semantic_disposition(), semantic_disposition())
        issues = REVIEW.validate_semantic_naming_review(
            (("ReviewReport", "path"),), records, ()
        )
        self.assertTrue(any("surface kind pairs" in issue for issue in issues))


class RemediationTests(unittest.TestCase):
    def test_repaired_material_finding_requires_complete_cycle_and_renewed_report(self) -> None:
        material = finding()
        follow_up = report(
            report_id="requirements-follow-up",
            follow_up_for_finding_ids=("F-001",),
            persisted_at="2026-08-09T11:21:00Z",
            reconciled_at="2026-08-09T11:30:00Z",
        )
        self.assertEqual(
            REVIEW.validate_remediation_cycles(
                (material,), (remediation_cycle(),), (*required_reports(), follow_up)
            ),
            [],
        )
        self.assertTrue(
            REVIEW.validate_remediation_cycles((material,), (), required_reports())
        )

    def test_cycle_rejects_wrong_order_failed_green_and_unaffected_finding(self) -> None:
        follow_up = report(
            report_id="requirements-follow-up",
            follow_up_for_finding_ids=("F-001",),
        )
        invalid = remediation_cycle(
            started_at="2026-08-09T11:20:00Z",
            completed_at="2026-08-09T11:10:00Z",
            verification_result="failed",
        )
        issues = REVIEW.validate_remediation_cycles(
            (finding(),), (invalid,), (*required_reports(), follow_up)
        )
        self.assertTrue(any("completion" in issue for issue in issues))
        self.assertTrue(any("verification" in issue for issue in issues))

    def test_cycle_requires_exact_changed_paths_and_affected_scopes(self) -> None:
        cycle = remediation_cycle()
        if "changed_paths" in REVIEW.RemediationCycle.__dataclass_fields__:
            cycle = replace(cycle, changed_paths=(), affected_scopes=())
        follow_up = report(
            report_id="requirements-follow-up",
            follow_up_for_finding_ids=("F-001",),
            persisted_at="2026-08-09T11:21:00Z",
            reconciled_at="2026-08-09T11:30:00Z",
        )
        issues = REVIEW.validate_remediation_cycles(
            (finding(),), (cycle,), (*required_reports(), follow_up)
        )
        self.assertTrue(any("changed paths" in issue for issue in issues))
        self.assertTrue(any("affected scopes" in issue for issue in issues))


class FinalVerificationTests(unittest.TestCase):
    def test_fresh_successful_verification_passes(self) -> None:
        self.assertEqual(
            REVIEW.validate_final_verification(
                final_verification(), (remediation_cycle(),), required_reports()
            ),
            [],
        )

    def test_pre_repair_success_is_not_fresh_final_verification(self) -> None:
        stale = final_verification(
            commands=(command_result(completed_at="2026-08-09T11:15:00Z"),),
            verified_at="2026-08-09T11:16:00Z",
        )
        issues = REVIEW.validate_final_verification(
            stale, (remediation_cycle(),), required_reports()
        )
        self.assertTrue(any("after remediation" in issue for issue in issues))

    def test_failed_duplicate_or_sensitive_results_are_rejected(self) -> None:
        duplicate = command_result()
        invalid = final_verification(
            commands=(
                duplicate,
                duplicate,
                command_result(command="python3 validation.py", exit_code=True),
                command_result(command="python3 safe.py", result="token=not-for-output"),
            ),
            unresolved_material_findings=1,
        )
        issues = REVIEW.validate_final_verification(invalid, (), required_reports())
        self.assertTrue(any("duplicated" in issue for issue in issues))
        self.assertTrue(any("integer zero" in issue for issue in issues))
        self.assertTrue(any("sensitive" in issue for issue in issues))
        self.assertTrue(any("unresolved" in issue for issue in issues))

    def test_required_command_set_must_exactly_match_observed_commands(self) -> None:
        value = final_verification()
        if "required_commands" in REVIEW.FinalVerification.__dataclass_fields__:
            value = replace(
                value,
                required_commands=(
                    "python3 -m unittest tests.test_review_coordination",
                    "python3 skills/implementing-staged-plans/scripts/validate_package.py .",
                ),
            )
        issues = REVIEW.validate_final_verification(value, (), required_reports())
        self.assertTrue(any("required command set" in issue for issue in issues))

    def test_command_receipts_require_expectation_and_relevant_inputs(self) -> None:
        item = command_result()
        if "expected_result" in REVIEW.CommandResult.__dataclass_fields__:
            item = replace(item, expected_result="", relevant_inputs=())
        issues = REVIEW.validate_final_verification(
            final_verification(commands=(item,)), (), required_reports()
        )
        self.assertTrue(any("expected result" in issue for issue in issues))
        self.assertTrue(any("relevant inputs" in issue for issue in issues))


class ReviewPacketTests(unittest.TestCase):
    def test_complete_packet_validates_and_renders_deterministically(self) -> None:
        value = packet()
        verification = final_verification()
        self.assertEqual(
            REVIEW.validate_review_packet(value, verification, required_reports(), (), ()),
            [],
        )
        rendered = REVIEW.render_review_packet(value)
        self.assertEqual(rendered, REVIEW.render_review_packet(value))
        self.assertTrue(rendered.startswith("# Review Packet\n\n## Identity and outcome\n"))

    def test_command_only_packet_is_rejected(self) -> None:
        empty = {
            name: ()
            for name in REVIEW.PACKET_FIELDS
            if name != "exact_commands_and_results"
        }
        invalid = packet(**empty)
        issues = REVIEW.validate_review_packet(
            invalid, final_verification(), required_reports(), (), ()
        )
        self.assertTrue(any("canonical field" in issue for issue in issues))

    def test_packet_commands_must_equal_final_verification(self) -> None:
        invalid = packet(exact_commands_and_results=("different command",))
        issues = REVIEW.validate_review_packet(
            invalid, final_verification(), required_reports(), (), ()
        )
        self.assertTrue(any("exact commands" in issue for issue in issues))

    def test_renderer_refuses_invalid_or_mutable_packet_data(self) -> None:
        invalid = packet(identity_and_outcome=[])
        with self.assertRaisesRegex(ValueError, "canonical field"):
            REVIEW.render_review_packet(invalid)

    def test_packet_candidate_binding_matches_final_verification(self) -> None:
        value = packet()
        if "candidate_sha256" in REVIEW.ReviewPacket.__dataclass_fields__:
            value = replace(value, candidate_sha256="f" * 64)
        issues = REVIEW.validate_review_packet(
            value, final_verification(), required_reports(), (), ()
        )
        self.assertTrue(any("candidate binding" in issue for issue in issues))


class IntegrationTests(unittest.TestCase):
    def test_neutral_repaired_finding_bundle_matches_persisted_packet(self) -> None:
        bundle = json.loads(FIXTURE_EVIDENCE.read_text(encoding="utf-8"))
        packet_text = FIXTURE_PACKET.read_text(encoding="utf-8")
        self.assertEqual(REVIEW.validate_review_bundle(bundle, packet_text), [])

    def test_bundle_rejects_unknown_schema_structural_gaps_and_packet_drift(self) -> None:
        bundle = json.loads(FIXTURE_EVIDENCE.read_text(encoding="utf-8"))
        changed = dict(bundle)
        changed["schema_version"] = "legacy/v0"
        self.assertTrue(REVIEW.validate_review_bundle(changed, FIXTURE_PACKET.read_text()))
        self.assertTrue(REVIEW.validate_review_bundle({}, "# Review Packet\n"))
        self.assertTrue(
            REVIEW.validate_review_bundle(
                bundle, FIXTURE_PACKET.read_text(encoding="utf-8") + "drift"
            )
        )
        with_unknown = {**bundle, "unexpected": True}
        self.assertTrue(
            any(
                "unknown fields" in issue
                for issue in REVIEW.validate_review_bundle(
                    with_unknown, FIXTURE_PACKET.read_text(encoding="utf-8")
                )
            )
        )

    def test_cli_returns_zero_one_and_two_without_exposing_bundle_contents(self) -> None:
        valid = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "validate-bundle", str(FIXTURE_EVIDENCE), "--packet", str(FIXTURE_PACKET)],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(valid.returncode, 0)
        self.assertEqual(valid.stdout, "Review bundle validation passed\n")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid_path = root / "invalid.json"
            invalid_path.write_text('{"password":"must-not-print"}', encoding="utf-8")
            packet_path = root / "packet.md"
            packet_path.write_text("# invalid\n", encoding="utf-8")
            invalid = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "validate-bundle", str(invalid_path), "--packet", str(packet_path)],
                cwd=REPOSITORY_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(invalid.returncode, 1)
            self.assertNotIn("must-not-print", invalid.stdout)
            symlink = root / "linked.json"
            symlink.symlink_to(invalid_path)
            usage = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "validate-bundle", str(symlink), "--packet", str(packet_path)],
                cwd=REPOSITORY_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(usage.returncode, 2)


if __name__ == "__main__":
    unittest.main()
