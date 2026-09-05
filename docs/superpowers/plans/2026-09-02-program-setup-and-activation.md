# Program Setup and Activation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement manifest/status v3 so a creation-only proposal is approved through one readable setup decision, activation stops before execution authority, and a fresh task starts the first increment through the complete typed authority chain.

**Architecture:** Preserve every manifest/status v1 and v2 route unchanged. Add one focused `program_setup.py` module for pure v3 semantic, recap, adapter, and source-gate contracts; extend existing publication, activation, state-validation, discovery, and lifecycle owners through exact-schema dispatch. Reuse current compare-and-swap, no-overwrite, and status-last primitives rather than introducing a new orchestration layer.

**Tech Stack:** Python 3 standard library, `unittest`, canonical JSON and SHA-256, existing filesystem compare-and-swap helpers.

**Spec:** `docs/superpowers/specs/2026-08-23-program-setup-and-activation-design.md`

## Global Constraints

- Preserve current manifest/status v1 and v2 bytes, readers, writers, prompt transport, recovery behavior, and next legal actions.
- New proposals use `implementation-program-manifest/v3` and `implementation-program-status/v3`; exact schema dispatch must reject cross-family artifacts.
- Setup and source-gate adapters accept only current direct top-level user evidence represented as typed values; repository code does not claim to authenticate human identity or comprehension.
- Activation ends at `active` / `awaiting-first-increment` and creates no grant, exact plan, execution baseline, action authorization, progress record, or product change.
- First-increment start writes grant and status before exact-plan preparation and retains the existing public `prepare_exact_plan(...)` and `materialize_exact_plan(...)` signatures.
- Every durable transaction remains deterministic, no-overwrite, retry-safe, and status-last.
- Do not implement v4 expanded operations, v5 progress cursors, installation, cache synchronization, consuming-program repair, Git publication, or external actions.
- Do not commit during this run; commit authority was not granted.

---

### Task 1: Repair the isolated activation import boundary

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Test: `tests/test_program_activation.py`

**Interfaces:**
- Consumes: the current lazy `program_rollover` dependency used by `validate_state_authority(...)` and successor baseline construction.
- Produces: `_preload_activation_dependencies() -> None`, called before the first durable activation write.

- [x] **Step 1: Confirm the existing isolated regression fails**

Run:

```bash
python3 -m unittest tests.test_program_activation
```

Expected: the activation cases fail with `No module named 'program_rollover'` when another test module has not populated `sys.modules`.

- [x] **Step 2: Implement one import preflight at the transaction boundary**

Use `importlib.util.spec_from_file_location()` only when normal sibling import cannot resolve, register the module before executing it, and call the preflight after read-only transaction construction but before appending the first approval. Preserve the existing CLI import route.

- [x] **Step 3: Verify the isolated suite is green**

Run:

```bash
python3 -m unittest tests.test_program_activation
```

Expected: all 16 tests pass without another test module's import order.

---

### Task 2: Add closed v3 setup, recap, adapter, and source-gate values

**Files:**
- Create: `skills/implementing-staged-plans/scripts/program_setup.py`
- Modify: `skills/implementing-staged-plans/scripts/validate_package.py`
- Test: `tests/test_program_setup.py`
- Test: `tests/test_package_validation.py`

**Interfaces:**
- Produces: `validate_setup_semantics(program_root, manifest, workspace, traceability) -> list[str]`.
- Produces: `render_setup_recap(program_root) -> str` and `setup_recap_checkpoint(program_root) -> dict[str, object]`.
- Produces: `adapt_setup_decision(program_root, response, *, role, provenance, checkpoint=None) -> dict[str, object]`.
- Produces: `render_increment_start_handoff(program_root) -> str` and `adapt_increment_start_intent(program_root, prompt, *, role, provenance) -> dict[str, object]`.
- Produces: `render_source_gate_recap(program_root, gate_id, protected_subject) -> str`, `adapt_source_gate_decision(...) -> dict[str, object]`, `persist_source_gate_decision(...)`, and `source_gate_satisfaction(...) -> dict[str, object]`.

- [x] **Step 1: Write failing pure-contract tests**

Cover canonical semantic identity; every required readable recap fact; deterministic recap checkpoint; direct affirmative/negative/ambiguous/conditional/quoted/retrieved/stale/replayed/malformed decisions; renderer-byte invalidation; supported trigger ownership; unsupported response semantics; stable gate ordering; exact checkpoint reuse; and acyclic satisfaction evidence.

Use literal expected values and real temporary program trees. Each test names the production mutation it catches.

- [x] **Step 2: Run the new tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_program_setup
```

Expected: import failure because `program_setup.py` does not exist.

- [x] **Step 3: Implement the smallest pure v3 contract module**

Use closed field sets, canonical JSON, literal schema constants, normalized repository-relative POSIX paths, sorted unique collections, and existing managed-path resolvers. Keep conversation classification explicit: only `role == "user"`, `provenance == "direct-user-message"`, and an unconditional affirmative produces a positive typed decision. Negative and non-authoritative results produce no durable record.

- [x] **Step 4: Register and verify the module**

Run:

```bash
python3 -m unittest tests.test_program_setup tests.test_package_validation
```

Expected: both modules pass.

---

### Task 3: Add v3 authority validation and immutable proposal publication

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/program_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/program_bootstrap.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Modify: `tests/program_bootstrap_support.py`
- Test: `tests/test_program_authority.py`
- Test: `tests/test_program_bootstrap.py`
- Test: `tests/test_program_bootstrap_lifecycle.py`

**Interfaces:**
- Produces: exact manifest-v3 proposal/approved validation modes with `setup_activation_decision` and `source_gate_decisions` roles.
- Produces: `implementation-program-proposal-request/v2` and `implementation-proposal-publication-owner/v2` with one closed `publication_freshness` value.
- Preserves: v1 request/owner validation and all completed historical publication roots.

- [x] **Step 1: Freeze legacy proposal and activation bytes**

Add immutable golden fixture assertions for the existing v2 proposal, launch command, and every partial/completed v2 activation prefix before shared writers change.

- [x] **Step 2: Write failing v3 authority and publication tests**

Cover exact `setup_semantics` validation, proposal absence/approved presence of the setup record, empty source-gate ledger, immutable candidate capture, request/owner freshness binding, instruction-declared manifest enumeration, freshness rechecks before final-root reservation and manifest-last publication, staging inventory revalidation, exact prefix adoption, multiple incomplete-root rejection, and completed-root nonblocking behavior.

- [x] **Step 3: Run targeted tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_program_authority tests.test_program_bootstrap tests.test_program_bootstrap_lifecycle
```

Expected: v3 assertions fail while legacy assertions remain green.

- [x] **Step 4: Extend validation and publication by exact schema**

Capture candidate bytes once into an immutable path/bytes/digest map and use that map for request, owner, staging, and final writes. Factor canonical instruction-source and manifest enumeration from discovery so publication and recovery compare the same closed freshness value. Keep v1 publication logic on its current route.

- [x] **Step 5: Verify targeted authority/publication suites**

Run the command from Step 3. Expected: all targeted tests pass.

---

### Task 4: Implement setup activation and fresh-task first start

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/program_launch.py`
- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Test: `tests/test_program_launch.py`
- Test: `tests/test_program_activation.py`
- Test: `tests/test_program_setup.py`

**Interfaces:**
- `activate_program(program_root, submitted_value, observation)` retains legacy string prompts for v2 and accepts only a typed setup decision for v3.
- Produces: `start_first_increment(program_root, start_intent, observation) -> ActivationReceipt`.
- Preserves: `prepare_exact_plan(program_root, plan_bytes, observation)` and `materialize_exact_plan(program_root, submitted_prompt, observation)`.

- [x] **Step 1: Write failing transaction tests**

Cover typed-decision binding, negative no-write behavior, setup record → activation gates → program approval → workspace approval → status-last ordering, failure injection and exact retry after each prefix, semantic handoff, typed first-start intent, start gates → v2 grant → sequence-two status-last ordering, and complete plan authorization stopping before execution.

- [x] **Step 2: Verify RED**

Run:

```bash
python3 -m unittest tests.test_program_setup tests.test_program_launch tests.test_program_activation
```

- [x] **Step 3: Add exact-schema activation routing**

Keep the existing v2 activation function byte-compatible behind a private legacy route. For v3, build every record fully in memory, resolve every dependency before the first write, create/adopt in deterministic order, and replace only the expected prior status digest. Setup activation must return `awaiting-first-increment`; first start must return `preparing` before exact-plan preparation.

- [x] **Step 4: Verify GREEN**

Run the command from Step 2. Expected: all targeted tests pass.

---

### Task 5: Route v3 state authority and fresh discovery

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Modify: `skills/implementing-staged-plans/scripts/program_discovery.py`
- Test: `tests/test_state_authority.py`
- Test: `tests/test_program_discovery.py`

**Interfaces:**
- Produces: exact sequence-zero setup-recap route, sequence-one semantic first-start route, and sequence-two existing preparation route.
- Produces: targeted cross-family substitution/addition rejection without rejecting unrelated legal extensions.

- [x] **Step 1: Write failing schema-routing and recovery tests**

Cover v3 setup/start states, partial activation/start prefixes, stale/wrong/downgraded grants and bindings, exact next gate selection, mixed-family rejection in both directions, and every frozen v1/v2 fixture's unchanged discovery and next legal action.

- [x] **Step 2: Verify RED**

Run:

```bash
python3 -m unittest tests.test_state_authority tests.test_program_discovery
```

- [x] **Step 3: Implement exact-schema routers before generic validation**

Dispatch on manifest and status schema before interpreting fields. Treat v3 proposal and waiting states as non-product authority. Reuse existing legacy route functions without optional-field fallthrough.

- [x] **Step 4: Verify GREEN**

Run the command from Step 2. Expected: both suites pass.

---

### Task 6: Bind supported source gates at existing lifecycle owners

**Files:**
- Modify: `skills/implementing-staged-plans/scripts/program_activation.py`
- Modify: `skills/implementing-staged-plans/scripts/program_rollover.py`
- Modify: `skills/implementing-staged-plans/scripts/blocked_recovery.py`
- Modify: `skills/implementing-staged-plans/scripts/diff_disposition.py`
- Modify: `skills/implementing-staged-plans/scripts/program_closure.py`
- Modify: `skills/implementing-staged-plans/scripts/state_authority.py`
- Test: `tests/test_program_setup.py`
- Test: existing owner-specific test modules for each changed writer.

**Interfaces:**
- Consumes: `source_gate_satisfaction(program_root, trigger, protected_subject, ...)`.
- Produces: the identical sorted satisfaction value embedded in each protected v3 receipt, authorization, operation event, or status.

- [x] **Step 1: Write one failing causal test per owning boundary**

Cover `before-program-activation`, `before-increment-start` for first and successor grants, `before-action-authorization`, `before-product-execution`, `before-review`, `before-diff-disposition`, and `before-program-closure`. Each test must prove the protected write cannot occur with missing, extra, stale, reordered, self-referential, or digest-mismatched satisfaction.

- [x] **Step 2: Verify RED in the owner suites**

Run:

```bash
python3 -m unittest tests.test_program_activation tests.test_program_rollover tests.test_execution_discipline tests.test_program_review tests.test_diff_disposition tests.test_program_closure
```

- [x] **Step 3: Add narrow v3 branches at each canonical writer**

Do not add a generic scheduler. Each writer declares its literal trigger and protected subject, validates the durable ascending decision prefix, builds one acyclic satisfaction, embeds it before computing the protected artifact digest, and leaves v1/v2 records unchanged.

- [x] **Step 4: Verify GREEN in the owner suites**

Run the command from Step 2. Expected: all owner suites pass.

---

### Task 7: Update the skill contract and run complete causal regression

**Files:**
- Modify: `skills/implementing-staged-plans/SKILL.md`
- Modify: `skills/implementing-staged-plans/references/program-authority.md`
- Modify: `skills/implementing-staged-plans/references/program-discovery.md`
- Modify: `docs/workflows.md`
- Test: `tests/test_program_setup.py`
- Test: `tests/test_front_door_contract.py`
- Test: `tests/test_distribution_documentation.py`
- Test: `tests/test_multi_increment_lifecycle.py`
- Test: `tests/test_integrated_pressure.py`

**Interfaces:**
- Produces: one readable setup question, semantic fresh-task start, separate exact-plan behavior, explicit claim limits, and links to canonical owners.

- [x] **Step 1: Write failing application-path contract tests**

Cover explicit direct creation intent plus exact source path, proposal-only creation authority, no machine payload in setup/gate/handoff output, no inferred external authority, a complete readable-setup-to-plan-authorization path stopping before product execution, and a successor start gate in both continuation domains.

- [x] **Step 2: Update front-door and canonical references**

Document v3 only where that surface owns behavior; link elsewhere. State that conversation role and comprehension are controller trust assumptions, not repository proofs. Preserve v1/v2 guidance as schema-specific compatibility behavior.

- [x] **Step 3: Run package and full deterministic verification**

Run:

```bash
python3 skills/implementing-staged-plans/scripts/validate_package.py
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Expected: package validation and all tests pass; `git diff --check` reports no errors.

- [x] **Step 4: Re-read the design and inspect the final diff**

Confirm every success criterion is implemented, every non-goal remains absent, public exact-plan signatures are unchanged, no new dependency or speculative v4/v5 abstraction was introduced, and the four user-owned design files remain byte-identical.
