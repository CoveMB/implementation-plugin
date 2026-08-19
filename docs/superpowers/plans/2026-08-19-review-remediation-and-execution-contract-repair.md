# Review Remediation and Execution Contract Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the three verified CodeRabbit defects without expanding the accepted `0.1.1` lifecycle beyond review remediation and exact execution-contract enforcement.

**Architecture:** Preserve the existing status-last, compare-and-swap lifecycle. An unresolved material review persists a typed `reviewing -> remediating` status binding containing immutable initial report evidence; a repaired candidate is validated against renewed affected reports before a typed `remediating -> reviewing` refreeze, after which the existing review-preparation transaction reaches the diff gate. The exact-file map remains Create/Modify/Preserve: every declared Modify is mandatory by review, and physical path renames are rejected because deletion has no supported disposition.

**Tech Stack:** Python 3 standard library, `unittest`, canonical JSON records, repository-owned SHA-256 bindings, atomic compare-and-swap status writes.

**Spec:** `docs/superpowers/plans/2026-08-15-program-bootstrap-launch-repair.md`

## Global Constraints

- Preserve accepted v1/v2 readers and existing persisted records; all new status fields are additive and required only in `remediating` or post-remediation states.
- Preserve the existing manifest, execution-baseline, review-evidence, and raw-report schema identifiers.
- Keep publication, activation, continuation, closure, commit, push, provider, and external authority unchanged.
- Every production behavior change begins with a focused failing test and ends with focused GREEN verification.
- Human prose changes use package validation and diff inspection rather than source-text assertions.

---

### Task 1: Typed Review Remediation Round Trip

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/review_coordination.py`
- Modify: `skills/implementing-staged-plans/scripts/program_review.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/references/review-coordination.md`
- Modify: `docs/workflows.md`
- Test: `tests/test_program_review.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Consumes: `ReviewReport`, `ReviewFinding`, `validate_review_bundle`, `validate_execution_workspace`, `_replace_or_adopt_status`, and the existing `implementation-program-status/v2` status-last contract.
- Produces: `REVIEW_REMEDIATION_SCHEMA`, `ReviewRemediationCandidate`, `ReviewRemediationReceipt`, `build_review_remediation`, `persist_review_remediation`, and `return_review_to_reviewing`.

- [ ] **Step 1: Write the failing lifecycle regression**

Add a production-flow test that reaches `reviewing`, persists an initial raw report containing material finding `F-OPEN`, and expects:

```python
remediation = REVIEW.persist_review_remediation(program_root, reviewing_observation)
self.assertEqual(remediation.increment_state, "remediating")

(fixture.repository / "archive-output.txt").write_text(
    "repaired archive output\n", encoding="utf-8"
)
write_follow_up_review_reports(fixture, finding_id="F-OPEN")
repaired_observation = ACTIVATION.inspect_repository(
    fixture.repository, fixture.head
).observation

returned = REVIEW.return_review_to_reviewing(program_root, repaired_observation)
self.assertEqual(returned.increment_state, "reviewing")
completed = REVIEW.persist_review_preparation(program_root, repaired_observation)
self.assertEqual(completed.increment_state, "awaiting-diff-approval")
```

Assert that the initial status-only write and repaired refreeze are each idempotent after a simulated lost response, that an unresolved or unrelated follow-up leaves status byte-identical, and that the final evidence contains one initial report, one affected follow-up, one repaired finding, and one matching remediation cycle.

- [ ] **Step 2: Run RED**

Run:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_program_review.ProgramReviewTests.test_material_finding_round_trip_returns_to_diff_gate -v
```

Expected: fail because `persist_review_remediation` and `return_review_to_reviewing` do not exist.

- [ ] **Step 3: Extend raw reports without breaking existing records**

Allow optional `report_id` and `follow_up_for_finding_ids` fields in `load_raw_review_report`. Default existing reports to `<scope>-initial`. Require follow-up identifiers to be nonempty strings and continue rejecting unknown fields.

- [ ] **Step 4: Implement the status-last remediation boundary**

Add these interfaces to `program_review.py`:

```python
REVIEW_REMEDIATION_SCHEMA = "implementation-review-remediation/v1"

@dataclass(frozen=True)
class ReviewRemediationCandidate:
    remediating_status: dict[str, object]
    remediating_status_bytes: bytes

@dataclass(frozen=True)
class ReviewRemediationReceipt:
    increment_state: str
    status_sha256: str
    product_delta_sha256: str
    unresolved_finding_ids: tuple[str, ...]
    recovered: bool

def build_review_remediation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewRemediationCandidate: ...

def persist_review_remediation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewRemediationReceipt: ...

def return_review_to_reviewing(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewRemediationReceipt: ...
```

`build_review_remediation` must accept only `reviewing`, validate current state and product-delta bindings, validate initial reports, require at least one open material finding, and bind canonical initial reports/findings and raw digests into `review_remediation_binding`. `persist_review_remediation` writes only the next status with digest CAS and adopts only byte-identical lost-response status.

`return_review_to_reviewing` must accept only a valid `remediating` binding, validate the repaired product delta, combine persisted initial reports with renewed affected reports, require every initially open finding to be repaired with one matching remediation cycle, validate the complete final bundle, then CAS a new `reviewing` status whose execution transition binds the repaired product delta.

- [ ] **Step 5: Reuse remediation history in final review preparation**

When `review_remediation_binding` is present, build final review evidence from its initial reports plus the current follow-up reports. Replace initial open finding dispositions only with same-ID repaired follow-up findings; reject missing, unknown, duplicate, unrelated, deferred, or still-open follow-ups. Keep the no-remediation path byte-compatible.

- [ ] **Step 6: Validate remediating state and repaired refreeze**

Update state authority so `remediating` requires a canonical remediation binding and positive unresolved count. Permit a current `reviewing` execution transition whose prior state is either `implementing` or `remediating`; continue requiring the derived event ID, authorization ID, and current product-delta digest.

- [ ] **Step 7: Run focused GREEN**

Run:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_program_review tests.test_review_coordination \
  tests.test_state_authority tests.test_program_discovery -v
```

Expected: all focused lifecycle, evidence, authority, and discovery tests pass.

### Task 2: Mandatory Modify and Unsupported Path-Rename Contracts

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/execution_discipline.py`
- Modify: `skills/implementing-staged-plans/references/execution-discipline.md`
- Test: `tests/test_repository_preparation.py`
- Test: `tests/test_execution_discipline.py`

**Interfaces:**
- Consumes: `validate_execution_workspace`, `ExecutionSurface`, and `validate_execution_surfaces`.
- Produces: explicit mandatory-all Modify wording and a validator error for `surface_kind="path", change_kind="renamed"`.

- [ ] **Step 1: Write two focused failing tests**

Add a two-Modify workspace test where only one path changes and assert:

```python
assessment = PREPARATION.validate_execution_workspace(
    program_root,
    baseline,
    inspection,
    increment_state="reviewing",
)
self.assertIn(
    "reviewing workspace has unchanged Modify path: second.txt",
    assessment.issues,
)
```

Add a semantic-surface test where a physical path uses `change_kind="renamed"` and assert that validation rejects it because the file map has no delete/rename disposition.

- [ ] **Step 2: Run RED**

Run:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_repository_preparation.ExecutionWorkspaceValidationTests.test_reviewing_requires_every_declared_modify_path \
  tests.test_execution_discipline.SemanticSurfaceTests.test_physical_path_rename_is_unsupported -v
```

Expected: the two-Modify test confirms current runtime behavior; the rename test fails until the semantic validator rejects unsupported physical path renames. The Modify test is retained because it causally fixes the prior one-path coverage gap.

- [ ] **Step 3: Implement the minimal contract repair**

In `validate_execution_surfaces`, append an issue when:

```python
item.surface_kind == "path" and item.change_kind == "renamed"
```

Do not add a delete disposition or weaken the existing missing-Modify guard. Update the canonical reference to say that `implementing` may contain a subset in progress, while `reviewing` and later require every declared Create path to exist and every declared Modify path to differ from its baseline. State that physical path renames require an approved future typed old/new migration contract and are unsupported by Create/Modify/Preserve.

- [ ] **Step 4: Run focused GREEN**

Run:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_repository_preparation tests.test_execution_discipline -v
```

Expected: all execution-baseline, ownership, and semantic-surface tests pass.

### Task 3: Documentation, Independent Review, and Release Verification

**Files:**
- Modify: `docs/workflows.md`
- Modify: `skills/implementing-staged-plans/references/review-coordination.md`
- Modify: `skills/implementing-staged-plans/references/execution-discipline.md`
- Verify: every file changed by Tasks 1 and 2.

**Interfaces:**
- Consumes: the implemented remediation APIs and persisted status transitions.
- Produces: source-faithful operator guidance and one independently reviewed repair batch.

- [ ] **Step 1: Document the implemented route**

Describe the exact sequence:

```text
reviewing -> remediating -> reviewing -> verified -> awaiting-diff-approval
```

State that questions do not accept the diff, open material findings require the typed remediation sink, repaired product bytes and renewed affected reports are validated before refreezing, and each status write is digest-CAS/idempotent rather than a hostile multi-file transaction.

- [ ] **Step 2: Run structural validation**

Run:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 \
  skills/implementing-staged-plans/scripts/validate_package.py
rtk git diff --check
```

Expected: package validation passes and the diff has no whitespace errors.

- [ ] **Step 3: Run the full deterministic suite once**

Run:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
```

Expected: all tests pass with only the repository's expected native-Windows skip.

- [ ] **Step 4: Obtain one bounded independent repair review**

The reviewer must inspect only the current repair diff and report material defects in the remediation transaction, mandatory Modify contract, or path-rename rejection. If no material defect exists, retain the PASS result without another review of the unchanged diff.

- [ ] **Step 5: Commit and push the coherent repair batch**

Run:

```bash
rtk git add -- <exact changed paths>
rtk git diff --cached --check
rtk git commit -m "fix: add typed review remediation recovery"
rtk git push origin agent/program-bootstrap-launch-repair
```

Then run a fresh authenticated CodeRabbit CLI review against the pushed committed scope. Verify any new issues against current code and repeat only for still-valid material defects.
