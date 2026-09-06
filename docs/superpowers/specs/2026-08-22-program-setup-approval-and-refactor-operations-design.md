# Program Setup Approval and Refactor Operations Split Design

**Status:** The original monolithic design is superseded by two active,
sequential designs and one deferred design. This file is the canonical overview
and ordering contract, not a direct implementation specification.

**Original monolith provenance:** Before the split, this path contained 1,311
lines at SHA-256
`b72b0d3c8a87b52302a163d98558ecf80ef557dfcf439b669a7ee6dc03e1905b`.
The three child designs preserve its material obligations while removing
cross-subsystem implementation coupling.

## Purpose

Deliver three user outcomes without treating them as one release:

1. one readable program-setup decision followed by activation that grants no
   product-change authority;
2. safe typed local refactors whose accepted results can include present and
   absent paths; and
3. truthful persisted part/task progress for new programs.

The original combined all three outcomes with one compatibility and recovery
model. Repeated material review showed that fixes in one subsystem created
new obligations in the others. The split makes each boundary independently
testable and reviewable.

## Shared invariants

Every child design preserves:

- immutable source and approved-program bindings;
- visible semantic authority and hidden machine integrity kept distinct;
- fresh repository, workspace, and protected-work observation;
- deterministic status-last transactions;
- owner-bound no-overwrite publication and exact-prefix recovery;
- exact plans, execution baselines, and plan-bound action authorization before
  product changes;
- review, verification, and diff disposition before increment acceptance;
- schema-led compatibility with no in-place reinterpretation;
- no reset, clean, stash, overwrite, guessed recovery, or fabricated authority;
  and
- separate authorization for commits, pushes, pull requests, merges,
  publication, deployment, external migration, permissions, providers, and
  every other consequential action.

## Canonical implementation sequence

### 1. Program setup and activation

**Design:**
[Program Setup and Activation Design](2026-08-23-program-setup-and-activation-design.md)

This design owns the readable recap, direct setup decision, recoverable
proposal publication, setup-activation transaction, waiting state, fresh-task
start, source-defined gate decisions, authority chain, and preservation of
existing lifecycle families.

It introduces manifest/status v3. It supports the current
Create/Modify/Preserve exact-plan grammar and creates no progress cursor.

### 2. Expanded local refactor operations

**Design:**
[Expanded Local Refactor Operations Design](2026-08-23-expanded-local-refactor-operations-design.md)

This design owns Move/Rename, Replace, Delete, expanded Preserve, exact present
and absent accepted states, migration groups, output and recovery staging,
finalization, cleanup barriers, and successor inheritance of absent paths.

It extends the setup family through manifest/status v4. It does not add dynamic
progress state. Twelve approved material corrections were applied: four on
2026-08-23 and eight on 2026-08-24. Narrow re-review remains required before
implementation planning.

### 3. Durable progress cursor — deferred

**Design:**
[Durable Progress Cursor Design](2026-08-23-durable-progress-cursor-design.md)

This design owns stable new-program part/task structure, the append-only cursor,
status-bound recovery, successor cursor allocation, and concise delivered
progress output.

It extends the operations family through manifest/status v5 and traceability
v3. It does not change product authority or refactor recovery.

This design is deferred and is not part of the current implementation sequence.
Do not prepare or execute its implementation plan without a new explicit
decision to require exact task-level crash recovery.

## Cross-plan interface contract

The schema sequence is deliberate:

- Existing manifest/status v1 and v2 programs, including the current v1 receipt
  families used by v2 programs, remain on their exact existing routes.
- Plan 1 creates manifest/status v3 and the setup-derived authority family.
- Plan 2 creates manifest/status v4 and the expanded-operation, execution-result,
  and accepted-result-binding family.
- Plan 3 creates manifest/status v5, traceability v3, and the progress-cursor
  family.

Each family is selected by exact schema. Optional fields, field presence, or a
new reader never upgrade an older family. Programs created between releases
remain valid on the family under which they were created and are not rewritten
solely to acquire a later feature.

Output routing follows the same boundary: manifest/status v1 and v2 use their
existing schema-specific navigation routes, v3 and v4 use setup-bound increment
output without task progress, and v5 uses status-current cursor output. No
family falls through to another renderer.

Plan 2 reuses Plan 1's setup-decision semantics, grant, exact-plan checkpoint,
approval mode, and action-authorization derivation while versioning the bindings
that must carry v4 inventories and results. Plan 3 reuses the accepted lifecycle
and canonical successor decisions from Plans 1 and 2 but grants no authority.

The current public exact-plan preparation and materialization signatures remain
unchanged. Versioned parsing and validation stay behind their existing package
boundary unless an independently reviewed implementation plan proves that an
interface change is unavoidable. Plan 2 preserves the existing three-argument
future-write derivation and composes its static result with a pure v4 operation-
derived staging allocation before plan persistence. Plan 3 extends the
versioned required-managed-write set so cursor-capable exact plans and execution
baselines allocate the cursor ledger without changing those public signatures.

## Simplifications applied

The split intentionally removes these monolithic mechanisms:

1. **Separate setup-decision and activation-integrity records.** Plan 1 uses one
   durable setup-activation record because both facts become durable in the same
   transaction.
2. **An exact-plan-sized recap for every destructive operation.** Plan 2 allows
   setup-visible destructive semantics to proceed without a redundant pause,
   but unresolved material facts use the existing exact-plan checkpoint in
   every approval mode.
3. **Digest-only accepted results.** Plan 2 introduces one canonical present-or-
   absent execution result from fresh assessment onward and versions every
   affected consumer rather than fabricating a digest for a removed path.
4. **Two-event staging release intent/completion.** Once the legal release
   boundary is durable, the owner-bound inventory permits one idempotent cleanup
   completion record; pending cleanup blocks rollover, closure, delivery, and
   later actions.
5. **Mutable progress projections and task remapping.** Plan 3 uses stable
   semantic part/task structure and one cursor ledger. Structural changes are a
   program revision rather than automatic bookkeeping.
6. **A universal in-flight migration matrix.** Existing programs continue on
   their exact schema family. Unsupported in-place upgrades fail closed.

## Implementation and review gates

Each child design receives its own implementation plan, TDD cycle, bounded
review, verification evidence, and merge decision. Implementing or accepting
one child does not authorize the next child, Git publication, plugin
installation, cached-copy synchronization, or consuming-program repair.

Before writing each implementation plan, freshly verify branch, HEAD, worktree
status, relevant schema and fixture identities, predecessor completion, and the
child design's exact bytes. Stop on unexpected drift or overlap.

Review findings must be verified against current code. Address only material
correctness, security, privacy, compatibility, recoverability, or regression
risks whose benefit clearly exceeds churn. If none exist, the correct verdict
is: `No material improvements recommended.`

## Independent review status

The prior blanket review result is superseded for the expanded-operations
design. Its approved corrections now derive the material-plan checkpoint from
bound inventory comparison with explicit direct-versus-policy provenance;
separate product-operation results from managed lifecycle writes; provide valid
operation identity for all six operations; carry one present/absent execution
result through pre-acceptance review and every versioned consumer; pre-authorize
every staged byte path while retaining an output master across atomic
publication; reject symlinked ancestors; and make inherited path-state
projection cumulative. Three further corrections preserve the legacy future-
write resolver while deriving v4 staging allocation from the parsed operation
inventory, bind the exact in-flight execution prefix across blocked recovery,
and require final closure to account for the complete accepted-increment chain
and cumulative path-state projection. Narrow re-review of that revised child
remains required; no implementation plan may begin until it passes the gate
above. This status change makes no new readiness claim for either sibling
design.

## Repository and action boundary

These designs, their future implementation plans, source changes, tests, and
canonical documentation belong only in the `implementation-plugin` repository.
They authorize no source implementation, staging, commit, push, pull request,
merge, installation, publication, deployment, external action, or consuming-
program modification by themselves.
