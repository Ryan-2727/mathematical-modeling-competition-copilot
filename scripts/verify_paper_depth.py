#!/usr/bin/env python3
"""Verify recorded paper depth coverage and explicit page-budget bounds."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = {
    "section", "role", "planned_pages", "actual_pages",
    "required_content", "evidence", "status",
}
REQUIRED_ROLES = {
    "abstract", "restatement", "analysis", "assumptions_notation",
    "validation", "conclusion", "references",
}
COMPLETE = {"complete", "pass", "verified"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--main-text-pages", type=int, required=True)
    parser.add_argument("--appendix-pages", type=int, default=0)
    parser.add_argument("--minimum-main-text-pages", type=int, required=True)
    parser.add_argument("--minimum-total-pages", type=int, default=0)
    parser.add_argument("--maximum-main-text-pages", type=int)
    parser.add_argument("--expected-subproblems", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    plan = args.project_dir / "reports" / "paper_depth_plan.csv"
    rows: list[dict[str, str]] = []
    fields: set[str] = set()
    if not plan.is_file():
        errors.append("reports/paper_depth_plan.csv is missing")
    else:
        with plan.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            rows = list(reader)
        if missing := FIELDS - fields:
            errors.append("paper_depth_plan.csv missing columns: " + ", ".join(sorted(missing)))

    roles = {(row.get("role") or "").strip() for row in rows}
    if missing := REQUIRED_ROLES - roles:
        errors.append("paper depth plan missing roles: " + ", ".join(sorted(missing)))
    subproblems = [row for row in rows if (row.get("role") or "").strip() == "subproblem"]
    if len(subproblems) < args.expected_subproblems:
        errors.append(
            f"paper depth plan has {len(subproblems)} subproblem rows; "
            f"expected at least {args.expected_subproblems}"
        )

    for index, row in enumerate(rows, 2):
        role = (row.get("role") or "").strip()
        if role not in REQUIRED_ROLES | {"subproblem", "appendix", "other"}:
            errors.append(f"paper_depth_plan.csv:{index} has unknown role: {role or '<empty>'}")
        for field in ("section", "role", "required_content", "evidence", "status"):
            if not (row.get(field) or "").strip():
                errors.append(f"paper_depth_plan.csv:{index} has empty {field}")
        if (row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"paper_depth_plan.csv:{index} is not complete")

    if args.main_text_pages < args.minimum_main_text_pages:
        errors.append(
            f"main text has {args.main_text_pages} pages; selected depth floor is "
            f"{args.minimum_main_text_pages}"
        )
    if args.maximum_main_text_pages is not None and args.main_text_pages > args.maximum_main_text_pages:
        errors.append(
            f"main text has {args.main_text_pages} pages; official maximum is "
            f"{args.maximum_main_text_pages}"
        )
    total_pages = args.main_text_pages + args.appendix_pages
    if total_pages < args.minimum_total_pages:
        errors.append(
            f"complete PDF has {total_pages} recorded pages; selected minimum is "
            f"{args.minimum_total_pages}"
        )
    if args.appendix_pages > args.main_text_pages:
        warnings.append("appendix is longer than main text; visually confirm that the main argument is self-contained")

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "recorded page bounds and section coverage; not mathematical or prose-quality certification",
        "counts": {
            "main_text_pages": args.main_text_pages,
            "appendix_pages": args.appendix_pages,
            "total_pages": total_pages,
            "subproblem_rows": len(subproblems),
        },
        "bounds": {
            "minimum_main_text_pages": args.minimum_main_text_pages,
            "minimum_total_pages": args.minimum_total_pages,
            "maximum_main_text_pages": args.maximum_main_text_pages,
        },
        "errors": errors,
        "warnings": warnings,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
