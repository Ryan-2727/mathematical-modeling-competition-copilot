#!/usr/bin/env python3
"""Verify that decisive figures retain a numeric evidence contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contestlib import read_csv_with_error as read_csv
from contestlib import safe_project_path as safe
from contestlib import sha256_bytes as digest


COMPLETE = {"pass", "complete", "verified"}
FIELDS = {
    "figure", "label", "source_data", "data_sha256", "axis_x", "axis_y",
    "axis_scale", "x_limits", "y_limits", "value_transform",
    "decisive_value_keys", "paper_location", "status",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify numeric figure contracts.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/figure_numeric_contract.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    contract = root / "reports" / "figure_numeric_contract.csv"
    manifest = root / "reports" / "figure_manifest.csv"
    values = root / "results" / "verified_values.csv"
    rows, columns, read_error = read_csv(contract)
    manifest_rows, manifest_columns, manifest_error = read_csv(manifest)
    value_rows, value_columns, value_error = read_csv(values)
    errors: list[str] = []
    for name, error in (("figure_numeric_contract.csv", read_error), ("figure_manifest.csv", manifest_error), ("verified_values.csv", value_error)):
        if error:
            errors.append(f"cannot read {name}: {error}")
    if FIELDS - columns:
        errors.append("figure_numeric_contract.csv missing columns: " + ", ".join(sorted(FIELDS - columns)))
    if {"label", "source_data"} - manifest_columns:
        errors.append("figure_manifest.csv missing label/source_data columns")
    if "key" not in value_columns:
        errors.append("verified_values.csv missing key column")
    manifest_by_label = {str(row.get("label") or "").strip(): row for row in manifest_rows}
    verified_keys = {str(row.get("key") or "").strip() for row in value_rows}
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in FIELDS):
            errors.append(f"figure_numeric_contract.csv:{line} has empty required evidence")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"figure_numeric_contract.csv:{line} is not complete")
        label = str(row.get("label") or "").strip()
        manifest_row = manifest_by_label.get(label)
        if manifest_row is None:
            errors.append(f"figure_numeric_contract.csv:{line} references an unknown figure label")
        elif str(manifest_row.get("source_data") or "").strip() != str(row.get("source_data") or "").strip():
            errors.append(f"figure_numeric_contract.csv:{line} source_data does not match figure_manifest.csv")
        data = safe(root, str(row.get("source_data") or ""))
        if data is None or not data.is_file():
            errors.append(f"figure_numeric_contract.csv:{line} source_data is missing or unsafe")
        elif digest(data) != str(row.get("data_sha256") or "").strip().lower():
            errors.append(f"figure_numeric_contract.csv:{line} data_sha256 is stale")
        keys = [item.strip() for item in str(row.get("decisive_value_keys") or "").split(";") if item.strip()]
        if not keys:
            errors.append(f"figure_numeric_contract.csv:{line} has no decisive_value_keys")
        for key in keys:
            if key not in verified_keys:
                errors.append(f"figure_numeric_contract.csv:{line} references an unverified value: {key}")
    if not rows:
        errors.append("figure_numeric_contract.csv has no evidence rows")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "declared data-to-figure numeric traceability only; not rendered-chart aesthetic review",
        "contract_sha256": digest(contract) if contract.is_file() else "",
        "figure_manifest_sha256": digest(manifest) if manifest.is_file() else "",
        "verified_values_sha256": digest(values) if values.is_file() else "",
        "figures": len(rows), "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
