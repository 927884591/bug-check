Root cause: The request reused the prior page number after a filter mutation.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two listed files.
Behavior claims:
- C1: [source: specified] [source-ref: user wording: "A narrower filter sends the next request with page 1"] Applying a narrower filter from page 3 sends the next request with page 1.
Counterexamples considered:
- C1: Starting on page 3 and selecting a one-page filter would disprove the claim if the request still carried page 3.
Evidence:
- C1: Not tested; not verified because the test runner was unavailable.
Checks run: PASS: `python3 -m unittest tests.test_report` completed with exit code 0.
Remaining risks: Browser rendering was not part of this proof report.
