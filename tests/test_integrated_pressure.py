import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SUPPORT_PATH = REPOSITORY_ROOT / "tests/integrated_pressure_support.py"
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "tests/fixtures/integrated-pressure/portable-library-program"
)
PRESSURE_ROOT = REPOSITORY_ROOT / "tests/pressure/integrated"
CONTINUATION_REPLAY_ROOT = (
    REPOSITORY_ROOT / "tests/pressure/continuation-replay"
)
EVIDENCE_PATH = (
    REPOSITORY_ROOT
    / "implementation-programs/ISP-001/increments/INC-008/integration-evidence.json"
)
READINESS_PATH = (
    REPOSITORY_ROOT
    / "implementation-programs/ISP-001/increments/INC-008/closure-readiness-evidence.json"
)

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    import continuity_closure
    import repository_preparation
    import review_coordination
    import state_authority
    import validate_package
finally:
    sys.path.remove(str(SCRIPT_ROOT))

SPEC = importlib.util.spec_from_file_location("integrated_pressure_support", SUPPORT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load integrated pressure support from {SUPPORT_PATH}")
SUPPORT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SUPPORT
SPEC.loader.exec_module(SUPPORT)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IntegratedFixtureContractTests(unittest.TestCase):
    def test_portable_library_fixture_is_neutral_and_complete(self) -> None:
        contract = json.loads(
            (FIXTURE_ROOT / "pilot-contract.json").read_text(encoding="utf-8")
        )
        source = (FIXTURE_ROOT / "source/implementation-plan.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(contract["schema_version"], "disposable-program-pilot/v1")
        self.assertEqual(contract["expected_requirement_count"], 9)
        self.assertEqual(sum(line.startswith("- ") for line in source.splitlines()), 9)
        self.assertEqual(len(contract["expected_stages"]), 11)
        self.assertNotRegex(source, r"\b(?:ISP|INC|REQ|P)-\d{3,}\b")

    def test_fresh_context_catalog_has_five_semantic_request_shapes(self) -> None:
        scenarios = SUPPORT.load_scenario_catalog(PRESSURE_ROOT / "scenarios.json")
        self.assertEqual(
            tuple(item.scenario_id for item in scenarios),
            SUPPORT.EXPECTED_SCENARIO_IDS,
        )
        for scenario in scenarios:
            prompt = (REPOSITORY_ROOT / scenario.prompt_path).read_text(
                encoding="utf-8"
            )
            self.assertTrue(prompt.strip())
            self.assertNotIn("## Apply Universal Gates", prompt)
            self.assertNotIn("approval matrix", prompt.lower())


class DisposableProgramPilotTests(unittest.TestCase):
    def test_repository_backed_pilot_runs_source_capture_through_separate_later_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = SUPPORT.DisposableProgramPilot(
                REPOSITORY_ROOT, Path(directory)
            ).run()

        contract = json.loads(
            (FIXTURE_ROOT / "pilot-contract.json").read_text(encoding="utf-8")
        )
        self.assertEqual(tuple(evidence["stages"]), tuple(contract["expected_stages"]))
        self.assertEqual(evidence["requirement_count"], 9)
        for field in (
            "program_authority_valid",
            "selected_workspace_unchanged",
            "bounded_amendment_allowed",
            "review_bundle_valid",
            "increment_acceptance_allowed",
            "resume_valid",
            "continuation_authority_valid",
            "compound_checkpoint_valid",
            "pilot_reconciliation_valid",
            "pilot_closure_packet_valid",
            "draft_pr_denied_without_grant",
            "draft_pr_decision_authorized_with_exact_grant",
            "draft_pr_same_turn_blocked_without_remote",
        ):
            self.assertTrue(evidence[field], field)
        for field in (
            "repository_has_remote",
            "new_commit_created",
            "draft_pr_performed",
            "isp_001_closed",
        ):
            self.assertFalse(evidence[field], field)


class InterruptionAndAtomicityTests(unittest.TestCase):
    def test_evaluator_environment_excludes_unrelated_parent_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory) / "codex-home"
            codex_home.mkdir()
            with mock.patch.dict(
                os.environ,
                {
                    "PATH": "/usr/bin:/bin",
                    "LANG": "C.UTF-8",
                    "SYNTHETIC_SECRET": "must-not-reach-child",
                },
                clear=True,
            ):
                environment = SUPPORT.build_isolated_evaluator_environment(codex_home)

        self.assertEqual(environment["CODEX_HOME"], str(codex_home))
        self.assertEqual(environment["HOME"], str(codex_home.parent))
        self.assertEqual(environment["PATH"], "/usr/bin:/bin")
        self.assertNotIn("SYNTHETIC_SECRET", environment)

    def test_atomic_status_replacement_failure_preserves_prior_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            path.write_text('{"state":"accepted"}\n', encoding="utf-8")
            before = path.read_bytes()
            before_sha256 = hashlib.sha256(before).hexdigest()
            with mock.patch.object(state_authority.os, "replace", side_effect=OSError("injected")):
                with self.assertRaises(OSError):
                    state_authority.atomic_replace_json(
                        path, {"state": "implementing"}, before_sha256
                    )
            self.assertEqual(path.read_bytes(), before)

    def test_append_only_failure_preserves_exact_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authorizations.jsonl"
            path.write_text(
                '{"authorization_id":"EXISTING"}\n', encoding="utf-8"
            )
            before = path.read_bytes()
            with mock.patch.object(state_authority.os, "replace", side_effect=OSError("injected")):
                with self.assertRaises(OSError):
                    state_authority.atomic_append_json_line(
                        path,
                        {"authorization_id": "NEW"},
                        hashlib.sha256(before).hexdigest(),
                    )
            self.assertEqual(path.read_bytes(), before)


class SchemaEvolutionTests(unittest.TestCase):
    def test_current_schemas_pass_and_unknown_versions_stop_explicitly(self) -> None:
        scenarios = json.loads(
            (PRESSURE_ROOT / "scenarios.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            len(SUPPORT.load_scenario_catalog(PRESSURE_ROOT / "scenarios.json")),
            5,
        )
        changed = dict(scenarios)
        changed["schema_version"] = "fresh-context-scenario-catalog/v999"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenarios.json"
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported"):
                SUPPORT.load_scenario_catalog(path)

        brief = continuity_closure.LeanBrief(
            schema_version="implementation-continuity-evidence/v1",
            program_id="portable-library",
            program_revision=1,
            increment_id="catalog-readiness",
            title="Catalog readiness",
            outcome="Validate the catalog.",
            requirement_ids=("LIBRARY-CATALOG-001",),
            acceptance="Use the approved criteria.",
            approval_mode="approval:full-increment",
            workspace_path="/workspace/portable-library",
            workspace_branch="main",
            workspace_base_commit="a" * 40,
            workspace_head_commit="b" * 40,
            status_path="state/status.json",
            status_sha256="1" * 64,
            handoff_path="increments/catalog-foundation/handoff.md",
            handoff_sha256="2" * 64,
            unresolved_user_decision="none",
            optional_context=(),
        )
        self.assertEqual(continuity_closure.validate_increment_brief(brief), [])
        self.assertIn(
            "unsupported",
            " ".join(
                continuity_closure.validate_increment_brief(
                    replace(brief, schema_version="implementation-continuity-evidence/v999")
                )
            ),
        )

        review = json.loads(
            (
                REPOSITORY_ROOT
                / "tests/fixtures/review-coordination/portable-archive-run/review-evidence.json"
            ).read_text(encoding="utf-8")
        )
        packet = (
            REPOSITORY_ROOT
            / "tests/fixtures/review-coordination/portable-archive-run/review-packet.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(review_coordination.validate_review_bundle(review, packet), [])
        review["schema_version"] = "implementation-review-evidence/v999"
        self.assertIn(
            "unsupported",
            " ".join(review_coordination.validate_review_bundle(review, packet)),
        )


class PackageDocumentationAndNamingTests(unittest.TestCase):
    def test_package_links_and_concise_front_door_pass(self) -> None:
        self.assertEqual(validate_package.validate_package(REPOSITORY_ROOT), [])
        front_door = (
            REPOSITORY_ROOT / "skills/implementing-staged-plans/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertLess(len(front_door.splitlines()), 250)
        self.assertIn("references/continuity-closure.md", front_door)

    def test_semantic_inventory_covers_every_surface_kind_without_blacklist(self) -> None:
        records = (
            repository_preparation.SemanticNameRecord(
                "tests/integrated_pressure_support.py",
                "path",
                "new",
                "integrated validation harness",
                "compose accepted owners",
                "none",
                "none",
                "test",
                "new test-only module",
            ),
            repository_preparation.SemanticNameRecord(
                "DisposableProgramPilot",
                "symbol",
                "new",
                "temporary repository lifecycle",
                "exercise a disposable source-to-closure program",
                "none",
                "none",
                "private",
                "new test-only API",
            ),
            repository_preparation.SemanticNameRecord(
                "evaluate-fresh-contexts",
                "command",
                "new",
                "authorized model evidence",
                "run five isolated read-only evaluations",
                "durable-domain",
                "fresh-context evidence runner",
                "test",
                "new bounded command",
            ),
            repository_preparation.SemanticNameRecord(
                "portable-library-program",
                "test-or-fixture",
                "new",
                "neutral repository pilot",
                "provide source and lifecycle expectations",
                "none",
                "none",
                "test",
                "synthetic fixture",
            ),
            repository_preparation.SemanticNameRecord(
                "source-to-closure pilot",
                "heading",
                "new",
                "isolated pilot report",
                "distinguish pilot closure from ISP-001 closure",
                "durable-domain",
                "pilot evidence report",
                "repository-only",
                "new evidence heading",
            ),
            repository_preparation.SemanticNameRecord(
                "implementation-integration-evidence/v1",
                "schema-or-identifier",
                "new",
                "combined readiness evidence",
                "reject incomplete or unsupported evidence",
                "durable-domain",
                "integrated evidence schema",
                "persisted",
                "versioned schema; unsupported versions stop",
            ),
            repository_preparation.SemanticNameRecord(
                "tests/pressure/integrated/results/direct-request.txt",
                "generated-path",
                "new",
                "raw model evidence",
                "preserve output before verdicting",
                "durable-domain",
                "pressure evidence owner",
                "test",
                "new sanitized evidence path",
            ),
        )
        self.assertEqual(
            {record.surface_kind for record in records},
            repository_preparation.SURFACE_KINDS,
        )
        self.assertEqual(
            repository_preparation.validate_semantic_naming_inventory(records), []
        )


class FreshContextEvidenceTests(unittest.TestCase):
    def test_raw_outputs_precede_complete_evidence_backed_verdicts(self) -> None:
        scenarios = SUPPORT.load_scenario_catalog(PRESSURE_ROOT / "scenarios.json")
        verdict_path = PRESSURE_ROOT / "verdicts.json"
        self.assertTrue(verdict_path.is_file())
        verdict_document = json.loads(verdict_path.read_text(encoding="utf-8"))
        self.assertEqual(
            verdict_document.get("schema_version"), "fresh-context-verdicts/v1"
        )
        verdicts = verdict_document.get("verdicts")
        self.assertIsInstance(verdicts, list)
        self.assertEqual(
            [item.get("id") for item in verdicts],
            list(SUPPORT.EXPECTED_SCENARIO_IDS),
        )
        for scenario, verdict in zip(scenarios, verdicts, strict=True):
            result_path = REPOSITORY_ROOT / scenario.result_path
            self.assertTrue(result_path.is_file())
            result_text = result_path.read_text(encoding="utf-8")
            self.assertIn("schema_version: fresh-context-evidence/v1", result_text)
            self.assertIn(f"scenario_id: {scenario.scenario_id}", result_text)
            self.assertEqual(verdict.get("outcome"), "pass")
            self.assertEqual(verdict.get("result_sha256"), digest(result_path))
            self.assertEqual(
                verdict.get("prompt_sha256"),
                digest(REPOSITORY_ROOT / scenario.prompt_path),
            )
            self.assertTrue(verdict.get("evidence"))
            self.assertTrue(verdict.get("limitations"))
            self.assertNotIn("score", verdict)


class ContinuationReplayContractTests(unittest.TestCase):
    def test_catalog_has_exact_routes_and_explicit_skill_prompts(self) -> None:
        catalog = json.loads(
            (CONTINUATION_REPLAY_ROOT / "scenarios.json").read_text(
                encoding="utf-8"
            )
        )
        scenarios = SUPPORT.load_continuation_replay(
            CONTINUATION_REPLAY_ROOT / "scenarios.json"
        )
        self.assertEqual(
            tuple(item.scenario_id for item in scenarios),
            ("immediate-continuation", "later-continuation"),
        )
        self.assertEqual(
            scenarios[0].expected_boundary,
            catalog["scenarios"][0]["expected_boundary"],
        )
        for scenario in scenarios:
            prompt_path = REPOSITORY_ROOT / scenario.prompt_path
            self.assertTrue(prompt_path.is_file())
            self.assertFalse(prompt_path.is_symlink())
            self.assertEqual(
                prompt_path.read_text(encoding="utf-8").splitlines()[0],
                "$implementing-staged-plans",
            )

    def test_catalog_rejects_wrong_boundary_types_before_evaluation(self) -> None:
        for wrong_value in (1, True, [], {}):
            with self.subTest(wrong_value=wrong_value):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    replay_root = root / "tests/pressure/continuation-replay"
                    shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
                    catalog_path = replay_root / "scenarios.json"
                    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
                    catalog["scenarios"][0]["expected_boundary"] = wrong_value
                    catalog_path.write_text(
                        json.dumps(catalog, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    output_directory = replay_root / "results"

                    with (
                        mock.patch.object(SUPPORT, "REPOSITORY_ROOT", root),
                        mock.patch.object(SUPPORT, "run_command") as run_command,
                    ):
                        with self.assertRaisesRegex(
                            ValueError, "expected_boundary must be a string"
                        ):
                            SUPPORT.evaluate_continuation_replay(
                                catalog_path=catalog_path,
                                output_directory=output_directory,
                                evaluator="codex",
                            )
                    run_command.assert_not_called()
                    self.assertFalse(output_directory.exists())

    def test_absent_live_results_are_valid_and_report_not_run(self) -> None:
        if (CONTINUATION_REPLAY_ROOT / "results").exists() or (
            CONTINUATION_REPLAY_ROOT / "verdicts.json"
        ).exists():
            self.skipTest("live continuation replay evidence is present")
        self.assertFalse((CONTINUATION_REPLAY_ROOT / "results").exists())
        self.assertFalse((CONTINUATION_REPLAY_ROOT / "verdicts.json").exists())
        self.assertEqual(
            SUPPORT.validate_continuation_replay_evidence(REPOSITORY_ROOT), []
        )

    def test_evidence_requires_complete_digest_bound_results_and_verdicts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay_root = root / "tests/pressure/continuation-replay"
            shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
            scenarios = SUPPORT.load_continuation_replay(
                replay_root / "scenarios.json"
            )
            verdicts = []
            for scenario in scenarios:
                prompt_path = root / scenario.prompt_path
                result_path = root / scenario.result_path
                result_path.parent.mkdir(parents=True, exist_ok=True)
                result_path.write_text(
                    "schema_version: implementation-continuation-replay-evidence/v1\n"
                    f"scenario_id: {scenario.scenario_id}\n"
                    f"prompt_sha256: {digest(prompt_path)}\n"
                    "evaluator: codex\n"
                    "client_version: codex 1.2.3\n"
                    "sandbox: read-only\n"
                    "session: ephemeral\n"
                    "exit_code: 0\n"
                    f"expected_boundary: {scenario.expected_boundary}\n"
                    "\n--- response ---\n"
                    "Synthetic response.\n",
                    encoding="utf-8",
                )
                verdicts.append(
                    {
                        "id": scenario.scenario_id,
                        "outcome": "pass",
                        "prompt_sha256": digest(prompt_path),
                        "result_sha256": digest(result_path),
                        "evidence": "The raw response reached the expected boundary.",
                        "limitations": "Synthetic evaluator fixture only.",
                    }
                )
            (replay_root / "verdicts.json").write_text(
                json.dumps(
                    {
                        "schema_version": "implementation-continuation-replay-verdicts/v1",
                        "verdicts": verdicts,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                SUPPORT.validate_continuation_replay_evidence(root), []
            )
            malformed_verdicts = [*verdicts, "unexpected"]
            (replay_root / "verdicts.json").write_text(
                json.dumps(
                    {
                        "schema_version": "implementation-continuation-replay-verdicts/v1",
                        "verdicts": malformed_verdicts,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertIn(
                "continuation replay verdict document is incomplete",
                SUPPORT.validate_continuation_replay_evidence(root),
            )
            (replay_root / "verdicts.json").write_text(
                json.dumps(
                    {
                        "schema_version": "implementation-continuation-replay-verdicts/v1",
                        "verdicts": verdicts,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            first_result = root / scenarios[0].result_path
            first_result.write_bytes(first_result.read_bytes() + b"tampered\n")
            self.assertIn(
                "result digest mismatch",
                " ".join(SUPPORT.validate_continuation_replay_evidence(root)),
            )

    def test_evaluator_uses_fresh_sessions_and_never_overwrites_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay_root = root / "tests/pressure/continuation-replay"
            shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
            calls: list[tuple[tuple[str, ...], Path]] = []

            def fake_run(arguments, *, cwd, timeout=30, environment=None):
                calls.append((tuple(arguments), Path(cwd)))
                if tuple(arguments) == ("codex", "--version"):
                    return subprocess.CompletedProcess(
                        arguments, 0, stdout="codex 1.2.3\n", stderr=""
                    )
                return subprocess.CompletedProcess(
                    arguments,
                    0,
                    stdout=(
                        '{"type":"item.completed","item":'
                        '{"type":"agent_message","text":"Synthetic response."}}\n'
                    ),
                    stderr="",
                )

            def fake_isolation(isolated_root):
                codex_home = Path(isolated_root) / "codex-home"
                codex_home.mkdir()
                return codex_home

            with (
                mock.patch.object(SUPPORT, "REPOSITORY_ROOT", root),
                mock.patch.object(SUPPORT, "run_command", side_effect=fake_run),
                mock.patch.object(
                    SUPPORT,
                    "_build_isolated_evaluation_root",
                    side_effect=fake_isolation,
                ),
            ):
                paths = SUPPORT.evaluate_continuation_replay(
                    catalog_path=replay_root / "scenarios.json",
                    output_directory=replay_root / "results",
                    evaluator="codex",
                )
                self.assertEqual(len(paths), 2)
                evaluation_calls = [call for call in calls if "exec" in call[0]]
                self.assertEqual(len(evaluation_calls), 2)
                self.assertNotEqual(
                    evaluation_calls[0][1], evaluation_calls[1][1]
                )
                for arguments, _cwd in evaluation_calls:
                    self.assertIn("--ephemeral", arguments)
                    self.assertIn("read-only", arguments)
                with self.assertRaisesRegex(ValueError, "must all be absent"):
                    SUPPORT.evaluate_continuation_replay(
                        catalog_path=replay_root / "scenarios.json",
                        output_directory=replay_root / "results",
                        evaluator="codex",
                    )

    def test_continuation_evaluator_failure_reports_concise_detail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay_root = root / "tests/pressure/continuation-replay"
            shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)

            def fake_run(arguments, *, cwd, timeout=30, environment=None):
                if tuple(arguments) == ("codex", "--version"):
                    return subprocess.CompletedProcess(
                        arguments, 0, stdout="codex 1.2.3\n", stderr=""
                    )
                return subprocess.CompletedProcess(
                    arguments,
                    7,
                    stdout="",
                    stderr="provider unavailable\n",
                )

            def fake_isolation(isolated_root):
                codex_home = Path(isolated_root) / "codex-home"
                codex_home.mkdir()
                return codex_home

            with (
                mock.patch.object(SUPPORT, "REPOSITORY_ROOT", root),
                mock.patch.object(SUPPORT, "run_command", side_effect=fake_run),
                mock.patch.object(
                    SUPPORT,
                    "_build_isolated_evaluation_root",
                    side_effect=fake_isolation,
                ),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "continuation replay evaluator failed for immediate-continuation: provider unavailable",
                ):
                    SUPPORT.evaluate_continuation_replay(
                        catalog_path=replay_root / "scenarios.json",
                        output_directory=replay_root / "results",
                        evaluator="codex",
                    )

    def test_second_evaluator_failure_leaves_no_partial_results_and_is_retryable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay_root = root / "tests/pressure/continuation-replay"
            shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
            evaluation_calls = 0
            fail_second_evaluation = True

            def fake_run(arguments, *, cwd, timeout=30, environment=None):
                nonlocal evaluation_calls
                if tuple(arguments) == ("codex", "--version"):
                    return subprocess.CompletedProcess(
                        arguments, 0, stdout="codex 1.2.3\n", stderr=""
                    )
                evaluation_calls += 1
                if fail_second_evaluation and evaluation_calls == 2:
                    return subprocess.CompletedProcess(
                        arguments,
                        7,
                        stdout="",
                        stderr="provider unavailable\n",
                    )
                return subprocess.CompletedProcess(
                    arguments,
                    0,
                    stdout=(
                        '{"type":"item.completed","item":'
                        '{"type":"agent_message","text":"Synthetic response."}}\n'
                    ),
                    stderr="",
                )

            def fake_isolation(isolated_root):
                codex_home = Path(isolated_root) / "codex-home"
                codex_home.mkdir()
                return codex_home

            output_directory = replay_root / "results"
            with (
                mock.patch.object(SUPPORT, "REPOSITORY_ROOT", root),
                mock.patch.object(SUPPORT, "run_command", side_effect=fake_run),
                mock.patch.object(
                    SUPPORT,
                    "_build_isolated_evaluation_root",
                    side_effect=fake_isolation,
                ),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "continuation replay evaluator failed for later-continuation: provider unavailable",
                ):
                    SUPPORT.evaluate_continuation_replay(
                        catalog_path=replay_root / "scenarios.json",
                        output_directory=output_directory,
                        evaluator="codex",
                    )
                self.assertFalse(output_directory.exists())

                fail_second_evaluation = False
                paths = SUPPORT.evaluate_continuation_replay(
                    catalog_path=replay_root / "scenarios.json",
                    output_directory=output_directory,
                    evaluator="codex",
                )

            self.assertEqual(
                tuple(path.name for path in paths),
                ("immediate-continuation.txt", "later-continuation.txt"),
            )
            self.assertTrue(all(path.is_file() for path in paths))

    def test_second_publication_failure_removes_owned_results_and_is_retryable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay_root = root / "tests/pressure/continuation-replay"
            shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
            real_create = SUPPORT._atomic_create_text
            publication_calls = 0
            fail_publication = True

            def fake_run(arguments, *, cwd, timeout=30, environment=None):
                if tuple(arguments) == ("codex", "--version"):
                    return subprocess.CompletedProcess(
                        arguments, 0, stdout="codex 1.2.3\n", stderr=""
                    )
                return subprocess.CompletedProcess(
                    arguments,
                    0,
                    stdout=(
                        '{"type":"item.completed","item":'
                        '{"type":"agent_message","text":"Synthetic response."}}\n'
                    ),
                    stderr="",
                )

            def fake_isolation(isolated_root):
                codex_home = Path(isolated_root) / "codex-home"
                codex_home.mkdir()
                return codex_home

            def fail_second_create(path, value, *, trusted_root=None):
                nonlocal publication_calls
                publication_calls += 1
                if fail_publication and publication_calls == 2:
                    raise OSError("publication unavailable")
                return real_create(path, value, trusted_root=trusted_root)

            output_directory = replay_root / "results"
            with (
                mock.patch.object(SUPPORT, "REPOSITORY_ROOT", root),
                mock.patch.object(SUPPORT, "run_command", side_effect=fake_run),
                mock.patch.object(
                    SUPPORT,
                    "_build_isolated_evaluation_root",
                    side_effect=fake_isolation,
                ),
                mock.patch.object(
                    SUPPORT, "_atomic_create_text", side_effect=fail_second_create
                ),
            ):
                with self.assertRaisesRegex(OSError, "publication unavailable"):
                    SUPPORT.evaluate_continuation_replay(
                        catalog_path=replay_root / "scenarios.json",
                        output_directory=output_directory,
                        evaluator="codex",
                    )
                self.assertEqual(tuple(output_directory.iterdir()), ())

                fail_publication = False
                paths = SUPPORT.evaluate_continuation_replay(
                    catalog_path=replay_root / "scenarios.json",
                    output_directory=output_directory,
                    evaluator="codex",
                )

            self.assertTrue(all(path.is_file() for path in paths))

    def test_incomplete_publication_recovery_preserves_foreign_replacement(
        self,
    ) -> None:
        class LegacyPublicationError(BaseException):
            add_note = None

        for exception_type, note_supported in (
            (OSError, True),
            (KeyboardInterrupt, True),
            (SystemExit, True),
            (LegacyPublicationError, False),
        ):
            with self.subTest(exception_type=exception_type.__name__):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    replay_root = root / "tests/pressure/continuation-replay"
                    shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
                    real_create = SUPPORT._atomic_create_text
                    publication_calls = 0
                    first_result = (
                        replay_root / "results/immediate-continuation.txt"
                    )

                    def fake_run(arguments, *, cwd, timeout=30, environment=None):
                        if tuple(arguments) == ("codex", "--version"):
                            return subprocess.CompletedProcess(
                                arguments,
                                0,
                                stdout="codex 1.2.3\n",
                                stderr="",
                            )
                        return subprocess.CompletedProcess(
                            arguments,
                            0,
                            stdout=(
                                '{"type":"item.completed","item":'
                                '{"type":"agent_message","text":"Synthetic response."}}\n'
                            ),
                            stderr="",
                        )

                    def fake_isolation(isolated_root):
                        codex_home = Path(isolated_root) / "codex-home"
                        codex_home.mkdir()
                        return codex_home

                    def replace_before_second_failure(
                        path,
                        value,
                        *,
                        trusted_root=None,
                        first_result=first_result,
                        exception_type=exception_type,
                        real_create=real_create,
                    ):
                        nonlocal publication_calls
                        publication_calls += 1
                        if publication_calls == 2:
                            first_result.unlink()
                            first_result.write_text("foreign\n", encoding="utf-8")
                            raise exception_type("publication unavailable")
                        return real_create(path, value, trusted_root=trusted_root)

                    with (
                        mock.patch.object(SUPPORT, "REPOSITORY_ROOT", root),
                        mock.patch.object(
                            SUPPORT, "run_command", side_effect=fake_run
                        ),
                        mock.patch.object(
                            SUPPORT,
                            "_build_isolated_evaluation_root",
                            side_effect=fake_isolation,
                        ),
                        mock.patch.object(
                            SUPPORT,
                            "_atomic_create_text",
                            side_effect=replace_before_second_failure,
                        ),
                    ):
                        with self.assertRaises(exception_type) as raised:
                            SUPPORT.evaluate_continuation_replay(
                                catalog_path=replay_root / "scenarios.json",
                                output_directory=replay_root / "results",
                                evaluator="codex",
                            )

                    self.assertEqual(str(raised.exception), "publication unavailable")
                    recovery_note = (
                        "continuation replay publication recovery failed for: "
                        "tests/pressure/continuation-replay/results/"
                        "immediate-continuation.txt"
                    )
                    if note_supported:
                        self.assertIn(
                            recovery_note,
                            getattr(raised.exception, "__notes__", ()),
                        )
                    else:
                        self.assertEqual(
                            getattr(raised.exception, "__notes__", ()), ()
                        )
                    self.assertEqual(
                        first_result.read_text(encoding="utf-8"), "foreign\n"
                    )
                    self.assertFalse(
                        (replay_root / "results/later-continuation.txt").exists()
                    )

    def test_replay_evidence_binds_exact_transmitted_prompt_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay_root = root / "tests/pressure/continuation-replay"
            shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
            scenarios = SUPPORT.load_continuation_replay(
                replay_root / "scenarios.json"
            )
            transmitted: dict[str, bytes] = {}
            evaluation_index = 0

            def fake_run(arguments, *, cwd, timeout=30, environment=None):
                nonlocal evaluation_index
                if tuple(arguments) == ("codex", "--version"):
                    return subprocess.CompletedProcess(
                        arguments, 0, stdout="codex 1.2.3\n", stderr=""
                    )
                scenario = scenarios[evaluation_index]
                prompt = arguments[-1]
                transmitted[scenario.scenario_id] = prompt.encode("utf-8")
                if evaluation_index == 0:
                    (root / scenario.prompt_path).write_text(
                        prompt + "\nmutated after evaluator input\n",
                        encoding="utf-8",
                    )
                evaluation_index += 1
                return subprocess.CompletedProcess(
                    arguments,
                    0,
                    stdout=(
                        '{"type":"item.completed","item":'
                        '{"type":"agent_message","text":"Synthetic response."}}\n'
                    ),
                    stderr="",
                )

            def fake_isolation(isolated_root):
                codex_home = Path(isolated_root) / "codex-home"
                codex_home.mkdir()
                return codex_home

            with (
                mock.patch.object(SUPPORT, "REPOSITORY_ROOT", root),
                mock.patch.object(SUPPORT, "run_command", side_effect=fake_run),
                mock.patch.object(
                    SUPPORT,
                    "_build_isolated_evaluation_root",
                    side_effect=fake_isolation,
                ),
            ):
                result_paths = SUPPORT.evaluate_continuation_replay(
                    catalog_path=replay_root / "scenarios.json",
                    output_directory=replay_root / "results",
                    evaluator="codex",
                )

            verdicts = []
            for scenario, result_path in zip(
                scenarios, result_paths, strict=True
            ):
                headers = SUPPORT._evidence_headers(
                    result_path.read_text(encoding="utf-8")
                )
                transmitted_digest = hashlib.sha256(
                    transmitted[scenario.scenario_id]
                ).hexdigest()
                self.assertEqual(headers["prompt_sha256"], transmitted_digest)
                verdicts.append(
                    {
                        "id": scenario.scenario_id,
                        "outcome": "pass",
                        "prompt_sha256": transmitted_digest,
                        "result_sha256": digest(result_path),
                        "evidence": "Synthetic response reached the boundary.",
                        "limitations": "Deterministic fake evaluator only.",
                    }
                )
            self.assertNotEqual(
                digest(root / scenarios[0].prompt_path),
                verdicts[0]["prompt_sha256"],
            )
            (replay_root / "verdicts.json").write_text(
                json.dumps(
                    {
                        "schema_version": (
                            "implementation-continuation-replay-verdicts/v1"
                        ),
                        "verdicts": verdicts,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                SUPPORT.validate_continuation_replay_evidence(root), []
            )

    def test_atomic_result_creation_preserves_a_competing_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "result.txt"
            real_link = SUPPORT.os.link

            def competing_link(source, destination, **kwargs):
                descriptor = SUPPORT.os.open(
                    destination,
                    SUPPORT.os.O_WRONLY | SUPPORT.os.O_CREAT | SUPPORT.os.O_EXCL,
                    0o600,
                    dir_fd=kwargs["dst_dir_fd"],
                )
                with SUPPORT.os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    stream.write("foreign\n")
                return real_link(source, destination, **kwargs)

            with mock.patch.object(
                SUPPORT.os, "link", side_effect=competing_link
            ):
                with self.assertRaisesRegex(ValueError, "appeared before creation"):
                    SUPPORT._atomic_create_text(target, "candidate\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "foreign\n")

    def test_atomic_result_creation_ignores_post_link_cleanup_failures(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "result.txt"
            real_unlink = SUPPORT.os.unlink
            real_close = SUPPORT.os.close

            def unlink_then_report_failure(path, *, dir_fd=None):
                real_unlink(path, dir_fd=dir_fd)
                raise OSError("temporary cleanup unavailable")

            def close_then_report_failure(descriptor):
                real_close(descriptor)
                raise OSError("directory cleanup unavailable")

            with (
                mock.patch.object(
                    SUPPORT.os, "unlink", side_effect=unlink_then_report_failure
                ),
                mock.patch.object(
                    SUPPORT.os, "close", side_effect=close_then_report_failure
                ),
            ):
                created_identity = SUPPORT._atomic_create_text(
                    target, "candidate\n"
                )

            target_identity = target.stat(follow_symlinks=False)
            self.assertEqual(
                created_identity,
                (target_identity.st_dev, target_identity.st_ino),
            )
            self.assertEqual(target.read_text(encoding="utf-8"), "candidate\n")

    def test_atomic_result_creation_falls_back_without_descriptor_apis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "result.txt"
            real_open = SUPPORT.os.open

            def guarded_open(path, flags, mode=0o777, *, dir_fd=None):
                if dir_fd is not None:
                    raise AssertionError("descriptor-relative open is unsupported")
                return real_open(path, flags, mode)

            with (
                mock.patch.object(SUPPORT.os, "supports_dir_fd", set()),
                mock.patch.object(SUPPORT.os, "supports_follow_symlinks", set()),
                mock.patch.object(SUPPORT.os, "open", side_effect=guarded_open),
                mock.patch.object(
                    SUPPORT.os,
                    "link",
                    side_effect=AssertionError("hard-link fallback was not selected"),
                ),
            ):
                SUPPORT._atomic_create_text(target, "candidate\n")

            self.assertEqual(target.read_text(encoding="utf-8"), "candidate\n")

    def test_symlinked_result_is_invalid_not_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            replay_root = root / "tests/pressure/continuation-replay"
            shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
            result_path = replay_root / "results/immediate-continuation.txt"
            result_path.parent.mkdir()
            result_path.symlink_to(replay_root / "prompts/immediate-continuation.md")

            self.assertIn(
                "result is not a regular non-symlink file",
                " ".join(SUPPORT.validate_continuation_replay_evidence(root)),
            )

    def test_symlinked_result_directory_is_rejected_by_validator_and_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repository"
            replay_root = root / "tests/pressure/continuation-replay"
            shutil.copytree(CONTINUATION_REPLAY_ROOT, replay_root)
            outside = Path(directory) / "outside-results"
            outside.mkdir()
            (replay_root / "results").symlink_to(outside, target_is_directory=True)

            self.assertIn(
                "symlinked path component",
                " ".join(SUPPORT.validate_continuation_replay_evidence(root)),
            )
            with (
                mock.patch.object(SUPPORT, "REPOSITORY_ROOT", root),
                mock.patch.object(SUPPORT, "run_command") as run_command,
            ):
                with self.assertRaisesRegex(ValueError, "symlinked path component"):
                    SUPPORT.evaluate_continuation_replay(
                        catalog_path=replay_root / "scenarios.json",
                        output_directory=replay_root / "results",
                        evaluator="codex",
                    )
            run_command.assert_not_called()
            self.assertEqual(tuple(outside.iterdir()), ())


class IntegratedEvidenceTests(unittest.TestCase):
    def test_integration_and_closure_readiness_evidence_are_bound_without_closure(self) -> None:
        self.assertTrue(EVIDENCE_PATH.is_file())
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(SUPPORT.validate_integrated_evidence(evidence), [])
        self.assertTrue(READINESS_PATH.is_file())
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(readiness.get("schema_version"), "implementation-closure-readiness-evidence/v1")
        self.assertEqual(readiness.get("integration_evidence_sha256"), digest(EVIDENCE_PATH))
        self.assertFalse(readiness.get("closure_reconciliation_performed"))
        self.assertFalse(readiness.get("program_closed"))
        self.assertFalse(readiness.get("real_draft_pr_decision_performed"))


if __name__ == "__main__":
    unittest.main()
