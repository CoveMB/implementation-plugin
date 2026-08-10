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

At the program level, work moves from captured source and program approval to an
active program, then to reconciliation, closure approval, and closed state.

Within an active program, an increment is prepared, planned, authorized,
implemented, reviewed, remediated when necessary, verified, and accepted. A
change request returns it to preparation. A blocked or superseded state cannot
be bypassed by changing the wording of a prompt.

The skill always revalidates current repository facts and controlling records
before relying on an earlier state.

## Approval modes

Approval modes control routine pauses, who accepts a verified diff, and whether
the workflow may continue to another increment. They do not grant action
authority.

| Mode | Scope | Routine plan pause | Diff acceptance | Continuation and mandatory stop |
| --- | --- | --- | --- | --- |
| `approval:standard` | One increment | Yes | User | Stops for plan approval, user-owned material decisions, contradictions, hard stops, and diff acceptance |
| `approval:pre-approve` | One increment | No | User | Stops for user-owned decisions, program amendments, contradictions, hard stops, and diff acceptance |
| `approval:full-increment` | One increment | No | User | Runs through verification, then stops for diff acceptance unless a hard stop occurs |
| `approval:full-diff` | One increment | No | Automatic only after verification and a valid bound packet | Stops after accepting that one diff; it cannot begin the next increment |
| `approval:full` | Multiple increments within one suitable conversation | No | Automatic only after verification and a valid bound packet | May continue in the same suitable conversation; stops at hard stops, program closure, later-action gates, or a new conversation requiring renewed authority |

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
