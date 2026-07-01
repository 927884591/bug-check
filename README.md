# bug-check

`bug-check` is a changed-files driven bug boundary system for AI coding agents. It packages modified files, bug descriptions, diff context, nearby tests, and a boundary-card index so the AI can select relevant boundary cases, record explicit handling status, and verify before completion.

It is designed to reduce common AI-introduced boundary bugs by turning bug work into this loop:

```text
Changed files + bug description + project shape
  -> context pack
  -> AI-selected boundary cards
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
│   ├── review-boundary-candidates.py
│   ├── validate-install.py
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
            ├── check-bug-report.py
            └── review-boundary-candidates.py
```

- `skills/bug-check/SKILL.md`: concise workflow and resource routing.
- `skills/bug-check/references/routing.md`: guides AI selection of boundary cards from context evidence.
- `skills/bug-check/references/boundaries/`: focused boundary cards for common frontend UI, responsive accessibility, navigation/URL state, performance/resource lifecycle, async state, realtime streams, backend, API, database, queue, file transfer, i18n/timezone, auth, tenant, deployment, and security bug classes.
- `skills/bug-check/references/completion-contract.md`: optional formal report structure for audits and checker validation.
- `skills/bug-check/scripts/build-bug-context.py`: builds changed-scope, diff, nearby-test, and boundary-card-index context packs.
- `skills/bug-check/scripts/check-bug-report.py`: rejects final reports missing boundary evidence.
- `skills/bug-check/scripts/review-boundary-candidates.py`: records and reviews project-local manual boundary candidates without loading them in normal checks.
- `scripts/install-local.sh`: installs the skill into `$AGENT_SKILLS_DIR/bug-check`.
- `scripts/validate-install.py`: checks installed skill copies against the repository source.
- `scripts/validate-project.py`: validates structure, routing behavior, fixtures, and report checking.

## Install

GitHub distribution:

```bash
npx skills add hruilabs/bug-check --skill bug-check -g -a codex -y
```

This installs the published GitHub copy through the Agent Skills CLI. Maintainers should commit and push changes to `https://github.com/hruilabs/bug-check.git` first, then verify the remote install path with:

```bash
npx skills add hruilabs/bug-check --skill bug-check -g -a codex -y
```

The command uses `npx` to run the installer CLI; this repository does not need to be published as an npm package for GitHub-based skill distribution.

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
Use the context pack and card index as evidence; the AI selects cards, not the script.
Compare those boundaries against the changed code.
Patch any missing relevant boundary handling before completion.
```

For review, audit, or checker requests, `$bug-check` should report boundary gaps first and avoid patching until the user asks. For fix or implementation requests, it should patch missing relevant handling before completion.

Default install only copies the skill. If a team wants a durable project policy, paste the snippet above into the project instruction file explicitly.

Do not generate the full completion report by default. The normal result is the engineering action: missing boundary fixed, no relevant gap found, or remaining risk called out. The context builder does not prove matches; it gives the AI enough evidence to choose cards.

If there are no changed files, diff, or explicit paths, `$bug-check` should degrade instead of pretending to complete a boundary check. It may list tentative boundary hypotheses from the bug text, but it must wait for changed code before marking any card as covered, missing, fixed, or not applicable.

Context pack examples:

```bash
python3 skills/bug-check/scripts/build-bug-context.py --files src/pages/UserList.tsx src/api/users.ts --bug "filter reset leaves page empty"
python3 skills/bug-check/scripts/build-bug-context.py --staged --bug "worker retries duplicate notifications"
python3 skills/bug-check/scripts/build-bug-context.py --base main --bug "review PR diff for missed boundaries"
python3 skills/bug-check/scripts/build-bug-context.py --diff-range main...HEAD --files src/pages --bug "route query state regressed"
python3 skills/bug-check/scripts/build-bug-context.py --bug "403 response shows success toast"
```

The context builder may print `Suggested candidate cards (not final matches)` and `Verification candidates (not executed)`. These are routing aids only: the AI still chooses final boundary cards from code-path evidence, and it must apply each card's `Do Not Select When` rules before loading or using that card.

The added high-frequency cards are `navigation-url-state` for URL/history/deep-link failures and `performance-resource-lifecycle` for repeated work, leaks, cleanup, and runtime performance failures.

Manual boundary candidate flow:

```bash
python3 skills/bug-check/scripts/review-boundary-candidates.py record \
  --family ui-list-table \
  --failed-invariant "active page remains valid after result set changes" \
  --trigger filter,pagination \
  --changed-path-shape "src/pages/*List.tsx" \
  --missing-handling "page index was not reset or clamped after the result set changed" \
  --verification "page 3 -> filter/delete -> valid page or correct empty state" \
  --suggested-action merge-into-existing-card

python3 skills/bug-check/scripts/review-boundary-candidates.py review
python3 skills/bug-check/scripts/review-boundary-candidates.py plan
```

The candidate store defaults to `.bug-check/manual-boundaries.jsonl` in the project where the script runs. Normal `$bug-check` routing does not load this file; it is only for maintenance review. Promote a candidate only when high risk justifies it, the same failed invariant repeats, and an existing boundary card cannot cover it with a small update.

Install validation:

```bash
python3 scripts/validate-install.py
python3 scripts/validate-install.py --target "$HOME/.codex/skills/bug-check" --json
```

Missing install targets are warnings, stale existing targets fail, and at least one current target is required for success.

Strict final audit/report mode, only when explicitly requested or used with `check-bug-report.py`:

```text
Root cause:
Changed files:
Context pack source:
Matched boundary cases: (AI-selected from the context pack, not script-matched)
Boundary handling table:
Original path verification:
Boundary verification:
Checks run:
Remaining risks:
```

## Validate

```bash
python3 scripts/validate-project.py
python3 scripts/validate-install.py --target skills/bug-check
python3 skills/bug-check/scripts/build-bug-context.py --files src/pages/UserList.tsx src/api/users.ts --bug "filter reset leaves page empty"
python3 skills/bug-check/scripts/build-bug-context.py --diff-range HEAD..HEAD --bug "no-op diff source smoke"
python3 skills/bug-check/scripts/review-boundary-candidates.py plan --store tests/fixtures/manual-boundaries.jsonl
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
