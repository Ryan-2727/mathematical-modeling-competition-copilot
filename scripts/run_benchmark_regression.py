#!/usr/bin/env python3
"""Run or inspect blinded quality cases and block score regressions.

The harness reads immutable baselines from the manifest. It has no baseline
update mode and never writes to the manifest.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from typing import Any


DIMENSIONS = (
    "correctness_evidence",
    "validation",
    "reproducibility",
    "writing",
    "visual_communication",
)
PROBLEM_FAMILIES = {
    "evaluation",
    "prediction",
    "optimization",
    "mechanism",
    "network",
    "simulation",
}


def safe_project_file(root: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def read_json(path: Path, label: str) -> tuple[Any, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"cannot read {label}: {exc}"


def validate_manifest_case(case: Any, index: int) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(case, dict):
        return None, [f"cases[{index}] must be an object"]
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        errors.append("id must be a non-empty string")
    if case.get("problem_family") not in PROBLEM_FAMILIES:
        errors.append(f"unsupported problem_family: {case.get('problem_family')!r}")
    for field in ("allowed_inputs", "required_subproblems", "expected_artifacts", "command"):
        if not isinstance(case.get(field), list):
            errors.append(f"{field} must be an array")
    if isinstance(case.get("allowed_inputs"), list) and any(
        not isinstance(item, str) or not item.strip()
        for item in case["allowed_inputs"]
    ):
        errors.append("allowed_inputs entries must be non-empty strings")
    if isinstance(case.get("required_subproblems"), list):
        if not case["required_subproblems"]:
            errors.append("required_subproblems must not be empty")
        elif any(
            not isinstance(item, str) or not item.strip()
            for item in case["required_subproblems"]
        ):
            errors.append("required_subproblems entries must be non-empty strings")
    if isinstance(case.get("expected_artifacts"), list) and not case["expected_artifacts"]:
        errors.append("expected_artifacts must not be empty")
    if isinstance(case.get("command"), list) and (
        not case["command"]
        or any(not isinstance(item, str) or not item for item in case["command"])
    ):
        errors.append("command must be a non-empty argv string array")
    runtime = finite_number(case.get("runtime_budget_seconds"))
    if runtime is None or runtime <= 0:
        errors.append("runtime_budget_seconds must be positive")
    if not isinstance(case.get("result_file"), str) or not case["result_file"].strip():
        errors.append("result_file must be a non-empty relative path")
    rubric = case.get("rubric")
    if not isinstance(rubric, dict):
        errors.append("rubric must be an object")
        rubric = {}
    weights: list[float] = []
    for dimension in DIMENSIONS:
        item = rubric.get(dimension)
        if not isinstance(item, dict):
            errors.append(f"rubric.{dimension} must be an object")
            continue
        weight = finite_number(item.get("weight"))
        if weight is None or weight <= 0:
            errors.append(f"rubric.{dimension}.weight must be positive")
        else:
            weights.append(weight)
        if not isinstance(item.get("criterion"), str) or not item["criterion"].strip():
            errors.append(f"rubric.{dimension}.criterion must be non-empty")
    if len(weights) == len(DIMENSIONS) and abs(sum(weights) - 1.0) > 1e-9:
        errors.append("rubric weights must sum to 1")

    baseline = case.get("baseline_scores")
    tolerance = case.get("regression_tolerance")
    if not isinstance(baseline, dict):
        errors.append("baseline_scores must be an object")
        baseline = {}
    if not isinstance(tolerance, dict):
        errors.append("regression_tolerance must be an object")
        tolerance = {}
    for dimension in DIMENSIONS:
        score = finite_number(baseline.get(dimension))
        if score is None or not 0 <= score <= 5:
            errors.append(f"baseline_scores.{dimension} must be in [0, 5]")
        allowed_drop = finite_number(tolerance.get(dimension))
        if allowed_drop is None or allowed_drop < 0:
            errors.append(f"regression_tolerance.{dimension} must be non-negative")
    overall_tolerance = finite_number(tolerance.get("overall"))
    if overall_tolerance is None or overall_tolerance < 0:
        errors.append("regression_tolerance.overall must be non-negative")

    expected = case.get("expected_artifacts")
    if isinstance(expected, list):
        for artifact_index, artifact in enumerate(expected, 1):
            if not isinstance(artifact, dict):
                errors.append(f"expected_artifacts[{artifact_index}] must be an object")
                continue
            if not isinstance(artifact.get("class"), str) or not artifact["class"].strip():
                errors.append(
                    f"expected_artifacts[{artifact_index}].class must be non-empty"
                )
            if not isinstance(artifact.get("path"), str) or not artifact["path"].strip():
                errors.append(
                    f"expected_artifacts[{artifact_index}].path must be non-empty"
                )
    return case, errors


def weighted_score(scores: dict[str, float], rubric: dict[str, Any]) -> float:
    return sum(scores[name] * float(rubric[name]["weight"]) for name in DIMENSIONS)


def verify_case_result(
    root: Path,
    case: dict[str, Any],
    result: Any,
) -> tuple[list[str], dict[str, float], float | None, float | None]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["result payload must be an object"], {}, None, None
    if result.get("case_id") != case["id"]:
        errors.append(
            f"result case_id {result.get('case_id')!r} does not match {case['id']!r}"
        )
    score_items = result.get("scores")
    if not isinstance(score_items, dict):
        errors.append("result scores must be an object")
        score_items = {}
    scores: dict[str, float] = {}
    for dimension in DIMENSIONS:
        item = score_items.get(dimension)
        if not isinstance(item, dict):
            errors.append(f"scores.{dimension} must contain score and evidence")
            continue
        score = finite_number(item.get("score"))
        if score is None or not 0 <= score <= 5:
            errors.append(f"scores.{dimension}.score must be in [0, 5]")
        else:
            scores[dimension] = score
        evidence_paths = item.get("evidence")
        if not isinstance(evidence_paths, list) or not evidence_paths:
            errors.append(f"scores.{dimension}.evidence must be a non-empty path array")
            continue
        for relative in evidence_paths:
            if not isinstance(relative, str):
                errors.append(f"scores.{dimension}.evidence entries must be strings")
                continue
            path = safe_project_file(root, relative)
            if path is None:
                errors.append(
                    f"scores.{dimension} evidence must stay inside project: {relative}"
                )
            elif not path.is_file():
                errors.append(f"scores.{dimension} evidence is missing: {relative}")

    result_artifacts = result.get("artifacts")
    if not isinstance(result_artifacts, list):
        errors.append("result artifacts must be an array")
        result_artifacts = []
    declared_artifacts: set[tuple[str, str]] = set()
    for artifact in result_artifacts:
        if not isinstance(artifact, dict):
            errors.append("result artifact entries must be objects")
            continue
        artifact_class = artifact.get("class")
        relative = artifact.get("path")
        if not isinstance(artifact_class, str) or not isinstance(relative, str):
            errors.append("result artifacts require string class and path")
            continue
        declared_artifacts.add((artifact_class, relative))
        path = safe_project_file(root, relative)
        if path is None:
            errors.append(f"artifact must stay inside project: {relative}")
        elif not path.is_file():
            errors.append(f"artifact is missing: {relative}")
    for expected in case["expected_artifacts"]:
        pair = (expected["class"], expected["path"])
        if pair not in declared_artifacts:
            errors.append(
                f"expected artifact not declared in result: {pair[0]} at {pair[1]}"
            )

    baseline = {
        dimension: float(case["baseline_scores"][dimension])
        for dimension in DIMENSIONS
    }
    tolerance = case["regression_tolerance"]
    for dimension, current in scores.items():
        minimum = baseline[dimension] - float(tolerance[dimension])
        if current < minimum:
            errors.append(
                f"{dimension} regressed: current {current:g}, baseline "
                f"{baseline[dimension]:g}, tolerance {float(tolerance[dimension]):g}"
            )

    current_overall = (
        weighted_score(scores, case["rubric"])
        if len(scores) == len(DIMENSIONS)
        else None
    )
    baseline_overall = weighted_score(baseline, case["rubric"])
    if current_overall is not None:
        minimum_overall = baseline_overall - float(tolerance["overall"])
        if current_overall < minimum_overall:
            errors.append(
                f"overall score regressed: current {current_overall:g}, baseline "
                f"{baseline_overall:g}, tolerance {float(tolerance['overall']):g}"
            )
    return errors, scores, current_overall, baseline_overall


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare blinded benchmark results against immutable manifest baselines."
    )
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run each enabled case's argv command before reading its result file.",
    )
    args = parser.parse_args()
    root = args.project_dir.resolve()
    manifest_path = args.manifest if args.manifest.is_absolute() else root / args.manifest
    out = args.out if args.out.is_absolute() else root / args.out
    try:
        manifest_path.resolve().relative_to(root)
        out.resolve().relative_to(root)
    except ValueError:
        raise SystemExit("manifest and output must stay inside the project directory")
    if manifest_path.resolve() == out.resolve():
        raise SystemExit("output must not overwrite the benchmark manifest")

    payload, read_error = read_json(manifest_path, "benchmark manifest")
    errors: list[str] = [read_error] if read_error else []
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(payload, dict):
        errors.append("benchmark manifest must be an object")
        cases = []
    elif payload.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not isinstance(cases, list):
        errors.append("benchmark manifest cases must be an array")
        cases = []
    if not cases:
        errors.append("benchmark manifest has no cases")

    reports: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    enabled_count = 0
    for index, raw_case in enumerate(cases, 1):
        case, case_errors = validate_manifest_case(raw_case, index)
        if case is None:
            errors.extend(case_errors)
            continue
        case_id = str(case.get("id") or f"cases[{index}]")
        if case_id in seen_ids:
            case_errors.append(f"duplicate case id: {case_id}")
        else:
            seen_ids.add(case_id)
        enabled = case.get("enabled", True)
        if not isinstance(enabled, bool):
            case_errors.append("enabled must be boolean")
            enabled = False
        if not enabled:
            reports.append(
                {
                    "id": case_id,
                    "problem_family": case.get("problem_family"),
                    "status": "SKIPPED",
                    "errors": case_errors,
                }
            )
            errors.extend(f"{case_id}: {error}" for error in case_errors)
            continue
        enabled_count += 1

        for relative in case.get("allowed_inputs", []):
            if not isinstance(relative, str):
                case_errors.append("allowed_inputs entries must be strings")
                continue
            path = safe_project_file(root, relative)
            if path is None:
                case_errors.append(f"allowed input must stay inside project: {relative}")
            elif not path.exists():
                case_errors.append(f"allowed input is missing: {relative}")

        execution: dict[str, Any] | None = None
        if args.execute and not case_errors:
            try:
                completed = subprocess.run(
                    case["command"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=float(case["runtime_budget_seconds"]),
                    shell=False,
                    check=False,
                )
                execution = {
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-4000:],
                    "stderr": completed.stderr[-4000:],
                }
                if completed.returncode != 0:
                    case_errors.append(
                        f"benchmark command failed with return code {completed.returncode}"
                    )
            except subprocess.TimeoutExpired:
                case_errors.append(
                    f"benchmark command exceeded {case['runtime_budget_seconds']} seconds"
                )
            except OSError as exc:
                case_errors.append(f"cannot execute benchmark command: {exc}")

        result_file = case.get("result_file", "")
        result_path = (
            safe_project_file(root, result_file)
            if isinstance(result_file, str)
            else None
        )
        scores: dict[str, float] = {}
        current_overall: float | None = None
        baseline_overall: float | None = None
        if result_path is None:
            case_errors.append(f"result_file must stay inside project: {result_file}")
        elif result_path.resolve() == out.resolve():
            case_errors.append("output must not overwrite a benchmark result file")
        elif not result_path.is_file():
            case_errors.append(f"benchmark result is missing: {result_file}")
        else:
            result_payload, result_error = read_json(
                result_path, f"benchmark result {result_file}"
            )
            if result_error:
                case_errors.append(result_error)
            elif not case_errors:
                (
                    result_errors,
                    scores,
                    current_overall,
                    baseline_overall,
                ) = verify_case_result(root, case, result_payload)
                case_errors.extend(result_errors)

        reports.append(
            {
                "id": case_id,
                "problem_family": case.get("problem_family"),
                "status": "PASS" if not case_errors else "FAIL",
                "baseline_scores": case.get("baseline_scores"),
                "current_scores": scores,
                "baseline_overall": baseline_overall,
                "current_overall": current_overall,
                "execution": execution,
                "errors": case_errors,
            }
        )
        errors.extend(f"{case_id}: {error}" for error in case_errors)

    if errors:
        status = "FAIL"
        returncode = 1
    elif enabled_count == 0:
        status = "LIMITED"
        returncode = 2
    else:
        status = "PASS"
        returncode = 0
    report = {
        "status": status,
        "scope": (
            "artifact-backed rubric scores compared with declared immutable baselines; "
            "not an award prediction and not proof of solution correctness"
        ),
        "baseline_updated": False,
        "counts": {
            "cases": len(reports),
            "enabled": enabled_count,
            "passed": sum(item["status"] == "PASS" for item in reports),
            "failed": sum(item["status"] == "FAIL" for item in reports),
            "skipped": sum(item["status"] == "SKIPPED" for item in reports),
        },
        "cases": reports,
        "errors": errors,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
