#!/usr/bin/env python3
"""Verify a reviewer-first three-minute paper reading path."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contestlib import read_csv_with_error as read_csv
from contestlib import safe_project_path as safe
from contestlib import sha256_bytes as digest


COMPLETE = {"pass", "complete", "verified"}
FIELDS = {"element", "reader_question", "direct_answer", "evidence_type", "evidence_ref", "paper_location", "status"}
REQUIRED = {"abstract", "route_figure", "core_result", "recommendation", "limitation"}
EVIDENCE_TYPES = {"paper_file", "figure_label", "verified_value", "conclusion_map"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a three-minute reviewer reading path.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/three_minute_review.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    review = root / "reports" / "three_minute_review.csv"
    manifest = root / "reports" / "figure_manifest.csv"
    values = root / "results" / "verified_values.csv"
    conclusions = root / "reports" / "conclusion_map.csv"
    rows, columns, review_error = read_csv(review)
    figure_rows, figure_columns, figure_error = read_csv(manifest)
    value_rows, value_columns, value_error = read_csv(values)
    conclusion_rows, conclusion_columns, conclusion_error = read_csv(conclusions)
    errors: list[str] = []
    for name, error in (("three_minute_review.csv", review_error), ("figure_manifest.csv", figure_error), ("verified_values.csv", value_error), ("conclusion_map.csv", conclusion_error)):
        if error:
            errors.append(f"cannot read {name}: {error}")
    if FIELDS - columns:
        errors.append("three_minute_review.csv missing columns: " + ", ".join(sorted(FIELDS - columns)))
    if "label" not in figure_columns:
        errors.append("figure_manifest.csv missing label column")
    if "key" not in value_columns:
        errors.append("verified_values.csv missing key column")
    if "subproblem" not in conclusion_columns:
        errors.append("conclusion_map.csv missing subproblem column")
    figure_labels = {str(row.get("label") or "").strip() for row in figure_rows}
    value_keys = {str(row.get("key") or "").strip() for row in value_rows}
    subproblems = {str(row.get("subproblem") or "").strip() for row in conclusion_rows}
    observed: set[str] = set()
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in FIELDS):
            errors.append(f"three_minute_review.csv:{line} has empty required evidence")
        element = str(row.get("element") or "").strip()
        observed.add(element)
        if element not in REQUIRED:
            errors.append(f"three_minute_review.csv:{line} has invalid element")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"three_minute_review.csv:{line} is not complete")
        kind = str(row.get("evidence_type") or "").strip()
        ref = str(row.get("evidence_ref") or "").strip()
        if kind not in EVIDENCE_TYPES:
            errors.append(f"three_minute_review.csv:{line} has invalid evidence_type")
        elif kind == "paper_file":
            path = safe(root, ref)
            if path is None or not path.is_file():
                errors.append(f"three_minute_review.csv:{line} paper_file is missing or unsafe")
        elif kind == "figure_label" and ref not in figure_labels:
            errors.append(f"three_minute_review.csv:{line} references an unknown figure label")
        elif kind == "verified_value" and ref not in value_keys:
            errors.append(f"three_minute_review.csv:{line} references an unverified value")
        elif kind == "conclusion_map" and ref not in subproblems:
            errors.append(f"three_minute_review.csv:{line} references an unknown conclusion subproblem")
    missing = REQUIRED - observed
    if missing:
        errors.append("three_minute_review.csv missing elements: " + ", ".join(sorted(missing)))
    if len(rows) != len(observed):
        errors.append("three_minute_review.csv must contain exactly one row per reading-path element")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "declared reviewer reading-path evidence only; human review remains authoritative",
        "review_sha256": digest(review) if review.is_file() else "",
        "figure_manifest_sha256": digest(manifest) if manifest.is_file() else "",
        "verified_values_sha256": digest(values) if values.is_file() else "",
        "conclusion_map_sha256": digest(conclusions) if conclusions.is_file() else "",
        "elements": sorted(observed), "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
