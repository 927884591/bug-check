# navigation-url-state

## Applies When
- Changed files include routing, navigation guards, redirects, URL query params, route loaders, breadcrumbs, tabs, filters in the URL, deep links, or browser history behavior.
- Bug text mentions back, forward, refresh, deep link, redirect, query params, URL state, route switch, browser history, copied link, or state lost after reload.

## Do Not Select When
- The changed code has no route, URL, history, redirect, tab, deep-link, or reload-visible state behavior.
- The issue is only in-memory list or cache state and the URL never represents or restores that state.
- The route is protected by auth and the failure is only login/session/permission behavior; use auth-permission instead.

## Inspect
- Source of truth for route params, query params, hash, browser history state, tabs, filters, pagination, and selected detail IDs.
- Initial load, refresh, copied URL, direct navigation, back/forward, redirect, and route replacement paths.
- Serialization and parsing of query values, defaults, unknown values, arrays, booleans, dates, numbers, and encoded characters.
- Interaction between URL state, local state, cache keys, loaders, guards, and context such as tenant or permissions.
- Tests or runtime checks for deep links and browser navigation transitions.

## Handled When
- URL state and in-memory state converge after initial load, refresh, back/forward, and copied deep links.
- Defaults, omitted params, invalid params, duplicate params, and encoded values behave deliberately.
- Navigation updates do not lose unsaved or selected state unless product requirements say so.
- Redirects preserve or intentionally drop return paths, filters, context, and user-visible error state.
- Tests or runtime checks cover at least one direct URL and one browser-history transition when relevant.

## Missing Means
- The fix only works after clicking through the UI and fails on refresh, copied URL, or back/forward.
- Query parsing treats missing, empty, invalid, and default values as the same without evidence.
- Local state and URL state can diverge after route switch, tab switch, redirect, or context switch.
- Redirects drop required params, return paths, filters, or error state.
- Verification only clicks forward through the happy path and does not exercise browser history.

## Verify
- Direct URL, copied link, refresh, back, forward, and route replacement.
- Missing, empty, invalid, duplicate, encoded, and unknown query params.
- Filter, tab, pagination, selected row/detail, and tenant/context state after navigation where relevant.
- Redirect after login/session expiry/no permission and return-path preservation where relevant.
- Route switch while data is loading or unsaved state is present.

## Test Ideas
- Router test for query param parse/serialize round trip.
- Integration test for direct deep link restoring visible state.
- E2E test for back/forward after filter, tab, or detail navigation.
- Regression test for redirect preserving intended return path and safe defaults.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
