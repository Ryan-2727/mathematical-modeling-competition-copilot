#!/usr/bin/env python3
"""Verify measured primary and fallback compute-budget evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


FIELDS = {
    "model_id",
    "selected",
    "primary_run_ids",
    "fallback_run_id",
    "required_scale_count",
    "single_scale_reason",
    "remaining_time_seconds",
    "solver_gap_required",
    "status",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def record_hash(record: dict[str, Any]) -> str:
    candidate = dict(record)
    candidate.pop("record_sha256", None)
    canonical = json.dumps(
        candidate,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    try:
        common = os.path.commonpath((os.path.normcase(str(root)), os.path.normcase(str(target))))
    except ValueError as exc:
        raise ValueError(f"path is outside project root: {relative}") from exc
    if common != os.path.normcase(str(root)):
        raise ValueError(f"path is outside project root: {relative}")
    return target


def load_runs(root: Path, path: Path, errors: list[str], warnings: list[str]) -> dict[str, dict[str, Any]]:
    runs: dict[str, dict[str, Any]] = {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read compute runs: {exc}")
        return runs
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("record must be an object")
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"compute_runs.jsonl line {line_number}: {exc}")
            continue
        run_id = str(record.get("run_id") or "").strip()
        if not run_id or run_id in runs:
            errors.append(f"compute_runs.jsonl line {line_number} has missing or duplicate run_id")
            continue
        expected_hash = record_hash(record)
        if record.get("record_sha256") != expected_hash:
            errors.append(f"run {run_id} has a stale record hash")
        artifact_relative = str(record.get("result_artifact") or "").strip()
        try:
            artifact = safe_file(root, artifact_relative)
        except ValueError as exc:
            errors.append(f"run {run_id}: {exc}")
            artifact = Path()
        if not artifact_relative or not artifact.is_file():
            errors.append(f"run {run_id} result artifact is missing")
        elif record.get("result_artifact_sha256") != sha256_file(artifact):
            errors.append(f"run {run_id} result artifact hash is stale")
        memory = record.get("memory")
        if not isinstance(memory, dict) or memory.get("status") not in {"PASS", "LIMITED"}:
            errors.append(f"run {run_id} has invalid memory evidence")
        elif memory.get("status") == "LIMITED":
            warnings.append(f"run {run_id} has limited peak-memory evidence")
        runs[run_id] = record
    return runs


def yes(value: Any) -> bool:
    return str(value or "").strip().casefold() in {"yes", "true", "1"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--budget", default="reports/compute_budget.csv")
    parser.add_argument("--runs", default="reports/compute_runs.jsonl")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    root = args.project_dir.resolve()
    budget_path = safe_file(root, args.budget)
    runs_path = safe_file(root, args.runs)
    out = args.out or root / "reports" / "compute_budget_verification.json"
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, str]] = []
    try:
        with budget_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or not FIELDS <= set(reader.fieldnames):
                missing = sorted(FIELDS - set(reader.fieldnames or []))
                errors.append("compute_budget.csv missing fields: " + ", ".join(missing))
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot read compute budget: {exc}")
    runs = load_runs(root, runs_path, errors, warnings)
    selected_rows = [row for row in rows if yes(row.get("selected"))]
    if not selected_rows:
        errors.append("compute budget has no selected model")
    seen_models: set[str] = set()
    for row_number, row in enumerate(selected_rows, 2):
        model_id = str(row.get("model_id") or "").strip()
        prefix = f"selected row {row_number}"
        if not model_id or model_id in seen_models:
            errors.append(f"{prefix} has missing or duplicate model_id")
        seen_models.add(model_id)
        if str(row.get("status") or "").strip().casefold() not in {"verified", "complete"}:
            errors.append(f"{prefix} is not verified")
        primary_ids = [value.strip() for value in str(row.get("primary_run_ids") or "").split(";") if value.strip()]
        fallback_id = str(row.get("fallback_run_id") or "").strip()
        try:
            required_scales = int(str(row.get("required_scale_count") or ""))
            remaining = float(str(row.get("remaining_time_seconds") or ""))
            if required_scales < 1 or remaining <= 0 or not math.isfinite(remaining):
                raise ValueError
        except ValueError:
            errors.append(f"{prefix} has invalid scale count or remaining time")
            continue
        if required_scales == 1 and not str(row.get("single_scale_reason") or "").strip():
            errors.append(f"{prefix} requires a reason for single-scale evidence")
        if required_scales > 1 and len(primary_ids) < required_scales:
            errors.append(f"{prefix} lacks the declared number of primary runs")
        primary_runs: list[dict[str, Any]] = []
        for run_id in primary_ids:
            record = runs.get(run_id)
            if record is None:
                errors.append(f"{prefix} references missing primary run {run_id}")
                continue
            primary_runs.append(record)
            if record.get("model_id") != model_id or record.get("role") != "primary":
                errors.append(f"primary run {run_id} has the wrong model or role")
            if record.get("status") != "PASS":
                errors.append(f"primary run {run_id} did not pass")
        scales = {str(record.get("scale_label")) for record in primary_runs}
        if len(scales) < required_scales:
            errors.append(f"{prefix} has only {len(scales)} distinct measured scales")
        if primary_runs and not scales.intersection({"representative", "full"}):
            errors.append(f"{prefix} lacks a representative or full-scale primary run")
        fallback = runs.get(fallback_id)
        if fallback is None:
            errors.append(f"{prefix} references missing fallback run {fallback_id or '<empty>'}")
        else:
            if fallback.get("model_id") != model_id or fallback.get("role") != "fallback":
                errors.append(f"fallback run {fallback_id} has the wrong model or role")
            if fallback.get("status") != "PASS":
                errors.append(f"fallback run {fallback_id} did not pass")
        budget_runs = primary_runs + ([fallback] if isinstance(fallback, dict) else [])
        for record in budget_runs:
            run_id = str(record.get("run_id"))
            aggregate = record.get("aggregate")
            wall = aggregate.get("wall_seconds_max") if isinstance(aggregate, dict) else None
            if not isinstance(wall, (int, float)) or not math.isfinite(float(wall)):
                errors.append(f"run {run_id} lacks finite wall-time evidence")
            elif float(wall) > remaining:
                errors.append(f"run {run_id} exceeds the declared remaining-time budget")
            timeout = record.get("timeout_seconds")
            if not isinstance(timeout, (int, float)) or float(timeout) <= 0:
                errors.append(f"run {run_id} lacks an explicit timeout")
            elif float(timeout) > remaining:
                errors.append(f"run {run_id} timeout exceeds the declared remaining time")
            run_remaining = record.get("remaining_time_seconds")
            if (
                not isinstance(run_remaining, (int, float))
                or not math.isfinite(float(run_remaining))
                or float(run_remaining) <= 0
            ):
                errors.append(f"run {run_id} lacks measured remaining-time context")
            elif isinstance(wall, (int, float)) and float(wall) > float(run_remaining):
                errors.append(f"run {run_id} exceeded its recorded remaining-time context")
        if yes(row.get("solver_gap_required")):
            for record in budget_runs:
                run_id = str(record.get("run_id"))
                solver_status = str(record.get("solver_status") or "").strip().casefold()
                gap = record.get("solver_gap")
                if solver_status in {"", "not_applicable", "unknown"}:
                    errors.append(f"run {run_id} lacks solver status")
                if not isinstance(gap, (int, float)) or float(gap) < 0 or not math.isfinite(float(gap)):
                    errors.append(f"run {run_id} lacks a finite nonnegative solver gap")

    status = "FAIL" if errors else "PASS"
    payload = {
        "schema_version": 1,
        "status": status,
        "compute_budget_sha256": sha256_file(budget_path) if budget_path.is_file() else "",
        "compute_runs_sha256": sha256_file(runs_path) if runs_path.is_file() else "",
        "selected_model_count": len(selected_rows),
        "run_count": len(runs),
        "errors": errors,
        "warnings": warnings,
        "scope_limitation": "Measured runs bound observed commands and artifacts; they do not prove asymptotic complexity or global optimality.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
