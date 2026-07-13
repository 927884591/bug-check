Root cause: The filter request captured the old page before the reset, and the empty response retained stale rows.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two explicit files.
Behavior claims:
- C1 [source: specified] [source-ref: user wording: "Filter changes send page 1"]: A filter change sends the next request with page 1.
- C2 [source: existing-contract] [source-ref: src/pages/UserList.test.tsx: filtered-empty regression]: An empty filtered response removes stale rows.
Counterexamples considered:
- C1: If the user filters from page 3 and the request still carries page 3, the claim is disproved.
- C2: If an empty response arrives after visible rows and those rows remain, the claim is disproved.
Evidence:
- C1: Inspection of src/pages/UserList.tsx shows the page reset before request construction.
- C2: PASS: The regression test in src/pages/UserList.test.tsx passed while asserting that stale rows disappear.
Checks run:
- PASS: `pytest tests/test_user_list.py` completed with exit code 0 and 2 tests passed.
Remaining risks: The browser focus transition remains outside this fixture.
