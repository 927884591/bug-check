Root cause: The filter mutation kept the old page index after a narrower search, so page 3 requested an empty backend page while matching records existed on page 1.

Changed files:
- src/pages/UserList.tsx
- src/pages/UserList.test.tsx

Context source: `build-bug-context.py --files src/pages/UserList.tsx src/api/users.ts --bug "filter reset leaves page empty"`

Behavior claims:
- Changing a filter always resets the visible list to a valid page before fetching.
- A filtered empty response renders the filtered-empty state instead of a stale page result.

Counterexamples considered:
- User starts on page 3, applies a filter that has only one page of results.
- User applies a filter that returns zero results after previous data was visible.

Evidence:
- Reproduced the page 3 filtered-empty path before the fix.
- Inspected the page state transition and verified the filter handler resets page to 1 before the request.
- Added a regression test that asserts page reset and filtered-empty rendering.

Checks run:
- npm test -- UserList.test.tsx
- npm run lint

Remaining risks: Cross-page select-all was not exercised because this page does not enable batch selection.
