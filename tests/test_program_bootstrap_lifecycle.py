import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from tests import program_bootstrap_support as bootstrap_support
from tests.program_bootstrap_support import BootstrapFixture, repository_snapshot


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_PATH = REPOSITORY_ROOT / "tests/program_bootstrap_support.py"
DISCOVERY_PATH = (
    REPOSITORY_ROOT
    / "skills/implementing-staged-plans/scripts/program_discovery.py"
)
COMPATIBILITY_FIXTURE = (
    REPOSITORY_ROOT / "tests/fixtures/program-bootstrap/v0.1.1"
)


class ProgramBootstrapLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BootstrapFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def run_phase(
        self,
        phase: str,
        *,
        prompt: str | None = None,
        fail_label: str | None = None,
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
            prompt_path = self.fixture.root / f"{phase}-prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            arguments.extend(("--prompt-file", str(prompt_path)))
        if fail_label is not None:
            arguments.extend(("--fail-label", fail_label))
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

    def reset_fixture(self) -> None:
        self.fixture.close()
        self.fixture = BootstrapFixture()

    def discover(self) -> dict[str, object]:
        completed = subprocess.run(
            [
                sys.executable,
                str(DISCOVERY_PATH),
                "discover",
                str(self.fixture.repository),
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertIn(completed.returncode, {0, 1}, completed.stderr)
        return json.loads(completed.stdout)

    def publish(self) -> str:
        _completed, value = self.run_phase("publish")
        return str(value["prompt"])

    def advance_to_authorized(self) -> None:
        launch_prompt = self.publish()
        self.run_phase("activate", prompt=launch_prompt)
        _completed, prepared = self.run_phase("prepare-plan")
        self.run_phase("materialize-plan", prompt=str(prepared["plan_prompt"]))

    def advance_to_reviewing(self) -> None:
        self.advance_to_authorized()
        self.run_phase("implementing")
        self.run_phase("reviewing")

    def advance_to_awaiting_diff(self) -> str:
        self.advance_to_reviewing()
        _completed, prepared = self.run_phase("prepare-review")
        return str(prepared["prompt"])

    def advance_to_accepted(self) -> None:
        self.run_phase("accept", prompt=self.advance_to_awaiting_diff())

    def prepare_prefix_phase(self, phase: str) -> str | None:
        prompt = None
        if phase == "activate":
            prompt = self.publish()
        elif phase == "prepare-plan":
            self.run_phase("activate", prompt=self.publish())
        elif phase == "materialize-plan":
            self.run_phase("activate", prompt=self.publish())
            _completed, prepared = self.run_phase("prepare-plan")
            prompt = str(prepared["plan_prompt"])
        elif phase in {"implementing", "reviewing"}:
            self.advance_to_authorized()
            if phase == "reviewing":
                self.run_phase("implementing")
        elif phase == "prepare-review":
            self.advance_to_reviewing()
        elif phase == "accept":
            prompt = self.advance_to_awaiting_diff()
        elif phase == "prepare-closure":
            self.advance_to_accepted()
        else:
            self.advance_to_accepted()
            _completed, prepared = self.run_phase("prepare-closure")
            prompt = str(prepared["prompt"])
        return prompt

    def mutate_newest_prefix(self, label: str) -> None:
        manifest = json.loads(
            (self.fixture.program_root / "manifest.json").read_text(encoding="utf-8")
        )
        storage = manifest["increment_storage"]
        closure = manifest["closure_storage"]
        increment_root = (
            self.fixture.program_root / storage["root"] / "ARCHIVE-INDEX"
        )
        paths = {
            "program-approval": self.fixture.program_root / manifest["logical_roles"]["approvals"],
            "workspace-approval": self.fixture.program_root / manifest["logical_roles"]["approvals"],
            "increment-grant": self.fixture.program_root / manifest["logical_roles"]["increment_grants"],
            "active-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "exact-plan": increment_root / storage["exact_file_plan_filename"],
            "awaiting-plan-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "plan-approval": self.fixture.program_root / manifest["logical_roles"]["approvals"],
            "execution-baseline": increment_root / storage["execution_baseline_filename"],
            "plan-action-authorization": self.fixture.program_root / manifest["logical_roles"]["action_authorizations"],
            "authorized-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "implementing-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "reviewing-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "review-evidence": increment_root / storage["review_evidence_filename"],
            "review-packet": increment_root / storage["review_packet_filename"],
            "verified-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "awaiting-diff-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "diff-approval": self.fixture.program_root / manifest["logical_roles"]["approvals"],
            "accepted-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "reconciliation": self.fixture.program_root / closure["root"] / closure["reconciliation_filename"],
            "packet": self.fixture.program_root / closure["root"] / closure["packet_filename"],
            "awaiting-closure-status": self.fixture.program_root / manifest["logical_roles"]["status"],
            "closure-approval": self.fixture.program_root / manifest["logical_roles"]["approvals"],
            "closed-status": self.fixture.program_root / manifest["logical_roles"]["status"],
        }
        path = paths[label]
        if label == "exact-plan":
            path.write_bytes(b"divergent exact-plan prefix\n")
            return
        if path.suffix == ".jsonl":
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            record = records[-1]
            identifier = next(
                field
                for field in ("event_id", "authorization_id", "grant_id")
                if field in record
            )
            record[identifier] = f"{record[identifier]}-DIVERGENT"
            path.write_text(
                "".join(
                    json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
                    for record in records
                ),
                encoding="utf-8",
            )
            return
        if path.name == "status.json":
            status = json.loads(path.read_text(encoding="utf-8"))
            binding_field = {
                "active-status": "activation_binding",
                "awaiting-plan-status": "plan_preparation_binding",
                "authorized-status": "plan_preparation_binding",
                "implementing-status": "execution_transition_binding",
                "reviewing-status": "execution_transition_binding",
                "verified-status": "review_preparation_binding",
                "awaiting-diff-status": "review_preparation_binding",
                "accepted-status": "diff_disposition_binding",
                "awaiting-closure-status": "closure_preparation_binding",
                "closed-status": "closure_command_binding",
            }[label]
            binding = status[binding_field]
            digest_field = next(
                (
                    field
                    for field in (
                        "product_delta_sha256",
                        "packet_sha256",
                        "reconciliation_sha256",
                        "closure_packet_sha256",
                        "exact_file_plan_sha256",
                        "submitted_prompt_sha256",
                        "prior_status_sha256",
                    )
                    if field in binding
                ),
                None,
            )
            if digest_field is None:
                identifier = next(
                    field
                    for field in (
                        "approval_event_id",
                        "event_id",
                        "closure_approval_event_id",
                    )
                    if field in binding
                )
                binding[identifier] = f"{binding[identifier]}-DIVERGENT"
            else:
                binding[digest_field] = "f" * 64
            path.write_text(
                json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return
        path.write_bytes(path.read_bytes() + b"\nDIVERGENT\n")

    def test_genesis_through_first_diff_accept_stop_and_closure(self) -> None:
        _completed, published = self.run_phase("publish")
        self.assertIsNotNone(published)
        _completed, awaiting_diff = self.run_phase(
            "activate-to-diff", prompt=str(published["prompt"])
        )
        self.assertEqual(awaiting_diff["increment_state"], "awaiting-diff-approval")
        self.assertEqual(
            (self.fixture.repository / "archive-output.txt").read_text(encoding="utf-8"),
            "verified archive output\n",
        )

        _completed, accepted = self.run_phase(
            "accept-and-prepare-closure", prompt=str(awaiting_diff["prompt"])
        )
        self.assertEqual(accepted["increment_state"], "accepted")
        self.assertEqual(accepted["program_state"], "awaiting-closure-approval")

        _completed, closed = self.run_phase(
            "close", prompt=str(accepted["prompt"])
        )
        self.assertEqual(closed["program_state"], "closed")

    def test_fresh_discovery_rejects_repository_drift_before_resume(self) -> None:
        self.advance_to_authorized()
        self.run_phase("implementing")
        self.assertEqual(self.discover()["disposition"], "resume")

        (self.fixture.repository / "catalog.txt").write_text(
            "changed outside the authorized product delta\n", encoding="utf-8"
        )

        discovered = self.discover()
        self.assertEqual(discovered["disposition"], "invalid", discovered)
        self.assertIn("catalog.txt", " ".join(discovered["issues"]))

    def test_every_post_publication_prefix_recovers_across_fresh_processes(self) -> None:
        cases = (
            ("activate", "program-approval", "program-activation-retry-ready"),
            ("activate", "workspace-approval", "program-activation-retry-ready"),
            ("activate", "increment-grant", "program-activation-retry-ready"),
            ("activate", "active-status", "resume"),
            ("prepare-plan", "exact-plan", "plan-preparation-retry-ready"),
            ("prepare-plan", "awaiting-plan-status", "plan-preparation-retry-ready"),
            ("materialize-plan", "plan-approval", "plan-materialization-retry-ready"),
            ("materialize-plan", "execution-baseline", "plan-materialization-retry-ready"),
            ("materialize-plan", "plan-action-authorization", "plan-materialization-retry-ready"),
            ("materialize-plan", "authorized-status", "resume"),
            ("implementing", "implementing-status", "resume"),
            ("reviewing", "reviewing-status", "resume"),
            ("prepare-review", "review-evidence", "review-preparation-retry-ready"),
            ("prepare-review", "review-packet", "review-preparation-retry-ready"),
            ("prepare-review", "verified-status", "review-preparation-retry-ready"),
            ("prepare-review", "awaiting-diff-status", "resume"),
            ("accept", "diff-approval", "increment-acceptance-retry-ready"),
            ("accept", "accepted-status", "accepted-stop"),
            ("prepare-closure", "reconciliation", "closure-preparation-retry-ready"),
            ("prepare-closure", "packet", "closure-preparation-retry-ready"),
            ("prepare-closure", "awaiting-closure-status", "closure-approval-ready"),
            ("close", "closure-approval", "closure-approval-retry-ready"),
            ("close", "closed-status", "terminal-programs"),
        )
        for phase, label, expected_disposition in cases:
            with self.subTest(phase=phase, label=label):
                self.reset_fixture()
                prompt = self.prepare_prefix_phase(phase)

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
                _completed, recovered = self.run_phase(phase, prompt=prompt)
                self.assertIn("recovered", recovered)
                self.assertTrue(recovered["recovered"])
                completed_snapshot = repository_snapshot(self.fixture.repository)
                self.run_phase(phase, prompt=prompt)
                self.assertEqual(
                    repository_snapshot(self.fixture.repository), completed_snapshot
                )

    def test_every_divergent_post_publication_prefix_is_preserved_and_typed(self) -> None:
        cases = (
            ("activate", "program-approval", "program-activation-recovery-required"),
            ("activate", "workspace-approval", "program-activation-recovery-required"),
            ("activate", "increment-grant", "program-activation-recovery-required"),
            ("activate", "active-status", "program-activation-recovery-required"),
            ("prepare-plan", "exact-plan", "plan-preparation-recovery-required"),
            ("prepare-plan", "awaiting-plan-status", "plan-preparation-recovery-required"),
            ("materialize-plan", "plan-approval", "plan-materialization-recovery-required"),
            ("materialize-plan", "execution-baseline", "plan-materialization-recovery-required"),
            ("materialize-plan", "plan-action-authorization", "plan-materialization-recovery-required"),
            ("materialize-plan", "authorized-status", "plan-materialization-recovery-required"),
            ("implementing", "implementing-status", "execution-transition-recovery-required"),
            ("reviewing", "reviewing-status", "execution-transition-recovery-required"),
            ("prepare-review", "review-evidence", "review-preparation-recovery-required"),
            ("prepare-review", "review-packet", "review-preparation-recovery-required"),
            ("prepare-review", "verified-status", "review-preparation-recovery-required"),
            ("prepare-review", "awaiting-diff-status", "review-preparation-recovery-required"),
            ("accept", "diff-approval", "increment-acceptance-recovery-required"),
            ("accept", "accepted-status", "increment-acceptance-recovery-required"),
            ("prepare-closure", "reconciliation", "closure-preparation-recovery-required"),
            ("prepare-closure", "packet", "closure-preparation-recovery-required"),
            ("prepare-closure", "awaiting-closure-status", "closure-preparation-recovery-required"),
            ("close", "closure-approval", "closure-approval-recovery-required"),
            ("close", "closed-status", "closure-approval-recovery-required"),
        )
        for phase, label, expected_disposition in cases:
            with self.subTest(phase=phase, label=label):
                self.reset_fixture()
                prompt = self.prepare_prefix_phase(phase)
                interrupted, _value = self.run_phase(
                    phase, prompt=prompt, fail_label=label, check=False
                )
                self.assertEqual(interrupted.returncode, 1, interrupted.stderr)
                self.mutate_newest_prefix(label)
                divergent_snapshot = repository_snapshot(self.fixture.repository)

                discovered = self.discover()
                self.assertEqual(
                    discovered["disposition"], expected_disposition, discovered
                )
                retry, _value = self.run_phase(phase, prompt=prompt, check=False)
                self.assertEqual(retry.returncode, 1, retry.stderr)
                self.assertEqual(
                    repository_snapshot(self.fixture.repository), divergent_snapshot
                )

    def test_every_publication_prefix_recovers_across_fresh_processes(self) -> None:
        inventory = tuple(
            path.relative_to(self.fixture.candidate).as_posix()
            for path in sorted(self.fixture.candidate.rglob("*"))
            if path.is_file() and not path.is_symlink()
        )
        boundaries = (
            "owner-receipt",
            *(f"staging:{path}" for path in inventory),
            "final-root-reserved",
            "final:.publication-owner.json",
            *(f"final:{path}" for path in inventory if path != "manifest.json"),
            "final:manifest.json",
        )
        for label in boundaries:
            with self.subTest(label=label):
                self.reset_fixture()
                interrupted, _value = self.run_phase(
                    "publish", fail_label=label, check=False
                )
                self.assertEqual(interrupted.returncode, 1, interrupted.stderr)
                self.assertIn(f"injected-after:{label}", interrupted.stderr)
                expected = (
                    "program-activation-ready"
                    if label == "final:manifest.json"
                    else "proposal-publication-retry-ready"
                )
                self.assertEqual(self.discover()["disposition"], expected)
                _completed, recovered = self.run_phase("publish")
                self.assertTrue(recovered["recovered"])
                completed_snapshot = repository_snapshot(self.fixture.repository)
                self.run_phase("publish")
                self.assertEqual(
                    repository_snapshot(self.fixture.repository), completed_snapshot
                )

    def test_every_divergent_publication_prefix_is_preserved_and_typed(self) -> None:
        inventory = tuple(
            path.relative_to(self.fixture.candidate).as_posix()
            for path in sorted(self.fixture.candidate.rglob("*"))
            if path.is_file() and not path.is_symlink()
        )
        boundaries = (
            "owner-receipt",
            *(f"staging:{path}" for path in inventory),
            "final-root-reserved",
            "final:.publication-owner.json",
            *(f"final:{path}" for path in inventory if path != "manifest.json"),
            "final:manifest.json",
        )
        for label in boundaries:
            with self.subTest(label=label):
                self.reset_fixture()
                interrupted, _value = self.run_phase(
                    "publish", fail_label=label, check=False
                )
                self.assertEqual(interrupted.returncode, 1, interrupted.stderr)
                staging = next(
                    self.fixture.repository.glob(".implementation-program-*")
                )
                if label == "owner-receipt":
                    target = staging / ".publication-owner.json"
                elif label.startswith("staging:"):
                    target = staging / label.removeprefix("staging:")
                elif label == "final-root-reserved":
                    target = self.fixture.program_root / "unexpected.txt"
                    target.write_bytes(b"divergent\n")
                elif label == "final:.publication-owner.json":
                    target = self.fixture.program_root / ".publication-owner.json"
                else:
                    target = self.fixture.program_root / label.removeprefix("final:")
                if label != "final-root-reserved":
                    target.write_bytes(target.read_bytes() + b" ")
                divergent_snapshot = repository_snapshot(self.fixture.repository)
                discovered = self.discover()
                self.assertEqual(
                    discovered["disposition"],
                    "proposal-publication-recovery-required",
                    discovered,
                )
                retry, _value = self.run_phase("publish", check=False)
                self.assertEqual(retry.returncode, 1, retry.stderr)
                self.assertEqual(
                    repository_snapshot(self.fixture.repository), divergent_snapshot
                )

    def test_frozen_v0_1_1_fixture_has_exact_inventory_and_two_gate_states(self) -> None:
        inventory = json.loads(
            (COMPATIBILITY_FIXTURE / "inventory.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            inventory["schema_version"], "implementation-fixture-inventory/v1"
        )
        self.assertEqual(inventory["inventory_excludes"], ["inventory.json"])
        actual: list[dict[str, str]] = []
        for directory, directory_names, file_names in os.walk(
            COMPATIBILITY_FIXTURE, followlinks=False
        ):
            root = Path(directory)
            for name in (*directory_names, *file_names):
                path = root / name
                self.assertFalse(path.is_symlink(), path)
            for name in sorted(file_names):
                path = root / name
                self.assertTrue(path.is_file(), path)
                relative = path.relative_to(COMPATIBILITY_FIXTURE).as_posix()
                if relative == "inventory.json":
                    continue
                payload = path.read_bytes()
                self.assertNotIn(b"0.1.2", payload)
                actual.append(
                    {
                        "path": relative,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                )
        self.assertEqual(inventory["files"], sorted(actual, key=lambda item: item["path"]))
        states = {
            name: json.loads(
                (
                    COMPATIBILITY_FIXTURE
                    / name
                    / "program/state/status.json"
                ).read_text(encoding="utf-8")
            )["current_increment_state"]
            for name in ("awaiting-diff", "accepted-stop")
        }
        self.assertEqual(
            states,
            {
                "awaiting-diff": "awaiting-diff-approval",
                "accepted-stop": "accepted",
            },
        )

    def test_v0_1_1_materializer_produces_both_live_discoverable_states(self) -> None:
        materialize = bootstrap_support.materialize_v0_1_1_compatibility_state
        expected = {
            "awaiting-diff": ("awaiting-diff-approval", "resume"),
            "accepted-stop": ("accepted", "accepted-stop"),
        }
        for state, (increment_state, disposition) in expected.items():
            with self.subTest(state=state):
                fixture = materialize(state)
                try:
                    manifest_path = fixture.program_root / "manifest.json"
                    plan_path = (
                        fixture.program_root
                        / "increments/ARCHIVE-INDEX/exact-file-plan.md"
                    )
                    protected_before = {
                        "manifest": manifest_path.read_bytes(),
                        "exact_plan": plan_path.read_bytes(),
                    }
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(DISCOVERY_PATH),
                            "discover",
                            str(fixture.repository),
                        ],
                        cwd=REPOSITORY_ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertIn(completed.returncode, {0, 1}, completed.stderr)
                    discovered = json.loads(completed.stdout)
                    status = json.loads(
                        (fixture.program_root / "state/status.json").read_text(
                            encoding="utf-8"
                        )
                    )
                    self.assertEqual(status["current_increment_state"], increment_state)
                    self.assertEqual(discovered["disposition"], disposition, discovered)
                    self.assertEqual(
                        manifest_path.read_bytes(), protected_before["manifest"]
                    )
                    self.assertEqual(
                        plan_path.read_bytes(), protected_before["exact_plan"]
                    )
                    self.assertTrue((fixture.repository / "catalog.txt").is_file())
                    self.assertEqual(
                        subprocess.run(
                            ["git", "rev-parse", "--is-inside-work-tree"],
                            cwd=fixture.repository,
                            text=True,
                            capture_output=True,
                            check=False,
                        ).stdout.strip(),
                        "true",
                    )
                finally:
                    fixture.close()


if __name__ == "__main__":
    unittest.main()
