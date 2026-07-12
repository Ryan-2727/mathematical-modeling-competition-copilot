#!/usr/bin/env python3
"""Render a Markdown AI-use report from the JSONL audit log."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = []
    if args.log.exists():
        for line in args.log.read_text(encoding="utf-8").splitlines():
            if line.strip(): records.append(json.loads(line))
    lines = ["# AI tool use details", "", "| Time (UTC) | Tool/version | Stage | Purpose | Adoption | Human verification |", "| --- | --- | --- | --- | --- | --- |"]
    for item in records:
        lines.append(f"| {item['timestamp_utc']} | {item['tool']} {item['version']} | {item['stage']} | {item['purpose']} | {item['adopted']} | {item['human_verification']} |")
    lines += ["", "## Key interaction summaries", ""]
    for index, item in enumerate(records, 1):
        lines += [f"### {index}. {item['tool']} - {item['stage']}", item['prompt_summary'], ""]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
