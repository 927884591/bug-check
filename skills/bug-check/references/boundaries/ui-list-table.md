# ui-list-table

## Applies When
- Changed files include list, table, grid, search, filter, sort, pagination, selection, or page/view components.
- Bug text mentions search, filter, reset, pagination, page 2+, selected rows, select all, empty state, sort, delete, or stale list data.

## Inspect
- Page index, page size, filters, query params, sort state, and URL state.
- Selected rows, all-select, cross-page selection, hidden IDs, and batch actions.
- List, detail, count, statistics, and action-button refresh after mutations.
- Loading, empty, filtered-empty, error, permission-denied, and last-item branches.
- Nearby tests for list transitions and table interactions.

## Handled When
- Search/filter/sort changes reset page index to page 1 unless product requirements explicitly preserve it.
- Pagination preserves current filters and sort.
- Reset clears visible inputs, hidden params, selected rows, dependent dropdowns, and cached table state.
- Delete or mutation on the last item moves to a valid page or shows the correct empty state.
- Empty, loading, error, permission, and filtered-empty states render distinctly.
- Batch actions never submit an empty or stale ID list.
- Code or tests cover the relevant state transition.

## Missing Means
- Current code has no branch, guard, state transition, cache update, invalidation, or test for a relevant list/table combination.
- The fix only covers the screenshot path while page 2+, filtered delete, reset, or selection state remains unproven.
- A passing lint/build is the only evidence for list behavior.

## Verify
- 0 results, 1 result, many results, and page 2+.
- Search/filter change while on page 2+.
- Reset after filters, sort, dependent dropdowns, and selected rows are set.
- Last-item delete, filtered deletion, select all, and batch delete.
- Slow, failing, and empty backend responses.
- Direct URL/query refresh when the page stores table state in the URL.

## Test Ideas
- Unit test for reducer/store transition from filtered page 3 to page 1.
- Integration test for search + pagination + reset.
- E2E test for select all + delete with filtered data.
- Regression test for last-item deletion producing a valid page.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
