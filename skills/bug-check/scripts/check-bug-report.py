#!/usr/bin/env python3
"""Check whether a bug-fix report satisfies the bug-check completion contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS: list[tuple[str, re.Pattern[str]]] = [
    ("root cause", re.compile(r"^\s*(root cause|根因|根源|原因)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("changed files", re.compile(r"^\s*(changed files|files changed|files|改动文件|修改文件)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("context pack source", re.compile(r"^\s*(context pack source|context source|上下文来源|上下文包来源)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("matched boundary cases", re.compile(r"^\s*(matched boundary cases|matched boundaries|boundary cases|命中的边界|边界情况)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("boundary handling table", re.compile(r"^\s*(boundary handling table|边界处理表)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("original path verification", re.compile(r"^\s*(original path verification|original path|reproduction verification|原路径验证|复现验证)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("boundary verification", re.compile(r"^\s*(boundary verification|边界验证)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("checks run", re.compile(r"^\s*(checks run|checks|tests run|executed checks|执行检查|验证命令)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("remaining risks", re.compile(r"^\s*(remaining risks|risks|剩余风险|风险)\s*:", re.IGNORECASE | re.MULTILINE)),
]

ALLOWED_STATUSES = ("relevant", "already handled", "missing -> fixed", "not applicable")


def read_report(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def has_boundary_table(text: str) -> bool:
    lowered = text.lower()
    header_ok = "| boundary | status | evidence | action |" in lowered
    separator_ok = bool(re.search(r"\|\s*-+\s*\|\s*-+\s*\|\s*-+\s*\|\s*-+\s*\|", lowered))
    status_ok = any(status in lowered for status in ALLOWED_STATUSES)
    pending_only = bool(re.search(r"\|\s*[^|\n]+\s*\|\s*pending\s*\|", lowered))
    return header_ok and separator_ok and status_ok and not pending_only


def extract_boundary_names(text: str) -> set[str]:
    names: set[str] = set()
    for line in text.splitlines():
        if "|" not in line or re.search(r"\|\s*-+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        name, status = cells[0], cells[1].lower()
        if name.lower() == "boundary":
            continue
        if status in ALLOWED_STATUSES:
            names.add(name)
    return names


def matched_cases_have_table_rows(text: str) -> bool:
    section_match = re.search(
        r"^\s*(matched boundary cases|matched boundaries|boundary cases|命中的边界|边界情况)\s*:\s*(.*?)(?:\n\s*[A-Za-z][A-Za-z ]{2,}\s*:|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return False
    matched_names = {
        item.strip().strip("-*` ")
        for item in re.split(r"[\n,]", section_match.group(2))
        if item.strip().strip("-*` ")
    }
    matched_names = {name for name in matched_names if re.match(r"^[a-z0-9-]+$", name)}
    if not matched_names:
        return False
    return matched_names.issubset(extract_boundary_names(text))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", help="Path to a final bug-fix report. Reads stdin when omitted.")
    args = parser.parse_args()

    text = read_report(args.report)
    missing = [label for label, pattern in REQUIRED_SECTIONS if not pattern.search(text)]
    if not has_boundary_table(text):
        missing.append("boundary handling table with final statuses")
    if not matched_cases_have_table_rows(text):
        missing.append("boundary handling table rows for matched boundary cases")

    if missing:
        print("FAIL: completion contract is missing:")
        for label in missing:
            print(f"- {label}")
        return 1

    print("PASS: completion contract evidence is present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
