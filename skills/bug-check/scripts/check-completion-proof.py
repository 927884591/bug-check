#!/usr/bin/env python3
"""Check whether a final report satisfies the bug-check completion-proof contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("root cause", re.compile(r"^\s*(root cause|根因|根源|原因)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("changed files", re.compile(r"^\s*(changed files|files changed|files|改动文件|修改文件)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("context source", re.compile(r"^\s*(context source|context pack source|上下文来源|上下文包来源)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("behavior claims", re.compile(r"^\s*(behavior claims|behavior claim|claims|行为声明|行为主张|行为断言)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("counterexamples considered", re.compile(r"^\s*(counterexamples considered|counterexamples|smallest counterexamples|反例|最小反例)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("evidence", re.compile(r"^\s*(evidence|proof evidence|证据|证明证据)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("checks run", re.compile(r"^\s*(checks run|checks|tests run|executed checks|执行检查|验证命令)\s*:", re.IGNORECASE | re.MULTILINE)),
    ("remaining risks", re.compile(r"^\s*(remaining risks|risks|剩余风险|风险)\s*:", re.IGNORECASE | re.MULTILINE)),
]

SECTION_HEADING = re.compile(
    r"^\s*(root cause|根因|根源|原因|changed files|files changed|files|改动文件|修改文件|context source|context pack source|上下文来源|上下文包来源|behavior claims|behavior claim|claims|行为声明|行为主张|行为断言|counterexamples considered|counterexamples|smallest counterexamples|反例|最小反例|evidence|proof evidence|证据|证明证据|checks run|checks|tests run|executed checks|执行检查|验证命令|remaining risks|risks|剩余风险|风险)\s*:",
    re.IGNORECASE | re.MULTILINE,
)

NON_PROOF_COMMANDS = (
    "lint",
    "build",
    "typecheck",
    "tsc",
    "format",
)
PROOF_WORDS = (
    "assert",
    "browser",
    "inspected",
    "log",
    "manual",
    "pytest",
    "reproduced",
    "request",
    "response",
    "runtime",
    "screenshot",
    "spec",
    "test",
    "verified",
    "复现",
    "检查",
    "浏览器",
    "请求",
    "响应",
    "截图",
    "断言",
    "测试",
    "验证",
)


def read_report(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def first_section(text: str, pattern: re.Pattern[str]) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_match = SECTION_HEADING.search(text, start)
    end = next_match.start() if next_match else len(text)
    return text[start:end].strip()


def missing_sections(text: str) -> list[str]:
    return [label for label, pattern in SECTION_PATTERNS if not pattern.search(text)]


def has_substantial_text(section: str) -> bool:
    normalized = re.sub(r"[\s\-*`|:.;,，。]+", "", section)
    lowered = normalized.lower()
    return len(normalized) >= 8 and lowered not in {"none", "n/a", "unknown", "无", "无风险", "未列出"}


def has_non_lint_evidence(evidence: str, checks: str) -> bool:
    combined = f"{evidence}\n{checks}".lower()
    if not has_substantial_text(evidence):
        return False
    if not any(word in combined for word in PROOF_WORDS):
        return False
    without_non_proof = combined
    for word in NON_PROOF_COMMANDS:
        without_non_proof = without_non_proof.replace(word, "")
    return bool(re.search(r"[a-z\u4e00-\u9fff]{4,}", without_non_proof))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", help="Path to a final proof report. Reads stdin when omitted.")
    args = parser.parse_args()

    text = read_report(args.report)
    missing = missing_sections(text)

    claim_section = first_section(text, SECTION_PATTERNS[3][1])
    counterexample_section = first_section(text, SECTION_PATTERNS[4][1])
    evidence_section = first_section(text, SECTION_PATTERNS[5][1])
    checks_section = first_section(text, SECTION_PATTERNS[6][1])

    if "behavior claims" not in missing and not has_substantial_text(claim_section):
        missing.append("non-empty behavior claims")
    if "counterexamples considered" not in missing and not has_substantial_text(counterexample_section):
        missing.append("concrete counterexamples")
    if "evidence" not in missing and not has_non_lint_evidence(evidence_section, checks_section):
        missing.append("evidence beyond lint/build")

    if missing:
        print("FAIL: completion proof is missing:")
        for label in missing:
            print(f"- {label}")
        return 1

    print("PASS: completion proof evidence is present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
