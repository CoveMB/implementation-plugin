#!/usr/bin/env python3
"""Persist sink-derived blocked state and prompt-bound managed recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from program_activation import (
    _canonical_json_bytes,
    _canonical_json_line,
    _identifier,
    _require_fresh_program_observation,
    _replace_or_adopt_status,
    _without_owned_program_paths,
)
from program_authority import (
    NEW_PROGRAM_MANIFEST_SCHEMA,
    SETUP_PROGRAM_MANIFEST_SCHEMA,
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
)
from repository_preparation import (
    ExecutionBaseline,
    REPOSITORY_INSPECTION_SCHEMA,
    RepositoryInspection,
    execution_baseline_from_value,
    inspect_repository,
    validate_execution_workspace,
)
from state_authority import (
    ACTION_AUTHORIZATION_SCHEMA,
    RepositoryObservation,
    StateTransitionReceipt,
    atomic_append_json_line,
    atomic_replace_json,
    validate_state_authority,
)
from task_prompt import parse_exact_prompt, render_exact_prompt


BLOCKED_CONTEXT_SCHEMA = "implementation-blocked-context/v1"
BLOCK_RESOLUTION_RECORD_SCHEMA = "implementation-block-resolution/v1"
BLOCK_RESOLUTION_COMMAND_SCHEMA = "implementation-block-resolution-command/v1"
BLOCK_RESOLUTION_CANDIDATE_SCHEMA = "implementation-block-resolution-candidate/v1"
BLOCK_RESOLUTION_BINDING_SCHEMA = "implementation-block-resolution-binding/v1"


@dataclass(frozen=True)
class EvidenceBinding:
    path: str
    sha256: str


@dataclass(frozen=True)
class BlockedTransitionRequest:
    reason_code: str
    recovery_criteria: tuple[str, ...]
    evidence_bindings: tuple[EvidenceBinding, ...] = ()


@dataclass(frozen=True)
class BlockResolutionCandidate:
    prompt: str
    continuation_checkpoint_id: str
    action_authorization_id: str
    resolution_id: str
    action_record: dict[str, object]
    resolution_record: dict[str, object]
    resumed_status: dict[str, object]
    blocked_status_sha256: str


@dataclass(frozen=True)
class BlockedRecoveryInspection:
    disposition: str | None
    prior_program_state: str | None
    prior_increment_state: str | None
    completed_steps: tuple[str, ...]
    issues: tuple[str, ...]


class _UsageError(ValueError):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fresh_observation(
    root: Path, supplied: RepositoryObservation
) -> RepositoryObservation:
    fresh = inspect_repository(Path(supplied.path), supplied.base_commit).observation
    return _require_fresh_program_observation(
        root,
        supplied,
        fresh,
        "workspace observation changed before blocked transaction",
    )


def _load_manifest_status(
    root: Path,
) -> tuple[dict[str, object], dict[str, object], Path]:
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    if manifest.get("schema_version") not in {
        NEW_PROGRAM_MANIFEST_SCHEMA,
        SETUP_PROGRAM_MANIFEST_SCHEMA,
    }:
        raise ValueError("blocked recovery requires a new-model manifest")
    roles = manifest.get("logical_roles")
    if not isinstance(roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    status_path, status_path_issues = resolve_managed_path(
        root, roles.get("status"), role="logical role status"
    )
    if status_path is None:
        raise ValueError("; ".join(status_path_issues))
    status, status_issues = load_json_object(status_path)
    if status is None:
        raise ValueError("; ".join(status_issues))
    return manifest, status, status_path


def _role_path(root: Path, manifest: Mapping[str, object], role: str) -> Path:
    roles = manifest.get("logical_roles")
    if not isinstance(roles, Mapping):
        raise ValueError("manifest logical_roles must be an object")
    path, issues = resolve_managed_path(
        root, roles.get(role), role=f"logical role {role}"
    )
    if path is None:
        raise ValueError("; ".join(issues))
    return path


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("evidence path must be a relative POSIX path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"evidence path is unsafe: {value!r}")
    return value


def _execution_contract(
    root: Path,
    manifest: Mapping[str, object],
    status: Mapping[str, object],
) -> tuple[
    ExecutionBaseline,
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    baseline_binding = status.get("execution_baseline_binding")
    authority_binding = status.get("current_increment_authority_binding")
    if not isinstance(baseline_binding, dict) or not isinstance(
        authority_binding, dict
    ):
        raise ValueError("blocking requires execution baseline and current grant")
    baseline_path, baseline_path_issues = resolve_managed_path(
        root,
        baseline_binding.get("path"),
        role="blocked execution baseline",
    )
    if baseline_path is None:
        raise ValueError("; ".join(baseline_path_issues))
    if baseline_binding.get("sha256") != sha256_file(baseline_path):
        raise ValueError("execution baseline digest mismatch")
    baseline_value, baseline_issues = load_json_object(baseline_path)
    if baseline_value is None:
        raise ValueError("; ".join(baseline_issues))
    baseline = execution_baseline_from_value(baseline_value)
    storage = manifest.get("increment_storage")
    if not isinstance(storage, Mapping):
        raise ValueError("manifest increment_storage must be an object")
    plan_relative = (
        f"{storage.get('root')}/{status.get('current_increment_id')}/"
        f"{storage.get('exact_file_plan_filename')}"
    )
    plan_path, plan_issues = resolve_managed_path(
        root, plan_relative, role="blocked exact-file plan"
    )
    if plan_path is None:
        raise ValueError("; ".join(plan_issues))
    expected_plan_sha256 = status.get("approved_exact_file_plan_sha256")
    if expected_plan_sha256 != sha256_file(plan_path):
        raise ValueError("exact-file plan digest mismatch")
    workspace_path = _role_path(root, manifest, "workspace")
    return (
        baseline,
        {"path": plan_relative, "sha256": expected_plan_sha256},
        dict(baseline_binding),
        {"path": workspace_path.relative_to(root).as_posix(), "sha256": sha256_file(workspace_path)},
    )


def _validate_evidence_bindings(
    workspace: Path,
    baseline: ExecutionBaseline,
    bindings: Sequence[EvidenceBinding],
) -> tuple[dict[str, str], ...]:
    allowed = {
        *baseline.file_map.create,
        *baseline.file_map.modify,
        *baseline.file_map.preserve,
    }
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, EvidenceBinding):
            raise ValueError("evidence bindings must use EvidenceBinding")
        path = _safe_relative_path(binding.path)
        if path in seen:
            raise ValueError("blocked evidence paths must be unique")
        seen.add(path)
        if path not in allowed:
            raise ValueError(f"blocked evidence path is not plan-allocated: {path}")
        target = workspace / path
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"blocked evidence must already be a regular file: {path}")
        if not re.fullmatch(r"[0-9a-f]{64}", binding.sha256):
            raise ValueError(f"blocked evidence digest is invalid: {path}")
        if sha256_file(target) != binding.sha256:
            raise ValueError(f"blocked evidence bytes changed: {path}")
        normalized.append({"path": path, "sha256": binding.sha256})
    return tuple(normalized)


def _validate_reason_and_criteria(
    reason_code: object, recovery_criteria: object
) -> tuple[str, tuple[str, ...]]:
    if not isinstance(reason_code, str) or re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", reason_code
    ) is None:
        raise ValueError("blocked reason_code must be a lowercase hyphenated token")
    if not isinstance(recovery_criteria, (list, tuple)):
        raise ValueError("blocked recovery criteria must be an ordered collection")
    criteria = tuple(recovery_criteria)
    if (
        not criteria
        or any(
            not isinstance(item, str)
            or not item.strip()
            or item != item.strip()
            or len(item) > 500
            for item in criteria
        )
        or len(set(criteria)) != len(criteria)
    ):
        raise ValueError("blocked recovery criteria must be ordered, unique text")
    return reason_code, criteria


def _build_blocked_context(
    root: Path,
    request: BlockedTransitionRequest,
    observation: RepositoryObservation,
    manifest: Mapping[str, object],
    status: Mapping[str, object],
    status_path: Path,
) -> dict[str, object]:
    reason_code, criteria = _validate_reason_and_criteria(
        request.reason_code, request.recovery_criteria
    )
    baseline, plan_binding, baseline_binding, workspace_binding = (
        _execution_contract(root, manifest, status)
    )
    evidence = _validate_evidence_bindings(
        Path(observation.path), baseline, request.evidence_bindings
    )
    seed = {
        "schema_domain": BLOCKED_CONTEXT_SCHEMA,
        "reason_code": reason_code,
        "prior_program_state": status["program_state"],
        "prior_increment_state": status["current_increment_state"],
        "prior_status_sha256": sha256_file(status_path),
        "prior_status_sequence": status["state_sequence"],
        "current_increment_id": status["current_increment_id"],
        "exact_file_plan_binding": plan_binding,
        "execution_baseline_binding": baseline_binding,
        "current_increment_authority_binding": status[
            "current_increment_authority_binding"
        ],
        "workspace_binding": workspace_binding,
        "inherited_workspace_binding": status.get(
            "inherited_workspace_binding"
        ),
        "recovery_criteria": list(criteria),
        "evidence_bindings": list(evidence),
    }
    return {
        "schema_version": BLOCKED_CONTEXT_SCHEMA,
        "block_id": _identifier("program-block", seed),
        **{key: value for key, value in seed.items() if key != "schema_domain"},
    }


def block_current_program(
    program_root: Path,
    request: BlockedTransitionRequest,
    observation: RepositoryObservation,
) -> StateTransitionReceipt:
    """Atomically enter blocked state from implementing or reviewing only."""
    root = Path(program_root)
    manifest, status, status_path = _load_manifest_status(root)
    state = status.get("current_increment_state")
    if state == "remediating":
        raise ValueError(
            "remediating cannot enter blocked; use the typed remediation return"
        )
    if status.get("program_state") != "active" or state not in {
        "implementing",
        "reviewing",
    }:
        raise ValueError("blocking requires active implementing or reviewing state")
    normalized = _fresh_observation(root, observation)
    authority_issues = validate_state_authority(root, normalized)
    if authority_issues:
        raise ValueError("; ".join(authority_issues))
    context = _build_blocked_context(
        root, request, normalized, manifest, status, status_path
    )
    prior_sha256 = sha256_file(status_path)
    blocked = dict(status)
    blocked.pop("block_resolution_binding", None)
    blocked.update(
        state_sequence=int(status["state_sequence"]) + 1,
        program_state="blocked",
        current_increment_state="blocked",
        blocked_context=context,
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": status["state_sequence"],
            "status_sha256": prior_sha256,
        },
        transition_authority={
            "kind": "blocked-context",
            "event_id": context["block_id"],
        },
    )
    receipt = atomic_replace_json(status_path, blocked, prior_sha256)
    return StateTransitionReceipt(
        prior_sha256=receipt.prior_sha256,
        current_sha256=receipt.current_sha256,
        state_sequence=int(blocked["state_sequence"]),
        program_state="blocked",
        increment_id=str(blocked["current_increment_id"]),
        increment_state="blocked",
    )


def validate_blocked_context(
    program_root: Path,
    status: Mapping[str, object],
    observation: RepositoryObservation,
) -> tuple[str, ...]:
    """Validate one sink-authored blocked context and its live evidence."""
    root = Path(program_root)
    issues: list[str] = []
    context = status.get("blocked_context")
    expected_keys = {
        "schema_version",
        "block_id",
        "reason_code",
        "prior_program_state",
        "prior_increment_state",
        "prior_status_sha256",
        "prior_status_sequence",
        "current_increment_id",
        "exact_file_plan_binding",
        "execution_baseline_binding",
        "current_increment_authority_binding",
        "workspace_binding",
        "inherited_workspace_binding",
        "recovery_criteria",
        "evidence_bindings",
    }
    if not isinstance(context, Mapping) or set(context) != expected_keys:
        return ("blocked context shape is invalid",)
    try:
        _validate_reason_and_criteria(
            context.get("reason_code"), context.get("recovery_criteria")
        )
        manifest, manifest_issues = load_json_object(root / "manifest.json")
        if manifest is None:
            raise ValueError("; ".join(manifest_issues))
        baseline, plan_binding, baseline_binding, workspace_binding = (
            _execution_contract(root, manifest, status)
        )
        evidence = tuple(
            EvidenceBinding(path=item["path"], sha256=item["sha256"])
            for item in context["evidence_bindings"]
            if isinstance(item, dict)
        )
        validated_evidence = _validate_evidence_bindings(
            Path(observation.path), baseline, evidence
        )
        inspection = RepositoryInspection(
            schema_version=REPOSITORY_INSPECTION_SCHEMA,
            observation=observation,
            git_directory="",
            git_common_directory="",
            selected_base_is_ancestor=True,
            status_format="porcelain-v2-z",
        )
        assessment = validate_execution_workspace(
            root,
            baseline,
            inspection,
            increment_state=str(context["prior_increment_state"]),
        )
        if not assessment.valid:
            issues.extend(assessment.issues)
    except (KeyError, OSError, TypeError, ValueError) as error:
        return (str(error),)
    if status.get("program_state") != "blocked" or status.get(
        "current_increment_state"
    ) != "blocked":
        issues.append("blocked context requires both controlling states blocked")
    if context.get("schema_version") != BLOCKED_CONTEXT_SCHEMA:
        issues.append("blocked context schema is invalid")
    if context.get("prior_program_state") != "active" or context.get(
        "prior_increment_state"
    ) not in {"implementing", "reviewing"}:
        issues.append("blocked context prior states are invalid")
    if context.get("prior_status_sequence") != status.get("state_sequence", -1) - 1:
        issues.append("blocked context prior sequence is invalid")
    previous = status.get("previous_state")
    if (
        not isinstance(previous, Mapping)
        or previous.get("state_sequence")
        != context.get("prior_status_sequence")
        or previous.get("status_sha256")
        != context.get("prior_status_sha256")
        or not isinstance(context.get("prior_status_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", context["prior_status_sha256"])
        is None
    ):
        issues.append("blocked context prior-status binding differs")
    transition = status.get("transition_authority")
    if (
        not isinstance(transition, Mapping)
        or transition.get("kind") != "blocked-context"
        or transition.get("event_id") != context.get("block_id")
    ):
        issues.append("blocked context transition authority differs")
    if context.get("current_increment_id") != status.get("current_increment_id"):
        issues.append("blocked context increment differs")
    if context.get("exact_file_plan_binding") != plan_binding:
        issues.append("blocked context exact-plan binding differs")
    if context.get("execution_baseline_binding") != baseline_binding:
        issues.append("blocked context execution-baseline binding differs")
    if context.get("current_increment_authority_binding") != status.get(
        "current_increment_authority_binding"
    ):
        issues.append("blocked context current-grant binding differs")
    authority = status.get("current_increment_authority_binding")
    if isinstance(authority, Mapping):
        try:
            grants, grant_issues = load_json_lines(
                _role_path(root, manifest, "increment_grants")
            )
        except (OSError, TypeError, ValueError) as error:
            issues.append(str(error))
        else:
            issues.extend(grant_issues)
            matches = (
                []
                if grants is None
                else [
                    record
                    for record in grants
                    if record.get("grant_id") == authority.get("grant_id")
                ]
            )
            if (
                len(matches) != 1
                or _sha256_bytes(_canonical_json_line(matches[0]))
                != authority.get("grant_sha256")
            ):
                issues.append("blocked context current grant bytes differ")
    if context.get("workspace_binding") != workspace_binding:
        issues.append("blocked context workspace binding differs")
    if context.get("inherited_workspace_binding") != status.get(
        "inherited_workspace_binding"
    ):
        issues.append("blocked context inherited-workspace binding differs")
    if context.get("evidence_bindings") != list(validated_evidence):
        issues.append("blocked context evidence inventory differs")
    seed = {
        "schema_domain": BLOCKED_CONTEXT_SCHEMA,
        **{
            key: value
            for key, value in context.items()
            if key not in {"schema_version", "block_id"}
        },
    }
    if context.get("block_id") != _identifier("program-block", seed):
        issues.append("blocked context identifier differs")
    return tuple(sorted(set(issues)))


def blocked_workspace_paths(
    program_root: Path, status: Mapping[str, object]
) -> tuple[str, ...]:
    """Return plan-owned product paths only after context validation elsewhere."""
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(manifest_issues))
    baseline, _plan, _binding, _workspace = _execution_contract(
        root, manifest, status
    )
    return tuple(sorted({*baseline.file_map.create, *baseline.file_map.modify}))


def _candidate_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "block_id",
        "criterion_results",
        "evidence_bindings",
    }:
        raise ValueError("block-resolution candidate shape is invalid")
    if value.get("schema_version") != BLOCK_RESOLUTION_CANDIDATE_SCHEMA:
        raise ValueError("block-resolution candidate schema is invalid")
    return value


def build_block_resolution_candidate(
    program_root: Path,
    candidate_value: object,
    observation: RepositoryObservation,
) -> BlockResolutionCandidate:
    """Build every prompt-bound recovery byte before persistence."""
    root = Path(program_root)
    normalized = _fresh_observation(root, observation)
    _manifest, status, status_path = _load_manifest_status(root)
    context_issues = validate_blocked_context(root, status, normalized)
    if context_issues:
        raise ValueError("; ".join(context_issues))
    value = _candidate_value(candidate_value)
    context = status["blocked_context"]
    if value["block_id"] != context["block_id"]:
        raise ValueError("block-resolution candidate block_id differs")
    results = value["criterion_results"]
    evidence_bindings = value["evidence_bindings"]
    if (
        not isinstance(results, list)
        or not all(
            isinstance(item, dict)
            and set(item) == {"criterion", "satisfied"}
            and type(item["criterion"]) is str
            and type(item["satisfied"]) is bool
            for item in results
        )
        or not isinstance(evidence_bindings, list)
        or not all(
            isinstance(item, dict)
            and set(item) == {"path", "sha256"}
            and type(item["path"]) is str
            and type(item["sha256"]) is str
            for item in evidence_bindings
        )
    ):
        raise ValueError("candidate nested field types are invalid")
    expected_results = [
        {"criterion": criterion, "satisfied": True}
        for criterion in context["recovery_criteria"]
    ]
    if results != expected_results:
        raise ValueError("every recovery criterion must be satisfied exactly once")
    if evidence_bindings != context["evidence_bindings"]:
        raise ValueError("resolution evidence must equal the blocked evidence inventory")
    blocked_status_sha256 = sha256_file(status_path)
    base_seed = {
        "schema_domain": BLOCK_RESOLUTION_COMMAND_SCHEMA,
        "block_id": context["block_id"],
        "blocked_context_sha256": _sha256_bytes(
            _canonical_json_bytes(dict(context))
        ),
        "blocked_status_sha256": blocked_status_sha256,
        "blocked_status_sequence": status["state_sequence"],
        "criterion_results": results,
        "evidence_bindings": evidence_bindings,
        "prior_program_state": context["prior_program_state"],
        "prior_increment_state": context["prior_increment_state"],
    }
    base_seed_sha256 = _sha256_bytes(_canonical_json_bytes(base_seed))
    checkpoint_id = _identifier(
        "block-resolution-checkpoint", {"base_seed_sha256": base_seed_sha256}
    )
    authorization_id = _identifier(
        "block-resolution-action",
        {"base_seed_sha256": base_seed_sha256, "checkpoint_id": checkpoint_id},
    )
    command = {
        "schema_version": BLOCK_RESOLUTION_COMMAND_SCHEMA,
        "base_seed_sha256": base_seed_sha256,
        "checkpoint_id": checkpoint_id,
        "action_authorization_id": authorization_id,
        "block_id": context["block_id"],
        "blocked_status_sha256": blocked_status_sha256,
        "criterion_results": results,
        "evidence_bindings": value["evidence_bindings"],
    }
    prompt = render_exact_prompt(command)
    prompt_sha256 = _sha256_bytes(prompt.encode("utf-8"))
    source = status["source_binding"]
    program = status["program_binding"]
    is_setup_program = (
        _manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
    )
    action_record = {
        "schema_version": (
            "implementation-action-authorization/v2"
            if is_setup_program
            else ACTION_AUTHORIZATION_SCHEMA
        ),
        "authorization_id": authorization_id,
        "decision": "authorized",
        "actions": ["resume-blocked-program"],
        "scope": ["restore only the states recorded by the blocked context"],
        "constraints": ["persist resolution evidence before resumed status"],
        "excluded": [
            "create-local-commit",
            "create-draft-pull-request",
            "merge",
            "publish",
            "release",
            "deploy",
            "migrate",
            "destructive-operation",
            "modify-provider-state",
            "modify-external-state",
        ],
        "program_id": status["program_id"],
        "program_revision": status["program_revision"],
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "program_sha256": program["sha256"],
        "semantic_requirements_sha256": program[
            "semantic_requirements_sha256"
        ],
        "increment_id": status["current_increment_id"],
        "block_id": context["block_id"],
        "blocked_status_sha256": blocked_status_sha256,
        "checkpoint_id": checkpoint_id,
        "criterion_results": results,
        "evidence_bindings": value["evidence_bindings"],
        "submitted_prompt_sha256": prompt_sha256,
    }
    if is_setup_program:
        setup_binding = status.get("setup_activation_binding")
        increment_authority = status.get("current_increment_authority_binding")
        plan_binding = context.get("exact_file_plan_binding")
        baseline_binding = status.get("execution_baseline_binding")
        if (
            not isinstance(setup_binding, dict)
            or not isinstance(increment_authority, dict)
            or not isinstance(plan_binding, dict)
            or not isinstance(baseline_binding, dict)
            or not isinstance(
                setup_binding.get("setup_activation_decision_id"), str
            )
            or not setup_binding["setup_activation_decision_id"].strip()
            or not isinstance(
                setup_binding.get("setup_activation_decision_sha256"), str
            )
            or re.fullmatch(
                r"[0-9a-f]{64}",
                setup_binding["setup_activation_decision_sha256"],
            )
            is None
            or not isinstance(increment_authority.get("grant_id"), str)
            or not increment_authority["grant_id"].strip()
            or not isinstance(increment_authority.get("grant_sha256"), str)
            or re.fullmatch(
                r"[0-9a-f]{64}", increment_authority["grant_sha256"]
            )
            is None
            or not isinstance(plan_binding.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", plan_binding["sha256"])
            is None
            or not isinstance(baseline_binding.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", baseline_binding["sha256"])
            is None
        ):
            raise ValueError("v3 blocked recovery authority is incomplete")
        from program_setup import (
            source_gate_satisfaction,
            validate_setup_activation_authority,
        )

        setup_authority_issues = validate_setup_activation_authority(root)
        if setup_authority_issues:
            raise ValueError(
                "v3 blocked recovery setup activation authority is invalid: "
                + "; ".join(setup_authority_issues)
            )

        action_record.update(
            setup_activation_decision_id=setup_binding[
                "setup_activation_decision_id"
            ],
            setup_activation_decision_sha256=setup_binding[
                "setup_activation_decision_sha256"
            ],
            increment_grant_id=increment_authority["grant_id"],
            increment_grant_sha256=increment_authority["grant_sha256"],
            exact_file_plan_sha256=plan_binding["sha256"],
            execution_baseline_sha256=baseline_binding["sha256"],
            source_gate_satisfaction=source_gate_satisfaction(
                root,
                "before-action-authorization",
                f"increment:{status['current_increment_id']}",
            ),
        )
    action_sha256 = _sha256_bytes(_canonical_json_line(action_record))
    resolution_id = _identifier(
        "block-resolution",
        {
            "base_seed_sha256": base_seed_sha256,
            "checkpoint_id": checkpoint_id,
            "action_authorization_id": authorization_id,
            "action_authorization_sha256": action_sha256,
        },
    )
    resolution_record = {
        "schema_version": BLOCK_RESOLUTION_RECORD_SCHEMA,
        "resolution_id": resolution_id,
        "block_id": context["block_id"],
        "blocked_context_sha256": base_seed["blocked_context_sha256"],
        "blocked_status_sha256": blocked_status_sha256,
        "criterion_results": results,
        "evidence_bindings": value["evidence_bindings"],
        "submitted_prompt_sha256": prompt_sha256,
        "action_authorization_id": authorization_id,
        "action_authorization_sha256": action_sha256,
        "prior_program_state": "blocked",
        "prior_increment_state": "blocked",
        "restored_program_state": context["prior_program_state"],
        "restored_increment_state": context["prior_increment_state"],
    }
    resolution_sha256 = _sha256_bytes(_canonical_json_line(resolution_record))
    resumed = dict(status)
    resumed.update(
        state_sequence=int(status["state_sequence"]) + 1,
        program_state=context["prior_program_state"],
        current_increment_state=context["prior_increment_state"],
        block_resolution_binding={
            "schema_version": BLOCK_RESOLUTION_BINDING_SCHEMA,
            "block_id": context["block_id"],
            "resolution_id": resolution_id,
            "resolution_sha256": resolution_sha256,
            "action_authorization_id": authorization_id,
            "action_authorization_sha256": action_sha256,
            "submitted_prompt_sha256": prompt_sha256,
            "blocked_status_sha256": blocked_status_sha256,
            "blocked_status_sequence": status["state_sequence"],
            "restored_program_state": context["prior_program_state"],
            "restored_increment_state": context["prior_increment_state"],
        },
        previous_state={
            "schema_version": status["schema_version"],
            "state_sequence": status["state_sequence"],
            "status_sha256": blocked_status_sha256,
        },
        transition_authority={
            "kind": "action-authorization",
            "event_id": resolution_id,
            "authorization_id": authorization_id,
            "checkpoint_id": checkpoint_id,
        },
    )
    return BlockResolutionCandidate(
        prompt=prompt,
        continuation_checkpoint_id=checkpoint_id,
        action_authorization_id=authorization_id,
        resolution_id=resolution_id,
        action_record=action_record,
        resolution_record=resolution_record,
        resumed_status=resumed,
        blocked_status_sha256=blocked_status_sha256,
    )


def _candidate_from_prompt(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> BlockResolutionCandidate:
    command = parse_exact_prompt(
        submitted_prompt, BLOCK_RESOLUTION_COMMAND_SCHEMA
    )
    value = {
        "schema_version": BLOCK_RESOLUTION_CANDIDATE_SCHEMA,
        "block_id": command.get("block_id"),
        "criterion_results": command.get("criterion_results"),
        "evidence_bindings": command.get("evidence_bindings"),
    }
    candidate = build_block_resolution_candidate(
        program_root, value, observation
    )
    if candidate.prompt != submitted_prompt:
        raise ValueError("submitted block-resolution prompt is stale")
    return candidate


def render_block_resolution_prompt(
    program_root: Path,
    candidate_value: object,
    observation: RepositoryObservation,
) -> str:
    return build_block_resolution_candidate(
        program_root, candidate_value, observation
    ).prompt


def _append_or_adopt(
    path: Path,
    record: dict[str, object],
    identifier_field: str,
    label: str,
) -> bool:
    records, issues = load_json_lines(path)
    if records is None:
        raise ValueError("; ".join(issues))
    matches = [
        item
        for item in records
        if item.get(identifier_field) == record.get(identifier_field)
    ]
    if matches:
        if len(matches) != 1 or matches[0] != record:
            raise ValueError(f"blocked-recovery-required: divergent {label}")
        return True
    atomic_append_json_line(path, record, sha256_file(path))
    return False


def _after_persist(_label: str) -> None:
    """Test seam after each durable recovery step."""


def validate_block_resolution_history(
    program_root: Path,
    status: Mapping[str, object],
    observation: RepositoryObservation,
) -> tuple[str, ...]:
    root = Path(program_root)
    binding = status.get("block_resolution_binding")
    if not isinstance(binding, Mapping):
        return ()
    context = status.get("blocked_context")
    if not isinstance(context, Mapping):
        return ("resolved status requires its sink-authored blocked context",)
    try:
        manifest, manifest_issues = load_json_object(root / "manifest.json")
        if manifest is None:
            raise ValueError("; ".join(manifest_issues))
        resolutions, resolution_issues = load_json_lines(
            _role_path(root, manifest, "block_resolutions")
        )
        actions, action_issues = load_json_lines(
            _role_path(root, manifest, "action_authorizations")
        )
        if resolutions is None or actions is None:
            raise ValueError("; ".join((*resolution_issues, *action_issues)))
        resolution_matches = [
            item
            for item in resolutions
            if item.get("resolution_id") == binding.get("resolution_id")
        ]
        action_matches = [
            item
            for item in actions
            if item.get("authorization_id")
            == binding.get("action_authorization_id")
        ]
    except (KeyError, OSError, TypeError, ValueError) as error:
        return (str(error),)
    issues: list[str] = []
    if (
        binding.get("schema_version") != BLOCK_RESOLUTION_BINDING_SCHEMA
        or binding.get("block_id") != context.get("block_id")
        or binding.get("restored_program_state")
        != context.get("prior_program_state")
        or binding.get("restored_increment_state")
        != context.get("prior_increment_state")
    ):
        issues.append("block-resolution status binding is invalid")
    if len(resolution_matches) != 1:
        issues.append("status-current block resolution must exist exactly once")
    else:
        record = resolution_matches[0]
        if (
            record.get("schema_version") != BLOCK_RESOLUTION_RECORD_SCHEMA
            or _sha256_bytes(_canonical_json_line(record))
            != binding.get("resolution_sha256")
            or record.get("block_id") != binding.get("block_id")
            or record.get("action_authorization_id")
            != binding.get("action_authorization_id")
            or record.get("action_authorization_sha256")
            != binding.get("action_authorization_sha256")
            or record.get("submitted_prompt_sha256")
            != binding.get("submitted_prompt_sha256")
            or record.get("restored_program_state")
            != binding.get("restored_program_state")
            or record.get("restored_increment_state")
            != binding.get("restored_increment_state")
        ):
            issues.append("block-resolution ledger binding differs")
    if len(action_matches) != 1:
        issues.append("block-resolution action must exist exactly once")
    else:
        expected_action_schema = (
            "implementation-action-authorization/v2"
            if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA
            else ACTION_AUTHORIZATION_SCHEMA
        )
        action = action_matches[0]
        if (
            action.get("schema_version") != expected_action_schema
            or action.get("actions") != ["resume-blocked-program"]
            or _sha256_bytes(_canonical_json_line(action))
            != binding.get("action_authorization_sha256")
        ):
            issues.append("block-resolution action binding differs")
        if manifest.get("schema_version") == SETUP_PROGRAM_MANIFEST_SCHEMA:
            setup_binding = status.get("setup_activation_binding")
            increment_authority = status.get(
                "current_increment_authority_binding"
            )
            baseline_binding = status.get("execution_baseline_binding")
            plan_binding = context.get("exact_file_plan_binding")
            try:
                from program_setup import source_gate_satisfaction

                expected_gate_satisfaction = source_gate_satisfaction(
                    root,
                    "before-action-authorization",
                    f"increment:{status.get('current_increment_id')}",
                )
            except (ImportError, ValueError) as error:
                issues.append(str(error))
                expected_gate_satisfaction = None
            if (
                not isinstance(setup_binding, Mapping)
                or not isinstance(increment_authority, Mapping)
                or not isinstance(baseline_binding, Mapping)
                or not isinstance(plan_binding, Mapping)
                or action.get("setup_activation_decision_id")
                != setup_binding.get("setup_activation_decision_id")
                or action.get("setup_activation_decision_sha256")
                != setup_binding.get("setup_activation_decision_sha256")
                or action.get("increment_grant_id")
                != increment_authority.get("grant_id")
                or action.get("increment_grant_sha256")
                != increment_authority.get("grant_sha256")
                or action.get("exact_file_plan_sha256")
                != plan_binding.get("sha256")
                or action.get("execution_baseline_sha256")
                != baseline_binding.get("sha256")
                or action.get("source_gate_satisfaction")
                != expected_gate_satisfaction
            ):
                issues.append("v3 block-resolution action authority differs")
    return tuple(sorted(set(issues)))


def _completed_receipt(
    root: Path,
    status: Mapping[str, object],
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> StateTransitionReceipt | None:
    binding = status.get("block_resolution_binding")
    if not isinstance(binding, Mapping):
        return None
    if binding.get("submitted_prompt_sha256") != _sha256_bytes(
        submitted_prompt.encode("utf-8")
    ):
        raise ValueError("blocked-recovery-required: submitted prompt differs")
    issues = validate_block_resolution_history(root, status, observation)
    if issues:
        raise ValueError("; ".join(issues))
    status_path = _load_manifest_status(root)[2]
    return StateTransitionReceipt(
        prior_sha256=str(binding["blocked_status_sha256"]),
        current_sha256=sha256_file(status_path),
        state_sequence=int(status["state_sequence"]),
        program_state=str(status["program_state"]),
        increment_id=str(status["current_increment_id"]),
        increment_state=str(status["current_increment_state"]),
    )


def persist_blocked_resolution(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> StateTransitionReceipt:
    """Append/adopt action and resolution before restoring status."""
    root = Path(program_root)
    normalized = _fresh_observation(root, observation)
    manifest, status, status_path = _load_manifest_status(root)
    completed = _completed_receipt(root, status, submitted_prompt, normalized)
    if completed is not None:
        authority_issues = validate_state_authority(root, normalized)
        if authority_issues:
            raise ValueError("; ".join(authority_issues))
        return completed
    candidate = _candidate_from_prompt(root, submitted_prompt, normalized)
    action_path = _role_path(root, manifest, "action_authorizations")
    resolution_path = _role_path(root, manifest, "block_resolutions")
    _append_or_adopt(
        action_path,
        candidate.action_record,
        "authorization_id",
        "block-resolution action",
    )
    _after_persist("action-authorization")
    _append_or_adopt(
        resolution_path,
        candidate.resolution_record,
        "resolution_id",
        "block-resolution record",
    )
    _after_persist("resolution-record")
    _replace_or_adopt_status(
        status_path,
        candidate.resumed_status,
        candidate.blocked_status_sha256,
        "blocked-resolution",
    )
    _after_persist("resumed-status")
    authority_issues = validate_state_authority(
        root, _fresh_observation(root, normalized)
    )
    if authority_issues:
        raise ValueError("; ".join(authority_issues))
    return StateTransitionReceipt(
        prior_sha256=candidate.blocked_status_sha256,
        current_sha256=sha256_file(status_path),
        state_sequence=int(candidate.resumed_status["state_sequence"]),
        program_state=str(candidate.resumed_status["program_state"]),
        increment_id=str(candidate.resumed_status["current_increment_id"]),
        increment_state=str(candidate.resumed_status["current_increment_state"]),
    )


def inspect_blocked_recovery(
    program_root: Path,
    observation: RepositoryObservation,
) -> BlockedRecoveryInspection:
    """Classify exact blocked and resolution prefixes without writes."""
    root = Path(program_root)
    try:
        manifest, status, _status_path = _load_manifest_status(root)
    except (OSError, TypeError, ValueError) as error:
        return BlockedRecoveryInspection(None, None, None, (), (str(error),))
    context = status.get("blocked_context")
    if isinstance(status.get("block_resolution_binding"), Mapping):
        issues = validate_block_resolution_history(root, status, observation)
        binding = status["block_resolution_binding"]
        is_just_resumed = (
            status.get("state_sequence")
            == binding.get("blocked_status_sequence", -1) + 1
            and status.get("program_state")
            == binding.get("restored_program_state")
            and status.get("current_increment_state")
            == binding.get("restored_increment_state")
        )
        return BlockedRecoveryInspection(
            (
                "resume"
                if not issues and is_just_resumed
                else "blocked-recovery-required"
                if issues
                else None
            ),
            str(binding.get("restored_program_state")),
            str(binding.get("restored_increment_state")),
            ("resumed-status",),
            issues,
        )
    if status.get("program_state") != "blocked" or status.get(
        "current_increment_state"
    ) != "blocked":
        return BlockedRecoveryInspection(None, None, None, (), ())
    context_issues = validate_blocked_context(root, status, observation)
    if context_issues or not isinstance(context, Mapping):
        return BlockedRecoveryInspection(
            "blocked-recovery-required", None, None, (), context_issues
        )
    actions, action_issues = load_json_lines(
        _role_path(root, manifest, "action_authorizations")
    )
    resolutions, resolution_issues = load_json_lines(
        _role_path(root, manifest, "block_resolutions")
    )
    if actions is None or resolutions is None:
        return BlockedRecoveryInspection(
            "blocked-recovery-required",
            str(context["prior_program_state"]),
            str(context["prior_increment_state"]),
            (),
            tuple((*action_issues, *resolution_issues)),
        )
    matching_actions = [
        record
        for record in actions
        if record.get("actions") == ["resume-blocked-program"]
        and record.get("block_id") == context.get("block_id")
    ]
    matching_resolutions = [
        record
        for record in resolutions
        if record.get("block_id") == context.get("block_id")
    ]
    if not matching_actions and not matching_resolutions:
        return BlockedRecoveryInspection(
            "blocked-recovery-ready",
            str(context["prior_program_state"]),
            str(context["prior_increment_state"]),
            (),
            (),
        )
    if len(matching_actions) != 1:
        return BlockedRecoveryInspection(
            "blocked-recovery-required", None, None, (), ("ambiguous resolution action",)
        )
    action = matching_actions[0]
    candidate_value = {
        "schema_version": BLOCK_RESOLUTION_CANDIDATE_SCHEMA,
        "block_id": context["block_id"],
        "criterion_results": action.get("criterion_results"),
        "evidence_bindings": action.get("evidence_bindings"),
    }
    try:
        candidate = build_block_resolution_candidate(
            root, candidate_value, observation
        )
    except (KeyError, OSError, TypeError, ValueError) as error:
        return BlockedRecoveryInspection(
            "blocked-recovery-required", None, None, (), (str(error),)
        )
    if action != candidate.action_record:
        return BlockedRecoveryInspection(
            "blocked-recovery-required", None, None, (), ("divergent resolution action",)
        )
    steps = ["action-authorization"]
    if matching_resolutions:
        if (
            len(matching_resolutions) != 1
            or matching_resolutions[0] != candidate.resolution_record
        ):
            return BlockedRecoveryInspection(
                "blocked-recovery-required", None, None, tuple(steps), ("divergent resolution record",)
            )
        steps.append("resolution-record")
    return BlockedRecoveryInspection(
        "blocked-resolution-retry-ready",
        str(context["prior_program_state"]),
        str(context["prior_increment_state"]),
        tuple(steps),
        (),
    )


def _selected_observation(root: Path) -> RepositoryObservation:
    manifest, _status, _status_path = _load_manifest_status(root)
    workspace_path = _role_path(root, manifest, "workspace")
    workspace, issues = load_json_object(workspace_path)
    if workspace is None:
        raise ValueError("; ".join(issues))
    selected = workspace.get("implementation_workspace")
    if not isinstance(selected, Mapping):
        raise ValueError("workspace selection is incomplete")
    return _without_owned_program_paths(
        root,
        inspect_repository(
            Path(str(selected["path"])), str(selected["base_commit"])
        ).observation,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="blocked_recovery.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("program_root")
    render_parser.add_argument("--candidate-file", required=True)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("program_root")
    apply_parser.add_argument("--prompt-file", required=True)
    apply_parser.add_argument("--repository", required=True)
    apply_parser.add_argument("--base-commit", required=True)
    return parser


def _regular_file(path_value: str, label: str) -> Path:
    path = Path(path_value)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular non-symlink file")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = build_argument_parser().parse_args(
            list(sys.argv[1:] if argv is None else argv)
        )
        root = Path(arguments.program_root)
        if arguments.command == "render":
            candidate_path = _regular_file(
                arguments.candidate_file, "candidate file"
            )
            value = json.loads(candidate_path.read_text(encoding="utf-8"))
            prompt = render_block_resolution_prompt(
                root, value, _selected_observation(root)
            )
            sys.stdout.write(prompt)
            return 0
        prompt_path = _regular_file(arguments.prompt_file, "prompt file")
        observation = inspect_repository(
            Path(arguments.repository), arguments.base_commit
        ).observation
        receipt = persist_blocked_resolution(
            root, prompt_path.read_text(encoding="utf-8"), observation
        )
    except (
        _UsageError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 2 if isinstance(error, _UsageError) else 1
    print(json.dumps(asdict(receipt), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
