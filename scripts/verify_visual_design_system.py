#!/usr/bin/env python3
"""Verify declared visual consistency for figures and tables."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


FIGURE_FIELDS = {
    "figure", "label", "source_data", "caption_insight", "axes_units",
    "color_accessibility", "claim_id", "question_answered", "reader_takeaway",
    "decision_relevance", "visual_role", "style_profile", "palette_or_grayscale",
    "typography_precision", "panel_order", "legibility_evidence", "status",
}
TABLE_FIELDS = {
    "table", "label", "source_data", "caption_insight", "units", "precision",
    "emphasis", "continuation_check", "claim_id", "question_answered",
    "reader_takeaway", "decision_relevance", "style_profile",
    "legibility_evidence", "status",
}
COMPLETE = {"pass", "complete", "verified"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str], str | None]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader), set(reader.fieldnames or []), None
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], set(), str(exc)


def audit(name: str, rows: list[dict[str, str]], fields: set[str], required: set[str], errors: list[str]) -> set[str]:
    if required - fields:
        errors.append(f"{name} missing columns: " + ", ".join(sorted(required - fields)))
    profiles: set[str] = set()
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in required):
            errors.append(f"{name}:{line} has empty design evidence")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"{name}:{line} is not complete")
        profile = str(row.get("style_profile") or "").strip()
        if profile:
            profiles.add(profile)
    if len(profiles) > 1:
        errors.append(f"{name} uses multiple style profiles: {', '.join(sorted(profiles))}")
    return profiles


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify figure/table design-system declarations.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/visual_design_system.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    figure_path = root / "reports/figure_manifest.csv"
    table_path = root / "reports/table_manifest.csv"
    errors: list[str] = []
    figures, figure_fields, figure_error = read_csv(figure_path)
    tables, table_fields, table_error = read_csv(table_path)
    if figure_error:
        errors.append(f"cannot read figure_manifest.csv: {figure_error}")
    if table_error:
        errors.append(f"cannot read table_manifest.csv: {table_error}")
    figure_profiles = audit("figure_manifest.csv", figures, figure_fields, FIGURE_FIELDS, errors)
    table_profiles = audit("table_manifest.csv", tables, table_fields, TABLE_FIELDS, errors)
    combined = figure_profiles | table_profiles
    if len(combined) > 1:
        errors.append("figures and tables do not share one declared style profile")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "declared visual-system consistency only; rendered visual quality requires human review",
        "figure_manifest_sha256": digest(figure_path) if figure_path.is_file() else "",
        "table_manifest_sha256": digest(table_path) if table_path.is_file() else "",
        "figures": len(figures), "tables": len(tables), "style_profiles": sorted(combined),
        "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
