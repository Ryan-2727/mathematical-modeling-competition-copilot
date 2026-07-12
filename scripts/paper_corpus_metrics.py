#!/usr/bin/env python3
"""Collect reproducible page metrics from a local PDF reference corpus."""
from __future__ import annotations

import argparse
import json
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
    args = parser.parse_args()
    papers = []
    for path in sorted(args.pdf_dir.glob("*.pdf")):
        info = pdfinfo(path)
        papers.append({"file": path.name, **info})
    result = {
        "pdf_count": len(papers),
        "papers": papers,
        "page_count_min": min((int(p["Pages"]) for p in papers if "Pages" in p), default=None),
        "page_count_max": max((int(p["Pages"]) for p in papers if "Pages" in p), default=None),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
