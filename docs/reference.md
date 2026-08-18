# Reference

This page is a compact guide to the terms and decisions used by
`implementing-staged-plans`. The [canonical skill instructions](../skills/implementing-staged-plans/SKILL.md)
and their linked procedures remain authoritative when a user guide and the
implemented workflow differ.

## Invocation

The command depends on how the skill was installed:

| Installation | Invoke with |
| --- | --- |
| Codex plugin or standalone skill | `$implementing-staged-plans` |
| Claude Code plugin | `/implementation-plugin:implementing-staged-plans` |
| Claude Code standalone skill | `/implementing-staged-plans` |

Follow the invocation with a target program or manifest, the action you want,
the desired approval mode when creating new state, and any explicit stop.

## Core terms

### Program

A repository-backed record that ties an authoritative source to requirements,
planned increments, approvals, state, workspace, and evidence.

### Increment

One bounded, reviewable unit of the program. An increment has its own plan,
authority, implementation, review, verification, and acceptance state.

### Exact-file plan

The current implementation plan for one increment, including the files and
behavior expected to change. It is bound to the current program, workspace, and
repository observation rather than acting as a timeless checklist.

### Execution baseline

The immutable pre-product-change snapshot of the exact plan, repository
observation, path dispositions, and preserved user work. New-program status
cannot become authorized until this baseline and its plan-bound action
authorization are durable.

### Workspace binding

The approved writable repository path, branch, base, current head, and recorded
pre-existing work. It prevents work prepared for one tree from being applied to
another without revalidation.

### Action authorization

A current grant for one named action and scope, such as modifying the workspace,
running local verification, or creating a local commit. It is separate from the
approval mode.

### Evidence

The concrete result that supports a claim: for example, a command result,
accepted review artifact, state digest, or repository observation. Evidence is
limited to what it actually exercised.

### Review packet

The bound collection of review findings, dispositions, verification results,
and the exact diff proposed for acceptance.

### Handoff

A navigation record for continuing later. It points to the controlling state
and evidence but grants no authority on its own.

### Reconciliation

The final accounting across every requirement, amendment, increment, finding,
deferral, and program-level verification result.

### Closure packet

The bound summary presented for explicit program-closure approval after
reconciliation succeeds.

## Lifecycle at a glance

The implemented Plan A order is: **Create a New Program**, **Activate a
Generated Program**, **Before Production Modification**, **Prepare Review and
Diff Disposition**, then **Close a Final Program**. Creation publishes only the
proposal control plane. Activation uses one exact prompt and separate typed
receipts. Planning persists the execution baseline before product work. Review
uses a typed preparation transaction. The only Plan A diff disposition is
`accept-stop`. A final program derives its closure files from
`implementation-closure-storage/v1` and closes only after another exact prompt.

Every typed transaction writes controlling status last and adopts only
byte-identical prefixes. A divergent prefix stops for recovery without cleanup.

The skill always revalidates current repository facts and controlling records
before relying on an earlier state.

## Approval modes

Approval modes define policy, but the 0.1.1 Plan A persistence surface supports
only first-increment `accept-stop`; successor continuation remains deferred.
Modes do not grant action authority.

| Mode | Scope | Routine plan pause | Diff acceptance | Continuation and mandatory stop |
| --- | --- | --- | --- | --- |
| `approval:standard` | One increment | Yes | User | Stops for plan approval, user-owned material decisions, contradictions, hard stops, and diff acceptance |
| `approval:pre-approve` | One increment | No | User | Stops for user-owned decisions, program amendments, contradictions, hard stops, and diff acceptance |
| `approval:full-increment` | One increment | No | User | Runs through verification, then stops for diff acceptance unless a hard stop occurs |
| `approval:full-diff` | One increment | No | Policy permits automatic acceptance only after verification and a valid bound packet | The 0.1.1 typed route still ends at `accept-stop`; it cannot begin another increment |
| `approval:full` | Future multi-increment policy | No | Policy permits automatic acceptance only after verification and a valid bound packet | Plan A does not persist continuation; the Plan B route is required |

When new state omits a mode, the default is `approval:standard`. Persisted state
with a missing or unknown mode is invalid and is not silently defaulted. An
explicit user-requested gate always remains in force, even if the selected mode
would normally omit that pause.

## Three different kinds of permission

**Approval mode** sets the routine interruption policy. It answers questions
such as whether to pause for the exact-file plan and who accepts the reviewed
diff.

**Implementation action authorization** permits one current program action and
scope. Examples include writing a specific program artifact, modifying the bound
workspace, running named local verification, or creating a local commit.

**Later or external-action authorization** covers consequential actions after
implementation, such as a pull request, merge, publication, release, deployment,
migration, destructive operation, permission change, or provider mutation. The
program must be in a suitable state, and the grant must name that exact action.

None of these permissions substitutes for the others. In particular, accepting
a diff does not authorize a commit, and closing a program does not authorize a
release.

## Common hard stops

The workflow stops instead of guessing when it finds:

- more than one possible program or workspace;
- a source, plan, approval, status, brief, handoff, or packet digest mismatch;
- a branch, base, head, path, or pre-existing-work observation that has drifted;
- an active or conflicted Git operation;
- a requested transition that is not legal from the current state;
- missing, expired, revoked, rejected, ambiguous, or mismatched authority;
- a user-owned decision or program amendment required by the selected mode; or
- a requested Git, publication, provider, or external action outside the grant.

The implemented deferred-operation stops are
`legacy-rollover-upgrade-required`, `blocked-transaction-required`,
`program-revision-workflow-required`, and `unsupported-program-mutation`.
Accepted legacy programs and historical terminal records remain readable, but
those read paths do not reactivate a mutation sink.

The result should name the failed invariant and return the smallest action that
can resolve it. The workflow does not manufacture replacement state to continue.

## What can be checked mechanically

The bundled scripts can validate schemas, exact bindings, digests, declared
state transitions, file constraints, deterministic packet structure, and
specific local command evidence supplied to them.

They do not prove that a reviewer was genuinely independent, a human approval
was well informed, a design is semantically correct, a live service behaves as
expected, or an external action occurred. Those claims still need evidence from
the relevant human or runtime process.

For copyable task prompts, continue with [Common workflows](workflows.md). For a
blocked run, use [Troubleshooting](troubleshooting.md).
