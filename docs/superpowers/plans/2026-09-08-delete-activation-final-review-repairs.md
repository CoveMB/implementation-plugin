# Delete Activation Final Review Repairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This planning task prohibits subagents and production repairs. Future implementation and fresh independent review require a separate execution instruction.

**Goal:** Repair the three revalidated Delete lifecycle defects without changing v1 records, public interfaces, or the PLUG-001 ownership boundary.

**Architecture:** Guard the existing Darwin rename-symbol initialization at its owner. Bind completed v2 rollover review bytes to both the retained disposition and its unique approval. Replace activation's substring exclusion with an exact, path-bound exception for independently classified interrupted Delete moves; all other authority issues remain blocking before a move or receipt adoption.

**Tech Stack:** Existing Python 3 standard library, `unittest`, subprocesses, temporary Git repositories, canonical JSON/SHA-256, descriptor-relative filesystem inspection, and status-last persistence. No new dependencies, schemas, CLI switches, or production files.

**Spec:** The bounded repair request is reproduced in the scope and acceptance criteria below. The controlling PLUG-001 contract is `docs/superpowers/plans/2026-09-05-delete-operation-support.md`, especially its Boundary, Tasks 2–4, security invariants, and completion limits. `docs/superpowers/specs/2026-08-23-program-setup-and-activation-design.md` supplies the existing setup/activation contract. Read both before execution; historical implementation checkboxes do not authorize additional work.

## Global constraints and authority

- Planning source: independent review task `01a07f27-0244-7191-b540-eed968f318bb`, reviewed head `a3168c367633c960534d84bb47d1632123c1ea24`, base `00c04a0f1c1ebb2cbdf890c4c4cf0334f89a344e`.
- Revalidation checkout: `/Users/CoveMB/.codex/worktrees/c034/implementation-plugin`, clean detached HEAD at that exact head. Local `origin/main` resolved to the exact base. Remote refs were not refreshed: the requested comparison is immutable and local.
- This task authorizes one new plan file and a local commit containing only that file. It does not authorize production/test edits, execution of this implementation plan, push, PR creation, review-comment replies, or subagent dispatch.
- During later execution, preserve staged, unstaged, untracked, and committed user work. Inspect branch/status before Git work; use the approved checkout, do not invent a branch, stash, reset, clean, amend, or overwrite user changes. Local implementation commits below are boundaries for the future execution authorization, not authorization supplied by this document itself.
- Commands below run from the repository root. Prefix shell commands with `rtk`; use `rtk env PYTHONDONTWRITEBYTECODE=1` for Python. Use `apply_patch` for edits. Do not write bytecode or temporary probes into the package.
- Keep setup/envelope family selection exact: `implementation-program-setup-semantics/v2` with `implementation-operation-envelope/v2`. Do not reinterpret persisted family hints. Preserve v1 constructors, canonical record bytes, field order, prompts, routes, and failure behavior.
- Keep Delete as exact normalized regular-file absence with null digest, bound to the manifest-owned receipt and retained bytes. Preserve descriptor-relative no-follow inspection, identity/mode/owner checks, hard-link/protected-path rejection, same-filesystem no-replace movement, and status-last publication.
- Preserve the precise recovery classes: `retry-ready`, `receipt-adoption-ready`, `resume`, and `recovery-required`. Never turn a malformed prefix or a divergent source/quarantine/receipt into valid recovery.
- Unsupported Delete primitives must stop with `descriptor-relative no-follow Delete quarantine is unsupported on this platform`. No path-based fallback, copy-and-delete, replacement rename, cross-device move, or new Windows/Linux Delete backend.
- No PLUG-002 requirement ownership, requirement-result evidence, later-increment semantic invalidation, complete-chain closure, quarantine disposal, secure erasure, automatic restoration, broad refactoring, API redesign, package version bump, or unrelated cleanup.
- A local simulator cannot establish native-Windows behavior. Keep the native-Windows limitation and skipped tests visible in the final receipt. Do not start hosted jobs or transmit source for external review without separate authorization.

## Revalidation and bounded disposition

Revalidation used unmodified production modules and temporary fixture repositories on macOS (`sys.platform == "darwin"`), Python 3.14.6. All three findings are retained, with the following limits. These are defect probes, not evidence that the future repairs pass. The full suite and package validator were not rerun for this plan-only task.

Planning validation also parsed all seven Python code blocks and resolved every unittest selector against existing definitions or the test definitions below. The test excerpts were executed without installing them in the repository: six F2 rebinding variants were accepted unexpectedly, both F3 trigger filenames reached movement, and the F3 receipt-prefix case reached adoption. The F1 simulator initially exposed a test-harness `_winapi` import error; after preloading native standard-library backends, both platform variants failed at the intended `CDLL` `TypeError`. Only that changed excerpt was rerun. No repair was applied and no GREEN result is claimed.

### F1 — Non-Darwin imports depend on a Darwin rename library

**Owner:** `skills/implementing-staged-plans/scripts/state_authority.py:21–32`, module initialization; `_rename_without_replacement` at line 4582 consumes `_RENAMEATX_NP`. `program_discovery.py` imports this authority chain before choosing a program family.

**Verified:** Module import calls `_ctypes.CDLL(None, use_errno=True)` unconditionally, before `_WINDOWS` and the named-mutex backend are selected. A fresh-process import of `program_discovery` with `ctypes.CDLL` raising the Windows loader's `TypeError` failed at that import. This affects entry-point availability independently of whether the selected program uses Delete.

**Current primary-source check, 2026-09-08:** [CPython 3.13 Windows loader](https://github.com/python/cpython/blob/3.13/Modules/_ctypes/callproc.c#L1296-L1303) parses a Unicode library name; its POSIX loader separately permits `None`. [Python ctypes documentation](https://docs.python.org/3/library/ctypes.html#loading-shared-libraries) describes the platform-specific loaders. These support the import-risk finding; native Windows was not executed here. The simulated exception is evidence of propagation through the application import path, not a native-Windows test.

**Narrow repair:** Initialize the optional `renameatx_np` library only on Darwin. Keep the current signature setup and unavailable-symbol fail-closed path. Do not redesign locking or assert that guarding this import implements Delete on Windows or Linux.

### F2 — Completed v2 rollover loses review approval hash binding

**Owner:** `skills/implementing-staged-plans/scripts/program_rollover.py`, `_validated_completed_rollover_records`, v2 branch around lines 1692–1840. Public `validated_inherited_paths` reaches it through `_validated_inherited_paths`. `validate_state_authority` and fresh-process discovery consume this chain.

**Verified executable probe:** `_complete_delete_rollover()` produced an accepted Delete and successor using production writers. The probe changed `review_packet.changes_and_rationale` in retained evidence, rendered its matching packet through `review_coordination.render_review_packet`, and verified `validate_review_bundle(...) == []`. It updated the current file digests in both rollover-level and embedded `accepted_diff_binding` review bindings, then rebound the status's rollover-row digest. It left the approval log and disposition's approved review hashes untouched.

Observed result: `approval_bytes_unchanged: true`, `authority_issues: []`, discovery `disposition: "resume"`, `stop_required: false`, `issues: []`. Existing tests detect changed files when their recorded digests are stale; they do not cover this coordinated rebinding.

**Narrow repair:** Compare the freshly retained evidence/packet hashes with the exact hashes already carried by the disposition and the unique, canonically hashed approval. Apply only inside the v2 completed-history branch, for both `accept-continue` and `accept-stop` followed by later continuation. This is consistency validation inside the existing local authority model; it does not make fully rewritten local authority cryptographically unforgeable.

### F3 — Filename text controls whether pre-mutation authority failures block

**Owner:** `skills/implementing-staged-plans/scripts/program_activation.py`, `advance_execution_state`, lines 2200–2226. The legitimate recovery-only warning originates in `repository_preparation.validate_execution_workspace_v2`, lines 1838–1846, because persisted status is still `authorized` after an interrupted move.

**Verified executable probe:** Create an authorized Delete through `_authorized_delete_program_with_successor()`, add one unmapped file, and call the real `advance_execution_state(root, "implementing", fresh_observation)`.

| Unmapped filename | Raised error | Source after rejection | Quarantine | Status |
| --- | --- | --- | --- | --- |
| `unmapped.txt` | `execution workspace has unmapped dirty paths: unmapped.txt` | Present | No entry | Unchanged, authorized |
| `unmapped-Delete.txt` | Same error with that filename | Absent | Original bytes retained | Unchanged, authorized |
| `unmapped-quarantine.txt` | Same error with that filename | Absent | Original bytes retained | Unchanged, authorized |

**Narrow repair:** Do not remove recovery support. The existing classifier independently validates exact baseline/source/quarantine/receipt state. Exempt only the complete authorized-source warning for an exact Delete path whose classification is `receipt-adoption-ready` or `resume`. Do not exempt anything for `retry-ready`, any inspection failure, generic Delete/quarantine text, or a different path. This does not promise atomicity across multiple files or automatic rollback after an actual filesystem race; it restores the pre-mutation authority barrier for observed invalid input.

**Recovery counterprobe:** Interrupting the production receipt writer after movement and interrupting the production status writer after receipt publication each left exactly `authorized Delete source does not match baseline: legacy.ts` as the authority issue. Both exact retries reached `implementing` on the original code. These observations constrain the exception to one complete diagnostic and protect against an overbroad repair that simply rejects every interrupted move.

## Exact change inventory

| File | Responsibility and permitted changes |
| --- | --- |
| `skills/implementing-staged-plans/scripts/state_authority.py` | F1 only: guard existing library initialization; keep public functions and record formats unchanged. |
| `tests/test_state_authority.py` | F1 fresh-process import/legacy-reader regression; use existing mutex, unsupported-primitives, descriptor, and native-Windows tests for related coverage. |
| `skills/implementing-staged-plans/scripts/program_rollover.py` | F2 only: review-hash consistency inside `_validated_completed_rollover_records` v2 completed-chain branch. |
| `skills/implementing-staged-plans/scripts/program_activation.py` | F3 only: replace broad issue substring exclusion in `advance_execution_state`. |
| `tests/test_delete_operation_lifecycle.py` | F2 production-generated completed-chain rebinding matrix; F3 real execution-transition no-mutation and interrupted-recovery regressions. Reuse existing fixtures. |

Read-only context: `tests/program_bootstrap_support.py`, `tests/script_module_support.py`, `tests/test_program_activation.py`, `tests/test_program_discovery.py`, `tests/test_program_rollover.py`, `tests/test_program_continuation.py`, `tests/test_multi_increment_lifecycle.py`, `repository_preparation.py`, `diff_disposition.py`, `program_continuation.py`, `program_discovery.py`, `review_coordination.py`, and `docs/maintainers.md`. Script basenames in this paragraph are under `skills/implementing-staged-plans/scripts/`. These are not additional write authority. No production helper extraction or test-fixture redesign is needed.

## Task 1 — Isolate the Darwin-only import without changing legacy behavior

**Files:** Modify `state_authority.py` and `tests/test_state_authority.py` from the inventory above.

**Interfaces:** `_RENAMEATX_NP` remains a ctypes callable or `None`; `_rename_without_replacement(...) -> None` keeps its signature and current unsupported error. `validate_state_authority(program_root, observation) -> list[str]` remains unchanged. Later tasks consume no new interface.

- [ ] **1. Record execution preflight.** Read the controlling plan/spec and this plan. Verify current checkout and proposed changes before editing:

```bash
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git diff --name-status
rtk git diff --cached --name-status
rtk proxy python3 --version
```

Expected: the three production owners still match the revalidated head, or only previously completed tasks in this plan have changed them. A new implementation head requires revalidation before proceeding. Preserve any unrelated changes; do not assume a clean index. Do not fetch solely for this fixed-head repair.

- [ ] **2. Add this application import/legacy-reader regression.** Add `subprocess`, `sys`, and `textwrap` imports to `tests/test_state_authority.py` and append this test class. The subprocess prevents already-loaded modules from hiding the import defect. It mocks the loader boundary only, then executes the existing real v1 authority test and imports production entry points. `os.name` is deliberately left native; this is not a simulated Windows filesystem or mutex certification.

```python
class PlatformImportCompatibilityTests(unittest.TestCase):
    def test_non_darwin_imports_keep_legacy_authority_available(self) -> None:
        script = textwrap.dedent("""
            import ctypes
            import pathlib
            import shutil
            import subprocess
            import sys
            import tempfile
            import unittest
            from unittest import mock

            # Initialize native standard-library backends before spoofing only
            # the optional application library-selection condition.
            selected_platform = sys.argv[1]
            sys.path.insert(0, sys.argv[2])
            with mock.patch.object(sys, "platform", selected_platform):
                with mock.patch.object(
                    ctypes, "CDLL",
                    side_effect=TypeError("Windows loader requires a string"),
                ) as loader:
                    from tests.test_state_authority import WorkspaceAndBindingTests
                    import program_discovery
                    import program_activation
                    suite = unittest.TestSuite([
                        WorkspaceAndBindingTests(
                            "test_valid_state_authority_and_workspace_pass"
                        )
                    ])
                    result = unittest.TextTestRunner(verbosity=2).run(suite)
                    loader.assert_not_called()
                    if not result.wasSuccessful():
                        raise SystemExit(1)
        """)
        for selected_platform in ("win32", "linux"):
            with self.subTest(platform=selected_platform):
                completed = subprocess.run(
                    [sys.executable, "-c", script, selected_platform, str(SCRIPT_ROOT)],
                    cwd=REPOSITORY_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(
                    completed.returncode, 0,
                    completed.stdout + completed.stderr,
                )
```

- [ ] **3. Run RED.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority.PlatformImportCompatibilityTests -v
```

Expected on the original head: both subtests fail because a fresh authority import invokes `CDLL` and raises `TypeError`. A missing import, broken test fixture, or collection error is not the intended RED; repair the test harness before touching production.

- [ ] **4. Make the smallest production change.** Replace only the `_LIBC` assignment; retain `getattr(_LIBC, "renameatx_np", None)`, argtypes, restype, `_RENAME_EXCL`, and all mutex code as they are:

```python
_LIBC = _ctypes.CDLL(None, use_errno=True) if sys.platform == "darwin" else None
```

No exception swallowing is required to repair the Windows claim: the unsupported platform must never call this loader. Darwin loader failures remain visible, and a missing symbol still causes the existing unsupported-operation stop.

- [ ] **5. Run GREEN and focused compatibility.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority.PlatformImportCompatibilityTests tests.test_state_authority.WorkspaceAndBindingTests tests.test_state_authority.AtomicAuthorityWriterTests tests.test_state_authority.DescriptorRelativeWorkspacePathTests tests.test_state_authority.DeleteQuarantineTests -v
```

Expected on macOS: all executed tests pass; the existing native-Windows-only test is visibly skipped. The real Delete movement and collision tests exercise the preserved Darwin callable; mocks do not substitute for those passes.

- [ ] **6. Commit this coherent change if execution authority includes local commits.** Review only these files and ensure no unrelated staged work is included:

```bash
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/state_authority.py tests/test_state_authority.py
rtk git add -- skills/implementing-staged-plans/scripts/state_authority.py tests/test_state_authority.py
rtk git diff --cached --name-status
rtk git commit --only -m "fix: isolate Darwin Delete loader initialization" -- skills/implementing-staged-plans/scripts/state_authority.py tests/test_state_authority.py
```

Expected commit scope: exactly the two listed files. Record full commit ID, test command, exit status, pass count, and skips. Otherwise leave the reviewed changes uncommitted at the authorized gate.

## Task 2 — Bind retained review files to the completed rollover approval

**Files:** Modify `program_rollover.py` and `tests/test_delete_operation_lifecycle.py` from the inventory.

**Interfaces:** `_validated_completed_rollover_records(program_root, status, *, allow_unbound_suffix) -> tuple[dict[str, object], ...]` keeps its existing signature and result. It raises `ValueError` on inconsistency; `_validated_inherited_paths`, `validated_inherited_paths`, `validate_state_authority`, and discovery retain their existing routing/error contracts. No new fields or writers.

- [ ] **1. Add the complete rebinding regression below** to `DeleteOperationLifecycleTests`. Add `import copy` at the top. This starts from a real accepted rollover; negative variants alter retained artifacts only after production has generated them. Keep the existing copied-file and approval-tampering tests.

```python
def test_completed_rollover_binds_review_hashes_to_approval_and_disposition(self):
    fixture, legacy_bytes, allocation, _receipt = _complete_delete_rollover()
    try:
        root = fixture.program_root
        status_path = root / "state/status.json"
        rows_path = root / "state/rollovers.jsonl"
        approvals_path = root / "state/approvals.jsonl"
        original_status = json.loads(status_path.read_text())
        original_rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
        original_row = original_rows[-1]
        evidence_path = root / original_row["review_evidence_binding"]["path"]
        packet_path = root / original_row["review_packet_binding"]["path"]
        originals = {
            path: path.read_bytes()
            for path in (status_path, rows_path, approvals_path, evidence_path, packet_path)
        }
        cases = (
            "replace-bundle",
            "replace-bundle-and-disposition",
            "disposition-evidence",
            "disposition-packet",
            "approval-evidence",
            "approval-packet",
        )
        for case in cases:
            with self.subTest(case=case):
                try:
                    status = copy.deepcopy(original_status)
                    rows = copy.deepcopy(original_rows)
                    row = rows[-1]
                    accepted = row["accepted_diff_binding"]
                    disposition = accepted["diff_disposition_binding"]
                    if case.startswith("replace-bundle"):
                        import review_coordination as coordination

                        evidence = json.loads(originals[evidence_path])
                        evidence["review_packet"]["changes_and_rationale"] = [
                            "Replacement created after the retained approval."
                        ]
                        packet = coordination.ReviewPacket(
                            **coordination._tuple_fields(
                                evidence["review_packet"], coordination.PACKET_FIELDS
                            )
                        )
                        packet_text = coordination.render_review_packet(packet)
                        self.assertEqual(
                            coordination.validate_review_bundle(evidence, packet_text), []
                        )
                        evidence_path.write_bytes(ACTIVATION._canonical_json_bytes(evidence))
                        packet_path.write_text(packet_text, encoding="utf-8")
                        for stem, path in (("review_evidence", evidence_path),
                                           ("review_packet", packet_path)):
                            digest = hashlib.sha256(path.read_bytes()).hexdigest()
                            row[stem + "_binding"]["sha256"] = digest
                            accepted[stem + "_binding"]["sha256"] = digest
                            if case == "replace-bundle-and-disposition":
                                disposition[stem + "_sha256"] = digest
                        self.assertEqual(approvals_path.read_bytes(), originals[approvals_path])
                    elif case.startswith("disposition-"):
                        stem = "review_evidence" if case.endswith("evidence") else "review_packet"
                        disposition[stem + "_sha256"] = "0" * 64
                    else:
                        approvals = [json.loads(line) for line in originals[approvals_path].splitlines()]
                        approval = next(
                            item for item in approvals
                            if item.get("event_id") == accepted["diff_approval_binding"]["event_id"]
                        )
                        stem = "review_evidence" if case.endswith("evidence") else "review_packet"
                        approval[stem + "_sha256"] = "0" * 64

                        def approval_line(value):
                            return (json.dumps(value, ensure_ascii=False,
                                               separators=(",", ":"), sort_keys=False)
                                    + "\n").encode("utf-8")

                        approvals_path.write_bytes(b"".join(approval_line(item) for item in approvals))
                        accepted["diff_approval_binding"]["sha256"] = hashlib.sha256(
                            approval_line(approval)
                        ).hexdigest()
                    rows_path.write_bytes(b"".join(ACTIVATION._canonical_json_line(item) for item in rows))
                    status["rollover_binding"]["rollover_sha256"] = hashlib.sha256(
                        ACTIVATION._canonical_json_line(row)
                    ).hexdigest()
                    status_path.write_bytes(ACTIVATION._canonical_json_bytes(status))
                    observation = ACTIVATION._without_owned_program_paths(root, _fresh_observation(fixture))
                    before = repository_snapshot(fixture.repository)
                    with self.assertRaisesRegex(ValueError, "rollover review .* approval binding mismatch"):
                        ROLLOVER.validated_inherited_paths(root, status, observation)
                    self.assertTrue(ACTIVATION.validate_state_authority(root, observation))
                    discovery = run_program_discovery(fixture.repository)
                    self.assertTrue(discovery["stop_required"])
                    self.assertNotEqual(discovery["disposition"], "resume")
                    self.assertEqual(repository_snapshot(fixture.repository), before)
                    self.assertEqual((root / allocation["entry_path"]).read_bytes(), legacy_bytes)
                    self.assertFalse((fixture.repository / "legacy.ts").exists())
                finally:
                    for path, content in originals.items():
                        path.write_bytes(content)
        observation = ACTIVATION._without_owned_program_paths(root, _fresh_observation(fixture))
        self.assertEqual(ACTIVATION.validate_state_authority(root, observation), [])
        self.assertEqual(run_program_discovery(fixture.repository)["disposition"], "resume")
    finally:
        fixture.close()
```

The per-case restoration above is confined to an owned temporary fixture, never a real program or user worktree. Approval byte order is preserved with `sort_keys=False`; do not use sorted object serialization to manufacture an approval hash failure.

- [ ] **2. Run RED.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_completed_rollover_binds_review_hashes_to_approval_and_disposition -v
```

Expected on the unrepaired owner: `ValueError not raised` for the accepted coordinated/rebound variants. Do not accept a failure from malformed packet generation, stale row hashes, fixture paths, or approval field order as proof of this defect.

- [ ] **3. Add the existing-authority comparisons.** In `_validated_completed_rollover_records`, within `if record_is_v2`, after validating the exact unique approval and its canonical SHA-256, and before the `accept-continue` projection check, insert:

```python
for stem, path in (
    ("review_evidence", evidence_path),
    ("review_packet", packet_path),
):
    current_sha256 = sha256_file(path)
    if (
        record[stem + "_binding"].get("sha256") != current_sha256
        or accepted_diff[stem + "_binding"].get("sha256") != current_sha256
        or disposition.get(stem + "_sha256") != current_sha256
        or approval.get(stem + "_sha256") != current_sha256
    ):
        label = stem.replace("_", " ")
        raise ValueError(f"rollover {label} approval binding mismatch")
```

The earlier binding validation and equality checks already establish the two binding mappings. Retain those checks, bundle validation, exact approval tuple/order, unique event match, approval digest, typed product result, projection, baseline, handoff, successor brief, cumulative tombstones, receipt/bytes validation, and unbound-suffix recovery rules. Do not modify v1 or rewrite historical approvals to make them pass.

- [ ] **4. Run GREEN and the existing immediate/later/multiple-rollover controls.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_completed_rollover_binds_review_hashes_to_approval_and_disposition tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_completed_rollover_revalidates_copied_files_and_approval tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_production_delete_accept_continue_preserves_tombstone_and_quarantine tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_later_continuation_carries_the_exact_v2_result_and_receipt tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_second_rollover_replaces_tombstone_in_place_and_keeps_history tests.test_program_rollover -v
```

Expected: all tests pass; unchanged legitimate completed chains still resume, negative reads stop without writing, later `accept-stop` continuation and legacy rollover remain valid. Every bound historical row is checked, not just the latest successor's current review artifacts.

- [ ] **5. Commit only Task 2 files when authorized.**

```bash
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_rollover.py tests/test_delete_operation_lifecycle.py
rtk git add -- skills/implementing-staged-plans/scripts/program_rollover.py tests/test_delete_operation_lifecycle.py
rtk git diff --cached --name-status
rtk git commit --only -m "fix: bind completed rollover reviews to approval" -- skills/implementing-staged-plans/scripts/program_rollover.py tests/test_delete_operation_lifecycle.py
```

Expected commit scope: these two files and only this task's changes. Task 3 also owns this test file, so execute sequentially.

## Task 3 — Preserve exact Delete recovery while enforcing the mutation barrier

**Files:** Modify `program_activation.py` and `tests/test_delete_operation_lifecycle.py` from the inventory.

**Interfaces:** `advance_execution_state(program_root, target_increment_state, observation)` continues returning `ExecutionTransitionReceipt | ExecutionTransitionReceiptV2`. Existing classifiers, mutation functions, authority readers, and their signatures remain unchanged. No global recovery flag, new validator mode, or general issue taxonomy.

- [ ] **1. Add the real pre-mutation regression** to `DeleteOperationLifecycleTests`:

```python
def test_unmapped_names_cannot_bypass_delete_authority_before_mutation(self):
    for filename in ("unmapped.txt", "unmapped-Delete.txt", "unmapped-quarantine.txt"):
        with self.subTest(filename=filename):
            fixture, legacy_bytes = _authorized_delete_program_with_successor()
            try:
                root = fixture.program_root
                (fixture.repository / filename).write_text("unmapped user work\n", encoding="utf-8")
                baseline = json.loads((root / "increments/ARCHIVE-INDEX/execution-baseline.json").read_text())
                allocation = baseline["delete_quarantine_bindings"][0]
                before = repository_snapshot(fixture.repository)
                status_before = (root / "state/status.json").read_bytes()
                with mock.patch.object(
                    ACTIVATION, "quarantine_bound_regular_file",
                    wraps=ACTIVATION.quarantine_bound_regular_file,
                ) as move, mock.patch.object(
                    ACTIVATION, "adopt_delete_quarantine_receipt",
                    wraps=ACTIVATION.adopt_delete_quarantine_receipt,
                ) as adopt:
                    with self.assertRaisesRegex(ValueError, "unmapped dirty paths"):
                        ACTIVATION.advance_execution_state(root, "implementing", _fresh_observation(fixture))
                    move.assert_not_called()
                    adopt.assert_not_called()
                self.assertEqual(repository_snapshot(fixture.repository), before)
                self.assertEqual((root / "state/status.json").read_bytes(), status_before)
                self.assertEqual((fixture.repository / "legacy.ts").read_bytes(), legacy_bytes)
                self.assertFalse((root / allocation["entry_path"]).exists())
                self.assertFalse((root / allocation["receipt_path"]).exists())
            finally:
                fixture.close()
```

- [ ] **2. Add this production-prefix recovery control** to the same class. It proves an unconditional `if state_issues: raise` is not an acceptable repair, and also checks that receipt adoption cannot bypass an unrelated issue. Fault injection stops the real writer at its persistence boundary; it does not manufacture a valid receipt or approval.

```python
def test_exact_delete_prefix_recovery_still_blocks_unmapped_work(self):
    for boundary in ("receipt", "status"):
        with self.subTest(boundary=boundary):
            fixture, legacy_bytes = _authorized_delete_program_with_successor()
            try:
                root = fixture.program_root
                baseline = json.loads((root / "increments/ARCHIVE-INDEX/execution-baseline.json").read_text())
                allocation = baseline["delete_quarantine_bindings"][0]
                entry_path = root / allocation["entry_path"]
                receipt_path = root / allocation["receipt_path"]
                status_before = (root / "state/status.json").read_bytes()
                fault = mock.Mock(side_effect=RuntimeError("interrupted Delete prefix"))
                patcher = (
                    mock.patch.dict(
                        ACTIVATION.quarantine_bound_regular_file.__globals__,
                        {"_write_delete_receipt": fault},
                    ) if boundary == "receipt" else
                    mock.patch.object(ACTIVATION, "atomic_replace_json", fault)
                )
                with patcher:
                    with self.assertRaisesRegex(RuntimeError, "interrupted Delete prefix"):
                        ACTIVATION.advance_execution_state(root, "implementing", _fresh_observation(fixture))
                self.assertEqual((root / "state/status.json").read_bytes(), status_before)
                self.assertEqual(entry_path.read_bytes(), legacy_bytes)
                self.assertFalse((fixture.repository / "legacy.ts").exists())
                self.assertEqual(receipt_path.exists(), boundary == "status")
                dirty_path = fixture.repository / "unmapped-quarantine.txt"
                dirty_path.write_text("unmapped user work\n", encoding="utf-8")
                before = repository_snapshot(fixture.repository)
                with mock.patch.object(
                    ACTIVATION, "quarantine_bound_regular_file",
                    wraps=ACTIVATION.quarantine_bound_regular_file,
                ) as move, mock.patch.object(
                    ACTIVATION, "adopt_delete_quarantine_receipt",
                    wraps=ACTIVATION.adopt_delete_quarantine_receipt,
                ) as adopt:
                    with self.assertRaisesRegex(ValueError, "unmapped dirty paths"):
                        ACTIVATION.advance_execution_state(root, "implementing", _fresh_observation(fixture))
                    move.assert_not_called()
                    adopt.assert_not_called()
                self.assertEqual(repository_snapshot(fixture.repository), before)
                # Remove only the test-created unmapped file in this disposable fixture.
                dirty_path.unlink()
                retained_entry = entry_path.read_bytes()
                with mock.patch.object(
                    ACTIVATION, "quarantine_bound_regular_file",
                    side_effect=AssertionError("recovery must not move again"),
                ), mock.patch.object(
                    Path, "unlink", side_effect=AssertionError("recovery must retain bytes"),
                ):
                    receipt = ACTIVATION.advance_execution_state(root, "implementing", _fresh_observation(fixture))
                self.assertEqual(receipt.increment_state, "implementing")
                self.assertEqual(entry_path.read_bytes(), retained_entry)
                self.assertTrue(receipt_path.is_file())
                normalized = ACTIVATION._without_owned_program_paths(root, _fresh_observation(fixture))
                self.assertEqual(ACTIVATION.validate_state_authority(root, normalized), [])
                discovery = run_program_discovery(fixture.repository)
                self.assertEqual(discovery["disposition"], "resume")
                self.assertFalse(discovery["stop_required"])
            finally:
                fixture.close()
```

- [ ] **3. Run RED.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_unmapped_names_cannot_bypass_delete_authority_before_mutation tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_exact_delete_prefix_recovery_still_blocks_unmapped_work -v
```

Expected on the unrepaired owner: trigger filenames reach the wrapped move, and an adoption-ready prefix reaches the wrapped receipt adopter. The neutral filename is a passing control. Existing post-mutation errors alone are insufficient: assert zero calls and unchanged files/status. If a failure occurs before the intended writer boundary, correct the test harness first.

- [ ] **4. Replace the substring filter with the exact recovery exception.** In `advance_execution_state`, inside `if v2_delete_execution`, after all paths have been classified and `recovery-required` rejected, replace the current `state_issues`/`blocking_issues` block with:

```python
state_issues = validate_state_authority(root, normalized)
# Status is still authorized after an exact interrupted move. Only its
# path-specific source warning can be explained by the classified prefix.
recoverable_source_issues = {
    f"authorized Delete source does not match baseline: {relative}"
    for relative, recovery in delete_recoveries.items()
    if recovery.disposition in {"receipt-adoption-ready", "resume"}
}
blocking_issues = [
    issue for issue in state_issues if issue not in recoverable_source_issues
]
if blocking_issues:
    raise ValueError("; ".join(blocking_issues))
```

This deliberately uses equality against one existing complete diagnostic, gated by exact path and classifier state. Changing that diagnostic later makes recovery stop safely until its application regression is updated. A generalized structured-issue/API migration would add unnecessary churn for this bounded repair. Preserve classification before writes, protected contexts, no-repeat-move/adoption functions, target-state workspace assessment, action/source-gate checks, and status-last validation. Do not change discovery to hide the failures.

- [ ] **5. Run GREEN plus recovery/security controls.**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_unmapped_names_cannot_bypass_delete_authority_before_mutation tests.test_delete_operation_lifecycle.DeleteOperationLifecycleTests.test_exact_delete_prefix_recovery_still_blocks_unmapped_work tests.test_state_authority.DeleteQuarantineTests tests.test_program_activation.ProgramActivationTests.test_every_activation_prefix_is_discovered_and_exact_retry_completes tests.test_program_activation.ProgramActivationTests.test_divergent_existing_record_is_preserved_and_requires_recovery tests.test_program_activation.ExactPlanMaterializationTests.test_execution_transitions_are_status_last_retry_safe_and_delta_bound -v
```

Expected: all pass on the supported local platform. All three filenames block before either product movement or receipt adoption; exact receipt/status interruptions still complete; divergent receipt/bytes, source replacement, unavailable primitives, collision, and malformed activation prefixes retain their existing safe stops. The upstream-replay recovery repaired at `a3168c3` must remain intact.

- [ ] **6. Commit only Task 3 files when authorized.**

```bash
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_activation.py tests/test_delete_operation_lifecycle.py
rtk git add -- skills/implementing-staged-plans/scripts/program_activation.py tests/test_delete_operation_lifecycle.py
rtk git diff --cached --name-status
rtk git commit --only -m "fix: restrict Delete recovery authority exceptions" -- skills/implementing-staged-plans/scripts/program_activation.py tests/test_delete_operation_lifecycle.py
```

## Task 4 — Verify the coherent repair and obtain one fresh independent review

**Files:** No additional production/test changes. Review only the five-file implementation inventory and this plan. Fixes discovered in this step are limited to defects caused by these three repairs; an unrelated finding or materially different approach needs a separately agreed scope.

**Interfaces:** No additions. Deliver a receipt tied to the exact final commit/tree and the actual test outputs.

- [ ] **1. Make one focused requirement/DRY pass.** Check all three retained findings against the implementation; remove only newly introduced unnecessary flexibility. Ensure the diff has only the loader guard, v2 review-hash comparisons, exact recovery exclusion, and the behavior regressions. Confirm no test weakening, new schemas, fixture snapshots, generated artifacts, package metadata, unrelated cleanup, or v1 serializer changes.

- [ ] **2. Run the full relevant suite once on the coherent tree.** The per-task commands are focused checks on changing inputs. This full suite is a separate integration obligation, not a reason to rerun successful focused commands against unchanged inputs.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk git diff --check
rtk git diff --check a3168c367633c960534d84bb47d1632123c1ea24 HEAD
rtk git status --short --branch
```

Expected: terminal exit 0 for the full suite and package validator, no whitespace errors, and only authorized files in the implementation diff. Report actual counts/skips; do not copy review task `01a07f27-0244-7191-b540-eed968f318bb`'s historical test counts as fresh results. A running/interrupted command is not a pass. Poll long commands in bounded waits and give concise status if they exceed 60 seconds. If inputs change after a material repair, rerun affected focused checks and the relevant integration/package check; do not rerun expensive external evaluation merely for a new commit ID with identical tested inputs.

- [ ] **3. Handle the native-Windows evidence boundary explicitly.** If a native-Windows runner is already available and execution there is authorized, run these targeted commands there; `rtk env` avoids shell-specific environment syntax:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_state_authority.PlatformImportCompatibilityTests tests.test_state_authority.WorkspaceAndBindingTests tests.test_state_authority.AtomicAuthorityWriterTests.test_native_windows_compare_and_swap_replaces_closed_destination -v
rtk env PYTHONDONTWRITEBYTECODE=1 python skills/implementing-staged-plans/scripts/program_discovery.py --help
rtk env PYTHONDONTWRITEBYTECODE=1 python skills/implementing-staged-plans/scripts/program_activation.py --help
rtk env PYTHONDONTWRITEBYTECODE=1 python skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: native imports/legacy authority/closed-destination compare-and-swap and package checks pass. Do not run POSIX Delete success fixtures as proof of Windows Delete support. If native Windows is unavailable, report: **“Native Windows was not executed; import coverage was simulated on macOS and the native-Windows test was skipped. No native-Windows validation or Windows Delete support is claimed.”** This limitation must appear even if every local test passes. Do not provision paid/hosted infrastructure to remove the limitation without authority.

- [ ] **4. Freeze one review scope.** Record final HEAD, full repair diff from `a3168c367633c960534d84bb47d1632123c1ea24`, aggregate context from `00c04a0f1c1ebb2cbdf890c4c4cf0334f89a344e`, dirty/index inventory, command exits/counts/skips, and package result. Do not refresh remote refs unless the later review asks about remote integration freshness.

- [ ] **5. Obtain one fresh, bounded independent review in a separately authorized review task.** No subagent is dispatched by this plan-only task. Supply the reviewer the exact final head, these two bases, this plan, and test receipts. Require read-only review, no recursive delegation, no external source transmission, no edits/push/PR/comments, and material findings only. Ask them to independently assess:

  - F1 import order, real v1 availability, preserved Darwin no-replace behavior, and truthful platform limits.
  - F2 actual retained bytes → rollover bindings → disposition → unique exact approval; both acceptance routes, historical rows, schema/order preservation, and no-write fail-closed discovery.
  - F3 real product/receipt mutation timing, hostile filenames, exact interrupted-prefix adoption/resume, unchanged action/source-gate checks, and preservation of `a3168c3` activation-prefix recovery.
  - Recovery/security invariants and test strength; no inference that green tests alone establish merge readiness.

Expected: no unresolved material defects in the bounded repair. Use at most one final reviewer unless that reviewer identifies a material defect. Validate a reported defect against current code, repair within the authorized scope, rerun changed-input checks, and request fresh evidence only for the changed scope. Do not repeatedly review unchanged code.

- [ ] **6. Report bounded completion and stop.** Give the exact three repair commits/final head, changed files, RED/GREEN evidence, full-suite/package results, native-Windows limitations, and the independent review result/head. If review or a required verification is unavailable, state that it remains outstanding; do not claim merge readiness.

## Recovery, security, and completion criteria

The repair is complete only when all of these hold on the final verified tree:

1. Fresh non-Darwin import paths do not load the Darwin process library; the existing v1 authority reader remains functional. Actual native-Windows evidence, if absent, is disclosed.
2. A production-generated completed v2 rollover rejects replaced/rebound review evidence or packet whenever either retained approval or disposition hashes disagree. The direct chain reader rejects, authority reports issues, fresh discovery stops, and no retained product/quarantine/control bytes change during those reads.
3. Unmapped filename text cannot exempt unrelated authority failures before a new move or receipt adoption. Exact interrupted moves still adopt/resume, while malformed or divergent recovery states continue to stop with bytes preserved.
4. v1 canonical bytes, family-specific prompts/readers/routes, typed v2 tombstones/receipts, approval field order, unique-event checks, cumulative rollover history, action/source gates, descriptor protection, and status-last recovery remain covered by the existing relevant suite.
5. Focused checks, the final full suite, package validation, whitespace checks, and one fresh independent review have terminal, attributable results. No material findings remain unresolved.

Recovery is preservation-first. Never “repair” a real program by rewriting its approval hashes, replacing evidence, removing a receipt, restoring the source, or deleting quarantine. Invalid retained evidence requires separately authorized reconciliation; interrupted movement uses only the existing exact classifier and no-overwrite adoption path. If a code repair is rejected, preserve the work and propose a reviewed reverse patch or separately authorized revert; never reset or discard user work.

Completion claims are limited to these three bounded repairs and tested compatibility. They do not authorize push, PR creation, merge, release, deployment, PLUG-002, quarantine disposal, terminal closure, secure erasure, or certification of an untested platform.
