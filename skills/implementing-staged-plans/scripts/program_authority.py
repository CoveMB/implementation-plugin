#!/usr/bin/env python3
"""Capture immutable sources and validate digest-bound program authority."""

import argparse
import ctypes
import hashlib
import importlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


MANIFEST_NAME = "manifest.json"
PROPOSAL_VALIDATION_MODE = "proposal"
APPROVED_VALIDATION_MODE = "approved"
VALIDATION_MODES = frozenset({PROPOSAL_VALIDATION_MODE, APPROVED_VALIDATION_MODE})
CLOSURE_STORAGE_SCHEMA = "implementation-closure-storage/v1"
INCREMENT_STORAGE_SCHEMA = "implementation-increment-storage/v1"
NEW_PROGRAM_MANIFEST_SCHEMA = "implementation-program-manifest/v2"
SETUP_PROGRAM_MANIFEST_SCHEMA = "implementation-program-manifest/v3"
NEW_PROGRAM_MANIFEST_SCHEMAS = frozenset(
    {NEW_PROGRAM_MANIFEST_SCHEMA, SETUP_PROGRAM_MANIFEST_SCHEMA}
)
SUPPORTED_NEW_PROGRAM_APPROVAL_MODES = frozenset(
    {"approval:standard", "approval:pre-approve", "approval:full-increment"}
)
REQUIRED_LOGICAL_ROLES = (
    "canonical_source_snapshot",
    "source_metadata",
    "approved_program",
    "traceability",
    "approvals",
)
NEW_PROGRAM_LOGICAL_ROLES = (
    *REQUIRED_LOGICAL_ROLES,
    "action_authorizations",
    "increment_grants",
    "rollovers",
    "block_resolutions",
    "workspace",
    "status",
)
NEW_PROGRAM_LEDGER_ROLES = (
    "approvals",
    "action_authorizations",
    "increment_grants",
    "rollovers",
    "block_resolutions",
)
SETUP_PROGRAM_LOGICAL_ROLES = (
    *NEW_PROGRAM_LOGICAL_ROLES,
    "setup_activation_decision",
    "source_gate_decisions",
)
SETUP_PROGRAM_LEDGER_ROLES = (*NEW_PROGRAM_LEDGER_ROLES, "source_gate_decisions")
SETUP_PROGRAM_ONLY_LOGICAL_ROLES = frozenset(
    {"setup_activation_decision", "source_gate_decisions"}
)
SETUP_PROGRAM_ONLY_MANIFEST_FIELDS = frozenset(
    {
        "setup_semantics",
        "setup_semantics_sha256",
        "source_gate_definitions",
        "source_gate_definitions_sha256",
    }
)
SETUP_AUTHORITY_RECORD_SCHEMAS = frozenset(
    {
        "implementation-approval/v2",
        "implementation-action-authorization/v2",
        "implementation-increment-grant/v2",
        "setup-activation-decision/v1",
        "source-gate-decision/v1",
    }
)
INCREMENT_STORAGE_FILENAME_FIELDS = (
    "brief_filename",
    "exact_file_plan_filename",
    "execution_baseline_filename",
    "review_evidence_filename",
    "review_packet_filename",
    "handoff_filename",
)
CLOSURE_STORAGE_FILENAME_FIELDS = (
    "reconciliation_filename",
    "packet_filename",
)
SEMANTIC_FIELDS = (
    "id",
    "group_id",
    "source_unit_ids",
    "normalized_requirement",
    "acceptance_criteria",
    "assigned_parts",
    "assigned_tasks",
    "assigned_increments",
)
ATOMIC_FIELDS = frozenset(
    (
        *SEMANTIC_FIELDS,
        "source_locator",
        "current_disposition",
        "decision_references",
        "implementation_evidence",
        "verification_evidence",
    )
)
SOURCE_UNIT_FIELDS = frozenset(
    (
        "id",
        "start_line",
        "end_line",
        "source_text_sha256",
        "classification",
        "requirement_ids",
    )
)
ALLOWED_DISPOSITIONS = frozenset(
    (
        "allocated",
        "implemented",
        "amended",
        "deferred",
        "rejected",
        "not-applicable",
        "resolved",
    )
)
SEMANTIC_IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceCaptureRecord:
    """Immutable result of a successful two-file source capture."""

    source_id: str
    snapshot_path: str
    metadata_path: str
    sha256: str
    byte_count: int
    line_count: int


@dataclass(frozen=True)
class _DirectoryNameSemantics:
    case_sensitive: bool
    normalizes_unicode: bool


class _UsageError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def _string_list(value: object, *, non_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (not non_empty or bool(value))
        and all(_is_non_empty_string(item) for item in value)
    )


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without interpreting its bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_object(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load one JSON object and return repository-data errors as issues."""
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


def load_json_lines(path: Path) -> tuple[list[dict[str, Any]] | None, list[str]]:
    """Load append-only JSON Lines records without accepting blank records."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None, [f"{path}: missing JSON Lines file"]
    except (OSError, UnicodeError) as error:
        return None, [f"{path}: could not be read: {error}"]

    records: list[dict[str, Any]] = []
    issues: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            issues.append(f"{path}: line {line_number} is blank")
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            issues.append(
                f"{path}: line {line_number} must contain valid JSON: {error.msg}"
            )
            continue
        if not isinstance(value, dict):
            issues.append(f"{path}: line {line_number} must contain a JSON object")
            continue
        records.append(value)
    if issues:
        return None, issues
    return records, []


def _contains_symlink(path: Path, stop_at: Path) -> bool:
    resolved_stop = stop_at.resolve()
    try:
        relative = path.absolute().relative_to(stop_at.absolute())
    except ValueError:
        return True
    current = stop_at.absolute()
    if current.is_symlink():
        return True
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return path.resolve(strict=False).is_relative_to(resolved_stop) is False


def resolve_managed_path(
    program_root: Path,
    relative_path: object,
    *,
    role: str = "managed path",
    require_file: bool = True,
) -> tuple[Path | None, list[str]]:
    """Resolve a relative POSIX path inside a program root and reject symlinks."""
    root = program_root.resolve()
    if not _is_non_empty_string(relative_path):
        return None, [f"{role}: path must be a non-empty relative POSIX path"]
    raw_path = str(relative_path)
    if "\\" in raw_path:
        return None, [f"{role}: path must use POSIX separators"]
    pure_path = PurePosixPath(raw_path)
    if pure_path.is_absolute() or any(part in ("", ".", "..") for part in pure_path.parts):
        return None, [f"{role}: path must stay under the program root"]
    candidate = program_root.joinpath(*pure_path.parts)
    if _contains_symlink(candidate, program_root):
        return None, [f"{role}: symlink paths are not allowed"]
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        return None, [f"{role}: path escapes the program root"]
    if require_file and not candidate.is_file():
        return None, [f"{role}: file is missing"]
    if require_file and candidate.is_symlink():
        return None, [f"{role}: symlink files are not allowed"]
    return candidate, []


def _darwin_directory_name_semantics(directory: Path) -> _DirectoryNameSemantics:
    """Read the mounted volume's filename comparison capabilities."""

    class _AttrList(ctypes.Structure):
        _fields_ = (
            ("bitmapcount", ctypes.c_ushort),
            ("reserved", ctypes.c_ushort),
            ("commonattr", ctypes.c_uint32),
            ("volattr", ctypes.c_uint32),
            ("dirattr", ctypes.c_uint32),
            ("fileattr", ctypes.c_uint32),
            ("forkattr", ctypes.c_uint32),
        )

    class _VolumeCapabilities(ctypes.Structure):
        _fields_ = (
            ("capabilities", ctypes.c_uint32 * 4),
            ("valid", ctypes.c_uint32 * 4),
        )

    class _CapabilityBuffer(ctypes.Structure):
        _fields_ = (
            ("length", ctypes.c_uint32),
            ("volume", _VolumeCapabilities),
        )

    attr_vol_info = 0x80000000
    attr_vol_capabilities = 0x00020000
    case_sensitive_capability = 0x00000100
    attributes = _AttrList(
        bitmapcount=5,
        reserved=0,
        commonattr=0,
        volattr=attr_vol_info | attr_vol_capabilities,
        dirattr=0,
        fileattr=0,
        forkattr=0,
    )
    result = _CapabilityBuffer()
    libc = ctypes.CDLL(None, use_errno=True)
    getattrlist = libc.getattrlist
    getattrlist.argtypes = (
        ctypes.c_char_p,
        ctypes.POINTER(_AttrList),
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_ulong,
    )
    getattrlist.restype = ctypes.c_int
    if getattrlist(
        os.fsencode(directory),
        ctypes.byref(attributes),
        ctypes.byref(result),
        ctypes.sizeof(result),
        0,
    ) != 0:
        error_number = ctypes.get_errno()
        raise OSError(
            error_number,
            f"could not query filesystem naming semantics for {directory}",
        )
    if not result.volume.valid[0] & case_sensitive_capability:
        raise ValueError(
            f"filesystem did not attest case semantics for {directory}"
        )
    return _DirectoryNameSemantics(
        case_sensitive=bool(
            result.volume.capabilities[0] & case_sensitive_capability
        ),
        # Darwin filesystems expose canonically equivalent Unicode names as
        # aliases even when their case comparison is sensitive.
        normalizes_unicode=True,
    )


def _linux_directory_name_semantics(directory: Path) -> _DirectoryNameSemantics:
    """Read Linux per-directory case-folding flags without creating entries."""
    import array
    import fcntl

    fs_ioc_getflags = (
        0x80000000
        | (ctypes.sizeof(ctypes.c_long) << 16)
        | (ord("f") << 8)
        | 1
    )
    fs_casefold_flag = 0x40000000
    descriptor = os.open(
        directory,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        flags = array.array("l", [0])
        try:
            fcntl.ioctl(descriptor, fs_ioc_getflags, flags, True)
        except OSError as error:
            raise ValueError(
                f"filesystem naming semantics are unsupported for {directory}: {error}"
            ) from error
    finally:
        os.close(descriptor)
    casefolded = bool(flags[0] & fs_casefold_flag)
    return _DirectoryNameSemantics(
        case_sensitive=not casefolded,
        normalizes_unicode=casefolded,
    )


def _windows_directory_name_semantics(directory: Path) -> _DirectoryNameSemantics:
    """Read the Windows per-directory case-sensitive-name flag."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        ctypes.c_wchar_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_void_p,
    )
    create_file.restype = ctypes.c_void_p
    get_information = kernel32.GetFileInformationByHandleEx
    get_information.argtypes = (
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_ulong,
    )
    get_information.restype = ctypes.c_int
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (ctypes.c_void_p,)
    close_handle.restype = ctypes.c_int

    file_read_attributes = 0x0080
    file_share_all = 0x0001 | 0x0002 | 0x0004
    open_existing = 3
    file_flag_backup_semantics = 0x02000000
    file_flag_open_reparse_point = 0x00200000
    file_case_sensitive_info = 23
    file_cs_flag_case_sensitive_dir = 0x00000001
    invalid_handle_value = ctypes.c_void_p(-1).value
    handle = create_file(
        str(directory),
        file_read_attributes,
        file_share_all,
        None,
        open_existing,
        file_flag_backup_semantics | file_flag_open_reparse_point,
        None,
    )
    if handle in (None, invalid_handle_value):
        error_number = ctypes.get_last_error()
        raise OSError(
            error_number,
            f"could not open directory to query naming semantics: {directory}",
        )
    flags = ctypes.c_uint32()
    try:
        if not get_information(
            handle,
            file_case_sensitive_info,
            ctypes.byref(flags),
            ctypes.sizeof(flags),
        ):
            error_number = ctypes.get_last_error()
            raise OSError(
                error_number,
                f"could not query directory naming semantics: {directory}",
            )
    finally:
        close_handle(handle)
    return _DirectoryNameSemantics(
        case_sensitive=bool(flags.value & file_cs_flag_case_sensitive_dir),
        normalizes_unicode=False,
    )


def _directory_name_semantics(directory: Path) -> _DirectoryNameSemantics:
    if sys.platform == "darwin":
        return _darwin_directory_name_semantics(directory)
    if sys.platform.startswith("linux"):
        return _linux_directory_name_semantics(directory)
    if os.name == "nt":
        return _windows_directory_name_semantics(directory)
    raise ValueError(
        f"filesystem naming semantics are unsupported on {sys.platform}"
    )


def _normalized_destination_part(
    value: str, semantics: _DirectoryNameSemantics
) -> str:
    normalized = (
        unicodedata.normalize("NFD", value)
        if semantics.normalizes_unicode
        else value
    )
    return normalized if semantics.case_sensitive else normalized.casefold()


def _destination_identity(path: Path) -> tuple[object, ...]:
    """Return filesystem identity for an existing or future managed path."""
    candidate = Path(path)
    if candidate.is_symlink():
        raise ValueError(f"destination must not be a symlink: {candidate}")
    if candidate.exists():
        target = candidate.stat(follow_symlinks=False)
        return ("existing", target.st_dev, target.st_ino)

    missing_parts: list[str] = []
    parent = candidate
    while not parent.exists():
        if parent.is_symlink():
            raise ValueError(f"destination parent must not be a symlink: {parent}")
        missing_parts.append(parent.name)
        parent = parent.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError(f"destination parent must be a directory: {parent}")

    before = parent.stat(follow_symlinks=False)
    semantics = _directory_name_semantics(parent)
    after = parent.stat(follow_symlinks=False)
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        raise ValueError(f"destination parent changed during validation: {parent}")
    normalized_parts = tuple(
        _normalized_destination_part(part, semantics)
        for part in reversed(missing_parts)
    )
    return ("future", before.st_dev, before.st_ino, normalized_parts)


def _destination_collision_issues(
    paths: Sequence[Path], *, label: str
) -> list[str]:
    identities: set[tuple[object, ...]] = set()
    issues: list[str] = []
    for path in paths:
        try:
            identity = _destination_identity(path)
        except (OSError, ValueError) as error:
            issues.append(f"{label}: {error}")
            continue
        if identity in identities:
            issues.append(f"{label} resolve duplicate filesystem targets")
        identities.add(identity)
    return sorted(set(issues))


def _resolve_storage_descriptor(
    program_root: Path,
    descriptor: object,
    *,
    label: str,
    schema: str,
    filename_fields: Sequence[str],
) -> tuple[dict[str, Path], list[str]]:
    """Resolve an immutable storage descriptor without requiring future files."""
    if not isinstance(descriptor, dict):
        return {}, [f"{label} must be an object"]
    expected_fields = frozenset({"schema_version", "root", *filename_fields})
    issues = _validate_exact_fields(descriptor, expected_fields, label)
    if descriptor.get("schema_version") != schema:
        issues.append(f"{label} schema_version must be {schema}")

    root_value = descriptor.get("root")
    if not _is_non_empty_string(root_value):
        issues.append(f"{label} root must be a non-empty relative POSIX path")
        return {}, sorted(set(issues))
    raw_root = str(root_value)
    root_path = PurePosixPath(raw_root)
    if (
        "\\" in raw_root
        or root_path.is_absolute()
        or root_path.as_posix() != raw_root
        or any(part in ("", ".", "..") for part in root_path.parts)
    ):
        issues.append(f"{label} root must stay under the program root")
        return {}, sorted(set(issues))

    storage_root = program_root.joinpath(*root_path.parts)
    if _contains_symlink(storage_root, program_root):
        issues.append(f"{label} root must not contain a symlink")
    elif storage_root.exists() and not storage_root.is_dir():
        issues.append(f"{label} root must be a directory when it exists")

    paths: dict[str, Path] = {}
    for field in filename_fields:
        value = descriptor.get(field)
        if not _is_non_empty_string(value):
            issues.append(f"{label} {field} must be a non-empty filename")
            continue
        filename = str(value)
        pure_filename = PurePosixPath(filename)
        if (
            "\\" in filename
            or pure_filename.is_absolute()
            or len(pure_filename.parts) != 1
            or pure_filename.name in ("", ".", "..")
        ):
            issues.append(f"{label} {field} must be one relative filename")
            continue
        candidate = storage_root / filename
        if _contains_symlink(candidate, program_root):
            issues.append(f"{label} {field} must not contain a symlink")
            continue
        if candidate.exists() and (candidate.is_symlink() or not candidate.is_file()):
            issues.append(f"{label} {field} must be a regular file when it exists")
            continue
        paths[field] = candidate

    issues.extend(
        _destination_collision_issues(
            list(paths.values()), label=label
        )
    )
    return paths, sorted(set(issues))


def resolve_program_closure_paths(program_root: Path) -> dict[str, Path]:
    """Resolve manifest-owned new-model closure paths without creating them."""
    root = Path(program_root)
    manifest, issues = load_json_object(root / MANIFEST_NAME)
    if manifest is None:
        raise ValueError("; ".join(issues))
    paths, path_issues = _resolve_storage_descriptor(
        root,
        manifest.get("closure_storage"),
        label="closure_storage",
        schema=CLOSURE_STORAGE_SCHEMA,
        filename_fields=CLOSURE_STORAGE_FILENAME_FIELDS,
    )
    if path_issues:
        raise ValueError("; ".join(path_issues))
    logical_roles = manifest.get("logical_roles")
    if (
        manifest.get("schema_version") in NEW_PROGRAM_MANIFEST_SCHEMAS
        and isinstance(logical_roles, dict)
        and isinstance(manifest.get("increment_storage"), dict)
    ):
        increment_paths, increment_issues = _resolve_storage_descriptor(
            root,
            manifest.get("increment_storage"),
            label="increment_storage",
            schema=INCREMENT_STORAGE_SCHEMA,
            filename_fields=INCREMENT_STORAGE_FILENAME_FIELDS,
        )
        traceability: dict[str, Any] | None = None
        traceability_value = logical_roles.get("traceability")
        if _is_non_empty_string(traceability_value):
            traceability_path, traceability_path_issues = resolve_managed_path(
                root,
                traceability_value,
                role="logical role traceability",
            )
            if traceability_path is None:
                raise ValueError("; ".join(traceability_path_issues))
            traceability, traceability_issues = load_json_object(traceability_path)
            if traceability is None:
                raise ValueError("; ".join(traceability_issues))
        status: dict[str, Any] | None = None
        status_value = logical_roles.get("status")
        if _is_non_empty_string(status_value):
            status_path, status_path_issues = resolve_managed_path(
                root,
                status_value,
                role="logical role status",
                require_file=False,
            )
            if status_path is None:
                raise ValueError("; ".join(status_path_issues))
            if status_path.is_file() and not status_path.is_symlink():
                status, status_issues = load_json_object(status_path)
                if status is None:
                    raise ValueError("; ".join(status_issues))
        destination_issues = _new_manifest_destination_collision_issues(
            root,
            manifest,
            logical_roles,
            increment_paths=increment_paths,
            closure_paths=paths,
            increment_ids=_manifest_increment_ids(
                manifest, traceability, status
            ),
        )
        all_issues = sorted(set([*increment_issues, *destination_issues]))
        if all_issues:
            raise ValueError("; ".join(all_issues))
    return {
        "reconciliation": paths["reconciliation_filename"],
        "packet": paths["packet_filename"],
    }


def compute_semantic_requirements_digest(
    atomic_requirements: object,
) -> str:
    """Hash only stable semantic fields from ordered atomic requirements."""
    if not isinstance(atomic_requirements, list):
        raise TypeError("atomic_requirements must be a list")
    semantic_records: list[dict[str, object]] = []
    for index, record in enumerate(atomic_requirements):
        if not isinstance(record, dict):
            raise TypeError(f"atomic requirement {index} must be an object")
        semantic_records.append({field: record.get(field) for field in SEMANTIC_FIELDS})
    canonical = json.dumps(
        semantic_records,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_source_binding(
    manifest: dict[str, Any],
    metadata: dict[str, Any],
    traceability: dict[str, Any],
    source_path: Path,
    source_role_path: str,
) -> tuple[list[bytes], list[str]]:
    """Validate the exact source bytes against all current bindings."""
    issues: list[str] = []
    try:
        source_bytes = source_path.read_bytes()
    except (OSError, UnicodeError) as error:
        return [], [f"source: could not be read: {error}"]
    source_lines = source_bytes.splitlines(keepends=True)
    actual_sha256 = hashlib.sha256(source_bytes).hexdigest()

    source_binding = manifest.get("source_binding")
    if not isinstance(source_binding, dict):
        issues.append("manifest source_binding must be an object")
        source_binding = {}

    expected_pairs = (
        ("manifest source_id", source_binding.get("source_id"), metadata.get("source_id")),
        ("traceability source_id", traceability.get("source_id"), metadata.get("source_id")),
        ("manifest source sha256", source_binding.get("sha256"), actual_sha256),
        ("metadata source sha256", metadata.get("sha256"), actual_sha256),
        ("traceability source sha256", traceability.get("source_sha256"), actual_sha256),
        ("metadata snapshot_path", metadata.get("snapshot_path"), source_role_path),
        ("metadata byte_count", metadata.get("byte_count"), len(source_bytes)),
        ("metadata line_count", metadata.get("line_count"), len(source_lines)),
    )
    for label, actual, expected in expected_pairs:
        if actual != expected:
            issues.append(f"{label} mismatch: expected {expected!r}, found {actual!r}")
    if metadata.get("immutable") is not True:
        issues.append("source metadata immutable must be true")
    return source_lines, issues


def _validate_exact_fields(
    record: dict[str, Any], expected: frozenset[str], label: str
) -> list[str]:
    actual = frozenset(record)
    if actual == expected:
        return []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    return [f"{label} fields mismatch: missing={missing!r}, extra={extra!r}"]


def _validate_source_units(
    source_lines: list[bytes], source_units: object
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    issues: list[str] = []
    if not isinstance(source_units, list):
        return {}, ["traceability source_units must be a list"]
    unit_by_id: dict[str, dict[str, Any]] = {}
    next_line = 1
    for index, value in enumerate(source_units):
        label = f"source unit {index}"
        if not isinstance(value, dict):
            issues.append(f"{label} must be an object")
            continue
        classification = value.get("classification")
        expected_fields = SOURCE_UNIT_FIELDS | (
            frozenset(("context_rationale",)) if classification == "context" else frozenset()
        )
        issues.extend(_validate_exact_fields(value, expected_fields, label))
        unit_id = value.get("id")
        if not _is_non_empty_string(unit_id):
            issues.append(f"{label} id must be a non-empty string")
        elif unit_id in unit_by_id:
            issues.append(f"duplicate source unit id {unit_id}")
        else:
            unit_by_id[unit_id] = value

        start_line = value.get("start_line")
        end_line = value.get("end_line")
        valid_range = (
            isinstance(start_line, int)
            and not isinstance(start_line, bool)
            and isinstance(end_line, int)
            and not isinstance(end_line, bool)
            and start_line > 0
            and end_line >= start_line
        )
        if not valid_range:
            issues.append(f"{label} has a reversed or invalid line range")
            continue
        if start_line != next_line:
            issues.append(
                f"source unit partition expected line {next_line}, found {start_line}"
            )
        next_line = end_line + 1
        if end_line > len(source_lines):
            issues.append(f"{label} line range exceeds source line count")
        else:
            unit_bytes = b"".join(source_lines[start_line - 1 : end_line])
            actual_digest = hashlib.sha256(unit_bytes).hexdigest()
            if value.get("source_text_sha256") != actual_digest:
                issues.append(f"{label} source_text_sha256 mismatch")

        requirement_ids = value.get("requirement_ids")
        if classification == "requirement":
            if not _string_list(requirement_ids, non_empty=True):
                issues.append(f"{label} requirement_ids must be a non-empty string list")
        elif classification == "context":
            if requirement_ids != []:
                issues.append(f"{label} context requirement_ids must be empty")
            if not _is_non_empty_string(value.get("context_rationale")):
                issues.append(f"{label} context_rationale must be non-empty")
        else:
            issues.append(f"{label} classification must be requirement or context")
    expected_final = len(source_lines) + 1
    if next_line != expected_final:
        issues.append(
            f"source unit partition ends at line {next_line - 1}, expected {len(source_lines)}"
        )
    if not source_lines and source_units:
        issues.append("empty source must not contain source units")
    return unit_by_id, issues


def _validate_atomic_requirements(
    atomic_requirements: object,
    requirement_groups: object,
    unit_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not isinstance(atomic_requirements, list):
        return ["traceability atomic_requirements must be a list"]
    if not isinstance(requirement_groups, list):
        issues.append("traceability requirement_groups must be a list")
        requirement_groups = []
    group_ids = {
        value.get("id")
        for value in requirement_groups
        if isinstance(value, dict) and _is_non_empty_string(value.get("id"))
    }
    atomic_by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(atomic_requirements):
        label = f"atomic requirement {index}"
        if not isinstance(value, dict):
            issues.append(f"{label} must be an object")
            continue
        issues.extend(_validate_exact_fields(value, ATOMIC_FIELDS, label))
        requirement_id = value.get("id")
        if not _is_non_empty_string(requirement_id) or not SEMANTIC_IDENTIFIER_PATTERN.fullmatch(
            str(requirement_id)
        ):
            issues.append(f"{label} id must be a stable semantic uppercase identifier")
        elif requirement_id in atomic_by_id:
            issues.append(f"duplicate atomic requirement id {requirement_id}")
        else:
            atomic_by_id[requirement_id] = value
        if value.get("group_id") not in group_ids:
            issues.append(f"{label} group_id does not reference a requirement group")
        source_unit_ids = value.get("source_unit_ids")
        if not _string_list(source_unit_ids, non_empty=True):
            issues.append(f"{label} source_unit_ids must be a non-empty string list")
        else:
            if len(source_unit_ids) != len(set(source_unit_ids)):
                issues.append(f"{label} source_unit_ids must be unique")
            for unit_id in source_unit_ids:
                unit = unit_by_id.get(unit_id)
                if unit is None:
                    issues.append(f"{label} references missing source unit {unit_id}")
                elif unit.get("classification") != "requirement":
                    issues.append(f"{label} references context source unit {unit_id}")
                elif requirement_id not in unit.get("requirement_ids", []):
                    issues.append(
                        f"{label} is not reciprocally referenced by source unit {unit_id}"
                    )
        for field in ("source_locator", "normalized_requirement"):
            if not _is_non_empty_string(value.get(field)):
                issues.append(f"{label} {field} must be non-empty")
        for field in (
            "acceptance_criteria",
            "assigned_parts",
            "assigned_tasks",
            "assigned_increments",
        ):
            if not _string_list(value.get(field), non_empty=True):
                issues.append(f"{label} {field} must be a non-empty string list")
        for field in (
            "decision_references",
            "implementation_evidence",
            "verification_evidence",
        ):
            if not _string_list(value.get(field)):
                issues.append(f"{label} {field} must be a string list")
        disposition = value.get("current_disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            issues.append(f"{label} current_disposition is invalid")
        elif disposition not in ("allocated", "implemented") and not value.get(
            "decision_references"
        ):
            issues.append(
                f"{label} disposition {disposition} requires a decision reference"
            )

    for unit_id, unit in unit_by_id.items():
        if unit.get("classification") != "requirement":
            continue
        for requirement_id in unit.get("requirement_ids", []):
            atomic = atomic_by_id.get(requirement_id)
            if atomic is None:
                issues.append(
                    f"source unit {unit_id} references missing atomic requirement {requirement_id}"
                )
            elif unit_id not in atomic.get("source_unit_ids", []):
                issues.append(
                    f"source unit {unit_id} is not reciprocally referenced by atomic requirement {requirement_id}"
                )
    return issues


def validate_traceability(
    traceability: dict[str, Any],
    source_lines: list[bytes],
    *,
    allow_incomplete: bool = False,
) -> list[str]:
    """Validate full line partitioning, atomic records, and completeness claim."""
    issues: list[str] = []
    if traceability.get("schema_version") != "implementation-traceability/v2":
        issues.append("traceability schema_version must be implementation-traceability/v2")
    source_units = traceability.get("source_units")
    unit_by_id, unit_issues = _validate_source_units(source_lines, source_units)
    issues.extend(unit_issues)
    atomic_requirements = traceability.get("atomic_requirements")
    issues.extend(
        _validate_atomic_requirements(
            atomic_requirements,
            traceability.get("requirement_groups"),
            unit_by_id,
        )
    )
    coverage = traceability.get("coverage_assertion")
    if not isinstance(coverage, dict):
        issues.append("traceability coverage_assertion must be an object")
        return issues
    if coverage.get("source_line_count") != len(source_lines):
        issues.append("coverage source_line_count mismatch")
    if isinstance(atomic_requirements, list):
        semantic_digest = compute_semantic_requirements_digest(atomic_requirements)
        if coverage.get("semantic_requirements_sha256") != semantic_digest:
            issues.append("coverage semantic_requirements_sha256 mismatch")
    complete_claim = coverage.get("status") == "complete" and coverage.get(
        "machine_complete"
    ) is True
    if not complete_claim and not allow_incomplete:
        issues.append("program authority requires an accepted machine completeness claim")
    if complete_claim and issues:
        issues.append("machine_complete true is invalid while completeness issues exist")
    return issues


def _validate_prior_revision(
    program_root: Path, traceability: dict[str, Any]
) -> list[str]:
    history = traceability.get("revision_history")
    revision = traceability.get("program_revision")
    if history is None:
        if isinstance(revision, int) and not isinstance(revision, bool) and revision > 1:
            return ["later program revision requires revision_history preservation bindings"]
        return []
    if not isinstance(history, dict):
        return ["revision_history must be an object"]
    issues: list[str] = []
    if isinstance(revision, int) and not isinstance(revision, bool) and revision > 1:
        superseded_revision = history.get("supersedes_program_revision")
        if (
            not isinstance(superseded_revision, int)
            or isinstance(superseded_revision, bool)
            or superseded_revision < 1
            or superseded_revision >= revision
        ):
            issues.append(
                "revision_history supersedes_program_revision must name an earlier positive revision"
            )
        for required_field in (
            "prior_source_path",
            "prior_source_sha256",
            "prior_program_path",
            "prior_program_sha256",
        ):
            if required_field not in history:
                issues.append(f"revision_history is missing {required_field}")
    path_pairs = (
        ("prior_source_path", "prior_source_sha256", "prior source"),
        ("prior_program_path", "prior_program_sha256", "prior program"),
        ("prior_traceability_path", "prior_traceability_sha256", "prior traceability"),
    )
    for path_field, digest_field, label in path_pairs:
        if path_field not in history and digest_field not in history:
            continue
        path, path_issues = resolve_managed_path(
            program_root, history.get(path_field), role=label
        )
        issues.extend(path_issues)
        if path is not None:
            expected = history.get(digest_field)
            if not _is_sha256(expected) or sha256_file(path) != expected:
                issues.append(f"{label} digest mismatch")
    evidence = history.get("prior_evidence", [])
    if not isinstance(evidence, list):
        issues.append("prior_evidence must be a list")
    elif isinstance(revision, int) and revision > 1 and not evidence:
        issues.append("later program revision requires prior evidence bindings")
    else:
        for index, record in enumerate(evidence):
            label = f"prior evidence {index}"
            if not isinstance(record, dict):
                issues.append(f"{label} must be an object")
                continue
            path, path_issues = resolve_managed_path(
                program_root, record.get("path"), role=label
            )
            issues.extend(path_issues)
            if path is not None:
                expected = record.get("sha256")
                if not _is_sha256(expected) or sha256_file(path) != expected:
                    issues.append(f"{label} digest mismatch")
    return issues


def validate_program_approval(
    manifest: dict[str, Any],
    traceability: dict[str, Any],
    approval_records: list[dict[str, Any]],
) -> list[str]:
    """Require one current exact approval and reject conflicting duplicates."""
    issues: list[str] = []
    source_binding = manifest.get("source_binding")
    program_binding = manifest.get("program_binding")
    coverage = traceability.get("coverage_assertion")
    if not all(isinstance(value, dict) for value in (source_binding, program_binding, coverage)):
        return ["approval binding inputs are incomplete"]
    expected = {
        "type": "program-approval",
        "decision": "approved",
        "program_id": manifest.get("program_id"),
        "program_revision": manifest.get("program_revision"),
        "source_id": source_binding.get("source_id"),
        "source_sha256": source_binding.get("sha256"),
        "program_sha256": program_binding.get("sha256"),
        "semantic_requirements_sha256": coverage.get(
            "semantic_requirements_sha256"
        ),
        "approval_mode": manifest.get("approval_mode"),
    }
    candidates = [
        record
        for record in approval_records
        if record.get("type") == "program-approval"
        and record.get("program_id") == expected["program_id"]
        and record.get("program_revision") == expected["program_revision"]
    ]
    matching = [
        record
        for record in candidates
        if all(record.get(field) == value for field, value in expected.items())
    ]
    if len(matching) != 1:
        issues.append(
            f"current program approval must have exactly one exact approved binding; found {len(matching)}"
        )
    candidate_bindings = {
        tuple(record.get(field) for field in expected) for record in candidates
    }
    if len(candidate_bindings) > 1:
        issues.append("conflicting current program approval records")
    if matching:
        approval_id = matching[0].get("event_id")
        if (
            manifest.get("schema_version") not in NEW_PROGRAM_MANIFEST_SCHEMAS
            and coverage.get("approval_event_id") != approval_id
        ):
            issues.append("coverage approval_event_id mismatch")
    return issues


def _validate_new_manifest_contract(
    root: Path,
    manifest: dict[str, Any],
    logical_roles: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    manifest_schema = manifest.get("schema_version")
    if manifest_schema not in NEW_PROGRAM_MANIFEST_SCHEMAS:
        return issues
    if manifest.get("approval_mode") not in SUPPORTED_NEW_PROGRAM_APPROVAL_MODES:
        issues.append("new program approval_mode is unsupported")
    for forbidden in ("program_status", "current_increment"):
        if forbidden in manifest:
            issues.append(f"new manifest must not contain mutable {forbidden}")
    if any(
        role in logical_roles for role in ("closure_reconciliation", "closure_packet")
    ):
        issues.append("new manifest must not duplicate closure logical roles")

    increment_paths, increment_issues = _resolve_storage_descriptor(
        root,
        manifest.get("increment_storage"),
        label="increment_storage",
        schema=INCREMENT_STORAGE_SCHEMA,
        filename_fields=INCREMENT_STORAGE_FILENAME_FIELDS,
    )
    closure_paths, closure_issues = _resolve_storage_descriptor(
        root,
        manifest.get("closure_storage"),
        label="closure_storage",
        schema=CLOSURE_STORAGE_SCHEMA,
        filename_fields=CLOSURE_STORAGE_FILENAME_FIELDS,
    )
    issues.extend(increment_issues)
    issues.extend(closure_issues)
    if manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA:
        try:
            setup_module = importlib.import_module("program_setup")
        except ModuleNotFoundError as error:
            if error.name != "program_setup":
                issues.append(str(error))
                setup_module = None
            else:
                script_root = str(Path(__file__).resolve().parent)
                sys.path.insert(0, script_root)
                try:
                    setup_module = importlib.import_module("program_setup")
                except (ImportError, OSError, TypeError, ValueError) as nested_error:
                    issues.append(str(nested_error))
                    setup_module = None
                finally:
                    sys.path.remove(script_root)
        except (ImportError, OSError, TypeError, ValueError) as error:
            issues.append(str(error))
            setup_module = None
        if setup_module is not None:
            issues.extend(setup_module.validate_setup_semantics(root))
    return sorted(set(issues))


def _new_manifest_destination_collision_issues(
    root: Path,
    manifest: dict[str, Any],
    logical_roles: dict[str, Any],
    *,
    increment_paths: dict[str, Path],
    closure_paths: dict[str, Path],
    increment_ids: Sequence[object],
) -> list[str]:
    logical_role_names = (
        SETUP_PROGRAM_LOGICAL_ROLES
        if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
        else NEW_PROGRAM_LOGICAL_ROLES
    )
    role_paths: list[Path] = []
    for role in logical_role_names:
        path, _ = resolve_managed_path(
            root,
            logical_roles.get(role),
            role=f"logical role {role}",
            require_file=False,
        )
        if path is not None:
            role_paths.append(path)
    allocated_increment_paths, allocation_issues = (
        _allocated_increment_storage_paths(root, increment_ids, increment_paths)
    )
    collision_issues = _destination_collision_issues(
        [*role_paths, *allocated_increment_paths, *closure_paths.values()],
        label="new manifest destinations",
    )
    return sorted(set([*allocation_issues, *collision_issues]))


def _allocated_increment_storage_paths(
    root: Path,
    allocated_increment_ids: Sequence[object],
    increment_paths: dict[str, Path],
) -> tuple[list[Path], list[str]]:
    increment_ids: set[str] = set()
    issues: list[str] = []
    for value in allocated_increment_ids:
        if not _is_non_empty_string(value):
            continue
        increment_id = str(value)
        pure_increment_id = PurePosixPath(increment_id)
        if (
            "\\" in increment_id
            or pure_increment_id.is_absolute()
            or len(pure_increment_id.parts) != 1
            or pure_increment_id.name in ("", ".", "..")
        ):
            issues.append(
                f"increment storage allocation {increment_id!r} must be one safe path segment"
            )
            continue
        increment_ids.add(increment_id)

    paths: list[Path] = []
    for increment_id in sorted(increment_ids):
        for field, base_path in sorted(increment_paths.items()):
            candidate = base_path.parent / increment_id / base_path.name
            if _contains_symlink(candidate, root):
                issues.append(
                    f"increment_storage {field} for {increment_id} must not contain a symlink"
                )
                continue
            if candidate.exists() and (
                candidate.is_symlink() or not candidate.is_file()
            ):
                issues.append(
                    f"increment_storage {field} for {increment_id} must be a regular file when it exists"
                )
                continue
            paths.append(candidate)
    return paths, sorted(set(issues))


def _manifest_increment_ids(
    manifest: dict[str, Any],
    traceability: dict[str, Any] | None,
    status: dict[str, Any] | None,
) -> list[object]:
    increment_ids: list[object] = []
    if isinstance(status, dict):
        increment_ids.append(status.get("current_increment_id"))
    semantics = manifest.get("setup_semantics")
    increments = semantics.get("increments") if isinstance(semantics, dict) else None
    if isinstance(increments, list):
        increment_ids.extend(
            increment.get("increment_id")
            for increment in increments
            if isinstance(increment, dict)
        )
    requirements = (
        traceability.get("atomic_requirements")
        if isinstance(traceability, dict)
        else None
    )
    if isinstance(requirements, list):
        for requirement in requirements:
            assigned = (
                requirement.get("assigned_increments")
                if isinstance(requirement, dict)
                else None
            )
            if not isinstance(assigned, list):
                continue
            increment_ids.extend(
                value
                for value in assigned
                if _is_non_empty_string(value)
                and len(PurePosixPath(str(value)).parts) == 1
                and "\\" not in str(value)
            )
    return increment_ids


def _validate_proposal_workspace(
    manifest: dict[str, Any], workspace: dict[str, Any]
) -> list[str]:
    issues: list[str] = []
    if workspace.get("schema_version") != "implementation-workspace-proposal/v1":
        issues.append(
            "proposal workspace schema_version must be implementation-workspace-proposal/v1"
        )
    if workspace.get("program_id") != manifest.get("program_id"):
        issues.append("proposal workspace program_id mismatch")
    if workspace.get("program_revision") != manifest.get("program_revision"):
        issues.append("proposal workspace program_revision mismatch")
    repository = workspace.get("repository")
    if not isinstance(repository, dict) or not _is_non_empty_string(
        repository.get("identity")
    ):
        issues.append("proposal workspace repository identity is required")
    selected = workspace.get("implementation_workspace")
    if not isinstance(selected, dict):
        issues.append("proposal implementation_workspace must be an object")
    else:
        for field in ("path", "branch", "base_commit", "head_commit_at_selection"):
            if not _is_non_empty_string(selected.get(field)):
                issues.append(f"proposal workspace {field} is required")
    existing = workspace.get("pre_existing_work_at_selection")
    if not isinstance(existing, dict):
        issues.append("proposal pre_existing_work_at_selection must be an object")
    else:
        for field in (
            "staged_paths",
            "modified_paths",
            "untracked_paths",
            "conflicted_paths",
        ):
            if not _string_list(existing.get(field)):
                issues.append(f"proposal workspace {field} must be a string list")
        if existing.get("active_git_operation") is not None:
            issues.append("proposal workspace active_git_operation must be null")
    for forbidden in (
        "selection_authority",
        "selection_approval_event_id",
        "action_authorization_id",
    ):
        if forbidden in workspace:
            issues.append(f"proposal workspace must not claim {forbidden}")
    return sorted(set(issues))


def _validate_proposal_status(
    manifest: dict[str, Any],
    traceability: dict[str, Any],
    status: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    status_schema = (
        "implementation-program-status/v3"
        if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
        else "implementation-program-status/v2"
    )
    expected_values = {
        "schema_version": status_schema,
        "program_id": manifest.get("program_id"),
        "program_revision": manifest.get("program_revision"),
        "state_sequence": 0,
        "program_state": "awaiting-program-approval",
        "current_increment_state": "not-started",
        "approval_mode": manifest.get("approval_mode"),
    }
    for field, expected in expected_values.items():
        if status.get(field) != expected:
            issues.append(f"proposal status {field} must be {expected!r}")
    if not _is_non_empty_string(status.get("current_increment_id")):
        issues.append("proposal status current_increment_id is required")
    if status.get("source_binding") != manifest.get("source_binding"):
        issues.append("proposal status source_binding mismatch")
    program_binding = status.get("program_binding")
    manifest_program = manifest.get("program_binding")
    coverage = traceability.get("coverage_assertion")
    expected_program_binding = {
        "sha256": (
            manifest_program.get("sha256") if isinstance(manifest_program, dict) else None
        ),
        "semantic_requirements_sha256": (
            coverage.get("semantic_requirements_sha256")
            if isinstance(coverage, dict)
            else None
        ),
    }
    if program_binding != expected_program_binding:
        issues.append("proposal status program_binding mismatch")
    if isinstance(coverage, dict) and not _is_non_empty_string(
        coverage.get("approval_event_id")
    ):
        issues.append("proposal reserves a future approval_event_id")
    return sorted(set(issues))


def validate_program_authority(
    program_root: Path,
    *,
    validation_mode: str = APPROVED_VALIDATION_MODE,
    allow_incomplete: bool = False,
) -> list[str]:
    """Validate the complete current program authority binding."""
    if validation_mode not in VALIDATION_MODES:
        return [
            "validation mode must be one of "
            f"{sorted(VALIDATION_MODES)!r}; found {validation_mode!r}"
        ]
    root = Path(program_root)
    manifest, issues = load_json_object(root / MANIFEST_NAME)
    if manifest is None:
        return sorted(set(issues))
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return ["manifest logical_roles must be an object"]

    manifest_schema = manifest.get("schema_version")
    new_manifest = manifest_schema in NEW_PROGRAM_MANIFEST_SCHEMAS
    if manifest_schema != SETUP_PROGRAM_MANIFEST_SCHEMA:
        for role in sorted(SETUP_PROGRAM_ONLY_LOGICAL_ROLES & set(logical_roles)):
            issues.append(f"manifest family rejects v3-only logical role {role}")
        for field in sorted(SETUP_PROGRAM_ONLY_MANIFEST_FIELDS & set(manifest)):
            issues.append(f"manifest family rejects v3-only field {field}")
    if validation_mode == PROPOSAL_VALIDATION_MODE and not new_manifest:
        issues.append(
            "proposal validation requires implementation-program-manifest/v2 or v3"
        )
    if new_manifest:
        issues.extend(_validate_new_manifest_contract(root, manifest, logical_roles))
        if allow_incomplete:
            issues.append("allow_incomplete is a legacy preparation mode")

    resolved_roles: dict[str, Path] = {}
    required_roles = (
        SETUP_PROGRAM_LOGICAL_ROLES
        if manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA
        else NEW_PROGRAM_LOGICAL_ROLES
        if new_manifest
        else REQUIRED_LOGICAL_ROLES
    )
    for role in required_roles:
        allocated_setup_record = (
            manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA
            and validation_mode == PROPOSAL_VALIDATION_MODE
            and role == "setup_activation_decision"
        )
        path, path_issues = resolve_managed_path(
            root,
            logical_roles.get(role),
            role=f"logical role {role}",
            require_file=not allocated_setup_record,
        )
        issues.extend(path_issues)
        if path is not None:
            resolved_roles[role] = path
            if allocated_setup_record and (path.exists() or path.is_symlink()):
                issues.append("proposal setup-activation decision must be absent")
        elif (
            manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA
            and validation_mode == APPROVED_VALIDATION_MODE
            and role == "setup_activation_decision"
        ):
            issues.append("setup-activation decision record is required")
    if len(resolved_roles) != len(required_roles):
        return sorted(set(issues))

    metadata, metadata_issues = load_json_object(resolved_roles["source_metadata"])
    traceability, traceability_issues = load_json_object(resolved_roles["traceability"])
    approvals, approval_load_issues = load_json_lines(resolved_roles["approvals"])
    issues.extend(metadata_issues)
    issues.extend(traceability_issues)
    issues.extend(approval_load_issues)
    if metadata is None or traceability is None or approvals is None:
        return sorted(set(issues))
    if new_manifest:
        status_for_destinations, status_destination_issues = load_json_object(
            resolved_roles["status"]
        )
        issues.extend(status_destination_issues)
        increment_paths, _ = _resolve_storage_descriptor(
            root,
            manifest.get("increment_storage"),
            label="increment_storage",
            schema=INCREMENT_STORAGE_SCHEMA,
            filename_fields=INCREMENT_STORAGE_FILENAME_FIELDS,
        )
        closure_paths, _ = _resolve_storage_descriptor(
            root,
            manifest.get("closure_storage"),
            label="closure_storage",
            schema=CLOSURE_STORAGE_SCHEMA,
            filename_fields=CLOSURE_STORAGE_FILENAME_FIELDS,
        )
        issues.extend(
            _new_manifest_destination_collision_issues(
                root,
                manifest,
                logical_roles,
                increment_paths=increment_paths,
                closure_paths=closure_paths,
                increment_ids=_manifest_increment_ids(
                    manifest, traceability, status_for_destinations
                ),
            )
        )

    new_ledgers: dict[str, list[dict[str, Any]]] = {"approvals": approvals}
    ledger_roles = (
        SETUP_PROGRAM_LEDGER_ROLES
        if manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA
        else NEW_PROGRAM_LEDGER_ROLES
    )
    if new_manifest:
        for role in ledger_roles:
            if role == "approvals":
                continue
            records, load_issues = load_json_lines(resolved_roles[role])
            issues.extend(load_issues)
            if records is not None:
                new_ledgers[role] = records

    if manifest_schema != SETUP_PROGRAM_MANIFEST_SCHEMA:
        records_to_check = list(approvals)
        for records in new_ledgers.values():
            if records is not approvals:
                records_to_check.extend(records)
        if not new_manifest:
            for role in NEW_PROGRAM_LEDGER_ROLES:
                if role == "approvals" or role not in logical_roles:
                    continue
                path, _ = resolve_managed_path(
                    root,
                    logical_roles.get(role),
                    role=f"logical role {role}",
                )
                if path is None:
                    continue
                records, _ = load_json_lines(path)
                if records is not None:
                    records_to_check.extend(records)
        for record in records_to_check:
            schema = record.get("schema_version")
            if schema in SETUP_AUTHORITY_RECORD_SCHEMAS:
                issues.append(
                    f"manifest family rejects foreign authority schema {schema}"
                )

    source_lines, source_issues = validate_source_binding(
        manifest,
        metadata,
        traceability,
        resolved_roles["canonical_source_snapshot"],
        str(logical_roles["canonical_source_snapshot"]),
    )
    issues.extend(source_issues)
    if traceability.get("program_id") != manifest.get("program_id"):
        issues.append("traceability program_id mismatch")
    if traceability.get("program_revision") != manifest.get("program_revision"):
        issues.append("traceability program_revision mismatch")
    issues.extend(
        validate_traceability(
            traceability, source_lines, allow_incomplete=allow_incomplete
        )
    )

    program_binding = manifest.get("program_binding")
    if not isinstance(program_binding, dict):
        issues.append("manifest program_binding must be an object")
        program_binding = {}
    program_role_path = str(logical_roles["approved_program"])
    if program_binding.get("path") != program_role_path:
        issues.append("program binding path mismatch")
    actual_program_sha256 = sha256_file(resolved_roles["approved_program"])
    if program_binding.get("sha256") != actual_program_sha256:
        issues.append("program digest mismatch")
    traceability_role_path = str(logical_roles["traceability"])
    if program_binding.get("traceability_path") != traceability_role_path:
        issues.append("traceability binding path mismatch")
    if not allow_incomplete:
        actual_traceability_sha256 = sha256_file(resolved_roles["traceability"])
        if program_binding.get("traceability_sha256") != actual_traceability_sha256:
            issues.append("traceability binding digest mismatch")
        if program_binding.get("machine_complete_traceability") is not True:
            issues.append("manifest must bind machine_complete_traceability true")
    if validation_mode == APPROVED_VALIDATION_MODE and not allow_incomplete:
        if manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA:
            try:
                from program_setup import validate_setup_activation_authority

                issues.extend(validate_setup_activation_authority(root))
            except (ImportError, ValueError) as error:
                issues.append(str(error))
        else:
            issues.extend(validate_program_approval(manifest, traceability, approvals))
    if new_manifest and validation_mode == PROPOSAL_VALIDATION_MODE:
        for role in ledger_roles:
            records = new_ledgers.get(role)
            if records is not None and records:
                issues.append(f"proposal {role} ledger must be empty")
        workspace, workspace_issues = load_json_object(resolved_roles["workspace"])
        status, status_issues = load_json_object(resolved_roles["status"])
        issues.extend(workspace_issues)
        issues.extend(status_issues)
        if workspace is not None:
            issues.extend(_validate_proposal_workspace(manifest, workspace))
        if status is not None:
            issues.extend(_validate_proposal_status(manifest, traceability, status))
    if (
        manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA
        and validation_mode == APPROVED_VALIDATION_MODE
        and "setup_activation_decision" not in resolved_roles
    ):
        issues.append("setup-activation decision record is required")
    if manifest_schema == SETUP_PROGRAM_MANIFEST_SCHEMA:
        if any(
            record.get("schema_version") == "implementation-approval/v1"
            for record in approvals
        ):
            issues.append("manifest v3 rejects v1 approval records")
        if any(
            record.get("schema_version") == "implementation-increment-grant/v1"
            for record in new_ledgers.get("increment_grants", [])
        ):
            issues.append("manifest v3 rejects v1 increment grants")
        if any(
            record.get("schema_version")
            == "implementation-action-authorization/v1"
            for record in new_ledgers.get("action_authorizations", [])
        ):
            issues.append("manifest v3 rejects v1 action authorizations")
    issues.extend(_validate_prior_revision(root, traceability))
    return sorted(set(issues))


class _StreamingLineCounter:
    def __init__(self) -> None:
        self.line_count = 0
        self.pending_cr = False
        self.has_unterminated_data = False

    def update(self, chunk: bytes) -> None:
        for byte in chunk:
            if self.pending_cr:
                self.line_count += 1
                self.pending_cr = False
                self.has_unterminated_data = False
                if byte == 0x0A:
                    continue
            if byte == 0x0D:
                self.pending_cr = True
            elif byte == 0x0A:
                self.line_count += 1
                self.has_unterminated_data = False
            else:
                self.has_unterminated_data = True

    def finish(self) -> int:
        if self.pending_cr:
            self.line_count += 1
            self.pending_cr = False
            self.has_unterminated_data = False
        elif self.has_unterminated_data:
            self.line_count += 1
            self.has_unterminated_data = False
        return self.line_count


def _resolve_capture_destination(
    program_root: Path, relative_path: PurePosixPath, label: str
) -> Path:
    if not isinstance(relative_path, PurePosixPath):
        raise TypeError(f"{label} must be a PurePosixPath")
    raw_path = relative_path.as_posix()
    if relative_path.is_absolute() or any(
        part in ("", ".", "..") for part in relative_path.parts
    ):
        raise ValueError(f"{label} must stay under the program root")
    destination = program_root.joinpath(*relative_path.parts)
    if _contains_symlink(destination.parent, program_root):
        raise ValueError(f"{label} parent must not contain a symlink")
    if not destination.parent.is_dir():
        raise ValueError(f"{label} parent must already exist")
    if not destination.parent.resolve().is_relative_to(program_root.resolve()):
        raise ValueError(f"{label} escapes the program root")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"{label} already exists: {raw_path}")
    return destination


def _finalize_without_overwrite(temporary_path: Path, destination: Path) -> None:
    try:
        os.link(temporary_path, destination)
    except FileExistsError:
        raise
    except OSError as error:
        raise OSError(
            f"non-overwriting hard-link finalization failed for {destination}: {error}"
        ) from error
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _write_temporary_bytes(directory: Path, value: bytes) -> Path:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w+b", dir=directory, delete=False) as output:
            temporary_name = output.name
            output.write(value)
            output.flush()
            os.fsync(output.fileno())
        return Path(temporary_name)
    except BaseException:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass
        raise


def capture_source(
    *,
    source_path: Path,
    program_root: Path,
    snapshot_path: PurePosixPath,
    metadata_path: PurePosixPath,
    source_id: str,
    expected_sha256: str,
    access_method: str,
) -> SourceCaptureRecord:
    """Capture source bytes and metadata without overwriting either destination."""
    source = Path(source_path)
    root = Path(program_root)
    if source.is_symlink() or not source.is_file():
        raise ValueError("source_path must be a regular non-symlink file")
    if root.is_symlink() or not root.is_dir():
        raise ValueError("program_root must be a regular non-symlink directory")
    if not _is_non_empty_string(source_id):
        raise ValueError("source_id must be non-empty")
    if not _is_sha256(expected_sha256):
        raise ValueError("expected_sha256 must be a lowercase SHA-256 digest")
    if not _is_non_empty_string(access_method):
        raise ValueError("access_method must be non-empty")
    snapshot_destination = _resolve_capture_destination(root, snapshot_path, "snapshot_path")
    metadata_destination = _resolve_capture_destination(root, metadata_path, "metadata_path")
    if snapshot_destination == metadata_destination:
        raise ValueError("snapshot_path and metadata_path must differ")

    temporary_name: str | None = None
    digest = hashlib.sha256()
    byte_count = 0
    line_counter = _StreamingLineCounter()
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b", dir=snapshot_destination.parent, delete=False
        ) as output:
            temporary_name = output.name
            with source.open("rb") as input_file:
                for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
                    output.write(chunk)
                    digest.update(chunk)
                    byte_count += len(chunk)
                    line_counter.update(chunk)
            output.flush()
            os.fsync(output.fileno())
        actual_sha256 = digest.hexdigest()
        line_count = line_counter.finish()
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"source digest mismatch: expected {expected_sha256}, found {actual_sha256}"
            )
        _finalize_without_overwrite(Path(temporary_name), snapshot_destination)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass

    metadata = {
        "access_method": access_method,
        "byte_count": byte_count,
        "immutable": True,
        "line_count": line_count,
        "metadata_path": metadata_path.as_posix(),
        "schema_version": "implementation-source-metadata/v1",
        "sha256": actual_sha256,
        "snapshot_path": snapshot_path.as_posix(),
        "source_id": source_id,
    }
    metadata_bytes = (
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary_metadata = _write_temporary_bytes(
        metadata_destination.parent, metadata_bytes
    )
    _finalize_without_overwrite(temporary_metadata, metadata_destination)
    return SourceCaptureRecord(
        source_id=source_id,
        snapshot_path=snapshot_path.as_posix(),
        metadata_path=metadata_path.as_posix(),
        sha256=actual_sha256,
        byte_count=byte_count,
        line_count=line_count,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the two-command program authority CLI."""
    parser = _ArgumentParser(prog="program_authority.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture = subparsers.add_parser("capture-source")
    capture.add_argument("--source-path", required=True)
    capture.add_argument("--program-root", required=True)
    capture.add_argument("--snapshot-path", required=True)
    capture.add_argument("--metadata-path", required=True)
    capture.add_argument("--source-id", required=True)
    capture.add_argument("--expected-sha256", required=True)
    capture.add_argument("--access-method", required=True)
    validate = subparsers.add_parser("validate-program")
    validate.add_argument("program_root")
    validate.add_argument("--allow-incomplete", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run capture or validation with stable 0, 1, and 2 exit statuses."""
    parser = build_argument_parser()
    try:
        arguments = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except _UsageError as error:
        parser.print_usage()
        print(f"program_authority.py: error: {error}")
        return 2
    try:
        if arguments.command == "capture-source":
            record = capture_source(
                source_path=Path(arguments.source_path),
                program_root=Path(arguments.program_root),
                snapshot_path=PurePosixPath(arguments.snapshot_path),
                metadata_path=PurePosixPath(arguments.metadata_path),
                source_id=arguments.source_id,
                expected_sha256=arguments.expected_sha256,
                access_method=arguments.access_method,
            )
            print(json.dumps(asdict(record), sort_keys=True))
            return 0
        issues = validate_program_authority(
            Path(arguments.program_root),
            allow_incomplete=arguments.allow_incomplete,
        )
        if issues:
            for issue in issues:
                print(issue)
            return 1
        if arguments.allow_incomplete:
            print(
                "Program authority structure passed; semantic machine completeness "
                "still requires accepted approval"
            )
        else:
            print("Program authority validation passed")
        return 0
    except (OSError, TypeError, ValueError) as error:
        print(f"program authority error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
