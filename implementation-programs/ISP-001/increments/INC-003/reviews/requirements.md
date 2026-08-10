# INC-003 Requirements Review

## Review identity

- Mode: non-independent controller self-review
- Scope: approved INC-003 exact-file plan `8db40db410f5d884dad1a611558415f1c6caa4e857a02bdd2cb6facaf6a01a6d`
- Authority: APR-012 and AUTH-008
- Comparison head: `53edb8fad2008c7d35b6c17dbb973b24022947fd`

## Acceptance coverage

- Separate program and increment states: explicit seven-state and thirteen-state matrices with exhaustive 49-pair and 169-pair tests.
- Five approval modes: one immutable policy table with exact table-driven assertions for scope, plan pause, interruptions, diff acceptance, and continuation.
- Approval binding: versioned exact source, program, semantic, increment, brief, plan, mode, and workspace matching; stale and ambiguous records fail closed.
- Workspace selection: explicit caller observation, exact selection approval, exact `create-workspace` authorization, prior-workspace digest, and atomic persistence.
- Action separation: approval policies never produce an action decision; every action grant is checked against its exact tuple.
- Atomic history: compare-and-swap replacement retains prior digest, schema, sequence, and JSONL byte prefix.
- Boundary: one-increment modes do not continue automatically; no diff acceptance or consequential action is performed by this increment.

## Material finding

### REQ-001 — Conflicting negative records did not poison a matching grant

- Evidence: `validate_approval_binding` and `decide_action_authorization` originally filtered rejected records before deciding whether an exact approved or authorized record existed.
- Impact: an exact rejected or revoked tuple could coexist with a positive tuple without producing the required ambiguity stop.
- Remediation: evaluate all schema-valid bound records first, reject conflicting decisions or revocation, then select a unique positive record.
- Regression evidence: `test_conflicting_duplicate_approval_is_rejected` and `test_rejected_revoked_expired_legacy_and_conflicting_grants_fail` observed RED, then passed after remediation.
- Disposition: resolved.

## Result

All five INC-003 acceptance criteria have direct implementation and test coverage. No unresolved material requirements finding remains. Assurance is reduced because this was a controller self-review, not an independent review.
