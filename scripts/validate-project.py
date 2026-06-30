#!/usr/bin/env python3
"""Validate the repository and installable AI-agent skill without third-party dependencies."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "bug-check"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCE_MD = SKILL_DIR / "references" / "bug-check.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
README_MD = ROOT / "README.md"
CHECKER = SKILL_DIR / "scripts" / "check-bug-report.py"

REQUIRED_FILES = [
    README_MD,
    ROOT / "AGENTS.md",
    ROOT / ".gitignore",
    ROOT / "scripts" / "install-local.sh",
    ROOT / "scripts" / "validate-project.py",
    ROOT / "scripts" / "check-bug-report.py",
    SKILL_MD,
    REFERENCE_MD,
    OPENAI_YAML,
    CHECKER,
]

REQUIRED_REFERENCE_HEADINGS = [
    "State Sync After Mutations",
    "Search, Filter, Reset, Pagination",
    "Data Consistency, Statistics, Units",
    "Forms, Validation, Save",
    "Async Tasks, Files, Logs, Deployment",
    "Empty, Error, Last-Item States",
    "Permission, Session, Password",
    "Date, Time Zone, Date Range",
    "Concurrency, Duplicate Actions, Stale Responses",
    "Routes, Browser History, Deep Links",
    "Input Method, Pasted Text, Special Characters",
    "Browser Cache, Local Storage, Version Upgrades",
    "Tenant, Project, Site, Organization Isolation",
    "Accessibility and Keyboard Operation",
    "Performance and Large Data Volume",
    "Video, Device, Alarm, Map, Realtime",
    "UI Layout, Long Text, Responsive",
    "API Parameters and Third-Party Integration",
    "Frontend Security and Sensitive Data",
    "Completion Contract",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def assert_no_placeholders(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden = ["todo", "[todo", "replace with", "[placeholder", "placeholder text"]
    matches = [item for item in forbidden if item in lowered]
    if matches:
        fail(f"{path.relative_to(ROOT)} contains placeholder text: {', '.join(matches)}")


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


def validate_skill() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    if fields.get("name") != "bug-check":
        fail("SKILL.md frontmatter name must be bug-check")
    description = fields.get("description", "")
    if len(description) < 180:
        fail("SKILL.md description is too short to trigger reliably")
    for trigger in ["debugging", "reviewing", "frontend", "pagination", "permissions", "security"]:
        if trigger not in description:
            fail(f"SKILL.md description is missing trigger term: {trigger}")
    if "references/bug-check.md" not in text:
        fail("SKILL.md must route detailed rules to references/bug-check.md")


def validate_reference() -> None:
    text = REFERENCE_MD.read_text(encoding="utf-8")
    for heading in REQUIRED_REFERENCE_HEADINGS:
        if f"## {heading}" not in text and f"### {heading}" not in text:
            fail(f"reference is missing heading: {heading}")
    blocked_terms = ["ZenTao", "禅道", "757", "141 reactivated", "26 bugs"]
    for term in blocked_terms:
        if term in text:
            fail(f"reference contains non-public source wording: {term}")


def validate_public_positioning() -> None:
    public_files = [README_MD, SKILL_MD, REFERENCE_MD, OPENAI_YAML, ROOT / "AGENTS.md"]
    blocked_terms = ["codex-bugfix-boundaries", "bugfix-boundaries", "Bug-Fix Boundaries", "Codex Skill", "ZenTao", "禅道"]
    for path in public_files:
        text = path.read_text(encoding="utf-8")
        for term in blocked_terms:
            if term in text:
                fail(f"{path.relative_to(ROOT)} contains deprecated positioning term: {term}")


def validate_openai_yaml() -> None:
    text = OPENAI_YAML.read_text(encoding="utf-8")
    if "display_name: \"Bug Check\"" not in text:
        fail("agents/openai.yaml display_name mismatch")
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
        "scripts/install-local.sh",
    ]
    for item in required:
        if item not in text:
            fail(f"README.md is missing: {item}")


def validate_checker() -> None:
    valid_report = """Root cause: stale query cache.
Changes: updated mutation invalidation.
Original path verification: reproduced and verified create/edit list refresh.
Boundary cases: checked pagination and empty state.
Tests/lint/build/UI checks run: npm test and UI screenshot.
Remaining risks: export flow not verified.
"""
    invalid_report = "Fixed the issue."

    valid = subprocess.run([sys.executable, str(CHECKER)], input=valid_report, text=True, capture_output=True)
    if valid.returncode != 0:
        fail(f"completion checker rejected valid report: {valid.stdout}{valid.stderr}")

    invalid = subprocess.run([sys.executable, str(CHECKER)], input=invalid_report, text=True, capture_output=True)
    if invalid.returncode == 0:
        fail("completion checker accepted invalid report")


def main() -> int:
    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"missing required file: {path.relative_to(ROOT)}")

    for path in [README_MD, ROOT / "AGENTS.md", SKILL_MD, REFERENCE_MD, OPENAI_YAML]:
        assert_no_placeholders(path)

    validate_skill()
    validate_reference()
    validate_public_positioning()
    validate_openai_yaml()
    validate_readme()
    validate_checker()

    print("PASS: project structure, skill metadata, references, and scripts are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
