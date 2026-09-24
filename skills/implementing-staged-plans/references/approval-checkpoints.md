# Approval Checkpoints

Use this procedure to reduce repeated prompts when several decisions are already concrete and share one stable authority binding. It changes presentation and ordered persistence only. It does not broaden what the user authorizes.

The mechanical boundary is [`approval_checkpoint.py`](../scripts/approval_checkpoint.py). It builds and resolves typed checkpoint items, classifies every declared action, adopts exact existing records, and persists the plan-approval sequence with retry receipts.

## Combined program start

New manifest-v3 proposals declare `program_start_contract: combined-start/v1`. Its absence selects the historical setup-only route; malformed values and older manifest families reject the marker. This dedicated initial contract is separate from the generic compound checkpoint below.

1. Revalidate the proposal, source, workspace, protected work, and first brief. Print `render_program_start_summary(program_root)` directly in the conversation. Obtain `program_start_checkpoint(program_root)` for that presentation; persist no rendered summary body or separate summary file.
2. Accept a new direct user reply after presentation in the same task. In a fresh task, rediscover and print the current summary before accepting its reply. Only whitespace/case-normalized **Start the first increment** approves the setup and requests the first increment. Do not use a creation request, opening handoff, old answer, quoted example, tool output, or assistant text.
3. Pass the actual presented checkpoint to `adapt_program_start_decision(..., checkpoint=checkpoint)`. Call `start_program` only after successful current validation with a fresh repository observation.
4. Keep the complete `program-start-decision/v1` inside `setup-activation-decision/v3`. Derive `increment-start-intent/v2` from that durable origin and actual sequence-one status; never manufacture a second direct message. Separate receipts and status-last transitions remain intact.
5. Continue through the exact-plan and execution gates. Standard mode keeps the routine exact-plan question; pre-approve and full-increment omit only that question. Starting can lead to local implementation. Source-defined gates retain their owning boundary, including before Delete execution. Reuse the setup component only for a gate explicitly permitting it and shown in the summary.

On interruption, discovery reports the next legal route without writing. An explicit retry reuses only the exact durable combined decision after current revalidation. Changed inputs, foreign authority, malformed or symlinked records, and later lifecycle states stop rather than resetting genesis. A user stop is never a background-start instruction. Legacy setup-only decisions retain their separate first-start requirement.

### Compact presentation and authoring

The current `program-start-summary/v2` renderer prints the program outcome, numbered increments in canonical order, one workspace/branch line, **Starting authorizes**, **Scope**, **Main limits**, actual Delete disclosures and source gates, then links to the source plan, full proposal, and exact scope. Its final line already contains the single start action. Print this canonical output once; add at most one short verified creation-status sentence in an ordinary response. Do not append an allocation dump, workflow-policy explanation, repeated start instruction, or stock skill appendix. Required host disclosures still apply. Never replace the bound text with an assistant paraphrase.

For newly authored proposals, keep each increment outcome and the existing protection, exclusion, boundary, and risk fields concise. Put decision-relevant exceptions in those canonical fields, such as repairs limited to independently validated findings or instruction edits limited to one named section. Keep complete conditional allocations and traceability in the linked machine records. Do not rewrite published manifests to improve their prose.

The ordinary five-increment target is 250–400 visible words, counting link labels rather than destinations. Ordinary Create/Modify/Preserve allocations never become summary rows. Preserve every distinct program-level restriction and risk; only exact repetitions after whitespace/terminal-punctuation normalization may disappear. Actual Delete targets, disposition, rationale, predecessor conditions, and gate questions remain explicit even when they exceed the ordinary budget. Protected-work text describes the selection snapshot, not a fresh cleanliness claim.

### Presentation version and durable consent

Fresh checkpoints use `program-start-summary/v2` with integer renderer version `2`. Checkpoint and decision schemas remain `program-start-checkpoint/v1` and `program-start-decision/v1`. A previously printed, unpersisted v1 checkpoint is stale: show current v2 and wait for its new direct reply. This applies in either the same task or a fresh task, without rewriting the proposal.

A validated durable setup decision retains its recorded `program-start-summary/v1`/integer `1` or v2/integer `2` pair. Historical validation and interrupted starts reproduce that version's exact text and preserve the original decision. Fresh adaptation requires a pristine proposal; an existing durable decision routes to retry. Never select v1 merely to accept an old answer. Unknown or mismatched pairs, Boolean versions, changed text digests, or changed source/workspace/protected-work/brief bindings stop. Publication's current summary digest is informational; it does not replace durable consent or require an immutable inventory rewrite.

The adapter trusts the controller's role/provenance and presentation assertions. Digests and deterministic tests do not prove that a human saw the summary or supplied the reply.

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

Diff acceptance and successor rollover are not a compound routine checkpoint. The exact `accept-continue` prompt authorizes its bound acceptance and immediate rollover transaction; after accepted status is durable, rollover continues without another user question. A later accepted-stop continuation requires the distinct accepted-state prompt. Neither route authorizes a commit or consequential action.

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
