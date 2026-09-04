#!/usr/bin/env python3
"""Pure manifest-v3 setup, conversational adapter, and source-gate contracts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from program_authority import (
    load_json_lines,
    load_json_object,
    resolve_managed_path,
    sha256_file,
)
from state_authority import atomic_append_json_line


MANIFEST_SCHEMA_V3 = "implementation-program-manifest/v3"
STATUS_SCHEMA_V3 = "implementation-program-status/v3"
SETUP_SEMANTICS_SCHEMA = "implementation-program-setup-semantics/v1"
OPERATION_ENVELOPE_SCHEMA = "implementation-operation-envelope/v1"
SETUP_RECAP_SCHEMA = "implementation-program-setup-recap/v1"
SETUP_RECAP_CHECKPOINT_SCHEMA = "implementation-program-setup-recap-checkpoint/v1"
SETUP_DECISION_ADAPTER_SCHEMA = "setup-approval-decision/v1"
SETUP_ACTIVATION_SCHEMA = "setup-activation-decision/v1"
INCREMENT_START_INTENT_SCHEMA = "increment-start-intent/v1"
SOURCE_GATE_DEFINITION_SCHEMA = "source-gate-definition/v1"
SOURCE_GATE_RECAP_SCHEMA = "source-gate-recap/v1"
SOURCE_GATE_DECISION_ADAPTER_SCHEMA = "source-gate-decision-adapter/v1"
SOURCE_GATE_DECISION_SCHEMA = "source-gate-decision/v1"
SOURCE_GATE_SATISFACTION_SCHEMA = "source-gate-satisfaction/v1"
DIRECT_USER_PROVENANCE = "direct-user-message"
SUPPORTED_OPERATIONS = ("Create", "Modify", "Preserve")
SUPPORTED_GATE_TRIGGERS = (
    "before-program-activation",
    "before-increment-start",
    "before-action-authorization",
    "before-product-execution",
    "before-review",
    "before-diff-disposition",
    "before-program-closure",
)
SUPPORTED_GATE_RESPONSE = "unconditional-affirmative-satisfaction"


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_identity_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def value_sha256(value: object) -> str:
    return hashlib.sha256(canonical_identity_bytes(value)).hexdigest()


def _bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _identifier(domain: str, value: object) -> str:
    digest = value_sha256({"identifier_domain": domain, "value": value})
    return f"{domain.upper().replace('_', '-')}-{digest[:24]}"


def derive_identifier(domain: str, value: object) -> str:
    """Derive an identifier in the setup contract's canonical domain."""
    return _identifier(domain, value)


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_list(value: object, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (not nonempty or bool(value))
        and all(_is_text(item) for item in value)
    )


def _exact_fields(value: object, expected: Sequence[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    actual = set(value)
    wanted = set(expected)
    issues = [f"{label} missing field {field}" for field in sorted(wanted - actual)]
    issues.extend(
        f"{label} contains unsupported field {field}" for field in sorted(actual - wanted)
    )
    return issues


def _safe_relative_path(value: object) -> bool:
    if not _is_text(value) or "\\" in str(value):
        return False
    path = PurePosixPath(str(value))
    return (
        not path.is_absolute()
        and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _load_manifest(root: Path) -> dict[str, Any]:
    manifest, issues = load_json_object(Path(root) / "manifest.json")
    if manifest is None:
        raise ValueError("; ".join(issues))
    if manifest.get("schema_version") != MANIFEST_SCHEMA_V3:
        raise ValueError("program setup requires implementation-program-manifest/v3")
    return manifest


def _load_role(
    root: Path,
    manifest: Mapping[str, object],
    role: str,
    *,
    json_lines: bool = False,
    require_file: bool = True,
) -> tuple[Any, Path]:
    logical_roles = manifest.get("logical_roles")
    if not isinstance(logical_roles, dict):
        raise ValueError("manifest logical_roles must be an object")
    path, path_issues = resolve_managed_path(
        Path(root),
        logical_roles.get(role),
        role=f"logical role {role}",
        require_file=require_file,
    )
    if path is None:
        raise ValueError("; ".join(path_issues))
    if not require_file:
        return None, path
    value, value_issues = (
        load_json_lines(path) if json_lines else load_json_object(path)
    )
    if value is None:
        raise ValueError("; ".join(value_issues))
    return value, path


def setup_semantic_identity(manifest: Mapping[str, object]) -> str:
    semantics = manifest.get("setup_semantics")
    if not isinstance(semantics, dict):
        raise ValueError("manifest setup_semantics must be an object")
    return value_sha256(semantics)


def _validate_source_gates(
    manifest: Mapping[str, object],
    source_binding: Mapping[str, object],
    traceability: Mapping[str, object],
) -> list[str]:
    issues: list[str] = []
    definitions = manifest.get("source_gate_definitions")
    if not isinstance(definitions, list):
        return ["manifest source_gate_definitions must be a list"]
    if manifest.get("source_gate_definitions_sha256") != value_sha256(definitions):
        issues.append("source-gate definition digest mismatch")
    gate_ids: list[str] = []
    expected_fields = (
        "schema_version",
        "gate_id",
        "source_id",
        "source_sha256",
        "source_title",
        "source_location",
        "source_unit_bindings",
        "question",
        "protected_subject",
        "trigger",
        "response_semantics",
        "setup_reuse",
    )
    for index, definition in enumerate(definitions):
        label = f"source gate {index}"
        issues.extend(_exact_fields(definition, expected_fields, label))
        if not isinstance(definition, dict):
            continue
        if definition.get("schema_version") != SOURCE_GATE_DEFINITION_SCHEMA:
            issues.append(f"{label} schema_version mismatch")
        gate_id = definition.get("gate_id")
        if not _is_text(gate_id):
            issues.append(f"{label} gate_id is required")
        else:
            gate_ids.append(str(gate_id))
        if (
            definition.get("source_id") != source_binding.get("source_id")
            or definition.get("source_sha256") != source_binding.get("sha256")
        ):
            issues.append(f"{label} source binding mismatch")
        for field in ("source_title", "source_location", "question", "protected_subject"):
            if not _is_text(definition.get(field)):
                issues.append(f"{label} {field} is required")
        source_unit_bindings = definition.get("source_unit_bindings")
        if not isinstance(source_unit_bindings, list):
            issues.append(f"{label} source_unit_bindings must be a list")
        else:
            traceability_units = traceability.get("source_units")
            unit_by_id = {
                str(unit.get("id")): unit
                for unit in traceability_units
                if isinstance(unit, dict) and _is_text(unit.get("id"))
            } if isinstance(traceability_units, list) else {}
            bound_unit_ids: list[str] = []
            for binding_index, binding in enumerate(source_unit_bindings):
                binding_label = f"{label} source-unit binding {binding_index}"
                issues.extend(
                    _exact_fields(
                        binding,
                        ("source_unit_id", "source_text_sha256"),
                        binding_label,
                    )
                )
                if not isinstance(binding, dict):
                    continue
                source_unit_id = binding.get("source_unit_id")
                source_text_sha256 = binding.get("source_text_sha256")
                if not _is_text(source_unit_id) or not _is_sha256(
                    source_text_sha256
                ):
                    issues.append(f"{binding_label} is invalid")
                    continue
                bound_unit_ids.append(str(source_unit_id))
                source_unit = unit_by_id.get(str(source_unit_id))
                if (
                    source_unit is None
                    or source_unit.get("source_text_sha256")
                    != source_text_sha256
                ):
                    issues.append(f"{label} source-unit binding mismatch")
            if bound_unit_ids != sorted(set(bound_unit_ids)):
                issues.append(
                    f"{label} source-unit bindings must be sorted and unique"
                )
        trigger = definition.get("trigger")
        if trigger not in SUPPORTED_GATE_TRIGGERS:
            issues.append(f"unsupported source-gate trigger: {trigger}")
        if definition.get("response_semantics") != SUPPORTED_GATE_RESPONSE:
            issues.append("unsupported-source-gate-response-semantics")
        if not isinstance(definition.get("setup_reuse"), bool):
            issues.append(f"{label} setup_reuse must be Boolean")
        expected_subject = (
            f"program:{manifest.get('program_id')}"
            if trigger in {"before-program-activation", "before-program-closure"}
            else None
        )
        if expected_subject is not None and definition.get(
            "protected_subject"
        ) != expected_subject:
            issues.append(f"{label} protected subject has no owning transaction")
    if gate_ids != sorted(gate_ids):
        issues.append("source-gate definitions must sort by stable gate ID")
    if len(gate_ids) != len(set(gate_ids)):
        issues.append("duplicate source-gate ID")
    return issues


def validate_setup_semantics(program_root: Path) -> list[str]:
    root = Path(program_root)
    manifest, manifest_issues = load_json_object(root / "manifest.json")
    if manifest is None:
        return sorted(set(manifest_issues))
    issues: list[str] = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA_V3:
        return ["program setup requires implementation-program-manifest/v3"]
    semantics = manifest.get("setup_semantics")
    expected_semantic_fields = (
        "schema_version",
        "program",
        "bindings",
        "sources",
        "workspace",
        "increments",
        "approval",
        "operation_envelope",
        "protections",
        "exclusions",
        "external_boundaries",
        "material_risks",
        "first_increment_id",
    )
    issues.extend(_exact_fields(semantics, expected_semantic_fields, "setup_semantics"))
    if not isinstance(semantics, dict):
        return sorted(set(issues))
    if semantics.get("schema_version") != SETUP_SEMANTICS_SCHEMA:
        issues.append("setup_semantics schema_version mismatch")
    semantic_identity = value_sha256(semantics)
    if manifest.get("setup_semantics_sha256") != semantic_identity:
        issues.append("setup_semantics digest mismatch")

    program = semantics.get("program")
    issues.extend(
        _exact_fields(
            program,
            ("name", "program_id", "program_revision", "intended_outcome"),
            "setup program",
        )
    )
    if isinstance(program, dict):
        if program.get("program_id") != manifest.get("program_id"):
            issues.append("setup program_id mismatch")
        if program.get("program_revision") != manifest.get("program_revision"):
            issues.append("setup program_revision mismatch")
        if not _is_text(program.get("name")) or not _is_text(
            program.get("intended_outcome")
        ):
            issues.append("setup program readable name and outcome are required")

    source_binding = manifest.get("source_binding")
    program_binding = manifest.get("program_binding")
    if not isinstance(source_binding, dict) or not isinstance(program_binding, dict):
        issues.append("manifest source and program bindings are required")
        source_binding = {}
        program_binding = {}
    try:
        workspace, workspace_path = _load_role(root, manifest, "workspace")
        traceability, _ = _load_role(root, manifest, "traceability")
    except ValueError as error:
        issues.append(str(error))
        workspace = {}
        traceability = {}
        workspace_path = root / "missing-workspace"
    bindings = semantics.get("bindings")
    issues.extend(
        _exact_fields(
            bindings,
            (
                "source",
                "program",
                "workspace_sha256",
                "source_gate_definitions_sha256",
            ),
            "setup bindings",
        )
    )
    coverage = traceability.get("coverage_assertion") if isinstance(traceability, dict) else None
    expected_program_binding = {
        **program_binding,
        "semantic_requirements_sha256": (
            coverage.get("semantic_requirements_sha256")
            if isinstance(coverage, dict)
            else None
        ),
    }
    if isinstance(bindings, dict):
        if bindings.get("source") != source_binding:
            issues.append("setup source binding mismatch")
        if bindings.get("program") != expected_program_binding:
            issues.append("setup program binding mismatch")
        if workspace_path.is_file() and bindings.get("workspace_sha256") != sha256_file(
            workspace_path
        ):
            issues.append("setup workspace digest mismatch")
        if bindings.get("source_gate_definitions_sha256") != manifest.get(
            "source_gate_definitions_sha256"
        ):
            issues.append("setup source-gate binding mismatch")

    sources = semantics.get("sources")
    if not isinstance(sources, list) or not sources:
        issues.append("setup sources must be a non-empty list")
    else:
        source_ids: list[str] = []
        authoritative_source: dict[str, object] | None = None
        for index, source in enumerate(sources):
            label = f"setup source {index}"
            issues.extend(
                _exact_fields(
                    source,
                    ("source_id", "title", "location", "sha256"),
                    label,
                )
            )
            if not isinstance(source, dict):
                continue
            if not all(_is_text(source.get(field)) for field in ("source_id", "title", "location")):
                issues.append(f"{label} readable fields are required")
            if not _is_sha256(source.get("sha256")):
                issues.append(f"{label} sha256 is invalid")
            source_ids.append(str(source.get("source_id")))
            if source.get("source_id") == source_binding.get("source_id"):
                authoritative_source = source
        if source_ids.count(str(source_binding.get("source_id"))) != 1:
            issues.append("setup sources must contain the authoritative source exactly once")
        elif authoritative_source is not None and any(
            authoritative_source.get(field) != source_binding.get(field)
            for field in ("source_id", "sha256")
        ):
            issues.append("setup authoritative source binding mismatch")
        if len(source_ids) != len(set(source_ids)):
            issues.append("setup source IDs must be unique")

    semantic_workspace = semantics.get("workspace")
    issues.extend(
        _exact_fields(
            semantic_workspace,
            (
                "repository",
                "path",
                "branch",
                "base_commit",
                "head_commit",
                "protected_work",
            ),
            "setup workspace",
        )
    )
    if isinstance(semantic_workspace, dict) and isinstance(workspace, dict):
        selected = workspace.get("implementation_workspace")
        expected_workspace = {
            "repository": (
                workspace.get("repository", {}).get("identity")
                if isinstance(workspace.get("repository"), dict)
                else None
            ),
            "path": selected.get("path") if isinstance(selected, dict) else None,
            "branch": selected.get("branch") if isinstance(selected, dict) else None,
            "base_commit": selected.get("base_commit") if isinstance(selected, dict) else None,
            "head_commit": (
                selected.get("head_commit_at_selection")
                if isinstance(selected, dict)
                else None
            ),
            "protected_work": workspace.get("pre_existing_work_at_selection"),
        }
        if semantic_workspace != expected_workspace:
            issues.append("setup workspace observation mismatch")

    increments = semantics.get("increments")
    increment_ids: list[str] = []
    if not isinstance(increments, list) or not increments:
        issues.append("setup increments must be a non-empty list")
    else:
        for index, increment in enumerate(increments):
            label = f"setup increment {index}"
            issues.extend(
                _exact_fields(
                    increment,
                    (
                        "increment_id",
                        "depends_on",
                        "requirement_ids",
                        "acceptance_meaning",
                        "intended_outcome",
                        "expected_checks",
                    ),
                    label,
                )
            )
            if not isinstance(increment, dict):
                continue
            increment_id = increment.get("increment_id")
            if not _is_text(increment_id):
                issues.append(f"{label} increment_id is required")
            else:
                increment_ids.append(str(increment_id))
            for field in ("depends_on", "requirement_ids", "acceptance_meaning", "expected_checks"):
                if not _text_list(increment.get(field), nonempty=field != "depends_on"):
                    issues.append(f"{label} {field} must be a suitable string list")
            if not _is_text(increment.get("intended_outcome")):
                issues.append(f"{label} intended_outcome is required")
        if len(increment_ids) != len(set(increment_ids)):
            issues.append("setup increment IDs must be unique")
        positions = {
            increment_id: index for index, increment_id in enumerate(increment_ids)
        }
        dependency_graph_invalid = False
        for index, increment in enumerate(increments):
            dependencies = (
                increment.get("depends_on") if isinstance(increment, dict) else None
            )
            if not _text_list(dependencies):
                dependency_graph_invalid = True
                continue
            if len(dependencies) != len(set(dependencies)) or any(
                dependency not in positions or positions[dependency] >= index
                for dependency in dependencies
            ):
                dependency_graph_invalid = True
        if dependency_graph_invalid:
            issues.append("setup increment dependency graph is invalid")
    if semantics.get("first_increment_id") not in increment_ids:
        issues.append("setup first increment must be allocated")
    atomic_requirements = (
        traceability.get("atomic_requirements")
        if isinstance(traceability, dict)
        else None
    )
    if isinstance(atomic_requirements, list):
        traceability_increment_ids = {
            increment_id
            for requirement in atomic_requirements
            if isinstance(requirement, dict)
            for increment_id in requirement.get("assigned_increments", [])
            if isinstance(increment_id, str)
        }
        if set(increment_ids) != traceability_increment_ids:
            issues.append("setup increments do not cover exact traceability allocation")
        for increment in increments if isinstance(increments, list) else []:
            if not isinstance(increment, dict):
                continue
            expected_requirement_ids = [
                str(requirement.get("id"))
                for requirement in atomic_requirements
                if isinstance(requirement, dict)
                and increment.get("increment_id")
                in requirement.get("assigned_increments", [])
            ]
            if increment.get("requirement_ids") != expected_requirement_ids:
                issues.append(
                    f"setup increment {increment.get('increment_id')} requirement allocation mismatch"
                )
    for index, definition in enumerate(
        manifest.get("source_gate_definitions", [])
        if isinstance(manifest.get("source_gate_definitions"), list)
        else []
    ):
        if (
            isinstance(definition, dict)
            and definition.get("trigger")
            not in {"before-program-activation", "before-program-closure"}
            and definition.get("protected_subject")
            not in {f"increment:{increment_id}" for increment_id in increment_ids}
        ):
            issues.append(
                f"source gate {index} protected subject has no owning transaction"
            )

    approval = semantics.get("approval")
    issues.extend(
        _exact_fields(
            approval,
            ("mode", "routine_exact_plan_question", "remaining_boundaries"),
            "setup approval",
        )
    )
    if isinstance(approval, dict):
        if approval.get("mode") != manifest.get("approval_mode"):
            issues.append("setup approval mode mismatch")
        expected_routine = approval.get("mode") == "approval:standard"
        if approval.get("routine_exact_plan_question") is not expected_routine:
            issues.append("setup exact-plan question disclosure mismatch")
        if not _text_list(approval.get("remaining_boundaries"), nonempty=True):
            issues.append("setup remaining boundaries must be visible")

    envelope = semantics.get("operation_envelope")
    issues.extend(
        _exact_fields(
            envelope,
            ("schema_version", "supported_operations", "allocations"),
            "operation envelope",
        )
    )
    if isinstance(envelope, dict):
        if envelope.get("schema_version") != OPERATION_ENVELOPE_SCHEMA:
            issues.append("operation envelope schema mismatch")
        if envelope.get("supported_operations") != list(SUPPORTED_OPERATIONS):
            issues.append("operation envelope must support exactly Create/Modify/Preserve")
        allocations = envelope.get("allocations")
        if not isinstance(allocations, list) or not allocations:
            issues.append("operation envelope allocations must be non-empty")
        else:
            seen_allocations: set[tuple[str, str, str]] = set()
            for index, allocation in enumerate(allocations):
                label = f"operation allocation {index}"
                expected = (
                    "kind",
                    "path",
                    "operation",
                    "increment_ids",
                    "inclusions",
                    "exclusions",
                    "ownership",
                    "protected",
                    "user_work",
                    "file_kind",
                    "link_kind",
                    "mode",
                    "collision",
                )
                issues.extend(_exact_fields(allocation, expected, label))
                if not isinstance(allocation, dict):
                    continue
                if allocation.get("kind") not in {"exact-path", "bounded-path-class"}:
                    issues.append(f"{label} kind is unsupported")
                if not _safe_relative_path(allocation.get("path")):
                    issues.append(f"{label} path is unsafe")
                if allocation.get("operation") not in SUPPORTED_OPERATIONS:
                    issues.append(f"{label} operation is unsupported")
                allocated = allocation.get("increment_ids")
                if not _text_list(allocated, nonempty=True) or any(
                    item not in increment_ids for item in (allocated or [])
                ):
                    issues.append(f"{label} increment allocation is invalid")
                for field in ("inclusions", "exclusions"):
                    if not _text_list(allocation.get(field)):
                        issues.append(f"{label} {field} must be a string list")
                for field in ("ownership", "file_kind", "link_kind", "collision"):
                    if not _is_text(allocation.get(field)):
                        issues.append(f"{label} {field} is required")
                for field in ("protected", "user_work"):
                    if not isinstance(allocation.get(field), bool):
                        issues.append(f"{label} {field} must be Boolean")
                key = (
                    str(allocation.get("kind")),
                    str(allocation.get("path")),
                    str(allocation.get("operation")),
                )
                if key in seen_allocations:
                    issues.append("operation envelope contains duplicate allocation")
                seen_allocations.add(key)

    for field in ("protections", "exclusions", "external_boundaries", "material_risks"):
        if not _text_list(semantics.get(field)):
            issues.append(f"setup {field} must be a string list")
    issues.extend(_validate_source_gates(manifest, source_binding, traceability))
    if semantics.get("first_increment_id") in increment_ids:
        try:
            _increment_brief_binding(
                root,
                manifest,
                {"current_increment_id": semantics["first_increment_id"]},
            )
        except ValueError as error:
            issues.append(str(error))
    return sorted(set(issues))


def _presented_integrity(program_root: Path, manifest: Mapping[str, object]) -> str:
    root = Path(program_root)
    _workspace, workspace_path = _load_role(root, manifest, "workspace")
    _traceability, traceability_path = _load_role(root, manifest, "traceability")
    source_path, source_issues = resolve_managed_path(
        root,
        manifest.get("logical_roles", {}).get("canonical_source_snapshot"),
        role="logical role canonical_source_snapshot",
    )
    if source_path is None:
        raise ValueError("; ".join(source_issues))
    return value_sha256(
        {
            "manifest_sha256": sha256_file(root / "manifest.json"),
            "workspace_sha256": sha256_file(workspace_path),
            "traceability_sha256": sha256_file(traceability_path),
            "source_sha256": sha256_file(source_path),
        }
    )


def _work_summary(protected_work: Mapping[str, object]) -> str:
    labels = (
        ("staged_paths", "staged"),
        ("modified_paths", "modified"),
        ("untracked_paths", "untracked"),
        ("conflicted_paths", "conflicted"),
    )
    parts = []
    for field, label in labels:
        paths = protected_work.get(field)
        rendered_paths = (
            ", ".join(str(path) for path in paths)
            if isinstance(paths, list) and paths
            else "none"
        )
        parts.append(f"{label}: {rendered_paths}")
    operation = protected_work.get("active_git_operation") or "none"
    return ", ".join(parts) + f"; active Git operation: {operation}"


def render_setup_recap(program_root: Path) -> str:
    root = Path(program_root)
    issues = validate_setup_semantics(root)
    if issues:
        raise ValueError("; ".join(issues))
    manifest = _load_manifest(root)
    semantics = manifest["setup_semantics"]
    program = semantics["program"]
    workspace = semantics["workspace"]
    approval = semantics["approval"]
    lines = [
        f"Program: {program['name']} ({program['program_id']}, revision {program['program_revision']})",
        f"Outcome: {program['intended_outcome']}",
        "",
        "Authoritative sources:",
    ]
    for source in semantics["sources"]:
        lines.append(
            f"- {source['title']} at {source['location']} "
            f"(source ID: {source['source_id']})"
        )
    lines.extend(
        [
            "",
            f"Repository: {workspace['repository']}",
            f"Workspace: {workspace['path']} on branch {workspace['branch']}",
            f"Repository work: {_work_summary(workspace['protected_work'])}",
            "",
            "Ordered increments:",
        ]
    )
    for increment in semantics["increments"]:
        dependencies = ", ".join(increment["depends_on"]) or "none"
        lines.extend(
            [
                f"- {increment['increment_id']} (depends on: {dependencies})",
                f"  Outcome: {increment['intended_outcome']}",
                f"  Requirements: {', '.join(increment['requirement_ids'])}",
                f"  Acceptance: {'; '.join(increment['acceptance_meaning'])}",
                f"  Checks: {'; '.join(increment['expected_checks'])}",
            ]
        )
    routine = (
        "keeps the routine exact-plan approval question"
        if approval["routine_exact_plan_question"]
        else "omits only the routine exact-plan approval question"
    )
    lines.extend(
        [
            "",
            f"Approval mode: {approval['mode']} — {routine}.",
            "Remaining boundaries: " + "; ".join(approval["remaining_boundaries"]),
            "",
            "Local operation envelope:",
            "Supported operations: "
            + ", ".join(semantics["operation_envelope"]["supported_operations"])
            + ".",
        ]
    )
    for allocation in semantics["operation_envelope"]["allocations"]:
        scope_label = (
            allocation["path"]
            if allocation["kind"] == "exact-path"
            else f"bounded class under {allocation['path']}"
        )
        inclusions = "; ".join(allocation["inclusions"]) or "none"
        exclusions = "; ".join(allocation["exclusions"]) or "none"
        mode = (
            allocation["mode"]
            if allocation["mode"] is not None
            else "not applicable"
        )
        lines.append(
            f"- {allocation['operation']} {scope_label} for "
            + ", ".join(allocation["increment_ids"])
            + f"; owner: {allocation['ownership']}; file: {allocation['file_kind']}; "
            + f"link: {allocation['link_kind']}; collision: {allocation['collision']}; "
            + f"mode: {mode}; inclusions: {inclusions}; exclusions: {exclusions}; "
            + f"protected: {'yes' if allocation['protected'] else 'no'}; "
            + f"user work: {'yes' if allocation['user_work'] else 'no'}"
        )
    lines.extend(["", "Source-defined gates:"])
    definitions = manifest["source_gate_definitions"]
    if not definitions:
        lines.append("- None.")
    for gate in definitions:
        reuse = (
            " This setup approval also satisfies it."
            if gate["setup_reuse"]
            else " It requires its own answer."
        )
        lines.append(
            f"- {gate['source_title']} at {gate['source_location']}: "
            f"{gate['question']} An unconditional yes means satisfied. "
            f"Every other response writes nothing. Trigger: {gate['trigger']}; "
            f"protects {gate['protected_subject']}.{reuse}"
        )
    for heading, field in (
        ("Protections", "protections"),
        ("Exclusions", "exclusions"),
        ("External boundaries", "external_boundaries"),
        ("Material risks", "material_risks"),
    ):
        lines.extend(["", f"{heading}:"])
        lines.extend(f"- {item}" for item in semantics[field])
    lines.extend(
        [
            "",
            "Approval persists only the setup decision and any exactly reused source gate. "
            "It does not authorize product changes, Git actions, installation, or external actions.",
            f"First increment after activation: {semantics['first_increment_id']}",
            "",
            "Approve this program setup?",
        ]
    )
    return "\n".join(lines)


def setup_recap_checkpoint(
    program_root: Path, recap: str | None = None
) -> dict[str, object]:
    root = Path(program_root)
    manifest = _load_manifest(root)
    rendered = render_setup_recap(root) if recap is None else recap
    value: dict[str, object] = {
        "schema_version": SETUP_RECAP_CHECKPOINT_SCHEMA,
        "renderer_schema": SETUP_RECAP_SCHEMA,
        "renderer_version": 1,
        "semantic_decision_identity": setup_semantic_identity(manifest),
        "presented_integrity_identity": _presented_integrity(root, manifest),
        "recap_sha256": _bytes_sha256(rendered.encode("utf-8")),
    }
    value["checkpoint_id"] = _identifier("setup-recap-checkpoint", value)
    return value


def _classify_direct_answer(response: str, role: str, provenance: str) -> str:
    if role != "user" or provenance != DIRECT_USER_PROVENANCE:
        return "no-decision"
    normalized = " ".join(response.strip().lower().split())
    affirmative = {"yes", "approve", "approved", "i approve", "proceed"}
    negative = {"no", "reject", "rejected", "decline", "declined"}
    if normalized in affirmative:
        return "approved"
    if normalized in negative:
        return "rejected"
    return "no-decision"


def adapt_setup_decision(
    program_root: Path,
    response: str,
    *,
    role: str,
    provenance: str,
    checkpoint: Mapping[str, object] | None = None,
) -> dict[str, object]:
    root = Path(program_root)
    expected_checkpoint = setup_recap_checkpoint(root)
    if checkpoint is not None and dict(checkpoint) != expected_checkpoint:
        raise ValueError("stale setup recap checkpoint")
    decision = _classify_direct_answer(response, role, provenance)
    base: dict[str, object] = {
        "schema_version": SETUP_DECISION_ADAPTER_SCHEMA,
        "semantic_decision_identity": expected_checkpoint[
            "semantic_decision_identity"
        ],
        "presented_integrity_identity": expected_checkpoint[
            "presented_integrity_identity"
        ],
        "recap_checkpoint": expected_checkpoint,
        "decision": decision,
        "provenance_class": provenance,
        "conversation_role": role,
        "response_sha256": _bytes_sha256(response.encode("utf-8")),
    }
    base["adapter_id"] = _identifier("setup-approval-adapter", base)
    return base


def validate_setup_decision(
    program_root: Path, decision: Mapping[str, object]
) -> list[str]:
    issues = _exact_fields(
        decision,
        (
            "schema_version",
            "semantic_decision_identity",
            "presented_integrity_identity",
            "recap_checkpoint",
            "decision",
            "provenance_class",
            "conversation_role",
            "response_sha256",
            "adapter_id",
        ),
        "setup decision adapter",
    )
    if decision.get("schema_version") != SETUP_DECISION_ADAPTER_SCHEMA:
        issues.append("setup decision adapter schema mismatch")
    expected_checkpoint = setup_recap_checkpoint(Path(program_root))
    if decision.get("recap_checkpoint") != expected_checkpoint:
        issues.append("setup decision recap binding mismatch")
    if decision.get("semantic_decision_identity") != expected_checkpoint.get(
        "semantic_decision_identity"
    ):
        issues.append("setup decision semantic binding mismatch")
    if decision.get("presented_integrity_identity") != expected_checkpoint.get(
        "presented_integrity_identity"
    ):
        issues.append("setup decision integrity binding mismatch")
    if decision.get("decision") != "approved":
        issues.append("setup decision is not affirmative")
    if decision.get("provenance_class") != DIRECT_USER_PROVENANCE or decision.get(
        "conversation_role"
    ) != "user":
        issues.append("setup decision is not a direct current user message")
    if not _is_sha256(decision.get("response_sha256")):
        issues.append("setup decision response digest is invalid")
    base = dict(decision)
    adapter_id = base.pop("adapter_id", None)
    if adapter_id != _identifier("setup-approval-adapter", base):
        issues.append("setup decision adapter identity mismatch")
    return sorted(set(issues))


def _increment_start_handoff_text(
    manifest: Mapping[str, object], status: Mapping[str, object]
) -> str:
    return (
        "$implementing-staged-plans\n\n"
        f"Start increment {status['current_increment_id']} for program "
        f"{manifest['program_id']}. Revalidate the approved program, workspace, "
        "and repository state before making changes."
    )


def render_increment_start_handoff(program_root: Path) -> str:
    root = Path(program_root)
    manifest = _load_manifest(root)
    status, _ = _load_role(root, manifest, "status")
    if not (
        status.get("schema_version") == STATUS_SCHEMA_V3
        and status.get("program_state") == "active"
        and status.get("current_increment_state") == "awaiting-first-increment"
        and status.get("state_sequence") == 1
    ):
        raise ValueError("program is not waiting for its first increment")
    return _increment_start_handoff_text(manifest, status)


def _increment_brief_binding(
    program_root: Path,
    manifest: Mapping[str, object],
    status: Mapping[str, object],
) -> dict[str, object]:
    root = Path(program_root)
    storage = manifest.get("increment_storage")
    increment_id = status.get("current_increment_id")
    if not isinstance(storage, dict) or not _is_text(increment_id):
        raise ValueError("increment brief storage binding is incomplete")
    relative_path = (
        f"{storage.get('root')}/{increment_id}/{storage.get('brief_filename')}"
    )
    brief_path, brief_issues = resolve_managed_path(
        root,
        relative_path,
        role="status-current increment brief",
    )
    if brief_path is None:
        raise ValueError("; ".join(brief_issues))
    workspace, workspace_path = _load_role(root, manifest, "workspace")
    selected = workspace.get("implementation_workspace")
    if not isinstance(selected, dict) or not _is_text(
        selected.get("head_commit_at_selection")
    ):
        raise ValueError("increment brief workspace binding is incomplete")
    return {
        "path": brief_path.relative_to(root).as_posix(),
        "sha256": sha256_file(brief_path),
        "workspace_sha256": sha256_file(workspace_path),
        "head_commit": selected["head_commit_at_selection"],
    }


def adapt_increment_start_intent(
    program_root: Path,
    prompt: str,
    *,
    role: str,
    provenance: str,
) -> dict[str, object]:
    root = Path(program_root)
    manifest = _load_manifest(root)
    status, status_path = _load_role(root, manifest, "status")
    expected = render_increment_start_handoff(root)
    if role != "user" or provenance != DIRECT_USER_PROVENANCE:
        raise ValueError("increment start requires a direct current user message")
    if prompt != expected:
        raise ValueError("increment start handoff does not match current program state")
    base: dict[str, object] = {
        "schema_version": INCREMENT_START_INTENT_SCHEMA,
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "increment_id": status["current_increment_id"],
        "waiting_status_sha256": sha256_file(status_path),
        "waiting_status_sequence": status["state_sequence"],
        "brief_binding": _increment_brief_binding(root, manifest, status),
        "prompt_sha256": _bytes_sha256(prompt.encode("utf-8")),
        "provenance_class": provenance,
        "conversation_role": role,
    }
    base["intent_id"] = _identifier("increment-start-intent", base)
    return base


def validate_increment_start_intent(
    program_root: Path, intent: Mapping[str, object]
) -> list[str]:
    """Validate the complete current first-increment start intent contract."""
    issues = _exact_fields(
        intent,
        (
            "schema_version",
            "program_id",
            "program_revision",
            "increment_id",
            "waiting_status_sha256",
            "waiting_status_sequence",
            "brief_binding",
            "prompt_sha256",
            "provenance_class",
            "conversation_role",
            "intent_id",
        ),
        "increment start intent",
    )
    root = Path(program_root)
    try:
        manifest = _load_manifest(root)
        status, status_path = _load_role(root, manifest, "status")
    except ValueError as error:
        issues.append(str(error))
        return sorted(set(issues))
    if intent.get("schema_version") != INCREMENT_START_INTENT_SCHEMA:
        issues.append("increment start intent schema mismatch")
    base = dict(intent)
    intent_id = base.pop("intent_id", None)
    if intent_id != _identifier("increment-start-intent", base):
        issues.append("increment start intent identity mismatch")
    if (
        intent.get("program_id") != manifest.get("program_id")
        or intent.get("program_revision") != manifest.get("program_revision")
        or intent.get("increment_id") != status.get("current_increment_id")
        or intent.get("provenance_class") != DIRECT_USER_PROVENANCE
        or intent.get("conversation_role") != "user"
    ):
        issues.append("increment start intent binding mismatch")
    if status.get("current_increment_state") == "awaiting-first-increment":
        expected_waiting_sha256 = sha256_file(status_path)
    elif status.get("current_increment_state") == "preparing":
        previous = status.get("previous_state")
        expected_waiting_sha256 = (
            previous.get("status_sha256") if isinstance(previous, dict) else None
        )
    else:
        expected_waiting_sha256 = None
    if (
        intent.get("waiting_status_sha256") != expected_waiting_sha256
        or intent.get("waiting_status_sequence") != 1
    ):
        issues.append("increment start intent waiting-status binding mismatch")
    try:
        expected_brief_binding = _increment_brief_binding(root, manifest, status)
    except ValueError as error:
        issues.append(str(error))
    else:
        if intent.get("brief_binding") != expected_brief_binding:
            issues.append("increment start intent brief binding mismatch")
    expected_prompt_sha256 = _bytes_sha256(
        _increment_start_handoff_text(manifest, status).encode("utf-8")
    )
    if intent.get("prompt_sha256") != expected_prompt_sha256:
        issues.append("increment start intent prompt binding mismatch")
    return sorted(set(issues))


def _gate_definitions(manifest: Mapping[str, object]) -> list[dict[str, object]]:
    definitions = manifest.get("source_gate_definitions")
    if not isinstance(definitions, list):
        raise ValueError("manifest source_gate_definitions must be a list")
    return [dict(item) for item in definitions if isinstance(item, dict)]


def _gate_definition(
    manifest: Mapping[str, object], gate_id: str, protected_subject: str
) -> dict[str, object]:
    matches = [
        item
        for item in _gate_definitions(manifest)
        if item.get("gate_id") == gate_id
        and item.get("protected_subject") == protected_subject
    ]
    if len(matches) != 1:
        raise ValueError("source gate is not the exact manifest-owned definition")
    return matches[0]


def _gate_recap_checkpoint(
    program_root: Path,
    definition: Mapping[str, object],
    recap: str,
) -> dict[str, object]:
    manifest = _load_manifest(Path(program_root))
    base: dict[str, object] = {
        "schema_version": SOURCE_GATE_RECAP_SCHEMA,
        "gate_definition_sha256": value_sha256(definition),
        "semantic_decision_identity": setup_semantic_identity(manifest),
        "presented_integrity_identity": _presented_integrity(
            Path(program_root), manifest
        ),
        "recap_sha256": _bytes_sha256(recap.encode("utf-8")),
    }
    base["checkpoint_id"] = _identifier("source-gate-recap", base)
    return base


def render_source_gate_recap(
    program_root: Path, gate_id: str, protected_subject: str
) -> str:
    root = Path(program_root)
    issues = validate_setup_semantics(root)
    if issues:
        raise ValueError("; ".join(issues))
    manifest = _load_manifest(root)
    gate = _gate_definition(manifest, gate_id, protected_subject)
    return "\n".join(
        (
            f"Source gate from {gate['source_title']} at {gate['source_location']}",
            f"Trigger: {gate['trigger']}; protects {gate['protected_subject']}",
            str(gate["question"]),
            "An unconditional yes records this gate as satisfied. Every other response writes nothing.",
        )
    )


def adapt_source_gate_decision(
    program_root: Path,
    gate_id: str,
    protected_subject: str,
    response: str,
    *,
    role: str,
    provenance: str,
) -> dict[str, object]:
    root = Path(program_root)
    manifest = _load_manifest(root)
    definition = _gate_definition(manifest, gate_id, protected_subject)
    recap = render_source_gate_recap(root, gate_id, protected_subject)
    checkpoint = _gate_recap_checkpoint(root, definition, recap)
    classified = _classify_direct_answer(response, role, provenance)
    decision = "satisfied" if classified == "approved" else "no-decision"
    base: dict[str, object] = {
        "schema_version": SOURCE_GATE_DECISION_ADAPTER_SCHEMA,
        "gate_id": gate_id,
        "protected_subject": protected_subject,
        "gate_definition_sha256": value_sha256(definition),
        "recap_checkpoint": checkpoint,
        "decision_semantics": SUPPORTED_GATE_RESPONSE,
        "decision": decision,
        "provenance_class": provenance,
        "conversation_role": role,
        "response_sha256": _bytes_sha256(response.encode("utf-8")),
    }
    base["adapter_id"] = _identifier("source-gate-adapter", base)
    return base


def _validate_gate_adapter(
    program_root: Path, adapter: Mapping[str, object]
) -> dict[str, object]:
    root = Path(program_root)
    manifest = _load_manifest(root)
    gate_id = adapter.get("gate_id")
    protected_subject = adapter.get("protected_subject")
    if not _is_text(gate_id) or not _is_text(protected_subject):
        raise ValueError("source-gate adapter identity is incomplete")
    definition = _gate_definition(manifest, str(gate_id), str(protected_subject))
    recap = render_source_gate_recap(root, str(gate_id), str(protected_subject))
    expected_checkpoint = _gate_recap_checkpoint(root, definition, recap)
    if adapter.get("schema_version") != SOURCE_GATE_DECISION_ADAPTER_SCHEMA:
        raise ValueError("source-gate adapter schema mismatch")
    if adapter.get("decision") != "satisfied":
        raise ValueError("source-gate response writes nothing")
    if adapter.get("provenance_class") != DIRECT_USER_PROVENANCE or adapter.get(
        "conversation_role"
    ) != "user":
        raise ValueError("source gate requires a direct current user message")
    if adapter.get("decision_semantics") != SUPPORTED_GATE_RESPONSE:
        raise ValueError("unsupported-source-gate-response-semantics")
    if adapter.get("gate_definition_sha256") != value_sha256(definition):
        raise ValueError("source-gate definition binding mismatch")
    if adapter.get("recap_checkpoint") != expected_checkpoint:
        raise ValueError("stale source-gate recap checkpoint")
    base = dict(adapter)
    adapter_id = base.pop("adapter_id", None)
    if adapter_id != _identifier("source-gate-adapter", base):
        raise ValueError("source-gate adapter identity mismatch")
    return definition


def _setup_activation_record(
    program_root: Path, manifest: Mapping[str, object]
) -> tuple[dict[str, object], Path]:
    record, path = _load_role(program_root, manifest, "setup_activation_decision")
    if record.get("schema_version") != SETUP_ACTIVATION_SCHEMA or not _is_text(
        record.get("decision_id")
    ):
        raise ValueError("setup-activation decision record is invalid")
    return record, path


def persist_source_gate_decision(
    program_root: Path,
    adapter: Mapping[str, object],
    *,
    status_sha256: str,
    status_sequence: int,
    workspace_observation: Mapping[str, object],
    boundary_authority: Mapping[str, object] | None,
    exact_plan_sha256: str | None = None,
    execution_baseline_sha256: str | None = None,
) -> dict[str, object]:
    root = Path(program_root)
    manifest = _load_manifest(root)
    definition = _validate_gate_adapter(root, adapter)
    if not _is_sha256(status_sha256) or not isinstance(status_sequence, int):
        raise ValueError("source-gate status binding is invalid")
    setup_record, setup_path = _setup_activation_record(root, manifest)
    status, status_path = _load_role(root, manifest, "status")
    if status_sha256 != sha256_file(status_path) or status_sequence != status.get(
        "state_sequence"
    ):
        raise ValueError("source-gate status binding is stale")
    if not isinstance(workspace_observation, Mapping):
        raise ValueError("source-gate workspace observation is required")
    if not isinstance(boundary_authority, Mapping) or not boundary_authority:
        raise ValueError("source-gate boundary authority is required")
    trigger = definition.get("trigger")
    if trigger == "before-program-activation":
        if boundary_authority.get("setup_adapter_id") != setup_record.get(
            "setup_adapter_id"
        ):
            raise ValueError("source-gate setup boundary authority mismatch")
    elif trigger == "before-increment-start":
        if status.get("current_increment_state") == "awaiting-first-increment":
            intent_issues = validate_increment_start_intent(
                root, dict(boundary_authority)
            )
            if intent_issues:
                raise ValueError("; ".join(intent_issues))
        else:
            actions, _ = _load_role(
                root, manifest, "action_authorizations", json_lines=True
            )
            if not any(record == dict(boundary_authority) for record in actions):
                raise ValueError("source-gate rollover authority is not durable")
    elif trigger == "before-action-authorization":
        if boundary_authority != status.get("current_increment_authority_binding"):
            raise ValueError("source-gate plan boundary authority mismatch")
        if not _is_sha256(exact_plan_sha256) or not _is_sha256(
            execution_baseline_sha256
        ):
            raise ValueError("source-gate plan and baseline bindings are required")
    elif trigger in {"before-product-execution", "before-review"}:
        if boundary_authority != status.get("execution_authorization"):
            raise ValueError("source-gate execution authority mismatch")
    elif trigger == "before-diff-disposition":
        if boundary_authority != status.get("execution_transition_binding"):
            raise ValueError("source-gate review boundary authority mismatch")
    elif trigger == "before-program-closure":
        if boundary_authority != status.get("closure_binding"):
            raise ValueError("source-gate closure boundary authority mismatch")
    records, ledger_path = _load_role(
        root, manifest, "source_gate_decisions", json_lines=True
    )
    applicable = [
        item
        for item in _gate_definitions(manifest)
        if item.get("trigger") == definition.get("trigger")
        and item.get("protected_subject") == definition.get("protected_subject")
        and item.get("setup_reuse") is False
    ]
    completed_ids = [
        str(item.get("gate_id"))
        for item in records
        if item.get("trigger") == definition.get("trigger")
        and item.get("protected_subject") == definition.get("protected_subject")
    ]
    expected_ids = [str(item["gate_id"]) for item in applicable]
    if completed_ids != expected_ids[: len(completed_ids)]:
        raise ValueError("source-gate decision ledger is not an exact stable prefix")
    gate_id = str(definition["gate_id"])
    if gate_id in completed_ids:
        existing = next(item for item in records if item.get("gate_id") == gate_id)
        return {"record": existing, "recovered": True}
    if len(completed_ids) >= len(expected_ids) or expected_ids[len(completed_ids)] != gate_id:
        raise ValueError("only the next source gate may be persisted")
    record_base: dict[str, object] = {
        "schema_version": SOURCE_GATE_DECISION_SCHEMA,
        "gate_id": gate_id,
        "gate_definition_sha256": value_sha256(definition),
        "program_id": manifest["program_id"],
        "program_revision": manifest["program_revision"],
        "source_binding": manifest["source_binding"],
        "semantic_decision_identity": setup_semantic_identity(manifest),
        "setup_activation_decision_id": setup_record["decision_id"],
        "setup_activation_decision_sha256": sha256_file(setup_path),
        "status_sha256": status_sha256,
        "status_sequence": status_sequence,
        "protected_subject": definition["protected_subject"],
        "trigger": definition["trigger"],
        "workspace_observation": dict(workspace_observation),
        "gate_recap_checkpoint": adapter["recap_checkpoint"],
        "decision": "satisfied",
        "provenance_class": DIRECT_USER_PROVENANCE,
        "gate_adapter_id": adapter["adapter_id"],
        "gate_adapter_sha256": value_sha256(adapter),
        "exact_plan_sha256": exact_plan_sha256,
        "execution_baseline_sha256": execution_baseline_sha256,
        "boundary_authority": (
            dict(boundary_authority) if boundary_authority is not None else None
        ),
    }
    record_base["decision_id"] = _identifier("source-gate-decision", record_base)
    atomic_append_json_line(ledger_path, record_base, sha256_file(ledger_path))
    return {"record": record_base, "recovered": False}


def source_gate_satisfaction(
    program_root: Path,
    trigger: str,
    protected_subject: str,
    *,
    expected_boundary_authority: Mapping[str, object] | None = None,
) -> dict[str, object]:
    root = Path(program_root)
    manifest = _load_manifest(root)
    if trigger not in SUPPORTED_GATE_TRIGGERS:
        raise ValueError(f"unsupported source-gate trigger: {trigger}")
    setup_record, setup_path = _setup_activation_record(root, manifest)
    records, _ = _load_role(root, manifest, "source_gate_decisions", json_lines=True)
    applicable = [
        item
        for item in _gate_definitions(manifest)
        if item.get("trigger") == trigger
        and item.get("protected_subject") == protected_subject
    ]
    entries: list[dict[str, object]] = []
    for definition in applicable:
        gate_id = str(definition["gate_id"])
        if definition.get("setup_reuse") is True:
            adapter_id = setup_record.get("setup_adapter_id")
            adapter_sha256 = setup_record.get("setup_adapter_sha256")
            if not _is_text(adapter_id) or not _is_sha256(adapter_sha256):
                raise ValueError("setup-reused source gate lacks adapter evidence")
            evidence = {
                "adapter_id": adapter_id,
                "adapter_sha256": adapter_sha256,
            }
            kind = "existing-checkpoint"
        else:
            matches = [
                record
                for record in records
                if record.get("gate_id") == gate_id
                and record.get("trigger") == trigger
                and record.get("protected_subject") == protected_subject
                and record.get("gate_definition_sha256") == value_sha256(definition)
                and record.get("setup_activation_decision_id")
                == setup_record.get("decision_id")
                and record.get("setup_activation_decision_sha256")
                == sha256_file(setup_path)
            ]
            if len(matches) != 1:
                raise ValueError(f"source gate {gate_id} is not durably satisfied")
            decision = matches[0]
            decision_base = dict(decision)
            decision_id = decision_base.pop("decision_id", None)
            if (
                decision.get("schema_version") != SOURCE_GATE_DECISION_SCHEMA
                or decision.get("program_id") != manifest.get("program_id")
                or decision.get("program_revision")
                != manifest.get("program_revision")
                or decision.get("source_binding") != manifest.get("source_binding")
                or decision.get("semantic_decision_identity")
                != setup_semantic_identity(manifest)
                or decision.get("decision") != "satisfied"
                or decision.get("provenance_class") != DIRECT_USER_PROVENANCE
                or not _is_text(decision.get("gate_adapter_id"))
                or not _is_sha256(decision.get("gate_adapter_sha256"))
                or not isinstance(decision.get("status_sequence"), int)
                or not _is_sha256(decision.get("status_sha256"))
                or not isinstance(decision.get("workspace_observation"), dict)
                or not isinstance(decision.get("boundary_authority"), dict)
                or decision_id != _identifier("source-gate-decision", decision_base)
            ):
                raise ValueError(f"source gate {gate_id} decision binding is invalid")
            if expected_boundary_authority is not None and decision.get(
                "boundary_authority"
            ) != dict(expected_boundary_authority):
                raise ValueError(
                    f"source gate {gate_id} boundary authority mismatch"
                )
            evidence = {
                "decision_id": decision.get("decision_id"),
                "decision_sha256": value_sha256(decision),
            }
            kind = "source-gate-decision"
        entries.append(
            {
                "gate_id": gate_id,
                "trigger": trigger,
                "protected_subject": protected_subject,
                "satisfaction_kind": kind,
                "evidence": evidence,
            }
        )
    return {
        "schema_version": SOURCE_GATE_SATISFACTION_SCHEMA,
        "trigger": trigger,
        "protected_subject": protected_subject,
        "entries": entries,
    }


def validate_setup_activation_authority(program_root: Path) -> list[str]:
    """Validate the durable v3 setup decision and its derived activation receipts."""
    root = Path(program_root)
    try:
        manifest = _load_manifest(root)
        setup, setup_path = _setup_activation_record(root, manifest)
        approvals, _ = _load_role(root, manifest, "approvals", json_lines=True)
        status, _ = _load_role(root, manifest, "status")
        gates, _ = _load_role(
            root, manifest, "source_gate_decisions", json_lines=True
        )
    except ValueError as error:
        return [str(error)]
    issues: list[str] = []
    expected_setup_fields = (
        "schema_version",
        "program_id",
        "program_revision",
        "source_binding",
        "program_binding",
        "semantic_decision_identity",
        "operation_envelope_sha256",
        "source_gate_definitions_sha256",
        "recap_checkpoint",
        "presented_integrity_identity",
        "decision",
        "provenance_class",
        "setup_adapter_id",
        "setup_adapter_sha256",
        "workspace_observation",
        "integrity_drift_classification",
        "program_approval_event_id",
        "workspace_approval_event_id",
        "proposal_status_sha256",
        "proposal_status_sequence",
        "decision_id",
    )
    issues.extend(
        _exact_fields(setup, expected_setup_fields, "setup-activation decision")
    )
    setup_base = dict(setup)
    decision_id = setup_base.pop("decision_id", None)
    semantics = manifest.get("setup_semantics")
    if (
        setup.get("schema_version") != SETUP_ACTIVATION_SCHEMA
        or setup.get("program_id") != manifest.get("program_id")
        or setup.get("program_revision") != manifest.get("program_revision")
        or setup.get("source_binding") != manifest.get("source_binding")
        or setup.get("program_binding") != manifest.get("program_binding")
        or setup.get("semantic_decision_identity")
        != setup_semantic_identity(manifest)
        or not isinstance(semantics, dict)
        or setup.get("operation_envelope_sha256")
        != value_sha256(semantics.get("operation_envelope"))
        or setup.get("source_gate_definitions_sha256")
        != manifest.get("source_gate_definitions_sha256")
        or setup.get("decision") != "approved"
        or setup.get("provenance_class") != DIRECT_USER_PROVENANCE
        or setup.get("proposal_status_sequence") != 0
        or decision_id != _identifier("setup-activation-decision", setup_base)
    ):
        issues.append("setup-activation decision binding mismatch")
    for field in (
        "setup_adapter_id",
        "program_approval_event_id",
        "workspace_approval_event_id",
    ):
        if not _is_text(setup.get(field)):
            issues.append(f"setup-activation decision {field} is required")
    for field in ("setup_adapter_sha256", "proposal_status_sha256"):
        if not _is_sha256(setup.get(field)):
            issues.append(f"setup-activation decision {field} is invalid")

    setup_sha256 = sha256_file(setup_path)
    expected_satisfaction: dict[str, object] | None
    try:
        expected_satisfaction = source_gate_satisfaction(
            root,
            "before-program-activation",
            f"program:{manifest['program_id']}",
        )
    except ValueError as error:
        issues.append(str(error))
        expected_satisfaction = None
    expected_types = (
        ("program-approval", setup.get("program_approval_event_id")),
        (
            "workspace-selection-approval",
            setup.get("workspace_approval_event_id"),
        ),
    )
    receipts: dict[str, dict[str, object]] = {}
    for record_type, event_id in expected_types:
        matches = [
            record
            for record in approvals
            if record.get("event_id") == event_id
            and record.get("type") == record_type
        ]
        if len(matches) != 1:
            issues.append(f"v3 {record_type} receipt must exist exactly once")
            continue
        record = matches[0]
        receipts[record_type] = record
        if (
            record.get("schema_version") != "implementation-approval/v2"
            or record.get("decision") != "approved"
            or record.get("program_id") != manifest.get("program_id")
            or record.get("program_revision") != manifest.get("program_revision")
            or record.get("setup_activation_decision_id") != decision_id
            or record.get("setup_activation_decision_sha256") != setup_sha256
            or record.get("source_gate_satisfaction") != expected_satisfaction
            or record.get("increment_grant_id") is not None
            or record.get("exact_file_plan_sha256") is not None
            or record.get("execution_baseline_sha256") is not None
        ):
            issues.append(f"v3 {record_type} receipt binding mismatch")
    if expected_satisfaction is not None and len(receipts) == len(expected_types):
        program_approval = receipts["program-approval"]
        workspace_approval = receipts["workspace-selection-approval"]
        expected_status_binding = {
            "schema_version": "implementation-setup-activation-status-binding/v1",
            "setup_activation_decision_id": decision_id,
            "setup_activation_decision_sha256": setup_sha256,
            "program_approval_event_id": program_approval.get("event_id"),
            "program_approval_sha256": _bytes_sha256(
                canonical_identity_bytes(program_approval) + b"\n"
            ),
            "workspace_approval_event_id": workspace_approval.get("event_id"),
            "workspace_approval_sha256": _bytes_sha256(
                canonical_identity_bytes(workspace_approval) + b"\n"
            ),
            "source_gate_satisfaction": expected_satisfaction,
        }
        if status.get("setup_activation_binding") != expected_status_binding:
            issues.append("v3 setup activation status binding mismatch")
    gate_ids = [str(record.get("gate_id")) for record in gates]
    if len(gate_ids) != len(set(gate_ids)):
        issues.append("source-gate decision ledger must contain unique decisions")
    definitions = {
        str(definition.get("gate_id")): definition
        for definition in _gate_definitions(manifest)
    }
    if any(gate_id not in definitions for gate_id in gate_ids):
        issues.append("source-gate decision ledger contains an undeclared gate")
    for trigger in SUPPORTED_GATE_TRIGGERS:
        actual = [
            gate_id
            for gate_id in gate_ids
            if definitions.get(gate_id, {}).get("trigger") == trigger
        ]
        expected = [
            str(definition["gate_id"])
            for definition in _gate_definitions(manifest)
            if definition.get("trigger") == trigger
            and definition.get("setup_reuse") is False
        ]
        if actual != expected[: len(actual)]:
            issues.append(
                f"source-gate decisions at {trigger} are not a stable prefix"
            )
    if any(
        record.get("schema_version") != SOURCE_GATE_DECISION_SCHEMA
        for record in gates
    ):
        issues.append("source-gate decision ledger contains a foreign schema")
    return sorted(set(issues))
