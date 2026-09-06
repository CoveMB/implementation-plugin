# Delete Operation Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add truthful, fail-closed support for exact regular-file `Delete` operations so a program can preserve an accepted absent path through review, diff acceptance, rollover, recovery, and closure without weakening existing `Create`, `Modify`, or `Preserve` contracts.

**Architecture:** Keep manifest/status v1, v2, and existing manifest-v3/setup-v1 programs on their exact current routes. A manifest-v3 program that selects setup-semantics/envelope v2 enters one nested v2 lifecycle family at sequence zero: every increment uses file-map, baseline, product-result, execution-transition, review, diff, blocked-context, rollover, discovery, and closure v2, including an empty ordered Delete section before the increment that first deletes a file. One canonical fail-closed Delete-target validator protects Git metadata, program roots, and manifest-owned control paths at allocation and every later reassessment. Complete-chain closure derives requirement ownership from traceability plus accepted per-increment evidence, validates later accepted deltas, and reuses existing nonfinal handoffs and the final manifest-owned closure artifacts instead of inventing an addendum. Route by exact schema pairs, never by optional-field presence or by whether the current increment happens to contain Delete. The workflow continues to authorize a human or agent to modify the bound local workspace—it does not become an automatic deletion engine, migration engine, cleanup command, or generic destructive-action authority.

**Tech Stack:** Python 3 standard library, frozen dataclasses, canonical JSON and SHA-256, `unittest`, temporary Git repositories, existing atomic/no-overwrite/status-last writers.

**Spec:** The real consumer is `/private/tmp/pipeflow-effect-flow.4Ox4Wl/planning/plans/2026-09-05-effect-flow-redesign.md` at SHA-256 `a0dfa0574f972c1b7378b36f6021f45c8cf2b042c332a223f45d64fa0e50230b`; the compatible broader design context is `docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md` and `docs/superpowers/specs/2026-08-23-expanded-local-refactor-operations-design.md`.

## Global Constraints

- The implementation candidate is exactly `b5eb689e780f48b218b807a4691f0994474e4178`. Start implementation only when that candidate is an ancestor of the clean kickoff HEAD on branch `repair/delete-operation-support`, every commit in `b5eb689e780f48b218b807a4691f0994474e4178..HEAD` changes only `docs/superpowers/plans/2026-09-05-delete-operation-support.md`, and the aggregate candidate-to-HEAD diff contains only that plan. Record the actual kickoff HEAD and the plan's actual SHA-256 as execution evidence before Task 1; do not use any correction commit's parent position or hash as a durable prerequisite.
- Use `rtk` for every repository command.
- Preserve manifest/status v1 and v2 and operation-envelope/setup/file-map/baseline/result/execution-transition/rollover/blocked/closure v1 bytes and behavior; do not rewrite persisted programs or frozen `0.1.1` fixtures.
- Existing manifest-v3 programs with `implementation-program-setup-semantics/v1` and `implementation-operation-envelope/v1` remain exactly `Create`/`Modify`/`Preserve` programs.
- Delete-capable manifest-v3 proposals use `implementation-program-setup-semantics/v2` paired with `implementation-operation-envelope/v2`; that setup choice fixes the complete program to the nested v2 lifecycle family from its first increment, and mixed v1/v2 nested contracts fail before every write.
- A `Delete` target must be one normalized repository-relative path that is a program-owned regular non-symlink, non-hard-linked file beneath the selected workspace when its deletion-increment baseline is captured. Setup may bind either an initially `existing` target or an `accepted-predecessor` target created and accepted by a strict predecessor increment; the latter requires a same-path predecessor `Create` allocation. Directories, symlinks, symlinked ancestors, hard links, special files, absent Delete baselines, external paths, protected paths, and pre-existing user work remain unsupported.
- Every Delete allocation and reassessment must pass the same fail-closed protection context. Reject a lexical `.git` component; an existing path or ancestor that resolves to the worktree `.git` entry, Git directory, or Git common directory; the conventional `implementation-programs` root; the actual or intended manifest program root; and every manifest-resolved logical-role, increment-storage, or closure-storage control path. Use `RepositoryInspection.git_directory` and `.git_common_directory` for normal and linked worktrees, filesystem identity for existing aliases, and exact component boundaries so `.github`, `.gitignore`, and ordinary product names containing `git` remain allowed. Missing, empty, stale, or unresolvable protection metadata is an error, never permission.
- Baseline capture and every later reassessment must repeat one shared component-by-component `lstat` walk and workspace-containment proof. Reject any unsafe existing component or containment escape, but return an absent snapshot after the first missing component so a caller may permit an absent suffix for Create, accepted Delete tombstones, inherited absence, or already-absent user work. Delete/Modify/Preserve baseline callers and every present-state caller separately require the ancestors and final regular file their operation needs; no earlier safe observation authorizes a later swapped ancestor.
- `Delete` means the approved final state is absent. Never encode absence as `Modify`, `Preserve`, an omitted path, an empty digest, or a fabricated digest.
- `authorized` requires every Delete target to remain byte-identical to its baseline; `implementing` permits either the exact baseline file or its absence; `reviewing` and later require absence. A changed-but-present Delete target is always invalid.
- A typed local Delete remains within the exact plan-bound `modify-workspace` action. It does not grant the separately named `destructive-operation`, cleanup, migration, Git, publication, deployment, provider, or external-state actions.
- Keep public `prepare_exact_plan(program_root, exact_plan_bytes, observation)`, `materialize_exact_plan(program_root, submitted_plan_prompt, observation)`, and `required_future_lifecycle_writes(program_root, workspace_root, increment_id)` signatures unchanged.
- Keep deterministic candidate construction, exact-prefix adoption, atomic compare-and-swap, no-overwrite publication, immutable ledgers, and status-last ordering at every existing transaction boundary.
- V2 current results use operation-section order followed by exact file-map order; cumulative v2 states replace an already-owned path in place and append newly owned paths in current-result order. Preserve every v1 lexical ordering rule and byte sequence.
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
6. `program_activation.py::_build_v3_setup_record(...)` imports and writes only `SETUP_ACTIVATION_SCHEMA` (`setup-activation-decision/v1`), so a setup-v2 activation cannot be a truthful Task 1 GREEN until that writer and both authority validators dispatch together.
7. The consumer rescan found additional hard-coded v1 edges. `program_discovery.py::_exact_closure_prefix_disposition(...)` requires diff-disposition and closure-preparation v1; its manifest-v3 loader validates full state authority before inspecting plan, review, acceptance, closure, or rollover prefixes and otherwise falls through to generic routes. `program_continuation.py::build_accept_continue_candidate(...)` rewrites its acceptance binding with `DIFF_DISPOSITION_BINDING_SCHEMA` v1, while its accepted-state command, parser, and embedded product values are fixed to `implementation-accepted-state-continuation-binding/v1` and `ProductDeltaPath(sha256: str)`. All must dispatch on exact families for v2 retry, recovery, and continuation to work.
8. Current product deltas and inherited paths are lexically sorted, while a typed v2 result needs one specified order. V2 therefore requires operation-section/exact-map result order and stable cumulative replace-in-place/append semantics while leaving v1 sorting unchanged.
9. Current activation and workspace assessment check the final `Path` with `is_symlink()`/`is_file()` but do not share a component walk. A safe final file beneath a later-swapped symlink ancestor can therefore evade the intended workspace-bound path contract. The shared walk must still preserve the current valid absence semantics for a Create target whose parent is not created yet and for already-absent user work; operation callers, not the primitive walk, own required-presence rules.
10. The real pipeFlow lifecycle does not begin with all 27 Task 8 Delete targets. `test/legacy/characterization.test.ts` is absent at setup, created and accepted in Task 1, inherited as present, and deleted with the other 26 legacy files in Task 8. A fixture that pre-creates all 27 paths does not exercise future Delete allocation, predecessor collision facts, or a real late tombstone.
11. `implementing-staged-plans-bootstrap-execution-review-runbook.md` declares itself the Plan A `0.1.1` plus Plan B `0.1.2` boundary and documents singleton/final-only closure. It is a live operational runbook, so `0.1.3` path states and complete-chain closure must update it rather than reclassifying it as historical.
12. `program_activation.py::advance_execution_state(...)` writes and retry-adopts only `implementation-execution-transition/v1` with `product_delta_sha256`, while `state_authority.py` accepts only that v1 shape and derives the event identifier from that v1 digest field. A setup-v2 writer output therefore has no exact execution-transition schema, result-family binding, event seed, state-authority route, or discovery retry/recovery contract even though Task 2 claims a complete v2 baseline/result family.
13. `_safe_relative_path(...)` and exact-file-map normalization accept `.git/config`. In a normal checkout that is a regular file; in a linked worktree `.git` itself is a regular gitfile. `RepositoryInspection` already records the resolved Git directory and common directory, but blocked recovery and state authority currently synthesize inspections with both fields empty, while the shared test snapshot intentionally skips `.git`. Path-shape validation and snapshot equality therefore cannot enforce the protected boundary.
14. `program_closure.py::_traceability_context(...)` counts every requirement not assigned to the final increment as unresolved, then fabricates every disposition as `implemented` with the final increment as owner and no accepted evidence. Task 6 also names a required `handoff addendum`, but the manifest increment storage and production rollover transaction create only a review packet, handoff, successor brief, and bound rollover record; the addendum belongs only to the preserved legacy continuity model and has no new-model writer or storage role.

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
- `skills/implementing-staged-plans/scripts/state_authority.py` — own shared versioned file-map types, exact nested-schema routing, execution-transition/result-family bindings, state bindings, and v1 compatibility rejection.
- `skills/implementing-staged-plans/scripts/repository_preparation.py` — own the canonical Git/program/control protection context, parse exact-file-map v2, parse baseline v2, and assess present/absent path states.
- `skills/implementing-staged-plans/scripts/program_activation.py` — construct Delete-aware plan candidates/baselines and bind v2 execution transitions without changing public signatures.
- `skills/implementing-staged-plans/scripts/program_discovery.py` — route manifest-v3/setup-v2 plan preparation/materialization, review, acceptance, immediate/later rollover, closure, and divergent prefixes by exact schema family before generic state validation.
- `skills/implementing-staged-plans/scripts/execution_discipline.py` — validate deleted ownership and semantic surfaces without treating Delete as a physical rename.
- `skills/implementing-staged-plans/scripts/review_coordination.py` — carry and validate the v2 accepted path-state result in review evidence and packets.
- `skills/implementing-staged-plans/scripts/program_review.py` — persist/revalidate Delete-aware review and remediation bindings, including the v2 remediating-to-reviewing execution transition.
- `skills/implementing-staged-plans/scripts/diff_disposition.py` — bind the exact reviewed v2 product result during acceptance.
- `skills/implementing-staged-plans/scripts/blocked_recovery.py` — freeze and revalidate Delete path states across blocked/resume.
- `skills/implementing-staged-plans/scripts/program_continuation.py` — consume accepted present/absent results and render/parse exact accepted-state-continuation v1/v2 commands without coercing absence to a string digest.
- `skills/implementing-staged-plans/scripts/program_rollover.py` — persist v2 rollover records with accepted review/diff/handoff bindings and cumulative inherited present/absent path states.
- `skills/implementing-staged-plans/scripts/continuity_closure.py` — validate/render versioned closure reconciliation over accepted result bindings and cumulative path states.
- `skills/implementing-staged-plans/scripts/program_closure.py` — build closure from complete accepted-increment evidence, traceability-owned requirement dispositions, later-invalidation checks, and final cumulative state.
- `skills/implementing-staged-plans/scripts/validate_package.py` — set and enforce package version `0.1.3`.
- `skills/implementing-staged-plans/SKILL.md` — route and explain the Delete-capable nested v2 family.
- `skills/implementing-staged-plans/agents/openai.yaml` — describe exact local Delete support without implying generic destructive authority.
- `skills/implementing-staged-plans/references/program-authority.md` — document v1/v2 setup pairing and authority limits.
- `skills/implementing-staged-plans/references/program-discovery.md` — document prefix-first exact v1/v2 discovery, retry, and recovery classification.
- `skills/implementing-staged-plans/references/repository-preparation.md` — own the v2 file-map grammar and baseline path-state rules.
- `skills/implementing-staged-plans/references/execution-discipline.md` — own lifecycle-state behavior for Delete.
- `skills/implementing-staged-plans/references/review-coordination.md` — own review/remediation result binding.
- `skills/implementing-staged-plans/references/state-authorization.md` — own acceptance and rollover version routing.
- `skills/implementing-staged-plans/references/continuity-closure.md` — own cumulative tombstone and closure rules.
- `docs/reference.md`, `docs/workflows.md`, `docs/troubleshooting.md`, `docs/maintainers.md`, `docs/installation.md` — synchronize the user-visible `0.1.3` contract, failure messages, and installation examples.
- `implementing-staged-plans-bootstrap-execution-review-runbook.md` — extend the live bootstrap/execution/review runbook through the `0.1.3` path-state, discovery, rollover, and complete-chain closure contract.
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
- `skills/implementing-staged-plans/scripts/program_bootstrap.py`, `program_launch.py`, `approval_checkpoint.py`, and `task_prompt.py` — exercise their existing generic routes in tests; change them only if a focused RED test proves an exact-schema integration defect.
- `/Users/CoveMB/Code/CoveMB/implementation-plugin/**` and `/private/tmp/pipeflow-effect-flow.4Ox4Wl/**` — read-only/out of scope throughout implementation.

---

## Implementation Kickoff Preflight

Before Task 1, record and require all of the following without changing the tree:

```bash
rtk git status --short --branch
rtk git rev-parse HEAD
rtk sha256sum docs/superpowers/plans/2026-09-05-delete-operation-support.md
rtk git merge-base --is-ancestor b5eb689e780f48b218b807a4691f0994474e4178 HEAD
rtk git log --reverse --format='commit %H parents %P' --name-only b5eb689e780f48b218b807a4691f0994474e4178..HEAD
rtk git diff --name-only b5eb689e780f48b218b807a4691f0994474e4178..HEAD
rtk git diff --check b5eb689e780f48b218b807a4691f0994474e4178..HEAD
```

Expected: the branch is `repair/delete-operation-support` and clean; record the exact `rev-parse HEAD` and plan SHA-256 stdout as the immutable kickoff evidence for this execution; `merge-base --is-ancestor` exits `0`; every path printed beneath every commit in the candidate-to-kickoff log is exactly `docs/superpowers/plans/2026-09-05-delete-operation-support.md`; the aggregate diff prints that one path; and `diff --check` is empty. Stop before implementation if the candidate is not an ancestor, any commit or aggregate diff contains a non-plan path, the tree is dirty, the recorded kickoff HEAD is not an ancestor of a later implementation HEAD, or the plan no longer reproduces the recorded kickoff SHA-256.

---

### Task 1: Version the Setup-Level Delete Contract

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/program_setup.py`
- Modify: `skills/implementing-staged-plans/scripts/program_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `tests/program_bootstrap_support.py`
- Test: `tests/test_program_setup.py`
- Test: `tests/test_program_authority.py`
- Test: `tests/test_repository_preparation.py`
- Test: `tests/test_program_bootstrap.py`
- Test: `tests/test_program_activation.py`
- Test: `tests/test_program_discovery.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Consumes: manifest-v3 `setup_semantics` and the existing immutable setup decision flow.
- Produces: `SETUP_SEMANTICS_SCHEMA_V2`, `OPERATION_ENVELOPE_SCHEMA_V2`, `SETUP_RECAP_SCHEMA_V2`, `SETUP_RECAP_CHECKPOINT_SCHEMA_V2`, `SETUP_DECISION_ADAPTER_SCHEMA_V2`, and `SETUP_ACTIVATION_SCHEMA_V2`.
- Produces: `_operation_contract(semantics: Mapping[str, object]) -> tuple[tuple[str, ...], bool]`, returning the exact supported-operation tuple and whether Delete fields are required.
- Produces: `DeleteProtectionContext`, `build_delete_protection_context(workspace_root: Path, manifest_program_root: Path, manifest: Mapping[str, object], inspection: RepositoryInspection) -> DeleteProtectionContext`, and `validate_delete_target_path(context: DeleteProtectionContext, relative_path: str) -> None` as the only Delete protection policy used by setup and later tasks.
- Produces test helpers: `BootstrapFixture.configure_delete_setup_v2(allocation: Mapping[str, object]) -> dict[str, object]`, `configure_v1_envelope_with_delete() -> list[str]`, and `configure_mixed_setup_versions() -> list[str]`; each recomputes the semantic digest after its exact mutation.
- Produces: recap, checkpoint, decision, activation-record, program-authority, and state-authority dispatch selected from the exact setup/envelope family before any activation record is written.
- Produces: manifest-v3/setup-v2 sequence-zero activation-prefix discovery that returns `program-activation-retry-ready` for every byte-exact incomplete prefix and `program-activation-recovery-required` for every started mixed, out-of-order, or divergent prefix before generic invalid-state routing.
- Preserves: every v1 setup/envelope/recap/decision/activation byte and error route.

- [ ] **Step 1: Write failing setup and authority tests**

Add these test cases with a helper that rewrites the candidate before recomputing `setup_semantics_sha256`:

```python
def delete_allocation(
    path: str,
    increment_id: str,
    *,
    collision: str = "existing",
) -> dict[str, object]:
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
        "collision": collision,
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

Also assert proposal validation, publication, recap checkpoint, and setup decision accept the all-v2 nested family and reject a substituted v1 record or v2 record in a v1 setup. Add a two-increment allocation for one initially absent exact path: `Create` in the first increment with facts `absent`/`none`/`None`/`none`, then `Delete` in its strict successor with facts `regular-file`/`none`/`100644`/`accepted-predecessor`. Require one same-path Create allocation in a transitive predecessor for `accepted-predecessor`, and reject an unrelated, same-increment, later, or absent predecessor allocation; the distinct operations are not a duplicate allocation. Keep an initially present Delete allocation on collision `existing` and reject any other collision/fact combination.

Before accepting either Delete allocation form, exercise the production protection validator in a normal temporary checkout and a real linked worktree. Reject `.git`, `.git/config`, a symlink or case/alias resolving into `.git`, the resolved `git_directory`, the resolved `git_common_directory`, `implementation-programs/**`, the intended `implementation-programs/<program_id>` publication target, an instruction-declared actual program root, `manifest.json`, every logical-role file, and the increment/closure storage roots even when the allocation says `protected: false`. In the linked worktree specifically prove that the regular `.git` gitfile is rejected. If the platform cannot create a case alias or hard link, skip only that alias variant and retain the symlink and linked-worktree cases. Positive controls must accept ordinary product files such as `.github/legacy.yml`, `.gitignore.backup`, and `src/legitimate-config.ts`; component matching must not become a substring ban.

Drive `program_activation.py::activate_program(...)` through the real sequence-zero transaction and assert that it writes `setup-activation-decision/v2`, not `setup-activation-decision/v1`, before the status-last transition; substitute either activation schema across families and require both program and state authority to fail closed. After each byte-exact v2 activation prefix, run discovery and require the existing `program-activation-retry-ready` route. For each started-prefix record class—setup activation decision, required source-gate decision, program approval, and workspace approval—change one bound field, substitute the opposite setup schema where applicable, or place the record out of order; require read-only discovery to return `program-activation-recovery-required`, `required_input == "activation-prefix-recovery"`, and `stop_required is True` without falling through to generic invalid-state or publication recovery. Keep malformed sequence-zero proposals with no activation transaction artifact on their existing invalid route.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_setup tests.test_program_authority tests.test_repository_preparation tests.test_program_bootstrap tests.test_program_activation tests.test_program_discovery tests.test_state_authority -v
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

In `repository_preparation.py`, add the protection context without changing the persisted repository-inspection v1 bytes:

```python
@dataclass(frozen=True)
class DeleteProtectionContext:
    workspace_root: Path
    git_directory: Path
    git_common_directory: Path
    protected_roots: tuple[Path, ...]
    protected_paths: tuple[Path, ...]

def build_delete_protection_context(
    workspace_root: Path,
    manifest_program_root: Path,
    manifest: Mapping[str, object],
    inspection: RepositoryInspection,
) -> DeleteProtectionContext:
    workspace = Path(workspace_root)
    if workspace.is_symlink() or not workspace.is_dir():
        raise ValueError("Delete protection requires a regular workspace root")
    workspace = workspace.resolve(strict=True)

    git_directory = Path(inspection.git_directory)
    git_common_directory = Path(inspection.git_common_directory)
    if not git_directory.is_absolute() or not git_common_directory.is_absolute():
        raise ValueError("Delete protection requires resolved Git metadata paths")
    if not git_directory.exists() or not git_common_directory.exists():
        raise ValueError("Delete protection Git metadata paths are missing")

    program_root = Path(manifest_program_root).absolute()
    try:
        program_root.relative_to(workspace.absolute())
    except ValueError as error:
        raise ValueError("manifest program root escapes the workspace") from error

    def managed_relative(value: object, label: str) -> PurePosixPath:
        if not isinstance(value, str) or not value or "\\" in value:
            raise ValueError(f"{label} is not a safe relative POSIX path")
        relative = PurePosixPath(value)
        if relative.is_absolute() or any(
            part in {"", ".", ".."} for part in relative.parts
        ):
            raise ValueError(f"{label} is not a safe relative POSIX path")
        return relative

    roles = manifest.get("logical_roles")
    increment_storage = manifest.get("increment_storage")
    closure_storage = manifest.get("closure_storage")
    if not isinstance(roles, Mapping):
        raise ValueError("manifest logical_roles must be an object")
    if not isinstance(increment_storage, Mapping) or not isinstance(
        closure_storage, Mapping
    ):
        raise ValueError("manifest lifecycle storage descriptors must be objects")

    increment_root = program_root.joinpath(
        *managed_relative(increment_storage.get("root"), "increment storage root").parts
    )
    closure_root = program_root.joinpath(
        *managed_relative(closure_storage.get("root"), "closure storage root").parts
    )
    control_paths = [program_root / "manifest.json"]
    control_paths.extend(
        program_root.joinpath(*managed_relative(value, f"logical role {role}").parts)
        for role, value in sorted(roles.items())
    )
    program_binding = manifest.get("program_binding")
    if isinstance(program_binding, Mapping):
        for field in ("path", "traceability_path"):
            control_paths.append(
                program_root.joinpath(
                    *managed_relative(
                        program_binding.get(field), f"program binding {field}"
                    ).parts
                )
            )

    protected_roots = (
        workspace / ".git",
        git_directory,
        git_common_directory,
        workspace / "implementation-programs",
        program_root,
        increment_root,
        closure_root,
    )
    for protected in (*protected_roots, *control_paths):
        if protected.is_symlink():
            raise ValueError("Delete protection metadata contains a symlink")
    return DeleteProtectionContext(
        workspace_root=workspace,
        git_directory=git_directory.resolve(strict=True),
        git_common_directory=git_common_directory.resolve(strict=True),
        protected_roots=tuple(path.absolute() for path in protected_roots),
        protected_paths=tuple(path.absolute() for path in control_paths),
    )

def validate_delete_target_path(
    context: DeleteProtectionContext,
    relative_path: str,
) -> None:
    relative = PurePosixPath(relative_path)
    if (
        not relative_path
        or "\\" in relative_path
        or relative.is_absolute()
        or relative.as_posix() != relative_path
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ValueError("Delete target must be one normalized repository-relative path")
    if ".git" in relative.parts:
        raise ValueError(f"Delete target is protected: {relative_path}")

    candidate = context.workspace_root.joinpath(*relative.parts).absolute()
    protected = (*context.protected_roots, *context.protected_paths)
    if any(candidate == item or candidate.is_relative_to(item) for item in protected):
        raise ValueError(f"Delete target is protected: {relative_path}")

    current = context.workspace_root
    for part in relative.parts:
        current = current / part
        if not current.exists() and not current.is_symlink():
            break
        if current.is_symlink():
            raise ValueError(f"Delete target has a symlink component: {relative_path}")
        resolved = current.resolve(strict=True)
        for protected_path in protected:
            protected_resolved = protected_path.resolve(strict=False)
            same_file = protected_path.exists() and current.samefile(protected_path)
            if (
                same_file
                or resolved == protected_resolved
                or resolved.is_relative_to(protected_resolved)
            ):
                raise ValueError(f"Delete target is protected: {relative_path}")
```

The builder requires a strict regular non-symlink workspace root, non-empty absolute Git directory/common-directory values from a fresh `inspect_repository(...)`, a manifest program root lexically beneath the workspace, and safe exact manifest path descriptors. Its protected roots are the workspace `.git` entry, both resolved Git metadata directories, the conventional `workspace/implementation-programs` root, the intended or actual manifest program root, and the manifest's increment/closure storage roots. Its protected exact paths include `manifest.json`, all resolved `logical_roles`, and every manifest binding path. Fail closed if any required protection value is missing, ambiguous, escaping, or symlinked.

The validator first rejects any normalized path with an exact lexical `.git` component. It then proves lexical workspace containment and walks existing components with `lstat`; compare existing filesystem identities with `samefile` where available and compare strict resolved ancestors against every protected root/path. This must catch case aliases, the linked-worktree gitfile, the per-worktree Git directory, the shared common directory, and symlink aliases before reading target bytes. Use exact path-component containment, not string prefixes. An absent suffix may still be classified by Task 2 only after its nearest existing ancestor passes this protection check.

For v2, require `accepted_state == "absent"`, one allowed `content_disposition`, and a non-empty rationale only on Delete allocations; reject those fields on non-Delete allocations. Require an exact-path Delete allocation to be program-owned, non-protected, non-user-work, and to declare collision `existing` or `accepted-predecessor`. The latter is valid only when the setup dependency graph contains one same-path `Create` allocation in a strict transitive predecessor; it does not weaken the activation-time exact fact comparison. Preserve all existing ownership, file-kind, link-kind, mode, collision, overlap, and duplicate-allocation checks.

For each setup-v2 Delete allocation, derive a fresh repository inspection from the setup workspace binding, reproduce the persisted workspace observation, build the context with the intended publication root, and call `validate_delete_target_path(...)`. Proposal validation, activation, and every activation retry must repeat this check; an old setup decision is not protection evidence. Use a local import if needed to avoid a `program_setup.py`/`repository_preparation.py` import cycle. Setup-v1 never enters this Delete-only route and retains exact bytes.

Select recap/checkpoint/adapter/activation schema versions solely from `_operation_contract(...)`. In this same task, change `program_activation.py::_build_v3_setup_record(...)` to select and write the matching activation schema instead of importing and unconditionally emitting `SETUP_ACTIVATION_SCHEMA`; update its activation-prefix adoption tests before calling this task GREEN. Extend `program_authority.py::SETUP_AUTHORITY_RECORD_SCHEMAS`, `program_setup.py`'s activation-record loaders/validators, and `state_authority.py::SETUP_ONLY_STATUS_SCHEMAS` plus its manifest-v3 family validation without admitting the v2 records to setup-v1 or legacy manifests.

In `program_discovery.py::_single_bootstrap_prefix_disposition(...)` and `_load_setup_candidate(...)`, inspect the sequence-zero transaction prefix before proposal-publication or generic program/state rejection. Preserve the existing pristine `program-setup-ready`, pending-gate `source-gate-approval-ready`, and exact-prefix `program-activation-retry-ready` routes for both setup families. When activation has started and `inspect_sequence_zero_activation_prefix(...)` reports a mixed, out-of-order, or divergent decision, gate, or approval prefix, return `program-activation-recovery-required` with the exact prefix issues for diagnosis; `_single_bootstrap_prefix_disposition(...)` must not relabel that owned activation divergence as `proposal-publication-recovery-required`, and `_load_setup_candidate(...)` must not relabel it as generic invalid. Keep immutable publication-manifest/owner/inventory divergence on `proposal-publication-recovery-required`. The activation recovery route is classification only: it must not rewrite, adopt, append, or delete any prefix byte. A malformed pristine proposal with no activation transaction artifact remains on its existing invalid or publication-recovery route.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command.

Expected: all setup, authority, generic proposal-publication, and sequence-zero discovery tests pass; every exact incomplete v2 activation prefix is retry-ready, every started mixed or divergent prefix is activation-recovery-required without mutation, the recap exposes each Delete fact, and legacy bytes stay exact.

- [ ] **Step 5: Commit the setup contract**

```bash
rtk git add skills/implementing-staged-plans/scripts/program_setup.py skills/implementing-staged-plans/scripts/program_authority.py skills/implementing-staged-plans/scripts/repository_preparation.py skills/implementing-staged-plans/scripts/program_activation.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/scripts/state_authority.py tests/program_bootstrap_support.py tests/test_program_setup.py tests/test_program_authority.py tests/test_repository_preparation.py tests/test_program_bootstrap.py tests/test_program_activation.py tests/test_program_discovery.py tests/test_state_authority.py
rtk git commit -m "feat: add typed delete setup contracts"
```

---

### Task 2: Add Exact-Plan, Baseline, Product Path-State, and Execution-Transition Semantics

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py` (sequence-one-and-later exact-plan routing only; preserve Task 1 sequence-zero activation routing)
- Test: `tests/test_repository_preparation.py`
- Test: `tests/test_program_activation.py`
- Test: `tests/test_approval_checkpoint.py`
- Test: `tests/test_program_discovery.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `ExactFileMapV2`, `ExecutionBaselineV2`, and `InheritedPathStateV2` while retaining `ExactFileMap` and `ExecutionBaseline` as v1 types.
- Produces: `file_map_entries(file_map) -> tuple[tuple[str, tuple[str, ...]], ...]` and `file_map_paths(file_map, *, mutable_only: bool) -> tuple[str, ...]` so consumers do not reconstruct operation inventories inconsistently.
- Produces: `WorkspacePathSnapshot(relative_path: str, exists: bool, sha256: str | None, mode: str | None, link_count: int | None)` and `inspect_workspace_path(workspace_root: Path, relative_path: str) -> WorkspacePathSnapshot`, the single component-by-component path-safety and containment check used at baseline and every reassessment.
- Consumes: Task 1's `DeleteProtectionContext` and `validate_delete_target_path(...)`; every Delete branch validates protection immediately before its component walk and never accepts an empty/synthetic Git protection context.
- Produces: `product_result_schema_version` on `ExecutionWorkspaceAssessment`; v1 remains `implementation-product-delta/v1`, v2 is `implementation-product-path-states/v2`.
- Produces: `EXECUTION_TRANSITION_SCHEMA_V2 = "implementation-execution-transition/v2"` and `ExecutionTransitionReceiptV2`; v2 status bindings use `product_result_schema_version` and `product_result_sha256`, never `product_delta_sha256`.
- Produces: exact baseline/result/transition pairing: baseline v1 + product-delta v1 + execution-transition v1, or baseline v2 + product-path-states v2 + execution-transition v2. A missing, mixed, substituted, or dual-family field set fails before adoption or any status write.
- Produces: an execution-transition event identifier derived from the exact family-specific seed and a retry path that adopts only a fully reproduced binding, `previous_state`, `transition_authority`, result digest, and event identifier.
- Produces: v2 product states in operation-section order and exact file-map order; v1 product deltas retain their current lexical ordering and bytes.
- Produces: manifest-v3/setup-v2 sequence-one-and-later `plan-preparation-*` and `plan-materialization-*` retry/recovery classification from exact transaction prefixes before full state-authority validation or generic lifecycle routing; Task 1 exclusively owns sequence-zero activation-prefix classification.
- Produces: writer-to-fresh-discovery coverage for implementing and reviewing status plus `execution-transition-recovery-required` classification for v1/v2 transition substitution or digest/event divergence.
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

Drive `program_activation.py::advance_execution_state(...)` through `authorized -> implementing -> reviewing` for one setup-v1 program and one setup-v2 program. For each family, pass the production-written implementing and reviewing statuses directly to fresh discovery and require `resume`, with state authority clean. Inject a lost response after each status-last write and call the same transition again: the exact binding must return `recovered is True` without changing status bytes. Recompute each `event_id` from the exact seed specified in Step 5 and compare it with both `execution_transition_binding.event_id` and `transition_authority.event_id`.

For both target states, substitute a v1 transition into the v2 status and a v2 transition into the v1 status; also try both digest field families together, remove the required result schema, change the result digest, change one seed-bound field, and change only `event_id`. The direct retry must raise `execution-transition-recovery-required: status binding differs`, fresh state authority must report `execution transition binding is invalid` or the family-specific reviewed-result mismatch, discovery must return `execution-transition-recovery-required` with `required_input == "execution-transition-recovery"` and `stop_required is True`, and every rejected case must preserve status bytes. Compare the production v1 transition/status serialization with the existing frozen `tests/fixtures/program-bootstrap/v0.1.1` route byte-for-byte; do not update that fixture.

Add one manifest-v3/setup-v2 program whose first increment contains only Create/Modify/Preserve, including Create for a currently absent exact path, and whose strict successor owns Delete for that same path with collision `accepted-predecessor`. In this task, assert only that the first increment rejects a v1 or unversioned file map, accepts file-map/baseline/result v2 with an empty Delete section, and reaches `authorized` with an exact v2 baseline. Do not fabricate or require accepted predecessor state here: Task 3 owns v2 review/diff acceptance, and Task 5 owns the production rollover into the Delete increment. Assert the inverse family substitution fails for setup v1.

For path traversal, add `nested/legacy.ts` with a real directory ancestor and capture an authorized baseline. Replace `nested` after authorization with a symlink to a temporary directory outside the workspace, then require the next `validate_execution_workspace(...)` call to report `execution path has symlinked ancestor: nested/legacy.ts` before reading or hashing the external target. Repeat the swap with a symlink into `.git` and into the active program root, and where supported with a hard-link/case alias to an existing protected file. Cover the same rejection during baseline construction, and assert every external/control sentinel is unchanged in both cases. Inject a lost response after the baseline and action-authorization prefixes, perform the protected swap, then retry materialization: it must return the exact plan-domain recovery stop without adopting authorization or writing status. A direct v2 baseline or inherited-state tamper that introduces `.git/config` or a manifest control path must also fail before hashing or status writes; repository snapshots that skip `.git` are not sufficient evidence, so assert the protected sentinel bytes and Git identity explicitly.

Preserve the current positive cases for an absent v1 Create target below a not-yet-created parent and an already-absent tracked user-work path whose suffix is missing. A missing suffix returns `exists=False`; Delete/Modify/Preserve baseline callers must then reject it as missing, while Create, accepted/inherited absence, and already-absent user-work callers may accept it. Add positive v2 Delete baselines for `.github/legacy.yml` and an ordinary nested product file to prove the protection rule does not narrow legitimate product deletion.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_preparation tests.test_program_activation tests.test_approval_checkpoint tests.test_program_discovery tests.test_state_authority -v
```

Expected: the unversioned parser test exposes the current Delete-to-Modify absorption; v2 imports, absent-result assertions, v2 transition schema, and writer-to-discovery assertions fail; existing v1 tests pass.

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

`parse_exact_file_map(...)` must first reject every unrecognized `###` heading within the v1 file-map body. Select v2 only from the exact schema marker, then require one ordered Create/Modify/Delete/Preserve heading. The Delete section may be empty for any increment in a setup-v2 program; the other required sections retain their current non-empty contract. Duplicate and unsafe path rejection remains global across all sections.

Add `implementation-execution-baseline/v2` in `repository_preparation.py` with an exact v2 file-map object, current path baselines, user-work baselines, and ordered `inherited_path_states`. Dispatch `execution_baseline_from_value(...)` on the exact baseline schema. In `program_activation.py::_build_plan_candidate(...)`, select file-map and baseline v2 for every increment solely when the manifest's exact setup/envelope pair is v2, even when Delete is empty and no inherited state exists; reject v1/v2 substitutions in both directions before persistence. Do not add fields to the v1 serialization.

Implement `inspect_workspace_path(...)` with `os.lstat`, never `Path.is_file()` or `resolve()` as the symlink test: normalize the relative POSIX path; `lstat` and reject a symlinked/non-directory supplied workspace root before resolving it strictly; prove the lexical candidate is beneath that root; then `lstat` components from the root downward. Every existing ancestor must be a non-symlink directory whose strict resolution remains inside the strict workspace root. If a component is missing, stop walking and return one absent snapshot for the whole remaining suffix without resolving, reading, or creating it. If the final component exists, require a regular non-symlink file, prove its strict resolution remains inside the workspace, and only then return its digest, mode, and link count. Reject every other existing component kind or containment escape.

Use this helper in activation allocation-fact checks, `_path_baselines(...)`, `_user_work_baselines(...)`, and every current, inherited, and user-work branch of `validate_execution_workspace(...)`. Every branch whose current operation or inherited state is Delete must first rebuild Task 1's protection context from the current manifest and fresh real `RepositoryInspection`, then call `validate_delete_target_path(...)`; a persisted allocation, baseline, action authorization, review, or accepted result is never a waiver. Callers then enforce their own presence contract: baseline Delete/Modify/Preserve and every state that expects presence require an existing regular file; Create before creation, Delete after removal, inherited tombstones, and recorded already-absent user work permit an absent suffix. A later lifecycle reassessment must repeat both the protection check and complete walk; an authorization-time result is never reused as current path-safety evidence.

- [ ] **Step 4: Implement Delete-aware candidate and workspace validation**

In `program_activation.py::_build_plan_candidate(...)`, require file-map v2 for the complete setup-v2 program family from its first increment. Match every non-managed current path, including each exact Delete path, to exactly one current-increment setup allocation. Keep lifecycle-managed writes limited to Create/Modify/Preserve. For the later-created Delete path, the first increment's Create facts must be absent/none/`None`/none; after accepted rollover, the Delete allocation must reproduce regular-file/none/mode/`accepted-predecessor`. Initially present Delete targets reproduce collision `existing`. A mismatched collision, ownership, file kind, link kind, mode, or inherited-state fact fails before plan or baseline persistence.

Use the shared operation iterator in `_path_baselines(...)`, `_user_work_baselines(...)`, `validate_required_managed_file_map(...)`, and `validate_execution_workspace(...)`. Include Delete in both the program-owned-operation check and the claimed-path/user-work-overlap set currently applied to Create/Modify. Enforce:

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

For v2 Create/Modify results emit `final_state: "present"` with the real digest. Construct v2 results by iterating `file_map_entries(...)` in Create, Modify, Delete, Preserve section order and retaining each section's exact path order; do not sort v2 states after construction. Keep the v1 result object, lexical sort, and hash byte-for-byte unchanged. Include Delete paths in mapped product dirt and claimed paths, but never in managed lifecycle requirements.

- [ ] **Step 5: Version execution-transition writes, adoption, and validation**

Keep `EXECUTION_TRANSITION_SCHEMA`, `ExecutionTransitionReceipt`, the v1 binding fields, and the v1 event seed byte-for-byte unchanged. Add:

```python
EXECUTION_TRANSITION_SCHEMA_V2 = "implementation-execution-transition/v2"
PRODUCT_PATH_STATES_SCHEMA_V2 = "implementation-product-path-states/v2"

@dataclass(frozen=True)
class ExecutionTransitionReceiptV2:
    prior_state: str
    increment_state: str
    status_sha256: str
    product_result_schema_version: str
    product_result_sha256: str
    recovered: bool
```

For a baseline/result v2 assessment, `advance_execution_state(...)` writes exactly this binding; `review_remediation_sha256` is the only additional field allowed, and is required only for the Task 3 `remediating -> reviewing` writer:

```python
{
    "schema_version": "implementation-execution-transition/v2",
    "event_id": event_id,
    "authorization_id": authorization_id,
    "prior_increment_state": current_state,
    "target_increment_state": target_increment_state,
    "prior_status_sha256": prior_sha256,
    "product_result_schema_version": "implementation-product-path-states/v2",
    "product_result_sha256": assessment.product_delta_sha256,
}
```

`product_result_sha256` is the canonical SHA-256 already computed over the ordered v2 path-state tuple; it must reproduce from `assessment.product_delta` without sorting or coercing `None`. Derive `event_id = _identifier("execution-transition", event_seed)` from exactly:

```python
{
    "program_id": status["program_id"],
    "program_revision": status["program_revision"],
    "increment_id": status["current_increment_id"],
    "prior_status_sha256": prior_sha256,
    "prior_increment_state": current_state,
    "target_increment_state": target_increment_state,
    "product_result_schema_version": "implementation-product-path-states/v2",
    "product_result_sha256": assessment.product_delta_sha256,
    "authorization_id": authorization_id,
}
```

Append `review_remediation_sha256` to that seed and binding only when `prior_increment_state == "remediating"`. `transition_authority.event_id` must equal the derived identifier and use the same authorization. `previous_state.status_sha256` must equal `prior_status_sha256`, and its sequence must be exactly one below the new status.

Select v1 or v2 only from the validated manifest setup/envelope, execution-baseline, and assessment result-schema tuple. The v1 binding has `product_delta_sha256` and no product-result fields; the v2 binding has the two product-result fields and no `product_delta_sha256`. In the same-target retry branch, rebuild the expected family, fields, canonical result digest, event seed, `previous_state`, and `transition_authority` before returning a recovered receipt; do not adopt from schema/target/digest alone. A mismatch raises the existing recovery-required error before any write.

In `state_authority.py`, validate the same exact field sets and family table, recompute the event identifier, and reject a cross-family or dual-family binding. While state is `implementing` or `remediating`, validate the entry digest's shape and seed binding but preserve it while product work may evolve; at `reviewing`, `verified`, `awaiting-diff-approval`, and `accepted`, recompute the v1 delta or canonical v2 path-state digest from the fresh assessment and require equality. Replace the current synthetic `RepositoryInspection(git_directory="", git_common_directory="", ...)` with a fresh `inspect_repository(...)`, require its observation to reproduce the supplied status-current observation, and pass its real Git metadata into Delete protection. Missing or changed Git metadata fails closed. Preserve the v1 error text and add `reviewed product result differs from its status binding` for v2. In `program_discovery.py`, classify either transition-invalid message and either reviewed-result mismatch as `execution-transition-recovery-required` before generic invalid routing; an exact production-written v1 or v2 transition proceeds to the existing `resume` route.

- [ ] **Step 6: Route exact setup-v2 plan prefixes before generic rejection**

In `program_discovery.py::_load_setup_candidate(...)`, preserve without reimplementing the exact setup-v1/setup-v2 sequence-zero activation retry/recovery routing completed in Task 1. For sequence one and later only, load the allocated transaction files and relevant ledgers, derive the fresh observation, and call `_exact_plan_prefix_disposition(...)` before `validate_state_authority(...)` or any generic `resume`/invalid route. Do not accept a prefix by state name alone. For a manifest-v3/setup-v2 program, interrupt standard-mode preparation after the exact plan and awaiting-plan status, and materialization after the plan approval, v2 baseline, and action authorization. Each byte-exact incomplete prefix must return the matching `plan-preparation-retry-ready` or `plan-materialization-retry-ready`; missing/out-of-order records, changed plan bytes, a v1 baseline, or changed v2 path-state order must return the matching recovery-required disposition. After the exact authorized status is written last, discovery returns `resume` only after full state validation. `approval:pre-approve` and `approval:full-increment` must exercise their shorter exact materialization prefixes and completed-status route. The same cases for setup-v1 keep their existing bytes and disposition names.

- [ ] **Step 7: Run the focused tests and verify GREEN**

Run the Step 2 command.

Expected: the exact parser, baseline, authorization, partial implementation, complete absence, transition writer/retry/discovery, cross-family rejection, and legacy-byte tests pass.

- [ ] **Step 8: Commit exact-plan, baseline, and execution-transition support**

```bash
rtk git add skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/repository_preparation.py skills/implementing-staged-plans/scripts/program_activation.py skills/implementing-staged-plans/scripts/program_discovery.py tests/test_repository_preparation.py tests/test_program_activation.py tests/test_approval_checkpoint.py tests/test_program_discovery.py tests/test_state_authority.py
rtk git commit -m "feat: validate delete path states"
```

---

### Task 3: Carry Absent Results Through Review and Diff Acceptance

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/execution_discipline.py`
- Modify: `skills/implementing-staged-plans/scripts/review_coordination.py`
- Modify: `skills/implementing-staged-plans/scripts/program_review.py`
- Modify: `skills/implementing-staged-plans/scripts/diff_disposition.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `tests/program_bootstrap_support.py`
- Test: `tests/test_execution_discipline.py`
- Test: `tests/test_review_coordination.py`
- Test: `tests/test_program_review.py`
- Test: `tests/test_diff_disposition.py`
- Test: `tests/test_program_discovery.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `implementation-review-evidence/v2`, `implementation-review-packet/v2`, `implementation-review-preparation/v2`, `implementation-review-remediation/v2`, `implementation-diff-disposition-binding/v2`, and `implementation-diff-disposition-command/v2` only for product path-state v2.
- Produces: review evidence field `product_result = {schema_version, sha256, ordered_path_states}`.
- Consumes: Task 2's exact execution-transition v1/v2 family; the remediation-return writer uses v2 result fields and seed extension for setup-v2 without redefining the schema.
- Produces: exact-family discovery of v2 acceptance prefixes and an `accepted-stop` route for an exact accepted v2 diff binding.
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

Add failures for a reappeared Delete target, changed path-state order, `final_state: present`, non-null absent digest, omitted Delete state, extra path state, v1/v2 review substitution, and remediation that restores or changes the deleted target without a renewed v2 assessment and review. In `tests/test_program_discovery.py`, persist an exact v2 diff-acceptance prefix and assert the pre-status prefix is `increment-acceptance-retry-ready`, the byte-exact accepted status is `accepted-stop`, and a substituted v1 binding, reordered state, or changed digest is `increment-acceptance-recovery-required` rather than resume or terminal.

After authorization and again after review preparation, replace an allowed Delete target or ancestor with an alias into `.git` or the program control root. Require `build_review_preparation(...)`, remediation return, `build_diff_acceptance_candidate(...)`, direct submission, state authority, and discovery to reject the protected target before reading it, accepting a packet, or appending an approval. Retry after an injected review-evidence or diff-approval prefix must preserve that prefix and return the matching review/acceptance recovery disposition. Keep a normal product Delete positive control through accepted-stop.

Drive one v2 remediation return through the production `program_review.py` writer. Require `implementation-execution-transition/v2`, the exact renewed product-result schema/digest, and an `event_id` derived from the Task 2 seed plus the exact `review_remediation_sha256`. Retry the byte-exact written status and require adoption without mutation. Substitute a v1 transition or v1 `product_delta_sha256` into that v2 return, and a v2 transition into the v1 control; require review retry, state authority, and discovery to fail on the exact transition family before any later review artifact is written. Preserve the existing v1 remediation-transition bytes.

This task owns the chronology assertion deferred from Task 2: drive a setup-v2 first increment containing only Create/Modify/Preserve through v2 review and exact `accept-stop`, with an empty Delete section in its file map/result family, and assert discovery returns `accepted-stop` before any successor or Delete plan is prepared. Use production review and diff writers; do not edit accepted status directly.

For manifest-v3/setup-v2 discovery, interrupt review preparation after evidence, packet, and verified status, then verify the exact awaiting-diff status written last routes to `resume` only after complete review-state validation. Interrupt acceptance after approval and accepted status. Every byte-exact incomplete review prefix returns `review-preparation-retry-ready`; the exact acceptance approval prefix returns `increment-acceptance-retry-ready`; the exact accepted status returns `accepted-stop`. Packet-before-evidence, changed evidence/packet/status, mixed v1/v2 review or command bytes, and changed/reordered accepted path states return the domain-specific recovery disposition before generic state validation. Repeat one setup-v1 control to prove its prompt bytes and route names are unchanged.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline tests.test_review_coordination tests.test_program_review tests.test_diff_disposition tests.test_program_discovery tests.test_state_authority -v
```

Expected: new v2 review/result schemas are absent and Delete surfaces cannot be represented.

- [ ] **Step 3: Implement typed review result persistence**

Extend execution ownership with a literal `delete` disposition: it requires a non-empty pre-write fingerprint, exact `post_write_fingerprint == "absent"`, program ownership, and no accepted user-work overlap. Add `deleted` to execution surface changes and require one semantic naming/compatibility record for each deleted path; keep physical `renamed` rejection unchanged.

When `assessment.product_result_schema_version` is v2, `program_review.py` writes v2 review evidence containing the exact ordered states and v2 preparation/remediation bindings. `review_coordination.py` validates that the result digest is the canonical digest of those exact states and renders absent paths as absent—never as files with digests. Every review, remediation, diff-candidate, diff-submission, retry, state-authority, and discovery entry point must obtain a fresh real repository inspection and repeat Task 1's Delete protection check through `validate_execution_workspace(...)`; do not trust the baseline or prior result to prove that a path is still outside control metadata.

For a v2 remediation return, `program_review.py` must consume Task 2's execution-transition contract and emit the exact v2 binding with `product_result_schema_version`, `product_result_sha256`, and `review_remediation_sha256`; its event seed is the Task 2 v2 seed plus that remediation digest. Its retry/adoption branch must reproduce the full binding, event identifier, previous-state link, transition authority, and renewed assessment before returning recovered. Keep the v1 writer and retry bytes unchanged.

`diff_disposition.py` loads that exact reviewed result, freshly reassesses the workspace, compares schema/digest/states, and emits v2 binding/command schemas containing `product_result_schema_version`. Its submitted-prompt parser derives the expected command schema from the persisted review/result family before calling `parse_exact_prompt(...)`; it never accepts caller-selected family substitution. `program_discovery.py::_exact_review_prefix_disposition(...)`, `_exact_acceptance_prefix_disposition(...)`, and accepted-status routing must recognize only the exact v1 or v2 review/diff family, rebuild the matching production candidate, and classify byte-exact v2 accepted-stop and retry prefixes without a hard-coded v1 gate.

Extend `_load_setup_candidate(...)` so the exact review and acceptance classifiers run on manifest-v3/setup-v2 prefixes before full `validate_state_authority(...)` and before its generic `verified`, `awaiting-diff-approval`, or `accepted` fallbacks. A classifier's recovery-required result is authoritative and cannot be replaced by `invalid`, `resume`, or a generic retry. Keep v1 base-seed construction, prompt bytes, and discovery dispositions unchanged.

- [ ] **Step 4: Extend state validation by exact review/diff schema**

In `state_authority.py`, pair baseline v1 with review/diff v1 and baseline v2 with review/diff v2. Reject mixed families, missing result schemas, changed state order, or a digest that does not reproduce from `ordered_path_states`. Preserve the existing source-gate and status-last checks.

- [ ] **Step 5: Run the focused tests and verify GREEN**

Run the Step 2 command.

Expected: Delete absence is visible and immutable from review preparation through accepted status; every v1 golden remains exact.

- [ ] **Step 6: Commit review and diff support**

```bash
rtk git add skills/implementing-staged-plans/scripts/execution_discipline.py skills/implementing-staged-plans/scripts/review_coordination.py skills/implementing-staged-plans/scripts/program_review.py skills/implementing-staged-plans/scripts/diff_disposition.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/scripts/state_authority.py tests/program_bootstrap_support.py tests/test_execution_discipline.py tests/test_review_coordination.py tests/test_program_review.py tests/test_diff_disposition.py tests/test_program_discovery.py tests/test_state_authority.py
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

Add a post-block protection swap: after blocking a normal product Delete, alias its ancestor into `.git` and separately into the program root. `validate_blocked_context(...)`, resolution-candidate construction, exact resume submission, state authority, and discovery must fail without reading the protected target or appending a resolution. Retry after a persisted blocked prefix must preserve the prefix. Assert protected sentinel bytes directly because the shared repository snapshot omits `.git`.

- [ ] **Step 2: Run the focused tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_blocked_recovery tests.test_program_discovery tests.test_state_authority -v
```

Expected: blocked context v1 has no path-state binding and Delete is not included in plan-owned workspace paths.

- [ ] **Step 3: Implement v2 blocked-context binding**

Build a fresh execution assessment before writing blocked status. For a v2 baseline, bind its exact schema, result digest, and ordered current path states into the block identifier. `validate_blocked_context(...)` must reproduce all three from a fresh real `inspect_repository(...)` result before resolution; remove the synthetic inspection with empty Git directory/common-directory fields. Include Delete in `blocked_workspace_paths(...)` but exclude absent Delete targets from regular-file evidence bindings. The fresh assessment repeats `validate_delete_target_path(...)` before examining any present or absent Delete state.

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
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Test: `tests/test_program_continuation.py`
- Test: `tests/test_program_rollover.py`
- Test: `tests/test_multi_increment_lifecycle.py`
- Test: `tests/test_program_activation.py`
- Test: `tests/test_program_discovery.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `ProductPathStateV2(path, disposition, final_state, sha256)` without changing `ProductDeltaPath` v1.
- Produces: `ContinuationExtensionV2` carrying `accepted_product_path_states` and `accepted_product_result_sha256` without changing the v1 `ContinuationExtension.accepted_product_delta` contract.
- Produces: `ACCEPTED_STATE_CONTINUATION_SCHEMA_V2 = "implementation-accepted-state-continuation-binding/v2"` and `ContinuationCommandV2`, whose inherited-workspace value embeds the exact accepted product-result schema, digest, and ordered present/absent path states.
- Produces: `build_continuation_extension(...) -> ContinuationExtension | ContinuationExtensionV2 | None`, `build_accept_continue_candidate(acceptance, extension: ContinuationExtension | ContinuationExtensionV2 | None) -> DiffAcceptanceCandidate`, and `_build_accepted_state_command(...) -> ContinuationCommand | ContinuationCommandV2`, all selected by exact persisted family rather than nullable-field presence.
- Produces: `implementation-successor-authority-projection/v2`, `implementation-increment-rollover/v2`, `implementation-increment-rollover-binding/v2`, and `implementation-inherited-workspace/v2`.
- Produces: each v2 rollover record copies the accepted status's exact review-evidence, review-packet, and diff-disposition bindings, plus `accepted_diff_approval_binding = {event_id, sha256}` and the existing manifest-owned `handoff_binding`; these are immutable closure-chain evidence after the status file advances to the successor.
- Produces: accept-and-continue status bindings that retain the exact v1 or v2 diff-disposition family of the accepted stop candidate instead of rewriting v2 acceptance as v1.
- Produces: `validated_inherited_path_states(program_root, status, observation) -> tuple[InheritedPathStateV2, ...]` while preserving `validated_inherited_paths(...)` for v1.
- Produces: cumulative last-writer-wins path states only when the later increment explicitly owns the same path under a valid operation, using stable replace-in-place/append ordering rather than lexical resorting.
- Produces: manifest-v3/setup-v2 exact retry/recovery discovery for both immediate and later accepted-state continuation and rollover prefixes before generic state validation.
- Produces test fixture: `ThreeIncrementDeleteFixture` configured as setup/envelope v2 from sequence zero, with `accept_predecessor_create(path)`, `rollover(accepted_status, successor_id)`, `accept_delete(increment_id, path)`, `accept_unrelated_create(increment_id, path)`, `rollover_current(successor_id)`, and `prepare_current_plan()` methods that call production writers rather than editing lifecycle artifacts directly. Its same-path Create-then-Delete allocation declares collision `none` for Create and `accepted-predecessor` for Delete.

- [ ] **Step 1: Write failing three-increment inheritance tests**

```python
def test_late_delete_tombstone_survives_an_unrelated_successor(self) -> None:
    fixture = ThreeIncrementDeleteFixture()
    try:
        first = fixture.accept_predecessor_create("legacy.ts")
        second = fixture.rollover(first, "SECOND")
        self.assertEqual(
            second["inherited_workspace_binding"]["inherited_path_states"],
            [{
                "path": "legacy.ts",
                "final_state": "present",
                "disposition": "Create",
                "sha256": fixture.sha256("legacy.ts"),
            }],
        )
        fixture.accept_delete("SECOND", "legacy.ts")
        third = fixture.rollover_current("THIRD")
        self.assertEqual(
            third["inherited_workspace_binding"]["inherited_path_states"],
            [{
                "path": "legacy.ts",
                "final_state": "absent",
                "disposition": "Delete",
                "sha256": None,
            }],
        )
        fixture.prepare_current_plan()
        fixture.repository.joinpath("legacy.ts").write_text("reappeared\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inherited absent path reappeared: legacy.ts"):
            fixture.prepare_current_plan()
    finally:
        fixture.close()
```

The first increment's exact file map must be v2 with an empty Delete section, create `legacy.ts` from an absent baseline, and be fully accepted before the SECOND Delete increment is prepared. SECOND must receive `legacy.ts` as inherited-present and validate the Delete allocation's `accepted-predecessor` collision before accepting its absence. Do not substitute unrelated first-path and deleted-path names; this test proves the same path's real later-Delete lifecycle.

Assert immediate accept-and-continue and later accepted-state continuation both retain `implementation-diff-disposition-binding/v2`; a hard-coded v1 rewrite must fail before rollover. For later continuation, assert the rendered command schema is `implementation-accepted-state-continuation-binding/v2` and its `inherited_workspace.accepted_product_result` is exactly `{schema_version: implementation-product-path-states/v2, sha256, ordered_path_states}`, including `sha256: None` for the absent Delete state. Preserve one byte-exact v1 prompt fixture. Submitting a v1 command to v2 accepted status or a v2 command to v1 accepted status must fail schema parsing before any continuation record is written.

Add a positive recreation case where a later exact plan explicitly owns `legacy.ts` as Create from an inherited absent baseline. Add negative cases for implicit recreation, Delete against inherited absence, Modify/Preserve against absence, Create against inherited presence, omitted/reordered/duplicated state, mixed v1/v2 continuation commands and rollover chains, `str(None)`, and a current result that is not the exact reviewed/diff-accepted v2 result. Add an ordering case whose first result has two paths in non-lexical exact-map order and whose second result replaces the first path and adds a new path: the replacement must keep its existing cumulative slot, the untouched state must keep its slot, and the new state must append in current result order.

Assert that every completed v2 rollover record contains byte-reproducible accepted review-evidence/packet bindings, the complete v2 diff-disposition binding, one uniquely matching diff-approval record digest, and the existing handoff path/digest. Delete or tamper with the nonfinal review evidence, review packet, diff approval, or handoff and require `_validated_completed_rollover_records(...)`, state authority, discovery, later rollover, and closure preflight to fail. Do not add a handoff addendum field, filename, writer, or schema.

Before consuming a current result or cumulative inherited state, replace an allowed Delete target with a symlink/alias into `.git` or the program root, and separately inject `.git/config` or a manifest control path into a v2 rollover record. Immediate continuation, later continuation, rollover retry/adoption, state authority, and discovery must repeat the canonical protection check and stop before action/grant/handoff/status writes. Preserve an allowed product tombstone through the same paths as the positive control.

- [ ] **Step 2: Run focused continuation/rollover tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_continuation tests.test_program_rollover tests.test_multi_increment_lifecycle tests.test_program_activation tests.test_program_discovery tests.test_state_authority -v
```

Expected: current continuation coerces `None` to a string and current rollover requires each accepted path to remain a regular file with a digest.

- [ ] **Step 3: Implement versioned accepted-result consumption and cumulative merge**

For v2, load the exact product result from current review evidence, freshly reassess it with a real repository inspection and the canonical Delete protection context, and compare it with the diff binding before constructing continuation authority. Use a separate dataclass:

```python
@dataclass(frozen=True)
class ProductPathStateV2:
    path: str
    disposition: str
    final_state: str
    sha256: str | None

@dataclass(frozen=True)
class ContinuationExtensionV2:
    successor_increment_id: str
    successor_brief_bytes: bytes
    accepted_product_path_states: tuple[ProductPathStateV2, ...]
    accepted_product_result_sha256: str
    checkpoint_id: str
    rollover_authorization_id: str
    successor_grant_id: str
    successor_projection: Mapping[str, object]

@dataclass(frozen=True)
class ContinuationCommandV2:
    schema_version: str
    base_seed_sha256: str
    checkpoint_id: str
    rollover_authorization_id: str
    successor_grant_id: str
    accepted_status_sha256: str
    accepted_status_sequence: int
    program_id: str
    program_revision: int
    current_increment_id: str
    successor_increment_id: str
    successor_brief_sha256: str
    accepted_product_result_schema_version: str
    accepted_product_result_sha256: str
    successor_approval_mode: str
    selected_workspace: Mapping[str, object]
    inherited_workspace: Mapping[str, object]
    allowed_conditional_action_ceiling: tuple[str, ...]
```

Never pass v2 entries through `ProductDeltaPath(sha256: str)`, `ContinuationExtension`, or `ContinuationCommand`. Build the v2 inherited-workspace input exactly as:

```python
{
    "selected_workspace": selected_workspace,
    "accepted_product_result": {
        "schema_version": "implementation-product-path-states/v2",
        "sha256": product_result_sha256,
        "ordered_path_states": [asdict(item) for item in path_states],
    },
}
```

In `program_continuation.py::build_accept_continue_candidate(...)`, dispatch from the exact accepted-stop binding schema and emit the matching v2 binding and command rather than unconditionally importing/writing `DIFF_DISPOSITION_BINDING_SCHEMA` and `DIFF_DISPOSITION_COMMAND_SCHEMA`; reject a mixed acceptance/projection family. The v2 rollover record carries the accepted current result plus the canonical cumulative `inherited_path_states` and digest. Before the accepted status is replaced, copy its exact `review_evidence_binding`, `review_packet_binding`, and full v2 `diff_disposition_binding`; find the unique canonical approval record named by `approval_event_id` and bind its canonical JSON-line SHA-256. Retain the existing `handoff_binding` and validate its manifest-derived path and bytes during every completed-chain read. These fields belong only to rollover v2; do not change v1 bytes.

Each current result already follows operation-section order plus exact file-map order. Merge accepted increments without sorting: start with the prior cumulative list; for each current state in order, replace an existing path in its current list position only when the current exact operation inventory owns that path and its baseline agrees with the inherited state; append a newly owned path at the end. Reject duplicate paths in either input. Call `validate_delete_target_path(...)` for every current or inherited Delete state before merge or filesystem reassessment. This deterministic replace-in-place/append rule is part of the v2 digest contract; preserve the v1 lexical merge and bytes unchanged.

`validated_inherited_path_states(...)` validates every completed v2 rollover record, action, grant, review evidence, review packet, diff decision, diff approval, handoff, and cumulative digest. It requires present files to match exact digests and absent files to remain absent after fresh protection validation. Mixed result families or an unresolvable/empty Git protection context stop before persistence.

- [ ] **Step 4: Render and parse exact accepted-state continuation families**

Keep `ACCEPTED_STATE_CONTINUATION_SCHEMA`, `ContinuationCommand`, `_immediate_base_seed(...)`, and every rendered v1 field and byte unchanged. Add `ACCEPTED_STATE_CONTINUATION_SCHEMA_V2` and construct `ContinuationCommandV2` only when the accepted status has the exact v2 diff binding paired with `implementation-product-path-states/v2`. The v2 base seed and command bind `accepted_product_result_schema_version`, `accepted_product_result_sha256`, and the exact `inherited_workspace.accepted_product_result.ordered_path_states`; no field is inferred from a nullable digest.

Make `_build_accepted_state_command(...)` return `ContinuationCommand | ContinuationCommandV2` after exact persisted-family dispatch. In both `validate_submitted_continuation_prompt(...)` paths, build the expected command from persisted state first, call `parse_exact_prompt(submitted_prompt, expected.schema_version)`, and then compare `render_exact_prompt(asdict(expected))` byte-for-byte. `program_rollover.py` accepts the union and selects v1 delta or v2 path-state fields only from the command type/schema pair. Reject a prompt schema, diff binding, successor projection, accepted result, or rollover family mismatch before the first action-authorization append. The v1 prompt golden, parser errors, and accepted-state rollover bytes must remain exact.

- [ ] **Step 5: Consume inherited states in successor baselines**

`program_activation.py::_build_plan_candidate(...)` stores validated v2 inherited states in baseline v2 and strips their expected Git dirt from user-work observation. `repository_preparation.py::validate_execution_workspace(...)` validates untouched inherited states throughout the successor after repeating the canonical Delete protection check. It allows an explicit Create only from inherited absence and Modify/Delete/Preserve only from inherited presence; no current operation means the inherited state must remain exact. A path becoming protected is invalid even when its absent/present digest is otherwise unchanged.

`state_authority.py` validates exact v1 or v2 rollover/binding pairs and delegates to the matching inherited validator. Do not modify v1 cumulative-path or digest behavior.

- [ ] **Step 6: Classify exact v2 continuation and rollover prefixes**

In `program_discovery.py::_load_setup_candidate(...)`, run `inspect_increment_rollover(...)` for manifest-v3/setup-v2 accepted status before full state-authority validation and before generic accepted/resume routing. For both immediate accept-and-continue and later accepted-state continuation, interrupt after the rollover action authorization, successor grant, handoff, successor brief, rollover record, and successor status. Exact early prefixes return `increment-continuation-retry-ready` or `accepted-state-continuation-retry-ready`; exact navigation/record prefixes return `increment-rollover-retry-ready` or `accepted-state-rollover-retry-ready`; completed status returns `resume`. A substituted command/result family, missing/out-of-order record, changed path state/digest, or divergent prefix returns `continuation-recovery-required` or `accepted-state-continuation-recovery-required`, never generic `invalid`, `accepted-stop`, or `resume`. Preserve the existing setup-v1 and manifest-v2 route bytes and names.

- [ ] **Step 7: Run focused continuation/rollover tests and verify GREEN**

Run the Step 2 command.

Expected: present identities and absent tombstones survive unrelated increments; explicit recreation is valid; implicit or mixed-family state changes fail before writes.

- [ ] **Step 8: Commit rollover inheritance**

```bash
rtk git add skills/implementing-staged-plans/scripts/program_continuation.py skills/implementing-staged-plans/scripts/program_rollover.py skills/implementing-staged-plans/scripts/program_activation.py skills/implementing-staged-plans/scripts/repository_preparation.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/scripts/state_authority.py tests/test_program_continuation.py tests/test_program_rollover.py tests/test_multi_increment_lifecycle.py tests/test_program_activation.py tests/test_program_discovery.py tests/test_state_authority.py
rtk git commit -m "feat: inherit accepted delete tombstones"
```

---

### Task 6: Reconcile the Complete Accepted Path-State Chain at Closure

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/continuity_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/program_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Test: `tests/test_continuity_closure.py`
- Test: `tests/test_program_closure.py`
- Test: `tests/test_program_discovery.py`
- Test: `tests/test_multi_increment_lifecycle.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**
- Produces: `implementation-closure-reconciliation/v2`, `implementation-closure-packet/v2`, `implementation-closure-preparation/v2`, `implementation-program-closure-command/v2`, and `implementation-program-closure-command-binding/v2` for a v2 accepted chain.
- Produces: `AcceptedResultBindingV2(increment_id, product_result_schema_version, product_result_sha256, ordered_path_states, review_evidence_path, review_evidence_sha256, review_packet_path, review_packet_sha256, diff_approval_event_id, diff_approval_sha256, handoff_path, handoff_sha256)`; the final increment alone has both handoff fields `None`.
- Produces: reconciliation fields `accepted_result_bindings`, `final_inherited_path_states`, and `final_inherited_path_states_sha256`; `accepted_artifact_bindings` contains review-evidence/review-packet bindings for every accepted increment and the existing handoff binding for every nonfinal increment, never a v2 handoff addendum.
- Produces: `_accepted_increment_chain_v2(...)` and `_requirement_dispositions_v2(...)` as deterministic internal constructors over the exact rollover chain, final accepted status, immutable setup/traceability allocation, accepted review/diff evidence, and later accepted results.
- Produces: exact v2 discovery classification for closure-preparation and closure-approval retry/recovery prefixes.
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
            {
                item["requirement_id"]: item["owner"]
                for item in reconciliation["requirement_dispositions"]
            },
            {
                "REQ-FIRST": "FIRST",
                "REQ-DELETE": "SECOND",
                "REQ-FINAL": "THIRD",
            },
        )
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

`accepted_three_increment_delete_program()` must give the immutable traceability three independently owned requirements: `REQ-FIRST` assigned only to FIRST, `REQ-DELETE` assigned only to SECOND, and `REQ-FINAL` assigned only to THIRD. It creates and accepts `legacy.ts` in FIRST under setup/file-map/baseline/result v2 with an empty Delete section, validates it as inherited-present with collision `accepted-predecessor`, accepts its Delete in SECOND, and accepts an unrelated `final.txt` Create in THIRD before closure. The final plan allocates both manifest-owned closure paths. Assert closure succeeds, attributes the three owners exactly, retains FIRST and SECOND evidence, and reaches closure assertions rather than reporting that earlier-only requirements are unallocated from THIRD.

Add failures for a missing/reordered/duplicated accepted increment; a traceability allocation absent from the accepted chain; missing/tampered earlier review evidence, review packet, diff decision, diff approval, or nonfinal handoff; changed result digest; lost tombstone; unexpected reappearance; stale later-invalidation check; mixed v1/v2 chain; and absent path represented as an evidence file. A later unrelated `final.txt` result must not invalidate REQ-FIRST or REQ-DELETE. A THIRD recreation/change of `legacy.ts` without assigning REQ-DELETE to THIRD or recording a resolved disposition must invalidate REQ-DELETE and block closure; the same change is valid when THIRD is explicitly added to that requirement's immutable allocation and has accepted review/diff evidence.

Exercise `current_disposition` values explicitly. `allocated`, `implemented`, and `resolved` produce closure `implemented` only with a complete accepted allocation/evidence chain. `amended` requires a decision reference present in both approved and resolved amendment IDs. `deferred` requires one exact deferral with a non-`none` owner and decision reference. `rejected` and `not-applicable` retain their disposition and first traceability-ordered decision reference. A missing assignment/evidence, unsupported disposition, unmatched amendment, ownerless/mismatched deferral, or unresolved later invalidation increments the blocker and stops before writes; never fabricate `implemented`, final-increment ownership, or `approval_reference="none"` for a satisfied implemented requirement.

For protection closure coverage, accept a normal product tombstone, then alias its path into `.git` and separately into the program root before preparation and before approval retry. `build_closure_preparation(...)`, state authority, discovery, and command construction must fail before reading the protected target or persisting/adopting closure bytes. Assert Git/control sentinels directly.

In `tests/test_program_discovery.py`, interrupt v2 closure preparation after each persisted reconciliation/packet prefix. Require a byte-exact prefix to return `closure-preparation-retry-ready`, packet-without-reconciliation or any changed/reordered v2 path state/digest to return `closure-preparation-recovery-required`, an exact persisted closure approval before status-last completion to return `closure-approval-retry-ready`, and any substituted v1 closure-preparation/command binding or divergent closed status to return `closure-approval-recovery-required`. Assert the same disposition names and bytes remain unchanged for v1.

- [ ] **Step 2: Run closure tests and verify RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_program_closure tests.test_program_discovery tests.test_multi_increment_lifecycle tests.test_state_authority -v
```

Expected: current production closure emits only the final increment and has no cumulative path-state binding.

- [ ] **Step 3: Add versioned closure values and validators**

Keep `ClosureReconciliation` and `ClosurePacket` unchanged. Add v2 dataclasses with the three new result fields and exact schema-specific constructors/validators/renderers. Canonical validation requires:

```python
@dataclass(frozen=True)
class AcceptedResultBindingV2:
    increment_id: str
    product_result_schema_version: str
    product_result_sha256: str
    ordered_path_states: tuple[Mapping[str, object], ...]
    review_evidence_path: str
    review_evidence_sha256: str
    review_packet_path: str
    review_packet_sha256: str
    diff_approval_event_id: str
    diff_approval_sha256: str
    handoff_path: str | None
    handoff_sha256: str | None
```

The validator requires accepted-result bindings in exact accepted-increment order, one unique review evidence/packet and diff approval for each increment, and a handoff path/digest on every nonfinal binding only. For v2, `accepted_artifact_bindings` must equal the ordered labels/digests `increment:review-evidence`, `increment:review-packet`, then `increment:handoff` for each nonfinal increment. Reject optional or complete `handoff-addendum` coverage in v2. Leave the existing v1 validator, legacy `ContinuityHandoff` fields, fixtures, renderers, and addendum rule byte-for-byte unchanged.

Canonical final-state validation requires:

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

Do not put absent product paths in `evidence_paths`; bind their typed result and final-state digest instead. Requirement evidence paths are only manifest-owned review evidence, review packets, nonfinal handoffs, and the final reconciliation/closure-packet paths. The reconciliation may name the final closure paths, but it must not include its own or the packet's digest in `accepted_artifact_bindings`: the v2 preparation binding, awaiting/closed status, exact command, and approval bind both finalized digests after construction and avoid a circular hash.

- [ ] **Step 4: Build closure from the canonical rollover chain**

In `program_closure.py::build_closure_preparation(...)`, dispatch on the exact setup family paired with the accepted product-result schema. For v2, enumerate Task 5's fully validated `program_rollover.py::_validated_completed_rollover_records(...)` plus the final accepted status in order. The chain must begin at `setup_semantics.first_increment_id`, be contiguous and duplicate-free, end at status-current, contain every traceability-assigned increment exactly where declared, and leave no allocated successor. Build each `AcceptedResultBindingV2` from the rollover record's copied accepted bindings for nonfinal increments and the final status's live bindings for the final increment. Revalidate the manifest-derived review evidence/packet files, unique diff approval, typed result bytes/digest/order, and each nonfinal manifest-owned handoff path/digest before using them.

Replace `_traceability_context(traceability, final_increment_id)` on the v2 route with deterministic chain-aware construction:

```python
accepted_ids = tuple(item.increment_id for item in accepted_results)
for requirement in traceability["atomic_requirements"]:
    assigned = tuple(requirement["assigned_increments"])
    assigned_in_chain_order = tuple(item for item in accepted_ids if item in assigned)
    if assigned != assigned_in_chain_order or not assigned:
        unresolved += 1
        continue
    owner = assigned[-1]
    contributing = tuple(
        item for item in accepted_results if item.increment_id in assigned
    )
    later = accepted_results[accepted_ids.index(owner) + 1 :]
    invalidated = later_result_invalidates(contributing, later, requirement)
```

`later_result_invalidates(...)` compares the canonical path states contributed by assigned increments with every later accepted delta. An unrelated new path is non-invalidating. A later change to a contributed path is invalidating unless that later increment is also assigned to the requirement or the traceability carries a closure-valid amended/deferred/rejected/not-applicable disposition and decision reference. Every later increment must still have a valid requirements-scope review, accepted packet, and diff approval; a material finding whose `affected_requirement_or_invariant` names the requirement must be fully repaired and renewed before it can count as checked. Set `later_invalidation_checked=True` only after all later accepted results pass, and keep `later_invalidation_checks` in exact accepted-chain order.

For `allocated`, `implemented`, or `resolved`, emit closure `implemented` only after all assigned increments have accepted evidence and no later invalidation; set `owner` to the last assigned accepted increment and `approval_reference` to that owner's diff-approval event. For `amended`, require one traceability-ordered decision reference present in both `approved_amendment_ids` and `resolved_amendment_ids`. For `deferred`, require exactly one matching deferral tuple with a non-`none` owner and a decision reference. Preserve `rejected` and `not-applicable` only with a decision reference. Invalid allocation/evidence, unresolved or mismatched amendments, ownerless deferrals, unsupported dispositions, and unhandled invalidation increment the exact closure blocker and stop before writes.

Build each requirement's stable de-duplicated evidence paths in accepted-chain order from the assigned increments' review evidence and review packet, the existing handoff for any assigned nonfinal increment, then the manifest-owned final reconciliation and closure packet. Do not substitute product paths, and do not create a handoff addendum. Merge the final current result into the validated cumulative inherited states only after every path repeats the canonical Delete protection check; then construct v2 reconciliation and packet.

Version closure preparation, prompt, approval, command, and status bindings together. The v2 preparation/status/command binding includes the ordered accepted-result-binding digest, final inherited-state digest, reconciliation digest, and closure-packet digest. `state_authority.py::_validate_closure_readiness(...)` obtains a fresh real repository inspection, repeats protected Delete validation, and recomputes the complete accepted chain, per-requirement owners/evidence/dispositions/later checks, and exact final-state digest. Change `program_discovery.py::_exact_closure_prefix_disposition(...)` to accept only the exact v1 diff/preparation/command family or exact v2 family, rebuild the matching closure candidate for retry classification, and route every divergent partial v2 prefix to the existing preparation/approval recovery dispositions. In `_load_setup_candidate(...)`, run that exact classifier before full state-authority validation and before generic awaiting-closure/terminal routing. Remove its hard-coded v1 diff-binding and closure-preparation gates without using field presence as schema inference. Existing v1 closure remains on its current singleton or legacy route.

- [ ] **Step 5: Run closure tests and verify GREEN**

Run the Step 2 command.

Expected: closure succeeds only when all accepted increments and the final cumulative present/absent state are exact; every tamper fails before closure persistence.

- [ ] **Step 6: Commit closure reconciliation**

```bash
rtk git add skills/implementing-staged-plans/scripts/continuity_closure.py skills/implementing-staged-plans/scripts/program_closure.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/scripts/state_authority.py tests/test_continuity_closure.py tests/test_program_closure.py tests/test_program_discovery.py tests/test_multi_increment_lifecycle.py tests/test_state_authority.py
rtk git commit -m "feat: reconcile deleted paths at closure"
```

---

### Task 7: Add the Final PipeFlow Integration Regression and Synchronize Release Contracts

**Files:**
- Create: `tests/fixtures/delete-operation/pipeflow-task-8-delete-paths.json`
- Create: `tests/test_delete_operation_lifecycle.py`
- Modify: `docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md`
- Modify: `docs/superpowers/specs/2026-08-23-expanded-local-refactor-operations-design.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/agents/openai.yaml`
- Modify: `skills/implementing-staged-plans/references/program-authority.md`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Modify: `skills/implementing-staged-plans/references/repository-preparation.md`
- Modify: `skills/implementing-staged-plans/references/execution-discipline.md`
- Modify: `skills/implementing-staged-plans/references/review-coordination.md`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `skills/implementing-staged-plans/references/continuity-closure.md`
- Modify: `docs/reference.md`
- Modify: `docs/workflows.md`
- Modify: `docs/troubleshooting.md`
- Modify: `implementing-staged-plans-bootstrap-execution-review-runbook.md`
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
- Produces: a deterministic temporary-repository replay from an initially absent characterization path through predecessor creation/acceptance, later 27-path Delete, unrelated rollover, and final closure.
- Produces: `DeleteLifecycleFixture(existing_delete_paths: Sequence[str], later_created_delete_path: str, source_sha256: str)` configured as setup/envelope v2 from sequence zero, with the exact production-writer methods used in Step 2: `validate_and_publish_proposal()`, `render_setup_recap()`, `approve_activate_and_start()`, `prepare_create_and_accept_predecessor()`, `assert_characterization_is_inherited_present()`, `rollover_to_delete_increment()`, `prepare_and_authorize_delete_plan()`, `delete_every_target()`, `review_and_accept_delete_result()`, `rollover_to_unrelated_increment()`, `prepare_and_accept_unrelated_increment()`, `assert_every_target_is_inherited_absent()`, and `prepare_final_closure()`.
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

- [ ] **Step 2: Write the final proposal-to-closure integration regression**

In `tests/test_delete_operation_lifecycle.py`, verify the fixture's final path is exactly `test/legacy/characterization.test.ts`. Build a temporary Git repository where the other 26 Delete targets are existing regular files but that characterization path is absent. Configure a Delete-capable setup/envelope v2 program with a predecessor increment, the later 27-path Delete increment, and an unrelated successor. Exercise real production writers and validators:

```python
def test_pipeflow_delete_inventory_replays_proposal_to_closure(self) -> None:
    source_sha256, delete_paths = load_pipeflow_delete_inventory()
    self.assertEqual(len(delete_paths), 27)
    later_created = "test/legacy/characterization.test.ts"
    self.assertEqual(delete_paths[-1], later_created)
    fixture = DeleteLifecycleFixture(delete_paths[:-1], later_created, source_sha256)
    try:
        self.assertFalse(fixture.repository.joinpath(later_created).exists())
        self.assertTrue(
            all(fixture.repository.joinpath(path).is_file() for path in delete_paths[:-1])
        )
        fixture.validate_and_publish_proposal()
        recap = fixture.render_setup_recap()
        self.assertTrue(all(path in recap for path in delete_paths))
        fixture.approve_activate_and_start()
        fixture.prepare_create_and_accept_predecessor()
        fixture.assert_characterization_is_inherited_present()
        fixture.rollover_to_delete_increment()
        fixture.prepare_and_authorize_delete_plan()
        fixture.delete_every_target()
        fixture.review_and_accept_delete_result()
        fixture.rollover_to_unrelated_increment()
        fixture.prepare_and_accept_unrelated_increment()
        fixture.assert_every_target_is_inherited_absent()
        closure = fixture.prepare_final_closure()
        self.assertEqual(
            [item["path"] for item in closure["final_inherited_path_states"] if item["final_state"] == "absent"],
            list(delete_paths),
        )
        self.assertEqual(
            {
                item["requirement_id"]: item["owner"]
                for item in closure["requirement_dispositions"]
            },
            fixture.expected_requirement_owners,
        )
    finally:
        fixture.close()
```

The proposal contains two exact allocations for the characterization path: Create in the predecessor with absent/none/`None`/none facts, and Delete in the later increment with regular-file/none/`100644`/`accepted-predecessor` facts. The other 26 Delete allocations use collision `existing`. Give the predecessor creation requirement, Delete requirement, and unrelated final requirement distinct traceability ownership so the replay proves PLUG-002's earlier-increment closure semantics. The predecessor exact plan must use file-map/baseline/result v2 with an empty Delete section, create the characterization file, reach exact accepted status, and rollover it as inherited-present before the Delete plan is prepared; discovery must return `accepted-stop` at that boundary. The Delete plan then lists all 27 paths in frozen order and its baseline validates the two collision classes separately. The unrelated successor also uses v2 with an empty Delete section, allocates the final closure artifacts, and contributes only an unrelated product result. Closure must reach its intended assertions with the earlier requirements attributed to their actual accepted increments, not fail because they are absent from the final increment's allocation.

Add negatives that pre-create the characterization path before its Create baseline, omit one of the other 26 paths before the Delete baseline, or declare the characterization Delete collision as `existing`; each must fail the production allocation-fact check before the corresponding plan/baseline write. Add `test_external_pipeflow_source_matches_frozen_inventory`, guarded only by `PIPEFLOW_PLAN_PATH`; when supplied, it computes the exact SHA-256, extracts Task 8's Delete bullets, and compares the ordered 27-path tuple with the fixture. The deterministic suite uses the frozen fixture and never requires the external path.

- [ ] **Step 3: Run the final integration regression and verify GREEN**

Tasks 1–6 already own and test every required schema, writer, validator, retry route, and rollover/closure behavior. Task 7 adds one cross-component regression over those completed contracts; it is not a new behavior RED. Run it immediately after writing the fixture and test:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_delete_operation_lifecycle -v
```

Expected: the frozen scenario passes on the unchanged Tasks 1–6 implementation and the optional external-source test is skipped. A failure is an integration defect in Tasks 1–6: repair it in the owning earlier task/commit, rerun that task's focused checks, then rerun this final regression. Do not treat a failing final integration test as a new Task 7 feature implementation.

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

Record authorized/implementing/reviewing state rules, typed absent results, blocked recovery, cumulative tombstones, explicit recreation, and complete-chain closure once at their canonical references; link from the skill and reader docs. Document the canonical Delete protection boundary: lexical/resolved `.git`, Git directory/common directory in normal and linked worktrees, conventional/actual program roots, and manifest-owned control paths are never Delete targets, while exact ordinary product paths remain allowed. Update `references/program-discovery.md` to make its existing prefix-before-generic-rejection rule explicit for both setup/envelope families and to enumerate exact setup-v2 plan preparation/materialization, review, acceptance, immediate/later rollover, and closure retry/recovery routes. State that advanced Move/Rename, Replace, migration groups, automatic staging/finalization, and expanded Preserve remain pending under the broader v4 design.

In the two version-owning design specs, `references/state-authorization.md`, `references/program-discovery.md`, and the live runbook, document `implementation-execution-transition/v2` as the setup-v2 companion to baseline/result v2: list its exact product-result fields, canonical ordered-state digest, family-specific event seed, conditional remediation-digest extension, retry/adoption checks, fresh-discovery route, and cross-family rejection. Preserve the documented v1 `product_delta_sha256` shape and byte contract.

Synchronize `implementing-staged-plans-bootstrap-execution-review-runbook.md` as a current `0.1.3` operational runbook, not historical evidence: retain its 0.1.1/0.1.2 guarantees, add setup-v2's from-first-increment file-map/baseline/result family and empty Delete sections before late Delete, document v2 accepted-stop and divergent-prefix discovery, and require closure to bind the complete accepted path-state chain, real per-requirement owners/evidence/later checks, existing nonfinal handoffs, and final cumulative digest. State explicitly that v2 creates no handoff addendum; the legacy continuity addendum contract remains v1-only. Do not rewrite older dated design plans; they remain historical version-bound records.

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
rtk git add tests/fixtures/delete-operation/pipeflow-task-8-delete-paths.json tests/test_delete_operation_lifecycle.py docs/superpowers/specs/2026-08-22-program-setup-approval-and-refactor-operations-design.md docs/superpowers/specs/2026-08-23-expanded-local-refactor-operations-design.md skills/implementing-staged-plans/SKILL.md skills/implementing-staged-plans/agents/openai.yaml skills/implementing-staged-plans/references/program-authority.md skills/implementing-staged-plans/references/program-discovery.md skills/implementing-staged-plans/references/repository-preparation.md skills/implementing-staged-plans/references/execution-discipline.md skills/implementing-staged-plans/references/review-coordination.md skills/implementing-staged-plans/references/state-authorization.md skills/implementing-staged-plans/references/continuity-closure.md docs/reference.md docs/workflows.md docs/troubleshooting.md implementing-staged-plans-bootstrap-execution-review-runbook.md docs/maintainers.md docs/installation.md .codex-plugin/plugin.json .claude-plugin/plugin.json .claude-plugin/marketplace.json skills/implementing-staged-plans/scripts/validate_package.py tests/test_front_door_contract.py tests/test_distribution_documentation.py tests/test_package_validation.py
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
- After a Delete-capable v2 setup, baseline, execution transition, review, rollover, blocked context, or closure artifact exists, do not downgrade that program to `0.1.2` or rewrite it as v1. Retain a `0.1.3` reader or ship a forward repair that preserves the v2 bytes.
- A failure before product mutation preserves the baseline file and exact partial control-plane prefix; retry may adopt only byte-identical owner-bound artifacts.
- A failure after a planned Delete while status is `implementing` preserves the absence as a valid partial product result. Recovery may block and resume from the exact bound absence; it does not restore automatically.
- A failure after review or diff acceptance must reproduce the same ordered path states and digest. Reappearance, changed content, missing result records, reordered states, or mixed schema families is divergent and stops without cleanup.
- Rollover merges a Delete tombstone only after exact diff acceptance. An unrelated successor cannot erase it; only a later exact Create operation whose baseline agrees with inherited absence can replace it.
- Closure binds the entire accepted chain, per-requirement allocation/owner/evidence/disposition, every later-invalidation check, existing nonfinal handoffs, and final cumulative state. It cannot close when a tombstone disappeared, a deleted file reappeared, an earlier accepted artifact is missing, an earlier-only requirement is falsely assigned to the final increment, a later result invalidates earlier evidence without a resolved disposition, or evidence treats an absent path as a file.
- Recovery bytes are not created by this repair. Source recovery remains a separately authorized manual or Git operation; the plugin never resets, restores, stashes, cleans, or deletes automatically.

## Final Validation Matrix

| Requirement | Primary owner | Required evidence | Failure signal |
| --- | --- | --- | --- |
| Locked implementation baseline | Git preflight | candidate `b5eb689e...` is an ancestor of the clean kickoff HEAD on `repair/delete-operation-support`; every candidate-to-HEAD commit and aggregate path is only this plan; actual kickoff HEAD and plan SHA-256 are recorded | stop before edits |
| Locked real source | scenario fixture/live replay | SHA-256 `a0dfa057...` and exact ordered 27-path Task 8 inventory | source drift; no claim |
| Setup can state Delete truthfully | `program_setup.py` | envelope/setup v2 validates and recap renders path, absent state, disposition, rationale | unsupported or mixed schema |
| Protected targets are mechanically excluded | `build_delete_protection_context(...)`, `validate_delete_target_path(...)` | normal and linked-worktree tests reject lexical/resolved `.git`, Git directory/common directory, conventional/actual program roots, every manifest control path, symlink/case/hard-link aliases, retries, and post-authorization swaps; allowed product controls pass | missing protection metadata, control-path Delete, alias escape, protected read, or substring over-rejection |
| Legacy setup unchanged | `program_setup.py`, `program_authority.py` | v1 golden bytes and cross-family negatives | any v1 byte/result drift |
| Exact plan does not misclassify Delete | `repository_preparation.py` | unversioned heading fails; v2 parses ordered Delete section | Delete absorbed as Modify |
| Late Delete uses one program family | setup/activation/preparation/rollover | `test/legacy/characterization.test.ts` begins absent, is created/accepted by a setup-v2 predecessor with an empty Delete section, becomes inherited-present with collision `accepted-predecessor`, then is deleted with the 26 initially existing targets | pre-created fixture, false collision facts, or mixed v1/v2 rollover/closure |
| Baseline proves a real removable file | `program_activation.py`, `inspect_workspace_path(...)` | component `lstat`, workspace containment, existing regular-file digest; unsafe/user-owned targets rejected | missing/unsafe/overlap issue |
| Ancestor safety is reassessed | `inspect_workspace_path(...)`, operation callers | baseline symlinked ancestor and post-authorization ancestor swap fail before external reads; missing suffix remains valid only for Create, accepted/inherited absence, and already-absent user work | path escape, rejected valid absence, or missing required Delete/Modify/Preserve target |
| Lifecycle path-state semantics | `validate_execution_workspace(...)` | authorized exact; implementing exact-or-absent; reviewing absent; v2 result with null digest and exact-map ordering | accidental loss, fabricated digest, or reordered state |
| Execution transition matches result family | `program_activation.py`, `program_review.py`, `state_authority.py`, `program_discovery.py` | v1 keeps `product_delta_sha256`; v2 uses `implementation-execution-transition/v2` with exact product-result schema/digest and derived event; production writer output survives fresh discovery and exact retry | mixed/dual family, changed seed or digest, invalid adoption, generic discovery route, or v1 byte drift |
| Managed lifecycle writes stay separate | `state_authority.py` | required writes remain only Create/Modify/Preserve and every Delete control-path collision is rejected independently | Delete accepted for a control path |
| Review and remediation bind absence | `program_review.py`, `review_coordination.py` | v2 evidence has exact ordered states/digest and renewed result after repair | stale/missing/mixed result |
| Diff acceptance binds reviewed result | `diff_disposition.py` | v2 binding/command matches fresh review result | prompt or result mismatch |
| Discovery resumes v2 safely | `program_discovery.py` | setup-v2 plan preparation/materialization, review, acceptance, immediate/later rollover, and closure exact prefixes classify before generic state validation; divergent prefixes use their domain recovery routes | v1-only gate, invalid/generic route, wrong resume, or terminal route |
| Blocked recovery freezes path state | `blocked_recovery.py` | v2 context reproduces exact partial/complete states | post-block change or evidence fabrication |
| Rollover preserves ordered tombstones and evidence | `program_rollover.py` | accepted predecessor before Delete; replace-in-place/append merge retains absent state; v2 record binds accepted review evidence/packet, diff decision/approval, and existing handoff | reappearance, omission, reorder, missing/tampered evidence or handoff, invented addendum, or mixed chain |
| Accepted-state prompts preserve typed results | `program_continuation.py` | exact v1/v2 command dispatch and parsing; v2 embeds ordered path states with null absent digest; v1 golden bytes stay exact | cross-family prompt, `str(None)`, or v1 byte drift |
| Recreation is explicit | activation/preparation | later Create owns inherited absent path and baseline agrees | implicit recreation or wrong operation |
| Closure covers the complete chain | `program_closure.py`, `continuity_closure.py` | all accepted results/reviews/diff approvals/handoffs plus real traceability owners, evidence paths, disposition handling, later-invalidation checks, final closure bindings, and cumulative digest | singleton-only, final-owner fabrication, unresolved allocation/disposition, invalidated evidence, invented addendum, or lost tombstone |
| Front door does not over-authorize | skill/references/docs | Delete remains local plan-bound `modify-workspace` only | generic destructive/external claim |
| Operational runbook is current | bootstrap/execution/review runbook | `0.1.3` path states, discovery, and complete-chain closure match canonical owners | live runbook remains at `0.1.2` |
| Package is synchronized | manifests/validator/docs | every owner says `0.1.3`; package validation exits `0` | version or inventory mismatch |
| Full regression | complete suite | one completed exit `0`, exact count recorded | failure, interruption, or partial output |
| External boundary | final status/diff | no push, PR, install, cache sync, pipeFlow edit, or provider action | any unauthorized external mutation |
