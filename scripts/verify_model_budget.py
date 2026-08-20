#!/usr/bin/env python3
"""Verify a time-bounded and fallback-aware modeling route budget."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contestlib import read_csv_with_error as read_csv
from contestlib import sha256_bytes as digest


COMPLETE = {"pass", "complete", "verified"}
FIELDS = {
    "subproblem", "route_name", "route_type", "selected", "estimated_hours",
    "risk_level", "validation_hours", "fallback_route", "expected_value",
    "deadline_hours", "comparison_metric", "metric_direction", "baseline_value",
    "candidate_value", "minimum_advantage", "validation_artifact",
    "paper_treatment", "status",
}
ROUTE_TYPES = {"baseline", "candidate", "fallback"}
RISK_LEVELS = {"low", "medium", "high"}
METRIC_DIRECTIONS = {"higher", "lower"}
PAPER_TREATMENTS = {
    "primary", "comparison", "rejected", "model_optimization", "fallback",
}


def number(raw: str) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 and value == value and value != float("inf") else None


def finite_number(raw: str) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value == value and abs(value) != float("inf") else None


def project_file(root: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the contest model-route budget.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/model_budget.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    path = root / "reports" / "model_budget.csv"
    rows, columns, read_error = read_csv(path)
    errors: list[str] = []
    if read_error:
        errors.append(f"cannot read model_budget.csv: {read_error}")
    if FIELDS - columns:
        errors.append("model_budget.csv missing columns: " + ", ".join(sorted(FIELDS - columns)))
    by_subproblem: dict[str, list[dict[str, str]]] = {}
    deadlines: set[float] = set()
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in FIELDS):
            errors.append(f"model_budget.csv:{line} has empty required evidence")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"model_budget.csv:{line} is not complete")
        subproblem = str(row.get("subproblem") or "").strip()
        by_subproblem.setdefault(subproblem, []).append(row)
        if str(row.get("route_type") or "").strip().lower() not in ROUTE_TYPES:
            errors.append(f"model_budget.csv:{line} has invalid route_type")
        if str(row.get("selected") or "").strip().lower() not in {"true", "false"}:
            errors.append(f"model_budget.csv:{line} has invalid selected flag")
        if str(row.get("risk_level") or "").strip().lower() not in RISK_LEVELS:
            errors.append(f"model_budget.csv:{line} has invalid risk_level")
        for field in ("estimated_hours", "validation_hours", "deadline_hours"):
            value = number(str(row.get(field) or ""))
            if value is None or (field == "deadline_hours" and value <= 0):
                errors.append(f"model_budget.csv:{line} has invalid {field}")
            elif field == "deadline_hours":
                deadlines.add(value)
    if len(deadlines) > 1:
        errors.append("model_budget.csv must use one shared deadline_hours value")
    selected_total = 0.0
    promotions: list[dict[str, object]] = []
    for subproblem, routes in by_subproblem.items():
        if not subproblem:
            continue
        names = {str(row.get("route_name") or "").strip() for row in routes}
        selected = [row for row in routes if str(row.get("selected") or "").strip().lower() == "true"]
        baselines = [row for row in routes if str(row.get("route_type") or "").strip().lower() == "baseline"]
        if not baselines:
            errors.append(f"model_budget.csv lacks an executable baseline for {subproblem}")
        if len(selected) != 1:
            errors.append(f"model_budget.csv must select exactly one route for {subproblem}")
        for row in selected:
            selected_total += number(str(row.get("estimated_hours") or "")) or 0
            route_type = str(row.get("route_type") or "").strip().lower()
            if route_type != "baseline" and str(row.get("expected_value") or "").strip().lower() in {"", "not_applicable", "n/a"}:
                errors.append(f"model_budget.csv selected non-baseline route for {subproblem} lacks expected_value")
            fallback = str(row.get("fallback_route") or "").strip()
            if fallback not in names or fallback == str(row.get("route_name") or "").strip():
                errors.append(f"model_budget.csv selected route for {subproblem} lacks a distinct listed fallback")
        for row in routes:
            route_type = str(row.get("route_type") or "").strip().lower()
            is_selected = str(row.get("selected") or "").strip().lower() == "true"
            treatment = str(row.get("paper_treatment") or "").strip().lower()
            if treatment not in PAPER_TREATMENTS:
                errors.append(
                    f"model_budget.csv route {row.get('route_name')} for {subproblem} "
                    "has invalid paper_treatment"
                )
            if route_type == "baseline" and is_selected and treatment != "primary":
                errors.append(f"selected baseline for {subproblem} must be primary in the paper")
            if route_type == "fallback" and treatment != "fallback":
                errors.append(f"fallback route for {subproblem} must use paper_treatment=fallback")
            if route_type != "candidate":
                continue
            direction = str(row.get("metric_direction") or "").strip().lower()
            baseline_value = finite_number(str(row.get("baseline_value") or ""))
            candidate_value = finite_number(str(row.get("candidate_value") or ""))
            minimum_advantage = number(str(row.get("minimum_advantage") or ""))
            if not str(row.get("comparison_metric") or "").strip() or direction not in METRIC_DIRECTIONS:
                errors.append(f"candidate route for {subproblem} lacks a valid comparison metric/direction")
            if (
                baseline_value is None
                or candidate_value is None
                or minimum_advantage is None
                or minimum_advantage <= 0
            ):
                errors.append(f"candidate route for {subproblem} lacks numeric promotion evidence")
                improvement = None
            else:
                improvement = (
                    candidate_value - baseline_value
                    if direction == "higher"
                    else baseline_value - candidate_value
                )
            artifact_raw = str(row.get("validation_artifact") or "").strip()
            artifact = project_file(root, artifact_raw)
            if artifact is None or not artifact.is_file():
                errors.append(f"candidate route for {subproblem} lacks a safe existing validation_artifact")
            promoted = (
                improvement is not None
                and minimum_advantage is not None
                and improvement >= minimum_advantage
            )
            if is_selected:
                if treatment != "primary":
                    errors.append(f"selected candidate for {subproblem} must be primary in the paper")
                if not promoted:
                    errors.append(
                        f"selected candidate for {subproblem} does not reach its "
                        "predeclared minimum advantage; retain the simpler route"
                    )
            elif treatment not in {"rejected", "model_optimization"}:
                errors.append(
                    f"unselected candidate for {subproblem} must be rejected or "
                    "placed in model_optimization"
                )
            promotions.append(
                {
                    "subproblem": subproblem,
                    "route_name": str(row.get("route_name") or "").strip(),
                    "metric": str(row.get("comparison_metric") or "").strip(),
                    "direction": direction,
                    "measured_advantage": improvement,
                    "minimum_advantage": minimum_advantage,
                    "selected": is_selected,
                    "promoted": promoted,
                    "paper_treatment": treatment,
                }
            )
    if deadlines and selected_total > next(iter(deadlines)):
        errors.append("model_budget.csv selected routes exceed deadline_hours")
    if not rows:
        errors.append("model_budget.csv has no evidence rows")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "recorded time/risk/fallback planning only; not an automatic estimate of team productivity",
        "model_budget_sha256": digest(path) if path.is_file() else "",
        "selected_hours": selected_total, "deadline_hours": next(iter(deadlines), None),
        "subproblems": len({key for key in by_subproblem if key}),
        "candidate_promotions": promotions,
        "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
