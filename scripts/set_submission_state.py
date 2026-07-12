#!/usr/bin/env python3
"""Advance the submission state only with an evidence path."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ORDER = ["draft", "verified", "frozen", "hashed", "submitted", "receipt_verified"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--state", choices=ORDER, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    old = data.get("submission_state", "draft")
    if ORDER.index(args.state) != ORDER.index(old) + 1:
        raise SystemExit(f"invalid transition: {old} -> {args.state}")
    if not args.evidence.exists(): raise SystemExit("evidence file is missing")
    data["submission_state"] = args.state
    data.setdefault("submission_history", []).append({"state": args.state, "evidence": str(args.evidence), "at_utc": datetime.now(timezone.utc).isoformat()})
    args.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
