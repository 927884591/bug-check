# realtime-subscription

## Applies When
- Changed files include WebSocket, SSE, realtime subscriptions, polling replacement, presence, notifications, collaborative state, event streams, reconnect logic, or pub/sub handlers.
- Bug text mentions websocket, SSE, realtime, subscription, reconnect, duplicate event, out of order, missed update, stale presence, disconnect, offline, or live data mismatch.

## Do Not Select When
- The changed path uses ordinary request/response fetching only and has no long-lived stream, subscription, channel, reconnect, or live event delivery.
- The async risk is a single stale promise/timer in the UI; use client-async-race instead.
- The live transport is untouched and the bug is only post-event cache invalidation in local state; use state-cache-sync instead.

## Inspect
- Connection lifecycle, authentication, reconnect/backoff, resubscription, heartbeat, and cleanup on route/context changes.
- Event schema, sequence/version handling, duplicate delivery, out-of-order events, and missed-event recovery.
- Initial snapshot versus live updates, cache invalidation, optimistic updates, and polling fallback behavior.
- Tenant/user/permission context in channels, topics, filters, and server-side publish paths.
- UI states for connecting, live, stale, offline, retrying, error, and permission denied.

## Handled When
- Initial data and live events converge to the same state after reconnect, refresh, or context switch.
- Duplicate, stale, missed, and out-of-order events are ignored, replayed, or reconciled deliberately.
- Subscriptions are scoped by active tenant/user/permission and are cleaned up on logout, route change, or unmount.
- Reconnect and offline behavior avoids duplicate listeners, duplicate toasts, and stale UI.
- Tests or runtime checks cover reconnect, duplicate event, and context switch paths when relevant.

## Missing Means
- The fix assumes events arrive once, in order, and only while the UI is mounted.
- Reconnect adds listeners without removing old ones.
- Channel names, filters, or cache keys omit tenant/user/permission dimensions.
- UI shows live success even when the stream is disconnected, stale, or unauthorized.
- Verification only reloads the page or covers the initial snapshot, not the live path.

## Verify
- Initial load followed by live create/update/delete events.
- Disconnect, reconnect, resubscribe, and missed-event recovery.
- Duplicate event, out-of-order event, stale event after context switch, and unauthorized channel access.
- Route change, tab close, logout, tenant switch, and unmount cleanup.
- Offline, retrying, stale, and recovered UI states.

## Test Ideas
- Integration test for initial snapshot plus ordered and out-of-order events.
- Fake transport test for reconnect without duplicate listeners.
- Cache/state test proving stale tenant or user events are ignored.
- E2E or component test for offline/retry/live status transitions.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
