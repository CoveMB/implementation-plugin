import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
READER_DOCUMENTS = (
    Path("README.md"),
    Path("docs/installation.md"),
    Path("docs/workflows.md"),
    Path("docs/reference.md"),
    Path("docs/troubleshooting.md"),
    Path("docs/maintainers.md"),
)
PLAN_A_GUIDES = (
    Path("implementing-staged-plans-consolidated-design-plan-final.md"),
    Path("implementing-staged-plans-bootstrap-execution-review-runbook.md"),
)
CODEX_MANIFEST = Path(".codex-plugin/plugin.json")
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
CLAUDE_MANIFEST = Path(".claude-plugin/plugin.json")
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
UNFINISHED_MARKER = re.compile(
    r"\b(?:FIXME|TBD|TODO)\b|{{|}}",
    re.IGNORECASE,
)


def load_json(relative_path: Path) -> dict[str, object]:
    return json.loads(
        (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
    )


def reader_text(relative_path: Path) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")


class DistributionMetadataTests(unittest.TestCase):
    def test_platform_metadata_is_present_and_consistent(self) -> None:
        codex_manifest = load_json(CODEX_MANIFEST)
        codex_marketplace = load_json(CODEX_MARKETPLACE)
        claude_manifest = load_json(CLAUDE_MANIFEST)
        claude_marketplace = load_json(CLAUDE_MARKETPLACE)

        self.assertEqual(codex_manifest["name"], "implementation-plugin")
        self.assertEqual(codex_manifest["version"], "0.1.2")
        self.assertEqual(codex_manifest["skills"], "./skills/")
        self.assertEqual(claude_manifest["name"], codex_manifest["name"])
        self.assertEqual(claude_manifest["version"], codex_manifest["version"])
        self.assertEqual(claude_manifest["skills"], codex_manifest["skills"])
        self.assertEqual(
            claude_manifest["description"], codex_manifest["description"]
        )
        self.assertEqual(
            codex_marketplace["name"], "implementation-workflows"
        )
        self.assertEqual(
            claude_marketplace["name"], "implementation-workflows"
        )
        self.assertEqual(
            codex_marketplace["plugins"][0]["name"],
            "implementation-plugin",
        )
        self.assertEqual(
            claude_marketplace["plugins"][0]["name"],
            "implementation-plugin",
        )
        self.assertEqual(
            claude_marketplace["plugins"][0]["version"],
            codex_manifest["version"],
        )
        self.assertEqual(
            claude_marketplace["plugins"][0]["description"],
            codex_manifest["description"],
        )


class ReaderDocumentationTests(unittest.TestCase):
    def test_required_reader_documents_exist(self) -> None:
        for relative_path in READER_DOCUMENTS:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((REPOSITORY_ROOT / relative_path).is_file())

    def test_relative_links_resolve(self) -> None:
        for relative_path in READER_DOCUMENTS:
            for raw_target in LINK_PATTERN.findall(reader_text(relative_path)):
                parsed = urlparse(raw_target)
                if parsed.scheme or raw_target.startswith("#"):
                    continue
                target = unquote(parsed.path)
                if not target:
                    continue
                resolved = (REPOSITORY_ROOT / relative_path).parent / target
                with self.subTest(source=relative_path, target=raw_target):
                    self.assertTrue(resolved.resolve().is_file())

    def test_code_fences_are_balanced_and_markers_are_resolved(self) -> None:
        for relative_path in READER_DOCUMENTS:
            text = reader_text(relative_path)
            with self.subTest(relative_path=relative_path):
                self.assertEqual(
                    sum(
                        line.startswith("```")
                        for line in text.splitlines()
                    )
                    % 2,
                    0,
                )
                self.assertIsNone(UNFINISHED_MARKER.search(text))
                self.assertNotIn("ISP-001", text)

    def test_installation_and_invocation_commands_are_documented(self) -> None:
        installation = reader_text(Path("docs/installation.md"))
        reference = reader_text(Path("docs/reference.md"))
        for command in (
            "codex plugin marketplace add",
            "codex plugin add implementation-plugin@implementation-workflows",
            "claude plugin marketplace add",
            "claude plugin install implementation-plugin@implementation-workflows",
            "claude --plugin-dir",
        ):
            self.assertIn(command, installation)
        for invocation in (
            "$implementing-staged-plans",
            "/implementation-plugin:implementing-staged-plans",
            "/implementing-staged-plans",
        ):
            self.assertIn(invocation, reference)

    def test_manual_skill_copy_examples_fail_closed(self) -> None:
        installation = reader_text(Path("docs/installation.md"))
        copy_lines = {
            line.strip()
            for line in installation.splitlines()
            if "cp -R" in line
        }
        pattern = re.compile(
            r"^test ! -e (?P<destination>\S+) && "
            r"cp -R \S+ (?P=destination)$"
        )
        expected_destinations = {
            ".agents/skills/implementing-staged-plans",
            "~/.agents/skills/implementing-staged-plans",
            ".claude/skills/implementing-staged-plans",
            "~/.claude/skills/implementing-staged-plans",
        }

        matched_destinations = {
            match.group("destination")
            for line in copy_lines
            if (match := pattern.fullmatch(line))
        }
        self.assertEqual(matched_destinations, expected_destinations)
        self.assertEqual(len(copy_lines), len(expected_destinations))

    def test_windows_and_current_claude_routes_are_documented(self) -> None:
        installation = reader_text(Path("docs/installation.md"))
        for required_text in (
            "Claude Code in VS Code",
            "/plugins",
            "claude --plugin-dir /absolute/path/to/implementation-plugin-0.1.2.zip",
            "```powershell",
            "if (Test-Path $skillDestination)",
            'throw "Destination already exists: $skillDestination"',
            "Copy-Item -Recurse $skillSource $skillDestination",
            ".agents\\skills\\implementing-staged-plans",
            ".claude\\skills\\implementing-staged-plans",
        ):
            self.assertIn(required_text, installation)
        self.assertEqual(installation.count("```powershell"), 4)
        self.assertEqual(
            installation.count("if (Test-Path $skillDestination)"),
            4,
        )

    def test_reader_routes_describe_the_complete_supported_lifecycle(self) -> None:
        documents = {
            path: reader_text(path)
            for path in (
                Path("docs/workflows.md"),
                Path("docs/reference.md"),
                Path("docs/troubleshooting.md"),
                *PLAN_A_GUIDES,
            )
        }
        combined = "\n".join(documents.values())
        for required in (
            "Create a New Program",
            "Activate a Generated Program",
            "Before Production Modification",
            "Prepare Review and Diff Disposition",
            "Dispose the Current Diff",
            "Continue an Accepted Program",
            "Authorize a Successor Increment",
            "Resolve a Blocked Program",
            "Close a Final Program",
            "accept-stop",
            "accept-continue",
            "accepted-state-continuation",
            "current_increment_authority_binding",
            "blocked-recovery",
            "implementation-closure-storage/v1",
            "legacy-rollover-upgrade-required",
            "blocked-transaction-required",
            "program-revision-workflow-required",
            "unsupported-program-mutation",
        ):
            self.assertIn(required, combined)
        self.assertIn("Plan A closure", combined)
        self.assertNotIn("execute `INC-001` under `approval:full-increment`", combined)
        continuity = reader_text(
            Path("skills/implementing-staged-plans/references/continuity-closure.md")
        )
        self.assertIn("## Apply Prompt-Bound Successor Rollover", continuity)
        self.assertIn("legacy-rollover-upgrade-required", continuity)
        for path, text in documents.items():
            with self.subTest(path=path):
                self.assertNotRegex(
                    text.lower(),
                    r"(?:handoff|retrieved prompt|assistant-quoted prompt).*authoriz(?:e|es) mutation",
                )

    def test_distribution_descriptions_do_not_claim_unsupported_program_mutations(self) -> None:
        descriptions = (
            ("codex manifest", str(load_json(CODEX_MANIFEST)["description"])),
            ("claude manifest", str(load_json(CLAUDE_MANIFEST)["description"])),
            (
                "claude marketplace",
                str(load_json(CLAUDE_MARKETPLACE)["plugins"][0]["description"]),
            ),
            (
                "openai agent metadata",
                reader_text(
                    Path("skills/implementing-staged-plans/agents/openai.yaml")
                ),
            ),
        )
        for label, description in descriptions:
            with self.subTest(label=label):
                self.assertNotRegex(
                    description.lower(),
                    r"\b(?:revise|revision|supersede|supersession|cancel|cancellation)\b",
                )


if __name__ == "__main__":
    unittest.main()
