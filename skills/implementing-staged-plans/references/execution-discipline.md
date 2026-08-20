# Execution Discipline

Use this procedure only after the current repository, program, workspace, exact-file plan, execution baseline, and action authorization have been revalidated. Require an exact plan-approval event only when the persisted mode and status contract requires it. The mechanical boundary is [`execution_discipline.py`](../scripts/execution_discipline.py). It validates caller-supplied evidence and decisions; it does not modify files, persist lifecycle state, stage paths, create commits, call a provider, or recover external state.

## Prerequisites and bindings

Load the manifest-owned current status, brief, preparation, exact-file plan, execution baseline, approvals, action authorizations, and workspace. Inspect the repository again immediately before the first production write. Standard mode requires the prompt-bound exact-plan approval event. Pre-approve and full-increment modes require the status-current increment grant, validated exact plan, execution baseline, and exact plan-bound action authorization without inventing a plan-approval event. In every mode require the selected branch, base, head, source, program, semantic digest, plan digest, baseline, and authorized action scope to match.

Before the execution baseline exists, repository dirt must equal the normalized launch observation. After it exists, validate product paths by disposition and lifecycle state: `authorized` permits no product delta; `implementing` permits any subset of declared Create and Modify work; `reviewing` and later require every declared Create path to exist and every declared Modify path to differ from its baseline while Preserve remains byte-identical. Reject new staged, conflicted, unmapped, deleted, unsafe, or changed user-owned paths.

For successor increments, validate every nonempty `inherited_paths` entry against the canonical rollover chain, matching accepted product bytes, and exact `Modify` or `Preserve` ownership. Inherited accepted history is not user-owned dirt and must not be merged into `user_work_baselines`. First-increment and frozen legacy baselines remain byte-compatible with `inherited_paths: []`.

## Meaningful test-first evidence

For behavioral work, write one focused test before production code and observe it fail nonzero for the intended missing behavior. Record a stable slice identifier, purpose, exact command, expected and observed failure, exit status, confirmation that RED preceded the production change, intended-reason match, focused GREEN command and result, and RED-before-GREEN ordering. A test that passes immediately, fails from a harness error, or records a different reason is not test-first evidence.

## Alternative verification

Use an alternative contract only when a behavioral test would be artificial for a declarative, documentation, manifest, reference, or non-behavioral fixture surface. Record why test-first is artificial, the exact command, expected and observed evidence, zero exit, every relevant input, and the residual limitation. Do not use this path when meaningful behavioral testing is available. Structural validation does not prove that an agent will follow prose at runtime.

## Reuse and ownership

Reuse accepted preparation validators instead of copying their ownership or overlap rules. Require exact equality between planned and actual changed paths. Give each path one disposition and exact owner. Accepted dirty overlaps need their controlling owner and an explicit extend or preserve decision. Preserve fingerprints must remain equal. Managed, generated, or application-owned paths need the owning mechanism and an exact regeneration or verification command. Reject unrelated cleanup, missing paths, duplicate ownership, and unaccepted overlap.

## Semantic-surface coverage

Inventory every created or renamed symbol, command, test or fixture, heading, schema or identifier, and every created or generated path exactly once. Delegate contextual naming and compatibility decisions to repository preparation. A physical path rename is unsupported because Create/Modify/Preserve has no deletion or typed old/new migration disposition; it requires a future approved migration contract. Reject coordinate-shaped planning names unless a specific implementation-governance artifact or durable domain concept owns them. Existing public, persisted, generated, or external names require an explicit compatibility or migration disposition.

## Bounded approach autonomy

The active approval mode controls routine interruptions, not requirements or action authority. A bounded mechanism change may proceed only when concrete evidence exists, all obligations remain intact, no user-owned decision remains, affected surfaces are named, reversal or recovery is credible, and renewed review is recorded. Preserve the exact-plan scope and stop at the first missing condition.

## Amendment decisions

Classify with the accepted preparation policy. An authoritative contradiction or a change to a program dimension always stops for program-level resolution. A minor path, helper, or test-convention correction may proceed only with a complete record. Under the standard mode, a material implementation change requires renewed exact-plan approval. Other supported preapproved modes may proceed with a complete bounded-amendment record; they do not waive review or action authority.

## Logical commit boundaries and separate authority

Partition the actual changed paths into stable, ordered, non-overlapping logical boundaries with a purpose, normal-form message, dependencies, and nonempty path set. Every changed path appears exactly once; protected and unplanned paths appear nowhere. Validate the partition without staging. Separately check an exact `create-local-commit` authorization through state authority. A valid logical partition never implies permission to stage or commit.

## Recovery domains

Record exactly four independent domains: source code, persistent data, deployment, and provider or external state. A touched domain needs its own mechanism, verification, limitation, and consequential-action authority. An untouched domain needs an explicit `not-touched` disposition. Git rollback is a source-code mechanism only; it never proves data restoration, deployment rollback, or provider reconciliation.

## Deviations and hard stops

Record the evidence, preserved obligations, affected surfaces, recovery, review consequence, and classification for every deviation. Stop on a contradiction, program amendment, unresolved user decision, absent recovery, missing semantic inventory, unowned path, incomplete evidence, missing action grant, or unsupported approval mode. Never broaden a bounded implementation change into adjacent cleanup or a later increment.

## Validation commands

Run the smallest focused behavioral tests first, followed by the structural tests and package validator named by the exact-file plan. Then run the full relevant suite once on the coherent tree. Record command, relevant inputs, exit status, and concise output. Use a separate exact action check for commit authority, and retain read-only Git evidence that no staging or commit occurred.

Static and local evidence does not prove live agent activation, review independence, deployment state, data restoration, provider recovery, publication, production safety, or hostile-concurrency guarantees.

## Bounded result

Return the authority tuple, lifecycle state, RED/GREEN or alternative evidence, ownership and naming results, amendment decision, logical commit partition, separate commit-authority decision, all four recovery dispositions, review assurance, deviations, verification results, and next legal action. Stop at the lifecycle gate required by the current approval mode.
