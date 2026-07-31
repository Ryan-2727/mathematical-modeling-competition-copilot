#!/usr/bin/env python3
"""Verify evidence-backed problem selection and the six-hour lock."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


FIELDS = {
    "problem_id", "attachment_status", "attachment_evidence",
    "baseline_command", "baseline_result", "subproblem_closure_risk",
    "result_verifiability", "upgrade_headroom", "team_fit",
    "writing_visual_potential", "fatal_risk", "score", "status",
}
LEVELS = {"low", "medium", "high"}


def project_file(root: Path, value: str) -> Path | None:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def load_rows(path: Path, errors: list[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = FIELDS - set(reader.fieldnames or [])
            if missing:
                errors.append("problem_audition.csv missing columns: " + ", ".join(sorted(missing)))
            return list(reader)
    except OSError as exc:
        errors.append(f"cannot read problem audition: {exc}")
        return []


def verify(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = load_rows(root / "reports" / "problem_audition.csv", errors)
    if len(rows) < 2:
        errors.append("problem audition needs at least two candidate rows")
    seen: set[str] = set()
    scores: dict[str, float] = {}
    for index, row in enumerate(rows, 2):
        problem = row.get("problem_id", "").strip()
        if not problem or problem in seen:
            errors.append(f"problem_audition.csv:{index} has a blank or duplicate problem_id")
        seen.add(problem)
        if row.get("attachment_status", "").strip() not in {"verified", "no_attachment"}:
            errors.append(f"problem_audition.csv:{index} attachment_status must be verified or no_attachment")
        evidence = row.get("attachment_evidence", "").strip()
        if row.get("attachment_status", "").strip() == "verified":
            path = project_file(root, evidence)
            if path is None or not path.is_file():
                errors.append(f"problem_audition.csv:{index} attachment evidence is missing or unsafe")
        elif evidence != "not_applicable":
            errors.append(f"problem_audition.csv:{index} no_attachment requires not_applicable evidence")
        if not row.get("baseline_command", "").strip():
            errors.append(f"problem_audition.csv:{index} baseline command is missing")
        result = project_file(root, row.get("baseline_result", "").strip())
        if result is None or not result.is_file():
            errors.append(f"problem_audition.csv:{index} baseline result is missing or unsafe")
        for field in (
            "subproblem_closure_risk", "result_verifiability", "upgrade_headroom",
            "team_fit", "writing_visual_potential",
        ):
            if row.get(field, "").strip() not in LEVELS:
                errors.append(f"problem_audition.csv:{index} {field} must be low, medium, or high")
        if not row.get("fatal_risk", "").strip():
            errors.append(f"problem_audition.csv:{index} fatal_risk is missing")
        try:
            score = float(row.get("score", ""))
        except ValueError:
            errors.append(f"problem_audition.csv:{index} score must be numeric")
        else:
            if not 0 <= score <= 100:
                errors.append(f"problem_audition.csv:{index} score must be between 0 and 100")
            scores[problem] = score
        if row.get("status", "").strip() != "verified":
            errors.append(f"problem_audition.csv:{index} status must be verified")

    selection_path = root / "reports" / "problem_selection.json"
    try:
        selection = json.loads(selection_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read problem selection: {exc}")
        selection = {}
    selected = str(selection.get("selected_problem") or "").strip()
    if selected not in seen:
        errors.append("selected problem is not a verified audition candidate")
    if not str(selection.get("rationale") or "").strip():
        errors.append("problem selection needs an evidence-based rationale")
    try:
        selection_hour = float(selection.get("selection_hour"))
    except (TypeError, ValueError):
        errors.append("selection_hour must be numeric")
        selection_hour = 999.0
    override = selection.get("override")
    if selection_hour > 6:
        required = {"type", "failed_problem", "reason", "evidence", "authorized_by"}
        if not isinstance(override, dict) or override.get("type") != "catastrophic_infeasibility":
            errors.append("selection after H6 requires a catastrophic-infeasibility override")
        else:
            missing = [field for field in required if not str(override.get(field) or "").strip()]
            if missing:
                errors.append("late-selection override missing fields: " + ", ".join(sorted(missing)))
            path = project_file(root, str(override.get("evidence") or ""))
            if path is None or not path.is_file():
                errors.append("late-selection override evidence is missing or unsafe")
    if selected in scores and scores and scores[selected] < max(scores.values()):
        warnings.append("selected problem does not have the highest recorded score; preserve the rationale")
    return {
        "status": "FAIL" if errors else "PASS",
        "scope": "candidate evidence completeness and H6 selection-lock verification",
        "candidate_count": len(rows),
        "selected_problem": selected,
        "selection_hour": selection_hour,
        "errors": errors,
        "warnings": warnings,
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
