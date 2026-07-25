#!/usr/bin/env python3
"""Check declared model-family validation evidence and numeric thresholds.

This verifier checks evidence structure and declared acceptance thresholds. A
PASS does not prove mathematical correctness, model suitability, or award level.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable


FAMILIES = {
    "regression_forecast",
    "classification",
    "optimization",
    "simulation_stochastic",
    "network_ranking",
    "mechanism_dynamics",
    "causal_econometric",
    "unsupervised",
    "queueing_reliability",
    "spatial_spatiotemporal",
    "multiobjective_dynamic_optimization",
}
SUCCESSFUL_SOLVER_STATUSES = {
    "optimal",
    "globally_optimal",
    "locally_optimal",
    "feasible",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def load_manifest(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.is_file():
        return [], [f"model validation manifest is missing: {path}"]
    errors: list[str] = []
    try:
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
            models: list[dict[str, Any]] = []
            for line_number, row in enumerate(rows, 2):
                thresholds_text = (
                    row.get("thresholds_json") or row.get("thresholds") or "{}"
                ).strip()
                try:
                    thresholds = json.loads(thresholds_text)
                except json.JSONDecodeError as exc:
                    errors.append(f"{path.name}:{line_number} invalid thresholds JSON: {exc}")
                    thresholds = {}
                for key, value in row.items():
                    if key and key.startswith("threshold.") and (value or "").strip():
                        parsed = finite_number(value)
                        thresholds[key.removeprefix("threshold.")] = (
                            parsed if parsed is not None else (value or "").strip()
                        )
                models.append(
                    {
                        "id": (row.get("id") or row.get("model_id") or "").strip(),
                        "family": (
                            row.get("family") or row.get("model_family") or ""
                        ).strip(),
                        "evidence_file": (row.get("evidence_file") or "").strip(),
                        "evidence_sha256": (row.get("evidence_sha256") or "").strip(),
                        "thresholds": thresholds,
                    }
                )
            return models, errors
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
        return [], [f"cannot read model validation manifest: {exc}"]

    if isinstance(payload, list):
        return payload, errors
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        return [], ["JSON manifest must be an object with a models array"]
    return payload["models"], errors


def required_true(evidence: dict[str, Any], field: str, errors: list[str]) -> None:
    if evidence.get(field) is not True:
        errors.append(f"{field} must be explicitly true")


def required_text(evidence: dict[str, Any], field: str, errors: list[str]) -> str:
    value = evidence.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")
        return ""
    return value.strip()


def required_number(
    payload: dict[str, Any],
    field: str,
    errors: list[str],
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    value = finite_number(payload.get(field))
    if value is None:
        errors.append(f"{field} must be a finite number")
        return None
    if minimum is not None and value < minimum:
        errors.append(f"{field}={value:g} is below required minimum {minimum:g}")
    if maximum is not None and value > maximum:
        errors.append(f"{field}={value:g} exceeds required maximum {maximum:g}")
    return value


def threshold_number(
    thresholds: dict[str, Any],
    field: str,
    errors: list[str],
    *,
    minimum: float | None = None,
) -> float | None:
    value = finite_number(thresholds.get(field))
    if value is None:
        errors.append(f"thresholds.{field} must be a finite number")
        return None
    if minimum is not None and value < minimum:
        errors.append(f"thresholds.{field} must be at least {minimum:g}")
    return value


def relative_improvement(model: float, baseline: float, direction: str) -> float:
    denominator = max(abs(baseline), 1e-12)
    if direction == "lower":
        return (baseline - model) / denominator
    return (model - baseline) / denominator


def check_regression_forecast(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    for field in ("split_ordered", "leakage_checked", "residual_diagnostics"):
        required_true(evidence, field, errors)
    required_text(evidence, "baseline_name", errors)
    min_holdout = threshold_number(thresholds, "minimum_holdout_size", errors, minimum=1)
    holdout = required_number(evidence, "holdout_size", errors, minimum=1)
    minimum_improvement = threshold_number(
        thresholds, "minimum_relative_improvement", errors, minimum=0
    )
    model_metric = required_number(evidence, "model_metric", errors)
    baseline_metric = required_number(evidence, "baseline_metric", errors)
    direction = evidence.get("metric_direction")
    if direction not in {"lower", "higher"}:
        errors.append("metric_direction must be 'lower' or 'higher'")
    if holdout is not None and min_holdout is not None and holdout < min_holdout:
        errors.append(
            f"holdout_size={holdout:g} is below declared threshold {min_holdout:g}"
        )
    if (
        model_metric is not None
        and baseline_metric is not None
        and direction in {"lower", "higher"}
    ):
        improvement = relative_improvement(model_metric, baseline_metric, direction)
        metrics["relative_improvement"] = improvement
        if minimum_improvement is not None and improvement < minimum_improvement:
            errors.append(
                f"relative improvement {improvement:g} is below declared threshold "
                f"{minimum_improvement:g}"
            )
    if "maximum_model_metric" in thresholds and model_metric is not None:
        maximum = threshold_number(thresholds, "maximum_model_metric", errors)
        if maximum is not None and model_metric > maximum:
            errors.append(
                f"model_metric={model_metric:g} exceeds declared threshold {maximum:g}"
            )
    return errors, metrics


def check_classification(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    counts = evidence.get("class_counts")
    labels: list[str] = []
    numeric_counts: list[float] = []
    if not isinstance(counts, dict) or len(counts) < 2:
        errors.append("class_counts must contain at least two classes")
    else:
        labels = list(counts)
        for label in labels:
            count = finite_number(counts[label])
            if count is None or count < 1 or not count.is_integer():
                errors.append(f"class_counts.{label} must be a positive integer")
            else:
                numeric_counts.append(count)

    min_class_count = threshold_number(thresholds, "minimum_class_count", errors, minimum=1)
    if numeric_counts and min_class_count is not None:
        observed_minimum = min(numeric_counts)
        metrics["minimum_class_count"] = observed_minimum
        if observed_minimum < min_class_count:
            errors.append(
                f"minimum class count {observed_minimum:g} is below declared threshold "
                f"{min_class_count:g}"
            )
    if numeric_counts:
        metrics["class_imbalance_ratio"] = max(numeric_counts) / min(numeric_counts)
        if "maximum_class_imbalance_ratio" in thresholds:
            maximum_ratio = threshold_number(
                thresholds, "maximum_class_imbalance_ratio", errors, minimum=1
            )
            if (
                maximum_ratio is not None
                and metrics["class_imbalance_ratio"] > maximum_ratio
            ):
                errors.append(
                    f"class imbalance ratio {metrics['class_imbalance_ratio']:g} exceeds "
                    f"declared threshold {maximum_ratio:g}"
                )

    matrix = evidence.get("confusion_matrix")
    valid_matrix = (
        isinstance(matrix, list)
        and labels
        and len(matrix) == len(labels)
        and all(isinstance(row, list) and len(row) == len(labels) for row in matrix)
    )
    if not valid_matrix:
        errors.append("confusion_matrix must be square and match class_counts")
    else:
        matrix_total = 0.0
        for row_index, row in enumerate(matrix):
            row_total = 0.0
            for value in row:
                number = finite_number(value)
                if number is None or number < 0 or not number.is_integer():
                    errors.append("confusion_matrix entries must be non-negative integers")
                    continue
                row_total += number
            matrix_total += row_total
            if len(numeric_counts) == len(labels) and row_total != numeric_counts[row_index]:
                errors.append(
                    f"confusion_matrix row {row_index} total does not match class_counts"
                )
        metrics["confusion_matrix_total"] = matrix_total

    threshold_selected = evidence.get("threshold_selected") is True
    calibration_checked = evidence.get("calibration_checked") is True
    decision_threshold = finite_number(evidence.get("decision_threshold"))
    if not calibration_checked and not (
        threshold_selected
        and decision_threshold is not None
        and 0 <= decision_threshold <= 1
    ):
        errors.append(
            "declare calibration_checked=true or a selected decision_threshold in [0, 1]"
        )

    macro_f1 = required_number(evidence, "macro_f1", errors, minimum=0, maximum=1)
    minority_recall = required_number(
        evidence, "minority_recall", errors, minimum=0, maximum=1
    )
    minimum_f1 = threshold_number(thresholds, "minimum_macro_f1", errors, minimum=0)
    minimum_recall = threshold_number(
        thresholds, "minimum_minority_recall", errors, minimum=0
    )
    if minimum_f1 is not None and minimum_f1 > 1:
        errors.append("thresholds.minimum_macro_f1 must not exceed 1")
    if minimum_recall is not None and minimum_recall > 1:
        errors.append("thresholds.minimum_minority_recall must not exceed 1")
    if macro_f1 is not None:
        metrics["macro_f1"] = macro_f1
        if minimum_f1 is not None and macro_f1 < minimum_f1:
            errors.append(
                f"macro_f1={macro_f1:g} is below declared threshold {minimum_f1:g}"
            )
    if minority_recall is not None:
        metrics["minority_recall"] = minority_recall
        if minimum_recall is not None and minority_recall < minimum_recall:
            errors.append(
                f"minority_recall={minority_recall:g} is below declared threshold "
                f"{minimum_recall:g}"
            )
    return errors, metrics


def check_optimization(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    for field in ("feasible", "constraint_audit"):
        required_true(evidence, field, errors)
    status = required_text(evidence, "solver_status", errors).lower()
    if status and status not in SUCCESSFUL_SOLVER_STATUSES:
        errors.append(f"solver_status is not accepted: {status}")
    direction = evidence.get("objective_direction")
    if direction not in {"minimize", "maximize"}:
        errors.append("objective_direction must be 'minimize' or 'maximize'")
    objective = required_number(evidence, "objective_value", errors)
    baseline = required_number(evidence, "baseline_objective", errors)
    gap = required_number(evidence, "relative_gap", errors, minimum=0)
    maximum_gap = threshold_number(thresholds, "maximum_relative_gap", errors, minimum=0)
    minimum_improvement = threshold_number(
        thresholds, "minimum_relative_improvement", errors, minimum=0
    )
    if gap is not None:
        metrics["relative_gap"] = gap
        if maximum_gap is not None and gap > maximum_gap:
            errors.append(
                f"relative_gap={gap:g} exceeds declared threshold {maximum_gap:g}"
            )
    if objective is not None and baseline is not None and direction in {"minimize", "maximize"}:
        improvement = relative_improvement(
            objective, baseline, "lower" if direction == "minimize" else "higher"
        )
        metrics["relative_improvement"] = improvement
        if minimum_improvement is not None and improvement < minimum_improvement:
            errors.append(
                f"objective improvement {improvement:g} is below declared threshold "
                f"{minimum_improvement:g}"
            )
    return errors, metrics


def check_simulation_stochastic(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    required_true(evidence, "convergence_checked", errors)
    seeds = evidence.get("seeds")
    if not isinstance(seeds, list) or not seeds:
        errors.append("seeds must be a non-empty list")
        unique_seeds = 0
    else:
        try:
            unique_seeds = len({json.dumps(seed, sort_keys=True) for seed in seeds})
        except TypeError:
            unique_seeds = 0
            errors.append("seeds must contain JSON-serializable scalar values")
        if unique_seeds != len(seeds):
            errors.append("seeds must be unique")
    replications = required_number(evidence, "replications", errors, minimum=1)
    if replications is not None and not replications.is_integer():
        errors.append("replications must be an integer")
    estimate = required_number(evidence, "estimate", errors)
    lower = required_number(evidence, "ci_lower", errors)
    upper = required_number(evidence, "ci_upper", errors)
    minimum_replications = threshold_number(
        thresholds, "minimum_replications", errors, minimum=1
    )
    minimum_seeds = threshold_number(
        thresholds, "minimum_unique_seeds", errors, minimum=1
    )
    maximum_width = threshold_number(
        thresholds, "maximum_relative_ci_width", errors, minimum=0
    )
    metrics["unique_seeds"] = float(unique_seeds)
    if minimum_seeds is not None and unique_seeds < minimum_seeds:
        errors.append(
            f"unique seed count {unique_seeds} is below declared threshold "
            f"{minimum_seeds:g}"
        )
    if (
        replications is not None
        and minimum_replications is not None
        and replications < minimum_replications
    ):
        errors.append(
            f"replications={replications:g} is below declared threshold "
            f"{minimum_replications:g}"
        )
    if estimate is not None and lower is not None and upper is not None:
        if not lower <= estimate <= upper:
            errors.append("estimate must lie inside [ci_lower, ci_upper]")
        if lower > upper:
            errors.append("ci_lower must not exceed ci_upper")
        relative_width = (upper - lower) / max(abs(estimate), 1e-12)
        metrics["relative_ci_width"] = relative_width
        if maximum_width is not None and relative_width > maximum_width:
            errors.append(
                f"relative CI width {relative_width:g} exceeds declared threshold "
                f"{maximum_width:g}"
            )
    return errors, metrics


def check_network_ranking(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    for field in (
        "connected_or_consistent",
        "normalized",
        "perturbation_checked",
        "weight_sensitivity_checked",
    ):
        required_true(evidence, field, errors)
    score_sum = required_number(evidence, "score_sum", errors)
    instability = required_number(evidence, "rank_instability", errors, minimum=0)
    target = threshold_number(thresholds, "normalization_target", errors)
    tolerance = threshold_number(
        thresholds, "normalization_tolerance", errors, minimum=0
    )
    maximum_instability = threshold_number(
        thresholds, "maximum_rank_instability", errors, minimum=0
    )
    if score_sum is not None and target is not None:
        normalization_error = abs(score_sum - target)
        metrics["normalization_error"] = normalization_error
        if tolerance is not None and normalization_error > tolerance:
            errors.append(
                f"normalization error {normalization_error:g} exceeds declared "
                f"tolerance {tolerance:g}"
            )
    if instability is not None:
        metrics["rank_instability"] = instability
        if maximum_instability is not None and instability > maximum_instability:
            errors.append(
                f"rank_instability={instability:g} exceeds declared threshold "
                f"{maximum_instability:g}"
            )
    return errors, metrics


def check_mechanism_dynamics(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    for field in (
        "units_checked",
        "initial_conditions_checked",
        "boundary_conditions_checked",
        "limiting_cases_checked",
        "numerical_stability_checked",
    ):
        required_true(evidence, field, errors)
    refinement_error = required_number(
        evidence, "time_step_refinement_error", errors, minimum=0
    )
    maximum_error = threshold_number(
        thresholds, "maximum_time_step_refinement_error", errors, minimum=0
    )
    if refinement_error is not None:
        metrics["time_step_refinement_error"] = refinement_error
        if maximum_error is not None and refinement_error > maximum_error:
            errors.append(
                f"time_step_refinement_error={refinement_error:g} exceeds declared "
                f"threshold {maximum_error:g}"
            )
    return errors, metrics


def check_causal_econometric(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    required_text(evidence, "identification_strategy", errors)
    for field in (
        "identification_assumptions_checked",
        "overlap_or_support_checked",
        "falsification_checked",
        "robust_inference_checked",
    ):
        required_true(evidence, field, errors)
    sample_size = required_number(evidence, "sample_size", errors, minimum=1)
    minimum_size = threshold_number(
        thresholds, "minimum_sample_size", errors, minimum=1
    )
    estimate = required_number(evidence, "effect_estimate", errors)
    standard_error = required_number(evidence, "standard_error", errors, minimum=0)
    sensitivity_shift = required_number(
        evidence, "relative_sensitivity_shift", errors, minimum=0
    )
    maximum_shift = threshold_number(
        thresholds, "maximum_relative_sensitivity_shift", errors, minimum=0
    )
    if sample_size is not None:
        metrics["sample_size"] = sample_size
        if minimum_size is not None and sample_size < minimum_size:
            errors.append(
                f"sample_size={sample_size:g} is below declared threshold "
                f"{minimum_size:g}"
            )
    if estimate is not None:
        metrics["effect_estimate"] = estimate
    if standard_error is not None:
        metrics["standard_error"] = standard_error
    if sensitivity_shift is not None:
        metrics["relative_sensitivity_shift"] = sensitivity_shift
        if maximum_shift is not None and sensitivity_shift > maximum_shift:
            errors.append(
                f"relative_sensitivity_shift={sensitivity_shift:g} exceeds "
                f"declared threshold {maximum_shift:g}"
            )
    return errors, metrics


def check_unsupervised(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    for field in (
        "scaling_checked",
        "cluster_or_component_choice_justified",
        "stability_checked",
        "baseline_compared",
    ):
        required_true(evidence, field, errors)
    sample_size = required_number(evidence, "sample_size", errors, minimum=2)
    stability = required_number(
        evidence, "stability_score", errors, minimum=0, maximum=1
    )
    quality = required_number(
        evidence, "quality_score", errors, minimum=-1, maximum=1
    )
    minimum_size = threshold_number(
        thresholds, "minimum_sample_size", errors, minimum=2
    )
    minimum_stability = threshold_number(
        thresholds, "minimum_stability_score", errors, minimum=0
    )
    minimum_quality = threshold_number(
        thresholds, "minimum_quality_score", errors, minimum=-1
    )
    if minimum_stability is not None and minimum_stability > 1:
        errors.append("thresholds.minimum_stability_score must not exceed 1")
    if minimum_quality is not None and minimum_quality > 1:
        errors.append("thresholds.minimum_quality_score must not exceed 1")
    for name, observed, threshold in (
        ("sample_size", sample_size, minimum_size),
        ("stability_score", stability, minimum_stability),
        ("quality_score", quality, minimum_quality),
    ):
        if observed is not None:
            metrics[name] = observed
            if threshold is not None and observed < threshold:
                errors.append(
                    f"{name}={observed:g} is below declared threshold {threshold:g}"
                )
    return errors, metrics


def check_queueing_reliability(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    for field in (
        "flow_or_probability_balance_checked",
        "stationarity_or_horizon_justified",
        "analytic_or_simulation_crosscheck",
        "transient_or_warmup_checked",
    ):
        required_true(evidence, field, errors)
    analysis_type = required_text(evidence, "analysis_type", errors).lower()
    if analysis_type not in {"queueing", "reliability"}:
        errors.append("analysis_type must be 'queueing' or 'reliability'")
    relative_error = required_number(
        evidence, "crosscheck_relative_error", errors, minimum=0
    )
    maximum_error = threshold_number(
        thresholds, "maximum_crosscheck_relative_error", errors, minimum=0
    )
    if analysis_type == "queueing":
        utilization = required_number(
            evidence, "maximum_utilization", errors, minimum=0
        )
        finite_horizon = evidence.get("finite_horizon_only") is True
        maximum_utilization = None
        if finite_horizon:
            required_true(evidence, "finite_horizon_capacity_checked", errors)
        else:
            maximum_utilization = threshold_number(
                thresholds, "maximum_utilization", errors, minimum=0
            )
            if maximum_utilization is not None and maximum_utilization > 1:
                errors.append("thresholds.maximum_utilization must not exceed 1")
        if utilization is not None:
            metrics["maximum_utilization"] = utilization
            if utilization >= 1 and not finite_horizon:
                errors.append(
                    "maximum_utilization must be below 1 unless finite_horizon_only is true"
                )
            if maximum_utilization is not None and utilization > maximum_utilization:
                errors.append(
                    f"maximum_utilization={utilization:g} exceeds declared threshold "
                    f"{maximum_utilization:g}"
                )
    elif analysis_type == "reliability":
        required_true(evidence, "component_monotonicity_checked", errors)
        reliability = required_number(
            evidence, "system_reliability", errors, minimum=0, maximum=1
        )
        minimum_reliability = threshold_number(
            thresholds, "minimum_system_reliability", errors, minimum=0
        )
        if minimum_reliability is not None and minimum_reliability > 1:
            errors.append("thresholds.minimum_system_reliability must not exceed 1")
        if reliability is not None:
            metrics["system_reliability"] = reliability
            if (
                minimum_reliability is not None
                and reliability < minimum_reliability
            ):
                errors.append(
                    f"system_reliability={reliability:g} is below declared threshold "
                    f"{minimum_reliability:g}"
                )
    if relative_error is not None:
        metrics["crosscheck_relative_error"] = relative_error
        if maximum_error is not None and relative_error > maximum_error:
            errors.append(
                f"crosscheck_relative_error={relative_error:g} exceeds declared "
                f"threshold {maximum_error:g}"
            )
    return errors, metrics


def check_spatial_spatiotemporal(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    for field in (
        "crs_checked",
        "spatial_leakage_checked",
        "spatial_holdout_checked",
        "residual_spatial_dependence_checked",
    ):
        required_true(evidence, field, errors)
    holdout_regions = required_number(evidence, "holdout_regions", errors, minimum=1)
    model_metric = required_number(evidence, "model_metric", errors)
    baseline_metric = required_number(evidence, "baseline_metric", errors)
    direction = evidence.get("metric_direction")
    if direction not in {"lower", "higher"}:
        errors.append("metric_direction must be 'lower' or 'higher'")
    minimum_regions = threshold_number(
        thresholds, "minimum_holdout_regions", errors, minimum=1
    )
    minimum_improvement = threshold_number(
        thresholds, "minimum_relative_improvement", errors, minimum=0
    )
    if holdout_regions is not None:
        metrics["holdout_regions"] = holdout_regions
        if minimum_regions is not None and holdout_regions < minimum_regions:
            errors.append(
                f"holdout_regions={holdout_regions:g} is below declared threshold "
                f"{minimum_regions:g}"
            )
    if (
        model_metric is not None
        and baseline_metric is not None
        and direction in {"lower", "higher"}
    ):
        improvement = relative_improvement(model_metric, baseline_metric, direction)
        metrics["relative_improvement"] = improvement
        if minimum_improvement is not None and improvement < minimum_improvement:
            errors.append(
                f"relative improvement {improvement:g} is below declared threshold "
                f"{minimum_improvement:g}"
            )
    return errors, metrics


def check_multiobjective_dynamic_optimization(
    evidence: dict[str, Any], thresholds: dict[str, Any]
) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    metrics: dict[str, float] = {}
    for field in (
        "feasible",
        "constraint_audit",
        "pareto_or_recursion_checked",
        "baseline_compared",
        "solution_stability_checked",
    ):
        required_true(evidence, field, errors)
    required_text(evidence, "tradeoff_or_state_interpretation", errors)
    gap = required_number(evidence, "relative_gap", errors, minimum=0)
    instability = required_number(evidence, "solution_instability", errors, minimum=0)
    maximum_gap = threshold_number(
        thresholds, "maximum_relative_gap", errors, minimum=0
    )
    maximum_instability = threshold_number(
        thresholds, "maximum_solution_instability", errors, minimum=0
    )
    if gap is not None:
        metrics["relative_gap"] = gap
        if maximum_gap is not None and gap > maximum_gap:
            errors.append(
                f"relative_gap={gap:g} exceeds declared threshold {maximum_gap:g}"
            )
    if instability is not None:
        metrics["solution_instability"] = instability
        if maximum_instability is not None and instability > maximum_instability:
            errors.append(
                f"solution_instability={instability:g} exceeds declared threshold "
                f"{maximum_instability:g}"
            )
    return errors, metrics


ADAPTERS: dict[
    str,
    Callable[[dict[str, Any], dict[str, Any]], tuple[list[str], dict[str, float]]],
] = {
    "regression_forecast": check_regression_forecast,
    "classification": check_classification,
    "optimization": check_optimization,
    "simulation_stochastic": check_simulation_stochastic,
    "network_ranking": check_network_ranking,
    "mechanism_dynamics": check_mechanism_dynamics,
    "causal_econometric": check_causal_econometric,
    "unsupervised": check_unsupervised,
    "queueing_reliability": check_queueing_reliability,
    "spatial_spatiotemporal": check_spatial_spatiotemporal,
    "multiobjective_dynamic_optimization": check_multiobjective_dynamic_optimization,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate declared evidence for supported model families."
    )
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest", type=Path, default=Path("reports/model_validation.json")
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else root / args.manifest
    out = args.out if args.out.is_absolute() else root / args.out
    errors: list[str] = []
    model_reports: list[dict[str, Any]] = []

    try:
        manifest.resolve().relative_to(root)
    except ValueError:
        errors.append("manifest must stay inside the project directory")
    try:
        out.resolve().relative_to(root)
    except ValueError:
        raise SystemExit("output must stay inside the project directory")
    if manifest.resolve() == out.resolve():
        raise SystemExit("output must not overwrite the model validation manifest")

    models, manifest_errors = (
        load_manifest(manifest)
        if manifest.resolve().is_relative_to(root)
        else ([], [])
    )
    errors.extend(manifest_errors)
    if not models and not manifest_errors:
        errors.append("model validation manifest has no model rows")
    seen_ids: set[str] = set()

    for index, model in enumerate(models, 1):
        local_errors: list[str] = []
        if not isinstance(model, dict):
            errors.append(f"models[{index}] must be an object")
            continue
        model_id = str(model.get("id") or model.get("model_id") or "").strip()
        family = str(model.get("family") or model.get("model_family") or "").strip()
        if not model_id:
            local_errors.append("id must be a non-empty string")
            model_id = f"models[{index}]"
        elif model_id in seen_ids:
            local_errors.append(f"duplicate model id: {model_id}")
        else:
            seen_ids.add(model_id)
        if family not in FAMILIES:
            local_errors.append(f"unsupported model family: {family!r}")
        thresholds = model.get("thresholds")
        if not isinstance(thresholds, dict):
            local_errors.append("thresholds must be an object")
            thresholds = {}

        evidence = model.get("evidence")
        evidence_file = str(model.get("evidence_file") or "").strip()
        evidence_path: Path | None = None
        if evidence is not None and evidence_file:
            local_errors.append("declare evidence or evidence_file, not both")
        elif evidence is None:
            if not evidence_file:
                local_errors.append("evidence_file is required when inline evidence is absent")
            else:
                evidence_path = safe_project_file(root, evidence_file)
                if evidence_path is None:
                    local_errors.append(
                        f"evidence_file must stay inside the project: {evidence_file}"
                    )
                elif not evidence_path.is_file():
                    local_errors.append(f"evidence file is missing: {evidence_file}")
                else:
                    expected_hash = str(model.get("evidence_sha256") or "").strip().lower()
                    if expected_hash and sha256_file(evidence_path) != expected_hash:
                        local_errors.append(
                            f"evidence SHA-256 mismatch for {evidence_file}"
                        )
                    try:
                        evidence = json.loads(
                            evidence_path.read_text(encoding="utf-8-sig")
                        )
                    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                        local_errors.append(
                            f"cannot read evidence file {evidence_file}: {exc}"
                        )
        if evidence is not None and not isinstance(evidence, dict):
            local_errors.append("evidence must be a JSON object")
            evidence = None

        metrics: dict[str, float] = {}
        if (
            evidence is not None
            and family in ADAPTERS
            and isinstance(thresholds, dict)
        ):
            adapter_errors, metrics = ADAPTERS[family](evidence, thresholds)
            local_errors.extend(adapter_errors)
        model_reports.append(
            {
                "id": model_id,
                "family": family,
                "status": "PASS" if not local_errors else "FAIL",
                "evidence_file": evidence_file or None,
                "metrics": metrics,
                "errors": local_errors,
            }
        )
        errors.extend(f"{model_id}: {error}" for error in local_errors)

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "declared model-family evidence and numeric acceptance thresholds only; "
            "does not prove mathematical correctness, model suitability, or award level"
        ),
        "counts": {
            "models": len(model_reports),
            "passed": sum(item["status"] == "PASS" for item in model_reports),
            "failed": sum(item["status"] == "FAIL" for item in model_reports),
            "families": len({item["family"] for item in model_reports}),
        },
        "models": model_reports,
        "errors": errors,
        "manifest_sha256": sha256_file(manifest) if manifest.is_file() else "",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
