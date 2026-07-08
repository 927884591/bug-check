# Bug Check Index

Use `$bug-check` as a pre-final completion proof gate for bug fixes and risky behavior changes.

Core files:

- `../scripts/build-bug-context.py`: collects changed scope, diff context, nearby tests, and verification candidates.
- `completion-proof.md`: formal proof report contract for explicit audit/checker output.
- `../scripts/check-completion-proof.py`: validates formal proof reports.

Default flow:

1. Build a context pack from changed files and bug text.
2. Inspect the diff and state material behavior claims.
3. Try to falsify each claim with the smallest concrete counterexample.
4. Continue fixing if a counterexample is not handled or not verified.
5. Verify the original path and material counterexamples before claiming completion.
