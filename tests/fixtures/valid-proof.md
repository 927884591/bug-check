Decision: verified

Root cause: The filter mutation retained the old page index after a narrower search, so page 3 requested an empty backend page while matching records existed on page 1.

Changed files:
- src/pages/UserList.tsx
- src/pages/UserList.test.tsx

Context source: `build-bug-context.py --files src/pages/UserList.tsx src/pages/UserList.test.tsx --bug "filter reset leaves page empty"`, followed by manual diff inspection.

Behavior claims:
- C1 [source: specified] [source-ref: user request: "Changing a filter resets the visible list to page 1"]: Changing a filter resets the visible list to page 1 before the filtered request is sent.
- C2: [source: existing-contract] [source-ref: src/pages/UserList.test.tsx: filtered-empty regression] A filtered response with zero records renders the filtered-empty state instead of retaining stale rows.

Counterexamples considered:
- C1: If the user starts on page 3 and applies a filter whose matching records fit on one page, a request for page 3 would disprove the reset claim.
- C2: Previous rows are visible when the user applies a filter that returns zero records; any retained row or generic page-empty state disproves the rendering claim.

Evidence:
- C1: PASS: Inspection of `src/pages/UserList.tsx` shows the filter handler setting page 1 before constructing the request, and the regression test passed while asserting the request page.
- C2: PASS: `src/pages/UserList.test.tsx` contains a regression test that seeds prior rows, returns an empty filtered response, and passed while asserting the filtered-empty state with no stale rows.

Checks run:
- PASS: `npm test -- UserList.test.tsx` completed with exit code 0 and 2 tests passed.
- PASS: Manual runtime check applied a one-page filter from page 3 and an empty filter after visible data; both rendered the expected states.

Remaining risks: Cross-page select-all was not exercised because this page does not enable batch selection.
