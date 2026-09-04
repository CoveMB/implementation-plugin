import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import canonical_json, repository_snapshot
from tests.test_diff_disposition import DIFF, awaiting_diff_program


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_closure.py"
DISCOVERY_PATH = SCRIPT_ROOT / "program_discovery.py"

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC = importlib.util.spec_from_file_location("program_closure", SCRIPT_PATH)
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load program closure from {SCRIPT_PATH}")
    CLOSURE = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = CLOSURE
    SPEC.loader.exec_module(CLOSURE)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def accepted_program():
    fixture, program_root, observation = awaiting_diff_program()
    prompt = DIFF.render_diff_disposition_prompt(program_root)
    DIFF.persist_accept_stop(program_root, prompt, observation)
    return fixture, program_root, observation


class ProgramClosureTests(unittest.TestCase):
    def discover(self, fixture) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, str(DISCOVERY_PATH), "discover", str(fixture.repository)],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertIn(completed.returncode, {0, 1}, completed.stderr)
        return json.loads(completed.stdout)

    def test_preparation_derives_only_manifest_owned_closure_files(self) -> None:
        fixture, program_root, observation = accepted_program()
        try:
            receipt = CLOSURE.prepare_program_closure(program_root, observation)
            self.assertEqual(receipt.program_state, "awaiting-closure-approval")
            self.assertTrue((program_root / "closure/reconciliation.json").is_file())
            self.assertTrue((program_root / "closure/closure-packet.md").is_file())
            self.assertFalse((program_root / "increments/ARCHIVE-INDEX/handoff.md").exists())
            self.assertEqual(
                self.discover(fixture)["disposition"], "closure-approval-ready"
            )
            prompt = CLOSURE.render_program_closure_prompt(program_root)
            self.assertIn("implementation-program-closure-command/v1", prompt)
            self.assertNotIn("commit", prompt.lower())
            self.assertNotIn("pull request", prompt.lower())
        finally:
            fixture.close()

    def test_closure_freshness_orders_timezone_offsets_by_instant(self) -> None:
        fixture, program_root, observation = accepted_program()
        try:
            evidence_path = (
                program_root
                / "increments/ARCHIVE-INDEX/review-evidence.json"
            )
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["reports"][0].update(
                persisted_at="2026-08-18T12:20:00+02:00",
                reconciled_at="2026-08-18T12:30:00+02:00",
            )
            for report in evidence["reports"][1:]:
                report.update(
                    persisted_at="2026-08-18T10:50:00Z",
                    reconciled_at="2026-08-18T11:00:00Z",
                )
            evidence["final_verification"]["commands"][0]["completed_at"] = (
                "2026-08-18T11:15:00Z"
            )
            evidence["final_verification"]["verified_at"] = (
                "2026-08-18T11:20:00Z"
            )
            evidence_path.write_bytes(canonical_json(evidence))

            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            evidence_sha256 = CLOSURE.sha256_file(evidence_path)
            status["review_evidence_binding"]["sha256"] = evidence_sha256
            status["diff_disposition_binding"]["review_evidence_sha256"] = (
                evidence_sha256
            )
            status_path.write_bytes(canonical_json(status))

            try:
                receipt = CLOSURE.prepare_program_closure(program_root, observation)
            except ValueError as error:
                self.fail(f"valid offset chronology was rejected: {error}")

            self.assertEqual(receipt.program_state, "awaiting-closure-approval")
        finally:
            fixture.close()

    def test_malformed_bound_review_evidence_fails_before_closure_writes(self) -> None:
        cases = (
            (
                "commands",
                lambda evidence: evidence["final_verification"].update(
                    commands=[{"command": "incomplete"}]
                ),
            ),
            ("findings", lambda evidence: evidence.update(findings={})),
            (
                "report-pair-array",
                lambda evidence: evidence["reports"].__setitem__(
                    0, list(evidence["reports"][0].items())
                ),
            ),
            (
                "command-pair-array",
                lambda evidence: evidence["final_verification"][
                    "commands"
                ].__setitem__(
                    0,
                    list(
                        evidence["final_verification"]["commands"][0].items()
                    ),
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                fixture, program_root, observation = accepted_program()
                try:
                    evidence_path = (
                        program_root
                        / "increments/ARCHIVE-INDEX/review-evidence.json"
                    )
                    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                    mutate(evidence)
                    evidence_path.write_bytes(canonical_json(evidence))

                    status_path = program_root / "state/status.json"
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    evidence_sha256 = CLOSURE.sha256_file(evidence_path)
                    status["review_evidence_binding"]["sha256"] = evidence_sha256
                    status["diff_disposition_binding"]["review_evidence_sha256"] = (
                        evidence_sha256
                    )
                    status_path.write_bytes(canonical_json(status))

                    before = repository_snapshot(program_root)
                    try:
                        CLOSURE.prepare_program_closure(program_root, observation)
                    except ValueError as error:
                        self.assertEqual(
                            str(error), "review bundle is structurally invalid"
                        )
                    except TypeError as error:
                        self.fail(f"uncontrolled TypeError escaped validation: {error}")
                    else:
                        self.fail("malformed review evidence was accepted")
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_every_exact_prefix_is_retry_safe_and_lost_responses_are_idempotent(self) -> None:
        cases = (
            ("reconciliation", "prepare", "closure-preparation-retry-ready"),
            ("packet", "prepare", "closure-preparation-retry-ready"),
            ("awaiting-closure-status", "prepare", "closure-approval-ready"),
            ("closure-approval", "approve", "closure-approval-retry-ready"),
            ("closed-status", "approve", "terminal-programs"),
        )
        for failure_label, phase, expected_disposition in cases:
            with self.subTest(label=failure_label):
                fixture, program_root, observation = accepted_program()
                try:
                    if phase == "prepare":
                        with mock.patch.object(
                            CLOSURE,
                            "_after_persist",
                            side_effect=lambda label: (
                                (_ for _ in ()).throw(RuntimeError("injected"))
                                if label == failure_label
                                else None
                            ),
                        ):
                            with self.assertRaisesRegex(RuntimeError, "injected"):
                                CLOSURE.prepare_program_closure(program_root, observation)
                        self.assertEqual(
                            self.discover(fixture)["disposition"], expected_disposition
                        )
                        receipt = CLOSURE.prepare_program_closure(program_root, observation)
                        self.assertEqual(
                            receipt.program_state, "awaiting-closure-approval"
                        )
                    else:
                        CLOSURE.prepare_program_closure(program_root, observation)
                        prompt = CLOSURE.render_program_closure_prompt(program_root)
                        with mock.patch.object(
                            CLOSURE,
                            "_after_persist",
                            side_effect=lambda label: (
                                (_ for _ in ()).throw(RuntimeError("injected"))
                                if label == failure_label
                                else None
                            ),
                        ):
                            with self.assertRaisesRegex(RuntimeError, "injected"):
                                CLOSURE.persist_program_closure(
                                    program_root, prompt, observation
                                )
                        self.assertEqual(
                            self.discover(fixture)["disposition"], expected_disposition
                        )
                        receipt = CLOSURE.persist_program_closure(
                            program_root, prompt, observation
                        )
                        self.assertEqual(receipt.program_state, "closed")
                        complete = repository_snapshot(program_root)
                        replay = CLOSURE.persist_program_closure(
                            program_root, prompt, observation
                        )
                        self.assertTrue(replay.recovered)
                        self.assertEqual(repository_snapshot(program_root), complete)
                finally:
                    fixture.close()

    def test_divergent_preparation_and_approval_prefixes_are_preserved(self) -> None:
        cases = ("reconciliation", "packet", "closure-approval")
        for failure_label in cases:
            with self.subTest(label=failure_label):
                fixture, program_root, observation = accepted_program()
                try:
                    if failure_label in {"reconciliation", "packet"}:
                        with mock.patch.object(
                            CLOSURE,
                            "_after_persist",
                            side_effect=lambda label: (
                                (_ for _ in ()).throw(RuntimeError("injected"))
                                if label == failure_label
                                else None
                            ),
                        ):
                            with self.assertRaises(RuntimeError):
                                CLOSURE.prepare_program_closure(
                                    program_root, observation
                                )
                        target = program_root / (
                            "closure/reconciliation.json"
                            if failure_label == "reconciliation"
                            else "closure/closure-packet.md"
                        )
                        target.write_bytes(target.read_bytes() + b" ")
                        operation = lambda: CLOSURE.prepare_program_closure(
                            program_root, observation
                        )
                        expected = "closure-preparation-recovery-required"
                    else:
                        CLOSURE.prepare_program_closure(program_root, observation)
                        prompt = CLOSURE.render_program_closure_prompt(program_root)
                        with mock.patch.object(
                            CLOSURE,
                            "_after_persist",
                            side_effect=lambda label: (
                                (_ for _ in ()).throw(RuntimeError("injected"))
                                if label == failure_label
                                else None
                            ),
                        ):
                            with self.assertRaises(RuntimeError):
                                CLOSURE.persist_program_closure(
                                    program_root, prompt, observation
                                )
                        approvals = program_root / "state/approvals.jsonl"
                        records = approvals.read_text(encoding="utf-8").splitlines()
                        value = json.loads(records[-1])
                        value["base_seed_sha256"] = "0" * 64
                        records[-1] = json.dumps(
                            value, separators=(",", ":"), sort_keys=True
                        )
                        approvals.write_text(
                            "\n".join(records) + "\n", encoding="utf-8"
                        )
                        operation = lambda: CLOSURE.persist_program_closure(
                            program_root, prompt, observation
                        )
                        expected = "closure-approval-recovery-required"
                    before = repository_snapshot(program_root)
                    self.assertEqual(self.discover(fixture)["disposition"], expected)
                    with self.assertRaises(ValueError):
                        operation()
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_invalid_finality_allocation_reconciliation_and_delta_stop_before_writes(self) -> None:
        cases = (
            ("successor", {"successor_id": "ARCHIVE-VERIFY"}),
            ("unresolved-requirement", {"unresolved_requirements": 1}),
            ("unresolved-finding", {"unresolved_material_findings": 1}),
            ("unresolved-amendment", {"unresolved_amendments": 1}),
            ("unowned-deferral", {"unowned_deferrals": 1}),
            ("stale-verification", {"verification_is_fresh": False}),
            ("unallocated-path", {"paths_allocated": False}),
        )
        for label, blockers in cases:
            with self.subTest(label=label):
                fixture, program_root, observation = accepted_program()
                try:
                    before = repository_snapshot(program_root)
                    with mock.patch.object(
                        CLOSURE, "_closure_preconditions", return_value=blockers
                    ):
                        with self.assertRaises(ValueError):
                            CLOSURE.prepare_program_closure(
                                program_root, observation
                            )
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_symlink_and_changed_accepted_delta_stop_before_closure_writes(self) -> None:
        for case in ("symlink", "delta"):
            with self.subTest(case=case):
                fixture, program_root, observation = accepted_program()
                try:
                    if case == "symlink":
                        closure_root = program_root / "closure"
                        closure_root.mkdir()
                        (closure_root / "reconciliation.json").symlink_to(
                            program_root / "manifest.json"
                        )
                    else:
                        (fixture.repository / "archive-output.txt").write_text(
                            "changed after acceptance\n", encoding="utf-8"
                        )
                        observation = CLOSURE.inspect_repository(
                            fixture.repository, fixture.head
                        ).observation
                    before = repository_snapshot(program_root)
                    with self.assertRaises(ValueError):
                        CLOSURE.prepare_program_closure(program_root, observation)
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_generic_new_program_closure_edges_cannot_bypass_typed_sink(self) -> None:
        fixture, program_root, observation = accepted_program()
        try:
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            request = CLOSURE.TransitionRequest(
                expected_status_sha256=CLOSURE.sha256_file(status_path),
                expected_state_sequence=status["state_sequence"],
                target_program_state="awaiting-closure-approval",
                target_increment_id=status["current_increment_id"],
                target_increment_state="accepted",
                transition_event_id="GENERIC-CLOSURE",
                action_authorization_id=status["execution_authorization"][
                    "authorization_id"
                ],
                evidence={"action_scope": "prepare closure"},
            )
            with self.assertRaisesRegex(ValueError, "typed-program-closure-required"):
                CLOSURE.apply_state_transition(program_root, request, observation)
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
