# Combined Program Start Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for native implementation, or superpowers:subagent-driven-development only if the user selects delegation. Steps use checkbox syntax. This plan is not authorization to implement.

**Goal:** Replace separate initial setup approval and first-start interactions with a short summary and one explicit start decision, preserving the underlying authority checks.

**Architecture:** Add a versioned combined-decision contract in the existing setup owner. Compose the existing setup and first-start transactions with durable consent and exact-prefix recovery; retain their separate receipts and status sequence. Preserve historical contracts through explicit schema dispatch.

**Tech Stack:** Python standard library, unittest, existing Markdown skill/reference documents, RTK-wrapped commands. No new dependencies.

**Spec:** [Combined program setup and first start](../specs/2026-09-22-combined-program-start-design.md).

**Status:** Independently reviewed and ready for implementation. The user selected new proposals only and starting in either the same or a fresh task. The summary is output only; no recap or replacement summary file is created. Implementation remains a separate request.

## Reader summary

The intended user flow is: generate proposal → read a short summary printed in the conversation → say **Start the first increment** → begin the first increment under the existing approval mode and gates. No recap file is created. The long machine-readable records remain supporting evidence. A fresh task redisplays the current summary before its start reply.

Five implementation increments follow: summary and consent, durable authority readers, combined activation and recovery, discovery and user instructions, then cross-lifecycle verification. Implement sequentially because they share authority contracts. No product code has been changed while preparing this plan.

## Global Constraints

- Retain the existing manifest-v3 and status-v3 state sequence: proposal at 0, active/awaiting-first-increment at 1, active/preparing at 2.
- Keep setup/envelope v1 and v2 operation semantics distinct.
- Keep legacy recap renderers, checkpoints, setup-only adapters, and first-start handoff validation byte-compatible for persisted history.
- Require the actual presented checkpoint as an adapter argument.
- New proposals declare program_start_contract equal to combined-start/v1 before publication; existing unmarked proposals retain their historical route.
- Neither generation nor publication saves a setup recap or replacement summary file. Persist summary identity metadata, never the rendered summary body.
- Allow starting in the same or a fresh task after current summary presentation and revalidation.
- Discovery only reports the next legal route and never resumes writes itself.
- Only a gate explicitly permitting setup reuse may reuse the setup component, and its meaning must be visible in the summary.
- No real Spotify proposal, source plan, ledger, cache, credential, or provider data is changed while implementing or testing the plugin.
- No automatic installation, publication, Git action, or package-version bump is included.
- Preserve the pre-existing untracked docs/superpowers/plans/2026-09-16-successor-operation-envelope-repair.md and all other user work.

## Review Focus

1. An old setup-only “yes” must never become combined consent: increments 1–3 test strict schema separation and unchanged legacy behavior.
2. A concise summary must expose destructive targets and meaningful limits without inventing broader permissions: increment 1 tests content and includes a human reading check.
3. A crash between sequence 0, 1, and 2 must not lose or duplicate start authority: increment 3 interrupts every persisted prefix; increment 4 rediscovers it in a fresh process.
4. Changed source, brief, workspace, protected work, or first-increment identity must stop before a new authority write: increments 1 and 3 test preflight and retry drift.
5. A new first-start record must remain valid through later review, successor, and closure readers without bypassing their gates: increment 5 exercises both operation families and approval modes.

## Baseline and canonical owners

Inspected local main at d6dccf705c7743cee13cae6ed287636d1a3e05e0 on 2026-09-22. Remote refs were not refreshed; this is a plan against the local source. Recheck branch, status, and relevant changes when execution begins.

| Owner | Existing behavior relevant to this change |
| --- | --- |
| skills/implementing-staged-plans/scripts/program_setup.py | Semantic validation, recap/checkpoint adapters, setup receipt validation, first-start intent, source gates, sequence-zero recovery classification |
| skills/implementing-staged-plans/scripts/program_activation.py | Setup record and receipt writers; separate first-start grant; status-last writes; exact plan and execution transitions |
| skills/implementing-staged-plans/scripts/program_discovery.py | Pure route classification, including partial publication and activation prefixes |
| skills/implementing-staged-plans/scripts/program_launch.py | Legacy launch behavior and v3 recap presentation |
| skills/implementing-staged-plans/scripts/program_bootstrap.py | Proposal publication and legacy setup-recap digest receipt |
| skills/implementing-staged-plans/scripts/program_authority.py and state_authority.py | Supported authority schemas and current-state validation |
| tests/program_bootstrap_support.py | Synthetic fixtures; keep existing defaults and historical fixtures intact |

The canonical semantic validator is already shared by publication, discovery, and activation. Reuse it. Do not add parallel semantic validators or relax successor permission checks. Do not edit the existing renderer to return shorter text: its bytes participate in old persisted approval identities.

## Confirmed decisions and eligibility

- [x] New proposals only. The user will delete the existing proposal; this plan includes no migration or deletion of it.
- [x] Starting is allowed in the same or a fresh task, using a direct reply after the current summary is presented. A fresh task redisplays the summary after discovery and revalidation.
- [x] Summary output is ephemeral conversation/command output. No setup-recap.md, replacement summary document, or separate persisted prose copy is produced.

Use one optional immutable manifest-v3 field, program_start_contract, with the sole supported value combined-start/v1. Its absence means the unchanged historical route; an unknown/null/malformed value fails shared validation. Reject the field on older manifest families. Validate it through validate_setup_semantics and the existing program-authority family checks, covering publication, discovery, and activation. The manifest digest already binds it; no extra ledger or policy file is needed. A marked program requires the new combined adapters/receipts; an unmarked program cannot accept them. Generation chooses the field before publication and never patches an old program to add it.

## Increment 1: Short summary and explicit combined consent

**Files:** Modify program_setup.py and program_authority.py; create tests/test_program_start.py; add an explicit opt-in combined-start fixture helper to tests/program_bootstrap_support.py while preserving its legacy defaults. Paths under scripts are those in the owner table.

**Interfaces to add in program_setup.py:**

~~~python
def render_program_start_summary(program_root: Path) -> str: ...
def program_start_checkpoint(program_root: Path) -> dict[str, object]: ...
def adapt_program_start_decision(
    program_root: Path, response: str, *, role: str, provenance: str,
    checkpoint: Mapping[str, object],
) -> dict[str, object]: ...
def validate_program_start_decision(
    program_root: Path, decision: Mapping[str, object],
) -> list[str]: ...
~~~

These are interface declarations, not stub implementations. They consume the existing manifest/setup validator and produce a proposal-bound combined decision. They must not write files.

- [ ] Add ProgramStartContractTests using BootstrapFixture.configure_setup_v3() plus an explicit combined-start fixture opt-in, and v2 Delete coverage using configure_delete_setup_v2() plus that opt-in. Set program_start_contract before publication and update fixture digests through existing helpers. Test absent, supported, null, unknown, and wrong-family values, including no-write rejection at publication, discovery, and activation. Pin the actual start phrase and reject generic or conditional consent. Representative application assertion:

~~~python
checkpoint = SETUP.program_start_checkpoint(self.fixture.candidate)
decision = SETUP.adapt_program_start_decision(
    self.fixture.candidate, "Start the first increment",
    role="user", provenance="direct-user-message", checkpoint=checkpoint,
)
self.assertEqual(
    SETUP.validate_program_start_decision(self.fixture.candidate, decision), []
)
for reply in ("Yes", "proceed", "Start the first increment if tests pass"):
    rejected = SETUP.adapt_program_start_decision(
        self.fixture.candidate, reply, role="user",
        provenance="direct-user-message", checkpoint=checkpoint,
    )
    self.assertTrue(
        SETUP.validate_program_start_decision(self.fixture.candidate, rejected)
    )
~~~

- [ ] Run the focused class and verify failure is caused by the missing contract:

~~~bash
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_start.ProgramStartContractTests -v
~~~

- [ ] Implement deterministic summary projection and closed-field schemas: program-start-summary/v1, program-start-checkpoint/v1, and program-start-decision/v1. The checkpoint contains renderer identity/version, summary SHA-256, existing semantic and presented-integrity identities, program ID/revision, sequence-zero status digest/sequence, first-increment ID, and existing brief binding. Hash and derive identifiers with the existing canonical helpers:

~~~python
checkpoint["checkpoint_id"] = derive_identifier("program-start-checkpoint", checkpoint)
decision["decision_id"] = derive_identifier("program-start-decision", decision)
~~~

The decision contains exactly its schema, checkpoint, decision value, requested_actions (the ordered pair approve-program-setup and start-first-increment), conversation_role, provenance_class, response_sha256, and decision_id. Require and compare the supplied presented checkpoint. Unknown fields, unsupported schema combinations, wrong status, invalid identities, or mismatched bindings reject; do not fall back to a legacy adapter.

- [ ] Test source/program/semantic/workspace/brief/renderer drift, wrong role/provenance, quoted text, wrong increment, and integer-versus-boolean sequence confusion. Compare whole repository snapshots before and after pure calls and invalid decisions. Assert that rendering creates no file and that checkpoints/decisions contain summary digests and version metadata, not the rendered prose. Test both operation families and each approval mode without mutating the default fixture contract.
- [ ] Exercise a synthetic five-increment, high-allocation example. Assert that every increment outcome, Delete target/disposition, source gate, protected-work summary, and material boundary is represented; repeated requirement IDs and file metadata are not the default body. Review the rendered result as prose. Use the 250–400-word target as an editorial signal, never a truncation rule or accessibility claim.
- [ ] Re-run the focused class and the existing ProgramSetupTests once after this coherent batch. Confirm legacy rendered bytes and checkpoints remain unchanged.

## Increment 2: Durable combined authority and historical readers

**Files:** Modify program_setup.py, program_authority.py, state_authority.py; extend tests/test_program_start.py. Preserve existing authority tests.

**Interfaces:** Add a strictly validated setup-activation-decision/v3 with the existing SETUP_ACTIVATION_FIELDS plus program_start_decision, which embeds the complete program-start-decision/v1. Its setup_adapter_id and setup_adapter_sha256 bind that combined decision's ID and canonical digest; recap_checkpoint binds the new checkpoint. Existing common source, program, semantic, workspace, gate, and proposal bindings remain mandatory. Add increment-start-intent/v2, derived from that record rather than from a second direct message. Existing setup record v1/v2 and increment-start-intent/v1 validation stays intact.

~~~python
def derive_program_start_intent(program_root: Path) -> dict[str, object]: ...
~~~

The new intent contains program/revision/first-increment identity, the actual sequence-one status digest and integer sequence, brief binding, setup decision ID/digest, combined decision ID/digest, provenance_class equal to derived-program-start-decision, and its own intent ID. It contains no invented handoff response or direct-user assertion. Derivation is legal only at the initial awaiting-first-increment/preparing boundary, not after rollover.

- [ ] Add ProgramStartAuthorityTests. Build synthetic valid combined records; reject an old setup-only record, changed embedded decision, foreign proposal, mixed operation family, missing/extra fields, stale brief, and changed waiting-status binding. Reject combined receipts on unmarked manifests and legacy setup-only receipts on marked manifests. Verify unchanged legacy records still validate.
- [ ] Run the new class to establish the unsupported-schema failures.
- [ ] Extend the canonical setup-record validator and loader with explicit v3 dispatch. Validate all existing source/program/workspace/envelope/source-gate bindings plus the complete nested combined decision. Validate canonical record bytes and integer sequences. Reuse common equality/hash checks where they already own the invariant; keep version-specific required fields explicit.
- [ ] Extend validate_increment_start_intent to dispatch exactly between v1 and v2. v2 validates its durable origin and current waiting/preparing predecessor, including intent ID derivation:

~~~python
intent["intent_id"] = derive_identifier("increment-start-intent", intent)
~~~

Retain the original proposal status binding for historical validation. Re-render immutable summary facts using their recorded renderer version; never replace the original proposal digest with the current status digest. The public validate_program_start_decision is the live proposal-acceptance check; historical setup-record validation shares its immutable identity checks without reapplying sequence-zero/current-increment checks to later lifecycle states. Resolve the genesis brief from the original first increment in setup semantics when validating history, not from the status-current successor. Test this distinction in increment 5.
- [ ] Add the new setup schema to the exact authority allowlists and exercise the normal program/state validators. Update source-gate record loading through the same canonical validator. Preserve setup reuse, gate-specific answers, and exact setup-adapter boundary identity; do not add a parallel gate system.
- [ ] Run ProgramStartAuthorityTests plus existing setup/state/program authority tests. Assert that the new record adds no generic action or successor authority.

## Increment 3: Compose setup and first start with exact recovery

**Files:** Modify program_activation.py and the prefix-validation portions of program_setup.py; extend tests/test_program_start.py and application assertions in tests/test_program_setup.py only where the new route is exercised.

**Public interface:**

~~~python
def start_program(
    program_root: Path, decision: Mapping[str, object],
    observation: RepositoryObservation,
) -> ActivationReceipt: ...
~~~

It consumes the combined decision or that exact decision recovered from the durable setup record. It returns the existing ActivationReceipt at preparing after successful first start. Source-gate stops continue to use the existing source-gate procedure and recoverable records.

- [ ] Add CombinedProgramStartTests that publish a synthetic proposal, present the new checkpoint, and submit one direct start decision. Pin observable state and permission separation:

~~~python
receipt = ACTIVATION.start_program(root, decision, self.observation())
status = json.loads((root / "state/status.json").read_text(encoding="utf-8"))
self.assertEqual(receipt.increment_state, "preparing")
self.assertEqual(status["state_sequence"], 2)
self.assertEqual(status["current_increment_state"], "preparing")
self.assertEqual((root / "state/action-authorizations.jsonl").read_bytes(), b"")
~~~

Use the manifest's logical role to resolve the action-authorization ledger if a fixture changes its filename. The assertion concerns authority, not a filename convention.

- [ ] Run CombinedProgramStartTests and confirm missing combined activation fails.
- [ ] Implement full no-write preflight, then compose existing status-last writers. Extend the setup record builder to accept validated combined consent without manufacturing a legacy adapter. Reuse the existing program/workspace receipt builder and append/adopt helpers. Derive the new intent only after sequence-one status is valid, then call the existing start_first_increment writer through its extended strict validator.
- [ ] Keep gate ordering: setup record may exist while a pre-activation gate waits; program/workspace receipts must not precede it. A first-start gate may pause at sequence one, before the grant. Explicitly reused setup gates must still be shown in the combined summary. Do not suppress before-product-execution, particularly before Delete quarantine mutation.
- [ ] Inject interruption at each existing persistence boundary: setup-activation-decision, every due gate record, program-approval, workspace-approval, active-waiting-status, first-increment-grant, first-increment-status. On retry, assert byte-identical adoption, unique receipt IDs, no duplicate grants, correct previous-state chain, and no product delta. Include a fresh observation after the internal state changes.
- [ ] Inject drift before initial writes and between the setup and first-start stages. Reject changed workspace/head/protected bytes, source, first brief, summary version, decision, corrupt ledger prefix, symlink, or unrelated grant without cleanup. Initial invalid input writes nothing; mid-transaction drift preserves the already valid prefix and adds no new authority.
- [ ] Test idempotent replay at preparing and refusal to reset any later state. Test legacy setup-only sequence one cannot enter start_program. Run the focused class and affected setup lifecycle tests once after the batch.

## Increment 4: Front door, discovery, and readable instructions

**Files:** Modify program_discovery.py, program_launch.py, program_bootstrap.py, SKILL.md, references/program-discovery.md, references/approval-checkpoints.md, references/program-authority.md, docs/workflows.md, docs/reference.md, docs/troubleshooting.md; extend tests/test_program_discovery.py, tests/test_program_launch.py, tests/test_program_bootstrap.py, tests/test_front_door_contract.py, tests/test_program_start.py.

**Interfaces:** Preserve discover_programs and existing result structure. A pristine manifest marked combined-start/v1 returns program-start-ready, requiring program-start-decision and presentation of the current summary. A valid interrupted combined transaction returns program-start-retry-ready, requiring only an explicitly requested retry of the existing bound decision; discovery performs no writes. Source-gate pauses continue to use source-gate-approval-ready. Legacy setup-only and manifest-v2 routes remain distinct. A completed first start uses the existing preparing/resume route.

- [ ] Add ProgramStartDiscoveryTests for pristine eligible proposals, legacy proposals, each valid partial combined prefix, pending gates, completed preparing state, later active state, and corrupted prefixes. Every discovery invocation compares before/after snapshots and is read-only. Repeat partial-prefix classification in a fresh process.
- [ ] Implement combined-route classification through canonical prefix/authority inspection. Update both the main setup candidate path and publication-freshness inspection, which currently special-case setup activation schema v2. Unknown or divergent new records must not fall through to a legacy-ready route.
- [ ] Route render_program_launch_prompt to render_program_start_summary only for the marked family; preserve legacy outputs. In ProposalPublication, add program_start_summary_sha256 for the marked route and return null for setup_recap_sha256 there. For legacy proposals, keep setup_recap_sha256 unchanged and return null for the new field. Never repurpose the old digest to mean the new renderer. Neither field stores prose or creates a file.
- [ ] Update generation instructions to set combined-start/v1 before building bound bytes and to return/print the summary without adding setup-recap.md or any replacement summary document to the candidate inventory. Do not add a summary logical role. Extend publication tests to verify the exact expected artifact inventory, absence of a recap/summary file, and byte-identical no-write rediscovery. Include a front-door trace verifying that the controller does not separately write the printed summary to disk.
- [ ] Update the front-door instructions for both conversation routes. Generation presents the summary and stops. In the same task, a later direct reply supplies the presented checkpoint. In a fresh task, rediscover, revalidate, and print the current summary, then use its direct reply. Never treat the task-opening handoff, creation request, or an earlier unrelated answer as the new checkpoint response. After combined start, follow existing exact-plan/execution routing, pausing only where the current mode or another gate requires it.
- [ ] Document the distinction between a legacy setup-only waiting state and an interrupted combined start. Describe how to retry the latter without inventing another user decision; an old “yes” cannot recover new start authority. Keep later continuation/closure prompt semantics unchanged.
- [ ] Run the focused publication/discovery/launch/front-door tests. Manually trace creation-only, same-task start, fresh-task redisplay and start, missing source gate, explicit stop, and crash/retry conversations. In each trace, verify that no recap file is written. Static text tests do not prove that a host actually displayed a summary or captured a direct reply.

## Increment 5: Cross-lifecycle regression and delivery evidence

**Files:** Extend tests/test_program_start.py, tests/test_multi_increment_lifecycle.py, and tests/test_delete_operation_lifecycle.py only for uncovered application paths; update docs/maintainers.md with the bounded validation claim if needed.

- [ ] Exercise both operation families under standard, pre-approve, and full-increment modes. Standard must still pause for exact-plan approval. Other modes must create and validate the exact plan, baseline, and action authorization before the typed product transition. A combined start alone must not create an execution baseline or product delta.
- [ ] Carry a combined-start program through review, diff acceptance, one successor, and closure using existing fixtures. Verify the new genesis receipt remains valid while current increment authority changes. Preserve accepted predecessor evidence, conditional Modify/Preserve behavior, Delete tombstones, and exact source-gate order.
- [ ] Keep all legacy launch, setup-only activation, exact first-start handoff, continuation, and frozen v0.1.1 fixture tests. Do not rewrite expected legacy bytes merely to make new behavior pass.
- [ ] After the coherent change, run the full suite once and package validation:

~~~bash
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk proxy git diff --check
~~~

An interrupted or timed-out run is incomplete. Report actual skips and failures. Repeat successful checks only when relevant inputs change or a material unresolved concern warrants it.

- [ ] Make one focused requirements/DRY review of the final diff. Confirm that there is one canonical validator for each contract, no new general migration/workflow framework, no hidden authorization widening, and no edits outside the selected scope. Use at most one independent final reviewer if separately selected; do not run repeated reviews of an unchanged tree.
- [ ] Show the actual short summary for a synthetic program modeled on the Spotify increment structure. Obtain human feedback on whether the start action, workspace, scope, and risks are understandable. Do not claim that word counts or unit tests prove accessibility or live host behavior.
- [ ] Report code/test status separately from installation and live behavior. A host/evaluator campaign, installation, release version change, commit, push, or PR requires its own authorization. No live Spotify calls belong in this change.

## Completion record for this planning task

- Repository call paths, schema dispatch, source-gate ownership, and recovery behavior inspected.
- Current W3C primary guidance consulted for summary presentation; links are in the spec.
- Existing Spotify proposal checked read-only for compatibility constraints.
- Design and implementation plan finalized with new-proposal scope, both conversation routes, and output-only summary behavior; no implementation, installation, generated-program mutation, commit, push, or PR performed.
- Spec coverage, eligibility/receipt separation, output-only artifact ownership, and interface consistency self-reviewed. No material design question remains open in this plan. Implementation and any eventual installation are separate actions.

## Independent readiness review

The independent read-only reviewer combined_start_plan_review returned **READY — No material improvements recommended.** The review checked the design and plan against local commit d6dccf705c7743cee13cae6ed287636d1a3e05e0, including setup/activation, publication, discovery, state authority, rollover readers, and relevant application tests.

Reviewed content before this status/evidence annotation:

- Design SHA-256: 5362dc2a034d9cbc7d654dd855ffb1b013b8b2bca2a3a70edc3431f0ef907266.
- Plan SHA-256: 8b2068b74817b8d6ba700bd76de742715d66a279439cfe5049729fe76f3b1820.

One review round was sufficient: no material finding required a plan change or another review. This annotation changes no implementation requirement. No product implementation, runtime test, installation, or remote refresh was performed during plan review. Readiness means the plan can be implemented; it is not evidence that the planned behavior already works.
