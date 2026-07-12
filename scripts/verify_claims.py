#!/usr/bin/env python3
"""Validate claim and argument ledgers before a contest-paper freeze."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


CLAIM_FIELDS = {"claim_id", "subproblem", "claim", "source_file", "source_locator", "command", "figure_or_table", "paper_location", "human_verification", "status"}
ARGUMENT_FIELDS = {"subproblem", "need_or_mechanism", "model", "solution", "quantified_result", "interpretation", "validation", "status"}


def rows(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    if not path.exists(): return [], set()
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir
    errors: list[str] = []
    claims, claim_fields = rows(root / "reports" / "claims.csv")
    arguments, argument_fields = rows(root / "reports" / "argument_coverage.csv")
    if CLAIM_FIELDS - claim_fields: errors.append("claims.csv missing columns: " + ", ".join(sorted(CLAIM_FIELDS - claim_fields)))
    if ARGUMENT_FIELDS - argument_fields: errors.append("argument_coverage.csv missing columns: " + ", ".join(sorted(ARGUMENT_FIELDS - argument_fields)))
    for index, row in enumerate(claims, 2):
        if any(not row.get(field, "").strip() for field in CLAIM_FIELDS): errors.append(f"claims.csv:{index} has empty required fields")
        source = root / row.get("source_file", "")
        if row.get("source_file") and not source.is_file(): errors.append(f"claims.csv:{index} source missing: {row['source_file']}")
        if row.get("status", "").lower() not in {"verified", "pass"}: errors.append(f"claims.csv:{index} is not verified")
    for index, row in enumerate(arguments, 2):
        if any(not row.get(field, "").strip() for field in ARGUMENT_FIELDS): errors.append(f"argument_coverage.csv:{index} has empty required fields")
        if row.get("status", "").lower() not in {"complete", "pass"}: errors.append(f"argument_coverage.csv:{index} is not complete")
    payload = {"status": "PASS" if not errors else "FAIL", "claim_rows": len(claims), "argument_rows": len(arguments), "errors": errors}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__": raise SystemExit(main())
