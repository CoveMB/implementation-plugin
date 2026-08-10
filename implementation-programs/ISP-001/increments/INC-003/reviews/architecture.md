# INC-003 Architecture Review

## Review identity

- Mode: non-independent controller self-review
- Scope: state authority, persistence boundary, package route, neutral fixtures, and current governance integration
- Design focus: state separation, fail-closed authorization, atomicity, security, naming, and smallest sufficient architecture

## Architecture assessment

The implementation keeps policy and effects distinct:

- immutable tables and pure decisions own legal transitions and approval modes;
- exact approval and action bindings are separate dataclasses and decision paths;
- repository observations are supplied by the caller instead of discovered or guessed;
- the accepted program-authority implementation is reused rather than duplicated;
- mutation is limited to same-file compare-and-swap replacement or append-only JSONL replacement;
- the front door links one focused procedure instead of copying its policy;
- reusable symbols, commands, schemas, fixtures, and paths remain project-neutral.

## Material findings

### ARCH-001 — Non-terminated JSONL could be corrupted by append

- Evidence: the original append path preserved a prior byte prefix without requiring that a non-empty prefix end in a newline.
- Impact: the next canonical record could be concatenated onto the prior JSON object.
- Remediation: validate the atomic target first and reject a non-empty JSONL file without a trailing newline before loading or replacing it.
- Regression evidence: the new non-terminated-prefix test observed RED, then passed.
- Disposition: resolved.

### ARCH-002 — Program-only transitions were coupled to increment movement

- Evidence: `apply_state_transition` always evaluated an increment edge, so `active -> awaiting-closure-approval` with an unchanged increment failed as a same-state increment transition.
- Impact: persisted program and increment state were syntactically separate but not independently advanceable.
- Remediation: require at least one axis to change, evaluate each changed axis independently, and leave the unchanged axis intact.
- Regression evidence: `test_program_only_transition_does_not_require_increment_movement` observed RED, then passed.
- Disposition: resolved.

### ARCH-003 — User diff acceptance lacked a fresh verification/packet decision gate

- Evidence: the `awaiting-diff-approval -> accepted` adjacency originally returned allowed without checking its verification binding or packet digest.
- Impact: a malformed persisted state could bypass the intended review and fresh-verification invariant if other approval records existed.
- Remediation: require a verified sequence, matching review-packet digest, zero unresolved material findings, and a user-diff approval mode on that edge.
- Regression evidence: the expanded full-diff/user-diff transition test observed RED, then passed.
- Disposition: resolved.

## Limits

Per-file replacement is atomic on the supported same-filesystem path. It is not a multi-file transaction, distributed lock, or hostile-concurrency no-clobber guarantee. Git fact discovery and drift classification remain assigned to the later repository-preparation increment; INC-003 validates explicit observations only.

## Result

No unresolved material architecture, security, privacy, naming, or simplicity finding remains. Assurance is reduced because this was a controller self-review.
