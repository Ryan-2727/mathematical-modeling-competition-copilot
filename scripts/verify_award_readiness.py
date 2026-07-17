#!/usr/bin/env python3
"""Check award-oriented evidence gates after the paper and review are complete.

Passing this structural check does not prove mathematical correctness or predict
an award. It confirms that the required decisions, tests, and reviewer evidence
were recorded and linked to the paper's subproblems.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


COMPLETE = {"complete", "completed", "pass", "passed", "verified"}
RESOLVED_VERDICTS = {
    "pass", "passed", "resolved", "claim_narrowed", "claim-narrowed",
    "accepted_limitation", "accepted-limitation",
}
REVIEW_DIMENSIONS = {
    "assumption_rationality",
    "model_creativity",
    "result_correctness",
    "writing_clarity",
}
SCHEMAS = {
    "argument_coverage.csv": {
        "subproblem", "need_or_mechanism", "model", "solution",
        "quantified_result", "interpretation", "validation", "status",
    },
    "model_decision_log.csv": {
        "subproblem", "baseline", "candidate", "mechanism_fit", "assumptions",
        "failure_test", "validation_cost", "selected", "selection_evidence", "status",
    },
    "stress_tests.csv": {
        "claim_id", "subproblem", "stress_type", "change", "acceptance_criterion",
        "result_file", "outcome", "verdict", "status",
    },
    "units.csv": {
        "symbol", "meaning", "unit", "source", "conversion", "range_check", "status",
    },
    "reviewer_scorecard.csv": {
        "dimension", "score_1_to_5", "evidence", "major_objection", "smallest_fix", "status",
    },
    "milestones.csv": {"milestone", "hour", "deliverable", "owner", "gate", "status"},
}


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    if not path.is_file():
        return [], set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def value(row: dict[str, str], field: str) -> str:
    return (row.get(field) or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir
    report_dir = root / "reports"
    errors: list[str] = []
    data: dict[str, list[dict[str, str]]] = {}

    for filename, required_fields in SCHEMAS.items():
        rows, fields = read_csv(report_dir / filename)
        data[filename] = rows
        if not fields:
            errors.append(f"reports/{filename} is missing or has no header")
        elif missing := required_fields - fields:
            errors.append(f"reports/{filename} missing columns: {', '.join(sorted(missing))}")

    arguments = data["argument_coverage.csv"]
    subproblems = {value(row, "subproblem") for row in arguments if value(row, "subproblem")}
    if not subproblems:
        errors.append("argument_coverage.csv has no subproblem rows")
    for index, row in enumerate(arguments, 2):
        if any(not value(row, field) for field in SCHEMAS["argument_coverage.csv"]):
            errors.append(f"argument_coverage.csv:{index} has empty required fields")
        if value(row, "status").lower() not in COMPLETE:
            errors.append(f"argument_coverage.csv:{index} is not complete")

    decisions = data["model_decision_log.csv"]
    decision_coverage = {value(row, "subproblem") for row in decisions if value(row, "subproblem")}
    for index, row in enumerate(decisions, 2):
        if any(not value(row, field) for field in SCHEMAS["model_decision_log.csv"]):
            errors.append(f"model_decision_log.csv:{index} has empty required fields")
        if value(row, "status").lower() not in COMPLETE:
            errors.append(f"model_decision_log.csv:{index} is not complete")
    for missing in sorted(subproblems - decision_coverage):
        errors.append(f"model_decision_log.csv does not cover subproblem {missing}")

    stress_tests = data["stress_tests.csv"]
    stress_coverage = {value(row, "subproblem") for row in stress_tests if value(row, "subproblem")}
    for index, row in enumerate(stress_tests, 2):
        if any(not value(row, field) for field in SCHEMAS["stress_tests.csv"]):
            errors.append(f"stress_tests.csv:{index} has empty required fields")
        result_file = value(row, "result_file")
        result_path = Path(result_file)
        if result_file and (result_path.is_absolute() or ".." in result_path.parts):
            errors.append(f"stress_tests.csv:{index} result must stay inside the project: {result_file}")
        elif result_file and not (root / result_path).is_file():
            errors.append(f"stress_tests.csv:{index} result missing: {result_file}")
        if value(row, "verdict").lower() not in RESOLVED_VERDICTS:
            errors.append(f"stress_tests.csv:{index} failed or inconclusive result is not resolved in the claim")
        if value(row, "status").lower() not in COMPLETE:
            errors.append(f"stress_tests.csv:{index} is not complete")
    for missing in sorted(subproblems - stress_coverage):
        errors.append(f"stress_tests.csv does not cover subproblem {missing}")

    units = data["units.csv"]
    units_by_symbol: dict[str, set[str]] = {}
    if not units:
        errors.append("units.csv has no reviewed quantity rows; record an explicit dimensionless/N/A row when appropriate")
    for index, row in enumerate(units, 2):
        if any(not value(row, field) for field in SCHEMAS["units.csv"]):
            errors.append(f"units.csv:{index} has empty required fields")
        symbol = value(row, "symbol")
        if symbol:
            units_by_symbol.setdefault(symbol, set()).add(value(row, "unit"))
        if value(row, "status").lower() not in COMPLETE:
            errors.append(f"units.csv:{index} is not complete")
    for symbol, recorded_units in units_by_symbol.items():
        if len(recorded_units) > 1:
            errors.append(f"units.csv has conflicting units for {symbol}: {sorted(recorded_units)}")

    scorecard = data["reviewer_scorecard.csv"]
    seen_dimensions: set[str] = set()
    for index, row in enumerate(scorecard, 2):
        dimension = value(row, "dimension")
        if dimension:
            seen_dimensions.add(dimension)
        try:
            score = int(value(row, "score_1_to_5"))
            if score not in range(1, 6):
                raise ValueError
        except ValueError:
            errors.append(f"reviewer_scorecard.csv:{index} score must be an integer from 1 to 5")
        if any(not value(row, field) for field in SCHEMAS["reviewer_scorecard.csv"]):
            errors.append(f"reviewer_scorecard.csv:{index} has empty required fields")
        if value(row, "status").lower() not in COMPLETE:
            errors.append(f"reviewer_scorecard.csv:{index} is not complete")
    if missing_dimensions := REVIEW_DIMENSIONS - seen_dimensions:
        errors.append("reviewer_scorecard.csv missing dimensions: " + ", ".join(sorted(missing_dimensions)))
    if extra_dimensions := seen_dimensions - REVIEW_DIMENSIONS:
        errors.append("reviewer_scorecard.csv has unknown dimensions: " + ", ".join(sorted(extra_dimensions)))
    if len(scorecard) != len(REVIEW_DIMENSIONS):
        errors.append("reviewer_scorecard.csv must contain exactly one row for each required dimension")

    milestones = data["milestones.csv"]
    if not milestones:
        errors.append("milestones.csv has no milestone rows")
    for index, row in enumerate(milestones, 2):
        if any(not value(row, field) for field in SCHEMAS["milestones.csv"]):
            errors.append(f"milestones.csv:{index} has empty required fields")
        if value(row, "status").lower() not in COMPLETE:
            errors.append(f"milestones.csv:{index} is not complete")

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "structural award-readiness evidence; not mathematical truth or an award prediction",
        "counts": {
            "subproblems": len(subproblems),
            "model_decisions": len(decisions),
            "stress_tests": len(stress_tests),
            "unit_rows": len(units),
            "review_dimensions": len(seen_dimensions),
            "milestones": len(milestones),
        },
        "errors": errors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
