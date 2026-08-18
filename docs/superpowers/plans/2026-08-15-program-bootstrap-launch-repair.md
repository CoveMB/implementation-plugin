# Program Genesis and First-Increment Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan sequentially, task by task. For every behavioral slice, use `superpowers:test-driven-development`; use `superpowers:systematic-debugging` for any unexpected failure; use `superpowers:verification-before-completion` before a completion claim; and use `superpowers:requesting-code-review` only at the single final review gate defined below. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release version `0.1.1` with a safe, causal path from one explicit program-creation request through proposal publication, exact launch, first-increment preparation, a real reviewed product delta, explicit `accept-stop`, and new-model closure, without successor rollover or blocked recovery.

**Architecture:** A manifest-last, owner-bound publisher creates an immutable new-program control plane with empty future ledgers and manifest-owned increment and closure storage. Exact direct-user prompts activate the first increment and later accept or close it; every transaction derives all bytes before its first write, creates or appends records without overwrite, and replaces status last. A status-current increment grant, execution baseline, transition-specific managed-write derivation, typed review preparation, and product-delta validation separate program authority from user-owned workspace state. Unsafe legacy rollover, new-model generic diff acceptance, and direct blocked transitions are quarantined at persistence sinks until Plan B supplies their complete prompt-bound transactions.

**Tech Stack:** Python 3 standard library, frozen dataclasses, canonical JSON and JSON Lines, Markdown control artifacts, Git porcelain-v2 inspection, `unittest`, subprocess fixtures, Codex skill metadata, and plugin manifests.

**Spec:** `docs/superpowers/specs/2026-08-15-staged-plan-repair-split-design.md`

## Global Constraints

- Work only in `/Users/CoveMB/Code/CoveMB/implementation-plugin` and freshly verify branch, HEAD, and the complete dirty inventory before the first source edit.
- Treat this plan as version `0.1.1`'s sole owner. Plan B, `docs/superpowers/plans/2026-08-14-continuation-hardening.md`, exclusively owns version `0.1.2`.
- Preserve every staged, unstaged, untracked, committed, generated, and accepted user-owned byte. Never reset, clean, restore, stash, amend, overwrite, or absorb unrelated work.
- Use `rtk` for every repository command. Do not fetch unless remote freshness becomes material to a verified requirement.
- Do not edit `implementation-programs/ISP-001/**`, the installed plugin cache, historical evaluator outputs, or Plan B while executing this plan.
- Do not install, publish, deploy, push, open a pull request, access a provider, run a live evaluator, change permissions, or perform destructive or external work.
- Commits are outside routine task execution. If the user separately grants local-commit authority, use the logical boundaries reported at the end; otherwise do not stage or commit.
- New program creation supports only `approval:standard`, `approval:pre-approve`, and `approval:full-increment`; default to `approval:full-increment`. Reject `approval:full-diff` and `approval:full` before every new-program write with `unsupported-new-program-approval-mode`.
- Continue to read accepted legacy `approval:full-diff` and `approval:full` records for their validated current-increment behavior. At every legacy successor boundary, stop before writes with `legacy-rollover-upgrade-required`.
- Preserve accepted v1/v2 manifest, status, workspace, approval, authorization, traceability, review, and closure readers. Do not silently migrate accepted bytes.
- The manifest is immutable after publication. Status is the sole mutable lifecycle owner and separates immutable `activation_binding` from replaceable `current_increment_authority_binding`.
- Listing a managed path allocates ownership; it never grants write authority. Every sink must rederive its exact transition-specific file map and revalidate the live action grant immediately before persistence.
- Every task produces one coherent, independently testable deliverable. End each task with the listed focused checks and focused self-review; do not ask the user for routine task approval.
- Use an alternative verification record only for non-behavioral metadata or documentation changes where a behavioral test would be artificial. Record the exact command, zero exit, relevant inputs, observed evidence, and limitation.
- Run package validation and the full deterministic suite exactly once on the final unchanged `0.1.1` release candidate. After that, obtain exactly one bounded independent material review from a reviewer who did not implement the candidate.
- Reviewer output is evidence, not repair or action authority. Validate every finding. Repair only an evidence-supported material defect within this plan, rerun invalidated checks, and request one focused follow-up tied to that repaired defect. Do not repeat review of an unchanged candidate.
- Stop for a material contradiction, changed requirement, unexpected user-owned overlap, unrepairable required-validator failure, scope expansion, new compatibility decision, absent commit authority when a commit is requested, or any destructive, installation, publication, provider, or external action.

## Version and Behavioral Ownership

Plan A owns:

- new-program proposal authority, immutable schema, manifest-last publication, and publication-prefix recovery;
- lifecycle-aware discovery through first-increment acceptance and closure, including explicit future-route stops;
- the shared exact prompt envelope and launch activation;
- transition-specific managed-write resolution and future lifecycle-write allocation;
- exact-plan preparation/materialization for all three supported new-program approval modes;
- execution-baseline and exact-plan product-delta enforcement;
- typed review preparation and `reviewing -> verified -> awaiting-diff-approval` persistence;
- the canonical diff-disposition base builder and exact `accept-stop` transaction;
- immutable closure storage, closure preparation, exact closure approval, and closed status for any new-model final increment, including successors later created by Plan B;
- deferred-operation quarantine and unsupported live-mutation guards;
- the `0.1.1` compatibility fixture and package-byte comparison.

Plan A does not implement or own:

- `accept-continue`, later continuation after `accept-stop`, successor grants, rollover records, successor status, or successor materialization;
- production blocked entry, block-resolution prompts, resolution records, or blocked resume;
- the causal two-increment regression or the optional live continuation replay;
- revision, supersession, cancellation, installation, commit, publication, or external-action execution.

## Immutable Control Plane and Transaction Rules

Every new manifest owns regular non-symlink paths for approvals, action authorizations, increment grants, rollovers, block resolutions, and status. It also owns these immutable descriptors:

```json
{
  "schema_version": "implementation-increment-storage/v1",
  "root": "increments",
  "brief_filename": "brief.md",
  "exact_file_plan_filename": "exact-file-plan.md",
  "execution_baseline_filename": "execution-baseline.json",
  "review_evidence_filename": "review-evidence.json",
  "review_packet_filename": "review-packet.md",
  "handoff_filename": "handoff.md"
}
```

```json
{
  "schema_version": "implementation-closure-storage/v1",
  "root": "closure",
  "reconciliation_filename": "reconciliation.json",
  "packet_filename": "closure-packet.md"
}
```

The rollovers and block-resolutions ledgers begin empty. Plan A allocates them and validates their ownership but never writes a rollover or block-resolution record. `resolve_program_closure_paths(program_root)` validates the closure descriptor, containment, filesystem kind, and symlink boundary. Legacy manifests continue resolving accepted `closure_reconciliation` and `closure_packet` roles through the compatibility branch.

All identifiers are derived in topological order from immutable input seeds. No seed contains the identifier being derived, final record bytes, record digests, status digests produced later in the transaction, or a prompt digest produced after rendering. Every mutating transaction:

1. loads persisted authority and a fresh repository observation;
2. builds and validates every canonical candidate byte before its first write;
3. verifies exact-file allocation and separate action authority;
4. creates with `O_EXCL`, appends/adopts exact JSON Lines records, or adopts byte-identical existing files only;
5. persists status last with expected digest and sequence compare-and-swap;
6. returns receipts for every completed prefix;
7. preserves divergent or unsafe bytes and returns a typed recovery-required stop.

## File Structure

### Create

- `skills/implementing-staged-plans/scripts/task_prompt.py` — shared explicit-skill envelope, fenced canonical command rendering, and exact transport normalization.
- `skills/implementing-staged-plans/scripts/program_bootstrap.py` — proposal request validation, staging, owner receipt, manifest-last publication, and recovery.
- `skills/implementing-staged-plans/scripts/program_launch.py` — launch record, prompt construction, and submitted-prompt validation.
- `skills/implementing-staged-plans/scripts/program_activation.py` — activation plus exact-plan preparation/materialization transactions.
- `skills/implementing-staged-plans/scripts/program_review.py` — typed review preparation and verified/diff-gate status transaction.
- `skills/implementing-staged-plans/scripts/diff_disposition.py` — canonical diff-disposition base builder and `accept-stop` prompt/persistence.
- `skills/implementing-staged-plans/scripts/program_closure.py` — new-model closure preparation and prompt-bound closure persistence.
- `tests/program_bootstrap_support.py` — reusable deterministic fixture; it may invoke production surfaces but may not manufacture authority records.
- `tests/test_task_prompt.py`
- `tests/test_program_bootstrap.py`
- `tests/test_program_launch.py`
- `tests/test_program_activation.py`
- `tests/test_program_review.py`
- `tests/test_diff_disposition.py`
- `tests/test_program_closure.py`
- `tests/test_program_bootstrap_lifecycle.py`
- `tests/fixtures/program-bootstrap/portable-notes/source-plan.md`
- `tests/fixtures/program-bootstrap/v0.1.1/` — frozen package and first-increment program fixture consumed by Plan B.

### Modify

- `skills/implementing-staged-plans/scripts/program_authority.py`
- `skills/implementing-staged-plans/scripts/program_discovery.py`
- `skills/implementing-staged-plans/scripts/repository_preparation.py`
- `skills/implementing-staged-plans/scripts/state_authority.py`
- `skills/implementing-staged-plans/scripts/approval_checkpoint.py`
- `skills/implementing-staged-plans/scripts/review_coordination.py`
- `skills/implementing-staged-plans/scripts/continuity_closure.py`
- `skills/implementing-staged-plans/scripts/validate_package.py`
- `skills/implementing-staged-plans/SKILL.md`
- `skills/implementing-staged-plans/agents/openai.yaml`
- `skills/implementing-staged-plans/references/program-authority.md`
- `skills/implementing-staged-plans/references/program-discovery.md`
- `skills/implementing-staged-plans/references/approval-checkpoints.md`
- `skills/implementing-staged-plans/references/state-authorization.md`
- `skills/implementing-staged-plans/references/repository-preparation.md`
- `skills/implementing-staged-plans/references/execution-discipline.md`
- `skills/implementing-staged-plans/references/review-coordination.md`
- `skills/implementing-staged-plans/references/continuity-closure.md`
- `docs/workflows.md`, `docs/reference.md`, `docs/troubleshooting.md`, `docs/installation.md`, and `docs/maintainers.md`
- `implementing-staged-plans-consolidated-design-plan-final.md`
- `implementing-staged-plans-bootstrap-execution-review-runbook.md`
- `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`
- focused tests and fixtures named by the tasks below.

### Preserve

- `implementation-programs/ISP-001/**`
- `docs/superpowers/plans/2026-08-14-continuation-hardening.md`
- installed plugin caches and external state
- frozen historical evaluator output

---

### Task 1: Define proposal authority and the immutable new-program schema

**Deliverable:** Proposal-mode authority validation accepts a complete unapproved new-program bundle, approved-mode validation still requires exact approval, and the immutable manifest already owns Plan B's future ledgers and closure storage.

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/program_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/references/program-authority.md`
- Test: `tests/test_program_authority.py`
- Test: `tests/test_state_authority.py`

**Interfaces:**

```python
PROPOSAL_VALIDATION_MODE = "proposal"
APPROVED_VALIDATION_MODE = "approved"
CLOSURE_STORAGE_SCHEMA = "implementation-closure-storage/v1"

def validate_program_authority(
    program_root: Path,
    *,
    validation_mode: str = APPROVED_VALIDATION_MODE,
) -> list[str]: ...

def resolve_program_closure_paths(program_root: Path) -> dict[str, Path]: ...
```

- [ ] **Step 1: Write RED tests**

Add tests that proposal mode accepts empty approval/action/grant/rollover/block-resolution ledgers with `awaiting-program-approval` / `not-started`; approved mode rejects the same bytes; unknown modes fail; both descriptors reject missing keys, absolute paths, separators, escapes, symlinked ancestors, duplicate resolved paths, and non-regular existing entries. Assert new manifests contain no mutable `program_status`, legacy `current_increment`, or closure logical-role duplication.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_authority tests.test_state_authority -v
```

Expected: nonzero failures naming the missing validation mode and closure resolver.

- [ ] **Step 3: Implement the smallest authority split**

Proposal mode validates immutable source, partition, atomic requirements, traceability, program bytes, manifest ownership, empty ledgers, workspace proposal, status sequence `0`, and future reserved approval identifiers without treating them as approval. Approved mode adds the existing exact approval requirement. Keep `--allow-incomplete` as the legacy CLI alias for its current preparation semantics; add no alternate weak path.

- [ ] **Step 4: Run GREEN and focused self-review**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_authority tests.test_state_authority -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_authority.py skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/references/program-authority.md tests/test_program_authority.py tests/test_state_authority.py
```

Confirm proposal validation cannot authorize implementation, every new manifest owns both empty future ledgers, and legacy closure roles remain read-only compatible.

---

### Task 2: Publish a complete proposal atomically and recover every publication prefix

**Deliverable:** One explicit create request publishes an owner-bound proposal without overwrite, makes it discoverable only at `manifest.json`, and adopts every exact crash prefix from a fresh process.

**Files:**

- Create: `skills/implementing-staged-plans/scripts/program_bootstrap.py`
- Create: `tests/program_bootstrap_support.py`
- Create: `tests/test_program_bootstrap.py`
- Create: `tests/fixtures/program-bootstrap/portable-notes/source-plan.md`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`

**Interfaces:**

```python
PROPOSAL_REQUEST_SCHEMA = "implementation-program-proposal-request/v1"
PUBLICATION_OWNER_SCHEMA = "implementation-proposal-publication-owner/v1"

@dataclass(frozen=True)
class ProposalPublication:
    program_root: str
    manifest_sha256: str
    status_sha256: str
    launch_sha256: str
    created_paths: tuple[str, ...]
    adopted_paths: tuple[str, ...]
    recovered: bool

def publish_program_proposal(
    repository_root: Path,
    source_plan: Path,
    candidate_root: Path,
    expected_source_sha256: str,
) -> ProposalPublication: ...
```

- [ ] **Step 1: Write causal RED tests**

Build a real temporary Git repository and canonical candidate. Inject failure after the owner receipt and after each subsequent staged artifact, after final-root reservation, after each owner-inventoried final file, and after `manifest.json` before response. In a new subprocess, retry the same request and require byte-identical adoption and one final manifest. Mutate the newest prefix independently and require preservation plus `proposal-publication-recovery-required`. Cover target collision, source drift, symlink, special file, path escape, unrelated workspace drift, staged/conflicted staging, and multiple controlling programs.

Invoke the real create/publish boundary separately with `approval:full-diff` and `approval:full`. Capture the complete repository snapshot before each call, require `unsupported-new-program-approval-mode`, and assert exact snapshot equality afterward. Patch the private owner-receipt writer in the test to fail if reached, proving mode validation occurs before staging-directory creation, owner-receipt persistence, proposal files, or final-root reservation.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_preparation tests.test_program_bootstrap -v
```

Expected: import failure for `program_bootstrap.py` and missing publisher behavior.

- [ ] **Step 3: Implement manifest-last publication**

Derive `owner_token = sha256(canonical_request_bytes)[:16]`. Stage at the exact direct repository child `.implementation-program-<program-id>-<owner-token>`. Write canonical files and the owner inventory with no overwrite, fsync files and directories, and validate the full candidate in memory. Re-run discovery and repository inspection immediately before reserving the target and immediately before creating `manifest.json`. Reserve the exact absent final root, copy/adopt only inventory-matching regular files, and create `manifest.json` with `O_CREAT | O_EXCL` last. Never replace a target or hide staged, conflicted, sibling, or production drift.

- [ ] **Step 4: Add and test the bounded CLI**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_bootstrap.py publish REPOSITORY --source-plan PLAN --candidate-root CANDIDATE --expected-source-sha256 DIGEST
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_authority tests.test_repository_preparation tests.test_program_bootstrap -v
```

Expected: zero for valid publication/adoption, one for a bounded safety failure, and two for invalid command usage.

- [ ] **Step 5: Focused self-review**

```bash
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_bootstrap.py skills/implementing-staged-plans/scripts/repository_preparation.py tests/program_bootstrap_support.py tests/test_program_bootstrap.py tests/fixtures/program-bootstrap/portable-notes/source-plan.md
```

Confirm every write is under the one invocation-owned staging/final root, the owner receipt contains no self-digest cycle, manifest publication is the discovery commit point, and divergence is never cleaned or overwritten.

---

### Task 3: Discover proposal, activation, execution, acceptance, closure, and partial-prefix states

**Deliverable:** Fresh discovery selects the validation mode from persisted status, recognizes every Plan A transaction prefix before generic rejection, and returns exact no-write stops for deferred Plan B operations.

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Test: `tests/test_program_discovery.py`
- Modify: `tests/program_bootstrap_support.py`

**Interfaces:**

```python
PLAN_A_DISCOVERY_DISPOSITIONS = frozenset({
    "new-program-bootstrap-ready",
    "program-activation-ready",
    "program-activation-retry-ready",
    "plan-preparation-retry-ready",
    "plan-materialization-retry-ready",
    "review-preparation-retry-ready",
    "increment-acceptance-retry-ready",
    "closure-preparation-retry-ready",
    "closure-approval-retry-ready",
    "resume",
    "accepted-stop",
    "closure-approval-ready",
    "terminal-programs",
})
```

- [ ] **Step 1: Write RED classification tests**

Test no manifests, one pristine proposal, each exact activation receipt prefix, active/preparing/authorized/implementing/reviewing/verified/diff-gate states, approval-only acceptance, accepted-stop, closure preparation/approval prefixes, closed and superseded history, multiple controlling candidates, and every malformed/divergent prefix. Direct legacy rollover returns `legacy-rollover-upgrade-required`; new-model successor and blocked prefixes without Plan B's typed context return their exact recovery-required stops without writes.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_discovery -v
```

Expected: the current discovery path rejects unapproved proposals before status-aware routing.

- [ ] **Step 3: Implement inspection before strict final validation**

Validate the manifest path boundary and load minimal status safely, select proposal or approved validation, then inspect exact transaction prefixes from controlling prior status and immutable inputs. Only after a prefix is explained should strict managed-tree and state validation run. Never accept a caller-provided missing-role list or state payload. Return sorted evidence, one next legal action, and `stop_required` truthfully.

- [ ] **Step 4: Run GREEN and focused self-review**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_program_authority tests.test_program_bootstrap tests.test_program_discovery -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/references/program-discovery.md tests/test_program_discovery.py tests/program_bootstrap_support.py
```

Confirm discovery repairs no bytes, terminal history is non-controlling, exact prefixes are reconstructable from persisted authority, and unknown or divergent artifacts still fail closed.

---

### Task 4: Render the shared exact prompt envelope and activate one first increment

**Deliverable:** A copy-ready launch prompt submitted in a fresh task persists program approval, workspace approval, and a distinct first-increment grant, then writes active/preparing status last without a second question.

**Files:**

- Create: `skills/implementing-staged-plans/scripts/task_prompt.py`
- Create: `skills/implementing-staged-plans/scripts/program_launch.py`
- Create: `skills/implementing-staged-plans/scripts/program_activation.py`
- Create: `tests/test_task_prompt.py`
- Create: `tests/test_program_launch.py`
- Create: `tests/test_program_activation.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `tests/program_bootstrap_support.py`

**Interfaces:**

```python
PROMPT_ENVELOPE_SCHEMA = "implementation-exact-prompt-envelope/v1"
LAUNCH_COMMAND_SCHEMA = "implementation-program-launch-command/v1"
INCREMENT_GRANT_SCHEMA = "implementation-increment-grant/v1"

def render_exact_prompt(command: Mapping[str, object]) -> str: ...
def parse_exact_prompt(markdown: str, expected_schema: str) -> dict[str, object]: ...
def render_program_launch_prompt(program_root: Path) -> str: ...
def validate_submitted_program_launch_prompt(
    program_root: Path,
    submitted_prompt: str,
) -> dict[str, object]: ...
def activate_program(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> ActivationReceipt: ...
```

- [ ] **Step 1: Write prompt and transaction RED tests**

Require `$implementing-staged-plans` as the first line, one fenced canonical JSON command, exact transport normalization, no self-digest field, and byte-identical rerendering. Reject altered whitespace inside canonical payloads, appended scope, stale observations, changed proposal bytes, unsupported approval modes, quoted/file/tool-derived content at the front-door contract, and duplicate/conflicting receipt IDs. Inject failures after program approval, workspace approval, first-increment grant, and active/preparing status; rediscover in a fresh process and resubmit the same prompt.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_task_prompt tests.test_program_launch tests.test_program_activation -v
```

Expected: missing modules and no prompt-bound activation transaction.

- [ ] **Step 3: Implement topological IDs and status-last activation**

Derive the launch checkpoint and three record IDs from immutable proposal, semantic, brief, workspace, mode, and conditional-action inputs. Render first, compute the submitted-prompt digest only after direct submission, then serialize records. Persist/adopt program approval, workspace approval, and grant in that order; compare-and-swap status last with immutable `activation_binding` and status-current `current_increment_authority_binding` pointing to the exact grant ID and digest.

- [ ] **Step 4: Expose and test subprocess boundaries**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_launch.py render PROGRAM_ROOT
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_activation.py apply PROGRAM_ROOT --prompt-file PROMPT --repository REPOSITORY --base-commit BASE
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_task_prompt tests.test_program_launch tests.test_program_activation tests.test_program_discovery -v
```

- [ ] **Step 5: Focused self-review**

```bash
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/task_prompt.py skills/implementing-staged-plans/scripts/program_launch.py skills/implementing-staged-plans/scripts/program_activation.py skills/implementing-staged-plans/scripts/state_authority.py tests/test_task_prompt.py tests/test_program_launch.py tests/test_program_activation.py tests/program_bootstrap_support.py
```

Confirm prompt rendering grants nothing, direct submission is one compound decision with separate typed records, unsupported modes fail before writes, and the first-increment grant cannot authorize a successor.

---

### Task 5: Allocate every transition-specific and future lifecycle write

**Deliverable:** Every exact plan declares current and future manifest-owned lifecycle paths under the correct disposition before any transaction writes, including final closure paths or the unique successor navigation allocation.

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `skills/implementing-staged-plans/scripts/approval_checkpoint.py`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `skills/implementing-staged-plans/references/repository-preparation.md`
- Test: `tests/test_state_authority.py`
- Test: `tests/test_repository_preparation.py`
- Test: `tests/test_approval_checkpoint.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ManagedWriteRequirement:
    path: str
    disposition: str

@dataclass(frozen=True)
class ExactFileMap:
    create: tuple[str, ...]
    modify: tuple[str, ...]
    preserve: tuple[str, ...]

def parse_exact_file_map(markdown: str) -> ExactFileMap: ...
def required_future_lifecycle_writes(
    program_root: Path,
    workspace_root: Path,
    increment_id: str,
) -> tuple[ManagedWriteRequirement, ...]: ...
def validate_required_managed_file_map(
    file_map: ExactFileMap,
    required: Sequence[ManagedWriteRequirement],
) -> list[str]: ...
```

- [ ] **Step 1: Write structural and sink-boundary RED tests**

Require approvals, status, action authorizations, increment grants, rollover ledger, and block-resolution ledger under `Modify`. Require execution baseline, review evidence, and review packet under `Create`. For a nonfinal increment with one traceability successor, require current handoff and successor brief under `Create`; for a final increment, require manifest-derived reconciliation and closure packet under `Create` and no invented successor files. Remove or misclassify each path independently and prove plan validation plus the applicable persistence sink fail before any write.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority tests.test_repository_preparation tests.test_approval_checkpoint -v
```

- [ ] **Step 3: Implement one manifest-derived resolver**

Parse exactly one `## File map` with one `### Create`, `### Modify`, and `### Preserve`. Accept only normalized repository-relative POSIX paths and reject duplicates across dispositions. Derive managed paths only from manifest roles, increment storage, closure storage, status, and traceability. Never accept caller-selected managed paths. Preserve `validate_required_managed_writes` as a compatibility wrapper that maps every input to `Modify`.

- [ ] **Step 4: Enforce at every Plan A sink and run GREEN**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority tests.test_repository_preparation tests.test_approval_checkpoint tests.test_program_activation -v
rtk git diff --check
```

- [ ] **Step 5: Focused self-review**

```bash
rtk git diff -- skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/repository_preparation.py skills/implementing-staged-plans/scripts/approval_checkpoint.py skills/implementing-staged-plans/references/state-authorization.md skills/implementing-staged-plans/references/repository-preparation.md tests/test_state_authority.py tests/test_repository_preparation.py tests/test_approval_checkpoint.py
```

Confirm declaration and authority remain separate, successor/final allocation is mutually exclusive, and Plan B can reuse the same derivation without manifest or first-plan rewriting.

---

### Task 6: Prepare and materialize exact plans with an execution baseline

**Deliverable:** All supported modes use one typed exact-plan path; standard mode persists plan then status, renders one prompt, and materializes approval/baseline/action/status, while automatic modes omit only the plan question and persist plan/baseline/action/status.

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/approval_checkpoint.py`
- Modify: `skills/implementing-staged-plans/references/approval-checkpoints.md`
- Modify: `skills/implementing-staged-plans/references/execution-discipline.md`
- Modify: `skills/implementing-staged-plans/references/repository-preparation.md`
- Test: `tests/test_program_activation.py`
- Test: `tests/test_repository_preparation.py`
- Test: `tests/test_state_authority.py`
- Test: `tests/test_front_door_contract.py`

**Interfaces:**

```python
EXECUTION_BASELINE_SCHEMA = "implementation-execution-baseline/v1"
PLAN_PREPARATION_SCHEMA = "implementation-exact-plan-preparation/v1"

def prepare_exact_plan(
    program_root: Path,
    exact_plan_bytes: bytes,
    observation: RepositoryObservation,
) -> ExactPlanPreparationReceipt: ...

def materialize_exact_plan(
    program_root: Path,
    submitted_plan_prompt: str | None,
    observation: RepositoryObservation,
) -> ExecutionMaterializationReceipt: ...

def validate_execution_workspace(
    program_root: Path,
    baseline: ExecutionBaseline,
    inspection: RepositoryInspection,
    *,
    increment_state: str,
) -> ExecutionWorkspaceAssessment: ...
```

- [ ] **Step 1: Write mode, ownership, and prefix RED tests**

For standard mode, inject after exact plan, awaiting-plan status, plan approval, baseline, action authorization, and authorized status. For pre-approve/full-increment, inject after plan, baseline, action, and authorized status. Restart discovery between every prefix and resubmit the same typed operation or prompt. Test `Create` absent, `Modify`/`Preserve` regular and digest-bound, user-owned dirty overlap, inherited paths empty for the first increment, symlink/special file, branch/base/head drift, status-current grant mismatch, plan digest drift, changed baseline, and lost response after status.

Also drive the production transition sink through `authorized -> implementing -> reviewing`. Inject a lost response immediately after each compare-and-swap status replacement, rediscover in a fresh process, and prove the same transition is idempotent. Independently change the product delta before retry and require state validation to preserve status and return the exact workspace issue.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_program_activation tests.test_repository_preparation tests.test_state_authority -v
```

- [ ] **Step 3: Implement the shared typed transaction**

Build and validate exact plan, future lifecycle writes, baseline, and action record before persistence. Standard preparation writes/adopts plan and awaiting-plan status, then exact prompt submission appends/adopts approval, creates/adopts baseline, appends/adopts action authorization, and writes authorized status. Automatic modes create/adopt plan and baseline, append/adopt action authorization, and write authorized status. Never restore the legacy approval/status/action ordering.

Update `references/approval-checkpoints.md` so the v2 standard-mode sequence is exactly approval event → execution baseline → plan-bound action authorization → authorized status last. Its retry contract adopts only byte-identical prefixes in that order. Update `references/execution-discipline.md` so exact plan approval is required only when the persisted mode/status contract requires it: standard mode requires the prompt-bound plan-approval event, while pre-approve/full-increment require the status-current grant, validated exact plan, execution baseline, and exact plan-bound action authorization without inventing a plan-approval event. Add static front-door contract assertions for both reference semantics so the prior status-before-action and unconditional-approval instructions cannot return.

- [ ] **Step 4: Replace post-authorization dirty equality**

Before baseline, compare the normalized launch observation exactly. After baseline, validate product paths by plan disposition and lifecycle state: no product delta at `authorized`; any subset of Create/Modify during `implementing`; complete Create and changed Modify with unchanged Preserve from `reviewing` onward. Always reject new staged/conflicted/unmapped/deleted/unsafe paths and changed preserved user work.

- [ ] **Step 5: Run GREEN and focused self-review**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_program_activation tests.test_repository_preparation tests.test_state_authority tests.test_program_discovery tests.test_front_door_contract -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_activation.py skills/implementing-staged-plans/scripts/repository_preparation.py skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/approval_checkpoint.py skills/implementing-staged-plans/references/approval-checkpoints.md skills/implementing-staged-plans/references/execution-discipline.md tests/test_program_activation.py tests/test_repository_preparation.py tests/test_state_authority.py tests/test_front_door_contract.py
```

Confirm status is last, the baseline distinguishes user work from product history, and all three modes share the same materialization contract except the explicit standard-mode plan approval.

---

### Task 7: Prepare review evidence and reach the real diff gate

**Deliverable:** A production-owned typed transaction derives status-current review evidence and packet, persists them without overwrite, derives review/verification bindings, and reaches `awaiting-diff-approval` with fresh-prefix recovery.

**Files:**

- Create: `skills/implementing-staged-plans/scripts/program_review.py`
- Create: `tests/test_program_review.py`
- Modify: `skills/implementing-staged-plans/scripts/review_coordination.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/references/review-coordination.md`
- Modify: `tests/program_bootstrap_support.py`

**Interfaces:**

```python
REVIEW_PREPARATION_SCHEMA = "implementation-review-preparation/v1"

@dataclass(frozen=True)
class ReviewPreparationCandidate:
    evidence_bytes: bytes
    packet_bytes: bytes
    evidence_sha256: str
    packet_sha256: str
    verified_status_bytes: bytes
    awaiting_diff_status_bytes: bytes

def build_review_preparation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewPreparationCandidate: ...

def persist_review_preparation(
    program_root: Path,
    observation: RepositoryObservation,
) -> ReviewPreparationReceipt: ...
```

- [ ] **Step 1: Write writer-to-fresh-reader RED tests**

Reach `reviewing` through the production transition sink. Build real scope, architecture, and test-evidence reports through existing review coordination, classify risk predicates, reconcile material findings, and construct deterministic packet data. Inject after review evidence, packet, verified status, and awaiting-diff status. Restart discovery and resubmit. Mutate the newest file/status independently and require `review-preparation-recovery-required` with every byte preserved.

- [ ] **Step 2: Add negative binding tests**

Reject caller-selected evidence or packet paths, files not declared by the exact plan, changed execution baseline/product delta, missing raw report, unresolved material finding, stale/nonzero verification, symlink, invalid packet rendering, replayed evidence from another increment, and direct generic `reviewing -> verified` without typed sink context.

- [ ] **Step 3: Run RED**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination tests.test_program_review tests.test_state_authority tests.test_program_discovery -v
```

- [ ] **Step 4: Implement the pure builder and status-last phases**

Resolve evidence/packet only through status-current increment storage and require their `Create` allocations. Validate the full in-memory review bundle before writing. Create/adopt evidence, then packet, then compare-and-swap verified status with both derived bindings; compare-and-swap awaiting-diff status only after fresh validation of verified state and product delta. Discovery reconstructs every prefix from controlling reviewing/verified status and immutable inputs.

- [ ] **Step 5: Run GREEN and focused self-review**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination tests.test_program_review tests.test_state_authority tests.test_program_discovery -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_review.py skills/implementing-staged-plans/scripts/review_coordination.py skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/references/review-coordination.md tests/test_program_review.py tests/program_bootstrap_support.py
```

Confirm persisted evidence is status-current and manifest-derived, packet rendering is byte-deterministic, unresolved material findings block status, and static validation is not claimed as independent review proof.

---

### Task 8: Build canonical diff disposition and persist exact accept-stop

**Deliverable:** The current verified delta always offers `Accept and stop`; direct exact submission appends/adopts diff approval and writes an acyclic accepted status with `decision=accept-stop`, independently of successor availability.

**Files:**

- Create: `skills/implementing-staged-plans/scripts/diff_disposition.py`
- Create: `tests/test_diff_disposition.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `tests/program_bootstrap_support.py`

**Interfaces and schema:**

```python
DIFF_DISPOSITION_BINDING_SCHEMA = "implementation-diff-disposition-binding/v1"

@dataclass(frozen=True)
class DiffAcceptanceCandidate:
    base_seed_sha256: str
    checkpoint_id: str
    approval_event_id: str
    decision: str
    approval_bytes: bytes
    accepted_status_bytes: bytes

def build_diff_acceptance_candidate(
    program_root: Path,
    observation: RepositoryObservation,
) -> DiffAcceptanceCandidate: ...
def render_diff_disposition_prompt(program_root: Path) -> str: ...
def persist_accept_stop(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> DiffDispositionReceipt: ...
```

The accepted status binding contains decision, checkpoint/event IDs, prior status digest/sequence, and review, verification, exact-plan, execution-baseline, and accepted-product-delta digests. It excludes its own digest and submitted-prompt digest. The approval record stores the submitted-prompt digest after rendering and direct submission.

- [ ] **Step 1: Write acceptance RED tests**

Test final increment, no successor, multiple successors, and unsatisfied successor dependencies: every case renders `Accept and stop` and no Plan B choice. Inject failure after approval and after accepted status; fresh discovery returns retry-ready for approval-only, treats accepted-stop as complete, and makes lost-response resubmission idempotent. Prompt tampering, changed review/product evidence, stale status, conflicting approval ID, and direct generic new-model acceptance stop before status writes.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_diff_disposition tests.test_state_authority tests.test_program_discovery -v
```

- [ ] **Step 3: Implement topological construction and the typed sink**

Build the immutable base seed from persisted program/revision, current increment, prior status digest/sequence, decision, review, verification, plan, baseline, and accepted-product-delta digests. Derive checkpoint, then event, then accepted status. Render the prompt from those values. On direct submission, compute prompt digest, serialize approval, append/adopt approval, and replace status last. Generic new-model `awaiting-diff-approval -> accepted` fails unless invoked with the typed sink context; accepted legacy behavior remains readable.

- [ ] **Step 4: Run GREEN and focused self-review**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_diff_disposition tests.test_state_authority tests.test_program_discovery -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/diff_disposition.py skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/references/state-authorization.md tests/test_diff_disposition.py tests/program_bootstrap_support.py
```

Confirm accept-stop never depends on a successor, every derivation is acyclic, approval-only retry is reconstructable, and replay can never initiate continuation.

---

### Task 9: Prepare and approve new-model closure

**Deliverable:** An accepted final increment derives only its manifest-owned closure files, reaches awaiting-closure approval status last, and closes from one exact prompt with complete prefix recovery.

**Files:**

- Create: `skills/implementing-staged-plans/scripts/program_closure.py`
- Create: `tests/test_program_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/continuity_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/references/continuity-closure.md`
- Modify: `tests/program_bootstrap_support.py`

**Interfaces:**

```python
CLOSURE_PREPARATION_SCHEMA = "implementation-closure-preparation/v1"
CLOSURE_COMMAND_SCHEMA = "implementation-program-closure-command/v1"

def prepare_program_closure(
    program_root: Path,
    observation: RepositoryObservation,
) -> ClosurePreparationReceipt: ...
def render_program_closure_prompt(program_root: Path) -> str: ...
def persist_program_closure(
    program_root: Path,
    submitted_prompt: str,
    observation: RepositoryObservation,
) -> ClosureReceipt: ...
```

- [ ] **Step 1: Write closure RED tests**

Use an accepted final first increment whose exact plan allocates both derived closure paths. Inject after reconciliation, packet, awaiting-closure status, closure approval, and closed status. Restart discovery and resubmit the same typed operation or prompt. Exact prefixes adopt and complete once; divergent reconciliation/packet/approval/status bytes are preserved and return typed recovery-required stops. A nonfinal accepted increment, an allocated successor, unallocated closure path, unresolved requirement/finding/amendment/deferral, stale program verification, symlink, or changed accepted delta stops before writes.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_program_closure tests.test_program_discovery -v
```

- [ ] **Step 3: Implement deterministic preparation and exact approval**

Reconcile every atomic requirement exactly once, validate accepted packets/addenda/amendments/deferrals, run fresh program-level commands, and derive canonical reconciliation then packet bytes at `resolve_program_closure_paths`. Create/adopt reconciliation, then packet, then status last. Render exact closure prompt from those digests. Direct submission appends/adopts `program-closure-approval` and writes closed status last. Keep this interface increment-agnostic so a final successor created by Plan B closes without a manifest or closure-contract change. Do not authorize or perform any later action.

- [ ] **Step 4: Run GREEN and focused self-review**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure tests.test_program_closure tests.test_program_discovery tests.test_state_authority -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/program_closure.py skills/implementing-staged-plans/scripts/continuity_closure.py skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/references/continuity-closure.md tests/test_program_closure.py tests/program_bootstrap_support.py
```

Confirm a final increment invents no successor files, closure storage is manifest-derived, accepted nonfinal work cannot close, and closure approval grants no commit or consequential action.

---

### Task 10: Quarantine deferred operations at persistence sinks

**Deliverable:** Every unsafe or out-of-scope mutation fails before writes while accepted legacy read compatibility remains intact.

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/continuity_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Test: `tests/test_state_authority.py`
- Test: `tests/test_continuity_closure.py`
- Test: `tests/test_program_discovery.py`

**Interfaces:**

```python
SUPPORTED_PROGRAM_OPERATIONS = frozenset({"create", "activate", "continue"})
UNSUPPORTED_LIVE_PROGRAM_MUTATIONS = frozenset({"revise", "supersede", "cancel"})

def classify_requested_program_operation(
    discovery: ProgramDiscoveryResult,
    requested_operation: str,
) -> ProgramDiscoveryResult: ...
```

- [ ] **Step 1: Write snapshot RED tests**

Call the legacy caller-authored rollover writer; generic new-model acceptance; direct new-model transitions into or out of blocked; direct supersession; and live revise, supersede, or cancel intent. Snapshot every repository byte before each call. Require exact errors `legacy-rollover-upgrade-required`, typed-diff-sink required, blocked-transaction required, `program-revision-workflow-required`, or `unsupported-program-mutation`, with byte equality afterward. Prove accepted legacy current-increment and historical superseded readers still validate.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority tests.test_continuity_closure tests.test_program_discovery -v
```

- [ ] **Step 3: Add defense-in-depth guards at every write sink**

The old rollover API raises unconditionally before resolving a write target. Generic acceptance and blocked transitions require unforgeable internal typed contexts produced only by their production transactions; Plan A supplies only the diff accept-stop context. No code creates superseded status. Keep the operation classifier pure and route unsupported live intent to a mandatory stop.

- [ ] **Step 4: Run GREEN and focused self-review**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_state_authority tests.test_continuity_closure tests.test_program_discovery -v
rtk git diff --check
rtk git diff -- skills/implementing-staged-plans/scripts/state_authority.py skills/implementing-staged-plans/scripts/continuity_closure.py skills/implementing-staged-plans/scripts/program_discovery.py skills/implementing-staged-plans/references/program-discovery.md skills/implementing-staged-plans/references/state-authorization.md tests/test_state_authority.py tests/test_continuity_closure.py tests/test_program_discovery.py
```

Confirm deferred operations are blocked at sinks rather than prose alone and no guard prevents Plan A's typed accept-stop or closure transactions.

---

### Task 11: Route the repaired first-increment lifecycle through the skill and documentation

**Deliverable:** The front door truthfully creates, activates, prepares, implements, reviews, accepts-stops, and closes Plan A programs while naming successor and blocked operations as deferred to Plan B.

**Files:**

- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/agents/openai.yaml`
- Modify: `skills/implementing-staged-plans/references/program-authority.md`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Modify: `skills/implementing-staged-plans/references/approval-checkpoints.md`
- Modify: `skills/implementing-staged-plans/references/state-authorization.md`
- Modify: `skills/implementing-staged-plans/references/repository-preparation.md`
- Modify: `skills/implementing-staged-plans/references/execution-discipline.md`
- Modify: `skills/implementing-staged-plans/references/review-coordination.md`
- Modify: `skills/implementing-staged-plans/references/continuity-closure.md`
- Modify: `docs/workflows.md`
- Modify: `docs/reference.md`
- Modify: `docs/troubleshooting.md`
- Modify: `implementing-staged-plans-consolidated-design-plan-final.md`
- Modify: `implementing-staged-plans-bootstrap-execution-review-runbook.md`
- Modify: `tests/test_front_door_contract.py`
- Modify: `tests/test_distribution_documentation.py`

**Required metadata:**

```yaml
interface:
  display_name: "Implementing Staged Plans"
  short_description: "Create, activate, or continue implementation programs."
  default_prompt: "Use $implementing-staged-plans to create, activate, or continue a repository-backed implementation program."
policy:
  allow_implicit_invocation: false
```

- [ ] **Step 1: Add static contract RED tests**

Require explicit create intent; creation-only control-plane authority; one copy-ready launch prompt; separate typed launch receipts; exact-plan mode behavior; execution-baseline ownership; typed review preparation; accept-stop independence; new-model closure; and mandatory no-write stops for successor rollover, blocked recovery, revision, supersession, and cancellation. Reject claims that handoffs, files, retrieved prompts, or assistant-quoted prompts authorize mutation.

- [ ] **Step 2: Run RED**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_front_door_contract tests.test_distribution_documentation -v
```

- [ ] **Step 3: Rewrite the lifecycle routes and canonical references**

Put `Create a New Program`, `Activate a Generated Program`, `Before Production Modification`, `Prepare Review and Diff Disposition`, and `Close a Final Program` in execution order. Keep ordinary handoffs navigation-only. Document exact prefix recovery and the deferred Plan B routes. Remove digest repetition, per-control-file approvals, routine per-task checkpoints, and broad claims of live program advancement.

- [ ] **Step 4: Use alternative verification for prose fidelity**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_front_door_contract tests.test_distribution_documentation -v
rtk rg -n "legacy-rollover-upgrade-required|accept-stop|implementation-closure-storage/v1|program-revision-workflow-required" skills/implementing-staged-plans docs implementing-staged-plans-consolidated-design-plan-final.md implementing-staged-plans-bootstrap-execution-review-runbook.md
rtk git diff --check
```

Expected: tests pass, each normative term has one canonical owner plus precise references, and no source behavior is inferred from prose checks.

- [ ] **Step 5: Focused self-review**

```bash
rtk git diff -- skills/implementing-staged-plans/SKILL.md skills/implementing-staged-plans/agents/openai.yaml skills/implementing-staged-plans/references docs/workflows.md docs/reference.md docs/troubleshooting.md implementing-staged-plans-consolidated-design-plan-final.md implementing-staged-plans-bootstrap-execution-review-runbook.md tests/test_front_door_contract.py tests/test_distribution_documentation.py
```

Confirm the initial request never approves implementation, direct prompt submission is the meaningful boundary, Plan A makes no continuation/blocked-recovery claim, and diff acceptance, closure, commits, and consequential actions remain explicit.

---

### Task 12: Prove genesis through first diff, accept-stop, and closure across fresh processes

**Deliverable:** One causal subprocess lifecycle test exercises production writers and fresh readers through the first real product delta, plus a frozen `0.1.1` compatibility fixture for Plan B.

**Files:**

- Create: `tests/test_program_bootstrap_lifecycle.py`
- Create: `tests/fixtures/program-bootstrap/v0.1.1/`
- Modify: `tests/program_bootstrap_support.py`
- Modify: `tests/test_pressure_evidence.py`

**Interfaces consumed without redefinition:**

```python
publish_program_proposal(...)
render_program_launch_prompt(...)
activate_program(...)
prepare_exact_plan(...)
materialize_exact_plan(...)
persist_review_preparation(...)
persist_accept_stop(...)
prepare_program_closure(...)
persist_program_closure(...)
```

The subprocess fixture may inject a failure at a named private write boundary and snapshot bytes. It may not append an approval, action authorization, increment grant, review binding, or status directly.

- [ ] **Step 1: Write the subprocess RED scenario**

Process 1 publishes a proposal and captures the exact launch prompt. Process 2 submits it, prepares/materializes the exact plan, writes the planned note through the application path, transitions to reviewing, prepares real review evidence/packet, and reaches the diff gate. Process 3 submits accept-stop and proves accepted status. A final-increment branch prepares closure; Process 4 submits closure approval and proves closed. No helper may append approvals, action authorizations, grants, review bindings, or statuses directly.

- [ ] **Step 2: Add the complete Plan A failure matrix**

Parameterize failures after every successfully persisted prefix named in Tasks 2, 4, 6, 7, 8, and 9. Include every atomic `authorized -> implementing -> reviewing` status replacement, verified status, awaiting-diff status, accepted status, awaiting-closure status, and closed status before its successful response or next transition. For each: restart discovery in a subprocess; require the exact retry-ready disposition; resubmit the same operation/prompt; require one completion; test post-status lost response; mutate the newest prefix; require preservation and typed recovery-required output. These are behavioral writer-to-fresh-reader tests, not source-text assertions.

- [ ] **Step 3: Run RED, then implement only fixture support needed by production calls**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_program_bootstrap_lifecycle -v
```

Expected: nonzero at the first missing production boundary, never a fixture-manufactured pass.

- [ ] **Step 4: Freeze the compatibility fixture**

After the lifecycle passes, copy only canonical `0.1.1` package/program bytes required to prove Plan B upgrade. Add an inventory JSON containing sorted relative paths and SHA-256 digests. A test reconstructs the fixture inventory and rejects any changed, missing, unexpected, symlinked, or non-regular entry. The fixture records a program at accepted-stop and a separate awaiting-diff state; it does not contain `0.1.2` records.

- [ ] **Step 5: Run GREEN and focused self-review**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_program_bootstrap_lifecycle tests.test_pressure_evidence -v
rtk git diff --check
rtk git diff -- tests/test_program_bootstrap_lifecycle.py tests/fixtures/program-bootstrap/v0.1.1 tests/program_bootstrap_support.py tests/test_pressure_evidence.py
```

Confirm separate processes cross every production write/read boundary, the product delta is observable, review and closure are real contracts, accept-stop never continues, and Plan B's fixture is immutable evidence rather than a second implementation owner.

---

### Task 13: Synchronize version 0.1.1, verify once, and obtain one independent review

**Deliverable:** All package surfaces identify version `0.1.1`, deterministic validation passes once on the final unchanged candidate, optional installed parity remains read-only and caller-path-bound, and one independent material review has no unresolved finding.

**Files:**

- Modify: `.codex-plugin/plugin.json`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Modify: `tests/test_package_validation.py`
- Modify: `tests/test_distribution_documentation.py`
- Modify: `docs/installation.md`
- Modify: `docs/maintainers.md`

**Interfaces:**

```python
PACKAGE_VERSION = "0.1.1"
PACKAGE_CONTENT_ROOT = Path("skills/implementing-staged-plans")

def package_file_digests(root: Path) -> dict[str, str]: ...
def validate_installed_copy(source_root: Path, installed_root: Path) -> list[str]: ...
```

- [ ] **Step 1: Add package and parity RED tests**

Require every Plan A production script, exact version/description equality across three manifests, deterministic package traversal, and changed/missing/unexpected/symlink diagnostics for a supplied installed root. Prove ordinary validation performs no installed-path lookup and `.claude-plugin/**`, repository docs, tests, plans, Git state, caches, and runtime state are excluded from parity.

- [ ] **Step 2: Run RED and implement read-only validation**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_distribution_documentation tests.test_front_door_contract -v
```

Traverse with sorted `os.scandir`, `follow_symlinks=False`, and SHA-256 of `.codex-plugin/plugin.json` plus every regular file under the skill root. `--compare-installed` accepts only the explicit caller path and never installs or repairs bytes.

- [ ] **Step 3: Run focused GREEN**

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_distribution_documentation tests.test_front_door_contract -v
rtk env PYTHONDWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans
```

Expected: zero exits. Do not run installed comparison unless the user separately supplies the exact root.

- [ ] **Step 4: Run final package validation and full deterministic suite once**

Freshly verify status and scope, then run on the unchanged candidate:

```bash
rtk env PYTHONDWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk git diff --check
rtk git status --short
rtk git diff --stat
```

Expected: all required commands exit zero; only Plan A's declared implementation scope plus the preserved untracked design/plan documents appear. Do not rerun successful unchanged inputs.

- [ ] **Step 5: Obtain exactly one bounded independent material review**

Give a reviewer who did not implement the candidate: the spec, this plan, the exact base/head and dirty inventory, the complete diff, package validation, full-suite output, and the frozen fixture inventory. Scope review to requirements/scope, architecture/authority/recovery, test causality, compatibility, and unnecessary complexity. Persist raw review evidence through the repository's review contract if that write is already authorized; otherwise report it without inventing a repository record.

- [ ] **Step 6: Reconcile findings and stop**

If there is no evidence-supported material defect, do not change or re-review the candidate. If one exists within scope, record it, make the smallest repair, rerun affected checks and any final checks invalidated by changed inputs, then request one focused independent follow-up for that finding only. Stop for a program amendment or new user-owned decision.

- [ ] **Step 7: Final focused self-review and report**

```bash
rtk git diff --check
rtk git status --short
rtk git diff --stat
```

Report exact changed files; exact commands and results; review findings/dispositions; optional evaluator and installed-parity status; logical commit boundaries without staging; residual limits; and that no commit, installation, push, pull request, publication, deployment, provider, destructive, or external action occurred.

## Completion Criteria

- One explicit creation request produces a durable unapproved proposal and one launch prompt without intermediate approval.
- Publication, activation, plan preparation/materialization, review preparation, accept-stop, and closure adopt every exact partial prefix, preserve divergence, and are idempotent after status replacement.
- New-program modes are limited to standard, pre-approve, and full-increment; legacy automatic modes remain readable but cannot roll over.
- Every new manifest owns immutable increment/closure storage and empty grant/rollover/block-resolution ledgers needed by Plan B.
- Every exact plan repeats the future lifecycle-write allocation and chooses successor navigation or final closure allocation correctly.
- The execution baseline preserves user work and permits only the exact-plan product delta.
- Review and verification bindings come only from status-current, manifest-derived, exact-plan-declared evidence.
- Accept-stop is available regardless of successor state, writes an acyclic disposition binding, and can never continue.
- Closure uses manifest-derived storage, requires a final accepted increment, and grants no later action.
- Unsafe rollover, blocked transitions, generic new-model acceptance, revision, supersession, and cancellation fail before writes.
- A separate-process causal regression reaches a real diff, accept-stop, and closure; the frozen `0.1.1` fixture is digest-verified.
- Version `0.1.1` has exactly one owner. Plan A contains no Plan B implementation obligation.
- Package validation and the full deterministic suite pass once on the final unchanged candidate, followed by exactly one bounded independent material review with no unresolved material finding.
- Diff acceptance, closure, commits, installation, publication, deployment, provider access, destructive work, and consequential actions remain separately explicit.
