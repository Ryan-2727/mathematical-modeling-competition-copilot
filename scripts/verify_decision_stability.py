#!/usr/bin/env python3
"""Verify that material recommendation changes are disclosed as conditional."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


COMPLETE = {"pass", "complete", "verified"}
FIELDS = {
    "decision_id", "subproblem", "baseline_recommendation", "perturbation_id",
    "perturbation", "perturbed_recommendation", "recommendation_changed",
    "materiality", "conditional_conclusion", "limitation_location", "result_file",
    "paper_location", "status",
}
CHANGED = {"true", "false"}
MATERIALITY = {"material", "not_material"}
CONDITIONAL = {"conditional", "qualified", "scenario_dependent"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str], str | None]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader), set(reader.fieldnames or []), None
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], set(), str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify recommendation stability disclosures.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/decision_stability.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    ledger = root / "reports" / "decision_stability.csv"
    conclusions = root / "reports" / "conclusion_map.csv"
    rows, columns, read_error = read_csv(ledger)
    conclusion_rows, conclusion_columns, conclusion_error = read_csv(conclusions)
    errors: list[str] = []
    if read_error:
        errors.append(f"cannot read decision_stability.csv: {read_error}")
    if conclusion_error:
        errors.append(f"cannot read conclusion_map.csv: {conclusion_error}")
    if FIELDS - columns:
        errors.append("decision_stability.csv missing columns: " + ", ".join(sorted(FIELDS - columns)))
    if "subproblem" not in conclusion_columns:
        errors.append("conclusion_map.csv missing subproblem column")
    conclusion_subproblems = {
        str(row.get("subproblem") or "").strip() for row in conclusion_rows
        if str(row.get("subproblem") or "").strip()
    }
    decisions: dict[str, list[dict[str, str]]] = {}
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in FIELDS):
            errors.append(f"decision_stability.csv:{line} has empty required evidence")
        decision = str(row.get("decision_id") or "").strip()
        decisions.setdefault(decision, []).append(row)
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"decision_stability.csv:{line} is not complete")
        changed = str(row.get("recommendation_changed") or "").strip().lower()
        materiality = str(row.get("materiality") or "").strip().lower()
        if changed not in CHANGED:
            errors.append(f"decision_stability.csv:{line} has invalid recommendation_changed")
        if materiality not in MATERIALITY:
            errors.append(f"decision_stability.csv:{line} has invalid materiality")
        if str(row.get("subproblem") or "").strip() not in conclusion_subproblems:
            errors.append(f"decision_stability.csv:{line} references an unanswered subproblem")
        result = safe(root, str(row.get("result_file") or ""))
        if result is None or not result.is_file():
            errors.append(f"decision_stability.csv:{line} result_file is missing or unsafe")
        if changed == "true" and materiality == "material":
            conclusion = str(row.get("conditional_conclusion") or "").strip().lower()
            if conclusion not in CONDITIONAL:
                errors.append(f"decision_stability.csv:{line} must disclose a conditional conclusion")
            if not str(row.get("limitation_location") or "").strip():
                errors.append(f"decision_stability.csv:{line} lacks a limitation location")
    for decision, decision_rows in decisions.items():
        if not decision:
            continue
        if not decision_rows:
            errors.append("decision_stability.csv has an empty decision identifier")
        elif not any(str(row.get("perturbation_id") or "").strip() for row in decision_rows):
            errors.append(f"decision_stability.csv lacks a perturbation for {decision}")
    if not rows:
        errors.append("decision_stability.csv has no evidence rows")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": "recorded perturbation disclosures only; not a numerical rerun or proof of model correctness",
        "decision_stability_sha256": digest(ledger) if ledger.is_file() else "",
        "conclusion_map_sha256": digest(conclusions) if conclusions.is_file() else "",
        "decisions": len({key for key in decisions if key}),
        "errors": errors,
    }
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
