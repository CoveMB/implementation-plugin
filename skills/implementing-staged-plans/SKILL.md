---
name: implementing-staged-plans
description: Advance approved implementation programs one reviewable increment at a time. Use when a repository-backed program needs lifecycle routing, invariant checks, or its next approved implementation increment advanced.
---

# Implementing Staged Plans

Advance only the next legal action recorded by a repository-backed implementation program. Treat this skill as a front door: discover authority and current state, apply universal gates, and route honestly without claiming that an absent safeguard is mechanically implemented.

## Establish Current Authority

1. Identify the target repository without modifying it.
2. Locate the program manifest named or implied by the request. Prefer an explicitly named path; otherwise search repository instructions and conventional implementation-program roots for a unique manifest. If identity remains ambiguous, report the candidates and stop.
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
