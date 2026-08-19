import importlib.util
import inspect
import json
import re
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPOSITORY_ROOT / "skills/implementing-staged-plans/scripts"
SCRIPT_PATH = SCRIPT_ROOT / "execution_discipline.py"
FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "tests/fixtures/execution-discipline/portable-archive-run/scenarios.json"
)

sys.path.insert(0, str(SCRIPT_ROOT))
try:
    import repository_preparation as PREPARATION
    import state_authority as AUTHORITY

    SPEC = importlib.util.spec_from_file_location("execution_discipline", SCRIPT_PATH)
    if SPEC is None or SPEC.loader is None:
        raise RuntimeError(f"Unable to load execution discipline from {SCRIPT_PATH}")
    EXECUTION = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = EXECUTION
    SPEC.loader.exec_module(EXECUTION)
finally:
    sys.path.remove(str(SCRIPT_ROOT))


def test_first_evidence(**overrides):
    values = {
        "schema_version": "implementation-execution-evidence/v1",
        "slice_id": "evidence-validation",
        "purpose": "reject invalid execution evidence",
        "red_command": "python3 -m unittest tests.test_execution_discipline.ExecutionEvidenceTests",
        "expected_failure": "execution module is missing",
        "observed_failure": "execution module is missing",
        "red_exit_code": 1,
        "observed_before_production_change": True,
        "intended_reason_match": True,
        "green_command": "python3 -m unittest tests.test_execution_discipline.ExecutionEvidenceTests",
        "observed_green": "tests pass",
        "green_exit_code": 0,
        "evidence_order": ("red", "green"),
    }
    values.update(overrides)
    return EXECUTION.TestFirstEvidence(**values)


def alternative_verification(**overrides):
    values = {
        "schema_version": "implementation-execution-evidence/v1",
        "surface_kind": "reference",
        "reason_tdd_is_artificial": "human-facing procedure has no runtime behavior",
        "command": "python3 skills/implementing-staged-plans/scripts/validate_package.py .",
        "expected_evidence": "required regular assets and links are valid",
        "observed_evidence": "package validation passed",
        "exit_code": 0,
        "relevant_inputs": ("skills/implementing-staged-plans/references/execution-discipline.md",),
        "residual_limitation": "structural checks do not prove agent execution behavior",
        "behavioral_test_available": False,
    }
    values.update(overrides)
    return EXECUTION.AlternativeVerificationContract(**values)


def observation(**overrides):
    values = {
        "repository": "/tmp/portable-archive-run",
        "path": "/tmp/portable-archive-run",
        "branch": "archive-maintenance",
        "base_commit": "b" * 40,
        "head_commit": "a" * 40,
        "staged_paths": (),
        "modified_paths": (),
        "untracked_paths": (),
        "conflicted_paths": (),
        "active_git_operation": None,
    }
    values.update(overrides)
    return PREPARATION.RepositoryObservation(**values)


def ownership(path, **overrides):
    values = {
        "path": path,
        "disposition": "create",
        "owner": "execution discipline",
        "accepted_overlap": False,
        "pre_write_fingerprint": "absent",
        "post_write_fingerprint": "present",
        "owning_mechanism": "none",
        "verification_command": "python3 -m unittest tests.test_execution_discipline",
    }
    values.update(overrides)
    return EXECUTION.OwnershipBoundary(**values)


def surface(name="execution_discipline.py", **overrides):
    values = {
        "surface": name,
        "surface_kind": "path",
        "change_kind": "created",
    }
    values.update(overrides)
    return EXECUTION.ExecutionSurface(**values)


def semantic_name(name="execution_discipline.py", **overrides):
    values = {
        "surface": name,
        "surface_kind": "path",
        "origin": "new",
        "context": "authorized increment execution",
        "intention": "validate execution evidence",
        "planning_term_basis": "none",
        "basis_owner": "none",
        "compatibility_class": "private",
        "compatibility_disposition": "new internal surface",
    }
    values.update(overrides)
    return PREPARATION.SemanticNameRecord(**values)


def amendment(**overrides):
    values = {
        "proposed_classification": "bounded-implementation-amendment",
        "changed_dimensions": ("mechanism",),
        "evidence": ("focused test evidence",),
        "obligations_preserved": True,
        "user_owned_decision": False,
        "reversible_or_recoverable": True,
        "authoritative_contradiction": False,
    }
    values.update(overrides)
    return PREPARATION.AmendmentProposal(**values)


def boundary(boundary_id="execution-contracts", **overrides):
    values = {
        "boundary_id": boundary_id,
        "purpose": "define execution contracts",
        "message": "test: define execution discipline contracts",
        "paths": ("tests/test_execution_discipline.py",),
        "depends_on": (),
    }
    values.update(overrides)
    return EXECUTION.CommitBoundary(**values)


def recovery(domain, **overrides):
    touched = domain == "source-code"
    values = {
        "domain": domain,
        "touched": touched,
        "disposition": "recoverable" if touched else "not-touched",
        "mechanism": "restore exact pre-write bytes" if touched else "none",
        "verification": "rerun focused tests" if touched else "confirm domain remained untouched",
        "limitation": "does not restore external state" if touched else "not applicable to this increment",
        "required_authority": "modify-workspace" if touched else "none",
        "authority_granted": touched,
    }
    values.update(overrides)
    return EXECUTION.RecoveryDomainPlan(**values)


class ExecutionEvidenceTests(unittest.TestCase):
    def test_valid_test_first_evidence_is_frozen_and_passes(self) -> None:
        record = test_first_evidence()
        self.assertEqual(EXECUTION.validate_execution_evidence((record,), ()), [])
        with self.assertRaises(FrozenInstanceError):
            record.slice_id = "changed"

    def test_red_must_fail_for_the_intended_reason(self) -> None:
        invalid_records = (
            test_first_evidence(red_exit_code=0),
            test_first_evidence(red_exit_code=True),
            test_first_evidence(observed_before_production_change=False),
            test_first_evidence(intended_reason_match=False),
            test_first_evidence(observed_failure="different failure"),
            test_first_evidence(evidence_order=("green", "red")),
        )
        for record in invalid_records:
            with self.subTest(record=record):
                self.assertTrue(EXECUTION.validate_execution_evidence((record,), ()))

    def test_green_evidence_must_be_focused_and_successful(self) -> None:
        for record in (
            test_first_evidence(green_command=""),
            test_first_evidence(observed_green=""),
            test_first_evidence(green_exit_code=1),
            test_first_evidence(green_exit_code=False),
        ):
            self.assertTrue(EXECUTION.validate_execution_evidence((record,), ()))

    def test_schema_identifiers_and_purpose_are_required(self) -> None:
        records = (
            test_first_evidence(schema_version="legacy/v0"),
            test_first_evidence(slice_id=""),
            test_first_evidence(slice_id="Task 5"),
            test_first_evidence(purpose=""),
            test_first_evidence(red_command=""),
            test_first_evidence(expected_failure=""),
        )
        for record in records:
            self.assertTrue(EXECUTION.validate_execution_evidence((record,), ()))

    def test_complete_alternative_verification_passes(self) -> None:
        self.assertEqual(
            EXECUTION.validate_execution_evidence((), (alternative_verification(),)),
            [],
        )

    def test_frozen_evidence_rejects_mutable_sequence_fields(self) -> None:
        mutable_order = test_first_evidence(evidence_order=["red", "green"])
        mutable_inputs = alternative_verification(
            relevant_inputs=["skills/implementing-staged-plans/references/execution-discipline.md"]
        )
        self.assertTrue(
            EXECUTION.validate_execution_evidence((mutable_order,), ())
        )
        self.assertTrue(
            EXECUTION.validate_execution_evidence((), (mutable_inputs,))
        )

    def test_alternative_verification_cannot_bypass_behavioral_tdd(self) -> None:
        invalid = (
            alternative_verification(surface_kind="behavior"),
            alternative_verification(behavioral_test_available=True),
            alternative_verification(reason_tdd_is_artificial=""),
            alternative_verification(exit_code=1),
            alternative_verification(relevant_inputs=()),
            alternative_verification(residual_limitation=""),
        )
        for record in invalid:
            self.assertTrue(EXECUTION.validate_execution_evidence((), (record,)))


class OwnershipTests(unittest.TestCase):
    def test_exact_planned_actual_and_owned_paths_pass(self) -> None:
        paths = ("archive/index.py", "tests/test_index.py")
        boundaries = tuple(ownership(path) for path in paths)
        self.assertEqual(
            EXECUTION.validate_execution_ownership(
                paths, paths, boundaries, observation(), ()
            ),
            [],
        )

    def test_unrelated_cleanup_missing_plan_and_duplicate_owner_fail(self) -> None:
        planned = ("archive/index.py",)
        actual = ("archive/index.py", "archive/unrelated_cleanup.py")
        boundaries = (ownership("archive/index.py"), ownership("archive/index.py"))
        issues = EXECUTION.validate_execution_ownership(
            planned, actual, boundaries, observation(), ()
        )
        self.assertTrue(any("actual changed paths" in issue for issue in issues))
        self.assertTrue(any("duplicate ownership" in issue for issue in issues))

    def test_preserve_fingerprints_must_remain_equal(self) -> None:
        protected = ownership(
            "archive/preserved.txt",
            disposition="preserve",
            pre_write_fingerprint="1" * 64,
            post_write_fingerprint="2" * 64,
        )
        issues = EXECUTION.validate_execution_ownership(
            (), (), (protected,), observation(), ()
        )
        self.assertTrue(any("preserve fingerprint" in issue for issue in issues))

    def test_extend_overlap_and_managed_paths_need_exact_owners(self) -> None:
        path = "catalog/generated-index.json"
        pre_write = observation(modified_paths=(path,))
        invalid = ownership(
            path,
            disposition="managed",
            owner="",
            accepted_overlap=False,
            owning_mechanism="",
            verification_command="",
        )
        issues = EXECUTION.validate_execution_ownership(
            (path,), (path,), (invalid,), pre_write, ()
        )
        self.assertTrue(any("unaccepted dirty work" in issue for issue in issues))
        self.assertTrue(any("owner" in issue for issue in issues))
        self.assertTrue(any("owning mechanism" in issue for issue in issues))

    def test_accepted_dirty_overlap_flag_must_match_controlling_inputs(self) -> None:
        path = "archive/index.py"
        boundary_record = ownership(
            path,
            disposition="extend",
            accepted_overlap=False,
        )
        issues = EXECUTION.validate_execution_ownership(
            (path,),
            (path,),
            (boundary_record,),
            observation(modified_paths=(path,)),
            (path,),
        )
        self.assertTrue(any("accepted_overlap" in issue for issue in issues))


class SemanticSurfaceTests(unittest.TestCase):
    def test_created_and_renamed_surfaces_require_one_to_one_inventory(self) -> None:
        created = surface()
        self.assertEqual(
            EXECUTION.validate_execution_surfaces((created,), (semantic_name(),)), []
        )
        self.assertTrue(EXECUTION.validate_execution_surfaces((created,), ()))
        self.assertTrue(
            EXECUTION.validate_execution_surfaces(
                (created, created), (semantic_name(), semantic_name())
            )
        )

    def test_every_accepted_surface_kind_is_delegated_contextually(self) -> None:
        surfaces = tuple(
            surface(f"archive-{kind}", surface_kind=kind)
            for kind in PREPARATION.SURFACE_KINDS
        )
        names = tuple(
            semantic_name(f"archive-{kind}", surface_kind=kind)
            for kind in PREPARATION.SURFACE_KINDS
        )
        self.assertEqual(EXECUTION.validate_execution_surfaces(surfaces, names), [])

    def test_roadmap_coordinate_is_rejected_but_governance_and_domain_names_pass(self) -> None:
        invalid_surface = surface("phase-7-loader", surface_kind="symbol")
        invalid_name = semantic_name("phase-7-loader", surface_kind="symbol")
        self.assertTrue(
            EXECUTION.validate_execution_surfaces((invalid_surface,), (invalid_name,))
        )
        governance = replace(
            invalid_name,
            planning_term_basis="implementation-governance",
            basis_owner="approved implementation record",
        )
        domain = replace(
            invalid_name,
            planning_term_basis="durable-domain",
            basis_owner="archive processing phase taxonomy",
        )
        self.assertEqual(
            EXECUTION.validate_execution_surfaces((invalid_surface,), (governance,)), []
        )
        self.assertEqual(
            EXECUTION.validate_execution_surfaces((invalid_surface,), (domain,)), []
        )

    def test_existing_external_name_needs_compatibility_disposition(self) -> None:
        changed = surface("archive-command", surface_kind="command", change_kind="renamed")
        record = semantic_name(
            "archive-command",
            surface_kind="command",
            origin="existing",
            compatibility_class="external",
            compatibility_disposition="preserve",
        )
        self.assertTrue(EXECUTION.validate_execution_surfaces((changed,), (record,)))

    def test_physical_path_rename_is_unsupported(self) -> None:
        renamed = surface(
            "archive-output.txt", surface_kind="path", change_kind="renamed"
        )
        issues = EXECUTION.validate_execution_surfaces(
            (renamed,), (semantic_name("archive-output.txt"),)
        )
        self.assertIn(
            "physical path rename is unsupported: archive-output.txt",
            issues,
        )

    def test_surface_and_naming_record_kinds_must_match(self) -> None:
        created = surface("archive-command", surface_kind="command")
        wrong_kind = semantic_name("archive-command", surface_kind="symbol")
        issues = EXECUTION.validate_execution_surfaces((created,), (wrong_kind,))
        self.assertTrue(any("surface kind" in issue for issue in issues))


class ActualSemanticInventoryTests(unittest.TestCase):
    def test_actual_created_surfaces_are_contextual_and_project_neutral(self) -> None:
        module_symbols = sorted(
            name
            for name, value in vars(EXECUTION).items()
            if not name.startswith("__")
            and (
                (
                    (inspect.isfunction(value) or inspect.isclass(value))
                    and getattr(value, "__module__", None) == EXECUTION.__name__
                )
                or name
                in {
                    "EXECUTION_EVIDENCE_SCHEMA",
                    "ALTERNATIVE_VERIFICATION_KINDS",
                    "OWNERSHIP_DISPOSITIONS",
                    "EXECUTION_SURFACE_CHANGES",
                    "RECOVERY_DOMAINS",
                    "RECOVERY_ACTIONS",
                }
            )
        )
        test_methods = sorted(
            method_name
            for _, test_class in inspect.getmembers(
                sys.modules[__name__], inspect.isclass
            )
            if test_class.__module__ == __name__
            for method_name, _ in inspect.getmembers(
                test_class, inspect.isfunction
            )
            if method_name.startswith("test_")
        )
        reference = (
            REPOSITORY_ROOT
            / "skills/implementing-staged-plans/references/execution-discipline.md"
        ).read_text(encoding="utf-8")
        headings = re.findall(r"^## (.+)$", reference, flags=re.MULTILINE)
        headings.append("Route Execution Discipline Work")

        surfaces = []
        names = []
        categories = (
            (
                (
                    "skills/implementing-staged-plans/scripts/execution_discipline.py",
                    "skills/implementing-staged-plans/references/execution-discipline.md",
                    "tests/test_execution_discipline.py",
                    "tests/fixtures/execution-discipline/portable-archive-run/scenarios.json",
                ),
                "path",
                "execution discipline package and test paths",
            ),
            (module_symbols, "symbol", "execution discipline implementation symbols"),
            (test_methods, "test-or-fixture", "execution discipline regression titles"),
            (headings, "heading", "execution discipline operator headings"),
            (
                ("implementation-execution-evidence/v1",),
                "schema-or-identifier",
                "versioned execution evidence schema",
            ),
        )
        for values, kind, context in categories:
            for value in values:
                surfaces.append(surface(value, surface_kind=kind))
                names.append(
                    semantic_name(
                        value,
                        surface_kind=kind,
                        context=context,
                        intention=f"identify {value} in {context}",
                        compatibility_class=(
                            "persisted"
                            if kind == "schema-or-identifier"
                            else "test" if kind == "test-or-fixture" else "private"
                        ),
                        compatibility_disposition=(
                            "new versioned schema contract"
                            if kind == "schema-or-identifier"
                            else "new contextual execution surface"
                        ),
                    )
                )
        self.assertGreaterEqual(len(surfaces), 60)
        self.assertEqual(
            EXECUTION.validate_execution_surfaces(tuple(surfaces), tuple(names)),
            [],
        )


class AmendmentTests(unittest.TestCase):
    def decide(self, proposal=None, mode="approval:full-increment", **overrides):
        values = {
            "affected_surfaces": ("execution validator",),
            "recovery_or_reversal": "restore the prior helper path",
            "renewed_review": True,
        }
        values.update(overrides)
        return EXECUTION.decide_execution_amendment(
            proposal or amendment(), mode, **values
        )

    def test_bounded_amendment_proceeds_in_four_preapproved_modes(self) -> None:
        for mode in (
            "approval:pre-approve",
            "approval:full-increment",
            "approval:full-diff",
            "approval:full",
        ):
            with self.subTest(mode=mode):
                decision = self.decide(mode=mode)
                self.assertTrue(decision.may_proceed)
                self.assertTrue(decision.renewed_review_required)

    def test_standard_mode_requires_renewed_exact_plan_approval(self) -> None:
        decision = self.decide(mode="approval:standard")
        self.assertFalse(decision.may_proceed)
        self.assertTrue(decision.requires_exact_plan_approval)

    def test_minor_program_unknown_and_contradiction_precedence(self) -> None:
        minor = self.decide(
            amendment(
                proposed_classification="minor-correction",
                changed_dimensions=("test-convention",),
            ),
            mode="approval:standard",
        )
        self.assertTrue(minor.may_proceed)
        program = self.decide(amendment(changed_dimensions=("scope",)))
        contradiction = self.decide(amendment(authoritative_contradiction=True))
        unknown = self.decide(amendment(proposed_classification="quick-fix"))
        self.assertTrue(program.requires_program_revision)
        self.assertEqual(contradiction.classification, "authoritative-contradiction")
        self.assertFalse(unknown.may_proceed)

    def test_bounded_amendment_requires_complete_execution_record(self) -> None:
        cases = (
            self.decide(affected_surfaces=()),
            self.decide(recovery_or_reversal=""),
            self.decide(renewed_review=False),
            self.decide(amendment(evidence=())),
            self.decide(amendment(user_owned_decision=True)),
        )
        for decision in cases:
            self.assertFalse(decision.may_proceed)


class CommitBoundaryTests(unittest.TestCase):
    def validate(self, boundaries, authorization=None, **overrides):
        values = {
            "actual_changed_paths": ("tests/test_execution_discipline.py",),
            "planned_paths": ("tests/test_execution_discipline.py",),
            "protected_paths": (),
            "boundaries": boundaries,
            "commit_authorization": authorization
            or AUTHORITY.AuthorizationDecision(True, "archive-commit", ()),
        }
        values.update(overrides)
        return EXECUTION.validate_commit_boundaries(**values)

    def test_complete_ordered_non_overlapping_partition_passes_with_exact_authority(self) -> None:
        self.assertEqual(self.validate((boundary(),)), [])

    def test_empty_duplicate_missing_extra_protected_and_dependency_errors_fail(self) -> None:
        cases = (
            self.validate(()),
            self.validate((boundary(), boundary())),
            self.validate((boundary(paths=("other.py",)),)),
            self.validate(
                (boundary(paths=("tests/test_execution_discipline.py", "extra.py")),)
            ),
            self.validate(
                (boundary(),), protected_paths=("tests/test_execution_discipline.py",)
            ),
            self.validate((boundary(depends_on=("missing-boundary",)),)),
            self.validate(
                (
                    boundary("second", depends_on=("first",)),
                    boundary("first"),
                )
            ),
        )
        for issues in cases:
            self.assertTrue(issues)

    def test_messages_ids_purpose_and_paths_are_normal_form(self) -> None:
        invalid = (
            boundary(boundary_id="Task 1"),
            boundary(purpose=""),
            boundary(message="Define tests"),
            boundary(paths=()),
        )
        for item in invalid:
            self.assertTrue(self.validate((item,)))

        mutable = boundary(paths=["tests/test_execution_discipline.py"], depends_on=[])
        self.assertTrue(self.validate((mutable,)))

    def test_boundary_partition_never_implies_commit_authority(self) -> None:
        unauthorized = AUTHORITY.AuthorizationDecision(
            False, None, ("no exact action authorization matches the required binding",)
        )
        issues = self.validate((boundary(),), authorization=unauthorized)
        self.assertIn("create-local-commit action is not authorized", issues)

        inconsistent = AUTHORITY.AuthorizationDecision(
            True, "archive-commit", ("conflicting action authorization records",)
        )
        inconsistent_issues = self.validate(
            (boundary(),), authorization=inconsistent
        )
        self.assertIn("create-local-commit action is not authorized", inconsistent_issues)

    def test_commit_authorization_reuses_the_exact_state_authority_binding(self) -> None:
        binding = AUTHORITY.ActionBinding(
            action="create-local-commit",
            scope="commit the archive execution boundary",
            program_id="portable-archive",
            program_revision=3,
            source_id="portable-source",
            source_sha256="1" * 64,
            program_sha256="2" * 64,
            semantic_requirements_sha256="3" * 64,
            increment_id="archive-index",
            brief_sha256="4" * 64,
            exact_file_plan_sha256="5" * 64,
            approval_mode="approval:full-increment",
            workspace_path="/srv/portable-archive",
            workspace_branch="archive-maintenance",
            workspace_base_commit="b" * 40,
            workspace_head_commit="a" * 40,
        )
        record = {
            "schema_version": "implementation-action-authorization/v1",
            "authorization_id": "archive-commit",
            "decision": "authorized",
            "program_id": binding.program_id,
            "program_revision": binding.program_revision,
            "source_id": binding.source_id,
            "source_sha256": binding.source_sha256,
            "program_sha256": binding.program_sha256,
            "semantic_requirements_sha256": binding.semantic_requirements_sha256,
            "increment_id": binding.increment_id,
            "brief_sha256": binding.brief_sha256,
            "exact_file_plan_sha256": binding.exact_file_plan_sha256,
            "approval_mode": binding.approval_mode,
            "workspace": {
                "path": binding.workspace_path,
                "branch": binding.workspace_branch,
                "base_commit": binding.workspace_base_commit,
                "head_commit": binding.workspace_head_commit,
            },
            "actions": ["create-local-commit"],
            "scope": [binding.scope],
        }
        decision = EXECUTION.decide_commit_authorization([record], binding)
        self.assertTrue(decision.authorized)
        self.assertEqual(decision.authorization_id, "archive-commit")


class RecoveryDomainTests(unittest.TestCase):
    def valid_domains(self):
        return tuple(recovery(domain) for domain in EXECUTION.RECOVERY_DOMAINS)

    def test_exactly_four_distinct_domains_are_required(self) -> None:
        self.assertEqual(EXECUTION.validate_recovery_domains(self.valid_domains()), [])
        self.assertTrue(EXECUTION.validate_recovery_domains(self.valid_domains()[:-1]))
        self.assertTrue(
            EXECUTION.validate_recovery_domains(
                self.valid_domains() + (recovery("source-code"),)
            )
        )

    def test_touched_domains_need_mechanism_evidence_limitation_and_authority(self) -> None:
        invalid_source = recovery(
            "source-code",
            mechanism="",
            verification="",
            limitation="",
            required_authority="",
            authority_granted=False,
        )
        domains = (invalid_source, *self.valid_domains()[1:])
        self.assertGreaterEqual(len(EXECUTION.validate_recovery_domains(domains)), 5)

    def test_untouched_domains_require_explicit_not_touched_disposition(self) -> None:
        domains = list(self.valid_domains())
        domains[1] = replace(domains[1], disposition="recoverable")
        self.assertTrue(EXECUTION.validate_recovery_domains(tuple(domains)))

        domains = list(self.valid_domains())
        domains[1] = replace(
            domains[1],
            mechanism="git-revert",
            required_authority="create-local-commit",
        )
        self.assertTrue(EXECUTION.validate_recovery_domains(tuple(domains)))

    def test_touched_domain_authority_must_match_the_recovery_domain(self) -> None:
        domains = list(self.valid_domains())
        domains[3] = recovery(
            "provider-or-external-state",
            touched=True,
            disposition="recoverable",
            mechanism="provider-specific reconciliation",
            verification="compare provider state with the recovery ledger",
            limitation="provider response may remain asynchronous",
            required_authority="modify-workspace",
            authority_granted=True,
        )
        issues = EXECUTION.validate_recovery_domains(tuple(domains))
        self.assertTrue(any("authority is not valid" in issue for issue in issues))

    def test_git_revert_cannot_satisfy_external_recovery(self) -> None:
        for domain in ("persistent-data", "deployment", "provider-or-external-state"):
            domains = list(self.valid_domains())
            index = EXECUTION.RECOVERY_DOMAINS.index(domain)
            domains[index] = recovery(
                domain,
                touched=True,
                disposition="recoverable",
                mechanism="git-revert",
                verification="git history inspected",
                limitation="source rollback only",
                required_authority="modify-provider-state",
                authority_granted=True,
            )
            issues = EXECUTION.validate_recovery_domains(tuple(domains))
            self.assertTrue(any("Git" in issue or "git" in issue for issue in issues))


class IntegrationTests(unittest.TestCase):
    def test_neutral_preparation_to_execution_scenario_passes_without_commit(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema_version"], "execution-discipline-scenarios/v1")
        scenario = fixture["scenario"]
        self.assertFalse(scenario["commit_requested"])
        self.assertFalse(scenario["commit_authorization"]["authorized"])
        self.assertEqual(EXECUTION.validate_execution_bundle(scenario), [])


if __name__ == "__main__":
    unittest.main()
