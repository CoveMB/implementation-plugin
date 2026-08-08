# INC-002 Test-Evidence Review

- Review time: `2026-08-08T22:12:22Z`
- Reviewer: coordinating agent, focused self-review
- Independence: non-independent; reduced assurance
- Frozen implementation head: `9043ba22d9ecb72556f805be2ba2dc3df7d8d8cd`

## Scope

Reviewed the observed RED evidence, negative-fixture intent, pilot completeness, CLI outcomes, final-command contract, and limits of static evidence.

## Evidence inspected

- Initial RED: `FileNotFoundError` for the absent `skills/implementing-staged-plans/scripts/program_authority.py`.
- Structural-route RED: missing `validate_authority_assets` plus the missing Program authority link.
- Pilot RED: missing `atomic_requirements` in the committed neutral fixture skeleton.
- Current-traceability RED: v1 schema and absent `source_units`.
- Negative tests cover missing/overlapping/reversed lines, changed unit digests, invalid atomic fields and references, stale/conflicting approvals, source/program mutation, absolute/escaping/symlink paths, capture mismatch/existing destinations, revision mutation, and CLI statuses 0/1/2.
- The neutral pilot rejects a changed source byte and a deleted atomic requirement.

## Raw material finding

### TEST-001 — Non-overwriting hard-link failure lacks direct test protection

- Affected requirement: `REQ-ARTIFACT-INVARIANTS`; immutable source capture finalization contract.
- Evidence: implementation has an `OSError` fail-closed branch for unsupported `os.link`, but the focused tests do not exercise it. Existing-destination coverage exercises `FileExistsError`, not unsupported finalization.
- Impact: a future overwrite-capable fallback or incomplete cleanup could regress without a focused failure.
- Severity/confidence: material test-protection gap, high confidence.
- Smallest remediation: mock `os.link` as unsupported, assert capture raises, and assert neither final snapshot nor metadata exists. Also assert a pre-existing metadata destination blocks capture before snapshot creation.

## Evidence limits

These tests establish deterministic local structural and file-behavior contracts. They do not prove installed skill discovery, live agent semantic judgment, cross-platform filesystem behavior, accessibility, deployment, provider, or external-state behavior. No fresh model evaluation was authorized or run.

## Post-repair disposition

`TEST-001` is repaired. `test_capture_fails_closed_when_hard_links_are_unsupported` mocks an unsupported hard-link operation and proves that capture raises with neither final artifact present. `test_existing_metadata_blocks_capture_before_snapshot_creation` proves metadata collision preserves the existing bytes and creates no snapshot. The focused capture suite and complete authority suite are GREEN.
