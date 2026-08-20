import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPOSITORY_ROOT
    / "skills"
    / "implementing-staged-plans"
    / "scripts"
    / "validate_package.py"
)
SPEC = importlib.util.spec_from_file_location("validate_package", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load validator from {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

AUTHORITY_REFERENCE = (
    "skills/implementing-staged-plans/references/program-authority.md"
)
AUTHORITY_SCRIPT = "skills/implementing-staged-plans/scripts/program_authority.py"
STATE_REFERENCE = (
    "skills/implementing-staged-plans/references/state-authorization.md"
)
STATE_SCRIPT = "skills/implementing-staged-plans/scripts/state_authority.py"
PREPARATION_REFERENCE = (
    "skills/implementing-staged-plans/references/repository-preparation.md"
)
PREPARATION_SCRIPT = (
    "skills/implementing-staged-plans/scripts/repository_preparation.py"
)
EXECUTION_REFERENCE = (
    "skills/implementing-staged-plans/references/execution-discipline.md"
)
EXECUTION_SCRIPT = (
    "skills/implementing-staged-plans/scripts/execution_discipline.py"
)
REVIEW_REFERENCE = (
    "skills/implementing-staged-plans/references/review-coordination.md"
)
REVIEW_SCRIPT = (
    "skills/implementing-staged-plans/scripts/review_coordination.py"
)
CONTINUITY_REFERENCE = (
    "skills/implementing-staged-plans/references/continuity-closure.md"
)
CONTINUITY_SCRIPT = (
    "skills/implementing-staged-plans/scripts/continuity_closure.py"
)
CHECKPOINT_REFERENCE = (
    "skills/implementing-staged-plans/references/approval-checkpoints.md"
)
CHECKPOINT_SCRIPT = (
    "skills/implementing-staged-plans/scripts/approval_checkpoint.py"
)
DISCOVERY_REFERENCE = (
    "skills/implementing-staged-plans/references/program-discovery.md"
)
DISCOVERY_SCRIPT = (
    "skills/implementing-staged-plans/scripts/program_discovery.py"
)
PLAN_A_SCRIPTS = tuple(
    f"skills/implementing-staged-plans/scripts/{name}.py"
    for name in (
        "program_bootstrap",
        "program_launch",
        "program_activation",
        "task_prompt",
        "program_review",
        "diff_disposition",
        "program_closure",
    )
)
PLAN_B_SCRIPTS = tuple(
    f"skills/implementing-staged-plans/scripts/{name}.py"
    for name in (
        "program_continuation",
        "program_rollover",
        "blocked_recovery",
    )
)


VALID_MANIFEST = {
    "name": "implementation-plugin",
    "version": "0.1.2",
    "description": "Run approved implementation programs one reviewable increment at a time.",
    "skills": "./skills/",
}
VALID_DESCRIPTION = (
    "Advance approved implementation programs one reviewable increment at a time. "
    "Use when a repository-backed program needs lifecycle routing or the next "
    "approved implementation increment."
)
VALID_SKILL = f"""---
name: implementing-staged-plans
description: {VALID_DESCRIPTION}
---

# Implementing Staged Plans

Route the next legal action.
"""
VALID_OPENAI_YAML = """interface:
  display_name: "Implementing Staged Plans"
  short_description: "Advance approved plans in reviewable increments."
  default_prompt: "Use $implementing-staged-plans to advance the next approved implementation increment."

policy:
  allow_implicit_invocation: false
"""


class PackageFixture:
    def __init__(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def close(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_json(self, relative_path: str, value: object) -> Path:
        return self.write(relative_path, json.dumps(value, indent=2) + "\n")

    def write_valid_package(self) -> None:
        self.write_json(".codex-plugin/plugin.json", VALID_MANIFEST)
        self.write_json(
            ".claude-plugin/plugin.json",
            {**VALID_MANIFEST, "displayName": "Implementation Plugin", "repository": "https://github.com/CoveMB/implementation-plugin"},
        )
        self.write_json(
            ".claude-plugin/marketplace.json",
            {
                "name": "implementation-workflows",
                "owner": {"name": "CoveMB"},
                "plugins": [
                    {
                        "name": VALID_MANIFEST["name"],
                        "source": "./",
                        "description": VALID_MANIFEST["description"],
                        "version": VALID_MANIFEST["version"],
                    }
                ],
            },
        )
        self.write("skills/implementing-staged-plans/SKILL.md", VALID_SKILL)
        self.write(
            "skills/implementing-staged-plans/agents/openai.yaml",
            VALID_OPENAI_YAML,
        )
        self.write(AUTHORITY_REFERENCE, "# Program Authority\n")
        self.write(AUTHORITY_SCRIPT, "# reusable authority validator\n")
        self.write(STATE_REFERENCE, "# State Authorization\n")
        self.write(STATE_SCRIPT, "# reusable state authority validator\n")
        self.write(PREPARATION_REFERENCE, "# Repository Preparation\n")
        self.write(PREPARATION_SCRIPT, "# read-only repository preparation validator\n")
        self.write(EXECUTION_REFERENCE, "# Execution Discipline\n")
        self.write(EXECUTION_SCRIPT, "# pure execution discipline validator\n")
        self.write(REVIEW_REFERENCE, "# Review Coordination\n")
        self.write(REVIEW_SCRIPT, "# pure review coordination validator\n")
        self.write(CONTINUITY_REFERENCE, "# Continuity and Closure\n")
        self.write(CONTINUITY_SCRIPT, "# pure continuity and closure validator\n")
        self.write(CHECKPOINT_REFERENCE, "# Approval Checkpoints\n")
        self.write(CHECKPOINT_SCRIPT, "# compound approval checkpoint helper\n")
        self.write(DISCOVERY_REFERENCE, "# Program Discovery\n")
        self.write(DISCOVERY_SCRIPT, "# deterministic read-only program discovery\n")
        for script in PLAN_A_SCRIPTS:
            self.write(script, f"# {Path(script).stem}\n")
        for script in PLAN_B_SCRIPTS:
            self.write(script, f"# {Path(script).stem}\n")


class PackageValidationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = PackageFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def assert_issue_contains(self, issues: list[str], expected: str) -> None:
        self.assertTrue(
            any(expected in issue for issue in issues),
            f"Expected issue containing {expected!r}; received {issues!r}",
        )


class JsonLoadingTests(PackageValidationTestCase):
    def test_load_json_object_reports_missing_invalid_and_non_object_files(self) -> None:
        missing, missing_issues = VALIDATOR.load_json_object(
            self.fixture.root / "missing.json"
        )
        self.assertIsNone(missing)
        self.assert_issue_contains(missing_issues, "missing")

        invalid_path = self.fixture.write("invalid.json", "{")
        invalid, invalid_issues = VALIDATOR.load_json_object(invalid_path)
        self.assertIsNone(invalid)
        self.assert_issue_contains(invalid_issues, "valid JSON")

        array_path = self.fixture.write_json("array.json", [])
        array, array_issues = VALIDATOR.load_json_object(array_path)
        self.assertIsNone(array)
        self.assert_issue_contains(array_issues, "JSON object")


class ManifestValidationTests(PackageValidationTestCase):
    def test_missing_and_invalid_manifests_are_rejected(self) -> None:
        self.assert_issue_contains(
            VALIDATOR.validate_plugin_manifest(self.fixture.root), "plugin.json is missing"
        )

        self.fixture.write(".codex-plugin/plugin.json", "not-json")
        self.assert_issue_contains(
            VALIDATOR.validate_plugin_manifest(self.fixture.root), "valid JSON"
        )

    def test_unknown_manifest_field_is_rejected(self) -> None:
        manifest = {**VALID_MANIFEST, "author": "Roadmap Team"}
        self.fixture.write_json(".codex-plugin/plugin.json", manifest)

        self.assert_issue_contains(
            VALIDATOR.validate_plugin_manifest(self.fixture.root), "exactly these fields"
        )

    def test_each_wrong_manifest_value_is_rejected(self) -> None:
        wrong_values = {
            "name": "other-plugin",
            "version": "1.0.0",
            "description": "Different description.",
            "skills": "skills",
        }
        for field, wrong_value in wrong_values.items():
            with self.subTest(field=field):
                manifest = {**VALID_MANIFEST, field: wrong_value}
                self.fixture.write_json(".codex-plugin/plugin.json", manifest)
                self.assert_issue_contains(
                    VALIDATOR.validate_plugin_manifest(self.fixture.root), field
                )


class SkillContractTests(PackageValidationTestCase):
    def test_missing_and_invalid_skill_frontmatter_are_rejected(self) -> None:
        self.assert_issue_contains(
            VALIDATOR.validate_skill_contract(self.fixture.root), "SKILL.md is missing"
        )

        self.fixture.write("skills/implementing-staged-plans/SKILL.md", "# Missing")
        self.assert_issue_contains(
            VALIDATOR.validate_skill_contract(self.fixture.root), "frontmatter"
        )

    def test_frontmatter_accepts_only_name_and_description(self) -> None:
        skill = VALID_SKILL.replace("---\n\n#", "metadata: extra\n---\n\n#")
        self.fixture.write("skills/implementing-staged-plans/SKILL.md", skill)

        self.assert_issue_contains(
            VALIDATOR.validate_skill_contract(self.fixture.root),
            "exactly name and description",
        )

    def test_wrong_skill_name_and_incomplete_trigger_description_are_rejected(self) -> None:
        wrong_name = VALID_SKILL.replace(
            "name: implementing-staged-plans", "name: roadmap-increment-one"
        )
        self.fixture.write("skills/implementing-staged-plans/SKILL.md", wrong_name)
        self.assert_issue_contains(
            VALIDATOR.validate_skill_contract(self.fixture.root), "skill name"
        )

        incomplete_description = VALID_SKILL.replace(
            VALID_DESCRIPTION, "Advance approved implementation programs."
        )
        self.fixture.write(
            "skills/implementing-staged-plans/SKILL.md", incomplete_description
        )
        self.assert_issue_contains(
            VALIDATOR.validate_skill_contract(self.fixture.root), "triggering contexts"
        )

    def test_missing_openai_fields_and_implicit_default_prompt_are_rejected(self) -> None:
        self.fixture.write("skills/implementing-staged-plans/SKILL.md", VALID_SKILL)
        for field in ("display_name", "short_description", "default_prompt"):
            with self.subTest(field=field):
                lines = [
                    line
                    for line in VALID_OPENAI_YAML.splitlines()
                    if f"{field}:" not in line
                ]
                self.fixture.write(
                    "skills/implementing-staged-plans/agents/openai.yaml",
                    "\n".join(lines) + "\n",
                )
                self.assert_issue_contains(
                    VALIDATOR.validate_skill_contract(self.fixture.root), field
                )

        implicit_prompt = VALID_OPENAI_YAML.replace("$implementing-staged-plans", "the skill")
        self.fixture.write(
            "skills/implementing-staged-plans/agents/openai.yaml", implicit_prompt
        )
        self.assert_issue_contains(
            VALIDATOR.validate_skill_contract(self.fixture.root),
            "explicitly name $implementing-staged-plans",
        )

    def test_implicit_invocation_must_be_explicitly_disabled(self) -> None:
        self.fixture.write("skills/implementing-staged-plans/SKILL.md", VALID_SKILL)
        invalid_metadata = (
            VALID_OPENAI_YAML.replace(
                "\npolicy:\n  allow_implicit_invocation: false\n", "\n"
            ),
            VALID_OPENAI_YAML.replace(
                "allow_implicit_invocation: false",
                "allow_implicit_invocation: true",
            ),
        )

        for metadata in invalid_metadata:
            with self.subTest(metadata=metadata):
                self.fixture.write(
                    "skills/implementing-staged-plans/agents/openai.yaml",
                    metadata,
                )
                self.assert_issue_contains(
                    VALIDATOR.validate_skill_contract(self.fixture.root),
                    "allow_implicit_invocation must be false",
                )


class LinkAndMarkerTests(PackageValidationTestCase):
    def test_unresolved_and_escaping_relative_links_are_rejected(self) -> None:
        self.fixture.write_valid_package()
        skill_path = self.fixture.root / "skills/implementing-staged-plans/SKILL.md"
        skill_path.write_text(VALID_SKILL + "\n[Missing](references/missing.md)\n")
        self.assert_issue_contains(
            VALIDATOR.validate_markdown_links(self.fixture.root), "does not resolve"
        )

        skill_path.write_text(VALID_SKILL + "\n[Escape](../../../outside.md)\n")
        self.assert_issue_contains(
            VALIDATOR.validate_markdown_links(self.fixture.root), "escapes repository"
        )

    def test_resolved_relative_link_is_accepted(self) -> None:
        self.fixture.write_valid_package()
        self.fixture.write(
            "skills/implementing-staged-plans/notes.md", "Reusable guidance.\n"
        )
        skill_path = self.fixture.root / "skills/implementing-staged-plans/SKILL.md"
        skill_path.write_text(VALID_SKILL + "\n[Notes](notes.md)\n")

        self.assertEqual(VALIDATOR.validate_markdown_links(self.fixture.root), [])

    def test_unresolved_template_marker_is_rejected(self) -> None:
        self.fixture.write_valid_package()
        skill_path = self.fixture.root / "skills/implementing-staged-plans/SKILL.md"
        skill_path.write_text(VALID_SKILL + "\nTODO: replace this marker.\n")

        self.assert_issue_contains(
            VALIDATOR.validate_skill_contract(self.fixture.root), "template marker"
        )


class ForbiddenSurfaceTests(PackageValidationTestCase):
    def test_every_forbidden_component_and_identity_surface_is_rejected(self) -> None:
        forbidden_paths = (
            ".mcp.json",
            ".app.json",
            "hooks.json",
            "publisher.json",
            "publication.json",
            "publish.json",
        )
        for relative_path in forbidden_paths:
            with self.subTest(relative_path=relative_path):
                self.fixture.write_valid_package()
                self.fixture.write_json(relative_path, {})
                self.assert_issue_contains(
                    VALIDATOR.validate_forbidden_components(self.fixture.root),
                    relative_path,
                )
                (self.fixture.root / relative_path).unlink()

    def test_only_approved_marketplace_paths_are_allowed(self) -> None:
        self.fixture.write_valid_package()
        for relative_path in (
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
        ):
            self.fixture.write_json(relative_path, {})

        self.assertEqual(
            VALIDATOR.validate_forbidden_components(self.fixture.root), []
        )

        for relative_path in (
            "marketplace.json",
            "nested/marketplace.json",
            ".agents/marketplace.json",
            ".claude-plugin/nested/marketplace.json",
        ):
            with self.subTest(relative_path=relative_path):
                self.fixture.write_json(relative_path, {})
                self.assert_issue_contains(
                    VALIDATOR.validate_forbidden_components(self.fixture.root),
                    relative_path,
                )
                (self.fixture.root / relative_path).unlink()

    def test_roadmap_identifiers_do_not_leak_into_package_facing_names(self) -> None:
        self.fixture.write_valid_package()
        skill_path = self.fixture.root / "skills/implementing-staged-plans/SKILL.md"
        skill_path.write_text(VALID_SKILL + "\n## INC-001 Review Role\n")

        self.assert_issue_contains(
            VALIDATOR.validate_forbidden_components(self.fixture.root),
            "roadmap-specific identifier INC-001",
        )


class CompletePackageTests(PackageValidationTestCase):
    def test_required_authority_assets_are_regular_files(self) -> None:
        for missing_path in (
            AUTHORITY_REFERENCE,
            AUTHORITY_SCRIPT,
            STATE_REFERENCE,
            STATE_SCRIPT,
            PREPARATION_REFERENCE,
            PREPARATION_SCRIPT,
            EXECUTION_REFERENCE,
            EXECUTION_SCRIPT,
            REVIEW_REFERENCE,
            REVIEW_SCRIPT,
            CONTINUITY_REFERENCE,
            CONTINUITY_SCRIPT,
            CHECKPOINT_REFERENCE,
            CHECKPOINT_SCRIPT,
            DISCOVERY_REFERENCE,
            DISCOVERY_SCRIPT,
        ):
            with self.subTest(missing_path=missing_path):
                self.fixture.write_valid_package()
                (self.fixture.root / missing_path).unlink()
                self.assert_issue_contains(
                    VALIDATOR.validate_authority_assets(self.fixture.root),
                    missing_path,
                )

    def test_required_authority_assets_reject_symlinks(self) -> None:
        for linked_path in (
            AUTHORITY_REFERENCE,
            AUTHORITY_SCRIPT,
            STATE_REFERENCE,
            STATE_SCRIPT,
            PREPARATION_REFERENCE,
            PREPARATION_SCRIPT,
            EXECUTION_REFERENCE,
            EXECUTION_SCRIPT,
            REVIEW_REFERENCE,
            REVIEW_SCRIPT,
            CONTINUITY_REFERENCE,
            CONTINUITY_SCRIPT,
            CHECKPOINT_REFERENCE,
            CHECKPOINT_SCRIPT,
            DISCOVERY_REFERENCE,
            DISCOVERY_SCRIPT,
        ):
            with self.subTest(linked_path=linked_path):
                self.fixture.write_valid_package()
                path = self.fixture.root / linked_path
                path.unlink()
                path.symlink_to(self.fixture.root / ".codex-plugin/plugin.json")
                self.assert_issue_contains(
                    VALIDATOR.validate_authority_assets(self.fixture.root),
                    linked_path,
                )

    def test_valid_minimal_package_returns_no_issues(self) -> None:
        self.fixture.write_valid_package()

        self.assertEqual(VALIDATOR.validate_package(self.fixture.root), [])

    def test_production_scripts_and_three_manifest_identities_are_required(self) -> None:
        self.fixture.write_valid_package()
        for script in (*PLAN_A_SCRIPTS, *PLAN_B_SCRIPTS):
            with self.subTest(script=script):
                path = self.fixture.root / script
                original = path.read_bytes()
                path.unlink()
                self.assert_issue_contains(
                    VALIDATOR.validate_package(self.fixture.root), script
                )
                path.write_bytes(original)
        claude = self.fixture.root / ".claude-plugin/plugin.json"
        value = json.loads(claude.read_text(encoding="utf-8"))
        value["version"] = "0.1.0"
        self.fixture.write_json(".claude-plugin/plugin.json", value)
        self.assert_issue_contains(
            VALIDATOR.validate_package(self.fixture.root), "version must equal '0.1.2'"
        )

    def test_package_digest_inventory_is_sorted_and_excludes_repository_surfaces(self) -> None:
        self.fixture.write_valid_package()
        self.fixture.write("docs/private.md", "excluded\n")
        self.fixture.write("tests/test_private.py", "excluded\n")
        self.fixture.write(".claude-plugin/private.json", "excluded\n")
        self.fixture.write("skills/implementing-staged-plans/cache.tmp", "included\n")

        digests = VALIDATOR.package_file_digests(self.fixture.root)

        self.assertEqual(list(digests), sorted(digests))
        self.assertIn(".codex-plugin/plugin.json", digests)
        self.assertIn("skills/implementing-staged-plans/cache.tmp", digests)
        self.assertNotIn("docs/private.md", digests)
        self.assertNotIn("tests/test_private.py", digests)
        self.assertNotIn(".claude-plugin/private.json", digests)

    def test_package_digest_inventory_records_an_unreadable_file(self) -> None:
        self.fixture.write_valid_package()
        unreadable = self.fixture.root / "skills/implementing-staged-plans/SKILL.md"
        real_read_bytes = Path.read_bytes

        def read_bytes(path: Path) -> bytes:
            if path == unreadable:
                raise OSError("injected read failure")
            return real_read_bytes(path)

        with mock.patch.object(Path, "read_bytes", autospec=True, side_effect=read_bytes):
            try:
                digests, issues = VALIDATOR._package_file_inventory(self.fixture.root)
            except OSError as error:
                self.fail(f"package inventory leaked a file read failure: {error}")

        relative = "skills/implementing-staged-plans/SKILL.md"
        self.assertNotIn(relative, digests)
        self.assert_issue_contains(issues, f"{relative}: could not be read")

    def test_package_digest_inventory_reports_unscannable_directory_relatively(
        self,
    ) -> None:
        self.fixture.write_valid_package()
        target = (
            self.fixture.root
            / "skills/implementing-staged-plans/scripts"
        )
        real_scandir = os.scandir

        def scandir(path):
            if Path(path) == target:
                raise OSError("injected scan failure")
            return real_scandir(path)

        with mock.patch.object(os, "scandir", side_effect=scandir):
            _digests, issues = VALIDATOR._package_file_inventory(
                self.fixture.root
            )

        self.assertIn(
            "skills/implementing-staged-plans/scripts: could not be scanned: "
            "injected scan failure",
            issues,
        )
        self.assertFalse(any(str(self.fixture.root) in issue for issue in issues))

    def test_installed_comparison_reports_changed_missing_unexpected_and_symlink(self) -> None:
        self.fixture.write_valid_package()
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory)
            for relative, _digest in VALIDATOR.package_file_digests(
                self.fixture.root
            ).items():
                source = self.fixture.root / relative
                target = installed / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            self.assertEqual(
                VALIDATOR.validate_installed_copy(self.fixture.root, installed), []
            )
            (installed / ".codex-plugin/plugin.json").write_text("changed\n")
            missing = installed / PLAN_A_SCRIPTS[0]
            missing.unlink()
            unexpected = installed / "skills/implementing-staged-plans/unexpected.txt"
            unexpected.write_text("unexpected\n")
            linked = installed / PLAN_A_SCRIPTS[1]
            linked.unlink()
            linked.symlink_to(unexpected)

            issues = VALIDATOR.validate_installed_copy(self.fixture.root, installed)

            for expected in ("changed", "missing", "unexpected", "symlink"):
                self.assert_issue_contains(issues, expected)

    def test_ordinary_validation_does_not_look_up_an_installed_copy(self) -> None:
        self.fixture.write_valid_package()
        with mock.patch.object(
            VALIDATOR,
            "validate_installed_copy",
            side_effect=AssertionError("installed lookup reached"),
        ):
            self.assertEqual(VALIDATOR.validate_package(self.fixture.root), [])

    def test_cli_success_and_failure_are_deterministic(self) -> None:
        self.fixture.write_valid_package()
        output = io.StringIO()
        with redirect_stdout(output):
            return_code = VALIDATOR.main([str(self.fixture.root)])
        self.assertEqual(return_code, 0)
        self.assertEqual(output.getvalue(), "Package validation passed\n")

        (self.fixture.root / ".codex-plugin/plugin.json").write_text("{}\n")
        output = io.StringIO()
        with redirect_stdout(output):
            return_code = VALIDATOR.main([str(self.fixture.root)])
        self.assertEqual(return_code, 1)
        issue_lines = output.getvalue().splitlines()
        self.assertGreater(len(issue_lines), 1)
        self.assertEqual(issue_lines, sorted(issue_lines))

    def test_cli_help_preserves_argparse_success_status(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            return_code = VALIDATOR.main(["--help"])

        self.assertEqual(return_code, 0)
        self.assertIn("usage: validate_package.py", output.getvalue())

        errors = io.StringIO()
        with redirect_stderr(errors):
            invalid_return_code = VALIDATOR.main(["--unknown-option"])
        self.assertEqual(invalid_return_code, 1)
        self.assertIn("unrecognized arguments", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
