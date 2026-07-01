#!/usr/bin/env python3
"""Check whether installed bug-check skill copies match this repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "skills" / "bug-check"
EXCLUDED_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


@dataclass(frozen=True)
class TargetStatus:
    path: Path
    status: str
    reason: str
    digest: str | None


def default_targets() -> list[Path]:
    targets = [
        Path.home() / ".codex" / "skills" / "bug-check",
        Path.home() / ".agents" / "skills" / "bug-check",
    ]
    skills_dir = os.environ.get("AGENT_SKILLS_DIR")
    if skills_dir:
        targets.append(Path(skills_dir) / "bug-check")
    return unique_paths(targets)


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    output: list[Path] = []
    for path in paths:
        key = str(path.expanduser().resolve() if path.exists() else path.expanduser())
        if key not in seen:
            output.append(path.expanduser())
            seen.add(key)
    return output


def included_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
            continue
        if "__pycache__" in path.parts:
            continue
        files.append(path)
    return sorted(files)


def directory_hash(root: Path) -> str | None:
    if not root.exists() or not root.is_dir():
        return None
    digest = hashlib.sha256()
    for path in included_files(root):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def check_target(path: Path, source_hash: str | None) -> TargetStatus:
    if source_hash is None:
        return TargetStatus(path=path, status="error", reason="source skill directory is missing", digest=None)
    target_hash = directory_hash(path)
    if target_hash is None:
        return TargetStatus(path=path, status="missing", reason="target skill directory is missing", digest=None)
    if target_hash == source_hash:
        return TargetStatus(path=path, status="current", reason="target matches repository source", digest=target_hash)
    return TargetStatus(path=path, status="stale", reason="target exists but differs from repository source", digest=target_hash)


def as_json(source_hash: str | None, targets: list[TargetStatus]) -> dict[str, Any]:
    return {
        "source": str(SOURCE_DIR),
        "source_hash": source_hash,
        "targets": [
            {
                "path": str(item.path),
                "status": item.status,
                "reason": item.reason,
                "hash": item.digest,
            }
            for item in targets
        ],
    }


def print_text(source_hash: str | None, targets: list[TargetStatus]) -> None:
    print("bug-check Install Validation")
    print(f"Source: {SOURCE_DIR}")
    print(f"Source hash: {source_hash or 'unavailable'}")
    print()
    for item in targets:
        print(f"- {item.status}: {item.path}")
        print(f"  reason: {item.reason}")
        if item.digest:
            print(f"  hash: {item.digest}")
    print()


def exit_code(source_hash: str | None, targets: list[TargetStatus]) -> int:
    if source_hash is None:
        return 1
    has_current = any(item.status == "current" for item in targets)
    has_stale = any(item.status == "stale" for item in targets)
    if has_current and not has_stale:
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", default=[], help="Installed bug-check skill directory to check. Repeatable.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    targets = [Path(item).expanduser() for item in args.target] if args.target else default_targets()
    source_hash = directory_hash(SOURCE_DIR)
    results = [check_target(path, source_hash) for path in targets]

    if args.json:
        print(json.dumps(as_json(source_hash, results), indent=2, sort_keys=True))
    else:
        print_text(source_hash, results)

    return exit_code(source_hash, results)


if __name__ == "__main__":
    raise SystemExit(main())
