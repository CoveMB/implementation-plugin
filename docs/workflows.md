# Common workflows

These examples use a fictional program called `LIBRARY-001`. Replace every
identifier and path with the persisted records in your repository. A request
selects a route; it does not override state or grant an unnamed action.

## 1. Create a New Program

Use this route only when discovery finds no controlling manifest and you
explicitly want to create a program proposal.

```text
Use $implementing-staged-plans to create a new repository-backed program from
docs/library-search-plan.md in /work/library-catalog. Inspect the repository
freshly. Publish only the creation control plane and print the short program
start summary once in the conversation: numbered increments, workspace, approval scope, limits, detail links, and one start action. Create no recap or summary file. Stop before starting.
```

The publisher binds the immutable source, traceability, proposed program,
workspace observation, first brief, empty ledgers, and initial status to one
owner receipt. It publishes `manifest.json` last. An exact partial prefix is
retryable; any divergent or foreign-owned prefix stops without overwrite.

Creation authority does not approve the program or permit product changes.

## 2. Approve and Activate a Generated Program

Review the printed summary, including the workspace, increments, limits, and gates.
After it is presented, reply directly:

```text
Start the first increment
```

New proposals use `combined-start/v1`. That decision approves the displayed setup
and starts the first increment under the selected approval mode. It can lead to
local implementation after the required plan and execution checks. Starting works
in the same task or a fresh task; a fresh task first rediscovers and prints the
current summary, then waits for its direct reply. Creation intent, an opening
handoff, generic “yes”, and quoted or conditional answers do not count.

Separate receipts and the recoverable `awaiting-first-increment` state remain
internal. If interrupted, request a retry of the existing combined decision;
discovery does not continue on its own. Source gates still pause where required.
Unmarked legacy v3 proposals retain the setup-only “yes” and separate first-start
handoff; they are not converted or deleted.

Existing manifest-v2 proposals keep the historical byte-exact launch prompt and
combined activation behavior.

## 3. Before Production Modification

Prepare the exact-file plan and execution baseline before changing product
files.

```text
Use $implementing-staged-plans to prepare the exact-file plan for LIBRARY-001
LIBRARY-INDEX under approval:standard. Preserve existing work. Stop for the
exact plan approval before product modification.
```

Standard mode keeps the plan gate. Pre-approve and full-increment modes may
omit only that routine pause. Every mode still needs the current increment
grant, an exact plan, an execution baseline, and plan-bound write authority.
Authorized state permits no product delta.

Accepted v1 setup supports `Create`, `Modify`, and `Preserve`. The exact
setup/envelope v2 family adds `Delete`; each Delete path must be an exact
regular file with a baseline-bound same-filesystem quarantine destination.
Protected paths, changed identities, symlinks, collisions, cross-device moves,
and unsupported descriptor operations stop before mutation.

## 4. Prepare Review and Diff Disposition

Before implementation, declare one exact Create path for each anticipated
review scope. At review, the architecture risk predicates select the required
specialists; the declarations and completed reports must match that selection.
Persist all selected reports, reconcile findings, and run fresh verification
before preparing the review evidence and packet. See the canonical
[review contract](../skills/implementing-staged-plans/references/review-coordination.md).

```text
Use $implementing-staged-plans to prepare the typed review transaction for
LIBRARY-001 LIBRARY-INDEX. Reconcile the exact requirements, architecture, and
test-evidence reports and every risk-selected specialist report. Stop at the
exact diff disposition.
```

Questions about the diff do not accept it. Keep the status unchanged until the
exact disposition is submitted directly.

For the v2 family, review and diff disposition carry the complete ordered
product-path result rather than a legacy product-delta digest. A deleted path
must remain absent and match its exact quarantine receipt and retained bytes
through approval-v3 acceptance.

An open material finding uses a typed remediation round trip. Persist the
initial review evidence in `reviewing`, enter `remediating`, make the bounded
repair, and require renewed affected-scope reports that name every initial
finding before returning to `reviewing`. Fresh verification then advances
through `verified` to `awaiting-diff-approval`. Questions and discussion do not
repair findings or advance the lifecycle.

## 5. Dispose the Current Diff

The new-model typed diff-disposition prompt always offers `accept-stop`. It
offers `accept-continue` only when the [successor contract](../skills/implementing-staged-plans/references/state-authorization.md#allocate-lifecycle-writes-before-authority)
resolves the next increment. Both choices persist the same Plan A acceptance prefix
and accepted status first. Already persisted legacy programs using
`approval:full` or `approval:full-diff` retain automatic acceptance.
The continue choice then completes its prompt-bound rollover with no second
routine checkpoint. Neither choice commits, pushes, opens a pull request, or
performs an external action.

## 6. Continue an Accepted Program

Replaying `accept-stop` cannot start a successor. A later fresh task must use the
distinct `accepted-state-continuation` prompt derived from current accepted
status. A handoff or earlier prompt is navigation only and cannot substitute for
direct submission of those exact current bytes.

## 7. Authorize a Successor Increment

The rollover transaction persists or adopts the action authorization,
successor grant, handoff, successor brief, and rollover record in order, then
writes status last. The successor status binds
`current_increment_authority_binding`; it does not rewrite the immutable
manifest or inherit genesis authority. The successor exact plan allocates its
own complete lifecycle paths before its baseline and write authority exist.

Delete-capable rollover uses result-bound action-v3 and reuses the existing
handoff. Its inherited workspace retains ordered product states and quarantine
receipts. A tombstone may be recreated only when that successor explicitly owns
the path as `Create`; recreation preserves historical quarantine evidence.

## 8. Resolve a Blocked Program

Only active `implementing` or `reviewing` state can enter the typed blocked
transaction. The sink derives prior state and controlling bindings before it
writes blocked status. Recovery uses the exact `blocked-recovery` prompt and
restores only the recorded prior states after its action and resolution records
are durable. Plan A's `reviewing -> remediating -> reviewing` path remains
separate.

For an existing blocked v1 increment whose report allocation is incomplete,
use the opt-in [review allocation recovery](../skills/implementing-staged-plans/references/state-authorization.md#review-allocation-recovery)
preview. It names exact fresh JSON reports inside the already approved report
class and retains the original plan, baseline, reports, and product evidence.
Ordinary resume grants no report allocation. Supply truthful evidence for each
original recovery criterion; the preview leaves assessments, reconciliation,
and fresh verification pending. Submit the exact allocation command only after
reviewing those paths and criteria, then complete the reports through the
normal review writer and stop at diff approval.

The allocation survives later blocks and ordinary resumes of that increment.
Accepted rollover archives its provenance, retains the predecessor reports,
and requires the successor plan to Preserve them. The successor receives no
active report extension from its predecessor. Terminal v1 closure validates
the same effective contract. Installation and recovery of an actual blocked
program are separate operations; local regression success proves neither.

## 9. Close a Final Program

Use this route only after current acceptance and an explicit terminal result from
the [successor contract](../skills/implementing-staged-plans/references/state-authorization.md#allocate-lifecycle-writes-before-authority).
Unavailable selection cannot authorize closure. PLUG-002's accepted-chain and
terminal Delete closure/disposal work remains separate.

```text
Use $implementing-staged-plans to prepare closure for the accepted final
increment of LIBRARY-001. Reconcile all requirements and fresh program evidence,
write only the manifest-owned closure artifacts, and stop for exact closure
approval.
```

New programs derive both closure paths from
`implementation-closure-storage/v1`. Preparation creates or adopts the
reconciliation, then the closure packet, and writes awaiting-closure status
last. The exact closure prompt appends or adopts its approval and writes closed
status last. Closure approval authorizes no commit or later action.

## Unsupported routes and mandatory stops

Version 0.1.3 adds exact regular-file Delete to typed successor rollover and
blocked recovery while
preserving these sink guards:

- legacy automatic or caller-authored rollover returns
  `legacy-rollover-upgrade-required`;
- generic direct blocked transitions return `blocked-transaction-required`;
- revision or supersession returns `program-revision-workflow-required`; and
- cancellation or another unsupported mutation returns
  `unsupported-program-mutation`.

Preserve the repository and partial evidence at these boundaries. Prose, a
handoff, or an approval for a different action cannot bypass the stop. Final
programs continue through the unchanged Plan A closure transaction.

## Recovery from an interrupted transaction

Retry only the same typed operation or exact prompt. The lifecycle writers
adopt byte-identical prefixes and continue in their defined order. A changed,
unsafe, stale, ambiguous, or unexpected prefix is preserved and returns the
corresponding recovery-required disposition. Do not delete or rewrite it as a
routine recovery step.

Delete recovery is likewise non-destructive: before rename, failure leaves the
product file in place; after a matching rename, only an exact receipt may be
adopted. A changed quarantine, replacement source, or divergent receipt is
preserved for diagnosis. PLUG-001 never unlinks quarantine, claims secure
erasure, supplies PLUG-002 requirement evidence, or performs terminal closure.

## Authority reminders

- Program creation is not program activation.
- Program activation is not implementation authority.
- Plan approval is not action authorization.
- Diff acceptance is not continuation or commit authority unless the submitted
  exact disposition is the bound `accept-continue` route; it never grants commit
  authority.
- Final-increment acceptance is not program closure.
- Closure is not pull-request, merge, publication, deployment, destructive, or
  provider authority.
- Handoffs and prompts are navigation artifacts. Only current persisted
  bindings and the required direct user decision authorize a typed transition.
