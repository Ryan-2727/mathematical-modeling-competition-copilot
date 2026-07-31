#!/usr/bin/env python3
"""Verify result-first simplification records and conclusion-driven visuals."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contestlib import read_csv_with_error as read_csv
from contestlib import safe_project_path as safe
from contestlib import sha256_bytes as digest


COMPLETE = {"pass", "complete", "verified"}
CONCLUSION_FIELDS = {"subproblem", "decisive_value_key", "status"}
SIMPLIFICATION_FIELDS = {
    "subproblem", "primary_route", "failure_diagnostic", "decision_state",
    "retained_core_factors", "removed_noncritical_factors", "simplified_route",
    "user_authorization", "original_model_treatment", "result_file",
    "paper_location", "status",
}
STORYBOARD_FIELDS = {
    "artifact_id", "artifact_type", "subproblem", "question", "claim_id",
    "source_result", "selection_rationale", "paper_location", "status",
}
ARTIFACT_TYPES = {
    "mechanism_diagram", "result_chart", "path_or_network", "model_comparison",
    "validation_chart",
}
DECISION_STATES = {"primary_result_verified", "user_authorized_simplification"}


def nonempty(row: dict[str, str], fields: set[str]) -> bool:
    return all(str(row.get(field) or "").strip() for field in fields)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify result-first model simplification and visual story evidence.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/result_story.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    reports = root / "reports"
    paths = {
        "conclusion": reports / "conclusion_map.csv",
        "values": root / "results/verified_values.csv",
        "simplification": reports / "model_simplification_log.csv",
        "storyboard": reports / "visual_storyboard.csv",
        "challenge": reports / "model_challenge.json",
    }
    errors: list[str] = []
    conclusion_rows, conclusion_columns, conclusion_error = read_csv(paths["conclusion"])
    value_rows, value_columns, value_error = read_csv(paths["values"])
    simplification_rows, simplification_columns, simplification_error = read_csv(paths["simplification"])
    storyboard_rows, storyboard_columns, storyboard_error = read_csv(paths["storyboard"])
    for label, error in (("conclusion_map.csv", conclusion_error), ("verified_values.csv", value_error), ("model_simplification_log.csv", simplification_error), ("visual_storyboard.csv", storyboard_error)):
        if error:
            errors.append(f"cannot read {label}: {error}")
    if CONCLUSION_FIELDS - conclusion_columns:
        errors.append("conclusion_map.csv missing columns: " + ", ".join(sorted(CONCLUSION_FIELDS - conclusion_columns)))
    if {"key", "value"} - value_columns:
        errors.append("verified_values.csv missing key/value columns")
    if SIMPLIFICATION_FIELDS - simplification_columns:
        errors.append("model_simplification_log.csv missing columns: " + ", ".join(sorted(SIMPLIFICATION_FIELDS - simplification_columns)))
    if STORYBOARD_FIELDS - storyboard_columns:
        errors.append("visual_storyboard.csv missing columns: " + ", ".join(sorted(STORYBOARD_FIELDS - storyboard_columns)))
    subproblems = {str(row.get("subproblem") or "").strip() for row in conclusion_rows if str(row.get("subproblem") or "").strip()}
    values = {str(row.get("key") or "").strip() for row in value_rows if str(row.get("key") or "").strip()}
    if not subproblems:
        errors.append("conclusion_map.csv has no answered subproblems")
    for line, row in enumerate(conclusion_rows, 2):
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"conclusion_map.csv:{line} is not complete")
        key = str(row.get("decisive_value_key") or "").strip()
        if key and key not in values:
            errors.append(f"conclusion_map.csv:{line} decisive value is not verified")
    by_subproblem: dict[str, list[dict[str, str]]] = {}
    for line, row in enumerate(simplification_rows, 2):
        subproblem = str(row.get("subproblem") or "").strip()
        by_subproblem.setdefault(subproblem, []).append(row)
        if not nonempty(row, SIMPLIFICATION_FIELDS):
            errors.append(f"model_simplification_log.csv:{line} has empty required evidence")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"model_simplification_log.csv:{line} is not complete")
        state = str(row.get("decision_state") or "").strip()
        if state not in DECISION_STATES:
            errors.append(f"model_simplification_log.csv:{line} has invalid decision_state")
        result = safe(root, str(row.get("result_file") or ""))
        if result is None or not result.is_file():
            errors.append(f"model_simplification_log.csv:{line} result_file is missing or unsafe")
        if state == "user_authorized_simplification":
            if not str(row.get("user_authorization") or "").strip():
                errors.append(f"model_simplification_log.csv:{line} lacks user authorization")
            if str(row.get("original_model_treatment") or "").strip() != "model_optimization":
                errors.append(f"model_simplification_log.csv:{line} must retain the original route as model_optimization")
            if str(row.get("removed_noncritical_factors") or "").strip().lower() in {"none", "not_applicable"}:
                errors.append(f"model_simplification_log.csv:{line} does not name removed noncritical factors")
            if str(row.get("primary_route") or "").strip() == str(row.get("simplified_route") or "").strip():
                errors.append(f"model_simplification_log.csv:{line} simplified route must differ from primary route")
    for subproblem in subproblems:
        if len(by_subproblem.get(subproblem, [])) != 1:
            errors.append(f"model_simplification_log.csv must contain exactly one result decision for {subproblem}")
    story_types: dict[str, set[str]] = {}
    for line, row in enumerate(storyboard_rows, 2):
        if not nonempty(row, STORYBOARD_FIELDS):
            errors.append(f"visual_storyboard.csv:{line} has empty required evidence")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"visual_storyboard.csv:{line} is not complete")
        kind = str(row.get("artifact_type") or "").strip()
        subproblem = str(row.get("subproblem") or "").strip()
        story_types.setdefault(subproblem, set()).add(kind)
        if kind not in ARTIFACT_TYPES:
            errors.append(f"visual_storyboard.csv:{line} has invalid artifact_type")
        result = safe(root, str(row.get("source_result") or ""))
        if result is None or not result.is_file():
            errors.append(f"visual_storyboard.csv:{line} source_result is missing or unsafe")
    for subproblem in subproblems:
        if "result_chart" not in story_types.get(subproblem, set()):
            errors.append(f"visual_storyboard.csv lacks a result_chart for {subproblem}")
    try:
        challenge = json.loads(paths["challenge"].read_text(encoding="utf-8-sig"))
        challenges = challenge.get("subproblems") if isinstance(challenge, dict) else []
    except (OSError, UnicodeError, json.JSONDecodeError):
        challenges = []
    for row in challenges if isinstance(challenges, list) else []:
        if not isinstance(row, dict):
            continue
        subproblem = str(row.get("subproblem") or "").strip()
        if subproblem and str(row.get("baseline_name") or "") != str(row.get("candidate_name") or "") and "model_comparison" not in story_types.get(subproblem, set()):
            errors.append(f"visual_storyboard.csv lacks a model_comparison for {subproblem}")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "recorded result decisions, user-authorized simplification, and visual-story coverage; not mathematical correctness",
        "conclusion_map_sha256": digest(paths["conclusion"]) if paths["conclusion"].is_file() else "",
        "verified_values_sha256": digest(paths["values"]) if paths["values"].is_file() else "",
        "simplification_log_sha256": digest(paths["simplification"]) if paths["simplification"].is_file() else "",
        "visual_storyboard_sha256": digest(paths["storyboard"]) if paths["storyboard"].is_file() else "",
        "counts": {"subproblems": len(subproblems), "decisions": len(simplification_rows), "visuals": len(storyboard_rows)},
        "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
