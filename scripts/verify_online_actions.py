#!/usr/bin/env python3
"""Verify declared online actions without inspecting or transmitting search text."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


FIELDS = {
    "action_id", "mode", "action_type", "purpose", "destination",
    "contains_current_contest_material", "privacy_ambiguity", "user_decision",
    "evidence", "status",
}
FORBIDDEN_LIVE_ACTIONS = {
    "upload", "post", "sync", "share", "external_ai", "online_compile",
    "online_execute", "cloud_store", "repository_push",
}


def verify(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    path = root / "reports" / "online_actions.csv"
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = FIELDS - set(reader.fieldnames or [])
            if missing:
                errors.append("online_actions.csv missing columns: " + ", ".join(sorted(missing)))
            rows = list(reader)
    except OSError as exc:
        errors.append(f"cannot read online_actions.csv: {exc}")
        rows = []
    seen: set[str] = set()
    for line, row in enumerate(rows, 2):
        action_id = row.get("action_id", "").strip()
        mode = row.get("mode", "").strip()
        action = row.get("action_type", "").strip()
        if not action_id or action_id in seen:
            errors.append(f"online_actions.csv:{line} has a blank or duplicate action_id")
        seen.add(action_id)
        if mode not in {"training", "live", "posthoc"}:
            errors.append(f"online_actions.csv:{line} mode is invalid")
        for field in ("action_type", "purpose", "destination", "evidence"):
            if not row.get(field, "").strip():
                errors.append(f"online_actions.csv:{line} {field} is missing")
        contains = row.get("contains_current_contest_material", "").strip().lower()
        ambiguity = row.get("privacy_ambiguity", "").strip().lower()
        decision = row.get("user_decision", "").strip().lower()
        if contains not in {"yes", "no"} or ambiguity not in {"yes", "no"}:
            errors.append(f"online_actions.csv:{line} privacy flags must be yes or no")
        if mode == "live" and action in FORBIDDEN_LIVE_ACTIONS:
            errors.append(f"online_actions.csv:{line} live mode forbids {action}; keep contest work local")
        if ambiguity == "yes" and decision not in {"approved", "denied"}:
            errors.append(f"online_actions.csv:{line} privacy is ambiguous; ask the user and record the reply")
        if ambiguity == "yes" and decision == "denied" and row.get("status", "").strip() != "cancelled":
            errors.append(f"online_actions.csv:{line} denied action must be cancelled")
        if row.get("status", "").strip() not in {"declared", "completed", "cancelled"}:
            errors.append(f"online_actions.csv:{line} status is invalid")
    return {
        "status": "FAIL" if errors else "PASS",
        "scope": (
            "local declaration audit only; search text is not lexically restricted or transmitted, "
            "and operating-system network interception is out of scope"
        ),
        "action_count": len(rows),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    report = verify(root)
    out = args.out.resolve()
    try:
        out.relative_to(root / "reports")
    except ValueError as exc:
        raise SystemExit("--out must stay inside project reports") from exc
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
