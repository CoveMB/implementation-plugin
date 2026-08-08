# Implementing Staged Plans — Bootstrap, Execution, and Review Runbook

**Date:** 2026-08-08  
**Status:** Operational companion to the approved consolidated design  
**Canonical design:** `implementing-staged-plans-consolidated-design-plan-final.md`

## 1. Purpose of this companion

The canonical design defines the skill's architecture, state model, workflow, approval modes, implementation sequence, review model, and lean increment-brief format. It intentionally does not prescribe repository-specific files before the target repository is inspected.

This companion supplies the missing operator layer:

- a bootstrap prompt for starting implementation before the skill exists;
- a program-approval and workspace-selection prompt;
- lean copy-ready briefs for all eight implementation increments;
- a consistent way to review and accept or reject each increment;
- same-thread and new-thread continuation prompts;
- closure and draft-pull-request prompts.

The companion is not a second source of workflow policy. Where it conflicts with the canonical design or the approved repository-specific implementation program, the canonical design and approved program control.

## 2. What “step by step” means here

There are three planning levels:

1. **Canonical design:** stable outcomes, invariants, state rules, review rules, and authority boundaries.
2. **Implementation program:** the repository-informed sequence of eight coherent increments and their acceptance criteria.
3. **Exact-file plan:** the just-in-time file, interface, test, command, and commit plan for the current increment only.

The eight increments below are the program-level steps. An exact-file implementation plan for all eight increments should not be written in advance because repository evidence may invalidate distant assumptions. The current increment receives its exact-file plan only after fresh repository inspection.

## 3. Recommended operating mode

Use `approval:full-increment` while building the skill.

Under this mode, the agent may prepare, plan, implement, commit, review, remediate, and verify one increment without routine interruption. It then stops with the completed diff and review packet for human acceptance. It cannot begin the next increment from the same authorization.

Use `approval:standard` instead when you also want to approve the exact-file plan before code changes. Avoid `approval:full-diff` and `approval:full` during the initial implementation unless you deliberately want to reduce or remove the per-increment human diff gate.

## 4. End-to-end operating flow

1. Submit **Prompt 0** with the canonical design and target repository.
2. Review the proposed implementation program and workspace recommendation.
3. Approve the program revision and select the writable workspace.
4. Submit the appropriate lean increment brief under `approval:full-increment`.
5. Review the resulting review packet and diff.
6. Accept, request changes, ask questions, reject, or propose a program amendment.
7. After acceptance, obtain or submit the next increment brief.
8. Repeat through Increment 8.
9. Run program closure as a separate stage.
10. Only after closure approval, decide whether to create a draft pull request.

---

# Part I — Starting the implementation

## 5. Prompt 0 — Read-only bootstrap and proposed implementation program

Use this before any implementation work. Replace the placeholders and attach or reference the canonical design.

```markdown
Treat `implementing-staged-plans-consolidated-design-plan-final.md` as the canonical design for the `implementing-staged-plans` skill.

Target repository: `<repository URL or local path>`

Inspect the actual repository read-only. Review its instructions, current structure, existing skills, manifests, tests, validators, scripts, documentation conventions, recent relevant commits, and any prior work related to this skill.

From that evidence, propose a repository-specific implementation program that:

- accounts for every requirement and invariant in the canonical design;
- retains the eight outcome-oriented increments unless repository evidence justifies a better reviewable decomposition;
- keeps distant technical details provisional;
- identifies dependencies, integration checkpoints, acceptance criteria, risks, and likely validation strategy;
- identifies any direct contradiction or genuinely blocking uncertainty;
- recommends the writable branch/worktree strategy and explains why.

Do not modify the repository, create a branch or worktree, or begin implementation. Return the proposed program revision, requirement coverage summary, repository-specific risks, workspace recommendation, and the exact next approval needed from me.
```

### What to review in the bootstrap response

Confirm that:

- all canonical design areas have a disposition;
- the eight increments remain coherent and independently reviewable;
- repository-specific conventions were actually inspected rather than guessed;
- distant file-level details remain provisional;
- the workspace recommendation protects existing user work;
- contradictions, assumptions, and uncertainty are clearly separated.

## 6. Program approval and workspace-selection prompt

Use this after reviewing Prompt 0's response.

```markdown
I approve implementation program `<program-id>` revision `<revision>` as the governing program for implementing the canonical design.

Use this writable workspace:

- repository: `<repository identity>`
- strategy: `<isolated worktree / new branch in current tree / named branch / current branch>`
- branch: `<branch name>`
- base: `<base branch or commit>`
- path, when applicable: `<worktree path>`

Initialize and persist the source snapshot, approved program, traceability, state, and workspace records without changing the approved semantics.

Then execute `INC-001 — Baseline pressure suite and minimal front door` under `approval:full-increment` using the brief below. Because the skill is not yet self-hosting, apply the canonical increment lifecycle directly and identify which safeguards are manual versus mechanically implemented. Stop with the completed Increment 1 review packet and diff for my approval.
```

If you want to approve the program but review the Increment 1 exact-file plan before code, replace the final paragraph with:

```markdown
Prepare and persist the exact-file plan for `INC-001` under `approval:standard`, then stop for my plan approval before modifying production files.
```

---

# Part II — Lean implementation briefs

## 7. Brief rules

Each brief identifies the semantic work. The canonical workflow governs repository inspection, exact-file planning, testing, commits, review, remediation, verification, packet construction, and stopping behavior.

Replace `<program-id>` and `<revision>` with the approved values. Requirement identifiers and acceptance criteria should normally be loaded from the persisted implementation program rather than repeated in the prompt.

Until the skill can mechanically enforce every relevant stage, the implementing agent must apply the still-unimplemented portions of the canonical workflow manually and disclose that limitation in the review packet.

## 8. Increment 1 brief — Baseline pressure suite and minimal front door

```markdown
Resume `<program-id>` revision `<revision>` and execute `INC-001 — Baseline pressure suite and minimal front door` under `approval:full-increment`.

**Outcome:** Establish representative control failures and add the smallest valid skill entry point, invariant gates, capability discovery, and stage routing.
**Advances:** The requirements assigned to `INC-001` in the approved program.
**Acceptance:** The approved `INC-001` criteria, including preserved baseline failures, package discoverability, refusal of illegal early actions, and no false claim that later subsystems already exist.
**Context:** This is a bootstrap increment. Apply workflow safeguards not yet implemented in the skill directly and identify them as manual controls.

Use the persisted program, selected workspace, and current handoff as authority. Execute through the canonical staged workflow.
```

## 9. Increment 2 brief — Immutable source capture, decomposition, and traceability

```markdown
Resume `<program-id>` revision `<revision>` and execute `INC-002 — Immutable source capture, decomposition, and traceability` under `approval:full-increment`.

**Outcome:** Register immutable source plans, extract complete requirements, create outcome-oriented implementation programs, support progressive elaboration, and require initial program approval.
**Advances:** The requirements assigned to `INC-002` in the approved program.
**Acceptance:** The approved `INC-002` criteria, including complete requirement disposition, source-digest integrity, program revisioning, and a decomposition pilot without project-specific policy leakage.
**Context:** Preserve source evidence exactly while allowing derived program structure to evolve through explicit revisions.

Use the persisted program, selected workspace, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

## 10. Increment 3 brief — Durable state, approval modes, and action authorization

```markdown
Resume `<program-id>` revision `<revision>` and execute `INC-003 — Durable state, approval modes, and action authorization` under `approval:full-increment`.

**Outcome:** Implement separate program and increment state, legal transitions, approval binding, all five approval modes, the workspace-selection gate, and separate consequential-action authorization.
**Advances:** The requirements assigned to `INC-003` in the approved program.
**Acceptance:** The approved `INC-003` criteria, including complete state and approval-mode matrices, stale-approval rejection, and proof that no mode implies pull-request, merge, release, deployment, migration, or external-state authority.
**Context:** Retain only state that enforces a real invariant or materially improves recovery, review, or traceability.

Use the persisted program, selected workspace, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

## 11. Increment 4 brief — Repository preparation, evidence, shaping, and exact-file planning

```markdown
Resume `<program-id>` revision `<revision>` and execute `INC-004 — Repository preparation, evidence, increment shaping, and exact-file planning` under `approval:full-increment`.

**Outcome:** Revalidate repository truth, protect user work, classify drift, collect applicable evidence, refine provisional increment shape, and create just-in-time exact-file plans.
**Advances:** The requirements assigned to `INC-004` in the approved program.
**Acceptance:** The approved `INC-004` criteria, including dirty-state and drift fixtures, evidence-applicability records, reusable-code discovery, bounded plan amendments, and reviewability checks.
**Context:** Repository-native mechanisms may replace provisional design assumptions when approved outcomes and obligations remain intact.

Use the persisted program, selected workspace, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

## 12. Increment 5 brief — Execution discipline, amendments, commits, and recovery

```markdown
Resume `<program-id>` revision `<revision>` and execute `INC-005 — Execution discipline, amendments, focused commits, and recovery` under `approval:full-increment`.

**Outcome:** Implement meaningful test-first slices and alternative verification, bounded technical-approach autonomy, ownership boundaries, focused commits, amendment classification, and distinct recovery domains.
**Advances:** The requirements assigned to `INC-005` in the approved program.
**Acceptance:** The approved `INC-005` criteria, including observed-red evidence where applicable, accurate non-TDD verification, no unrelated cleanup, and correct separation of implementation amendments from program amendments.
**Context:** Prefer the smallest sufficient repository-native approach. Technical elegance alone does not justify changing approved semantics.

Use the persisted program, selected workspace, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

## 13. Increment 6 brief — Reviews, remediation, verification, and packets

```markdown
Resume `<program-id>` revision `<revision>` and execute `INC-006 — Reviews, remediation, verification, and review packets` under `approval:full-increment`.

**Outcome:** Implement required review scopes, specialist-review predicates, truthful independence handling, material-finding contracts, remediation loops, fresh verification, and review-packet validation.
**Advances:** The requirements assigned to `INC-006` in the approved program.
**Acceptance:** The approved `INC-006` criteria, including preserved raw reviews, evidence-backed finding classification, repaired material findings, rerun evidence, and packets that support efficient human review.
**Context:** When independent dispatch is unavailable, use and disclose separate non-independent review passes rather than claiming independence.

Use the persisted program, selected workspace, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

## 14. Increment 7 brief — Lean prompts, continuity, closure, and authority gates

```markdown
Resume `<program-id>` revision `<revision>` and execute `INC-007 — Lean prompt generation, continuity, closure, and authority gates` under `approval:full-increment`.

**Outcome:** Generate minimal briefs from persisted state, create durable handoffs, revalidate on resume, manage full-mode continuation, reconcile programs, require closure approval, and gate draft pull requests and later consequential actions.
**Advances:** The requirements assigned to `INC-007` in the approved program.
**Acceptance:** The approved `INC-007` criteria, including prompt minimality and completeness, stale-brief rejection, cross-conversation renewal, closure reconciliation, and correct draft-pull-request timing.
**Context:** Prompts and handoffs are navigation evidence; persisted program state and current repository truth remain authoritative.

Use the persisted program, selected workspace, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

## 15. Increment 8 brief — Integrated hardening and release pilot

```markdown
Resume `<program-id>` revision `<revision>` and execute `INC-008 — Integrated pressure hardening and release pilot` under `approval:full-increment`.

**Outcome:** Run combined pressure, crash/resume, schema-evolution, repository-backed pilot, packaging, documentation, and concision checks; repair only demonstrated material gaps.
**Advances:** The requirements assigned to `INC-008` in the approved program.
**Acceptance:** The approved `INC-008` criteria, including full-suite results, complete pilot artifacts, no duplicated prompt policy, no broken references, and closure-readiness evidence.
**Context:** Closure exercised in an isolated pilot applies only to that pilot. Do not close the skill's own implementation program during this increment.

Use the persisted program, selected workspace, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

---

# Part III — Reviewing each increment

## 16. Required endpoint of every increment

For `approval:full-increment`, the agent should stop with:

1. the achieved outcome and requirement coverage;
2. the changed files and focused commits;
3. a recommended human review order;
4. exact verification commands and exact results;
5. baseline failures separated from introduced failures;
6. test-first evidence or an explicit alternative verification contract;
7. requirements, architecture, and test-evidence review reports;
8. relevant specialist reviews;
9. findings, repairs, and rerun evidence;
10. deviations and implementation amendments;
11. unresolved design judgments, edge cases, risks, and deferrals;
12. rollback and any data, deployment, or provider recovery considerations;
13. current persisted state and the next legal action.

A statement such as “all tests pass” without exact commands, scope, and results is not a sufficient review packet.

## 17. Human review sequence

Review in this order:

### Gate 1 — Outcome and scope

- Does the increment deliver its stated outcome?
- Is every assigned requirement implemented, explicitly deferred, or otherwise accounted for?
- Did the diff add unrelated scope or silently alter a protected contract?

### Gate 2 — Design and implementation approach

- Does the approach follow repository-native conventions?
- Is complexity justified by current requirements rather than speculative extensibility?
- Did any technical amendment actually change program semantics, risk, sequencing, or user-visible behavior?

### Gate 3 — Evidence and tests

- Are failing-test claims backed by observed failure for the intended reason?
- Do the exact commands and results support the completion claim?
- Are baseline failures clearly distinguished from regressions?
- Were affected broader checks rerun after repairs?

### Gate 4 — Review quality

- Were requirements, architecture, and test evidence reviewed separately?
- Are specialist reviews included only where relevant?
- Is reviewer independence described accurately?
- Are material findings evidence-backed and dispositioned?

### Gate 5 — Risk and recovery

- Are remaining uncertainties, edge cases, and deferred work explicit?
- Is source rollback credible?
- For stateful or external changes, are data, deployment, and provider recovery separately addressed?

### Gate 6 — Repository state and next action

- Do the branch, worktree, base, head, and commit range match the reviewed diff?
- Is the increment still awaiting acceptance rather than already treated as accepted?
- Is the proposed next action legal under the current approval mode?

## 18. Acceptance prompt — accept and stop before the next increment

This is the safest default response.

```markdown
I accept the diff and review packet for `<increment-id>` at head `<commit>` under program `<program-id>` revision `<revision>`.

Persist the acceptance, update traceability and current state, and preserve the accepted packet as immutable. Do not begin the next increment.

Generate the lean brief for the next legal increment and recommend whether it should run in this conversation or a new one, with the reason for that recommendation.
```

## 19. Acceptance prompt — accept and immediately authorize the next increment

Use this only when the current conversation remains a clean context and you have reviewed the prior increment.

```markdown
I accept the diff and review packet for `<current-increment>` at head `<commit>` under program `<program-id>` revision `<revision>`.

Persist that acceptance. Then execute `<next-increment> — <title>` under `approval:full-increment` using its generated lean brief and the current persisted state. Stop with the next increment's completed review packet and diff.
```

## 20. Question-only prompt — hold the diff without changing it

```markdown
Keep `<increment-id>` in `awaiting-diff-approval`. Do not modify the repository, accept the diff, or begin another increment.

Answer these review questions using the diff, review packet, and persisted evidence:

1. `<question>`
2. `<question>`

Separate verified facts, inference, uncertainty, and recommendation.
```

## 21. Change-request prompt — repair the current increment

```markdown
I do not accept `<increment-id>` yet.

Address only these review findings:

1. `<finding with file, requirement, or evidence reference>`
2. `<finding>`

Reopen the current increment without broadening its approved outcome. Amend the exact-file plan when necessary, record any deviation, implement the smallest justified repair, rerun affected reviews and verification, update the review packet, and stop again for diff approval.

Do not begin the next increment.
```

## 22. Program-amendment prompt

Use this when the requested correction changes requirements, acceptance criteria, user-visible behavior, protected contracts, risk posture, ownership, irreversible behavior, or material sequencing.

```markdown
Do not treat this as a technical implementation correction.

Propose a program amendment for `<program-id>` revision `<revision>` covering:

- requested semantic change: `<change>`
- reason: `<reason>`
- affected requirements and acceptance criteria: `<references>`
- affected increments, dependencies, risks, and prior approvals: `<references>`

Preserve the current repository and program state. Produce the proposed new program revision and its consequences, then stop for my approval before further implementation.
```

## 23. Rejection or rollback-planning prompt

```markdown
I reject the current `<increment-id>` diff. Do not begin another increment and do not perform rollback automatically.

Preserve the review artifacts and current repository state. Explain the smallest safe options to:

1. revise the increment in place;
2. revert the increment's source changes;
3. recover any data, deployment, provider, or external state affected by the increment.

Recommend one option with evidence and stop for explicit authorization.
```

## 24. Accepting a known deferral

Do not silently accept a material unresolved issue. Record it explicitly.

```markdown
I accept `<increment-id>` with this explicit deferral:

- deferred item: `<item>`
- affected requirement or risk: `<reference>`
- owner: `<owner>`
- intended resolution point: `<increment, issue, or date>`
- accepted consequence: `<consequence>`

Persist the acceptance and deferral in traceability and the review packet. Do not begin the next increment. Generate the next lean brief and identify whether the deferral blocks any later work or closure.
```

---

# Part IV — Continuing in another conversation

## 25. New-conversation resume prompt

Prefer the generated handoff and brief. Use this wrapper when starting a fresh conversation.

```markdown
Resume implementation program `<program-id>` revision `<revision>` in repository `<repository>`.

Authoritative navigation artifacts:

- current handoff: `<path>`
- current status: `<path>`
- approved program: `<path>`
- selected workspace record: `<path>`
- latest accepted review packet: `<path>`
- next increment brief: `<path or pasted brief>`

Independently revalidate the actual repository, branch/worktree, base/head commits, working-tree state, and legal next transition before relying on the handoff.

Execute the supplied next increment brief under its stated approval mode through the canonical staged workflow. Do not infer authority from the prior conversation beyond what the persisted approval and the submitted brief validly authorize.
```

If the generated brief retains `approval:full`, submitting it in the new conversation renews that conversational instruction. Persisted state alone does not transfer it.

---

# Part V — Program closure and pull request

## 26. Closure prompt

Use only after Increment 8 has been explicitly accepted.

```markdown
Resume `<program-id>` revision `<revision>` after acceptance of `INC-008`. Enter program-closure mode; this is not another implementation increment.

Revalidate the repository, workspace, base/head commits, immutable source plan, approved program revision, all accepted increment packets, traceability, decisions, amendments, deferrals, current tests, and closure-readiness evidence.

Reconcile every authoritative requirement and approved amendment. Verify that later changes did not invalidate earlier accepted increments. Run the required program-level integration, structural, packaging, pressure, resume, and repository-backed verification. Reassess architecture, documentation, operations, and recovery.

Do not add feature work during closure. If a material gap remains, identify the affected requirement and increment, preserve a blocked closure state, recommend the smallest reopening plan, and stop.

Otherwise produce the program-closure packet with complete requirement dispositions, exact verification results, unresolved accepted risks, deferrals and owners, recovery considerations, and the final commit range. Stop for explicit closure approval. Do not create a draft pull request.
```

## 27. Closure-approval prompt

```markdown
I approve closure of program `<program-id>` revision `<revision>` at head `<commit>` based on the program-closure packet `<path or identifier>`.

Persist the closed state and immutable closure packet. Do not create a pull request yet. Ask me separately whether to create a draft pull request, stating the proposed base branch, head branch, title, and summary.
```

## 28. Draft-pull-request authorization prompt

```markdown
Create the proposed draft pull request from `<head branch>` to `<base branch>` using the approved closure packet as the factual basis for its description.

Do not merge, release, deploy, migrate production data, perform destructive operations, or modify consequential external state. Report the created draft pull request and any failure or uncertainty accurately.
```

---

# Part VI — Minimal operator checklist

For each increment, verify that the sequence is:

```text
approved program
  -> authorized workspace
  -> lean increment brief
  -> repository revalidation
  -> just-in-time exact-file plan
  -> implementation in verifiable slices
  -> required reviews
  -> material repairs
  -> fresh verification
  -> review packet
  -> explicit acceptance or change request
```

Never treat these as equivalent:

- an accepted increment and a closed program;
- a passing test and valid test-first evidence;
- a self-review and an independent review;
- a Git revert and complete external-state recovery;
- a lean prompt and permission to change approved semantics;
- `approval:full-increment` and permission to begin the next increment;
- closure approval and permission to create, merge, release, or deploy without a separate action decision.

## 29. Expected generated artifacts after the workflow is implemented

Once Increment 7 is accepted, the skill should normally generate rather than require manual composition of:

- the next lean increment brief;
- the same-thread versus new-thread recommendation;
- the durable handoff;
- the closure invocation when all increments are accepted;
- the separate draft-pull-request question after closure.

Before those capabilities exist, use this companion as the bootstrap operator interface.
