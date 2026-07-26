#!/usr/bin/env python3
"""Require every recorded figure to state its question, claim, and takeaway."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = {"figure", "label", "claim_id", "question_answered", "reader_takeaway", "decision_relevance", "status"}
COMPLETE = {"pass", "complete", "verified"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify figure narrative evidence.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/figure_narrative_verification.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    errors: list[str] = []
    try:
        with (root / "reports" / "figure_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows, fields = list(reader), set(reader.fieldnames or [])
    except (OSError, UnicodeError, csv.Error) as exc:
        rows, fields = [], set()
        errors.append(f"cannot read figure_manifest.csv: {exc}")
    if FIELDS - fields:
        errors.append("figure_manifest.csv missing narrative columns: " + ", ".join(sorted(FIELDS - fields)))
    try:
        with (root / "reports" / "claims.csv").open(encoding="utf-8-sig", newline="") as handle:
            claim_ids = {str(row.get("claim_id") or "").strip() for row in csv.DictReader(handle)}
    except (OSError, UnicodeError, csv.Error) as exc:
        claim_ids = set()
        errors.append(f"cannot read claims.csv: {exc}")
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in FIELDS):
            errors.append(f"figure_manifest.csv:{line} has empty narrative evidence")
        if str(row.get("status") or "").lower() not in COMPLETE:
            errors.append(f"figure_manifest.csv:{line} is not complete")
        if str(row.get("claim_id") or "").strip() not in claim_ids:
            errors.append(f"figure_manifest.csv:{line} references an unknown claim")
    payload = {"status": "PASS" if not errors else "FAIL", "scope": "figure question-claim-takeaway declarations only; rendered-page inspection remains required", "rows": len(rows), "errors": errors}
    out = Path(args.out) if Path(args.out).is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
