# INC-005 Requirements Review

## Scope and assurance

- Review mode: controller self-review; non-independent with reduced assurance.
- Authority: `APR-016` / `AUTH-014`; approved plan `748c8622778e70cf3eab9b5aef035f16c382006cee6319614572c1cfbd70c9f9`.
- Reviewed surfaces: execution module/reference, focused tests/fixture, front-door/package changes, execution record, direct traceability evidence, and lifecycle state.
- No commit, external action, later-increment work, dependency, runtime, provider, persistence, deployment, security-control, or public application surface is in scope.

## Acceptance review

1. **Test-first evidence:** observed missing-module RED preceded production code and the same focused command later passed 28 tests. Material gap R-1 below prevents the current record types from fully enforcing immutable ordering.
2. **Alternative verification:** structural tests observed five intended failures before the reference/route/asset declarations, then 22 tests and package validation passed. The limitation is explicit.
3. **Ownership and unrelated work:** exact planned/actual equality, preserve fingerprints, managed ownership, and accepted overlap are implemented. Material gap R-2 permits an accepted dirty overlap record to claim `accepted_overlap=false` while still passing.
4. **Semantic naming:** contextual validation delegates to the accepted implementation and paired coordinate/governance/domain tests pass. Material gap R-3 allows a created surface and its naming record to share text while disagreeing on surface kind.
5. **Amendments:** minor, bounded, program, unknown, incomplete, and contradiction paths are covered; all five modes are exercised; standard mode renews exact-plan approval.
6. **Recovery:** exactly four domains and Git-only external recovery rejection are covered. Architecture review owns the remaining domain-record consistency finding.

## Advanced requirement groups

- `REQ-AUTHORITY`: plan approval and non-commit action authorization remain separate and exact.
- `REQ-EXECUTION-AMENDMENT`: current-plan execution composes accepted amendment precedence and mode decisions.
- `REQ-VALIDATION`: focused negative matrices cover invalid evidence, ownership, naming, amendments, boundaries, authority, and recovery.
- `REQ-SEQUENCE`: sequence 36→37→38→39 used accepted state authority; no mode inferred commit authority.
- `REQ-DEFAULTS`: complete bounded changes proceed only in supported preapproved modes without user-owned decisions.
- `REQ-SEMANTIC-NAMING`: created and renamed surfaces receive contextual inventory with explicit compatibility treatment.
- `REQ-DESIGN-RISKS`: program dimensions and contradictions dominate caller labels and approval mode.

## Material findings

### R-1 — Frozen evidence accepts mutable sequence fields

- Invariant: accepted immutable evidence cannot change after validation.
- Location: `execution_discipline.py` lines 47-75 and 132-137.
- Evidence: frozen dataclasses type `evidence_order` and `relevant_inputs` as tuple-or-list, and `_string_sequence` accepts lists. A caller can mutate a previously accepted list in place.
- Impact: persisted RED/GREEN order or relevant-input evidence can change after validation without a new decision.
- Confidence: high.
- Smallest repair: accept tuples only in frozen record sequence fields and add negative tests for lists.
- Required rerun: focused execution-discipline suite.

### R-2 — Accepted overlap flag is not reconciled with controlling overlap inputs

- Invariant: ownership records must agree with accepted pre-write dirty ownership.
- Location: `execution_discipline.py` lines 268-301.
- Evidence: a record with `accepted_overlap=false` passes when the same path is both dirty and listed in `accepted_existing_paths`; only false positive claims are rejected.
- Impact: the durable ownership record can contradict the controlling accepted-overlap decision.
- Confidence: high.
- Smallest repair: require the flag to equal whether a planned path is both pre-write dirty and accepted; retain the accepted overlap validator.
- Required rerun: focused ownership and integration tests.

### R-3 — Semantic inventory equality ignores surface kind

- Invariant: each created or renamed surface has exactly one naming record for the same kind.
- Location: `execution_discipline.py` lines 322-332.
- Evidence: equality compares only surface strings, so a created path paired with a symbol record of the same text passes.
- Impact: a path, command, schema, or generated surface can bypass its kind-specific contextual contract.
- Confidence: high.
- Smallest repair: compare `(surface, surface_kind)` pairs and add a mismatched-kind regression.
- Required rerun: focused semantic-surface and integration tests.

## Disposition

Requirements review: **material findings present; remediation required before verification**. No finding changes program requirements, acceptance, public behavior, protected contracts, risk posture, dependency sequence, or review cadence.
