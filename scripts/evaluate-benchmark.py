#!/usr/bin/env python3
"""Validate anonymous bug replays, export blind prompts, and score exact labels."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "benchmark" / "cases.json"
SCHEMA_VERSION = 1

REQUIRED_CATEGORIES = (
    "requirement-ambiguity",
    "stale-state",
    "async-first-interaction",
    "product-rule-units-naming",
    "realtime-integration",
    "canvas-zoom",
    "empty-data",
)
REQUIRED_STAGES = ("clarify", "pre-change", "post-change", "runtime")
REQUIRED_DECISIONS = (
    "product-decision-required",
    "continue-investigating",
    "continue-fixing",
    "runtime-evidence-required",
    "verified",
)
REQUIRED_SOURCES = (
    "specified",
    "existing-contract",
    "inferred",
    "product-decision-required",
)

FORBIDDEN_IDENTITY_KEYS = {
    "account",
    "account_id",
    "assignee",
    "bug_id",
    "company",
    "company_name",
    "ip",
    "ip_address",
    "organization",
    "organization_name",
    "original_bug_id",
    "person",
    "person_name",
    "product_name",
    "reporter",
    "reporter_name",
    "source_url",
    "url",
    "user_email",
    "username",
}
URL_PATTERN = re.compile(r"\b(?:https?://|www\.)", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
CASE_ID_PATTERN = re.compile(r"^replay-[0-9]{3}$")
SCENARIO_FIELDS = (
    "report",
    "observed_behavior",
    "replay_trigger",
    "changed_scope",
    "available_evidence",
    "runtime_access",
)
IDENTITY_ROLE_KEY = re.compile(
    r"^(?:account|assignee|client|contact|customer|employee|member|owner|person|reporter|user)"
    r"(?:$|(?:_[a-z0-9]+)*_(?:email|id|name|phone|username))$"
)
IDENTITY_CONTACT_KEY = re.compile(r"(?:^|_)(?:e_mail|email|mobile|phone|telephone)(?:$|_)")
IDENTITY_NAME_KEY = re.compile(r"^(?:display|first|full|last|legal)_name$")

SCORING_LIMITATIONS = (
    "Scores measure exact agreement with the stored stage, decision, and source labels only.",
    "They do not evaluate explanation quality, root-cause validity, evidence quality, or semantic correctness.",
)
BLIND_TASK_INSTRUCTION = (
    "For each prompt, classify the workflow stage, engineering decision, and requirement "
    "source. Use exactly one allowed label for each field, return exactly one prediction "
    "per case_id, and do not use explanations in the scoring JSON. Apply this identical "
    "task contract to both comparison runs. Do not access the source dataset, gold labels, "
    "scoring output, or the other run's predictions."
)


class ValidationError(ValueError):
    """Raised when a benchmark or prediction payload violates its contract."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValidationError(f"duplicate JSON key is not allowed: {key}")
        output[key] = value
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the anonymized replay dataset and optionally score prediction JSON. "
            "Scoring is exact stage, decision, and source label agreement only; it does not "
            "judge semantic correctness."
        ),
        epilog=(
            "Prediction shape: {\"schema_version\": 1, \"predictions\": "
            "[{\"case_id\": \"...\", \"stage\": \"...\", \"decision\": \"...\", "
            "\"source\": \"...\"}]}. Missing cases score as incorrect. "
            "Allowed stages: " + ", ".join(REQUIRED_STAGES) + ". Allowed decisions: "
            + ", ".join(REQUIRED_DECISIONS) + ". Allowed sources: "
            + ", ".join(REQUIRED_SOURCES) + "."
        ),
    )
    parser.add_argument(
        "--cases",
        default=str(DEFAULT_CASES),
        help=f"Benchmark JSON path (default: {DEFAULT_CASES.relative_to(ROOT)}).",
    )
    parser.add_argument(
        "--predictions",
        help="Prediction JSON path. Use '-' to read prediction JSON from standard input.",
    )
    parser.add_argument(
        "--export-prompts",
        metavar="PATH",
        help=(
            "Export a gold-free shared task contract, label vocabulary, prediction schema, "
            "and prompts containing only case_id and scenario. Use '-' for standard output."
        ),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help=(
            "Validate dataset structure, category corpus coverage, stage/decision/source "
            "coverage, and obvious privacy leaks without scoring."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the validation and scoring result as JSON.",
    )
    args = parser.parse_args()
    if args.validate_only and args.predictions:
        parser.error("--validate-only cannot be combined with --predictions")
    if args.export_prompts and args.predictions:
        parser.error("--export-prompts cannot be combined with --predictions")
    if args.cases == "-" and args.predictions == "-":
        parser.error("--cases and --predictions cannot both read from standard input")
    return args


def load_json(path_value: str, *, kind: str) -> Any:
    try:
        if path_value == "-":
            source = "standard input"
            text = sys.stdin.buffer.read().decode("utf-8")
        else:
            path = Path(path_value)
            source = str(path)
            text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(
            f"invalid UTF-8 in {kind} JSON from {source}: byte {exc.start}"
        ) from exc
    except OSError as exc:
        raise ValidationError(f"cannot read {kind} JSON: {exc}") from exc

    try:
        return json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"invalid {kind} JSON in {source} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{location} must be an object")
    return value


def require_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{location} must be a non-empty string")
    return value


def require_string_list(value: Any, location: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(f"{location} must be an array of strings")
    if not allow_empty and not value:
        raise ValidationError(f"{location} must not be empty")
    for index, item in enumerate(value):
        require_string(item, f"{location}[{index}]")
    return value


def require_exact_fields(value: dict[str, Any], expected: tuple[str, ...], location: str) -> None:
    missing = sorted(set(expected) - set(value))
    extra = sorted(set(value) - set(expected))
    if missing or extra:
        raise ValidationError(f"{location} fields mismatch; missing={missing}, extra={extra}")


def string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in string_values(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in string_values(item)]
    return []


def validate_no_explicit_gold(
    scenario: dict[str, Any],
    *,
    case_id: str,
    category: str,
    stage: str,
    decision: str,
    source: str,
) -> None:
    scenario_text = "\n".join(string_values(scenario))
    labels = {
        "category": category,
        "stage": stage,
        "decision": decision,
        "source": source,
    }
    for field, label in labels.items():
        label_pattern = re.escape(label).replace(r"\-", r"[-_\s]+")
        verbatim_label = re.compile(
            rf"(?<![A-Za-z0-9_-]){label_pattern}(?![A-Za-z0-9_-])",
            re.IGNORECASE,
        )
        if verbatim_label.search(scenario_text):
            raise ValidationError(
                f"case {case_id}.scenario contains the expected {field} label verbatim"
            )
        annotation = re.compile(
            rf"(?<![A-Za-z0-9_])[\"']?(?:expected[\s_-]+)?{re.escape(field)}[\"']?\s*"
            rf"(?::|=|[-=]>|→|\b(?:is|was|equals?|should\s+be|must\s+be)\b)\s*"
            rf"[\"']?{label_pattern}(?![A-Za-z0-9_-])",
            re.IGNORECASE,
        )
        if annotation.search(scenario_text):
            raise ValidationError(
                f"case {case_id}.scenario contains an explicit expected {field} label"
            )


def validate_schema_version(payload: dict[str, Any], location: str) -> None:
    value = payload.get("schema_version")
    if type(value) is not int or value != SCHEMA_VERSION:
        raise ValidationError(f"{location}.schema_version must be {SCHEMA_VERSION}")


def validate_label_space(payload: dict[str, Any]) -> None:
    label_space = require_object(payload.get("label_space"), "dataset.label_space")
    expected_groups = {
        "categories": REQUIRED_CATEGORIES,
        "stages": REQUIRED_STAGES,
        "decisions": REQUIRED_DECISIONS,
        "sources": REQUIRED_SOURCES,
    }
    for group, expected in expected_groups.items():
        values = require_string_list(label_space.get(group), f"dataset.label_space.{group}")
        if len(values) != len(set(values)):
            raise ValidationError(f"dataset.label_space.{group} contains duplicate labels")
        if set(values) != set(expected):
            missing = sorted(set(expected) - set(values))
            extra = sorted(set(values) - set(expected))
            raise ValidationError(
                f"dataset.label_space.{group} mismatch; missing={missing}, extra={extra}"
            )


def validate_privacy_shape(payload: dict[str, Any]) -> None:
    privacy = require_object(payload.get("privacy"), "dataset.privacy")
    require_string(privacy.get("source_handling"), "dataset.privacy.source_handling")
    require_string(privacy.get("validation_limit"), "dataset.privacy.validation_limit")


def lint_obvious_identity_data(value: Any, location: str = "dataset") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", key)
            normalized_key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized_key)
            normalized_key = re.sub(r"[^a-z0-9]+", "_", normalized_key.lower()).strip("_")
            if (
                normalized_key in FORBIDDEN_IDENTITY_KEYS
                or IDENTITY_ROLE_KEY.fullmatch(normalized_key)
                or IDENTITY_CONTACT_KEY.search(normalized_key)
                or IDENTITY_NAME_KEY.fullmatch(normalized_key)
            ):
                raise ValidationError(f"{location}.{key} is an identity-bearing field and is not allowed")
            lint_obvious_identity_data(child, f"{location}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            lint_obvious_identity_data(child, f"{location}[{index}]")
        return
    if not isinstance(value, str):
        return

    patterns = (
        (URL_PATTERN, "URL-like value"),
        (EMAIL_PATTERN, "email-like value"),
        (IPV4_PATTERN, "IPv4-like value"),
    )
    for pattern, label in patterns:
        if pattern.search(value):
            raise ValidationError(f"{location} contains a forbidden {label}")


def validate_case(case: Any, index: int) -> dict[str, Any]:
    item = require_object(case, f"dataset.cases[{index}]")
    case_id = require_string(item.get("case_id"), f"dataset.cases[{index}].case_id")
    if not CASE_ID_PATTERN.fullmatch(case_id):
        raise ValidationError(
            f"dataset.cases[{index}].case_id must use an opaque replay-NNN identifier"
        )

    category = require_string(item.get("category"), f"case {case_id}.category")
    if category not in REQUIRED_CATEGORIES:
        raise ValidationError(f"case {case_id}.category is not in the corpus category set")

    scenario = require_object(item.get("scenario"), f"case {case_id}.scenario")
    require_exact_fields(scenario, SCENARIO_FIELDS, f"case {case_id}.scenario")
    for field in ("report", "observed_behavior", "replay_trigger"):
        require_string(scenario.get(field), f"case {case_id}.scenario.{field}")
    require_string_list(
        scenario.get("changed_scope"),
        f"case {case_id}.scenario.changed_scope",
        allow_empty=True,
    )
    require_string_list(
        scenario.get("available_evidence"),
        f"case {case_id}.scenario.available_evidence",
    )
    if not isinstance(scenario.get("runtime_access"), bool):
        raise ValidationError(f"case {case_id}.scenario.runtime_access must be a boolean")

    expected = require_object(item.get("expected"), f"case {case_id}.expected")
    stage = require_string(expected.get("stage"), f"case {case_id}.expected.stage")
    decision = require_string(expected.get("decision"), f"case {case_id}.expected.decision")
    source = require_string(expected.get("source"), f"case {case_id}.expected.source")
    require_string(
        expected.get("minimum_counterexample"),
        f"case {case_id}.expected.minimum_counterexample",
    )
    require_string(expected.get("rationale"), f"case {case_id}.expected.rationale")

    if stage not in REQUIRED_STAGES:
        raise ValidationError(f"case {case_id}.expected.stage is not in the stage label space")
    if decision not in REQUIRED_DECISIONS:
        raise ValidationError(f"case {case_id}.expected.decision is not in the decision label space")
    if source not in REQUIRED_SOURCES:
        raise ValidationError(f"case {case_id}.expected.source is not in the source label space")
    validate_no_explicit_gold(
        scenario,
        case_id=case_id,
        category=category,
        stage=stage,
        decision=decision,
        source=source,
    )
    return item


def validate_dataset(payload: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    dataset = require_object(payload, "dataset")
    validate_schema_version(dataset, "dataset")
    require_string(dataset.get("dataset_name"), "dataset.dataset_name")
    require_string(dataset.get("dataset_purpose"), "dataset.dataset_purpose")
    validate_privacy_shape(dataset)
    validate_label_space(dataset)

    raw_cases = dataset.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValidationError("dataset.cases must be a non-empty array")
    cases = [validate_case(case, index) for index, case in enumerate(raw_cases)]

    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValidationError("dataset.cases contains duplicate case_id values")

    category_coverage = {case["category"] for case in cases}
    missing_categories = sorted(set(REQUIRED_CATEGORIES) - category_coverage)
    if missing_categories:
        raise ValidationError(f"dataset is missing required categories: {missing_categories}")

    stage_coverage = {case["expected"]["stage"] for case in cases}
    missing_stages = sorted(set(REQUIRED_STAGES) - stage_coverage)
    if missing_stages:
        raise ValidationError(f"dataset is missing expected stages: {missing_stages}")

    decision_coverage = {case["expected"]["decision"] for case in cases}
    missing_decisions = sorted(set(REQUIRED_DECISIONS) - decision_coverage)
    if missing_decisions:
        raise ValidationError(f"dataset is missing expected decisions: {missing_decisions}")

    source_coverage = {case["expected"]["source"] for case in cases}
    missing_sources = sorted(set(REQUIRED_SOURCES) - source_coverage)
    if missing_sources:
        raise ValidationError(f"dataset is missing expected sources: {missing_sources}")

    lint_obvious_identity_data(dataset)
    return dataset, cases


def validate_predictions(
    payload: Any,
    cases: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    prediction_set = require_object(payload, "prediction_set")
    require_exact_fields(prediction_set, ("schema_version", "predictions"), "prediction_set")
    validate_schema_version(prediction_set, "prediction_set")
    raw_predictions = prediction_set.get("predictions")
    if not isinstance(raw_predictions, list):
        raise ValidationError("prediction_set.predictions must be an array")

    known_case_ids = {case["case_id"] for case in cases}
    predictions: dict[str, dict[str, str]] = {}
    for index, raw_prediction in enumerate(raw_predictions):
        prediction = require_object(raw_prediction, f"prediction_set.predictions[{index}]")
        require_exact_fields(
            prediction,
            ("case_id", "stage", "decision", "source"),
            f"prediction_set.predictions[{index}]",
        )
        case_id = require_string(
            prediction.get("case_id"), f"prediction_set.predictions[{index}].case_id"
        )
        if case_id not in known_case_ids:
            raise ValidationError(f"prediction references unknown case_id: {case_id}")
        if case_id in predictions:
            raise ValidationError(f"prediction_set contains duplicate case_id: {case_id}")

        stage = require_string(prediction.get("stage"), f"prediction {case_id}.stage")
        decision = require_string(prediction.get("decision"), f"prediction {case_id}.decision")
        source = require_string(prediction.get("source"), f"prediction {case_id}.source")
        if stage not in REQUIRED_STAGES:
            raise ValidationError(f"prediction {case_id}.stage is not in the stage label space")
        if decision not in REQUIRED_DECISIONS:
            raise ValidationError(f"prediction {case_id}.decision is not in the decision label space")
        if source not in REQUIRED_SOURCES:
            raise ValidationError(f"prediction {case_id}.source is not in the source label space")
        predictions[case_id] = {
            "stage": stage,
            "decision": decision,
            "source": source,
        }
    return predictions


def ratio(correct: int, total: int) -> float:
    return round(correct / total, 6) if total else 0.0


def score_predictions(
    cases: list[dict[str, Any]],
    predictions: dict[str, dict[str, str]],
) -> dict[str, Any]:
    stage_correct = 0
    decision_correct = 0
    source_correct = 0
    joint_correct = 0
    per_case: list[dict[str, Any]] = []

    for case in cases:
        case_id = case["case_id"]
        expected = case["expected"]
        prediction = predictions.get(case_id)
        stage_match = bool(prediction and prediction["stage"] == expected["stage"])
        decision_match = bool(prediction and prediction["decision"] == expected["decision"])
        source_match = bool(prediction and prediction["source"] == expected["source"])
        joint_match = stage_match and decision_match and source_match
        stage_correct += int(stage_match)
        decision_correct += int(decision_match)
        source_correct += int(source_match)
        joint_correct += int(joint_match)
        per_case.append(
            {
                "case_id": case_id,
                "predicted": prediction,
                "expected": {
                    "stage": expected["stage"],
                    "decision": expected["decision"],
                    "source": expected["source"],
                },
                "stage_match": stage_match,
                "decision_match": decision_match,
                "source_match": source_match,
                "joint_match": joint_match,
            }
        )

    total = len(cases)
    predicted = len(predictions)
    return {
        "case_count": total,
        "prediction_count": predicted,
        "missing_prediction_count": total - predicted,
        "coverage": ratio(predicted, total),
        "stage": {
            "correct": stage_correct,
            "total": total,
            "accuracy": ratio(stage_correct, total),
        },
        "decision": {
            "correct": decision_correct,
            "total": total,
            "accuracy": ratio(decision_correct, total),
        },
        "source": {
            "correct": source_correct,
            "total": total,
            "accuracy": ratio(source_correct, total),
        },
        "joint": {
            "correct": joint_correct,
            "total": total,
            "accuracy": ratio(joint_correct, total),
        },
        "per_case": per_case,
    }


def build_result(
    dataset: dict[str, Any],
    cases: list[dict[str, Any]],
    scoring: dict[str, Any] | None,
) -> dict[str, Any]:
    categories_seen = sorted({case["category"] for case in cases})
    stages_seen = sorted({case["expected"]["stage"] for case in cases})
    decisions_seen = sorted({case["expected"]["decision"] for case in cases})
    sources_seen = sorted({case["expected"]["source"] for case in cases})
    return {
        "status": "valid",
        "dataset_name": dataset["dataset_name"],
        "schema_version": dataset["schema_version"],
        "case_count": len(cases),
        "coverage": {
            "categories": {
                "required": list(REQUIRED_CATEGORIES),
                "seen": categories_seen,
                "complete": set(categories_seen) == set(REQUIRED_CATEGORIES),
            },
            "stages": {
                "required": list(REQUIRED_STAGES),
                "seen": stages_seen,
                "complete": set(stages_seen) == set(REQUIRED_STAGES),
            },
            "decisions": {
                "required": list(REQUIRED_DECISIONS),
                "seen": decisions_seen,
                "complete": set(decisions_seen) == set(REQUIRED_DECISIONS),
            },
            "sources": {
                "required": list(REQUIRED_SOURCES),
                "seen": sources_seen,
                "complete": set(sources_seen) == set(REQUIRED_SOURCES),
            },
        },
        "privacy_check": {
            "status": "passed",
            "scope": "Obvious identity-bearing keys, URL-like values, email-like values, and IPv4-like values only.",
            "complete_anonymization_proof": False,
        },
        "scoring": scoring,
        "limitations": list(SCORING_LIMITATIONS),
    }


def print_text(result: dict[str, Any]) -> None:
    category_coverage = result["coverage"]["categories"]
    stage_coverage = result["coverage"]["stages"]
    decision_coverage = result["coverage"]["decisions"]
    source_coverage = result["coverage"]["sources"]
    print(f"PASS: validated {result['case_count']} benchmark cases")
    print(
        "Corpus-category coverage: "
        f"{len(category_coverage['seen'])}/{len(category_coverage['required'])} required categories"
    )
    print(
        "Expected-stage coverage: "
        f"{len(stage_coverage['seen'])}/{len(stage_coverage['required'])} required stages"
    )
    print(
        "Expected-decision coverage: "
        f"{len(decision_coverage['seen'])}/{len(decision_coverage['required'])} required decisions"
    )
    print(
        "Expected-source coverage: "
        f"{len(source_coverage['seen'])}/{len(source_coverage['required'])} required sources"
    )
    print("Privacy lint: passed obvious-pattern checks; this is not proof of full anonymization")

    scoring = result["scoring"]
    if scoring is not None:
        print(
            f"Prediction coverage: {scoring['prediction_count']}/{scoring['case_count']} "
            f"({scoring['coverage']:.1%})"
        )
        print(
            f"Stage exact match: {scoring['stage']['correct']}/{scoring['stage']['total']} "
            f"({scoring['stage']['accuracy']:.1%})"
        )
        print(
            f"Decision exact match: {scoring['decision']['correct']}/{scoring['decision']['total']} "
            f"({scoring['decision']['accuracy']:.1%})"
        )
        print(
            f"Source exact match: {scoring['source']['correct']}/{scoring['source']['total']} "
            f"({scoring['source']['accuracy']:.1%})"
        )
        print(
            f"Joint exact match: {scoring['joint']['correct']}/{scoring['joint']['total']} "
            f"({scoring['joint']['accuracy']:.1%})"
        )
    print("Limitation: exact stored-label agreement only; semantic correctness is not evaluated")


def export_blind_prompts(cases: list[dict[str, Any]], path_value: str) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task": BLIND_TASK_INSTRUCTION,
        "label_space": {
            "stages": list(REQUIRED_STAGES),
            "decisions": list(REQUIRED_DECISIONS),
            "sources": list(REQUIRED_SOURCES),
        },
        "prediction_contract": {
            "schema_version": SCHEMA_VERSION,
            "top_level_field": "predictions",
            "prediction_fields": ["case_id", "stage", "decision", "source"],
            "coverage": "Return exactly one prediction for every exported case_id.",
        },
        "prompts": [
            {
                "case_id": case["case_id"],
                "scenario": {
                    field: case["scenario"][field]
                    for field in SCENARIO_FIELDS
                },
            }
            for case in cases
        ],
    }
    output = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path_value == "-":
        sys.stdout.write(output)
        return
    try:
        Path(path_value).write_text(output, encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"cannot write blind prompt JSON: {exc}") from exc


def main() -> int:
    args = parse_args()
    try:
        dataset_payload = load_json(args.cases, kind="benchmark")
        dataset, cases = validate_dataset(dataset_payload)
        scoring = None
        if args.predictions:
            prediction_payload = load_json(args.predictions, kind="prediction")
            predictions = validate_predictions(prediction_payload, cases)
            scoring = score_predictions(cases, predictions)
        result = build_result(dataset, cases, scoring)
        if args.export_prompts:
            export_blind_prompts(cases, args.export_prompts)
    except ValidationError as exc:
        if args.json:
            print(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.export_prompts == "-":
        return 0
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
