# performance-resource-lifecycle

## Applies When
- Changed files include rendering loops, large lists, charts, canvas/WebGL, animations, observers, event listeners, timers, intervals, workers, media, polling, heavy calculations, virtualization, memoization, or cleanup code.
- Bug text mentions slow, lag, freeze, jank, memory leak, duplicate listener, repeated request, repeated render, CPU, memory, scroll performance, animation stutter, or cleanup after close/unmount.

## Do Not Select When
- The change has no long-lived resource, repeated work, rendering hot path, listener, timer, observer, worker, media, or large-data behavior.
- The only lifecycle risk is correctness of one async response after context changes; use client-async-race instead.
- The issue is backend queue retry/idempotency rather than client/runtime resource ownership; use async-job-queue instead.

## Inspect
- Creation and cleanup of event listeners, observers, intervals, timeouts, animation frames, workers, media streams, sockets, subscriptions, and polling.
- Render frequency, dependency arrays, memoization boundaries, expensive calculations, list virtualization, and large data transformations.
- Resource ownership across mount, unmount, route change, tab switch, dialog close, context switch, and error paths.
- Duplicate requests, duplicate listeners, retained closures, stale refs, and cleanup after interrupted animations or failed initialization.
- Nearby tests, runtime profiles, counters, or instrumentation that prove resource counts return to normal.

## Handled When
- Every long-lived resource has a matching cleanup path for unmount, close, route/context switch, and initialization failure.
- Re-renders, recalculations, subscriptions, polling, and event listeners do not multiply after repeated opens or state changes.
- Large lists, charts, and animations avoid unnecessary layout work, blocking loops, and unbounded memory growth.
- Duplicate requests or listeners are deduped, cancelled, or deliberately scoped to the active view.
- Verification covers repeated open/close or navigation and a representative large/slow case when relevant.

## Missing Means
- The fix adds a listener, timer, observer, animation, worker, subscription, or polling loop without proving cleanup.
- Dependency changes recreate expensive work or subscriptions without dedupe or teardown.
- Manual verification only checks first render and not repeated open/close, navigation, or large data.
- Loading/error/close paths skip cleanup and leave retained callbacks, DOM nodes, workers, or timers.
- Performance claims are based only on lint/build success with no runtime or targeted regression evidence.

## Verify
- Open/close, mount/unmount, route switch, tab switch, context switch, and failed initialization.
- Repeated user actions that previously created duplicate listeners, requests, timers, or subscriptions.
- Large list, long text, large chart, heavy calculation, animation, and scroll paths where relevant.
- Browser or runtime evidence such as listener counts, request counts, timer cleanup, CPU profile, or memory before/after.
- Slow device, throttled CPU, hidden tab, or background/foreground transition when feasible.

## Test Ideas
- Component test proving cleanup removes listener/timer/subscription after unmount.
- Regression test for repeated open/close not increasing request or listener counts.
- Performance-oriented unit test for memoized transformation or virtualized range sizing.
- Runtime smoke check for large list/chart interaction without duplicate work.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
