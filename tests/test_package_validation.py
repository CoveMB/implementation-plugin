import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


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


VALID_MANIFEST = {
    "name": "implementation-plugin",
    "version": "0.1.0",
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
        self.write("skills/implementing-staged-plans/SKILL.md", VALID_SKILL)
        self.write(
            "skills/implementing-staged-plans/agents/openai.yaml",
            VALID_OPENAI_YAML,
        )
        self.write(AUTHORITY_REFERENCE, "# Program Authority\n")
        self.write(AUTHORITY_SCRIPT, "# reusable authority validator\n")


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
            "marketplace.json",
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
        for missing_path in (AUTHORITY_REFERENCE, AUTHORITY_SCRIPT):
            with self.subTest(missing_path=missing_path):
                self.fixture.write_valid_package()
                (self.fixture.root / missing_path).unlink()
                self.assert_issue_contains(
                    VALIDATOR.validate_authority_assets(self.fixture.root),
                    missing_path,
                )

    def test_valid_minimal_package_returns_no_issues(self) -> None:
        self.fixture.write_valid_package()

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


if __name__ == "__main__":
    unittest.main()
