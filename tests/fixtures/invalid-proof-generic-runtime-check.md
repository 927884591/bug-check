Root cause: The request reused the prior page number after a filter mutation.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two listed files.
Behavior claims:
- C1: [source: specified] [source-ref: user wording: "A narrower filter sends the next request with page 1"] Applying a narrower filter from page 3 sends the next request with page 1.
Counterexamples considered:
- C1: Starting on page 3 and selecting a one-page filter would disprove the claim if the request still carried page 3.
Evidence:
- C1: PASS: Inspection of src/pages/UserList.tsx shows the page reset before request construction, and the regression test passed while asserting page 1.
Checks run: PASS: manual runtime check.
Remaining risks: Browser rendering was not part of this proof report.
