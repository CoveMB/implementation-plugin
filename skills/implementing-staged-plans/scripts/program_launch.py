#!/usr/bin/env python3
"""Render and validate the exact new-program launch prompt."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from program_authority import (
    APPROVED_VALIDATION_MODE,
    PROPOSAL_VALIDATION_MODE,
    SUPPORTED_NEW_PROGRAM_APPROVAL_MODES,
    SETUP_PROGRAM_MANIFEST_SCHEMA,
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
    validate_program_authority,
)
from task_prompt import parse_exact_prompt, render_exact_prompt


LAUNCH_COMMAND_SCHEMA = "implementation-program-launch-command/v1"


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _derive_identifier(label: str, seed: Mapping[str, object]) -> str:
    digest = hashlib.sha256(
        _canonical_bytes({"identifier_domain": label, "seed": dict(seed)})
    ).hexdigest()
    return f"{label.upper()}-{digest[:24]}"


def _load_role(
    root: Path,
    manifest: dict[str, Any],
    role: str,
    *,
    json_lines: bool = False,
) -> tuple[Any, Path]:
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    path, path_issues = resolve_managed_path(
        root, logical_roles.get(role), role=f"logical role {role}"
    )
    if path is None:
        raise ValueError("; ".join(path_issues))
    value, issues = load_json_lines(path) if json_lines else load_json_object(path)
    if value is None:
        raise ValueError("; ".join(issues))
    return value, path


def _validate_launch_authority(root: Path, manifest: dict[str, Any]) -> None:
    approval_mode = manifest.get("approval_mode")
    if approval_mode not in SUPPORTED_NEW_PROGRAM_APPROVAL_MODES:
        raise ValueError("unsupported-new-program-approval-mode")
    approvals, _ = _load_role(root, manifest, "approvals", json_lines=True)
    validation_mode = (
        APPROVED_VALIDATION_MODE if approvals else PROPOSAL_VALIDATION_MODE
    )
    issues = validate_program_authority(root, validation_mode=validation_mode)
    if issues:
        raise ValueError("; ".join(issues))


def _launch_command(
    root: Path,
    *,
    proposal_status_sha256: str | None = None,
    proposal_status_sequence: int | None = None,
) -> dict[str, object]:
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    _validate_launch_authority(root, manifest)
    status, status_path = _load_role(root, manifest, "status")
    workspace, workspace_path = _load_role(root, manifest, "workspace")
    traceability, _ = _load_role(root, manifest, "traceability")
    approved_program_path, role_issues = resolve_managed_path(
        root,
        manifest.get("logical_roles", {}).get("approved_program"),
        role="logical role approved_program",
    )
    if approved_program_path is None:
        raise ValueError("; ".join(role_issues))
    coverage = traceability.get("coverage_assertion")
    if not isinstance(coverage, dict):
        raise ValueError("traceability coverage_assertion must be an object")

    proposal_controls = (
        status.get("program_state") == "awaiting-program-approval"
        and status.get("current_increment_state") == "not-started"
        and status.get("state_sequence") == 0
    )
    if proposal_controls:
        actual_status_sha256 = sha256_file(status_path)
        if (
            proposal_status_sha256 is not None
            and proposal_status_sha256 != actual_status_sha256
        ):
            raise ValueError("submitted launch prompt proposal status digest changed")
        proposal_status_sha256 = actual_status_sha256
        proposal_status_sequence = int(status["state_sequence"])
    elif proposal_status_sha256 is None:
        if not proposal_controls:
            activation = status.get("activation_binding")
            if not isinstance(activation, dict):
                raise ValueError("program status is not an activatable proposal")
            proposal_status_sha256 = activation.get("prior_status_sha256")
            proposal_status_sequence = activation.get("prior_status_sequence")
    if (
        not isinstance(proposal_status_sha256, str)
        or len(proposal_status_sha256) != 64
        or not isinstance(proposal_status_sequence, int)
        or isinstance(proposal_status_sequence, bool)
        or proposal_status_sequence != 0
    ):
        raise ValueError("proposal status binding is invalid")

    selected = workspace.get("implementation_workspace")
    pre_existing = workspace.get("pre_existing_work_at_selection")
    if not isinstance(selected, dict) or not isinstance(pre_existing, dict):
        raise ValueError("workspace proposal selection is incomplete")
    source_binding = manifest.get("source_binding")
    program_binding = manifest.get("program_binding")
    if not isinstance(source_binding, dict) or not isinstance(program_binding, dict):
        raise ValueError("manifest source and program bindings are required")
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        raise ValueError("manifest logical_roles must be an object")

    base_seed: dict[str, object] = {
        "schema_domain": LAUNCH_COMMAND_SCHEMA,
        "manifest_sha256": sha256_file(root / "manifest.json"),
        "proposal_status_sha256": proposal_status_sha256,
        "proposal_status_sequence": proposal_status_sequence,
        "workspace_proposal_sha256": sha256_file(workspace_path),
        "program_id": manifest.get("program_id"),
        "program_revision": manifest.get("program_revision"),
        "increment_id": status.get("current_increment_id"),
        "approval_mode": manifest.get("approval_mode"),
        "source_binding": source_binding,
        "program_sha256": program_binding.get("sha256"),
        "semantic_requirements_sha256": coverage.get(
            "semantic_requirements_sha256"
        ),
        "brief_binding": {
            "path": logical_roles.get("approved_program"),
            "sha256": sha256_file(approved_program_path),
        },
        "workspace": {
            "repository": workspace.get("repository"),
            "implementation_workspace": selected,
            "pre_existing_work_at_selection": pre_existing,
        },
        "allowed_conditional_actions": [],
    }
    launch_checkpoint_id = _derive_identifier("launch-checkpoint", base_seed)
    program_approval_event_id = _derive_identifier(
        "program-approval",
        {"base_seed": base_seed, "launch_checkpoint_id": launch_checkpoint_id},
    )
    workspace_approval_event_id = _derive_identifier(
        "workspace-approval",
        {
            "base_seed": base_seed,
            "launch_checkpoint_id": launch_checkpoint_id,
            "program_approval_event_id": program_approval_event_id,
        },
    )
    increment_grant_id = _derive_identifier(
        "increment-grant",
        {
            "base_seed": base_seed,
            "launch_checkpoint_id": launch_checkpoint_id,
            "program_approval_event_id": program_approval_event_id,
            "workspace_approval_event_id": workspace_approval_event_id,
        },
    )
    return {
        "schema_version": LAUNCH_COMMAND_SCHEMA,
        **base_seed,
        "launch_checkpoint_id": launch_checkpoint_id,
        "program_approval_event_id": program_approval_event_id,
        "workspace_approval_event_id": workspace_approval_event_id,
        "increment_grant_id": increment_grant_id,
    }


def render_program_launch_prompt(program_root: Path) -> str:
    """Render the legacy exact prompt or the v3 readable setup recap."""
    root = Path(program_root)
    manifest, issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(issues))
    if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA:
        status, _ = _load_role(root, manifest, "status")
        if status.get("schema_version") != "implementation-program-status/v3":
            raise ValueError("manifest v3 requires status v3")
        from program_setup import render_setup_recap

        return render_setup_recap(root)
    return render_exact_prompt(_launch_command(root))


def validate_submitted_program_launch_prompt(
    program_root: Path, submitted_prompt: str
) -> dict[str, object]:
    """Validate direct prompt bytes against freshly loaded proposal authority."""
    root = Path(program_root)
    manifest, issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(issues))
    if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA:
        status, _ = _load_role(root, manifest, "status")
        if status.get("schema_version") != "implementation-program-status/v3":
            raise ValueError("manifest v3 requires status v3")
        raise ValueError("v3 activation requires a typed setup decision")
    command = parse_exact_prompt(submitted_prompt, LAUNCH_COMMAND_SCHEMA)
    expected = _launch_command(
        root,
        proposal_status_sha256=command.get("proposal_status_sha256"),
        proposal_status_sequence=command.get("proposal_status_sequence"),
    )
    if command != expected or render_exact_prompt(expected) != submitted_prompt:
        raise ValueError("submitted launch prompt does not match current proposal bytes")
    return command


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="program_launch.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render = subparsers.add_parser("render")
    render.add_argument("program_root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(
        list(sys.argv[1:] if argv is None else argv)
    )
    try:
        prompt = render_program_launch_prompt(Path(arguments.program_root))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    sys.stdout.write(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
