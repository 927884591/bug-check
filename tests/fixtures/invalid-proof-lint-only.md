Root cause: The request reused the prior page number after a filter mutation.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two listed files.
Behavior claims:
- C1 [source: specified] [source-ref: user wording: "A narrower filter sends the next request with page 1"]: Applying a narrower filter from page 3 sends the next request with page 1.
Counterexamples considered:
- C1: Start on page 3 and apply a filter with only one result page.
Evidence:
- C1: PASS: Inspection of src/pages/UserList.tsx confirms the page reset before request construction.
Checks run: PASS: `npm run lint` completed with exit code 0.
Remaining risks: The request behavior still requires an executed regression or runtime check.
