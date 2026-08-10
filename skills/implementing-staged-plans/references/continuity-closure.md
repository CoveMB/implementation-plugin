# Continuity and Closure

Use this procedure to generate lean navigation artifacts, decide whether conversational authority continues, validate a resumed run, reconcile a completed program, request closure approval, or decide whether a separately authorized later action may proceed. It does not perform Git, network, provider, or external-state actions.

## Prerequisites and Current Truth

Load the manifest-owned source, approved program revision, traceability, workspace, status, approvals, authorizations, current brief and plan, latest accepted review packet and addendum, and latest accepted handoff. Inspect the repository again for identity, path, branch, base, head, dirty paths, conflicts, and active operations.

Persisted state and current repository observations control. A brief or handoff is a navigation aid. Reject unsupported schemas, missing or duplicate matching records, changed bytes, stale observations, symlinks, path escape, and conflicting bindings.

## Generate a Semantic Brief

Generate a brief from the current approved program and state. Include the program and revision; increment and title; outcome; advanced requirements; acceptance criterion or authoritative pointer; approval mode; exact workspace, status, and handoff navigation; and any already-known unresolved user decision. Add only a material integration checkpoint, risk, non-goal, approved decision, sequencing reason, or repository drift note.

Do not copy repository-inspection policy, test or review procedures, hard-stop lists, action prohibitions, exact-file plans, or provisional implementation choices. Validate the structured record before rendering deterministic Markdown.

## Create a Durable Handoff

After accepted work, bind the handoff to the program revision, current increment, approval mode, workspace, base and head, accepted increments, verification result, accepted packet and addendum, accepted status sequence and digest, amendments, unresolved risks, next legal action, and first-read files. Reject secret-like content and wording that purports to authorize work.

The next legal action explains navigation only. It never renews conversational authority or grants a pull request, merge, release, deployment, migration, destructive, provider, or external-state action.

## Assess Conversation Suitability

For automatic continuation, record evidence for each approved suitability predicate: program-part boundary, risk or architecture domain, workspace or base, superseded discussion, evidence or expertise, and lossless summary. A failed or missing predicate requires a durable handoff.

One-increment modes stop after their increment. `approval:full` can continue automatically only within the same suitable conversation. In every new conversation, require the submitted matching brief and explicit renewed user authority even when the requested mode remains `approval:full`.

## Revalidate a Resume

Compare a fresh observation with the exact source, program, semantic digest, workspace, branch, base, head, status sequence and digest, brief, handoff, accepted packet, accepted addendum, and one matching renewed authorization. Reject conflicts, active Git operations, unsupported schemas, duplicate grants, and every mismatched dimension.

Do not use handoff prose to repair a controlling mismatch. Return the first authority boundary and the smallest legal recovery action.

## Apply an Authorized Rollover

Rollover requires an accepted current increment, the exact dependent next increment, validated proposed handoff and brief bytes, expected digests for controlling files, and a matching write authorization. When both navigation paths are absent, create the handoff and brief before manifest and status updates. Persist one receipt per completed write.

When both navigation paths already exist, adopt them only if each is a regular non-symlink file and its bytes exactly match the validated rendering. Do not rewrite adopted navigation or report it as a completed write; advance only the controlling manifest and status. Mixed presence, changed bytes, symlinks, unsafe paths, or controlling digest drift fail before any write.

If any write fails, retain completed files as inert evidence. Do not delete, overwrite, or roll back user work. Report the partial receipts and require a fresh resume validation before any retry.

## Reconcile a Program

Only after the final increment is accepted, account for every atomic requirement exactly once with an allowed disposition and evidence. Validate every accepted increment, review packet, addendum, approved amendment, decision, owned deferral, later-invalidation check, and material-finding disposition. Require fresh successful program-level commands completed after all contributing evidence and reassess architecture, documentation, operations, and recovery.

Any unallocated requirement, incomplete accepted artifact, unresolved amendment, unowned deferral, material finding, stale verification, or missing reassessment blocks closure readiness. Reopen the smallest affected scope under separate authority.

## Build the Closure Packet and Request Approval

Render a deterministic packet bound to the exact reconciliation digest. Include final-increment acceptance, requirement and amendment outcomes, deferrals, accepted-packet integrity, fresh program verification, the four reassessments, findings and dispositions, residual risks, current active state, an explicit closure-approval request, and a stop as the next action.

Final-increment acceptance leaves the program active. Moving to `awaiting-closure-approval` requires exact manifest-owned reconciliation and packet paths, matching digests, validated readiness, and zero blocking counts. Moving to `closed` requires one explicit `program-closure-approval` record bound to both exact digests.

## Decide a Later Action

Closure approval alone denies every later action. A decision may be authorized only when the program is closed, one exact closure approval matches, one current non-revoked grant matches the requested action and scope, and applicable non-Git recovery evidence exists. Supported decision classes cover draft pull request, merge, publication, release, deployment, migration, destructive operation, and provider or external-state modification.

An authorized decision is not execution. Return the decision and stop; use a separately authorized procedure to perform the action.

## Validate

Run focused validation without bytecode output:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_state_authority -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/continuity_closure.py validate-bundle <evidence.json> --brief <brief.md> --handoff <handoff.md>
```

For closure evidence, add both `--reconciliation <reconciliation.json>` and `--closure-packet <closure-packet.md>`. Exit `0` means the supplied local artifacts satisfy the validator; exit `1` means an invariant failed; exit `2` means invocation or input-path usage is invalid. These checks do not prove conversational judgment, human approval quality, external state, or action execution.

## Hard Stops

Stop on stale or contradictory authority, unresolved user-owned decisions, base-invalidating drift, active operations or conflicts, unsupported schema evolution, incomplete reconciliation, non-zero closure blockers, missing exact closure approval, or absent later-action authority or recovery evidence. Preserve all existing and partial artifacts.

## Bounded Result

Return the validated navigation or decision artifact, exact controlling bindings, material issues, partial-write receipts when present, current state, next legal action, and mandatory stop. Never silently advance another increment, close a program, or perform a later action.
