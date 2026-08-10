# Execution Discipline, Amendments, Commit Boundaries, and Recovery Implementation Plan

**Goal:** Implement a project-neutral, non-mutating execution boundary that proves meaningful RED/GREEN or explicit alternative verification, protects ownership and semantic naming, classifies bounded approach changes under the active mode, validates focused logical commit slices, and keeps recovery domains distinct.

**Architecture:** Add one standard-library `execution_discipline.py` module containing immutable evidence records and pure validators. Compose the accepted `repository_preparation` amendment, naming, and overlap contracts with `state_authority` approval-mode and action decisions. Add one concise operator reference and one neutral prepared-execution fixture; the module never stages paths or creates commits.

**Tech stack:** Python 3.14 standard library, `unittest`, JSON fixtures, existing program/state/preparation/package validators, and read-only Git inspection.

## Global constraints

- Program ID: `ISP-001`; program revision: `2`; increment ID: `INC-005`.
- Source digest: `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program digest: `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Accepted traceability digest: `07258dbd177bf08e7f1e7eb1d40cc769a9bdc115b38d05bc3d93e81de0e985a2`.
- Semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`; implementation and verification evidence may change, but ordered semantic fields and this digest must not.
- Preparation evidence digest: `f5c643f33d9cfd38d4feb69f9058d93f620081c94a33e547e4bcfb6133f54913`.
- Workspace path: `/Users/CoveMB/Code/CoveMB/implementation-plugin`; workspace branch: `main`; workspace base: `f14449b8808574c720927aedab5b64871cc63858`; workspace head: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Approval mode is `approval:full-increment`, but the user-imposed exact-plan approval gate remains controlling.
- Preserve SOURCE-001, SOURCE-002, both program revisions, accepted INC-001 through INC-004 evidence, accepted dirty work, and all unrelated or user-owned work byte-for-byte.
- Keep reusable, package-facing, test, fixture, schema, command, and generated names project-neutral. Governance artifacts may retain required ISP/INC/SOURCE/requirement/approval/authorization coordinates.
- Use standard-library Python and existing repository mechanisms; add no dependency, runtime, provider, network integration, schema framework, application component, hook, marketplace entry, publisher surface, or CI workflow.
- Use strict RED-GREEN-REFACTOR for behavioral changes. Non-behavioral work must have a complete alternative verification contract.
- Do not stage or create a commit. Logical commit boundaries are review artifacts only unless a later exact `create-local-commit` grant names the boundary and paths.
- Stop at INC-005 `awaiting-diff-approval`; do not begin INC-006, close the program, or perform any consequential external action.

## Requirements and acceptance binding

This plan advances `REQ-AUTHORITY`, `REQ-EXECUTION-AMENDMENT`, `REQ-VALIDATION`, `REQ-SEQUENCE`, `REQ-DEFAULTS`, `REQ-SEMANTIC-NAMING`, and `REQ-DESIGN-RISKS`. Direct implementation evidence is added only to atomic records demonstrated by INC-005.

Acceptance is exact:

1. test-first claims contain observed failure for the intended reason;
2. non-behavioral work records an explicit alternative verification contract;
3. unrelated cleanup and pre-existing user work remain untouched;
4. roadmap-derived implementation names fail context-aware validation while implementation-governance artifacts and justified durable domain concepts remain valid;
5. minor corrections, implementation amendments, program amendments, and contradictions classify correctly;
6. source, data, deployment, and provider recovery remain distinct.

Integration checkpoint: one neutral repository fixture advances through accepted preparation contracts and execution validation with a bounded, evidence-backed amendment. It creates no commit.

## File map

### Create during implementation

- `skills/implementing-staged-plans/scripts/execution_discipline.py` — immutable evidence types and pure execution validators; no repository mutation.
- `skills/implementing-staged-plans/references/execution-discipline.md` — focused operator procedure and front-door target.
- `tests/test_execution_discipline.py` — focused behavioral, matrix, integration, and CLI-free contract tests.
- `tests/fixtures/execution-discipline/portable-archive-run/scenarios.json` — neutral preparation-to-execution catalog including bounded amendment, naming, ownership, commit-boundary, and recovery cases.
- `implementation-programs/ISP-001/increments/INC-005/execution-record.md` — observed RED/GREEN or alternative evidence, amendments, ownership, naming, logical commit slices, and lifecycle receipts.
- `implementation-programs/ISP-001/increments/INC-005/reviews/requirements.md` — raw non-independent requirements review.
- `implementation-programs/ISP-001/increments/INC-005/reviews/architecture.md` — raw non-independent architecture, naming, ownership, commit, and recovery review.
- `implementation-programs/ISP-001/increments/INC-005/reviews/test-evidence.md` — raw non-independent evidence-validity review.
- `implementation-programs/ISP-001/increments/INC-005/review-packet.md` — human review packet.
- `implementation-programs/ISP-001/increments/INC-005/handoff.md` — durable awaiting-diff-approval handoff.

### Modify during implementation

- `skills/implementing-staged-plans/SKILL.md` — add one execution-discipline route; preserve existing front-door gates.
- `skills/implementing-staged-plans/scripts/validate_package.py` — require the new reference/module assets through the existing asset tuple.
- `tests/test_package_validation.py` — prove required regular-file and symlink behavior for the new assets.
- `tests/test_front_door_contract.py` — prove the concise route and retained authority boundaries.
- `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json` — add only directly demonstrated INC-005 evidence; preserve semantic fields/digest.
- `implementation-programs/ISP-001/manifest.json` — keep current INC-005 artifact roles and lifecycle binding current.
- `implementation-programs/ISP-001/state/status.json` — accepted lifecycle transitions and final awaiting-diff-approval evidence.
- `implementation-programs/ISP-001/state/approvals.jsonl` — append only the later exact plan approval and any later diff decision; never rewrite accepted events.
- `implementation-programs/ISP-001/state/action-authorizations.jsonl` — append only later exact non-commit implementation and lifecycle grants; never rewrite accepted grants.
- `implementation-programs/ISP-001/increments/INC-005/exact-file-plan.md` — amend only under the approved amendment policy, preserving prior digest/addendum evidence.

### Already created at this preparation gate

- `implementation-programs/ISP-001/increments/INC-005/brief.md` — lean current brief.
- `implementation-programs/ISP-001/increments/INC-005/preparation.md` — repository evidence, design decision, naming inventory, and risks.
- `implementation-programs/ISP-001/increments/INC-005/exact-file-plan.md` — this approval-bound implementation contract.

### Preserve without modification

- `implementation-programs/ISP-001/source/implementation-plan.md`
- `implementation-programs/ISP-001/source/revisions/SOURCE-002/implementation-plan.md`
- `implementation-programs/ISP-001/program/implementation-program.md`
- `implementation-programs/ISP-001/program/revisions/revision-2/implementation-program.md`
- `implementation-programs/ISP-001/increments/INC-001/`
- `implementation-programs/ISP-001/increments/INC-002/`
- `implementation-programs/ISP-001/increments/INC-003/`
- `implementation-programs/ISP-001/increments/INC-004/`
- every path outside the exact create/modify map, including all unrelated user-owned work.

### Interfaces and ownership

- Consume `repository_preparation.AmendmentProposal`, `classify_plan_amendment`, `SemanticNameRecord`, `validate_semantic_naming_inventory`, and `validate_plan_overlap`; do not copy their policy tables or regular expressions.
- Consume `state_authority.APPROVAL_MODE_POLICIES`, `ActionBinding`, `AuthorizationDecision`, and `decide_action_authorization`; approval mode never grants `create-local-commit`.
- Produce `TestFirstEvidence`, `AlternativeVerificationContract`, `OwnershipBoundary`, `ExecutionSurface`, `ExecutionAmendmentDecision`, `CommitBoundary`, `RecoveryDomainPlan`, `validate_execution_evidence`, `validate_execution_ownership`, `validate_execution_surfaces`, `decide_execution_amendment`, `validate_commit_boundaries`, and `validate_recovery_domains`.
- `execution_discipline.py` is read-only and pure except for loading caller-supplied JSON-compatible records if a loader is needed. It must not invoke `git add`, `git commit`, state persistence, network calls, or external providers.
- Current governance mutation remains owned by accepted state-authority compare-and-swap/append mechanisms. Review-packet validation remains INC-006.

## Semantic naming inventory

| Surface | Kind | Context | Intention | Origin | Planning-term basis | Basis owner | Compatibility class | Compatibility disposition |
|---|---|---|---|---|---|---|---|---|
| `execution_discipline.py` | path | authorized increment execution | validate evidence and execution boundaries | new | none | none | private | new internal module; no migration |
| `execution-discipline.md` | path | operator procedure | route execution safeguards | new | none | none | package | new required asset; package tests lock it |
| `implementation-execution-evidence/v1` | schema-or-identifier | durable execution evidence | reject incompatible records | new | durable-domain | execution evidence schema | persisted | versioned schema; unsupported versions fail |
| `TestFirstEvidence` | symbol | behavioral evidence | prove intended RED precedes GREEN | new | none | none | private | new internal API |
| `AlternativeVerificationContract` | symbol | non-behavioral evidence | record exact proof and limitation | new | none | none | private | new internal API |
| `OwnershipBoundary` | symbol | protected paths | enforce preserve, extend, and managed ownership | new | none | none | private | new internal API |
| `ExecutionSurface` | symbol | touched implementation surfaces | require complete naming inventory coverage | new | none | none | private | new internal API |
| `ExecutionAmendmentDecision` | symbol | current approach changes | apply mode and plan-gate consequences | new | none | none | private | new internal API |
| `CommitBoundary` | symbol | logical commit plan | partition changed paths without committing | new | none | none | private | new internal API |
| `RecoveryDomainPlan` | symbol | recovery analysis | keep four recovery domains distinct | new | durable-domain | recovery domain contract | private | new internal API |
| `validate_execution_evidence` | symbol | current execution | validate RED/GREEN and alternative contracts | new | none | none | private | new internal API |
| `validate_execution_ownership` | symbol | changed path set | reject unrelated cleanup and protected drift | new | none | none | private | new internal API |
| `validate_execution_surfaces` | symbol | created/renamed names | enforce one-to-one contextual naming records | new | none | none | private | new internal API |
| `decide_execution_amendment` | symbol | execution deviation | preserve accepted classification precedence | new | none | none | private | new internal API |
| `validate_commit_boundaries` | symbol | logical commit slices | enforce complete, unique, ordered coverage | new | none | none | private | new internal API |
| `validate_recovery_domains` | symbol | stateful recovery | reject Git-only external recovery | new | none | none | private | new internal API |
| `portable-archive-run` | test-or-fixture | neutral repository fixture | exercise preparation-to-execution integration | new | none | none | test | synthetic fixture; no migration |
| INC-005 governance artifacts | heading | implementation governance | bind planning, evidence, review, and handoff | new | implementation-governance | ISP-001 manifest | repository-only | required governance identifiers |

## Test-first slices and verification contracts

### Task 0: Bind plan approval and non-commit implementation authority

**Files:**

- Modify: `implementation-programs/ISP-001/state/approvals.jsonl`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl`
- Modify: `implementation-programs/ISP-001/state/status.json`

**Produces:** One exact plan approval and one separate implementation grant before package/test/fixture writes. Commit authority remains absent.

- [ ] Revalidate SOURCE-001/SOURCE-002, both program revisions, semantic digest, INC-004 accepted bindings, branch/base/head, active operation, full dirty inventory, brief digest, preparation digest, and this plan digest.
- [ ] Append one `implementation-approval/v1` `exact-file-plan-approval` event binding INC-005, the current tuple, and the user gate.
- [ ] Append one `implementation-action-authorization/v1` grant limited to the exact create/modify map, strict test-first/alternative evidence, deterministic local verification, three separate non-independent reviews, and evidence-backed material remediation. Exclude staging, `create-local-commit`, and all external/consequential actions.
- [ ] Advance INC-005 only from `awaiting-plan-approval` to `authorized` through accepted state authority. Do not mark `implementing` before Task 1 RED is about to be written.

### Task 1: Define execution contracts and observe RED

**Files:**

- Create: `tests/test_execution_discipline.py`
- Create: `tests/fixtures/execution-discipline/portable-archive-run/scenarios.json`

**Interfaces:**

- Consumes: accepted preparation/state types and neutral repository-preparation fixture conventions.
- Produces: executable contracts for every public record and function listed under Interfaces and ownership.

- [ ] Add schema/field tests for test-first evidence: nonempty stable slice identifier and purpose, exact command, expected/observed failure, nonzero RED exit, `observed_before_production_change=true`, intended-reason match, focused GREEN command/result, and immutable evidence ordering.
- [ ] Add alternative-verification tests: allowed non-behavioral kinds, explicit reason TDD is artificial, exact command, expected/observed evidence, zero exit, relevant inputs, and residual limitation. Reject using alternative verification to bypass a meaningful behavioral test.
- [ ] Add ownership tests: every actual changed path must be planned; preserve fingerprints remain equal; extend/create paths have exact owners; managed/generated/application-owned paths name owning mechanism and verification; unrelated cleanup and unaccepted overlap fail.
- [ ] Add execution-surface tests across every accepted surface kind. Require exact one-to-one created/renamed inventory coverage; reject roadmap-only coordinates; accept specific implementation-governance ownership and justified durable domain concepts; require compatibility disposition for existing public/persisted/generated/external names.
- [ ] Add amendment tests for minor correction, bounded implementation amendment in all five modes, material plan change under standard, program dimensions, unknown labels, unresolved user decisions, absent evidence/recovery, and authoritative contradiction.
- [ ] Add commit-boundary tests for empty, duplicate, overlapping, missing, extra, protected, incoherently ordered, unknown dependency, and complete non-overlapping path partitions. Assert that no validator creates or implies a commit.
- [ ] Add recovery tests requiring exactly `source-code`, `persistent-data`, `deployment`, and `provider-or-external-state`; touched domains need mechanism/evidence/authority; `git-revert` is valid only for source code and never completes external recovery.
- [ ] Add the neutral integration scenario: accepted preparation inputs, observed RED/GREEN, protected ownership, contextual names, a bounded evidence-backed mechanism amendment under `approval:full-increment`, logical commit slices, and all four recovery dispositions pass without a commit.
- [ ] Run `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline -v`. Expected RED: import fails because `skills/implementing-staged-plans/scripts/execution_discipline.py` does not exist. Persist the exact failure and tree state before production code.

### Task 2: Implement evidence, ownership, and semantic execution surfaces

**Files:**

- Create: `skills/implementing-staged-plans/scripts/execution_discipline.py`
- Modify: `tests/test_execution_discipline.py` only when the harness, not an accepted contract, is wrong.

**Produces:** Evidence, ownership, and naming records plus their pure validators.

- [ ] Define `EXECUTION_EVIDENCE_SCHEMA = "implementation-execution-evidence/v1"`, immutable allowed kind/domain sets, frozen dataclasses, strict type checks that reject booleans as integers, and deterministic sorted issues.
- [ ] Implement `validate_execution_evidence`. A TDD record passes only when the observed pre-change command failed nonzero for the explicitly matched intended reason and its focused GREEN evidence passes. An alternative record passes only for a named non-behavioral surface with complete proof and limitation.
- [ ] Implement `validate_execution_ownership`. Compare exact planned and actual path sets, require every ownership disposition, check preserve fingerprints, reuse accepted overlap rules, and require owning mechanism/verification for managed or generated paths.
- [ ] Implement `validate_execution_surfaces`. Require exact set equality between created/renamed surfaces and naming records, reject duplicates or omissions, then delegate contextual classification and compatibility to `validate_semantic_naming_inventory`.
- [ ] Run focused evidence, ownership, and naming test classes. Expected: Task 2 tests pass; amendment/commit/recovery/integration tests remain RED.

### Task 3: Implement amendments, logical commits, and recovery domains

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/execution_discipline.py`
- Modify: `tests/test_execution_discipline.py` only when the harness, not an accepted contract, is wrong.

**Produces:** Mode-aware execution-amendment decisions, logical commit partitions, separate commit authority, recovery-domain validation, and integrated bundle validation.

- [ ] Implement `decide_execution_amendment` by calling `classify_plan_amendment`. Contradictions and program amendments always stop. Minor corrections may proceed when their required record is complete. Bounded amendments may proceed in `approval:pre-approve`, `approval:full-increment`, `approval:full-diff`, or `approval:full` only with evidence, preserved obligations, no user-owned decision, affected surfaces, recovery/reversal, and renewed review. Under `approval:standard`, a material plan change requires renewed exact-plan approval.
- [ ] Implement `validate_commit_boundaries` as a pure partition check. Require stable IDs, purpose, normal-form message, dependency order, nonempty path sets, one boundary per actual changed path, no protected/unplanned path, and no duplicate assignment. Return a separate exact action-authority issue when no `create-local-commit` grant is supplied; never invoke Git mutation.
- [ ] Implement `validate_recovery_domains` with exactly four domain records. Untouched domains need an explicit `not-touched` disposition; touched domains need domain-specific recovery, verification, limitation, and any consequential-action authorization. Reject Git/source rollback as data, deployment, or provider recovery.
- [ ] Implement one integrated validator for the neutral fixture that composes all accepted and new decisions without repository mutation or invented review/packet completion.
- [ ] Run `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline -v`. Expected: all execution-discipline tests pass.

### Task 4: Add the focused procedure and front-door/package route

**Files:**

- Create: `skills/implementing-staged-plans/references/execution-discipline.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Modify: `tests/test_package_validation.py`
- Modify: `tests/test_front_door_contract.py`

**Produces:** A concise discoverable route with explicit alternative verification for declarative/package changes.

- [ ] Extend structural tests first. Require the execution reference/module as regular non-symlink assets, require one narrow front-door route, retain project-neutral naming and all universal gates, and record the intended RED for missing assets/route.
- [ ] Write `execution-discipline.md` in this order: prerequisites/bindings; meaningful test-first evidence; alternative verification; reuse/ownership; semantic-surface coverage; bounded approach autonomy; amendment decisions; logical commit boundaries and separate authority; recovery domains; deviations/hard stops; validation commands; bounded result.
- [ ] Add one front-door section routing authorized execution evidence, ownership, naming, amendments, logical commit boundaries, and recovery to the new reference. Do not duplicate its rules or alter review/continuity routes.
- [ ] Extend the existing package asset tuple and focused tests. Keep deterministic issue ordering and prior package contracts.
- [ ] Record this alternative verification contract in the INC-005 execution record: non-behavioral surfaces are reference/front-door/asset declarations; exact commands are the focused structural tests, package validator, skill validator, and link/naming scans they perform; expected and observed evidence is zero exit with the new regular assets and route discovered; limitation is that structural checks do not prove agent execution behavior.
- [ ] Run the focused structural tests and package validation. Expected: all pass after the assets/route exist.

### Task 5: Exercise preparation-to-execution integration and record direct evidence

**Files:**

- Modify: `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
- Modify: `implementation-programs/ISP-001/manifest.json`
- Modify: `implementation-programs/ISP-001/state/status.json`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl` only for authorized lifecycle records.
- Create/modify: `implementation-programs/ISP-001/increments/INC-005/execution-record.md`

**Produces:** Current-program execution evidence without staging or commit creation.

- [ ] Re-run accepted live repository inspection and current plan validation immediately before the first production write; stop on any new drift or binding issue.
- [ ] Execute the neutral fixture through accepted preparation decisions and the new integrated execution validator. Its mechanism change must classify as a bounded implementation amendment, preserve outcome/contracts/risk/acceptance, name affected surfaces, include reversal/recovery, and pass under `approval:full-increment`.
- [ ] Validate the actual INC-005 changed-path set against ownership and semantic surface inventories. Prove all preserve fingerprints remain unchanged and no actual path is omitted from logical commit boundaries.
- [ ] Prove commit authority remains absent with an exact `create-local-commit` action check. Do not run `git add` or `git commit`; record logical boundaries only.
- [ ] Update only directly demonstrated INC-005 `implementation_evidence` and `verification_evidence` arrays. Recompute and assert semantic digest `151cbe...10f`; stop if it changes.
- [ ] Transition through `implementing` only at the first RED, then `reviewing` after freezing the complete non-commit diff. Use accepted atomic status writes and exact non-commit grants.

### Task 6: Review, remediate, verify, and build the INC-005 packet

**Files:**

- Create: the INC-005 execution record, three reviews, review packet, and handoff listed above.
- Modify: revision-2 traceability, manifest, status, approvals, and action authorizations only as authorized.

**Produces:** A reviewed INC-005 diff at `awaiting-diff-approval`, with no commit and no INC-006 work.

- [ ] Freeze the proposed diff and record exact changed/untracked paths, protected accepted paths, base/head, plan/preparation/source/program/semantic digests, and absence of staged paths and commits.
- [ ] Run separate non-independent requirements, architecture, and test-evidence reviews. Requirements checks all six criteria and seven groups. Architecture checks pure/authority boundaries, ownership fingerprints, semantic coverage, amendment precedence/modes, commit partitioning/no mutation, four recovery domains, simplicity, and later-increment exclusions. Test-evidence checks intended RED reason, GREEN/alternative evidence, negative matrices, fixture integration, protected bytes, absent commit authority, and static-versus-runtime limits. Persist each raw review before reconciliation and label assurance reduced/non-independent.
- [ ] Repair only evidence-backed material INC-005 findings. Record invariant, location, impact, confidence, smallest repair, and affected reruns. Stop for a program amendment if remediation changes requirements, acceptance, scope, public behavior, protected contracts, security/privacy, risk, data ownership, dependencies, sequencing, or review cadence.
- [ ] Run fresh final verification once on the coherent final tree using the exact commands below.
- [ ] Build the review packet with criterion mapping, files/interfaces, RED/GREEN/alternative evidence, ownership/naming/amendment/commit/recovery decisions, fixture integration, reviews/findings/repairs, deviations, semantic digest, risks/limits, workspace/base/head, no-stage/no-commit evidence, current state, and next legal action.
- [ ] End at `awaiting-diff-approval`. Do not accept the diff, create a commit, begin INC-006, close the program, or perform any consequential action.

## Commands and expected evidence

Focused RED/GREEN and structural commands:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_front_door_contract -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: the first invocation records the missing-module RED before implementation; focused execution classes turn green slice by slice; structural tests first fail for the missing assets/route and then pass. No command stages or creates a commit.

Fresh final verification:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-preparation implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-plan implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858 --preparation implementation-programs/ISP-001/increments/INC-005/preparation.md --plan implementation-programs/ISP-001/increments/INC-005/exact-file-plan.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans
rtk git diff --check
rtk git status --porcelain=v2 --branch
```

Expected: full tests, package/program/preparation/plan/skill validation, whitespace, and bounded status checks pass; status reports no staged/conflicted paths and unchanged head. Static/local checks do not prove live agent activation, review independence, deployment, provider recovery, or production behavior.

Negative evidence retained:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline.ExecutionEvidenceTests.test_red_must_fail_for_the_intended_reason -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline.SemanticSurfaceTests.test_roadmap_coordinate_is_rejected_but_governance_and_domain_names_pass -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline.CommitBoundaryTests.test_boundary_partition_never_implies_commit_authority -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline.RecoveryDomainTests.test_git_revert_cannot_satisfy_external_recovery -v
```

Expected: all regression tests pass by rejecting the invalid record while accepting the paired valid context. These are validators' negative cases, not actual commit or external-recovery actions.

## Review scopes and specialist predicates

- Required: requirements/scope, architecture/boundaries/semantic naming/simplicity, and test/evidence validity as three separately persisted passes.
- Review mode: controller self-review, explicitly non-independent with reduced assurance. No subagent or external evaluator is authorized by this plan.
- Security/privacy predicate: bounded internal review is required because ownership records fingerprint repository paths and evidence records may contain command output. Check path containment, digest-only protected evidence, no file contents/secrets/environment persistence, deterministic redaction, and no subprocess mutation.
- Compatibility predicate: bounded internal review is required for new schema/symbol/reference names and imports from accepted modules. Check schema version rejection, exact enum behavior, accepted API reuse, and package link/naming tests.
- Reliability/recovery predicate: bounded internal review is required for evidence ordering, amendment-mode decisions, commit partition completeness, and recovery-domain separation. Check fail-closed behavior and no claim of multi-file atomicity or external recovery.
- No persistent-data migration, accessibility, deployment/infrastructure, concurrency/distributed-state, payment, performance, or live provider review is triggered because those surfaces are modeled but not touched. The recovery validator must still require explicit `not-touched` dispositions.

## Commit boundaries

No stage or commit is authorized. Keep these as logical, complete, non-overlapping review slices only:

1. `test: define execution discipline contracts` — `tests/test_execution_discipline.py` and neutral execution fixture.
2. `feat: validate execution evidence and ownership` — evidence, ownership, semantic-surface records/functions and focused tests.
3. `feat: enforce amendments and recovery boundaries` — mode-aware amendment, logical commit, recovery validation, and focused tests.
4. `feat: route execution discipline workflow` — reference, front door, package validator, and structural tests.
5. `docs: record execution discipline evidence` — direct traceability/governance evidence, reviews, packet, handoff, and final status.

Every actual INC-005 path must appear in exactly one boundary before review. Cross-boundary dependencies must be ordered, protected paths must appear in none, and a separate exact `create-local-commit` authorization is required before any future staging or commit command.

## Rollback and recovery

- **Source-code recovery:** Before any authorized commit, repair only exact INC-005 files from their observed pre-write bytes; never reset, clean, stash, restore, or overwrite accepted/user work. A future Git revert would require separate authority and could address only an exact authorized source commit.
- **Persistent-data recovery:** Not touched by INC-005. The validator must still require a `not-touched` disposition. A Git revert is never data recovery; any future migration needs independent backup, restore, verification, and authorization evidence.
- **Deployment rollback:** Not touched by INC-005. The validator must require a `not-touched` disposition. A source change or Git revert does not prove an artifact or environment rolled back.
- **Provider or external-state recovery:** Not touched by INC-005. The validator must require a `not-touched` disposition. Any future provider mutation requires exact authority and provider-specific reversal/reconciliation evidence.
- Governance files retain accepted per-file compare-and-swap and append-only behavior. If an append succeeds and a later status write fails, preserve the inert event, report partial progress, and retry only from freshly observed exact digests.
- Immutable sources, approved revisions, accepted packets/handoffs, approvals, and authorizations are never rolled back. Corrections use addenda, supersession/revocation records, or a new program revision as applicable.
- No module in this plan claims multi-file atomicity, hostile-concurrency locking, remote freshness, commit-hook behavior, deployment state, provider state, or complete recovery outside its named domain.

## Approval required to execute

The next legal approval must bind ISP-001 revision 2, SOURCE-002/program/semantic digests, accepted INC-004 evidence, `main`, selected base, current head, exact dirty inventory after these preparation writes, INC-005 brief digest, preparation digest, and this exact-file-plan digest.

Separate implementation authorization must permit only:

1. the named execution reference/module/test/neutral-fixture, front-door/package-validator, direct traceability evidence, and INC-005 review/handoff writes;
2. strict test-first slices plus explicit alternative verification for non-behavioral surfaces;
3. read-only Git observation, deterministic local verification, accepted atomic lifecycle/governance writes, and one fixture-bounded evidence-backed implementation amendment;
4. three separate non-independent review passes and evidence-backed remediation limited to material INC-005 findings;
5. logical commit-boundary validation with no staging or commit creation.

It must preserve prohibitions on evaluator/subagent dispatch, `create-local-commit`, INC-006, installation, marketplace change, push, pull request, publication, release, deployment, migration, destructive action, provider mutation, and consequential external state.
