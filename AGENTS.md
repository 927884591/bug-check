# Repository Rules

This repository packages the `bug-check` AI-agent skill.

## Change Rules

- Keep `skills/bug-check/SKILL.md` concise. It should contain workflow and routing only.
- Keep the detailed checklist in `skills/bug-check/references/bug-check.md`; do not duplicate it in README or SKILL.md.
- Keep scripts dependency-free unless a dependency removes real operational risk.
- Preserve the completion contract: root cause, changes, original-path verification, boundary cases, executed checks, and remaining risks.
- Run `python3 scripts/validate-project.py` before claiming changes are complete.

## Release Rules

- Update the Skill first, then README if installation or usage changes.
- Do not publish a GitHub release until `scripts/validate-project.py` passes.
- Do not change the skill name without also updating install paths, README commands, and `agents/openai.yaml`.
