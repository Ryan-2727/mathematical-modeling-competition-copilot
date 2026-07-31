#!/usr/bin/env python3
"""Verify semantics, low-truth validation, conclusion maps, and minimal innovation."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from contestlib import read_csv_strict as read_csv
from contestlib import safe_project_path as safe


COMPLETE = {"pass", "complete", "verified"}
SEMANTIC_TYPES = {"observed_zero", "structural_zero", "no_opportunity", "not_observed", "censored_not_detected", "missing", "not_applicable"}
TRUTH = {"external_ground_truth", "partial_ground_truth", "no_ground_truth"}


def number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def load_table(root: Path, name: str, fields: set[str], errors: list[str]) -> list[dict[str, str]]:
    try:
        rows, actual = read_csv(root / "reports" / name)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot read {name}: {exc}")
        return []
    if fields - actual:
        errors.append(f"{name} missing columns: " + ", ".join(sorted(fields - actual)))
    if not rows:
        errors.append(f"{name} has no evidence rows")
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in fields):
            errors.append(f"{name}:{line} has empty required fields")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"{name}:{line} is not complete")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify high-leverage modeling and paper-argument evidence.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/modeling_argument_quality.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    out = safe(root, args.out)
    if out is None:
        raise SystemExit("output must stay inside --project-dir")
    errors: list[str] = []
    semantics = load_table(root, "semantic_audit.csv", {"semantic_id", "dataset", "field", "raw_representation", "semantic_type", "decision_impact", "evidence", "alternative_treatment", "sensitivity_needed", "used_by", "status"}, errors)
    semantic_ids = {str(row.get("semantic_id") or "").strip() for row in semantics}
    for line, row in enumerate(semantics, 2):
        if str(row.get("semantic_type") or "").strip() not in SEMANTIC_TYPES:
            errors.append(f"semantic_audit.csv:{line} has unsupported semantic_type")

    mechanism_path = root / "reports" / "mechanism_audit.json"
    try:
        mechanism = json.loads(mechanism_path.read_text(encoding="utf-8-sig"))
        mechanisms = mechanism.get("subproblems") if isinstance(mechanism, dict) else None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        mechanisms = None
        errors.append(f"cannot read mechanism_audit.json: {exc}")
    if not isinstance(mechanisms, list) or not mechanisms:
        errors.append("mechanism_audit.json requires non-empty subproblems")
        mechanisms = []
    subproblems: set[str] = set()
    required_mechanism = {"subproblem", "mechanism", "assumptions", "semantic_ids", "falsifiable_implication", "result_file", "status"}
    for index, row in enumerate(mechanisms, 1):
        if not isinstance(row, dict) or any(not row.get(field) for field in required_mechanism):
            errors.append(f"mechanism_audit subproblem {index} lacks required evidence")
            continue
        subproblem = str(row["subproblem"]).strip()
        subproblems.add(subproblem)
        semantic_refs = row.get("semantic_ids")
        if not isinstance(semantic_refs, list) or not set(map(str, semantic_refs)).issubset(semantic_ids):
            errors.append(f"mechanism_audit subproblem {index} references unknown semantic IDs")
        result = safe(root, str(row["result_file"]))
        if result is None or not result.is_file():
            errors.append(f"mechanism_audit subproblem {index} result_file is missing or unsafe")
        if str(row.get("status") or "").lower() not in COMPLETE:
            errors.append(f"mechanism_audit subproblem {index} is not complete")

    validations = load_table(root, "validation_design.csv", {"subproblem", "truth_availability", "validation_strategy", "independent_checks", "primary_metric", "baseline_or_invariant", "split_or_scenario", "acceptance_criterion", "limitation", "result_file", "status"}, errors)
    for line, row in enumerate(validations, 2):
        truth = str(row.get("truth_availability") or "")
        checks = number(row.get("independent_checks"))
        if truth not in TRUTH or checks is None or checks < 1:
            errors.append(f"validation_design.csv:{line} has invalid truth/independent_checks")
        if truth == "no_ground_truth" and (checks is None or checks < 2):
            errors.append(f"validation_design.csv:{line} needs at least two independent checks without ground truth")
        result = safe(root, str(row.get("result_file") or ""))
        if result is None or not result.is_file():
            errors.append(f"validation_design.csv:{line} result_file is missing or unsafe")
    if subproblems - {str(row.get("subproblem") or "") for row in validations}:
        errors.append("validation_design.csv lacks a mechanism-audited subproblem")

    conclusions = load_table(root, "conclusion_map.csv", {"subproblem", "question", "answer_or_recommendation", "decisive_value_key", "method_rationale_location", "validation_location", "limitation_location", "figure_or_table", "paper_location", "status"}, errors)
    try:
        values, _ = read_csv(root / "results" / "verified_values.csv")
        value_keys = {str(row.get("key") or "").strip() for row in values}
    except (OSError, UnicodeError, csv.Error) as exc:
        value_keys = set()
        errors.append(f"cannot read verified_values.csv: {exc}")
    for line, row in enumerate(conclusions, 2):
        if str(row.get("decisive_value_key") or "") not in value_keys:
            errors.append(f"conclusion_map.csv:{line} decisive_value_key is missing")
    if subproblems - {str(row.get("subproblem") or "") for row in conclusions}:
        errors.append("conclusion_map.csv lacks a mechanism-audited subproblem")

    innovations = load_table(root, "innovation_ledger.csv", {"subproblem", "baseline", "problem_specific_change", "mechanism_target", "added_assumption", "incremental_cost", "comparison_metric", "baseline_value", "innovation_value", "metric_direction", "predeclared_minimum_improvement", "relative_improvement", "validation_artifact", "claim_boundary", "status"}, errors)
    for line, row in enumerate(innovations, 2):
        baseline, innovation = number(row.get("baseline_value")), number(row.get("innovation_value"))
        minimum, reported = number(row.get("predeclared_minimum_improvement")), number(row.get("relative_improvement"))
        direction = str(row.get("metric_direction") or "")
        if None in {baseline, innovation, minimum, reported} or minimum < 0 or direction not in {"lower", "higher"}:
            errors.append(f"innovation_ledger.csv:{line} has invalid comparison metrics")
            continue
        actual = ((baseline - innovation) / max(abs(baseline), 1e-12)) if direction == "lower" else ((innovation - baseline) / max(abs(baseline), 1e-12))
        if abs(actual - reported) > 1e-6:
            errors.append(f"innovation_ledger.csv:{line} relative_improvement is inconsistent")
        if actual < minimum and str(row.get("claim_boundary") or "") not in {"interpretive_only", "rejected"}:
            errors.append(f"innovation_ledger.csv:{line} overclaims an innovation without measured gain")
        artifact = safe(root, str(row.get("validation_artifact") or ""))
        if artifact is None or not artifact.is_file():
            errors.append(f"innovation_ledger.csv:{line} validation_artifact is missing or unsafe")
    if subproblems - {str(row.get("subproblem") or "") for row in innovations}:
        errors.append("innovation_ledger.csv lacks a mechanism-audited subproblem")
    payload = {"status": "PASS" if not errors else "FAIL", "scope": "recorded semantics, validation design, conclusion structure, and innovation evidence; not proof of mathematical truth", "counts": {"semantics": len(semantics), "subproblems": len(subproblems), "validation_designs": len(validations), "conclusions": len(conclusions), "innovations": len(innovations)}, "errors": errors}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
