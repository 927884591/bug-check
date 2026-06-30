#!/usr/bin/env python3
"""Validate the bug-check skill package against its boundary-system contract."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "bug-check"
REFERENCES_DIR = SKILL_DIR / "references"
BOUNDARIES_DIR = REFERENCES_DIR / "boundaries"
FIXTURES_DIR = ROOT / "tests" / "fixtures"

SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCE_INDEX = REFERENCES_DIR / "bug-check.md"
ROUTING_MD = REFERENCES_DIR / "routing.md"
CARD_FORMAT_MD = REFERENCES_DIR / "boundary-card-format.md"
COMPLETION_CONTRACT_MD = REFERENCES_DIR / "completion-contract.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
README_MD = ROOT / "README.md"
CONTEXT_BUILDER = SKILL_DIR / "scripts" / "build-bug-context.py"
CHECKER = SKILL_DIR / "scripts" / "check-bug-report.py"

REQUIRED_FILES = [
    README_MD,
    ROOT / "AGENTS.md",
    ROOT / ".gitignore",
    ROOT / "scripts" / "install-local.sh",
    ROOT / "scripts" / "validate-project.py",
    ROOT / "scripts" / "check-bug-report.py",
    SKILL_MD,
    REFERENCE_INDEX,
    ROUTING_MD,
    CARD_FORMAT_MD,
    COMPLETION_CONTRACT_MD,
    OPENAI_YAML,
    CONTEXT_BUILDER,
    CHECKER,
]

EXPECTED_BOUNDARY_CARDS = {
    "ui-list-table",
    "form-validation",
    "state-cache-sync",
    "api-contract",
    "auth-permission",
    "tenant-isolation",
    "database-transaction",
    "async-job-queue",
    "deployment-config",
    "security-sensitive-data",
}

REQUIRED_CARD_HEADINGS = [
    "Applies When",
    "Inspect",
    "Handled When",
    "Missing Means",
    "Verify",
    "Test Ideas",
]

REQUIRED_SKILL_POINTERS = [
    "scripts/build-bug-context.py",
    "references/routing.md",
    "references/completion-contract.md",
    "fix any missing handling",
    "Do not turn this into a separate report-writing step",
]

REQUIRED_README_STRINGS = [
    "changed-files driven bug boundary system",
    "context pack",
    "boundary cards",
    "compare boundary knowledge with changed code",
    "fix missing handling",
    "normal result is the engineering action",
    "does not modify project AGENTS.md by default",
    "does not replace your test framework",
]

PUBLIC_FILES = [
    README_MD,
    SKILL_MD,
    REFERENCE_INDEX,
    ROUTING_MD,
    CARD_FORMAT_MD,
    COMPLETION_CONTRACT_MD,
    OPENAI_YAML,
    ROOT / "AGENTS.md",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_no_placeholders(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden = ["todo", "[todo", "replace with", "[placeholder", "placeholder text"]
    matches = [item for item in forbidden if item in lowered]
    if matches:
        fail(f"{rel(path)} contains placeholder text: {', '.join(matches)}")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail("SKILL.md is missing YAML frontmatter")

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            fail(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def run(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        cwd=ROOT,
    )


def validate_skill() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    if fields.get("name") != "bug-check":
        fail("SKILL.md frontmatter name must be bug-check")
    description = fields.get("description", "")
    if len(description) < 160:
        fail("SKILL.md description is too short to trigger reliably")
    for trigger in ["debugging", "reviewing", "APIs", "databases", "queues", "permissions", "security"]:
        if trigger not in description:
            fail(f"SKILL.md description is missing trigger term: {trigger}")
    for pointer in REQUIRED_SKILL_POINTERS:
        if pointer not in text:
            fail(f"SKILL.md is missing required pointer: {pointer}")
    if len(text.splitlines()) > 120:
        fail("SKILL.md is too long; keep workflow and routing only")


def validate_reference_index() -> None:
    text = REFERENCE_INDEX.read_text(encoding="utf-8")
    required = ["# Bug Check Index", "routing.md", "boundaries/", "completion-contract.md"]
    for item in required:
        if item not in text:
            fail(f"bug-check.md index is missing: {item}")


def validate_routing() -> None:
    text = ROUTING_MD.read_text(encoding="utf-8")
    required = [
        "## Inputs",
        "## Output Tags",
        "## Routes",
        "Signals:",
        "Boundary tags:",
        "Load files:",
        "Inspect first:",
        "Do not read yet:",
    ]
    for item in required:
        if item not in text:
            fail(f"routing.md is missing: {item}")
    for card in ["ui-list-table", "state-cache-sync", "api-contract", "async-job-queue"]:
        if card not in text:
            fail(f"routing.md does not route card: {card}")


def validate_boundary_cards() -> None:
    if not BOUNDARIES_DIR.exists():
        fail("references/boundaries directory is missing")

    card_paths = sorted(BOUNDARIES_DIR.glob("*.md"))
    card_names = {path.stem for path in card_paths}
    missing_cards = sorted(EXPECTED_BOUNDARY_CARDS - card_names)
    if missing_cards:
        fail(f"missing expected boundary cards: {', '.join(missing_cards)}")
    if len(card_paths) < 8:
        fail("references/boundaries must contain at least 8 cards")

    for path in card_paths:
        text = path.read_text(encoding="utf-8")
        if f"# {path.stem}" not in text:
            fail(f"{rel(path)} must start with '# {path.stem}'")
        for heading in REQUIRED_CARD_HEADINGS:
            if f"## {heading}" not in text:
                fail(f"{rel(path)} is missing heading: {heading}")
        for status in ["already handled", "missing -> fixed", "not applicable"]:
            if status not in text:
                fail(f"{rel(path)} must mention handling status: {status}")


def validate_completion_contract() -> None:
    text = COMPLETION_CONTRACT_MD.read_text(encoding="utf-8")
    required = [
        "Root cause:",
        "Changed files:",
        "Context pack source:",
        "Matched boundary cases:",
        "Boundary handling table:",
        "Original path verification:",
        "Boundary verification:",
        "Checks run:",
        "Remaining risks:",
        "| Boundary | Status | Evidence | Action |",
    ]
    for item in required:
        if item not in text:
            fail(f"completion-contract.md is missing: {item}")


def validate_context_builder() -> None:
    if not CONTEXT_BUILDER.exists():
        fail("build-bug-context.py is missing")
    if not (CONTEXT_BUILDER.stat().st_mode & 0o111):
        fail("build-bug-context.py must be executable")

    command = [
        sys.executable,
        str(CONTEXT_BUILDER),
        "--files",
        "src/pages/UserList.tsx",
        "src/api/users.ts",
        "--bug",
        "filter reset leaves page 3 empty after delete",
    ]
    result = run(command)
    if result.returncode != 0:
        fail(f"build-bug-context.py failed: {result.stdout}{result.stderr}")
    output = result.stdout
    required = [
        "Bug Context Pack",
        "Changed scope:",
        "Project signals:",
        "Matched boundary cards:",
        "- ui-list-table",
        "- state-cache-sync",
        "Read next:",
        "Inspect first:",
        "Do not read yet:",
        "Boundary handling table template:",
    ]
    for item in required:
        if item not in output:
            fail(f"build-bug-context.py output is missing: {item}")

    git_result = run([sys.executable, str(CONTEXT_BUILDER), "--bug", "manual queue retry timeout"])
    if git_result.returncode != 0:
        fail(f"build-bug-context.py failed in git discovery mode: {git_result.stdout}{git_result.stderr}")
    malformed_paths = ["GENTS.md", "EADME.md", "cripts/validate-project.py", "kills/bug-check/SKILL.md"]
    for malformed in malformed_paths:
        if f"- {malformed}" in git_result.stdout:
            fail(f"build-bug-context.py emitted malformed git status path: {malformed}")


def validate_fixtures() -> None:
    scenarios = {
        "list-pagination": {"ui-list-table", "state-cache-sync"},
        "api-contract": {"api-contract", "auth-permission"},
        "queue-worker": {"async-job-queue"},
    }
    for name, expected_tags in scenarios.items():
        scenario_dir = FIXTURES_DIR / name
        changed = scenario_dir / "changed-files.txt"
        bug = scenario_dir / "bug.txt"
        expected = scenario_dir / "expected-tags.txt"
        for path in [changed, bug, expected]:
            if not path.exists():
                fail(f"missing fixture file: {rel(path)}")
        expected_from_file = {line.strip() for line in expected.read_text(encoding="utf-8").splitlines() if line.strip()}
        if expected_from_file != expected_tags:
            fail(f"{rel(expected)} does not match validator expectation")

        files = [line.strip() for line in changed.read_text(encoding="utf-8").splitlines() if line.strip()]
        bug_text = bug.read_text(encoding="utf-8").strip()
        result = run([sys.executable, str(CONTEXT_BUILDER), "--files", *files, "--bug", bug_text])
        if result.returncode != 0:
            fail(f"context builder failed for fixture {name}: {result.stdout}{result.stderr}")
        actual_tags = extract_matched_cards(result.stdout)
        if actual_tags != expected_tags:
            fail(f"fixture {name} matched {sorted(actual_tags)} but expected {sorted(expected_tags)}")


def validate_checker() -> None:
    valid_report = FIXTURES_DIR / "valid-report.md"
    invalid_report = FIXTURES_DIR / "invalid-report.md"
    if not valid_report.exists():
        fail(f"missing fixture file: {rel(valid_report)}")
    if not invalid_report.exists():
        fail(f"missing fixture file: {rel(invalid_report)}")

    valid = run([sys.executable, str(CHECKER), str(valid_report)])
    if valid.returncode != 0:
        fail(f"completion checker rejected valid report: {valid.stdout}{valid.stderr}")

    invalid = run([sys.executable, str(CHECKER), str(invalid_report)])
    if invalid.returncode == 0:
        fail("completion checker accepted invalid report without boundary table")
    if "boundary handling table" not in (invalid.stdout + invalid.stderr).lower():
        fail("invalid report failure should mention boundary handling table")


def extract_matched_cards(output: str) -> set[str]:
    match = re.search(r"Matched boundary cards:\n(.*?)(?:\n\n|\Z)", output, re.DOTALL)
    if not match:
        fail("context builder output is missing parseable Matched boundary cards section")
    cards: set[str] = set()
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            cards.add(stripped[2:].strip())
    return cards


def validate_openai_yaml() -> None:
    text = OPENAI_YAML.read_text(encoding="utf-8")
    lowered = text.lower()
    if 'display_name: "Bug Check"' not in text:
        fail("agents/openai.yaml display_name mismatch")
    lowered = text.lower()
    for term in ["changed code", "bug boundaries"]:
        if term not in lowered:
            fail(f"agents/openai.yaml must reflect changed-code boundary positioning: {term}")
    if "default_prompt: \"Use $bug-check" not in text:
        fail("agents/openai.yaml default_prompt must mention $bug-check")
    if "Use -check" in text:
        fail("agents/openai.yaml contains shell-expanded broken skill name")


def validate_readme() -> None:
    text = README_MD.read_text(encoding="utf-8")
    required = [
        "# bug-check",
        "## Architecture",
        "## Install",
        "## Use",
        "## Validate",
        "## Publish",
        "skills/bug-check/SKILL.md",
        "scripts/build-bug-context.py",
        "scripts/check-bug-report.py",
        "scripts/install-local.sh",
    ]
    for item in required:
        if item not in text:
            fail(f"README.md is missing: {item}")
    for item in REQUIRED_README_STRINGS:
        if item not in text:
            fail(f"README.md is missing positioning text: {item}")


def validate_public_positioning() -> None:
    blocked_terms = ["codex-bugfix-boundaries", "bugfix-boundaries", "Bug-Fix Boundaries", "ZenTao", "禅道"]
    for path in PUBLIC_FILES:
        text = path.read_text(encoding="utf-8")
        for term in blocked_terms:
            if term in text:
                fail(f"{rel(path)} contains deprecated or non-public term: {term}")


def main() -> int:
    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"missing required file: {rel(path)}")

    text_files = [path for path in PUBLIC_FILES if path.exists()]
    for path in text_files:
        assert_no_placeholders(path)

    validate_skill()
    validate_reference_index()
    validate_routing()
    validate_boundary_cards()
    validate_completion_contract()
    validate_context_builder()
    validate_fixtures()
    validate_checker()
    validate_openai_yaml()
    validate_readme()
    validate_public_positioning()

    print("PASS: bug-check boundary system structure, routing, scripts, fixtures, and report checks are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
