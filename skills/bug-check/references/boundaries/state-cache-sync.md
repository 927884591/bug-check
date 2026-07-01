# state-cache-sync

## Applies When
- Changed files include state stores, query caches, mutations, list/detail pages, derived counters, tabs, polling, subscriptions, or local storage.
- Bug text mentions stale data, refresh, cache, invalidation, create/edit/delete not reflected, count mismatch, old callback, or context switch.

## Do Not Select When
- The changed behavior is stateless rendering with no store, query cache, local storage, mutation, polling, or derived state.
- The failure mechanism is only URL/query navigation persistence; use navigation-url-state instead.
- The stale behavior comes from overlapping in-flight async work rather than cache/update propagation; use client-async-race instead.

## Inspect
- Mutation success, failure, optimistic update, rollback, and invalidation paths.
- List, detail, cards, counters, charts, and action buttons affected by the mutation.
- Store/query/cache keys including filters, tenant, permissions, locale, and feature flags.
- Timers, polling, subscriptions, pending requests, and callbacks on unmount or context change.
- Local storage/session storage schema and migration/clear behavior.

## Handled When
- Create/edit/delete/enable/disable/start/stop/rollback refreshes or updates every affected view.
- Query/cache keys include relevant context such as tenant, user, filter, permissions, locale, and feature flags.
- Failed or rolled-back optimistic updates restore correct state.
- Old requests, subscriptions, timers, or callbacks cannot overwrite a newer context.
- Context switch, tab switch, route switch, and reload do not show stale state.

## Missing Means
- Mutation code only updates one visible component while other derived views remain stale.
- Cache invalidation omits the relevant key or context dimension.
- No cancellation/version check prevents older responses from overwriting newer requests.
- No evidence covers failure, rollback, context switch, or reload behavior.

## Verify
- Create, edit, delete, enable/disable, and last-item mutation paths relevant to the bug.
- List, detail, counters, charts, and action buttons after mutation.
- Route switch, tab switch, context switch, and page reload.
- Slow response followed by newer search/filter/context request.
- Failed mutation and optimistic rollback.
- Local storage/session storage after logout, permission change, or version upgrade when relevant.

## Test Ideas
- Unit test for cache-key construction.
- Integration test for mutation invalidation across list and detail.
- Race test where an older request resolves after a newer one.
- Regression test for context switch clearing selected rows and derived data.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
