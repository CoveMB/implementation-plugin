# Portable Library Program

## Catalog intake

- Record a stable identifier for every received volume.
- Reject duplicate volume identifiers.
- Preserve the supplied title and edition metadata.

## Lending integrity

- Record every loan against one known volume.
- Prevent a returned volume from remaining marked as loaned.
- Preserve an append-only loan event history.

## Privacy and recovery

- Restrict borrower details to authorized operators.
- Redact borrower details from operational logs.
- Restore the catalog from the latest verified local snapshot.
