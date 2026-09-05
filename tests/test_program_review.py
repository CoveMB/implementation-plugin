import json
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture,
    canonical_json,
    repository_snapshot,
    run_program_discovery,
    write_raw_review_reports,
)
from tests.script_module_support import load_script_module
from tests.test_program_activation import ACTIVATION, activated_program, exact_plan_bytes


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_review.py"

REVIEW = load_script_module("program_review", SCRIPT_PATH)


def implementing_program() -> tuple[BootstrapFixture, Path, object]:
    fixture = BootstrapFixture()
    program_root, observation = activated_program(
        fixture, "approval:full-increment"
    )
    ACTIVATION.prepare_exact_plan(
        program_root, exact_plan_bytes(program_root, observation), observation
    )
    ACTIVATION.advance_execution_state(program_root, "implementing", observation)
    (fixture.repository / "archive-output.txt").write_text(
        "archive output\n", encoding="utf-8"
    )
    write_raw_review_reports(fixture.repository)
    product_observation = ACTIVATION.inspect_repository(
        fixture.repository, fixture.head
    ).observation
    return fixture, program_root, product_observation


def reviewing_program(
    raw_mutator=None,
) -> tuple[BootstrapFixture, Path, object]:
    fixture, program_root, _observation = implementing_program()
    if raw_mutator is not None:
        raw_mutator(fixture)
    product_observation = ACTIVATION.inspect_repository(
        fixture.repository, fixture.head
    ).observation
    ACTIVATION.advance_execution_state(
        program_root, "reviewing", product_observation
    )
    return fixture, program_root, product_observation


class ProgramReviewTests(unittest.TestCase):
    def discover(self, fixture: BootstrapFixture) -> dict[str, object]:
        return run_program_discovery(fixture.repository)

    def test_builder_derives_manifest_owned_valid_review_bundle(self) -> None:
        fixture, program_root, observation = reviewing_program()
        try:
            candidate = REVIEW.build_review_preparation(program_root, observation)
            self.assertEqual(
                candidate.evidence_path,
                program_root / "increments/ARCHIVE-INDEX/review-evidence.json",
            )
            self.assertEqual(
                candidate.packet_path,
                program_root / "increments/ARCHIVE-INDEX/review-packet.md",
            )
            evidence = json.loads(candidate.evidence_bytes)
            self.assertEqual(
                tuple(item["scope"] for item in evidence["reports"]),
                ("requirements", "architecture", "test-evidence"),
            )
            self.assertEqual(evidence["final_verification"]["unresolved_material_findings"], 0)
            self.assertIn(b"awaiting-diff-approval", candidate.packet_bytes)
        finally:
            fixture.close()

    def test_every_review_prefix_is_discovered_and_exact_retry_completes(self) -> None:
        for failure_label in (
            "review-evidence",
            "review-packet",
            "verified-status",
            "awaiting-diff-status",
        ):
            with self.subTest(label=failure_label):
                fixture, program_root, observation = reviewing_program()
                try:
                    def interrupt(label: str) -> None:
                        if label == failure_label:
                            raise RuntimeError("injected review interruption")

                    with mock.patch.object(REVIEW, "_after_persist", side_effect=interrupt):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            REVIEW.persist_review_preparation(program_root, observation)
                    expected = (
                        "resume"
                        if failure_label == "awaiting-diff-status"
                        else "review-preparation-retry-ready"
                    )
                    discovered = self.discover(fixture)
                    self.assertEqual(discovered["disposition"], expected, discovered)
                    receipt = REVIEW.persist_review_preparation(program_root, observation)
                    self.assertEqual(receipt.increment_state, "awaiting-diff-approval")
                    completed = repository_snapshot(program_root)
                    recovered = REVIEW.persist_review_preparation(program_root, observation)
                    self.assertTrue(recovered.recovered)
                    self.assertEqual(repository_snapshot(program_root), completed)
                finally:
                    fixture.close()

    def test_every_divergent_review_prefix_is_preserved_and_stops(self) -> None:
        for failure_label in (
            "review-evidence",
            "review-packet",
            "verified-status",
            "awaiting-diff-status",
        ):
            with self.subTest(label=failure_label):
                fixture, program_root, observation = reviewing_program()
                try:
                    def interrupt(label: str) -> None:
                        if label == failure_label:
                            raise RuntimeError("injected review interruption")

                    with mock.patch.object(REVIEW, "_after_persist", side_effect=interrupt):
                        with self.assertRaises(RuntimeError):
                            REVIEW.persist_review_preparation(program_root, observation)
                    if failure_label == "review-evidence":
                        target = program_root / "increments/ARCHIVE-INDEX/review-evidence.json"
                        target.write_bytes(target.read_bytes() + b" ")
                    elif failure_label == "review-packet":
                        target = program_root / "increments/ARCHIVE-INDEX/review-packet.md"
                        target.write_bytes(target.read_bytes() + b"divergent\n")
                    else:
                        target = program_root / "state/status.json"
                        value = json.loads(target.read_text(encoding="utf-8"))
                        value["transition_authority"]["event_id"] = "DIVERGENT"
                        target.write_bytes(canonical_json(value))
                    before = repository_snapshot(program_root)
                    discovered = self.discover(fixture)
                    self.assertEqual(
                        discovered["disposition"],
                        "review-preparation-recovery-required",
                        discovered,
                    )
                    with self.assertRaises(ValueError):
                        REVIEW.persist_review_preparation(program_root, observation)
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_missing_or_unsafe_raw_report_blocks_reviewing_transition(self) -> None:
        mutations = (
            (
                "missing raw",
                lambda fixture: (fixture.repository / "reviews/requirements.json").unlink(),
                "missing Create path",
            ),
            (
                "symlink raw",
                lambda fixture: (
                    (fixture.repository / "reviews/requirements.json").unlink(),
                    (fixture.repository / "reviews/requirements.json").symlink_to(
                        "architecture.json"
                    ),
                ),
                "execution path is unsafe",
            ),
        )
        for label, mutate, message in mutations:
            with self.subTest(label=label):
                fixture, program_root, _observation = implementing_program()
                try:
                    mutate(fixture)
                    changed = ACTIVATION.inspect_repository(
                        fixture.repository, fixture.head
                    ).observation
                    before = repository_snapshot(program_root)
                    with self.assertRaisesRegex(ValueError, message):
                        ACTIVATION.advance_execution_state(
                            program_root, "reviewing", changed
                        )
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_replayed_unresolved_or_nonzero_raw_report_fails_before_review_writes(self) -> None:
        cases = (
            (
                lambda fixture: self.change_raw(
                    fixture, "requirements", increment_id="ARCHIVE-OTHER"
                ),
                "replayed from another",
            ),
            (lambda fixture: self.add_open_finding(fixture), "unresolved material findings"),
            (lambda fixture: self.change_verification_exit(fixture), "exit must be integer zero"),
            (lambda fixture: self.make_verification_stale(fixture), "after remediation and review"),
        )
        for mutate, message in cases:
            with self.subTest(message=message):
                fixture, program_root, observation = reviewing_program(mutate)
                try:
                    before = repository_snapshot(program_root)
                    with self.assertRaisesRegex(ValueError, message):
                        REVIEW.build_review_preparation(program_root, observation)
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    @staticmethod
    def change_raw(fixture: BootstrapFixture, scope: str, **changes: object) -> None:
        path = fixture.repository / f"reviews/{scope}.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value.update(changes)
        path.write_bytes(canonical_json(value))

    def add_open_finding(self, fixture: BootstrapFixture) -> None:
        self.change_raw(
            fixture,
            "requirements",
            findings=[
                {
                    "finding_id": "F-OPEN",
                    "report_id": "requirements-initial",
                    "scope": "requirements",
                    "classification": "material",
                    "summary": "review found a material defect",
                    "evidence": "exact evidence",
                    "impact": "requested behavior is not met",
                    "confidence": "high",
                    "remediation": "repair before diff approval",
                    "disposition": "open",
                    "affected_requirement_or_invariant": "archive output",
                    "severity": "high",
                    "inspection_path": "archive-output.txt",
                    "decision_reference": "none",
                }
            ],
        )

    def repair_open_finding(
        self,
        fixture: BootstrapFixture,
        *,
        finding_id: str = "F-OPEN",
    ) -> None:
        requirements_path = fixture.repository / "reviews/requirements.json"
        requirements = json.loads(requirements_path.read_text(encoding="utf-8"))
        requirements.update(
            report_id="requirements-follow-up",
            follow_up_for_finding_ids=[finding_id],
            persisted_at="2026-08-18T10:30:00Z",
            reconciled_at="2026-08-18T10:40:00Z",
            findings=[
                {
                    "finding_id": finding_id,
                    "report_id": "requirements-follow-up",
                    "scope": "requirements",
                    "classification": "material",
                    "summary": "review found a material defect",
                    "evidence": "exact evidence",
                    "impact": "requested behavior is not met",
                    "confidence": "high",
                    "remediation": "repair before diff approval",
                    "disposition": "repaired",
                    "affected_requirement_or_invariant": "archive output",
                    "severity": "high",
                    "inspection_path": "archive-output.txt",
                    "decision_reference": "none",
                }
            ],
        )
        requirements_path.write_bytes(canonical_json(requirements))

        evidence_path = fixture.repository / "reviews/test-evidence.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence["remediation_cycles"] = [
            {
                "cycle_id": "repair-open-finding",
                "finding_ids": [finding_id],
                "started_at": "2026-08-18T10:15:00Z",
                "completed_at": "2026-08-18T10:20:00Z",
                "regression_command": "python3 -m unittest tests.test_archive_output",
                "intended_failure": "archive output failed its requirement",
                "observed_failure": "archive output failed its requirement",
                "repair": "corrected the archive output",
                "verification_command": "python3 -m unittest tests.test_archive_output",
                "verification_result": "passed with exit 0",
                "renewed_report_ids": ["requirements-follow-up"],
                "changed_paths": ["archive-output.txt"],
                "affected_scopes": ["requirements"],
            }
        ]
        evidence_path.write_bytes(canonical_json(evidence))

    def test_material_finding_round_trip_returns_to_diff_gate(self) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            remediation = REVIEW.persist_review_remediation(program_root, observation)
            self.assertEqual(remediation.increment_state, "remediating")
            self.assertEqual(remediation.unresolved_finding_ids, ("F-OPEN",))

            (fixture.repository / "archive-output.txt").write_text(
                "repaired archive output\n", encoding="utf-8"
            )
            self.repair_open_finding(fixture)
            repaired = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation

            returned = REVIEW.return_review_to_reviewing(program_root, repaired)
            self.assertEqual(returned.increment_state, "reviewing")
            completed = REVIEW.persist_review_preparation(program_root, repaired)
            self.assertEqual(completed.increment_state, "awaiting-diff-approval")

            evidence = json.loads(
                (program_root / "increments/ARCHIVE-INDEX/review-evidence.json")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(
                tuple(item["report_id"] for item in evidence["reports"]),
                (
                    "requirements-initial",
                    "architecture-initial",
                    "test-evidence-initial",
                    "requirements-follow-up",
                ),
            )
            self.assertEqual(evidence["findings"][0]["finding_id"], "F-OPEN")
            self.assertEqual(evidence["findings"][0]["disposition"], "repaired")
            self.assertEqual(
                evidence["findings"][0]["evidence"], "exact evidence"
            )
            self.assertEqual(
                evidence["findings"][0]["impact"],
                "requested behavior is not met",
            )
            self.assertEqual(
                evidence["findings"][0]["remediation"],
                "repair before diff approval",
            )
            self.assertEqual(
                evidence["remediation_cycles"][0]["finding_ids"], ["F-OPEN"]
            )
        finally:
            fixture.close()

    def test_review_remediation_rejects_incomplete_follow_up_without_status_write(
        self,
    ) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            REVIEW.persist_review_remediation(program_root, observation)
            (fixture.repository / "archive-output.txt").write_text(
                "changed but not reviewed\n", encoding="utf-8"
            )
            self.repair_open_finding(fixture, finding_id="F-OTHER")
            changed = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation
            status_path = program_root / "state/status.json"
            before = status_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "unknown initial finding"):
                REVIEW.return_review_to_reviewing(program_root, changed)

            self.assertEqual(status_path.read_bytes(), before)
        finally:
            fixture.close()

    def test_review_remediation_rejects_unrelated_same_id_follow_up(self) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            REVIEW.persist_review_remediation(program_root, observation)
            (fixture.repository / "archive-output.txt").write_text(
                "repaired archive output\n", encoding="utf-8"
            )
            self.repair_open_finding(fixture)
            requirements_path = fixture.repository / "reviews/requirements.json"
            requirements = json.loads(
                requirements_path.read_text(encoding="utf-8")
            )
            requirements["findings"][0]["summary"] = "unrelated replacement issue"
            requirements_path.write_bytes(canonical_json(requirements))
            repaired = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation
            status_path = program_root / "state/status.json"
            before = status_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "does not match initial finding"):
                REVIEW.return_review_to_reviewing(program_root, repaired)

            self.assertEqual(status_path.read_bytes(), before)
        finally:
            fixture.close()

    def test_review_remediation_rejects_unreferenced_follow_up_finding(self) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            REVIEW.persist_review_remediation(program_root, observation)
            (fixture.repository / "archive-output.txt").write_text(
                "repaired archive output\n", encoding="utf-8"
            )
            self.repair_open_finding(fixture)
            requirements_path = fixture.repository / "reviews/requirements.json"
            requirements = json.loads(
                requirements_path.read_text(encoding="utf-8")
            )
            requirements["findings"].append(
                {
                    "finding_id": "F-NEW",
                    "report_id": "requirements-follow-up",
                    "scope": "requirements",
                    "classification": "material",
                    "summary": "new unrelated issue",
                    "evidence": "new evidence",
                    "impact": "new impact",
                    "confidence": "high",
                    "remediation": "new remediation",
                    "disposition": "open",
                    "affected_requirement_or_invariant": "different invariant",
                    "severity": "high",
                    "inspection_path": "archive-output.txt",
                    "decision_reference": "none",
                }
            )
            requirements_path.write_bytes(canonical_json(requirements))
            repaired = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation
            status_path = program_root / "state/status.json"
            before = status_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "unreferenced finding"):
                REVIEW.return_review_to_reviewing(program_root, repaired)

            self.assertEqual(status_path.read_bytes(), before)
        finally:
            fixture.close()

    def test_review_remediation_status_boundaries_are_idempotent(self) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            first = REVIEW.persist_review_remediation(program_root, observation)
            second = REVIEW.persist_review_remediation(program_root, observation)
            self.assertFalse(first.recovered)
            self.assertTrue(second.recovered)

            (fixture.repository / "archive-output.txt").write_text(
                "repaired archive output\n", encoding="utf-8"
            )
            self.repair_open_finding(fixture)
            repaired = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation
            first_return = REVIEW.return_review_to_reviewing(program_root, repaired)
            second_return = REVIEW.return_review_to_reviewing(program_root, repaired)
            self.assertFalse(first_return.recovered)
            self.assertTrue(second_return.recovered)
        finally:
            fixture.close()

    def test_divergent_review_remediation_status_is_preserved_and_stops(self) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            REVIEW.persist_review_remediation(program_root, observation)
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["transition_authority"]["event_id"] = "DIVERGENT"
            status_path.write_bytes(canonical_json(status))
            before = status_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "transition authority"):
                REVIEW.persist_review_remediation(program_root, observation)

            self.assertEqual(status_path.read_bytes(), before)
        finally:
            fixture.close()

    def test_malformed_rebound_remediation_status_uses_typed_recovery_error(
        self,
    ) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            REVIEW.persist_review_remediation(program_root, observation)
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            binding = status["review_remediation_binding"]
            binding.pop("initial_product_delta_sha256")
            status["review_binding"]["candidate_sha256"] = None
            status["transition_authority"]["event_id"] = REVIEW._identifier(
                "review-remediation", binding
            )
            status_path.write_bytes(canonical_json(status))
            before = status_path.read_bytes()
            self.assertIn(
                "remediating state requires an exact review remediation binding",
                REVIEW.validate_state_authority(program_root, observation),
            )

            with self.assertRaisesRegex(
                ValueError, "review-remediation-recovery-required"
            ):
                REVIEW.persist_review_remediation(program_root, observation)

            self.assertEqual(status_path.read_bytes(), before)
        finally:
            fixture.close()

    def test_retained_review_remediation_history_is_digest_bound(self) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            REVIEW.persist_review_remediation(program_root, observation)
            (fixture.repository / "archive-output.txt").write_text(
                "repaired archive output\n", encoding="utf-8"
            )
            self.repair_open_finding(fixture)
            repaired = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation
            REVIEW.return_review_to_reviewing(program_root, repaired)

            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["review_remediation_binding"]["raw_report_bindings"][0][
                "sha256"
            ] = "0" * 64
            status_path.write_bytes(canonical_json(status))
            before = repository_snapshot(program_root)

            self.assertIn(
                "review remediation history binding is invalid",
                REVIEW.validate_state_authority(program_root, repaired),
            )
            with self.assertRaisesRegex(ValueError, "history binding"):
                REVIEW.build_review_preparation(program_root, repaired)
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def change_verification_exit(self, fixture: BootstrapFixture) -> None:
        path = fixture.repository / "reviews/test-evidence.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["final_verification"]["commands"][0]["exit_code"] = 1
        path.write_bytes(canonical_json(value))

    def make_verification_stale(self, fixture: BootstrapFixture) -> None:
        path = fixture.repository / "reviews/test-evidence.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["final_verification"]["commands"][0]["completed_at"] = (
            "2026-08-18T09:00:00Z"
        )
        path.write_bytes(canonical_json(value))

    def test_changed_product_delta_and_invalid_packet_rendering_fail_closed(self) -> None:
        fixture, program_root, observation = reviewing_program()
        try:
            (fixture.repository / "archive-output.txt").write_text(
                "changed after reviewing\n", encoding="utf-8"
            )
            changed = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation
            with self.assertRaisesRegex(ValueError, "product delta differs"):
                REVIEW.build_review_preparation(program_root, changed)
        finally:
            fixture.close()

        fixture, program_root, observation = reviewing_program()
        try:
            with mock.patch.object(REVIEW, "render_review_packet", return_value="# invalid\n"):
                with self.assertRaisesRegex(ValueError, "deterministic rendering"):
                    REVIEW.build_review_preparation(program_root, observation)
        finally:
            fixture.close()

    def test_direct_generic_reviewed_transition_is_quarantined(self) -> None:
        fixture, program_root, observation = reviewing_program()
        try:
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            request = REVIEW.TransitionRequest(
                expected_status_sha256=REVIEW.sha256_file(status_path),
                expected_state_sequence=status["state_sequence"],
                target_program_state="active",
                target_increment_id="ARCHIVE-INDEX",
                target_increment_state="verified",
                transition_event_id="GENERIC-REVIEW",
                action_authorization_id=status["execution_authorization"]["authorization_id"],
                evidence={"action_scope": status["execution_authorization"]["scope"]},
                authority_kind="action-authorization",
            )
            before = status_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "review-preparation-required"):
                REVIEW.apply_state_transition(program_root, request, observation)
            self.assertEqual(status_path.read_bytes(), before)
        finally:
            fixture.close()

    def test_direct_generic_review_remediation_edges_are_quarantined(self) -> None:
        fixture, program_root, observation = reviewing_program(self.add_open_finding)
        try:
            status_path = program_root / "state/status.json"

            def request(target: str):
                status = json.loads(status_path.read_text(encoding="utf-8"))
                return REVIEW.TransitionRequest(
                    expected_status_sha256=REVIEW.sha256_file(status_path),
                    expected_state_sequence=status["state_sequence"],
                    target_program_state="active",
                    target_increment_id="ARCHIVE-INDEX",
                    target_increment_state=target,
                    transition_event_id="GENERIC-REMEDIATION",
                    action_authorization_id=status["execution_authorization"][
                        "authorization_id"
                    ],
                    evidence={
                        "action_scope": status["execution_authorization"]["scope"]
                    },
                    authority_kind="action-authorization",
                )

            before = status_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "typed-review-remediation-required"):
                REVIEW.apply_state_transition(
                    program_root, request("remediating"), observation
                )
            self.assertEqual(status_path.read_bytes(), before)

            REVIEW.persist_review_remediation(program_root, observation)
            remediating = status_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "typed-review-remediation-required"):
                REVIEW.apply_state_transition(
                    program_root, request("reviewing"), observation
                )
            self.assertEqual(status_path.read_bytes(), remediating)
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
