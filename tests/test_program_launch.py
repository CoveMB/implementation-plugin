import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.program_bootstrap_support import BootstrapFixture, canonical_json
from tests.script_module_support import load_script_module


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills" / "implementing-staged-plans" / "scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_launch.py"
_PROGRAM_SETUP = load_script_module(
    "program_setup", SCRIPT_ROOT / "program_setup.py"
)
LAUNCH = load_script_module("program_launch", SCRIPT_PATH)


class ProgramLaunchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BootstrapFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_launch_prompt_is_deterministic_bound_and_has_distinct_ids(self) -> None:
        prompt = LAUNCH.render_program_launch_prompt(self.fixture.candidate)

        command = LAUNCH.validate_submitted_program_launch_prompt(
            self.fixture.candidate, prompt
        )
        self.assertEqual(command["schema_version"], LAUNCH.LAUNCH_COMMAND_SCHEMA)
        self.assertEqual(command["program_id"], "ARCHIVE-PROGRAM")
        identifiers = {
            command["launch_checkpoint_id"],
            command["program_approval_event_id"],
            command["workspace_approval_event_id"],
            command["increment_grant_id"],
        }
        self.assertEqual(len(identifiers), 4)
        self.assertNotIn("submitted_prompt_sha256", prompt)
        self.assertEqual(LAUNCH.render_program_launch_prompt(self.fixture.candidate), prompt)

    def test_changed_proposal_status_or_workspace_rejects_submitted_prompt(self) -> None:
        for relative_path in ("state/status.json", "state/workspace.json"):
            with self.subTest(relative_path=relative_path):
                fixture = BootstrapFixture()
                try:
                    prompt = LAUNCH.render_program_launch_prompt(fixture.candidate)
                    path = fixture.candidate / relative_path
                    value = json.loads(path.read_text(encoding="utf-8"))
                    value["unexpected"] = True
                    path.write_bytes(canonical_json(value))
                    with self.assertRaises(ValueError):
                        LAUNCH.validate_submitted_program_launch_prompt(
                            fixture.candidate, prompt
                        )
                finally:
                    fixture.close()

    def test_unsupported_new_program_modes_fail_before_rendering(self) -> None:
        for mode in ("approval:full-diff", "approval:full"):
            with self.subTest(mode=mode):
                fixture = BootstrapFixture()
                try:
                    manifest_path = fixture.candidate / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["approval_mode"] = mode
                    manifest_path.write_bytes(canonical_json(manifest))
                    before = manifest_path.read_bytes()
                    with self.assertRaisesRegex(
                        ValueError, "unsupported-new-program-approval-mode"
                    ):
                        LAUNCH.render_program_launch_prompt(fixture.candidate)
                    self.assertEqual(manifest_path.read_bytes(), before)
                finally:
                    fixture.close()

    def test_render_cli_returns_prompt_and_usage_errors_return_two(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "render", str(self.fixture.candidate)],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            LAUNCH.validate_submitted_program_launch_prompt(
                self.fixture.candidate, completed.stdout
            )["schema_version"],
            LAUNCH.LAUNCH_COMMAND_SCHEMA,
        )
        usage = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "render"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(usage.returncode, 2)

    def test_v3_render_route_returns_readable_setup_recap_not_machine_payload(self) -> None:
        self.fixture.configure_setup_v3()

        recap = LAUNCH.render_program_launch_prompt(self.fixture.candidate)

        self.assertIn("Approve this program setup?", recap)
        self.assertIn("ARCHIVE-INDEX", recap)
        self.assertNotIn("implementation-program-launch-command", recap)
        with self.assertRaisesRegex(ValueError, "typed setup decision"):
            LAUNCH.validate_submitted_program_launch_prompt(
                self.fixture.candidate,
                recap,
            )

    def test_launch_requires_matching_manifest_and_status_schema_families(
        self,
    ) -> None:
        cases = (
            (False, "implementation-program-status/v2", False),
            (False, "implementation-program-status/v3", True),
            (True, "implementation-program-status/v2", True),
            (True, "implementation-program-status/v3", False),
        )
        for setup_v3, status_schema, rejected in cases:
            with self.subTest(
                setup_v3=setup_v3,
                status_schema=status_schema,
            ):
                self.tearDown()
                self.setUp()
                if setup_v3:
                    self.fixture.configure_setup_v3()
                status_path = self.fixture.candidate / "state/status.json"
                status = json.loads(status_path.read_text(encoding="utf-8"))
                status["schema_version"] = status_schema
                status_path.write_bytes(canonical_json(status))

                if rejected:
                    with self.assertRaises(ValueError):
                        LAUNCH.render_program_launch_prompt(self.fixture.candidate)
                else:
                    prompt = LAUNCH.render_program_launch_prompt(
                        self.fixture.candidate
                    )
                    if setup_v3:
                        self.assertIn("Approve this program setup?", prompt)
                    else:
                        self.assertIn(LAUNCH.LAUNCH_COMMAND_SCHEMA, prompt)


if __name__ == "__main__":
    unittest.main()
