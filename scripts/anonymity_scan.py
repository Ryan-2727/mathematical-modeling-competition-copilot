#!/usr/bin/env python3
"""Scan text, metadata, Office files, PDFs, and ZIP contents for identity leaks."""
from __future__ import annotations

import argparse
import re
import subprocess
import zipfile
from pathlib import Path


TEXT_SUFFIXES = {".txt", ".md", ".tex", ".py", ".m", ".r", ".csv", ".json", ".yaml", ".yml", ".ipynb"}


def command_text(command: list[str]) -> str:
    try: return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False).stdout
    except FileNotFoundError: return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    defaults = [r"C:\\Users\\", r"/home/", r"school", r"university", "学院", "大学", "赛区"]
    patterns = [re.compile(value, re.I) for value in defaults + args.term]
    findings: list[str] = []
    def scan(label: str, text: str) -> None:
        for number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in patterns): findings.append(f"{label}:{number}: {line[:240]}")
    for path in sorted(args.root.rglob("*")):
        relative = path.relative_to(args.root)
        if any(pattern.search(str(relative)) for pattern in patterns): findings.append(f"PATH {relative}")
        if not path.is_file(): continue
        suffix = path.suffix.lower()
        if suffix in TEXT_SUFFIXES: scan(f"TEXT {relative}", path.read_text(encoding="utf-8", errors="ignore"))
        if suffix == ".pdf":
            scan(f"PDF_METADATA {relative}", command_text(["pdfinfo", str(path)]))
            extracted = command_text(["pdftotext", str(path), "-"])
            if extracted: scan(f"PDF_TEXT {relative}", extracted)
        if suffix in {".docx", ".xlsx", ".pptx", ".zip"}:
            try:
                with zipfile.ZipFile(path) as archive:
                    for name in archive.namelist():
                        if any(pattern.search(name) for pattern in patterns): findings.append(f"ARCHIVE_PATH {relative}!{name}")
                        if name in {"docProps/core.xml", "docProps/app.xml"} or name.endswith(".xml"):
                            scan(f"ARCHIVE_TEXT {relative}!{name}", archive.read(name).decode("utf-8", errors="ignore"))
            except zipfile.BadZipFile: findings.append(f"UNREADABLE_ARCHIVE {relative}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(findings) + ("\n" if findings else ""), encoding="utf-8")
    print(f"findings={len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__": raise SystemExit(main())
