#!/usr/bin/env python3
"""Collect reproducible page metrics from a local PDF reference corpus."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def pdfinfo(path: Path) -> dict[str, str]:
    result = subprocess.run(
        ["pdfinfo", str(path)], capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False
    )
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.strip() in {"Pages", "Page size"}:
                values[key.strip()] = value.strip()
    values["returncode"] = str(result.returncode)
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--recursive", action="store_true", help="include PDFs in year/topic subdirectories")
    args = parser.parse_args()
    papers = []
    paths = args.pdf_dir.rglob("*.pdf") if args.recursive else args.pdf_dir.glob("*.pdf")
    for path in sorted(paths):
        info = pdfinfo(path)
        papers.append({"file": path.name, "relative_path": str(path.relative_to(args.pdf_dir)), **info})
    by_year: dict[str, list[int]] = {}
    for paper in papers:
        match = re.search(r"(?:19|20)\d{2}", paper["relative_path"])
        if match and "Pages" in paper:
            by_year.setdefault(match.group(0), []).append(int(paper["Pages"]))
    year_summary = {
        year: {"count": len(values), "page_min": min(values), "page_median": sorted(values)[len(values) // 2], "page_max": max(values)}
        for year, values in sorted(by_year.items())
    }
    result = {
        "pdf_count": len(papers),
        "papers": papers,
        "page_count_min": min((int(p["Pages"]) for p in papers if "Pages" in p), default=None),
        "page_count_max": max((int(p["Pages"]) for p in papers if "Pages" in p), default=None),
        "year_summary": year_summary,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pdf_count": result["pdf_count"], "page_count_min": result["page_count_min"], "page_count_max": result["page_count_max"], "year_summary": year_summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
