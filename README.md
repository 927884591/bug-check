# bug-check

AI-agent skill for frontend/product bug fixing. It forces bug work to cover root cause, real reproduction paths, state/cache/API inspection, edge-case verification, and residual risk reporting.

## Architecture

```text
.
├── AGENTS.md
├── README.md
├── scripts/
│   ├── check-bug-report.py
│   ├── install-local.sh
│   └── validate-project.py
└── skills/
    └── bug-check/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/bug-check.md
        └── scripts/check-bug-report.py
```

- `skills/bug-check/SKILL.md`: skill entrypoint. Short workflow and resource routing.
- `skills/bug-check/references/bug-check.md`: single source of truth for the bug-check matrix.
- `skills/bug-check/scripts/check-bug-report.py`: deterministic final-report checker.
- `scripts/install-local.sh`: installs the skill into `$AGENT_SKILLS_DIR/bug-check`.
- `scripts/validate-project.py`: repository and skill validation for local use and CI.

## Install

```bash
export AGENT_SKILLS_DIR="$HOME/.agents/skills"
./scripts/install-local.sh
```

Manual install:

```bash
mkdir -p "$AGENT_SKILLS_DIR"
rsync -a --delete skills/bug-check/ "$AGENT_SKILLS_DIR/bug-check/"
```

Set `AGENT_SKILLS_DIR` to the skills directory used by your agent runtime.

Restart or open a new agent session after installation if the skill list was already loaded.

## Use

Explicit invocation:

```text
Use $bug-check to debug this frontend bug and verify the relevant edge cases.
```

Recommended agent instruction:

```markdown
When fixing, debugging, reviewing, or validating a frontend/product bug, use `$bug-check` before editing code or claiming completion.
```

Expected final bug-fix report:

```text
Root cause:
Changes:
Original path verification:
Boundary cases verified:
Tests/lint/build/UI checks run:
Remaining risks:
```

## Validate

```bash
python3 scripts/validate-project.py
python3 skills/bug-check/scripts/check-bug-report.py path/to/final-report.md
```

Optional SKILL.md validator, when available:

```bash
python3 path/to/quick_validate.py skills/bug-check
```

GitHub Actions note: this repository intentionally does not include `.github/workflows` by default. Add CI after the publishing token has GitHub `workflow` scope.

## Publish

```bash
git init
git add .
git commit -m "Initial bug-check skill"
git branch -M main
git remote add origin git@github.com:<owner>/bug-check.git
git push -u origin main
```

Before publishing, decide the license and add a `LICENSE` file if this will be public.
