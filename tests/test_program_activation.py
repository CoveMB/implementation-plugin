import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture,
    canonical_json,
    repository_snapshot,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills" / "implementing-staged-plans" / "scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_activation.py"
DISCOVERY_PATH = SCRIPT_ROOT / "program_discovery.py"
SPEC = importlib.util.spec_from_file_location("program_activation", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load program activation from {SCRIPT_PATH}")
ACTIVATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ACTIVATION
sys.path.insert(0, str(SCRIPT_ROOT))
try:
    SPEC.loader.exec_module(ACTIVATION)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def proposal_observation(fixture: BootstrapFixture):
    workspace = fixture.load_json("state/workspace.json")
    selected = workspace["implementation_workspace"]
    existing = workspace["pre_existing_work_at_selection"]
    return ACTIVATION.RepositoryObservation(
        repository=workspace["repository"]["identity"],
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


def activated_program(
    fixture: BootstrapFixture, mode: str = "approval:standard"
) -> tuple[Path, object]:
    manifest = fixture.load_json("manifest.json")
    manifest["approval_mode"] = mode
    fixture.write_json("manifest.json", manifest)
    status = fixture.load_json("state/status.json")
    status["approval_mode"] = mode
    fixture.write_json("state/status.json", status)
    program_root = fixture.repository / "implementation-programs/ARCHIVE-PROGRAM"
    program_root.parent.mkdir()
    shutil.copytree(fixture.candidate, program_root)
    observation = proposal_observation(fixture)
    prompt = ACTIVATION.render_program_launch_prompt(program_root)
    ACTIVATION.activate_program(program_root, prompt, observation)
    return program_root, observation


def exact_plan_bytes(program_root: Path, observation) -> bytes:
    manifest = json.loads((program_root / "manifest.json").read_text(encoding="utf-8"))
    status = json.loads((program_root / "state/status.json").read_text(encoding="utf-8"))
    required = ACTIVATION.required_future_lifecycle_writes(
        program_root, Path(observation.path), status["current_increment_id"]
    )
    create = sorted(
        {
            "archive-output.txt",
            "reviews/architecture.json",
            "reviews/requirements.json",
            "reviews/test-evidence.json",
            *(
                item.path
                for item in required
                if item.disposition == "Create"
            ),
        }
    )
    modify = sorted(
        item.path for item in required if item.disposition == "Modify"
    )
    preserve = ["catalog.txt"]
    source = status["source_binding"]
    program = status["program_binding"]
    lines = [
        "# Archive exact plan",
        "",
        "## Global constraints",
        "Preserve user work and write only declared paths.",
        "",
        "## Requirements and acceptance binding",
        f"Program id: {manifest['program_id']}",
        f"Program revision: {manifest['program_revision']}",
        f"Increment id: {status['current_increment_id']}",
        f"Source digest: {source['sha256']}",
        f"Program digest: {program['sha256']}",
        f"Semantic digest: {program['semantic_requirements_sha256']}",
        f"Workspace path: {observation.path}",
        f"Workspace branch: {observation.branch}",
        f"Workspace base: {observation.base_commit}",
        f"Workspace head: {observation.head_commit}",
        "",
        "## File map",
        "",
    ]
    for disposition, paths in (
        ("Create", create),
        ("Modify", modify),
        ("Preserve", preserve),
    ):
        lines.extend(
            [
                f"### {disposition}",
                "",
                *[f"- `{path}` — exact owned path." for path in paths],
                "",
            ]
        )
    lines.extend(
        [
            "Interfaces: `archive-output.txt` is the bounded product output.",
            "",
            "## Semantic naming inventory",
            "| Surface | Kind | Context | Intention |",
            "|---|---|---|---|",
            "| `archive-output.txt` | path | archive output | record the verified result |",
            "",
            "## Test-first slices and verification contracts",
            "Create the output, then verify its observable bytes.",
            "",
            "## Commands and expected evidence",
            "Run `python3 -m unittest`; expected exit 0.",
            "",
            "## Review scopes and specialist predicates",
            "- requirements: `reviews/requirements.json`",
            "- architecture: `reviews/architecture.json`",
            "- test-evidence: `reviews/test-evidence.json`",
            "",
            "## Commit boundaries",
            "One logical local commit boundary; no commit authority is granted.",
            "",
            "## Rollback and recovery",
            "Preserve prefixes and retry only byte-identical transactions.",
            "",
            "## Approval required to execute",
            "Use the persisted approval-mode and status-current grant.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


class ProgramActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BootstrapFixture()
        self.observation = proposal_observation(self.fixture)

    def tearDown(self) -> None:
        self.fixture.close()

    def test_no_overwrite_creation_syncs_file_and_parent_directory(self) -> None:
        path = self.fixture.root / "durable" / "candidate.json"

        with mock.patch.object(
            ACTIVATION.os, "fsync", wraps=ACTIVATION.os.fsync
        ) as fsync:
            recovered = ACTIVATION._create_or_adopt_bytes(
                path, b'{"schema_version":"candidate/v1"}\n', "candidate"
            )

        self.assertFalse(recovered)
        self.assertGreaterEqual(fsync.call_count, 2)

    def test_activation_persists_three_records_then_active_preparing_status(self) -> None:
        prompt = ACTIVATION.render_program_launch_prompt(self.fixture.candidate)

        receipt = ACTIVATION.activate_program(
            self.fixture.candidate, prompt, self.observation
        )

        manifest = self.fixture.load_json("manifest.json")
        approvals = [
            json.loads(line)
            for line in (
                self.fixture.candidate / manifest["logical_roles"]["approvals"]
            ).read_text(encoding="utf-8").splitlines()
        ]
        grants = [
            json.loads(line)
            for line in (
                self.fixture.candidate / manifest["logical_roles"]["increment_grants"]
            ).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(
            tuple(record["type"] for record in approvals),
            ("program-approval", "workspace-selection-approval"),
        )
        self.assertEqual(len(grants), 1)
        self.assertEqual(grants[0]["schema_version"], ACTIVATION.INCREMENT_GRANT_SCHEMA)
        status = self.fixture.load_json("state/status.json")
        self.assertEqual(status["program_state"], "active")
        self.assertEqual(status["current_increment_state"], "preparing")
        self.assertEqual(status["state_sequence"], 1)
        self.assertEqual(
            status["current_increment_authority_binding"]["grant_id"],
            grants[0]["grant_id"],
        )
        self.assertEqual(receipt.status_sha256, ACTIVATION.sha256_file(self.fixture.candidate / "state/status.json"))
        self.assertEqual(
            ACTIVATION.validate_state_authority(
                self.fixture.candidate, self.observation
            ),
            [],
        )

    def test_changed_prompt_or_observation_fails_before_writes(self) -> None:
        prompt = ACTIVATION.render_program_launch_prompt(self.fixture.candidate)
        before = repository_snapshot(self.fixture.candidate)
        cases = (
            prompt + "extra\n",
            prompt.replace("ARCHIVE-PROGRAM", "OTHER-PROGRAM", 1),
        )
        for candidate in cases:
            with self.subTest(candidate=candidate[-30:]):
                with self.assertRaises(ValueError):
                    ACTIVATION.activate_program(
                        self.fixture.candidate, candidate, self.observation
                    )
                self.assertEqual(repository_snapshot(self.fixture.candidate), before)
        stale = ACTIVATION.RepositoryObservation(
            **{**self.observation.__dict__, "head_commit": "0" * 40}
        )
        with self.assertRaisesRegex(ValueError, "workspace observation"):
            ACTIVATION.activate_program(self.fixture.candidate, prompt, stale)
        self.assertEqual(repository_snapshot(self.fixture.candidate), before)

    def test_first_increment_grant_cannot_authorize_a_successor(self) -> None:
        prompt = ACTIVATION.render_program_launch_prompt(self.fixture.candidate)
        ACTIVATION.activate_program(self.fixture.candidate, prompt, self.observation)
        status_path = self.fixture.candidate / "state/status.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status["current_increment_id"] = "ARCHIVE-SUCCESSOR"
        status_path.write_bytes(canonical_json(status))

        issues = ACTIVATION.validate_state_authority(
            self.fixture.candidate, self.observation
        )

        self.assertIn("v2 current increment authority binding is invalid", issues)

    def test_every_activation_prefix_is_discovered_and_exact_retry_completes(self) -> None:
        for failure_label in (
            "program-approval",
            "workspace-approval",
            "increment-grant",
            "active-status",
        ):
            with self.subTest(failure_label=failure_label):
                fixture = BootstrapFixture()
                try:
                    program_root = fixture.repository / "implementation-programs/ARCHIVE-PROGRAM"
                    program_root.parent.mkdir()
                    shutil.copytree(fixture.candidate, program_root)
                    prompt = ACTIVATION.render_program_launch_prompt(program_root)
                    observation = proposal_observation(fixture)

                    def fail_after(label: str) -> None:
                        if label == failure_label:
                            raise RuntimeError("injected activation interruption")

                    with mock.patch.object(ACTIVATION, "_after_persist", side_effect=fail_after):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            ACTIVATION.activate_program(program_root, prompt, observation)

                    discovered = subprocess.run(
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
                    payload = json.loads(discovered.stdout)
                    self.assertIn(
                        payload["disposition"],
                        {"program-activation-retry-ready", "resume"},
                    )

                    ACTIVATION.activate_program(program_root, prompt, observation)
                    completed = repository_snapshot(program_root)
                    recovered = ACTIVATION.activate_program(
                        program_root, prompt, observation
                    )
                    self.assertTrue(recovered.recovered)
                    self.assertEqual(repository_snapshot(program_root), completed)
                finally:
                    fixture.close()

    def test_divergent_existing_record_is_preserved_and_requires_recovery(self) -> None:
        prompt = ACTIVATION.render_program_launch_prompt(self.fixture.candidate)

        def fail_after_program_approval(label: str) -> None:
            if label == "program-approval":
                raise RuntimeError("injected")

        with mock.patch.object(
            ACTIVATION, "_after_persist", side_effect=fail_after_program_approval
        ):
            with self.assertRaises(RuntimeError):
                ACTIVATION.activate_program(
                    self.fixture.candidate, prompt, self.observation
                )
        approvals = self.fixture.candidate / "state/approvals.jsonl"
        record = json.loads(approvals.read_text(encoding="utf-8"))
        record["launch_checkpoint_id"] = "DIVERGENT"
        approvals.write_text(
            json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        before = repository_snapshot(self.fixture.candidate)

        with self.assertRaisesRegex(
            ValueError, "program-activation-recovery-required"
        ):
            ACTIVATION.activate_program(
                self.fixture.candidate, prompt, self.observation
            )
        self.assertEqual(repository_snapshot(self.fixture.candidate), before)
        manifest_path = self.fixture.candidate / "manifest.json"
        discovered = subprocess.run(
            [
                sys.executable,
                str(DISCOVERY_PATH),
                "discover",
                str(self.fixture.root),
                "--manifest",
                str(manifest_path),
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(discovered.stdout)
        self.assertEqual(
            payload["disposition"], "program-activation-recovery-required"
        )
        self.assertTrue(payload["stop_required"])

    def test_apply_cli_uses_fresh_repository_observation(self) -> None:
        program_root = self.fixture.repository / "implementation-programs/ARCHIVE-PROGRAM"
        program_root.parent.mkdir()
        shutil.copytree(self.fixture.candidate, program_root)
        prompt = ACTIVATION.render_program_launch_prompt(program_root)
        prompt_path = self.fixture.root / "launch.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "apply",
                str(program_root),
                "--prompt-file",
                str(prompt_path),
                "--repository",
                str(self.fixture.repository),
                "--base-commit",
                self.fixture.head,
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertIn(completed.returncode, {0, 1}, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["increment_state"], "preparing")


class ExactPlanMaterializationTests(unittest.TestCase):
    def discover(self, fixture: BootstrapFixture) -> dict[str, object]:
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
        self.assertTrue(completed.stdout.strip(), completed.stderr)
        return json.loads(completed.stdout)

    def test_standard_mode_waits_for_exact_prompt_then_materializes_in_order(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root, observation = activated_program(fixture)
            plan = exact_plan_bytes(program_root, observation)

            prepared = ACTIVATION.prepare_exact_plan(
                program_root, plan, observation
            )

            self.assertEqual(prepared.increment_state, "awaiting-plan-approval")
            self.assertIsInstance(prepared.plan_prompt, str)
            self.assertFalse((program_root / "increments/ARCHIVE-INDEX/execution-baseline.json").exists())
            materialized = ACTIVATION.materialize_exact_plan(
                program_root, prepared.plan_prompt, observation
            )
            self.assertEqual(materialized.increment_state, "authorized")
            approvals = (program_root / "state/approvals.jsonl").read_text(encoding="utf-8")
            self.assertIn("exact-file-plan-approval", approvals)
            self.assertTrue((program_root / "increments/ARCHIVE-INDEX/execution-baseline.json").is_file())
            baseline = json.loads(
                (
                    program_root
                    / "increments/ARCHIVE-INDEX/execution-baseline.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(baseline["inherited_paths"], [])
            status = json.loads((program_root / "state/status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["current_increment_state"], "authorized")
        finally:
            fixture.close()

    def test_plan_grant_and_baseline_drift_are_preserved_and_rejected(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root, observation = activated_program(fixture)
            plan = exact_plan_bytes(program_root, observation)
            prepared = ACTIVATION.prepare_exact_plan(program_root, plan, observation)
            plan_path = program_root / "increments/ARCHIVE-INDEX/exact-file-plan.md"
            plan_path.write_bytes(plan + b"drift\n")
            before = repository_snapshot(program_root)
            self.assertEqual(
                self.discover(fixture)["disposition"],
                "plan-preparation-recovery-required",
            )
            with self.assertRaisesRegex(ValueError, "plan digest mismatch"):
                ACTIVATION.materialize_exact_plan(
                    program_root, prepared.plan_prompt, observation
                )
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

        fixture = BootstrapFixture()
        try:
            program_root, observation = activated_program(
                fixture, "approval:full-increment"
            )
            plan = exact_plan_bytes(program_root, observation)
            ACTIVATION.prepare_exact_plan(program_root, plan, observation)
            baseline_path = (
                program_root / "increments/ARCHIVE-INDEX/execution-baseline.json"
            )
            baseline_path.write_bytes(baseline_path.read_bytes() + b" ")
            before = repository_snapshot(program_root)
            self.assertEqual(
                self.discover(fixture)["disposition"],
                "plan-materialization-recovery-required",
            )
            with self.assertRaisesRegex(ValueError, "execution baseline"):
                ACTIVATION.prepare_exact_plan(program_root, plan, observation)
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_status_current_grant_and_user_owned_overlap_fail_before_plan_write(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root, observation = activated_program(fixture)
            status_path = program_root / "state/status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["current_increment_authority_binding"]["grant_id"] = "WRONG-GRANT"
            status_path.write_bytes(canonical_json(status))
            plan_path = program_root / "increments/ARCHIVE-INDEX/exact-file-plan.md"
            with self.assertRaisesRegex(ValueError, "increment grant"):
                ACTIVATION.prepare_exact_plan(
                    program_root, exact_plan_bytes(program_root, observation), observation
                )
            self.assertFalse(plan_path.exists())
        finally:
            fixture.close()

        fixture = BootstrapFixture()
        try:
            (fixture.repository / "archive-output.txt").write_text(
                "user owned\n", encoding="utf-8"
            )
            workspace = fixture.load_json("state/workspace.json")
            workspace["pre_existing_work_at_selection"]["untracked_paths"] = [
                "archive-output.txt"
            ]
            fixture.write_json("state/workspace.json", workspace)
            program_root, observation = activated_program(fixture)
            plan_path = program_root / "increments/ARCHIVE-INDEX/exact-file-plan.md"
            with self.assertRaisesRegex(ValueError, "pre-existing user work"):
                ACTIVATION.prepare_exact_plan(
                    program_root, exact_plan_bytes(program_root, observation), observation
                )
            self.assertFalse(plan_path.exists())
        finally:
            fixture.close()

    def test_preapprove_and_full_increment_omit_only_plan_approval(self) -> None:
        for mode in ("approval:pre-approve", "approval:full-increment"):
            with self.subTest(mode=mode):
                fixture = BootstrapFixture()
                try:
                    program_root, observation = activated_program(fixture, mode)
                    receipt = ACTIVATION.prepare_exact_plan(
                        program_root, exact_plan_bytes(program_root, observation), observation
                    )
                    self.assertEqual(receipt.increment_state, "authorized")
                    self.assertIsNone(receipt.plan_prompt)
                    approvals = (program_root / "state/approvals.jsonl").read_text(encoding="utf-8")
                    self.assertNotIn("exact-file-plan-approval", approvals)
                    self.assertTrue((program_root / "increments/ARCHIVE-INDEX/execution-baseline.json").is_file())
                    self.assertTrue((program_root / "state/action-authorizations.jsonl").read_text(encoding="utf-8"))
                finally:
                    fixture.close()

    def test_invalid_managed_map_and_stale_observation_fail_before_plan_write(self) -> None:
        fixture = BootstrapFixture()
        try:
            program_root, observation = activated_program(fixture)
            plan = exact_plan_bytes(program_root, observation).replace(
                "- `implementation-programs/ARCHIVE-PROGRAM/state/status.json` — exact owned path.\n".encode(),
                b"",
            )
            before = repository_snapshot(program_root)
            with self.assertRaisesRegex(ValueError, "required Modify path is missing"):
                ACTIVATION.prepare_exact_plan(program_root, plan, observation)
            self.assertEqual(repository_snapshot(program_root), before)
            stale = ACTIVATION.RepositoryObservation(
                **{**observation.__dict__, "head_commit": "0" * 40}
            )
            with self.assertRaisesRegex(ValueError, "workspace observation"):
                ACTIVATION.prepare_exact_plan(
                    program_root,
                    exact_plan_bytes(program_root, observation),
                    stale,
                )
            self.assertEqual(repository_snapshot(program_root), before)
        finally:
            fixture.close()

    def test_every_standard_plan_prefix_is_discovered_and_exact_retry_completes(self) -> None:
        preparation_labels = ("exact-plan", "awaiting-plan-status")
        for failure_label in preparation_labels:
            with self.subTest(transaction="preparation", label=failure_label):
                fixture = BootstrapFixture()
                try:
                    program_root, observation = activated_program(fixture)
                    plan = exact_plan_bytes(program_root, observation)

                    def interrupt(label: str) -> None:
                        if label == failure_label:
                            raise RuntimeError("injected plan preparation interruption")

                    with mock.patch.object(ACTIVATION, "_after_persist", side_effect=interrupt):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            ACTIVATION.prepare_exact_plan(program_root, plan, observation)
                    self.assertEqual(
                        self.discover(fixture)["disposition"],
                        "plan-preparation-retry-ready",
                    )
                    receipt = ACTIVATION.prepare_exact_plan(
                        program_root, plan, observation
                    )
                    self.assertEqual(receipt.increment_state, "awaiting-plan-approval")
                finally:
                    fixture.close()

        materialization_labels = (
            "plan-approval",
            "execution-baseline",
            "plan-action-authorization",
            "authorized-status",
        )
        for failure_label in materialization_labels:
            with self.subTest(transaction="materialization", label=failure_label):
                fixture = BootstrapFixture()
                try:
                    program_root, observation = activated_program(fixture)
                    prepared = ACTIVATION.prepare_exact_plan(
                        program_root,
                        exact_plan_bytes(program_root, observation),
                        observation,
                    )

                    def interrupt(label: str) -> None:
                        if label == failure_label:
                            raise RuntimeError("injected plan materialization interruption")

                    with mock.patch.object(ACTIVATION, "_after_persist", side_effect=interrupt):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            ACTIVATION.materialize_exact_plan(
                                program_root, prepared.plan_prompt, observation
                            )
                    expected = (
                        "resume"
                        if failure_label == "authorized-status"
                        else "plan-materialization-retry-ready"
                    )
                    self.assertEqual(self.discover(fixture)["disposition"], expected)
                    receipt = ACTIVATION.materialize_exact_plan(
                        program_root, prepared.plan_prompt, observation
                    )
                    self.assertEqual(receipt.increment_state, "authorized")
                finally:
                    fixture.close()

    def test_automatic_plan_prefixes_are_retry_safe_without_plan_approval(self) -> None:
        for failure_label in (
            "exact-plan",
            "execution-baseline",
            "plan-action-authorization",
            "authorized-status",
        ):
            with self.subTest(label=failure_label):
                fixture = BootstrapFixture()
                try:
                    program_root, observation = activated_program(
                        fixture, "approval:full-increment"
                    )
                    plan = exact_plan_bytes(program_root, observation)

                    def interrupt(label: str) -> None:
                        if label == failure_label:
                            raise RuntimeError("injected automatic materialization interruption")

                    with mock.patch.object(ACTIVATION, "_after_persist", side_effect=interrupt):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            ACTIVATION.prepare_exact_plan(program_root, plan, observation)
                    expected = (
                        "resume"
                        if failure_label == "authorized-status"
                        else (
                            "plan-preparation-retry-ready"
                            if failure_label == "exact-plan"
                            else "plan-materialization-retry-ready"
                        )
                    )
                    self.assertEqual(self.discover(fixture)["disposition"], expected)
                    receipt = ACTIVATION.prepare_exact_plan(
                        program_root, plan, observation
                    )
                    self.assertEqual(receipt.increment_state, "authorized")
                    self.assertNotIn(
                        "exact-file-plan-approval",
                        (program_root / "state/approvals.jsonl").read_text(
                            encoding="utf-8"
                        ),
                    )
                finally:
                    fixture.close()

    def test_execution_transitions_are_status_last_retry_safe_and_delta_bound(self) -> None:
        fixture = BootstrapFixture()
        try:
            (fixture.repository / "preserved.txt").write_text(
                "preserve me\n", encoding="utf-8"
            )
            fixture.head = subprocess.run(
                ["git", "add", "preserved.txt"],
                cwd=fixture.repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout or fixture.head
            subprocess.run(
                ["git", "commit", "-m", "add preserved fixture"],
                cwd=fixture.repository,
                check=True,
                capture_output=True,
                text=True,
            )
            fixture.head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=fixture.repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            workspace = fixture.load_json("state/workspace.json")
            workspace["implementation_workspace"].update(
                base_commit=fixture.head,
                head_commit_at_selection=fixture.head,
            )
            fixture.write_json("state/workspace.json", workspace)
            program_root, observation = activated_program(
                fixture, "approval:full-increment"
            )
            plan = exact_plan_bytes(program_root, observation).replace(
                b"### Modify\n\n",
                b"### Modify\n\n- `catalog.txt` \xe2\x80\x94 exact owned path.\n",
            ).replace(
                b"### Preserve\n\n- `catalog.txt` \xe2\x80\x94 exact owned path.",
                b"### Preserve\n\n- `preserved.txt` \xe2\x80\x94 exact owned path.",
            )
            ACTIVATION.prepare_exact_plan(
                program_root,
                plan,
                observation,
            )

            with mock.patch.object(
                ACTIVATION,
                "_after_persist",
                side_effect=lambda label: (
                    (_ for _ in ()).throw(RuntimeError("lost implementing response"))
                    if label == "implementing-status"
                    else None
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "lost implementing"):
                    ACTIVATION.advance_execution_state(
                        program_root, "implementing", observation
                    )
            recovered = ACTIVATION.advance_execution_state(
                program_root, "implementing", observation
            )
            self.assertTrue(recovered.recovered)

            (fixture.repository / "catalog.txt").write_text(
                "implemented catalog\n", encoding="utf-8"
            )
            (fixture.repository / "archive-output.txt").write_text(
                "archive output\n", encoding="utf-8"
            )
            reviews = fixture.repository / "reviews"
            reviews.mkdir()
            for scope in ("requirements", "architecture", "test-evidence"):
                (reviews / f"{scope}.json").write_text(
                    json.dumps({"scope": scope}) + "\n", encoding="utf-8"
                )
            product_observation = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation
            with mock.patch.object(
                ACTIVATION,
                "_after_persist",
                side_effect=lambda label: (
                    (_ for _ in ()).throw(RuntimeError("lost reviewing response"))
                    if label == "reviewing-status"
                    else None
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "lost reviewing"):
                    ACTIVATION.advance_execution_state(
                        program_root, "reviewing", product_observation
                    )
            recovered = ACTIVATION.advance_execution_state(
                program_root, "reviewing", product_observation
            )
            self.assertTrue(recovered.recovered)

            (fixture.repository / "catalog.txt").write_text(
                "different product delta\n", encoding="utf-8"
            )
            changed_observation = ACTIVATION.inspect_repository(
                fixture.repository, fixture.head
            ).observation
            before_status = (program_root / "state/status.json").read_bytes()
            with self.assertRaisesRegex(
                ValueError, "execution-transition-recovery-required"
            ):
                ACTIVATION.advance_execution_state(
                    program_root, "reviewing", changed_observation
                )
            self.assertEqual(
                (program_root / "state/status.json").read_bytes(), before_status
            )
            self.assertIn(
                "reviewed product delta differs from its status binding",
                ACTIVATION.validate_state_authority(
                    program_root,
                    ACTIVATION._without_owned_program_paths(
                        program_root, changed_observation
                    ),
                ),
            )
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
