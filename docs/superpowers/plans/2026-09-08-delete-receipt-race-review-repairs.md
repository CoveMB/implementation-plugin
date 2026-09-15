# Delete Receipt Race Review Repairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This planning task permits only this new plan and its local commit; it prohibits implementation and subagents. Future execution requires a separate instruction.

**Goal:** Reject failed Delete receipt reinspection before status persistence, repair the wrong-mode regression fixture, and restore the documented manifest-v3 activation order.

**Architecture:** Keep receipt binding construction in `repository_preparation.validate_execution_workspace_v2`; convert inspection failures and absent/invalid digests into assessment issues before appending a binding. Reuse activation's existing `assessment.valid` barrier rather than adding a second writer or changing persistence. Isolate the mode test using the existing allocation helper, and correct only the runbook's ordered list.

**Tech Stack:** Existing Python 3 standard library, `unittest`, temporary Git fixtures, descriptor-relative no-follow inspection, canonical SHA-256 results, and status-last persistence. No dependencies, schemas, public interfaces, or version changes.

**Spec:** `docs/superpowers/plans/2026-09-05-delete-operation-support.md` supplies the PLUG-001 boundary and Delete invariants. `docs/superpowers/specs/2026-08-23-program-setup-and-activation-design.md` supplies setup/source-gate and status-last contracts. Read the current `skills/implementing-staged-plans/SKILL.md` and `skills/implementing-staged-plans/references/repository-preparation.md`; retain the preceding repairs recorded in `docs/superpowers/plans/2026-09-08-delete-activation-final-review-repairs.md`. Historical kickoff branches and checkboxes in those plans are context, not execution authority for this repair.

## Global constraints

- Reviewed production head: `b031fe442efc685f459f6b49a102767d6ede061b`; PR #18 base: `00c04a0f1c1ebb2cbdf890c4c4cf0334f89a344e`. The planning branch is `repair/delete-review-receipt-race-plan`; initial HEAD matched the reviewed head and status was clean. No remote refs were fetched; this is an immutable-head repair scope.
- Planning owns exactly this file. Do not edit production, tests, existing documents, manifests, versions, or other files during planning. Commit only this plan. Do not push, create a PR, merge, reinstall, replay pipeFlow, respond to review comments, or spawn subagents.
- Later execution must preserve all user-owned staged, unstaged, untracked, and committed work. Use the explicitly approved checkout/branch; do not invent branch names, reset, clean, stash, amend, or overwrite unrelated changes.
- Prefix every shell command with `rtk`. Commands below run from the repository root. Use `apply_patch` for edits and `rtk env PYTHONDONTWRITEBYTECODE=1` for Python; keep temporary fixtures and probes outside the package.
- Existing manifest/status v1 and v2, plus manifest-v3 programs using setup/envelope v1, retain their exact schemas, prompts, ordering, errors, and persisted bytes. The nested v2 family remains selected only by the exact supported setup/envelope pair.
- Delete means accepted absence of the exact product path with `sha256: null`, bound to a manifest-owned quarantine receipt that preserves the removed bytes. The **receipt** digest must be a valid SHA-256 string; it must never inherit the product tombstone's null-digest rule.
- Preserve normalized exact regular-file ownership, descriptor-relative no-follow inspection, held identities, mode/owner and hard-link checks, Git/program/control/quarantine protection, same-filesystem no-replace movement, immutable ledgers, compare-and-swap, and status-last ordering.
- Preserve `retry-ready`, `receipt-adoption-ready`, `resume`, and `recovery-required`, including exact interrupted-move adoption and the preceding repair's path-specific authority exceptions. Never weaken a classifier or accept divergent evidence to make a test pass.
- No PLUG-002 requirement attribution, semantic invalidation, terminal closure, quarantine disposal, automatic restoration, secure erasure, Move/Rename, Replace, directory deletion, broad refactoring, diagnostic cleanup, docstring expansion, manifest edits, or package version bump.
- This plan changes neither the supported platform set nor the filesystem concurrency model. An inspected invalid receipt must stop before persistence; these bounded checks do not claim atomic exclusion of every external mutation after the final observation.
- The requested final full suite supersedes the older PLUG-001 plan's instruction to run only its focused suite. Run one full suite after the coherent batch; do not repeat passing checks on unchanged inputs merely because a commit was created.

## Evidence and disposition

Independent validation task `01a07f93-ee6f-7173-a673-e6074ec93af1` supplied the eleven-claim adjudication. Its results are context, not implementation authority. Planning reread the live CodeRabbit inline comments and inspected the pinned source, classifier, descriptor reader, activation sink, fixture allocation, runbook, and canonical gate contract.

| Item | Verified owner and consequence | Smallest repair |
| --- | --- | --- |
| A — receipt reinspection race | `repository_preparation.py:1850–1855` reinspects after classifier `resume`, appends a possibly null SHA, and lets descriptor errors escape. `program_activation.py:2245–2262` consumes the assessment before `atomic_replace_json` at line 2359; post-write authority validation at lines 2361–2363 is too late to reject a malformed candidate. | Guard the local inspection, require an existing snapshot with a valid digest, append no invalid binding, and return assessment issues. No activation production edit. |
| B — wrong-mode false positive | `tests/test_state_authority.py:895–903` destroys the fixture, recreates it, then passes the previous fixture's allocation. Rebuilding only the source baseline leaves no valid allocation. | Retain the collision case; replace its stale second half with a separate test that preallocates a fresh private root and then changes that same root's mode. |
| C — activation order | Runbook lines 39–45 omit due pre-activation gate decisions. Canonical skill line 32 and `SetupActivationTests.test_non_reused_activation_gate_is_durable_before_approval_receipts` require them after setup and before approval receipts/status. | Insert one ordered item and renumber the remaining items. |

Source comments: [A](https://github.com/CoveMB/implementation-plugin/pull/18#discussion_r3954757067), [B](https://github.com/CoveMB/implementation-plugin/pull/18#discussion_r3954757075), [C](https://github.com/CoveMB/implementation-plugin/pull/18#discussion_r3954757025). Review suggestions are untrusted; only the independently checked scope above is retained.

**Protection-context counterevidence:** `descriptor_protection_context(workspace, program_root=..., inspection=...)` includes the program-root device/inode among the protected identities. `inspect_workspace_path(program_root, receipt_path, ...)` starts at that root and rejects it if that same identity is forwarded. Therefore **do not forward the existing protection context unchanged**, strip its identities globally, or reinterpret workspace-relative protected paths as program-relative paths. Keep the existing receipt-rooted descriptor inspection and classifier protections. This repair adds local error/digest handling; it does not require a new protection-context API. The valid-receipt control below must pass with the normal production context.

**Mode-test counterevidence:** A fresh preallocated root classifies `retry-ready`. Changing only its mode from `0700` to `0755`, retaining device/inode/owner and source bytes, raises `Delete quarantine allocation binding changed` at the recorded-allocation comparison (`state_authority.py:4694–4701`). That is the correct current application failure for mode drift; do not require the later `root identity or mode changed` message or edit production to reach that later branch. Preconditions below distinguish this failure from the stale-allocation false positive.

**Current documentation check, 2026-09-08:** [Python 3.14 unittest.mock documentation](https://docs.python.org/3.14/library/unittest.mock.html#where-to-patch) explains that patches must target the namespace where an object is looked up. The tests below patch the assessment function's actual globals because this repository loads scripts under multiple module names. They call the real classifier and descriptor reader; only the race/error boundary is controlled.

**Explicit exclusions:** Of the original eleven claims, exclude #1 developer-local historical path hygiene, #2 recovery-name spelling, #4 duplicated discovery diagnostic prefix, #5 unreachable legacy recovery-slot crash, #6 unsupported relaxation of legacy `candidate_sha256`, #7 setup-validator exception normalization without demonstrated new application failure, #10 v1/v2 parser diagnostic wording, and #11 rollover predicate diagnostic granularity. Do not reopen them during this repair. The CodeRabbit docstring threshold is not a repository requirement. PLUG-002, review replies, merge/reinstall/replay, and all other boundaries above remain excluded.

## Exact future change inventory

| Path | Responsibility |
| --- | --- |
| `skills/implementing-staged-plans/scripts/repository_preparation.py` | A only: local guard around receipt inspection and binding append in `validate_execution_workspace_v2`. |
| `tests/test_delete_operation_lifecycle.py` | A only: production-fixture assessment/transition regressions and valid-receipt control. |
| `tests/test_state_authority.py` | B only: remove stale wrong-mode half of collision test; add independently allocated mode-drift test. |
| `implementing-staged-plans-bootstrap-execution-review-runbook.md` | C only: manifest-v3 ordered activation list. |

All other files are read-only context, including `program_activation.py`, `state_authority.py`, shared fixtures, existing plans, package metadata, and version owners. No new implementation files or fixture framework are needed.

## Task 1 — Reject invalid receipt snapshots before persistence

**Files:** The A production owner and lifecycle test file from the inventory.

**Interfaces:** Keep `validate_execution_workspace_v2(program_root, baseline, inspection, *, increment_state, protected_paths=(), protected_identities=()) -> ExecutionWorkspaceAssessmentV2` unchanged. Invalid receipt reinspection produces `valid=False`, a receipt-specific issue, and no binding for that Delete path. Keep `advance_execution_state(program_root, target_increment_state, observation)` unchanged; its existing guard raises before the status writer.

- [ ] **1. Verify execution scope.** Read this plan and its contracts, then inspect current state. A later execution instruction must identify the approved worktree/branch; this plan's commit alone grants no implementation authority.

```bash
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git diff --name-status b031fe442efc685f459f6b49a102767d6ede061b
rtk git diff --cached --name-status
rtk proxy python3 --version
```

Expected: production still matches the pinned head, or a separately authorized change has been revalidated. The only pre-implementation addition should be this plan. Preserve unexpected work and resolve a material scope conflict before edits. Do not fetch for this fixed-head comparison.

- [ ] **2. Add these tests to `tests/test_delete_operation_lifecycle.py`.** Add `tempfile`, `contextmanager` from `contextlib`, and `replace` from `dataclasses` to the existing imports, then append this class. The fixture reaches implementing through production activation and quarantine writers; required Create outputs include the raw review reports. No status or receipt records are fabricated.

```python
class DeleteReceiptReinspectionTests(unittest.TestCase):
    def setUp(self):
        self.fixture, self.legacy_bytes = _authorized_delete_program_with_successor()
        self.addCleanup(self.fixture.close)
        self.root = self.fixture.program_root
        ACTIVATION.advance_execution_state(
            self.root, "implementing", _fresh_observation(self.fixture)
        )
        (self.fixture.repository / "archive-output.txt").write_text(
            "archive output\n", encoding="utf-8"
        )
        write_raw_review_reports(self.fixture.repository)
        self.baseline = ACTIVATION.execution_baseline_v2_from_value(
            json.loads(
                (self.root / "increments/ARCHIVE-INDEX/execution-baseline.json")
                .read_text(encoding="utf-8")
            )
        )
        self.binding = self.baseline.delete_quarantine_bindings[0]
        self.receipt_path = self.root / self.binding["receipt_path"]
        self.validate = ACTIVATION.validate_execution_workspace_v2

    def assess(self):
        inspection = ACTIVATION.inspect_repository(self.fixture.repository, self.fixture.head)
        normalized = ACTIVATION._without_owned_program_paths(self.root, inspection.observation)
        return self.validate(
            self.root,
            self.baseline,
            replace(inspection, observation=normalized),
            increment_state="reviewing",
        )

    @contextmanager
    def receipt_race(self, kind):
        namespace = self.validate.__globals__
        classify = namespace["classify_delete_quarantine_recovery"]
        inspect = namespace["inspect_workspace_path"]
        events = []
        with tempfile.TemporaryDirectory() as directory:
            saved = Path(directory) / "receipt.json"
            displaced = Path(directory) / "receipt-link"

            def classify_then_race(*args, **kwargs):
                recovery = classify(*args, **kwargs)
                if not events and recovery.disposition == "resume":
                    events.append("classified-resume")
                    if kind in {"missing", "symlink"}:
                        self.receipt_path.rename(saved)
                        if kind == "symlink":
                            self.receipt_path.symlink_to(saved)
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
                    if kind == "null-sha":
                        return replace(snapshot, sha256=None)
                    if kind == "invalid-sha":
                        return replace(snapshot, sha256="invalid")
                    return snapshot
                finally:
                    if saved.exists():
                        if self.receipt_path.is_symlink():
                            self.receipt_path.rename(displaced)
                        saved.rename(self.receipt_path)

            with mock.patch.dict(
                namespace,
                {
                    "classify_delete_quarantine_recovery": classify_then_race,
                    "inspect_workspace_path": inspect_receipt,
                },
            ):
                yield events

    def test_receipt_reinspection_failure_returns_invalid_assessment(self):
        for kind in ("missing", "symlink", "oserror", "null-sha", "invalid-sha"):
            with self.subTest(kind=kind):
                before = repository_snapshot(self.fixture.repository)
                with self.receipt_race(kind) as events:
                    assessment = self.assess()
                self.assertEqual(events, ["classified-resume", "reinspected"])
                self.assertFalse(assessment.valid)
                self.assertTrue(any(
                    issue.startswith("Delete quarantine receipt ")
                    for issue in assessment.issues
                ), assessment.issues)
                self.assertEqual(assessment.product_states.delete_quarantine_bindings, ())
                self.assertEqual(repository_snapshot(self.fixture.repository), before)

    def assert_reviewing_rejected(self, kind):
        status_path = self.root / "state/status.json"
        before_status = status_path.read_bytes()
        before = repository_snapshot(self.fixture.repository)
        with self.receipt_race(kind) as events:
            with mock.patch.object(
                ACTIVATION, "atomic_replace_json",
                wraps=ACTIVATION.atomic_replace_json,
            ) as writer:
                with self.assertRaises(ValueError) as raised:
                    ACTIVATION.advance_execution_state(
                        self.root, "reviewing", _fresh_observation(self.fixture)
                    )
                writer.assert_not_called()
        self.assertIn("Delete quarantine receipt ", str(raised.exception))
        self.assertEqual(events, ["classified-resume", "reinspected"])
        self.assertEqual(status_path.read_bytes(), before_status)
        self.assertEqual(repository_snapshot(self.fixture.repository), before)
        self.assertFalse((self.fixture.repository / "legacy.ts").exists())
        self.assertEqual(
            (self.root / self.binding["entry_path"]).read_bytes(),
            self.legacy_bytes,
        )

    def test_missing_receipt_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("missing")

    def test_symlink_receipt_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("symlink")

    def test_receipt_oserror_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("oserror")

    def test_null_receipt_sha_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("null-sha")

    def test_invalid_receipt_sha_blocks_reviewing_before_status_write(self):
        self.assert_reviewing_rejected("invalid-sha")

    def test_valid_receipt_keeps_exact_digest_and_reviewing_transition(self):
        receipt_bytes = self.receipt_path.read_bytes()
        expected_digest = hashlib.sha256(receipt_bytes).hexdigest()
        assessment = self.assess()
        self.assertTrue(assessment.valid, assessment.issues)
        expected_bindings = ({
            "path": "legacy.ts",
            "receipt_path": self.binding["receipt_path"],
            "receipt_sha256": expected_digest,
        },)
        self.assertEqual(assessment.product_states.delete_quarantine_bindings, expected_bindings)
        prior = json.loads((self.root / "state/status.json").read_text())
        transition = ACTIVATION.advance_execution_state(
            self.root, "reviewing", _fresh_observation(self.fixture)
        )
        status = json.loads((self.root / "state/status.json").read_text())
        self.assertEqual(transition.increment_state, "reviewing")
        self.assertEqual(status["state_sequence"], prior["state_sequence"] + 1)
        result = status["execution_transition_binding"]["product_path_states"]
        self.assertEqual(result["delete_quarantine_bindings"], list(expected_bindings))
        tombstone = next(row for row in result["ordered_path_states"] if row["path"] == "legacy.ts")
        self.assertFalse(tombstone["exists"])
        self.assertIsNone(tombstone["sha256"])
        self.assertEqual(self.receipt_path.read_bytes(), receipt_bytes)
        self.assertEqual((self.root / self.binding["entry_path"]).read_bytes(), self.legacy_bytes)
        self.assertEqual(
            ACTIVATION.validate_state_authority(
                self.root,
                ACTIVATION._without_owned_program_paths(
                    self.root, _fresh_observation(self.fixture)
                ),
            ), []
        )
```

The transient missing/symlink races occur **after real successful classification**. The wrapper restores the original receipt after the descriptor read, preserving its bytes and identity. This ensures a later fresh authority read cannot mask the invalid candidate produced by the earlier assessment. Each transition variant gets its own fresh fixture so one bad status write cannot contaminate another RED. Direct assessment uses activation's existing owned-program-path normalization, including retained publication staging paths. Null/invalid digest cases inject only the descriptor-result boundary; they do not mock the classifier or assessment. The OSError case checks the promised assessment error contract. The valid control prevents an unconditional failure or incorrect protection-context forwarding from passing the negative tests.

- [ ] **3. Run RED before production changes.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle.DeleteReceiptReinspectionTests -v
```

Expected: the valid control passes. Missing/null/invalid SHA assessment cases fail because the current assessment accepts them. Unsafe symlink and OSError cases escape assessment. Transition variants fail because status is written or the error lacks the receipt-specific assessment issue; OSError escapes the expected ValueError contract. Loader errors, missing fixture outputs, or unmapped publication staging paths do not count as RED. Record actual failure text before the production edit.

- [ ] **4. Replace only the existing receipt-snapshot-and-append block inside the `resume` branch with this code.** Reuse the module's existing `_SHA256` validator. Keep the preceding classifier and subsequent product-state assembly unchanged.

```python
                    try:
                        receipt_snapshot = inspect_workspace_path(
                            program_root,
                            str(binding["receipt_path"]),
                        )
                    except (OSError, ValueError) as error:
                        issues.append(
                            f"Delete quarantine receipt inspection failed: {relative} ({error})"
                        )
                    else:
                        if (
                            not receipt_snapshot.exists
                            or not isinstance(receipt_snapshot.sha256, str)
                            or not _SHA256.fullmatch(receipt_snapshot.sha256)
                        ):
                            issues.append(
                                f"Delete quarantine receipt is missing or invalid: {relative}"
                            )
                        else:
                            bindings.append({
                                "path": relative,
                                "receipt_path": binding["receipt_path"],
                                "receipt_sha256": receipt_snapshot.sha256,
                            })
```

Do not use `continue` to skip the path-state append; preserve the assessment's complete ordered inventory even when invalid. Do not catch errors around the whole validator, return a fabricated valid product result, loosen parsers, add post-write rollback, or change activation. The existing final missing-binding diagnostic may accompany the new inspection issue and remains useful.

- [ ] **5. Run GREEN and the focused application contract checks.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle.DeleteReceiptReinspectionTests tests.test_repository_preparation.ExecutionWorkspaceValidationTests tests.test_repository_preparation.ExecutionV2ContractTests -v
```

Expected: all executed cases pass. Failures leave exact status bytes/sequence, authority ledgers, product files, receipt bytes, and retained quarantine bytes unchanged. The valid transition persists a real receipt SHA and a null product tombstone SHA, then passes authority validation. This is one bounded production/test deliverable; inspect its diff before moving on. Keep implementation commits pending until the final verification step unless a separate execution instruction explicitly authorizes intermediate commits.

## Task 2 — Make the wrong-mode test exercise a valid allocation

**Files:** Only `tests/test_state_authority.py`.

**Interfaces:** Reuse `DeleteQuarantineTests.allocate(baseline)`, `classify_delete_quarantine_recovery(...)`, and `quarantine_bound_regular_file(...)`. No production changes or new fixture helpers.

- [ ] **1. Expose the false-positive fixture with RED.** In the current collision test's second half, insert this precondition immediately after `self.setUp()` and before creating the manual root. Keep its existing local `baseline` for this RED run.

```python
        self.assertEqual(
            AUTHORITY.classify_delete_quarantine_recovery(
                self.program_root, self.workspace, "legacy.ts", baseline
            ).disposition,
            "retry-ready",
        )
```

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority.DeleteQuarantineTests.test_quarantine_destination_collision_fails_without_replacing_bytes -v
```

Expected RED: the supposed starting allocation is `recovery-required`, not `retry-ready`. This test-only repair has a fixture-precondition RED; do not deliberately break a working production mode check to manufacture failure.

- [ ] **2. Preserve the collision case and replace its stale second half.** Remove that test's block from `shutil.rmtree(self.workspace)` through its final source-byte assertion, including the temporary RED precondition. Add this separate method to the same class. Its normal `setUp` supplies a fresh source and baseline; `allocate` supplies the same root later changed to `0755`.

```python
    def test_preallocated_quarantine_mode_drift_fails_before_move(self) -> None:
        baseline = {
            **self.baseline.__dict__,
            "program_id": "DELETE-PROGRAM",
            "program_revision": 7,
            "increment_id": "DELETE-1",
        }
        allocation = self.allocate(baseline)
        root = self.program_root / allocation.root_path
        original = root.stat()
        source_bytes = self.target.read_bytes()
        self.assertEqual(original.st_mode & 0o777, 0o700)
        self.assertEqual(
            AUTHORITY.classify_delete_quarantine_recovery(
                self.program_root, self.workspace, "legacy.ts", baseline
            ).disposition,
            "retry-ready",
        )

        root.chmod(0o755)
        changed = root.stat()
        self.assertEqual(changed.st_mode & 0o777, 0o755)
        self.assertEqual(
            (changed.st_dev, changed.st_ino, changed.st_uid),
            (original.st_dev, original.st_ino, original.st_uid),
        )
        with self.assertRaisesRegex(
            ValueError, "^Delete quarantine allocation binding changed$"
        ):
            AUTHORITY.quarantine_bound_regular_file(
                self.program_root, self.workspace, "legacy.ts", baseline
            )
        self.assertEqual(self.target.read_bytes(), source_bytes)
        self.assertEqual(source_bytes, b"bytes retained by quarantine\n")
        self.assertEqual(
            AUTHORITY.inspect_workspace_path(self.workspace, "legacy.ts"), self.baseline
        )
        self.assertFalse((self.program_root / allocation.quarantine_path).exists())
        self.assertFalse((self.program_root / allocation.receipt_path).exists())
```

- [ ] **3. Run GREEN for both distinct protections and the related quarantine cases.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority.DeleteQuarantineTests -v
```

Expected: the collision test still preserves attacker destination bytes and source bytes. The new mode test proves valid allocation before a mode-only change, then rejection without a product move or receipt. Existing symlink, relocation/race, unsupported primitive, interruption, and no-data-loss tests remain intact. No production mode/error changes are permitted to satisfy this task.

## Task 3 — Restore the manifest-v3 activation record order

**Files:** Only `implementing-staged-plans-bootstrap-execution-review-runbook.md`, the ordered list under “Activate a Generated Program.”

**Interfaces:** Documentation only. Canonical gate decisions, approval records, status fields, and first-start behavior do not change.

- [ ] **1. Confirm the existing application gate test.** Read the canonical skill's activation paragraph and this existing test, then run it once:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_setup.SetupActivationTests.test_non_reused_activation_gate_is_durable_before_approval_receipts -v
```

Expected: PASS. It proves an unsatisfied non-reused gate leaves approval receipts empty and status awaiting approval, then a persisted gate permits activation. The defect is documentary omission, so no source-text assertion or artificial failing application test is warranted.

- [ ] **2. Replace the four-item list with exactly this sequence.** Keep its introduction and the following semantic-handoff/legacy-v2 paragraph unchanged.

```markdown
1. setup decision;
2. any due pre-activation gate decisions;
3. program approval;
4. workspace-selection approval; and
5. active/awaiting-first-increment status last.
```

- [ ] **3. Verify the narrow diff and existing documentation contracts.**

```bash
rtk git diff -- implementing-staged-plans-bootstrap-execution-review-runbook.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation -v
```

Expected: only the ordered item/numbering changes, and documentation checks pass. Manual comparison with the canonical owner verifies the wording; these checks do not themselves prove gate enforcement.

## Final verification and bounded handoff

- [ ] **1. Make one requirement and DRY pass.** Map A/B/C to the four-file inventory. Confirm the receipt guard cannot append null/invalid digests or skip product-state collection; the production sink is unchanged; mode drift starts from a real allocation; the runbook has the exact gate order. Remove only newly introduced unnecessary flexibility. Preserve all eight excluded claims and preceding Delete repairs without editing them.

- [ ] **2. Run one final full suite, package validation, and whitespace/scope checks after all three tasks.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk git diff --check
rtk git diff --check b031fe442efc685f459f6b49a102767d6ede061b
rtk git diff --name-status b031fe442efc685f459f6b49a102767d6ede061b
rtk git status --short --branch
```

Expected: terminal exit 0 with actual counts/skips recorded, package validation success, no whitespace errors, and only this plan plus the four approved implementation paths in the aggregate diff. The full suite includes legacy v1/v2, setup/envelope-v1, typed Delete, interrupted adoption, prior activation authority exceptions, review-hash binding, rollover, and discovery coverage. Inspect results rather than copying historical counts. Do not compare/install a plugin or start hosted jobs. Disclose native-Windows or other platform tests that were skipped; local Darwin Delete tests do not establish additional platform support.

- [ ] **3. Freeze the exact final review scope.** Record HEAD, the worktree/index diff against the reviewed head, changed-path inventory, RED/GREEN receipts, full-suite and package results, and platform limitations. No subagents are authorized by this planning task. If later execution authorizes an independent reviewer, use at most one bounded read-only final reviewer for A/B/C and regressions caused by them, with no recursive delegation or external source transmission. Otherwise leave that independent review outstanding for the user rather than silently spawning one. Do not label a self-review independent or repeatedly review unchanged code.

- [ ] **4. Commit the coherent implementation only if the future execution instruction authorizes it.** Confirm no unrelated staged work is included; use the exact four approved paths. A suitable concise message is `Reject invalid Delete receipt bindings`. This plan authorizes no implementation commit on its own.

```bash
rtk git diff --check
rtk git add -- skills/implementing-staged-plans/scripts/repository_preparation.py tests/test_delete_operation_lifecycle.py tests/test_state_authority.py implementing-staged-plans-bootstrap-execution-review-runbook.md
rtk git diff --cached --name-status
rtk git commit --only -m "Reject invalid Delete receipt bindings" -- skills/implementing-staged-plans/scripts/repository_preparation.py tests/test_delete_operation_lifecycle.py tests/test_state_authority.py implementing-staged-plans-bootstrap-execution-review-runbook.md
rtk git show --format=fuller --stat HEAD
rtk git rev-parse HEAD HEAD^
rtk git status --short --branch
```

- [ ] **5. Report and stop at the authorized boundary.** Report exact changed paths, head/parent, RED/GREEN failures and passes, final suite/package results, independent review status, and limitations. If a required check or review is outstanding, state it. No push, PR, merge, reinstall, pipeFlow replay, comment replies, or PLUG-002 work follows automatically.

## Recovery and acceptance criteria

The implementation is complete only when failed reinspection returns an invalid assessment with no invalid receipt binding; reviewing transitions reject before status persistence; successful transitions retain their exact valid bindings; mode-only quarantine drift rejects while preserving the source and empty destinations; the activation list agrees with its canonical owner; and the required final checks pass on the actual candidate.

Keep real program evidence intact on failure. Do not rewrite receipt/status hashes, dispose of quarantine, recreate product files, or clean a divergent transaction. Existing exact recovery classification/adoption remains the only previously authorized recovery mechanism; a divergent real program needs separately authorized reconciliation. For a rejected code change, preserve work and prepare a reverse diff for review instead of resetting the checkout.

Planning verification receipts are recorded below; they are not future GREEN or full-suite results.

### Planning verification receipts — 2026-09-08

- Planning ran on Darwin with Python 3.14.6. The reviewed production files remained unchanged. No filesystem `AGENTS.md` was found in this worktree or its ancestor directories; the supplied user instructions and `/Users/CoveMB/.codex/RTK.md` governed the task.
- All four Python excerpts parsed successfully using `ast.parse(textwrap.dedent(block))`. The lifecycle class was executed directly from this Markdown with the existing test module's imports plus the three specified imports, without writing a test file or modifying a production function.
- Final A excerpt run: **7 test methods, 7 assertion failures and 3 errors across the negative cases, 0 skips; valid-receipt control passed.** Each missing/null/invalid-SHA transition reached `atomic_replace_json` once, failing `writer.assert_not_called()`. Direct assessments incorrectly returned valid; symlink and injected OSError escaped the assessment. These are expected RED observations of the pinned defect, not a passing suite.
- B excerpt checks: the strengthened original fixture failed once with `recovery-required != retry-ready`; the corrected standalone fresh-allocation test passed once against unchanged production. The mode-only probe retained the same device/inode/owner and source bytes and raised `Delete quarantine allocation binding changed`.
- The existing gate application test passed: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_setup.SetupActivationTests.test_non_reused_activation_gate_is_durable_before_approval_receipts -v` — **1 test, exit 0**.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` — **Package validation passed, exit 0**. This checks the current package; the added plan is outside its runtime surface.
- Initial exploratory harnesses exposed a candidate-versus-published-root mistake, missing raw-review Create outputs, and missing owned-program-path normalization. Those harness issues were corrected in the final excerpts, and only the changed A harness was rerun. They are not counted as defect evidence or passing checks.
- No production GREEN, final full suite, native-Windows execution, independent final implementation review, merge, or installed-copy validation was performed during planning. Those claims remain unavailable until separately authorized execution and its required checks.
