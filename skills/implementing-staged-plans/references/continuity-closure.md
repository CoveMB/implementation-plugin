# Continuity and Closure

Use this procedure to generate lean navigation artifacts, decide whether conversational authority continues, validate a resumed run, reconcile a completed program, request closure approval, or decide whether a separately authorized later action may proceed. It does not perform Git, network, provider, or external-state actions.

## Prerequisites and Current Truth

Load the manifest-owned source, approved program revision, traceability, workspace, status, approvals, authorizations, current brief and plan, and latest accepted review packet. Load an accepted addendum and handoff only when an earlier rollover created them. Inspect the repository again for identity, path, branch, base, head, dirty paths, conflicts, and active operations.

Persisted state and current repository observations control. A brief or handoff is a navigation aid. Reject unsupported schemas, missing or duplicate matching records, changed bytes, stale observations, symlinks, path escape, and conflicting bindings.

## Generate a Semantic Brief

Generate a brief from the current approved program and state. Include the program and revision; increment and title; outcome; advanced requirements; acceptance criterion or authoritative pointer; approval mode; exact workspace, status, and handoff navigation; and any already-known unresolved user decision. Add only a material integration checkpoint, risk, non-goal, approved decision, sequencing reason, or repository drift note.

Do not copy repository-inspection policy, test or review procedures, hard-stop lists, action prohibitions, exact-file plans, or provisional implementation choices. Validate the structured record before rendering deterministic Markdown.

Render every newly generated next-increment or new-conversation prompt with `$implementing-staged-plans` as its first line. Keep the invocation as a copy-ready wrapper around the lean semantic brief so exact accepted historical brief bytes remain valid without rewriting them.

## Create a Durable Handoff

After accepted work, bind the handoff to the program revision, current increment, approval mode, workspace, base and head, accepted increments, verification result, accepted packet and addendum, accepted status sequence and digest, amendments, unresolved risks, next legal action, and first-read files. Reject secret-like content and wording that purports to authorize work.

The next legal action explains navigation only. It never renews conversational authority or grants a pull request, merge, release, deployment, migration, destructive, provider, or external-state action.

## Return Bounded Continuation Navigation

Return every route as a structured bounded continuation result with the current state, one concrete next legal action, a mandatory-stop boolean, and a destination of `current-task`, `new-task`, or `none`. This result is navigation only: it creates no approval, action authorization, grant, status, or continuation receipt.

Only `new-task` may carry a continuation command, and it must set the mandatory stop. Derive its copy-ready prompt at render time through the shared exact-prompt envelope so `$implementing-staged-plans` is the first line. Store no caller-authored Markdown prompt. A `current-task` or `none` result carries no command and renders no prompt.

## Assess Conversation Suitability

For automatic continuation, record evidence for each approved suitability predicate: program-part boundary, risk or architecture domain, workspace or base, superseded discussion, evidence or expertise, and lossless summary. A failed or missing predicate requires a durable handoff.

Every approval mode stops after its current increment. A successor requires the submitted matching brief and explicit renewed user authority, including when a persisted legacy program remains in `approval:full`; conversation suitability alone never supplies successor authority.

## Revalidate a Resume

Compare a fresh observation with the exact source, program, semantic digest, workspace, branch, base, head, status sequence and digest, brief, handoff, accepted packet, accepted addendum, and one matching renewed authorization. Reject conflicts, active Git operations, unsupported schemas, duplicate grants, and every mismatched dimension.

Build renewed authority from the complete validated `ResumeContext`, the current user-request identifier, the one requested continuation action, the exact scope, and a bounded validity period. Validation must match the entire context again and require exactly one live, approved, non-revoked record. Never renew from a reduced tuple or infer authority from the handoff.

Do not use handoff prose to repair a controlling mismatch. Return the first authority boundary and the smallest legal recovery action.

## Apply Prompt-Bound Successor Rollover

Version `0.1.2` keeps the Plan A accept-stop bytes unchanged and adds two explicit successor routes. An immediate accept-and-continue prompt first persists the diff-acceptance prefix and then completes rollover without another user checkpoint. A later continuation from accepted-stop uses its own exact accepted-state prompt. Neither route derives authority from a handoff, brief, approval mode, or accepted status alone.

The legacy caller-authored rollover writer remains quarantined at `legacy-rollover-upgrade-required`; accepted legacy automatic modes never grant successor authority. Only the typed prompt-bound routes below can persist new rollover bytes.

Validate the complete prompt, status-current projection, canonical successor, dependencies, workspace, and accepted product bytes before writing. Persist or adopt the `rollover-increment` authorization, distinct successor grant, current handoff, successor brief, and rollover record in that order; replace successor status last. Every durable prefix is discoverable and retryable with the same prompt. Divergent bytes are preserved and require the matching continuation recovery route.

Successor execution baselines use the existing `inherited_paths` field. Each inherited path must come from the canonical rollover chain, match the accepted product bytes, have exactly one baseline, be owned as `Modify` or `Preserve`, and remain separate from user-work baselines. First-increment baselines remain byte-compatible with `inherited_paths: []`.

## Reconcile a Program

Only after the final increment is accepted, account for every atomic requirement exactly once with an allowed disposition and evidence. Validate every accepted increment, review packet, addendum, approved amendment, decision, owned deferral, later-invalidation check, and material-finding disposition. Require fresh successful program-level commands completed after all contributing evidence and reassess architecture, documentation, operations, and recovery.

For a new-model final first increment, use `program_closure.py`. It resolves both closure paths from the immutable manifest descriptor and requires both paths under the accepted exact plan's `Create` disposition. It does not create a handoff, successor brief, rollover, or later-action authority. A first-increment closure binds the accepted review packet; addendum coverage becomes mandatory only when accepted rollover history exists.

Any unallocated requirement, incomplete accepted artifact, unresolved amendment, unowned deferral, material finding, stale verification, or missing reassessment blocks closure readiness. Reopen the smallest affected scope under separate authority.

## Build the Closure Packet and Request Approval

Render a deterministic packet bound to the exact reconciliation digest. Include final-increment acceptance, requirement and amendment outcomes, deferrals, accepted-packet integrity, fresh program verification, the four reassessments, findings and dispositions, residual risks, current active state, an explicit closure-approval request, and a stop as the next action.

Final-increment acceptance leaves the program active. Moving to `awaiting-closure-approval` requires exact manifest-owned reconciliation and packet paths, matching digests, validated readiness, and zero blocking counts. Moving to `closed` requires one explicit `program-closure-approval` record bound to both exact digests.

New-model preparation creates or adopts the canonical reconciliation, then the packet, and replaces status last. Exact partial prefixes are retryable. Changed files, unsafe paths, nonfinal allocation, stale accepted product bytes, or divergent prefixes are preserved and require typed recovery. The exact closure prompt appends or adopts the closure approval and replaces status with `closed` last. Replaying that prompt can only recover or report the same closure; it cannot authorize a commit or any consequential action.

## Decide a Later Action

Closure approval alone denies every later action. A decision may be authorized only when the program is closed, one exact closure approval matches, one current non-revoked grant matches the requested action and scope, and applicable non-Git recovery evidence exists. Supported decision classes cover draft pull request, merge, publication, release, deployment, migration, destructive operation, and provider or external-state modification.

An authorized decision is not execution. Return the decision and stop; use a separately authorized procedure to perform the action.

One narrow same-turn route exists for creating a draft pull request without pushing. The action grant and resulting decision must bind the exact current request identifier, provider, repository, base branch, head branch, closed workspace head, draft status, `push_requested: false`, and a current bounded expiry. The router accepts only request- and authorization-bound preflight evidence whose checked and valid-until timestamps contain the routing time, and compares its remote observation only with those grant-bound values; caller-supplied substitute targets carry no authority. It also requires an already-existing remote head ref at that exact commit.

The pure router only reports eligibility and returns an exact request-consumption receipt. A downstream executor must durably record that receipt before provider mutation and must supply the complete authoritative prior-consumption set on every route check. An existing receipt for the request or grant, a missing or stale preflight, a missing or different remote ref, a jointly changed target, any push request, a non-draft request, or any other later action returns a mandatory stop. The router neither persists the receipt nor performs the provider action, so callers that cannot establish the complete consumption history must stop. Merge, publication, release, deployment, migration, destructive operations, permission changes, and provider or external-state mutations never use this narrow route.

## Validate

Run focused validation without bytecode output:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_program_closure tests.test_state_authority -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/continuity_closure.py validate-bundle <evidence.json> --brief <brief.md> --handoff <handoff.md>
```

For closure evidence, add both `--reconciliation <reconciliation.json>` and `--closure-packet <closure-packet.md>`. Exit `0` means the supplied local artifacts satisfy the validator; exit `1` means an invariant failed; exit `2` means invocation or input-path usage is invalid. These checks do not prove conversational judgment, human approval quality, external state, or action execution.

## Hard Stops

Stop on stale or contradictory authority, unresolved user-owned decisions, base-invalidating drift, active operations or conflicts, unsupported schema evolution, incomplete reconciliation, non-zero closure blockers, missing exact closure approval, or absent later-action authority or recovery evidence. Preserve all existing and partial artifacts.

## Bounded Result

Return the validated navigation or decision artifact, exact controlling bindings, material issues, partial-write receipts when present, current state, next legal action, and mandatory stop. Never silently advance another increment, close a program, or perform a later action.
