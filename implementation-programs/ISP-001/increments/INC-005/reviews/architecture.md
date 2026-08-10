# INC-005 Architecture Review

## Scope and assurance

- Review mode: controller self-review; non-independent with reduced assurance.
- Focus: pure/authority boundaries, reuse, ownership, semantic coverage, amendment precedence, logical commit partitioning, recovery separation, simplicity, and later-increment exclusions.

## Boundary assessment

- The module is standard-library and pure. It imports accepted preparation/state records and validators; it performs no subprocess, filesystem, Git, network, provider, or lifecycle mutation.
- Amendment dimensions and coordinate detection are not duplicated. Approval modes are read from accepted state policy, and commit decisions delegate to exact action authority.
- Package routing is one concise reference link; the reference owns detailed execution rules.
- The bounded path-level consolidation of two conceptual code slices is coherent: one module and one test path each appear once, while review language retains both responsibilities.
- No absent review-packet enforcement, continuity, closure, pressure-evaluation, deployment, data, or provider mechanism is claimed.

## Material findings

### A-1 — Logical commit validation accepts an internally inconsistent authorization decision

- Invariant: only a successful exact state-authority decision can satisfy commit authority.
- Location: `execution_discipline.py` lines 480-485.
- Evidence: `authorized=true` plus a nonempty issue tuple and identifier passes. The normal state helper does not produce this shape, but the public validator accepts caller-supplied decisions and the bundle loads one from JSON.
- Impact: malformed or tampered evidence can be represented as exact commit authority.
- Confidence: high.
- Smallest repair: require boolean true, nonempty authorization identifier, and an empty issue tuple; add a regression.
- Required rerun: focused commit and integration tests.

### A-2 — Recovery records do not enforce untouched neutrality or domain-specific authority

- Invariant: untouched domains claim no recovery mechanism or authority; touched domains name authority applicable to that domain.
- Location: `execution_discipline.py` lines 505-539.
- Evidence: an untouched domain may retain `git-revert` and a non-`none` required authority; a touched provider domain may claim an arbitrary authority string.
- Impact: records can blur the source/data/deployment/provider boundaries the increment exists to preserve.
- Confidence: high.
- Smallest repair: require `mechanism=none` and `required_authority=none` when untouched; constrain touched authority to a domain-specific accepted action set; add negative cases.
- Required rerun: focused recovery and integration tests.

## Security and privacy predicate

- Repository paths and commands remain caller-supplied strings; the module neither resolves nor executes them.
- Preserve evidence uses fingerprints, not file contents. No environment, credential, secret, output capture, or external payload is persisted by the reusable module.
- Deterministic sorted issues avoid leaking nondeterministic state. The reference states that command output must be bounded and limitations recorded.

## Compatibility and simplicity predicate

- New schema/symbol/reference names are project-neutral. Unsupported schemas and surface kinds fail closed.
- Existing public/persisted/generated/external names route through accepted compatibility checks.
- One module remains cohesive and avoids speculative staging, commit, recovery, or provider abstractions.

## Disposition

Architecture review: **two material consistency findings; bounded remediation required**. Neither finding requires a program amendment.
