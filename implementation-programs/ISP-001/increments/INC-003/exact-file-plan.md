# Durable State and Action Authority Implementation Plan

**Goal:** Implement mechanically validated, separately bound program state, increment state, approval modes, workspace selection, and action authorization for one repository-backed implementation program.

**Architecture:** Add one focused standard-library state-authority module with a pure validation/decision core and narrowly bounded atomic persistence functions. Reuse the accepted program-authority loaders and digest/path validation, keep approval policy separate from action authorization, and route the front door to a concise focused procedure. Preserve the existing status schema and accepted history while requiring versioned exact bindings for every new mechanically relied-on event.

**Tech stack:** Python 3 standard library, `unittest`, JSON/JSONL/Markdown repository artifacts, existing package and skill validators.

## Global constraints

- Authority is ISP-001 revision 2, SOURCE-002 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`, program Markdown `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`, accepted traceability artifact `4aecc6614164f43d039bf472a4244a73ecb40050bc3632a0aa60a3cfe7b10f6b`, and atomic semantic digest `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Preserve SOURCE-001, SOURCE-002, prior program revisions, accepted INC-001/INC-002 evidence, `APR-010`, `APR-011`, and the approved semantic digest byte-for-byte except for append-only/addendum updates explicitly named here.
- Base implementation on `main` at accepted INC-002 head `53edb8fad2008c7d35b6c17dbb973b24022947fd` and selected base `f14449b8808574c720927aedab5b64871cc63858`.
- Preserve all accepted uncommitted INC-002 paths. Extend overlapping governance files from their current bytes; never restore them from `HEAD` or reconstruct them from conversation memory.
- The selected mode is `approval:full-increment`, but the user explicitly requires this plan to be approved before implementation. This explicit gate controls.
- Approval mode governs interruption/diff acceptance only. It never grants repository writes, evaluation, commit, pull-request, merge, publication, release, deployment, migration, destructive operation, provider mutation, or external-state authority.
- No commit, subagent/evaluator dispatch, installation, marketplace mutation, push, pull request, publication, release, deployment, migration, destructive operation, provider mutation, or other consequential external action is authorized by this plan.
- Keep reusable/package-facing paths, symbols, commands, tests, fixtures, headings, schemas, and observable identifiers project-neutral. ISP-001 and INC-003 may appear only in repository governance/evidence artifacts.
- Use strict RED-GREEN-REFACTOR for behavior. Record the observed intended RED before implementation. Use explicit alternative verification only for documentation/evidence writes.
- Use `PYTHONDONTWRITEBYTECODE=1` for Python commands. Do not install dependencies or introduce a package manager.
- Stop with INC-003 at `awaiting-diff-approval`. Do not accept the diff, continue to INC-004, close ISP-001, or infer any consequential action.

## Requirements and acceptance binding

| Accepted criterion | Planned evidence |
|---|---|
| Every legal transition succeeds and every illegal transition fails closed | Exhaustive program and increment state-pair tests plus conditional invariant tests and blocked-resume tests |
| All five modes match the approved matrix | One immutable policy table and an exact table-driven test for scope, plan pause, interruption, diff acceptance, and continuation |
| Stale or mismatched approvals, state, workspaces, and briefs are rejected | Field-by-field binding mutation tests covering source/program/semantic/workspace/head/scope/mode/increment/brief/plan/packet/status sequence |
| Atomic updates retain prior-state evidence and schema version | Compare-and-swap atomic-write tests, replacement-failure cleanup tests, JSONL-prefix preservation, and previous-status digest/schema assertions |
| No approval mode implies pull-request, merge, release, deployment, migration, destructive, or provider authority | Cross-product tests for five modes and every consequential action with an empty authorization log, plus exact-grant/mismatch tests |

The implementation advances the eight named requirement groups. Atomic records assigned across multiple increments remain `allocated` unless the INC-003 diff directly demonstrates their contract. The accepted semantic fields and their digest must remain unchanged.

## Exact state contracts

### Program transition matrix

The module defines these unconditional edges:

```python
PROGRAM_TRANSITIONS = {
    "captured": frozenset({"awaiting-program-approval", "blocked", "superseded"}),
    "awaiting-program-approval": frozenset({"active", "blocked", "superseded"}),
    "active": frozenset({"blocked", "awaiting-closure-approval", "superseded"}),
    "blocked": frozenset(),
    "awaiting-closure-approval": frozenset({"active", "blocked", "closed", "superseded"}),
    "closed": frozenset(),
    "superseded": frozenset(),
}
```

`blocked` resumes only to `blocked_context.resume_program_state`, which must itself be a valid nonterminal state captured when blocking. `closed` and `superseded` are terminal. `awaiting-closure-approval -> active` represents an explicit closure change request; `-> closed` requires a bound closure packet and closure approval.

### Increment transition matrix

```python
INCREMENT_TRANSITIONS = {
    "not-started": frozenset({"preparing", "blocked", "superseded"}),
    "preparing": frozenset({"awaiting-plan-approval", "authorized", "blocked", "superseded"}),
    "awaiting-plan-approval": frozenset({"authorized", "change-requested", "blocked", "superseded"}),
    "authorized": frozenset({"implementing", "blocked", "superseded"}),
    "implementing": frozenset({"reviewing", "blocked", "superseded"}),
    "reviewing": frozenset({"remediating", "verified", "blocked", "superseded"}),
    "remediating": frozenset({"reviewing", "blocked", "superseded"}),
    "verified": frozenset({"awaiting-diff-approval", "accepted", "blocked", "superseded"}),
    "awaiting-diff-approval": frozenset({"accepted", "change-requested", "blocked", "superseded"}),
    "accepted": frozenset(),
    "change-requested": frozenset({"preparing", "blocked", "superseded"}),
    "blocked": frozenset(),
    "superseded": frozenset(),
}
```

`blocked` resumes only to the recorded `resume_increment_state`. Moving from an accepted increment to a different increment is `start_increment`, not an `accepted -> preparing` same-increment edge. It requires program state `active`, a valid workspace, a matching preparation authorization, and either renewed one-increment user authority or `approval:full` with a suitable current conversation.

### Conditional transition gates

- `awaiting-program-approval -> active`: exact approved program event and valid source/program authority.
- any repository-writing increment transition from `preparing` onward: selected matching workspace and action authorization.
- `preparing -> awaiting-plan-approval`: current brief and persisted pending exact-file-plan digest.
- `preparing -> authorized`: only a mode without a routine plan pause, current brief/plan bindings, and separate implementation authorization; an explicit user plan gate still forces `awaiting-plan-approval`.
- `awaiting-plan-approval -> authorized`: exact approved plan event plus separate implementation authorization.
- `implementing -> reviewing`: frozen diff evidence.
- `reviewing -> remediating`: at least one unresolved material finding.
- `reviewing -> verified`: no unresolved material findings plus fresh verification binding.
- `verified -> accepted`: only `approval:full-diff` or `approval:full`, with a complete packet binding and separate state-write authorization.
- `verified -> awaiting-diff-approval`: `approval:standard`, `approval:pre-approve`, or `approval:full-increment`.
- `awaiting-diff-approval -> accepted`: exact approved diff event.
- any `-> blocked`: block evidence, violated invariant, required decision, recommended option, and legal resume target.
- `awaiting-closure-approval -> closed`: complete reconciliation/closure packet plus exact closure approval; acceptance of the current increment is insufficient.

### Approval-mode policy

```python
APPROVAL_MODE_POLICIES = {
    "approval:standard": {
        "scope": "one-increment",
        "routine_plan_pause": True,
        "interruptions": ("material-decision", "contradiction", "hard-stop"),
        "diff_acceptance": "user",
        "automatic_continuation": False,
    },
    "approval:pre-approve": {
        "scope": "one-increment",
        "routine_plan_pause": False,
        "interruptions": ("user-owned-decision", "program-amendment", "contradiction", "hard-stop"),
        "diff_acceptance": "user",
        "automatic_continuation": False,
    },
    "approval:full-increment": {
        "scope": "one-increment",
        "routine_plan_pause": False,
        "interruptions": ("hard-stop",),
        "diff_acceptance": "user",
        "automatic_continuation": False,
    },
    "approval:full-diff": {
        "scope": "one-increment",
        "routine_plan_pause": False,
        "interruptions": ("hard-stop",),
        "diff_acceptance": "automatic-after-verification-and-packet",
        "automatic_continuation": False,
    },
    "approval:full": {
        "scope": "conversation-bounded-multiple-increments",
        "routine_plan_pause": False,
        "interruptions": ("hard-stop",),
        "diff_acceptance": "automatic-after-verification-and-packet",
        "automatic_continuation": True,
    },
}
```

Unknown or omitted mode resolves to `approval:standard` only when creating a new record; an unknown mode in persisted state is an error, not a default.

### Status persistence

Continue using `implementation-program-status/v1`. Keep `program_state` and `current_increment_state` separate. Every newly written status includes:

```json
{
  "schema_version": "implementation-program-status/v1",
  "state_sequence": 19,
  "program_id": "ARCHIVE-PROGRAM",
  "program_revision": 1,
  "program_state": "active",
  "current_increment_id": "ARCHIVE-INDEX",
  "current_increment_state": "authorized",
  "approval_mode": "approval:standard",
  "source_binding": {"source_id": "ARCHIVE-SOURCE", "sha256": "1111111111111111111111111111111111111111111111111111111111111111"},
  "program_binding": {"sha256": "2222222222222222222222222222222222222222222222222222222222222222", "semantic_requirements_sha256": "3333333333333333333333333333333333333333333333333333333333333333"},
  "brief_binding": {
    "path": "increments/archive-index/brief.md",
    "sha256": "4444444444444444444444444444444444444444444444444444444444444444",
    "workspace_sha256": "5555555555555555555555555555555555555555555555555555555555555555",
    "head_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "approved_exact_file_plan_sha256": "6666666666666666666666666666666666666666666666666666666666666666",
  "pending_exact_file_plan_sha256": null,
  "previous_state": {
    "schema_version": "implementation-program-status/v1",
    "status_sha256": "7777777777777777777777777777777777777777777777777777777777777777",
    "state_sequence": 18,
    "program_state": "active",
    "current_increment_id": "ARCHIVE-INDEX",
    "current_increment_state": "awaiting-plan-approval",
    "transition_event_id": "ARCHIVE-PLAN-APPROVAL"
  }
}
```

New records may retain additional existing verification/next-action fields. The validator requires the controlling fields above, rejects unknown schema versions, and checks state-specific plan/packet/verification invariants. Accepted historical v1 state remains evidence; the first INC-003 transition supplies the stronger previous-state digest without rewriting history.

### Approval binding

New mechanically relied-on approval records use `implementation-approval/v1` and bind:

```json
{
  "schema_version": "implementation-approval/v1",
  "event_id": "ARCHIVE-PLAN-APPROVAL",
  "type": "exact-file-plan-approval",
  "decision": "approved",
  "program_id": "ARCHIVE-PROGRAM",
  "program_revision": 1,
  "source_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
  "program_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
  "semantic_requirements_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
  "increment_id": "ARCHIVE-INDEX",
  "brief_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
  "exact_file_plan_sha256": "6666666666666666666666666666666666666666666666666666666666666666",
  "approval_mode": "approval:standard",
  "workspace": {
    "path": "/srv/portable-archive",
    "branch": "archive-maintenance",
    "base_commit": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "head_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "scope": ["authorize the bound archive-index plan"]
}
```

Diff and closure approvals additionally bind the review/closure packet digest and verified status sequence. Duplicate matching events are rejected as ambiguous; rejected or conflicting events fail closed. Schema-less historical events may corroborate preserved history but never grant a new mechanically checked transition.

### Workspace selection

`implementation-workspace/v1` remains the selected-workspace schema. `select_workspace` records repository identity, real path, branch, base/head observation, staged/modified/untracked/conflicted paths, active Git operation, selection authority, and optional prior-workspace digest. It requires an exact workspace-selection approval and action authorization. Validation compares an explicit caller-supplied `RepositoryObservation`; it does not run Git or classify drift in INC-003.

### Action authorization

New grants use `implementation-action-authorization/v1` and bind the same source/program/increment/mode/workspace/head/brief/plan tuple plus an exact non-empty action list, scopes, constraints, and exclusions. Supported action names are:

```python
ACTION_NAMES = frozenset({
    "write-program-artifact",
    "create-workspace",
    "modify-workspace",
    "run-local-verification",
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
})
```

Authorization is exact: a grant for one action, scope, increment, head, or plan does not authorize another. Expired, rejected, revoked, stale, schema-less, or conflicting records do not grant. Approval policies contain no action names and cannot produce an authorization decision.

### Atomic update boundary

`atomic_replace_json` and `atomic_append_json_line`:

1. reject symlinked controlling paths and invalid parent directories;
2. compare the current file digest with `expected_sha256` immediately before writing;
3. serialize deterministic UTF-8 JSON with sorted keys, two-space indentation, and one trailing newline, or preserve the exact JSONL byte prefix and append one canonical line;
4. create the temporary file in the target directory with `NamedTemporaryFile(delete=False)`;
5. flush and `os.fsync` the temporary file;
6. `os.replace` the temporary path over the target;
7. clean the temporary path on pre-replacement failure;
8. return old/new digests in a receipt.

The status payload contains the old status digest/schema/sequence as previous-state evidence. Per-file replacement is atomic on supported same-filesystem paths; no multi-file transaction, lock, or hostile-concurrency guarantee is claimed.

## Public interfaces

`skills/implementing-staged-plans/scripts/state_authority.py` produces:

```python
@dataclass(frozen=True)
class RepositoryObservation:
    repository: str
    path: str
    branch: str
    base_commit: str
    head_commit: str
    staged_paths: tuple[str, ...]
    modified_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]
    conflicted_paths: tuple[str, ...]
    active_git_operation: str | None

@dataclass(frozen=True)
class TransitionRequest:
    expected_status_sha256: str
    expected_state_sequence: int
    target_program_state: str
    target_increment_id: str
    target_increment_state: str
    transition_event_id: str
    action_authorization_id: str
    evidence: dict[str, object]

@dataclass(frozen=True)
class StateTransitionReceipt:
    prior_sha256: str
    current_sha256: str
    state_sequence: int
    program_state: str
    increment_id: str
    increment_state: str

def approval_mode_policy(mode: str | None, *, creating: bool = False) -> ApprovalModePolicy: ...
def validate_workspace_selection(workspace: dict[str, object], observation: RepositoryObservation) -> list[str]: ...
def validate_brief_binding(program_root: Path, manifest: dict[str, object], status: dict[str, object], workspace_sha256: str, observation: RepositoryObservation) -> list[str]: ...
def validate_state(program_root: Path, manifest: dict[str, object], status: dict[str, object], observation: RepositoryObservation) -> list[str]: ...
def validate_approval_binding(records: list[dict[str, object]], required: ApprovalBinding) -> list[str]: ...
def decide_action_authorization(records: list[dict[str, object]], required: ActionBinding) -> AuthorizationDecision: ...
def evaluate_transition(current: dict[str, object], request: TransitionRequest, context: TransitionContext) -> TransitionDecision: ...
def validate_state_authority(program_root: Path, observation: RepositoryObservation) -> list[str]: ...
def select_workspace(program_root: Path, selection: WorkspaceSelection, expected_sha256: str | None) -> WorkspaceSelectionReceipt: ...
def apply_state_transition(program_root: Path, request: TransitionRequest, observation: RepositoryObservation) -> StateTransitionReceipt: ...
def atomic_replace_json(path: Path, value: dict[str, object], expected_sha256: str) -> AtomicWriteReceipt: ...
def atomic_append_json_line(path: Path, value: dict[str, object], expected_sha256: str) -> AtomicWriteReceipt: ...
```

The CLI exposes `validate-state`, `select-workspace`, `transition-state`, and `check-action`. Mutating commands require an explicit JSON request carrying expected digests and event/authorization IDs. Exit statuses are 0 for success/authorized, 1 for invariant failure/not authorized, and 2 for usage errors. Output is deterministic and never includes source contents, tokens, credentials, or secret values.

## File map

### Already created at this planning gate

- `implementation-programs/ISP-001/increments/INC-003/brief.md` — lean semantic invocation record.
- `implementation-programs/ISP-001/increments/INC-003/preparation.md` — authority, repository evidence, design comparison, official evidence, risks, and boundaries.
- `implementation-programs/ISP-001/increments/INC-003/exact-file-plan.md` — this frozen implementation plan.

### Create during authorized implementation

- `skills/implementing-staged-plans/references/state-authorization.md` — focused operator procedure for state, mode, workspace, approval, atomic update, and action gates.
- `skills/implementing-staged-plans/scripts/state_authority.py` — standard-library transition, binding, workspace, authorization, persistence, and CLI implementation.
- `tests/test_state_authority.py` — exhaustive state-pair, mode, binding, workspace, authorization, atomic-write, CLI, and current-program tests.
- `tests/fixtures/state-authorization/portable-archive-run/state/status.json` — neutral lifecycle seed.
- `tests/fixtures/state-authorization/portable-archive-run/state/workspace.json` — neutral selected-workspace seed rewritten to the temporary test path.
- `tests/fixtures/state-authorization/portable-archive-run/state/approvals.jsonl` — neutral versioned program/plan/diff/closure approval cases.
- `tests/fixtures/state-authorization/portable-archive-run/state/action-authorizations.jsonl` — neutral exact action grants and exclusions.
- `tests/fixtures/state-authorization/portable-archive-run/increments/archive-index/brief.md` — neutral digest-bound brief.
- `tests/fixtures/state-authorization/portable-archive-run/increments/archive-index/exact-file-plan.md` — neutral plan binding.
- `tests/fixtures/state-authorization/portable-archive-run/increments/archive-index/review-packet.md` — neutral packet binding for automatic-diff tests.
- `implementation-programs/ISP-001/increments/INC-003/execution-record.md` — observed RED/GREEN/refactor commands, transition evidence, binding digests, deviations, and limitations.
- `implementation-programs/ISP-001/increments/INC-003/reviews/requirements.md` — acceptance/matrix/authority review.
- `implementation-programs/ISP-001/increments/INC-003/reviews/architecture.md` — state-boundary, atomicity, security, naming, and simplicity review.
- `implementation-programs/ISP-001/increments/INC-003/reviews/test-evidence.md` — exhaustive-matrix and failure-evidence review.
- `implementation-programs/ISP-001/increments/INC-003/review-packet.md` — human diff handoff.
- `implementation-programs/ISP-001/increments/INC-003/handoff.md` — durable continuation record that stops before INC-004.

### Modify during authorized implementation

- `skills/implementing-staged-plans/SKILL.md:60-78` — add one narrow state/authorization route after universal gates and after the program-authority route.
- `skills/implementing-staged-plans/scripts/validate_package.py:13-22,286-304` — require the state reference/script as regular non-symlink assets through the existing asset validator.
- `tests/test_package_validation.py:13-27,57-80,285-301` — include both state assets in valid fixtures and missing-asset tests.
- `tests/test_front_door_contract.py:29-85` — require the focused state route while preserving the under-250-line front-door contract.
- `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json` — add only directly proven INC-003 implementation/verification evidence and dispositions; preserve order and every semantic field and assert the semantic digest remains exact.
- `implementation-programs/ISP-001/manifest.json` — update current INC-003 evidence/status/logical-role bindings and artifact digests from the current accepted bytes.
- `implementation-programs/ISP-001/state/status.json` — advance only through authorized INC-003 lifecycle states and end at `awaiting-diff-approval`, preserving prior digest/schema/sequence evidence.
- `implementation-programs/ISP-001/state/approvals.jsonl` — append versioned plan/diff approval events only when explicitly supplied; never edit prior lines.
- `implementation-programs/ISP-001/state/action-authorizations.jsonl` — append bounded versioned implementation/action authority only when explicitly supplied; never edit prior lines.

### Preserve unchanged

- `implementing-staged-plans-consolidated-design-plan-final.md`.
- `implementation-programs/ISP-001/source/**`, including SOURCE-001 and SOURCE-002.
- `implementation-programs/ISP-001/program/implementation-program.md` and `program/traceability.json` for revision 1.
- `implementation-programs/ISP-001/program/revisions/revision-2/implementation-program.md`.
- every accepted INC-001 and INC-002 artifact, review, packet, handoff, and addendum.
- `skills/implementing-staged-plans/scripts/program_authority.py`, `references/program-authority.md`, and `tests/fixtures/program-authority/**`.
- `.gitignore`, `.codex-plugin/plugin.json`, and `skills/implementing-staged-plans/agents/openai.yaml`.
- all pressure evidence and unrelated user-owned files.

## Semantic naming inventory

| Proposed surface | Stable context and intention | Governance-term basis |
|---|---|---|
| `references/state-authorization.md` | Procedure controlling lifecycle state and action authority | “state” names the durable implemented domain |
| `scripts/state_authority.py` | Mechanical state and authorization trust boundary | “state” names the durable implemented domain |
| `validate_state_authority` | Validates complete persisted lifecycle bindings | none |
| `RepositoryObservation` | Caller-supplied current repository facts | none |
| `TransitionRequest` / `TransitionDecision` | Requested and evaluated lifecycle movement | “transition” is a durable state-machine concept |
| `ApprovalModePolicy` | Immutable interpretation of one approved mode | “approval mode” is a public workflow contract |
| `AuthorizationDecision` | Exact action-grant result | none |
| `atomic_replace_json` | Atomic mutable-record replacement | none |
| `portable-archive-run` / `archive-index` | Fictional pilot domain | no roadmap coordinate |
| ISP-001/INC-003 paths and headings | Repository implementation governance and evidence | explicitly permitted governance records |

No distributable filename, symbol, command, test title, fixture title, schema identifier, or generated path is named from the ISP-001 increment sequence.

---

### Task 0: Bind plan approval and separate implementation authority

**Files:**

- Modify: `implementation-programs/ISP-001/state/status.json`
- Modify: `implementation-programs/ISP-001/state/approvals.jsonl`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl`

**Produces:** A digest-bound approved plan and a separate bounded authorization before package, test, fixture, traceability, or implementation-evidence writes.

- [ ] **Step 1: Revalidate the frozen basis**

Confirm current branch/head, selected base/workspace, all dirty paths, SOURCE-001/SOURCE-002, both program revisions, accepted traceability/semantic digests, INC-001/INC-002 accepted evidence, this plan digest, and absence of a conflicting Git operation. Stop on any unexpected overlap or binding change.

- [ ] **Step 2: Append exact plan approval**

Append one `implementation-approval/v1` event binding ISP-001 revision 2, SOURCE-002/program/semantic digests, `main`, selected base/current head, INC-003 brief digest, this plan digest, `approval:full-increment`, decision `approved`, and the explicit user-requested plan gate.

- [ ] **Step 3: Append separate action authorization**

Append one `implementation-action-authorization/v1` event naming exactly the package/reference/script/test/fixture/traceability/evidence files in this plan, deterministic local verification, three non-independent review passes, evidence-backed remediation, and any explicitly authorized focused local commits. Retain every external/consequential exclusion.

- [ ] **Step 4: Transition only to `authorized`**

Update status atomically from the exact pending-plan digest/sequence to `authorized`, embedding the prior status digest/schema/sequence and approval/authorization IDs. Do not begin the RED test in the same state-write operation.

### Task 1: Define the full state and authority contract through failing tests

**Files:**

- Create: `tests/test_state_authority.py`
- Create: the seven neutral overlay files under `tests/fixtures/state-authorization/portable-archive-run/`

**Interfaces:**

- Consumes: the exact matrices, mode table, bindings, and action names in this plan.
- Produces: executable expectations for state validation, workspace selection, mode interpretation, approval matching, action decisions, atomic updates, and CLI behavior.

- [ ] **Step 1: Add the neutral fixture composition helper**

Copy the accepted `portable-archive-program` authority fixture into a temporary directory, overlay the seven state-authorization files, patch only temp-path/head/digest values, and import `state_authority.py` by path with the sibling script directory temporarily available for `program_authority` reuse.

- [ ] **Step 2: Exhaust every program-state pair**

For all 49 ordered pairs, assert every declared edge succeeds and every undeclared edge fails. Separately cover exact blocked-state resume, terminal closed/superseded states, closure-packet/approval gates, and program/increment contradiction cases.

- [ ] **Step 3: Exhaust every increment-state pair**

For all 169 ordered pairs across the thirteen persisted labels in the matrix, assert every declared edge succeeds and every undeclared edge fails. Separately cover new-increment start, plan/brief/workspace prerequisites, review/remediation/verification evidence, mode-controlled diff acceptance, one-increment continuation refusal, and full-mode conversation suitability.

- [ ] **Step 4: Test the five-mode matrix exactly**

Compare every policy field for all five modes. Assert omitted mode defaults only during creation, while unknown persisted modes fail. Assert an explicit plan gate overrides the routine-pause field without changing the mode.

- [ ] **Step 5: Test stale/mismatched bindings**

Mutate source ID/digest, program ID/revision/digest, semantic digest, workspace path/branch/base/head, scope, mode, increment, brief path/digest, plan digest, packet digest, status sequence, decision, event ID, duplicate/conflicting event, schema, and symlink path one at a time; require deterministic rejection.

- [ ] **Step 6: Test action separation**

For each mode and each consequential action, assert no authorization log means not authorized. Assert one exact action grant succeeds only for its bound tuple; stale, revoked, expired, schema-less, differently scoped, differently headed, and conflicting grants fail.

- [ ] **Step 7: Test atomic persistence and CLI statuses**

Cover successful status replacement, previous digest/schema/sequence evidence, compare-and-swap mismatch, `os.replace` failure preserving old bytes and cleaning the temp, JSONL prefix preservation, duplicate ID rejection, write/`fsync` failure, deterministic issue order, success 0, invariant/not-authorized 1, and usage 2.

- [ ] **Step 8: Run focused tests and record the intended RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority -v
```

Expected: import failure naming the absent `skills/implementing-staged-plans/scripts/state_authority.py`. Record the exact failure before creating implementation code.

### Task 2: Implement pure policies, bindings, and transition decisions

**Files:**

- Create: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `tests/test_state_authority.py` only if the test harness, not an accepted contract, is wrong

**Produces:** Constants, typed records, and pure validators/decisions without repository mutation.

- [ ] **Step 1: Reuse accepted authority primitives**

Import the sibling module's `sha256_file`, `load_json_object`, `load_json_lines`, `resolve_managed_path`, and `validate_program_authority`. Do not modify or duplicate the accepted source/program authority implementation.

- [ ] **Step 2: Implement exact constants and typed records**

Add the matrices, five policies, action names, state/schema sets, binding dataclasses, decision dataclasses, and deterministic helper validation. Keep all collections immutable at module scope.

- [ ] **Step 3: Implement workspace and brief freshness validation**

Validate selected-workspace schema and program binding, compare the explicit repository observation, verify current brief/plan paths and digests through manifest logical roles, and reject symlinked controlling paths. Leave Git discovery/drift classification out of scope.

- [ ] **Step 4: Implement approval and action matching**

Require one exact versioned matching event, reject non-approved/revoked/expired/conflicting/duplicate matches, and return structured decisions. Never consult approval mode when deciding action authority.

- [ ] **Step 5: Implement state and transition invariants**

Validate schema, source/program/workspace/brief/plan bindings, program/increment consistency, state-specific evidence, state sequence, previous-state evidence, blocked context, closure gates, and new-increment rules. `evaluate_transition` remains pure and returns all sorted issues.

- [ ] **Step 6: Run focused policy tests**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority.StateMatrixTests tests.test_state_authority.ApprovalModeTests tests.test_state_authority.BindingTests tests.test_state_authority.ActionAuthorizationTests -v
```

Expected: pure matrix, mode, binding, and authorization tests pass; atomic persistence tests remain RED.

### Task 3: Implement atomic persistence, workspace selection, and CLI routing

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `tests/test_state_authority.py` only for implementation-specific failure injection fixtures

**Produces:** Safe per-file writes plus usable read/write command routes with explicit authorization inputs.

- [ ] **Step 1: Implement deterministic atomic writers**

Use same-directory `NamedTemporaryFile(delete=False)`, canonical bytes, flush, `os.fsync`, expected-digest compare-and-swap, `os.replace`, cleanup, and old/new digest receipts. Reject target/parent symlinks. Preserve exact JSONL prefix bytes and reject blank/corrupt prior logs.

- [ ] **Step 2: Implement workspace selection**

Validate exact workspace-selection approval and `create-workspace` authorization, construct `implementation-workspace/v1` from `RepositoryObservation`, include prior-workspace digest when replacing a selection, and atomically persist one file. Do not create branches/worktrees or run Git.

- [ ] **Step 3: Implement state application**

Reload and revalidate immediately before mutation, compare request sequence/digest, evaluate the transition, require its exact action grant, embed prior-state evidence, increment sequence once, atomically replace status, and return the receipt. Orphaned approval/authorization log records are inert if status write fails; do not claim multi-file atomicity.

- [ ] **Step 4: Implement deterministic CLI behavior**

`validate-state` and `check-action` are read-only. `select-workspace` and `transition-state` require explicit JSON request paths and expected digests. Catch repository-data/usage errors, return 0/1/2, sort issues, and never print secret values or file contents.

- [ ] **Step 5: Run all focused state tests**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority -v
```

Expected: every state, mode, binding, workspace, authorization, atomic-write, and CLI test passes.

### Task 4: Add the focused procedure and front-door route

**Files:**

- Create: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Modify: `tests/test_package_validation.py`
- Modify: `tests/test_front_door_contract.py`

**Produces:** A concise discoverable package route without duplicating the state procedure.

- [ ] **Step 1: Extend structural tests and observe RED**

Require the state reference/script in valid fixtures; reject either missing/symlink asset; require the front door link for lifecycle state, approval modes/bindings, workspace selection, and action authorization; retain the under-250-line and project-neutral naming contracts.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_front_door_contract -v
```

Expected: failures naming the missing state assets/route.

- [ ] **Step 2: Write `state-authorization.md`**

Document, in order: prerequisites; persisted authority reload; program/increment separation; legal transitions; blocked recovery; exact approval binding; five-mode behavior; workspace selection/validation; separate action authorization; atomic per-file update contract; validation commands; hard stops; and bounded result. State that approval mode never creates action authority and that the writer does not claim multi-file atomicity.

- [ ] **Step 3: Add the narrow front-door route**

Route current-state validation, transition, approval-mode/binding, workspace-selection, and action-authorization work to `[State and action authorization](references/state-authorization.md)`. Preserve the existing program-authority route and fallback.

- [ ] **Step 4: Extend package validation**

Add state asset constants and include them in `validate_authority_assets`. Reuse the existing regular non-symlink, Markdown-link, and naming scans. Do not add a new general asset framework.

- [ ] **Step 5: Run focused structural tests**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_front_door_contract -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: all commands pass.

### Task 5: Validate the neutral pilot and current ISP-001 state

**Files:**

- Complete: `tests/fixtures/state-authorization/portable-archive-run/**`
- Modify: `tests/test_state_authority.py`
- Modify: `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
- Modify: `implementation-programs/ISP-001/manifest.json`
- Modify: `implementation-programs/ISP-001/state/status.json`

**Produces:** One neutral mechanically valid lifecycle fixture and honest current-program evidence without semantic-digest drift.

- [ ] **Step 1: Exercise the neutral lifecycle**

Validate program authority, select a workspace, bind a brief/plan, traverse every legal state for one increment, exercise user diff acceptance under `approval:standard`, separately exercise automatic acceptance under `approval:full-diff`, prove no automatic continuation, and test blocked/resume. Use a fresh fixture per path so terminal states are never rewritten.

- [ ] **Step 2: Validate current ISP-001 state read-only**

Build `RepositoryObservation` from the already revalidated `main` facts and run `validate-state`. Historical schema-less approvals/authorizations remain preserved but do not count as future grants. The current versioned INC-003 events/status created during authorized execution must form the active mechanical binding.

- [ ] **Step 3: Update traceability evidence without changing semantics**

Add implementation and verification evidence only to atomic records directly proven by INC-003 source sections and acceptance criteria. Leave cross-increment/global obligations allocated where this diff does not complete them. Preserve the ordered values of `id`, `group_id`, `source_unit_ids`, `normalized_requirement`, `acceptance_criteria`, `assigned_parts`, `assigned_tasks`, and `assigned_increments`; assert `compute_semantic_requirements_digest` remains `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.

- [ ] **Step 4: Advance only to `awaiting-diff-approval`**

After review/remediation/final verification, atomically write status with fresh verification binding and previous-state digest/schema/sequence, update manifest artifact/current-role digests from the current bytes, and stop. Do not append or synthesize diff approval.

### Task 6: Review, verify, and build the INC-003 packet

**Files:**

- Create: INC-003 execution record, three review reports, review packet, and handoff listed above.
- Modify: only the authorized governance/evidence fields named in Tasks 0 and 5.

**Produces:** A reviewed INC-003 diff at `awaiting-diff-approval`, with no INC-004 work.

- [ ] **Step 1: Freeze the proposed diff**

Record accepted base/head, current head, authorized commits if any, changed paths, dirty-state preservation, approval/authorization IDs, exact source/program/semantic/plan digests, and neutral/current state receipts.

- [ ] **Step 2: Run three separate non-independent reviews**

Requirements review checks both complete matrices, all five modes, every binding field, workspace/brief freshness, action separation, accepted criteria, and no INC-004 leakage. Architecture review checks pure/mutation boundaries, program-authority reuse, atomic-write safety, symlink/path behavior, multi-file/concurrency claim limits, secret handling, semantic naming, and unnecessary complexity. Test-evidence review checks observed RED, state-pair coverage, conditional-edge coverage, failure injection, CLI results, and evidence limits. Persist raw reports before reconciliation and label them non-independent with reduced assurance.

- [ ] **Step 3: Repair only material INC-003 findings**

Record affected requirement, evidence, impact, confidence, smallest repair, and rerun. Stop for a program amendment if a repair changes approved outcome, acceptance, public contract, source/program authority, sequencing, risk posture, or later-increment boundary.

- [ ] **Step 4: Run fresh final verification once**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program tests/fixtures/program-authority/portable-archive-program
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/state_authority.py validate-state implementation-programs/ISP-001 --repository /Users/CoveMB/Code/CoveMB/implementation-plugin --branch main --base f14449b8808574c720927aedab5b64871cc63858 --head "$(rtk git rev-parse HEAD)"
rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans
rtk git diff --check
rtk git status --short --branch
```

Expected: tests, package, neutral/current program authority, current state authority, quick validation, whitespace, and bounded status checks pass. The execution record captures the resolved head emitted by the nested read-only Git command.

- [ ] **Step 5: Build the review packet**

Include achieved outcome, requirement/acceptance disposition, state and mode matrices, changed files by purpose, review order, RED/GREEN/final results, current and neutral state receipts, binding mutation coverage, action-separation proof, atomicity/concurrency limits, semantic digest preservation, reviews/findings/repairs, deviations, naming inventory, edge cases, security/privacy implications, rollback/recovery, workspace/base/head/commits, current state, and next legal action.

- [ ] **Step 6: End at the mandatory boundary**

Set INC-003 to `awaiting-diff-approval`. Do not accept the diff, begin INC-004, close the program, or perform any consequential external action.

## Focused commit boundaries if separately authorized

1. `test: define state authority contracts` — Task 1 tests and neutral state fixture.
2. `feat: enforce lifecycle state and approval modes` — Task 2 pure matrices, policies, bindings, and tests.
3. `feat: gate workspace and action authority` — Task 3 atomic persistence, workspace selection, action decisions, CLI, and passing focused tests.
4. `feat: route state authorization workflow` — Task 4 reference, front-door route, package validation, and tests.
5. `docs: record increment 3 review evidence` — Tasks 5-6 current traceability/state, reviews, packet, handoff, and final status.

Commit messages are proposed review boundaries only. Do not stage or commit anything unless the later action authorization explicitly includes these exact local commits.

## Rollback and recovery

- No data, deployment, provider, marketplace, installation, production, or external state is touched.
- Before commits, recover by editing only named INC-003 files and append-only additions; never reset, clean, stash, overwrite, or discard accepted/user work.
- Per-file state/log updates use old/new digest receipts. If an authorization/approval append succeeds but a later status update fails, retain the inert append-only event, report the partial update, and retry only against the newly observed exact digests.
- Never roll back immutable sources, prior programs, accepted packets, approvals, or authorizations. Corrections use addenda, revocation/supersession events, or a new program revision.
- After separately authorized commits, any proposed reversion targets only the focused INC-003 commits and requires explicit authorization before execution.
- The implementation does not claim a transaction spanning manifest, status, and logs, nor protection against a privileged or hostile concurrent filesystem writer.

## Approval required to execute

The next legal approval must bind ISP-001 revision 2, SOURCE-002/program/semantic digests, the current accepted traceability artifact, `main`, selected base, the current head and dirty state after these governance writes, INC-003 brief digest, and this exact-file-plan digest. It must separately authorize:

1. the named state reference, Python module, tests, neutral fixtures, package route/validator tests, traceability evidence, and INC-003 evidence writes;
2. atomic status/append-only log updates and deterministic local verification;
3. three separate non-independent review passes and evidence-backed remediation limited to material INC-003 findings;
4. the five focused local commits only if desired.

It must preserve all prohibitions on INC-004, subagent/evaluator dispatch unless separately requested, installation, marketplace change, push, pull request, publication, release, deployment, migration, destructive action, provider mutation, and consequential external state.
