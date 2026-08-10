# Repository Preparation

Use this procedure to prepare one repository-backed implementation increment. It observes and validates; it does not approve a plan, authorize a write, update program state, or create a commit.

## Prerequisites and Current Observation

Load the manifest and its logical roles. Bind the approved source and program revision, semantic requirements digest, current increment and lifecycle state, selected workspace, accepted handoff, approval mode, and separate action records.

Inspect the selected workspace with `repository_preparation.py inspect-repository --workspace <path> --base <commit>`. The inspection must resolve the repository root, branch, head, Git and common directories, selected-base ancestry, porcelain-v2 staged, modified, untracked, renamed, and conflicted paths, plus active operation markers. Stop on a detached head, Git error, timeout, conflict, active operation, path escape, or unsupported mandatory status record.

## Accepted and User-Owned Work

Treat every pre-existing staged, unstaged, untracked, conflicted, accepted, or otherwise user-owned path as preserved work. Do not clean, reset, restore, stash, overwrite, or absorb it into the increment.

A proposed overlap is valid only when the exact-file plan names the path, identifies its accepted owner, and states a preserve-or-extend disposition. A managed or generated path also needs its owning mechanism and exact regeneration or verification command. An unowned managed path or unaccepted dirty overlap is a stop.

## Git Discovery

Use only read-only argument-vector Git commands with an explicit working directory, captured byte output, a bounded timeout, and `shell=False`. Parse porcelain `-z` records before decoding filesystem paths so whitespace, tabs, newlines, rename pairs, and filesystem-representable byte names remain intact. Never print file contents, environment variables, credentials, or tokens.

## Qualitative Drift

Compare the current inspection with the prepared repository, path, branch, base, head, dirty inventory, assumptions, protected contracts, relevant failures, dependency surfaces, and reusable mechanisms.

- `base-invalidating`: a binding or head moved; the base is no longer an ancestor; a conflict or operation is active; protected or unaccepted work overlaps; requirements or protected contracts changed; a new relevant failure appeared; or material dependency compatibility is absent. Stop and refresh preparation or escalate to a program decision.
- `reconcilable-relevant`: relevant files, manifests, reusable mechanisms, evidence, or provisional assumptions changed without invalidating authority, ownership, protected contracts, or compatibility. Refresh evidence and the exact-file plan under the current gate.
- `benign`: changes are unrelated, non-overlapping, and do not affect current assumptions or contracts. Record them and continue.

Never relabel an unchanged unrelated baseline failure as an increment regression. Never ignore a new relevant failure. Record reusable candidates and the selected reuse or explicit rationale before adding an abstraction.

## Baseline, Reuse, and Evidence Records

Record the baseline command, result, relevant inputs, pre-existing failures, and which failures are relevant to the current outcome. Record reusable candidates, the selected mechanism, and the reason.

Refresh official evidence when the work materially changes a dependency or runtime, provider or integration, version-sensitive API, authentication or authorization, security or privacy, payments, persistence or migration, deployment or provider state, compatibility or security assumption, or externally defined public contract. Record source locator, access date, applicable version and configuration, supported claims, risk domain, reuse basis, and remaining uncertainty.

Installed but untouched surfaces are not material. Unavailable official evidence blocks high-risk work. Lower-risk prior evidence may be reused only when version, configuration, and assumptions match exactly and both the access failure and residual uncertainty are recorded.

## Increment Shape

Require one coherent outcome, traceable requirements, explicit acceptance criteria, meaningful verification, coherent rollback or recovery, and a valid resulting repository. Do not bundle unrelated risk domains or depend on safeguards that do not yet exist. Reviewability is qualitative; file counts and line counts are not substitutes for coherence.

## Amendment Boundary

An authoritative contradiction stops. Any change to a requirement, acceptance criterion, scope, user-visible behavior, security or privacy obligation, protected contract, data ownership, irreversible behavior, risk posture, dependency sequence, material sequence, or user-review cadence is a program amendment regardless of its proposed label.

A bounded implementation amendment requires concrete evidence, preserved obligations, no unresolved user-owned decision, and credible reversal or recovery. A minor correction is limited to paths, helper selection, or test convention and cannot change a program dimension.

## Semantic Naming and Compatibility

Inventory every proposed path, symbol, command, test or fixture, heading, schema or identifier, and generated path. Each entry needs stable context, intention, origin, planning-term basis, basis owner, compatibility class, and compatibility disposition.

Coordinate-shaped names such as a phase, task, step, wave, sprint, priority, or ticket plus an identifier require a specific implementation-governance artifact or durable domain concept. A word match alone is not a rejection. Existing public, persisted, generated, or externally consumed names require an explicit compatibility or migration disposition; do not silently preserve, alias, or rename them.

## Exact-File Plan Contract

Create the exact-file plan just in time from current repository evidence. Bind the program, revision, increment, source, program and semantic digests, workspace path, branch, base and head, and preparation evidence. Include global constraints; requirements and acceptance; non-empty create, modify, and preserve maps; interfaces; semantic naming inventory; test-first or alternative verification slices; exact commands and expected evidence; review predicates; logical commit boundaries; rollback and recovery; risks, exclusions, and amendment rules; and the required approval gate.

Reject a missing, symlinked, stale, digest-mismatched, or structurally incomplete plan. A content-valid plan is not write authority.

## Approval and Action Gate

Before production changes, require an exact plan approval bound to the current tuple and a separate action authorization naming the requested writes and verification. Approval mode controls interruption and diff acceptance only. Use the state-authority procedure for lifecycle and append-only governance writes.

## Validation Commands

Run the smallest applicable checks first:

```bash
python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-preparation <program-root> --workspace <path> --base <commit>
python3 skills/implementing-staged-plans/scripts/repository_preparation.py validate-plan <program-root> --workspace <path> --base <commit> --preparation <path> --plan <path>
python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Record commands, relevant inputs, exit status, and concise output. Static validation does not prove live integration, deployment, publication, production safety, accessibility, translation quality, or external provider behavior.

## Hard Stops

Stop for ambiguous repository identity, stale or contradictory authority, selected-workspace mismatch, base-invalidating drift, unowned overlap, unavailable required evidence, a program amendment, missing safeguards, missing plan approval, missing action authorization, or any action outside the named increment. Do not infer commit or external-action authority.

## Bounded Result

Return the inspected repository tuple, protected dirty inventory, drift and evidence decisions, increment-shape result, amendment classification, naming inventory result, exact plan path and digest, verification evidence, remaining uncertainty, current lifecycle state, next legal action, and mandatory stop.
