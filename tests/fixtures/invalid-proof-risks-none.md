Root cause: The request retained stale state after a successful mutation.
Changed files: src/state/update.ts and src/state/update.test.ts.
Context source: Manual diff inspection of the listed files.
Behavior claims:
- C1 [source: specified] [source-ref: user wording: "A successful mutation replaces the visible stale state"]: A successful mutation replaces the visible stale state.
Counterexamples considered:
- C1: The mutation returns success while the prior state remains visible.
Evidence:
- C1: PASS: The regression test in src/state/update.test.ts passed while asserting that the successful response replaces the prior state.
Checks run: PASS: `npm test -- update.test.ts` completed with exit code 0.
Remaining risks: none.
