"""Application contracts for opt-in combined setup and first-increment start."""

import copy
import json
import re
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture, canonical_compact_sha256, canonical_json, repository_snapshot, run_program_discovery,
    _exact_plan_bytes, _rewrite_inherited_review_reports, write_raw_review_reports,
)
from tests.test_program_setup import (
    SETUP, BOOTSTRAP, ACTIVATION, AUTHORITY, STATE, DISCOVERY, REVIEW, DIFF, CLOSURE, gate_definition,
)


class ProgramStartContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = BootstrapFixture()
        self.fixture.configure_setup_v3()
        self.fixture.configure_combined_start()
        self.root = self.fixture.candidate

    def tearDown(self):
        self.fixture.close()

    def decision(self, reply="Start the first increment", **kwargs):
        return SETUP.adapt_program_start_decision(
            self.root, reply, role=kwargs.get("role", "user"),
            provenance=kwargs.get("provenance", "direct-user-message"),
            checkpoint=kwargs.get("checkpoint", SETUP.program_start_checkpoint(self.root)),
        )

    def test_direct_start_is_the_only_combined_consent_and_calls_are_pure(self):
        before = repository_snapshot(self.fixture.root)
        for reply in ("Start the first increment", "  START the FIRST\n increment  "):
            self.assertEqual(SETUP.validate_program_start_decision(self.root, self.decision(reply)), [])
        for reply in ("Yes", "proceed", "Start the first increment if tests pass", '"Start the first increment"', "No"):
            self.assertTrue(SETUP.validate_program_start_decision(self.root, self.decision(reply)))
        for kwargs in ({"role": "assistant"}, {"provenance": "retrieved-content"}):
            self.assertTrue(SETUP.validate_program_start_decision(self.root, self.decision(**kwargs)))
        self.assertEqual(repository_snapshot(self.fixture.root), before)

    def test_manifest_eligibility_is_explicit_and_closed(self):
        for value in (None, "unknown", {}, False):
            with self.subTest(value=value):
                manifest = self.fixture.load_json("manifest.json")
                manifest["program_start_contract"] = value
                self.fixture.write_json("manifest.json", manifest)
                before = repository_snapshot(self.fixture.root)
                self.assertTrue(SETUP.validate_setup_semantics(self.root))
                with self.assertRaises(ValueError):
                    BOOTSTRAP.publish_program_proposal(self.fixture.repository, self.fixture.source_plan, self.root, self.fixture.source_sha256)
                self.assertEqual(repository_snapshot(self.fixture.root), before)
        manifest.pop("program_start_contract")
        self.fixture.write_json("manifest.json", manifest)
        self.assertEqual(SETUP.validate_setup_semantics(self.root), [])
        with self.assertRaises(ValueError):
            SETUP.program_start_checkpoint(self.root)

    def test_presented_checkpoint_and_closed_decision_reject_drift(self):
        checkpoint = SETUP.program_start_checkpoint(self.root)
        for key, value in (("state_sequence", False), ("first_increment_id", "OTHER"), ("renderer_version", 2), ("summary_sha256", "0" * 64)):
            changed = copy.deepcopy(checkpoint)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.decision(checkpoint=changed)
        decision = self.decision()
        decision["extra"] = "not authority"
        self.assertTrue(SETUP.validate_program_start_decision(self.root, decision))
        brief = self.root / checkpoint["brief_binding"]["path"]
        brief.write_text("Changed first brief\n")
        before = repository_snapshot(self.fixture.root)
        with self.assertRaises(ValueError):
            self.decision(checkpoint=checkpoint)
        self.assertEqual(repository_snapshot(self.fixture.root), before)

    def test_checkpoint_binds_actual_program_source_metadata_and_renderer_bytes(self):
        manifest = self.fixture.load_json("manifest.json")
        for role in ("approved_program", "source_metadata", "canonical_source_snapshot", "traceability"):
            with self.subTest(role=role):
                checkpoint = SETUP.program_start_checkpoint(self.root)
                path = self.root / manifest["logical_roles"][role]
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                try:
                    with self.assertRaises(ValueError):
                        self.decision(checkpoint=checkpoint)
                finally:
                    path.write_bytes(original)
        checkpoint = SETUP.program_start_checkpoint(self.root)
        summary = SETUP.render_program_start_summary(self.root)
        with mock.patch.object(SETUP, "render_program_start_summary", return_value=summary + "\nChanged renderer"):
            with self.assertRaises(ValueError):
                self.decision(checkpoint=checkpoint)

    def test_older_manifest_family_rejects_combined_marker_before_publication(self):
        fixture = BootstrapFixture()
        self.addCleanup(fixture.close)
        fixture.configure_combined_start()
        before = repository_snapshot(fixture.root)
        with self.assertRaises(ValueError):
            BOOTSTRAP.publish_program_proposal(fixture.repository, fixture.source_plan, fixture.candidate, fixture.source_sha256)
        self.assertEqual(repository_snapshot(fixture.root), before)

    def test_summary_is_ephemeral_and_explains_modes_and_delete(self):
        for mode in ("approval:standard", "approval:pre-approve", "approval:full-increment"):
            self.fixture.configure_approval_mode(mode)
            self.fixture.configure_delete_setup_v2()
            self.fixture.configure_combined_start()
            before = repository_snapshot(self.fixture.root)
            summary = SETUP.render_program_start_summary(self.root)
            self.assertIn("Start the first increment", summary)
            self.assertIn("catalog.txt", summary)
            self.assertIn("obsolete", summary)
            self.assertIn(mode, summary)
            self.assertIn("exact-plan", summary)
            self.assertIn("local implementation", summary)
            self.assertIn("ARCHIVE-INDEX", summary)
            decision = self.decision()
            self.assertNotIn(summary, json.dumps(decision))
            self.assertEqual(repository_snapshot(self.fixture.root), before)

    def test_changed_bytes_of_already_dirty_work_invalidate_presented_checkpoint(self):
        catalog = self.fixture.repository / "catalog.txt"
        catalog.write_text("User draft one\n")
        observation = ACTIVATION.inspect_repository(self.fixture.repository, self.fixture.head).observation
        workspace = self.fixture.load_json("state/workspace.json")
        workspace["pre_existing_work_at_selection"]["modified_paths"] = list(observation.modified_paths)
        self.fixture.write_json("state/workspace.json", workspace)
        self.fixture.configure_setup_v3()
        checkpoint = SETUP.program_start_checkpoint(self.root)
        catalog.write_text("User draft two\n")
        before = repository_snapshot(self.fixture.root)
        with self.assertRaisesRegex(ValueError, "stale"):
            self.decision(checkpoint=checkpoint)
        self.assertEqual(repository_snapshot(self.fixture.root), before)

    def test_high_allocation_summary_keeps_outcomes_gates_and_conditional_limits(self):
        self.fixture.configure_successor_chain(("ARCHIVE-INDEX", "REQUEST-CONTROL", "RETRY-WAITS", "CHECKPOINTS", "PUBLISH-RESUME"))
        gate = gate_definition(setup_reuse=True)
        gate["source_sha256"] = self.fixture.source_sha256
        self.fixture.configure_delete_setup_v2(source_gate_definitions=(gate,))
        manifest = self.fixture.load_json("manifest.json")
        semantics = manifest["setup_semantics"]
        semantics["program"].update(name="Continuous publishing resilience",
            intended_outcome="Keep publishing progress recoverable while honoring provider limits.")
        outcomes = ("Separate local search limits from provider responses.", "Handle provider request limits.",
                    "Respect retry delays and transient failures.", "Preserve progress through interruption.",
                    "Resume continuous publishing without duplicate additions.")
        for increment, outcome in zip(semantics["increments"], outcomes):
            increment["intended_outcome"] = outcome
        allocations = semantics["operation_envelope"]["allocations"]
        template = next(item for item in allocations if item["operation"] == "Create" and item["kind"] == "exact-path")
        for index in range(70):
            allocation = copy.deepcopy(template)
            allocation["path"] = f"output/check-{index}.txt"
            allocations.append(allocation)
        semantics["protections"] = ["Preserve all unrelated work and existing progress caches."]
        manifest["setup_semantics_sha256"] = canonical_compact_sha256(semantics)
        self.fixture.write_json("manifest.json", manifest)
        before = repository_snapshot(self.fixture.root)
        summary = SETUP.render_program_start_summary(self.root)
        for outcome in outcomes:
            self.assertIn(outcome, summary)
        for text in ("catalog.txt", "obsolete", "before-program-activation", "setup-reusable", "accepted predecessor", "separate approval"):
            self.assertIn(text, summary)
        self.assertNotIn("check-69.txt", summary)
        self.assertNotIn("100644", summary)
        self.assertLess(len(summary.split()), len(SETUP.render_setup_recap(self.root).split()) // 3)
        self.assertEqual(repository_snapshot(self.fixture.root), before)

    def test_conditional_delete_summary_exposes_its_predecessor_requirement(self):
        self.fixture.configure_successor_chain(("ARCHIVE-INDEX", "ARCHIVE-VERIFY"))
        self.fixture.configure_delete_setup_v2(path="archive-output.txt", increment_id="ARCHIVE-VERIFY", collision="accepted-predecessor")
        manifest = self.fixture.load_json("manifest.json")
        semantics = manifest["setup_semantics"]
        for allocation in semantics["operation_envelope"]["allocations"]:
            if allocation["path"] == "archive-output.txt" and allocation["operation"] == "Create":
                allocation["increment_ids"] = ["ARCHIVE-INDEX"]
        manifest["setup_semantics_sha256"] = canonical_compact_sha256(semantics)
        self.fixture.write_json("manifest.json", manifest)
        summary = SETUP.render_program_start_summary(self.root)
        delete_line = next(line for line in summary.splitlines() if line.startswith("Delete "))
        self.assertIn("only against accepted predecessor evidence", delete_line)

    def test_summary_links_resolve_machine_artifacts_even_with_human_source_locators(self):
        manifest = self.fixture.load_json("manifest.json")
        manifest["setup_semantics"]["sources"][0]["location"] = "Archive Plan, section on checksums"
        manifest["setup_semantics_sha256"] = canonical_compact_sha256(manifest["setup_semantics"])
        self.fixture.write_json("manifest.json", manifest)
        summary = SETUP.render_program_start_summary(self.root)
        links = re.findall(r"\]\(([^)]+)\)", summary)
        self.assertEqual(len(links), 4)
        self.assertTrue(all(Path(link).is_absolute() and Path(link).is_file() for link in links), links)

    def test_summary_and_checkpoint_are_stable_across_equivalent_root_paths(self):
        equivalent_root = self.root / ".." / self.root.name
        self.assertEqual(SETUP.render_program_start_summary(self.root),
                         SETUP.render_program_start_summary(equivalent_root))
        self.assertEqual(SETUP.program_start_checkpoint(self.root),
                         SETUP.program_start_checkpoint(equivalent_root))


class ProgramStartFixture:
    def setUp(self):
        self.fixture = BootstrapFixture()
        self.fixture.configure_setup_v3()
        self.fixture.configure_combined_start()
        self.publish()

    def publish(self):
        BOOTSTRAP.publish_program_proposal(self.fixture.repository, self.fixture.source_plan,
                                         self.fixture.candidate, self.fixture.source_sha256)
        self.root = self.fixture.program_root
        self.decision = SETUP.adapt_program_start_decision(
            self.root, "Start the first increment", role="user", provenance="direct-user-message",
            checkpoint=SETUP.program_start_checkpoint(self.root))

    def tearDown(self):
        self.fixture.close()

    def observation(self):
        return ACTIVATION.inspect_repository(self.fixture.repository, self.fixture.head).observation

    def status(self):
        return json.loads((self.root / "state/status.json").read_text())


class CombinedProgramStartTests(ProgramStartFixture, unittest.TestCase):
    def test_legacy_adapters_cannot_enter_combined_route(self):
        before = repository_snapshot(self.fixture.root)
        with self.assertRaises(ValueError):
            SETUP.adapt_setup_decision(self.root, "Yes", role="user", provenance="direct-user-message")
        self.assertEqual(repository_snapshot(self.fixture.root), before)
        receipt = ACTIVATION.activate_program(self.root, self.decision, self.observation())
        self.assertEqual(receipt.increment_state, "preparing")

    def test_one_decision_starts_without_execution_authority_and_replays_exactly(self):
        receipt = ACTIVATION.start_program(self.root, self.decision, self.observation())
        self.assertEqual(receipt.increment_state, "preparing")
        self.assertEqual(self.status()["state_sequence"], 2)
        self.assertEqual(self.status()["previous_state"]["state_sequence"], 1)
        self.assertEqual((self.root / "state/action-authorizations.jsonl").read_bytes(), b"")
        self.assertFalse((self.fixture.repository / "archive-output.txt").exists())
        before = repository_snapshot(self.fixture.root)
        replay = ACTIVATION.start_program(self.root, self.decision, self.observation())
        self.assertTrue(replay.recovered)
        self.assertEqual(repository_snapshot(self.fixture.root), before)
        self.assertEqual(STATE.validate_state_authority(self.root,
            ACTIVATION._without_owned_program_paths(self.root, self.observation())), [])

    def test_every_persistence_prefix_recovers_once(self):
        for label in ("setup-activation-decision", "program-approval", "workspace-approval",
                      "active-waiting-status", "first-increment-grant", "first-increment-status"):
            with self.subTest(label=label):
                self.tearDown()
                self.setUp()
                def interrupt(actual):
                    if actual == label:
                        raise RuntimeError(label)
                with mock.patch.object(ACTIVATION, "_after_persist", side_effect=interrupt):
                    with self.assertRaisesRegex(RuntimeError, label):
                        ACTIVATION.start_program(self.root, self.decision, self.observation())
                prefix = {path: (self.root / path).read_bytes() for path in (
                    "state/setup-activation-decision.json", "state/approvals.jsonl", "state/increment-grants.jsonl")}
                receipt = ACTIVATION.start_program(self.root, self.decision, self.observation())
                self.assertEqual(receipt.increment_state, "preparing")
                for path, payload in prefix.items():
                    self.assertTrue((self.root / path).read_bytes().startswith(payload))
                grants = (self.root / "state/increment-grants.jsonl").read_text().splitlines()
                approvals = (self.root / "state/approvals.jsonl").read_text().splitlines()
                self.assertEqual(len(grants), 1)
                self.assertEqual(len(approvals), 2)

    def test_invalid_input_and_unrelated_grant_write_nothing(self):
        for mutation in ("decision", "source", "brief", "grant", "workspace"):
            with self.subTest(mutation=mutation):
                self.tearDown()
                self.setUp()
                if mutation == "decision":
                    self.decision["checkpoint"]["renderer_version"] = 2
                elif mutation == "source":
                    (self.root / "source/implementation-plan.md").write_text("Changed source\n")
                elif mutation == "brief":
                    (self.root / self.decision["checkpoint"]["brief_binding"]["path"]).write_text("Changed brief\n")
                elif mutation == "grant":
                    (self.root / "state/increment-grants.jsonl").write_text('{"grant_id":"OTHER"}\n')
                else:
                    (self.fixture.repository / "catalog.txt").write_text("Changed protected catalog\n")
                before = repository_snapshot(self.fixture.root)
                with self.assertRaises(ValueError):
                    ACTIVATION.start_program(self.root, self.decision, self.observation())
                self.assertEqual(repository_snapshot(self.fixture.root), before)

    def test_mid_transaction_brief_drift_preserves_waiting_prefix(self):
        def drift(label):
            if label == "active-waiting-status":
                (self.root / self.decision["checkpoint"]["brief_binding"]["path"]).write_text("Changed brief\n")
        with mock.patch.object(ACTIVATION, "_after_persist", side_effect=drift):
            with self.assertRaises(ValueError):
                ACTIVATION.start_program(self.root, self.decision, self.observation())
        self.assertEqual(self.status()["state_sequence"], 1)
        self.assertEqual((self.root / "state/increment-grants.jsonl").read_bytes(), b"")

    def test_divergent_recovery_prefixes_are_preserved_without_new_authority(self):
        for boundary in ("setup-activation-decision", "active-waiting-status"):
            for mutation in ("grant", "approval", "setup-symlink", "status-bool", "brief", "decision"):
                with self.subTest(boundary=boundary, mutation=mutation):
                    self.tearDown()
                    self.setUp()
                    def interrupt(label):
                        if label == boundary:
                            raise RuntimeError(boundary)
                    with mock.patch.object(ACTIVATION, "_after_persist", side_effect=interrupt):
                        with self.assertRaises(RuntimeError):
                            ACTIVATION.start_program(self.root, self.decision, self.observation())
                    if mutation in {"grant", "approval"}:
                        name = "increment-grants" if mutation == "grant" else "approvals"
                        with (self.root / f"state/{name}.jsonl").open("ab") as ledger:
                            ledger.write(b'{"unrelated":true}\n')
                    elif mutation == "setup-symlink":
                        path = self.root / "state/setup-activation-decision.json"
                        target = self.fixture.root / "retained-setup.json"
                        path.rename(target)
                        path.symlink_to(target)
                    elif mutation == "status-bool":
                        status = self.status()
                        status["state_sequence"] = bool(status["state_sequence"])
                        (self.root / "state/status.json").write_bytes(canonical_json(status))
                    elif mutation == "brief":
                        (self.root / self.decision["checkpoint"]["brief_binding"]["path"]).write_text("Drift\n")
                    else:
                        self.decision["response_sha256"] = "0" * 64
                    before = repository_snapshot(self.fixture.root)
                    with self.assertRaises(ValueError):
                        ACTIVATION.start_program(self.root, self.decision, self.observation())
                    self.assertEqual(repository_snapshot(self.fixture.root), before)
                    if mutation != "decision":
                        result = run_program_discovery(self.fixture.repository)
                        self.assertIn(result["disposition"], {"invalid", "program-activation-recovery-required", "proposal-publication-recovery-required"}, result)
                        self.assertEqual(repository_snapshot(self.fixture.root), before)


class ProgramStartAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = BootstrapFixture()
        self.fixture.configure_setup_v3()
        self.fixture.configure_combined_start()
        BOOTSTRAP.publish_program_proposal(self.fixture.repository, self.fixture.source_plan,
                                         self.fixture.candidate, self.fixture.source_sha256)
        self.root = self.fixture.program_root
        self.manifest = json.loads((self.root / "manifest.json").read_text())
        self.decision = SETUP.adapt_program_start_decision(
            self.root, "Start the first increment", role="user", provenance="direct-user-message",
            checkpoint=SETUP.program_start_checkpoint(self.root))
        # Construct a synthetic durable record independently of the new writer.
        checkpoint = self.decision["checkpoint"]
        observation = ACTIVATION._without_owned_program_paths(self.root,
            ACTIVATION.inspect_repository(self.fixture.repository, self.fixture.head).observation)
        record = ACTIVATION._build_v3_setup_record(self.root, self.manifest, {
            "adapter_id": self.decision["decision_id"], "recap_checkpoint": checkpoint,
            "presented_integrity_identity": checkpoint["presented_integrity_identity"],
            "provenance_class": "direct-user-message",
        }, observation, checkpoint["status_sha256"], 0)
        record.update(schema_version="setup-activation-decision/v3",
                      program_start_decision=self.decision,
                      setup_adapter_sha256=SETUP.value_sha256(self.decision))
        record.pop("decision_id")
        record["decision_id"] = SETUP.derive_identifier("setup-activation-decision", record)
        self.record = record
        self.record_path = self.root / self.manifest["logical_roles"]["setup_activation_decision"]

    def tearDown(self):
        self.fixture.close()

    def waiting(self):
        self.record_path.write_bytes(canonical_json(self.record))
        satisfaction = SETUP.source_gate_satisfaction(self.root, "before-program-activation", "program:ARCHIVE-PROGRAM")
        program, workspace, status = ACTIVATION._v3_activation_candidates(
            self.root, self.manifest, self.record, AUTHORITY.sha256_file(self.record_path), satisfaction,
            self.root / self.manifest["logical_roles"]["workspace"])
        (self.root / self.manifest["logical_roles"]["approvals"]).write_bytes(
            b"".join(SETUP.canonical_identity_bytes(item) + b"\n" for item in (program, workspace)))
        (self.root / self.manifest["logical_roles"]["status"]).write_bytes(canonical_json(status))

    def test_durable_record_validates_nested_decision_and_preserves_proposal(self):
        self.assertEqual(SETUP._setup_activation_record_issues(self.root, self.manifest, self.record), [])
        for field, value in (("schema_version", "setup-activation-decision/v1"),
                             ("proposal_status_sequence", False), ("setup_adapter_sha256", "0" * 64)):
            changed = copy.deepcopy(self.record)
            changed[field] = value
            changed.pop("decision_id")
            changed["decision_id"] = SETUP.derive_identifier("setup-activation-decision", changed)
            self.assertTrue(SETUP._setup_activation_record_issues(self.root, self.manifest, changed))
        self.waiting()
        self.assertEqual(SETUP.validate_setup_activation_authority(self.root), [])
        self.assertEqual(AUTHORITY.validate_program_authority(self.root), [])
        observation = ACTIVATION._without_owned_program_paths(self.root,
            ACTIVATION.inspect_repository(self.fixture.repository, self.fixture.head).observation)
        self.assertEqual(STATE.validate_state_authority(self.root, observation), [])
        self.assertEqual(self.record["proposal_status_sha256"], self.decision["checkpoint"]["status_sha256"])
        self.record["program_start_decision"]["requested_actions"] = ["approve-program-setup"]
        self.assertTrue(SETUP._setup_activation_record_issues(self.root, self.manifest, self.record))

    def test_derived_intent_has_durable_provenance_and_strict_waiting_binding(self):
        self.waiting()
        before = repository_snapshot(self.fixture.root)
        intent = SETUP.derive_program_start_intent(self.root)
        self.assertEqual(intent["schema_version"], "increment-start-intent/v2")
        self.assertEqual(intent["provenance_class"], "derived-program-start-decision")
        self.assertNotIn("conversation_role", intent)
        self.assertNotIn("prompt_sha256", intent)
        self.assertEqual(SETUP.validate_increment_start_intent(self.root, intent), [])
        for field, value in (("waiting_status_sequence", True), ("waiting_status_sha256", "0" * 64),
                             ("program_start_decision_id", "OTHER"), ("increment_id", "OTHER")):
            changed = copy.deepcopy(intent)
            changed[field] = value
            changed.pop("intent_id")
            changed["intent_id"] = SETUP.derive_identifier("increment-start-intent", changed)
            self.assertTrue(SETUP.validate_increment_start_intent(self.root, changed))
        self.assertEqual(repository_snapshot(self.fixture.root), before)


class ProgramStartDiscoveryTests(ProgramStartFixture, unittest.TestCase):

    def test_pristine_and_interrupted_prefixes_are_read_only_in_a_fresh_process(self):
        for label in (None, "setup-activation-decision", "program-approval", "workspace-approval",
                      "active-waiting-status", "first-increment-grant", "first-increment-status"):
            with self.subTest(label=label):
                self.tearDown()
                self.setUp()
                if label:
                    def interrupt(actual):
                        if actual == label:
                            raise RuntimeError(label)
                    with mock.patch.object(ACTIVATION, "_after_persist", side_effect=interrupt):
                        with self.assertRaises(RuntimeError):
                            ACTIVATION.start_program(self.root, self.decision, self.observation())
                before = repository_snapshot(self.fixture.root)
                result = run_program_discovery(self.fixture.repository)
                expected = "resume" if label == "first-increment-status" else "program-start-retry-ready" if label else "program-start-ready"
                self.assertEqual(result["disposition"], expected, result)
                self.assertEqual(result["required_input"], "program-start-decision" if label is None else None)
                self.assertEqual(repository_snapshot(self.fixture.root), before)

    def test_publication_and_launch_have_separate_output_only_summary_identity(self):
        from tests.script_module_support import load_script_module
        from tests.test_program_setup import SCRIPT_ROOT
        launch = load_script_module("program_launch", SCRIPT_ROOT / "program_launch.py")
        receipt = BOOTSTRAP.publish_program_proposal(self.fixture.repository, self.fixture.source_plan,
                                                     self.fixture.candidate, self.fixture.source_sha256)
        self.assertIsNone(receipt.setup_recap_sha256)
        self.assertEqual(receipt.program_start_summary_sha256, self.decision["checkpoint"]["summary_sha256"])
        before = repository_snapshot(self.fixture.root)
        self.assertEqual(launch.render_program_launch_prompt(self.root), SETUP.render_program_start_summary(self.root))
        self.assertEqual(repository_snapshot(self.fixture.root), before)
        self.assertFalse(any("recap" in path.name or "summary" in path.name for path in self.root.rglob("*")))


class ProgramStartLifecycleTests(ProgramStartFixture, unittest.TestCase):
    def configure(self, *, delete=False, mode="approval:standard", gates=(), successors=False):
        self.fixture.close()
        self.fixture = BootstrapFixture()
        if successors:
            self.fixture.configure_successor_chain(("ARCHIVE-INDEX", "ARCHIVE-VERIFY"))
            # This supported closure fixture verifies every requirement again in
            # the final increment; accepted-chain attribution is a separate feature.
            traceability = self.fixture.load_json("program/traceability.json")
            for requirement in traceability["atomic_requirements"]:
                if "ARCHIVE-VERIFY" not in requirement["assigned_increments"]:
                    requirement["assigned_increments"].append("ARCHIVE-VERIFY")
            digest = AUTHORITY.compute_semantic_requirements_digest(traceability["atomic_requirements"])
            traceability["coverage_assertion"]["semantic_requirements_sha256"] = digest
            self.fixture.write_json("program/traceability.json", traceability)
            manifest = self.fixture.load_json("manifest.json")
            manifest["program_binding"]["traceability_sha256"] = AUTHORITY.sha256_file(self.fixture.candidate / "program/traceability.json")
            self.fixture.write_json("manifest.json", manifest)
            status = self.fixture.load_json("state/status.json")
            status["program_binding"]["semantic_requirements_sha256"] = digest
            self.fixture.write_json("state/status.json", status)
        self.fixture.configure_approval_mode(mode)
        for gate in gates:
            gate["source_sha256"] = self.fixture.source_sha256
        configure = self.fixture.configure_delete_setup_v2 if delete else self.fixture.configure_setup_v3
        configure(source_gate_definitions=gates)
        self.fixture.configure_combined_start()
        self.publish()

    def persist_gate(self, gate, boundary):
        path = self.root / "state/status.json"
        adapter = SETUP.adapt_source_gate_decision(self.root, gate["gate_id"], gate["protected_subject"],
            "Yes", role="user", provenance="direct-user-message")
        return SETUP.persist_source_gate_decision(self.root, adapter,
            status_sha256=AUTHORITY.sha256_file(path), status_sequence=self.status()["state_sequence"],
            workspace_observation=ACTIVATION._observation_value(
                ACTIVATION._without_owned_program_paths(self.root, self.observation())), boundary_authority=boundary,
            exact_plan_sha256=self.status().get("approved_exact_file_plan_sha256"),
            execution_baseline_sha256=self.status().get("execution_baseline_binding", {}).get("sha256"))

    def test_setup_reuse_does_not_bypass_delete_execution_gate(self):
        reused = gate_definition("GATE-SETUP", setup_reuse=True)
        product = gate_definition("GATE-DELETE", "before-product-execution")
        product["protected_subject"] = "increment:ARCHIVE-INDEX"
        self.configure(delete=True, mode="approval:full-increment", gates=(reused, product))
        ACTIVATION.start_program(self.root, self.decision, self.observation())
        self.assertEqual((self.root / "state/source-gate-decisions.jsonl").read_bytes(), b"")
        self.authorize()
        before = repository_snapshot(self.fixture.root)
        with self.assertRaisesRegex(ValueError, "not durably satisfied"):
            ACTIVATION.advance_execution_state(self.root, "implementing", self.observation())
        self.assertEqual(repository_snapshot(self.fixture.root), before)
        self.persist_gate(product, self.status()["execution_authorization"])
        ACTIVATION.advance_execution_state(self.root, "implementing", self.observation())
        self.assertFalse((self.fixture.repository / "catalog.txt").exists())

    def test_source_gate_pauses_and_interrupted_gate_records_recover_in_order(self):
        for delete in (False, True):
            gates = [gate_definition("GATE-A"), gate_definition("GATE-B"),
                     gate_definition("GATE-C", "before-increment-start")]
            gates[-1]["protected_subject"] = "increment:ARCHIVE-INDEX"
            self.configure(delete=delete, gates=gates)
            for index, gate in enumerate(gates):
                with self.subTest(delete=delete, gate=gate["gate_id"]):
                    with self.assertRaisesRegex(ValueError, "not durably satisfied"):
                        ACTIVATION.start_program(self.root, self.decision, self.observation())
                    self.assertEqual(self.status()["state_sequence"], 0 if index < 2 else 1)
                    self.assertEqual((self.root / "state/increment-grants.jsonl").read_bytes(), b"")
                    before = repository_snapshot(self.fixture.root)
                    discovered = run_program_discovery(self.fixture.repository)
                    self.assertEqual(discovered["disposition"], "source-gate-approval-ready", discovered)
                    self.assertEqual(repository_snapshot(self.fixture.root), before)
                    setup = json.loads((self.root / "state/setup-activation-decision.json").read_text())
                    boundary = ({"setup_adapter_id": setup["setup_adapter_id"]} if index < 2
                                else SETUP.derive_program_start_intent(self.root))
                    append = SETUP.atomic_append_json_line
                    def interrupt(*args, **kwargs):
                        append(*args, **kwargs)
                        raise RuntimeError("gate persisted")
                    with mock.patch.object(SETUP, "atomic_append_json_line", side_effect=interrupt):
                        with self.assertRaisesRegex(RuntimeError, "gate persisted"):
                            self.persist_gate(gate, boundary)
                    before = repository_snapshot(self.fixture.root)
                    self.assertTrue(self.persist_gate(gate, boundary)["recovered"])
                    self.assertEqual(repository_snapshot(self.fixture.root), before)
            receipt = ACTIVATION.start_program(self.root, self.decision, self.observation())
            self.assertEqual(receipt.increment_state, "preparing")
            self.assertTrue((self.fixture.repository / "catalog.txt").exists())

    def test_initial_source_gates_revalidate_protected_bytes_and_selected_workspace(self):
        for trigger, drift in (
            (trigger, drift)
            for trigger in ("before-program-activation", "before-increment-start")
            for drift in ("protected-bytes", "new-untracked-path", "stale-supplied-observation")
        ):
            with self.subTest(trigger=trigger, drift=drift):
                self.fixture.close()
                self.fixture = BootstrapFixture()
                catalog = self.fixture.repository / "catalog.txt"
                catalog.write_text("User draft one\n")
                workspace = self.fixture.load_json("state/workspace.json")
                workspace["pre_existing_work_at_selection"]["modified_paths"] = list(self.observation().modified_paths)
                self.fixture.write_json("state/workspace.json", workspace)
                gate = gate_definition("GATE-A", trigger)
                if trigger == "before-increment-start":
                    gate["protected_subject"] = "increment:ARCHIVE-INDEX"
                gate["source_sha256"] = self.fixture.source_sha256
                self.fixture.configure_setup_v3(source_gate_definitions=(gate,))
                self.fixture.configure_combined_start()
                self.publish()
                with self.assertRaisesRegex(ValueError, "not durably satisfied"):
                    ACTIVATION.start_program(self.root, self.decision, self.observation())
                setup = json.loads((self.root / "state/setup-activation-decision.json").read_text())
                boundary = ({"setup_adapter_id": setup["setup_adapter_id"]}
                            if trigger == "before-program-activation" else SETUP.derive_program_start_intent(self.root))
                if drift == "protected-bytes":
                    catalog.write_text("User draft two\n")
                elif drift == "new-untracked-path":
                    (self.fixture.repository / "new-user-work.txt").write_text("New work\n")
                adapter = SETUP.adapt_source_gate_decision(self.root, gate["gate_id"], gate["protected_subject"],
                    "Yes", role="user", provenance="direct-user-message")
                observation = ACTIVATION._observation_value(ACTIVATION._without_owned_program_paths(self.root, self.observation()))
                if drift == "stale-supplied-observation":
                    observation["head_commit"] = "0" * 40
                before = repository_snapshot(self.fixture.root)
                with self.assertRaisesRegex(ValueError, "checkpoint binding mismatch|workspace observation"):
                    SETUP.persist_source_gate_decision(self.root, adapter,
                        status_sha256=AUTHORITY.sha256_file(self.root / "state/status.json"),
                        status_sequence=self.status()["state_sequence"],
                        workspace_observation=observation, boundary_authority=boundary)
                self.assertEqual(repository_snapshot(self.fixture.root), before)

    def authorize(self):
        plan = _exact_plan_bytes(self.root, self.observation())
        prior_actions = (self.root / "state/action-authorizations.jsonl").read_bytes()
        prepared = ACTIVATION.prepare_exact_plan(self.root, plan, self.observation())
        if self.status()["approval_mode"] == "approval:standard":
            self.assertEqual(prepared.increment_state, "awaiting-plan-approval")
            self.assertEqual((self.root / "state/action-authorizations.jsonl").read_bytes(), prior_actions)
            ACTIVATION.materialize_exact_plan(self.root, prepared.plan_prompt, self.observation())
        self.assertEqual(self.status()["current_increment_state"], "authorized")

    def review(self):
        self.authorize()
        ACTIVATION.advance_execution_state(self.root, "implementing", self.observation())
        (self.fixture.repository / "archive-output.txt").write_text(self.status()["current_increment_id"] + "\n")
        increment_id = self.status()["current_increment_id"]
        _rewrite_inherited_review_reports(self.fixture.repository, self.status(), increment_id)
        write_raw_review_reports(self.fixture.repository, increment_id=increment_id,
            relative_directory="reviews" if increment_id == "ARCHIVE-INDEX" else f"reviews/{increment_id}")
        ACTIVATION.advance_execution_state(self.root, "reviewing", self.observation())
        REVIEW.persist_review_preparation(self.root, self.observation())

    def test_both_operation_families_and_modes_preserve_later_authority_through_closure(self):
        for delete in (False, True):
            for mode in ("approval:standard", "approval:pre-approve", "approval:full-increment"):
                with self.subTest(delete=delete, mode=mode):
                    self.configure(delete=delete, mode=mode, successors=True)
                    ACTIVATION.start_program(self.root, self.decision, self.observation())
                    genesis = (self.root / "state/setup-activation-decision.json").read_bytes()
                    self.assertFalse((self.root / "increments/ARCHIVE-INDEX/execution-baseline.json").exists())
                    self.review()
                    choices = DIFF.render_diff_disposition_prompt(self.root)
                    DIFF.persist_diff_disposition(self.root, choices[choices.index("Accept and continue"):], self.observation())
                    self.assertEqual(self.status()["current_increment_id"], "ARCHIVE-VERIFY")
                    self.assertEqual(SETUP.validate_setup_activation_authority(self.root), [])
                    before = repository_snapshot(self.fixture.root)
                    with self.assertRaises(ValueError):
                        ACTIVATION.start_program(self.root, self.decision, self.observation())
                    self.assertEqual(repository_snapshot(self.fixture.root), before)
                    self.review()
                    DIFF.persist_diff_disposition(self.root, DIFF.render_diff_disposition_prompt(self.root), self.observation())
                    if delete:
                        before = repository_snapshot(self.fixture.root)
                        with self.assertRaisesRegex(ValueError, "Delete section requires setup-v2 exact-file map"):
                            CLOSURE.prepare_program_closure(self.root, self.observation())
                        self.assertEqual(repository_snapshot(self.fixture.root), before)
                    else:
                        CLOSURE.prepare_program_closure(self.root, self.observation())
                        CLOSURE.persist_program_closure(self.root, CLOSURE.render_program_closure_prompt(self.root), self.observation())
                        self.assertEqual(self.status()["program_state"], "closed")
                    self.assertEqual((self.root / "state/setup-activation-decision.json").read_bytes(), genesis)
                    self.assertEqual(SETUP.validate_setup_activation_authority(self.root), [])
                    self.assertEqual((self.fixture.repository / "catalog.txt").exists(), not delete)


if __name__ == "__main__":
    unittest.main()
