# Repository Rules

This repository packages the `bug-check` AI-agent skill.

## Change Rules

- Keep `skills/bug-check/SKILL.md` concise. It should contain workflow and routing only.
- Keep `skills/bug-check/references/bug-check.md` as a short index only.
- Keep routing logic in `skills/bug-check/references/routing.md`.
- Keep reusable edge-case knowledge in focused boundary cards under `skills/bug-check/references/boundaries/`.
- Do not duplicate boundary-card details in README or SKILL.md.
- Keep scripts dependency-free unless a dependency removes real operational risk.
- Preserve the default user experience: `$bug-check` should use changed files to find relevant boundary cards, compare them against changed code, and fix missing handling. It should not be a separate report-writing step.
- Preserve the strict completion contract for explicit audits/checker use: root cause, changed files, context pack source, matched boundary cases, Boundary Handling Table, original-path verification, boundary verification, executed checks, and remaining risks.
- Run `python3 scripts/validate-project.py` before claiming changes are complete.

## Release Rules

- Update the Skill first, then README if installation or usage changes.
- Do not publish a GitHub release until `scripts/validate-project.py` passes.
- Do not change the skill name without also updating install paths, README commands, and `agents/openai.yaml`.
