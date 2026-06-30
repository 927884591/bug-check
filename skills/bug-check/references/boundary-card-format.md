# Boundary Card Format

Each boundary card is a compact checklist that lets an AI decide whether a common bug boundary is relevant and handled. Keep cards concrete enough to drive a Boundary Handling Table entry.

## Required Sections

```md
# boundary-name

## Applies When
- Changed files or bug words that make this card relevant.

## Inspect
- Code paths, state, API, data, tests, or runtime evidence to inspect first.

## Handled When
- Observable code behavior, guards, tests, or verification proving the boundary is handled.

## Missing Means
- How to decide that the current code has no branch, guard, test, invalidation, transaction, or verification for this case.

## Verify
- Manual, automated, or runtime checks that prove the boundary after the fix.

## Test Ideas
- Focused tests that catch regressions.
```

## Handling Status

Use these exact statuses in the Boundary Handling Table:

- `relevant`: the card applies, but evidence is still being gathered.
- `already handled`: current code and verification already cover the boundary.
- `missing -> fixed`: the boundary was missing and the change added handling.
- `not applicable`: the card was matched, but current evidence proves it does not apply.

Do not mark a card `not applicable` because it is inconvenient to verify. Use evidence.
