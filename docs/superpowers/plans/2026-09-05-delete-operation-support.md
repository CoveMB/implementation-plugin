# Delete Operation Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add truthful, fail-closed support for exact regular-file `Delete` operations so a program can preserve an accepted absent path through review, diff acceptance, rollover, recovery, and closure without weakening existing `Create`, `Modify`, or `Preserve` contracts.

**Architecture:** Keep manifest/status v1, v2, and existing v3 programs on their exact current routes. Extend manifest-v3 only through explicitly versioned nested v2 setup, file-map, baseline, product-result, rollover, blocked-context, and closure contracts; route by exact schema, never by optional-field presence. The workflow continues to authorize a human or agent to modify the bound local workspace—it does not become an automatic deletion engine, migration engine, cleanup command, or generic destructive-action authority.

**Tech Stack:** Python 3 standard library, frozen dataclasses, canonical JSON and SHA-256, `unittest`, temporary Git repositories, existing atomic/no-overwrite/status-last writers.

**Spec:** The real consumer is `/private/tmp/pipeflow-effect-flow.4Ox4Wl/planning/plans/2026-09-05-effect-flow-redesign.md` at SHA-256 `a0dfa0574f972c1b7378b36f6021f45c8cf2b042c332a223f45d64fa0e50230b`; the compatible broader design context is `docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md` and `docs/superpowers/specs/2026-08-23-expanded-local-refactor-operations-design.md`.

## Global Constraints

- Start only from a clean branch `repair/delete-operation-support` whose kickoff HEAD is the plan-only commit directly above `b5eb689e780f48b218b807a4691f0994474e4178` (candidate parent `c6a32575ee07b79cc26fcecfec037f2a206f442a`) and whose only kickoff delta from the candidate is this plan file.
- Use `rtk` for every repository command.
- Preserve manifest/status v1 and v2 and operation-envelope/setup/file-map/baseline/result/rollover/blocked/closure v1 bytes and behavior; do not rewrite persisted programs or frozen `0.1.1` fixtures.
- Existing manifest-v3 programs with `implementation-program-setup-semantics/v1` and `implementation-operation-envelope/v1` remain exactly `Create`/`Modify`/`Preserve` programs.
- Delete-capable manifest-v3 proposals use `implementation-program-setup-semantics/v2` paired with `implementation-operation-envelope/v2`; mixed v1/v2 nested contracts fail before every write.
- A `Delete` target must be one normalized repository-relative path to an existing program-owned regular non-symlink, non-hard-linked file beneath the selected workspace. Directories, symlinks, symlinked ancestors, hard links, special files, missing parents, external paths, protected paths, and pre-existing user work remain unsupported.
- `Delete` means the approved final state is absent. Never encode absence as `Modify`, `Preserve`, an omitted path, an empty digest, or a fabricated digest.
- `authorized` requires every Delete target to remain byte-identical to its baseline; `implementing` permits either the exact baseline file or its absence; `reviewing` and later require absence. A changed-but-present Delete target is always invalid.
- A typed local Delete remains within the exact plan-bound `modify-workspace` action. It does not grant the separately named `destructive-operation`, cleanup, migration, Git, publication, deployment, provider, or external-state actions.
- Keep public `prepare_exact_plan(program_root, exact_plan_bytes, observation)`, `materialize_exact_plan(program_root, submitted_plan_prompt, observation)`, and `required_future_lifecycle_writes(program_root, workspace_root, increment_id)` signatures unchanged.
- Keep deterministic candidate construction, exact-prefix adoption, atomic compare-and-swap, no-overwrite publication, immutable ledgers, and status-last ordering at every existing transaction boundary.
- Add no dependency, generic operation framework, automatic restore, staging engine, Move/Rename, Replace, directory deletion, progress cursor, or v4/v5 manifest/status implementation.
- Release the coherent implementation as package version `0.1.3`; synchronize only the existing version owners.
- Run the full deterministic suite once after the coherent implementation batch. Focused RED/GREEN commands may run per task.
- Do not push, open a pull request, install the plugin, synchronize a cached copy, mutate the pipeFlow worktree, or perform any external action under this plan.

---

## Confirmed Root Cause and Scope Decision

The defect is confirmed at the locked baseline:

1. `program_setup.py::SUPPORTED_OPERATIONS` is exactly `("Create", "Modify", "Preserve")`; `validate_setup_semantics(...)` rejects both a v1 envelope listing `Delete` and every allocation whose operation is `Delete`. A real probe returns `operation allocation 0 operation is unsupported` and `operation envelope must support exactly Create/Modify/Preserve`.
2. `repository_preparation.py::parse_exact_file_map(...)` recognizes only `Create`, `Modify`, and `Preserve`. Worse, an unversioned `### Delete` heading is currently ignored and its bullet is absorbed into the preceding `Modify` section. The repair must make this legacy input fail explicitly before adding the versioned v2 route.
3. `program_activation.py::_path_baselines(...)` and `repository_preparation.py::validate_execution_workspace(...)` require every `Modify` path to remain a file. The focused baseline test confirms deletion is rejected as `execution workspace deleted Modify path: <path>`.
4. The accepted product-delta and rollover contracts require a string `sha256` for every result, so they cannot represent a legitimate absent path. `program_rollover.py::_validated_inherited_paths(...)` also requires every inherited path to remain a regular file with the accepted digest.
5. The pipeFlow Task 8 file map contains 27 explicit regular-file Delete paths. Omitting them would make the exact plan incomplete and make their Git deletions unmapped product changes; relabeling them `Modify` would preserve the existing, correct missing-Modify failure.

The smallest coherent repair is therefore a versioned Delete-only path-state extension inside manifest-v3. The pending manifest/status-v4 expanded-operations design remains pending for Move/Rename, Replace, migration groups, automated staging/finalization, and expanded Preserve; this repair does not claim to implement it.

Unsafe alternatives are rejected:

- **Encode Delete as Modify:** destroys the invariant that every Modify result is present and causes the confirmed missing-Modify failure.
- **Omit deleted paths:** removes them from setup authority, exact-plan ownership, review surfaces, accepted results, rollover inheritance, and closure evidence; it also turns the Git deletion into an unmapped dirty path.
- **Use Preserve:** contradicts both the requested outcome and Preserve's byte-identical present-state contract.
- **Store `""`, zeroes, or `str(None)` as a digest:** fabricates an identity for an absent file and lets existing string-only consumers confuse absence with content.
- **Loosen v1 validators:** reinterprets accepted manifests and fixtures in place and can turn accidental file loss into a valid legacy result.
- **Implement the entire pending expanded-operations engine:** adds unrelated Move/Rename, Replace, staging, leases, cleanup, and migration-group machinery without solving a current requirement that needs only exact regular-file removal and durable tombstones.

## File Map

### Create

- `tests/fixtures/delete-operation/pipeflow-task-8-delete-paths.json` — frozen 27-path real-scenario inventory and authoritative source digest.
- `tests/test_delete_operation_lifecycle.py` — one causal proposal-to-closure application-path replay plus the optional live source-identity check.

### Modify

- `docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md` — record the narrow v3 nested-v2 Delete repair between setup v3 and the still-pending expanded v4 design.
- `docs/superpowers/specs/2026-08-23-expanded-local-refactor-operations-design.md` — state that basic exact regular-file Delete is owned by `0.1.3`, while advanced migration/staging semantics remain pending v4 work.
- `skills/implementing-staged-plans/scripts/program_setup.py` — own setup-semantics/envelope v2 validation, pairing, and recap rendering.
- `skills/implementing-staged-plans/scripts/program_authority.py` — recognize only the exact new setup authority schemas on manifest-v3 and reject cross-family substitution.
- `skills/implementing-staged-plans/scripts/state_authority.py` — own shared versioned file-map types, exact nested-schema routing, state bindings, and v1 compatibility rejection.
- `skills/implementing-staged-plans/scripts/repository_preparation.py` — parse exact-file-map v2, parse baseline v2, and assess present/absent path states.
- `skills/implementing-staged-plans/scripts/program_activation.py` — construct Delete-aware plan candidates/baselines and bind v2 execution transitions without changing public signatures.
- `skills/implementing-staged-plans/scripts/execution_discipline.py` — validate deleted ownership and semantic surfaces without treating Delete as a physical rename.
- `skills/implementing-staged-plans/scripts/review_coordination.py` — carry and validate the v2 accepted path-state result in review evidence and packets.
- `skills/implementing-staged-plans/scripts/program_review.py` — persist/revalidate Delete-aware review and remediation bindings.
- `skills/implementing-staged-plans/scripts/diff_disposition.py` — bind the exact reviewed v2 product result during acceptance.
- `skills/implementing-staged-plans/scripts/blocked_recovery.py` — freeze and revalidate Delete path states across blocked/resume.
- `skills/implementing-staged-plans/scripts/program_continuation.py` — consume accepted present/absent results without coercing absence to a string digest.
- `skills/implementing-staged-plans/scripts/program_rollover.py` — persist v2 rollover records and cumulative inherited present/absent path states.
- `skills/implementing-staged-plans/scripts/continuity_closure.py` — validate/render versioned closure reconciliation over accepted result bindings and cumulative path states.
- `skills/implementing-staged-plans/scripts/program_closure.py` — build closure from the complete accepted increment chain and final cumulative state.
- `skills/implementing-staged-plans/scripts/validate_package.py` — set and enforce package version `0.1.3`.
- `skills/implementing-staged-plans/SKILL.md` — route and explain the Delete-capable nested v2 family.
- `skills/implementing-staged-plans/agents/openai.yaml` — describe exact local Delete support without implying generic destructive authority.
- `skills/implementing-staged-plans/references/program-authority.md` — document v1/v2 setup pairing and authority limits.
- `skills/implementing-staged-plans/references/repository-preparation.md` — own the v2 file-map grammar and baseline path-state rules.
- `skills/implementing-staged-plans/references/execution-discipline.md` — own lifecycle-state behavior for Delete.
- `skills/implementing-staged-plans/references/review-coordination.md` — own review/remediation result binding.
- `skills/implementing-staged-plans/references/state-authorization.md` — own acceptance and rollover version routing.
- `skills/implementing-staged-plans/references/continuity-closure.md` — own cumulative tombstone and closure rules.
- `docs/reference.md`, `docs/workflows.md`, `docs/troubleshooting.md`, `docs/maintainers.md`, `docs/installation.md` — synchronize the user-visible `0.1.3` contract, failure messages, and installation examples.
- `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — synchronize only the package version.
- `tests/program_bootstrap_support.py` — construct exact v1 and Delete-capable v2 setup fixtures.
- `tests/test_program_setup.py`, `tests/test_program_authority.py`, `tests/test_program_bootstrap.py` — setup, authority, recap, publication, and v1 compatibility coverage.
- `tests/test_repository_preparation.py`, `tests/test_program_activation.py`, `tests/test_approval_checkpoint.py` — parser, baseline, exact-plan, and execution assessment coverage.
- `tests/test_execution_discipline.py`, `tests/test_review_coordination.py`, `tests/test_program_review.py`, `tests/test_diff_disposition.py` — review/diff path-state coverage.
- `tests/test_blocked_recovery.py`, `tests/test_program_discovery.py`, `tests/test_state_authority.py` — recovery and schema-routing coverage.
- `tests/test_program_continuation.py`, `tests/test_program_rollover.py`, `tests/test_multi_increment_lifecycle.py` — cumulative present/absent inheritance coverage.
- `tests/test_continuity_closure.py`, `tests/test_program_closure.py` — complete-chain closure coverage.
- `tests/test_front_door_contract.py`, `tests/test_distribution_documentation.py`, `tests/test_package_validation.py` — contract, documentation, and version synchronization.

### Preserve

- `docs/superpowers/plans/2026-09-05-delete-operation-support.md` — use as the locked implementation plan; do not rewrite it while executing the tasks.
- `implementation-programs/ISP-001/**` — historical accepted program/control-plane evidence is not part of this repair.
- `tests/fixtures/program-bootstrap/v0.1.1/**` — frozen compatibility fixtures remain byte-for-byte unchanged.
- `skills/implementing-staged-plans/scripts/program_bootstrap.py`, `program_launch.py`, `approval_checkpoint.py`, `program_discovery.py`, and `task_prompt.py` — exercise their existing generic routes in tests; change them only if a focused RED test proves an exact-schema integration defect.
- `/Users/CoveMB/Code/CoveMB/implementation-plugin/**` and `/private/tmp/pipeflow-effect-flow.4Ox4Wl/**` — read-only/out of scope throughout implementation.

---

### Task 1: Version the Setup-Level Delete Contract

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/program_setup.py`
- Modify: `skills/implementing-staged-plans/scripts/program_authority.py`
- Modify: `tests/program_bootstrap_support.py`
- Test: `tests/test_program_setup.py`
- Test: `tests/test_program_authority.py`
- Test: `tests/test_program_bootstrap.py`

**Interfaces:**
- Consumes: manifest-v3 `setup_semantics` and the existing immutable setup decision flow.
- Produces: `SETUP_SEMANTICS_SCHEMA_V2`, `OPERATION_ENVELOPE_SCHEMA_V2`, `SETUP_RECAP_SCHEMA_V2`, `SETUP_RECAP_CHECKPOINT_SCHEMA_V2`, `SETUP_DECISION_ADAPTER_SCHEMA_V2`, and `SETUP_ACTIVATION_SCHEMA_V2`.
- Produces: `_operation_contract(semantics: Mapping[str, object]) -> tuple[tuple[str, ...], bool]`, returning the exact supported-operation tuple and whether Delete fields are required.
- Produces test helpers: `BootstrapFixture.configure_delete_setup_v2(allocation: Mapping[str, object]) -> dict[str, object]`, `configure_v1_envelope_with_delete() -> list[str]`, and `configure_mixed_setup_versions() -> list[str]`; each recomputes the semantic digest after its exact mutation.
- Preserves: every v1 setup/envelope/recap/decision/activation byte and error route.

- [ ] **Step 1: Write failing setup and authority tests**

Add these test cases with a helper that rewrites the candidate before recomputing `setup_semantics_sha256`:

```python
def delete_allocation(path: str, increment_id: str) -> dict[str, object]:
    return {
        "kind": "exact-path",
        "path": path,
        "operation": "Delete",
        "increment_ids": [increment_id],
        "inclusions": ["legacy implementation removal"],
        "exclusions": ["directories", "user-owned work"],
        "ownership": "program",
        "protected": False,
        "user_work": False,
        "file_kind": "regular-file",
        "link_kind": "none",
        "mode": "100644",
        "collision": "existing",
        "accepted_state": "absent",
        "content_disposition": "obsolete",
        "rationale": "The approved replacement implementation makes this file obsolete.",
    }

def test_setup_v2_accepts_and_renders_delete(self) -> None:
    manifest = self.fixture.configure_delete_setup_v2(
        delete_allocation("legacy.ts", "ARCHIVE-INDEX")
    )
    self.assertEqual(SETUP.validate_setup_semantics(self.fixture.candidate), [])
    recap = SETUP.render_setup_recap(self.fixture.candidate)
    self.assertIn("Supported operations: Create, Modify, Delete, Preserve.", recap)
    self.assertIn("Delete legacy.ts", recap)
    self.assertIn("final state: absent", recap)
    self.assertIn("content: obsolete", recap)
    self.assertIn("makes this file obsolete", recap)
    self.assertEqual(
        manifest["setup_semantics"]["schema_version"],
        "implementation-program-setup-semantics/v2",
    )

def test_v1_and_mixed_setup_contracts_reject_delete(self) -> None:
    issues = self.fixture.configure_v1_envelope_with_delete()
    self.assertIn("operation allocation 0 operation is unsupported", issues)
    self.assertIn("operation envelope must support exactly Create/Modify/Preserve", issues)
    self.assertIn(
        "setup semantics and operation envelope schema families do not match",
        self.fixture.configure_mixed_setup_versions(),
    )
```

Also assert proposal validation, publication, recap checkpoint, setup decision, and setup activation accept the all-v2 nested family and reject a substituted v1 record or v2 record in a v1 setup.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_setup tests.test_program_authority tests.test_program_bootstrap -v
```

Expected: new tests fail because only setup/envelope v1 exists and `Delete` is unsupported; all pre-existing tests remain green.

- [ ] **Step 3: Implement exact nested-schema dispatch**

Add literal paired contracts; do not mutate the v1 tuple:

```python
SETUP_SEMANTICS_SCHEMA_V2 = "implementation-program-setup-semantics/v2"
OPERATION_ENVELOPE_SCHEMA_V2 = "implementation-operation-envelope/v2"
SETUP_RECAP_SCHEMA_V2 = "implementation-program-setup-recap/v2"
SETUP_RECAP_CHECKPOINT_SCHEMA_V2 = "implementation-program-setup-recap-checkpoint/v2"
SETUP_DECISION_ADAPTER_SCHEMA_V2 = "setup-approval-decision/v2"
SETUP_ACTIVATION_SCHEMA_V2 = "setup-activation-decision/v2"
SUPPORTED_OPERATIONS_V1 = ("Create", "Modify", "Preserve")
SUPPORTED_OPERATIONS_V2 = ("Create", "Modify", "Delete", "Preserve")
DELETE_CONTENT_DISPOSITIONS = frozenset({"migrated", "obsolete", "intentional-discard"})

def _operation_contract(
    semantics: Mapping[str, object],
) -> tuple[tuple[str, ...], bool]:
    schema = semantics.get("schema_version")
    envelope = semantics.get("operation_envelope")
    envelope_schema = envelope.get("schema_version") if isinstance(envelope, dict) else None
    if (schema, envelope_schema) == (SETUP_SEMANTICS_SCHEMA, OPERATION_ENVELOPE_SCHEMA):
        return SUPPORTED_OPERATIONS_V1, False
    if (schema, envelope_schema) == (SETUP_SEMANTICS_SCHEMA_V2, OPERATION_ENVELOPE_SCHEMA_V2):
        return SUPPORTED_OPERATIONS_V2, True
    raise ValueError("setup semantics and operation envelope schema families do not match")
```

For v2, require `accepted_state == "absent"`, one allowed `content_disposition`, and a non-empty rationale only on Delete allocations; reject those fields on non-Delete allocations. Preserve existing ownership/facts checks and require Delete to be program-owned, non-protected, and non-user-work before setup approval can be valid.

Select recap/checkpoint/adapter/activation schema versions solely from `_operation_contract(...)`. Extend `program_authority.py::SETUP_AUTHORITY_RECORD_SCHEMAS` and its manifest-v3 foreign-schema checks with the v2 setup records without relaxing v1 matching.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command.

Expected: all setup, authority, and generic proposal-publication tests pass; the recap exposes each Delete fact and legacy bytes stay exact.

- [ ] **Step 5: Commit the setup contract**

```bash
rtk git add skills/implementing-staged-plans/scripts/program_setup.py skills/implementing-staged-plans/scripts/program_authority.py tests/program_bootstrap_support.py tests/test_program_setup.py tests/test_program_authority.py tests/test_program_bootstrap.py
rtk git commit -m "feat: add typed delete setup contracts"
```

---

### Task 2: Add Exact-Plan, Baseline, and Product Path-State Semantics

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Test: `tests/test_repository_preparation.py`
- Test: `tests/test_program_activation.py`
- Test: `tests/test_approval_checkpoint.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `ExactFileMapV2`, `ExecutionBaselineV2`, and `InheritedPathStateV2` while retaining `ExactFileMap` and `ExecutionBaseline` as v1 types.
- Produces: `file_map_entries(file_map) -> tuple[tuple[str, tuple[str, ...]], ...]` and `file_map_paths(file_map, *, mutable_only: bool) -> tuple[str, ...]` so consumers do not reconstruct operation inventories inconsistently.
- Produces: `product_result_schema_version` on `ExecutionWorkspaceAssessment`; v1 remains `implementation-product-delta/v1`, v2 is `implementation-product-path-states/v2`.
- Produces test helpers on `ExecutionWorkspaceValidationTests`: `delete_baseline(path: str) -> ExecutionBaselineV2` and `assess_v2(baseline: ExecutionBaselineV2, state: str) -> ExecutionWorkspaceAssessment`; both use the class's temporary `workspace` path.
- Preserves: public plan preparation/materialization and three-argument future-write signatures.

- [ ] **Step 1: Write failing parser and assessment tests**

Add exact parser and lifecycle assertions:

```python
DELETE_MAP = """# Delete plan
## File map
Schema: `implementation-exact-file-map/v2`

### Create
- `review/evidence.json`
### Modify
- `state/status.json`
### Delete
- `legacy.ts`
### Preserve
- `catalog.txt`
"""

def test_unversioned_delete_heading_is_rejected_instead_of_absorbed_as_modify(self) -> None:
    unversioned = DELETE_MAP.replace(
        "Schema: `implementation-exact-file-map/v2`\n\n", ""
    )
    with self.assertRaisesRegex(
        ValueError, "unversioned exact-file map contains unsupported heading: Delete"
    ):
        PREPARATION.parse_exact_file_map(unversioned)

def test_v2_delete_path_must_transition_from_exact_file_to_absence(self) -> None:
    baseline = self.delete_baseline("legacy.ts")
    self.assertTrue(self.assess_v2(baseline, "authorized").valid)
    self.workspace.joinpath("legacy.ts").write_text("changed\n", encoding="utf-8")
    self.assertIn(
        "execution workspace changed Delete path before removal: legacy.ts",
        self.assess_v2(baseline, "implementing").issues,
    )
    self.workspace.joinpath("legacy.ts").unlink()
    reviewing = self.assess_v2(baseline, "reviewing")
    self.assertTrue(reviewing.valid, reviewing.issues)
    self.assertEqual(
        reviewing.product_delta,
        ({
            "path": "legacy.ts",
            "disposition": "Delete",
            "final_state": "absent",
            "sha256": None,
        },),
    )
```

Add negative cases for a missing Delete target at baseline, unchanged Delete at reviewing, changed-but-present Delete, symlink/hard-link/directory/special-file targets, overlap with recorded user work, duplicate cross-disposition paths, `sha256` on an absent result, and `None` on a present result. Retain the existing assertion that deleting a v1 Modify path fails.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_preparation tests.test_program_activation tests.test_approval_checkpoint tests.test_state_authority -v
```

Expected: the unversioned parser test exposes the current Delete-to-Modify absorption; v2 imports and absent-result assertions fail; existing v1 tests pass.

- [ ] **Step 3: Add versioned file-map and baseline types**

In `state_authority.py`, retain `ExactFileMap` unchanged and add:

```python
EXACT_FILE_MAP_SCHEMA_V2 = "implementation-exact-file-map/v2"

@dataclass(frozen=True)
class ExactFileMapV2:
    schema_version: str
    create: tuple[str, ...]
    modify: tuple[str, ...]
    delete: tuple[str, ...]
    preserve: tuple[str, ...]

def file_map_entries(
    file_map: ExactFileMap | ExactFileMapV2,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if isinstance(file_map, ExactFileMapV2):
        return (
            ("Create", file_map.create),
            ("Modify", file_map.modify),
            ("Delete", file_map.delete),
            ("Preserve", file_map.preserve),
        )
    return (
        ("Create", file_map.create),
        ("Modify", file_map.modify),
        ("Preserve", file_map.preserve),
    )
```

`parse_exact_file_map(...)` must first reject every unrecognized `###` heading within the v1 file-map body. Select v2 only from the exact schema marker, then require one ordered Create/Modify/Delete/Preserve heading; allow the Delete section to contain no path only for a successor that needs v2 inherited-state validation. Duplicate and unsafe path rejection remains global across all sections.

Add `implementation-execution-baseline/v2` with an exact v2 file-map object, current path baselines, user-work baselines, and ordered `inherited_path_states`. Dispatch `execution_baseline_from_value(...)` on the exact baseline schema. Do not add fields to the v1 serialization.

- [ ] **Step 4: Implement Delete-aware candidate and workspace validation**

In `program_activation.py::_build_plan_candidate(...)`, require file-map v2 when the current increment has a setup-envelope Delete allocation or status carries v2 inherited path states. Match every Delete path to exactly one current-increment exact or bounded-class setup allocation. Keep lifecycle-managed writes limited to Create/Modify/Preserve.

Use the shared operation iterator in `_path_baselines(...)`, `_user_work_baselines(...)`, `validate_required_managed_file_map(...)`, and `validate_execution_workspace(...)`. Enforce:

```python
if disposition == "Delete":
    if increment_state == "authorized" and (actual is None or actual != entry.sha256):
        issues.append(f"authorized workspace changed Delete path: {relative}")
    elif increment_state == "implementing" and actual not in {None, entry.sha256}:
        issues.append(
            f"execution workspace changed Delete path before removal: {relative}"
        )
    elif increment_state in later_states and actual is not None:
        issues.append(f"reviewing workspace still contains Delete path: {relative}")
    elif actual is None:
        product_delta.append({
            "path": relative,
            "disposition": "Delete",
            "final_state": "absent",
            "sha256": None,
        })
```

For v2 Create/Modify results emit `final_state: "present"` with the real digest. Keep the v1 result object and hash byte-for-byte unchanged. Include Delete paths in mapped product dirt and claimed paths, but never in managed lifecycle requirements.

- [ ] **Step 5: Run the focused tests and verify GREEN**

Run the Step 2 command.

Expected: the exact parser, baseline, authorization, partial implementation, complete absence, and legacy-negative tests pass.

- [ ] **Step 6: Commit exact-plan and baseline support**

```bash
rtk git add skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/repository_preparation.py skills/implementing-staged-plans/scripts/program_activation.py tests/test_repository_preparation.py tests/test_program_activation.py tests/test_approval_checkpoint.py tests/test_state_authority.py
rtk git commit -m "feat: validate delete path states"
```

---

### Task 3: Carry Absent Results Through Review and Diff Acceptance

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/execution_discipline.py`
- Modify: `skills/implementing-staged-plans/scripts/review_coordination.py`
- Modify: `skills/implementing-staged-plans/scripts/program_review.py`
- Modify: `skills/implementing-staged-plans/scripts/diff_disposition.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `tests/program_bootstrap_support.py`
- Test: `tests/test_execution_discipline.py`
- Test: `tests/test_review_coordination.py`
- Test: `tests/test_program_review.py`
- Test: `tests/test_diff_disposition.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `implementation-review-evidence/v2`, `implementation-review-packet/v2`, `implementation-review-preparation/v2`, `implementation-review-remediation/v2`, `implementation-diff-disposition-binding/v2`, and `implementation-diff-disposition-command/v2` only for product path-state v2.
- Produces: review evidence field `product_result = {schema_version, sha256, ordered_path_states}`.
- Produces test helpers in `tests/program_bootstrap_support.py`: `BootstrapFixture.observation() -> RepositoryObservation` and `reviewing_delete_program() -> tuple[BootstrapFixture, Path, RepositoryObservation]`, returning a real temporary manifest-v3/setup-v2 program at `reviewing` with `legacy.ts` absent and raw review reports ready.
- Preserves: v1 review evidence, packet rendering, remediation, prompt bytes, diff bindings, and approval records.

- [ ] **Step 1: Write failing review/remediation/diff tests**

Add a reviewing fixture with one absent Delete path and assert:

```python
def test_delete_result_is_reviewed_and_accepted_as_absent(self) -> None:
    fixture, program_root, observation = reviewing_delete_program()
    try:
        candidate = REVIEW.build_review_preparation(program_root, observation)
        evidence = json.loads(candidate.evidence_bytes)
        self.assertEqual(evidence["schema_version"], "implementation-review-evidence/v2")
        self.assertEqual(
            evidence["product_result"]["ordered_path_states"],
            [{
                "path": "legacy.ts",
                "disposition": "Delete",
                "final_state": "absent",
                "sha256": None,
            }],
        )
        REVIEW.persist_review_preparation(program_root, observation)
        accepted = DIFF.build_diff_acceptance_candidate(program_root, observation)
        self.assertEqual(
            accepted.accepted_status["diff_disposition_binding"]["schema_version"],
            "implementation-diff-disposition-binding/v2",
        )
        self.assertEqual(
            accepted.accepted_status["diff_disposition_binding"][
                "product_result_schema_version"
            ],
            "implementation-product-path-states/v2",
        )
    finally:
        fixture.close()
```

Add failures for a reappeared Delete target, changed path-state order, `final_state: present`, non-null absent digest, omitted Delete state, extra path state, v1/v2 review substitution, and remediation that restores or changes the deleted target without a renewed v2 assessment and review.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline tests.test_review_coordination tests.test_program_review tests.test_diff_disposition tests.test_state_authority -v
```

Expected: new v2 review/result schemas are absent and Delete surfaces cannot be represented.

- [ ] **Step 3: Implement typed review result persistence**

Extend execution ownership with a literal `delete` disposition: it requires a non-empty pre-write fingerprint, exact `post_write_fingerprint == "absent"`, program ownership, and no accepted user-work overlap. Add `deleted` to execution surface changes and require one semantic naming/compatibility record for each deleted path; keep physical `renamed` rejection unchanged.

When `assessment.product_result_schema_version` is v2, `program_review.py` writes v2 review evidence containing the exact ordered states and v2 preparation/remediation bindings. `review_coordination.py` validates that the result digest is the canonical digest of those exact states and renders absent paths as absent—never as files with digests.

`diff_disposition.py` loads that exact reviewed result, freshly reassesses the workspace, compares schema/digest/states, and emits v2 binding/command schemas containing `product_result_schema_version`. Keep v1 base-seed construction and prompt bytes unchanged.

- [ ] **Step 4: Extend state validation by exact review/diff schema**

In `state_authority.py`, pair baseline v1 with review/diff v1 and baseline v2 with review/diff v2. Reject mixed families, missing result schemas, changed state order, or a digest that does not reproduce from `ordered_path_states`. Preserve the existing source-gate and status-last checks.

- [ ] **Step 5: Run the focused tests and verify GREEN**

Run the Step 2 command.

Expected: Delete absence is visible and immutable from review preparation through accepted status; every v1 golden remains exact.

- [ ] **Step 6: Commit review and diff support**

```bash
rtk git add skills/implementing-staged-plans/scripts/execution_discipline.py skills/implementing-staged-plans/scripts/review_coordination.py skills/implementing-staged-plans/scripts/program_review.py skills/implementing-staged-plans/scripts/diff_disposition.py skills/implementing-staged-plans/scripts/state_authority.py tests/program_bootstrap_support.py tests/test_execution_discipline.py tests/test_review_coordination.py tests/test_program_review.py tests/test_diff_disposition.py tests/test_state_authority.py
rtk git commit -m "feat: bind deleted results through review"
```

---

### Task 4: Freeze Delete State Across Blocked Recovery

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/blocked_recovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Test: `tests/test_blocked_recovery.py`
- Test: `tests/test_program_discovery.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `implementation-blocked-context/v2` with `product_result_schema_version`, `product_result_sha256`, and exact `ordered_path_states` captured at the block boundary.
- Produces: `blocked_workspace_paths(...)` including current Delete paths for v2 baselines.
- Consumes test helper: `reviewing_delete_program()` from `tests/program_bootstrap_support.py`; expose its fixture observation as `BootstrapFixture.observation() -> RepositoryObservation` there.
- Preserves: blocked-context/resolution/command v1 and the existing prohibition on entering blocked from `remediating`.

- [ ] **Step 1: Write failing block/resume tests**

```python
def test_reviewing_delete_can_block_and_resume_only_with_the_same_absence(self) -> None:
    fixture, program_root, observation = reviewing_delete_program()
    try:
        receipt = BLOCKED.block_current_program(
            program_root,
            BLOCKED.BlockedTransitionRequest(
                reason_code="review-evidence-unavailable",
                recovery_criteria=("Review evidence is available.",),
                evidence_bindings=(),
            ),
            observation,
        )
        self.assertEqual(receipt.increment_state, "blocked")
        status = fixture.load_json("state/status.json")
        self.assertEqual(
            status["blocked_context"]["schema_version"],
            "implementation-blocked-context/v2",
        )
        self.assertEqual(
            status["blocked_context"]["ordered_path_states"][0]["final_state"],
            "absent",
        )
        fixture.repository.joinpath("legacy.ts").write_text("restored\n", encoding="utf-8")
        self.assertIn(
            "blocked product path states changed",
            BLOCKED.validate_blocked_context(program_root, status, fixture.observation()),
        )
    finally:
        fixture.close()
```

Also cover an implementing-state partial deletion, a post-block extra deletion, changed state order, evidence that claims a missing Delete file digest, exact prompt-bound resume, every failure-injection prefix, and v1 context byte compatibility.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_blocked_recovery tests.test_program_discovery tests.test_state_authority -v
```

Expected: blocked context v1 has no path-state binding and Delete is not included in plan-owned workspace paths.

- [ ] **Step 3: Implement v2 blocked-context binding**

Build a fresh execution assessment before writing blocked status. For a v2 baseline, bind its exact schema, result digest, and ordered current path states into the block identifier. `validate_blocked_context(...)` must reproduce all three from fresh observation before resolution. Include Delete in `blocked_workspace_paths(...)` but exclude absent Delete targets from regular-file evidence bindings.

Keep the existing status-last transaction and exact record adoption. Never recreate, restore, remove, or clean a product path during block or resume.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command.

Expected: exact absence/partial-state prefixes resume; any post-block path-state change is preserved and fails closed.

- [ ] **Step 5: Commit blocked recovery support**

```bash
rtk git add skills/implementing-staged-plans/scripts/blocked_recovery.py skills/implementing-staged-plans/scripts/state_authority.py tests/test_blocked_recovery.py tests/test_program_discovery.py tests/test_state_authority.py
rtk git commit -m "feat: preserve delete state in recovery"
```

---

### Task 5: Carry Tombstones Through Successor Rollover

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/program_continuation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_rollover.py`
- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Test: `tests/test_program_continuation.py`
- Test: `tests/test_program_rollover.py`
- Test: `tests/test_multi_increment_lifecycle.py`
- Test: `tests/test_program_activation.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `ProductPathStateV2(path, disposition, final_state, sha256)` without changing `ProductDeltaPath` v1.
- Produces: `implementation-successor-authority-projection/v2`, `implementation-increment-rollover/v2`, `implementation-increment-rollover-binding/v2`, and `implementation-inherited-workspace/v2`.
- Produces: `validated_inherited_path_states(program_root, status, observation) -> tuple[InheritedPathStateV2, ...]` while preserving `validated_inherited_paths(...)` for v1.
- Produces: cumulative last-writer-wins path states only when the later increment explicitly owns the same path under a valid operation.
- Produces test fixture: `ThreeIncrementDeleteFixture` with `accept_delete(path)`, `rollover(accepted_status, successor_id)`, `accept_unrelated_create(increment_id, path)`, `rollover_current(successor_id)`, and `prepare_third_plan()` methods that call production writers rather than editing lifecycle artifacts directly.

- [ ] **Step 1: Write failing three-increment inheritance tests**

```python
def test_delete_tombstone_survives_unrelated_successor_and_closes_over_third_increment(self) -> None:
    fixture = ThreeIncrementDeleteFixture()
    try:
        first = fixture.accept_delete("legacy.ts")
        second = fixture.rollover(first, "SECOND")
        self.assertEqual(
            second["inherited_workspace_binding"]["inherited_path_states"],
            [{
                "path": "legacy.ts",
                "final_state": "absent",
                "disposition": "Delete",
                "sha256": None,
            }],
        )
        fixture.accept_unrelated_create("SECOND", "new.ts")
        third = fixture.rollover_current("THIRD")
        self.assertEqual(
            [item["path"] for item in third["inherited_workspace_binding"]["inherited_path_states"]],
            ["legacy.ts", "new.ts"],
        )
        fixture.repository.joinpath("legacy.ts").write_text("reappeared\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inherited absent path reappeared: legacy.ts"):
            fixture.prepare_third_plan()
    finally:
        fixture.close()
```

Add a positive recreation case where the later exact plan explicitly owns `legacy.ts` as Create from an inherited absent baseline. Add negative cases for implicit recreation, Delete against inherited absence, Modify/Preserve against absence, Create against inherited presence, omitted/reordered/duplicated state, mixed v1/v2 rollover chains, `str(None)`, and a current result that is not the exact reviewed/diff-accepted v2 result.

- [ ] **Step 2: Run focused continuation/rollover tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_continuation tests.test_program_rollover tests.test_multi_increment_lifecycle tests.test_program_activation tests.test_state_authority -v
```

Expected: current continuation coerces `None` to a string and current rollover requires each accepted path to remain a regular file with a digest.

- [ ] **Step 3: Implement versioned accepted-result consumption and cumulative merge**

For v2, load the exact product result from current review evidence, freshly reassess it, and compare it with the diff binding before constructing continuation authority. Use a separate dataclass:

```python
@dataclass(frozen=True)
class ProductPathStateV2:
    path: str
    disposition: str
    final_state: str
    sha256: str | None
```

Never pass v2 entries through `ProductDeltaPath(sha256: str)`. The v2 rollover record carries the accepted current result plus the canonical cumulative `inherited_path_states` and digest. Merge by path in accepted increment order; replace an earlier state only when the current exact operation inventory owns that same path and its baseline agrees with the inherited state.

`validated_inherited_path_states(...)` validates every completed v2 rollover record, action, grant, review result, diff decision, and cumulative digest. It requires present files to match exact digests and absent files to remain absent. Mixed result families stop before persistence.

- [ ] **Step 4: Consume inherited states in successor baselines**

`program_activation.py::_build_plan_candidate(...)` stores validated v2 inherited states in baseline v2 and strips their expected Git dirt from user-work observation. `repository_preparation.py::validate_execution_workspace(...)` validates untouched inherited states throughout the successor. It allows an explicit Create only from inherited absence and Modify/Delete/Preserve only from inherited presence; no current operation means the inherited state must remain exact.

`state_authority.py` validates exact v1 or v2 rollover/binding pairs and delegates to the matching inherited validator. Do not modify v1 cumulative-path or digest behavior.

- [ ] **Step 5: Run focused continuation/rollover tests and verify GREEN**

Run the Step 2 command.

Expected: present identities and absent tombstones survive unrelated increments; explicit recreation is valid; implicit or mixed-family state changes fail before writes.

- [ ] **Step 6: Commit rollover inheritance**

```bash
rtk git add skills/implementing-staged-plans/scripts/program_continuation.py skills/implementing-staged-plans/scripts/program_rollover.py skills/implementing-staged-plans/scripts/program_activation.py skills/implementing-staged-plans/scripts/repository_preparation.py skills/implementing-staged-plans/scripts/state_authority.py tests/test_program_continuation.py tests/test_program_rollover.py tests/test_multi_increment_lifecycle.py tests/test_program_activation.py tests/test_state_authority.py
rtk git commit -m "feat: inherit accepted delete tombstones"
```

---

### Task 6: Reconcile the Complete Accepted Path-State Chain at Closure

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/continuity_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/program_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Test: `tests/test_continuity_closure.py`
- Test: `tests/test_program_closure.py`
- Test: `tests/test_multi_increment_lifecycle.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `implementation-closure-reconciliation/v2`, `implementation-closure-packet/v2`, `implementation-closure-preparation/v2`, `implementation-program-closure-command/v2`, and `implementation-program-closure-command-binding/v2` for a v2 accepted chain.
- Produces: reconciliation fields `accepted_result_bindings`, `final_inherited_path_states`, and `final_inherited_path_states_sha256`.
- Consumes test helper: `accepted_three_increment_delete_program() -> ThreeIncrementDeleteFixture`, which extends the Task 5 fixture through accepted `THIRD` state with current review/diff evidence intact.
- Preserves: all v1 closure dataclasses, renderers, commands, approvals, and singleton first-increment closure bytes.

- [ ] **Step 1: Write failing closure-chain tests**

```python
def test_v2_closure_binds_every_accepted_result_and_final_tombstone(self) -> None:
    fixture = accepted_three_increment_delete_program()
    try:
        candidate = CLOSURE.build_closure_preparation(
            fixture.program_root, fixture.observation()
        )
        reconciliation = json.loads(candidate.reconciliation_bytes)
        self.assertEqual(
            reconciliation["accepted_increment_ids"],
            ["FIRST", "SECOND", "THIRD"],
        )
        self.assertEqual(len(reconciliation["accepted_result_bindings"]), 3)
        self.assertEqual(
            next(
                item
                for item in reconciliation["final_inherited_path_states"]
                if item["path"] == "legacy.ts"
            )["final_state"],
            "absent",
        )
        self.assertNotIn(
            "legacy.ts",
            reconciliation["requirement_dispositions"][0]["evidence_paths"],
        )
    finally:
        fixture.close()
```

Add failures for a missing/reordered/duplicated accepted increment, missing earlier review packet or diff decision, changed result digest, lost tombstone, unexpected reappearance, unowned recreation, stale later-invalidation check, mixed v1/v2 chain, and absent path represented as an evidence file.

- [ ] **Step 2: Run closure tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_program_closure tests.test_multi_increment_lifecycle tests.test_state_authority -v
```

Expected: current production closure emits only the final increment and has no cumulative path-state binding.

- [ ] **Step 3: Add versioned closure values and validators**

Keep `ClosureReconciliation` and `ClosurePacket` unchanged. Add v2 dataclasses with the three new result fields and exact schema-specific constructors/validators/renderers. Canonical validation requires:

```python
expected_state_digest = hashlib.sha256(
    json.dumps(
        list(candidate.final_inherited_path_states),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()
if candidate.final_inherited_path_states_sha256 != expected_state_digest:
    issues.append("final inherited path-state digest mismatch")
```

Do not put absent paths in `evidence_paths`; bind their typed result and final-state digest instead.

- [ ] **Step 4: Build closure from the canonical rollover chain**

In `program_closure.py::build_closure_preparation(...)`, dispatch on the accepted product-result schema. For v2, enumerate `program_rollover.py::_validated_completed_rollover_records(...)` plus the final accepted increment in order. Bind each increment's exact reviewed result, review packet, diff decision, and required handoff addendum; merge the final current result into validated cumulative inherited states; perform later-invalidation checks across every accepted increment; then construct v2 reconciliation and packet.

Version closure preparation, prompt, approval, command, and status bindings together. `state_authority.py::_validate_closure_readiness(...)` recomputes the complete chain and exact final-state digest. Existing v1 closure remains on its current singleton or legacy route.

- [ ] **Step 5: Run closure tests and verify GREEN**

Run the Step 2 command.

Expected: closure succeeds only when all accepted increments and the final cumulative present/absent state are exact; every tamper fails before closure persistence.

- [ ] **Step 6: Commit closure reconciliation**

```bash
rtk git add skills/implementing-staged-plans/scripts/continuity_closure.py skills/implementing-staged-plans/scripts/program_closure.py skills/implementing-staged-plans/scripts/state_authority.py tests/test_continuity_closure.py tests/test_program_closure.py tests/test_multi_increment_lifecycle.py tests/test_state_authority.py
rtk git commit -m "feat: reconcile deleted paths at closure"
```

---

### Task 7: Replay the PipeFlow Scenario and Synchronize Release Contracts

**Files:**
- Create: `tests/fixtures/delete-operation/pipeflow-task-8-delete-paths.json`
- Create: `tests/test_delete_operation_lifecycle.py`
- Modify: `docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md`
- Modify: `docs/superpowers/specs/2026-08-23-expanded-local-refactor-operations-design.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/agents/openai.yaml`
- Modify: `skills/implementing-staged-plans/references/program-authority.md`
- Modify: `skills/implementing-staged-plans/references/repository-preparation.md`
- Modify: `skills/implementing-staged-plans/references/execution-discipline.md`
- Modify: `skills/implementing-staged-plans/references/review-coordination.md`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `skills/implementing-staged-plans/references/continuity-closure.md`
- Modify: `docs/reference.md`
- Modify: `docs/workflows.md`
- Modify: `docs/troubleshooting.md`
- Modify: `docs/maintainers.md`
- Modify: `docs/installation.md`
- Modify: `.codex-plugin/plugin.json`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Test: `tests/test_front_door_contract.py`
- Test: `tests/test_distribution_documentation.py`
- Test: `tests/test_package_validation.py`

**Interfaces:**
- Produces: `load_pipeflow_delete_inventory() -> tuple[str, tuple[str, ...]]` returning the source SHA-256 and exactly 27 normalized paths.
- Produces: a deterministic temporary-repository replay from Delete-capable proposal validation through final closure.
- Produces: `DeleteLifecycleFixture(delete_paths: Sequence[str], source_sha256: str)` with the exact production-writer methods used in Step 2: `validate_and_publish_proposal()`, `render_setup_recap()`, `approve_activate_and_start()`, `prepare_and_authorize_delete_plan()`, `delete_every_target()`, `review_and_accept_delete_result()`, `rollover_through_unrelated_increment()`, `assert_every_target_is_inherited_absent()`, and `prepare_final_closure()`.
- Produces: package version `0.1.3` on all existing version owners.
- Preserves: the external pipeFlow source and workspace as read-only inputs.

- [ ] **Step 1: Create the frozen real-scenario inventory**

Create this exact JSON fixture:

```json
{
  "schema_version": "pipeflow-delete-scenario/v1",
  "source_plan_sha256": "a0dfa0574f972c1b7378b36f6021f45c8cf2b042c332a223f45d64fa0e50230b",
  "source_task": "Task 8: Migrate Use Cases and Delete the Legacy Architecture",
  "delete_paths": [
    "src/pipeFlow.ts",
    "src/helpers/helpers-error.ts",
    "src/helpers/index.ts",
    "src/helpers/utils.ts",
    "src/types/context.ts",
    "src/types/error.ts",
    "src/types/flow.ts",
    "src/types/helpers.ts",
    "src/types/index.ts",
    "src/types/internals.ts",
    "src/types/middleware.ts",
    "src/utils/const.ts",
    "src/utils/context.ts",
    "src/utils/fp.ts",
    "src/utils/guards-messages.ts",
    "src/utils/guards-reasons.ts",
    "__tests__/compatibility.test.ts",
    "__tests__/error.test.ts",
    "__tests__/flow.test.ts",
    "__tests__/gard.test.ts",
    "__tests__/pipeFlow.integration.test.ts",
    "__tests__/public-api.types.ts",
    "__tests__/subFlow.ts",
    "__tests__/utils.test.ts",
    "__tests__/fixtures/data.ts",
    "__tests__/fixtures/helpers.ts",
    "test/legacy/characterization.test.ts"
  ]
}
```

The loader rejects a non-27 count, duplicate, unsafe path, wrong order, missing source digest, or directory-like entry.

- [ ] **Step 2: Write the failing proposal-to-closure replay**

In `tests/test_delete_operation_lifecycle.py`, build a temporary Git repository with all 27 regular files, a Delete-capable setup/envelope v2 proposal, and a later unrelated increment. Exercise real production writers and validators:

```python
def test_pipeflow_delete_inventory_replays_proposal_to_closure(self) -> None:
    source_sha256, delete_paths = load_pipeflow_delete_inventory()
    self.assertEqual(len(delete_paths), 27)
    fixture = DeleteLifecycleFixture(delete_paths, source_sha256)
    try:
        fixture.validate_and_publish_proposal()
        recap = fixture.render_setup_recap()
        self.assertTrue(all(path in recap for path in delete_paths))
        fixture.approve_activate_and_start()
        fixture.prepare_and_authorize_delete_plan()
        fixture.delete_every_target()
        fixture.review_and_accept_delete_result()
        fixture.rollover_through_unrelated_increment()
        fixture.assert_every_target_is_inherited_absent()
        closure = fixture.prepare_final_closure()
        self.assertEqual(
            [item["path"] for item in closure["final_inherited_path_states"] if item["final_state"] == "absent"],
            list(delete_paths),
        )
    finally:
        fixture.close()
```

Add `test_external_pipeflow_source_matches_frozen_inventory`, guarded only by `PIPEFLOW_PLAN_PATH`; when supplied, it computes the exact SHA-256, extracts Task 8's Delete bullets, and compares the ordered 27-path tuple with the fixture. The deterministic suite uses the frozen fixture and never requires the external path.

- [ ] **Step 3: Run the scenario tests and verify RED, then GREEN**

Initial RED:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle -v
```

Expected before the Tasks 1–6 implementation: proposal validation rejects Delete. Expected after Tasks 1–6: the frozen scenario passes and the optional external-source test is skipped.

Run the live identity replay against the locked read-only source:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 PIPEFLOW_PLAN_PATH=/private/tmp/pipeflow-effect-flow.4Ox4Wl/planning/plans/2026-09-05-effect-flow-redesign.md python3 -m unittest tests.test_delete_operation_lifecycle -v
```

Expected: no skip; source digest and ordered Task 8 inventory match; all 27 tombstones survive the unrelated rollover and final closure.

- [ ] **Step 4: Update canonical documentation without overstating authority**

Document both grammars exactly:

```markdown
Legacy setup/envelope v1 and unversioned exact-file maps support Create, Modify,
and Preserve only. Delete-capable programs use setup/envelope v2 and an exact
file map marked `implementation-exact-file-map/v2` with ordered Create, Modify,
Delete, and Preserve sections. Delete authorizes only the named regular-file
absence inside the bound local `modify-workspace` action; it is not generic
destructive-operation, cleanup, migration, Git, publication, deployment, or
external-state authority.
```

Record authorized/implementing/reviewing state rules, typed absent results, blocked recovery, cumulative tombstones, explicit recreation, and complete-chain closure once at their canonical references; link from the skill and reader docs. State that advanced Move/Rename, Replace, migration groups, automatic staging/finalization, and expanded Preserve remain pending under the broader v4 design.

- [ ] **Step 5: Synchronize package version `0.1.3`**

Set:

```python
PACKAGE_VERSION = "0.1.3"
```

Update the three plugin/marketplace manifests, installation archive examples, maintainers' current-version text, front-door snapshot, distribution tests, and package-validator expectations to the same literal version. Change no plugin name, skill path, invocation policy, marketplace owner, repository identity, or manifest field set.

- [ ] **Step 6: Run focused package and documentation checks**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle tests.test_front_door_contract tests.test_distribution_documentation tests.test_package_validation -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: the real-scenario fixture, front-door contract, documentation, synchronized version, package inventory, and package validator pass.

- [ ] **Step 7: Commit scenario and release contracts**

```bash
rtk git add tests/fixtures/delete-operation/pipeflow-task-8-delete-paths.json tests/test_delete_operation_lifecycle.py docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md docs/superpowers/specs/2026-08-23-expanded-local-refactor-operations-design.md skills/implementing-staged-plans/SKILL.md skills/implementing-staged-plans/agents/openai.yaml skills/implementing-staged-plans/references/program-authority.md skills/implementing-staged-plans/references/repository-preparation.md skills/implementing-staged-plans/references/execution-discipline.md skills/implementing-staged-plans/references/review-coordination.md skills/implementing-staged-plans/references/state-authorization.md skills/implementing-staged-plans/references/continuity-closure.md docs/reference.md docs/workflows.md docs/troubleshooting.md docs/maintainers.md docs/installation.md .codex-plugin/plugin.json .claude-plugin/plugin.json .claude-plugin/marketplace.json skills/implementing-staged-plans/scripts/validate_package.py tests/test_front_door_contract.py tests/test_distribution_documentation.py tests/test_package_validation.py
rtk git commit -m "feat: release typed delete operation support"
```

---

## Final Verification, Review, and Claim Gate

- [ ] **Step 1: Reconfirm exact scope before final checks**

```bash
rtk git status --short --branch
rtk git diff --name-only b5eb689e780f48b218b807a4691f0994474e4178...HEAD
rtk git diff --check b5eb689e780f48b218b807a4691f0994474e4178...HEAD
```

Expected: only this locked plan plus the File Map Create/Modify paths are changed; the tree is clean; `diff --check` reports no errors; frozen v0.1.1 and historical ISP-001 paths are absent from the diff.

- [ ] **Step 2: Run the complete deterministic suite once on the unchanged candidate**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: package validation passes and the complete test process exits `0`. Record the exact executed test count and skipped-platform limitations; do not convert an interrupted or partial run into a pass.

- [ ] **Step 3: Run the locked live scenario once without changing either repository**

```bash
rtk shasum -a 256 /private/tmp/pipeflow-effect-flow.4Ox4Wl/planning/plans/2026-09-05-effect-flow-redesign.md
rtk env PYTHONDONTWRITEBYTECODE=1 PIPEFLOW_PLAN_PATH=/private/tmp/pipeflow-effect-flow.4Ox4Wl/planning/plans/2026-09-05-effect-flow-redesign.md python3 -m unittest tests.test_delete_operation_lifecycle -v
```

Expected: SHA-256 is `a0dfa0574f972c1b7378b36f6021f45c8cf2b042c332a223f45d64fa0e50230b`; all scenario tests pass; the pipeFlow worktree has no writes.

- [ ] **Step 4: Perform one bounded independent material review**

Review only `b5eb689e780f48b218b807a4691f0994474e4178...HEAD` for correctness, fail-closed path-state behavior, compatibility, recovery, and test protection. Verify every finding against current code. Fix only confirmed material defects, rerun only affected focused checks, then rerun the full suite only if a relevant input changed after Step 2. If no material issue exists, record exactly: `No material improvements recommended.`

- [ ] **Step 5: Stop before publication or consumer mutation**

Report commits, exact changed paths, focused/full check evidence, scenario replay evidence, compatibility limitations, and residual risks. Do not push, open a pull request, install, update caches, edit pipeFlow, or claim Move/Rename, Replace, directory deletion, automatic rollback, external migration, production safety, or platform behavior not exercised by the completed checks.

## Rollback and Failure Semantics

- Before any v2 program artifact is persisted, the implementation commits can be reverted normally; v1 programs remain readable throughout.
- After a Delete-capable v2 setup, baseline, review, rollover, blocked context, or closure artifact exists, do not downgrade that program to `0.1.2` or rewrite it as v1. Retain a `0.1.3` reader or ship a forward repair that preserves the v2 bytes.
- A failure before product mutation preserves the baseline file and exact partial control-plane prefix; retry may adopt only byte-identical owner-bound artifacts.
- A failure after a planned Delete while status is `implementing` preserves the absence as a valid partial product result. Recovery may block and resume from the exact bound absence; it does not restore automatically.
- A failure after review or diff acceptance must reproduce the same ordered path states and digest. Reappearance, changed content, missing result records, reordered states, or mixed schema families is divergent and stops without cleanup.
- Rollover merges a Delete tombstone only after exact diff acceptance. An unrelated successor cannot erase it; only a later exact Create operation whose baseline agrees with inherited absence can replace it.
- Closure binds the entire accepted chain and final cumulative state. It cannot close when a tombstone disappeared, a deleted file reappeared, an earlier accepted result is missing, or evidence treats an absent path as a file.
- Recovery bytes are not created by this repair. Source recovery remains a separately authorized manual or Git operation; the plugin never resets, restores, stashes, cleans, or deletes automatically.

## Final Validation Matrix

| Requirement | Primary owner | Required evidence | Failure signal |
| --- | --- | --- | --- |
| Locked implementation baseline | Git preflight | branch `repair/delete-operation-support`, HEAD `b5eb689e...`, clean | stop before edits |
| Locked real source | scenario fixture/live replay | SHA-256 `a0dfa057...` and exact ordered 27-path Task 8 inventory | source drift; no claim |
| Setup can state Delete truthfully | `program_setup.py` | envelope/setup v2 validates and recap renders path, absent state, disposition, rationale | unsupported or mixed schema |
| Legacy setup unchanged | `program_setup.py`, `program_authority.py` | v1 golden bytes and cross-family negatives | any v1 byte/result drift |
| Exact plan does not misclassify Delete | `repository_preparation.py` | unversioned heading fails; v2 parses ordered Delete section | Delete absorbed as Modify |
| Baseline proves a real removable file | `program_activation.py` | existing regular-file digest; unsafe/user-owned targets rejected | missing/unsafe/overlap issue |
| Lifecycle path-state semantics | `validate_execution_workspace(...)` | authorized exact; implementing exact-or-absent; reviewing absent; v2 result with null digest | accidental loss or fabricated digest |
| Managed lifecycle writes stay separate | `state_authority.py` | required writes remain only Create/Modify/Preserve | Delete accepted for a control path |
| Review and remediation bind absence | `program_review.py`, `review_coordination.py` | v2 evidence has exact ordered states/digest and renewed result after repair | stale/missing/mixed result |
| Diff acceptance binds reviewed result | `diff_disposition.py` | v2 binding/command matches fresh review result | prompt or result mismatch |
| Blocked recovery freezes path state | `blocked_recovery.py` | v2 context reproduces exact partial/complete states | post-block change or evidence fabrication |
| Rollover preserves tombstones | `program_rollover.py` | three-increment test retains absent state through unrelated work | reappearance, omission, mixed chain |
| Recreation is explicit | activation/preparation | later Create owns inherited absent path and baseline agrees | implicit recreation or wrong operation |
| Closure covers the complete chain | `program_closure.py`, `continuity_closure.py` | all accepted results/reviews/diff decisions plus final cumulative digest | singleton-only or lost tombstone |
| Front door does not over-authorize | skill/references/docs | Delete remains local plan-bound `modify-workspace` only | generic destructive/external claim |
| Package is synchronized | manifests/validator/docs | every owner says `0.1.3`; package validation exits `0` | version or inventory mismatch |
| Full regression | complete suite | one completed exit `0`, exact count recorded | failure, interruption, or partial output |
| External boundary | final status/diff | no push, PR, install, cache sync, pipeFlow edit, or provider action | any unauthorized external mutation |
