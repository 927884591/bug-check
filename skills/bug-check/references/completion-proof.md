# Completion Proof Contract

Formal reports must prove the original path and each material behavior claim. Use this contract only for explicit audit/checker output.

Required fields:

```text
Root cause:
Changed files:
Context source:
Behavior claims:
Counterexamples considered:
Evidence:
Checks run:
Remaining risks:
```

Minimum evidence:

- `Root cause:` names the failed mechanism, not only the symptom.
- `Changed files:` lists the files or clearly states no code files changed.
- `Context source:` says whether evidence came from `build-bug-context.py`, a manual diff review, explicit files, or a user-provided report.
- `Behavior claims:` states observable claims created or fixed by the diff.
- `Counterexamples considered:` names the smallest concrete cases that would disprove each material claim.
- `Evidence:` ties claims to code inspection, tests, runtime checks, browser checks, logs, screenshots, request/response samples, or equivalent proof.
- `Checks run:` lists actual commands or manual runtime checks.
- `Remaining risks:` names unverified cases or says none after evidence.

A lint, typecheck, or build pass alone is not completion evidence for a behavior claim.
