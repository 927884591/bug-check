Root cause: The request reused the prior page number after a filter mutation.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two listed files.
Behavior claims:
- C1: [source: specified] [source-ref: user wording: "A narrower filter sends the next request with page 1"] Applying a narrower filter from page 3 sends the next request with page 1.
- C2: [source: existing-contract] [source-ref: src/pages/UserList.test.tsx: stale-row regression] An empty filtered response removes rows from the prior response.
Counterexamples considered:
- C1: Starting on page 3 and selecting a one-page filter disproves the claim if the request still carries page 3.
- C3: A rejected request that displays a success banner would disprove an unrelated error-state claim.
Evidence:
- C1: PASS: Inspection of src/pages/UserList.tsx shows the page reset before request construction, and the regression test passed while asserting page 1.
Checks run: PASS: `npm test -- UserList.test.tsx` completed with exit code 0 and 2 tests passed.
Remaining risks: Browser rendering was not part of this proof report.
