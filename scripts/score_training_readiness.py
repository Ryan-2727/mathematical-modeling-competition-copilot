#!/usr/bin/env python3
"""Score timed CUMCM rehearsals with trend and tail-risk evidence."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RUN_FIELDS = {
    "run_id", "rehearsal_hours", "selection_lock_hour",
    "first_verified_result_hour", "all_subproblem_results_hour",
    "full_draft_hour", "strict_freeze_hour", "submission_rehearsal",
    "unresolved_vetoes", "status",
}
DEFECT_FIELDS = {"run_id", "defect_class", "severity", "evidence", "resolution_status"}
ROLE_FIELDS = {
    "run_id", "role", "owner", "planned_complete_hour", "actual_complete_hour",
    "handoff_evidence", "backup_owner", "status",
}
METRIC_TARGETS = {
    "selection_lock_hour": 6.0,
    "first_verified_result_hour": 12.0,
    "all_subproblem_results_hour": 24.0,
    "full_draft_hour": 64.0,
    "strict_freeze_hour": 70.0,
}


def rows(
    path: Path,
    required: set[str],
    label: str,
    errors: list[str],
    *,
    optional_missing: bool = False,
) -> list[dict[str, str]]:
    if optional_missing and not path.is_file():
        return []
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
        errors.append(f"row {line} {field} must be numeric")
        return None
    if value < 0:
        errors.append(f"row {line} {field} cannot be negative")
    return value


def nearest_rank_p90(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)]


def latest_three_slope(values: list[float]) -> float | None:
    recent = values[-3:]
    if len(recent) < 3:
        return None
    mean_x = 1.0
    mean_y = statistics.mean(recent)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in enumerate(recent))
    denominator = sum((x - mean_x) ** 2 for x in range(3))
    return numerator / denominator


def direction(slope: float | None) -> str:
    if slope is None:
        return "insufficient_runs"
    if slope < -0.05:
        return "improving"
    if slope > 0.05:
        return "deteriorating"
    return "stable"


def metric_report(values: list[float], target: float) -> dict[str, Any]:
    median = statistics.median(values) if values else None
    p90 = nearest_rank_p90(values)
    worst = max(values) if values else None
    slope = latest_three_slope(values)
    return {
        "sample_count": len(values),
        "median": median,
        "p90_nearest_rank": p90,
        "worst": worst,
        "latest_three_slope_hours_per_run": slope,
        "trend": direction(slope),
        "target_hour": target,
        "p90_safety_margin_hours": target - p90 if p90 is not None else None,
        "worst_safety_margin_hours": target - worst if worst is not None else None,
    }


def score(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    run_rows = rows(root / "reports" / "training_runs.csv", RUN_FIELDS, "training_runs.csv", errors)
    defect_rows = rows(root / "reports" / "training_defects.csv", DEFECT_FIELDS, "training_defects.csv", errors)
    role_rows = rows(
        root / "reports" / "training_roles.csv",
        ROLE_FIELDS,
        "training_roles.csv",
        errors,
        optional_missing=True,
    )
    if not run_rows:
        errors.append("at least one timed rehearsal is required")
    run_ids: set[str] = set()
    run_order: dict[str, int] = {}
    run_reports: list[dict[str, Any]] = []
    metrics: dict[str, list[float]] = {field: [] for field in METRIC_TARGETS}
    full_runs: list[dict[str, Any]] = []
    for line, row in enumerate(run_rows, 2):
        run_id = row.get("run_id", "").strip()
        if not run_id or run_id in run_ids:
            errors.append(f"training_runs.csv:{line} has a blank or duplicate run_id")
        run_ids.add(run_id)
        run_order[run_id] = line
        hours_value = number(row, "rehearsal_hours", line, errors)
        hours = int(hours_value or 0)
        if hours not in {8, 24, 48, 74}:
            errors.append(f"training_runs.csv:{line} rehearsal_hours must be 8, 24, 48, or 74")
        values = {
            field: number(
                row, field, line, errors,
                optional=field in {"full_draft_hour", "strict_freeze_hour"},
            )
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
            checks.append(
                values["all_subproblem_results_hour"] is not None
                and values["all_subproblem_results_hour"] <= 24
            )
        if hours >= 48:
            checks.append(
                values["full_draft_hour"] is not None
                and values["full_draft_hour"] <= (48 if hours == 48 else 64)
            )
        if hours == 74:
            checks.extend(
                [
                    values["strict_freeze_hour"] is not None and values["strict_freeze_hour"] <= 70,
                    row.get("submission_rehearsal", "").strip().lower() == "yes",
                    vetoes == 0,
                ]
            )
        passed = all(checks) and row.get("status", "").strip() == "complete"
        report = {
            "run_id": run_id,
            "rehearsal_hours": hours,
            "status": "PASS" if passed else "FAIL",
        }
        run_reports.append(report)
        if hours == 74:
            full_runs.append(report)

    required_roles = {"selection", "modeling", "paper", "submission"}
    full_run_ids = {report["run_id"] for report in full_runs}
    role_coverage: dict[str, set[str]] = defaultdict(set)
    role_delays: dict[str, list[float]] = defaultdict(list)
    owner_delays: dict[str, list[float]] = defaultdict(list)
    role_blockers: Counter[str] = Counter()
    for line, row in enumerate(role_rows, 2):
        run_id = row.get("run_id", "").strip()
        role = row.get("role", "").strip()
        owner = row.get("owner", "").strip()
        backup = row.get("backup_owner", "").strip()
        if run_id not in run_ids or not role or not owner:
            errors.append(f"training_roles.csv:{line} has an invalid run_id, role, or owner")
            continue
        planned = number(row, "planned_complete_hour", line, errors)
        actual = number(row, "actual_complete_hour", line, errors)
        if not row.get("handoff_evidence", "").strip():
            errors.append(f"training_roles.csv:{line} handoff_evidence is missing")
        if not backup or backup == owner:
            errors.append(f"training_roles.csv:{line} needs a distinct backup_owner")
        status_value = row.get("status", "").strip()
        if status_value not in {"complete", "blocked"}:
            errors.append(f"training_roles.csv:{line} status must be complete or blocked")
        if planned is not None and actual is not None:
            delay = actual - planned
            role_delays[role].append(delay)
            owner_delays[owner].append(delay)
        if status_value == "blocked":
            role_blockers[role] += 1
            if run_id in full_run_ids:
                errors.append(
                    f"full rehearsal {run_id} has a blocked {role} role handoff"
                )
        elif status_value == "complete" and run_id in full_run_ids:
            role_coverage[run_id].add(role)
    for run_id in sorted(full_run_ids):
        missing = sorted(required_roles - role_coverage.get(run_id, set()))
        if missing:
            errors.append(
                f"full rehearsal {run_id} missing role handoff evidence: "
                + ", ".join(missing)
            )

    def delay_summary(values: list[float]) -> dict[str, float]:
        return {
            "mean_delay_hours": statistics.mean(values),
            "worst_delay_hours": max(values),
        }

    role_bottlenecks = {
        role: delay_summary(values) for role, values in sorted(role_delays.items())
    }
    owner_bottlenecks = {
        owner: delay_summary(values) for owner, values in sorted(owner_delays.items())
    }

    defect_counts: Counter[str] = Counter()
    defect_run_sets: dict[str, set[str]] = defaultdict(set)
    defect_history: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    open_critical: list[str] = []
    for line, row in enumerate(defect_rows, 2):
        defect = row.get("defect_class", "").strip()
        run_id = row.get("run_id", "").strip()
        if not defect or run_id not in run_ids:
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
        defect_run_sets[defect].add(run_id)
        defect_history[defect].append((run_order[run_id], resolution, run_id))
        if severity == "critical" and resolution == "open":
            open_critical.append(defect)
    repeated = {key: value for key, value in sorted(defect_counts.items()) if value >= 2}
    recurrence_counts = {
        key: max(0, len(runs) - 1)
        for key, runs in sorted(defect_run_sets.items())
        if len(runs) >= 2
    }
    reopened: dict[str, list[str]] = {}
    for defect, history in sorted(defect_history.items()):
        resolved_seen = False
        reopened_runs: list[str] = []
        for _, resolution, run_id in sorted(history):
            if resolution in {"resolved", "accepted"}:
                resolved_seen = True
            elif resolution == "open" and resolved_seen:
                reopened_runs.append(run_id)
        if reopened_runs:
            reopened[defect] = reopened_runs

    milestone_statistics = {
        field: metric_report(values, METRIC_TARGETS[field])
        for field, values in metrics.items()
    }
    medians = {
        field: report["median"] for field, report in milestone_statistics.items()
    }
    trends = [
        report["trend"]
        for report in milestone_statistics.values()
        if report["trend"] != "insufficient_runs"
    ]
    if not trends:
        overall_trend = "insufficient_runs"
    elif "deteriorating" in trends and "improving" in trends:
        overall_trend = "mixed"
    elif "deteriorating" in trends:
        overall_trend = "deteriorating"
    elif "improving" in trends:
        overall_trend = "improving"
    else:
        overall_trend = "stable"

    consecutive_full_passes = 0
    for report in reversed(full_runs):
        if report["status"] != "PASS":
            break
        consecutive_full_passes += 1
    if errors or open_critical:
        status, state = "FAIL", "not_ready"
    elif consecutive_full_passes >= 2:
        status, state = "PASS", "ready"
    elif consecutive_full_passes == 1:
        status, state = "LIMITED", "provisional"
    elif any(report["status"] == "PASS" for report in full_runs):
        status, state = "LIMITED", "unstable"
    else:
        status, state = "LIMITED", "partial"
    return {
        "status": status,
        "readiness_state": state,
        "scope": "timed rehearsal trend and tail-risk evidence; not mathematical truth or an award prediction",
        "runs": run_reports,
        "milestone_medians": medians,
        "milestone_statistics": milestone_statistics,
        "repeated_defects": repeated,
        "defect_recurrence_counts": recurrence_counts,
        "reopened_after_resolution": reopened,
        "defect_recurrence_rate": (
            len(recurrence_counts) / len(defect_run_sets) if defect_run_sets else 0.0
        ),
        "open_critical_defects": sorted(open_critical),
        "role_bottlenecks": role_bottlenecks,
        "owner_bottlenecks": owner_bottlenecks,
        "blocked_role_counts": dict(sorted(role_blockers.items())),
        "full_rehearsal_role_coverage": {
            run_id: sorted(role_coverage.get(run_id, set()))
            for run_id in sorted(full_run_ids)
        },
        "full_rehearsal_count": len(full_runs),
        "consecutive_full_passes": consecutive_full_passes,
        "required_consecutive_full_passes": 2,
        "trend_direction": overall_trend,
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
