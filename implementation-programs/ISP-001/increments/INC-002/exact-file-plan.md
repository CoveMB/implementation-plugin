# Immutable Source and Program Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Do not delegate, run fresh model evaluations, create commits, or continue into another increment unless the approving instruction explicitly authorizes that action. Steps use checkbox syntax for tracking.

**Goal:** Add a focused, reusable procedure and deterministic implementation for immutable source capture, complete source-located requirement traceability, revisioned outcome programs, progressive elaboration, and digest-bound initial program approval.

**Architecture:** Keep the existing front door concise and route source/program authority work to one stage reference. Implement the mechanical boundary in one standard-library Python module with a pure validator and a bounded capture command. Represent extraction completeness as a digest-checked partition of every physical source line plus atomic requirement records; semantic classification remains human-reviewed and approval-bound rather than falsely automated.

**Tech stack:** Markdown; JSON and JSON Lines; Python 3 standard library (`argparse`, `dataclasses`, `hashlib`, `json`, `os`, `pathlib`, `tempfile`); `unittest`; repository fixtures; existing package validator.

## Global constraints

- Canonical source: SOURCE-002 at SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program: ISP-001 revision 2.
- Accepted prior increment: INC-001, bound to SOURCE-001 and revision 1.
- Workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin` on `main`.
- Continuation base: `f14449b8808574c720927aedab5b64871cc63858`.
- Preparation head: `62cf3fb444919c8ee2cc0eb97ee1e8ff8d28b53d`.
- Approval mode: `approval:full-increment`; this mode controls interruption and diff acceptance only.
- Preserve the explicit user-requested stop for exact-file-plan approval before implementation.
- Implementation and commit authority must be recorded separately from plan approval.
- Keep reusable and package-facing names project-neutral. ISP, INC, SOURCE, requirement, approval, authorization, decision, and amendment identifiers are allowed only in repository governance records.
- Preserve SOURCE-001, revision-1 program artifacts, accepted INC-001 evidence, and all unrelated work byte-for-byte.
- Do not overwrite an existing source snapshot, accepted packet, decision, amendment, approval, authorization, or evidence record.
- Do not add a third-party dependency, package manager, MCP server, app, hook, marketplace, publisher identity, publication configuration, network call, or external connector.
- Do not install the plugin, push, create a pull request, publish, release, deploy, migrate, perform destructive operations, or modify consequential external state.
- Treat line coverage as mechanical extraction evidence, not proof that semantic classification is correct.
- Do not claim current ISP-001 traceability is machine-complete until the atomic inventory is implemented, validated, reviewed, and accepted.
- Do not begin INC-003.

## Requirements and acceptance binding

This plan advances the approved groups `REQ-AUTHORITY`, `REQ-SOURCE-PROGRAM`, `REQ-ARTIFACT-INVARIANTS`, `REQ-VALIDATION`, `REQ-SEQUENCE`, and `REQ-DEFAULTS`.

It must satisfy the five approved INC-002 criteria:

1. every source requirement receives a stable identifier, source locator, acceptance criteria, increment allocation, and current disposition;
2. partial extraction cannot claim completeness;
3. source or approval digest mismatch fails closed;
4. program revisions preserve prior evidence and invalidate stale approval;
5. a large-plan pilot avoids project-specific policy leakage.

## Exact data contracts

### Source capture record

`capture_source(...) -> SourceCaptureRecord` returns an immutable record with:

```python
@dataclass(frozen=True)
class SourceCaptureRecord:
    source_id: str
    snapshot_path: str
    metadata_path: str
    sha256: str
    byte_count: int
    line_count: int
```

The public function signature is:

```python
def capture_source(
    *,
    source_path: Path,
    program_root: Path,
    snapshot_path: PurePosixPath,
    metadata_path: PurePosixPath,
    source_id: str,
    expected_sha256: str,
    access_method: str,
) -> SourceCaptureRecord:
```

Both destination paths are relative to the resolved program root, must have existing resolved parents inside that root, and must not already exist. The source must be a regular non-symlink file. Capture streams exact bytes into securely created same-directory temporary files, verifies SHA-256 before finalization, finalizes without overwriting an existing path, and writes metadata only for the verified bytes. A failed or partial capture never advances program state.

### Traceability v2 record

The current traceability artifact advances to `implementation-traceability/v2` with these top-level fields:

```json
{
  "schema_version": "implementation-traceability/v2",
  "program_id": "PROGRAM-001",
  "program_revision": 1,
  "source_id": "SOURCE-001",
  "source_sha256": "f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57",
  "coverage_assertion": {
    "status": "complete",
    "machine_complete": true,
    "source_line_count": 120,
    "semantic_requirements_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "approval_event_id": "APPROVAL-001"
  },
  "source_units": [],
  "requirement_groups": [],
  "atomic_requirements": []
}
```

Each `source_units` entry contains exactly:

```json
{
  "id": "SOURCE-UNIT-AUTHORITY",
  "start_line": 1,
  "end_line": 8,
  "source_text_sha256": "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
  "classification": "requirement",
  "requirement_ids": ["AUTHORITY-PRESERVE-SOURCE"]
}
```

For `classification: context`, `requirement_ids` is empty and a non-empty `context_rationale` is required. Units are unique, ordered, non-overlapping, and form one exact partition from line 1 through the source metadata line count, including headings and blank lines.

Each `atomic_requirements` entry contains exactly:

```json
{
  "id": "AUTHORITY-PRESERVE-SOURCE",
  "group_id": "AUTHORITY",
  "source_unit_ids": ["SOURCE-UNIT-AUTHORITY"],
  "source_locator": "section 4.1, lines 99-107",
  "normalized_requirement": "Preserve the authoritative source as immutable evidence.",
  "acceptance_criteria": ["A changed source byte produces a digest mismatch and a failed authority validation."],
  "assigned_parts": ["Program authority"],
  "assigned_tasks": ["Capture and validate immutable source evidence"],
  "assigned_increments": ["Source and program authority"],
  "current_disposition": "allocated",
  "decision_references": [],
  "implementation_evidence": [],
  "verification_evidence": []
}
```

Stable requirement identifiers use semantic uppercase tokens and must not derive meaning only from source order. Atomic records require at least one requirement-classified source unit, one acceptance criterion, and non-empty part, task, and increment allocations. Allowed current dispositions are `allocated`, `implemented`, `amended`, `deferred`, `rejected`, `not-applicable`, and `resolved`; every disposition other than `allocated` or `implemented` requires its corresponding approval, ownership, or rationale fields.

`semantic_requirements_sha256` is SHA-256 over canonical UTF-8 JSON containing only the ordered semantic fields (`id`, `group_id`, `source_unit_ids`, `normalized_requirement`, `acceptance_criteria`, and allocation fields). Evidence and mutable disposition fields are excluded so accepted semantics remain distinguishable from later evidence updates.

### Program approval binding

An approved program requires one append-only JSON Lines event whose exact binding fields match the loaded artifacts:

```json
{
  "type": "program-approval",
  "decision": "approved",
  "program_id": "PROGRAM-001",
  "program_revision": 1,
  "source_id": "SOURCE-001",
  "source_sha256": "f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57",
  "program_sha256": "ec94caa50ff8918e242170220816e92ea2c48b36cd6b2e19c531d37aea8d0324",
  "semantic_requirements_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "approval_mode": "approval:standard"
}
```

Any missing approval, non-approved decision, changed source digest, changed program digest, changed semantic digest, different revision, or duplicate conflicting approval fails closed. A later revision points to prior immutable program/source records and their digests; the matching approval must name the later revision, while accepted prior evidence remains bound to the earlier revision.

The digest strings in the schema examples demonstrate the required lowercase 64-character format; fixture generation and validation always recompute the actual bound values.

## File map

### Create during authorized implementation

- `skills/implementing-staged-plans/references/program-authority.md` — focused operator procedure for source capture, complete decomposition, progressive elaboration, program revisioning, approval, validation, and hard stops.
- `skills/implementing-staged-plans/scripts/program_authority.py` — standard-library capture and authority validator described above.
- `tests/test_program_authority.py` — unit, negative, CLI, revision, approval, and current-program contract tests.
- `tests/fixtures/program-authority/portable-archive-program/manifest.json` — neutral pilot logical-role mapping and digest bindings.
- `tests/fixtures/program-authority/portable-archive-program/source/implementation-plan.md` — fictional large plan with twelve sections and forty-eight independently dispositionable requirements.
- `tests/fixtures/program-authority/portable-archive-program/source/source-metadata.json` — immutable pilot source record.
- `tests/fixtures/program-authority/portable-archive-program/program/implementation-program.md` — outcome-oriented pilot program with distant files left provisional.
- `tests/fixtures/program-authority/portable-archive-program/program/traceability.json` — complete v2 source-unit and atomic-requirement inventory.
- `tests/fixtures/program-authority/portable-archive-program/state/approvals.jsonl` — exact digest-bound pilot program approval.
- `implementation-programs/ISP-001/increments/INC-002/execution-record.md` — commands, observed RED/GREEN evidence, deviations, and immutable bindings.
- `implementation-programs/ISP-001/increments/INC-002/reviews/requirements.md` — accepted-scope and atomic-coverage review.
- `implementation-programs/ISP-001/increments/INC-002/reviews/architecture.md` — boundary, naming, security, and simplicity review.
- `implementation-programs/ISP-001/increments/INC-002/reviews/test-evidence.md` — test and evidence-validity review.
- `implementation-programs/ISP-001/increments/INC-002/review-packet.md` — human diff handoff.
- `implementation-programs/ISP-001/increments/INC-002/handoff.md` — durable continuation record that stops before INC-003.

### Modify during authorized implementation

- `skills/implementing-staged-plans/SKILL.md:62-74` — route source registration, decomposition, traceability, revision, and initial-program-approval work to the focused reference after universal gates.
- `skills/implementing-staged-plans/scripts/validate_package.py:13-15,242-288` — require the accepted authority reference/script and continue package-facing naming and link validation.
- `tests/test_package_validation.py:52-75,212-301` — extend valid fixtures and negative checks for the new required package assets.
- `tests/test_front_door_contract.py:13-77,80-108` — require the narrow route and resolved reference without relaxing the concise front-door limit.
- `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json` — replace group-only completeness with v2 source-unit coverage and source-located atomic requirements; retain group allocation and revision-1 evidence references.
- `implementation-programs/ISP-001/manifest.json` — update traceability binding and current INC-002 evidence/status after implementation.
- `implementation-programs/ISP-001/state/status.json` — advance only through authorized INC-002 lifecycle states and end at `awaiting-diff-approval`.
- `implementation-programs/ISP-001/state/approvals.jsonl` — append exact-file-plan and later diff approval records only when explicitly supplied.
- `implementation-programs/ISP-001/state/action-authorizations.jsonl` — append bounded implementation authority only when explicitly supplied.

### Preserve unchanged

- `implementing-staged-plans-consolidated-design-plan-final.md`.
- `implementation-programs/ISP-001/source/implementation-plan.md` and `source/source-metadata.json` for SOURCE-001.
- `implementation-programs/ISP-001/source/revisions/SOURCE-002/**`.
- `implementation-programs/ISP-001/program/implementation-program.md` and `program/traceability.json` for revision 1.
- all accepted INC-001 implementation, evidence, reviews, packet, and handoff files.
- `.gitignore`, `.codex-plugin/plugin.json`, and `skills/implementing-staged-plans/agents/openai.yaml`.

## Semantic naming inventory

| Proposed surface | Stable context and intention | Governance-term basis |
|---|---|---|
| `references/program-authority.md` | Procedure controlling source and approved-program authority | “program” names the durable implemented domain |
| `scripts/program_authority.py` | Mechanical source/program authority boundary | “program” names the durable implemented domain |
| `validate_program_authority` | Validates the complete authority binding | none |
| `capture_source` | Captures immutable source evidence | none |
| `SourceCaptureRecord` | Immutable capture result | none |
| `source_units` | Complete partition of source evidence | none |
| `atomic_requirements` | Independently dispositionable obligations | none |
| `portable-archive-program` | Fictional pilot domain | “program” names a real governance artifact |
| `test_machine_complete_claim_requires_full_source_partition` | Observable behavior under test | none |
| ISP-001/INC-002 paths and headings | Repository implementation governance and evidence | explicitly permitted governance records |

No distributable filename, symbol, command, test title, fixture title, schema identifier, or generated path is named from the ISP-001 increment sequence.

---

### Task 0: Bind plan approval and implementation authority

**Files:**

- Modify: `implementation-programs/ISP-001/state/status.json`
- Modify: `implementation-programs/ISP-001/state/approvals.jsonl`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl`

**Produces:** A digest-bound approved plan and a separate bounded authorization before package, test, fixture, or current traceability implementation writes begin.

- [ ] **Step 1: Revalidate the approval basis**

Confirm SOURCE-002 digest, revision 2 program digest, this exact-file-plan digest, `main`, selected base, current head, clean/dirty state, INC-001 accepted evidence, approval mode, and named write scope. Treat any overlap or changed binding as drift and stop.

- [ ] **Step 2: Persist exact-file-plan approval**

Append one approval event binding the plan digest, SOURCE-002 digest, revision 2 program digest, workspace, INC-002, and `approval:full-increment`.

- [ ] **Step 3: Persist separate action authorization**

Append one authorization naming the package/reference/script/test/fixture/governance files, local verification, proposed focused commits if authorized, and review mode. Preserve every consequential-action exclusion.

- [ ] **Step 4: Transition only to `authorized`**

Update status atomically with a previous-state reference. Do not mark implementation started until the first approved RED test is about to be written.

### Task 1: Define complete authority validation through failing tests

**Files:**

- Create: `tests/test_program_authority.py`
- Create the six files under `tests/fixtures/program-authority/portable-archive-program/`

**Interfaces:**

- Consumes: the exact contracts in this plan.
- Produces: executable expectations for `capture_source`, `validate_program_authority`, `compute_semantic_requirements_digest`, and CLI `main`.

- [ ] **Step 1: Add import and fixture helpers**

Load `program_authority.py` with `importlib.util.spec_from_file_location`. Add `ProgramAuthorityFixture`, which copies the neutral valid fixture into a `TemporaryDirectory`, reads/writes JSON deterministically, rewrites approval events after an intentional mutation, and never uses ISP-001 identifiers.

- [ ] **Step 2: Add traceability completeness tests**

Cover a valid source partition; missing first/last/interior lines; overlap; reversed range; changed unit digest; duplicate unit; requirement unit without an atomic record; context unit without rationale; atomic record referencing context; duplicate semantic ID; empty acceptance; missing part/task/increment allocation; invalid disposition; and `machine_complete: true` while any completeness issue exists.

- [ ] **Step 3: Add source and program binding tests**

Cover missing logical role, absolute/escaping role path, symlink role path, changed source bytes, changed metadata digest/count, changed program Markdown, missing approval, non-approved decision, stale source/program/semantic digest, conflicting approvals, and correct current binding.

- [ ] **Step 4: Add revision preservation tests**

Build revision 2 from the fixture, retain revision-1 source/program/evidence paths and digests, and assert revision-1 approval becomes stale for revision 2 while the new matching approval passes. Reject a revision that omits or mutates its declared prior evidence.

- [ ] **Step 5: Add source capture and CLI tests**

Cover exact byte preservation, SHA-256/count metadata, wrong expected digest, existing destination, source symlink, destination-parent symlink, path escape, deterministic sorted validation output, success exit 0, validation failure exit 1, and usage failure exit 2.

- [ ] **Step 6: Run focused tests and observe RED**

```bash
rtk python3 -m unittest tests.test_program_authority -v
```

Expected: import failure naming missing `skills/implementing-staged-plans/scripts/program_authority.py`. Record the exact failure before implementation.

### Task 2: Implement the pure program-authority validator

**Files:**

- Create: `skills/implementing-staged-plans/scripts/program_authority.py`
- Modify: `tests/test_program_authority.py`

**Interfaces:**

- Produces: `sha256_file`, `load_json_object`, `load_json_lines`, `resolve_managed_path`, `compute_semantic_requirements_digest`, `validate_source_binding`, `validate_traceability`, `validate_program_approval`, and `validate_program_authority`.

- [ ] **Step 1: Implement deterministic loading and path containment**

Use resolved concrete paths. Require logical-role paths to be non-empty relative POSIX paths whose resolved target stays under the resolved program root. Reject symlinks for immutable or controlling files. Return issues rather than raising for malformed repository data.

- [ ] **Step 2: Implement exact source binding validation**

Hash binary source bytes, count bytes, count `bytes.splitlines(keepends=True)`, and compare source ID/path/digest/count fields across manifest, metadata, and traceability.

- [ ] **Step 3: Implement complete source-unit validation**

Validate the exact partition, recompute every unit digest from source bytes, enforce requirement/context contracts, and prevent a complete claim when any line, digest, or atomic reference is invalid.

- [ ] **Step 4: Implement atomic requirement and semantic digest validation**

Validate exact fields, stable semantic IDs, group references, source-unit references, non-empty acceptance/allocation arrays, allowed dispositions, and deterministic canonical semantic digest.

- [ ] **Step 5: Implement program and approval binding validation**

Hash the approved Markdown program; require one matching approved event; reject stale or conflicting bindings; validate declared prior-revision source/program/evidence paths without treating the prior approval as current.

- [ ] **Step 6: Run validator tests**

```bash
rtk python3 -m unittest tests.test_program_authority -v
```

Expected: validation tests pass; capture tests remain RED until Task 3.

### Task 3: Implement immutable source capture and CLI routing

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/program_authority.py`
- Modify: `tests/test_program_authority.py`

**Interfaces:**

- Produces: `SourceCaptureRecord`, `capture_source`, `build_argument_parser`, and `main` subcommands `capture-source` and `validate-program`.

- [ ] **Step 1: Implement secure temporary capture**

Create temporary files in each resolved destination directory with `NamedTemporaryFile(delete=False)`, mode `w+b`, and explicit cleanup on ordinary failure. Stream source bytes once while hashing and counting. Close handles before finalization.

- [ ] **Step 2: Finalize without overwriting**

Require absent final paths, finalize by creating a same-filesystem hard link from the temporary file to the final path so an existing target fails rather than being replaced, then unlink the temporary name. If hard-link finalization is unsupported, fail closed with an actionable issue; do not fall back to overwrite-capable replacement.

- [ ] **Step 3: Write deterministic metadata**

Serialize UTF-8 JSON with sorted keys, two-space indentation, and one trailing newline. Finalize metadata without overwrite only after snapshot verification. Report partial multi-file capture explicitly and do not advance state.

- [ ] **Step 4: Implement deterministic CLI behavior**

`capture-source` requires every path/identity/digest/access argument. `validate-program` accepts a program root and optional `--allow-incomplete` for preparation only; the default rejects incomplete or unapproved authority. Print sorted issues, no tracebacks for repository-data errors, and no secrets or source content.

- [ ] **Step 5: Run focused tests**

```bash
rtk python3 -m unittest tests.test_program_authority -v
```

Expected: all authority, capture, revision, and CLI tests pass.

### Task 4: Add the focused procedure and front-door route

**Files:**

- Create: `skills/implementing-staged-plans/references/program-authority.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Modify: `tests/test_package_validation.py`
- Modify: `tests/test_front_door_contract.py`

**Produces:** A concise discoverable package route without duplicating the canonical workflow.

- [ ] **Step 1: Extend structural tests and observe RED**

Require the reference and script in valid package fixtures; reject either missing asset; require the front door to link the procedure for source capture, decomposition, traceability, revision, and initial approval; retain the under-250-line constraint and project-neutral package-facing naming check.

```bash
rtk python3 -m unittest tests.test_package_validation tests.test_front_door_contract -v
```

Expected: failures naming the missing reference/route.

- [ ] **Step 2: Write `program-authority.md`**

Document, in this order: prerequisite authority; exact capture; read-only repository inspection; exhaustive source-unit classification; atomic requirement splitting; outcome-oriented decomposition; progressive elaboration boundaries; revision/evidence preservation; digest-bound program approval; validation command; hard stops; and returned bounded result. State explicitly that source coverage is mechanical evidence while semantic classification requires human review and approval.

- [ ] **Step 3: Add the narrow front-door route**

After universal gates and current-stage discovery, route source registration, decomposition, traceability, program revision, and initial approval to `[Program authority](references/program-authority.md)`. Do not copy the procedure into `SKILL.md` or alter unrelated routing.

- [ ] **Step 4: Extend package validation**

Add constants for the reference and script plus `validate_authority_assets(repository_root)`. Require both regular files, include the reference in existing link/naming scans, and preserve deterministic issue ordering.

- [ ] **Step 5: Run focused structural tests**

```bash
rtk python3 -m unittest tests.test_package_validation tests.test_front_door_contract -v
rtk python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: all commands pass.

### Task 5: Prove decomposition and expand ISP-001 atomic traceability

**Files:**

- Complete: `tests/fixtures/program-authority/portable-archive-program/**`
- Modify: `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
- Modify: `tests/test_program_authority.py`

**Produces:** One neutral large-plan pilot and one honest source-located ISP-001 atomic inventory.

- [ ] **Step 1: Complete the neutral pilot**

The fictional source contains twelve headed sections and forty-eight separately testable requirements covering inventory intake, checksum verification, retention, privacy, recovery, accessibility, compatibility, observability, operator review, approval, staged delivery, and closure. Context paragraphs and blank lines remain explicit context units. The program groups requirements into outcomes and provisional increments without prescribing distant files. No ISP, INC, P, or REQ roadmap identifiers appear in package-facing or reusable fixture names/content.

- [ ] **Step 2: Validate pilot completeness and leakage**

Assert every physical source line is partitioned, all forty-eight requirements have atomic records, every record has acceptance/allocation/disposition, the approval digests match, changing one byte fails, deleting one atomic record fails, and package-facing roadmap-pattern validation reports no issue.

- [ ] **Step 3: Expand ISP-001 revision-2 traceability**

Partition all 1,362 SOURCE-002 lines into digest-bound source units. Classify every unit as requirement or context with a rationale. Split each independently dispositionable obligation into a semantic atomic requirement, retain its approved group parent, add exact section/line locator, acceptance criteria, part/task/increment allocation, current disposition, and any revision-1 evidence binding. Keep `machine_complete: false` and set expansion status to `awaiting-inc-002-diff-approval` until the human accepts the completed INC-002 diff.

- [ ] **Step 4: Audit atomic extraction without sampling**

Review all source units in order against SOURCE-002. Search every normative keyword and every bulleted/numbered contract; reconcile each hit to an atomic requirement or explicit context rationale. Run the validator against ISP-001 with the preparation-only incomplete-approval allowance, and record the complete command output and semantic digest.

```bash
rtk python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001 --allow-incomplete
rtk python3 -m unittest tests.test_program_authority -v
```

Expected: structure, source coverage, source/program digests, and atomic records validate; the current machine-completeness claim remains false pending diff acceptance.

### Task 6: Review, verify, and build the INC-002 packet

**Files:**

- Create: the INC-002 execution record, three review reports, review packet, and handoff listed in the file map.
- Modify: revision-2 traceability, manifest, status, approvals, and action-authorizations only as authorized.

**Produces:** A reviewed INC-002 diff in `awaiting-diff-approval`, with no INC-003 work.

- [ ] **Step 1: Freeze the proposed diff**

Record preparation head, current head, authorized commits if any, changed paths, worktree state, and exact SOURCE-001/SOURCE-002/revision-1/revision-2 digests.

- [ ] **Step 2: Run separate non-independent review passes**

Requirements review checks every approved INC-002 criterion, every advanced group, full source-unit coverage, atomic fields, and absence of a premature completeness claim. Architecture review checks immutable-write safety, path containment, revision preservation, semantic naming, pure-core boundaries, and unnecessary complexity. Test-evidence review checks observed RED evidence, negative-fixture intent, pilot completeness, exact commands, and static-versus-agent-behavior claim limits. Persist each report before reconciling them and label assurance reduced/non-independent unless a separately authorized independent reviewer is used.

- [ ] **Step 3: Repair only material INC-002 findings**

Record affected requirement, evidence, impact, repair, and rerun. Stop for a program amendment if a repair changes approved outcome, acceptance, source authority, sequencing, risk posture, or public contract.

- [ ] **Step 4: Run fresh final verification once**

```bash
rtk python3 -m unittest discover -s tests -v
rtk python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program tests/fixtures/program-authority/portable-archive-program
rtk python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001 --allow-incomplete
rtk python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans
rtk git diff --check
rtk git status --short --branch
```

Expected: all test, package, neutral-pilot, current-program structural, quick-validation, and changed-tree whitespace checks pass. The current ISP-001 command must explicitly report that semantic machine completeness awaits INC-002 diff approval rather than falsely reporting final approval.

- [ ] **Step 5: Build and validate the review packet**

Include achieved outcome, requirement and acceptance disposition, changed files by purpose, recommended review order, exact RED/GREEN/final results, revision preservation, source and semantic digests, review findings/repairs, deviations, naming inventory, completeness limitations, edge cases, security/privacy implications, rollback/recovery, workspace/base/head/commits, current state, and next legal action.

- [ ] **Step 6: End at the mandatory boundary**

Set INC-002 to `awaiting-diff-approval`. Do not mark atomic traceability machine-complete, accept the diff, begin INC-003, or perform any consequential external action. The later human acceptance event may bind the semantic digest and activate the completeness claim.

## Focused commit boundaries if separately authorized

1. `test: define program authority contracts` — Task 1 tests and neutral fixture skeleton.
2. `feat: validate source and program authority` — Tasks 2 and 3 implementation plus passing focused tests.
3. `feat: route program authority workflow` — Task 4 reference, front-door route, package validation, and tests.
4. `docs: expand atomic requirement traceability` — Task 5 neutral pilot and ISP-001 atomic records.
5. `docs: record increment 2 review evidence` — Task 6 reviews, packet, handoff, and final state.

Commit messages are proposed review boundaries only. Do not create them unless the action authorization explicitly includes local commits.

## Rollback and recovery

- No data, deployment, provider, marketplace, installation, or production state is touched.
- Before commits, recover by editing only named files; never reset, clean, stash, overwrite, or discard unrelated work.
- After authorized commits, propose targeted reversion of only the focused INC-002 commits and wait for explicit authorization before reverting.
- Immutable snapshots and accepted evidence are never rollback targets. Corrections use a new source/program revision or addendum.
- A partial new capture is blocked evidence, not an approved snapshot; preserve its paths and report the smallest repair rather than overwriting it.

## Approval required to execute

The next legal approval must bind ISP-001 revision 2, SOURCE-002 digest, the revision-2 program digest, `main`, the current head after these governance writes, INC-002, and this exact-file-plan digest. It must separately authorize:

1. the named reference, Python module, tests, fixtures, current traceability, and INC-002 evidence writes;
2. local deterministic verification commands;
3. the five focused local commits, if desired;
4. separate non-independent review passes, or one bounded independent final reviewer if explicitly requested;
5. remediation limited to evidence-backed material INC-002 findings.

It must preserve all prohibitions on INC-003, installation, marketplace changes, push, pull request, publication, release, deployment, migration, destructive action, and consequential external state.
