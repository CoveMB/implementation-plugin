import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "continuity_closure.py"
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "tests/fixtures/continuity-closure/portable-catalog-run"
)

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC = importlib.util.spec_from_file_location("continuity_closure", SCRIPT_PATH)
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load continuity and closure from {SCRIPT_PATH}")
    CONTINUITY = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = CONTINUITY
    SPEC.loader.exec_module(CONTINUITY)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def brief(**overrides):
    values = {
        "schema_version": "implementation-continuity-evidence/v1",
        "program_id": "portable-catalog",
        "program_revision": 3,
        "increment_id": "catalog-index",
        "title": "Catalog index",
        "outcome": "Produce a verified catalog index from accepted archive metadata.",
        "requirement_ids": ("CAT-001", "CAT-002"),
        "acceptance": "Use the approved catalog-index criteria.",
        "approval_mode": "approval:full",
        "workspace_path": "/workspace/portable-catalog",
        "workspace_branch": "catalog-maintenance",
        "workspace_base_commit": "b" * 40,
        "workspace_head_commit": "a" * 40,
        "status_path": "state/status.json",
        "status_sha256": "1" * 64,
        "handoff_path": "increments/archive-scan/handoff.md",
        "handoff_sha256": "2" * 64,
        "unresolved_user_decision": "none",
        "optional_context": (("integration_checkpoint", "Keep the prior archive ordering stable."),),
    }
    values.update(overrides)
    return CONTINUITY.LeanBrief(**values)


def handoff(**overrides):
    values = {
        "schema_version": "implementation-continuity-evidence/v1",
        "program_id": "portable-catalog",
        "program_revision": 3,
        "current_increment_id": "archive-scan",
        "current_increment_state": "accepted",
        "approval_mode": "approval:full",
        "workspace_path": "/workspace/portable-catalog",
        "workspace_branch": "catalog-maintenance",
        "base_commit": "b" * 40,
        "head_commit": "a" * 40,
        "accepted_increments": ("archive-capture", "archive-scan"),
        "verification_status": "accepted with focused and program validation passing",
        "accepted_review_packet_path": "increments/archive-scan/review-packet.md",
        "accepted_review_packet_sha256": "3" * 64,
        "accepted_handoff_addendum_path": "increments/archive-scan/handoff-addendum.md",
        "accepted_handoff_addendum_sha256": "4" * 64,
        "accepted_status_sequence": 14,
        "accepted_status_sha256": "5" * 64,
        "amendments": ("none",),
        "unresolved_risks": ("A live archive import remains outside this local run.",),
        "next_legal_action": "Submit the matching catalog-index brief and request renewed authority.",
        "first_read_files": (
            "manifest.json",
            "state/status.json",
            "increments/archive-scan/review-packet.md",
        ),
    }
    values.update(overrides)
    return CONTINUITY.HandoffRecord(**values)


def assessment(**overrides):
    predicates = tuple(
        (name, True, f"fresh evidence for {name}")
        for name in CONTINUITY.CONVERSATION_SUITABILITY_PREDICATES
    )
    values = {
        "schema_version": "implementation-continuity-evidence/v1",
        "approval_mode": "approval:full",
        "same_conversation": True,
        "predicate_evidence": predicates,
        "submitted_brief_sha256": "6" * 64,
        "expected_brief_sha256": "6" * 64,
        "explicit_renewed_authority": False,
    }
    values.update(overrides)
    return CONTINUITY.ConversationAssessment(**values)


def resume_context(**overrides):
    values = {
        "schema_version": "implementation-continuity-evidence/v1",
        "program_id": "portable-catalog",
        "program_revision": 3,
        "source_sha256": "7" * 64,
        "program_sha256": "8" * 64,
        "semantic_requirements_sha256": "9" * 64,
        "workspace_path": "/workspace/portable-catalog",
        "workspace_branch": "catalog-maintenance",
        "workspace_base_commit": "b" * 40,
        "workspace_head_commit": "a" * 40,
        "status_sha256": "1" * 64,
        "status_sequence": 14,
        "brief_sha256": "6" * 64,
        "handoff_sha256": "2" * 64,
        "accepted_review_packet_sha256": "3" * 64,
        "accepted_handoff_addendum_sha256": "4" * 64,
        "conflicted_paths": (),
        "active_git_operation": None,
        "matching_authorization_ids": ("CATALOG-RESUME-AUTH",),
    }
    values.update(overrides)
    return CONTINUITY.ResumeContext(**values)


def disposition(requirement_id="CAT-001", **overrides):
    values = {
        "requirement_id": requirement_id,
        "disposition": "implemented",
        "evidence_paths": (f"evidence/{requirement_id.lower()}.json",),
        "owner": "catalog-maintainers",
        "approval_reference": "none",
        "later_invalidation_checked": True,
    }
    values.update(overrides)
    return CONTINUITY.ClosureRequirementDisposition(**values)


def reconciliation(**overrides):
    values = {
        "schema_version": "implementation-closure-reconciliation/v1",
        "program_id": "portable-catalog",
        "program_revision": 3,
        "final_increment_id": "catalog-index",
        "expected_requirement_ids": ("CAT-001", "CAT-002"),
        "requirement_dispositions": (disposition(), disposition("CAT-002")),
        "accepted_increment_ids": ("archive-capture", "archive-scan", "catalog-index"),
        "accepted_artifact_bindings": (
            ("archive-capture:review-packet", "1" * 64),
            ("archive-capture:handoff-addendum", "2" * 64),
            ("archive-scan:review-packet", "3" * 64),
            ("archive-scan:handoff-addendum", "4" * 64),
            ("catalog-index:review-packet", "a" * 64),
            ("catalog-index:handoff-addendum", "b" * 64),
        ),
        "approved_amendment_ids": ("none",),
        "resolved_amendment_ids": ("none",),
        "decision_ids": ("CATALOG-DECISION-001",),
        "deferrals": (),
        "unresolved_material_findings": 0,
        "program_command_results": (
            ("python3 -m unittest", 0, "2026-08-09T12:10:00Z"),
        ),
        "latest_contributing_evidence_at": "2026-08-09T12:00:00Z",
        "later_invalidation_checks": ("archive-capture", "archive-scan", "catalog-index"),
        "architecture_assessment": "cohesive local boundary",
        "documentation_assessment": "operator route is current",
        "operations_assessment": "no external state was changed",
        "recovery_assessment": "per-file recovery remains available",
    }
    values.update(overrides)
    return CONTINUITY.ClosureReconciliation(**values)


def closure_packet(**overrides):
    values = {
        "schema_version": "implementation-closure-packet/v1",
        "program_id": "portable-catalog",
        "program_revision": 3,
        "final_increment_id": "catalog-index",
        "final_increment_accepted": True,
        "reconciliation_sha256": "c" * 64,
        "current_program_state": "active",
        "requirement_summary": ("CAT-001 and CAT-002 are implemented with accepted evidence.",),
        "amendment_and_deferral_summary": ("No unresolved amendments or deferrals.",),
        "accepted_packet_integrity": ("All accepted packet and addendum digests match.",),
        "program_verification": ("Fresh program command completed successfully.",),
        "architecture_documentation_operations_recovery": (
            "Architecture, documentation, operations, and recovery were reassessed.",
        ),
        "findings_and_dispositions": ("No unresolved material findings.",),
        "residual_risks": ("Live provider behavior was not exercised.",),
        "closure_approval_request": "Review this exact packet and explicitly approve or reject program closure.",
        "next_action": "Stop for explicit closure approval.",
    }
    values.update(overrides)
    return CONTINUITY.ClosurePacket(**values)


def authority_context():
    return {
        "program_id": "portable-catalog",
        "program_revision": 3,
        "source_id": "CATALOG-SOURCE-002",
        "source_sha256": "7" * 64,
        "program_sha256": "8" * 64,
        "semantic_requirements_sha256": "9" * 64,
        "increment_id": "catalog-index",
        "brief_sha256": "6" * 64,
        "exact_file_plan_sha256": "e" * 64,
        "approval_mode": "approval:full",
        "workspace": {
            "path": "/workspace/portable-catalog",
            "branch": "catalog-maintenance",
            "base_commit": "b" * 40,
            "head_commit": "a" * 40,
        },
    }


def bound_record(values):
    return {**authority_context(), **values}


class ImmutableRecordTests(unittest.TestCase):
    def test_records_are_frozen_and_nested_json_lists_are_normalized(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            brief().program_id = "changed"
        loaded = CONTINUITY.lean_brief_from_mapping(
            {**brief().__dict__, "requirement_ids": ["CAT-001", "CAT-002"], "optional_context": [["risk", "bounded"]]}
        )
        self.assertIsInstance(loaded.requirement_ids, tuple)
        self.assertIsInstance(loaded.optional_context, tuple)

    def test_booleans_are_rejected_as_sequences_and_exit_codes(self) -> None:
        self.assertIn(
            "status_sequence",
            " ".join(CONTINUITY.validate_resume_context(resume_context(status_sequence=True), resume_context())),
        )
        invalid = reconciliation(program_command_results=(("python3 -m unittest", True, "2026-08-09T12:10:00Z"),))
        self.assertIn("exit code", " ".join(CONTINUITY.validate_closure_reconciliation(invalid)))


class BriefAndHandoffTests(unittest.TestCase):
    def test_copy_ready_prompt_explicitly_invokes_front_door_skill(self) -> None:
        rendered = CONTINUITY.render_increment_brief(brief())

        self.assertEqual(rendered.splitlines()[0], "$implementing-staged-plans")

    def test_minimal_brief_has_all_semantics_and_deterministic_markdown(self) -> None:
        self.assertEqual(CONTINUITY.validate_increment_brief(brief()), [])
        rendered = CONTINUITY.render_increment_brief(brief())
        self.assertEqual(rendered, CONTINUITY.render_increment_brief(brief()))
        for value in ("portable-catalog", "catalog-index", "CAT-001", "approval:full", "state/status.json"):
            self.assertIn(value, rendered)
        for copied_policy in ("TDD procedures", "review-role definitions", "hard-stop catalogues"):
            self.assertNotIn(copied_policy, rendered)

    def test_brief_rejects_missing_stale_policy_and_unknown_optional_context(self) -> None:
        cases = (
            brief(outcome=""),
            brief(status_sha256="0" * 64),
            brief(acceptance="Copy all TDD procedures and hard-stop catalogues."),
            brief(optional_context=(("workflow_policy", "repeat every rule"),)),
        )
        for candidate in cases:
            with self.subTest(candidate=candidate):
                self.assertTrue(CONTINUITY.validate_increment_brief(candidate))

    def test_material_optional_context_is_preserved(self) -> None:
        candidate = brief(optional_context=(("notable_risk", "Archive ordering is a protected compatibility surface."),))
        self.assertEqual(CONTINUITY.validate_increment_brief(candidate), [])
        self.assertIn("Archive ordering", CONTINUITY.render_increment_brief(candidate))

    def test_handoff_is_complete_deterministic_and_navigation_only(self) -> None:
        self.assertEqual(CONTINUITY.validate_handoff(handoff()), [])
        rendered = CONTINUITY.render_handoff(handoff())
        self.assertEqual(rendered, CONTINUITY.render_handoff(handoff()))
        for value in ("archive-scan", "catalog-maintenance", "review-packet.md", "Next legal action", "Files to inspect first"):
            self.assertIn(value, rendered)

    def test_handoff_rejects_stale_incomplete_secret_like_or_authorizing_text(self) -> None:
        cases = (
            handoff(accepted_status_sequence=True),
            handoff(first_read_files=()),
            handoff(head_commit="0" * 40),
            handoff(unresolved_risks=("token=secret-value",)),
            handoff(next_legal_action="You are authorized to create a draft pull request."),
        )
        for candidate in cases:
            with self.subTest(candidate=candidate):
                self.assertTrue(CONTINUITY.validate_handoff(candidate))


class ContinuationAndResumeTests(unittest.TestCase):
    def test_full_mode_continues_only_in_a_suitable_same_conversation(self) -> None:
        allowed, issues = CONTINUITY.evaluate_continuation(assessment())
        self.assertTrue(allowed, issues)
        for predicate in CONTINUITY.CONVERSATION_SUITABILITY_PREDICATES:
            changed = tuple(
                (name, False, "boundary reached") if name == predicate else item
                for item in assessment().predicate_evidence
                for name in (item[0],)
            )
            allowed, issues = CONTINUITY.evaluate_continuation(assessment(predicate_evidence=changed))
            self.assertFalse(allowed)
            self.assertIn("handoff", " ".join(issues).lower())

    def test_one_increment_modes_stop_and_new_conversation_requires_brief_plus_authority(self) -> None:
        for mode in ("approval:standard", "approval:pre-approve", "approval:full-increment", "approval:full-diff"):
            with self.subTest(mode=mode):
                self.assertFalse(CONTINUITY.evaluate_continuation(assessment(approval_mode=mode))[0])
        resumed = assessment(same_conversation=False, explicit_renewed_authority=True)
        self.assertTrue(CONTINUITY.evaluate_continuation(resumed)[0])
        for changed in (
            replace(resumed, explicit_renewed_authority=False),
            replace(resumed, submitted_brief_sha256="0" * 64),
        ):
            self.assertFalse(CONTINUITY.evaluate_continuation(changed)[0])

    def test_resume_revalidates_every_authority_dimension(self) -> None:
        expected = resume_context()
        self.assertEqual(CONTINUITY.validate_resume_context(expected, expected), [])
        replacements = {
            "source_sha256": "0" * 64,
            "program_sha256": "0" * 64,
            "semantic_requirements_sha256": "0" * 64,
            "workspace_path": "/other",
            "workspace_branch": "other",
            "workspace_base_commit": "c" * 40,
            "workspace_head_commit": "d" * 40,
            "status_sha256": "0" * 64,
            "brief_sha256": "0" * 64,
            "handoff_sha256": "0" * 64,
            "accepted_review_packet_sha256": "0" * 64,
            "accepted_handoff_addendum_sha256": "0" * 64,
            "active_git_operation": "rebase",
            "conflicted_paths": ("catalog.json",),
            "matching_authorization_ids": (),
        }
        for field, value in replacements.items():
            with self.subTest(field=field):
                self.assertTrue(CONTINUITY.validate_resume_context(replace(expected, **{field: value}), expected))
        duplicate = replace(expected, matching_authorization_ids=("A", "B"))
        self.assertIn("exactly one", " ".join(CONTINUITY.validate_resume_context(duplicate, expected)))

    def test_resume_composes_current_state_authority_when_supplied(self) -> None:
        expected = resume_context()
        with mock.patch.object(CONTINUITY, "validate_state_authority", return_value=["state drift"]):
            issues = CONTINUITY.validate_resume_context(
                expected,
                expected,
                program_root=Path("/program"),
                observation=object(),
            )
        self.assertIn("state drift", issues)

    def test_explicit_resume_request_materializes_and_validates_the_full_context(self) -> None:
        expected = resume_context()
        record = CONTINUITY.build_continuation_authorization(
            expected,
            authorization_id="CATALOG-RESUME-AUTH",
            user_request_id="REQUEST-RESUME-CATALOG",
            requested_action="modify-workspace",
            requested_scope="continue the exact catalog index increment",
            issued_at="2000-08-10T12:00:00Z",
            expires_at="2999-08-10T13:00:00Z",
        )

        self.assertEqual(
            CONTINUITY.validate_continuation_authority(
                expected,
                expected,
                (record,),
                user_request_id="REQUEST-RESUME-CATALOG",
                requested_action="modify-workspace",
                requested_scope="continue the exact catalog index increment",
            ),
            [],
        )
        for field, changed in {
            "source_sha256": "0" * 64,
            "program_sha256": "0" * 64,
            "semantic_requirements_sha256": "0" * 64,
            "workspace_path": "/other",
            "workspace_branch": "other",
            "workspace_base_commit": "c" * 40,
            "workspace_head_commit": "d" * 40,
            "status_sha256": "0" * 64,
            "status_sequence": 15,
            "brief_sha256": "0" * 64,
            "handoff_sha256": "0" * 64,
            "accepted_review_packet_sha256": "0" * 64,
            "accepted_handoff_addendum_sha256": "0" * 64,
        }.items():
            with self.subTest(field=field):
                stale = {**record, field: changed}
                issues = CONTINUITY.validate_continuation_authority(
                    expected,
                    expected,
                    (stale,),
                    user_request_id="REQUEST-RESUME-CATALOG",
                    requested_action="modify-workspace",
                    requested_scope="continue the exact catalog index increment",
                )
                self.assertIn("exactly one current continuation authorization", issues)

    def test_resume_authority_rejects_handoff_only_duplicate_revoked_expired_and_wrong_request(self) -> None:
        expected = resume_context()
        record = CONTINUITY.build_continuation_authorization(
            expected,
            authorization_id="CATALOG-RESUME-AUTH",
            user_request_id="REQUEST-RESUME-CATALOG",
            requested_action="modify-workspace",
            requested_scope="continue the exact catalog index increment",
            issued_at="2000-08-10T12:00:00Z",
            expires_at="2999-08-10T13:00:00Z",
        )

        scenarios = (
            (),
            (record, dict(record)),
            ({**record, "revoked": True},),
            ({**record, "expires_at": "2000-01-01T00:00:00Z"},),
            ({**record, "decision": "denied"},),
        )
        for records in scenarios:
            with self.subTest(records=records):
                self.assertTrue(
                    CONTINUITY.validate_continuation_authority(
                        expected,
                        expected,
                        records,
                        user_request_id="REQUEST-RESUME-CATALOG",
                        requested_action="modify-workspace",
                        requested_scope="continue the exact catalog index increment",
                    )
                )
        wrong_request = CONTINUITY.validate_continuation_authority(
            expected,
            expected,
            (record,),
            user_request_id="REQUEST-OTHER",
            requested_action="modify-workspace",
            requested_scope="continue the exact catalog index increment",
        )
        self.assertIn("exactly one current continuation authorization", wrong_request)

    def test_resume_authority_is_live_only_within_its_issuance_interval(self) -> None:
        expected = resume_context()
        record = CONTINUITY.build_continuation_authorization(
            expected,
            authorization_id="CATALOG-RESUME-AUTH",
            user_request_id="REQUEST-RESUME-CATALOG",
            requested_action="modify-workspace",
            requested_scope="continue the exact catalog index increment",
            issued_at="2000-08-10T12:00:00Z",
            expires_at="2999-08-10T13:00:00Z",
        )
        common = {
            "user_request_id": "REQUEST-RESUME-CATALOG",
            "requested_action": "modify-workspace",
            "requested_scope": "continue the exact catalog index increment",
        }

        self.assertEqual(
            CONTINUITY.validate_continuation_authority(
                expected,
                expected,
                (record,),
                **common,
            ),
            [],
        )
        for changed in (
            {
                **record,
                "issued_at": "2998-08-10T12:00:00Z",
                "expires_at": "2999-08-10T13:00:00Z",
            },
            {
                **record,
                "issued_at": "2999-08-10T12:00:00Z",
                "expires_at": "2998-08-10T13:00:00Z",
            },
        ):
            with self.subTest(changed=changed):
                issues = CONTINUITY.validate_continuation_authority(
                    expected,
                    expected,
                    (changed,),
                    **common,
                )
                self.assertIn("continuation authorization is not currently valid", issues)
        with self.assertRaisesRegex(ValueError, "valid issuance interval"):
            CONTINUITY.build_continuation_authorization(
                expected,
                authorization_id="CATALOG-RESUME-AUTH",
                user_request_id="REQUEST-RESUME-CATALOG",
                requested_action="modify-workspace",
                requested_scope="continue the exact catalog index increment",
                issued_at="2999-08-10T12:00:00Z",
                expires_at="2998-08-10T13:00:00Z",
            )


class RolloverTests(unittest.TestCase):
    def rollover_values(self, root: Path):
        (root / "state").mkdir(exist_ok=True)
        manifest_path = root / "manifest.json"
        status_path = root / "state/status.json"
        manifest_path.write_text('{"current_increment":"archive-scan"}\n', encoding="utf-8")
        status_path.write_text('{"current_increment_state":"accepted"}\n', encoding="utf-8")
        return {
            "root": root,
            "handoff_relative_path": "increments/archive-scan/handoff.md",
            "handoff_record": handoff(),
            "handoff_markdown": CONTINUITY.render_handoff(handoff()),
            "brief_relative_path": "increments/catalog-index/brief.md",
            "brief_record": brief(),
            "brief_markdown": CONTINUITY.render_increment_brief(brief()),
            "manifest_relative_path": "manifest.json",
            "expected_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "manifest_value": {"current_increment": "catalog-index"},
            "status_relative_path": "state/status.json",
            "expected_status_sha256": hashlib.sha256(status_path.read_bytes()).hexdigest(),
            "status_value": {"current_increment_state": "preparing"},
            "current_increment_state": "accepted",
            "current_increment_id": "archive-scan",
            "expected_current_increment_id": "archive-scan",
            "next_increment_id": "catalog-index",
            "next_increment_dependencies": ("archive-scan",),
            "matching_authorization_ids": ("CATALOG-ROLLOVER",),
        }

    def test_rollover_writes_navigation_before_controlling_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "state").mkdir()
            manifest_path = root / "manifest.json"
            status_path = root / "state/status.json"
            manifest_path.write_text('{"current_increment":"archive-scan"}\n', encoding="utf-8")
            status_path.write_text('{"current_increment_state":"accepted"}\n', encoding="utf-8")
            receipt = CONTINUITY.apply_increment_rollover(
                root,
                handoff_relative_path="increments/archive-scan/handoff.md",
                handoff_record=handoff(),
                handoff_markdown=CONTINUITY.render_handoff(handoff()),
                brief_relative_path="increments/catalog-index/brief.md",
                brief_record=brief(),
                brief_markdown=CONTINUITY.render_increment_brief(brief()),
                manifest_relative_path="manifest.json",
                expected_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                manifest_value={"current_increment": "catalog-index"},
                status_relative_path="state/status.json",
                expected_status_sha256=hashlib.sha256(status_path.read_bytes()).hexdigest(),
                status_value={"current_increment_state": "preparing"},
                current_increment_state="accepted",
                current_increment_id="archive-scan",
                expected_current_increment_id="archive-scan",
                next_increment_id="catalog-index",
                next_increment_dependencies=("archive-scan",),
                matching_authorization_ids=("CATALOG-ROLLOVER",),
            )
            self.assertEqual(tuple(path for path, _ in receipt.completed_writes), (
                "increments/archive-scan/handoff.md",
                "increments/catalog-index/brief.md",
                "manifest.json",
                "state/status.json",
            ))
            generated_prompt = (
                root / "increments/catalog-index/brief.md"
            ).read_text(encoding="utf-8")
            self.assertEqual(
                generated_prompt.splitlines()[0],
                "$implementing-staged-plans",
            )
            self.assertFalse(receipt.requires_fresh_resume)

    def test_rollover_adopts_exact_existing_navigation_without_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = self.rollover_values(root)
            handoff_path = root / values["handoff_relative_path"]
            brief_path = root / values["brief_relative_path"]
            handoff_path.parent.mkdir(parents=True)
            brief_path.parent.mkdir(parents=True)
            handoff_path.write_text(values["handoff_markdown"], encoding="utf-8")
            brief_path.write_text(values["brief_markdown"], encoding="utf-8")
            navigation_before = {
                path: (path.stat().st_ino, hashlib.sha256(path.read_bytes()).hexdigest())
                for path in (handoff_path, brief_path)
            }

            receipt = CONTINUITY.apply_increment_rollover(**values)

            self.assertEqual(
                tuple(path for path, _ in receipt.completed_writes),
                ("manifest.json", "state/status.json"),
            )
            self.assertFalse(receipt.requires_fresh_resume)
            self.assertEqual(
                navigation_before,
                {
                    path: (path.stat().st_ino, hashlib.sha256(path.read_bytes()).hexdigest())
                    for path in (handoff_path, brief_path)
                },
            )

    def test_rollover_rejects_changed_mixed_or_symlinked_existing_navigation(self) -> None:
        for case in ("changed", "mixed", "symlink"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                values = self.rollover_values(root)
                handoff_path = root / values["handoff_relative_path"]
                brief_path = root / values["brief_relative_path"]
                handoff_path.parent.mkdir(parents=True)
                brief_path.parent.mkdir(parents=True)
                handoff_path.write_text(values["handoff_markdown"], encoding="utf-8")
                if case == "changed":
                    brief_path.write_text("changed\n", encoding="utf-8")
                elif case == "mixed":
                    pass
                else:
                    outside = root / "outside.md"
                    outside.write_text(values["brief_markdown"], encoding="utf-8")
                    brief_path.symlink_to(outside)
                manifest_before = (root / "manifest.json").read_bytes()
                status_before = (root / "state/status.json").read_bytes()

                with self.assertRaises(ValueError):
                    CONTINUITY.apply_increment_rollover(**values)

                self.assertEqual((root / "manifest.json").read_bytes(), manifest_before)
                self.assertEqual((root / "state/status.json").read_bytes(), status_before)

    def test_existing_navigation_interruption_reports_only_controlling_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = self.rollover_values(root)
            for path, markdown in (
                (root / values["handoff_relative_path"], values["handoff_markdown"]),
                (root / values["brief_relative_path"], values["brief_markdown"]),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(markdown, encoding="utf-8")
            navigation_before = {
                path: path.read_bytes()
                for path in (
                    root / values["handoff_relative_path"],
                    root / values["brief_relative_path"],
                )
            }
            values["fail_after_writes"] = 1

            receipt = CONTINUITY.apply_increment_rollover(**values)

            self.assertEqual(
                tuple(path for path, _ in receipt.completed_writes),
                ("manifest.json",),
            )
            self.assertEqual(receipt.failed_path, "state/status.json")
            self.assertTrue(receipt.requires_fresh_resume)
            self.assertEqual(
                navigation_before,
                {path: path.read_bytes() for path in navigation_before},
            )

    def test_partial_rollover_is_inert_and_requires_fresh_resume(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "state").mkdir()
            manifest_path = root / "manifest.json"
            status_path = root / "state/status.json"
            manifest_path.write_text('{"current_increment":"archive-scan"}\n', encoding="utf-8")
            status_path.write_text('{"current_increment_state":"accepted"}\n', encoding="utf-8")
            unrelated = root / "notes.txt"
            unrelated.write_text("user-owned\n", encoding="utf-8")
            receipt = CONTINUITY.apply_increment_rollover(
                root,
                handoff_relative_path="increments/archive-scan/handoff.md",
                handoff_record=handoff(),
                handoff_markdown=CONTINUITY.render_handoff(handoff()),
                brief_relative_path="increments/catalog-index/brief.md",
                brief_record=brief(),
                brief_markdown=CONTINUITY.render_increment_brief(brief()),
                manifest_relative_path="manifest.json",
                expected_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                manifest_value={"current_increment": "catalog-index"},
                status_relative_path="state/status.json",
                expected_status_sha256=hashlib.sha256(status_path.read_bytes()).hexdigest(),
                status_value={"current_increment_state": "preparing"},
                current_increment_state="accepted",
                current_increment_id="archive-scan",
                expected_current_increment_id="archive-scan",
                next_increment_id="catalog-index",
                next_increment_dependencies=("archive-scan",),
                matching_authorization_ids=("CATALOG-ROLLOVER",),
                fail_after_writes=1,
            )
            self.assertTrue(receipt.requires_fresh_resume)
            self.assertEqual(receipt.failed_path, "increments/catalog-index/brief.md")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user-owned\n")
            self.assertEqual(json.loads(status_path.read_text())["current_increment_state"], "accepted")

    def test_rollover_rejects_missing_authority_illegal_state_and_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "exists.md").write_text("owned\n", encoding="utf-8")
            common = {
                "root": root,
                "handoff_relative_path": "exists.md",
                "handoff_record": handoff(),
                "handoff_markdown": CONTINUITY.render_handoff(handoff()),
                "brief_relative_path": "brief.md",
                "brief_record": brief(),
                "brief_markdown": CONTINUITY.render_increment_brief(brief()),
                "manifest_relative_path": "manifest.json",
                "expected_manifest_sha256": "0" * 64,
                "manifest_value": {},
                "status_relative_path": "status.json",
                "expected_status_sha256": "0" * 64,
                "status_value": {},
                "current_increment_state": "accepted",
                "current_increment_id": "archive-scan",
                "expected_current_increment_id": "archive-scan",
                "next_increment_id": "catalog-index",
                "next_increment_dependencies": ("archive-scan",),
                "matching_authorization_ids": ("CATALOG-ROLLOVER",),
            }
            with self.assertRaises(ValueError):
                CONTINUITY.apply_increment_rollover(**common)
            with self.assertRaisesRegex(ValueError, "authorization"):
                CONTINUITY.apply_increment_rollover(**{**common, "handoff_relative_path": "handoff.md", "matching_authorization_ids": ()})

    def test_rollover_rejects_symlink_parent_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside_directory:
            root = Path(directory)
            values = self.rollover_values(root)
            (root / "linked").symlink_to(Path(outside_directory), target_is_directory=True)
            values.update(
                handoff_relative_path="linked/handoff.md",
                brief_relative_path="increments/catalog-index/brief.md",
            )
            with self.assertRaisesRegex(ValueError, "symlink"):
                CONTINUITY.apply_increment_rollover(**values)
            self.assertFalse((Path(outside_directory) / "handoff.md").exists())

    def test_rollover_preflights_controlling_digests_before_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = self.rollover_values(root)
            values["expected_manifest_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "digest changed"):
                CONTINUITY.apply_increment_rollover(**values)
            self.assertFalse((root / values["handoff_relative_path"]).exists())
            self.assertFalse((root / values["brief_relative_path"]).exists())

    def test_rollover_requires_rendered_bytes_to_match_validated_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            values = self.rollover_values(Path(directory))
            values["brief_markdown"] += "unexpected policy\n"
            with self.assertRaisesRegex(ValueError, "brief Markdown"):
                CONTINUITY.apply_increment_rollover(**values)


class ClosureAndLaterActionTests(unittest.TestCase):
    def draft_preflight(
        self,
        decision,
        remote,
        *,
        prior_consumptions=(),
        checked_at="2026-08-10T12:00:00Z",
        valid_until="2026-08-10T12:05:00Z",
    ):
        return CONTINUITY.DraftPullRequestPreflight(
            request_id="REQUEST-DRAFT-CATALOG",
            authorization_id=str(decision.authorization_id),
            checked_at=checked_at,
            valid_until=valid_until,
            remote_head=remote,
            prior_consumptions=prior_consumptions,
        )

    def authorized_later_action(self, action="create-draft-pull-request"):
        approval = bound_record({
            "schema_version": "implementation-approval/v1",
            "type": "program-closure-approval",
            "decision": "approved",
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
        })
        scope = "open the reviewed catalog as a draft"
        draft_request = (
            CONTINUITY.DraftPullRequestAuthority(
                request_id="REQUEST-DRAFT-CATALOG",
                provider="github",
                repository="example/portable-catalog",
                base_ref="main",
                head_ref="catalog-maintenance",
                head_commit="a" * 40,
                draft=True,
                push_requested=False,
            )
            if action == "create-draft-pull-request"
            else None
        )
        draft_binding = (
            {
                "user_request_id": draft_request.request_id,
                "remote_provider": draft_request.provider,
                "remote_repository": draft_request.repository,
                "base_ref": draft_request.base_ref,
                "head_ref": draft_request.head_ref,
                "head_commit": draft_request.head_commit,
                "draft": draft_request.draft,
                "push_requested": draft_request.push_requested,
            }
            if draft_request is not None
            else {}
        )
        grant = bound_record({
            "schema_version": "implementation-action-authorization/v1",
            "authorization_id": "CATALOG-LATER-ACTION",
            "decision": "authorized",
            "actions": [action],
            "scope": [scope],
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
            **draft_binding,
            **({"expires_at": "2999-08-10T13:00:00Z"} if draft_request else {}),
        })
        decision = CONTINUITY.decide_later_action(
            program_state="closed",
            action=action,
            scope=scope,
            reconciliation_sha256="c" * 64,
            closure_packet_sha256="d" * 64,
            closure_approvals=(approval,),
            action_authorizations=(grant,),
            recovery_evidence=(
                "exact provider recovery"
                if action in CONTINUITY.RECOVERY_REQUIRED_ACTIONS
                else "none required"
            ),
            authority_context=authority_context(),
            draft_pull_request=draft_request,
        )
        self.assertTrue(decision.authorized, decision.issues)
        return decision, scope

    def test_exact_existing_remote_head_can_route_draft_pr_in_the_current_request(self) -> None:
        decision, scope = self.authorized_later_action()
        remote = CONTINUITY.RemoteHeadObservation(
            provider="github",
            repository="example/portable-catalog",
            base_ref="main",
            head_ref="catalog-maintenance",
            head_commit="a" * 40,
            remote_ref_exists=True,
            requires_push=False,
            draft=True,
        )

        routed = CONTINUITY.route_later_action(
            decision,
            action="create-draft-pull-request",
            scope=scope,
            current_request_id="REQUEST-DRAFT-CATALOG",
            current_request_action="create-draft-pull-request",
            current_request_scope=scope,
            authority_context=authority_context(),
            preflight=self.draft_preflight(decision, remote),
            routed_at="2026-08-10T12:01:00Z",
        )

        self.assertTrue(routed.may_execute_same_turn, routed.issues)
        self.assertFalse(routed.must_stop)
        self.assertEqual(routed.authorization_id, decision.authorization_id)

    def test_draft_pr_routing_denies_push_stale_remote_or_implicit_request(self) -> None:
        decision, scope = self.authorized_later_action()
        valid = CONTINUITY.RemoteHeadObservation(
            provider="github",
            repository="example/portable-catalog",
            base_ref="main",
            head_ref="catalog-maintenance",
            head_commit="a" * 40,
            remote_ref_exists=True,
            requires_push=False,
            draft=True,
        )
        cases = (
            {"preflight": self.draft_preflight(decision, replace(valid, requires_push=True))},
            {"preflight": self.draft_preflight(decision, replace(valid, remote_ref_exists=False))},
            {"preflight": self.draft_preflight(decision, replace(valid, head_commit="f" * 40))},
            {"preflight": self.draft_preflight(decision, replace(valid, repository="other/catalog"))},
            {"preflight": self.draft_preflight(decision, replace(valid, draft=False))},
            {"current_request_id": ""},
            {"current_request_action": "merge"},
            {"current_request_scope": "different scope"},
            {"preflight": self.draft_preflight(decision, valid, valid_until="2026-08-10T12:00:30Z")},
        )
        common = {
            "action": "create-draft-pull-request",
            "scope": scope,
            "current_request_id": "REQUEST-DRAFT-CATALOG",
            "current_request_action": "create-draft-pull-request",
            "current_request_scope": scope,
            "authority_context": authority_context(),
            "preflight": self.draft_preflight(decision, valid),
            "routed_at": "2026-08-10T12:01:00Z",
        }
        for overrides in cases:
            with self.subTest(overrides=overrides):
                routed = CONTINUITY.route_later_action(
                    decision, **{**common, **overrides}
                )
                self.assertFalse(routed.may_execute_same_turn)
                self.assertTrue(routed.must_stop)

    def test_high_consequence_later_actions_always_stop_after_authorization(self) -> None:
        decision, scope = self.authorized_later_action("merge")
        routed = CONTINUITY.route_later_action(
            decision,
            action="merge",
            scope=scope,
            current_request_id="REQUEST-MERGE-CATALOG",
            current_request_action="merge",
            current_request_scope=scope,
            authority_context=authority_context(),
            preflight=None,
            routed_at="2026-08-10T12:01:00Z",
        )

        self.assertFalse(routed.may_execute_same_turn)
        self.assertTrue(routed.must_stop)
        self.assertIn("mandatory stop", routed.issues)

    def test_draft_pr_route_rejects_request_replay_and_joint_target_change(self) -> None:
        decision, scope = self.authorized_later_action()
        original = CONTINUITY.RemoteHeadObservation(
            provider="github",
            repository="example/portable-catalog",
            base_ref="main",
            head_ref="catalog-maintenance",
            head_commit="a" * 40,
            remote_ref_exists=True,
            requires_push=False,
            draft=True,
        )
        common = {
            "action": "create-draft-pull-request",
            "scope": scope,
            "current_request_id": "REQUEST-DRAFT-CATALOG",
            "current_request_action": "create-draft-pull-request",
            "current_request_scope": scope,
            "authority_context": authority_context(),
            "preflight": self.draft_preflight(decision, original),
            "routed_at": "2026-08-10T12:01:00Z",
        }

        replayed = CONTINUITY.route_later_action(
            decision,
            **{**common, "current_request_id": "REQUEST-REPLAYED"},
        )
        changed_target = CONTINUITY.route_later_action(
            decision,
            **{
                **common,
                "preflight": self.draft_preflight(
                    decision,
                    replace(
                        original,
                        repository="other/portable-catalog",
                        head_ref="other-maintenance",
                    ),
                ),
            },
        )

        self.assertFalse(replayed.may_execute_same_turn)
        self.assertTrue(replayed.must_stop)
        self.assertFalse(changed_target.may_execute_same_turn)
        self.assertTrue(changed_target.must_stop)

    def test_draft_pr_route_rejects_an_exact_consumed_request_replay(self) -> None:
        decision, scope = self.authorized_later_action()
        remote = CONTINUITY.RemoteHeadObservation(
            provider="github",
            repository="example/portable-catalog",
            base_ref="main",
            head_ref="catalog-maintenance",
            head_commit="a" * 40,
            remote_ref_exists=True,
            requires_push=False,
            draft=True,
        )
        try:
            preflight = CONTINUITY.DraftPullRequestPreflight(
                request_id="REQUEST-DRAFT-CATALOG",
                authorization_id=str(decision.authorization_id),
                checked_at="2026-08-10T12:00:00Z",
                valid_until="2026-08-10T12:05:00Z",
                remote_head=remote,
                prior_consumptions=(),
            )
            first = CONTINUITY.route_later_action(
                decision,
                action="create-draft-pull-request",
                scope=scope,
                current_request_id="REQUEST-DRAFT-CATALOG",
                current_request_action="create-draft-pull-request",
                current_request_scope=scope,
                authority_context=authority_context(),
                preflight=preflight,
                routed_at="2026-08-10T12:01:00Z",
            )
        except (AttributeError, TypeError) as error:
            self.fail(f"draft route lacks request consumption evidence: {error}")

        self.assertTrue(first.may_execute_same_turn, first.issues)
        self.assertIsNotNone(first.consumption_receipt)
        replay_preflight = replace(
            preflight,
            prior_consumptions=(first.consumption_receipt,),
        )
        replayed = CONTINUITY.route_later_action(
            decision,
            action="create-draft-pull-request",
            scope=scope,
            current_request_id="REQUEST-DRAFT-CATALOG",
            current_request_action="create-draft-pull-request",
            current_request_scope=scope,
            authority_context=authority_context(),
            preflight=replay_preflight,
            routed_at="2026-08-10T12:02:00Z",
        )

        self.assertFalse(replayed.may_execute_same_turn)
        self.assertTrue(replayed.must_stop)
        self.assertIn("draft pull request request was already consumed", replayed.issues)

    def test_draft_pr_route_revalidates_grant_expiry(self) -> None:
        decision, scope = self.authorized_later_action()
        remote = CONTINUITY.RemoteHeadObservation(
            provider="github",
            repository="example/portable-catalog",
            base_ref="main",
            head_ref="catalog-maintenance",
            head_commit="a" * 40,
            remote_ref_exists=True,
            requires_push=False,
            draft=True,
        )

        routed = CONTINUITY.route_later_action(
            decision,
            action="create-draft-pull-request",
            scope=scope,
            current_request_id="REQUEST-DRAFT-CATALOG",
            current_request_action="create-draft-pull-request",
            current_request_scope=scope,
            authority_context=authority_context(),
            preflight=self.draft_preflight(
                decision,
                remote,
                checked_at="3000-08-10T12:00:00Z",
                valid_until="3000-08-10T12:05:00Z",
            ),
            routed_at="3000-08-10T12:01:00Z",
        )

        self.assertFalse(routed.may_execute_same_turn)
        self.assertTrue(routed.must_stop)
        self.assertIn("draft pull request grant is not current", routed.issues)
        self.assertIsNone(routed.consumption_receipt)

    def test_draft_pr_decision_requires_request_and_remote_bound_grant(self) -> None:
        scope = "open the reviewed catalog as a draft"
        approval = bound_record({
            "schema_version": "implementation-approval/v1",
            "type": "program-closure-approval",
            "decision": "approved",
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
        })
        draft_request = CONTINUITY.DraftPullRequestAuthority(
            request_id="REQUEST-DRAFT-CATALOG",
            provider="github",
            repository="example/portable-catalog",
            base_ref="main",
            head_ref="catalog-maintenance",
            head_commit="a" * 40,
            draft=True,
            push_requested=False,
        )
        grant = bound_record({
            "schema_version": "implementation-action-authorization/v1",
            "authorization_id": "CATALOG-DRAFT-PR",
            "decision": "authorized",
            "actions": ["create-draft-pull-request"],
            "scope": [scope],
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
            "user_request_id": draft_request.request_id,
            "remote_provider": draft_request.provider,
            "remote_repository": draft_request.repository,
            "base_ref": draft_request.base_ref,
            "head_ref": draft_request.head_ref,
            "head_commit": draft_request.head_commit,
            "draft": True,
            "push_requested": False,
            "expires_at": "2999-08-10T13:00:00Z",
        })
        common = {
            "program_state": "closed",
            "action": "create-draft-pull-request",
            "scope": scope,
            "reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
            "closure_approvals": (approval,),
            "recovery_evidence": "none required",
            "authority_context": authority_context(),
        }

        wrong_request = CONTINUITY.decide_later_action(
            **common,
            action_authorizations=(grant,),
            draft_pull_request=replace(
                draft_request,
                request_id="REQUEST-REPLAYED",
            ),
        )
        wrong_target = CONTINUITY.decide_later_action(
            **common,
            action_authorizations=(grant,),
            draft_pull_request=replace(
                draft_request,
                repository="other/portable-catalog",
            ),
        )
        unbounded_grant = dict(grant)
        unbounded_grant.pop("expires_at")
        unbounded = CONTINUITY.decide_later_action(
            **common,
            action_authorizations=(unbounded_grant,),
            draft_pull_request=draft_request,
        )

        self.assertFalse(wrong_request.authorized)
        self.assertFalse(wrong_target.authorized)
        self.assertFalse(unbounded.authorized)
        self.assertIn("same-turn draft grant requires bounded expiry", unbounded.issues)

    def test_reconciliation_requires_complete_exact_fresh_resolution(self) -> None:
        self.assertEqual(CONTINUITY.validate_closure_reconciliation(reconciliation()), [])
        cases = (
            reconciliation(requirement_dispositions=(disposition(),)),
            reconciliation(requirement_dispositions=(disposition(), disposition())),
            reconciliation(unresolved_material_findings=1),
            reconciliation(program_command_results=(("python3 -m unittest", 1, "2026-08-09T12:10:00Z"),)),
            reconciliation(program_command_results=(("python3 -m unittest", 0, "2026-08-09T11:00:00Z"),)),
            reconciliation(later_invalidation_checks=("catalog-index",)),
            reconciliation(recovery_assessment=""),
        )
        for candidate in cases:
            with self.subTest(candidate=candidate):
                self.assertTrue(CONTINUITY.validate_closure_reconciliation(candidate))

    def test_deferral_and_rejection_require_owner_and_approval(self) -> None:
        deferred = disposition(disposition="deferred", owner="", approval_reference="none")
        rejected = disposition(disposition="rejected", approval_reference="none")
        self.assertTrue(CONTINUITY.validate_closure_reconciliation(reconciliation(requirement_dispositions=(deferred, disposition("CAT-002")))))
        self.assertTrue(CONTINUITY.validate_closure_reconciliation(reconciliation(requirement_dispositions=(rejected, disposition("CAT-002")))))

    def test_reconciliation_requires_packet_and_addendum_for_every_increment(self) -> None:
        incomplete = reconciliation(
            accepted_artifact_bindings=(
                ("catalog-index:review-packet", "a" * 64),
                ("catalog-index:handoff-addendum", "b" * 64),
            )
        )
        self.assertIn("every accepted increment", " ".join(CONTINUITY.validate_closure_reconciliation(incomplete)))

    def test_closure_packet_is_exact_deterministic_and_requests_only_closure(self) -> None:
        self.assertEqual(CONTINUITY.validate_closure_packet(closure_packet(), "c" * 64), [])
        rendered = CONTINUITY.render_closure_packet(closure_packet())
        self.assertEqual(rendered, CONTINUITY.render_closure_packet(closure_packet()))
        self.assertIn("Closure approval request", rendered)
        self.assertNotIn("authorized to create", rendered.lower())
        for candidate in (
            closure_packet(final_increment_accepted=False),
            closure_packet(reconciliation_sha256="0" * 64),
            closure_packet(current_program_state="closed"),
            closure_packet(program_verification=()),
            closure_packet(closure_approval_request="Create a draft pull request."),
        ):
            self.assertTrue(CONTINUITY.validate_closure_packet(candidate, "c" * 64))

    def test_closure_alone_never_authorizes_a_later_action(self) -> None:
        closure_approval = bound_record({
            "schema_version": "implementation-approval/v1",
            "type": "program-closure-approval",
            "decision": "approved",
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
        })
        for action in CONTINUITY.LATER_ACTIONS:
            with self.subTest(action=action):
                decision = CONTINUITY.decide_later_action(
                    program_state="closed",
                    action=action,
                    scope=f"perform {action}",
                    reconciliation_sha256="c" * 64,
                    closure_packet_sha256="d" * 64,
                    closure_approvals=(closure_approval,),
                    action_authorizations=(),
                    recovery_evidence="exact recovery" if action in CONTINUITY.RECOVERY_REQUIRED_ACTIONS else "none required",
                    authority_context=authority_context(),
                )
                self.assertFalse(decision.authorized)

    def test_exact_separate_grant_authorizes_only_the_decision(self) -> None:
        approval = bound_record({
            "schema_version": "implementation-approval/v1",
            "type": "program-closure-approval",
            "decision": "approved",
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
        })
        grant = bound_record({
            "schema_version": "implementation-action-authorization/v1",
            "authorization_id": "CATALOG-DRAFT-PR",
            "decision": "authorized",
            "actions": ["create-draft-pull-request"],
            "scope": ["open the reviewed catalog as a draft"],
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
        })
        decision = CONTINUITY.decide_later_action(
            program_state="closed",
            action="create-draft-pull-request",
            scope="open the reviewed catalog as a draft",
            reconciliation_sha256="c" * 64,
            closure_packet_sha256="d" * 64,
            closure_approvals=(approval,),
            action_authorizations=(grant,),
            recovery_evidence="none required",
            authority_context=authority_context(),
        )
        self.assertTrue(decision.authorized, decision.issues)
        self.assertEqual(decision.authorization_id, "CATALOG-DRAFT-PR")
        self.assertFalse(CONTINUITY.decide_later_action(
            program_state="closed",
            action="merge",
            scope="open the reviewed catalog as a draft",
            reconciliation_sha256="c" * 64,
            closure_packet_sha256="d" * 64,
            closure_approvals=(approval,),
            action_authorizations=(grant,),
            recovery_evidence="none required",
            authority_context=authority_context(),
        ).authorized)

    def test_conflicting_exact_closure_record_denies_later_action(self) -> None:
        approval = bound_record({
            "schema_version": "implementation-approval/v1",
            "type": "program-closure-approval",
            "decision": "approved",
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
        })
        rejection = {**approval, "decision": "rejected"}
        grant = bound_record({
            "schema_version": "implementation-action-authorization/v1",
            "authorization_id": "CATALOG-DRAFT-PR",
            "decision": "authorized",
            "actions": ["create-draft-pull-request"],
            "scope": ["open the reviewed catalog as a draft"],
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
        })
        decision = CONTINUITY.decide_later_action(
            program_state="closed",
            action="create-draft-pull-request",
            scope="open the reviewed catalog as a draft",
            reconciliation_sha256="c" * 64,
            closure_packet_sha256="d" * 64,
            closure_approvals=(approval, rejection),
            action_authorizations=(grant,),
            recovery_evidence="none required",
            authority_context=authority_context(),
        )
        self.assertFalse(decision.authorized)
        self.assertIn("conflicting", " ".join(decision.issues))


class BundleAndCliTests(unittest.TestCase):
    def test_neutral_fixture_bundle_is_valid_and_rendered_exactly(self) -> None:
        issues = CONTINUITY.validate_continuity_bundle(
            json.loads((FIXTURE_ROOT / "continuity-evidence.json").read_text(encoding="utf-8")),
            brief_markdown=(FIXTURE_ROOT / "next-increment-brief.md").read_text(encoding="utf-8"),
            handoff_markdown=(FIXTURE_ROOT / "handoff.md").read_text(encoding="utf-8"),
            reconciliation_mapping=json.loads((FIXTURE_ROOT / "closure-reconciliation.json").read_text(encoding="utf-8")),
            closure_packet_markdown=(FIXTURE_ROOT / "closure-packet.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(issues, [])

    def test_bundle_resume_is_compared_with_independent_handoff_bindings(self) -> None:
        evidence = json.loads(
            (FIXTURE_ROOT / "continuity-evidence.json").read_text(encoding="utf-8")
        )
        evidence["resume"]["accepted_review_packet_sha256"] = "e" * 64

        issues = CONTINUITY.validate_continuity_bundle(
            evidence,
            brief_markdown=(FIXTURE_ROOT / "next-increment-brief.md").read_text(
                encoding="utf-8"
            ),
            handoff_markdown=(FIXTURE_ROOT / "handoff.md").read_text(
                encoding="utf-8"
            ),
        )

        self.assertIn(
            "accepted_review_packet_sha256 mismatch",
            " ".join(issues),
        )

    def test_fixture_negative_scenarios_cover_continuity_and_authority_boundaries(self) -> None:
        evidence = json.loads((FIXTURE_ROOT / "continuity-evidence.json").read_text(encoding="utf-8"))
        scenarios = evidence["negative_scenarios"]
        self.assertEqual(
            {item["name"] for item in scenarios},
            {"overloaded-continuation", "stale-handoff", "premature-closure", "inferred-later-authority"},
        )

    def test_non_full_bundle_still_rejects_malformed_assessment(self) -> None:
        evidence = json.loads((FIXTURE_ROOT / "continuity-evidence.json").read_text(encoding="utf-8"))
        evidence["conversation"]["approval_mode"] = "approval:full-increment"
        evidence["conversation"]["predicate_evidence"] = evidence["conversation"]["predicate_evidence"][:-1]
        issues = CONTINUITY.validate_continuity_bundle(
            evidence,
            brief_markdown=(FIXTURE_ROOT / "next-increment-brief.md").read_text(encoding="utf-8"),
            handoff_markdown=(FIXTURE_ROOT / "handoff.md").read_text(encoding="utf-8"),
            reconciliation_mapping=json.loads((FIXTURE_ROOT / "closure-reconciliation.json").read_text(encoding="utf-8")),
            closure_packet_markdown=(FIXTURE_ROOT / "closure-packet.md").read_text(encoding="utf-8"),
        )
        self.assertIn("predicate", " ".join(issues))

    def test_cli_returns_zero_one_and_two_without_mutating_inputs(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "validate-bundle",
            str(FIXTURE_ROOT / "continuity-evidence.json"),
            "--brief",
            str(FIXTURE_ROOT / "next-increment-brief.md"),
            "--handoff",
            str(FIXTURE_ROOT / "handoff.md"),
            "--reconciliation",
            str(FIXTURE_ROOT / "closure-reconciliation.json"),
            "--closure-packet",
            str(FIXTURE_ROOT / "closure-packet.md"),
        ]
        before = {path: path.read_bytes() for path in FIXTURE_ROOT.iterdir()}
        completed = subprocess.run(command, cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(completed.stdout, "Continuity and closure validation passed\n")
        self.assertEqual(before, {path: path.read_bytes() for path in FIXTURE_ROOT.iterdir()})

        invalid = subprocess.run([*command[:3], str(FIXTURE_ROOT / "missing.json")], cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(invalid.returncode, 2)
        usage = subprocess.run([sys.executable, str(SCRIPT_PATH), "validate-bundle"], cwd=REPOSITORY_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(usage.returncode, 2)


class BriefTests(unittest.TestCase):
    def test_workflow_policy_cannot_be_copied_into_brief(self) -> None:
        candidate = brief(acceptance="Copy all TDD procedures and hard-stop catalogues.")
        self.assertIn("workflow policy", " ".join(CONTINUITY.validate_increment_brief(candidate)))


class ResumeTests(unittest.TestCase):
    def test_stale_handoff_cannot_authorize_resume(self) -> None:
        expected = resume_context()
        stale = replace(expected, handoff_sha256="0" * 64)
        self.assertTrue(CONTINUITY.validate_resume_context(stale, expected))


class ContinuationTests(unittest.TestCase):
    def test_new_conversation_requires_matching_brief_and_renewed_authority(self) -> None:
        candidate = assessment(same_conversation=False)
        self.assertFalse(CONTINUITY.evaluate_continuation(candidate)[0])


class ClosureTests(unittest.TestCase):
    def test_final_acceptance_does_not_close_program(self) -> None:
        candidate = closure_packet(current_program_state="active")
        self.assertEqual(CONTINUITY.validate_closure_packet(candidate, "c" * 64), [])
        self.assertEqual(candidate.current_program_state, "active")


class LaterActionTests(unittest.TestCase):
    def test_closure_approval_does_not_authorize_draft_pull_request(self) -> None:
        approval = bound_record({
            "schema_version": "implementation-approval/v1",
            "type": "program-closure-approval",
            "decision": "approved",
            "closure_reconciliation_sha256": "c" * 64,
            "closure_packet_sha256": "d" * 64,
        })
        decision = CONTINUITY.decide_later_action(
            program_state="closed",
            action="create-draft-pull-request",
            scope="open the reviewed catalog as a draft",
            reconciliation_sha256="c" * 64,
            closure_packet_sha256="d" * 64,
            closure_approvals=(approval,),
            action_authorizations=(),
            recovery_evidence="none required",
            authority_context=authority_context(),
        )
        self.assertFalse(decision.authorized)


class IntegrationTests(unittest.TestCase):
    def test_portable_catalog_bundle(self) -> None:
        evidence = json.loads((FIXTURE_ROOT / "continuity-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(CONTINUITY.validate_continuity_bundle(
            evidence,
            brief_markdown=(FIXTURE_ROOT / "next-increment-brief.md").read_text(encoding="utf-8"),
            handoff_markdown=(FIXTURE_ROOT / "handoff.md").read_text(encoding="utf-8"),
            reconciliation_mapping=json.loads((FIXTURE_ROOT / "closure-reconciliation.json").read_text(encoding="utf-8")),
            closure_packet_markdown=(FIXTURE_ROOT / "closure-packet.md").read_text(encoding="utf-8"),
        ), [])


if __name__ == "__main__":
    unittest.main()
