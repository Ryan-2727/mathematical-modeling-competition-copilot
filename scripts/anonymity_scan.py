#!/usr/bin/env python3
"""Scan submission paths and readable text for identity or local-path leaks."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


TEXT_SUFFIXES = {".txt", ".md", ".tex", ".py", ".m", ".r", ".csv", ".json", ".yaml", ".yml", ".ipynb"}


def pdf_metadata(path: Path) -> str:
    result = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    defaults = [r"C:\\Users\\", r"/home/", r"school", r"university", r"学院", r"大学", r"赛区"]
    patterns = [re.compile(value, re.I) for value in defaults + args.term]
    findings: list[str] = []
    for path in sorted(args.root.rglob("*")):
        relative = path.relative_to(args.root)
        if any(pattern.search(str(relative)) for pattern in patterns):
            findings.append(f"PATH {relative}")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for number, line in enumerate(text.splitlines(), 1):
                if any(pattern.search(line) for pattern in patterns):
                    findings.append(f"TEXT {relative}:{number}: {line[:240]}")
        if path.is_file() and path.suffix.lower() == ".pdf":
            metadata = pdf_metadata(path)
            for line in metadata.splitlines():
                if line.startswith(("Title:", "Author:", "Creator:", "Producer:")) and line.split(":", 1)[1].strip():
                    findings.append(f"PDF_METADATA {relative}: {line}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(findings) + ("\n" if findings else ""), encoding="utf-8")
    print(f"findings={len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
