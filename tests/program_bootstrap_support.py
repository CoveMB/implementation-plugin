import hashlib
import argparse
from dataclasses import asdict
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEGACY_PROGRAM_FIXTURE = (
    REPOSITORY_ROOT
    / "tests/fixtures/program-authority/portable-archive-program"
)
SOURCE_PLAN_FIXTURE = (
    REPOSITORY_ROOT
    / "tests/fixtures/program-bootstrap/portable-notes/source-plan.md"
)
COMPATIBILITY_FIXTURE = (
    REPOSITORY_ROOT / "tests/fixtures/program-bootstrap/v0.1.1"
)
COMPATIBILITY_WORKSPACE_SEED = COMPATIBILITY_FIXTURE / "seed-workspace/catalog.txt"


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_compact_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def run_git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GIT_AUTHOR_DATE": "2026-08-18T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-08-18T00:00:00Z",
        },
    ).stdout.strip()


def repository_snapshot(root: Path) -> dict[str, tuple[str, str]]:
    snapshot: dict[str, tuple[str, str]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        if path.is_symlink():
            snapshot[relative] = ("symlink", str(path.readlink()))
        elif path.is_file():
            snapshot[relative] = (
                "file",
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        elif path.is_dir():
            snapshot[relative] = ("directory", "")
        else:
            snapshot[relative] = ("special", "")
    return snapshot


REVIEW_RISK_SCOPES = {
    "security-privacy": "specialist-security-privacy",
    "public-api-compatibility": "specialist-compatibility",
    "concurrency-reliability-distributed-state": "specialist-reliability",
    "persistent-data-migrations": "specialist-persistent-data",
    "accessibility": "specialist-accessibility",
    "platform-deployment-infrastructure": "specialist-platform",
    "payments-financial-state": "specialist-financial",
    "performance": "specialist-performance",
    "provider-external-state": "specialist-provider",
}


def raw_review_report(
    scope: str, increment_id: str = "ARCHIVE-INDEX"
) -> dict[str, object]:
    """Return one deterministic raw first-increment review report fixture."""
    value: dict[str, object] = {
        "schema_version": "implementation-raw-review-report/v1",
        "scope": scope,
        "program_id": "ARCHIVE-PROGRAM",
        "program_revision": 1,
        "increment_id": increment_id,
        "reviewer_role": "controller-self-review",
        "independent": False,
        "reduced_assurance": True,
        "persisted_at": "2026-08-18T10:00:00Z",
        "reconciled_at": "2026-08-18T10:10:00Z",
        "review_basis": f"bounded {scope} review of the exact current delta",
        "prior_conclusions_withheld": False,
        "findings": [],
    }
    if scope == "architecture":
        value["risk_predicates"] = [
            {
                "predicate": predicate,
                "touched": False,
                "specialist_scope": specialist,
                "evidence": f"the exact delta does not touch {predicate}",
                "rationale": "no specialist scope selected",
            }
            for predicate, specialist in REVIEW_RISK_SCOPES.items()
        ]
    if scope == "test-evidence":
        command = "python3 -m unittest tests.test_archive_output"
        value.update(
            test_first_evidence=[
                {
                    "schema_version": "implementation-execution-evidence/v1",
                    "slice_id": "archive-output",
                    "purpose": "create the archive output",
                    "red_command": command,
                    "expected_failure": "archive output was missing",
                    "observed_failure": "archive output was missing",
                    "red_exit_code": 1,
                    "observed_before_production_change": True,
                    "intended_reason_match": True,
                    "green_command": command,
                    "observed_green": "archive output test passed",
                    "green_exit_code": 0,
                    "evidence_order": ["red", "green"],
                }
            ],
            alternative_verification=[],
            recovery_domains=[
                {
                    "domain": "source-code",
                    "touched": True,
                    "disposition": "recoverable",
                    "mechanism": "remove exact-plan Create paths; restore exact pre-write bytes for Modify paths",
                    "verification": "rerun the bound deterministic test",
                    "limitation": "does not recover external state",
                    "required_authority": "modify-workspace",
                    "authority_granted": True,
                },
                *[
                    {
                        "domain": domain,
                        "touched": False,
                        "disposition": "not-touched",
                        "mechanism": "none",
                        "verification": "confirmed outside the exact plan",
                        "limitation": "not exercised",
                        "required_authority": "none",
                        "authority_granted": False,
                    }
                    for domain in (
                        "persistent-data",
                        "deployment",
                        "provider-or-external-state",
                    )
                ],
            ],
            final_verification={
                "verified_at": "2026-08-18T11:05:00Z",
                "commands": [
                    {
                        "command": command,
                        "exit_code": 0,
                        "result": "archive output test passed",
                        "completed_at": "2026-08-18T11:00:00Z",
                        "expected_result": "exit zero",
                        "relevant_inputs": ["archive-output.txt"],
                    }
                ],
                "required_commands": [command],
                "baseline_failures": ["none"],
            },
            remediation_cycles=[],
        )
    return value


def write_raw_review_reports(
    repository: Path,
    increment_id: str = "ARCHIVE-INDEX",
    relative_directory: str = "reviews",
) -> None:
    reviews = Path(repository) / relative_directory
    reviews.mkdir(parents=True, exist_ok=True)
    for scope in ("requirements", "architecture", "test-evidence"):
        (reviews / f"{scope}.json").write_bytes(
            canonical_json(raw_review_report(scope, increment_id))
        )


def _rewrite_inherited_review_reports(
    repository: Path,
    status: dict[str, object],
    increment_id: str,
) -> None:
    binding = status.get("inherited_workspace_binding", {})
    inherited_paths = (
        binding.get("inherited_paths", []) if isinstance(binding, dict) else []
    )
    if not isinstance(inherited_paths, list):
        raise ValueError("inherited review paths must be a list")
    report_names = {
        "architecture.json",
        "requirements.json",
        "test-evidence.json",
    }
    for relative in inherited_paths:
        if not isinstance(relative, str) or "\\" in relative:
            raise ValueError("inherited review path must be a relative POSIX path")
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or any(
            part in {"", ".", ".."} for part in relative_path.parts
        ):
            raise ValueError("inherited review path must be a relative POSIX path")
        if relative_path.name not in report_names:
            continue
        report_path = Path(repository).joinpath(*relative_path.parts)
        if not report_path.is_file() or report_path.is_symlink():
            raise ValueError(f"inherited review report is invalid: {relative}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise ValueError(f"inherited review report is invalid: {relative}")
        report["increment_id"] = increment_id
        report_path.write_bytes(canonical_json(report))


class BootstrapFixture:
    def __init__(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.repository = self.root / "repository"
        self.repository.mkdir()
        run_git(self.repository, "init", "-b", "archive-maintenance")
        run_git(self.repository, "config", "user.name", "Archive Fixture")
        run_git(self.repository, "config", "user.email", "archive@example.invalid")
        shutil.copyfile(COMPATIBILITY_WORKSPACE_SEED, self.repository / "catalog.txt")
        run_git(self.repository, "add", "catalog.txt")
        run_git(self.repository, "commit", "-m", "seed archive")
        self.head = run_git(self.repository, "rev-parse", "HEAD")

        self.source_plan = self.root / "source-plan.md"
        shutil.copyfile(SOURCE_PLAN_FIXTURE, self.source_plan)
        self.source_sha256 = hashlib.sha256(self.source_plan.read_bytes()).hexdigest()
        self.candidate = self.root / "candidate"
        shutil.copytree(LEGACY_PROGRAM_FIXTURE, self.candidate)
        self._configure_candidate()
        self.program_root = (
            self.repository / "implementation-programs/ARCHIVE-PROGRAM"
        ).resolve(strict=False)

    def close(self) -> None:
        self.temporary_directory.cleanup()

    def load_json(self, relative_path: str) -> dict[str, object]:
        return json.loads((self.candidate / relative_path).read_text(encoding="utf-8"))

    def write_json(self, relative_path: str, value: object) -> None:
        path = self.candidate / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json(value))

    def configure_successors(
        self,
        successors: dict[str, tuple[str, ...]],
    ) -> None:
        """Allocate deterministic successor semantics before program activation."""
        traceability = self.load_json("program/traceability.json")
        source_units = traceability["source_units"]
        requirement_unit = next(
            unit for unit in source_units if unit["classification"] == "requirement"
        )
        atomic_requirements = traceability["atomic_requirements"]
        for successor_index, (successor_id, dependencies) in enumerate(
            successors.items(), start=1
        ):
            requirement_id = f"SUCCESSOR-OUTCOME-{successor_index}"
            requirement_unit["requirement_ids"].append(requirement_id)
            atomic_requirements.append(
                {
                    "id": requirement_id,
                    "group_id": "INTEGRITY",
                    "source_unit_ids": [requirement_unit["id"]],
                    "source_locator": "Archive Plan, line 3",
                    "normalized_requirement": f"Complete {successor_id}.",
                    "acceptance_criteria": [f"{successor_id} is complete."],
                    "assigned_parts": ["Archive integrity"],
                    "assigned_tasks": [f"Complete {successor_id}"],
                    "assigned_increments": ["ARCHIVE-INDEX", successor_id],
                    "current_disposition": "allocated",
                    "decision_references": [],
                    "implementation_evidence": [],
                    "verification_evidence": [],
                }
            )
            for dependency_index, dependency_id in enumerate(dependencies, start=1):
                if dependency_id == "ARCHIVE-INDEX":
                    continue
                dependency_requirement_id = (
                    f"SUCCESSOR-DEPENDENCY-{successor_index}-{dependency_index}"
                )
                requirement_unit["requirement_ids"].append(
                    dependency_requirement_id
                )
                atomic_requirements.append(
                    {
                        "id": dependency_requirement_id,
                        "group_id": "INTEGRITY",
                        "source_unit_ids": [requirement_unit["id"]],
                        "source_locator": "Archive Plan, line 3",
                        "normalized_requirement": (
                            f"Complete {dependency_id} before {successor_id}."
                        ),
                        "acceptance_criteria": [
                            f"{dependency_id} precedes {successor_id}."
                        ],
                        "assigned_parts": ["Archive integrity"],
                        "assigned_tasks": [f"Complete {dependency_id}"],
                        "assigned_increments": [dependency_id, successor_id],
                        "current_disposition": "allocated",
                        "decision_references": [],
                        "implementation_evidence": [],
                        "verification_evidence": [],
                    }
                )
        semantic_records = [
            {
                field: record[field]
                for field in (
                    "id",
                    "group_id",
                    "source_unit_ids",
                    "normalized_requirement",
                    "acceptance_criteria",
                    "assigned_parts",
                    "assigned_tasks",
                    "assigned_increments",
                )
            }
            for record in atomic_requirements
        ]
        semantic_sha256 = hashlib.sha256(
            json.dumps(
                semantic_records,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        traceability["coverage_assertion"][
            "semantic_requirements_sha256"
        ] = semantic_sha256
        self.write_json("program/traceability.json", traceability)
        manifest = self.load_json("manifest.json")
        manifest["program_binding"]["traceability_sha256"] = hashlib.sha256(
            (self.candidate / "program/traceability.json").read_bytes()
        ).hexdigest()
        self.write_json("manifest.json", manifest)
        status = self.load_json("state/status.json")
        status["program_binding"][
            "semantic_requirements_sha256"
        ] = semantic_sha256
        self.write_json("state/status.json", status)

    def configure_successor_chain(self, increment_ids: tuple[str, ...]) -> None:
        """Allocate one deterministic causal increment chain before activation."""
        if (
            len(increment_ids) < 2
            or increment_ids[0] != "ARCHIVE-INDEX"
            or any(not item for item in increment_ids)
            or len(increment_ids) != len(set(increment_ids))
        ):
            raise ValueError("successor chain must start at ARCHIVE-INDEX and be unique")
        traceability = self.load_json("program/traceability.json")
        source_units = traceability["source_units"]
        requirement_unit = next(
            unit for unit in source_units if unit["classification"] == "requirement"
        )
        requirement_id = "SUCCESSOR-CHAIN"
        requirement_unit["requirement_ids"].append(requirement_id)
        atomic_requirements = traceability["atomic_requirements"]
        atomic_requirements.append(
            {
                "id": requirement_id,
                "group_id": "INTEGRITY",
                "source_unit_ids": [requirement_unit["id"]],
                "source_locator": "Archive Plan, line 3",
                "normalized_requirement": "Complete the archive increment chain.",
                "acceptance_criteria": [
                    "Each archive increment follows its allocated predecessor."
                ],
                "assigned_parts": ["Archive integrity"],
                "assigned_tasks": ["Complete the archive increment chain"],
                "assigned_increments": list(increment_ids),
                "current_disposition": "allocated",
                "decision_references": [],
                "implementation_evidence": [],
                "verification_evidence": [],
            }
        )
        semantic_records = [
            {
                field: record[field]
                for field in (
                    "id",
                    "group_id",
                    "source_unit_ids",
                    "normalized_requirement",
                    "acceptance_criteria",
                    "assigned_parts",
                    "assigned_tasks",
                    "assigned_increments",
                )
            }
            for record in atomic_requirements
        ]
        semantic_sha256 = hashlib.sha256(
            json.dumps(
                semantic_records,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        traceability["coverage_assertion"][
            "semantic_requirements_sha256"
        ] = semantic_sha256
        self.write_json("program/traceability.json", traceability)
        manifest = self.load_json("manifest.json")
        manifest["program_binding"]["traceability_sha256"] = hashlib.sha256(
            (self.candidate / "program/traceability.json").read_bytes()
        ).hexdigest()
        self.write_json("manifest.json", manifest)
        status = self.load_json("state/status.json")
        status["program_binding"][
            "semantic_requirements_sha256"
        ] = semantic_sha256
        self.write_json("state/status.json", status)

    def configure_approval_mode(self, approval_mode: str) -> None:
        """Select one supported Plan A approval mode before publication."""
        if approval_mode not in {
            "approval:standard",
            "approval:pre-approve",
            "approval:full-increment",
        }:
            raise ValueError("unsupported fixture approval mode")
        manifest = self.load_json("manifest.json")
        manifest["approval_mode"] = approval_mode
        self.write_json("manifest.json", manifest)
        status = self.load_json("state/status.json")
        status["approval_mode"] = approval_mode
        self.write_json("state/status.json", status)

    def configure_setup_v3(
        self,
        *,
        source_gate_definitions: Sequence[dict[str, object]] = (),
    ) -> None:
        """Upgrade the candidate fixture to the closed setup/activation family."""
        manifest = self.load_json("manifest.json")
        workspace = self.load_json("state/workspace.json")
        traceability = self.load_json("program/traceability.json")
        definitions = sorted(
            (dict(item) for item in source_gate_definitions),
            key=lambda item: str(item.get("gate_id", "")),
        )
        manifest["schema_version"] = "implementation-program-manifest/v3"
        manifest["logical_roles"].update(
            setup_activation_decision="state/setup-activation-decision.json",
            source_gate_decisions="state/source-gate-decisions.jsonl",
        )
        gate_ledger = self.candidate / "state/source-gate-decisions.jsonl"
        gate_ledger.parent.mkdir(parents=True, exist_ok=True)
        gate_ledger.write_bytes(b"")
        manifest["source_gate_definitions"] = definitions
        manifest["source_gate_definitions_sha256"] = canonical_compact_sha256(
            definitions
        )
        atomic_requirements = traceability["atomic_requirements"]
        increment_ids: list[str] = []
        for atomic_requirement in atomic_requirements:
            for increment_id in atomic_requirement["assigned_increments"]:
                if increment_id not in increment_ids:
                    increment_ids.append(increment_id)
        increments = []
        for increment_index, increment_id in enumerate(increment_ids):
            assigned = [
                atomic_requirement
                for atomic_requirement in atomic_requirements
                if increment_id in atomic_requirement["assigned_increments"]
            ]
            increments.append(
                {
                    "increment_id": increment_id,
                    "depends_on": (
                        [increment_ids[increment_index - 1]]
                        if increment_index
                        else []
                    ),
                    "requirement_ids": [item["id"] for item in assigned],
                    "acceptance_meaning": [
                        criterion
                        for item in assigned
                        for criterion in item["acceptance_criteria"]
                    ],
                    "intended_outcome": " ".join(
                        item["normalized_requirement"] for item in assigned
                    ),
                    "expected_checks": [
                        "python3 -m unittest tests.test_archive_output"
                    ],
                }
            )
        setup_semantics = {
            "schema_version": "implementation-program-setup-semantics/v1",
            "program": {
                "name": "Archive integrity program",
                "program_id": manifest["program_id"],
                "program_revision": manifest["program_revision"],
                "intended_outcome": "Verify stored archive checksums.",
            },
            "bindings": {
                "source": dict(manifest["source_binding"]),
                "program": {
                    **dict(manifest["program_binding"]),
                    "semantic_requirements_sha256": traceability[
                        "coverage_assertion"
                    ]["semantic_requirements_sha256"],
                },
                "workspace_sha256": hashlib.sha256(
                    canonical_json(workspace)
                ).hexdigest(),
                "source_gate_definitions_sha256": manifest[
                    "source_gate_definitions_sha256"
                ],
            },
            "sources": [
                {
                    "source_id": manifest["source_binding"]["source_id"],
                    "title": "Archive Plan",
                    "location": "source/implementation-plan.md",
                    "sha256": manifest["source_binding"]["sha256"],
                }
            ],
            "workspace": {
                "repository": workspace["repository"]["identity"],
                "path": workspace["implementation_workspace"]["path"],
                "branch": workspace["implementation_workspace"]["branch"],
                "base_commit": workspace["implementation_workspace"]["base_commit"],
                "head_commit": workspace["implementation_workspace"][
                    "head_commit_at_selection"
                ],
                "protected_work": dict(workspace["pre_existing_work_at_selection"]),
            },
            "increments": increments,
            "approval": {
                "mode": manifest["approval_mode"],
                "routine_exact_plan_question": manifest["approval_mode"]
                == "approval:standard",
                "remaining_boundaries": [
                    "source-defined gates",
                    "diff disposition",
                    "continuation",
                    "consequential actions",
                ],
            },
            "operation_envelope": {
                "schema_version": "implementation-operation-envelope/v1",
                "supported_operations": ["Create", "Modify", "Preserve"],
                "allocations": [
                    {
                        "kind": "exact-path",
                        "path": "archive-output.txt",
                        "operation": "Create",
                        "increment_ids": increment_ids,
                        "inclusions": ["archive checksum output"],
                        "exclusions": [],
                        "ownership": "program",
                        "protected": False,
                        "user_work": False,
                        "file_kind": "absent",
                        "link_kind": "none",
                        "mode": None,
                        "collision": "none",
                    },
                    {
                        "kind": "exact-path",
                        "path": "catalog.txt",
                        "operation": "Preserve",
                        "increment_ids": increment_ids,
                        "inclusions": ["existing archive catalog"],
                        "exclusions": [],
                        "ownership": "user",
                        "protected": True,
                        "user_work": False,
                        "file_kind": "regular-file",
                        "link_kind": "none",
                        "mode": "100644",
                        "collision": "existing",
                    },
                    {
                        "kind": "bounded-path-class",
                        "path": "reviews",
                        "operation": "Create",
                        "increment_ids": increment_ids,
                        "inclusions": ["required review scope reports"],
                        "exclusions": [],
                        "ownership": "program",
                        "protected": False,
                        "user_work": False,
                        "file_kind": "absent",
                        "link_kind": "none",
                        "mode": None,
                        "collision": "none",
                    },
                ],
            },
            "protections": ["Preserve catalog.txt byte-for-byte."],
            "exclusions": ["No external publication."],
            "external_boundaries": ["Git and provider actions require separate approval."],
            "material_risks": ["Repository drift invalidates the setup checkpoint."],
            "first_increment_id": "ARCHIVE-INDEX",
        }
        if len(increment_ids) > 1:
            setup_semantics["operation_envelope"]["allocations"].extend(
                [
                    {
                        "kind": "exact-path",
                        "path": "archive-output.txt",
                        "operation": "Modify",
                        "increment_ids": increment_ids[1:],
                        "inclusions": ["accepted archive checksum output"],
                        "exclusions": [],
                        "ownership": "program",
                        "protected": False,
                        "user_work": False,
                        "file_kind": "regular-file",
                        "link_kind": "none",
                        "mode": "100644",
                        "collision": "accepted-predecessor",
                    },
                    {
                        "kind": "bounded-path-class",
                        "path": "reviews",
                        "operation": "Modify",
                        "increment_ids": increment_ids[1:],
                        "inclusions": ["accepted predecessor review reports"],
                        "exclusions": [],
                        "ownership": "program",
                        "protected": False,
                        "user_work": False,
                        "file_kind": "regular-file",
                        "link_kind": "none",
                        "mode": "100644",
                        "collision": "accepted-predecessor",
                    },
                ]
            )
        manifest["setup_semantics"] = setup_semantics
        manifest["setup_semantics_sha256"] = canonical_compact_sha256(setup_semantics)
        self.write_json("manifest.json", manifest)
        first_brief = (
            self.candidate
            / manifest["increment_storage"]["root"]
            / setup_semantics["first_increment_id"]
            / manifest["increment_storage"]["brief_filename"]
        )
        first_brief.parent.mkdir(parents=True, exist_ok=True)
        first_brief.write_text(
            "# Archive integrity\n\nVerify every stored checksum.\n",
            encoding="utf-8",
        )
        status = self.load_json("state/status.json")
        status["schema_version"] = "implementation-program-status/v3"
        self.write_json("state/status.json", status)

    def _configure_candidate(self) -> None:
        manifest = self.load_json("manifest.json")
        source_bytes = self.source_plan.read_bytes()
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        (self.candidate / "source/implementation-plan.md").write_bytes(source_bytes)
        source_lines = source_bytes.splitlines(keepends=True)
        source_units = []
        for line_number, line in enumerate(source_lines, start=1):
            requirement = line_number == 3
            unit = {
                "id": f"SOURCE-UNIT-LINE-{line_number}",
                "start_line": line_number,
                "end_line": line_number,
                "source_text_sha256": hashlib.sha256(line).hexdigest(),
                "classification": "requirement" if requirement else "context",
                "requirement_ids": ["INTEGRITY-VERIFY-CHECKSUMS"] if requirement else [],
            }
            if not requirement:
                unit["context_rationale"] = "Heading or structural separation."
            source_units.append(unit)
        atomic_requirements = [
            {
                "id": "INTEGRITY-VERIFY-CHECKSUMS",
                "group_id": "INTEGRITY",
                "source_unit_ids": ["SOURCE-UNIT-LINE-3"],
                "source_locator": "Archive Plan, line 3",
                "normalized_requirement": "Verify every stored checksum.",
                "acceptance_criteria": [
                    "A corrupted stored object is rejected by checksum verification."
                ],
                "assigned_parts": ["Archive integrity"],
                "assigned_tasks": ["Verify stored objects"],
                "assigned_increments": ["ARCHIVE-INDEX"],
                "current_disposition": "allocated",
                "decision_references": [],
                "implementation_evidence": [],
                "verification_evidence": [],
            }
        ]
        semantic_records = [
            {
                field: record[field]
                for field in (
                    "id",
                    "group_id",
                    "source_unit_ids",
                    "normalized_requirement",
                    "acceptance_criteria",
                    "assigned_parts",
                    "assigned_tasks",
                    "assigned_increments",
                )
            }
            for record in atomic_requirements
        ]
        semantic_sha256 = hashlib.sha256(
            json.dumps(
                semantic_records,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        self.write_json(
            "source/source-metadata.json",
            {
                "byte_count": len(source_bytes),
                "immutable": True,
                "line_count": len(source_lines),
                "schema_version": "implementation-source-metadata/v1",
                "sha256": source_sha256,
                "snapshot_path": "source/implementation-plan.md",
                "source_id": "ARCHIVE-SOURCE",
            },
        )
        traceability = {
            "schema_version": "implementation-traceability/v2",
            "program_id": "ARCHIVE-PROGRAM",
            "program_revision": 1,
            "source_id": "ARCHIVE-SOURCE",
            "source_sha256": source_sha256,
            "coverage_assertion": {
                "status": "complete",
                "machine_complete": True,
                "source_line_count": len(source_lines),
                "semantic_requirements_sha256": semantic_sha256,
                "approval_event_id": "ARCHIVE-APPROVAL",
            },
            "source_units": source_units,
            "requirement_groups": [{"id": "INTEGRITY", "title": "Archive integrity"}],
            "atomic_requirements": atomic_requirements,
        }
        self.write_json("program/traceability.json", traceability)
        manifest.update(
            program_id="ARCHIVE-PROGRAM",
            program_revision=1,
            source_binding={"source_id": "ARCHIVE-SOURCE", "sha256": source_sha256},
        )
        manifest["program_binding"]["traceability_sha256"] = hashlib.sha256(
            (self.candidate / "program/traceability.json").read_bytes()
        ).hexdigest()
        manifest.update(
            schema_version="implementation-program-manifest/v2",
            increment_storage={
                "schema_version": "implementation-increment-storage/v1",
                "root": "increments",
                "brief_filename": "brief.md",
                "exact_file_plan_filename": "exact-file-plan.md",
                "execution_baseline_filename": "execution-baseline.json",
                "review_evidence_filename": "review-evidence.json",
                "review_packet_filename": "review-packet.md",
                "handoff_filename": "handoff.md",
            },
            closure_storage={
                "schema_version": "implementation-closure-storage/v1",
                "root": "closure",
                "reconciliation_filename": "reconciliation.json",
                "packet_filename": "closure-packet.md",
            },
        )
        manifest["logical_roles"].update(
            action_authorizations="state/action-authorizations.jsonl",
            increment_grants="state/increment-grants.jsonl",
            rollovers="state/rollovers.jsonl",
            block_resolutions="state/block-resolutions.jsonl",
            workspace="state/workspace.json",
            status="state/status.json",
        )
        self.write_json("manifest.json", manifest)
        for relative_path in (
            "state/approvals.jsonl",
            "state/action-authorizations.jsonl",
            "state/increment-grants.jsonl",
            "state/rollovers.jsonl",
            "state/block-resolutions.jsonl",
        ):
            path = self.candidate / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"")
        workspace = {
            "schema_version": "implementation-workspace-proposal/v1",
            "program_id": manifest["program_id"],
            "program_revision": manifest["program_revision"],
            "repository": {"identity": str(self.repository.resolve())},
            "implementation_workspace": {
                "path": str(self.repository.resolve()),
                "branch": "archive-maintenance",
                "base_commit": self.head,
                "head_commit_at_selection": self.head,
            },
            "pre_existing_work_at_selection": {
                "staged_paths": [],
                "modified_paths": [],
                "untracked_paths": [],
                "conflicted_paths": [],
                "active_git_operation": None,
            },
        }
        self.write_json("state/workspace.json", workspace)
        status = {
            "schema_version": "implementation-program-status/v2",
            "program_id": manifest["program_id"],
            "program_revision": manifest["program_revision"],
            "state_sequence": 0,
            "program_state": "awaiting-program-approval",
            "current_increment_id": "ARCHIVE-INDEX",
            "current_increment_state": "not-started",
            "approval_mode": manifest["approval_mode"],
            "source_binding": dict(manifest["source_binding"]),
            "program_binding": {
                "sha256": manifest["program_binding"]["sha256"],
                "semantic_requirements_sha256": traceability["coverage_assertion"][
                    "semantic_requirements_sha256"
                ],
            },
        }
        self.write_json("state/status.json", status)


def _exact_plan_bytes(program_root: Path, observation: object) -> bytes:
    """Build the deterministic application-path plan used by lifecycle tests."""
    from program_activation import required_future_lifecycle_writes

    manifest = json.loads((program_root / "manifest.json").read_text(encoding="utf-8"))
    status = json.loads((program_root / "state/status.json").read_text(encoding="utf-8"))
    required = required_future_lifecycle_writes(
        program_root, Path(observation.path), status["current_increment_id"]
    )
    inherited = set(
        status.get("inherited_workspace_binding", {}).get("inherited_paths", [])
    )
    increment_id = str(status["current_increment_id"])
    review_root = (
        "reviews"
        if increment_id == "ARCHIVE-INDEX"
        else f"reviews/{increment_id}"
    )
    raw_review_paths = {
        scope: f"{review_root}/{scope}.json"
        for scope in ("architecture", "requirements", "test-evidence")
    }
    product_paths = {
        "archive-output.txt",
        *raw_review_paths.values(),
    }
    create = sorted(
        {
            *(product_paths - inherited),
            *(item.path for item in required if item.disposition == "Create"),
        }
    )
    modify = sorted(
        {
            *inherited,
            *(item.path for item in required if item.disposition == "Modify"),
        }
    )
    preserve = sorted(
        {
            "catalog.txt",
            *(item.path for item in required if item.disposition == "Preserve"),
        }
    )
    source = status["source_binding"]
    program = status["program_binding"]
    lines = [
        "# Archive exact plan",
        "",
        "## Global constraints",
        "Preserve user work and write only declared paths.",
        "",
        "## Requirements and acceptance binding",
        f"Program id: {manifest['program_id']}",
        f"Program revision: {manifest['program_revision']}",
        f"Increment id: {status['current_increment_id']}",
        f"Source digest: {source['sha256']}",
        f"Program digest: {program['sha256']}",
        f"Semantic digest: {program['semantic_requirements_sha256']}",
        f"Workspace path: {observation.path}",
        f"Workspace branch: {observation.branch}",
        f"Workspace base: {observation.base_commit}",
        f"Workspace head: {observation.head_commit}",
        "",
        "## File map",
        "",
    ]
    for disposition, paths in (
        ("Create", create),
        ("Modify", modify),
        ("Preserve", preserve),
    ):
        lines.extend(
            [
                f"### {disposition}",
                "",
                *[f"- `{path}` — exact owned path." for path in paths],
                "",
            ]
        )
    lines.extend(
        [
            "Interfaces: `archive-output.txt` is the bounded product output.",
            "",
            "## Semantic naming inventory",
            "| Surface | Kind | Context | Intention |",
            "|---|---|---|---|",
            "| `archive-output.txt` | path | archive output | record the verified result |",
            "",
            "## Test-first slices and verification contracts",
            "Create the output, then verify its observable bytes.",
            "",
            "## Commands and expected evidence",
            "Run `python3 -m unittest tests.test_archive_output`; expected exit 0.",
            "",
            "## Review scopes and specialist predicates",
            f"- requirements: `{raw_review_paths['requirements']}`",
            f"- architecture: `{raw_review_paths['architecture']}`",
            f"- test-evidence: `{raw_review_paths['test-evidence']}`",
            "",
            "## Commit boundaries",
            "One logical local commit boundary; no commit authority is granted.",
            "",
            "## Rollback and recovery",
            "Preserve prefixes and retry only byte-identical transactions.",
            "",
            "## Approval required to execute",
            "Use the persisted approval mode and status-current grant.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _load_prompt(path_value: str | None) -> str:
    if path_value is None:
        raise ValueError("this phase requires --prompt-file")
    path = Path(path_value)
    if path.is_symlink() or not path.is_file():
        raise ValueError("prompt file must be a regular non-symlink file")
    return path.read_text(encoding="utf-8")


def _fresh_observation(repository: Path):
    from repository_preparation import inspect_repository

    base_commit = run_git(repository, "rev-parse", "HEAD")
    return inspect_repository(repository, base_commit).observation


def _install_failure_hook(module: object, fail_label: str | None) -> None:
    if fail_label is None:
        return

    def fail_after_persist(label: str) -> None:
        if label == fail_label:
            raise RuntimeError(f"injected-after:{label}")

    module._after_persist = fail_after_persist


def _program_root(repository: Path) -> Path:
    return repository / "implementation-programs/ARCHIVE-PROGRAM"


def run_lifecycle_phase(arguments: argparse.Namespace) -> dict[str, object]:
    """Run one production lifecycle phase for a fresh-process causal test."""
    script_root = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
    sys.path.insert(0, str(script_root))
    try:
        import diff_disposition
        import blocked_recovery
        import program_activation
        import program_bootstrap
        import program_closure
        import program_continuation
        import program_launch
        import program_review
        import program_rollover

        repository = Path(arguments.repository).resolve(strict=True)
        program_root = _program_root(repository)
        phase = arguments.phase
        if phase == "publish":
            _install_failure_hook(program_bootstrap, arguments.fail_label)
            receipt = program_bootstrap.publish_program_proposal(
                repository,
                Path(arguments.source_plan),
                Path(arguments.candidate),
                arguments.source_sha256,
            )
            return {
                **asdict(receipt),
                "prompt": program_launch.render_program_launch_prompt(program_root),
            }

        if phase == "activate":
            _install_failure_hook(program_activation, arguments.fail_label)
            receipt = program_activation.activate_program(
                program_root,
                _load_prompt(arguments.prompt_file),
                _fresh_observation(repository),
            )
            return asdict(receipt)

        if phase == "prepare-plan":
            _install_failure_hook(program_activation, arguments.fail_label)
            observation = _fresh_observation(repository)
            plan_bytes = (
                Path(arguments.exact_plan_file).read_bytes()
                if arguments.exact_plan_file is not None
                else _exact_plan_bytes(program_root, observation)
            )
            receipt = program_activation.prepare_exact_plan(
                program_root, plan_bytes, observation
            )
            return asdict(receipt)

        if phase == "render-exact-plan":
            observation = _fresh_observation(repository)
            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            required = program_activation.required_future_lifecycle_writes(
                program_root,
                repository,
                str(status["current_increment_id"]),
            )
            return {
                "plan": _exact_plan_bytes(program_root, observation).decode("utf-8"),
                "required_future_paths": [item.path for item in required],
            }

        if phase == "materialize-plan":
            _install_failure_hook(program_activation, arguments.fail_label)
            receipt = program_activation.materialize_exact_plan(
                program_root,
                _load_prompt(arguments.prompt_file),
                _fresh_observation(repository),
            )
            return asdict(receipt)

        if phase in {"implementing", "reviewing"}:
            _install_failure_hook(program_activation, arguments.fail_label)
            if phase == "reviewing":
                status = json.loads(
                    (program_root / "state/status.json").read_text(encoding="utf-8")
                )
                increment_id = status["current_increment_id"]
                output = (
                    "verified archive output\n"
                    if increment_id == "ARCHIVE-INDEX"
                    else f"verified {increment_id.lower()} output\n"
                )
                (repository / "archive-output.txt").write_text(
                    output, encoding="utf-8"
                )
                _rewrite_inherited_review_reports(
                    repository,
                    status,
                    str(increment_id),
                )
                relative_review_directory = (
                    "reviews"
                    if increment_id == "ARCHIVE-INDEX"
                    else f"reviews/{increment_id}"
                )
                write_raw_review_reports(
                    repository,
                    str(increment_id),
                    relative_review_directory,
                )
            receipt = program_activation.advance_execution_state(
                program_root, phase, _fresh_observation(repository)
            )
            return asdict(receipt)

        if phase == "prepare-review":
            _install_failure_hook(program_review, arguments.fail_label)
            observation = program_activation._without_owned_program_paths(
                program_root, _fresh_observation(repository)
            )
            receipt = program_review.persist_review_preparation(
                program_root, observation
            )
            return {
                **asdict(receipt),
                "prompt": diff_disposition.render_diff_disposition_prompt(program_root)
                if receipt.increment_state == "awaiting-diff-approval"
                else None,
            }

        if phase == "accept":
            _install_failure_hook(diff_disposition, arguments.fail_label)
            receipt = diff_disposition.persist_accept_stop(
                program_root,
                _load_prompt(arguments.prompt_file),
                _fresh_observation(repository),
            )
            return asdict(receipt)

        if phase == "render-accept-stop":
            candidate = diff_disposition.build_diff_acceptance_candidate(
                program_root, _fresh_observation(repository)
            )
            return {"prompt": "Accept and stop.\n\n" + candidate.prompt}

        if phase == "render-accept-continue":
            return {
                "prompt": program_continuation.render_accept_continue_prompt(
                    program_root
                )
            }

        if phase == "dispose-diff":
            _install_failure_hook(diff_disposition, arguments.fail_label)
            _install_failure_hook(program_rollover, arguments.fail_label)
            receipt = diff_disposition.persist_diff_disposition(
                program_root,
                _load_prompt(arguments.prompt_file),
                _fresh_observation(repository),
            )
            return asdict(receipt)

        if phase == "render-later-continuation":
            return {
                "prompt": program_continuation.render_accepted_state_continuation_prompt(
                    program_root
                )
            }

        if phase == "rollover":
            _install_failure_hook(program_rollover, arguments.fail_label)
            receipt = program_rollover.persist_increment_rollover(
                program_root,
                _load_prompt(arguments.prompt_file),
                _fresh_observation(repository),
            )
            return asdict(receipt)

        if phase == "block":
            _install_failure_hook(blocked_recovery, arguments.fail_label)
            observation = _fresh_observation(repository)
            receipt = blocked_recovery.block_current_program(
                program_root,
                blocked_recovery.BlockedTransitionRequest(
                    reason_code="verification-environment-unavailable",
                    recovery_criteria=(
                        "The local verification environment is available.",
                        "The preserved catalog evidence remains unchanged.",
                    ),
                    evidence_bindings=(
                        blocked_recovery.EvidenceBinding(
                            path="catalog.txt",
                            sha256=hashlib.sha256(
                                (repository / "catalog.txt").read_bytes()
                            ).hexdigest(),
                        ),
                    ),
                ),
                observation,
            )
            return asdict(receipt)

        if phase == "render-block-resolution":
            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            context = status["blocked_context"]
            candidate_value = {
                "schema_version": blocked_recovery.BLOCK_RESOLUTION_CANDIDATE_SCHEMA,
                "block_id": context["block_id"],
                "criterion_results": [
                    {"criterion": criterion, "satisfied": True}
                    for criterion in context["recovery_criteria"]
                ],
                "evidence_bindings": context["evidence_bindings"],
            }
            return {
                "prompt": blocked_recovery.render_block_resolution_prompt(
                    program_root,
                    candidate_value,
                    _fresh_observation(repository),
                )
            }

        if phase == "resolve-block":
            _install_failure_hook(blocked_recovery, arguments.fail_label)
            receipt = blocked_recovery.persist_blocked_resolution(
                program_root,
                _load_prompt(arguments.prompt_file),
                _fresh_observation(repository),
            )
            return asdict(receipt)

        if phase == "prepare-closure":
            _install_failure_hook(program_closure, arguments.fail_label)
            receipt = program_closure.prepare_program_closure(
                program_root, _fresh_observation(repository)
            )
            return {
                **asdict(receipt),
                "prompt": program_closure.render_program_closure_prompt(program_root),
            }

        if phase == "activate-to-diff":
            prompt = _load_prompt(arguments.prompt_file)
            observation = _fresh_observation(repository)
            program_activation.activate_program(program_root, prompt, observation)
            observation = _fresh_observation(repository)
            preparation = program_activation.prepare_exact_plan(
                program_root, _exact_plan_bytes(program_root, observation), observation
            )
            if preparation.plan_prompt is None:
                raise ValueError("standard lifecycle fixture requires exact-plan approval")
            observation = _fresh_observation(repository)
            program_activation.materialize_exact_plan(
                program_root, preparation.plan_prompt, observation
            )
            observation = _fresh_observation(repository)
            program_activation.advance_execution_state(
                program_root, "implementing", observation
            )
            (repository / "archive-output.txt").write_text(
                "verified archive output\n", encoding="utf-8"
            )
            write_raw_review_reports(repository)
            observation = _fresh_observation(repository)
            program_activation.advance_execution_state(
                program_root, "reviewing", observation
            )
            observation = _fresh_observation(repository)
            receipt = program_review.persist_review_preparation(
                program_root, observation
            )
            return {
                **asdict(receipt),
                "prompt": diff_disposition.render_diff_disposition_prompt(program_root),
            }

        if phase == "accept-and-prepare-closure":
            observation = _fresh_observation(repository)
            accepted = diff_disposition.persist_accept_stop(
                program_root, _load_prompt(arguments.prompt_file), observation
            )
            observation = _fresh_observation(repository)
            prepared = program_closure.prepare_program_closure(
                program_root, observation
            )
            return {
                "increment_state": accepted.increment_state,
                "program_state": prepared.program_state,
                "prompt": program_closure.render_program_closure_prompt(program_root),
            }

        if phase == "close":
            _install_failure_hook(program_closure, arguments.fail_label)
            observation = _fresh_observation(repository)
            receipt = program_closure.persist_program_closure(
                program_root, _load_prompt(arguments.prompt_file), observation
            )
            return asdict(receipt)
        raise ValueError(f"unsupported lifecycle phase: {phase}")
    finally:
        sys.path.remove(str(script_root))


def _validate_compatibility_fixture_inventory() -> None:
    inventory = json.loads(
        (COMPATIBILITY_FIXTURE / "inventory.json").read_text(encoding="utf-8")
    )
    expected = {
        item["path"]: item["sha256"] for item in inventory.get("files", [])
    }
    actual: dict[str, str] = {}
    for path in sorted(COMPATIBILITY_FIXTURE.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"compatibility fixture contains symlink: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"compatibility fixture contains special path: {path}")
        relative = path.relative_to(COMPATIBILITY_FIXTURE).as_posix()
        if relative == "inventory.json":
            continue
        actual[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError("compatibility fixture inventory mismatch")


def _normalize_path_bound_exact_plan(payload: bytes) -> bytes:
    normalized: list[str] = []
    for line in payload.decode("utf-8").splitlines():
        label = next(
            (
                prefix
                for prefix in (
                    "Workspace path: ",
                    "Workspace base: ",
                    "Workspace head: ",
                )
                if line.startswith(prefix)
            ),
            None,
        )
        normalized.append(line if label is None else f"{label}<PATH-BOUND>")
    return ("\n".join(normalized) + "\n").encode("utf-8")


def _validate_materialized_compatibility_state(
    fixture: BootstrapFixture, state: str
) -> None:
    frozen = COMPATIBILITY_FIXTURE / state / "program"
    for relative in (
        "manifest.json",
        "program/implementation-program.md",
        "program/traceability.json",
        "source/implementation-plan.md",
        "source/source-metadata.json",
    ):
        if (fixture.program_root / relative).read_bytes() != (frozen / relative).read_bytes():
            raise ValueError(f"materialized compatibility byte mismatch: {relative}")
    relative_plan = "increments/ARCHIVE-INDEX/exact-file-plan.md"
    if _normalize_path_bound_exact_plan(
        (fixture.program_root / relative_plan).read_bytes()
    ) != _normalize_path_bound_exact_plan((frozen / relative_plan).read_bytes()):
        raise ValueError("materialized compatibility exact-plan mismatch")
    status = json.loads(
        (fixture.program_root / "state/status.json").read_text(encoding="utf-8")
    )
    expected = {
        "awaiting-diff": "awaiting-diff-approval",
        "accepted-stop": "accepted",
    }[state]
    if status.get("current_increment_state") != expected:
        raise ValueError("materialized compatibility state mismatch")


def materialize_v0_1_1_compatibility_state(state: str) -> BootstrapFixture:
    """Materialize one live path-bound v0.1.1 state through production writers."""
    if state not in {"awaiting-diff", "accepted-stop"}:
        raise ValueError("compatibility state must be awaiting-diff or accepted-stop")
    _validate_compatibility_fixture_inventory()
    fixture = BootstrapFixture()

    def run(phase: str, prompt: str | None = None) -> dict[str, object]:
        prompt_path = None
        if prompt is not None:
            prompt_path = fixture.root / f"compatibility-{phase}-prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
        return run_lifecycle_phase(
            argparse.Namespace(
                phase=phase,
                repository=str(fixture.repository),
                candidate=str(fixture.candidate),
                source_plan=str(fixture.source_plan),
                source_sha256=fixture.source_sha256,
                prompt_file=None if prompt_path is None else str(prompt_path),
                fail_label=None,
            )
        )

    try:
        published = run("publish")
        awaiting = run("activate-to-diff", str(published["prompt"]))
        if state == "accepted-stop":
            run("accept", str(awaiting["prompt"]))
        _validate_materialized_compatibility_state(fixture, state)
        return fixture
    except BaseException:
        fixture.close()
        raise


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="program_bootstrap_support.py")
    parser.add_argument(
        "phase",
        choices=(
            "publish",
            "activate",
            "prepare-plan",
            "render-exact-plan",
            "materialize-plan",
            "implementing",
            "reviewing",
            "prepare-review",
            "accept",
            "render-accept-stop",
            "render-accept-continue",
            "dispose-diff",
            "render-later-continuation",
            "rollover",
            "block",
            "render-block-resolution",
            "resolve-block",
            "prepare-closure",
            "activate-to-diff",
            "accept-and-prepare-closure",
            "close",
        ),
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--source-plan", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--prompt-file")
    parser.add_argument("--fail-label")
    parser.add_argument("--exact-plan-file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(
        list(sys.argv[1:] if argv is None else argv)
    )
    try:
        value = run_lifecycle_phase(arguments)
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
