#!/usr/bin/env python3
"""Score private historical regression evidence without copying its content."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


DIMENSIONS = ("input_audit", "feasibility", "reproducibility", "writing", "visual_communication")
SCORES = {"PASS": 5.0, "LIMITED": 2.0, "FAIL": 0.0}
DEFECT_FIELDS = {"dimension", "category", "severity", "artifact_locator", "status"}
DEFECT_CATEGORIES = {
    "unverifiable_assumption", "unsupported_figure", "decorative_sensitivity",
    "missing_fallback", "causal_overclaim", "weak_implementation",
    "broken_evidence_chain", "layout_readability",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a metadata-only private regression rubric report.")
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--evidence", action="append", default=[], metavar="DIMENSION=RELATIVE_JSON")
    parser.add_argument("--defect-log", help="optional relative CSV with evidence-located defect categories")
    parser.add_argument("--out", default="regression_rubric.json")
    args = parser.parse_args()
    root = args.private_root.resolve()
    supplied: dict[str, Path] = {}
    errors: list[str] = []
    for item in args.evidence:
        dimension, separator, raw_path = item.partition("=")
        path = Path(raw_path)
        if not separator or dimension not in DIMENSIONS or path.is_absolute() or ".." in path.parts:
            errors.append(f"invalid evidence declaration: {item}")
        elif dimension in supplied:
            errors.append(f"duplicate evidence dimension: {dimension}")
        else:
            supplied[dimension] = root / path
    if set(supplied) != set(DIMENSIONS):
        errors.append("exactly one evidence item is required for each rubric dimension")
    rows: dict[str, dict[str, object]] = {}
    for dimension in DIMENSIONS:
        path = supplied.get(dimension)
        if path is None or not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            status = payload.get("status") if isinstance(payload, dict) else None
        except (OSError, UnicodeError, json.JSONDecodeError):
            status = None
        if status not in SCORES:
            errors.append(f"{dimension} evidence must be JSON with status PASS, LIMITED, or FAIL")
            continue
        rows[dimension] = {"status": status, "score": SCORES[status], "sha256": sha256(path)}
    defects: list[dict[str, str]] = []
    if args.defect_log:
        defect_path = Path(args.defect_log)
        if defect_path.is_absolute() or ".." in defect_path.parts:
            errors.append("defect log must stay inside --private-root")
        else:
            try:
                with (root / defect_path).open(encoding="utf-8-sig", newline="") as handle:
                    reader = csv.DictReader(handle)
                    fields = set(reader.fieldnames or [])
                    defects = list(reader)
                if DEFECT_FIELDS - fields:
                    errors.append("defect log missing columns: " + ", ".join(sorted(DEFECT_FIELDS - fields)))
                for index, defect in enumerate(defects, 2):
                    if any(not str(defect.get(field) or "").strip() for field in DEFECT_FIELDS):
                        errors.append(f"defect log row {index} has empty required fields")
                    if defect.get("dimension") not in DIMENSIONS:
                        errors.append(f"defect log row {index} has invalid dimension")
                    if defect.get("category") not in DEFECT_CATEGORIES:
                        errors.append(f"defect log row {index} has invalid category")
                    if defect.get("severity") not in {"minor", "major", "veto"}:
                        errors.append(f"defect log row {index} has invalid severity")
                    if defect.get("status") not in {"open", "resolved", "accepted_limitation"}:
                        errors.append(f"defect log row {index} has invalid status")
            except (OSError, UnicodeError, csv.Error) as exc:
                errors.append(f"cannot read defect log: {exc}")
    status = "FAIL" if errors or any(row["status"] == "FAIL" for row in rows.values()) else ("LIMITED" if any(row["status"] == "LIMITED" for row in rows.values()) else "PASS")
    out = Path(args.out)
    if out.is_absolute() or ".." in out.parts:
        raise SystemExit("output must stay inside --private-root")
    target = root / out
    target.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "case_id": args.case_id,
        "status": status,
        "scope": "metadata-only evidence rubric; no private statement, data, answer, artifact contents, or award prediction is emitted",
        "dimensions": rows,
        "defects": defects,
        "defect_category_counts": {
            category: sum(item.get("category") == category for item in defects)
            for category in sorted(DEFECT_CATEGORIES)
            if any(item.get("category") == category for item in defects)
        },
        "mean_score": sum(float(row["score"]) for row in rows.values()) / len(rows) if len(rows) == len(DIMENSIONS) else None,
        "errors": errors,
    }
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    return 0 if status == "PASS" else (2 if status == "LIMITED" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
