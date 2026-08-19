# Continuation, Recovery, and Approval Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan sequentially, task by task. For every behavioral slice, use `superpowers:test-driven-development`; use `superpowers:systematic-debugging` for any unexpected failure; use `superpowers:verification-before-completion` before a completion claim; and use `superpowers:requesting-code-review` only at the single final review gate defined below. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release version `0.1.2` with exact `accept-continue`, distinct later continuation after `accept-stop`, status-current successor authority, immutable-manifest rollover, successor exact-plan materialization, prompt-bound blocked recovery, and a causal multi-increment regression, without weakening Plan A's first-increment or closure contracts.

**Architecture:** Extend Plan A's canonical diff-disposition candidate with one optional, topologically derived continuation projection. One direct `accept-continue` submission first persists diff approval and accepted-current status, then persists rollover action authority, a distinct successor grant, navigation, rollover record, and successor status last. A separate accepted-state prompt performs the same continuation suffix after a prior `accept-stop` without reusing its checkpoint or approval. Blocked entry derives resume context at its production sink; exact resolution submission appends action authority and a manifest-owned resolution record before status. All successor plans reuse Plan A's future-write derivation, exact-plan materialization, execution-baseline, review, accept-stop, and closure interfaces.

**Tech Stack:** Python 3 standard library, frozen dataclasses, canonical JSON and JSON Lines, exact Markdown prompts, Git porcelain-v2 observations, `unittest`, subprocess fixtures, optional isolated Codex evaluator harness, and synchronized plugin metadata.

**Spec:** `docs/superpowers/specs/2026-08-15-staged-plan-repair-split-design.md`

**Required predecessor:** `docs/superpowers/plans/2026-08-15-program-bootstrap-launch-repair.md` implemented, verified, independently reviewed, and unchanged at version `0.1.1`.

## Global Constraints

- Begin only after freshly verifying the completed Plan A tree, its package version `0.1.1`, full-suite evidence, independent-review disposition, frozen compatibility-fixture inventory, branch, HEAD, and complete dirty inventory.
- If an implemented Plan A signature or behavior differs from the interface recorded below, stop and reconcile this plan before any Plan B source edit. Do not silently adapt during mutation.
- Treat this plan as version `0.1.2`'s sole owner. Plan A remains version `0.1.1`'s sole owner.
- Preserve every user-owned and Plan A-owned staged, unstaged, untracked, committed, generated, accepted, and fixture byte unless this plan explicitly lists it under `Modify` or `Create`.
- Never reset, clean, restore, stash, amend, overwrite, rewrite accepted legacy bytes, or mutate the frozen `0.1.1` compatibility fixture.
- Use `rtk` for every repository command. Do not fetch unless remote freshness becomes material to a verified requirement.
- Do not edit installed plugin caches, `implementation-programs/ISP-001/**`, frozen historical evaluator outputs, or Plan A's implementation plan.
- Do not install, publish, deploy, push, open a pull request, access a provider, run a live evaluator, change permissions, or perform destructive or external work without its own explicit authority.
- Commits are outside routine task execution. If the user separately grants local-commit authority, use the logical boundaries reported at the end; otherwise do not stage or commit.
- Preserve accepted legacy current-increment behavior for `approval:full-diff` and `approval:full`, but stop every legacy successor boundary before writes with `legacy-rollover-upgrade-required`. Do not migrate a legacy manifest, first exact plan, or automatic mode into the new transaction.
- Every successor exact plan must call Plan A's `required_future_lifecycle_writes(...)`; no successor may rely only on the first-increment file map.
- All prompt and record identifiers are acyclic and topologically derived. No seed contains its own derived identifier, later record bytes/digests, later status digest, or submitted-prompt digest.
- All persistence uses no-overwrite creation, exact JSON Lines append/adopt, and expected digest/sequence compare-and-swap. Status is last within acceptance, rollover, and blocked-resolution transactions.
- Handoffs and bounded results are navigation only. Only exact direct-user submission of the current canonical prompt supplies prompt-derived action authority.
- Every task produces one coherent, independently testable deliverable. End each task with the listed focused checks and focused self-review; do not ask the user for routine task approval.
- Use alternative verification only for non-behavioral documentation, metadata, or optional-evaluator protocol changes where a behavioral unit test would be artificial. Record command, exit, inputs, evidence, and limitation.
- Run package validation and the full deterministic suite exactly once on the final unchanged `0.1.2` candidate. Then obtain exactly one bounded independent material review from a reviewer who did not implement the candidate.
- Reviewer output is evidence, not repair or action authority. Repair only a validated material defect within scope; rerun invalidated checks; request one focused follow-up tied to that defect. Never repeat review of an unchanged candidate.
- Stop for a material contradiction, changed requirement, unexpected user-owned overlap, unrepairable validator failure, scope expansion, new compatibility decision, absent commit authority when a commit is requested, or any destructive, installation, publication, provider, or external action.

## Plan B Ownership

Plan B owns:

- structured bounded continuation results that use Plan A's shared prompt envelope;
- optional `Accept and continue to <successor-id>` rendering and persistence;
- a distinct accepted-state continuation prompt after `accept-stop`;
- prompt-derived rollover action authorization and successor increment grant;
- immutable-manifest, authority-first, status-last rollover and fresh-prefix recovery;
- inherited accepted product history and successor exact-plan materialization;
- sink-derived blocked entry and prompt-bound managed resolution;
- `0.1.1` fixture upgrade, two-increment causal execution, blocked recovery, and a further third-increment rollover preflight;
- optional, separately authorized fresh-task live continuation replay;
- version `0.1.2` package and documentation synchronization.

Plan B does not own or redefine:

- proposal publication, launch activation, prompt-envelope bytes, first-increment grant, exact-plan schemas, execution-baseline schema, review preparation, `accept-stop`, closure storage/transaction, package digest comparison, or version `0.1.1` fixture construction;
- program revision, supersession, cancellation, installation, commit, publication, deployment, destructive work, provider mutation, or external-action execution.

## Plan A Interfaces Consumed Unchanged

Plan B must import and reuse these implemented Plan A interfaces. A signature change is a plan-reconciliation stop:

```python
# task_prompt.py
def render_exact_prompt(command: Mapping[str, object]) -> str: ...
def parse_exact_prompt(markdown: str, expected_schema: str) -> dict[str, object]: ...

# diff_disposition.py
def build_diff_acceptance_candidate(
    program_root: Path,
    observation: RepositoryObservation,
) -> DiffAcceptanceCandidate: ...
def render_diff_disposition_prompt(program_root: Path) -> str: ...
def persist_accept_stop(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> DiffDispositionReceipt: ...

# state_authority.py / repository_preparation.py
def required_future_lifecycle_writes(
    program_root: Path,
    workspace_root: Path,
    increment_id: str,
) -> tuple[ManagedWriteRequirement, ...]: ...
def resolve_program_closure_paths(program_root: Path) -> dict[str, Path]: ...
def validate_execution_workspace(
    program_root: Path,
    baseline: ExecutionBaseline,
    inspection: RepositoryInspection,
    *,
    increment_state: str,
) -> ExecutionWorkspaceAssessment: ...

# program_activation.py
def prepare_exact_plan(
    program_root: Path,
    exact_plan_bytes: bytes,
    observation: RepositoryObservation,
) -> ExactPlanPreparationReceipt: ...
def materialize_exact_plan(
    program_root: Path,
    submitted_plan_prompt: str | None,
    observation: RepositoryObservation,
) -> ExecutionMaterializationReceipt: ...

# program_review.py / program_closure.py
def persist_review_preparation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewPreparationReceipt: ...
def prepare_program_closure(
    program_root: Path,
    observation: RepositoryObservation,
) -> ClosurePreparationReceipt: ...
def persist_program_closure(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> ClosureReceipt: ...
```

## Shared-File Extension Inventory

Every Plan B modification to a Plan A-owned file has one precise extension:

- `scripts/diff_disposition.py` — consume the unchanged Plan A acceptance candidate and `accept-stop` bytes; add optional `accept-continue` projection, accepted-state continuation builder, and coordinator. Never change the canonical stop seed, prompt section, approval bytes, or status binding.
- `scripts/program_discovery.py` — add exact immediate-continuation, accepted-state continuation, rollover, and blocked-resolution prefix classifications before generic rejection. Preserve all Plan A routes.
- `scripts/state_authority.py` — add typed successor and blocked contexts plus the two lifecycle action names. Preserve Plan A status, grant, managed-path, acceptance, and closure validation.
- `scripts/repository_preparation.py` — extend Plan A execution-baseline construction only to validate and record inherited accepted product paths from a canonical rollover record. Do not change the schema or first-increment behavior.
- `scripts/approval_checkpoint.py` — add `rollover-increment` and `resume-blocked-program` as `explicit-local` risk classes. Do not route their persistence through the standard plan-approval checkpoint.
- `scripts/continuity_closure.py` — add the structured bounded result and semantic successor selection used by Plan B. Preserve accepted legacy brief/handoff bytes and Plan A closure behavior.
- `SKILL.md` — consume Plan A's create/launch/materialize/review/accept-stop/closure routes unchanged; add diff choice, accepted-state continuation, successor rollover, and blocked-resolution routing.
- `agents/openai.yaml` — preserve explicit-only invocation and Plan A's create/activate wording; extend the current description/default prompt to include safe continuation at version `0.1.2` without revision/supersession/cancellation claims.
- `references/program-discovery.md` — consume Plan A's proposal, activation, plan, review, acceptance, closure, and terminal routes; add exact immediate/later rollover and blocked prefix dispositions.
- `references/approval-checkpoints.md` — preserve Plan A's standard plan-approval ordering; add only the two `explicit-local` lifecycle action classifications and state that their prompt-bound sinks remain separate.
- `references/state-authorization.md` — consume Plan A's status-current grant, managed-write, acceptance, and closure contracts; add successor-authority replacement and sink-derived blocked/resolution contexts.
- `references/repository-preparation.md` — consume Plan A's exact-plan and execution-baseline contract; add inherited accepted-product validation for successor baselines.
- `references/execution-discipline.md` — consume Plan A's mode-conditional materialization rules; require the identical rules and future-write derivation for every successor.
- `references/continuity-closure.md` — consume Plan A's closure and prompt-envelope contracts; add bounded navigation, unique-successor selection, immediate/later continuation, and rollover recovery.
- `docs/workflows.md` — preserve Plan A create/start examples; add immediate continue, later continue, and blocked-resolution workflows.
- `docs/reference.md` — preserve Plan A schemas; document only the new successor projection, rollover, accepted-state continuation, blocked context, and resolution record.
- `docs/troubleshooting.md` — preserve Plan A recovery routes; add exact immediate/later continuation, rollover, and blocked prefix recovery.
- `docs/installation.md` — preserve Plan A source/install parity procedure; update only the current package version example to `0.1.2`.
- `docs/maintainers.md` — preserve Plan A deterministic release gates; add the optional live continuation replay and its separate authority boundary.
- `implementing-staged-plans-consolidated-design-plan-final.md` — preserve Plan A lifecycle ownership; append the post-acceptance continuation and blocked-recovery design allocation.
- `implementing-staged-plans-bootstrap-execution-review-runbook.md` — preserve Plan A bootstrap/launch execution; add exact accepted-diff and blocked-resume runbook routes.
- `scripts/validate_package.py` and package manifests — require Plan B scripts and version `0.1.2`; reuse Plan A's package digest and installed-copy interfaces unchanged.
- `tests/program_bootstrap_support.py` — add production-driven successor and blocked scenario helpers; never manufacture an action authorization, grant, rollover, blocked context, or resolution record.
- `tests/test_diff_disposition.py` — freeze Plan A stop bytes and add conditional continue/acceptance-prefix coverage.
- `tests/test_program_discovery.py` — preserve Plan A route assertions and add exact Plan B prefix dispositions.
- `tests/test_state_authority.py` — preserve Plan A state contracts and add successor/blocked typed-context enforcement.
- `tests/test_repository_preparation.py` — preserve Plan A baseline tests and add inherited accepted-product validation.
- `tests/test_approval_checkpoint.py` — preserve Plan A persistence ordering and add only lifecycle action classification assertions.
- `tests/test_continuity_closure.py` — preserve Plan A closure/legacy bytes and add bounded-result and successor-selection coverage.
- `tests/test_front_door_contract.py` — preserve Plan A obligations and add post-acceptance routing claims.

## File Structure

### Create

- `skills/implementing-staged-plans/scripts/program_continuation.py` — immediate and accepted-state continuation commands, prompt construction, and prompt-derived authority records.
- `skills/implementing-staged-plans/scripts/program_rollover.py` — status-last rollover persistence, prefix inspection, and retry adoption.
- `skills/implementing-staged-plans/scripts/blocked_recovery.py` — sink-derived blocked context, resolution candidates/prompts, managed resolution records, and resume persistence.
- `tests/test_program_continuation.py`
- `tests/test_program_rollover.py`
- `tests/test_blocked_recovery.py`
- `tests/test_multi_increment_lifecycle.py`
- `tests/pressure/continuation-replay/scenarios.json`
- `tests/pressure/continuation-replay/prompts/immediate-continuation.md`
- `tests/pressure/continuation-replay/prompts/later-continuation.md`
- after separately authorized evaluation only: raw result and digest-bound verdict files under `tests/pressure/continuation-replay/`.

### Modify

- the exact shared files and extensions listed above;
- `tests/test_diff_disposition.py`, `tests/test_program_discovery.py`, `tests/test_state_authority.py`, `tests/test_repository_preparation.py`, `tests/test_approval_checkpoint.py`, `tests/test_continuity_closure.py`, and `tests/test_front_door_contract.py`;
- `tests/integrated_pressure_support.py` and `tests/test_integrated_pressure.py`;
- `docs/workflows.md`, `docs/reference.md`, `docs/troubleshooting.md`, `docs/installation.md`, and `docs/maintainers.md`;
- `implementing-staged-plans-consolidated-design-plan-final.md` and `implementing-staged-plans-bootstrap-execution-review-runbook.md`;
- `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`;
- `tests/test_package_validation.py` and `tests/test_distribution_documentation.py`.

### Preserve

- Plan A's `task_prompt.py`, `program_bootstrap.py`, `program_launch.py`, `program_review.py`, and `program_closure.py` implementation contracts unless a verified material defect forces plan reconciliation;
- `tests/fixtures/program-bootstrap/v0.1.1/**` byte-for-byte;
- Plan A's implementation plan and the approved split design;
- `implementation-programs/ISP-001/**`, installed caches, and historical evaluator evidence.

---

### Task 1: Return a structured bounded continuation result without redefining prompts

**Deliverable:** Every new-task navigation result contains a concrete next legal action, mandatory stop, and exact copy-ready prompt generated through Plan A's envelope; no other result can carry a prompt.

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/continuity_closure.py`
- Modify: `skills/implementing-staged-plans/references/continuity-closure.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `tests/test_continuity_closure.py`
- Modify: `tests/test_front_door_contract.py`

**Interfaces:**

```python
CONTINUATION_DESTINATIONS = frozenset({"current-task", "new-task", "none"})

@dataclass(frozen=True)
class BoundedContinuationResult:
    current_state: str
    next_legal_action: str
    mandatory_stop: bool
    destination: str
    continuation_command: Mapping[str, object] | None

def build_bounded_continuation_result(...) -> BoundedContinuationResult: ...
def validate_bounded_continuation_result(
    candidate: BoundedContinuationResult,
) -> list[str]: ...
def render_bounded_continuation_result(
    candidate: BoundedContinuationResult,
) -> str: ...
```

- [ ] **Step 1: Write RED tests**

Require `destination="new-task"` to have `mandatory_stop=True` and one validated continuation command; render it only through `task_prompt.render_exact_prompt`. Reject arbitrary prompt strings, absent commands, a prompt on `current-task`/`none`, authorizing navigation prose, and an envelope whose first line is not `$implementing-staged-plans`. Load the accepted legacy `LeanBrief` and handoff fixtures before and after the change and require byte equality.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_front_door_contract -v
```

Expected: failure naming the missing structured result.

- [ ] **Step 3: Implement derived-only rendering**

Validate state/action text, destination, mandatory stop, and command schema. Render ordinary fields deterministically, then call Plan A's prompt renderer once for a new-task result. Store no arbitrary Markdown prompt field. A bounded result never creates an approval, action authorization, grant, status, or continuation receipt.

- [ ] **Step 4: Run GREEN and focused self-review**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_front_door_contract -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/continuity_closure.py skills/implementing-staged-plans/references/continuity-closure.md skills/implementing-staged-plans/SKILL.md tests/test_continuity_closure.py tests/test_front_door_contract.py
```

Confirm accepted bytes are unchanged, the shared envelope is consumed rather than copied, and navigation never supplies authority.

---

### Task 2: Extend canonical diff disposition with accept-continue and later continuation

**Deliverable:** Plan A's exact `accept-stop` remains byte-identical; a unique satisfied successor adds one `Accept and continue` choice, and an accepted-stop state can later render a separate continuation prompt with a non-colliding identifier domain.

**Files:**

- Create: `skills/implementing-staged-plans/scripts/program_continuation.py`
- Create: `tests/test_program_continuation.py`
- Modify: `skills/implementing-staged-plans/scripts/diff_disposition.py`
- Modify: `skills/implementing-staged-plans/scripts/continuity_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `tests/test_diff_disposition.py`
- Modify: `tests/test_program_discovery.py`
- Modify: `tests/program_bootstrap_support.py`

**Interfaces and schemas:**

```python
SUCCESSOR_PROJECTION_SCHEMA = "implementation-successor-authority-projection/v1"
ACCEPTED_STATE_CONTINUATION_SCHEMA = "implementation-accepted-state-continuation-binding/v1"

@dataclass(frozen=True)
class ContinuationExtension:
    successor_increment_id: str
    successor_brief_bytes: bytes
    accepted_product_delta: tuple[ProductDeltaPath, ...]
    checkpoint_id: str
    rollover_authorization_id: str
    successor_grant_id: str
    successor_projection: Mapping[str, object]

def build_continuation_extension(
    program_root: Path,
    acceptance: DiffAcceptanceCandidate,
    observation: RepositoryObservation,
) -> ContinuationExtension | None: ...
def render_accepted_state_continuation_prompt(program_root: Path) -> str: ...
def validate_submitted_continuation_prompt(
    program_root: Path,
    submitted_prompt: str,
) -> ContinuationCommand: ...
```

`implementation-successor-authority-projection/v1` contains exactly: program ID/revision; current and successor increment IDs; prior awaiting-diff status digest/sequence; disposition checkpoint and approval-event IDs; successor brief and accepted-product-delta digests; successor approval mode; selected workspace path/branch/base/head and selection digest; inherited-workspace digest; allowed conditional-action ceiling; rollover action-authorization ID; and successor grant ID. It excludes accepted-status digest, submitted-prompt digest, action/grant/rollover record digests, and successor-status digest.

`implementation-accepted-state-continuation-binding/v1` contains exactly: its schema domain; accepted-stop status digest/sequence; program ID/revision; current and unique satisfied successor IDs; successor brief and accepted-product-delta digests; successor approval mode; selected and inherited workspace bindings; allowed conditional-action ceiling; and, after topological derivation, its distinct checkpoint, rollover action, and successor grant IDs. It excludes final record bytes/digests, successor-status digest, and prompt digest.

- [ ] **Step 1: Freeze Plan A stop bytes and write RED choice tests**

Load the frozen `0.1.1` awaiting-diff fixture, render `accept-stop`, and assert exact expected bytes/digest. Add cases for final increment, no successor, two successors, and unsatisfied dependencies: stop remains rendered and continuation is omitted with a non-blocking reason. With exactly one satisfied successor, add the exact second choice and bind current review, verification, plan, baseline, live accepted product delta, successor, brief, workspace, and status-current authority.

- [ ] **Step 2: Write topological identifier RED tests**

Derive the base seed without any derived ID or later byte. Derive disposition checkpoint, approval event, rollover action ID, then successor grant ID. Build the projection from pre-record values only. Assert it excludes accepted-status digest, submitted-prompt digest, action/grant/rollover record digests, and successor-status digest. Serialize accepted status with Plan A's diff binding extended only for continue. Prove no identifier changes when later canonical record serialization order is varied.

- [ ] **Step 3: Write immediate and later acceptance-prefix tests**

For immediate continue, persist/adopt diff approval then accepted-current status with `decision=accept-continue`; fresh discovery returns `increment-acceptance-retry-ready` after approval and `accepted-continuation-retry-ready` after status. For stop, keep Plan A's complete/idempotent behavior. For later continuation, derive a schema-distinct seed rooted in accepted-stop status digest/sequence and prove its checkpoint/action/grant IDs differ from the earlier stop and immediate-continue domains. Replaying the stop prompt never renders or persists continuation.

- [ ] **Step 4: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_diff_disposition tests.test_program_continuation tests.test_program_discovery -v
```

- [ ] **Step 5: Implement pure builders and the acceptance prefix**

Reuse `build_diff_acceptance_candidate` unchanged for both choices. Add successor semantic/workspace validation before the continuation extension. Preserve Plan A stop rendering byte-for-byte; append the continue choice only when the extension is non-null. Direct immediate submission writes/adopts approval and accepted status first. Do not write an action authorization, grant, navigation, rollover, or successor status in this task; Task 3 consumes the exact accepted continuation projection and completes that suffix from the same prompt.

For a later request, validate accepted-stop plus exactly one satisfied successor read-only, derive the distinct accepted-state command, render through Plan A's envelope, and stop. Do not reuse the diff approval event or checkpoint.

- [ ] **Step 6: Run GREEN and focused self-review**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_diff_disposition tests.test_program_continuation tests.test_program_discovery tests.test_continuity_closure -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/diff_disposition.py skills/implementing-staged-plans/scripts/program_continuation.py skills/implementing-staged-plans/scripts/continuity_closure.py skills/implementing-staged-plans/scripts/program_discovery.py tests/test_diff_disposition.py tests/test_program_continuation.py tests/test_program_discovery.py tests/program_bootstrap_support.py
```

Confirm stop bytes and behavior are unchanged, acceptance is independent of successor availability, immediate/later identifiers cannot collide, and accepted status contains only the pre-record projection.

---

### Task 3: Persist successor authority, navigation, rollover, and status last

**Deliverable:** The same immediate or later continuation prompt persists action authority, a distinct successor grant, navigation, a rollover record, and successor status last; every partial prefix is freshly discoverable and retryable.

**Files:**

- Create: `skills/implementing-staged-plans/scripts/program_rollover.py`
- Create: `tests/test_program_rollover.py`
- Modify: `skills/implementing-staged-plans/scripts/program_continuation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `skills/implementing-staged-plans/scripts/approval_checkpoint.py`
- Modify: `skills/implementing-staged-plans/references/continuity-closure.md`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `tests/test_state_authority.py`
- Modify: `tests/test_repository_preparation.py`
- Modify: `tests/test_approval_checkpoint.py`
- Modify: `tests/program_bootstrap_support.py`

**Interfaces:**

```python
ROLLOVER_RECORD_SCHEMA = "implementation-increment-rollover/v1"

@dataclass(frozen=True)
class IncrementRolloverReceipt:
    prior_status_sha256: str
    current_status_sha256: str
    current_increment_id: str
    successor_increment_id: str
    rollover_authorization_id: str
    successor_grant_id: str
    created_steps: tuple[str, ...]
    adopted_steps: tuple[str, ...]
    status_replaced: bool
    requires_retry: bool

def required_increment_rollover_writes(
    program_root: Path,
    workspace_root: Path,
    successor_increment_id: str,
) -> tuple[ManagedWriteRequirement, ...]: ...
def inspect_increment_rollover(
    program_root: Path,
    observation: RepositoryObservation,
) -> IncrementRolloverInspection: ...
def persist_increment_rollover(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> IncrementRolloverReceipt: ...

# diff_disposition.py coordinator; Plan A persist_accept_stop remains unchanged
def persist_diff_disposition(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> DiffDispositionReceipt | IncrementRolloverReceipt: ...
```

- [ ] **Step 1: Write authority and file-map RED tests**

Register `rollover-increment` as `explicit-local`. Require action authorizations, increment grants, rollovers, and status under `Modify`; current handoff and successor brief under `Create`. Compose with, rather than replace, Plan A's `required_future_lifecycle_writes`. Remove/misclassify each path independently and prove the sink writes nothing. Reject caller-supplied record IDs, status/manifest payloads, synthetic observations, genesis-grant reuse, successor not allocated, unsatisfied dependencies, stale prompt/status, changed accepted product delta, and legacy manifests.

- [ ] **Step 2: Write the complete rollover prefix matrix**

For immediate continuation, start after exact accepted-continue status. For later continuation, start at accepted-stop with the distinct prompt. Inject after action authorization, successor grant, handoff, successor brief, rollover record, and successor status. Restart discovery after every prefix; require exact `increment-continuation-retry-ready`, `increment-rollover-retry-ready`, `accepted-state-continuation-retry-ready`, or `accepted-state-rollover-retry-ready`; resubmit the same prompt; adopt once; and reach ordinary successor resume. Test lost response after successor status. Mutate the newest record/file and require the matching recovery-required stop with all bytes preserved and no replacement ID.

- [ ] **Step 3: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_continuation tests.test_program_rollover tests.test_program_discovery tests.test_state_authority tests.test_repository_preparation tests.test_approval_checkpoint -v
```

- [ ] **Step 4: Implement authority-first status-last persistence**

Validate the complete submitted prompt and accepted-state projection, then compute every canonical record before writing. Persist/adopt action authorization, successor grant, handoff, successor brief, and rollover record in order. The rollover record stores actual prompt/record digests and the validated accepted-product-delta inventory. Replace status last, preserving immutable activation history and replacing `current_increment_authority_binding` with the exact successor grant. Add `rollover_binding` and `inherited_workspace_binding`; clear prior plan/baseline/review bindings. Never modify the manifest.

Expose `persist_diff_disposition` as the one front-door coordinator. For Plan A's stop prompt it delegates to unchanged `persist_accept_stop`. For immediate continue it persists/adopts the acceptance prefix, then passes the same submitted prompt and fresh observation into `persist_increment_rollover`; it never returns an intermediate user checkpoint. Later accepted-state continuation calls `persist_increment_rollover` directly from its distinct prompt because acceptance is already complete.

- [ ] **Step 5: Extend execution baseline only for inherited product history**

Validate the unique rollover chain from genesis to status-current successor. Load the predecessor's accepted product inventory and require current bytes to match. Record those paths under the existing `inherited_program_paths` field. A successor plan may classify an inherited regular file under `Modify` or `Preserve`, never `Create`; unrelated selected user work retains its original ownership. Call Plan A's exact-plan preparation/materialization without a successor-specific bypass.

- [ ] **Step 6: Expose bounded CLIs and run GREEN**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_continuation.py render PROGRAM_ROOT
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_rollover.py apply PROGRAM_ROOT --prompt-file PROMPT --repository REPOSITORY --base-commit BASE
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_continuation tests.test_program_rollover tests.test_program_discovery tests.test_state_authority tests.test_repository_preparation tests.test_approval_checkpoint tests.test_program_activation -v
```

- [ ] **Step 7: Focused self-review**

```bash
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_continuation.py skills/implementing-staged-plans/scripts/program_rollover.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/repository_preparation.py skills/implementing-staged-plans/scripts/approval_checkpoint.py skills/implementing-staged-plans/references/continuity-closure.md skills/implementing-staged-plans/references/program-discovery.md skills/implementing-staged-plans/references/state-authorization.md tests/test_program_continuation.py tests/test_program_rollover.py tests/test_program_discovery.py tests/test_state_authority.py tests/test_repository_preparation.py tests/test_approval_checkpoint.py tests/program_bootstrap_support.py
```

Confirm immediate and later paths share only the suffix contract, each uses its own prompt-bound IDs, the manifest is byte-identical, successor authority is status-current, and partial writes are never deleted or overwritten.

---

### Task 4: Enter and resolve blocked state through a manifest-owned ledger

**Deliverable:** A legal nonterminal successor can enter blocked through a sink-derived context, rediscover in a fresh process, and resume exactly its prior state after one exact prompt persists action authority and managed resolution evidence before status.

**Files:**

- Create: `skills/implementing-staged-plans/scripts/blocked_recovery.py`
- Create: `tests/test_blocked_recovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/scripts/approval_checkpoint.py`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Modify: `tests/test_state_authority.py`
- Modify: `tests/test_program_discovery.py`
- Modify: `tests/test_approval_checkpoint.py`
- Modify: `tests/program_bootstrap_support.py`

**Interfaces and schemas:**

```python
BLOCKED_CONTEXT_SCHEMA = "implementation-blocked-context/v1"
BLOCK_RESOLUTION_RECORD_SCHEMA = "implementation-block-resolution/v1"
BLOCK_RESOLUTION_COMMAND_SCHEMA = "implementation-block-resolution-command/v1"

@dataclass(frozen=True)
class BlockedTransitionRequest:
    reason_code: str
    recovery_criteria: tuple[str, ...]
    evidence_bindings: tuple[EvidenceBinding, ...] = ()

def block_current_program(
    program_root: Path,
    request: BlockedTransitionRequest,
    observation: RepositoryObservation,
) -> StateTransitionReceipt: ...
def build_block_resolution_candidate(...) -> BlockResolutionCandidate: ...
def render_block_resolution_prompt(...) -> str: ...
def persist_blocked_resolution(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> StateTransitionReceipt: ...
```

The persisted `implementation-blocked-context/v1` contains exactly: block ID; reason code; prior program and increment states; prior status digest/sequence; current increment ID; exact-plan, execution-baseline, current-grant, workspace, and inherited-workspace bindings; ordered unique recovery criteria; and safe evidence bindings to already-existing controlled files. The caller supplies only reason, criteria, and candidate evidence; the sink derives every state/authority field.

Each `implementation-block-resolution/v1` record contains exactly: resolution ID; block/context and blocked-status digests; complete satisfied criterion results; safe evidence inventory; submitted-prompt digest; action-authorization ID/digest; and prior and restored states. It contains no caller-selected resume state or external evidence-file authority.

- [ ] **Step 1: Write the causal writer-reader-resume RED test**

Use the production writer to block an active program with a nonterminal successor in `implementing` or `reviewing`. It derives prior states, prior digest/sequence, current plan/baseline/grant, stable block ID, bounded criteria, and safe existing-evidence digests. Exit the process. Fresh discovery returns `blocked-recovery-ready` with exact recorded resume states. Build a fully satisfied candidate, render the exact prompt, submit in another process, and assert one `resume-blocked-program` authorization, one ledger record, and restored prior states.

- [ ] **Step 2: Write fail-closed and prefix tests**

Register `resume-blocked-program` as `explicit-local`. Reject caller-supplied resume targets, fabricated context, preapproval/final/accepted blocking, changed plan/baseline/grant, evidence created only for recovery, outside/unallocated/escaped/symlinked/changed evidence, duplicate/unsatisfied criteria, tampered prompt, stale status, and generic direct blocked edges. Inject after action authorization, resolution record, and resumed status; fresh discovery retries exact prefixes, lost response is idempotent, and divergent bytes remain preserved. Require action authorizations, block-resolutions, and status under `Modify` in the successor plan before resolution writes.

- [ ] **Step 3: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_blocked_recovery tests.test_state_authority tests.test_program_discovery tests.test_approval_checkpoint -v
```

- [ ] **Step 4: Implement one canonical context/evidence validator**

Share the validator across block writer, discovery, prompt builder, and resume sink. Block entry validates all existing authority/workspace invariants and atomically replaces status with both states blocked. Resolution precomputes canonical action, ledger record, and resumed status, then appends/adopts action and record before compare-and-swap status. Target states come only from blocked context. The candidate transport file used by `render` is not persisted, cited as evidence, or treated as authority.

- [ ] **Step 5: Expose bounded CLIs and run GREEN**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/blocked_recovery.py render PROGRAM_ROOT --candidate-file CANDIDATE
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/blocked_recovery.py apply PROGRAM_ROOT --prompt-file PROMPT --repository REPOSITORY --base-commit BASE
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_blocked_recovery tests.test_state_authority tests.test_program_discovery tests.test_approval_checkpoint -v
```

- [ ] **Step 6: Focused self-review**

```bash
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/blocked_recovery.py skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/scripts/approval_checkpoint.py skills/implementing-staged-plans/references/state-authorization.md skills/implementing-staged-plans/references/program-discovery.md tests/test_blocked_recovery.py tests/test_state_authority.py tests/test_program_discovery.py tests/test_approval_checkpoint.py tests/program_bootstrap_support.py
```

Confirm every blocked byte originates from a production sink, resolution uses only managed ledger/evidence, resume cannot expand authority, and malformed legacy state is preserved rather than guessed or migrated.

---

### Task 5: Prove 0.1.1 upgrade, two increments, blocked recovery, and a further rollover

**Deliverable:** One deterministic subprocess regression starts from frozen `0.1.1` bytes, continues under `0.1.2` without rewriting manifest/first plan, executes a successor through the real diff gate, exercises blocked recovery, and completes a third-increment rollover preflight.

**Files:**

- Create: `tests/test_multi_increment_lifecycle.py`
- Modify: `tests/program_bootstrap_support.py`
- Read-only fixture: `tests/fixtures/program-bootstrap/v0.1.1/**`

**Interfaces consumed without redefinition:**

```python
persist_diff_disposition(...)
persist_increment_rollover(...)
prepare_exact_plan(...)
materialize_exact_plan(...)
block_current_program(...)
persist_blocked_resolution(...)
persist_review_preparation(...)
prepare_program_closure(...)
persist_program_closure(...)
```

The test helper exposes process launch, byte snapshot, and failure-injection controls only. It exposes no method that appends an authority/grant/rollover/resolution record or writes status directly.

- [ ] **Step 1: Verify the frozen predecessor before RED**

Recompute the fixture's sorted path/digest inventory, reject symlinks/special files, and require package/program version `0.1.1`. Copy it into an isolated temporary repository without changing fixture bytes. Snapshot its manifest and first exact plan for later byte-equality assertions.

- [ ] **Step 2: Write immediate and later multi-process RED branches**

Immediate branch submits `accept-continue`, restarts, completes rollover, and materializes the successor under each supported successor mode through Plan A's transaction. Later branch submits `accept-stop`, proves replay remains stopped, starts a new task with the distinct accepted-state prompt, and completes rollover. Require no second user checkpoint after either continuation prompt.

For `approval:standard`, inject after successor plan, awaiting-plan status, plan approval, baseline, action authorization, and authorized status. For pre-approve/full-increment, inject after plan, baseline, action, and authorized status. Restart after every prefix. Re-run `required_future_lifecycle_writes` against the successor plan and remove each future path in turn to prove sink-boundary rejection.

- [ ] **Step 3: Write blocked and further-rollover causal branches**

Block the nonterminal second increment, rediscover in a new process, resolve by exact prompt, restore the prior state, implement the real second product delta, prepare review, and reach its second diff gate. In a separate branch, accept the second diff and complete one further rollover to a traceability-allocated third increment. Assert neither the manifest nor first exact plan changes and the second plan already allocated third-navigation and block-resolution paths.

Add a final-successor compatibility branch with no allocated successor. Accept-stop that successor, then call Plan A's unchanged `prepare_program_closure` and `persist_program_closure` interfaces. Require manifest-derived closure paths, awaiting-closure status, exact closure approval, and closed status without any Plan B closure-specific branch or manifest change.

- [ ] **Step 4: Encode the complete release-blocking failure matrix**

Cover diff approval → accepted status; accepted status → action authorization; action → successor grant; grant → handoff; handoff → brief; brief → rollover record; rollover → successor status; every successor materialization prefix for standard and automatic modes; block-resolution action → ledger; ledger → resumed status. Run the action-through-successor-status suffix once for immediate and once for later continuation. For every prefix, restart discovery, adopt exact bytes, mutate the newest byte independently, require the exact recovery-required route, and prove no cleanup, duplicate authority, replacement identifier, or later status.

- [ ] **Step 5: Run RED, implement only production-driven fixture support, then GREEN**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_multi_increment_lifecycle -v
```

Expected RED: first missing production boundary, never a fixture-manufactured authority pass.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_multi_increment_lifecycle tests.test_program_continuation tests.test_program_rollover tests.test_blocked_recovery -v
```

- [ ] **Step 6: Focused self-review**

```bash
rtk git diff --check
rtk git diff -- tests/test_multi_increment_lifecycle.py tests/program_bootstrap_support.py
```

Confirm the test crosses real writer/fresh-reader boundaries, accepted product bytes become program history, status-current successor grants replace genesis authority, Plan A interfaces are reused unchanged, and second/further increment behavior is causal rather than source-text asserted.

---

### Task 6: Add an optional separately authorized live fresh-task continuation replay

**Deliverable:** A deterministic two-route replay catalog and safe evaluator gate can test runtime front-door behavior without making live evaluation a source-completion dependency.

**Files:**

- Create: `tests/pressure/continuation-replay/scenarios.json`
- Create: `tests/pressure/continuation-replay/prompts/immediate-continuation.md`
- Create: `tests/pressure/continuation-replay/prompts/later-continuation.md`
- Create only after explicit evaluator and evidence-write authority: `tests/pressure/continuation-replay/results/*.txt`
- Create only after human review: `tests/pressure/continuation-replay/verdicts.json`
- Modify: `tests/integrated_pressure_support.py`
- Modify: `tests/test_integrated_pressure.py`
- Modify: `docs/maintainers.md`

**Interfaces:**

```python
@dataclass(frozen=True)
class ContinuationReplayScenario:
    scenario_id: str
    prompt_path: str
    result_path: str
    expected_boundary: str

def load_continuation_replay(path: Path) -> tuple[ContinuationReplayScenario, ...]: ...
def validate_continuation_replay_evidence(root: Path) -> list[str]: ...
```

- [ ] **Step 1: Write deterministic artifact RED tests**

Require exactly the immediate and later scenario IDs, repository-contained normalized paths, prompts beginning with `$implementing-staged-plans`, atomic no-overwrite result creation, evaluator/client version, isolated ephemeral sessions, zero exit, prompt/result digests, and verdicts bound to raw results. Reject absent authority as a reason to claim runtime success; deterministic tests must pass with no live results present and report the replay as not run.

- [ ] **Step 2: Run RED and implement the offline contract**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_integrated_pressure -v
```

The evaluator subcommand runs each prompt in a fresh isolated session, stops on first failure, and never overwrites a result. It does not modify program state, install the skill, or choose a model/provider without the approved command.

- [ ] **Step 3: Document and stop at the external gate**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 tests/integrated_pressure_support.py evaluate-continuation-replay --scenario-catalog tests/pressure/continuation-replay/scenarios.json --output-directory tests/pressure/continuation-replay/results --evaluator codex
```

Before running, report the exact command, evaluator/client version preflight, source-egress/authentication/model-capacity implications, number of fresh tasks, write targets, and existing-target check. Run once only after explicit evaluator and evidence-write authority. If not authorized, record `live continuation replay: not run`; deterministic source completion remains possible.

- [ ] **Step 4: Run offline GREEN and focused self-review**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_integrated_pressure -v
rtk git diff --check
rtk git diff -- tests/pressure/continuation-replay tests/integrated_pressure_support.py tests/test_integrated_pressure.py docs/maintainers.md
```

Confirm external evaluation is optional and explicitly authorized, raw outputs are evidence rather than authority, and no runtime claim is made when the replay is absent.

---

### Task 7: Synchronize version 0.1.2, verify once, and obtain one independent review

**Deliverable:** Skill/docs/package surfaces describe the exact post-acceptance lifecycle at version `0.1.2`; final deterministic validation passes once on the unchanged candidate; exactly one independent material review has no unresolved finding.

**Files:**

- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/agents/openai.yaml`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Modify: `skills/implementing-staged-plans/references/approval-checkpoints.md`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `skills/implementing-staged-plans/references/repository-preparation.md`
- Modify: `skills/implementing-staged-plans/references/execution-discipline.md`
- Modify: `skills/implementing-staged-plans/references/continuity-closure.md`
- Modify: `docs/workflows.md`, `docs/reference.md`, `docs/troubleshooting.md`, `docs/installation.md`, and `docs/maintainers.md`
- Modify: `implementing-staged-plans-consolidated-design-plan-final.md`
- Modify: `implementing-staged-plans-bootstrap-execution-review-runbook.md`
- Modify: `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Modify: `tests/test_front_door_contract.py`, `tests/test_distribution_documentation.py`, and `tests/test_package_validation.py`

**Interfaces:**

```python
PACKAGE_VERSION = "0.1.2"

# Plan A interfaces, behavior unchanged
def package_file_digests(root: Path) -> dict[str, str]: ...
def validate_installed_copy(source_root: Path, installed_root: Path) -> list[str]: ...
```

- [ ] **Step 1: Add front-door and distribution RED tests**

Require exact `accept-stop` and conditional `accept-continue`; distinct later continuation after stop; status-current successor grant; immutable manifest; future-write allocation on every successor; prompt-bound blocked resolution; exact retry/recovery routes; legacy rollover quarantine; Plan A closure reuse; and version/description equality at `0.1.2`. Reject routine per-task approvals, handoff authority, automatic legacy successor claims, or descriptions that imply revision/supersession/cancellation support.

- [ ] **Step 2: Synchronize canonical prose and metadata**

Add front-door sections `Dispose the Current Diff`, `Continue an Accepted Program`, `Authorize a Successor Increment`, and `Resolve a Blocked Program`. State exact meaningful user decisions and internal receipt order. Preserve Plan A create, launch, exact-plan, review, accept-stop, and closure sections. Keep `allow_implicit_invocation: false`. Update current package examples only; preserve historical version evidence.

- [ ] **Step 3: Use alternative verification for synchronized prose**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_front_door_contract tests.test_distribution_documentation tests.test_package_validation -v
rtk rg -n "accept-continue|accepted-state-continuation|current_increment_authority_binding|blocked-recovery|legacy-rollover-upgrade-required" skills/implementing-staged-plans docs implementing-staged-plans-consolidated-design-plan-final.md implementing-staged-plans-bootstrap-execution-review-runbook.md
rtk git diff --check
```

Expected: tests pass, normative contracts have one owner with precise references, and prose checks make no runtime claim.

- [ ] **Step 4: Run focused behavioral GREEN**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_diff_disposition tests.test_program_continuation tests.test_program_rollover tests.test_blocked_recovery tests.test_multi_increment_lifecycle tests.test_program_discovery tests.test_state_authority tests.test_repository_preparation tests.test_approval_checkpoint tests.test_continuity_closure tests.test_front_door_contract tests.test_package_validation tests.test_distribution_documentation -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_CREATOR_VALIDATOR" skills/implementing-staged-plans
```

The optional external Skill Creator check requires the caller to supply
`SKILL_CREATOR_VALIDATOR` as the exact regular `quick_validate.py` path and
confirm that path before running it. If unavailable, skip only that optional
check and retain the repository-owned package validator below.

- [ ] **Step 5: Run package validation and the full deterministic suite exactly once**

Freshly verify status and exact Plan A/Plan B scope, then run on the final unchanged candidate:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk git diff --check
rtk git status --short
rtk git diff --stat
```

Expected: all required commands exit zero; the frozen `0.1.1` fixture and unrelated work remain byte-identical. Do not rerun successful unchanged inputs. Do not run installed-copy comparison without a separately supplied exact installed root.

- [ ] **Step 6: Obtain exactly one bounded independent material review**

Give a reviewer who did not implement the candidate: the spec, final Plan A and Plan B, exact base/head and dirty inventory, complete Plan B diff, package/full-suite results, frozen predecessor inventory, multi-increment evidence, and optional-live-replay status. Scope review to ownership disjointness, Plan A interface compatibility, authority/order/recovery, test causality, legacy compatibility, and unnecessary complexity.

- [ ] **Step 7: Reconcile findings and stop**

If no evidence-supported material defect exists, do not change or re-review the candidate. If one exists within scope, record it, make the smallest repair, rerun affected checks and final checks invalidated by changed inputs, then request one focused independent follow-up for that finding only. Stop for a program amendment or new user-owned decision.

- [ ] **Step 8: Final focused self-review and report**

```bash
rtk git diff --check
rtk git status --short
rtk git diff --stat
```

Report exact changed files and commands; both plan-version owners; Plan A interface compatibility; review findings/dispositions; live replay and installed-parity status; logical commit boundaries without staging; residual limits; and that no commit, installation, push, pull request, publication, deployment, provider, destructive, or external action occurred.

## Completion Criteria

- Plan A `accept-stop`, prompt-envelope, exact-plan, execution-baseline, review, closure, package-digest, and fixture bytes/contracts remain owned by Plan A and are not redefined.
- `Accept and stop` is always available; `Accept and continue` appears only for one satisfied successor and requires no second routine checkpoint.
- Accepted status durably distinguishes stop from continue with an acyclic binding; replaying stop never continues.
- Later continuation after stop uses a distinct accepted-status-rooted prompt and identifier domain.
- Rollover persists action authorization, distinct successor grant, navigation, rollover record, and successor status in order; status-current authority replaces genesis authority and manifest bytes never change.
- Every immediate and later rollover prefix is freshly discoverable, byte-identically adoptable, divergence-preserving, and idempotent after status.
- Every successor plan repeats Plan A's future lifecycle-write allocation and uses Plan A's status-last exact-plan materialization under standard, pre-approve, and full-increment modes.
- Inherited accepted product bytes become program history, never unexplained user dirt.
- Blocked entry is legal only from a nonterminal state and derives resume context at the sink. Resolution uses a direct exact prompt, manifest-owned ledger, already-existing controlled evidence, and status last.
- The frozen `0.1.1` program continues under `0.1.2` without rewriting its manifest or first exact plan.
- One causal branch reaches the second real diff gate through blocked recovery; another accepts the second diff and completes a further rollover to a third increment.
- The complete failure-injection matrix covers every acceptance, immediate/later continuation, rollover, successor materialization, and blocked-resolution prefix with fresh-process adoption and divergence preservation.
- Optional live replay is separately authorized and its absence is reported without blocking deterministic source completion.
- Version `0.1.2` has exactly one owner. Plan B contains no Plan A implementation obligation.
- Package validation and the full deterministic suite pass once on the final unchanged candidate, followed by exactly one bounded independent material review with no unresolved material finding.
- Diff acceptance, closure, commits, installation, publication, deployment, provider access, destructive work, and consequential actions remain separately explicit.
