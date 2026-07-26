#!/usr/bin/env python3
"""Check model challenge, uncertainty, fallback, causal, and implementation evidence."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


COMPLETE = {"pass", "complete", "verified"}
CSV_FIELDS = {
    "decision_robustness.csv": {"decision_id", "uncertainty_material", "comparison_type", "scenario_count", "expected_value", "worst_case_value", "extreme_feasibility_rate", "policy_changed", "interpretation", "status"},
    "implementation_readiness.csv": {"decision_id", "implementation_steps", "required_inputs", "execution_cost", "execution_time", "interpretability", "extreme_feasibility_rate", "failure_mode", "contingency", "paper_location", "status"},
    "fallback_plan.csv": {"subproblem", "model_family", "failure_mode", "trigger", "primary_route", "fallback_route", "boundary_statement", "result_file", "paper_location", "status"},
    "causal_claims.csv": {"claim_id", "claim_type", "estimand", "causal_graph", "confounders", "counterfactual", "identification_strategy", "diagnostic", "limitation", "paper_location", "status"},
}


def safe(root: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify award-oriented decision-quality evidence.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/decision_quality.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    out = safe(root, args.out)
    if out is None:
        raise SystemExit("output must stay inside --project-dir")
    errors: list[str] = []
    challenge_path = root / "reports" / "model_challenge.json"
    try:
        challenge = json.loads(challenge_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        challenge = {}
        errors.append(f"cannot read model_challenge.json: {exc}")
    challenges = challenge.get("subproblems") if isinstance(challenge, dict) else None
    if not isinstance(challenges, list) or not challenges:
        errors.append("model_challenge.json requires non-empty subproblems")
        challenges = []
    challenge_subproblems: set[str] = set()
    required = {"subproblem", "baseline_name", "candidate_name", "metric_direction", "baseline_metric", "candidate_metric", "minimum_relative_improvement", "falsification_test", "falsification_result", "result_file", "selected_route", "conclusion_status"}
    for index, row in enumerate(challenges, 1):
        if not isinstance(row, dict) or any(not str(row.get(field) or "").strip() for field in required):
            errors.append(f"model_challenge subproblem {index} lacks required evidence")
            continue
        challenge_subproblems.add(str(row["subproblem"]).strip())
        baseline, candidate, threshold = number(row.get("baseline_metric")), number(row.get("candidate_metric")), number(row.get("minimum_relative_improvement"))
        direction = row.get("metric_direction")
        if direction not in {"lower", "higher"} or baseline is None or candidate is None or threshold is None or threshold < 0:
            errors.append(f"model_challenge subproblem {index} has invalid comparison metrics")
            continue
        improvement = ((baseline - candidate) / max(abs(baseline), 1e-12)) if direction == "lower" else ((candidate - baseline) / max(abs(baseline), 1e-12))
        selected = str(row.get("selected_route"))
        verdict = str(row.get("conclusion_status"))
        if selected == "candidate" and improvement < threshold and verdict not in {"claim_narrowed", "mechanism_justified"}:
            errors.append(f"model_challenge subproblem {index} keeps an unsupported candidate claim")
        result = safe(root, str(row.get("result_file") or ""))
        if result is None or not result.is_file():
            errors.append(f"model_challenge subproblem {index} result_file is missing or unsafe")

    parsed: dict[str, list[dict[str, str]]] = {}
    for name, fields in CSV_FIELDS.items():
        path = root / "reports" / name
        try:
            rows, actual = read_csv(path)
        except (OSError, UnicodeError, csv.Error) as exc:
            rows, actual = [], set()
            errors.append(f"cannot read {name}: {exc}")
        parsed[name] = rows
        if fields - actual:
            errors.append(f"{name} missing columns: " + ", ".join(sorted(fields - actual)))
        if name != "causal_claims.csv" and not rows:
            errors.append(f"{name} has no evidence rows")
        for line, row in enumerate(rows, 2):
            if any(not str(row.get(field) or "").strip() for field in fields):
                errors.append(f"{name}:{line} has empty required fields")
            if str(row.get("status") or "").lower() not in COMPLETE:
                errors.append(f"{name}:{line} is not complete")
    for line, row in enumerate(parsed["decision_robustness.csv"], 2):
        material = str(row.get("uncertainty_material") or "").lower()
        comparison = str(row.get("comparison_type") or "").lower()
        count, feasibility = number(row.get("scenario_count")), number(row.get("extreme_feasibility_rate"))
        if material not in {"true", "false"} or count is None or feasibility is None or not 0 <= feasibility <= 1:
            errors.append(f"decision_robustness.csv:{line} has invalid uncertainty values")
        if material == "true" and (comparison not in {"robust", "stochastic", "scenario"} or count < 2):
            errors.append(f"decision_robustness.csv:{line} lacks a material-uncertainty comparison")
    fallback_subproblems = {str(row.get("subproblem") or "").strip() for row in parsed["fallback_plan.csv"]}
    for subproblem in challenge_subproblems - fallback_subproblems:
        errors.append(f"fallback_plan.csv lacks a degradation route for {subproblem}")
    for line, row in enumerate(parsed["fallback_plan.csv"], 2):
        result = safe(root, str(row.get("result_file") or ""))
        if result is None or not result.is_file():
            errors.append(f"fallback_plan.csv:{line} result_file is missing or unsafe")
    for line, row in enumerate(parsed["causal_claims.csv"], 2):
        kind = str(row.get("claim_type") or "").lower()
        if kind not in {"causal", "predictive", "association"}:
            errors.append(f"causal_claims.csv:{line} has invalid claim_type")
        if kind == "causal":
            for field in ("estimand", "causal_graph", "confounders", "counterfactual", "identification_strategy", "diagnostic"):
                if str(row.get(field) or "").strip().lower() in {"n/a", "not_applicable"}:
                    errors.append(f"causal_claims.csv:{line} causal claim lacks {field}")
        elif "causal" not in str(row.get("limitation") or "").lower():
            errors.append(f"causal_claims.csv:{line} non-causal claim must state its causal limitation")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "recorded model challenge, uncertainty, fallback, causal, and implementation evidence; not an award prediction",
        "counts": {"model_challenges": len(challenges), **{name: len(rows) for name, rows in parsed.items()}},
        "errors": errors,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
