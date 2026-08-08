# ISP-001 Revision 2 — Implementing Staged Plans

**Status:** Approved on 2026-08-08  
**Canonical source:** SOURCE-002 at SHA-256 f4d4bca12706170210be202444df0d4c6d0bbb382143c5a0d0c8da2616eb9c57  
**Current approval mode:** approval:full-increment for INC-002  
**Supersedes:** Revision 1 for remaining work; accepted INC-001 evidence remains bound to revision 1 and SOURCE-001.  
**Package identity:** implementation-plugin  
**Skill identity:** implementing-staged-plans

## Goal

Build a layered, repository-backed skill that turns an authoritative implementation plan into a persistent, traceable implementation program and advances one reviewable increment at a time without silently changing requirements, endangering user work, or inferring consequential-action authority.

## Approved architecture

Use one skills-only plugin with a concise front door, stage-focused references, durable program artifacts, and deterministic validators for mechanical invariants. Persist operational state in repository artifacts rather than chat history. Keep prompts semantically bounded but procedurally lean.

The following are fixed:

- the canonical source digest and authority model;
- all eight outcome-oriented increments;
- the five approval modes and their universal gates;
- separate program, increment, and action-authorization state;
- just-in-time exact-file planning;
- user-work protection, evidence applicability, amendment classification, honest review independence, observed test evidence, review packets, continuity, reconciliation, closure, and later-action gates;
- context-and-intention-based semantic naming across implementation surfaces, with planning terms allowed only for implementation-governance artifacts or justified durable domain concepts;
- the plugin and skill identities and the exclusion of MCP, app, hook, marketplace, publisher, and publication configuration.

The following remain provisional until the preparing increment inspects current repository evidence:

- exact files beyond the current increment;
- reference decomposition beyond the front door;
- script language after the current increment;
- schema and validation libraries;
- test runner beyond the current increment;
- future artifact refinements;
- release and distribution mechanics.

## Global dependencies and gates

The governing dependency chain is:

SOURCE-002 confirmation -> revision 2 approval -> selected writable workspace -> accepted INC-001 evidence from revision 1 -> INC-002 -> INC-003 -> INC-004 -> INC-005 -> INC-006 -> INC-007 -> INC-008 -> separate closure reconciliation -> separate closure approval.

Every increment must:

1. revalidate repository and program state;
2. prepare or amend its current exact-file plan;
3. obey its approval mode;
4. implement only the authorized outcome;
5. run requirements, architecture, and test-evidence reviews;
6. run relevant specialist review;
7. remediate evidence-backed material findings;
8. perform fresh verification;
9. produce a complete review packet;
10. stop or continue only as the current approval and action authority allow.

## INC-001 — Baseline pressure suite and minimal front door

**Revision 2 carry-forward:** Accepted under revision 1 and SOURCE-001. The semantic-naming amendment is not retroactively claimed as INC-001 evidence; its new enforcement and pressure obligations are allocated to INC-004 through INC-008 and closure.

**Outcome:** Establish representative control failures and add the smallest valid plugin and skill entry point, invariant gates, capability discovery, and lifecycle routing.

**Depends on:** Approved revision 1, selected workspace, exact-file-plan approval.

**Deliverables:**

- preserved no-skill pressure cases, raw outputs, verdicts, and rationalizations;
- minimal skills-only plugin manifest and skill metadata;
- concise front door that reads persisted state, enforces early universal gates, discovers relevant capabilities, and truthfully stops when a later subsystem is unavailable;
- structural validation for package identity, metadata, links, prohibited components, placeholders, and front-door contracts.

**Acceptance:**

- baseline outputs are preserved before the skill is introduced;
- package and skill discovery contracts are structurally valid;
- coding before program approval, workspace selection, or an exact-file plan is refused;
- later lifecycle stages are not simulated as complete;
- no MCP, app, hook, marketplace, publisher, or publication surface appears;
- static validation and fresh-context pressure evidence remain clearly distinguished.

**Integration checkpoint:** The front door and validation command are stable enough for later increments to add focused procedures without replacing the routing contract.

## INC-002 — Immutable source capture, decomposition, and traceability

**Outcome:** Register immutable source plans, extract complete requirements, create outcome-oriented programs, support progressive elaboration, and enforce initial program approval.

**Depends on:** Accepted INC-001.

**Acceptance:**

- every source requirement receives a stable identifier, source locator, acceptance criteria, increment allocation, and current disposition;
- partial extraction cannot claim completeness;
- source or approval digest mismatch fails closed;
- program revisions preserve prior evidence and invalidate stale approval;
- a large-plan pilot avoids project-specific policy leakage.

**Integration checkpoint:** Source, program, and traceability authority can be loaded and validated by INC-003.

## INC-003 — Durable state, approval modes, and action authorization

**Outcome:** Implement separate program and increment state, legal transitions, approval binding, all five approval modes, workspace selection, and separate consequential-action authorization.

**Depends on:** Accepted INC-002.

**Acceptance:**

- every legal transition succeeds and every illegal transition fails closed;
- all five modes match the approved matrix;
- stale or mismatched approvals, state, workspaces, and briefs are rejected;
- atomic updates retain prior-state evidence and schema version;
- no approval mode implies pull-request, merge, release, deployment, migration, destructive, or provider authority.

**Integration checkpoint:** INC-004 preparation can rely on mechanically enforced lifecycle and authorization state.

## INC-004 — Repository preparation, evidence, shaping, and exact-file planning

**Outcome:** Revalidate repository truth, protect user work, classify drift, collect applicable evidence, refine increment shape, and create just-in-time exact-file plans with semantic naming inventories.

**Depends on:** Accepted INC-003.

**Acceptance:**

- repository fixtures cover dirty state, untracked files, active Git operations, base movement, pre-existing failures, managed paths, reusable code, dependency drift, and invalidated provisional assumptions;
- evidence refresh follows materiality and risk;
- benign, reconcilable, and base-invalidating drift are distinct;
- production changes cannot begin without a current exact-file plan;
- a bounded implementation amendment cannot conceal a program amendment;
- proposed implementation-owned names identify stable context and intention, and planning vocabulary is justified only by an implementation-governance role or durable domain concept.

**Integration checkpoint:** INC-005 is prepared using the implemented preparation and exact-file-plan workflow.

## INC-005 — Execution discipline, amendments, commits, and recovery

**Outcome:** Implement meaningful test-first slices and alternative verification, bounded approach autonomy, semantic naming enforcement, ownership boundaries, focused commits, amendment classification, and distinct recovery domains.

**Depends on:** Accepted INC-004.

**Acceptance:**

- test-first claims contain observed failure for the intended reason;
- non-behavioral work records an explicit alternative verification contract;
- unrelated cleanup and pre-existing user work remain untouched;
- roadmap-derived implementation names fail context-aware validation while implementation-governance artifacts and justified durable domain concepts remain valid;
- minor corrections, implementation amendments, program amendments, and contradictions classify correctly;
- source, data, deployment, and provider recovery remain distinct.

**Integration checkpoint:** One repository fixture advances through preparation and execution with a bounded evidence-backed amendment.

## INC-006 — Reviews, remediation, verification, and review packets

**Outcome:** Implement required review scopes, including contextual semantic naming review, risk predicates, truthful independence, material-finding contracts, remediation loops, fresh verification, and review-packet validation.

**Depends on:** Accepted INC-005.

**Acceptance:**

- requirements, architecture, and test-evidence reviews remain distinct;
- at most one bounded independent final reviewer is used for a coherent increment unless a material defect requires follow-up;
- raw reports are persisted before reconciliation;
- self-review is labelled non-independent with reduced assurance;
- semantic naming findings identify the affected implementation surface, context, intention, and any permitted governance or durable-domain basis;
- material findings include evidence, impact, confidence, remediation, and disposition;
- packets satisfy all canonical fields with exact commands and exact results.

**Integration checkpoint:** INC-006 itself receives the implemented packet and verification workflow before acceptance.

## INC-007 — Lean prompts, continuity, closure, and authority gates

**Outcome:** Generate minimal semantic briefs, create durable handoffs, revalidate resume state, manage full-mode continuation, reconcile programs, require closure approval, and gate later actions.

**Depends on:** Accepted INC-006.

**Acceptance:**

- generated briefs include all required semantic fields without copying workflow policy;
- stale or mismatched briefs and handoffs fail closed;
- a new conversation independently revalidates repository truth and renews conversational full-mode authority;
- final-increment acceptance does not close the program;
- closure approval and draft-PR, merge, release, deployment, migration, and provider decisions remain separate.

**Integration checkpoint:** The skill generates the valid INC-008 brief and handoff without closing ISP-001.

## INC-008 — Integrated pressure hardening and release pilot

**Outcome:** Run combined pressure, crash and resume, schema evolution, repository-backed pilot, packaging, documentation, and concision checks; repair only demonstrated material gaps.

**Depends on:** Accepted INC-007.

**Acceptance:**

- focused and full validation pass on the final shared tree;
- interruption and atomic-write scenarios recover or fail closed;
- schema evolution is compatible or produces an explicit unsupported-version stop;
- a disposable repository-backed pilot covers source capture through closure and the separate draft-PR decision;
- direct, indirect, incomplete, non-triggering, and unsupported-action requests are evaluated in fresh contexts;
- package validation, links, schemas, and artifact bindings pass;
- semantic naming coverage spans paths, symbols, commands, tests, fixtures, headings, schemas and observable identifiers, and generated paths without a global word blacklist;
- no prompt duplicates canonical workflow policy.

**Integration checkpoint:** Produce closure-readiness evidence without closing ISP-001.

## Separate program closure

After explicit INC-008 acceptance:

1. revalidate source, program, workspace, accepted packets, amendments, deferrals, and current repository state;
2. reconcile every requirement and approved amendment;
3. rerun program-level integration, structural, packaging, pressure, resume, and pilot validation;
4. block and reopen the smallest affected increment when a material gap remains;
5. otherwise produce the closure packet and stop for explicit closure approval;
6. ask separately about a draft pull request only after closure approval.

## Revision 2 amendment disposition

- SOURCE-002 incorporates the approved semantic implementation naming boundary.
- INC-001 remains accepted on its revision-1 evidence; revision 2 does not manufacture retroactive naming-pressure evidence.
- Semantic naming preparation, enforcement, review, and integrated validation are allocated to INC-004, INC-005, INC-006, INC-008, and closure respectively.
- INC-002 must expand the approved group-level traceability into source-located atomic requirements before any machine-completeness claim.

## Repository-specific risks

- DEC-007 selects the main checkout for the remaining ISP-001 implementation only. Revision 2 was captured from clean `main` at `62cf3fb444919c8ee2cc0eb97ee1e8ff8d28b53d`; future user work remains protected and must be revalidated before every plan or write.
- The repository has no pre-existing runtime, package manager, CI, or documentation conventions.
- The current bundled plugin validator requires identity metadata excluded by the approved scope; it is not an authoritative completion gate for INC-001.
- Bootstrap safeguards remain manual until their implementing increments are accepted.
- Group-level allocation is not machine-complete traceability; INC-002 must implement atomic source coverage and preserve the reduced-assurance distinction until validation passes.
- Static validation cannot prove agent activation, stopping, review independence, or resume behavior.
- State corruption and schema evolution require explicit fixtures.
- Marketplace installation, local plugin configuration, publication, push, pull request, release, and deployment remain separately authorized actions.
