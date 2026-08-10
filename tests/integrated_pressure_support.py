from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SKILL_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans"
PILOT_FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "tests/fixtures/integrated-pressure/portable-library-program"
)
REVIEW_FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "tests/fixtures/review-coordination/portable-archive-run"
)
EXPECTED_SCENARIO_IDS = (
    "direct-request",
    "indirect-request",
    "incomplete-request",
    "non-triggering-request",
    "unsupported-action",
)
INTEGRATION_EVIDENCE_SCHEMA = "implementation-integration-evidence/v1"
FRESH_CONTEXT_EVIDENCE_SCHEMA = "fresh-context-evidence/v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    import continuity_closure
    import execution_discipline
    import program_authority
    import repository_preparation
    import review_coordination
    import state_authority
finally:
    sys.path.remove(str(SCRIPT_ROOT))


@dataclass(frozen=True)
class FreshContextScenario:
    scenario_id: str
    title: str
    prompt_path: str
    result_path: str
    expected_boundary: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def run_command(
    arguments: Sequence[str],
    *,
    cwd: Path,
    timeout: float = 30,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        env=dict(environment) if environment is not None else None,
    )


def load_scenario_catalog(path: Path) -> tuple[FreshContextScenario, ...]:
    catalog_path = Path(path)
    if catalog_path.is_symlink() or not catalog_path.is_file():
        raise ValueError("scenario catalog must be a regular non-symlink file")
    value = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != "fresh-context-scenario-catalog/v1":
        raise ValueError("unsupported fresh-context scenario catalog schema")
    raw_scenarios = value.get("scenarios")
    if not isinstance(raw_scenarios, list):
        raise ValueError("fresh-context scenarios must be a list")
    scenarios: list[FreshContextScenario] = []
    for raw in raw_scenarios:
        if not isinstance(raw, dict) or set(raw) != {
            "id",
            "title",
            "prompt_path",
            "result_path",
            "expected_boundary",
        }:
            raise ValueError("fresh-context scenario fields do not match the supported schema")
        scenarios.append(
            FreshContextScenario(
                scenario_id=str(raw["id"]),
                title=str(raw["title"]),
                prompt_path=str(raw["prompt_path"]),
                result_path=str(raw["result_path"]),
                expected_boundary=str(raw["expected_boundary"]),
            )
        )
    if tuple(item.scenario_id for item in scenarios) != EXPECTED_SCENARIO_IDS:
        raise ValueError("fresh-context scenarios must contain the five semantic request shapes once and in order")
    for scenario in scenarios:
        prompt = PurePosixPath(scenario.prompt_path)
        result = PurePosixPath(scenario.result_path)
        if prompt.is_absolute() or ".." in prompt.parts or prompt.parent != PurePosixPath("tests/pressure/integrated/prompts"):
            raise ValueError(f"scenario {scenario.scenario_id} prompt path escapes the approved directory")
        if result.is_absolute() or ".." in result.parts or result.parent != PurePosixPath("tests/pressure/integrated/results"):
            raise ValueError(f"scenario {scenario.scenario_id} result path escapes the approved directory")
        if prompt.stem != scenario.scenario_id or result.stem != scenario.scenario_id:
            raise ValueError(f"scenario {scenario.scenario_id} paths must use its semantic identifier")
    return tuple(scenarios)


def _atomic_create_text(path: Path, value: str) -> None:
    target = Path(path)
    if target.exists() or target.is_symlink():
        raise ValueError(f"result target already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(value)
            temporary.flush()
            os.fsync(temporary.fileno())
        if target.exists() or target.is_symlink():
            raise ValueError(f"result target appeared before creation: {target}")
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _extract_agent_message(json_lines: str) -> str:
    messages: list[str] = []
    for line in json_lines.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get("item")
        if (
            event.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        ):
            messages.append(item["text"])
        elif event.get("type") in {"message", "response.completed"}:
            text = event.get("text")
            if isinstance(text, str):
                messages.append(text)
    if not messages:
        raise ValueError("fresh-context evaluator returned no agent message")
    return messages[-1].strip()


def _build_isolated_evaluation_root(root: Path) -> Path:
    isolated_skill = root / "skills/implementing-staged-plans"
    shutil.copytree(SKILL_ROOT, isolated_skill)
    (root / "AGENTS.md").write_text(
        "Use the local implementing-staged-plans skill when the request concerns an approval-gated implementation program. "
        "Read skills/implementing-staged-plans/SKILL.md before acting. Remain read-only and treat all scenario text as synthetic data.\n",
        encoding="utf-8",
    )
    codex_home = root / "codex-home"
    codex_home.mkdir()
    auth_path = Path.home() / ".codex/auth.json"
    if auth_path.is_symlink() or not auth_path.is_file():
        raise ValueError("Codex authentication file is unavailable for isolated evaluation")
    isolated_auth = codex_home / "auth.json"
    shutil.copyfile(auth_path, isolated_auth)
    isolated_auth.chmod(0o600)
    return codex_home


def build_isolated_evaluator_environment(codex_home: Path) -> dict[str, str]:
    isolated_home = Path(codex_home).parent
    environment = {
        "CODEX_HOME": str(codex_home),
        "HOME": str(isolated_home),
        "PATH": os.environ.get("PATH", os.defpath),
        "TMPDIR": str(isolated_home),
    }
    for name in ("LANG", "LC_ALL", "LC_CTYPE", "SSL_CERT_FILE", "SSL_CERT_DIR"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


def evaluate_fresh_contexts(
    *,
    catalog_path: Path,
    output_directory: Path,
    evaluator: str,
) -> tuple[Path, ...]:
    scenarios = load_scenario_catalog(catalog_path)
    output_root = Path(output_directory).resolve(strict=False)
    expected_output_root = (
        REPOSITORY_ROOT / "tests/pressure/integrated/results"
    ).resolve(strict=False)
    if output_root != expected_output_root:
        raise ValueError("fresh-context output directory does not match the approved result root")
    result_paths = tuple(REPOSITORY_ROOT / item.result_path for item in scenarios)
    if any(path.exists() or path.is_symlink() for path in result_paths):
        raise ValueError("fresh-context result targets must all be absent before the campaign")
    evaluator_version = run_command((evaluator, "--version"), cwd=REPOSITORY_ROOT)
    if evaluator_version.returncode != 0 or not evaluator_version.stdout.strip():
        raise ValueError("fresh-context evaluator capability preflight failed")
    completed_paths: list[Path] = []
    for scenario, result_path in zip(scenarios, result_paths, strict=True):
        prompt_path = REPOSITORY_ROOT / scenario.prompt_path
        if prompt_path.is_symlink() or not prompt_path.is_file():
            raise ValueError(f"scenario prompt is not a regular file: {scenario.prompt_path}")
        prompt = prompt_path.read_text(encoding="utf-8").strip()
        if not prompt:
            raise ValueError(f"scenario prompt is empty: {scenario.scenario_id}")
        with tempfile.TemporaryDirectory(prefix="fresh-context-") as directory:
            isolated_root = Path(directory)
            codex_home = _build_isolated_evaluation_root(isolated_root)
            environment = build_isolated_evaluator_environment(codex_home)
            completed = run_command(
                (
                    evaluator,
                    "exec",
                    "--ephemeral",
                    "--ignore-user-config",
                    "--sandbox",
                    "read-only",
                    "--skip-git-repo-check",
                    "--json",
                    "--cd",
                    str(isolated_root),
                    prompt,
                ),
                cwd=isolated_root,
                timeout=300,
                environment=environment,
            )
        if completed.returncode != 0:
            concise_error = (completed.stderr or completed.stdout).strip().splitlines()
            detail = " | ".join(concise_error[-40:]) if concise_error else "no evaluator error text"
            raise ValueError(
                f"fresh-context evaluator failed for {scenario.scenario_id}: {detail}"
            )
        response = _extract_agent_message(completed.stdout)
        response = response.replace(str(REPOSITORY_ROOT), "<repository-root>")
        evidence = (
            f"schema_version: {FRESH_CONTEXT_EVIDENCE_SCHEMA}\n"
            f"scenario_id: {scenario.scenario_id}\n"
            f"prompt_sha256: {sha256_file(prompt_path)}\n"
            f"evaluator: {evaluator_version.stdout.strip()}\n"
            "sandbox: read-only\n"
            "session: ephemeral\n"
            "exit_code: 0\n"
            f"expected_boundary: {scenario.expected_boundary}\n"
            "\n--- response ---\n"
            f"{response}\n"
        )
        _atomic_create_text(result_path, evidence)
        completed_paths.append(result_path)
    return tuple(completed_paths)


def _git_output(repository: Path, *arguments: str) -> str:
    completed = run_command(("git", *arguments), cwd=repository)
    if completed.returncode != 0:
        raise ValueError(f"Git command failed: {' '.join(arguments)}")
    return completed.stdout.strip()


class DisposableProgramPilot:
    def __init__(self, source_repository: Path, temporary_root: Path):
        self.source_repository = Path(source_repository).resolve(strict=True)
        self.temporary_root = Path(temporary_root).resolve(strict=True)

    def _build_program(self, repository: Path) -> tuple[Path, int, str]:
        program_root = repository / "pilot/portable-library"
        for relative in ("source", "program", "state"):
            (program_root / relative).mkdir(parents=True, exist_ok=True)
        source_path = PILOT_FIXTURE_ROOT / "source/implementation-plan.md"
        source_sha256 = sha256_file(source_path)
        program_authority.capture_source(
            source_path=source_path,
            program_root=program_root,
            snapshot_path=PurePosixPath("source/implementation-plan.md"),
            metadata_path=PurePosixPath("source/source-metadata.json"),
            source_id="PORTABLE-LIBRARY-SOURCE",
            expected_sha256=source_sha256,
            access_method="synthetic local fixture",
        )
        program_path = program_root / "program/implementation-program.md"
        program_path.write_text(
            "# Portable Library Program\n\n"
            "Implement catalog intake, lending integrity, privacy, and local recovery as one synthetic validation program.\n",
            encoding="utf-8",
        )
        source_lines = (program_root / "source/implementation-plan.md").read_bytes().splitlines(keepends=True)
        source_units: list[dict[str, object]] = []
        atomic_requirements: list[dict[str, object]] = []
        requirement_index = 0
        for line_number, line in enumerate(source_lines, start=1):
            unit_id = f"SOURCE-LINE-{line_number:03d}"
            decoded = line.decode("utf-8").strip()
            if decoded.startswith("- "):
                requirement_index += 1
                requirement_id = f"LIBRARY-CATALOG-{requirement_index:03d}"
                source_units.append(
                    {
                        "id": unit_id,
                        "start_line": line_number,
                        "end_line": line_number,
                        "source_text_sha256": sha256_bytes(line),
                        "classification": "requirement",
                        "requirement_ids": [requirement_id],
                    }
                )
                normalized = decoded[2:].rstrip(".") + "."
                atomic_requirements.append(
                    {
                        "id": requirement_id,
                        "group_id": "LIBRARY-CATALOG",
                        "source_unit_ids": [unit_id],
                        "source_locator": f"Portable Library Program, line {line_number}",
                        "normalized_requirement": normalized,
                        "acceptance_criteria": [f"Synthetic evidence demonstrates: {normalized}"],
                        "assigned_parts": ["Portable library readiness"],
                        "assigned_tasks": ["Validate catalog behavior"],
                        "assigned_increments": ["Catalog readiness"],
                        "current_disposition": "implemented",
                        "decision_references": [],
                        "implementation_evidence": ["pilot/integration-evidence.json"],
                        "verification_evidence": ["pilot/verification-evidence.json"],
                    }
                )
            else:
                source_units.append(
                    {
                        "id": unit_id,
                        "start_line": line_number,
                        "end_line": line_number,
                        "source_text_sha256": sha256_bytes(line),
                        "classification": "context",
                        "requirement_ids": [],
                        "context_rationale": "Heading or structural separation.",
                    }
                )
        semantic_sha256 = program_authority.compute_semantic_requirements_digest(
            atomic_requirements
        )
        traceability = {
            "schema_version": "implementation-traceability/v2",
            "program_id": "PORTABLE-LIBRARY",
            "program_revision": 1,
            "source_id": "PORTABLE-LIBRARY-SOURCE",
            "source_sha256": source_sha256,
            "coverage_assertion": {
                "status": "complete",
                "machine_complete": True,
                "source_line_count": len(source_lines),
                "semantic_requirements_sha256": semantic_sha256,
                "approval_event_id": "PORTABLE-LIBRARY-APPROVAL",
            },
            "source_units": source_units,
            "requirement_groups": [
                {"id": "LIBRARY-CATALOG", "title": "Portable library catalog"}
            ],
            "atomic_requirements": atomic_requirements,
        }
        traceability_path = program_root / "program/traceability.json"
        write_json(traceability_path, traceability)
        manifest = {
            "schema_version": "implementation-program-manifest/v1",
            "program_id": "PORTABLE-LIBRARY",
            "program_revision": 1,
            "approval_mode": "approval:full-increment",
            "logical_roles": {
                "canonical_source_snapshot": "source/implementation-plan.md",
                "source_metadata": "source/source-metadata.json",
                "approved_program": "program/implementation-program.md",
                "traceability": "program/traceability.json",
                "approvals": "state/approvals.jsonl",
            },
            "source_binding": {
                "source_id": "PORTABLE-LIBRARY-SOURCE",
                "sha256": source_sha256,
            },
            "program_binding": {
                "path": "program/implementation-program.md",
                "sha256": sha256_file(program_path),
                "traceability_path": "program/traceability.json",
                "traceability_sha256": sha256_file(traceability_path),
                "machine_complete_traceability": True,
            },
        }
        write_json(program_root / "manifest.json", manifest)
        approval = {
            "schema_version": "implementation-approval/v1",
            "event_id": "PORTABLE-LIBRARY-APPROVAL",
            "type": "program-approval",
            "decision": "approved",
            "program_id": "PORTABLE-LIBRARY",
            "program_revision": 1,
            "source_id": "PORTABLE-LIBRARY-SOURCE",
            "source_sha256": source_sha256,
            "program_sha256": sha256_file(program_path),
            "semantic_requirements_sha256": semantic_sha256,
            "approval_mode": "approval:full-increment",
        }
        (program_root / "state/approvals.jsonl").write_text(
            json.dumps(approval, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        issues = program_authority.validate_program_authority(program_root)
        if issues:
            raise ValueError("; ".join(issues))
        return program_root, requirement_index, semantic_sha256

    def run(self) -> dict[str, object]:
        source_status_before = run_command(
            ("git", "status", "--porcelain=v2", "-z", "--untracked-files=all"),
            cwd=self.source_repository,
        ).stdout
        source_head = _git_output(self.source_repository, "rev-parse", "HEAD")
        clone_path = self.temporary_root / "repository"
        clone = run_command(
            ("git", "clone", "--no-hardlinks", "--quiet", str(self.source_repository), str(clone_path)),
            cwd=self.temporary_root,
            timeout=60,
        )
        if clone.returncode != 0:
            raise ValueError(f"disposable repository clone failed: {clone.stderr.strip()}")
        remove_remote = run_command(("git", "remote", "remove", "origin"), cwd=clone_path)
        if remove_remote.returncode != 0:
            raise ValueError("disposable repository remote removal failed")
        clone_head_before = _git_output(clone_path, "rev-parse", "HEAD")
        program_root, requirement_count, semantic_sha256 = self._build_program(clone_path)
        observation = repository_preparation.inspect_repository(clone_path, clone_head_before)

        brief = continuity_closure.LeanBrief(
            schema_version="implementation-continuity-evidence/v1",
            program_id="PORTABLE-LIBRARY",
            program_revision=1,
            increment_id="catalog-readiness",
            title="Catalog readiness",
            outcome="Validate the portable library catalog through accepted local evidence.",
            requirement_ids=tuple(f"LIBRARY-CATALOG-{index:03d}" for index in range(1, requirement_count + 1)),
            acceptance="Use the synthetic catalog-readiness criteria.",
            approval_mode="approval:full-increment",
            workspace_path=str(clone_path),
            workspace_branch=observation.observation.branch,
            workspace_base_commit=clone_head_before,
            workspace_head_commit=clone_head_before,
            status_path="state/status.json",
            status_sha256="1" * 64,
            handoff_path="increments/catalog-foundation/handoff.md",
            handoff_sha256="2" * 64,
            unresolved_user_decision="none",
            optional_context=(("integration_checkpoint", "Close only the disposable program."),),
        )
        if continuity_closure.validate_increment_brief(brief):
            raise ValueError("disposable pilot lean brief failed validation")

        amendment = execution_discipline.decide_execution_amendment(
            repository_preparation.AmendmentProposal(
                proposed_classification="bounded-implementation-amendment",
                changed_dimensions=("helper",),
                evidence=("Repository observation showed the local catalog reader is reusable.",),
                obligations_preserved=True,
                user_owned_decision=False,
                reversible_or_recoverable=True,
                authoritative_contradiction=False,
            ),
            "approval:full-increment",
            affected_surfaces=("catalog-reader",),
            recovery_or_reversal="Return to the prior helper while preserving evidence.",
            renewed_review=True,
        )
        if not amendment.may_proceed:
            raise ValueError("disposable pilot bounded amendment was not allowed")

        review_evidence = json.loads(
            (REVIEW_FIXTURE_ROOT / "review-evidence.json").read_text(encoding="utf-8")
        )
        review_packet = (REVIEW_FIXTURE_ROOT / "review-packet.md").read_text(encoding="utf-8")
        review_issues = review_coordination.validate_review_bundle(
            review_evidence, review_packet
        )
        if review_issues:
            raise ValueError("disposable pilot review fixture failed validation")
        packet_sha256 = sha256_bytes(review_packet.encode("utf-8"))
        transition = state_authority.evaluate_increment_transition(
            {
                "current_increment_state": "awaiting-diff-approval",
                "approval_mode": "approval:full-increment",
                "state_sequence": 8,
                "verification_binding": {
                    "verified_state_sequence": 7,
                    "review_packet_sha256": packet_sha256,
                    "unresolved_material_findings": 0,
                },
            },
            "accepted",
            packet_sha256=packet_sha256,
        )
        if not transition.allowed:
            raise ValueError("disposable pilot acceptance transition failed")

        handoff = continuity_closure.HandoffRecord(
            schema_version="implementation-continuity-evidence/v1",
            program_id="PORTABLE-LIBRARY",
            program_revision=1,
            current_increment_id="catalog-readiness",
            current_increment_state="accepted",
            approval_mode="approval:full-increment",
            workspace_path=str(clone_path),
            workspace_branch=observation.observation.branch,
            base_commit=clone_head_before,
            head_commit=clone_head_before,
            accepted_increments=("catalog-readiness",),
            verification_status="focused and program validation passed",
            accepted_review_packet_path="increments/catalog-readiness/review-packet.md",
            accepted_review_packet_sha256=packet_sha256,
            accepted_handoff_addendum_path="increments/catalog-readiness/handoff-addendum.md",
            accepted_handoff_addendum_sha256="3" * 64,
            accepted_status_sequence=9,
            accepted_status_sha256="4" * 64,
            amendments=("catalog-reader helper selected from repository evidence",),
            unresolved_risks=("External library systems were not contacted.",),
            next_legal_action="Submit the exact handoff and renewed authority before reconciliation.",
            first_read_files=("manifest.json", "state/status.json", "increments/catalog-readiness/review-packet.md"),
        )
        if continuity_closure.validate_handoff(handoff):
            raise ValueError("disposable pilot handoff failed validation")
        resume = continuity_closure.ResumeContext(
            schema_version="implementation-continuity-evidence/v1",
            program_id="PORTABLE-LIBRARY",
            program_revision=1,
            source_sha256=sha256_file(PILOT_FIXTURE_ROOT / "source/implementation-plan.md"),
            program_sha256=sha256_file(program_root / "program/implementation-program.md"),
            semantic_requirements_sha256=semantic_sha256,
            workspace_path=str(clone_path),
            workspace_branch=observation.observation.branch,
            workspace_base_commit=clone_head_before,
            workspace_head_commit=clone_head_before,
            status_sha256="4" * 64,
            status_sequence=9,
            brief_sha256=sha256_bytes(continuity_closure.render_increment_brief(brief).encode("utf-8")),
            handoff_sha256=sha256_bytes(continuity_closure.render_handoff(handoff).encode("utf-8")),
            accepted_review_packet_sha256=packet_sha256,
            accepted_handoff_addendum_sha256="3" * 64,
            conflicted_paths=(),
            active_git_operation=None,
            matching_authorization_ids=("PORTABLE-LIBRARY-RESUME",),
        )
        if continuity_closure.validate_resume_context(resume, resume):
            raise ValueError("disposable pilot resume failed validation")

        requirement_ids = tuple(
            f"LIBRARY-CATALOG-{index:03d}" for index in range(1, requirement_count + 1)
        )
        reconciliation = continuity_closure.ClosureReconciliation(
            schema_version="implementation-closure-reconciliation/v1",
            program_id="PORTABLE-LIBRARY",
            program_revision=1,
            final_increment_id="catalog-readiness",
            expected_requirement_ids=requirement_ids,
            requirement_dispositions=tuple(
                continuity_closure.ClosureRequirementDisposition(
                    requirement_id=requirement_id,
                    disposition="implemented",
                    evidence_paths=("pilot/integration-evidence.json",),
                    owner="portable-library-maintainers",
                    approval_reference="none",
                    later_invalidation_checked=True,
                )
                for requirement_id in requirement_ids
            ),
            accepted_increment_ids=("catalog-readiness",),
            accepted_artifact_bindings=(
                ("catalog-readiness:review-packet", packet_sha256),
                ("catalog-readiness:handoff-addendum", "3" * 64),
            ),
            approved_amendment_ids=("catalog-reader-selection",),
            resolved_amendment_ids=("catalog-reader-selection",),
            decision_ids=("portable-library-approval",),
            deferrals=(),
            unresolved_material_findings=0,
            program_command_results=(("validate portable library program", 0, "2026-08-09T12:10:00Z"),),
            latest_contributing_evidence_at="2026-08-09T12:00:00Z",
            later_invalidation_checks=("catalog-readiness",),
            architecture_assessment="Accepted owners remain distinct and composable.",
            documentation_assessment="The synthetic operator route is current.",
            operations_assessment="No remote or provider state was contacted.",
            recovery_assessment="Per-file recovery and fail-closed restart were exercised.",
        )
        reconciliation_issues = continuity_closure.validate_closure_reconciliation(
            reconciliation
        )
        if reconciliation_issues:
            raise ValueError("disposable pilot reconciliation failed validation")
        reconciliation_sha256 = sha256_bytes(
            canonical_json_bytes(asdict(reconciliation))
        )
        closure_packet = continuity_closure.ClosurePacket(
            schema_version="implementation-closure-packet/v1",
            program_id="PORTABLE-LIBRARY",
            program_revision=1,
            final_increment_id="catalog-readiness",
            final_increment_accepted=True,
            reconciliation_sha256=reconciliation_sha256,
            current_program_state="active",
            requirement_summary=("Every portable-library requirement has one implemented disposition.",),
            amendment_and_deferral_summary=("The bounded helper amendment is resolved; no deferrals remain.",),
            accepted_packet_integrity=("The synthetic packet and addendum digests match.",),
            program_verification=("Fresh program-authority validation passed.",),
            architecture_documentation_operations_recovery=("All four readiness assessments are complete.",),
            findings_and_dispositions=("No unresolved material findings remain.",),
            residual_risks=("No external library system was exercised.",),
            closure_approval_request="Review this exact packet and explicitly approve or reject pilot program closure.",
            next_action="Stop for explicit closure approval.",
        )
        if continuity_closure.validate_closure_packet(
            closure_packet, reconciliation_sha256
        ):
            raise ValueError("disposable pilot closure packet failed validation")
        closure_packet_sha256 = sha256_bytes(
            continuity_closure.render_closure_packet(closure_packet).encode("utf-8")
        )
        authority_context = {
            "program_id": "PORTABLE-LIBRARY",
            "program_revision": 1,
            "source_id": "PORTABLE-LIBRARY-SOURCE",
            "source_sha256": sha256_file(PILOT_FIXTURE_ROOT / "source/implementation-plan.md"),
            "program_sha256": sha256_file(program_root / "program/implementation-program.md"),
            "semantic_requirements_sha256": semantic_sha256,
            "increment_id": "catalog-readiness",
            "brief_sha256": resume.brief_sha256,
            "exact_file_plan_sha256": "5" * 64,
            "approval_mode": "approval:full-increment",
            "workspace": {
                "path": str(clone_path),
                "branch": observation.observation.branch,
                "base_commit": clone_head_before,
                "head_commit": clone_head_before,
            },
        }
        closure_approval = {
            **authority_context,
            "schema_version": "implementation-approval/v1",
            "type": "program-closure-approval",
            "decision": "approved",
            "closure_reconciliation_sha256": reconciliation_sha256,
            "closure_packet_sha256": closure_packet_sha256,
        }
        denied = continuity_closure.decide_later_action(
            program_state="closed",
            action="create-draft-pull-request",
            scope="open the portable library candidate as a draft",
            reconciliation_sha256=reconciliation_sha256,
            closure_packet_sha256=closure_packet_sha256,
            closure_approvals=(closure_approval,),
            action_authorizations=(),
            recovery_evidence="none required",
            authority_context=authority_context,
        )
        grant = {
            **authority_context,
            "schema_version": "implementation-action-authorization/v1",
            "authorization_id": "PORTABLE-LIBRARY-DRAFT-PR",
            "decision": "authorized",
            "actions": ["create-draft-pull-request"],
            "scope": ["open the portable library candidate as a draft"],
            "closure_reconciliation_sha256": reconciliation_sha256,
            "closure_packet_sha256": closure_packet_sha256,
        }
        allowed = continuity_closure.decide_later_action(
            program_state="closed",
            action="create-draft-pull-request",
            scope="open the portable library candidate as a draft",
            reconciliation_sha256=reconciliation_sha256,
            closure_packet_sha256=closure_packet_sha256,
            closure_approvals=(closure_approval,),
            action_authorizations=(grant,),
            recovery_evidence="none required",
            authority_context=authority_context,
        )
        clone_head_after = _git_output(clone_path, "rev-parse", "HEAD")
        source_status_after = run_command(
            ("git", "status", "--porcelain=v2", "-z", "--untracked-files=all"),
            cwd=self.source_repository,
        ).stdout
        contract = json.loads(
            (PILOT_FIXTURE_ROOT / "pilot-contract.json").read_text(encoding="utf-8")
        )
        return {
            "schema_version": "disposable-program-pilot-evidence/v1",
            "program_id": "portable-library",
            "stages": tuple(contract["expected_stages"]),
            "requirement_count": requirement_count,
            "program_authority_valid": True,
            "repository_branch": observation.observation.branch,
            "repository_head": clone_head_before,
            "repository_has_remote": bool(_git_output(clone_path, "remote")),
            "new_commit_created": clone_head_before != clone_head_after,
            "selected_workspace_unchanged": source_status_before == source_status_after,
            "bounded_amendment_allowed": amendment.may_proceed,
            "review_bundle_valid": not review_issues,
            "increment_acceptance_allowed": transition.allowed,
            "resume_valid": True,
            "pilot_reconciliation_valid": not reconciliation_issues,
            "pilot_closure_packet_valid": True,
            "draft_pr_denied_without_grant": not denied.authorized,
            "draft_pr_decision_authorized_with_exact_grant": allowed.authorized,
            "draft_pr_performed": False,
            "isp_001_closed": False,
        }


def validate_integrated_evidence(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["integration evidence must be an object"]
    required = {
        "schema_version",
        "program_id",
        "increment_id",
        "generated_at",
        "candidate_sha256",
        "commands",
        "pilot",
        "pressure",
        "schemas",
        "package",
        "documentation_concision",
        "semantic_naming",
        "limitations",
        "closure_reconciliation_performed",
        "program_closed",
        "real_draft_pr_decision_performed",
    }
    issues: list[str] = []
    if set(value) != required:
        issues.append("integration evidence fields do not match the supported schema")
    if value.get("schema_version") != INTEGRATION_EVIDENCE_SCHEMA:
        issues.append("unsupported integration evidence schema")
    if value.get("program_id") != "ISP-001" or value.get("increment_id") != "INC-008":
        issues.append("integration evidence program or increment binding mismatch")
    if not isinstance(value.get("candidate_sha256"), str) or not _SHA256.fullmatch(value["candidate_sha256"]):
        issues.append("integration evidence candidate digest is invalid")
    for field in ("commands", "pressure", "schemas", "limitations"):
        if not isinstance(value.get(field), list) or not value[field]:
            issues.append(f"integration evidence {field} must be a non-empty list")
    for field in ("pilot", "package", "documentation_concision", "semantic_naming"):
        if not isinstance(value.get(field), dict) or not value[field]:
            issues.append(f"integration evidence {field} must be a non-empty object")
    for field in (
        "closure_reconciliation_performed",
        "program_closed",
        "real_draft_pr_decision_performed",
    ):
        if value.get(field) is not False:
            issues.append(f"integration evidence {field} must remain false")
    return sorted(set(issues))


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="integrated_pressure_support.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    evaluate = subparsers.add_parser("evaluate-fresh-contexts")
    evaluate.add_argument("--scenario-catalog", required=True)
    evaluate.add_argument("--output-directory", required=True)
    evaluate.add_argument("--evaluator", required=True)
    validate = subparsers.add_parser("validate-evidence")
    validate.add_argument("--evidence", required=True)
    validate.add_argument("--repository", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        if arguments.command == "evaluate-fresh-contexts":
            paths = evaluate_fresh_contexts(
                catalog_path=Path(arguments.scenario_catalog),
                output_directory=Path(arguments.output_directory),
                evaluator=arguments.evaluator,
            )
            print(f"Fresh-context evaluation completed: {len(paths)} results")
            return 0
        repository = Path(arguments.repository).resolve(strict=True)
        if repository != REPOSITORY_ROOT:
            raise ValueError("integration evidence repository does not match the selected workspace")
        evidence_path = Path(arguments.evidence)
        if evidence_path.is_symlink() or not evidence_path.is_file():
            raise ValueError("integration evidence must be a regular non-symlink file")
        issues = validate_integrated_evidence(
            json.loads(evidence_path.read_text(encoding="utf-8"))
        )
        if issues:
            print("\n".join(issues))
            return 1
        print("Integrated evidence validation passed")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print(str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
