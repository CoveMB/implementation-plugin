# INC-002 Preparation

## Authority and boundary

- Program: ISP-001 revision 2.
- Source: SOURCE-002, SHA-256 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`.
- Approval mode: `approval:full-increment`.
- Current authorized work: persist SOURCE-002/revision-2 governance and prepare the INC-002 exact-file plan.
- Mandatory stop: exact-file-plan approval and bounded implementation/action authorization.
- Excluded: implementation, evaluator dispatch, commit, push, pull request, installation, publication, release, deployment, migration, destructive action, or other consequential external state.

The implemented front door exists, but the focused source/program authority procedure belongs to INC-002 and is not yet available. This preparation therefore applies the approved bootstrap runbook as a manual safeguard and makes no mechanical-enforcement claim.

## Repository revalidation

- Repository/workspace: `/Users/CoveMB/Code/CoveMB/implementation-plugin`.
- Branch: `main`.
- Current head at preparation: `62cf3fb444919c8ee2cc0eb97ee1e8ff8d28b53d`.
- Selected continuation base: `f14449b8808574c720927aedab5b64871cc63858`; verified ancestor of the preparation head.
- Working tree before governance writes: clean, with no staged, unstaged, untracked, conflicted, or stashed paths reported.
- Active Git operation: none reported by `git status`.
- Current SOURCE-002 canonical path: 1,362 lines, 64,933 bytes, approved digest match.
- SOURCE-001 snapshot: unchanged at SHA-256 `3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8`.
- Supplemental runbook: unchanged at SHA-256 `7443254dcf48db50f96f5ef55192c0352b712ce9b7dcd80ee66af1e7341bbe3b`.
- Remote refs were not fetched because this local planning gate does not depend on remote freshness.

## Accepted prior evidence

INC-001 remains accepted on SOURCE-001/revision 1. Its current front door, validator, pressure corpus, review packet, and handoff are reusable inputs. Revision 2 does not claim that INC-001 supplied the later semantic-naming pressure evidence introduced by SOURCE-002.

Fresh preparation checks on the unchanged implementation tree:

- `rtk python3 -m unittest discover -s tests -v` — PASS, 26 tests.
- `rtk python3 skills/implementing-staged-plans/scripts/validate_package.py .` — PASS.
- `rtk python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans` — PASS.

These results establish current structural and test baselines only. They do not establish INC-002 behavior.

## Canonical source locations

The INC-002 plan is grounded in the following SOURCE-002 locations:

- authority and layered durable-artifact design: sections 1-6, lines 11-222;
- source registration and program decomposition: section 7.2, lines 237-254;
- program and traceability management: section 7.3, lines 255-261;
- semantic naming context boundary: section 9.3, lines 536-580;
- artifact invariants: section 10.1, lines 610-621;
- atomic traceability fields and closure dispositions: section 10.2, lines 623-637;
- intake and complete decomposition lifecycle: section 13.1, lines 723-738;
- artifact/traceability validation and repository-backed pilot: sections 23.4 and 23.8, lines 1114-1196;
- outcome sequence and INC-002 evidence: section 24, lines 1198-1252;
- design-wide acceptance: section 25, lines 1254-1282;
- approved defaults, including JSON/Markdown, schema evolution, state minimization, and contextual naming: section 26, lines 1284-1300.

Revision-2 group traceability remains explicitly non-machine-complete. INC-002 must replace the current group-only completeness basis with a source-unit inventory that accounts for every physical source line and source-located atomic requirement records that can be validated without pretending semantic classification is fully automatic.

## Current implementation and reusable patterns

- `skills/implementing-staged-plans/SKILL.md` is an 87-line front door with an honest unavailable-procedure fallback. It should gain one narrow route to the new focused procedure, not absorb the procedure.
- `skills/implementing-staged-plans/scripts/validate_package.py` establishes standard-library Python conventions: `Path`, deterministic sorted issues, pure validation functions, a small CLI, and no third-party runtime dependency.
- `tests/test_package_validation.py` establishes isolated `TemporaryDirectory` fixtures, import-by-path for hyphenated skill directories, deterministic issue assertions, and CLI-contract tests.
- `tests/test_front_door_contract.py` owns concise front-door structure and link validation.
- No repository runtime, package manager, CI workflow, external connector, or existing source/program authority implementation exists.

## Current official evidence

Accessed 2026-08-08:

- Python 3.14.6 `hashlib` documentation: `https://docs.python.org/3.14/library/hashlib.html`. Applicable to binary SHA-256 capture; `file_digest` leaves the file object in an unknown position, so the plan uses a dedicated binary handle and closes it immediately.
- Python 3.14.6 `tempfile` documentation: `https://docs.python.org/3.14/library/tempfile.html`. Applicable to secure same-directory temporary creation; deprecated `mktemp()` is excluded.
- Python 3.14.6 `os.replace` documentation: `https://docs.python.org/3.14/library/os.html#os.replace`. Applicable to atomic replacement of mutable state, but immutable source capture must use exclusive destination creation and must never overwrite an existing snapshot.
- Python 3.14.6 `os.link` documentation: `https://docs.python.org/3.14/library/os.html#os.link`. Applicable to no-overwrite finalization from a same-directory temporary file on Unix and Windows; unsupported hard-link behavior must fail closed rather than fall back to replacement.
- Python 3.14.6 `pathlib` documentation: `https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.resolve`. Applicable to containment and symlink-aware path validation; concrete paths are resolved before relative containment is accepted.

No dependency installation or version change is justified. The plan retains the Python standard library and current `unittest` harness.

## Repository-informed design

1. Add one focused package reference named `program-authority.md` for exact source capture, decomposition, progressive elaboration, approval binding, and hard stops.
2. Add one standard-library module named `program_authority.py` with a pure validation core and a bounded source-capture CLI. The name expresses the durable authority boundary rather than an increment coordinate.
3. Represent completeness with two layers in traceability:
   - source units partition every physical source line with a digest and a `requirement` or `context` classification;
   - atomic requirements reference requirement-classified source units and carry stable semantic identifiers, source locators, acceptance criteria, program allocation, and current disposition.
4. Treat complete line coverage as mechanically checkable and semantic classification as approval-bound human judgment. Never claim that line coverage alone proves semantic correctness.
5. Bind program approval to source digest, program revision, program-content digest, and the approved semantic-requirements digest. A changed binding rejects stale approval.
6. Preserve prior source/program revisions and their evidence; never overwrite an immutable snapshot or accepted evidence packet.
7. Demonstrate decomposition with a fictional portable-archive operations program. Reusable fixtures and package documentation contain no ISP-001, INC-002, or repository-specific roadmap names.

## Material risks and controls

- **False completeness:** full source-unit coverage can still misclassify a normative line as context. Control: explicit rationale, approval-bound semantic digest, requirements review, and no automatic semantic-completeness claim.
- **Path escape or symlink substitution:** source capture could read or write outside the selected root. Control: resolved containment checks, regular-file checks, no destination symlink, and negative fixtures.
- **Immutable overwrite:** retry behavior could replace prior evidence. Control: exclusive destination creation and a deterministic existing-snapshot failure.
- **Partial multi-file capture:** interruption can leave one new immutable file without its metadata. Control: do not advance program state until the complete binding validates; surface repair evidence rather than overwriting the snapshot.
- **Program revision drift:** changing program or semantic requirements can leave an old approval apparently current. Control: digest-bound approval validation and stale-approval fixtures.
- **Project leakage:** concrete ISP identifiers could leak into distributable procedure names or fixtures. Control: neutral names, package validation, and explicit positive/negative naming tests.

## Planning conclusion

INC-002 remains one coherent increment: source capture, authority validation, atomic traceability, revision/approval binding, and a decomposition pilot share one trust boundary and one verification contract. Splitting them would leave an intermediate state that could register evidence without proving complete program authority.
