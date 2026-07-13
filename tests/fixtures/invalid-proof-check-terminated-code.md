Decision: verified
Root cause: The filter request captured the old page before the reset.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two explicit files.
Behavior claims:
- C1 [source: specified] [source-ref: user wording: "Filter changes send page 1"]: A filter change sends the next request with page 1.
Counterexamples considered:
- C1: If the user filters from page 3 and the request still carries page 3, the claim is disproved.
Evidence:
- C1: PASS: The regression test asserted page 1 and passed.
Checks run:
- PASS: `npm test -- UserList.test.tsx` passed setup, then terminated with code 7.
Remaining risks: The browser focus transition remains outside this fixture.
