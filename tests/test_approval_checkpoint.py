import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_state_authority import StateAuthorityFixture, write_json_lines


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
CHECKPOINT_PATH = SCRIPT_ROOT / "approval_checkpoint.py"

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC = importlib.util.spec_from_file_location(
        "approval_checkpoint", CHECKPOINT_PATH
    )
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load approval checkpoint from {CHECKPOINT_PATH}")
    CHECKPOINT = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = CHECKPOINT
    SPEC.loader.exec_module(CHECKPOINT)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def common_binding(*, plan_sha256: str = "6" * 64) -> dict[str, object]:
    return {
        "program_id": "portable-library",
        "program_revision": 3,
        "source_id": "PORTABLE-SOURCE",
        "source_sha256": "1" * 64,
        "program_sha256": "2" * 64,
        "semantic_requirements_sha256": "3" * 64,
        "increment_id": "library-index",
        "brief_sha256": "4" * 64,
        "exact_file_plan_sha256": plan_sha256,
        "approval_mode": "approval:standard",
        "workspace": {
            "path": "/workspace/portable-library",
            "branch": "library-maintenance",
            "base_commit": "b" * 40,
            "head_commit": "a" * 40,
        },
    }


def plan_approval(*, plan_sha256: str = "6" * 64) -> dict[str, object]:
    return {
        "schema_version": "implementation-approval/v1",
        "event_id": "LIBRARY-PLAN-APPROVAL",
        "type": "exact-file-plan-approval",
        "scope": ["approve the exact portable library plan"],
        **common_binding(plan_sha256=plan_sha256),
    }


def execution_authorization(
    *, plan_sha256: str = "6" * 64
) -> dict[str, object]:
    return {
        "schema_version": "implementation-action-authorization/v1",
        "authorization_id": "LIBRARY-EXECUTION-AUTHORIZATION",
        "actions": ["modify-workspace", "run-local-verification"],
        "scope": ["implement the exact portable library plan"],
        "constraints": [],
        "excluded": [
            "create-local-commit",
            "create-draft-pull-request",
            "merge",
            "publish",
            "release",
            "deploy",
            "migrate",
            "destructive-operation",
            "modify-provider-state",
            "modify-external-state",
        ],
        **common_binding(plan_sha256=plan_sha256),
    }


def requirements(*, action_plan_sha256: str = "6" * 64):
    return (
        CHECKPOINT.AuthorityRequirement(
            requirement_id="approve-plan",
            kind="approval",
            summary="Approve the exact portable library plan.",
            record=plan_approval(),
        ),
        CHECKPOINT.AuthorityRequirement(
            requirement_id="execute-plan",
            kind="action",
            summary="Authorize bounded local implementation and verification.",
            record=execution_authorization(plan_sha256=action_plan_sha256),
            prerequisites=("approve-plan",),
        ),
    )


class CheckpointConstructionTests(unittest.TestCase):
    def test_same_binding_requirements_share_one_checkpoint_but_remain_separate(self) -> None:
        checkpoint = CHECKPOINT.build_checkpoint(requirements(), (), ())

        self.assertEqual(checkpoint.binding_sha256, "6" * 64)
        self.assertEqual(checkpoint.pending_requirement_ids, ("approve-plan", "execute-plan"))
        self.assertEqual(checkpoint.blocked_requirement_ids, ())
        self.assertEqual(
            tuple(item.kind for item in checkpoint.items),
            ("approval", "action"),
        )

        resolved = CHECKPOINT.resolve_checkpoint(
            checkpoint,
            {"approve-plan": "approve", "execute-plan": "authorize"},
        )
        self.assertEqual(resolved.approval_records[0]["decision"], "approved")
        self.assertEqual(resolved.action_records[0]["decision"], "authorized")

    def test_cross_stage_binding_is_blocked_instead_of_batched(self) -> None:
        checkpoint = CHECKPOINT.build_checkpoint(
            requirements(action_plan_sha256="9" * 64), (), ()
        )

        self.assertEqual(checkpoint.pending_requirement_ids, ("approve-plan",))
        self.assertEqual(checkpoint.blocked_requirement_ids, ("execute-plan",))
        self.assertIn("checkpoint binding mismatch", checkpoint.items[1].issues)

    def test_every_action_has_one_fail_closed_risk_class(self) -> None:
        classified = {
            action: CHECKPOINT.action_risk_class(action)
            for action in CHECKPOINT.AUTHORITY_ACTIONS
        }

        self.assertEqual(set(classified), set(CHECKPOINT.AUTHORITY_ACTIONS))
        self.assertEqual(classified["modify-workspace"], "routine-local")
        self.assertEqual(classified["create-local-commit"], "explicit-local")
        self.assertEqual(classified["create-draft-pull-request"], "bounded-external")
        self.assertEqual(classified["destructive-operation"], "high-consequence")
        with self.assertRaisesRegex(ValueError, "unsupported action"):
            CHECKPOINT.action_risk_class("unknown-action")

    def test_every_high_consequence_action_is_blocked_from_resolution(self) -> None:
        high_consequence_actions = tuple(
            action
            for action in CHECKPOINT.AUTHORITY_ACTIONS
            if CHECKPOINT.action_risk_class(action) == "high-consequence"
        )
        self.assertTrue(high_consequence_actions)
        for action in high_consequence_actions:
            with self.subTest(action=action):
                record = execution_authorization()
                record.update(
                    authorization_id=f"LIBRARY-{action.upper()}-AUTHORIZATION",
                    actions=[action],
                )
                requirement = CHECKPOINT.AuthorityRequirement(
                    requirement_id=f"authorize-{action}",
                    kind="action",
                    summary=f"Request {action} authority.",
                    record=record,
                )

                checkpoint = CHECKPOINT.build_checkpoint(
                    (requirement,),
                    (),
                    (),
                )

                self.assertEqual(
                    checkpoint.blocked_requirement_ids,
                    (f"authorize-{action}",),
                )
                self.assertIn(
                    "high-consequence",
                    " ".join(checkpoint.items[0].issues),
                )
                with self.assertRaisesRegex(ValueError, "blocked checkpoint"):
                    CHECKPOINT.resolve_checkpoint(
                        checkpoint,
                        {f"authorize-{action}": "authorize"},
                    )

    def test_forged_risk_label_cannot_hide_any_high_consequence_action(self) -> None:
        high_consequence_actions = tuple(
            action
            for action in CHECKPOINT.AUTHORITY_ACTIONS
            if CHECKPOINT.action_risk_class(action) == "high-consequence"
        )
        for action in high_consequence_actions:
            with self.subTest(action=action):
                requirement_id = f"forged-{action}"
                record = execution_authorization()
                record.update(
                    authorization_id=f"LIBRARY-FORGED-{action.upper()}",
                    actions=[action],
                )
                checkpoint = CHECKPOINT.CompoundCheckpoint(
                    binding_sha256="6" * 64,
                    items=(
                        CHECKPOINT.CheckpointItem(
                            requirement_id=requirement_id,
                            kind="action",
                            summary=f"Forged {action} item.",
                            state="pending",
                            risk_class="routine-local",
                            issues=(),
                            record=record,
                        ),
                    ),
                    pending_requirement_ids=(requirement_id,),
                    blocked_requirement_ids=(),
                )

                with self.assertRaisesRegex(ValueError, "high-consequence"):
                    CHECKPOINT.resolve_checkpoint(
                        checkpoint,
                        {requirement_id: "authorize"},
                    )

    def test_missing_or_wrong_explicit_choice_never_materializes_a_record(self) -> None:
        checkpoint = CHECKPOINT.build_checkpoint(requirements(), (), ())

        with self.assertRaisesRegex(ValueError, "decision is required"):
            CHECKPOINT.resolve_checkpoint(checkpoint, {"approve-plan": "approve"})
        with self.assertRaisesRegex(ValueError, "invalid action decision"):
            CHECKPOINT.resolve_checkpoint(
                checkpoint,
                {"approve-plan": "approve", "execute-plan": "approve"},
            )

    def test_exact_existing_record_is_adopted_but_conflicting_identifier_blocks(self) -> None:
        approved = {**plan_approval(), "decision": "approved"}
        adopted = CHECKPOINT.build_checkpoint(requirements(), (approved,), ())
        self.assertEqual(adopted.items[0].state, "satisfied")

        conflicting = {
            **approved,
            "exact_file_plan_sha256": "9" * 64,
        }
        blocked = CHECKPOINT.build_checkpoint(requirements(), (conflicting,), ())
        self.assertEqual(blocked.items[0].state, "blocked")
        self.assertIn("record identifier conflict", blocked.items[0].issues)

    def test_equivalent_authority_under_another_identifier_blocks_ambiguity(self) -> None:
        approval = {
            **plan_approval(),
            "event_id": "LIBRARY-OTHER-PLAN-APPROVAL",
            "decision": "approved",
        }
        action = {
            **execution_authorization(),
            "authorization_id": "LIBRARY-OTHER-EXECUTION-AUTHORIZATION",
            "decision": "authorized",
        }

        approval_checkpoint = CHECKPOINT.build_checkpoint(
            requirements()[:1],
            (approval,),
            (),
        )
        action_requirement = CHECKPOINT.AuthorityRequirement(
            requirement_id="execute-plan",
            kind="action",
            summary="Authorize bounded local implementation and verification.",
            record=execution_authorization(),
        )
        action_checkpoint = CHECKPOINT.build_checkpoint(
            (action_requirement,),
            (),
            (action,),
        )

        self.assertEqual(
            approval_checkpoint.blocked_requirement_ids,
            ("approve-plan",),
        )
        self.assertEqual(
            action_checkpoint.blocked_requirement_ids,
            ("execute-plan",),
        )
        for item in (*approval_checkpoint.items, *action_checkpoint.items):
            self.assertIn(
                "equivalent authority record",
                " ".join(item.issues),
            )


class RetrySafeAppendTests(unittest.TestCase):
    def test_append_then_retry_adopts_the_exact_record_without_duplicate_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approvals.jsonl"
            path.write_text("", encoding="utf-8")
            record = {**plan_approval(), "decision": "approved"}

            first = CHECKPOINT.append_exact_record_or_adopt(
                path, record, sha256_file(path)
            )
            persisted = path.read_bytes()
            second = CHECKPOINT.append_exact_record_or_adopt(
                path, record, first.current_sha256
            )

            self.assertFalse(first.adopted)
            self.assertTrue(second.adopted)
            self.assertEqual(path.read_bytes(), persisted)
            self.assertEqual(second.record_identifier, record["event_id"])

    def test_retry_rejects_same_identifier_with_different_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approvals.jsonl"
            record = {**plan_approval(), "decision": "approved"}
            path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
            changed = {**record, "scope": ["different scope"]}

            with self.assertRaisesRegex(ValueError, "identifier conflict"):
                CHECKPOINT.append_exact_record_or_adopt(
                    path, changed, sha256_file(path)
                )


class OrderedPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = StateAuthorityFixture()
        status = self.fixture.load_json("state/status.json")
        status["schema_version"] = "implementation-program-status/v2"
        self.fixture.write_json("state/status.json", status)
        write_json_lines(
            self.fixture.approvals_path,
            [
                record
                for record in self.fixture.approvals()
                if record.get("event_id") != "ARCHIVE-PLAN-APPROVAL"
            ],
        )
        write_json_lines(self.fixture.authorizations_path, [])
        self.request = CHECKPOINT.CheckpointPersistenceRequest(
            checkpoint_id="ARCHIVE-PLAN-CHECKPOINT",
            approval_record=dict(self.fixture.plan_approval),
            action_records=(dict(self.fixture.implementation_authorization),),
            expected_approvals_sha256=sha256_file(self.fixture.approvals_path),
            expected_authorizations_sha256=sha256_file(
                self.fixture.authorizations_path
            ),
            expected_previous_program_state="active",
            expected_previous_increment_id="archive-index",
            expected_previous_increment_state="awaiting-plan-approval",
            transition=CHECKPOINT.TransitionRequest(
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
            ),
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def test_v1_status_is_rejected_before_any_checkpoint_record_is_appended(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status["schema_version"] = "implementation-program-status/v1"
        self.fixture.write_json("state/status.json", status)
        request = CHECKPOINT.CheckpointPersistenceRequest(
            **{
                **self.request.__dict__,
                "transition": CHECKPOINT.TransitionRequest(
                    **{
                        **self.request.transition.__dict__,
                        "expected_status_sha256": sha256_file(
                            self.fixture.status_path
                        ),
                    }
                ),
            }
        )
        approval_bytes = self.fixture.approvals_path.read_bytes()

        with self.assertRaisesRegex(
            CHECKPOINT.CheckpointPersistenceError,
            "v2 status",
        ):
            CHECKPOINT.persist_checkpoint(
                self.fixture.root,
                request,
                self.fixture.observation,
            )

        self.assertEqual(self.fixture.approvals_path.read_bytes(), approval_bytes)

    def test_equivalent_approval_identifier_is_rejected_before_any_append(self) -> None:
        equivalent = {
            **self.request.approval_record,
            "event_id": "ARCHIVE-OTHER-PLAN-APPROVAL",
        }
        write_json_lines(
            self.fixture.approvals_path,
            [*self.fixture.approvals(), equivalent],
        )
        request = CHECKPOINT.CheckpointPersistenceRequest(
            **{
                **self.request.__dict__,
                "expected_approvals_sha256": sha256_file(
                    self.fixture.approvals_path
                ),
            }
        )
        approval_bytes = self.fixture.approvals_path.read_bytes()

        with self.assertRaisesRegex(
            CHECKPOINT.CheckpointPersistenceError,
            "equivalent authority record",
        ):
            CHECKPOINT.persist_checkpoint(
                self.fixture.root,
                request,
                self.fixture.observation,
            )

        self.assertEqual(self.fixture.approvals_path.read_bytes(), approval_bytes)

    def test_equivalent_action_identifier_is_rejected_before_approval_append(self) -> None:
        equivalent = {
            **self.request.action_records[0],
            "authorization_id": "ARCHIVE-OTHER-IMPLEMENTATION-AUTHORIZATION",
        }
        write_json_lines(self.fixture.authorizations_path, [equivalent])
        request = CHECKPOINT.CheckpointPersistenceRequest(
            **{
                **self.request.__dict__,
                "expected_authorizations_sha256": sha256_file(
                    self.fixture.authorizations_path
                ),
            }
        )
        approval_bytes = self.fixture.approvals_path.read_bytes()

        with self.assertRaisesRegex(
            CHECKPOINT.CheckpointPersistenceError,
            "equivalent authority record",
        ):
            CHECKPOINT.persist_checkpoint(
                self.fixture.root,
                request,
                self.fixture.observation,
            )

        self.assertEqual(self.fixture.approvals_path.read_bytes(), approval_bytes)

    def test_foreign_checkpoint_binding_is_rejected_before_approval_append(self) -> None:
        foreign_approval = {
            **self.request.approval_record,
            "program_id": "foreign-program",
        }
        foreign_action = {
            **self.request.action_records[0],
            "program_id": "foreign-program",
        }
        request = CHECKPOINT.CheckpointPersistenceRequest(
            **{
                **self.request.__dict__,
                "approval_record": foreign_approval,
                "action_records": (foreign_action,),
            }
        )
        approval_bytes = self.fixture.approvals_path.read_bytes()

        with self.assertRaises(CHECKPOINT.CheckpointPersistenceError) as raised:
            CHECKPOINT.persist_checkpoint(
                self.fixture.root,
                request,
                self.fixture.observation,
            )

        self.assertEqual(raised.exception.receipt.failed_step, "preflight")
        self.assertEqual(raised.exception.receipt.completed_steps, ())
        self.assertEqual(self.fixture.approvals_path.read_bytes(), approval_bytes)

    def test_every_high_consequence_action_is_rejected_before_persistence(self) -> None:
        high_consequence_actions = tuple(
            action
            for action in CHECKPOINT.AUTHORITY_ACTIONS
            if CHECKPOINT.action_risk_class(action) == "high-consequence"
        )
        approval_bytes = self.fixture.approvals_path.read_bytes()
        for action in high_consequence_actions:
            with self.subTest(action=action):
                authorization_id = f"ARCHIVE-{action.upper()}-AUTHORIZATION"
                action_record = {
                    **self.fixture.implementation_authorization,
                    "authorization_id": authorization_id,
                    "actions": [action],
                }
                request = CHECKPOINT.CheckpointPersistenceRequest(
                    **{
                        **self.request.__dict__,
                        "action_records": (action_record,),
                        "transition": CHECKPOINT.TransitionRequest(
                            **{
                                **self.request.transition.__dict__,
                                "execution_authorization_id": authorization_id,
                            }
                        ),
                    }
                )

                with self.assertRaisesRegex(ValueError, "high-consequence"):
                    CHECKPOINT.persist_checkpoint(
                        self.fixture.root,
                        request,
                        self.fixture.observation,
                    )

                self.assertEqual(
                    self.fixture.approvals_path.read_bytes(),
                    approval_bytes,
                )

    def test_retry_rejects_substituted_transition_authority_and_plan_state(self) -> None:
        real_append = CHECKPOINT.atomic_append_json_line

        def fail_action_append(path, record, expected_sha256):
            if Path(path) == self.fixture.authorizations_path:
                raise OSError("simulated action record failure")
            return real_append(path, record, expected_sha256)

        with mock.patch.object(
            CHECKPOINT,
            "atomic_append_json_line",
            side_effect=fail_action_append,
        ):
            with self.assertRaises(CHECKPOINT.CheckpointPersistenceError):
                CHECKPOINT.persist_checkpoint(
                    self.fixture.root,
                    self.request,
                    self.fixture.observation,
                )

        applied = self.fixture.load_json("state/status.json")
        mutations = {
            "execution authorization id": lambda status: status[
                "execution_authorization"
            ].update(authorization_id="ARCHIVE-SUBSTITUTED-AUTHORIZATION"),
            "execution authorization scope": lambda status: status[
                "execution_authorization"
            ].update(scope="different scope"),
            "transition authority": lambda status: status[
                "transition_authority"
            ].update(checkpoint_id="ARCHIVE-OTHER-CHECKPOINT"),
            "approved plan": lambda status: status.update(
                approved_exact_file_plan_sha256="0" * 64
            ),
            "pending plan": lambda status: status.update(
                pending_exact_file_plan_sha256=self.fixture.plan_sha256
            ),
            "previous transition event": lambda status: status[
                "previous_state"
            ].update(transition_event_id="ARCHIVE-OTHER-PLAN-APPROVAL"),
            "previous lifecycle state": lambda status: status[
                "previous_state"
            ].update(current_increment_state="implementing"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(applied)
                mutate(changed)
                self.fixture.write_json("state/status.json", changed)

                with self.assertRaises(CHECKPOINT.CheckpointPersistenceError) as raised:
                    CHECKPOINT.persist_checkpoint(
                        self.fixture.root,
                        self.request,
                        self.fixture.observation,
                    )

                self.assertEqual(raised.exception.receipt.failed_step, "preflight")
                self.assertEqual(
                    self.fixture.authorizations_path.read_text(encoding="utf-8"),
                    "",
                )

    def test_persistence_orders_approval_transition_then_action_and_retries_idempotently(self) -> None:
        first = CHECKPOINT.persist_checkpoint(
            self.fixture.root,
            self.request,
            self.fixture.observation,
        )
        first_approval_bytes = self.fixture.approvals_path.read_bytes()
        first_status_bytes = self.fixture.status_path.read_bytes()
        first_authorization_bytes = self.fixture.authorizations_path.read_bytes()

        second = CHECKPOINT.persist_checkpoint(
            self.fixture.root,
            self.request,
            self.fixture.observation,
        )

        self.assertEqual(
            first.completed_steps,
            ("approval:ARCHIVE-PLAN-APPROVAL", "transition", "action:ARCHIVE-IMPLEMENTATION-AUTHORIZATION"),
        )
        self.assertFalse(first.requires_retry)
        self.assertTrue(second.approval_receipt.adopted)
        self.assertTrue(second.action_receipts[0].adopted)
        self.assertEqual(self.fixture.approvals_path.read_bytes(), first_approval_bytes)
        self.assertEqual(self.fixture.status_path.read_bytes(), first_status_bytes)
        self.assertEqual(
            self.fixture.authorizations_path.read_bytes(),
            first_authorization_bytes,
        )

    def test_retry_rejects_changed_transition_evidence_before_action_append(self) -> None:
        real_append = CHECKPOINT.atomic_append_json_line

        def fail_action_append(path, record, expected_sha256):
            if Path(path) == self.fixture.authorizations_path:
                raise OSError("simulated action record failure")
            return real_append(path, record, expected_sha256)

        with mock.patch.object(
            CHECKPOINT,
            "atomic_append_json_line",
            side_effect=fail_action_append,
        ):
            with self.assertRaises(CHECKPOINT.CheckpointPersistenceError):
                CHECKPOINT.persist_checkpoint(
                    self.fixture.root,
                    self.request,
                    self.fixture.observation,
                )

        changed_transition = CHECKPOINT.TransitionRequest(
            **{
                **self.request.transition.__dict__,
                "evidence": {
                    **self.request.transition.evidence,
                    "review_packet_sha256": "9" * 64,
                },
            }
        )
        changed_request = CHECKPOINT.CheckpointPersistenceRequest(
            **{
                **self.request.__dict__,
                "transition": changed_transition,
            }
        )

        with self.assertRaises(CHECKPOINT.CheckpointPersistenceError) as raised:
            CHECKPOINT.persist_checkpoint(
                self.fixture.root,
                changed_request,
                self.fixture.observation,
            )

        self.assertEqual(raised.exception.receipt.failed_step, "preflight")
        self.assertEqual(
            self.fixture.authorizations_path.read_text(encoding="utf-8"),
            "",
        )

    def test_action_append_failure_reports_partial_state_and_retry_finishes_without_duplication(self) -> None:
        real_append = CHECKPOINT.atomic_append_json_line

        def fail_action_append(path, record, expected_sha256):
            if Path(path) == self.fixture.authorizations_path:
                raise OSError("simulated action record failure")
            return real_append(path, record, expected_sha256)

        with mock.patch.object(
            CHECKPOINT,
            "atomic_append_json_line",
            side_effect=fail_action_append,
        ):
            with self.assertRaises(CHECKPOINT.CheckpointPersistenceError) as raised:
                CHECKPOINT.persist_checkpoint(
                    self.fixture.root,
                    self.request,
                    self.fixture.observation,
                )

        receipt = raised.exception.receipt
        self.assertEqual(
            receipt.completed_steps,
            ("approval:ARCHIVE-PLAN-APPROVAL", "transition"),
        )
        self.assertEqual(
            receipt.failed_step,
            "action:ARCHIVE-IMPLEMENTATION-AUTHORIZATION",
        )
        self.assertTrue(receipt.requires_retry)
        self.assertEqual(self.fixture.authorizations_path.read_text(encoding="utf-8"), "")

        recovered = CHECKPOINT.persist_checkpoint(
            self.fixture.root,
            self.request,
            self.fixture.observation,
        )
        self.assertFalse(recovered.requires_retry)
        self.assertEqual(len(self.fixture.approvals()), 2)
        self.assertEqual(len(self.fixture.authorizations()), 1)


if __name__ == "__main__":
    unittest.main()
