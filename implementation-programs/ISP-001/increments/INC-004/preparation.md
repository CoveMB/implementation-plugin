# INC-004 Preparation

## Authority and boundary

- Program: ISP-001 revision 2.
- Source: SOURCE-002, SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program Markdown: SHA-256 `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Accepted traceability artifact: SHA-256 `eb0ab811543ad3e9da15373462bd9fe661d0085f9bb4f8e57ea1c002bef349d6`.
- Accepted atomic semantic digest: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Latest accepted increment: INC-003, approval event `APR-013`, authorization `AUTH-009`.
- Approval mode: `approval:full-increment`.
- Current authorized work: revalidate persisted authority and repository truth; prepare the INC-004 brief, preparation record, and exact-file plan; extend current governance bindings from their accepted bytes; run read-only and deterministic local checks.
- Mandatory stop: explicit approval of the exact-file plan plus separate bounded implementation/action authorization.
- Excluded: INC-004 package implementation, evaluator or subagent dispatch, commit, INC-005, installation, marketplace change, push, pull request, publication, release, deployment, migration, destructive action, provider mutation, or other consequential external state.

The front door, program-authority procedure, and state/action-authority procedure are implemented and pass current validation. Git discovery, drift classification, evidence applicability, increment shaping, and semantic exact-plan validation belong to INC-004 and are therefore manual safeguards at this preparation gate. The accepted state module can validate a caller-supplied observation but does not mechanically start a different increment identity; the governance rollover to INC-004 is recorded as a disclosed manual safeguard under the renewed one-increment user authority.

## Repository revalidation

- Repository and selected workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin`.
- Branch: `main`.
- Current and accepted INC-003 head: `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Selected continuation base: `f14449b8808574c720927aedab5b64871cc63858`; `git merge-base --is-ancestor` passed.
- Local Git: `2.50.1 (Apple Git-155)`; Python: `3.14.6`; platform: `Darwin 25.5.0 arm64`.
- This is the selected main checkout. No remote is configured, and no fetch was run because remote freshness cannot affect this local planning gate.
- `git status --porcelain=v2 --branch` reported no staged or conflicted paths and no detached head.
- No merge, rebase, cherry-pick, revert, bisect, or sequencer marker was found during preparation.
- Pre-planning modified paths:
  - `implementation-programs/ISP-001/manifest.json`
  - `implementation-programs/ISP-001/program/revisions/revision-2/traceability.json`
  - `implementation-programs/ISP-001/state/action-authorizations.jsonl`
  - `implementation-programs/ISP-001/state/approvals.jsonl`
  - `implementation-programs/ISP-001/state/status.json`
  - `skills/implementing-staged-plans/SKILL.md`
  - `skills/implementing-staged-plans/scripts/validate_package.py`
  - `tests/test_front_door_contract.py`
  - `tests/test_package_validation.py`
  - `tests/test_program_authority.py`
- Pre-planning untracked paths:
  - `implementation-programs/ISP-001/increments/INC-002/handoff-addendum.md`
  - `implementation-programs/ISP-001/increments/INC-003/`
  - `skills/implementing-staged-plans/references/state-authorization.md`
  - `skills/implementing-staged-plans/scripts/state_authority.py`
  - `tests/fixtures/state-authorization/`
  - `tests/test_state_authority.py`
- These paths match the accepted, uncommitted INC-002/INC-003 surface described by the INC-003 handoff, acceptance addendum, packet, and bound approval. No contrary user work was observed. INC-004 planning may create only its three governance artifacts, extend `manifest.json` and `status.json` from current bytes, and append one preparation authorization. It must not rewrite, stage, commit, discard, or reconstruct any accepted path.

## Accepted authority revalidation

- SOURCE-001: `3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8` — match.
- SOURCE-002: `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57` — match.
- Revision-1 program: `ec94caa50ff8918e242170220816e92ea2c48b36cd6b2e19c531d37aea8d0324` — match.
- Revision-1 traceability: `16d5001a22a1e72c5328a308c03b0866bbc48fb0d78c94b3b1d29919805a3f5a` — match.
- Accepted INC-001 packet and handoff: `6534809d9ceda16b9fa457b56af0128f70ebe5640f201fadaf47d3168cd7e031` and `763b0963c81f2663188bbc591e15c8930f18eba6a48d932c49913d56f8e0f061` — match.
- Accepted INC-002 plan, packet, handoff, and addendum: `955f8da03250aa5d10c068ffd1f617673dc556b4e9612daffdca78d57a724641`, `3aaf4b8d983809dfc06ba804c655c3134965ec4ec7ef55c7f77c3b4b7f4d9e0e`, `cb5b395c230498c4010c00af2261abf5260dfa140ece5ab2ed80f6b73a6c52e8`, and `f0d197942295a5e06faf985649dc7fed4c271f063e78e8c346b4a47ae9ab8637` — match.
- Accepted INC-003 plan, packet, original handoff, and acceptance addendum: `8db40db410f5d884dad1a611558415f1c6caa4e857a02bdd2cb6facaf6a01a6d`, `677eaf7bb8603b9d8f53c0f00c5db919007a9d528f1acbb80fd2d2fd93a28f24`, `b92c38746860a1577d460cd4af4b5b6488fd838f33a2d8d0e973a04f9a476f4d`, and `ca32d89adbb5abf6f053990f3d78cd6bf7aa7662fbb7e87eba2d61382e90f4ca` — match.
- `APR-013` exactly binds the reviewed INC-003 diff; `AUTH-009` bounds its acceptance-record writes.
- `program_authority.py validate-program implementation-programs/ISP-001` — PASS.
- `state_authority.py validate-state` with the exact current repository observation — PASS.

## Drift classification at preparation

- Workspace identity, branch, selected base, head, accepted artifact digests, and dirty path inventory agree with the accepted handoff and persisted state.
- There is no active operation, conflict, base movement, dependency/version change, or newly overlapping user path.
- Classification: **benign**, with accepted-continuity context. The dirty tree is material but accepted and already bound, so it is preserved and carried forward rather than treated as clean or discarded.
- The repository has no package manager, dependency manifest, lockfile, CI workflow, provider binding, database, generated-code convention, or application-owned runtime path. There is therefore no dependency or provider evidence refresh beyond the Git/Python surfaces used by the proposed preparation module.
- Any new overlap, head movement, active Git operation, conflict, incompatible dependency change, protected-contract change, or changed source/program binding before implementation invalidates this plan and requires renewed classification.

## Fresh preparation checks

- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — PASS, 72 tests.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001` — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/state_authority.py validate-state ...` with every current modified and untracked path — PASS.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans` — PASS.
- `rtk git diff --check` — PASS.

These checks establish the accepted structural, authority, lifecycle, and deterministic-test baseline only. They do not establish the not-yet-implemented Git observation, drift, evidence, amendment, reviewability, naming-inventory, or exact-plan behavior assigned to INC-004.

## Canonical source locations

The plan is grounded in these SOURCE-002 sections:

- workspace and user-work protection: section 7.5, lines 275-289;
- preparation and evidence registry: section 7.6, lines 291-304;
- increment shaping and exact-file plans: section 7.7, lines 306-334;
- execution reuse and naming boundary: section 7.8, lines 336-351;
- amendment and drift classification: section 7.9, lines 353-364;
- agent discretion and program-amendment boundary: sections 8.5 and 9.1-9.3, lines 458-556;
- durable artifacts and stale-binding protection: section 10, lines 560-621;
- increment preparation sequence: section 13.4, lines 755-770;
- amendment, drift, hard-stop, and evidence policy: sections 14-17, lines 832-918;
- repository fixture coverage: section 23.5, lines 1125-1140;
- INC-004 outcome and key evidence: section 24, lines 1219-1223;
- design-wide acceptance, defaults, and risks: sections 25-27, lines 1254-1339.

Revision-2 traceability allocates 433 atomic requirements to INC-004 across the eight named groups: REQ-AUTHORITY 123, REQ-DEFAULTS 17, REQ-DESIGN-RISKS 20, REQ-EVIDENCE-PLANNING 122, REQ-SEMANTIC-NAMING 51, REQ-SEQUENCE 12, REQ-VALIDATION 66, and REQ-WORKSPACE-DRIFT 22. Many are cross-increment obligations. Implementation evidence must be added only to records directly demonstrated by INC-004; the accepted semantic fields and digest remain unchanged.

## Current implementation and reusable patterns

- `state_authority.RepositoryObservation` is the accepted observation contract. INC-004 should reuse it rather than define a competing staged/modified/untracked/conflicted record.
- `program_authority.py` provides accepted `sha256_file`, JSON/JSONL loaders, managed-path resolution, and complete program validation.
- `state_authority.py` provides exact state/brief/plan/workspace validation, action-binding decisions, and atomic JSON/JSONL persistence. INC-004 should consume these rather than duplicate authority or mutation logic.
- `validate_package.py` already requires focused reference/script assets and performs resolved-link and package-facing naming checks. The INC-004 assets should extend its existing required-asset tuple.
- `tests/test_program_authority.py` and `tests/test_state_authority.py` establish temporary-directory fixtures, import-by-path, deterministic JSON, explicit Git-free observation injection, fail-closed issue lists, and CLI exit conventions.
- The accepted modules are 921 and 1,333 lines. Adding INC-004 behavior to either would mix immutable program authority or mutable lifecycle state with repository/evidence/planning policy and raise regression risk.
- The repository still has no third-party runtime dependency or schema library. Standard-library Python and `unittest` remain the smallest repository-native choice.

## Current official evidence

Accessed 2026-08-08 local time:

- Git status documentation: `https://git-scm.com/docs/git-status`. Porcelain v2 provides detailed, configuration-stable changed-item records and extensible branch headers; `-z` supplies unquoted NUL-delimited paths suitable for machine parsing.
- Git rev-parse documentation: `https://git-scm.com/docs/git-rev-parse`. `--show-toplevel`, `--git-dir`, `--git-common-dir`, and `--git-path` resolve repository and operation-administration paths without assuming `.git` is a directory in the worktree.
- Python 3.14 subprocess documentation: `https://docs.python.org/3/library/subprocess.html`. `subprocess.run` is the recommended bounded interface; argument arrays, captured output, explicit `cwd`, timeouts, and return-code handling avoid shell interpolation and hanging discovery.
- Python 3.14 pathlib documentation: `https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.resolve`. `Path.resolve()` removes `..` and resolves symlinks before containment comparisons.

The locally installed Git 2.50.1 supports the selected porcelain-v2 and rev-parse options. No dependency upgrade, network-backed runtime behavior, or nonstandard library is justified. Active-operation marker detection remains a bounded compatibility surface and must be tested through `git rev-parse --git-path` plus explicit merge, rebase, cherry-pick, revert, sequencer, and bisect cases.

## Design options and decision

### Recommended: one focused repository-preparation module

Add `repository_preparation.py` and `repository-preparation.md`. Keep Git observation and parsing, qualitative drift, evidence applicability, amendment classification, reviewability, semantic naming inventory, and exact-plan validation in one cohesive preparation boundary. Reuse the accepted authority types/functions. The module stays read-only; existing state authority remains the only package mutation boundary.

### Rejected: extend `state_authority.py`

This would reuse its observation type without an import, but would mix current lifecycle authorization and atomic persistence with Git execution, external-evidence policy, naming, and plan semantics. It would enlarge an already substantial accepted module and blur which facts are observed versus authorized.

### Rejected: split into Git, evidence, naming, and plan modules with standalone schemas

The responsibilities could be separated physically, but the repository has one implementation and one test module per accepted authority boundary and no schema framework. Four modules plus schema assets would increase package surface and cross-module binding work without a second consumer. A later demonstrated size or reuse pressure can justify a bounded split.

## Repository-informed increment shape

INC-004 remains one coherent review unit. Its six acceptance criteria share one trust boundary: current repository and evidence must be transformed into a safe, reviewable, semantically named exact-file plan before implementation authorization can match that plan. Splitting before the planning validator exists would leave either repository facts without a plan gate or a plan gate without trustworthy facts.

The internal implementation is divided into independently testable slices:

1. neutral fixture contracts and observed RED;
2. Git observation plus user-work/drift classification;
3. evidence, amendment, reviewability, semantic naming, and exact-plan validation;
4. focused operator procedure and front-door/package integration;
5. current-program evidence integration, review, remediation, and final verification.

No program amendment is required. The plan replaces the source plan's provisional multi-reference/schema illustration with one repository-native module/reference/test boundary while preserving outcome, acceptance, risk posture, dependencies, sequence, review cadence, and public behavior.

## Material risks and controls

- **Path parsing:** newline-delimited status output can misparse unusual filenames. Control: porcelain v2 with `-z`, byte-oriented parsing, rename/unmerged/untracked fixtures, and deterministic sorting only after complete parsing.
- **Active-operation detection:** Git operation state spans refs and administration directories. Control: resolve every marker through `git rev-parse --git-path`, cover merge/rebase/cherry-pick/revert/sequencer/bisect, and fail closed on ambiguous simultaneous markers.
- **User-work overlap:** an exact plan could normalize accepted dirty work into the increment. Control: compare proposed operations with recorded pre-existing and accepted paths; require an explicit ownership/disposition for every overlap and stop on ambiguity.
- **Over-classification:** treating every change as base-invalidating would make the workflow unusable. Control: qualitative benign/reconcilable/base-invalidating rules with paired fixtures and explicit relevant/protected/dependency inputs.
- **Evidence performativity:** refreshing every installed surface would add noise. Control: exact materiality predicates, high-risk stop behavior, and version/configuration/assumption matching for lower-risk reuse.
- **Amendment concealment:** a technical label could hide changed scope or obligations. Control: program dimensions dominate classification regardless of proposed label; tests cross every protected dimension.
- **Naming blacklist:** a token denylist would reject valid governance/domain uses and miss semantic leaks. Control: candidate detection plus context, intention, owner, governance/durable-domain basis, and compatibility analysis.
- **Plan-parser brittleness:** Markdown structure can drift. Control: one bounded required-heading/table contract, clear parse failures, no prose inference, and neutral valid/invalid fixtures.
- **Scope leakage:** execution, commit/recovery orchestration, review-packet validation, prompt generation, closure, and integrated pressure remain later increments. Control: read-only INC-004 module and explicit file/test exclusions.

## Planning conclusion

Repository truth supports the approved INC-004 outcome without changing program semantics. The selected design is standard-library, project-neutral, reversible, and consistent with accepted package boundaries. The exact-file plan is ready for digest binding and human approval; no production/package implementation may begin before that approval and a separate action authorization.
