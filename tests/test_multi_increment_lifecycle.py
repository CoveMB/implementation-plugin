import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from tests import program_bootstrap_support as bootstrap_support
from tests.program_bootstrap_support import (
    BootstrapFixture,
    repository_snapshot,
    run_program_discovery,
)
from tests.test_program_setup import ACTIVATION, BOOTSTRAP, SETUP


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_PATH = REPOSITORY_ROOT / "tests/program_bootstrap_support.py"
COMPATIBILITY_FIXTURE = (
    REPOSITORY_ROOT / "tests/fixtures/program-bootstrap/v0.1.1"
)


class MultiIncrementLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BootstrapFixture()
        self.fixture.configure_successor_chain(
            ("ARCHIVE-INDEX", "ARCHIVE-VERIFY", "ARCHIVE-PUBLISH")
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def test_inherited_review_rewrite_preserves_reports_and_scope(self) -> None:
        inherited_paths = [
            "reviews/architecture.json",
            "reviews/requirements.json",
            "reviews/test-evidence.json",
        ]
        expected: dict[str, dict[str, object]] = {}
        for scope, relative in zip(
            ("architecture", "requirements", "test-evidence"),
            inherited_paths,
            strict=True,
        ):
            value = bootstrap_support.raw_review_report(scope)
            value["findings"] = [{"id": f"preserved-{scope}"}]
            path = self.fixture.repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bootstrap_support.canonical_json(value))
            expected[relative] = value
        unowned = self.fixture.repository / "reviews/unowned/requirements.json"
        unowned.parent.mkdir(parents=True)
        unowned.write_bytes(
            bootstrap_support.canonical_json(
                bootstrap_support.raw_review_report("requirements")
            )
        )
        unowned_before = unowned.read_bytes()
        status = {
            "inherited_workspace_binding": {
                "inherited_paths": inherited_paths,
            }
        }

        bootstrap_support._rewrite_inherited_review_reports(
            self.fixture.repository,
            status,
            "ARCHIVE-VERIFY",
        )

        for relative, prior in expected.items():
            with self.subTest(relative=relative):
                rewritten = json.loads(
                    (self.fixture.repository / relative).read_text(encoding="utf-8")
                )
                self.assertEqual(rewritten["increment_id"], "ARCHIVE-VERIFY")
                self.assertEqual(
                    {key: value for key, value in rewritten.items() if key != "increment_id"},
                    {key: value for key, value in prior.items() if key != "increment_id"},
                )
        self.assertEqual(unowned.read_bytes(), unowned_before)

    def run_phase(
        self,
        phase: str,
        *,
        prompt: str | None = None,
        fail_label: str | None = None,
        exact_plan: bytes | None = None,
        check: bool = True,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object] | None]:
        arguments = [
            sys.executable,
            str(SUPPORT_PATH),
            phase,
            "--repository",
            str(self.fixture.repository),
            "--candidate",
            str(self.fixture.candidate),
            "--source-plan",
            str(self.fixture.source_plan),
            "--source-sha256",
            self.fixture.source_sha256,
        ]
        if prompt is not None:
            prompt_path = self.fixture.root / f"{phase}-prompt.md"
            prompt_path.write_text(prompt, encoding="utf-8")
            arguments.extend(("--prompt-file", str(prompt_path)))
        if fail_label is not None:
            arguments.extend(("--fail-label", fail_label))
        if exact_plan is not None:
            exact_plan_path = self.fixture.root / f"{phase}-exact-plan.md"
            exact_plan_path.write_bytes(exact_plan)
            arguments.extend(("--exact-plan-file", str(exact_plan_path)))
        completed = subprocess.run(
            arguments,
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if check:
            self.assertEqual(completed.returncode, 0, completed.stderr)
        value = json.loads(completed.stdout) if completed.stdout.strip() else None
        return completed, value

    def reset_fixture(
        self,
        *,
        approval_mode: str = "approval:standard",
        with_chain: bool = True,
    ) -> None:
        self.fixture.close()
        self.fixture = BootstrapFixture()
        if with_chain:
            self.fixture.configure_successor_chain(
                ("ARCHIVE-INDEX", "ARCHIVE-VERIFY", "ARCHIVE-PUBLISH")
            )
        self.fixture.configure_approval_mode(approval_mode)

    def discover(self) -> dict[str, object]:
        return run_program_discovery(self.fixture.repository)

    def load_status(self) -> dict[str, object]:
        return json.loads(
            (self.fixture.program_root / "state/status.json").read_text(
                encoding="utf-8"
            )
        )

    def materialize_current_plan(self) -> dict[str, object]:
        _completed, prepared = self.run_phase("prepare-plan")
        assert prepared is not None
        if prepared["plan_prompt"] is not None:
            _completed, materialized = self.run_phase(
                "materialize-plan", prompt=str(prepared["plan_prompt"])
            )
            assert materialized is not None
            return materialized
        return prepared

    def advance_current_to_diff(self) -> None:
        self.materialize_current_plan()
        self.run_phase("implementing")
        self.run_phase("reviewing")
        self.run_phase("prepare-review")

    def publish_and_advance_first_to_diff(self) -> None:
        _completed, published = self.run_phase("publish")
        assert published is not None
        self.run_phase("activate", prompt=str(published["prompt"]))
        self.advance_current_to_diff()

    def rollover(self, domain: str) -> dict[str, object]:
        if domain == "immediate":
            _completed, choice = self.run_phase("render-accept-continue")
            assert choice is not None
            _completed, receipt = self.run_phase(
                "dispose-diff", prompt=str(choice["prompt"])
            )
        elif domain == "accepted-state":
            _completed, stop = self.run_phase("render-accept-stop")
            assert stop is not None
            self.run_phase("accept", prompt=str(stop["prompt"]))
            stopped = repository_snapshot(self.fixture.repository)
            self.run_phase("accept", prompt=str(stop["prompt"]))
            self.assertEqual(repository_snapshot(self.fixture.repository), stopped)
            _completed, choice = self.run_phase("render-later-continuation")
            assert choice is not None
            _completed, receipt = self.run_phase(
                "rollover", prompt=str(choice["prompt"])
            )
        else:
            raise ValueError(f"unsupported continuation domain: {domain}")
        assert receipt is not None
        return receipt

    def test_later_continuation_crosses_a_fresh_process_boundary(self) -> None:
        self.publish_and_advance_first_to_diff()
        rollover = self.rollover("accepted-state")
        self.assertEqual(rollover["successor_increment_id"], "ARCHIVE-VERIFY")

    def start_sparse_program(self, mode="approval:full-increment"):
        self.fixture.close()
        self.fixture = BootstrapFixture()
        self.fixture.configure_approval_mode(mode)
        schedule = self.fixture.configure_portable_successors()
        BOOTSTRAP.publish_program_proposal(self.fixture.repository, self.fixture.source_plan, self.fixture.candidate, self.fixture.source_sha256)
        observation = ACTIVATION.inspect_repository(self.fixture.repository, self.fixture.head).observation
        decision = SETUP.adapt_setup_decision(self.fixture.program_root, "Yes", role="user", provenance="direct-user-message")
        activation = ACTIVATION.activate_program(self.fixture.program_root, decision, observation)
        intent = SETUP.adapt_increment_start_intent(self.fixture.program_root, activation.handoff, role="user", provenance="direct-user-message")
        ACTIVATION.start_first_increment(self.fixture.program_root, intent, observation)
        return schedule

    def test_portable_nine_increment_chain_uses_both_continuation_routes(self):
        schedule = self.start_sparse_program()
        manifest_bytes = (self.fixture.program_root / "manifest.json").read_bytes()
        prefix = "implementation-programs/ARCHIVE-PROGRAM/"
        for index, current in enumerate(schedule):
            with self.subTest(current=current):
                self.assertEqual(self.load_status()["current_increment_id"], current)
                _, rendered = self.run_phase("render-exact-plan")
                paths = set(rendered["required_future_paths"])
                if index < 8:
                    self.assertIn(prefix + f"increments/{current}/handoff.md", paths)
                    self.assertIn(prefix + f"increments/{schedule[index + 1]}/brief.md", paths)
                    self.assertNotIn(prefix + "closure/reconciliation.json", paths)
                    self.advance_current_to_diff()
                    receipt = self.rollover("immediate" if index % 2 == 0 else "accepted-state")
                    self.assertEqual(receipt["successor_increment_id"], schedule[index + 1])
                    records = [json.loads(line) for line in (self.fixture.program_root / "state/rollovers.jsonl").read_text().splitlines()]
                    self.assertEqual([(row["current_increment_id"], row["successor_increment_id"]) for row in records], list(zip(schedule[:index + 1], schedule[1:index + 2])))
                    self.assertIn("archive-output.txt", self.load_status()["inherited_workspace_binding"]["inherited_paths"])
                    self.assertEqual(self.discover()["disposition"], "resume")
                else:
                    self.assertIn(prefix + "closure/reconciliation.json", paths)
                    self.assertIn(prefix + "closure/closure-packet.md", paths)
                    self.assertNotIn(prefix + f"increments/{current}/handoff.md", paths)
                    self.materialize_current_plan()
                self.assertEqual((self.fixture.program_root / "manifest.json").read_bytes(), manifest_bytes)

    def test_sparse_first_boundary_supports_later_continuation(self):
        self.start_sparse_program()
        self.advance_current_to_diff()
        receipt = self.rollover("accepted-state")
        self.assertEqual(receipt["successor_increment_id"], "ARCHIVE-VERIFY")
        self.materialize_current_plan()

    def test_completed_history_must_match_the_approved_serial_edge(self):
        from tests.test_program_rollover import ROLLOVER
        from tests.test_program_setup import AUTHORITY

        self.start_sparse_program()
        self.advance_current_to_diff()
        self.rollover("immediate")
        root = self.fixture.program_root
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        traceability_path = root / "program/traceability.json"
        traceability = json.loads(traceability_path.read_text())
        increments = manifest["setup_semantics"]["increments"]
        increments[1], increments[2] = increments[2], increments[1]
        schedule = [item["increment_id"] for item in increments]
        for index, increment in enumerate(increments):
            increment["depends_on"] = schedule[index - 1:index] if index else []
        for requirement in traceability["atomic_requirements"]:
            requirement["assigned_increments"].sort(key=schedule.index)
        semantic_digest = bootstrap_support.canonical_compact_sha256([
            {field: item[field] for field in AUTHORITY.SEMANTIC_FIELDS}
            for item in traceability["atomic_requirements"]
        ])
        traceability["coverage_assertion"]["semantic_requirements_sha256"] = semantic_digest
        traceability_path.write_bytes(bootstrap_support.canonical_json(traceability))
        manifest["program_binding"]["traceability_sha256"] = AUTHORITY.sha256_file(traceability_path)
        manifest["setup_semantics"]["bindings"]["program"].update(manifest["program_binding"], semantic_requirements_sha256=semantic_digest)
        manifest["setup_semantics_sha256"] = bootstrap_support.canonical_compact_sha256(manifest["setup_semantics"])
        manifest_path.write_bytes(bootstrap_support.canonical_json(manifest))
        self.assertEqual(SETUP.validate_setup_semantics(root), [])
        before = repository_snapshot(root)
        with self.assertRaisesRegex(ValueError, "schedule|successor"):
            ROLLOVER._validated_completed_rollover_records(root, self.load_status(), allow_unbound_suffix=False)
        self.assertEqual(repository_snapshot(root), before)

    def test_sparse_exact_plan_prefixes_are_discovered_and_replayed(self):
        cases = [
            ("approval:standard", "prepare-plan", "exact-plan"),
            ("approval:standard", "prepare-plan", "awaiting-plan-status"),
            *[("approval:standard", "materialize-plan", label) for label in ("plan-approval", "execution-baseline", "plan-action-authorization", "authorized-status")],
            *[("approval:full-increment", "prepare-plan", label) for label in ("exact-plan", "execution-baseline", "plan-action-authorization", "authorized-status")],
        ]
        for mode, phase, label in cases:
            with self.subTest(mode=mode, phase=phase, label=label):
                self.start_sparse_program(mode)
                _, rendered = self.run_phase("render-exact-plan")
                plan = rendered["plan"].encode()
                prompt = None
                if phase == "materialize-plan":
                    _, prepared = self.run_phase("prepare-plan", exact_plan=plan)
                    prompt = prepared["plan_prompt"]
                failed, _ = self.run_phase(phase, exact_plan=plan, prompt=prompt, fail_label=label, check=False)
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn("injected-after:", failed.stderr)
                expected = "plan-preparation-retry-ready" if label in {"exact-plan", "awaiting-plan-status"} else "plan-materialization-retry-ready"
                if label == "authorized-status":
                    expected = "resume"
                self.assertEqual(self.discover()["disposition"], expected)
                self.run_phase(phase, exact_plan=plan, prompt=prompt)
                before = repository_snapshot(self.fixture.repository)
                self.run_phase(phase, exact_plan=plan, prompt=prompt)
                self.assertEqual(repository_snapshot(self.fixture.repository), before)

    def test_fresh_diff_prompt_preserves_exact_rollover_record_choice(self):
        from tests.test_program_rollover import DIFF, ROLLOVER

        immutable_before = repository_snapshot(REPOSITORY_ROOT / "tests/fixtures")
        self.start_sparse_program()
        self.advance_current_to_diff()
        root = self.fixture.program_root
        manifest_before = (root / "manifest.json").read_bytes()
        original_public = DIFF.render_diff_disposition_prompt(root)
        _, choice = self.run_phase("render-accept-continue")
        prompt = choice["prompt"]
        self.assertEqual(original_public.count(prompt), 1)

        interrupted, _ = self.run_phase(
            "dispose-diff", prompt=prompt,
            fail_label="rollover-record", check=False,
        )
        self.assertEqual(interrupted.returncode, 1, interrupted.stderr)
        self.assertIn("injected-after:rollover-record", interrupted.stderr)
        self.assertEqual(self.load_status()["current_increment_state"], "accepted")
        self.assertEqual(self.load_status()["current_increment_id"], "ARCHIVE-INDEX")

        before = repository_snapshot(self.fixture.repository)
        discovered = self.discover()
        self.assertEqual(discovered["disposition"], "increment-rollover-retry-ready")
        self.assertEqual(discovered["issues"], [])
        observation = DIFF.inspect_repository(self.fixture.repository, self.fixture.head).observation
        inspection = ROLLOVER.inspect_increment_rollover(root, observation)
        self.assertEqual(inspection.disposition, "increment-rollover-retry-ready")
        self.assertEqual(inspection.issues, ())
        self.assertEqual(inspection.completed_steps, (
            "action-authorization", "successor-grant", "handoff",
            "successor-brief", "rollover-record",
        ))
        fresh_public = DIFF.render_diff_disposition_prompt(root)
        self.assertEqual(repository_snapshot(self.fixture.repository), before)
        self.assertEqual((root / "manifest.json").read_bytes(), manifest_before)
        self.assertEqual(repository_snapshot(REPOSITORY_ROOT / "tests/fixtures"), immutable_before)
        self.assertEqual(fresh_public, original_public)
        self.assertEqual(fresh_public.count(prompt), 1)
        self.assertEqual(fresh_public.count("Accept and continue to `ARCHIVE-VERIFY`."), 1)
        self.assertEqual(fresh_public.count("$implementing-staged-plans"), 2)

    def test_fresh_diff_prompt_rejects_mismatched_rollover_suffix_without_writes(self):
        from tests.test_program_rollover import DIFF, ROLLOVER

        immutable_before = repository_snapshot(REPOSITORY_ROOT / "tests/fixtures")
        self.start_sparse_program()
        self.advance_current_to_diff()
        root = self.fixture.program_root
        manifest_before = (root / "manifest.json").read_bytes()
        _, choice = self.run_phase("render-accept-continue")
        interrupted, _ = self.run_phase(
            "dispose-diff", prompt=choice["prompt"],
            fail_label="rollover-record", check=False,
        )
        self.assertEqual(interrupted.returncode, 1, interrupted.stderr)
        self.assertIn("injected-after:rollover-record", interrupted.stderr)
        rollover_path = root / "state/rollovers.jsonl"
        records = [json.loads(line) for line in rollover_path.read_text().splitlines()]
        self.assertEqual(len(records), 1)
        records[0]["successor_increment_id"] = "ARCHIVE-CATALOG"
        rollover_path.write_bytes(ROLLOVER._canonical_json_line(records[0]))

        before = repository_snapshot(self.fixture.repository)
        observation = DIFF.inspect_repository(self.fixture.repository, self.fixture.head).observation
        inspection = ROLLOVER.inspect_increment_rollover(root, observation)
        self.assertEqual(inspection.disposition, "continuation-recovery-required")
        self.assertIn("divergent rollover-record", inspection.issues)
        self.assertNotIn("rollover-record", inspection.completed_steps)
        acceptance = DIFF.build_diff_acceptance_candidate(root, observation)
        self.assertIsNone(DIFF._continuation.build_continuation_extension(root, acceptance, observation))
        rendered = DIFF.render_diff_disposition_prompt(root)
        self.assertEqual(repository_snapshot(self.fixture.repository), before)
        self.assertEqual((root / "manifest.json").read_bytes(), manifest_before)
        self.assertEqual(repository_snapshot(REPOSITORY_ROOT / "tests/fixtures"), immutable_before)
        self.assertEqual(rendered, (
            f"Accept and stop.\n\n{acceptance.prompt}\n"
            "Continuation unavailable: unbound rollover history is not lifecycle authority.\n"
        ))
        self.assertNotIn("Accept and continue", rendered)
        self.assertNotIn(choice["prompt"], rendered)
        self.assertEqual(rendered.count("$implementing-staged-plans"), 1)

    def test_sparse_acceptance_and_rollover_prefixes_replay_one_bound_transaction(self):
        labels = ("action-authorization", "successor-grant", "handoff", "successor-brief", "rollover-record", "successor-status")
        for domain in ("immediate", "accepted-state"):
            for label in (("diff-approval", "accepted-status") + labels if domain == "immediate" else labels):
                with self.subTest(domain=domain, label=label):
                    self.start_sparse_program()
                    self.advance_current_to_diff()
                    if domain == "accepted-state":
                        _, stopped = self.run_phase("render-accept-stop")
                        self.run_phase("accept", prompt=stopped["prompt"])
                    _, choice = self.run_phase("render-accept-continue" if domain == "immediate" else "render-later-continuation")
                    prompt = choice["prompt"]
                    phase = "dispose-diff" if domain == "immediate" else "rollover"
                    manifest_bytes = (self.fixture.program_root / "manifest.json").read_bytes()
                    failed, _ = self.run_phase(phase, prompt=prompt, fail_label=label, check=False)
                    self.assertNotEqual(failed.returncode, 0)
                    self.assertIn("injected-after:", failed.stderr)
                    if label == "successor-status":
                        expected = "resume"
                    elif label == "diff-approval":
                        expected = "increment-acceptance-retry-ready"
                    elif label == "accepted-status":
                        expected = "accepted-continuation-retry-ready"
                    elif label in {"action-authorization", "successor-grant"}:
                        expected = "increment-continuation-retry-ready" if domain == "immediate" else "accepted-state-continuation-retry-ready"
                    else:
                        expected = "increment-rollover-retry-ready" if domain == "immediate" else "accepted-state-rollover-retry-ready"
                    self.assertEqual(self.discover()["disposition"], expected)
                    _, receipt = self.run_phase(phase, prompt=prompt)
                    self.assertEqual(receipt["successor_increment_id"], "ARCHIVE-VERIFY")
                    self.assertFalse(receipt["requires_retry"])
                    before = repository_snapshot(self.fixture.repository)
                    self.run_phase(phase, prompt=prompt)
                    self.assertEqual(repository_snapshot(self.fixture.repository), before)
                    self.assertEqual((self.fixture.program_root / "manifest.json").read_bytes(), manifest_bytes)
                    self.assertEqual(len((self.fixture.program_root / "state/rollovers.jsonl").read_text().splitlines()), 1)
                    self.assertEqual(len((self.fixture.program_root / "state/increment-grants.jsonl").read_text().splitlines()), 2)

    def test_incompatible_closure_only_plan_and_successor_prefix_preserve_all_bytes(self):
        self.start_sparse_program()
        _, rendered = self.run_phase("render-exact-plan")
        old_plan = rendered["plan"].replace("increments/ARCHIVE-INDEX/handoff.md", "closure/reconciliation.json").replace("increments/ARCHIVE-VERIFY/brief.md", "closure/closure-packet.md").encode()
        (self.fixture.program_root / "increments/ARCHIVE-INDEX/exact-file-plan.md").write_bytes(old_plan)
        before = repository_snapshot(self.fixture.repository)
        self.assertEqual(self.discover()["disposition"], "plan-preparation-recovery-required")
        failed, _ = self.run_phase("prepare-plan", exact_plan=old_plan, check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(repository_snapshot(self.fixture.repository), before)

        self.start_sparse_program()
        self.advance_current_to_diff()
        _, choice = self.run_phase("render-accept-continue")
        failed, _ = self.run_phase("dispose-diff", prompt=choice["prompt"], fail_label="action-authorization", check=False)
        self.assertIn("injected-after:", failed.stderr)
        path = self.fixture.program_root / "state/action-authorizations.jsonl"
        records = [json.loads(line) for line in path.read_text().splitlines()]
        records[-1]["successor_increment_id"] = "ARCHIVE-CATALOG"
        path.write_text("".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records))
        before = repository_snapshot(self.fixture.repository)
        self.assertIn(self.discover()["disposition"], {"increment-continuation-recovery-required", "continuation-recovery-required"})
        failed, _ = self.run_phase("dispose-diff", prompt=choice["prompt"], check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(repository_snapshot(self.fixture.repository), before)

    def test_each_successor_mode_materializes_inherited_history_after_both_routes(
        self,
    ) -> None:
        expected_inherited = {
            "archive-output.txt",
            "reviews/architecture.json",
            "reviews/requirements.json",
            "reviews/test-evidence.json",
        }
        for approval_mode in (
            "approval:standard",
            "approval:pre-approve",
            "approval:full-increment",
        ):
            for domain in ("immediate", "accepted-state"):
                with self.subTest(approval_mode=approval_mode, domain=domain):
                    self.reset_fixture(approval_mode=approval_mode)
                    self.publish_and_advance_first_to_diff()
                    original_manifest = (
                        self.fixture.program_root / "manifest.json"
                    ).read_bytes()
                    first_plan = (
                        self.fixture.program_root
                        / "increments/ARCHIVE-INDEX/exact-file-plan.md"
                    ).read_bytes()
                    genesis_grant = self.load_status()[
                        "current_increment_authority_binding"
                    ]["grant_id"]

                    rollover = self.rollover(domain)
                    self.assertEqual(
                        rollover["successor_increment_id"], "ARCHIVE-VERIFY"
                    )
                    successor = self.load_status()
                    self.assertEqual(successor["current_increment_state"], "preparing")
                    self.assertNotEqual(
                        successor["current_increment_authority_binding"]["grant_id"],
                        genesis_grant,
                    )
                    self.materialize_current_plan()

                    baseline = json.loads(
                        (
                            self.fixture.program_root
                            / "increments/ARCHIVE-VERIFY/execution-baseline.json"
                        ).read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        set(baseline["inherited_paths"]), expected_inherited
                    )
                    self.assertEqual(
                        (self.fixture.program_root / "manifest.json").read_bytes(),
                        original_manifest,
                    )
                    self.assertEqual(
                        (
                            self.fixture.program_root
                            / "increments/ARCHIVE-INDEX/exact-file-plan.md"
                        ).read_bytes(),
                        first_plan,
                    )

    def test_blocked_second_increment_resumes_and_rolls_to_third(self) -> None:
        _completed, published = self.run_phase("publish")
        assert published is not None
        self.run_phase("activate", prompt=str(published["prompt"]))
        _completed, first_rendered = self.run_phase("render-exact-plan")
        assert first_rendered is not None
        first_plan_text = str(first_rendered["plan"]).replace(
            "### Create\n\n",
            "### Create\n\n- `historical-only.txt` — exact owned path.\n",
            1,
        )
        _completed, first_prepared = self.run_phase(
            "prepare-plan", exact_plan=first_plan_text.encode("utf-8")
        )
        assert first_prepared is not None
        self.run_phase(
            "materialize-plan", prompt=str(first_prepared["plan_prompt"])
        )
        self.run_phase("implementing")
        (self.fixture.repository / "historical-only.txt").write_text(
            "accepted historical bytes\n", encoding="utf-8"
        )
        self.run_phase("reviewing")
        self.run_phase("prepare-review")
        manifest_bytes = (self.fixture.program_root / "manifest.json").read_bytes()
        first_plan_path = (
            self.fixture.program_root
            / "increments/ARCHIVE-INDEX/exact-file-plan.md"
        )
        first_plan_bytes = first_plan_path.read_bytes()
        self.rollover("immediate")

        _completed, rendered = self.run_phase("render-exact-plan")
        assert rendered is not None
        successor_plan_text = str(rendered["plan"])
        inherited_preserve_line = "- `historical-only.txt` — exact owned path.\n"
        self.assertIn(inherited_preserve_line, successor_plan_text)
        successor_plan_text = successor_plan_text.replace(
            inherited_preserve_line, "", 1
        ).replace(
            "### Preserve\n\n",
            f"### Preserve\n\n{inherited_preserve_line}",
            1,
        )
        successor_plan = successor_plan_text.encode("utf-8")
        required_paths = tuple(rendered["required_future_paths"])
        self.assertTrue(required_paths)
        for relative in required_paths:
            with self.subTest(missing_future_path=relative):
                lines = successor_plan.decode("utf-8").splitlines(keepends=True)
                tampered = "".join(
                    line for line in lines if f"`{relative}`" not in line
                ).encode("utf-8")
                before = repository_snapshot(self.fixture.program_root)
                rejected, _value = self.run_phase(
                    "prepare-plan", exact_plan=tampered, check=False
                )
                self.assertEqual(rejected.returncode, 1, rejected.stderr)
                self.assertEqual(repository_snapshot(self.fixture.program_root), before)

        _completed, prepared = self.run_phase(
            "prepare-plan", exact_plan=successor_plan
        )
        assert prepared is not None
        self.run_phase(
            "materialize-plan", prompt=str(prepared["plan_prompt"])
        )
        self.run_phase("implementing")
        self.run_phase("block")
        self.assertEqual(self.discover()["disposition"], "blocked-recovery-ready")
        _completed, resolution = self.run_phase("render-block-resolution")
        assert resolution is not None
        self.run_phase("resolve-block", prompt=str(resolution["prompt"]))
        self.assertEqual(self.load_status()["current_increment_state"], "implementing")

        self.run_phase("reviewing")
        self.run_phase("prepare-review")
        self.assertEqual(self.discover()["disposition"], "resume")
        second_plan_path = (
            self.fixture.program_root
            / "increments/ARCHIVE-VERIFY/exact-file-plan.md"
        )
        second_plan_bytes = second_plan_path.read_bytes()
        _completed, stop = self.run_phase("render-accept-stop")
        assert stop is not None
        self.run_phase("accept", prompt=str(stop["prompt"]))
        self.assertEqual(self.discover()["disposition"], "accepted-stop")
        _completed, choice = self.run_phase("render-later-continuation")
        assert choice is not None
        _completed, third = self.run_phase(
            "rollover", prompt=str(choice["prompt"])
        )
        assert third is not None
        self.assertEqual(third["successor_increment_id"], "ARCHIVE-PUBLISH")
        self.assertEqual(self.load_status()["current_increment_state"], "preparing")
        _completed, third_preflight = self.run_phase("render-exact-plan")
        assert third_preflight is not None
        third_required = set(third_preflight["required_future_paths"])
        self.assertIn(
            "implementation-programs/ARCHIVE-PROGRAM/closure/reconciliation.json",
            third_required,
        )
        self.assertIn(
            "implementation-programs/ARCHIVE-PROGRAM/closure/closure-packet.md",
            third_required,
        )
        third_plan_text = str(third_preflight["plan"]).replace(
            inherited_preserve_line, "", 1
        ).replace(
            "### Preserve\n\n",
            f"### Preserve\n\n{inherited_preserve_line}",
            1,
        )
        _completed, third_prepared = self.run_phase(
            "prepare-plan", exact_plan=third_plan_text.encode("utf-8")
        )
        assert third_prepared is not None
        if third_prepared["plan_prompt"] is not None:
            self.run_phase(
                "materialize-plan", prompt=str(third_prepared["plan_prompt"])
            )
        third_baseline = json.loads(
            (
                self.fixture.program_root
                / "increments/ARCHIVE-PUBLISH/execution-baseline.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("historical-only.txt", third_baseline["inherited_paths"])
        self.run_phase("implementing")
        self.run_phase("reviewing")
        self.run_phase("prepare-review")
        _completed, final_stop = self.run_phase("render-accept-stop")
        assert final_stop is not None
        self.run_phase("accept", prompt=str(final_stop["prompt"]))
        self.assertEqual(self.discover()["disposition"], "accepted-stop")
        self.assertEqual(first_plan_path.read_bytes(), first_plan_bytes)
        self.assertEqual(second_plan_path.read_bytes(), second_plan_bytes)
        self.assertEqual(
            (self.fixture.program_root / "manifest.json").read_bytes(),
            manifest_bytes,
        )

    def test_frozen_v0_1_1_final_increment_closes_without_rewrite(self) -> None:
        frozen_before = repository_snapshot(COMPATIBILITY_FIXTURE)
        bootstrap_support._validate_compatibility_fixture_inventory()
        contract = json.loads(
            (COMPATIBILITY_FIXTURE / "fixture-contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["package_version"], "0.1.1")
        self.fixture.close()
        self.fixture = bootstrap_support.materialize_v0_1_1_compatibility_state(
            "accepted-stop"
        )
        manifest_path = self.fixture.program_root / "manifest.json"
        plan_path = (
            self.fixture.program_root
            / "increments/ARCHIVE-INDEX/exact-file-plan.md"
        )
        manifest_bytes = manifest_path.read_bytes()
        plan_bytes = plan_path.read_bytes()

        _completed, prepared = self.run_phase("prepare-closure")
        assert prepared is not None
        self.run_phase("close", prompt=str(prepared["prompt"]))
        self.assertEqual(self.load_status()["program_state"], "closed")
        self.assertEqual(manifest_path.read_bytes(), manifest_bytes)
        self.assertEqual(plan_path.read_bytes(), plan_bytes)
        self.assertEqual(repository_snapshot(COMPATIBILITY_FIXTURE), frozen_before)
        inventory = json.loads(
            (COMPATIBILITY_FIXTURE / "inventory.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            sorted(item["path"] for item in inventory["files"]),
            [item["path"] for item in inventory["files"]],
        )
        self.assertTrue(
            all(
                re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None
                for item in inventory["files"]
            )
        )

    def test_rollover_and_blocked_prefixes_recover_across_fresh_processes(
        self,
    ) -> None:
        immediate_cases = (
            ("diff-approval", "increment-acceptance-retry-ready"),
            ("accepted-status", "accepted-continuation-retry-ready"),
            ("action-authorization", "increment-continuation-retry-ready"),
            ("successor-grant", "increment-continuation-retry-ready"),
            ("handoff", "increment-rollover-retry-ready"),
            ("successor-brief", "increment-rollover-retry-ready"),
            ("rollover-record", "increment-rollover-retry-ready"),
            ("successor-status", "resume"),
        )
        later_cases = (
            ("action-authorization", "accepted-state-continuation-retry-ready"),
            ("successor-grant", "accepted-state-continuation-retry-ready"),
            ("handoff", "accepted-state-rollover-retry-ready"),
            ("successor-brief", "accepted-state-rollover-retry-ready"),
            ("rollover-record", "accepted-state-rollover-retry-ready"),
            ("successor-status", "resume"),
        )
        for domain, cases in (
            ("immediate", immediate_cases),
            ("accepted-state", later_cases),
        ):
            for label, expected_disposition in cases:
                with self.subTest(domain=domain, label=label):
                    self.reset_fixture()
                    self.publish_and_advance_first_to_diff()
                    if domain == "immediate":
                        _completed, choice = self.run_phase(
                            "render-accept-continue"
                        )
                        phase = "dispose-diff"
                    else:
                        _completed, stop = self.run_phase("render-accept-stop")
                        assert stop is not None
                        self.run_phase("accept", prompt=str(stop["prompt"]))
                        _completed, choice = self.run_phase(
                            "render-later-continuation"
                        )
                        phase = "rollover"
                    assert choice is not None
                    interrupted, _value = self.run_phase(
                        phase,
                        prompt=str(choice["prompt"]),
                        fail_label=label,
                        check=False,
                    )
                    self.assertEqual(interrupted.returncode, 1, interrupted.stderr)
                    self.assertIn(f"injected-after:{label}", interrupted.stderr)
                    self.assertEqual(
                        self.discover()["disposition"], expected_disposition
                    )
                    self.run_phase(phase, prompt=str(choice["prompt"]))
                    self.assertEqual(
                        self.load_status()["current_increment_id"], "ARCHIVE-VERIFY"
                    )

        for label, expected_disposition in (
            ("action-authorization", "blocked-resolution-retry-ready"),
            ("resolution-record", "blocked-resolution-retry-ready"),
            ("resumed-status", "resume"),
        ):
            with self.subTest(blocked_label=label):
                self.reset_fixture()
                self.publish_and_advance_first_to_diff()
                self.rollover("immediate")
                self.materialize_current_plan()
                self.run_phase("implementing")
                self.run_phase("block")
                _completed, resolution = self.run_phase(
                    "render-block-resolution"
                )
                assert resolution is not None
                interrupted, _value = self.run_phase(
                    "resolve-block",
                    prompt=str(resolution["prompt"]),
                    fail_label=label,
                    check=False,
                )
                self.assertEqual(interrupted.returncode, 1, interrupted.stderr)
                self.assertIn(f"injected-after:{label}", interrupted.stderr)
                self.assertEqual(
                    self.discover()["disposition"], expected_disposition
                )
                self.run_phase(
                    "resolve-block", prompt=str(resolution["prompt"])
                )
                self.assertEqual(
                    self.load_status()["current_increment_state"], "implementing"
                )

    def test_successor_materialization_prefixes_recover_in_each_mode(self) -> None:
        cases = {
            "approval:standard": (
                ("prepare-plan", "exact-plan", "plan-preparation-retry-ready"),
                (
                    "prepare-plan",
                    "awaiting-plan-status",
                    "plan-preparation-retry-ready",
                ),
                (
                    "materialize-plan",
                    "plan-approval",
                    "plan-materialization-retry-ready",
                ),
                (
                    "materialize-plan",
                    "execution-baseline",
                    "plan-materialization-retry-ready",
                ),
                (
                    "materialize-plan",
                    "plan-action-authorization",
                    "plan-materialization-retry-ready",
                ),
                ("materialize-plan", "authorized-status", "resume"),
            ),
            "approval:pre-approve": (
                ("prepare-plan", "exact-plan", "plan-preparation-retry-ready"),
                (
                    "prepare-plan",
                    "execution-baseline",
                    "plan-materialization-retry-ready",
                ),
                (
                    "prepare-plan",
                    "plan-action-authorization",
                    "plan-materialization-retry-ready",
                ),
                ("prepare-plan", "authorized-status", "resume"),
            ),
            "approval:full-increment": (
                ("prepare-plan", "exact-plan", "plan-preparation-retry-ready"),
                (
                    "prepare-plan",
                    "execution-baseline",
                    "plan-materialization-retry-ready",
                ),
                (
                    "prepare-plan",
                    "plan-action-authorization",
                    "plan-materialization-retry-ready",
                ),
                ("prepare-plan", "authorized-status", "resume"),
            ),
        }
        for approval_mode, mode_cases in cases.items():
            for phase, label, expected_disposition in mode_cases:
                with self.subTest(approval_mode=approval_mode, label=label):
                    self.reset_fixture(approval_mode=approval_mode)
                    self.publish_and_advance_first_to_diff()
                    self.rollover("immediate")
                    prompt = None
                    if phase == "materialize-plan":
                        _completed, prepared = self.run_phase("prepare-plan")
                        assert prepared is not None
                        prompt = str(prepared["plan_prompt"])
                    interrupted, _value = self.run_phase(
                        phase,
                        prompt=prompt,
                        fail_label=label,
                        check=False,
                    )
                    self.assertEqual(interrupted.returncode, 1, interrupted.stderr)
                    self.assertIn(f"injected-after:{label}", interrupted.stderr)
                    self.assertEqual(
                        self.discover()["disposition"], expected_disposition
                    )
                    self.run_phase(phase, prompt=prompt)
                    status = self.load_status()
                    if phase == "materialize-plan" or approval_mode != "approval:standard":
                        self.assertEqual(
                            status["current_increment_state"], "authorized"
                        )


if __name__ == "__main__":
    unittest.main()
