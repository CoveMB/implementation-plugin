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
freshly. Publish only the creation control plane and return the one exact launch
prompt. Do not activate or implement it.
```

The publisher binds the immutable source, traceability, proposed program,
workspace observation, first brief, empty ledgers, and initial status to one
owner receipt. It publishes `manifest.json` last. An exact partial prefix is
retryable; any divergent or foreign-owned prefix stops without overwrite.

Creation authority does not approve the program or permit product changes.

## 2. Approve and Activate a Generated Program

Review the readable setup recap and answer its final setup question directly.

```text
Yes
```

For manifest v3, activation records the typed setup decision and separate
program/workspace receipts, then stops at `awaiting-first-increment` without a
grant or product authority. Submit the returned semantic handoff in a fresh task;
that task revalidates current state, records the first-start grant, and reaches
`preparing`. A file, quoted answer, retrieved answer, conditional answer, or
assistant-generated answer cannot satisfy either direct-user boundary.

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

## 4. Prepare Review and Diff Disposition

After the exact implementation delta reaches reviewing state, prepare the
required raw reports, review evidence, review packet, and fresh verification.

```text
Use $implementing-staged-plans to prepare the typed review transaction for
LIBRARY-001 LIBRARY-INDEX. Reconcile the exact requirements, architecture, and
test-evidence reports. Stop at the exact diff disposition.
```

Questions about the diff do not accept it. Keep the status unchanged until the
exact disposition is submitted directly.

An open material finding uses a typed remediation round trip. Persist the
initial review evidence in `reviewing`, enter `remediating`, make the bounded
repair, and require renewed affected-scope reports that name every initial
finding before returning to `reviewing`. Fresh verification then advances
through `verified` to `awaiting-diff-approval`. Questions and discussion do not
repair findings or advance the lifecycle.

## 5. Dispose the Current Diff

The new-model typed diff-disposition prompt always offers `accept-stop`. It
offers `accept-continue` only when traceability names one successor and every
dependency is satisfied. Both choices persist the same Plan A acceptance prefix
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

## 8. Resolve a Blocked Program

Only active `implementing` or `reviewing` state can enter the typed blocked
transaction. The sink derives prior state and controlling bindings before it
writes blocked status. Recovery uses the exact `blocked-recovery` prompt and
restores only the recorded prior states after its action and resolution records
are durable. Plan A's `reviewing -> remediating -> reviewing` path remains
separate.

## 9. Close a Final Program

Use this route only after the accepted increment is final and traceability
allocates no successor.

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

Version 0.1.2 adds typed successor rollover and blocked recovery while
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
