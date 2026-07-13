Decision: verified
Root cause: Option-like revisions reached Git as options, and the authentication error fixture previously conflated an expected business failure with a failed test command.
Changed files:
- skills/bug-check/scripts/build-bug-context.py
- tests/test_invalid_inputs.py
Context source: Manual diff inspection of the two explicit files.
Behavior claims:
- C1 [source: specified] [source-ref: user wording: "Reject option-like revision input without side effects"]: An option-like revision returns exit 2 and creates no output file.
- C2 [source: existing-contract] [source-ref: tests/test_invalid_inputs.py: failed-login response contract]: A failed login returns HTTP 401 with response payload status: error.
Counterexamples considered:
- C1: If `--base=--output=x` returns zero or creates x, either outcome disproves rejection safety.
- C2: If invalid credentials return HTTP 200 or a success payload, the authentication-error contract is disproved.
Evidence:
- C1: PASS: The regression test passed while asserting subprocess exit 2 and no output file.
- C2: PASS: The failed login returned HTTP 401 and response payload status: error, as asserted by the regression test.
Checks run:
- PASS: `python3 scripts/validate-project.py` exited 0; its subprocess assertion observed the expected exit 2 for the invalid input.
Remaining risks: Git implementations with nonstandard option parsing remain outside the tested runtime matrix.
