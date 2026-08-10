# INC-004 Review Packet

## Decision requested

Review and approve or request changes to the bounded INC-004 diff. Approval would accept this increment only. It would not authorize a commit, begin INC-005, close the program, or authorize any external action.

## Outcome

INC-004 adds a project-neutral, read-only repository-preparation boundary. It observes Git truth, preserves and classifies dirty work, distinguishes qualitative drift, decides evidence applicability, assesses increment shape and amendment scope, inventories semantic names in context, and validates manifest-owned exact-file plans plus their separate full-tuple write authority.

## Authority and immutable bindings

- Program: ISP-001 revision 2; approval mode `approval:full-increment`.
- Source: SOURCE-002 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`; SOURCE-001 remains `3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8`.
- Program Markdown: revision 1 `ec94caa50ff8918e242170220816e92ea2c48b36cd6b2e19c531d37aea8d0324`; revision 2 `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Approved semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`, unchanged after evidence-only traceability edits.
- Plan approval/action authority: `APR-014` / `AUTH-011`; plan `bf56b85605b928baf1340d19f3a229918524814628ab1eb0bba7bc07b34d434b`.
- Workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin`; `main`; base `f14449b8808574c720927aedab5b64871cc63858`; head `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- No commit, stage, stash, reset, clean, restore, fetch, push, PR, publication, deployment, installation, provider mutation, or other consequential action occurred.

## Files and interfaces

### New reusable/package-facing assets

- `skills/implementing-staged-plans/scripts/repository_preparation.py`
  - `RepositoryInspection` and `inspect_repository`
  - `DriftContext`, `DriftAssessment`, `classify_repository_drift`, and `validate_plan_overlap`
  - `EvidenceRecord`, `EvidenceContext`, `EvidenceDecision`, `decide_evidence_refresh`, and `validate_evidence_record`
  - `AmendmentProposal`, `AmendmentAssessment`, and `classify_plan_amendment`
  - `IncrementShape` and `assess_increment_shape`
  - `SemanticNameRecord` and `validate_semantic_naming_inventory`
  - `PlanBinding`, `validate_exact_file_plan`, `validate_preparation`, and three read-only CLI routes
- `skills/implementing-staged-plans/references/repository-preparation.md`
- `tests/test_repository_preparation.py`
- `tests/fixtures/repository-preparation/portable-archive-workspace/{scenarios.json,evidence.json,exact-file-plan.md}`

### Extended accepted package surfaces

- `skills/implementing-staged-plans/SKILL.md` — one focused route only.
- `skills/implementing-staged-plans/scripts/validate_package.py` — regular non-symlink requirements for the new assets.
- `tests/test_package_validation.py` and `tests/test_front_door_contract.py` — structural contracts.

### Governance/evidence surfaces

- INC-004 brief, preparation, approved exact-file plan, execution record, three raw reviews, this packet, and durable handoff.
- Revision-2 traceability adds direct evidence to eight atomic requirements while leaving their distributed disposition and all semantic fields unchanged.
- Manifest, approval log, action-authorization log, and status record only carry current INC-004 bindings and lifecycle evidence.

## Acceptance mapping

1. Dirty/untracked state, operations, base movement, baseline failures, managed ownership, reuse, dependency drift, and invalidated assumptions: neutral scenario catalog plus real-Git/parser/drift tests.
2. Evidence materiality and risk: every material predicate, official availability, high-risk unavailability, lower-risk exact reuse, mismatch, access failure, and irrelevant installed surface are tested.
3. Benign, reconcilable-relevant, and base-invalidating drift: immutable categories with deterministic invalidating precedence and separate required actions.
4. Current exact plan before production changes: missing, symlinked, stale, structurally incomplete, tuple-mismatched, digest-mutated, unbound-preparation, and non-exact-action cases reject.
5. Amendment boundary: every program dimension and authoritative contradiction dominates labels; bounded changes require evidence, preserved obligations, no unresolved user choice, and recovery.
6. Semantic naming: every required surface kind requires context/intention; coordinate candidates receive contextual governance/domain treatment; compatibility-sensitive existing names require explicit disposition.

The implementation directly advances `REQ-AUTHORITY`, `REQ-DEFAULTS`, `REQ-DESIGN-RISKS`, `REQ-EVIDENCE-PLANNING`, `REQ-SEMANTIC-NAMING`, `REQ-SEQUENCE`, `REQ-VALIDATION`, and `REQ-WORKSPACE-DRIFT`. Cross-increment atomic requirements remain `allocated`.

## Key decisions

- Git is the read-only adapter; classification and validation remain pure data decisions.
- Porcelain v2 `-z` is parsed as bytes. Rename pairs and unusual filesystem paths remain indivisible; escaping and unsupported mandatory records reject.
- Qualitative precedence replaces arbitrary drift or reviewability scores.
- Evidence is refreshed only for materially touched surfaces; high-risk unavailable evidence blocks.
- Program-amendment dimensions dominate all proposed implementation labels.
- Naming detection is contextual, not a global banned-word list.
- Plan validation never creates authority: the manifest-owned plan, manifest-owned preparation, persisted status, and one full-tuple `modify-workspace` grant must all agree.

## RED, GREEN, review, and remediation evidence

- Initial RED: missing `repository_preparation.py` caused the focused test import to fail.
- Initial GREEN: 29 preparation tests passed.
- Structural RED: five assertions exposed missing required assets and front-door route.
- Structural GREEN: 22 package/front-door tests passed; package validation passed.
- Raw self-reviews: requirements, architecture, and test/evidence passes were persisted separately and labelled non-independent/reduced assurance.
- Review RED: 32 tests produced one failure and one error, proving incomplete action tuple validation and missing preparation-identity validation.
- Remediation GREEN: 32 focused tests passed; both live CLI validators passed.
- Material findings after remediation: zero observed.

## Fresh final verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — 104 tests passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` — passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001` — passed.
- Live `repository_preparation.py validate-preparation ...` — passed.
- Live `repository_preparation.py validate-plan ...` — passed.
- Skill quick validation — passed.
- `git diff --check` — passed.
- A temporary one-character plan mutation returned exit 1 for both plan-digest and exact-action mismatches.

## Workspace preservation and bounded diff

Pre-existing accepted/user-owned paths remain present and are not silently incorporated: `tests/test_program_authority.py`, the state-authority reference/script/fixtures/tests, INC-002 addendum, all INC-003 artifacts, and all earlier accepted files. The current branch/head did not move, no path is staged or conflicted, and no Git operation is active.

INC-004 changes are limited to the approved planning/evidence artifacts; preparation reference/module/tests/fixtures; front-door/package validator and their structural tests; direct traceability evidence; and bound manifest/status/append-only approval and authorization records.

## Risks and limits

- Review assurance is reduced because all three passes are controller self-reviews, not independent evaluations.
- The parser intentionally fails on unknown mandatory future porcelain record kinds.
- Per-file state writes do not claim hostile-concurrency locking or multi-file atomicity.
- Local/static evidence does not prove remote freshness, live integration, deployment, publication, production safety, accessibility, translation quality, or external provider behavior.

## Rollback and recovery

Before a future commit, modify only named INC-004 paths from recorded prior bytes. Never reset, clean, stash, restore, or overwrite accepted/user work. Immutable sources, approved program revisions, accepted evidence, approvals, and authorizations remain preserved; corrections use the applicable addendum, supersession, or later revision mechanism.

## Next legal action

After the packet is digest-bound through verification, transition only to `awaiting-diff-approval` and ask the user to approve or request changes to this INC-004 diff. Do not accept it automatically, commit it, or begin INC-005.
