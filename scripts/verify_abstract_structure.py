#!/usr/bin/env python3
"""Require a concise analysis-method-result contest abstract structure."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from contestlib import sha256_bytes as digest


BLOCKS = {
    "analysis": re.compile(r"(?:问题分析|analysis)\s*[:：]", re.I),
    "method": re.compile(r"(?:建模方法|研究方法|方法|method(?:ology)?)\s*[:：]", re.I),
    "result": re.compile(r"(?:主要结果|结果|results?)\s*[:：]", re.I),
}
NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?\s*(?:%|[A-Za-z]+)?")
VERIFIED_NUMBER = re.compile(r"\\VerifiedValue(?:WithUnit)?\s*\{[^{}]+\}")


def plain_tex(text: str) -> str:
    text = re.sub(r"(?<!\\)%.*", " ", text)
    text = re.sub(r"\\(?:textbf|emph|paragraph)\s*\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    return re.sub(r"\s+", " ", text.replace("{", " ").replace("}", " ")).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a concise analysis-method-result abstract.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--abstract", default="paper/sections/abstract.tex")
    parser.add_argument("--maximum-content-units", type=int, default=1300)
    parser.add_argument("--out", default="reports/abstract_structure.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    path = root / args.abstract
    errors: list[str] = []
    if args.maximum_content_units < 1:
        errors.append("maximum-content-units must be positive")
    if not path.is_file():
        raw_text = ""
        text = ""
        errors.append("abstract source is missing")
    else:
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        text = plain_tex(raw_text)
    checks = {name: bool(pattern.search(text)) for name, pattern in BLOCKS.items()}
    for name, passed in checks.items():
        if not passed:
            errors.append(f"abstract lacks an explicit {name} block")
    result_match = BLOCKS["result"].search(text)
    result_text = text[result_match.end():] if result_match else ""
    if result_match and not (
        NUMBER.search(result_text) or VERIFIED_NUMBER.search(raw_text)
    ):
        errors.append("abstract result block lacks a quantitative result")
    units = len(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+", text))
    if args.maximum_content_units > 0 and units > args.maximum_content_units:
        errors.append(f"abstract has {units} content units; limit is {args.maximum_content_units}")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "explicit concise analysis-method-result structure only; not factual or mathematical correctness",
        "source_sha256": digest(path) if path.is_file() else "",
        "content_units": units,
        "checks": checks,
        "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
