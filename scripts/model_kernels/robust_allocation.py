from __future__ import annotations

import itertools
import math
from typing import Any

from .common import as_finite, choose_backend, limited, success


def _parse(payload: dict[str, Any]) -> tuple[Any, ...]:
    raw = payload.get("items")
    if not isinstance(raw, list) or not raw:
        raise ValueError("items must be a non-empty list")
    items = []
    seen: set[str] = set()
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            raise ValueError(f"item {index} must be an object")
        item_id = str(item.get("id") or "").strip()
        if not item_id or item_id in seen:
            raise ValueError("item ids must be non-empty and unique")
        seen.add(item_id)
        cost = as_finite(item.get("cost"), f"item {item_id} cost")
        nominal = as_finite(item.get("nominal_value"), f"item {item_id} nominal_value")
        worst = as_finite(item.get("worst_value"), f"item {item_id} worst_value")
        if cost < 0:
            raise ValueError("item costs must be nonnegative")
        items.append((item_id, cost, nominal, worst))
    items.sort(key=lambda value: value[0])
    budget = as_finite(payload.get("budget"), "budget")
    min_items = int(payload.get("minimum_items", 0))
    required_worst = payload.get("required_worst_value")
    if required_worst is not None:
        required_worst = as_finite(required_worst, "required_worst_value")
    if budget < 0 or min_items < 0:
        raise ValueError("budget and minimum_items must be nonnegative")
    return items, budget, min_items, required_worst


def _values(items: list[tuple[str, float, float, float]], selected: list[int]) -> dict[str, Any]:
    chosen = [items[index] for index in selected]
    return {
        "selected_ids": [item[0] for item in chosen],
        "cost": sum(item[1] for item in chosen),
        "nominal_value": sum(item[2] for item in chosen),
        "worst_value": sum(item[3] for item in chosen),
    }


def _feasible(values: dict[str, Any], budget: float, min_items: int, required: float | None) -> bool:
    return (
        values["cost"] <= budget + 1e-9
        and len(values["selected_ids"]) >= min_items
        and (required is None or values["worst_value"] >= required - 1e-9)
    )


def _enumerate(
    items: list[tuple[str, float, float, float]],
    budget: float,
    min_items: int,
    required: float | None,
    objective: str,
) -> dict[str, Any] | None:
    best: tuple[tuple[Any, ...], dict[str, Any]] | None = None
    for bits in itertools.product((0, 1), repeat=len(items)):
        selected = [index for index, bit in enumerate(bits) if bit]
        values = _values(items, selected)
        if not _feasible(values, budget, min_items, required):
            continue
        primary = values["worst_value"] if objective == "worst" else values["nominal_value"]
        secondary = values["nominal_value"] if objective == "worst" else values["worst_value"]
        score = (primary, secondary, -values["cost"], tuple(values["selected_ids"]))
        if best is None or score > best[0]:
            best = (score, values)
    return None if best is None else best[1]


def _milp(
    items: list[tuple[str, float, float, float]],
    budget: float,
    min_items: int,
    required: float | None,
    objective: str,
) -> tuple[dict[str, Any] | None, str, float | None]:
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    costs = np.asarray([item[1] for item in items], dtype=float)
    nominal = np.asarray([item[2] for item in items], dtype=float)
    worst = np.asarray([item[3] for item in items], dtype=float)
    primary = worst if objective == "worst" else nominal
    secondary = nominal if objective == "worst" else worst
    coefficient = -(primary + 1e-8 * secondary - 1e-10 * costs)
    constraints = [LinearConstraint(costs, -np.inf, budget)]
    if min_items:
        constraints.append(LinearConstraint(np.ones(len(items)), min_items, np.inf))
    if required is not None:
        constraints.append(LinearConstraint(worst, required, np.inf))
    result = milp(
        coefficient,
        integrality=np.ones(len(items)),
        bounds=Bounds(np.zeros(len(items)), np.ones(len(items))),
        constraints=constraints,
        options={"time_limit": 10.0},
    )
    status = str(getattr(result, "message", "unknown"))
    gap = getattr(result, "mip_gap", None)
    gap_value = None if gap is None or not math.isfinite(float(gap)) else float(gap)
    if not bool(result.success) or result.x is None:
        return None, status, gap_value
    selected = [index for index, value in enumerate(result.x) if value >= 0.5]
    values = _values(items, selected)
    if not _feasible(values, budget, min_items, required):
        return None, "rounded MILP solution failed independent feasibility", gap_value
    return values, status, gap_value


def run(payload: dict[str, Any], requested_backend: str) -> dict[str, Any]:
    backend, warnings = choose_backend(requested_backend, "numpy", "scipy")
    if backend is None:
        return limited(warnings[0])
    items, budget, min_items, required = _parse(payload)
    if backend == "stdlib" and len(items) > 22:
        return limited("stdlib enumeration is intentionally limited to 22 binary items", backend)
    if backend == "scientific":
        robust, robust_status, robust_gap = _milp(
            items, budget, min_items, required, "worst"
        )
        baseline, baseline_status, baseline_gap = _milp(
            items, budget, min_items, required, "nominal"
        )
    else:
        robust = _enumerate(items, budget, min_items, required, "worst")
        baseline = _enumerate(items, budget, min_items, required, "nominal")
        robust_status = baseline_status = "complete enumeration"
        robust_gap = baseline_gap = 0.0
    if robust is None or baseline is None:
        return success(
            backend,
            {"robust": None, "baseline": None},
            {
                "feasible": False,
                "robust_solver_status": robust_status,
                "baseline_solver_status": baseline_status,
            },
            warnings + ["no allocation satisfies the declared constraints"],
            status="LIMITED",
        )
    feasibility_residual = max(0.0, robust["cost"] - budget)
    if required is not None:
        feasibility_residual = max(feasibility_residual, required - robust["worst_value"])
    return success(
        backend,
        {
            "robust": robust,
            "baseline": baseline,
            "worst_value_advantage": robust["worst_value"] - baseline["worst_value"],
            "nominal_price_of_robustness": baseline["nominal_value"] - robust["nominal_value"],
        },
        {
            "feasible": feasibility_residual <= 1e-9,
            "maximum_feasibility_residual": feasibility_residual,
            "robust_solver_status": robust_status,
            "baseline_solver_status": baseline_status,
            "robust_solver_gap": robust_gap,
            "baseline_solver_gap": baseline_gap,
            "independent_recalculation": True,
        },
        warnings,
    )
