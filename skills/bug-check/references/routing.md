# Boundary Selection Guide

Use this file after building a context pack. The goal is for the AI to select a small set of boundary cards from evidence, not for a script to decide the match.

## Inputs

Use:
- changed file paths from git diff, staged files, `--base`, `--diff-range`, explicit `--files`, or the user's report
- diff hunks and changed symbols when available
- bug description words, error messages, status codes, and reproduction steps
- project structure signals such as package files, API folders, migration folders, worker folders, and test folders
- nearby tests in the same directory, `__tests__`, `tests`, or matching `*.test.*` and `*.spec.*`
- the boundary card index emitted by `scripts/build-bug-context.py`
- suggested candidate cards emitted by `scripts/build-bug-context.py`, treated only as weak routing hints
- verification candidates emitted by `scripts/build-bug-context.py`, treated only as possible commands or manual checks

## Selection Rules

- If there is no changed scope, do not select final matched cards. Use bug text only to list tentative boundary hypotheses and state that a real boundary check requires changed files, a diff, or explicit paths.
- Start from the failed mechanism, not the directory name.
- Treat file paths and keyword hits as weak hints. Select a card only when the changed code path can cross that boundary.
- Apply a card's `Do Not Select When` section before reading or using it; weak candidate ranking never overrides those exclusion rules.
- Prefer 1-4 cards. Choose more only when the bug crosses multiple real boundaries, such as UI state plus API contract plus auth.
- Read only selected card files from `references/boundaries/`.
- If no card fits, record a manual boundary with evidence instead of skipping boundary analysis.
- Persist a manual boundary candidate only when it names a reusable failed invariant. Use the project-local `.bug-check/manual-boundaries.jsonl` store through `scripts/review-boundary-candidates.py record`; do not read that store during normal routing.
- If a plausible card is not selected, be ready to explain why the current code path does not cross that boundary.

## Manual Boundary Candidates

Manual candidates are an evidence log for skill maintenance, not formal boundary cards.

Promote or merge a candidate only when:
- high or critical risk affects security, permissions, tenant isolation, persisted data, or production recovery
- the same failed invariant repeats across tasks, modules, or projects
- a current card cannot cover the mechanism with a small focused update
- the candidate has a reusable `Verify` path, not only a business-specific symptom

Prefer updating an existing card over creating a new card when one to three lines cover the mechanism. Keep project-private details in the candidate store and add only abstracted, reusable knowledge to formal boundary cards.

## Card Index

`scripts/build-bug-context.py` reads `references/boundaries/*.md` and prints each card with its file path and `Applies When` summary. Use that index as the source of truth for available cards.

Common selection patterns:

- `ui-list-table`: list, table, grid, search, filter, sort, pagination, selection, empty, or batch-action behavior.
- `ui-overlay-focus`: modal, dialog, drawer, popover, portal, focus, keyboard, screen reader, scroll lock, or overlay cleanup behavior.
- `responsive-a11y-input`: responsive layout, mobile viewport, keyboard access, focus, labels, touch targets, or hover-only controls.
- `form-validation`: forms, dialogs, drawers, validators, submit state, hidden/disabled fields, or backend validation mapping.
- `state-cache-sync`: state stores, query caches, mutations, polling, subscriptions, stale callbacks, or context switch cleanup.
- `client-async-race`: hooks, effects, fetchers, timers, subscriptions, stale requests, unmount callbacks, or async state races.
- `realtime-subscription`: WebSocket, SSE, event streams, subscriptions, reconnect, duplicate events, missed updates, or offline recovery.
- `navigation-url-state`: route params, query params, tabs, deep links, redirects, refresh, copied URLs, or browser back/forward behavior.
- `performance-resource-lifecycle`: long-lived resources, listeners, observers, timers, repeated renders, large lists/charts, cleanup, leaks, or jank.
- `api-contract`: request/response shape, status codes, params, headers, DTOs, schemas, serialization, or generated clients.
- `auth-permission`: login/logout/session, route/API guards, roles, object-level authorization, 401, or 403 behavior.
- `tenant-isolation`: tenant/project/site/org/workspace propagation, cache keys, scoped APIs, exports, or cross-context data.
- `database-transaction`: queries, repositories, migrations, transactions, rollback, constraints, backfills, or persisted consistency.
- `async-job-queue`: jobs, workers, queues, retries, idempotency, timeouts, schedulers, webhooks, or long-running work.
- `file-transfer-export`: upload, download, import, export, file validation, generated reports, signed URLs, or partial transfer failures.
- `i18n-timezone-format`: timezone, DST, locale, date boundaries, currency, decimals, rounding, translated labels, or export formatting.
- `deployment-config`: env/config, feature flags, startup/readiness, CI/deploy, secrets, or old/new version compatibility.
- `security-sensitive-data`: XSS/injection, unsafe rendering, tokens, cookies, secrets, private URLs, logs, exports, or downloads.

## Output

If changed scope exists, decide before reading boundary cards:
- selected boundary cards
- evidence for selecting each card
- candidate cards intentionally rejected by `Do Not Select When` when the context builder suggested them
- cards intentionally not selected when they are plausible but not supported by the code path
- source/test files to inspect next

Then read the selected cards and complete the Boundary Handling Table with final statuses.

If no changed scope exists, output only:
- no changed files or explicit paths were available
- tentative boundary hypotheses, clearly labeled as hypotheses
- the code evidence needed before this can become a real boundary check
