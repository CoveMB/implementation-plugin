# Specialist Review Persistence and Recovery Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` for sequential implementation after approval. Steps use checkboxes. Use at most one bounded final reviewer for the coherent implementation unless it finds a material defect. This planning document authorizes no implementation, installation, Git mutation, or change to the affected Spotify program.

**Goal:** Make every required specialist review usable throughout the supported review lifecycle, and provide an explicitly approved, evidence-preserving recovery route for the reported blocked task.

**Architecture:** Reuse the canonical risk-to-scope registry and existing review transactions. Extend exact-plan parsing and report loading without changing valid three-report behavior. Recovery of an already-bound, underallocated plan is a separate, narrowly typed allocation supplement; it must never silently rewrite the original plan, baseline, approvals, or retained reports.

**Tech Stack:** Existing Python standard-library modules, `unittest`, Markdown, canonical JSON and SHA-256 bindings, existing append/adopt and status-last persistence helpers. No dependencies or Python-version change.

**Spec:** The requested repair and the design contract in this document, constrained by `skills/implementing-staged-plans/references/review-coordination.md`, `references/repository-preparation.md`, and `references/state-authorization.md`. This document proposes a limited exception to the existing prohibition on post-start allocation changes; that exception requires an explicit design decision before implementation.

**Status:** Planning only. Investigation began at local `main` `dd9fe7bff8021d55bc63dac06b1756d0e7996f9d`; another task advanced it to `1453318eb9cd40d79326398d1014ea1070a8f6ad` during planning. The intervening compact-summary change does not change the failing report parser, loader, or blocked-recovery owner. Preserve that commit and its documentation. Remote refs were not refreshed. The existing-task recovery scope question is pending; the recommended full plan includes it. Independent review on 2026-09-24 retained one material finding: supplement authority must survive a second blocking episode. This revision incorporates that correction and its regression coverage; it has been self-checked, not independently re-reviewed.

## Decision and scope

The recommended scope includes both the ordinary writer repair and safe recovery of the existing blocked task. The alternative is to ship only the ordinary repair and leave that task blocked. A question asking the user to choose these scopes is pending. Do not treat silence or approval of the ordinary writer repair as approval of the new recovery contract.

Implement the shared repair first, then the recovery contract, then downstream lifecycle verification. They form one coherent delivery when recovery is selected. The current task must not be advertised as recoverable until the complete recovery round trip passes.

The initial allocation-recovery case is deliberately narrow: manifest/setup programs already supported by blocked recovery, execution-baseline v1, blocked from `implementing`, no persisted review-preparation/remediation/diff-acceptance prefix, and missing or incomplete report allocation within an already approved review path class. The reported Spotify task fits this case. Once granted, the same supplement must survive subsequent supported blocks from `implementing` or `reviewing` and their ordinary resumes; those resumes retain existing authority and allocate nothing new. Do not add general program revision, supersession, cancellation, Delete-family blocked recovery, or arbitrary re-planning. Unsupported cases remain unchanged and stop before writes.

## Verified evidence

- Task: `codex://threads/01a0d40f-79c0-7a61-b0ac-ec5fd7922607`, titled **Prepare Spotify program start**.
- `program_review.py:_raw_report_paths` recognizes only three literal scope names. `_load_current_report_inputs` independently loops over the same three names.
- `review_coordination.py:select_review_scopes` correctly selects the base scopes plus every materially touched risk. The reported case selects security/privacy, compatibility, reliability, performance, and provider specialists.
- An in-memory reproduction supplied all eight declarations; the parser returned three. Loading the preserved reports produced five `selected scope ... must have exactly one initial report` errors. Both affected source files match the installed `0.1.3` files.
- The production writer fixture in `tests/program_bootstrap_support.py:raw_review_report` marks every risk untouched. Existing validator-level specialist tests do not exercise specialist reports through the production writer.
- The Spotify program is blocked at sequence 5, from `implementing`. Its exact plan and execution-baseline v1 allocate only the three base report files. The manifest already permits risk-triggered specialist JSON reports in the increment's review directory and Preserve retention by later increments.
- `blocked_recovery.py` requires the exact original plan, baseline, and seven evidence hashes. Ordinary recovery restores the original state; it grants no new report paths. `program_activation.py:_build_plan_candidate` does not permit post-start plan replacement. The skill explicitly leaves program revision unsupported.
- `block_current_program` removes `block_resolution_binding` and replaces `blocked_context` on a later block; `test_second_blocking_episode_replaces_current_resolution_binding` protects that behavior. Supplement authority therefore cannot depend solely on the latest block's resolution binding. `_execution_contract` and blocked evidence/workspace validation must recognize the retained effective allocation.
- All seven blocked evidence digests matched during diagnosis. The three preserved reports have empty `reconciled_at` values. They are incomplete historical evidence, not completed reviews that can simply be relabeled.

## Global constraints

- Preserve the original exact plan, execution baseline, source/program bindings, approval and action history, four product files, and three retained raw report files during allocation recovery.
- Keep required risk predicates truthful. Do not mark a touched domain untouched, merge specialist findings into another scope, invent reviewer expertise, or infer external verification from local tests.
- A single bounded independent reviewer may provide separately identified scope assessments. No new reviewer-per-scope requirement is introduced. Independence and reduced assurance remain explicit.
- Reuse `REQUIRED_REVIEW_SCOPES`, `RISK_REVIEW_SCOPES`, and `select_review_scopes`; do not copy their registry into production code.
- Preserve valid legacy three-report output and persisted v1/v2 review families. New recovery semantics are explicitly versioned and opt-in; old records remain byte-identical.
- Keep no-overwrite creation, exact-byte adoption, append-only authority records, fresh observations, and status-last compare-and-swap writes. Reuse existing owners rather than inventing another transaction framework.
- Do not add a directory-wide dirty-path exemption, caller-selected lifecycle output paths, arbitrary scope names, or general permission to extend product scope.
- Preserve the pre-existing untracked `2026-09-16-successor-operation-envelope-repair.md` and the concurrently committed `2026-09-24-compact-program-start-summary.md` and its implementation.
- No cache patching, dependency changes, Spotify calls, credentials, private-data mutation, commit, push, PR, merge, installation, or live program recovery follows from this planning request.
- Do not run the full suite while merely planning. During implementation, observe focused RED/GREEN, run the full relevant suite once on the coherent tree, and repeat only for changed inputs or new concerns.

## Review focus

1. A valid specialist report is actually loaded, bound, rendered, and retained by production transactions, including remediation; parser-only success is insufficient.
2. A missing, unknown, duplicate, unsafe, stale, or replayed report cannot change status or leave accepted partial output.
3. Recovery cannot use a new report allocation to change application files, conceal old evidence, expand the manifest envelope, or acquire general write authority.
4. A lost response at any persistence boundary either adopts the exact prefix or preserves divergent bytes and stops, including discovery from a fresh process and a second block after report files exist.
5. Recovered review files survive acceptance, successor preparation, and terminal closure; reaching `awaiting-diff-approval` alone is insufficient.

## Design contract

### Canonical declarations and selection

Add `parse_raw_review_report_paths(markdown: str) -> dict[str, str]` to `review_coordination.py`, which already owns the scope registry and has no dependency on the review writer. Keep `program_review._raw_report_paths` as a thin forwarding wrapper if necessary to avoid gratuitous breakage of existing internal callers.

Read exactly the `Review scopes and specialist predicates` section. Require the three base declarations once, in their existing order. Accept specialist declarations only from `RISK_REVIEW_SCOPES.values()`. Reject duplicate scopes, duplicate normalized paths, unknown scope/path declarations, malformed declarations beginning with a recognized scope, absolute paths, escapes, dot segments, and backslashes. Ordinary explanatory prose is not a report declaration.

Return deterministic order: base scopes followed by specialists in canonical registry order. Do not require specialist lines to have been authored in that order. Preserve the existing three-entry result exactly for a valid legacy plan.

At exact-plan preparation, use this parser to require each declared report path to have an exact Create allocation and pass existing ownership/envelope checks. Assess anticipated material risks before authoring that map; do not allocate every possible specialist as a workaround. This preflight checks declarations and ownership, not the semantics of a future diff.

At review, load and validate the architecture report, derive actual selected scopes through `select_review_scopes`, and require equality between selected and declared scopes. Missing and excess declarations produce explicit diagnostics. Then load every selected report in canonical order, reusing the architecture value already loaded. Apply current schema, program/revision/increment, scope, identity, finding, assurance, timestamp, and digest checks to specialists exactly as to base reports.

Review and remediation use this same loader. Existing report/finding arrays and raw digest bindings already support multiple scopes; retain their formats. No blanket specialist exemption belongs in bundle validation.

### Recovery allocation supplement — proposed, requires the pending decision

Use the existing blocked-recovery transaction and existing manifest-owned action/resolution ledgers. Introduce a versioned review-allocation supplement inside a new recovery record family, rather than editing the original plan or writing an untracked authorization sidecar. Keep current v1 recovery readers and exact retry behavior intact.

The supplement carries:

| Field | Required binding |
| --- | --- |
| Identity | Program/revision/increment, source/program/semantic digests, workspace/branch/base/head, current grant |
| Original contract | Original exact-plan digest, baseline digest, blocked context/status digest and sequence |
| Preservation | Original blocked evidence inventory, raw report paths/digests, and current non-report product fingerprint |
| Scope | Canonically selected scopes and architecture-risk evidence digest |
| Exact additions | Each absent regular-file JSON report path, Create disposition, absent baseline, and matching approved envelope allocation |
| Report selection | One active report path per selected scope, plus explicitly retained prior paths; no implicit directory discovery |
| Authority | Exact displayed recovery command, direct user decision, action record, and supplement digest |

Allocate a fresh report set beneath a deterministic child directory of the already approved increment review path class, using existing scope filenames such as `requirements.json` and `specialist-provider.json`. Derive the child identity from the block identity; include the exact paths in the approval preview. This permits new completed base reports while preserving the original three incomplete files. Reject an occupied destination or an envelope that does not permit the exact additions and later retention.

Use a new recovery candidate/command/record/binding version for this case. Keep the original blocked context unchanged. Explicitly distinguish permission to complete these exact report files from `resume-blocked-program`; ordinary resume authority must not gain that permission. A separate increment-bound `review_allocation_binding` in status must reference the exact originating resolution/supplement record and authorizing action, including their identifiers and digests. `block_resolution_binding` remains specific to the latest blocking episode. An older plugin must reject the new recovery family rather than ignore its authority requirements.

Build every candidate record in memory. Verify the unchanged blocked state and original bytes, all new slots absent, selected scopes, exclusions, and successor Preserve coverage before the first ledger write. Present this concrete recovery preview and obtain its own direct decision. Persist action, resolution/supplement, then restored `implementing` status, using the current exact-prefix retry pattern. Do not write reports as part of granting their allocation. Do not mark the review or increment complete. Record concrete evidence for each original recovery criterion; the new record must distinguish satisfied resume prerequisites from review work that remains pending. Do not mechanically set every criterion to true. If an original criterion explicitly requires completed artifacts before any resume, this narrow variant is inapplicable and must stop for a separate design decision.

Add one canonical reader/projection in `repository_preparation.py` for the effective execution contract. When no supplement has been granted for the current increment, return the existing baseline/map unchanged. A missing, malformed, or stale binding to an existing grant fails closed; it must not silently fall back to the original baseline. With a validated supplement, extend only the exact Create report paths and absent path baselines and select the new report mapping. The original persisted baseline and exact-plan digest remain unchanged and continue to be checked. The supplement is a separately authorized extension, not an alternative interpretation of those original bytes.

Every live execution/review/acceptance/continuation reader and every blocked-state contract, evidence, and workspace reader must use that projection. This includes `_execution_contract`, `_build_blocked_context`, `validate_blocked_context`, and `blocked_workspace_paths`. It must validate the supplement's provenance before accepting additional dirty paths or new report paths as blocked evidence. Do not scatter `if recovery` exemptions among callers. Use local imports where the current module graph requires them; avoid a cycle between repository preparation, state authority, activation, and recovery.

#### Supplement lifetime across blocking episodes

Retain `review_allocation_binding` unchanged when `block_current_program` clears the episode-specific resolution binding and creates a new blocked context. Persist the complete original blocked context, its digest, the supplement, and its authorizing action reference in the immutable originating resolution record, so validation does not depend on the later `blocked_context` still describing the first episode. The new current blocked context binds the existing increment supplement as well as its own reason, evidence, and prior state. Use an explicitly versioned context for supplemented episodes; unsupplemented v1 context bytes and behavior remain unchanged.

Before entering another block, validate the supplement and current workspace against the effective contract. Retain the existing state restrictions: `implementing` and `reviewing` may block; `remediating` still uses its own supported return path. Added reports may be included in the new block's evidence inventory with their actual hashes. Original retained reports remain protected by their preservation bindings. Missing or mismatched supplement provenance must stop before the status write rather than publish a blocked state that discovery cannot read.

An ordinary resolution of this later block must preserve the same `review_allocation_binding` and restore only that episode's recorded prior state. Its prompt and versioned record bind the retained supplement digest, but grant only ordinary resume authority: no second allocation action, new report directory, extra path, or reuse of the first allocation approval. Retrying the original allocation after a later block must reject as stale. Fresh-process discovery and exact-prefix recovery validate the originating allocation record independently of the latest resolution record. The original absent-slot checks apply when granting the supplement, not when validating already authorized report files during a later block.

Keep the original three report bytes immutable. Complete new report inputs with truthful persistence/reconciliation times, current risk evidence, and actual scope assessments. Empty old reconciliation timestamps must not be replaced in place or backdated. Old test results remain historical; obtain final verification after the new review/reconciliation under the existing freshness contract. Do not claim the allocator itself supplies those reviews or satisfies their quality requirements.

Recovery returns to `implementing` with the original application authority unchanged and only the exact extra report writes separately authorized. The effective product delta includes the newly allocated report files; final review refreezes and binds it. The original application fingerprint is an allocation-time preservation check, not a permanent prohibition on a later independently justified, normally authorized material-defect repair.

On acceptance and rollover, retain the supplement's provenance and include its report paths in the accepted/inherited inventory. Remove `review_allocation_binding` and its active report selection from the successor's current status while retaining the predecessor's exact binding in rollover history. A successor must explicitly Preserve retained reports through its own normal exact map. Existing envelope coverage permits this in the reported program; programs without that coverage stop. Terminal closure must reconstruct the same effective contract.

Downgrade after adopting a new supplement is not a recovery procedure. Retain evidence and stop on unsupported schemas. Do not delete records, roll back sequence numbers, or install an older plugin and claim that the new state is supported.

## Task 1: Make ordinary specialist review work through the production writer

**Modify:**

- `skills/implementing-staged-plans/scripts/review_coordination.py` — canonical declaration parser.
- `skills/implementing-staged-plans/scripts/program_review.py` — all selected report inputs through existing review/remediation transactions.
- `skills/implementing-staged-plans/scripts/program_activation.py` — declaration/allocation preflight before exact-plan writes.
- `tests/program_bootstrap_support.py` — optional specialist risk/report inputs; existing defaults and frozen fixtures unchanged.
- `tests/test_review_coordination.py`, `tests/test_program_review.py`, `tests/test_program_activation.py` — behavior and persistence-boundary regressions.
- `skills/implementing-staged-plans/references/review-coordination.md`, `references/repository-preparation.md` — remove the three-report writer limitation; explain anticipated allocation and actual-diff selection.

**Interfaces:** Preserve `_load_current_report_inputs` and public transaction signatures. Introduce only the shared declaration parser above. Fixture helpers receive an optional immutable collection of touched canonical predicate names, defaulting to empty; use the production registry when constructing those optional entries.

- [ ] Add a minimal regression that demonstrates specialist declarations are lost by the current parser. Example assertion using existing imports in `tests/test_program_review.py`:

```python
scopes = ("requirements", "architecture", "test-evidence", "specialist-provider")
markdown = "## Review scopes and specialist predicates\n" + "\n".join(
    f"- {scope}: `reviews/{scope}.json`" for scope in scopes
)
self.assertEqual(tuple(REVIEW._raw_report_paths(markdown)), scopes)
```

- [ ] Add a production-flow regression using `BootstrapFixture`, `activated_program`, `prepare_exact_plan`, `advance_execution_state`, and `persist_review_preparation`. Declare the provider path in the exact map before materialization; mark its risk touched; persist its distinct raw report; assert the final evidence contains its exact scope/path/hash and discovery reaches the diff gate. Snapshot program bytes on failure. Do not patch selection or validators to force success.
- [ ] Run focused RED with `rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_review -k specialist -v`. Expected failure is the omitted specialist or selected-scope error, not fixture setup/import failure.
- [ ] Implement the shared parser, early allocation check, and architecture-first selected-scope loader. The core selection logic is:

```python
predicates = tuple(ReviewRiskPredicate(**item) for item in architecture["risk_predicates"])
selected = select_review_scopes(predicates)
missing = set(selected) - set(raw_paths)
unexpected = set(raw_paths) - set(selected)
if missing or unexpected:
    raise ValueError("review declarations differ from selected risk scopes")
for scope in selected:
    # Reuse architecture and apply the existing per-report binding checks.
    relative = raw_paths[scope]
```

- [ ] Add a table covering each of the nine specialist predicates, the reported five-risk combination, all nine together, and no touched risks. Exercise report/bundle construction for the table; use representative full production transactions for baseline v1 and Delete-capable review v2.
- [ ] Add rejection cases: unknown/duplicate scope; malformed declaration; alias/duplicate path; missing/excess specialist; undeclared Create path; missing file; symlinked file/parent; escape; wrong scope/program/revision/increment; stale final verification; duplicate report ID; material open specialist finding. Every rejected production call must leave records/status unchanged.
- [ ] Use the existing managed-path resolver to reject unsafe path components before report loading. Keep the scope to this report input boundary; do not redesign generic filesystem access.
- [ ] Generalize one existing material-finding round-trip test to a specialist scope. Assert preserved initial report metadata, matching raw bindings, affected follow-up scope/finding IDs, and fresh final evidence. Verify unchanged no-specialist fixtures produce the same bytes and that v1/v2 families do not cross.
- [ ] Run focused GREEN once after the coherent task:

```bash
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination tests.test_program_review tests.test_program_activation -v
```

## Task 2: Add the narrowly authorized recovery supplement

**Prerequisite:** The user selects existing-task recovery and approves the proposed design contract. Do not start this task from a generic approval of Task 1.

**Modify:**

- `skills/implementing-staged-plans/scripts/blocked_recovery.py` — versioned candidate/context, exact prompt, separate report-allocation action, retained increment binding across later blocks, prefix persistence and provenance validation.
- `skills/implementing-staged-plans/scripts/repository_preparation.py` — canonical effective-contract projection and strict exact report additions.
- `skills/implementing-staged-plans/scripts/state_authority.py` — recognize only the typed supplement authority, validate history, and use the effective contract.
- `skills/implementing-staged-plans/scripts/program_activation.py` — effective contract at execution transitions and reuse of the existing envelope matcher.
- `skills/implementing-staged-plans/scripts/program_review.py` — active recovery report selection plus effective ownership checks.
- `skills/implementing-staged-plans/scripts/program_discovery.py` — recovery routing through existing inspection hooks; change only if needed to surface the new typed disposition.
- `tests/test_blocked_recovery.py`, `tests/test_repository_preparation.py`, `tests/test_state_authority.py`, `tests/test_program_discovery.py`, `tests/program_bootstrap_support.py`.
- `skills/implementing-staged-plans/SKILL.md`, `references/state-authorization.md`, `references/program-discovery.md`, `references/repository-preparation.md`, `references/review-coordination.md` — one precise recovery exception and references to its canonical contract.

**Interfaces:** Extend `build_block_resolution_candidate`, `persist_blocked_resolution`, `block_current_program`, and existing blocked contract/context/inspection/history readers to dispatch explicitly by recovery record family. The old v1 argument/value/output behavior remains exact. Add `validated_review_allocation_supplement(program_root: Path, status: Mapping[str, object]) -> Mapping[str, object] | None` in `blocked_recovery.py` as the shared read-only provenance owner. It follows `review_allocation_binding` to the originating immutable records, independently of the current episode's resolution binding, and returns `None` only when the current increment has no granted supplement. It validates records directly without calling the full state-authority validator or an execution-baseline reader, preventing recursive validation. Add `effective_execution_baseline(program_root: Path, status: Mapping[str, object], baseline: ExecutionBaseline) -> ExecutionBaseline` in repository preparation, consuming that validated value. Blocked readers and the review writer consume the same validated value. Its v1-only boundary is explicit; reject a supplement on baseline v2 before writes.

- [ ] Build a synthetic regression matching the real state shape: existing product delta, only three allocated base reports, five touched risks, empty old reconciliation timestamps, blocked from implementing, and a manifest-approved review directory with successor retention. Never copy private Spotify source into a fixture.
- [ ] Before implementation, assert that an ordinary v1 resume adds no report authority and that the new candidate cannot be accepted by the current code. Record the intended RED reason.
- [ ] Implement the new typed candidate fields and validator from the design table. Preserve the old block context verbatim. Allow only new absent JSON report files in the approved current-increment path class; keep original file dispositions and user-work baselines unchanged. Check later retention using the canonical operation-envelope rules, extracting a small shared matcher only if required by two actual callers.
- [ ] Implement the effective baseline using `dataclasses.replace` with the exact added Create paths and `ExecutionPathBaseline(path, "Create", None)` entries. Keep the original plan digest and baseline identity; the independently validated supplement supplies the additional authority. Return the original value when no supplement is present.

```python
# additions is the tuple of exact paths from the validated supplement.
return replace(
    baseline,
    file_map=replace(
        baseline.file_map,
        create=tuple(sorted((*baseline.file_map.create, *additions))),
    ),
    path_baselines=(
        *baseline.path_baselines,
        *(ExecutionPathBaseline(path, "Create", None) for path in additions),
    ),
)
```

- [ ] Implement all-candidate preflight, exact user prompt, action append/adoption, supplement/resolution append/adoption, and restored-status CAS. Reuse existing failure hooks and helpers. No report or application file is written by this transaction.
- [ ] Preserve the increment-bound supplement across `block_current_program` and subsequent ordinary resolutions. Use the effective contract in blocked context construction, evidence validation, workspace validation, and path discovery. Keep the legacy second-block behavior of replacing the episode context and clearing `block_resolution_binding`; preserve the distinct `review_allocation_binding` and bind it in the new versioned context before status persistence.
- [ ] Assert original plan, baseline, all prior ledger prefixes, old reports, and application files remain byte-identical. New report paths are still absent immediately after recovery authorization. A changed plan, changed evidence, stale workspace, occupied path, missing envelope/retention coverage, arbitrary executable path, unselected scope, unsupported baseline family, or replayed approval fails before the first write.
- [ ] Inject interruption after action, resolution, and status persistence. A fresh process must identify the exact prefix; retries create no duplicate record and restore only implementing. For each prefix, change one bound byte and verify recovery stops without overwrite.
- [ ] Test both ordinary legacy recovery and supplemented recovery side by side. Unknown versions and mismatched command/record/binding families fail closed. Do not update frozen legacy fixtures to make the new tests pass.
- [ ] Add `test_supplement_survives_second_block_and_ordinary_resume` to `tests/test_blocked_recovery.py`. Through production APIs, grant the supplement, create the authorized reports, and block again for an unrelated verification failure. Cover both an `implementing` branch and a `reviewing` branch. Include a new report in the second block's evidence. Fresh-process discovery must accept the effective map; the ordinary resume restores the second episode's exact prior state while retaining the identical supplement binding. Assert one allocation grant, unchanged originating ledger records and original report hashes, no new paths, and no extra allocation authority in the later resume record.
- [ ] Extend that regression with lost-response retry at the later resume's action, resolution, and status boundaries. Remove or swap the retained binding, change the originating supplement/action, alter a bound report, and replay the first allocation prompt against the second block. Each invalid transition must preserve the pre-call ledger/status bytes. Keep `test_second_blocking_episode_replaces_current_resolution_binding` unchanged for unsupplemented programs.
- [ ] Complete fresh report inputs under the synthetic supplement, then reach `reviewing` and `awaiting-diff-approval` through normal writers. Assert all eight active scopes exist and all three original reports remain preserved. No fabricated timestamps or specialist identities may be introduced.
- [ ] Run focused GREEN:

```bash
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_blocked_recovery tests.test_repository_preparation tests.test_state_authority tests.test_program_discovery tests.test_program_review -v
```

## Task 3: Prove persistence, downstream continuity, and package compatibility

**Modify:**

- `skills/implementing-staged-plans/scripts/program_continuation.py` — effective live accepted delta.
- `skills/implementing-staged-plans/scripts/program_rollover.py` — retain supplement provenance and report paths; clear active selection for the successor.
- `skills/implementing-staged-plans/scripts/program_closure.py` — effective v1 contract during terminal validation.
- `tests/test_program_rollover.py`, `tests/test_program_closure.py`, `tests/test_diff_disposition.py`, `tests/test_program_review.py`, `tests/test_blocked_recovery.py` — real production call paths and interruption coverage.
- `docs/workflows.md` — report completion and recovery user flow, linked to canonical references.

**Interfaces:** Reuse the effective-contract reader from Task 2 at actual baseline consumers. `diff_disposition.py` should keep deriving acceptance through existing review/continuation owners; add production code there only if the new regression proves a direct unconverted read. Do not duplicate projection logic.

- [ ] Add one full ordinary specialist scenario and one supplemented-recovery scenario. Each goes through review persistence, fresh-process discovery, exact diff acceptance, successor rollover, successor exact-plan preparation, and preservation of predecessor review files. Use exact existing public transaction APIs and their prompt builders; no direct status edits.
- [ ] Add a terminal scenario using a final v1 increment that reaches valid closure with specialist reports. Preserve the existing unsupported Delete-family closure boundary; the ordinary specialist review test for v2 remains required.
- [ ] Verify the supplemented increment's accepted delta and inherited inventory include the fresh and retained reports. The successor retains the historical supplement binding but has no active report-write extension for its predecessor. Tampering with retained reports or supplement records must fail during discovery/continuation.
- [ ] Repeat existing review evidence/packet/verified/awaiting-diff interruption and divergent-prefix tests with specialists. Verify exact-byte output adoption, deterministic report order, and unchanged previous authority records.
- [ ] Confirm declaration validation runs before plan/status persistence; test both new first-increment and successor plan entry. Do not rely solely on prose telling the agent to allocate specialists.
- [ ] Make one focused ownership/DRY pass: all changed lines serve these contracts; no duplicated scope registry, alternate approval engine, broad migration framework, or unrelated review remediation cleanup remains.
- [ ] Run the coherent full suite and package checks once:

```bash
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk git diff --check
```

- [ ] Use one bounded independent final reviewer after implementation, scoped to the actual changed files, persisted compatibility, no-write failure guarantees, and the recovery/rollover round trip. Supply the plan and factual test evidence; withhold the implementer's correctness conclusion. Re-review only if a material defect requires it.

## Deployment and live recovery runbook

These are later actions requiring their own scope and authority. Record local implementation success separately from installation and successful recovery of the real task.

1. Preserve a verified recovery inventory for the real task: Git identity/status, source/manifest/program/plan/baseline/status digests, prior ledger bytes, the four product files, three original reports, and protected pre-existing work. Do not stash, reset, delete staging copies, or overwrite the blocked program.
2. Publish/install only through the normal approved plugin delivery route. Use a clean selected source snapshot. Verify installed file parity using `validate_package.py SOURCE_ROOT --compare-installed INSTALLED_ROOT`; resolve these paths from the actual installation rather than assuming the version directory changed. Verify target-workspace skill discovery separately from byte parity.
3. Read the real program using the repaired installed plugin. Recheck the sequence and all original bindings; sequence 5 is a diagnostic snapshot, not a future authorization.
4. Build the narrow recovery preview. Show the exact fresh report paths, selected scopes, retained files, unchanged product fingerprint, and actions granted. Obtain the exact direct decision required by the new typed transaction. Ordinary “resume” must not authorize allocation changes.
5. Persist the allocation/resolution and restore implementing. Complete new review evidence truthfully; obtain any actually missing specialist assessment with accurately stated assurance. Preserve original reports and never turn their empty timestamps into invented past events.
6. Run applicable fresh final verification after review/reconciliation. Prior recorded 49/618 test results are historical observations and must not be represented as new post-recovery checks. Avoid rerunning unrelated expensive or external evaluations.
7. Reach the normal `awaiting-diff-approval` packet through the typed writer, verify discovery, and stop for the user's diff decision. Do not accept, commit, start a successor, or call Spotify as part of unblocking.
8. If interrupted, use exact-prefix recovery. If anything diverges, preserve all bytes and report the specific conflict. Do not claim that uninstalling/downgrading the plugin reverts the program's newly versioned records.

## Completion criteria

- All canonical specialist scopes work through the production writer; missing or contradictory reports cannot advance status.
- Legacy three-report fixtures, historical records, and ordinary v1 recovery retain their behavior and bytes.
- Valid v2 review/remediation continues to bind the typed Delete result correctly; unsupported recovery families still reject before writes.
- The approved recovery variant preserves original code/evidence and grants only exact report additions inside existing program authority.
- A subsequent supported block and ordinary resume preserve the original supplement authority, recognize its report paths, and restore only the later episode's prior state; stale or missing provenance fails before writes.
- Every selected interruption boundary has an idempotent exact retry and a no-overwrite divergent retry test.
- Acceptance, successor preparation, and final v1 closure retain specialist reports and recovery provenance.
- The installed repair and the real blocked task's recovery are reported separately; only successful real recovery closes the user-visible incident.

## Current-source research and limits

Live official documentation was checked on 2026-09-24. Python's [unittest documentation](https://docs.python.org/3.11/library/unittest.html#distinguishing-test-iterations-using-subtests) supports subtests for the scope matrix; give each stateful case its own fixture and cleanup. The [os documentation](https://docs.python.org/3.11/library/os.html#os.replace) describes atomic successful replacement and filesystem/platform limitations; retain the existing transaction preflight and durability helpers rather than treating a rename as an entire multi-file transaction.

These sources support test and filesystem mechanics. Repository code is the authority for plugin schemas, gates, and compatibility. Static tests do not establish reviewer expertise, live model behavior, Spotify behavior, or successful host installation. The most consequential risk is inconsistent effective-contract handling by a downstream reader; the production continuation/closure tests are release requirements, not optional follow-up work.
