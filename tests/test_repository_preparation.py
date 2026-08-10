import importlib.util
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "repository_preparation.py"
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "tests/fixtures/repository-preparation/portable-archive-workspace"
)

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC = importlib.util.spec_from_file_location("repository_preparation", SCRIPT_PATH)
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load repository preparation from {SCRIPT_PATH}")
    PREPARATION = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = PREPARATION
    SPEC.loader.exec_module(PREPARATION)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def run_git(repository: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=check,
        capture_output=True,
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GitFixture:
    def __init__(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "portable-archive-workspace"
        self.root.mkdir()
        run_git(self.root, "init", "-b", "archive-maintenance")
        run_git(self.root, "config", "user.name", "Archive Fixture")
        run_git(self.root, "config", "user.email", "archive@example.invalid")
        (self.root / "catalog.txt").write_text("first entry\n", encoding="utf-8")
        run_git(self.root, "add", "catalog.txt")
        run_git(self.root, "commit", "-m", "seed archive")
        self.base = run_git(self.root, "rev-parse", "HEAD").stdout.decode().strip()

    def close(self) -> None:
        self.temporary_directory.cleanup()


def observation(
    *,
    repository: str = "/tmp/portable-archive-workspace",
    branch: str = "archive-maintenance",
    base: str = "b" * 40,
    head: str = "a" * 40,
    staged: tuple[str, ...] = (),
    modified: tuple[str, ...] = (),
    untracked: tuple[str, ...] = (),
    conflicted: tuple[str, ...] = (),
    operation: str | None = None,
):
    return PREPARATION.RepositoryObservation(
        repository=repository,
        path=repository,
        branch=branch,
        base_commit=base,
        head_commit=head,
        staged_paths=staged,
        modified_paths=modified,
        untracked_paths=untracked,
        conflicted_paths=conflicted,
        active_git_operation=operation,
    )


def inspection(**overrides):
    values = {
        "schema_version": PREPARATION.REPOSITORY_INSPECTION_SCHEMA,
        "observation": observation(),
        "git_directory": "/tmp/portable-archive-workspace/.git",
        "git_common_directory": "/tmp/portable-archive-workspace/.git",
        "selected_base_is_ancestor": True,
        "status_format": "porcelain-v2-z",
    }
    values.update(overrides)
    return PREPARATION.RepositoryInspection(**values)


def drift_context(**overrides):
    prior = inspection()
    values = {
        "previous": prior,
        "current": prior,
        "relevant_paths": ("archive/catalog.py",),
        "protected_paths": ("archive/preserved.txt",),
        "accepted_existing_paths": (),
        "managed_paths": (),
        "dependency_paths": (),
        "dependency_compatibility_confirmed": True,
        "pre_existing_failures": (),
        "current_failures": (),
        "relevant_failures": (),
        "reusable_candidates": (),
        "selected_reuse": (),
        "requirements_changed": False,
        "protected_contract_changed": False,
        "provisional_assumption_invalidated": False,
    }
    values.update(overrides)
    return PREPARATION.DriftContext(**values)


class FixtureContractTests(unittest.TestCase):
    def test_neutral_scenario_catalog_covers_required_repository_conditions(self) -> None:
        catalog = json.loads((FIXTURE_ROOT / "scenarios.json").read_text(encoding="utf-8"))
        identifiers = {item["id"] for item in catalog["scenarios"]}
        self.assertTrue(
            {
                "unrelated-dirty-note",
                "untracked-import-file",
                "active-merge",
                "selected-base-moved",
                "new-relevant-test-failure",
                "managed-output-without-owner",
                "reusable-parser-changed",
                "incompatible-manifest-change",
                "invalidated-file-layout-assumption",
            }.issubset(identifiers)
        )
        fixture_text = "".join(path.read_text(encoding="utf-8") for path in FIXTURE_ROOT.iterdir())
        self.assertNotRegex(fixture_text, r"\b(?:ISP|INC|REQ)-\d")


class RepositoryInspectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = GitFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_inspection_collects_staged_modified_untracked_rename_and_safe_paths(self) -> None:
        root = self.fixture.root
        (root / "catalog.txt").write_text("changed\n", encoding="utf-8")
        run_git(root, "add", "catalog.txt")
        run_git(root, "mv", "catalog.txt", "renamed catalog.txt")
        unusual = root / "new\nentry.txt"
        unusual.write_text("new\n", encoding="utf-8")

        result = PREPARATION.inspect_repository(root, self.fixture.base)

        self.assertEqual(result.observation.branch, "archive-maintenance")
        self.assertEqual(result.observation.base_commit, self.fixture.base)
        self.assertEqual(result.observation.repository, str(root.resolve()))
        self.assertIn("catalog.txt", result.observation.staged_paths)
        self.assertIn("renamed catalog.txt", result.observation.staged_paths)
        self.assertIn("new\nentry.txt", result.observation.untracked_paths)
        self.assertTrue(result.selected_base_is_ancestor)
        self.assertEqual(result.status_format, "porcelain-v2-z")

    def test_detached_head_is_rejected(self) -> None:
        run_git(self.fixture.root, "checkout", "--detach", self.fixture.base)
        with self.assertRaisesRegex(PREPARATION.RepositoryInspectionError, "detached HEAD"):
            PREPARATION.inspect_repository(self.fixture.root, self.fixture.base)

    def test_git_timeout_and_failure_are_concise(self) -> None:
        with mock.patch.object(PREPARATION.subprocess, "run", side_effect=subprocess.TimeoutExpired(["git", "status"], 0.1)):
            with self.assertRaisesRegex(PREPARATION.RepositoryInspectionError, "timed out"):
                PREPARATION.inspect_repository(self.fixture.root, self.fixture.base)
        with self.assertRaisesRegex(PREPARATION.RepositoryInspectionError, "not a Git repository"):
            PREPARATION.inspect_repository(Path(self.fixture.temporary_directory.name), self.fixture.base)

    def test_operation_markers_are_resolved_through_git_paths(self) -> None:
        git_directory = Path(run_git(self.fixture.root, "rev-parse", "--git-dir").stdout.decode().strip())
        if not git_directory.is_absolute():
            git_directory = self.fixture.root / git_directory
        for marker, operation in PREPARATION._OPERATION_MARKERS.items():
            with self.subTest(marker=marker):
                marker_path = git_directory / marker
                if marker in {"rebase-merge", "rebase-apply", "sequencer"}:
                    marker_path.mkdir()
                else:
                    marker_path.write_text(self.fixture.base + "\n", encoding="ascii")
                result = PREPARATION.inspect_repository(self.fixture.root, self.fixture.base)
                self.assertEqual(result.observation.active_git_operation, operation)
                if marker_path.is_dir():
                    marker_path.rmdir()
                else:
                    marker_path.unlink()

    def test_porcelain_parser_rejects_unknown_mandatory_records_and_escaping_paths(self) -> None:
        with self.assertRaisesRegex(PREPARATION.RepositoryInspectionError, "unsupported porcelain"):
            PREPARATION._parse_porcelain_v2(b"9 unsupported\0", self.fixture.root)
        with self.assertRaisesRegex(PREPARATION.RepositoryInspectionError, "escapes repository"):
            PREPARATION._parse_porcelain_v2(b"? ../outside\0", self.fixture.root)
        with self.assertRaisesRegex(PREPARATION.RepositoryInspectionError, "invalid UTF-8"):
            PREPARATION._parse_porcelain_v2(b"# branch.head \xff\0", self.fixture.root)

    def test_porcelain_parser_records_unmerged_paths(self) -> None:
        payload = b"u UU N... 100644 100644 100644 100644 " + b"1" * 40 + b" " + b"2" * 40 + b" " + b"3" * 40 + b" conflicted catalog.txt\0"
        staged, modified, untracked, conflicted = PREPARATION._parse_porcelain_v2(payload, self.fixture.root)
        self.assertEqual(staged, ("conflicted catalog.txt",))
        self.assertEqual(modified, staged)
        self.assertEqual(conflicted, staged)
        self.assertEqual(untracked, ())


class DriftAndOwnershipTests(unittest.TestCase):
    def test_benign_unrelated_dirty_work_is_recorded(self) -> None:
        current = inspection(observation=observation(modified=("notes/private.txt",)))
        result = PREPARATION.classify_repository_drift(drift_context(current=current))
        self.assertEqual(result.category, "benign")
        self.assertIn("notes/private.txt", result.affected_paths)

    def test_relevant_and_assumption_drift_requires_plan_refresh(self) -> None:
        current = inspection(observation=observation(modified=("archive/catalog.py",)))
        result = PREPARATION.classify_repository_drift(
            drift_context(current=current, provisional_assumption_invalidated=True)
        )
        self.assertEqual(result.category, "reconcilable-relevant")
        self.assertIn("refresh", result.required_action)

    def test_base_invalidating_conditions_dominate(self) -> None:
        cases = {
            "branch": inspection(observation=observation(branch="other")),
            "head": inspection(observation=observation(head="c" * 40)),
            "ancestry": inspection(selected_base_is_ancestor=False),
            "conflict": inspection(observation=observation(conflicted=("archive/catalog.py",))),
            "operation": inspection(observation=observation(operation="rebase")),
        }
        for label, current in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    PREPARATION.classify_repository_drift(drift_context(current=current)).category,
                    "base-invalidating",
                )

    def test_contract_dependency_and_relevant_failure_invalidate(self) -> None:
        contexts = (
            drift_context(requirements_changed=True),
            drift_context(protected_contract_changed=True),
            drift_context(
                current=inspection(observation=observation(modified=("archive-lock.json",))),
                dependency_paths=("archive-lock.json",),
                dependency_compatibility_confirmed=False,
            ),
            drift_context(current_failures=("catalog-test",), relevant_failures=("catalog-test",)),
        )
        for context in contexts:
            self.assertEqual(PREPARATION.classify_repository_drift(context).category, "base-invalidating")

    def test_preexisting_unrelated_failure_does_not_become_a_regression(self) -> None:
        result = PREPARATION.classify_repository_drift(
            drift_context(pre_existing_failures=("legacy-thumbnail-test",), current_failures=("legacy-thumbnail-test",))
        )
        self.assertEqual(result.category, "benign")

    def test_overlap_requires_accepted_owner_disposition_and_managed_owner(self) -> None:
        current = observation(modified=("archive/catalog.py", "catalog/generated-index.json"))
        issues = PREPARATION.validate_plan_overlap(
            ("archive/catalog.py", "catalog/generated-index.json"),
            current,
            ("archive/catalog.py",),
            {"archive/catalog.py": "extend accepted work"},
            managed_paths=("catalog/generated-index.json",),
            managed_owners={},
        )
        self.assertTrue(any("unaccepted" in issue for issue in issues))
        self.assertTrue(any("owning mechanism" in issue for issue in issues))

    def test_reusable_candidates_must_be_accounted_for(self) -> None:
        result = PREPARATION.classify_repository_drift(
            drift_context(reusable_candidates=("archive/path_reader.py",), selected_reuse=())
        )
        self.assertEqual(result.category, "reconcilable-relevant")
        self.assertTrue(any("reusable" in reason for reason in result.reasons))


class EvidenceTests(unittest.TestCase):
    def context(self, **overrides):
        values = {
            "material_predicates": (),
            "risk_level": "low",
            "official_evidence_available": False,
            "prior_version_matches": True,
            "prior_configuration_matches": True,
            "prior_assumptions_match": True,
            "access_failure": None,
        }
        values.update(overrides)
        return PREPARATION.EvidenceContext(**values)

    def test_every_material_predicate_requires_current_official_evidence(self) -> None:
        for predicate in PREPARATION.MATERIAL_EVIDENCE_PREDICATES:
            with self.subTest(predicate=predicate):
                decision = PREPARATION.decide_evidence_refresh(
                    self.context(material_predicates=(predicate,), official_evidence_available=True)
                )
                self.assertEqual(decision.disposition, "refresh-required")

    def test_irrelevant_installed_surface_is_not_material(self) -> None:
        self.assertEqual(PREPARATION.decide_evidence_refresh(self.context()).disposition, "not-material")

    def test_unavailable_high_risk_evidence_blocks(self) -> None:
        decision = PREPARATION.decide_evidence_refresh(
            self.context(material_predicates=("security-or-privacy",), risk_level="high", access_failure="offline")
        )
        self.assertEqual(decision.disposition, "blocked")

    def test_lower_risk_reuse_requires_exact_applicability_and_failure_record(self) -> None:
        valid = PREPARATION.decide_evidence_refresh(
            self.context(material_predicates=("version-sensitive-api",), access_failure="offline")
        )
        self.assertEqual(valid.disposition, "reuse-with-residual-uncertainty")
        for mismatch in ("prior_version_matches", "prior_configuration_matches", "prior_assumptions_match"):
            with self.subTest(mismatch=mismatch):
                decision = PREPARATION.decide_evidence_refresh(
                    self.context(material_predicates=("version-sensitive-api",), access_failure="offline", **{mismatch: False})
                )
                self.assertEqual(decision.disposition, "blocked")

    def test_evidence_record_validation_is_schema_and_field_complete(self) -> None:
        fixture = json.loads((FIXTURE_ROOT / "evidence.json").read_text(encoding="utf-8"))
        valid = PREPARATION.EvidenceRecord(**fixture["valid_record"])
        invalid = PREPARATION.EvidenceRecord(**fixture["invalid_record"])
        self.assertEqual(PREPARATION.validate_evidence_record(valid), [])
        self.assertGreaterEqual(len(PREPARATION.validate_evidence_record(invalid)), 8)


class AmendmentAndShapeTests(unittest.TestCase):
    def proposal(self, **overrides):
        values = {
            "proposed_classification": "bounded-implementation-amendment",
            "changed_dimensions": ("helper-path",),
            "evidence": ("repository inspection",),
            "obligations_preserved": True,
            "user_owned_decision": False,
            "reversible_or_recoverable": True,
            "authoritative_contradiction": False,
        }
        values.update(overrides)
        return PREPARATION.AmendmentProposal(**values)

    def test_every_program_dimension_forces_program_amendment(self) -> None:
        for dimension in PREPARATION.PROGRAM_AMENDMENT_DIMENSIONS:
            assessment = PREPARATION.classify_plan_amendment(self.proposal(changed_dimensions=(dimension,)))
            self.assertEqual(assessment.classification, "program-amendment")
            self.assertTrue(assessment.requires_program_revision)

    def test_contradiction_and_unsupported_bounded_amendments_stop(self) -> None:
        contradiction = PREPARATION.classify_plan_amendment(self.proposal(authoritative_contradiction=True))
        self.assertEqual(contradiction.classification, "authoritative-contradiction")
        for overrides in ({"evidence": ()}, {"obligations_preserved": False}, {"user_owned_decision": True}, {"reversible_or_recoverable": False}):
            self.assertFalse(PREPARATION.classify_plan_amendment(self.proposal(**overrides)).may_proceed_under_current_mode)

    def test_minor_correction_is_limited_to_non_program_dimensions(self) -> None:
        assessment = PREPARATION.classify_plan_amendment(
            self.proposal(proposed_classification="minor-correction", changed_dimensions=("test-convention",))
        )
        self.assertEqual(assessment.classification, "minor-correction")
        self.assertTrue(assessment.may_proceed_under_current_mode)

    def test_increment_shape_requires_coherence_verification_recovery_and_valid_result(self) -> None:
        valid = PREPARATION.IncrementShape(
            outcomes=("refresh archive catalog",),
            requirement_ids=("archive-catalog-current",),
            acceptance_criteria=("catalog validation passes",),
            verification_contracts=("focused unit test",),
            rollback_or_recovery=("restore catalog bytes",),
            risk_domains=("local-file-integrity",),
            depends_on_unimplemented_safeguards=(),
            leaves_repository_valid=True,
        )
        self.assertEqual(PREPARATION.assess_increment_shape(valid), [])
        invalid = replace(
            valid,
            outcomes=("refresh catalog", "redesign uploader"),
            verification_contracts=(),
            rollback_or_recovery=(),
            risk_domains=("local-file-integrity", "provider-authentication"),
            depends_on_unimplemented_safeguards=("future-locking",),
            leaves_repository_valid=False,
        )
        self.assertGreaterEqual(len(PREPARATION.assess_increment_shape(invalid)), 5)


class SemanticNamingTests(unittest.TestCase):
    def record(self, **overrides):
        values = {
            "surface": "archive/catalog_reader.py",
            "surface_kind": "path",
            "origin": "new",
            "context": "archive catalog access",
            "intention": "read catalog entries",
            "planning_term_basis": "none",
            "basis_owner": "none",
            "compatibility_class": "private",
            "compatibility_disposition": "add",
        }
        values.update(overrides)
        return PREPARATION.SemanticNameRecord(**values)

    def test_every_surface_kind_accepts_contextual_ordinary_names(self) -> None:
        records = [self.record(surface=f"archive-{kind}", surface_kind=kind) for kind in PREPARATION.SURFACE_KINDS]
        self.assertEqual(PREPARATION.validate_semantic_naming_inventory(records), [])

    def test_roadmap_coordinate_needs_governance_or_durable_domain_basis(self) -> None:
        invalid = self.record(surface="phase-7-loader", surface_kind="symbol")
        self.assertTrue(any("planning coordinate" in issue for issue in PREPARATION.validate_semantic_naming_inventory([invalid])))
        governance = replace(invalid, planning_term_basis="implementation-governance", basis_owner="approved execution plan")
        domain = replace(invalid, planning_term_basis="durable-domain", basis_owner="archival phase classification")
        self.assertEqual(PREPARATION.validate_semantic_naming_inventory([governance]), [])
        self.assertEqual(PREPARATION.validate_semantic_naming_inventory([domain]), [])

    def test_missing_context_duplicate_surface_and_compatibility_are_rejected(self) -> None:
        missing = self.record(context="", intention="")
        public = self.record(origin="existing", compatibility_class="public", compatibility_disposition="preserve")
        issues = PREPARATION.validate_semantic_naming_inventory([missing, public, public])
        self.assertTrue(any("context" in issue for issue in issues))
        self.assertTrue(any("duplicated" in issue for issue in issues))
        self.assertTrue(any("compatibility" in issue for issue in issues))


class ExactPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = GitFixture()
        self.inspection = PREPARATION.inspect_repository(self.fixture.root, self.fixture.base)
        self.plan_path = self.fixture.root / "exact-file-plan.md"
        template = (FIXTURE_ROOT / "exact-file-plan.md").read_text(encoding="utf-8")
        self.binding = PREPARATION.PlanBinding(
            program_id="portable-archive",
            program_revision=3,
            increment_id="catalog-refresh",
            source_sha256="1" * 64,
            program_sha256="2" * 64,
            semantic_requirements_sha256="3" * 64,
            workspace_path=str(self.fixture.root.resolve()),
            workspace_branch="archive-maintenance",
            workspace_base_commit=self.fixture.base,
            workspace_head_commit=self.inspection.observation.head_commit,
            preparation_sha256="4" * 64,
        )
        replacements = {
            "SOURCE_DIGEST": self.binding.source_sha256,
            "PROGRAM_DIGEST": self.binding.program_sha256,
            "SEMANTIC_DIGEST": self.binding.semantic_requirements_sha256,
            "WORKSPACE_PATH": self.binding.workspace_path,
            "BASE_COMMIT": self.binding.workspace_base_commit,
            "HEAD_COMMIT": self.binding.workspace_head_commit,
            "PREPARATION_DIGEST": self.binding.preparation_sha256,
        }
        for old, new in replacements.items():
            template = template.replace(old, new)
        self.plan_path.write_text(template, encoding="utf-8")

    def write_bound_program_state(self) -> tuple[Path, Path, dict[str, object]]:
        preparation_path = self.fixture.root / "preparation.md"
        preparation_path.write_text("# Current preparation\n", encoding="utf-8")
        status_directory = self.fixture.root / "state"
        status_directory.mkdir()
        manifest = {
            "program_id": self.binding.program_id,
            "program_revision": self.binding.program_revision,
            "source_binding": {"source_id": "portable-source", "sha256": self.binding.source_sha256},
            "program_binding": {"sha256": self.binding.program_sha256},
            "current_increment": {"increment_id": self.binding.increment_id},
            "workspace_binding": {
                "path": self.binding.workspace_path,
                "branch": self.binding.workspace_branch,
                "base_commit": self.binding.workspace_base_commit,
                "head_at_preparation": self.binding.workspace_head_commit,
            },
            "logical_roles": {
                "status": "state/status.json",
                "action_authorizations": "state/action-authorizations.jsonl",
                "current_exact_file_plan": "exact-file-plan.md",
                "current_preparation": "preparation.md",
            },
        }
        status = {
            "approved_exact_file_plan_sha256": sha256_file(self.plan_path),
            "pending_exact_file_plan_sha256": None,
            "transition_authorization": {"action_authorization_id": "archive-write-authorization"},
            "program_id": self.binding.program_id,
            "program_revision": self.binding.program_revision,
            "source_binding": manifest["source_binding"],
            "program_binding": {
                "sha256": self.binding.program_sha256,
                "semantic_requirements_sha256": self.binding.semantic_requirements_sha256,
            },
            "current_increment_id": self.binding.increment_id,
            "approval_mode": "approval:standard",
            "brief_binding": {"sha256": "5" * 64},
            "preparation_binding": {
                "path": "preparation.md",
                "sha256": sha256_file(preparation_path),
                "head_commit": self.binding.workspace_head_commit,
            },
        }
        authorization = {
            "schema_version": "implementation-action-authorization/v1",
            "authorization_id": "archive-write-authorization",
            "decision": "authorized",
            "program_id": self.binding.program_id,
            "program_revision": self.binding.program_revision,
            "source_id": "portable-source",
            "source_sha256": self.binding.source_sha256,
            "program_sha256": self.binding.program_sha256,
            "semantic_requirements_sha256": self.binding.semantic_requirements_sha256,
            "increment_id": self.binding.increment_id,
            "brief_sha256": "5" * 64,
            "exact_file_plan_sha256": sha256_file(self.plan_path),
            "approval_mode": "approval:standard",
            "workspace": {
                "path": self.binding.workspace_path,
                "branch": self.binding.workspace_branch,
                "base_commit": self.binding.workspace_base_commit,
                "head_commit": self.binding.workspace_head_commit,
            },
            "actions": ["modify-workspace"],
            "scope": ["modify only the bound archive catalog files"],
        }
        (self.fixture.root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (status_directory / "status.json").write_text(json.dumps(status), encoding="utf-8")
        (status_directory / "action-authorizations.jsonl").write_text(json.dumps(authorization) + "\n", encoding="utf-8")
        return preparation_path, status_directory / "action-authorizations.jsonl", authorization

    def tearDown(self) -> None:
        self.fixture.close()

    def test_complete_current_plan_passes(self) -> None:
        self.assertEqual(PREPARATION.validate_exact_file_plan(self.plan_path, self.binding, self.inspection), [])

    def test_missing_symlinked_stale_mismatched_and_incomplete_plans_fail(self) -> None:
        missing = self.fixture.root / "missing.md"
        self.assertTrue(PREPARATION.validate_exact_file_plan(missing, self.binding, self.inspection))
        link = self.fixture.root / "linked.md"
        link.symlink_to(self.plan_path)
        self.assertTrue(any("symlink" in issue for issue in PREPARATION.validate_exact_file_plan(link, self.binding, self.inspection)))
        moved = replace(self.inspection, observation=replace(self.inspection.observation, head_commit="f" * 40))
        self.assertTrue(any("head" in issue for issue in PREPARATION.validate_exact_file_plan(self.plan_path, self.binding, moved)))
        wrong = replace(self.binding, source_sha256="9" * 64)
        self.assertTrue(any("source" in issue for issue in PREPARATION.validate_exact_file_plan(self.plan_path, wrong, self.inspection)))
        self.plan_path.write_text("# Incomplete\n", encoding="utf-8")
        self.assertGreaterEqual(len(PREPARATION.validate_exact_file_plan(self.plan_path, self.binding, self.inspection)), len(PREPARATION.REQUIRED_PLAN_SECTIONS))

    def test_plan_write_authorization_must_match_the_complete_current_tuple(self) -> None:
        _, authorization_path, authorization = self.write_bound_program_state()
        self.assertEqual(PREPARATION._validate_bound_plan_digest(self.fixture.root, self.plan_path), [])
        authorization["program_id"] = "different-program"
        authorization_path.write_text(json.dumps(authorization) + "\n", encoding="utf-8")
        issues = PREPARATION._validate_bound_plan_digest(self.fixture.root, self.plan_path)
        self.assertTrue(any("no exact current write authorization" in issue for issue in issues))

    def test_preparation_must_be_manifest_owned_and_status_bound(self) -> None:
        preparation_path, _, _ = self.write_bound_program_state()
        self.assertEqual(
            PREPARATION._validate_preparation_artifact(self.fixture.root, preparation_path, self.inspection),
            [],
        )
        other = self.fixture.root / "other-preparation.md"
        other.write_text(preparation_path.read_text(encoding="utf-8"), encoding="utf-8")
        issues = PREPARATION._validate_preparation_artifact(self.fixture.root, other, self.inspection)
        self.assertTrue(any("manifest-owned" in issue for issue in issues))
        preparation_path.write_text("changed\n", encoding="utf-8")
        issues = PREPARATION._validate_preparation_artifact(self.fixture.root, preparation_path, self.inspection)
        self.assertTrue(any("digest" in issue for issue in issues))


class CliContractTests(unittest.TestCase):
    def test_usage_errors_return_two_without_traceback(self) -> None:
        with mock.patch.object(sys, "stdout") as output:
            self.assertEqual(PREPARATION.main([]), 2)
        rendered = "".join(str(call) for call in output.write.call_args_list)
        self.assertNotIn("Traceback", rendered)

    def test_inspect_repository_emits_deterministic_json(self) -> None:
        fixture = GitFixture()
        try:
            with mock.patch.object(sys, "argv", ["repository_preparation.py"]):
                with mock.patch("builtins.print") as printer:
                    exit_code = PREPARATION.main(["inspect-repository", "--workspace", str(fixture.root), "--base", fixture.base])
            self.assertEqual(exit_code, 0)
            payload = json.loads(printer.call_args.args[0])
            self.assertEqual(payload["schema_version"], PREPARATION.REPOSITORY_INSPECTION_SCHEMA)
            self.assertNotIn("environment", payload)
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
