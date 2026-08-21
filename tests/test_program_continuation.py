import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import repository_snapshot
from tests.test_diff_disposition import DIFF, awaiting_diff_program


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_continuation.py"
DISCOVERY_PATH = SCRIPT_ROOT / "program_discovery.py"

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC = importlib.util.spec_from_file_location("program_continuation", SCRIPT_PATH)
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load program continuation from {SCRIPT_PATH}")
    CONTINUATION = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = CONTINUATION
    SPEC.loader.exec_module(CONTINUATION)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


class ProgramContinuationTests(unittest.TestCase):
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

    def test_extension_binds_exact_pre_record_projection_and_live_delta(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            acceptance = DIFF.build_diff_acceptance_candidate(
                program_root, observation
            )
            extension = CONTINUATION.build_continuation_extension(
                program_root, acceptance, observation
            )
            self.assertIsNotNone(extension)
            projection = dict(extension.successor_projection)
            self.assertEqual(
                set(projection),
                {
                    "schema_version",
                    "program_id",
                    "program_revision",
                    "current_increment_id",
                    "successor_increment_id",
                    "prior_status_sha256",
                    "prior_status_sequence",
                    "checkpoint_id",
                    "approval_event_id",
                    "successor_brief_sha256",
                    "accepted_product_delta_sha256",
                    "successor_approval_mode",
                    "selected_workspace",
                    "workspace_selection_sha256",
                    "inherited_workspace_sha256",
                    "allowed_conditional_action_ceiling",
                    "rollover_authorization_id",
                    "successor_grant_id",
                },
            )
            for forbidden in (
                "accepted_status_sha256",
                "submitted_prompt_sha256",
                "action_authorization_sha256",
                "successor_grant_sha256",
                "rollover_sha256",
                "successor_status_sha256",
            ):
                self.assertNotIn(forbidden, projection)
            self.assertEqual(
                tuple(item.path for item in extension.accepted_product_delta),
                tuple(sorted(item.path for item in extension.accepted_product_delta)),
            )
        finally:
            fixture.close()

    def test_accept_continue_identifiers_are_topological_and_order_independent(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            acceptance = DIFF.build_diff_acceptance_candidate(
                program_root, observation
            )
            extension = CONTINUATION.build_continuation_extension(
                program_root, acceptance, observation
            )
            candidate = CONTINUATION.build_accept_continue_candidate(
                acceptance, extension
            )
            binding = candidate.accepted_status["diff_disposition_binding"]
            self.assertEqual(binding["decision"], "accept-continue")
            self.assertEqual(
                binding["successor_authority_projection"],
                extension.successor_projection,
            )
            self.assertNotEqual(candidate.checkpoint_id, acceptance.checkpoint_id)
            self.assertNotEqual(
                candidate.approval_event_id, acceptance.approval_event_id
            )
            reordered = dict(reversed(tuple(extension.successor_projection.items())))
            self.assertEqual(
                CONTINUATION.successor_projection_sha256(reordered),
                CONTINUATION.successor_projection_sha256(
                    extension.successor_projection
                ),
            )
        finally:
            fixture.close()

    def test_immediate_acceptance_prefixes_are_discoverable_and_retryable(self) -> None:
        for failure_label, expected in (
            ("diff-approval", "increment-acceptance-retry-ready"),
            ("accepted-status", "accepted-continuation-retry-ready"),
        ):
            with self.subTest(failure_label=failure_label):
                fixture, program_root, observation = awaiting_diff_program(
                    {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
                )
                try:
                    prompt = CONTINUATION.render_accept_continue_prompt(program_root)

                    def interrupt(
                        label: str, *, expected_label: str = failure_label
                    ) -> None:
                        if label == expected_label:
                            raise RuntimeError("injected continuation acceptance failure")

                    with mock.patch.object(DIFF, "_after_persist", side_effect=interrupt):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            DIFF._persist_diff_acceptance_prefix(
                                program_root, prompt, observation
                            )
                    discovered = self.discover(fixture)
                    self.assertEqual(discovered["disposition"], expected, discovered)
                    receipt = DIFF._persist_diff_acceptance_prefix(
                        program_root, prompt, observation
                    )
                    self.assertEqual(receipt.decision, "accept-continue")
                    self.assertEqual(receipt.increment_state, "accepted")
                finally:
                    fixture.close()

    def test_later_continuation_uses_a_distinct_read_only_prompt_domain(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            stop_prompt = "Accept and stop.\n\n" + DIFF.build_diff_acceptance_candidate(
                program_root, observation
            ).prompt
            stopped = DIFF.persist_accept_stop(program_root, stop_prompt, observation)
            before = repository_snapshot(program_root)
            prompt = CONTINUATION.render_accepted_state_continuation_prompt(
                program_root
            )
            command = CONTINUATION.validate_submitted_continuation_prompt(
                program_root, prompt
            )
            self.assertEqual(
                command.schema_version,
                CONTINUATION.ACCEPTED_STATE_CONTINUATION_SCHEMA,
            )
            self.assertNotEqual(command.checkpoint_id, stopped.approval_event_id)
            self.assertNotIn(stop_prompt, prompt)
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_stop_prompt_replay_never_creates_continuation_authority(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            action_authorizations = (
                program_root / "state/action-authorizations.jsonl"
            ).read_bytes()
            increment_grants = (
                program_root / "state/increment-grants.jsonl"
            ).read_bytes()
            stop_prompt = "Accept and stop.\n\n" + DIFF.build_diff_acceptance_candidate(
                program_root, observation
            ).prompt
            DIFF.persist_accept_stop(program_root, stop_prompt, observation)
            before = repository_snapshot(program_root)
            replay = DIFF.persist_accept_stop(program_root, stop_prompt, observation)
            self.assertTrue(replay.recovered)
            self.assertEqual(repository_snapshot(program_root), before)
            self.assertEqual(
                (program_root / "state/action-authorizations.jsonl").read_bytes(),
                action_authorizations,
            )
            self.assertEqual(
                (program_root / "state/increment-grants.jsonl").read_bytes(),
                increment_grants,
            )
        finally:
            fixture.close()

    def test_later_continuation_stops_without_writes_when_no_successor_exists(self) -> None:
        fixture, program_root, observation = awaiting_diff_program()
        try:
            stop_prompt = "Accept and stop.\n\n" + DIFF.build_diff_acceptance_candidate(
                program_root, observation
            ).prompt
            DIFF.persist_accept_stop(program_root, stop_prompt, observation)
            before = repository_snapshot(program_root)
            with self.assertRaisesRegex(ValueError, "no allocated successor"):
                CONTINUATION.render_accepted_state_continuation_prompt(program_root)
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_unbound_rollover_row_cannot_satisfy_successor_dependency(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-BLOCKER",)}
        )
        try:
            acceptance = DIFF.build_diff_acceptance_candidate(
                program_root, observation
            )
            self.assertIsNone(
                CONTINUATION.build_continuation_extension(
                    program_root, acceptance, observation
                )
            )
            rollover_path = program_root / "state/rollovers.jsonl"
            rollover_path.write_text(
                json.dumps(
                    {"current_increment_id": "ARCHIVE-BLOCKER"},
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            before = repository_snapshot(program_root)
            with self.assertRaisesRegex(ValueError, "unbound rollover history"):
                CONTINUATION.build_continuation_extension(
                    program_root, acceptance, observation
                )
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_render_cli_emits_the_exact_accepted_state_prompt_without_writes(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            stop_prompt = "Accept and stop.\n\n" + DIFF.build_diff_acceptance_candidate(
                program_root, observation
            ).prompt
            DIFF.persist_accept_stop(program_root, stop_prompt, observation)
            expected = CONTINUATION.render_accepted_state_continuation_prompt(
                program_root
            )
            before = repository_snapshot(program_root)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "render", str(program_root)],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, expected)
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_accept_stop_validation_is_not_relaxed_for_a_divergent_binding(self) -> None:
        fixture, program_root, observation = awaiting_diff_program()
        try:
            stop_prompt = DIFF.render_diff_disposition_prompt(program_root)
            DIFF.persist_accept_stop(program_root, stop_prompt, observation)
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["diff_disposition_binding"]["approval_event_id"] = "DIVERGENT"
            status_path.write_text(
                json.dumps(status, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError, "accepted status diff disposition binding is invalid"
            ):
                DIFF.build_diff_acceptance_candidate(program_root, observation)
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
