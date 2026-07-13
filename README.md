# bug-check

`bug-check` is a two-stage behavior-safety skill for AI coding agents. Before coding, it separates specified behavior and existing contracts from AI inference and unresolved product decisions. After coding, it packages validated changed scope, diff context, nearby tests, and verification candidates so the agent can falsify observable claims and require executed evidence before completion.

It is designed to reduce both requirement-guessing errors and AI-introduced regressions through this loop:

```text
Requirement + existing contracts
  -> sourced acceptance claims
  -> unresolved product decisions
  -> impact scope + changed files
  -> smallest counterexamples
  -> executed runtime/test evidence
  -> product decision, investigate, fix, runtime evidence, or verified
```

It does not invent product policy, guarantee all bugs disappear, replace your test framework, independently prove that a written report is truthful, run hooks by default, or modify project AGENTS.md by default.

## Architecture

```text
.
├── AGENTS.md
├── README.md
├── scripts/
│   ├── check-completion-proof.py
│   ├── install-local.sh
│   ├── evaluate-benchmark.py
│   ├── validate-install.py
│   └── validate-project.py
├── tests/
│   ├── benchmark/
│   └── fixtures/
└── skills/
    └── bug-check/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        │   ├── behavior-contract.md
        │   ├── bug-check.md
        │   └── completion-proof.md
        └── scripts/
            ├── build-bug-context.py
            └── check-completion-proof.py
```

- `skills/bug-check/SKILL.md`: concise proof workflow and resource routing.
- `skills/bug-check/references/behavior-contract.md`: pre-change source and product-decision contract.
- `skills/bug-check/references/completion-proof.md`: optional formal proof report contract for audits and checker validation.
- `skills/bug-check/scripts/build-bug-context.py`: builds validated changed-scope, diff, nearby-test, verification-candidate, and proof-instruction packs.
- `skills/bug-check/scripts/check-completion-proof.py`: lints claim/counterexample/evidence linkage and obvious proof gaps without pretending to verify truth.
- `tests/benchmark/`: anonymized replay cases for requirement, state, interaction, and runtime failure classes.
- `scripts/evaluate-benchmark.py`: validates the replay corpus and scores structured predictions without claiming semantic evaluation.
- `scripts/install-local.sh`: installs the skill into `$AGENT_SKILLS_DIR/bug-check`.
- `scripts/validate-install.py`: checks installed skill copies against the repository source and succeeds only when every requested target is current.
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
Use $bug-check before and after this behavior-changing implementation.
```

Recommended opt-in project instruction:

```markdown
Use `$bug-check` for every behavior-changing implementation, bug fix, review, or validation.
Before editing, classify each material behavior as specified, existing-contract, inferred, or product-decision-required.
Do not silently implement product-decision-required behavior; ask when it blocks correctness or report it out of scope.
State observable acceptance claims and inspect affected callers, consumers, state, contracts, and tests.
After editing, map each material claim to the current diff and changed scope.
For each material claim, name the smallest counterexample that would disprove it.
Inspect whether the changed code handles each counterexample.
Run the narrowest useful verification for the original path and material counterexamples.
If evidence is missing for a material claim, continue fixing or report the risk instead of claiming completion.
```

For review, audit, or checker requests, `$bug-check` reports decision and proof gaps first and avoids patching until the user asks. For fix or implementation requests, it patches material proof gaps before completion.

Use one decision label consistently: `product-decision-required`, `continue-investigating`, `continue-fixing`, `runtime-evidence-required`, or `verified`.

Default install only copies the skill. If a team wants a durable project policy, paste the snippet above into the project instruction file explicitly.

Do not generate a formal proof report by default. The normal result is the engineering action: product decision requested, gap fixed, claim verified, or remaining risk called out. A lint, typecheck, or build pass alone is not enough evidence for a behavior claim.

If there are no valid changed files, diff, or explicit paths, `$bug-check` degrades instead of pretending to prove completion. Requirement text may establish tentative claims, but completion still waits for changed code and executed verification.

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
Decision: verified
Change rationale: accepted behavior contract for this feature, or use Root cause for a bug fix
Changed files:
- path/to/changed-file
Context source: validated context pack or explicit manual diff
Behavior claims:
- C1 [source: specified]: [source-ref: user request "changing a filter starts from page 1"] observable behavior
Counterexamples considered:
- C1: smallest concrete disproof case
Evidence:
- C1: PASS — the regression test exercised the counterexample and observed the claimed behavior
Checks run:
- PASS: command or manual runtime check -> exit 0 or equivalent successful result
Remaining risks: no unverified material cases remain after the listed evidence
```

The checker rejects a missing/non-`verified` completion decision, a no-change report, mismatched or missing source provenance, broken claim linkage, empty sections, obvious generic counterexamples/evidence, negative or failing outer checks, and checks without observed positive results. Expected nested rejection behavior such as an asserted subprocess exit 2 can still be valid when the outer regression test passes. The other four workflow decisions remain valid engineering exits, but they cannot pass as completion proofs. The checker remains a heuristic report linter: actual completion depends on running and inspecting the listed checks.

## Replay benchmark

`tests/benchmark/cases.json` contains anonymized replay cases spanning requirement ambiguity, stale state, first-interaction timing, product rules, realtime integration, canvas transforms, and empty data. Validate the corpus with:

```bash
python3 scripts/evaluate-benchmark.py --validate-only
```

Export blind inputs with `python3 scripts/evaluate-benchmark.py --export-prompts prompts.json`; the gold-free export includes one shared classification instruction, the allowed `stage`, `decision`, and `source` labels, the prediction output contract, and prompts containing only an opaque `case_id` plus `scenario`. To compare workflows, copy only the exported prompt file into two isolated, clean sessions that cannot read this repository, `cases.json`, gold labels, scoring output, or each other's predictions. Use the same model and settings, enabling `$bug-check` in only one session. Produce both prediction files before scoring either run with `--predictions`; otherwise the comparison is not blind. The evaluator reports exact stored-label agreement only; it does not judge explanation quality, evidence truth, or semantic correctness.

## Validate

```bash
python3 scripts/validate-project.py
python3 scripts/validate-install.py --target skills/bug-check
python3 scripts/evaluate-benchmark.py --validate-only
python3 skills/bug-check/scripts/build-bug-context.py --files skills/bug-check/SKILL.md skills/bug-check/references/behavior-contract.md --bug "behavior contract changed"
python3 skills/bug-check/scripts/build-bug-context.py --diff-range HEAD..HEAD --bug "no-op diff source smoke"
python3 skills/bug-check/scripts/check-completion-proof.py tests/fixtures/valid-proof.md
python3 skills/bug-check/scripts/check-completion-proof.py tests/fixtures/invalid-proof.md
```

The invalid proof command should fail because it has vague claims, no concrete claim-linked counterexample, negative evidence, no executed check, and no explained remaining-risk assessment.

## Publish

```bash
git init
git add .
git commit -m "Build two-stage bug-check skill"
git branch -M main
git remote add origin git@github.com:<owner>/bug-check.git
git push -u origin main
```

Before publishing, decide the license and add a `LICENSE` file if this will be public.
