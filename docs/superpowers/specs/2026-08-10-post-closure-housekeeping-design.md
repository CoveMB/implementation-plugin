# Post-Closure Housekeeping Proposal Design

**Status:** Approved in conversation on 2026-08-10

## Purpose

Add an optional, proposal-only post-closure housekeeping boundary to the
`implementing-staged-plans` skill. The boundary may describe recoverable
cleanup for verified program-created disposable resources, but it never moves,
trashes, prunes, removes, or deletes anything.

## Fixed Safety Decisions

- Immutable source snapshots, approved program revisions and traceability,
  status, approvals, authorizations, increment review packets, handoffs,
  accepted evidence, reconciliation, closure packets, user-owned files, and
  provenance-uncertain files are permanent.
- The default result is a deterministic dry-run proposal followed by a
  mandatory stop.
- A proposal may contain only `program-created-disposable` resources with
  closure-bound provenance and a current matching fingerprint.
- Closure approval is never cleanup authority.
- A later decision requires one exact, current, non-revoked
  `destructive-operation` authorization bound to the reconciliation digest,
  closure-packet digest, candidate-inventory digest, sorted absolute candidate
  paths, and the full authority context.
- Even a successful authorization decision stops. This feature contains no
  execution API or CLI command.
- No existing program, closure, installation, program-discovery, or
  continuation-prompt artifact is changed.

## Architecture

Create a focused `housekeeping_proposal.py` module beside the existing
authority scripts. It consumes an optional closure-bound disposable-resource
inventory, inspects only the exact recorded resources, builds a canonical
proposal, revalidates it against the live filesystem and local Git state, and
decides whether an exact destructive authorization exists. It reuses the
existing program loaders, managed-path protection, repository inspection, and
later-action decision boundary without adding a cleanup executor.

The skill front door gains one route to a human-readable
`post-closure-housekeeping.md` procedure. A dedicated test module owns the
proposal and safety contract.

## Provenance Input

The optional input schema is
`implementation-disposable-resource-inventory/v1`. It is authoritative only
when both bindings exist and agree:

- manifest logical role `disposable_resource_inventory`;
- status closure fields `disposable_resource_inventory_path` and
  `disposable_resource_inventory_sha256`.

The inventory binds the program, revision, source, program, and semantic
digests. Each resource contains:

- `resource_id`: a unique 1-128 character lowercase portable path component;
- exact `absolute_path`;
- `resource_kind`: `temporary-directory`, `linked-worktree`, or
  `ignored-cache`;
- `ownership_classification`: exactly `program-created-disposable`;
- `creation_authorization_id`;
- accepted `creation_evidence_path` and `creation_evidence_sha256`;
- exact absolute `containment_root`;
- `filesystem_identity`, binding the candidate root's device, inode, owner and
  group IDs, permission mode, and change timestamp in both the inventory and
  accepted creation evidence;
- final `fingerprint_sha256`;
- `disposable_after`: exactly `program-closure`.

Missing provenance produces a valid empty proposal. Missing, malformed,
unbound, stale, symlinked, or contradictory provenance fails closed.

## Proposal Contract

The output schema is `implementation-housekeeping-proposal/v1`. It binds:

- program ID and revision;
- source, program, and semantic digests;
- reconciliation and closure-packet digests;
- current repository root, branch, HEAD, Git directory, and common Git
  directory;
- the exact optional quarantine root used to derive recoverable targets;
- canonical candidate inventory digest;
- sorted candidates;
- `mode: dry-run`;
- `execution_authorized: false`;
- a mandatory-stop next action.

Every candidate records the exact provenance fields, ownership classification,
filesystem-object identity and content fingerprint, symlink and containment results, proposed action, receipt
requirement, recovery mechanism, and reason removal is safe. A linked-worktree
candidate additionally records registration, current/linked state, lock state,
branch, HEAD, staged/modified/untracked/conflicted paths, active Git operation,
dirty state, and whether unique commits exist.

Candidates are sorted by absolute path. The inventory digest is SHA-256 over
UTF-8 canonical JSON containing the program and closure bindings plus the
candidate list, using sorted keys, compact separators, and one final newline.

## Candidate Safety

All candidate and containment paths must be absolute. Use `lstat` on the root,
every ancestor from the containment root, and every descendant. Reject
symlinks, sockets, devices, FIFOs, broken paths, lexical escape, resolved-path
escape, and overlapping candidates.

Reject any candidate that equals, contains, or is contained by the program
root, the repository's Git directory or common Git directory, a manifest-owned
closure/source/program/state/review/evidence path, or the current worktree
root. User-owned and provenance-uncertain classifications are never eligible.

For an ignored cache, require that it is under the repository, has no tracked
descendants, and is positively ignored by Git. For a linked worktree, require
the stable NUL-delimited `git worktree list --porcelain -z` record, a linked
non-main unlocked worktree, an entirely clean repository observation, no
active operation, matching branch and HEAD, and at least one other local ref
containing HEAD after excluding its own checked-out branch. Never use
`--force`.

Revalidation recomputes all closure, provenance, filesystem, and Git bindings.
Any difference, including replacement of a candidate by a byte-identical
filesystem object, makes the proposal stale. Git inspection commands run with
`GIT_OPTIONAL_LOCKS=0` so proposal generation does not refresh index bytes.

## Proposed Recovery

- `temporary-directory` and `ignored-cache` candidates propose a
  `quarantine-move` to an exact target beneath a caller-supplied existing
  non-symlink quarantine root. The target is a unique resolved direct child of
  that root derived only from the validated resource ID. Recovery moves the unchanged quarantined object
  back only if the original path remains absent.
- `linked-worktree` candidates propose `git-worktree-remove` without force.
  Recovery recreates the worktree at the recorded absolute path from the
  preserved branch or HEAD.
- Every action requires a future receipt containing the original and recovery
  paths or Git identities, before/after fingerprints, closure digests,
  inventory digest, and authorization ID.

These are proposal records only. This module performs none of the actions.

## Authorization Decision

`check_housekeeping_authorization` first performs full live proposal
validation. It then requires exactly one existing closure approval plus one
current non-revoked action grant for `destructive-operation` with scope:

`apply post-closure housekeeping inventory <candidate-inventory-sha256>`

The grant must also contain the exact candidate-inventory digest and the exact
sorted absolute candidate paths. A matching decision returns authorization
metadata and another mandatory stop. It never invokes a cleanup operation.

## Public Interface

- `build_housekeeping_proposal(program_root, repository_root,
  quarantine_root=None) -> HousekeepingProposal`
- `validate_housekeeping_proposal(proposal, program_root, repository_root) ->
  list[str]`
- `check_housekeeping_authorization(proposal, program_root, repository_root,
  *, recovery_evidence) -> HousekeepingAuthorizationDecision`

CLI commands are limited to `propose`, `validate-proposal`, and
`check-authorization`. JSON is written only to standard output.

## Verification

Safety tests cover user ownership, uncertain and missing provenance,
symlinks, containment escape, stale inventories, protected closure evidence,
tracked and non-ignored caches, current/dirty/locked/conflicted worktrees,
detached and operation-active worktrees, unique commits, byte-identical path
replacement, quarantine-target escape, closure-only approval, revoked/expired
or stale destructive authority, read-only Git index behavior, and a valid
decision that still stops without execution.

No cleanup, installation, discovery, continuation-prompt, staging, commit,
push, pull-request, or publication behavior is in scope.
