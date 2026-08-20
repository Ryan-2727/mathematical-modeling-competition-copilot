#!/usr/bin/env python3
"""Advance the submission state only with an evidence path."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from contest_profile import load_contest_profile


ORDER = ["draft", "verified", "frozen", "hashed", "submitted", "receipt_verified"]


def parse_at(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit("--at must be an ISO-8601 datetime") from exc
    if parsed.tzinfo is None:
        raise SystemExit("--at must include a timezone offset")
    return parsed


def enforce_profile_window(profile_id: str, state: str, at: datetime) -> None:
    if profile_id != "cumcm-2026" or state not in {
        "hashed",
        "submitted",
        "receipt_verified",
    }:
        return
    profile = load_contest_profile(profile_id)
    start = datetime.fromisoformat(profile["competition_start"])
    hash_deadline = datetime.fromisoformat(profile["hash_deadline"])
    upload_open = datetime.fromisoformat(profile["upload_open"])
    upload_deadline = datetime.fromisoformat(profile["upload_deadline"])
    if state == "hashed" and not start <= at <= hash_deadline:
        raise SystemExit(
            "CUMCM 2026 final hash state must be recorded between contest start "
            "and the MD5 deadline"
        )
    if state in {"submitted", "receipt_verified"} and not (
        upload_open <= at <= upload_deadline
    ):
        raise SystemExit(
            "CUMCM 2026 upload/receipt state must be recorded inside the official "
            "upload window"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--state", choices=ORDER, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--at")
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    old = data.get("submission_state", "draft")
    if ORDER.index(args.state) != ORDER.index(old) + 1:
        raise SystemExit(f"invalid transition: {old} -> {args.state}")
    if not args.evidence.exists(): raise SystemExit("evidence file is missing")
    at = parse_at(args.at)
    enforce_profile_window(str(data.get("submission_profile") or ""), args.state, at)
    data["submission_state"] = args.state
    data.setdefault("submission_history", []).append(
        {
            "state": args.state,
            "evidence": str(args.evidence),
            "at_utc": at.astimezone(timezone.utc).isoformat(),
            "at_recorded": at.isoformat(),
        }
    )
    args.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
