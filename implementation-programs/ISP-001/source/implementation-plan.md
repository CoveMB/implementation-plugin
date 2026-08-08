# Implementing Staged Plans — Consolidated Design Plan

**Date:** 2026-08-07  
**Status:** Proposed consolidated design for approval  
**Scope:** Architecture and behavior of the `implementing-staged-plans` skill. This is not an exact-file implementation plan for a specific repository.  
**Source basis:** Consolidates the strongest elements of the prior proposed design and copy-ready increment prompts, with a revised lean-prompt model.

---

## 1. Purpose

The skill receives an authoritative implementation plan and turns it into a persistent, reviewable implementation program. It then prepares, implements, reviews, verifies, and hands off one coherent increment at a time without silently changing requirements, relying on chat history as authoritative state, or inferring permission for consequential actions.

The design optimizes for:

- fidelity to the approved source plan;
- repository-informed progressive elaboration;
- coherent increments that remain practical to review;
- explicit human approval and action-authority boundaries;
- repository integrity and reversibility;
- evidence-backed implementation choices;
- test-first implementation where meaningful;
- independent review where available and honest fallback where not;
- useful human review packets rather than command logs;
- reliable continuation across conversations;
- explicit program-wide reconciliation and closure;
- enough agent discretion to select the best implementation approach after inspecting repository reality;
- minimal duplication between the workflow and the prompts that invoke it.

---

## 2. Central design decision

Use a **layered skill with durable repository artifacts and validators**.

A small front door determines the current lifecycle stage and routes to focused procedures. Repository artifacts hold the authoritative source snapshot, approved program, state, approvals, evidence, increment plans, reviews, packets, and handoffs. Validators enforce the invariants that should not depend on an agent remembering prose.

The invocation prompts are deliberately thin. They identify the work to advance and point to the persisted program; they do not restate the workflow. Inspection, exact-file planning, testing, review, remediation, verification, packet construction, stopping behavior, and action gates are responsibilities of the skill itself.

This separates three concerns:

1. **Program semantics:** what outcome and requirements must be delivered.
2. **Execution protocol:** how implementation is prepared, governed, reviewed, and accepted.
3. **Invocation brief:** which approved increment should now be advanced.

The implementation brief should be **procedurally thin but semantically bounded**. Removing repeated procedural rules improves agent judgment and reduces prompt drift. Removing the outcome, requirements, acceptance criteria, or material exclusions would instead create uncontrolled scope expansion. The design therefore favors lean prompts, not boundary-free prompts.

---

## 3. Terminology

### 3.1 Source plan

The original implementation plan supplied by the user. It is preserved as immutable evidence.

### 3.2 Implementation program

The approved repository-backed decomposition of the source plan into requirements, dependencies, outcome-oriented parts, provisional increments, acceptance criteria, risks, and integration checkpoints.

### 3.3 Increment

A coherent review and acceptance unit that advances a bounded outcome. Program increments are provisional until prepared against the current repository.

### 3.4 Implementation slice

A smaller test-first or otherwise verifiable change within an increment. Slices may produce focused commits without requiring separate user approval unless the selected mode or a hard stop requires it.

### 3.5 Increment brief

A lean invocation artifact identifying the current increment, outcome, requirements, acceptance criteria, approval mode, and relevant handoff. It does not prescribe exact files or repeat the canonical workflow.

### 3.6 Exact-file plan

The just-in-time implementation contract produced after current repository inspection. It describes the files, interfaces, tests, commands, commit boundaries, review needs, risks, and recovery considerations for the current increment.

### 3.7 Implementation amendment

A bounded change to the technical approach, file plan, or internal sequencing that preserves the approved outcome, requirements, contracts, risk posture, and user-visible behavior.

### 3.8 Program amendment

A change to approved scope, requirements, acceptance criteria, user-visible behavior, security or privacy obligations, protected contracts, data ownership, irreversible behavior, or material sequencing.

### 3.9 Review packet

The durable human handoff explaining what changed, why, how it was verified, what reviewers found, what remains uncertain, and how to inspect or recover.

### 3.10 Handoff

A durable continuation record used when resuming later or moving to another conversation. It is navigation evidence, not a substitute for repository revalidation.

---

## 4. Authority model

Different forms of authority govern different questions. A single undifferentiated precedence list would be misleading.

### 4.1 Requirements authority

Requirements come from:

1. the immutable source plan;
2. explicit user decisions and approved program amendments;
3. the currently approved implementation-program revision.

The implementation program may normalize and organize requirements but cannot silently replace them.

### 4.2 Repository truth

The actual repository, selected workspace, branch, commits, manifests, tests, configuration, and current working-tree state are authoritative for implementation reality. A stale plan or handoff cannot override current repository evidence.

### 4.3 Operational state

Persisted program artifacts are authoritative for lifecycle state, accepted increments, approvals, amendments, unresolved findings, and next legal actions. Chat memory and generated prompts are navigation aids only.

### 4.4 Implementation decisions

Ordinary technical decisions are resolved from:

- the approved program;
- current repository evidence and established conventions;
- current official documentation or advisories where materially relevant;
- accepted engineering practice;
- the smallest sufficient and reversible approach.

### 4.5 Safety and action authority

Approval modes never override repository-integrity gates, hard stops, or the requirement for separate authorization of consequential actions.

Supporting capabilities may assist the workflow but cannot change its approval, state, or authority rules.

---

## 5. Architectural principles

1. **The source plan is immutable evidence.** Derived artifacts may interpret it but never rewrite it in place.
2. **Repository artifacts, not chat history, hold operational state.**
3. **Program planning and increment planning occur at different levels.** Distant work remains outcome-oriented; exact files are selected just in time.
4. **Prompts activate the workflow; they do not define it.**
5. **Semantic boundaries remain explicit.** Lean prompts still identify outcome, requirements, acceptance, and material constraints.
6. **Implementation discretion is evidence-bounded.** Agents may choose or amend the internal approach while preserving approved obligations.
7. **Approval and consequential-action authorization are separate.**
8. **Each increment is transactional.** Preparation, planning, implementation, review, remediation, verification, packet creation, and acceptance form one bounded cycle.
9. **State transitions are explicit and validated.**
10. **Repository and user work are protected.** No silent stash, reset, discard, restore, overwrite, or incorporation.
11. **Evidence is applicability-bound.** Previously gathered evidence may be reused only when versions, assumptions, and configurations still match.
12. **Review independence is represented truthfully.** Separate self-review passes are not labelled independent.
13. **Testing claims require observed evidence.** Passing tests written after implementation cannot be represented as prior failing-test evidence.
14. **The smallest sufficient implementation is preferred.** Avoid speculative architecture and unrelated cleanup.
15. **State exists only to enforce real invariants.** Avoid ornamental workflow machinery.
16. **Project-facing artifacts use generic role names.** Internal tool or capability names do not leak into them.
17. **Closure is separate from accepting the final increment.**
18. **Draft pull requests and later actions require separate, timely authorization.**

---

## 6. System overview

```text
Authoritative implementation plan
        |
        v
Immutable source registration
        |
        v
Read-only repository-informed decomposition
        |
        v
Persistent implementation program + traceability
        |
        v
Explicit program approval
        |
        v
Writable workspace selection
        |
        v
Lean increment brief
        |
        v
+----------------------------------------------------------------+
| Canonical increment workflow                                   |
|                                                                |
| Load state and revalidate repository truth                     |
|     -> assess or refine increment shape                        |
|     -> collect applicable evidence                             |
|     -> create just-in-time exact-file plan                     |
|     -> apply approval mode                                     |
|     -> implement in focused, verifiable slices                 |
|     -> run required and specialist reviews                     |
|     -> remediate evidence-backed material findings             |
|     -> perform fresh verification                              |
|     -> produce human review packet                             |
|     -> accept, request changes, block, or supersede            |
|     -> continue or create durable handoff                      |
+----------------------------------------------------------------+
        |
        v
Program-wide reconciliation and integration verification
        |
        v
Program-closure packet and explicit closure approval
        |
        v
Separate question about draft pull-request creation
```

Cross-cutting controls:

- requirement traceability;
- state, approval, and action authorization;
- workspace and user-work integrity;
- evidence applicability;
- amendment and drift classification;
- rollback and external-state recovery;
- capability discovery and fallback procedures;
- schema and invariant validation;
- prompt and handoff generation.

---

## 7. Major components

The following are logical responsibilities. They do not require one physical file or module each. The target repository’s conventions should determine the final package structure.

### 7.1 Entry router

**Responsibility:** Read persisted state and determine the next legal lifecycle action.

**Inputs:** user request, repository identity, program manifest, current state, approval mode, action authorizations.

**Outputs:** applicable procedure, next legal action, and any mandatory stop.

**Invariant:** phrasing in a user prompt cannot bypass an illegal transition or absent authorization.

### 7.2 Source registrar and program decomposer

**Responsibility:** Preserve the source plan, assign stable requirement identifiers, inspect repository reality read-only, and derive an implementation program.

The program records:

- normalized requirements and source locations;
- outcome-oriented parts and tasks;
- provisional increments;
- dependencies and integration checkpoints;
- acceptance criteria;
- risks and uncertainty;
- sequencing and parallelism constraints;
- decisions, assumptions, and unresolved questions;
- complete traceability.

Distant increments remain high-level. Exact files, symbols, commands, and test slices are deferred until preparation.

### 7.3 Program and traceability manager

**Responsibility:** Maintain the approved program revision and account for every source requirement through implementation and closure.

It prevents sampled or partial extraction from being labelled complete and prevents unallocated requirements from passing closure.

### 7.4 State, approval, and action-authorization engine

**Responsibility:** Maintain legal program and increment states, bind approvals to the correct source/program/workspace/scope, interpret approval modes, and keep consequential actions separately authorized.

It rejects:

- implementation before program approval;
- repository modification before workspace selection;
- production changes before a valid current-increment plan;
- diff acceptance before review, remediation, and fresh verification;
- continuation under a one-increment mode;
- closure without a closure packet and explicit approval;
- inferred authority for pull requests, merges, releases, deployments, migrations, destructive actions, or provider changes.

### 7.5 Workspace and repository-integrity guard

**Responsibility:** Identify the implementation workspace and protect user work.

It records:

- repository identity;
- worktree path and branch;
- selected base and current head;
- staged, modified, untracked, and conflicted paths;
- active Git operations;
- relevant divergence or branch movement;
- managed, generated, application-owned, and user-owned boundaries.

It never silently stashes, resets, discards, restores, overwrites, or commits pre-existing user work.

### 7.6 Increment preparation and evidence registry

**Responsibility:** Revalidate repository truth and applicable external evidence before the increment is planned.

Preparation covers:

- repository instructions and architecture records;
- relevant recent commits and accepted prior packets;
- manifests, lockfiles, runtimes, configuration, and provider bindings;
- current tests and baseline failures;
- reusable existing code and patterns;
- current official documentation, compatibility information, and advisories for materially touched surfaces.

Evidence records include source, access date, version/configuration applicability, claims supported, risk domain, reuse basis, and remaining uncertainty.

### 7.7 Increment shaper and exact-file planner

**Responsibility:** Translate the program’s provisional increment into the best current implementation contract.

The component may:

- refine the internal sequence;
- split the increment into smaller implementation slices;
- adjust file boundaries or test strategy;
- choose a repository-native mechanism instead of a provisional design assumption;
- propose a narrower increment if the original unit is not safely reviewable;
- identify when a requested combination should instead be separated.

The exact-file plan normally contains:

- bounded outcome and requirements advanced;
- current acceptance criteria;
- files to create, modify, move, or delete;
- responsibilities and interfaces;
- test-first slices or alternative verification contracts;
- commands and expected evidence;
- relevant documentation and evidence updates;
- focused commit boundaries;
- required review scopes and specialist predicates;
- rollback and recovery domains;
- exclusions, risks, and recorded amendments.

The exact-file plan is a local implementation contract, not an immutable product specification. It may be amended through the defined policy when repository evidence invalidates the anticipated approach.

### 7.8 Execution controller

**Responsibility:** Implement the authorized increment using the current exact-file plan and approved amendment rules.

For behavior changes, the normal loop is:

1. add a focused test;
2. run it and observe the expected failure for the intended reason;
3. implement the minimum sufficient production change;
4. rerun focused and required broader checks;
5. refactor only while green;
6. commit at a coherent boundary.

For documentation, packaging, configuration, or declarative changes where a failing behavioral test is artificial, the plan defines an alternative verification contract.

The controller searches for reusable code before adding abstractions, preserves ownership boundaries, avoids unrelated cleanup, and records deviations immediately.

### 7.9 Amendment, drift, and recovery classifier

**Responsibility:** Distinguish ordinary corrections, bounded implementation amendments, program amendments, authoritative contradictions, repository drift, and recovery domains.

It also distinguishes:

- source-code rollback;
- persistent-data recovery;
- deployment rollback;
- provider or external-state recovery.

A Git revert is not represented as complete recovery for external state.

### 7.10 Review and verification coordinator

**Responsibility:** Run distinct review scopes for:

- requirements and accepted-scope compliance;
- architecture, boundaries, and unnecessary complexity;
- test adequacy and evidence validity.

It selects additional review scopes from observable risk predicates, including security/privacy, persistent data, migrations, accessibility, platform/deployment, concurrency/reliability, public APIs, payments, performance, and consequential external state.

Independent reviewers are used when available. Otherwise, separate focused self-review passes are run, recorded before reconciliation, and explicitly labelled non-independent with reduced assurance.

### 7.11 Review-packet builder

**Responsibility:** Produce a human-review handoff rather than a transcript or command log.

It explains what changed, why, where to inspect, which requirements advanced, what evidence exists, what reviewers found, which findings were repaired, what remains uncertain, and how rollback or recovery would work.

### 7.12 Continuity, prompt-generation, and closure controller

**Responsibility:** Decide whether the current conversation remains a reliable implementation context, create durable handoffs, generate the next lean increment brief, revalidate on resume, reconcile the complete program, and enforce closure and later authority gates.

The prompt generator never recreates the full workflow in the prompt. It extracts only the current semantic work brief and navigation context from persisted artifacts.

---

## 8. Lean increment brief model

### 8.1 Role of the brief

The brief selects the work. The skill governs how the work is performed.

A good brief should let a fresh agent answer:

- Which approved program and revision am I resuming?
- Which outcome should advance now?
- Which requirements and acceptance criteria matter?
- What approval mode applies?
- Where is the current state and handoff?
- Are there any material constraints or unresolved risks specific to this increment?

It should not attempt to answer, before repository inspection:

- exactly which files must change;
- which internal architecture is best;
- which commands will be sufficient;
- how many commits or test slices are optimal;
- which specialist reviews will be triggered;
- whether the provisional increment should be internally split.

### 8.2 Required fields

Every generated increment brief contains:

1. program identifier and approved revision;
2. increment identifier and title;
3. intended outcome;
4. requirement identifiers advanced;
5. acceptance criteria or a pointer to their authoritative location;
6. approval mode;
7. workspace and handoff/status reference;
8. any unresolved user-owned decision already known to block preparation.

### 8.3 Optional fields

Include only when materially helpful:

- integration checkpoint;
- notable risk domain;
- explicit non-goal needed to prevent likely scope confusion;
- relevant approved design decision;
- reason the increment is sequenced now;
- known repository drift requiring revalidation.

### 8.4 Content intentionally omitted

Do not repeat in every prompt:

- full repository-inspection instructions;
- workspace-integrity rules;
- TDD procedures;
- evidence-refresh rules;
- review-role definitions;
- review-packet field lists;
- hard-stop catalogues;
- pull-request, merge, release, or deployment prohibitions;
- exact-file plans;
- fixed technical solutions that were only provisional;
- generic reminders to avoid unrelated work.

Those belong to the canonical workflow and validators.

### 8.5 Agent discretion

After loading the brief and persisted state, the agent may determine the best implementation approach from repository evidence. It may refine the exact files, tests, internal sequence, reusable abstractions, and commit structure.

It may autonomously split the increment into implementation slices. It may also narrow or reshape the current increment when doing so preserves the approved outcome, dependencies, acceptance criteria, risk posture, reviewability, and integration intent.

It may not silently:

- drop an assigned requirement;
- add unrelated product scope;
- change externally observable behavior outside the approved outcome;
- weaken security, privacy, accessibility, data, or compatibility obligations;
- change a protected public contract;
- merge increments in a way that materially reduces reviewability;
- reorder dependent work in a way that changes program risk or acceptance;
- treat a program amendment as a technical implementation detail.

### 8.6 Lean brief template

```markdown
Resume `<program-id>` revision `<revision>` and execute `<increment-id> — <title>` under `<approval-mode>`.

**Outcome:** <bounded outcome>
**Advances:** <requirement IDs or authoritative reference>
**Acceptance:** <criteria or authoritative reference>
**Context:** <only material increment-specific context, risk, or non-goal>

Use the persisted program, current workspace record, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

### 8.7 Example

```markdown
Resume `ISP-001` revision `3` and execute `INC-004 — Repository preparation, evidence, and just-in-time planning` under `approval:full-increment`.

**Outcome:** The workflow can safely prepare the next increment from current repository truth and produce an evidence-backed exact-file plan.
**Advances:** `REQ-041` through `REQ-058`.
**Acceptance:** Use the approved program criteria for `INC-004`.
**Context:** Preserve repository-native conventions; the physical artifact layout remains provisional until the repository is inspected.

Use the persisted program, selected workspace, and latest accepted handoff as authority. Execute through the canonical staged workflow.
```

The generated prompt should usually be close to this length. Additional operational instructions are evidence that the workflow itself is incomplete or not being loaded reliably.

---

## 9. Increment shaping and reviewability

The program decomposition defines provisional increments, not rigid file-level work packages. The current increment becomes concrete only during preparation.

### 9.1 Reviewable-increment criteria

An increment should normally:

- produce one coherent outcome;
- advance a traceable set of requirements;
- be understandable and reviewable as a unit;
- have a verification contract that can establish meaningful confidence;
- have coherent rollback or recovery boundaries;
- avoid combining materially unrelated risk domains unless integration itself is the outcome;
- avoid depending on safeguards that have not yet been implemented;
- leave the repository in a valid state.

No numeric line-count or file-count threshold is authoritative. Reviewability depends on coupling, risk, novelty, and the clarity of evidence.

### 9.2 Permitted local refinement

Without changing the program revision, preparation may:

- divide an increment into smaller internal slices;
- adjust task order within the increment;
- replace a provisional mechanism with a repository-native one;
- revise exact files, symbols, commands, or test boundaries;
- separate a risky portion and propose it as the next increment when the current unit is not safely reviewable.

A change becomes a program amendment when it materially affects requirements, acceptance, scope, externally visible behavior, protected contracts, risk posture, dependencies, sequencing, or user review cadence.

---

## 10. Durable artifact model

The physical paths should adapt to the target repository. A manifest maps logical roles to actual paths so validators do not depend on one fixed directory layout.

```text
<program-root>/
  manifest.json

  source/
    implementation-plan.md
    source-metadata.json

  program/
    implementation-program.md
    traceability.json
    decisions.md
    amendments.md

  state/
    status.json
    approvals.jsonl
    action-authorizations.jsonl

  evidence/
    evidence-index.json
    YYYY-MM-DD-<increment-or-topic>.md

  increments/
    INC-001/
      brief.md
      preparation.md
      exact-file-plan.md
      execution-record.md
      reviews/
        requirements.md
        architecture.md
        test-evidence.md
        specialist-*.md
      review-packet.md
      handoff.md

  continuity/
    current-handoff.md
    next-increment-brief.md

  closure/
    reconciliation.json
    program-closure-packet.md
```

### 10.1 Artifact invariants

- The source snapshot and cryptographic digest are immutable.
- The implementation program has an explicit revision identifier.
- Approvals bind to source digest, program revision, workspace, scope, and mode.
- Decisions, amendments, approvals, authorizations, and evidence are append-only records.
- Mutable status updates are atomic and retain a previous-state reference.
- Accepted review packets are immutable; corrections use addenda.
- Only the coordinating workflow changes controlling program state.
- Secrets, tokens, and sensitive credential values are never persisted.
- Each brief is derived from the current approved program and state; it is not a parallel source of truth.
- Stale briefs and handoffs are detected by revision, workspace, and commit bindings.

### 10.2 Traceability record

Each authoritative requirement records:

- stable identifier;
- source location or source-text digest;
- normalized requirement text;
- assigned part, task, and provisional increment;
- acceptance criteria;
- implementation and verification evidence;
- decision or amendment references;
- current disposition.

At closure, every requirement must be explicitly marked as implemented, amended, deferred with ownership, rejected with approval, not applicable with rationale, or otherwise resolved. Unallocated requirements block closure.

---

## 11. State model

Program and increment state remain separate. Implementations may use fewer stored labels if all required distinctions and transition invariants remain explicit, unambiguous, and testable.

### 11.1 Program states

- `captured`
- `awaiting-program-approval`
- `active`
- `blocked`
- `awaiting-closure-approval`
- `closed`
- `superseded`

### 11.2 Increment states

- `not-started`
- `preparing`
- `awaiting-plan-approval`
- `authorized`
- `implementing`
- `reviewing`
- `remediating`
- `verified`
- `awaiting-diff-approval`
- `accepted`
- `change-requested`
- `blocked`
- `superseded`

### 11.3 Required transition invariants

- Program approval precedes implementation.
- Writable workspace selection precedes repository modification.
- A current exact-file plan precedes production changes.
- Review, remediation of material findings, and fresh verification precede diff acceptance.
- Automatic diff acceptance applies only to verified increments with complete packets.
- One-increment modes cannot continue automatically to another increment.
- Accepted increments do not imply program closure.
- Closure requires reconciliation, a closure packet, and explicit closure approval.
- Blocked state records evidence, violated invariant, required decision, and legal resume transition.
- A material program amendment creates a new program revision and invalidates approvals bound to the superseded revision.
- A stale or mismatched brief cannot authorize work.

---

## 12. Approval modes

Approval mode controls interruption and diff acceptance. It does not authorize consequential actions.

| Mode | Scope | Routine exact-file-plan pause | Intermediate interruption | Diff acceptance | Automatic continuation |
|---|---|---:|---|---:|---:|
| `approval:standard` | One increment | Yes | Material decisions, contradictions, or hard stops | User | No |
| `approval:pre-approve` | One increment | No | User-owned decisions, program amendments, contradictions, or hard stops | User | No |
| `approval:full-increment` | One increment | No | Hard stops only | User | No |
| `approval:full-diff` | One increment | No | Hard stops only | Automatic after verification and packet completion | No |
| `approval:full` | Multiple increments while the current conversation remains suitable | No | Hard stops only | Automatic after each verified increment | Yes |

### 12.1 Universal gates

No mode bypasses:

- immutable source preservation;
- initial program approval;
- workspace selection;
- exact-file-plan persistence;
- hard stops;
- required review and verification;
- program-closure approval;
- separate authorization for a draft pull request, merge, release, deployment, destructive operation, migration, or consequential external-state change.

### 12.2 Full-diff behavior

After `approval:full-diff` automatically accepts a verified increment, the workflow updates traceability and status, produces the next recommendation and lean brief if useful, and stops.

### 12.3 Full-mode continuity

`approval:full` may continue only while the current conversation remains a reliable execution context. When a new conversation becomes preferable, the workflow persists a handoff and generates a self-contained continuation brief retaining the requested mode. Submission of that brief in the new conversation renews the instruction; persisted state alone does not silently transfer conversational authority.

---

## 13. Lifecycle behavior

### 13.1 Plan intake and decomposition

1. Capture the source plan exactly and calculate a digest.
2. Record source identity, access method, and revision.
3. Inspect the target repository read-only enough to identify architecture, instructions, existing work, and obvious feasibility constraints.
4. Extract all requirements without sampling.
5. Assign stable requirement identifiers.
6. Decompose work into outcome-oriented parts, tasks, and provisional increments.
7. Record dependencies, integration checkpoints, risks, assumptions, and acceptance criteria.
8. Keep distant implementation details high-level.
9. Persist the program and complete initial traceability.
10. Stop for explicit program approval.

Read-only repository identification supports decomposition. It does not authorize modification of the inspected checkout.

### 13.2 Workspace selection

When no writable workspace is authorized, present the viable options with a recommendation:

- named existing branch;
- current branch;
- new branch in the current working tree;
- dedicated branch in an isolated worktree.

The default recommendation is an isolated worktree unless repository constraints make it inappropriate.

The workspace record includes repository identity, path, branch, base commit, and pre-existing work state.

### 13.3 Increment invocation

The user or prior workflow supplies a lean increment brief. The router verifies that it matches the current program revision, state, workspace, and legal next action. The brief does not supersede persisted state.

### 13.4 Increment preparation

Before each increment:

1. Load the approved program, latest accepted packet, current state, and handoff.
2. Revalidate repository identity, workspace, branch, base/head, cleanliness, conflicts, and active Git operations.
3. Inspect relevant instructions, code, tests, manifests, architecture records, and recent commits.
4. Run relevant baseline checks and distinguish pre-existing failures.
5. Revalidate current official evidence for materially touched surfaces.
6. Search for reusable code and repository-native conventions.
7. Reassess the provisional increment’s size, boundaries, risks, and dependencies.
8. Classify contradictions, user-owned decisions, ordinary implementation details, assumptions, and speculation.
9. Resolve ordinary details autonomously from evidence.
10. Consolidate only genuinely blocking questions, each with a recommendation and consequence.
11. Create or amend the exact-file plan.
12. Apply the selected approval mode.

### 13.5 Implementation

The workflow:

- implements the current authorized outcome;
- uses focused test-first slices where meaningful;
- records alternative verification where test-first behavior is not meaningful;
- selects the smallest sufficient repository-native approach;
- preserves managed, generated, application-owned, and user-owned boundaries;
- avoids unrelated cleanup, silent upgrades, and speculative abstractions;
- records deviations and amendments as they occur;
- creates focused, coherent commits;
- leaves unrelated user work untouched.

### 13.6 Review, remediation, and verification

1. Freeze the proposed increment diff for review.
2. Run requirements/scope, architecture/anti-overengineering, and test-evidence reviews separately.
3. Add specialist reviews based on touched risks.
4. Persist raw reviewer reports before reconciliation.
5. Classify findings as material, non-material, speculative, or invalid.
6. Repair evidence-backed material findings within the approved outcome.
7. Rerun affected tests, reviews, and broader checks.
8. Perform fresh final verification against the resulting diff.
9. Build the review packet.
10. Apply the current mode’s diff-acceptance rule.

### 13.7 Continue or hand off

After acceptance, determine whether the current conversation remains a clean and reliable context.

A new conversation is favored when:

- a meaningful program part boundary is reached;
- the next increment enters a materially different risk or architecture domain;
- the authoritative workspace or base changes;
- accumulated superseded discussion could mislead implementation;
- substantially different evidence or reviewer expertise is required;
- the current context cannot be summarized without losing material constraints.

The handoff includes program revision, current increment, approval mode, workspace, base/head commits, accepted increments, verification status, amendments, unresolved risks, next legal action, and the files to inspect first.

A resumed workflow independently revalidates repository truth. A conversation boundary never triggers or authorizes a draft pull request.

### 13.8 Program closure

After the final increment is accepted:

1. Reconcile every source requirement and approved amendment.
2. Verify that later work did not invalidate earlier accepted increments.
3. Run program-level integration and structural verification.
4. Reassess architecture, documentation, operations, and recovery.
5. Resolve or explicitly disposition all material findings and deferrals.
6. Produce the closure packet.
7. Stop for explicit closure approval.

Only after closure approval should the workflow ask whether to create a draft pull request.

---

## 14. Amendment policy

| Classification | Examples | Automatic handling | Required record |
|---|---|---|---|
| Minor plan correction | Existing helper replaces proposed helper; actual path differs; tests follow repository convention | Yes in all modes | Exact-file-plan addendum, execution record, review packet |
| Bounded implementation amendment | Different internal mechanism, boundary, or current-increment shape while outcome, contracts, risk posture, and acceptance remain unchanged | Proceed autonomously in `pre-approve`, `full-increment`, `full-diff`, or `full` when no user-owned decision is introduced; in `standard`, renew plan approval when the approved exact-file plan changes materially | Amended exact-file plan, amendment ledger, evidence, affected surfaces, reversibility analysis, renewed review |
| Program amendment | Requirement, acceptance criterion, user-visible behavior, scope, security/privacy obligation, protected contract, data ownership, irreversible behavior, or material sequencing changes | No | Proposed program revision, affected traceability, rationale, renewed program approval |
| Authoritative contradiction | Two controlling requirements cannot both be satisfied | No | Contradiction record, preserved state, smallest required user decision |

A technically preferable solution is not sufficient for automatic amendment. The change must be evidence-backed, bounded, obligation-preserving, and credibly reversible or recoverable.

---

## 15. Repository drift policy

Use qualitative categories rather than a numerical score.

### 15.1 Benign drift

Unrelated changes do not affect the current outcome, assumptions, contracts, or user work.

**Action:** record and continue.

### 15.2 Reconcilable relevant drift

Relevant changes alter expected files or implementation details but leave the approved outcome and contracts valid.

**Action:** refresh evidence and exact-file plan, record the amendment, and apply the current mode’s plan gate.

### 15.3 Base-invalidating drift

Branch movement, conflicting user work, active merge-like operations, incompatible dependency changes, changed requirements, or altered protected contracts invalidate the approved basis.

**Action:** preserve state and stop for the smallest necessary decision.

---

## 16. Hard-stop engine

Hard stops are explicit predicates, not discretionary prose.

They include:

- irreconcilable authoritative requirements;
- a required program amendment;
- material scope expansion;
- repository drift that invalidates the approved base or plan;
- ambiguous incorporation, overwrite, or destruction of user work;
- active conflicting Git operations;
- unavailable current official evidence for high-risk work;
- unvalidated material security, privacy, compatibility, or data assumptions;
- missing credentials, accounts, permissions, or secrets required to proceed;
- required human legal, compliance, organizational, or conformance authority;
- irreversible or destructive operations without separate authorization;
- merge, release, deployment, migration, or production modification without authorization;
- no implementation satisfying the approved requirements;
- verification unable to establish acceptable confidence.

A hard-stop record contains:

- verified facts and evidence;
- inferences and uncertainty;
- violated requirement or invariant;
- preserved repository and program state;
- smallest required user decision;
- recommended option and trade-offs;
- legal resume transition.

Ordinary implementation ambiguity is not a hard stop. The agent resolves it from the approved program, repository evidence, applicable official guidance, and established practice.

---

## 17. Evidence policy

Current official evidence is required when the increment materially touches a version-sensitive or consequential surface.

A surface is materially touched when the work:

- introduces or upgrades a dependency, runtime, provider, or integration;
- depends on a version-sensitive or weakly documented API;
- changes authentication, authorization, security, privacy, payments, persistence, migrations, deployment, or provider state;
- relies on a compatibility or security assumption that could invalidate the implementation;
- modifies a public contract whose current behavior is externally defined.

The workflow should not refresh every dependency merely because it exists in the repository. Overbroad evidence collection creates noise and can conceal the genuinely important checks.

For high-risk work, unavailable current official evidence blocks progress. For lower-risk work, prior evidence may be reused only when version, configuration, and assumptions remain applicable, with the access failure and residual uncertainty recorded.

---

## 18. Review model

### 18.1 Required review scopes

Every increment receives separate review for:

1. requirements and accepted-scope compliance;
2. architecture, boundaries, simplicity, and unnecessary complexity;
3. test adequacy and evidence validity.

### 18.2 Specialist predicates

Add only relevant specialist review when the diff materially touches:

- security or privacy;
- persistent data or migrations;
- accessibility;
- platform, deployment, or infrastructure;
- concurrency, reliability, or distributed state;
- public APIs or compatibility contracts;
- payments or financial state;
- performance-sensitive paths;
- consequential provider or external state.

### 18.3 Independence

When independent dispatch is available, reviewers receive the approved scope, relevant artifacts, and frozen diff without being asked to confirm prior conclusions.

When it is unavailable:

- run separate focused self-review passes;
- withhold prior review conclusions where practical;
- persist each review before reconciliation;
- rerun relevant passes after repair;
- disclose that independent review was unavailable;
- label assurance as reduced and non-independent.

### 18.4 Material findings

A material finding identifies:

- affected requirement or invariant;
- concrete evidence and location;
- plausible impact;
- qualitative severity and confidence;
- reproduction or inspection path;
- smallest justified remediation;
- final disposition.

Speculative preference without evidence is not a material finding.

---

## 19. Review-packet contract

Each increment packet contains:

1. increment identity and achieved outcome;
2. what changed and why;
3. relevant program context;
4. changed files grouped by purpose;
5. recommended human review order;
6. requirements and acceptance criteria advanced;
7. exact commands and exact results;
8. baseline failures separated from introduced failures;
9. test-first evidence or alternative verification evidence;
10. reviewer roles, independence status, findings, and dispositions;
11. repairs and renewed verification;
12. exact-file-plan deviations and amendments;
13. specific design points requiring human judgment;
14. known edge cases and manual checks;
15. relevant security, privacy, accessibility, data, deployment, migration, performance, or operational implications;
16. residual risks and deferred work;
17. source rollback and any data, deployment, or provider recovery considerations;
18. workspace, branch, base/head commits, and focused commits;
19. current state and next permitted action.

The validator rejects command-only reports, unsupported completion claims, absent review evidence, missing requirement traceability, or missing recovery information for stateful changes.

---

## 20. Consequential-action authorization

Action authorization is recorded separately from approval mode.

| Action | Default authority |
|---|---|
| Read repository and research | Allowed within the requested task |
| Write program artifacts | Allowed after source registration |
| Create selected branch or worktree | Allowed after workspace choice |
| Modify implementation workspace | Allowed after program and increment authorization |
| Run local verification | Allowed |
| Create focused commits | Allowed within an authorized increment |
| Create draft pull request | Ask after explicit program closure |
| Merge | Just-in-time explicit approval |
| Release | Just-in-time explicit approval |
| Deploy or modify production | Just-in-time explicit approval |
| Production migration | Just-in-time explicit approval |
| Destructive data operation | Separate explicit approval |
| Consequential provider or external-state change | Just-in-time approval with recovery evidence |

Approval modes never alter this table implicitly.

---

## 21. Capability discovery and fallback

At each stage, the skill detects relevant installed planning, isolation, testing, debugging, review, verification, or specialist capabilities.

Constraints:

- load only capabilities relevant to the current stage;
- respect an explicit user instruction disabling a supporting capability;
- prevent recursive invocation of the active workflow;
- never let a supporting capability bypass state, approval, or action gates;
- provide a standalone fallback procedure when a capability is absent;
- use generic role names in repository artifacts;
- disclose reduced assurance when the preferred capability is unavailable.

The skill should depend on behavior contracts, not on one host product or named tool.

---

## 22. Package design

Illustrative structure:

```text
implementing-staged-plans/
  SKILL.md
  references/
    intake-and-program.md
    state-approval-and-authority.md
    workspace-evidence-and-preparation.md
    increment-shaping-and-planning.md
    execution-amendments-and-recovery.md
    review-verification-and-packets.md
    continuity-prompts-and-closure.md
  assets/
    templates/
    schemas/
  scripts/
    validate-package
    validate-program
    validate-transition
    generate-increment-brief
  tests/
    structural/
    state-machine/
    pressure-scenarios/
    repository-fixtures/
    resume-and-crash/
    pilots/
```

The front door contains discovery metadata, non-negotiable invariants, state routing, and links to focused procedures. It does not duplicate every detailed rule.

Exact filenames, physical artifact locations, scripting language, and schema mechanisms are selected only after inspecting the target repository and its conventions.

---

## 23. Validation and test strategy

### 23.1 Baseline controls

Before relying on the new skill, run representative pressure scenarios without it and preserve the observed failures and rationalizations. These controls establish that later tests detect meaningful improvement rather than merely restating the implementation.

### 23.2 Structural validation

Verify:

- required package files and references exist;
- metadata and schemas parse;
- internal links resolve;
- logical artifact roles map to actual paths;
- internal capability names do not leak into project-facing artifacts;
- lean prompts do not duplicate the workflow or omit required semantic fields.

### 23.3 State and approval tests

Verify:

- every legal transition succeeds;
- every illegal transition fails closed;
- stale or mismatched approvals and briefs are rejected;
- blocked-state recovery is explicit;
- program and increment states cannot contradict each other;
- all five approval modes follow the defined matrix;
- no mode implies consequential-action authority.

### 23.4 Artifact and traceability tests

Verify:

- all source requirements are captured;
- partial extraction cannot claim completeness;
- source digests and approval bindings remain valid;
- accepted packets and evidence references exist;
- closure fails with unallocated requirements;
- a generated brief matches the approved program revision and current state.

### 23.5 Repository fixtures

Exercise:

- dirty current branch;
- untracked user files;
- branch or base movement;
- active merge, rebase, or cherry-pick;
- pre-existing test failures;
- generated or managed paths;
- reusable existing code;
- changed manifests and dependency versions;
- provisional increment assumptions invalidated by repository reality.

### 23.6 Pressure scenarios

Use adversarial prompts that encourage:

- coding before approval;
- silent requirement omission;
- distant exact-file planning;
- tests written after implementation but represented as prior red evidence;
- unrelated cleanup;
- silent dependency upgrades;
- rigid adherence to a poor provisional approach;
- unjustified broadening because the prompt is lean;
- misclassified program amendments;
- fake reviewer independence;
- unsupported completion claims;
- continuation in an overloaded conversation;
- trust in stale handoffs;
- premature closure;
- inferred pull-request, merge, or deployment authority.

Where the harness permits, repeat material scenarios in fresh contexts and with varied wording, compare them with a no-workflow control, and preserve both failures and the rationalizations that produced them.

### 23.7 Resume and crash tests

Exercise:

- interruption after each lifecycle transition;
- restart from persisted state;
- stale handoff versus current repository;
- `approval:full` renewal in a new conversation;
- atomic status-update failure and recovery;
- partially written packet or review artifact;
- regenerated prompt after a program revision.

### 23.8 Repository-backed pilot

Before release, run a real or representative temporary program through:

- source capture and complete decomposition;
- program approval;
- workspace selection;
- lean brief generation;
- one full increment;
- bounded approach amendment prompted by repository evidence;
- review, remediation, verification, and acceptance;
- handoff and resume;
- program reconciliation and closure;
- separate draft-pull-request decision.

Closure exercised by this pilot applies only to the isolated pilot program. It does not close the skill's own implementation program, which still requires acceptance of its final increment and a separate program-closure decision.

A prose review alone cannot establish dynamic compliance.

---

## 24. Proposed implementation sequence

The implementation should remain incremental because the workflow is stateful and must prove its own controls. The prompts used to implement these increments should follow the lean brief model rather than repeating the workflow.

### Increment 1 — Baseline pressure suite and minimal front door

**Outcome:** Establish control failures and add the smallest valid entry point, invariant gates, capability discovery, and stage routing.

**Key evidence:** Baseline scenarios are preserved; the package is discoverable; illegal early actions are refused; no later subsystem is simulated as complete.

### Increment 2 — Immutable source capture, decomposition, and traceability

**Outcome:** Register source plans, extract complete requirements, create outcome-oriented programs, support progressive elaboration, and require initial program approval.

**Key evidence:** Complete requirement disposition, source digest integrity, program revisioning, and decomposition pilot against a large plan without project-specific leakage.

### Increment 3 — Durable state, approval modes, and action authorization

**Outcome:** Implement separate program/increment state, legal transitions, approval binding, five approval modes, workspace-selection gate, and distinct action authorization.

**Key evidence:** Complete state and mode matrices, stale-approval rejection, and proof that no mode implies pull-request, merge, release, deployment, or external-state authority.

### Increment 4 — Repository preparation, evidence, increment shaping, and exact-file planning

**Outcome:** Revalidate repository truth, protect user work, classify drift, collect applicable evidence, refine provisional increment shape, and create just-in-time exact-file plans.

**Key evidence:** Dirty-state and drift fixtures, evidence-applicability records, reusable-code discovery, plan amendments, and reviewability checks.

### Increment 5 — Execution discipline, amendments, focused commits, and recovery

**Outcome:** Implement test-first slices and alternative verification, bounded approach autonomy, ownership boundaries, focused commits, amendment classification, and distinct recovery domains.

**Key evidence:** Observed-red tests where applicable, accurate non-TDD verification, no unrelated cleanup, and correct distinction between technical amendment and program amendment.

### Increment 6 — Reviews, remediation, verification, and review packets

**Outcome:** Implement required review scopes, specialist predicates, truthful independence handling, material-finding contracts, remediation loops, final verification, and packet validation.

**Key evidence:** Raw review preservation, repaired material findings, rerun evidence, and packets that support efficient human review.

### Increment 7 — Lean prompt generation, continuity, closure, and authority gates

**Outcome:** Generate minimal briefs from persisted state, create durable handoffs, revalidate on resume, manage full-mode continuation, reconcile the program, require closure approval, and gate draft pull requests and later actions.

**Key evidence:** Prompt minimality and completeness tests, stale-brief rejection, cross-conversation renewal, closure reconciliation, and correct draft-PR timing.

### Increment 8 — Integrated pressure hardening and release pilot

**Outcome:** Run combined pressure, crash/resume, schema-evolution, repository-backed pilot, packaging, documentation, and concision checks; fix only demonstrated material gaps.

**Key evidence:** Full suite results, pilot artifacts, absence of duplicated prompt policy, no broken references, and closure-readiness evidence.

Each increment should use the accepted portions of the workflow already implemented, without pretending later controls exist.

---

## 25. Design acceptance criteria

The design is successfully implemented only when:

- every authoritative source requirement is traceable;
- source evidence remains immutable;
- no implementation begins before program approval and workspace selection;
- exact-file plans are created from current repository truth before production changes;
- prompts remain lean and do not duplicate the canonical workflow;
- prompts still preserve the current outcome, requirements, acceptance criteria, mode, and navigation context;
- the agent can choose or amend the internal implementation approach without silently changing program semantics;
- all five approval modes behave deterministically;
- no approval mode implies consequential-action authority;
- repository drift and pre-existing user work are protected;
- evidence refresh follows a materiality- and risk-based rule;
- implementation amendments cannot disguise program amendments;
- TDD claims are backed by observed evidence where applicable;
- alternative verification is explicit where TDD is not meaningful;
- reviewer independence is represented truthfully;
- material findings are evidence-backed and remediated or explicitly dispositioned;
- review packets support efficient human inspection and recovery;
- cross-conversation continuation revalidates repository truth;
- accepted increments cannot automatically close the program;
- closure and draft-pull-request creation remain separately authorized;
- baseline, pressure, fixture, resume, and repository-backed pilot tests pass.

---

## 26. Proposed defaults requiring approval

1. **Architecture:** layered skill with durable artifacts and validators.
2. **Artifact encoding:** human-facing Markdown plus machine-facing JSON validated by schema where mechanical enforcement is valuable.
3. **Artifact location:** discover the repository’s established documentation root; use a documented fallback only when none exists.
4. **Prompt model:** generated lean briefs containing semantic scope and references, not duplicated workflow instructions.
5. **Increment model:** program increments are provisional until repository-informed preparation; internal slicing is autonomous.
6. **Bounded technical amendments:** proceed autonomously in `approval:pre-approve` and the full-autonomy modes when no user-owned decision or program amendment is introduced; under `approval:standard`, renew plan approval when the approved exact-file plan changes materially.
7. **Full-autonomy modes:** `approval:full-increment`, `approval:full-diff`, and `approval:full`; `approval:pre-approve` is not a full-autonomy mode.
8. **Default when no mode is supplied:** `approval:standard`.
9. **Draft pull-request timing:** ask only after explicit program-closure approval.
10. **State authority:** persisted repository state is authoritative; prompts and handoffs are navigation evidence.
11. **Schema evolution:** record workflow and schema versions; incompatible state requires migration or a clear unsupported-version stop.
12. **State minimization:** retain only states and artifacts that enforce a real invariant or materially improve recovery, review, or traceability.

---

## 27. Risks, counterarguments, and unresolved evidence

### 27.1 Lean prompts may become underspecified

A prompt that merely names an increment without its outcome or acceptance criteria can invite scope drift. The mitigation is the required semantic brief fields and reliable loading of persisted program state.

### 27.2 The workflow may become too large to load reliably

Centralizing policy is preferable to duplicating it, but one monolithic instruction file can still overload context. The mitigation is a small front door, stage-specific references, validators, and progressive disclosure.

### 27.3 Exact-file plans can overconstrain implementation

A plan written before sufficient inspection can encode false assumptions. The mitigation is just-in-time planning and an explicit bounded amendment path.

### 27.4 Agent discretion can disguise program changes

Allowing the agent to reshape an increment improves implementation quality but creates classification risk. The mitigation is requirement traceability, explicit amendment criteria, review against approved outcomes, and program-revision invalidation when semantics change.

### 27.5 State machinery can itself fail

Too many states and artifacts can become harder to reason about than the work. The implementation should preserve logical invariants while minimizing stored state and testing every transition that remains.

### 27.6 Reviewer independence depends on runtime capability

Instruction text cannot manufacture independent review. The workflow must disclose when it is using separate self-review passes and lower its assurance claim accordingly.

### 27.7 Evidence collection can become performative

Refreshing every dependency on every increment creates cost without proportional confidence. Materiality predicates and risk-based evidence requirements are necessary.

### 27.8 Program decomposition may incorrectly freeze early assumptions

The program should bind outcomes, requirements, dependencies, and acceptance criteria while keeping distant technical detail provisional. Repository-informed increment shaping is required to correct early assumptions.

### 27.9 Full-mode continuation can degrade in a long conversation

Automatic continuation is useful only while context remains coherent. The workflow needs an explicit conversation-quality stop and durable handoff generation.

### 27.10 Repository-specific implementation remains unknown

No target skill repository was inspected for this consolidated design. Exact package paths, scripts, schema technology, and test harness remain provisional until repository inspection.

---

## 28. Recommended adoption

Approve this document as the canonical design for the skill.

Retire the prior copy-ready prompts as normative workflow specifications. Their useful operational intent should instead be preserved through:

- the implementation sequence in this design;
- generated lean increment briefs;
- the canonical workflow procedures;
- validators and pressure tests;
- durable review packets and handoffs.

The design plan should remain stable at the level of outcomes and invariants. Repository-specific exact-file planning should occur only when implementation begins and should be allowed to adapt as current evidence warrants.
