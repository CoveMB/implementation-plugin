# Expanded Local Refactor Operations Design

**Status:** Split from the approved 2026-08-22 design. Twelve approved material
corrections were applied: four on 2026-08-23 and eight on 2026-08-24. Narrow
re-review is pending, so this design is not ready for implementation planning.

**Original source:**
`docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md`
at SHA-256 `b72b0d3c8a87b52302a163d98558ecf80ef557dfcf439b669a7ee6dc03e1905b`
(1,311 lines).

**Dependency:** The program-setup and activation design must be implemented
first. This design extends its setup-decision, exact-plan, baseline, grant, and
action-authorization boundaries; it does not replace them.

## Goal

Support Create, Modify, Move/Rename, Replace, Delete, and Preserve as typed
local-workspace operations with exact accepted results, crash-safe execution,
recoverable destructive inputs, and successor inheritance that can represent
both present and absent paths.

Operation type is not authority. Local refactoring remains inside the existing
plan-bound `modify-workspace` boundary. External data migration, remote state,
credentials, permissions, branches or worktrees, deployment, publication, and
user-owned material remain consequential actions requiring separate authority.

## Scope reduction from the original design

The first version deliberately supports only regular, non-symlink files and
disjoint source and destination sets. It rejects directories as owned
artifacts, symlinks at either a leaf or any ancestor below the workspace root,
hard links, special files, swaps, rename cycles, case-equivalent collisions,
and replacements that retain a source path as a destination.

The original design required complete destructive path accounting during every
setup approval. This split uses a narrower rule:

- If every destructive source, destination, lineage, disposition, discard
  rationale, and gate is known and visible in the setup recap, later exact
  planning may refine identities and execution order without another material
  decision.
- If any such fact is unresolved at setup, the exact plan must present it for a
  direct material plan decision. `approval:pre-approve` and
  `approval:full-increment` cannot skip that decision.

The checkpoint is caused by unresolved material semantics, not by the operation
name. This avoids both hidden destructive authority and an exact-plan-sized
setup recap.

The checkpoint reason is derived, never selected by a caller. For v4 proposals,
setup preparation canonically projects every setup-visible destructive source,
destination, lineage, disposition, discard rationale, and gate into an ordered
setup destructive inventory. The setup decision binds that inventory and its
digest. Exact-plan preparation produces a second canonical inventory over the
same semantic fields. Planning-only identities, verification observations, and
execution order are excluded from this comparison.

Each exact-plan entry that claims prior visibility identifies one setup entry
and reproduces its canonical semantic projection. Preparation mechanically
computes an ordered difference containing every added, omitted, or changed
semantic fact. An empty difference sets `comparison_reason` to
`routine-standard`; a non-empty difference sets it to
`unresolved-material-fact`. Missing inventories, mismatched digests, duplicate
matches, unmatched setup claims, or a caller-supplied reason are invalid rather
than grounds for choosing the routine path.

The checkpoint reuses the existing exact-plan checkpoint transaction but has
two explicit provenance routes. `checkpoint_route` is derived from the
inventory difference and the persisted approval-mode policy:

- A non-empty difference always sets `checkpoint_route` to
  `direct-plan-decision-required`. An empty difference also uses that route
  when the approval mode retains its routine plan pause. Exact-plan preparation
  creates or adopts the plan, persists the two inventory bindings and their
  difference, and writes `awaiting-plan-approval` status last. The exact
  submitted prompt produces a direct plan-approval receipt that binds its prompt
  digest, decision and event identifiers, `comparison_reason`,
  `checkpoint_route`, both inventory digests, the difference digest, the setup
  decision, grant, exact plan, prior status, and workspace.
- An empty difference in a no-pause mode sets `checkpoint_route` to
  `approval-mode-routine`.
  Preparation creates or adopts the plan and persists the same comparison, but
  it creates no user-approval event and does not claim a direct decision.
  Materialization instead persists a separately typed approval-mode derivation
  bound to the setup decision, grant, exact approval mode, `comparison_reason`,
  `checkpoint_route`, empty difference, plan, prior status, and workspace.

`approval:pre-approve`, `approval:full-increment`, and any other no-pause policy
cannot manufacture the direct receipt required for a non-empty difference. The
expanded action authorization binds the three inventory digests and exactly one
valid provenance record: either the direct plan-approval receipt or the typed
approval-mode derivation. Only then may materialization persist the execution
baseline, planned product operations and migration groups, action authorization,
and `authorized` status last. Every prefix, including a policy-derived
preparation without an intermediate waiting status, is deterministic and
freshly discoverable.

## Schema family

Expanded-operation proposals use `implementation-program-manifest/v4` and
`implementation-program-status/v4`. They extend the setup design's v3 family
with canonical setup/exact-plan destructive inventories, new setup-decision,
plan-approval, and approval-mode-derivation versions that bind their comparison,
explicit v2 exact-file-map and execution-baseline forms, execution-result v2,
new versions of every
consumer whose validation or meaning changes, migration-event, execution-result,
and staging-owner ledgers, release-completion records, and a chain-bearing
action-authorization version that binds the planned migration prefix and pre-
authorized internal staging allocation. Manifest/status v3 programs remain
valid Create/Modify/Preserve programs and do not acquire v4 semantics through
optional fields.

## Typed operations

- **Create:** introduce a path absent at baseline.
- **Modify:** change an existing regular file at the same path.
- **Move/Rename:** move one file to one distinct destination while preserving
  lineage.
- **Replace:** supersede one or more sources with one or more distinct owning
  destinations.
- **Delete:** remove a file after recording whether its content was migrated,
  obsolete, or intentionally discarded.
- **Preserve:** prove a protected file retains its bound content-and-mode
  identity.

Existing Create/Modify/Preserve schemas keep their current meaning. Expanded
operations use new explicit file-map and execution-baseline versions. Unused
operations own no paths and require no placeholder records.

## Exact execution and accepted-result model

`ExactFileMapV2` separates two inventories that the legacy file map combines:

- the ordered product-operation inventory contains only product paths owned by
  Create, Modify, Move/Rename, Replace, Delete, or Preserve; and
- the ordered managed-lifecycle-write inventory contains control-plane files,
  ledgers, descriptors, release records, and internal staged byte allocations
  with their exact Create or Modify dispositions.

The two inventories are disjoint. The existing three-argument
`required_future_lifecycle_writes(...)` contract continues to derive only the
static manifest- and traceability-owned requirements it can derive without an
exact plan. For v4 only, exact-plan preparation composes those requirements
with a separate pure derivation over the already parsed product-operation and
migration-group allocation. That derivation returns every deterministic staged
byte requirement and no caller-selected path. Validation evaluates the complete
composed managed-lifecycle-write inventory before any plan byte is persisted.
Execution assessment, review, acceptance, inheritance, and closure consume only
the product-operation inventory. Legacy exact-file maps and the legacy three-
argument derivation retain their existing shape, meaning, and route.

Expanded operations use one canonical versioned result representation from
fresh execution assessment through review, diff disposition, acceptance,
rollover, and closure rather than assuming every result path still exists:

```text
ImplementationExecutionResultV2
  result_id
  program_id
  program_revision
  increment_id
  ordered_path_states: [ExecutionPathStateV2]

ExecutionPathStateV2
  path
  final_state: present | absent
  operation_id
  operation_type: create | modify | move-rename | replace | delete | preserve
  migration_group_id                                               # Move/Rename, Replace, Delete only
  lineage
  regular_file_identity: kind, byte_length, sha256, supported_mode  # present only
  absence_reason                                                   # absent only
```

`final_state: present` requires the complete regular-file identity and forbids
an absence reason. `final_state: absent` requires a bounded reason such as
`moved-away`, `replaced`, or `deleted` and forbids a file digest or mode. Fresh
assessment must include exactly every path in the approved product-operation
inventory, including absent sources and Preserve paths, and must exclude every
managed lifecycle or staging path. Every state binds one stable operation
identifier. `migration_group_id` is required for Move/Rename, Replace, and
Delete and forbidden for Create, Modify, and Preserve; omission, fabrication,
or cross-operation reuse is invalid.

Accepted state is operation- and path-role-specific. Create, Modify, and
Preserve paths must be `present`. Move/Rename and Replace sources must be
`absent` while their destinations must be `present`. Delete paths must be
`absent`. Fresh assessment derives the complete expected accepted-state map
from the bound product-operation inventory and, for Move/Rename, Replace, and
Delete, requires exact agreement with the migration-group record's expected
accepted path states. Every result path must also match its expected operation,
migration-group membership, lineage, identity or bounded absence reason, and
order. A missing, extra, reordered, role-mismatched, or state-mismatched entry
is divergent and cannot reach review, acceptance, inheritance, or closure.

Before status enters `reviewing`, fresh execution assessment appends one
immutable `implementation-execution-result/v2` record to the manifest-owned
execution-result ledger and writes status last with an opaque binding containing
its schema, ledger path, record identifier, and digest. Execution-transition,
review-preparation, raw and normalized review reports, review evidence and
packet, and review-remediation records bind that exact result. A remediation
that changes any owned product path requires a new fresh assessment, a new
immutable result record, and renewed affected review before status can return to
`reviewing`; prior result records remain available for validation.

A crash after a result append but before its status binding is a recoverable
prefix only when fresh assessment reproduces that exact record and the prior
status permits the same transition. Multiple candidate records, a mismatched
record, or a status binding without its exact ledger record is divergent.

Diff disposition accepts the final reviewed execution-result record and digest;
acceptance does not re-encode it as a second path-state shape. New-version
continuation projection and command, rollover record and binding, inherited
workspace, closure preparation, command, and evidence all carry an opaque
versioned binding to that same accepted record and digest. A record that merely
carries this binding need not duplicate `ordered_path_states`.

Final closure additionally validates the complete canonical rollover chain. It
enumerates every accepted increment in order and binds each increment's accepted
execution result, diff decision, review packet, and any family-required handoff
addendum. Later-invalidation checks cover every accepted increment, and closure
binds the final cumulative `inherited_path_states` projection and digest. Only a
program with no completed rollover may close with a singleton accepted-increment
inventory. A missing, reordered, duplicated, unbound, or mismatched historical
result, decision, review artifact, or cumulative projection is divergent.

Successor preparation:

- validates every inherited `present` path against its exact identity;
- validates every inherited `absent` path remains absent;
- creates execution `path_baselines` only for present files;
- places all present and absent states in the new execution-baseline
  `inherited_path_states` field while creating `path_baselines` only for
  present files, so absent states remain lineage/tombstone evidence rather than
  fabricated baselines; and
- rejects duplicate, contradictory, unowned, or cross-operation/group states
  before materialization.

`inherited_path_states` is cumulative. Rollover starts from the prior cumulative
path-state projection, replaces only paths owned by the newly accepted
increment with their final states, and retains every untouched present state and
tombstone. It never rebuilds inheritance from only the newest result. The
rollover and inherited-workspace bindings own the complete projected inventory
and digest.

Every consumer whose validation or meaning changes uses a new schema version.
This includes execution assessment and transition; review preparation, raw and
normalized reports, evidence, packets, and remediation; diff disposition;
accepted-result binding; continuation; rollover; inherited workspace and
successor baseline; blocked context and resolution when they bind the current
result; and closure preparation, command, and evidence. Every v4 blocked context
and resolution uses its new version even before an execution result exists,
because it also binds the status-current execution prefix described below. A
carrier whose only role is an opaque versioned record binding may retain its
shape if its existing schema contract already permits that binding without
reinterpretation.

Current digest-only product deltas and all v1 consumers retain their exact
meaning and validation. A chain may use exactly one result family; mixed v1/v2
inheritance is rejected before persistence.

## Migration groups

Every v2 product operation has one stable operation identifier. Every
Move/Rename, Replace, or Delete additionally belongs to one acyclic migration
group. Create, Modify, and Preserve do not fabricate migration groups. The
exact migration group records:

- stable identifier and operation type;
- source and destination paths;
- baseline file identities;
- expected accepted path states;
- lineage and useful-content destination for every source;
- intentional discard and its concrete rationale;
- affected imports, links, metadata, configuration, tests, documentation, and
  other dependents;
- source-defined gates;
- ordered finalization steps;
- verification observations; and
- exact retry and recovery classifications.

Each path has one owning operation per increment. Sources, destinations,
Preserve paths, protected control-plane files, Git metadata, external paths,
and unrelated user-work baselines must be mutually non-overlapping. Same-path
content changes remain Modify operations.

A newly discovered destructive target, changed lineage or disposition, new
discard, changed gate, path outside an approved bounded class, ownership
change, or new material risk is decision drift. It requires the direct material
plan decision described above or, when it contradicts an already approved
immutable program decision, stops at `program-revision-workflow-required`.

## File identity and platform boundary

Expanded file identity includes regular-file kind, byte length, content digest,
and the supported executable or mode state. Restrictive staging permissions are
never accepted as the final mode. Move/Rename preserves mode unless an approved
exact plan binds a supported change. Expanded Preserve checks content and mode;
legacy Preserve remains byte-only under its existing schema.

Every product and staged path is resolved beneath its bound root without
following symlinks. Each ancestor from the workspace or staging root through
the leaf's parent must already exist as a real directory, remain inside that
root, and retain its bound filesystem identity through the final pre-mutation
check. The leaf is opened, compared, created, replaced, or removed with
no-follow semantics appropriate to its expected present or absent state.
Missing parents, directory creation, a symlinked ancestor or leaf, or resolution
outside the bound root is unsupported and stops before product mutation or
cleanup.

If the platform cannot create, preserve, replace, or verify the required
regular-file and permission contracts, preparation stops as unsupported.

## Execution state machine

Each product operation advances through four durable states. Operations that
share a migration group advance under one group-bound ordered state:

1. **Planned:** exact plan, baseline, gates, accepted states, order, and recovery
   contract are durable before product mutation.
2. **Prepared:** every output identity and every pre-mutation recovery copy is
   durable in distinct owner-bound same-filesystem staging inventories; product
   paths still match baseline.
3. **Applied:** fresh inspection matches one complete or explicitly recognized
   ordered result prefix.
4. **Verified:** named checks, dependencies, Preserve obligations, and accepted
   path states reconcile.

Exact-plan materialization persists all planned product operations and migration
groups before the expanded action authorization and writes `authorized` status
last. A caller cannot add or change an operation or group after authorization.

The new manifest allocates the migration-event ledger, execution-result ledger,
staging-namespace root, staging descriptor, staging-owner/index records, and
release-completion records. The existing
`required_future_lifecycle_writes(...)` boundary derives the exact static
managed paths for the current increment. After parsing the v2 operation and
migration-group inventory, the v4-only pure derivation adds the internal staged
byte allocations below. Exact-plan validation requires the composed set under
the correct dispositions in the v2 managed-lifecycle-write inventory before
any plan byte, baseline, planned operation/group, provenance record, or action
authorization is persisted. The staged allocation is an input to validation,
not a later mutable extension. None of these paths may appear in the product-
operation inventory.

Exact-plan preparation derives one immutable private staging namespace for the
increment and deterministic distinct output and recovery byte paths for every
planned operation item. The paths derive only from bound program, revision,
increment, operation, optional migration group, item, and role identifiers. The
exact plan and its applicable provenance record bind the ordered allocation,
its owners, and its digest. Before action authorization, materialization
persists or adopts the same allocation in the staging descriptor/index, and
action authorization binds it again. These are internal ephemeral write
allocations, not product exact-file-map entries. No caller may add, rename, or
broaden a staged byte path after provenance binding or action authorization.

## Output and recovery staging

Before removing a source or replacing an existing destination, preparation
copies its exact pre-mutation bytes into private owner-bound recovery staging.
The owner record binds the operation, optional migration group, plan, baseline,
original path and role, content identity, and original mode. Recovery bytes are
not rollback authority and are never restored automatically. They remain
excluded from product deltas, commits, publication, and normal output.

Outputs not knowable during planning are fully constructed as retained masters
in separate private output staging before product mutation. Prepared records
bind their exact bytes, destinations, and final modes. Each destination that
requires an atomic or exclusive publication step also receives a distinct,
pre-authorized publication-candidate path on the destination filesystem. The
candidate is reproduced or adopted from the retained master immediately before
publication. Consuming a publication candidate never consumes the retained
master.

Preparation may write only the exact pre-authorized staged byte path for that
owner and role. Fresh discovery and cleanup resolve targets from the immutable
authorization-bound allocation, never from a directory scan or a later mutable
inventory. A missing allocation, foreign entry, changed owner/path binding, or
attempt to target any unallocated byte is divergent and cleanup removes
nothing.

Cleanup is simpler than the original two-event intent/completion protocol:

- output staging becomes eligible for removal only after the applied event is
  durable;
- pre-mutation recovery becomes eligible only after diff disposition and
  `accepted` status are durable;
- cleanup removes only the already owner-bound inventory, verifies absence,
  then appends or adopts one `staging-released` record;
- after the legal release boundary, either present bytes or verified absence
  without the completion record is an idempotently recoverable prefix;
- before the applied event, an absent publication candidate is a known prefix
  only when its retained master remains exact and the destination matches the
  candidate's exact final identity at the bound ordered step; and
- absence of a retained output master or recovery copy before its legal release
  boundary, foreign bytes, broadened permissions, or a completion record with
  remaining bytes is divergent.

No release-intent record is needed because the legal boundary and owner-bound
inventory already determine exactly what may be removed. Cleanup never targets
product or user files.

After recovery staging reaches its legal release boundary, pending cleanup is
the only discoverable next action until `staging-released` is durable. Delivery,
accept-continue rollover, final-increment closure, later-action authority, and
any progress output remain blocked. Fresh discovery resumes exact removal or
adopts verified absence, appends the completion record, and only then exposes
the next lifecycle action.

## Finalization and concurrency

Finalization holds one manifest-owned advisory workspace lease that serializes
cooperating lifecycle writers. The supported contract also requires a quiescent
workspace during the bounded finalization window. The design does not claim an
atomic compare-and-swap against editors, Git commands, or other non-cooperating
writers.

Absent destinations use exclusive no-overwrite publication. Expected existing
destinations are freshly compared against their bound identity immediately
before atomic replacement while the lease is held. Destinations reach and
verify their final content and mode before any source-removal step. Any detected
drift stops without product mutation. An uncooperative race after the final
check remains an explicit unsupported boundary.

Atomic or exclusive publication may consume only its allocated publication
candidate. Fresh discovery recognizes candidate-consumed/destination-exact with
an exact retained master as an applied prefix; it never treats loss of the
retained master or recovery copy as publication progress.

Fresh discovery classifies each operation or migration group as baseline,
prepared, known exact prefix, exact applied result, verified, or divergent. It
adopts only an exact owner-bound prefix. It never resets, cleans, stashes,
overwrites, guesses, or automatically restores recovery bytes.

Before a v4 program enters blocked state from an execution-capable state, the
blocked transaction derives one canonical execution-prefix binding. Its bound
payload contains the authorized staging-allocation digest; exact migration-
event and execution-result ledger prefixes; staging descriptor, owner/index,
and release-completion prefixes; and the present identity or expected absence
of every allocated staged byte. The blocked context binds that payload and its
digest before writing blocked status last. Fresh blocked discovery and block
resolution require exact equality with the bound prefix and reject every
post-block suffix, missing record or byte, changed identity, or broadened
allocation. This adds one snapshot binding to the existing blocked transaction;
it does not create another operation state or authorize restoration.

## Gates and authority

Source-defined gates from the setup design bind affected product operations and
migration groups and prevent the first operation or group event, or lifecycle
transition beyond their declared trigger, until the exact gate decision
validates.

Move/Rename, Replace, or Delete does not request generic destructive authority
solely because of its name. The complete plan-bound action authorization still
binds the setup or material plan decision, grant, approval mode, exact plan,
baseline, planned product operations, migration groups, and required gates.
User-work overlap and every consequential or external effect remain outside
this local-operation authority.

## Compatibility

Compatibility is versioned and no-rewrite:

- Existing exact-file maps, baselines, digest-only accepted deltas,
  execution transitions, review artifacts, diff dispositions, continuation
  records, rollover records, blocked-recovery artifacts, closure artifacts, and
  frozen fixtures retain their current meaning.
- Expanded file maps, execution baselines and results, execution transitions,
  setup-destructive inventories, setup decisions, plan approvals, action
  authorizations, review artifacts and remediation, diff dispositions,
  continuation projections and commands, rollover records and bindings,
  inherited workspaces, blocked-recovery artifacts whose result binding changes,
  closure artifacts, migration events, and staging owners use the new versions
  specified above.
- Existing public exact-plan preparation and materialization signatures remain
  unchanged; schema-specific parsing occurs behind the current boundary.
- The legacy three-argument `required_future_lifecycle_writes(...)` contract and
  its outputs remain unchanged. Only the v4 candidate builder composes its
  result with the pure operation-derived staged-byte allocation before v2 map
  validation.
- v2 parsers keep product-operation and managed-lifecycle-write inventories
  distinct. No consumer may infer product results from the managed-write
  inventory or reinterpret a legacy combined map as the v2 split form.
- Manifest, discovery, status validation, recovery, continuation, rollover, and
  closure dispatch on exact supported manifest/status schema pairs. v4 selects
  only the expanded family; v3 and every supported legacy pair stay on their
  existing routes. A single newest-version constant, an older-versus-current
  branch, or optional-field detection must not route v1, v2, or v3 artifacts
  through v4 semantics.
- A legacy program cannot request expanded operations in place. It continues
  under Create/Modify/Preserve or stops at
  `setup-approval-required-for-expanded-operations` and requires a separately
  authorized replacement proposal.
- New accepted states cannot be downgraded to digest-only v1 records or mixed
  with them in one continuation chain.

## Test contract

Implementation must add causal writer-to-fresh-discovery tests for:

- parsing, ownership, baselines, accepted states, and verification for all six
  operation types, including rejection of every wrong present/absent state,
  absence reason, lineage, operation binding, migration-group binding, or
  expected-state-map mismatch;
- present and absent execution states flowing from fresh assessment through
  execution transition, initial and follow-up review, remediation, diff
  disposition, acceptance, rollover, inherited workspace, blocked recovery,
  successor baseline creation, and closure;
- a three-increment chain whose first increment creates tombstones, whose second
  increment owns unrelated paths, and whose third increment still validates all
  untouched present states and tombstones from the first; plus replacement only
  when a later increment actually owns the same path; the chain then closes only
  after closure binds all three accepted results, decisions, review artifacts,
  later-invalidation checks, and the final cumulative path-state projection;
- setup-visible destructive semantics avoiding a redundant checkpoint, and an
  unresolved material destructive fact requiring a direct exact-plan decision
  even in no-pause approval modes;
- mechanical setup/exact-plan destructive-inventory comparison, derived
  `comparison_reason` values `routine-standard` and
  `unresolved-material-fact`, derived `checkpoint_route` values, rejection of a
  caller-selected reason or route or missing/tampered inventory/difference binding,
  prompt-bound direct decisions in every required mode, policy-derived routine
  provenance only for empty differences in no-pause modes, rejection of either
  provenance on the wrong route, decision-to-baseline/planned-operation/group/
  action/status ordering, failure injection after every write, and rejection of
  a missing or mismatched material decision;
- separation of product-operation results from every control-plane, ledger,
  release, and staged-byte allocation, plus stable operation identifiers for all
  six operation types and migration-group identifiers only where permitted;
- path overlap, cycle, case collision, leaf or ancestor symlink, hard-link,
  directory, missing-parent, special-file, protected-path, user-work, external-
  resolution, and unsupported-platform rejection;
- content-and-mode identities, expanded Preserve, and legacy byte-only Preserve;
- planned, prepared, every supported finalization prefix, applied, verified,
  and divergent recovery after fresh discovery;
- failure injection after each recovery copy, staged output, execution-result
  append, reviewing/remediation status write, durable operation or group event,
  destination publication-candidate creation and consumption, destination
  write, source removal, diff acceptance, and staging cleanup boundary,
  including adoption of candidate-consumed/destination-exact only while the
  retained master is exact;
- blocked entry from prepared, every known applied prefix, result-appended-before-
  status, reviewing, and remediating states; exact binding of each status-current
  execution prefix; and rejection of every post-block ledger suffix, staged-byte
  change, missing prefix item, or broadened allocation before resolution;
- pending recovery cleanup blocking delivery, accept-continue rollover,
  closure, progress output, and later actions through every partial removal
  prefix;
- rejection before authorization when the exact plan omits any allocated
  migration ledger, execution-result ledger, staging owner/index, staged byte
  path, or release record, and rejection when later recovery or cleanup mutates
  or broadens that allocation;
- unchanged legacy three-argument future-write results, deterministic v4
  operation-derived staging requirements, and validation of their complete
  composed managed-write set before any plan byte is persisted;
- recovery bytes remaining private and available after failed verification,
  review, or diff disposition, without automatic rollback;
- cooperating-writer lease serialization and detected drift immediately before
  replacement, while documenting the non-cooperating-writer claim limit;
- proof that exact manifest/status routing preserves v1 result consumers and v3
  setup programs while selecting v4 only for expanded programs; and
- proof that local Delete does not create generic consequential authority.

The full relevant deterministic suite runs once after the coherent
implementation batch. Local tests do not prove behavior in an unexercised
filesystem, operating system, or external system.

## Documentation and repository scope

Implementation updates the skill front door and canonical operation reference
for all six operation types, accepted present/absent states, the material-plan
checkpoint rule, recovery retention, platform limitations, and the cooperating-
writer claim boundary. Normative recovery rules have one canonical owner.

Design, implementation, tests, and source documentation belong only in this
repository. Installation, cached-copy synchronization, consuming-program
rewrites, and external migrations remain separately authorized.

## Success criteria

This design is complete when all six local operations can be planned,
authorized, executed, recovered, reviewed, accepted, and inherited by a
successor; deleted and moved-away paths remain representable without fabricated
digests from execution assessment onward; product results cannot absorb managed
lifecycle or staging paths; every operation has valid non-fabricated identity;
destructive plan decisions and their direct or policy-derived provenance are
mechanically derived from the approved setup-visible facts; every staged byte
path is owner-bound before authorization; atomic publication retains a durable
output master through the applied event; cumulative present states and
tombstones survive unrelated rollovers; symlinked ancestors cannot escape the
workspace boundary; blocked recovery cannot adopt execution progress written
after the blocked boundary; closure accounts for every accepted increment and
the final cumulative path-state projection; and v1 record consumers and every
supported legacy program retain their existing behavior without record
rewrites.

## Non-goals

This design does not add directory moves, symlink operations, hard-link
preservation, graph-aware swaps, arbitrary rollback, general program revision,
dynamic progress projections, external migration, Git operations, publication,
deployment, plugin installation, or consuming-program repair.
