#!/usr/bin/env python3
"""Build a compact completion-proof context pack from changed files and bug text."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


INVOCATION_ROOT = Path.cwd()


def repository_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
            check=False,
            cwd=INVOCATION_ROOT,
        )
    except OSError:
        return INVOCATION_ROOT
    if result.returncode != 0 or not result.stdout.strip():
        return INVOCATION_ROOT
    return Path(result.stdout.strip()).resolve()


ROOT = repository_root()
MAX_DIFF_LINES = 180
MAX_DIFF_LINE_LENGTH = 220
MAX_READ_NEXT = 10
TOOL_METADATA_PARTS = {
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
}
GENERATED_PARTS = {
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
    "Gemfile.lock",
    "gradle.lockfile",
    "uv.lock",
}
JS_SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts", ".vue", ".svelte"}
JS_TEST_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs")


class ContextError(RuntimeError):
    """An input or repository failure that makes the requested scope unreliable."""


@dataclass
class ScopeDiscovery:
    files: list[str]
    diff_args: list[str]
    notices: list[str]


@dataclass
class DiffContext:
    lines: list[str]
    omitted_lines: int = 0
    shortened_lines: int = 0
    omitted_characters: int = 0


@dataclass
class CappedPaths:
    shown: list[str]
    omitted: int


def run_git(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            text=True,
            input=input_text,
            capture_output=True,
            check=False,
            cwd=ROOT,
        )
    except OSError as error:
        raise ContextError(f"unable to run git: {error}") from error


def git_failure(args: list[str], result: subprocess.CompletedProcess[str]) -> ContextError:
    detail = (result.stderr or result.stdout).strip() or f"exit status {result.returncode}"
    return ContextError(f"`{shlex.join(['git', *args])}` failed: {detail}")


def git_names(args: list[str], *, required: bool = False, nul_terminated: bool = False) -> list[str]:
    result = run_git(args)
    if result.returncode != 0:
        if required:
            raise git_failure(args, result)
        return []
    if nul_terminated:
        return [item for item in result.stdout.split("\0") if item]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def unique(items: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item and item not in seen:
            output.append(item)
            seen.add(item)
    return output


def normalize_explicit_arguments(files: list[str]) -> list[str]:
    normalized: list[str] = []
    root = ROOT.resolve()
    for raw_path in files:
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = INVOCATION_ROOT / candidate
        resolved = Path(os.path.abspath(candidate))
        if resolved.is_dir() and not resolved.is_symlink():
            raise ContextError(f"explicit --files path must be a file, not a directory: {raw_path}")
        resolved_parent = resolved.parent.resolve(strict=False)
        try:
            resolved_parent.relative_to(root)
        except ValueError as exc:
            raise ContextError(
                f"explicit --files path traverses a parent symlink outside the project root: {raw_path}"
            ) from exc
        try:
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise ContextError(f"explicit --files path is outside the project root: {raw_path}") from exc
        normalized.append(relative.as_posix())
    return unique(normalized)


def diff_names(
    diff_args: list[str], pathspecs: list[str] | None = None, *, required: bool = False
) -> list[str]:
    command = ["--literal-pathspecs", "diff", "--name-only", "-z", *diff_args]
    if pathspecs:
        command.extend(["--", *pathspecs])
    return git_names(command, required=required, nul_terminated=True)


def is_git_worktree() -> bool:
    result = run_git(["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def has_git_head() -> bool:
    return run_git(["rev-parse", "--verify", "HEAD"]).returncode == 0


def empty_tree_oid() -> str:
    args = ["hash-object", "-t", "tree", "--stdin"]
    result = run_git(args, input_text="")
    if result.returncode != 0:
        raise git_failure(args, result)
    oid = result.stdout.strip()
    if not oid:
        raise ContextError("git returned no object ID for the empty tree")
    return oid


def untracked_files(pathspecs: list[str] | None = None) -> list[str]:
    command = ["--literal-pathspecs", "ls-files", "--others", "--exclude-standard", "-z"]
    if pathspecs:
        command.extend(["--", *pathspecs])
    return git_names(command, required=True, nul_terminated=True)


def changed_files_from_git(staged: bool, pathspecs: list[str] | None = None) -> ScopeDiscovery:
    if not is_git_worktree():
        if staged:
            raise ContextError("--staged requires the current directory to be a Git work tree")
        return ScopeDiscovery([], [], ["Git discovery skipped: current directory is not a Git work tree."])

    head_exists = has_git_head()
    notices: list[str] = []
    if staged:
        names = diff_names(["--cached"], pathspecs, required=True)
        if not head_exists:
            notices.append("HEAD is unborn; staged additions are compared with the empty repository.")
        return ScopeDiscovery(unique(names), ["--cached"], notices)

    diff_args = ["HEAD"] if head_exists else [empty_tree_oid()]
    names = diff_names(diff_args, pathspecs, required=True)
    untracked = untracked_files(pathspecs)
    names.extend(untracked)
    if not head_exists:
        notices.append("HEAD is unborn; tracked changes are compared with the empty repository and current worktree.")
    if untracked:
        notices.append(
            f"{len(untracked)} untracked path(s) are listed in scope but have no Git diff until staged."
        )
    return ScopeDiscovery(unique(names), diff_args, notices)


def changed_files_from_diff_range(diff_range: str, pathspecs: list[str] | None = None) -> ScopeDiscovery:
    files = unique(diff_names([diff_range], pathspecs, required=True))
    return ScopeDiscovery(files, [diff_range], [])


def validate_revision_value(option: str, value: str) -> None:
    if not value or value.startswith("-"):
        invalid_value = value or "<empty>"
        raise ContextError(
            f"{option} requires a Git revision or range, not an option-like value: {invalid_value}"
        )


def exclusion_reason(path: str) -> str | None:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(ROOT)
        except ValueError:
            pass
    parts = set(candidate.parts)
    if candidate.name in LOCKFILE_NAMES:
        return "lockfile"
    if parts & TOOL_METADATA_PARTS:
        return "tool metadata/cache"
    if parts & GENERATED_PARTS:
        return "generated/dependency output"
    return None


def normalize_files(files: list[str]) -> tuple[list[str], list[str]]:
    included: list[str] = []
    excluded: dict[str, list[str]] = {}
    for path in unique(files):
        reason = exclusion_reason(path)
        if reason:
            excluded.setdefault(reason, []).append(path)
        elif path:
            included.append(path)

    notices: list[str] = []
    for reason, paths in excluded.items():
        notices.append(
            f"Filtered {len(paths)} {reason} path(s) from detailed analysis: {', '.join(paths)}"
        )
    return included, notices


def validate_explicit_files(files: list[str]) -> list[str]:
    missing = [path for path in files if not (ROOT / path).exists()]
    if not missing:
        return []

    deleted: list[str] = []
    if is_git_worktree() and has_git_head():
        deleted = [path for path in missing if diff_names(["HEAD"], [path])]
    deleted_set = set(deleted)
    unknown = [path for path in missing if path not in deleted_set]
    if unknown:
        raise ContextError(f"explicit --files path(s) do not exist: {', '.join(unknown)}")
    return deleted


def explicit_files_discovery(files: list[str]) -> ScopeDiscovery:
    deleted = validate_explicit_files(files)
    if not is_git_worktree():
        return ScopeDiscovery(
            files,
            [],
            ["Git diff skipped for explicit files: current directory is not a Git work tree."],
        )
    notices = (
        [f"{len(deleted)} explicit deleted path(s) are resolved from the HEAD diff: {', '.join(deleted)}"]
        if deleted
        else []
    )
    explicit_untracked = untracked_files(files) if files else []
    if explicit_untracked:
        notices.append(
            f"{len(explicit_untracked)} explicit untracked path(s) are in scope but have no Git diff until staged: "
            f"{', '.join(explicit_untracked)}"
        )
    if has_git_head():
        return ScopeDiscovery(files, ["HEAD"], notices)
    notices.append("HEAD is unborn; explicit-file diff context compares the empty repository with the current worktree.")
    return ScopeDiscovery(
        files,
        [empty_tree_oid()],
        notices,
    )


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
        try:
            package_data = json.loads(safe_read(package, limit=20000))
        except json.JSONDecodeError:
            package_data = {}
        dependency_names: set[str] = set()
        if isinstance(package_data, dict):
            for field in ["dependencies", "devDependencies", "peerDependencies"]:
                dependencies = package_data.get(field)
                if isinstance(dependencies, dict):
                    dependency_names.update(str(name) for name in dependencies)
        framework_dependencies = {
            "react": "react",
            "next": "next",
            "vue": "vue",
            "vite": "vite",
            "svelte": "svelte",
            "express": "express",
            "nestjs": "@nestjs/core",
        }
        frameworks = [
            label for label, dependency in framework_dependencies.items() if dependency in dependency_names
        ]
        signals.append(f"package.json: {'/'.join(frameworks)} detected" if frameworks else "package.json present")
    if any((root / name).exists() for name in ["pyproject.toml", "setup.py", "setup.cfg"]):
        signals.append("Python project marker detected")
    if (root / "go.mod").exists():
        signals.append("go.mod: Go project detected")
    if (root / "Cargo.toml").exists():
        signals.append("Cargo.toml: Rust project detected")
    if (root / "Package.swift").exists():
        signals.append("Package.swift: Swift Package detected")
    if any(
        (root / name).exists()
        for name in ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradlew"]
    ):
        signals.append("Gradle project marker detected")
    if (root / "pom.xml").exists() or (root / "mvnw").exists():
        signals.append("Maven project marker detected")
    if any((root / name).is_dir() for name in ["tests", "test", "__tests__", "Tests"]):
        signals.append("tests directory detected")
    return signals or ["no package/project marker detected from current directory"]


def absolute_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def nearest_marker_root(source: Path, markers: tuple[str, ...]) -> Path | None:
    current = source.parent
    if current != ROOT and ROOT not in current.parents:
        return None
    while True:
        if any((current / marker).exists() for marker in markers):
            return current
        if current == ROOT:
            return None
        current = current.parent


def stripped_source_parent(source: Path) -> Path:
    try:
        relative = source.relative_to(ROOT).parent
    except ValueError:
        return source.parent
    parts = relative.parts
    if parts and parts[0] in {"src", "app", "lib"}:
        return Path(*parts[1:])
    return relative


def looks_like_test(path: Path) -> bool:
    lowered = path.name.lower()
    parts = {part.lower() for part in path.parts}
    return (
        bool(parts & {"test", "tests", "__tests__"})
        or ".test." in lowered
        or ".spec." in lowered
        or lowered.startswith("test_")
        or lowered.endswith("_test.go")
        or lowered.endswith(("test.java", "tests.java", "test.kt", "tests.kt", "tests.swift"))
    )


def js_test_candidates(source: Path) -> list[Path]:
    candidates: list[Path] = []
    parent = source.parent
    stem = source.stem
    for extension in JS_TEST_SUFFIXES:
        names = [f"{stem}.test{extension}", f"{stem}.spec{extension}"]
        for name in names:
            candidates.extend([parent / name, parent / "__tests__" / name])
        candidates.append(parent / "__tests__" / f"{stem}{extension}")

        try:
            relative_parent = source.relative_to(ROOT).parent
        except ValueError:
            continue
        trimmed_parent = stripped_source_parent(source)
        for test_root in [ROOT / "tests", ROOT / "test"]:
            for target_parent in unique([str(relative_parent), str(trimmed_parent)]):
                for name in names:
                    candidates.append(test_root / target_parent / name)
    return candidates


def python_test_candidates(source: Path) -> list[Path]:
    stem = source.stem
    names = [f"test_{stem}.py", f"{stem}_test.py"]
    candidates = [source.parent / name for name in names]
    candidates.extend(source.parent / "tests" / name for name in names)
    try:
        relative_parent = source.relative_to(ROOT).parent
    except ValueError:
        return candidates
    trimmed_parent = stripped_source_parent(source)
    for test_root in [ROOT / "tests", ROOT / "test"]:
        for name in names:
            candidates.extend(
                [
                    test_root / name,
                    test_root / relative_parent / name,
                    test_root / trimmed_parent / name,
                ]
            )
    return candidates


def rust_test_candidates(source: Path) -> list[Path]:
    candidates = [source.parent / f"{source.stem}_test.rs"]
    package_root = nearest_marker_root(source, ("Cargo.toml",))
    if package_root:
        candidates.extend(
            [
                package_root / "tests" / f"{source.stem}.rs",
                package_root / "tests" / f"{source.stem}_test.rs",
            ]
        )
    return candidates


def swift_test_candidates(source: Path) -> list[Path]:
    names = [f"{source.stem}Tests.swift", f"{source.stem}Test.swift", f"{source.stem}Spec.swift"]
    candidates = [source.parent / name for name in names]
    package_root = nearest_marker_root(source, ("Package.swift",))
    if not package_root:
        return candidates
    try:
        relative = source.relative_to(package_root)
    except ValueError:
        return candidates
    if len(relative.parts) >= 3 and relative.parts[0] == "Sources":
        module = relative.parts[1]
        nested_parent = Path(*relative.parent.parts[2:])
        test_root = package_root / "Tests" / f"{module}Tests"
        for name in names:
            candidates.extend([test_root / name, test_root / nested_parent / name])
    return candidates


def jvm_test_candidates(source: Path) -> list[Path]:
    try:
        parts = list(source.relative_to(ROOT).parts)
    except ValueError:
        return []
    candidates: list[Path] = []
    for index in range(len(parts) - 2):
        if parts[index : index + 2] != ["src", "main"]:
            continue
        language = parts[index + 2]
        if language not in {"java", "kotlin", "groovy"}:
            continue
        test_parent = ROOT.joinpath(*parts[:index], "src", "test", language, *parts[index + 3 : -1])
        extensions = {
            "java": (".java", ".kt"),
            "kotlin": (".kt", ".java"),
            "groovy": (".groovy", ".java"),
        }[language]
        for suffix in ["Test", "Tests", "Spec"]:
            for extension in extensions:
                candidates.append(test_parent / f"{source.stem}{suffix}{extension}")
    return candidates


def candidate_test_paths(path: str) -> list[str]:
    source = absolute_path(path)
    candidates: list[Path] = []
    if looks_like_test(source):
        candidates.append(source)
    if source.suffix.lower() in JS_SOURCE_SUFFIXES:
        candidates.extend(js_test_candidates(source))
    elif source.suffix.lower() == ".py":
        candidates.extend(python_test_candidates(source))
    elif source.suffix.lower() == ".go":
        candidates.append(source.with_name(f"{source.stem}_test.go"))
    elif source.suffix.lower() == ".rs":
        candidates.extend(rust_test_candidates(source))
    elif source.suffix.lower() == ".swift":
        candidates.extend(swift_test_candidates(source))
    elif source.suffix.lower() in {".java", ".kt", ".kts", ".groovy"}:
        candidates.extend(jvm_test_candidates(source))
    found: list[str] = []
    seen_files: set[tuple[int, int]] = set()
    for candidate in candidates:
        try:
            stat = candidate.stat()
        except OSError:
            continue
        if not candidate.is_file():
            continue
        identity = (stat.st_dev, stat.st_ino)
        if identity in seen_files:
            continue
        seen_files.add(identity)
        found.append(display_path(candidate))
    return found


def nearby_tests(files: list[str]) -> list[str]:
    found: list[str] = []
    seen_files: set[tuple[int, int]] = set()
    for path in files:
        for candidate in candidate_test_paths(path):
            try:
                stat = absolute_path(candidate).stat()
            except OSError:
                continue
            identity = (stat.st_dev, stat.st_ino)
            if identity in seen_files:
                continue
            seen_files.add(identity)
            found.append(candidate)
    return found


def read_next(files: list[str], tests: list[str]) -> CappedPaths:
    paths = unique(files + tests)
    return CappedPaths(paths[:MAX_READ_NEXT], max(0, len(paths) - MAX_READ_NEXT))


def collect_diff(files: list[str], diff_args: list[str]) -> DiffContext:
    if not files or not diff_args:
        return DiffContext([])
    command = ["--literal-pathspecs", "diff", "--unified=3", *diff_args, "--", *files]
    result = run_git(command)
    if result.returncode != 0:
        raise git_failure(command, result)
    if not result.stdout.strip():
        return DiffContext([])
    return trim_diff_lines(result.stdout.splitlines())


def trim_diff_lines(lines: list[str]) -> DiffContext:
    output: list[str] = []
    shortened_lines = 0
    omitted_characters = 0
    for line in lines[:MAX_DIFF_LINES]:
        if len(line) > MAX_DIFF_LINE_LENGTH:
            shortened_lines += 1
            omitted_characters += len(line) - (MAX_DIFF_LINE_LENGTH - 3)
            line = f"{line[: MAX_DIFF_LINE_LENGTH - 3]}..."
        output.append(line)
    return DiffContext(
        output,
        omitted_lines=max(0, len(lines) - MAX_DIFF_LINES),
        shortened_lines=shortened_lines,
        omitted_characters=omitted_characters,
    )


def print_section(title: str, items: list[str], *, numbered: bool = False) -> None:
    print(f"{title}:")
    if items:
        for index, item in enumerate(items, start=1):
            prefix = f"{index}. " if numbered else "- "
            print(f"{prefix}{item}")
    else:
        print("- none detected")
    print()


def print_diff_section(diff: DiffContext) -> None:
    print("Diff context:")
    if diff.lines:
        print("```diff")
        for line in diff.lines:
            print(line)
        print("```")
    else:
        print("- no git diff detected for the changed scope")
    print()
    truncation: list[str] = []
    if diff.omitted_lines:
        truncation.append(
            f"{diff.omitted_lines} line(s) omitted after the first {MAX_DIFF_LINES} diff lines."
        )
    if diff.shortened_lines:
        truncation.append(
            f"{diff.shortened_lines} long line(s) shortened; "
            f"{diff.omitted_characters} character(s) omitted at the {MAX_DIFF_LINE_LENGTH}-character limit."
        )
    if truncation:
        print_section("Diff truncation", truncation)


def print_read_next(paths: CappedPaths) -> None:
    print_section("Read next", paths.shown, numbered=True)
    if paths.omitted:
        print(
            f"Read next truncation: {paths.omitted} additional path(s) omitted "
            f"after the first {MAX_READ_NEXT}."
        )
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


def go_test_command(paths: list[str]) -> str:
    packages: list[str] = []
    for path in paths:
        if Path(path).suffix.lower() != ".go":
            continue
        candidate = absolute_path(path)
        try:
            parent = candidate.relative_to(ROOT).parent
        except ValueError:
            return "go test ./..."
        package = "." if parent == Path(".") else f"./{parent.as_posix()}"
        packages.append(package)
    return f"go test {shlex.join(unique(packages))}" if packages else "go test ./..."


def verification_candidates(files: list[str], tests: list[str]) -> list[str]:
    candidates: list[str] = []
    manager = package_manager(ROOT)
    scripts = package_scripts(ROOT)
    all_paths = files + tests
    names = {Path(path).name for path in files}
    suffixes = {Path(path).suffix.lower() for path in all_paths}
    js_test_paths = shlex.join([path for path in tests if Path(path).suffix.lower() in JS_TEST_SUFFIXES])
    python_test_paths = shlex.join([path for path in tests if Path(path).suffix.lower() == ".py"])
    js_relevant = bool(suffixes & JS_SOURCE_SUFFIXES) or "package.json" in names
    python_relevant = ".py" in suffixes or bool(names & {"pyproject.toml", "setup.py", "setup.cfg"})
    go_relevant = ".go" in suffixes or "go.mod" in names
    rust_relevant = ".rs" in suffixes or "Cargo.toml" in names
    swift_relevant = ".swift" in suffixes or "Package.swift" in names
    jvm_relevant = bool(suffixes & {".java", ".kt", ".kts", ".groovy"})
    gradle_relevant = jvm_relevant or bool(
        names & {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradlew"}
    )
    maven_relevant = jvm_relevant or bool(names & {"pom.xml", "mvnw"})

    if js_relevant and manager and "test" in scripts:
        candidates.append(f"{manager} test -- {js_test_paths}" if js_test_paths else f"{manager} test")
    if js_relevant and manager and "lint" in scripts:
        candidates.append(f"{manager} run lint")
    if js_relevant and manager and "typecheck" in scripts:
        candidates.append(f"{manager} run typecheck")
    if python_relevant:
        candidates.append(f"python3 -m pytest {python_test_paths}".strip())
    if go_relevant:
        candidates.append(go_test_command(all_paths))
    if rust_relevant:
        candidates.append("cargo test")
    if swift_relevant:
        candidates.append("swift test")
    if gradle_relevant and any(
        (ROOT / name).exists()
        for name in ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradlew"]
    ):
        candidates.append("./gradlew test" if (ROOT / "gradlew").exists() else "gradle test")
    if maven_relevant and ((ROOT / "pom.xml").exists() or (ROOT / "mvnw").exists()):
        candidates.append("./mvnw test" if (ROOT / "mvnw").exists() else "mvn test")
    if (ROOT / "scripts" / "validate-project.py").exists():
        candidates.append("python3 scripts/validate-project.py")
    if not candidates:
        candidates.append("no automated command detected; verify the original path and material counterexamples manually")
    return unique(candidates)


def print_verification_candidates(files: list[str], tests: list[str]) -> None:
    print_section("Verification candidates (not executed)", verification_candidates(files, tests))


def print_proof_instructions() -> None:
    print("Proof instructions:")
    print("- State each material behavior claim and label its source: specified, existing-contract, or inferred.")
    print("- For each claim, name the smallest concrete counterexample that would disprove it.")
    print("- Inspect whether the changed code handles each counterexample.")
    print("- Run the narrowest verification that proves the original path and material counterexamples.")
    print("- Treat product-decision-required as unresolved, never as a passed claim.")
    print("- If evidence is missing for a material claim, continue fixing or report the risk instead of claiming completion.")
    print()


def print_no_changed_scope_guidance() -> None:
    print("No changed scope fallback:")
    print("- No changed files or explicit paths were available, so this is not a completion proof.")
    print("- Bug text may suggest tentative claims and counterexamples, but it cannot prove completion.")
    print("- Do not mark the fix complete until changed code is inspected and verified.")
    print("- Ask for changed files, wait for a diff, or rerun with explicit --files after implementation.")
    print()


def build_pack(discovery: ScopeDiscovery, bug_text: str, source: str) -> int:
    files, filter_notices = normalize_files(discovery.files)
    diff = collect_diff(files, discovery.diff_args)
    tests = nearby_tests(files)
    project_signals = detect_project_signals(ROOT)
    if tests:
        project_signals.append(f"tests: {len(tests)} nearby test path(s) detected")

    print("Completion Proof Pack")
    print()
    print(f"Source: {source}")
    if bug_text:
        print(f"Bug description: {bug_text}")
    print()
    print_section("Changed scope", files)
    scope_notices = discovery.notices + filter_notices
    if scope_notices:
        print_section("Scope notices", scope_notices)
    print_section("Project signals", project_signals)
    print_diff_section(diff)
    print_section("Nearby tests", tests)
    print_read_next(read_next(files, tests))
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
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Changed files relative to the invocation directory. Directories are rejected; overrides git discovery.",
    )
    args = parser.parse_args()

    try:
        if args.base is not None:
            validate_revision_value("--base", args.base)
        if args.diff_range is not None:
            validate_revision_value("--diff-range", args.diff_range)
        has_diff_source = args.staged or args.base is not None or args.diff_range is not None
        explicit_files = normalize_explicit_arguments(args.files) if args.files is not None else None
        pathspecs = explicit_files if explicit_files is not None and has_diff_source else None
        if pathspecs == []:
            raise ContextError("--files requires at least one path when combined with --staged, --base, or --diff-range")
        if explicit_files is not None and not has_diff_source:
            discovery = explicit_files_discovery(explicit_files)
            source = "explicit --files"
        elif args.base is not None:
            diff_range = f"{args.base}...HEAD"
            discovery = changed_files_from_diff_range(diff_range, pathspecs)
            source = f"git diff {diff_range}"
        elif args.diff_range is not None:
            discovery = changed_files_from_diff_range(args.diff_range, pathspecs)
            source = f"git diff {args.diff_range}"
        else:
            discovery = changed_files_from_git(staged=args.staged, pathspecs=pathspecs)
            source = "git diff --cached" if args.staged else "git diff/status"
        return build_pack(discovery, args.bug, source)
    except ContextError as error:
        print(f"build-bug-context: error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
