#!/usr/bin/env python3
"""Verify model ladders, identifiability, route independence, and reconciliation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from contestlib import read_csv_strict as read_csv
from contestlib import safe_project_path as safe


COMPLETE = {"pass", "complete", "verified", "accepted"}
MODEL_LEVELS = {"C0", "C1", "C2", "C3"}
PARAMETER_ROLES = {"shared", "condition_specific", "nuisance", "fixed"}
IDENTIFIABILITY = {"PASS", "CONDITIONAL", "FAIL"}
ROUTE_ROLES = {"primary", "independent_check", "complementary_check", "algorithm_check"}
COMPARISON = {"agree", "disagree_resolved", "disagree_unresolved", "not_compared"}
CLAIM_ACTIONS = {"admit", "conditional", "narrow", "reject", "not_applicable"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def yes(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def text(value: Any) -> str:
    return str(value or "").strip()


def table(
    root: Path, name: str, required: set[str], errors: list[str]
) -> tuple[list[dict[str, str]], Path]:
    path = root / "reports" / name
    try:
        rows, fields = read_csv(path)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot read {name}: {exc}")
        return [], path
    missing = required - fields
    if missing:
        errors.append(f"{name} missing columns: " + ", ".join(sorted(missing)))
    if not rows:
        errors.append(f"{name} has no evidence rows")
    return rows, path


def evidence_file(root: Path, relative: str, label: str, errors: list[str]) -> None:
    path = safe(root, relative)
    if path is None or not path.is_file():
        errors.append(f"{label} evidence file is missing or unsafe")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the cross-domain model reasoning core."
    )
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/model_reasoning_core.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    out = safe(root, args.out)
    if out is None:
        raise SystemExit("output must stay inside --project-dir")
    errors: list[str] = []
    warnings: list[str] = []

    models, model_path = table(
        root,
        "model_decision_log.csv",
        {
            "subproblem", "model_level", "parent_model", "baseline", "candidate",
            "added_mechanism", "new_parameters", "expected_diagnostic_signature",
            "failure_test", "identifiability_status", "selected",
            "selection_evidence", "status",
        },
        errors,
    )
    by_subproblem: dict[str, list[dict[str, str]]] = {}
    for line, row in enumerate(models, 2):
        subproblem = text(row.get("subproblem"))
        by_subproblem.setdefault(subproblem, []).append(row)
        level = text(row.get("model_level")).upper()
        if not subproblem or level not in MODEL_LEVELS:
            errors.append(f"model_decision_log.csv:{line} has invalid subproblem/model_level")
        if level in {"C2", "C3"} and any(
            not text(row.get(field))
            for field in ("parent_model", "added_mechanism", "new_parameters", "expected_diagnostic_signature")
        ):
            errors.append(f"model_decision_log.csv:{line} complex candidate lacks promotion evidence")
        if text(row.get("identifiability_status")).upper() not in IDENTIFIABILITY:
            errors.append(f"model_decision_log.csv:{line} has invalid identifiability_status")
        if text(row.get("status")).lower() not in COMPLETE:
            errors.append(f"model_decision_log.csv:{line} is not complete")
    for subproblem, rows in by_subproblem.items():
        levels = {text(row.get("model_level")).upper() for row in rows}
        if not ({"C0", "C1"} & levels):
            errors.append(f"{subproblem or '<blank>'} lacks a C0/C1 baseline")
        selected = [row for row in rows if yes(row.get("selected"))]
        if len(selected) != 1:
            errors.append(f"{subproblem or '<blank>'} must have exactly one selected model")
        elif text(selected[0].get("identifiability_status")).upper() == "FAIL":
            errors.append(f"{subproblem or '<blank>'} selected model has identifiability FAIL")
        elif text(selected[0].get("identifiability_status")).upper() == "CONDITIONAL":
            warnings.append(f"{subproblem} selected model is conditionally identifiable")

    parameters, parameter_path = table(
        root,
        "parameter_registry.csv",
        {"subproblem", "model_id", "parameter", "role", "unit", "scope", "source",
         "bounds", "identifiability_status", "claim_boundary", "status"},
        errors,
    )
    parameter_subproblems: set[str] = set()
    for line, row in enumerate(parameters, 2):
        parameter_subproblems.add(text(row.get("subproblem")))
        role = text(row.get("role"))
        verdict = text(row.get("identifiability_status")).upper()
        if role not in PARAMETER_ROLES:
            errors.append(f"parameter_registry.csv:{line} has invalid role")
        if verdict not in IDENTIFIABILITY:
            errors.append(f"parameter_registry.csv:{line} has invalid identifiability_status")
        if verdict == "FAIL" and text(row.get("claim_boundary")).lower() not in {
            "not_reported", "range_only", "identifiable_combination", "fallback"
        }:
            errors.append(f"parameter_registry.csv:{line} FAIL is not bounded safely")
        if verdict == "CONDITIONAL" and not text(row.get("claim_boundary")):
            errors.append(f"parameter_registry.csv:{line} CONDITIONAL lacks claim_boundary")
        elif verdict == "CONDITIONAL":
            warnings.append(
                f"parameter_registry.csv:{line} parameter is conditionally identifiable"
            )
        if any(not text(row.get(field)) for field in ("subproblem", "model_id", "parameter", "unit", "scope", "source", "bounds")):
            errors.append(f"parameter_registry.csv:{line} has empty required fields")
        if text(row.get("status")).lower() not in COMPLETE:
            errors.append(f"parameter_registry.csv:{line} is not complete")
    missing_parameters = set(by_subproblem) - parameter_subproblems
    if missing_parameters:
        errors.append("parameter_registry.csv lacks subproblems: " + ", ".join(sorted(missing_parameters)))

    routes, route_path = table(
        root,
        "independent_routes.csv",
        {"subproblem", "route_id", "route_role", "principle", "data_representation",
         "failure_mode", "result_file", "result_value", "tolerance",
         "comparison_status", "limitation", "status"},
        errors,
    )
    routes_by_subproblem: dict[str, list[dict[str, str]]] = {}
    for line, row in enumerate(routes, 2):
        subproblem = text(row.get("subproblem"))
        routes_by_subproblem.setdefault(subproblem, []).append(row)
        role = text(row.get("route_role"))
        if role not in ROUTE_ROLES:
            errors.append(f"independent_routes.csv:{line} has invalid route_role")
        if text(row.get("comparison_status")) not in COMPARISON:
            errors.append(f"independent_routes.csv:{line} has invalid comparison_status")
        if finite(row.get("result_value")) is None or finite(row.get("tolerance")) is None:
            errors.append(f"independent_routes.csv:{line} has invalid numeric result/tolerance")
        evidence_file(root, text(row.get("result_file")), f"independent_routes.csv:{line}", errors)
        if text(row.get("status")).lower() not in COMPLETE:
            errors.append(f"independent_routes.csv:{line} is not complete")
    for subproblem in by_subproblem:
        rows = routes_by_subproblem.get(subproblem, [])
        primary = [row for row in rows if text(row.get("route_role")) == "primary"]
        if len(primary) != 1:
            errors.append(f"{subproblem} must have exactly one primary route")
            continue
        independent = [row for row in rows if text(row.get("route_role")) == "independent_check"]
        if independent:
            anchor = primary[0]
            for row in independent:
                differences = sum(
                    text(row.get(field)).casefold() != text(anchor.get(field)).casefold()
                    for field in ("principle", "data_representation", "failure_mode")
                )
                if differences < 2:
                    errors.append(f"{subproblem} independent route fails the two-difference rule")
        else:
            complementary = [row for row in rows if text(row.get("route_role")) == "complementary_check"]
            limitations = [text(row.get("limitation")) for row in complementary]
            if len(complementary) < 2 or not all(limitations):
                errors.append(f"{subproblem} needs an independent route or two documented complementary checks")
            else:
                warnings.append(f"{subproblem} uses complementary checks; claim must retain the limitation")

    reconciliations, reconciliation_path = table(
        root,
        "result_reconciliation.csv",
        {"subproblem", "comparison_id", "primary_route", "comparison_route",
         "primary_value", "comparison_value", "tolerance", "disagreement_material",
         "investigation_step", "cause", "resolution", "claim_action", "evidence_file", "status"},
        errors,
    )
    reconciled_subproblems: set[str] = set()
    for line, row in enumerate(reconciliations, 2):
        subproblem = text(row.get("subproblem"))
        reconciled_subproblems.add(subproblem)
        action = text(row.get("claim_action"))
        if action not in CLAIM_ACTIONS:
            errors.append(f"result_reconciliation.csv:{line} has invalid claim_action")
        if any(finite(row.get(field)) is None for field in ("primary_value", "comparison_value", "tolerance")):
            errors.append(f"result_reconciliation.csv:{line} has invalid numeric comparison")
        material = yes(row.get("disagreement_material"))
        if material and action == "admit":
            errors.append(f"result_reconciliation.csv:{line} admits a material disagreement")
        if material and any(not text(row.get(field)) for field in ("investigation_step", "cause", "resolution")):
            errors.append(f"result_reconciliation.csv:{line} material disagreement is unexplained")
        evidence_file(root, text(row.get("evidence_file")), f"result_reconciliation.csv:{line}", errors)
        if text(row.get("status")).lower() not in COMPLETE:
            errors.append(f"result_reconciliation.csv:{line} is not complete")
    missing_reconciliation = set(by_subproblem) - reconciled_subproblems
    if missing_reconciliation:
        errors.append("result_reconciliation.csv lacks subproblems: " + ", ".join(sorted(missing_reconciliation)))

    joint_path = root / "reports" / "joint_inference_design.json"
    verified_path = root / "results" / "verified_values.csv"
    try:
        joint = json.loads(joint_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        joint = {}
        errors.append(f"cannot read joint_inference_design.json: {exc}")
    if not isinstance(joint, dict) or not isinstance(joint.get("applicable"), bool):
        errors.append("joint_inference_design.json requires boolean applicable")
    elif joint["applicable"]:
        designs = joint.get("subproblems")
        if not isinstance(designs, list) or not designs:
            errors.append("joint inference is applicable but has no subproblem design")
        else:
            required = {"subproblem", "conditions", "shared_parameters", "condition_specific_parameters", "nuisance_parameters", "separate_fit_baseline", "joint_objective", "comparison_result", "sharing_verdict", "evidence_file", "status"}
            scalar_required = required - {
                "conditions", "shared_parameters", "condition_specific_parameters", "nuisance_parameters"
            }
            for index, row in enumerate(designs, 1):
                if not isinstance(row, dict) or any(field not in row for field in required) or any(
                    row.get(field) in (None, "") for field in scalar_required
                ):
                    errors.append(f"joint inference design {index} lacks required evidence")
                    continue
                if str(row.get("status") or "").lower() not in COMPLETE:
                    errors.append(f"joint inference design {index} is not complete")
                conditions = row.get("conditions")
                if not isinstance(conditions, list) or len(conditions) < 2:
                    errors.append(f"joint inference design {index} needs at least two conditions")
                strategies = row.get("strategies_compared")
                if not isinstance(strategies, list) or "separate" not in strategies or not any(
                    strategy in {"joint_shared", "partial_pooling"} for strategy in strategies
                ):
                    errors.append(
                        f"joint inference design {index} must compare separate and joint strategies"
                    )
                registered = {
                    text(item.get("parameter"))
                    for item in parameters
                    if text(item.get("subproblem")) == text(row.get("subproblem"))
                }
                declared = set()
                for field in (
                    "shared_parameters", "condition_specific_parameters", "nuisance_parameters"
                ):
                    values = row.get(field)
                    if not isinstance(values, list):
                        errors.append(f"joint inference design {index} {field} must be a list")
                    else:
                        declared.update(map(text, values))
                unknown = declared - registered
                if unknown:
                    errors.append(
                        f"joint inference design {index} references unregistered parameters: "
                        + ", ".join(sorted(unknown))
                    )
                evidence_file(root, text(row.get("evidence_file")), f"joint inference design {index}", errors)
    elif not text(joint.get("reason")):
        errors.append("joint inference not applicable requires a reason")

    paths = {
        "model_decision_log_sha256": model_path,
        "parameter_registry_sha256": parameter_path,
        "independent_routes_sha256": route_path,
        "result_reconciliation_sha256": reconciliation_path,
        "joint_inference_design_sha256": joint_path,
        "verified_values_sha256": verified_path,
    }
    reasoning_status = "FAIL" if errors else ("CONDITIONAL" if warnings else "PASS")
    payload = {
        "status": "FAIL" if errors else ("LIMITED" if warnings else "PASS"),
        "reasoning_status": reasoning_status,
        "scope": "recorded model-ladder, identifiability, route-independence, joint-design, and reconciliation evidence; not proof of mathematical truth",
        "counts": {
            "subproblems": len(by_subproblem),
            "models": len(models),
            "parameters": len(parameters),
            "routes": len(routes),
            "reconciliations": len(reconciliations),
        },
        "warnings": warnings,
        "errors": errors,
        **{key: digest(path) for key, path in paths.items()},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 1 if errors else (2 if warnings else 0)


if __name__ == "__main__":
    raise SystemExit(main())
