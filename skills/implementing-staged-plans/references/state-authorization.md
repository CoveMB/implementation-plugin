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
- Legacy `approval:full-diff` may accept one verified, packet-bound current-increment diff automatically; it does not continue to another increment.
- Legacy `approval:full` may automatically accept one verified, packet-bound current-increment diff; it does not continue to another increment.

`approval:full-diff` and `approval:full` are dual-read compatibility modes for already persisted legacy programs only. New-model proposal construction, bootstrap, and launch reject either mode before every write. New programs accept only `approval:standard`, `approval:pre-approve`, or `approval:full-increment`; version `0.1.3` continues only through an exact typed continuation prompt.

For both legacy modes, automatic behavior ends with acceptance of the current increment. A successor requires the typed continuation route; neither legacy mode supplies successor authority.

An omitted mode defaults to `approval:full-increment` only while constructing new state and before any proposal bytes exist. Persist the selected mode explicitly. Never default an omitted or unknown mode in persisted state. An explicit user gate remains controlling even when the mode would normally omit that pause.

## Bind approvals exactly

`implementation-approval/v1` and `implementation-action-authorization/v1` are legacy-only. Manifest-v3 setup and product-delta transactions use `implementation-approval/v2` and `implementation-action-authorization/v2`; manifest v3 rejects the v1 schemas. Setup/envelope v2 result-bound diff acceptance advances to approval v3 as described below. Every mechanically relied-on approval must be approved and match the exact schema, event type, identifier, and transaction-owned program, source, increment, plan, workspace, prompt, result, and authority fields required by its family.

Rejected, stale, schema-less, differently scoped, or conflicting records do not grant approval. More than one exact match is ambiguous and fails closed. Historical records remain evidence but cannot authorize a new mechanically checked transition.

## Select a workspace

Legacy `implementation-workspace/v1` selection retains its existing contract: require both an exact workspace-selection approval and an exact `create-workspace` action authorization. This is dual-read compatibility, not a request to rewrite an accepted record.

For a newly created `implementation-workspace/v2` selection, record the exact approved workspace-selection event as `selection_authority`. Do not claim `create-workspace` action authority when the workspace already exists and selection only adopts the caller-observed path. When replacing either schema, supply the current workspace digest and retain it as prior-workspace evidence.

Selection records repository identity, path, branch, base and head, pre-existing work, active Git operation, and the schema-appropriate authority. The function writes the record only; it does not create a branch or worktree, run Git, or classify drift.

## Authorize actions separately

Use the schema-specific typed sink for the requested action and scope. The generic `decide_action_authorization` helper checks accepted legacy `implementation-action-authorization/v1` records. Manifest-v3 ordinary action grants use `implementation-action-authorization/v2`; only the setup/envelope v2 result-bound rollover uses `implementation-action-authorization/v3`. Every grant must bind its family-specific program, source, semantic, increment, mode, brief, plan, workspace, result, and prior-authority tuple, and must name the exact action and scope.

Approval policies contain no action grants. Approval of any mode never authorizes a commit, pull request, merge, publication, release, deployment, migration, destructive operation, provider mutation, or external-state change. Expired, rejected, revoked, stale, schema-less, or conflicting grants fail closed.

## Allocate lifecycle writes before authority

For a new-model exact plan, derive the required control-plane paths with `required_future_lifecycle_writes`. The resolver accepts the program root, selected workspace root, and status-current increment identifier. It derives paths only from manifest logical roles, immutable increment and closure storage descriptors, status-current identity, and traceability.

The file map must classify approvals, status, action authorizations, increment grants, rollovers, and block resolutions as `Modify`. It must classify the current execution baseline, review evidence, and review packet as `Create`. A traceability-allocated successor adds the current handoff and successor brief as `Create`; a final increment instead adds the manifest-derived reconciliation and closure packet. These alternatives are mutually exclusive.

`validate_required_managed_file_map` rejects a missing or misclassified required path. Extra product paths remain subject to repository ownership and action-authorization checks. Declaring a managed path allocates ownership only. In particular, declaring rollover, block-resolution, closure, approval, or status paths grants no permission to write them.

## Persist one transition

Before `apply_state_transition`, revalidate authority and provide a `TransitionRequest` with the expected status digest and sequence, target program and increment states, exact transition event, schema-appropriate authority, and the controlling action scope in its evidence.

For setup/envelope v2, `implementation-execution-baseline/v2` and `implementation-execution-transition/v2` replace the legacy product-delta scalar with an ordered `implementation-product-path-states/v2` result. A Delete entry must be `absent`, have no product digest, and bind exactly one `implementation-delete-quarantine-receipt/v1`; current source absence, quarantine identity, and retained bytes must still match. Review and acceptance use that exact result and its digest.

Legacy `implementation-program-status/v1` transitions keep their existing action-authorization contract. New v2 status is dual-read and records an explicit authority union. The exact approval-driven edges are program approval to active, standard-mode plan approval to authorized, diff approval to accepted, and closure approval to closed. Those governance transitions rely on the matching approved event and do not falsely claim `modify-workspace` authority. Every other declared state change still requires an exact live `modify-workspace` authorization.

New-model diff acceptance uses [`diff_disposition.py`](../scripts/diff_disposition.py), not the generic transition sink. Its acyclic base seed binds the prior status, review evidence and packet, final verification, exact plan, execution baseline, and family-specific accepted product state. It derives the checkpoint, then approval event, then accepted status. Product-delta diff acceptance keeps `implementation-diff-disposition-binding/v1`; manifest-v3 pairs it with `implementation-approval/v2`, while legacy pairs it with `implementation-approval/v1`. Setup/envelope v2 Delete diff acceptance uses `implementation-diff-disposition-binding/v2` with `implementation-approval/v3`, and its result-bound rollover uses `implementation-action-authorization/v3`. Accept-stop remains byte-compatible and grants no successor action. When one allocated successor has satisfied dependencies, the rendered disposition may also contain an exact accept-and-continue prompt. The front-door coordinator persists acceptance first and delegates its status-last successor suffix to [`program_rollover.py`](../scripts/program_rollover.py).

Rollover registers `rollover-increment` as `explicit-local`. Its authorization, successor grant, handoff, successor brief, rollover record, and successor status form an ordered, retry-safe persistence sequence, with status last. Status retains immutable activation history, replaces the status-current grant with the distinct successor grant in `current_increment_authority_binding`, binds the canonical rollover and inherited workspace, and clears prior plan, execution-baseline, review, diff, and closure bindings. The manifest is never rewritten.

For a new-model manifest, `apply_state_transition` rejects generic diff acceptance with `typed-diff-disposition-required`. It rejects every generic direct transition into or out of `blocked` with `blocked-transaction-required`, and every direct supersession with `program-revision-workflow-required`, before general transition validation or persistence. New-model closure likewise uses only the typed closure preparation and exact approval sinks. These guards do not change accepted legacy read validation or legacy state-transition compatibility.

Typed blocked entry uses [`blocked_recovery.py`](../scripts/blocked_recovery.py). Only active `implementing` or `reviewing` state may enter; `remediating` and all plan, preapproval, final, accepted, terminal, or already-blocked states fail before candidate construction or writes. The sink derives the stable block identifier, prior states, status sequence and digest, current plan, baseline, grant, workspace and inherited-workspace bindings, ordered unique criteria, and safe plan-allocated evidence bytes. It atomically replaces status with both states blocked. Callers cannot supply a resume target or fabricated context.

Resolution requires a transport-only candidate whose criteria exactly match the blocked context and are all satisfied. The exact prompt authorizes only `resume-blocked-program`, which is `explicit-local`. Its sink appends or adopts the action authorization, then the manifest-owned block-resolution record, and restores only the context-recorded prior states in status last. Exact prefixes are retryable; changed plan, baseline, grant, evidence, prompt, status, action, or ledger bytes are preserved and fail closed. This path does not intercept Plan A's typed `reviewing -> remediating -> reviewing` lifecycle.

The transition must be a declared matrix edge and satisfy its conditional evidence gates. Blocked state may resume only to its recorded legal target. Terminal state has no same-entity outgoing edge. Starting another increment is a separate operation and requires renewed authority; conversation suitability and legacy approval modes do not supply it.

State replacement uses a same-directory temporary file, flush and file sync, digest compare-and-swap, and atomic replacement. JSON Lines append preserves the exact prior byte prefix and rejects duplicate identifiers. Each receipt reports prior and current digests. This is per-file atomicity, not a multi-file transaction, lock, or hostile-concurrency guarantee. For an approval plus governance transition plus execution grants, use the ordered and retry-safe checkpoint procedure rather than treating those files as one transaction.

## Command results and stop conditions

The CLI provides `validate-state`, `check-action`, `select-workspace`, and `transition-state`. Mutating commands require explicit JSON requests. Exit status `0` means valid or authorized, `1` means invariant failure or no authorization, and `2` means usage error.

After verification, modes with user diff acceptance stop at `awaiting-diff-approval`. Present the exact disposition prompt. Accept-stop authority accepts only the current increment and does not authorize continuation, closure, staging, a commit, or another consequential action.
