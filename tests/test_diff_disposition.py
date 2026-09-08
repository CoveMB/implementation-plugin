import json
from contextlib import nullcontext
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture,
    _exact_plan_bytes,
    canonical_json,
    repository_snapshot,
    run_program_discovery,
    write_raw_review_reports,
)
from tests.script_module_support import load_script_module
from tests.test_program_activation import ACTIVATION, activated_program, exact_plan_bytes
from tests.test_program_review import REVIEW as PROGRAM_REVIEW
from tests.test_program_review import reviewing_program
from tests.test_program_setup import BOOTSTRAP, SETUP


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "diff_disposition.py"

DIFF = load_script_module("diff_disposition", SCRIPT_PATH)


def setUpModule() -> None:
    sys.path.insert(0, str(SCRIPT_ROOT))


def tearDownModule() -> None:
    sys.path.remove(str(SCRIPT_ROOT))


def awaiting_diff_program(successors: dict[str, tuple[str, ...]] | None = None):
    if successors is not None:
        fixture = BootstrapFixture()
        fixture.configure_successors(successors)
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
        observation = ACTIVATION.inspect_repository(
            fixture.repository, fixture.head
        ).observation
        ACTIVATION.advance_execution_state(program_root, "reviewing", observation)
        PROGRAM_REVIEW.persist_review_preparation(program_root, observation)
        return fixture, program_root, observation
    fixture, program_root, observation = reviewing_program()
    PROGRAM_REVIEW.persist_review_preparation(program_root, observation)
    return fixture, program_root, observation


def _setup_awaiting_diff_program(*, delete: bool):
    fixture = BootstrapFixture()
    if delete:
        fixture.configure_delete_setup_v2(path="catalog.txt")
    else:
        fixture.configure_setup_v3()
    BOOTSTRAP.publish_program_proposal(
        fixture.repository,
        fixture.source_plan,
        fixture.candidate,
        fixture.source_sha256,
    )
    observation = ACTIVATION.inspect_repository(
        fixture.repository, fixture.head
    ).observation
    activation = ACTIVATION.activate_program(
        fixture.program_root,
        SETUP.adapt_setup_decision(
            fixture.program_root, "Yes", role="user", provenance="direct-user-message"
        ),
        observation,
    )
    intent = SETUP.adapt_increment_start_intent(
        fixture.program_root, activation.handoff,
        role="user", provenance="direct-user-message",
    )
    ACTIVATION.start_first_increment(fixture.program_root, intent, observation)
    observation = ACTIVATION.inspect_repository(
        fixture.repository, fixture.head
    ).observation
    prepared = ACTIVATION.prepare_exact_plan(
        fixture.program_root,
        _exact_plan_bytes(fixture.program_root, observation),
        observation,
    )
    ACTIVATION.materialize_exact_plan(
        fixture.program_root, prepared.plan_prompt, observation
    )
    ACTIVATION.advance_execution_state(
        fixture.program_root, "implementing", observation
    )
    (fixture.repository / "archive-output.txt").write_text(
        "archive output\n", encoding="utf-8"
    )
    write_raw_review_reports(fixture.repository)
    observation = ACTIVATION.inspect_repository(
        fixture.repository, fixture.head
    ).observation
    ACTIVATION.advance_execution_state(
        fixture.program_root, "reviewing", observation
    )
    PROGRAM_REVIEW.persist_review_preparation(fixture.program_root, observation)
    return fixture, fixture.program_root, observation


def delete_setup_v2_awaiting_diff_program():
    return _setup_awaiting_diff_program(delete=True)


def setup_v1_awaiting_diff_program():
    return _setup_awaiting_diff_program(delete=False)


class DiffDispositionTests(unittest.TestCase):
    def discover(self, fixture) -> dict[str, object]:
        return run_program_discovery(fixture.repository)

    def test_v2_acceptance_rejects_legacy_disposition_and_approval_family(self) -> None:
        fixture, program_root, observation = delete_setup_v2_awaiting_diff_program()
        try:
            candidate = DIFF.build_diff_acceptance_candidate(program_root, observation)
            DIFF.persist_accept_stop(
                program_root,
                f"Accept and stop.\n\n{candidate.prompt}",
                observation,
            )
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            disposition = status["diff_disposition_binding"]
            disposition["schema_version"] = "implementation-diff-disposition-binding/v1"
            disposition.pop("product_result_schema_version", None)
            disposition.pop("product_result_sha256", None)
            status_path.write_bytes(canonical_json(status))
            approvals_path = program_root / "state/approvals.jsonl"
            records = [json.loads(line) for line in approvals_path.read_text().splitlines()]
            approval = next(record for record in records if record.get("type") == "increment-diff-approval")
            approval["schema_version"] = "implementation-approval/v2"
            approval.pop("product_result_schema_version", None)
            approval.pop("product_result_sha256", None)
            approvals_path.write_text(
                "\n".join(json.dumps(record, separators=(",", ":"), sort_keys=False) for record in records) + "\n",
                encoding="utf-8",
            )
            before_status = status_path.read_bytes()
            before_approvals = approvals_path.read_bytes()
            issues = DIFF.validate_state_authority(program_root, observation)
            self.assertTrue(issues, issues)
            self.assertTrue(any("family" in issue or "product" in issue or "approval" in issue for issue in issues))
            with self.assertRaises(ValueError):
                DIFF.persist_accept_stop(
                    program_root,
                    f"Accept and stop.\n\n{candidate.prompt}",
                    observation,
                )
            self.assertEqual(status_path.read_bytes(), before_status)
            self.assertEqual(approvals_path.read_bytes(), before_approvals)
        finally:
            fixture.close()

    def test_v1_acceptance_rejects_coordinated_v2_disposition_and_approval(self) -> None:
        fixture, program_root, observation = setup_v1_awaiting_diff_program()
        try:
            candidate = DIFF.build_diff_acceptance_candidate(program_root, observation)
            DIFF.persist_accept_stop(
                program_root,
                f"Accept and stop.\n\n{candidate.prompt}",
                observation,
            )
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            disposition = status["diff_disposition_binding"]
            disposition["schema_version"] = "implementation-diff-disposition-binding/v2"
            disposition["product_result_schema_version"] = "implementation-product-path-states/v2"
            disposition["product_result_sha256"] = "0" * 64
            status["execution_transition_binding"]["schema_version"] = "implementation-execution-transition/v2"
            status["review_preparation_binding"]["schema_version"] = "implementation-review-preparation/v2"
            status["review_evidence_binding"]["product_result_schema_version"] = "implementation-product-path-states/v2"
            status_path.write_bytes(canonical_json(status))
            approvals_path = program_root / "state/approvals.jsonl"
            records = [json.loads(line) for line in approvals_path.read_text().splitlines()]
            approval = next(record for record in records if record.get("type") == "increment-diff-approval")
            approval["schema_version"] = "implementation-approval/v3"
            approval["product_result_schema_version"] = "implementation-product-path-states/v2"
            approval["product_result_sha256"] = "0" * 64
            approvals_path.write_text(
                "\n".join(json.dumps(record, separators=(",", ":"), sort_keys=False) for record in records) + "\n",
                encoding="utf-8",
            )
            before_status = status_path.read_bytes()
            before_approvals = approvals_path.read_bytes()
            issues = DIFF.validate_state_authority(program_root, observation)
            self.assertTrue(issues, issues)
            self.assertTrue(any("family" in issue for issue in issues), issues)
            with self.assertRaises(ValueError):
                DIFF.persist_accept_stop(
                    program_root,
                    f"Accept and stop.\n\n{candidate.prompt}",
                    observation,
                )
            self.assertEqual(status_path.read_bytes(), before_status)
            self.assertEqual(approvals_path.read_bytes(), before_approvals)
        finally:
            fixture.close()

    def test_v2_product_result_propagates_exactly_through_acceptance_sinks(self) -> None:
        fixture, program_root, observation = delete_setup_v2_awaiting_diff_program()
        try:
            review_candidate = PROGRAM_REVIEW.build_review_preparation(
                program_root, observation
            )
            evidence = json.loads(review_candidate.evidence_bytes)
            product_result = evidence["product_result"]
            self.assertEqual(
                product_result["schema_version"],
                "implementation-product-path-states/v2",
            )
            PROGRAM_REVIEW.persist_review_preparation(program_root, observation)
            acceptance = DIFF.build_diff_acceptance_candidate(program_root, observation)
            self.assertEqual(
                acceptance.approval_record["product_result_schema_version"],
                product_result["schema_version"],
            )
            self.assertEqual(
                acceptance.approval_record["product_result_sha256"],
                product_result["sha256"],
            )
            self.assertIn(product_result["sha256"], acceptance.prompt)
            self.assertIn(product_result["sha256"], review_candidate.packet_bytes.decode("utf-8"))
            DIFF.persist_accept_stop(
                program_root,
                f"Accept and stop.\n\n{acceptance.prompt}",
                observation,
            )
            status = json.loads((program_root / "state/status.json").read_text())
            preparation = status["review_preparation_binding"]
            self.assertEqual(preparation["product_result_schema_version"], product_result["schema_version"])
            self.assertEqual(preparation["product_result_sha256"], product_result["sha256"])
            binding = status["diff_disposition_binding"]
            self.assertEqual(binding["product_result_schema_version"], product_result["schema_version"])
            self.assertEqual(binding["product_result_sha256"], product_result["sha256"])
        finally:
            fixture.close()

    def test_v2_acceptance_revalidates_persisted_review_artifacts(self) -> None:
        for case in ("failed verification", "stripped packet binding"):
            with self.subTest(case=case):
                fixture, program_root, observation = (
                    delete_setup_v2_awaiting_diff_program()
                )
                try:
                    status_path = program_root / "state/status.json"
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    preparation = status["review_preparation_binding"]
                    if case == "failed verification":
                        evidence_path = (
                            program_root
                            / status["review_evidence_binding"]["path"]
                        )
                        evidence = json.loads(
                            evidence_path.read_text(encoding="utf-8")
                        )
                        evidence["final_verification"]["commands"][0][
                            "exit_code"
                        ] = 1
                        evidence_path.write_bytes(canonical_json(evidence))
                        evidence_sha256 = DIFF.sha256_file(evidence_path)
                        status["review_evidence_binding"]["sha256"] = (
                            evidence_sha256
                        )
                        preparation["evidence_sha256"] = evidence_sha256
                    else:
                        packet_path = (
                            program_root / status["review_packet_binding"]["path"]
                        )
                        packet_text = packet_path.read_text(encoding="utf-8")
                        metadata = (
                            "Packet schema: implementation-review-packet/v2\n"
                            "Product result schema: "
                            "implementation-product-path-states/v2\n"
                            f"Product result SHA-256: "
                            f"{preparation['product_result_sha256']}\n\n"
                        )
                        self.assertIn(metadata, packet_text)
                        packet_path.write_text(
                            packet_text.replace(metadata, "", 1),
                            encoding="utf-8",
                        )
                        packet_sha256 = DIFF.sha256_file(packet_path)
                        status["review_packet_binding"]["sha256"] = packet_sha256
                        preparation["packet_sha256"] = packet_sha256
                    status_path.write_bytes(canonical_json(status))

                    with self.assertRaisesRegex(ValueError, "review"):
                        DIFF.build_diff_acceptance_candidate(
                            program_root, observation
                        )
                finally:
                    fixture.close()

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
            candidate = DIFF.build_diff_acceptance_candidate(
                program_root, _observation
            )
            self.assertEqual(
                prompt,
                f"Accept and stop.\n\n{candidate.prompt}",
            )
            self.assertEqual(prompt.count("Accept and stop."), 1)
            self.assertNotIn("continue", prompt.lower())
            self.assertFalse(any("traceability" in path for path in loaded_paths))
            binding = candidate.accepted_status["diff_disposition_binding"]
            self.assertNotIn("accepted_status_sha256", binding)
            self.assertNotIn("submitted_prompt_sha256", binding)
        finally:
            fixture.close()

    def test_unique_satisfied_successor_adds_one_bound_continue_choice(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            prompt = DIFF.render_diff_disposition_prompt(program_root)
            acceptance = DIFF.build_diff_acceptance_candidate(
                program_root, observation
            )
            extension = DIFF._continuation.build_continuation_extension(
                program_root, acceptance, observation
            )
            self.assertIsNotNone(extension)
            continued = DIFF._continuation.build_accept_continue_candidate(
                acceptance, extension
            )
            self.assertEqual(
                prompt,
                (
                    f"Accept and stop.\n\n{acceptance.prompt}\n"
                    f"Accept and continue to `{extension.successor_increment_id}`.\n\n"
                    f"{continued.prompt}"
                ),
            )
            self.assertEqual(prompt.count("Accept and stop."), 1)
            self.assertEqual(
                prompt.count("Accept and continue to `ARCHIVE-VERIFY`."), 1
            )
            self.assertEqual(prompt.count("$implementing-staged-plans"), 2)
            candidate = DIFF.build_diff_acceptance_candidate(program_root, observation)
            self.assertEqual(candidate.decision, "accept-stop")
        finally:
            fixture.close()

    def test_unavailable_successor_never_blocks_or_changes_stop_choice(self) -> None:
        cases = (
            (None, "no allocated successor"),
            (
                {
                    "ARCHIVE-VERIFY": ("ARCHIVE-INDEX",),
                    "ARCHIVE-EXPORT": ("ARCHIVE-INDEX",),
                },
                "multiple allocated successors",
            ),
            (
                {"ARCHIVE-VERIFY": ("ARCHIVE-BLOCKER",)},
                "successor dependencies are unsatisfied",
            ),
        )
        for successors, reason in cases:
            with self.subTest(reason=reason):
                # Unsafe allocations now stop before a new exact plan. Inject the
                # unavailable boundary here to exercise stop-choice policy for
                # an independently valid acceptance, including historical callers.
                fixture, program_root, _observation = awaiting_diff_program()
                try:
                    selection = (
                        mock.patch.object(DIFF._continuation, "_successor_selection", return_value=(None, reason))
                        if successors is not None else nullcontext()
                    )
                    with selection:
                        prompt = DIFF.render_diff_disposition_prompt(program_root)
                        candidate = DIFF.build_diff_acceptance_candidate(
                            program_root, _observation
                        )
                        expected = f"Accept and stop.\n\n{candidate.prompt}"
                        if reason != "no allocated successor":
                            expected += f"\nContinuation unavailable: {reason}.\n"
                        self.assertEqual(prompt, expected)
                        self.assertEqual(prompt.count("Accept and stop."), 1)
                        self.assertNotIn("Accept and continue", prompt)
                        if successors is None:
                            from program_continuation import (
                                build_continuation_extension,
                                continuation_unavailability_reason,
                            )

                            candidate = DIFF.build_diff_acceptance_candidate(
                                program_root, _observation
                            )
                            self.assertIsNone(
                                build_continuation_extension(
                                    program_root, candidate, _observation
                                )
                            )
                            self.assertEqual(
                                continuation_unavailability_reason(
                                    program_root, candidate
                                ),
                                reason,
                            )
                        else:
                            self.assertIn(reason, prompt)
                        self.assertEqual(prompt.count("$implementing-staged-plans"), 1)
                finally:
                    fixture.close()

    def test_stop_submission_does_not_derive_continuation(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            acceptance = DIFF.build_diff_acceptance_candidate(
                program_root, observation
            )
            stop_prompt = "Accept and stop.\n\n" + acceptance.prompt
            with mock.patch.object(
                DIFF._continuation,
                "build_continuation_extension",
                side_effect=ValueError("unrelated continuation failure"),
            ):
                receipt = DIFF._persist_diff_acceptance_prefix(
                    program_root, stop_prompt, observation
                )

            self.assertEqual(receipt.decision, "accept-stop")
            self.assertEqual(receipt.increment_state, "accepted")
        finally:
            fixture.close()

    def test_approval_only_and_status_lost_response_prefixes_are_exactly_retry_safe(self) -> None:
        for failure_label in ("diff-approval", "accepted-status"):
            with self.subTest(label=failure_label):
                fixture, program_root, observation = awaiting_diff_program()
                try:
                    prompt = DIFF.render_diff_disposition_prompt(program_root)

                    def interrupt(
                        label: str, *, expected_label: str = failure_label
                    ) -> None:
                        if label == expected_label:
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
