# Implementation Plugin Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add beginner-friendly documentation and working Codex and Claude distribution metadata for the existing `implementing-staged-plans` skill.

**Architecture:** Keep `skills/implementing-staged-plans/` as the one canonical workflow. Add a progressive README-and-guides documentation layer, two platform marketplace catalogs, and a Claude manifest. Extend validation only enough to recognize the two exact marketplace paths and verify the new reader-facing contract.

**Tech Stack:** Markdown, JSON, Python 3 standard-library `unittest`, Codex CLI 0.146.0, current official Codex and Claude plugin documentation.

## Global Constraints

- Preserve the approved design at `docs/superpowers/specs/2026-08-09-implementation-plugin-documentation-design.md`.
- Preserve all pre-existing user changes in `skills/implementing-staged-plans/agents/openai.yaml`, `skills/implementing-staged-plans/scripts/validate_package.py`, and `tests/test_package_validation.py`.
- Do not edit `implementation-programs/ISP-001/` or any accepted lifecycle evidence.
- Keep `.codex-plugin/plugin.json` at its exact four-field contract.
- Use fictional examples; do not use `ISP-001` as reusable user documentation.
- Keep the skill and its references canonical; user guides explain behavior without copying the full policy.
- Use exact platform commands and distinguish current, conditional, and unpublished routes.
- Run an Editorial Humanizer factual-integrity pass without changing commands, identifiers, conditions, or safety boundaries.
- Do not stage, commit, push, install, publish, share, submit, release, or deploy.
- Execute inline in the current session. Do not dispatch subagents.

---

## File Structure

**Create:**

- `README.md` — beginner entry point and five-minute start.
- `docs/installation.md` — Codex and Claude installation matrix and exact steps.
- `docs/workflows.md` — task-based prompts for every lifecycle action.
- `docs/reference.md` — terminology, approval modes, state, authority, and invocation reference.
- `docs/troubleshooting.md` — symptom-led safe recovery guidance.
- `docs/maintainers.md` — packaging map, freshness checks, and validation commands.
- `.agents/plugins/marketplace.json` — Codex repository marketplace catalog.
- `.claude-plugin/plugin.json` — Claude plugin manifest.
- `.claude-plugin/marketplace.json` — Claude repository marketplace catalog.
- `tests/test_distribution_documentation.py` — deterministic distribution and documentation contract.

**Modify:**

- `skills/implementing-staged-plans/scripts/validate_package.py` — allow only the two approved marketplace paths.
- `tests/test_package_validation.py` — protect the new narrow marketplace exception.

**Do not modify:**

- `.codex-plugin/plugin.json`
- `skills/implementing-staged-plans/SKILL.md`
- `skills/implementing-staged-plans/agents/openai.yaml`
- `implementation-programs/ISP-001/**`

---

### Task 1: Permit only the approved marketplace catalogs

**Files:**

- Modify: `tests/test_package_validation.py`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`

**Interfaces:**

- Consumes: `validate_forbidden_components(repository_root: Path) -> list[str]`
- Produces: exact-path exception for `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json`

- [ ] **Step 1: Add the failing marketplace-path test**

In `ForbiddenSurfaceTests`, remove `marketplace.json` from the generic filename tuple and add:

```python
def test_only_approved_marketplace_paths_are_allowed(self) -> None:
    for relative_path in (
        ".agents/plugins/marketplace.json",
        ".claude-plugin/marketplace.json",
    ):
        with self.subTest(relative_path=relative_path):
            self.fixture.write_valid_package()
            self.fixture.write_json(relative_path, {})
            issues = VALIDATOR.validate_forbidden_components(self.fixture.root)
            self.assertFalse(
                any(relative_path in issue for issue in issues),
                issues,
            )
            (self.fixture.root / relative_path).unlink()

    for relative_path in (
        "marketplace.json",
        "nested/marketplace.json",
    ):
        with self.subTest(relative_path=relative_path):
            self.fixture.write_valid_package()
            self.fixture.write_json(relative_path, {})
            self.assert_issue_contains(
                VALIDATOR.validate_forbidden_components(self.fixture.root),
                relative_path,
            )
            (self.fixture.root / relative_path).unlink()
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation.ForbiddenSurfaceTests.test_only_approved_marketplace_paths_are_allowed -v
```

Expected: FAIL because both approved nested catalogs are still rejected as forbidden `marketplace.json` files.

- [ ] **Step 3: Add the narrow validator exception**

Add beside `FORBIDDEN_FILENAMES`:

```python
ALLOWED_MARKETPLACE_PATHS = {
    Path(".agents/plugins/marketplace.json"),
    Path(".claude-plugin/marketplace.json"),
}
```

Update the filename loop:

```python
for forbidden_name in sorted(FORBIDDEN_FILENAMES):
    for path in sorted(repository_root.rglob(forbidden_name)):
        relative_path = path.relative_to(repository_root)
        if relative_path in ALLOWED_MARKETPLACE_PATHS:
            continue
        issues.append(
            "forbidden component or identity surface: "
            f"{relative_path.as_posix()}"
        )
```

- [ ] **Step 4: Run focused package-validation tests and verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation.ForbiddenSurfaceTests -v
```

Expected: all `ForbiddenSurfaceTests` pass, including the pre-existing roadmap-identifier test.

- [ ] **Step 5: Review the diff without staging or committing**

Confirm the earlier implicit-invocation parsing and tests remain byte-for-byte present outside the new marketplace change.

---

### Task 2: Define the documentation and distribution contract

**Files:**

- Create: `tests/test_distribution_documentation.py`

**Interfaces:**

- Consumes: repository files and JSON metadata
- Produces: focused `unittest` contract for packaging, links, examples, commands, and unfinished markers

- [ ] **Step 1: Create the failing documentation test module**

Create a standard-library test with these constants and helpers:

```python
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
CODEX_MANIFEST = Path(".codex-plugin/plugin.json")
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
CLAUDE_MANIFEST = Path(".claude-plugin/plugin.json")
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
UNFINISHED_MARKER = re.compile(r"\b(?:FIXME|TBD|TODO)\b|{{|}}", re.IGNORECASE)


def load_json(relative_path: Path) -> dict[str, object]:
    return json.loads((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))


def reader_text(relative_path: Path) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
```

Add test classes with these contracts:

```python
class DistributionMetadataTests(unittest.TestCase):
    def test_platform_metadata_is_present_and_consistent(self) -> None:
        codex_manifest = load_json(CODEX_MANIFEST)
        codex_marketplace = load_json(CODEX_MARKETPLACE)
        claude_manifest = load_json(CLAUDE_MANIFEST)
        claude_marketplace = load_json(CLAUDE_MARKETPLACE)

        self.assertEqual(codex_manifest["name"], "implementation-plugin")
        self.assertEqual(codex_manifest["version"], "0.1.0")
        self.assertEqual(codex_manifest["skills"], "./skills/")
        self.assertEqual(claude_manifest["name"], codex_manifest["name"])
        self.assertEqual(claude_manifest["version"], codex_manifest["version"])
        self.assertEqual(claude_manifest["skills"], codex_manifest["skills"])
        self.assertEqual(codex_marketplace["name"], "implementation-workflows")
        self.assertEqual(claude_marketplace["name"], "implementation-workflows")
        self.assertEqual(codex_marketplace["plugins"][0]["name"], "implementation-plugin")
        self.assertEqual(claude_marketplace["plugins"][0]["name"], "implementation-plugin")


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
                    sum(line.startswith("```") for line in text.splitlines()) % 2,
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
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation -v
```

Expected: ERROR or FAIL for missing marketplace manifests and reader documents.

- [ ] **Step 3: Keep the failing test as the contract for Tasks 3–6**

Do not weaken missing-file, link, marker, identity, version, command, or invocation assertions to make partial work pass.

---

### Task 3: Add Codex and Claude distribution metadata

**Files:**

- Create: `.agents/plugins/marketplace.json`
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`

**Interfaces:**

- Consumes: exact `.codex-plugin/plugin.json` identity and `skills/` layout
- Produces: `implementation-plugin@implementation-workflows` on both marketplace systems

- [ ] **Step 1: Add the Codex marketplace catalog**

Use:

```json
{
  "name": "implementation-workflows",
  "interface": {
    "displayName": "Implementation Workflows"
  },
  "plugins": [
    {
      "name": "implementation-plugin",
      "source": {
        "source": "local",
        "path": "./"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

- [ ] **Step 2: Add the Claude manifest**

Use:

```json
{
  "name": "implementation-plugin",
  "displayName": "Implementation Plugin",
  "version": "0.1.0",
  "description": "Run approved implementation programs one reviewable increment at a time.",
  "repository": "https://github.com/CoveMB/implementation-plugin",
  "skills": "./skills/"
}
```

- [ ] **Step 3: Add the Claude marketplace catalog**

Use:

```json
{
  "name": "implementation-workflows",
  "owner": {
    "name": "CoveMB"
  },
  "plugins": [
    {
      "name": "implementation-plugin",
      "source": "./",
      "description": "Run approved implementation programs one reviewable increment at a time.",
      "version": "0.1.0"
    }
  ]
}
```

- [ ] **Step 4: Run the metadata test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation.DistributionMetadataTests -v
```

Expected: PASS.

- [ ] **Step 5: Run package validation**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: `Package validation passed`.

---

### Task 4: Write the README and installation guide

**Files:**

- Create: `README.md`
- Create: `docs/installation.md`

**Interfaces:**

- Consumes: marketplace selectors, invocation names, official platform commands
- Produces: beginner explanation, five-minute route, complete installation matrix

- [ ] **Step 1: Write the README front door**

Use this section order:

```markdown
# Implementation Plugin

Run an approved implementation plan in small, reviewable increments without treating approval as permission for every later action.

## Why staged implementation?
## What this plugin does
## When to use it
## When not to use it
## Five-minute start
## Choose what you want to do
## Installation
## Safety boundary
## Documentation
```

The five-minute prompt uses fictional `LIBRARY-001`, an approved plan at `docs/library-search-plan.md`, and `approval:standard`. It must say the first response is a read-only orientation or the smallest legal next action, not guaranteed code changes.

- [ ] **Step 2: Write the support matrix in `docs/installation.md`**

Include columns for host, route, availability, persistence, and invocation. Cover Codex desktop marketplace, Codex CLI marketplace, local Codex marketplace, Codex repository and personal standalone skills, `$skill-installer`, Claude Desktop, Claude interactive plugin commands, Claude CLI, `--plugin-dir`, personal and project Claude skills, and conditional `--plugin-url`.

- [ ] **Step 3: Write exact Codex instructions**

Include:

```bash
codex plugin marketplace add CoveMB/implementation-plugin --ref main
codex plugin add implementation-plugin@implementation-workflows
codex plugin list
```

Also document local source registration:

```bash
codex plugin marketplace add /absolute/path/to/implementation-plugin
codex plugin add implementation-plugin@implementation-workflows
```

State that adding a marketplace does not install its plugin and that public-directory discovery requires separate publication.

- [ ] **Step 4: Write exact Claude instructions**

Include interactive and non-interactive forms:

```text
/plugin marketplace add CoveMB/implementation-plugin
/plugin install implementation-plugin@implementation-workflows
/reload-plugins
```

```bash
claude plugin marketplace add CoveMB/implementation-plugin
claude plugin install implementation-plugin@implementation-workflows
claude --plugin-dir /absolute/path/to/implementation-plugin
```

State that Claude marketplace runtime was not verified locally because Claude CLI is absent.

- [ ] **Step 5: Run reader-document tests and inspect the expected remaining failures**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation.ReaderDocumentationTests -v
```

Expected: missing workflow, reference, troubleshooting, and maintainer files still fail; README and installation content introduces no marker or fence failure.

---

### Task 5: Write the workflow and reference guides

**Files:**

- Create: `docs/workflows.md`
- Create: `docs/reference.md`

**Interfaces:**

- Consumes: canonical behavior in `SKILL.md` and six reference files
- Produces: copyable user workflows and compact factual reference

- [ ] **Step 1: Write all task-based workflow examples**

Use the repeated structure “Use this when,” “What to provide,” “Example,” “What happens next,” and “Where it stops.” Cover all 15 workflows named in the design. Use fictional `LIBRARY-001`, `INC-002`, `/work/library-catalog`, and `docs/library-search-plan.md` consistently.

The initial example begins:

```text
Use $implementing-staged-plans with the approved plan at docs/library-search-plan.md.
Work in /work/library-catalog under approval:standard.
Start with read-only orientation, show me the proposed program and workspace binding,
and stop at the first required approval.
```

The later-action example must authorize one exact action and explicitly exclude others:

```text
Authorize only the commit described in the accepted packet for INC-002.
Do not push, create a pull request, publish, release, deploy, or begin INC-003.
```

- [ ] **Step 2: Write the approval-mode reference**

Document the exact five modes from `state-authorization.md`. Include scope, routine plan pause, diff acceptance owner, cross-increment continuation, and mandatory stop. State that an explicit user gate overrides a mode that would normally omit that pause.

- [ ] **Step 3: Write terminology and authority references**

Define program, increment, exact-file plan, workspace binding, action authorization, evidence, review packet, handoff, reconciliation, and closure packet in user language. Explain approval mode versus action authorization versus external-action authorization.

- [ ] **Step 4: Run content-contract tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation.ReaderDocumentationTests.test_installation_and_invocation_commands_are_documented -v
```

Expected: PASS.

---

### Task 6: Write troubleshooting and maintainer guides

**Files:**

- Create: `docs/troubleshooting.md`
- Create: `docs/maintainers.md`

**Interfaces:**

- Consumes: actual validation commands, platform limits, and safe recovery boundaries
- Produces: symptom-led recovery and maintenance checklist

- [ ] **Step 1: Write symptom-led troubleshooting**

For each approved symptom, use “Likely cause,” “Safe checks,” and “Next action.” Never recommend resetting, discarding, broad cache deletion, or bypassing gates as the routine fix.

- [ ] **Step 2: Write maintainer documentation**

Include the exact file map, shared-skill/no-fork rule, manifest version synchronization, source-freshness links, and these commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation -v
PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
git diff --check
codex plugin add --help
codex plugin marketplace add --help
```

State that these checks do not prove Claude runtime loading, marketplace publication, plugin installation, live agent behavior, or human review quality.

- [ ] **Step 3: Run the complete focused documentation contract**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation -v
```

Expected: PASS.

---

### Task 7: Apply the natural-language editorial pass

**Files:**

- Modify: `README.md`
- Modify: `docs/installation.md`
- Modify: `docs/workflows.md`
- Modify: `docs/reference.md`
- Modify: `docs/troubleshooting.md`
- Modify: `docs/maintainers.md`

**Interfaces:**

- Consumes: complete factual draft
- Produces: natural, concise reader-facing prose with unchanged contracts

- [ ] **Step 1: Map protected anchors before editing**

Protect every command, invocation name, file path, approval mode, lifecycle state, limitation, source link, and explicit authorization boundary.

- [ ] **Step 2: Apply Editorial Humanizer guidance**

Remove chatbot framing, inflated claims, repeated summaries, empty transitions, padded lists, formulaic contrast, and unnecessary jargon. Keep technical terms where they define actual behavior.

- [ ] **Step 3: Re-run the focused documentation contract**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation -v
```

Expected: PASS with every protected anchor intact.

- [ ] **Step 4: Read the README and one end-to-end workflow aloud mentally**

Confirm that a reader new to staged implementation can identify the purpose, first step, expected stop, and next decision without consulting internal program records.

---

### Task 8: Verify the coherent final tree

**Files:**

- Verify all files named in this plan

**Interfaces:**

- Consumes: final unstaged documentation, packaging, tests, and preserved user changes
- Produces: deterministic evidence and explicit residual limitations

- [ ] **Step 1: Run focused package and documentation tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_distribution_documentation -v
```

Expected: PASS.

- [ ] **Step 2: Run package validation**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: `Package validation passed`.

- [ ] **Step 3: Run the complete unit-test suite once**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
```

Expected: all tests pass.

- [ ] **Step 4: Run whitespace validation**

```bash
git diff --check
```

Expected: no output and exit status 0.

- [ ] **Step 5: Verify current Codex CLI command shapes**

```bash
codex plugin add --help
codex plugin marketplace add --help
```

Expected: help lists `plugin add` selectors and local, GitHub shorthand, HTTPS, and SSH marketplace sources.

- [ ] **Step 6: Verify preservation and scope**

Inspect `git status --short`, `git diff --stat`, and the final diff. Confirm:

- the pre-existing implicit-invocation changes remain;
- no `implementation-programs/ISP-001/` path changed;
- `.codex-plugin/plugin.json` is unchanged;
- no file was staged or committed;
- every changed line traces to documentation, distribution metadata, or its validation.

- [ ] **Step 7: Report residual limitations**

State that Claude CLI/runtime, marketplace registration, plugin installation, public-directory publication, live workflow behavior, and external actions were not performed or proven.
