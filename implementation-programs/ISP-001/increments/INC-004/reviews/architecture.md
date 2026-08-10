# INC-004 Architecture Review

## Review status

Controller self-review; non-independent and reduced assurance. This is the raw architecture, security, semantic-naming, and simplicity pass before reconciliation or remediation.

## Strengths observed

- One standard-library module separates read-only Git adaptation from immutable decision records and pure validators.
- Git calls use argument vectors, `shell=False`, explicit resolved working directories, captured bytes, bounded timeouts, and concise failures.
- Porcelain-v2 parsing preserves complete NUL-delimited paths and rename pairs before filesystem decoding; absolute and parent-escaping paths reject.
- Git/common directories and operation markers are resolved through Git, including linked-worktree layouts.
- Drift and amendment decisions use explicit qualitative precedence. Program dimensions and authoritative contradictions dominate caller labels.
- Package-facing surfaces and neutral fixtures use domain responsibility and intention rather than repository program coordinates.
- The front door contains one route and leaves detailed policy in the focused reference.

## Material findings

### ARCH-004-01 — Fail closed on the whole authority tuple

- Invariant: a plan-content pass cannot create write authority; the authorization must match the same complete current tuple used by state authority.
- Location: `_validate_bound_plan_digest`.
- Impact: matching only authorization ID, `modify-workspace`, and plan digest is weaker than the accepted authority boundary.
- Confidence: high.
- Smallest repair: compare all common binding fields and workspace fields and require one authorized record with a non-empty scope.
- Rerun: new binding-negative test, existing exact-plan tests, live plan validation.

### ARCH-004-02 — Bind the preparation path before hashing it

- Invariant: preparation evidence must be the regular, non-symlink artifact owned by the manifest and bound by status.
- Location: `_current_plan_binding` and `validate_preparation`.
- Impact: hashing a caller-selected file establishes bytes, but not artifact identity or current status binding.
- Confidence: high.
- Smallest repair: resolve the manifest role, compare the caller path, validate the status path/digest/head tuple, and reject symlinks through the managed-path resolver.
- Rerun: preparation-binding tests plus live preparation/plan commands.

## Simplicity and exclusions

No second module, dependency, schema framework, hook, service, cache, persistent evidence store, or external connector is warranted. No unrelated refactor is recommended. No program amendment is required for either finding.
