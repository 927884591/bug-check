#!/usr/bin/env python3
"""Check whether a bug-fix report includes the required completion evidence."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("root cause", re.compile(r"\b(root cause|根因|根源|原因)\b", re.IGNORECASE)),
    ("changed behavior or files", re.compile(r"\b(changes?|changed|files?|改动|修改|文件)\b", re.IGNORECASE)),
    ("original path verification", re.compile(r"\b(repro|reproduction|original path|原路径|复现|验证)\b", re.IGNORECASE)),
    ("boundary cases", re.compile(r"\b(boundar(y|ies)|edge cases?|边界|边界情况)\b", re.IGNORECASE)),
    ("executed checks", re.compile(r"\b(test|tests|lint|typecheck|build|ui|screenshot|测试|构建|检查)\b", re.IGNORECASE)),
    ("remaining risks", re.compile(r"\b(risk|risks|unverified|remaining|风险|未验证|剩余)\b", re.IGNORECASE)),
]


def read_report(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", help="Path to a final bug-fix report. Reads stdin when omitted.")
    args = parser.parse_args()

    text = read_report(args.report)
    missing = [label for label, pattern in REQUIRED_PATTERNS if not pattern.search(text)]

    if missing:
        print("FAIL: completion contract is missing:")
        for label in missing:
            print(f"- {label}")
        return 1

    print("PASS: completion contract evidence is present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
