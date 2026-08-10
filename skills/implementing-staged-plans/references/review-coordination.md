# Review Coordination

Use this procedure only after the current source, approved program, workspace, exact-file plan, and separate review/write authorization validate. Freeze the proposed logical diff before opening review and preserve every accepted or user-owned path outside the plan.

The mechanical boundary is [`review_coordination.py`](../scripts/review_coordination.py). Its validators are deterministic and non-mutating. They validate supplied evidence; they do not establish reviewer identity, independence, expertise, or review quality.

## Required and risk-triggered scopes

Persist separate initial reports for requirements and scope, architecture and boundaries, and test adequacy and evidence validity. Do not merge these scopes into one report.

Classify every canonical risk predicate from the actual frozen diff. Add only the specialist scopes whose predicates are materially touched. Each touched or not-touched decision needs current evidence and rationale; a missing, duplicated, unknown, or misbound predicate fails closed.

## Raw report preservation

Write each initial raw report before reconciliation. Record its regular path, digest, persistence time, scope, reviewer role, assurance status, and finding identifiers. Reconciliation and follow-up evidence belong in later records; never rewrite an initial report to hide a finding.

## Truthful independence

Label controller self-review as non-independent with reduced assurance. Never infer independence from a role label, a successful test, or a tool invocation. Use at most one bounded independent final reviewer for a coherent change unless a material defect requires a focused follow-up reviewer. The follow-up must identify the material finding it addresses.

## Contextual semantic naming

Review every created or renamed path, symbol, command, test or fixture, heading, schema or identifier, and generated path in its implementation context. Record the surface kind, stable context, intention, compatibility disposition, and any finding. A planning coordinate is allowed only when it has a specific implementation-governance or durable-domain basis and named owner.

## Material findings

Classify only evidence-supported defects as material. Every material finding needs an identifier, owning report and scope, summary, evidence, impact, calibrated confidence, remediation, and explicit disposition. Unsupported preferences remain non-material, speculative, or invalid and cannot remain open as merge blockers.

## Remediation and renewed review

Reconcile only after all initial reports are persisted. For each repaired material finding, capture one focused cycle: intended regression failure, observed failure, smallest repair, successful affected verification, and a renewed report for the affected scope. Preserve the initial report. Stop for a program amendment if repair changes approved requirements, acceptance, public behavior, protected contracts, risk posture, data ownership, dependencies, sequencing, or review cadence.

## Fresh final verification

Final verification must complete after all repairs and reconciled reviews. Record exact commands, integer exit codes, concise results, completion times, verified paths, and a candidate digest. Reject duplicate commands, nonzero or boolean exits, sensitive result text, stale timestamps, and unresolved material findings. A prior successful run is not fresh evidence after repair.

## Packet data and rendering

Build packet data from the reconciled structured evidence and render it deterministically. The packet must include identity and outcome; changes and rationale; program context; files by purpose; human review order; requirements and acceptance; exact commands and results; baseline failures; execution evidence; reviewer roles, findings, and dispositions; repairs and renewed verification; deviations and amendments; human judgment; edge cases and manual checks; implications; residual risks and deferred work; recovery; workspace and logical boundaries; and current state and next action.

Require byte equality between the deterministic rendering and the persisted packet. A command-only packet is incomplete.

## Lifecycle and authority boundary

Review authorization does not authorize staging, a commit, diff acceptance, another increment, publication, deployment, migration, provider mutation, or other consequential action. Logical commit boundaries remain planning evidence until a separate exact commit grant exists. Apply lifecycle transitions only through accepted state authority and stop at the mode's required diff-approval boundary.

## Validation commands

Run focused tests before the complete local verification set:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_review_coordination -v
PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/review_coordination.py validate-bundle path/to/review-evidence.json --packet path/to/review-packet.md
PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

Exit `0` means the supplied bundle and exact packet are valid, `1` means an invariant failed, and `2` means the command input is unusable. The command reads regular non-symlink files and prints only concise issues or a pass line.

## Hard stops

Stop without representing the review as complete when authority or bindings drift; a required raw report is absent; a risk predicate is unresolved; independence is overstated; a material finding lacks its contract or disposition; repair lacks renewed affected review; final verification is stale or failing; packet data and rendering differ; a program amendment is required; or the next lifecycle action lacks exact authority.

## Bounded result

Return the frozen logical change boundary, selected scopes and predicates, raw report digests, reviewer roles and truthful assurance, findings and dispositions, remediation and renewed-review evidence, exact final command results, packet validation result, residual limitations, current state, next legal action, and mandatory stop. Static validation does not prove independent identity, expert judgment, live agent behavior, accessibility quality, deployment, data restoration, provider reconciliation, or production behavior.
