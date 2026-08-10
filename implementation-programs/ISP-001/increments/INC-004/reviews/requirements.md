# INC-004 Requirements Review

## Review status

Controller self-review; non-independent and reduced assurance. This is the raw requirements pass before reconciliation or remediation.

## Scope reviewed

- Approved INC-004 outcome, six acceptance criteria, eight advanced requirement groups, exact file map, and exclusions.
- New repository-preparation module, reference, tests, neutral fixtures, front-door/package integration, current-workspace evidence, and traceability changes.

## Criterion results

1. Repository fixtures cover dirty/untracked state, operations, base movement, baseline failures, managed ownership, reuse, dependency drift, and invalidated assumptions: demonstrated, but operation-marker execution coverage is incomplete.
2. Evidence refresh follows materiality and risk: demonstrated across every material predicate, official availability, high-risk blocking, exact lower-risk reuse, mismatch, access failure, and irrelevant installed surfaces.
3. Drift categories are distinct: demonstrated with deterministic base-invalidating precedence and separate reconcilable/benign results.
4. Production changes require a current exact-file plan: partially demonstrated. Missing/stale/symlinked/mismatched/incomplete content and digest changes reject, but the CLI does not yet validate the entire action-authorization tuple or prove that `--preparation` names the manifest-owned bound artifact.
5. Bounded implementation amendments cannot conceal program amendments: demonstrated for every program dimension, contradictions, evidence, obligation, user-decision, and recovery gates.
6. Proposed names identify context/intention and planning vocabulary has a governed basis: demonstrated across all required surface kinds with positive and negative contextual cases and compatibility handling.

## Material findings

### REQ-004-01 — Complete plan/action/preparation binding

- Requirement/invariant: production modification requires the current exact-file plan plus exact action authority and current preparation evidence.
- Location: `repository_preparation.py` current-plan binding helpers and `test_repository_preparation.py` integration coverage.
- Impact: a record sharing only authorization ID, action, and plan digest could be mistaken for the current full tuple; an arbitrary preparation path contributes a digest without being manifest-owned.
- Confidence: high.
- Smallest repair: validate program/revision/source/program/semantic/increment/brief/mode/workspace tuple, non-empty scope, manifest-owned plan/preparation paths, and status preparation digest/head; add negative tests.
- Rerun: focused preparation tests, live preparation/plan CLI, state/program validators, full suite.

## Disposition

One material finding requires bounded remediation. No program amendment is indicated: the repair enforces the already approved contract without changing scope, behavior, risk posture, dependencies, sequencing, or public semantics.
