#!/usr/bin/env python3
"""Validate the bug-check two-stage behavior contract, proof tooling, and replay baseline."""

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
BEHAVIOR_CONTRACT_MD = REFERENCES_DIR / "behavior-contract.md"
COMPLETION_PROOF_MD = REFERENCES_DIR / "completion-proof.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
README_MD = ROOT / "README.md"
CONTEXT_BUILDER = SKILL_DIR / "scripts" / "build-bug-context.py"
PROOF_CHECKER = SKILL_DIR / "scripts" / "check-completion-proof.py"
PROOF_CHECKER_WRAPPER = ROOT / "scripts" / "check-completion-proof.py"
INSTALL_VALIDATOR = ROOT / "scripts" / "validate-install.py"
BENCHMARK_CASES = ROOT / "tests" / "benchmark" / "cases.json"
BENCHMARK_EVALUATOR = ROOT / "scripts" / "evaluate-benchmark.py"

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
    BEHAVIOR_CONTRACT_MD,
    COMPLETION_PROOF_MD,
    OPENAI_YAML,
    CONTEXT_BUILDER,
    PROOF_CHECKER,
    BENCHMARK_CASES,
    BENCHMARK_EVALUATOR,
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
    BEHAVIOR_CONTRACT_MD,
    COMPLETION_PROOF_MD,
    OPENAI_YAML,
    ROOT / "AGENTS.md",
    BENCHMARK_CASES,
]

REQUIRED_SKILL_POINTERS = [
    "product-decision-required",
    "continue-investigating",
    "runtime-evidence-required",
    "acceptance claim",
    "smallest concrete counterexample",
    "executed evidence",
    "scripts/build-bug-context.py",
    "references/behavior-contract.md",
    "references/completion-proof.md",
    "scripts/check-completion-proof.py",
]

REQUIRED_README_STRINGS = [
    "two-stage behavior-safety skill",
    "product-decision-required",
    "smallest counterexample",
    "executed runtime/test evidence",
    "validated changed-scope",
    "check-completion-proof.py",
    "evaluate-benchmark.py",
    "--base",
    "--diff-range",
    "lint, typecheck, or build pass alone is not enough",
    "report linter",
    "--export-prompts",
    "`stage`, `decision`, and `source`",
    "gold-free export",
    "Decision: verified",
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
    if set(fields) != {"name", "description"}:
        fail("SKILL.md frontmatter must contain only name and description")
    if fields.get("name") != "bug-check":
        fail("SKILL.md frontmatter name must be bug-check")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", fields["name"]):
        fail("SKILL.md frontmatter name must be lowercase hyphen-case and at most 64 characters")
    description = fields.get("description", "")
    if len(description) > 1024 or "<" in description or ">" in description:
        fail("SKILL.md frontmatter description violates skill metadata constraints")
    for term in ["behavior-changing", "product decisions", "diff", "counterexamples", "executed evidence"]:
        if term not in description:
            fail(f"SKILL.md description is missing trigger term: {term}")
    for pointer in REQUIRED_SKILL_POINTERS:
        if pointer not in text:
            fail(f"SKILL.md is missing required pointer: {pointer}")
    if len(text.splitlines()) > 100:
        fail("SKILL.md is too long; keep workflow and routing only")


def validate_reference_index() -> None:
    text = REFERENCE_INDEX.read_text(encoding="utf-8")
    for item in ["# Bug Check Index", "behavior-contract.md", "completion-proof.md", "build-bug-context.py", "check-completion-proof.py"]:
        if item not in text:
            fail(f"bug-check.md index is missing: {item}")


def validate_behavior_contract_reference() -> None:
    text = BEHAVIOR_CONTRACT_MD.read_text(encoding="utf-8")
    required = [
        "# Behavior Contract",
        "specified",
        "existing-contract",
        "inferred",
        "product-decision-required",
        "ID: C1",
        "exact user wording",
        "Observable acceptance:",
        "Impact surface:",
        "Open decision:",
        "Do not convert `product-decision-required` into a passing acceptance claim",
    ]
    for item in required:
        if item not in text:
            fail(f"behavior-contract.md is missing: {item}")


def validate_completion_proof_reference() -> None:
    text = COMPLETION_PROOF_MD.read_text(encoding="utf-8")
    required = [
        "Decision: verified",
        "Root cause:",
        "Changed files:",
        "Context source:",
        "Behavior claims:",
        "Counterexamples considered:",
        "Evidence:",
        "Checks run:",
        "Remaining risks:",
        "stable IDs such as `C1`",
        "uses the same claim IDs",
        "[source-ref: ...]",
        "explicit post-change",
        "Change rationale:",
        "does not independently prove",
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
        "skills/bug-check/SKILL.md",
        "skills/bug-check/references/behavior-contract.md",
        "--bug",
        "behavior contract changed",
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
        "specified, existing-contract, or inferred",
        "product-decision-required",
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

    subdir_discovery = run(
        [sys.executable, "scripts/build-bug-context.py", "--bug", "subdirectory discovery"],
        cwd=SKILL_DIR,
    )
    if subdir_discovery.returncode != 0:
        fail(
            "build-bug-context.py failed from a repository subdirectory: "
            f"{subdir_discovery.stdout}{subdir_discovery.stderr}"
        )
    for expected_path in [
        "- scripts/check-completion-proof.py",
        "- skills/bug-check/scripts/check-completion-proof.py",
        "- skills/bug-check/references/behavior-contract.md",
    ]:
        if expected_path not in subdir_discovery.stdout:
            fail(f"build-bug-context.py subdirectory scope is missing repository-root path: {expected_path}")
    if "- references/behavior-contract.md" in subdir_discovery.stdout:
        fail("build-bug-context.py mixed invocation-relative and repository-relative Git paths")

    subdir_explicit = run(
        [
            sys.executable,
            "scripts/build-bug-context.py",
            "--files",
            "scripts/check-completion-proof.py",
            "--bug",
            "subdirectory explicit file",
        ],
        cwd=SKILL_DIR,
    )
    if (
        subdir_explicit.returncode != 0
        or "- skills/bug-check/scripts/check-completion-proof.py" not in subdir_explicit.stdout
        or "diff --git a/skills/bug-check/scripts/check-completion-proof.py" not in subdir_explicit.stdout
        or "diff --git a/scripts/check-completion-proof.py" in subdir_explicit.stdout
    ):
        fail("build-bug-context.py should resolve subdirectory --files relative to invocation cwd")

    for directory_path in [".", "skills/bug-check"]:
        directory_scope = run(
            [
                sys.executable,
                str(CONTEXT_BUILDER),
                "--files",
                directory_path,
                "--bug",
                "directory scope must fail",
            ]
        )
        if directory_scope.returncode == 0 or "not a directory" not in (
            directory_scope.stdout + directory_scope.stderr
        ):
            fail(f"build-bug-context.py should reject explicit directory scope {directory_path}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        run(["git", "init"], cwd=tmp)
        (tmp / "target-a.txt").write_text("a\n", encoding="utf-8")
        (tmp / "target-b.txt").write_text("b\n", encoding="utf-8")
        link = tmp / "link.txt"
        link.symlink_to("target-a.txt")
        run(["git", "add", "."], cwd=tmp)
        run(
            ["git", "-c", "user.email=a@example.com", "-c", "user.name=A", "commit", "-m", "symlink"],
            cwd=tmp,
        )
        link.unlink()
        link.symlink_to("target-b.txt")
        symlink_scope = run(
            [sys.executable, str(CONTEXT_BUILDER), "--files", "link.txt", "--bug", "symlink target changed"],
            cwd=tmp,
        )
        if (
            symlink_scope.returncode != 0
            or "- link.txt" not in symlink_scope.stdout
            or "diff --git a/link.txt b/link.txt" not in symlink_scope.stdout
            or "\n- target-b.txt\n" in symlink_scope.stdout
        ):
            fail("build-bug-context.py should preserve a literal tracked symlink path")

    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        repo = base / "repo"
        outside = base / "outside"
        repo.mkdir()
        outside.mkdir()
        (outside / "secret.py").write_text("SECRET = True\n", encoding="utf-8")
        run(["git", "init"], cwd=repo)
        (repo / "vendor").symlink_to(outside, target_is_directory=True)
        run(["git", "add", "."], cwd=repo)
        run(
            ["git", "-c", "user.email=a@example.com", "-c", "user.name=A", "commit", "-m", "vendor link"],
            cwd=repo,
        )
        parent_symlink = run(
            [
                sys.executable,
                str(CONTEXT_BUILDER),
                "--files",
                "vendor/secret.py",
                "--bug",
                "parent symlink must not escape",
            ],
            cwd=repo,
        )
        if parent_symlink.returncode == 0 or "parent symlink outside" not in (
            parent_symlink.stdout + parent_symlink.stderr
        ):
            fail("build-bug-context.py should reject explicit paths through an external parent symlink")

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
        if "Scope notices:" not in hygiene_result.stdout or "tool metadata/cache" not in hygiene_result.stdout:
            fail("build-bug-context.py should explain filtered tool metadata")

    range_result = run([sys.executable, str(CONTEXT_BUILDER), "--diff-range", "HEAD..HEAD", "--bug", "no-op diff source smoke"])
    if range_result.returncode != 0:
        fail(f"build-bug-context.py failed with --diff-range: {range_result.stdout}{range_result.stderr}")
    if "Source: git diff HEAD..HEAD" not in range_result.stdout:
        fail("build-bug-context.py --diff-range output should name the diff source")

    conflict_result = run([sys.executable, str(CONTEXT_BUILDER), "--staged", "--base", "HEAD", "--bug", "conflict"])
    if conflict_result.returncode == 0:
        fail("build-bug-context.py accepted conflicting --staged and --base flags")

    invalid_range = run(
        [
            sys.executable,
            str(CONTEXT_BUILDER),
            "--diff-range",
            "definitely-not-a-revision",
            "--bug",
            "invalid range must fail",
        ]
    )
    if invalid_range.returncode == 0 or "definitely-not-a-revision" not in (
        invalid_range.stdout + invalid_range.stderr
    ):
        fail("build-bug-context.py should fail and name an invalid --diff-range")

    invalid_base = run(
        [
            sys.executable,
            str(CONTEXT_BUILDER),
            "--base",
            "definitely-not-a-base",
            "--bug",
            "invalid base must fail",
        ]
    )
    if invalid_base.returncode == 0 or "definitely-not-a-base" not in (
        invalid_base.stdout + invalid_base.stderr
    ):
        fail("build-bug-context.py should fail and name an invalid --base")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        for option in ["--base", "--diff-range"]:
            output_path = tmp / f"{option[2:]}-side-effect"
            injected = run(
                [
                    sys.executable,
                    str(CONTEXT_BUILDER),
                    f"{option}=--output={output_path}",
                    "--bug",
                    "revision options must not execute",
                ]
            )
            if injected.returncode == 0 or output_path.exists():
                fail(f"build-bug-context.py should reject option-like {option} without side effects")

    missing_file = run(
        [
            sys.executable,
            str(CONTEXT_BUILDER),
            "--files",
            "src/does-not-exist.ts",
            "--bug",
            "explicit paths must exist",
        ]
    )
    if missing_file.returncode == 0 or "do not exist" not in (
        missing_file.stdout + missing_file.stderr
    ):
        fail("build-bug-context.py should reject nonexistent explicit --files paths")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        run(["git", "init"], cwd=tmp)
        for filename in ["a.py", "b.py"]:
            (tmp / filename).write_text("VALUE = 1\n", encoding="utf-8")
        run(["git", "add", "."], cwd=tmp)
        run(
            ["git", "-c", "user.email=a@example.com", "-c", "user.name=A", "commit", "-m", "init"],
            cwd=tmp,
        )
        for filename in ["a.py", "b.py"]:
            (tmp / filename).write_text("VALUE = 2\n", encoding="utf-8")
        wildcard = run(
            [sys.executable, str(CONTEXT_BUILDER), "--files", "*.py", "--bug", "literal explicit scope"],
            cwd=tmp,
        )
        if wildcard.returncode == 0 or "do not exist" not in (wildcard.stdout + wildcard.stderr):
            fail("build-bug-context.py should reject wildcard/pathspec syntax as a nonexistent literal path")
        if "a.py" in wildcard.stdout or "b.py" in wildcard.stdout:
            fail("build-bug-context.py wildcard input must not widen into matching files")

    empty_pathspec = run(
        [
            sys.executable,
            str(CONTEXT_BUILDER),
            "--base",
            "HEAD",
            "--files",
            "--bug",
            "empty pathspec must not expand to the whole diff",
        ]
    )
    if empty_pathspec.returncode == 0 or "requires at least one path" not in (
        empty_pathspec.stdout + empty_pathspec.stderr
    ):
        fail("build-bug-context.py should reject an empty --files diff pathspec")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        run(["git", "init"], cwd=tmp)
        staged_file = tmp / "src" / "new.py"
        staged_file.parent.mkdir(parents=True)
        staged_file.write_text("value = 1\n", encoding="utf-8")
        run(["git", "add", "."], cwd=tmp)
        staged_file.write_text("value = 2\n", encoding="utf-8")
        for staged_args, expected, forbidden in [
            ([], "+value = 2", "+value = 1"),
            (["--staged"], "+value = 1", "+value = 2"),
            (["--files", "src/new.py"], "+value = 2", "+value = 1"),
        ]:
            unborn = run(
                [sys.executable, str(CONTEXT_BUILDER), *staged_args, "--bug", "unborn staged addition"],
                cwd=tmp,
            )
            if (
                unborn.returncode != 0
                or "src/new.py" not in unborn.stdout
                or "HEAD is unborn" not in unborn.stdout
                or expected not in unborn.stdout
                or forbidden in unborn.stdout
            ):
                mode = " ".join(staged_args) if staged_args else "default"
                fail(f"build-bug-context.py unborn scope is stale or incomplete in {mode} mode")
        untracked_file = tmp / "src" / "untracked.py"
        untracked_file.write_text("value = 2\n", encoding="utf-8")
        explicit_untracked = run(
            [
                sys.executable,
                str(CONTEXT_BUILDER),
                "--files",
                "src/untracked.py",
                "--bug",
                "explicit untracked scope",
            ],
            cwd=tmp,
        )
        if explicit_untracked.returncode != 0 or "explicit untracked path(s)" not in explicit_untracked.stdout:
            fail("build-bug-context.py should disclose explicit untracked files without Git diff")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        run(["git", "init"], cwd=tmp)
        (tmp / "package-lock.json").write_text('{"lockfileVersion": 3}\n', encoding="utf-8")
        lockfile = run([sys.executable, str(CONTEXT_BUILDER), "--bug", "lockfile-only change"], cwd=tmp)
        if lockfile.returncode != 0:
            fail(f"build-bug-context.py failed on lockfile-only scope: {lockfile.stdout}{lockfile.stderr}")
        for item in ["Scope notices:", "lockfile", "package-lock.json", "No changed scope fallback:"]:
            if item not in lockfile.stdout:
                fail(f"build-bug-context.py lockfile-only output is missing: {item}")

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

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        run(["git", "init"], cwd=tmp)
        removed = tmp / "removed.py"
        removed.write_text("VALUE = 1\n", encoding="utf-8")
        run(["git", "add", "."], cwd=tmp)
        run(["git", "-c", "user.email=a@example.com", "-c", "user.name=A", "commit", "-m", "init"], cwd=tmp)
        removed.unlink()
        deleted = run(
            [sys.executable, str(CONTEXT_BUILDER), "--files", "removed.py", "--bug", "review deletion"],
            cwd=tmp,
        )
        if deleted.returncode != 0 or "deleted file mode" not in deleted.stdout or "removed.py" not in deleted.stdout:
            fail("build-bug-context.py should allow and show explicitly deleted tracked files")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        files = {
            "package.json": '{"scripts":{"test":"vitest","lint":"eslint .","typecheck":"tsc --noEmit"}}\n',
            "web/widget.ts": "export const widget = true;\n",
            "web/widget.test.ts": "test('widget', () => {});\n",
            "pyproject.toml": "[project]\nname='sample'\nversion='0.0.1'\n",
            "src/service.py": "VALUE = 1\n",
            "tests/test_service.py": "def test_service(): assert True\n",
            "go.mod": "module example.invalid/sample\n\ngo 1.22\n",
            "pkg/worker.go": "package pkg\n",
            "pkg/worker_test.go": "package pkg\n",
            "Cargo.toml": '[package]\nname="sample"\nversion="0.1.0"\n',
            "src/engine.rs": "pub fn run() {}\n",
            "tests/engine.rs": "#[test] fn run() {}\n",
            "Package.swift": "// swift-tools-version: 5.9\n",
            "Sources/Core/Thing.swift": "public struct Thing {}\n",
            "Tests/CoreTests/ThingTests.swift": "import XCTest\n",
            "build.gradle": "plugins { id 'java' }\n",
            "pom.xml": "<project></project>\n",
            "src/main/java/acme/Thing.java": "package acme; class Thing {}\n",
            "src/test/java/acme/ThingTest.java": "package acme; class ThingTest {}\n",
        }
        for relative, content in files.items():
            path = tmp / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        source_paths = [
            "web/widget.ts",
            "src/service.py",
            "pkg/worker.go",
            "src/engine.rs",
            "Sources/Core/Thing.swift",
            "src/main/java/acme/Thing.java",
        ]
        cross_stack = run(
            [sys.executable, str(CONTEXT_BUILDER), "--files", *source_paths, "--bug", "cross-stack discovery"],
            cwd=tmp,
        )
        if cross_stack.returncode != 0:
            fail(f"build-bug-context.py failed cross-stack discovery: {cross_stack.stdout}{cross_stack.stderr}")
        required_cross_stack = [
            "web/widget.test.ts",
            "tests/test_service.py",
            "pkg/worker_test.go",
            "tests/engine.rs",
            "Tests/CoreTests/ThingTests.swift",
            "src/test/java/acme/ThingTest.java",
            "npm test",
            "python3 -m pytest",
            "go test ./pkg",
            "cargo test",
            "swift test",
            "gradle test",
            "mvn test",
            "Read next truncation:",
        ]
        for item in required_cross_stack:
            if item not in cross_stack.stdout:
                fail(f"build-bug-context.py cross-stack output is missing: {item}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        run(["git", "init"], cwd=tmp)
        source = tmp / "src" / "large.ts"
        source.parent.mkdir(parents=True)
        old_lines = [f"old-{index}" for index in range(240)]
        old_lines[20] = "y" * 400
        source.write_text("\n".join(old_lines) + "\n", encoding="utf-8")
        run(["git", "add", "."], cwd=tmp)
        run(["git", "-c", "user.email=a@example.com", "-c", "user.name=A", "commit", "-m", "init"], cwd=tmp)
        changed_lines = [f"new-{index}" for index in range(240)]
        changed_lines[20] = "x" * 400
        source.write_text("\n".join(changed_lines) + "\n", encoding="utf-8")
        truncated = run(
            [sys.executable, str(CONTEXT_BUILDER), "--files", "src/large.ts", "--bug", "large diff"],
            cwd=tmp,
        )
        if truncated.returncode != 0:
            fail(f"build-bug-context.py failed large-diff smoke: {truncated.stdout}{truncated.stderr}")
        for item in ["Diff truncation:", "line(s) omitted", "long line(s) shortened", "character(s) omitted"]:
            if item not in truncated.stdout:
                fail(f"build-bug-context.py large-diff output is missing: {item}")


def validate_proof_checker() -> None:
    if not PROOF_CHECKER.exists():
        fail("check-completion-proof.py is missing")
    if not (PROOF_CHECKER.stat().st_mode & 0o111):
        fail("check-completion-proof.py must be executable")
    if not (PROOF_CHECKER_WRAPPER.stat().st_mode & 0o111):
        fail("scripts/check-completion-proof.py must be executable")

    valid_fixtures = sorted(FIXTURES_DIR.glob("valid-proof*.md"))
    invalid_fixtures = sorted(FIXTURES_DIR.glob("invalid-proof*.md"))
    if len(valid_fixtures) < 2:
        fail("completion proof checker needs at least two valid fixtures")
    if len(invalid_fixtures) < 10:
        fail("completion proof checker needs at least ten adversarial invalid fixtures")

    for path in valid_fixtures:
        result = run([sys.executable, str(PROOF_CHECKER), str(path)])
        if result.returncode != 0:
            fail(f"completion proof checker rejected {rel(path)}: {result.stdout}{result.stderr}")
        output = (result.stdout + result.stderr).lower()
        if "report contract satisfied" not in output:
            fail(f"completion proof checker success for {rel(path)} should describe report contract only")
        if "evidence is present" in output or "evidence verified" in output:
            fail("completion proof checker must not claim evidence truth")

    for path in invalid_fixtures:
        result = run([sys.executable, str(PROOF_CHECKER), str(path)])
        if result.returncode == 0:
            fail(f"completion proof checker accepted adversarial fixture: {rel(path)}")
        if "contract violations" not in (result.stdout + result.stderr).lower():
            fail(f"completion proof checker should explain contract violations for {rel(path)}")

    expected_failures = {
        "invalid-proof-negative-evidence.md": "not performed",
        "invalid-proof-id-mismatch.md": "claim ids",
        "invalid-proof-lint-only.md": "cannot prove behavior",
        "invalid-proof-risks-none.md": "remaining risks",
        "invalid-proof-missing-source-ref.md": "source-ref",
        "invalid-proof-did-not-pass.md": "failing or non-zero result",
        "invalid-proof-evidence-failed.md": "failing, skipped, or negative result",
        "invalid-proof-path-ok.md": "positive result marker",
        "invalid-proof-generic-production-claim.md": "generic rather than observable",
        "invalid-proof-quoted-number-counterexample.md": "concrete state, input, or disproof outcome",
        "invalid-proof-no-changed-files.md": "post-change completion proof",
        "invalid-proof-no-changed-files-version.md": "no-change statement",
        "invalid-proof-no-changed-files-passive.md": "no-change statement",
        "invalid-proof-no-changed-files-untouched.md": "no-change statement",
        "invalid-proof-missing-decision.md": "missing section: decision",
        "invalid-proof-nonverified-decision.md": "not a completion decision",
        "invalid-proof-evidence-final-failure.md": "failing, skipped, or negative result",
        "invalid-proof-check-error-count.md": "failing or non-zero result",
        "invalid-proof-check-contraction.md": "failing or non-zero result",
        "invalid-proof-check-unsuccessfully.md": "failing or non-zero result",
        "invalid-proof-check-status-unsuccessful.md": "failing or non-zero result",
        "invalid-proof-check-terminated-code.md": "failing or non-zero result",
        "invalid-proof-check-errors-equals.md": "failing or non-zero result",
        "invalid-proof-evidence-test-errored.md": "failing, skipped, or negative result",
        "invalid-proof-check-didnt-pass.md": "failing or non-zero result",
        "invalid-proof-generic-robust-claim.md": "generic rather than observable",
        "invalid-proof-generic-filter-robust.md": "generic rather than observable",
        "invalid-proof-generic-dependable.md": "generic rather than observable",
        "invalid-proof-generic-good.md": "generic rather than observable",
        "invalid-proof-generic-has-behavior.md": "generic rather than observable",
    }
    for filename, expected in expected_failures.items():
        result = run([sys.executable, str(PROOF_CHECKER), str(FIXTURES_DIR / filename)])
        if expected not in (result.stdout + result.stderr).lower():
            fail(f"{filename} should fail with an actionable {expected!r} message")

    fake_proof = """Root cause:
Changed files:
Context source:
Behavior claims: Everything works correctly for all users.
Counterexamples considered: Any input that would make it fail somehow.
Evidence: Not tested; not verified in a browser.
Checks run: none.
Remaining risks:
"""
    fake = run([sys.executable, str(PROOF_CHECKER)], input_text=fake_proof)
    if fake.returncode == 0:
        fail("completion proof checker accepted the original empty and negative-evidence counterexample")

    wrapper = run([sys.executable, str(PROOF_CHECKER_WRAPPER), str(valid_fixtures[0])])
    if wrapper.returncode != 0 or "report contract satisfied" not in wrapper.stdout.lower():
        fail(f"repo proof-checker wrapper failed: {wrapper.stdout}{wrapper.stderr}")

    base_report = (FIXTURES_DIR / "valid-proof.md").read_text(encoding="utf-8")

    def assert_rejected_variant(
        name: str,
        original: str,
        replacement: str,
        expected_message: str,
    ) -> None:
        if original not in base_report:
            fail(f"proof variant {name} could not find its source text")
        report = base_report.replace(original, replacement, 1)
        result = run([sys.executable, str(PROOF_CHECKER)], input_text=report)
        output = (result.stdout + result.stderr).lower()
        if result.returncode == 0 or expected_message not in output:
            fail(f"completion proof checker accepted or misdiagnosed variant {name}: {output}")

    changed_block = "Changed files:\n- src/pages/UserList.tsx\n- src/pages/UserList.test.tsx"
    for name, changed_text in [
        ("no-edits", "Changed files: No edits were made; src/pages/UserList.tsx was examined."),
        ("empty-diff", "Changed files: The diff is empty; src/pages/UserList.tsx was examined."),
        ("clean-tree", "Changed files: Working tree is clean; src/pages/UserList.tsx was examined."),
        ("zero-edits", "Changed files: Zero edits; src/pages/UserList.tsx was examined."),
        ("zh-no-change", "Changed files: 本次未修改任何文件，仅检查 src/pages/UserList.tsx。"),
    ]:
        assert_rejected_variant(name, changed_block, changed_text, "no-change statement")
    for name, changed_text in [
        ("url-as-file", "Changed files: https://example.com"),
        ("ftp-url-as-file", "Changed files: ftp://example.com/path.ts"),
        ("file-url-as-file", "Changed files: file:///tmp/example.py"),
        ("email-as-file", "Changed files: user@example.com"),
        ("pass-as-file", "Changed files: PASS"),
        ("verified-as-file", "Changed files: VERIFIED"),
        ("success-as-file", "Changed files: SUCCESS"),
        ("ticket-as-file", "Changed files: ABC-123"),
    ]:
        expected = (
            "not concrete file paths"
            if name in {"url-as-file", "ftp-url-as-file", "file-url-as-file", "email-as-file"}
            else "must list at least one"
        )
        assert_rejected_variant(name, changed_block, changed_text, expected)

    check_line = "- PASS: `npm test -- UserList.test.tsx` completed with exit code 0 and 2 tests passed."
    for name, check_text in [
        ("did-not-succeed", "- PASS: `npm test` passed setup but did not succeed overall."),
        ("returned-number", "- PASS: `npm test` returned 7."),
        ("exit-status-was", "- PASS: `npm test`; exit status was 7."),
        ("unexpected-exit", "- PASS: `npm test` observed exit 7 unexpectedly."),
        ("crashed", "- PASS: `npm test` passed setup but crashed before completion."),
        ("not-passed", "- PASS: `npm test` was not passed."),
        ("zh-not-passed", "- 通过：`npm test` 验证没有通过。"),
    ]:
        assert_rejected_variant(name, check_line, check_text, "failing or non-zero result")

    counter_line = (
        "- C1: If the user starts on page 3 and applies a filter whose matching records fit "
        "on one page, a request for page 3 would disprove the reset claim."
    )
    assert_rejected_variant(
        "generic-counterexample",
        counter_line,
        "- C1: If something goes wrong, the behavior is disproved.",
        "generic rather than a concrete disproof case",
    )

    evidence_line = (
        "- C1: PASS: Inspection of `src/pages/UserList.tsx` shows the filter handler setting "
        "page 1 before constructing the request, and the regression test passed while "
        "asserting the request page."
    )
    assert_rejected_variant(
        "generic-focused-evidence",
        evidence_line,
        "- C1: PASS: The focused test passed.",
        "generic rather than a concrete artifact",
    )

    claim_line = (
        '- C1 [source: specified] [source-ref: user request: "Changing a filter resets the '
        'visible list to page 1"]: Changing a filter resets the visible list to page 1 before '
        "the filtered request is sent."
    )
    for name, source_tags in [
        ("specified-as-assumption", "[source: specified] [source-ref: explicit assumption: preserve pagination]"),
        ("contract-as-user", '[source: existing-contract] [source-ref: user request: "reset pagination"]'),
        ("inferred-as-test", "[source: inferred] [source-ref: test src/pages/UserList.test.tsx]"),
    ]:
        assert_rejected_variant(
            name,
            claim_line,
            f"- C1 {source_tags}: Changing a filter resets the visible list to page 1 before the filtered request is sent.",
            "conflicts with its",
        )
    assert_rejected_variant(
        "generic-source-ref",
        claim_line,
        "- C1 [source: existing-contract] [source-ref: file current implementation]: "
        "Changing a filter resets the visible list to page 1 before the filtered request is sent.",
        "source-ref",
    )
    assert_rejected_variant(
        "unexplained-no-risk",
        "Remaining risks: Cross-page select-all was not exercised because this page does not enable batch selection.",
        "Remaining risks: No remaining risks.",
        "explain why none remain",
    )


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

        mode_stale = tmp / "bug-check-mode-stale"
        shutil.copytree(SKILL_DIR, mode_stale)
        mode_script = mode_stale / "scripts" / "build-bug-context.py"
        mode_script.chmod(mode_script.stat().st_mode & ~0o111)
        mode_result = run([sys.executable, str(INSTALL_VALIDATOR), "--target", str(mode_stale)])
        if mode_result.returncode == 0 or "stale" not in (mode_result.stdout + mode_result.stderr):
            fail("validate-install.py should detect a missing executable bit in an installed script")

        missing = tmp / "missing-bug-check"
        missing_result = run([sys.executable, str(INSTALL_VALIDATOR), "--target", str(missing)])
        if missing_result.returncode == 0 or "missing" not in (missing_result.stdout + missing_result.stderr):
            fail("validate-install.py should fail when all targets are missing")

        mixed_result = run(
            [
                sys.executable,
                str(INSTALL_VALIDATOR),
                "--target",
                str(SKILL_DIR),
                "--target",
                str(missing),
            ]
        )
        if mixed_result.returncode == 0 or "current" not in mixed_result.stdout or "missing" not in mixed_result.stdout:
            fail("validate-install.py should fail when any requested target is missing")


def validate_benchmark() -> None:
    if not (BENCHMARK_EVALUATOR.stat().st_mode & 0o111):
        fail("scripts/evaluate-benchmark.py must be executable")

    validation = run(
        [sys.executable, str(BENCHMARK_EVALUATOR), "--validate-only", "--json"]
    )
    if validation.returncode != 0:
        fail(f"benchmark validation failed: {validation.stdout}{validation.stderr}")
    try:
        validation_payload = json.loads(validation.stdout)
    except json.JSONDecodeError as exc:
        fail(f"evaluate-benchmark.py --json did not emit JSON: {exc}")
    if validation_payload.get("status") != "valid":
        fail("benchmark validator should report valid status")
    if validation_payload.get("case_count", 0) < 8:
        fail("benchmark baseline should contain at least eight anonymized replay cases")
    coverage = validation_payload.get("coverage", {})
    for group in ["categories", "stages", "decisions", "sources"]:
        if not coverage.get(group, {}).get("complete"):
            fail(f"benchmark baseline should completely cover required {group}")
    if validation_payload.get("privacy_check", {}).get("complete_anonymization_proof") is not False:
        fail("benchmark privacy lint must not claim complete anonymization proof")

    dataset = json.loads(BENCHMARK_CASES.read_text(encoding="utf-8"))
    expected_case_ids = [f"replay-{index:03d}" for index in range(1, len(dataset["cases"]) + 1)]
    if [case["case_id"] for case in dataset["cases"]] != expected_case_ids:
        fail("benchmark case IDs should be opaque, sequential replay-NNN identifiers")
    predictions = {
        "schema_version": dataset["schema_version"],
        "predictions": [
            {
                "case_id": case["case_id"],
                "stage": case["expected"]["stage"],
                "decision": case["expected"]["decision"],
                "source": case["expected"]["source"],
            }
            for case in dataset["cases"]
        ],
    }
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        predictions_path = tmp / "predictions.json"
        predictions_path.write_text(json.dumps(predictions), encoding="utf-8")
        scored = run(
            [
                sys.executable,
                str(BENCHMARK_EVALUATOR),
                "--predictions",
                str(predictions_path),
                "--json",
            ]
        )
        if scored.returncode != 0:
            fail(f"benchmark perfect-prediction scoring failed: {scored.stdout}{scored.stderr}")
        scored_payload = json.loads(scored.stdout)
        if scored_payload.get("scoring", {}).get("joint", {}).get("accuracy") != 1.0:
            fail("benchmark perfect predictions should receive exact joint score 1.0")
        for label in ["stage", "decision", "source"]:
            if scored_payload.get("scoring", {}).get(label, {}).get("accuracy") != 1.0:
                fail(f"benchmark perfect predictions should receive exact {label} score 1.0")

        boolean_prediction_version = json.loads(json.dumps(predictions))
        boolean_prediction_version["schema_version"] = True
        boolean_prediction_path = tmp / "boolean-prediction-schema.json"
        boolean_prediction_path.write_text(json.dumps(boolean_prediction_version), encoding="utf-8")
        boolean_prediction = run(
            [
                sys.executable,
                str(BENCHMARK_EVALUATOR),
                "--predictions",
                str(boolean_prediction_path),
            ]
        )
        if boolean_prediction.returncode == 0 or "schema_version must be" not in (
            boolean_prediction.stdout + boolean_prediction.stderr
        ):
            fail("benchmark prediction schema_version must reject boolean true")

        duplicate_prediction_path = tmp / "duplicate-prediction-key.json"
        duplicate_prediction_path.write_text(
            '{"schema_version":1,"predictions":[{"case_id":"replay-001",'
            '"stage":"clarify","decision":"verified",'
            '"decision":"product-decision-required","source":"product-decision-required"}]}',
            encoding="utf-8",
        )
        duplicate_prediction = run(
            [
                sys.executable,
                str(BENCHMARK_EVALUATOR),
                "--predictions",
                str(duplicate_prediction_path),
            ]
        )
        if duplicate_prediction.returncode == 0 or "duplicate JSON key" not in (
            duplicate_prediction.stdout + duplicate_prediction.stderr
        ):
            fail("benchmark prediction parser should reject duplicate JSON keys")

        for location in ["top-level", "prediction"]:
            extra_fields = json.loads(json.dumps(predictions))
            if location == "top-level":
                extra_fields["unexpected"] = "not declared by the prediction contract"
            else:
                extra_fields["predictions"][0]["explanation"] = "extra prose"
            extra_path = tmp / f"extra-{location}.json"
            extra_path.write_text(json.dumps(extra_fields), encoding="utf-8")
            extra_result = run(
                [
                    sys.executable,
                    str(BENCHMARK_EVALUATOR),
                    "--predictions",
                    str(extra_path),
                ]
            )
            if extra_result.returncode == 0 or "fields mismatch" not in (
                extra_result.stdout + extra_result.stderr
            ):
                fail(f"benchmark prediction validator should reject {location} extra fields")

        blind_path = tmp / "blind-prompts.json"
        blind = run(
            [
                sys.executable,
                str(BENCHMARK_EVALUATOR),
                "--export-prompts",
                str(blind_path),
            ]
        )
        if blind.returncode != 0 or not blind_path.exists():
            fail(f"benchmark blind prompt export failed: {blind.stdout}{blind.stderr}")
        blind_payload = json.loads(blind_path.read_text(encoding="utf-8"))
        if set(blind_payload) != {
            "schema_version",
            "task",
            "label_space",
            "prediction_contract",
            "prompts",
        }:
            fail("benchmark blind export should contain one shared gold-free task contract")
        if blind_payload.get("schema_version") != dataset["schema_version"]:
            fail("benchmark blind export schema version mismatch")
        if "identical" not in blind_payload.get("task", "").lower():
            fail("benchmark blind export should require the identical task contract for both runs")
        expected_blind_labels = {
            "stages": dataset["label_space"]["stages"],
            "decisions": dataset["label_space"]["decisions"],
            "sources": dataset["label_space"]["sources"],
        }
        if blind_payload.get("label_space") != expected_blind_labels:
            fail("benchmark blind export should include all scoring label vocabularies without categories")
        prediction_contract = blind_payload.get("prediction_contract", {})
        if prediction_contract.get("prediction_fields") != [
            "case_id",
            "stage",
            "decision",
            "source",
        ]:
            fail("benchmark blind export should define the prediction fields")
        prompts = blind_payload.get("prompts", [])
        if len(prompts) != len(dataset["cases"]):
            fail("benchmark blind prompt export should include every case")
        for prompt in prompts:
            if set(prompt) != {"case_id", "scenario"}:
                fail("benchmark blind prompt export must contain only case_id and scenario")
        serialized_blind = json.dumps(blind_payload, ensure_ascii=False)
        for forbidden_gold_key in ['"category"', '"expected"', '"rationale"', '"minimum_counterexample"']:
            if forbidden_gold_key in serialized_blind:
                fail(f"benchmark blind prompt export leaked gold field {forbidden_gold_key}")
        blind_stdout = run(
            [sys.executable, str(BENCHMARK_EVALUATOR), "--export-prompts", "-"]
        )
        if blind_stdout.returncode != 0 or json.loads(blind_stdout.stdout) != blind_payload:
            fail("benchmark blind prompt stdout export should match file export")

        for leaked_key in [
            "companyName",
            "customerDisplayName",
            "customerFullName",
            "customerName",
            "emailAddress",
            "memberName",
            "phoneNumber",
            "sourceUrl",
            "userEmail",
        ]:
            leaked = json.loads(BENCHMARK_CASES.read_text(encoding="utf-8"))
            leaked["cases"][0][leaked_key] = "Example Identity"
            leaked_path = tmp / f"leaked-{leaked_key}.json"
            leaked_path.write_text(json.dumps(leaked), encoding="utf-8")
            privacy = run(
                [
                    sys.executable,
                    str(BENCHMARK_EVALUATOR),
                    "--cases",
                    str(leaked_path),
                    "--validate-only",
                ]
            )
            if privacy.returncode == 0 or "identity-bearing field" not in (privacy.stdout + privacy.stderr):
                fail(f"benchmark validator should reject obvious identity field {leaked_key}")

        for nested_gold_key in ["category", "expected"]:
            nested_gold = json.loads(BENCHMARK_CASES.read_text(encoding="utf-8"))
            nested_gold["cases"][0]["scenario"][nested_gold_key] = nested_gold["cases"][0].get(
                nested_gold_key,
                nested_gold["cases"][0]["expected"],
            )
            nested_gold_path = tmp / f"nested-gold-{nested_gold_key}.json"
            nested_gold_path.write_text(json.dumps(nested_gold), encoding="utf-8")
            nested_result = run(
                [
                    sys.executable,
                    str(BENCHMARK_EVALUATOR),
                    "--cases",
                    str(nested_gold_path),
                    "--export-prompts",
                    str(tmp / f"nested-gold-{nested_gold_key}-prompts.json"),
                ]
            )
            if nested_result.returncode == 0 or "fields mismatch" not in (
                nested_result.stdout + nested_result.stderr
            ):
                fail(f"benchmark validator should reject nested gold field {nested_gold_key}")

        gold_variants = [
            ("equals", "=", False),
            ("arrow", " -> ", False),
            ("should-be", " should be ", False),
            ("space-label", ": ", True),
        ]
        for separator_name, separator, use_space_labels in gold_variants:
            explicit_gold = json.loads(BENCHMARK_CASES.read_text(encoding="utf-8"))
            gold_case = explicit_gold["cases"][0]
            labels = {
                field: gold_case["expected"][field].replace("-", " ")
                if use_space_labels
                else gold_case["expected"][field]
                for field in ["stage", "decision", "source"]
            }
            gold_case["scenario"]["report"] = (
                f"Gold answer: stage{separator}{labels['stage']}; "
                f"the expected decision{separator}{labels['decision']}; "
                f"source{separator}{labels['source']}"
            )
            explicit_gold_path = tmp / f"explicit-gold-{separator_name}-in-report.json"
            explicit_gold_path.write_text(json.dumps(explicit_gold), encoding="utf-8")
            explicit_gold_result = run(
                [
                    sys.executable,
                    str(BENCHMARK_EVALUATOR),
                    "--cases",
                    str(explicit_gold_path),
                    "--export-prompts",
                    str(tmp / f"explicit-gold-{separator_name}-prompts.json"),
                ]
            )
            explicit_gold_output = explicit_gold_result.stdout + explicit_gold_result.stderr
            if (
                explicit_gold_result.returncode == 0
                or "expected" not in explicit_gold_output
                or "label" not in explicit_gold_output
            ):
                fail(
                    f"benchmark validator should reject {separator_name} gold labels embedded in scenario text"
                )

        boolean_dataset_version = json.loads(BENCHMARK_CASES.read_text(encoding="utf-8"))
        boolean_dataset_version["schema_version"] = True
        boolean_dataset_path = tmp / "boolean-dataset-schema.json"
        boolean_dataset_path.write_text(json.dumps(boolean_dataset_version), encoding="utf-8")
        boolean_dataset = run(
            [
                sys.executable,
                str(BENCHMARK_EVALUATOR),
                "--cases",
                str(boolean_dataset_path),
                "--validate-only",
            ]
        )
        if boolean_dataset.returncode == 0 or "schema_version must be" not in (
            boolean_dataset.stdout + boolean_dataset.stderr
        ):
            fail("benchmark dataset schema_version must reject boolean true")

        duplicate_dataset_path = tmp / "duplicate-dataset-key.json"
        duplicate_dataset_text = BENCHMARK_CASES.read_text(encoding="utf-8").replace(
            '"schema_version": 1,',
            '"schema_version": 1,\n  "schema_version": 1,',
            1,
        )
        duplicate_dataset_path.write_text(duplicate_dataset_text, encoding="utf-8")
        duplicate_dataset = run(
            [
                sys.executable,
                str(BENCHMARK_EVALUATOR),
                "--cases",
                str(duplicate_dataset_path),
                "--validate-only",
            ]
        )
        if duplicate_dataset.returncode == 0 or "duplicate JSON key" not in (
            duplicate_dataset.stdout + duplicate_dataset.stderr
        ):
            fail("benchmark dataset parser should reject duplicate JSON keys")

        for field, error_text in [
            ("stage", "missing expected stages"),
            ("decision", "missing expected decisions"),
            ("source", "missing expected sources"),
        ]:
            values = [case["expected"][field] for case in dataset["cases"]]
            unique_value = next((value for value in values if values.count(value) == 1), None)
            if unique_value is None:
                fail(f"benchmark fixture needs a uniquely represented {field} to test coverage")
            missing_coverage = json.loads(BENCHMARK_CASES.read_text(encoding="utf-8"))
            label_group = {"stage": "stages", "decision": "decisions", "source": "sources"}[field]
            replacement = next(
                label for label in missing_coverage["label_space"][label_group] if label != unique_value
            )
            for case in missing_coverage["cases"]:
                if case["expected"][field] == unique_value:
                    case["expected"][field] = replacement
            missing_path = tmp / f"missing-{field}.json"
            missing_path.write_text(json.dumps(missing_coverage), encoding="utf-8")
            missing_result = run(
                [
                    sys.executable,
                    str(BENCHMARK_EVALUATOR),
                    "--cases",
                    str(missing_path),
                    "--validate-only",
                ]
            )
            if missing_result.returncode == 0 or error_text not in (missing_result.stdout + missing_result.stderr):
                fail(f"benchmark validator should reject incomplete {field} coverage")

        invalid_utf8 = tmp / "invalid-utf8.json"
        invalid_utf8.write_bytes(b"\xff")
        for utf8_args in [
            ["--cases", str(invalid_utf8), "--validate-only", "--json"],
            ["--predictions", str(invalid_utf8), "--json"],
        ]:
            utf8 = run([sys.executable, str(BENCHMARK_EVALUATOR), *utf8_args])
            if utf8.returncode != 2 or "traceback" in utf8.stderr.lower():
                fail("benchmark invalid UTF-8 should return structured exit 2 without traceback")
            try:
                utf8_payload = json.loads(utf8.stdout)
            except json.JSONDecodeError:
                fail("benchmark invalid UTF-8 --json response should be valid JSON")
            if utf8_payload.get("status") != "invalid" or "UTF-8" not in utf8_payload.get("error", ""):
                fail("benchmark invalid UTF-8 JSON should explain the encoding error")


def validate_openai_yaml() -> None:
    text = OPENAI_YAML.read_text(encoding="utf-8")
    lowered = text.lower()
    if 'display_name: "Bug Check"' not in text:
        fail("agents/openai.yaml display_name mismatch")
    for term in ["behavior", "product decisions", "counterexamples", "executed evidence"]:
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
    validate_behavior_contract_reference()
    validate_completion_proof_reference()
    validate_context_builder()
    validate_proof_checker()
    validate_install_validator()
    validate_benchmark()
    validate_openai_yaml()
    validate_readme()
    validate_public_positioning()

    print("PASS: bug-check behavior contract, proof tooling, replay baseline, and install checks are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
