# INC-008 Execution Record

## Frozen authority tuple

- Source: SOURCE-002, `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Program: ISP-001 revision 2, `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`.
- Semantic requirements: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`.
- Brief: `07a21014d60f3e84b8ac59c1f5d9a9db3bc6640600463d1c28ac2f6bfa3a44f1`.
- Preparation: `5c09c6c91470ecaae5fe95821f52d924d4a4efb28248041b6d112274cc39f070`.
- Exact plan: `599932f1bf845e66149830ed7749a606eaf0775908b76368aba3a99bb53ea8b4`.
- Plan approval: APR-022.
- Local non-commit implementation authorization: AUTH-023.
- Separate five-run synthetic evaluation authorization: AUTH-025, replacing the unsupported action names in AUTH-024 without broadening scope.
- Workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin`, branch `main`, base `f14449b8808574c720927aedab5b64871cc63858`, head `53edb8fad2008c7d35b6c17dbb973b24022947fd`.
- Commit and staging authority: false.
- ISP-001 closure reconciliation or closure authority: false.

## Accepted baseline

- Completed before implementation writes: 2026-08-09T23:37:00Z.
- Full suite: 209 tests passed in 12.18 seconds.
- Package, program, preparation, exact-plan, accepted continuity bundle, accepted review bundle, skill, JSON, and diff-hygiene validation passed.
- No remote is configured; no fetch was run.
- Current dirty inventory is the accepted uncommitted ISP-001 implementation through INC-007 plus the planned INC-008 governance and test path. No staged, conflicted, active-operation, or unrelated overlapping path was observed.

## Test-first execution evidence

### exact-navigation-adoption

- Purpose: allow an accepted rollover to adopt both pre-existing, validated, byte-exact navigation artifacts without rewriting them, while retaining create-new and fail-closed behavior.
- Test written before production repair: `tests/test_continuity_closure.py::RolloverTests.test_rollover_adopts_exact_existing_navigation_without_rewrite`.
- RED command: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_continuity_closure.RolloverTests.test_rollover_adopts_exact_existing_navigation_without_rewrite -v`.
- Expected failure: the accepted implementation rejects exact existing navigation with `rollover navigation target already exists`.
- Observed at: 2026-08-09T23:42:27Z.
- Exit: 1.
- Observed failure: `ValueError: rollover navigation target already exists` at `continuity_closure.py:743`.
- Intended-reason match: yes. The test reached the existing target guard after valid records and before controlling writes; this is the repository-demonstrated missing behavior, not a harness/import failure.
- RED preceded production change: yes.
- Recovery constraint: mixed presence, changed bytes, symlinks, unsafe parents, or controlling digest drift must fail before any write. Exact existing navigation must keep its inode and digest; only manifest and status replacements may appear as completed writes.
- GREEN evidence: `RolloverTests` passed 9 tests; the complete continuity owner passed 37 tests. Exact existing navigation kept its inode and digest, mixed/changed/symlinked targets failed before writes, and interruption receipts named only controlling files actually replaced.

### isolated-evaluator-environment

- Review finding: `F-008-001` demonstrated that the evaluator child inherited the complete parent environment through `os.environ.copy()` despite the synthetic minimum-context contract.
- RED command: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_integrated_pressure.InterruptionAndAtomicityTests.test_evaluator_environment_excludes_unrelated_parent_values -v`.
- Expected and observed failure: `AttributeError: module integrated_pressure_support has no attribute build_isolated_evaluator_environment`.
- Exit: 1; intended-reason match: yes; RED preceded the harness repair.
- Repair: add an explicit isolated environment containing only disposable home, executable path, temporary directory, locale, and optional certificate paths; stop copying unrelated parent values.
- GREEN evidence: the focused secret-exclusion regression passed 1 test. The five already-persisted outputs were inspected and contain no credential or private-source value; successful scenarios were not rerun or overwritten.

## Integrated pilot and pressure evidence

- The deterministic integrated subset passed 8 tests before fresh output verdicting. It exercised the neutral nine-requirement disposable repository, accepted owner composition, bounded amendment, review and acceptance, handoff/resume, pilot-only reconciliation/closure, denied-then-exact hypothetical draft-PR decision, atomic status/append failure, current/unsupported schemas, package links, documentation concision, and all semantic surface kinds.
- The separately authorized campaign used Codex CLI 0.146.0 in five ephemeral read-only roots. An initial normal-sandbox startup failure caused by read-only evaluator state and a later restricted-network failure produced no result files and were treated as startup evidence, not model verdicts.
- The corrected network-enabled campaign produced exactly five immutable sanitized results. Direct, indirect, incomplete, non-triggering, and unsupported-action responses passed their specified boundaries; `tests/pressure/integrated/verdicts.json` binds every prompt and result digest with evidence and limitations.
- Traceability adds direct INC-008 evidence to one exercised atomic obligation in each of the fifteen advanced groups. Atomic order, normalized requirements, assignments, and semantic digest remain unchanged; traceability SHA-256 is `a5fb73c3b9fa8619e0a225c2a388e20a88c475b291805508466dbd324a114cb0`.
- Integrated candidate SHA-256 is `34e1d8685c44b5a4aaab90041a66aa35bee1552e169cda6c584ce8075703d753`; integration-evidence SHA-256 is `a8a0b7175381c5fef6ac5f057aa2acbeb3d3f31fd68de29b26d2fc8b06ff02ad`.

## Review evidence

- Six distinct controller self-reviews were persisted before reconciliation. All are non-independent and reduced assurance; no reviewer or subagent dispatch occurred.
- Requirements, architecture, test-evidence, compatibility, and reliability reviews found no material gap.
- Security/privacy reported `F-008-001`; the focused repair and renewed security review closed it. Zero unresolved material findings remain.
- Review packet SHA-256 is `d870ce5bd8a0d8061d4ce2108cfc441e6842719a601cc4603145b0865b894d8d`.
- Closure readiness explicitly records `closure_reconciliation_performed: false`, `program_closed: false`, and `real_draft_pr_decision_performed: false`.

## Deviations and amendments

- `evaluator-action-name` — minor correction recorded at 2026-08-09T23:53:16Z. State-authority preflight rejected AUTH-024 with `unsupported action` because `fresh-model-evaluation` and `external-egress` are not accepted action identifiers. AUTH-024 remains immutable and unrelied. AUTH-025 uses the accepted `modify-external-state` identifier, supersedes AUTH-024, and preserves the exact user-approved five-run synthetic scope, constraints, recovery, and exclusions. No prompt was transmitted before correction. No program dimension or user-owned decision changed.
- The exact-navigation repair is already named in the approved initial modify map and is not an implementation amendment.
- Every other accepted package owner remains preserve-only until a new material RED and complete bounded amendment record exist.

## Recovery domains

- Source code: touched only inside the exact plan; recover with attributed `apply_patch` edits before evidence binding. Git reset/clean/stash is prohibited.
- Persistent data: not touched; synthetic state is confined to temporary fixtures and repository governance files.
- Deployment: not touched.
- Provider or external state: only the separately authorized five read-only synthetic model evaluations may occur; they authorize no provider mutation.

## Logical boundaries

Logical only; no staging or commit:

1. `integrated-contract-red` — planned tests, fixtures, prompts, and preserved RED.
2. `disposable-pilot-green` — continuity repair and deterministic integrated pilot.
3. `fresh-context-evidence` — five authorized raw outputs and verdicts.
4. `package-naming-readiness` — package, documentation, concision, naming, traceability, and readiness evidence.
5. `reviewed-inc-008-candidate` — actual reviews, final verification, packet, readiness evidence, and handoff.

## Final verification and stop

- Final coherent suite after lifecycle sealing: `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — exit 0; 223 tests passed in 12.273 seconds.
- Package, program authority, repository preparation, exact-plan, integrated-evidence, review-bundle, and skill validators passed on the final tree.
- `rtk git diff --check` passed with no output. Final Git observation remains branch `main`, head `53edb8fad2008c7d35b6c17dbb973b24022947fd`, zero staged or conflicted paths, no active operation, and the accepted shared dirty tree plus planned INC-008 paths.
- Review evidence SHA-256: `46cdea6c565b219ea49e4e5ccb85db9ced13411dda3f5a9f1745a5a3b1bbd914`.
- Review packet SHA-256: `d870ce5bd8a0d8061d4ce2108cfc441e6842719a601cc4603145b0865b894d8d`.
- Closure-readiness evidence SHA-256: `b0ba785927c9574eb1af61b9f448cdd70cceaee660e8f7d24d70dd4d2ac3c59f`.
- Handoff SHA-256: `66e4a0eedd89a8a46cf874d016cbc1c35c7e71c5e35b84ea01acd46ee2e872ee`.
- Lifecycle receipts: sequence 66 `reviewing`, sequence 67 `verified`, sequence 68 `awaiting-diff-approval`; final status SHA-256 `83466918bbcd028777bb956f1e18e60195d707fc64ca8b097d76eb56152d3a64`.
- ISP-001 remains `active`. INC-008 is not accepted. ISP-001 closure reconciliation, closure approval, and closure were not performed.
- Commit created: false. Staged: false. Real pull request, push, release, deployment, installation, migration, destructive action, and provider mutation: false.
- Mandatory stop: await explicit inspection and diff approval for INC-008. Do not begin program-closure reconciliation.
