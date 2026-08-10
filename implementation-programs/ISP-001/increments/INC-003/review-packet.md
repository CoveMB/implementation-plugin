# INC-003 Review Packet

## Decision requested

Review the complete non-commit INC-003 diff and either approve it or request changes. The selected `approval:full-increment` mode requires user diff acceptance. This packet does not accept the diff, authorize a commit or external action, begin INC-004, or close ISP-001.

## Authority and scope

- Program: ISP-001 revision 2
- Source: SOURCE-002 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`
- Program Markdown: `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`
- Atomic semantic requirements: `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`
- Approved exact-file plan: `8db40db410f5d884dad1a611558415f1c6caa4e857a02bdd2cb6facaf6a01a6d`
- Approval: APR-012
- Non-commit implementation authorization: AUTH-008
- Workspace: main checkout at head `53edb8fad2008c7d35b6c17dbb973b24022947fd`, selected base `f14449b8808574c720927aedab5b64871cc63858`

## Outcome delivered

INC-003 now provides:

- distinct durable program and increment state matrices;
- all five approval modes with creation-only defaulting;
- exact versioned approval binding and ambiguity rejection;
- explicit repository observation and separately authorized workspace selection;
- exact action authorization independent of approval policy;
- conditional verification and packet gates for diff acceptance;
- compare-and-swap atomic JSON replacement and prefix-preserving JSONL append;
- deterministic `validate-state`, `check-action`, `select-workspace`, and `transition-state` routes;
- a focused state/action procedure linked from the concise front door; and
- package enforcement for the new regular, non-symlink assets.

Reusable and package-facing paths, symbols, commands, schemas, and fixtures are project-neutral. Program identifiers appear only in repository governance records.

## Accepted-criterion evidence

| Criterion | Evidence |
|---|---|
| Every legal transition succeeds and every illegal transition fails closed | exhaustive 49-pair program and 169-pair increment tests, blocked-resume test, program-only application test, and state-specific diff gates |
| All five modes match the approved matrix | exact table-driven mode policy test plus default and continuation tests |
| Stale or mismatched approvals, state, workspaces, and briefs are rejected | field mutation, schema, duplicate, conflict, workspace observation, brief, plan, and CLI invariant tests |
| Atomic updates retain prior-state evidence and schema version | replacement, previous-state, compare-and-swap, replacement failure, file-sync failure, JSONL prefix, duplicate, and trailing-newline tests |
| No approval mode implies consequential authority | every mode crossed with pull-request, merge, publish, release, deploy, migrate, destructive, provider, and external-state actions without a grant |

## Reviews and remediation

The required reviews were separate controller self-review passes and therefore non-independent:

- Requirements review `11508f6acc667cb6a99cdf5d76bf2a2eb1fc1d4ab61fb170e671e3234111093b`
- Architecture review `14bb60649245e9f7f4f406291d90123535b30f9d3adf70c5ca305570fc70f275`
- Test-evidence review `dfa73cc4aafdea8a845d441d65d5646cc07c54351d3ed12692fa53be5dcb5065`

Four material findings were remediated and regression-tested:

- REQ-001: exact rejected/revoked records now conflict with positive authority.
- ARCH-001: non-terminated JSONL prefixes are rejected before append.
- ARCH-002: program-only transitions no longer require increment movement.
- ARCH-003: user diff acceptance requires fresh verification and a matching packet.

No unresolved material finding remains.

## Fresh verification

Run at `2026-08-08T23:28:01Z` on the reviewed tree:

- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — exit `0`; 72 tests passed.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .` — exit `0`; package passed.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program implementation-programs/ISP-001` — exit `0`; program authority passed.
- `rtk env PYTHONDONTWRITEBYTECODE=1 python3 /Users/CoveMB/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/implementing-staged-plans` — exit `0`; skill passed.
- `rtk git diff --check` — exit `0`; no output.

Preservation verification:

- SOURCE-001 `3f31c011961368a6b8c6808d9542b3b24cbc2afa82a2ca5291c062d51dc917a8`
- SOURCE-002 `f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57`
- revision 1 program `ec94caa50ff8918e242170220816e92ea2c48b36cd6b2e19c531d37aea8d0324`
- revision 2 program `1ed05a86525f9801b593f71272e15fe7ea8ef2088ea3e62e44686824728ba253`
- semantic digest `151cbe6731fe012b92f2d6138745465bec9b548e89b00d2538fdb706bbe0c10f`
- evidence-updated traceability `eb0ab811543ad3e9da15373462bd9fe661d0085f9bb4f8e57ea1c002bef349d6`

## Changed surface

Production/package behavior:

- `skills/implementing-staged-plans/scripts/state_authority.py`
- `skills/implementing-staged-plans/references/state-authorization.md`
- `skills/implementing-staged-plans/SKILL.md`
- `skills/implementing-staged-plans/scripts/validate_package.py`

Tests and neutral fixtures:

- `tests/test_state_authority.py`
- `tests/test_package_validation.py`
- `tests/test_front_door_contract.py`
- seven files below `tests/fixtures/state-authorization/portable-archive-run/`

Governance and evidence:

- approved INC-003 brief, preparation, exact-file plan, execution record, three reviews, this packet, and handoff
- current manifest, traceability evidence, approval log, action-authorization log, and lifecycle status
- accepted INC-002 handoff addendum and prior accepted dirty governance/test files were preserved and extended from their current bytes

No files were staged or committed.

## Known limits

- Per-file atomicity does not provide a multi-file transaction, distributed lock, or hostile-concurrency guarantee.
- Repository observations are caller-supplied; Git discovery and drift classification remain assigned to INC-004.
- Static and fixture tests do not prove external integration, deployment, provider, publication, or production behavior.
- Review assurance is reduced because subagent and external evaluation were not authorized.
- Two lifecycle writes were recorded immediately after, rather than immediately before, the corresponding RED and remediation work; the execution record discloses both deviations with causal evidence.

## Mandatory stop

INC-003 stops at `awaiting-diff-approval`. Do not infer acceptance, commit authority, continuation to INC-004, program closure, or any consequential external action from this packet.
