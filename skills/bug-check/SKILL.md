---
name: bug-check
description: Use when fixing, debugging, reviewing, or validating frontend/product bugs, especially defects involving state refresh, forms, lists, search/filter/pagination, async tasks, permissions, realtime/video/map flows, routing, cache, tenants, accessibility, performance, layout, API parameters, security, or repeated bug reactivation. Guides an AI coding agent to inspect code paths, classify root causes, load the bug-check matrix, verify edge cases, and report root cause, changes, verification, and residual risk.
---

# Bug Check

## Operating Rule

Use this skill for bug fixing, debugging, code review, and bug validation. Do not use it for unrelated feature ideation, formatting, one-off shell commands, or purely explanatory work.

When this skill triggers, read `references/bug-check.md` before editing code or claiming completion. Treat the reference as a checklist for missed edge cases, not as a replacement for reading the current code and reproducing the real path.

## Workflow

1. Reproduce or trace the real bug path. Do not infer the fix from the title or screenshot alone.
2. Read the relevant page/component, state store or query cache, API call, and existing tests.
3. Classify the root cause with the bug-check categories in `references/bug-check.md`.
4. Fix the root cause with the smallest change that preserves existing conventions.
5. Verify the original path and the relevant boundary cases from the reference.
6. Run available lint, typecheck, tests, build, and UI checks that match the risk.
7. Report root cause, changed behavior/files, original-path verification, boundary cases verified, executed checks, and remaining unverified risks.

## Resource Routing

- Load `references/bug-check.md` for the full bug-check matrix and completion contract.
- Use `scripts/check-bug-report.py` only when a deterministic check of a final bug-fix report is useful. It reads a report from a file or stdin and verifies that the required completion sections are present.

## Completion Standard

Do not mark a bug as fixed if the original path was not verified or if relevant boundary cases were skipped without saying so. Passing lint or a narrow precheck is supporting evidence, not proof of bug closure.
