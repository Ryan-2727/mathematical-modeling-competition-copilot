from __future__ import annotations

import math
from typing import Any

from .common import as_finite, choose_backend, success


def _centers(length: float, spacing: float, swath: float) -> list[float]:
    radius = swath / 2.0
    if swath >= length:
        return [length / 2.0]
    centers = [radius]
    while centers[-1] + spacing < length - radius - 1e-12:
        centers.append(centers[-1] + spacing)
    if centers[-1] + radius < length - 1e-12:
        centers.append(length - radius)
    return centers


def _union_length(intervals: list[tuple[float, float]]) -> float:
    total = 0.0
    current_left: float | None = None
    current_right: float | None = None
    for left, right in sorted(intervals):
        if current_left is None:
            current_left, current_right = left, right
        elif left <= float(current_right) + 1e-12:
            current_right = max(float(current_right), right)
        else:
            total += float(current_right) - current_left
            current_left, current_right = left, right
    if current_left is not None:
        total += float(current_right) - current_left
    return total


def _grid_coverage(
    centers: list[float], cross_length: float, radius: float, points: int, scientific: bool
) -> float:
    if scientific:
        import numpy as np

        grid = (np.arange(points, dtype=float) + 0.5) * cross_length / points
        center_values = np.asarray(centers, dtype=float)
        covered = np.any(np.abs(grid[:, None] - center_values[None, :]) <= radius, axis=1)
        return float(np.mean(covered))
    covered = 0
    for index in range(points):
        value = (index + 0.5) * cross_length / points
        if any(abs(value - center) <= radius for center in centers):
            covered += 1
    return covered / points


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
    width = as_finite(payload.get("width"), "width")
    height = as_finite(payload.get("height"), "height")
    swath = as_finite(payload.get("swath_width"), "swath_width")
    spacing = as_finite(payload.get("sweep_spacing"), "sweep_spacing")
    target = as_finite(payload.get("minimum_coverage", 1.0), "minimum_coverage")
    points = int(payload.get("grid_points", 2001))
    if min(width, height, swath, spacing) <= 0 or points < 10:
        raise ValueError("dimensions, swath, spacing, and grid_points must be positive")
    if not 0 < target <= 1:
        raise ValueError("minimum_coverage must be in (0, 1]")
    axis = str(payload.get("sweep_axis") or "y").lower()
    if axis not in {"x", "y"}:
        raise ValueError("sweep_axis must be x or y")
    origin = payload.get("origin", [0.0, 0.0])
    if not isinstance(origin, list) or len(origin) != 2:
        raise ValueError("origin must contain x and y")
    ox = as_finite(origin[0], "origin x")
    oy = as_finite(origin[1], "origin y")
    cross_length, along_length = (width, height) if axis == "y" else (height, width)
    centers = _centers(cross_length, spacing, swath)
    radius = swath / 2.0
    intervals = [
        (max(0.0, center - radius), min(cross_length, center + radius))
        for center in centers
    ]
    coverage = _union_length(intervals) / cross_length
    grid_coverage = _grid_coverage(
        centers, cross_length, radius, points, backend == "scientific"
    )
    connectors = sum(abs(right - left) for left, right in zip(centers, centers[1:]))
    include_connectors = bool(payload.get("include_connectors", True))
    path_length = len(centers) * along_length + (connectors if include_connectors else 0.0)
    route: list[list[float]] = []
    for index, center in enumerate(centers):
        if axis == "y":
            endpoints = [[ox + center, oy], [ox + center, oy + height]]
        else:
            endpoints = [[ox, oy + center], [ox + width, oy + center]]
        route.extend(endpoints if index % 2 == 0 else list(reversed(endpoints)))
    feasible = coverage + 1e-12 >= target and grid_coverage + 1e-3 >= target
    status = "PASS" if feasible else "LIMITED"
    if not feasible:
        warnings.append("independent coverage check does not meet the declared target")
    return success(
        backend,
        {
            "line_centers": centers,
            "line_count": len(centers),
            "path_length": path_length,
            "route": route,
        },
        {
            "coverage_ratio": coverage,
            "independent_grid_coverage": grid_coverage,
            "uncovered_ratio": max(0.0, 1.0 - coverage),
            "maximum_center_spacing": max(
                (abs(right - left) for left, right in zip(centers, centers[1:])),
                default=0.0,
            ),
            "target_met": feasible,
        },
        warnings,
        status=status,
    )
