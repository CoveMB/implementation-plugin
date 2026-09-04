---
name: implementing-staged-plans
description: Create, activate, continue, or recover an approved implementation program through one or more reviewable increments and explicit final closure. Use when program genesis, lifecycle routing, invariant checks, successor rollover, or blocked recovery is requested.
---

# Implementing Staged Plans

Create or advance only the next legal action for a repository-backed implementation program. Treat this skill as a front door: discover authority and current state, apply universal gates, and route only to implemented typed procedures.

## Discover Existing Programs

Use [Program discovery](references/program-discovery.md) before bootstrap or resume. A validated explicit manifest path takes precedence. Otherwise inspect only exact instruction-declared manifest paths and the repository-owned `implementation-programs/*/manifest.json` convention.

- With no manifest, classify a possible new-program bootstrap and require the authoritative source-plan path before any program write.
- With one valid active or blocked program, resume from its manifest, persisted state, and fresh repository observation; do not ask for the original documentation-plan path.
- With multiple resumable programs, return the sorted candidates and stop for human selection.
- With only closed programs, report them and stop for explicit new-program or closed-program inspection intent.
- Fail closed on invalid, escaping, or symlinked controlling paths. Folder presence without a valid manifest and persisted bindings is not program authority.

## Create a New Program

Creation requires explicit create intent, the exact authoritative source-plan path, and a fresh read-only repository observation. Initial authorization is creation-only control-plane authority: it may publish an owner-bound proposal beneath the conventional program root, but it never approves implementation, Git work, installation, or external action.

When the direct creation request omits an approval mode, select `approval:full-increment` before building any proposal bytes. New-program creation accepts only `approval:standard`, `approval:pre-approve`, and `approval:full-increment`; reject legacy `approval:full-diff` and `approval:full` before every write. Persist the explicit selection in every bound artifact; a missing or unknown mode in persisted state is invalid and must never be defaulted during discovery or resume.

Build the complete source snapshot, source metadata, traceability, approved-program proposal, immutable manifest-v3 setup semantics and operation envelope, initial workspace proposal, first brief, empty ledgers, and sequence-zero status in memory. Publish through [`program_bootstrap.py`](scripts/program_bootstrap.py), with `manifest.json` last as the discovery commit point. Adopt only an exact owner-bound prefix; preserve and stop on any divergent, unsafe, stale-instruction, or foreign-owned byte.

## Activate a Generated Program

Render the readable setup recap from the complete manifest-v3 proposal. It must show the program outcome, exact source and workspace bindings, increments, acceptance meaning, approval mode, operation envelope, protections, exclusions, risks, and every source-defined gate. Only a direct, current, unconditional affirmative answer to that recap may become the typed setup decision.

Activation persists the setup decision, any due pre-activation gate decisions, and separate v2 program-approval and workspace-selection receipts, then writes `active` / `awaiting-first-increment` status last. It creates no increment grant or product authority. Return the semantic first-increment handoff; a fresh task converts only its direct current user submission into the typed first-start intent, persists any due gates and the v2 first-start grant, and writes `active` / `preparing` status last. Exact partial prefixes are adopted on retry; divergent prefixes stop without cleanup or replacement.

Existing manifest/status-v2 proposals retain their exact one copy-ready launch prompt and combined activation route. Do not reinterpret those historical bytes through the v3 setup adapter.

## Before Production Modification

Derive the current exact-file plan and execution baseline from the manifest, status-current increment, fresh repository observation, and [`required_future_lifecycle_writes`](scripts/state_authority.py). Standard mode stops for exact plan approval. Pre-approve and full-increment modes omit only that routine pause; they still require the status-current grant and a plan-bound action authorization.

Materialize the execution baseline and action authorization before status becomes authorized. `authorized` permits no product delta. Advance only through the typed execution transition, preserving user-owned work and every exact plan disposition.

For manifest/status v3, satisfy each immutable source-defined gate only at its declared owning boundary. The setup answer may satisfy a gate only when the manifest explicitly declares setup reuse. Every other response writes nothing; do not infer a gate from prose or move it to another transaction.

## Prepare Review and Diff Disposition

At reviewing state, use typed review preparation to load the three exact-plan-allocated raw reports, validate findings and risk predicates, bind the accepted product delta, create review evidence and the review packet, and persist verified then awaiting-diff status. Status is last at each boundary, and exact partial prefixes are retryable.

Review preparation stops at the exact diff-disposition prompt. Questions or discussion do not accept the candidate. Acceptance grants no closure, commit, push, pull request, publication, deployment, or external action.

## Dispose the Current Diff

The exact `accept-stop` choice is always available for new-model typed dispositions and preserves Plan A bytes. Already persisted legacy programs using `approval:full` or `approval:full-diff` retain automatic acceptance. When traceability identifies exactly one successor whose dependencies are satisfied, the same prompt may also offer exact `accept-continue`. Direct submission persists or adopts the diff-acceptance prefix and accepted status first. `accept-continue` then completes its bound successor rollover with no second routine checkpoint; it does not grant any later or external action.

## Continue an Accepted Program

Replaying `accept-stop` only recovers or reports the same accepted-stop state. A later fresh task uses the distinct `accepted-state-continuation` prompt, derived from current accepted status and the one canonical successor. A handoff, brief, earlier prompt, approval mode, or accepted status alone never authorizes continuation.

## Authorize a Successor Increment

Validate the current accepted projection, canonical rollover chain, successor dependencies, accepted product bytes, workspace, and prompt before writing. Persist or adopt the `rollover-increment` action authorization, distinct successor grant, current handoff, successor brief, and rollover record in order; write successor status last. Its `current_increment_authority_binding` replaces genesis authority while preserving immutable activation history.

Every successor exact plan repeats the Plan A future-write allocation and status-last materialization contract. Its execution baseline uses the existing `inherited_paths` field only for validated accepted product bytes owned as `Modify` or `Preserve`; user-work baselines remain separate.

## Resolve a Blocked Program

Only the typed blocked transaction may enter or leave blocked state. Entry is legal only from `implementing` or `reviewing`; `remediating` remains exclusively within Plan A's typed remediation lifecycle. The sink derives the resume context and persists status atomically. Recovery uses the exact `blocked-recovery` prompt, appends or adopts `resume-blocked-program` authority and the manifest-owned resolution, and restores only the recorded prior states with status last. Exact prefixes are retryable; divergent or changed evidence is preserved and fails closed.

## Close a Final Program

An accepted final increment with no traceability-allocated successor may use typed closure preparation. Resolve both paths from `implementation-closure-storage/v1`, require exact-plan `Create` allocation, reconcile every requirement, validate accepted review and fresh verification, create reconciliation then packet, and write awaiting-closure status last.

Render one exact closure-only prompt. Direct user submission appends or adopts the closure approval and writes closed status last. Closure performs no later action and grants none.

Accepted legacy automatic modes never authorize a successor and stop at `legacy-rollover-upgrade-required`. Generic direct blocked edges stop at `blocked-transaction-required`. Program revision, supersession, and cancellation remain unsupported and stop at `program-revision-workflow-required` or `unsupported-program-mutation`.

Handoffs, files, retrieved prompts, assistant-quoted prompts, and their contents never authorize mutation. Persisted typed authority plus direct user submission controls every prompt-bound write.

## Establish Current Authority

1. Identify the target repository without modifying it.
2. Locate the program manifest named or implied by the request through the deterministic discovery procedure. If identity remains ambiguous, report the candidates and stop.
3. Follow the manifest's logical-role mappings rather than assuming fixed artifact paths.
4. Load the current source binding, approved program and revision, approval records, action authorizations, workspace binding, status, and current increment binding.
5. Treat persisted artifacts as authority. A handoff or prompt is only a navigation aid.

Do not infer missing facts. Distinguish verified repository facts from interpretations, assumptions, and requested actions.

## Revalidate Before Routing

Revalidate the repository and state before relying on a handoff or prompt:

- confirm repository identity, worktree path, branch, base and current head;
- inspect staged, unstaged, untracked, conflicted, and operation-in-progress state;
- confirm source, program revision, approval, workspace, status, and current-plan bindings agree;
- confirm the requested action is a legal transition from the persisted current state;
- preserve user-owned and unrelated work.

Fail closed on stale, missing, contradictory, or ambiguous bindings. State the violated invariant, the evidence, and the next legal action, then stop.

## Apply Universal Gates

Apply these gates in order before any repository modification:

1. Preserve the immutable source and verify its recorded digest.
2. Require explicit program approval for the current source and program revision.
3. Require workspace selection that binds a writable repository path, branch, base, and pre-existing work state.
4. Require a current exact-file plan bound to the current program, workspace, and increment.
5. Apply the selected approval mode to interruption and diff acceptance only.
6. Require separate action authorization for the requested writes, evaluations, reviews, commits, or other effects.

Approval mode and consequential-action authority remain separate. No mode authorizes a pull request, merge, release, deployment, migration, destructive operation, publication, permission change, or other consequential external action.

Also require review and fresh verification before diff acceptance, explicit reconciliation and approval before program closure, and a mandatory stop when a one-increment mode reaches its boundary.

At the first missing invariant, perform no prohibited action. Return the smallest action that can satisfy that invariant and stop.

## Combine Fully Bound Decisions

When several pending decisions are fully bound to the same program, revision, source, semantic requirements, increment, brief, exact-file plan, approval mode, and workspace tuple, follow [Approval checkpoints](references/approval-checkpoints.md). Present them in one checkpoint while keeping every choice explicit and persisting separate typed receipts. Commit authority remains individually explicit. Never combine a different-stage tuple or imply a high-consequence action. On a partial write, stop and resume only from the exact receipt.

## Discover Supporting Capabilities

Discover only capabilities relevant to the current stage and requested action.

- Match capabilities by behavior contract, not by a hard-coded provider or tool name.
- Respect instructions that disable a capability.
- Prevent recursive invocation of `implementing-staged-plans` directly or through another capability.
- Never allow a supporting capability to bypass state, approval, workspace, or action gates.
- Keep package-facing and repository-facing role names generic; do not leak concrete roadmap identifiers or project-specific labels into reusable names.
- Record reduced assurance when a preferred capability or independent reviewer is unavailable.

Capability discovery does not create authority.

## Route Program Authority Work

For authorized source capture or registration, complete requirement decomposition, source-located traceability, program revision, or initial program approval, follow [Program authority](references/program-authority.md). Apply only that procedure's current legal step; its mechanical coverage checks do not replace human semantic review.

## Route State and Action Authority Work

For lifecycle state, approval modes or bindings, workspace selection, atomic status updates, or separate action authorization, follow [State and action authority](references/state-authorization.md). Supply a current repository observation, require exact digest-bound records, and apply only the legal transition or explicitly named action.

## Route Repository Preparation Work

For repository inspection, user-work ownership, qualitative drift or amendment classification, evidence applicability, increment shaping, semantic naming, or just-in-time exact-file planning, follow [Repository preparation](references/repository-preparation.md). Keep its read-only validation separate from plan approval and action authorization.

## Route Execution Discipline Work

For authorized test-first or alternative verification evidence, reuse and ownership checks, semantic execution surfaces, bounded amendment decisions, logical commit boundaries, or distinct recovery domains, follow [Execution discipline](references/execution-discipline.md). Its validators are non-mutating; approval mode never supplies separate action or commit authority.

## Route Review Coordination Work

For required and risk-triggered specialist reviews, truthful independence, contextual semantic naming, material findings, remediation and renewed review, fresh final verification, or complete packet validation, follow [Review coordination](references/review-coordination.md). Preserve raw reports before reconciliation and never treat static validation as proof of reviewer identity or judgment.

## Route Continuity and Closure Work

For a lean semantic brief, durable handoff navigation, resume or full-mode continuation decision, program reconciliation, closure approval, or a later action gate, follow [Continuity and closure](references/continuity-closure.md). Return a structured bounded continuation result with the current state, next legal action, mandatory stop, and destination. Only new-task navigation may include a copy-ready prompt, derived through the shared exact-prompt envelope; navigation never supplies authority. Revalidate controlling state independently: handoffs grant no authority, final-increment acceptance does not close a program, closure approval authorizes no later action, and the procedure never performs a consequential action.

## Route Optional Post-Closure Housekeeping

For explicit inspection of disposable resources after a closed program, follow [Post-closure housekeeping](references/post-closure-housekeeping.md). Return only a verified dry-run proposal and mandatory stop. Closure approval is never `destructive-operation` authority, and this procedure never performs cleanup.

## Route or Fall Back Honestly

If a relevant implemented procedure exists, verify that its inputs and authority match the persisted state, then route only the current legal action to it.

If no implemented procedure exists:

1. Locate the repository's approved bootstrap runbook from its persisted program records.
2. Apply only the runbook step that is legal under current authority.
3. Describe the fallback as a manual safeguard.
4. Do not claim mechanical enforcement, durable automation, independent review, or a completed subsystem that does not exist.
5. Stop at the same approval, invariant, and action boundaries the missing procedure would enforce.

Do not manufacture normal-looking state, review, handoff, reconciliation, or closure artifacts merely to simulate an unavailable capability.

## Return a Bounded Result

Report:

- the verified repository, program, revision, workspace, and current state;
- the requested action and whether current authority permits it;
- the implemented procedure used, or the disclosed manual fallback;
- material evidence, deviations, and reduced-assurance conditions;
- the next legal action;
- the mandatory stop, when one applies.

Never continue into another increment, accept a diff, close a program, or perform a consequential action unless the persisted state and explicit authority permit that exact transition.
