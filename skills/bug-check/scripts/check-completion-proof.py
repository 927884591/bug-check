#!/usr/bin/env python3
"""Lint a formal completion-proof report without asserting that its evidence is true."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "decision": ("decision", "engineering decision", "决策", "工程决策"),
    "root cause": (
        "root cause",
        "change rationale",
        "根因",
        "根源",
        "原因",
        "变更依据",
    ),
    "changed files": ("changed files", "files changed", "files", "改动文件", "修改文件"),
    "context source": ("context source", "context pack source", "上下文来源", "上下文包来源"),
    "behavior claims": (
        "behavior claims",
        "behavior claim",
        "claims",
        "行为声明",
        "行为主张",
        "行为断言",
    ),
    "counterexamples considered": (
        "counterexamples considered",
        "counterexamples",
        "smallest counterexamples",
        "反例",
        "最小反例",
    ),
    "evidence": ("evidence", "proof evidence", "证据", "证明证据"),
    "checks run": (
        "checks run",
        "checks",
        "tests run",
        "executed checks",
        "执行检查",
        "验证命令",
    ),
    "remaining risks": ("remaining risks", "risks", "剩余风险", "风险"),
}
REQUIRED_SECTIONS = tuple(SECTION_ALIASES)
ALIAS_TO_SECTION = {
    alias.casefold(): section
    for section, aliases in SECTION_ALIASES.items()
    for alias in aliases
}
HEADING_ALTERNATION = "|".join(
    re.escape(alias)
    for alias in sorted(ALIAS_TO_SECTION, key=len, reverse=True)
)
SECTION_HEADING = re.compile(
    rf"^\s{{0,3}}(?:#{{1,6}}\s*)?(?:\*\*|__)?"
    rf"(?P<heading>{HEADING_ALTERNATION})\s*(?:\*\*|__)?\s*[:：]\s*"
    rf"(?:\*\*|__)?\s*(?P<body>.*)$",
    re.IGNORECASE,
)

LIST_PREFIX = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
ID_ENTRY = re.compile(
    r"^(?:\[\s*)?(?P<id>C[1-9]\d*)(?:\s*\])?\s*"
    r"(?P<metadata>(?:\[\s*source(?:(?:\s*[-_]\s*|\s+)ref)?\s*"
    r"[:：]\s*[^\]]+\]\s*)*)"
    r"(?:[:：]|[-–—])\s*(?P<body>.*)$",
    re.IGNORECASE,
)
CLAIM_SOURCE = re.compile(
    r"\[\s*source\s*[:：]\s*(specified|existing-contract|inferred)\s*\]",
    re.IGNORECASE,
)
CLAIM_SOURCE_REF = re.compile(
    r"\[\s*source(?:(?:\s*[-_]\s*|\s+)ref)\s*[:：]\s*(?P<ref>[^\]]+)\]",
    re.IGNORECASE,
)
PRODUCT_DECISION_REQUIRED = re.compile(
    r"\bproduct[-_\s]+decision[-_\s]+required\b",
    re.IGNORECASE,
)
COMPLETION_DECISION = "verified"
DECISION_VALUE = re.compile(
    r"(?:product-decision-required|continue-investigating|continue-fixing|"
    r"runtime-evidence-required|verified)",
    re.IGNORECASE,
)

PLACEHOLDER_ONLY = re.compile(
    r"(?:none|n\s*/?\s*a|unknown|tbd|todo|pending|placeholder|"
    r"not provided|not available|not applicable|same as above|"
    r"无|未知|待定|暂无|未提供|未列出|占位|同上)",
    re.IGNORECASE,
)
NEGATIVE_PROOF = re.compile(
    r"\b(?:not|never)\s+(?:tested|verified|validated|run|executed|checked|inspected)\b|"
    r"\b(?:untested|unverified|unvalidated)\b|"
    r"\bno\s+(?:test(?:s|ing)?(?!\s+(?:failures?|failed))|verification|validation|evidence|checks?)\b|"
    r"\b(?:could not|unable to)\s+(?:test|verify|validate|run|execute|check|inspect)\b|"
    r"(?:未|没有|没|尚未)(?:测试|验证|校验|运行|执行|检查)|"
    r"(?:无|没有)(?:测试|验证|证据|检查)|(?:无法|不能)(?:测试|验证|运行|执行|检查)|待验证",
    re.IGNORECASE,
)

GENERIC_CLAIM = re.compile(
    r"(?:"
    r"(?:the\s+)?(?:fix|bug|change|feature|functionality|behavio(?:u)?r|code|it|everything|[\w-]+)?\s*"
    r"(?:now\s+)?(?:works?|is\s+fixed|is\s+correct|behaves?\s+correctly)"
    r"(?:\s+(?:now|correctly|as\s+expected|for\s+all\s+(?:inputs?|cases?|scenarios?)|without\s+issues?))*"
    r"|(?:handles?|covers?)\s+(?:all\s+)?(?:inputs?|cases?|scenarios?|edge\s+cases?)"
    r"|(?:all|every)\s+(?:inputs?|cases?|paths?|scenarios?|edge\s+cases?)\s+"
    r"(?:work|pass|are\s+(?:handled|covered|fixed))"
    r"|(?:the\s+)?(?:fix|change|feature|functionality|behavio(?:u)?r|implementation|it|everything)\s+"
    r"(?:behaves?|functions?|operates?)\s+(?:correctly|as\s+(?:expected|intended))"
    r"|(?:all\s+(?:cases?|paths?|scenarios?)|everything)\s+(?:is|are)\s+(?:fine|correct|handled|covered)"
    r"|(?:修复|问题|功能|代码|行为)?(?:已经|已|现在)?(?:修复|正常|正确|可用|没问题|工作正常|符合预期)"
    r"|(?:处理|覆盖)了?(?:所有|全部|各种)?(?:输入|情况|场景|边界情况|边缘情况)"
    r"|(?:所有|全部|各种)?(?:输入|情况|场景|边界情况|边缘情况)(?:都)?(?:正常|已处理|通过|已覆盖)"
    r"|(?:一切|所有功能|实现)(?:都)?(?:正常|没问题|符合预期|按预期(?:工作|运行))"
    r"|(?:按预期|正常)(?:工作|运行)"
    r"|(?:the\s+)?(?:implementation|system|code|behavio(?:u)?r|feature|functionality)\s+"
    r"(?:is|seems|appears|remains)\s+(?:amazing|excellent|flawless|perfect|trustworthy)\b"
    r"|(?:returns?|responds?|runs?|executes?)\s+(?:correctly|properly|successfully)$"
    r"|has\s+(?:a|an|the)\s+(?:response|result|value|state|status|behavio(?:u)?r)$"
    r")",
    re.IGNORECASE,
)
GENERIC_ADJECTIVE_CLAIM = re.compile(
    r"(?:"
    r"(?:the\s+)?(?:[\w-]+\s+){1,6}"
    r"(?:is|seems|appears|remains)\s+"
    r"(?:dependable|excellent|fine|good|healthy|okay|ok|proper|resilient|robust|reliable|safe|solid|stable|sound|"
    r"production[-\s]+ready|ready\s+for\s+production)"
    r"|[\u3400-\u9fff]{1,20}(?:很|是|已经|已)?(?:健壮|可靠|安全|稳定|生产可用|可用于生产)"
    r")",
    re.IGNORECASE,
)
SUBJECTIVE_CLAIM_SIGNAL = re.compile(
    r"\b(?:is|are|seems|appears|remains)\s+(?:amazing|awesome|best|better|correct|dependable|"
    r"excellent|fine|flawless|good|great|healthy|nice|okay|ok|perfect|proper|reliable|robust|"
    r"safe|solid|sound|trustworthy|working|production[-\s]+ready)\b|"
    r"(?:很好|完美|优秀|健壮|可靠|安全|稳定|没问题|生产可用|符合预期)",
    re.IGNORECASE,
)
GENERIC_COUNTEREXAMPLE = re.compile(
    r"(?:"
    r"(?:all|any|the|various)?\s*(?:edge\s+cases?|corner\s+cases?|inputs?|cases?|scenarios?)"
    r"(?:\s+(?:were\s+)?(?:considered|covered|tested|handled))?"
    r"|(?:considered|covered|tested|handled)\s+(?:all\s+)?(?:edge\s+cases?|cases?|scenarios?)"
    r"|(?:所有|全部|各种)?(?:边界情况|边缘情况|异常情况|输入|情况|场景)(?:均|都)?(?:已考虑|已覆盖|已测试|已处理)?"
    r"|反例(?:已考虑|已覆盖)?"
    r"|(?:if|when)\s+(?:the\s+)?(?:claim|behavio(?:u)?r|code|implementation|it)\s+"
    r"(?:fails?|is\s+wrong),?\s+(?:the\s+)?counterexample\s+"
    r"(?:disproves?|invalidates?)\s+(?:the\s+claim|it)"
    r"|if\s+something\s+goes\s+wrong,?\s+(?:the\s+)?behavio(?:u)?r\s+is\s+disproved"
    r")",
    re.IGNORECASE,
)
DISPROOF_SIGNAL = re.compile(
    r"\b(?:after|before|crash(?:es|ed)?|disprov(?:e|es|ed)|duplicate|error|fail(?:s|ed)?|"
    r"hidden|if|leav(?:e|es)|missing|remain(?:s|ed)?|render(?:s|ed)?|request(?:s|ed)?|"
    r"retain(?:s|ed)?|return(?:s|ed)?|send(?:s|ing)?|show(?:s|ed)?|stale|still|throw(?:s|ing)?|"
    r"visible|when|wrong|would|start(?:s|ed|ing)?|appl(?:y|ies|ied|ying)|"
    r"select(?:s|ed|ing)?|enter(?:s|ed|ing)?|submit(?:s|ted|ting)?|click(?:s|ed|ing)?|"
    r"open(?:s|ed|ing)?|clos(?:e|es|ed|ing)|reload(?:s|ed|ing)?)\b|"
    r"(?:若|如果|仍|依然|继续|错误|失败|崩溃|残留|保留|显示|返回|请求|发送|推翻|"
    r"旧数据|重复|缺失|开始|选择|输入|提交|点击|打开|关闭|加载|切换|应用)",
    re.IGNORECASE,
)
EVIDENCE_SIGNAL = re.compile(
    r"\b(?:assert(?:ion|ed|s)?|browser|code\s+inspection|diff|fixture|inspection|inspected|"
    r"log|manual\s+check|output|pytest|regression\s+test|reproduced|request|response|runtime|"
    r"screenshot|source|spec|test(?:ed|s|ing)?)\b|"
    r"(?:代码|源码|差异|检查|断言|日志|输出|回归测试|测试|复现|运行时|浏览器|截图|请求|响应)|"
    r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:py|sh|js|jsx|ts|tsx|swift|go|rs|java|kt|rb|php|vue|md)(?::\d+)?",
    re.IGNORECASE,
)
GENERIC_EVIDENCE = re.compile(
    r"(?:"
    r"(?:the\s+)?(?:test(?:s)?|inspection|evidence|verification)(?:\s+(?:all))?\s+"
    r"(?:passed|exists|is\s+present|looks\s+good|confirms\s+it)"
    r"|(?:verified|tested|confirmed)(?:\s+successfully)?"
    r"|(?:测试|检查|验证)(?:已)?(?:通过|成功|完成)|已有证据"
    r")",
    re.IGNORECASE,
)
COMMAND_CHECK = re.compile(
    r"(?:^|[\s`])(?:python(?:3)?|pytest|tox|npx|npm|pnpm|yarn|bun|deno|node|cargo|"
    r"go\s+test|swift\s+test|xcodebuild|make|mvn|gradle|bazel|mix|flutter|rspec|jest|vitest|"
    r"git\s+diff|curl|playwright|cypress|dotnet\s+test|bundle\s+exec|composer|phpunit|rake)\b|"
    r"(?:^|[\s`])(?:\./)?(?:gradlew|mvnw)\b|"
    r"(?:^|[\s`])\./[A-Za-z0-9_./-]+(?=\s|`|$)|"
    r"(?:^|[\s`])(?:\./|/)?[A-Za-z0-9_./-]+\.(?:py|sh|js|ts)(?:\s|`|$)|"
    r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/",
    re.IGNORECASE | re.MULTILINE,
)
RUNTIME_CHECK = re.compile(
    r"\b(?:manual|runtime|browser|ui|api)\s+(?:check|verification|test)\b|"
    r"(?:手动|运行时|浏览器|界面|接口|请求|响应|真机|模拟器)(?:检查|验证|测试)",
    re.IGNORECASE,
)
BEHAVIOR_CHECK = re.compile(
    r"\b(?:check|cypress|curl|pytest|rspec|jest|vitest|spec|test(?:s|ing)?|unittest|"
    r"verif(?:y|ied|ication))\b|"
    r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/|(?:检查|验证|测试|浏览器|运行时|请求|响应)",
    re.IGNORECASE,
)
POSITIVE_RESULT = re.compile(
    r"(?<![A-Za-z0-9_./-])(?-i:PASS)(?=$|[\s:;,!?，。；：]|\.(?![A-Za-z0-9]))|"
    r"(?<![A-Za-z0-9_./-])passed(?=$|[\s:;,!?，。；：]|\.(?![A-Za-z0-9]))|"
    r"(?<![A-Za-z0-9_./-])success(?:ful|fully)?(?=$|[\s:;,!?，。；：]|\.(?![A-Za-z0-9]))|"
    r"(?<![A-Za-z0-9_./-])(?-i:OK)(?=$|[\s:;,!?，。；：]|\.(?![A-Za-z0-9]))|"
    r"\b(?:exit|return)(?:\s+(?:code|status))?\s*[:=]?\s*0\b|"
    r"\b[1-9]\d*\s+(?:tests?\s+)?passed\b|\bstatus\s*[:=]?\s*2\d\d\b|"
    r"(?:通过|成功|退出(?:码|状态)\s*[:：=]?\s*0|返回码\s*[:：=]?\s*0|状态码\s*[:：=]?\s*2\d\d)",
    re.IGNORECASE,
)
NO_CHANGED_FILES_SIGNAL = re.compile(
    r"\bno\s+(?:edits?|changes?)\s+(?:(?:were|are|have\s+been)\s+)?made\b|"
    r"\bno\s+modifications?\s+(?:(?:were|are|have\s+been)\s+)?(?:made|performed)\b|"
    r"\bzero\s+(?:edits?|changes?|modifications?)\b|"
    r"\b(?:the\s+)?working\s+tree\s+(?:is|was|remains?)\s+clean\b|"
    r"\b(?:the\s+)?(?:git\s+)?diff\s+(?:is|was|remains?)\s+empty\b|"
    r"\bempty\s+(?:git\s+)?diff\b|"
    r"\bno\s+(?:(?:code|source|tracked|modified|changed)\s+)?(?:files?|paths?)\s+"
    r"(?:(?:were|are|have\s+been)\s+)?(?:changed|modified|updated)\b|"
    r"\b(?:0|zero)\s+(?:(?:code|source|tracked)\s+)?(?:files?|paths?)\s+"
    r"(?:(?:were|are|have\s+been)\s+)?(?:changed|modified|updated)\b|"
    r"\bnone\s+of\s+(?:the\s+)?(?:(?:code|source|tracked)\s+)?(?:files?|paths?)\s+"
    r"(?:(?:were|are|have\s+been)\s+)?(?:changed|modified|updated)\b|"
    r"\b(?:files?|paths?)\s+(?:changed|modified|updated)\s*[:=]\s*(?:none|zero|0)\b|"
    r"\bno\s+(?:file|path)\s+changes?\s+(?:were|are|have\s+been)\s+made\b|"
    r"\b(?:repository\s+)?(?:sources?|files?|paths?)\s+"
    r"(?:remain|remained|are|were)\s+(?:untouched|unmodified)\b|"
    r"\b(?:was|were)\s+(?:only|merely)\s+(?:reviewed|inspected|read|examined)\b|"
    r"\bnothing\s+(?:was\s+|has\s+been\s+)?(?:changed|modified|updated)\b|"
    r"\bno\s+changes?\s+(?:were\s+made\s+)?to\s+(?:any\s+)?(?:files?|paths?)\b|"
    r"\bwithout\s+(?:any\s+)?(?:file|path)\s+changes?\b|"
    r"(?:没有|无|未有|不存在)(?:任何)?(?:代码|源码|源代码|已跟踪)?(?:文件|路径)(?:改动|变更|修改)|"
    r"0\s*个?(?:代码|源码|源代码|已跟踪)?(?:文件|路径)(?:改动|变更|修改)|"
    r"(?:本次)?未修改任何文件|没有进行[^，。；\n]{0,20}(?:代码)?修改|"
    r"工作区[^，。；\n]{0,10}干净|零(?:文件)?改动",
    re.IGNORECASE,
)
FILE_SCOPE_SIGNAL = re.compile(
    r"(?:^|[\s`'\"(])(?:\.{1,2}/|/)?(?:[A-Za-z0-9_.\-\u3400-\u9fff]+/)+"
    r"[A-Za-z0-9_.\-\u3400-\u9fff]+(?:\.[A-Za-z0-9_.\-\u3400-\u9fff]+)?"
    r"(?=$|[\s`'\",;:)])|"
    r"\b[A-Za-z_\u3400-\u9fff][A-Za-z0-9_.\-\u3400-\u9fff]*\."
    r"[A-Za-z\u3400-\u9fff][A-Za-z0-9_\-\u3400-\u9fff]{0,20}\b|"
    r"(?:^|\s)\./[A-Za-z0-9_.\-\u3400-\u9fff]+(?=$|[\s,;:)])|"
    r"(?:^|\s)\.[A-Za-z0-9_.-]+(?:\s|$)|"
    r"\b(?:Dockerfile|Makefile|Gemfile|Rakefile|Procfile|gradlew)\b|"
    r"(?:^|\s)(?-i:BUILD|WORKSPACE|LICENSE|NOTICE|COPYING|AUTHORS|CHANGELOG|VERSION|"
    r"CODEOWNERS|Jenkinsfile|gradlew|mvnw)(?=$|[\s,;:)])",
    re.IGNORECASE | re.MULTILINE,
)
NON_FILE_SCOPE_TOKEN = re.compile(
    r"\b[A-Za-z][A-Za-z0-9+.-]*://\S+|\bwww\.\S+|"
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
SCOPED_UNCHANGED_SIGNAL = re.compile(
    r"\b(?:generated|derived|companion|unrelated)\s+(?:files?|paths?)\s+"
    r"(?:remain|remained|are|were)\s+(?:unchanged|untouched|unmodified)\b",
    re.IGNORECASE,
)
EXPLICIT_CHANGED_PATH_SIGNAL = re.compile(
    r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+(?:\.[A-Za-z0-9_.-]+)?\s*"
    r"(?:[-–—:()]\s*)?(?:changed|modified|updated|added|deleted|created|renamed)\b|"
    r"\b(?:changed|modified|updated|added|deleted|created|renamed)\s*[:：–—-]\s*"
    r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+(?:\.[A-Za-z0-9_.-]+)?",
    re.IGNORECASE,
)
CONTEXT_SOURCE_SIGNAL = re.compile(
    r"\b(?:build-bug-context|git\s+diff|manual\s+diff|manual\s+inspection|explicit\s+files?|"
    r"user-provided|context\s+pack)\b|(?:手动|人工)(?:差异|检查|审查)|"
    r"(?:显式|指定)文件|用户提供|上下文包",
    re.IGNORECASE,
)
NEGATIVE_CHECK_RESULT = re.compile(
    r"\b(?:did|does|do)(?:\s+not|n['’]?t)\s+(?:pass|succeed)\b|\bnot\s+(?:ok|successful)\b|"
    r"\b(?:was|were|has|have|had)\s+not\s+passed\b|\bnever\s+passed\b|"
    r"\b(?:cannot|can['’]?t)\s+pass\b|"
    r"\b(?:result|status)\s*[:=]\s*(?:fail(?:ed|ure)?|error|skipped)\b|"
    r"\b(?:tests?|checks?|verification|command|suite|assertion)\s+"
    r"(?:was\s+|were\s+)?(?:failed|skipped)\b|"
    r"\b(?:failed|skipped)\s+(?:tests?|checks?|verification|command|suite|assertion)\b|"
    r"\b[1-9]\d*\s+(?:tests?\s+)?failed\b|"
    r"\b[1-9]\d*\s+(?:(?:tests?|checks?|assertions?)\s+)?(?:errors?|failures?)\b|"
    r"\b[1-9]\d*\s+(?:tests?|checks?|assertions?)\s+(?:errored|failed)\b|"
    r"\b(?:errors?|failures?)\s*[:=]\s*[1-9]\d*\b|"
    r"\b(?:error|failure)\s+count\s*[:=]\s*[1-9]\d*\b|"
    r"\b(?:completed|ended|finished)\s+with\s+(?:an?\s+)?(?:error|failure)\b|"
    r"\b(?:completed|ended|finished)\s+unsuccessfully\b|"
    r"\bunsuccessful(?:ly)?\b|"
    r"\b(?:terminated|exited|returned|completed|ended|finished)\s+with\s+"
    r"(?:(?:exit|return)\s+)?(?:code|status)\s*[:=]?\s*[1-9]\d*\b|"
    r"\b(?:returned|exited)\s+(?:with\s+)?[1-9]\d*\b|"
    r"\b(?:exit|return)\s+(?:code|status)\s+(?:was\s+)?[1-9]\d*\b|"
    r"\b(?:exit|return)(?:\s+(?:code|status))?\s*[:=]?\s*[1-9]\d*\b|"
    r"\b(?:crash(?:ed)?|abort(?:ed)?|timed\s+out|timeout|was\s+killed|killed|"
    r"segfault(?:ed)?|panic(?:ked)?)\b|"
    r"(?:结果|状态)\s*[:：=]\s*(?:失败|错误|未通过)|"
    r"(?:测试|检查|验证|命令)(?:已|被)?(?:失败|跳过|未通过)|"
    r"(?:测试|检查|验证|命令)?(?:没有|没能|未能|不|尚未)通过|"
    r"(?:退出码|返回码)\s*[:：=]?\s*[1-9]\d*",
    re.IGNORECASE,
)
FAIL_RESULT_MARKER = re.compile(
    r"(?<![A-Za-z0-9_./-])(?-i:FAIL(?:ED)?)(?![A-Za-z0-9_./-])",
)
EXPECTED_NONZERO_OUTCOME = re.compile(
    r"(?:expected|assert(?:ed|ing)?|verif(?:ied|ying)?)[^.;\n]{0,120}"
    r"\b(?:exit|return)(?:\s+(?:code|status))?\s*[:=]?\s*[1-9]\d*\b|"
    r"observ(?:ed|ing)?[^.;\n]{0,80}\bexpected\b[^.;\n]{0,60}"
    r"\b(?:exit|return)(?:\s+(?:code|status))?\s*[:=]?\s*[1-9]\d*\b|"
    r"\b(?:exit|return)(?:\s+(?:code|status))?\s*[:=]?\s*[1-9]\d*\b"
    r"[^.;\n]{0,60}\b(?:as\s+expected|was\s+expected)\b",
    re.IGNORECASE,
)
EXPECTED_FAIL_OUTCOME = re.compile(
    r"(?:expected|assert(?:ed|ing)?|verif(?:ied|ying)?)[^.;\n]{0,120}"
    r"(?<![A-Za-z0-9_./-])FAIL(?:ED)?(?![A-Za-z0-9_./-])|"
    r"observ(?:ed|ing)?[^.;\n]{0,80}\bexpected\b[^.;\n]{0,60}"
    r"(?<![A-Za-z0-9_./-])FAIL(?:ED)?(?![A-Za-z0-9_./-])|"
    r"(?<![A-Za-z0-9_./-])FAIL(?:ED)?(?![A-Za-z0-9_./-])[^.;\n]{0,60}"
    r"\b(?:as\s+expected|was\s+expected)\b",
    re.IGNORECASE,
)
BUSINESS_ERROR_STATUS = re.compile(
    r"\b(?:api|http|payload|request|response|response\s+body)\b[^.;\n]{0,60}"
    r"\b(?:result|status)\s*[:=]\s*(?:error|fail(?:ed|ure)?|skipped)\b|"
    r"(?:接口|请求|响应|载荷|返回体)[^；。\n]{0,40}(?:结果|状态)\s*[:：=]\s*"
    r"(?:失败|错误|未通过)|"
    r"\b(?:result|status)\s*[:=]\s*(?:error|fail(?:ed|ure)?|skipped)\b"
    r"[^.;\n]{0,60}\b(?:api|http|payload|request|response|response\s+body)\b",
    re.IGNORECASE,
)
ZERO_FAILED_COUNT = re.compile(
    r"\b0\s+(?:(?:tests?|checks?|assertions?)\s+)?failed\b",
    re.IGNORECASE,
)
ZERO_PASSED_COUNT = re.compile(
    r"\b0\s+(?:(?:tests?|checks?|assertions?)\s+)?passed\b",
    re.IGNORECASE,
)
FENCE_START = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
SOURCE_REF_KIND = re.compile(
    r"^(?:user(?:\s+(?:request|wording|quote))?|accepted\s+requirement|requirement|"
    r"acceptance\s+criteria|ticket|issue|file|test|spec|api|schema|contract|design|"
    r"current\s+behavio(?:u)?r|explicit\s+assumption|assumption|"
    r"用户(?:原句|需求|要求)?|需求(?:原文|说明)?|验收标准|工单|问题单|文件|测试|"
    r"规范|接口|模式|契约|设计|现有行为|明确假设|假设|推断)",
    re.IGNORECASE,
)
SPECIFIED_SOURCE_REF = re.compile(
    r"^(?:user(?:\s+(?:request|wording|quote))?|accepted\s+requirement|requirement|"
    r"acceptance\s+criteria|ticket|issue|用户(?:原句|需求|要求)?|需求(?:原文|说明)?|"
    r"验收标准|工单|问题单)",
    re.IGNORECASE,
)
CONTRACT_SOURCE_REF = re.compile(
    r"^(?:file|test|spec|api|schema|contract|design|current\s+behavio(?:u)?r|"
    r"文件|测试|规范|接口|模式|契约|设计|现有行为)",
    re.IGNORECASE,
)
INFERRED_SOURCE_REF = re.compile(
    r"^(?:explicit\s+assumption|assumption|inference|明确假设|假设|推断)",
    re.IGNORECASE,
)
SOURCE_REF_ARTIFACT = re.compile(
    r"(?:[A-Za-z0-9_.\-\u3400-\u9fff]+/)+[A-Za-z0-9_.\-\u3400-\u9fff]+"
    r"(?:\.[A-Za-z0-9\u3400-\u9fff]+)?(?::\d+)?|"
    r"\b[A-Za-z_\u3400-\u9fff][A-Za-z0-9_.\-\u3400-\u9fff]*\."
    r"[A-Za-z\u3400-\u9fff][A-Za-z0-9_\-\u3400-\u9fff]{0,20}(?::\d+)?\b|"
    r"(?:^|\s)\./[A-Za-z0-9_.\-\u3400-\u9fff]+(?::\d+)?(?=$|[\s,;:)])|"
    r"\b(?-i:BUILD|WORKSPACE|LICENSE|NOTICE|COPYING|AUTHORS|CHANGELOG|VERSION|"
    r"CODEOWNERS|Jenkinsfile|gradlew|mvnw)(?::\d+)?\b|"
    r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/\S+|"
    r"\b[A-Z][A-Z0-9]+-\d+\b|"
    r"\b[A-Za-z_$][A-Za-z0-9_$]*(?:Test|Spec|Contract|Schema)\b",
    re.IGNORECASE,
)
GENERIC_SOURCE_REF_DETAIL = re.compile(
    r"(?:current|existing|the|this)?\s*(?:implementation|code|file|source|behavior|behaviour)",
    re.IGNORECASE,
)
UNEXPLAINED_NO_RISK = re.compile(
    r"(?:no\s+(?:remaining\s+)?risks?|no\s+risks?\s+remain|zero\s+(?:remaining\s+)?risks?)",
    re.IGNORECASE,
)


def read_report(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def normalized_text(text: str) -> str:
    text = re.sub(r"[`*_~#]", "", text)
    return re.sub(r"\s+", " ", text).strip(" \t\r\n-–—:：;；,.，。")


def has_content(text: str) -> bool:
    return bool(re.search(r"[A-Za-z0-9\u3400-\u9fff]", normalized_text(text)))


def is_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER_ONLY.fullmatch(normalized_text(text)))


def has_changed_path_line(text: str) -> bool:
    for line in text.splitlines():
        if not FILE_SCOPE_SIGNAL.search(line):
            continue
        if SCOPED_UNCHANGED_SIGNAL.search(line) or NO_CHANGED_FILES_SIGNAL.search(line):
            continue
        if re.search(
            r"\b(?:only|merely)\s+(?:reviewed|inspected|read|examined)\b|"
            r"(?:仅|只)(?:检查|审查|查看|阅读)",
            line,
            re.IGNORECASE,
        ):
            continue
        return True
    return False


def parse_sections(text: str) -> tuple[dict[str, str], list[str]]:
    section_lines: dict[str, list[str]] = {}
    duplicate_sections: list[str] = []
    current: str | None = None
    fence_character: str | None = None
    fence_length = 0

    for line in text.splitlines():
        if fence_character is not None:
            closing_fence = re.compile(
                rf"^\s{{0,3}}{re.escape(fence_character)}{{{fence_length},}}\s*$"
            )
            if closing_fence.match(line):
                fence_character = None
                fence_length = 0
            if current is not None:
                section_lines[current].append(line)
            continue

        fence_match = FENCE_START.match(line)
        if fence_match:
            marker = fence_match.group("marker")
            fence_character = marker[0]
            fence_length = len(marker)
            if current is not None:
                section_lines[current].append(line)
            continue

        match = SECTION_HEADING.match(line)
        if match:
            current = ALIAS_TO_SECTION[match.group("heading").casefold()]
            if current in section_lines:
                duplicate_sections.append(current)
            else:
                section_lines[current] = []
            inline_body = match.group("body").strip()
            if inline_body:
                section_lines[current].append(inline_body)
            continue
        if current is not None:
            section_lines[current].append(line)

    return (
        {section: "\n".join(lines).strip() for section, lines in section_lines.items()},
        duplicate_sections,
    )


def parse_id_entries(section: str) -> tuple[dict[str, list[str]], list[str]]:
    entries: dict[str, list[str]] = {}
    orphan_lines: list[str] = []
    current_id: str | None = None

    for raw_line in section.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        had_list_prefix = bool(LIST_PREFIX.match(stripped))
        candidate = LIST_PREFIX.sub("", stripped, count=1)
        candidate = candidate.replace("**", "").replace("__", "").strip()
        match = ID_ENTRY.match(candidate)
        if match:
            current_id = match.group("id").upper()
            body = match.group("body").strip()
            metadata = match.group("metadata").strip()
            if metadata:
                body = f"{metadata} {body}".strip()
            entries.setdefault(current_id, []).append(body)
            continue
        if current_id is None or had_list_prefix:
            orphan_lines.append(stripped)
            current_id = None
            continue
        entries[current_id][-1] = f"{entries[current_id][-1]}\n{stripped}".strip()

    return entries, orphan_lines


def entry_is_too_short(text: str) -> bool:
    compact = re.sub(r"[^A-Za-z0-9\u3400-\u9fff]", "", normalized_text(text))
    return len(compact) < 6


def section_is_too_short(text: str) -> bool:
    compact = re.sub(r"[^A-Za-z0-9\u3400-\u9fff]", "", normalized_text(text))
    return len(compact) < 8


def source_ref_is_concrete(source_ref: str) -> bool:
    cleaned = normalized_text(source_ref)
    if SOURCE_REF_ARTIFACT.search(source_ref):
        return True
    compact = re.sub(r"[^A-Za-z0-9\u3400-\u9fff]", "", cleaned)
    if len(compact) < 8 or is_placeholder(cleaned):
        return False

    kind = SOURCE_REF_KIND.match(cleaned)
    if kind is None:
        return False
    detail = cleaned[kind.end() :].strip(" \t:：=-–—'\"")
    detail_compact = re.sub(r"[^A-Za-z0-9\u3400-\u9fff]", "", detail)
    return (
        len(detail_compact) >= 6
        and not is_placeholder(detail)
        and not GENERIC_SOURCE_REF_DETAIL.fullmatch(detail)
    )


def source_ref_category(source_ref: str) -> str | None:
    cleaned = normalized_text(source_ref)
    if INFERRED_SOURCE_REF.match(cleaned):
        return "inferred"
    if SPECIFIED_SOURCE_REF.match(cleaned):
        return "specified"
    if CONTRACT_SOURCE_REF.match(cleaned) or SOURCE_REF_ARTIFACT.search(source_ref):
        return "existing-contract"
    return None


def has_negative_result(text: str) -> bool:
    masked_expected_outcomes = EXPECTED_NONZERO_OUTCOME.sub(" expected nested outcome ", text)
    masked_expected_outcomes = EXPECTED_FAIL_OUTCOME.sub(
        " expected nested failure marker ", masked_expected_outcomes
    )
    masked_expected_outcomes = BUSINESS_ERROR_STATUS.sub(
        " expected business error outcome ", masked_expected_outcomes
    )
    without_zero_failures = ZERO_FAILED_COUNT.sub("", masked_expected_outcomes)
    return bool(
        FAIL_RESULT_MARKER.search(without_zero_failures)
        or NEGATIVE_CHECK_RESULT.search(without_zero_failures)
    )


def has_positive_result(text: str) -> bool:
    return bool(POSITIVE_RESULT.search(ZERO_PASSED_COUNT.sub("", text)))


def validate_id_section(section_name: str, text: str) -> tuple[dict[str, list[str]], list[str]]:
    entries, orphan_lines = parse_id_entries(text)
    issues: list[str] = []
    if not entries:
        issues.append(f"{section_name}: expected entries labeled with stable IDs such as C1")
    if orphan_lines:
        issues.append(f"{section_name}: every item must start with its claim ID")

    for claim_id, bodies in entries.items():
        if section_name == "behavior claims" and len(bodies) > 1:
            issues.append(f"behavior claims: duplicate claim ID {claim_id}")
        for body in bodies:
            if not has_content(body) or is_placeholder(body):
                issues.append(f"{section_name}: {claim_id} is empty or a placeholder")
                continue
            if section_name == "behavior claims":
                sources = CLAIM_SOURCE.findall(body)
                if len(sources) != 1:
                    issues.append(
                        f"behavior claims: {claim_id} must include exactly one "
                        "[source: specified|existing-contract|inferred] tag"
                    )
                source_refs = CLAIM_SOURCE_REF.findall(body)
                if len(source_refs) != 1:
                    issues.append(
                        f"behavior claims: {claim_id} must include exactly one concrete "
                        "[source-ref: ...]"
                    )
                elif not source_ref_is_concrete(source_refs[0]):
                    issues.append(
                        f"behavior claims: {claim_id} source-ref must quote the user, name a "
                        "file/test/API/contract, or state an explicit assumption"
                    )
                elif len(sources) == 1:
                    ref_category = source_ref_category(source_refs[0])
                    if ref_category is not None and ref_category != sources[0].casefold():
                        issues.append(
                            f"behavior claims: {claim_id} source tag {sources[0]} conflicts "
                            f"with its {ref_category} source-ref"
                        )
                claim_text = CLAIM_SOURCE_REF.sub("", CLAIM_SOURCE.sub("", body))
                if entry_is_too_short(claim_text):
                    issues.append(f"behavior claims: {claim_id} is too vague to lint")
                    continue
                if PRODUCT_DECISION_REQUIRED.search(claim_text):
                    issues.append(
                        f"behavior claims: {claim_id} cannot use product-decision-required as a passing claim"
                    )
                normalized_claim = normalized_text(claim_text)
                if (
                    GENERIC_CLAIM.search(normalized_claim)
                    or GENERIC_ADJECTIVE_CLAIM.fullmatch(normalized_claim)
                    or SUBJECTIVE_CLAIM_SIGNAL.search(normalized_claim)
                ):
                    issues.append(f"behavior claims: {claim_id} is generic rather than observable")
            elif section_name == "counterexamples considered":
                if entry_is_too_short(body):
                    issues.append(f"counterexamples considered: {claim_id} is too vague to lint")
                    continue
                if GENERIC_COUNTEREXAMPLE.fullmatch(normalized_text(body)):
                    issues.append(f"counterexamples: {claim_id} is generic rather than a concrete disproof case")
                elif not DISPROOF_SIGNAL.search(body):
                    issues.append(
                        f"counterexamples: {claim_id} must name a concrete state, input, or disproof outcome"
                    )
            elif section_name == "evidence":
                if entry_is_too_short(body):
                    issues.append(f"evidence: {claim_id} is too vague to lint")
                    continue
                if NEGATIVE_PROOF.search(body):
                    issues.append(f"evidence: {claim_id} says verification was not performed")
                if has_negative_result(body):
                    issues.append(
                        f"evidence: {claim_id} contains a failing, skipped, or negative result"
                    )
                generic_evidence = normalized_text(POSITIVE_RESULT.sub("", body))
                if GENERIC_EVIDENCE.fullmatch(normalized_text(body)) or re.fullmatch(
                    r"(?:the\s+)?(?:(?:focused|regression|unit|integration)\s+)?"
                    r"(?:test|tests|inspection|verification|evidence)(?:\s+result)?",
                    generic_evidence,
                    re.IGNORECASE,
                ):
                    issues.append(f"evidence: {claim_id} is generic rather than a concrete artifact or observation")
                elif not EVIDENCE_SIGNAL.search(body):
                    issues.append(f"evidence: {claim_id} must name a concrete inspection or executed artifact")
                if not has_positive_result(body):
                    issues.append(
                        f"evidence: {claim_id} must include its own explicit positive result "
                        "such as PASS, passed, exit 0, or HTTP 2xx"
                    )

    return entries, issues


def validate_id_correspondence(
    claim_ids: set[str],
    related_ids: set[str],
    section_name: str,
) -> list[str]:
    issues: list[str] = []
    missing_ids = sorted(claim_ids - related_ids)
    extra_ids = sorted(related_ids - claim_ids)
    if missing_ids:
        issues.append(f"{section_name}: missing claim IDs {', '.join(missing_ids)}")
    if extra_ids:
        issues.append(f"{section_name}: unknown claim IDs {', '.join(extra_ids)}")
    return issues


def split_check_entries(text: str) -> list[str]:
    entries: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if LIST_PREFIX.match(stripped):
            if current:
                entries.append("\n".join(current))
            current = [LIST_PREFIX.sub("", stripped, count=1)]
        elif current:
            current.append(stripped)
        else:
            current = [stripped]
    if current:
        entries.append("\n".join(current))
    return entries


def runtime_check_has_detail(text: str) -> bool:
    residue = RUNTIME_CHECK.sub("", normalized_text(text))
    residue = POSITIVE_RESULT.sub("", residue)
    residue = re.sub(r"\b(?:result|status)\b|(?:结果|状态)", "", residue, flags=re.IGNORECASE)
    compact = re.sub(r"[^A-Za-z0-9\u3400-\u9fff]", "", residue)
    return len(compact) >= 10


def validate_checks(text: str) -> list[str]:
    issues: list[str] = []
    if is_placeholder(text):
        return ["checks run: placeholder values such as none are not executed checks"]
    entries = split_check_entries(text)
    has_behavior_check = False
    for index, entry in enumerate(entries, start=1):
        prefix = f"checks run: entry {index}"
        if is_placeholder(entry):
            issues.append(f"{prefix} is a placeholder rather than an executed check")
            continue
        if NEGATIVE_PROOF.search(entry):
            issues.append(f"{prefix} says the check was not performed")
        if has_negative_result(entry):
            issues.append(f"{prefix} contains a failing or non-zero result")
        command_match = COMMAND_CHECK.search(entry)
        runtime_match = RUNTIME_CHECK.search(entry)
        normalized_entry = normalized_text(entry)
        behavior_match = BEHAVIOR_CHECK.search(normalized_entry)
        diff_check_only = bool(
            re.search(r"\bgit\s+diff\b.*--check\b", normalized_entry, re.IGNORECASE)
        )
        expected_rejection_check = bool(command_match and EXPECTED_NONZERO_OUTCOME.search(entry))
        if runtime_match or expected_rejection_check or (behavior_match and not diff_check_only):
            has_behavior_check = True
        if not command_match and not runtime_match:
            issues.append(f"{prefix} must name a concrete command or manual runtime check")
        elif runtime_match and not command_match and not runtime_check_has_detail(entry):
            issues.append(f"{prefix} must describe the runtime path and observed outcome")
        if not has_positive_result(entry):
            issues.append(f"{prefix} must include an explicit positive result marker such as PASS or exit 0")
    if entries and not has_behavior_check:
        issues.append("checks run: lint, typecheck, build, format, or diff-only checks cannot prove behavior")
    return issues


def deduplicate(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", help="Path to a final proof report. Reads stdin when omitted.")
    args = parser.parse_args()

    try:
        text = read_report(args.report)
    except (OSError, UnicodeError) as exc:
        print(f"FAIL: could not read completion proof report: {exc}")
        return 2

    sections, duplicate_sections = parse_sections(text)
    issues = [f"duplicate section heading: {section}" for section in duplicate_sections]

    for section in REQUIRED_SECTIONS:
        if section not in sections:
            issues.append(f"missing section: {section}")
            continue
        if not has_content(sections[section]):
            issues.append(f"empty section: {section}")
        elif is_placeholder(sections[section]):
            if section == "remaining risks":
                issues.append(
                    "remaining risks: name the unverified cases or explain why none remain after evidence"
                )
            else:
                issues.append(f"placeholder section: {section}")
        elif section in {"root cause", "context source", "remaining risks"}:
            if section_is_too_short(sections[section]):
                issues.append(f"{section}: content is too vague to lint")

    changed_files = sections.get("changed files", "")
    has_scoped_unchanged = SCOPED_UNCHANGED_SIGNAL.search(changed_files)
    has_explicit_changed_path = bool(
        EXPLICIT_CHANGED_PATH_SIGNAL.search(changed_files) or has_changed_path_line(changed_files)
    )
    if has_content(changed_files) and NON_FILE_SCOPE_TOKEN.search(changed_files):
        issues.append("changed files: URLs and email addresses are not concrete file paths")
    elif has_content(changed_files) and (
        NO_CHANGED_FILES_SIGNAL.search(changed_files)
        or (has_scoped_unchanged and not has_explicit_changed_path)
    ):
        issues.append(
            "changed files: a no-change statement cannot be used in a post-change completion proof"
        )
    elif has_content(changed_files) and not FILE_SCOPE_SIGNAL.search(changed_files):
        issues.append(
            "changed files: a post-change completion proof must list at least one concrete changed or explicit path"
        )
    decision = normalized_text(sections.get("decision", ""))
    if has_content(decision):
        if not DECISION_VALUE.fullmatch(decision):
            issues.append(
                "decision: use exactly one workflow label: product-decision-required, "
                "continue-investigating, continue-fixing, runtime-evidence-required, or verified"
            )
        elif decision.casefold() != COMPLETION_DECISION:
            issues.append(
                "decision: a passing post-change completion proof must use verified; "
                f"{decision} is not a completion decision"
            )
    context_source = sections.get("context source", "")
    if has_content(context_source) and not CONTEXT_SOURCE_SIGNAL.search(context_source):
        issues.append("context source: name the context pack, diff inspection, explicit files, or user report")
    remaining_risks = normalized_text(sections.get("remaining risks", ""))
    if UNEXPLAINED_NO_RISK.fullmatch(remaining_risks):
        issues.append(
            "remaining risks: explain why none remain after the listed evidence instead of only asserting no risk"
        )

    claims: dict[str, list[str]] = {}
    counterexamples: dict[str, list[str]] = {}
    evidence: dict[str, list[str]] = {}
    if has_content(sections.get("behavior claims", "")):
        claims, claim_issues = validate_id_section("behavior claims", sections["behavior claims"])
        issues.extend(claim_issues)
    if has_content(sections.get("counterexamples considered", "")):
        counterexamples, counterexample_issues = validate_id_section(
            "counterexamples considered", sections["counterexamples considered"]
        )
        issues.extend(counterexample_issues)
    if has_content(sections.get("evidence", "")):
        evidence, evidence_issues = validate_id_section("evidence", sections["evidence"])
        issues.extend(evidence_issues)

    claim_ids = set(claims)
    issues.extend(
        validate_id_correspondence(claim_ids, set(counterexamples), "counterexamples")
    )
    issues.extend(validate_id_correspondence(claim_ids, set(evidence), "evidence"))

    if has_content(sections.get("checks run", "")):
        issues.extend(validate_checks(sections["checks run"]))

    issues = deduplicate(issues)
    if issues:
        print("FAIL: completion proof report contract violations:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("PASS: completion proof report contract satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
