from __future__ import annotations

import math
from typing import Any

from .common import as_finite, choose_backend, success


def _parse(payload: dict[str, Any]) -> tuple[list[float], list[list[int]]]:
    raw_support = payload.get("support")
    if not isinstance(raw_support, list) or len(raw_support) < 2:
        raise ValueError("support must contain at least two ordered values")
    support = sorted({as_finite(value, "support value") for value in raw_support})
    if len(support) != len(raw_support):
        raise ValueError("support values must be unique")
    raw_intervals = payload.get("intervals")
    if not isinstance(raw_intervals, list) or not raw_intervals:
        raise ValueError("intervals must be a non-empty list")
    allowed: list[list[int]] = []
    for index, item in enumerate(raw_intervals, 1):
        if not isinstance(item, dict):
            raise ValueError(f"interval {index} must be an object")
        lower = None if item.get("lower") is None else as_finite(item["lower"], "lower")
        upper = None if item.get("upper") is None else as_finite(item["upper"], "upper")
        if lower is not None and upper is not None and lower > upper:
            raise ValueError(f"interval {index} has lower greater than upper")
        choices = [
            position
            for position, value in enumerate(support)
            if (lower is None or value >= lower - 1e-12)
            and (upper is None or value <= upper + 1e-12)
        ]
        if not choices:
            raise ValueError(f"interval {index} contains no support point")
        allowed.append(choices)
    return support, allowed


def _stdlib(
    support: list[float], allowed: list[list[int]], tolerance: float, max_iter: int
) -> tuple[list[float], int, bool]:
    probabilities = [1.0 / len(support)] * len(support)
    for iteration in range(1, max_iter + 1):
        counts = [0.0] * len(support)
        for choices in allowed:
            denominator = sum(probabilities[index] for index in choices)
            if denominator <= 0:
                raise ArithmeticError("interval likelihood collapsed to zero")
            for index in choices:
                counts[index] += probabilities[index] / denominator
        updated = [value / len(allowed) for value in counts]
        change = max(abs(left - right) for left, right in zip(updated, probabilities))
        probabilities = updated
        if change <= tolerance:
            return probabilities, iteration, True
    return probabilities, max_iter, False


def _scientific(
    support: list[float], allowed: list[list[int]], tolerance: float, max_iter: int
) -> tuple[list[float], int, bool]:
    import numpy as np

    probabilities = np.full(len(support), 1.0 / len(support), dtype=float)
    masks = []
    for choices in allowed:
        mask = np.zeros(len(support), dtype=bool)
        mask[choices] = True
        masks.append(mask)
    for iteration in range(1, max_iter + 1):
        counts = np.zeros(len(support), dtype=float)
        for mask in masks:
            denominator = float(probabilities[mask].sum())
            if denominator <= 0:
                raise ArithmeticError("interval likelihood collapsed to zero")
            counts[mask] += probabilities[mask] / denominator
        updated = counts / len(masks)
        change = float(np.max(np.abs(updated - probabilities)))
        probabilities = updated
        if change <= tolerance:
            return probabilities.tolist(), iteration, True
    return probabilities.tolist(), max_iter, False


def run(payload: dict[str, Any], requested_backend: str) -> dict[str, Any]:
    backend, warnings = choose_backend(requested_backend, "numpy")
    if backend is None:
        return {
            "status": "LIMITED",
            "backend_used": None,
            "result": {},
            "diagnostics": {},
            "warnings": warnings,
            "errors": [],
        }
    support, allowed = _parse(payload)
    tolerance = as_finite(payload.get("tolerance", 1e-10), "tolerance")
    max_iter = int(payload.get("max_iterations", 10000))
    if tolerance <= 0 or max_iter < 1:
        raise ValueError("tolerance and max_iterations must be positive")
    probabilities, iterations, converged = (
        _scientific(support, allowed, tolerance, max_iter)
        if backend == "scientific"
        else _stdlib(support, allowed, tolerance, max_iter)
    )
    cumulative = []
    total = 0.0
    for value in probabilities:
        total += value
        cumulative.append(total)
    median_index = next(index for index, value in enumerate(cumulative) if value >= 0.5)
    entropy = -sum(value * math.log(value) for value in probabilities if value > 0)
    unique_patterns = {tuple(choices) for choices in allowed}
    weakly_identified = len(unique_patterns) == 1 and len(next(iter(unique_patterns))) > 1
    status = "PASS" if converged and not weakly_identified else "LIMITED"
    if not converged:
        warnings.append("interval-censored EM did not reach the declared tolerance")
    if weakly_identified:
        warnings.append("all observations imply the same broad interval; timing is weakly identified")
    return success(
        backend,
        {
            "support": support,
            "probabilities": probabilities,
            "cdf": cumulative,
            "median": support[median_index],
        },
        {
            "iterations": iterations,
            "converged": converged,
            "entropy": entropy,
            "unique_interval_patterns": len(unique_patterns),
            "weakly_identified": weakly_identified,
        },
        warnings,
        status=status,
    )
