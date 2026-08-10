# Repository Preparation and Exact-File Planning Implementation Plan

**Goal:** Implement a read-only, repository-backed preparation boundary that observes Git truth, protects existing work, classifies drift and evidence applicability, assesses increment shape and amendment scope, and validates current exact-file plans with contextual semantic naming inventories.

**Architecture:** Add one focused standard-library `repository_preparation.py` module with a Git adapter around a pure decision/validation core, plus one concise operator reference. Reuse `RepositoryObservation`, program/state authority validation, managed-path resolution, and existing package-validation conventions. Persist no external evidence and mutate no repository state from the new module; program-state and append-only governance writes remain owned by the accepted state-authority boundary.

**Tech stack:** Python 3.14 standard library, Git porcelain v2/rev-parse, `unittest`, JSON/Markdown fixtures, existing package, program, state, and skill validators.

## Global constraints

- Authority is ISP-001 revision 2, SOURCE-002 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`, program Markdown `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`, accepted traceability `eb0ab811543ad3e9da15373462bd9fe661d0085f9bb4f8e57ea1c002bef349d6`, and semantic digest `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Preserve SOURCE-001, SOURCE-002, both prior program revisions, accepted INC-001 through INC-003 evidence, `APR-013`, `AUTH-009`, the approved semantic fields/digest, and every accepted or user-owned dirty path.
- Base implementation on `main` at accepted INC-003 head `53edb8fad2008c7d35b6c17dbb973b24022947fd` and selected base `f14449b8808574c720927aedab5b64871cc63858`. Revalidate both and the full dirty inventory immediately before any write.
- The selected mode is `approval:full-increment`, but the user explicitly requires approval of this plan before implementation. This explicit gate controls.
- Approval mode controls interruption and diff acceptance only. It never grants repository writes, evaluator/subagent dispatch, commits, push, pull request, publication, release, deployment, migration, destructive operations, provider mutation, or external-state authority.
- No commit is authorized. Proposed commit boundaries below are review slices only and must not be staged or committed without a later separate exact authorization.
- Keep reusable/package-facing paths, symbols, commands, tests, fixture content, headings, schemas, and observable identifiers project-neutral. ISP-001 and INC-004 appear only in repository governance/evidence artifacts.
- Use strict RED-GREEN-REFACTOR for behavior. Record every intended RED before implementation. Use alternative verification only for reference/evidence/governance documents.
- Use argument-vector subprocess calls with `shell=False`, explicit `cwd`, captured bytes, bounded timeouts, and deterministic issue reporting. Never print source contents, environment variables, credentials, tokens, or secrets.
- Use `PYTHONDONTWRITEBYTECODE=1` for Python checks. Add no dependency, package manager, schema framework, hook, app, MCP server, marketplace, publisher, or publication configuration.
- Stop with INC-004 at `awaiting-diff-approval`. Do not accept its diff, begin INC-005, close ISP-001, or perform any consequential external action.

## Requirements and acceptance binding

| Accepted criterion | Planned evidence |
|---|---|
| Repository fixtures cover dirty state, untracked files, active Git operations, base movement, pre-existing failures, managed paths, reusable code, dependency drift, and invalidated provisional assumptions | A neutral scenario catalog plus temporary real-Git tests for porcelain parsing, operation markers, ancestry, dirty-path ownership, baseline-result records, managed/generated boundaries, reuse discovery, manifest drift, and invalidated assumptions |
| Evidence refresh follows materiality and risk | Table-driven `decide_evidence_refresh` tests for every materiality predicate, high-risk unavailable evidence, lower-risk exact reuse, version/configuration/assumption mismatch, access failure, and irrelevant installed surfaces |
| Benign, reconcilable, and base-invalidating drift are distinct | Immutable qualitative categories and paired tests for unrelated dirty work, relevant file/assumption movement, protected overlap, conflicts, operations, base/head movement, requirements/contracts, and incompatible dependency change |
| Production changes cannot begin without a current exact-file plan | Current-plan path/digest/head/preparation binding tests plus integration with accepted state/action binding so absent, stale, symlinked, or mismatched plans reject workspace modification |
| A bounded implementation amendment cannot conceal a program amendment | Program dimensions dominate classification in exhaustive table tests; bounded classification additionally requires evidence, obligation preservation, no user-owned decision, and credible reversibility/recovery |
| Proposed implementation-owned names identify stable context and intention, and planning vocabulary is justified only by an implementation-governance role or durable domain concept | Contextual naming inventory tests across paths, symbols, commands, tests, fixtures, headings, schemas/identifiers, and generated paths, with paired valid governance/domain uses, invalid roadmap-only uses, and compatibility handling for existing public/persisted/generated/external names |

The implementation advances the eight named requirement groups. Atomic requirements assigned across multiple increments remain `allocated` unless the INC-004 diff directly demonstrates their contract. Evidence-only traceability updates must not change ordered semantic fields or their digest.

## Exact preparation contracts

### Repository inspection

Reuse `state_authority.RepositoryObservation` as the authoritative staged/modified/untracked/conflicted/operation record. Add:

```python
REPOSITORY_INSPECTION_SCHEMA = "implementation-repository-inspection/v1"

@dataclass(frozen=True)
class RepositoryInspection:
    schema_version: str
    observation: RepositoryObservation
    git_directory: str
    git_common_directory: str
    selected_base_is_ancestor: bool
    status_format: str

def inspect_repository(
    workspace_path: Path,
    selected_base_commit: str,
    *,
    timeout_seconds: float = 10.0,
) -> RepositoryInspection: ...
```

`inspect_repository` runs only these read-only Git command families with argument vectors:

- `git rev-parse --show-toplevel`, `--git-dir`, `--git-common-dir`, and `HEAD`;
- `git branch --show-current`;
- `git status --porcelain=v2 --branch -z --untracked-files=all`;
- `git merge-base --is-ancestor <selected-base> <head>`;
- `git rev-parse --git-path <marker>` for `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, `rebase-merge`, `rebase-apply`, `sequencer`, and `BISECT_LOG`.

The parser consumes bytes so a filename with whitespace, tabs, newlines, non-ASCII bytes representable by the filesystem, or rename metadata cannot be split as prose. It returns repository-root-relative POSIX paths, preserves both rename paths for overlap analysis, rejects unknown mandatory record kinds, rejects detached HEAD for a branch-bound workspace, and reports Git failure/timeout without a traceback or partial success claim. Multiple operation markers are returned as a deterministic compound operation and classified base-invalidating.

### Workspace ownership and drift

```python
DRIFT_CATEGORIES = frozenset({
    "benign",
    "reconcilable-relevant",
    "base-invalidating",
})

@dataclass(frozen=True)
class DriftContext:
    previous: RepositoryInspection
    current: RepositoryInspection
    relevant_paths: tuple[str, ...]
    protected_paths: tuple[str, ...]
    accepted_existing_paths: tuple[str, ...]
    managed_paths: tuple[str, ...]
    dependency_paths: tuple[str, ...]
    dependency_compatibility_confirmed: bool
    pre_existing_failures: tuple[str, ...]
    current_failures: tuple[str, ...]
    relevant_failures: tuple[str, ...]
    reusable_candidates: tuple[str, ...]
    selected_reuse: tuple[str, ...]
    requirements_changed: bool
    protected_contract_changed: bool
    provisional_assumption_invalidated: bool

@dataclass(frozen=True)
class DriftAssessment:
    category: str
    reasons: tuple[str, ...]
    affected_paths: tuple[str, ...]
    required_action: str

def classify_repository_drift(context: DriftContext) -> DriftAssessment: ...
def validate_plan_overlap(
    proposed_paths: Sequence[str],
    current: RepositoryObservation,
    accepted_existing_paths: Sequence[str],
    explicit_dispositions: Mapping[str, str],
) -> list[str]: ...
```

Classification precedence is deterministic:

1. **Base-invalidating:** repository/path/branch/base binding mismatch; selected base not an ancestor; prepared head moved; conflicts or active Git operation; proposed overlap with unaccepted user work; changed requirements/protected contract; incompatible or unverified material dependency change.
2. **Reconcilable relevant:** relevant file, manifest, reusable mechanism, or provisional assumption changed while source/program semantics, protected contracts, base, user ownership, and compatibility remain valid. Required action is evidence and plan refresh under the current gate.
3. **Benign:** changes are unrelated to current outcome/assumptions/contracts and do not overlap proposed or protected paths. Required action is record and continue.

An accepted dirty path is not silently considered product scope. It is only eligible for modification when the exact plan names the path, its current owner, and an explicit preserve/extend disposition. Managed or generated paths require their owning mechanism and regeneration/verification command; an absent owner is an issue.

Known baseline failures remain recorded and do not become INC-004 regressions by relabelling. A new relevant failure is base-invalidating until explained or repaired; an unchanged unrelated pre-existing failure is recorded without being incorporated. Reusable candidates and the selected reuse/rationale are part of the assessment so a new abstraction cannot be justified without first accounting for current repository mechanisms.

### Evidence applicability

```python
EVIDENCE_RECORD_SCHEMA = "implementation-evidence-record/v1"

MATERIAL_EVIDENCE_PREDICATES = frozenset({
    "dependency-or-runtime-change",
    "provider-or-integration-change",
    "version-sensitive-api",
    "authentication-or-authorization",
    "security-or-privacy",
    "payments",
    "persistence-or-migration",
    "deployment-or-provider-state",
    "compatibility-or-security-assumption",
    "externally-defined-public-contract",
})

@dataclass(frozen=True)
class EvidenceRecord:
    schema_version: str
    source: str
    accessed_on: str
    version: str
    configuration: str
    claims_supported: tuple[str, ...]
    risk_domain: str
    reuse_basis: str
    remaining_uncertainty: str

@dataclass(frozen=True)
class EvidenceContext:
    material_predicates: tuple[str, ...]
    risk_level: str
    official_evidence_available: bool
    prior_version_matches: bool
    prior_configuration_matches: bool
    prior_assumptions_match: bool
    access_failure: str | None

@dataclass(frozen=True)
class EvidenceDecision:
    disposition: str
    reasons: tuple[str, ...]
    required_record_fields: tuple[str, ...]

def decide_evidence_refresh(context: EvidenceContext) -> EvidenceDecision: ...
def validate_evidence_record(record: EvidenceRecord) -> list[str]: ...
```

Dispositions are `not-material`, `refresh-required`, `reuse-with-residual-uncertainty`, and `blocked`. A material surface with available official evidence requires refresh. Unavailable evidence blocks high-risk work. Lower-risk prior evidence is reusable only when version, configuration, and assumptions all match and the access failure plus uncertainty are recorded. Installed but untouched dependencies do not trigger refresh.

### Amendment and increment-shape assessment

```python
PROGRAM_AMENDMENT_DIMENSIONS = frozenset({
    "requirement",
    "acceptance-criterion",
    "scope",
    "user-visible-behavior",
    "security-or-privacy-obligation",
    "protected-contract",
    "data-ownership",
    "irreversible-behavior",
    "risk-posture",
    "dependency-sequence",
    "material-sequencing",
    "user-review-cadence",
})

@dataclass(frozen=True)
class AmendmentProposal:
    proposed_classification: str
    changed_dimensions: tuple[str, ...]
    evidence: tuple[str, ...]
    obligations_preserved: bool
    user_owned_decision: bool
    reversible_or_recoverable: bool
    authoritative_contradiction: bool

@dataclass(frozen=True)
class AmendmentAssessment:
    classification: str
    reasons: tuple[str, ...]
    requires_program_revision: bool
    may_proceed_under_current_mode: bool

@dataclass(frozen=True)
class IncrementShape:
    outcomes: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    verification_contracts: tuple[str, ...]
    rollback_or_recovery: tuple[str, ...]
    risk_domains: tuple[str, ...]
    depends_on_unimplemented_safeguards: tuple[str, ...]
    leaves_repository_valid: bool

def classify_plan_amendment(proposal: AmendmentProposal) -> AmendmentAssessment: ...
def assess_increment_shape(shape: IncrementShape) -> list[str]: ...
```

An authoritative contradiction always stops. Any program dimension forces `program-amendment` regardless of the proposed label. A bounded implementation amendment requires non-empty evidence, preserved obligations, no unresolved user-owned decision, and credible reversibility/recovery. A minor correction is limited to path/helper/test-convention corrections with no changed program dimension. Reviewability has no numeric file/line threshold; it requires one coherent outcome, traceable requirements, acceptance, meaningful verification, coherent recovery, no unrelated risk-domain bundling, no dependency on absent safeguards, and a valid resulting repository.

### Semantic naming inventory

```python
SURFACE_KINDS = frozenset({
    "path",
    "symbol",
    "command",
    "test-or-fixture",
    "heading",
    "schema-or-identifier",
    "generated-path",
})

@dataclass(frozen=True)
class SemanticNameRecord:
    surface: str
    surface_kind: str
    origin: str
    context: str
    intention: str
    planning_term_basis: str
    basis_owner: str
    compatibility_class: str
    compatibility_disposition: str

def validate_semantic_naming_inventory(
    records: Sequence[SemanticNameRecord],
) -> list[str]: ...
```

Every proposed surface requires stable context and intention. Deterministic candidate detection flags coordinate-shaped tokens such as a phase/part/task/step/milestone/wave/sprint/priority/ticket plus an ordinal or identifier, but never rejects solely from a word match. A flagged name is valid only when `planning_term_basis` is `implementation-governance` with a specific owning artifact or `durable-domain` with a specific domain concept. Existing private names may receive a bounded rename disposition. Existing public, persisted, generated, or externally consumed names require an explicit compatibility/migration disposition and cannot be silently preserved, aliased, or renamed.

### Exact-file plan validation

```python
REQUIRED_PLAN_SECTIONS = (
    "Global constraints",
    "Requirements and acceptance binding",
    "File map",
    "Semantic naming inventory",
    "Test-first slices and verification contracts",
    "Commands and expected evidence",
    "Review scopes and specialist predicates",
    "Commit boundaries",
    "Rollback and recovery",
    "Approval required to execute",
)

@dataclass(frozen=True)
class PlanBinding:
    program_id: str
    program_revision: int
    increment_id: str
    source_sha256: str
    program_sha256: str
    semantic_requirements_sha256: str
    workspace_path: str
    workspace_branch: str
    workspace_base_commit: str
    workspace_head_commit: str
    preparation_sha256: str

def validate_exact_file_plan(
    plan_path: Path,
    binding: PlanBinding,
    inspection: RepositoryInspection,
) -> list[str]: ...
def validate_preparation(
    program_root: Path,
    inspection: RepositoryInspection,
) -> list[str]: ...
```

The validator requires one H1, every bounded section, non-empty create/modify/preserve maps, explicit interfaces, test/alternative-verification slices, exact commands and expected evidence, review predicates, rollback/recovery domains, risks/exclusions/amendments, and a parseable semantic naming table. It checks the current program/source/semantic/workspace/head/preparation tuple and delegates program/state authority to accepted validators. It rejects missing, symlinked, stale, mismatched, or structurally incomplete plans. State/action binding remains the final production-write gate: a plan content pass cannot create write authority.

### CLI boundary

`repository_preparation.py` exposes:

- `inspect-repository --workspace <path> --base <commit>` — print one deterministic JSON inspection without file contents;
- `validate-preparation <program-root> --workspace <path> --base <commit>` — inspect current Git state and validate program/state/preparation authority;
- `validate-plan <program-root> --workspace <path> --base <commit> --preparation <path> --plan <path>` — validate the current bound plan and naming inventory.

Exit status is `0` for valid, `1` for repository/invariant failure, and `2` for usage error. Read-only Git failures, timeouts, unsupported status records, invalid UTF-8 control records, and malformed artifacts produce sorted concise issues, not tracebacks.

## File map

### Already created at this planning gate

- `implementation-programs/ISP-001/increments/INC-004/brief.md` — lean semantic invocation record.
- `implementation-programs/ISP-001/increments/INC-004/preparation.md` — current authority, repository observation, drift/evidence record, shape decision, and risks.
- `implementation-programs/ISP-001/increments/INC-004/exact-file-plan.md` — this frozen implementation contract.

### Create during authorized implementation

- `skills/implementing-staged-plans/references/repository-preparation.md` — focused operator procedure for inspection, ownership, drift, evidence, shaping, amendments, naming, plan validation, and hard stops.
- `skills/implementing-staged-plans/scripts/repository_preparation.py` — standard-library Git adapter, pure decisions/validators, and read-only CLI.
- `tests/test_repository_preparation.py` — real-Git parser tests, qualitative decision matrices, naming/plan validation, authority integration, and CLI tests.
- `tests/fixtures/repository-preparation/portable-archive-workspace/scenarios.json` — neutral scenario catalog covering dirty/untracked work, operations, base movement, failures, managed/reusable/dependency/assumption drift, and amendment/naming cases.
- `tests/fixtures/repository-preparation/portable-archive-workspace/evidence.json` — neutral valid/invalid evidence applicability records.
- `tests/fixtures/repository-preparation/portable-archive-workspace/exact-file-plan.md` — neutral complete plan used for structural, binding, and naming tests.
- `implementation-programs/ISP-001/increments/INC-004/execution-record.md` — observed RED/GREEN evidence, decisions, amendments, deviations, preservation checks, and state receipts.
- `implementation-programs/ISP-001/increments/INC-004/reviews/requirements.md` — accepted-scope and criterion review.
- `implementation-programs/ISP-001/increments/INC-004/reviews/architecture.md` — boundary, Git parsing, security, naming, and simplicity review.
- `implementation-programs/ISP-001/increments/INC-004/reviews/test-evidence.md` — fixture/test applicability and evidence-validity review.
- `implementation-programs/ISP-001/increments/INC-004/review-packet.md` — human diff handoff.
- `implementation-programs/ISP-001/increments/INC-004/handoff.md` — durable continuation record that stops before INC-005.

### Modify during authorized implementation

- `skills/implementing-staged-plans/SKILL.md` — add one narrow route from repository preparation/evidence/shaping/exact-plan work to the focused reference; do not duplicate the procedure.
- `skills/implementing-staged-plans/scripts/validate_package.py` — require the new regular non-symlink reference/script assets and include them in existing link/naming checks.
- `tests/test_package_validation.py` — extend valid fixtures and missing/symlinked-asset cases for the preparation assets.
- `tests/test_front_door_contract.py` — require the narrow repository-preparation route while preserving concision and all accepted gates.
- `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json` — add direct INC-004 implementation and verification evidence only; do not change semantic fields/digest.
- `implementation-programs/ISP-001/manifest.json` — advance current INC-004 artifact/status bindings from its accepted dirty bytes.
- `implementation-programs/ISP-001/state/status.json` — advance only authorized INC-004 lifecycle states and end at `awaiting-diff-approval`.
- `implementation-programs/ISP-001/state/approvals.jsonl` — append exact-file-plan and later diff approval only when explicitly supplied.
- `implementation-programs/ISP-001/state/action-authorizations.jsonl` — append bounded implementation/state-write authority only when explicitly supplied.

### Preserve unchanged

- `implementing-staged-plans-consolidated-design-plan-final.md` and the bootstrap runbook.
- `implementation-programs/ISP-001/source/**` for SOURCE-001 and SOURCE-002.
- `implementation-programs/ISP-001/program/implementation-program.md`, revision-2 `implementation-program.md`, and revision-1 `traceability.json`.
- every accepted INC-001 through INC-003 brief, plan, implementation, review, packet, handoff, and addendum artifact.
- `skills/implementing-staged-plans/scripts/program_authority.py`, `state_authority.py`, and their focused references/tests except for imports from their public interfaces in the new module/tests.
- all existing pressure evidence, `.gitignore`, `.codex-plugin/plugin.json`, and `skills/implementing-staged-plans/agents/openai.yaml`.

## Semantic naming inventory

| Proposed surface | Kind | Stable context | Intention | Planning-term basis | Compatibility disposition |
|---|---|---|---|---|---|
| `references/repository-preparation.md` | path | repository-backed implementation preparation | guide safe observation, evidence, shaping, and plan gates | `preparation` is a durable workflow responsibility | new private package asset |
| `scripts/repository_preparation.py` | path | repository-backed implementation preparation | implement read-only observation and decisions | `preparation` is a durable workflow responsibility | new private package asset |
| `RepositoryInspection` | symbol | current Git/workspace facts | bind one complete observed snapshot | none | new private symbol |
| `inspect_repository` | symbol/command | selected Git workspace | collect machine-readable current facts | none | new public script function; exact behavior tested |
| `DriftContext` / `DriftAssessment` | symbols | repository change relative to a prepared basis | classify qualitative drift and required action | none | new private data contracts |
| `classify_repository_drift` | symbol | current versus prepared repository | return benign, reconcilable, or invalidating disposition | none | new public script function; exact behavior tested |
| `EvidenceRecord` / `EvidenceDecision` | symbols | applicability-bound technical evidence | record source applicability and refresh decision | none | new private data contracts |
| `decide_evidence_refresh` | symbol | material/version-sensitive surface | choose refresh, bounded reuse, or stop | none | new public script function; exact behavior tested |
| `AmendmentProposal` / `AmendmentAssessment` | symbols | exact-plan change classification | prevent program changes hiding as technical changes | `amendment` is a durable workflow-governance concept | new private data contracts |
| `classify_plan_amendment` | symbol | current exact-file plan | distinguish correction, bounded amendment, program change, contradiction | `plan` and `amendment` name implemented governance artifacts | new public script function; exact behavior tested |
| `IncrementShape` / `assess_increment_shape` | symbols | current review unit | validate coherence, evidence, recovery, and safeguards | `increment` is a durable workflow-governance concept | new private/public script contracts |
| `SemanticNameRecord` | symbol/schema | proposed implementation surfaces | bind context, intention, basis, and compatibility | none | new private data contract |
| `validate_semantic_naming_inventory` | symbol | exact-file plan naming table | enforce contextual naming without a global blacklist | none | new public script function; exact behavior tested |
| `PlanBinding` / `validate_exact_file_plan` | symbols | just-in-time implementation contract | reject absent, stale, incomplete, or mismatched plans | `plan` names an implemented governance artifact | new public script contracts |
| `inspect-repository` | command | local Git workspace | emit one safe observation | none | new read-only CLI route |
| `validate-preparation` | command | current program/workspace preparation | verify authority and repository basis | `preparation` is a durable workflow responsibility | new read-only CLI route |
| `validate-plan` | command | current exact-file plan | verify structure, binding, overlap, and naming | `plan` names an implemented governance artifact | new read-only CLI route |
| `portable-archive-workspace` | fixture path | fictional archive-maintenance repository | exercise preparation without project identifiers | none | neutral test-only fixture |
| `scenarios.json` headings/IDs | fixture identifiers | observable repository conditions | describe dirty work, operations, evidence, and drift by behavior | no roadmap coordinates permitted | neutral test-only identifiers |
| `implementation-repository-inspection/v1` | schema identifier | persisted/serialized repository observation | version the inspection wire contract | none | new observable identifier; compatibility locked by tests |
| `implementation-evidence-record/v1` | schema identifier | applicability evidence | version evidence fields | `implementation` names the governance domain, not a roadmap stage | new observable identifier; compatibility locked by tests |
| INC-004 brief/preparation/plan/reviews/packet/handoff headings | governance headings | repository implementation governance | trace and review the approved increment | explicitly permitted implementation-governance artifacts | repository-only, not package-facing |

The touched package currently contains no existing roadmap-derived implementation name requiring rename or compatibility migration. `program_authority`, `state_authority`, and their schemas use durable implemented authority domains and remain valid. No package-facing surface will contain ISP/INC/source-plan coordinates.

## Test-first slices and verification contracts

### Task 0: Bind plan approval and implementation authority

**Files:**

- Modify: `implementation-programs/ISP-001/state/approvals.jsonl`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl`
- Modify: `implementation-programs/ISP-001/state/status.json`

**Produces:** One exact plan approval and one separate non-commit implementation authorization before package/test/fixture writes.

- [ ] Revalidate SOURCE-001/SOURCE-002, both program revisions, semantic digest, INC-003 accepted bindings, branch/base/head, active operation, full dirty inventory, brief digest, preparation digest, and this plan digest.
- [ ] Append one `implementation-approval/v1` `exact-file-plan-approval` event binding INC-004, the current tuple, and the explicit plan gate.
- [ ] Append one `implementation-action-authorization/v1` grant limited to the exact create/modify list, deterministic local verification, three separate non-independent reviews, and evidence-backed material remediation. Exclude commit and all external/consequential actions.
- [ ] Advance INC-004 only from `awaiting-plan-approval` to `authorized` through the accepted state authority, recording exact old/new status digests. Do not mark `implementing` before Task 1 RED is about to be written.

### Task 1: Define preparation behavior with neutral fixtures

**Files:**

- Create: `tests/test_repository_preparation.py`
- Create: the three files under `tests/fixtures/repository-preparation/portable-archive-workspace/`

**Interfaces:**

- Consumes: public accepted helpers from `program_authority.py` and `state_authority.py`.
- Produces: executable contracts for every dataclass, constant, decision function, validator, Git adapter, and CLI named above.

- [ ] Create `RepositoryPreparationFixture` using `TemporaryDirectory`, argument-vector Git commands, deterministic JSON/Markdown helpers, and a copied neutral scenario catalog. Configure only local test identity; never read or mutate global Git configuration.
- [ ] Add real-Git observation tests for staged modification, unstaged modification, untracked path, rename, conflict record parsing, path whitespace/newline handling, branch/head/root/git-dir/common-dir, base ancestry, detached head, Git failure, timeout, and sorted stable output.
- [ ] Add operation tests/fixtures for merge, rebase, cherry-pick, revert, sequencer, and bisect markers resolved through the repository's actual Git directory.
- [ ] Add drift/ownership matrix tests for benign unrelated changes, accepted dirty work, relevant reconcilable changes, provisional-assumption invalidation, managed/generated owner absence, protected overlap, head/base/branch movement, conflicts/operations, requirements/contracts, compatible/incompatible dependency drift, reusable-code discovery, and pre-existing baseline failures.
- [ ] Add evidence matrix tests for every material predicate, high/lower risk, current official availability, exact prior applicability, mismatch, access failure, and irrelevant installed surfaces.
- [ ] Add amendment/reviewability tests for minor corrections, every program dimension, contradiction, unsupported bounded labels, evidence/reversibility/user-decision gates, coherent shape, unrelated risk bundling, absent safeguards, missing verification/recovery, and invalid final repository.
- [ ] Add naming tests across every surface kind with invalid roadmap-only coordinates, valid implementation-governance ownership, valid durable domain concepts, ordinary semantic names, private rename, and public/persisted/generated/external compatibility requirements.
- [ ] Add exact-plan/state integration tests for absent/stale/symlinked/mismatched/incomplete plans, missing sections/table entries, current valid plan, plan digest mismatch in action binding, and a structurally valid plan that still lacks write authorization.
- [ ] Run `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_preparation -v` and record the intended import failure for missing `repository_preparation.py` before implementation.

### Task 2: Implement repository inspection, ownership, and drift

**Files:**

- Create: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `tests/test_repository_preparation.py` only when the harness, not an accepted contract, is wrong.

**Produces:** `RepositoryInspection`, the Git adapter/parser, `DriftContext`, `DriftAssessment`, `inspect_repository`, `classify_repository_drift`, and `validate_plan_overlap`.

- [ ] Import `RepositoryObservation` and accepted authority helpers without modifying or copying their implementations.
- [ ] Implement a private `_run_git` using `subprocess.run([...], shell=False, cwd=resolved_workspace, capture_output=True, check=False, timeout=...)`. Preserve byte output, scrub command errors to command name/exit status, and convert timeout/not-found to deterministic issues.
- [ ] Implement byte-oriented porcelain-v2 `-z` parsing for headers, ordinary, rename/copy, unmerged, untracked, and ignored records. Normalize only repository-relative paths after complete parsing; reject absolute/escaping paths and unsupported mandatory record kinds.
- [ ] Resolve Git/common directories and active-operation markers through `rev-parse`; confirm selected base object/ancestry; construct one immutable inspection.
- [ ] Implement exact path-set and binding comparisons, accepted-dirty ownership, managed/generated owner checks, qualitative precedence, stable reasons, and smallest required action.
- [ ] Run the observation/drift/ownership test classes. Expected: all Task 2 tests pass; evidence/amendment/naming/plan tests remain RED.

### Task 3: Implement evidence, amendment, shape, naming, and plan validation

**Files:**

- Modify: `skills/implementing-staged-plans/scripts/repository_preparation.py`
- Modify: `tests/test_repository_preparation.py` only when the harness, not an accepted contract, is wrong.

**Produces:** the evidence/amendment/shape/name/plan dataclasses, constants, pure decisions/validators, and CLI.

- [ ] Implement exact dataclass validation and immutable constant sets. Reject booleans where numeric types are expected, unknown enums/schemas, duplicate identifiers/surfaces, empty evidence/context/intention/basis details, and unsorted nondeterministic issue output.
- [ ] Implement evidence materiality/risk decisions exactly as specified. Validation records source locator, access date, version/configuration, claims, risk, reuse basis, and uncertainty without fetching or storing source content.
- [ ] Implement amendment precedence and reviewability checks. A program dimension or contradiction must override a caller's bounded label; do not score reviewability numerically.
- [ ] Implement contextual candidate detection and semantic inventory validation. Keep detection separate from disposition, require basis owner/detail for exceptions, and enforce compatibility analysis by origin/class.
- [ ] Implement the bounded Markdown section/table parser and exact tuple validation. Reuse managed-path/symlink checks and program/state validators. Verify state/action plan digest matching; never authorize a write from content validation alone.
- [ ] Implement the three read-only CLI routes with exit `0/1/2`, deterministic JSON/issues, no shell, and no file-content/secret output.
- [ ] Run `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_preparation -v`. Expected: all preparation tests pass.

### Task 4: Add the focused procedure and front-door route

**Files:**

- Create: `skills/implementing-staged-plans/references/repository-preparation.md`
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Modify: `tests/test_package_validation.py`
- Modify: `tests/test_front_door_contract.py`

**Produces:** A concise discoverable package route without duplicating preparation policy.

- [ ] Extend structural tests first. Require both preparation assets as regular non-symlink files, include the reference in link/naming scans, require one narrow front-door route, and retain existing metadata, concision, project-neutral naming, and authority contracts. Run the two structural modules and record RED naming the missing assets/route.
- [ ] Write `repository-preparation.md` in this order: prerequisites and current observation; accepted/user-work ownership; Git discovery; qualitative drift; baseline/reuse/evidence records; increment shape; amendment boundary; semantic naming inventory and compatibility; exact-plan contract; approval/action gate; validation commands; hard stops; bounded result.
- [ ] Add one front-door section routing repository inspection, evidence applicability, shaping, drift/amendment classification, and current exact-file planning to the new reference. Do not copy details or weaken universal gates.
- [ ] Extend required-asset validation through the existing tuple/helper pattern. Keep deterministic issue ordering and all previous package rules.
- [ ] Run the focused structural tests and package validation. Expected: all pass.

### Task 5: Exercise current preparation and record direct traceability evidence

**Files:**

- Modify: `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
- Modify: `implementation-programs/ISP-001/manifest.json`
- Modify: `implementation-programs/ISP-001/state/status.json`
- Modify: `implementation-programs/ISP-001/state/action-authorizations.jsonl` only for authorized transition records.
- Create/modify: `implementation-programs/ISP-001/increments/INC-004/execution-record.md`

**Produces:** Dogfood evidence from the real selected workspace without changing accepted semantics.

- [ ] Run `inspect-repository` and `validate-preparation` against the selected workspace; record exact branch/base/head, accepted dirty inventory, operation result, and drift disposition without persisting source content or secrets.
- [ ] Validate this INC-004 plan through `validate-plan`; prove a temporary one-byte plan change or head mismatch fails while the bound current bytes pass.
- [ ] Update only directly demonstrated INC-004 `implementation_evidence` and `verification_evidence` arrays. Recompute and assert semantic digest `151cbe...10f`; stop if it changes.
- [ ] Transition through `implementing` only at the first RED, then `reviewing` after freezing the complete non-commit diff. Use accepted atomic status writes and exact action grants; record every receipt and any inert append-only event if a later write fails.

### Task 6: Review, remediate, verify, and build the INC-004 packet

**Files:**

- Create: the INC-004 execution record, three reviews, review packet, and handoff listed above.
- Modify: revision-2 traceability, manifest, status, approvals, and action authorizations only as authorized.

**Produces:** A reviewed INC-004 diff at `awaiting-diff-approval`, with no INC-005 work.

- [ ] Freeze the proposed diff and record exact changed/untracked paths, accepted pre-existing paths, base/head, plan/preparation/source/program/semantic digests, and no-commit state.
- [ ] Run separate non-independent requirements, architecture, and test-evidence reviews. Requirements checks all six criteria and eight groups. Architecture checks Git parser safety, path ownership, pure/adapter boundaries, fail-closed behavior, evidence materiality, amendment precedence, naming context, simplicity, and later-increment exclusions. Test-evidence checks intended REDs, real/static fixture fidelity, every qualitative matrix, plan/state integration, CLI results, and static-versus-runtime limits. Persist each raw review before reconciliation and label assurance reduced/non-independent.
- [ ] Repair only evidence-backed material INC-004 findings. Record requirement/invariant, location, impact, confidence, smallest repair, and affected reruns. Stop for program amendment if remediation changes scope, requirements, acceptance, protected contracts, security/privacy, risk posture, dependencies, sequencing, review cadence, or public behavior.
- [ ] Run fresh final verification once on the coherent final tree using the exact commands below.
- [ ] Build the review packet with outcome, criterion mapping, files/interfaces, inspection/drift/evidence/amendment/naming decisions, RED/GREEN/final results, fixture coverage, reviews/findings/repairs, deviations, semantic digest preservation, risks/limits, rollback/recovery, workspace/base/head, no-commit status, current state, and next legal action.
- [ ] End at `awaiting-diff-approval`. Do not accept the diff, begin INC-005, close the program, or perform any consequential action.

## Commands and expected evidence

Focused RED/GREEN and structural commands:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_preparation -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_package_validation tests.test_front_door_contract -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Expected: the first invocation records the missing-module RED before implementation, focused classes turn green slice by slice, structural tests first fail for missing preparation assets/route, then all pass.

Fresh final verification:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-preparation implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-plan implementation-programs/ISP-001 --workspace /Users/CoveMB/Code/CoveMB/implementation-plugin --base f14449b8808574c720927aedab5b64871cc63858 --preparation implementation-programs/ISP-001/increments/INC-004/preparation.md --plan implementation-programs/ISP-001/increments/INC-004/exact-file-plan.md
rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans
rtk git diff --check
rtk git status --porcelain=v2 --branch
```

`validate-preparation` performs fresh Git inspection and delegates the resulting complete observation to accepted state-authority validation, so the verification command does not duplicate a manually assembled path list. Expected: full tests, package/program/state/preparation/plan/skill validation, whitespace, and bounded status checks pass; no command claims external integration, deployment, publication, accessibility, or production behavior.

## Review scopes and specialist predicates

- Required: requirements/scope, architecture/boundaries/semantic naming/simplicity, and test/evidence validity as three separately persisted passes.
- Review mode: controller self-review, explicitly non-independent with reduced assurance. No subagent or external evaluator is authorized by this plan.
- Security/privacy predicate: bounded internal review is required because the module executes Git and handles repository paths. Check `shell=False`, argument separation, timeout, path containment, error redaction, no source/environment output, and no mutation.
- Compatibility predicate: bounded internal review is required for observable CLI/schema names and Git-format support. Check local Git 2.50.1, documented porcelain v2/rev-parse behavior, unknown-record failure, and schema/exit-code tests.
- No data/migration, accessibility, deployment/platform infrastructure, concurrency/distributed state, payments, performance, or provider-state specialist review is triggered by the planned read-only local module.

## Commit boundaries

No commit is authorized. Keep these as logical review slices only:

1. `test: define repository preparation contracts` — Task 1 tests and neutral fixtures.
2. `feat: inspect repository state and classify drift` — Task 2 Git adapter, ownership, drift, and tests.
3. `feat: validate evidence and exact file plans` — Task 3 evidence/amendment/shape/naming/plan/CLI and tests.
4. `feat: route repository preparation workflow` — Task 4 reference, front door, package validator, and structural tests.
5. `docs: record repository preparation evidence` — Tasks 5-6 traceability/governance, reviews, packet, handoff, and final state.

Do not stage or commit these slices unless a later separate authorization names the exact local commit action and boundaries.

## Rollback and recovery

- The new package module and CLI are read-only. No persistent data, provider, marketplace, installation, deployment, production, or external state is touched.
- Before any commit, recovery is limited to editing the named INC-004 files from their current bytes. Never reset, clean, stash, restore, overwrite, or discard accepted/user work.
- Governance files use accepted per-file compare-and-swap/append behavior. If an approval/authorization append succeeds but a later status write fails, preserve the inert event, report the partial update, and retry only from newly observed exact digests.
- Never roll back immutable sources, approved program revisions, accepted packets/handoffs, approvals, or authorizations. Corrections use addenda, revocation/supersession events, or a new program revision as applicable.
- Any future commit reversion would require separate authorization and target only exact INC-004 commits. A Git revert would not represent recovery of external state, though no external state is planned here.
- The module does not claim multi-file atomicity, hostile-concurrency locking, remote freshness, provider integration, or exhaustive support for undocumented future Git operation formats.

## Approval required to execute

The next legal approval must bind ISP-001 revision 2, SOURCE-002/program/semantic digests, accepted INC-003 evidence, `main`, selected base, current head and exact dirty inventory after these planning writes, the INC-004 brief digest, preparation digest, and this exact-file-plan digest.

Separate implementation authorization must permit only:

1. the named preparation reference/module/test/neutral-fixture, front-door/package-validator, direct traceability-evidence, and INC-004 review/handoff writes;
2. read-only Git observation, deterministic local verification, and accepted atomic lifecycle/governance writes;
3. three separate non-independent review passes and evidence-backed remediation limited to material INC-004 findings;
4. no commits unless separately and explicitly added later.

It must preserve all prohibitions on INC-005, subagent/evaluator dispatch, installation, marketplace change, staging/commit, push, pull request, publication, release, deployment, migration, destructive action, provider mutation, and consequential external state.
