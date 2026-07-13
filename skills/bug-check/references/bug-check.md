# Bug Check Index

Use `$bug-check` before and after behavior-changing implementation: establish the behavior contract first, then prove the resulting change.

Core files:

- `../scripts/build-bug-context.py`: collects changed scope, diff context, nearby tests, and verification candidates.
- `behavior-contract.md`: separates specified behavior from inference and unresolved product decisions.
- `completion-proof.md`: formal proof report contract for explicit audit/checker output.
- `../scripts/check-completion-proof.py`: validates formal proof reports.

Default flow:

1. Classify each material behavior by source; ask when an unresolved product decision blocks correctness, otherwise keep it out of scope and report it.
2. State observable acceptance claims and inspect their impact surface.
3. Build a validated context pack and map the claims to the diff.
4. Falsify each claim with the smallest concrete counterexample.
5. Continue fixing until the original path and material counterexamples have executed evidence.
