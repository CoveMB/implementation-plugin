# ISP-001 Post-Closure Integration Preparation

Prepared at `2026-08-10T02:20:06Z`.

## Authority and preparation-only boundary

- Program: `ISP-001` revision `2`; SOURCE-002 SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program Markdown SHA-256: `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Traceability SHA-256: `a5fb73c3b9fa8619e0a225c2a388e20a88c475b291805508466dbd324a114cb0`; semantic requirements SHA-256 `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Approval mode: `approval:full-increment`.
- Controlling closed status: sequence `71`, SHA-256 `f041a16399768055b757da2550b73b4e52afbc382cc49dd53d06e040d2912d0e`.
- Input manifest SHA-256: `8c35465b5887dd4d6c844b3e4840bd3d1d083a6e0e96cc11a21687f380c85042`.
- Closure approval: `APR-026`; reconciliation SHA-256 `7ddac33846fdccb061b11e6c72071b0842877aa776dace4c97a2ee28d30a0f3e`; packet SHA-256 `d9bef2f326690035c6570ca722eb4ce37071732c97535ef0864ec98ed35dffb5`.
- Input approval-log SHA-256: `17ace85150a1be6c0a4be63e4d61d4401999b91c19707455ed28e69a2b92a410`.
- Input authorization-log SHA-256: `bd622d883d2d172e9041d2c87558ad4c9290e7e89e968d3392defa6cd422fc1a`.
- This prompt is persisted as preparation-only approval `APR-027` and bounded local preparation authorization `AUTH-030`.
- Current authorized writes: create this preparation, the lean integration brief, and the exact-file plan; append APR-027 and AUTH-030 without changing prior JSONL bytes; add their manifest-owned paths and exact digests; run local read-only verification; then stop.

This authority does not cover staging, a commit, a branch change, remote configuration, fetch, push, a pull-request decision or creation, publication, installation, release, deployment, migration, destructive action, provider mutation, or any other consequential action. It adds no implementation requirement and does not reopen the closed program.

## Repository revalidation

- Repository and selected workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin`.
- Branch: `main`; HEAD: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Selected base: `f14449b8808574c720927aedab5b64871cc63858`; ancestry check passed.
- Git: `2.50.1 (Apple Git-155)`; Python: `3.14.6`; GitHub CLI: `2.97.0`.
- No Git remote is configured. Remote freshness therefore cannot be established or affect this local preparation gate; no fetch was run.
- Fresh porcelain-v2 inspection found zero staged paths, zero conflicts, and no merge, rebase, cherry-pick, revert, bisect, or sequencer operation.
- The inspection found 10 modified paths and 135 untracked non-ignored paths before these three preparation files. They are the accepted ISP-001 revision-2 implementation, evidence, closure artifacts, and append-only control-plane state already bound by the closed status.
- Ignored `.DS_Store`, `__pycache__`, and bytecode files are not part of the proposed boundary. They remain untouched.
- SOURCE-001, SOURCE-002, both program revisions, accepted INC-001 through INC-008 artifacts, closure evidence, and user-owned bytes remain preserve-only.

Drift classification: **benign accepted-continuity context**. Repository identity, branch, base, HEAD, source, program, semantic, status, manifest, closure, approval-log, authorization-log, workspace, and accepted-evidence bindings match the submitted tuple. A change to any of those inputs invalidates this preparation before approval or execution.

## Program and later-action fit

Revision-2 closure item 6 requires the draft-pull-request question to be separate and after closure approval. That sequence is now satisfied: INC-008 is accepted, ISP-001 is closed, and exactly one matching `program-closure-approval` record (`APR-026`) binds the current reconciliation and packet.

The accepted continuity procedure still denies every later action unless one current, non-revoked grant matches the exact action and scope. Its `decide_later_action` function returns a decision only; it does not stage, commit, push, create a pull request, or mutate a provider.

The current prompt authorizes preparation only. Therefore no call is made to decide `create-draft-pull-request`, and no affirmative or negative pull-request decision is persisted.

## Repository-informed integration assessment

The closed program has a coherent accepted tree, but it is not yet commit- or pull-request-ready because four external coordinates are absent:

1. no remote repository or remote name is configured;
2. no remote base branch or exact base commit is known;
3. the current workspace is on `main`, and no user-selected topic-branch name or branch-creation authority exists;
4. no exact `create-local-commit` or `create-draft-pull-request` grant covers this post-closure scope.

The safest prospective shape is to keep every working-tree byte unchanged, have the user name a topic branch, create or select that branch before any commit, verify the intended remote base, and then treat local commit, push, draft-PR decision, and draft-PR creation as separate gates. This is a recommendation, not a selected or authorized branch strategy.

Current Git history already contains focused commits through INC-002. The remaining accepted INC-003 through INC-008 and closure tree shares the final manifest, status, traceability, approval ledger, and authorization ledger. Splitting those final shared bytes into reconstructed historical commits would add staging-hunk and invalid-intermediate-state risk. One coherent logical boundary for the complete accepted remaining lifecycle is therefore the smallest resilient commit proposal.

Proposed message: `feat: complete staged-plan lifecycle workflow`.

## Current official guidance

Current official GitHub documentation was checked on 2026-08-10:

- GitHub CLI documents `gh pr create --draft` and explicit `--base` / `--head` selection: https://cli.github.com/manual/gh_pr_create
- GitHub documents that a pull request compares a topic (head) branch against a chosen base branch: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request
- GitHub documents that a remote name and URL must be explicitly associated before remote publication: https://docs.github.com/en/get-started/git-basics/managing-remote-repositories

These sources support the missing-coordinate stop. They do not grant authority, select a repository or branch, prove permissions, or justify adding a remote.

## Semantic naming inventory

This inventory is canonical for this preparation. No package-facing code, public API, command, test, fixture, schema, or product identifier is created or renamed.

| Surface | Kind | Context | Intention | Origin | Planning-term basis | Basis owner | Compatibility class | Compatibility disposition |
|---|---|---|---|---|---|---|---|---|
| `implementation-programs/ISP-001/integration/` | path | closed-program integration governance | collect local integration preparation without reopening the program | new | implementation-governance | ISP-001 manifest | repository-only | additive governance path; no migration |
| `integration/brief.md` | path | post-closure navigation | summarize outcome, bindings, and unresolved decisions | new | implementation-governance | post-closure integration binding | repository-only | additive; no earlier brief rewrite |
| `integration/preparation.md` | path | repository-informed integration evidence | record current truth, commit shape, official evidence, risks, and naming | new | implementation-governance | post-closure integration binding | repository-only | additive; no migration |
| `integration/exact-file-plan.md` | path | later-action planning gate | freeze exact local evidence writes and authority boundaries | new | implementation-governance | post-closure integration binding | repository-only | additive approval target |
| `accepted-staged-plan-lifecycle` | schema-or-identifier | logical commit partition | identify the complete accepted remaining lifecycle tree by intention | new | durable-domain | accepted execution-discipline contract | private evidence | additive logical label; not a Git ref |
| `feat: complete staged-plan lifecycle workflow` | schema-or-identifier | proposed local commit | describe the accepted workflow capability in normal commit form | new | durable-domain | accepted execution-discipline contract | local Git history | proposal only; no commit created |
| `create-draft-pull-request` | schema-or-identifier | accepted later-action vocabulary | request an authority decision distinct from execution | existing | durable-domain | continuity-and-closure contract | persisted | preserve exact accepted action name |
| `Draft pull request decision` | heading | future integration evidence | separate authority evaluation from draft-PR creation | planned | durable-domain | continuity-and-closure contract | repository-only | additive only after exact authorization |

## Exact current logical commit boundary

The exact-file plan contains the complete sorted path partition. Every current changed non-ignored path after this preparation is assigned once to `accepted-staged-plan-lifecycle`. Protected ignored paths and every unchanged path are assigned nowhere.

Commit authority result for this preparation: **not authorized**. The partition is planning evidence only; it is not a staging instruction.

## Risks, recovery, and mandatory stops

- A remote, base, or branch inferred from local names could publish to the wrong repository or produce a misleading PR comparison.
- Creating commits on `main` before selecting a topic-branch strategy could constrain the later PR shape.
- Reconstructing per-increment shared-control-plane commits could produce unverifiable intermediate states and accidental partial-ledger staging.
- A plan approval never supplies `create-local-commit`, branch, push, later-action decision, or PR-creation authority.
- If the tree, controlling digest, remote inventory, branch, base, HEAD, operation state, or conflict state changes, refresh the preparation and logical partition before any action.
- Source recovery is limited to preserving or deliberately editing exact attributed paths; do not reset, clean, stash, restore, or overwrite accepted/user work.
- Persistent data, deployment, and provider state are not touched. Git operations cannot prove recovery for those domains.
- No review dispatch or external evaluator is needed for this preparation. Controller review remains non-independent and reduced assurance.

Mandatory stop: exact-file-plan review. The next prompt must either approve the exact plan with the missing repository/branch coordinates and separately name any permitted local commit and decision actions, request changes, or stop.
