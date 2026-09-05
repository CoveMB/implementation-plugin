import copy
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture,
    canonical_json,
    repository_snapshot,
)
from tests.script_module_support import load_script_module
from tests.test_program_activation import activated_program


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
STATE_AUTHORITY_PATH = SCRIPT_ROOT / "state_authority.py"
PROGRAM_FIXTURE = (
    REPOSITORY_ROOT
    / "tests/fixtures/program-authority/portable-archive-program"
)
STATE_OVERLAY = (
    REPOSITORY_ROOT
    / "tests/fixtures/state-authorization/portable-archive-run"
)

AUTHORITY = load_script_module("state_authority", STATE_AUTHORITY_PATH)

from tests.test_diff_disposition import awaiting_diff_program
from tests.test_blocked_recovery import BLOCKED, block_request, implementing_program
from tests.test_program_rollover import ROLLOVER, accepted_continuation_program


BASE_COMMIT = "b" * 40
HEAD_COMMIT = "a" * 40


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class ManagedLifecycleWriteTests(unittest.TestCase):
    def test_rollover_is_a_supported_distinct_lifecycle_action(self) -> None:
        self.assertIn("rollover-increment", AUTHORITY.ACTION_NAMES)

    def test_blocked_resume_is_a_supported_distinct_lifecycle_action(self) -> None:
        self.assertIn("resume-blocked-program", AUTHORITY.ACTION_NAMES)

    def test_status_brief_must_match_the_status_current_increment_grant(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root, observation = activated_program(fixture)
            replacement = program_root / "program/substituted-brief.md"
            replacement.write_text("# Substitute brief\n", encoding="utf-8")
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["brief_binding"] = {
                **status["brief_binding"],
                "path": "program/substituted-brief.md",
                "sha256": sha256_file(replacement),
            }
            status_path.write_bytes(canonical_json(status))

            issues = AUTHORITY.validate_state_authority(
                program_root, observation
            )

            self.assertIn(
                "status-current increment grant brief binding mismatch", issues
            )
        finally:
            fixture.close()

    def test_final_increment_derives_modify_review_and_closure_allocations(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root = fixture.repository / "implementation-programs/ARCHIVE-PROGRAM"
            program_root.parent.mkdir()
            shutil.copytree(fixture.candidate, program_root)

            required = AUTHORITY.required_future_lifecycle_writes(
                program_root, fixture.repository, "ARCHIVE-INDEX"
            )
            by_disposition = {
                disposition: {
                    requirement.path
                    for requirement in required
                    if requirement.disposition == disposition
                }
                for disposition in ("Create", "Modify", "Preserve")
            }
            prefix = "implementation-programs/ARCHIVE-PROGRAM"
            self.assertEqual(
                by_disposition["Modify"],
                {
                    f"{prefix}/state/approvals.jsonl",
                    f"{prefix}/state/status.json",
                    f"{prefix}/state/action-authorizations.jsonl",
                    f"{prefix}/state/increment-grants.jsonl",
                    f"{prefix}/state/rollovers.jsonl",
                    f"{prefix}/state/block-resolutions.jsonl",
                },
            )
            self.assertEqual(
                by_disposition["Create"],
                {
                    f"{prefix}/increments/ARCHIVE-INDEX/execution-baseline.json",
                    f"{prefix}/increments/ARCHIVE-INDEX/review-evidence.json",
                    f"{prefix}/increments/ARCHIVE-INDEX/review-packet.md",
                    f"{prefix}/closure/reconciliation.json",
                    f"{prefix}/closure/closure-packet.md",
                },
            )
            self.assertEqual(by_disposition["Preserve"], set())
        finally:
            fixture.close()

    def test_traceability_successor_does_not_cross_disjoint_allocations(self) -> None:
        traceability = {
            "atomic_requirements": [
                {"assigned_increments": ["INCREMENT-A", "INCREMENT-B"]},
                {"assigned_increments": ["INCREMENT-C", "INCREMENT-D"]},
            ]
        }

        self.assertIsNone(
            AUTHORITY._traceability_successor(traceability, "INCREMENT-B")
        )

    def test_traceability_successor_suppresses_multiple_direct_successors(self) -> None:
        traceability = {
            "atomic_requirements": [
                {"assigned_increments": ["INCREMENT-A", "INCREMENT-B"]},
                {"assigned_increments": ["INCREMENT-A", "INCREMENT-C"]},
            ]
        }

        self.assertIsNone(
            AUTHORITY._traceability_successor(traceability, "INCREMENT-A")
        )

    def test_traceability_successor_rejects_duplicate_allocation_entries(self) -> None:
        traceability = {
            "atomic_requirements": [
                {"assigned_increments": ["INCREMENT-A", "INCREMENT-A"]},
            ]
        }

        with self.assertRaisesRegex(ValueError, "unique strings"):
            AUTHORITY._traceability_successor(traceability, "INCREMENT-A")

    def test_unique_traceability_successor_replaces_closure_with_navigation(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root = fixture.repository / "implementation-programs/ARCHIVE-PROGRAM"
            program_root.parent.mkdir()
            shutil.copytree(fixture.candidate, program_root)
            manifest = json.loads((program_root / "manifest.json").read_text(encoding="utf-8"))
            traceability_path = program_root / manifest["logical_roles"]["traceability"]
            traceability = json.loads(traceability_path.read_text(encoding="utf-8"))
            traceability["atomic_requirements"][0]["assigned_increments"] = [
                "ARCHIVE-INDEX",
                "ARCHIVE-SUCCESSOR",
            ]
            traceability_path.write_bytes(canonical_json(traceability))

            required = AUTHORITY.required_future_lifecycle_writes(
                program_root, fixture.repository, "ARCHIVE-INDEX"
            )
            create = {
                requirement.path
                for requirement in required
                if requirement.disposition == "Create"
            }
            prefix = "implementation-programs/ARCHIVE-PROGRAM"
            self.assertIn(
                f"{prefix}/increments/ARCHIVE-INDEX/handoff.md", create
            )
            self.assertIn(
                f"{prefix}/increments/ARCHIVE-SUCCESSOR/brief.md", create
            )
            self.assertFalse(any("/closure/" in path for path in create))
        finally:
            fixture.close()

    def test_required_map_rejects_every_missing_or_misclassified_path(self) -> None:
        required = (
            AUTHORITY.ManagedWriteRequirement("state/status.json", "Modify"),
            AUTHORITY.ManagedWriteRequirement("review/evidence.json", "Create"),
        )
        valid = AUTHORITY.ExactFileMap(
            create=("review/evidence.json",),
            modify=("state/status.json",),
            preserve=("catalog.txt",),
        )
        self.assertEqual(
            AUTHORITY.validate_required_managed_file_map(valid, required), []
        )
        for candidate in (
            AUTHORITY.ExactFileMap((), valid.modify, valid.preserve),
            AUTHORITY.ExactFileMap(
                ("review/evidence.json", "state/status.json"), (), valid.preserve
            ),
        ):
            with self.subTest(candidate=candidate):
                self.assertTrue(
                    AUTHORITY.validate_required_managed_file_map(candidate, required)
                )

    def test_three_increment_allocation_selects_only_immediate_successor(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root = fixture.repository / "implementation-programs/ARCHIVE-PROGRAM"
            program_root.parent.mkdir()
            shutil.copytree(fixture.candidate, program_root)
            manifest = json.loads((program_root / "manifest.json").read_text(encoding="utf-8"))
            traceability_path = program_root / manifest["logical_roles"]["traceability"]
            traceability = json.loads(traceability_path.read_text(encoding="utf-8"))
            traceability["atomic_requirements"][0]["assigned_increments"] = [
                "ARCHIVE-INDEX",
                "ARCHIVE-NEXT-A",
                "ARCHIVE-NEXT-B",
            ]
            traceability_path.write_bytes(canonical_json(traceability))

            required = AUTHORITY.required_future_lifecycle_writes(
                program_root, fixture.repository, "ARCHIVE-INDEX"
            )
            create = {
                requirement.path
                for requirement in required
                if requirement.disposition == "Create"
            }
            prefix = "implementation-programs/ARCHIVE-PROGRAM/increments"
            self.assertIn(f"{prefix}/ARCHIVE-NEXT-A/brief.md", create)
            self.assertNotIn(f"{prefix}/ARCHIVE-NEXT-B/brief.md", create)
            self.assertFalse(any("/closure/" in path for path in create))
        finally:
            fixture.close()


def write_json_lines(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


class RolloverHistoryAuthorityTests(unittest.TestCase):
    def test_inherited_path_validation_failure_is_reported(self) -> None:
        fixture, program_root, observation, prompt = accepted_continuation_program(
            "accepted-state"
        )
        try:
            ROLLOVER.persist_increment_rollover(program_root, prompt, observation)
            normalized = ROLLOVER._fresh_observation(program_root, observation)

            with mock.patch(
                "program_rollover.validated_inherited_paths",
                side_effect=ValueError("inherited path diagnostics are unavailable"),
            ):
                issues = AUTHORITY.validate_state_authority(
                    program_root, normalized
                )

            self.assertIn("inherited path diagnostics are unavailable", issues)
        finally:
            fixture.close()

    def test_blocked_path_validation_failure_is_reported(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )

            with mock.patch(
                "blocked_recovery.blocked_workspace_paths",
                side_effect=ValueError("blocked path diagnostics are unavailable"),
            ):
                issues = AUTHORITY.validate_state_authority(
                    program_root, observation
                )

            self.assertIn("blocked path diagnostics are unavailable", issues)
        finally:
            fixture.close()

    def test_arbitrary_genesis_rollover_row_is_not_state_authority(self) -> None:
        fixture, program_root, observation = awaiting_diff_program(
            {"ARCHIVE-VERIFY": ("ARCHIVE-BLOCKER",)}
        )
        try:
            rollover_path = program_root / "state/rollovers.jsonl"
            write_json_lines(
                rollover_path,
                [{"current_increment_id": "ARCHIVE-BLOCKER"}],
            )
            before = repository_snapshot(program_root)

            issues = AUTHORITY.validate_state_authority(program_root, observation)

            self.assertIn(
                "unbound rollover history is not lifecycle authority", issues
            )
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_arbitrary_bound_rollover_suffix_is_not_state_authority(self) -> None:
        fixture, program_root, observation, prompt = accepted_continuation_program(
            "accepted-state"
        )
        try:
            ROLLOVER.persist_increment_rollover(program_root, prompt, observation)
            rollover_path = program_root / "state/rollovers.jsonl"
            records = [
                json.loads(line)
                for line in rollover_path.read_text(encoding="utf-8").splitlines()
            ]
            write_json_lines(
                rollover_path,
                [*records, {"current_increment_id": "ARCHIVE-BLOCKER"}],
            )
            normalized = ROLLOVER._fresh_observation(program_root, observation)
            before = repository_snapshot(program_root)

            issues = AUTHORITY.validate_state_authority(program_root, normalized)

            self.assertIn(
                "unbound rollover history is not lifecycle authority", issues
            )
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_exact_rollover_record_prefix_remains_state_authority(self) -> None:
        fixture, program_root, observation, prompt = accepted_continuation_program(
            "accepted-state"
        )
        try:
            def interrupt(completed_label: str) -> None:
                if completed_label == "rollover-record":
                    raise RuntimeError("injected rollover interruption")

            with mock.patch.object(ROLLOVER, "_after_persist", side_effect=interrupt):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    ROLLOVER.persist_increment_rollover(
                        program_root, prompt, observation
                    )
            before = repository_snapshot(program_root)

            self.assertEqual(
                AUTHORITY.validate_state_authority(program_root, observation),
                [],
            )
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()


class DeferredMutationGuardTests(unittest.TestCase):
    def test_new_program_state_rejects_malformed_authority_bindings(self) -> None:
        fixture, program_root, observation = awaiting_diff_program()
        try:
            status_path = program_root / "state/status.json"
            original = json.loads(status_path.read_text(encoding="utf-8"))
            cases = (
                (
                    "transition authority",
                    "v2 transition authority is invalid",
                    lambda status: status["transition_authority"].update(event_id=""),
                ),
                (
                    "execution authorization",
                    "v2 execution authorization binding is invalid",
                    lambda status: status["execution_authorization"].update(scope=""),
                ),
            )
            for label, expected, mutate in cases:
                with self.subTest(label=label):
                    candidate = copy.deepcopy(original)
                    mutate(candidate)
                    status_path.write_bytes(canonical_json(candidate))

                    issues = AUTHORITY.validate_state_authority(
                        program_root, observation
                    )

                    self.assertIn(expected, issues)
        finally:
            fixture.close()

    def test_generic_new_program_diff_acceptance_stops_before_any_write(self) -> None:
        fixture, program_root, observation = awaiting_diff_program()
        try:
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            request = AUTHORITY.TransitionRequest(
                expected_status_sha256=sha256_file(status_path),
                expected_state_sequence=status["state_sequence"],
                target_program_state="active",
                target_increment_id=status["current_increment_id"],
                target_increment_state="accepted",
                transition_event_id="DIRECT-DIFF-ACCEPTANCE",
                action_authorization_id=None,
                evidence={"action_scope": "accept current increment"},
                authority_kind="approval-event",
            )
            before = repository_snapshot(program_root)
            with self.assertRaisesRegex(
                ValueError, "typed-diff-disposition-required"
            ):
                AUTHORITY.apply_state_transition(program_root, request, observation)
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_new_program_blocked_and_superseded_transitions_stop_before_writes(self) -> None:
        cases = (
            ("blocked", "blocked", "blocked-transaction-required"),
            ("superseded", "superseded", "program-revision-workflow-required"),
        )
        for program_state, increment_state, expected in cases:
            with self.subTest(program_state=program_state):
                fixture = BootstrapFixture()
                try:
                    program_root, observation = activated_program(fixture)
                    status_path = program_root / "state/status.json"
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    request = AUTHORITY.TransitionRequest(
                        expected_status_sha256=sha256_file(status_path),
                        expected_state_sequence=status["state_sequence"],
                        target_program_state=program_state,
                        target_increment_id=status["current_increment_id"],
                        target_increment_state=increment_state,
                        transition_event_id="DIRECT-DEFERRED-MUTATION",
                        action_authorization_id=None,
                        evidence={"action_scope": "deferred mutation"},
                    )
                    before = repository_snapshot(program_root)
                    with self.assertRaisesRegex(ValueError, expected):
                        AUTHORITY.apply_state_transition(
                            program_root, request, observation
                        )
                    self.assertEqual(repository_snapshot(program_root), before)
                finally:
                    fixture.close()

    def test_new_program_transition_out_of_blocked_stops_before_writes(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root, observation = activated_program(fixture)
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status.update(
                program_state="blocked",
                current_increment_state="blocked",
                blocked_context={
                    "resume_program_state": "active",
                    "resume_increment_state": "preparing",
                },
            )
            status_path.write_bytes(canonical_json(status))
            request = AUTHORITY.TransitionRequest(
                expected_status_sha256=sha256_file(status_path),
                expected_state_sequence=status["state_sequence"],
                target_program_state="active",
                target_increment_id=status["current_increment_id"],
                target_increment_state="preparing",
                transition_event_id="DIRECT-BLOCK-RESOLUTION",
                action_authorization_id=None,
                evidence={"action_scope": "resolve block"},
            )
            before = repository_snapshot(program_root)
            with self.assertRaisesRegex(ValueError, "blocked-transaction-required"):
                AUTHORITY.apply_state_transition(program_root, request, observation)
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()


class StateAuthorityFixture:
    def __init__(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "portable-archive-run"
        shutil.copytree(PROGRAM_FIXTURE, self.root)
        program_approval = json.loads(
            (self.root / "state/approvals.jsonl").read_text(encoding="utf-8")
        )
        shutil.copytree(STATE_OVERLAY, self.root, dirs_exist_ok=True)

        self.manifest_path = self.root / "manifest.json"
        self.status_path = self.root / "state/status.json"
        self.workspace_path = self.root / "state/workspace.json"
        self.approvals_path = self.root / "state/approvals.jsonl"
        self.authorizations_path = self.root / "state/action-authorizations.jsonl"
        self.brief_path = self.root / "increments/archive-index/brief.md"
        self.plan_path = self.root / "increments/archive-index/exact-file-plan.md"
        self.packet_path = self.root / "increments/archive-index/review-packet.md"

        self.manifest = self.load_json("manifest.json")
        self.traceability = self.load_json("program/traceability.json")
        self.source_sha256 = self.manifest["source_binding"]["sha256"]
        self.program_sha256 = self.manifest["program_binding"]["sha256"]
        self.semantic_sha256 = self.traceability["coverage_assertion"][
            "semantic_requirements_sha256"
        ]
        self.brief_sha256 = sha256_file(self.brief_path)
        self.plan_sha256 = sha256_file(self.plan_path)
        self.packet_sha256 = sha256_file(self.packet_path)

        workspace = self.load_json("state/workspace.json")
        workspace["repository"] = {"identity": str(self.root)}
        workspace["implementation_workspace"].update(
            path=str(self.root),
            branch="archive-maintenance",
            base_commit=BASE_COMMIT,
            head_commit_at_selection=HEAD_COMMIT,
        )
        write_json(self.workspace_path, workspace)
        self.workspace_sha256 = sha256_file(self.workspace_path)

        self.observation = AUTHORITY.RepositoryObservation(
            repository=str(self.root),
            path=str(self.root),
            branch="archive-maintenance",
            base_commit=BASE_COMMIT,
            head_commit=HEAD_COMMIT,
            staged_paths=(),
            modified_paths=(),
            untracked_paths=(),
            conflicted_paths=(),
            active_git_operation=None,
        )

        status = self.load_json("state/status.json")
        status["source_binding"] = {
            "source_id": self.manifest["source_binding"]["source_id"],
            "sha256": self.source_sha256,
        }
        status["program_binding"] = {
            "sha256": self.program_sha256,
            "semantic_requirements_sha256": self.semantic_sha256,
        }
        status["brief_binding"] = {
            "path": "increments/archive-index/brief.md",
            "sha256": self.brief_sha256,
            "workspace_sha256": self.workspace_sha256,
            "head_commit": HEAD_COMMIT,
        }
        status["pending_exact_file_plan_sha256"] = self.plan_sha256
        write_json(self.status_path, status)

        self.plan_approval = self._bound_record(
            {
                "schema_version": "implementation-approval/v1",
                "event_id": "ARCHIVE-PLAN-APPROVAL",
                "type": "exact-file-plan-approval",
                "decision": "approved",
                "scope": ["authorize the bound archive index plan"],
            }
        )
        self.implementation_authorization = self._bound_record(
            {
                "schema_version": "implementation-action-authorization/v1",
                "authorization_id": "ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
                "decision": "authorized",
                "actions": ["modify-workspace", "run-local-verification"],
                "scope": ["implement the bound archive index plan"],
                "constraints": [],
                "excluded": [
                    "create-draft-pull-request",
                    "merge",
                    "release",
                    "deploy",
                    "migrate",
                    "destructive-operation",
                    "modify-provider-state",
                ],
            }
        )
        write_json_lines(self.approvals_path, [program_approval, self.plan_approval])
        write_json_lines(
            self.authorizations_path, [self.implementation_authorization]
        )

        self.manifest["logical_roles"].update(
            status="state/status.json",
            workspace="state/workspace.json",
            action_authorizations="state/action-authorizations.jsonl",
            current_increment_brief="increments/archive-index/brief.md",
            current_exact_file_plan="increments/archive-index/exact-file-plan.md",
            current_review_packet="increments/archive-index/review-packet.md",
        )
        self.manifest["current_increment"] = {
            "increment_id": "archive-index",
            "state": "awaiting-plan-approval",
            "exact_file_plan_sha256": self.plan_sha256,
        }
        self.manifest["workspace_binding"] = {
            "path": str(self.root),
            "branch": "archive-maintenance",
            "base_commit": BASE_COMMIT,
            "head_at_preparation": HEAD_COMMIT,
        }
        write_json(self.manifest_path, self.manifest)

    def _bound_record(self, specific: dict[str, object]) -> dict[str, object]:
        return {
            **specific,
            "program_id": self.manifest["program_id"],
            "program_revision": self.manifest["program_revision"],
            "source_id": self.manifest["source_binding"]["source_id"],
            "source_sha256": self.source_sha256,
            "program_sha256": self.program_sha256,
            "semantic_requirements_sha256": self.semantic_sha256,
            "increment_id": "archive-index",
            "brief_sha256": self.brief_sha256,
            "exact_file_plan_sha256": self.plan_sha256,
            "approval_mode": "approval:standard",
            "workspace": {
                "path": str(self.root),
                "branch": "archive-maintenance",
                "base_commit": BASE_COMMIT,
                "head_commit": HEAD_COMMIT,
            },
        }

    def close(self) -> None:
        self.temporary_directory.cleanup()

    def load_json(self, relative_path: str) -> dict[str, object]:
        return json.loads((self.root / relative_path).read_text(encoding="utf-8"))

    def write_json(self, relative_path: str, value: dict[str, object]) -> None:
        write_json(self.root / relative_path, value)

    def approvals(self) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in self.approvals_path.read_text(encoding="utf-8").splitlines()
        ]

    def authorizations(self) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in self.authorizations_path.read_text(
                encoding="utf-8"
            ).splitlines()
        ]

    def approval_binding(self) -> object:
        return AUTHORITY.ApprovalBinding(
            event_type="exact-file-plan-approval",
            program_id=self.manifest["program_id"],
            program_revision=self.manifest["program_revision"],
            source_sha256=self.source_sha256,
            program_sha256=self.program_sha256,
            semantic_requirements_sha256=self.semantic_sha256,
            increment_id="archive-index",
            brief_sha256=self.brief_sha256,
            exact_file_plan_sha256=self.plan_sha256,
            approval_mode="approval:standard",
            workspace_path=str(self.root),
            workspace_branch="archive-maintenance",
            workspace_base_commit=BASE_COMMIT,
            workspace_head_commit=HEAD_COMMIT,
            source_id=self.manifest["source_binding"]["source_id"],
        )

    def action_binding(self, action: str = "modify-workspace") -> object:
        return AUTHORITY.ActionBinding(
            action=action,
            scope="implement the bound archive index plan",
            program_id=self.manifest["program_id"],
            program_revision=self.manifest["program_revision"],
            source_sha256=self.source_sha256,
            program_sha256=self.program_sha256,
            semantic_requirements_sha256=self.semantic_sha256,
            increment_id="archive-index",
            brief_sha256=self.brief_sha256,
            exact_file_plan_sha256=self.plan_sha256,
            approval_mode="approval:standard",
            workspace_path=str(self.root),
            workspace_branch="archive-maintenance",
            workspace_base_commit=BASE_COMMIT,
            workspace_head_commit=HEAD_COMMIT,
            source_id=self.manifest["source_binding"]["source_id"],
        )


class StateAuthorityTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = StateAuthorityFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def assert_issue(self, issues: list[str], expected: str) -> None:
        self.assertTrue(
            any(expected in issue for issue in issues),
            f"Expected issue containing {expected!r}; received {issues!r}",
        )


class StateMatrixTests(unittest.TestCase):
    def test_every_program_state_pair_matches_the_declared_matrix(self) -> None:
        states = tuple(AUTHORITY.PROGRAM_TRANSITIONS)
        self.assertEqual(len(states), 7)
        for current in states:
            for target in states:
                with self.subTest(current=current, target=target):
                    expected = target in AUTHORITY.PROGRAM_TRANSITIONS[current]
                    self.assertEqual(
                        AUTHORITY.is_program_transition_allowed(current, target),
                        expected,
                    )

    def test_every_increment_state_pair_matches_the_declared_matrix(self) -> None:
        states = tuple(AUTHORITY.INCREMENT_TRANSITIONS)
        self.assertEqual(len(states), 13)
        for current in states:
            for target in states:
                with self.subTest(current=current, target=target):
                    expected = target in AUTHORITY.INCREMENT_TRANSITIONS[current]
                    self.assertEqual(
                        AUTHORITY.is_increment_transition_allowed(current, target),
                        expected,
                    )

    def test_blocked_state_resumes_only_to_the_recorded_target(self) -> None:
        context = {"resume_increment_state": "reviewing"}
        self.assertTrue(
            AUTHORITY.is_increment_transition_allowed(
                "blocked", "reviewing", blocked_context=context
            )
        )
        self.assertFalse(
            AUTHORITY.is_increment_transition_allowed(
                "blocked", "implementing", blocked_context=context
            )
        )


class ApprovalModeTests(unittest.TestCase):
    EXPECTED = {
        "approval:standard": (
            "one-increment",
            True,
            ("material-decision", "contradiction", "hard-stop"),
            "user",
            False,
        ),
        "approval:pre-approve": (
            "one-increment",
            False,
            (
                "user-owned-decision",
                "program-amendment",
                "contradiction",
                "hard-stop",
            ),
            "user",
            False,
        ),
        "approval:full-increment": (
            "one-increment",
            False,
            ("hard-stop",),
            "user",
            False,
        ),
        "approval:full-diff": (
            "one-increment",
            False,
            ("hard-stop",),
            "automatic-after-verification-and-packet",
            False,
        ),
        "approval:full": (
            "one-increment",
            False,
            ("hard-stop",),
            "automatic-after-verification-and-packet",
            False,
        ),
    }

    def test_all_five_modes_match_the_approved_matrix(self) -> None:
        self.assertEqual(set(AUTHORITY.APPROVAL_MODE_POLICIES), set(self.EXPECTED))
        for mode, expected in self.EXPECTED.items():
            with self.subTest(mode=mode):
                policy = AUTHORITY.approval_mode_policy(mode)
                self.assertEqual(
                    (
                        policy.scope,
                        policy.routine_plan_pause,
                        policy.interruptions,
                        policy.diff_acceptance,
                        policy.automatic_continuation,
                    ),
                    expected,
                )

    def test_default_applies_only_when_creating_new_state(self) -> None:
        self.assertEqual(
            AUTHORITY.approval_mode_policy(None, creating=True).mode,
            "approval:full-increment",
        )
        with self.assertRaisesRegex(ValueError, "persisted approval mode"):
            AUTHORITY.approval_mode_policy(None)
        with self.assertRaisesRegex(ValueError, "unsupported approval mode"):
            AUTHORITY.approval_mode_policy("approval:unknown")


class WorkspaceAndBindingTests(StateAuthorityTestCase):
    def test_valid_state_authority_and_workspace_pass(self) -> None:
        self.assertEqual(
            AUTHORITY.validate_state_authority(
                self.fixture.root, self.fixture.observation
            ),
            [],
        )

    def test_workspace_observation_mismatches_fail_closed(self) -> None:
        replacements = {
            "path": {"path": str(self.fixture.root / "other")},
            "branch": {"branch": "other-branch"},
            "base": {"base_commit": "c" * 40},
            "head": {"head_commit": "d" * 40},
            "dirty": {"modified_paths": ("user-note.md",)},
            "operation": {"active_git_operation": "rebase"},
        }
        for label, replacement in replacements.items():
            with self.subTest(label=label):
                observation = AUTHORITY.RepositoryObservation(
                    **{**self.fixture.observation.__dict__, **replacement}
                )
                issues = AUTHORITY.validate_state_authority(
                    self.fixture.root, observation
                )
                self.assertTrue(issues, label)

    def test_stale_brief_plan_and_schema_fail_closed(self) -> None:
        self.fixture.brief_path.write_text("changed brief\n", encoding="utf-8")
        self.assert_issue(
            AUTHORITY.validate_state_authority(
                self.fixture.root, self.fixture.observation
            ),
            "brief digest",
        )

        self.fixture.brief_path.write_text(
            "# Archive Index Brief\n\nBuild the checksum index for the approved portable archive program.\n",
            encoding="utf-8",
        )
        status = self.fixture.load_json("state/status.json")
        status["pending_exact_file_plan_sha256"] = "f" * 64
        self.fixture.write_json("state/status.json", status)
        self.assert_issue(
            AUTHORITY.validate_state_authority(
                self.fixture.root, self.fixture.observation
            ),
            "plan digest",
        )

        status["pending_exact_file_plan_sha256"] = self.fixture.plan_sha256
        status["schema_version"] = "implementation-program-status/v99"
        self.fixture.write_json("state/status.json", status)
        self.assert_issue(
            AUTHORITY.validate_state_authority(
                self.fixture.root, self.fixture.observation
            ),
            "unsupported status schema",
        )

    def test_approval_binding_rejects_every_stale_dimension(self) -> None:
        required = self.fixture.approval_binding()
        self.assertEqual(
            AUTHORITY.validate_approval_binding(
                self.fixture.approvals(), required
            ),
            [],
        )
        mutations = {
            "program_id": "OTHER-PROGRAM",
            "program_revision": 2,
            "source_id": "OTHER-SOURCE",
            "source_sha256": "0" * 64,
            "program_sha256": "1" * 64,
            "semantic_requirements_sha256": "2" * 64,
            "increment_id": "other-index",
            "brief_sha256": "3" * 64,
            "exact_file_plan_sha256": "4" * 64,
            "approval_mode": "approval:full",
            "decision": "rejected",
            "schema_version": "implementation-approval/v99",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                records = copy.deepcopy(self.fixture.approvals())
                records[-1][field] = value
                self.assertTrue(
                    AUTHORITY.validate_approval_binding(records, required), field
                )

        records = copy.deepcopy(self.fixture.approvals())
        records[-1]["scope"] = []
        self.assertTrue(AUTHORITY.validate_approval_binding(records, required))

        for field, value in {
            "path": "/other",
            "branch": "other",
            "base_commit": "c" * 40,
            "head_commit": "d" * 40,
        }.items():
            with self.subTest(workspace_field=field):
                records = copy.deepcopy(self.fixture.approvals())
                records[-1]["workspace"][field] = value
                self.assertTrue(
                    AUTHORITY.validate_approval_binding(records, required), field
                )

    def test_conflicting_duplicate_approval_is_rejected(self) -> None:
        records = self.fixture.approvals()
        duplicate = copy.deepcopy(records[-1])
        duplicate["event_id"] = "ARCHIVE-PLAN-APPROVAL-DUPLICATE"
        records.append(duplicate)
        self.assert_issue(
            AUTHORITY.validate_approval_binding(
                records, self.fixture.approval_binding()
            ),
            "multiple matching approvals",
        )

        rejected = copy.deepcopy(records[-1])
        rejected["event_id"] = "ARCHIVE-PLAN-REJECTION"
        rejected["decision"] = "rejected"
        self.assert_issue(
            AUTHORITY.validate_approval_binding(
                [records[0], records[-1], rejected],
                self.fixture.approval_binding(),
            ),
            "conflicting approval records",
        )


class ActionAuthorizationTests(StateAuthorityTestCase):
    CONSEQUENT_ACTIONS = (
        "create-draft-pull-request",
        "merge",
        "publish",
        "release",
        "deploy",
        "migrate",
        "destructive-operation",
        "modify-provider-state",
        "modify-external-state",
    )

    def test_no_approval_mode_implies_consequential_action_authority(self) -> None:
        for mode in AUTHORITY.APPROVAL_MODE_POLICIES:
            for action in self.CONSEQUENT_ACTIONS:
                with self.subTest(mode=mode, action=action):
                    binding = self.fixture.action_binding(action)
                    binding = AUTHORITY.ActionBinding(
                        **{**binding.__dict__, "approval_mode": mode}
                    )
                    decision = AUTHORITY.decide_action_authorization([], binding)
                    self.assertFalse(decision.authorized)
                    self.assertIsNone(decision.authorization_id)

    def test_exact_action_grant_authorizes_only_its_bound_tuple(self) -> None:
        decision = AUTHORITY.decide_action_authorization(
            self.fixture.authorizations(), self.fixture.action_binding()
        )
        self.assertTrue(decision.authorized)
        self.assertEqual(
            decision.authorization_id, "ARCHIVE-IMPLEMENTATION-AUTHORIZATION"
        )

        mutations = {
            "action": "deploy",
            "scope": "different scope",
            "increment_id": "other-index",
            "workspace_head_commit": "d" * 40,
            "exact_file_plan_sha256": "e" * 64,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                binding = self.fixture.action_binding()
                binding = AUTHORITY.ActionBinding(
                    **{**binding.__dict__, field: value}
                )
                self.assertFalse(
                    AUTHORITY.decide_action_authorization(
                        self.fixture.authorizations(), binding
                    ).authorized
                )

    def test_rejected_revoked_expired_legacy_and_conflicting_grants_fail(self) -> None:
        required = self.fixture.action_binding()
        for mutation in (
            {"decision": "rejected"},
            {"revoked": True},
            {"expires_at": "2000-01-01T00:00:00Z"},
            {"schema_version": None},
        ):
            with self.subTest(mutation=mutation):
                records = copy.deepcopy(self.fixture.authorizations())
                for field, value in mutation.items():
                    if value is None:
                        records[0].pop(field)
                    else:
                        records[0][field] = value
                self.assertFalse(
                    AUTHORITY.decide_action_authorization(records, required).authorized
                )

        records = self.fixture.authorizations()
        duplicate = copy.deepcopy(records[0])
        duplicate["authorization_id"] = "ARCHIVE-SECOND-AUTHORIZATION"
        records.append(duplicate)
        decision = AUTHORITY.decide_action_authorization(records, required)
        self.assertFalse(decision.authorized)
        self.assertIn("multiple matching authorizations", decision.issues)

        rejected = copy.deepcopy(records[0])
        rejected["authorization_id"] = "ARCHIVE-REJECTED-AUTHORIZATION"
        rejected["decision"] = "rejected"
        decision = AUTHORITY.decide_action_authorization(
            [records[0], rejected], required
        )
        self.assertFalse(decision.authorized)
        self.assertIn("conflicting action authorization records", decision.issues)


class AtomicPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_atomic_replace_retains_prior_digest_schema_and_sequence(self) -> None:
        path = self.root / "status.json"
        prior = {
            "schema_version": "implementation-program-status/v1",
            "state_sequence": 7,
            "program_state": "active",
        }
        write_json(path, prior)
        old_sha256 = sha256_file(path)
        current = {
            "schema_version": "implementation-program-status/v1",
            "state_sequence": 8,
            "program_state": "active",
            "previous_state": {
                "schema_version": prior["schema_version"],
                "state_sequence": prior["state_sequence"],
                "status_sha256": old_sha256,
            },
        }
        receipt = AUTHORITY.atomic_replace_json(path, current, old_sha256)
        self.assertEqual(receipt.prior_sha256, old_sha256)
        self.assertEqual(receipt.current_sha256, sha256_file(path))
        self.assertEqual(json.loads(path.read_text())["previous_state"], current["previous_state"])

    def test_atomic_replace_receipt_identifies_own_bytes_after_unlock(self) -> None:
        path = self.root / "status.json"
        write_json(path, {"schema_version": "record/v1", "value": 1})
        replacement = {"schema_version": "record/v1", "value": 2}
        replacement_sha256 = hashlib.sha256(canonical_json(replacement)).hexdigest()
        release_lock = AUTHORITY._release_advisory_lock

        def release_then_replace(lock: object) -> None:
            release_lock(lock)
            path.write_text("foreign replacement\n", encoding="utf-8")

        with mock.patch.object(
            AUTHORITY,
            "_release_advisory_lock",
            side_effect=release_then_replace,
        ):
            receipt = AUTHORITY.atomic_replace_json(
                path,
                replacement,
                sha256_file(path),
            )

        self.assertEqual(receipt.current_sha256, replacement_sha256)
        self.assertNotEqual(receipt.current_sha256, sha256_file(path))

    def test_compare_and_swap_and_replace_failure_preserve_old_bytes(self) -> None:
        path = self.root / "status.json"
        write_json(path, {"schema_version": "record/v1", "value": 1})
        old_bytes = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "digest changed"):
            AUTHORITY.atomic_replace_json(path, {"value": 2}, "0" * 64)
        self.assertEqual(path.read_bytes(), old_bytes)

        with mock.patch.object(AUTHORITY.os, "replace", side_effect=OSError("blocked")):
            with self.assertRaisesRegex(OSError, "blocked"):
                AUTHORITY.atomic_replace_json(
                    path, {"schema_version": "record/v1", "value": 2}, sha256_file(path)
                )
        self.assertEqual(path.read_bytes(), old_bytes)
        self.assertEqual(list(self.root.glob(".status.json.*.tmp")), [])

        with mock.patch.object(AUTHORITY.os, "fsync", side_effect=OSError("no sync")):
            with self.assertRaisesRegex(OSError, "no sync"):
                AUTHORITY.atomic_replace_json(
                    path,
                    {"schema_version": "record/v1", "value": 3},
                    sha256_file(path),
                )
        self.assertEqual(path.read_bytes(), old_bytes)
        self.assertEqual(list(self.root.glob(".status.json.*.tmp")), [])

    def test_compare_and_swap_rechecks_the_target_immediately_before_replace(self) -> None:
        path = self.root / "status.json"
        write_json(path, {"schema_version": "record/v1", "value": 1})
        old_sha256 = sha256_file(path)

        with (
            mock.patch.object(
                AUTHORITY,
                "sha256_file",
                side_effect=(old_sha256, "f" * 64),
            ),
            mock.patch.object(AUTHORITY.os, "replace") as replace,
        ):
            with self.assertRaisesRegex(ValueError, "digest changed"):
                AUTHORITY.atomic_replace_json(
                    path,
                    {"schema_version": "record/v1", "value": 2},
                    old_sha256,
                )

        replace.assert_not_called()

    def test_atomic_replace_syncs_file_and_parent_directory(self) -> None:
        path = self.root / "status.json"
        write_json(path, {"schema_version": "record/v1", "value": 1})

        with mock.patch.object(
            AUTHORITY.os, "fsync", wraps=AUTHORITY.os.fsync
        ) as fsync:
            AUTHORITY.atomic_replace_json(
                path,
                {"schema_version": "record/v1", "value": 2},
                sha256_file(path),
            )

        self.assertGreaterEqual(fsync.call_count, 2)

    def test_windows_named_mutex_runs_compare_and_swap_without_fcntl(self) -> None:
        path = self.root / "status.json"
        write_json(path, {"schema_version": "record/v1", "value": 1})
        windows_backend = mock.Mock()
        windows_backend.CreateMutexW.return_value = 71
        windows_backend.WaitForSingleObject.return_value = 0
        windows_backend.ReleaseMutex.return_value = 1
        windows_backend.CloseHandle.return_value = 1
        file_events: list[str] = []
        real_close = AUTHORITY.os.close
        real_replace = AUTHORITY.os.replace

        def close_descriptor(descriptor: int) -> None:
            file_events.append("close")
            real_close(descriptor)

        def replace_file(source: object, target: object) -> None:
            file_events.append("replace")
            real_replace(source, target)

        with (
            mock.patch.object(AUTHORITY, "_WINDOWS", True),
            mock.patch.object(AUTHORITY, "_fcntl", None),
            mock.patch.object(AUTHORITY, "_kernel32", windows_backend),
            mock.patch.object(AUTHORITY.os, "close", side_effect=close_descriptor),
            mock.patch.object(AUTHORITY.os, "replace", side_effect=replace_file),
        ):
            receipt = AUTHORITY.atomic_replace_json(
                path,
                {"schema_version": "record/v1", "value": 2},
                sha256_file(path),
            )

        self.assertEqual(receipt.current_sha256, sha256_file(path))
        windows_backend.CreateMutexW.assert_called_once()
        windows_backend.WaitForSingleObject.assert_called_once_with(71, 0xFFFFFFFF)
        windows_backend.ReleaseMutex.assert_called_once_with(71)
        windows_backend.CloseHandle.assert_called_once_with(71)
        self.assertLess(file_events.index("close"), file_events.index("replace"))

    @unittest.skipUnless(os.name == "nt", "requires native Windows rename semantics")
    def test_native_windows_compare_and_swap_replaces_closed_destination(self) -> None:
        path = self.root / "status.json"
        write_json(path, {"schema_version": "record/v1", "value": 1})

        receipt = AUTHORITY.atomic_replace_json(
            path,
            {"schema_version": "record/v1", "value": 2},
            sha256_file(path),
        )

        self.assertEqual(receipt.current_sha256, sha256_file(path))
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["value"], 2)

    def test_atomic_json_line_append_preserves_prefix_and_rejects_duplicate_id(self) -> None:
        path = self.root / "events.jsonl"
        path.write_text('{"event_id":"FIRST"}\n', encoding="utf-8")
        prefix = path.read_bytes()
        receipt = AUTHORITY.atomic_append_json_line(
            path,
            {"event_id": "SECOND", "decision": "approved"},
            sha256_file(path),
        )
        self.assertTrue(path.read_bytes().startswith(prefix))
        self.assertEqual(receipt.current_sha256, sha256_file(path))
        with self.assertRaisesRegex(ValueError, "duplicate record identifier"):
            AUTHORITY.atomic_append_json_line(
                path, {"event_id": "SECOND"}, sha256_file(path)
            )

        path.write_text('{"event_id":"FIRST"}', encoding="utf-8")
        old_bytes = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "trailing newline"):
            AUTHORITY.atomic_append_json_line(
                path, {"event_id": "THIRD"}, sha256_file(path)
            )
        self.assertEqual(path.read_bytes(), old_bytes)


class ClosureStorageResolutionTests(unittest.TestCase):
    def test_manifest_owned_closure_paths_resolve_without_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(
                root / "manifest.json",
                {
                    "closure_storage": {
                        "schema_version": "implementation-closure-storage/v1",
                        "root": "closure",
                        "reconciliation_filename": "reconciliation.json",
                        "packet_filename": "closure-packet.md",
                    }
                },
            )
            self.assertEqual(
                AUTHORITY.resolve_program_closure_paths(root),
                {
                    "reconciliation": root / "closure/reconciliation.json",
                    "packet": root / "closure/closure-packet.md",
                },
            )


class StateApplicationAndCliTests(StateAuthorityTestCase):
    def test_v2_authorized_state_requires_exact_plan_approval_lineage(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status.update(
            schema_version="implementation-program-status/v2",
            current_increment_state="authorized",
            approved_exact_file_plan_sha256=self.fixture.plan_sha256,
            pending_exact_file_plan_sha256=None,
            execution_authorization={
                "authorization_id": "ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
                "scope": "implement the bound archive index plan",
            },
        )
        self.fixture.write_json("state/status.json", status)
        write_json_lines(
            self.fixture.approvals_path,
            [
                record
                for record in self.fixture.approvals()
                if record.get("event_id") != "ARCHIVE-PLAN-APPROVAL"
            ],
        )

        issues = AUTHORITY.validate_state_authority(
            self.fixture.root,
            self.fixture.observation,
        )

        self.assertIn("v2 approved plan requires exact plan approval", issues)
        self.assertIn("v2 approved state requires transition authority", issues)

    def test_v2_plan_approval_records_governance_transition_before_execution_grant(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status["schema_version"] = "implementation-program-status/v2"
        self.fixture.write_json("state/status.json", status)
        write_json_lines(self.fixture.authorizations_path, [])
        request = AUTHORITY.TransitionRequest(
            expected_status_sha256=sha256_file(self.fixture.status_path),
            expected_state_sequence=1,
            target_program_state="active",
            target_increment_id="archive-index",
            target_increment_state="authorized",
            transition_event_id="ARCHIVE-PLAN-APPROVAL",
            action_authorization_id=None,
            evidence={"action_scope": "implement the bound archive index plan"},
            authority_kind="approval-event",
            execution_authorization_id="ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
            checkpoint_id="ARCHIVE-PLAN-CHECKPOINT",
        )

        receipt = AUTHORITY.apply_state_transition(
            self.fixture.root, request, self.fixture.observation
        )

        self.assertEqual(receipt.increment_state, "authorized")
        current = self.fixture.load_json("state/status.json")
        self.assertEqual(
            current["transition_authority"],
            {
                "kind": "approval-event",
                "event_id": "ARCHIVE-PLAN-APPROVAL",
                "checkpoint_id": "ARCHIVE-PLAN-CHECKPOINT",
            },
        )
        self.assertEqual(
            current["execution_authorization"],
            {
                "authorization_id": "ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
                "scope": "implement the bound archive index plan",
            },
        )

        current["transition_authority"]["event_id"] = ""
        self.assertIn(
            "v2 transition authority is invalid",
            AUTHORITY.validate_state(
                self.fixture.root,
                self.fixture.manifest,
                current,
                self.fixture.observation,
            ),
        )

    def test_v2_nonapproval_transition_still_requires_exact_execution_authority(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status.update(
            schema_version="implementation-program-status/v2",
            current_increment_state="authorized",
            approved_exact_file_plan_sha256=self.fixture.plan_sha256,
            pending_exact_file_plan_sha256=None,
            execution_authorization={
                "authorization_id": "ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
                "scope": "implement the bound archive index plan",
            },
            transition_authority={
                "kind": "approval-event",
                "event_id": "ARCHIVE-PLAN-APPROVAL",
            },
        )
        self.fixture.write_json("state/status.json", status)
        request = AUTHORITY.TransitionRequest(
            expected_status_sha256=sha256_file(self.fixture.status_path),
            expected_state_sequence=1,
            target_program_state="active",
            target_increment_id="archive-index",
            target_increment_state="implementing",
            transition_event_id="ARCHIVE-IMPLEMENTATION-STARTED",
            action_authorization_id="ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
            evidence={"action_scope": "implement the bound archive index plan"},
            authority_kind="action-authorization",
            execution_authorization_id="ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
            checkpoint_id="ARCHIVE-PLAN-CHECKPOINT",
        )

        receipt = AUTHORITY.apply_state_transition(
            self.fixture.root, request, self.fixture.observation
        )
        self.assertEqual(receipt.increment_state, "implementing")

        current = self.fixture.load_json("state/status.json")
        current.update(
            current_increment_state="authorized",
            state_sequence=1,
        )
        current.pop("previous_state", None)
        self.fixture.write_json("state/status.json", current)
        wrong_kind = AUTHORITY.TransitionRequest(
            **{
                **request.__dict__,
                "expected_status_sha256": sha256_file(self.fixture.status_path),
                "authority_kind": "approval-event",
                "action_authorization_id": None,
            }
        )
        with self.assertRaisesRegex(ValueError, "action-authorization authority"):
            AUTHORITY.apply_state_transition(
                self.fixture.root, wrong_kind, self.fixture.observation
            )

    def test_transition_authority_policy_classifies_every_declared_edge(self) -> None:
        for current, targets in AUTHORITY.PROGRAM_TRANSITIONS.items():
            for target in targets:
                with self.subTest(domain="program", current=current, target=target):
                    self.assertIn(
                        AUTHORITY.transition_authority_policy(
                            current,
                            target,
                            "accepted",
                            "accepted",
                        ),
                        {"approval-event", "action-authorization"},
                    )
        for current, targets in AUTHORITY.INCREMENT_TRANSITIONS.items():
            for target in targets:
                with self.subTest(domain="increment", current=current, target=target):
                    self.assertIn(
                        AUTHORITY.transition_authority_policy(
                            "active",
                            "active",
                            current,
                            target,
                        ),
                        {"approval-event", "action-authorization"},
                    )
        self.assertEqual(
            AUTHORITY.transition_authority_policy(
                "blocked", "active", "blocked", "implementing"
            ),
            "action-authorization",
        )

    def test_v2_workspace_selection_records_approval_without_claiming_creation(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status["schema_version"] = "implementation-program-status/v2"
        self.fixture.write_json("state/status.json", status)
        selection_approval = self.fixture._bound_record(
            {
                "schema_version": "implementation-approval/v1",
                "event_id": "ARCHIVE-WORKSPACE-SELECTION",
                "type": "workspace-selection-approval",
                "decision": "approved",
                "scope": ["select the bound implementation workspace"],
            }
        )
        write_json_lines(
            self.fixture.approvals_path,
            [*self.fixture.approvals(), selection_approval],
        )
        write_json_lines(self.fixture.authorizations_path, [])
        selection = AUTHORITY.WorkspaceSelection(
            selected_at="2026-08-08T12:00:00Z",
            observation=self.fixture.observation,
            approval_event_id="ARCHIVE-WORKSPACE-SELECTION",
            action_authorization_id=None,
            authority_kind="approval-event",
        )

        AUTHORITY.select_workspace(
            self.fixture.root,
            selection,
            sha256_file(self.fixture.workspace_path),
        )

        workspace = self.fixture.load_json("state/workspace.json")
        self.assertEqual(workspace["schema_version"], "implementation-workspace/v2")
        self.assertEqual(
            workspace["selection_authority"],
            {
                "kind": "approval-event",
                "event_id": "ARCHIVE-WORKSPACE-SELECTION",
            },
        )
        self.assertNotIn("action_authorization_id", workspace)

        workspace["selection_authority"]["event_id"] = ""
        self.assertIn(
            "v2 workspace selection authority is invalid",
            AUTHORITY.validate_workspace_selection(
                workspace,
                self.fixture.observation,
            ),
        )

    def test_closure_transition_requires_exact_reconciliation_and_packet(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status.update(current_increment_state="accepted", pending_exact_file_plan_sha256=None, approved_exact_file_plan_sha256=self.fixture.plan_sha256)
        self.fixture.write_json("state/status.json", status)
        request = AUTHORITY.TransitionRequest(
            expected_status_sha256=sha256_file(self.fixture.status_path),
            expected_state_sequence=1,
            target_program_state="awaiting-closure-approval",
            target_increment_id="archive-index",
            target_increment_state="accepted",
            transition_event_id="ARCHIVE-CLOSURE-PREPARATION",
            action_authorization_id="ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
            evidence={"action_scope": "implement the bound archive index plan"},
        )
        with self.assertRaisesRegex(ValueError, "closure"):
            AUTHORITY.apply_state_transition(self.fixture.root, request, self.fixture.observation)

    def test_approved_plan_transition_is_applied_atomically(self) -> None:
        prior_sha256 = sha256_file(self.fixture.status_path)
        request = AUTHORITY.TransitionRequest(
            expected_status_sha256=prior_sha256,
            expected_state_sequence=1,
            target_program_state="active",
            target_increment_id="archive-index",
            target_increment_state="authorized",
            transition_event_id="ARCHIVE-PLAN-APPROVAL",
            action_authorization_id="ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
            evidence={"action_scope": "implement the bound archive index plan"},
        )
        receipt = AUTHORITY.apply_state_transition(
            self.fixture.root, request, self.fixture.observation
        )
        self.assertEqual(receipt.state_sequence, 2)
        self.assertEqual(receipt.increment_state, "authorized")
        status = self.fixture.load_json("state/status.json")
        self.assertEqual(status["previous_state"]["status_sha256"], prior_sha256)
        self.assertEqual(
            status["approved_exact_file_plan_sha256"], self.fixture.plan_sha256
        )
        self.assertIsNone(status["pending_exact_file_plan_sha256"])

    def test_workspace_selection_requires_exact_approval_and_action(self) -> None:
        selection_approval = self.fixture._bound_record(
            {
                "schema_version": "implementation-approval/v1",
                "event_id": "ARCHIVE-WORKSPACE-SELECTION",
                "type": "workspace-selection-approval",
                "decision": "approved",
                "scope": ["select the bound implementation workspace"],
            }
        )
        selection_authorization = self.fixture._bound_record(
            {
                "schema_version": "implementation-action-authorization/v1",
                "authorization_id": "ARCHIVE-WORKSPACE-AUTHORIZATION",
                "decision": "authorized",
                "actions": ["create-workspace"],
                "scope": ["select the bound implementation workspace"],
                "constraints": [],
                "excluded": ["modify-external-state"],
            }
        )
        selection = AUTHORITY.WorkspaceSelection(
            selected_at="2026-08-08T12:00:00Z",
            observation=self.fixture.observation,
            approval_event_id="ARCHIVE-WORKSPACE-SELECTION",
            action_authorization_id="ARCHIVE-WORKSPACE-AUTHORIZATION",
        )
        previous_sha256 = sha256_file(self.fixture.workspace_path)
        with self.assertRaisesRegex(ValueError, "approved event"):
            AUTHORITY.select_workspace(
                self.fixture.root, selection, previous_sha256
            )

        write_json_lines(
            self.fixture.approvals_path,
            [*self.fixture.approvals(), selection_approval],
        )
        write_json_lines(
            self.fixture.authorizations_path,
            [*self.fixture.authorizations(), selection_authorization],
        )
        receipt = AUTHORITY.select_workspace(
            self.fixture.root, selection, previous_sha256
        )
        self.assertEqual(receipt.prior_sha256, previous_sha256)
        workspace = self.fixture.load_json("state/workspace.json")
        self.assertEqual(workspace["selected_at"], selection.selected_at)
        self.assertEqual(workspace["prior_workspace_sha256"], previous_sha256)
        self.assertEqual(
            workspace["implementation_workspace"]["path"], str(self.fixture.root)
        )

    def test_full_diff_acceptance_requires_verification_and_packet(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status.update(
            current_increment_state="verified",
            approval_mode="approval:full-diff",
            approved_exact_file_plan_sha256=self.fixture.plan_sha256,
            pending_exact_file_plan_sha256=None,
        )
        status.pop("verification_binding", None)
        decision = AUTHORITY.evaluate_increment_transition(
            status,
            "accepted",
            packet_sha256=self.fixture.packet_sha256,
            conversation_suitable=True,
        )
        self.assertFalse(decision.allowed)
        self.assertIn("fresh verification", decision.issues)

        status["verification_binding"] = {
            "state_sequence": 1,
            "review_packet_sha256": self.fixture.packet_sha256,
            "unresolved_material_findings": 0,
        }
        decision = AUTHORITY.evaluate_increment_transition(
            status,
            "accepted",
            packet_sha256=self.fixture.packet_sha256,
            conversation_suitable=True,
        )
        self.assertTrue(decision.allowed, decision.issues)

        status.update(
            current_increment_state="awaiting-diff-approval",
            approval_mode="approval:standard",
        )
        status.pop("verification_binding")
        decision = AUTHORITY.evaluate_increment_transition(
            status,
            "accepted",
            packet_sha256=self.fixture.packet_sha256,
            conversation_suitable=True,
        )
        self.assertFalse(decision.allowed)
        self.assertIn("fresh verification", decision.issues)

        status["verification_binding"] = {
            "verified_state_sequence": 1,
            "review_packet_sha256": self.fixture.packet_sha256,
            "unresolved_material_findings": 0,
        }
        decision = AUTHORITY.evaluate_increment_transition(
            status,
            "accepted",
            packet_sha256=self.fixture.packet_sha256,
            conversation_suitable=True,
        )
        self.assertTrue(decision.allowed, decision.issues)

    def test_program_only_closure_transition_requires_exact_readiness_bindings(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status.update(
            current_increment_state="accepted",
            approved_exact_file_plan_sha256=self.fixture.plan_sha256,
            pending_exact_file_plan_sha256=None,
        )
        self.fixture.write_json("state/status.json", status)
        request = AUTHORITY.TransitionRequest(
            expected_status_sha256=sha256_file(self.fixture.status_path),
            expected_state_sequence=1,
            target_program_state="awaiting-closure-approval",
            target_increment_id="archive-index",
            target_increment_state="accepted",
            transition_event_id="ARCHIVE-CLOSURE-PREPARATION",
            action_authorization_id="ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
            evidence={"action_scope": "implement the bound archive index plan"},
        )
        with self.assertRaisesRegex(ValueError, "closure"):
            AUTHORITY.apply_state_transition(
                self.fixture.root, request, self.fixture.observation
            )

        reconciliation_path = self.fixture.root / "closure/reconciliation.json"
        closure_packet_path = self.fixture.root / "closure/program-closure-packet.md"
        write_json(reconciliation_path, {"schema_version": "implementation-closure-reconciliation/v1"})
        closure_packet_path.write_text("# Program closure packet\n", encoding="utf-8")
        self.fixture.manifest["logical_roles"].update(
            closure_reconciliation="closure/reconciliation.json",
            closure_packet="closure/program-closure-packet.md",
        )
        write_json(self.fixture.manifest_path, self.fixture.manifest)
        status = self.fixture.load_json("state/status.json")
        status["closure_binding"] = {
            "final_increment_id": "archive-index",
            "reconciliation_path": "closure/reconciliation.json",
            "reconciliation_sha256": sha256_file(reconciliation_path),
            "closure_packet_path": "closure/program-closure-packet.md",
            "closure_packet_sha256": sha256_file(closure_packet_path),
            "readiness_validated": True,
            "unresolved_requirements": 0,
            "unresolved_amendments": 0,
            "unowned_deferrals": 0,
            "unresolved_material_findings": 0,
        }
        self.fixture.write_json("state/status.json", status)
        request = AUTHORITY.TransitionRequest(
            **{
                **request.__dict__,
                "expected_status_sha256": sha256_file(self.fixture.status_path),
            }
        )
        receipt = AUTHORITY.apply_state_transition(
            self.fixture.root, request, self.fixture.observation
        )
        self.assertEqual(receipt.program_state, "awaiting-closure-approval")
        self.assertEqual(receipt.increment_state, "accepted")

    def test_program_closure_requires_one_exact_digest_bound_approval(self) -> None:
        reconciliation_path = self.fixture.root / "closure/reconciliation.json"
        closure_packet_path = self.fixture.root / "closure/program-closure-packet.md"
        write_json(reconciliation_path, {"schema_version": "implementation-closure-reconciliation/v1"})
        closure_packet_path.parent.mkdir(parents=True, exist_ok=True)
        closure_packet_path.write_text("# Program closure packet\n", encoding="utf-8")
        self.fixture.manifest["logical_roles"].update(
            closure_reconciliation="closure/reconciliation.json",
            closure_packet="closure/program-closure-packet.md",
        )
        write_json(self.fixture.manifest_path, self.fixture.manifest)
        status = self.fixture.load_json("state/status.json")
        status.update(
            program_state="awaiting-closure-approval",
            current_increment_state="accepted",
            approved_exact_file_plan_sha256=self.fixture.plan_sha256,
            pending_exact_file_plan_sha256=None,
            closure_binding={
                "final_increment_id": "archive-index",
                "reconciliation_path": "closure/reconciliation.json",
                "reconciliation_sha256": sha256_file(reconciliation_path),
                "closure_packet_path": "closure/program-closure-packet.md",
                "closure_packet_sha256": sha256_file(closure_packet_path),
                "readiness_validated": True,
                "unresolved_requirements": 0,
                "unresolved_amendments": 0,
                "unowned_deferrals": 0,
                "unresolved_material_findings": 0,
            },
        )
        self.fixture.write_json("state/status.json", status)
        request = AUTHORITY.TransitionRequest(
            expected_status_sha256=sha256_file(self.fixture.status_path),
            expected_state_sequence=1,
            target_program_state="closed",
            target_increment_id="archive-index",
            target_increment_state="accepted",
            transition_event_id="ARCHIVE-CLOSURE-APPROVAL",
            action_authorization_id="ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
            evidence={"action_scope": "implement the bound archive index plan"},
        )
        with self.assertRaisesRegex(ValueError, "approved event"):
            AUTHORITY.apply_state_transition(
                self.fixture.root, request, self.fixture.observation
            )

        approval = self.fixture._bound_record(
            {
                "schema_version": "implementation-approval/v1",
                "event_id": "ARCHIVE-CLOSURE-APPROVAL",
                "type": "program-closure-approval",
                "decision": "approved",
                "scope": ["close the exact reconciled portable archive program"],
                "closure_reconciliation_sha256": sha256_file(reconciliation_path),
                "closure_packet_sha256": sha256_file(closure_packet_path),
            }
        )
        stale_approval = copy.deepcopy(approval)
        stale_approval["closure_reconciliation_sha256"] = "0" * 64
        write_json_lines(
            self.fixture.approvals_path,
            [*self.fixture.approvals(), stale_approval],
        )
        with self.assertRaisesRegex(ValueError, "approved event"):
            AUTHORITY.apply_state_transition(
                self.fixture.root, request, self.fixture.observation
            )
        write_json_lines(self.fixture.approvals_path, [*self.fixture.approvals(), approval])
        receipt = AUTHORITY.apply_state_transition(
            self.fixture.root, request, self.fixture.observation
        )
        self.assertEqual(receipt.program_state, "closed")

    def test_one_increment_modes_never_continue_automatically(self) -> None:
        for mode in (
            "approval:standard",
            "approval:pre-approve",
            "approval:full-increment",
            "approval:full-diff",
            "approval:full",
        ):
            with self.subTest(mode=mode):
                self.assertFalse(
                    AUTHORITY.may_start_next_increment(
                        mode, renewed_user_authority=False, conversation_suitable=True
                    )
                )
    def test_cli_returns_zero_one_and_two_deterministically(self) -> None:
        common = [
            "validate-state",
            str(self.fixture.root),
            "--repository",
            str(self.fixture.root),
            "--branch",
            "archive-maintenance",
            "--base",
            BASE_COMMIT,
            "--head",
            HEAD_COMMIT,
        ]
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(AUTHORITY.main(common), 0)
        self.assertEqual(output.getvalue(), "State authority validation passed\n")

        invalid = [*common]
        invalid[-1] = "d" * 40
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(AUTHORITY.main(invalid), 1)
        issue_lines = output.getvalue().splitlines()
        self.assertEqual(issue_lines, sorted(issue_lines))

        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(AUTHORITY.main(["validate-state"]), 2)
        self.assertIn("usage:", output.getvalue())

        request_path = self.fixture.root / "action-request.json"
        write_json(request_path, self.fixture.action_binding().__dict__)
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                AUTHORITY.main(
                    [
                        "check-action",
                        str(self.fixture.root),
                        "--request",
                        str(request_path),
                    ]
                ),
                0,
            )
        self.assertEqual(
            output.getvalue(),
            "Authorized by ARCHIVE-IMPLEMENTATION-AUTHORIZATION\n",
        )

        for command in ("check-action", "select-workspace", "transition-state"):
            with self.subTest(command=command):
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(AUTHORITY.main([command]), 2)
                self.assertIn("usage:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
