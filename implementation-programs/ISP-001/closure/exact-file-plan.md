# Program Closure Reconciliation Exact-File Plan

**Goal:** Account for the complete accepted ISP-001 revision-2 program, produce deterministic whole-program reconciliation and closure-review artifacts only when every blocker count is zero, transition the active program only to `awaiting-closure-approval`, and stop without closing ISP-001 or performing a later action.

## Global constraints

- Program ID: `ISP-001`.
- Program revision: `2`.
- Increment ID: `CLOSURE` (the separate post-INC-008 governance step, not a ninth implementation increment).
- Approval mode: `approval:full-increment`.
- Source digest: `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program digest: `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Traceability digest: `a5fb73c3b9fa8619e0a225c2a388e20a88c475b291805508466dbd324a114cb0`.
- Semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Workspace path: `/Users/CoveMB/Code/CoveMB/implementation-plugin`.
- Workspace branch: `main`.
- Workspace base: `f14449b8808574c720927aedab5b64871cc63858`.
- Workspace head: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Accepted status input: sequence `69`, SHA-256 `1c12575d6af27e942c2ffdc91260bb6177885f7c036d8faf7ffac9fe7a81e38b`.
- Accepted final increment: `INC-008`, approval `APR-023`, candidate `34e1d8685c44b5a4aaab90041a66aa35bee1552e169cda6c584ce8075703d753`.
- Accepted INC-008 review packet: `d870ce5bd8a0d8061d4ce2108cfc441e6842719a601cc4603145b0865b894d8d`.
- Accepted INC-008 addendum: `6b394698853809df3804c850be3d7b08618008f63d01bebf1a63c7f7dbe2b3c5`.
- Closure brief: `6c54077809df02f51569c390043793f1959622754c1cfab0e52eef8ab4c1d0ca`.
- Closure preparation: `b6d19db1a51eb1905ac31ba52c022d1e0cb0b31bac78d009d47860b2361c87ca`.

All source, program, traceability, workspace, approval, authorization, accepted increment, review, remediation, packet, handoff, addendum, integration, pressure, and readiness evidence bytes are preserve-only. Before each write batch, revalidate the exact tuple above, current Git observation, the manifest-owned closure preparation binding, and the still-current exact plan approval/action authorization. Stop on any mismatch.

This step contains no production implementation, test change, schema change, dependency change, accepted-evidence rewrite, staging, or commit. It authorizes no closure approval, program closure, draft-pull-request decision or creation, push, merge, publication, release, deployment, migration, destructive action, provider mutation, or other consequential external action. Logical commit boundaries are review labels only.

The closure exact-plan approval is a disclosed manual digest gate because the accepted state schema has no separate post-increment plan-approval transition. The existing state machinery must still mechanically validate the final closure bindings and the `active -> awaiting-closure-approval` transition. No manual fallback may waive source, artifact, blocker, action-authorization, or state-transition checks.

## Requirements and acceptance binding

This separate step advances the revision-2 closure allocations in REQ-ADOPTION, REQ-AUTHORITY, REQ-CONTINUITY-CLOSURE, REQ-REVIEW-PACKET, REQ-SEMANTIC-NAMING, REQ-SEQUENCE, REQ-SOURCE-PROGRAM, REQ-STATE-AUTHORIZATION, and REQ-VALIDATION. It adds no requirement and changes no accepted requirement, acceptance criterion, risk posture, sequencing rule, or user-review cadence.

Acceptance is bound to these observable contracts:

1. The approved SOURCE-002, revision-2 program, semantic digest, workspace, and accepted status remain exact.
2. All 755 atomic requirement IDs appear exactly once in the reconciliation with an allowed disposition, concrete evidence path, required owner/approval reference, and successful later-invalidation check.
3. INC-001 through INC-008 are accepted and each contributes exactly one current review-packet and handoff-addendum digest matching its approval record and current bytes.
4. AMEND-001 and AMEND-002 are both present and resolved; DEC-001 through DEC-008 are accounted for; every deferral is exactly owned or the deferral set remains empty.
5. Every accepted material finding has a valid final disposition, no fresh material finding remains unresolved, and no accepted evidence is silently invalidated by later work.
6. Fresh program-level integration, structural, package, pressure, resume, pilot, continuity, state, skill, and diff checks complete successfully after the latest contributing evidence.
7. Architecture, documentation, operations, and recovery are each reassessed against the final accepted tree and recorded without extending static evidence into production, provider, accessibility, or independent-review claims.
8. `continuity_closure.validate_closure_reconciliation` accepts the exact reconciliation, the deterministic closure packet renders byte-for-byte, and the current continuity bundle validates its brief, handoff, packet, and negative authority cases.
9. Manifest and status bind the exact reconciliation and packet digests; all blocker counts are zero; the accepted final increment remains `accepted`; the only program transition is `active -> awaiting-closure-approval`.
10. The packet requests explicit closure approval and stops. ISP-001 is not closed, and no later-action decision is requested or performed.

Any failure blocks closure readiness and reopens the smallest affected scope under a new exact approval/action boundary. Closure may not repair product or accepted evidence in place.

## File map

### Create during authorized reconciliation

- `implementation-programs/ISP-001/closure/reconciliation.json` — complete `implementation-closure-reconciliation/v1` ledger for all 755 atomic requirements, accepted artifact bindings, amendments, decisions, deferrals, findings, fresh command receipts, later-invalidation checks, and four program reassessments.
- `implementation-programs/ISP-001/closure/continuity-evidence.json` — current `implementation-continuity-evidence/v1` bundle binding the deterministic brief, handoff, resume context, closure-packet data, and required negative scenarios.
- `implementation-programs/ISP-001/closure/handoff.md` — deterministic navigation record for the accepted final increment and the closure-approval stop.
- `implementation-programs/ISP-001/closure/program-closure-packet.md` — deterministic human review packet bound to the reconciliation digest and requesting only explicit closure approval.

### Modify during authorized reconciliation

- `implementation-programs/ISP-001/manifest.json` — add only the final `closure_reconciliation`, `closure_continuity_evidence`, `closure_handoff`, and `closure_packet` logical roles plus their exact closure binding; retain all accepted current and latest-handoff roles.
- `implementation-programs/ISP-001/state/status.json` — add the exact zero-blocker closure binding and use accepted state authority to advance program state to `awaiting-closure-approval` while retaining INC-008 `accepted`.
- `implementation-programs/ISP-001/state/approvals.jsonl` — append only the explicit closure exact-plan approval record before reconciliation; do not append a program-closure approval.
- `implementation-programs/ISP-001/state/action-authorizations.jsonl` — append only the exact local closure-reconciliation/write/verification grant before reconciliation.

### Already created at this preparation gate

- `implementation-programs/ISP-001/closure/brief.md` — deterministic lean closure navigation.
- `implementation-programs/ISP-001/closure/preparation.md` — current repository, evidence, design, freshness, naming, and risk record.
- `implementation-programs/ISP-001/closure/exact-file-plan.md` — this frozen plan.
- `implementation-programs/ISP-001/increments/INC-008/handoff-addendum.md` — accepted final-increment seal; immutable during closure.

### Preserve without modification

- `implementation-programs/ISP-001/source/**` and `implementation-programs/ISP-001/program/**`, including accepted revision-2 traceability and the atomic semantic digest.
- `implementation-programs/ISP-001/increments/INC-001/**` through `implementation-programs/ISP-001/increments/INC-008/**`.
- `.codex-plugin/**`, `skills/**`, `tests/**`, repository-root source files, `.DS_Store` files, and every user-owned staged, modified, or untracked path outside the four governance modifications and four closure outputs.
- Git index, branch, HEAD, worktrees, remotes, local configuration, credentials, environment, provider state, and external systems.

### Interfaces and ownership

- `traceability.json.atomic_requirements` produces the ordered 755-ID expected set; closure preserves its bytes and writes final dispositions only to `reconciliation.json`.
- `APR-006`, `APR-011`, `APR-013`, `APR-015`, `APR-017`, `APR-019`, `APR-021`, and `APR-023` produce the accepted packet/addendum bindings consumed by reconciliation.
- `continuity_closure.closure_reconciliation_from_mapping` and `validate_closure_reconciliation` consume the reconciliation JSON and produce deterministic issue evidence only.
- `continuity_closure.closure_packet_from_mapping`, `validate_closure_packet`, and `render_closure_packet` consume the exact reconciliation digest and packet data and produce byte-exact Markdown.
- `continuity_closure.validate_continuity_bundle` consumes the closure brief, generated handoff, structured continuity evidence, reconciliation, and packet.
- `state_authority.validate_state_authority` and `apply_state_transition` consume a fresh repository observation, exact closure binding, exact action scope, and compare-and-swap status digest; they produce sequence 70 `awaiting-closure-approval` or fail without claiming closure.
- No new reusable interface, public API, command, test helper, fixture schema, or product owner is introduced.

## Semantic naming inventory

All new names are repository governance or accepted durable closure-domain names. No global word blacklist is introduced.

| Surface | Kind | Context | Intention | Origin | Planning-term basis | Basis owner | Compatibility class | Compatibility disposition |
|---|---|---|---|---|---|---|---|---|
| `implementation-programs/ISP-001/closure/reconciliation.json` | path | whole-program evidence | store the exact final requirement and artifact ledger | new | durable-domain | continuity closure contract | persisted | new accepted-schema instance; no migration |
| `implementation-programs/ISP-001/closure/continuity-evidence.json` | path | closure navigation validation | bind current brief, handoff, resume, packet, and negative cases | new | durable-domain | continuity closure contract | persisted | new accepted-schema instance; unsupported versions stop |
| `implementation-programs/ISP-001/closure/handoff.md` | path | closure approval navigation | point to readiness evidence without granting authority | new | durable-domain | continuity closure contract | repository-only | deterministic additive handoff; earlier handoffs preserved |
| `implementation-programs/ISP-001/closure/program-closure-packet.md` | path | human closure review | present reconciliation and request only closure approval | new | durable-domain | closure packet renderer | repository-only | deterministic additive packet; no later-action authority |
| `CLOSURE` | schema-or-identifier | revision-2 traceability and governance | identify the separate post-INC-008 closure allocation | existing | implementation-governance | ISP-001 revision-2 program | repository-only | preserve approved governance identifier |
| `implementation-closure-reconciliation/v1` | schema-or-identifier | final disposition ledger | reject incomplete, duplicate, stale, or unsupported reconciliation | existing | durable-domain | `continuity_closure.py` | persisted | reuse accepted version; no schema expansion |
| `implementation-continuity-evidence/v1` | schema-or-identifier | closure continuity bundle | validate exact rendered navigation and closure evidence | existing | durable-domain | `continuity_closure.py` | persisted | reuse accepted version; no schema expansion |
| `implementation-closure-packet/v1` | schema-or-identifier | closure packet data | bind packet fields to the reconciliation digest | existing | durable-domain | `continuity_closure.py` | persisted | reuse accepted version; no schema expansion |
| `Architecture, documentation, operations, and recovery` | heading | closure packet | expose the four required program reassessments | existing | durable-domain | closure packet renderer | repository-only | preserve accepted deterministic heading |
| `program-closure-approval` | schema-or-identifier | later human decision | name the only approval that may close a ready program | existing | durable-domain | state authority contract | persisted | not created by this plan execution; reserved for later explicit approval |

## Test-first slices and verification contracts

No implementation behavior changes, so fabricated RED/GREEN evidence would be misleading. Each task uses alternative verification against accepted validators and exact bytes. A material failure is a closure blocker, not an invitation to edit product or accepted evidence.

### Task 0: Bind exact closure-plan approval and local action authority

- [ ] Re-run the repository observation, source/program/semantic digests, accepted status sequence/digest, all eight acceptance records, and the manifest closure-preparation binding. Expected: exact match with this plan and zero conflict/operation/staging evidence.
- [ ] Require an explicit user statement approving this exact closure-plan digest. If the append-only logs remain unchanged, persist it as `APR-024`, type `exact-file-plan-approval`, bound to the current common ISP-001/INC-008 tuple plus `closure_step_id: CLOSURE`, closure brief/preparation/plan paths and SHA-256 digests, accepted status sequence 69/digest, and scope `approve the frozen separate closure-reconciliation exact-file plan only`.
- [ ] Persist `AUTH-027` only from the same explicit request when it separately authorizes local reconciliation, the exact four create paths, exact four modify paths, deterministic local verification, and the program-only transition to `awaiting-closure-approval`. Exclude product/test/source/traceability edits, dispatch, staging, commit, closure approval, program closure, later actions, egress, and consequential external state.
- [ ] Validate both append-only prefixes and unique identifiers. Expected: prior bytes preserved and exactly one matching approval/grant. If identifiers, bytes, scope, or digests drift, stop and prepare a renewed plan; do not renumber silently.

### Task 1: Freeze accepted program evidence and later-invalidation coverage

- [ ] Verify SOURCE-001, SOURCE-002, both program revisions, workspace, amendments, decisions, status, approvals, authorizations, and the eight accepted artifact pairs against current regular non-symlink bytes.
- [ ] Verify the accepted evidence chronology and later-invalidation state for each increment in order. INC-001 revision-1 evidence remains valid only under its explicit revision-2 preservation decision; INC-002 through INC-008 must retain exact revision-2 bindings.
- [ ] Extract the ordered 755 atomic requirement IDs from accepted traceability and assert unique exact coverage. Expected: source partition remains machine-complete and the semantic digest stays `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- [ ] Inventory every accepted material finding and disposition from the accepted packets/bundles. Expected: no unresolved material finding; reduced-assurance self-review labels remain truthful.

### Task 2: Build the complete reconciliation ledger

- [ ] Create one `requirement_dispositions` entry for each ordered atomic requirement. Use only `implemented`, `amended`, `deferred`, `rejected`, or `not-applicable`; cite concrete accepted evidence paths; set the exact owner and approval reference required by the disposition; and record `later_invalidation_checked: true` only after evidence inspection.
- [ ] Add accepted increment IDs `INC-001` through `INC-008` and exactly sixteen artifact bindings: `review-packet` and `handoff-addendum` for each accepted increment.
- [ ] Record approved and resolved amendment sets as exactly `AMEND-001` and `AMEND-002`; record decision IDs `DEC-001` through `DEC-008`; keep deferrals empty only if the ledger supports that result.
- [ ] Record one later-invalidation check per accepted increment, the complete material-finding outcome, the latest contributing evidence timestamp, and non-empty architecture, documentation, operations, and recovery assessments.
- [ ] Do not yet persist `reconciliation.json`. Validate the complete in-memory/mapping candidate with `closure_reconciliation_from_mapping` and record any issue as a blocker.

### Task 3: Run fresh whole-program verification

- [ ] Run the focused continuity/state tests, integrated pressure tests, complete 223-test suite, package validator, program-authority validator, accepted state-authority composition, accepted structured review bundles, skill validator, JSON/Markdown link checks through the package suite, `git diff --check`, and final porcelain-v2 observation.
- [ ] Complete every program command after the latest contributing acceptance/preparation evidence. Record the exact command, integer exit code, concise result, completion timestamp, and relevant inputs. Expected: every required result exits 0; duplicate, boolean, stale, or sensitive receipts are rejected.
- [ ] If any check fails or repository truth drifts, do not write reconciliation or packet artifacts. Record the exact blocker and reopen the smallest affected scope under separate authority.

### Task 4: Persist and validate closure evidence while the program remains active

- [ ] Add the fresh command receipts to the complete reconciliation candidate and create `closure/reconciliation.json` with one apply-patch write. Validate it with `validate_closure_reconciliation`; expected: zero issues and all 755 requirements exactly covered.
- [ ] Hash the reconciliation, construct `implementation-closure-packet/v1` data with `current_program_state: active`, and render `closure/program-closure-packet.md` only through `render_closure_packet`. Expected: exact byte equality and an explicit closure-approval request that contains no later-action authority.
- [ ] Construct the current `HandoffRecord` for INC-008 `accepted`, all eight accepted increments, accepted packet/addendum/status bindings, both amendments, residual risks, next action `Stop for explicit closure approval`, and exact first-read files. Render `closure/handoff.md` through `render_handoff` and require byte equality.
- [ ] Create `closure/continuity-evidence.json` with the exact structured closure brief, handoff, one-increment conversation stop, resume context, negative scenarios, and closure-packet data. Validate the full bundle with the exact brief, handoff, reconciliation, and packet paths.

### Task 5: Bind readiness and transition only to awaiting closure approval

- [ ] Add manifest logical roles for the exact reconciliation, continuity evidence, handoff, and closure packet. Add a closure binding containing their paths/digests, final increment `INC-008`, readiness validated true, and zero unresolved requirements, amendments, unowned deferrals, and material findings.
- [ ] Add the same exact closure binding to status while program state is still `active` and INC-008 remains `accepted`. Revalidate state authority against the current status digest and fresh Git observation.
- [ ] Use `apply_state_transition` with exact compare-and-swap input, target program state `awaiting-closure-approval`, target increment `INC-008` state `accepted`, transition event/action authorization `AUTH-027`, and action scope `transition ISP-001 from active to awaiting-closure-approval after validated reconciliation`.
- [ ] Verify the resulting sequence is 70, previous-state evidence binds sequence 69 and its exact pre-transition digest, program state is `awaiting-closure-approval`, increment state is still `accepted`, and no `program-closure-approval` record exists.

### Task 6: Final closure-readiness verification and mandatory stop

- [ ] Re-run state authority, program authority, closure continuity-bundle validation, package validation, the complete test suite, `git diff --check`, and porcelain-v2 status on the final tree because manifest/status inputs changed.
- [ ] Inspect the final exact file map. Expected: only the four planned closure outputs and four controlling governance files changed during reconciliation; no accepted evidence, source, traceability, product, test, skill, index, HEAD, branch, or external state changed.
- [ ] Stop with ISP-001 at `awaiting-closure-approval`. Present the closure packet for a later explicit human decision; do not record that approval, close the program, ask about a draft pull request, stage, commit, or perform a consequential action in the same execution.

## Commands and expected evidence

Run from `/Users/CoveMB/Code/CoveMB/implementation-plugin` with `PYTHONDONTWRITEBYTECODE=1` where Python imports or tests are involved.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_state_authority tests.test_integrated_pressure -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/continuity_closure.py validate-bundle implementation-programs/ISP-001/closure/continuity-evidence.json --brief implementation-programs/ISP-001/closure/brief.md --handoff implementation-programs/ISP-001/closure/handoff.md --reconciliation implementation-programs/ISP-001/closure/reconciliation.json --closure-packet implementation-programs/ISP-001/closure/program-closure-packet.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle implementation-programs/ISP-001/increments/INC-006/review-evidence.json --packet implementation-programs/ISP-001/increments/INC-006/review-packet.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle implementation-programs/ISP-001/increments/INC-007/review-evidence.json --packet implementation-programs/ISP-001/increments/INC-007/review-packet.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle implementation-programs/ISP-001/increments/INC-008/review-evidence.json --packet implementation-programs/ISP-001/increments/INC-008/review-packet.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 tests/integrated_pressure_support.py validate-evidence --evidence implementation-programs/ISP-001/increments/INC-008/integration-evidence.json --repository .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans
rtk git diff --check
rtk git status --porcelain=v2 --branch
```

State authority must also be invoked with a fresh exact `RepositoryObservation` from `repository_preparation.inspect_repository`, first against active/accepted sequence 69 and later against awaiting-closure-approval sequence 70. Expected evidence is `State authority validation passed`; a hand-copied stale path list is not acceptable.

Before the status transition, validate the reconciliation object directly with `closure_reconciliation_from_mapping` and `validate_closure_reconciliation`, validate the packet data with `validate_closure_packet`, and require `render_closure_packet(packet) == persisted_packet_bytes`. Expected: empty issue lists and byte equality. After the transition, the full bundle command above must exit 0.

Static and local checks do not prove independent reviewer identity, live Codex activation, deployment, provider behavior, production recovery, accessibility quality, hostile concurrency, or future model behavior. The closure packet must retain those limitations.

## Review scopes and specialist predicates

This closure step changes no product or reusable implementation. It performs an evidence-backed program reassessment, not a new implementation review cycle.

- Requirements/acceptance/authority: verify exact 755-item disposition coverage, accepted artifacts, amendments/decisions/deferrals/findings, zero blocker counts, and the separation of acceptance, closure approval, closure, and later actions.
- Architecture/boundaries/semantic naming: verify no new product owner, duplicate state machinery, traceability rewrite, public/persisted schema change, or planning-coordinate leakage; inspect every new governance surface in context.
- Test adequacy/evidence validity: verify freshness ordering, exact command receipts, accepted packet integrity, later-invalidation coverage, deterministic rendering, and honest limitations.
- Security/privacy, public API/compatibility, reliability/distributed state, persistent data/migrations, accessibility, platform/deployment, payments, performance, and provider/external state are not materially changed. Authority-sensitive status writes reuse accepted state controls; no specialist dispatch is authorized. If reconciliation reveals a material domain defect, closure blocks and the smallest affected scope is reopened.

Any controller reassessment is non-independent and must remain labeled reduced assurance. No reviewer or subagent is dispatched by this plan.

## Commit boundaries

No staging or commit is authorized. For human review only, the planned closure work has one coherent logical boundary:

1. `docs: reconcile accepted implementation program` — exact closure plan authorization records, complete reconciliation, continuity evidence, handoff, deterministic closure packet, manifest/status closure bindings, transition to awaiting closure approval, and fresh verification receipts.

This label grants no commit authority. A later commit requires a separate exact `create-local-commit` authorization after closure approval or another explicit user decision.

## Rollback and recovery

- Source/product/tests/package: not touched. Any observed change is a blocker, not planned work.
- Governance files: use accepted compare-and-swap/append-only mechanisms and apply-patch creation. Partial new closure files remain inert evidence; do not delete, reset, clean, stash, or overwrite them. Revalidate all digests before retry.
- Status: `apply_state_transition` must preserve the exact prior digest and sequence. A failed replacement leaves the prior bytes controlling; a successful transition is not rolled back without a separately authorized legal transition.
- Persistent application data, deployment, provider state, and external systems: not touched. Git restoration is not represented as recovery for any external domain.
- If closure readiness fails, preserve the evidence, keep the program `active`, name the smallest affected scope, and seek a new exact plan/authorization. Do not weaken a disposition or blocker to force closure.

## Approval required to execute

Stop now. Execution requires explicit approval of the exact SHA-256 of this closure plan and a separate exact action authorization matching the unchanged program/source/semantic/workspace/status/brief/preparation/plan tuple and the exact create/modify maps above.

That approval may authorize reconciliation only through `awaiting-closure-approval`. It must not authorize or be treated as program-closure approval, a closure-approval response, a commit, a draft-pull-request decision, or any consequential external action. Any material drift requires a refreshed preparation and plan before execution.
