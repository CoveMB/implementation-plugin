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

For an approved exact-file plan plus its expected execution grant, persist in this order:

1. append or adopt the exact approved event;
2. apply or adopt the approval-driven status transition;
3. append or adopt each exact action-authorization record.

The status transition records the approval event and checkpoint identifier, then binds the expected execution-authorization identifier and scope. It does not claim that the later JSON Lines append already exists. Repository preparation therefore validates the bound grant itself before any implementation write.

Each file operation is atomic, but the sequence is not a multi-file transaction. A failure returns completed steps, exact file receipts, the failed step, and `requires_retry`. Preserve partial records. On retry, adopt byte-for-byte identical records only. An already-applied transition must match the complete authority object, expected execution identifier and scope, plan-state updates, previous lifecycle state, checkpoint, event, sequence, and prior digest. Reject every substitution, identifier conflict, or digest conflict. Never delete, roll back, duplicate, or silently skip a partial write.

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
