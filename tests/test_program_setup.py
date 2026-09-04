import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture,
    _exact_plan_bytes,
    canonical_compact_sha256,
    canonical_json,
    repository_snapshot,
    write_raw_review_reports,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_setup.py"
sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC = importlib.util.spec_from_file_location("program_setup", SCRIPT_PATH)
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load program setup from {SCRIPT_PATH}")
    SETUP = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = SETUP
    SPEC.loader.exec_module(SETUP)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def load_script(name: str):
    path = SCRIPT_ROOT / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    sys.path.insert(0, str(SCRIPT_ROOT))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(SCRIPT_ROOT))
    return module


BOOTSTRAP = load_script("program_bootstrap")
ACTIVATION = load_script("program_activation")
STATE = sys.modules["state_authority"]
AUTHORITY = sys.modules["program_authority"]
REVIEW = load_script("program_review")
DIFF = load_script("diff_disposition")
CLOSURE = load_script("program_closure")
BLOCKED = load_script("blocked_recovery")
DISCOVERY = load_script("program_discovery")


def gate_definition(
    gate_id: str = "SOURCE-GATE-ARCHIVE",
    trigger: str = "before-program-activation",
    *,
    setup_reuse: bool = False,
) -> dict[str, object]:
    return {
        "schema_version": "source-gate-definition/v1",
        "gate_id": gate_id,
        "source_id": "ARCHIVE-SOURCE",
        "source_sha256": "0" * 64,
        "source_title": "Archive Plan",
        "source_location": "source/implementation-plan.md, line 3",
        "source_unit_bindings": [],
        "question": "Confirm archive checksum verification?",
        "protected_subject": "program:ARCHIVE-PROGRAM",
        "trigger": trigger,
        "response_semantics": "unconditional-affirmative-satisfaction",
        "setup_reuse": setup_reuse,
    }


class ProgramSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BootstrapFixture()
        gate = gate_definition()
        gate["source_sha256"] = self.fixture.source_sha256
        self.fixture.configure_setup_v3(source_gate_definitions=(gate,))

    def tearDown(self) -> None:
        self.fixture.close()

    def manifest(self) -> dict[str, object]:
        return self.fixture.load_json("manifest.json")

    def test_setup_semantics_validate_and_visible_mutation_changes_identity(self) -> None:
        manifest = self.manifest()
        self.assertEqual(SETUP.validate_setup_semantics(self.fixture.candidate), [])
        original = SETUP.setup_semantic_identity(manifest)
        changed = copy.deepcopy(manifest)
        changed["setup_semantics"]["material_risks"].append("A new visible risk.")
        changed["setup_semantics_sha256"] = canonical_compact_sha256(
            changed["setup_semantics"]
        )
        self.assertNotEqual(SETUP.setup_semantic_identity(changed), original)

    def test_recap_projects_every_approval_bound_surface_without_json(self) -> None:
        recap = SETUP.render_setup_recap(self.fixture.candidate)
        for expected in (
            "Archive integrity program",
            "ARCHIVE-PROGRAM",
            "Archive Plan",
            "ARCHIVE-SOURCE",
            "archive-maintenance",
            "staged: none",
            "ARCHIVE-INDEX",
            "Verify every stored checksum.",
            "approval:standard",
            "Supported operations: Create, Modify, Preserve.",
            "Create archive-output.txt",
            "archive checksum output",
            "mode: not applicable",
            "Preserve catalog.txt",
            "Confirm archive checksum verification?",
            "Every other response writes nothing.",
            "No external publication.",
            "Approve this program setup?",
        ):
            self.assertIn(expected, recap)
        self.assertNotIn('"schema_version"', recap)
        self.assertNotIn(self.manifest()["setup_semantics_sha256"], recap)
        self.assertNotIn(self.fixture.source_sha256, recap)
        self.assertNotIn("Base commit:", recap)
        self.assertNotIn("Observed head commit:", recap)
        self.assertNotIn(self.fixture.head, recap)

    def test_authoritative_source_and_increment_dependencies_are_exact(self) -> None:
        manifest = self.manifest()
        manifest["setup_semantics"]["sources"][0]["sha256"] = "f" * 64
        manifest["setup_semantics"]["increments"][0]["depends_on"] = [
            "UNKNOWN-INCREMENT"
        ]
        manifest["setup_semantics_sha256"] = canonical_compact_sha256(
            manifest["setup_semantics"]
        )
        self.fixture.write_json("manifest.json", manifest)

        issues = SETUP.validate_setup_semantics(self.fixture.candidate)

        self.assertIn("setup authoritative source binding mismatch", issues)
        self.assertIn("setup increment dependency graph is invalid", issues)

    def test_source_gate_unit_bindings_match_traceability(self) -> None:
        manifest = self.manifest()
        traceability = self.fixture.load_json("program/traceability.json")
        source_unit = traceability["source_units"][2]
        manifest["source_gate_definitions"][0]["source_unit_bindings"] = [
            {
                "source_unit_id": source_unit["id"],
                "source_text_sha256": source_unit["source_text_sha256"],
            }
        ]
        manifest["source_gate_definitions_sha256"] = canonical_compact_sha256(
            manifest["source_gate_definitions"]
        )
        manifest["setup_semantics"]["bindings"][
            "source_gate_definitions_sha256"
        ] = manifest["source_gate_definitions_sha256"]
        manifest["setup_semantics_sha256"] = canonical_compact_sha256(
            manifest["setup_semantics"]
        )
        self.fixture.write_json("manifest.json", manifest)
        self.assertEqual(SETUP.validate_setup_semantics(self.fixture.candidate), [])

        manifest["source_gate_definitions"][0]["source_unit_bindings"][0][
            "source_text_sha256"
        ] = "f" * 64
        manifest["source_gate_definitions_sha256"] = canonical_compact_sha256(
            manifest["source_gate_definitions"]
        )
        manifest["setup_semantics"]["bindings"][
            "source_gate_definitions_sha256"
        ] = manifest["source_gate_definitions_sha256"]
        manifest["setup_semantics_sha256"] = canonical_compact_sha256(
            manifest["setup_semantics"]
        )
        self.fixture.write_json("manifest.json", manifest)
        self.assertIn(
            "source gate 0 source-unit binding mismatch",
            SETUP.validate_setup_semantics(self.fixture.candidate),
        )

    def test_setup_requires_the_status_current_first_brief(self) -> None:
        (
            self.fixture.candidate / "increments/ARCHIVE-INDEX/brief.md"
        ).unlink()
        self.assertIn(
            "status-current increment brief: file is missing",
            SETUP.validate_setup_semantics(self.fixture.candidate),
        )

    def test_recap_checkpoint_changes_when_only_renderer_bytes_change(self) -> None:
        recap = SETUP.render_setup_recap(self.fixture.candidate)
        checkpoint = SETUP.setup_recap_checkpoint(self.fixture.candidate, recap)
        changed = SETUP.setup_recap_checkpoint(self.fixture.candidate, recap + "\n")
        self.assertNotEqual(checkpoint["recap_sha256"], changed["recap_sha256"])
        self.assertNotEqual(checkpoint["checkpoint_id"], changed["checkpoint_id"])

    def test_setup_adapter_accepts_only_current_direct_unconditional_answer(self) -> None:
        recap = SETUP.render_setup_recap(self.fixture.candidate)
        checkpoint = SETUP.setup_recap_checkpoint(self.fixture.candidate, recap)
        approved = SETUP.adapt_setup_decision(
            self.fixture.candidate,
            "Yes",
            role="user",
            provenance="direct-user-message",
            checkpoint=checkpoint,
        )
        self.assertEqual(approved["decision"], "approved")
        for response, role, provenance in (
            ("No", "user", "direct-user-message"),
            ("Yes, if the tests pass", "user", "direct-user-message"),
            ('The user said "yes"', "user", "direct-user-message"),
            ("Yes", "assistant", "direct-user-message"),
            ("Yes", "user", "retrieved-content"),
        ):
            value = SETUP.adapt_setup_decision(
                self.fixture.candidate,
                response,
                role=role,
                provenance=provenance,
                checkpoint=checkpoint,
            )
            self.assertNotEqual(value["decision"], "approved")

    def test_stale_setup_checkpoint_is_rejected(self) -> None:
        recap = SETUP.render_setup_recap(self.fixture.candidate)
        checkpoint = SETUP.setup_recap_checkpoint(self.fixture.candidate, recap)
        checkpoint["recap_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "stale setup recap checkpoint"):
            SETUP.adapt_setup_decision(
                self.fixture.candidate,
                "Yes",
                role="user",
                provenance="direct-user-message",
                checkpoint=checkpoint,
            )

    def test_gate_validation_rejects_unsupported_trigger_and_response_model(self) -> None:
        manifest = self.manifest()
        invalid = copy.deepcopy(manifest)
        invalid["source_gate_definitions"][0]["trigger"] = "before-unknown"
        invalid["source_gate_definitions"][0]["response_semantics"] = "choice"
        invalid["source_gate_definitions_sha256"] = canonical_compact_sha256(
            invalid["source_gate_definitions"]
        )
        invalid["setup_semantics"]["bindings"][
            "source_gate_definitions_sha256"
        ] = invalid["source_gate_definitions_sha256"]
        invalid["setup_semantics_sha256"] = canonical_compact_sha256(
            invalid["setup_semantics"]
        )
        self.fixture.write_json("manifest.json", invalid)
        issues = SETUP.validate_setup_semantics(self.fixture.candidate)
        self.assertIn("unsupported source-gate trigger: before-unknown", issues)
        self.assertIn("unsupported-source-gate-response-semantics", issues)

    def test_older_manifest_families_reject_recognized_v3_additions(self) -> None:
        for manifest_schema in (
            "implementation-program-manifest/v2",
            "implementation-program-manifest/v1",
        ):
            with self.subTest(manifest_schema=manifest_schema):
                fixture = BootstrapFixture()
                try:
                    manifest = fixture.load_json("manifest.json")
                    manifest["schema_version"] = manifest_schema
                    manifest["logical_roles"].update(
                        setup_activation_decision=(
                            "state/setup-activation-decision.json"
                        ),
                        source_gate_decisions="state/source-gate-decisions.jsonl",
                    )
                    fixture.write_json("manifest.json", manifest)
                    issues = AUTHORITY.validate_program_authority(
                        fixture.candidate,
                        validation_mode=(
                            AUTHORITY.PROPOSAL_VALIDATION_MODE
                            if manifest_schema.endswith("/v2")
                            else AUTHORITY.APPROVED_VALIDATION_MODE
                        ),
                    )
                    self.assertIn(
                        "manifest family rejects v3-only logical role "
                        "setup_activation_decision",
                        issues,
                    )
                    self.assertIn(
                        "manifest family rejects v3-only logical role "
                        "source_gate_decisions",
                        issues,
                    )
                finally:
                    fixture.close()

    def test_manifest_v2_rejects_v3_only_status_binding_addition(self) -> None:
        fixture = BootstrapFixture()
        try:
            status = fixture.load_json("state/status.json")
            status["setup_activation_binding"] = {
                "schema_version": "implementation-setup-activation-status-binding/v1"
            }
            fixture.write_json("state/status.json", status)
            manifest = fixture.load_json("manifest.json")
            issues = STATE.validate_state(
                fixture.candidate,
                manifest,
                status,
                STATE.RepositoryObservation(
                    repository="fixture",
                    path=str(fixture.repository),
                    branch="archive-maintenance",
                    base_commit=fixture.head,
                    head_commit=fixture.head,
                    staged_paths=(),
                    modified_paths=(),
                    untracked_paths=(),
                    conflicted_paths=(),
                    active_git_operation=None,
                ),
            )
            self.assertIn(
                "manifest family rejects foreign authority schema "
                "implementation-setup-activation-status-binding/v1",
                issues,
            )
        finally:
            fixture.close()

    def test_manifest_v3_rejects_legacy_status_binding_addition(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status["activation_binding"] = {
            "schema_version": "implementation-program-activation-binding/v1"
        }
        self.fixture.write_json("state/status.json", status)
        issues = STATE.validate_state(
            self.fixture.candidate,
            self.manifest(),
            status,
            STATE.RepositoryObservation(
                repository="fixture",
                path=str(self.fixture.repository),
                branch="archive-maintenance",
                base_commit=self.fixture.head,
                head_commit=self.fixture.head,
                staged_paths=(),
                modified_paths=(),
                untracked_paths=(),
                conflicted_paths=(),
                active_git_operation=None,
            ),
        )
        self.assertIn(
            "manifest family rejects foreign authority schema "
            "implementation-program-activation-binding/v1",
            issues,
        )

    def test_gate_recap_and_adapter_bind_the_exact_next_gate(self) -> None:
        recap = SETUP.render_source_gate_recap(
            self.fixture.candidate,
            "SOURCE-GATE-ARCHIVE",
            "program:ARCHIVE-PROGRAM",
        )
        self.assertIn("Confirm archive checksum verification?", recap)
        self.assertIn("Every other response writes nothing.", recap)
        adapter = SETUP.adapt_source_gate_decision(
            self.fixture.candidate,
            "SOURCE-GATE-ARCHIVE",
            "program:ARCHIVE-PROGRAM",
            "Yes",
            role="user",
            provenance="direct-user-message",
        )
        self.assertEqual(adapter["decision"], "satisfied")
        self.assertEqual(adapter["gate_id"], "SOURCE-GATE-ARCHIVE")

    def test_source_gate_satisfaction_is_sorted_and_acyclic(self) -> None:
        second = gate_definition("SOURCE-GATE-ZETA")
        second["source_sha256"] = self.fixture.source_sha256
        first = gate_definition("SOURCE-GATE-ALPHA")
        first["source_sha256"] = self.fixture.source_sha256
        self.fixture.configure_setup_v3(source_gate_definitions=(second, first))
        setup_record = {
            "schema_version": "setup-activation-decision/v1",
            "decision_id": "SETUP-ACTIVATION-TEST",
            "setup_adapter_id": "SETUP-ADAPTER-TEST",
            "setup_adapter_sha256": "b" * 64,
        }
        setup_path = self.fixture.candidate / "state/setup-activation-decision.json"
        setup_path.write_bytes(canonical_json(setup_record))
        status_path = self.fixture.candidate / "state/status.json"
        for gate_id in ("SOURCE-GATE-ALPHA", "SOURCE-GATE-ZETA"):
            adapter = SETUP.adapt_source_gate_decision(
                self.fixture.candidate,
                gate_id,
                "program:ARCHIVE-PROGRAM",
                "Yes",
                role="user",
                provenance="direct-user-message",
            )
            SETUP.persist_source_gate_decision(
                self.fixture.candidate,
                adapter,
                status_sha256=SETUP.sha256_file(status_path),
                status_sequence=0,
                workspace_observation={"head_commit": self.fixture.head},
                boundary_authority={"setup_adapter_id": "SETUP-ADAPTER-TEST"},
            )
        satisfaction = SETUP.source_gate_satisfaction(
            self.fixture.candidate,
            "before-program-activation",
            "program:ARCHIVE-PROGRAM",
        )
        ids = [item["gate_id"] for item in satisfaction["entries"]]
        self.assertEqual(ids, ["SOURCE-GATE-ALPHA", "SOURCE-GATE-ZETA"])
        encoded = json.dumps(satisfaction, sort_keys=True)
        self.assertNotIn("protected_artifact_sha256", encoded)

    def test_semantic_first_start_handoff_and_intent_contain_no_machine_payload(self) -> None:
        status = self.fixture.load_json("state/status.json")
        status.update(
            state_sequence=1,
            program_state="active",
            current_increment_state="awaiting-first-increment",
        )
        self.fixture.write_json("state/status.json", status)
        handoff = SETUP.render_increment_start_handoff(self.fixture.candidate)
        self.assertIn("Start increment ARCHIVE-INDEX", handoff)
        self.assertNotIn("sha256", handoff)
        intent = SETUP.adapt_increment_start_intent(
            self.fixture.candidate,
            handoff,
            role="user",
            provenance="direct-user-message",
        )
        self.assertEqual(intent["increment_id"], "ARCHIVE-INDEX")
        self.assertEqual(
            intent["brief_binding"]["path"],
            "increments/ARCHIVE-INDEX/brief.md",
        )
        self.assertEqual(intent["brief_binding"]["head_commit"], self.fixture.head)
        with self.assertRaisesRegex(ValueError, "direct current user message"):
            SETUP.adapt_increment_start_intent(
                self.fixture.candidate,
                handoff,
                role="assistant",
                provenance="direct-user-message",
            )


class SetupActivationTests(unittest.TestCase):
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
            self.fixture.repository,
            self.fixture.head,
        ).observation

    def normalized_observation(self):
        return ACTIVATION._without_owned_program_paths(
            self.fixture.program_root, self.observation()
        )

    def setup_decision(self, response: str = "Yes") -> dict[str, object]:
        return SETUP.adapt_setup_decision(
            self.fixture.program_root,
            response,
            role="user",
            provenance="direct-user-message",
        )

    def reset_with_gate(self, trigger: str, protected_subject: str) -> dict[str, object]:
        self.tearDown()
        self.fixture = BootstrapFixture()
        gate = gate_definition(trigger=trigger)
        gate["source_sha256"] = self.fixture.source_sha256
        gate["protected_subject"] = protected_subject
        self.fixture.configure_setup_v3(source_gate_definitions=(gate,))
        BOOTSTRAP.publish_program_proposal(
            self.fixture.repository,
            self.fixture.source_plan,
            self.fixture.candidate,
            self.fixture.source_sha256,
        )
        return gate

    def activate_and_start(self) -> None:
        activation = ACTIVATION.activate_program(
            self.fixture.program_root,
            self.setup_decision(),
            self.observation(),
        )
        intent = SETUP.adapt_increment_start_intent(
            self.fixture.program_root,
            activation.handoff,
            role="user",
            provenance="direct-user-message",
        )
        ACTIVATION.start_first_increment(
            self.fixture.program_root, intent, self.observation()
        )

    def authorize_current_plan(self):
        self.activate_and_start()
        plan = _exact_plan_bytes(
            self.fixture.program_root, self.normalized_observation()
        )
        prepared = ACTIVATION.prepare_exact_plan(
            self.fixture.program_root, plan, self.observation()
        )
        return ACTIVATION.materialize_exact_plan(
            self.fixture.program_root, prepared.plan_prompt, self.observation()
        )

    def persist_gate(
        self,
        gate: dict[str, object],
        boundary_authority: dict[str, object],
    ) -> None:
        status_path = self.fixture.program_root / "state/status.json"
        status = json.loads(status_path.read_text())
        adapter = SETUP.adapt_source_gate_decision(
            self.fixture.program_root,
            gate["gate_id"],
            gate["protected_subject"],
            "Yes",
            role="user",
            provenance="direct-user-message",
        )
        SETUP.persist_source_gate_decision(
            self.fixture.program_root,
            adapter,
            status_sha256=ACTIVATION.sha256_file(status_path),
            status_sequence=status["state_sequence"],
            workspace_observation=ACTIVATION._observation_value(
                self.normalized_observation()
            ),
            boundary_authority=boundary_authority,
            exact_plan_sha256=(
                status.get("approved_exact_file_plan_sha256")
                or status.get("pending_exact_file_plan_sha256")
            ),
            execution_baseline_sha256=(
                status.get("execution_baseline_binding", {}).get("sha256")
                if isinstance(status.get("execution_baseline_binding"), dict)
                else (
                    ACTIVATION.sha256_file(
                        self.fixture.program_root
                        / "increments/ARCHIVE-INDEX/execution-baseline.json"
                    )
                    if (
                        self.fixture.program_root
                        / "increments/ARCHIVE-INDEX/execution-baseline.json"
                    ).is_file()
                    else None
                )
            ),
        )

    def test_negative_setup_decision_leaves_published_proposal_byte_identical(self) -> None:
        before = {
            path.relative_to(self.fixture.program_root).as_posix(): path.read_bytes()
            for path in self.fixture.program_root.rglob("*")
            if path.is_file()
        }
        with self.assertRaisesRegex(ValueError, "not affirmative"):
            ACTIVATION.activate_program(
                self.fixture.program_root,
                self.setup_decision("No"),
                self.observation(),
            )
        after = {
            path.relative_to(self.fixture.program_root).as_posix(): path.read_bytes()
            for path in self.fixture.program_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)

    def test_setup_activation_stops_waiting_without_execution_authority(self) -> None:
        receipt = ACTIVATION.activate_program(
            self.fixture.program_root,
            self.setup_decision(),
            self.observation(),
        )
        status = json.loads(
            (self.fixture.program_root / "state/status.json").read_text()
        )
        self.assertEqual(status["schema_version"], "implementation-program-status/v3")
        self.assertEqual(status["state_sequence"], 1)
        self.assertEqual(status["program_state"], "active")
        self.assertEqual(status["current_increment_state"], "awaiting-first-increment")
        self.assertIsNone(receipt.increment_grant_id)
        self.assertIn("Start increment ARCHIVE-INDEX", receipt.handoff)
        self.assertEqual(
            (self.fixture.program_root / "state/increment-grants.jsonl").read_bytes(),
            b"",
        )
        self.assertEqual(
            (self.fixture.program_root / "state/action-authorizations.jsonl").read_bytes(),
            b"",
        )
        increment_root = self.fixture.program_root / "increments/ARCHIVE-INDEX"
        self.assertTrue((increment_root / "brief.md").is_file())
        self.assertFalse((increment_root / "exact-file-plan.md").exists())
        self.assertFalse((increment_root / "execution-baseline.json").exists())
        self.assertEqual(
            STATE.validate_state_authority(
                self.fixture.program_root, self.normalized_observation()
            ),
            [],
        )

    def test_status_setup_activation_binding_must_match_durable_authority(
        self,
    ) -> None:
        cases = (
            ("decision-id", "setup_activation_decision_id", "OTHER-DECISION"),
            ("decision-digest", "setup_activation_decision_sha256", "f" * 64),
            ("program-event-id", "program_approval_event_id", "OTHER-EVENT"),
            ("program-digest", "program_approval_sha256", "f" * 64),
            ("workspace-event-id", "workspace_approval_event_id", "OTHER-EVENT"),
            ("workspace-digest", "workspace_approval_sha256", "f" * 64),
            ("source-gates", "source_gate_satisfaction", {}),
        )
        for label, field, value in cases:
            with self.subTest(label=label):
                self.tearDown()
                self.setUp()
                ACTIVATION.activate_program(
                    self.fixture.program_root,
                    self.setup_decision(),
                    self.observation(),
                )
                status_path = self.fixture.program_root / "state/status.json"
                status = json.loads(status_path.read_text(encoding="utf-8"))
                status["setup_activation_binding"][field] = value
                status_path.write_bytes(ACTIVATION._canonical_json_bytes(status))

                self.assertIn(
                    "v3 setup activation status binding mismatch",
                    STATE.validate_state_authority(
                        self.fixture.program_root,
                        self.normalized_observation(),
                    ),
                )

    def test_first_start_rejects_corrupt_setup_activation_binding_before_write(
        self,
    ) -> None:
        activation = ACTIVATION.activate_program(
            self.fixture.program_root,
            self.setup_decision(),
            self.observation(),
        )
        status_path = self.fixture.program_root / "state/status.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status["setup_activation_binding"][
            "setup_activation_decision_sha256"
        ] = "f" * 64
        status_path.write_bytes(ACTIVATION._canonical_json_bytes(status))
        intent = SETUP.adapt_increment_start_intent(
            self.fixture.program_root,
            activation.handoff,
            role="user",
            provenance="direct-user-message",
        )
        before = repository_snapshot(self.fixture.program_root)

        with self.assertRaisesRegex(ValueError, "setup activation authority"):
            ACTIVATION.start_first_increment(
                self.fixture.program_root,
                intent,
                self.observation(),
            )

        self.assertEqual(repository_snapshot(self.fixture.program_root), before)
        self.assertEqual(
            (self.fixture.program_root / "state/increment-grants.jsonl").read_bytes(),
            b"",
        )

    def test_every_setup_activation_prefix_is_retry_safe(self) -> None:
        for label in (
            "setup-activation-decision",
            "program-approval",
            "workspace-approval",
            "active-waiting-status",
        ):
            with self.subTest(label=label):
                self.tearDown()
                self.setUp()

                def fail_after(persisted: str) -> None:
                    if persisted == label:
                        raise RuntimeError(f"injected-after:{label}")

                decision = self.setup_decision()
                with mock.patch.object(
                    ACTIVATION,
                    "_after_persist",
                    side_effect=fail_after,
                ):
                    with self.assertRaisesRegex(RuntimeError, "injected-after"):
                        ACTIVATION.activate_program(
                            self.fixture.program_root,
                            decision,
                            self.observation(),
                        )
                recovered = ACTIVATION.activate_program(
                    self.fixture.program_root,
                    decision,
                    self.observation(),
                )
                self.assertTrue(recovered.recovered)
                self.assertEqual(
                    json.loads(
                        (self.fixture.program_root / "state/status.json").read_text()
                    )["current_increment_state"],
                    "awaiting-first-increment",
                )

    def test_fresh_task_start_persists_v2_grant_then_preparing_status(self) -> None:
        activation = ACTIVATION.activate_program(
            self.fixture.program_root,
            self.setup_decision(),
            self.observation(),
        )
        intent = SETUP.adapt_increment_start_intent(
            self.fixture.program_root,
            activation.handoff,
            role="user",
            provenance="direct-user-message",
        )
        receipt = ACTIVATION.start_first_increment(
            self.fixture.program_root,
            intent,
            self.observation(),
        )
        grants = [
            json.loads(line)
            for line in (
                self.fixture.program_root / "state/increment-grants.jsonl"
            ).read_text().splitlines()
        ]
        status = json.loads(
            (self.fixture.program_root / "state/status.json").read_text()
        )
        self.assertEqual(len(grants), 1)
        self.assertEqual(grants[0]["schema_version"], "implementation-increment-grant/v2")
        self.assertEqual(grants[0]["grant_kind"], "first-increment-start")
        self.assertEqual(status["state_sequence"], 2)
        self.assertEqual(status["current_increment_state"], "preparing")
        self.assertEqual(receipt.increment_grant_id, grants[0]["grant_id"])
        self.assertEqual(
            STATE.validate_state_authority(
                self.fixture.program_root, self.normalized_observation()
            ),
            [],
        )

    def test_every_first_start_prefix_is_retry_safe(self) -> None:
        for label in ("first-increment-grant", "first-increment-status"):
            with self.subTest(label=label):
                self.tearDown()
                self.setUp()
                activation = ACTIVATION.activate_program(
                    self.fixture.program_root,
                    self.setup_decision(),
                    self.observation(),
                )
                intent = SETUP.adapt_increment_start_intent(
                    self.fixture.program_root,
                    activation.handoff,
                    role="user",
                    provenance="direct-user-message",
                )

                def fail_after(persisted: str) -> None:
                    if persisted == label:
                        raise RuntimeError(f"injected-after:{label}")

                with mock.patch.object(
                    ACTIVATION, "_after_persist", side_effect=fail_after
                ):
                    with self.assertRaisesRegex(RuntimeError, "injected-after"):
                        ACTIVATION.start_first_increment(
                            self.fixture.program_root,
                            intent,
                            self.observation(),
                        )
                recovered = ACTIVATION.start_first_increment(
                    self.fixture.program_root, intent, self.observation()
                )
                self.assertTrue(recovered.recovered)
                self.assertEqual(recovered.increment_state, "preparing")

    def test_non_reused_activation_gate_is_durable_before_approval_receipts(self) -> None:
        self.tearDown()
        self.fixture = BootstrapFixture()
        gate = gate_definition()
        gate["source_sha256"] = self.fixture.source_sha256
        self.fixture.configure_setup_v3(source_gate_definitions=(gate,))
        BOOTSTRAP.publish_program_proposal(
            self.fixture.repository,
            self.fixture.source_plan,
            self.fixture.candidate,
            self.fixture.source_sha256,
        )
        decision = self.setup_decision()

        with self.assertRaisesRegex(ValueError, "not durably satisfied"):
            ACTIVATION.activate_program(
                self.fixture.program_root, decision, self.observation()
            )
        self.assertEqual(
            (self.fixture.program_root / "state/approvals.jsonl").read_bytes(), b""
        )
        status_path = self.fixture.program_root / "state/status.json"
        adapter = SETUP.adapt_source_gate_decision(
            self.fixture.program_root,
            gate["gate_id"],
            gate["protected_subject"],
            "Yes",
            role="user",
            provenance="direct-user-message",
        )
        SETUP.persist_source_gate_decision(
            self.fixture.program_root,
            adapter,
            status_sha256=ACTIVATION.sha256_file(status_path),
            status_sequence=0,
            workspace_observation=ACTIVATION._observation_value(
                self.normalized_observation()
            ),
            boundary_authority={"setup_adapter_id": decision["adapter_id"]},
        )

        receipt = ACTIVATION.activate_program(
            self.fixture.program_root, decision, self.observation()
        )

        self.assertEqual(receipt.increment_state, "awaiting-first-increment")
        approval = json.loads(
            (self.fixture.program_root / "state/approvals.jsonl")
            .read_text()
            .splitlines()[0]
        )
        self.assertEqual(
            approval["source_gate_satisfaction"]["entries"][0]["gate_id"],
            gate["gate_id"],
        )

    def test_action_authorization_gate_blocks_the_plan_action_record(self) -> None:
        gate = self.reset_with_gate(
            "before-action-authorization", "increment:ARCHIVE-INDEX"
        )
        self.activate_and_start()
        plan = _exact_plan_bytes(
            self.fixture.program_root, self.normalized_observation()
        )
        prepared = ACTIVATION.prepare_exact_plan(
            self.fixture.program_root, plan, self.observation()
        )
        with self.assertRaisesRegex(ValueError, "not durably satisfied"):
            ACTIVATION.materialize_exact_plan(
                self.fixture.program_root, prepared.plan_prompt, self.observation()
            )
        self.assertTrue(
            (
                self.fixture.program_root
                / "increments/ARCHIVE-INDEX/execution-baseline.json"
            ).is_file()
        )
        self.assertEqual(
            (self.fixture.program_root / "state/action-authorizations.jsonl").read_bytes(),
            b"",
        )
        status = json.loads(
            (self.fixture.program_root / "state/status.json").read_text()
        )
        self.persist_gate(gate, status["current_increment_authority_binding"])

        materialized = ACTIVATION.materialize_exact_plan(
            self.fixture.program_root, prepared.plan_prompt, self.observation()
        )

        self.assertEqual(materialized.increment_state, "authorized")

    def test_first_start_gate_binds_the_direct_start_intent_before_grant(self) -> None:
        gate = self.reset_with_gate(
            "before-increment-start", "increment:ARCHIVE-INDEX"
        )
        activation = ACTIVATION.activate_program(
            self.fixture.program_root,
            self.setup_decision(),
            self.observation(),
        )
        intent = SETUP.adapt_increment_start_intent(
            self.fixture.program_root,
            activation.handoff,
            role="user",
            provenance="direct-user-message",
        )
        with self.assertRaisesRegex(ValueError, "not durably satisfied"):
            ACTIVATION.start_first_increment(
                self.fixture.program_root, intent, self.observation()
            )
        self.assertEqual(
            (self.fixture.program_root / "state/increment-grants.jsonl").read_bytes(),
            b"",
        )
        self.persist_gate(gate, intent)

        receipt = ACTIVATION.start_first_increment(
            self.fixture.program_root, intent, self.observation()
        )

        grant = json.loads(
            (self.fixture.program_root / "state/increment-grants.jsonl")
            .read_text()
            .splitlines()[0]
        )
        self.assertEqual(receipt.increment_state, "preparing")
        self.assertEqual(grant["start_intent"], intent)
        self.assertEqual(
            grant["source_gate_satisfaction"]["entries"][0]["gate_id"],
            gate["gate_id"],
        )

    def test_first_start_revalidates_complete_setup_approval_prefix_before_write(
        self,
    ) -> None:
        def remove_program(records: list[dict[str, object]]) -> None:
            records.pop(0)

        def duplicate_program(records: list[dict[str, object]]) -> None:
            records.insert(0, copy.deepcopy(records[0]))

        def reject_program(records: list[dict[str, object]]) -> None:
            records[0]["decision"] = "rejected"

        def change_workspace_program(records: list[dict[str, object]]) -> None:
            records[1]["program_id"] = "OTHER-PROGRAM"

        def change_workspace_revision(records: list[dict[str, object]]) -> None:
            records[1]["program_revision"] = 99

        def change_workspace_setup_digest(records: list[dict[str, object]]) -> None:
            records[1]["setup_activation_decision_sha256"] = "f" * 64

        def change_program_gate_satisfaction(
            records: list[dict[str, object]],
        ) -> None:
            records[0]["source_gate_satisfaction"] = {}

        def add_workspace_forward_binding(
            records: list[dict[str, object]],
        ) -> None:
            records[1]["increment_grant_id"] = "INCREMENT-GRANT-FUTURE"

        cases = (
            ("missing-program", remove_program),
            ("duplicate-program", duplicate_program),
            ("rejected-program", reject_program),
            ("wrong-workspace-program", change_workspace_program),
            ("wrong-workspace-revision", change_workspace_revision),
            ("wrong-workspace-setup-digest", change_workspace_setup_digest),
            ("wrong-program-gate-satisfaction", change_program_gate_satisfaction),
            ("workspace-forward-binding", add_workspace_forward_binding),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                self.tearDown()
                self.setUp()
                activation = ACTIVATION.activate_program(
                    self.fixture.program_root,
                    self.setup_decision(),
                    self.observation(),
                )
                intent = SETUP.adapt_increment_start_intent(
                    self.fixture.program_root,
                    activation.handoff,
                    role="user",
                    provenance="direct-user-message",
                )
                approvals_path = (
                    self.fixture.program_root / "state/approvals.jsonl"
                )
                records = [
                    json.loads(line)
                    for line in approvals_path.read_text(encoding="utf-8").splitlines()
                ]
                mutate(records)
                approvals_path.write_bytes(
                    b"".join(ACTIVATION._canonical_json_line(item) for item in records)
                )
                before = repository_snapshot(self.fixture.program_root)

                with self.assertRaisesRegex(ValueError, "setup activation authority"):
                    ACTIVATION.start_first_increment(
                        self.fixture.program_root,
                        intent,
                        self.observation(),
                    )

                self.assertEqual(
                    repository_snapshot(self.fixture.program_root), before
                )

    def test_first_start_gate_rejects_incompletely_bound_intent_before_decision_write(
        self,
    ) -> None:
        def change_program(intent: dict[str, object]) -> None:
            intent["program_id"] = "OTHER-PROGRAM"

        def change_revision(intent: dict[str, object]) -> None:
            intent["program_revision"] = 99

        def change_increment(intent: dict[str, object]) -> None:
            intent["increment_id"] = "OTHER-INCREMENT"

        def change_brief(intent: dict[str, object]) -> None:
            intent["brief_binding"] = {
                **dict(intent["brief_binding"]),
                "sha256": "f" * 64,
            }

        def change_prompt(intent: dict[str, object]) -> None:
            intent["prompt_sha256"] = "f" * 64

        def change_provenance(intent: dict[str, object]) -> None:
            intent["provenance_class"] = "retrieved-content"

        def change_role(intent: dict[str, object]) -> None:
            intent["conversation_role"] = "assistant"

        cases = (
            ("program", change_program),
            ("revision", change_revision),
            ("increment", change_increment),
            ("brief", change_brief),
            ("prompt", change_prompt),
            ("provenance", change_provenance),
            ("role", change_role),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                gate = self.reset_with_gate(
                    "before-increment-start", "increment:ARCHIVE-INDEX"
                )
                activation = ACTIVATION.activate_program(
                    self.fixture.program_root,
                    self.setup_decision(),
                    self.observation(),
                )
                intent = SETUP.adapt_increment_start_intent(
                    self.fixture.program_root,
                    activation.handoff,
                    role="user",
                    provenance="direct-user-message",
                )
                mutate(intent)
                intent_base = dict(intent)
                intent_base.pop("intent_id")
                intent["intent_id"] = SETUP.derive_identifier(
                    "increment-start-intent", intent_base
                )
                before = repository_snapshot(self.fixture.program_root)

                with self.assertRaisesRegex(ValueError, "increment start intent"):
                    self.persist_gate(gate, intent)

                self.assertEqual(
                    repository_snapshot(self.fixture.program_root), before
                )

    def test_first_start_rejects_gate_boundary_authority_different_from_grant_intent_before_write(
        self,
    ) -> None:
        gate = self.reset_with_gate(
            "before-increment-start", "increment:ARCHIVE-INDEX"
        )
        activation = ACTIVATION.activate_program(
            self.fixture.program_root,
            self.setup_decision(),
            self.observation(),
        )
        intent = SETUP.adapt_increment_start_intent(
            self.fixture.program_root,
            activation.handoff,
            role="user",
            provenance="direct-user-message",
        )
        self.persist_gate(gate, intent)
        decisions_path = (
            self.fixture.program_root / "state/source-gate-decisions.jsonl"
        )
        decision = json.loads(decisions_path.read_text(encoding="utf-8"))
        boundary_authority = dict(decision["boundary_authority"])
        boundary_authority["prompt_sha256"] = "f" * 64
        intent_base = dict(boundary_authority)
        intent_base.pop("intent_id")
        boundary_authority["intent_id"] = SETUP.derive_identifier(
            "increment-start-intent", intent_base
        )
        decision["boundary_authority"] = boundary_authority
        decision_base = dict(decision)
        decision_base.pop("decision_id")
        decision["decision_id"] = SETUP.derive_identifier(
            "source-gate-decision", decision_base
        )
        decisions_path.write_bytes(ACTIVATION._canonical_json_line(decision))
        before = repository_snapshot(self.fixture.program_root)

        with self.assertRaisesRegex(ValueError, "boundary authority"):
            ACTIVATION.start_first_increment(
                self.fixture.program_root,
                intent,
                self.observation(),
            )

        self.assertEqual(repository_snapshot(self.fixture.program_root), before)

    def test_product_and_review_gates_bind_their_status_transitions(self) -> None:
        for trigger, target in (
            ("before-product-execution", "implementing"),
            ("before-review", "reviewing"),
        ):
            with self.subTest(trigger=trigger):
                gate = self.reset_with_gate(trigger, "increment:ARCHIVE-INDEX")
                self.authorize_current_plan()
                if target == "reviewing":
                    ACTIVATION.advance_execution_state(
                        self.fixture.program_root,
                        "implementing",
                        self.observation(),
                    )
                    for relative in (
                        "archive-output.txt",
                        "reviews/architecture.json",
                        "reviews/requirements.json",
                        "reviews/test-evidence.json",
                    ):
                        path = self.fixture.repository / relative
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text("{}\n" if path.suffix == ".json" else "ok\n")
                status_path = self.fixture.program_root / "state/status.json"
                before = status_path.read_bytes()
                with self.assertRaisesRegex(ValueError, "not durably satisfied"):
                    ACTIVATION.advance_execution_state(
                        self.fixture.program_root, target, self.observation()
                    )
                self.assertEqual(status_path.read_bytes(), before)
                status = json.loads(status_path.read_text())
                self.persist_gate(gate, status["execution_authorization"])

                receipt = ACTIVATION.advance_execution_state(
                    self.fixture.program_root, target, self.observation()
                )

                current = json.loads(status_path.read_text())
                self.assertEqual(receipt.increment_state, target)
                self.assertEqual(
                    current["source_gate_satisfaction"]["trigger"], trigger
                )

    def test_stale_first_start_intent_is_rejected_before_write(self) -> None:
        activation = ACTIVATION.activate_program(
            self.fixture.program_root,
            self.setup_decision(),
            self.observation(),
        )
        intent = SETUP.adapt_increment_start_intent(
            self.fixture.program_root,
            activation.handoff,
            role="user",
            provenance="direct-user-message",
        )
        intent["waiting_status_sha256"] = "f" * 64
        before = (
            self.fixture.program_root / "state/increment-grants.jsonl"
        ).read_bytes()
        with self.assertRaisesRegex(ValueError, "intent"):
            ACTIVATION.start_first_increment(
                self.fixture.program_root,
                intent,
                self.observation(),
            )
        self.assertEqual(
            (self.fixture.program_root / "state/increment-grants.jsonl").read_bytes(),
            before,
        )

    def test_v3_first_start_reaches_plan_authority_without_product_execution(self) -> None:
        activation = ACTIVATION.activate_program(
            self.fixture.program_root,
            self.setup_decision(),
            self.observation(),
        )
        intent = SETUP.adapt_increment_start_intent(
            self.fixture.program_root,
            activation.handoff,
            role="user",
            provenance="direct-user-message",
        )
        ACTIVATION.start_first_increment(
            self.fixture.program_root, intent, self.observation()
        )
        plan = _exact_plan_bytes(
            self.fixture.program_root, self.normalized_observation()
        )

        prepared = ACTIVATION.prepare_exact_plan(
            self.fixture.program_root, plan, self.observation()
        )
        materialized = ACTIVATION.materialize_exact_plan(
            self.fixture.program_root,
            prepared.plan_prompt,
            self.observation(),
        )

        approvals = [
            json.loads(line)
            for line in (
                self.fixture.program_root / "state/approvals.jsonl"
            ).read_text().splitlines()
        ]
        actions = [
            json.loads(line)
            for line in (
                self.fixture.program_root / "state/action-authorizations.jsonl"
            ).read_text().splitlines()
        ]
        self.assertEqual(prepared.increment_state, "awaiting-plan-approval")
        self.assertEqual(materialized.increment_state, "authorized")
        self.assertEqual(approvals[-1]["schema_version"], "implementation-approval/v2")
        self.assertEqual(
            actions[-1]["schema_version"],
            "implementation-action-authorization/v2",
        )
        self.assertEqual(
            actions[-1]["source_gate_satisfaction"]["trigger"],
            "before-action-authorization",
        )
        self.assertFalse((self.fixture.repository / "archive-output.txt").exists())

    def test_exact_plan_rejects_changed_operation_envelope_path_facts(self) -> None:
        self.activate_and_start()
        hard_link = self.fixture.root / "catalog-hard-link.txt"
        hard_link.hardlink_to(self.fixture.repository / "catalog.txt")
        plan = _exact_plan_bytes(
            self.fixture.program_root, self.normalized_observation()
        )

        with self.assertRaisesRegex(
            ValueError, "setup-approved operation envelope observation"
        ):
            ACTIVATION.prepare_exact_plan(
                self.fixture.program_root, plan, self.observation()
            )

    def test_v3_blocked_recovery_uses_the_v3_action_family(self) -> None:
        self.authorize_current_plan()
        ACTIVATION.advance_execution_state(
            self.fixture.program_root, "implementing", self.observation()
        )
        observation = self.normalized_observation()
        BLOCKED.block_current_program(
            self.fixture.program_root,
            BLOCKED.BlockedTransitionRequest(
                reason_code="verification-environment-unavailable",
                recovery_criteria=("The verification environment is available.",),
                evidence_bindings=(
                    BLOCKED.EvidenceBinding(
                        path="catalog.txt",
                        sha256=BLOCKED.sha256_file(
                            self.fixture.repository / "catalog.txt"
                        ),
                    ),
                ),
            ),
            observation,
        )
        blocked_status = json.loads(
            (self.fixture.program_root / "state/status.json").read_text()
        )
        discovered = DISCOVERY.discover_programs(self.fixture.repository)
        self.assertEqual(discovered.disposition, "blocked-recovery-ready")
        context = blocked_status["blocked_context"]
        candidate = {
            "schema_version": BLOCKED.BLOCK_RESOLUTION_CANDIDATE_SCHEMA,
            "block_id": context["block_id"],
            "criterion_results": [
                {"criterion": criterion, "satisfied": True}
                for criterion in context["recovery_criteria"]
            ],
            "evidence_bindings": context["evidence_bindings"],
        }
        prompt = BLOCKED.render_block_resolution_prompt(
            self.fixture.program_root, candidate, observation
        )

        receipt = BLOCKED.persist_blocked_resolution(
            self.fixture.program_root, prompt, observation
        )

        actions = [
            json.loads(line)
            for line in (
                self.fixture.program_root / "state/action-authorizations.jsonl"
            ).read_text().splitlines()
        ]
        self.assertEqual(receipt.increment_state, "implementing")
        self.assertEqual(
            actions[-1]["schema_version"],
            "implementation-action-authorization/v2",
        )
        self.assertEqual(
            STATE.validate_state_authority(
                self.fixture.program_root, self.normalized_observation()
            ),
            [],
        )

    def test_diff_and_closure_gates_bind_v2_receipts_and_status_last(self) -> None:
        self.tearDown()
        self.fixture = BootstrapFixture()
        diff_gate = gate_definition(
            "SOURCE-GATE-DIFF", "before-diff-disposition"
        )
        diff_gate["source_sha256"] = self.fixture.source_sha256
        diff_gate["protected_subject"] = "increment:ARCHIVE-INDEX"
        closure_gate = gate_definition(
            "SOURCE-GATE-CLOSURE", "before-program-closure"
        )
        closure_gate["source_sha256"] = self.fixture.source_sha256
        closure_gate["protected_subject"] = "program:ARCHIVE-PROGRAM"
        self.fixture.configure_setup_v3(
            source_gate_definitions=(closure_gate, diff_gate)
        )
        BOOTSTRAP.publish_program_proposal(
            self.fixture.repository,
            self.fixture.source_plan,
            self.fixture.candidate,
            self.fixture.source_sha256,
        )
        self.authorize_current_plan()
        ACTIVATION.advance_execution_state(
            self.fixture.program_root, "implementing", self.observation()
        )
        (self.fixture.repository / "archive-output.txt").write_text(
            "archive output\n", encoding="utf-8"
        )
        write_raw_review_reports(self.fixture.repository)
        product_observation = self.observation()
        ACTIVATION.advance_execution_state(
            self.fixture.program_root, "reviewing", product_observation
        )
        REVIEW.persist_review_preparation(
            self.fixture.program_root, product_observation
        )
        with self.assertRaisesRegex(ValueError, "not durably satisfied"):
            DIFF.render_diff_disposition_prompt(self.fixture.program_root)
        status = json.loads(
            (self.fixture.program_root / "state/status.json").read_text()
        )
        self.persist_gate(diff_gate, status["execution_transition_binding"])

        diff_prompt = DIFF.render_diff_disposition_prompt(self.fixture.program_root)
        disposition = DIFF.persist_diff_disposition(
            self.fixture.program_root, diff_prompt, product_observation
        )

        self.assertEqual(disposition.increment_state, "accepted")
        diff_approval = json.loads(
            (self.fixture.program_root / "state/approvals.jsonl")
            .read_text()
            .splitlines()[-1]
        )
        self.assertEqual(
            diff_approval["schema_version"], "implementation-approval/v2"
        )
        CLOSURE.prepare_program_closure(
            self.fixture.program_root, product_observation
        )
        with self.assertRaisesRegex(ValueError, "not durably satisfied"):
            CLOSURE.render_program_closure_prompt(self.fixture.program_root)
        closure_status = json.loads(
            (self.fixture.program_root / "state/status.json").read_text()
        )
        self.persist_gate(closure_gate, closure_status["closure_binding"])

        closure_prompt = CLOSURE.render_program_closure_prompt(
            self.fixture.program_root
        )
        closed = CLOSURE.persist_program_closure(
            self.fixture.program_root, closure_prompt, product_observation
        )

        self.assertEqual(closed.program_state, "closed")
        closure_approval = json.loads(
            (self.fixture.program_root / "state/approvals.jsonl")
            .read_text()
            .splitlines()[-1]
        )
        self.assertEqual(
            closure_approval["source_gate_satisfaction"]["trigger"],
            "before-program-closure",
        )

    def test_v3_successor_rollover_uses_successor_grant_kind_and_gate_family(self) -> None:
        self.tearDown()
        self.fixture = BootstrapFixture()
        self.fixture.configure_successor_chain(("ARCHIVE-INDEX", "ARCHIVE-VERIFY"))
        successor_gate = gate_definition(
            "SOURCE-GATE-SUCCESSOR", "before-increment-start"
        )
        successor_gate["source_sha256"] = self.fixture.source_sha256
        successor_gate["protected_subject"] = "increment:ARCHIVE-VERIFY"
        self.fixture.configure_setup_v3(
            source_gate_definitions=(successor_gate,)
        )
        BOOTSTRAP.publish_program_proposal(
            self.fixture.repository,
            self.fixture.source_plan,
            self.fixture.candidate,
            self.fixture.source_sha256,
        )
        self.authorize_current_plan()
        ACTIVATION.advance_execution_state(
            self.fixture.program_root, "implementing", self.observation()
        )
        (self.fixture.repository / "archive-output.txt").write_text(
            "archive output\n", encoding="utf-8"
        )
        write_raw_review_reports(self.fixture.repository)
        product_observation = self.observation()
        ACTIVATION.advance_execution_state(
            self.fixture.program_root, "reviewing", product_observation
        )
        REVIEW.persist_review_preparation(
            self.fixture.program_root, product_observation
        )
        choices = DIFF.render_diff_disposition_prompt(self.fixture.program_root)
        continue_prompt = choices[choices.index("Accept and continue") :]

        with self.assertRaisesRegex(ValueError, "not durably satisfied"):
            DIFF.persist_diff_disposition(
                self.fixture.program_root, continue_prompt, product_observation
            )
        actions = [
            json.loads(line)
            for line in (
                self.fixture.program_root / "state/action-authorizations.jsonl"
            ).read_text().splitlines()
        ]
        self.assertEqual(actions[-1]["actions"], ["rollover-increment"])
        self.persist_gate(successor_gate, actions[-1])

        receipt = DIFF.persist_diff_disposition(
            self.fixture.program_root, continue_prompt, product_observation
        )

        status = json.loads(
            (self.fixture.program_root / "state/status.json").read_text()
        )
        grants = [
            json.loads(line)
            for line in (
                self.fixture.program_root / "state/increment-grants.jsonl"
            ).read_text().splitlines()
        ]
        self.assertEqual(receipt.successor_increment_id, "ARCHIVE-VERIFY")
        self.assertEqual(grants[-1]["grant_kind"], "successor-rollover")
        self.assertEqual(
            status["current_increment_authority_binding"]["grant_kind"],
            "successor-rollover",
        )
        self.assertEqual(status["current_increment_state"], "preparing")


if __name__ == "__main__":
    unittest.main()
