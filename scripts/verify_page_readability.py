#!/usr/bin/env python3
"""Check a human page-review ledger against the compiled PDF page count."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = {"page", "abstract_density", "formula_first_definition", "figure_legibility", "blank_space", "table_break", "appendix_boundary", "reference_consistency", "reviewer", "status"}
COMPLETE = {"pass", "complete", "verified", "not_applicable"}


def page_count(path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore
        return len(PdfReader(str(path)).pages)
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a page-by-page manual readability review.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--pdf", default="paper/main.pdf")
    parser.add_argument("--out", default="reports/page_readability_verification.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    pdf = root / args.pdf
    errors: list[str] = []
    warnings: list[str] = []
    if not pdf.is_file():
        errors.append("compiled PDF is missing")
    try:
        with (root / "reports" / "page_readability_checklist.csv").open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows, fields = list(reader), set(reader.fieldnames or [])
    except (OSError, UnicodeError, csv.Error) as exc:
        rows, fields = [], set()
        errors.append(f"cannot read page_readability_checklist.csv: {exc}")
    if FIELDS - fields:
        errors.append("page_readability_checklist.csv missing columns: " + ", ".join(sorted(FIELDS - fields)))
    reviewed: set[int] = set()
    for line, row in enumerate(rows, 2):
        try:
            page = int(str(row.get("page") or ""))
            if page < 1:
                raise ValueError
            reviewed.add(page)
        except ValueError:
            errors.append(f"page_readability_checklist.csv:{line} has invalid page")
        if not str(row.get("reviewer") or "").strip():
            errors.append(f"page_readability_checklist.csv:{line} lacks reviewer")
        for field in FIELDS - {"page", "reviewer"}:
            if str(row.get(field) or "").strip().lower() not in COMPLETE:
                errors.append(f"page_readability_checklist.csv:{line} {field} is not resolved")
    pages = page_count(pdf) if pdf.is_file() else None
    if pages is None and not errors:
        warnings.append("pypdf unavailable; page coverage cannot be automatically checked")
    elif pages is not None:
        missing = sorted(set(range(1, pages + 1)) - reviewed)
        extra = sorted(reviewed - set(range(1, pages + 1)))
        if missing:
            errors.append("page review missing pages: " + ", ".join(map(str, missing)))
        if extra:
            errors.append("page review lists nonexistent pages: " + ", ".join(map(str, extra)))
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    payload = {"status": status, "scope": "human readability checklist and PDF page coverage; no automated visual-quality judgment", "pdf_pages": pages, "reviewed_pages": sorted(reviewed), "errors": errors, "warnings": warnings}
    out = Path(args.out) if Path(args.out).is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[status]


if __name__ == "__main__":
    raise SystemExit(main())
