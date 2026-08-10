# Program Discovery

Use this read-only procedure before creating or resuming an implementation program. It discovers authority; it never creates directories, captures a source, changes state, or grants an action.

## Search Boundary

Provide the exact target repository. If the request supplies a manifest, validate and use only that path. Otherwise consider exact manifest paths declared by applicable repository instructions and direct children matching `implementation-programs/*/manifest.json`. Do not recursively search arbitrary repository paths. A directory without a valid manifest and persisted bindings is not a program.

Every repository, manifest, program root, and manifest-owned logical role must remain in its declared boundary and be a regular non-symlink path. Invalid JSON, path escape, symlink traversal, missing roles, changed digests, or contradictory manifest and status state fails closed.

## Deterministic Classification

- No manifests: return `new-program-bootstrap-possible`, require the authoritative source-plan path, and perform no program write. A supplied source plan must be a regular non-symlink file; validation only makes the bootstrap route ready.
- One valid `active` or `blocked` program: select it, inspect its bound workspace afresh, validate program and state authority, and build resume expectations from the manifest, persisted status, and fresh observation. Do not request the original documentation-plan path.
- More than one valid `active` or `blocked` program: return sorted manifest candidates and stop for human selection.
- Only `closed` programs: return the sorted closed manifests and stop until the user states new-program or closed-program inspection intent.
- Any invalid candidate or unsupported controlling state: return the evidence and stop. Do not choose around it.

An explicit valid manifest takes precedence over convention and instruction candidates. A selected resumable program does not inherit write, approval, commit, installation, cleanup, external-action, or publication authority from discovery.

## Resume Evidence

Build expected program, source, semantic, status, increment, workspace, plan, and dirty-state bindings independently from the discovered manifest and fresh Git observation. Compare submitted resume evidence with those expectations. Structural bundle validation may validate a submitted record, but it must not present a record-versus-itself comparison as repository-backed resume validation.

## Command

From the repository root:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/program_discovery.py discover .
```

Add `--manifest <path>` for explicit selection, repeat `--instruction-manifest <path>` for exact instruction-declared locations, or add `--source-plan <path>` only when no manifest exists. Output is deterministic JSON. Exit `0` identifies a ready read-only route; exit `1` identifies a mandatory stop or missing human input; argument errors exit `2`.

## Bounded Result

Return the selected manifest or candidate lists, persisted program state, exact resume expectations when applicable, material issues, required human input, next legal action, and stop requirement. Continue only through the separately authorized focused procedure for that next action.
