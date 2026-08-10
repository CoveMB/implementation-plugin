# INC-007 Compatibility Review

- Report ID: `specialist-compatibility-initial`
- Reviewer role: `controller-self-review`
- Independent: `false`
- Reduced assurance: `true`
- Reviewed candidate: `66e727233fc19beebdc54f38a11cf30e0c5eb6ab1912067e24d2fa872866b642`
- Persisted before reconciliation: `2026-08-09T22:32:04Z`
- Trigger: three new version-one schemas, a new CLI, required assets, and optional closure approval bindings.

## Finding F-005

- Classification: material
- Affected requirement or invariant: conflicting closure approvals or later-action grants fail closed
- Severity: high
- Summary: later-action matching filters to approved/current records before checking conflicts.
- Evidence: one exact approved closure record plus one exact rejected record still leaves one matching approval; the same pattern applies to authorized versus rejected or revoked grants.
- Impact: contradictory persisted decisions can be treated as an unambiguous authority grant.
- Confidence: high
- Inspection path: `decide_later_action` matching approval and grant comprehensions
- Smallest remediation: identify all exact-bound records first, reject conflicting decisions/revocations and duplicates, then select one current approval and grant; add regressions.
- Disposition: open pending test-first repair
- Decision reference: none; version-one fail-closed repair

## Compatibility disposition

Existing non-closure `ApprovalBinding` construction remains compatible because new digest fields are optional and last. Existing action bindings, modes, transitions, and CLI contracts remain unchanged. Unsupported evidence schemas and unknown mapping fields fail closed.
