---
name: bug-check
description: Use when fixing, debugging, reviewing, or validating software bugs, especially defects involving UI state, APIs, databases, caches, queues, background jobs, auth, permissions, concurrency, integrations, deployments, performance, security, or repeated bug reactivation.
---

# Bug Check

## Purpose

After code changes, build a compact context pack, choose relevant bug-boundary cards from evidence, compare those boundaries against the current code, and fix any missing handling.

Do not treat the context builder as the decision-maker. It lists changed scope, diff context, and available cards; the AI must select cards from actual code and bug evidence. Do not turn this into a separate report-writing step. The useful output is the next engineering action: patch missing handling, run targeted verification, or say no relevant boundary gap was found.

## Workflow

1. Decide if the changed scope can create a bug boundary: state, UI list/form behavior, API contract, auth, cache, tenant scope, database write, queue/job, config/deploy, security, or user-visible behavior.
2. Get the changed files from the current diff, staged diff, or user-provided paths. If useful, run `scripts/build-bug-context.py` to collect changed scope, diff context, nearby tests, and the boundary card index.
   If there are no changed files or explicit paths, do not perform a full boundary check. Treat bug text only as tentative boundary hypotheses, ask for or wait for changed code, and do not mark cards as covered, missing, fixed, or not applicable.
3. Read `references/routing.md`, use the context pack to select relevant cards yourself, then read only those cards in `references/boundaries/`.
4. For each selected card, inspect the changed code and mark it mentally as:
   - `missing -> fixed`: relevant boundary was not handled and you patched it.
   - `already handled`: code and verification already cover it.
   - `not applicable`: the card looked plausible, but evidence shows it does not apply.
   If no exact card fits, record a manual boundary in the final answer and inspect the changed code path anyway. If the failed invariant may recur, optionally append a project-local candidate with `scripts/review-boundary-candidates.py record`; do not load candidate history during the normal check.
5. If anything is missing, follow the user's requested mode:
   - For fix, implementation, or continuation work, patch the missing handling before finishing the original task.
   - For review, audit, or checker work, report the boundary gap first and do not patch unless the user asks.
6. Verify the original path and the fixed boundary with the narrowest useful command or runtime check.
7. Answer briefly with what was missing, what was covered, what was verified, and any remaining risk. Use `references/completion-contract.md` only if the user explicitly asks for a formal report or a checker-ready final report.

## Resources

- `scripts/build-bug-context.py`: builds a changed-scope, diff, nearby-test, and boundary-card-index context pack.
- `references/routing.md`: AI card selection guide.
- `references/boundaries/`: bug-boundary knowledge cards.
- `references/boundary-card-format.md`: format for adding a new boundary card.
- `references/completion-contract.md`: optional formal report contract for explicit audits.
- `scripts/check-bug-report.py`: optional checker for formal reports.
- `scripts/review-boundary-candidates.py`: optional project-local manual-boundary candidate recorder and reviewer.
