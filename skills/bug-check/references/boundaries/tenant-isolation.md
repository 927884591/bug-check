# tenant-isolation

## Applies When
- Changed files include tenant, project, site, organization, workspace, context switch, scoped APIs, dropdown options, exports, websocket/polling, or cache keys.
- Bug text mentions tenant, project, site, org, workspace, isolation, cross-context data, leak, switch, stale options, or wrong records.

## Inspect
- Active tenant/project/site/org propagation through list, detail, mutation, export, polling, and websocket calls.
- Cache keys, selected rows, dropdown options, recent records, statistics, permissions, and local storage.
- Detail URLs, browser history, direct navigation, copied links, and exports.
- Server-side filters and authorization on every read/write path.
- Context switch cleanup and default selections.

## Handled When
- Every read, write, option query, export, and realtime request includes the active context or has a documented global scope.
- Switching context clears or reloads selections, detail panels, dropdowns, recent records, statistics, permissions, and subscriptions.
- Cache keys include context dimensions.
- Cross-context detail URLs and exports are rejected or redirected safely.
- Server-side authorization prevents object-level data exposure.

## Missing Means
- Only the visible list query includes context while detail, export, options, or mutations do not.
- Cache or store data survives a context switch without proof it is global.
- UI filtering is used as the only isolation control.
- No verification covers copied URLs, browser history, or export paths.

## Verify
- Switch tenant/project/site/org with selected rows, open detail, dropdowns, and statistics visible.
- Direct URL to a record from another context.
- Export/download and websocket/polling after context switch.
- Mutation against a stale selected record from the previous context.
- Cache/local storage after logout or permission/context change.

## Test Ideas
- Integration test for context switch clearing scoped stores.
- API test for cross-tenant object access rejection.
- E2E test for copied detail URL from another tenant.
- Cache-key unit test including tenant/project/site dimensions.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
