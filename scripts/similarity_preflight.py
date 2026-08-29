#!/usr/bin/env python3
"""Advisory: flag long exact phrase overlap against an offline corpus."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TEXT_SUFFIXES = {".md", ".txt", ".tex"}


def tokens(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    words = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text)
    return {" ".join(words[index:index + 12]) for index in range(max(0, len(words) - 11))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-overlap", type=int, default=3)
    args = parser.parse_args()
    draft = tokens(args.draft)
    findings = []
    for path in args.corpus_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            overlap = len(draft & tokens(path))
            if overlap >= args.min_overlap: findings.append({"file": str(path), "shared_12_token_phrases": overlap})
    payload = {
        "status": "REVIEW" if findings else "PASS",
        "scope": "local_long_phrase_advisory",
        "draft": str(args.draft),
        "findings": findings,
        "note": (
            "This is not a plagiarism verdict, does not estimate either official "
            "Tongfang/CNKI metric, and cannot establish compliance with the 25% threshold."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0


if __name__ == "__main__": raise SystemExit(main())
