# INC-007 Architecture and Semantic Naming Review

- Report ID: `architecture-initial`
- Reviewer role: `controller-self-review`
- Independent: `false`
- Reduced assurance: `true`
- Reviewed candidate: `66e727233fc19beebdc54f38a11cf30e0c5eb6ab1912067e24d2fa872866b642`
- Persisted before reconciliation: `2026-08-09T22:32:01Z`
- Basis: boundary, ownership, reuse, state minimization, and complete created/renamed semantic-surface inspection; no dispatch.

## Finding F-002

- Classification: material
- Affected requirement or invariant: compose accepted state authority and validate proposed records before rollover
- Severity: high
- Summary: resume and rollover retain avoidable trust in caller assertions.
- Evidence: `validate_resume_context` compares two records but cannot optionally compose `validate_state_authority`; `apply_increment_rollover` accepts raw Markdown without exact `LeanBrief` and `HandoffRecord` equality.
- Impact: a caller can present internally matching but repository-invalid resume evidence, or persist navigation bytes that were not generated from the validated records.
- Confidence: high
- Inspection path: `validate_resume_context` and `apply_increment_rollover`
- Smallest remediation: add optional accepted-state composition and require validated records whose deterministic renderings equal the proposed bytes.
- Disposition: open pending test-first repair
- Decision reference: none; implements the approved composition boundary

## Semantic naming disposition

All planned created paths, schemas, records, functions, command, tests, fixture scenario, and reference headings describe durable continuity or closure responsibilities. Governance-only increment identifiers remain confined to repository records. No roadmap-derived package name was found. F-002 concerns ownership, not naming.
