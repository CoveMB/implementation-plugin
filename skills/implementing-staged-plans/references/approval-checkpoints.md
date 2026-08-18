# Approval Checkpoints

Use this procedure to reduce repeated prompts when several decisions are already concrete and share one stable authority binding. It changes presentation and ordered persistence only. It does not broaden what the user authorizes.

The mechanical boundary is [`approval_checkpoint.py`](../scripts/approval_checkpoint.py). It builds and resolves typed checkpoint items, classifies every declared action, adopts exact existing records, and persists the plan-approval sequence with retry receipts.

## Admit Only One Stable Binding

Every checkpoint item must bind the same program identifier and revision, source identifier and digest, program and semantic digests, increment, brief and exact-file-plan digests, approval mode, and workspace path, branch, base, and head. Missing fields block the item. A different tuple belongs to a different stage and must not enter the checkpoint.

Inspect existing approval and authorization logs before presenting the checkpoint. Adopt one exact existing positive record as satisfied. The same event or authorization identifier with different content is a conflict and stops the checkpoint. Do not manufacture a replacement identifier to evade the conflict.

## Present One Checkpoint, Keep Explicit Choices

Present pending items together only after the full binding is stable. Label each item as approval or action authority, state its exact scope, and show its risk class. Require an explicit decision for every pending item:

- approval: approve or reject;
- action authority: authorize or deny.

Do not parse consent from free-form prose. Do not apply one answer to every item. A local commit remains a separately explicit item even when it appears in the same checkpoint. High-consequence actions are blocked requirements: construction, resolution, and persistence must not materialize their grants, and this procedure never performs them.

The exhaustive action classes are:

- routine local: program-artifact write, workspace modification, local verification;
- explicit local: workspace creation and local commit;
- bounded external: draft pull-request creation;
- high consequence: merge, publish, release, deploy, migrate, destructive operation, provider mutation, and external-state mutation.

Unknown actions fail closed.

## Persist in Retry-Safe Order

Compound persistence is available only with `implementation-program-status/v2`. Keep accepted v1 records unchanged and dual-read them elsewhere.

For a new-model program in `approval:standard`, the typed plan materializer persists in exactly this order:

1. append or adopt the exact approved event;
2. create or adopt the execution baseline;
3. append or adopt the exact plan-bound action-authorization record;
4. replace or adopt the `authorized` status last.

The `approval:pre-approve` and `approval:full-increment` modes omit only the exact-plan question and approval event. They still create or adopt the exact plan, execution baseline, plan-bound action authorization, and `authorized` status in that order. The status binds records that already exist; it never claims a future append.

The generic compound-checkpoint persistence API remains a legacy-program compatibility path. It rejects new-model manifests with `new-program-plan-materialization-required`; it cannot restore the former approval → status → action ordering.

Each file operation is atomic, but the sequence is not a multi-file transaction. Preserve partial records. New-model discovery reconstructs the controlling exact-plan transaction and classifies only byte-identical ordered prefixes as retry-ready. A divergent plan, approval, baseline, action record, or status returns the corresponding recovery-required stop. Never delete, roll back, duplicate, or silently skip a partial write.

## Preserve Narrow Gates

Combining a checkpoint does not lift these boundaries:

- cross-stage or unstable bindings;
- user-owned product decisions;
- local commit authority;
- push or remote-branch creation;
- merge, publication, release, deployment, migration, destructive work, permissions, provider mutation, or other external-state changes;
- another increment, another conversation, or another workspace tuple.

Post-closure housekeeping remains proposal-only. It may report a verified dry-run and mandatory stop; no cleanup executor is added by this procedure.

## Validate

Run focused validation without bytecode output:

```bash
rtk env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_approval_checkpoint tests.test_state_authority tests.test_repository_preparation -v
```

Passing checks prove the supplied local records meet the deterministic contracts. They do not prove semantic consent, user identity, provider state, or that any external action occurred.
