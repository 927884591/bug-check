#!/usr/bin/env python3
"""Build a compact bug context pack from changed files and bug text."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path.cwd()
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
BOUNDARIES_DIR = SKILL_DIR / "references" / "boundaries"
EXCLUDED_PARTS = {".git", "node_modules", "dist", "build", ".next", ".turbo", "coverage", "__pycache__"}
LOCKFILE_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
}
MAX_DIFF_LINES = 180
MAX_DIFF_LINE_LENGTH = 220
SIGNAL_WORDS = (
    "abortcontroller",
    "aria-",
    "auth",
    "await",
    "cache",
    "callback",
    "cancel",
    "collation",
    "cookie",
    "cron",
    "currency",
    "cursor",
    "decimal",
    "debounce",
    "dedupe",
    "disabled",
    "drawer",
    "dst",
    "download",
    "empty",
    "error",
    "export",
    "fetch",
    "file",
    "filter",
    "focus",
    "form",
    "guard",
    "header",
    "hover",
    "idempotent",
    "import",
    "invalidate",
    "job",
    "keyboard",
    "locale",
    "localstorage",
    "mobile",
    "modal",
    "mutation",
    "offline",
    "pagination",
    "permission",
    "promise",
    "query",
    "querykey",
    "reconnect",
    "realtime",
    "request",
    "retry",
    "role=",
    "route",
    "rollback",
    "rounding",
    "sanitize",
    "secret",
    "session",
    "setstate",
    "sse",
    "sort",
    "stale",
    "subscription",
    "tenant",
    "timezone",
    "touch",
    "token",
    "transaction",
    "unmount",
    "upload",
    "useeffect",
    "viewport",
    "websocket",
    "worker",
    "xss",
)


@dataclass(frozen=True)
class BoundaryCard:
    name: str
    relative_path: str
    applies_when: tuple[str, ...]
    do_not_select_when: tuple[str, ...]


def git_names(args: list[str]) -> list[str]:
    try:
        result = subprocess.run(["git", *args], text=True, capture_output=True, check=False, cwd=ROOT)
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


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
        status_lines = git_names(["status", "--short"])
        for line in status_lines:
            if not line:
                continue
            status = line[:2]
            if status.strip() != "??":
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


def unique(items: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item and item not in seen:
            output.append(item)
            seen.add(item)
    return output


def is_excluded(path: str) -> bool:
    parts = set(Path(path).parts)
    if parts & EXCLUDED_PARTS:
        return True
    return Path(path).name in LOCKFILE_NAMES


def normalize_files(files: list[str]) -> list[str]:
    return [path for path in unique(files) if path and not is_excluded(path)]


def detect_project_signals(root: Path) -> list[str]:
    signals: list[str] = []
    package = root / "package.json"
    if package.exists():
        text = safe_read(package, limit=20000).lower()
        frameworks = []
        for name in ["react", "next", "vue", "vite", "svelte", "express", "nestjs"]:
            if name in text:
                frameworks.append(name)
        label = "/".join(frameworks) if frameworks else "package.json present"
        signals.append(f"package.json: {label} detected")
    if (root / "pyproject.toml").exists():
        signals.append("pyproject.toml: Python project detected")
    if (root / "go.mod").exists():
        signals.append("go.mod: Go project detected")
    if (root / "Cargo.toml").exists():
        signals.append("Cargo.toml: Rust project detected")
    if any((root / name).exists() for name in ["prisma", "migrations", "db", "database"]):
        signals.append("persistence folders detected")
    if any((root / name).exists() for name in ["tests", "test", "__tests__"]):
        signals.append("tests directory detected")
    return signals or ["no package/project marker detected from current directory"]


def safe_read(path: Path, limit: int) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def candidate_test_paths(path: str) -> list[str]:
    source = Path(path)
    stem = source.stem
    suffix = "".join(source.suffixes) or source.suffix
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
    if suffix and suffix not in suffixes:
        candidates.append(parent / f"{stem}.test{suffix}")
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
    command = ["git", "diff", "--unified=3"]
    command.extend(diff_args)
    command.extend(["--", *files])
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


def signal_words(files: list[str], bug_text: str, diff_lines: list[str]) -> list[str]:
    haystack = "\n".join([*files, bug_text, *diff_lines]).lower()
    found = [word for word in SIGNAL_WORDS if word in haystack]
    return unique(found)


def section_bullets(text: str, heading: str) -> tuple[str, ...]:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?:\n## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not match:
        return ()
    bullets: list[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return tuple(bullets)


def load_boundary_cards() -> list[BoundaryCard]:
    cards: list[BoundaryCard] = []
    for path in sorted(BOUNDARIES_DIR.glob("*.md")):
        text = safe_read(path, limit=20000)
        applies_when = section_bullets(text, "Applies When")
        do_not_select_when = section_bullets(text, "Do Not Select When")
        relative_path = path.relative_to(SKILL_DIR).as_posix()
        cards.append(
            BoundaryCard(
                name=path.stem,
                relative_path=relative_path,
                applies_when=applies_when,
                do_not_select_when=do_not_select_when,
            )
        )
    return cards


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


def print_card_index(cards: list[BoundaryCard]) -> None:
    print("Available boundary card index:")
    if not cards:
        print("- none detected")
    for card in cards:
        print(f"- {card.name} -> {card.relative_path}")
        for item in card.applies_when[:2]:
            print(f"  applies: {item}")
    print()


COMMON_TERMS = {
    "and",
    "are",
    "bug",
    "changed",
    "changes",
    "code",
    "file",
    "files",
    "include",
    "mentions",
    "only",
    "path",
    "text",
    "the",
    "when",
    "with",
}


def terms(text: str) -> set[str]:
    return {
        item
        for item in re.findall(r"[a-z0-9][a-z0-9-]{2,}", text.lower())
        if item not in COMMON_TERMS and not item.isdigit()
    }


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def matching_terms(card_terms: set[str], haystack: str) -> list[str]:
    normalized = normalize_text(haystack)
    return sorted(term for term in card_terms if term.replace("-", " ") in normalized or term in normalized)


def suggested_candidates(
    cards: list[BoundaryCard],
    files: list[str],
    bug_text: str,
    diff_lines: list[str],
) -> list[tuple[int, BoundaryCard, list[str]]]:
    file_text = "\n".join(files)
    diff_text = "\n".join(diff_lines)
    suggestions: list[tuple[int, BoundaryCard, list[str]]] = []
    for card in cards:
        card_terms = terms(" ".join([card.name, *card.applies_when]))
        path_hits = matching_terms(card_terms, file_text)
        bug_hits = matching_terms(card_terms, bug_text)
        diff_hits = matching_terms(card_terms, diff_text)
        score = len(path_hits) * 3 + len(bug_hits) * 2 + len(diff_hits)
        reasons: list[str] = []
        if path_hits:
            reasons.append(f"path hints: {', '.join(path_hits[:5])}")
        if bug_hits:
            reasons.append(f"bug hints: {', '.join(bug_hits[:5])}")
        if diff_hits:
            reasons.append(f"diff hints: {', '.join(diff_hits[:5])}")
        if score:
            suggestions.append((score, card, reasons))
    return sorted(suggestions, key=lambda item: (-item[0], item[1].name))[:6]


def print_suggested_candidates(cards: list[BoundaryCard], files: list[str], bug_text: str, diff_lines: list[str]) -> None:
    print("Suggested candidate cards (not final matches):")
    suggestions = suggested_candidates(cards, files, bug_text, diff_lines)
    if not suggestions:
        print("- none from weak path, bug, or diff signals")
    for score, card, reasons in suggestions:
        reason_text = "; ".join(reasons) if reasons else "weak evidence only"
        print(f"- {card.name} (score {score}): {reason_text}")
    print()


def print_selection_guidance() -> None:
    print("Card selection guidance:")
    print("- AI selects final boundary cards from evidence; this script only suggests candidates and does not decide matches.")
    print("- Use changed files, bug text, diff context, project signals, and nearby tests as evidence.")
    print("- Treat path and keyword hints as weak signals; apply each card's Do Not Select When rules before reading it.")
    print("- If no card fits, record a manual boundary instead of skipping boundary analysis.")
    print()


def print_no_changed_scope_guidance() -> None:
    print("No changed scope fallback:")
    print("- No changed files or explicit paths were available, so this is not a full boundary check.")
    print("- Bug text may suggest tentative boundary hypotheses, but those are not matched cards.")
    print("- Do not mark cards as covered, missing, fixed, or not applicable until changed code is inspected.")
    print("- Ask for changed files, wait for a diff, or rerun with explicit --files after implementation.")
    print()


def print_boundary_table_template() -> None:
    print("Boundary handling table template:")
    print("| Boundary | Status | Evidence | Action |")
    print("|---|---|---|---|")
    print("| selected-boundary | relevant | why this card was selected from code/diff evidence | inspect, fix, or verify |")


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
        candidates.append("no automated command detected; verify the original path and selected boundary manually")
    return unique(candidates)


def print_verification_candidates(files: list[str], tests: list[str]) -> None:
    print_section("Verification candidates (not executed)", verification_candidates(files, tests))


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
    signals = signal_words(files, bug_text, diff_lines)
    cards = load_boundary_cards()
    tests = nearby_tests(files)
    project_signals = detect_project_signals(ROOT)
    if tests:
        project_signals.append("tests: nearby tests detected")

    print("Bug Context Pack")
    print()
    print(f"Source: {source}")
    if bug_text:
        print(f"Bug description: {bug_text}")
    print()
    print_section("Changed scope", files)
    print_section("Project signals", project_signals)
    print_diff_section(diff_lines)
    print_section("Diff signal words", signals)
    print_suggested_candidates(cards, files, bug_text, diff_lines)
    print_card_index(cards)
    print_selection_guidance()
    if not files:
        print_no_changed_scope_guidance()
    print_section("Read next", read_next(files, tests), numbered=True)
    print_verification_candidates(files, tests)
    print_boundary_table_template()
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
