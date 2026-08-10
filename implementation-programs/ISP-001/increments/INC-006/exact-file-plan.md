# Review Coordination, Remediation, Verification, and Packet Implementation Plan

**Goal:** Implement a project-neutral review boundary that keeps required and risk-triggered scopes distinct, represents reviewer independence truthfully, validates contextual semantic naming and evidence-complete findings, enforces remediation/re-review and fresh-verification ordering, and produces a complete human packet from matching structured evidence.

**Architecture:** Add one standard-library `review_coordination.py` module with frozen normalized records, pure deterministic validators, a deterministic packet renderer, and a read-only `validate-bundle` command. Compose accepted naming, execution-evidence, recovery, and lifecycle bindings without copying their policy owners. Add one focused operator reference, one neutral bundle/packet fixture pair, and one structured INC-006 evidence record whose validated packet projection is the human Markdown review surface.

**Tech stack:** Python 3.14 standard library, `unittest`, JSON review evidence, Markdown packet rendering, existing program/state/preparation/execution/package validators, and read-only Git inspection.

## Global constraints

- Program ID: `ISP-001`; program revision: `2`; increment ID: `INC-006`.
- Source digest: `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program digest: `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Accepted traceability digest: `22e2ebd3d4ca413a9f27d13b254453c39c79a0f51ed5e7a869c0de54fd614907`.
- Semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`; implementation and verification evidence may change, but ordered semantic fields and this digest must not.
- Preparation evidence digest: `e878882a1d5a3ebfe560572f2c1e196ba1aea678d24ae578bdef1c3877d61c3c`.
- Workspace path: `/Users/CoveMB/Code/CoveMB/implementation-plugin`; workspace branch: `main`; workspace base: `f14449b8808574c720927aedab5b64871cc63858`; workspace head: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Approval mode is `approval:full-increment`, but the user-imposed exact-plan approval gate remains controlling.
- Preserve SOURCE-001, SOURCE-002, both program revisions, accepted INC-001 through INC-005 evidence, accepted dirty work, and all unrelated or user-owned work byte-for-byte.
- Keep reusable, package-facing, test, fixture, schema, command, error, heading, and generated names project-neutral. Governance artifacts may retain required ISP/INC/SOURCE/requirement/approval/authorization coordinates.
- Use standard-library Python and existing repository mechanisms; add no dependency, runtime, provider, network integration, schema framework, application component, hook, marketplace entry, publisher surface, or CI workflow.
- Use strict RED-GREEN-REFACTOR for behavioral changes. Non-behavioral reference, route, package-asset, review-report, evidence, packet, and governance work must have complete alternative verification.
- Actual INC-006 reports are separate controller self-reviews and must be labelled non-independent with reduced assurance. No reviewer/evaluator/subagent dispatch is authorized by this plan. Synthetic tests cover one bounded independent final reviewer and material-defect follow-up without claiming actual independence.
- Do not stage or create a commit. Logical commit boundaries are review artifacts only unless a later exact `create-local-commit` grant names the boundary and paths.
- Stop at INC-006 `awaiting-diff-approval`; do not begin INC-007, accept the diff, close the program, or perform any consequential external action.

## Requirements and acceptance binding

This plan advances `REQ-AUTHORITY`, `REQ-REVIEW-PACKET`, `REQ-ARTIFACT-INVARIANTS`, `REQ-VALIDATION`, `REQ-SEQUENCE`, `REQ-SEMANTIC-NAMING`, and `REQ-DESIGN-RISKS`. Direct implementation evidence is added only to atomic records demonstrated by INC-006.

Acceptance is exact:

1. requirements, architecture, and test-evidence reviews remain distinct;
2. at most one bounded independent final reviewer is used for a coherent increment unless a material defect requires follow-up;
3. raw reports are persisted before reconciliation;
4. self-review is labelled non-independent with reduced assurance;
5. semantic naming findings identify the affected implementation surface, context, intention, and any permitted governance or durable-domain basis;
6. material findings include evidence, impact, confidence, remediation, and disposition;
7. packets satisfy all canonical fields with exact commands and exact results.

Integration checkpoint: INC-006 itself must use the implemented structured bundle, report/remediation/final-verification validators, deterministic renderer, and packet equality check before it can reach `awaiting-diff-approval`.

## File map

### Create during implementation

- `skills/implementing-staged-plans/scripts/review_coordination.py` — immutable review evidence types, pure validators, deterministic packet renderer, and read-only bundle CLI.
- `skills/implementing-staged-plans/references/review-coordination.md` — focused operator procedure and front-door target.
- `tests/test_review_coordination.py` — focused behavioral, matrix, integration, renderer, and CLI contract tests.
- `tests/fixtures/review-coordination/portable-archive-run/review-evidence.json` — neutral required/specialist review, material-repair, verification, and packet-data scenario.
- `tests/fixtures/review-coordination/portable-archive-run/review-packet.md` — exact deterministic human packet projection for the neutral scenario.
- `implementation-programs/ISP-001/increments/INC-006/execution-record.md` — observed RED/GREEN/alternative evidence, lifecycle receipts, review sequence, remediation, and final verification.
- `implementation-programs/ISP-001/increments/INC-006/review-evidence.json` — actual structured risk, report, finding, remediation, verification, recovery, and packet data.
- `implementation-programs/ISP-001/increments/INC-006/reviews/requirements.md` — raw non-independent requirements and accepted-scope review.
- `implementation-programs/ISP-001/increments/INC-006/reviews/architecture.md` — raw non-independent architecture, boundary, naming, and simplicity review.
- `implementation-programs/ISP-001/increments/INC-006/reviews/test-evidence.md` — raw non-independent test adequacy and evidence-validity review.
- `implementation-programs/ISP-001/increments/INC-006/reviews/specialist-security-privacy.md` — raw non-independent evidence-handling and secret-minimization review selected by the actual risk predicates.
- `implementation-programs/ISP-001/increments/INC-006/reviews/specialist-compatibility.md` — raw non-independent schema/package compatibility review selected by the actual risk predicates.
- `implementation-programs/ISP-001/increments/INC-006/reviews/specialist-reliability.md` — raw non-independent ordering, freshness, fail-closed, and recovery-limits review selected by the actual risk predicates.
- `implementation-programs/ISP-001/increments/INC-006/reviews/remediation.md` — reconciliation and any material-finding repair/re-review cycles; records an explicit not-triggered disposition when none exist.
- `implementation-programs/ISP-001/increments/INC-006/review-packet.md` — deterministic human review packet rendered from validated packet data.
- `implementation-programs/ISP-001/increments/INC-006/handoff.md` — durable awaiting-diff-approval handoff.

### Modify during implementation

- `skills/implementing-staged-plans/SKILL.md` — add one review-coordination route; preserve existing front-door gates and prior routes.
- `skills/implementing-staged-plans/scripts/validate_package.py` — require the new reference/module assets through the existing asset tuple.
- `tests/test_package_validation.py` — prove required regular-file and symlink behavior for the new assets.
- `tests/test_front_door_contract.py` — prove the concise review route and retained authority boundaries.
- `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json` — add only directly demonstrated INC-006 evidence; preserve semantic fields/digest.
- `implementation-programs/ISP-001/manifest.json` — keep current INC-006 artifact roles and lifecycle binding current.
- `implementation-programs/ISP-001/state/status.json` — accepted lifecycle transitions and final awaiting-diff-approval evidence.
- `implementation-programs/ISP-001/state/approvals.jsonl` — append only the later exact plan approval and any later diff decision; never rewrite accepted events.
- `implementation-programs/ISP-001/state/action-authorizations.jsonl` — append only later exact non-commit implementation and lifecycle grants; never rewrite accepted grants.
- `implementation-programs/ISP-001/increments/INC-006/exact-file-plan.md` — amend only under the accepted amendment policy, preserving prior digest/addendum evidence.

### Already created at this preparation gate

- `implementation-programs/ISP-001/increments/INC-006/brief.md` — lean current brief.
- `implementation-programs/ISP-001/increments/INC-006/preparation.md` — repository evidence, design decision, semantic naming inventory, and risks.
- `implementation-programs/ISP-001/increments/INC-006/exact-file-plan.md` — this approval-bound implementation contract.

### Preserve without modification

- `implementation-programs/ISP-001/source/implementation-plan.md`
- `implementation-programs/ISP-001/source/revisions/SOURCE-002/implementation-plan.md`
- `implementation-programs/ISP-001/program/implementation-program.md`
- `implementation-programs/ISP-001/program/revisions/revision-2/implementation-program.md`
- `implementation-programs/ISP-001/increments/INC-001/`
- `implementation-programs/ISP-001/increments/INC-002/`
- `implementation-programs/ISP-001/increments/INC-003/`
- `implementation-programs/ISP-001/increments/INC-004/`
- `implementation-programs/ISP-001/increments/INC-005/`
- every path outside the exact create/modify map, including all unrelated user-owned work.

### Interfaces and ownership

- Consume `repository_preparation.SemanticNameRecord` and `validate_semantic_naming_inventory`; do not copy coordinate detection, basis, or compatibility policy.
- Consume `execution_discipline.TestFirstEvidence`, `AlternativeVerificationContract`, `RecoveryDomainPlan`, `validate_execution_evidence`, and `validate_recovery_domains` where the packet relies on those accepted contracts; do not redefine TDD or recovery truth.
- Consume caller-supplied source/program/semantic/brief/plan/workspace/state/diff bindings. Lifecycle mutation remains owned by accepted state-authority compare-and-swap and append-only mechanisms.
- Produce `ReviewRiskPredicate`, `ReviewReport`, `ReviewFinding`, `SemanticNamingDisposition`, `RemediationCycle`, `CommandResult`, `FinalVerification`, `ReviewPacket`, `select_review_scopes`, `validate_review_reports`, `validate_semantic_naming_review`, `validate_findings`, `validate_remediation_cycles`, `validate_final_verification`, `validate_review_packet`, `render_review_packet`, and `validate_review_bundle`.
- Define `implementation-review-evidence/v1` and `implementation-review-packet/v1`. Reject unknown schemas, unknown fields where exact records are required, mutable nested sequences, duplicate identifiers, and booleans supplied as integer sequence/exit values.
- `review_coordination.py` may read only explicit bundle/packet paths for its CLI. It must reject symlinked or non-regular inputs, perform no subprocess/Git/state/network/provider action, print no file contents or environment values, and return deterministic status `0` valid, `1` invariant failure, `2` usage error.
- `review-evidence.json` records review facts and packet data but does not control requirements, approval, authorization, or lifecycle state. `review-packet.md` is rendered from its validated packet data; status binds the final packet digest after rendering.

## Semantic naming inventory

| Surface | Kind | Context | Intention | Origin | Planning-term basis | Basis owner | Compatibility class | Compatibility disposition |
|---|---|---|---|---|---|---|---|---|
| `review_coordination.py` | path | post-implementation review lifecycle | validate review, remediation, verification, and packet evidence | new | none | none | private | new internal module; no migration |
| `review-coordination.md` | path | operator procedure | route review safeguards | new | none | none | package | new required asset; package tests lock it |
| `implementation-review-evidence/v1` | schema-or-identifier | durable review evidence | reject incompatible review bundles | new | durable-domain | review evidence schema | persisted | versioned schema; unsupported versions fail |
| `implementation-review-packet/v1` | schema-or-identifier | human packet data | reject incompatible packet records and rendering | new | durable-domain | review packet schema | persisted | versioned schema; unsupported versions fail |
| `ReviewRiskPredicate` | symbol | touched-risk classification | select only required specialist scopes | new | none | none | private | new internal API |
| `ReviewReport` | symbol | raw review evidence | bind scope, reviewer, assurance, diff, digest, and order | new | none | none | private | new internal API |
| `ReviewFinding` | symbol | review result | validate classification, evidence, impact, remediation, and disposition | new | none | none | private | new internal API |
| `SemanticNamingDisposition` | symbol | contextual naming review | bind finding to surface, intention, and specific basis | new | durable-domain | semantic naming contract | private | composes accepted naming record |
| `RemediationCycle` | symbol | material-defect repair | bind repair, changed paths, checks, and renewed reports | new | none | none | private | new internal API |
| `CommandResult` | symbol | exact verification receipt | bind command, expected/observed result, exit, and inputs | new | none | none | private | new internal API |
| `FinalVerification` | symbol | final reviewed diff | prove freshness and exact diff binding | new | none | none | private | new internal API |
| `ReviewPacket` | symbol | human review handoff | hold all nineteen canonical fields | new | durable-domain | review packet contract | private | new internal API |
| `select_review_scopes` | symbol | review planning | combine three base scopes with touched-risk specialists | new | none | none | private | new internal API |
| `validate_review_reports` | symbol | raw report graph | enforce scope separation, ordering, and truthful independence | new | none | none | private | new internal API |
| `validate_semantic_naming_review` | symbol | architecture naming review | enforce contextual surface and basis records | new | none | none | private | delegates accepted naming policy |
| `validate_findings` | symbol | finding contract | reject incomplete or speculative material findings | new | none | none | private | new internal API |
| `validate_remediation_cycles` | symbol | repair lifecycle | require targeted reruns and renewed affected reviews | new | none | none | private | new internal API |
| `validate_final_verification` | symbol | final diff evidence | reject stale, mismatched, or inexact receipts | new | none | none | private | new internal API |
| `validate_review_packet` | symbol | packet data | reject missing canonical fields and unsupported claims | new | none | none | private | new internal API |
| `render_review_packet` | symbol | human packet projection | render deterministic Markdown after validation | new | none | none | private | new internal API |
| `validate_review_bundle` | symbol | integrated review evidence | compose risk, reports, findings, repair, verification, recovery, and packet | new | none | none | private | new internal API |
| `validate-bundle` | command | operator validation | compare structured evidence with an exact rendered packet | new | none | none | package | read-only command; stable exit contract |
| `portable-archive-run` | test-or-fixture | neutral archive-maintenance scenario | exercise review-to-packet integration | new | none | none | test | synthetic fixture; no migration |
| `test_semantic_finding_requires_context_intention_and_specific_basis` | test-or-fixture | semantic review regression | pair invalid and valid naming contexts | new | none | none | test | project-neutral test title |
| INC-006 governance artifacts | heading | implementation governance | bind planning, evidence, review, packet, and handoff | new | implementation-governance | ISP-001 manifest | repository-only | required governance identifiers |

## Test-first slices and verification contracts

### Task 0: Bind plan approval and non-commit implementation authority

**Files:**

- Modify: `implementation-programs/ISP-001/state/approvals.jsonl`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl`
- Modify: `implementation-programs/ISP-001/state/status.json`

**Produces:** One exact plan approval and one separate non-commit implementation/review grant before package/test/fixture/review writes. Commit and dispatch authority remain absent.

- [ ] Revalidate SOURCE-001/SOURCE-002, both program revisions, semantic digest, INC-005 accepted bindings, branch/base/head, active operation, full dirty inventory, brief digest, preparation digest, and this plan digest.
- [ ] Append one `implementation-approval/v1` `exact-file-plan-approval` event binding INC-006, the current tuple, and the user gate.
- [ ] Append one `implementation-action-authorization/v1` grant limited to the exact create/modify map, strict test-first/alternative evidence, deterministic local verification, separate non-independent required/specialist reports, and evidence-backed material remediation. Exclude staging, `create-local-commit`, reviewer/evaluator/subagent dispatch, and all external/consequential actions.
- [ ] Advance INC-006 only from `awaiting-plan-approval` to `authorized` through accepted state authority. Do not mark `implementing` before Task 1 RED is observed.

### Task 1: Define review contracts and observe RED

**Files:**

- Create: `tests/test_review_coordination.py`
- Create: `tests/fixtures/review-coordination/portable-archive-run/review-evidence.json`
- Create: `tests/fixtures/review-coordination/portable-archive-run/review-packet.md`

**Interfaces:**

- Consumes: accepted semantic naming, execution evidence, recovery, and neutral fixture conventions.
- Produces: executable contracts for every public record/function/CLI listed under Interfaces and ownership.

- [ ] Add immutable schema/field tests for risk predicates, reports, findings, semantic dispositions, remediation cycles, command results, final verification, packet data, and integrated bundle loading. Require normalized tuples/frozensets and reject booleans as integers.
- [ ] Add risk tests requiring exactly one predicate per canonical source domain: security/privacy; persistent data/migrations; accessibility; platform/deployment/infrastructure; concurrency/reliability/distributed state; public API/compatibility; payments/financial; performance; provider/external state. Touched domains require evidence and a specialist scope; untouched domains require explicit rationale and must not create a specialist report.
- [ ] Add report tests requiring distinct requirements, architecture, and test-evidence raw paths/digests/scopes; selected specialist reports; reviewed-diff equality; persistence sequence before reconciliation; scope-specific predicates; and no duplicate identity.
- [ ] Add independence tests: self-review requires `non-independent-reduced`, no false dispatch basis, and separate reports. Independent claims require a bounded scope, concrete capability/dispatch basis, prior conclusions withheld, and `independent-bounded`. Reject more than one independent final reviewer unless every extra pass is an exact follow-up to a material finding.
- [ ] Add semantic review tests across accepted surface kinds. Each naming finding must bind the surface, kind, context, intention, origin, compatibility, and specific implementation-governance or durable-domain basis where used; reject generic allowlists and roadmap-only meaning.
- [ ] Add finding tests for material/non-material/speculative/invalid classification. Material findings require affected requirement/invariant, evidence/location, impact, severity, confidence, reproduction/inspection path, smallest remediation, disposition, and any decision reference for accepted/deferred risk.
- [ ] Add remediation tests requiring each repaired material finding in exactly one cycle, repair sequence after its raw report, changed paths, targeted command results, affected-scope renewed reports, renewed-report sequence after repair, and no unresolved material finding before final verification.
- [ ] Add final-verification tests requiring exact command/expected/observed/exit/input records, final-diff equality, execution after every repair and renewed report, full required-command coverage, and zero successful-but-stale receipts.
- [ ] Add packet tests for all nineteen source fields, exact command-result equality with final verification, raw report/finding/repair bindings, baseline-versus-introduced failures, traceability, implications, recovery, workspace/commit boundary, state/next action, and rejection of command-only or unsupported completion claims.
- [ ] Add renderer/CLI tests requiring deterministic Markdown equality, regular non-symlink inputs, zero/one/two exits, concise issues, and no mutation or file-content echo.
- [ ] Add the neutral scenario with three required self-reviews, only evidence-triggered specialists, one material semantic defect, a targeted repair and renewed review, fresh final verification, zero unresolved material findings, four recovery dispositions, and exact packet equality. Add separate synthetic cases for one independent final reviewer and an evidence-bound follow-up exception.
- [ ] Run `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination -v`. Expected RED: import fails because `skills/implementing-staged-plans/scripts/review_coordination.py` does not exist. Persist the exact failure and tree state before production code.

### Task 2: Implement review scope, report, naming, and finding validation

**Files:**

- Create: `skills/implementing-staged-plans/scripts/review_coordination.py`
- Modify: `tests/test_review_coordination.py` only when the harness, not an accepted contract, is wrong.

**Produces:** Versioned immutable records plus pure review-selection, raw-report, independence, semantic naming, and finding validators.

- [ ] Define exact frozen domain/scope/classification/disposition/assurance constants with private immutable backing values. Normalize JSON sequences before record creation; reject unknown schema/fields and mutable nested values.
- [ ] Implement `select_review_scopes`. Always require requirements, architecture, and test-evidence; add exactly the specialist scope named by each materially touched risk predicate; reject missing, duplicate, unsupported, ungrounded, or contradictory predicates.
- [ ] Implement `validate_review_reports`. Require exact selected-scope coverage, distinct base report paths/digests, one reviewed diff, persistence before reconciliation, complete role predicates, and deterministic issue order.
- [ ] Enforce truthful independence. Self-review is always non-independent/reduced. Independent claims require a concrete bounded basis and withheld conclusions. Count unique independent final reviewers; any pass beyond one must name a material finding that actually triggered the follow-up.
- [ ] Implement `validate_semantic_naming_review` by composing `SemanticNameRecord` and accepted contextual validation. Require every naming finding to identify its affected surface, context, intention, and specific permitted basis; no global allowlist or word blacklist.
- [ ] Implement `validate_findings`. Require complete evidence/impact/confidence/remediation/disposition for material records, exact report/finding links, and evidence-backed classifications. Speculative preferences cannot be material.
- [ ] Run focused scope/report/independence/naming/finding test classes. Expected: Task 2 classes pass; remediation, final-verification, packet, renderer, CLI, and integration classes remain RED.

### Task 3: Implement remediation, final verification, packet validation, rendering, and CLI

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/review_coordination.py`
- Modify: `tests/test_review_coordination.py` only when the harness, not an accepted contract, is wrong.

**Produces:** Repair/re-review sequencing, fresh verification, complete packet validation, deterministic rendering, read-only CLI, and integrated bundle validation.

- [ ] Implement `validate_remediation_cycles`. Require one cycle per repaired material finding, no invented finding IDs, exact changed paths, targeted command results, affected review scopes, fresh follow-up report bindings, monotonic ordering, and final disposition consistency. Explicitly accept an empty cycle set only when zero material findings require remediation.
- [ ] Implement `validate_final_verification`. Require the final reviewed-diff digest, immutable sequence newer than all repairs/reviews, exact required command set, exact expected/observed/exit/input receipts, zero exit for passing gates, explicit preserved baseline failures, and no unsupported runtime/independence/external claims.
- [ ] Implement `validate_review_packet` over exactly nineteen named semantic fields plus schema/bindings. Cross-check changed files, review order, requirements, execution evidence, reports/findings/dispositions, repairs/reruns, deviations, judgment, edge cases, implications, risks, recovery, workspace/commit boundaries, state/next action, and exact final command results.
- [ ] Implement `render_review_packet` as a deterministic human-oriented projection. Use stable headings and concise evidence summaries, not raw transcript dumping. Refuse rendering invalid packet data.
- [ ] Implement `validate_review_bundle` to compose accepted execution/recovery validation with all new review, remediation, verification, and packet checks. Validate final packet rendering against supplied Markdown without mutating either path.
- [ ] Implement `validate-bundle` with regular non-symlink input checks and deterministic exit `0` valid, `1` invariant failure, `2` usage error. Print only concise issues or a pass line; never print source/report contents, environment values, credentials, or tokens.
- [ ] Run `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination -v`. Expected: all review-coordination tests and the neutral bundle/packet integration pass.

### Task 4: Add the focused procedure and front-door/package route

**Files:**

- Create: `skills/implementing-staged-plans/references/review-coordination.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Modify: `tests/test_package_validation.py`
- Modify: `tests/test_front_door_contract.py`

**Produces:** A concise discoverable route with explicit alternative verification for declarative/package changes.

- [ ] Extend structural tests first. Require the review reference/module as regular non-symlink assets, require one narrow front-door route, retain project-neutral naming and all universal gates, and record the intended RED for missing assets/route.
- [ ] Write `review-coordination.md` in this order: prerequisites and frozen diff; required and risk-triggered scopes; raw report preservation; truthful independence; contextual semantic naming; material findings; remediation and renewed review; fresh final verification; packet data/rendering; lifecycle/authority boundary; validation commands; hard stops; bounded result.
- [ ] Add one front-door section routing required/specialist reviews, independence, findings, remediation, final verification, and packet validation to the new reference. Do not duplicate its rules or alter continuity/closure behavior.
- [ ] Extend the existing package asset tuple and focused tests. Keep deterministic issue ordering and prior package contracts.
- [ ] Record the alternative verification contract: the reference/front-door/asset declarations have no standalone runtime behavior; exact commands are the focused structural tests, package validator, skill validator, link scan, and project-neutral naming scan; expected/observed evidence is zero exit with regular assets and a resolved route; limitation is that structure does not prove actual reviewer independence or workflow execution.
- [ ] Run the focused structural tests and package validation. Expected: all pass after the assets/route exist.

### Task 5: Exercise review coordination on INC-006 and record direct evidence

**Files:**

- Modify: `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
- Modify: `implementation-programs/ISP-001/manifest.json`
- Modify: `implementation-programs/ISP-001/state/status.json`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl` only for authorized lifecycle records.
- Create: `implementation-programs/ISP-001/increments/INC-006/execution-record.md`
- Create: all initial required/specialist review paths listed in the file map.

**Produces:** A frozen INC-006 diff, separate raw reports, and source-located direct evidence without staging, commit, or reviewer dispatch.

- [ ] Re-run live repository inspection and current plan validation immediately before the first production write; stop on any new drift, accepted-byte change, or binding issue.
- [ ] Observe Task 1 RED, transition to `implementing`, complete Tasks 2-4, validate actual ownership and semantic surface coverage, then freeze the proposed non-commit diff and transition to `reviewing`.
- [ ] Classify every canonical risk predicate from the actual diff. Require security/privacy review for evidence minimization, compatibility review for new persisted schemas/package assets, and reliability review for ordering/freshness/fail-closed behavior. Record the other predicates as evidence-backed not touched; do not create unrelated specialist scopes.
- [ ] Persist requirements, architecture, test-evidence, security/privacy, compatibility, and reliability raw reports before any reconciliation. Label every actual report `controller-self-review`, non-independent, reduced assurance; do not create an independent-review claim or dispatch a reviewer.
- [ ] In architecture review, validate every actual created/renamed surface and every flagged candidate against context, intention, compatibility, and a specific governance/domain basis. In all reviews, use the complete material-finding contract and reject unsupported preferences.
- [ ] Update only directly demonstrated INC-006 `implementation_evidence` and `verification_evidence` arrays. Recompute and assert semantic digest `151cbe...10f`; stop if it changes.
- [ ] Prove commit authority remains absent and validate complete logical boundaries without `git add` or `git commit`.

### Task 6: Reconcile, remediate, verify, render, validate, and hand off

**Files:**

- Create: `implementation-programs/ISP-001/increments/INC-006/reviews/remediation.md`
- Create: `implementation-programs/ISP-001/increments/INC-006/review-evidence.json`
- Create: `implementation-programs/ISP-001/increments/INC-006/review-packet.md`
- Create: `implementation-programs/ISP-001/increments/INC-006/handoff.md`
- Modify: revision-2 traceability, manifest, status, approvals, and authorizations only as separately authorized.

**Produces:** A self-validating INC-006 review bundle and human packet at `awaiting-diff-approval`, with no commit and no INC-007 work.

- [ ] Reconcile the persisted raw reports. If any material root finding exists, transition to `remediating`, write a focused regression that fails for the intended defect, make the smallest in-plan repair, rerun affected tests, and persist renewed affected-scope review evidence before returning to `reviewing`. Do not manufacture a remediation cycle when no material defect exists.
- [ ] Stop for a program amendment if remediation changes requirements, acceptance, scope, public behavior, protected contracts, security/privacy obligations, risk posture, data ownership, dependencies, sequencing, or review cadence.
- [ ] Build the structured review evidence only after raw report digests, finding dispositions, remediation cycles, renewed reports, recovery dispositions, and a coherent candidate verification receipt exist.
- [ ] Render the packet from validated packet data. It must contain all nineteen canonical fields: identity/outcome; change/rationale; program context; files by purpose; human review order; requirements/acceptance; exact commands/results; baseline failures; test-first/alternative evidence; reviewer roles/independence/findings/dispositions; repairs/renewed verification; deviations/amendments; human judgment; edge cases/manual checks; implications; residual risks/deferred work; recovery; workspace/base/head/logical commits; state/next action.
- [ ] Run the complete candidate verification command set, seal its exact deterministic results into the evidence/packet, and render again. Then run fresh final sealing verification against the complete resulting product/review/evidence/packet tree. If any result differs, update the evidence/packet and repeat final sealing verification; do not claim freshness from an earlier tree.
- [ ] Run the actual read-only `validate-bundle` command and require byte equality between rendered and persisted packet. Static validation does not prove independent identity, human judgment quality, agent activation, deployment, data restore, provider reconciliation, or production behavior.
- [ ] Transition `reviewing` to `verified`, then `verified` to `awaiting-diff-approval` through accepted state authority. Status-only sealing must not change product/review/packet bytes after final verification.
- [ ] End at `awaiting-diff-approval`. Do not accept the diff, stage, create a commit, begin INC-007, close the program, or perform any consequential action.

## Commands and expected evidence

Focused RED/GREEN and structural commands:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_front_door_contract -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: the first invocation records the missing-module RED before implementation; review scope/report/finding classes and remediation/verification/packet classes turn green slice by slice; structural tests first fail for the missing assets/route and then pass. No command stages, commits, dispatches, or mutates external state.

Neutral integration and actual packet commands:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination.IntegrationTests -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle tests/fixtures/review-coordination/portable-archive-run/review-evidence.json --packet tests/fixtures/review-coordination/portable-archive-run/review-packet.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle implementation-programs/ISP-001/increments/INC-006/review-evidence.json --packet implementation-programs/ISP-001/increments/INC-006/review-packet.md
```

Expected: the neutral repaired-finding scenario passes with exact rendered-packet equality; the actual INC-006 bundle passes only after all raw reports, any remediation, fresh verification, recovery, and packet fields agree. The command is read-only and reports no raw contents.

Fresh final verification:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-preparation implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-plan implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858 --preparation implementation-programs/ISP-001/increments/INC-006/preparation.md --plan implementation-programs/ISP-001/increments/INC-006/exact-file-plan.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle implementation-programs/ISP-001/increments/INC-006/review-evidence.json --packet implementation-programs/ISP-001/increments/INC-006/review-packet.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans
rtk git diff --check
rtk git status --porcelain=v2 --branch
```

Expected: full tests, package/program/preparation/plan/review-bundle/skill validation, whitespace, and bounded status checks pass; status reports no staged/conflicted path and unchanged head. Exact concise outputs and exits are persisted in the structured evidence and packet. Static/local checks do not prove live agent activation, real reviewer independence, accessibility quality, deployment, data restore, provider recovery, publication, or production behavior.

Negative evidence retained:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination.ReviewReportTests.test_self_review_cannot_claim_independence -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination.ReviewReportTests.test_second_independent_reviewer_requires_material_follow_up -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination.SemanticNamingReviewTests.test_semantic_finding_requires_context_intention_and_specific_basis -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination.FinalVerificationTests.test_pre_repair_success_is_not_fresh_final_verification -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination.ReviewPacketTests.test_command_only_packet_is_rejected -v
```

Expected: all regression tests pass by rejecting invalid records while their paired valid contexts remain accepted. These are validator negative cases, not actual independent dispatch, remediation, or external action.

## Review scopes and specialist predicates

- Required actual reports: requirements/scope; architecture/boundaries/contextual semantic naming/simplicity; test adequacy/evidence validity. They use distinct raw files and are persisted before reconciliation.
- Actual review mode: controller self-review, explicitly non-independent with reduced assurance. No subagent, evaluator, or external reviewer is authorized. The module and synthetic tests support a single bounded independent final reviewer and material-defect follow-up without representing the actual INC-006 reviews as independent.
- Security/privacy predicate: **materially touched** because structured reports and command results could persist sensitive contents. The specialist checks minimum necessary locators/digests, concise redacted results, no environment/file-content capture, regular non-symlink inputs, no secret-like fixture values, and no mutation.
- Public API/compatibility predicate: **materially touched** for the new persisted evidence/packet schema identifiers, required package assets, CLI exit contract, and imports from accepted modules. The specialist checks unknown-version failure, exact fields, immutable normalization, package/link/naming tests, and no silent migration/alias claim.
- Concurrency/reliability/distributed-state predicate: **materially touched only for reliability** because report/repair/verification sequence and final-diff binding are the core invariant. The specialist checks deterministic order, stale-evidence rejection, fail-closed partial records, status-only sealing limits, and no hostile-concurrency or multi-file-atomicity claim.
- Persistent data/migrations, accessibility, platform/deployment/infrastructure, payments/financial state, performance, and provider/external state are not materially touched. Each receives an evidence-backed `not-touched` predicate and no specialist report. Required packet implication/recovery fields still state their limits.

## Commit boundaries

No stage or commit is authorized. Keep these as logical, complete, non-overlapping review slices only:

1. `test: define review coordination contracts` — focused test module and neutral review-evidence/packet fixture pair.
2. `feat: validate review evidence and packets` — review coordination module and read-only CLI.
3. `feat: route review coordination workflow` — operator reference, front door, package validator, and structural tests.
4. `docs: record review coordination evidence` — INC-006 brief/preparation/plan, direct traceability, manifest/state/approval/authorization records, execution record, raw required/specialist/remediation reports, structured evidence, packet, and handoff.

Every actual INC-006 path must appear in exactly one boundary before final review. Cross-boundary dependencies must be ordered, protected paths must appear in none, and a separate exact `create-local-commit` authorization is required before any future staging or commit command.

## Rollback and recovery

- **Source-code recovery:** Before any authorized commit, repair only exact INC-006 files from their observed pre-write bytes; never reset, clean, stash, restore, or overwrite accepted/user work. A future Git revert would require separate authority and could address only an exact authorized source commit.
- **Persistent-data recovery:** Not touched by INC-006. Structured JSON/Markdown files are source-controlled governance artifacts, not an application database. A Git/source restoration is not persistent-data recovery; any future migration needs separate backup, restore, verification, and authorization.
- **Deployment rollback:** Not touched by INC-006. No artifact is installed or deployed, and a source change or Git revert does not prove an environment rolled back.
- **Provider or external-state recovery:** Not touched by INC-006. No reviewer/provider/external service is invoked; any future provider mutation requires exact authority and provider-specific reversal or reconciliation evidence.
- Governance files retain accepted per-file compare-and-swap and append-only behavior. If an append succeeds and a later status write fails, preserve the inert event, report partial progress, and retry only from freshly observed exact digests.
- Raw initial review reports are preserved as written before reconciliation. Reconciliation and renewed-review evidence goes in `reviews/remediation.md` and structured records; do not rewrite initial conclusions to hide a finding.
- Immutable sources, approved revisions, accepted packets/handoffs, approvals, and authorizations are never rolled back. Corrections use addenda, supersession/revocation records, or a new program revision as applicable.
- No module or artifact in this plan claims true object immutability, multi-file atomicity, hostile-concurrency locking, remote freshness, independent identity, deployment state, data restoration, provider state, or complete recovery outside its named domain.

## Approval required to execute

The next legal approval must bind ISP-001 revision 2, SOURCE-002/program/semantic digests, accepted INC-005 packet/handoff/addendum and `APR-017`, `main`, selected base, current head, exact dirty inventory after these preparation writes, INC-006 brief digest, preparation digest, and this exact-file-plan digest.

Separate implementation authorization must permit only:

1. the named review module/reference/test/neutral-fixture pair, front-door/package-validator, direct traceability evidence, and INC-006 governance/review/packet/handoff writes;
2. strict test-first slices plus explicit alternative verification for non-behavioral surfaces;
3. read-only Git observation, deterministic local verification, read-only bundle validation, and accepted atomic lifecycle/governance writes;
4. three separate non-independent required reports and the three evidence-triggered non-independent specialist reports, all persisted before reconciliation with reduced assurance;
5. evidence-backed remediation limited to material INC-006 findings, affected test reruns, renewed affected-scope review, fresh final sealing verification, deterministic packet rendering, and packet equality validation;
6. logical commit-boundary validation with no staging or commit creation.

It must preserve prohibitions on reviewer/evaluator/subagent dispatch, `create-local-commit`, INC-007, installation, marketplace change, push, pull request, publication, release, deployment, migration, destructive action, provider mutation, and consequential external state.
