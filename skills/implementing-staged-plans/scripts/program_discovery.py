#!/usr/bin/env python3
"""Discover repository-backed implementation programs without modifying them."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Callable

from program_authority import (
    load_json_object,
    resolve_managed_path,
    sha256_file,
    validate_program_authority,
)
from repository_preparation import inspect_repository
from state_authority import (
    INCREMENT_TRANSITIONS,
    STATUS_SCHEMA,
    WORKSPACE_SCHEMA,
    RepositoryObservation,
    validate_state_authority,
)


RESUMABLE_PROGRAM_STATES = frozenset({"active", "blocked"})
SUPPORTED_PROGRAM_STATES = frozenset({*RESUMABLE_PROGRAM_STATES, "closed"})


@dataclass(frozen=True)
class ProgramCandidate:
    manifest_path: str
    program_root: str
    program_id: str
    program_revision: int
    program_state: str
    status_path: str
    status_sha256: str
    status_sequence: int


@dataclass(frozen=True)
class ResumeExpectations:
    manifest_path: str
    manifest_sha256: str
    status_path: str
    status_sha256: str
    status_sequence: int
    program_id: str
    program_revision: int
    program_state: str
    source_id: str
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    approval_mode: str
    workspace_path: str
    workspace_branch: str
    workspace_base_commit: str
    workspace_head_commit: str
    staged_paths: tuple[str, ...]
    modified_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]
    conflicted_paths: tuple[str, ...]
    active_git_operation: str | None
    current_increment_id: str
    current_increment_state: str
    brief_path: str
    brief_sha256: str
    exact_file_plan_sha256: str


@dataclass(frozen=True)
class ProgramDiscoveryResult:
    disposition: str
    required_input: str | None
    source_plan_path: str | None
    candidates: tuple[ProgramCandidate, ...]
    closed_programs: tuple[ProgramCandidate, ...]
    resume_expectations: ResumeExpectations | None
    issues: tuple[str, ...]
    next_action: str
    stop_required: bool


ObservationProvider = Callable[[Path, str], RepositoryObservation]


def validate_resume_evidence(
    observed: ResumeExpectations,
    expected: ResumeExpectations,
) -> list[str]:
    """Compare submitted resume evidence with independently discovered expectations."""
    if not isinstance(observed, ResumeExpectations) or not isinstance(
        expected, ResumeExpectations
    ):
        return ["resume evidence and expectations must use ResumeExpectations"]
    return [
        f"resume {field.name} mismatch"
        for field in fields(ResumeExpectations)
        if getattr(observed, field.name) != getattr(expected, field.name)
    ]


def _default_observation_provider(
    workspace_path: Path, base_commit: str
) -> RepositoryObservation:
    return inspect_repository(workspace_path, base_commit).observation


def _relative_path(repository: Path, path: Path) -> str:
    return path.relative_to(repository).as_posix()


def _display_path(repository: Path, path: Path) -> str:
    try:
        return _relative_path(repository, path)
    except ValueError:
        return path.as_posix()


def _absolute_input_path(repository: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = repository / path
    return Path(os.path.abspath(path))


def _path_issues(repository: Path, path: Path, label: str) -> list[str]:
    issues: list[str] = []
    try:
        relative = _absolute_input_path(repository, path).relative_to(repository)
    except ValueError:
        return [f"{label} escapes the repository"]
    current = repository
    if repository.is_symlink() or not repository.is_dir():
        return ["repository root must be a regular non-symlink directory"]
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            issues.append(f"{label} traverses a symlink: {_relative_path(repository, current)}")
            break
    if not path.is_file():
        issues.append(f"{label} must be a regular file")
    return issues


def _validate_persisted_bindings(
    program_root: Path,
    manifest: dict[str, object],
    status: dict[str, object],
) -> list[str]:
    issues: list[str] = []
    if status.get("schema_version") != STATUS_SCHEMA:
        issues.append("unsupported status schema")
    if status.get("current_increment_state") not in INCREMENT_TRANSITIONS:
        issues.append("unknown increment state")
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return ["manifest logical_roles must be an object"]
    resolved_roles: dict[str, Path] = {}
    for role, raw_path in sorted(logical_roles.items()):
        path, path_issues = resolve_managed_path(
            program_root,
            raw_path,
            role=f"logical role {role}",
        )
        issues.extend(path_issues)
        if path is not None:
            resolved_roles[str(role)] = path

    source_binding = manifest.get("source_binding")
    status_source = status.get("source_binding")
    if not isinstance(source_binding, dict) or not isinstance(status_source, dict):
        issues.append("source binding must be an object")
    else:
        for field in ("source_id", "sha256"):
            if status_source.get(field) != source_binding.get(field):
                issues.append(f"status source {field} mismatch")

    program_binding = manifest.get("program_binding")
    status_program = status.get("program_binding")
    if not isinstance(program_binding, dict) or not isinstance(status_program, dict):
        issues.append("program binding must be an object")
    else:
        if status_program.get("sha256") != program_binding.get("sha256"):
            issues.append("status program digest mismatch")
        traceability_path = resolved_roles.get("traceability")
        if traceability_path is not None:
            traceability, traceability_issues = load_json_object(traceability_path)
            issues.extend(traceability_issues)
            if traceability is not None:
                coverage = traceability.get("coverage_assertion")
                semantic_sha256 = (
                    coverage.get("semantic_requirements_sha256")
                    if isinstance(coverage, dict)
                    else None
                )
                if (
                    status_program.get("semantic_requirements_sha256")
                    != semantic_sha256
                ):
                    issues.append("status semantic requirements digest mismatch")

    if status.get("approval_mode") != manifest.get("approval_mode"):
        issues.append("status approval mode mismatch")
    current_increment = manifest.get("current_increment")
    if not isinstance(current_increment, dict):
        issues.append("manifest current_increment must be an object")
    else:
        if current_increment.get("increment_id") != status.get("current_increment_id"):
            issues.append("manifest current increment mismatch")
        if current_increment.get("state") != status.get("current_increment_state"):
            issues.append("manifest current increment state mismatch")

    brief_binding = status.get("brief_binding")
    brief_path = resolved_roles.get("current_increment_brief")
    if not isinstance(brief_binding, dict):
        issues.append("status brief_binding must be an object")
    elif brief_path is not None:
        if brief_binding.get("path") != logical_roles.get("current_increment_brief"):
            issues.append("brief path mismatch")
        if brief_binding.get("sha256") != sha256_file(brief_path):
            issues.append("brief digest mismatch")

    plan_path = resolved_roles.get("current_exact_file_plan")
    if plan_path is not None:
        plan_sha256 = sha256_file(plan_path)
        if plan_sha256 not in {
            status.get("pending_exact_file_plan_sha256"),
            status.get("approved_exact_file_plan_sha256"),
        }:
            issues.append("plan digest mismatch")
        if (
            isinstance(current_increment, dict)
            and current_increment.get("exact_file_plan_sha256") != plan_sha256
        ):
            issues.append("manifest plan digest mismatch")

    workspace_path = resolved_roles.get("workspace")
    if workspace_path is not None:
        workspace, workspace_issues = load_json_object(workspace_path)
        issues.extend(workspace_issues)
        if workspace is not None:
            if workspace.get("schema_version") != WORKSPACE_SCHEMA:
                issues.append("unsupported workspace schema")
            for field in ("program_id", "program_revision"):
                if workspace.get(field) != manifest.get(field):
                    issues.append(f"workspace {field} mismatch")
            selected = workspace.get("implementation_workspace")
            workspace_binding = manifest.get("workspace_binding")
            if not isinstance(selected, dict) or not isinstance(
                workspace_binding, dict
            ):
                issues.append("workspace selection and manifest binding are required")
            else:
                persisted_pairs = (
                    ("path", selected.get("path"), workspace_binding.get("path")),
                    ("branch", selected.get("branch"), workspace_binding.get("branch")),
                    (
                        "base commit",
                        selected.get("base_commit"),
                        workspace_binding.get("base_commit"),
                    ),
                )
                for label, persisted, manifest_value in persisted_pairs:
                    if persisted != manifest_value:
                        issues.append(f"workspace {label} binding mismatch")
                selected_head = selected.get(
                    "head_commit_at_selection",
                    selected.get("head_commit_at_revision_activation"),
                )
                if not isinstance(selected_head, str) or not selected_head:
                    issues.append("workspace selected head is required")
            if (
                isinstance(brief_binding, dict)
                and brief_binding.get("workspace_sha256")
                != sha256_file(workspace_path)
            ):
                issues.append("brief workspace digest mismatch")
    return sorted(set(issues))


def _load_candidate(
    repository: Path,
    manifest_path: Path,
    observation_provider: ObservationProvider,
) -> tuple[ProgramCandidate | None, ResumeExpectations | None, tuple[str, ...]]:
    display_path = _display_path(repository, manifest_path)
    issues = _path_issues(repository, manifest_path, f"manifest {display_path}")
    if issues:
        return None, None, tuple(sorted(set(issues)))
    program_root = manifest_path.parent
    authority_issues = validate_program_authority(program_root)
    if authority_issues:
        return None, None, tuple(
            f"{display_path}: {issue}" for issue in authority_issues
        )
    manifest, manifest_issues = load_json_object(manifest_path)
    if manifest is None:
        return None, None, tuple(f"{display_path}: {issue}" for issue in manifest_issues)
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return None, None, (f"{display_path}: manifest logical_roles must be an object",)
    status_path, status_path_issues = resolve_managed_path(
        program_root,
        logical_roles.get("status"),
        role="logical role status",
    )
    if status_path is None:
        return None, None, tuple(f"{display_path}: {issue}" for issue in status_path_issues)
    status, status_issues = load_json_object(status_path)
    if status is None:
        return None, None, tuple(f"{display_path}: {issue}" for issue in status_issues)

    program_state = status.get("program_state")
    issues.extend(_validate_persisted_bindings(program_root, manifest, status))
    for label, actual, expected in (
        ("program_id", status.get("program_id"), manifest.get("program_id")),
        ("program_revision", status.get("program_revision"), manifest.get("program_revision")),
        ("program_state", program_state, manifest.get("program_status")),
    ):
        if actual != expected:
            issues.append(f"{display_path}: status {label} does not match manifest")
    if program_state not in SUPPORTED_PROGRAM_STATES:
        issues.append(f"{display_path}: unsupported controlling program state {program_state!r}")
    sequence = status.get("state_sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        issues.append(f"{display_path}: status state_sequence is invalid")
    if issues:
        return None, None, tuple(sorted(set(issues)))

    candidate = ProgramCandidate(
        manifest_path=display_path,
        program_root=_relative_path(repository, program_root),
        program_id=str(manifest["program_id"]),
        program_revision=int(manifest["program_revision"]),
        program_state=str(program_state),
        status_path=_relative_path(repository, status_path),
        status_sha256=sha256_file(status_path),
        status_sequence=sequence,
    )
    if program_state == "closed":
        return candidate, None, ()

    workspace_binding = manifest.get("workspace_binding")
    if not isinstance(workspace_binding, dict):
        return None, None, (f"{display_path}: manifest workspace_binding must be an object",)
    workspace_path = workspace_binding.get("path")
    base_commit = workspace_binding.get("base_commit")
    if not isinstance(workspace_path, str) or not workspace_path:
        issues.append(f"{display_path}: manifest workspace path is required")
    if not isinstance(base_commit, str) or not base_commit:
        issues.append(f"{display_path}: manifest workspace base commit is required")
    if issues:
        return None, None, tuple(sorted(set(issues)))
    try:
        observation = observation_provider(Path(workspace_path), base_commit)
    except (OSError, TypeError, ValueError) as error:
        return None, None, (f"{display_path}: repository observation failed: {error}",)
    state_issues = validate_state_authority(program_root, observation)
    if state_issues:
        return None, None, tuple(f"{display_path}: {issue}" for issue in state_issues)

    source_binding = manifest["source_binding"]
    program_binding = status["program_binding"]
    brief_binding = status["brief_binding"]
    exact_file_plan_sha256 = status.get("approved_exact_file_plan_sha256")
    if not isinstance(exact_file_plan_sha256, str):
        exact_file_plan_sha256 = status.get("pending_exact_file_plan_sha256")
    expectations = ResumeExpectations(
        manifest_path=display_path,
        manifest_sha256=sha256_file(manifest_path),
        status_path=candidate.status_path,
        status_sha256=candidate.status_sha256,
        status_sequence=candidate.status_sequence,
        program_id=candidate.program_id,
        program_revision=candidate.program_revision,
        program_state=candidate.program_state,
        source_id=str(source_binding["source_id"]),
        source_sha256=str(source_binding["sha256"]),
        program_sha256=str(program_binding["sha256"]),
        semantic_requirements_sha256=str(
            program_binding["semantic_requirements_sha256"]
        ),
        approval_mode=str(status["approval_mode"]),
        workspace_path=observation.path,
        workspace_branch=observation.branch,
        workspace_base_commit=observation.base_commit,
        workspace_head_commit=observation.head_commit,
        staged_paths=observation.staged_paths,
        modified_paths=observation.modified_paths,
        untracked_paths=observation.untracked_paths,
        conflicted_paths=observation.conflicted_paths,
        active_git_operation=observation.active_git_operation,
        current_increment_id=str(status["current_increment_id"]),
        current_increment_state=str(status["current_increment_state"]),
        brief_path=str(brief_binding["path"]),
        brief_sha256=str(brief_binding["sha256"]),
        exact_file_plan_sha256=str(exact_file_plan_sha256),
    )
    return candidate, expectations, ()


def discover_programs(
    repository_root: Path,
    *,
    explicit_manifest_path: str | Path | None = None,
    instruction_manifest_paths: Sequence[str | Path] = (),
    authoritative_source_plan_path: str | Path | None = None,
    observation_provider: ObservationProvider = _default_observation_provider,
) -> ProgramDiscoveryResult:
    """Discover convention-owned manifests and return one deterministic route."""
    repository = Path(repository_root).absolute()
    if repository.is_symlink() or not repository.is_dir():
        return ProgramDiscoveryResult(
            disposition="invalid",
            required_input=None,
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=("repository root must be a regular non-symlink directory",),
            next_action="Use the exact regular repository path and rerun discovery.",
            stop_required=True,
        )
    conventional_root = repository / "implementation-programs"
    if explicit_manifest_path is not None:
        manifests = (
            _absolute_input_path(repository, explicit_manifest_path),
        )
    elif conventional_root.is_symlink():
        return ProgramDiscoveryResult(
            disposition="invalid",
            required_input=None,
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=("implementation-programs root must not be a symlink",),
            next_action="Replace the controlling symlink with an instruction-declared regular path.",
            stop_required=True,
        )
    else:
        declared = tuple(
            _absolute_input_path(repository, path)
            for path in instruction_manifest_paths
        )
        conventional = (
            tuple(conventional_root.glob("*/manifest.json"))
            if conventional_root.is_dir()
            else ()
        )
        manifests = tuple(
            sorted(
                {*declared, *conventional},
                key=lambda path: path.as_posix(),
            )
        )
    if manifests:
        candidates: list[ProgramCandidate] = []
        closed: list[ProgramCandidate] = []
        expectations: list[ResumeExpectations] = []
        issues: list[str] = []
        for manifest_path in manifests:
            candidate, resume, candidate_issues = _load_candidate(
                repository, manifest_path, observation_provider
            )
            issues.extend(candidate_issues)
            if candidate is None:
                continue
            if candidate.program_state == "closed":
                closed.append(candidate)
            else:
                candidates.append(candidate)
                if resume is not None:
                    expectations.append(resume)
        if issues:
            return ProgramDiscoveryResult(
                disposition="invalid",
                required_input=None,
                source_plan_path=None,
                candidates=tuple(candidates),
                closed_programs=tuple(closed),
                resume_expectations=None,
                issues=tuple(sorted(set(issues))),
                next_action="Correct the invalid controlling path or binding and rerun discovery.",
                stop_required=True,
            )
        if len(candidates) == 1:
            return ProgramDiscoveryResult(
                disposition="resume",
                required_input=None,
                source_plan_path=None,
                candidates=tuple(candidates),
                closed_programs=tuple(closed),
                resume_expectations=expectations[0],
                issues=(),
                next_action="Resume from the selected manifest and persisted state.",
                stop_required=False,
            )
        if len(candidates) > 1:
            return ProgramDiscoveryResult(
                disposition="selection-required",
                required_input="program-manifest-selection",
                source_plan_path=None,
                candidates=tuple(candidates),
                closed_programs=tuple(closed),
                resume_expectations=None,
                issues=(),
                next_action="Select exactly one candidate manifest and rerun discovery explicitly.",
                stop_required=True,
            )
        return ProgramDiscoveryResult(
            disposition="closed-programs",
            required_input="new-program-or-closed-program-inspection-intent",
            source_plan_path=None,
            candidates=(),
            closed_programs=tuple(closed),
            resume_expectations=None,
            issues=(),
            next_action=(
                "State explicit new-program intent or name a closed manifest for inspection."
            ),
            stop_required=True,
        )
    if authoritative_source_plan_path is None:
        return ProgramDiscoveryResult(
            disposition="new-program-bootstrap-possible",
            required_input="authoritative-source-plan-path",
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=(),
            next_action="Supply the authoritative source-plan path before any program write.",
            stop_required=True,
        )
    source_plan = Path(os.path.abspath(Path(authoritative_source_plan_path)))
    if source_plan.is_symlink() or not source_plan.is_file():
        source_issue = (
            "authoritative source-plan path must be a regular non-symlink file"
        )
        return ProgramDiscoveryResult(
            disposition="invalid",
            required_input=None,
            source_plan_path=None,
            candidates=(),
            closed_programs=(),
            resume_expectations=None,
            issues=(source_issue,),
            next_action="Supply the exact regular authoritative source-plan path.",
            stop_required=True,
        )
    return ProgramDiscoveryResult(
        disposition="new-program-bootstrap-ready",
        required_input=None,
        source_plan_path=str(source_plan),
        candidates=(),
        closed_programs=(),
        resume_expectations=None,
        issues=(),
        next_action="Route the validated source plan to the program-authority bootstrap gate.",
        stop_required=False,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="program_discovery.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    discover = subparsers.add_parser("discover")
    discover.add_argument("repository_root")
    discover.add_argument("--manifest")
    discover.add_argument("--instruction-manifest", action="append", default=[])
    discover.add_argument("--source-plan")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(
        list(sys.argv[1:] if argv is None else argv)
    )
    result = discover_programs(
        Path(arguments.repository_root),
        explicit_manifest_path=arguments.manifest,
        instruction_manifest_paths=arguments.instruction_manifest,
        authoritative_source_plan_path=arguments.source_plan,
    )
    print(json.dumps(asdict(result), sort_keys=True))
    return 1 if result.stop_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
