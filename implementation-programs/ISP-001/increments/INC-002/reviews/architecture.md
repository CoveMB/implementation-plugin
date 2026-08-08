# INC-002 Architecture Review

- Review time: `2026-08-08T22:12:22Z`
- Reviewer: coordinating agent, focused self-review
- Independence: non-independent; reduced assurance
- Frozen implementation head: `9043ba22d9ecb72556f805be2ba2dc3df7d8d8cd`

## Scope

Reviewed immutable-write safety, program-root containment, symlink handling, revision/evidence preservation, semantic naming, pure validation boundaries, standard-library dependency scope, and unnecessary complexity.

## Confirmed design properties

- Source capture streams exact bytes to same-directory secure temporary files and finalizes with `os.link`; it has no overwrite-capable fallback.
- Both destination parents must already exist inside the resolved program root; source and controlling paths reject symlinks.
- Validation returns deterministic issues for malformed repository data and does not print source content or secrets.
- Stable semantic fields alone determine the semantic requirements digest; later evidence and disposition changes do not rewrite approved semantics.
- The front door adds one narrow route to one focused procedure. Package-facing names and the fictional pilot remain project-neutral.
- The implementation remains one standard-library module as approved. One unused helper was removed during the review.

## Raw material finding

### ARCH-001 — Later revision could omit preservation bindings

- Affected requirement: `REQ-SOURCE-PROGRAM`; INC-002 acceptance criterion 4.
- Evidence: a new revision-2 fixture with current source/program/semantic approval but no `revision_history` returned no issues. The focused RED test `test_later_revision_without_preservation_record_fails` failed with `received []`.
- Impact: a later program revision could validate while failing to bind prior source, program, and accepted evidence, defeating revision preservation.
- Severity/confidence: material, high confidence.
- Smallest remediation: require every revision greater than 1 to name an earlier positive revision and provide validated prior-source, prior-program, and non-empty prior-evidence path/digest bindings.
- Approved-scope effect: none; this enforces the accepted contract without changing it.

## Non-material observations

- Filesystem validation is fail-closed for the stated local contract but does not claim protection from a privileged concurrent attacker changing directory entries between checks.
- A partial two-file capture can leave an immutable snapshot if metadata finalization fails; the procedure explicitly treats that as blocked evidence and forbids overwrite or state advancement.

## Post-repair disposition

`ARCH-001` is repaired. The validator now rejects later revisions without `revision_history`, requires an earlier positive superseded revision, requires prior source and program paths plus digests, and requires non-empty prior-evidence path/digest bindings. The observed RED test is GREEN, the full authority suite remains GREEN, and current revision-2 incomplete validation remains GREEN. No approved outcome, public contract, or semantic traceability record changed.
