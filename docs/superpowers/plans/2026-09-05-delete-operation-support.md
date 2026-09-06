# PLUG-001 Typed Delete Support Implementation Plan

> **For implementers:** Execute task by task with strict RED-GREEN sequencing and preserve all legacy bytes.

**Goal:** Add truthful, fail-closed support for an exact regular-file `Delete` operation from setup through accepted result, successor rollover, and fresh discovery.

**Boundary:** PLUG-001 owns Delete setup, activation, exact-plan parsing, baseline and execution validation, protected-path enforcement, the actual bound-file deletion primitive, typed review/diff acceptance, result-bound approval, cumulative rollover, and retry/recovery discovery. It does not own chain-wide requirement attribution, requirement-specific result evidence, later-increment semantic invalidation, or complete-chain closure.

**PLUG-002 dependency:** Terminal closure is not independently truthful until PLUG-002 adds machine-bound requirement ownership and later-increment invalidation evidence across the accepted chain. The PLUG-001 replay ends after the Delete result is accepted, rolled into a successor, and rediscovered as resumable. Do not add closure fields, requirement-result schemas, path-overlap heuristics, or fabricated ownership to make this plan appear terminal.

**Compatibility:** Existing manifest/status v1 and v2, plus manifest-v3 programs using setup/envelope v1, retain their exact schemas, prompts, ordering, errors, and persisted bytes. PLUG-001 adds a nested v2 family only for manifest-v3 programs selecting setup/envelope v2 from sequence zero.

**Tech stack:** Python 3 standard library, frozen dataclasses, canonical JSON/SHA-256, `unittest`, temporary Git repositories, and existing atomic/no-overwrite/status-last writers.

---

## Implementation Kickoff Gate

Before implementation:

```bash
rtk git branch --show-current
rtk git status --short --branch
rtk git merge-base --is-ancestor b5eb689e780f48b218b807a4691f0994474e4178 HEAD
rtk git diff --name-only b5eb689e780f48b218b807a4691f0994474e4178...HEAD
rtk git diff --check b5eb689e780f48b218b807a4691f0994474e4178...HEAD
rtk shasum -a 256 docs/superpowers/plans/2026-09-05-delete-operation-support.md
```

Proceed only when the branch is `repair/delete-operation-support-narrowed`, the tree is clean, `b5eb689e780f48b218b807a4691f0994474e4178` is an ancestor of `HEAD`, and the aggregate candidate-to-`HEAD` diff contains only this plan. The implementation prompt must supply the final plan SHA-256 externally and the computed digest must match it.

The plan deliberately does not embed its own digest. Do not infer the expected digest from a parent commit, earlier review, or this prose.

## Stable Constraints

- Use `rtk` for every repository command.
- Preserve user-owned staged, unstaged, untracked, and committed work.
- Route by exact schema pairs, never optional-field presence or whether an increment has a non-empty Delete section.
- A Delete-capable program uses its nested v2 family from the first increment; earlier increments have an empty ordered Delete section.
- Delete targets are normalized repository-relative regular files owned by the exact plan. Directories, symlinks, hard links, special files, missing deletion baselines, external paths, protected paths, and pre-existing user work are unsupported.
- Delete means accepted absence with `sha256: null`; never encode it as Modify, Preserve, omission, an empty digest, or a fabricated digest.
- `authorized` requires the exact baseline file. `implementing` permits that file or its bound absence. `reviewing`, acceptance, rollover, and later states require absence.
- Delete remains inside approved local `modify-workspace` authority. It grants no generic destructive-operation, cleanup, migration, Git, publication, deployment, provider, or external-state authority.
- Keep public plan preparation/materialization signatures unchanged.
- Preserve exact-prefix adoption, compare-and-swap, no-overwrite publication, immutable ledgers, and status-last ordering.
- Reuse existing review packets and nonfinal handoffs; do not invent a handoff addendum.
- Add no generic operations framework, Move/Rename, Replace, directory deletion, automatic restore, staging engine, or manifest/status v4.
- Record unrelated observations without enlarging this plan.

## Confirmed PLUG-001 Defects

1. `program_setup.py` permits only Create, Modify, and Preserve.
2. The exact-plan parser can absorb an unversioned `### Delete` section into Modify.
3. Baseline and execution validation require mutable paths to remain present; accepted results require a string digest.
4. `program_activation.py::advance_execution_state(...)` emits only transition v1 with `product_delta_sha256`.
5. Discovery validates generic state before several owned prefixes, misclassifying exact setup-v2 retries.
6. Path-shape and final-`Path` checks do not mechanically exclude normal/linked-worktree Git metadata, program/control paths, or ancestor/final swaps.
7. A path check followed by hashing or unlinking reopens a race; Delete needs one descriptor-relative identity flow through mutation.
8. Product-result-bearing approvals and rollover actions use legacy delta fields; producers and readers need exact versioned families.
9. Rollover writes a review packet, handoff, successor brief, rollover record, and status. No v2 handoff-addendum producer exists.

## File Map

### Create

- `tests/test_delete_operation_lifecycle.py` — production-writer replay through accepted Delete rollover and discovery.

### Modify

- `skills/implementing-staged-plans/scripts/program_setup.py`
- `skills/implementing-staged-plans/scripts/repository_preparation.py`
- `skills/implementing-staged-plans/scripts/program_activation.py`
- `skills/implementing-staged-plans/scripts/execution_discipline.py`
- `skills/implementing-staged-plans/scripts/review_coordination.py`
- `skills/implementing-staged-plans/scripts/program_review.py`
- `skills/implementing-staged-plans/scripts/diff_disposition.py`
- `skills/implementing-staged-plans/scripts/program_continuation.py`
- `skills/implementing-staged-plans/scripts/program_rollover.py`
- `skills/implementing-staged-plans/scripts/program_authority.py`
- `skills/implementing-staged-plans/scripts/program_discovery.py`
- `skills/implementing-staged-plans/scripts/state_authority.py`
- `tests/program_bootstrap_support.py`
- focused tests named per task
- canonical references, docs, and version owners named in Task 5

No PLUG-002 requirement-evidence or closure file is in scope.

---

### Task 1: Add the Delete-Capable Setup Family and Own Sequence-Zero Discovery

**Files:**

- Modify: setup, activation, program-authority, discovery, and state-authority scripts
- Modify: `tests/program_bootstrap_support.py`
- Test: `tests/test_program_setup.py`, `tests/test_program_activation.py`, `tests/test_program_authority.py`, `tests/test_program_discovery.py`, `tests/test_state_authority.py`

**Contract:**

```python
SETUP_SEMANTICS_SCHEMA_V2 = "implementation-program-setup-semantics/v2"
OPERATION_ENVELOPE_SCHEMA_V2 = "implementation-operation-envelope/v2"
SETUP_RECAP_SCHEMA_V2 = "implementation-program-setup-recap/v2"
SETUP_RECAP_CHECKPOINT_SCHEMA_V2 = "implementation-program-setup-recap-checkpoint/v2"
SETUP_DECISION_ADAPTER_SCHEMA_V2 = "setup-approval-decision/v2"
SETUP_ACTIVATION_SCHEMA_V2 = "setup-activation-decision/v2"

SUPPORTED_OPERATIONS_V1 = ("Create", "Modify", "Preserve")
SUPPORTED_OPERATIONS_V2 = ("Create", "Modify", "Delete", "Preserve")
DELETE_CONTENT_DISPOSITIONS = frozenset(
    {"migrated", "obsolete", "intentional-discard"}
)
```

A Delete allocation requires one exact path, `accepted_state == "absent"`, one allowed content disposition, a non-empty rationale, program ownership, and collision `existing` or `accepted-predecessor`. `accepted-predecessor` requires a same-path Create allocation in a strict transitive predecessor; its Delete baseline must still observe a present safe file. Reject Delete-only fields on other operations.

#### Step 1: Write RED tests

Prove setup/envelope v2 accepts well-formed Delete; v1 rejects it with unchanged bytes; mixed families fail before publication; recap/checkpoint/adapter/activation select the exact family; the production writer emits activation v2; and setup-v1/v2 records cannot substitute for one another. Interrupt sequence-zero activation after each record: byte-exact prefixes are retry-ready, while mixed/reordered/changed started prefixes are activation-recovery-required before generic routing.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_setup tests.test_program_activation tests.test_program_authority tests.test_program_discovery tests.test_state_authority -v
```

Expected RED: setup rejects Delete and has no v2 activation family.

#### Step 2: Implement and verify GREEN

Dispatch setup validation, recap, adapter, activation writer, authority readers, and discovery from the exact setup/envelope pair. Run the same command. Do not alter setup-v1 constructors or fixtures.

---

### Task 2: Add Descriptor-Bound Delete, Exact Plan/Baseline/Result, and Transition v2

**Files:**

- Modify: repository-preparation, activation, discovery, and state-authority scripts
- Test: `tests/test_repository_preparation.py`, `tests/test_program_activation.py`, `tests/test_approval_checkpoint.py`, `tests/test_program_discovery.py`, `tests/test_state_authority.py`

**Contracts:**

```python
EXACT_FILE_MAP_SCHEMA_V2 = "implementation-exact-file-map/v2"
EXECUTION_BASELINE_SCHEMA_V2 = "implementation-execution-baseline/v2"
PRODUCT_PATH_STATES_SCHEMA_V2 = "implementation-product-path-states/v2"
EXECUTION_TRANSITION_SCHEMA_V2 = "implementation-execution-transition/v2"

@dataclass(frozen=True)
class WorkspacePathSnapshot:
    path: str
    exists: bool
    sha256: str | None
    mode: str | None
    device: int | None
    inode: int | None
    link_count: int | None

@dataclass(frozen=True)
class DeleteReceipt:
    path: str
    baseline_sha256: str
    device: int
    inode: int
    final_state: str
```

V2 exact maps have ordered Create, Modify, Delete, and Preserve sections. Unversioned Delete fails explicitly. V2 result order is operation-section then exact-map order; v1 keeps lexical ordering and bytes.

#### Step 1: Write RED tests

Test v2 parsing including empty Delete; unversioned Delete rejection; present regular-file baseline; typed absent/null-digest result; authorized/implementing/reviewing/accepted rules; transition-v2 product-result fields without `product_delta_sha256`; family-specific seed/adoption/recovery; and production output through fresh authority/discovery.

Use normal and linked worktrees. Reject lexical `.git`, Git directory/common directory, conventional/actual program roots, manifest control paths, symlinked ancestors/finals, protected identity aliases, hard links, directories, special files, and ancestor/final/content swaps. Allow `.github`, `.gitignore`, and ordinary names containing `git`.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_preparation tests.test_program_activation tests.test_approval_checkpoint tests.test_program_discovery tests.test_state_authority -v
```

Expected RED: no v2 map/baseline/result/transition or protected descriptor path exists.

#### Step 2: Implement one descriptor-relative identity path

From a fresh repository inspection, normalize one relative POSIX path; reject absolute/dot/backslash/Git/control paths; open workspace and ancestors with `O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC` and `dir_fd`; open final with `O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC`; match descriptors to parent-relative no-follow stats and protected identities; require regular type and `st_nlink == 1`; hash the held final descriptor; compare pre/post `fstat`; and revalidate the held chain. Only descriptor-relative `ENOENT` means absence.

No setup-v2 authorization may use `Path.resolve()`, `is_file()`, `read_bytes()`, or a separate check-then-open target.

Actual deletion uses production `delete_bound_regular_file(...)`, never test-side `Path.unlink()`. It receives the exact v2 baseline identity and fresh protection context, repeats the held walk/hash, requires matching device/inode/mode/digest and one link, revalidates the final name immediately before `os.unlink(name, dir_fd=parent_fd)`, then verifies the held inode lost its link, the name is absent, and ancestors are identical. A swap before unlink fails before the syscall. Syscall-boundary divergence never returns an accepted receipt and enters deterministic recovery. The helper runs only for the current authorized setup-v2 exact-plan Delete and grants no authority itself.

If required primitives are unavailable, fail before v2 artifacts or mutation with `descriptor-relative no-follow Delete is unsupported on this platform`. No path fallback; legacy families do not call the primitive.

#### Step 3: Implement exact baseline/result/transition and verify GREEN

Add v2 dataclasses rather than widening v1. Pair only baseline v1 + delta v1 + transition v1, or baseline v2 + path-states v2 + transition v2. Reconstruct the pair at activation, reassessment, retry, authority, and discovery. Run the Step 1 command.

---

### Task 3: Carry Typed Delete Through Review and Exact Diff Approval

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/execution_discipline.py`
- Modify: `skills/implementing-staged-plans/scripts/review_coordination.py`
- Modify: `skills/implementing-staged-plans/scripts/program_review.py`
- Modify: `skills/implementing-staged-plans/scripts/diff_disposition.py`
- Modify: `skills/implementing-staged-plans/scripts/program_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Test: `tests/test_execution_discipline.py`
- Test: `tests/test_review_coordination.py`
- Test: `tests/test_program_review.py`
- Test: `tests/test_diff_disposition.py`
- Test: `tests/test_program_authority.py`
- Test: `tests/test_program_discovery.py`
- Test: `tests/test_state_authority.py`

**Contracts:**

- `implementation-review-evidence/v2`
- `implementation-review-packet/v2`
- `implementation-review-preparation/v2`
- `implementation-review-remediation/v2`
- `implementation-diff-disposition-binding/v2`
- `implementation-diff-disposition-command/v2`
- `implementation-approval/v3` only for setup-v2 result-bearing diff approval

Review evidence v2 binds `{schema_version, sha256, ordered_path_states}` as `product_result`. It contains no requirement-result object; PLUG-002 owns that evidence.

Exact setup-v2 accept-stop approval order:

```python
SETUP_V2_DIFF_APPROVAL_FIELDS = (
    "schema_version", "event_id", "type", "decision", "scope",
    "diff_decision", "checkpoint_id", "base_seed_sha256",
    "submitted_prompt_sha256", "program_id", "program_revision",
    "source_id", "source_sha256", "program_sha256",
    "semantic_requirements_sha256", "increment_id", "brief_sha256",
    "exact_file_plan_sha256", "approval_mode", "workspace",
    "review_evidence_sha256", "review_packet_sha256",
    "verification_sha256", "execution_baseline_sha256",
    "product_result_schema_version", "product_result_sha256",
    "setup_activation_decision_id", "setup_activation_decision_sha256",
    "increment_grant_id", "increment_grant_sha256",
    "source_gate_satisfaction",
)
```

Accept-continue adds only `successor_increment_id` and `successor_authority_projection_sha256`.

#### Step 1: Write RED tests

Drive one absent result through production review/diff writers. Assert exact state through evidence, packet, preparation, command, approval, and status. Reject reappearance/change/reorder/omission, stale remediation, prompt mismatch, malformed/dual records, approval-v2 on setup-v2, and approval-v3 on setup-v1. Approval v3 binds the product-result pair and omits `accepted_product_delta_sha256`. Review/acceptance prefixes classify before generic routing; setup-v1 bytes remain exact. Repeat protected assessment at each entry.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_execution_discipline tests.test_review_coordination tests.test_program_review tests.test_diff_disposition tests.test_program_authority tests.test_program_discovery tests.test_state_authority -v
```

Expected RED: v2 review/diff and result-bound approval do not exist.

#### Step 2: Implement and verify GREEN

Select v2 review/diff only from the validated v2 result. Binding, command, status, approval tuple, and seed carry its schema/digest. Reject cross-family substitution before writes; preserve v1 prompts/bytes. Run the same command.

---

### Task 4: Preserve the Tombstone Through Rollover and Discovery

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/program_continuation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_rollover.py`
- Modify: `skills/implementing-staged-plans/scripts/program_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `tests/program_bootstrap_support.py`
- Create: `tests/test_delete_operation_lifecycle.py`
- Test: `tests/test_program_continuation.py`
- Test: `tests/test_program_rollover.py`
- Test: `tests/test_multi_increment_lifecycle.py`
- Test: `tests/test_program_activation.py`
- Test: `tests/test_program_authority.py`
- Test: `tests/test_program_discovery.py`
- Test: `tests/test_state_authority.py`

**Contracts:**

- `implementation-accepted-state-continuation-binding/v2`
- `implementation-successor-authority-projection/v2`
- `implementation-action-authorization/v3` only for setup-v2 result-bearing rollover
- `implementation-increment-rollover/v2`
- `implementation-increment-rollover-binding/v2`
- `implementation-inherited-workspace/v2`

Exact setup-v2 rollover action order:

```python
SETUP_V2_ROLLOVER_ACTION_FIELDS = (
    "schema_version", "authorization_id", "decision", "actions", "scope",
    "constraints", "excluded", "program_id", "program_revision",
    "source_id", "source_sha256", "program_sha256",
    "semantic_requirements_sha256", "current_increment_id",
    "successor_increment_id", "continuation_domain",
    "continuation_checkpoint_id", "accepted_status_sha256",
    "accepted_status_sequence", "product_result_schema_version",
    "product_result_sha256", "workspace", "submitted_prompt_sha256",
    "setup_activation_decision_id", "setup_activation_decision_sha256",
    "increment_grant_id", "increment_grant_sha256",
    "source_gate_satisfaction",
)
```

#### Step 1: Write RED rollover and application-path tests

Prove immediate/later continuation retains v2 diff binding and embeds the exact result; cumulative states replace owned paths in place and append in result order; tombstones survive unrelated successors; only explicit Create from inherited absence recreates; rollover v2 copies review evidence/packet, full diff binding, unique approval-v3 binding, existing handoff, result pair, and cumulative digest; no addendum exists; action v3 uses the exact tuple and omits `accepted_product_delta_sha256`; malformed/stale/cross-family prefixes recover before later writes; and setup-v1 bytes remain exact.

Add one replay using production writers: setup-v2 publication and activation, authorized Delete plan, `delete_bound_regular_file("legacy.ts")`, production review and accept-continue, completed rollover, exact inherited absent state, fresh authority, and discovery `resume`. The fixture never directly unlinks or hand-writes records. Negative variants cover hard links, symlinks, ancestor/final swaps, protected paths, changed content, and reappearance.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_continuation tests.test_program_rollover tests.test_multi_increment_lifecycle tests.test_program_activation tests.test_program_authority tests.test_program_discovery tests.test_state_authority tests.test_delete_operation_lifecycle -v
```

Expected RED: accepted absence cannot survive current continuation/rollover.

#### Step 2: Implement and verify GREEN

Load accepted results only from exact review/diff/approval-v3 state. Carry the result pair through continuation, projection, action-v3, grant, rollover, inherited workspace, and status. Merge without sorting: replace owned paths in place, append new paths, reject duplicates. Freshly validate present digests and absent tombstones. Validate existing handoff and copied evidence on every completed-chain read. Classify exact prefixes before full authority and generic routing.

Do not add requirement ownership or closure. Run the Step 1 command.

---

### Task 5: Synchronize PLUG-001 Documentation and Package Version

**Files:**

- Modify: `skills/implementing-staged-plans/SKILL.md`, `skills/implementing-staged-plans/agents/openai.yaml`
- Modify: `skills/implementing-staged-plans/references/repository-preparation.md`
- Modify: `skills/implementing-staged-plans/references/execution-discipline.md`
- Modify: `skills/implementing-staged-plans/references/review-coordination.md`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `skills/implementing-staged-plans/references/program-authority.md`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Modify: `docs/reference.md`, `docs/workflows.md`, `docs/troubleshooting.md`
- Modify: `implementing-staged-plans-bootstrap-execution-review-runbook.md`
- Modify: `docs/installation.md`, `docs/maintainers.md`
- Modify: `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Test: `tests/test_front_door_contract.py`, `tests/test_distribution_documentation.py`, `tests/test_package_validation.py`

Set existing version owners to `0.1.3` without changing plugin identity or manifest field sets.

Document once at canonical owners: v1 versus v2 operations; descriptor-bound mutation and local authority limit; exact transition/review/diff/continuation/rollover families; approval-v3/action-v3 result bindings; Git/program/control protection and unsupported platforms; absent results, recovery stops, tombstones, explicit recreation; reuse of existing handoff; and PLUG-002 requirement-evidence/closure dependency.

#### Step 1: Update expectations and observe RED

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_front_door_contract tests.test_distribution_documentation tests.test_package_validation -v
```

#### Step 2: Synchronize and verify GREEN

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_front_door_contract tests.test_distribution_documentation tests.test_package_validation -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

---

## Final Focused Verification and Claim Gate

Run once on the unchanged candidate:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_setup tests.test_repository_preparation tests.test_program_activation tests.test_approval_checkpoint tests.test_execution_discipline tests.test_review_coordination tests.test_program_review tests.test_diff_disposition tests.test_program_continuation tests.test_program_rollover tests.test_multi_increment_lifecycle tests.test_program_authority tests.test_program_discovery tests.test_state_authority tests.test_delete_operation_lifecycle tests.test_front_door_contract tests.test_distribution_documentation tests.test_package_validation -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk git diff --check
```

Record exact counts, skips, and platform limitations. Interrupted or partial output is not a pass. Do not run the unrelated full suite.

Limit completion claims to exact regular-file Delete under setup/envelope v2; descriptor-bound local mutation; typed absence through review, acceptance, rollover, and discovery; exact result-bound records; and focused legacy compatibility.

Do not claim PLUG-002 requirement ownership, semantic invalidation, terminal closure, Move/Rename, Replace, directory deletion, automatic rollback, external migration, deployment, or untested-platform support.

## Failure and Recovery

- Before product mutation, adopt only byte-identical prefixes; divergence stops without cleanup.
- Failure before bound unlink leaves the product file unchanged.
- Unlink-boundary divergence never yields an accepted receipt; preserve the control prefix and require recovery inspection.
- Successful Delete absence is a valid implementing partial result; no automatic restore occurs.
- Review, approval, and rollover reproduce the ordered absent state. Reappearance, omission, reorder, mixed schemas, or changed evidence stops.
- Rollover preserves the tombstone until a later exact Create owns the path from inherited absence.
- PLUG-001 does not close the program; PLUG-002 must add requirement-specific accepted-chain evidence first.

## Validation Matrix

| Requirement | Owner | Required evidence | Failure signal |
| --- | --- | --- | --- |
| Stable kickoff | Git preflight | branch, clean tree, candidate ancestry, plan-only aggregate scope, external final digest | stop |
| Setup truth | setup | exact setup/envelope v2 and Delete facts | mixed/unsupported schema |
| Discovery ownership | discovery | exact prefix retry/recovery before generic routing | misclassification |
| Protected identity | repository preparation | normal/linked Git, program/control, link/swap coverage | protected access |
| Actual Delete | bound delete helper | held identity/digest, dirfd unlink, absent postcondition | recovery-required |
| Plan/result truth | activation | ordered map/baseline and absent/null result | fabricated state |
| Transition | activation/authority | exact transition-v2 pair and seed | malformed family |
| Review/acceptance | review/diff | exact v2 evidence and approval-v3 | stale/legacy binding |
| Rollover | continuation/rollover | action-v3, existing evidence/handoff, tombstone | addendum/stale state |
| Application path | lifecycle regression | production setup through rollover and discovery resume | hand-written state |
| Legacy compatibility | focused controls | unchanged v1 bytes and routes | drift |
| PLUG-002 boundary | docs/tests | no requirement-result or terminal closure claim | false terminal claim |
| Package | existing owners | `0.1.3`, focused tests, validator zero | mismatch |
