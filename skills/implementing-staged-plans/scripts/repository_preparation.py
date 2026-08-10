#!/usr/bin/env python3
"""Inspect repository truth and validate implementation preparation artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

from program_authority import (
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
)
from state_authority import (
    ActionBinding,
    RepositoryObservation,
    decide_action_authorization,
    validate_state_authority,
)


REPOSITORY_INSPECTION_SCHEMA = "implementation-repository-inspection/v1"
EVIDENCE_RECORD_SCHEMA = "implementation-evidence-record/v1"

DRIFT_CATEGORIES = frozenset(
    {"benign", "reconcilable-relevant", "base-invalidating"}
)
MATERIAL_EVIDENCE_PREDICATES = frozenset(
    {
        "dependency-or-runtime-change",
        "provider-or-integration-change",
        "version-sensitive-api",
        "authentication-or-authorization",
        "security-or-privacy",
        "payments",
        "persistence-or-migration",
        "deployment-or-provider-state",
        "compatibility-or-security-assumption",
        "externally-defined-public-contract",
    }
)
PROGRAM_AMENDMENT_DIMENSIONS = frozenset(
    {
        "requirement",
        "acceptance-criterion",
        "scope",
        "user-visible-behavior",
        "security-or-privacy-obligation",
        "protected-contract",
        "data-ownership",
        "irreversible-behavior",
        "risk-posture",
        "dependency-sequence",
        "material-sequencing",
        "user-review-cadence",
    }
)
SURFACE_KINDS = frozenset(
    {
        "path",
        "symbol",
        "command",
        "test-or-fixture",
        "heading",
        "schema-or-identifier",
        "generated-path",
    }
)
REQUIRED_PLAN_SECTIONS = (
    "Global constraints",
    "Requirements and acceptance binding",
    "File map",
    "Semantic naming inventory",
    "Test-first slices and verification contracts",
    "Commands and expected evidence",
    "Review scopes and specialist predicates",
    "Commit boundaries",
    "Rollback and recovery",
    "Approval required to execute",
)

_OPERATION_MARKERS = {
    "BISECT_LOG": "bisect",
    "CHERRY_PICK_HEAD": "cherry-pick",
    "MERGE_HEAD": "merge",
    "REVERT_HEAD": "revert",
    "rebase-apply": "rebase",
    "rebase-merge": "rebase",
    "sequencer": "sequencer",
}
_PLANNING_COORDINATE = re.compile(
    r"(?:^|[^a-z0-9])(?:phase|part|task|step|milestone|wave|sprint|priority|ticket)"
    r"[-_ .:/]*(?:\d+|[a-z]+-?\d+)(?:$|[^a-z0-9])",
    re.IGNORECASE,
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_RISK_LEVELS = frozenset({"low", "medium", "high", "critical"})
_ALLOWED_AMENDMENT_CLASSIFICATIONS = frozenset(
    {"minor-correction", "bounded-implementation-amendment", "program-amendment"}
)
_EXISTING_COMPATIBILITY_CLASSES = frozenset(
    {"public", "persisted", "generated", "external"}
)


class RepositoryInspectionError(ValueError):
    """A concise, safe repository-inspection failure."""


class _UsageError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


@dataclass(frozen=True)
class RepositoryInspection:
    schema_version: str
    observation: RepositoryObservation
    git_directory: str
    git_common_directory: str
    selected_base_is_ancestor: bool
    status_format: str


@dataclass(frozen=True)
class DriftContext:
    previous: RepositoryInspection
    current: RepositoryInspection
    relevant_paths: tuple[str, ...]
    protected_paths: tuple[str, ...]
    accepted_existing_paths: tuple[str, ...]
    managed_paths: tuple[str, ...]
    dependency_paths: tuple[str, ...]
    dependency_compatibility_confirmed: bool
    pre_existing_failures: tuple[str, ...]
    current_failures: tuple[str, ...]
    relevant_failures: tuple[str, ...]
    reusable_candidates: tuple[str, ...]
    selected_reuse: tuple[str, ...]
    requirements_changed: bool
    protected_contract_changed: bool
    provisional_assumption_invalidated: bool


@dataclass(frozen=True)
class DriftAssessment:
    category: str
    reasons: tuple[str, ...]
    affected_paths: tuple[str, ...]
    required_action: str


@dataclass(frozen=True)
class EvidenceRecord:
    schema_version: str
    source: str
    accessed_on: str
    version: str
    configuration: str
    claims_supported: tuple[str, ...] | list[str]
    risk_domain: str
    reuse_basis: str
    remaining_uncertainty: str


@dataclass(frozen=True)
class EvidenceContext:
    material_predicates: tuple[str, ...]
    risk_level: str
    official_evidence_available: bool
    prior_version_matches: bool
    prior_configuration_matches: bool
    prior_assumptions_match: bool
    access_failure: str | None


@dataclass(frozen=True)
class EvidenceDecision:
    disposition: str
    reasons: tuple[str, ...]
    required_record_fields: tuple[str, ...]


@dataclass(frozen=True)
class AmendmentProposal:
    proposed_classification: str
    changed_dimensions: tuple[str, ...]
    evidence: tuple[str, ...]
    obligations_preserved: bool
    user_owned_decision: bool
    reversible_or_recoverable: bool
    authoritative_contradiction: bool


@dataclass(frozen=True)
class AmendmentAssessment:
    classification: str
    reasons: tuple[str, ...]
    requires_program_revision: bool
    may_proceed_under_current_mode: bool


@dataclass(frozen=True)
class IncrementShape:
    outcomes: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    verification_contracts: tuple[str, ...]
    rollback_or_recovery: tuple[str, ...]
    risk_domains: tuple[str, ...]
    depends_on_unimplemented_safeguards: tuple[str, ...]
    leaves_repository_valid: bool


@dataclass(frozen=True)
class SemanticNameRecord:
    surface: str
    surface_kind: str
    origin: str
    context: str
    intention: str
    planning_term_basis: str
    basis_owner: str
    compatibility_class: str
    compatibility_disposition: str


@dataclass(frozen=True)
class PlanBinding:
    program_id: str
    program_revision: int
    increment_id: str
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    workspace_path: str
    workspace_branch: str
    workspace_base_commit: str
    workspace_head_commit: str
    preparation_sha256: str


def _run_git(
    workspace_path: Path,
    arguments: Sequence[str],
    *,
    timeout_seconds: float,
    allowed_returncodes: frozenset[int] = frozenset({0}),
) -> subprocess.CompletedProcess[bytes]:
    command = ["git", *arguments]
    try:
        result = subprocess.run(
            command,
            shell=False,
            cwd=workspace_path,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        raise RepositoryInspectionError(
            f"git {arguments[0]} timed out after {timeout_seconds:g} seconds"
        ) from error
    except FileNotFoundError as error:
        raise RepositoryInspectionError("git executable was not found") from error
    except OSError as error:
        raise RepositoryInspectionError(
            f"git {arguments[0]} could not start: {error.__class__.__name__}"
        ) from error
    if result.returncode not in allowed_returncodes:
        qualifier = ""
        if b"not a git repository" in result.stderr.lower():
            qualifier = ": not a Git repository"
        raise RepositoryInspectionError(
            f"git {arguments[0]} failed with exit status {result.returncode}{qualifier}"
        )
    return result


def _decode_control(value: bytes, label: str) -> str:
    try:
        return value.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise RepositoryInspectionError(f"git {label} returned invalid UTF-8 control data") from error


def _safe_repository_path(value: bytes) -> str:
    path = os.fsdecode(value)
    pure = PurePosixPath(path)
    if not path or pure.is_absolute() or ".." in pure.parts:
        raise RepositoryInspectionError(f"porcelain path escapes repository: {path!r}")
    normalized = pure.as_posix()
    if normalized in {"", "."}:
        raise RepositoryInspectionError("porcelain path is empty")
    return normalized


def _add_status_path(
    path: str,
    index_status: bytes,
    worktree_status: bytes,
    staged: set[str],
    modified: set[str],
) -> None:
    if index_status != b".":
        staged.add(path)
    if worktree_status != b".":
        modified.add(path)


def _parse_porcelain_v2(
    payload: bytes, workspace_path: Path
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    del workspace_path
    staged: set[str] = set()
    modified: set[str] = set()
    untracked: set[str] = set()
    conflicted: set[str] = set()
    records = payload.split(b"\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        kind = record[:1]
        if kind == b"#":
            try:
                record.decode("utf-8")
            except UnicodeDecodeError as error:
                raise RepositoryInspectionError(
                    "porcelain header contains invalid UTF-8 control data"
                ) from error
            continue
        if kind == b"1":
            fields = record.split(b" ", 8)
            if len(fields) != 9 or len(fields[1]) != 2:
                raise RepositoryInspectionError("malformed porcelain ordinary record")
            path = _safe_repository_path(fields[8])
            _add_status_path(path, fields[1][:1], fields[1][1:], staged, modified)
            continue
        if kind == b"2":
            fields = record.split(b" ", 9)
            if len(fields) != 10 or len(fields[1]) != 2 or index >= len(records):
                raise RepositoryInspectionError("malformed porcelain rename record")
            path = _safe_repository_path(fields[9])
            original = _safe_repository_path(records[index])
            index += 1
            for candidate in (path, original):
                _add_status_path(
                    candidate, fields[1][:1], fields[1][1:], staged, modified
                )
            continue
        if kind == b"u":
            fields = record.split(b" ", 10)
            if len(fields) != 11:
                raise RepositoryInspectionError("malformed porcelain unmerged record")
            path = _safe_repository_path(fields[10])
            conflicted.add(path)
            staged.add(path)
            modified.add(path)
            continue
        if kind == b"?" and record.startswith(b"? "):
            untracked.add(_safe_repository_path(record[2:]))
            continue
        if kind == b"!" and record.startswith(b"! "):
            continue
        raise RepositoryInspectionError(
            f"unsupported porcelain v2 record kind {os.fsdecode(kind)!r}"
        )
    return tuple(sorted(staged)), tuple(sorted(modified)), tuple(sorted(untracked)), tuple(sorted(conflicted))


def _resolve_git_path(repository_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = repository_root / path
    return path.resolve(strict=False)


def inspect_repository(
    workspace_path: Path,
    selected_base_commit: str,
    *,
    timeout_seconds: float = 10.0,
) -> RepositoryInspection:
    """Collect one immutable, read-only Git observation."""
    workspace = Path(workspace_path).resolve(strict=True)
    root_result = _run_git(
        workspace, ("rev-parse", "--show-toplevel"), timeout_seconds=timeout_seconds
    )
    repository_root = Path(
        _decode_control(root_result.stdout, "rev-parse --show-toplevel")
    ).resolve(strict=True)
    git_directory = _resolve_git_path(
        repository_root,
        _decode_control(
            _run_git(
                repository_root,
                ("rev-parse", "--git-dir"),
                timeout_seconds=timeout_seconds,
            ).stdout,
            "rev-parse --git-dir",
        ),
    )
    git_common_directory = _resolve_git_path(
        repository_root,
        _decode_control(
            _run_git(
                repository_root,
                ("rev-parse", "--git-common-dir"),
                timeout_seconds=timeout_seconds,
            ).stdout,
            "rev-parse --git-common-dir",
        ),
    )
    head = _decode_control(
        _run_git(
            repository_root, ("rev-parse", "HEAD"), timeout_seconds=timeout_seconds
        ).stdout,
        "rev-parse HEAD",
    )
    branch = _decode_control(
        _run_git(
            repository_root,
            ("branch", "--show-current"),
            timeout_seconds=timeout_seconds,
        ).stdout,
        "branch --show-current",
    )
    if not branch:
        raise RepositoryInspectionError("detached HEAD is not a branch-bound workspace")
    _run_git(
        repository_root,
        ("rev-parse", "--verify", f"{selected_base_commit}^{{commit}}"),
        timeout_seconds=timeout_seconds,
    )
    status = _run_git(
        repository_root,
        ("status", "--porcelain=v2", "--branch", "-z", "--untracked-files=all"),
        timeout_seconds=timeout_seconds,
    )
    staged, modified, untracked, conflicted = _parse_porcelain_v2(
        status.stdout, repository_root
    )
    ancestry = _run_git(
        repository_root,
        ("merge-base", "--is-ancestor", selected_base_commit, head),
        timeout_seconds=timeout_seconds,
        allowed_returncodes=frozenset({0, 1}),
    ).returncode == 0
    operations: set[str] = set()
    for marker, operation in _OPERATION_MARKERS.items():
        raw = _decode_control(
            _run_git(
                repository_root,
                ("rev-parse", "--git-path", marker),
                timeout_seconds=timeout_seconds,
            ).stdout,
            f"rev-parse --git-path {marker}",
        )
        if _resolve_git_path(repository_root, raw).exists():
            operations.add(operation)
    active_operation = "+".join(sorted(operations)) or None
    return RepositoryInspection(
        schema_version=REPOSITORY_INSPECTION_SCHEMA,
        observation=RepositoryObservation(
            repository=str(repository_root),
            path=str(repository_root),
            branch=branch,
            base_commit=selected_base_commit,
            head_commit=head,
            staged_paths=staged,
            modified_paths=modified,
            untracked_paths=untracked,
            conflicted_paths=conflicted,
            active_git_operation=active_operation,
        ),
        git_directory=str(git_directory),
        git_common_directory=str(git_common_directory),
        selected_base_is_ancestor=ancestry,
        status_format="porcelain-v2-z",
    )


def _dirty_paths(observation: RepositoryObservation) -> set[str]:
    return set(
        (
            *observation.staged_paths,
            *observation.modified_paths,
            *observation.untracked_paths,
            *observation.conflicted_paths,
        )
    )


def classify_repository_drift(context: DriftContext) -> DriftAssessment:
    """Classify repository movement with fail-closed qualitative precedence."""
    previous = context.previous
    current = context.current
    previous_observation = previous.observation
    current_observation = current.observation
    dirty = _dirty_paths(current_observation)
    affected = set(dirty)
    invalidating: list[str] = []
    reconcilable: list[str] = []

    for label, old, new in (
        ("repository binding", previous_observation.repository, current_observation.repository),
        ("workspace path binding", previous_observation.path, current_observation.path),
        ("branch binding", previous_observation.branch, current_observation.branch),
        ("base binding", previous_observation.base_commit, current_observation.base_commit),
        ("prepared head", previous_observation.head_commit, current_observation.head_commit),
    ):
        if old != new:
            invalidating.append(f"{label} changed")
    if not current.selected_base_is_ancestor:
        invalidating.append("selected base is not an ancestor of current head")
    if current_observation.conflicted_paths:
        invalidating.append("repository has conflicted paths")
    if current_observation.active_git_operation:
        invalidating.append(
            f"repository has active Git operation {current_observation.active_git_operation}"
        )
    protected_overlap = dirty.intersection(context.protected_paths)
    if protected_overlap:
        affected.update(protected_overlap)
        invalidating.append("dirty work overlaps protected paths")
    if context.requirements_changed:
        invalidating.append("requirements changed")
    if context.protected_contract_changed:
        invalidating.append("protected contract changed")

    changed_dependencies = dirty.intersection(context.dependency_paths)
    if changed_dependencies and not context.dependency_compatibility_confirmed:
        affected.update(changed_dependencies)
        invalidating.append("material dependency compatibility is unverified")
    new_relevant_failures = set(context.relevant_failures).difference(
        context.pre_existing_failures
    )
    if new_relevant_failures:
        invalidating.append("new relevant verification failure")

    relevant_changes = dirty.intersection(context.relevant_paths)
    if relevant_changes:
        affected.update(relevant_changes)
        reconcilable.append("relevant repository paths changed")
    if context.provisional_assumption_invalidated:
        reconcilable.append("a provisional implementation assumption was invalidated")
    unselected_reuse = set(context.reusable_candidates).difference(context.selected_reuse)
    if unselected_reuse:
        affected.update(unselected_reuse)
        reconcilable.append("reusable repository mechanisms require a reuse decision")
    if changed_dependencies and context.dependency_compatibility_confirmed:
        reconcilable.append("compatible dependency evidence changed")

    if invalidating:
        return DriftAssessment(
            "base-invalidating",
            tuple(sorted(set(invalidating))),
            tuple(sorted(affected)),
            "stop and obtain a refreshed preparation or program decision",
        )
    if reconcilable:
        return DriftAssessment(
            "reconcilable-relevant",
            tuple(sorted(set(reconcilable))),
            tuple(sorted(affected)),
            "refresh applicable evidence and the exact-file plan under the current gate",
        )
    reasons = ["only unrelated or already recorded repository work is present"]
    unchanged_failures = set(context.current_failures).intersection(
        context.pre_existing_failures
    )
    if unchanged_failures:
        reasons.append("unrelated pre-existing failures remain recorded")
    return DriftAssessment(
        "benign",
        tuple(sorted(reasons)),
        tuple(sorted(affected)),
        "record the observation and continue",
    )


def validate_plan_overlap(
    proposed_paths: Sequence[str],
    current: RepositoryObservation,
    accepted_existing_paths: Sequence[str],
    explicit_dispositions: Mapping[str, str],
    *,
    managed_paths: Sequence[str] = (),
    managed_owners: Mapping[str, str] | None = None,
) -> list[str]:
    """Require ownership and dispositions for dirty or managed proposed paths."""
    issues: list[str] = []
    dirty = _dirty_paths(current)
    accepted = set(accepted_existing_paths)
    proposed = set(proposed_paths)
    dispositions = dict(explicit_dispositions)
    for path in sorted(dirty.intersection(proposed)):
        if path not in accepted:
            issues.append(f"proposed path {path!r} overlaps unaccepted dirty work")
        elif not dispositions.get(path, "").strip():
            issues.append(f"accepted dirty path {path!r} needs an explicit disposition")
    owners = dict(managed_owners or {})
    for path in sorted(proposed.intersection(managed_paths)):
        if not owners.get(path, "").strip():
            issues.append(f"managed path {path!r} needs an owning mechanism and verification command")
    return sorted(set(issues))


def decide_evidence_refresh(context: EvidenceContext) -> EvidenceDecision:
    """Choose an evidence disposition from materiality, applicability, and risk."""
    unknown = set(context.material_predicates).difference(MATERIAL_EVIDENCE_PREDICATES)
    if unknown:
        return EvidenceDecision(
            "blocked",
            (f"unknown material evidence predicate: {', '.join(sorted(unknown))}",),
            (),
        )
    if context.risk_level not in _ALLOWED_RISK_LEVELS:
        return EvidenceDecision("blocked", ("unknown risk level",), ())
    if not context.material_predicates:
        return EvidenceDecision(
            "not-material",
            ("no touched surface meets a material evidence predicate",),
            (),
        )
    required = (
        "source",
        "accessed_on",
        "version",
        "configuration",
        "claims_supported",
        "risk_domain",
        "reuse_basis",
        "remaining_uncertainty",
    )
    if context.official_evidence_available:
        return EvidenceDecision(
            "refresh-required",
            ("current official evidence is available for a material surface",),
            required,
        )
    mismatches = []
    if not context.prior_version_matches:
        mismatches.append("prior evidence version does not match")
    if not context.prior_configuration_matches:
        mismatches.append("prior evidence configuration does not match")
    if not context.prior_assumptions_match:
        mismatches.append("prior evidence assumptions do not match")
    if context.risk_level in {"high", "critical"}:
        mismatches.append("unavailable evidence blocks high-risk work")
    if not context.access_failure:
        mismatches.append("evidence access failure is not recorded")
    if mismatches:
        return EvidenceDecision("blocked", tuple(sorted(mismatches)), required)
    return EvidenceDecision(
        "reuse-with-residual-uncertainty",
        ("prior evidence exactly matches and the access failure is recorded",),
        required,
    )


def validate_evidence_record(record: EvidenceRecord) -> list[str]:
    issues: list[str] = []
    if record.schema_version != EVIDENCE_RECORD_SCHEMA:
        issues.append("unsupported evidence record schema")
    for field in (
        "source",
        "version",
        "configuration",
        "risk_domain",
        "reuse_basis",
        "remaining_uncertainty",
    ):
        if not isinstance(getattr(record, field), str) or not getattr(record, field).strip():
            issues.append(f"evidence {field} must be non-empty")
    try:
        date.fromisoformat(record.accessed_on)
    except (TypeError, ValueError):
        issues.append("evidence accessed_on must be an ISO date")
    if (
        not isinstance(record.claims_supported, (tuple, list))
        or not record.claims_supported
        or not all(isinstance(item, str) and item.strip() for item in record.claims_supported)
    ):
        issues.append("evidence claims_supported must be a non-empty string sequence")
    return sorted(set(issues))


def classify_plan_amendment(proposal: AmendmentProposal) -> AmendmentAssessment:
    reasons: list[str] = []
    if proposal.authoritative_contradiction:
        return AmendmentAssessment(
            "authoritative-contradiction",
            ("authoritative artifacts contradict the proposed plan",),
            True,
            False,
        )
    program_changes = set(proposal.changed_dimensions).intersection(
        PROGRAM_AMENDMENT_DIMENSIONS
    )
    if program_changes:
        return AmendmentAssessment(
            "program-amendment",
            (f"program dimensions changed: {', '.join(sorted(program_changes))}",),
            True,
            False,
        )
    if proposal.proposed_classification not in _ALLOWED_AMENDMENT_CLASSIFICATIONS:
        reasons.append("unknown proposed amendment classification")
    if proposal.proposed_classification == "program-amendment":
        return AmendmentAssessment(
            "program-amendment", ("caller requested a program amendment",), True, False
        )
    if not proposal.evidence:
        reasons.append("bounded amendment evidence is required")
    if not proposal.obligations_preserved:
        reasons.append("accepted obligations are not preserved")
    if proposal.user_owned_decision:
        reasons.append("an unresolved user-owned decision remains")
    if not proposal.reversible_or_recoverable:
        reasons.append("credible reversal or recovery is required")
    classification = proposal.proposed_classification
    if classification == "minor-correction":
        allowed = {"path", "helper", "helper-path", "test-convention"}
        unsupported = set(proposal.changed_dimensions).difference(allowed)
        if unsupported:
            reasons.append("minor correction changes more than path, helper, or test convention")
    return AmendmentAssessment(
        classification,
        tuple(sorted(set(reasons))) or ("bounded implementation obligations remain intact",),
        False,
        not reasons,
    )


def assess_increment_shape(shape: IncrementShape) -> list[str]:
    issues: list[str] = []
    if len(shape.outcomes) != 1 or not all(item.strip() for item in shape.outcomes):
        issues.append("increment must have one coherent outcome")
    if not shape.requirement_ids:
        issues.append("increment needs traceable requirements")
    if not shape.acceptance_criteria:
        issues.append("increment needs acceptance criteria")
    if not shape.verification_contracts:
        issues.append("increment needs meaningful verification contracts")
    if not shape.rollback_or_recovery:
        issues.append("increment needs coherent rollback or recovery")
    if len(set(shape.risk_domains)) > 1:
        issues.append("increment bundles unrelated risk domains")
    if shape.depends_on_unimplemented_safeguards:
        issues.append("increment depends on unimplemented safeguards")
    if not shape.leaves_repository_valid:
        issues.append("increment does not leave the repository valid")
    return sorted(set(issues))


def validate_semantic_naming_inventory(
    records: Sequence[SemanticNameRecord],
) -> list[str]:
    issues: list[str] = []
    counts: dict[str, int] = {}
    for record in records:
        counts[record.surface] = counts.get(record.surface, 0) + 1
        if not record.surface.strip():
            issues.append("semantic naming surface must be non-empty")
        if record.surface_kind not in SURFACE_KINDS:
            issues.append(f"semantic naming surface {record.surface!r} has unknown kind")
        if not record.context.strip():
            issues.append(f"semantic naming surface {record.surface!r} needs stable context")
        if not record.intention.strip():
            issues.append(f"semantic naming surface {record.surface!r} needs intention")
        coordinate = _PLANNING_COORDINATE.search(record.surface) is not None
        if coordinate:
            if record.planning_term_basis not in {
                "implementation-governance",
                "durable-domain",
            } or not record.basis_owner.strip() or record.basis_owner == "none":
                issues.append(
                    f"semantic naming surface {record.surface!r} is a planning coordinate without a specific governance or durable-domain basis"
                )
        elif record.planning_term_basis not in {
            "none",
            "implementation-governance",
            "durable-domain",
        }:
            issues.append(f"semantic naming surface {record.surface!r} has unknown planning-term basis")
        if record.planning_term_basis in {
            "implementation-governance",
            "durable-domain",
        } and (not record.basis_owner.strip() or record.basis_owner == "none"):
            issues.append(f"semantic naming surface {record.surface!r} needs a basis owner")
        if (
            record.origin == "existing"
            and record.compatibility_class in _EXISTING_COMPATIBILITY_CLASSES
            and not any(
                term in record.compatibility_disposition.lower()
                for term in ("migration", "alias", "version", "contract", "deprecation")
            )
        ):
            issues.append(
                f"semantic naming surface {record.surface!r} needs an explicit compatibility or migration disposition"
            )
        if not record.compatibility_disposition.strip():
            issues.append(f"semantic naming surface {record.surface!r} needs a compatibility disposition")
    for surface, count in counts.items():
        if count > 1:
            issues.append(f"semantic naming surface {surface!r} is duplicated")
    return sorted(set(issues))


def _section_body(markdown: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        markdown,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _validate_plan_naming_table(markdown: str) -> list[str]:
    body = _section_body(markdown, "Semantic naming inventory")
    rows = [line for line in body.splitlines() if line.strip().startswith("|")]
    if len(rows) < 3:
        return ["semantic naming inventory needs a parseable table and at least one record"]
    header = [cell.strip().lower() for cell in rows[0].strip().strip("|").split("|")]
    expected = {"surface", "kind", "context", "intention"}
    normalized_header = {
        cell.replace("proposed ", "").replace("stable ", "") for cell in header
    }
    if not expected.issubset(normalized_header):
        return ["semantic naming inventory table is missing required columns"]
    issues: list[str] = []
    seen: set[str] = set()
    for line in rows[2:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(header):
            issues.append("semantic naming inventory row has the wrong number of columns")
            continue
        values = dict(zip(header, cells, strict=True))
        surface = values.get("surface", values.get("proposed surface", "")).strip("`")
        context = values.get("context", values.get("stable context", ""))
        intention = values.get("intention", "")
        if not surface or not context or not intention:
            issues.append("semantic naming inventory row needs surface, context, and intention")
        if surface in seen:
            issues.append(f"semantic naming surface {surface!r} is duplicated")
        seen.add(surface)
        if _PLANNING_COORDINATE.search(surface):
            basis = values.get("planning-term basis", "")
            if not basis or basis.lower() in {"none", "n/a"}:
                issues.append(f"semantic naming surface {surface!r} lacks a planning-term basis")
    return sorted(set(issues))


def validate_exact_file_plan(
    plan_path: Path,
    binding: PlanBinding,
    inspection: RepositoryInspection,
) -> list[str]:
    issues: list[str] = []
    if (
        not isinstance(binding.program_revision, int)
        or isinstance(binding.program_revision, bool)
        or binding.program_revision < 1
    ):
        issues.append("exact-file plan program revision binding must be a positive integer")
    path = Path(plan_path)
    if path.is_symlink():
        return [f"exact-file plan {path} must not be a symlink"]
    if not path.is_file():
        return [f"exact-file plan {path} is missing"]
    try:
        markdown = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [f"exact-file plan could not be read: {error.__class__.__name__}"]
    if len(re.findall(r"^# (?!#)", markdown, flags=re.MULTILINE)) != 1:
        issues.append("exact-file plan must contain exactly one H1")
    for section in REQUIRED_PLAN_SECTIONS:
        if not _section_body(markdown, section):
            issues.append(f"exact-file plan section {section!r} is missing or empty")
    file_map = _section_body(markdown, "File map")
    for disposition in ("Create", "Modify", "Preserve"):
        match = re.search(
            rf"^### (?:Already )?{disposition}[^\n]*\n(.*?)(?=^### |\Z)",
            file_map,
            flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        if match is None or "`" not in match.group(1):
            issues.append(f"exact-file plan file map needs a non-empty {disposition.lower()} map")
    if "interface" not in file_map.lower() and "### exact preparation contracts" not in markdown.lower():
        issues.append("exact-file plan must name explicit interfaces")
    commands = _section_body(markdown, "Commands and expected evidence")
    if "`" not in commands or not re.search(r"\b(?:expected|exits?|pass|fail|evidence)\b", commands, re.IGNORECASE):
        issues.append("exact-file plan must include exact commands and expected evidence")
    issues.extend(_validate_plan_naming_table(markdown))

    observation = inspection.observation
    expected_values = {
        "program id": binding.program_id,
        "program revision": str(binding.program_revision),
        "increment id": binding.increment_id,
        "source digest": binding.source_sha256,
        "program digest": binding.program_sha256,
        "semantic digest": binding.semantic_requirements_sha256,
        "workspace path": binding.workspace_path,
        "workspace branch": binding.workspace_branch,
        "workspace base": binding.workspace_base_commit,
        "workspace head": binding.workspace_head_commit,
    }
    for label, value in expected_values.items():
        if value not in markdown:
            issues.append(f"exact-file plan {label} binding is missing or mismatched")
    for label, expected, actual in (
        ("workspace path", binding.workspace_path, observation.path),
        ("workspace branch", binding.workspace_branch, observation.branch),
        ("workspace base", binding.workspace_base_commit, observation.base_commit),
        ("workspace head", binding.workspace_head_commit, observation.head_commit),
    ):
        if expected != actual:
            issues.append(f"exact-file plan {label} is stale")
    if not inspection.selected_base_is_ancestor:
        issues.append("exact-file plan selected base is no longer an ancestor")
    if observation.active_git_operation:
        issues.append("exact-file plan cannot proceed during an active Git operation")
    if observation.conflicted_paths:
        issues.append("exact-file plan cannot proceed with conflicted paths")
    return sorted(set(issues))


def _current_plan_binding(
    program_root: Path,
    inspection: RepositoryInspection,
    preparation_path: Path,
) -> tuple[PlanBinding | None, list[str]]:
    root = Path(program_root)
    manifest, issues = load_json_object(root / "manifest.json")
    if manifest is None:
        return None, issues
    logical_roles = manifest.get("logical_roles")
    program_binding = manifest.get("program_binding")
    source_binding = manifest.get("source_binding")
    current_increment = manifest.get("current_increment")
    if not all(isinstance(value, dict) for value in (logical_roles, program_binding, source_binding, current_increment)):
        return None, ["manifest is missing current plan binding objects"]
    issues.extend(
        _validate_preparation_artifact(root, preparation_path, inspection)
    )
    traceability_path, path_issues = resolve_managed_path(
        root,
        program_binding.get("traceability_path"),
        role="program traceability",
    )
    issues.extend(path_issues)
    if traceability_path is None:
        return None, sorted(set(issues))
    traceability, traceability_issues = load_json_object(traceability_path)
    issues.extend(traceability_issues)
    if traceability is None:
        return None, sorted(set(issues))
    coverage = traceability.get("coverage_assertion")
    semantic = coverage.get("semantic_requirements_sha256") if isinstance(coverage, dict) else None
    if not isinstance(semantic, str):
        issues.append("traceability semantic requirements digest is missing")
    try:
        binding = PlanBinding(
            program_id=str(manifest["program_id"]),
            program_revision=int(manifest["program_revision"]),
            increment_id=str(current_increment["increment_id"]),
            source_sha256=str(source_binding["sha256"]),
            program_sha256=str(program_binding["sha256"]),
            semantic_requirements_sha256=str(semantic),
            workspace_path=inspection.observation.path,
            workspace_branch=inspection.observation.branch,
            workspace_base_commit=inspection.observation.base_commit,
            workspace_head_commit=inspection.observation.head_commit,
            preparation_sha256=sha256_file(preparation_path),
        )
    except (KeyError, TypeError, ValueError) as error:
        issues.append(f"manifest current plan binding is incomplete: {error}")
        return None, sorted(set(issues))
    return binding, sorted(set(issues))


def validate_preparation(
    program_root: Path, inspection: RepositoryInspection
) -> list[str]:
    """Validate current program/state authority against fresh Git inspection."""
    issues = list(validate_state_authority(Path(program_root), inspection.observation))
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    issues.extend(manifest_issues)
    if manifest is not None:
        logical_roles = manifest.get("logical_roles")
        if isinstance(logical_roles, dict):
            preparation_path, path_issues = resolve_managed_path(
                root,
                logical_roles.get("current_preparation"),
                role="logical role current_preparation",
            )
            issues.extend(path_issues)
            if preparation_path is not None:
                issues.extend(
                    _validate_preparation_artifact(root, preparation_path, inspection)
                )
        else:
            issues.append("manifest logical_roles must be an object")
    if inspection.schema_version != REPOSITORY_INSPECTION_SCHEMA:
        issues.append("unsupported repository inspection schema")
    if inspection.status_format != "porcelain-v2-z":
        issues.append("unsupported repository status format")
    if not inspection.selected_base_is_ancestor:
        issues.append("selected base is not an ancestor of current head")
    if inspection.observation.active_git_operation:
        issues.append("active Git operation blocks preparation")
    if inspection.observation.conflicted_paths:
        issues.append("conflicted paths block preparation")
    return sorted(set(issues))


def _validate_preparation_artifact(
    program_root: Path,
    preparation_path: Path,
    inspection: RepositoryInspection,
) -> list[str]:
    """Bind a caller-supplied preparation to its manifest role and status digest."""
    root = Path(program_root)
    issues: list[str] = []
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    issues.extend(manifest_issues)
    if manifest is None:
        return sorted(set(issues))
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return sorted(set([*issues, "manifest logical_roles must be an object"]))
    expected_path, expected_path_issues = resolve_managed_path(
        root,
        logical_roles.get("current_preparation"),
        role="logical role current_preparation",
    )
    status_path, status_path_issues = resolve_managed_path(
        root,
        logical_roles.get("status"),
        role="logical role status",
    )
    issues.extend(expected_path_issues)
    issues.extend(status_path_issues)
    supplied = Path(preparation_path)
    if supplied.is_symlink():
        issues.append("current preparation must not be a symlink")
    if expected_path is None or status_path is None:
        return sorted(set(issues))
    if supplied.resolve(strict=False) != expected_path.resolve(strict=False):
        issues.append("preparation path is not the manifest-owned current preparation")
    status, status_issues = load_json_object(status_path)
    issues.extend(status_issues)
    if status is None:
        return sorted(set(issues))
    binding = status.get("preparation_binding")
    if not isinstance(binding, dict):
        return sorted(set([*issues, "status preparation_binding must be an object"]))
    if binding.get("path") != logical_roles.get("current_preparation"):
        issues.append("current preparation path binding mismatch")
    if expected_path.is_file() and binding.get("sha256") != sha256_file(expected_path):
        issues.append("current preparation digest binding mismatch")
    if binding.get("head_commit") != inspection.observation.head_commit:
        issues.append("current preparation head binding mismatch")
    return sorted(set(issues))


def _validate_bound_plan_digest(program_root: Path, plan_path: Path) -> list[str]:
    root = Path(program_root)
    manifest, issues = load_json_object(root / "manifest.json")
    if manifest is None:
        return issues
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        return ["manifest logical_roles must be an object"]
    status_path, path_issues = resolve_managed_path(
        root, logical_roles.get("status"), role="logical role status"
    )
    issues.extend(path_issues)
    expected_plan_path, plan_path_issues = resolve_managed_path(
        root,
        logical_roles.get("current_exact_file_plan"),
        role="logical role current_exact_file_plan",
    )
    issues.extend(plan_path_issues)
    if status_path is None or expected_plan_path is None:
        return sorted(set(issues))
    supplied_plan = Path(plan_path)
    if supplied_plan.is_symlink():
        issues.append("current exact-file plan must not be a symlink")
    if supplied_plan.resolve(strict=False) != expected_plan_path.resolve(strict=False):
        issues.append("plan path is not the manifest-owned current exact-file plan")
    status, status_issues = load_json_object(status_path)
    issues.extend(status_issues)
    if status is None:
        return sorted(set(issues))
    actual = sha256_file(supplied_plan)
    is_v2 = status.get("schema_version") == "implementation-program-status/v2"
    if is_v2:
        if status.get("approved_exact_file_plan_sha256") != actual:
            issues.append("v2 execution requires the approved exact-file plan")
        authorization = status.get("execution_authorization")
        authorization_id = (
            authorization.get("authorization_id")
            if isinstance(authorization, dict)
            else None
        )
        authorization_scope = (
            authorization.get("scope") if isinstance(authorization, dict) else None
        )
    else:
        if actual not in {
            status.get("approved_exact_file_plan_sha256"),
            status.get("pending_exact_file_plan_sha256"),
        }:
            issues.append("current exact-file plan digest does not match persisted state")
        authorization = status.get("transition_authorization")
        authorization_id = (
            authorization.get("action_authorization_id")
            if isinstance(authorization, dict)
            else None
        )
        authorization_scope = None
    records_path, record_path_issues = resolve_managed_path(
        root,
        logical_roles.get("action_authorizations"),
        role="logical role action_authorizations",
    )
    issues.extend(record_path_issues)
    if records_path is not None:
        records, record_issues = load_json_lines(records_path)
        issues.extend(record_issues)
        if records is None:
            records = []
        source = manifest.get("source_binding")
        program = manifest.get("program_binding")
        current_increment = manifest.get("current_increment")
        status_source = status.get("source_binding")
        status_program = status.get("program_binding")
        brief = status.get("brief_binding")
        workspace = manifest.get("workspace_binding")
        expected_workspace = None
        if isinstance(workspace, dict):
            expected_workspace = {
                "path": workspace.get("path"),
                "branch": workspace.get("branch"),
                "base_commit": workspace.get("base_commit"),
                "head_commit": workspace.get("head_at_preparation"),
            }
        expected_fields = {
            "program_id": manifest.get("program_id"),
            "program_revision": manifest.get("program_revision"),
            "source_id": source.get("source_id") if isinstance(source, dict) else None,
            "source_sha256": status_source.get("sha256") if isinstance(status_source, dict) else None,
            "program_sha256": program.get("sha256") if isinstance(program, dict) else None,
            "semantic_requirements_sha256": status_program.get("semantic_requirements_sha256") if isinstance(status_program, dict) else None,
            "increment_id": current_increment.get("increment_id") if isinstance(current_increment, dict) else None,
            "brief_sha256": brief.get("sha256") if isinstance(brief, dict) else None,
            "exact_file_plan_sha256": actual,
            "approval_mode": status.get("approval_mode"),
        }
        if is_v2 and isinstance(authorization_scope, str) and expected_workspace is not None:
            binding = ActionBinding(
                action="modify-workspace",
                scope=authorization_scope,
                program_id=str(expected_fields["program_id"]),
                program_revision=int(expected_fields["program_revision"]),
                source_id=str(expected_fields["source_id"]),
                source_sha256=str(expected_fields["source_sha256"]),
                program_sha256=str(expected_fields["program_sha256"]),
                semantic_requirements_sha256=str(
                    expected_fields["semantic_requirements_sha256"]
                ),
                increment_id=str(expected_fields["increment_id"]),
                brief_sha256=str(expected_fields["brief_sha256"]),
                exact_file_plan_sha256=actual,
                approval_mode=str(expected_fields["approval_mode"]),
                workspace_path=str(expected_workspace["path"]),
                workspace_branch=str(expected_workspace["branch"]),
                workspace_base_commit=str(expected_workspace["base_commit"]),
                workspace_head_commit=str(expected_workspace["head_commit"]),
            )
            decision = decide_action_authorization(records, binding)
            if (
                not decision.authorized
                or decision.authorization_id != authorization_id
            ):
                issues.append("no exact current write authorization matches the plan digest")
        else:
            matching = []
            for record in records:
                scope = record.get("scope")
                if (
                    record.get("schema_version") == "implementation-action-authorization/v1"
                    and record.get("authorization_id") == authorization_id
                    and record.get("decision") == "authorized"
                    and isinstance(record.get("actions"), list)
                    and "modify-workspace" in record["actions"]
                    and isinstance(scope, list)
                    and scope
                    and all(isinstance(item, str) and item for item in scope)
                    and all(record.get(field) == value for field, value in expected_fields.items())
                    and record.get("workspace") == expected_workspace
                ):
                    matching.append(record)
            if len(matching) != 1:
                issues.append("no exact current write authorization matches the plan digest")
    return sorted(set(issues))


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(prog="repository_preparation.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser("inspect-repository")
    inspect.add_argument("--workspace", required=True)
    inspect.add_argument("--base", required=True)
    for name in ("validate-preparation", "validate-plan"):
        command = subparsers.add_parser(name)
        command.add_argument("program_root")
        command.add_argument("--workspace", required=True)
        command.add_argument("--base", required=True)
        if name == "validate-plan":
            command.add_argument("--preparation", required=True)
            command.add_argument("--plan", required=True)
    return parser


def _print_issues(issues: Sequence[str]) -> int:
    for issue in sorted(set(issues)):
        print(issue)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        arguments = parser.parse_args(argv)
    except _UsageError as error:
        print(parser.format_usage().strip())
        print(f"error: {error}")
        return 2
    try:
        inspection = inspect_repository(Path(arguments.workspace), arguments.base)
        if arguments.command == "inspect-repository":
            print(json.dumps(asdict(inspection), ensure_ascii=True, sort_keys=True))
            return 0
        preparation_issues = validate_preparation(
            Path(arguments.program_root), inspection
        )
        if arguments.command == "validate-preparation":
            if preparation_issues:
                return _print_issues(preparation_issues)
            print("Repository preparation validation passed")
            return 0
        preparation_path = Path(arguments.preparation).resolve(strict=False)
        plan_path = Path(arguments.plan).resolve(strict=False)
        binding, binding_issues = _current_plan_binding(
            Path(arguments.program_root), inspection, preparation_path
        )
        issues = [*preparation_issues, *binding_issues]
        if binding is not None:
            issues.extend(validate_exact_file_plan(plan_path, binding, inspection))
            issues.extend(_validate_bound_plan_digest(Path(arguments.program_root), plan_path))
        if issues:
            return _print_issues(issues)
        print("Exact-file plan validation passed")
        return 0
    except (OSError, RepositoryInspectionError, ValueError) as error:
        return _print_issues((str(error),))


if __name__ == "__main__":
    sys.exit(main())
