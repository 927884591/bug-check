Root cause: The filter mutation kept the old page index after a narrower search, so page 3 requested an empty backend page while matching records existed on page 1.

Changed files:
- src/pages/UserList.tsx
- src/pages/UserList.test.tsx

Context pack source: `build-bug-context.py --files src/pages/UserList.tsx src/api/users.ts --bug "filter reset leaves page empty"`

Matched boundary cases:
- ui-list-table
- state-cache-sync
- api-contract

Boundary handling table:

| Boundary | Status | Evidence | Action |
|---|---|---|---|
| ui-list-table | missing -> fixed | filter changes on page 3 did not reset page index | reset page to 1 and added regression test |
| state-cache-sync | already handled | existing query key includes filters and page | no change |
| api-contract | already handled | API client already sends filter params and page params separately | no change |

Original path verification: Reproduced page 3 filtered empty state, applied the fix, and verified the filtered results appear on page 1.

Boundary verification:
- ui-list-table: covered filter change from page 3, reset, and empty result branch.
- state-cache-sync: verified existing query key changes with filters.
- api-contract: inspected request params for filter and page.

Checks run:
- npm test -- UserList.test.tsx
- npm run lint

Remaining risks: Cross-page select-all was inspected but not exercised manually because this page does not enable batch selection.
