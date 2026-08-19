#!/usr/bin/env python3
"""Validate the minimal implementing-staged-plans package contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path


PLUGIN_MANIFEST = Path(".codex-plugin/plugin.json")
CLAUDE_MANIFEST = Path(".claude-plugin/plugin.json")
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
PACKAGE_CONTENT_ROOT = Path("skills/implementing-staged-plans")
PACKAGE_VERSION = "0.1.1"
SKILL_MARKDOWN = Path("skills/implementing-staged-plans/SKILL.md")
OPENAI_METADATA = Path("skills/implementing-staged-plans/agents/openai.yaml")
PROGRAM_AUTHORITY_REFERENCE = Path(
    "skills/implementing-staged-plans/references/program-authority.md"
)
PROGRAM_AUTHORITY_SCRIPT = Path(
    "skills/implementing-staged-plans/scripts/program_authority.py"
)
STATE_AUTHORITY_REFERENCE = Path(
    "skills/implementing-staged-plans/references/state-authorization.md"
)
STATE_AUTHORITY_SCRIPT = Path(
    "skills/implementing-staged-plans/scripts/state_authority.py"
)
REPOSITORY_PREPARATION_REFERENCE = Path(
    "skills/implementing-staged-plans/references/repository-preparation.md"
)
REPOSITORY_PREPARATION_SCRIPT = Path(
    "skills/implementing-staged-plans/scripts/repository_preparation.py"
)
EXECUTION_DISCIPLINE_REFERENCE = Path(
    "skills/implementing-staged-plans/references/execution-discipline.md"
)
EXECUTION_DISCIPLINE_SCRIPT = Path(
    "skills/implementing-staged-plans/scripts/execution_discipline.py"
)
REVIEW_COORDINATION_REFERENCE = Path(
    "skills/implementing-staged-plans/references/review-coordination.md"
)
REVIEW_COORDINATION_SCRIPT = Path(
    "skills/implementing-staged-plans/scripts/review_coordination.py"
)
CONTINUITY_CLOSURE_REFERENCE = Path(
    "skills/implementing-staged-plans/references/continuity-closure.md"
)
CONTINUITY_CLOSURE_SCRIPT = Path(
    "skills/implementing-staged-plans/scripts/continuity_closure.py"
)
APPROVAL_CHECKPOINT_REFERENCE = Path(
    "skills/implementing-staged-plans/references/approval-checkpoints.md"
)
APPROVAL_CHECKPOINT_SCRIPT = Path(
    "skills/implementing-staged-plans/scripts/approval_checkpoint.py"
)
PROGRAM_DISCOVERY_REFERENCE = Path(
    "skills/implementing-staged-plans/references/program-discovery.md"
)
PROGRAM_DISCOVERY_SCRIPT = Path(
    "skills/implementing-staged-plans/scripts/program_discovery.py"
)
PLAN_A_PRODUCTION_SCRIPTS = tuple(
    Path(f"skills/implementing-staged-plans/scripts/{name}.py")
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

EXPECTED_MANIFEST: dict[str, object] = {
    "name": "implementation-plugin",
    "version": PACKAGE_VERSION,
    "description": "Run approved implementation programs one reviewable increment at a time.",
    "skills": "./skills/",
}
FORBIDDEN_FILENAMES = {
    ".app.json",
    ".mcp.json",
    "author.json",
    "hooks.json",
    "marketplace.json",
    "publication.json",
    "publish.json",
    "publisher.json",
}
ALLOWED_MARKETPLACE_PATHS = {
    Path(".agents/plugins/marketplace.json"),
    Path(".claude-plugin/marketplace.json"),
}
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
TEMPLATE_MARKER_PATTERN = re.compile(
    r"\b(?:FIXME|TBD|TODO)\b|{{|}}|<[^>]*(?:placeholder|replace|todo)[^>]*>",
    re.IGNORECASE,
)
ROADMAP_IDENTIFIER_PATTERN = re.compile(
    r"\b(?:INC-\d{3,}|ISP-\d{3,}|P-\d{3,}|REQ-[A-Z0-9-]+)\b"
)


def load_json_object(path: Path) -> tuple[dict[str, object] | None, list[str]]:
    """Load a JSON object and return deterministic validation issues."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"{path}: missing JSON file"]
    except (OSError, UnicodeError) as error:
        return None, [f"{path}: could not be read: {error}"]
    except json.JSONDecodeError as error:
        return None, [f"{path}: must contain valid JSON: {error.msg}"]

    if not isinstance(value, dict):
        return None, [f"{path}: must contain a JSON object"]
    return value, []


def validate_plugin_manifest(repository_root: Path) -> list[str]:
    """Validate the exact approved skills-only plugin manifest."""
    manifest_path = repository_root / PLUGIN_MANIFEST
    if not manifest_path.is_file():
        return [f"{PLUGIN_MANIFEST.as_posix()} is missing"]

    manifest, issues = load_json_object(manifest_path)
    if manifest is None:
        return issues

    expected_fields = set(EXPECTED_MANIFEST)
    if set(manifest) != expected_fields:
        fields = ", ".join(sorted(expected_fields))
        issues.append(
            f"{PLUGIN_MANIFEST.as_posix()} must contain exactly these fields: {fields}"
        )

    for field, expected_value in EXPECTED_MANIFEST.items():
        if manifest.get(field) != expected_value:
            issues.append(
                f"{PLUGIN_MANIFEST.as_posix()} field {field} must equal "
                f"{expected_value!r}"
            )
    return issues


def validate_distribution_identity(repository_root: Path) -> list[str]:
    """Require the same package identity across all three version owners."""
    issues: list[str] = []
    codex, codex_issues = load_json_object(repository_root / PLUGIN_MANIFEST)
    claude, claude_issues = load_json_object(repository_root / CLAUDE_MANIFEST)
    marketplace, marketplace_issues = load_json_object(
        repository_root / CLAUDE_MARKETPLACE
    )
    issues.extend((*codex_issues, *claude_issues, *marketplace_issues))
    if codex is None or claude is None or marketplace is None:
        return issues
    expected_identity = {
        "name": EXPECTED_MANIFEST["name"],
        "version": PACKAGE_VERSION,
        "description": EXPECTED_MANIFEST["description"],
    }
    for path, value in ((PLUGIN_MANIFEST, codex), (CLAUDE_MANIFEST, claude)):
        for field, expected in expected_identity.items():
            if value.get(field) != expected:
                issues.append(
                    f"{path.as_posix()} field {field} must equal {expected!r}"
                )
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1 or not isinstance(
        plugins[0], dict
    ):
        issues.append(
            f"{CLAUDE_MARKETPLACE.as_posix()} must contain exactly one plugin object"
        )
    else:
        plugin = plugins[0]
        for field, expected in expected_identity.items():
            if plugin.get(field) != expected:
                issues.append(
                    f"{CLAUDE_MARKETPLACE.as_posix()} plugin {field} must equal {expected!r}"
                )
    return issues


def _package_file_inventory(root: Path) -> tuple[dict[str, str], list[str]]:
    digests: dict[str, str] = {}
    issues: list[str] = []

    def add_file(path: Path, relative: Path) -> None:
        if path.is_symlink():
            issues.append(f"{relative.as_posix()}: symlink is not allowed")
        elif not path.is_file():
            issues.append(f"{relative.as_posix()}: missing or non-regular file")
        else:
            try:
                digests[relative.as_posix()] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
            except OSError as error:
                issues.append(f"{relative.as_posix()}: could not be read: {error}")

    add_file(root / PLUGIN_MANIFEST, PLUGIN_MANIFEST)
    skill_root = root / PACKAGE_CONTENT_ROOT
    if skill_root.is_symlink() or not skill_root.is_dir():
        issues.append(
            f"{PACKAGE_CONTENT_ROOT.as_posix()}: missing, symlink, or non-directory"
        )
    else:
        stack = [skill_root]
        while stack:
            directory = stack.pop()
            try:
                entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
            except OSError as error:
                issues.append(
                    f"{directory.relative_to(root).as_posix()}: "
                    f"could not be scanned: {error}"
                )
                continue
            child_directories: list[Path] = []
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(root)
                if entry.is_symlink():
                    issues.append(f"{relative.as_posix()}: symlink is not allowed")
                elif entry.is_file(follow_symlinks=False):
                    add_file(path, relative)
                elif entry.is_dir(follow_symlinks=False):
                    child_directories.append(path)
                else:
                    issues.append(f"{relative.as_posix()}: non-regular entry")
            stack.extend(reversed(child_directories))
    return dict(sorted(digests.items())), issues


def package_file_digests(root: Path) -> dict[str, str]:
    """Return the deterministic package-content digest inventory."""
    digests, issues = _package_file_inventory(Path(root))
    if issues:
        raise ValueError("; ".join(sorted(issues)))
    return digests


def validate_installed_copy(source_root: Path, installed_root: Path) -> list[str]:
    """Compare only an explicitly supplied installed package path, read-only."""
    source, source_issues = _package_file_inventory(Path(source_root))
    installed, installed_issues = _package_file_inventory(Path(installed_root))
    issues = [f"source {issue}" for issue in source_issues]
    issues.extend(f"installed {issue}" for issue in installed_issues)
    source_paths = set(source)
    installed_paths = set(installed)
    issues.extend(
        f"installed package missing {path}"
        for path in sorted(source_paths.difference(installed_paths))
    )
    issues.extend(
        f"installed package has unexpected {path}"
        for path in sorted(installed_paths.difference(source_paths))
    )
    issues.extend(
        f"installed package changed {path}"
        for path in sorted(source_paths.intersection(installed_paths))
        if source[path] != installed[path]
    )
    return sorted(set(issues))


def parse_skill_frontmatter(
    skill_markdown: str,
) -> tuple[dict[str, str] | None, list[str]]:
    """Parse the deliberately small YAML subset used by skill frontmatter."""
    normalized = skill_markdown.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return None, ["SKILL.md frontmatter must start with ---"]

    closing_index = normalized.find("\n---\n", 4)
    if closing_index == -1:
        return None, ["SKILL.md frontmatter must end with ---"]

    frontmatter: dict[str, str] = {}
    issues: list[str] = []
    for line_number, line in enumerate(
        normalized[4:closing_index].splitlines(), start=2
    ):
        if not line.strip():
            continue
        match = re.fullmatch(r"([A-Za-z0-9_-]+):\s*(.+)", line)
        if match is None:
            issues.append(f"SKILL.md frontmatter line {line_number} is invalid")
            continue
        key, value = match.groups()
        if key in frontmatter:
            issues.append(f"SKILL.md frontmatter field {key} is duplicated")
            continue
        frontmatter[key] = value.strip().strip('"\'')

    if issues:
        return None, issues
    return frontmatter, []


def _parse_openai_fields(openai_yaml: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in re.finditer(
        r"^\s{2}(display_name|short_description|default_prompt):\s*(.+?)\s*$",
        openai_yaml,
        flags=re.MULTILINE,
    ):
        fields[match.group(1)] = match.group(2).strip().strip('"\'')
    return fields


def _parse_implicit_invocation_policy(openai_yaml: str) -> list[str]:
    values: list[str] = []
    in_policy = False
    for line in openai_yaml.splitlines():
        if line and not line[0].isspace():
            in_policy = line.strip() == "policy:"
            continue
        if not in_policy:
            continue
        match = re.fullmatch(r"\s{2}allow_implicit_invocation:\s*(\S+)\s*", line)
        if match is not None:
            values.append(match.group(1))
    return values


def validate_skill_contract(repository_root: Path) -> list[str]:
    """Validate skill metadata, trigger description, and UI metadata."""
    skill_path = repository_root / SKILL_MARKDOWN
    if not skill_path.is_file():
        return [f"{SKILL_MARKDOWN.as_posix()} is missing"]

    try:
        skill_markdown = skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [f"{SKILL_MARKDOWN.as_posix()} could not be read: {error}"]

    frontmatter, issues = parse_skill_frontmatter(skill_markdown)
    if frontmatter is not None:
        if set(frontmatter) != {"name", "description"}:
            issues.append("SKILL.md frontmatter must contain exactly name and description")
        if frontmatter.get("name") != "implementing-staged-plans":
            issues.append("SKILL.md skill name must equal implementing-staged-plans")

        description = frontmatter.get("description", "")
        description_requirements = (
            "approved implementation program" in description.lower(),
            "reviewable increment" in description.lower(),
            re.search(r"\buse when\b", description, re.IGNORECASE) is not None,
        )
        if not all(description_requirements):
            issues.append(
                "SKILL.md description must state the workflow goal and triggering contexts"
            )

    marker = TEMPLATE_MARKER_PATTERN.search(skill_markdown)
    if marker is not None:
        issues.append(f"SKILL.md contains unresolved template marker {marker.group(0)!r}")

    metadata_path = repository_root / OPENAI_METADATA
    if not metadata_path.is_file():
        issues.append(f"{OPENAI_METADATA.as_posix()} is missing")
        return issues

    try:
        openai_yaml = metadata_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        issues.append(f"{OPENAI_METADATA.as_posix()} could not be read: {error}")
        return issues

    fields = _parse_openai_fields(openai_yaml)
    for required_field in ("display_name", "short_description", "default_prompt"):
        if not fields.get(required_field):
            issues.append(f"agents/openai.yaml is missing {required_field}")

    default_prompt = fields.get("default_prompt", "")
    if default_prompt and "$implementing-staged-plans" not in default_prompt:
        issues.append(
            "agents/openai.yaml default_prompt must explicitly name "
            "$implementing-staged-plans"
        )

    if _parse_implicit_invocation_policy(openai_yaml) != ["false"]:
        issues.append(
            "agents/openai.yaml policy allow_implicit_invocation must be false"
        )

    metadata_marker = TEMPLATE_MARKER_PATTERN.search(openai_yaml)
    if metadata_marker is not None:
        issues.append(
            "agents/openai.yaml contains unresolved template marker "
            f"{metadata_marker.group(0)!r}"
        )
    return issues


def _relative_markdown_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    else:
        target = target.split(maxsplit=1)[0]
    target = target.split("#", maxsplit=1)[0]
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        return None
    return target


def validate_markdown_links(repository_root: Path) -> list[str]:
    """Reject broken or repository-escaping relative links in package Markdown."""
    issues: list[str] = []
    resolved_root = repository_root.resolve()
    skill_root = repository_root / "skills" / "implementing-staged-plans"
    if not skill_root.is_dir():
        return issues

    for markdown_path in sorted(skill_root.rglob("*.md")):
        try:
            markdown = markdown_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            issues.append(f"{markdown_path}: could not be read: {error}")
            continue
        for match in MARKDOWN_LINK_PATTERN.finditer(markdown):
            target = _relative_markdown_target(match.group(1))
            if target is None:
                continue
            resolved_target = (markdown_path.parent / target).resolve()
            relative_markdown_path = markdown_path.relative_to(repository_root)
            if not resolved_target.is_relative_to(resolved_root):
                issues.append(
                    f"{relative_markdown_path.as_posix()}: relative link {target!r} "
                    "escapes repository"
                )
            elif not resolved_target.exists():
                issues.append(
                    f"{relative_markdown_path.as_posix()}: relative link {target!r} "
                    "does not resolve"
                )
    return issues


def _package_facing_paths(repository_root: Path) -> list[Path]:
    paths = [repository_root / PLUGIN_MANIFEST, repository_root / SKILL_MARKDOWN]
    metadata_path = repository_root / OPENAI_METADATA
    paths.append(metadata_path)
    reference_root = (
        repository_root / "skills" / "implementing-staged-plans" / "references"
    )
    if reference_root.is_dir():
        paths.extend(sorted(reference_root.rglob("*.md")))
    return paths


def validate_forbidden_components(repository_root: Path) -> list[str]:
    """Reject unapproved component, identity, publication, and naming surfaces."""
    issues: list[str] = []
    for forbidden_name in sorted(FORBIDDEN_FILENAMES):
        for path in sorted(repository_root.rglob(forbidden_name)):
            relative = path.relative_to(repository_root)
            if relative in ALLOWED_MARKETPLACE_PATHS:
                continue
            relative_path = relative.as_posix()
            issues.append(f"forbidden component or identity surface: {relative_path}")

    for path in _package_facing_paths(repository_root):
        if not path.is_file():
            continue
        try:
            package_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            issues.append(f"{path}: could not be read: {error}")
            continue
        identifiers = sorted(set(ROADMAP_IDENTIFIER_PATTERN.findall(package_text)))
        for identifier in identifiers:
            relative_path = path.relative_to(repository_root).as_posix()
            issues.append(
                f"{relative_path}: roadmap-specific identifier {identifier} "
                "must not leak into package-facing names"
            )
    return issues


def validate_authority_assets(repository_root: Path) -> list[str]:
    """Require the accepted focused procedure and mechanical authority boundary."""
    issues: list[str] = []
    for relative_path in (
        PROGRAM_AUTHORITY_REFERENCE,
        PROGRAM_AUTHORITY_SCRIPT,
        STATE_AUTHORITY_REFERENCE,
        STATE_AUTHORITY_SCRIPT,
        REPOSITORY_PREPARATION_REFERENCE,
        REPOSITORY_PREPARATION_SCRIPT,
        EXECUTION_DISCIPLINE_REFERENCE,
        EXECUTION_DISCIPLINE_SCRIPT,
        REVIEW_COORDINATION_REFERENCE,
        REVIEW_COORDINATION_SCRIPT,
        CONTINUITY_CLOSURE_REFERENCE,
        CONTINUITY_CLOSURE_SCRIPT,
        APPROVAL_CHECKPOINT_REFERENCE,
        APPROVAL_CHECKPOINT_SCRIPT,
        PROGRAM_DISCOVERY_REFERENCE,
        PROGRAM_DISCOVERY_SCRIPT,
        *PLAN_A_PRODUCTION_SCRIPTS,
    ):
        path = repository_root / relative_path
        if not path.is_file() or path.is_symlink():
            issues.append(
                f"{relative_path.as_posix()} must be a regular non-symlink file"
            )
    return issues


def validate_package(repository_root: Path) -> list[str]:
    """Return all deterministic package validation issues."""
    issues = [
        *validate_plugin_manifest(repository_root),
        *validate_distribution_identity(repository_root),
        *validate_skill_contract(repository_root),
        *validate_authority_assets(repository_root),
        *validate_markdown_links(repository_root),
        *validate_forbidden_components(repository_root),
    ]
    return sorted(set(issues))


def main(argv: Sequence[str] | None = None) -> int:
    """Run package validation and return the documented CLI status."""
    parser = argparse.ArgumentParser(prog="validate_package.py")
    parser.add_argument("repository_root", nargs="?", default=".")
    parser.add_argument("--compare-installed")
    try:
        arguments = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except SystemExit as error:
        return 0 if error.code == 0 else 1
    repository_root = Path(arguments.repository_root).resolve()
    issues = validate_package(repository_root)
    if arguments.compare_installed is not None:
        issues.extend(
            validate_installed_copy(
                repository_root, Path(arguments.compare_installed).resolve()
            )
        )
        issues = sorted(set(issues))
    if issues:
        for issue in issues:
            print(issue)
        return 1

    print("Package validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
