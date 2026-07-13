Root cause: The filter request captured the old page before the reset.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two explicit files.
Behavior claims:
- C1 [source: specified] [source-ref: user wording: "Filter changes send page 1"]: A filter change sends the next request with page 1.
Counterexamples considered:
- C1: Scenario "42" with input 7.
Evidence:
- C1: PASS: The regression test in src/pages/UserList.test.tsx passed while asserting request page 1.
Checks run:
- PASS: `pytest tests/test_user_list.py` completed with exit code 0 and 1 test passed.
Remaining risks: The browser focus transition remains outside this fixture.
