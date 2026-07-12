#!/usr/bin/env python3
"""Verify size, type, hashes, and selected contest-profile submission rules."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


PROFILES = {
    "generic": {"paper_suffixes": {".pdf"}, "support_suffixes": {".zip", ".rar"}, "max_paper_mb": 20, "max_support_mb": 20},
    "cumcm-2026": {"paper_suffixes": {".pdf", ".doc", ".docx"}, "support_suffixes": {".zip", ".rar"}, "max_paper_mb": 20, "max_support_mb": 20, "max_main_text_pages": 30, "toc_forbidden": True},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()


def pdf_pages(path: Path) -> int | None:
    result = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"): return int(line.split(":", 1)[1].strip())
    return None


def zip_names(path: Path) -> list[str] | None:
    if path.suffix.lower() != ".zip": return None
    try:
        with zipfile.ZipFile(path) as archive: return archive.namelist()
    except zipfile.BadZipFile: return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="generic")
    parser.add_argument("--main-text-pages", type=int)
    parser.add_argument("--require-ai-report", action="store_true")
    parser.add_argument("--max-paper-mb", type=float)
    parser.add_argument("--max-support-mb", type=float)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    profile = PROFILES[args.profile]
    paper_limit = args.max_paper_mb if args.max_paper_mb is not None else profile["max_paper_mb"]
    support_limit = args.max_support_mb if args.max_support_mb is not None else profile["max_support_mb"]
    errors: list[str] = []; warnings: list[str] = []; artifacts = []
    if not args.paper.is_file(): errors.append("paper is missing")
    elif args.paper.suffix.lower() not in profile["paper_suffixes"]: errors.append(f"paper type is not allowed by {args.profile}")
    if args.paper.is_file():
        size = args.paper.stat().st_size
        if size > paper_limit * 1024 * 1024: errors.append(f"paper exceeds {paper_limit} MB")
        artifacts.append({"role": "paper", "file": args.paper.name, "bytes": size, "sha256": sha256(args.paper), "pages": pdf_pages(args.paper) if args.paper.suffix.lower() == ".pdf" else None})
    if args.support is not None:
        if not args.support.is_file(): errors.append("support is missing")
        elif args.support.suffix.lower() not in profile["support_suffixes"]: errors.append(f"support type is not allowed by {args.profile}")
        else:
            size = args.support.stat().st_size
            if size > support_limit * 1024 * 1024: errors.append(f"support exceeds {support_limit} MB")
            artifacts.append({"role": "support", "file": args.support.name, "bytes": size, "sha256": sha256(args.support), "pages": None})
    if "max_main_text_pages" in profile:
        if args.main_text_pages is None: warnings.append("main-text page count was not supplied; visual counting remains required")
        elif args.main_text_pages > profile["max_main_text_pages"]: errors.append(f"main text exceeds {profile['max_main_text_pages']} pages")
    if args.require_ai_report:
        if args.support is None or not args.support.is_file(): errors.append("AI use requires a support archive containing AI工具使用详情.pdf")
        else:
            names = zip_names(args.support)
            if names is None: warnings.append("RAR contents were not inspected; verify AI工具使用详情.pdf manually")
            elif not any(Path(name).name == "AI工具使用详情.pdf" for name in names): errors.append("support ZIP lacks AI工具使用详情.pdf")
    payload = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "profile": args.profile, "status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings, "artifacts": artifacts}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__": raise SystemExit(main())
