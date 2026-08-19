import hashlib
import argparse
from dataclasses import asdict
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
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


def raw_review_report(scope: str) -> dict[str, object]:
    """Return one deterministic raw first-increment review report fixture."""
    value: dict[str, object] = {
        "schema_version": "implementation-raw-review-report/v1",
        "scope": scope,
        "program_id": "ARCHIVE-PROGRAM",
        "program_revision": 1,
        "increment_id": "ARCHIVE-INDEX",
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


def write_raw_review_reports(repository: Path) -> None:
    reviews = Path(repository) / "reviews"
    reviews.mkdir(exist_ok=True)
    for scope in ("requirements", "architecture", "test-evidence"):
        (reviews / f"{scope}.json").write_bytes(canonical_json(raw_review_report(scope)))


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
    create = sorted(
        {
            "archive-output.txt",
            "reviews/architecture.json",
            "reviews/requirements.json",
            "reviews/test-evidence.json",
            *(item.path for item in required if item.disposition == "Create"),
        }
    )
    modify = sorted(item.path for item in required if item.disposition == "Modify")
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
        ("Preserve", ["catalog.txt"]),
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
            "- requirements: `reviews/requirements.json`",
            "- architecture: `reviews/architecture.json`",
            "- test-evidence: `reviews/test-evidence.json`",
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
        import program_activation
        import program_bootstrap
        import program_closure
        import program_launch
        import program_review

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
            receipt = program_activation.prepare_exact_plan(
                program_root, _exact_plan_bytes(program_root, observation), observation
            )
            return asdict(receipt)

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
                (repository / "archive-output.txt").write_text(
                    "verified archive output\n", encoding="utf-8"
                )
                write_raw_review_reports(repository)
            receipt = program_activation.advance_execution_state(
                program_root, phase, _fresh_observation(repository)
            )
            return asdict(receipt)

        if phase == "prepare-review":
            _install_failure_hook(program_review, arguments.fail_label)
            receipt = program_review.persist_review_preparation(
                program_root, _fresh_observation(repository)
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
            "materialize-plan",
            "implementing",
            "reviewing",
            "prepare-review",
            "accept",
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
