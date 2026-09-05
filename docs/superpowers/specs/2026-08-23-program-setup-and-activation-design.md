# Program Setup and Activation Design

**Status:** Split from the approved 2026-08-22 design; material corrections from
the 2026-08-24 repository-contract review, independent narrow re-review, and
2026-08-26 recovery, response-semantics, publication-snapshot/freshness, recap-
binding, and baseline-regression reviews and the 2026-08-27 creation-authority,
publication-recovery, and successor-gate materiality/complexity reviews are
applied; ready for its separate implementation plan subject to the isolated
legacy-activation baseline gate below.

**Original source:**
`docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md`
at SHA-256 `b72b0d3c8a87b52302a163d98558ecf80ef557dfcf439b669a7ee6dc03e1905b`
(1,311 lines).

## Goal

Replace machine-payload setup approval with one readable program decision,
separate activation from first-increment execution, and preserve the existing
typed authority, no-overwrite, status-last, and legacy compatibility
boundaries.

This design is independently implementable. It supports the current
Create/Modify/Preserve exact-plan grammar. Expanded Move/Rename, Replace, and
Delete operations are owned by the separate expanded-operations design.
Durable part/task navigation is owned by the separate progress-cursor design.

## User-visible flow

1. A current direct new-program request supplies explicit create intent, the
   exact authoritative source-plan path, and creation-only control-plane
   authority. That authority permits only owner-bound proposal publication; it
   grants no setup approval, product change, Git action, installation, or
   external action.
2. Read-only preparation builds and validates a complete program proposal in
   memory.
3. The owner-bound publisher persists the proposal under that creation-only
   authority with `manifest.json` last.
4. The user sees one plain-language recap and answers one setup question.
5. Activation persists that decision. It ends at
   `active` / `awaiting-first-increment` without execution authority when no
   non-reused source gate is due; otherwise it first pauses at the current gate
   recap and reaches that state only after the separate gate decision.
6. A semantic handoff starts a fresh task.
7. The fresh task revalidates state, persists the first-increment grant, and
   follows the selected exact-plan approval mode before any product change.

Source-defined gate questions remain separate and appear only at their declared
supported triggers. The setup answer satisfies a source gate only when the gate
and setup checkpoint satisfy the exact semantic-reuse rule below.

During setup approval, source-gate decisions, and the semantic first-start
handoff, the user never copies JSON, hashes, schema names, record identifiers,
or exact prompt bytes. The existing schema-specific exact-plan prompt required
by `approval:standard` remains outside that setup-flow promise.

## Authority boundaries

The following decisions remain distinct:

1. **Creation-only proposal publication** permits the exact owner-bound
   control-plane proposal to be published from the current direct create intent
   and exact source path. It approves neither the proposal semantics nor any
   product, Git, installation, or external action.
2. **Setup approval** approves the visible program semantics, workspace,
   increment order, requirement, acceptance, and operation allocation, approval
   mode, gates, protections, exclusions, and material risks.
3. **Start-increment intent** asks to begin the status-current increment after
   fresh discovery. It is not product-change authority.
4. **Source-gate decisions** satisfy source-required checkpoints at their
   declared lifecycle boundaries.
5. **Increment action authorization** binds the current grant, exact plan,
   execution baseline, approval mode, any required plan approval, and every
   applicable source-gate satisfaction.
6. **Consequential actions** such as commit, push, external or product
   publication, deployment, external migration, permission change, and provider
   mutation remain separately authorized.

Creation intent cannot satisfy setup approval, and no one input may create an
increment action authorization by itself.

## Setup preparation and recap

Preparation remains read-only with respect to product files. It inspects the
authoritative source, repository instructions, relevant implementation and
tests, workspace and branch identity, user work, supported lifecycle state,
and current Create/Modify/Preserve capability.

The visible recap must show:

- program name, identifier, revision, and intended outcome;
- readable source titles and locations;
- selected workspace and branch;
- a plain summary of staged, modified, untracked, conflicted, and protected
  work;
- ordered increments and dependencies;
- for every increment, the allocated requirements, acceptance meaning,
  intended outcome, and expected checks;
- the approval mode in plain language, including whether it omits the routine
  exact-plan question, its remaining interruption conditions, and the retained
  diff-disposition, continuation, and consequential-action boundaries;
- every source-defined gate, including its readable authoritative source title
  and exact location, question, unconditional affirmative meaning, the no-write
  effect of every other response, timing, protected subject, and whether the
  setup answer will satisfy it through exact checkpoint reuse;
- the supported local-operation envelope, including concrete Create, Modify,
  and Preserve paths or deterministic bounded path classes with normalized
  repository-relative roots or finite path sets, explicit inclusions and
  exclusions, the increment or explicitly bounded set of increments allocated
  to each path or class, and current ownership, protection, user-work,
  file-kind, link, mode, and collision observations for every concrete path;
- protected material, exclusions, external boundaries, and material risks;
- what approval will persist and what it will not authorize; and
- the first increment available after activation.

Approval binds only decision facts shown in that recap. Internal evidence may
retain exact bytes, identifiers, and digests, but hidden semantic facts cannot
be claimed as user-approved.

Manifest v3 embeds one required closed `setup_semantics` value as the canonical
proposal owner of those approval-bound semantic facts. It binds the existing
manifest-owned program, source, traceability, workspace, and source-gate values
by exact identity and digest, and directly owns the operation envelope and
increment allocations, recap-visible workspace and concrete-path observation
facts, protection and exclusion rules, external boundaries, material risks,
and first-increment fact. Its canonical JSON digest is the semantic decision
identity. The recap is a deterministic projection of that value after fresh
validation of its observation bindings, and the presented integrity identity
also binds the exact fresh evidence used for that validation. This adds no
separate proposal artifact or mutable recap ledger.

The recap checkpoint is a versioned canonical value that binds the renderer
schema and version, semantic decision identity, presented integrity identity,
and SHA-256 digest of the exact UTF-8 recap bytes presented to the user. Its
identity and digest are derived before the typed decision. A renderer or recap-
byte change therefore invalidates an earlier decision even when the underlying
semantic facts are unchanged. This checkpoint remains an embedded binding; it
does not add a durable recap artifact or ledger.

Exact planning for the status-current increment must refine, never broaden, the
portion of the recap-visible operation scope allocated to that increment. A
path outside a bounded class, a path or class allocated only to another
increment, symlink, hard link, unsupported file kind, unexpected collision,
protected-path overlap, user-work overlap, changed ownership, or new material
risk stops before action authorization. A newly resolved path inside a bounded
class may proceed without renewed setup approval only when it inherits that
class's increment allocation and every visible ownership, protection, gate,
exclusion, and risk fact remains unchanged. Allocation stops at increment
granularity; it does not require task-level mapping or premature exact paths for
distant increments. A path or class may be shared by multiple increments only
when the recap says so.

The recap ends with:

> Approve this program setup?

## Conversational decision adapter

Only the current top-level message with conversation role `user` may answer
the current recap. A clear affirmative answer is sufficient. Ambiguous,
conditional, quoted, retrieved, tool-produced, assistant-produced, stale, or
replayed content is not approval.

The trusted controller produces a typed `setup-approval-decision` value bound
to the recap checkpoint, semantic decision identity, presented integrity
identity, decision, and provenance class `direct-user-message`. Activation
accepts only that typed value at its package boundary; it rejects raw text,
caller-supplied Booleans, malformed values, and stale bindings.

The setup-activation record binds the exact typed setup-adapter value identity
and digest in addition to those checkpoint bindings. This gives setup approval
the same adapter-to-durable-record traceability required for a separately
presented source-gate decision without introducing another record.

A correctly bound typed negative is a valid conversational outcome but is not
activation authority. It starts no activation transaction, writes no setup
record, source-gate decision, receipt, or status, and leaves the published
proposal byte-identical. Fresh discovery therefore presents the same setup
recap. This design adds no durable setup-negative or cancellation record.

Repository code can validate the typed value and its bindings. It cannot prove
human identity, comprehension, message origin, or an unforgeable controller
attestation. Documentation and tests must preserve that claim limit.

## Schema family

New proposals use `implementation-program-manifest/v3` and
`implementation-program-status/v3`. Exact manifest schema dispatch selects this
closed record family:

| Artifact | Exact schema | Manifest ownership |
| --- | --- | --- |
| setup-activation decision | `setup-activation-decision/v1` | allocated single-record logical role `setup_activation_decision`; absent in the proposal and created or adopted during activation |
| program, workspace-selection, exact-plan, diff-disposition, and closure approval receipts | `implementation-approval/v2` | existing append-only `approvals` role |
| first-start or successor increment grant | `implementation-increment-grant/v2` | existing append-only `increment_grants` role |
| current-increment grant binding | `implementation-current-increment-authority-binding/v2` | embedded in status v3 |
| every v3 action authorization, including plan, rollover, recovery, and closure actions | `implementation-action-authorization/v2` | existing append-only `action_authorizations` role |
| setup activation status binding | `implementation-setup-activation-status-binding/v1` | embedded in status v3 |
| source-gate definition | `source-gate-definition/v1` | immutable `source_gate_definitions` collection embedded in manifest v3 and present at proposal publication |
| source-gate decision | `source-gate-decision/v1` | new append-only `source_gate_decisions` logical role, published empty |
| source-gate satisfaction | `source-gate-satisfaction/v1` | embedded in each protected v3 receipt, authorization, event, or status |

The manifest-owned source-gate definition collection is the canonical
structured owner of every proposed gate. Definitions sort by stable gate ID.
Each definition binds the exact authoritative source identity and digest,
readable source locator, any applicable traceability source-unit identities and
digests, question, protected subject, trigger, the exact response semantic
`unconditional-affirmative-satisfaction`, and setup-reuse declaration. The
manifest digest and semantic decision identity bind the complete collection.
Fresh discovery reads that exact collection and never reconstructs gate
authority from recap prose or other free text.

`implementation-approval/v2` and `implementation-action-authorization/v2`
carry their existing type or action discriminators plus the exact causal chain
applicable to that discriminator and lifecycle boundary. Program- and
workspace-selection approvals bind the setup-activation record and applicable
pre-activation gate satisfactions, and require the explicit absence of the not-
yet-created grant, plan, and baseline. Later approval and action-authorization
types bind the setup, grant, plan/baseline, and applicable source-gate prefix
that must exist at their boundary. No v2 record contains a placeholder or
forward reference to authority created by a later transition. An
`implementation-increment-grant/v2` carries an exact `grant_kind`.
`first-increment-start` binds the typed start intent, waiting status, status-
current first increment, and its brief path/digest. `successor-rollover` instead
binds the prior accepted status and increment as predecessor context, the exact
successor increment and brief path/digest, typed continuation domain and
checkpoint, and already-durable rollover action authorization ID and digest.
Both grant kinds also bind the exact setup-activation record ID and digest,
approval mode, and controlling workspace-selection approval receipt ID and
digest. The v2 current-increment authority binding binds the exact grant ID and
digest, and the resulting status-current increment and brief must match the
grant's protected increment and brief. The manifest storage contract allocates
the absent setup record for an activation-writer `Create` and publishes the
source-gate ledger empty for an activation-writer `Modify`. After activation,
the schema-specific
`required_future_lifecycle_writes(...)` route requires the setup record as
`Preserve` and the source-gate ledger as `Modify` in every applicable exact
plan. Proposal-mode v3 validation resolves the setup record's allocated parent
without requiring the file and rejects a premature record; activation-prefix
and approved-mode validation require the exact manifest-owned record.

The `before-increment-start` gate chain uses the authority appropriate to the
grant kind. A `first-increment-start` chain binds the typed
`increment-start-intent`. A `successor-rollover` chain instead binds the exact
typed continuation checkpoint and rollover authority, including its immediate
or accepted-state continuation domain. It never fabricates a first-start intent
for a successor. The applicable decision prefix and satisfaction are consumed
by the corresponding v2 grant and status-current authority binding.

Status v3 has these initial transitions:

| Durable boundary | Program / increment state | Sequence | Transition authority |
| --- | --- | --- | --- |
| published proposal | `awaiting-program-approval` / `not-started` | `0` | none; proposal only |
| completed setup activation | `active` / `awaiting-first-increment` | `1` | exact setup-activation record and derived v2 approval receipts through `implementation-setup-activation-status-binding/v1`; never an action authorization |
| completed first-increment start | `active` / `preparing` | `2` | exact `implementation-increment-grant/v2` with `grant_kind: first-increment-start` |

Pre-activation gate decisions leave the sequence-zero proposal status in place;
pre-start gate decisions leave the sequence-one waiting status in place. Later
v3 lifecycle transitions increment the sequence under their existing semantic
edges but use the exact v3 receipt, grant, authorization, and status bindings
above. The v3 state router therefore handles the two bootstrap edges before the
legacy generic transition-authority policy; it must not classify either edge as
product-change authorization.

Existing manifest/status v2 programs and their v1 approval, grant, current-
increment binding, activation binding, and action-authorization records retain
their exact current readers and writers. Existing unchanged storage,
traceability, rollover, block-resolution, and workspace-proposal schemas may be
reused only through the manifest/status-specific reader that owns them. A v3
reader rejects every v1 approval, increment grant, current-increment binding,
or action authorization. Each reader rejects a recognized artifact from another
family whether it is supplied as a substitute or as an additional logical role,
record, or status binding. For v2, this targeted rejection does not reinterpret
or blanket-reject unrelated extension roles already valid under its current
reader. The same targeted rule applies to every existing pre-v2-manifest route:
a recognized setup, source-gate, receipt, grant, binding, authorization, or
status artifact not owned by that exact route is rejected as a substitution or
addition, while every artifact and unrelated extension role already legal in
that route remains unchanged.
Later split designs extend this family through manifest/status v4 and v5 rather
than adding optional upgrade fields to v3.

## Durable setup-activation record

The original design proposed separate setup-decision and activation-integrity
records. This split uses one versioned, manifest-owned
`setup-activation-decision/v1` record because both facts become durable in the
same activation transaction.

The record binds:

- program and source identities;
- semantic decision identity;
- the recap-visible operation envelope, every concrete path and path fact shown
  in the recap, bounded path-class definitions, increment allocations,
  inclusions, exclusions, ownership, protections, gates, and material-risk
  facts covered by that identity;
- the exact manifest-owned source-gate definition collection identity and
  digest;
- recap checkpoint and presented integrity identity;
- the controller decision and provenance class;
- the exact typed setup-adapter value identity and digest;
- freshly validated repository, workspace, branch, and protected-work
  observations;
- a bounded classification for safe integrity drift that changes no visible
  decision fact; and
- the derived program-approval and workspace-selection receipt identities.

Any change to a visible source, workspace, increment, requirement or operation
allocation, acceptance meaning, approval mode, gate, protection, exclusion,
external boundary, material risk, operation envelope, previously presented
concrete path or path fact, or bounded path-class definition changes the
semantic decision identity and stops at
`program-revision-workflow-required`. A newly resolved exact path inside an
unchanged approved class does not change semantic identity when it inherits the
class's increment allocation and every other recap-visible fact remains
unchanged. It instead creates a later exact-resolution integrity identity and
must be bound by the exact plan, execution baseline, and action authorization
before use. This design does not rewrite or supersede the immutable proposal in
place.

Safe evidence refresh may proceed only when the visible decision is unchanged
and all source, ownership, and workspace checks still pass. Once a partial
activation prefix contains the setup-activation record, retry must reproduce
it exactly.

## Proposal publication

The existing front-door creation gate remains authoritative. Before any
publication write, the current top-level direct user request must provide
explicit new-program create intent and the exact authoritative source-plan path,
and preparation must have a fresh stable repository observation. This live
creation-only authority permits the exact owner-bound proposal write and
nothing else. The publication request and owner receipt provide deterministic
integrity and retry identity; neither substitutes for create intent, setup
approval, or later action authority. This preserves the current boundary
without adding another durable decision record or user checkpoint.

The existing owner-bound, same-filesystem, manifest-last, no-overwrite protocol
and its prefix-recovery semantics remain, but the publisher tightens its
candidate snapshot and controlling-program freshness gates. Before any
publication write, publication retains the exact regular non-symlink repository-
instruction source identities and digests used during preparation together with
their canonically derived manifest-path set. It uses that set for the same
canonical manifest enumeration and validation as program discovery and retains
the discovered manifest set, dispositions, and manifest/status identities and
digests in memory. Immediately before adopting or reserving the final root and
again before publishing `manifest.json`, it rereads the same instruction
sources, rederives the manifest-path set, and requires both the instruction-
source bindings and derived set to remain exact before repeating discovery. The
exact request-owned staging and target prefixes remain publication-owned work
rather than competing programs. A missing, unsafe, added, or changed instruction
source, a changed derived path set, an invalid manifest, another controlling
program, or any change to the retained discovery result stops; a pre-final-root
stop leaves the target untouched, while a later stop preserves the exact owner-
bound prefix for recovery. A conventional-root-only scan or reuse of caller-
supplied manifest paths without fresh instruction-source validation is not
sufficient publication authority.

That publication-freshness observation must survive the first durable write.
New v3 proposal publication therefore uses
`implementation-program-proposal-request/v2` and
`implementation-proposal-publication-owner/v2`. The request binds the digest of
one closed canonical freshness value; the owner receipt embeds that exact value
and digest, and its existing request digest binds the complete request. The value
contains the complete canonically enumerated applicable instruction-source set
with repository-relative identities, regular non-symlink facts, and byte
digests; the derived instruction-declared manifest-path set; and every retained
discovery disposition with the applicable manifest and status identities and
digests. This versions the two existing publication records and adds no new
ledger or user checkpoint.

Fresh recovery of an incomplete v2 publication prefix reruns canonical
instruction-source enumeration, rederives the declaration set, repeats program
discovery, and requires the result to equal the owner-bound freshness value
before returning retry-ready, adopting a final prefix, or publishing
`manifest.json`. A missing, added, unsafe, or byte-changed instruction source, a
changed declaration, or changed discovery result preserves the exact prefix and
stops recovery. Once a v2 publication is manifest-last complete, later legitimate
instruction or controlling-program changes do not retroactively invalidate that
historical publication root; recovery validates its owner, immutable staging,
target, and committed schema-specific state. Existing v1 requests, owner
receipts, and prefixes retain their exact current validation and recovery route.

Before writing the owner receipt, the publisher enumerates the candidate once,
captures every regular non-symlink file into one immutable in-memory path/bytes/
digest map, and validates that exact captured candidate. The request and owner
inventory derive from the same map, and every staging and final artifact is
written from those exact bytes rather than rereading the mutable candidate or
using a later staging read as publication payload. The complete staging
inventory and digests must match the owner receipt before final-root adoption and
again before manifest-last publication. A changed or divergent staging prefix
stops without final publication. The publisher otherwise writes the owner
receipt and canonical managed artifacts in deterministic order, adopts only an
exact owner-bound final root, and publishes `manifest.json` as the discoverability
commit point.

Fresh bootstrap recovery validates every present prefix before ordinary
program discovery. Exact bytes are adopted; divergent, unsafe, or foreign-owned
bytes stop without deletion or overwrite. A lost response after manifest
publication returns the existing proposal result.

The recovery scanner enumerates every retained proposal-publication staging
root. It independently validates each root's canonical owner receipt, immutable
staging tree, allocated target, inventory, and schema-specific post-publication
target state. A root whose manifest-last commit and target validate is a
completed historical publication and does not block publication or discovery
for another program. Exactly one incomplete, nondivergent request may return
retry-ready. Multiple incomplete requests, duplicate or conflicting target
claims, or any unsafe, divergent, or foreign-owned root stop at recovery without
deletion or overwrite.

The bootstrap-prefix scanner routes by exact manifest schema. For v3, an exact
setup-activation record, source-gate decision, or derived v2 approval receipt
marks activation as started even while status remains sequence-zero
`awaiting-program-approval` / `not-started`. The scanner then validates the
typed activation prefix instead of requiring the mutable target to remain
byte-identical to the published proposal inventory. The immutable staging tree
must remain owner-bound and exact; an unexpected or unbound target path still
fails closed.

## Activation transaction

For a new program, activation writes in this order:

1. create or adopt the exact setup-activation decision record;
2. append or adopt every non-reused source-gate decision whose supported trigger
   is `before-program-activation`;
3. create or adopt the program-approval receipt derived from the setup record;
4. create or adopt the workspace-selection receipt derived from it; and
5. replace only the exact sequence-zero proposal status with sequence-one
   `active` / `awaiting-first-increment` status last, using
   `implementation-setup-activation-status-binding/v1` to bind the exact setup
   record, derived v2 receipts, and applicable source-gate satisfactions.

Activation creates no increment grant, exact plan, execution baseline, action
authorization, progress cursor, or product change.

Every write is deterministic, no-overwrite, and retry-safe. Fresh discovery
adopts an identical prefix and preserves a divergent or foreign prefix as a
recovery stop. A lost response after the status-last write returns the existing
activation result rather than repeating the user question. If a partial prefix
contains the setup record but still needs a non-reused pre-activation gate,
fresh discovery returns that current gate recap and does not repeat setup
approval.

## First-increment start

Activation returns a semantic handoff such as:

```text
$implementing-staged-plans

Start increment <increment-id> for program <program-id>. Revalidate the
approved program, workspace, and repository state before making changes.
```

The prompt contains no authority payload. When the user submits it as the
current top-level message in a fresh task, the controller produces a typed
`increment-start-intent` bound to the discovered program, waiting status,
status-current increment, and provenance class.

The typed start intent remains live controller evidence until the first durable
first-start artifact exists. When one or more non-reused
`before-increment-start` gates are due, the first appended gate-decision record
embeds the complete canonical typed start-intent value and its digest; every
later decision at that trigger binds the identical value. The first-start grant
binds that durable value. This adds no intent ledger or new record family. If no
such gate decision or grant exists after interruption, fresh discovery requires
the semantic handoff again rather than reconstructing direct-message provenance.

The fresh task:

1. discovers one current program and validates the setup-activation record,
   derived receipts, workspace, protected work, and waiting status;
2. confirms the named increment is status-current;
3. appends or adopts every non-reused source-gate decision whose trigger is
   `before-increment-start`;
4. appends or adopts an `implementation-increment-grant/v2` record with
   `grant_kind: first-increment-start`, bound to the start intent and applicable
   source-gate satisfactions;
5. replaces only the exact sequence-one waiting status with sequence-two
   `active` / `preparing` status last, bound to that grant and the same
   satisfactions;
6. builds and validates the current Create/Modify/Preserve exact-plan and
   execution-baseline candidates in memory, then creates or adopts the exact
   plan and, for `approval:standard`, writes `awaiting-plan-approval` status
   last;
7. for `approval:standard`, obtains and appends or adopts the required plan
   approval; then, for every approval mode, creates or adopts the execution
   baseline;
8. appends or adopts every non-reused source-gate decision whose trigger is
   `before-action-authorization`;
9. appends or adopts an `implementation-action-authorization/v2` record only
   from the complete setup-activation, grant, approval-mode, exact-plan,
   baseline, and applicable v2 plan-approval and source-gate chain; and
10. writes `authorized` status last, bound to the same gate satisfactions,
    before product execution begins.

`approval:pre-approve` and `approval:full-increment` may omit only the routine
exact-plan question for facts already inside the setup-approved envelope. They
do not omit the plan, baseline, action authorization, review, diff disposition,
or consequential-action boundaries.

For `approval:standard`, v3 retains the existing schema-specific exact-plan
prompt and byte-exact response checkpoint. This design changes neither that
transport nor its authority semantics.

## Source-defined gates

Preparation records every source-defined gate in the manifest's immutable
structured definition collection and in the recap. A gate definition identifies
its exact authoritative source identity, digest, and locator; any applicable
traceability source-unit identities and digests; question; protected subject;
trigger; the required v3 response semantic; and setup-reuse declaration. Proposal
validation rejects a missing or duplicate gate ID, a missing or mismatched
source binding, or a recap gate that is not an exact readable rendering of that
structured definition. After manifest publication, no reader or writer may
infer, add, move, or reinterpret a gate from free-form source or recap text.

Manifest/status v3 supports only this bounded trigger-to-owner mapping:

| Trigger | Owning typed transaction | First protected artifact or event |
| --- | --- | --- |
| `before-program-activation` | setup activation | program- and workspace-approval receipts and active waiting status |
| `before-increment-start` | first-start or successor-rollover increment-start transaction | increment grant and preparing status |
| `before-action-authorization` | exact-plan materialization | plan-bound action authorization and authorized status |
| `before-product-execution` | execution-state transition | implementing status and first product operation |
| `before-review` | execution-state transition | reviewing status |
| `before-diff-disposition` | diff-disposition transaction | disposition receipt and accepted status |
| `before-program-closure` | closure-approval transaction | closure receipt and closed status |

For the two execution-state triggers, the status v3 replacement is the sole
durable lifecycle event. It embeds the source-gate satisfaction at the status
v3 level while preserving the existing
`implementation-execution-transition/v1` binding inside that status. This
design adds neither a transition ledger nor a new execution-transition schema;
the first product operation proceeds only after the gate-bound implementing
status is durable.

These are the only supported source-gate triggers in v3. Preparation rejects a
gate with any other trigger, a trigger earlier than creation of the setup-
activation record, or a protected subject without exactly one owning
transaction. Later schema families may add triggers only through their own
reviewed designs.

V3 source gates support only an unconditional affirmative whose sole durable
effect is `satisfied`. Preparation stops at
`unsupported-source-gate-response-semantics` before publication when a source
gate requires a choice, value-bearing or conditional response, multiple
satisfying outcomes, or a durable negative, rejection, cancellation, or
amendment result. Those response models require a separately reviewed later
schema family; they are not coerced into affirmative satisfaction.

At one trigger boundary, applicable non-reused gates are appended or adopted in
the manifest collection's ascending stable gate-ID order. Only the next
unsatisfied gate may be written, and fresh discovery derives the same next gate
from the immutable definitions and durable prefix. This adds no separate
ordinal or scheduler.

A `before-increment-start` gate protecting the first increment is written by the
first-start transaction before its grant. One protecting a successor is written
by the rollover transaction after both the current increment's accepted
disposition and the successor-bound rollover action authorization are durable,
and before the successor grant. Immediate continuation binds the exact accepted
`accept-continue` checkpoint; later continuation binds the exact typed accepted-
state continuation checkpoint. Neither route reapproves the current diff, and
both retain their existing action-authorization-first and status-last rollover
boundaries.

When a gate coincides exactly with an existing typed checkpoint, the checkpoint
adapter value satisfies it only when the checkpoint's presented semantic
identity binds the exact gate definition and the boundary and all subject
bindings are identical. A matching boundary or protected subject alone is not
reuse authority. That identity and digest are derived before any protected
receipt, event, authorization, or status is built. Reuse never points at the
final digest of a protected artifact that embeds the satisfaction. Otherwise
the manifest allocates a source-gate decision ledger through
`required_future_lifecycle_writes(...)`. A versioned decision record is
produced from a direct response to the current gate recap and is appended or
adopted before the protected subject crosses its trigger.

For setup-checkpoint reuse, the visible recap must present the gate's readable
question and unconditional affirmative meaning and state that the setup answer
will satisfy it. The setup adapter's unconditional affirmative may reuse only a
gate whose exact v3 response semantic gives that same answer the same effect.
Omitted, hidden, conditional, or differently worded decision semantics require
their own gate recap and decision.

The owning transaction creates one deterministic
`source-gate-satisfaction/v1` binding. It contains a sorted entry for every gate
applicable to the protected subject: gate ID, trigger, protected subject IDs,
satisfaction kind (`source-gate-decision` or `existing-checkpoint`), and one
acyclic evidence reference. `source-gate-decision` references the exact durable
decision-record ID and digest. `existing-checkpoint` references the exact typed
checkpoint/adapter identity and digest that existed before the protected
artifact. It never references that artifact's own ID or digest. The protected
receipt, authorization, operation event, or status emitted by the owner binds
the identical satisfaction value. Missing, extra, stale, differently ordered,
self-referential, or differently bound entries stop before the protected
boundary. This is a fixed mapping inside each existing typed writer, not a
generic orchestration subsystem.

The record binds the stable gate ID and definition, program and authoritative
source identities, semantic decision identity, setup-activation record ID,
current status digest and sequence, the current increment's role, protected
subject IDs, declared trigger, current workspace observation, exact gate-recap
checkpoint and presented integrity identity, explicit affirmative `satisfied`
decision, provenance class `direct-user-message`, and the typed gate-adapter
value identity and digest. At or after plan materialization for the protected
subject it also binds that subject's exact plan and execution baseline; an
earlier gate binds their explicit absence for that subject. A prior accepted
increment's plan and baseline are predecessor context, not authority for a
protected successor. A `before-increment-start` decision additionally embeds one
complete canonical grant-kind-specific boundary-authority value and digest. For
`first-increment-start` this is the typed start intent, waiting status, and first
increment. For `successor-rollover` it is the prior accepted status and current
increment, exact successor increment and brief, typed continuation domain and
checkpoint, and already-durable rollover action authorization ID and digest. All
decisions in that trigger prefix require the identical binding, and the
corresponding grant consumes it. Other triggers require the field's explicit
absence. The first protected lifecycle transition or operation event beyond the
trigger binds the exact acyclic evidence reference through
`source-gate-satisfaction/v1`.

The same trusted conversational adapter contract used for setup approval
applies to a gate recap. Only its current top-level direct user response may
produce a typed gate-decision value, and that value binds the exact gate-recap
identity, decision semantics, and provenance class `direct-user-message` before
the durable record is built. Raw text, caller Booleans, non-user roles, quoted
or retrieved content, and stale or replayed adapter values are rejected.

A negative, conditional, ambiguous, stale, foreign, conflicting, or differently
bound response appends no source-gate decision and performs no protected write;
it leaves the subject before the gate. A later undeclared or moved gate stops at
`program-revision-workflow-required`; it is not inserted into the immutable
proposal by this design.

When that no-write result occurs at `before-increment-start`, fresh discovery
may return the same gate recap only if an earlier decision in the same trigger
prefix already durably carries the identical grant-kind-specific boundary
authority. Otherwise it returns the semantic first-start handoff for a first
increment or the exact schema-specific continuation prompt for a successor and
requires a new direct intent.

## Compatibility

Compatibility is schema-led, dual-read, and no-rewrite:

- New record and status schemas apply only to proposals created under this
  design.
- Artifact families route independently: current bootstrap manifests and
  statuses retain their existing v2 schemas, while their approval, grant, and
  action-authorization records retain their existing v1 schemas. No family is
  called legacy merely by one shared version number.
- Existing manifest/status v1 programs retain their exact current readers,
  writers, lifecycle actions, and navigation output.
- Every existing manifest/status/receipt family and lifecycle state continues
  through its current readers and writers without reinterpretation or
  migration.
- Existing `awaiting-program-approval` / `not-started` proposals retain their
  exact-prompt activation and exact-prefix recovery route through each current
  approval, workspace-approval, grant, and status write.
- Existing `implementation-program-proposal-request/v1` and
  `implementation-proposal-publication-owner/v1` values and publication prefixes
  retain their exact current reader and recovery behavior. New v3 publication
  selects the v2 pair by exact schema; field presence never upgrades v1.
- Before a shared reader or writer changes, immutable golden bytes and digests
  preserve the existing proposal, its exact
  `implementation-program-launch-command/v1` prompt, and every partial and
  completed v2 activation prefix. The unchanged pre-change prompt must remain
  valid against each prefix. Expectations produced only by the modified writer
  are supplemental evidence, not proof of this compatibility promise.
- An exact completed `active` / `preparing` activation prefix may adopt a lost
  status-last response only for the same submitted prompt and bindings. That
  retry is distinct from ordinary first-increment work in an already active
  program.
- Existing `active` / `preparing` programs retain their current first-increment
  route when their v1 approvals, grant, workspace, and state validate.
- Other valid in-flight existing states remain actionable only through their
  current lifecycle contracts. New setup or start records are never injected
  into them.
- New readers route by manifest and status schema before validation. Field
  presence never upgrades a v1 record.
- A v3 manifest rejects v1 approval, grant, current-increment binding, or
  action-authorization downgrade. A v2 manifest rejects the recognized v3-only
  setup, source-gate, receipt, grant, binding, and authorization families whether
  they appear as substitutions or additions. These targeted checks do not alter
  legal v2 routes or unrelated extension roles already accepted by the v2
  reader.
- Every pre-v2-manifest route applies the same targeted substitution/addition
  rejection to recognized artifacts not owned by its exact route, without
  changing any manifest/status combination, owned artifact, next legal action,
  or unrelated extension role already valid in that route.

The implementation must exercise every existing frozen lifecycle fixture
through discovery and its next existing legal action. The compatibility promise
is preservation, not in-place upgrade.

## Failure handling

Unsupported capability, contradictory source, incomplete decomposition,
ambiguous ownership, unsafe Git state, or changed visible decision facts stop
before activation. Identical partial prefixes are adopted. Divergent records,
unsafe workspace drift, and mixed schema families are preserved and reported
without reset, clean, stash, overwrite, or fabricated replacement authority.

Before an activation transaction begins, every reader and validator dependency
needed to validate any partial or completed activation prefix must be resolvable
through the supported package/import boundary. Dependency resolution must not
first occur after a durable write. An unavailable dependency stops before the
first activation write rather than leaving a valid written prefix reported as a
failed activation.

## Test contract

Before v3 source changes, the existing isolated `tests.test_program_activation`
module suite must pass from the repository root without relying on another test
module's import order or path mutation. A failure at that boundary is a baseline
blocker, not an accepted expected failure or a reason to weaken frozen legacy-
prefix coverage.

Implementation must add causal writer-to-fresh-discovery tests for:

- front-door contract coverage preserving explicit direct create intent, the
  exact authoritative source-plan path, fresh read-only repository observation,
  and proposal-only scope; publication request or owner data cannot satisfy
  setup approval or any later authority boundary;
- exact manifest-v3 `setup_semantics` validation, semantic-identity stability
  and mutation coverage, and deterministic recap rendering with all approval-
  bound facts visible,
  including the authoritative source title and exact location, question,
  unconditional affirmative meaning, no-write behavior for every other response,
  and disclosed setup reuse for every reused source gate,
  and no user-facing machine payload during setup, gate decisions, or semantic
  handoff;
- direct affirmative, direct negative, ambiguous, conditional, quoted,
  retrieved, stale, replayed, and malformed setup decisions, with a negative
  starting no activation transaction, leaving every proposal artifact byte-
  identical, and fresh discovery returning the same setup recap;
- a renderer-schema or rendered-recap-byte-only mutation changing the recap
  checkpoint and rejecting the earlier typed setup decision before any durable
  write, plus setup-activation record rejection for a missing or mismatched
  typed setup-adapter identity or digest;
- setup-activation record and derived receipt ordering, with failure injection
  after the setup record, every applicable pre-activation gate decision, every
  derived receipt, and status-last;
- broadened operation scope or path classes changing semantic identity, while a
  safe exact-path resolution inside an unchanged bounded class preserves it;
- status-current exact plans accepting only paths and classes allocated to that
  increment, including inherited allocation for a newly resolved class member,
  explicit recap-visible sharing, and rejection of cross-increment scope;
- activation ending at `active` / `awaiting-first-increment` with no grant,
  plan, baseline, action authorization, progress record, or product change;
- exact v3 routing for the sequence-zero proposal, sequence-one setup
  activation, and sequence-two first-start states, including rejection of every
  v1 approval, grant, current-increment binding, or action-authorization
  substitution, plus v2 rejection of recognized v3-only substitutions and
  additions, and the same rejection for every pre-v2-manifest route, without
  changing any exact existing manifest/status combination, legal route, owned
  artifact, or unrelated accepted extension;
- discriminator-specific v2 causal shapes, with program- and workspace-
  selection approvals rejecting grant, plan, or baseline forward references
  and every later approval or action authorization requiring its exact existing
  authority prefix;
- fresh-task handoff production and consumption;
- `approval:standard` retaining its existing byte-exact plan checkpoint while
  setup approval, gate decisions, and the semantic handoff remain free of user-
  facing machine payload;
- grant and action-authorization chain rejection when any input, including the
  status-current brief or workspace-selection binding, is absent, stale,
  replayed, downgraded, or mismatched;
- `before-increment-start` failure injection for `first-increment-start` and
  `successor-rollover`, including both immediate and accepted-state continuation,
  before the first first-start gate decision, after the successor rollover action
  authorization but before its first gate decision, after every boundary-
  authority-bearing gate decision, after the corresponding grant, and after
  status-last; fresh discovery re-requests the schema-specific handoff or
  continuation prompt before any durable boundary-authority binding, adopts the
  exact binding afterward, and rejects an absent, changed, wrong-grant-kind,
  wrong predecessor or successor, cross-trigger, cross-domain, wrong-checkpoint,
  wrong-prompt, or conflicting binding;
- every supported source-gate trigger routing to exactly one owning transaction,
  with unsupported, premature, ownerless, and multiply owned triggers rejected
  during preparation before publication; choice, value-bearing, conditional,
  multi-outcome, and durable-negative response semantics rejected before
  publication; and multiple gates at one trigger being appended, retried, and
  rediscovered only in ascending stable gate-ID order;
- proposal publication and fresh discovery preserving the exact manifest-owned
  gate-definition collection, with missing, duplicate, reordered, added, or
  source-identity, locator, source-unit, or digest-mismatched definitions
  rejected and no definition inferred from free-form text;
- exact existing-checkpoint reuse only when the checkpoint's presented semantic
  identity binds the exact gate definition and its boundary and subject bindings
  match, with same-boundary question, response-semantics, or subject near-matches
  and omitted or undisclosed setup reuse requiring their own gate decision, and
  the diff-disposition and closure checkpoints proving that no satisfaction
  contains a protected artifact's own ID or digest;
- source-gate persistence, retry, and trigger enforcement, with failure
  injection after the gate decision and after each protected receipt,
  authorization, and schema-routed status, including the status-owned durable
  execution-state event, followed by fresh discovery;
- proposal-publication failure injection after every owner/staging/final write
  through manifest-last discovery, with exact adoption and divergent-prefix
  preservation, plus mutation of a candidate after its immutable capture proving
  that no owner, staging, or final byte can diverge from the captured map, and
  mutation of staging before each final gate producing a preserved recovery
  stop; coverage also includes sequential program publication and fresh
  discovery while the earlier completed staging root remains, and fail-closed
  handling of multiple incomplete or conflicting roots; the publication
  freshness checks cover conventional and instruction-declared controlling
  manifests that exist initially or appear or change immediately before final-
  root adoption or manifest-last publication, plus same-path instruction-source
  byte changes that add, remove, or retarget a declaration without changing its
  Git status category; after every durable incomplete v2 prefix, a fresh process
  must re-enumerate and reject an added, removed, unsafe, or changed instruction
  source or any changed declaration or discovery disposition before retry or
  finalization, while a completed historical v2 publication remains nonblocking
  after later instruction changes and every v1 publication prefix retains its
  exact current route;
- first-increment failure injection after the grant, `preparing` status, exact
  plan, `awaiting-plan-approval` status when applicable, plan approval,
  execution baseline, action authorization, and `authorized` status, followed
  by fresh discovery and exact adoption or a divergent-prefix stop;
- targeted v3 schema-routed prefix and retry coverage for the existing review-
  preparation, review-remediation, rollover, blocked-resolution, diff-
  disposition, and closure writers wherever this design changes an approval,
  grant, action-authorization, status, or source-gate binding; review coverage
  exercises fresh discovery, exact retry or adoption, and divergent-prefix
  stops after review evidence, review packet, verified status, awaiting-diff
  status, remediating status, and reviewing-after-remediation status; this is
  affected-interface coverage, not a duplicate end-to-end lifecycle matrix;
- wrong-status, wrong-subject, wrong-plan/baseline, wrong-recap, missing or
  altered decision/provenance/adapter binding, duplicate, and conflicting
  source-gate decisions;
- missing, extra, stale, reordered, or digest-mismatched
  `source-gate-satisfaction/v1` entries on every protected artifact and event;
- direct affirmative, direct negative, non-user-role, quoted, retrieved, tool-
  produced, ambiguous, conditional, stale, replayed, and malformed gate-adapter
  values, with a negative response leaving the source-gate ledger, every
  protected artifact, and status byte-identical; fresh discovery returns the
  same current gate recap when durable trigger context exists, but requires the
  schema-specific first-start handoff or successor continuation prompt when no
  grant-kind-specific boundary-authority binding exists;
- every existing frozen v1 and v2 manifest/status/receipt fixture remaining
  discoverable and able to take its unchanged next legal action and schema-
  specific output route, plus pre-change immutable golden bytes and digests for
  the v2 proposal, its exact `implementation-program-launch-command/v1` prompt,
  and every partial and completed activation prefix, with that unchanged prompt
  submitted rather than regenerated by the modified renderer and every prefix
  retaining its exact current fresh-discovery retry or next-action route; this
  coverage runs in isolation and proves that every dependency used to validate
  a partial or completed activation prefix resolves before the first durable
  activation write; and
- a complete new-program path from readable recap through first-increment plan
  authorization, stopping before product execution.

Static tests must not be described as proof of human comprehension or an
unforgeable conversation-role attestation.

## Documentation and repository scope

Implementation updates the skill front door and canonical reference material
for setup approval, activation, fresh-task start, source gates, schema routing,
and legacy preservation. Normative rules have one canonical owner and are
linked rather than copied across references.

Design, implementation, tests, and source documentation belong only in this
repository. Installation, generated or cached plugin synchronization, and
consuming-program repair require separate authorization.

## Success criteria

This design is complete when explicit creation-only authority publishes only an
owner-bound proposal; one readable setup decision, plus any separately required
source gate at the activation boundary, creates a durable, retry-safe active
program waiting for its first increment; a fresh task can derive the first plan-
bound action authorization from the complete authority chain; every supported
gate, including a successor increment-start gate, is consumed by exactly one
owning transaction; existing programs keep their current lifecycle behavior;
and no setup or activation step changes product files or authorizes
consequential actions.

## Non-goals

This design does not add expanded destructive operations, accepted-result
tombstones, pre-mutation recovery staging, progress projections, part/task
cursors, general program revision, commits, external or product publication,
deployment, plugin installation, or consuming-program repair.
