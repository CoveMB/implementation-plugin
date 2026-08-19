import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import canonical_json, repository_snapshot
from tests.test_program_review import REVIEW as PROGRAM_REVIEW
from tests.test_program_review import reviewing_program


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "diff_disposition.py"
DISCOVERY_PATH = SCRIPT_ROOT / "program_discovery.py"

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC = importlib.util.spec_from_file_location("diff_disposition", SCRIPT_PATH)
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load diff disposition from {SCRIPT_PATH}")
    DIFF = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = DIFF
    SPEC.loader.exec_module(DIFF)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def awaiting_diff_program():
    fixture, program_root, observation = reviewing_program()
    PROGRAM_REVIEW.persist_review_preparation(program_root, observation)
    return fixture, program_root, observation


class DiffDispositionTests(unittest.TestCase):
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

    def test_prompt_always_offers_only_accept_and_stop_without_successor_input(self) -> None:
        fixture, program_root, _observation = awaiting_diff_program()
        try:
            loaded_paths: list[str] = []
            real_load = DIFF.load_json_object

            def recording_load(path):
                loaded_paths.append(str(path))
                return real_load(path)

            with mock.patch.object(DIFF, "load_json_object", side_effect=recording_load):
                prompt = DIFF.render_diff_disposition_prompt(program_root)
            self.assertEqual(prompt.count("Accept and stop."), 1)
            self.assertNotIn("continue", prompt.lower())
            self.assertFalse(any("traceability" in path for path in loaded_paths))
            candidate = DIFF.build_diff_acceptance_candidate(
                program_root, _observation
            )
            binding = candidate.accepted_status["diff_disposition_binding"]
            self.assertNotIn("accepted_status_sha256", binding)
            self.assertNotIn("submitted_prompt_sha256", binding)
        finally:
            fixture.close()

    def test_approval_only_and_status_lost_response_prefixes_are_exactly_retry_safe(self) -> None:
        for failure_label in ("diff-approval", "accepted-status"):
            with self.subTest(label=failure_label):
                fixture, program_root, observation = awaiting_diff_program()
                try:
                    prompt = DIFF.render_diff_disposition_prompt(program_root)

                    def interrupt(label: str) -> None:
                        if label == failure_label:
                            raise RuntimeError("injected diff disposition interruption")

                    with mock.patch.object(DIFF, "_after_persist", side_effect=interrupt):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            DIFF.persist_accept_stop(program_root, prompt, observation)
                    expected = (
                        "increment-acceptance-retry-ready"
                        if failure_label == "diff-approval"
                        else "accepted-stop"
                    )
                    discovered = self.discover(fixture)
                    self.assertEqual(discovered["disposition"], expected, discovered)
                    receipt = DIFF.persist_accept_stop(program_root, prompt, observation)
                    self.assertEqual(receipt.increment_state, "accepted")
                    complete = repository_snapshot(program_root)
                    replay = DIFF.persist_accept_stop(program_root, prompt, observation)
                    self.assertTrue(replay.recovered)
                    self.assertEqual(repository_snapshot(program_root), complete)
                finally:
                    fixture.close()

    def test_prompt_status_review_and_product_drift_fail_before_acceptance_writes(self) -> None:
        cases = ("prompt", "status", "review", "product")
        for case in cases:
            with self.subTest(case=case):
                fixture, program_root, observation = awaiting_diff_program()
                try:
                    prompt = DIFF.render_diff_disposition_prompt(program_root)
                    if case == "prompt":
                        prompt += "tampered\n"
                    elif case == "status":
                        status_path = program_root / "state/status.json"
                        status = json.loads(status_path.read_text(encoding="utf-8"))
                        status["state_sequence"] += 1
                        status_path.write_bytes(canonical_json(status))
                    elif case == "review":
                        evidence = program_root / "increments/ARCHIVE-INDEX/review-evidence.json"
                        evidence.write_bytes(evidence.read_bytes() + b" ")
                    else:
                        (fixture.repository / "archive-output.txt").write_text(
                            "changed after diff prompt\n", encoding="utf-8"
                        )
                        observation = DIFF.inspect_repository(
                            fixture.repository, fixture.head
                        ).observation
                    approvals = (program_root / "state/approvals.jsonl").read_bytes()
                    with self.assertRaises(ValueError):
                        DIFF.persist_accept_stop(program_root, prompt, observation)
                    self.assertEqual(
                        (program_root / "state/approvals.jsonl").read_bytes(), approvals
                    )
                finally:
                    fixture.close()

    def test_conflicting_approval_is_preserved_and_discovery_requires_recovery(self) -> None:
        fixture, program_root, observation = awaiting_diff_program()
        try:
            prompt = DIFF.render_diff_disposition_prompt(program_root)

            def interrupt(label: str) -> None:
                if label == "diff-approval":
                    raise RuntimeError("injected")

            with mock.patch.object(DIFF, "_after_persist", side_effect=interrupt):
                with self.assertRaises(RuntimeError):
                    DIFF.persist_accept_stop(program_root, prompt, observation)
            approvals_path = program_root / "state/approvals.jsonl"
            lines = approvals_path.read_text(encoding="utf-8").splitlines()
            record = json.loads(lines[-1])
            record["base_seed_sha256"] = "0" * 64
            lines[-1] = json.dumps(record, separators=(",", ":"), sort_keys=True)
            approvals_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            before = repository_snapshot(program_root)
            discovered = self.discover(fixture)
            self.assertEqual(
                discovered["disposition"],
                "increment-acceptance-recovery-required",
                discovered,
            )
            with self.assertRaisesRegex(ValueError, "conflicting approval"):
                DIFF.persist_accept_stop(program_root, prompt, observation)
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_generic_new_program_acceptance_cannot_bypass_typed_sink(self) -> None:
        fixture, program_root, observation = awaiting_diff_program()
        try:
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            request = DIFF.TransitionRequest(
                expected_status_sha256=DIFF.sha256_file(status_path),
                expected_state_sequence=status["state_sequence"],
                target_program_state="active",
                target_increment_id="ARCHIVE-INDEX",
                target_increment_state="accepted",
                transition_event_id="GENERIC-DIFF-ACCEPTANCE",
                action_authorization_id=None,
                evidence={"action_scope": "accept current increment"},
                authority_kind="approval-event",
            )
            before = status_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "typed-diff-disposition-required"):
                DIFF.apply_state_transition(program_root, request, observation)
            self.assertEqual(status_path.read_bytes(), before)
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
