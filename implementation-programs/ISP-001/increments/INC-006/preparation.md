# INC-006 Preparation

## Authority and boundary

- Program: ISP-001 revision 2.
- Source: SOURCE-002, SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program Markdown: SHA-256 `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Accepted traceability artifact: SHA-256 `22e2ebd3d4ca413a9f27d13b254453c39c79a0f51ed5e7a869c0de54fd614907`.
- Accepted atomic semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Latest accepted increment: INC-005, diff approval `APR-017`, bounded acceptance authorization `AUTH-015`.
- Approval mode: `approval:full-increment`.
- Current authorized work: revalidate persisted authority and repository truth; prepare the INC-006 brief, preparation evidence, contextual semantic naming inventory, and exact-file plan; extend current governance bindings from their accepted bytes; run read-only and deterministic local checks.
- Mandatory stop: explicit approval of the exact-file plan plus separate bounded implementation, verification, review, and remediation authorization.
- Excluded: INC-006 package implementation, reviewer/evaluator/subagent dispatch, staging, commit creation, INC-007, installation, marketplace change, push, pull request, publication, release, deployment, migration, destructive action, provider mutation, or other consequential external state.

The accepted front door, program authority, state/action authority, repository preparation, and execution-discipline procedures pass current validation. No accepted procedure mechanically owns cross-increment identity rollover or the INC-006 review/packet lifecycle yet, so this preparation records the rollover as the same disclosed manual safeguard used for INC-005. It does not claim that review coordination, reviewer independence, remediation sequencing, final-verification freshness, or packet validation is already implemented.

## Repository revalidation

- Repository and selected workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin`.
- Branch: `main`.
- Current and accepted INC-005 head: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
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
  - every file under `implementation-programs/ISP-001/increments/INC-003/`, `INC-004/`, and `INC-005/`
  - accepted repository-preparation, state-authorization, and execution-discipline reference/module paths
  - accepted repository-preparation, state-authorization, and execution-discipline fixture trees and focused tests
- These paths match the accepted, uncommitted INC-002 through INC-005 surface bound by the INC-005 packet, handoff, acceptance addendum, `APR-017`, `AUTH-015`, and persisted status. No contrary user-owned path was observed.
- INC-006 preparation may create only its brief, preparation, and exact-file plan, extend `manifest.json` and `status.json` from current accepted bytes, and append one preparation authorization. It must not rewrite, stage, commit, discard, or reconstruct any accepted path.

## Accepted authority revalidation

- SOURCE-001: `3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8` — match.
- SOURCE-002 and canonical repository source: `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57` — match.
- Revision-1 program: `ec94caa50ff8918e242170220816e92ea2c48b36cd6b2e19c531d37aea8d0324` — match.
- Revision-2 program: `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253` — match.
- Accepted INC-005 plan, packet, handoff, and acceptance addendum: `748c8622778e70cf3eab9b5aef035f16c382006cee6319614572c1cfbd70c9f9`, `b108dea813a2a3248dc55b67c00d0ef797c6ec3c73f3d5c42156145d76ec6e19`, `705777437ea20dafcf8ec1b1e693ac83f77ff85999ec6269811c6cb33ebd3404`, and `306a54672d9dd0cb60674c7f714c5efb45d87098b8b5bbf3f00ab26eac35cb95` — match.
- `APR-017` exactly binds the reviewed INC-005 diff; `AUTH-015` bounds only its acceptance-record writes. Neither grants INC-006 implementation, staging, commit, dispatch, or external-action authority.
- Persisted status sequence 44 records INC-005 `accepted`; current status SHA-256 is `06215086a45b4d90414ff7bed0e61ee8d7f0568332d2e93888efc170bf8345b4`. Manifest, workspace, brief, preparation, plan, review packet, handoff, addendum, approval, and authorization bindings agree.
- `state_authority.py validate-state` against the fresh exact dirty observation — PASS.
- `program_authority.py validate-program implementation-programs/ISP-001` — PASS.
- `repository_preparation.py validate-preparation` and `validate-plan` against the accepted INC-005 tuple — PASS.

## Drift classification at preparation

- Workspace identity, branch, selected base, head, accepted artifact digests, and dirty inventory agree with the persisted accepted state.
- There is no active operation, conflict, base movement, dependency/version change, protected-contract change, or newly overlapping user path.
- Classification: **benign**, with accepted-continuity context. The dirty tree is material and accepted; every existing byte remains protected.
- The proposed INC-006 implementation extends only accepted dirty front-door, package-validator, structural-test, traceability, manifest, status, approval, and authorization paths explicitly marked `extend`. It creates a focused review owner, neutral fixtures, and INC-006 governance evidence. It proposes no write to SOURCE-001, SOURCE-002, either program Markdown revision, accepted INC-001 through INC-005 evidence, or unrelated paths.
- Any new overlap, head movement, active Git operation, conflict, incompatible dependency change, protected-contract change, changed source/program binding, or altered accepted artifact byte before implementation invalidates this plan and requires renewed preparation.

## Fresh preparation checks

- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — PASS, 137 tests.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001` — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-preparation ...` — PASS against the accepted INC-005 binding.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-plan ...` — PASS against the accepted INC-005 binding.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans` — PASS.
- `rtk git diff --check` — PASS.

After this preparation tuple is persisted, `validate-preparation` and direct plan-content validation must pass. Full `validate-plan` is expected to withhold production-write authorization with exactly the current-plan authorization issue until the user approves the exact plan and a separate `modify-workspace` grant is recorded. That expected refusal is the gate, not a preparation failure.

These checks establish only the current deterministic baseline. They do not establish the not-yet-implemented review-scope selection, risk predicates, independent-review representation, raw-report ordering, material-finding completeness, remediation/re-review sequencing, final-verification freshness, or packet contract.

## Canonical source and traceability locations

The plan is grounded in these SOURCE-002 sections:

- review packet and authority terminology: sections 3.9-5, lines 85-157;
- review and packet component responsibilities: sections 7.10-7.11, lines 366-383;
- contextual semantic naming: section 9.3, lines 536-556;
- artifact invariants: section 10.1, lines 610-621;
- review, remediation, and final verification lifecycle: section 13.6, lines 786-798;
- evidence materiality, required scopes, specialist predicates, independence, and findings: sections 17-18, lines 904-974;
- canonical nineteen-field packet contract: section 19, lines 975-1002;
- validation strategy and review pressure cases: section 23, lines 1083-1197;
- INC-006 outcome and key evidence: section 24, lines 1232-1237;
- design acceptance, defaults, and reviewer/evidence/naming risks: sections 25-27, lines 1254-1349.

Revision-2 traceability allocates 348 atomic requirements to INC-006 across the seven named groups: REQ-AUTHORITY 123, REQ-ARTIFACT-INVARIANTS 14, REQ-DESIGN-RISKS 20, REQ-REVIEW-PACKET 62, REQ-SEMANTIC-NAMING 51, REQ-SEQUENCE 12, and REQ-VALIDATION 66. Many are cross-increment obligations. Implementation evidence must be added only to records directly demonstrated by INC-006, and the ordered semantic digest must remain unchanged.

## Current implementation and reusable patterns

- `repository_preparation.py` owns `SemanticNameRecord`, contextual naming validation, overlap/drift policy, exact-file-plan structure, and material evidence predicates. INC-006 should reuse those decisions instead of defining a word blacklist or a second repository-risk policy.
- `execution_discipline.py` owns immutable test-first/alternative evidence, execution ownership, semantic execution-surface coverage, amendment decisions, logical commit partitions, and four recovery domains. INC-006 should consume those records as review inputs instead of copying their validators.
- `state_authority.py` owns exact approval/action bindings and lifecycle persistence. The review module must validate caller-supplied sequence and digest evidence without writing status, approvals, or authorizations.
- `program_authority.py` owns accepted digests and managed-path loading. `validate_package.py` owns the required regular non-symlink package-asset tuple and package-facing naming/link scans.
- Existing tests use Python standard-library `unittest`, frozen dataclasses, tuples/frozensets, deterministic sorted issues, neutral JSON fixtures, import-by-path, and focused CLI exit contracts. The new boundary can follow that pattern without a dependency, provider, database, migration, deployment target, or external state.
- Review coordination is a distinct lifecycle responsibility. Extending preparation would mix pre-write plan safety with post-diff review evidence; extending execution discipline would mix implementation evidence with reviewer selection, remediation, final verification, and human packet construction.

## Current official evidence

Accessed 2026-08-09 local time against local Python 3.14.6:

- Python 3.14 `dataclasses`: `https://docs.python.org/3.14/library/dataclasses.html`. `frozen=True` emulates read-only instances but does not create truly immutable Python objects. INC-006 must convert nested JSON lists to tuples/frozensets and must not treat a frozen outer record as proof that nested mutable values cannot change.
- Python 3.14 `unittest`: `https://docs.python.org/3.14/library/unittest.html`. `subTest()` gives distinct evidence for table-driven predicate, classification, and missing-field cases while allowing the full matrix to run.
- Python 3.14 `types.MappingProxyType`: `https://docs.python.org/3.14/library/types.html#types.MappingProxyType`. A mapping proxy is a read-only dynamic view of its backing mapping. Any constant mapping used by INC-006 must have a private, never-mutated backing object; tuples and frozensets remain preferable for fixed policy sets.

No third-party API, dependency version, provider, authentication, public external behavior, deployment system, payment surface, persistence technology, or migration is touched. Current official evidence is sufficient for this low-risk standard-library planning surface. Static documentation does not prove reviewer independence, raw-report persistence, or runtime workflow compliance.

## Design options and decision

### Recommended: one focused review-coordination module and structured evidence record

Add `review_coordination.py` and `review-coordination.md`. Keep risk predicates, review reports, semantic naming dispositions, findings, remediation cycles, final command receipts, and packet data in versioned immutable records with pure deterministic validators. Add a read-only `validate-bundle` command that loads a structured review-evidence JSON artifact, validates it, renders the canonical human packet, and requires exact equality with the supplied Markdown packet. The module performs no repository, state, subprocess, network, provider, or external mutation.

The structured record is justified because ordering, exact digests, independence labels, finding dispositions, command results, and packet-field correspondence cannot be mechanically established from unconstrained prose. The Markdown packet remains the human review surface; the JSON record is evidence, not a parallel requirements or lifecycle source.

### Rejected: extend execution discipline

Execution discipline proves the implementation activity and recovery boundaries before review. Reviewer selection, raw-report sequencing, finding reconciliation, renewed review, final verification, and packet construction occur after the proposed diff is frozen. Combining them would blur distinct lifecycle stages and enlarge an already substantial accepted module.

### Rejected: separate risk, finding, remediation, verification, and packet modules

All five responsibilities share one immutable reviewed-diff and report/finding graph. Separate modules would duplicate schema validation, identifiers, digest binding, issue ordering, and fixture construction without independent consumers. A later demonstrated reuse or size pressure can justify a bounded split.

### Rejected: prose-only packet checks or automatic reviewer dispatch

Heading presence alone cannot prove exact commands/results, raw report digests, remediation ordering, or freshness. Conversely, dispatch text cannot manufacture independence. INC-006 will validate structured evidence and render the packet deterministically. The actual increment will use separate controller self-reviews labelled non-independent/reduced unless a later exact authorization permits one bounded independent final reviewer; the synthetic contract covers the independent and defect-follow-up cases without dispatching anyone during preparation.

## Repository-informed increment shape

INC-006 remains one coherent review unit. Its seven acceptance criteria share one invariant: a diff may reach human review only after required and risk-triggered reports are persisted truthfully, material findings are repaired or explicitly dispositioned, affected checks/reviews are rerun, fresh final verification binds the final diff, and a complete packet matches that evidence.

The internal implementation has five meaningful slices:

1. neutral review contracts and an observed missing-module RED;
2. required/risk-triggered scope selection, raw-report ordering, truthful independence, contextual naming, and finding completeness;
3. remediation/re-review cycles, final-verification freshness, packet-data validation, deterministic rendering, and read-only bundle validation;
4. focused operator procedure plus front-door/package integration with explicit alternative verification;
5. INC-006 self-application: separate raw reports, relevant specialist reports, any evidence-backed remediation, final verification, structured evidence, rendered packet, and direct traceability evidence.

No program amendment is required. The source's preferred independent review is capability- and authority-dependent. Truthful self-review with reduced assurance preserves the requirements when independent dispatch is unavailable or unauthorized; it does not weaken the at-most-one independent-final-reviewer rule or represent self-review as independent.

## Semantic naming inventory

Every proposed reusable/package/test surface describes a durable review responsibility. Repository governance paths may retain INC-006 and ISP-001 because their purpose is implementation planning, traceability, review, evidence, approval, and handoff.

| Proposed surface | Kind | Stable context | Intention | Origin | Planning-term basis | Basis owner | Compatibility class | Compatibility disposition |
|---|---|---|---|---|---|---|---|---|
| `review_coordination.py` | path | post-implementation review lifecycle | validate review, remediation, verification, and packet evidence | new | none | none | private | new internal module; no migration |
| `review-coordination.md` | path | operator procedure | route review safeguards without duplicating policy | new | none | none | package | new referenced asset; package tests lock presence |
| `implementation-review-evidence/v1` | schema-or-identifier | durable review evidence interchange | version reports, findings, remediation, and verification bindings | new | durable-domain | review evidence schema | persisted | versioned new schema; unsupported versions fail |
| `implementation-review-packet/v1` | schema-or-identifier | human packet data contract | version canonical packet fields and rendering | new | durable-domain | review packet schema | persisted | versioned new schema; unsupported versions fail |
| `ReviewRiskPredicate` | symbol | touched-risk classification | select only materially required specialist scopes | new | none | none | private | new internal API |
| `ReviewReport` | symbol | raw review evidence | bind scope, reviewer kind, assurance, diff, path, digest, and ordering | new | none | none | private | new internal API |
| `ReviewFinding` | symbol | review result | distinguish material, non-material, speculative, and invalid findings | new | none | none | private | new internal API |
| `SemanticNamingDisposition` | symbol | contextual naming review | bind a naming finding to surface, context, intention, and specific basis | new | durable-domain | semantic naming contract | private | composes accepted naming record; no migration |
| `RemediationCycle` | symbol | material-defect repair | bind findings to repair, changed paths, reruns, and renewed reports | new | none | none | private | new internal API |
| `CommandResult` | symbol | exact verification receipt | retain exact command, expected result, observed result, and exit status | new | none | none | private | new internal API |
| `FinalVerification` | symbol | final reviewed diff | prove verification is newer than repairs/reviews and binds the same diff | new | none | none | private | new internal API |
| `ReviewPacket` | symbol | human review handoff | represent all nineteen canonical packet fields | new | durable-domain | review packet contract | private | new internal API |
| `select_review_scopes` | symbol | review planning | require three base scopes plus touched-risk specialists | new | none | none | private | new internal API |
| `validate_review_reports` | symbol | raw report graph | enforce distinct scopes, persistence order, and truthful independence | new | none | none | private | new internal API |
| `validate_semantic_naming_review` | symbol | architecture naming review | require contextual surface and basis dispositions | new | none | none | private | reuses accepted semantic validator |
| `validate_findings` | symbol | finding contract | reject incomplete or unsupported material findings | new | none | none | private | new internal API |
| `validate_remediation_cycles` | symbol | repair lifecycle | require affected tests and reviews after material repairs | new | none | none | private | new internal API |
| `validate_final_verification` | symbol | final diff evidence | reject stale, partial, mismatched, or inexact command receipts | new | none | none | private | new internal API |
| `validate_review_packet` | symbol | packet data | reject missing canonical fields and unsupported claims | new | none | none | private | new internal API |
| `render_review_packet` | symbol | human packet projection | produce deterministic Markdown from validated packet data | new | none | none | private | new internal API |
| `validate_review_bundle` | symbol | integrated review evidence | compose the complete review-to-packet invariant without mutation | new | none | none | private | new internal API |
| `tests/fixtures/review-coordination/portable-archive-run/` | test-or-fixture | neutral archive-maintenance review scenario | exercise repair, re-review, verification, and packet equality | new | none | none | test | synthetic fixture; no migration |
| `test_semantic_finding_requires_context_intention_and_specific_basis` | test-or-fixture | contextual naming regression | pair an invalid roadmap-only candidate with valid governance/domain bases | new | none | none | test | project-neutral test title |
| INC-006 brief/preparation/plan/evidence/reviews/packet/handoff headings | heading | repository implementation governance | trace, verify, review, and hand off this increment | new | implementation-governance | ISP-001 manifest and approved program | repository-only | required governance coordinates, never package-facing |

Existing accepted `program_authority`, `state_authority`, `repository_preparation`, and `execution_discipline` names describe durable responsibilities and remain valid. No existing public, generated, externally consumed package-facing name requires migration.

## Material risks and controls

- **Fake independence:** a boolean supplied by the caller can overstate reviewer separation. Control: require reviewer kind, stable reviewer identity, capability/dispatch basis for independent claims, prior-conclusion withholding, bounded scope, assurance label, and explicit limitation that records cannot prove real identity separation. Self-review must use `non-independent-reduced`.
- **Review collapse:** one report can masquerade as requirements, architecture, and test evidence. Control: require all three scope identifiers, distinct raw paths/digests, scope-specific predicates, and persistence before reconciliation.
- **Specialist overreach or omission:** always-on specialist reviews create noise, while caller-selected scopes can hide touched risks. Control: require exactly one evidence-backed predicate for every canonical risk domain; a materially touched domain selects its named specialist, and an untouched domain records why.
- **Semantic word blacklist:** a token match can reject valid governance/domain vocabulary or permit a renamed leak. Control: reuse `SemanticNameRecord`, require affected surface/kind/context/intention and specific basis owner, and retain paired invalid/valid fixtures.
- **Material-finding dilution:** vague preferences can be marked material, or defects can omit impact/remediation. Control: material records require affected requirement/invariant, evidence/location, impact, qualitative severity/confidence, inspection path, smallest remediation, and final disposition. Speculation without evidence is not material.
- **Remediation laundering:** a finding can be marked repaired without a targeted regression or renewed review. Control: each repaired material finding appears in exactly one remediation cycle with changed paths, affected command results, renewed scope/report bindings, sequence evidence, and zero unresolved material findings before final verification.
- **Stale verification:** a successful suite run before the last repair can be reported as final. Control: bind every report, repair, and final verification to one diff digest and monotonic immutable sequence; final verification must be later than all repairs and renewed reports.
- **Command transcript masquerading as packet:** logs can be long but omit outcome, traceability, judgment, or recovery. Control: require all nineteen canonical packet fields and structured exact command/expected/observed/exit records; reject command-only or unsupported claims.
- **Packet/JSON drift:** machine evidence and human packet can disagree. Control: render canonical Markdown deterministically from validated packet data and require byte equality in the read-only CLI and actual INC-006 integration check.
- **Sensitive evidence capture:** raw output may include file contents, environment values, credentials, or private data. Control: store only bounded locators, digests, concise redacted results, and necessary commands; reject empty redaction/limitation fields and never read or persist unrelated contents.
- **Mutable nested evidence:** frozen dataclasses do not freeze contained lists/dicts. Control: normalize JSON sequences to tuples/frozensets and immutable value records before validation; never expose a mutable backing policy mapping.
- **Circular packet completion:** a packet cannot prove its own post-write digest while embedding that digest. Control: the structured record binds final diff, raw reports, findings, remediation, and verification; status binds the packet file digest only after rendering/validation. No packet field claims self-authentication.
- **Scope leakage:** continuity, prompt generation, resume, closure, and integrated pressure remain INC-007/INC-008/closure. Control: the new module validates review evidence only and must not generate the next brief, accept a diff, close a program, or authorize later actions.

## Planning conclusion

Repository truth supports the approved INC-006 outcome without changing program semantics. The selected design is standard-library, project-neutral, read-only, and composes accepted authority, preparation, execution, naming, and recovery owners. The exact-file plan can now be digest-bound and presented for human approval. No review module/reference/test/fixture implementation, reviewer dispatch, review evidence, status execution transition, staging, commit, or INC-007 work may begin before that approval and a separate exact non-commit implementation authorization.
