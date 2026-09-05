import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.script_module_support import load_script_module


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "housekeeping_proposal.py"
PROGRAM_FIXTURE = (
    REPOSITORY_ROOT
    / "tests/fixtures/program-authority/portable-archive-program"
)


def load_housekeeping_module():
    if not SCRIPT_PATH.is_file():
        return None
    return load_script_module("housekeeping_proposal", SCRIPT_PATH)


HOUSEKEEPING = load_housekeeping_module()


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


def portable_tree_fingerprint(path: Path) -> str:
    """Independent test oracle for the documented content-tree fingerprint."""
    entries: list[dict[str, object]] = []
    for candidate in [path, *sorted(path.rglob("*"), key=lambda item: item.as_posix())]:
        relative = "." if candidate == path else candidate.relative_to(path).as_posix()
        if candidate.is_symlink():
            kind = "symlink"
            sha256 = None
        elif candidate.is_dir():
            kind = "directory"
            sha256 = None
        else:
            kind = "file"
            sha256 = sha256_file(candidate)
        entries.append({"path": relative, "kind": kind, "sha256": sha256})
    canonical = (
        json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def filesystem_identity(path: Path) -> dict[str, int]:
    metadata = path.lstat()
    return {
        "device_id": metadata.st_dev,
        "inode": metadata.st_ino,
        "owner_user_id": metadata.st_uid,
        "owner_group_id": metadata.st_gid,
        "mode": metadata.st_mode & 0o7777,
        "change_time_ns": metadata.st_ctime_ns,
    }


class ClosedProgramFixture:
    def __init__(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository_root = Path(self.temporary_directory.name) / "repository"
        self.repository_root.mkdir()
        self._git("init", "-b", "archive-maintenance")
        self._git("config", "user.email", "archive@example.invalid")
        self._git("config", "user.name", "Archive Fixture")

        self.program_root = (
            self.repository_root / "implementation-programs/portable-archive"
        )
        shutil.copytree(PROGRAM_FIXTURE, self.program_root)
        self.reconciliation_path = self.program_root / "closure/reconciliation.json"
        self.packet_path = self.program_root / "closure/closure-packet.md"
        write_json(
            self.reconciliation_path,
            {
                "schema_version": "implementation-closure-reconciliation/v1",
                "program_id": "ARCHIVE-PROGRAM",
                "program_revision": 1,
            },
        )
        self.packet_path.parent.mkdir(parents=True, exist_ok=True)
        self.packet_path.write_text(
            "# Portable archive closure packet\n",
            encoding="utf-8",
        )
        self.authorizations_path = (
            self.program_root / "state/action-authorizations.jsonl"
        )
        self.authorizations_path.write_text("", encoding="utf-8")

        manifest_path = self.program_root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["logical_roles"].update(
            status="state/status.json",
            action_authorizations="state/action-authorizations.jsonl",
            closure_reconciliation="closure/reconciliation.json",
            closure_packet="closure/closure-packet.md",
        )
        write_json(manifest_path, manifest)
        traceability = json.loads(
            (self.program_root / "program/traceability.json").read_text(
                encoding="utf-8"
            )
        )
        self.status_path = self.program_root / "state/status.json"
        write_json(
            self.status_path,
            {
                "schema_version": "implementation-program-status/v1",
                "program_id": manifest["program_id"],
                "program_revision": manifest["program_revision"],
                "program_state": "closed",
                "state_sequence": 18,
                "increment_id": "archive-finalization",
                "brief_sha256": "6" * 64,
                "exact_file_plan_sha256": "e" * 64,
                "approval_mode": "approval:standard",
                "workspace": {
                    "path": str(self.repository_root),
                    "branch": "archive-maintenance",
                    "base_commit": "b" * 40,
                    "head_commit": "a" * 40,
                },
                "source_binding": manifest["source_binding"],
                "program_binding": {
                    "sha256": manifest["program_binding"]["sha256"],
                    "semantic_requirements_sha256": traceability[
                        "coverage_assertion"
                    ]["semantic_requirements_sha256"],
                },
                "closure_binding": {
                    "state": "closed",
                    "readiness_validated": True,
                    "reconciliation_path": "closure/reconciliation.json",
                    "reconciliation_sha256": sha256_file(self.reconciliation_path),
                    "closure_packet_path": "closure/closure-packet.md",
                    "closure_packet_sha256": sha256_file(self.packet_path),
                },
            },
        )
        self._git("add", ".")
        self._git("commit", "-m", "fixture: close portable archive program")
        self.resources_root = Path(self.temporary_directory.name) / "resources"
        self.resources_root.mkdir()
        self.quarantine_root = Path(self.temporary_directory.name) / "quarantine"
        self.quarantine_root.mkdir()

    def _git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repository_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def close(self) -> None:
        self.temporary_directory.cleanup()

    def status(self) -> dict[str, object]:
        return json.loads(self.status_path.read_text(encoding="utf-8"))

    def write_status(self, value: dict[str, object]) -> None:
        write_json(self.status_path, value)

    def resource_record(
        self,
        candidate_path: Path,
        *,
        resource_id: str = "evaluation-output",
        resource_kind: str = "temporary-directory",
        ownership: str = "program-created-disposable",
        fingerprint_sha256: str | None = None,
    ) -> dict[str, object]:
        identity = filesystem_identity(candidate_path)
        evidence_path = self.program_root / f"evidence/{resource_id}-creation.json"
        write_json(
            evidence_path,
            {
                "schema_version": "implementation-resource-creation-evidence/v1",
                "resource_id": resource_id,
                "absolute_path": str(candidate_path.absolute()),
                "creation_authorization_id": f"create-{resource_id}",
                "filesystem_identity": identity,
                "result": "created-by-program",
                "accepted": True,
            },
        )
        return {
            "resource_id": resource_id,
            "absolute_path": str(candidate_path.absolute()),
            "resource_kind": resource_kind,
            "ownership_classification": ownership,
            "creation_authorization_id": f"create-{resource_id}",
            "creation_evidence_path": str(evidence_path.relative_to(self.program_root)),
            "creation_evidence_sha256": sha256_file(evidence_path),
            "containment_root": str(self.resources_root.absolute()),
            "filesystem_identity": identity,
            "fingerprint_sha256": (
                fingerprint_sha256
                if fingerprint_sha256 is not None
                else portable_tree_fingerprint(candidate_path)
            ),
            "disposable_after": "program-closure",
            "recovery_deadline": "2026-09-10T00:00:00Z",
        }

    def bind_resource_inventory(
        self, resources: list[dict[str, object]]
    ) -> Path:
        manifest_path = self.program_root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        traceability = json.loads(
            (self.program_root / "program/traceability.json").read_text(
                encoding="utf-8"
            )
        )
        inventory_path = self.program_root / "closure/disposable-resources.json"
        write_json(
            inventory_path,
            {
                "schema_version": "implementation-disposable-resource-inventory/v1",
                "program_id": manifest["program_id"],
                "program_revision": manifest["program_revision"],
                "source_id": manifest["source_binding"]["source_id"],
                "source_sha256": manifest["source_binding"]["sha256"],
                "program_sha256": manifest["program_binding"]["sha256"],
                "semantic_requirements_sha256": traceability[
                    "coverage_assertion"
                ]["semantic_requirements_sha256"],
                "resources": resources,
            },
        )
        manifest["logical_roles"][
            "disposable_resource_inventory"
        ] = "closure/disposable-resources.json"
        write_json(manifest_path, manifest)
        status = self.status()
        status["closure_binding"][
            "disposable_resource_inventory_path"
        ] = "closure/disposable-resources.json"
        status["closure_binding"][
            "disposable_resource_inventory_sha256"
        ] = sha256_file(inventory_path)
        self.write_status(status)
        return inventory_path

    def add_worktree(self, name: str) -> Path:
        worktree = self.resources_root / name
        self._git("worktree", "add", "-b", name, str(worktree))
        return worktree

    def authority_context(self) -> dict[str, object]:
        status = self.status()
        return {
            "program_id": status["program_id"],
            "program_revision": status["program_revision"],
            "source_id": status["source_binding"]["source_id"],
            "source_sha256": status["source_binding"]["sha256"],
            "program_sha256": status["program_binding"]["sha256"],
            "semantic_requirements_sha256": status["program_binding"][
                "semantic_requirements_sha256"
            ],
            "increment_id": status["increment_id"],
            "brief_sha256": status["brief_sha256"],
            "exact_file_plan_sha256": status["exact_file_plan_sha256"],
            "approval_mode": status["approval_mode"],
            "workspace": status["workspace"],
        }

    def write_authority_records(
        self,
        proposal,
        *,
        include_closure_approval: bool = True,
        include_action_authorization: bool = True,
        bind_inventory: bool = True,
    ) -> None:
        context = self.authority_context()
        if include_closure_approval:
            approvals_path = self.program_root / "state/approvals.jsonl"
            existing = approvals_path.read_text(encoding="utf-8")
            closure_record = {
                **context,
                "schema_version": "implementation-approval/v1",
                "type": "program-closure-approval",
                "decision": "approved",
                "event_id": "archive-closure-approval",
                "closure_reconciliation_sha256": proposal.reconciliation_sha256,
                "closure_packet_sha256": proposal.closure_packet_sha256,
            }
            approvals_path.write_text(
                existing + json.dumps(closure_record, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        if include_action_authorization:
            scope = (
                "apply post-closure housekeeping inventory "
                + proposal.candidate_inventory_sha256
            )
            action_record = {
                **context,
                "schema_version": "implementation-action-authorization/v1",
                "authorization_id": "archive-housekeeping-authorization",
                "decision": "authorized",
                "revoked": False,
                "actions": ["destructive-operation"],
                "scope": [scope],
                "closure_reconciliation_sha256": proposal.reconciliation_sha256,
                "closure_packet_sha256": proposal.closure_packet_sha256,
            }
            if bind_inventory:
                action_record.update(
                    candidate_inventory_sha256=proposal.candidate_inventory_sha256,
                    candidate_paths=[
                        candidate.absolute_path for candidate in proposal.candidates
                    ],
                )
            self.authorizations_path.write_text(
                json.dumps(action_record, sort_keys=True) + "\n",
                encoding="utf-8",
            )


@unittest.skipIf(HOUSEKEEPING is None, "housekeeping proposal module is absent")
class ClosedProgramProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ClosedProgramFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_closed_program_without_provenance_returns_empty_dry_run_and_stop(
        self,
    ) -> None:
        proposal = HOUSEKEEPING.build_housekeeping_proposal(
            self.fixture.program_root,
            self.fixture.repository_root,
        )

        self.assertEqual(proposal.mode, "dry-run")
        self.assertEqual(proposal.candidates, ())
        self.assertFalse(proposal.execution_authorized)
        self.assertIn("Stop", proposal.next_action)
        self.assertEqual(
            proposal.candidate_inventory_sha256,
            HOUSEKEEPING.candidate_inventory_sha256(proposal),
        )

    def test_open_program_is_rejected(self) -> None:
        status = self.fixture.status()
        status["program_state"] = "active"
        self.fixture.write_status(status)

        with self.assertRaisesRegex(ValueError, "program is not closed"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
            )


@unittest.skipIf(HOUSEKEEPING is None, "housekeeping proposal module is absent")
class CandidateSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ClosedProgramFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_program_created_temporary_directory_has_recoverable_proposal(self) -> None:
        candidate_path = self.fixture.resources_root / "evaluation-output"
        candidate_path.mkdir()
        (candidate_path / "result.txt").write_text("accepted elsewhere\n", encoding="utf-8")
        self.fixture.bind_resource_inventory(
            [self.fixture.resource_record(candidate_path)]
        )

        proposal = HOUSEKEEPING.build_housekeeping_proposal(
            self.fixture.program_root,
            self.fixture.repository_root,
            self.fixture.quarantine_root,
        )

        self.assertEqual(len(proposal.candidates), 1)
        candidate = proposal.candidates[0]
        self.assertEqual(candidate.absolute_path, str(candidate_path))
        self.assertEqual(candidate.ownership_classification, "program-created-disposable")
        self.assertTrue(candidate.symlink_and_containment.contained)
        self.assertFalse(candidate.symlink_and_containment.any_symlink)
        self.assertEqual(
            candidate.filesystem_identity.inode,
            candidate_path.lstat().st_ino,
        )
        self.assertEqual(candidate.proposed_action.kind, "quarantine-move")
        self.assertEqual(
            Path(candidate.proposed_action.target).parent,
            self.fixture.quarantine_root.resolve(),
        )
        self.assertTrue(candidate.recovery.receipt_required)
        self.assertEqual(proposal.mode, "dry-run")
        self.assertFalse(proposal.execution_authorized)
        self.assertEqual(
            HOUSEKEEPING.validate_housekeeping_proposal(
                proposal,
                self.fixture.program_root,
                self.fixture.repository_root,
            ),
            [],
        )

    def test_absolute_resource_id_cannot_escape_quarantine(self) -> None:
        candidate_path = self.fixture.resources_root / "absolute-id-output"
        candidate_path.mkdir()
        resource = self.fixture.resource_record(
            candidate_path, resource_id="safe-absolute-id"
        )
        evidence_path = self.fixture.program_root / str(
            resource["creation_evidence_path"]
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        resource["resource_id"] = "/private/tmp/escaped-housekeeping"
        evidence["resource_id"] = resource["resource_id"]
        write_json(evidence_path, evidence)
        resource["creation_evidence_sha256"] = sha256_file(evidence_path)
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "portable path component"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_byte_identical_replacement_loses_program_created_identity(self) -> None:
        candidate_path = self.fixture.resources_root / "replaceable-output"
        candidate_path.mkdir()
        self.fixture.bind_resource_inventory(
            [self.fixture.resource_record(candidate_path)]
        )
        original_path = self.fixture.resources_root / "original-program-object"
        candidate_path.rename(original_path)
        candidate_path.mkdir()

        with self.assertRaisesRegex(ValueError, "filesystem identity is stale"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_traversal_resource_id_cannot_escape_quarantine(self) -> None:
        candidate_path = self.fixture.resources_root / "traversal-id-output"
        candidate_path.mkdir()
        resource = self.fixture.resource_record(
            candidate_path, resource_id="safe-traversal-id"
        )
        evidence_path = self.fixture.program_root / str(
            resource["creation_evidence_path"]
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        resource["resource_id"] = "../../escaped-housekeeping"
        evidence["resource_id"] = resource["resource_id"]
        write_json(evidence_path, evidence)
        resource["creation_evidence_sha256"] = sha256_file(evidence_path)
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "portable path component"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_quarantine_root_overlapping_program_evidence_is_rejected(self) -> None:
        candidate_path = self.fixture.resources_root / "unsafe-quarantine-output"
        candidate_path.mkdir()
        self.fixture.bind_resource_inventory(
            [self.fixture.resource_record(candidate_path)]
        )
        protected_quarantine = self.fixture.program_root / "closure/quarantine"
        protected_quarantine.mkdir()

        with self.assertRaisesRegex(ValueError, "quarantine root overlaps protected"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                protected_quarantine,
            )

    def test_user_owned_candidate_is_rejected(self) -> None:
        candidate_path = self.fixture.resources_root / "user-notes"
        candidate_path.mkdir()
        resource = self.fixture.resource_record(
            candidate_path, ownership="user-owned"
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "ownership classification"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_missing_creation_provenance_is_rejected(self) -> None:
        candidate_path = self.fixture.resources_root / "unknown-origin"
        candidate_path.mkdir()
        resource = self.fixture.resource_record(candidate_path)
        del resource["creation_authorization_id"]
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "creation authorization"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_symlink_candidate_is_rejected(self) -> None:
        target = self.fixture.resources_root / "real-output"
        target.mkdir()
        candidate_path = self.fixture.resources_root / "linked-output"
        candidate_path.symlink_to(target, target_is_directory=True)
        resource = self.fixture.resource_record(
            candidate_path,
            fingerprint_sha256="0" * 64,
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "symlink"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_candidate_with_symlink_descendant_is_rejected(self) -> None:
        candidate_path = self.fixture.resources_root / "mixed-output"
        candidate_path.mkdir()
        (candidate_path / "ordinary.txt").write_text("ordinary\n", encoding="utf-8")
        (candidate_path / "linked.txt").symlink_to(candidate_path / "ordinary.txt")
        resource = self.fixture.resource_record(
            candidate_path,
            fingerprint_sha256="0" * 64,
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "symlink"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_closure_evidence_path_is_rejected(self) -> None:
        resource = self.fixture.resource_record(
            self.fixture.packet_path,
            resource_id="closure-packet",
            fingerprint_sha256="0" * 64,
        )
        resource["containment_root"] = str(self.fixture.program_root)
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "protected program or closure evidence"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_stale_inventory_fingerprint_is_rejected(self) -> None:
        candidate_path = self.fixture.resources_root / "stale-output"
        candidate_path.mkdir()
        stale_file = candidate_path / "result.txt"
        stale_file.write_text("closure bytes\n", encoding="utf-8")
        resource = self.fixture.resource_record(candidate_path)
        self.fixture.bind_resource_inventory([resource])
        stale_file.write_text("drifted bytes\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "fingerprint is stale"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_proposal_validation_detects_post_proposal_drift(self) -> None:
        candidate_path = self.fixture.resources_root / "validated-output"
        candidate_path.mkdir()
        self.fixture.bind_resource_inventory(
            [self.fixture.resource_record(candidate_path)]
        )
        proposal = HOUSEKEEPING.build_housekeeping_proposal(
            self.fixture.program_root,
            self.fixture.repository_root,
            self.fixture.quarantine_root,
        )
        (candidate_path / "late-file.txt").write_text("drift\n", encoding="utf-8")

        self.assertEqual(
            HOUSEKEEPING.validate_housekeeping_proposal(
                proposal,
                self.fixture.program_root,
                self.fixture.repository_root,
            ),
            ["proposal inventory is stale"],
        )

    def test_clean_obsolete_worktree_reports_git_state(self) -> None:
        worktree = self.fixture.add_worktree("obsolete-worktree")
        resource = self.fixture.resource_record(
            worktree,
            resource_kind="linked-worktree",
        )
        self.fixture.bind_resource_inventory([resource])

        proposal = HOUSEKEEPING.build_housekeeping_proposal(
            self.fixture.program_root,
            self.fixture.repository_root,
        )

        candidate = proposal.candidates[0]
        self.assertEqual(candidate.proposed_action.kind, "git-worktree-remove")
        self.assertIsNotNone(candidate.worktree_state)
        self.assertFalse(candidate.worktree_state.dirty)
        self.assertFalse(candidate.worktree_state.unique_commits)
        self.assertFalse(candidate.worktree_state.locked)
        self.assertNotIn("--force", candidate.proposed_action.command)

    def test_locked_worktree_is_rejected(self) -> None:
        worktree = self.fixture.add_worktree("locked-worktree")
        self.fixture._git("worktree", "lock", str(worktree))
        resource = self.fixture.resource_record(
            worktree,
            resource_kind="linked-worktree",
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "worktree is locked"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
            )

    def test_current_worktree_is_rejected(self) -> None:
        resource = self.fixture.resource_record(
            self.fixture.repository_root,
            resource_id="current-worktree",
            resource_kind="linked-worktree",
            fingerprint_sha256="0" * 64,
        )
        resource["containment_root"] = str(
            Path(self.fixture.temporary_directory.name).absolute()
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "current worktree root"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
            )

    def test_detached_worktree_is_rejected(self) -> None:
        worktree = self.fixture.resources_root / "detached-worktree"
        self.fixture._git("worktree", "add", "--detach", str(worktree))
        resource = self.fixture.resource_record(
            worktree,
            resource_kind="linked-worktree",
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "detached HEAD"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
            )

    def test_conflicted_worktree_is_rejected_by_conflict_guard(self) -> None:
        conflict_path = self.fixture.repository_root / "conflict.txt"
        conflict_path.write_text("base\n", encoding="utf-8")
        self.fixture._git("add", "conflict.txt")
        self.fixture._git("commit", "-m", "fixture: add conflict base")
        worktree = self.fixture.add_worktree("conflicted-worktree")
        (worktree / "conflict.txt").write_text("candidate\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "conflict.txt"], cwd=worktree, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "fixture: candidate conflict"],
            cwd=worktree,
            check=True,
            capture_output=True,
        )
        conflict_path.write_text("current\n", encoding="utf-8")
        self.fixture._git("add", "conflict.txt")
        self.fixture._git("commit", "-m", "fixture: current conflict")
        merge = subprocess.run(
            ["git", "merge", "archive-maintenance"],
            cwd=worktree,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(merge.returncode, 0)
        resource = self.fixture.resource_record(
            worktree,
            resource_kind="linked-worktree",
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "conflict or active operation"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
            )

    def test_operation_active_worktree_is_rejected_by_operation_guard(self) -> None:
        worktree = self.fixture.add_worktree("operation-worktree")
        (self.fixture.repository_root / "operation.txt").write_text(
            "pending merge\n", encoding="utf-8"
        )
        self.fixture._git("add", "operation.txt")
        self.fixture._git("commit", "-m", "fixture: add operation input")
        merge = subprocess.run(
            ["git", "merge", "--no-commit", "--no-ff", "archive-maintenance"],
            cwd=worktree,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(merge.returncode, 0, merge.stderr)
        resource = self.fixture.resource_record(
            worktree,
            resource_kind="linked-worktree",
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "conflict or active operation"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
            )

    def test_worktree_inspection_does_not_refresh_index_bytes(self) -> None:
        worktree = self.fixture.add_worktree("read-only-worktree")
        resource = self.fixture.resource_record(
            worktree,
            resource_kind="linked-worktree",
        )
        self.fixture.bind_resource_inventory([resource])
        index_result = subprocess.run(
            ["git", "rev-parse", "--git-path", "index"],
            cwd=worktree,
            check=True,
            capture_output=True,
            text=True,
        )
        index_path = Path(index_result.stdout.strip())
        if not index_path.is_absolute():
            index_path = worktree / index_path
        before = (index_path.read_bytes(), index_path.stat().st_mtime_ns)
        tracked_path = (
            worktree / "implementation-programs/portable-archive/manifest.json"
        )
        tracked_metadata = tracked_path.stat()
        os.utime(
            tracked_path,
            ns=(tracked_metadata.st_atime_ns, tracked_metadata.st_mtime_ns + 1_000_000_000),
        )

        HOUSEKEEPING.build_housekeeping_proposal(
            self.fixture.program_root,
            self.fixture.repository_root,
        )

        self.assertEqual(
            (index_path.read_bytes(), index_path.stat().st_mtime_ns),
            before,
        )

    def test_registered_worktree_mislabeled_as_temporary_is_rejected(self) -> None:
        worktree = self.fixture.add_worktree("misclassified-worktree")
        resource = self.fixture.resource_record(worktree)
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "registered worktree must use"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_non_worktree_candidate_with_git_metadata_is_rejected(self) -> None:
        candidate_path = self.fixture.resources_root / "unassessed-repository"
        candidate_path.mkdir()
        subprocess.run(
            ["git", "init", "-b", "temporary-evaluation"],
            cwd=candidate_path,
            check=True,
            capture_output=True,
        )
        self.fixture.bind_resource_inventory(
            [self.fixture.resource_record(candidate_path)]
        )

        with self.assertRaisesRegex(ValueError, "unassessed Git metadata"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_program_created_ignored_cache_is_quarantinable(self) -> None:
        (self.fixture.repository_root / ".gitignore").write_text(
            ".evaluation-cache/\n", encoding="utf-8"
        )
        candidate_path = self.fixture.repository_root / ".evaluation-cache"
        candidate_path.mkdir()
        (candidate_path / "cache.bin").write_bytes(b"cache")
        resource = self.fixture.resource_record(
            candidate_path,
            resource_kind="ignored-cache",
        )
        resource["containment_root"] = str(self.fixture.repository_root)
        self.fixture.bind_resource_inventory([resource])

        proposal = HOUSEKEEPING.build_housekeeping_proposal(
            self.fixture.program_root,
            self.fixture.repository_root,
            self.fixture.quarantine_root,
        )

        self.assertEqual(proposal.candidates[0].resource_kind, "ignored-cache")
        self.assertEqual(proposal.candidates[0].proposed_action.kind, "quarantine-move")

    def test_non_ignored_cache_is_rejected(self) -> None:
        candidate_path = self.fixture.repository_root / ".unignored-cache"
        candidate_path.mkdir()
        resource = self.fixture.resource_record(
            candidate_path,
            resource_kind="ignored-cache",
        )
        resource["containment_root"] = str(self.fixture.repository_root)
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "not currently ignored"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_tracked_cache_is_rejected_even_when_ignore_rule_matches(self) -> None:
        (self.fixture.repository_root / ".gitignore").write_text(
            ".tracked-cache/\n", encoding="utf-8"
        )
        candidate_path = self.fixture.repository_root / ".tracked-cache"
        candidate_path.mkdir()
        (candidate_path / "tracked.bin").write_bytes(b"tracked cache")
        self.fixture._git("add", ".gitignore")
        self.fixture._git("add", "-f", ".tracked-cache/tracked.bin")
        self.fixture._git("commit", "-m", "fixture: track ignored cache")
        resource = self.fixture.resource_record(
            candidate_path,
            resource_kind="ignored-cache",
        )
        resource["containment_root"] = str(self.fixture.repository_root)
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "contains a tracked path"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
                self.fixture.quarantine_root,
            )

    def test_dirty_worktree_is_rejected(self) -> None:
        worktree = self.fixture.add_worktree("dirty-worktree")
        (worktree / "untracked.txt").write_text("preserve me\n", encoding="utf-8")
        resource = self.fixture.resource_record(
            worktree,
            resource_kind="linked-worktree",
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "worktree is dirty"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
            )

    def test_worktree_with_unique_commit_is_rejected(self) -> None:
        worktree = self.fixture.add_worktree("unique-worktree")
        (worktree / "unique.txt").write_text("unique history\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "unique.txt"], cwd=worktree, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "fixture: unique worktree commit"],
            cwd=worktree,
            check=True,
            capture_output=True,
        )
        resource = self.fixture.resource_record(
            worktree,
            resource_kind="linked-worktree",
        )
        self.fixture.bind_resource_inventory([resource])

        with self.assertRaisesRegex(ValueError, "unique commits"):
            HOUSEKEEPING.build_housekeeping_proposal(
                self.fixture.program_root,
                self.fixture.repository_root,
            )


@unittest.skipIf(HOUSEKEEPING is None, "housekeeping proposal module is absent")
class AuthorizationAndCommandLineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ClosedProgramFixture()
        self.candidate_path = self.fixture.resources_root / "authorization-output"
        self.candidate_path.mkdir()
        self.fixture.bind_resource_inventory(
            [self.fixture.resource_record(self.candidate_path)]
        )
        self.proposal = HOUSEKEEPING.build_housekeeping_proposal(
            self.fixture.program_root,
            self.fixture.repository_root,
            self.fixture.quarantine_root,
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def test_closure_approval_alone_never_authorizes_cleanup(self) -> None:
        self.fixture.write_authority_records(
            self.proposal,
            include_action_authorization=False,
        )

        decision = HOUSEKEEPING.check_housekeeping_authorization(
            self.proposal,
            self.fixture.program_root,
            self.fixture.repository_root,
            recovery_evidence="quarantine move receipt and exact reverse path",
        )

        self.assertFalse(decision.authorized)
        self.assertIsNone(decision.authorization_id)
        self.assertIn("Stop", decision.next_action)
        self.assertTrue(self.candidate_path.is_dir())

    def test_authorization_without_exact_inventory_binding_is_rejected(self) -> None:
        self.fixture.write_authority_records(
            self.proposal,
            bind_inventory=False,
        )

        decision = HOUSEKEEPING.check_housekeeping_authorization(
            self.proposal,
            self.fixture.program_root,
            self.fixture.repository_root,
            recovery_evidence="quarantine move receipt and exact reverse path",
        )

        self.assertFalse(decision.authorized)
        self.assertIn("candidate inventory", " ".join(decision.issues))
        self.assertTrue(self.candidate_path.is_dir())

    def test_exact_destructive_authorization_only_authorizes_later_execution(self) -> None:
        self.fixture.write_authority_records(self.proposal)

        decision = HOUSEKEEPING.check_housekeeping_authorization(
            self.proposal,
            self.fixture.program_root,
            self.fixture.repository_root,
            recovery_evidence="quarantine move receipt and exact reverse path",
        )

        self.assertTrue(decision.authorized)
        self.assertEqual(
            decision.authorization_id, "archive-housekeeping-authorization"
        )
        self.assertEqual(
            decision.candidate_inventory_sha256,
            self.proposal.candidate_inventory_sha256,
        )
        self.assertFalse(self.proposal.execution_authorized)
        self.assertIn("Stop", decision.next_action)
        self.assertTrue(self.candidate_path.is_dir())

    def test_revoked_exact_destructive_authorization_is_rejected(self) -> None:
        self.fixture.write_authority_records(self.proposal)
        record = json.loads(
            self.fixture.authorizations_path.read_text(encoding="utf-8")
        )
        record["revoked"] = True
        self.fixture.authorizations_path.write_text(
            json.dumps(record, sort_keys=True) + "\n", encoding="utf-8"
        )

        decision = HOUSEKEEPING.check_housekeeping_authorization(
            self.proposal,
            self.fixture.program_root,
            self.fixture.repository_root,
            recovery_evidence="quarantine move receipt and exact reverse path",
        )

        self.assertFalse(decision.authorized)
        self.assertIn("conflicting exact later-action authorization", " ".join(decision.issues))

    def test_expired_exact_destructive_authorization_is_rejected(self) -> None:
        self.fixture.write_authority_records(self.proposal)
        record = json.loads(
            self.fixture.authorizations_path.read_text(encoding="utf-8")
        )
        record["expires_at"] = "2000-01-01T00:00:00Z"
        self.fixture.authorizations_path.write_text(
            json.dumps(record, sort_keys=True) + "\n", encoding="utf-8"
        )

        decision = HOUSEKEEPING.check_housekeeping_authorization(
            self.proposal,
            self.fixture.program_root,
            self.fixture.repository_root,
            recovery_evidence="quarantine move receipt and exact reverse path",
        )

        self.assertFalse(decision.authorized)
        self.assertIn("exactly one current action authorization", " ".join(decision.issues))

    def test_authorization_rejects_stale_proposal_before_records(self) -> None:
        self.fixture.write_authority_records(self.proposal)
        (self.candidate_path / "late.txt").write_text("drift\n", encoding="utf-8")

        decision = HOUSEKEEPING.check_housekeeping_authorization(
            self.proposal,
            self.fixture.program_root,
            self.fixture.repository_root,
            recovery_evidence="quarantine move receipt and exact reverse path",
        )

        self.assertFalse(decision.authorized)
        self.assertEqual(decision.issues, ("proposal inventory is stale",))

    def test_proposal_round_trip_is_deterministic(self) -> None:
        mapping = HOUSEKEEPING.proposal_to_mapping(self.proposal)

        loaded = HOUSEKEEPING.housekeeping_proposal_from_mapping(mapping)

        self.assertEqual(loaded, self.proposal)
        self.assertEqual(
            HOUSEKEEPING.proposal_to_mapping(loaded),
            mapping,
        )

    def test_cli_has_read_only_proposal_mode_and_no_execute_command(self) -> None:
        empty_fixture = ClosedProgramFixture()
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "propose",
                    "--program-root",
                    str(empty_fixture.program_root),
                    "--repository-root",
                    str(empty_fixture.repository_root),
                ],
                cwd=REPOSITORY_ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                check=False,
                capture_output=True,
                text=True,
            )
            unsupported = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "execute"],
                cwd=REPOSITORY_ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                check=False,
                capture_output=True,
                text=True,
            )
        finally:
            empty_fixture.close()

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["mode"], "dry-run")
        self.assertFalse(output["execution_authorized"])
        self.assertIn("Stop", output["next_action"])
        self.assertNotEqual(unsupported.returncode, 0)

    def test_cli_validates_proposal_and_checks_authorization_without_action(self) -> None:
        self.fixture.write_authority_records(self.proposal)
        proposal_path = Path(self.fixture.temporary_directory.name) / "proposal.json"
        write_json(proposal_path, HOUSEKEEPING.proposal_to_mapping(self.proposal))
        base_arguments = [
            "--proposal",
            str(proposal_path),
            "--program-root",
            str(self.fixture.program_root),
            "--repository-root",
            str(self.fixture.repository_root),
        ]

        validated = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "validate-proposal", *base_arguments],
            cwd=REPOSITORY_ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            check=False,
            capture_output=True,
            text=True,
        )
        authorized = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "check-authorization",
                *base_arguments,
                "--recovery-evidence",
                "quarantine move receipt and exact reverse path",
            ],
            cwd=REPOSITORY_ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertTrue(json.loads(validated.stdout)["valid"])
        self.assertEqual(authorized.returncode, 0, authorized.stderr)
        authorization_output = json.loads(authorized.stdout)
        self.assertTrue(authorization_output["authorized"])
        self.assertIn("Stop", authorization_output["next_action"])
        self.assertTrue(self.candidate_path.is_dir())

class ModulePresenceTests(unittest.TestCase):
    def test_housekeeping_proposal_module_exists(self) -> None:
        self.assertIsNotNone(
            HOUSEKEEPING,
            "housekeeping_proposal.py must provide the approved proposal boundary",
        )


if __name__ == "__main__":
    unittest.main()
