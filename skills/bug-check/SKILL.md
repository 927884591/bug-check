---
name: bug-check
description: Use when Codex implements new features or fixes, debugs, reviews, or validates any behavior-changing code and must avoid guessing product decisions and prove completion. Run before editing to classify requirement sources and unresolved decisions, then before completion to inspect impact and diff scope, falsify observable behavior claims with minimal counterexamples, and verify them with executed evidence.
---

# Bug Check

## Purpose

Prevent two common AI coding failures: implementing an unstated product rule and claiming completion without proving material behavior.

Use the loop:

```text
requirement/contract -> source -> acceptance claim -> impact/diff
-> smallest counterexample -> executed evidence -> pass/fix/decision needed
```

Do not turn this into a checklist report. The useful output is one engineering decision: `product-decision-required`, `continue-investigating`, `continue-fixing`, `runtime-evidence-required`, or `verified`.

## Workflow

1. Before editing, derive material behavior from the user request and available contracts: current behavior, tests, types, API schemas, designs, or documentation. Give each claim a stable `C1`-style ID and label it `specified`, `existing-contract`, `inferred`, or `product-decision-required` with concrete source evidence as defined in `references/behavior-contract.md`.
2. Do not silently turn a product suggestion or ambiguous rule into a requirement. If a material `product-decision-required` item blocks correct implementation, ask; otherwise keep it out of scope and report it. State narrow, reversible assumptions explicitly.
3. Write observable acceptance claims before implementation. Select only material counterexample families for the change, such as empty/error/loading states, permissions, retries, concurrency, reloads, cancellation, idempotency, or lifecycle transitions.
4. Inspect impact beyond the edited files: callers, consumers, contracts, persistent state, and nearby tests. If useful, run `scripts/build-bug-context.py` to collect a validated changed scope, diff context, nearby tests, and verification candidates.
5. Implement or review the smallest coherent change, then map every material claim to the resulting diff. If there are no valid changed files or explicit paths, do not produce a completion proof.
6. For each claim, name the smallest concrete counterexample that would disprove it and inspect whether the code handles it.
7. Run the narrowest verification that proves the original path and material counterexamples. Record the actual command or runtime check and its result; lint, typecheck, or build alone is insufficient.
8. If a material claim lacks handling or evidence:
   - For fix, implementation, or continuation work, patch the gap before finishing.
   - For review, audit, or checker work, report the proof gap first and do not patch unless the user asks.
9. For a pre-change exit, answer with the decision, sourced behavior contract, assumptions, and open product questions. Do not invent a root cause or completion evidence when no implementation exists.
10. For post-change work, answer with the decision first. Give the root cause for a bug or the change rationale for a new feature, then the changed scope, sourced claims, counterexamples, executed evidence, and remaining risks.

## Resources

- `references/behavior-contract.md`: read before coding when requirements, acceptance behavior, or product ownership are unclear.
- `scripts/build-bug-context.py`: builds a validated changed-scope, diff, nearby-test, verification-candidate, and proof-instruction pack.
- `references/completion-proof.md`: read only for explicit formal audits or checker-ready reports.
- `scripts/check-completion-proof.py`: lints formal report structure and obvious proof gaps; it cannot verify that claimed commands really ran.
