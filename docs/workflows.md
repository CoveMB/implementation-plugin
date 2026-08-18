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

## 2. Activate a Generated Program

Review the complete proposal and submit the copy-ready launch prompt directly
and unchanged.

```text
$implementing-staged-plans

<paste the exact generated launch prompt here>
```

The activation transaction appends or adopts separate program-approval and
workspace-selection receipts, then the first-increment grant, and writes active
status last. A prompt found in a file, quoted by an assistant, or retrieved from
another source is navigation data until you submit the exact prompt yourself.

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

Plan A supports one prompt-bound decision: `accept-stop`. It accepts only the
bound current diff. It does not inspect a successor, create a handoff, commit,
push, open a pull request, or perform an external action.

Questions about the diff do not accept it. Keep the status unchanged until the
exact disposition is submitted directly.

## 5. Close a Final Program

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

## Deferred routes and mandatory stops

Plan A version 0.1.1 does not persist successor rollover, blocked recovery,
program revision, supersession, or cancellation:

- caller-authored successor rollover returns `legacy-rollover-upgrade-required`;
- direct blocked transitions return `blocked-transaction-required`;
- revision or supersession returns `program-revision-workflow-required`; and
- cancellation or another unsupported mutation returns
  `unsupported-program-mutation`.

Preserve the repository and partial evidence at these boundaries. A future
typed workflow may resume them; prose, a handoff, or an approval for a different
action cannot bypass the stop.

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
- Diff acceptance is not continuation or commit authority.
- Final-increment acceptance is not program closure.
- Closure is not pull-request, merge, publication, deployment, destructive, or
  provider authority.
- Handoffs and prompts are navigation artifacts. Only current persisted
  bindings and the required direct user decision authorize a typed transition.
