# Archive exact plan

## Global constraints
Preserve user work and write only declared paths.

## Requirements and acceptance binding
Program id: ARCHIVE-PROGRAM
Program revision: 1
Increment id: ARCHIVE-INDEX
Source digest: 2dab0af58f832caef7eea74640dac0c36b3fae60087ba9df83d0522530e79ffb
Program digest: 3702df1a6c7e863a829dd0e00b78f4116a444fc6ef43b362c5a941b3c0131bc3
Semantic digest: 5b669e2f72f340dd221be4a983d6f557dc0c1fa2972baed4c3aa868f829e59ea
Workspace path: /private/var/folders/4b/92vv49v10lj3j8mwm6k0q8qh0000gn/T/tmpcy_txmee/repository
Workspace branch: archive-maintenance
Workspace base: 26d48190f7643e19dc9999c22654529f8286274d
Workspace head: 26d48190f7643e19dc9999c22654529f8286274d

## File map

### Create

- `archive-output.txt` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/closure/closure-packet.md` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/closure/reconciliation.json` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/increments/ARCHIVE-INDEX/execution-baseline.json` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/increments/ARCHIVE-INDEX/review-evidence.json` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/increments/ARCHIVE-INDEX/review-packet.md` — exact owned path.
- `reviews/architecture.json` — exact owned path.
- `reviews/requirements.json` — exact owned path.
- `reviews/test-evidence.json` — exact owned path.

### Modify

- `implementation-programs/ARCHIVE-PROGRAM/state/action-authorizations.jsonl` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/state/approvals.jsonl` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/state/block-resolutions.jsonl` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/state/increment-grants.jsonl` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/state/rollovers.jsonl` — exact owned path.
- `implementation-programs/ARCHIVE-PROGRAM/state/status.json` — exact owned path.

### Preserve

- `catalog.txt` — exact owned path.

Interfaces: `archive-output.txt` is the bounded product output.

## Semantic naming inventory
| Surface | Kind | Context | Intention |
|---|---|---|---|
| `archive-output.txt` | path | archive output | record the verified result |

## Test-first slices and verification contracts
Create the output, then verify its observable bytes.

## Commands and expected evidence
Run `python3 -m unittest tests.test_archive_output`; expected exit 0.

## Review scopes and specialist predicates
- requirements: `reviews/requirements.json`
- architecture: `reviews/architecture.json`
- test-evidence: `reviews/test-evidence.json`

## Commit boundaries
One logical local commit boundary; no commit authority is granted.

## Rollback and recovery
Preserve prefixes and retry only byte-identical transactions.

## Approval required to execute
Use the persisted approval mode and status-current grant.
