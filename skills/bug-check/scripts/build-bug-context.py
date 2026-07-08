#!/usr/bin/env python3
"""Build a compact completion-proof context pack from changed files and bug text."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path.cwd()
MAX_DIFF_LINES = 180
MAX_DIFF_LINE_LENGTH = 220
EXCLUDED_PARTS = {
    ".bug-check",
    ".codex",
    ".codegraph",
    ".git",
    ".idea",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
}
LOCKFILE_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
}


def git_names(args: list[str]) -> list[str]:
    try:
        result = subprocess.run(["git", *args], text=True, capture_output=True, check=False, cwd=ROOT)
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def unique(items: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item and item not in seen:
            output.append(item)
            seen.add(item)
    return output


def path_matches(path: str, pathspecs: list[str] | None) -> bool:
    if not pathspecs:
        return True
    normalized = path.strip("/")
    for spec in pathspecs:
        clean = spec.strip("/")
        if normalized == clean or normalized.startswith(f"{clean}/"):
            return True
    return False


def diff_names(diff_args: list[str], pathspecs: list[str] | None = None) -> list[str]:
    command = ["diff", "--name-only", *diff_args]
    if pathspecs:
        command.extend(["--", *pathspecs])
    return git_names(command)


def changed_files_from_git(staged: bool, pathspecs: list[str] | None = None) -> list[str]:
    names: list[str] = []
    if staged:
        names.extend(diff_names(["--cached"], pathspecs))
    else:
        names.extend(diff_names(["HEAD"], pathspecs))
        for line in git_names(["status", "--short"]):
            if not line or line[:2].strip() != "??":
                continue
            path = line[3:] if len(line) > 3 else line[2:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            path = path.strip()
            if path_matches(path, pathspecs):
                names.append(path)
    return unique(names)


def changed_files_from_diff_range(diff_range: str, pathspecs: list[str] | None = None) -> list[str]:
    return unique(diff_names([diff_range], pathspecs))


def is_excluded(path: str) -> bool:
    parts = set(Path(path).parts)
    if parts & EXCLUDED_PARTS:
        return True
    return Path(path).name in LOCKFILE_NAMES


def normalize_files(files: list[str]) -> list[str]:
    return [path for path in unique(files) if path and not is_excluded(path)]


def safe_read(path: Path, limit: int) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def detect_project_signals(root: Path) -> list[str]:
    signals: list[str] = []
    package = root / "package.json"
    if package.exists():
        text = safe_read(package, limit=20000).lower()
        frameworks = [name for name in ["react", "next", "vue", "vite", "svelte", "express", "nestjs"] if name in text]
        label = "/".join(frameworks) if frameworks else "package.json present"
        signals.append(f"package.json: {label} detected")
    if (root / "pyproject.toml").exists():
        signals.append("pyproject.toml: Python project detected")
    if (root / "go.mod").exists():
        signals.append("go.mod: Go project detected")
    if (root / "Cargo.toml").exists():
        signals.append("Cargo.toml: Rust project detected")
    if any((root / name).exists() for name in ["tests", "test", "__tests__"]):
        signals.append("tests directory detected")
    return signals or ["no package/project marker detected from current directory"]


def candidate_test_paths(path: str) -> list[str]:
    source = Path(path)
    stem = source.stem
    suffixes = [source.suffix] if source.suffix else [".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"]
    candidates: list[Path] = []
    parent = source.parent
    for ext in suffixes:
        candidates.extend(
            [
                parent / f"{stem}.test{ext}",
                parent / f"{stem}.spec{ext}",
                parent / "__tests__" / f"{stem}.test{ext}",
                parent / "__tests__" / f"{stem}.spec{ext}",
                Path("tests") / parent / f"{stem}.test{ext}",
                Path("tests") / parent / f"{stem}.spec{ext}",
            ]
        )
    return [str(candidate) for candidate in candidates if (ROOT / candidate).exists()]


def nearby_tests(files: list[str]) -> list[str]:
    found: list[str] = []
    for path in files:
        found.extend(candidate_test_paths(path))
    return unique(found)


def read_next(files: list[str], tests: list[str]) -> list[str]:
    return unique(files + tests)[:10]


def collect_diff(files: list[str], diff_args: list[str]) -> list[str]:
    if not files:
        return []
    command = ["git", "diff", "--unified=3", *diff_args, "--", *files]
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=False, cwd=ROOT)
    except OSError:
        return []
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return trim_diff_lines(result.stdout.splitlines())


def trim_diff_lines(lines: list[str]) -> list[str]:
    output: list[str] = []
    for line in lines[:MAX_DIFF_LINES]:
        if len(line) > MAX_DIFF_LINE_LENGTH:
            line = f"{line[: MAX_DIFF_LINE_LENGTH - 3]}..."
        output.append(line)
    if len(lines) > MAX_DIFF_LINES:
        output.append(f"... diff truncated after {MAX_DIFF_LINES} lines ...")
    return output


def print_section(title: str, items: list[str], *, numbered: bool = False) -> None:
    print(f"{title}:")
    if items:
        for index, item in enumerate(items, start=1):
            prefix = f"{index}. " if numbered else "- "
            print(f"{prefix}{item}")
    else:
        print("- none detected")
    print()


def print_diff_section(diff_lines: list[str]) -> None:
    print("Diff context:")
    if diff_lines:
        print("```diff")
        for line in diff_lines:
            print(line)
        print("```")
    else:
        print("- no git diff detected for the changed scope")
    print()


def package_manager(root: Path) -> str | None:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists():
        return "bun"
    if (root / "package-lock.json").exists() or (root / "package.json").exists():
        return "npm"
    return None


def package_scripts(root: Path) -> set[str]:
    package = root / "package.json"
    if not package.exists():
        return set()
    try:
        data = json.loads(package.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return set()
    return {str(key) for key in scripts}


def verification_candidates(files: list[str], tests: list[str]) -> list[str]:
    candidates: list[str] = []
    manager = package_manager(ROOT)
    scripts = package_scripts(ROOT)
    test_paths = " ".join(tests[:4])

    if manager and "test" in scripts:
        candidates.append(f"{manager} test -- {test_paths}" if test_paths else f"{manager} test")
    if manager and "lint" in scripts:
        candidates.append(f"{manager} run lint")
    if manager and "typecheck" in scripts:
        candidates.append(f"{manager} run typecheck")
    if (ROOT / "pyproject.toml").exists() or any(path.endswith(".py") for path in files + tests):
        candidates.append(f"python3 -m pytest {test_paths}".strip())
    if (ROOT / "scripts" / "validate-project.py").exists():
        candidates.append("python3 scripts/validate-project.py")
    if not candidates:
        candidates.append("no automated command detected; verify the original path and material counterexamples manually")
    return unique(candidates)


def print_verification_candidates(files: list[str], tests: list[str]) -> None:
    print_section("Verification candidates (not executed)", verification_candidates(files, tests))


def print_proof_instructions() -> None:
    print("Proof instructions:")
    print("- State each material behavior claim introduced or fixed by this diff.")
    print("- For each claim, name the smallest concrete counterexample that would disprove it.")
    print("- Inspect whether the changed code handles each counterexample.")
    print("- Run the narrowest verification that proves the original path and material counterexamples.")
    print("- If evidence is missing for a material claim, continue fixing or report the risk instead of claiming completion.")
    print()


def print_no_changed_scope_guidance() -> None:
    print("No changed scope fallback:")
    print("- No changed files or explicit paths were available, so this is not a completion proof.")
    print("- Bug text may suggest tentative claims and counterexamples, but it cannot prove completion.")
    print("- Do not mark the fix complete until changed code is inspected and verified.")
    print("- Ask for changed files, wait for a diff, or rerun with explicit --files after implementation.")
    print()


def diff_source_args(staged: bool, base: str | None, diff_range: str | None) -> list[str]:
    if staged:
        return ["--cached"]
    if base:
        return [f"{base}...HEAD"]
    if diff_range:
        return [diff_range]
    return ["HEAD"]


def build_pack(files: list[str], bug_text: str, source: str, staged: bool, base: str | None, diff_range: str | None) -> int:
    files = normalize_files(files)
    diff_lines = collect_diff(files, diff_source_args(staged, base, diff_range))
    tests = nearby_tests(files)
    project_signals = detect_project_signals(ROOT)
    if tests:
        project_signals.append("tests: nearby tests detected")

    print("Completion Proof Pack")
    print()
    print(f"Source: {source}")
    if bug_text:
        print(f"Bug description: {bug_text}")
    print()
    print_section("Changed scope", files)
    print_section("Project signals", project_signals)
    print_diff_section(diff_lines)
    print_section("Read next", read_next(files, tests), numbered=True)
    print_verification_candidates(files, tests)
    print_proof_instructions()
    if not files:
        print_no_changed_scope_guidance()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bug", default="", help="Bug description, error text, or reproduction summary.")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--staged", action="store_true", help="Use staged git changes instead of all working tree changes.")
    source_group.add_argument("--base", help="Use git diff BASE...HEAD as the changed scope source.")
    source_group.add_argument("--diff-range", help="Use an explicit git diff range, such as main...HEAD or HEAD~1..HEAD.")
    parser.add_argument("--files", nargs="*", default=None, help="Changed files to route. Overrides git discovery.")
    args = parser.parse_args()

    pathspecs = args.files if args.files is not None and (args.staged or args.base or args.diff_range) else None
    if args.files is not None and not (args.staged or args.base or args.diff_range):
        files = args.files
        source = "explicit --files"
    elif args.base:
        files = changed_files_from_diff_range(f"{args.base}...HEAD", pathspecs)
        source = f"git diff {args.base}...HEAD"
    elif args.diff_range:
        files = changed_files_from_diff_range(args.diff_range, pathspecs)
        source = f"git diff {args.diff_range}"
    else:
        files = changed_files_from_git(staged=args.staged, pathspecs=pathspecs)
        source = "git diff --cached" if args.staged else "git diff/status"

    return build_pack(files, args.bug, source, staged=args.staged, base=args.base, diff_range=args.diff_range)


if __name__ == "__main__":
    raise SystemExit(main())
