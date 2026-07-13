Root cause: The request reused the prior page number after a filter mutation.
Changed files: src/pages/UserList.tsx and src/pages/UserList.test.tsx.
Context source: Manual diff inspection of the two listed files.
Behavior claims:
- C1: [source: inferred] [source-ref: explicit assumption: preserve the existing filter request semantics] The filter works correctly for all inputs.
Counterexamples considered:
- C1: All edge cases were considered.
Evidence:
- C1: The regression test in src/pages/UserList.test.tsx asserts the page-reset request and passed.
Checks run: PASS: `npm test -- UserList.test.tsx` completed with exit code 0.
Remaining risks: The browser path remains outside this fixture's scope.
