#!/usr/bin/env python3
"""Score timed CUMCM rehearsals without predicting an award."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


RUN_FIELDS = {
    "run_id", "rehearsal_hours", "selection_lock_hour",
    "first_verified_result_hour", "all_subproblem_results_hour",
    "full_draft_hour", "strict_freeze_hour", "submission_rehearsal",
    "unresolved_vetoes", "status",
}
DEFECT_FIELDS = {"run_id", "defect_class", "severity", "evidence", "resolution_status"}


def rows(path: Path, required: set[str], label: str, errors: list[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = required - set(reader.fieldnames or [])
            if missing:
                errors.append(f"{label} missing columns: " + ", ".join(sorted(missing)))
            return list(reader)
    except OSError as exc:
        errors.append(f"cannot read {label}: {exc}")
        return []


def number(row: dict[str, str], field: str, line: int, errors: list[str], *, optional: bool = False) -> float | None:
    raw = row.get(field, "").strip()
    if optional and not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        errors.append(f"training_runs.csv:{line} {field} must be numeric")
        return None
    if value < 0:
        errors.append(f"training_runs.csv:{line} {field} cannot be negative")
    return value


def score(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    run_rows = rows(root / "reports" / "training_runs.csv", RUN_FIELDS, "training_runs.csv", errors)
    defect_rows = rows(root / "reports" / "training_defects.csv", DEFECT_FIELDS, "training_defects.csv", errors)
    if not run_rows:
        errors.append("at least one timed rehearsal is required")
    run_ids: set[str] = set()
    run_reports: list[dict[str, Any]] = []
    metrics: dict[str, list[float]] = {
        "selection_lock_hour": [], "first_verified_result_hour": [],
        "all_subproblem_results_hour": [], "full_draft_hour": [],
        "strict_freeze_hour": [],
    }
    full_pass = False
    for line, row in enumerate(run_rows, 2):
        run_id = row.get("run_id", "").strip()
        if not run_id or run_id in run_ids:
            errors.append(f"training_runs.csv:{line} has a blank or duplicate run_id")
        run_ids.add(run_id)
        hours_value = number(row, "rehearsal_hours", line, errors)
        hours = int(hours_value or 0)
        if hours not in {8, 24, 48, 74}:
            errors.append(f"training_runs.csv:{line} rehearsal_hours must be 8, 24, 48, or 74")
        values = {
            field: number(row, field, line, errors, optional=field in {"full_draft_hour", "strict_freeze_hour"})
            for field in metrics
        }
        for field, value in values.items():
            if value is not None:
                metrics[field].append(value)
        vetoes = number(row, "unresolved_vetoes", line, errors)
        checks = [
            values["selection_lock_hour"] is not None and values["selection_lock_hour"] <= 6,
            values["first_verified_result_hour"] is not None and values["first_verified_result_hour"] <= min(hours, 12),
        ]
        if hours >= 24:
            checks.append(values["all_subproblem_results_hour"] is not None and values["all_subproblem_results_hour"] <= (24 if hours == 24 else 36))
        if hours >= 48:
            checks.append(values["full_draft_hour"] is not None and values["full_draft_hour"] <= (48 if hours == 48 else 64))
        if hours == 74:
            checks.extend(
                [
                    values["strict_freeze_hour"] is not None and values["strict_freeze_hour"] <= 70,
                    row.get("submission_rehearsal", "").strip().lower() == "yes",
                    vetoes == 0,
                ]
            )
        passed = all(checks) and row.get("status", "").strip() == "complete"
        full_pass = full_pass or (hours == 74 and passed)
        run_reports.append({"run_id": run_id, "rehearsal_hours": hours, "status": "PASS" if passed else "FAIL"})

    defect_counts: Counter[str] = Counter()
    open_critical: list[str] = []
    for line, row in enumerate(defect_rows, 2):
        defect = row.get("defect_class", "").strip()
        if not defect or row.get("run_id", "").strip() not in run_ids:
            errors.append(f"training_defects.csv:{line} has an invalid run_id or defect_class")
            continue
        severity = row.get("severity", "").strip()
        resolution = row.get("resolution_status", "").strip()
        if severity not in {"critical", "major", "minor"}:
            errors.append(f"training_defects.csv:{line} severity is invalid")
        if resolution not in {"open", "resolved", "accepted"}:
            errors.append(f"training_defects.csv:{line} resolution_status is invalid")
        if not row.get("evidence", "").strip():
            errors.append(f"training_defects.csv:{line} evidence is missing")
        defect_counts[defect] += 1
        if severity == "critical" and resolution == "open":
            open_critical.append(defect)
    repeated = {key: value for key, value in sorted(defect_counts.items()) if value >= 2}
    medians = {
        field: statistics.median(values) if values else None
        for field, values in metrics.items()
    }
    if errors or open_critical:
        status, state = "FAIL", "not_ready"
    elif full_pass:
        status, state = "PASS", "ready"
    else:
        status, state = "LIMITED", "partial"
    return {
        "status": status,
        "readiness_state": state,
        "scope": "timed rehearsal evidence; not mathematical truth or an award prediction",
        "runs": run_reports,
        "milestone_medians": medians,
        "repeated_defects": repeated,
        "open_critical_defects": sorted(open_critical),
        "trend_direction": "insufficient_runs" if len(run_rows) < 3 else "review_milestone_medians",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    report = score(root)
    out = args.out.resolve()
    try:
        out.relative_to(root / "reports")
    except ValueError as exc:
        raise SystemExit("--out must stay inside project reports") from exc
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
