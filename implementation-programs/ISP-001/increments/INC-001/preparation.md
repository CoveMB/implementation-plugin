# INC-001 Preparation

**Prepared:** 2026-08-08  
**State:** Complete for exact-file-plan review  
**Mode:** approval:standard

**Exact-file-plan SHA-256:** c9fc55af3a8076eaab846114d2363580697c97a801418e2a377db69c262fb2a1

## Verified repository state

- Main checkout: /Users/CoveMB/Code/CoveMB/implementation-plugin on clean main.
- Initial base commit: 456a5ae26b4136cd9f6b6136e36830cbff478083.
- Base commit contains exactly the canonical design and bootstrap runbook.
- Implementation worktree: /private/tmp/implementation-plugin-worktree.7CBpFf.
- Implementation branch: implementing-staged-plans.
- Worktree was clean before program artifacts were created.
- No remote is configured.
- No package manifest, plugin manifest, skill, test harness, validator, script, CI configuration, or established repository documentation convention exists.
- No merge, rebase, cherry-pick, revert, bisect, or conflict is active.
- Canonical source snapshot SHA-256 matches the confirmed root source: 3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8.

## Applicable current evidence

Accessed on 2026-08-08:

- https://developers.openai.com/plugins/build/skills — a focused skill requires SKILL.md, may use references, scripts, assets, and agents/openai.yaml, and should be tested with direct, indirect, incomplete, non-triggering, and unsupported-action requests.
- https://developers.openai.com/plugins/build/plugins — a skills-only plugin uses .codex-plugin/plugin.json and a skills directory.
- https://learn.chatgpt.com/docs/environments/git-worktrees — worktrees isolate changes but require a Git base.
- Current local skill-creator guidance — keep SKILL.md concise, place detailed policy in references, use scripts only for deterministic needs, and validate frontmatter.
- Current local plugin-creator guidance — do not create MCP, app, hook, or marketplace components unless requested.

External documentation is evidence, not workflow authority. The canonical design, approved program, and current repository state control.

## Current tool and portability evidence

- Codex CLI: 0.146.0.
- Git: 2.50.1.
- Python: 3.14.6.
- Node.js: 24.19.0.
- No repository runtime or dependency policy is approved.

INC-001 therefore uses Python 3 standard-library validation and unittest only. This is a current-increment implementation choice, not a program-wide runtime commitment.

## Resolved implementation choices

- Use official minimal skills-only plugin structure.
- Use plugin identity implementation-plugin and skill identity implementing-staged-plans.
- Use version 0.1.0 for the first unshipped local manifest.
- Omit author, publisher, marketplace, publication, MCP, app, and hook fields.
- Keep the front door concise and add no stage-specific procedure reference before that procedure exists.
- Place the package validator inside the skill because later workflow stages may invoke it.
- Place development tests at repository root.
- Preserve pressure prompts and raw evaluator outputs as repository test evidence.

## Known evidence limitation

The bundled local plugin validator currently requires author and interface identity fields that the approved scope excludes, while current official documentation shows a minimal manifest without those fields. Do not invent identity to satisfy the stricter local helper. INC-001 uses a repository-owned validator for the approved manifest contract and records the discrepancy; public packaging qualification remains an INC-008 concern.

## Execution authorization still required

Plan approval must separately authorize:

- modifying the exact plugin, skill, script, and test files listed in the plan;
- running five ephemeral read-only fresh-context baseline evaluations and five corresponding skill-guided evaluations;
- creating the focused commits listed in the plan;
- using at most one bounded final reviewer after implementation.

Without that authority, the legal next action remains plan revision or plan approval; implementation cannot begin.

## Worktree continuity risk

The current linked worktree is under /private/tmp. Do not rely on it for long-term continuation while program artifacts remain uncommitted. The next approval should either authorize the planned focused commits or select a durable replacement worktree before a system restart or cleanup.
