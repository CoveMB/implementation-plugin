# Program Authority

Use this procedure only after the front door has established current repository authority and the requested action is permitted. It governs source registration, complete requirement decomposition, outcome-program creation and revision, traceability, and initial program approval.

## Establish prerequisites

Before writing anything:

1. Resolve the repository and program root from persisted records.
2. Confirm the selected worktree, branch, base, head, and pre-existing dirty state.
3. Load the manifest through its logical roles.
4. Confirm separate authority for the proposed capture, program, traceability, approval, and state writes.
5. Preserve unrelated work and every immutable source, accepted packet, approval, and prior-revision evidence record.

Stop on a missing, stale, contradictory, ambiguous, or unauthorized binding.

## Capture exact source evidence

Hash the candidate source as bytes and obtain explicit confirmation of that digest. Capture only a regular non-symlink file into absent destinations whose existing parents resolve inside the program root. Use the capture command with explicit source identity, expected digest, access method, snapshot path, and metadata path.

The capture implementation streams the source once, verifies its digest, and finalizes same-filesystem temporary files with non-overwriting hard links. It never replaces an existing destination. If snapshot finalization succeeds but metadata finalization fails, preserve and report the partial evidence; do not overwrite it or advance program state.

The immutable snapshot is authority. A mutable working document, conversation, or handoff is not a substitute.

## Inspect the repository read-only

Before decomposition, inspect relevant implementation, tests, documentation, manifests, schemas, supported versions, and repository instructions. Identify existing behavior and canonical owners without changing them. Record verified facts separately from interpretations and unresolved questions.

## Partition and classify the full source

Partition every physical source line exactly once, including headings, context paragraphs, and blank lines. For each ordered unit, record its inclusive line range and digest over the exact source bytes.

Classify each unit as either:

- `requirement`, with every atomic requirement identifier supported by the unit; or
- `context`, with no requirement identifiers and a concrete rationale.

Line partitioning and digest checks provide mechanical coverage evidence. They do not prove that semantic classification is correct. A human must review every unit in source order and reconcile normative keywords, bullets, numbered contracts, exceptions, defaults, and negative obligations.

Partial extraction must retain an incomplete status. Never use an empty record, broad group, or sampled review to claim complete extraction.

## Split atomic requirements

Create one stable semantic identifier for each independently dispositionable obligation. Split joined statements when one part could be accepted, deferred, amended, rejected, or verified independently.

Each atomic record must include:

- its approved requirement group;
- one or more requirement-classified source units and an exact human-readable locator;
- a normalized requirement that preserves the source meaning;
- observable acceptance criteria;
- allocations to outcome part, current or provisional task, and increment;
- current disposition;
- decision, implementation, and verification evidence lists.

Use names that communicate durable context and intention. Sequence-derived or project-specific planning labels belong only in repository governance records, not reusable package surfaces.

## Decompose into outcome programs

Organize atomic requirements into reviewable outcomes with explicit acceptance, dependencies, risks, and boundaries. Keep distant technical files and commands provisional until the relevant stage is prepared. Do not turn early uncertainty into invented implementation detail.

Every requirement must be allocated. A group-level allocation may guide preparation, but it cannot substitute for the source-located atomic inventory required for a machine-completeness claim.

## Elaborate progressively

Make the current outcome exact enough to execute and review. Preserve later outcomes semantically while deferring repository-specific file choices. When new evidence changes an approved outcome, acceptance condition, sequence, public contract, authority, or risk posture, stop for a recorded program amendment. Ordinary implementation detail may be elaborated within approved bounds.

## Revise without rewriting history

A new source or program revision receives new immutable paths and digests. Its traceability declares the prior source, program, traceability, and accepted evidence records it preserves. Validate every declared prior digest.

Never mutate a prior source, program, approval, accepted packet, or evidence record. A prior approval is stale for a changed source digest, program digest, semantic-requirements digest, or revision.

## Publish before approval

A new `implementation-program-manifest/v2` proposal is complete but unapproved. Its immutable manifest owns regular non-symlink paths for approvals, action authorizations, increment grants, rollovers, block resolutions, workspace, and status. It also owns `implementation-increment-storage/v1` and `implementation-closure-storage/v1` descriptors. The rollover and block-resolution ledgers begin empty, closure files remain absent until a final increment allocates them, and the manifest contains neither mutable `program_status` nor legacy `current_increment` data.

Proposal validation requires complete source, program, and traceability bindings; empty authority ledgers; the unapproved workspace proposal; and sequence-zero `awaiting-program-approval` / `not-started` status. A reserved future approval identifier is not approval. Approved validation adds the exact event requirement below. Unknown validation modes fail closed.

The closure resolver derives reconciliation and packet paths only from the immutable descriptor. It rejects missing or extra descriptor keys, absolute or escaping roots, separators in filenames, duplicate paths, symlinked ancestors, and non-regular existing entries. Legacy manifests continue to use their accepted closure logical roles.

## Bind initial program approval

Before implementation, require one explicit approved event that exactly binds:

- program identity and revision;
- source identity and digest;
- program digest;
- semantic-requirements digest;
- approval mode.

Reject a missing, non-approved, stale, or conflicting event. Approval mode controls interruption and diff acceptance; it does not authorize writes or consequential external actions.

## Validate

From the repository root, run:

```bash
python3 skills/implementing-staged-plans/scripts/program_authority.py validate-program path/to/program-root
```

Production callers select proposal or approved validation explicitly. The CLI remains approved validation by default.

Use `--allow-incomplete` only during authorized preparation before human acceptance. It continues to enforce path, source, program, partition, atomic-record, and prior-evidence integrity while explicitly withholding final completeness and approval claims.

## Hard stops

Stop without advancing state when:

- a source, program, traceability, semantic, approval, or prior-evidence digest differs;
- any managed path escapes the program root or contains a symlink;
- any source line is missing, duplicated, overlapped, reordered, or incorrectly digested;
- any requirement lacks atomic traceability, acceptance, allocation, or disposition;
- semantic review is incomplete;
- approval is absent, stale, rejected, or conflicting;
- requested writes or effects exceed separate action authority.

## Return a bounded result

Report the verified source and program bindings, source-unit and atomic counts, semantic digest, approval result, preserved prior evidence, incomplete or reduced-assurance conditions, current legal state, next legal action, and mandatory stop. Do not imply that structural validation proves semantic correctness or acceptance.
