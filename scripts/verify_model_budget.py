#!/usr/bin/env python3
"""Verify a time-bounded and fallback-aware modeling route budget."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


COMPLETE = {"pass", "complete", "verified"}
FIELDS = {
    "subproblem", "route_name", "route_type", "selected", "estimated_hours",
    "risk_level", "validation_hours", "fallback_route", "expected_value",
    "deadline_hours", "status",
}
ROUTE_TYPES = {"baseline", "candidate", "fallback"}
RISK_LEVELS = {"low", "medium", "high"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(raw: str) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 and value == value and value != float("inf") else None


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str], str | None]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader), set(reader.fieldnames or []), None
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], set(), str(exc)


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
            if str(row.get("route_type") or "").strip().lower() != "baseline" and str(row.get("expected_value") or "").strip().lower() in {"", "not_applicable", "n/a"}:
                errors.append(f"model_budget.csv selected non-baseline route for {subproblem} lacks expected_value")
            fallback = str(row.get("fallback_route") or "").strip()
            if fallback not in names or fallback == str(row.get("route_name") or "").strip():
                errors.append(f"model_budget.csv selected route for {subproblem} lacks a distinct listed fallback")
    if deadlines and selected_total > next(iter(deadlines)):
        errors.append("model_budget.csv selected routes exceed deadline_hours")
    if not rows:
        errors.append("model_budget.csv has no evidence rows")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "recorded time/risk/fallback planning only; not an automatic estimate of team productivity",
        "model_budget_sha256": digest(path) if path.is_file() else "",
        "selected_hours": selected_total, "deadline_hours": next(iter(deadlines), None),
        "subproblems": len({key for key in by_subproblem if key}), "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
