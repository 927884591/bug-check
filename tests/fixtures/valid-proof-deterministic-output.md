Decision: verified
Change rationale: The accepted export contract requires repeat executions to produce the same bytes for the same normalized input.
Changed files: src/export/deterministic.py and tests/test_deterministic_export.py.
Context source: Manual diff inspection of the two explicit files.
Behavior claims:
- C1 [source: existing-contract] [source-ref: tests/test_deterministic_export.py: repeated-input contract]: Two executions with identical input yield byte-for-byte identical output.
Counterexamples considered:
- C1: If the second execution returns a different byte for identical input, the deterministic-output claim is disproved.
Evidence:
- C1: PASS: The regression test executed the export twice, compared both byte arrays, and passed with identical output.
Checks run:
- PASS: `pytest tests/test_deterministic_export.py` completed with exit code 0 and 1 test passed.
Remaining risks: Cross-version serializer differences remain outside this same-runtime proof.
