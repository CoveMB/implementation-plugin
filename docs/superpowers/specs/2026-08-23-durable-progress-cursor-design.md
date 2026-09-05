# Durable Progress Cursor Design

**Status:** Deferred on 2026-08-24. Do not prepare or execute an implementation
plan without a new explicit decision to require exact task-level crash recovery.

**Original source:**
`docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md`
at SHA-256 `b72b0d3c8a87b52302a163d98558ecf80ef557dfcf439b669a7ee6dc03e1905b`
(1,311 lines).

**Dependency:** The program-setup and activation design must be implemented
first. Expanded local operations are not a functional prerequisite, but this
design is implemented after them so progress work does not complicate the
higher-risk authority and recovery changes.

## Goal

Persist the current part and task for new programs and render one concise,
truthful next-work line after a delivered increment without guessing from
prose, file changes, or caller-selected state.

## Scope reduction from the original design

The original design introduced mutable progress projections, projection
identity, automatic task split/combine/renumber operations, and historical
remapping across completed and incomplete work. Those features are deferred.

This first version uses the stable ordered parts and tasks already present in a
new program's validated semantic traceability. Changing their identity, order,
allocation, or acceptance meaning is a program revision. No automatic
projection rewrite or completion remapping occurs.

This removes an entire mutable projection event chain while retaining the user
benefit that justified the feature: exact current-task recovery and concise
next-work output.

## Stable progress structure

New-program semantic traceability must provide, for each increment:

- the stable `increment_id` values in the exact canonical order already approved
  by the Plan 1 setup decision;
- stable `part_id` and `task_id` values;
- one unambiguous total order of parts and tasks;
- task-to-part and task-to-increment ownership;
- requirement and acceptance allocation; and
- the checks that make task completion observable.

Cursor-enabled programs use `implementation-traceability/v3`. It retains the
stable semantic requirement fields from v2 and adds one canonical ordered
`progress_structure` whose part/task ownership, order, allocation, acceptance,
checks, and bound canonical increment order produce a distinct
`progress_structure_sha256`. The increment order is not independently authored
by progress code: traceability v3 must reproduce and validate the exact ordered
increment identifiers approved by Plan 1.

The retained v2 semantic fields and the v3 structure are exact reciprocal
views. Every requirement's `assigned_parts`, `assigned_tasks`,
`assigned_increments`, and `acceptance_criteria` must agree with the stable
identifiers and allocations in `progress_structure`, and every structure
allocation must resolve back to the retained requirement record. Missing,
extra, duplicate, or contradictory allocations invalidate traceability v3.
Continuation and rollover therefore cannot derive a different increment from
the retained fields than progress derives from the canonical structure.

Existing `implementation-traceability/v2` files remain unchanged and cannot
acquire cursor semantics through optional fields.

The setup recap shows the ordered structure as decision-relevant program
semantics. The setup decision therefore binds it. Display-only naming changes
are allowed before that decision. After approval, even a display-only change
changes the exact traceability bytes and requires an explicit program revision.
Every structural or post-approval display change stops at
`program-revision-workflow-required` rather than rebinding an active cursor
family in place.

Legacy traceability remains byte-for-byte governed by its current schema. The
implementation does not synthesize a stable order or task-to-part relation from
legacy `assigned_parts` and `assigned_tasks` lists.

## Progress cursor ledger

Cursor-enabled programs use `implementation-program-manifest/v5`, which owns
one append-only `progress-cursor/v1` ledger and selects traceability v3 and
cursor-aware status v5. `implementation-program-status/v5` retains the
applicable lifecycle bindings from its predecessor and adds the exact
traceability identity and progress-structure digest. It also contains exactly
one of:

- an explicit absent-cursor binding while the state is
  `awaiting-program-approval / not-started` or
  `active / awaiting-first-increment`, with an empty cursor ledger; or
- the current cursor identity, cursor digest, and cursor sequence after the
  first-increment start transaction.

No other state permits an absent cursor. No separate projection ledger exists.

Proposal publication pre-allocates the empty cursor-ledger path in its
owner-bound inventory. Because genesis precedes an exact-file plan, only the
typed first-increment start transaction may append the genesis event. After
genesis, the cursor-ledger logical role is a required `Modify` entry in every
cursor-capable exact-file plan and derived execution baseline, including the
predecessor baseline that governs successor rollover. No cursor append bypasses
managed-write allocation.

Each cursor event binds:

- program and revision;
- current increment;
- semantic traceability identity;
- prior cursor identity and sequence, or explicit genesis;
- prior status digest and sequence;
- expected citing status sequence;
- one complete canonical `progress-transition-intent/v1` payload embedded in
  the event, plus its deterministic identity and digest; the payload carries
  every transition-specific status-delta input needed to reconstruct the
  expected status, including unchanged bindings required by a same-state cursor
  refresh;
- stable part and task identifiers and their validated ordinals; and
- one state: `ready`, `in-progress`, `blocked`, or `completed`.

A `completed` event also binds the exact durable evidence for every check and
acceptance obligation allocated to that task. Missing, stale, incomplete, or
caller-authored completion evidence cannot produce a completed cursor. Event
and status identifiers are derived topologically from the complete intent
payload before the cursor digest and target status digest are computed.

Exactly one latest cursor is current. A gap, fork, duplicate sequence, stale
traceability identity, impossible transition, unknown task, wrong ordinal, or
divergent event stops without rewriting history.

The transition intent is built by the same typed lifecycle transaction that
owns the cursor update. It is retry evidence, not independent lifecycle or
product-change authority. Fresh discovery may complete a missing status write
only when it can rebuild the exact cursor and status bytes from the embedded
intent payload, the controlling prior status, and the durable records cited by
that payload. Caller memory, mutable prose, and newly supplied transition inputs
are not recovery evidence.

## Cursor lifecycle

The setup design remains independent and creates no cursor. A cursor-enabled v5
program may therefore wait only as `awaiting-program-approval / not-started` or,
after activation, as `active / awaiting-first-increment`. Both states carry the
explicit absent-cursor binding and require an empty cursor ledger. Activation
preserves Plan 1's waiting state and does not allocate progress.

The separate first-increment start transaction appends or adopts the first
task's `ready` cursor, replaces the absent-cursor binding, and then writes
`active / preparing` status last.

The legal cursor transition table is exact:

- explicit genesis -> first task `ready` during first-increment start;
- `ready` -> the same task `in-progress` before task work;
- `in-progress` -> the same task `blocked` through the typed blocking
  transaction;
- `blocked` -> the same task `in-progress` only through the durable typed
  resolution or retry transaction;
- a non-final task `in-progress` -> the same task `completed` after its bound
  checks and acceptance obligations validate;
- a non-final task `completed` -> the next canonical task `ready`.

Every arrow is one independently recoverable cursor append followed by one
status-last write. Completing and advancing a non-final task therefore uses two
ordered subtransactions: the current task first becomes status-current
`completed`; a second transaction advances the next task to status-current
`ready`. Fresh discovery recognizes the intermediate completed state and
routes only the deterministic advancement transaction. It never fabricates the
second event or treats completion as advancement authority.

The final task follows a distinct terminal transition. It remains `in-progress`
through review, any
`reviewing -> remediating -> reviewing` loop, verification, and the diff
checkpoint. A change request returns to work without reopening a completed
cursor. The diff-acceptance transaction appends or adopts `completed` only
after the acceptance decision is durable and immediately before the current
increment's `accepted` status-last write. That accepted status binds the
completed cursor. Any required recovery cleanup then finishes under the
expanded-operations barrier before a later successor rollover appends `ready`
and writes successor status last.

Every typed successor rollover appends or adopts the successor increment's
first-task `ready` cursor, bound to the rollover transaction and successor
grant, immediately before successor status-last. The prior increment's
completed cursor cannot satisfy the successor status. Failure after the cursor
write is recovered from the exact rollover intent and prefix.

A lifecycle transition writes status last. A cursor-only update within the same
lifecycle state writes a higher-sequence status refresh last. The resulting
status binds the cursor identity and digest. Fresh discovery reports a part or
task only when that status-current binding validates.

A lost response after a cursor append but before status is an exact recoverable
prefix: discovery validates the embedded event and transition intent against
the controlling prior status and cited durable evidence, reconstructs every
target status binding, and completes the expected status write. A cursor whose
exact intent, completion evidence, or expected status cannot be reconstructed
is preserved as a recovery stop.

Cursor state is informational lifecycle evidence. It grants no setup,
implementation, successor, diff, closure, Git, publication, deployment, or
external authority.

## Delivered progress output

An increment is delivered only after implementation, required checks, review,
diff disposition, accepted status, and any required destructive-operation
recovery cleanup are durable.

After a delivered non-final new-program increment, output ends with exactly:

```text
Next: INC-003 (increment 3 of 5) — part 1 of 3, task 1 of 4.
```

The increment ordinal and total come only from the Plan 1 increment order bound
and validated by traceability v3.

Before rollover, the delivered predecessor comes from status-current accepted
state and its unique validated canonical successor. Because no successor cursor
exists yet, output stops at the successor increment rather than inventing a
part or task:

```text
Next: INC-003 (increment 3 of 5) — task not started.
```

This form is valid only after the prior increment is accepted and before typed
successor rollover begins. Rollover must create the successor `ready` cursor
before its status-last write.

After rollover, the delivered predecessor no longer comes from status-current.
It is derived exclusively from the validated rollover record bound by the
successor's current status, including the prior accepted-status digest and the
record's predecessor and successor increment identifiers. The successor
increment and part/task position come exclusively from that status-current
successor cursor. The rollover successor must also be the next increment in the
bound canonical order. Caller-selected predecessor or successor identifiers
are never rendered.

After the final new-program increment:

```text
Next: program reconciliation — all 5 increments delivered.
```

Blocked or incomplete output names the blocker and exact current part and task
only when the status-current cursor validates. Otherwise it names the
status-current increment and a progress-recovery stop.

No completed/remaining total is shown beyond the stable current ordinals.

## Pre-cursor setup-family output

Manifest/status v3 and v4 programs remain on their exact setup-derived schema
families. They have a setup decision and canonical increment order but no cursor
ledger or task position. They never enter either the v5 cursor renderer or the
legacy renderer.

After a delivered non-final pre-cursor increment, the validated setup order and
canonical-successor result render exactly:

```text
Next: INC-003 (increment 3 of 5) — task progress unavailable.
```

After a delivered final pre-cursor increment, finality must be established by
the setup-bound canonical order and validated lifecycle history before rendering:

```text
Next: program reconciliation — all 5 setup-bound increments delivered.
```

Pre-cursor output never synthesizes part/task ordinals or writes progress state.

## Legacy output

Legacy programs receive no cursor ledger, synthetic task structure, setup
decision, or progress-driven status write. Navigation uses only the validated
status-current increment and existing canonical-successor result.

After a delivered legacy increment with one successor:

```text
Next: INC-003 — legacy progress ordinals unavailable.
```

After a delivered legacy increment whose finality is independently established
by existing durable evidence:

```text
Next: program reconciliation — final legacy increment delivered.
```

If canonical-successor validation returns an unavailable disposition:

```text
Next: successor unavailable — <validated bounded reason>.
```

Allowed reasons come from the existing validator, such as no allocated
successor, multiple allocated successors, or unsatisfied successor dependencies.
`No allocated successor` alone is not legacy finality evidence because v2 has no
complete canonical increment order. Arbitrary exception text, retrieved prose,
and caller-authored reasons are never rendered.

Expected legacy cursor absence is not a recovery defect. Blocked or incomplete
legacy output names the blocker and status-current increment without a finer
position unless existing durable evidence already supplies one.

## Compatibility

Compatibility is schema-led and no-rewrite:

- Only manifest v5 programs with traceability v3 and a progress-cursor ledger
  may write cursor events or status v5.
- Existing manifests and status records continue through their existing
  lifecycle without progress writes.
- Status v5 requires traceability v3 plus the exact progress-structure binding
  and either the state-limited explicit absent-cursor binding or an exact current
  cursor binding. Missing, stale, nonempty-ledger/absent-cursor,
  empty-ledger/current-cursor, optional-field upgrades, and mixed-family
  substitutions are rejected.
- Current public continuation and rollover decisions remain navigation and
  successor authority. Progress events do not replace them.
- Programs created after the setup design but before this design remain valid
  no-cursor programs; exact manifest/status v3 and v4 routes receive the
  setup-family increment-level output above rather than legacy output, v5 task
  output, or an in-place progress migration.
- No existing traceability document is rewritten solely to create stable task
  ordinals.

## Failure handling

A missing cursor outside the two valid pre-genesis states, a nonempty ledger
with an absent-cursor binding, invalid status binding, traceability drift,
unknown task, impossible transition, incomplete completion evidence, or
ambiguous successor stops without guessed output. Identical cursor/status
prefixes are adopted. Divergent events are preserved. Recovery never rewrites
history, fabricates completion, advances an increment, or creates authority.

## Test contract

Implementation must add causal writer-to-fresh-discovery tests for:

- stable increment/part/task structure, exact binding to Plan 1's approved
  increment order, reciprocal v2/v3 requirement and acceptance allocation, and
  rejection of structural changes as program revision rather than automatic
  bookkeeping;
- rejection of missing, extra, duplicate, contradictory, branched, or
  noncontiguous increment/part/task allocations that cannot produce the bound
  canonical order;
- cursorless v5 discovery only at
  `awaiting-program-approval / not-started` and
  `active / awaiting-first-increment`, with an explicit absent-cursor binding
  and empty ledger, plus rejection of every invalid absent/current binding and
  ledger combination;
- cursor genesis and every legal transition through `ready`, `in-progress`,
  `blocked`, and `completed`, including fresh discovery of a non-final task's
  completed intermediate state followed by deterministic advancement;
- traceability v3 ordered-structure validation and digest binding, manifest v5
  owner-inventory allocation of the empty ledger, exact-plan and execution-
  baseline `Modify` allocation for every later cursor write, predecessor-
  baseline allocation for rollover, status v5 cursor binding, and rejection of
  v2/v3 or pre-cursor/cursor-aware family mixing;
- rejection of gap, fork, duplicate, stale traceability, wrong ordinal, unknown
  task, impossible transition, and mixed schema family;
- failure injection after each cursor append and before its status-last write,
  followed by fresh discovery, exact transition-intent reconstruction, and
  status completion for both lifecycle transitions and same-state refreshes;
- rejection of missing, incomplete, stale, or tampered embedded transition
  intents and task completion evidence;
- successor rollover cursor allocation immediately before successor status-
  last, including failure recovery after the cursor append;
- final-task review/remediation/re-review and diff-change-request paths proving
  `completed` is not appended until the eventual diff acceptance is durable;
- proof that cursor events grant no product-change or successor authority;
- non-final, final, blocked, and progress-recovery output for new programs,
  including pre-rollover `task not started` output derived from accepted status
  and post-rollover part/task output derived from the validated rollover record
  plus the status-current successor cursor;
- legacy successor, independently proven final, unavailable-successor including
  `no allocated successor` without finality proof, blocked, and incomplete
  output without any ledger or fabricated ordinal;
- manifest/status v3 and v4 programs remaining valid on exact schema routes and
  receiving setup-bound increment-level output without cursor state or task
  ordinals; and
- a multi-increment path proving a delivered increment's line is derived before
  rollover from accepted state and canonical successor, and after rollover from
  the bound rollover record, canonical increment order, semantic traceability,
  and the exact status-current successor cursor.

Static formatting tests do not prove that an increment is delivered; the
causal tests must traverse the actual persisted lifecycle.

## Documentation and repository scope

Implementation updates the skill front door and canonical progress reference
for stable task structure, cursor transitions, status binding, delivered output,
legacy output, and pre-cursor compatibility. The output formats and recovery
rules have one canonical owner.

Design, implementation, tests, and source documentation belong only in this
repository. Installation, cached-copy synchronization, and consuming-program
rewrites remain separately authorized.

## Success criteria

This design is complete when fresh discovery can recover a new program's exact
current task from persisted status-current evidence, delivered increments emit
one truthful bounded next-work line, legacy and pre-cursor programs remain valid
without migration, every cursor append remains managed-write allocated, and no
dynamic projection or task-remapping subsystem is required.

## Non-goals

This design does not add automatic task split/combine/renumber operations,
mutable projections, completed-work remapping, program revision, expanded local
operations, product execution, diff acceptance, successor authority, Git
operations, publication, deployment, plugin installation, or consuming-program
repair.
