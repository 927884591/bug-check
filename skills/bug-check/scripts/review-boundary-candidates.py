#!/usr/bin/env python3
"""Record and review manual bug-boundary candidates without loading them by default."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_STORE = Path(".bug-check") / "manual-boundaries.jsonl"
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class Candidate:
    mechanism_key: str
    family: str
    failed_invariant: str
    severity: str
    triggers: tuple[str, ...]
    changed_path_shapes: tuple[str, ...]
    missing_handling: str
    verification: str
    suggested_action: str
    observed_at: str


def slug(value: str) -> str:
    lowered = value.strip().lower()
    replaced = re.sub(r"[^a-z0-9]+", "-", lowered)
    return replaced.strip("-")[:96] or "manual-boundary"


def mechanism_key(family: str, failed_invariant: str) -> str:
    return slug(f"{family}-{failed_invariant}")


def split_values(values: list[str]) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        for item in value.split(","):
            stripped = item.strip()
            if stripped and stripped not in output:
                output.append(stripped)
    return tuple(output)


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    if not path.exists():
        return [], 0

    records: list[dict[str, Any]] = []
    invalid = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            invalid += 1
            continue
        if isinstance(value, dict):
            records.append(value)
        else:
            invalid += 1
    return records, invalid


def candidate_from_record(record: dict[str, Any]) -> Candidate | None:
    family = str(record.get("family") or record.get("boundary_family") or "").strip()
    failed_invariant = str(record.get("failed_invariant") or "").strip()
    if not family or not failed_invariant:
        return None

    key = str(record.get("mechanism_key") or mechanism_key(family, failed_invariant)).strip()
    severity = str(record.get("severity") or "medium").strip().lower()
    if severity not in SEVERITY_RANK:
        severity = "medium"

    return Candidate(
        mechanism_key=key,
        family=family,
        failed_invariant=failed_invariant,
        severity=severity,
        triggers=tuple(record.get("triggers") or record.get("signals") or ()),
        changed_path_shapes=tuple(record.get("changed_path_shapes") or ()),
        missing_handling=str(record.get("missing_handling") or "").strip(),
        verification=str(record.get("verification") or "").strip(),
        suggested_action=str(record.get("suggested_action") or "keep-candidate").strip(),
        observed_at=str(record.get("observed_at") or record.get("date") or "").strip(),
    )


def write_record(args: argparse.Namespace) -> int:
    family = args.family.strip()
    failed_invariant = args.failed_invariant.strip()
    key = args.mechanism_key or mechanism_key(family, failed_invariant)
    record = {
        "schema_version": 1,
        "observed_at": args.observed_at or date.today().isoformat(),
        "mechanism_key": key,
        "family": family,
        "failed_invariant": failed_invariant,
        "severity": args.severity,
        "triggers": split_values(args.trigger),
        "changed_path_shapes": split_values(args.changed_path_shape),
        "missing_handling": args.missing_handling.strip(),
        "verification": args.verification.strip(),
        "suggested_action": args.suggested_action,
    }

    store = Path(args.store)
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        handle.write("\n")

    print(f"Recorded manual boundary candidate: {key}")
    print(f"Store: {store}")
    return 0


def recommendation(candidates: list[Candidate], promote_count: int, merge_count: int) -> str:
    max_severity = max(SEVERITY_RANK[item.severity] for item in candidates)
    if max_severity >= SEVERITY_RANK["high"]:
        return "review now: high-severity boundary can justify promotion after one clear mechanism"
    if len(candidates) >= promote_count:
        return "promote or merge: repeated mechanism reached promotion threshold"
    if len(candidates) >= merge_count:
        return "merge if covered by an existing card; promote only if the mechanism is distinct"
    return "keep as candidate: needs more recurrence or higher risk"


def ranked_groups(candidates: list[Candidate]) -> list[list[Candidate]]:
    groups: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        groups[candidate.mechanism_key].append(candidate)

    return sorted(
        groups.values(),
        key=lambda items: (
            max(SEVERITY_RANK[item.severity] for item in items),
            len(items),
            items[-1].observed_at,
        ),
        reverse=True,
    )


def print_group(index: int, candidates: list[Candidate], promote_count: int, merge_count: int) -> None:
    first = candidates[0]
    severities = [item.severity for item in candidates]
    max_severity = max(severities, key=lambda item: SEVERITY_RANK[item])
    family_counts = Counter(item.family for item in candidates)
    trigger_counts = Counter(trigger for item in candidates for trigger in item.triggers)
    dates = sorted({item.observed_at for item in candidates if item.observed_at})
    latest = candidates[-1]

    print(f"{index}. {first.mechanism_key}")
    print(f"   count: {len(candidates)}")
    print(f"   max severity: {max_severity}")
    print(f"   families: {', '.join(family_counts)}")
    if trigger_counts:
        print(f"   triggers: {', '.join(item for item, _ in trigger_counts.most_common(8))}")
    if dates:
        print(f"   evidence dates: {', '.join(dates[-5:])}")
    print(f"   failed invariant: {first.failed_invariant}")
    if latest.missing_handling:
        print(f"   latest missing handling: {latest.missing_handling}")
    if latest.verification:
        print(f"   latest verification: {latest.verification}")
    print(f"   recommendation: {recommendation(candidates, promote_count, merge_count)}")
    print()


def review_records(args: argparse.Namespace) -> int:
    store = Path(args.store)
    raw_records, invalid_json = load_jsonl(store)
    candidates = [candidate for record in raw_records if (candidate := candidate_from_record(record))]
    invalid_records = len(raw_records) - len(candidates)

    ranked = ranked_groups(candidates)

    print("Manual Boundary Candidate Review")
    print(f"Source: {store}")
    print(f"Records read: {len(raw_records)}")
    print(f"Invalid records skipped: {invalid_json + invalid_records}")
    print(f"Groups: {len(ranked)}")
    print()
    print("Promotion policy:")
    print("- high or critical severity: review after one clear reusable mechanism")
    print(f"- repeated ordinary mechanism: review at {args.merge_count} occurrences, promote at {args.promote_count}")
    print("- prefer updating an existing boundary card when 1-3 focused lines cover the mechanism")
    print("- do not promote business-specific cases without a reusable failed invariant")
    print()

    if not ranked:
        print("Top candidates:")
        print("- none")
        return 0

    print("Top candidates:")
    for index, items in enumerate(ranked[: args.limit], start=1):
        print_group(index, items, args.promote_count, args.merge_count)
    return 0


def recommended_action(candidates: list[Candidate], promote_count: int, merge_count: int) -> str:
    latest = candidates[-1]
    if latest.suggested_action in {"merge-into-existing-card", "promote-new-card"}:
        return latest.suggested_action
    max_severity = max(SEVERITY_RANK[item.severity] for item in candidates)
    if max_severity >= SEVERITY_RANK["high"] or len(candidates) >= promote_count:
        return "promote-new-card"
    if len(candidates) >= merge_count:
        return "merge-into-existing-card"
    return "keep-candidate"


def plan_records(args: argparse.Namespace) -> int:
    store = Path(args.store)
    raw_records, invalid_json = load_jsonl(store)
    candidates = [candidate for record in raw_records if (candidate := candidate_from_record(record))]
    invalid_records = len(raw_records) - len(candidates)
    ranked = ranked_groups(candidates)

    selected: list[Candidate] | None = None
    if args.mechanism_key:
        for group in ranked:
            if group[0].mechanism_key == args.mechanism_key:
                selected = group
                break
    elif ranked:
        selected = ranked[0]

    print("Candidate Promotion Plan")
    print(f"Source: {store}")
    print(f"Records read: {len(raw_records)}")
    print(f"Invalid records skipped: {invalid_json + invalid_records}")
    print()

    if not selected:
        print("Recommended action: keep-candidate")
        print("Reason: no matching candidate group was found")
        return 0

    first = selected[0]
    latest = selected[-1]
    action = recommended_action(selected, args.promote_count, args.merge_count)
    new_card_name = slug(first.failed_invariant)

    print(f"Mechanism key: {first.mechanism_key}")
    print(f"Recommended action: {action}")
    print(f"Nearest family: {first.family}")
    print(f"Count: {len(selected)}")
    print(f"Max severity: {max((item.severity for item in selected), key=lambda item: SEVERITY_RANK[item])}")
    print(f"Failed invariant: {first.failed_invariant}")
    if latest.missing_handling:
        print(f"Latest missing handling: {latest.missing_handling}")
    if latest.verification:
        print(f"Latest verification: {latest.verification}")
    print()
    print("Files to update:")
    if action == "merge-into-existing-card":
        print(f"- skills/bug-check/references/boundaries/{first.family}.md")
    elif action == "promote-new-card":
        print(f"- skills/bug-check/references/boundaries/{new_card_name}.md")
    else:
        print("- no formal boundary card update yet")
    print("- skills/bug-check/references/routing.md")
    print("- skills/bug-check/references/bug-check.md")
    print("- scripts/validate-project.py")
    print("- tests/fixtures/")
    print("- README.md if the public card inventory or usage changes")
    print()
    print("Plan notes:")
    print("- Promote only abstract reusable mechanism details; keep project-private facts in the JSONL store.")
    print("- Prefer a 1-3 line merge into an existing card when that fully covers the invariant.")
    print("- Add or update a fixture so validation proves the card remains discoverable.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="Append one manual boundary candidate to a project-local store.")
    record.add_argument("--store", default=str(DEFAULT_STORE), help="JSONL store path. Defaults to .bug-check/manual-boundaries.jsonl.")
    record.add_argument("--family", required=True, help="Nearest existing boundary family, such as ui-list-table.")
    record.add_argument("--failed-invariant", required=True, help="Reusable invariant that failed, not the one-off symptom.")
    record.add_argument("--severity", choices=tuple(SEVERITY_RANK), default="medium")
    record.add_argument("--trigger", action="append", default=[], help="Trigger or signal. Repeat or pass comma-separated values.")
    record.add_argument("--changed-path-shape", action="append", default=[], help="Path shape, such as src/pages/*List.tsx.")
    record.add_argument("--missing-handling", required=True, help="What handling was absent.")
    record.add_argument("--verification", required=True, help="How the boundary was or should be verified.")
    record.add_argument("--suggested-action", choices=("keep-candidate", "merge-into-existing-card", "promote-new-card"), default="keep-candidate")
    record.add_argument("--mechanism-key", help="Stable key. Defaults to a slug from family and failed invariant.")
    record.add_argument("--observed-at", help="Observation date. Defaults to today.")
    record.set_defaults(func=write_record)

    review = subparsers.add_parser("review", help="Aggregate candidates and print promotion guidance.")
    review.add_argument("--store", default=str(DEFAULT_STORE), help="JSONL store path. Defaults to .bug-check/manual-boundaries.jsonl.")
    review.add_argument("--merge-count", type=int, default=2, help="Occurrence count where existing-card merge should be considered.")
    review.add_argument("--promote-count", type=int, default=3, help="Occurrence count where promotion should be considered.")
    review.add_argument("--limit", type=int, default=10, help="Maximum groups to print.")
    review.set_defaults(func=review_records)

    plan = subparsers.add_parser("plan", help="Print a maintenance plan for promoting or merging one candidate group.")
    plan.add_argument("--store", default=str(DEFAULT_STORE), help="JSONL store path. Defaults to .bug-check/manual-boundaries.jsonl.")
    plan.add_argument("--mechanism-key", help="Specific mechanism key to plan. Defaults to the top-ranked candidate.")
    plan.add_argument("--merge-count", type=int, default=2, help="Occurrence count where existing-card merge should be considered.")
    plan.add_argument("--promote-count", type=int, default=3, help="Occurrence count where promotion should be considered.")
    plan.set_defaults(func=plan_records)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
