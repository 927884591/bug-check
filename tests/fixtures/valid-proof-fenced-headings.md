```text
Root cause: fake heading from captured output
Evidence: fake evidence from captured output
Checks run: none
```

Decision: verified
Root cause: The filter request captured the old page before the page-reset state update.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two explicit files.
Behavior claims:
- C1 [source: specified] [source-ref: user wording: "Send the filtered request from page 1"]: The request builder reads page 1 after a filter change.
Counterexamples considered:
- C1: If the request builder runs before the reset on page 3, a page 3 request would disprove the claim.
Evidence:
- C1: PASS: The test in src/pages/UserList.test.tsx captured the request after filtering and passed with page 1 asserted.
Checks run:
- PASS: `pytest tests/test_user_list.py` completed with exit code 0 and 1 test passed.
Remaining risks: The equivalent browser interaction was not exercised by this fixture.
