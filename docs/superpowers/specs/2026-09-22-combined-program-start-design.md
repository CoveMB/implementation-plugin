# Combined program setup and first start

Status: planning complete with the user's scope decisions incorporated. This document is not implementation authorization.

## Intended result

After creating an incremental program, print a short, useful summary in the conversation and one explicit **Start the first increment** choice. Do not create a setup recap file or a replacement summary document. That choice approves the displayed setup and requests the first increment. Keep the detailed operation envelope, traceability, integrity bindings, and separate internal receipts. Creating a proposal continues to stop before starting it.

This changes the initial interaction described in the [existing setup design](2026-08-23-program-setup-and-activation-design.md). It preserves that design's source, workspace, authority, and recovery guarantees. Historical setup-only decisions keep their original meaning.

## Confirmed scope

1. **New proposals only.** The user will delete the existing proposal. No migration, revision, supersession, or deletion procedure is included in this plugin change. Existing programs retain their current routes and history. New proposals declare the immutable manifest-v3 field program_start_contract with the exact string value combined-start/v1. Absence selects the historical route; unknown, null, or malformed values are invalid. This is an eligibility discriminator, not execution consent, and is covered by the manifest integrity binding. Never add it to an existing published proposal.
2. **Same or fresh task.** Both are supported after current-state revalidation. Same-task use must be a new direct user reply after presenting the summary. In a fresh task, rediscover and display the current summary before accepting its direct start reply. A creation request, copied handoff, or earlier answer cannot double as the later start decision.
3. **Output only.** The summary is rendered in memory and printed in the conversation or returned as command output. Neither generation nor publication saves setup-recap.md, a replacement Markdown summary, or a separate text/JSON copy of the rendered prose. Existing machine records still persist the canonical program details; decision metadata retains the summary digest and version for integrity and retry validation.

The user's statement that the existing proposal will be deleted resolves compatibility scope; this planning task does not perform that deletion.

## Evidence and approach

The inspected Spotify setup recap contains 4,513 words and 76 operation allocations. The renderer repeats individual requirements, checks, and file metadata. This is a presentation problem; removing validation would not address it.

Three approaches were considered:

- Shorten the recap but keep separate setup and start questions: least lifecycle change, but retains the redundant interaction the user wants removed.
- **Use a short summary and one explicit combined decision:** recommended. Preserve separate setup and first-start receipts and the existing status sequence; connect their writers using durable, specific consent.
- Skip setup authority and start automatically after generation: rejected. Proposal-generation intent does not authorize implementation or select the displayed workspace and scope.

Use the existing Python modules and standard library. Do not add a UI framework, generic workflow engine, new ledger, dependency, or background runner.

## Summary contract

Render the summary deterministically from validated canonical records. Its reading order is:

1. Program outcome and what starting will do.
2. One outcome line per increment, in order; identify the first increment.
3. Selected repository, workspace, branch, protected existing work, and approval mode in plain language.
4. Material scope limits, changes from the source request, exclusions, risks, and any destructive operation with its exact target and disposition.
5. Source-defined gates and remaining design, Git, provider, installation, and other consequential-action boundaries.
6. Links to the source plan, approved-program proposal, detailed operation envelope, and traceability, followed by the explicit start choice.

All links point to existing source or machine artifacts. There is no summary-file link or recap logical role. On rediscovery, regenerate the prose from the bound records and renderer version. Persist no summary body in the checkpoint or decision receipt.

Group repeated ordinary operation details by their actual meaning. Do not synthesize a broader directory permission from a set of exact paths. Keep conditional permissions visibly conditional. No automatic deletion is implied by showing a Delete allocation.

Aim for approximately 250–400 words for an ordinary five-increment program, with no hard truncation rule. Additional material risks or gates may require more text. Do not dump requirement IDs, hashes, mode bits, or repeated allocation metadata into the default summary. Detailed records remain available for inspection; linking them is not evidence that the user read every requirement.

The summary must distinguish the approval modes: standard still asks for the exact plan; pre-approve and full-increment omit that routine pause but retain all applicable authority checks. Starting may lead to local implementation under those checks. Do not misleadingly promise that starting can only create records.

W3C's current supplemental guidance supports putting important actions first and explaining consequences at the point of choice: [important information](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o2p04-page-important/) and [results of actions](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o7p03-supported-choice/). These inform the design; they do not establish accessibility conformance.

## Authority contract

- Retain the existing manifest-v3 and status-v3 state sequence: proposal at 0, active/awaiting-first-increment at 1, active/preparing at 2. Sequence 1 becomes an internal recoverable boundary on the combined route.
- Keep setup/envelope v1 and v2 operation semantics distinct. The new interaction does not broaden Create, Modify, Delete, or Preserve permissions or alter accepted-predecessor evidence.
- Keep legacy recap renderers, checkpoints, setup-only adapters, and first-start handoff validation byte-compatible for persisted history. Add a separate versioned summary and combined consent contract.
- Validate program_start_contract in the shared manifest/setup validation path. The combined route and setup-activation-decision/v3 require combined-start/v1; legacy setup-only adapters and receipts require absence. Reject the field on older manifest families. Do not infer eligibility from file names, timestamps, or prose.
- The combined adapter accepts the explicit phrase “Start the first increment” after whitespace/case normalization. Generic “yes”, “proceed”, conditional answers, quoted examples, tool output, or assistant text do not authorize the combined route. Do not translate the phrase into a fabricated setup “yes” or fabricated direct-user handoff submission.
- Require the actual presented checkpoint as an adapter argument. Bind the summary renderer/version and bytes, program/source/semantic identities, proposal status, workspace selection, first increment, and first brief. Revalidate against current canonical evidence before the first write.
- Store the complete typed combined decision in the existing setup-activation record so an interrupted writer can recover the original setup-and-start scope. A setup-only record must never acquire that scope through a reader upgrade.
- Derive the first-start intent from that validated durable decision and the actual sequence-one status. Mark its provenance as derived combined consent, with a link to the original direct user decision. Do not label generated text as a new user message.
- Keep the separate program approval, workspace approval, first-increment grant, exact plan, baseline, action authorization, and execution transition. The combined checkpoint is not the existing generic compound-approval mechanism.
- Historical validation uses the original proposal binding retained in the decision. It must not compare that binding to a later current status or discard it to make retries pass.

The existing adapter boundary trusts the controller's role/provenance assertion; hashing it is not independent proof of human identity or presentation. Front-door behavior therefore needs review as well as deterministic tests.

## Execution and interruption contract

1. Validate the decision, immutable inputs, current repository observation, selected workspace, and legal prefix before any write.
2. Persist or adopt the combined setup decision; satisfy each due pre-activation gate through its existing procedure; persist program and workspace receipts; write sequence-one status last.
3. Revalidate the live observation and bound first brief; satisfy each due first-start gate; derive and persist the first-start grant; write sequence-two status last.
4. Continue through existing exact-plan and execution procedures according to the selected approval mode. No second routine setup/start question on this route.

Each write remains independently recoverable. Do not claim an atomic transaction across both stages. A crash may leave sequence 0 or 1 with a valid prefix. An explicit retry can adopt only that exact prefix using the original combined decision; it cannot authorize a different workspace, brief, source, or first increment. Discovery only reports the next legal route and never resumes writes itself.

Missing source-gate answers pause at their owning boundary. Only a gate explicitly permitting setup reuse may reuse the setup component, and its meaning must be visible in the summary. A separately answered gate cannot substitute for the combined decision. A user stop ends execution; recovery is not a background-start mechanism.

Malformed, symlinked, divergent, mixed-family, or out-of-order records are preserved and rejected. Once the first increment has progressed beyond initial preparation, replay reports current state or the applicable existing resume route; it never recreates genesis authority or resets status.

## Compatibility and rollout constraints

- Existing active, accepted, blocked, closed, and superseded programs retain their authority and history.
- Existing unmarked proposals retain their legacy setup-only flow. New proposal generation selects combined-start/v1 before producing any bound bytes; no compatibility migration is needed.
- Old setup-only sequence-one programs still require their existing first-start decision.
- Legacy manifest/status-v2 launch behavior and frozen v0.1.1 fixtures remain unchanged.
- No real Spotify proposal, source plan, ledger, cache, credential, or provider data is changed while implementing or testing the plugin. Use synthetic fixtures for integration coverage.
- No automatic installation, publication, Git action, or package-version bump is included. An eventual release must synchronize metadata deliberately and verify the explicitly selected installed copy after installation is authorized.

## Acceptance criteria

- An eligible newly presented summary plus one direct start reply reaches first-increment preparation without a separate setup-only pause.
- Newly generated proposals contain no recap or replacement summary file, and printing/rediscovery does not create one. Persisted checkpoints and receipts contain identity metadata, not a saved summary body.
- Starting works in the same task or a fresh task after current summary presentation and revalidation.
- Proposal creation, summary rendering, discovery, invalid replies, and stale checkpoints do not create execution authority.
- Interrupted setup and first-start prefixes recover without duplicate receipts, expanded permission, or repeated routine consent.
- Existing setup-only records cannot start through the new route; operation families and all later gates retain their behavior.
- The ordinary summary is materially easier to read, and a human can identify the next action, scope, workspace, approval mode, and meaningful risks from it.
- The existing Spotify proposal is outside the implementation scope; a newly generated replacement will use the same new-proposal route as other projects.
