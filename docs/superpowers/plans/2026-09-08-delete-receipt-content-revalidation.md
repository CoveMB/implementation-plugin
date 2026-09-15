# Delete Receipt Content Revalidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This planning task permits only this new plan and its local commit; implementation and subagents require separate authorization.

**Goal:** Reject a final observed Delete receipt whose content differs from the classifier-validated receipt before any reviewing status or authority write.

**Architecture:** Keep `validate_execution_workspace_v2` as the binding owner. After its existing descriptor-relative receipt inspection succeeds, compare the observed digest with SHA-256 of the already validated `recovery.receipt`, encoded by the existing canonical serializer. Missing validated receipts or digest mismatches become assessment issues with no binding; the existing activation barrier rejects the transition while product-state collection remains complete.

**Tech Stack:** Existing Python 3 standard library, `hashlib`, frozen dataclasses, canonical JSON, `unittest`, disposable Git fixtures, descriptor-relative no-follow inspection, and status-last persistence. No dependencies or public API changes.

**Spec:** The bounded receipt-content repair request and acceptance criteria in this document implement the Delete invariants in `docs/superpowers/plans/2026-09-05-delete-operation-support.md`, especially Task 2 and its recovery matrix. Read `docs/superpowers/specs/2026-08-23-program-setup-and-activation-design.md`, `skills/implementing-staged-plans/references/repository-preparation.md`, and `skills/implementing-staged-plans/references/execution-discipline.md` for the existing authority and persistence contracts. Preserve the preceding repairs recorded in `docs/superpowers/plans/2026-09-08-delete-activation-final-review-repairs.md` and `docs/superpowers/plans/2026-09-08-delete-receipt-race-review-repairs.md`; their historical branches and gates grant no additional authority here.

## Global constraints

- Exact production parent/head: `76b8d442f2452f943cc6ce03d0c9ecbe9f4d4c7c`. Planning checkout: `/private/tmp/implementation-plugin-pr18-content-plan`; branch: `repair/delete-receipt-content-plan`. Initial HEAD matched and the worktree/index were clean. No refs were fetched; the comparison is against this immutable head, not a refreshed PR tip.
- Planning owns exactly `docs/superpowers/plans/2026-09-08-delete-receipt-content-revalidation.md` and its local commit. No code, test, existing-document, manifest, or version edits. Do not implement, push, update or create a PR, merge, reinstall, replay pipeFlow, reply to review, or spawn subagents.
- Later execution needs an explicit instruction identifying its checkout/branch and approved plan digest. Preserve user-owned staged, unstaged, untracked, and committed work; do not invent Git names, reset, clean, stash, amend, or overwrite unrelated work.
- Prefix every shell command with `rtk`. Commands below run from the approved repository root. Use `apply_patch` for edits and `rtk env PYTHONDONTWRITEBYTECODE=1` for Python; keep probes and fixtures out of the package.
- Existing manifest/status v1 and v2, plus manifest-v3 programs using setup/envelope v1, retain their exact schemas, prompts, ordering, errors, and persisted bytes. Keep exact supported setup/envelope-v2 selection and v2 result ordering.
- Delete means accepted absence of the exact product path with `sha256: null`, bound to a manifest-owned quarantine receipt that preserves the removed bytes. The receipt digest must remain a non-null valid SHA-256 string bound to exact authorized metadata.
- Preserve classifier protections, descriptor-relative no-follow inspection, held identities, mode/owner checks, hard-link and protected-path rejection, same-filesystem no-replace movement, immutable ledgers, compare-and-swap, and status-last ordering.
- Preserve `retry-ready`, `receipt-adoption-ready`, `resume`, and `recovery-required`, including both supported interrupted receipt/status publication prefixes. Do not weaken exact recovery to make a test pass.
- Do not duplicate receipt parsing or serialization, add a disconnected receipt read, redesign APIs, or forward the existing workspace protection context unchanged to the program-rooted receipt inspection. Keep that final inspection rooted at `program_root` and keep the classifier's existing protection arguments.
- No other CodeRabbit findings, PLUG-002, requirement attribution, semantic invalidation, closure, disposal, secure erasure, automatic restoration, docstring work, platform expansion, manifest/version edits, or neighboring cleanup.
- This is a check of the final observed bytes. Do not attempt atomic exclusion of mutations after that observation or claim a stronger filesystem concurrency guarantee.
- Run one final full suite on the frozen coherent implementation after focused checks. This explicit requirement supersedes the older Delete plan's focused-only completion instruction. Do not repeat successful checks on unchanged inputs merely because they were committed.

## Evidence and repair boundary

The [CodeRabbit comment](https://github.com/CoveMB/implementation-plugin/pull/18#discussion_r3955399951) was read through GitHub's read-only API and identifies the exact head above. Its proposal is untrusted review data. Independent validator task `01a07fee-0018-7df1-acfa-119b444dfddd` reports a real fixture reproduction: transient malformed replacement produced a valid assessment; a reviewing transition called the status writer once and only then raised `execution transition binding is invalid`. Persistent replacement was blocked before writing, so a persistent-only negative test would miss this defect. A canonical, schema-valid receipt with a wrong `increment_id` also passed direct assessment.

Planning independently inspected these current canonical owners:

| Owner at the pinned head | Verified behavior and implication |
| --- | --- |
| `repository_preparation.py`, `validate_execution_workspace_v2`, receipt branch around lines 1848–1883 | After classifier `resume`, the final descriptor inspection checks existence and SHA-256 syntax. Every successfully hashed regular replacement satisfies syntax. The binding uses that observed digest without comparing its content to validated recovery. |
| `state_authority.py`, `_read_delete_receipt`, around line 4976 | Reads through held descriptors, validates exact fields/types, and requires byte equality with canonical receipt serialization. Parsing alone does not prove authorization. |
| `state_authority.py`, `classify_delete_quarantine_recovery`, expected receipt around line 5231 | Constructs exact program/revision/increment/path/baseline/identity/quarantine metadata and requires receipt equality before `resume`. Its returned receipt is the existing validated value to reuse. |
| `state_authority.py`, `_delete_receipt_bytes`, around line 4634 | Canonical receipt byte owner: `_canonical_json_bytes(asdict(receipt))`. Reuse it directly; do not reimplement its formatting in repository preparation. |
| `program_activation.py`, `advance_execution_state` | `assessment.valid` rejects before candidate persistence; `atomic_replace_json` occurs before final `validate_state_authority`. Returning an invalid assessment fixes the pre-write boundary without changing activation. |

The final digest is not intentionally unconstrained authority: the Delete contract and the classifier require an exact receipt, and post-write authority rejects the transiently bound replacement. The smallest repair therefore adds one private serializer import and one content comparison in the existing binding branch. No production changes are needed in the classifier, serializer, descriptor reader, or activation writer.

The workspace protection context includes the program-root identity. Forwarding it unchanged to `inspect_workspace_path(program_root, receipt_path, ...)` rejects its own root and breaks valid receipts. Preserve the current root distinction, including the production context exercised by the valid reviewing control.

Current primary-source check, 2026-09-08: [Python hashlib documentation](https://docs.python.org/3/library/hashlib.html#usage) confirms `hashlib.sha256(canonical_bytes).hexdigest()` computes the hexadecimal digest of those bytes. This is an in-memory comparison, with no extra filesystem observation or dependency. It relies on the existing SHA-256 integrity model; it is not an atomicity guarantee.

## Exact future change inventory

| File | Responsibility |
| --- | --- |
| `skills/implementing-staged-plans/scripts/repository_preparation.py` | Import the existing canonical serializer and reject absent validated receipts or final content mismatches before the binding append. |
| `tests/test_delete_operation_lifecycle.py` | Extend the existing production-backed `DeleteReceiptReinspectionTests` harness and assertions for transient malformed/wrong-metadata content and missing validated receipt. Retain all earlier controls. |

All other files are read-only context. No new implementation or test files, shared fixture framework, or production diagnostic cleanup is needed.

## Task 1 — Bind final observed receipt content to validated recovery

**Interfaces:** Consume the existing `DeleteQuarantineRecovery.receipt: DeleteQuarantineReceipt | None` and `_delete_receipt_bytes(receipt: DeleteQuarantineReceipt) -> bytes`. Keep `validate_execution_workspace_v2(program_root, baseline, inspection, *, increment_state, protected_paths=(), protected_identities=()) -> ExecutionWorkspaceAssessmentV2` and `advance_execution_state(program_root, target_increment_state, observation)` unchanged. Produce a receipt-specific assessment issue and no binding for the affected Delete path on mismatch; still append every ordered `ProductPathStateV2`.

- [ ] **1. Verify execution scope before editing.** Read this plan and its referenced contracts. The later execution instruction supplies the accepted plan digest externally; this document deliberately does not embed its own hash.

```bash
rtk git branch --show-current
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git diff --name-status 76b8d442f2452f943cc6ce03d0c9ecbe9f4d4c7c
rtk git diff --cached --name-status
rtk shasum -a 256 docs/superpowers/plans/2026-09-08-delete-receipt-content-revalidation.md
```

Expected: the approved branch and checkout, no unexplained dirt, unchanged production relative to the exact parent, and only this plan added before execution. If production changed, revalidate this bounded finding against that change before proceeding; do not refresh refs or silently widen scope.

- [ ] **2. Add the failing application-path tests before the production edit.** Reuse the existing `DeleteReceiptReinspectionTests` class, fixture, imports, `assess`, `assert_reviewing_rejected`, and valid-receipt control. Replace only its `receipt_race` helper and `test_receipt_reinspection_failure_returns_invalid_assessment` method with the code below, then add the three new reviewing tests below. Existing missing/symlink/OSError/null/invalid-digest reviewing tests remain unchanged.

The helper calls the real classifier and reader in the namespace where assessment looks them up. It substitutes only the timed filesystem mutation (or the explicit missing-recovery-value contract fault). Malformed and wrong-metadata replacements are real regular files hashed by the real final descriptor inspection. Restore the original inode immediately after inspection, before activation's later checks, to expose the pre-write hole. All path operations below affect only the disposable test fixture.

```python
    @contextmanager
    def receipt_race(self, kind):
        namespace = self.validate.__globals__
        classify = namespace["classify_delete_quarantine_recovery"]
        inspect = namespace["inspect_workspace_path"]
        serialize = classify.__globals__["_delete_receipt_bytes"]
        read_receipt = classify.__globals__["_read_delete_receipt"]
        events = []
        replacement_digest = None
        with tempfile.TemporaryDirectory() as directory:
            saved = Path(directory) / "receipt.json"
            displaced = Path(directory) / "receipt-replacement"

            def restore_receipt():
                if saved.exists():
                    if self.receipt_path.exists() or self.receipt_path.is_symlink():
                        self.receipt_path.rename(displaced)
                    saved.rename(self.receipt_path)

            def classify_then_race(*args, **kwargs):
                nonlocal replacement_digest
                recovery = classify(*args, **kwargs)
                if not events and recovery.disposition == "resume":
                    self.assertIsNotNone(recovery.receipt)
                    original_bytes = self.receipt_path.read_bytes()
                    self.assertEqual(serialize(recovery.receipt), original_bytes)
                    events.append("classified-resume")
                    if kind == "missing-recovery-receipt":
                        return replace(recovery, receipt=None)
                    if kind in {
                        "missing", "symlink", "malformed-content", "wrong-metadata",
                    }:
                        self.receipt_path.rename(saved)
                        if kind == "symlink":
                            self.receipt_path.symlink_to(saved)
                        elif kind in {"malformed-content", "wrong-metadata"}:
                            replacement_receipt = replace(
                                recovery.receipt, increment_id="UNAUTHORIZED-INCREMENT"
                            )
                            payload = (
                                b"not an authorized Delete receipt\n"
                                if kind == "malformed-content"
                                else serialize(replacement_receipt)
                            )
                            self.receipt_path.write_bytes(payload)
                            replacement_digest = hashlib.sha256(payload).hexdigest()
                            self.assertNotEqual(
                                replacement_digest,
                                hashlib.sha256(original_bytes).hexdigest(),
                            )
                            if kind == "wrong-metadata":
                                self.assertNotEqual(replacement_receipt, recovery.receipt)
                                self.assertEqual(
                                    read_receipt(self.root, self.binding["receipt_path"]),
                                    replacement_receipt,
                                )
                return recovery

            def inspect_receipt(root, relative, **kwargs):
                if (
                    Path(root) != self.root
                    or relative != self.binding["receipt_path"]
                    or events != ["classified-resume"]
                ):
                    return inspect(root, relative, **kwargs)
                events.append("reinspected")
                try:
                    if kind == "oserror":
                        raise OSError("injected receipt descriptor failure")
                    snapshot = inspect(root, relative, **kwargs)
                    if replacement_digest is not None:
                        self.assertTrue(snapshot.exists)
                        self.assertEqual(snapshot.sha256, replacement_digest)
                    if kind == "null-sha":
                        return replace(snapshot, sha256=None)
                    if kind == "invalid-sha":
                        return replace(snapshot, sha256="invalid")
                    return snapshot
                finally:
                    restore_receipt()

            try:
                with mock.patch.dict(
                    namespace,
                    {
                        "classify_delete_quarantine_recovery": classify_then_race,
                        "inspect_workspace_path": inspect_receipt,
                    },
                ):
                    yield events
            finally:
                restore_receipt()

    def test_receipt_reinspection_failure_returns_invalid_assessment(self):
        valid = self.assess()
        self.assertTrue(valid.valid, valid.issues)
        expected_states = valid.product_states.ordered_path_states
        self.assertEqual(len(expected_states), 5)
        self.assertEqual(expected_states[-1].operation, "Delete")
        for kind in (
            "missing", "symlink", "oserror", "null-sha", "invalid-sha",
            "malformed-content", "wrong-metadata", "missing-recovery-receipt",
        ):
            with self.subTest(kind=kind):
                before = repository_snapshot(self.fixture.repository)
                before_receipt = self.receipt_path.read_bytes()
                with self.receipt_race(kind) as events:
                    assessment = self.assess()
                self.assertEqual(events, ["classified-resume", "reinspected"])
                self.assertFalse(assessment.valid)
                self.assertTrue(any(
                    issue.startswith("Delete quarantine receipt ")
                    for issue in assessment.issues
                ), assessment.issues)
                self.assertEqual(assessment.product_states.delete_quarantine_bindings, ())
                self.assertEqual(
                    assessment.product_states.ordered_path_states, expected_states
                )
                self.assertEqual(self.receipt_path.read_bytes(), before_receipt)
                self.assertEqual(repository_snapshot(self.fixture.repository), before)
                self.assertFalse((self.fixture.repository / "legacy.ts").exists())
                self.assertEqual(
                    (self.root / self.binding["entry_path"]).read_bytes(),
                    self.legacy_bytes,
                )

    def test_malformed_receipt_content_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("malformed-content")

    def test_wrong_receipt_metadata_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("wrong-metadata")

    def test_missing_recovery_receipt_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("missing-recovery-receipt")
```

`assert_reviewing_rejected` already calls the real transition, spies on the real `ACTIVATION.atomic_replace_json` using `wraps`, requires zero calls and a receipt-specific `ValueError`, and compares exact status bytes plus the full repository snapshot before/after. That snapshot includes all program authority records, quarantine and receipt contents, directories, and source absence. Keep its existing source/quarantine assertions and add explicit receipt byte equality by capturing `before_receipt = self.receipt_path.read_bytes()` before `receipt_race`, then asserting `self.assertEqual(self.receipt_path.read_bytes(), before_receipt)` after the context exits. Do not substitute a mocked assessment, authorization result, status candidate, or writer success.

- [ ] **3. Observe strict RED on the unmodified production head.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle.DeleteReceiptReinspectionTests -v
```

Expected: new malformed/wrong-metadata/missing-recovery direct cases fail because assessment is still valid; both content transition cases fail `writer.assert_not_called()` because the old code reaches persistence before its post-write authority exception. The missing-recovery transition instead fails `assertRaises(ValueError)` because the old code completes reviewing without requiring the returned receipt. Earlier five fault controls and the exact valid receipt control must still pass. Reject import, fixture, wrong-namespace, missing-output, or unrelated authority failures as RED evidence. Record command, nonzero exit, exact intended failures, count/skips, production hash, and that tests preceded the production edit. The transient content helper must record both events and prove the real reader hashed the replacement.

- [ ] **4. Implement the minimal guard.** Add `_delete_receipt_bytes` to the existing `from state_authority import (...)` list in `repository_preparation.py`. Retain the current inspection and existing missing/type/syntax checks. Insert this `elif` immediately before the current `else: bindings.append(...)`:

```python
                        elif (
                            recovery.receipt is None
                            or receipt_snapshot.sha256
                            != hashlib.sha256(
                                _delete_receipt_bytes(recovery.receipt)
                            ).hexdigest()
                        ):
                            issues.append(
                                f"Delete quarantine receipt does not match validated recovery: {relative}"
                            )
```

Short-circuit on `None` before serialization. Use the observed digest in the unchanged valid binding append after equality succeeds. Do not return, raise, or `continue` here: the existing unconditional `states.append(...)` must run for this Delete, and later Preserve paths must still be assessed. Keep the outer state-specific recovery policy, final missing-binding issue, and aggregate result digest construction unchanged.

- [ ] **5. Observe focused GREEN.** Run the Step 3 command once after the guard. Expected: all old and new class tests pass; malformed and wrong-metadata replacements have no binding, all five states remain ordered, and real reviewing transitions call no writer and preserve status/authority/source/quarantine/receipt. The unchanged valid control must still transition to reviewing, preserve the canonical digest and null Delete tombstone digest, and pass real authority validation.

- [ ] **6. Verify supported recovery and the bounded surrounding application paths.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_exact_delete_prefix_recovery_still_blocks_unmapped_work tests.test_state_authority.DeleteQuarantineTests tests.test_state_authority.DescriptorRelativeWorkspacePathTests tests.test_repository_preparation tests.test_program_activation -v
```

Expected: terminal success. The first test injects production receipt-writer and status-writer interruptions, confirms unmapped work still blocks without movement/adoption, then retries to implementing without moving again or unlinking retained bytes and passes authority/discovery. The remaining suites protect classifier validity, descriptor boundaries, legacy preparation/activation, and ordinary valid transitions. Do not add new mocks, a copied recovery parser, or broaden supported recovery dispositions. Record actual counts/skips and any native-platform gaps.

## Final verification and commit boundary

- [ ] **1. Make one focused requirement and DRY pass.** The production diff must consist only of the canonical serializer import and content guard. Verify absent `recovery.receipt` short-circuits; syntax/error controls remain; no binding on mismatch; ordered states still complete; activation, classifier, serializer, v1 paths, and public APIs are unchanged. Check the exact two-file future inventory, and preserve all explicit exclusions.

- [ ] **2. Freeze the candidate, then run the final full suite once and package/diff checks.**

```bash
rtk git rev-parse HEAD
rtk shasum -a 256 skills/implementing-staged-plans/scripts/repository_preparation.py tests/test_delete_operation_lifecycle.py
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk git diff --check
rtk git diff --check 76b8d442f2452f943cc6ce03d0c9ecbe9f4d4c7c
rtk git diff --name-status 76b8d442f2452f943cc6ce03d0c9ecbe9f4d4c7c
rtk git status --short --branch
```

Expected: full suite and package validator exit 0, no whitespace errors, and only this plan plus the two approved implementation paths in the aggregate comparison. Capture final counts, skips, hashes, and terminal exit codes; partial output is not a pass. No changes after the frozen run unless a material defect is found; a relevant change invalidates affected evidence. Static/package checks do not establish native-Windows Delete behavior, live model behavior, installed-copy behavior, or production safety.

- [ ] **3. Prepare one bounded final review handoff if separately authorized.** Include exact parent/HEAD, final diff and changed-file hashes, RED/GREEN receipts, complete suite/package outputs, all exclusions, and platform limitations. Limit review to this defect and regressions caused by the two-file repair. Use at most one read-only reviewer, no recursive delegation or external transmission; do not dispatch any subagent under this planning authorization. Do not call a self-review independent. If independent review is not yet authorized, report it as outstanding without blocking the already authorized plan commit.

- [ ] **4. Commit implementation only if the future execution instruction authorizes it.** A suitable message is `Revalidate final Delete receipt content`. Verify only the two approved implementation paths are staged; preserve unrelated work. This plan's local commit does not grant implementation commit or publication authority.

```bash
rtk git diff --check
rtk git add -- skills/implementing-staged-plans/scripts/repository_preparation.py tests/test_delete_operation_lifecycle.py
rtk git diff --cached --name-status
rtk git diff --cached --check
rtk git commit --only -m "Revalidate final Delete receipt content" -- skills/implementing-staged-plans/scripts/repository_preparation.py tests/test_delete_operation_lifecycle.py
rtk git show --format=fuller --stat HEAD
rtk git rev-parse HEAD HEAD^
rtk git status --short --branch
```

- [ ] **5. Report evidence and stop.** Report the actual change, RED/GREEN observations, final suite/package exits and counts/skips, exact parent/head, review status, and any limitations. Do not push, update PR #18, reply to review, merge, reinstall, replay pipeFlow, or perform excluded work.

## Acceptance and recovery

Acceptance requires both transient content variants and absent validated receipt to produce an invalid direct assessment with a receipt-specific issue, no Delete binding, and complete ordered product states; the real reviewing path must reject with zero status writer calls and unchanged status, authority, source absence, retained source bytes, and original receipt bytes. Exact valid receipts and supported interrupted recovery must pass, and all five earlier reinspection controls must remain effective. Final focused/full-suite/package/diff evidence must refer to the actual implementation tree.

For a real divergent program, preserve all evidence and retained bytes. This repair does not rewrite receipt/status hashes, restore source names, or dispose of quarantine. Existing exact classifier/adoption behavior remains the authorized recovery mechanism; divergent evidence requires separately authorized reconciliation. If a candidate repair is rejected, preserve work and prepare a reverse diff for review instead of resetting the checkout.

## Planning verification receipts

Planning verification records below describe the plan and unmodified production only. They are not implementation GREEN or final full-suite evidence.

- Initial branch/HEAD/clean-state verification passed at the exact requested parent. No filesystem `AGENTS.md` was found in this worktree or its ancestor directories; the supplied instructions and `/Users/CoveMB/.codex/RTK.md` apply. GitHub comment retrieval succeeded through a read-only API call; no refs were fetched or external state changed.
- Both Python excerpts parsed successfully (the `elif` excerpt inside its required conditional context). Test methods were loaded directly from this Markdown into the existing test class in one disposable Python process; no production function or on-disk test was edited.
- Initial excerpt run: **10 test methods, 4 failures, 0 errors, 0 skips, exit 1**. Both transient content transition tests reached the real status writer exactly once and failed the zero-call assertion. Missing validated receipt completed reviewing without the required exception. All five prior transition fault controls and the valid canonical-receipt/authority control passed.
- The remaining initial failure was a plan-harness mistake: this production fixture has four Create states followed by Delete, not a trailing Preserve state. Corrected that assertion in the plan and reran only the affected direct-assessment method. **1 method, 3 intended subtest failures, 0 errors, 0 skips, exit 1**: malformed content, canonical/schema-valid wrong metadata, and missing validated receipt each still returned `valid=True`. The five earlier fault subcases passed with complete ordered-state equality. Harness failures are excluded from defect evidence.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` returned **Package validation passed, exit 0**. The plan is outside the runtime package surface. `rtk git diff --check` passed. All tracked files remained unchanged; SHA-256 checks confirmed the inspected repository-preparation, state-authority, activation, and lifecycle-test files still matched their initial bytes.
- The single-file/hash/staged-diff/parent verification accompanies the planning commit in the task receipt. No production GREEN, final implementation full suite, independent implementation review, native-Windows execution, installed-copy validation, or publication was performed or claimed. These remain future execution obligations.
