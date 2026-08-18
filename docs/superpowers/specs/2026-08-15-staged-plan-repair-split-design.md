# Staged-Plan Repair Split and Approval Consolidation Design

**Status:** Revised through iterative independent material review; pending a
clean final go/no-go before implementation-plan rewriting.

**Reviewed source identities:**

- `docs/superpowers/plans/2026-08-15-program-bootstrap-launch-repair.md`
  - SHA-256: `b178265c61626f4bbe0e7d14a632e7a22d3401ad7fdde9665331a38e6181acee`
  - 3,910 lines
- `docs/superpowers/plans/2026-08-14-continuation-hardening.md`
  - SHA-256: `b5d6de6dd50350362dbba62a2ebcff7e3313fd3988d88e4c119874d1ecd9b8ab`
  - 843 lines
- Repository baseline: local `main` at
  `ad654b98634efdbb13d74b71ddbdc80e4fe5e157`.
- Both source plans are untracked user-owned files. Rewriting must preserve their
  approved obligations intentionally and must not silently discard later edits.

## Purpose

Replace the overlapping 12-task lifecycle repair and five-task continuation
hardening plans with two sequential, independently testable implementation
plans:

1. program genesis and first-increment integrity at `0.1.1`;
2. continuation, recovery, and reduced approval burden at `0.1.2`.

The split changes delivery boundaries, not the core safety model. Deterministic
path, digest, state, retry, and workspace validators remain. Routine user
decisions at the same lifecycle boundary are consolidated into one direct,
exact-prompt decision while still producing separate typed records.

## Fresh Review of the Changed Repair Plan

The changed 3,910-line plan materially improves the earlier version in three
ways. These changes must be retained:

1. **Status-current successor authority.** It separates immutable genesis
   `activation_binding` from replaceable
   `current_increment_authority_binding`, persists a successor grant during
   rollover, and prevents reuse of the first-increment grant.
2. **Production continuation authority.** It adds an exact direct-user
   continuation prompt that derives both the `rollover-increment` action
   authorization and successor increment grant. Tests may invoke the production
   surface but may not manufacture those records.
3. **Managed blocked-resolution evidence.** It replaces caller-selected
   recovery files with a manifest-owned block-resolution ledger, bounded
   structured criteria, and a prompt-bound status-last recovery transaction.

The fresh review also confirms four remaining plan-design defects:

1. **The plan is two releases disguised as one.** Genesis/first-increment work
   reaches a complete diff gate without rollover or blocked recovery. Rollover,
   blocked recovery, and navigation form a second coherent subsystem with their
   own authority and retry model.
2. **Diff acceptance and continuation remain consecutive user approvals.** The
   changed plan waits for diff acceptance, renders a continuation prompt, and
   waits again. The second decision can be consolidated with the first when the
   successor is unique and fully bound.
3. **The “complete lifecycle” test is only a first-increment test.** It stops at
   `awaiting-diff-approval`. It does not prove acceptance, continuation,
   successor-grant consumption, second-increment execution, or the next diff
   gate.
4. **The two source plans still overlap.** Both claim managed-write enforcement,
   prompt hardening, installed-copy parity, package version `0.1.1`, and final
   release verification. Their current instructions require later manual scope
   removal. The rewritten plans must have disjoint ownership immediately.

No other material defect was found in the changed design. In particular,
managed-write coverage, the execution baseline, exact-plan delta validation,
status-last persistence, no-overwrite adoption, sink-derived recovery context,
and installed-copy comparison remain justified.

## Plan A: Program Genesis and First-Increment Integrity

**Target file:**
`docs/superpowers/plans/2026-08-15-program-bootstrap-launch-repair.md`

**Package version:** `0.1.1`

**Goal:** Prove the complete safe path from one explicit creation request to a
real reviewed first-increment diff, with no intermediate digest, control-file,
workspace, or routine exact-plan approval.

**Required causal path:**

```text
explicit create request
  -> durable unapproved proposal
  -> exact launch prompt
  -> fresh-task activation
  -> status-current first-increment grant
  -> exact-plan execution baseline
  -> authorized production delta
  -> review and verification
  -> awaiting-diff-approval
```

Plan A also provides one exact `accept-stop` prompt and transaction so the user
can complete the first increment without waiting for Plan B. It does not provide
successor continuation.

**Task ownership:**

1. Proposal authority model, validation modes, and immutable new-program schema.
2. Atomic no-overwrite proposal publisher and publication recovery.
3. Lifecycle-aware discovery for preparation, activation-ready, active,
   closure, terminal history, and explicit fail-closed future routes.
4. Shared exact prompt envelope, launch prompt, and retry-safe activation from
   one direct submission.
5. Transition-specific managed-write declarations, forward continuation
   allocation, and persistence-sink enforcement.
6. Shared typed exact-plan preparation and materialization transactions for
   `approval:standard`, `approval:pre-approve`, and
   `approval:full-increment`, with execution baseline, action authorization,
   status-last persistence, prefix recovery, and exact-plan product-delta
   validation.
7. Production-owned, typed review-preparation transaction that derives the
   status-current manifest-owned review evidence and packet, validates the
   complete in-memory bundle, creates both files with no-overwrite semantics,
   derives review and verification bindings, and advances
   `reviewing -> verified -> awaiting-diff-approval` through compare-and-swap
   status replacements with prefix recovery and causal tests.
8. Canonical diff-acceptance builder and prompt-bound `accept-stop`
   persistence, including an acyclic disposition binding and retry adoption.
9. New-model closure storage, typed no-overwrite preparation of the derived
   reconciliation and packet, exact closure approval, prefix recovery, and
   status-last transitions through `awaiting-closure-approval` to `closed`.
10. Deferred-operation quarantine and unsupported-mutation guards.
11. Honest first-increment front door and synchronized documentation.
12. Separate-process genesis-to-first-diff-and-accept lifecycle regression plus a reusable
   `0.1.1` compatibility fixture for Plan B.
13. Package synchronization, deterministic verification, and optional
    caller-path-bound installed-copy comparison.

The authority model and publisher stay separate because each has an
independently rejectable contract and causal test surface. Internal task review
does not create a user approval checkpoint.

### Forward-compatible immutable control plane

Every Plan A proposal must already contain the immutable structure required for
Plan B. The new-program manifest owns:

- the status-current increment-grant ledger used by launch;
- an empty append-only rollover ledger;
- an empty append-only block-resolution ledger;
- the immutable increment-storage descriptor;
- an immutable closure-storage descriptor that derives the future closure
  reconciliation and closure packet paths without requiring either file to
  exist during proposal publication;
- logical roles for approvals, action authorizations, increment grants,
  rollovers, block resolutions, and status.

The closure descriptor is
`implementation-closure-storage/v1`. It names normalized relative filenames
beneath one manifest-owned closure directory. A shared
`resolve_program_closure_paths(program_root)` validates containment, rejects
symlinks and unsafe existing entries, and returns the reconciliation and packet
paths. New programs use this resolver; existing legacy manifests continue using
their accepted `closure_reconciliation` and `closure_packet` logical roles.

Plan A does not write rollover or block-resolution records. It provisions their
empty managed owners so Plan B can continue a `0.1.1` program without mutating an
immutable manifest or introducing a migration merely to add storage.

Every new-model exact-file plan must allocate the later managed paths that
acceptance, blocked recovery, and any traceability-allocated successor may
write. Plan A implements one reusable
`required_future_lifecycle_writes(program_root, workspace_root, increment_id)`
derivation and enforces it before materialization. Plan B reuses the same
derivation for every successor plan; it may extend only the transition-specific
set when its new record schemas require a path already owned by the immutable
manifest.

The disposition-aware file map includes, as applicable:

- approvals, status, action authorizations, increment grants, rollover ledger,
  and block-resolution ledger under `Modify`;
- the current handoff and a uniquely traceability-allocated successor brief
  under `Create` when a successor exists;
- the closure reconciliation and closure packet under `Create` when the current
  increment is final and traceability allocates no successor;
- current review evidence, review packet, and execution baseline under their
  existing required dispositions.

This is allocation, not authority. A final increment declares its derived
closure files instead of inventing a successor handoff or brief. It still
declares approval, status, action, grant, rollover, block-resolution, and review
owners. Plan A may not use the future continuation declarations to perform
rollover or blocked recovery.

### Deferred-operation quarantine

Deferral must be enforced at persistence sinks, not only in discovery or prose:

- the legacy caller-authored rollover API returns an unconditional
  `legacy-rollover-upgrade-required` error before every write;
- the generic `awaiting-diff-approval -> accepted` edge fails for new-program
  manifests unless it is invoked through Plan A's typed prompt-bound
  `accept-stop` sink; accepted legacy manifests retain their validated existing
  transition behavior;
- direct generic transitions into or out of `blocked` fail before status
  persistence unless a valid typed sink-derived context is present; Plan A
  provides no production writer for that context;
- discovery preserves any legacy or partial evidence and returns an exact
  recovery-required stop;
- snapshot tests call the direct legacy surfaces and prove every repository byte
  remains unchanged.

Plan B replaces these guards only when its prompt-bound, retry-safe persistence
transactions and causal tests are complete.

### Bootstrap, activation, and materialization transactions

Plan A retains the source plan's owner-bound, no-overwrite proposal publisher
and makes its recovery contract explicit. After the complete proposal candidate
validates in memory, the publisher writes the owner receipt and every canonical
managed artifact in a deterministic order inside its same-filesystem staging
tree, adopts the exact owner-bound final root, and publishes `manifest.json`
last. Fresh bootstrap recovery validates every present prefix before generic
program discovery; exact bytes are adopted, while any divergent, unsafe, or
foreign-owned byte stops without deletion or overwrite. The manifest is the
discoverability commit point, and a lost response after it is idempotent.

Activation is one typed transaction derived only from the freshly rerendered
launch prompt and current proposal. It appends or adopts the program approval,
workspace-selection approval, and first-increment grant in that order, then
replaces status with `active` / `preparing` last. Discovery examines these exact
receipt prefixes while the proposal status still controls and returns
`program-activation-retry-ready`; divergence returns
`program-activation-recovery-required` without cleanup or new identifiers.

Plan A also owns one shared typed exact-plan preparation and materialization
interface. Its pure builder consumes canonical exact-plan candidate bytes plus
the status-current grant, workspace binding, current repository observation,
and selected approval mode. Before the first write it validates the complete
plan, required future lifecycle writes, execution-baseline candidate, and
derived plan-bound action authorization.

For `approval:standard`, preparation creates or adopts the exact plan and
replaces status with `awaiting-plan-approval` last, then renders one exact plan-
approval prompt. Direct submission appends or adopts the plan-approval event,
creates or adopts the execution baseline, appends or adopts the action
authorization, and replaces status with `authorized` last. It never uses the
existing `approval -> status -> action` ordering.

For `approval:pre-approve` and `approval:full-increment`, the launch-bound grant
already permits omission of that routine plan question. The same interface
creates or adopts the exact plan, creates or adopts the execution baseline,
appends or adopts the action authorization, and replaces status with
`authorized` last. The omission changes only whether an exact plan-approval
event is required; it does not omit the baseline, action record, managed-write
validation, or diff decision.

Fresh discovery checks exact plan/materialization prefixes before treating a
present plan, baseline, or action record as unknown. It returns
`plan-preparation-retry-ready` or `plan-materialization-retry-ready` only when
the candidate can be reconstructed from the controlling status and bound input;
otherwise it returns the corresponding `*-recovery-required` stop and preserves
all bytes. Plan B must reuse this interface for every successor and may not
restore the status-before-action checkpoint path.

**Explicitly excluded from Plan A:**

- successor rollover persistence;
- successor continuation authorization;
- production blocked-resolution persistence;
- the live continuation replay;
- second-increment execution;
- revision, supersession, and cancellation writers.

Until Plan B is complete, both discovery and persistence sinks must preserve
evidence and return explicit no-write stops for unsupported successor
continuation and blocked entry or resolution. Plan A must not imply those
operations are repaired.

## Plan B: Continuation, Recovery, and Approval Consolidation

**Target file:**
`docs/superpowers/plans/2026-08-14-continuation-hardening.md`

The filename remains for link stability, but its title and complete content are
rewritten to own the post-first-diff subsystem.

**Package version:** `0.1.2`

**Goal:** Continue accepted work across increments and recover blocked work
through exact direct-user decisions, managed ledgers, status-current grants,
fresh-process retry, and no extra routine approval between diff acceptance and
the next increment.

**Task ownership:**

1. Structured bounded continuation result using Plan A's exact prompt envelope.
   Preserve accepted legacy continuation bytes where their schema requires it;
   do not redefine the shared envelope.
2. Extend Plan A's canonical diff-disposition builder and persistence sink with
   retry-safe `accept-continue`; preserve its `accept-stop` bytes and behavior.
3. Status-current successor grant, authority-first rollover records, immutable
   manifest, status-last successor transition, and inherited product delta.
4. Sink-derived blocked context and exact prompt-bound managed resolution ledger.
5. Fresh-process `0.1.1`-to-`0.1.2` upgrade and two-increment regression,
   successor reuse of Plan A's exact-plan materialization transaction, a
   focused blocked-recovery causal regression, and a second accepted-increment
   rollover preflight.
6. Optional separately authorized live fresh-task continuation replay.
7. `0.1.2` skill/docs/package synchronization and final deterministic release
   gate.

Plan B reuses Plan A's managed-path resolver, structural exact-file map,
execution baseline, exact prompt envelope, discovery model, package digest
comparison, and first-increment compatibility fixture. It may extend the same
source files at explicitly named interfaces, but it must not reimplement or
re-own those contracts.

## User Approval Model

### 1. Create

An explicit request to create a program authorizes only the new program's local
control-plane proposal writes. It returns one exact launch prompt and asks no
intermediate question.

### 2. Launch

Direct submission of the exact launch prompt is one compound decision. It
persists separate program approval, workspace approval, and first-increment
grant records, then executes under the selected approval mode. Under
`approval:full-increment`, there is no routine exact-plan pause before the first
diff gate.

New-program creation and activation support only approval modes whose verified
diff remains a direct user decision:

- `approval:standard`;
- `approval:pre-approve`;
- `approval:full-increment`.

The default is `approval:full-increment`. A request to create or activate a new
program under `approval:full-diff` or `approval:full` fails before proposal,
approval, grant, or status writes with
`unsupported-new-program-approval-mode`. Those modes currently bypass user diff
acceptance, while `approval:full` also implies automatic continuation; both
contradict this design's explicit diff-disposition boundary.

Existing persisted legacy programs that already name either automatic mode
remain readable and retain their existing validated current-increment behavior.
`approval:full-diff` may keep its validated automatic current-diff acceptance.
`approval:full` may keep validated current-increment plan, execution, review, and
automatic diff behavior only. Neither mode may use the caller-authored legacy
rollover writer or automatically begin a successor increment.

At a legacy successor boundary, both modes return
`legacy-rollover-upgrade-required` before every write. No manifest, plan, grant,
or status migration is included in either repair plan. Completion documentation
must identify this deliberate compatibility restriction: accepted legacy bytes
remain readable, but unsafe automatic successor continuation is removed. Legacy
programs are not silently migrated into the new prompt-bound continuation
transaction.

### 3. Diff disposition

At `awaiting-diff-approval`, always render this exact copy-ready choice after
validating the current diff:

- **Accept and stop.** Accept the current diff and leave the program at the
  accepted current increment.

Render the second choice only after separately proving that traceability has
exactly one allocated successor whose dependencies are satisfied:

- **Accept and continue to `<successor-id>`.** Accept the current diff and start
  exactly the named, uniquely allocated successor under its bound semantic brief
  and approval mode.

A final increment, multiple possible successors, or unsatisfied successor
dependencies suppresses only “accept and continue.” It never prevents “accept
and stop.” The rendered result states why continuation is unavailable without
turning that reason into an acceptance blocker.

Plan A owns the acceptance builder, exact `accept-stop` prompt, approval event,
accepted-status disposition binding, approval-only retry, and idempotent lost
response. Plan B must preserve those bytes and extends the same interface only
with the optional `accept-continue` candidate and continuation suffix.

The second choice is one user decision but two internal retry-safe transactions.
Before rendering either choice, a pure canonical acceptance builder loads and
validates the current `awaiting-diff-approval` status, review and verification
bindings, exact plan, execution baseline, and live accepted product-delta
candidate. It derives:

- the diff-approval event and identifier;
- the exact accepted-current status bytes and digest;
- the disposition checkpoint identifier.

A separate pure continuation extension consumes that validated acceptance
candidate and, only when one satisfied successor exists, derives the successor
semantic and workspace inputs before deriving:

- the rollover action-authorization identifier,
  successor-grant identifier, successor brief and digest, inherited accepted
  product-delta inventory and digest, and a non-cyclic successor-authority
  projection.

The projection schema is
`implementation-successor-authority-projection/v1`. It contains only values
known before any continuation record or accepted status is serialized:

- program id and revision;
- current and successor increment ids;
- prior `awaiting-diff-approval` status digest and sequence;
- diff-disposition checkpoint and approval-event ids;
- successor brief and accepted-product-delta digests;
- successor approval mode;
- selected workspace path, branch, base/head commits, and selection digest;
- inherited-workspace digest;
- allowed conditional action ceiling;
- rollover action-authorization id and successor grant id.

It explicitly excludes the accepted status digest, submitted-prompt digest,
action-authorization record digest, successor-grant record digest, rollover
record digest, and successor status digest. The accepted status may bind this
projection. After the prompt-bound records are persisted, the rollover record
and successor status replace the projection with the actual action/grant ids,
canonical record digests, submitted-prompt digest, and status-current authority
binding.

Identifier and byte construction follows one required topological order:

1. Build an immutable base seed from the schema domain, bound program revision,
   current increment, prior status digest and sequence, decision, review,
   verification, exact-plan, execution-baseline, and accepted-product-delta
   digests plus, for continuation, the already validated successor semantic and
   workspace inputs. The seed contains no derived identifier, final record
   bytes, record digest, status digest, or prompt digest.
2. Derive the disposition checkpoint id from that base seed alone.
3. Derive the diff-approval event id from the base seed and checkpoint id.
4. For continuation, derive the rollover action-authorization id from the base
   seed, checkpoint id, and approval-event id, then derive the successor-grant
   id from those values and the action-authorization id.
5. Build the successor-authority projection from the pre-record values and the
   now-derived ids.
6. Serialize the accepted status and compute its digest, binding the projection
   only for `accept-continue`.
7. Render the exact prompt from the preceding canonical values and compute the
   submitted-prompt digest only after direct submission.
8. Serialize the approval and continuation records that store that submitted-
   prompt digest, then persist or adopt them in transaction order.

No derivation step may depend on a value produced by a later step. In
particular, the checkpoint id is not part of its own seed, and no identifier
hashes final record bytes, a record field containing the submitted-prompt
digest, or the prompt digest itself.

The accepted status contains an acyclic
`implementation-diff-disposition-binding/v1` object with:

- decision: `accept-stop` or `accept-continue`;
- checkpoint id and diff-approval event id;
- prior status digest and sequence;
- review, verification, exact-plan, execution-baseline, and accepted-product-
  delta digests;
- only for `accept-continue`: successor increment id, successor brief digest,
  rollover action-authorization id, successor grant id, inherited-product-delta
  digest, and the exact successor-authority projection.

The binding excludes the accepted status's own digest and the submitted-prompt
digest. This keeps accepted-status derivation acyclic while durably distinguishing
stop from continue. The prompt may contain the already derived accepted-status
digest. The prompt itself has no self-digest field; its final digest is stored in
the canonical approval and continuation records produced after direct
submission. Fresh validation loads the approval event through the status-bound
event id and requires its decision and submitted-prompt digest to match the
disposition binding and rerendered prompt.

On exact direct submission, persist or adopt:

1. the canonical diff-approval event;
2. the canonical accepted-current status by compare-and-swap;
3. for “accept and continue,” the prompt-bound rollover action authorization;
4. the successor increment grant;
5. the current handoff and successor brief;
6. the rollover ledger record;
7. the successor status by compare-and-swap.

Each status is last within its transaction. “Accept and stop” ends after step 2.
“Accept and continue” performs all seven steps from the one submitted prompt.

Fresh discovery inspects exact disposition receipts before generic unknown-record
rejection and classifies every prefix:

- pristine `awaiting-diff-approval`: ordinary disposition prompt ready;
- exact approval-only prefix: `increment-acceptance-retry-ready`;
- accepted status with `decision=accept-stop` and no accepted-state continuation
  prefix: completed accepted state; an exact lost-response resubmission is
  idempotently successful and never routes to continuation;
- accepted status with `decision=accept-continue` but no continuation prefix:
  `accepted-continuation-retry-ready`;
- exact action/grant prefix: `increment-continuation-retry-ready`;
- exact navigation/rollover prefix: `increment-rollover-retry-ready`;
- exact successor status: ordinary successor resume;
- divergent, ambiguous, stale, or multiply bound prefix:
  `continuation-recovery-required`.

Resubmission of the same exact prompt adopts a valid prefix and continues. A
lost response after either status replacement is idempotent. Divergent bytes,
changed review or product evidence, multiple successors, unsatisfied
dependencies, or a prompt mismatch stop without cleanup, duplicate authority,
or record substitution.

For `accept-stop`, successor ambiguity or dependency state is irrelevant. For
`accept-continue`, a successor becoming ambiguous, unallocated, or unsatisfied
after prompt rendering makes the prompt stale and stops before continuation
writes; it does not undo an already persisted exact acceptance prefix.

### Later continuation after accept-and-stop

An accepted-and-stopped program remains continuable later. A new explicit
“continue the accepted program” request performs read-only validation and renders
a distinct exact accepted-state continuation prompt.

This route uses
`implementation-accepted-state-continuation-binding/v1`; it never reuses the
diff-disposition checkpoint, diff-approval event, or original `accept-stop`
prompt as continuation authority. Its immutable base seed has its own schema
domain and contains the accepted status digest and sequence, program revision,
current and uniquely satisfied successor increment ids, successor brief and
accepted-product-delta digests, successor approval mode, validated workspace and
inherited-workspace bindings, and allowed conditional action ceiling. It
contains no derived identifier, final record byte or digest, successor status
digest, or prompt digest.

Construction is topological: derive a distinct accepted-state continuation
checkpoint id from that seed; derive the rollover action-authorization id from
the seed and checkpoint; derive the successor-grant id from those values and
the action id; build the accepted-state successor-authority projection; render
the exact prompt; and only after direct submission compute its digest and
serialize the action, grant, navigation, rollover, and successor-status records.
Direct submission performs continuation steps 3 through 7 above, with successor
status last. Every record binds the accepted-state schema and checkpoint so its
identifier space and retry path cannot collide with immediate
`accept-continue`.

While the accepted status still controls, fresh discovery inspects exact later-
continuation action, grant, handoff, brief, and rollover prefixes before
classifying `accept-stop` as merely complete. It returns
`accepted-state-continuation-retry-ready` for exact action/grant prefixes and
`accepted-state-rollover-retry-ready` for exact navigation/rollover prefixes.
Any mismatch returns `accepted-state-continuation-recovery-required`, preserves
all bytes, and refuses a replacement checkpoint, authority record, grant, or
prompt.

The later prompt is schema- and byte-distinct from the earlier `accept-stop`
prompt. Replaying `accept-stop` remains an idempotent acceptance result and can
never authorize continuation. If the accepted status already records
`decision=accept-continue`, discovery requires retry of that original compound
prompt and does not offer a second continuation prompt. No successor, ambiguous
successors, or unsatisfied dependencies return an exact no-write continuation
stop while leaving the accepted increment valid.

This consolidation does not make diff acceptance automatic. It removes only the
second routine question after the user has explicitly chosen “accept and
continue.”

### 4. Blocked recovery

A block is exceptional and may require new evidence. Once every sink-authored
criterion is satisfied, one exact direct-user resolution prompt persists the
separate action-authorization and managed resolution records, then restores only
the recorded prior states. No additional routine confirmation follows that
prompt.

### Internal preparation transactions

Review and closure preparation are typed, deterministic transactions even
though they require no additional user decision. Their pure builders derive and
validate all canonical output bytes before the first write. Their sinks use
no-overwrite creation, adopt only byte-identical files at the exact derived
paths, and replace status by compare-and-swap only after the required files are
durable.

Fresh discovery inspects these transaction prefixes before applying generic
one-sided-bundle or unexpected-file rejection. From the controlling prior
status and its bound inputs, it reconstructs the expected bytes and returns
`review-preparation-retry-ready` or `closure-preparation-retry-ready` for an
exact prefix. Missing later files remain absent until resubmission of the same
typed operation adopts the prefix and completes it. Any changed, unsafe,
unexpected, ambiguously owned, or non-reconstructable prefix returns the
corresponding `*-recovery-required` stop while preserving every byte. It never
cleans up, overwrites, invents a replacement identifier, or skips to a later
status.

### 5. Closure and consequential actions

Plan A owns closure for both its programs and later Plan B successors. After an
accepted final increment with no allocated successor, the closure-preparation
transaction derives and validates the reconciliation and closure packet at the
manifest-derived paths, creates the reconciliation then packet, replaces status
with `awaiting-closure-approval` last, and renders one exact closure prompt.
Direct submission persists or adopts the typed closure approval and replaces
status with `closed` last. Missing, changed, unsafe, unallocated, divergent, or
invalid closure artifacts stop before approval or status writes except for an
exact adoptable preparation prefix. Partial preparation and partial approval
are retryable; lost responses after either status are idempotent.

Program closure remains one explicit final decision. Commits, pushes, pull
requests, installation, publication, deployment, destructive work, provider
changes, permission changes, and other external actions remain outside lifecycle
approval and require their own authority.

## Plan-Execution Approval Model

Implementation workers do not stop for user approval at each task review.
Focused review and deterministic checks are internal verification steps.

Each rewritten plan must route execution through the applicable plan-execution,
test-driven-development, systematic-debugging, completion-verification, and
code-review skills. Skill invocation does not replace the plan's exact tests,
evidence, authority checks, or stop conditions.

One user authorization may cover all bounded local source edits and deterministic
checks in one approved plan. One optional authorization may cover that plan's
specified local commits. The worker stops only for:

- a material contradiction or changed requirement;
- unexpected user-owned workspace overlap;
- a nonzero required validator that cannot be repaired within scope;
- scope expansion or a new public compatibility decision;
- destructive, external, installation, publication, or provider action;
- a commit when commit authority was not included.

Remove repeated per-task “if commit authority is separately granted” paragraphs.
Keep one global commit boundary and one final report of what was or was not
authorized.

After every task's focused self-review, each complete Plan A and Plan B release
candidate must run its package validation and full deterministic suite once on
the final unchanged tree, then receive exactly one bounded independent material
review from a reviewer that did not implement that candidate. Reviewer output is
evidence, not repair or action authority. The controller validates every finding
and changes the candidate only for an evidence-supported material defect within
the approved plan. After a repair, rerun the affected checks and any final-suite
checks invalidated by the changed inputs, then request only a focused independent
follow-up tied to that defect. Do not repeat review of an unchanged candidate.
Plan B may not begin until Plan A has no unresolved material finding; completion
of the repair requires the same gate for Plan B. These reviews create no new user
checkpoint unless they expose one of the stop conditions above.

## Test Contract

Plan A must causally prove:

- creation asks no intermediate question;
- launch asks no routine question before diff acceptance;
- `approval:standard` creates an exact plan-approval prompt, and direct
  submission in a separate process persists approval, baseline, action
  authorization, then `authorized` status before the increment reaches its real
  diff gate;
- `approval:pre-approve` and `approval:full-increment` omit that routine plan
  prompt but use the same baseline-before-action, status-last materialization
  contract and still stop for diff disposition;
- new-program requests using `approval:full-diff` or `approval:full` fail before
  every write, while accepted legacy records using those modes remain readable;
- exact managed writes are declared before any persistence;
- a planned product delta survives fresh state validation;
- unrelated or preserved user work cannot be claimed;
- `reviewing -> verified` loads only the status-current, manifest-derived,
  exact-plan-declared review evidence and packet; it derives the review and
  verification bindings in the same atomic status replacement, while missing,
  changed, unsafe, invalid, or replayed evidence leaves status unchanged except
  that an exact typed preparation prefix is adopted and completed;
- the first increment reaches a real review packet and diff gate in separate
  processes;
- direct `accept-stop` submission appends/adopts its approval, writes a status
  with `decision=accept-stop`, survives approval-only interruption, and is
  idempotent after accepted-status loss of response;
- direct generic new-model diff acceptance cannot bypass the typed sink;
- an accepted final increment derives only its manifest-owned, exact-plan-
  declared reconciliation and packet, reaches `awaiting-closure-approval`, and
  closes from one exact direct-user approval with approval-only retry and
  post-status idempotence; exact partial preparation is adopted, while divergent
  partial preparation is preserved and stops;
- a nonfinal accepted increment cannot enter closure, while a final increment
  does not require or invent successor navigation files.

Plan A must inject a failure after every successfully persisted prefix of each
transaction, restart discovery in a fresh process, and resubmit the same typed
operation or exact prompt:

- proposal owner receipt and each subsequent canonical staging artifact before
  the next artifact;
- complete owner-bound staging or adopted final root before `manifest.json`;
- `manifest.json` before the successful publication response;
- program approval before workspace-selection approval;
- workspace-selection approval before first-increment grant;
- first-increment grant before `active` / `preparing` status;
- `active` / `preparing` status before the successful activation response;
- standard-mode exact plan before `awaiting-plan-approval` status;
- `awaiting-plan-approval` status before returning the exact plan prompt;
- standard plan approval before execution baseline;
- execution baseline before plan-bound action authorization;
- plan-bound action authorization before `authorized` status;
- automatic-mode exact plan before execution baseline, followed by the same
  baseline, action-authorization, and `authorized` boundaries;
- each atomic `authorized -> implementing -> reviewing` status replacement
  before its successful response or next transition;
- review evidence before review packet;
- review packet before verified status;
- verified status before `awaiting-diff-approval` status;
- `awaiting-diff-approval` status before returning its exact disposition prompt;
- `accept-stop` diff approval before accepted status;
- closure reconciliation before closure packet;
- closure packet before `awaiting-closure-approval` status;
- `awaiting-closure-approval` status before returning its exact closure prompt;
- closure approval before closed status.

For every Plan A prefix, exact bytes are adopted and the transaction completes
once. Lost responses after proposal publication, activation, `authorized`,
`implementing`, `reviewing`, `awaiting-diff-approval`, accepted,
`awaiting-closure-approval`, and closed status are idempotent. Independently
mutating the newest file or record produces the exact typed recovery-required
stop, preserves all bytes, and refuses cleanup, replacement identifiers,
duplicate authority, or a later status transition.

Plan B must causally prove:

- direct “accept and continue” submission performs no second user checkpoint;
- accept-and-stop remains available with no successor, multiple successors, or
  unsatisfied successor dependencies;
- accepted status durably distinguishes `accept-stop` from `accept-continue`, and
  lost-response discovery never routes a stopped decision into continuation;
- the disposition prompt and derived records bind the current review,
  verification, exact-plan, accepted-product-delta, successor, brief, workspace,
  and authority tuple;
- a crash after the diff-approval append but before accepted status is freshly
  discoverable and retryable from the same prompt;
- a crash after accepted-current persistence is freshly discoverable and
  retryable from the same prompt;
- lost responses after accepted status and successor status are idempotent;
- the successor status consumes a distinct successor grant rather than genesis
  authority;
- inherited accepted product bytes become successor program history, not
  user-owned dirt;
- a program created and executed under the frozen `0.1.1` compatibility fixture
  continues under `0.1.2` without rewriting its manifest or first exact plan;
- the successor exact plan satisfies the same reusable future-write derivation;
- one causal branch blocks the nonterminal second increment, rediscovers it in a
  fresh process, resolves it through the managed prompt-bound ledger, resumes
  exactly its prior nonterminal state, and then reaches the second real diff
  gate;
- a separate causal branch reaches and accepts the second diff, then preflights
  and completes one further rollover to an allocated third increment without
  manifest or second-plan amendment;
- an accepted-and-stopped program can later render and submit a distinct exact
  continuation prompt whose accepted-status-rooted identifiers cannot collide
  with immediate continuation, while replaying its original stop prompt never
  continues;
- every successor approval mode reuses Plan A's status-last exact-plan
  preparation and materialization transaction in a fresh process;
- blocked entry, fresh discovery, exact resolution submission, and restored
  execution cross production writer/reader boundaries;
- navigation-only handoffs never authorize lifecycle mutation;
- exact prompt tampering and stale state stop before writes.

Add explicit accepted-status step-2 tests for both choices: stop is complete and
idempotent; continue is retry-ready. Add final-increment, ambiguous-successor,
and unsatisfied-successor tests proving acceptance remains available while
continuation is omitted. Repeat future-write validation against the successor
exact plan rather than proving it only on the first fixture.

### Complete failure-injection matrix

Plan B must inject one failure immediately after every successfully persisted
prefix, restart discovery in a fresh process, and resubmit the same exact prompt
or typed materialization operation:

- diff approval before accepted status;
- accepted status before continuation action authorization;
- rollover action authorization before successor grant;
- successor grant before handoff;
- handoff before successor brief;
- successor brief before rollover record;
- rollover record before successor status;
- successor exact plan before execution baseline for automatic materialization;
- successor execution baseline before plan-bound action authorization;
- successor plan-bound action authorization before `authorized` status;
- for a standard-mode successor, exact plan before
  `awaiting-plan-approval`, plan approval before baseline, baseline before
  action authorization, and action authorization before `authorized`;
- block-resolution action authorization before resolution-ledger record;
- resolution-ledger record before resumed status.

Run the action-authorization-through-successor-status portion twice: once after
the immediate `accept-continue` accepted-status prefix, and once from an
accepted-and-stopped status using the distinct accepted-state continuation
checkpoint and identifiers. For each prefix, exact bytes are adopted and the
transaction completes once.
Add a lost-response case after accepted status, successor status, and resumed
status. At every prefix, independently mutate the newest record or managed file
and prove fresh discovery returns the exact recovery-required disposition while
preserving every byte and refusing cleanup, replacement identifiers, or a second
authority record. The matrix is release-blocking deterministic evidence; it is
not replaced by source-text assertions or the optional live replay.

Static text assertions supplement but do not replace these behavioral tests.

## Compatibility and Release Boundaries

- Preserve existing v1/v2 readers and accepted legacy bytes.
- Plan A owns `0.1.1`; Plan B owns `0.1.2`.
- New-program manifests reject `approval:full-diff` and `approval:full` before
  writes. Legacy manifests already using those modes remain dual-read and are
  never silently converted to the explicit diff-disposition model. Their
  validated current-increment behavior may remain, but successor rollover always
  stops at `legacy-rollover-upgrade-required` before writes, including for
  `approval:full`.
- Plan A owns the shared prompt envelope, managed-path resolver, exact-file map,
  immutable future ledger and closure storage, execution baseline, package digest
  comparison, canonical `accept-stop` builder and sink, closure transaction, and
  `0.1.1` compatibility fixture. Plan B extends those named interfaces but may
  not redefine their contracts.
- Sequential plans may modify the same source, test, documentation, or metadata
  file. Their behavioral obligations and version ownership must be disjoint;
  every shared-file modification must be listed explicitly in Plan B as an
  extension of a Plan A interface.
- Each plan runs package validation and the full deterministic suite once on its
  final unchanged tree, then passes the bounded independent material-review gate
  defined above before its release candidate is complete.
- Installed-copy comparison remains optional, read-only, and bound to an exact
  caller-supplied root.
- Neither plan installs, commits, pushes, publishes, deploys, or runs a live
  evaluator without separate authority.
- Plan B retains the fresh-task live continuation replay as an optional,
  separately authorized evidence gate. Its absence does not block deterministic
  source completion, and the completion report must state that runtime
  front-door behavior remains untested when it was not run.
- Plan B begins only from a freshly verified completed Plan A tree. If Plan A's
  implemented interfaces differ from their written contracts, Plan B must be
  reconciled before execution rather than silently adapting during mutation.

## Rewriting Rules

1. Re-read and hash both source plans immediately before applying their rewrite.
   Stop on any change from the reviewed identities above until the new bytes are
   reviewed.
2. Use the current changed repair plan as the source of truth for successor
   authority and managed blocked recovery; do not regress to the earlier
   caller-selected authorization or evidence-file designs.
3. Move behavioral obligations to exactly one plan. Do not duplicate normative
   ownership or version ownership across both plans. When both plans modify the
   same file sequentially, name the Plan A interface that Plan B consumes and the
   exact extension Plan B adds.
4. Every task must have one independently testable deliverable and one internal
   focused self-review. After all tasks and final deterministic checks, each
   coherent plan must receive exactly one bounded independent material review,
   with a focused follow-up only for a validated material defect. Neither review
   creates a user checkpoint unless a stop condition is reached.
5. Preserve all user-owned work and do not stage, commit, install, or mutate
   external state while rewriting the plans.

## Success Criteria

- The two plans have disjoint behavioral obligation, task, and version ownership.
  Sequential shared-file modifications are explicitly inventoried as Plan B
  extensions of Plan A interfaces.
- Plan A truthfully delivers creation through the first diff gate at `0.1.1`.
- Plan A can also accept and close a final first increment without Plan B.
- Plan B truthfully delivers accept-and-continue, successor execution, and
  blocked recovery at `0.1.2`.
- A `0.1.1` program carries the immutable ledger roles and exact-plan write
  allocation needed for `0.1.2` continuation without manifest or plan rewriting.
- Plan A disables unsafe legacy rollover and blocked-transition writers before
  exposing its repaired first-increment path.
- Plan A also prevents generic new-model diff acceptance from creating a status
  without its typed disposition binding while preserving validated legacy
  behavior.
- Plan A disables every caller-authored legacy successor rollover. Legacy
  `approval:full` does not override that sink-level safety boundary.
- Plan A owns the production review-to-verified sink and derives its bindings
  from validated persisted evidence before any diff disposition is rendered.
- The changed plan's successor-grant and managed-resolution repairs are retained.
- The disposition transaction has deterministic acyclic record construction and
  fresh-process recovery for approval-only, accepted, continuation, rollover,
  and lost-response prefixes.
- Accepted status binds only the pre-record successor-authority projection;
  actual prompt and record digests appear only after their records exist and in
  the final rollover/successor bindings.
- Runtime approval is one decision per meaningful lifecycle boundary, not one
  decision per internal record or routine action.
- Accept-and-stop is never conditioned on successor availability, and accepted
  status contains an acyclic decision binding that prevents stop/continue retry
  ambiguity.
- Accept-and-stop completes the increment but does not permanently waive later
  continuation; later continuation requires a new, distinct exact direct-user
  prompt.
- Every successor exact plan repeats the future lifecycle write allocation, so
  continuation and recovery do not work only for the first increment.
- Every final exact plan allocates the derived closure reconciliation and packet,
  and closure works for both Plan A first increments and Plan B successors
  without manifest mutation.
- Blocked recovery is tested only from a legal nonterminal increment state;
  further rollover is tested separately from an accepted increment.
- Every acceptance, continuation, rollover, and blocked-resolution write prefix
  has a fresh-process adoption, divergence-preservation, and post-status
  idempotence test.
- Every task receives focused self-review, and each final unchanged Plan A and
  Plan B candidate passes one bounded independent material review with no
  unresolved material finding. These evidence gates do not burden the user or
  grant repair, commit, or consequential-action authority.
- Diff acceptance, closure, commits, and consequential actions remain explicit.
- No source plan, implementation file, installed copy, Git metadata, or external
  state is changed by this design document.
