#!/usr/bin/env python3
"""Append a transparent AI-use record required by contest compliance workflows."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--prompt-summary", required=True)
    parser.add_argument("--adopted", choices=["yes", "no", "partial"], required=True)
    parser.add_argument("--human-verification", required=True)
    args = parser.parse_args()
    log_path = args.log
    record = vars(args).copy()
    record["log"] = str(log_path)
    record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
