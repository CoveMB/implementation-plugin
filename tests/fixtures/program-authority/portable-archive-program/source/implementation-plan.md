# Portable Archive Plan

## Inventory intake

- Record a stable identifier for every received object.
- Reject duplicate object identifiers.
- Record the received byte count for every object.
- Preserve the original media-type declaration.

## Checksum verification

- Compute a SHA-256 checksum for every received object.
- Compare each received checksum with the supplier declaration.
- Quarantine every checksum mismatch.
- Record the checksum verification result.

## Retention

- Assign every accepted object to a retention class.
- Prevent deletion before the retention period expires.
- Record every approved retention exception.
- Re-evaluate retention when governing policy changes.

## Privacy

- Classify each object for privacy sensitivity.
- Restrict sensitive objects to authorized operators.
- Redact sensitive values from operational logs.
- Record every access to a sensitive object.

## Recovery

- Maintain two independently stored recovery copies.
- Verify each recovery copy on a defined schedule.
- Exercise restoration using a representative object set.
- Record restoration duration and outcome.

## Accessibility

- Provide text alternatives for visual archive summaries.
- Preserve keyboard access to every operator action.
- Expose validation errors with programmatic labels.
- Publish the supported assistive-technology baseline.

## Compatibility

- Declare every supported archive package version.
- Reject unsupported package versions before ingest.
- Preserve documented behavior across compatible revisions.
- Record the compatibility decision for every package.

## Observability

- Emit a stable event identifier for every ingest attempt.
- Record validation duration without source content.
- Alert when the quarantine rate exceeds its threshold.
- Preserve diagnostic events for the approved interval.

## Operator review

- Present checksum mismatches for operator review.
- Require a rationale for every quarantine release.
- Separate the reviewer from the original releaser.
- Record the final operator disposition.

## Approval

- Bind approval to the exact source digest.
- Bind approval to the exact program digest.
- Invalidate approval when either bound digest changes.
- Reject conflicting approval records.

## Staged delivery

- Deliver intake before recovery automation.
- Verify each delivery stage before the next begins.
- Keep distant implementation files provisional.
- Stop at every required human acceptance boundary.

## Closure

- Reconcile every requirement before closure.
- Preserve accepted evidence from prior revisions.
- Record unresolved risk with an accountable owner.
- Require explicit closure approval.
