#!/usr/bin/env python3
"""Publish one owner-bound implementation-program proposal with manifest last."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from program_authority import (
    PROPOSAL_VALIDATION_MODE,
    SUPPORTED_NEW_PROGRAM_APPROVAL_MODES,
    load_json_object,
    resolve_managed_path,
    sha256_file,
    validate_program_authority,
)
from repository_preparation import inspect_repository, validate_repository_stability


PROPOSAL_REQUEST_SCHEMA = "implementation-program-proposal-request/v1"
PUBLICATION_OWNER_SCHEMA = "implementation-proposal-publication-owner/v1"


@dataclass(frozen=True)
class ProposalPublication:
    program_root: str
    manifest_sha256: str
    status_sha256: str
    launch_sha256: str
    created_paths: tuple[str, ...]
    adopted_paths: tuple[str, ...]
    recovered: bool


class _UsageError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _after_persist(label: str) -> None:
    """Private test seam called only after a durable publication prefix."""
    del label


def _safe_relative_path(relative_path: str) -> PurePosixPath:
    pure = PurePosixPath(relative_path)
    if (
        not relative_path
        or "\\" in relative_path
        or pure.is_absolute()
        or pure.as_posix() != relative_path
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        raise ValueError(f"candidate path escapes publication root: {relative_path!r}")
    return pure


def _candidate_inventory(candidate_root: Path) -> tuple[str, ...]:
    root = Path(candidate_root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("candidate root must be a regular non-symlink directory")
    files: list[str] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                path = Path(entry.path)
                relative = path.relative_to(root).as_posix()
                _safe_relative_path(relative)
                if entry.is_symlink():
                    raise ValueError(f"candidate symlink is not allowed: {relative}")
                if entry.is_dir(follow_symlinks=False):
                    stack.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(relative)
                else:
                    raise ValueError(f"candidate special file is not allowed: {relative}")
    files.sort()
    if "manifest.json" not in files:
        raise ValueError("candidate manifest.json is missing")
    if ".publication-owner.json" in files:
        raise ValueError("candidate must not supply .publication-owner.json")
    return tuple(files)


def _candidate_file_digests(
    candidate_root: Path, inventory: Sequence[str]
) -> dict[str, str]:
    return {
        relative: sha256_file(candidate_root.joinpath(*_safe_relative_path(relative).parts))
        for relative in inventory
    }


def _repository_head(repository_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError("repository HEAD could not be resolved")
    return result.stdout.strip()


def _ensure_directory(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"publication directory is unsafe: {path}")
        return
    _ensure_directory(path.parent)
    path.mkdir()
    _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _create_or_adopt(path: Path, payload: bytes) -> bool:
    """Create one regular file exclusively, or adopt byte-identical bytes."""
    _ensure_directory(path.parent)
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"proposal-publication-recovery-required: unsafe {path}")
        if path.read_bytes() != payload:
            raise ValueError(f"proposal-publication-recovery-required: divergent {path}")
        return False
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written == 0:
                raise OSError(f"short write while publishing {path}")
            view = view[written:]
        os.fsync(descriptor)
    except FileExistsError:
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise ValueError(
                f"proposal-publication-recovery-required: divergent {path}"
            )
        return False
    except BaseException:
        opened_identity: tuple[int, int] | None = None
        if descriptor is not None:
            try:
                opened = os.fstat(descriptor)
                opened_identity = (opened.st_dev, opened.st_ino)
            except OSError:
                pass
            try:
                os.close(descriptor)
            except OSError:
                pass
            descriptor = None
        if opened_identity is not None:
            try:
                current = path.lstat()
                if (
                    stat.S_ISREG(current.st_mode)
                    and (current.st_dev, current.st_ino) == opened_identity
                ):
                    path.unlink()
                    _fsync_directory(path.parent)
            except OSError:
                pass
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    _fsync_directory(path.parent)
    return True


def _write_publication_owner(path: Path, payload: bytes) -> bool:
    return _create_or_adopt(path, payload)


def _load_candidate_manifest(candidate_root: Path) -> dict[str, Any]:
    manifest, issues = load_json_object(candidate_root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(issues))
    return manifest


def _candidate_workspace_matches(
    candidate_root: Path,
    manifest: dict[str, Any],
    inspection: Any,
    *,
    owned_prefixes: Sequence[str] = (),
) -> None:
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        raise ValueError("candidate manifest logical_roles must be an object")
    workspace_path, path_issues = resolve_managed_path(
        candidate_root,
        logical_roles.get("workspace"),
        role="logical role workspace",
    )
    if workspace_path is None:
        raise ValueError("; ".join(path_issues))
    workspace, workspace_issues = load_json_object(workspace_path)
    if workspace is None:
        raise ValueError("; ".join(workspace_issues))
    observation = inspection.observation
    selected = workspace.get("implementation_workspace")
    existing = workspace.get("pre_existing_work_at_selection")
    expected_selected = {
        "path": observation.path,
        "branch": observation.branch,
        "base_commit": observation.base_commit,
        "head_commit_at_selection": observation.head_commit,
    }
    untracked_paths = [
        path
        for path in observation.untracked_paths
        if not any(
            path == prefix.rstrip("/")
            or path.startswith(prefix.rstrip("/") + "/")
            for prefix in owned_prefixes
        )
    ]
    expected_existing = {
        "staged_paths": list(observation.staged_paths),
        "modified_paths": list(observation.modified_paths),
        "untracked_paths": untracked_paths,
        "conflicted_paths": list(observation.conflicted_paths),
        "active_git_operation": observation.active_git_operation,
    }
    if workspace.get("repository") != {"identity": observation.repository}:
        raise ValueError("candidate workspace repository binding mismatch")
    if selected != expected_selected or existing != expected_existing:
        raise ValueError("candidate workspace observation binding mismatch")


def _controlling_programs(repository_root: Path, current_program_id: str) -> list[str]:
    programs_root = repository_root / "implementation-programs"
    if programs_root.is_symlink():
        raise ValueError("implementation-programs must not be a symlink")
    if not programs_root.exists():
        return []
    if not programs_root.is_dir():
        raise ValueError("implementation-programs must be a directory")
    controlling: list[str] = []
    for child in sorted(programs_root.iterdir(), key=lambda path: path.name):
        manifest_path = child / "manifest.json"
        if child.is_symlink() or not child.is_dir() or not manifest_path.is_file():
            continue
        manifest, _ = load_json_object(manifest_path)
        if manifest is None:
            controlling.append(child.name)
            continue
        if manifest.get("program_id") == current_program_id:
            continue
        roles = manifest.get("logical_roles")
        status = None
        if isinstance(roles, dict):
            status_path, _ = resolve_managed_path(
                child, roles.get("status"), role="logical role status"
            )
            if status_path is not None:
                status, _ = load_json_object(status_path)
        if status is None or status.get("program_state") not in {"closed", "superseded"}:
            controlling.append(str(manifest.get("program_id", child.name)))
    return controlling


def _validate_source(
    source_plan: Path,
    expected_source_sha256: str,
    candidate_root: Path,
    manifest: dict[str, Any],
) -> None:
    if source_plan.is_symlink() or not source_plan.is_file():
        raise ValueError("source plan must be a regular non-symlink file")
    actual = sha256_file(source_plan)
    if actual != expected_source_sha256:
        raise ValueError(
            f"source digest mismatch: expected {expected_source_sha256}, found {actual}"
        )
    source_binding = manifest.get("source_binding")
    logical_roles = manifest.get("logical_roles")
    if not isinstance(source_binding, dict) or not isinstance(logical_roles, dict):
        raise ValueError("candidate source binding is incomplete")
    source_path, issues = resolve_managed_path(
        candidate_root,
        logical_roles.get("canonical_source_snapshot"),
        role="logical role canonical_source_snapshot",
    )
    if source_path is None:
        raise ValueError("; ".join(issues))
    if source_binding.get("sha256") != expected_source_sha256:
        raise ValueError("candidate source digest binding mismatch")
    if source_path.read_bytes() != source_plan.read_bytes():
        raise ValueError("candidate source bytes differ from the requested source plan")


def _validate_existing_target(
    target: Path, owner_bytes: bytes, expected_files: set[str]
) -> bool:
    if not target.exists() and not target.is_symlink():
        return False
    if target.is_symlink() or not target.is_dir():
        raise ValueError("target collision: program root is not a regular directory")
    owner_path = target / ".publication-owner.json"
    present = {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if not present:
        return True
    if (
        owner_path.is_symlink()
        or not owner_path.is_file()
        or owner_path.read_bytes() != owner_bytes
    ):
        raise ValueError("target collision: publication owner does not match")
    unexpected = present.difference(expected_files | {".publication-owner.json"})
    if unexpected:
        raise ValueError(
            "proposal-publication-recovery-required: unexpected target paths "
            + ", ".join(sorted(unexpected))
        )
    return True


def publish_program_proposal(
    repository_root: Path,
    source_plan: Path,
    candidate_root: Path,
    expected_source_sha256: str,
) -> ProposalPublication:
    """Publish or recover one proposal without overwriting any divergent byte."""
    repository = Path(repository_root).resolve(strict=True)
    source = Path(source_plan).resolve(strict=False)
    candidate = Path(candidate_root).resolve(strict=False)
    inventory = _candidate_inventory(candidate)
    manifest = _load_candidate_manifest(candidate)
    approval_mode = manifest.get("approval_mode")
    if approval_mode not in SUPPORTED_NEW_PROGRAM_APPROVAL_MODES:
        raise ValueError("unsupported-new-program-approval-mode")
    _validate_source(source, expected_source_sha256, candidate, manifest)
    validation_issues = validate_program_authority(
        candidate, validation_mode=PROPOSAL_VALIDATION_MODE
    )
    if validation_issues:
        raise ValueError("; ".join(validation_issues))

    program_id = manifest.get("program_id")
    revision = manifest.get("program_revision")
    if not isinstance(program_id, str) or not program_id.strip():
        raise ValueError("candidate program_id is required")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ValueError("candidate program_revision must be positive")
    if "/" in program_id or "\\" in program_id or program_id in {".", ".."}:
        raise ValueError("candidate program_id is not a safe directory name")

    target = repository / "implementation-programs" / program_id
    digests = _candidate_file_digests(candidate, inventory)
    request = {
        "schema_version": PROPOSAL_REQUEST_SCHEMA,
        "program_id": program_id,
        "program_revision": revision,
        "source_sha256": expected_source_sha256,
        "candidate_manifest_sha256": digests["manifest.json"],
        "candidate_inventory_sha256": _sha256_bytes(_canonical_json(digests)),
        "target": target.relative_to(repository).as_posix(),
    }
    request_bytes = _canonical_json(request)
    request_sha256 = _sha256_bytes(request_bytes)
    owner_token = request_sha256[:16]
    staging = repository / f".implementation-program-{program_id}-{owner_token}"
    owner = {
        "schema_version": PUBLICATION_OWNER_SCHEMA,
        "owner_token": owner_token,
        "program_id": program_id,
        "program_revision": revision,
        "request_sha256": request_sha256,
        "target": request["target"],
        "inventory": [
            {"path": path, "sha256": digests[path]} for path in inventory
        ],
    }
    owner_bytes = _canonical_json(owner)

    if target.exists() or target.is_symlink():
        owner_path = target / ".publication-owner.json"
        target_has_entries = (
            True
            if target.is_symlink()
            else (any(target.iterdir()) if target.is_dir() else True)
        )
        staging_owner = staging / ".publication-owner.json"
        recoverable_empty_reservation = (
            not target_has_entries
            and staging_owner.is_file()
            and not staging_owner.is_symlink()
            and staging_owner.read_bytes() == owner_bytes
        )
        if (
            target.is_symlink()
            or not target.is_dir()
            or (
                target_has_entries
                and (
                    owner_path.is_symlink()
                    or not owner_path.is_file()
                    or owner_path.read_bytes() != owner_bytes
                )
            )
            or (not target_has_entries and not recoverable_empty_reservation)
        ):
            raise ValueError("target collision: existing program root is not request-owned")

    head = _repository_head(repository)
    baseline = inspect_repository(repository, head)
    if baseline.observation.staged_paths or baseline.observation.conflicted_paths:
        raise ValueError("staged or conflicted repository state blocks publication")
    controlling = _controlling_programs(repository, program_id)
    if controlling:
        raise ValueError(
            "multiple controlling programs: " + ", ".join(sorted(controlling))
        )
    _candidate_workspace_matches(
        candidate,
        manifest,
        baseline,
        owned_prefixes=(
            staging.relative_to(repository).as_posix(),
            target.relative_to(repository).as_posix(),
        ),
    )

    created: list[str] = []
    adopted: list[str] = []
    preexisting_prefix = staging.exists() or target.exists()
    _ensure_directory(staging)
    owner_created = _write_publication_owner(
        staging / ".publication-owner.json", owner_bytes
    )
    _after_persist("owner-receipt")
    for relative in inventory:
        source_path = candidate.joinpath(*_safe_relative_path(relative).parts)
        destination = staging.joinpath(*_safe_relative_path(relative).parts)
        _create_or_adopt(destination, source_path.read_bytes())
        _after_persist(f"staging:{relative}")

    owned_prefixes = (
        staging.relative_to(repository).as_posix(),
        target.relative_to(repository).as_posix(),
    )
    current = inspect_repository(repository, head)
    stability_issues = validate_repository_stability(
        baseline, current, owned_prefixes=owned_prefixes
    )
    if stability_issues:
        raise ValueError("; ".join(stability_issues))
    if _controlling_programs(repository, program_id):
        raise ValueError("multiple controlling programs appeared during publication")
    _validate_source(source, expected_source_sha256, candidate, manifest)

    target_preexisted = _validate_existing_target(target, owner_bytes, set(inventory))
    if not target_preexisted:
        _ensure_directory(target.parent)
        try:
            target.mkdir()
        except FileExistsError as error:
            raise ValueError("target collision: program root appeared during reservation") from error
        _fsync_directory(target.parent)
    _after_persist("final-root-reserved")

    final_owner_created = _write_publication_owner(
        target / ".publication-owner.json", owner_bytes
    )
    (created if final_owner_created else adopted).append(".publication-owner.json")
    _after_persist("final:.publication-owner.json")
    for relative in inventory:
        if relative == "manifest.json":
            continue
        payload = staging.joinpath(*_safe_relative_path(relative).parts).read_bytes()
        was_created = _create_or_adopt(
            target.joinpath(*_safe_relative_path(relative).parts), payload
        )
        (created if was_created else adopted).append(relative)
        _after_persist(f"final:{relative}")

    current = inspect_repository(repository, head)
    stability_issues = validate_repository_stability(
        baseline, current, owned_prefixes=owned_prefixes
    )
    if stability_issues:
        raise ValueError("; ".join(stability_issues))
    if _controlling_programs(repository, program_id):
        raise ValueError("multiple controlling programs appeared before manifest publication")
    _validate_source(source, expected_source_sha256, candidate, manifest)

    manifest_payload = staging.joinpath("manifest.json").read_bytes()
    manifest_created = _create_or_adopt(target / "manifest.json", manifest_payload)
    (created if manifest_created else adopted).append("manifest.json")
    _after_persist("final:manifest.json")
    final_issues = validate_program_authority(
        target, validation_mode=PROPOSAL_VALIDATION_MODE
    )
    if final_issues:
        raise ValueError(
            "proposal-publication-recovery-required: " + "; ".join(final_issues)
        )
    final_manifest, _ = load_json_object(target / "manifest.json")
    assert final_manifest is not None
    roles = final_manifest["logical_roles"]
    status_path, status_issues = resolve_managed_path(
        target, roles.get("status"), role="logical role status"
    )
    if status_path is None:
        raise ValueError("; ".join(status_issues))
    return ProposalPublication(
        program_root=str(target),
        manifest_sha256=sha256_file(target / "manifest.json"),
        status_sha256=sha256_file(status_path),
        launch_sha256=request_sha256,
        created_paths=tuple(sorted(created)),
        adopted_paths=tuple(sorted(adopted)),
        recovered=(
            preexisting_prefix
            or target_preexisted
            or not owner_created
            or bool(adopted)
        ),
    )


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(prog="program_bootstrap.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    publish = subparsers.add_parser("publish")
    publish.add_argument("repository")
    publish.add_argument("--source-plan", required=True)
    publish.add_argument("--candidate-root", required=True)
    publish.add_argument("--expected-source-sha256", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        arguments = parser.parse_args(argv)
    except _UsageError as error:
        print(parser.format_usage().strip())
        print(f"program_bootstrap.py: error: {error}")
        return 2
    try:
        receipt = publish_program_proposal(
            Path(arguments.repository),
            Path(arguments.source_plan),
            Path(arguments.candidate_root),
            arguments.expected_source_sha256,
        )
    except (OSError, TypeError, ValueError) as error:
        print(str(error))
        return 1
    print(json.dumps(asdict(receipt), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
