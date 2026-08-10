# State and Action Authority

Use this procedure to validate or change durable lifecycle state after source and program authority are valid. It separates program state from increment state, approval policy from action permission, and caller-observed repository facts from persisted workspace selection.

The mechanical boundary is [`state_authority.py`](../scripts/state_authority.py). It uses the accepted program-authority validator before relying on state. Run it only against the program root selected through the manifest.

## Required inputs

Before routing an action, load the manifest logical roles for status, workspace, approvals, action authorizations, the current brief, exact-file plan, and review packet. Supply a `RepositoryObservation` containing repository identity, workspace path, branch, base and head commits, all staged, modified, untracked, and conflicted paths, plus any active Git operation.

The validator does not discover Git facts. Obtain them independently and pass them explicitly. A handoff, prompt, approval mode, or old observation cannot substitute for current facts.

## Validate before deciding

Call `validate_state_authority` before relying on status. It checks:

- immutable source, approved program, traceability, and semantic digests;
- supported status and workspace schemas;
- separate program and increment states;
- current workspace, brief, plan, and head bindings;
- persisted approval mode without silently defaulting it; and
- previous-state schema, sequence, and digest evidence when present.

Unknown states, unsupported schemas, symlinked controlling paths, stale digests, ambiguous records, or observation drift fail closed. Report the sorted issues and stop without writing.

## Apply approval modes

Approval modes control routine interruption, diff acceptance, and continuation only:

- `approval:standard` pauses for the exact-file plan and user diff acceptance.
- `approval:pre-approve` omits the routine plan pause but stops for user-owned decisions, program amendments, contradictions, and hard stops; diff acceptance remains with the user.
- `approval:full-increment` runs one increment through verification, then stops for user diff acceptance unless a hard stop occurs.
- `approval:full-diff` may accept one verified, packet-bound diff automatically; it does not continue to another increment.
- `approval:full` may automatically accept a verified, packet-bound diff and continue only while the same conversation remains suitable.

An omitted mode defaults to `approval:standard` only when creating new state. Never default an omitted or unknown mode in persisted state. An explicit user gate remains controlling even when the mode would normally omit that pause.

## Bind approvals exactly

A mechanically relied-on approval must use `implementation-approval/v1`, be approved, and bind the program and revision, source and program digests, semantic digest, increment, brief and plan digests, approval mode, and workspace path, branch, base, and head. Require the expected event type and exact event identifier for the transition.

Rejected, stale, schema-less, differently scoped, or conflicting records do not grant approval. More than one exact match is ambiguous and fails closed. Historical records remain evidence but cannot authorize a new mechanically checked transition.

## Select a workspace

Legacy `implementation-workspace/v1` selection retains its existing contract: require both an exact workspace-selection approval and an exact `create-workspace` action authorization. This is dual-read compatibility, not a request to rewrite an accepted record.

For a newly created `implementation-workspace/v2` selection, record the exact approved workspace-selection event as `selection_authority`. Do not claim `create-workspace` action authority when the workspace already exists and selection only adopts the caller-observed path. When replacing either schema, supply the current workspace digest and retain it as prior-workspace evidence.

Selection records repository identity, path, branch, base and head, pre-existing work, active Git operation, and the schema-appropriate authority. The function writes the record only; it does not create a branch or worktree, run Git, or classify drift.

## Authorize actions separately

Use `decide_action_authorization` for the requested action and scope. A valid `implementation-action-authorization/v1` grant must bind the same program, source, semantic, increment, mode, brief, plan, and workspace tuple. The exact action and scope must appear in the grant.

Approval policies contain no action grants. Approval of any mode never authorizes a commit, pull request, merge, publication, release, deployment, migration, destructive operation, provider mutation, or external-state change. Expired, rejected, revoked, stale, schema-less, or conflicting grants fail closed.

## Persist one transition

Before `apply_state_transition`, revalidate authority and provide a `TransitionRequest` with the expected status digest and sequence, target program and increment states, exact transition event, schema-appropriate authority, and the controlling action scope in its evidence.

Legacy `implementation-program-status/v1` transitions keep their existing action-authorization contract. New v2 status is dual-read and records an explicit authority union. The exact approval-driven edges are program approval to active, plan approval to authorized, diff approval to accepted, and closure approval to closed. Those governance transitions rely on the matching approved event and do not falsely claim `modify-workspace` authority. Every other declared state change still requires an exact live `modify-workspace` authorization. Plan approval also binds the separately expected execution-authorization identifier and scope; it does not make that future grant exist.

The transition must be a declared matrix edge and satisfy its conditional evidence gates. Blocked state may resume only to its recorded legal target. Terminal state has no same-entity outgoing edge. Starting another increment is a separate operation and requires renewed one-increment authority or suitable conversation-bound full authority.

State replacement uses a same-directory temporary file, flush and file sync, digest compare-and-swap, and atomic replacement. JSON Lines append preserves the exact prior byte prefix and rejects duplicate identifiers. Each receipt reports prior and current digests. This is per-file atomicity, not a multi-file transaction, lock, or hostile-concurrency guarantee. For an approval plus governance transition plus execution grants, use the ordered and retry-safe checkpoint procedure rather than treating those files as one transaction.

## Command results and stop conditions

The CLI provides `validate-state`, `check-action`, `select-workspace`, and `transition-state`. Mutating commands require explicit JSON requests. Exit status `0` means valid or authorized, `1` means invariant failure or no authorization, and `2` means usage error.

After verification, modes with user diff acceptance stop at `awaiting-diff-approval`. Do not accept the diff, begin another increment, close the program, or perform any consequential action without the separate exact authority for that operation.
