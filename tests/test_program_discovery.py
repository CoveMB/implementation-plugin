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
from tests.program_bootstrap_support import (
    BootstrapFixture,
    canonical_json,
    repository_snapshot,
)
from tests.script_module_support import load_script_module
from tests.test_program_setup import ACTIVATION, BOOTSTRAP, SETUP


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills" / "implementing-staged-plans" / "scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_discovery.py"
DISCOVERY = load_script_module("program_discovery", SCRIPT_PATH)


BASE_COMMIT = "b" * 40
HEAD_COMMIT = "a" * 40


class SetupV3DiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BootstrapFixture()
        self.fixture.configure_setup_v3()
        BOOTSTRAP.publish_program_proposal(
            self.fixture.repository,
            self.fixture.source_plan,
            self.fixture.candidate,
            self.fixture.source_sha256,
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def observation(self):
        return ACTIVATION.inspect_repository(
            self.fixture.repository, self.fixture.head
        ).observation

    def decision(self):
        return SETUP.adapt_setup_decision(
            self.fixture.program_root,
            "Yes",
            role="user",
            provenance="direct-user-message",
        )

    def test_sequence_zero_routes_to_readable_setup(self) -> None:
        result = DISCOVERY.discover_programs(self.fixture.repository)

        self.assertEqual(result.disposition, "program-setup-ready")
        self.assertEqual(result.required_input, "program-setup-approval")
        self.assertFalse(result.stop_required)

    def test_sequence_one_routes_to_fresh_task_first_start(self) -> None:
        ACTIVATION.activate_program(
            self.fixture.program_root, self.decision(), self.observation()
        )

        result = DISCOVERY.discover_programs(self.fixture.repository)

        self.assertEqual(result.disposition, "first-increment-start-ready")
        self.assertEqual(result.required_input, "first-increment-start-intent")
        self.assertFalse(result.stop_required)

    def test_malformed_setup_revision_and_sequence_return_invalid_discovery(
        self,
    ) -> None:
        cases = (
            ("program-revision", "manifest program_revision is invalid"),
            ("state-sequence", "status state_sequence is invalid"),
        )
        for case, expected_issue in cases:
            with self.subTest(case=case):
                fixture = BootstrapFixture()
                try:
                    fixture.configure_setup_v3()
                    program_root = (
                        fixture.repository
                        / "implementation-programs/ARCHIVE-PROGRAM"
                    )
                    program_root.parent.mkdir()
                    shutil.copytree(fixture.candidate, program_root)
                    manifest_path = program_root / "manifest.json"
                    status_path = program_root / "state/status.json"
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    if case == "program-revision":
                        manifest["program_revision"] = "one"
                        status["program_revision"] = "one"
                        manifest_path.write_bytes(canonical_json(manifest))
                    else:
                        status["state_sequence"] = None
                    status_path.write_bytes(canonical_json(status))

                    result = DISCOVERY.discover_programs(fixture.repository)

                    self.assertEqual(result.disposition, "invalid")
                    self.assertTrue(
                        any(expected_issue in issue for issue in result.issues),
                        result.issues,
                    )
                finally:
                    fixture.close()


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

    def add_new_program(
        self,
        name: str,
        *,
        program_state: str = "awaiting-program-approval",
        increment_state: str = "not-started",
    ) -> Path:
        bootstrap = BootstrapFixture()
        program_root = self.repository / "implementation-programs" / name
        try:
            shutil.copytree(bootstrap.candidate, program_root)
        finally:
            bootstrap.close()
        manifest_path = program_root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        workspace_path = program_root / manifest["logical_roles"]["workspace"]
        workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
        workspace["repository"] = {"identity": str(self.repository)}
        workspace["implementation_workspace"] = {
            "path": str(self.repository),
            "branch": "archive-maintenance",
            "base_commit": BASE_COMMIT,
            "head_commit_at_selection": HEAD_COMMIT,
        }
        workspace_path.write_bytes(canonical_json(workspace))
        status_path = program_root / manifest["logical_roles"]["status"]
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status.update(
            state_sequence=0 if program_state == "awaiting-program-approval" else 1,
            program_state=program_state,
            current_increment_state=increment_state,
        )
        status_path.write_bytes(canonical_json(status))
        if program_state != "awaiting-program-approval":
            traceability = json.loads(
                (program_root / manifest["logical_roles"]["traceability"]).read_text(
                    encoding="utf-8"
                )
            )
            approval = {
                "event_id": "ARCHIVE-APPROVAL",
                "type": "program-approval",
                "decision": "approved",
                "program_id": manifest["program_id"],
                "program_revision": manifest["program_revision"],
                "source_id": manifest["source_binding"]["source_id"],
                "source_sha256": manifest["source_binding"]["sha256"],
                "program_sha256": manifest["program_binding"]["sha256"],
                "semantic_requirements_sha256": traceability["coverage_assertion"][
                    "semantic_requirements_sha256"
                ],
                "approval_mode": manifest["approval_mode"],
            }
            (program_root / manifest["logical_roles"]["approvals"]).write_text(
                json.dumps(approval, sort_keys=True) + "\n", encoding="utf-8"
            )
        return manifest_path

    def program_approval_record(self, manifest_path: Path) -> dict[str, object]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        traceability = json.loads(
            (manifest_path.parent / manifest["logical_roles"]["traceability"]).read_text(
                encoding="utf-8"
            )
        )
        return {
            "event_id": "ARCHIVE-APPROVAL",
            "type": "program-approval",
            "decision": "approved",
            "program_id": manifest["program_id"],
            "program_revision": manifest["program_revision"],
            "source_id": manifest["source_binding"]["source_id"],
            "source_sha256": manifest["source_binding"]["sha256"],
            "program_sha256": manifest["program_binding"]["sha256"],
            "semantic_requirements_sha256": traceability["coverage_assertion"][
                "semantic_requirements_sha256"
            ],
            "approval_mode": manifest["approval_mode"],
        }

    def append_record(
        self, manifest_path: Path, logical_role: str, record: dict[str, object]
    ) -> None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        path = manifest_path.parent / manifest["logical_roles"][logical_role]
        with path.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
            )

    def activation_transaction(
        self, manifest_path: Path
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        prompt = DISCOVERY.render_program_launch_prompt(manifest_path.parent)
        command = DISCOVERY.validate_submitted_program_launch_prompt(
            manifest_path.parent, prompt
        )
        workspace = command["workspace"]
        repository = workspace["repository"]
        selected = workspace["implementation_workspace"]
        existing = workspace["pre_existing_work_at_selection"]
        observation = DISCOVERY.RepositoryObservation(
            repository=repository["identity"],
            path=selected["path"],
            branch=selected["branch"],
            base_commit=selected["base_commit"],
            head_commit=selected["head_commit_at_selection"],
            staged_paths=tuple(existing["staged_paths"]),
            modified_paths=tuple(existing["modified_paths"]),
            untracked_paths=tuple(existing["untracked_paths"]),
            conflicted_paths=tuple(existing["conflicted_paths"]),
            active_git_operation=existing["active_git_operation"],
        )
        program, workspace_record, grant, _status = (
            DISCOVERY.build_activation_transaction(command, prompt, observation)
        )
        return program, workspace_record, grant


class ProgramDiscoveryTests(unittest.TestCase):
    def test_publication_recovery_rejects_non_object_freshness(self) -> None:
        for label, freshness in (("missing", ...), ("null", None), ("list", [])):
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as directory:
                    repository = Path(directory) / "repository"
                    repository.mkdir()
                    owner_token = "0" * 16
                    staging = repository / (
                        f".implementation-program-ARCHIVE-PROGRAM-{owner_token}"
                    )
                    staging.mkdir()
                    manifest_path = staging / "manifest.json"
                    manifest_path.write_bytes(canonical_json({}))
                    owner = {
                        "schema_version": "implementation-proposal-publication-owner/v2",
                        "owner_token": owner_token,
                        "program_id": "ARCHIVE-PROGRAM",
                        "request_schema_version": (
                            "implementation-program-proposal-request/v2"
                        ),
                        "target": "implementation-programs/ARCHIVE-PROGRAM",
                        "inventory": [
                            {
                                "path": "manifest.json",
                                "sha256": sha256_file(manifest_path),
                            }
                        ],
                    }
                    if freshness is not ...:
                        owner["publication_freshness"] = freshness
                    (staging / ".publication-owner.json").write_bytes(
                        canonical_json(owner)
                    )

                    disposition, issues = DISCOVERY._single_bootstrap_prefix_disposition(
                        repository, staging
                    )

                    self.assertEqual(
                        disposition, "proposal-publication-recovery-required"
                    )
                    self.assertEqual(
                        issues,
                        ("proposal-publication freshness binding is invalid",),
                    )

    def test_publication_recovery_uses_manifest_roles_after_activation_started(self) -> None:
        fixture = BootstrapFixture()
        try:
            manifest_path = fixture.candidate / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            custom_status = "records/custom-status.json"
            custom_approvals = "records/custom-approvals.jsonl"
            for role, custom_path in (
                ("status", custom_status),
                ("approvals", custom_approvals),
            ):
                original = fixture.candidate / manifest["logical_roles"][role]
                replacement = fixture.candidate / custom_path
                replacement.parent.mkdir(parents=True, exist_ok=True)
                original.rename(replacement)
                manifest["logical_roles"][role] = custom_path
            manifest_path.write_bytes(canonical_json(manifest))

            inventory = [
                {
                    "path": path.relative_to(fixture.candidate).as_posix(),
                    "sha256": sha256_file(path),
                }
                for path in sorted(fixture.candidate.rglob("*"))
                if path.is_file()
            ]
            owner_token = "0" * 16
            owner_bytes = canonical_json(
                {
                    "schema_version": "implementation-proposal-publication-owner/v1",
                    "owner_token": owner_token,
                    "program_id": "ARCHIVE-PROGRAM",
                    "target": "implementation-programs/ARCHIVE-PROGRAM",
                    "inventory": inventory,
                }
            )
            staging = fixture.repository / (
                f".implementation-program-ARCHIVE-PROGRAM-{owner_token}"
            )
            target = fixture.repository / "implementation-programs/ARCHIVE-PROGRAM"
            target.parent.mkdir()
            shutil.copytree(fixture.candidate, staging)
            shutil.copytree(fixture.candidate, target)
            (staging / ".publication-owner.json").write_bytes(owner_bytes)
            (target / ".publication-owner.json").write_bytes(owner_bytes)

            status_path = target / custom_status
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["current_increment_state"] = "preparing"
            status_path.write_bytes(canonical_json(status))

            disposition, issues = DISCOVERY._bootstrap_prefix_disposition(
                fixture.repository
            )

            self.assertIsNone(disposition, issues)
            self.assertEqual(issues, ())
        finally:
            fixture.close()

    def test_publication_recovery_rejects_unsafe_program_id_before_target_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            owner_token = "0" * 16
            staging = repository / f".implementation-program-..-{owner_token}"
            staging.mkdir()
            (staging / ".publication-owner.json").write_bytes(
                canonical_json(
                    {
                        "schema_version": "implementation-proposal-publication-owner/v1",
                        "owner_token": owner_token,
                        "program_id": "..",
                        "target": "implementation-programs/..",
                        "inventory": [
                            {"path": "manifest.json", "sha256": "0" * 64}
                        ],
                    }
                )
            )

            result = DISCOVERY.discover_programs(repository)

            self.assertEqual(
                result.disposition, "proposal-publication-recovery-required"
            )
            self.assertEqual(
                result.issues,
                ("proposal-publication owner receipt is invalid",),
            )

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


class PlanADiscoveryTests(unittest.TestCase):
    def test_live_revision_supersession_and_cancel_intent_are_quarantined(self) -> None:
        fixture = DiscoveryFixture()
        try:
            fixture.add_new_program(
                "archive", program_state="active", increment_state="implementing"
            )
            discovery = DISCOVERY.discover_programs(fixture.repository)
            before = repository_snapshot(fixture.repository)
            expected = {
                "revise": "program-revision-workflow-required",
                "supersede": "program-revision-workflow-required",
                "cancel": "unsupported-program-mutation",
            }
            for operation, disposition in expected.items():
                with self.subTest(operation=operation):
                    result = DISCOVERY.classify_requested_program_operation(
                        discovery, operation
                    )
                    self.assertEqual(result.disposition, disposition)
                    self.assertTrue(result.stop_required)
                    self.assertEqual(repository_snapshot(fixture.repository), before)
        finally:
            fixture.close()

    def test_supported_operation_classification_and_terminal_readers_are_unchanged(self) -> None:
        fixture = DiscoveryFixture()
        try:
            fixture.add_new_program(
                "archive", program_state="superseded", increment_state="superseded"
            )
            discovery = DISCOVERY.discover_programs(fixture.repository)
            for operation in DISCOVERY.SUPPORTED_PROGRAM_OPERATIONS:
                self.assertIs(
                    DISCOVERY.classify_requested_program_operation(
                        discovery, operation
                    ),
                    discovery,
                )
            self.assertEqual(discovery.disposition, "invalid")
        finally:
            fixture.close()

    def test_pristine_proposal_is_activation_ready(self) -> None:
        fixture = DiscoveryFixture()
        try:
            fixture.add_new_program("archive")
            result = DISCOVERY.discover_programs(fixture.repository)
            self.assertEqual(result.disposition, "program-activation-ready")
            self.assertFalse(result.stop_required)
            self.assertEqual(len(result.candidates), 1)
        finally:
            fixture.close()

    def test_exact_activation_prefix_is_retry_ready(self) -> None:
        fixture = DiscoveryFixture()
        try:
            manifest_path = fixture.add_new_program("archive")
            program, _workspace, _grant = fixture.activation_transaction(manifest_path)
            fixture.append_record(manifest_path, "approvals", program)
            result = DISCOVERY.discover_programs(fixture.repository)
            self.assertEqual(result.disposition, "program-activation-retry-ready")
            self.assertFalse(result.stop_required)
        finally:
            fixture.close()

    def test_each_ordered_activation_receipt_prefix_is_retry_ready(self) -> None:
        fixture = DiscoveryFixture()
        try:
            manifest_path = fixture.add_new_program("archive")
            program, workspace, grant = fixture.activation_transaction(manifest_path)
            fixture.append_record(manifest_path, "approvals", program)
            self.assertEqual(
                DISCOVERY.discover_programs(fixture.repository).disposition,
                "program-activation-retry-ready",
            )

            fixture.append_record(
                manifest_path,
                "approvals",
                workspace,
            )
            self.assertEqual(
                DISCOVERY.discover_programs(fixture.repository).disposition,
                "program-activation-retry-ready",
            )

            fixture.append_record(
                manifest_path,
                "increment_grants",
                grant,
            )
            self.assertEqual(
                DISCOVERY.discover_programs(fixture.repository).disposition,
                "program-activation-retry-ready",
            )
        finally:
            fixture.close()

    def test_out_of_order_or_unrelated_activation_prefix_fails_closed(self) -> None:
        cases = (
            (
                "workspace-before-program",
                "approvals",
                {
                    "event_id": "ARCHIVE-WORKSPACE-APPROVAL",
                    "type": "workspace-selection-approval",
                    "decision": "approved",
                },
            ),
            (
                "grant-before-approvals",
                "increment_grants",
                {
                    "schema_version": "implementation-increment-grant/v1",
                    "grant_id": "ARCHIVE-FIRST-INCREMENT-GRANT",
                    "increment_id": "ARCHIVE-INDEX",
                },
            ),
            (
                "action-before-activation",
                "action_authorizations",
                {"authorization_id": "UNRELATED"},
            ),
        )
        for label, role, record in cases:
            with self.subTest(label=label):
                fixture = DiscoveryFixture()
                try:
                    manifest_path = fixture.add_new_program("archive")
                    fixture.append_record(manifest_path, role, record)
                    result = DISCOVERY.discover_programs(fixture.repository)
                    self.assertEqual(
                        result.disposition, "program-activation-recovery-required"
                    )
                    self.assertTrue(result.stop_required)
                finally:
                    fixture.close()

    def test_status_routes_cover_resume_acceptance_closure_and_terminal_history(self) -> None:
        cases = (
            ("active", "authorized", None, "plan-preparation-recovery-required"),
            ("active", "implementing", None, "invalid"),
            ("active", "reviewing", None, "invalid"),
            ("active", "verified", None, "review-preparation-recovery-required"),
            ("active", "awaiting-diff-approval", None, "review-preparation-recovery-required"),
            (
                "active",
                "accepted",
                {"schema_version": "implementation-diff-disposition-binding/v1", "decision": "accept-stop"},
                "increment-acceptance-recovery-required",
            ),
            ("awaiting-closure-approval", "accepted", None, "invalid"),
            ("closed", "accepted", None, "invalid"),
            ("superseded", "superseded", None, "invalid"),
        )
        for program_state, increment_state, disposition_binding, expected in cases:
            with self.subTest(program_state=program_state, increment_state=increment_state):
                fixture = DiscoveryFixture()
                try:
                    manifest_path = fixture.add_new_program(
                        "archive",
                        program_state=program_state,
                        increment_state=increment_state,
                    )
                    if disposition_binding is not None:
                        status_path = manifest_path.parent / "state/status.json"
                        status = json.loads(status_path.read_text(encoding="utf-8"))
                        status["diff_disposition_binding"] = disposition_binding
                        status_path.write_bytes(canonical_json(status))
                    result = DISCOVERY.discover_programs(fixture.repository)
                    self.assertEqual(result.disposition, expected, result.issues)
                finally:
                    fixture.close()

    def test_transaction_file_and_receipt_prefixes_route_to_exact_retries(self) -> None:
        cases = (
            ("preparing", "increment", "exact_file_plan_filename", None, "plan-preparation-recovery-required"),
            (
                "awaiting-plan-approval",
                None,
                None,
                ("approvals", {"event_id": "PLAN-APPROVAL", "type": "plan-approval"}),
                "plan-preparation-recovery-required",
            ),
            ("reviewing", "increment", "review_evidence_filename", None, "review-preparation-recovery-required"),
            (
                "awaiting-diff-approval",
                None,
                None,
                ("approvals", {"event_id": "DIFF-APPROVAL", "type": "increment-diff-approval"}),
                "increment-acceptance-recovery-required",
            ),
            ("accepted", "closure", "reconciliation_filename", None, "increment-acceptance-recovery-required"),
        )
        for increment_state, storage, filename_field, record, expected in cases:
            with self.subTest(increment_state=increment_state, expected=expected):
                fixture = DiscoveryFixture()
                try:
                    manifest_path = fixture.add_new_program(
                        "archive", program_state="active", increment_state=increment_state
                    )
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    if storage == "increment":
                        descriptor = manifest["increment_storage"]
                        path = (
                            manifest_path.parent
                            / descriptor["root"]
                            / "ARCHIVE-INDEX"
                            / descriptor[filename_field]
                        )
                        path.parent.mkdir(parents=True, exist_ok=True)
                        if path.suffix == ".json":
                            path.write_bytes(canonical_json({"schema_version": "prefix/v1"}))
                        else:
                            path.write_text("# Exact plan candidate\n", encoding="utf-8")
                            status_path = manifest_path.parent / manifest["logical_roles"]["status"]
                            status = json.loads(status_path.read_text(encoding="utf-8"))
                            status["pending_exact_file_plan_sha256"] = sha256_file(path)
                            status_path.write_bytes(canonical_json(status))
                    elif storage == "closure":
                        descriptor = manifest["closure_storage"]
                        path = manifest_path.parent / descriptor["root"] / descriptor[filename_field]
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(canonical_json({"schema_version": "prefix/v1"}))
                    if record is not None:
                        fixture.append_record(manifest_path, record[0], record[1])

                    result = DISCOVERY.discover_programs(fixture.repository)

                    self.assertEqual(result.disposition, expected, result.issues)
                    self.assertEqual(
                        result.stop_required,
                        expected.endswith("recovery-required"),
                    )
                finally:
                    fixture.close()

    def test_unbound_closure_approval_prefix_is_invalid(self) -> None:
        fixture = DiscoveryFixture()
        try:
            manifest_path = fixture.add_new_program(
                "archive",
                program_state="awaiting-closure-approval",
                increment_state="accepted",
            )
            fixture.append_record(
                manifest_path,
                "approvals",
                {"event_id": "CLOSURE-APPROVAL", "type": "program-closure-approval"},
            )

            result = DISCOVERY.discover_programs(fixture.repository)

            self.assertEqual(result.disposition, "invalid")
            self.assertTrue(result.stop_required)
        finally:
            fixture.close()

    def test_deferred_successor_and_blocked_prefixes_stop_without_writes(self) -> None:
        cases = (
            ("state/rollovers.jsonl", '{"rollover_id":"R-1"}\n', "continuation-recovery-required"),
            ("state/block-resolutions.jsonl", '{"resolution_id":"B-1"}\n', "blocked-recovery-required"),
        )
        for relative, payload, expected in cases:
            with self.subTest(relative=relative):
                fixture = DiscoveryFixture()
                try:
                    manifest_path = fixture.add_new_program(
                        "archive", program_state="active", increment_state="accepted"
                    )
                    path = manifest_path.parent / relative
                    path.write_text(payload, encoding="utf-8")
                    before = path.read_bytes()
                    result = DISCOVERY.discover_programs(fixture.repository)
                    self.assertEqual(result.disposition, expected)
                    self.assertTrue(result.stop_required)
                    self.assertEqual(path.read_bytes(), before)
                finally:
                    fixture.close()

    def test_accepted_automatic_legacy_program_stops_at_upgrade_boundary(self) -> None:
        fixture = DiscoveryFixture()
        try:
            manifest_path = fixture.add_program("archive", "active")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["approval_mode"] = "approval:full"
            manifest["current_increment"]["state"] = "accepted"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            status_path = manifest_path.parent / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["approval_mode"] = "approval:full"
            status["current_increment_state"] = "accepted"
            status_path.write_text(
                json.dumps(status, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            approvals_path = manifest_path.parent / "state/approvals.jsonl"
            approvals = [
                json.loads(line)
                for line in approvals_path.read_text(encoding="utf-8").splitlines()
            ]
            for approval in approvals:
                if approval.get("type") == "program-approval":
                    approval["approval_mode"] = "approval:full"
            approvals_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in approvals),
                encoding="utf-8",
            )

            result = DISCOVERY.discover_programs(
                fixture.repository,
                observation_provider=lambda _path, _base: fixture.observation,
            )

            self.assertEqual(result.disposition, "legacy-rollover-upgrade-required")
            self.assertTrue(result.stop_required)
        finally:
            fixture.close()

    def test_multiple_new_controlling_candidates_require_selection(self) -> None:
        fixture = DiscoveryFixture()
        try:
            fixture.add_new_program("zeta")
            fixture.add_new_program("alpha")
            result = DISCOVERY.discover_programs(fixture.repository)
            self.assertEqual(result.disposition, "selection-required")
            self.assertTrue(result.stop_required)
        finally:
            fixture.close()

    def test_exact_accepted_continue_status_routes_to_compound_prompt_retry(self) -> None:
        from tests.test_diff_disposition import DIFF, awaiting_diff_program
        from tests.test_program_continuation import CONTINUATION

        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)}
        )
        try:
            prompt = CONTINUATION.render_accept_continue_prompt(program_root)

            def interrupt(label: str) -> None:
                if label == "accepted-status":
                    raise RuntimeError("injected accepted-status response loss")

            with mock.patch.object(DIFF, "_after_persist", side_effect=interrupt):
                with self.assertRaisesRegex(RuntimeError, "response loss"):
                    DIFF._persist_diff_acceptance_prefix(
                        program_root, prompt, observation
                    )
            result = DISCOVERY.discover_programs(fixture.repository)
            self.assertEqual(
                result.disposition,
                "accepted-continuation-retry-ready",
            )
            self.assertFalse(result.stop_required)
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
