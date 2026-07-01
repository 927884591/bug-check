# Bug Check Index

Use `routing.md` first. Load boundary cards from `boundaries/` only after selecting them from changed files, bug text, diff context, and project signals.

Core files:

- `routing.md`: explains how the AI selects boundary cards from a context pack.
- `boundary-card-format.md`: required format for adding new boundary cards.
- `completion-contract.md`: final report contract and required Boundary Handling Table.
- `boundaries/`: common bug-boundary cards for UI lists, forms, responsive accessibility, navigation/URL state, performance/resource lifecycle, caches, realtime streams, APIs, auth, tenancy, databases, queues, file transfer, i18n/timezone, deployment/config, and sensitive data.
- `../scripts/review-boundary-candidates.py`: optional recorder/reviewer for project-local manual boundary candidates.

Default flow:

1. Build a context pack with `../scripts/build-bug-context.py` from changed files and bug text.
2. Read `routing.md`, then select relevant cards from the context pack's boundary card index.
3. Use suggested candidates only as weak hints, apply each card's `Do Not Select When` rules, then read only the selected cards. If no exact card fits, record a manual boundary instead of skipping boundary analysis.
4. If the manual boundary is a reusable failed invariant, optionally append it to the current project's `.bug-check/manual-boundaries.jsonl` candidate store for later review.
5. Fill a Boundary Handling Table before claiming a bug is fixed or a review is complete.
6. Verify the original bug path and every boundary marked `missing -> fixed`.
