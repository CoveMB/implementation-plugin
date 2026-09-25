import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest import mock

from tests.program_bootstrap_support import (
    BootstrapFixture,
    _exact_plan_bytes,
    canonical_json,
    canonical_compact_sha256,
    write_raw_review_reports,
    repository_snapshot,
    run_program_discovery,
)
from tests.script_module_support import load_script_module
from tests.test_program_activation import ACTIVATION, activated_program, exact_plan_bytes


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "blocked_recovery.py"
LIFECYCLE_SUPPORT_PATH = REPOSITORY_ROOT / "tests/program_bootstrap_support.py"

BLOCKED = load_script_module("blocked_recovery", SCRIPT_PATH)


def implementing_program():
    fixture = BootstrapFixture()
    fixture.configure_successors({"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)})
    program_root, observation = activated_program(fixture)
    plan = exact_plan_bytes(program_root, observation)
    prepared = ACTIVATION.prepare_exact_plan(program_root, plan, observation)
    ACTIVATION.materialize_exact_plan(
        program_root, prepared.plan_prompt, observation
    )
    ACTIVATION.advance_execution_state(program_root, "implementing", observation)
    fresh = ACTIVATION._without_owned_program_paths(
        program_root,
        ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation,
    )
    return fixture, program_root, fresh


def block_request(fixture: BootstrapFixture):
    return BLOCKED.BlockedTransitionRequest(
        reason_code="verification-environment-unavailable",
        recovery_criteria=(
            "The local verification environment is available.",
            "The preserved catalog evidence remains unchanged.",
        ),
        evidence_bindings=(
            BLOCKED.EvidenceBinding(
                path="catalog.txt",
                sha256=BLOCKED.sha256_file(fixture.repository / "catalog.txt"),
            ),
        ),
    )


def resolution_candidate(program_root: Path) -> dict[str, object]:
    status = json.loads(
        (program_root / "state/status.json").read_text(encoding="utf-8")
    )
    context = status["blocked_context"]
    return {
        "schema_version": BLOCKED.BLOCK_RESOLUTION_CANDIDATE_SCHEMA,
        "block_id": context["block_id"],
        "criterion_results": [
            {"criterion": criterion, "satisfied": True}
            for criterion in context["recovery_criteria"]
        ],
        "evidence_bindings": context["evidence_bindings"],
    }


RECOVERY_RISKS = (
    "security-privacy", "public-api-compatibility",
    "concurrency-reliability-distributed-state", "performance", "provider-external-state",
)


def specialist_program(*, recovery=True, terminal=False, preserve_reports=True, bounded_reports=True):
    """Synthetic blocked program; never reads the user's application data."""
    from tests.test_program_setup import BOOTSTRAP, SETUP

    fixture = BootstrapFixture()
    if not terminal:
        fixture.configure_successors({"ARCHIVE-VERIFY": ("ARCHIVE-INDEX",)})
    fixture.configure_setup_v3()
    manifest = fixture.load_json("manifest.json")
    for allocation in manifest["setup_semantics"]["operation_envelope"]["allocations"]:
        if preserve_reports and allocation["path"] == "reviews" and allocation["operation"] == "Modify":
            allocation["operation"] = "Preserve"
    if not bounded_reports:
        allocations = manifest["setup_semantics"]["operation_envelope"]["allocations"]
        report_class = next(item for item in allocations if item["path"] == "reviews" and item["operation"] == "Create")
        allocations.remove(report_class)
        allocations.extend(dict(report_class, kind="exact-path", path=f"reviews/{scope}.json") for scope in ("requirements", "architecture", "test-evidence"))
    manifest["setup_semantics_sha256"] = canonical_compact_sha256(manifest["setup_semantics"])
    fixture.write_json("manifest.json", manifest)
    BOOTSTRAP.publish_program_proposal(fixture.repository, fixture.source_plan, fixture.candidate, fixture.source_sha256)
    root = fixture.program_root
    observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
    activation = ACTIVATION.activate_program(root, SETUP.adapt_setup_decision(
        root, "Yes", role="user", provenance="direct-user-message"), observation)
    intent = SETUP.adapt_increment_start_intent(root, activation.handoff, role="user", provenance="direct-user-message")
    ACTIVATION.start_first_increment(root, intent, observation)
    observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
    prepared = ACTIVATION.prepare_exact_plan(
        root, _exact_plan_bytes(root, observation, () if recovery else RECOVERY_RISKS), observation
    )
    ACTIVATION.materialize_exact_plan(root, prepared.plan_prompt, observation)
    ACTIVATION.advance_execution_state(root, "implementing", observation)
    (fixture.repository / "archive-output.txt").write_text("preserved application result\n")
    if not recovery:
        write_raw_review_reports(fixture.repository, touched_predicates=RECOVERY_RISKS)
        return fixture, root, ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
    # Only the originally allocated three reports exist, with incomplete reconciliation.
    from tests.program_bootstrap_support import raw_review_report
    for scope in ("requirements", "architecture", "test-evidence"):
        path = fixture.repository / f"reviews/{scope}.json"
        path.parent.mkdir(exist_ok=True)
        value = raw_review_report(scope, touched_predicates=RECOVERY_RISKS)
        value["reconciled_at"] = ""
        path.write_bytes(canonical_json(value))
    observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
    evidence = tuple(BLOCKED.EvidenceBinding(path, BLOCKED.sha256_file(fixture.repository / path))
        for path in ("archive-output.txt", "reviews/requirements.json", "reviews/architecture.json", "reviews/test-evidence.json"))
    BLOCKED.block_current_program(root, BLOCKED.BlockedTransitionRequest(
        "review-report-allocation-incomplete",
        ("Original product and report evidence remains preserved.",
         "The report-only allocation repair fits the approved program envelope."), evidence), observation)
    return fixture, root, observation


def underallocated_program(**options):
    return specialist_program(**options)


def reviewed_specialist_program(*, recovery, terminal=False):
    from tests.test_program_review import REVIEW

    fixture, root, observation = specialist_program(recovery=recovery, terminal=terminal)
    if recovery:
        grant_review_allocation(root, observation)
        complete_allocated_reports(fixture, root)
    observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
    ACTIVATION.advance_execution_state(root, "reviewing", observation)
    REVIEW.persist_review_preparation(root, observation)
    return fixture, root, observation


def allocation_candidate(root):
    value = resolution_candidate(root)
    value["schema_version"] = "implementation-block-resolution-candidate/v2"
    for result in value["criterion_results"]:
        result["evidence"] = "The bound original files remain unchanged; the existing review path class covers the exact report additions and later retention."
    return value


def grant_review_allocation(root, observation):
    candidate = BLOCKED.build_block_resolution_candidate(root, allocation_candidate(root), observation)
    BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
    return candidate


def complete_allocated_reports(fixture, root):
    status = json.loads((root / "state/status.json").read_text())
    supplement = BLOCKED.validated_review_allocation_supplement(root, status)
    directory = str(Path(supplement["report_paths"]["requirements"]).parent)
    write_raw_review_reports(fixture.repository, relative_directory=directory, touched_predicates=RECOVERY_RISKS)
    return supplement


class BlockedRecoveryTests(unittest.TestCase):
    def discover(self, fixture: BootstrapFixture) -> dict[str, object]:
        return run_program_discovery(fixture.repository)

    def test_review_allocation_preserves_original_bytes_and_reaches_review(self):
        from tests.test_program_review import REVIEW
        fixture, root, observation = underallocated_program()
        self.addCleanup(fixture.close)
        before = repository_snapshot(fixture.repository)
        original_ledgers = {name: (root / "state" / name).read_bytes() for name in ("action-authorizations.jsonl", "block-resolutions.jsonl")}
        candidate = grant_review_allocation(root, observation)
        for name, original in original_ledgers.items():
            self.assertTrue((root / "state" / name).read_bytes().startswith(original))
        status = json.loads((root / "state/status.json").read_text())
        self.assertEqual(status["current_increment_state"], "implementing")
        supplement = BLOCKED.validated_review_allocation_supplement(root, status)
        self.assertEqual(len(supplement["report_paths"]), 8)
        self.assertEqual(candidate.action_record["actions"], ["allocate-review-reports", "resume-blocked-program"])
        for path in supplement["report_paths"].values():
            self.assertFalse((fixture.repository / path).exists())
        after = repository_snapshot(fixture.repository)
        changing = {"implementation-programs/ARCHIVE-PROGRAM/state/" + name
                    for name in ("status.json", "action-authorizations.jsonl", "block-resolutions.jsonl")}
        self.assertEqual({p: v for p, v in before.items() if p not in changing},
                         {p: v for p, v in after.items() if p not in changing})
        self.assertEqual(self.discover(fixture)["disposition"], "resume")
        complete_allocated_reports(fixture, root)
        observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
        ACTIVATION.advance_execution_state(root, "reviewing", observation)
        REVIEW.persist_review_preparation(root, observation)
        evidence = json.loads((root / "increments/ARCHIVE-INDEX/review-evidence.json").read_text())
        self.assertEqual(len(evidence["reports"]), 8)
        self.assertEqual(evidence["reports"][-1]["scope"], "specialist-provider")
        for path in ("reviews/requirements.json", "reviews/architecture.json", "reviews/test-evidence.json"):
            self.assertEqual(repository_snapshot(fixture.repository)[path], before[path])

    def test_ordinary_resolution_does_not_allocate_review_reports(self):
        fixture, root, observation = underallocated_program()
        self.addCleanup(fixture.close)
        candidate = BLOCKED.build_block_resolution_candidate(root, resolution_candidate(root), observation)
        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
        status = json.loads((root / "state/status.json").read_text())
        self.assertNotIn("review_allocation_binding", status)
        self.assertEqual(candidate.action_record["actions"], ["resume-blocked-program"])
        self.assertNotIn("review_allocation_supplement", candidate.resolution_record)

    def test_supplement_survives_second_block_and_ordinary_resume(self):
        for prior_state in ("implementing", "reviewing"):
            with self.subTest(prior_state=prior_state):
                fixture, root, observation = underallocated_program()
                try:
                    first = grant_review_allocation(root, observation)
                    supplement = complete_allocated_reports(fixture, root)
                    observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
                    if prior_state == "reviewing":
                        ACTIVATION.advance_execution_state(root, "reviewing", observation)
                    binding = json.loads((root / "state/status.json").read_text())["review_allocation_binding"]
                    allocation_prefix = (root / "state/block-resolutions.jsonl").read_bytes()
                    path = supplement["report_paths"]["specialist-provider"]
                    request = BLOCKED.BlockedTransitionRequest("verification-environment-unavailable", ("Local verification is available.",),
                        (BLOCKED.EvidenceBinding(path, BLOCKED.sha256_file(fixture.repository / path)),))
                    BLOCKED.block_current_program(root, request, observation)
                    status = json.loads((root / "state/status.json").read_text())
                    self.assertNotIn("block_resolution_binding", status)
                    self.assertEqual(status["review_allocation_binding"], binding)
                    self.assertEqual(self.discover(fixture)["disposition"], "blocked-recovery-ready")
                    before = repository_snapshot(root)
                    with self.assertRaises(ValueError):
                        BLOCKED.persist_blocked_resolution(root, first.prompt, observation)
                    self.assertEqual(repository_snapshot(root), before)
                    later = BLOCKED.build_block_resolution_candidate(root, resolution_candidate(root), observation)
                    self.assertEqual(later.action_record["actions"], ["resume-blocked-program"])
                    self.assertNotIn("review_allocation_supplement", later.resolution_record)
                    BLOCKED.persist_blocked_resolution(root, later.prompt, observation)
                    status = json.loads((root / "state/status.json").read_text())
                    self.assertEqual(status["current_increment_state"], prior_state)
                    self.assertEqual(status["review_allocation_binding"], binding)
                    self.assertTrue((root / "state/block-resolutions.jsonl").read_bytes().startswith(allocation_prefix))
                    self.assertEqual(BLOCKED.validated_review_allocation_supplement(root, status), supplement)
                    self.assertEqual(self.discover(fixture)["disposition"], "resume")
                finally:
                    fixture.close()

    def test_allocation_preflights_divergent_resolution_before_action_write(self):
        fixture, root, observation = underallocated_program()
        self.addCleanup(fixture.close)
        candidate = BLOCKED.build_block_resolution_candidate(root, allocation_candidate(root), observation)
        divergent = dict(candidate.resolution_record, restored_increment_state="reviewing")
        (root / "state/block-resolutions.jsonl").write_bytes(BLOCKED._canonical_json_line(divergent))
        before = repository_snapshot(root)
        with self.assertRaises(ValueError):
            BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
        self.assertEqual(repository_snapshot(root), before)

    def test_later_resume_identifier_collisions_reject_before_any_write(self):
        fixture, root, observation = underallocated_program()
        self.addCleanup(fixture.close)
        grant_review_allocation(root, observation)
        supplement = complete_allocated_reports(fixture, root)
        observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
        path = supplement["report_paths"]["specialist-provider"]
        BLOCKED.block_current_program(root, BLOCKED.BlockedTransitionRequest(
            "verification-environment-unavailable", ("Local verification is available.",),
            (BLOCKED.EvidenceBinding(path, BLOCKED.sha256_file(fixture.repository / path)),)), observation)
        candidate = BLOCKED.build_block_resolution_candidate(root, resolution_candidate(root), observation)
        for name, record in (("action-authorizations.jsonl", candidate.action_record),
                             ("block-resolutions.jsonl", candidate.resolution_record)):
            with self.subTest(ledger=name):
                ledger = root / "state" / name
                original = ledger.read_bytes()
                ledger.write_bytes(original + BLOCKED._canonical_json_line(dict(record, block_id="different-block")))
                try:
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                    self.assertNotEqual(self.discover(fixture)["disposition"], "blocked-resolution-retry-ready")
                finally:
                    ledger.write_bytes(original)

    def test_completed_later_resume_rejects_divergent_authority_bytes(self):
        fixture, root, observation = underallocated_program()
        self.addCleanup(fixture.close)
        grant_review_allocation(root, observation)
        supplement = complete_allocated_reports(fixture, root)
        observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
        path = supplement["report_paths"]["specialist-provider"]
        BLOCKED.block_current_program(root, BLOCKED.BlockedTransitionRequest(
            "verification-environment-unavailable", ("Local verification is available.",),
            (BLOCKED.EvidenceBinding(path, BLOCKED.sha256_file(fixture.repository / path)),)), observation)
        candidate = BLOCKED.build_block_resolution_candidate(root, resolution_candidate(root), observation)
        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
        for name in ("action-authorizations.jsonl", "block-resolutions.jsonl"):
            with self.subTest(ledger=name):
                ledger = root / "state" / name
                original = ledger.read_bytes()
                lines = original.splitlines(keepends=True)
                lines[-1] = lines[-1].rstrip(b"\n") + b" \n"
                ledger.write_bytes(b"".join(lines))
                try:
                    before = repository_snapshot(fixture.repository)
                    with self.subTest(check="retry"), self.assertRaises(ValueError):
                        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                    with self.subTest(check="fresh-process-discovery"):
                        self.assertNotEqual(self.discover(fixture)["disposition"], "resume")
                finally:
                    ledger.write_bytes(original)

    def test_supplement_and_later_resume_prefixes_are_exact_and_discoverable(self):
        for episode in ("allocation", "implementing", "reviewing"):
            for label in ("action-authorization", "resolution-record", "resumed-status"):
                with self.subTest(episode=episode, label=label):
                    fixture, root, observation = underallocated_program()
                    try:
                        if episode != "allocation":
                            grant_review_allocation(root, observation)
                            supplement = complete_allocated_reports(fixture, root)
                            observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
                            if episode == "reviewing":
                                ACTIVATION.advance_execution_state(root, "reviewing", observation)
                            path = supplement["report_paths"]["specialist-provider"]
                            BLOCKED.block_current_program(root, BLOCKED.BlockedTransitionRequest(
                                "verification-environment-unavailable", ("Local verification is available.",),
                                (BLOCKED.EvidenceBinding(path, BLOCKED.sha256_file(fixture.repository / path)),)), observation)
                        candidate = BLOCKED.build_block_resolution_candidate(root,
                            allocation_candidate(root) if episode == "allocation" else resolution_candidate(root), observation)
                        def interrupt(step):
                            if step == label:
                                raise RuntimeError("injected lost response")
                        with mock.patch.object(BLOCKED, "_after_persist", side_effect=interrupt), self.assertRaises(RuntimeError):
                            BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                        discovered = self.discover(fixture)
                        self.assertEqual(discovered["disposition"], "resume" if label == "resumed-status" else "blocked-resolution-retry-ready", discovered)
                        if label == "resolution-record":
                            with tempfile.TemporaryDirectory() as directory:
                                prompt_path = Path(directory) / "resume.md"
                                prompt_path.write_text(candidate.prompt)
                                process = subprocess.run([sys.executable, str(SCRIPT_PATH), "apply", str(root),
                                    "--prompt-file", str(prompt_path), "--repository", str(fixture.repository),
                                    "--base-commit", fixture.head], capture_output=True, text=True, check=False)
                                self.assertEqual(process.returncode, 0, process.stderr)
                        else:
                            BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                        completed = repository_snapshot(root)
                        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                        self.assertEqual(repository_snapshot(root), completed)
                        actions = [json.loads(line) for line in (root / "state/action-authorizations.jsonl").read_text().splitlines()]
                        self.assertEqual(sum("allocate-review-reports" in item["actions"] for item in actions), 1)
                        self.assertEqual(json.loads((root / "state/status.json").read_text())["current_increment_state"], "reviewing" if episode == "reviewing" else "implementing")
                    finally:
                        fixture.close()

    def test_later_resume_lost_status_response_rejects_changed_bound_report(self):
        fixture, root, observation = underallocated_program()
        self.addCleanup(fixture.close)
        grant_review_allocation(root, observation)
        supplement = complete_allocated_reports(fixture, root)
        observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
        path = fixture.repository / supplement["report_paths"]["specialist-provider"]
        BLOCKED.block_current_program(root, BLOCKED.BlockedTransitionRequest(
            "verification-environment-unavailable", ("Local verification is available.",),
            (BLOCKED.EvidenceBinding(path.relative_to(fixture.repository).as_posix(), BLOCKED.sha256_file(path)),)), observation)
        candidate = BLOCKED.build_block_resolution_candidate(root, resolution_candidate(root), observation)
        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
        path.write_bytes(path.read_bytes() + b" ")
        before = repository_snapshot(root)
        with self.assertRaises(ValueError):
            BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
        self.assertEqual(repository_snapshot(root), before)

    def test_supplement_tampering_stops_before_second_block(self):
        fixture, root, observation = underallocated_program()
        self.addCleanup(fixture.close)
        grant_review_allocation(root, observation)
        complete_allocated_reports(fixture, root)
        observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
        status_path = root / "state/status.json"
        for mutation in ("missing-binding", "swapped-binding", "unknown-binding", "origin-action", "origin-resolution", "old-report", "plan"):
            with self.subTest(mutation=mutation):
                path = status_path
                original = path.read_bytes()
                if mutation in ("missing-binding", "swapped-binding", "unknown-binding"):
                    value = json.loads(original)
                    if mutation == "missing-binding":
                        value.pop("review_allocation_binding")
                    elif mutation == "swapped-binding":
                        value["review_allocation_binding"]["resolution_sha256"] = "0" * 64
                    else:
                        value["review_allocation_binding"]["schema_version"] = "unsupported"
                    path.write_bytes(canonical_json(value))
                else:
                    path = {"origin-action": root / "state/action-authorizations.jsonl",
                            "origin-resolution": root / "state/block-resolutions.jsonl",
                            "old-report": fixture.repository / "reviews/architecture.json",
                            "plan": root / "increments/ARCHIVE-INDEX/exact-file-plan.md"}[mutation]
                    original = path.read_bytes()
                    if mutation.startswith("origin-"):
                        lines = original.splitlines(keepends=True)
                        lines[-1] = lines[-1].rstrip(b"\n") + b" \n"
                        path.write_bytes(b"".join(lines))
                    else:
                        path.write_bytes(original + b" ")
                try:
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.block_current_program(root, block_request(fixture), observation)
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                    self.assertNotEqual(self.discover(fixture)["disposition"], "resume")
                finally:
                    path.write_bytes(original)

    def test_allocation_prompt_cannot_expand_paths_scopes_or_replay_family(self):
        fixture, root, observation = underallocated_program()
        self.addCleanup(fixture.close)
        candidate = BLOCKED.build_block_resolution_candidate(root, allocation_candidate(root), observation)
        from task_prompt import parse_exact_prompt, render_exact_prompt
        for mutation in ("executable", "extra-scope", "ordinary-command", "unknown-command", "false-criterion"):
            with self.subTest(mutation=mutation):
                command = parse_exact_prompt(candidate.prompt, "implementation-block-resolution-command/v2")
                if mutation == "executable":
                    command["review_allocation_supplement"]["report_paths"]["specialist-provider"] = "run.sh"
                elif mutation == "extra-scope":
                    command["review_allocation_supplement"]["report_paths"]["specialist-financial"] = "reviews/more.json"
                elif mutation == "ordinary-command":
                    command["schema_version"] = "implementation-block-resolution-command/v1"
                elif mutation == "unknown-command":
                    command["schema_version"] = "implementation-block-resolution-command/v999"
                else:
                    command["criterion_results"][0]["satisfied"] = False
                before = repository_snapshot(fixture.repository)
                with self.assertRaises(ValueError):
                    BLOCKED.persist_blocked_resolution(root, render_exact_prompt(command), observation)
                self.assertEqual(repository_snapshot(fixture.repository), before)
        occupied = fixture.repository / candidate.resolution_record["review_allocation_supplement"]["report_paths"]["requirements"]
        occupied.parent.mkdir(parents=True)
        occupied.write_text("occupied")
        fresh = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
        before = repository_snapshot(fixture.repository)
        with self.assertRaises(ValueError):
            BLOCKED.persist_blocked_resolution(root, candidate.prompt, fresh)
        self.assertEqual(repository_snapshot(fixture.repository), before)

    def test_allocation_and_later_resume_divergent_prefixes_preserve_bytes(self):
        for later in (False, True):
            for label in ("action-authorization", "resolution-record", "resumed-status"):
                with self.subTest(later=later, label=label):
                    fixture, root, observation = underallocated_program()
                    try:
                        path = fixture.repository / "reviews/architecture.json"
                        if later:
                            grant_review_allocation(root, observation)
                            supplement = complete_allocated_reports(fixture, root)
                            path = fixture.repository / supplement["report_paths"]["specialist-provider"]
                            observation = ACTIVATION.inspect_repository(fixture.repository, fixture.head).observation
                            BLOCKED.block_current_program(root, BLOCKED.BlockedTransitionRequest(
                                "verification-environment-unavailable", ("Local verification is available.",),
                                (BLOCKED.EvidenceBinding(path.relative_to(fixture.repository).as_posix(), BLOCKED.sha256_file(path)),)), observation)
                        value = resolution_candidate(root) if later else allocation_candidate(root)
                        candidate = BLOCKED.build_block_resolution_candidate(root, value, observation)
                        def interrupt(step):
                            if step == label:
                                raise RuntimeError("injected lost response")
                        with mock.patch.object(BLOCKED, "_after_persist", side_effect=interrupt), self.assertRaises(RuntimeError):
                            BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                        path.write_bytes(path.read_bytes() + b" ")
                        before = repository_snapshot(fixture.repository)
                        with self.assertRaises(ValueError):
                            BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                        self.assertEqual(repository_snapshot(fixture.repository), before)
                    finally:
                        fixture.close()

    def test_allocation_requires_existing_class_and_successor_preservation(self):
        for options in ({"preserve_reports": False}, {"bounded_reports": False}):
            with self.subTest(options=options):
                fixture, root, observation = underallocated_program(**options)
                try:
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.build_block_resolution_candidate(root, allocation_candidate(root), observation)
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                finally:
                    fixture.close()

    def test_noncanonical_recovery_prefix_is_not_discovered_as_retryable(self):
        for label in ("action-authorization", "resolution-record"):
            with self.subTest(label=label):
                fixture, root, observation = underallocated_program()
                try:
                    candidate = BLOCKED.build_block_resolution_candidate(root, allocation_candidate(root), observation)
                    def interrupt(step):
                        if step == label:
                            raise RuntimeError("injected lost response")
                    with mock.patch.object(BLOCKED, "_after_persist", side_effect=interrupt), self.assertRaises(RuntimeError):
                        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                    path = root / "state" / ("action-authorizations.jsonl" if label == "action-authorization" else "block-resolutions.jsonl")
                    path.write_bytes(path.read_bytes().rstrip(b"\n") + b" \n")
                    before = repository_snapshot(root)
                    self.assertEqual(self.discover(fixture)["disposition"], "blocked-recovery-required")
                    with self.assertRaises(ValueError):
                        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                    self.assertEqual(repository_snapshot(root), before)
                finally:
                    fixture.close()

    def test_ordinary_resume_cannot_replace_pending_allocation_prefix(self):
        for label in ("action-authorization", "resolution-record"):
            with self.subTest(label=label):
                fixture, root, observation = underallocated_program()
                try:
                    candidate = BLOCKED.build_block_resolution_candidate(root, allocation_candidate(root), observation)
                    ordinary = BLOCKED.build_block_resolution_candidate(root, resolution_candidate(root), observation)
                    def interrupt(step):
                        if step == label:
                            raise RuntimeError("injected lost response")
                    with mock.patch.object(BLOCKED, "_after_persist", side_effect=interrupt), self.assertRaises(RuntimeError):
                        BLOCKED.persist_blocked_resolution(root, candidate.prompt, observation)
                    before = repository_snapshot(root)
                    with self.assertRaises(ValueError):
                        BLOCKED.persist_blocked_resolution(root, ordinary.prompt, observation)
                    self.assertEqual(repository_snapshot(root), before)
                finally:
                    fixture.close()

    def test_production_block_fresh_discovery_and_exact_resume(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            blocked_process = subprocess.run(
                [
                    sys.executable,
                    str(LIFECYCLE_SUPPORT_PATH),
                    "block",
                    "--repository",
                    str(fixture.repository),
                    "--candidate",
                    str(fixture.candidate),
                    "--source-plan",
                    str(fixture.source_plan),
                    "--source-sha256",
                    fixture.source_sha256,
                ],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(blocked_process.returncode, 0, blocked_process.stderr)
            blocked = json.loads(blocked_process.stdout)
            self.assertEqual(blocked["program_state"], "blocked")
            self.assertEqual(blocked["increment_state"], "blocked")
            discovered = self.discover(fixture)
            self.assertEqual(discovered["disposition"], "blocked-recovery-ready")
            self.assertEqual(
                discovered["candidates"][0]["resume_program_state"], "active"
            )
            self.assertEqual(
                discovered["candidates"][0]["resume_increment_state"],
                "implementing",
            )

            candidate = resolution_candidate(program_root)
            prompt = BLOCKED.render_block_resolution_prompt(
                program_root, candidate, observation
            )
            receipt = BLOCKED.persist_blocked_resolution(
                program_root, prompt, observation
            )
            self.assertEqual(receipt.program_state, "active")
            self.assertEqual(receipt.increment_state, "implementing")
            actions = [
                json.loads(line)
                for line in (
                    program_root / "state/action-authorizations.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
            resolutions = [
                json.loads(line)
                for line in (
                    program_root / "state/block-resolutions.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
            resume_actions = [
                item
                for item in actions
                if item.get("actions") == ["resume-blocked-program"]
            ]
            self.assertEqual(len(resume_actions), 1)
            self.assertEqual(len(resolutions), 1)
            for record in (*resume_actions, *resolutions):
                self.assertTrue(
                    all(
                        type(result["satisfied"]) is bool
                        for result in record["criterion_results"]
                    )
                )
        finally:
            fixture.close()

    def test_second_blocking_episode_replaces_current_resolution_binding(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )
            first_block_id = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )["blocked_context"]["block_id"]
            prompt = BLOCKED.render_block_resolution_prompt(
                program_root, resolution_candidate(program_root), observation
            )
            BLOCKED.persist_blocked_resolution(program_root, prompt, observation)

            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )
            status = json.loads(
                (program_root / "state/status.json").read_text(encoding="utf-8")
            )
            self.assertNotEqual(status["blocked_context"]["block_id"], first_block_id)
            self.assertNotIn("block_resolution_binding", status)
            self.assertEqual(
                self.discover(fixture)["disposition"], "blocked-recovery-ready"
            )
            resolutions = (
                program_root / "state/block-resolutions.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(resolutions), 1)
        finally:
            fixture.close()

    def test_resolution_prefixes_are_discoverable_and_idempotent(self) -> None:
        for label in ("action-authorization", "resolution-record", "resumed-status"):
            with self.subTest(label=label):
                fixture, program_root, observation = implementing_program()
                try:
                    BLOCKED.block_current_program(
                        program_root, block_request(fixture), observation
                    )
                    prompt = BLOCKED.render_block_resolution_prompt(
                        program_root, resolution_candidate(program_root), observation
                    )

                    def interrupt(
                        completed_label: str, *, expected_label: str = label
                    ) -> None:
                        if completed_label == expected_label:
                            raise RuntimeError("injected blocked recovery interruption")

                    with mock.patch.object(
                        BLOCKED, "_after_persist", side_effect=interrupt
                    ):
                        with self.assertRaisesRegex(RuntimeError, "injected"):
                            BLOCKED.persist_blocked_resolution(
                                program_root, prompt, observation
                            )
                    discovered = self.discover(fixture)
                    expected = (
                        "resume"
                        if label == "resumed-status"
                        else "blocked-resolution-retry-ready"
                    )
                    self.assertEqual(discovered["disposition"], expected, discovered)
                    completed = BLOCKED.persist_blocked_resolution(
                        program_root, prompt, observation
                    )
                    self.assertEqual(completed.increment_state, "implementing")
                    snapshot = repository_snapshot(fixture.repository)
                    recovered = BLOCKED.persist_blocked_resolution(
                        program_root, prompt, observation
                    )
                    self.assertEqual(recovered.increment_state, "implementing")
                    self.assertEqual(repository_snapshot(fixture.repository), snapshot)
                finally:
                    fixture.close()

    def test_remediating_and_invalid_entry_requests_fail_before_writes(self) -> None:
        from tests.program_bootstrap_support import canonical_json
        from tests.test_program_review import REVIEW, reviewing_program

        def add_open_finding(fixture: BootstrapFixture) -> None:
            path = fixture.repository / "reviews/requirements.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["findings"] = [
                {
                    "finding_id": "F-BLOCK-BOUNDARY",
                    "report_id": "requirements-initial",
                    "scope": "requirements",
                    "classification": "material",
                    "summary": "review found a material defect",
                    "evidence": "exact evidence",
                    "impact": "requested behavior is not met",
                    "confidence": "high",
                    "remediation": "repair before diff approval",
                    "disposition": "open",
                    "affected_requirement_or_invariant": "archive output",
                    "severity": "high",
                    "inspection_path": "archive-output.txt",
                    "decision_reference": "none",
                }
            ]
            path.write_bytes(canonical_json(report))

        fixture, program_root, observation = reviewing_program(add_open_finding)
        try:
            REVIEW.persist_review_remediation(program_root, observation)
            observation = ACTIVATION._without_owned_program_paths(
                program_root,
                ACTIVATION.inspect_repository(
                    fixture.repository, fixture.head
                ).observation,
            )
            before = repository_snapshot(fixture.repository)
            with self.assertRaisesRegex(ValueError, "remediating"):
                BLOCKED.block_current_program(
                    program_root, block_request(fixture), observation
                )
            self.assertEqual(repository_snapshot(fixture.repository), before)
        finally:
            fixture.close()

        for state in ("preparing", "awaiting-plan-approval", "authorized", "verified", "accepted"):
            with self.subTest(state=state):
                fixture, program_root, observation = implementing_program()
                try:
                    status_path = program_root / "state/status.json"
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                    status["current_increment_state"] = state
                    status_path.write_text(
                        json.dumps(status, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.block_current_program(
                            program_root, block_request(fixture), observation
                        )
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                finally:
                    fixture.close()

    def test_candidate_tampering_and_stale_authority_fail_before_writes(self) -> None:
        for case in (
            "resume-target",
            "unsatisfied",
            "duplicate",
            "outside-evidence",
            "changed-evidence",
            "prompt",
            "status",
        ):
            with self.subTest(case=case):
                fixture, program_root, observation = implementing_program()
                try:
                    BLOCKED.block_current_program(
                        program_root, block_request(fixture), observation
                    )
                    candidate = resolution_candidate(program_root)
                    if case == "resume-target":
                        candidate["resume_increment_state"] = "reviewing"
                    elif case == "unsatisfied":
                        candidate["criterion_results"][0]["satisfied"] = False
                    elif case == "duplicate":
                        candidate["criterion_results"].append(
                            dict(candidate["criterion_results"][0])
                        )
                    elif case == "outside-evidence":
                        candidate["evidence_bindings"] = [
                            {"path": "outside.txt", "sha256": "0" * 64}
                        ]
                    elif case == "changed-evidence":
                        (fixture.repository / "catalog.txt").write_text(
                            "changed\n", encoding="utf-8"
                        )
                    prompt = None
                    if case not in {"status", "prompt"}:
                        before = repository_snapshot(fixture.repository)
                        with self.assertRaises(ValueError):
                            BLOCKED.build_block_resolution_candidate(
                                program_root, candidate, observation
                            )
                        self.assertEqual(repository_snapshot(fixture.repository), before)
                        continue
                    prompt = BLOCKED.render_block_resolution_prompt(
                        program_root, candidate, observation
                    )
                    if case == "prompt":
                        prompt += "tampered\n"
                    else:
                        status_path = program_root / "state/status.json"
                        status = json.loads(status_path.read_text(encoding="utf-8"))
                        status["state_sequence"] += 1
                        status_path.write_text(
                            json.dumps(status, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.persist_blocked_resolution(
                            program_root, prompt, observation
                        )
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                finally:
                    fixture.close()

    def test_resolution_candidate_requires_exact_nested_field_types(self) -> None:
        for case in (
            "integer-satisfied",
            "float-satisfied",
            "criterion-type",
            "criterion-extra-key",
            "evidence-path-type",
            "evidence-sha-type",
            "evidence-extra-key",
        ):
            with self.subTest(case=case):
                fixture, program_root, observation = implementing_program()
                try:
                    BLOCKED.block_current_program(
                        program_root, block_request(fixture), observation
                    )
                    candidate = resolution_candidate(program_root)
                    if case == "integer-satisfied":
                        candidate["criterion_results"][0]["satisfied"] = 1
                    elif case == "float-satisfied":
                        candidate["criterion_results"][0]["satisfied"] = 1.0
                    elif case == "criterion-type":
                        candidate["criterion_results"][0]["criterion"] = 1
                    elif case == "criterion-extra-key":
                        candidate["criterion_results"][0]["extra"] = "value"
                    elif case == "evidence-path-type":
                        candidate["evidence_bindings"][0]["path"] = 1
                    elif case == "evidence-sha-type":
                        candidate["evidence_bindings"][0]["sha256"] = 1
                    else:
                        candidate["evidence_bindings"][0]["extra"] = "value"
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaisesRegex(
                        ValueError, "candidate nested field types are invalid"
                    ):
                        BLOCKED.build_block_resolution_candidate(
                            program_root, candidate, observation
                        )
                    self.assertEqual(
                        repository_snapshot(fixture.repository), before
                    )
                finally:
                    fixture.close()

    def test_changed_plan_baseline_grant_context_or_evidence_fails_closed(self) -> None:
        for case in ("plan", "baseline", "grant", "context", "symlink-evidence"):
            with self.subTest(case=case):
                fixture, program_root, observation = implementing_program()
                try:
                    BLOCKED.block_current_program(
                        program_root, block_request(fixture), observation
                    )
                    if case == "plan":
                        path = program_root / "increments/ARCHIVE-INDEX/exact-file-plan.md"
                        path.write_bytes(path.read_bytes() + b"drift\n")
                    elif case == "baseline":
                        path = program_root / "increments/ARCHIVE-INDEX/execution-baseline.json"
                        path.write_bytes(path.read_bytes() + b" ")
                    elif case == "grant":
                        path = program_root / "state/increment-grants.jsonl"
                        records = [json.loads(line) for line in path.read_text().splitlines()]
                        records[-1]["decision"] = "revoked"
                        path.write_text(
                            "".join(
                                json.dumps(item, separators=(",", ":"), sort_keys=True)
                                + "\n"
                                for item in records
                            ),
                            encoding="utf-8",
                        )
                    elif case == "context":
                        path = program_root / "state/status.json"
                        status = json.loads(path.read_text(encoding="utf-8"))
                        status["blocked_context"]["block_id"] = "FABRICATED"
                        path.write_text(
                            json.dumps(status, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )
                    else:
                        evidence = fixture.repository / "catalog.txt"
                        evidence.unlink()
                        evidence.symlink_to("archive-output.txt")
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaises(ValueError):
                        BLOCKED.build_block_resolution_candidate(
                            program_root, resolution_candidate(program_root), observation
                        )
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                finally:
                    fixture.close()

    def test_divergent_resolution_action_is_preserved_and_stops(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )
            prompt = BLOCKED.render_block_resolution_prompt(
                program_root, resolution_candidate(program_root), observation
            )

            def interrupt(label: str) -> None:
                if label == "action-authorization":
                    raise RuntimeError("injected")

            with mock.patch.object(BLOCKED, "_after_persist", side_effect=interrupt):
                with self.assertRaises(RuntimeError):
                    BLOCKED.persist_blocked_resolution(
                        program_root, prompt, observation
                    )
            path = program_root / "state/action-authorizations.jsonl"
            records = [json.loads(line) for line in path.read_text().splitlines()]
            records[-1]["checkpoint_id"] = "DIVERGENT"
            path.write_text(
                "".join(
                    json.dumps(item, separators=(",", ":"), sort_keys=True) + "\n"
                    for item in records
                ),
                encoding="utf-8",
            )
            before = repository_snapshot(fixture.repository)
            discovered = self.discover(fixture)
            self.assertEqual(
                discovered["disposition"], "blocked-recovery-required", discovered
            )
            with self.assertRaisesRegex(ValueError, "recovery-required"):
                BLOCKED.persist_blocked_resolution(
                    program_root, prompt, observation
                )
            self.assertEqual(repository_snapshot(fixture.repository), before)
        finally:
            fixture.close()

    def test_render_and_apply_clis_use_transport_only_as_input(self) -> None:
        fixture, program_root, observation = implementing_program()
        try:
            BLOCKED.block_current_program(
                program_root, block_request(fixture), observation
            )
            candidate_path = fixture.root / "block-candidate.json"
            candidate_path.write_text(
                json.dumps(resolution_candidate(program_root), sort_keys=True) + "\n",
                encoding="utf-8",
            )
            before = repository_snapshot(fixture.repository)
            rendered = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "render",
                    str(program_root),
                    "--candidate-file",
                    str(candidate_path),
                ],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertEqual(repository_snapshot(fixture.repository), before)
            prompt_path = fixture.root / "block-prompt.md"
            prompt_path.write_text(rendered.stdout, encoding="utf-8")
            applied = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "apply",
                    str(program_root),
                    "--prompt-file",
                    str(prompt_path),
                    "--repository",
                    str(fixture.repository),
                    "--base-commit",
                    fixture.head,
                ],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(json.loads(applied.stdout)["increment_state"], "implementing")
            self.assertFalse(
                any(
                    path.name == "block-candidate.json"
                    for path in program_root.rglob("*")
                )
            )
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
