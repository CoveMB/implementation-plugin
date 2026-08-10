# Common workflows

These examples are starting points for a fictional program called
`LIBRARY-001`. Replace its identifiers and paths with the persisted records in
your repository. A prompt helps the skill find the work; it does not override
the program's current state or grant an action that has not been authorized.

## 1. Start from an approved implementation plan

**Use this when:** You have an approved plan and want to establish the program
and workspace without assuming that implementation may begin.

**What to provide:** The plan path, intended repository or worktree, and desired
approval mode.

**Example:**

```text
Use $implementing-staged-plans with the approved plan at docs/library-search-plan.md.
Work in /work/library-catalog under approval:standard.
Start with read-only orientation, show me the proposed program and workspace binding,
and stop at the first required approval.
```

**What happens next:** The skill looks for the authoritative source, program
manifest, current state, repository identity, and any existing bindings. If no
program has been captured, it identifies the smallest legal setup step.

**Where it stops:** At the first missing approval, ambiguous program identity,
workspace conflict, or stale binding. You decide whether to approve or correct
the proposed record.

## 2. Capture a program and select a workspace

**Use this when:** A plan exists, but its source, program revision, or writable
workspace has not yet been bound.

**What to provide:** The authoritative source, proposed program identifier,
repository path, branch, base commit, and known pre-existing work.

**Example:**

```text
$implementing-staged-plans

Prepare the program-authority and workspace-selection records for LIBRARY-001.
Use docs/library-search-plan.md as the proposed source and /work/library-catalog
as the proposed workspace. Inspect the repository read-only, include all existing
changes in the observation, and show me the exact records before any write.
```

**What happens next:** The skill checks the source and repository, proposes
digest-bound records, and distinguishes observed facts from decisions you still
need to make.

**Where it stops:** Before writing records or selecting a workspace unless that
exact write is authorized. Program approval and workspace selection are separate
decisions.

## 3. Choose an approval mode

**Use this when:** You want to decide how often routine plan and diff approvals
interrupt an increment.

**What to provide:** The program, current increment, preferred mode, and any
extra pauses you want to keep.

**Example:**

```text
$implementing-staged-plans

For LIBRARY-001 INC-002, compare approval:standard and approval:full-increment.
Do not change persisted state. Explain which routine pauses each mode keeps and
confirm that neither mode authorizes a commit, push, pull request, or release.
```

**What happens next:** The skill explains the five supported modes against the
current program state. See the [approval-mode reference](reference.md).

**Where it stops:** After the comparison. Choosing a mode is not the same as
recording a bound approval or granting write authority.

## 4. Prepare and execute one increment

**Use this when:** The program and workspace are valid and one increment is
ready for an exact-file plan and test-first implementation.

**What to provide:** The manifest path, increment, current workspace, approval
mode, and the exact actions already authorized.

**Example:**

```text
$implementing-staged-plans

Advance LIBRARY-001 INC-002 in /work/library-catalog under approval:standard.
Revalidate the manifest, workspace, branch, base, current head, and existing work.
Prepare the exact-file plan and stop for its required approval before implementation.
```

**What happens next:** The skill revalidates current authority, inspects
comparable code, shapes a bounded plan, and routes implementation only after the
plan and write scope are authorized.

**Where it stops:** In standard mode, at plan approval and later at diff
acceptance. Any contradiction, unauthorized action, or repository drift causes
an earlier stop.

## 5. Accept an increment and stop

**Use this when:** Review and fresh verification are complete and you want to
accept the current increment without continuing.

**What to provide:** The increment, accepted review packet, current diff, and an
explicit acceptance decision bound to them.

**Example:**

```text
$implementing-staged-plans

Accept only the verified, packet-bound diff for LIBRARY-001 INC-002. Record the
accepted increment and prepare its handoff. Stop before INC-003 and do not commit,
push, create a pull request, publish, release, or deploy.
```

**What happens next:** The skill confirms that the review packet, addendum,
verification, workspace, and current diff still match before applying the legal
acceptance transition.

**Where it stops:** After the increment is accepted and its navigation artifacts
are valid. Acceptance does not authorize a commit or another increment.

## 6. Accept an increment and authorize the next increment

**Use this when:** One increment is ready for acceptance and you also want to
grant renewed authority for the dependent next increment.

**What to provide:** The current acceptance, next increment, validated handoff
and brief, and exact new authorization scope.

**Example:**

```text
$implementing-staged-plans

Accept the verified diff for LIBRARY-001 INC-002, then validate the proposed
handoff and brief for INC-003. Record authority to prepare INC-003 only. Do not
implement INC-003 or perform any Git or external action.
```

**What happens next:** The skill treats current acceptance, rollover, and next
increment authority as distinct transitions. It validates each binding before
moving to the next.

**Where it stops:** After the specifically authorized rollover or preparation
step. It does not infer implementation authority from permission to prepare.

## 7. Hold the current diff while asking a question

**Use this when:** A diff is awaiting acceptance and you need an explanation
before deciding.

**What to provide:** The increment, the exact concern, and a clear instruction
not to change the tree or state.

**Example:**

```text
$implementing-staged-plans

Keep LIBRARY-001 INC-002 at awaiting-diff-approval. Explain why
src/catalog/search.py changed and how its tests protect the accepted behavior.
Do not edit files, change state, or treat this question as diff acceptance.
```

**What happens next:** The skill reads the accepted plan, current diff, review
evidence, and tests needed to answer the question.

**Where it stops:** After the explanation. The diff remains unaccepted until you
make an explicit bound decision.

## 8. Request a bounded repair

**Use this when:** Review found a material defect in the current increment and
the repair scope is known.

**What to provide:** The finding, affected increment, allowed files or behavior,
and renewed review expectations.

**Example:**

```text
$implementing-staged-plans

Repair only finding REV-SEARCH-04 for LIBRARY-001 INC-002. The allowed scope is
src/catalog/search.py and tests/test_search.py. Re-enter review after the repair,
run the required verification, and stop for diff acceptance. Do not address
unrelated cleanup.
```

**What happens next:** The skill verifies that the finding and repair authority
match the current packet, then routes the smallest test-first remediation and a
fresh review.

**Where it stops:** At a new contradiction, a scope expansion, an unresolved
material finding, or the next diff-acceptance gate.

## 9. Request a program-level amendment

**Use this when:** The accepted program is no longer the right description of
the work, rather than when a small implementation repair is enough.

**What to provide:** The evidence that changed, affected requirements or
increments, and the decision you want evaluated.

**Example:**

```text
$implementing-staged-plans

Evaluate a program amendment for LIBRARY-001 because the catalog service no
longer exposes the endpoint assumed by docs/library-search-plan.md. Do not patch
around the contradiction. Identify affected requirements, increments, plans,
approvals, and evidence, then stop with the proposed amendment boundary.
```

**What happens next:** The skill classifies the drift, traces its impact, and
prepares the smallest honest amendment path without silently rewriting accepted
history.

**Where it stops:** Before changing the program revision or resuming affected
implementation until the amendment is explicitly approved and rebound.

## 10. Reject work or request rollback planning

**Use this when:** You do not accept the current diff and want a safe recovery
proposal.

**What to provide:** The rejected increment, reasons, work that must be
preserved, and whether you want a revised plan or a rollback proposal.

**Example:**

```text
$implementing-staged-plans

Reject the current LIBRARY-001 INC-002 diff because it changes the public search
contract. Preserve all pre-existing work. Produce a read-only rollback and
replanning proposal, including affected evidence and recovery risks. Do not
discard, reset, restore, or overwrite files.
```

**What happens next:** The skill records or proposes the change-requested path
and inspects recovery options without assuming destructive authority.

**Where it stops:** Before any rollback, file restoration, or replacement. You
choose and authorize the exact recovery action separately.

## 11. Continue in the same suitable conversation

**Use this when:** The persisted mode is `approval:full`, an increment has been
accepted, and the same conversation still has enough context and authority to
continue.

**What to provide:** The current state, accepted packet, next increment, and a
request to revalidate suitability before continuation.

**Example:**

```text
$implementing-staged-plans

Revalidate LIBRARY-001 after accepted INC-002. If approval:full remains valid in
this conversation and the exact dependent INC-003 brief, plan, workspace, and
action authority all match, advance the next legal action. Otherwise stop and
tell me what must be renewed.
```

**What happens next:** The skill checks the repository and controlling records
again. Automatic continuation applies only inside a still-suitable conversation
and never bypasses a hard stop.

**Where it stops:** At any stale binding, new user-owned decision, hard stop, or
action outside the recorded authorization.

## 12. Resume in a new conversation

**Use this when:** Work has moved to a new conversation, even if the earlier run
used `approval:full`.

**What to provide:** The manifest, validated brief, handoff, workspace, and
explicit renewed authority for the requested increment.

**Example:**

```text
$implementing-staged-plans

Resume LIBRARY-001 from implementation-programs/LIBRARY-001/manifest.json using
the exact accepted handoff and brief for INC-003. Treat them as navigation only.
Revalidate the repository and all bindings, then use this message as renewed
authority to orient to INC-003 and stop before any ungranted write.
```

**What happens next:** The skill independently validates the brief and handoff
against current state rather than trusting their summary.

**Where it stops:** If the new-conversation authorization, any digest, repository
observation, or navigation artifact does not match.

## 13. Reconcile and close a completed program

**Use this when:** Every planned increment has been accepted and the whole
program is ready for final accounting.

**What to provide:** The manifest, all accepted increment evidence, known
deferrals, program-level verification, and any remaining risks.

**Example:**

```text
$implementing-staged-plans

Reconcile completed program LIBRARY-001. Account for every requirement,
amendment, accepted increment, material finding, deferral, and residual risk.
Run only authorized local verification, prepare the reconciliation and closure
packet, and stop for explicit program-closure approval.
```

**What happens next:** The skill checks complete traceability, fresh
program-level evidence, and the required architecture, documentation,
operations, and recovery reassessments.

**Where it stops:** At `awaiting-closure-approval`. Final-increment acceptance is
not program closure, and closure approval grants no later action.

## 14. Authorize one later action

**Use this when:** The relevant increment or program decision is accepted and
you want to consider a commit, pull request, release, deployment, publication,
or another consequential action.

**What to provide:** One exact action, its scope, the accepted packet or closure
record, and any required recovery evidence.

**Example:**

```text
$implementing-staged-plans

Authorize only the commit described in the accepted packet for INC-002.
Do not push, create a pull request, publish, release, deploy, or begin INC-003.
```

**What happens next:** The skill decides whether a current, non-revoked grant
matches that exact action and scope. Approval of the implementation diff is not
used as a substitute.

**Where it stops:** After the one authorized decision or action. Every excluded
action remains unauthorized.

## 15. Handle an incomplete, stale, or contradictory request

**Use this when:** You suspect the prompt, handoff, program records, or repository
state may disagree.

**What to provide:** Whatever locator you have and a request for read-only
diagnosis.

**Example:**

```text
$implementing-staged-plans

Orient read-only to LIBRARY-001. The handoff says INC-002 is accepted, but I am
not sure the current branch or head still matches. Compare the persisted state
with fresh repository facts, name every material contradiction, and return only
the smallest legal next action.
```

**What happens next:** The skill treats the prompt and handoff as navigation,
checks current repository facts and persisted authority, and separates verified
facts from uncertainty.

**Where it stops:** At the first unresolved ambiguity, stale digest,
contradiction, active Git operation, or missing authorization. It does not invent
records to make the state appear complete.

