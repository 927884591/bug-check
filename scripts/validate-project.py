#!/usr/bin/env python3
"""Validate the bug-check skill package against its completion-proof contract."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "bug-check"
REFERENCES_DIR = SKILL_DIR / "references"
FIXTURES_DIR = ROOT / "tests" / "fixtures"

SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCE_INDEX = REFERENCES_DIR / "bug-check.md"
COMPLETION_PROOF_MD = REFERENCES_DIR / "completion-proof.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
README_MD = ROOT / "README.md"
CONTEXT_BUILDER = SKILL_DIR / "scripts" / "build-bug-context.py"
PROOF_CHECKER = SKILL_DIR / "scripts" / "check-completion-proof.py"
PROOF_CHECKER_WRAPPER = ROOT / "scripts" / "check-completion-proof.py"
INSTALL_VALIDATOR = ROOT / "scripts" / "validate-install.py"

REQUIRED_FILES = [
    README_MD,
    ROOT / "AGENTS.md",
    ROOT / ".gitignore",
    ROOT / "scripts" / "install-local.sh",
    ROOT / "scripts" / "validate-project.py",
    PROOF_CHECKER_WRAPPER,
    INSTALL_VALIDATOR,
    SKILL_MD,
    REFERENCE_INDEX,
    COMPLETION_PROOF_MD,
    OPENAI_YAML,
    CONTEXT_BUILDER,
    PROOF_CHECKER,
]

REMOVED_PATHS = [
    REFERENCES_DIR / "routing.md",
    REFERENCES_DIR / "boundary-card-format.md",
    REFERENCES_DIR / "completion-contract.md",
    REFERENCES_DIR / "boundaries",
    SKILL_DIR / "scripts" / "check-bug-report.py",
    SKILL_DIR / "scripts" / "review-boundary-candidates.py",
    ROOT / "scripts" / "check-bug-report.py",
    ROOT / "scripts" / "review-boundary-candidates.py",
    FIXTURES_DIR / "manual-boundaries.jsonl",
]

PUBLIC_FILES = [
    README_MD,
    SKILL_MD,
    REFERENCE_INDEX,
    COMPLETION_PROOF_MD,
    OPENAI_YAML,
    ROOT / "AGENTS.md",
]

REQUIRED_SKILL_POINTERS = [
    "completion proof gate",
    "behavior claim",
    "smallest counterexample",
    "code/evidence",
    "scripts/build-bug-context.py",
    "references/completion-proof.md",
    "scripts/check-completion-proof.py",
]

REQUIRED_README_STRINGS = [
    "diff-driven completion proof gate",
    "behavior claims",
    "smallest counterexamples",
    "executed evidence",
    "completion proof pack",
    "check-completion-proof.py",
    "--base",
    "--diff-range",
    "lint, typecheck, or build pass alone is not enough",
]

OLD_ARCHITECTURE_TERMS = [
    "boundary-card",
    "boundary card",
    "Boundary Handling Table",
    "matched boundary cases",
    "Matched boundary cases",
    "review-boundary-candidates",
    "manual boundary",
    "candidate cards",
    "Available boundary card index",
    "Suggested candidate cards",
    "references/boundaries",
    ".bug-check/boundaries",
    "routing.md",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def run(
    command: list[str],
    *,
    input_text: str | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        cwd=cwd or ROOT,
    )


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


def validate_removed_architecture() -> None:
    for path in REMOVED_PATHS:
        if path.exists():
            fail(f"removed architecture path still exists: {rel(path)}")


def validate_skill() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    if fields.get("name") != "bug-check":
        fail("SKILL.md frontmatter name must be bug-check")
    description = fields.get("description", "")
    for term in ["completion proof", "diff", "behavior claims", "counterexamples", "evidence"]:
        if term not in description:
            fail(f"SKILL.md description is missing trigger term: {term}")
    for pointer in REQUIRED_SKILL_POINTERS:
        if pointer not in text:
            fail(f"SKILL.md is missing required pointer: {pointer}")
    if len(text.splitlines()) > 100:
        fail("SKILL.md is too long; keep workflow and routing only")


def validate_reference_index() -> None:
    text = REFERENCE_INDEX.read_text(encoding="utf-8")
    for item in ["# Bug Check Index", "completion-proof.md", "build-bug-context.py", "check-completion-proof.py"]:
        if item not in text:
            fail(f"bug-check.md index is missing: {item}")


def validate_completion_proof_reference() -> None:
    text = COMPLETION_PROOF_MD.read_text(encoding="utf-8")
    required = [
        "Root cause:",
        "Changed files:",
        "Context source:",
        "Behavior claims:",
        "Counterexamples considered:",
        "Evidence:",
        "Checks run:",
        "Remaining risks:",
        "A lint, typecheck, or build pass alone is not completion evidence",
    ]
    for item in required:
        if item not in text:
            fail(f"completion-proof.md is missing: {item}")


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
        "Completion Proof Pack",
        "Changed scope:",
        "Project signals:",
        "Diff context:",
        "Read next:",
        "Verification candidates (not executed):",
        "Proof instructions:",
        "State each material behavior claim",
        "smallest concrete counterexample",
    ]
    for item in required:
        if item not in output:
            fail(f"build-bug-context.py output is missing: {item}")
    for old in [
        "Available boundary card index:",
        "Suggested candidate cards",
        "Card selection guidance:",
        "Diff signal words:",
        "Boundary handling table",
    ]:
        if old in output:
            fail(f"build-bug-context.py output still contains old architecture text: {old}")

    no_scope_result = run([sys.executable, str(CONTEXT_BUILDER), "--files", "--bug", "button stays disabled"])
    if no_scope_result.returncode != 0:
        fail(f"build-bug-context.py failed in no-scope mode: {no_scope_result.stdout}{no_scope_result.stderr}")
    no_scope_output = no_scope_result.stdout
    for item in [
        "No changed scope fallback:",
        "not a completion proof",
        "Bug text may suggest tentative claims and counterexamples",
        "Do not mark the fix complete",
    ]:
        if item not in no_scope_output:
            fail(f"build-bug-context.py no-scope output is missing: {item}")

    git_result = run([sys.executable, str(CONTEXT_BUILDER), "--bug", "manual retry timeout"])
    if git_result.returncode != 0:
        fail(f"build-bug-context.py failed in git discovery mode: {git_result.stdout}{git_result.stderr}")
    malformed_paths = ["GENTS.md", "EADME.md", "cripts/validate-project.py", "kills/bug-check/SKILL.md"]
    for malformed in malformed_paths:
        if f"- {malformed}" in git_result.stdout:
            fail(f"build-bug-context.py emitted malformed git status path: {malformed}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        run(["git", "init"], cwd=tmp)
        for tool_path in [
            tmp / ".codegraph" / "codegraph.db",
            tmp / ".bug-check" / "state.json",
            tmp / ".codex" / "state.json",
            tmp / ".vscode" / "settings.json",
        ]:
            tool_path.parent.mkdir(parents=True, exist_ok=True)
            tool_path.write_text("tool metadata\n", encoding="utf-8")
        hygiene_result = run([sys.executable, str(CONTEXT_BUILDER), "--bug", "tool metadata only"], cwd=tmp)
        if hygiene_result.returncode != 0:
            fail(f"build-bug-context.py failed in scope hygiene temp repo: {hygiene_result.stdout}{hygiene_result.stderr}")
        if "- .codegraph/" in hygiene_result.stdout or "- .bug-check/" in hygiene_result.stdout:
            fail("build-bug-context.py should exclude tool metadata directories from changed scope")
        if "No changed scope fallback:" not in hygiene_result.stdout:
            fail("build-bug-context.py should fall back when only tool metadata directories changed")

    range_result = run([sys.executable, str(CONTEXT_BUILDER), "--diff-range", "HEAD..HEAD", "--bug", "no-op diff source smoke"])
    if range_result.returncode != 0:
        fail(f"build-bug-context.py failed with --diff-range: {range_result.stdout}{range_result.stderr}")
    if "Source: git diff HEAD..HEAD" not in range_result.stdout:
        fail("build-bug-context.py --diff-range output should name the diff source")

    conflict_result = run([sys.executable, str(CONTEXT_BUILDER), "--staged", "--base", "HEAD", "--bug", "conflict"])
    if conflict_result.returncode == 0:
        fail("build-bug-context.py accepted conflicting --staged and --base flags")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        run(["git", "init"], cwd=tmp)
        source = tmp / "src" / "pages"
        source.mkdir(parents=True)
        page = source / "UserList.tsx"
        page.write_text("export const page = 1;\n", encoding="utf-8")
        run(["git", "add", "."], cwd=tmp)
        run(["git", "-c", "user.email=a@example.com", "-c", "user.name=A", "commit", "-m", "init"], cwd=tmp)
        page.write_text("export const page = 2;\n", encoding="utf-8")
        run(["git", "add", "."], cwd=tmp)
        run(["git", "-c", "user.email=a@example.com", "-c", "user.name=A", "commit", "-m", "change page"], cwd=tmp)
        base_result = run([sys.executable, str(CONTEXT_BUILDER), "--base", "HEAD~1", "--bug", "page changed"], cwd=tmp)
        if base_result.returncode != 0:
            fail(f"build-bug-context.py failed with --base in temp repo: {base_result.stdout}{base_result.stderr}")
        if "src/pages/UserList.tsx" not in base_result.stdout or "Source: git diff HEAD~1...HEAD" not in base_result.stdout:
            fail("build-bug-context.py --base should discover changed files and name the merge-base diff source")
        diff_range_result = run([sys.executable, str(CONTEXT_BUILDER), "--diff-range", "HEAD~1..HEAD", "--bug", "page changed"], cwd=tmp)
        if diff_range_result.returncode != 0:
            fail(f"build-bug-context.py failed with temp --diff-range: {diff_range_result.stdout}{diff_range_result.stderr}")
        if "src/pages/UserList.tsx" not in diff_range_result.stdout:
            fail("build-bug-context.py --diff-range should discover changed files")


def validate_proof_checker() -> None:
    if not PROOF_CHECKER.exists():
        fail("check-completion-proof.py is missing")
    if not (PROOF_CHECKER.stat().st_mode & 0o111):
        fail("check-completion-proof.py must be executable")
    if not (PROOF_CHECKER_WRAPPER.stat().st_mode & 0o111):
        fail("scripts/check-completion-proof.py must be executable")

    valid_proof = FIXTURES_DIR / "valid-proof.md"
    invalid_proof = FIXTURES_DIR / "invalid-proof.md"
    for path in [valid_proof, invalid_proof]:
        if not path.exists():
            fail(f"missing fixture file: {rel(path)}")

    valid = run([sys.executable, str(PROOF_CHECKER), str(valid_proof)])
    if valid.returncode != 0:
        fail(f"completion proof checker rejected valid proof: {valid.stdout}{valid.stderr}")

    invalid = run([sys.executable, str(PROOF_CHECKER), str(invalid_proof)])
    if invalid.returncode == 0:
        fail("completion proof checker accepted invalid proof")
    invalid_text = (invalid.stdout + invalid.stderr).lower()
    for item in ["counterexamples", "evidence"]:
        if item not in invalid_text:
            fail(f"invalid proof failure should mention {item}")


def validate_install_validator() -> None:
    if not INSTALL_VALIDATOR.exists():
        fail("scripts/validate-install.py is missing")
    if not (INSTALL_VALIDATOR.stat().st_mode & 0o111):
        fail("scripts/validate-install.py must be executable")

    current = run([sys.executable, str(INSTALL_VALIDATOR), "--target", str(SKILL_DIR), "--json"])
    if current.returncode != 0:
        fail(f"validate-install.py rejected the source skill as a current target: {current.stdout}{current.stderr}")
    try:
        payload = json.loads(current.stdout)
    except json.JSONDecodeError as exc:
        fail(f"validate-install.py --json did not emit JSON: {exc}")
    if not payload.get("source_hash") or payload.get("targets", [{}])[0].get("status") != "current":
        fail("validate-install.py --json should include source_hash and current target status")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        stale = tmp / "bug-check-stale"
        shutil.copytree(SKILL_DIR, stale)
        (stale / "SKILL.md").write_text("# stale\n", encoding="utf-8")
        stale_result = run([sys.executable, str(INSTALL_VALIDATOR), "--target", str(stale)])
        if stale_result.returncode == 0 or "stale" not in (stale_result.stdout + stale_result.stderr):
            fail("validate-install.py should fail existing stale targets")

        missing = tmp / "missing-bug-check"
        missing_result = run([sys.executable, str(INSTALL_VALIDATOR), "--target", str(missing)])
        if missing_result.returncode == 0 or "missing" not in (missing_result.stdout + missing_result.stderr):
            fail("validate-install.py should fail when all targets are missing")


def validate_openai_yaml() -> None:
    text = OPENAI_YAML.read_text(encoding="utf-8")
    lowered = text.lower()
    if 'display_name: "Bug Check"' not in text:
        fail("agents/openai.yaml display_name mismatch")
    for term in ["completion proof", "counterexamples", "evidence"]:
        if term not in lowered:
            fail(f"agents/openai.yaml must reflect completion-proof positioning: {term}")
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
        "scripts/check-completion-proof.py",
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
        for term in blocked_terms + OLD_ARCHITECTURE_TERMS:
            if term in text:
                fail(f"{rel(path)} contains removed or non-public term: {term}")


def main() -> int:
    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"missing required file: {rel(path)}")
    validate_removed_architecture()

    for path in PUBLIC_FILES:
        assert_no_placeholders(path)

    validate_skill()
    validate_reference_index()
    validate_completion_proof_reference()
    validate_context_builder()
    validate_proof_checker()
    validate_install_validator()
    validate_openai_yaml()
    validate_readme()
    validate_public_positioning()

    print("PASS: bug-check completion proof structure, scripts, fixtures, and install checks are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
