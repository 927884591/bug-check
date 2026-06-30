# Bug Check Index

Use `routing.md` first. Load boundary cards from `boundaries/` only when matched by changed files, bug text, or project signals.

Core files:

- `routing.md`: converts changed files and bug descriptions into matched boundary cards and focused read targets.
- `boundary-card-format.md`: required format for adding new boundary cards.
- `completion-contract.md`: final report contract and required Boundary Handling Table.
- `boundaries/`: common bug-boundary cards for UI lists, forms, caches, APIs, auth, tenancy, databases, queues, deployment/config, and sensitive data.

Default flow:

1. Build a context pack with `../scripts/build-bug-context.py` from changed files and bug text.
2. Read only `routing.md` and the matched cards.
3. Fill a Boundary Handling Table before claiming a bug is fixed or a review is complete.
4. Verify the original bug path and every boundary marked `missing -> fixed`.
