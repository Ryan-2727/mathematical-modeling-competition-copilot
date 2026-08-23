#!/usr/bin/env python3
"""Record a user's declared A/B/C choice against an exact local recommendation hash."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from problem_selection_core import (
    PROBLEMS,
    load_json_object,
    parse_utc,
    safe_project_file,
    sha256_file,
    stale_input_errors,
)


RECOMMENDATION = "reports/problem_selection_recommendation.json"
SELECTION = "reports/problem_selection.json"


def record_confirmation(
    root: Path,
    selected_problem: str,
    selection_hour: float,
    rationale: str,
    note: str,
) -> dict[str, Any]:
    recommendation_path = root / RECOMMENDATION
    recommendation = load_json_object(recommendation_path)
    if recommendation.get("status") not in {"PASS", "LIMITED"}:
        raise ValueError("recommendation must be PASS or LIMITED before confirmation")
    if recommendation.get("requires_user_confirmation") is not True:
        raise ValueError("recommendation is not ready for user confirmation")
    if selected_problem not in recommendation.get("candidates", {}):
        raise ValueError("selected problem is not an evaluated A/B/C candidate")
    stale = stale_input_errors(root, recommendation.get("input_hashes"))
    if stale:
        raise ValueError("; ".join(stale))
    generated = parse_utc(recommendation.get("generated_at_utc"))
    if generated is None:
        raise ValueError("recommendation generation time is invalid")
    now = datetime.now(timezone.utc)
    if now < generated:
        raise ValueError("confirmation time cannot precede recommendation generation")
    selection_path = root / SELECTION
    try:
        current = load_json_object(selection_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        current = {}
    current.update(
        {
            "schema_version": 2,
            "selected_problem": selected_problem,
            "confirmed_problem": selected_problem,
            "selection_hour": selection_hour,
            "rationale": rationale,
            "recommendation_file": RECOMMENDATION,
            "recommendation_sha256": sha256_file(recommendation_path),
            "recommendation_generated_at_utc": recommendation["generated_at_utc"],
            "recommendation_input_hashes": recommendation["input_hashes"],
            "confirmation": {
                "decision": "confirmed",
                "recorded_at_utc": now.isoformat(),
                "note": note,
                "audit_limitation": (
                    "This records a declared user choice; it is not identity authentication "
                    "or proof of who typed the command."
                ),
            },
            "selection_override": current.get("selection_override"),
            "override": current.get("override"),
        }
    )
    selection_path.parent.mkdir(parents=True, exist_ok=True)
    selection_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return current


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--selected-problem", choices=PROBLEMS, required=True)
    parser.add_argument("--selection-hour", type=float, required=True)
    parser.add_argument("--rationale", required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    if not 0 <= args.selection_hour <= 6:
        parser.error("--selection-hour must be between H0 and H6")
    if not args.rationale.strip():
        parser.error("--rationale cannot be blank")
    root = args.project_dir.resolve()
    if safe_project_file(root, RECOMMENDATION) is None:
        raise SystemExit("unsafe project path")
    try:
        record_confirmation(
            root, args.selected_problem, args.selection_hour, args.rationale.strip(), args.note.strip()
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print("RECORDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
