# Compact Program Start Summary Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for sequential implementation. Use subagents only if separately selected. Steps use checkboxes. This document authorizes no implementation, installation, Git action, or change to a generated project.

**Goal:** Make the printed program-start summary follow the concise example accepted in the conversation: the same ordered increments, one workspace/approval explanation, concise scope and risks, detail links, and one start action.

**Architecture:** Add an explicitly versioned compact renderer while retaining the existing renderer for durable approval history. Render from existing canonical setup fields, stop enumerating ordinary operation allocations, and keep exact scope in the linked machine records. Reuse the existing checkpoint and lifecycle contracts; do not introduce another approval stage, summary file, manifest family, or summarization service.

**Tech Stack:** Python standard library, unittest, Markdown skill/reference instructions. All shell commands use RTK. No dependency changes.

**Spec:** The user-approved corrected example and the design contract below refine the Summary contract in [Combined program setup and first start](../specs/2026-09-22-combined-program-start-design.md). Existing authority, source-gate, operation-family, and recovery requirements remain applicable.

**Status:** Implemented and independently reviewed in the isolated worktree based on dd9fe7bff8021d55bc63dac06b1756d0e7996f9d. Full suite: 743 passed, one native-Windows-only test skipped; final focused checks and package validation passed. No material review findings remain. Implementation verification is complete; Git integration and installation are tracked separately. Remote refs were not refreshed.

## Reader summary

Replace the repeated Create/Modify/Preserve paragraphs with a short decision summary. Keep the five increment IDs and their order. Aim for 250–400 visible words for an ordinary five-increment program; never cut a warning to meet that target. Save no recap or replacement summary file.

The repair has three implementation increments: the compact renderer, approval/version compatibility, and front-door integration with realistic verification. Existing approvals remain bound to their original text. A pristine proposal can show the new summary without changing its manifest, but must receive a fresh direct reply to that presentation.

## Global Constraints

- Summary prose is output only; persist digest/version metadata, not a recap file or another copy of the rendered body.
- Preserve program_start_contract=combined-start/v1, manifest/status families, operation-envelope v1/v2, first-increment identity, exact source gates, and approval modes.
- Keep the existing program-start-summary/v1 renderer byte-compatible for historical validation and interrupted transactions.
- The displayed summary and accepted checkpoint must identify the same renderer and exact text. Never approve a short assistant paraphrase against the long renderer's digest.
- A changed presentation invalidates an unpersisted answer. A durable decision retains its original renderer and all original bindings.
- No migration, deletion, or rewriting of a real proposal, source plan, approval record, or installed plugin is included in this implementation scope.
- Preserve the unrelated untracked docs/superpowers/plans/2026-09-16-successor-operation-envelope-repair.md.

## Review Focus

1. Many different operation groups, not merely many identical paths: a realistic five-increment fixture must remain within 400 visible words and contain no ordinary allocation rows.
2. An exceptional destructive action or source gate must remain explicit even when it makes the summary longer: exercise Delete targets, disposition, conditions, and gates separately from the ordinary-size assertion.
3. Old approved text must still validate after the renderer changes: cover durable v1 decisions at sequence zero, sequence one, preparing, and later lifecycle states.
4. An old unpersisted checkpoint must not acquire new meaning: reject v1 live submissions on pristine proposals and redisplay v2 before accepting a new reply.
5. Generation must not surround the compact text with another long recap: trace the complete user-facing response and ensure one start action, no routine allocation dump, and no recap file.

## Verified problem

- The supplied Spotify output was reproduced by the current installed/source-identical renderer: 1,289 words including the final start action. Its 27 ordinary operation-group rows contribute about 888 words.
- program_setup.py:render_program_start_summary groups by operation, kind, collision, inclusion/exclusion lists, and increment IDs. Differences across increments retain repeated policy prose as separate groups.
- tests/test_program_start.py:test_high_allocation_summary_keeps_outcomes_gates_and_conditional_limits adds 70 copies of one allocation shape. Its assertion only requires fewer than one third of the legacy recap's words; it does not exercise the reported variation or enforce the agreed reading budget.
- An in-memory editorial sizing probe retained every existing program-level scope, boundary, and risk statement, omitted allocation rows, and produced approximately 372 words. This establishes that the example can fit the intended size without truncating those statements; it is not an implemented renderer or a readability certification.
- _program_start_checkpoint hashes the renderer output; historical _program_start_decision_issues currently reconstructs it using the same v1 renderer. Replacing that body in place would invalidate approvals and interrupted starts.

## Design contract

### Visible output

Use this order, with short bold labels and blank lines:

1. Program name and one-sentence intended outcome. A controller may add one short, verified creation-status sentence; the renderer does not claim a clean worktree, successful tests, or unchanged application code without that evidence.
2. A numbered list of all increments in canonical order, one outcome sentence each. Keep IDs unchanged in the underlying program. Display the ID as the label, or mechanically replace hyphens with spaces for a readable label; do not invent new increment names or reorder them. Clearly identify increment 1 as the next action.
3. One workspace/branch line. Show protected pre-existing work once when present; distinguish the immutable selection snapshot from a claim about today's live worktree. Link the full workspace path instead of repeating repository and workspace paths when identical.
4. **Starting authorizes:** setup and first-increment local work, with the selected approval mode explained in ordinary language. Standard retains exact-plan approval; pre-approve/full-increment omit that routine pause. Material design decisions and other remaining boundaries stay explicit.
5. **Scope:** program-level protections and exclusions, once. Keep all permissions conditional where the underlying plan is conditional. Detailed paths, operation counts, modes, review-report allocations, and ordinary inclusion/exclusion logs belong in the linked exact scope.
6. **Main limits:** the canonical material risks. Explain any actual Delete allocation separately with its exact path, owning increment, content disposition/rationale, and predecessor condition. Never manufacture a generic “no deletion” claim when Delete is allocated.
7. Source-defined gates, including whether starting satisfies an explicitly reusable gate or a separate answer is required. Gates can justify output longer than the ordinary target.
8. A compact link row to the source plan, full proposal, and exact scope. Traceability remains available through the proposal/machine records and need not be a fourth default link.
9. One action: “To approve this setup and begin increment 1, reply: **Start the first increment**”. This starts only the first increment; later acceptance, continuation, and closure retain their existing procedures.

Preserve all distinct program-level protections, exclusions, external boundaries, remaining approval boundaries, and material risks. Merge them into the appropriate sections, remove only exact repetitions after whitespace/terminal-punctuation normalization, and avoid duplicated fixed boilerplate. Do not use fuzzy semantic deduplication, keyword-based deletion of warnings, sentence clipping, ellipses, or a live LLM call inside the renderer. Do not print ordinary Create/Modify/Preserve allocation rows, even if their wording varies.

New-proposal authoring must put concise, decision-relevant exceptions in the existing canonical protection/exclusion/risk fields before immutable publication. Examples are repairs restricted to independently validated findings and instruction edits limited to a project-purpose section. This is part of faithfully authoring the proposal, not a new persisted summary body. Never silently edit those fields in an already published proposal. The concise display remains a projection with links to its complete conditional scope, not a broader permission grant.

The user's corrected Spotify text is the editorial reference, not a hardcoded Spotify template. No program-specific phrases or source paths belong in the generic renderer. Preserve source facts; use concise outcome and scope text when authoring new proposals rather than algorithmically paraphrasing arbitrary existing prose. Existing lengthy unique risks must remain visible even when they exceed the ordinary budget.

### Renderer and consent compatibility

Keep checkpoint schema program-start-checkpoint/v1 and decision schema program-start-decision/v1: both already carry renderer identity/version and a text digest. Recognize exactly these pairs:

| renderer_schema | renderer_version | Use |
| --- | --- | --- |
| program-start-summary/v1 | integer 1 | Existing durable decisions and exact retry/history validation |
| program-start-summary/v2 | integer 2 | Newly presented compact summaries and fresh consent |

No manifest marker change is needed. A pristine combined-start/v1 proposal uses current renderer v2 without writing any proposal bytes. An old v1 checkpoint that was merely displayed is stale after upgrade: redisplay v2 and require its new direct reply. A valid setup record already containing a v1 decision fixes the retry/history renderer to v1; it must not be re-approved or rewritten as v2.

Unknown versions, Boolean versions, mismatched schema/version pairs, and changed digests fail closed. Selecting a valid historical version is necessary for reconstruction, but never enough to authorize a pristine legacy submission. Preserve all existing source, program, semantic, brief, protected-work, workspace, and state bindings.

### Success measures and limits

- For the ordinary five-increment fixture modeled on the reported variation, the full canonical summary is at most 400 visible words. Count link labels, not URL targets; count the title, headings, permission explanation, and start action. Do not pad a shorter useful result to 250 words.
- That fixture has exactly five increment entries, one start action, no ordinary allocation rows, no repeated repository/workspace identity, and every required program-level restriction and risk.
- Adding more routine allocations with otherwise unchanged canonical summary facts does not add prose to the summary. The manifest/checkpoint integrity bindings still change.
- Delete and gate fixtures assert complete disclosure rather than a universal hard maximum. Ordinary allocations must never return as an overflow fallback.
- The complete controller response should add at most one brief factual status sentence in the ordinary creation flow. It should not quote workflow mechanics or repeat the start instruction as stock boilerplate. Preserve genuinely required host disclosures when they apply.
- Word counts and structural assertions catch the observed regression; a human inspection of the rendered result is still required to judge readability.

## Increment 1: Versioned compact renderer and realistic regression

**Modify:** skills/implementing-staged-plans/scripts/program_setup.py; tests/test_program_start.py; tests/program_bootstrap_support.py only for a reusable fixture that has more than one real consumer.

**Interfaces:**

~~~python
CURRENT_PROGRAM_START_RENDERER_VERSION = 2

def render_program_start_summary(
    program_root: Path, *, renderer_version: int | None = None,
) -> str: ...
~~~

None selects the current version; only exact integer 1 or 2 is accepted explicitly. Retain the old function body as a private v1 renderer. Add a private v2 renderer in the same canonical module, using the existing manifest/path validators. Do not share new formatting helpers with the frozen v1 body if that changes its bytes. Interface ellipses here are declarations, not implementation stubs.

- [x] Add CompactProgramStartSummaryTests. Construct five increments with at least 70 valid ordinary allocations and at least 20 distinct old grouping keys: different increment memberships, existing versus accepted-predecessor conditions, Create/Modify/Preserve, and bounded review-report paths. Retain valid successor permission schedules. Preserve the existing identical-allocation test as a separate case.
- [x] Add a representative output test with program-level scope/risk prose comparable in size to the reported example. Include the validated-repair condition and instruction-edit limitation as canonical scope facts, alongside no-provider/no-data-mutation boundaries. Do not copy the user's repository, source file, credentials, or generated proposal into a fixture.
- [x] Pin observable assertions, including the absolute budget:

~~~python
summary = SETUP.render_program_start_summary(self.root)
visible = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", summary)
self.assertLessEqual(len(visible.split()), 400)
self.assertEqual(len(re.findall(r"^\d+\. ", summary, re.MULTILINE)), 5)
self.assertNotRegex(summary, r"(?m)^(Create|Modify|Preserve):")
self.assertEqual(summary.count("Start the first increment"), 1)
~~~

Also assert each expected outcome, meaningful restriction, material risk, workspace/branch, and resolved link destination. Word count alone is insufficient.
- [x] Run the new test class against the existing implementation and confirm failure reflects allocation rows/size rather than fixture invalidity:

~~~bash
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_start.CompactProgramStartSummaryTests -v
~~~

- [x] Before changing rendering, capture an exact v1 expected output for a controlled fixture as a Python test literal. Normalize only fixture-dependent absolute root prefixes in that assertion. Verify line breaks, ordering, punctuation, and terminal action; retain no generated recap file in a real or candidate program.
- [x] Implement the v2 section layout from the design contract. Use stable first-occurrence deduplication for exact repeated statement text, preserve distinct warnings, and keep full Delete/gate details. Replace verbose fixed approval mechanics with the approved user-facing explanation. Reuse resolve_managed_path for links and preserve root-alias determinism.
- [x] Add tests for all three approval modes, selected user work, distinct repository/workspace paths, no Delete versus actual Delete, conditional Delete, reusable and non-reusable gates, unusually long unique risks, and no filesystem writes. A large gate/risk case must preserve content even if over 400 words.
- [x] Run the focused class once on the coherent renderer change; inspect the actual compact output as prose. Preserve v1 byte-equivalence tests instead of updating their expectations to v2.

## Increment 2: Bind fresh consent to v2 while preserving v1 recovery

**Modify:** skills/implementing-staged-plans/scripts/program_setup.py; skills/implementing-staged-plans/scripts/program_activation.py where necessary to use the canonical acceptance/retry distinction; tests/test_program_start.py; tests/test_program_discovery.py for recovered routes. No new ledger or public migration command.

**Interfaces and callers:**

- _program_start_checkpoint gains an explicit renderer_version keyword; it sets the matching renderer schema/version and hashes that renderer's exact bytes. All existing fields and identifier derivations remain intact.
- program_start_checkpoint creates a fresh current-v2 checkpoint for a pristine proposal. It does not silently select v1 from an arbitrary caller-supplied checkpoint.
- _program_start_decision_issues reconstructs the exact recognized pair in the decision being validated. Historical reconstruction retains the original proposal digest and protected-work identity; live validation still rechecks current protected work.
- validate_program_start_decision distinguishes pristine acceptance from an exact existing durable prefix. Pristine acceptance requires current v2. Retry acceptance requires a validated canonical setup record whose embedded decision is exactly the submitted decision; only that durable origin permits v1. Reuse the sequence-zero prefix validator and _setup_activation_record rather than treating file existence as validity.
- adapt_program_start_decision accepts only the fresh current presentation on a pristine proposal. An existing durable setup decision routes to retry, not another adaptation. Preserve exact direct-user consent requirements.

- [x] Add ProgramStartRendererCompatibilityTests. Before changing the current-version default, create synthetic v1 records using the frozen old renderer and existing typed writers. Keep those records available to the upgraded reader within the fixture; do not manufacture user provenance from new renderer output.
- [x] Cover this boundary table with assertions that no unrelated bytes change:

| State at upgrade | Expected behavior |
| --- | --- |
| Pristine, v1 text previously printed, no receipt | Fresh default is v2; reject old unpersisted v1 decision; accept only a new reply to current v2 |
| Sequence zero, durable v1 setup record, pending pre-activation gate | Validate original v1 decision, persist the exact gate answer, and recover the original prefix |
| Sequence zero, v1 program/workspace receipt prefix | Adopt identical receipt bytes and continue without new consent |
| Sequence one, durable v1 setup, pending first-start gate or grant prefix | Preserve original decision and intent identity; recover through existing source-gate/start writers |
| Preparing or later active/accepted/blocked/closed state | Existing authority remains valid; no rewrite or reset; use the current legal lifecycle route |
| Any unknown pair, edited v1/v2 text, changed source/workspace/brief, or forged retry origin | Fail closed and preserve all bytes |

- [x] Audit the complete current call chain, including the second validation inside _activate_setup_program and the pre-activation call inside persist_source_gate_decision. Both currently invoke validate_program_start_decision and would strand a v1 prefix if only fresh-v2 validation were added. Keep the historical reader path non-recursive: its low-level decision reconstruction must not call the outer live/prefix validator.
- [x] Preserve live fresh-observation checks during an old-version retry. Matching the original renderer cannot excuse drift in protected work or selected workspace. A version selected from a submitted decision without a valid durable origin is insufficient authority.
- [x] Update existing renderer tamper tests: version 2 is now valid only with its matching schema and correctly bound current output. Use version 99, Boolean values, and cross-paired schema/version cases for unsupported-version rejection. Keep a separate test that old unpersisted v1 consent is stale.
- [x] Run focused compatibility, existing CombinedProgramStartTests, and affected discovery tests. Include at least one v1-approved program reaching a successor so genesis history and status-current authority remain distinct. Do not change legacy setup-only recap or manifest-v2 launch contracts.

## Increment 3: Integrate presentation, authoring guidance, and complete verification

**Modify as required by behavior:** skills/implementing-staged-plans/SKILL.md; references/approval-checkpoints.md; docs/workflows.md; docs/reference.md; docs/troubleshooting.md; tests/test_program_start.py; tests/test_front_door_contract.py. Verify program_launch.py and program_bootstrap.py use the current default renderer; change their code only if necessary. Update the Summary contract in docs/superpowers/specs/2026-09-22-combined-program-start-design.md to point to the implemented v2 behavior, preserving its historical context.

- [x] Document the exact compact layout and authoring rules. In new proposals, make outcome/protection/exclusion/risk text concise and ensure decision-relevant scope exceptions are represented in those existing canonical fields. Preserve the full allocations and source traceability. Do not save an independently authored recap or permit the controller to substitute a free-form paraphrase after the checkpoint is computed.
- [x] Make render_program_launch_prompt and ProposalPublication.program_start_summary_sha256 agree with current-v2 presentation. Publication's informational digest can be recomputed for a pristine proposal without changing its immutable candidate/owner inventory; it is not an approval. Durable setup decisions continue to select their recorded renderer for validation. Legacy setup_recap_sha256 retains its original meaning.
- [x] Extend the publication/launch application test: captured output equals the v2 renderer, publication digest equals the presented checkpoint's summary digest, and candidate/staging/final inventories contain no recap or replacement summary file. Verify repeated render/discovery operations are read-only.
- [x] Trace a complete creation response and same-task/fresh-task starts. Print the canonical summary once, add no repeated allocation or workflow-policy appendix, and offer one exact start action. Keep independent gates where the existing lifecycle requires them. A fresh task redisplays the current summary before its direct reply; it does not inherit old unpersisted consent.
- [x] Run focused application and document tests after the coherent change:

~~~bash
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_start tests.test_program_discovery tests.test_program_launch tests.test_program_bootstrap tests.test_front_door_contract tests.test_distribution_documentation -v
~~~

- [x] Then run the full relevant suite once, package validation, and whitespace checks:

~~~bash
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk proxy git diff --check
~~~

Allow the full suite to reach terminal completion; interrupted output is incomplete evidence. Repeat successful checks only after relevant inputs change or a concrete unresolved concern warrants it.

- [x] Inspect the ordinary and exceptional rendered examples as a human-facing response. Confirm the five items remain the same implementation increments, not new phases or different scope. Report the visible word count alongside the actual output. The ordinary example must meet the 400-word ceiling; exception cases must explain any necessary additional warning/gate content.
- [x] Make one final requirements and unnecessary-change pass. No generic migration framework, new dependencies, arbitrary prose parser, persisted recap, expanded permission, or unrelated refactor should be present. Review of this implementation, installation, source-cache parity after installation, and any release/Git action remain separately scoped; no provider or real Spotify execution is needed for this repair.

## Research and planning verification

Current W3C supplemental guidance was checked during planning. [Make important actions and information easy to find](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o2p04-page-important/) supports the compact ordered presentation. [Explain action consequences and disadvantages](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o7p03-supported-choice/) supports retaining visible risks and meaningful scope changes. These are design references, not a claim of accessibility conformance.

Self-review checks: the accepted layout is mapped to renderer tests; historical consent is mapped to explicit old/new-version application paths; no-file behavior is mapped to publication and front-door tests; controller verbosity is covered separately from the pure renderer. The plan changes presentation, not the five-increment program or its execution authority. No implementation, project mutation, installation, commit, push, or PR occurred while authoring this plan.

## Implementation verification

The reported program renders at 375 visible words versus 1,289 with v1, with the same five increments and one start-action line. The varied ordinary-allocation fixture renders at 252 words. Rendering remains output only. The complete original v1 renderer body is unchanged.

The full suite completed 744 tests in 3226.072 seconds: 743 passed and the native Windows rename-semantics case was skipped on macOS. During that run, only test code changed: the reviewer-requested portable fixture normalization and an additional exceptional Delete/separate-gate presentation case. Both final test changes passed targeted verification; production code remained unchanged throughout the full run. Package validation and final whitespace checks passed.

One independent reviewer checked the complete production change and lifecycle callers. Its sole retained finding was the portable fixture assertion, reproduced and fixed before review closure. No material improvements were recommended afterward. Live host presentation, human comprehension/accessibility, installation, and provider behavior were not certified by these deterministic checks. The original checkout and real program were preserved.
