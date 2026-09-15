# PLUG-001 Typed Delete Support Implementation Plan

> **For implementers:** Execute task by task with strict RED-GREEN sequencing and preserve all legacy bytes.

**Goal:** Add truthful, fail-closed support for an exact regular-file `Delete` operation from setup through accepted result, successor rollover, and fresh discovery.

**Boundary:** PLUG-001 owns Delete setup, activation, exact-plan parsing, baseline and execution validation, protected-path enforcement, the no-data-loss bound-file quarantine transition that makes the product path absent, typed review/diff acceptance, result-bound approval, cumulative rollover, and retry/recovery discovery. It does not own chain-wide requirement attribution, requirement-specific result evidence, later-increment semantic invalidation, quarantine disposal, or complete-chain closure.

**PLUG-002 dependency:** Terminal closure is not independently truthful until PLUG-002 adds machine-bound requirement ownership and later-increment invalidation evidence across the accepted chain, then authorizes the final disposition of retained quarantine bytes. The PLUG-001 replay ends after the Delete result is accepted, rolled into a successor, and rediscovered as resumable with quarantine intact. Do not add closure fields, requirement-result schemas, path-overlap heuristics, quarantine disposal, or fabricated ownership to make this plan appear terminal.

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
- Delete means accepted absence of the exact product path with `sha256: null`, bound to a manifest-owned quarantine receipt that preserves the removed bytes; it is not a secure-erasure claim. Never encode it as Modify, Preserve, omission, an empty digest, or a fabricated digest.
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
7. A final identity check followed by `os.unlink(name, dir_fd=parent_fd)` is still name-bound. A concurrent rename-and-replacement can make it irreversibly unlink an unvalidated replacement, and post-unlink checks detect the loss too late. PLUG-001 must instead atomically rename into a same-filesystem manifest-owned quarantine, validate the moved identity, and never unlink user bytes.
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
DELETE_QUARANTINE_RECEIPT_SCHEMA_V1 = "implementation-delete-quarantine-receipt/v1"

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
class DeleteQuarantineReceipt:
    schema_version: str
    program_id: str
    program_revision: int
    increment_id: str
    path: str
    baseline_sha256: str
    device: int
    inode: int
    quarantine_path: str
    quarantine_sha256: str
    final_state: str
```

V2 exact maps have ordered Create, Modify, Delete, and Preserve sections. Unversioned Delete fails explicitly. V2 result order is operation-section then exact-map order; v1 keeps lexical ordering and bytes.

#### Step 1: Write RED tests

Test v2 parsing including empty Delete; unversioned Delete rejection; present regular-file baseline; manifest-owned quarantine allocation; typed absent/null-digest result with its exact quarantine-receipt binding; authorized/implementing/reviewing/accepted rules; transition-v2 product-result fields without `product_delta_sha256`; family-specific seed/adoption/recovery; and production output through fresh authority/discovery.

Use normal and linked worktrees. Reject lexical `.git`, Git directory/common directory, conventional/actual program roots, manifest control paths, symlinked ancestors/finals, protected identity aliases, hard links, directories, special files, and ancestor/final/content swaps. Require the quarantine root and receipt to be manifest-owned protected control paths, and reject caller-selected or symlinked quarantine locations. Allow `.github`, `.gitignore`, and ordinary names containing `git`.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_preparation tests.test_program_activation tests.test_approval_checkpoint tests.test_program_discovery tests.test_state_authority -v
```

Expected RED: no v2 map/baseline/result/transition or protected descriptor path exists.

#### Step 2: Implement one descriptor-relative identity path

From a fresh repository inspection, normalize one relative POSIX path; reject absolute/dot/backslash/Git/control paths; open workspace and ancestors with `O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC` and `dir_fd`; open final with `O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC`; match descriptors to parent-relative no-follow stats and protected identities; require regular type and `st_nlink == 1`; hash the held final descriptor; compare pre/post `fstat`; and revalidate the held chain. Only descriptor-relative `ENOENT` means absence.

No setup-v2 authorization may use `Path.resolve()`, `is_file()`, `read_bytes()`, or a separate check-then-open target.

The product-path transition uses production `quarantine_bound_regular_file(...)`, never test-side `Path.unlink()` and never `os.unlink()` on product or quarantine bytes. During plan materialization, allocate a deterministic per-target quarantine entry and receipt beneath the current increment's manifest-owned storage. The quarantine directory is created as a private regular directory, is included in required future lifecycle writes, and is added to the protection context so it can never be a product Delete target. The entry name derives from the canonical program/revision/increment/path/baseline binding; callers cannot choose it.

At mutation time, open the quarantine directory with the same descriptor-relative no-follow rules, require its recorded owner/mode/identity, and compare its `st_dev` with the held product parent and target before changing either namespace. A mismatch, unavailable atomic rename, or `EXDEV` is a pre-mutation fail-closed stop. Require the deterministic quarantine entry and receipt to be absent, repeat the held target walk/hash, and require matching device/inode/mode/digest plus `st_nlink == 1`. Then call one same-filesystem `os.rename(source_name, quarantine_name, src_dir_fd=source_parent_fd, dst_dir_fd=quarantine_fd)`. This operation may move a raced replacement, but it cannot destroy its bytes.

After rename, open the quarantine entry through the held quarantine descriptor and require its device/inode/mode/digest to equal the already-open validated target. Revalidate every held ancestor, require the source name to be absent, and require no replacement to have appeared. Only then persist canonical `DeleteQuarantineReceipt` bytes with no-overwrite/status-last semantics and return success. The v2 product result contains ordered `delete_quarantine_bindings` entries `{path, receipt_path, receipt_sha256}` alongside its ordered path states; its canonical digest therefore binds both the tombstone and preserved bytes. Review, approval, continuation, rollover, authority, and discovery must reproduce that binding.

Recovery classifies the existing authorized action as the immutable intent. Source exact + empty quarantine means retry-ready; source absent + exact quarantined identity + missing receipt means receipt-adoption-ready; source absent + exact quarantine + exact receipt means resume. A pre-rename replacement moved into quarantine, a post-rename replacement at the source name, both names present, wrong quarantine bytes/identity, unexpected receipt, or missing source and quarantine is recovery-required. Never delete, overwrite, or automatically restore either name during classification. Report the exact source/quarantine identities so separately authorized recovery can preserve both byte sequences.

If required descriptor or same-filesystem atomic-rename primitives are unavailable, fail before mutation with `descriptor-relative no-follow Delete quarantine is unsupported on this platform`. No copy fallback, cross-device move, or path fallback is allowed; legacy families do not allocate or inspect quarantine.

#### Step 3: Implement exact baseline/result/transition and verify GREEN

Add v2 dataclasses rather than widening v1. The product-path-states v2 digest covers both `ordered_path_states` and ordered `delete_quarantine_bindings`; every absent Delete state has exactly one matching canonical receipt, while non-Delete states have none. Pair only baseline v1 + delta v1 + transition v1, or baseline v2 + path-states-plus-quarantine v2 + transition v2. Reconstruct the pair at activation, reassessment, retry, authority, and discovery. Run the Step 1 command.

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

Review evidence v2 binds `{schema_version, sha256, ordered_path_states, delete_quarantine_bindings}` as `product_result`. It reopens and verifies every receipt and quarantined identity before accepting absence. It contains no requirement-result object; PLUG-002 owns that evidence.

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

Drive one quarantined absent result through production review/diff writers. Assert the exact state and receipt binding through evidence, packet, preparation, command, approval, and status. Reject reappearance, changed/reordered/omitted states or receipts, missing/wrong quarantine bytes, stale remediation, prompt mismatch, malformed/dual records, approval-v2 on setup-v2, and approval-v3 on setup-v1. Approval v3 binds the complete product-result digest and omits `accepted_product_delta_sha256`. Review/acceptance prefixes classify before generic routing; setup-v1 bytes remain exact. Repeat protected source/quarantine assessment at each entry.

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

Prove immediate/later continuation retains v2 diff binding and embeds the exact result plus quarantine-receipt bindings; cumulative states replace owned paths in place and append in result order; tombstones and their quarantine receipts survive unrelated successors; only explicit Create from inherited absence recreates the product path without consuming or deleting quarantined bytes; rollover v2 copies review evidence/packet, full diff binding, unique approval-v3 binding, existing handoff, result pair, quarantine bindings, and cumulative digest; no addendum exists; action v3 uses the exact tuple and omits `accepted_product_delta_sha256`; malformed/stale/cross-family prefixes recover before later writes; and setup-v1 bytes remain exact.

Add one replay using production writers: setup-v2 publication and activation, authorized Delete plan, `quarantine_bound_regular_file("legacy.ts")`, production review and accept-continue, completed rollover, exact inherited absent state with its receipt binding, fresh authority, and discovery `resume`. Assert the source path is absent, the manifest-owned quarantine entry retains the exact original bytes, and no unlink call occurs. The fixture never directly renames, unlinks, or hand-writes records. Negative variants cover normal and linked worktrees, cross-device preflight, caller-selected/symlinked quarantine, hard links, source or quarantine swaps before rename, source replacement after rename, changed content, crash-before-receipt adoption, and divergent recovery without data loss.

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_continuation tests.test_program_rollover tests.test_multi_increment_lifecycle tests.test_program_activation tests.test_program_authority tests.test_program_discovery tests.test_state_authority tests.test_delete_operation_lifecycle -v
```

Expected RED: accepted absence cannot survive current continuation/rollover.

#### Step 2: Implement and verify GREEN

Load accepted results only from exact review/diff/approval-v3 state. Carry the result pair and ordered quarantine bindings through continuation, projection, action-v3, grant, rollover, inherited workspace, and status. Merge without sorting: replace owned paths in place, append new paths, reject duplicates. Freshly validate present digests; for each absent tombstone, require source absence plus its exact protected quarantine receipt and bytes. Validate existing handoff and copied evidence on every completed-chain read. Classify exact source/quarantine/receipt and transaction prefixes before full authority and generic routing.

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

Document once at canonical owners: v1 versus v2 operations; same-filesystem descriptor-bound quarantine and local authority limit; exact transition/review/diff/continuation/rollover families; approval-v3/action-v3 result bindings; Git/program/control/quarantine protection and unsupported or cross-device stops; absent results bound to retained quarantine bytes, deterministic recovery, tombstones, and explicit recreation; reuse of existing handoff; no secure-erasure claim; and PLUG-002 requirement-evidence/quarantine-disposal/closure dependency.

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

Limit completion claims to exact regular-file product-path removal under setup/envelope v2; no-data-loss same-filesystem quarantine; typed absence bound to retained bytes through review, acceptance, rollover, and discovery; exact result-bound records; and focused legacy compatibility.

Do not claim secure erasure, quarantine disposal, PLUG-002 requirement ownership, semantic invalidation, terminal closure, Move/Rename, Replace, directory deletion, automatic rollback, external migration, deployment, or untested-platform support.

## Failure and Recovery

- Before product mutation, adopt only byte-identical prefixes; divergence stops without cleanup.
- A cross-device or capability failure stops before rename and leaves the product file unchanged.
- A pre-rename replacement can be moved only into the protected deterministic quarantine slot; identity mismatch stops, preserves its bytes, and yields no receipt.
- After a matching rename, source replacement, quarantine change, or receipt interruption yields recovery-required or receipt-adoption-ready without unlinking, overwriting, or restoring either name.
- Successful product-path absence is a valid implementing partial result only with the exact quarantine receipt and retained bytes.
- Review, approval, and rollover reproduce the ordered absent state and quarantine binding. Reappearance, omission, reorder, mixed schemas, changed receipt, or changed quarantine bytes stops.
- Rollover preserves the tombstone and retained quarantine binding until a later exact Create owns the product path from inherited absence; recreation does not dispose of the quarantine.
- PLUG-001 does not dispose of quarantine or close the program; PLUG-002 must add requirement-specific accepted-chain evidence and terminal disposition first.

## Validation Matrix

| Requirement | Owner | Required evidence | Failure signal |
| --- | --- | --- | --- |
| Stable kickoff | Git preflight | branch, clean tree, candidate ancestry, plan-only aggregate scope, external final digest | stop |
| Setup truth | setup | exact setup/envelope v2 and Delete facts | mixed/unsupported schema |
| Discovery ownership | discovery | exact prefix retry/recovery before generic routing | misclassification |
| Protected identity | repository preparation | normal/linked Git, program/control/quarantine, link/swap coverage | protected access |
| Actual Delete | bound quarantine helper | held identity/digest, same-device atomic rename, exact receipt, absent source, retained bytes, zero unlink calls | pre-mutation stop or recovery-required |
| Plan/result truth | activation | ordered map/baseline and absent/null result | fabricated state |
| Transition | activation/authority | exact transition-v2 pair and seed | malformed family |
| Review/acceptance | review/diff | exact v2 evidence binds tombstone and quarantine receipt; approval-v3 binds its digest | stale/legacy/quarantine mismatch |
| Rollover | continuation/rollover | action-v3, existing evidence/handoff, tombstone and retained quarantine binding | addendum/stale state |
| Application path | lifecycle regression | production setup through rollover and discovery resume | hand-written state |
| Legacy compatibility | focused controls | unchanged v1 bytes and routes | drift |
| PLUG-002 boundary | docs/tests | no requirement-result or terminal closure claim | false terminal claim |
| Package | existing owners | `0.1.3`, focused tests, validator zero | mismatch |
