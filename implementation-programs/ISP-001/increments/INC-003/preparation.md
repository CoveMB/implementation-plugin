# INC-003 Preparation

## Authority and boundary

- Program: ISP-001 revision 2.
- Source: SOURCE-002, SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program Markdown: SHA-256 `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Accepted traceability artifact: SHA-256 `4aecc6614164f43d039bf472a4244a73ecb40050bc3632a0aa60a3cfe7b10f6b`.
- Accepted atomic semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Approval mode: `approval:full-increment`.
- Current authorized work: revalidate persisted authority and prepare the INC-003 brief, repository-informed preparation, and exact-file plan.
- Mandatory stop: explicit approval of the exact-file plan plus separate bounded implementation/action authorization.
- Excluded: INC-003 implementation, commit, evaluator or subagent dispatch, INC-004, installation, marketplace change, push, pull request, publication, release, deployment, migration, destructive action, provider mutation, or other consequential external state.

The implemented front door and program-authority procedure are available and passed current validation. The state/approval/action-authorization procedure belongs to INC-003 and is not yet implemented, so this preparation uses the approved repository records as a manual safeguard and makes no premature mechanical-enforcement claim.

## Repository revalidation

- Repository/workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin`.
- Branch: `main`.
- Current and accepted INC-002 head at preparation: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Selected continuation base: `f14449b8808574c720927aedab5b64871cc63858`; verified ancestor of the preparation head.
- Git directory and common directory are both `.git`; this is the selected main checkout, not a linked worktree.
- Active Git operation or conflict: none reported by `git status --porcelain=v2 --branch`.
- Pre-planning staged paths: none.
- Pre-planning modified paths: `implementation-programs/ISP-001/manifest.json`, revision-2 `traceability.json`, `state/approvals.jsonl`, `state/status.json`, and `tests/test_program_authority.py`.
- Pre-planning untracked path: `implementation-programs/ISP-001/increments/INC-002/handoff-addendum.md`.
- Those six paths exactly form the accepted but uncommitted INC-002 semantic-acceptance and diff-acceptance state. They are preserved as user-owned accepted work. INC-003 planning may extend only the manifest and status from their current bytes and append one preparation authorization; it must not rewrite, discard, stage, or commit any accepted path.
- Remote refs were not fetched because this local planning gate does not depend on remote freshness.

## Accepted authority revalidation

- SOURCE-001: `3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8` — match.
- SOURCE-002: `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57` — match.
- Revision-1 program: `ec94caa50ff8918e242170220816e92ea2c48b36cd6b2e19c531d37aea8d0324` — match.
- Revision-1 traceability: `16d5001a22a1e72c5328a308c03b0866bbc48fb0d78c94b3b1d29919805a3f5a` — match.
- Accepted INC-001 review packet and handoff: `6534809d9ceda16b9fa457b56af0128f70ebe5640f201fadaf47d3168cd7e031` and `763b0963c81f2663188bbc591e15c8930f18eba6a48d932c49913d56f8e0f061` — match.
- Accepted INC-002 plan, review packet, original handoff, and acceptance addendum: `955f8da03250aa5d10c068ffd1f617673dc556b4e9612daffdca78d57a724641`, `3aaf4b8d983809dfc06ba804c655c3134965ec4ec7ef55c7f77c3b4b7f4d9e0e`, `cb5b395c230498c4010c00af2261abf5260dfa140ece5ab2ed80f6b73a6c52e8`, and `f0d197942295a5e06faf985649dc7fed4c271f063e78e8c346b4a47ae9ab8637` — match.
- `APR-010` binds the accepted semantic digest and `APR-011` binds the accepted INC-002 diff and current traceability artifact.
- `program_authority.py validate-program implementation-programs/ISP-001` — PASS with complete accepted authority.

## Fresh preparation checks

- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — PASS, 49 tests.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001` — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans` — PASS.
- `rtk git diff --check` — PASS.

These checks establish current structural, authority, and deterministic-test baselines only. They do not establish INC-003 transition, approval-mode, workspace-selection, atomic-update, or action-authorization behavior.

## Canonical source locations

The plan is grounded in these SOURCE-002 sections:

- operational, safety, and action authority: sections 4.3 and 4.5, lines 113-133;
- explicit state transitions and separate action authority: section 5, lines 135-156;
- entry routing and state/approval/action engine: sections 7.1 and 7.4, lines 227-273;
- workspace-selection boundary: section 7.5, lines 275-289;
- durable artifact invariants: section 10.1, lines 610-621;
- complete program and increment state models: section 11, lines 640-684;
- five-mode matrix and universal gates: section 12, lines 686-719;
- workspace selection and increment invocation: sections 13.2-13.3, lines 738-753;
- consequential-action authority table: section 20, lines 1003-1025;
- state/approval validation contract: section 23.3, lines 1102-1112;
- INC-003 outcome and key evidence: section 24, lines 1214-1218;
- design-wide acceptance and approved defaults: sections 25-26, lines 1254-1300;
- state-machinery minimization risk: section 27.5, lines 1320-1322.

Atomic traceability allocates 388 requirements to INC-003 across the eight advanced groups. Many are intentionally cross-increment obligations. Implementation evidence must be added only to the directly demonstrated state/approval/workspace/action contracts; no bulk disposition or semantic-field change is allowed.

## Current implementation and reusable patterns

- `skills/implementing-staged-plans/SKILL.md` is a 91-line front door. It should gain one narrow route to a focused state-authority procedure rather than absorb the procedure.
- `program_authority.py` already exposes project-neutral `sha256_file`, `load_json_object`, `load_json_lines`, `resolve_managed_path`, and `validate_program_authority` functions. INC-003 can reuse these without modifying the accepted module.
- `validate_package.py` already requires focused reference/script assets and scans package-facing Markdown for broken links and roadmap leakage. The state assets should extend that tuple and existing tests.
- `tests/test_program_authority.py` establishes `TemporaryDirectory`, deterministic JSON, import-by-path, fail-closed issue lists, and CLI status conventions.
- Existing status, manifest, workspace, approval, and authorization records provide a real migration fixture, but accepted historical records predate the new mechanical contract. The new engine must not rewrite history or claim legacy events independently grant future actions.
- The repository still has no third-party runtime dependency, package manager, CI workflow, schema library, database, or concurrency framework.

## Current official evidence

Accessed 2026-08-08 from Python 3.14 documentation:

- `os.replace`: `https://docs.python.org/3/library/os.html#os.replace`. A successful same-filesystem replacement is atomic on POSIX; the destination is replaced, so the implementation must combine it with a caller-supplied expected digest and symlink checks.
- `os.fsync`: `https://docs.python.org/3/library/os.html#os.fsync`. Buffered files must be flushed before `fsync`; the plan requires both before replacement.
- `tempfile.NamedTemporaryFile`: `https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile`. A visible, securely created same-directory temporary name supports controlled cleanup and replacement without `mktemp` races.
- `pathlib.Path.resolve`: `https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.resolve`. It resolves symlinks and eliminates `..`; current managed-path checks remain applicable.

No dependency installation or version change is justified. The plan retains Python standard-library code and the current `unittest` harness.

## Design options and decision

### Recommended: one focused state-authority module

Add `state_authority.py` plus `state-authorization.md`. Keep transition matrices, approval policies, binding validation, workspace selection, authorization decisions, atomic status/log writes, and a small CLI in one cohesive module. Reuse the accepted program-authority loader and path/digest functions. This preserves a clear authority boundary, avoids changing the 921-line accepted program-authority implementation, and remains small enough to test exhaustively.

### Rejected: extend `program_authority.py`

This would avoid one import but mix immutable source/program approval with mutable lifecycle and action authorization. It would enlarge an already substantial accepted module, raise regression risk for INC-002, and obscure the separate-authority invariant.

### Rejected: declarative schemas plus a generic workflow engine

Separate JSON schema files and a generic state-machine abstraction could encode the matrices, but the repository has no schema dependency or multiple workflows requiring that abstraction. It would add files and indirection before evidence justifies them. Plain immutable constants, typed records, and focused validators are simpler and sufficient.

## Repository-informed design

1. Keep persisted `implementation-program-status/v1`; model program and increment states as separate validated fields and typed views rather than introduce premature schema migration.
2. Encode complete adjacency sets for the seven program states and fourteen increment states. A blocked state may resume only to its recorded resume target. Starting a different increment is a separate operation from a same-increment state transition.
3. Encode the five approval modes as immutable data, not branches scattered through the workflow. The policy reports plan pause, interruption predicates, diff acceptance, and continuation separately.
4. Validate every approval against source, program revision/digest, semantic digest where relevant, workspace path/branch/base/head, scope, mode, increment, brief digest, plan digest, and packet/verification evidence required by the transition.
5. Store a digest-bound brief binding in controlling state. INC-003 validates identity and freshness; semantic brief generation/content validation remains INC-007.
6. Record workspace selection from a caller-supplied repository observation. INC-003 validates exact identity/path/branch/base and records pre-existing work. Git observation and qualitative drift classification remain INC-004.
7. Require a distinct action authorization for each requested write/evaluation/commit/effect class. Approval mode can never synthesize an authorization.
8. Replace mutable status and append-only JSONL logs one file at a time through same-directory temporary files, file flush/`fsync`, expected-digest compare-and-swap, and `os.replace`. Each new status embeds the prior status digest and schema version. Do not claim multi-file atomicity or protection from hostile concurrent writers.
9. Build a fictional portable-archive state overlay on the accepted neutral program-authority fixture. Reusable files, functions, commands, and fixture content remain free of ISP/INC roadmap names.
10. Preserve later boundaries: no repository drift classifier (INC-004), execution/amendment/commit controller (INC-005), review-packet validator (INC-006), brief generator/continuity/closure engine (INC-007), or crash/schema-evolution pilot (INC-008).

## Material risks and controls

- **State-machine gaps:** an omitted or accidental edge could permit an unsafe transition. Control: enumerate every state-pair test and test conditional gates separately.
- **Approval/action conflation:** an autonomy mode could accidentally grant an external action. Control: a mode-policy function has no authorization output; every action decision reads the separate authorization log.
- **Stale binding:** a valid approval for another head, workspace, plan, or brief could be reused. Control: exact binding comparison and negative mutation tests for every field.
- **Atomic-write overclaim:** rename atomicity does not create a multi-file transaction or hostile-concurrency lock. Control: compare-and-swap digest, per-file receipts, failure tests, safe ordering, and explicit residual limitation.
- **Legacy history:** accepted events do not have the new exact schema. Control: preserve them as historical evidence, never treat a schema-less event as a future mechanical grant, and append new versioned events for INC-003.
- **Workspace overlap:** manifest/status are already accepted dirty paths. Control: patch current bytes only, record prior digests, and never reset, stash, stage, or commit them during planning.
- **Scope leakage:** implementing Git drift, packet, closure, or continuation behavior now would steal later increments. Control: caller-supplied observations and digest bindings only.

## Planning conclusion

INC-003 remains one coherent increment. State transitions, approval-mode interpretation, workspace selection, approval freshness, atomic status persistence, and action authorization share one lifecycle trust boundary and one exhaustive matrix-based verification contract. Splitting them would leave an intermediate engine that could transition state without enforcing one of its authority inputs.
