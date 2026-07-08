# Repository Rules

This repository packages the `bug-check` AI-agent skill.

## Change Rules

- Keep `skills/bug-check/SKILL.md` concise. It should contain the core proof workflow and resource routing only.
- Keep `skills/bug-check/references/bug-check.md` as a short index only.
- Keep `skills/bug-check/references/completion-proof.md` as the formal checker/report contract.
- Preserve the default user experience: `$bug-check` should inspect changed code, state behavior claims, try to falsify them with minimal counterexamples, and require evidence before completion.
- Do not reintroduce the old taxonomy, routing, or promotion machinery.
- Keep scripts dependency-free unless a dependency removes real operational risk.
- Run `python3 scripts/validate-project.py` before claiming changes are complete.

## Release Rules

- Update the Skill first, then README if installation or usage changes.
- Do not publish a GitHub release until `scripts/validate-project.py` passes.
- Do not change the skill name without also updating install paths, README commands, and `agents/openai.yaml`.
