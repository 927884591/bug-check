#!/usr/bin/env python3
"""Build a compact bug context pack from changed files and bug text."""

from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path.cwd()
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


@dataclass(frozen=True)
class Route:
    name: str
    path_patterns: tuple[str, ...]
    words: tuple[str, ...]
    cards: tuple[str, ...]
    inspect: tuple[str, ...]
    avoid: tuple[str, ...]


ROUTES: tuple[Route, ...] = (
    Route(
        name="list-table-ui",
        path_patterns=(
            "*List*",
            "*Table*",
            "*/pages/*",
            "*/components/*",
            "*/views/*",
            "*/table/*",
            "*/tables/*",
        ),
        words=("search", "filter", "reset", "pagination", "page", "selected", "select all", "empty", "delete", "sort"),
        cards=("ui-list-table", "state-cache-sync"),
        inspect=("search/filter state", "page index reset", "selected rows", "list/detail/count refresh"),
        avoid=("unrelated routes", "global styles", "full services directory"),
    ),
    Route(
        name="form-validation",
        path_patterns=(
            "*Form.*",
            "*Form/*",
            "*-form.*",
            "*_form.*",
            "*/form/*",
            "*/forms/*",
            "*Dialog*",
            "*Modal*",
            "*/validators/*",
            "*/validation/*",
            "*/schema/*",
        ),
        words=("form", "validation", "submit", "save", "duplicate", "required", "disabled", "hidden", "max length", "error"),
        cards=("form-validation", "api-contract", "state-cache-sync"),
        inspect=("form schema and visibility", "submit loading/error state", "backend validation errors", "save invalidation"),
        avoid=("unrelated list rendering", "unrelated deployment config"),
    ),
    Route(
        name="api-contract",
        path_patterns=(
            "*/api/*",
            "*/client/*",
            "*/clients/*",
            "*/request/*",
            "*/requests/*",
            "*/service/*",
            "*/services/*",
            "*/controllers/*",
            "*/routes/*",
            "*Controller*",
            "*Service*",
        ),
        words=("400", "404", "409", "422", "500", "response", "request", "params", "headers", "body", "serialization", "dto", "schema", "openapi"),
        cards=("api-contract",),
        inspect=("API method/path/params/body", "status-code branches", "error body shape", "client/server DTO sync"),
        avoid=("unrelated UI layout files", "full migrations directory unless persistence is implicated"),
    ),
    Route(
        name="auth-permission",
        path_patterns=("*/auth/*", "*/permission/*", "*/permissions/*", "*/session/*", "*/login/*", "*/middleware/*", "*/guard/*"),
        words=("login", "logout", "session", "token", "permission", "role", "unauthorized", "forbidden", "password", "expired", "401", "403"),
        cards=("auth-permission",),
        inspect=("route/API guards", "session state machine", "menu/button/API permission consistency", "token cleanup"),
        avoid=("unrelated table pagination", "unrelated worker queues"),
    ),
    Route(
        name="tenant-context",
        path_patterns=("*/tenant/*", "*/project/*", "*/site/*", "*/organization/*", "*/org/*", "*/workspace/*"),
        words=("tenant", "project", "site", "org", "organization", "workspace", "switch", "isolation", "leak", "cross tenant"),
        cards=("tenant-isolation", "state-cache-sync", "security-sensitive-data"),
        inspect=("active context propagation", "cache keys and selected rows", "exports and realtime requests", "server-side authorization"),
        avoid=("unrelated visual styling", "unrelated deployment scripts"),
    ),
    Route(
        name="database-persistence",
        path_patterns=("*/db/*", "*/database/*", "*/models/*", "*/repositories/*", "*/repo/*", "*/migrations/*", "*/prisma/*", "*/sql/*"),
        words=("transaction", "migration", "query", "join", "index", "duplicate", "soft delete", "rollback", "deadlock", "constraint", "backfill"),
        cards=("database-transaction", "tenant-isolation", "api-contract"),
        inspect=("query filters and ordering", "transaction boundaries", "migration safety", "tenant/user scoping"),
        avoid=("unrelated component CSS", "unrelated browser-only code"),
    ),
    Route(
        name="queue-worker",
        path_patterns=("*/jobs/*", "*/job/*", "*/queue/*", "*/queues/*", "*/worker/*", "*/workers/*", "*/scheduler/*", "*/cron/*", "*/webhook/*"),
        words=("queue", "worker", "job", "retry", "dead letter", "scheduler", "cron", "webhook", "duplicate", "idempotent", "timeout", "out of order"),
        cards=("async-job-queue",),
        inspect=("idempotency and dedupe", "retry/timeout/dead-letter behavior", "worker transaction boundaries", "deploy restart behavior"),
        avoid=("unrelated UI components", "unrelated static assets"),
    ),
    Route(
        name="deployment-config",
        path_patterns=("*.env*", "*/config/*", "*/deploy/*", "*/deployment/*", "*/docker/*", "*/Dockerfile", "*/compose*.yml", "*/helm/*", "*/k8s/*", "*/ci/*", ".github/*"),
        words=("env", "config", "deploy", "staging", "production", "feature flag", "compatibility", "health check", "startup", "rollback", "secret"),
        cards=("deployment-config", "api-contract", "security-sensitive-data"),
        inspect=("env defaults and required secrets", "feature flag states", "startup/readiness ordering", "old/new version compatibility"),
        avoid=("unrelated form fields", "unrelated table rendering"),
    ),
    Route(
        name="security-sensitive-data",
        path_patterns=("*/security/*", "*/download/*", "*/export/*", "*/upload/*", "*/render/*", "*/html/*", "*/logger/*", "*/logging/*"),
        words=("xss", "injection", "sanitize", "token", "cookie", "secret", "password", "private", "pii", "sensitive", "download", "export", "log", "html"),
        cards=("security-sensitive-data", "auth-permission", "tenant-isolation"),
        inspect=("unsafe rendering and links", "logs and telemetry", "server-side authorization", "export/download contents"),
        avoid=("unrelated cosmetic layout", "unrelated pagination state unless the leak appears there"),
    ),
)


def git_names(args: list[str]) -> list[str]:
    try:
        result = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files_from_git(staged: bool) -> list[str]:
    names: list[str] = []
    if staged:
        names.extend(git_names(["diff", "--cached", "--name-only"]))
    else:
        names.extend(git_names(["diff", "--name-only", "HEAD"]))
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
            names.append(path.strip())
    return unique(names)


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


def match_pattern(path: str, pattern: str) -> bool:
    normalized = path.replace(os.sep, "/")
    if fnmatch.fnmatch(normalized, pattern):
        return True
    if fnmatch.fnmatch(Path(normalized).name, pattern):
        return True
    if pattern.startswith("*/") and fnmatch.fnmatch(normalized, pattern[2:]):
        return True
    return False


def route_score(route: Route, files: list[str], bug_text: str) -> int:
    score, _path_hits, _word_hits = route_hits(route, files, bug_text)
    return score


def route_hits(route: Route, files: list[str], bug_text: str) -> tuple[int, int, int]:
    score = 0
    path_hits = 0
    word_hits = 0
    lowered = bug_text.lower()
    for path in files:
        path_lower = path.lower()
        for pattern in route.path_patterns:
            if match_pattern(path, pattern) or match_pattern(path_lower, pattern.lower()):
                score += 3
                path_hits += 1
    for word in route.words:
        if word.lower() in lowered:
            score += 2
            word_hits += 1
    return score, path_hits, word_hits


def matched_routes(files: list[str], bug_text: str) -> list[tuple[Route, int]]:
    details = [(route, *route_hits(route, files, bug_text)) for route in ROUTES]
    strong_non_api = any(route.name != "api-contract" and score >= 3 for route, score, _path_hits, _word_hits in details)
    matches: list[tuple[Route, int]] = []
    for route, score, _path_hits, word_hits in details:
        if score < 3:
            continue
        if route.name == "api-contract" and word_hits == 0 and strong_non_api:
            continue
        matches.append((route, score))
    matches.sort(key=lambda item: (-item[1], item[0].name))
    return matches


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


def print_section(title: str, items: list[str], *, numbered: bool = False) -> None:
    print(f"{title}:")
    if items:
        for index, item in enumerate(items, start=1):
            prefix = f"{index}. " if numbered else "- "
            print(f"{prefix}{item}")
    else:
        print("- none detected")
    print()


def build_pack(files: list[str], bug_text: str, source: str) -> int:
    files = normalize_files(files)
    matches = matched_routes(files, bug_text)
    cards = unique([card for route, _score in matches for card in route.cards])
    inspect = unique([item for route, _score in matches for item in route.inspect])
    avoid = unique([item for route, _score in matches for item in route.avoid])
    tests = nearby_tests(files)
    signals = detect_project_signals(ROOT)
    if tests:
        signals.append("tests: nearby tests detected")

    print("Bug Context Pack")
    print()
    print(f"Source: {source}")
    if bug_text:
        print(f"Bug description: {bug_text}")
    print()
    print_section("Changed scope", files)
    print_section("Project signals", signals)
    print_section("Matched boundary cards", cards)
    print_section("Read next", read_next(files, tests), numbered=True)
    print_section("Inspect first", inspect)
    print_section("Do not read yet", avoid)
    print("Boundary handling table template:")
    print("| Boundary | Status | Evidence | Action |")
    print("|---|---|---|---|")
    for card in cards:
        print(f"| {card} | pending | | |")
    if not cards:
        print("| none matched | pending | add manual routing from bug evidence | inspect changed files first |")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bug", default="", help="Bug description, error text, or reproduction summary.")
    parser.add_argument("--staged", action="store_true", help="Use staged git changes instead of all working tree changes.")
    parser.add_argument("--files", nargs="*", default=None, help="Changed files to route. Overrides git discovery.")
    args = parser.parse_args()

    if args.files is not None and len(args.files) > 0:
        files = args.files
        source = "explicit --files"
    else:
        files = changed_files_from_git(staged=args.staged)
        source = "git diff --cached" if args.staged else "git diff/status"

    return build_pack(files, args.bug, source)


if __name__ == "__main__":
    raise SystemExit(main())
