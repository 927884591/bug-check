# bug-check

`bug-check` is a diff-driven completion proof gate for AI coding agents. It packages changed files, bug descriptions, diff context, nearby tests, and verification candidates so the agent can prove a bug fix from explicit behavior claims, minimal counterexamples, and executed evidence before claiming completion.

It is designed to reduce AI-introduced regressions by turning bug work into this loop:

```text
Changed files + bug description + project shape
  -> completion proof pack
  -> behavior claims
  -> smallest counterexamples
  -> code and runtime/test evidence
  -> pass, continue fixing, or report risk
```

It does not guarantee all bugs disappear, does not replace your test framework, does not run hooks by default, and does not modify project AGENTS.md by default.

## Architecture

```text
.
├── AGENTS.md
├── README.md
├── scripts/
│   ├── check-completion-proof.py
│   ├── install-local.sh
│   ├── validate-install.py
│   └── validate-project.py
├── tests/fixtures/
└── skills/
    └── bug-check/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        │   ├── bug-check.md
        │   └── completion-proof.md
        └── scripts/
            ├── build-bug-context.py
            └── check-completion-proof.py
```

- `skills/bug-check/SKILL.md`: concise proof workflow and resource routing.
- `skills/bug-check/references/completion-proof.md`: optional formal proof report contract for audits and checker validation.
- `skills/bug-check/scripts/build-bug-context.py`: builds changed-scope, diff, nearby-test, verification-candidate, and proof-instruction packs.
- `skills/bug-check/scripts/check-completion-proof.py`: rejects formal reports missing claims, counterexamples, or evidence.
- `scripts/install-local.sh`: installs the skill into `$AGENT_SKILLS_DIR/bug-check`.
- `scripts/validate-install.py`: checks installed skill copies against the repository source.
- `scripts/validate-project.py`: validates structure, proof-pack behavior, checker behavior, and public positioning.

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
Use $bug-check as a completion proof gate before final response.
```

Recommended opt-in project instruction:

```markdown
After making code changes for a bug fix or risky behavior change, use `$bug-check`.
Use the current diff, changed files, and bug description to state behavior claims.
For each material claim, name the smallest counterexample that would disprove it.
Inspect whether the changed code handles each counterexample.
Run the narrowest useful verification for the original path and material counterexamples.
If evidence is missing for a material claim, continue fixing or report the risk instead of claiming completion.
```

For review, audit, or checker requests, `$bug-check` should report proof gaps first and avoid patching until the user asks. For fix or implementation requests, it should patch material proof gaps before completion.

Default install only copies the skill. If a team wants a durable project policy, paste the snippet above into the project instruction file explicitly.

Do not generate a formal proof report by default. The normal result is the engineering action: gap fixed, claim verified, or remaining risk called out. A lint, typecheck, or build pass alone is not enough evidence for a behavior claim.

If there are no changed files, diff, or explicit paths, `$bug-check` should degrade instead of pretending to prove completion. It may list tentative claims and counterexamples from the bug text, but it must wait for changed code before marking a fix complete.

Context pack examples:

```bash
python3 skills/bug-check/scripts/build-bug-context.py --files src/pages/UserList.tsx src/api/users.ts --bug "filter reset leaves page empty"
python3 skills/bug-check/scripts/build-bug-context.py --staged --bug "worker retries duplicate notifications"
python3 skills/bug-check/scripts/build-bug-context.py --base main --bug "review PR diff for proof gaps"
python3 skills/bug-check/scripts/build-bug-context.py --diff-range main...HEAD --files src/pages --bug "route query state regressed"
python3 skills/bug-check/scripts/build-bug-context.py --bug "403 response shows success toast"
```

Strict final audit/checker mode, only when explicitly requested or used with `check-completion-proof.py`:

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

## Validate

```bash
python3 scripts/validate-project.py
python3 scripts/validate-install.py --target skills/bug-check
python3 skills/bug-check/scripts/build-bug-context.py --files src/pages/UserList.tsx src/api/users.ts --bug "filter reset leaves page empty"
python3 skills/bug-check/scripts/build-bug-context.py --diff-range HEAD..HEAD --bug "no-op diff source smoke"
python3 skills/bug-check/scripts/check-completion-proof.py tests/fixtures/valid-proof.md
python3 skills/bug-check/scripts/check-completion-proof.py tests/fixtures/invalid-proof.md
```

The invalid proof command should fail because it lacks concrete counterexamples and evidence beyond lint/build.

## Publish

```bash
git init
git add .
git commit -m "Build bug-check completion proof skill"
git branch -M main
git remote add origin git@github.com:<owner>/bug-check.git
git push -u origin main
```

Before publishing, decide the license and add a `LICENSE` file if this will be public.
