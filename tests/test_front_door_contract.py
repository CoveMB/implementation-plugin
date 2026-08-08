import importlib.util
import json
import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "implementing-staged-plans"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
OPENAI_METADATA_PATH = SKILL_ROOT / "agents" / "openai.yaml"
VALIDATOR_PATH = SKILL_ROOT / "scripts" / "validate_package.py"

SPEC = importlib.util.spec_from_file_location("validate_package", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load validator from {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

EXPECTED_MANIFEST = {
    "name": "implementation-plugin",
    "version": "0.1.0",
    "description": "Run approved implementation programs one reviewable increment at a time.",
    "skills": "./skills/",
}

OBLIGATION_PATTERNS = {
    "locate named or implied program manifest": (
        r"program manifest",
        r"named or implied",
    ),
    "load current bindings": (
        r"source",
        r"program",
        r"approval",
        r"workspace",
        r"status",
    ),
    "revalidate repository and state": (
        r"revalidate",
        r"repository",
        r"handoff or prompt",
    ),
    "refuse before universal early gates": (
        r"program approval",
        r"workspace selection",
        r"exact-file plan",
        r"stop",
    ),
    "separate approval mode from action authority": (
        r"approval mode",
        r"consequential-action authority",
        r"separate",
    ),
    "discover only relevant capabilities": (
        r"discover only",
        r"current stage",
        r"capabilit",
    ),
    "prevent recursive invocation": (
        r"recursive invocation",
        r"implementing-staged-plans",
    ),
    "route only to implemented procedures": (
        r"implemented procedure",
        r"route",
    ),
    "disclose manual bootstrap fallback": (
        r"bootstrap runbook",
        r"manual safeguard",
        r"mechanical enforcement",
    ),
    "return next legal action and stop": (
        r"next legal action",
        r"stop",
    ),
}


class FrontDoorContractTests(unittest.TestCase):
    def test_actual_repository_package_is_valid(self) -> None:
        self.assertEqual(VALIDATOR.validate_package(REPOSITORY_ROOT), [])

    def test_manifest_matches_the_exact_approved_contract(self) -> None:
        manifest_path = REPOSITORY_ROOT / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest, EXPECTED_MANIFEST)

    def test_front_door_is_concise_and_covers_every_obligation(self) -> None:
        skill_markdown = SKILL_PATH.read_text(encoding="utf-8")
        self.assertLess(len(skill_markdown.splitlines()), 250)

        for obligation, patterns in OBLIGATION_PATTERNS.items():
            with self.subTest(obligation=obligation):
                for pattern in patterns:
                    self.assertRegex(skill_markdown, re.compile(pattern, re.IGNORECASE))

    def test_package_has_no_forbidden_or_broken_surface(self) -> None:
        self.assertEqual(VALIDATOR.validate_forbidden_components(REPOSITORY_ROOT), [])
        self.assertEqual(VALIDATOR.validate_markdown_links(REPOSITORY_ROOT), [])

    def test_ui_metadata_explicitly_invokes_the_approved_skill(self) -> None:
        metadata = OPENAI_METADATA_PATH.read_text(encoding="utf-8")
        self.assertIn('display_name: "Implementing Staged Plans"', metadata)
        self.assertIn("$implementing-staged-plans", metadata)


if __name__ == "__main__":
    unittest.main()
