import json
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import repository_snapshot, run_program_discovery
from tests.script_module_support import load_script_module
from tests.test_diff_disposition import DIFF, awaiting_diff_program
from tests.test_program_continuation import CONTINUATION


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_rollover.py"

ROLLOVER = load_script_module("program_rollover", SCRIPT_PATH)


def accepted_continuation_program(domain: str):
    fixture, program_root, observation = awaiting_diff_program(
        {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
    )
    if domain == "immediate":
        prompt = CONTINUATION.render_accept_continue_prompt(program_root)
        DIFF._persist_diff_acceptance_prefix(program_root, prompt, observation)
    elif domain == "accepted-state":
        stop_prompt = "Accept and stop.\n\n" + DIFF.build_diff_acceptance_candidate(
            program_root, observation
        ).prompt
        DIFF.persist_accept_stop(program_root, stop_prompt, observation)
        prompt = CONTINUATION.render_accepted_state_continuation_prompt(program_root)
    else:
        raise ValueError(f"unsupported continuation test domain: {domain}")
    return fixture, program_root, observation, prompt


class ProgramRolloverTests(unittest.TestCase):
    def test_specialist_acceptance_rollover_and_successor_preparation(self):
        from tests.test_blocked_recovery import (
            ACTIVATION, BLOCKED, RECOVERY_RISKS, reviewed_specialist_program,
        )
        from tests.program_bootstrap_support import _exact_plan_bytes

        for recovery in (False, True):
            with self.subTest(recovery=recovery):
                fixture, root, observation = reviewed_specialist_program(recovery=recovery)
                self.addCleanup(fixture.close)
                status = json.loads((root / "state/status.json").read_text())
                allocation = status.get("review_allocation_binding")
                reports = {p: v for p, v in repository_snapshot(fixture.repository).items()
                           if p.startswith("reviews/") and p.endswith(".json")}
                self.assertEqual(self.discover(fixture)["disposition"], "increment-acceptance-retry-ready")
                DIFF.render_diff_disposition_prompt(root)
                stop_prompt = "Accept and stop.\n\n" + DIFF.build_diff_acceptance_candidate(root, observation).prompt
                DIFF.persist_accept_stop(root, stop_prompt, observation)
                prompt = CONTINUATION.render_accepted_state_continuation_prompt(root)
                ROLLOVER.persist_increment_rollover(root, prompt, observation)
                status = json.loads((root / "state/status.json").read_text())
                self.assertNotIn("review_allocation_binding", status)
                self.assertIsNone(BLOCKED.validated_review_allocation_supplement(root, status))
                records = [json.loads(line) for line in (root / "state/rollovers.jsonl").read_text().splitlines()]
                self.assertEqual(records[-1].get("review_allocation_binding"), allocation)
                inherited = ROLLOVER.validated_inherited_paths(root, status, observation)
                self.assertTrue(set(reports).issubset(inherited))
                self.assertEqual(self.discover(fixture)["disposition"], "resume")
                observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
                plan = _exact_plan_bytes(root, observation, RECOVERY_RISKS)
                invalid = plan.replace("- `reviews/ARCHIVE-VERIFY/specialist-provider.json` — exact owned path.\n".encode(), b"")
                before = repository_snapshot(fixture.repository)
                with self.assertRaises(ValueError):
                    ACTIVATION.prepare_exact_plan(root, invalid, observation)
                self.assertEqual(repository_snapshot(fixture.repository), before)
                prepared = ACTIVATION.prepare_exact_plan(root, plan, observation)
                ACTIVATION.materialize_exact_plan(root, prepared.plan_prompt, observation)
                self.assertEqual(self.discover(fixture)["disposition"], "resume")
                self.assertEqual({p: repository_snapshot(fixture.repository)[p] for p in reports}, reports)

    def test_archived_supplement_and_reports_reject_tampering_in_successor(self):
        from tests.test_blocked_recovery import ACTIVATION, reviewed_specialist_program
        from tests.program_bootstrap_support import _exact_plan_bytes, canonical_json

        fixture, root, observation = reviewed_specialist_program(recovery=True)
        self.addCleanup(fixture.close)
        stop_prompt = "Accept and stop.\n\n" + DIFF.build_diff_acceptance_candidate(root, observation).prompt
        DIFF.persist_accept_stop(root, stop_prompt, observation)
        prompt = CONTINUATION.render_accepted_state_continuation_prompt(root)
        ROLLOVER.persist_increment_rollover(root, prompt, observation)
        observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
        plan = _exact_plan_bytes(root, observation)
        omitted = plan.replace("- `reviews/requirements.json` — exact owned path.\n".encode(), b"")
        before = repository_snapshot(fixture.repository)
        with self.assertRaisesRegex(ValueError, "Preserve retained"):
            ACTIVATION.prepare_exact_plan(root, omitted, observation)
        self.assertEqual(repository_snapshot(fixture.repository), before)
        prepared = ACTIVATION.prepare_exact_plan(root, plan, observation)
        ACTIVATION.materialize_exact_plan(root, prepared.plan_prompt, observation)
        ACTIVATION.advance_execution_state(root, "implementing", observation)
        status_path = root / "state/status.json"
        rollover_path = root / "state/rollovers.jsonl"
        status = json.loads(status_path.read_text())
        rollover = json.loads(rollover_path.read_text())
        fresh_report = next(fixture.repository.glob("reviews/recovery-*/specialist-provider.json"))
        targets = {
            "old-report": fixture.repository / "reviews/requirements.json",
            "new-report": fresh_report,
            "origin-resolution": root / "state/block-resolutions.jsonl",
            "missing-archive": rollover_path,
            "downgraded-archive": rollover_path,
        }
        for label, target in targets.items():
            with self.subTest(label=label):
                original = target.read_bytes()
                status_bytes = status_path.read_bytes()
                try:
                    if label.endswith("archive"):
                        changed = dict(rollover)
                        if label == "missing-archive":
                            changed.pop("review_allocation_binding")
                        else:
                            changed["schema_version"] = "implementation-increment-rollover/v1"
                        target.write_bytes(ROLLOVER._canonical_json_line(changed))
                        changed_status = json.loads(status_bytes)
                        changed_status["rollover_binding"]["rollover_sha256"] = ROLLOVER.sha256_file(target)
                        status_path.write_bytes(canonical_json(changed_status))
                    else:
                        target.write_bytes(original + b" ")
                    current = json.loads(status_path.read_text())
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        ROLLOVER.validated_inherited_paths(root, current, observation)
                    self.assertNotEqual(self.discover(fixture)["disposition"], "resume")
                    with self.assertRaises(ValueError):
                        CONTINUATION.render_accepted_state_continuation_prompt(root)
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                finally:
                    target.write_bytes(original)
                    status_path.write_bytes(status_bytes)
        self.assertEqual(self.discover(fixture)["disposition"], "resume")

    def test_supplemented_rollover_prefixes_are_discoverable_and_exact(self):
        from tests.test_blocked_recovery import reviewed_specialist_program

        for boundary in ("action-authorization", "successor-grant", "handoff",
                         "successor-brief", "rollover-record", "successor-status"):
            with self.subTest(boundary=boundary):
                fixture, root, observation = reviewed_specialist_program(recovery=True)
                self.addCleanup(fixture.close)
                stop_prompt = "Accept and stop.\n\n" + DIFF.build_diff_acceptance_candidate(root, observation).prompt
                DIFF.persist_accept_stop(root, stop_prompt, observation)
                prompt = CONTINUATION.render_accepted_state_continuation_prompt(root)
                original_resolutions = (root / "state/block-resolutions.jsonl").read_bytes()

                def interrupt(label):
                    if label == boundary:
                        raise RuntimeError("injected rollover interruption")

                with mock.patch.object(ROLLOVER, "_after_persist", side_effect=interrupt):
                    with self.assertRaisesRegex(RuntimeError, "injected"):
                        ROLLOVER.persist_increment_rollover(root, prompt, observation)
                expected = (
                    "resume" if boundary == "successor-status" else
                    "accepted-state-continuation-retry-ready"
                    if boundary in {"action-authorization", "successor-grant"} else
                    "accepted-state-rollover-retry-ready"
                )
                self.assertEqual(self.discover(fixture)["disposition"], expected)
                ROLLOVER.persist_increment_rollover(root, prompt, observation)
                complete = repository_snapshot(fixture.repository)
                ROLLOVER.persist_increment_rollover(root, prompt, observation)
                self.assertEqual(repository_snapshot(fixture.repository), complete)
                self.assertEqual((root / "state/block-resolutions.jsonl").read_bytes(), original_resolutions)
                self.assertEqual(self.discover(fixture)["disposition"], "resume")

    def discover(self, fixture) -> dict[str, object]:
        return run_program_discovery(fixture.repository)

    def test_required_rollover_writes_compose_with_plan_a_allocations(self) -> None:
        fixture, program_root, _observation, _prompt = accepted_continuation_program(
            "immediate"
        )
        try:
            required = ROLLOVER.required_increment_rollover_writes(
                program_root,
                fixture.repository,
                "ARCHIVE-VERIFY",
            )
            by_path = {item.path: item.disposition for item in required}
            prefix = "implementation-programs/ARCHIVE-PROGRAM"
            self.assertEqual(
                by_path[f"{prefix}/state/action-authorizations.jsonl"], "Modify"
            )
            self.assertEqual(
                by_path[f"{prefix}/state/increment-grants.jsonl"], "Modify"
            )
            self.assertEqual(by_path[f"{prefix}/state/rollovers.jsonl"], "Modify")
            self.assertEqual(by_path[f"{prefix}/state/status.json"], "Modify")
            self.assertEqual(
                by_path[f"{prefix}/increments/ARCHIVE-INDEX/handoff.md"], "Create"
            )
            self.assertEqual(
                by_path[f"{prefix}/increments/ARCHIVE-VERIFY/brief.md"], "Create"
            )
            self.assertGreater(len(required), 6)
        finally:
            fixture.close()

    def test_immediate_and_later_prefixes_are_discoverable_and_retryable(self) -> None:
        labels = (
            "action-authorization",
            "successor-grant",
            "handoff",
            "successor-brief",
            "rollover-record",
            "successor-status",
        )
        for domain in ("immediate", "accepted-state"):
            for label in labels:
                with self.subTest(domain=domain, label=label):
                    fixture, program_root, observation, prompt = (
                        accepted_continuation_program(domain)
                    )
                    try:
                        manifest_before = (program_root / "manifest.json").read_bytes()

                        def interrupt(
                            completed_label: str, *, expected_label: str = label
                        ) -> None:
                            if completed_label == expected_label:
                                raise RuntimeError("injected rollover interruption")

                        with mock.patch.object(
                            ROLLOVER, "_after_persist", side_effect=interrupt
                        ):
                            with self.assertRaisesRegex(RuntimeError, "injected"):
                                ROLLOVER.persist_increment_rollover(
                                    program_root, prompt, observation
                                )
                        if label == "rollover-record":
                            status = json.loads(
                                (program_root / "state/status.json").read_text(
                                    encoding="utf-8"
                                )
                            )
                            with self.assertRaisesRegex(
                                ValueError, "unbound rollover history"
                            ):
                                ROLLOVER.validated_inherited_paths(
                                    program_root, status, observation
                                )
                        discovered = self.discover(fixture)
                        if label == "successor-status":
                            expected = "resume"
                        elif label in {"action-authorization", "successor-grant"}:
                            expected = (
                                "increment-continuation-retry-ready"
                                if domain == "immediate"
                                else "accepted-state-continuation-retry-ready"
                            )
                        else:
                            expected = (
                                "increment-rollover-retry-ready"
                                if domain == "immediate"
                                else "accepted-state-rollover-retry-ready"
                            )
                        self.assertEqual(
                            discovered["disposition"], expected, discovered
                        )
                        receipt = (
                            DIFF.persist_diff_disposition(
                                program_root, prompt, observation
                            )
                            if domain == "immediate"
                            else ROLLOVER.persist_increment_rollover(
                                program_root, prompt, observation
                            )
                        )
                        self.assertEqual(
                            receipt.successor_increment_id, "ARCHIVE-VERIFY"
                        )
                        self.assertEqual(receipt.current_increment_id, "ARCHIVE-VERIFY")
                        self.assertFalse(receipt.requires_retry)
                        self.assertEqual(
                            (program_root / "manifest.json").read_bytes(),
                            manifest_before,
                        )
                    finally:
                        fixture.close()

    def test_continuation_reason_preserves_rollover_retry_authority(self) -> None:
        fixture, program_root, observation, prompt = accepted_continuation_program(
            "accepted-state"
        )
        try:
            acceptance = DIFF.build_diff_acceptance_candidate(
                program_root, observation
            )

            def interrupt(
                completed_label: str, *, label: str = "rollover-record"
            ) -> None:
                if completed_label == label:
                    raise RuntimeError("injected rollover interruption")

            with mock.patch.object(
                ROLLOVER, "_after_persist", side_effect=interrupt
            ):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    ROLLOVER.persist_increment_rollover(
                        program_root, prompt, observation
                    )

            self.assertEqual(
                CONTINUATION.continuation_unavailability_reason(
                    program_root,
                    acceptance,
                    allow_unbound_rollover_suffix=True,
                ),
                "",
            )
        finally:
            fixture.close()

    def test_rollover_rejects_non_object_inherited_workspace_binding(self) -> None:
        for inherited_binding in (None, [], "invalid", 1):
            with self.subTest(inherited_binding=inherited_binding):
                fixture, program_root, observation, _prompt = (
                    accepted_continuation_program("accepted-state")
                )
                try:
                    status_path = program_root / "state/status.json"
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    status["inherited_workspace_binding"] = inherited_binding
                    status_path.write_bytes(ROLLOVER._canonical_json_bytes(status))
                    prompt = (
                        CONTINUATION.render_accepted_state_continuation_prompt(
                            program_root
                        )
                    )

                    with self.assertRaisesRegex(
                        ValueError,
                        "^prior inherited workspace inventory is invalid$",
                    ):
                        ROLLOVER._build_rollover_candidate(
                            program_root, prompt, observation
                        )
                finally:
                    fixture.close()

    def test_completed_rollover_history_requires_activation_authority_anchor(
        self,
    ) -> None:
        fixture, program_root, observation, prompt = accepted_continuation_program(
            "accepted-state"
        )
        try:
            ROLLOVER.persist_increment_rollover(
                program_root, prompt, observation
            )
            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            self.assertTrue(
                ROLLOVER.validated_inherited_paths(
                    program_root, status, observation
                )
            )
            rollover_path = program_root / "state/rollovers.jsonl"
            records = [
                json.loads(line)
                for line in rollover_path.read_text(encoding="utf-8").splitlines()
            ]
            records[0]["prior_increment_authority_binding"][
                "grant_id"
            ] = "FORGED-GENESIS-GRANT"
            rollover_path.write_bytes(ROLLOVER._canonical_json_line(records[0]))
            status["rollover_binding"]["rollover_sha256"] = (
                ROLLOVER._sha256_bytes(ROLLOVER._canonical_json_line(records[0]))
            )
            (program_root / "state/status.json").write_bytes(
                ROLLOVER._canonical_json_bytes(status)
            )
            with self.assertRaisesRegex(
                ValueError,
                "^rollover chain prior increment authority is invalid$",
            ):
                ROLLOVER.validated_inherited_paths(
                    program_root, status, observation
                )
        finally:
            fixture.close()

    def test_completed_rollover_history_requires_genesis_increment_identity(
        self,
    ) -> None:
        fixture, program_root, observation, prompt = accepted_continuation_program(
            "accepted-state"
        )
        try:
            ROLLOVER.persist_increment_rollover(
                program_root, prompt, observation
            )
            status_path = program_root / "state/status.json"
            rollover_path = program_root / "state/rollovers.jsonl"
            action_path = program_root / "state/action-authorizations.jsonl"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            rollovers = [
                json.loads(line)
                for line in rollover_path.read_text(encoding="utf-8").splitlines()
            ]
            actions = [
                json.loads(line)
                for line in action_path.read_text(encoding="utf-8").splitlines()
            ]
            rollover = rollovers[0]
            rollover["current_increment_id"] = "FORGED-GENESIS"
            action = next(
                item
                for item in actions
                if item.get("authorization_id")
                == rollover["rollover_authorization_id"]
            )
            action["current_increment_id"] = "FORGED-GENESIS"
            action_path.write_bytes(
                b"".join(ROLLOVER._canonical_json_line(item) for item in actions)
            )
            rollover["rollover_authorization_sha256"] = ROLLOVER._sha256_bytes(
                ROLLOVER._canonical_json_line(action)
            )
            rollover_path.write_bytes(ROLLOVER._canonical_json_line(rollover))
            status["rollover_binding"]["rollover_sha256"] = ROLLOVER._sha256_bytes(
                ROLLOVER._canonical_json_line(rollover)
            )
            status_path.write_bytes(ROLLOVER._canonical_json_bytes(status))

            with self.assertRaisesRegex(
                ValueError,
                "^rollover chain increment authority is invalid$",
            ):
                ROLLOVER.validated_inherited_paths(
                    program_root, status, observation
                )
        finally:
            fixture.close()

    def test_forged_rollover_history_fails_before_every_transaction_write(
        self,
    ) -> None:
        for forged_delta in ("empty", "extra-path"):
            with self.subTest(forged_delta=forged_delta):
                fixture, program_root, observation, prompt = (
                    accepted_continuation_program("accepted-state")
                )
                try:
                    candidate = ROLLOVER._build_rollover_candidate(
                        program_root, prompt, observation
                    )
                    forged = dict(candidate.rollover_record)
                    forged["rollover_id"] = f"FORGED-{forged_delta.upper()}"
                    if forged_delta == "empty":
                        forged["accepted_product_delta"] = []
                    else:
                        forged["accepted_product_delta"] = [
                            *forged["accepted_product_delta"],
                            {
                                "path": "forged-extra.txt",
                                "disposition": "Modify",
                                "sha256": "f" * 64,
                            },
                        ]
                    candidate.rollover_path.write_bytes(
                        ROLLOVER._canonical_json_line(forged)
                    )
                    before = repository_snapshot(program_root)

                    with self.assertRaisesRegex(ValueError, "rollover"):
                        ROLLOVER.persist_increment_rollover(
                            program_root, prompt, observation
                        )
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_coordinator_completes_immediate_continuation_without_second_prompt(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            prompt = CONTINUATION.render_accept_continue_prompt(program_root)
            receipt = DIFF.persist_diff_disposition(program_root, prompt, observation)
            self.assertEqual(receipt.successor_increment_id, "ARCHIVE-VERIFY")
            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status["current_increment_id"], "ARCHIVE-VERIFY")
            self.assertEqual(status["current_increment_state"], "preparing")
        finally:
            fixture.close()

    def test_apply_cli_uses_fresh_observation_and_completes_later_rollover(self) -> None:
        fixture, program_root, _observation, prompt = accepted_continuation_program(
            "accepted-state"
        )
        try:
            prompt_path = fixture.root / "continuation-prompt.md"
            prompt_path.write_text(prompt, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "apply",
                    str(program_root),
                    "--prompt-file",
                    str(prompt_path),
                    "--repository",
                    str(fixture.repository),
                    "--base-commit",
                    fixture.head,
                ],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["successor_increment_id"], "ARCHIVE-VERIFY")
            self.assertFalse(payload["requires_retry"])
        finally:
            fixture.close()

    def test_invalid_prompt_observation_product_or_manifest_fails_before_writes(self) -> None:
        for case in ("prompt", "observation", "product", "manifest"):
            with self.subTest(case=case):
                fixture, program_root, observation, prompt = (
                    accepted_continuation_program("accepted-state")
                )
                try:
                    if case == "prompt":
                        prompt += "tampered\n"
                    elif case == "observation":
                        observation = replace(observation, head_commit="f" * 40)
                    elif case == "product":
                        (fixture.repository / "archive-output.txt").write_text(
                            "changed after acceptance\n", encoding="utf-8"
                        )
                    else:
                        manifest_path = program_root / "manifest.json"
                        manifest = json.loads(
                            manifest_path.read_text(encoding="utf-8")
                        )
                        manifest["schema_version"] = "implementation-program-manifest/v1"
                        manifest_path.write_text(
                            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )
                    before = repository_snapshot(program_root)
                    with self.assertRaises(ValueError):
                        ROLLOVER.persist_increment_rollover(
                            program_root, prompt, observation
                        )
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_divergent_partial_file_is_preserved_and_requires_recovery(self) -> None:
        fixture, program_root, observation, prompt = accepted_continuation_program(
            "accepted-state"
        )
        try:
            def interrupt(label: str) -> None:
                if label == "handoff":
                    raise RuntimeError("injected")

            with mock.patch.object(ROLLOVER, "_after_persist", side_effect=interrupt):
                with self.assertRaises(RuntimeError):
                    ROLLOVER.persist_increment_rollover(
                        program_root, prompt, observation
                    )
            handoff = program_root / "increments/ARCHIVE-INDEX/handoff.md"
            handoff.write_bytes(handoff.read_bytes() + b"divergent\n")
            before = repository_snapshot(program_root)
            discovered = self.discover(fixture)
            self.assertEqual(
                discovered["disposition"],
                "accepted-state-continuation-recovery-required",
                discovered,
            )
            with self.assertRaisesRegex(ValueError, "recovery-required"):
                ROLLOVER.persist_increment_rollover(
                    program_root, prompt, observation
                )
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
