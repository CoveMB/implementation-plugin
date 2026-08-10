# Compatibility Specialist Review

- Predicate: public API/compatibility materially touched by two new persisted schema identifiers, a read-only CLI exit contract, required package assets, and imports from accepted modules.
- Reviewer role: controller self-review acting in the specialist scope.
- Independence: non-independent.
- Assurance: reduced; no specialist reviewer or external tool was dispatched.
- Persisted before reconciliation: 2026-08-09T21:12:34Z.

## Assessment

Unknown evidence and packet schema versions fail closed. JSON list fields normalize to immutable tuples before frozen record creation, unknown record fields fail constructor parsing, package tests require regular non-symlink assets, links resolve, and reusable names remain project-neutral. No migration, alias, or backward-compatibility claim is made for these new version-one schemas.

## Material finding F-004

- Classification: material.
- Affected requirement or invariant: the new persisted schemas must encode the approved report, finding, remediation, final-verification, and packet bindings completely on their first version.
- Evidence and location: the frozen version-one record shapes omit the dimensions identified in F-001 through F-003. Once evidence is persisted, accepting those incomplete shapes as the version-one contract would create avoidable schema drift.
- Impact: later repairs would require a schema revision or silently reinterpret version-one records, undermining compatibility and artifact invariants.
- Severity: high.
- Confidence: high; the schema identifiers are already exposed by the fixture and CLI while their dataclasses are incomplete relative to the approved exact plan.
- Reproduction or inspection path: compare the exact-plan interface and test-first requirements with the current dataclass fields and fixture keys.
- Smallest remediation: repair all incomplete record shapes and fixture data before final evidence is persisted; retain the same version-one identifiers only after the complete contract validates.
- Disposition: open pending the focused F-001 through F-003 repairs and renewed compatibility review.

## Compatibility limit

This increment establishes a new local contract only. It does not prove third-party adoption, migration safety, runtime integration, or provider compatibility.
