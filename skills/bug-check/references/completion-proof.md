# Completion Proof Contract

Formal reports must trace each material behavior claim from its source to a counterexample and executed evidence. Use this contract only for explicit post-change audit/checker output. For a pre-change `product-decision-required` exit, use `behavior-contract.md` instead; do not fabricate a root cause, diff, or evidence.

Required fields:

```text
Decision: verified
Root cause: failed mechanism for a bug, or use Change rationale for a new feature
Changed files:
Context source:
Behavior claims:
Counterexamples considered:
Evidence:
Checks run:
Remaining risks:
```

Minimum evidence:

- `Decision:` uses exactly one workflow label. A passing formal completion proof must use `verified`; the other four labels are valid workflow exits, not completion decisions.
- `Root cause:` names the failed mechanism for a bug; `Change rationale:` names the accepted behavior contract for a new feature.
- `Changed files:` lists at least one concrete changed or explicitly reviewed path. A no-change/pre-change report is not a completion proof.
- `Context source:` says whether evidence came from `build-bug-context.py`, a manual diff review, explicit files, or a user-provided report.
- `Behavior claims:` uses stable IDs such as `C1`, keeps the same behavior-contract ID, states each observable claim, names its source as `specified`, `existing-contract`, or `inferred`, and includes a concrete `[source-ref: ...]` whose evidence type agrees with that source label. Unresolved product decisions cannot be passing claims.
- `Counterexamples considered:` uses the same claim IDs and names the smallest concrete case that would disprove each claim.
- `Evidence:` uses the same claim IDs and ties them to code inspection plus tests, runtime checks, browser checks, logs, screenshots, request/response samples, or equivalent proof and result.
- `Checks run:` lists actual commands or manual runtime checks with their observed result, such as `exit 0`, `PASS`, `FAIL`, or an HTTP/runtime status. Any unresolved `FAIL` or non-zero exit prevents a passing completion report.
- `Remaining risks:` names unverified cases or explains why none remain after the listed evidence.

A lint, typecheck, or build pass alone is not completion evidence for a behavior claim.

Example claim linkage:

```text
Decision: verified
Behavior claims:
- C1 [source: specified]: [source-ref: user requirement "changing a filter starts from page 1"] Changing a filter resets the visible list to page 1.
Counterexamples considered:
- C1: Start on page 3 and apply a filter with only one result page.
Evidence:
- C1: Regression test asserted the request used page 1 and passed.
Checks run:
- `npm test -- UserList.test.tsx` -> exit 0
```

`check-completion-proof.py` checks this report structure and rejects obvious placeholders, mismatched source provenance, missing linkage, and negative evidence. It is a heuristic report linter, not a semantic judge: it does not independently prove that claims are meaningful, commands were executed, or evidence is truthful. Completion still requires the agent to run and inspect the checks.
