---
name: bug-check
description: Use when fixing, debugging, reviewing, or validating bugs or risky behavior changes and Codex must prove completion from changed code. Run as a pre-final completion proof gate: inspect the diff, state behavior claims, try to falsify them with minimal counterexamples, verify evidence, and continue fixing or report risk before claiming completion.
---

# Bug Check

## Purpose

Before claiming a bug fix or risky behavior change is complete, prove the changed behavior from code and executed evidence.

Use the loop:

```text
diff -> behavior claim -> smallest counterexample -> code/evidence -> pass/fail
```

Do not turn this into a checklist report. The useful output is an engineering decision: continue fixing a proof gap, run missing verification, or state the proof and remaining risk.

## Workflow

1. Get the changed scope from the current diff, staged diff, a base/range diff, or user-provided files. If useful, run `scripts/build-bug-context.py` to collect changed files, diff context, nearby tests, and verification candidates.
2. If there are no changed files or explicit paths, do not produce a completion proof. Bug text alone can suggest tentative claims and counterexamples, but it cannot prove completion.
3. Inspect the changed code and state each material behavior claim the fix relies on. A claim must be observable, such as "filtering resets to a valid page" or "403 responses never render success state".
4. For each claim, name the smallest counterexample that would disprove it. Prefer concrete state transitions, bad inputs, stale async timing, permission failures, empty/null values, reloads, or runtime lifecycle cases.
5. Check whether the current code handles each counterexample. If a material claim lacks handling or evidence:
   - For fix, implementation, or continuation work, patch the gap before finishing.
   - For review, audit, or checker work, report the proof gap first and do not patch unless the user asks.
6. Run the narrowest useful verification for the original path and the material counterexamples. A broad lint/build pass is not enough by itself.
7. Answer briefly with the root cause, changed files, claims, counterexamples, evidence, checks run, and remaining risks. Use `references/completion-proof.md` only when the user asks for a formal proof report or checker-ready output.

## Resources

- `scripts/build-bug-context.py`: builds a changed-scope, diff, nearby-test, verification-candidate, and proof-instruction pack.
- `references/completion-proof.md`: formal proof report contract for explicit audits or checker-ready reports.
- `scripts/check-completion-proof.py`: optional checker for proof reports.
