# client-async-race

## Applies When
- Changed files include hooks, effects, fetchers, query handlers, subscriptions, timers, debounced search, route loaders, or async state transitions.
- Bug text mentions stale response, old request, race, unmount, route switch, context switch, double fetch, loading stuck, flicker, timeout, abort, or callback after close.

## Do Not Select When
- The changed path is synchronous and deterministic with no promise, timer, subscription, debounce, polling, or callback after a state/context change.
- The async behavior is owned by a durable background queue or webhook; use async-job-queue instead.
- The issue is only cache invalidation after a completed mutation with no overlapping request or stale callback risk; use state-cache-sync instead.

## Inspect
- Async request lifecycle, cancellation, sequence/version guards, and cleanup on unmount or dependency change.
- State writes after `await`, promise callbacks, timers, subscriptions, polling, debounced handlers, and retries.
- Loading/error/empty state transitions when a newer request starts before an older one resolves.
- Cache/query keys, route params, tenant/user context, and form/list filters captured by closures.
- Nearby tests for slow response, fast follow-up request, unmount, and failure paths.

## Handled When
- Older async work cannot overwrite newer context or state.
- Unmount, route change, dialog close, filter change, and context switch cancel or ignore stale callbacks.
- Loading and error state belong to the active request, not whichever request finishes last.
- Debounced, retried, or polling work is cleaned up and cannot update hidden or destroyed UI.
- Tests or runtime checks cover slow-old-response-after-newer-request behavior when relevant.

## Missing Means
- The fix assumes async responses arrive in request order.
- State is written after `await` or in callbacks without cancellation, version, or mounted-context checks.
- Dependency arrays, captured params, query keys, or cleanup functions do not match the active data context.
- Manual verification only covers a fast happy path with no delayed or interrupted request.

## Verify
- Slow first request followed by faster second request.
- Route, tab, tenant/context, filter, or modal state switch while the first async operation is pending.
- Unmount or close before request, timer, subscription, or retry callback resolves.
- Failed active request after stale successful request and stale failed request after active successful request.
- Loading, error, empty, and success states after interruption.

## Test Ideas
- Race test where an older promise resolves after a newer one and must be ignored.
- Cleanup test proving unmount or close prevents later state writes.
- Query-key or dependency test covering captured route/filter/context values.
- Fake-timer test for debounced search or delayed retry cleanup.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
