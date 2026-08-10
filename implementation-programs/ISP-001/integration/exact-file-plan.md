# ISP-001 Post-Closure Integration Decision Plan

**Program id:** ISP-001
**Program revision:** 2
**Increment id:** INC-008 (accepted; binding only, no new increment)
**Integration context:** post-closure commit-boundary and possible draft-pull-request decision evidence
**Source digest:** f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57
**Program digest:** 1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253
**Semantic digest:** 151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f
**Workspace path:** /Users/CoveMB/Code/CoveMB/implementation-plugin
**Workspace branch:** main
**Workspace base:** f14449b8808574c720927aedab5b64871cc63858
**Workspace head:** 53edb8fad2008c7d35b6c17dbb973b24022947fd
**Closed status input:** sequence 71, f041a16399768055b757da2550b73b4e52afbc382cc49dd53d06e040d2912d0e
**Closure approval:** APR-026
**Closure reconciliation:** 7ddac33846fdccb061b11e6c72071b0842877aa776dace4c97a2ee28d30a0f3e
**Closure packet:** d9bef2f326690035c6570ca722eb4ce37071732c97535ef0864ec98ed35dffb5
**Preparation:** `implementation-programs/ISP-001/integration/preparation.md`
**Approval mode:** `approval:full-increment`

## Global constraints

- Add no implementation requirement and do not reopen, supersede, or mutate the closed ISP-001 program.
- Preserve every accepted source, program, traceability, increment, review, handoff, reconciliation, packet, status, approval, authorization, workspace, and user-owned byte except exact append-only or manifest bindings separately authorized by this plan.
- Keep reusable and package-facing names project-neutral.
- Treat logical commit partitioning, local commit creation, branch mutation, remote configuration, push, later-action decision, and draft-PR creation as distinct actions.
- No staging, commit, branch change, remote write, push, pull-request decision or creation, publication, release, deployment, migration, destructive operation, provider mutation, reviewer dispatch, or evaluator dispatch is authorized by this plan or its approval alone.

## Requirements and acceptance binding

This plan advances no atomic implementation requirement. It satisfies revision-2 separate-program-closure item 6 by preparing the separate post-closure question only after `APR-026` closed the exact reconciled program.

Acceptance for a future authorized decision-evidence pass:

1. independently revalidate the exact source, program, semantic, workspace, status, closure, approval-log, authorization-log, manifest, branch, base, HEAD, dirty inventory, conflicts, and operation state;
2. validate a complete non-overlapping logical commit boundary for every current non-ignored changed path without staging;
3. preserve an explicit denial of commit authority unless one exact `create-local-commit` grant names the current path partition and user-selected branch strategy;
4. call `decide_later_action` only if a separate exact `create-draft-pull-request` grant binds the closure evidence, action, scope, and authority context;
5. record that an authorized decision is not push or pull-request creation;
6. stop with evidence and unresolved remote/base/head coordinates, without external mutation.

## File map

### Create if separately authorized

- `implementation-programs/ISP-001/integration/execution-record.md` — record fresh observations, logical-boundary validation, exact command results, authority decisions, and the no-stage/no-commit/no-external-action result.
- `implementation-programs/ISP-001/integration/draft-pull-request-decision.md` — record only the validated `LaterActionDecision`, its exact grant or denial issues, closure bindings, missing remote/base/head coordinates, and the next separate action gate.

### Modify if separately authorized

- `implementation-programs/ISP-001/manifest.json` — add logical roles and exact digests for the two completed integration evidence files without changing `program_status: closed`.
- `implementation-programs/ISP-001/state/approvals.jsonl` — append only a future exact plan-approval or decision-evidence approval record; preserve the existing byte prefix.
- `implementation-programs/ISP-001/state/action-authorizations.jsonl` — append only future exact grants actually supplied by the user; preserve the existing byte prefix.

Explicit interfaces: existing `CommitBoundary` and `validate_commit_boundaries` from `execution_discipline.py`; existing `LaterActionDecision` and `decide_later_action` from `continuity_closure.py`; existing append-only authority records; manifest logical-role mappings. No new schema, reusable symbol, CLI command, or production interface is planned.

### Preserve

- `implementation-programs/ISP-001/state/status.json` — exact closed sequence-71 bytes and digest.
- `implementation-programs/ISP-001/closure/reconciliation.json`, `implementation-programs/ISP-001/closure/program-closure-packet.md`, and all other closure files.
- `implementation-programs/ISP-001/source/**`, `implementation-programs/ISP-001/program/**`, and `implementation-programs/ISP-001/increments/**`.
- `skills/implementing-staged-plans/**` and `tests/**` during decision-evidence execution.
- Git index, refs, commits, remotes, configuration, and external provider state.
- Ignored `.DS_Store`, `__pycache__`, and bytecode paths.

## Semantic naming inventory

The canonical detailed inventory is in `implementation-programs/ISP-001/integration/preparation.md#semantic-naming-inventory`.

| Surface | Kind | Context | Intention | Planning-term basis |
|---|---|---|---|---|
| `integration/execution-record.md` | path | post-closure local evidence | record exact local validation and absent effects | implementation-governance |
| `integration/draft-pull-request-decision.md` | path | later-action authority | persist a decision separately from execution | implementation-governance |
| `accepted-staged-plan-lifecycle` | schema-or-identifier | logical commit partition | name the complete accepted lifecycle by intention | durable-domain |
| `create-draft-pull-request` | schema-or-identifier | accepted action vocabulary | bind only the exact supported decision class | durable-domain |
| `Draft pull request decision` | heading | integration evidence | make the later-action decision boundary explicit | durable-domain |

## Test-first slices and verification contracts

No production behavior changes, so a RED/GREEN slice would be artificial. Use an alternative-verification contract:

- Relevant inputs: the exact controlling tuple above, the fresh repository inspection, the exact sorted changed-path inventory, existing accepted commit/later-action interfaces, and current official GitHub documentation.
- Expected evidence: program, state, closure bundle, package, and full tests pass; the logical path partition is complete; commit authorization is false unless separately granted; later-action decision is not called without its exact separate grant; no staged path, commit, branch change, remote, push, or PR appears.
- Limitation: local static evidence cannot prove remote permissions, remote freshness, GitHub repository identity, PR comparison correctness, reviewer identity, or any external action.

## Commands and expected evidence

Preparation and future preflight commands:

- `rtk git branch --show-current` — expected `main` until the user separately selects and authorizes a branch change.
- `rtk git rev-parse HEAD` — expected `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- `rtk git remote -v` — expected no output for the current preparation; any future remote is material drift requiring refreshed evidence.
- `rtk git status --porcelain=v2 --branch` — expected no staged/conflicted paths and the exact planned inventory.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001` — expected exit 0.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-preparation implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858` — expected exit 0.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/continuity_closure.py validate-bundle implementation-programs/ISP-001/closure/continuity-evidence.json --brief implementation-programs/ISP-001/closure/brief.md --handoff implementation-programs/ISP-001/closure/handoff.md --reconciliation implementation-programs/ISP-001/closure/reconciliation.json --closure-packet implementation-programs/ISP-001/closure/program-closure-packet.md` — expected exit 0.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline tests.test_continuity_closure tests.test_state_authority -v` — expected pass.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — expected complete pass once after the coherent evidence batch.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` — expected exit 0.
- `rtk git diff --check` — expected exit 0 with no output.
- `rtk git diff --cached --quiet` and a before/after `rtk git rev-parse HEAD` comparison — expected proof that no staging or commit occurred.

The exact `validate_commit_boundaries` call must use the sorted path set below, one `CommitBoundary` with identifier `accepted-staged-plan-lifecycle`, the proposed normal-form message, no protected paths, and an explicit unauthorized commit decision. Expected result: the partition itself is complete and the only commit-related issue is `create-local-commit action is not authorized`.

The exact `decide_later_action` call is conditional and must not run until a separate current grant exists. If it runs, its action is `create-draft-pull-request`; its scope must repeat the user-approved remote repository, base, head, and draft-only intent; recovery evidence is `none required`; and the authority context must match the accepted common tuple. Expected result is an authorized or denied decision record, never execution.

## Review scopes and specialist predicates

- Requirements and scope: verify no new requirement, no reopened program, exact closure sequencing, and no inferred later-action authority.
- Architecture and semantic naming: verify reuse of the accepted execution/continuity owners, one coherent logical boundary, no new schema or product surface, and contextual names.
- Test and evidence: verify exact digest/path bindings, append-only prefixes, complete path partition, command results, and accurate static-versus-external limitations.
- Security/privacy: check that no remote URL, credential, identity, environment value, private file content, or secret is persisted or transmitted.
- Reliability/recovery: check branch/base/HEAD drift, active operations, conflicts, partial append evidence, and no destructive recovery.
- External reviewer assurance: not authorized or needed for this planning increment. Any controller assessment is non-independent and reduced assurance.

## Commit boundaries

Current logical boundary: `accepted-staged-plan-lifecycle`.

Purpose: preserve the complete accepted remaining staged-plan lifecycle and closure as one coherent commit candidate because the final manifest, status, traceability, approval ledger, and authorization ledger are shared control-plane owners.

Proposed message: `feat: complete staged-plan lifecycle workflow`.

Dependencies: the committed INC-001 and INC-002 history ending at `53edb8fad2008c7d35b6c17dbb973b24022947fd`.

Exact current non-ignored path set after this preparation:

- `implementation-programs/ISP-001/closure/brief.md`
- `implementation-programs/ISP-001/closure/continuity-evidence.json`
- `implementation-programs/ISP-001/closure/exact-file-plan.md`
- `implementation-programs/ISP-001/closure/handoff.md`
- `implementation-programs/ISP-001/closure/preparation.md`
- `implementation-programs/ISP-001/closure/program-closure-packet.md`
- `implementation-programs/ISP-001/closure/reconciliation.json`
- `implementation-programs/ISP-001/increments/INC-002/handoff-addendum.md`
- `implementation-programs/ISP-001/increments/INC-003/brief.md`
- `implementation-programs/ISP-001/increments/INC-003/exact-file-plan.md`
- `implementation-programs/ISP-001/increments/INC-003/execution-record.md`
- `implementation-programs/ISP-001/increments/INC-003/handoff-addendum.md`
- `implementation-programs/ISP-001/increments/INC-003/handoff.md`
- `implementation-programs/ISP-001/increments/INC-003/preparation.md`
- `implementation-programs/ISP-001/increments/INC-003/review-packet.md`
- `implementation-programs/ISP-001/increments/INC-003/reviews/architecture.md`
- `implementation-programs/ISP-001/increments/INC-003/reviews/requirements.md`
- `implementation-programs/ISP-001/increments/INC-003/reviews/test-evidence.md`
- `implementation-programs/ISP-001/increments/INC-004/brief.md`
- `implementation-programs/ISP-001/increments/INC-004/exact-file-plan.md`
- `implementation-programs/ISP-001/increments/INC-004/execution-record.md`
- `implementation-programs/ISP-001/increments/INC-004/handoff-addendum.md`
- `implementation-programs/ISP-001/increments/INC-004/handoff.md`
- `implementation-programs/ISP-001/increments/INC-004/preparation.md`
- `implementation-programs/ISP-001/increments/INC-004/review-packet.md`
- `implementation-programs/ISP-001/increments/INC-004/reviews/architecture.md`
- `implementation-programs/ISP-001/increments/INC-004/reviews/requirements.md`
- `implementation-programs/ISP-001/increments/INC-004/reviews/test-evidence.md`
- `implementation-programs/ISP-001/increments/INC-005/brief.md`
- `implementation-programs/ISP-001/increments/INC-005/exact-file-plan.md`
- `implementation-programs/ISP-001/increments/INC-005/execution-record.md`
- `implementation-programs/ISP-001/increments/INC-005/handoff-addendum.md`
- `implementation-programs/ISP-001/increments/INC-005/handoff.md`
- `implementation-programs/ISP-001/increments/INC-005/preparation.md`
- `implementation-programs/ISP-001/increments/INC-005/review-packet.md`
- `implementation-programs/ISP-001/increments/INC-005/reviews/architecture.md`
- `implementation-programs/ISP-001/increments/INC-005/reviews/requirements.md`
- `implementation-programs/ISP-001/increments/INC-005/reviews/test-evidence.md`
- `implementation-programs/ISP-001/increments/INC-006/brief.md`
- `implementation-programs/ISP-001/increments/INC-006/exact-file-plan.md`
- `implementation-programs/ISP-001/increments/INC-006/execution-record.md`
- `implementation-programs/ISP-001/increments/INC-006/handoff-addendum.md`
- `implementation-programs/ISP-001/increments/INC-006/handoff.md`
- `implementation-programs/ISP-001/increments/INC-006/preparation.md`
- `implementation-programs/ISP-001/increments/INC-006/review-evidence.json`
- `implementation-programs/ISP-001/increments/INC-006/review-packet.md`
- `implementation-programs/ISP-001/increments/INC-006/reviews/architecture.md`
- `implementation-programs/ISP-001/increments/INC-006/reviews/remediation.md`
- `implementation-programs/ISP-001/increments/INC-006/reviews/requirements.md`
- `implementation-programs/ISP-001/increments/INC-006/reviews/specialist-compatibility.md`
- `implementation-programs/ISP-001/increments/INC-006/reviews/specialist-reliability.md`
- `implementation-programs/ISP-001/increments/INC-006/reviews/specialist-security-privacy.md`
- `implementation-programs/ISP-001/increments/INC-006/reviews/test-evidence.md`
- `implementation-programs/ISP-001/increments/INC-007/brief.md`
- `implementation-programs/ISP-001/increments/INC-007/continuity-evidence.json`
- `implementation-programs/ISP-001/increments/INC-007/exact-file-plan.md`
- `implementation-programs/ISP-001/increments/INC-007/execution-record.md`
- `implementation-programs/ISP-001/increments/INC-007/handoff-addendum.md`
- `implementation-programs/ISP-001/increments/INC-007/handoff.md`
- `implementation-programs/ISP-001/increments/INC-007/preparation.md`
- `implementation-programs/ISP-001/increments/INC-007/review-evidence.json`
- `implementation-programs/ISP-001/increments/INC-007/review-packet.md`
- `implementation-programs/ISP-001/increments/INC-007/reviews/architecture.md`
- `implementation-programs/ISP-001/increments/INC-007/reviews/remediation.md`
- `implementation-programs/ISP-001/increments/INC-007/reviews/requirements.md`
- `implementation-programs/ISP-001/increments/INC-007/reviews/specialist-compatibility.md`
- `implementation-programs/ISP-001/increments/INC-007/reviews/specialist-reliability.md`
- `implementation-programs/ISP-001/increments/INC-007/reviews/specialist-security-privacy.md`
- `implementation-programs/ISP-001/increments/INC-007/reviews/test-evidence.md`
- `implementation-programs/ISP-001/increments/INC-008/brief.md`
- `implementation-programs/ISP-001/increments/INC-008/closure-readiness-evidence.json`
- `implementation-programs/ISP-001/increments/INC-008/exact-file-plan.md`
- `implementation-programs/ISP-001/increments/INC-008/execution-record.md`
- `implementation-programs/ISP-001/increments/INC-008/handoff-addendum.md`
- `implementation-programs/ISP-001/increments/INC-008/handoff.md`
- `implementation-programs/ISP-001/increments/INC-008/integration-evidence.json`
- `implementation-programs/ISP-001/increments/INC-008/preparation.md`
- `implementation-programs/ISP-001/increments/INC-008/review-evidence.json`
- `implementation-programs/ISP-001/increments/INC-008/review-packet.md`
- `implementation-programs/ISP-001/increments/INC-008/reviews/architecture.md`
- `implementation-programs/ISP-001/increments/INC-008/reviews/remediation.md`
- `implementation-programs/ISP-001/increments/INC-008/reviews/requirements.md`
- `implementation-programs/ISP-001/increments/INC-008/reviews/specialist-compatibility.md`
- `implementation-programs/ISP-001/increments/INC-008/reviews/specialist-reliability.md`
- `implementation-programs/ISP-001/increments/INC-008/reviews/specialist-security-privacy.md`
- `implementation-programs/ISP-001/increments/INC-008/reviews/test-evidence.md`
- `implementation-programs/ISP-001/integration/brief.md`
- `implementation-programs/ISP-001/integration/exact-file-plan.md`
- `implementation-programs/ISP-001/integration/preparation.md`
- `implementation-programs/ISP-001/manifest.json`
- `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
- `implementation-programs/ISP-001/state/action-authorizations.jsonl`
- `implementation-programs/ISP-001/state/approvals.jsonl`
- `implementation-programs/ISP-001/state/status.json`
- `skills/implementing-staged-plans/SKILL.md`
- `skills/implementing-staged-plans/references/continuity-closure.md`
- `skills/implementing-staged-plans/references/execution-discipline.md`
- `skills/implementing-staged-plans/references/repository-preparation.md`
- `skills/implementing-staged-plans/references/review-coordination.md`
- `skills/implementing-staged-plans/references/state-authorization.md`
- `skills/implementing-staged-plans/scripts/continuity_closure.py`
- `skills/implementing-staged-plans/scripts/execution_discipline.py`
- `skills/implementing-staged-plans/scripts/repository_preparation.py`
- `skills/implementing-staged-plans/scripts/review_coordination.py`
- `skills/implementing-staged-plans/scripts/state_authority.py`
- `skills/implementing-staged-plans/scripts/validate_package.py`
- `tests/fixtures/continuity-closure/portable-catalog-run/closure-packet.md`
- `tests/fixtures/continuity-closure/portable-catalog-run/closure-reconciliation.json`
- `tests/fixtures/continuity-closure/portable-catalog-run/continuity-evidence.json`
- `tests/fixtures/continuity-closure/portable-catalog-run/handoff.md`
- `tests/fixtures/continuity-closure/portable-catalog-run/next-increment-brief.md`
- `tests/fixtures/execution-discipline/portable-archive-run/scenarios.json`
- `tests/fixtures/integrated-pressure/portable-library-program/pilot-contract.json`
- `tests/fixtures/integrated-pressure/portable-library-program/source/implementation-plan.md`
- `tests/fixtures/repository-preparation/portable-archive-workspace/evidence.json`
- `tests/fixtures/repository-preparation/portable-archive-workspace/exact-file-plan.md`
- `tests/fixtures/repository-preparation/portable-archive-workspace/scenarios.json`
- `tests/fixtures/review-coordination/portable-archive-run/review-evidence.json`
- `tests/fixtures/review-coordination/portable-archive-run/review-packet.md`
- `tests/fixtures/state-authorization/portable-archive-run/increments/archive-index/brief.md`
- `tests/fixtures/state-authorization/portable-archive-run/increments/archive-index/exact-file-plan.md`
- `tests/fixtures/state-authorization/portable-archive-run/increments/archive-index/review-packet.md`
- `tests/fixtures/state-authorization/portable-archive-run/state/action-authorizations.jsonl`
- `tests/fixtures/state-authorization/portable-archive-run/state/approvals.jsonl`
- `tests/fixtures/state-authorization/portable-archive-run/state/status.json`
- `tests/fixtures/state-authorization/portable-archive-run/state/workspace.json`
- `tests/integrated_pressure_support.py`
- `tests/pressure/integrated/prompts/direct-request.md`
- `tests/pressure/integrated/prompts/incomplete-request.md`
- `tests/pressure/integrated/prompts/indirect-request.md`
- `tests/pressure/integrated/prompts/non-triggering-request.md`
- `tests/pressure/integrated/prompts/unsupported-action.md`
- `tests/pressure/integrated/results/direct-request.txt`
- `tests/pressure/integrated/results/incomplete-request.txt`
- `tests/pressure/integrated/results/indirect-request.txt`
- `tests/pressure/integrated/results/non-triggering-request.txt`
- `tests/pressure/integrated/results/unsupported-action.txt`
- `tests/pressure/integrated/scenarios.json`
- `tests/pressure/integrated/verdicts.json`
- `tests/test_continuity_closure.py`
- `tests/test_execution_discipline.py`
- `tests/test_front_door_contract.py`
- `tests/test_integrated_pressure.py`
- `tests/test_package_validation.py`
- `tests/test_program_authority.py`
- `tests/test_repository_preparation.py`
- `tests/test_review_coordination.py`
- `tests/test_state_authority.py`

Every path above belongs exactly once to this logical boundary. No staging or commit is authorized. The two future evidence files in the Create map are not part of this frozen current boundary; if they are later created, refresh the partition before requesting commit authority.

## Rollback and recovery

- Source-code domain: no write outside the three future integration evidence/control-plane paths is planned. Repair an unbound evidence file only with attributed `apply_patch`; once digest-bound, correct it through an append-only/addendum path. Never reset, clean, stash, restore, or overwrite user work.
- Persistent-data domain: not touched. A Git commit or revert is not data backup or restoration.
- Deployment domain: not touched. No artifact publication or environment mutation is planned.
- Provider/external-state domain: not touched. Reading official documentation does not configure a remote or prove GitHub permissions. Any later remote mutation needs exact provider-specific authority and verification.
- If an append succeeds and a later manifest write fails, preserve the appended record as inert evidence, report partial receipts, revalidate its exact prefix/digests, and require renewed authority before retry.
- Any branch/base/HEAD/remote/status/manifest/log/closure/path inventory drift invalidates the plan.

## Approval required to execute

This exact-file plan is the approval target. Approval of its digest authorizes no action by itself.

A future execution requires all of the following:

1. exact plan approval bound to the current source/program/semantic/workspace/status/closure tuple and this plan digest;
2. exact `write-program-artifact` authorization for only `integration/execution-record.md`, conditional `integration/draft-pull-request-decision.md`, the named manifest binding, and append-only records;
3. a user-supplied remote repository, remote name, PR base branch and commit, and topic-branch name before any affirmative readiness claim;
4. separate branch-change authority before creating or switching a branch;
5. separate `create-local-commit` authority before staging or committing the frozen or refreshed logical boundary;
6. separate `create-draft-pull-request` grant before calling the later-action decision function; that grant authorizes only the decision under the accepted continuity contract;
7. later, separate push and draft-PR creation authority before any external mutation.

Under `approval:full-increment`, a properly authorized evidence pass may proceed through local verification and decision recording, then must stop for user inspection. It must not stage, commit, push, create a pull request, or continue into another action unless each exact separate grant exists.

Mandatory stop now: review this exact-file plan. No staging, commit, branch change, remote action, pull-request decision, or pull-request creation has occurred.
