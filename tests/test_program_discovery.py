import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tests.test_program_authority import ProgramAuthorityFixture


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills" / "implementing-staged-plans" / "scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_discovery.py"
SPEC = importlib.util.spec_from_file_location("program_discovery", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load program discovery from {SCRIPT_PATH}")
DISCOVERY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DISCOVERY
sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC.loader.exec_module(DISCOVERY)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


BASE_COMMIT = "b" * 40
HEAD_COMMIT = "a" * 40


def sha256_file(path: Path) -> str:
    return DISCOVERY.sha256_file(path)


class DiscoveryFixture:
    def __init__(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary_directory.name) / "repository"
        self.repository.mkdir()
        self.observation = DISCOVERY.RepositoryObservation(
            repository=str(self.repository),
            path=str(self.repository),
            branch="archive-maintenance",
            base_commit=BASE_COMMIT,
            head_commit=HEAD_COMMIT,
            staged_paths=(),
            modified_paths=(),
            untracked_paths=(),
            conflicted_paths=(),
            active_git_operation=None,
        )

    def close(self) -> None:
        self.temporary_directory.cleanup()

    def add_program(
        self,
        name: str,
        state: str,
        *,
        parent: str = "implementation-programs",
    ) -> Path:
        authority_fixture = ProgramAuthorityFixture()
        program_root = self.repository / parent / name
        try:
            shutil.copytree(authority_fixture.root, program_root)
        finally:
            authority_fixture.close()

        brief_path = program_root / "increments/archive-index/brief.md"
        plan_path = program_root / "increments/archive-index/exact-file-plan.md"
        brief_path.parent.mkdir(parents=True)
        brief_path.write_text("# Archive index brief\n", encoding="utf-8")
        plan_path.write_text("# Archive index exact-file plan\n", encoding="utf-8")

        workspace_path = program_root / "state/workspace.json"
        workspace = {
            "schema_version": "implementation-workspace/v1",
            "program_id": "ARCHIVE-PROGRAM",
            "program_revision": 1,
            "selected_at": "2026-08-09T00:00:00Z",
            "repository": {"identity": str(self.repository)},
            "implementation_workspace": {
                "path": str(self.repository),
                "branch": "archive-maintenance",
                "base_commit": BASE_COMMIT,
                "head_commit_at_selection": HEAD_COMMIT,
            },
            "pre_existing_work_at_selection": {
                "staged_paths": [],
                "modified_paths": [],
                "untracked_paths": [],
                "conflicted_paths": [],
                "active_git_operation": None,
            },
            "selection_approval_event_id": "ARCHIVE-WORKSPACE-APPROVAL",
            "action_authorization_id": "ARCHIVE-WORKSPACE-AUTHORIZATION",
        }
        workspace_path.write_text(
            json.dumps(workspace, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        manifest_path = program_root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        traceability = json.loads(
            (program_root / "program/traceability.json").read_text(encoding="utf-8")
        )
        plan_sha256 = sha256_file(plan_path)
        increment_state = {
            "active": "awaiting-plan-approval",
            "blocked": "blocked",
            "closed": "accepted",
        }[state]
        status = {
            "schema_version": "implementation-program-status/v1",
            "state_sequence": 4,
            "program_id": manifest["program_id"],
            "program_revision": manifest["program_revision"],
            "program_state": state,
            "current_increment_id": "archive-index",
            "current_increment_state": increment_state,
            "approved_exact_file_plan_sha256": None,
            "pending_exact_file_plan_sha256": plan_sha256,
            "approval_mode": manifest["approval_mode"],
            "source_binding": manifest["source_binding"],
            "program_binding": {
                "sha256": manifest["program_binding"]["sha256"],
                "semantic_requirements_sha256": traceability["coverage_assertion"][
                    "semantic_requirements_sha256"
                ],
            },
            "brief_binding": {
                "path": "increments/archive-index/brief.md",
                "sha256": sha256_file(brief_path),
                "workspace_sha256": sha256_file(workspace_path),
                "head_commit": HEAD_COMMIT,
            },
        }
        status_path = program_root / "state/status.json"
        status_path.write_text(
            json.dumps(status, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        manifest["program_status"] = state
        manifest["logical_roles"].update(
            status="state/status.json",
            workspace="state/workspace.json",
            current_increment_brief="increments/archive-index/brief.md",
            current_exact_file_plan="increments/archive-index/exact-file-plan.md",
        )
        manifest["current_increment"] = {
            "increment_id": "archive-index",
            "state": increment_state,
            "exact_file_plan_sha256": plan_sha256,
        }
        manifest["workspace_binding"] = {
            "path": str(self.repository),
            "branch": "archive-maintenance",
            "base_commit": BASE_COMMIT,
            "head_at_preparation": HEAD_COMMIT,
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest_path


class ProgramDiscoveryTests(unittest.TestCase):
    def test_no_manifest_is_a_possible_bootstrap_requiring_source_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            folder_without_manifest = repository / "implementation-programs" / "archive"
            folder_without_manifest.mkdir(parents=True)
            before = tuple(sorted(path.relative_to(repository) for path in repository.rglob("*")))

            result = DISCOVERY.discover_programs(repository)

            self.assertEqual(result.disposition, "new-program-bootstrap-possible")
            self.assertEqual(result.required_input, "authoritative-source-plan-path")
            self.assertEqual(result.candidates, ())
            self.assertIsNone(result.resume_expectations)
            self.assertTrue(result.stop_required)
            self.assertEqual(
                before,
                tuple(sorted(path.relative_to(repository) for path in repository.rglob("*"))),
            )

    def test_no_manifest_with_valid_source_plan_is_bootstrap_ready_but_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            repository.mkdir()
            source_plan = Path(directory) / "authoritative-plan.md"
            source_plan.write_text("# Authoritative plan\n", encoding="utf-8")
            before = source_plan.read_bytes()

            result = DISCOVERY.discover_programs(
                repository,
                authoritative_source_plan_path=source_plan,
            )

            self.assertEqual(result.disposition, "new-program-bootstrap-ready")
            self.assertIsNone(result.required_input)
            self.assertEqual(result.source_plan_path, str(source_plan))
            self.assertFalse(result.stop_required)
            self.assertEqual(source_plan.read_bytes(), before)
            self.assertFalse((repository / "implementation-programs").exists())

            linked_source = Path(directory) / "linked-plan.md"
            linked_source.symlink_to(source_plan)
            invalid = DISCOVERY.discover_programs(
                repository,
                authoritative_source_plan_path=linked_source,
            )
            self.assertEqual(invalid.disposition, "invalid")
            self.assertIn("symlink", " ".join(invalid.issues).lower())

    def test_one_active_program_resumes_from_manifest_and_fresh_observation(self) -> None:
        fixture = DiscoveryFixture()
        try:
            manifest_path = fixture.add_program("archive", "active")
            observer = mock.Mock(return_value=fixture.observation)

            result = DISCOVERY.discover_programs(
                fixture.repository,
                observation_provider=observer,
            )

            self.assertEqual(result.disposition, "resume")
            self.assertIsNone(result.required_input)
            self.assertFalse(result.stop_required)
            self.assertEqual(
                tuple(candidate.manifest_path for candidate in result.candidates),
                ("implementation-programs/archive/manifest.json",),
            )
            expectations = result.resume_expectations
            self.assertIsNotNone(expectations)
            self.assertEqual(expectations.manifest_path, result.candidates[0].manifest_path)
            self.assertEqual(expectations.program_state, "active")
            self.assertEqual(expectations.workspace_head_commit, HEAD_COMMIT)
            self.assertEqual(expectations.status_sha256, sha256_file(manifest_path.parent / "state/status.json"))
            observer.assert_called_once_with(fixture.repository, BASE_COMMIT)

            stale = replace(expectations, status_sha256="0" * 64)
            self.assertIn(
                "status_sha256 mismatch",
                " ".join(DISCOVERY.validate_resume_evidence(stale, expectations)),
            )
        finally:
            fixture.close()

    def test_multiple_active_programs_return_sorted_candidates_and_stop(self) -> None:
        fixture = DiscoveryFixture()
        try:
            fixture.add_program("zeta", "blocked")
            fixture.add_program("alpha", "active")

            result = DISCOVERY.discover_programs(
                fixture.repository,
                observation_provider=lambda _path, _base: fixture.observation,
            )

            self.assertEqual(result.disposition, "selection-required")
            self.assertTrue(result.stop_required)
            self.assertIsNone(result.resume_expectations)
            self.assertEqual(
                tuple(candidate.manifest_path for candidate in result.candidates),
                (
                    "implementation-programs/alpha/manifest.json",
                    "implementation-programs/zeta/manifest.json",
                ),
            )
        finally:
            fixture.close()

    def test_only_closed_programs_are_reported_and_require_explicit_intent(self) -> None:
        fixture = DiscoveryFixture()
        try:
            fixture.add_program("archive", "closed")
            fixture.add_program("catalog", "closed")

            result = DISCOVERY.discover_programs(fixture.repository)

            self.assertEqual(result.disposition, "closed-programs")
            self.assertEqual(
                result.required_input,
                "new-program-or-closed-program-inspection-intent",
            )
            self.assertEqual(result.candidates, ())
            self.assertEqual(
                tuple(candidate.manifest_path for candidate in result.closed_programs),
                (
                    "implementation-programs/archive/manifest.json",
                    "implementation-programs/catalog/manifest.json",
                ),
            )
            self.assertTrue(result.stop_required)
        finally:
            fixture.close()

    def test_closed_program_still_requires_valid_persisted_bindings(self) -> None:
        for case in ("source-drift", "symlinked-workspace", "workspace-binding-drift"):
            with self.subTest(case=case):
                fixture = DiscoveryFixture()
                try:
                    manifest_path = fixture.add_program("archive", "closed")
                    if case == "source-drift":
                        status_path = manifest_path.parent / "state/status.json"
                        status = json.loads(status_path.read_text(encoding="utf-8"))
                        status["source_binding"]["sha256"] = "0" * 64
                        status_path.write_text(
                            json.dumps(status, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )
                    else:
                        workspace_path = manifest_path.parent / "state/workspace.json"
                        if case == "symlinked-workspace":
                            target = workspace_path.with_name("workspace-target.json")
                            workspace_path.rename(target)
                            workspace_path.symlink_to(target)
                        else:
                            manifest = json.loads(
                                manifest_path.read_text(encoding="utf-8")
                            )
                            manifest["workspace_binding"]["branch"] = "other-branch"
                            manifest_path.write_text(
                                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8",
                            )

                    result = DISCOVERY.discover_programs(fixture.repository)

                    self.assertEqual(result.disposition, "invalid")
                    self.assertTrue(result.issues)
                finally:
                    fixture.close()

    def test_closed_program_allows_selection_head_to_predate_preparation(self) -> None:
        fixture = DiscoveryFixture()
        try:
            manifest_path = fixture.add_program("archive", "closed")
            workspace_path = manifest_path.parent / "state/workspace.json"
            workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
            workspace["implementation_workspace"]["head_commit_at_selection"] = "c" * 40
            workspace_path.write_text(
                json.dumps(workspace, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            status_path = manifest_path.parent / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["brief_binding"]["workspace_sha256"] = sha256_file(workspace_path)
            status_path.write_text(
                json.dumps(status, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = DISCOVERY.discover_programs(fixture.repository)

            self.assertEqual(result.disposition, "closed-programs")
        finally:
            fixture.close()

    def test_invalid_manifest_and_escaping_status_role_fail_closed(self) -> None:
        for case in ("invalid-json", "escaping-status"):
            with self.subTest(case=case):
                fixture = DiscoveryFixture()
                try:
                    manifest_path = fixture.add_program("archive", "active")
                    if case == "invalid-json":
                        manifest_path.write_text("{", encoding="utf-8")
                    else:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        manifest["logical_roles"]["status"] = "../outside-status.json"
                        manifest_path.write_text(
                            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )

                    result = DISCOVERY.discover_programs(
                        fixture.repository,
                        observation_provider=lambda _path, _base: fixture.observation,
                    )

                    self.assertEqual(result.disposition, "invalid")
                    self.assertTrue(result.issues)
                    self.assertTrue(result.stop_required)
                    self.assertIsNone(result.resume_expectations)
                finally:
                    fixture.close()

    def test_symlinked_manifest_or_conventional_root_fails_closed(self) -> None:
        fixture = DiscoveryFixture()
        try:
            manifest_path = fixture.add_program("archive", "active")
            real_manifest = manifest_path.with_name("manifest-target.json")
            manifest_path.rename(real_manifest)
            manifest_path.symlink_to(real_manifest)

            result = DISCOVERY.discover_programs(fixture.repository)

            self.assertEqual(result.disposition, "invalid")
            self.assertIn("symlink", " ".join(result.issues).lower())
        finally:
            fixture.close()

        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            outside = Path(directory) / "outside-programs"
            repository.mkdir()
            outside.mkdir()
            (repository / "implementation-programs").symlink_to(
                outside,
                target_is_directory=True,
            )

            result = DISCOVERY.discover_programs(repository)

            self.assertEqual(result.disposition, "invalid")
            self.assertIn("symlink", " ".join(result.issues).lower())

    def test_explicit_manifest_precedes_other_locations_after_validation(self) -> None:
        fixture = DiscoveryFixture()
        try:
            selected = fixture.add_program(
                "selected",
                "blocked",
                parent="declared-programs",
            )
            invalid = fixture.repository / "implementation-programs/invalid/manifest.json"
            invalid.parent.mkdir(parents=True)
            invalid.write_text("{", encoding="utf-8")

            result = DISCOVERY.discover_programs(
                fixture.repository,
                explicit_manifest_path=selected,
                observation_provider=lambda _path, _base: fixture.observation,
            )

            self.assertEqual(result.disposition, "resume")
            self.assertEqual(result.candidates[0].program_state, "blocked")
            self.assertEqual(
                result.candidates[0].manifest_path,
                "declared-programs/selected/manifest.json",
            )
            self.assertEqual(result.issues, ())
        finally:
            fixture.close()

    def test_instruction_declared_manifest_is_discovered_without_broad_search(self) -> None:
        fixture = DiscoveryFixture()
        try:
            declared = fixture.add_program(
                "archive",
                "active",
                parent="governance/programs",
            )
            unrelated = fixture.repository / "other/deep/program/manifest.json"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("{", encoding="utf-8")

            result = DISCOVERY.discover_programs(
                fixture.repository,
                instruction_manifest_paths=(declared.relative_to(fixture.repository),),
                observation_provider=lambda _path, _base: fixture.observation,
            )

            self.assertEqual(result.disposition, "resume")
            self.assertEqual(
                result.candidates[0].manifest_path,
                "governance/programs/archive/manifest.json",
            )
        finally:
            fixture.close()

    def test_explicit_or_declared_manifest_escape_fails_closed(self) -> None:
        fixture = DiscoveryFixture()
        try:
            outside = fixture.add_program(
                "outside",
                "active",
                parent="../outside-programs",
            )
            for arguments in (
                {"explicit_manifest_path": outside},
                {"instruction_manifest_paths": (outside,)},
            ):
                with self.subTest(arguments=arguments):
                    result = DISCOVERY.discover_programs(
                        fixture.repository,
                        observation_provider=lambda _path, _base: fixture.observation,
                        **arguments,
                    )
                    self.assertEqual(result.disposition, "invalid")
                    self.assertIn("escapes", " ".join(result.issues))
        finally:
            fixture.close()

    def test_cli_returns_deterministic_json_and_never_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            repository.mkdir()
            marker = repository / "notes.txt"
            marker.write_text("preserve\n", encoding="utf-8")
            before = marker.read_bytes()

            completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "discover", str(repository)],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["disposition"], "new-program-bootstrap-possible")
            self.assertEqual(marker.read_bytes(), before)
            self.assertFalse((repository / "implementation-programs").exists())

            usage = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "discover"],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(usage.returncode, 2)


if __name__ == "__main__":
    unittest.main()
