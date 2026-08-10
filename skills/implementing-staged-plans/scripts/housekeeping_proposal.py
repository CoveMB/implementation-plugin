#!/usr/bin/env python3
"""Build and validate dry-run post-closure housekeeping proposals."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from continuity_closure import decide_later_action
from program_authority import (
    load_json_object,
    load_json_lines,
    resolve_managed_path,
    sha256_file,
    validate_program_authority,
)


PROPOSAL_SCHEMA = "implementation-housekeeping-proposal/v1"
RESOURCE_INVENTORY_SCHEMA = "implementation-disposable-resource-inventory/v1"
STOP_ACTION = (
    "Stop. Review this dry-run proposal. Any cleanup requires a separate exact "
    "destructive-operation authorization and a separately authorized executor."
)
AUTHORIZATION_STOP_ACTION = (
    "Stop. Authorization verification does not execute cleanup. Any action must "
    "be performed by a separately authorized executor that revalidates this exact inventory."
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_RESOURCE_ID = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
_RESOURCE_KINDS = frozenset(
    {"temporary-directory", "linked-worktree", "ignored-cache"}
)


@dataclass(frozen=True)
class RepositoryIdentity:
    root: str
    branch: str
    head_commit: str
    git_directory: str
    git_common_directory: str


@dataclass(frozen=True)
class ClosedHousekeepingContext:
    program_root: str
    program_id: str
    program_revision: int
    source_id: str
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    reconciliation_sha256: str
    closure_packet_sha256: str
    repository: RepositoryIdentity
    manifest: dict[str, Any]
    status: dict[str, Any]


@dataclass(frozen=True)
class ProgramCreatedProvenance:
    creation_authorization_id: str
    creation_evidence_path: str
    creation_evidence_sha256: str
    resource_inventory_path: str
    resource_inventory_sha256: str


@dataclass(frozen=True)
class FilesystemIdentity:
    device_id: int
    inode: int
    owner_user_id: int
    owner_group_id: int
    mode: int
    change_time_ns: int


@dataclass(frozen=True)
class SymlinkAndContainmentResult:
    containment_root: str
    contained: bool
    candidate_is_symlink: bool
    ancestor_symlink: bool
    descendant_symlink: bool
    any_symlink: bool


@dataclass(frozen=True)
class WorktreeState:
    registered: bool
    is_current_worktree: bool
    branch: str
    head_commit: str
    staged_paths: tuple[str, ...]
    modified_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]
    conflicted_paths: tuple[str, ...]
    active_operation: str | None
    locked: bool
    unique_commits: bool
    dirty: bool


@dataclass(frozen=True)
class ProposedAction:
    kind: str
    target: str | None
    command: tuple[str, ...]
    force: bool
    receipt_required: bool


@dataclass(frozen=True)
class RecoveryPlan:
    deadline: str
    mechanism: str
    receipt_required: bool


@dataclass(frozen=True)
class HousekeepingCandidate:
    resource_id: str
    absolute_path: str
    resource_kind: str
    program_created_provenance: ProgramCreatedProvenance
    ownership_classification: str
    symlink_and_containment: SymlinkAndContainmentResult
    filesystem_identity: FilesystemIdentity
    fingerprint_sha256: str
    worktree_state: WorktreeState | None
    proposed_action: ProposedAction
    recovery: RecoveryPlan
    safe_removal_reason: str


@dataclass(frozen=True)
class BoundResourceInventory:
    path: str
    sha256: str
    resources: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class HousekeepingProposal:
    schema_version: str
    program_id: str
    program_revision: int
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    reconciliation_sha256: str
    closure_packet_sha256: str
    repository: RepositoryIdentity
    quarantine_root: str | None
    candidate_inventory_sha256: str
    candidates: tuple[HousekeepingCandidate, ...]
    mode: str
    execution_authorized: bool
    next_action: str


@dataclass(frozen=True)
class HousekeepingAuthorizationDecision:
    authorized: bool
    authorization_id: str | None
    candidate_inventory_sha256: str
    candidate_paths: tuple[str, ...]
    issues: tuple[str, ...]
    next_action: str


def _read_only_git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    return environment


def _run_git(repository_root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=repository_root,
            env=_read_only_git_environment(),
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(
            f"git {arguments[0]} could not complete: {error.__class__.__name__}"
        ) from error
    if result.returncode != 0:
        raise ValueError(
            f"git {arguments[0]} failed with exit status {result.returncode}"
        )
    return result.stdout.rstrip("\n")


def _resolve_git_path(repository_root: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = repository_root / candidate
    return candidate.resolve(strict=False)


def _repository_identity(repository_root: Path) -> RepositoryIdentity:
    root = Path(repository_root).absolute()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("repository root must be a regular non-symlink directory")
    resolved_root = root.resolve(strict=True)
    observed_root = Path(_run_git(root, "rev-parse", "--show-toplevel")).resolve(
        strict=True
    )
    if observed_root != resolved_root:
        raise ValueError("repository root does not match Git")
    branch = _run_git(root, "branch", "--show-current")
    if not branch:
        raise ValueError("repository must have a branch-bound HEAD")
    return RepositoryIdentity(
        root=str(resolved_root),
        branch=branch,
        head_commit=_run_git(root, "rev-parse", "HEAD"),
        git_directory=str(
            _resolve_git_path(root, _run_git(root, "rev-parse", "--git-dir"))
        ),
        git_common_directory=str(
            _resolve_git_path(
                root, _run_git(root, "rev-parse", "--git-common-dir")
            )
        ),
    )


def _required_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} is required")
    return value


def _required_sha256(value: object, label: str) -> str:
    digest = _required_string(value, label)
    if _SHA256.fullmatch(digest) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return digest


def _required_resource_id(value: object) -> str:
    resource_id = _required_string(value, "resource id")
    if _RESOURCE_ID.fullmatch(resource_id) is None:
        raise ValueError(
            "resource id must be a 1-128 character lowercase portable path component"
        )
    return resource_id


def _required_nonnegative_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _filesystem_identity_from_mapping(
    value: object,
    label: str,
) -> FilesystemIdentity:
    mapping = _required_mapping(value, label)
    fields = {
        "device_id",
        "inode",
        "owner_user_id",
        "owner_group_id",
        "mode",
        "change_time_ns",
    }
    if set(mapping) != fields:
        raise ValueError(f"{label} fields do not match the supported schema")
    return FilesystemIdentity(
        **{
            field: _required_nonnegative_integer(mapping.get(field), f"{label} {field}")
            for field in fields
        }
    )


def _filesystem_identity(path: Path) -> FilesystemIdentity:
    metadata = path.lstat()
    return FilesystemIdentity(
        device_id=metadata.st_dev,
        inode=metadata.st_ino,
        owner_user_id=metadata.st_uid,
        owner_group_id=metadata.st_gid,
        mode=stat.S_IMODE(metadata.st_mode),
        change_time_ns=metadata.st_ctime_ns,
    )


def _required_absolute_path(value: object, label: str) -> Path:
    raw = _required_string(value, label)
    path = Path(raw)
    if not path.is_absolute() or os.path.abspath(raw) != raw:
        raise ValueError(f"{label} must be an exact normalized absolute path")
    return path


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _paths_overlap(first: Path, second: Path) -> bool:
    return _is_within_or_equal(first, second) or _is_within_or_equal(second, first)


def _path_components_from(root: Path, path: Path) -> tuple[Path, ...]:
    relative = path.relative_to(root)
    current = root
    components = [root]
    for part in relative.parts:
        current = current / part
        components.append(current)
    return tuple(components)


def _contains_symlink(path: Path) -> bool:
    for current_root, directory_names, file_names in os.walk(
        path, topdown=True, followlinks=False
    ):
        root = Path(current_root)
        for name in (*directory_names, *file_names):
            if (root / name).is_symlink():
                return True
    return False


def _tree_fingerprint(path: Path) -> str:
    entries: list[dict[str, object]] = []
    candidates = [path, *sorted(path.rglob("*"), key=lambda item: item.as_posix())]
    for candidate in candidates:
        metadata = candidate.lstat()
        relative = "." if candidate == path else candidate.relative_to(path).as_posix()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"candidate contains a symlink: {candidate}")
        if stat.S_ISDIR(metadata.st_mode):
            kind = "directory"
            digest = None
        elif stat.S_ISREG(metadata.st_mode):
            kind = "file"
            digest = sha256_file(candidate)
        else:
            raise ValueError(f"candidate contains a special filesystem entry: {candidate}")
        entries.append({"path": relative, "kind": kind, "sha256": digest})
    return hashlib.sha256(_canonical_json_bytes(entries)).hexdigest()


def _parse_status_paths(status: str) -> tuple[tuple[str, ...], ...]:
    staged: set[str] = set()
    modified: set[str] = set()
    untracked: set[str] = set()
    conflicted: set[str] = set()
    skip_rename_source = False
    for record in status.split("\0"):
        if not record:
            continue
        if skip_rename_source:
            skip_rename_source = False
            continue
        if record.startswith("? "):
            untracked.add(record[2:])
            continue
        if record.startswith("u "):
            path = record.split(" ", 10)[-1]
            staged.add(path)
            modified.add(path)
            conflicted.add(path)
            continue
        if record.startswith(("1 ", "2 ")):
            fields = record.split(" ")
            change = fields[1]
            path_index = 8 if record.startswith("1 ") else 9
            path = " ".join(fields[path_index:])
            if change[0] != ".":
                staged.add(path)
            if change[1] != ".":
                modified.add(path)
            skip_rename_source = record.startswith("2 ")
            continue
        raise ValueError("unsupported Git status record in worktree")
    return tuple(sorted(staged)), tuple(sorted(modified)), tuple(sorted(untracked)), tuple(sorted(conflicted))


def _worktree_records(repository_root: Path) -> tuple[dict[str, object], ...]:
    output = _run_git(repository_root, "worktree", "list", "--porcelain", "-z")
    records: list[dict[str, object]] = []
    current: dict[str, object] = {}
    for token in output.split("\0"):
        if not token:
            if current:
                records.append(current)
                current = {}
            continue
        key, separator, value = token.partition(" ")
        if key == "worktree" and current:
            records.append(current)
            current = {}
        current[key] = value if separator else True
    if current:
        records.append(current)
    return tuple(records)


def _is_registered_worktree(
    repository: RepositoryIdentity,
    candidate_path: Path,
) -> bool:
    resolved_candidate = candidate_path.resolve(strict=True)
    return any(
        isinstance(record.get("worktree"), str)
        and Path(str(record["worktree"])).resolve(strict=False) == resolved_candidate
        for record in _worktree_records(Path(repository.root))
    )


def _active_git_operation(worktree: Path) -> str | None:
    markers = {
        "BISECT_LOG": "bisect",
        "CHERRY_PICK_HEAD": "cherry-pick",
        "MERGE_HEAD": "merge",
        "REVERT_HEAD": "revert",
        "rebase-apply": "rebase",
        "rebase-merge": "rebase",
        "sequencer": "sequencer",
    }
    operations: list[str] = []
    for marker, operation in markers.items():
        marker_path = _resolve_git_path(
            worktree, _run_git(worktree, "rev-parse", "--git-path", marker)
        )
        if marker_path.exists():
            operations.append(operation)
    return "+".join(sorted(operations)) or None


def _inspect_worktree(
    repository: RepositoryIdentity,
    candidate_path: Path,
) -> WorktreeState:
    resolved_candidate = candidate_path.resolve(strict=True)
    matching = [
        record
        for record in _worktree_records(Path(repository.root))
        if isinstance(record.get("worktree"), str)
        and Path(str(record["worktree"])).resolve(strict=False) == resolved_candidate
    ]
    if len(matching) != 1:
        raise ValueError("candidate is not exactly one registered Git worktree")
    record = matching[0]
    head = _run_git(candidate_path, "rev-parse", "HEAD")
    branch = _run_git(candidate_path, "branch", "--show-current")
    if not branch:
        raise ValueError("candidate worktree has a detached HEAD")
    staged, modified, untracked, conflicted = _parse_status_paths(
        _run_git(
            candidate_path,
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
        )
    )
    active_operation = _active_git_operation(candidate_path)
    containing_refs = set(
        filter(
            None,
            _run_git(
                Path(repository.root),
                "for-each-ref",
                "--format=%(refname)",
                f"--contains={head}",
            ).splitlines(),
        )
    )
    containing_refs.discard(f"refs/heads/{branch}")
    unique_commits = not containing_refs
    locked = "locked" in record
    is_current = resolved_candidate == Path(repository.root)
    dirty = bool(
        staged
        or modified
        or untracked
        or conflicted
        or active_operation
    )
    state = WorktreeState(
        registered=True,
        is_current_worktree=is_current,
        branch=branch,
        head_commit=head,
        staged_paths=staged,
        modified_paths=modified,
        untracked_paths=untracked,
        conflicted_paths=conflicted,
        active_operation=active_operation,
        locked=locked,
        unique_commits=unique_commits,
        dirty=dirty,
    )
    if state.is_current_worktree:
        raise ValueError("candidate is the current worktree")
    if state.locked:
        raise ValueError("candidate worktree is locked")
    if state.conflicted_paths or state.active_operation:
        raise ValueError("candidate worktree has a conflict or active operation")
    if state.dirty:
        raise ValueError("candidate worktree is dirty")
    if state.unique_commits:
        raise ValueError("candidate worktree has unique commits")
    return state


def load_closed_housekeeping_context(
    program_root: Path,
    repository_root: Path,
) -> ClosedHousekeepingContext:
    root = Path(program_root).absolute()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("program root must be a regular non-symlink directory")
    authority_issues = validate_program_authority(root)
    if authority_issues:
        raise ValueError("; ".join(authority_issues))
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    logical_roles = _required_mapping(
        manifest.get("logical_roles"), "manifest logical_roles"
    )
    status_path, status_path_issues = resolve_managed_path(
        root, logical_roles.get("status"), role="logical role status"
    )
    if status_path is None:
        raise ValueError("; ".join(status_path_issues))
    status, status_issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(status_issues))
    if status.get("program_state") != "closed":
        raise ValueError("program is not closed")
    closure = _required_mapping(status.get("closure_binding"), "closure binding")
    if closure.get("state") != "closed" or closure.get("readiness_validated") is not True:
        raise ValueError("closure binding is not validated and closed")

    resolved_closure: dict[str, tuple[Path, str]] = {}
    for role, path_field, digest_field in (
        ("closure_reconciliation", "reconciliation_path", "reconciliation_sha256"),
        ("closure_packet", "closure_packet_path", "closure_packet_sha256"),
    ):
        role_value = logical_roles.get(role)
        if closure.get(path_field) != role_value:
            raise ValueError(f"closure {path_field} mismatch")
        path, path_issues = resolve_managed_path(
            root, role_value, role=f"logical role {role}"
        )
        if path is None:
            raise ValueError("; ".join(path_issues))
        digest = _required_string(closure.get(digest_field), f"closure {digest_field}")
        if sha256_file(path) != digest:
            raise ValueError(f"closure {digest_field} mismatch")
        resolved_closure[role] = (path, digest)

    source_binding = _required_mapping(
        status.get("source_binding"), "status source binding"
    )
    program_binding = _required_mapping(
        status.get("program_binding"), "status program binding"
    )
    program_revision = status.get("program_revision")
    if not isinstance(program_revision, int) or isinstance(program_revision, bool):
        raise ValueError("program revision must be an integer")
    if status.get("program_id") != manifest.get("program_id"):
        raise ValueError("status program_id mismatch")
    if program_revision != manifest.get("program_revision"):
        raise ValueError("status program_revision mismatch")

    return ClosedHousekeepingContext(
        program_root=str(root.resolve(strict=True)),
        program_id=_required_string(status.get("program_id"), "program id"),
        program_revision=program_revision,
        source_id=_required_string(source_binding.get("source_id"), "source id"),
        source_sha256=_required_string(
            source_binding.get("sha256"), "source digest"
        ),
        program_sha256=_required_string(
            program_binding.get("sha256"), "program digest"
        ),
        semantic_requirements_sha256=_required_string(
            program_binding.get("semantic_requirements_sha256"),
            "semantic requirements digest",
        ),
        reconciliation_sha256=resolved_closure["closure_reconciliation"][1],
        closure_packet_sha256=resolved_closure["closure_packet"][1],
        repository=_repository_identity(Path(repository_root)),
        manifest=manifest,
        status=status,
    )


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _candidate_payload(proposal: HousekeepingProposal) -> dict[str, object]:
    return {
        "schema_version": PROPOSAL_SCHEMA,
        "program_id": proposal.program_id,
        "program_revision": proposal.program_revision,
        "source_sha256": proposal.source_sha256,
        "program_sha256": proposal.program_sha256,
        "semantic_requirements_sha256": proposal.semantic_requirements_sha256,
        "reconciliation_sha256": proposal.reconciliation_sha256,
        "closure_packet_sha256": proposal.closure_packet_sha256,
        "repository": asdict(proposal.repository),
        "quarantine_root": proposal.quarantine_root,
        "candidates": [
            asdict(candidate) if hasattr(candidate, "__dataclass_fields__") else candidate
            for candidate in proposal.candidates
        ],
    }


def candidate_inventory_sha256(proposal: HousekeepingProposal) -> str:
    return hashlib.sha256(_canonical_json_bytes(_candidate_payload(proposal))).hexdigest()


def _load_bound_disposable_resources(
    context: ClosedHousekeepingContext,
) -> BoundResourceInventory | None:
    logical_roles = _required_mapping(
        context.manifest.get("logical_roles"), "manifest logical_roles"
    )
    closure = _required_mapping(
        context.status.get("closure_binding"), "closure binding"
    )
    role_value = logical_roles.get("disposable_resource_inventory")
    bound_path = closure.get("disposable_resource_inventory_path")
    bound_digest = closure.get("disposable_resource_inventory_sha256")
    if role_value is None and bound_path is None and bound_digest is None:
        return None
    if role_value != bound_path:
        raise ValueError("disposable resource inventory path mismatch")
    inventory_path, path_issues = resolve_managed_path(
        Path(context.program_root),
        role_value,
        role="logical role disposable_resource_inventory",
    )
    if inventory_path is None:
        raise ValueError("; ".join(path_issues))
    if not isinstance(bound_digest, str) or sha256_file(inventory_path) != bound_digest:
        raise ValueError("disposable resource inventory digest mismatch")
    inventory, inventory_issues = load_json_object(inventory_path)
    if inventory is None:
        raise ValueError("; ".join(inventory_issues))
    if inventory.get("schema_version") != RESOURCE_INVENTORY_SCHEMA:
        raise ValueError("unsupported disposable resource inventory schema")
    expected_bindings = {
        "program_id": context.program_id,
        "program_revision": context.program_revision,
        "source_id": context.source_id,
        "source_sha256": context.source_sha256,
        "program_sha256": context.program_sha256,
        "semantic_requirements_sha256": context.semantic_requirements_sha256,
    }
    for field, expected in expected_bindings.items():
        if inventory.get(field) != expected:
            raise ValueError(f"disposable resource inventory {field} mismatch")
    resources = inventory.get("resources")
    if not isinstance(resources, list):
        raise ValueError("disposable resource inventory resources must be a list")
    if not all(isinstance(resource, dict) for resource in resources):
        raise ValueError("disposable resource records must be objects")
    return BoundResourceInventory(
        path=str(inventory_path),
        sha256=str(bound_digest),
        resources=tuple(resources),
    )


def _protected_paths(context: ClosedHousekeepingContext) -> tuple[Path, ...]:
    protected = {
        Path(context.program_root),
        Path(context.repository.git_directory),
        Path(context.repository.git_common_directory),
    }
    logical_roles = _required_mapping(
        context.manifest.get("logical_roles"), "manifest logical_roles"
    )
    for role, value in logical_roles.items():
        path, issues = resolve_managed_path(
            Path(context.program_root), value, role=f"logical role {role}"
        )
        if path is None:
            raise ValueError("; ".join(issues))
        protected.add(path)
    return tuple(sorted(protected, key=lambda path: str(path)))


def _validate_candidate_path_boundary(
    context: ClosedHousekeepingContext,
    candidate_path: Path,
    containment_root: Path,
) -> SymlinkAndContainmentResult:
    if not candidate_path.exists() and not candidate_path.is_symlink():
        raise ValueError("candidate path does not exist")
    if not containment_root.is_dir() or containment_root.is_symlink():
        raise ValueError("candidate containment root must be a non-symlink directory")
    resolved_containment = containment_root.resolve(strict=True)
    candidate_is_symlink = candidate_path.is_symlink()
    resolved_candidate = candidate_path.resolve(strict=True)
    if not _is_within_or_equal(resolved_candidate, resolved_containment) or resolved_candidate == resolved_containment:
        raise ValueError("candidate is not strictly contained by its declared root")
    repository_root = Path(context.repository.root)
    if resolved_candidate == repository_root or _is_within_or_equal(repository_root, resolved_candidate):
        raise ValueError("candidate overlaps the current worktree root")
    for protected in _protected_paths(context):
        if _paths_overlap(resolved_candidate, protected.resolve(strict=False)):
            raise ValueError("candidate overlaps protected program or closure evidence")
    components = _path_components_from(containment_root, candidate_path)
    ancestor_symlink = any(component.is_symlink() for component in components[:-1])
    descendant_symlink = (
        False if candidate_is_symlink or not candidate_path.is_dir() else _contains_symlink(candidate_path)
    )
    result = SymlinkAndContainmentResult(
        containment_root=str(resolved_containment),
        contained=True,
        candidate_is_symlink=candidate_is_symlink,
        ancestor_symlink=ancestor_symlink,
        descendant_symlink=descendant_symlink,
        any_symlink=candidate_is_symlink or ancestor_symlink or descendant_symlink,
    )
    if result.any_symlink:
        raise ValueError("candidate or its containment chain contains a symlink")
    if not candidate_path.is_dir():
        raise ValueError("disposable resource candidate must be a directory")
    return result


def _verify_ignored_cache(repository: RepositoryIdentity, candidate_path: Path) -> None:
    repository_root = Path(repository.root)
    resolved_candidate = candidate_path.resolve(strict=True)
    if not _is_within_or_equal(resolved_candidate, repository_root):
        raise ValueError("ignored cache must be inside the current repository")
    relative = resolved_candidate.relative_to(repository_root).as_posix()
    ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", relative],
        cwd=repository_root,
        env=_read_only_git_environment(),
        shell=False,
        check=False,
        capture_output=True,
        timeout=10,
    )
    if ignored.returncode != 0:
        raise ValueError("ignored cache is not currently ignored by Git")
    tracked = _run_git(repository_root, "ls-files", "--", relative)
    if tracked:
        raise ValueError("ignored cache contains a tracked path")


def _validated_quarantine_root(
    context: ClosedHousekeepingContext,
    quarantine_root: Path,
) -> Path:
    root = Path(quarantine_root)
    if not root.is_absolute() or os.path.abspath(str(root)) != str(root):
        raise ValueError("quarantine root must be an exact normalized absolute path")
    if not root.is_dir() or root.is_symlink():
        raise ValueError("quarantine root must be an existing non-symlink directory")
    resolved_root = root.resolve(strict=True)
    protected_paths = (*_protected_paths(context), Path(context.repository.root))
    if any(
        _paths_overlap(resolved_root, protected.resolve(strict=False))
        for protected in protected_paths
    ):
        raise ValueError("quarantine root overlaps protected program, Git, or worktree evidence")
    return resolved_root


def _quarantine_action(
    resource_id: str,
    candidate_path: Path,
    quarantine_root: Path | None,
    containment: SymlinkAndContainmentResult,
) -> tuple[ProposedAction, str]:
    if quarantine_root is None:
        raise ValueError("quarantine root is required for non-worktree candidates")
    resolved_root = quarantine_root
    if _paths_overlap(resolved_root, Path(containment.containment_root)):
        raise ValueError("quarantine root must not overlap the candidate containment root")
    target = (resolved_root / resource_id).resolve(strict=False)
    if target.parent != resolved_root or not _is_within_or_equal(target, resolved_root):
        raise ValueError("quarantine target must be a direct child of quarantine root")
    if target.exists() or target.is_symlink():
        raise ValueError("quarantine target already exists")
    return (
        ProposedAction(
            kind="quarantine-move",
            target=str(target),
            command=("move", str(candidate_path), str(target)),
            force=False,
            receipt_required=True,
        ),
        (
            f"Move the quarantined resource from {target} back to {candidate_path} "
            "using the operation receipt, only while the original path remains absent."
        ),
    )


def _candidate_from_resource(
    context: ClosedHousekeepingContext,
    inventory: BoundResourceInventory,
    resource: dict[str, Any],
    quarantine_root: Path | None,
) -> HousekeepingCandidate:
    resource_id = _required_resource_id(resource.get("resource_id"))
    candidate_path = _required_absolute_path(
        resource.get("absolute_path"), f"resource {resource_id} absolute path"
    )
    containment_root = _required_absolute_path(
        resource.get("containment_root"), f"resource {resource_id} containment root"
    )
    resource_kind = _required_string(
        resource.get("resource_kind"), f"resource {resource_id} kind"
    )
    if resource_kind not in _RESOURCE_KINDS:
        raise ValueError(f"resource {resource_id} kind is not disposable")
    ownership = resource.get("ownership_classification")
    if ownership != "program-created-disposable":
        raise ValueError(f"resource {resource_id} ownership classification is not disposable")
    creation_authorization_id = _required_string(
        resource.get("creation_authorization_id"),
        f"resource {resource_id} creation authorization",
    )
    expected_filesystem_identity = _filesystem_identity_from_mapping(
        resource.get("filesystem_identity"),
        f"resource {resource_id} filesystem identity",
    )
    evidence_path, evidence_issues = resolve_managed_path(
        Path(context.program_root),
        resource.get("creation_evidence_path"),
        role=f"resource {resource_id} creation evidence",
    )
    if evidence_path is None:
        raise ValueError("; ".join(evidence_issues))
    evidence_digest = _required_sha256(
        resource.get("creation_evidence_sha256"),
        f"resource {resource_id} creation evidence digest",
    )
    if sha256_file(evidence_path) != evidence_digest:
        raise ValueError(f"resource {resource_id} creation evidence digest mismatch")
    evidence, evidence_issues = load_json_object(evidence_path)
    if evidence is None:
        raise ValueError("; ".join(evidence_issues))
    if (
        evidence.get("schema_version")
        != "implementation-resource-creation-evidence/v1"
        or evidence.get("resource_id") != resource_id
        or evidence.get("absolute_path") != str(candidate_path)
        or evidence.get("creation_authorization_id") != creation_authorization_id
        or evidence.get("filesystem_identity")
        != asdict(expected_filesystem_identity)
        or evidence.get("result") != "created-by-program"
        or evidence.get("accepted") is not True
    ):
        raise ValueError(f"resource {resource_id} creation evidence is not accepted provenance")
    if resource.get("disposable_after") != "program-closure":
        raise ValueError(f"resource {resource_id} is not disposable after program closure")
    recovery_deadline = _required_string(
        resource.get("recovery_deadline"), f"resource {resource_id} recovery deadline"
    )
    containment = _validate_candidate_path_boundary(
        context, candidate_path, containment_root
    )
    observed_filesystem_identity = _filesystem_identity(candidate_path)
    if observed_filesystem_identity != expected_filesystem_identity:
        raise ValueError(f"resource {resource_id} filesystem identity is stale")
    if resource_kind != "linked-worktree":
        if _is_registered_worktree(context.repository, candidate_path):
            raise ValueError(
                f"resource {resource_id} registered worktree must use linked-worktree kind"
            )
        if any(
            entry.name == ".git"
            for entry in (candidate_path, *candidate_path.rglob("*"))
        ):
            raise ValueError(
                f"resource {resource_id} contains unassessed Git metadata"
            )
    expected_fingerprint = _required_sha256(
        resource.get("fingerprint_sha256"), f"resource {resource_id} fingerprint"
    )
    observed_fingerprint = _tree_fingerprint(candidate_path)
    if observed_fingerprint != expected_fingerprint:
        raise ValueError(f"resource {resource_id} fingerprint is stale")

    worktree_state: WorktreeState | None = None
    if resource_kind == "linked-worktree":
        worktree_state = _inspect_worktree(context.repository, candidate_path)
        action = ProposedAction(
            kind="git-worktree-remove",
            target=None,
            command=("git", "worktree", "remove", str(candidate_path)),
            force=False,
            receipt_required=True,
        )
        recovery_mechanism = (
            f"Use the receipt branch {worktree_state.branch} and commit "
            f"{worktree_state.head_commit} with git worktree add to recreate "
            f"{candidate_path}."
        )
        safe_reason = (
            "The path is a registered, unlocked, clean non-current worktree; its "
            "HEAD is reachable from another local ref and it has no conflict or active operation."
        )
    else:
        if resource_kind == "ignored-cache":
            _verify_ignored_cache(context.repository, candidate_path)
        action, recovery_mechanism = _quarantine_action(
            resource_id, candidate_path, quarantine_root, containment
        )
        safe_reason = (
            "The directory has exact program-created provenance, is contained without "
            "symlinks or special entries, matches its closure-bound fingerprint, and "
            "does not overlap protected program, closure, or Git evidence."
        )
    return HousekeepingCandidate(
        resource_id=resource_id,
        absolute_path=str(candidate_path),
        resource_kind=resource_kind,
        program_created_provenance=ProgramCreatedProvenance(
            creation_authorization_id=creation_authorization_id,
            creation_evidence_path=str(evidence_path),
            creation_evidence_sha256=evidence_digest,
            resource_inventory_path=inventory.path,
            resource_inventory_sha256=inventory.sha256,
        ),
        ownership_classification=str(ownership),
        symlink_and_containment=containment,
        filesystem_identity=observed_filesystem_identity,
        fingerprint_sha256=observed_fingerprint,
        worktree_state=worktree_state,
        proposed_action=action,
        recovery=RecoveryPlan(
            deadline=recovery_deadline,
            mechanism=recovery_mechanism,
            receipt_required=True,
        ),
        safe_removal_reason=safe_reason,
    )


def build_housekeeping_proposal(
    program_root: Path,
    repository_root: Path,
    quarantine_root: Path | None = None,
) -> HousekeepingProposal:
    context = load_closed_housekeeping_context(program_root, repository_root)
    inventory = _load_bound_disposable_resources(context)
    resources = inventory.resources if inventory is not None else ()
    resolved_quarantine = (
        _validated_quarantine_root(context, quarantine_root)
        if quarantine_root is not None
        else None
    )
    resource_ids: set[str] = set()
    candidate_paths: set[str] = set()
    quarantine_targets: set[str] = set()
    candidates: list[HousekeepingCandidate] = []
    if inventory is not None:
        for resource in resources:
            candidate = _candidate_from_resource(
                context, inventory, resource, resolved_quarantine
            )
            if candidate.resource_id in resource_ids:
                raise ValueError("disposable resource ids must be unique")
            target = candidate.proposed_action.target
            if target is not None and target in quarantine_targets:
                raise ValueError("disposable resource quarantine targets must be unique")
            resolved_candidate_path = str(
                Path(candidate.absolute_path).resolve(strict=True)
            )
            if resolved_candidate_path in candidate_paths:
                raise ValueError("disposable resource paths must be unique")
            if any(
                _paths_overlap(Path(resolved_candidate_path), Path(existing))
                for existing in candidate_paths
            ):
                raise ValueError("disposable resource candidates must not overlap")
            resource_ids.add(candidate.resource_id)
            candidate_paths.add(resolved_candidate_path)
            if target is not None:
                quarantine_targets.add(target)
            candidates.append(candidate)
    quarantine = str(resolved_quarantine) if resolved_quarantine else None
    proposal = HousekeepingProposal(
        schema_version=PROPOSAL_SCHEMA,
        program_id=context.program_id,
        program_revision=context.program_revision,
        source_sha256=context.source_sha256,
        program_sha256=context.program_sha256,
        semantic_requirements_sha256=context.semantic_requirements_sha256,
        reconciliation_sha256=context.reconciliation_sha256,
        closure_packet_sha256=context.closure_packet_sha256,
        repository=context.repository,
        quarantine_root=quarantine,
        candidate_inventory_sha256="",
        candidates=tuple(
            sorted(candidates, key=lambda candidate: (candidate.absolute_path, candidate.resource_id))
        ),
        mode="dry-run",
        execution_authorized=False,
        next_action=STOP_ACTION,
    )
    return replace(
        proposal,
        candidate_inventory_sha256=candidate_inventory_sha256(proposal),
    )


def proposal_to_mapping(proposal: HousekeepingProposal) -> dict[str, object]:
    return asdict(proposal)


def validate_housekeeping_proposal(
    proposal: HousekeepingProposal,
    program_root: Path,
    repository_root: Path,
) -> list[str]:
    issues: list[str] = []
    if proposal.schema_version != PROPOSAL_SCHEMA:
        issues.append("unsupported housekeeping proposal schema")
    if proposal.mode != "dry-run":
        issues.append("housekeeping proposal mode must be dry-run")
    if proposal.execution_authorized is not False:
        issues.append("housekeeping proposal must not authorize execution")
    if proposal.next_action != STOP_ACTION:
        issues.append("housekeeping proposal must stop for separate authorization")
    if proposal.candidate_inventory_sha256 != candidate_inventory_sha256(proposal):
        issues.append("candidate inventory digest mismatch")
    if issues:
        return issues
    try:
        current = build_housekeeping_proposal(
            program_root,
            repository_root,
            Path(proposal.quarantine_root) if proposal.quarantine_root else None,
        )
    except (OSError, ValueError):
        return ["proposal inventory is stale"]
    if proposal_to_mapping(current) != proposal_to_mapping(proposal):
        return ["proposal inventory is stale"]
    return []


def _exact_fields(
    value: object,
    fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    mapping = _required_mapping(value, label)
    if set(mapping) != fields:
        raise ValueError(f"{label} fields do not match the supported schema")
    return mapping


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not all(isinstance(item, str) for item in value)
    ):
        raise ValueError(f"{label} must be a string list")
    return tuple(value)


def _repository_from_mapping(value: object) -> RepositoryIdentity:
    mapping = _exact_fields(
        value,
        frozenset(
            {"root", "branch", "head_commit", "git_directory", "git_common_directory"}
        ),
        "proposal repository",
    )
    return RepositoryIdentity(
        **{
            field: _required_string(mapping.get(field), f"proposal repository {field}")
            for field in mapping
        }
    )


def _candidate_from_mapping(value: object) -> HousekeepingCandidate:
    mapping = _exact_fields(
        value,
        frozenset(
            {
                "resource_id",
                "absolute_path",
                "resource_kind",
                "program_created_provenance",
                "ownership_classification",
                "symlink_and_containment",
                "filesystem_identity",
                "fingerprint_sha256",
                "worktree_state",
                "proposed_action",
                "recovery",
                "safe_removal_reason",
            }
        ),
        "housekeeping candidate",
    )
    provenance_mapping = _exact_fields(
        mapping.get("program_created_provenance"),
        frozenset(
            {
                "creation_authorization_id",
                "creation_evidence_path",
                "creation_evidence_sha256",
                "resource_inventory_path",
                "resource_inventory_sha256",
            }
        ),
        "candidate provenance",
    )
    provenance = ProgramCreatedProvenance(
        **{
            field: _required_string(provenance_mapping.get(field), f"provenance {field}")
            for field in provenance_mapping
        }
    )
    containment_mapping = _exact_fields(
        mapping.get("symlink_and_containment"),
        frozenset(
            {
                "containment_root",
                "contained",
                "candidate_is_symlink",
                "ancestor_symlink",
                "descendant_symlink",
                "any_symlink",
            }
        ),
        "candidate symlink and containment result",
    )
    for field in (
        "contained",
        "candidate_is_symlink",
        "ancestor_symlink",
        "descendant_symlink",
        "any_symlink",
    ):
        if not isinstance(containment_mapping.get(field), bool):
            raise ValueError(f"candidate containment {field} must be boolean")
    containment = SymlinkAndContainmentResult(
        containment_root=_required_string(
            containment_mapping.get("containment_root"), "candidate containment root"
        ),
        contained=containment_mapping["contained"],
        candidate_is_symlink=containment_mapping["candidate_is_symlink"],
        ancestor_symlink=containment_mapping["ancestor_symlink"],
        descendant_symlink=containment_mapping["descendant_symlink"],
        any_symlink=containment_mapping["any_symlink"],
    )
    filesystem_identity = _filesystem_identity_from_mapping(
        mapping.get("filesystem_identity"), "candidate filesystem identity"
    )
    worktree_value = mapping.get("worktree_state")
    worktree: WorktreeState | None = None
    if worktree_value is not None:
        worktree_mapping = _exact_fields(
            worktree_value,
            frozenset(
                {
                    "registered",
                    "is_current_worktree",
                    "branch",
                    "head_commit",
                    "staged_paths",
                    "modified_paths",
                    "untracked_paths",
                    "conflicted_paths",
                    "active_operation",
                    "locked",
                    "unique_commits",
                    "dirty",
                }
            ),
            "candidate worktree state",
        )
        for field in (
            "registered",
            "is_current_worktree",
            "locked",
            "unique_commits",
            "dirty",
        ):
            if not isinstance(worktree_mapping.get(field), bool):
                raise ValueError(f"candidate worktree {field} must be boolean")
        active_operation = worktree_mapping.get("active_operation")
        if active_operation is not None and not isinstance(active_operation, str):
            raise ValueError("candidate worktree active operation must be a string or null")
        worktree = WorktreeState(
            registered=worktree_mapping["registered"],
            is_current_worktree=worktree_mapping["is_current_worktree"],
            branch=_required_string(worktree_mapping.get("branch"), "worktree branch"),
            head_commit=_required_string(
                worktree_mapping.get("head_commit"), "worktree head commit"
            ),
            staged_paths=_string_tuple(worktree_mapping.get("staged_paths"), "staged paths"),
            modified_paths=_string_tuple(worktree_mapping.get("modified_paths"), "modified paths"),
            untracked_paths=_string_tuple(worktree_mapping.get("untracked_paths"), "untracked paths"),
            conflicted_paths=_string_tuple(worktree_mapping.get("conflicted_paths"), "conflicted paths"),
            active_operation=active_operation,
            locked=worktree_mapping["locked"],
            unique_commits=worktree_mapping["unique_commits"],
            dirty=worktree_mapping["dirty"],
        )
    action_mapping = _exact_fields(
        mapping.get("proposed_action"),
        frozenset({"kind", "target", "command", "force", "receipt_required"}),
        "candidate proposed action",
    )
    if not isinstance(action_mapping.get("force"), bool) or not isinstance(
        action_mapping.get("receipt_required"), bool
    ):
        raise ValueError("candidate proposed action flags must be boolean")
    target = action_mapping.get("target")
    if target is not None and not isinstance(target, str):
        raise ValueError("candidate proposed action target must be a string or null")
    action = ProposedAction(
        kind=_required_string(action_mapping.get("kind"), "proposed action kind"),
        target=target,
        command=_string_tuple(action_mapping.get("command"), "proposed action command"),
        force=action_mapping["force"],
        receipt_required=action_mapping["receipt_required"],
    )
    recovery_mapping = _exact_fields(
        mapping.get("recovery"),
        frozenset({"deadline", "mechanism", "receipt_required"}),
        "candidate recovery",
    )
    if not isinstance(recovery_mapping.get("receipt_required"), bool):
        raise ValueError("candidate recovery receipt_required must be boolean")
    return HousekeepingCandidate(
        resource_id=_required_resource_id(mapping.get("resource_id")),
        absolute_path=_required_string(mapping.get("absolute_path"), "candidate absolute path"),
        resource_kind=_required_string(mapping.get("resource_kind"), "candidate resource kind"),
        program_created_provenance=provenance,
        ownership_classification=_required_string(
            mapping.get("ownership_classification"), "candidate ownership classification"
        ),
        symlink_and_containment=containment,
        filesystem_identity=filesystem_identity,
        fingerprint_sha256=_required_sha256(
            mapping.get("fingerprint_sha256"), "candidate fingerprint"
        ),
        worktree_state=worktree,
        proposed_action=action,
        recovery=RecoveryPlan(
            deadline=_required_string(recovery_mapping.get("deadline"), "recovery deadline"),
            mechanism=_required_string(recovery_mapping.get("mechanism"), "recovery mechanism"),
            receipt_required=recovery_mapping["receipt_required"],
        ),
        safe_removal_reason=_required_string(
            mapping.get("safe_removal_reason"), "candidate safe removal reason"
        ),
    )


def housekeeping_proposal_from_mapping(value: object) -> HousekeepingProposal:
    mapping = _exact_fields(
        value,
        frozenset(
            {
                "schema_version",
                "program_id",
                "program_revision",
                "source_sha256",
                "program_sha256",
                "semantic_requirements_sha256",
                "reconciliation_sha256",
                "closure_packet_sha256",
                "repository",
                "quarantine_root",
                "candidate_inventory_sha256",
                "candidates",
                "mode",
                "execution_authorized",
                "next_action",
            }
        ),
        "housekeeping proposal",
    )
    revision = mapping.get("program_revision")
    if not isinstance(revision, int) or isinstance(revision, bool):
        raise ValueError("proposal program revision must be an integer")
    if not isinstance(mapping.get("execution_authorized"), bool):
        raise ValueError("proposal execution_authorized must be boolean")
    candidate_values = mapping.get("candidates")
    if not isinstance(candidate_values, Sequence) or isinstance(
        candidate_values, (str, bytes)
    ):
        raise ValueError("proposal candidates must be a list")
    quarantine = mapping.get("quarantine_root")
    if quarantine is not None and not isinstance(quarantine, str):
        raise ValueError("proposal quarantine root must be a string or null")
    return HousekeepingProposal(
        schema_version=_required_string(mapping.get("schema_version"), "proposal schema"),
        program_id=_required_string(mapping.get("program_id"), "proposal program id"),
        program_revision=revision,
        source_sha256=_required_sha256(mapping.get("source_sha256"), "proposal source digest"),
        program_sha256=_required_sha256(mapping.get("program_sha256"), "proposal program digest"),
        semantic_requirements_sha256=_required_sha256(
            mapping.get("semantic_requirements_sha256"), "proposal semantic requirements digest"
        ),
        reconciliation_sha256=_required_sha256(
            mapping.get("reconciliation_sha256"), "proposal reconciliation digest"
        ),
        closure_packet_sha256=_required_sha256(
            mapping.get("closure_packet_sha256"), "proposal closure packet digest"
        ),
        repository=_repository_from_mapping(mapping.get("repository")),
        quarantine_root=quarantine,
        candidate_inventory_sha256=_required_sha256(
            mapping.get("candidate_inventory_sha256"), "proposal candidate inventory digest"
        ),
        candidates=tuple(_candidate_from_mapping(item) for item in candidate_values),
        mode=_required_string(mapping.get("mode"), "proposal mode"),
        execution_authorized=mapping["execution_authorized"],
        next_action=_required_string(mapping.get("next_action"), "proposal next action"),
    )


def _load_role_records(
    context: ClosedHousekeepingContext,
    role: str,
) -> list[dict[str, Any]]:
    logical_roles = _required_mapping(
        context.manifest.get("logical_roles"), "manifest logical_roles"
    )
    path, path_issues = resolve_managed_path(
        Path(context.program_root), logical_roles.get(role), role=f"logical role {role}"
    )
    if path is None:
        raise ValueError("; ".join(path_issues))
    records, record_issues = load_json_lines(path)
    if records is None:
        raise ValueError("; ".join(record_issues))
    return records


def _later_action_context(context: ClosedHousekeepingContext) -> dict[str, object]:
    status = context.status
    fields = (
        "increment_id",
        "brief_sha256",
        "exact_file_plan_sha256",
        "approval_mode",
        "workspace",
    )
    for field in fields:
        if field not in status:
            raise ValueError(f"status is missing later-action authority field {field}")
    return {
        "program_id": context.program_id,
        "program_revision": context.program_revision,
        "source_id": context.source_id,
        "source_sha256": context.source_sha256,
        "program_sha256": context.program_sha256,
        "semantic_requirements_sha256": context.semantic_requirements_sha256,
        **{field: status[field] for field in fields},
    }


def check_housekeeping_authorization(
    proposal: HousekeepingProposal,
    program_root: Path,
    repository_root: Path,
    *,
    recovery_evidence: str,
) -> HousekeepingAuthorizationDecision:
    validation_issues = validate_housekeeping_proposal(
        proposal, program_root, repository_root
    )
    candidate_paths = tuple(
        sorted(candidate.absolute_path for candidate in proposal.candidates)
    )
    if validation_issues:
        return HousekeepingAuthorizationDecision(
            authorized=False,
            authorization_id=None,
            candidate_inventory_sha256=proposal.candidate_inventory_sha256,
            candidate_paths=candidate_paths,
            issues=tuple(validation_issues),
            next_action=AUTHORIZATION_STOP_ACTION,
        )
    context = load_closed_housekeeping_context(program_root, repository_root)
    closure_approvals = _load_role_records(context, "approvals")
    action_authorizations = _load_role_records(context, "action_authorizations")
    exact_inventory_grants = [
        record
        for record in action_authorizations
        if record.get("candidate_inventory_sha256")
        == proposal.candidate_inventory_sha256
        and record.get("candidate_paths") == list(candidate_paths)
    ]
    scope = (
        "apply post-closure housekeeping inventory "
        + proposal.candidate_inventory_sha256
    )
    later_decision = decide_later_action(
        program_state="closed",
        action="destructive-operation",
        scope=scope,
        reconciliation_sha256=proposal.reconciliation_sha256,
        closure_packet_sha256=proposal.closure_packet_sha256,
        closure_approvals=closure_approvals,
        action_authorizations=exact_inventory_grants,
        recovery_evidence=recovery_evidence,
        authority_context=_later_action_context(context),
    )
    issues = set(later_decision.issues)
    if not candidate_paths:
        issues.add("candidate inventory is empty")
    if not exact_inventory_grants:
        issues.add("no exact action authorization matches the candidate inventory")
    authorized = later_decision.authorized and not issues
    return HousekeepingAuthorizationDecision(
        authorized=authorized,
        authorization_id=later_decision.authorization_id if authorized else None,
        candidate_inventory_sha256=proposal.candidate_inventory_sha256,
        candidate_paths=candidate_paths,
        issues=tuple(sorted(issues)),
        next_action=AUTHORIZATION_STOP_ACTION,
    )


def _load_proposal_file(path: Path) -> HousekeepingProposal:
    candidate = Path(path)
    if not candidate.is_file() or candidate.is_symlink():
        raise ValueError("proposal path must be a regular non-symlink file")
    mapping, issues = load_json_object(candidate)
    if mapping is None:
        raise ValueError("; ".join(issues))
    return housekeeping_proposal_from_mapping(mapping)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or validate read-only post-closure housekeeping proposals."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    propose = commands.add_parser("propose")
    propose.add_argument("--program-root", type=Path, required=True)
    propose.add_argument("--repository-root", type=Path, required=True)
    propose.add_argument("--quarantine-root", type=Path)
    validate = commands.add_parser("validate-proposal")
    validate.add_argument("--proposal", type=Path, required=True)
    validate.add_argument("--program-root", type=Path, required=True)
    validate.add_argument("--repository-root", type=Path, required=True)
    authorize = commands.add_parser("check-authorization")
    authorize.add_argument("--proposal", type=Path, required=True)
    authorize.add_argument("--program-root", type=Path, required=True)
    authorize.add_argument("--repository-root", type=Path, required=True)
    authorize.add_argument("--recovery-evidence", required=True)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    try:
        options = _parser().parse_args(arguments)
        if options.command == "propose":
            proposal = build_housekeeping_proposal(
                options.program_root,
                options.repository_root,
                options.quarantine_root,
            )
            payload: object = proposal_to_mapping(proposal)
            exit_code = 0
        else:
            proposal = _load_proposal_file(options.proposal)
            if options.command == "validate-proposal":
                issues = validate_housekeeping_proposal(
                    proposal, options.program_root, options.repository_root
                )
                payload = {
                    "valid": not issues,
                    "issues": issues,
                    "next_action": STOP_ACTION,
                }
                exit_code = 0 if not issues else 1
            else:
                decision = check_housekeeping_authorization(
                    proposal,
                    options.program_root,
                    options.repository_root,
                    recovery_evidence=options.recovery_evidence,
                )
                payload = asdict(decision)
                exit_code = 0 if decision.authorized else 1
        sys.stdout.buffer.write(_canonical_json_bytes(payload))
        return exit_code
    except (OSError, ValueError) as error:
        sys.stderr.buffer.write(
            _canonical_json_bytes(
                {"error": str(error), "next_action": STOP_ACTION}
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
