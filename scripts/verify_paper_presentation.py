#!/usr/bin/env python3
"""Verify recorded PDF presentation evidence without inventing an aesthetic score."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


FIELDS = {
    "page", "hierarchy", "font_readability", "orphaned_headings_captions",
    "formula_breaks", "table_continuity", "whitespace_balance",
    "visual_consistency", "reviewer", "status",
}
COMPLETE = {"pass", "complete", "verified", "not_applicable"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_pdf(path: Path) -> tuple[int | None, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        return None, warnings, ["compiled PDF does not have a PDF header"]
    pages = len(re.findall(rb"/Type\s*/Page\b", data))
    if pages < 1:
        warnings.append("PDF page count could not be inferred from page objects")
        pages = None
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        warnings.append("pypdf unavailable; page coverage uses PDF object inference when possible")
    else:
        try:
            pages = len(PdfReader(str(path)).pages)
        except Exception:
            errors.append("pypdf could not parse the compiled PDF")
    return pages, warnings, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify presentation evidence for a compiled contest PDF.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--pdf", default="paper/main.pdf")
    parser.add_argument("--checklist", default="reports/presentation_checklist.csv")
    parser.add_argument("--out", default="reports/paper_presentation.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    pdf = root / args.pdf
    checklist = root / args.checklist
    errors: list[str] = []
    warnings: list[str] = []
    pages: int | None = None
    if not pdf.is_file():
        errors.append("compiled PDF is missing")
    else:
        pages, page_warnings, page_errors = inspect_pdf(pdf)
        warnings.extend(page_warnings)
        errors.extend(page_errors)
    try:
        with checklist.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows, columns = list(reader), set(reader.fieldnames or [])
    except (OSError, UnicodeError, csv.Error) as exc:
        rows, columns = [], set()
        errors.append(f"cannot read presentation checklist: {exc}")
    if FIELDS - columns:
        errors.append("presentation checklist missing columns: " + ", ".join(sorted(FIELDS - columns)))
    reviewed: set[int] = set()
    for line, row in enumerate(rows, 2):
        try:
            page = int(str(row.get("page") or ""))
            if page < 1:
                raise ValueError
            reviewed.add(page)
        except ValueError:
            errors.append(f"presentation_checklist.csv:{line} has invalid page")
        if not str(row.get("reviewer") or "").strip():
            errors.append(f"presentation_checklist.csv:{line} lacks reviewer")
        for field in FIELDS - {"page", "reviewer"}:
            if str(row.get(field) or "").strip().lower() not in COMPLETE:
                errors.append(f"presentation_checklist.csv:{line} {field} is not resolved")
    if pages is not None:
        missing = sorted(set(range(1, pages + 1)) - reviewed)
        extra = sorted(reviewed - set(range(1, pages + 1)))
        if missing:
            errors.append("presentation review missing pages: " + ", ".join(map(str, missing)))
        if extra:
            errors.append("presentation review lists nonexistent pages: " + ", ".join(map(str, extra)))
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "scope": "PDF signals and hash-bound human presentation review; no automated aesthetic or award judgment",
        "paper_sha256": digest(pdf) if pdf.is_file() else "",
        "checklist_sha256": digest(checklist) if checklist.is_file() else "",
        "pdf_pages": pages,
        "reviewed_pages": sorted(reviewed),
        "errors": errors,
        "warnings": warnings,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    return {"PASS": 0, "LIMITED": 2, "FAIL": 1}[status]


if __name__ == "__main__":
    raise SystemExit(main())
