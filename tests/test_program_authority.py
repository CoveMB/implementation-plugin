import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path, PurePosixPath
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPOSITORY_ROOT
    / "skills"
    / "implementing-staged-plans"
    / "scripts"
    / "program_authority.py"
)
SPEC = importlib.util.spec_from_file_location("program_authority", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load program authority module from {MODULE_PATH}")
AUTHORITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUTHORITY)
PILOT_ROOT = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "program-authority"
    / "portable-archive-program"
)
CURRENT_PROGRAM_ROOT = REPOSITORY_ROOT / "implementation-programs" / "ISP-001"


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class ProgramAuthorityFixture:
    def __init__(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source_bytes = b"# Archive Plan\n\n- Verify every stored checksum.\n"
        self._write_valid_program()

    def close(self) -> None:
        self.temporary_directory.cleanup()

    def path(self, relative_path: str) -> Path:
        return self.root / relative_path

    def write_bytes(self, relative_path: str, value: bytes) -> Path:
        path = self.path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return path

    def write_text(self, relative_path: str, value: str) -> Path:
        return self.write_bytes(relative_path, value.encode("utf-8"))

    def write_json(self, relative_path: str, value: object) -> Path:
        return self.write_text(
            relative_path, json.dumps(value, indent=2, sort_keys=True) + "\n"
        )

    def load_json(self, relative_path: str) -> dict[str, object]:
        return json.loads(self.path(relative_path).read_text(encoding="utf-8"))

    def mutate_json(self, relative_path: str, mutator) -> None:
        value = self.load_json(relative_path)
        mutator(value)
        self.write_json(relative_path, value)

    def _write_valid_program(self) -> None:
        source_path = self.write_bytes("source/implementation-plan.md", self.source_bytes)
        source_sha256 = digest_bytes(self.source_bytes)
        self.write_json(
            "source/source-metadata.json",
            {
                "schema_version": "implementation-source-metadata/v1",
                "source_id": "ARCHIVE-SOURCE",
                "snapshot_path": "source/implementation-plan.md",
                "sha256": source_sha256,
                "byte_count": len(self.source_bytes),
                "line_count": len(self.source_bytes.splitlines(keepends=True)),
                "immutable": True,
            },
        )
        program_path = self.write_text(
            "program/implementation-program.md", "# Portable Archive Program\n"
        )
        source_lines = self.source_bytes.splitlines(keepends=True)
        source_units = []
        for line_number, line in enumerate(source_lines, start=1):
            requirement = line_number == 3
            unit = {
                "id": f"SOURCE-UNIT-LINE-{line_number}",
                "start_line": line_number,
                "end_line": line_number,
                "source_text_sha256": digest_bytes(line),
                "classification": "requirement" if requirement else "context",
                "requirement_ids": ["INTEGRITY-VERIFY-CHECKSUMS"] if requirement else [],
            }
            if not requirement:
                unit["context_rationale"] = "Heading or structural separation."
            source_units.append(unit)
        atomic_requirements = [
            {
                "id": "INTEGRITY-VERIFY-CHECKSUMS",
                "group_id": "INTEGRITY",
                "source_unit_ids": ["SOURCE-UNIT-LINE-3"],
                "source_locator": "Archive Plan, line 3",
                "normalized_requirement": "Verify every stored checksum.",
                "acceptance_criteria": [
                    "A corrupted stored object is rejected by checksum verification."
                ],
                "assigned_parts": ["Archive integrity"],
                "assigned_tasks": ["Verify stored objects"],
                "assigned_increments": ["Integrity foundation"],
                "current_disposition": "allocated",
                "decision_references": [],
                "implementation_evidence": [],
                "verification_evidence": [],
            }
        ]
        semantic_digest = AUTHORITY.compute_semantic_requirements_digest(
            atomic_requirements
        )
        traceability = {
            "schema_version": "implementation-traceability/v2",
            "program_id": "ARCHIVE-PROGRAM",
            "program_revision": 1,
            "source_id": "ARCHIVE-SOURCE",
            "source_sha256": source_sha256,
            "coverage_assertion": {
                "status": "complete",
                "machine_complete": True,
                "source_line_count": len(source_lines),
                "semantic_requirements_sha256": semantic_digest,
                "approval_event_id": "ARCHIVE-APPROVAL",
            },
            "source_units": source_units,
            "requirement_groups": [{"id": "INTEGRITY", "title": "Archive integrity"}],
            "atomic_requirements": atomic_requirements,
        }
        traceability_path = self.write_json("program/traceability.json", traceability)
        program_sha256 = AUTHORITY.sha256_file(program_path)
        traceability_sha256 = AUTHORITY.sha256_file(traceability_path)
        manifest = {
            "schema_version": "implementation-program-manifest/v1",
            "program_id": "ARCHIVE-PROGRAM",
            "program_revision": 1,
            "approval_mode": "approval:standard",
            "logical_roles": {
                "canonical_source_snapshot": "source/implementation-plan.md",
                "source_metadata": "source/source-metadata.json",
                "approved_program": "program/implementation-program.md",
                "traceability": "program/traceability.json",
                "approvals": "state/approvals.jsonl",
            },
            "source_binding": {
                "source_id": "ARCHIVE-SOURCE",
                "sha256": source_sha256,
            },
            "program_binding": {
                "path": "program/implementation-program.md",
                "sha256": program_sha256,
                "traceability_path": "program/traceability.json",
                "traceability_sha256": traceability_sha256,
                "machine_complete_traceability": True,
            },
        }
        self.write_json("manifest.json", manifest)
        self.write_approval()
        self.assert_source_path = source_path

    def write_approval(self, **overrides: object) -> None:
        manifest = self.load_json("manifest.json")
        traceability = self.load_json("program/traceability.json")
        event = {
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
            **overrides,
        }
        self.write_text("state/approvals.jsonl", json.dumps(event, sort_keys=True) + "\n")

    def configure_new_program_proposal(self) -> None:
        """Convert the approved legacy fixture into a complete unapproved v2 proposal."""
        manifest = self.load_json("manifest.json")
        traceability = self.load_json("program/traceability.json")
        manifest.update(
            schema_version="implementation-program-manifest/v2",
            increment_storage={
                "schema_version": "implementation-increment-storage/v1",
                "root": "increments",
                "brief_filename": "brief.md",
                "exact_file_plan_filename": "exact-file-plan.md",
                "execution_baseline_filename": "execution-baseline.json",
                "review_evidence_filename": "review-evidence.json",
                "review_packet_filename": "review-packet.md",
                "handoff_filename": "handoff.md",
            },
            closure_storage={
                "schema_version": "implementation-closure-storage/v1",
                "root": "closure",
                "reconciliation_filename": "reconciliation.json",
                "packet_filename": "closure-packet.md",
            },
        )
        manifest["logical_roles"].update(
            action_authorizations="state/action-authorizations.jsonl",
            increment_grants="state/increment-grants.jsonl",
            rollovers="state/rollovers.jsonl",
            block_resolutions="state/block-resolutions.jsonl",
            workspace="state/workspace.json",
            status="state/status.json",
        )
        self.write_json("manifest.json", manifest)
        for relative_path in (
            "state/approvals.jsonl",
            "state/action-authorizations.jsonl",
            "state/increment-grants.jsonl",
            "state/rollovers.jsonl",
            "state/block-resolutions.jsonl",
        ):
            self.write_text(relative_path, "")
        self.write_json(
            "state/workspace.json",
            {
                "schema_version": "implementation-workspace-proposal/v1",
                "program_id": manifest["program_id"],
                "program_revision": manifest["program_revision"],
                "repository": {"identity": "portable-archive"},
                "implementation_workspace": {
                    "path": "/portable/archive",
                    "branch": "archive-maintenance",
                    "base_commit": "b" * 40,
                    "head_commit_at_selection": "a" * 40,
                },
                "pre_existing_work_at_selection": {
                    "staged_paths": [],
                    "modified_paths": [],
                    "untracked_paths": [],
                    "conflicted_paths": [],
                    "active_git_operation": None,
                },
            },
        )
        self.write_json(
            "state/status.json",
            {
                "schema_version": "implementation-program-status/v2",
                "program_id": manifest["program_id"],
                "program_revision": manifest["program_revision"],
                "state_sequence": 0,
                "program_state": "awaiting-program-approval",
                "current_increment_id": "ARCHIVE-INDEX",
                "current_increment_state": "not-started",
                "approval_mode": manifest["approval_mode"],
                "source_binding": dict(manifest["source_binding"]),
                "program_binding": {
                    "sha256": manifest["program_binding"]["sha256"],
                    "semantic_requirements_sha256": traceability["coverage_assertion"][
                        "semantic_requirements_sha256"
                    ],
                },
            },
        )


class ProgramAuthorityTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ProgramAuthorityFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def assert_issue(self, issues: list[str], expected: str) -> None:
        self.assertTrue(
            any(expected in issue for issue in issues),
            f"Expected issue containing {expected!r}; received {issues!r}",
        )

    def validate(self, allow_incomplete: bool = False) -> list[str]:
        return AUTHORITY.validate_program_authority(
            self.fixture.root, allow_incomplete=allow_incomplete
        )


class TraceabilityCompletenessTests(ProgramAuthorityTestCase):
    def test_valid_complete_partition_passes(self) -> None:
        self.assertEqual(self.validate(), [])

    def test_missing_first_last_or_interior_line_fails(self) -> None:
        for index in (0, 1, 2):
            with self.subTest(index=index):
                fixture = ProgramAuthorityFixture()
                try:
                    traceability = fixture.load_json("program/traceability.json")
                    del traceability["source_units"][index]
                    fixture.write_json("program/traceability.json", traceability)
                    issues = AUTHORITY.validate_program_authority(fixture.root)
                    self.assertTrue(any("partition" in issue for issue in issues), issues)
                finally:
                    fixture.close()

    def test_overlap_reversed_range_changed_digest_and_duplicate_unit_fail(self) -> None:
        mutations = {
            "overlap": lambda units: units[1].update(start_line=1),
            "reversed": lambda units: units[1].update(start_line=3, end_line=2),
            "digest": lambda units: units[1].update(source_text_sha256="0" * 64),
            "duplicate": lambda units: units.append(copy.deepcopy(units[0])),
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label):
                fixture = ProgramAuthorityFixture()
                try:
                    traceability = fixture.load_json("program/traceability.json")
                    mutation(traceability["source_units"])
                    fixture.write_json("program/traceability.json", traceability)
                    self.assertNotEqual(
                        AUTHORITY.validate_program_authority(fixture.root), []
                    )
                finally:
                    fixture.close()

    def test_requirement_without_atomic_record_and_context_without_rationale_fail(self) -> None:
        traceability = self.fixture.load_json("program/traceability.json")
        traceability["atomic_requirements"] = []
        traceability["coverage_assertion"]["semantic_requirements_sha256"] = (
            AUTHORITY.compute_semantic_requirements_digest([])
        )
        self.fixture.write_json("program/traceability.json", traceability)
        self.assert_issue(self.validate(), "atomic requirement")

        self.fixture.close()
        self.fixture = ProgramAuthorityFixture()
        traceability = self.fixture.load_json("program/traceability.json")
        del traceability["source_units"][0]["context_rationale"]
        self.fixture.write_json("program/traceability.json", traceability)
        self.assert_issue(self.validate(), "context_rationale")

    def test_atomic_contract_rejects_context_duplicate_empty_and_invalid_fields(self) -> None:
        mutations = {
            "context source unit": lambda record: record.update(
                source_unit_ids=["SOURCE-UNIT-LINE-1"]
            ),
            "duplicate atomic requirement": None,
            "acceptance_criteria": lambda record: record.update(acceptance_criteria=[]),
            "assigned_parts": lambda record: record.update(assigned_parts=[]),
            "assigned_tasks": lambda record: record.update(assigned_tasks=[]),
            "assigned_increments": lambda record: record.update(assigned_increments=[]),
            "current_disposition": lambda record: record.update(
                current_disposition="unknown"
            ),
        }
        for expected, mutation in mutations.items():
            with self.subTest(expected=expected):
                fixture = ProgramAuthorityFixture()
                try:
                    traceability = fixture.load_json("program/traceability.json")
                    record = traceability["atomic_requirements"][0]
                    if mutation is None:
                        traceability["atomic_requirements"].append(copy.deepcopy(record))
                    else:
                        mutation(record)
                    traceability["coverage_assertion"][
                        "semantic_requirements_sha256"
                    ] = AUTHORITY.compute_semantic_requirements_digest(
                        traceability["atomic_requirements"]
                    )
                    fixture.write_json("program/traceability.json", traceability)
                    issues = AUTHORITY.validate_program_authority(fixture.root)
                    self.assertTrue(any(expected in issue for issue in issues), issues)
                finally:
                    fixture.close()

    def test_incomplete_claim_is_rejected_unless_explicitly_allowed(self) -> None:
        traceability = self.fixture.load_json("program/traceability.json")
        traceability["coverage_assertion"].update(
            status="awaiting-review", machine_complete=False
        )
        self.fixture.write_json("program/traceability.json", traceability)
        self.assert_issue(self.validate(), "machine completeness")
        self.assertEqual(self.validate(allow_incomplete=True), [])


class BindingAndRevisionTests(ProgramAuthorityTestCase):
    def test_missing_escaping_absolute_and_symlink_roles_fail_closed(self) -> None:
        manifest = self.fixture.load_json("manifest.json")
        del manifest["logical_roles"]["source_metadata"]
        self.fixture.write_json("manifest.json", manifest)
        self.assert_issue(self.validate(), "source_metadata")

        for value in ("../outside.json", "/tmp/outside.json"):
            with self.subTest(value=value):
                fixture = ProgramAuthorityFixture()
                try:
                    manifest = fixture.load_json("manifest.json")
                    manifest["logical_roles"]["source_metadata"] = value
                    fixture.write_json("manifest.json", manifest)
                    self.assertNotEqual(
                        AUTHORITY.validate_program_authority(fixture.root), []
                    )
                finally:
                    fixture.close()

        self.fixture.close()
        self.fixture = ProgramAuthorityFixture()
        target = self.fixture.path("source/source-metadata.json")
        linked = self.fixture.path("source/linked-metadata.json")
        linked.symlink_to(target)
        manifest = self.fixture.load_json("manifest.json")
        manifest["logical_roles"]["source_metadata"] = "source/linked-metadata.json"
        self.fixture.write_json("manifest.json", manifest)
        self.assert_issue(self.validate(), "symlink")

    def test_changed_source_metadata_program_and_traceability_binding_fail(self) -> None:
        mutations = (
            lambda fixture: fixture.path("source/implementation-plan.md").write_bytes(
                fixture.source_bytes + b"changed\n"
            ),
            lambda fixture: fixture.mutate_json(
                "source/source-metadata.json",
                lambda value: value.update(byte_count=value["byte_count"] + 1),
            ),
            lambda fixture: fixture.path("program/implementation-program.md").write_text(
                "# Changed Program\n", encoding="utf-8"
            ),
            lambda fixture: fixture.mutate_json(
                "manifest.json",
                lambda value: value["program_binding"].update(
                    traceability_sha256="0" * 64
                ),
            ),
        )
        for mutation in mutations:
            fixture = ProgramAuthorityFixture()
            try:
                mutation(fixture)
                self.assertNotEqual(AUTHORITY.validate_program_authority(fixture.root), [])
            finally:
                fixture.close()

    def test_missing_rejected_stale_and_conflicting_approval_fail(self) -> None:
        self.fixture.path("state/approvals.jsonl").unlink()
        self.assert_issue(self.validate(), "approval")

        for overrides in (
            {"decision": "rejected"},
            {"source_sha256": "0" * 64},
            {"program_sha256": "0" * 64},
            {"semantic_requirements_sha256": "0" * 64},
            {"program_revision": 2},
        ):
            fixture = ProgramAuthorityFixture()
            try:
                fixture.write_approval(**overrides)
                self.assertNotEqual(AUTHORITY.validate_program_authority(fixture.root), [])
            finally:
                fixture.close()

        self.fixture.close()
        self.fixture = ProgramAuthorityFixture()
        approval_path = self.fixture.path("state/approvals.jsonl")
        first = approval_path.read_text(encoding="utf-8")
        event = json.loads(first)
        event["program_sha256"] = "0" * 64
        approval_path.write_text(first + json.dumps(event) + "\n", encoding="utf-8")
        self.assert_issue(self.validate(), "conflicting")

    def test_revision_preserves_prior_evidence_and_requires_current_approval(self) -> None:
        prior_source = self.fixture.write_text("history/source.md", "prior source\n")
        prior_program = self.fixture.write_text("history/program.md", "prior program\n")
        prior_evidence = self.fixture.write_text("history/evidence.md", "accepted\n")
        traceability = self.fixture.load_json("program/traceability.json")
        traceability["revision_history"] = {
            "supersedes_program_revision": 1,
            "prior_source_path": "history/source.md",
            "prior_source_sha256": AUTHORITY.sha256_file(prior_source),
            "prior_program_path": "history/program.md",
            "prior_program_sha256": AUTHORITY.sha256_file(prior_program),
            "prior_evidence": [
                {
                    "path": "history/evidence.md",
                    "sha256": AUTHORITY.sha256_file(prior_evidence),
                }
            ],
        }
        traceability["program_revision"] = 2
        self.fixture.write_json("program/traceability.json", traceability)
        manifest = self.fixture.load_json("manifest.json")
        manifest["program_revision"] = 2
        manifest["program_binding"]["traceability_sha256"] = AUTHORITY.sha256_file(
            self.fixture.path("program/traceability.json")
        )
        self.fixture.write_json("manifest.json", manifest)
        self.assert_issue(self.validate(), "approval")
        self.fixture.write_approval()
        self.assertEqual(self.validate(), [])
        prior_evidence.write_text("mutated\n", encoding="utf-8")
        self.assert_issue(self.validate(), "prior evidence")

    def test_later_revision_without_preservation_record_fails(self) -> None:
        traceability = self.fixture.load_json("program/traceability.json")
        traceability["program_revision"] = 2
        self.fixture.write_json("program/traceability.json", traceability)
        manifest = self.fixture.load_json("manifest.json")
        manifest["program_revision"] = 2
        manifest["program_binding"]["traceability_sha256"] = AUTHORITY.sha256_file(
            self.fixture.path("program/traceability.json")
        )
        self.fixture.write_json("manifest.json", manifest)
        self.fixture.write_approval()

        self.assert_issue(self.validate(), "revision_history")


class ProposalAuthorityAndStorageTests(ProgramAuthorityTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.fixture.configure_new_program_proposal()

    def test_proposal_mode_accepts_complete_unapproved_bundle_only(self) -> None:
        self.assertEqual(
            AUTHORITY.validate_program_authority(
                self.fixture.root,
                validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
            ),
            [],
        )
        approved_issues = AUTHORITY.validate_program_authority(
            self.fixture.root,
            validation_mode=AUTHORITY.APPROVED_VALIDATION_MODE,
        )
        self.assert_issue(approved_issues, "approval")
        unknown_issues = AUTHORITY.validate_program_authority(
            self.fixture.root,
            validation_mode="unknown",
        )
        self.assert_issue(unknown_issues, "validation mode")

    def test_proposal_mode_requires_empty_future_ledgers_and_initial_status(self) -> None:
        ledger_paths = (
            "state/approvals.jsonl",
            "state/action-authorizations.jsonl",
            "state/increment-grants.jsonl",
            "state/rollovers.jsonl",
            "state/block-resolutions.jsonl",
        )
        for relative_path in ledger_paths:
            with self.subTest(relative_path=relative_path):
                fixture = ProgramAuthorityFixture()
                try:
                    fixture.configure_new_program_proposal()
                    fixture.write_text(relative_path, "{}\n")
                    issues = AUTHORITY.validate_program_authority(
                        fixture.root,
                        validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
                    )
                    self.assertTrue(any("must be empty" in issue for issue in issues), issues)
                finally:
                    fixture.close()

        status = self.fixture.load_json("state/status.json")
        status["state_sequence"] = 1
        status["program_state"] = "active"
        status["current_increment_state"] = "preparing"
        self.fixture.write_json("state/status.json", status)
        issues = AUTHORITY.validate_program_authority(
            self.fixture.root,
            validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
        )
        self.assert_issue(issues, "state_sequence")
        self.assert_issue(issues, "awaiting-program-approval")
        self.assert_issue(issues, "not-started")

    def test_new_manifest_rejects_mutable_and_duplicate_closure_ownership(self) -> None:
        manifest = self.fixture.load_json("manifest.json")
        manifest["program_status"] = {"program_state": "active"}
        manifest["current_increment"] = {"increment_id": "ARCHIVE-INDEX"}
        manifest["logical_roles"]["closure_reconciliation"] = (
            "closure/reconciliation.json"
        )
        manifest["logical_roles"]["closure_packet"] = "closure/closure-packet.md"
        self.fixture.write_json("manifest.json", manifest)
        issues = AUTHORITY.validate_program_authority(
            self.fixture.root,
            validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
        )
        self.assert_issue(issues, "program_status")
        self.assert_issue(issues, "current_increment")
        self.assert_issue(issues, "closure logical roles")

    def test_storage_descriptors_reject_unsafe_or_ambiguous_paths(self) -> None:
        mutations = {
            "missing key": lambda descriptor: descriptor.pop("packet_filename"),
            "absolute root": lambda descriptor: descriptor.update(root="/tmp/closure"),
            "escaping root": lambda descriptor: descriptor.update(root="../closure"),
            "separator filename": lambda descriptor: descriptor.update(
                packet_filename="nested/packet.md"
            ),
            "duplicate path": lambda descriptor: descriptor.update(
                packet_filename=descriptor["reconciliation_filename"]
            ),
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label):
                fixture = ProgramAuthorityFixture()
                try:
                    fixture.configure_new_program_proposal()
                    manifest = fixture.load_json("manifest.json")
                    mutation(manifest["closure_storage"])
                    fixture.write_json("manifest.json", manifest)
                    issues = AUTHORITY.validate_program_authority(
                        fixture.root,
                        validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
                    )
                    self.assertNotEqual(issues, [])
                finally:
                    fixture.close()

        for descriptor_name, field, value in (
            ("increment_storage", "brief_filename", "nested/brief.md"),
            ("increment_storage", "root", "/tmp/increments"),
            ("closure_storage", "root", "nested//closure"),
        ):
            with self.subTest(descriptor=descriptor_name, field=field, value=value):
                fixture = ProgramAuthorityFixture()
                try:
                    fixture.configure_new_program_proposal()
                    manifest = fixture.load_json("manifest.json")
                    manifest[descriptor_name][field] = value
                    fixture.write_json("manifest.json", manifest)
                    issues = AUTHORITY.validate_program_authority(
                        fixture.root,
                        validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
                    )
                    self.assertNotEqual(issues, [])
                finally:
                    fixture.close()

    def test_malformed_logical_role_is_reported_without_an_exception(self) -> None:
        manifest = self.fixture.load_json("manifest.json")
        manifest["logical_roles"]["status"] = {}
        self.fixture.write_json("manifest.json", manifest)
        issues = AUTHORITY.validate_program_authority(
            self.fixture.root,
            validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
        )
        self.assert_issue(issues, "status")

    def test_storage_rejects_symlinked_ancestors_and_non_regular_entries(self) -> None:
        outside = self.fixture.path("outside")
        outside.mkdir()
        self.fixture.path("closure").symlink_to(outside, target_is_directory=True)
        issues = AUTHORITY.validate_program_authority(
            self.fixture.root,
            validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
        )
        self.assert_issue(issues, "symlink")

        self.fixture.path("closure").unlink()
        self.fixture.path("closure/reconciliation.json").mkdir(parents=True)
        issues = AUTHORITY.validate_program_authority(
            self.fixture.root,
            validation_mode=AUTHORITY.PROPOSAL_VALIDATION_MODE,
        )
        self.assert_issue(issues, "regular file")


class SourceCaptureAndCliTests(ProgramAuthorityTestCase):
    def capture(self, source_path: Path | None = None, **overrides):
        input_path = source_path or self.fixture.write_bytes("input.bin", b"one\ntwo\n")
        expected = digest_bytes(input_path.read_bytes())
        values = {
            "source_path": input_path,
            "program_root": self.fixture.root,
            "snapshot_path": PurePosixPath("capture/source.bin"),
            "metadata_path": PurePosixPath("capture/source-metadata.json"),
            "source_id": "CAPTURED-SOURCE",
            "expected_sha256": expected,
            "access_method": "local-file",
        }
        values.update(overrides)
        self.fixture.path("capture").mkdir(exist_ok=True)
        return AUTHORITY.capture_source(**values)

    def test_capture_preserves_exact_bytes_and_writes_counts_and_digest(self) -> None:
        source = self.fixture.write_bytes("input.bin", b"one\r\ntwo\nlast")
        record = self.capture(source)
        self.assertEqual(self.fixture.path(record.snapshot_path).read_bytes(), source.read_bytes())
        metadata = self.fixture.load_json(record.metadata_path)
        self.assertEqual(metadata["sha256"], digest_bytes(source.read_bytes()))
        self.assertEqual(metadata["byte_count"], len(source.read_bytes()))
        self.assertEqual(metadata["line_count"], 3)
        with self.assertRaises(Exception):
            record.source_id = "changed"

    def test_capture_rejects_wrong_digest_existing_targets_and_path_escape(self) -> None:
        with self.assertRaises(ValueError):
            self.capture(expected_sha256="0" * 64)
        self.capture()
        with self.assertRaises(FileExistsError):
            self.capture()
        with self.assertRaises(ValueError):
            self.capture(snapshot_path=PurePosixPath("../escape.bin"))

    def test_capture_rejects_source_and_destination_parent_symlinks(self) -> None:
        source = self.fixture.write_bytes("real.bin", b"source\n")
        linked_source = self.fixture.path("linked.bin")
        linked_source.symlink_to(source)
        with self.assertRaises(ValueError):
            self.capture(linked_source)

        real_parent = self.fixture.path("real-capture")
        real_parent.mkdir()
        linked_parent = self.fixture.path("linked-capture")
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.capture(
                source,
                snapshot_path=PurePosixPath("linked-capture/source.bin"),
                metadata_path=PurePosixPath("linked-capture/metadata.json"),
            )

    def test_capture_fails_closed_when_hard_links_are_unsupported(self) -> None:
        source = self.fixture.write_bytes("hard-link-source.bin", b"source\n")
        with patch.object(
            AUTHORITY.os, "link", side_effect=OSError("hard links unsupported")
        ):
            with self.assertRaises(OSError):
                self.capture(source)

        self.assertFalse(self.fixture.path("capture/source.bin").exists())
        self.assertFalse(self.fixture.path("capture/source-metadata.json").exists())

    def test_existing_metadata_blocks_capture_before_snapshot_creation(self) -> None:
        source = self.fixture.write_bytes("metadata-source.bin", b"source\n")
        self.fixture.path("capture").mkdir(exist_ok=True)
        self.fixture.write_text("capture/source-metadata.json", "preserve\n")

        with self.assertRaises(FileExistsError):
            self.capture(source)

        self.assertFalse(self.fixture.path("capture/source.bin").exists())
        self.assertEqual(
            self.fixture.path("capture/source-metadata.json").read_text(
                encoding="utf-8"
            ),
            "preserve\n",
        )

    def test_cli_returns_zero_one_two_and_sorts_issues(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = AUTHORITY.main(["validate-program", str(self.fixture.root)])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), "Program authority validation passed\n")

        self.fixture.path("source/implementation-plan.md").write_bytes(b"changed\n")
        output = io.StringIO()
        with redirect_stdout(output):
            result = AUTHORITY.main(["validate-program", str(self.fixture.root)])
        self.assertEqual(result, 1)
        lines = output.getvalue().splitlines()
        self.assertEqual(lines, sorted(lines))

        output = io.StringIO()
        with redirect_stdout(output):
            result = AUTHORITY.main(["unknown-command"])
        self.assertEqual(result, 2)
        self.assertIn("usage:", output.getvalue())


class LargePilotTests(unittest.TestCase):
    def copy_pilot(self) -> tempfile.TemporaryDirectory:
        temporary_directory = tempfile.TemporaryDirectory()
        shutil.copytree(PILOT_ROOT, Path(temporary_directory.name), dirs_exist_ok=True)
        return temporary_directory

    def test_neutral_pilot_has_twelve_sections_and_forty_eight_requirements(self) -> None:
        source = (PILOT_ROOT / "source/implementation-plan.md").read_text(
            encoding="utf-8"
        )
        traceability = json.loads(
            (PILOT_ROOT / "program/traceability.json").read_text(encoding="utf-8")
        )
        self.assertEqual(sum(line.startswith("## ") for line in source.splitlines()), 12)
        self.assertEqual(len(traceability["atomic_requirements"]), 48)
        self.assertEqual(AUTHORITY.validate_program_authority(PILOT_ROOT), [])

    def test_neutral_pilot_fails_on_one_changed_byte_or_missing_atomic_record(self) -> None:
        temporary_directory = self.copy_pilot()
        try:
            root = Path(temporary_directory.name)
            source_path = root / "source/implementation-plan.md"
            source_path.write_bytes(source_path.read_bytes() + b"x")
            self.assertNotEqual(AUTHORITY.validate_program_authority(root), [])
        finally:
            temporary_directory.cleanup()

        temporary_directory = self.copy_pilot()
        try:
            root = Path(temporary_directory.name)
            traceability_path = root / "program/traceability.json"
            traceability = json.loads(traceability_path.read_text(encoding="utf-8"))
            del traceability["atomic_requirements"][0]
            traceability["coverage_assertion"][
                "semantic_requirements_sha256"
            ] = AUTHORITY.compute_semantic_requirements_digest(
                traceability["atomic_requirements"]
            )
            traceability_path.write_text(
                json.dumps(traceability, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            issues = AUTHORITY.validate_program_authority(root, allow_incomplete=True)
            self.assertTrue(any("atomic requirement" in issue for issue in issues), issues)
        finally:
            temporary_directory.cleanup()

    def test_neutral_pilot_contains_no_roadmap_identifiers(self) -> None:
        pattern = re.compile(r"\b(?:INC-\d{3,}|ISP-\d{3,}|P-\d{3,}|REQ-[A-Z0-9-]+)\b")
        for path in sorted(PILOT_ROOT.rglob("*")):
            if path.is_file():
                self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")), path)


class CurrentProgramTraceabilityTests(unittest.TestCase):
    def test_current_source_atomic_inventory_matches_lifecycle_claim(self) -> None:
        traceability = json.loads(
            (
                CURRENT_PROGRAM_ROOT
                / "program/revisions/revision-2/traceability.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            traceability["schema_version"], "implementation-traceability/v2"
        )
        self.assertEqual(traceability["coverage_assertion"]["source_line_count"], 1362)
        self.assertGreater(len(traceability["atomic_requirements"]), 100)
        coverage = traceability["coverage_assertion"]
        if coverage["machine_complete"]:
            self.assertEqual(coverage["status"], "complete")
            self.assertEqual(coverage["approval_event_id"], "APR-010")
            self.assertEqual(
                AUTHORITY.validate_program_authority(CURRENT_PROGRAM_ROOT), []
            )
        else:
            self.assertEqual(
                coverage["status"], "awaiting-inc-002-diff-approval"
            )
            self.assertIsNone(coverage["approval_event_id"])
            self.assertEqual(
                AUTHORITY.validate_program_authority(
                    CURRENT_PROGRAM_ROOT, allow_incomplete=True
                ),
                [],
            )

    def test_every_normative_or_list_line_is_requirement_classified(self) -> None:
        source_path = (
            CURRENT_PROGRAM_ROOT
            / "source/revisions/SOURCE-002/implementation-plan.md"
        )
        traceability = json.loads(
            (
                CURRENT_PROGRAM_ROOT
                / "program/revisions/revision-2/traceability.json"
            ).read_text(encoding="utf-8")
        )
        classification_by_line = {
            unit["start_line"]: unit["classification"]
            for unit in traceability["source_units"]
            if unit["start_line"] == unit["end_line"]
        }
        normative = re.compile(
            r"\b(?:must|must not|should|should not|shall|required?|requires?|never|"
            r"do not|cannot|may not|only|rejects?|prevents?|enforces?|blocks?|"
            r"authoritative|immutable|approval|authorization|hard stop|fails? closed)\b",
            re.IGNORECASE,
        )
        source_lines = source_path.read_text(encoding="utf-8").splitlines()
        table_header_lines = {
            index + 1
            for index, line in enumerate(source_lines[:-1])
            if line.startswith("|")
            and re.match(r"^\|?\s*:?-{3,}", source_lines[index + 1])
        }
        inside_fence = False
        for line_number, line in enumerate(
            source_lines, start=1
        ):
            if line.startswith("```"):
                inside_fence = not inside_fence
                continue
            stripped = line.lstrip()
            is_list_contract = bool(
                re.match(r"(?:[-*+] |\d+\. )", stripped)
            )
            is_explicit_context = (
                stripped.startswith("#")
                or (line_number <= 7 and stripped.startswith("**"))
                or (stripped.endswith(":") and not is_list_contract)
                or bool(re.match(r"^\|?\s*:?-{3,}", stripped))
                or line_number in table_header_lines
            )
            if (
                not inside_fence
                and not is_explicit_context
                and (is_list_contract or normative.search(line))
            ):
                self.assertEqual(
                    classification_by_line[line_number],
                    "requirement",
                    f"line {line_number}: {line}",
                )


if __name__ == "__main__":
    unittest.main()
