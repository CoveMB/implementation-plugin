import copy
import hashlib
import json
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture,
    _exact_plan_bytes,
    repository_snapshot,
    run_git,
    run_program_discovery,
    write_raw_review_reports,
)
from tests.script_module_support import load_script_module
from tests.test_diff_disposition import DIFF
from tests.test_program_activation import ACTIVATION
from tests.test_program_continuation import CONTINUATION
from tests.test_program_review import REVIEW
from tests.test_program_rollover import ROLLOVER
from tests.test_program_setup import BOOTSTRAP, SETUP


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
AUTHORITY = load_script_module(
    "delete_lifecycle_state_authority", SCRIPT_ROOT / "state_authority.py"
)

SETUP_V2_ROLLOVER_ACTION_FIELDS = (
    "schema_version", "authorization_id", "decision", "actions", "scope",
    "constraints", "excluded", "program_id", "program_revision",
    "source_id", "source_sha256", "program_sha256",
    "semantic_requirements_sha256", "current_increment_id",
    "successor_increment_id", "continuation_domain",
    "continuation_checkpoint_id", "accepted_status_sha256",
    "accepted_status_sequence", "product_result_schema_version",
    "product_result_sha256", "workspace", "submitted_prompt_sha256",
    "setup_activation_decision_id", "setup_activation_decision_sha256",
    "increment_grant_id", "increment_grant_sha256",
    "source_gate_satisfaction",
)


def _fresh_observation(fixture: BootstrapFixture):
    return ACTIVATION.inspect_repository(
        fixture.repository, fixture.head
    ).observation


def _authorized_delete_program_with_successor(
    *, recreate_in_successor=False, third_successor=False
):
    fixture = BootstrapFixture()
    legacy_bytes = b"legacy implementation\n"
    (fixture.repository / "legacy.ts").write_bytes(legacy_bytes)
    run_git(fixture.repository, "add", "legacy.ts")
    run_git(fixture.repository, "commit", "-m", "seed legacy implementation")
    fixture.head = run_git(fixture.repository, "rev-parse", "HEAD")
    workspace = fixture.load_json("state/workspace.json")
    workspace["implementation_workspace"]["base_commit"] = fixture.head
    workspace["implementation_workspace"]["head_commit_at_selection"] = fixture.head
    fixture.write_json("state/workspace.json", workspace)
    if third_successor:
        fixture.configure_successor_chain(
            ("ARCHIVE-INDEX", "ARCHIVE-VERIFY", "ARCHIVE-REPORT")
        )
    else:
        fixture.configure_successors({"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)})
    fixture.configure_delete_setup_v2(path="legacy.ts")
    if recreate_in_successor:
        manifest = fixture.load_json("manifest.json")
        semantics = manifest["setup_semantics"]
        semantics["operation_envelope"]["allocations"].append(
            {
                "kind": "exact-path",
                "path": "legacy.ts",
                "operation": "Create",
                "increment_ids": ["ARCHIVE-VERIFY"],
                "inclusions": ["explicitly recreated successor implementation"],
                "exclusions": [],
                "ownership": "program",
                "protected": False,
                "user_work": False,
                "file_kind": "absent",
                "link_kind": "none",
                "mode": None,
                "collision": "none",
            }
        )
        manifest["setup_semantics_sha256"] = hashlib.sha256(
            json.dumps(
                semantics,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        fixture.write_json("manifest.json", manifest)
    BOOTSTRAP.publish_program_proposal(
        fixture.repository,
        fixture.source_plan,
        fixture.candidate,
        fixture.source_sha256,
    )
    observation = _fresh_observation(fixture)
    activation = ACTIVATION.activate_program(
        fixture.program_root,
        SETUP.adapt_setup_decision(
            fixture.program_root,
            "Yes",
            role="user",
            provenance="direct-user-message",
        ),
        observation,
    )
    intent = SETUP.adapt_increment_start_intent(
        fixture.program_root,
        activation.handoff,
        role="user",
        provenance="direct-user-message",
    )
    ACTIVATION.start_first_increment(fixture.program_root, intent, observation)
    observation = _fresh_observation(fixture)
    prepared = ACTIVATION.prepare_exact_plan(
        fixture.program_root,
        _exact_plan_bytes(fixture.program_root, observation),
        observation,
    )
    ACTIVATION.materialize_exact_plan(
        fixture.program_root, prepared.plan_prompt, observation
    )
    return fixture, legacy_bytes


def _reviewed_delete_program(
    *, recreate_in_successor=False, third_successor=False
):
    fixture, legacy_bytes = _authorized_delete_program_with_successor(
        recreate_in_successor=recreate_in_successor,
        third_successor=third_successor,
    )
    program_root = fixture.program_root
    baseline = json.loads(
        (
            program_root / "increments/ARCHIVE-INDEX/execution-baseline.json"
        ).read_text(encoding="utf-8")
    )
    allocation = baseline["delete_quarantine_bindings"][0]
    with mock.patch.object(
        Path,
        "unlink",
        side_effect=AssertionError("Delete lifecycle must not unlink"),
    ):
        ACTIVATION.advance_execution_state(
            program_root, "implementing", _fresh_observation(fixture)
        )
        (fixture.repository / "archive-output.txt").write_text(
            "archive output\n", encoding="utf-8"
        )
        write_raw_review_reports(fixture.repository)
        observation = _fresh_observation(fixture)
        ACTIVATION.advance_execution_state(program_root, "reviewing", observation)
        REVIEW.persist_review_preparation(program_root, observation)
    return fixture, legacy_bytes, allocation


def _complete_delete_rollover(
    *, recreate_in_successor=False, third_successor=False
):
    fixture, legacy_bytes, allocation = _reviewed_delete_program(
        recreate_in_successor=recreate_in_successor,
        third_successor=third_successor,
    )
    prompt = CONTINUATION.render_accept_continue_prompt(fixture.program_root)
    receipt = DIFF.persist_diff_disposition(
        fixture.program_root, prompt, _fresh_observation(fixture)
    )
    return fixture, legacy_bytes, allocation, receipt


def _product_result(states, receipts):
    canonical = {
        "ordered_path_states": states,
        "delete_quarantine_bindings": receipts,
    }
    return {
        "schema_version": "implementation-product-path-states/v2",
        "sha256": hashlib.sha256(
            json.dumps(
                canonical,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
        **canonical,
    }


class DeleteOperationLifecycleTests(unittest.TestCase):
    def test_unmapped_names_cannot_bypass_delete_authority_before_mutation(self):
        for filename in ("unmapped.txt", "unmapped-Delete.txt", "unmapped-quarantine.txt"):
            with self.subTest(filename=filename):
                fixture, legacy_bytes = _authorized_delete_program_with_successor()
                try:
                    root = fixture.program_root
                    (fixture.repository / filename).write_text("unmapped user work\n", encoding="utf-8")
                    baseline = json.loads((root / "increments/ARCHIVE-INDEX/execution-baseline.json").read_text())
                    allocation = baseline["delete_quarantine_bindings"][0]
                    before = repository_snapshot(fixture.repository)
                    status_before = (root / "state/status.json").read_bytes()
                    with mock.patch.object(
                        ACTIVATION, "quarantine_bound_regular_file",
                        wraps=ACTIVATION.quarantine_bound_regular_file,
                    ) as move, mock.patch.object(
                        ACTIVATION, "adopt_delete_quarantine_receipt",
                        wraps=ACTIVATION.adopt_delete_quarantine_receipt,
                    ) as adopt:
                        with self.assertRaisesRegex(ValueError, "unmapped dirty paths"):
                            ACTIVATION.advance_execution_state(root, "implementing", _fresh_observation(fixture))
                        move.assert_not_called()
                        adopt.assert_not_called()
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                    self.assertEqual((root / "state/status.json").read_bytes(), status_before)
                    self.assertEqual((fixture.repository / "legacy.ts").read_bytes(), legacy_bytes)
                    self.assertFalse((root / allocation["entry_path"]).exists())
                    self.assertFalse((root / allocation["receipt_path"]).exists())
                finally:
                    fixture.close()

    def test_exact_delete_prefix_recovery_still_blocks_unmapped_work(self):
        for boundary in ("receipt", "status"):
            with self.subTest(boundary=boundary):
                fixture, legacy_bytes = _authorized_delete_program_with_successor()
                try:
                    root = fixture.program_root
                    baseline = json.loads((root / "increments/ARCHIVE-INDEX/execution-baseline.json").read_text())
                    allocation = baseline["delete_quarantine_bindings"][0]
                    entry_path = root / allocation["entry_path"]
                    receipt_path = root / allocation["receipt_path"]
                    status_before = (root / "state/status.json").read_bytes()
                    fault = mock.Mock(side_effect=RuntimeError("interrupted Delete prefix"))
                    patcher = (
                        mock.patch.dict(
                            ACTIVATION.quarantine_bound_regular_file.__globals__,
                            {"_write_delete_receipt": fault},
                        ) if boundary == "receipt" else
                        mock.patch.object(ACTIVATION, "atomic_replace_json", fault)
                    )
                    with patcher:
                        with self.assertRaisesRegex(RuntimeError, "interrupted Delete prefix"):
                            ACTIVATION.advance_execution_state(root, "implementing", _fresh_observation(fixture))
                    self.assertEqual((root / "state/status.json").read_bytes(), status_before)
                    self.assertEqual(entry_path.read_bytes(), legacy_bytes)
                    self.assertFalse((fixture.repository / "legacy.ts").exists())
                    self.assertEqual(receipt_path.exists(), boundary == "status")
                    dirty_path = fixture.repository / "unmapped-quarantine.txt"
                    dirty_path.write_text("unmapped user work\n", encoding="utf-8")
                    before = repository_snapshot(fixture.repository)
                    with mock.patch.object(
                        ACTIVATION, "quarantine_bound_regular_file",
                        wraps=ACTIVATION.quarantine_bound_regular_file,
                    ) as move, mock.patch.object(
                        ACTIVATION, "adopt_delete_quarantine_receipt",
                        wraps=ACTIVATION.adopt_delete_quarantine_receipt,
                    ) as adopt:
                        with self.assertRaisesRegex(ValueError, "unmapped dirty paths"):
                            ACTIVATION.advance_execution_state(root, "implementing", _fresh_observation(fixture))
                        move.assert_not_called()
                        adopt.assert_not_called()
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                    # Remove only the test-created unmapped file in this disposable fixture.
                    dirty_path.unlink()
                    retained_entry = entry_path.read_bytes()
                    with mock.patch.object(
                        ACTIVATION, "quarantine_bound_regular_file",
                        side_effect=AssertionError("recovery must not move again"),
                    ), mock.patch.object(
                        Path, "unlink", side_effect=AssertionError("recovery must retain bytes"),
                    ):
                        receipt = ACTIVATION.advance_execution_state(root, "implementing", _fresh_observation(fixture))
                    self.assertEqual(receipt.increment_state, "implementing")
                    self.assertEqual(entry_path.read_bytes(), retained_entry)
                    self.assertTrue(receipt_path.is_file())
                    normalized = ACTIVATION._without_owned_program_paths(root, _fresh_observation(fixture))
                    self.assertEqual(ACTIVATION.validate_state_authority(root, normalized), [])
                    discovery = run_program_discovery(fixture.repository)
                    self.assertEqual(discovery["disposition"], "resume")
                    self.assertFalse(discovery["stop_required"])
                finally:
                    fixture.close()

    def test_completed_rollover_binds_review_hashes_to_approval_and_disposition(self):
        fixture, legacy_bytes, allocation, _receipt = _complete_delete_rollover()
        try:
            root = fixture.program_root
            status_path = root / "state/status.json"
            rows_path = root / "state/rollovers.jsonl"
            approvals_path = root / "state/approvals.jsonl"
            original_status = json.loads(status_path.read_text())
            original_rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
            original_row = original_rows[-1]
            evidence_path = root / original_row["review_evidence_binding"]["path"]
            packet_path = root / original_row["review_packet_binding"]["path"]
            originals = {
                path: path.read_bytes()
                for path in (status_path, rows_path, approvals_path, evidence_path, packet_path)
            }
            cases = (
                "replace-bundle",
                "replace-bundle-and-disposition",
                "disposition-evidence",
                "disposition-packet",
                "approval-evidence",
                "approval-packet",
            )
            for case in cases:
                with self.subTest(case=case):
                    try:
                        status = copy.deepcopy(original_status)
                        rows = copy.deepcopy(original_rows)
                        row = rows[-1]
                        accepted = row["accepted_diff_binding"]
                        disposition = accepted["diff_disposition_binding"]
                        if case.startswith("replace-bundle"):
                            import review_coordination as coordination

                            evidence = json.loads(originals[evidence_path])
                            evidence["review_packet"]["changes_and_rationale"] = [
                                "Replacement created after the retained approval."
                            ]
                            packet = coordination.ReviewPacket(
                                **coordination._tuple_fields(
                                    evidence["review_packet"], coordination.PACKET_FIELDS
                                )
                            )
                            packet_text = coordination.render_review_packet(packet)
                            self.assertEqual(
                                coordination.validate_review_bundle(evidence, packet_text), []
                            )
                            evidence_path.write_bytes(ACTIVATION._canonical_json_bytes(evidence))
                            packet_path.write_text(packet_text, encoding="utf-8")
                            for stem, path in (("review_evidence", evidence_path),
                                               ("review_packet", packet_path)):
                                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                                row[stem + "_binding"]["sha256"] = digest
                                accepted[stem + "_binding"]["sha256"] = digest
                                if case == "replace-bundle-and-disposition":
                                    disposition[stem + "_sha256"] = digest
                            self.assertEqual(approvals_path.read_bytes(), originals[approvals_path])
                        elif case.startswith("disposition-"):
                            stem = "review_evidence" if case.endswith("evidence") else "review_packet"
                            disposition[stem + "_sha256"] = "0" * 64
                        else:
                            approvals = [json.loads(line) for line in originals[approvals_path].splitlines()]
                            approval = next(
                                item for item in approvals
                                if item.get("event_id") == accepted["diff_approval_binding"]["event_id"]
                            )
                            stem = "review_evidence" if case.endswith("evidence") else "review_packet"
                            approval[stem + "_sha256"] = "0" * 64

                            def approval_line(value):
                                return (json.dumps(value, ensure_ascii=False,
                                                   separators=(",", ":"), sort_keys=False)
                                        + "\n").encode("utf-8")

                            approvals_path.write_bytes(b"".join(approval_line(item) for item in approvals))
                            accepted["diff_approval_binding"]["sha256"] = hashlib.sha256(
                                approval_line(approval)
                            ).hexdigest()
                        rows_path.write_bytes(b"".join(ACTIVATION._canonical_json_line(item) for item in rows))
                        status["rollover_binding"]["rollover_sha256"] = hashlib.sha256(
                            ACTIVATION._canonical_json_line(row)
                        ).hexdigest()
                        status_path.write_bytes(ACTIVATION._canonical_json_bytes(status))
                        observation = ACTIVATION._without_owned_program_paths(root, _fresh_observation(fixture))
                        before = repository_snapshot(fixture.repository)
                        with self.assertRaisesRegex(ValueError, "rollover review .* approval binding mismatch"):
                            ROLLOVER.validated_inherited_paths(root, status, observation)
                        self.assertTrue(ACTIVATION.validate_state_authority(root, observation))
                        discovery = run_program_discovery(fixture.repository)
                        self.assertTrue(discovery["stop_required"])
                        self.assertNotEqual(discovery["disposition"], "resume")
                        self.assertEqual(repository_snapshot(fixture.repository), before)
                        self.assertEqual((root / allocation["entry_path"]).read_bytes(), legacy_bytes)
                        self.assertFalse((fixture.repository / "legacy.ts").exists())
                    finally:
                        for path, content in originals.items():
                            path.write_bytes(content)
            observation = ACTIVATION._without_owned_program_paths(root, _fresh_observation(fixture))
            self.assertEqual(ACTIVATION.validate_state_authority(root, observation), [])
            self.assertEqual(run_program_discovery(fixture.repository)["disposition"], "resume")
        finally:
            fixture.close()

    def test_production_delete_accept_continue_preserves_tombstone_and_quarantine(
        self,
    ) -> None:
        fixture, legacy_bytes, allocation, receipt = _complete_delete_rollover()
        try:
            program_root = fixture.program_root
            self.assertEqual(receipt.successor_increment_id, "ARCHIVE-VERIFY")
            self.assertFalse((fixture.repository / "legacy.ts").exists())
            quarantine_path = program_root / allocation["entry_path"]
            self.assertEqual(quarantine_path.read_bytes(), legacy_bytes)

            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                status["inherited_workspace_binding"]["schema_version"],
                "implementation-inherited-workspace/v2",
            )
            inherited_states = status["inherited_workspace_binding"][
                "inherited_path_states"
            ]
            tombstone = next(
                item for item in inherited_states if item["path"] == "legacy.ts"
            )
            self.assertFalse(tombstone["exists"])
            self.assertTrue(
                any(
                    item["path"] == "legacy.ts"
                    and item["receipt_path"] == allocation["receipt_path"]
                    for item in status["inherited_workspace_binding"][
                        "delete_quarantine_bindings"
                    ]
                )
            )

            rollover = json.loads(
                (program_root / "state/rollovers.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()[-1]
            )
            self.assertEqual(
                rollover["schema_version"], "implementation-increment-rollover/v2"
            )
            self.assertEqual(
                rollover["product_result_schema_version"],
                "implementation-product-path-states/v2",
            )
            self.assertEqual(
                rollover["accepted_product_result"]["sha256"],
                rollover["product_result_sha256"],
            )
            self.assertEqual(
                rollover["review_evidence_binding"],
                rollover["accepted_diff_binding"]["review_evidence_binding"],
            )
            self.assertEqual(
                rollover["review_packet_binding"],
                rollover["accepted_diff_binding"]["review_packet_binding"],
            )
            self.assertNotIn("handoff_addendum_binding", rollover)
            handoff = program_root / rollover["handoff_binding"]["path"]
            self.assertEqual(
                hashlib.sha256(handoff.read_bytes()).hexdigest(),
                rollover["handoff_binding"]["sha256"],
            )

            actions = [
                json.loads(line)
                for line in (program_root / "state/action-authorizations.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            action = next(
                item for item in actions if item.get("actions") == ["rollover-increment"]
            )
            self.assertEqual(
                action["schema_version"], "implementation-action-authorization/v3"
            )
            self.assertEqual(tuple(action), SETUP_V2_ROLLOVER_ACTION_FIELDS)
            self.assertNotIn("accepted_product_delta_sha256", action)

            authority_observation = ACTIVATION._without_owned_program_paths(
                program_root, _fresh_observation(fixture)
            )
            self.assertEqual(
                AUTHORITY.validate_state_authority(
                    program_root, authority_observation
                ),
                [],
            )
            rollover_inspection = ROLLOVER.inspect_increment_rollover(
                program_root, authority_observation
            )
            self.assertEqual(
                rollover_inspection.disposition,
                "resume",
                rollover_inspection,
            )
            discovery = run_program_discovery(fixture.repository)
            self.assertEqual(discovery["disposition"], "resume", discovery)
        finally:
            fixture.close()

    def test_cumulative_v2_states_replace_append_and_recreate_in_result_order(
        self,
    ) -> None:
        absent = {
            "path": "legacy.ts",
            "exists": False,
            "sha256": None,
            "mode": None,
            "device": None,
            "inode": None,
            "link_count": None,
        }
        present = {
            "path": "archive-output.txt",
            "exists": True,
            "sha256": "1" * 64,
            "mode": "0o100644",
            "device": 1,
            "inode": 2,
            "link_count": 1,
        }
        prior_receipt = {
            "path": "legacy.ts",
            "receipt_path": "increments/ONE/delete.receipt.json",
            "receipt_sha256": "2" * 64,
        }
        status = {
            "inherited_workspace_binding": {
                "schema_version": "implementation-inherited-workspace/v2",
                "inherited_path_states": [absent, present],
                "delete_quarantine_bindings": [prior_receipt],
            }
        }
        replacement = {**present, "sha256": "3" * 64, "inode": 4}
        appended = {**present, "path": "verification.txt", "sha256": "4" * 64}
        merged = CONTINUATION._merge_inherited_workspace_v2(
            status,
            {"path": "/workspace"},
            _product_result([replacement, appended], []),
        )
        self.assertEqual(
            [item["path"] for item in merged["inherited_path_states"]],
            ["legacy.ts", "archive-output.txt", "verification.txt"],
        )
        self.assertEqual(merged["delete_quarantine_bindings"], [prior_receipt])

        recreated = {**present, "path": "legacy.ts", "sha256": "5" * 64}
        recreated_merge = CONTINUATION._merge_inherited_workspace_v2(
            status,
            {"path": "/workspace"},
            _product_result([recreated], []),
        )
        self.assertEqual(recreated_merge["inherited_path_states"][0], recreated)
        self.assertEqual(recreated_merge["delete_quarantine_bindings"], [])

        replacement_receipt = {
            **prior_receipt,
            "receipt_path": "increments/TWO/delete.receipt.json",
            "receipt_sha256": "6" * 64,
        }
        repeated_delete = CONTINUATION._merge_inherited_workspace_v2(
            status,
            {"path": "/workspace"},
            _product_result([absent], [replacement_receipt]),
        )
        self.assertEqual(
            repeated_delete["delete_quarantine_bindings"], [replacement_receipt]
        )

    def test_later_continuation_carries_the_exact_v2_result_and_receipt(self) -> None:
        fixture, legacy_bytes, allocation = _reviewed_delete_program()
        try:
            program_root = fixture.program_root
            observation = _fresh_observation(fixture)
            authority_observation = ACTIVATION._without_owned_program_paths(
                program_root, observation
            )
            self.assertEqual(
                AUTHORITY.validate_state_authority(
                    program_root, authority_observation
                ),
                [],
            )
            discovery = run_program_discovery(fixture.repository)
            self.assertEqual(
                discovery["disposition"],
                "increment-acceptance-retry-ready",
                discovery,
            )
            acceptance = DIFF.build_diff_acceptance_candidate(
                program_root, observation
            )
            stop_prompt = "Accept and stop.\n\n" + acceptance.prompt
            DIFF.persist_accept_stop(program_root, stop_prompt, observation)

            prompt = CONTINUATION.render_accepted_state_continuation_prompt(
                program_root
            )
            command = CONTINUATION.validate_submitted_continuation_prompt(
                program_root, prompt
            )
            self.assertEqual(
                command.schema_version,
                "implementation-accepted-state-continuation-binding/v2",
            )
            self.assertEqual(
                command.product_result_sha256,
                command.accepted_product_result["sha256"],
            )
            self.assertEqual(
                command.accepted_product_result["delete_quarantine_bindings"],
                command.inherited_workspace["delete_quarantine_bindings"],
            )
            ROLLOVER.persist_increment_rollover(
                program_root, prompt, _fresh_observation(fixture)
            )
            rollover = json.loads(
                (program_root / "state/rollovers.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()[-1]
            )
            self.assertEqual(rollover["continuation_domain"], "accepted-state")
            self.assertEqual(
                (program_root / allocation["entry_path"]).read_bytes(), legacy_bytes
            )
            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                ROLLOVER.validated_inherited_paths(
                    program_root,
                    status,
                    ACTIVATION._without_owned_program_paths(
                        program_root, _fresh_observation(fixture)
                    ),
                ),
                tuple(
                    item["path"]
                    for item in status["inherited_workspace_binding"][
                        "inherited_path_states"
                    ]
                ),
            )
        finally:
            fixture.close()

    def test_completed_rollover_revalidates_copied_files_and_approval(self) -> None:
        fixture, _legacy_bytes, allocation, _receipt = _complete_delete_rollover()
        try:
            program_root = fixture.program_root
            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            rollover = json.loads(
                (program_root / "state/rollovers.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()[-1]
            )
            targets = (
                ("review evidence", rollover["review_evidence_binding"]["path"]),
                ("review packet", rollover["review_packet_binding"]["path"]),
                ("handoff", rollover["handoff_binding"]["path"]),
                ("successor brief", rollover["successor_brief_binding"]["path"]),
            )
            observation = ACTIVATION._without_owned_program_paths(
                program_root, _fresh_observation(fixture)
            )
            for label, relative in targets:
                path = program_root / relative
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b"tamper")
                    with self.assertRaisesRegex(ValueError, label):
                        ROLLOVER.validated_inherited_paths(
                            program_root, status, observation
                        )
                finally:
                    path.write_bytes(original)

            approvals_path = program_root / "state/approvals.jsonl"
            approvals_bytes = approvals_path.read_bytes()
            try:
                approvals = [
                    json.loads(line) for line in approvals_bytes.splitlines()
                ]
                approval = next(
                    item
                    for item in approvals
                    if item.get("event_id")
                    == rollover["accepted_diff_binding"]["diff_approval_binding"][
                        "event_id"
                    ]
                )
                approval["product_result_sha256"] = "0" * 64
                approvals_path.write_text(
                    "\n".join(
                        json.dumps(item, separators=(",", ":"), sort_keys=False)
                        for item in approvals
                    )
                    + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "diff approval"):
                    ROLLOVER.validated_inherited_paths(
                        program_root, status, observation
                    )
            finally:
                approvals_path.write_bytes(approvals_bytes)

            for relative in (
                allocation["entry_path"],
                allocation["receipt_path"],
            ):
                path = program_root / relative
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b"tamper")
                    with self.assertRaisesRegex(ValueError, "Delete quarantine"):
                        ROLLOVER.validated_inherited_paths(
                            program_root, status, observation
                        )
                finally:
                    path.write_bytes(original)

            (fixture.repository / "legacy.ts").write_text(
                "unexpected reappearance\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(
                ValueError, "inherited accepted product bytes changed"
            ):
                ROLLOVER.validated_inherited_paths(
                    program_root, status, _fresh_observation(fixture)
                )
        finally:
            fixture.close()

    def test_explicit_successor_create_recreates_tombstone_and_retains_quarantine(
        self,
    ) -> None:
        fixture, legacy_bytes, allocation, _receipt = _complete_delete_rollover(
            recreate_in_successor=True
        )
        try:
            program_root = fixture.program_root
            observation = _fresh_observation(fixture)
            prepared = ACTIVATION.prepare_exact_plan(
                program_root,
                _exact_plan_bytes(program_root, observation),
                observation,
            )
            ACTIVATION.materialize_exact_plan(
                program_root, prepared.plan_prompt, observation
            )
            baseline = json.loads(
                (
                    program_root
                    / "increments/ARCHIVE-VERIFY/execution-baseline.json"
                ).read_text(encoding="utf-8")
            )
            self.assertIn("legacy.ts", baseline["file_map"]["create"])
            self.assertNotIn("legacy.ts", baseline["file_map"]["modify"])

            recreated_bytes = b"successor recreation\n"
            with mock.patch.object(
                Path,
                "unlink",
                side_effect=AssertionError("recreation must not unlink quarantine"),
            ):
                ACTIVATION.advance_execution_state(
                    program_root, "implementing", _fresh_observation(fixture)
                )
                (fixture.repository / "legacy.ts").write_bytes(recreated_bytes)
                (fixture.repository / "archive-output.txt").write_text(
                    "successor archive output\n", encoding="utf-8"
                )
                write_raw_review_reports(
                    fixture.repository,
                    increment_id="ARCHIVE-VERIFY",
                    relative_directory="reviews/ARCHIVE-VERIFY",
                )
                ACTIVATION.advance_execution_state(
                    program_root, "reviewing", _fresh_observation(fixture)
                )

            self.assertEqual((fixture.repository / "legacy.ts").read_bytes(), recreated_bytes)
            self.assertEqual(
                (program_root / allocation["entry_path"]).read_bytes(), legacy_bytes
            )
            self.assertTrue((program_root / allocation["receipt_path"]).is_file())
        finally:
            fixture.close()

    def test_unrelated_successor_cannot_recreate_an_inherited_tombstone(self) -> None:
        fixture, _legacy_bytes, _allocation, _receipt = _complete_delete_rollover()
        try:
            program_root = fixture.program_root
            observation = _fresh_observation(fixture)
            prepared = ACTIVATION.prepare_exact_plan(
                program_root,
                _exact_plan_bytes(program_root, observation),
                observation,
            )
            ACTIVATION.materialize_exact_plan(
                program_root, prepared.plan_prompt, observation
            )
            baseline = json.loads(
                (
                    program_root
                    / "increments/ARCHIVE-VERIFY/execution-baseline.json"
                ).read_text(encoding="utf-8")
            )
            self.assertNotIn("legacy.ts", baseline["file_map"]["create"])
            self.assertNotIn("legacy.ts", baseline["file_map"]["modify"])
            self.assertNotIn("legacy.ts", baseline["file_map"]["delete"])

            ACTIVATION.advance_execution_state(
                program_root, "implementing", _fresh_observation(fixture)
            )
            (fixture.repository / "legacy.ts").write_bytes(
                b"undeclared successor recreation\n"
            )
            (fixture.repository / "archive-output.txt").write_text(
                "successor archive output\n", encoding="utf-8"
            )
            write_raw_review_reports(
                fixture.repository,
                increment_id="ARCHIVE-VERIFY",
                relative_directory="reviews/ARCHIVE-VERIFY",
            )
            before = repository_snapshot(program_root)

            with self.assertRaisesRegex(
                ValueError, "inherited accepted product bytes changed: legacy.ts"
            ):
                ACTIVATION.advance_execution_state(
                    program_root, "reviewing", _fresh_observation(fixture)
                )

            self.assertEqual(repository_snapshot(program_root), before)
            self.assertEqual(
                json.loads(
                    (program_root / "state/status.json").read_text(
                        encoding="utf-8"
                    )
                )["current_increment_state"],
                "implementing",
            )
            authority_observation = ACTIVATION._without_owned_program_paths(
                program_root, _fresh_observation(fixture)
            )
            self.assertIn(
                "inherited accepted product bytes changed: legacy.ts",
                AUTHORITY.validate_state_authority(
                    program_root, authority_observation
                ),
            )
        finally:
            fixture.close()

    def test_second_rollover_replaces_tombstone_in_place_and_keeps_history(
        self,
    ) -> None:
        fixture, legacy_bytes, allocation, _receipt = _complete_delete_rollover(
            recreate_in_successor=True,
            third_successor=True,
        )
        try:
            program_root = fixture.program_root
            observation = _fresh_observation(fixture)
            prepared = ACTIVATION.prepare_exact_plan(
                program_root,
                _exact_plan_bytes(program_root, observation),
                observation,
            )
            ACTIVATION.materialize_exact_plan(
                program_root, prepared.plan_prompt, observation
            )
            recreated_bytes = b"successor recreation\n"
            with mock.patch.object(
                Path,
                "unlink",
                side_effect=AssertionError("rollover must retain quarantine"),
            ):
                ACTIVATION.advance_execution_state(
                    program_root, "implementing", _fresh_observation(fixture)
                )
                (fixture.repository / "legacy.ts").write_bytes(recreated_bytes)
                (fixture.repository / "archive-output.txt").write_text(
                    "successor archive output\n", encoding="utf-8"
                )
                write_raw_review_reports(
                    fixture.repository,
                    increment_id="ARCHIVE-VERIFY",
                    relative_directory="reviews/ARCHIVE-VERIFY",
                )
                observation = _fresh_observation(fixture)
                ACTIVATION.advance_execution_state(
                    program_root, "reviewing", observation
                )
                REVIEW.persist_review_preparation(program_root, observation)
                discovery = run_program_discovery(fixture.repository)
                self.assertEqual(
                    discovery["disposition"],
                    "increment-acceptance-retry-ready",
                    discovery,
                )
                prompt = CONTINUATION.render_accept_continue_prompt(program_root)
                DIFF.persist_diff_disposition(
                    program_root, prompt, _fresh_observation(fixture)
                )

            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status["current_increment_id"], "ARCHIVE-REPORT")
            states = status["inherited_workspace_binding"][
                "inherited_path_states"
            ]
            legacy_state = next(item for item in states if item["path"] == "legacy.ts")
            self.assertTrue(legacy_state["exists"])
            self.assertEqual(
                legacy_state["sha256"], hashlib.sha256(recreated_bytes).hexdigest()
            )
            self.assertFalse(
                any(
                    item["path"] == "legacy.ts"
                    for item in status["inherited_workspace_binding"][
                        "delete_quarantine_bindings"
                    ]
                )
            )
            rollovers = [
                json.loads(line)
                for line in (program_root / "state/rollovers.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(rollovers), 2)
            self.assertTrue(
                any(
                    item["path"] == "legacy.ts"
                    for item in rollovers[0]["delete_quarantine_bindings"]
                )
            )
            self.assertEqual(
                (program_root / allocation["entry_path"]).read_bytes(), legacy_bytes
            )
            observation = ACTIVATION._without_owned_program_paths(
                program_root, _fresh_observation(fixture)
            )
            self.assertEqual(
                ROLLOVER.validated_inherited_paths(
                    program_root, status, observation
                ),
                tuple(item["path"] for item in states),
            )
        finally:
            fixture.close()


class DeleteReceiptReinspectionTests(unittest.TestCase):
    def setUp(self):
        self.fixture, self.legacy_bytes = _authorized_delete_program_with_successor()
        self.addCleanup(self.fixture.close)
        self.root = self.fixture.program_root
        ACTIVATION.advance_execution_state(
            self.root, "implementing", _fresh_observation(self.fixture)
        )
        (self.fixture.repository / "archive-output.txt").write_text(
            "archive output\n", encoding="utf-8"
        )
        write_raw_review_reports(self.fixture.repository)
        self.baseline = ACTIVATION.execution_baseline_v2_from_value(
            json.loads(
                (self.root / "increments/ARCHIVE-INDEX/execution-baseline.json")
                .read_text(encoding="utf-8")
            )
        )
        self.binding = self.baseline.delete_quarantine_bindings[0]
        self.receipt_path = self.root / self.binding["receipt_path"]
        self.validate = ACTIVATION.validate_execution_workspace_v2

    def assess(self):
        inspection = ACTIVATION.inspect_repository(self.fixture.repository, self.fixture.head)
        normalized = ACTIVATION._without_owned_program_paths(self.root, inspection.observation)
        return self.validate(
            self.root,
            self.baseline,
            replace(inspection, observation=normalized),
            increment_state="reviewing",
        )

    @contextmanager
    def receipt_race(self, kind):
        namespace = self.validate.__globals__
        classify = namespace["classify_delete_quarantine_recovery"]
        inspect = namespace["inspect_workspace_path"]
        events = []
        with tempfile.TemporaryDirectory() as directory:
            saved = Path(directory) / "receipt.json"
            displaced = Path(directory) / "receipt-link"

            def classify_then_race(*args, **kwargs):
                recovery = classify(*args, **kwargs)
                if not events and recovery.disposition == "resume":
                    events.append("classified-resume")
                    if kind in {"missing", "symlink"}:
                        self.receipt_path.rename(saved)
                        if kind == "symlink":
                            self.receipt_path.symlink_to(saved)
                return recovery

            def inspect_receipt(root, relative, **kwargs):
                if (
                    Path(root) != self.root
                    or relative != self.binding["receipt_path"]
                    or events != ["classified-resume"]
                ):
                    return inspect(root, relative, **kwargs)
                events.append("reinspected")
                try:
                    if kind == "oserror":
                        raise OSError("injected receipt descriptor failure")
                    snapshot = inspect(root, relative, **kwargs)
                    if kind == "null-sha":
                        return replace(snapshot, sha256=None)
                    if kind == "invalid-sha":
                        return replace(snapshot, sha256="invalid")
                    return snapshot
                finally:
                    if saved.exists():
                        if self.receipt_path.is_symlink():
                            self.receipt_path.rename(displaced)
                        saved.rename(self.receipt_path)

            with mock.patch.dict(
                namespace,
                {
                    "classify_delete_quarantine_recovery": classify_then_race,
                    "inspect_workspace_path": inspect_receipt,
                },
            ):
                yield events

    def test_receipt_reinspection_failure_returns_invalid_assessment(self):
        for kind in ("missing", "symlink", "oserror", "null-sha", "invalid-sha"):
            with self.subTest(kind=kind):
                before = repository_snapshot(self.fixture.repository)
                with self.receipt_race(kind) as events:
                    assessment = self.assess()
                self.assertEqual(events, ["classified-resume", "reinspected"])
                self.assertFalse(assessment.valid)
                self.assertTrue(any(
                    issue.startswith("Delete quarantine receipt ")
                    for issue in assessment.issues
                ), assessment.issues)
                self.assertEqual(assessment.product_states.delete_quarantine_bindings, ())
                self.assertEqual(repository_snapshot(self.fixture.repository), before)

    def assert_reviewing_rejected(self, kind):
        status_path = self.root / "state/status.json"
        before_status = status_path.read_bytes()
        before = repository_snapshot(self.fixture.repository)
        with self.receipt_race(kind) as events:
            with mock.patch.object(
                ACTIVATION, "atomic_replace_json",
                wraps=ACTIVATION.atomic_replace_json,
            ) as writer:
                with self.assertRaises(ValueError) as raised:
                    ACTIVATION.advance_execution_state(
                        self.root, "reviewing", _fresh_observation(self.fixture)
                    )
                writer.assert_not_called()
        self.assertIn("Delete quarantine receipt ", str(raised.exception))
        self.assertEqual(events, ["classified-resume", "reinspected"])
        self.assertEqual(status_path.read_bytes(), before_status)
        self.assertEqual(repository_snapshot(self.fixture.repository), before)
        self.assertFalse((self.fixture.repository / "legacy.ts").exists())
        self.assertEqual(
            (self.root / self.binding["entry_path"]).read_bytes(),
            self.legacy_bytes,
        )

    def test_missing_receipt_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("missing")

    def test_symlink_receipt_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("symlink")

    def test_receipt_oserror_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("oserror")

    def test_null_receipt_sha_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("null-sha")

    def test_invalid_receipt_sha_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("invalid-sha")

    def test_valid_receipt_keeps_exact_digest_and_reviewing_transition(self):
        receipt_bytes = self.receipt_path.read_bytes()
        expected_digest = hashlib.sha256(receipt_bytes).hexdigest()
        assessment = self.assess()
        self.assertTrue(assessment.valid, assessment.issues)
        expected_bindings = ({
            "path": "legacy.ts",
            "receipt_path": self.binding["receipt_path"],
            "receipt_sha256": expected_digest,
        },)
        self.assertEqual(assessment.product_states.delete_quarantine_bindings, expected_bindings)
        prior = json.loads((self.root / "state/status.json").read_text())
        transition = ACTIVATION.advance_execution_state(
            self.root, "reviewing", _fresh_observation(self.fixture)
        )
        status = json.loads((self.root / "state/status.json").read_text())
        self.assertEqual(transition.increment_state, "reviewing")
        self.assertEqual(status["state_sequence"], prior["state_sequence"] + 1)
        result = status["execution_transition_binding"]["product_path_states"]
        self.assertEqual(result["delete_quarantine_bindings"], list(expected_bindings))
        tombstone = next(row for row in result["ordered_path_states"] if row["path"] == "legacy.ts")
        self.assertFalse(tombstone["exists"])
        self.assertIsNone(tombstone["sha256"])
        self.assertEqual(self.receipt_path.read_bytes(), receipt_bytes)
        self.assertEqual((self.root / self.binding["entry_path"]).read_bytes(), self.legacy_bytes)
        self.assertEqual(
            ACTIVATION.validate_state_authority(
                self.root,
                ACTIVATION._without_owned_program_paths(
                    self.root, _fresh_observation(self.fixture)
                ),
            ), []
        )


if __name__ == "__main__":
    unittest.main()
