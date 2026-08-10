# Post-Closure Housekeeping Proposal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic proposal-only post-closure housekeeping boundary that can identify only closure-bound program-created disposable resources and can validate, but never execute, a separate destructive authorization.

**Architecture:** A new focused Python module loads immutable closed-program bindings, reads an optional closure-bound provenance inventory, inspects exact candidate paths, renders canonical dry-run JSON, revalidates stale state, and delegates the existing later-action authority decision after exact inventory filtering. A new reference and one front-door route document the boundary; a dedicated unittest module protects behavior.

**Tech Stack:** Python 3 standard library, `unittest`, local Git CLI through argument-vector subprocess calls, existing program-authority/repository-preparation/continuity modules.

## Global Constraints

- Never delete, move, trash, prune, or remove any path.
- Never expose an execution-capable function or CLI route.
- Preserve all accepted program artifacts and all existing staged, unstaged, untracked, user-owned, and provenance-uncertain work.
- Do not change installation, program discovery, continuation prompting, accepted program evidence, manifests, status, approvals, or authorization logs.
- Do not stage, commit, push, create a pull request, publish, or perform external actions.
- Use project-neutral identifiers and fictional fixture data.
- Use strict RED-GREEN-REFACTOR cycles; every production behavior must have first failed for the intended reason.
- Replace plan commit steps with read-only `git diff` and `git status` checkpoints.

---

### Task 1: Closed-program context and deterministic empty proposal

**Files:**
- Create: `tests/test_housekeeping_proposal.py`
- Create: `skills/implementing-staged-plans/scripts/housekeeping_proposal.py`

**Interfaces:**
- Consumes: `program_authority.load_json_object`, `resolve_managed_path`, `sha256_file`, and `validate_program_authority`.
- Produces: `HousekeepingProposal`, `load_closed_housekeeping_context`, `build_housekeeping_proposal`, and `candidate_inventory_sha256`.

- [ ] **Step 1: Write the failing closed-context and empty-proposal tests**

```python
def test_closed_program_without_provenance_returns_empty_dry_run_and_stop(self):
    proposal = HOUSEKEEPING.build_housekeeping_proposal(
        self.program_root, self.repository_root
    )
    self.assertEqual(proposal.mode, "dry-run")
    self.assertEqual(proposal.candidates, ())
    self.assertFalse(proposal.execution_authorized)
    self.assertIn("Stop", proposal.next_action)

def test_open_program_is_rejected(self):
    self.write_status(program_state="active")
    with self.assertRaisesRegex(ValueError, "program is not closed"):
        HOUSEKEEPING.build_housekeeping_proposal(
            self.program_root, self.repository_root
        )
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_housekeeping_proposal -v`

Expected: import or missing-symbol failure naming `housekeeping_proposal.py` or `build_housekeeping_proposal`.

- [ ] **Step 3: Implement strict records, closed-program loading, and canonical empty proposal**

```python
@dataclass(frozen=True)
class HousekeepingProposal:
    schema_version: str
    program_id: str
    program_revision: int
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    reconciliation_sha256: str
    closure_packet_sha256: str
    repository: RepositoryIdentity
    quarantine_root: str | None
    candidate_inventory_sha256: str
    candidates: tuple[HousekeepingCandidate, ...]
    mode: str
    execution_authorized: bool
    next_action: str

def build_housekeeping_proposal(
    program_root: Path,
    repository_root: Path,
    quarantine_root: Path | None = None,
) -> HousekeepingProposal:
    context = load_closed_housekeeping_context(program_root, repository_root)
    resources = load_bound_disposable_resources(context)
    candidates = tuple(
        inspect_candidate(context, resource, quarantine_root)
        for resource in resources
    )
    return proposal_from_candidates(context, candidates)
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_housekeeping_proposal -v`

Expected: closed-context and empty-proposal tests pass.

- [ ] **Step 5: Check the exact diff without staging or committing**

Run: `rtk git diff -- tests/test_housekeeping_proposal.py skills/implementing-staged-plans/scripts/housekeeping_proposal.py`

Expected: only Task 1 tests and minimal production support.

### Task 2: Candidate provenance, containment, Git state, and stale validation

**Files:**
- Modify: `tests/test_housekeeping_proposal.py`
- Modify: `skills/implementing-staged-plans/scripts/housekeeping_proposal.py`

**Interfaces:**
- Consumes: Task 1 context/proposal types and `repository_preparation.inspect_repository`.
- Produces: `DisposableResource`, `FilesystemObservation`, `WorktreeObservation`, `HousekeepingCandidate`, `inspect_candidate`, and `validate_housekeeping_proposal`.

- [ ] **Step 1: Add failing table-driven safety tests**

```python
def test_rejects_ineligible_candidate_classes(self):
    cases = {
        "user-owned": "ownership must be program-created-disposable",
        "provenance-uncertain": "ownership must be program-created-disposable",
        "missing-provenance": "disposable resource inventory",
        "symlink": "symlink",
        "closure-evidence": "protected program path",
        "stale": "proposal inventory is stale",
    }
    for case, expected_issue in cases.items():
        with self.subTest(case=case):
            self.assertIn(expected_issue, self.validate_case(case))
```

Add real synthetic-Git tests for ignored/untracked cache behavior and linked-worktree main, dirty, locked, conflicted, operation-active, and unique-commit rejection. Each test names the production guard whose removal would make it fail.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_housekeeping_proposal -v`

Expected: failures identify missing provenance, filesystem, worktree, and stale-inventory behavior.

- [ ] **Step 3: Implement exact candidate inspection and revalidation**

```python
def validate_housekeeping_proposal(
    proposal: HousekeepingProposal,
    program_root: Path,
    repository_root: Path,
) -> list[str]:
    current = build_housekeeping_proposal(
        program_root,
        repository_root,
        proposal.quarantine_root,
    )
    if canonical_proposal_bytes(current) != canonical_proposal_bytes(proposal):
        return ["proposal inventory is stale"]
    return []
```

Use `lstat`, lexical and resolved containment, descendant fingerprinting, protected-path overlap, `git check-ignore`, `git ls-files`, stable worktree porcelain, existing repository inspection, and other-ref containment. Reject before rendering rather than silently dropping an invalid provenance record.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_housekeeping_proposal -v`

Expected: every safety and stale-inventory case passes.

- [ ] **Step 5: Refactor only demonstrated duplication and rerun focused tests**

Run: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_housekeeping_proposal -v`

Expected: all focused tests pass after the unchanged-behavior cleanup.

### Task 3: Exact destructive decision and proposal-only CLI

**Files:**
- Modify: `tests/test_housekeeping_proposal.py`
- Modify: `skills/implementing-staged-plans/scripts/housekeeping_proposal.py`

**Interfaces:**
- Consumes: Task 2 live validation, manifest-owned approvals/authorizations, and `continuity_closure.decide_later_action`.
- Produces: `HousekeepingAuthorizationDecision`, `check_housekeeping_authorization`, and CLI commands `propose`, `validate-proposal`, and `check-authorization`.

- [ ] **Step 1: Add failing authorization and CLI tests**

```python
def test_closure_approval_alone_never_authorizes_cleanup(self):
    decision = HOUSEKEEPING.check_housekeeping_authorization(
        self.proposal, self.program_root, self.repository_root,
        recovery_evidence="receipt-bound reverse path",
    )
    self.assertFalse(decision.authorized)
    self.assertIn("action authorization", " ".join(decision.issues))

def test_exact_inventory_authorization_returns_decision_and_stop_only(self):
    self.append_exact_destructive_grant(self.proposal)
    decision = HOUSEKEEPING.check_housekeeping_authorization(
        self.proposal, self.program_root, self.repository_root,
        recovery_evidence="receipt-bound reverse path",
    )
    self.assertTrue(decision.authorized)
    self.assertIn("Stop", decision.next_action)
```

Exercise the parser and prove that `execute`, `cleanup`, `remove`, `trash`, and `prune` are invalid commands.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_housekeeping_proposal -v`

Expected: failures identify missing exact authorization and CLI behavior.

- [ ] **Step 3: Implement the exact authorization filter and read-only CLI**

```python
def check_housekeeping_authorization(
    proposal: HousekeepingProposal,
    program_root: Path,
    repository_root: Path,
    *,
    recovery_evidence: str,
) -> HousekeepingAuthorizationDecision:
    issues = validate_housekeeping_proposal(
        proposal, program_root, repository_root
    )
    if issues:
        return HousekeepingAuthorizationDecision(False, None, tuple(issues), STOP)
    scope = (
        "apply post-closure housekeeping inventory "
        f"{proposal.candidate_inventory_sha256}"
    )
    # Filter to exact inventory digest and sorted candidate paths, then call
    # the existing later-action decision for destructive-operation.
```

CLI output is canonical JSON on stdout. It writes no files and exposes no cleanup operation.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_housekeeping_proposal -v`

Expected: authorization and CLI tests pass.

### Task 4: Front-door route, reference, full verification, and review

**Files:**
- Create: `skills/implementing-staged-plans/references/post-closure-housekeeping.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `tests/test_housekeeping_proposal.py`

**Interfaces:**
- Consumes: Tasks 1-3 public API and CLI.
- Produces: package-facing route and human procedure.

- [ ] **Step 1: Add a failing behavior test for the package-facing route**

Create a temporary package fixture whose SKILL contains the new route but whose
reference is absent, then assert `validate_markdown_links` reports the broken
relative link. The test must fail before the production reference exists. Do
not remove or rename any repository path, and do not edit program discovery or
continuation prompting.

- [ ] **Step 2: Write the reference and append the isolated SKILL route**

Document prerequisites, provenance, candidate fields, dry-run behavior, stale revalidation, exact destructive authorization, recoverable proposals, validation commands, and hard stops. Preserve the existing uncommitted program-discovery section byte-for-byte outside the new hunk.

- [ ] **Step 3: Run focused and complete verification once on the final tree**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_housekeeping_proposal -v
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk env PYTHONDWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk git diff --check
```

Expected: zero test failures, package validation passes, and diff hygiene passes.

- [ ] **Step 4: Perform a bounded self-review**

Review only the new housekeeping module, reference, tests, and SKILL hunk for correctness, security/privacy, authorization separation, recovery semantics, test protection, unnecessary complexity, and overlap with user-owned changes. Repair any material defect through a new RED-GREEN cycle, then rerun every final command affected by the repair.

- [ ] **Step 5: Report without staging or committing**

Run: `rtk git status --short --branch`

Report exact changed paths, fresh verification evidence, review findings, reduced-assurance limits, and the mandatory no-cleanup/no-commit stop.
