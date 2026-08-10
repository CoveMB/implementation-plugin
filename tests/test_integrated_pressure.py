import hashlib
import importlib.util
import json
import os
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
