Decision: verified
Change rationale: The new filter mutation must preserve the accepted pagination reset while reusing the existing request builder.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two explicit files.
Behavior claims:
- C1 [source: inferred] [source-ref: explicit assumption: preserve the existing page-reset request order]: The filter handler writes page 1 before constructing the next request.
Counterexamples considered:
- C1: If a page 3 filter request is constructed before the reset, the request page would remain 3 and disprove the ordering claim.
Evidence:
- C1: The regression test in src/pages/UserList.test.tsx observed the request page after the filter event; result: 0 failed, 12 passed.
Checks run:
- `pytest tests/test_user_list.py` -> 0 failed, 12 passed.
Remaining risks: The browser-only focus transition remains outside this request-order proof.
