---
name: bug-check
description: Use when fixing, debugging, reviewing, or validating software bugs, especially defects involving UI state, APIs, databases, caches, queues, background jobs, auth, permissions, concurrency, integrations, deployments, performance, security, or repeated bug reactivation.
---

# Bug Check

## Purpose

After code changes, use the changed file range to find relevant bug-boundary knowledge, compare those boundaries against the current code, and fix any missing handling.

Do not turn this into a separate report-writing step. The useful output is the next engineering action: patch missing handling, run targeted verification, or say no relevant boundary gap was found.

## Workflow

1. Decide if the changed scope can create a bug boundary: state, UI list/form behavior, API contract, auth, cache, tenant scope, database write, queue/job, config/deploy, security, or user-visible behavior.
2. Get the changed files from the current diff, staged diff, or user-provided paths. If useful, run `scripts/build-bug-context.py` to route those paths.
3. Read `references/routing.md`, then only the matched cards in `references/boundaries/`.
4. For each matched card, inspect the changed code and mark it mentally as:
   - `missing -> fix`: relevant boundary is not handled.
   - `covered`: code already handles it.
   - `not relevant`: route matched, but evidence shows the boundary does not apply.
5. If anything is missing, patch it before finishing the original task.
6. Verify the original path and the fixed boundary with the narrowest useful command or runtime check.
7. Answer briefly with what was missing, what was covered, what was verified, and any remaining risk. Use `references/completion-contract.md` only if the user explicitly asks for a formal report or a checker-ready final report.

## Resources

- `scripts/build-bug-context.py`: routes changed files and bug text to relevant boundary cards.
- `references/routing.md`: manual route map.
- `references/boundaries/`: bug-boundary knowledge cards.
- `references/boundary-card-format.md`: format for adding a new boundary card.
- `references/completion-contract.md`: optional formal report contract for explicit audits.
- `scripts/check-bug-report.py`: optional checker for formal reports.
