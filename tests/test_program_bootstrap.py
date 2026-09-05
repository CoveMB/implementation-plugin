import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import BootstrapFixture, repository_snapshot
from tests.script_module_support import load_script_module


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "program_bootstrap.py"
BOOTSTRAP = load_script_module("program_bootstrap", SCRIPT_PATH)


class ProgramBootstrapTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = BootstrapFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def publish(self):
        return BOOTSTRAP.publish_program_proposal(
            self.fixture.repository,
            self.fixture.source_plan,
            self.fixture.candidate,
            self.fixture.source_sha256,
        )

    def retry_in_subprocess(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "publish",
                str(self.fixture.repository),
                "--source-plan",
                str(self.fixture.source_plan),
                "--candidate-root",
                str(self.fixture.candidate),
                "--expected-source-sha256",
                self.fixture.source_sha256,
            ],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )


class PublicationTests(ProgramBootstrapTestCase):
    def test_publication_freshness_uses_relative_invalid_manifest_issues(
        self,
    ) -> None:
        snapshots = []
        relative = "implementation-programs/OTHER/manifest.json"
        for _ in range(2):
            with tempfile.TemporaryDirectory() as directory:
                repository = Path(directory) / "repository"
                manifest = repository / relative
                manifest.parent.mkdir(parents=True)
                manifest.write_text("{", encoding="utf-8")

                freshness = BOOTSTRAP.publication_freshness(
                    repository, "ARCHIVE-PROGRAM"
                )

                issue = freshness["discovery"][0]["issues"][0]
                self.assertTrue(issue.startswith(f"{relative}:"), issue)
                self.assertNotIn(str(repository), issue)
                snapshots.append(freshness)
        self.assertEqual(snapshots[0], snapshots[1])

    def test_v3_publication_uses_v2_owner_and_an_immutable_candidate_snapshot(self) -> None:
        self.fixture.configure_setup_v3()
        program_path = self.fixture.candidate / "program/implementation-program.md"
        original_program_bytes = program_path.read_bytes()

        def mutate_after_capture(label: str) -> None:
            if label == "owner-receipt":
                program_path.write_text("changed after immutable capture\n", encoding="utf-8")

        with mock.patch.object(
            BOOTSTRAP,
            "_after_persist",
            side_effect=mutate_after_capture,
        ):
            receipt = self.publish()

        owner = json.loads(
            (self.fixture.program_root / ".publication-owner.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            owner["schema_version"],
            "implementation-proposal-publication-owner/v2",
        )
        self.assertEqual(
            owner["request_schema_version"],
            "implementation-program-proposal-request/v2",
        )
        self.assertIn("publication_freshness", owner)
        self.assertEqual(
            (self.fixture.program_root / "program/implementation-program.md").read_bytes(),
            original_program_bytes,
        )
        self.assertEqual(
            receipt.setup_recap_sha256,
            hashlib.sha256(BOOTSTRAP.render_setup_recap(self.fixture.program_root).encode()).hexdigest(),
        )

    def test_v3_publication_stops_when_bound_instruction_source_changes(self) -> None:
        instructions = self.fixture.repository / "AGENTS.md"
        instructions.write_text("Program manifest: implementation-programs/OTHER/manifest.json\n")
        workspace = self.fixture.load_json("state/workspace.json")
        workspace["pre_existing_work_at_selection"]["untracked_paths"] = ["AGENTS.md"]
        self.fixture.write_json("state/workspace.json", workspace)
        self.fixture.configure_setup_v3()
        original_inspection = BOOTSTRAP.inspect_repository
        calls = 0

        def mutate_before_final_root(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                instructions.write_text(
                    "Program manifest: implementation-programs/CHANGED/manifest.json\n"
                )
            return original_inspection(*args, **kwargs)

        with mock.patch.object(
            BOOTSTRAP,
            "inspect_repository",
            side_effect=mutate_before_final_root,
        ):
            with self.assertRaisesRegex(ValueError, "publication freshness changed"):
                BOOTSTRAP.publish_program_proposal(
                    self.fixture.repository,
                    self.fixture.source_plan,
                    self.fixture.candidate,
                    self.fixture.source_sha256,
                    instruction_source_paths=(instructions,),
                    instruction_manifest_paths=(
                        "implementation-programs/OTHER/manifest.json",
                    ),
                )
        self.assertFalse(self.fixture.program_root.exists())

    def test_v3_completed_publication_is_adopted_with_original_freshness(self) -> None:
        self.fixture.configure_setup_v3()
        first = self.publish()

        second = self.publish()

        self.assertEqual(second.manifest_sha256, first.manifest_sha256)
        self.assertEqual(second.created_paths, ())
        self.assertIn("manifest.json", second.adopted_paths)

    def test_repository_head_timeout_is_bounded_and_translated(self) -> None:
        def timeout_run(*args, timeout=None, **kwargs):
            if timeout is None:
                raise AssertionError("git HEAD resolution omitted its timeout")
            raise subprocess.TimeoutExpired(args[0], timeout)

        try:
            with mock.patch.object(
                BOOTSTRAP.subprocess,
                "run",
                side_effect=timeout_run,
            ):
                BOOTSTRAP._repository_head(self.fixture.repository)
        except AssertionError as error:
            self.fail(str(error))
        except subprocess.TimeoutExpired as error:
            self.fail(f"git HEAD timeout was not translated: {error}")
        except ValueError as error:
            self.assertIn("timed out", str(error))
        else:
            self.fail("git HEAD timeout did not fail closed")

    def test_manifest_last_publication_is_valid_and_idempotent(self) -> None:
        receipt = self.publish()
        self.assertEqual(receipt.program_root, str(self.fixture.program_root))
        self.assertTrue((self.fixture.program_root / "manifest.json").is_file())
        self.assertTrue((self.fixture.program_root / ".publication-owner.json").is_file())
        self.assertFalse(receipt.recovered)

        second = self.publish()
        self.assertTrue(second.recovered)
        self.assertEqual(second.manifest_sha256, receipt.manifest_sha256)
        self.assertEqual(second.status_sha256, receipt.status_sha256)
        self.assertEqual(second.launch_sha256, receipt.launch_sha256)
        self.assertEqual(second.created_paths, ())
        self.assertIn("manifest.json", second.adopted_paths)

    def test_every_publication_prefix_recovers_in_a_fresh_process(self) -> None:
        expected_inventory = BOOTSTRAP._candidate_inventory(self.fixture.candidate)
        boundaries = [
            "owner-receipt",
            *[f"staging:{path}" for path in expected_inventory],
            "final-root-reserved",
            "final:.publication-owner.json",
            *[
                f"final:{path}"
                for path in expected_inventory
                if path != "manifest.json"
            ],
            "final:manifest.json",
        ]
        for boundary in boundaries:
            with self.subTest(boundary=boundary):
                fixture = BootstrapFixture()
                self.fixture.close()
                self.fixture = fixture

                def fail_after(label: str) -> None:
                    if label == boundary:
                        raise RuntimeError(f"injected after {label}")

                with mock.patch.object(BOOTSTRAP, "_after_persist", side_effect=fail_after):
                    with self.assertRaisesRegex(RuntimeError, "injected after"):
                        self.publish()
                result = self.retry_in_subprocess()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((self.fixture.program_root / "manifest.json").is_file())

    def test_failed_write_removes_only_the_partial_file_created_by_this_call(self) -> None:
        real_write = os.write
        write_count = 0

        def fail_after_partial_write(descriptor: int, payload) -> int:
            nonlocal write_count
            write_count += 1
            if write_count == 1:
                return real_write(descriptor, bytes(payload[:1]))
            raise OSError("injected write failure")

        with mock.patch.object(BOOTSTRAP.os, "write", side_effect=fail_after_partial_write):
            with self.assertRaisesRegex(OSError, "injected write failure"):
                self.publish()

        staging_root = next(self.fixture.repository.glob(".implementation-program-*"))
        self.assertFalse((staging_root / ".publication-owner.json").exists())

        self.publish()
        self.assertTrue((self.fixture.program_root / "manifest.json").is_file())

    def test_failed_fsync_removes_only_the_file_created_by_this_call(self) -> None:
        real_fsync = os.fsync

        def fail_file_fsync(descriptor: int) -> None:
            if stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError("injected fsync failure")
            real_fsync(descriptor)

        with mock.patch.object(BOOTSTRAP.os, "fsync", side_effect=fail_file_fsync):
            with self.assertRaisesRegex(OSError, "injected fsync failure"):
                self.publish()

        staging_root = next(self.fixture.repository.glob(".implementation-program-*"))
        self.assertFalse((staging_root / ".publication-owner.json").exists())

    def test_failed_write_preserves_a_foreign_replacement_file(self) -> None:
        foreign_bytes = b"foreign replacement\n"

        def replace_before_failure(descriptor: int, payload) -> int:
            staging_root = next(
                self.fixture.repository.glob(".implementation-program-*")
            )
            owner_path = staging_root / ".publication-owner.json"
            owner_path.unlink()
            owner_path.write_bytes(foreign_bytes)
            raise OSError("injected write failure after replacement")

        with mock.patch.object(BOOTSTRAP.os, "write", side_effect=replace_before_failure):
            with self.assertRaisesRegex(OSError, "after replacement"):
                self.publish()

        staging_root = next(self.fixture.repository.glob(".implementation-program-*"))
        self.assertEqual(
            (staging_root / ".publication-owner.json").read_bytes(), foreign_bytes
        )

    def test_divergent_prefix_is_preserved_and_requires_recovery(self) -> None:
        with mock.patch.object(
            BOOTSTRAP,
            "_after_persist",
            side_effect=lambda label: (_ for _ in ()).throw(RuntimeError(label))
            if label == "staging:program/implementation-program.md"
            else None,
        ):
            with self.assertRaises(RuntimeError):
                self.publish()
        staging_root = next(self.fixture.repository.glob(".implementation-program-*"))
        divergent = staging_root / "program/implementation-program.md"
        divergent.write_text("divergent\n", encoding="utf-8")
        before = divergent.read_bytes()
        with self.assertRaisesRegex(ValueError, "proposal-publication-recovery-required"):
            self.publish()
        self.assertEqual(divergent.read_bytes(), before)

    def test_source_target_and_candidate_safety_fail_closed(self) -> None:
        self.fixture.source_plan.write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "source digest"):
            self.publish()

        self.fixture.close()
        self.fixture = BootstrapFixture()
        self.fixture.program_root.mkdir(parents=True)
        (self.fixture.program_root / "foreign.txt").write_text("foreign\n")
        with self.assertRaisesRegex(ValueError, "target collision"):
            self.publish()

        self.fixture.close()
        self.fixture = BootstrapFixture()
        self.fixture.program_root.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "target collision"):
            self.publish()

        self.fixture.close()
        self.fixture = BootstrapFixture()
        candidate_file = self.fixture.candidate / "program/implementation-program.md"
        candidate_file.unlink()
        candidate_file.symlink_to(self.fixture.source_plan)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.publish()

    def test_workspace_drift_and_multiple_controlling_programs_stop(self) -> None:
        original_inspection = BOOTSTRAP.inspect_repository
        calls = 0

        def drift_after_first(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                (self.fixture.repository / "unexpected.txt").write_text("drift\n")
            return original_inspection(*args, **kwargs)

        with mock.patch.object(BOOTSTRAP, "inspect_repository", side_effect=drift_after_first):
            with self.assertRaisesRegex(ValueError, "repository drift"):
                self.publish()

        self.fixture.close()
        self.fixture = BootstrapFixture()
        controlling = self.fixture.repository / "implementation-programs/OTHER"
        (controlling / "state").mkdir(parents=True)
        (controlling / "manifest.json").write_text(
            json.dumps({"logical_roles": {"status": "state/status.json"}}),
            encoding="utf-8",
        )
        (controlling / "state/status.json").write_text(
            json.dumps({"program_state": "active"}), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "multiple controlling programs"):
            self.publish()

    def test_unsupported_new_modes_fail_before_any_write(self) -> None:
        for mode in ("approval:full-diff", "approval:full"):
            with self.subTest(mode=mode):
                fixture = BootstrapFixture()
                self.fixture.close()
                self.fixture = fixture
                manifest = self.fixture.load_json("manifest.json")
                manifest["approval_mode"] = mode
                self.fixture.write_json("manifest.json", manifest)
                status = self.fixture.load_json("state/status.json")
                status["approval_mode"] = mode
                self.fixture.write_json("state/status.json", status)
                before = repository_snapshot(self.fixture.repository)
                with mock.patch.object(
                    BOOTSTRAP,
                    "_write_publication_owner",
                    side_effect=AssertionError("owner writer reached"),
                ):
                    with self.assertRaisesRegex(
                        ValueError, "unsupported-new-program-approval-mode"
                    ):
                        self.publish()
                self.assertEqual(repository_snapshot(self.fixture.repository), before)


class CommandTests(ProgramBootstrapTestCase):
    def test_cli_returns_zero_one_and_two(self) -> None:
        valid = self.retry_in_subprocess()
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        self.assertEqual(json.loads(valid.stdout)["program_root"], str(self.fixture.program_root))

        invalid = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "publish", str(self.fixture.repository)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(invalid.returncode, 2)

        self.fixture.close()
        self.fixture = BootstrapFixture()
        self.fixture.source_plan.write_text("changed\n", encoding="utf-8")
        failed = self.retry_in_subprocess()
        self.assertEqual(failed.returncode, 1)
        self.assertIn("source digest", failed.stdout)


if __name__ == "__main__":
    unittest.main()
