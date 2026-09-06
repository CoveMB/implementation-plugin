import json
import subprocess
import sys
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture,
    repository_snapshot,
    run_program_discovery,
)
from tests.script_module_support import load_script_module
from tests.test_program_activation import ACTIVATION, activated_program, exact_plan_bytes


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "blocked_recovery.py"
LIFECYCLE_SUPPORT_PATH = REPOSITORY_ROOT / "tests/program_bootstrap_support.py"

BLOCKED = load_script_module("blocked_recovery", SCRIPT_PATH)


def implementing_program():
    fixture = BootstrapFixture()
    fixture.configure_successors({"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)})
    program_root, observation = activated_program(fixture)
    plan = exact_plan_bytes(program_root, observation)
    prepared = ACTIVATION.prepare_exact_plan(program_root, plan, observation)
    ACTIVATION.materialize_exact_plan(
        program_root, prepared.plan_prompt, observation
    )
    ACTIVATION.advance_execution_state(program_root, "implementing", observation)
    fresh = ACTIVATION._without_owned_program_paths(
        program_root,
        ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation,
    )
    return fixture, program_root, fresh


def block_request(fixture: BootstrapFixture):
    return BLOCKED.BlockedTransitionRequest(
        reason_code="verification-environment-unavailable",
        recovery_criteria=(
            "The local verification environment is available.",
            "The preserved catalog evidence remains unchanged.",
        ),
        evidence_bindings=(
            BLOCKED.EvidenceBinding(
                path="catalog.txt",
                sha256=BLOCKED.sha256_file(fixture.repository / "catalog.txt"),
            ),
        ),
    )


def resolution_candidate(program_root: Path) -> dict[str, object]:
    status = json.loads(
        (program_root / "state/status.json").read_text(encoding="utf-8")
    )
    context = status["blocked_context"]
    return {
        "schema_version": BLOCKED.BLOCK_RESOLUTION_CANDIDATE_SCHEMA,
        "block_id": context["block_id"],
        "criterion_results": [
            {"criterion": criterion, "satisfied": True}
            for criterion in context["recovery_criteria"]
        ],
        "evidence_bindings": context["evidence_bindings"],
    }


class BlockedRecoveryTests(unittest.TestCase):
    def discover(self, fixture: BootstrapFixture) -> dict[str, object]:
        return run_program_discovery(fixture.repository)

    def test_production_block_fresh_discovery_and_exact_resume(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            blocked_process = subprocess.run(
                [
                    sys.executable,
                    str(LIFECYCLE_SUPPORT_PATH),
                    "block",
                    "--repository",
                    str(fixture.repository),
                    "--candidate",
                    str(fixture.candidate),
                    "--source-plan",
                    str(fixture.source_plan),
                    "--source-sha256",
                    fixture.source_sha256,
                ],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(blocked_process.returncode, 0, blocked_process.stderr)
            blocked = json.loads(blocked_process.stdout)
            self.assertEqual(blocked["program_state"], "blocked")
            self.assertEqual(blocked["increment_state"], "blocked")
            discovered = self.discover(fixture)
            self.assertEqual(discovered["disposition"], "blocked-recovery-ready")
            self.assertEqual(
                discovered["candidates"][0]["resume_program_state"], "active"
            )
            self.assertEqual(
                discovered["candidates"][0]["resume_increment_state"],
                "implementing",
            )

            candidate = resolution_candidate(program_root)
            prompt = BLOCKED.render_block_resolution_prompt(
                program_root, candidate, observation
            )
            receipt = BLOCKED.persist_blocked_resolution(
                program_root, prompt, observation
            )
            self.assertEqual(receipt.program_state, "active")
            self.assertEqual(receipt.increment_state, "implementing")
            actions = [
                json.loads(line)
                for line in (
                    program_root / "state/action-authorizations.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
            resolutions = [
                json.loads(line)
                for line in (
                    program_root / "state/block-resolutions.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
            resume_actions = [
                item
                for item in actions
                if item.get("actions") == ["resume-blocked-program"]
            ]
            self.assertEqual(len(resume_actions), 1)
            self.assertEqual(len(resolutions), 1)
            for record in (*resume_actions, *resolutions):
                self.assertTrue(
                    all(
                        type(result["satisfied"]) is bool
                        for result in record["criterion_results"]
                    )
                )
        finally:
            fixture.close()

    def test_second_blocking_episode_replaces_current_resolution_binding(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )
            first_block_id = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )["blocked_context"]["block_id"]
            prompt = BLOCKED.render_block_resolution_prompt(
                program_root, resolution_candidate(program_root), observation
            )
            BLOCKED.persist_blocked_resolution(program_root, prompt, observation)

            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )
            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            self.assertNotEqual(status["blocked_context"]["block_id"], first_block_id)
            self.assertNotIn("block_resolution_binding", status)
            self.assertEqual(
                self.discover(fixture)["disposition"], "blocked-recovery-ready"
            )
            resolutions = (
                program_root / "state/block-resolutions.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(resolutions), 1)
        finally:
            fixture.close()

    def test_resolution_prefixes_are_discoverable_and_idempotent(self) -> None:
        for label in ("action-authorization", "resolution-record", "resumed-status"):
            with self.subTest(label=label):
                fixture, program_root, observation = implementing_program()
                try:
                    BLOCKED.block_current_program(
                        program_root, block_request(fixture), observation
                    )
                    prompt = BLOCKED.render_block_resolution_prompt(
                        program_root, resolution_candidate(program_root), observation
                    )

                    def interrupt(
                        completed_label: str, *, expected_label: str = label
                    ) -> None:
                        if completed_label == expected_label:
                            raise RuntimeError("injected blocked recovery interruption")

                    with mock.patch.object(
                        BLOCKED, "_after_persist", side_effect=interrupt
                    ):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            BLOCKED.persist_blocked_resolution(
                                program_root, prompt, observation
                            )
                    discovered = self.discover(fixture)
                    expected = (
                        "resume"
                        if label == "resumed-status"
                        else "blocked-resolution-retry-ready"
                    )
                    self.assertEqual(discovered["disposition"], expected, discovered)
                    completed = BLOCKED.persist_blocked_resolution(
                        program_root, prompt, observation
                    )
                    self.assertEqual(completed.increment_state, "implementing")
                    snapshot = repository_snapshot(fixture.repository)
                    recovered = BLOCKED.persist_blocked_resolution(
                        program_root, prompt, observation
                    )
                    self.assertEqual(recovered.increment_state, "implementing")
                    self.assertEqual(repository_snapshot(fixture.repository), snapshot)
                finally:
                    fixture.close()

    def test_remediating_and_invalid_entry_requests_fail_before_writes(self) -> None:
        from tests.program_bootstrap_support import canonical_json
        from tests.test_program_review import REVIEW, reviewing_program

        def add_open_finding(fixture: BootstrapFixture) -> None:
            path = fixture.repository / "reviews/requirements.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["findings"] = [
                {
                    "finding_id": "F-BLOCK-BOUNDARY",
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
            ]
            path.write_bytes(canonical_json(report))

        fixture, program_root, observation = reviewing_program(add_open_finding)
        try:
            REVIEW.persist_review_remediation(program_root, observation)
            observation = ACTIVATION._without_owned_program_paths(
                program_root,
                ACTIVATION.inspect_repository(
                    fixture.repository, fixture.head
                ).observation,
            )
            before = repository_snapshot(fixture.repository)
            with self.assertRaisesRegex(ValueError, "remediating"):
                BLOCKED.block_current_program(
                    program_root, block_request(fixture), observation
                )
            self.assertEqual(repository_snapshot(fixture.repository), before)
        finally:
            fixture.close()

        for state in ("preparing", "awaiting-plan-approval", "authorized", "verified", "accepted"):
            with self.subTest(state=state):
                fixture, program_root, observation = implementing_program()
                try:
                    status_path = program_root / "state/status.json"
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    status["current_increment_state"] = state
                    status_path.write_text(
                        json.dumps(status, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.block_current_program(
                            program_root, block_request(fixture), observation
                        )
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                finally:
                    fixture.close()

    def test_candidate_tampering_and_stale_authority_fail_before_writes(self) -> None:
        for case in (
            "resume-target",
            "unsatisfied",
            "duplicate",
            "outside-evidence",
            "changed-evidence",
            "prompt",
            "status",
        ):
            with self.subTest(case=case):
                fixture, program_root, observation = implementing_program()
                try:
                    BLOCKED.block_current_program(
                        program_root, block_request(fixture), observation
                    )
                    candidate = resolution_candidate(program_root)
                    if case == "resume-target":
                        candidate["resume_increment_state"] = "reviewing"
                    elif case == "unsatisfied":
                        candidate["criterion_results"][0]["satisfied"] = False
                    elif case == "duplicate":
                        candidate["criterion_results"].append(
                            dict(candidate["criterion_results"][0])
                        )
                    elif case == "outside-evidence":
                        candidate["evidence_bindings"] = [
                            {"path": "outside.txt", "sha256": "0" * 64}
                        ]
                    elif case == "changed-evidence":
                        (fixture.repository / "catalog.txt").write_text(
                            "changed\n", encoding="utf-8"
                        )
                    prompt = None
                    if case not in {"status", "prompt"}:
                        before = repository_snapshot(fixture.repository)
                        with self.assertRaises(ValueError):
                            BLOCKED.build_block_resolution_candidate(
                                program_root, candidate, observation
                            )
                        self.assertEqual(repository_snapshot(fixture.repository), before)
                        continue
                    prompt = BLOCKED.render_block_resolution_prompt(
                        program_root, candidate, observation
                    )
                    if case == "prompt":
                        prompt += "tampered\n"
                    else:
                        status_path = program_root / "state/status.json"
                        status = json.loads(status_path.read_text(encoding="utf-8"))
                        status["state_sequence"] += 1
                        status_path.write_text(
                            json.dumps(status, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.persist_blocked_resolution(
                            program_root, prompt, observation
                        )
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                finally:
                    fixture.close()

    def test_resolution_candidate_requires_exact_nested_field_types(self) -> None:
        for case in (
            "integer-satisfied",
            "float-satisfied",
            "criterion-type",
            "criterion-extra-key",
            "evidence-path-type",
            "evidence-sha-type",
            "evidence-extra-key",
        ):
            with self.subTest(case=case):
                fixture, program_root, observation = implementing_program()
                try:
                    BLOCKED.block_current_program(
                        program_root, block_request(fixture), observation
                    )
                    candidate = resolution_candidate(program_root)
                    if case == "integer-satisfied":
                        candidate["criterion_results"][0]["satisfied"] = 1
                    elif case == "float-satisfied":
                        candidate["criterion_results"][0]["satisfied"] = 1.0
                    elif case == "criterion-type":
                        candidate["criterion_results"][0]["criterion"] = 1
                    elif case == "criterion-extra-key":
                        candidate["criterion_results"][0]["extra"] = "value"
                    elif case == "evidence-path-type":
                        candidate["evidence_bindings"][0]["path"] = 1
                    elif case == "evidence-sha-type":
                        candidate["evidence_bindings"][0]["sha256"] = 1
                    else:
                        candidate["evidence_bindings"][0]["extra"] = "value"
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaisesRegex(
                        ValueError, "candidate nested field types are invalid"
                    ):
                        BLOCKED.build_block_resolution_candidate(
                            program_root, candidate, observation
                        )
                    self.assertEqual(
                        repository_snapshot(fixture.repository), before
                    )
                finally:
                    fixture.close()

    def test_changed_plan_baseline_grant_context_or_evidence_fails_closed(self) -> None:
        for case in ("plan", "baseline", "grant", "context", "symlink-evidence"):
            with self.subTest(case=case):
                fixture, program_root, observation = implementing_program()
                try:
                    BLOCKED.block_current_program(
                        program_root, block_request(fixture), observation
                    )
                    if case == "plan":
                        path = program_root / "increments/ARCHIVE-INDEX/exact-file-plan.md"
                        path.write_bytes(path.read_bytes() + b"drift\n")
                    elif case == "baseline":
                        path = program_root / "increments/ARCHIVE-INDEX/execution-baseline.json"
                        path.write_bytes(path.read_bytes() + b" ")
                    elif case == "grant":
                        path = program_root / "state/increment-grants.jsonl"
                        records = [json.loads(line) for line in path.read_text().splitlines()]
                        records[-1]["decision"] = "revoked"
                        path.write_text(
                            "".join(
                                json.dumps(item, separators=(",", ":"), sort_keys=True)
                                + "\n"
                                for item in records
                            ),
                            encoding="utf-8",
                        )
                    elif case == "context":
                        path = program_root / "state/status.json"
                        status = json.loads(path.read_text(encoding="utf-8"))
                        status["blocked_context"]["block_id"] = "FABRICATED"
                        path.write_text(
                            json.dumps(status, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )
                    else:
                        evidence = fixture.repository / "catalog.txt"
                        evidence.unlink()
                        evidence.symlink_to("archive-output.txt")
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.build_block_resolution_candidate(
                            program_root, resolution_candidate(program_root), observation
                        )
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                finally:
                    fixture.close()

    def test_divergent_resolution_action_is_preserved_and_stops(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )
            prompt = BLOCKED.render_block_resolution_prompt(
                program_root, resolution_candidate(program_root), observation
            )

            def interrupt(label: str) -> None:
                if label == "action-authorization":
                    raise RuntimeError("injected")

            with mock.patch.object(BLOCKED, "_after_persist", side_effect=interrupt):
                with self.assertRaises(RuntimeError):
                    BLOCKED.persist_blocked_resolution(
                        program_root, prompt, observation
                    )
            path = program_root / "state/action-authorizations.jsonl"
            records = [json.loads(line) for line in path.read_text().splitlines()]
            records[-1]["checkpoint_id"] = "DIVERGENT"
            path.write_text(
                "".join(
                    json.dumps(item, separators=(",", ":"), sort_keys=True) + "\n"
                    for item in records
                ),
                encoding="utf-8",
            )
            before = repository_snapshot(fixture.repository)
            discovered = self.discover(fixture)
            self.assertEqual(
                discovered["disposition"], "blocked-recovery-required", discovered
            )
            with self.assertRaisesRegex(ValueError, "recovery-required"):
                BLOCKED.persist_blocked_resolution(
                    program_root, prompt, observation
                )
            self.assertEqual(repository_snapshot(fixture.repository), before)
        finally:
            fixture.close()

    def test_render_and_apply_clis_use_transport_only_as_input(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )
            candidate_path = fixture.root / "block-candidate.json"
            candidate_path.write_text(
                json.dumps(resolution_candidate(program_root), sort_keys=True) + "\n",
                encoding="utf-8",
            )
            before = repository_snapshot(fixture.repository)
            rendered = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "render",
                    str(program_root),
                    "--candidate-file",
                    str(candidate_path),
                ],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertEqual(repository_snapshot(fixture.repository), before)
            prompt_path = fixture.root / "block-prompt.md"
            prompt_path.write_text(rendered.stdout, encoding="utf-8")
            applied = subprocess.run(
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
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(json.loads(applied.stdout)["increment_state"], "implementing")
            self.assertFalse(
                any(
                    path.name == "block-candidate.json"
                    for path in program_root.rglob("*")
                )
            )
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
