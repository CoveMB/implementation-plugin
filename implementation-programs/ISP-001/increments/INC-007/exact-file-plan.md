# Continuity, Closure, and Later-Action Authority Implementation Plan

**Goal:** Implement a project-neutral continuity and closure boundary that generates lean semantic navigation artifacts, independently revalidates resume state, permits full-mode continuation only from evidence-complete conversational authority, reconciles complete programs, binds closure approval to exact evidence, and keeps every later consequential action separately authorized.

**Architecture:** Add one standard-library `continuity_closure.py` module with frozen normalized records, pure deterministic validators/renderers, a read-only `validate-bundle` command, and a bounded per-file rollover operation composed from accepted state-authority persistence. Compose accepted program, state, repository-preparation, execution, and review owners instead of duplicating them. Extend state authority only enough to require exact reconciliation/closure-packet bindings at closure transitions.

**Tech stack:** Python 3.14 standard library, `unittest`, JSON continuity/reconciliation evidence, Markdown brief/handoff/closure rendering, existing program/state/preparation/execution/review/package validators, and read-only Git inspection.

## Global constraints

- Program ID: `ISP-001`; program revision: `2`; increment ID: `INC-007`.
- Source digest: `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program digest: `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Accepted traceability digest: `e338e50fcf9101fc85122473f4f731afd103c95f998c5231b8765447fe1b06c7`.
- Semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`; implementation and verification evidence may change, but ordered semantic fields and this digest must not.
- Preparation evidence digest: `a925b6d8bf1f6c692591a0b6a62e81861dd84e5214674a7e2c637503ca09347c`.
- Workspace path: `/Users/CoveMB/Code/CoveMB/implementation-plugin`; workspace branch: `main`; workspace base: `f14449b8808574c720927aedab5b64871cc63858`; workspace head: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Approval mode is `approval:full-increment`, but the user-imposed exact-plan approval gate remains controlling.
- Preserve SOURCE-001, SOURCE-002, both program revisions, accepted INC-001 through INC-006 evidence, accepted dirty work, and all unrelated or user-owned work byte-for-byte.
- Keep reusable, package-facing, test, fixture, schema, command, error, heading, and generated names project-neutral. Governance artifacts may retain required ISP/INC/SOURCE/requirement/approval/authorization coordinates.
- Use standard-library Python and existing repository mechanisms; add no dependency, runtime, provider, network integration, schema framework, application component, hook, marketplace entry, publisher surface, or CI workflow.
- Generated briefs contain the required semantic fields and only materially helpful context. They must not copy workflow policy, exact-file instructions, TDD/review rules, hard-stop catalogues, or later-action prohibition lists.
- Handoffs and briefs are navigation evidence, never authority. Resume must independently revalidate source, program, workspace, branch/base/head, state, accepted artifacts, and exact submitted navigation bytes.
- A new conversation renews `approval:full` only through a submitted matching brief and explicit user authority. Persisted mode or handoff bytes alone never transfer conversational authority.
- Actual ISP-001 closure reconciliation is excluded from INC-007. Exercise reconciliation/closure only in neutral fixtures; self-application generates the valid minimal INC-008 brief and INC-007 handoff without starting INC-008, changing the current increment identity, reconciling ISP-001, or closing ISP-001.
- Use strict RED-GREEN-REFACTOR for behavioral changes. Non-behavioral reference, route, package-asset, generated-artifact, review-report, evidence, packet, and governance work must have complete alternative verification.
- Actual INC-007 reports are separate controller self-reviews labelled non-independent with reduced assurance. No reviewer/evaluator/subagent dispatch is authorized by this plan. Synthetic tests may cover bounded independent-review inputs without claiming actual independence.
- Do not stage or create a commit. Logical commit boundaries are review artifacts only unless a later exact `create-local-commit` grant names the boundary and paths.
- Stop at INC-007 `awaiting-diff-approval`; do not accept the diff, begin INC-008, reconcile or close ISP-001, or perform any consequential external action.

## Requirements and acceptance binding

This plan advances `REQ-AUTHORITY`, `REQ-STATE-AUTHORIZATION`, `REQ-CONTINUITY-CLOSURE`, `REQ-ARTIFACT-INVARIANTS`, `REQ-VALIDATION`, `REQ-SEQUENCE`, `REQ-EVIDENCE-PLANNING`, `REQ-DEFAULTS`, `REQ-ADOPTION`, and `REQ-DESIGN-RISKS`. Direct implementation evidence is added only to atomic records demonstrated by INC-007.

Acceptance is exact:

1. generated briefs include all required semantic fields without copying workflow policy;
2. stale or mismatched briefs and handoffs fail closed;
3. a new conversation independently revalidates repository truth and renews conversational full-mode authority;
4. final-increment acceptance does not close the program;
5. closure approval and draft-PR, merge, release, deployment, migration, and provider decisions remain separate.

Integration checkpoint: INC-007 must use the implemented controller to produce a valid minimal INC-008 brief and durable INC-007 handoff while status remains on INC-007 and program state remains `active`. Neutral fixtures must demonstrate reconciliation through explicit closure approval and a separately denied/authorized later-action decision without reconciling or closing ISP-001.

## File map

### Create during implementation

- `skills/implementing-staged-plans/scripts/continuity_closure.py` — immutable continuity/closure evidence types, pure validators/renderers, bounded rollover persistence, and read-only bundle CLI.
- `skills/implementing-staged-plans/references/continuity-closure.md` — focused operator procedure and front-door target.
- `tests/test_continuity_closure.py` — focused brief, handoff, resume, continuation, rollover, reconciliation, closure, later-action, renderer, CLI, and integration contract tests.
- `tests/fixtures/continuity-closure/portable-catalog-run/continuity-evidence.json` — neutral accepted-increment, handoff, new-conversation renewal, and next-brief scenario.
- `tests/fixtures/continuity-closure/portable-catalog-run/next-increment-brief.md` — exact minimal semantic brief projection for the neutral scenario.
- `tests/fixtures/continuity-closure/portable-catalog-run/handoff.md` — exact durable navigation projection for the neutral scenario.
- `tests/fixtures/continuity-closure/portable-catalog-run/closure-reconciliation.json` — neutral final-increment, requirement, amendment, packet, finding, deferral, and program-verification reconciliation.
- `tests/fixtures/continuity-closure/portable-catalog-run/closure-packet.md` — exact deterministic human closure packet projection for the neutral scenario.
- `implementation-programs/ISP-001/increments/INC-007/execution-record.md` — observed RED/GREEN/alternative evidence, lifecycle receipts, review sequence, remediation, final verification, and explicit non-closure evidence.
- `implementation-programs/ISP-001/increments/INC-007/continuity-evidence.json` — actual INC-007 semantic brief/handoff/resume/continuation evidence; contains no ISP-001 closure reconciliation.
- `implementation-programs/ISP-001/increments/INC-007/review-evidence.json` — actual structured risk, report, finding, remediation, verification, recovery, and packet data.
- `implementation-programs/ISP-001/increments/INC-007/reviews/requirements.md` — raw non-independent requirements, acceptance, continuity, and authority review.
- `implementation-programs/ISP-001/increments/INC-007/reviews/architecture.md` — raw non-independent boundaries, naming, state minimization, and simplicity review.
- `implementation-programs/ISP-001/increments/INC-007/reviews/test-evidence.md` — raw non-independent test adequacy and evidence-validity review.
- `implementation-programs/ISP-001/increments/INC-007/reviews/specialist-security-privacy.md` — raw non-independent prompt/handoff minimization, secret-exclusion, and action-authority review selected by risk predicates.
- `implementation-programs/ISP-001/increments/INC-007/reviews/specialist-compatibility.md` — raw non-independent schema/state/approval compatibility review selected by risk predicates.
- `implementation-programs/ISP-001/increments/INC-007/reviews/specialist-reliability.md` — raw non-independent stale-state, partial-write, resume, ordering, and fail-closed review selected by risk predicates.
- `implementation-programs/ISP-001/increments/INC-007/reviews/remediation.md` — reconciliation and material-finding repair/re-review cycles; records an explicit not-triggered disposition when none exist.
- `implementation-programs/ISP-001/increments/INC-007/review-packet.md` — deterministic human review packet rendered from validated packet data.
- `implementation-programs/ISP-001/increments/INC-007/handoff.md` — durable awaiting-diff-approval navigation artifact generated by the implemented controller.
- `implementation-programs/ISP-001/increments/INC-008/brief.md` — valid minimal semantic next-work brief generated as the INC-007 integration checkpoint; it grants no INC-008 authority.

### Modify during implementation

- `skills/implementing-staged-plans/SKILL.md` — add one continuity/closure route; preserve existing front-door gates and prior routes.
- `skills/implementing-staged-plans/scripts/state_authority.py` — add exact closure reconciliation/packet bindings to the existing transition and closure-approval checks; preserve existing mode, transition, and action semantics.
- `skills/implementing-staged-plans/scripts/validate_package.py` — require the continuity reference/module through the existing asset tuple.
- `tests/test_state_authority.py` — prove direct closure-state bypass, stale closure approval, and closure-packet mismatch fail closed while prior transitions remain compatible.
- `tests/test_package_validation.py` — prove required regular-file and symlink behavior for the new assets.
- `tests/test_front_door_contract.py` — prove the concise continuity route, navigation/authority distinction, closure separation, and later-action gate.
- `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json` — add only directly demonstrated INC-007 evidence; preserve semantic fields/digest.
- `implementation-programs/ISP-001/manifest.json` — keep current INC-007 roles and latest accepted INC-006 navigation roles current; add actual continuity/review/handoff roles only when their files exist.
- `implementation-programs/ISP-001/state/status.json` — accepted lifecycle transitions and final awaiting-diff-approval evidence; keep program state `active` and current increment `INC-007`.
- `implementation-programs/ISP-001/state/approvals.jsonl` — append only the later exact plan approval and any later diff decision; never rewrite accepted events.
- `implementation-programs/ISP-001/state/action-authorizations.jsonl` — append only later exact non-commit implementation and lifecycle grants; never rewrite accepted grants.
- `implementation-programs/ISP-001/increments/INC-007/exact-file-plan.md` — amend only under the accepted amendment policy, preserving prior digest/addendum evidence.

### Already created at this preparation gate

- `implementation-programs/ISP-001/increments/INC-007/brief.md` — lean current brief.
- `implementation-programs/ISP-001/increments/INC-007/preparation.md` — repository evidence, design decision, semantic naming inventory, and risks.
- `implementation-programs/ISP-001/increments/INC-007/exact-file-plan.md` — this approval-bound implementation contract.

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
- `implementation-programs/ISP-001/increments/INC-006/`
- every path outside the exact create/modify map, including all unrelated user-owned work.

### Interfaces and ownership

- Consume `program_authority.validate_program_authority`, managed-path loading, atomic requirements, requirement groups, revisions, and semantic digest; do not copy source/traceability completeness policy.
- Consume `state_authority.RepositoryObservation`, `ApprovalBinding`, `ActionBinding`, `approval_mode_policy`, `validate_state_authority`, `may_start_next_increment`, `validate_approval_binding`, `decide_action_authorization`, `atomic_replace_json`, and `atomic_append_json_line`; do not copy state matrices, mode policy, or persistence algorithms.
- Consume `repository_preparation.inspect_repository` and current preparation/plan bindings for resume truth; do not let handoff/brief fields substitute for live observation or drift classification.
- Consume accepted execution amendment/recovery evidence and review report/finding/remediation/final-verification/packet contracts by exact digest; do not restate their policy.
- Produce `LeanBrief`, `HandoffRecord`, `ConversationAssessment`, `ResumeContext`, `ClosureRequirementDisposition`, `ClosureReconciliation`, `ClosurePacket`, `ContinuityWriteReceipt`, and `LaterActionDecision` as frozen records with normalized tuple/frozenset fields.
- Produce `render_increment_brief`, `validate_increment_brief`, `render_handoff`, `validate_handoff`, `evaluate_continuation`, `validate_resume_context`, `apply_increment_rollover`, `validate_closure_reconciliation`, `render_closure_packet`, `validate_closure_packet`, `decide_later_action`, and `validate_continuity_bundle`.
- Define `implementation-continuity-evidence/v1`, `implementation-closure-reconciliation/v1`, and `implementation-closure-packet/v1`. Reject unknown schemas/fields, mutable nested sequences, duplicate identifiers, ambiguous matches, and booleans supplied as integer sequence/exit values.
- `LeanBrief` requires program/revision, increment/title, outcome, requirement identifiers, acceptance pointer/criteria, mode, workspace/status/handoff navigation, and unresolved user decisions. Its renderer permits only approved optional context and rejects copied workflow-policy headings or catalogues while preserving materially necessary increment-specific constraints.
- `HandoffRecord` requires program/revision, current increment/state, mode, workspace/base/head, accepted increments and packet bindings, verification status, amendments, unresolved risks, next legal action, and first-read files. It cannot grant an action or conversation authority.
- `ResumeContext` binds the submitted brief/handoff bytes and digests to a fresh repository observation plus current manifest/status/workspace/accepted artifacts. Any mismatch fails before rollover or implementation.
- `ConversationAssessment` requires explicit evidence for boundary, risk/architecture shift, workspace/base change, superseded discussion, evidence/expertise shift, and lossless-summary feasibility. Only `approval:full` with every suitability predicate satisfied may continue without renewed user authority; a new conversation always requires the submitted matching brief and renewed user instruction.
- `apply_increment_rollover` accepts only validated records, exact expected file digests/absence assertions, and a matching `write-program-artifact` action authorization. It writes handoff/brief before manifest/status through accepted per-file primitives, returns every receipt, preserves inert partial writes on failure, and never claims multi-file atomicity or begins the next increment without a legal current-state decision.
- Closure reconciliation requires the final increment accepted, one exact disposition for every atomic requirement, approved amendment/decision resolution, accepted packet/addendum integrity, later-invalidation checks, zero unresolved material findings/deferrals without owned decision, fresh program-level commands, architecture/documentation/operations/recovery reassessment, and an exact rendered closure packet.
- Add optional `closure_reconciliation_sha256` and `closure_packet_sha256` fields to closure approval binding only. Existing non-closure approvals remain byte/schema compatible. State authority must reject `active -> awaiting-closure-approval` without exact validated closure bindings and reject `awaiting-closure-approval -> closed` unless the approval event binds the exact closure packet/reconciliation.
- `decide_later_action` validates but never performs `create-draft-pull-request`, merge, release, deploy/production modification, migration, destructive data action, or provider/external mutation. It requires closed state, exact closure approval, the exact action/scope grant, and applicable recovery evidence. Closure approval alone returns denied.
- The CLI reads only explicit regular non-symlink JSON/Markdown paths, performs no Git/subprocess/state/network/provider mutation, prints no contents or environment values, and returns deterministic status `0` valid, `1` invariant failure, `2` usage error. Rollover remains a library operation invoked only after separate authority, not a CLI side effect.

## Semantic naming inventory

| Surface | Kind | Context | Intention | Origin | Planning-term basis | Basis owner | Compatibility class | Compatibility disposition |
|---|---|---|---|---|---|---|---|---|
| `continuity_closure.py` | path | cross-conversation and program-completion control | validate navigation, resume, reconciliation, closure, and later-action evidence | new | none | none | private | new internal module; no migration |
| `continuity-closure.md` | path | operator procedure | route continuity and closure safeguards | new | none | none | package | new required asset; package tests lock it |
| `implementation-continuity-evidence/v1` | schema-or-identifier | durable continuity evidence | reject incompatible brief, handoff, resume, and conversation records | new | durable-domain | continuity evidence schema | persisted | versioned schema; unsupported versions fail |
| `implementation-closure-reconciliation/v1` | schema-or-identifier | program completion evidence | reject incomplete reconciliation | new | durable-domain | closure reconciliation schema | persisted | versioned schema; unsupported versions fail |
| `implementation-closure-packet/v1` | schema-or-identifier | human closure review | bind the exact approval target | new | durable-domain | closure packet schema | persisted | versioned schema; unsupported versions fail |
| `LeanBrief` | symbol | semantic work selection | hold required scope/navigation without workflow policy | new | none | none | private | new internal API |
| `HandoffRecord` | symbol | durable navigation | bind accepted progress, risks, next action, and first-read files | new | none | none | private | new internal API |
| `ConversationAssessment` | symbol | automatic continuation | record evidence for context suitability or mandatory handoff | new | none | none | private | new internal API |
| `ResumeContext` | symbol | independent restart validation | bind current observation, navigation artifacts, state, and renewed authority | new | none | none | private | new internal API |
| `ClosureRequirementDisposition` | symbol | program reconciliation | bind one atomic requirement to final disposition/evidence | new | none | none | private | new internal API |
| `ClosureReconciliation` | symbol | closure readiness | bind complete program reconciliation and verification | new | durable-domain | closure workflow | private | new internal API |
| `ClosurePacket` | symbol | closure review | hold exact reconciliation summary, risks, recovery, and next action | new | durable-domain | closure packet contract | private | new internal API |
| `ContinuityWriteReceipt` | symbol | rollover recovery | report ordered writes and inert partial progress | new | none | none | private | new internal API |
| `LaterActionDecision` | symbol | post-closure authority | explain denial or exact separate authority | new | none | none | private | new internal API |
| `render_increment_brief` | symbol | lean prompt generation | render required semantic and material optional fields | new | none | none | private | new internal API |
| `validate_increment_brief` | symbol | lean prompt validation | reject missing semantics, copied policy, and stale bindings | new | none | none | private | new internal API |
| `render_handoff` | symbol | durable handoff generation | render exact validated navigation evidence | new | none | none | private | new internal API |
| `validate_handoff` | symbol | durable handoff validation | require complete navigation and accepted-state bindings | new | none | none | private | new internal API |
| `evaluate_continuation` | symbol | conversation boundary | require full-mode suitability or renewed authority | new | none | none | private | new internal API |
| `validate_resume_context` | symbol | resume fail-closed gate | reject stale repository/state/navigation tuples | new | none | none | private | composes accepted validators |
| `apply_increment_rollover` | symbol | authorized next-work persistence | write validated navigation and controlling state in recoverable order | new | none | none | private | composes accepted persistence |
| `validate_closure_reconciliation` | symbol | program completion | require complete resolution and fresh program evidence | new | none | none | private | new internal API |
| `render_closure_packet` | symbol | closure review | render deterministic human approval target | new | none | none | private | new internal API |
| `validate_closure_packet` | symbol | closure approval binding | reject packet/evidence drift and unsupported claims | new | none | none | private | new internal API |
| `decide_later_action` | symbol | consequential action gate | require closure plus separate exact grant/recovery | new | none | none | private | composes accepted action authority |
| `validate_continuity_bundle` | symbol | integrated evidence | compose continuity, closure, and later-action gates | new | none | none | private | new internal API |
| `validate-bundle` | command | operator validation | compare structured evidence with exact Markdown | new | none | none | package | read-only command; stable exit contract |
| `portable-catalog-run` | test-or-fixture | neutral catalog-maintenance scenario | exercise handoff/resume through closure and separate later action | new | none | none | test | synthetic fixture; no migration |
| `test_stale_handoff_cannot_authorize_resume` | test-or-fixture | continuity regression | reject navigation that no longer matches repository truth | new | none | none | test | project-neutral test title |
| `test_final_acceptance_does_not_close_program` | test-or-fixture | closure regression | preserve acceptance/reconciliation/approval/closure separation | new | none | none | test | project-neutral test title |
| INC-007 and generated INC-008 governance artifacts | heading | implementation governance | bind evidence, review, handoff, and next-work selection | new | implementation-governance | ISP-001 manifest | repository-only | required governance identifiers |

## Test-first slices and verification contracts

### Task 0: Bind plan approval and non-commit implementation authority

**Files:**

- Modify: `implementation-programs/ISP-001/state/approvals.jsonl`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl`
- Modify: `implementation-programs/ISP-001/state/status.json`

**Produces:** One exact plan approval and one separate non-commit implementation/review grant before package/test/fixture/product/review writes. Commit, INC-008, ISP-001 closure, and dispatch authority remain absent.

- [ ] Revalidate SOURCE-001/SOURCE-002, both program revisions, semantic digest, INC-006 accepted bindings, branch/base/head, active operation, full dirty inventory, brief digest, preparation digest, and this plan digest.
- [ ] Append one `implementation-approval/v1` `exact-file-plan-approval` event binding INC-007, the current tuple, and the user gate.
- [ ] Append one `implementation-action-authorization/v1` grant limited to the exact create/modify map, strict test-first/alternative evidence, deterministic local verification, separate non-independent required/specialist reports, and evidence-backed material remediation. Exclude staging, `create-local-commit`, reviewer/evaluator/subagent dispatch, INC-008 execution, ISP-001 closure reconciliation/approval, and all external/consequential actions.
- [ ] Advance INC-007 only from `awaiting-plan-approval` to `authorized` through accepted state authority. Do not mark `implementing` before Task 1 RED is observed.

### Task 1: Define continuity and closure contracts and observe RED

**Files:**

- Create: `tests/test_continuity_closure.py`
- Create: the five neutral fixture files under `tests/fixtures/continuity-closure/portable-catalog-run/`
- Modify: `tests/test_state_authority.py`

**Interfaces:**

- Consumes: accepted program/state/preparation/execution/review fixtures and immutable-record conventions.
- Produces: executable contracts for every public record/function/CLI and exact state closure binding listed under Interfaces and ownership.

- [ ] Add immutable schema/field tests for briefs, handoffs, conversation assessments, resume contexts, requirement dispositions, reconciliation, closure packets, rollover receipts, and later-action decisions. Normalize nested lists before construction and reject booleans as integer sequence/exit values.
- [ ] Add brief tests requiring exactly the eight source fields, approved optional context only, deterministic Markdown, exact program/revision/increment/mode/workspace/status/handoff bindings, and no duplicated workflow-policy sections/catalogues. Pair a complete minimal brief with missing-field, stale-binding, copied-policy, and materially necessary-context cases.
- [ ] Add handoff tests requiring every Section 13.7 field, exact accepted packet/addendum/status/workspace/base/head bindings, deterministic Markdown, first-read files, and a next legal action that grants nothing. Reject stale, mismatched, incomplete, secret-like, and action-authorizing handoffs.
- [ ] Add conversation tests covering all six suitability predicates, every mode, a part/risk/workspace/context boundary, lossless-summary failure, automatic same-conversation `approval:full`, one-increment stops, and new-conversation renewal only from the submitted matching brief plus explicit user authority.
- [ ] Add resume tests that construct a fresh repository observation and fail on changed source/program/semantic/workspace/branch/base/head/status/brief/handoff/accepted packet/addendum bytes, active operation, conflict, duplicate matching record, unsupported schema, or missing renewed authority. Assert handoff prose cannot repair a persisted mismatch.
- [ ] Add rollover tests requiring legal current accepted state, exact next increment/program dependency, matching brief/handoff, exact action grant, expected file absence/digests, deterministic write order, per-file receipts, and fresh revalidation after injected failure. Prove inert partial artifacts grant no authority and unrelated/user-owned paths remain unchanged.
- [ ] Add reconciliation tests requiring exactly one final disposition for every atomic requirement, complete accepted increment/packet/addendum bindings, approved amendments and decisions, deferral ownership, later-invalidation checks, zero unresolved material findings, fresh program-level commands, and architecture/documentation/operations/recovery reassessment.
- [ ] Add closure tests proving final-increment acceptance leaves program `active`; `active -> awaiting-closure-approval` needs exact validated reconciliation/packet bindings; `awaiting-closure-approval -> closed` needs one explicit approval bound to their digests; changed, missing, duplicate, rejected, stale, or generic approval records fail.
- [ ] Add later-action tests for draft PR, merge, release, deploy/production modification, migration, destructive data action, and provider/external mutation. Closure approval alone denies all; closed state plus exact action/scope grant and applicable recovery evidence authorizes only the decision, never performs the action.
- [ ] Add the neutral portable-catalog scenario: accepted final work; valid handoff; new-conversation renewal; complete reconciliation; exact closure packet; explicit closure approval; separately denied then exactly authorized draft-PR decision. Add distinct negative scenarios for overloaded continuation, stale handoff, premature closure, and inferred later authority.
- [ ] Run `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure -v`. Expected RED: import fails because `skills/implementing-staged-plans/scripts/continuity_closure.py` does not exist. Persist the exact failure and tree state before production code.

### Task 2: Implement lean brief, handoff, resume, continuation, and rollover behavior

**Files:**

- Create: `skills/implementing-staged-plans/scripts/continuity_closure.py`
- Modify: `tests/test_continuity_closure.py` only when the harness, not an accepted contract, is wrong.

**Produces:** Versioned immutable continuity records plus pure generation/validation/decision functions and recoverable next-increment persistence.

- [ ] Define exact schema, mode, suitability-predicate, disposition, closure-field, and later-action constants with private immutable backing values. Normalize JSON sequences to tuples/frozensets and reject unknown schema/fields.
- [ ] Implement `validate_increment_brief` and `render_increment_brief`. Require all semantic fields and exact navigation bindings, preserve materially necessary optional context, reject absent semantics and workflow-policy duplication, and render stable concise Markdown without using a raw length threshold as a substitute for semantics.
- [ ] Implement `validate_handoff` and `render_handoff`. Require all durable navigation fields, accepted artifact digests, risks/amendments/verification, next legal action, and first-read files; reject any text or field that purports to authorize work or consequential action.
- [ ] Implement `validate_resume_context` by composing fresh program/state/preparation validation with exact submitted brief/handoff and accepted-artifact digests. Return deterministic issues at the first authority boundary and expose no file contents, environment values, or credentials.
- [ ] Implement `evaluate_continuation`. Require one evidence record per suitability predicate, exact mode behavior, same-conversation evidence for automatic `approval:full`, and submitted-brief plus explicit renewed authority for every new conversation. Return a mandatory handoff decision when any context predicate fails.
- [ ] Implement `apply_increment_rollover` with validated proposed bytes, exact action binding, expected digest/absence assertions, handoff/brief-first then manifest/status ordering, accepted atomic writes, and `ContinuityWriteReceipt`. On injected or real failure, preserve completed writes as inert evidence, report exact receipts, and require a fresh resume decision; never roll back by deleting or overwriting user work.
- [ ] Run focused brief/handoff/resume/conversation/rollover test classes. Expected: Task 2 classes pass; reconciliation, closure, later-action, CLI, and integration classes remain RED.

### Task 3: Implement reconciliation, closure packet, later-action gates, and CLI

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/continuity_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `tests/test_continuity_closure.py` and `tests/test_state_authority.py` only when the harness, not an accepted contract, is wrong.

**Produces:** Complete program reconciliation, deterministic closure packet, exact closure transition binding, separate later-action decisions, and integrated read-only validation.

- [ ] Implement `validate_closure_reconciliation`. Load validated program/traceability records; require exact atomic-requirement partition and allowed final dispositions, accepted increment/artifact integrity, amendment/decision/deferral/finding resolution, later-invalidation checks, and fresh program-level command receipts newer than all contributing evidence.
- [ ] Implement `validate_closure_packet` and `render_closure_packet`. Require program identity/revision; final increment acceptance; requirement/amendment/deferral summary; accepted packet integrity; program verification; architecture/documentation/operations/recovery assessment; findings/dispositions; residual risks; exact reconciliation digest; current state; closure-approval request; and next action. Refuse unsupported completion or external-state claims.
- [ ] Extend closure transition binding in `state_authority.py`. `active -> awaiting-closure-approval` requires current final increment `accepted`, manifest-owned regular reconciliation/packet paths, matching status digests, zero blocking counts, and exact readiness evidence. `awaiting-closure-approval -> closed` requires one `program-closure-approval` event whose optional closure digest fields exactly match; non-closure approval behavior remains unchanged.
- [ ] Implement `decide_later_action`. Require closed status, exact closure approval and packet/reconciliation bindings, one exact non-revoked/unexpired action/scope grant, and applicable recovery evidence. Return deterministic denied reasons for pre-closure, closure-only, wrong action/scope, stale digest, missing recovery, conflicting, or duplicate grants.
- [ ] Implement `validate_continuity_bundle` to compose continuity, optional closure, state closure binding, and later-action decisions without requiring closure data for a non-final increment. Validate exact rendered brief/handoff/closure packet equality.
- [ ] Implement `validate-bundle` with explicit regular non-symlink JSON/Markdown inputs and deterministic exit `0` valid, `1` invariant failure, `2` usage error. Print only concise issues or a pass line; never mutate state or print source/artifact contents.
- [ ] Run `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_state_authority -v`. Expected: all focused continuity/closure/state tests and neutral Markdown equality pass; every pre-existing state test remains green.

### Task 4: Add the focused procedure and front-door/package route

**Files:**

- Create: `skills/implementing-staged-plans/references/continuity-closure.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Modify: `tests/test_package_validation.py`
- Modify: `tests/test_front_door_contract.py`

**Produces:** A concise discoverable route with explicit alternative verification for declarative/package changes.

- [ ] Extend structural tests first. Require the continuity reference/module as regular non-symlink assets, one narrow front-door route, navigation-not-authority language, closure/later-action separation, and all prior universal gates. Record the intended RED for missing assets/route.
- [ ] Write `continuity-closure.md` in this order: prerequisites/current truth; semantic brief generation; durable handoff; conversation suitability; independent resume validation; authorized rollover and partial progress; reconciliation; closure packet/approval; later actions; validation commands; hard stops; bounded result.
- [ ] Add one front-door section routing brief/handoff generation, resume/full-mode decisions, reconciliation, closure, and later actions to the new reference. Do not copy its field lists, suitability catalogue, reconciliation rules, or action matrix.
- [ ] Extend the existing package asset tuple and focused tests. Keep deterministic issue ordering and prior package contracts.
- [ ] Record the alternative verification contract: reference/front-door/asset declarations have no standalone runtime behavior; exact commands are the focused structural tests, package validator, skill validator, link scan, and project-neutral naming scan; expected evidence is zero exit with regular assets and a resolved concise route; limitation is that structure does not prove live conversation quality, user authority, closure completeness, or external action state.
- [ ] Run focused structural tests and package validation. Expected: all pass after assets/route exist.

### Task 5: Exercise INC-007 implementation and record direct evidence

**Files:**

- Modify: `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
- Modify: `implementation-programs/ISP-001/manifest.json`
- Modify: `implementation-programs/ISP-001/state/status.json`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl` only for authorized lifecycle records.
- Create: `implementation-programs/ISP-001/increments/INC-007/execution-record.md`
- Create: all initial required/specialist review paths listed in the file map.

**Produces:** A frozen INC-007 product diff, separate raw reports, and source-located direct evidence without staging, commit, INC-008 execution, or ISP-001 closure reconciliation.

- [ ] Re-run live repository inspection and current plan validation immediately before the first production write; stop on any new drift, accepted-byte change, or binding issue.
- [ ] Observe Task 1 RED, transition to `implementing`, complete Tasks 2-4, validate actual ownership and semantic surface coverage, then freeze the proposed non-commit diff and transition to `reviewing`.
- [ ] Classify every canonical risk predicate from the actual diff. Require security/privacy review for prompt/handoff minimization and secret exclusion, compatibility review for new persisted schemas and optional closure approval fields, and reliability review for stale-state/ordering/partial-write/recovery behavior. Record other predicates as evidence-backed not touched; do not create unrelated specialist scopes.
- [ ] Persist requirements, architecture, test-evidence, security/privacy, compatibility, and reliability raw reports before reconciliation. Label every actual report `controller-self-review`, non-independent, reduced assurance; do not create an independent-review claim or dispatch a reviewer.
- [ ] In architecture review, validate every actual created/renamed surface and flagged candidate against context, intention, compatibility, and a specific governance/domain basis. In all reviews, use the complete material-finding contract and reject unsupported preferences.
- [ ] Update only directly demonstrated INC-007 `implementation_evidence` and `verification_evidence` arrays. Recompute and assert semantic digest `151cbe...10f`; stop if it changes.
- [ ] Prove current status remains INC-007/program `active`, INC-008 has not started, no ISP-001 closure roles or reconciliation exist, commit authority remains absent, and complete logical boundaries validate without `git add` or `git commit`.

### Task 6: Reconcile reviews, verify, generate navigation, validate packets, and hand off

**Files:**

- Create: `implementation-programs/ISP-001/increments/INC-007/reviews/remediation.md`
- Create: `implementation-programs/ISP-001/increments/INC-007/continuity-evidence.json`
- Create: `implementation-programs/ISP-001/increments/INC-007/review-evidence.json`
- Create: `implementation-programs/ISP-001/increments/INC-007/review-packet.md`
- Create: `implementation-programs/ISP-001/increments/INC-007/handoff.md`
- Create: `implementation-programs/ISP-001/increments/INC-008/brief.md`
- Modify: revision-2 traceability, manifest, status, approvals, and authorizations only as separately authorized.

**Produces:** A self-validating INC-007 review/continuity bundle at `awaiting-diff-approval`, with a valid minimal INC-008 brief and no INC-008 or ISP-001 closure authority.

- [ ] Reconcile persisted raw reports. If a material root finding exists, transition to `remediating`, write a focused regression that fails for the intended defect, make the smallest in-plan repair, rerun affected tests, and persist renewed affected-scope review evidence before returning to `reviewing`. Do not manufacture a remediation cycle when no material defect exists.
- [ ] Stop for a program amendment if remediation changes requirements, acceptance, scope, public behavior, protected contracts, security/privacy obligations, risk posture, data ownership, dependencies, sequencing, or review cadence.
- [ ] Build actual continuity evidence only after final source/program/semantic/workspace/status/accepted INC-006 and frozen INC-007 candidate bindings exist. Mark closure reconciliation and later-action decisions not applicable to this non-final accepted state; do not create ISP-001 closure artifacts.
- [ ] Generate the INC-008 brief from persisted program/state and the planned INC-007 handoff data. Require all semantic fields, only material context, exact deterministic rendering, and explicit non-authority. Its presence must not change current increment identity or state and must not authorize any INC-008 command or write.
- [ ] After review/remediation and fresh verification, generate the INC-007 handoff with exact review packet, verification, workspace/base/head, risks, next legal action, and first-read files. Validate both generated Markdown files against the actual continuity evidence byte-for-byte.
- [ ] Build the structured review evidence and render the nineteen-field INC-007 review packet only after report digests, finding dispositions, remediation, recovery, continuity evidence, generated navigation, and final command receipts agree.
- [ ] Run complete candidate verification, seal exact results into evidence/packet, render again, and rerun final sealing verification against the complete product/review/evidence/navigation tree. If any result differs, update evidence/packet/navigation and repeat; do not claim freshness from an earlier tree.
- [ ] Run actual read-only continuity and review `validate-bundle` commands. Static/local validation does not prove live agent activation, conversation quality, renewed user intent, independent identity, human judgment quality, deployment, data restore, provider reconciliation, or production behavior.
- [ ] Transition `reviewing` to `verified`, then `verified` to `awaiting-diff-approval` through accepted state authority. Status-only sealing must not change product/review/continuity/packet/navigation bytes after final verification.
- [ ] End at INC-007 `awaiting-diff-approval` with program `active`. Do not accept the diff, roll current identity to INC-008, stage, create a commit, reconcile or close ISP-001, ask about a draft PR, or perform any consequential action.

## Commands and expected evidence

Focused RED/GREEN and structural commands:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_front_door_contract -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: the first invocation records the missing-module RED before implementation; continuity and closure classes turn green slice by slice; state tests first reject absent closure bindings and then pass with exact bindings while all earlier transitions remain green; structural tests first fail for missing assets/route and then pass. No command stages, commits, dispatches, starts INC-008, reconciles ISP-001, or mutates external state.

Neutral integration commands:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure.IntegrationTests -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/continuity_closure.py validate-bundle tests/fixtures/continuity-closure/portable-catalog-run/continuity-evidence.json --brief tests/fixtures/continuity-closure/portable-catalog-run/next-increment-brief.md --handoff tests/fixtures/continuity-closure/portable-catalog-run/handoff.md --reconciliation tests/fixtures/continuity-closure/portable-catalog-run/closure-reconciliation.json --closure-packet tests/fixtures/continuity-closure/portable-catalog-run/closure-packet.md
```

Expected: the neutral handoff/new-conversation renewal/reconciliation/closure/later-action scenario passes with exact Markdown equality. Paired invalid fixtures/tests reject overloaded continuation, stale navigation, incomplete reconciliation, premature closure, closure-only draft-PR authority, and mismatched action/recovery evidence. The CLI is read-only and reports no source contents.

Actual INC-007 continuity and packet commands:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/continuity_closure.py validate-bundle implementation-programs/ISP-001/increments/INC-007/continuity-evidence.json --brief implementation-programs/ISP-001/increments/INC-008/brief.md --handoff implementation-programs/ISP-001/increments/INC-007/handoff.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle implementation-programs/ISP-001/increments/INC-007/review-evidence.json --packet implementation-programs/ISP-001/increments/INC-007/review-packet.md
```

Expected: actual continuity validation passes without `--reconciliation` or `--closure-packet`, proves generated Markdown equality and current INC-007/program-active bindings, and refuses any closure or later-action claim. Actual review validation passes only after raw reports, remediation, fresh verification, recovery, continuity evidence, and packet fields agree.

Fresh final verification:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-preparation implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-plan implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858 --preparation implementation-programs/ISP-001/increments/INC-007/preparation.md --plan implementation-programs/ISP-001/increments/INC-007/exact-file-plan.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/continuity_closure.py validate-bundle implementation-programs/ISP-001/increments/INC-007/continuity-evidence.json --brief implementation-programs/ISP-001/increments/INC-008/brief.md --handoff implementation-programs/ISP-001/increments/INC-007/handoff.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle implementation-programs/ISP-001/increments/INC-007/review-evidence.json --packet implementation-programs/ISP-001/increments/INC-007/review-packet.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans
rtk git diff --check
rtk git status --porcelain=v2 --branch
```

Expected: full tests, package/program/preparation/plan/continuity/review-bundle/skill validation, whitespace, and bounded status checks pass; status reports no staged/conflicted path, unchanged head, current INC-007, program `active`, and no ISP-001 closure binding. Exact concise outputs/exits are persisted in evidence and packet. Static/local checks do not prove live conversational renewal, human closure approval, external action state, or production behavior.

Negative evidence retained:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure.BriefTests.test_workflow_policy_cannot_be_copied_into_brief -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure.ResumeTests.test_stale_handoff_cannot_authorize_resume -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure.ContinuationTests.test_new_conversation_requires_matching_brief_and_renewed_authority -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure.ClosureTests.test_final_acceptance_does_not_close_program -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure.LaterActionTests.test_closure_approval_does_not_authorize_draft_pull_request -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority.StateApplicationAndCliTests.test_closure_transition_requires_exact_reconciliation_and_packet -v
```

Expected: all regression tests pass by rejecting invalid records/transitions while paired valid contexts remain accepted. These are synthetic validator cases, not actual ISP-001 reconciliation, closure approval, draft-PR creation, external action, or new-conversation authority.

## Review scopes and specialist predicates

- Required actual reports: requirements/acceptance/authority; architecture/boundaries/contextual semantic naming/state minimization; test adequacy/evidence validity. They use distinct raw files and are persisted before reconciliation.
- Actual review mode: controller self-review, explicitly non-independent with reduced assurance. No subagent, evaluator, or external reviewer is authorized. Synthetic tests may represent a bounded independent input without claiming actual INC-007 independence.
- Security/privacy predicate: **materially touched** because generated briefs/handoffs and evidence could persist secrets, private context, or excessive content, and later-action decisions are authorization-sensitive. Review minimum necessary fields, secret-like rejection, no transcript/environment/file-content capture, safe error output, and no authority escalation.
- Public API/compatibility predicate: **materially touched** for new persisted schema identifiers, required package assets, CLI exit/argument contract, optional closure approval fields, status closure binding, and imports from accepted modules. Review unknown-version failure, exact optional-field behavior, immutable normalization, package/link/naming tests, and backward compatibility for existing non-closure records.
- Concurrency/reliability/distributed-state predicate: **materially touched only for reliability** because stale bindings, ordered rollover writes, partial progress, resume, final verification, and closure sequencing are core invariants. Review deterministic order, failure injection, inert partial artifacts, compare-and-swap behavior, resume revalidation, and no hostile-concurrency/multi-file-atomicity claim.
- Persistent application data/migrations, accessibility, platform/deployment/infrastructure, payments/financial state, performance, and provider/external state are not materially touched. Each receives an evidence-backed `not-touched` predicate and no specialist report. Closure/later-action fixtures mention these domains only to prove authorization/recovery gates, not to mutate or validate an external system.

## Commit boundaries

No stage or commit is authorized. Keep these as logical, complete, non-overlapping review slices only:

1. `test: define continuity and closure contracts` — focused continuity/state tests and neutral continuity/brief/handoff/reconciliation/closure fixtures.
2. `feat: validate continuity and closure evidence` — continuity/closure module, rollover operation, state closure binding, and read-only CLI.
3. `feat: route continuity and closure workflow` — operator reference, front door, package validator, and structural tests.
4. `docs: record continuity and closure evidence` — INC-007 preparation/plan, direct traceability, manifest/state/approval/authorization records, execution record, raw reports/remediation, continuity/review evidence, packet, generated INC-007 handoff, and generated INC-008 brief.

Every actual INC-007 path must appear in exactly one boundary before final review. Cross-boundary dependencies must be ordered, protected paths must appear in none, and a separate exact `create-local-commit` authorization is required before any future staging or commit command.

## Rollback and recovery

- **Source-code recovery:** Before any authorized commit, repair only exact INC-007 files from observed pre-write bytes; never reset, clean, stash, restore, delete, or overwrite accepted/user work. A future Git revert would require separate authority and could address only an exact authorized source commit.
- **Persistent-data recovery:** No application database or user data is touched. JSON/Markdown program artifacts are governance state. Per-file compare-and-swap and append-only writes provide recovery evidence but not a transaction. A Git/source restoration is not application-data recovery; future migrations require separate backup, restore, verification, and authority.
- **Deployment rollback:** Not touched. No artifact is installed or deployed, and source restoration does not prove an environment rollback.
- **Provider or external-state recovery:** Not touched. No external reviewer/provider/service or pull-request API is invoked; future provider mutation requires exact authority and provider-specific reversal/reconciliation evidence.
- Rollover writes validated handoff/brief bytes before manifest/status. If a later write fails, preserve earlier files as inert evidence, report every receipt, keep controlling state unchanged where possible, and resume only after fresh observation. Do not delete partial artifacts or treat their presence as authority.
- Closure readiness writes reconciliation/packet before status enters `awaiting-closure-approval`. Partial artifacts grant nothing. A stale or unmatched closure approval cannot close the program.
- Initial raw review reports remain immutable after reconciliation. Remediation and renewed review go in the remediation record and structured evidence; do not rewrite initial conclusions to hide a finding.
- Immutable sources, approved revisions, accepted packets/handoffs/addenda, approvals, and authorizations are never rolled back. Corrections use addenda, supersession/revocation records, or a new program revision as applicable.
- No module or artifact claims true object immutability, cross-file atomicity, hostile-concurrency locking, remote freshness, live conversational intent, independent identity, closure approval, external action execution, deployment state, data restoration, provider state, or complete recovery outside its named domain.

## Approval required to execute

The next legal approval must bind ISP-001 revision 2, SOURCE-002/program/semantic digests, accepted INC-006 packet/handoff/addendum and `APR-019`, `main`, selected base, current head, exact dirty inventory after these preparation writes, INC-007 brief digest, preparation digest, and this exact-file-plan digest.

Separate implementation authorization must permit only:

1. the named continuity/closure module/reference/test/neutral fixtures, narrow state-authority closure binding, front-door/package-validator, direct traceability evidence, and INC-007 governance/review/packet/handoff plus generated INC-008 brief writes;
2. strict test-first slices plus explicit alternative verification for non-behavioral surfaces;
3. read-only Git observation, deterministic local verification, read-only continuity/review bundle validation, and accepted atomic lifecycle/governance writes;
4. three separate non-independent required reports and the three evidence-triggered non-independent specialist reports, all persisted before reconciliation with reduced assurance;
5. evidence-backed remediation limited to material INC-007 findings, affected test reruns, renewed affected-scope review, fresh final sealing verification, deterministic navigation/packet rendering, and exact Markdown equality validation;
6. neutral synthetic reconciliation/closure/later-action fixtures only, plus actual INC-007 continuity evidence that explicitly excludes ISP-001 closure;
7. logical commit-boundary validation with no staging or commit creation.

It must preserve prohibitions on reviewer/evaluator/subagent dispatch, `create-local-commit`, staging, INC-008 execution or identity rollover, actual ISP-001 closure reconciliation/approval/closure, installation, marketplace change, push, pull request, merge, publication, release, deployment, migration, destructive action, provider mutation, and consequential external state.
