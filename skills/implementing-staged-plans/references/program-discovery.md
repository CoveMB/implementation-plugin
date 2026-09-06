# Program Discovery

Use this read-only procedure before creating or resuming an implementation program. It discovers authority; it never creates directories, captures a source, changes state, or grants an action.

## Search Boundary

Provide the exact target repository. If the request supplies a manifest, validate and use only that path. Otherwise consider exact manifest paths declared by applicable repository instructions and direct children matching `implementation-programs/*/manifest.json`. Do not recursively search arbitrary repository paths. A directory without a valid manifest and persisted bindings is not a program.

Every repository, manifest, program root, and manifest-owned logical role must remain in its declared boundary and be a regular non-symlink path. Invalid JSON, path escape, symlink traversal, missing roles, changed digests, or contradictory manifest and status state fails closed.

## Deterministic Classification

- No manifests: return `new-program-bootstrap-possible`, require the authoritative source-plan path, and perform no program write. A supplied source plan must be a regular non-symlink file; validation returns `new-program-bootstrap-ready` without creating authority.
- A manifest-v3 proposal at sequence zero uses proposal validation. An empty proposal returns `program-setup-ready`; an exact setup-only or partial non-reused pre-activation source-gate prefix returns `source-gate-approval-ready` with the first missing gate's canonical recap; an exact complete gate or derived approval prefix returns `program-activation-retry-ready`. Completed sequence one returns `first-increment-start-ready` for the semantic fresh-task handoff. A v2 proposal retains `program-activation-ready` and its exact launch-prompt recovery route. Out-of-order, duplicate, unrelated, stale, mixed-family, or divergent prefixes fail closed.
- Approved new-program status selects approved validation. Discovery inspects manifest-allocated plan, baseline, review, acceptance, closure, approval, authorization, and grant prefixes before applying generic state rejection. Exact controlled prefixes route to the corresponding `*-retry-ready` transaction; unsafe, malformed, unexpected, or state-incompatible artifacts stop without repair.
- A new-model accepted status with an exact `accept-stop` binding returns `accepted-stop`. Closure files are a retryable preparation prefix. Complete closure preparation returns `closure-approval-ready`; an exact approval prefix returns `closure-approval-retry-ready`. Closed and superseded programs are non-controlling terminal history.
- A byte-exact immediate rollover prefix returns `increment-continuation-retry-ready` before navigation or `increment-rollover-retry-ready` after navigation begins. A later accepted-state prefix returns the corresponding `accepted-state-*` route. The same exact prompt adopts the prefix; divergence returns the domain-specific continuation recovery route. A completed successor status resumes normally.
- A valid sink-authored blocked status returns `blocked-recovery-ready` and reports only its recorded prior program and increment states. An exact resolution action or ledger prefix returns `blocked-resolution-retry-ready`; a completed resumed status returns ordinary `resume`. Malformed context, changed bound evidence, out-of-order records, or divergent prefix bytes return `blocked-recovery-required` without repair.
- Classify caller intent with `classify_requested_program_operation`. The implemented front door supports `create`, `activate`, and typed `continue` routing, including exact continuation and blocked-recovery prefixes. A live `revise` or `supersede` intent returns `program-revision-workflow-required`; `cancel` and every other mutation return `unsupported-program-mutation`. Classification is pure and always stops before any unsupported live write.
- One valid legacy `active` or `blocked` program: select it, inspect its bound workspace afresh, validate program and state authority, and build resume expectations from the manifest, persisted status, and fresh observation. An accepted legacy automatic mode stops at `legacy-rollover-upgrade-required` before successor writes. Do not request the original documentation-plan path.
- More than one valid `active` or `blocked` program: return sorted manifest candidates and stop for human selection.
- Only legacy `closed` programs: return the sorted closed manifests and stop until the user states new-program or closed-program inspection intent. Only new-model `closed` or `superseded` programs return `terminal-programs` and require explicit new-program or terminal-inspection intent.
- Any invalid candidate or unsupported controlling state: return the evidence and stop. Do not choose around it.

An explicit valid manifest takes precedence over convention and instruction candidates. A selected resumable program does not inherit write, approval, commit, installation, cleanup, external-action, or publication authority from discovery.

The legacy caller-authored rollover writer is quarantined at its persistence entry point and always returns `legacy-rollover-upgrade-required`. Accepted legacy state remains readable; historical closed and superseded records remain terminal evidence. Read compatibility does not reactivate an unsafe writer.

## Resume Evidence

Build expected program, source, semantic, status, increment, workspace, plan, and dirty-state bindings independently from the discovered manifest and fresh Git observation. Compare submitted resume evidence with those expectations. Structural bundle validation may validate a submitted record, but it must not present a record-versus-itself comparison as repository-backed resume validation.

## Command

From the repository root:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_discovery.py discover .
```

Add `--manifest <path>` for explicit selection, repeat `--instruction-manifest <path>` for exact instruction-declared locations, or add `--source-plan <path>` only when no manifest exists. Output is deterministic JSON. Exit `0` identifies a ready read-only route; exit `1` identifies a mandatory stop or missing human input; argument errors exit `2`.

## Bounded Result

Return the selected manifest or candidate lists, persisted program state, exact legacy resume expectations when applicable, material issues, required human input, one next legal action, and the truthful stop requirement. Discovery never adopts, deletes, overwrites, appends, or replaces transaction bytes. Continue only through the separately authorized typed procedure for the returned action.
