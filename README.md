# bug-check

`bug-check` is a changed-files driven bug boundary system for AI coding agents. It routes modified files and bug descriptions to relevant boundary cases, requires explicit handling status, and enforces verification before completion.

It is designed to reduce common AI-introduced boundary bugs by turning bug work into this loop:

```text
Changed files + bug description + project shape
  -> context pack
  -> matched boundary cards
  -> compare boundary knowledge with changed code
  -> fix missing handling
  -> targeted verification
```

It does not guarantee all bugs disappear, does not replace your test framework, does not run hooks by default, and does not modify project AGENTS.md by default.

## Architecture

```text
.
├── AGENTS.md
├── README.md
├── scripts/
│   ├── check-bug-report.py
│   ├── install-local.sh
│   └── validate-project.py
├── tests/fixtures/
└── skills/
    └── bug-check/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        │   ├── bug-check.md
        │   ├── routing.md
        │   ├── boundary-card-format.md
        │   ├── completion-contract.md
        │   └── boundaries/
        └── scripts/
            ├── build-bug-context.py
            └── check-bug-report.py
```

- `skills/bug-check/SKILL.md`: concise workflow and resource routing.
- `skills/bug-check/references/routing.md`: maps changed files and bug words to boundary cards.
- `skills/bug-check/references/boundaries/`: focused boundary cards for common frontend, backend, API, database, queue, auth, tenant, deployment, and security bug classes.
- `skills/bug-check/references/completion-contract.md`: optional formal report structure for audits and checker validation.
- `skills/bug-check/scripts/build-bug-context.py`: routes changed files and bug text to relevant boundary cards.
- `skills/bug-check/scripts/check-bug-report.py`: rejects final reports missing boundary evidence.
- `scripts/install-local.sh`: installs the skill into `$AGENT_SKILLS_DIR/bug-check`.
- `scripts/validate-project.py`: validates structure, routing behavior, fixtures, and report checking.

## Install

Codex local skills:

```bash
AGENT_SKILLS_DIR="$HOME/.codex/skills" ./scripts/install-local.sh
```

Shared agent skills:

```bash
AGENT_SKILLS_DIR="$HOME/.agents/skills" ./scripts/install-local.sh
```

Manual install:

```bash
mkdir -p "$AGENT_SKILLS_DIR"
rsync -a --delete skills/bug-check/ "$AGENT_SKILLS_DIR/bug-check/"
```

Restart or open a new agent session after installation if the skill list was already loaded.

## Use

Explicit invocation:

```text
Use $bug-check to check this changed scope against relevant bug boundaries and fix any missing handling.
```

Recommended opt-in project instruction:

```markdown
After making code changes for a bug fix or risky behavior change, use `$bug-check`.
Use the changed files and bug description to load only relevant boundary cards.
Compare those boundaries against the changed code.
Patch any missing relevant boundary handling before completion.
```

Default install only copies the skill. If a team wants a durable project policy, paste the snippet above into the project instruction file explicitly.

Do not generate the full completion report by default. The normal result is the engineering action: missing boundary fixed, no relevant gap found, or remaining risk called out.

Context pack examples:

```bash
python3 skills/bug-check/scripts/build-bug-context.py --files src/pages/UserList.tsx src/api/users.ts --bug "filter reset leaves page empty"
python3 skills/bug-check/scripts/build-bug-context.py --staged --bug "worker retries duplicate notifications"
python3 skills/bug-check/scripts/build-bug-context.py --bug "403 response shows success toast"
```

Strict final audit/report mode, only when explicitly requested or used with `check-bug-report.py`:

```text
Root cause:
Changed files:
Context pack source:
Matched boundary cases:
Boundary handling table:
Original path verification:
Boundary verification:
Checks run:
Remaining risks:
```

## Validate

```bash
python3 scripts/validate-project.py
python3 skills/bug-check/scripts/build-bug-context.py --files src/pages/UserList.tsx src/api/users.ts --bug "filter reset leaves page empty"
python3 skills/bug-check/scripts/check-bug-report.py tests/fixtures/valid-report.md
python3 skills/bug-check/scripts/check-bug-report.py tests/fixtures/invalid-report.md
```

The invalid report command should fail because it lacks the Boundary handling table.

## Publish

```bash
git init
git add .
git commit -m "Build bug-check boundary skill"
git branch -M main
git remote add origin git@github.com:<owner>/bug-check.git
git push -u origin main
```

Before publishing, decide the license and add a `LICENSE` file if this will be public.
