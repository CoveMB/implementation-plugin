# ISP-001 Decisions

## DEC-001 — Canonical source identity

Accepted on 2026-08-08.

The bytes formerly stored as implementing-staged-plans-consolidated-design-plan-final (2).md are the canonical design. The approved canonical repository filename is implementing-staged-plans-consolidated-design-plan-final.md. The controlling SHA-256 digest is 3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8.

## DEC-002 — Program revision and decomposition

Accepted on 2026-08-08.

ISP-001 revision 1 is the governing program. It retains the eight canonical outcome-oriented increments. Closure remains a separate stage after Increment 8 acceptance.

## DEC-003 — Package scope and identities

Accepted on 2026-08-08.

Use a skills-only plugin with plugin identity implementation-plugin and skill identity implementing-staged-plans. Do not add an MCP server, app, hook, marketplace entry, publisher identity, or publication configuration.

## DEC-004 — Approval gate

Accepted on 2026-08-08.

Prepare Increment 1 under approval:standard and stop for exact-file-plan approval before modifying skill or plugin implementation files.

## DEC-005 — Workspace

Accepted on 2026-08-08 and applied as a bounded implementation detail.

Use branch implementing-staged-plans from exact base commit 456a5ae26b4136cd9f6b6136e36830cbff478083 in an isolated linked worktree. No current-thread native enter-worktree capability was available, so the Git fallback created /private/tmp/implementation-plugin-worktree.7CBpFf. The temporary filesystem location is a continuity risk until the uncommitted program artifacts are reviewed and intentionally committed or moved under separate authorization.

## DEC-006 — Program artifact root

Accepted on 2026-08-08.

Persist this program under implementation-programs/ISP-001/. Its manifest maps logical roles to physical paths.

## DEC-007 — Main-checkout continuation for ISP-001

Accepted on 2026-08-08 and applied as a bounded implementation detail.

After fast-forward integration of accepted INC-001, use `/Users/CoveMB/Code/CoveMB/implementation-plugin` on branch `main` as the implementation workspace for the remaining ISP-001 increments. This decision applies only to this repository-specific implementation program. It does not alter the reusable `implementing-staged-plans` skill, its generic workspace-selection contract, or the canonical workflow's default recommendation.

The selected main checkout contains user-owned pre-existing changes to `implementing-staged-plans-consolidated-design-plan-final.md` and untracked `.DS_Store` files at the repository root, `implementation-programs/`, and `implementation-programs/ISP-001/`. Preserve them. The amended canonical-plan path has SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`, which differs from ISP-001 revision 1's approved source digest. Reconcile and approve that source/program revision before INC-002 preparation or implementation.

## DEC-008 — SOURCE-002 and ISP-001 revision 2

Accepted on 2026-08-08.

The canonical plan at SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57` is SOURCE-002. ISP-001 revision 2 governs the remaining program under `approval:full-increment`. SOURCE-001, revision 1, and accepted INC-001 evidence remain preserved and bound to their original digests; revision 2 does not manufacture retroactive semantic-naming evidence.

The semantic naming amendment is progressively allocated to preparation, execution, review, integrated validation, and closure. Package-facing and reusable implementation names remain project-neutral. Repository governance artifacts may retain ISP, INC, SOURCE, requirement, approval, authorization, and decision identifiers required for traceability.

The original request still requires a stop after the INC-002 exact-file plan is prepared. `approval:full-increment` removes a routine mode-imposed plan pause but does not create implementation, evaluation, reviewer, commit, or consequential-action authority.
