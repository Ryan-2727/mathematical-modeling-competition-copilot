#!/usr/bin/env python3
"""Verify evidence-backed, weight-stable problem selection and the H6 lock."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


CRITERIA = (
    "subproblem_closure_risk",
    "result_verifiability",
    "upgrade_headroom",
    "team_fit",
    "writing_visual_potential",
)
FIELDS = {
    "problem_id", "attachment_status", "attachment_evidence",
    "attachment_parse_command", "baseline_command", "baseline_result",
    "baseline_elapsed_hours", "paper_figure", "subproblem_closure_evidence",
    "fallback_route", "fallback_evidence", *CRITERIA,
    "fatal_risk", "score", "status",
}
LEVELS = {"low", "medium", "high"}
LEVEL_VALUE = {"low": 0.0, "medium": 0.5, "high": 1.0}


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


def load_json(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {label}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return payload


def validated_weights(raw: object, label: str, errors: list[str]) -> dict[str, float]:
    if not isinstance(raw, dict) or set(raw) != set(CRITERIA):
        errors.append(f"{label} must define exactly: " + ", ".join(CRITERIA))
        return {}
    weights: dict[str, float] = {}
    for criterion in CRITERIA:
        try:
            value = float(raw[criterion])
        except (TypeError, ValueError):
            errors.append(f"{label}.{criterion} must be numeric")
            continue
        if value < 0:
            errors.append(f"{label}.{criterion} cannot be negative")
        weights[criterion] = value
    if len(weights) == len(CRITERIA) and abs(sum(weights.values()) - 1.0) > 1e-6:
        errors.append(f"{label} weights must sum to 1")
    return weights


def load_weight_scenarios(
    root: Path, errors: list[str]
) -> tuple[list[tuple[str, dict[str, float]]], float, float]:
    payload = load_json(
        root / "reports" / "problem_audition_weights.json",
        "problem_audition_weights.json",
        errors,
    )
    if payload.get("schema_version") != 1:
        errors.append("problem_audition_weights.json schema_version must be 1")
    scenarios: list[tuple[str, dict[str, float]]] = []
    base = validated_weights(payload.get("base_weights"), "base_weights", errors)
    if base:
        scenarios.append(("base", base))
    raw_scenarios = payload.get("sensitivity_scenarios")
    if not isinstance(raw_scenarios, list) or len(raw_scenarios) < 2:
        errors.append("at least two sensitivity_scenarios are required")
        raw_scenarios = []
    names = {"base"}
    for index, scenario in enumerate(raw_scenarios, 1):
        if not isinstance(scenario, dict):
            errors.append(f"sensitivity_scenarios[{index}] must be an object")
            continue
        name = str(scenario.get("name") or "").strip()
        if not name or name in names:
            errors.append(f"sensitivity_scenarios[{index}] has a blank or duplicate name")
            continue
        names.add(name)
        weights = validated_weights(
            scenario.get("weights"), f"sensitivity_scenarios[{index}].weights", errors
        )
        if weights:
            scenarios.append((name, weights))
    try:
        minimum_win_rate = float(payload.get("minimum_selected_win_rate"))
    except (TypeError, ValueError):
        errors.append("minimum_selected_win_rate must be numeric")
        minimum_win_rate = 1.0
    if not 0 <= minimum_win_rate <= 1:
        errors.append("minimum_selected_win_rate must be between 0 and 1")
    try:
        tolerance = float(payload.get("recorded_score_tolerance", 1.0))
    except (TypeError, ValueError):
        errors.append("recorded_score_tolerance must be numeric")
        tolerance = 1.0
    if tolerance < 0:
        errors.append("recorded_score_tolerance cannot be negative")
    return scenarios, minimum_win_rate, tolerance


def computed_score(row: dict[str, str], weights: dict[str, float]) -> float:
    values = {criterion: LEVEL_VALUE[row[criterion].strip()] for criterion in CRITERIA}
    values["subproblem_closure_risk"] = 1.0 - values["subproblem_closure_risk"]
    return round(100.0 * sum(weights[key] * values[key] for key in CRITERIA), 6)


def valid_selection_override(
    root: Path, raw: object, reasons: set[str], errors: list[str]
) -> bool:
    required = {"type", "reason", "evidence", "authorized_by", "exceptions"}
    if not isinstance(raw, dict) or raw.get("type") != "selection_exception":
        errors.append(
            "non-winning, unstable, or gate-failing selection requires a "
            "selection_exception selection_override"
        )
        return False
    missing = [field for field in required if not str(raw.get(field) or "").strip()]
    if missing:
        errors.append("selection_override missing fields: " + ", ".join(sorted(missing)))
        return False
    exceptions = raw.get("exceptions")
    if not isinstance(exceptions, list) or not all(
        isinstance(item, str) and item.strip() for item in exceptions
    ):
        errors.append("selection_override.exceptions must be a non-empty string list")
        return False
    uncovered = sorted(reasons - {item.strip() for item in exceptions})
    if uncovered:
        errors.append(
            "selection_override does not cover exception(s): " + ", ".join(uncovered)
        )
        return False
    path = project_file(root, str(raw.get("evidence") or ""))
    if path is None or not path.is_file():
        errors.append("selection_override evidence is missing or unsafe")
        return False
    return True


def verify(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = load_rows(root / "reports" / "problem_audition.csv", errors)
    scenarios, minimum_win_rate, score_tolerance = load_weight_scenarios(root, errors)
    if len(rows) < 2:
        errors.append("problem audition needs at least two candidate rows")
    seen: set[str] = set()
    recorded_scores: dict[str, float] = {}
    valid_rows: dict[str, dict[str, str]] = {}
    candidate_gate_failures: dict[str, list[str]] = {}
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
            if not row.get("attachment_parse_command", "").strip():
                errors.append(f"problem_audition.csv:{index} attachment_parse_command is missing")
        elif evidence != "not_applicable":
            errors.append(f"problem_audition.csv:{index} no_attachment requires not_applicable evidence")
        elif row.get("attachment_parse_command", "").strip() != "not_applicable":
            errors.append(
                f"problem_audition.csv:{index} no_attachment requires a not_applicable parse command"
            )
        if not row.get("baseline_command", "").strip():
            errors.append(f"problem_audition.csv:{index} baseline command is missing")
        result = project_file(root, row.get("baseline_result", "").strip())
        if result is None or not result.is_file():
            errors.append(f"problem_audition.csv:{index} baseline result is missing or unsafe")
        try:
            elapsed = float(row.get("baseline_elapsed_hours", ""))
        except ValueError:
            errors.append(f"problem_audition.csv:{index} baseline_elapsed_hours must be numeric")
            elapsed = 999.0
        else:
            if elapsed <= 0:
                errors.append(f"problem_audition.csv:{index} baseline_elapsed_hours must be positive")
        figure = project_file(root, row.get("paper_figure", "").strip())
        if figure is None or not figure.is_file() or figure.suffix.lower() not in {
            ".pdf", ".png", ".jpg", ".jpeg", ".svg"
        }:
            errors.append(f"problem_audition.csv:{index} paper_figure is missing, unsafe, or not a paper figure")
        for field in ("subproblem_closure_evidence", "fallback_evidence"):
            path = project_file(root, row.get(field, "").strip())
            if path is None or not path.is_file():
                errors.append(f"problem_audition.csv:{index} {field} is missing or unsafe")
        if not row.get("fallback_route", "").strip():
            errors.append(f"problem_audition.csv:{index} fallback_route is missing")
        levels_valid = True
        for field in CRITERIA:
            if row.get(field, "").strip() not in LEVELS:
                errors.append(f"problem_audition.csv:{index} {field} must be low, medium, or high")
                levels_valid = False
        if not row.get("fatal_risk", "").strip():
            errors.append(f"problem_audition.csv:{index} fatal_risk is missing")
        try:
            recorded = float(row.get("score", ""))
        except ValueError:
            errors.append(f"problem_audition.csv:{index} score must be numeric")
        else:
            if not 0 <= recorded <= 100:
                errors.append(f"problem_audition.csv:{index} score must be between 0 and 100")
            recorded_scores[problem] = recorded
        if row.get("status", "").strip() != "verified":
            errors.append(f"problem_audition.csv:{index} status must be verified")
        if problem and levels_valid:
            valid_rows[problem] = row
            gate_failures: list[str] = []
            if elapsed > 2.0:
                gate_failures.append("baseline_over_2h")
            if row.get("fatal_risk", "").strip().lower() not in {
                "none", "no", "not_applicable"
            }:
                gate_failures.append("fatal_risk")
            candidate_gate_failures[problem] = gate_failures

    computed: dict[str, dict[str, float]] = {}
    if scenarios and len(valid_rows) == len(rows):
        for name, weights in scenarios:
            computed[name] = {
                problem: computed_score(row, weights)
                for problem, row in valid_rows.items()
            }
        for problem, recorded in recorded_scores.items():
            if problem in computed.get("base", {}) and abs(recorded - computed["base"][problem]) > score_tolerance:
                warnings.append(
                    f"{problem} recorded score differs from the recomputed base score; "
                    "the verifier uses the recomputed score"
                )

    selection = load_json(
        root / "reports" / "problem_selection.json", "problem selection", errors
    )
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
    if selection_hour > 6:
        override = selection.get("override")
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

    base_winners: list[str] = []
    win_rate: float | None = None
    minimum_margin: float | None = None
    confidence = "unavailable"
    scenario_winners: dict[str, list[str]] = {}
    if computed and selected in valid_rows:
        margins: list[float] = []
        selected_wins = 0
        for name, scores in computed.items():
            best = max(scores.values())
            winners = sorted(problem for problem, value in scores.items() if abs(value - best) <= 1e-9)
            scenario_winners[name] = winners
            if name == "base":
                base_winners = winners
            if selected in winners:
                selected_wins += 1
            alternatives = [value for problem, value in scores.items() if problem != selected]
            margins.append(scores[selected] - max(alternatives))
        win_rate = selected_wins / len(computed)
        minimum_margin = min(margins)
        if win_rate == 1.0 and minimum_margin >= 5.0:
            confidence = "high"
        elif win_rate >= minimum_win_rate:
            confidence = "medium"
        else:
            confidence = "low"
        exception_reasons = set(candidate_gate_failures.get(selected, []))
        if selected not in base_winners:
            exception_reasons.add("not_base_winner")
        if win_rate < minimum_win_rate:
            exception_reasons.add("low_scenario_win_rate")
        if exception_reasons:
            valid_selection_override(
                root, selection.get("selection_override"), exception_reasons, errors
            )
    else:
        exception_reasons = set()

    return {
        "status": "FAIL" if errors else "PASS",
        "scope": "candidate evidence, recomputed score stability, and H6 selection-lock verification",
        "candidate_count": len(rows),
        "selected_problem": selected,
        "selection_hour": selection_hour,
        "computed_scores": computed,
        "scenario_winners": scenario_winners,
        "base_winners": base_winners,
        "selected_win_rate": win_rate,
        "minimum_selected_win_rate": minimum_win_rate,
        "selected_minimum_margin": minimum_margin,
        "selection_confidence": confidence,
        "candidate_gate_failures": candidate_gate_failures,
        "selection_exception_reasons": sorted(exception_reasons),
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
