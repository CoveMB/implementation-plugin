# Post-Closure Housekeeping

Use this optional procedure only after a program is verifiably closed and a human explicitly asks to inspect possible housekeeping. It builds and validates a dry-run proposal. It never deletes, moves, quarantines, removes a worktree, or invokes an executor.

## Permanent Preservation Boundary

Never propose these paths for cleanup:

- immutable source snapshots;
- approved program revisions, requirements, and traceability;
- status, approval, and action-authorization records;
- increment briefs, exact-file plans, review packets, raw reports, handoffs, addenda, and accepted evidence;
- reconciliation records and closure packets;
- Git directories, the current worktree, or any user-owned or provenance-uncertain path.

Treat the whole program root and every manifest-owned logical-role path as protected. Reject a candidate that contains, is contained by, or otherwise overlaps protected program, closure, or Git evidence.

## Optional Provenance Inventory

No disposable-resource inventory is required. When the manifest and closure binding contain no `disposable_resource_inventory` role, path, or digest, return a valid empty proposal, mark it `dry-run`, set `execution_authorized` to `false`, and stop.

When present, all three bindings must agree:

- manifest logical role `disposable_resource_inventory`;
- closure field `disposable_resource_inventory_path`;
- closure field `disposable_resource_inventory_sha256` matching the current bytes.

The inventory schema is `implementation-disposable-resource-inventory/v1`. Bind it exactly to `program_id`, `program_revision`, `source_id`, `source_sha256`, `program_sha256`, and `semantic_requirements_sha256`. Each resource must contain:

- a unique 1-128 character lowercase portable-path-component `resource_id`
  and normalized exact `absolute_path`;
- `resource_kind`: `temporary-directory`, `linked-worktree`, or `ignored-cache`;
- `ownership_classification`: exactly `program-created-disposable`;
- `creation_authorization_id` plus a manifest-contained, digest-bound accepted creation-evidence record;
- a normalized exact `containment_root` that strictly contains the candidate;
- `filesystem_identity`, binding the root device, inode, owner and group IDs,
  permission mode, and change timestamp in both the inventory and accepted
  creation evidence;
- a closure-time `fingerprint_sha256` of the candidate content tree;
- `disposable_after`: exactly `program-closure`;
- a non-empty `recovery_deadline`.

The creation-evidence schema is `implementation-resource-creation-evidence/v1`. It must exactly identify the resource ID, path, creation authorization, filesystem identity, `created-by-program` result, and `accepted: true`. Missing, contradictory, or unverifiable provenance is a hard stop. Do not infer program ownership from a directory name, location, ignore rule, worktree registration, or apparent disposability.

## Inspect Every Candidate Read-Only

For every resource, re-read the closed program and current repository, then verify:

1. The candidate and containment root still exist at their exact absolute paths.
2. The candidate is strictly contained by its declared root and candidates neither duplicate nor overlap one another.
3. No candidate, containment-chain component below the declared root, or descendant is a symlink; no descendant is a special filesystem entry.
4. The current root filesystem identity and deterministic content-tree fingerprint equal their closure-bound values. A byte-identical replacement object is stale and provenance-uncertain.
5. The candidate does not overlap the program root, any logical-role path, Git directory or common directory, or the current worktree root.
6. A claimed ignored cache is currently ignored by Git and has no tracked path.

A registered worktree must use `linked-worktree`; reject one labeled as a temporary directory or cache. Conversely, reject `.git` metadata anywhere in a non-worktree candidate because its repository state and unique history have not been assessed.

For `linked-worktree`, also require exactly one current `git worktree list --porcelain -z` record and report the branch, HEAD, staged, modified, untracked, conflicted, active-operation, locked, current-worktree, dirty, and unique-commit results. Reject detached, current, locked, dirty, conflicted, or operation-active worktrees. Reject a worktree unless another local ref contains its exact HEAD after excluding its own branch.

Run every Git inspection with `GIT_OPTIONAL_LOCKS=0`; a proposal must not
refresh index bytes or refs.

Any observation failure rejects the candidate and the proposal. Do not silently omit an unsafe inventory record, weaken a check, use `--force`, or convert uncertain ownership into disposable ownership.

## Build the Deterministic Proposal

The proposal schema is `implementation-housekeeping-proposal/v1`. Sort candidates by absolute path and resource ID. Include the closed program and revision bindings, source/program/semantic digests, reconciliation and closure-packet digests, current repository identity, optional quarantine root, candidate inventory digest, candidate records, `mode: dry-run`, `execution_authorized: false`, and a mandatory stop.

Each candidate records:

- exact absolute path, kind, program-created provenance, and ownership classification;
- explicit symlink and containment results plus the observed filesystem identity and fingerprint;
- full worktree state when applicable;
- proposed recoverable action, target or Git command, `force: false`, and receipt requirement;
- recovery deadline and mechanism;
- the concrete reason removal is considered safe.

For temporary directories and ignored caches, require a separate existing non-symlink quarantine root outside the candidate containment root. Propose a unique deterministic `quarantine-move` target that resolves to a direct child of that root and does not exist; reject absolute, traversal-bearing, or otherwise non-portable resource IDs. Require an operation receipt. Recovery moves the receipt-bound quarantined path back only while the original path remains absent.

For an eligible worktree, propose `git worktree remove <exact-path>` without `--force`, require a receipt, and record the branch and HEAD needed to recreate it with `git worktree add`. This is a proposal only; the procedure runs neither command.

Hash canonical JSON containing all closure, repository, quarantine, and candidate observations as `candidate_inventory_sha256`. Validation must rebuild the full proposal from live state and require byte-equivalent structured content. Any changed path, fingerprint, Git state, repository identity, quarantine target, provenance record, binding, or closure digest makes the inventory stale.

## Check Separate Destructive Authority

Closure approval is never cleanup authority. First validate the exact live proposal. Then require one current non-revoked `implementation-action-authorization/v1` record that:

- authorizes `destructive-operation`;
- includes scope `apply post-closure housekeeping inventory <candidate_inventory_sha256>`;
- matches the exact reconciliation and closure-packet digests and full later-action authority context;
- binds `candidate_inventory_sha256` and the exact sorted `candidate_paths` list;
- has applicable recovery evidence.

Reuse the continuity later-action decision for closure approval and action-authorization checks. A successful decision authorizes only a possible later executor. Return the authorization ID and mandatory stop. It does not change `execution_authorized` in the proposal, perform cleanup, or create execution authority from closure approval.

## Read-Only Commands

Build a proposal on standard output:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/housekeeping_proposal.py propose --program-root <program-root> --repository-root <repository-root> [--quarantine-root <existing-directory>]
```

Validate a saved proposal against live state:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/housekeeping_proposal.py validate-proposal --proposal <proposal.json> --program-root <program-root> --repository-root <repository-root>
```

Check, but do not exercise, separate authority:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/housekeeping_proposal.py check-authorization --proposal <proposal.json> --program-root <program-root> --repository-root <repository-root> --recovery-evidence <receipt-and-recovery-description>
```

The script exposes no execute, delete, move, trash, quarantine, or worktree-removal command. It writes JSON only to standard output or standard error. Exit `0` means the requested read-only decision validated; exit `1` means validation or authorization failed; command-line usage errors exit `2`.

## Hard Stops and Bounded Result

Stop on an open program; invalid or changed closure evidence; absent or mismatched provenance; user-owned or uncertain ownership; non-absolute or stale paths; symlinks; special entries; protected-path overlap; dirty, locked, detached, current, conflicted, operation-active, or unique-commit worktrees; tracked or non-ignored caches; overlapping candidates; quarantine drift; proposal drift; missing exact closure approval; or missing exact destructive-operation authority.

Return only the dry-run proposal or read-only validation/authorization decision, exact issues, and mandatory stop. Never perform cleanup automatically.
