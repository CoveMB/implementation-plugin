# Portable Archive Catalog Update

Program `portable-archive`, revision `3`, increment `catalog-refresh`.
Source digest `SOURCE_DIGEST`; program digest `PROGRAM_DIGEST`; semantic digest `SEMANTIC_DIGEST`.
Workspace `WORKSPACE_PATH`, branch `archive-maintenance`, base `BASE_COMMIT`, head `HEAD_COMMIT`.
Preparation digest `PREPARATION_DIGEST`.

## Global constraints

Preserve existing archive entries and do not publish or commit.

## Requirements and acceptance binding

The catalog remains readable and the focused validation command passes.

## File map

### Create

- `archive/catalog_reader.py` — expose the bounded reader interface.

### Modify

- `tests/test_catalog_reader.py` — verify requested behavior.

### Preserve

- `archive/existing-index.json` — user-owned; preserve bytes.

Interfaces: `read_catalog(path)` returns normalized catalog entries.

## Semantic naming inventory

| Surface | Kind | Origin | Context | Intention | Planning-term basis | Basis owner | Compatibility class | Compatibility disposition |
|---|---|---|---|---|---|---|---|---|
| `archive/catalog_reader.py` | path | new | archive catalog access | read catalog entries | none | none | private | add |
| `read_catalog` | symbol | new | archive catalog access | return catalog entries | none | none | private | add |

## Test-first slices and verification contracts

First observe an import failure, then implement the reader and verify malformed input.

## Commands and expected evidence

`python3 -m unittest tests.test_catalog_reader -v` exits zero after the RED is recorded.

## Review scopes and specialist predicates

Review requirements, path safety, and test evidence; no external specialist is triggered.

## Commit boundaries

Logical review slices only. No commit is authorized.

## Rollback and recovery

Remove only newly created private files and restore modified files from their recorded prior bytes.

## Approval required to execute

Require exact-plan approval and separate local write authorization.
