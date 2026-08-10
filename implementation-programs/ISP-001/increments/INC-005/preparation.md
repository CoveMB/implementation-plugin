# INC-005 Preparation

## Authority and boundary

- Program: ISP-001 revision 2.
- Source: SOURCE-002, SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program Markdown: SHA-256 `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Accepted traceability artifact: SHA-256 `07258dbd177bf08e7f1e7eb1d40cc769a9bdc115b38d05bc3d93e81de0e985a2`.
- Accepted atomic semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Latest accepted increment: INC-004, approval event `APR-015`, authorization `AUTH-012`.
- Approval mode: `approval:full-increment`.
- Current authorized work: revalidate persisted authority and repository truth; prepare the INC-005 brief, preparation record, semantic naming inventory, and exact-file plan; extend current governance bindings from their accepted bytes; run read-only and deterministic local checks.
- Mandatory stop: explicit approval of the exact-file plan plus separate bounded implementation/action authorization.
- Excluded: INC-005 package implementation, evaluator or subagent dispatch, staging, commit creation, INC-006, installation, marketplace change, push, pull request, publication, release, deployment, migration, destructive action, provider mutation, or other consequential external state.

The front door, program authority, state/action authority, and repository-preparation procedures are implemented and pass current validation. The accepted state module does not mechanically start a different increment identity, so the governance rollover to INC-005 remains a disclosed manual safeguard under renewed one-increment user authority. This preparation does not claim that INC-005 execution safeguards already exist.

## Repository revalidation

- Repository and selected workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin`.
- Branch: `main`.
- Current and accepted INC-004 head: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Selected continuation base: `f14449b8808574c720927aedab5b64871cc63858`; selected-base ancestry passed.
- Local Git: `2.50.1 (Apple Git-155)`; Python: `3.14.6`; platform: `Darwin 25.5.0 arm64`.
- This is the selected main checkout. No remote is configured, and no fetch was run because remote freshness cannot affect this local preparation gate.
- `repository_preparation.py inspect-repository` reported no staged or conflicted path, no detached head, and no merge, rebase, cherry-pick, revert, bisect, or sequencer operation.
- Pre-planning modified paths:
  - `implementation-programs/ISP-001/manifest.json`
  - `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
  - `implementation-programs/ISP-001/state/action-authorizations.jsonl`
  - `implementation-programs/ISP-001/state/approvals.jsonl`
  - `implementation-programs/ISP-001/state/status.json`
  - `skills/implementing-staged-plans/SKILL.md`
  - `skills/implementing-staged-plans/scripts/validate_package.py`
  - `tests/test_front_door_contract.py`
  - `tests/test_package_validation.py`
  - `tests/test_program_authority.py`
- Pre-planning untracked paths:
  - `implementation-programs/ISP-001/increments/INC-002/handoff-addendum.md`
  - every file under `implementation-programs/ISP-001/increments/INC-003/`
  - every file under `implementation-programs/ISP-001/increments/INC-004/`
  - `skills/implementing-staged-plans/references/repository-preparation.md`
  - `skills/implementing-staged-plans/references/state-authorization.md`
  - `skills/implementing-staged-plans/scripts/repository_preparation.py`
  - `skills/implementing-staged-plans/scripts/state_authority.py`
  - every file under `tests/fixtures/repository-preparation/`
  - every file under `tests/fixtures/state-authorization/`
  - `tests/test_repository_preparation.py`
  - `tests/test_state_authority.py`
- These paths match the accepted, uncommitted INC-002 through INC-004 surface bound by the INC-004 packet, handoff, acceptance addendum, `APR-015`, and persisted status. No contrary user-owned path was observed.
- INC-005 preparation may create only its brief, preparation, and exact-file plan, extend `manifest.json` and `status.json` from current accepted bytes, and append one preparation authorization. It must not rewrite, stage, commit, discard, or reconstruct any accepted path.

## Accepted authority revalidation

- SOURCE-001: `3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8` — match.
- SOURCE-002: `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57` — match.
- Revision-1 program: `ec94caa50ff8918e242170220816e92ea2c48b36cd6b2e19c531d37aea8d0324` — match.
- Revision-2 program: `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253` — match.
- Accepted INC-004 plan, packet, handoff, and acceptance addendum: `bf56b85605b928baf1340d19f3a229918524814628ab1eb0bba7bc07b34d434b`, `1ff5e7a0e83d00c599c9e8043c066c6defd7067a9207bf0c26db6feaee793f63`, `96c1b018be94050887c63ab45d2bfaddfa98d412ed0bad1974d83a5335c9cb26`, and `b2dca9d1d5162701673cd2cf3161f59a95ea2632d134c629830207087fa0c2de` — match.
- `APR-015` exactly binds the reviewed INC-004 diff; `AUTH-012` bounds only its acceptance-record writes.
- Persisted status sequence 35 records INC-004 `accepted`, and the manifest, workspace, brief, preparation, plan, packet, handoff, and addendum bindings agree.
- `program_authority.py validate-program implementation-programs/ISP-001` — PASS.
- `repository_preparation.py validate-preparation` and `validate-plan` against the accepted INC-004 tuple — PASS.

## Drift classification at preparation

- Workspace identity, branch, selected base, head, accepted artifact digests, and dirty inventory agree with the persisted accepted state.
- There is no active operation, conflict, base movement, dependency/version change, protected-contract change, or newly overlapping user path.
- Classification: **benign**, with accepted-continuity context. The dirty tree is material and accepted; every existing byte remains protected.
- The proposed INC-005 implementation extends the accepted dirty skill, package-validator, test, traceability, manifest, status, approval, and authorization surfaces only where the exact-file plan says `extend`. It proposes no write to SOURCE-001, SOURCE-002, prior program revisions, accepted INC-001 through INC-004 evidence, or unrelated paths.
- Any new overlap, head movement, active Git operation, conflict, incompatible dependency change, protected-contract change, changed source/program binding, or altered accepted artifact byte before implementation invalidates this plan and requires renewed preparation.

## Fresh preparation checks

- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — PASS, 104 tests.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001` — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-preparation ...` — PASS against the accepted INC-004 binding.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-plan ...` — PASS against the accepted INC-004 binding.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans` — PASS.
- `rtk git diff --check` — PASS.

After persisting the INC-005 preparation tuple, live `validate-preparation` passed and direct `validate_exact_file_plan` content validation passed. The complete `validate-plan` command returned exit `1` with exactly `no exact current write authorization matches the plan digest`. This is the intended gate: the plan is current and structurally valid, while production-write authority remains absent until explicit plan approval and a separate exact implementation grant.

These checks establish the accepted deterministic baseline only. They do not establish the not-yet-implemented execution-evidence, ownership, naming-enforcement, amendment-mode, focused-boundary, or recovery-domain behavior assigned to INC-005.

## Canonical source and traceability locations

The plan is grounded in these SOURCE-002 sections:

- execution controller and recovery classifier: sections 7.8-7.9, lines 336-364;
- bounded approach autonomy and semantic naming: sections 8.5 and 9.1-9.3, lines 458-556;
- state and action separation: sections 11-12 and 20, lines 637-734 and 1003-1023;
- implementation behavior: section 13.5, lines 772-781;
- amendment classification: section 14, lines 832-841;
- required review and packet evidence: sections 18-19, lines 919-999;
- repository fixtures and execution evidence: section 23, lines 1077-1182;
- INC-005 outcome and key evidence: section 24, lines 1224-1228;
- design acceptance, defaults, and risks: sections 25-27, lines 1254-1339.

Revision-2 traceability allocates 334 atomic requirements to INC-005 across the seven named groups: REQ-AUTHORITY 123, REQ-DEFAULTS 17, REQ-DESIGN-RISKS 20, REQ-EXECUTION-AMENDMENT 45, REQ-SEMANTIC-NAMING 51, REQ-SEQUENCE 12, and REQ-VALIDATION 66. Many are cross-increment obligations. Implementation evidence must be added only to records directly demonstrated by INC-005, and the ordered semantic digest must remain unchanged.

## Current implementation and reusable patterns

- `repository_preparation.py` already owns `AmendmentProposal`, `AmendmentAssessment`, `classify_plan_amendment`, `SemanticNameRecord`, `validate_semantic_naming_inventory`, `validate_plan_overlap`, and the current inspection contract. INC-005 should compose these accepted decisions instead of redefining amendment dimensions, planning-coordinate detection, or dirty-path ownership.
- `state_authority.py` already owns approval-mode policy, complete action bindings, `decide_action_authorization`, and the separate `create-local-commit` action name. INC-005 should consume these and must not imply commit authority from approval mode.
- `program_authority.py` provides accepted digests and managed-path loading. `validate_package.py` provides the established focused-asset tuple and package-facing naming scans.
- Existing tests use standard-library `unittest`, dataclasses, deterministic sorted issues, neutral JSON fixtures, import-by-path, and focused CLI exit contracts. No dependency, runtime, schema library, provider, persistence layer, deployment target, or external state is introduced.
- Extending `repository_preparation.py` would mix pre-authorization planning with authorized execution evidence. Extending `state_authority.py` would mix lifecycle persistence with test evidence, naming, commits, and recovery. One focused execution-discipline module preserves both accepted ownership boundaries.

## Current official evidence

Accessed 2026-08-09 local time:

- Git diff documentation: `https://git-scm.com/docs/git-diff`. Git distinguishes working-tree, index, and commit/tree comparisons and accepts pathspec-limited inspection. The implementation can therefore validate logical boundary coverage from explicit path inventories without staging or committing the selected workspace.
- Git commit documentation: `https://git-scm.com/docs/git-commit`. `--dry-run` reports paths that would be committed without creating a commit, and explicit pathspecs or NUL-delimited `--pathspec-from-file` can bound path selection. INC-005 will treat this only as optional non-mutating evidence; pure path coverage remains authoritative, and no actual `git commit` command is in scope.
- Python 3.14 `unittest` documentation: `https://docs.python.org/3/library/unittest.html`. `subTest()` identifies parameterized failures without stopping at the first table entry, matching the repository's existing qualitative matrix-test convention.

The local Git version is 2.50.1, and the current Git manual records no relevant manual change between 2.49.1 and 2.50.1. The new package boundary uses no Git subprocess for commit creation, no third-party dependency, and no external integration. Current official evidence is therefore sufficient for the touched local validation surface.

## Design options and decision

### Recommended: one focused execution-discipline module

Add `execution_discipline.py` and `execution-discipline.md`. Keep immutable evidence records and pure validators for test-first/alternative verification, ownership and semantic-surface coverage, mode-aware amendment decisions, logical commit boundaries, and four recovery domains in one cohesive execution trust boundary. Reuse accepted preparation/state types and decisions; the module never writes files, stages paths, or creates commits.

### Rejected: extend repository preparation

Preparation decides whether a plan is current and safe before production writes. Recording RED/GREEN ordering, actual changed paths, execution deviations, logical commit slices, and recovery after authorization is a distinct lifecycle responsibility. Combining them would blur planning truth with execution evidence and enlarge an already substantial accepted module.

### Rejected: an automatic Git staging/commit controller

The user expressly withholds commit authority, the selected workspace contains accepted dirty work, and `state_authority.py` already models `create-local-commit` separately. A staging controller would add mutation, index recovery, hooks, signing, and partial-file concerns unnecessary to prove focused boundaries. INC-005 will validate complete, non-overlapping logical commit slices and authority decisions without staging or committing.

### Rejected: separate modules for TDD, amendments, commits, and recovery

These responsibilities share one input: the authorized execution scope and its observed evidence. Four modules would duplicate binding and issue-ordering machinery without independent consumers. A later demonstrated size or reuse pressure can justify a bounded split.

## Repository-informed increment shape

INC-005 remains one coherent review unit. Its six acceptance criteria share one execution invariant: only evidence-backed, semantically named, ownership-safe, reversibly amended, reviewable work may advance from an authorized exact-file plan. Splitting naming, amendments, and recovery from execution evidence would allow one of those gates to be bypassed before INC-006 review-packet enforcement exists.

The internal implementation has five meaningful slices:

1. neutral execution contracts and an observed missing-module RED;
2. test-first and alternative-verification evidence plus ownership and semantic-surface enforcement;
3. mode-aware amendments, logical commit boundaries, separate commit authority, and recovery domains;
4. focused operator procedure and front-door/package integration with explicit alternative verification;
5. prepared-fixture execution, direct traceability evidence, review, remediation, and final verification.

No program amendment is required. The plan replaces the source plan's provisional automatic focused-commit behavior with a non-mutating logical-boundary validator because exact commit authority is withheld. This preserves the outcome, acceptance, action separation, risk posture, sequencing, review cadence, and later ability to create exact authorized commits.

## Semantic naming inventory

Every proposed package-facing surface communicates a stable execution responsibility. Repository governance paths may retain INC-005 because their purpose is implementation planning, traceability, review, and handoff.

| Proposed surface | Kind | Stable context | Intention | Origin | Planning-term basis | Basis owner | Compatibility class | Compatibility disposition |
|---|---|---|---|---|---|---|---|---|
| `execution_discipline.py` | path | authorized increment execution | validate execution evidence and boundaries | new | none | none | private | new internal module; no migration |
| `execution-discipline.md` | path | operator procedure | route execution safeguards without duplicating policy | new | none | none | package | new referenced asset; package tests lock presence |
| `implementation-execution-evidence/v1` | schema-or-identifier | durable evidence interchange | version execution evidence records | new | durable-domain | execution evidence schema | persisted | versioned new schema; unsupported versions fail |
| `TestFirstEvidence` | symbol | behavioral implementation evidence | prove intended RED precedes GREEN | new | none | none | private | new internal API; tests lock fields |
| `AlternativeVerificationContract` | symbol | non-behavioral change evidence | state why TDD is artificial and what proves the change | new | none | none | private | new internal API; tests lock fields |
| `OwnershipBoundary` | symbol | accepted and user-owned paths | prove preserve, extend, create, and managed-owner dispositions | new | none | none | private | new internal API; reuses accepted path rules |
| `ExecutionSurface` | symbol | created or renamed implementation surface | bind actual surfaces to semantic naming records | new | none | none | private | new internal API; reuses accepted naming records |
| `ExecutionAmendmentDecision` | symbol | approach changes during execution | apply classification and approval-mode consequences | new | none | none | private | new internal API; classification remains compatible |
| `CommitBoundary` | symbol | logical review/commit unit | assign every changed path once without committing | new | none | none | private | new internal API; no Git mutation |
| `RecoveryDomainPlan` | symbol | stateful recovery analysis | distinguish source, data, deployment, and provider recovery | new | durable-domain | recovery domain contract | private | new internal API; explicit domain enum |
| `validate_execution_evidence` | symbol | current authorized execution | validate evidence ordering and contracts | new | none | none | private | new internal API |
| `validate_execution_ownership` | symbol | current changed path set | reject unrelated cleanup and protected-byte drift | new | none | none | private | new internal API |
| `validate_execution_surfaces` | symbol | created and renamed surfaces | require complete contextual naming coverage | new | none | none | private | new internal API |
| `decide_execution_amendment` | symbol | plan deviation policy | combine accepted classification with mode and plan gate | new | none | none | private | new internal API |
| `validate_commit_boundaries` | symbol | logical commit plan | enforce complete, non-overlapping, ordered path slices | new | none | none | private | new internal API |
| `validate_recovery_domains` | symbol | recovery analysis | prevent Git revert from standing in for external recovery | new | none | none | private | new internal API |
| `tests/fixtures/execution-discipline/portable-archive-run/scenarios.json` | test-or-fixture | neutral prepared repository scenario | exercise bounded amendment and execution evidence | new | none | none | test | synthetic fixture; no migration |
| `test_roadmap_coordinate_is_rejected_but_governance_and_domain_names_pass` | test-or-fixture | semantic enforcement regression | pair invalid and valid naming contexts | new | none | none | test | project-neutral test title |
| INC-005 brief/preparation/plan/reviews/packet/handoff headings | heading | repository implementation governance | trace and review this approved increment | new | implementation-governance | ISP-001 manifest and approved program | repository-only | required governance coordinates, never package-facing |

No existing public, generated, persisted package-facing, or external implementation name in the touched package requires migration. The existing `program_authority`, `state_authority`, and `repository_preparation` names describe durable implemented responsibilities and remain valid.

## Material risks and controls

- **False TDD claims:** a nonzero command can fail for setup or syntax rather than the intended missing behavior. Control: require exact command, observed exit, expected and observed reason, tree timing, and an explicit intended-reason match before accepting RED evidence.
- **Artificial tests for declarative work:** forcing a behavior test can hide what a package/document change actually proves. Control: require change kind, why test-first is not meaningful, exact verification command, expected and observed evidence, and residual limitation.
- **Protected-byte drift:** path-only checks can miss edits to already-dirty user or accepted files. Control: require baseline/current SHA-256 or explicit non-regular-path fingerprint for preserve dispositions; only named `extend` paths may change.
- **Naming coverage gaps:** validating only a supplied inventory lets a created surface be omitted. Control: compare the exact created/renamed surface set with one-to-one `SemanticNameRecord` coverage before invoking the accepted contextual validator.
- **Amendment laundering:** a caller can label a program change as bounded. Control: accepted program-dimension precedence remains controlling; the new decision adds mode/plan-gate consequences but cannot downgrade the classification.
- **Commit leakage:** a logical boundary helper could become an implicit commit command. Control: the module performs no staging/commit mutation, requires complete path partitioning, and reports separate `create-local-commit` authority as absent unless an exact grant exists.
- **Mechanical coherence claims:** unique path assignment cannot prove that a commit has one semantic purpose. Control: require purpose, message, dependency order, and a focused human architecture review; do not use numeric size limits.
- **Recovery collapse:** a Git revert cannot undo data migrations, deployments, or provider effects. Control: require all four domains, touched-domain-specific mechanism/evidence/authority, and forbid `git-revert` outside source-code recovery.
- **Scope leakage:** review-packet validation, prompt/continuity, closure, and integrated pressure remain INC-006 through INC-008. Control: this module validates execution evidence only and the current workflow continues to use manual review artifacts until later safeguards exist.

## Planning conclusion

Repository truth supports the approved INC-005 outcome without changing program semantics. The selected design is standard-library, project-neutral, non-mutating, and composes accepted preparation and action-authority boundaries. The exact-file plan is ready for digest binding and human approval; no package/test/fixture implementation, staging, commit, or INC-006 work may begin before that approval and a separate non-commit implementation authorization.
