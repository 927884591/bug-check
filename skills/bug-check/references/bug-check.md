# Bug Check Matrix

Use these rules for frontend/product bug fixing, debugging, review, and validation.

## Core Principle

Do not fix only the visible happy path from the screenshot. Most repeat bugs came from missed state transitions, stale data, incomplete refresh, search/filter/pagination combinations, async task states, empty/error states, permission/session branches, and layout edge cases.

Before marking a bug fixed, identify which class it belongs to:

- state not refreshed
- data or statistics mismatch
- form validation or save failure
- search/filter/reset/pagination issue
- async task, upload, download, log, or deployment issue
- empty/error/last-item state
- permission, session, password, or role issue
- date, time zone, or date range issue
- concurrency, duplicate action, or stale response issue
- route, browser history, deep link, or URL state issue
- input method, pasted text, or special character issue
- browser cache, local storage, or frontend version upgrade issue
- tenant, project, site, or organization isolation issue
- accessibility or keyboard operation issue
- performance or large data volume issue
- video, device, alarm, map, or realtime polling issue
- UI layout, long text, scroll, or responsive issue
- API parameter or third-party integration issue
- frontend security, unsafe rendering, or sensitive data exposure issue

## Required Debug Flow

1. Reproduce the real path first. Do not infer from title alone.
2. Read the relevant page/component, state store/query cache, API call, and existing tests.
3. Determine the root cause category: state, data, UI, workflow, permission, async, or integration.
4. Fix the root cause, not only the symptom.
5. Verify the original path plus the relevant boundary matrix below.
6. Report exact verifications and any remaining unverified risks.

## Bug Check Matrix

### State Sync After Mutations

After create, edit, delete, enable, disable, stop, start, confirm, close, discard, or rollback:

- Refresh list, detail, cards, counters, charts, and action button states.
- Invalidate or update query cache/store/local component state consistently.
- Confirm route switching, tab switching, project/site/container switching, and page reload do not show stale state.
- Clean up timers, polling, subscriptions, pending requests, and old-context callbacks on unmount or context change.

### Search, Filter, Reset, Pagination

Always test these as combinations, not separate features:

- Search/filter changes reset page index to page 1.
- Pagination preserves current filters and sort.
- Reset clears visible inputs, hidden params, selected rows, dependent dropdowns, and cached table state.
- Test 0 results, 1 result, many results, last item, page 2+, large page sizes such as 100/1000, select all, cross-page selection, and filtered deletion.
- Never submit an empty ID list after all-select/delete flows.

### Data Consistency, Statistics, Units

For any count, status, metric, or displayed value:

- Use one trusted source of truth across list, detail, overview cards, charts, exports, and dialogs.
- Confirm backend success by reading back or refreshing actual data when the operation changes persisted data.
- Verify unit conversion and display: B/KB/MB, percent, temperature, humidity, duration, hours/minutes, date ranges, and file sizes.
- Check rounding, default values, null, empty string, zero, and missing fields.
- Confirm labels, placeholders, filenames, chart axes, and table columns match business wording.

### Forms, Validation, Save

Every form fix must consider:

- Empty values, max length, special characters, duplicate names, invalid dates, boundary dates, and end-before-start.
- Hidden fields must not remain required or be submitted incorrectly.
- Disabled/read-only fields must not be editable through stale state.
- Backend validation errors must stay visible; do not close the dialog or show success on failure.
- Slow requests and repeated submit clicks must not create duplicates or leave buttons stuck.

### Async Tasks, Files, Logs, Deployment

For logs, uploads, downloads, exports, imports, capture, rollback, deployment, or long-running jobs:

- Show loading/progress, success, failure, retry/cancel where applicable.
- Restore button and page state after success or failure.
- Use context-specific filenames when exporting/downloading, such as service IP, container name, and timestamp when relevant.
- Switching container/project/page during a task must not let old callbacks overwrite the new view.
- Verify failed upload/download/import paths with real backend errors.

### Empty, Error, Last-Item States

Do not treat all empty states the same:

- Distinguish no data, filtered no result, loading, request failure, permission denied, and not configured.
- Test deleting/confirming/processing the last item.
- After the current item disappears, explicitly decide whether to show next item, previous item, close dialog, or show empty state.
- Avoid leaving old data visible after a failed or empty request.

### Permission, Session, Password

Permission/session fixes must cover the full state machine:

- Logged out, logged in, session expired, password expired, no permission, and direct route access.
- Active user operation should not be mistaken for inactivity timeout.
- Login page refresh should not show a misleading "session expired" message.
- Permissions must be consistent across menu visibility, button enabled state, route access, and API handling.

### Date, Time Zone, Date Range

For date filters, statistics, exports, schedules, and expiration logic:

- Verify today, yesterday, this week, this month, cross-day, cross-month, cross-year, leap year, and daylight-saving boundaries where applicable.
- Confirm whether start and end dates are inclusive or exclusive, and keep that behavior consistent between UI, API parameters, exported data, and charts.
- Check frontend local time zone, backend/server time zone, UTC timestamps, and formatted display values for mismatches.
- Verify default ranges, manually typed dates, cleared dates, invalid dates, end-before-start, and boundary times such as 00:00:00 and 23:59:59.
- Confirm date range filters and date labels use the same business meaning across list, detail, statistics, and export flows.

### Concurrency, Duplicate Actions, Stale Responses

For save, delete, confirm, submit, retry, and any state-changing operation:

- Prevent repeated clicks, double submits, duplicate creates, duplicate deletes, and repeated binding/unbinding while a request is pending.
- Verify slow request, failed request, retry, cancel, and optimistic update rollback behavior.
- Ensure an older response cannot overwrite a newer request result after search/filter/tab/context changes.
- Consider two tabs, two dialogs, or two users editing the same record when the workflow allows it.
- Confirm idempotency expectations with backend behavior instead of assuming repeated calls are safe.

### Routes, Browser History, Deep Links

For page, tab, detail, and query-string state:

- Verify direct URL access, browser refresh, back, forward, and opening links in a new tab.
- Keep URL query, route params, visible filters, selected tab, pagination, and component state consistent.
- Handle missing list context when entering a detail page directly.
- Define behavior when a deep-linked record is deleted, moved, unauthorized, or no longer belongs to the current project/site/tenant.
- Avoid showing stale previous-page data while a route-level request for the new page is loading or failing.

### Input Method, Pasted Text, Special Characters

For search boxes, forms, names, codes, descriptions, and rich text:

- Verify Chinese IME composition does not trigger premature search, validation, or submit behavior.
- Handle leading/trailing spaces, full-width and half-width characters, newlines, tabs, invisible characters, emoji, and special symbols.
- Test paste behavior for long text, multiline text, rich text, and values copied from spreadsheets.
- Confirm max length, byte length, display length, backend validation, and UI counters use compatible rules.
- Be explicit about case sensitivity, exact match, fuzzy match, and whitespace normalization.

### Browser Cache, Local Storage, Version Upgrades

For persisted frontend state and deployments:

- Verify old localStorage/sessionStorage/cache data does not break current code after a frontend release.
- Clear or migrate stale cached user info, permissions, feature flags, route state, table settings, and form drafts when their schema changes.
- Confirm logout, tenant/project switch, password change, and permission changes clear sensitive or context-specific caches.
- Check behavior when old static assets call newer APIs or new static assets receive older cached API-shaped data.
- Do not let persisted filters, selected rows, hidden columns, or old tab state make the page appear broken after navigation or upgrade.

### Tenant, Project, Site, Organization Isolation

For any multi-tenant or multi-context page:

- Confirm every list, detail, option query, mutation, export, and websocket/polling request uses the active tenant/project/site/org context.
- Verify switching context clears or reloads selected rows, detail panels, cached dropdown options, recent records, statistics, and permissions.
- Ensure data from one tenant/project/site/org cannot appear through search, export, detail URLs, browser history, or cached stores.
- Check default selections and dependent dropdowns after context changes.
- Treat cross-context data exposure as a security issue, not only a display bug.

### Accessibility and Keyboard Operation

For modals, forms, menus, tables, and icon-only actions:

- Verify focus moves into dialogs/drawers and returns to the triggering control when they close.
- Check Tab order, Enter submit behavior, Escape close behavior, disabled controls, and keyboard-only operation.
- Icon-only buttons need accessible names, and error messages should be associated with the relevant input when the framework supports it.
- Confirm loading, error, empty, and permission states are understandable without relying only on color.
- Disabled or hidden actions must not remain triggerable through keyboard shortcuts, stale focus, or direct DOM events.

### Performance and Large Data Volume

For tables, trees, charts, maps, video, polling, and heavy forms:

- Test large page sizes, many selected rows, many dropdown options, deep trees, long logs, and high-frequency updates.
- Use debounce/throttle/cancellation intentionally for search, resize, scroll, polling, and realtime updates.
- Clean up timers, subscriptions, event listeners, observers, map/video instances, and pending requests on unmount or context change.
- Avoid full re-rendering, repeated expensive formatting, and repeated chart/map/video initialization on small state changes.
- Verify the UI remains usable during loading, filtering, selecting all, exporting, and expanding/collapsing large data sets.

### Video, Device, Alarm, Map, Realtime

For video streams, cameras, alarms, maps, devices, and polling:

- Verify view mode versus edit mode.
- Verify realtime status updates reach video frame, map marker, alarm list, cards, and buttons.
- Confirm stream URL precedence after the user enters a custom stream URL and revisits the device.
- Cover offline, online, alarm active, alarm cleared, no alarm, and last alarm.
- Map drawing must handle unfinished polygons, cancel, double-click, repeated drawing, and click behavior in non-edit mode.

### UI Layout, Long Text, Responsive

Layout is a functional requirement:

- Test long names, long codes, long error messages, and long table cell values.
- Use wrapping, ellipsis plus tooltip, scroll areas, or column constraints intentionally.
- Check modal/drawer height, bottom action visibility, table pagination footer, and large page sizes.
- Verify with an actual rendered page or screenshot for visual fixes, not only type/lint checks.

### API Parameters and Third-Party Integration

For API/integration bugs:

- Inspect the real network request before and after the fix.
- Verify parameters for each branch, protocol, mode, selected item, and default state.
- Distinguish third-party not synced, syncing, synced empty, API failed, and field missing.
- Do not assume API success means business success; validate returned data and UI rendering.

### Frontend Security and Sensitive Data

For rendered backend content, links, downloads, logs, and client-side state:

- Do not render HTML from URL params, backend messages, table cells, tooltips, dialogs, or rich text without a deliberate sanitization path.
- Check download, preview, share, and detail links for permission bypass through copied URLs or stale cached tokens.
- Avoid exposing passwords, tokens, cookies, tenant IDs, private URLs, or personally identifiable information in console logs, analytics, telemetry, error reports, or screenshots.
- Verify user-controlled filenames, CSV/Excel content, and exported formulas cannot create injection or unsafe-open behavior.
- Treat frontend-only permission hiding as insufficient; verify API errors and UI handling for unauthorized access.

## Completion Contract

Do not mark a bug as fixed until the final response includes:

- The root cause.
- The files or behavior changed.
- The original reproduction path verification.
- Boundary cases verified from this document.
- Tests/lint/build/UI checks run.
- Remaining risks or cases not verified.

If any relevant boundary above was not verified, say so explicitly. Do not replace real verification with "precheck passed" or "lint passed".

## Prompt Snippet for Future AI Bug Fixes

```text
Read the current code, API calls, state/cache, and existing tests before fixing. Do not guess from the title.
Fix the root cause and verify the original path plus relevant edge cases:
- mutation refresh across list/detail/statistics/buttons
- search/filter/reset/pagination/select-all
- empty/one/many/last item
- backend success/failure/slow response
- hidden/disabled/form validation fields
- date range/time zone boundaries
- duplicate clicks/concurrent requests/stale responses
- direct URL/refresh/back-forward/query state
- tenant/project/site isolation and cache cleanup
- IME/paste/special-character inputs
- context switching and stale request cleanup
- accessibility keyboard paths and focus state
- large data volume/performance cleanup
- long text/layout/large page size
- real network parameters and returned data
- unsafe rendering/download links/sensitive data exposure
Final answer must include root cause, changes, executed verification, and remaining risks.
```
