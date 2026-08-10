# ISP-001 Draft Pull Request Decision

## Closure and authority binding

- Program: ISP-001 revision 2, closed; INC-008 remains accepted.
- Closed status: sequence 71, `f041a16399768055b757da2550b73b4e52afbc382cc49dd53d06e040d2912d0e`.
- Closure approval: APR-026.
- Closure reconciliation: `7ddac33846fdccb061b11e6c72071b0842877aa776dace4c97a2ee28d30a0f3e`.
- Closure packet: `d9bef2f326690035c6570ca722eb4ce37071732c97535ef0864ec98ed35dffb5`.
- Integration exact-file plan: `d93fee493971e16cabe289070cde759b6e325319d456aa078300f2b2bd5b34ec`.
- Whitespace-correction approval: APR-029.
- Refreshed exact plan approval: APR-030, superseding APR-028 for the normalized bytes.
- Later-action decision authorization: AUTH-032.
- Refreshed local-commit authorization: AUTH-034.
- Refreshed external-action authorization: AUTH-035, superseding AUTH-033 for execution.

## Exact decision

- Action: `create-draft-pull-request`.
- Scope: `decide whether to create a draft pull request from agent/complete-staged-plan-lifecycle at the new lifecycle commit into origin main at baseline 53edb8fad2008c7d35b6c17dbb973b24022947fd for CoveMB/implementation-plugin`.
- `decide_later_action` authorized: true.
- Matched authorization: AUTH-032.
- Issues: none.
- Recovery evidence: `none required` for the decision itself.

This result authorizes the decision only. AUTH-035 separately authorizes the exact external mutations after the corrected local commit exists: initialize the empty remote's `main` ref at the existing committed baseline, push the topic branch without force, and create exactly one draft pull request. It authorizes no merge or ready-for-review transition.

## Repository and pull-request coordinates

- Repository: `CoveMB/implementation-plugin`.
- Remote: `origin`.
- Remote URL: `git@github.com:CoveMB/implementation-plugin.git`.
- PR base branch: `main`.
- PR base commit: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Topic branch: `agent/complete-staged-plan-lifecycle`.
- Draft intent: true.

Read-only preflight found the remote reachable and empty: `git ls-remote --symref origin HEAD refs/heads/main refs/heads/agent/complete-staged-plan-lifecycle` returned no refs. The connected GitHub application identified the same repository, default branch `main`, and push/admin permission. The local GitHub CLI credential is invalid, so pull-request creation must use the connected GitHub application after Git pushes succeed.

## Execution and recovery boundary

1. Create the local topic branch from `main` at the exact base commit.
2. Revalidate the complete logical path partition and full deterministic suite.
3. Stage every authorized path exactly once and create one commit with `feat: complete staged-plan lifecycle workflow`.
4. Push local `main` to empty `origin/main` without force and verify the remote base digest.
5. Push the topic branch with upstream tracking without force.
6. Create one draft pull request from the topic branch into `main` through the connected GitHub application.

If remote state differs before a push, stop without force. If the topic push fails, retain the local branch and commit. If draft-PR creation fails, retain both remote branches and report the provider failure; do not create a duplicate blindly. No merge, publication, release, deployment, migration, destructive action, or unrelated provider mutation is authorized.
