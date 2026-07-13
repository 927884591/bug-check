Root cause: The request reused the prior page number after a filter mutation.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two listed files.
Behavior claims:
- C1: [source-ref: user wording: "A narrower filter sends the next request with page 1"] Applying a narrower filter from page 3 sends the next request with page 1.
- C2 [source: product-decision-required] [source-ref: user request: "Choose an empty response presentation"]: The empty response presentation still needs a product decision.
Counterexamples considered:
- C1: Starting on page 3 and selecting a one-page filter disproves the claim if the request still carries page 3.
- C2: Returning zero records disproves the claim if old rows remain visible.
Evidence:
- C1: PASS: Inspection of src/pages/UserList.tsx shows the page reset before request construction, and the regression test passed while asserting page 1.
- C2: PASS: The test in src/pages/UserList.test.tsx passed while asserting that prior rows disappear after the empty response.
Checks run: PASS: `npm test -- UserList.test.tsx` completed with exit code 0 and 2 tests passed.
Remaining risks: Browser rendering was not part of this proof report.
