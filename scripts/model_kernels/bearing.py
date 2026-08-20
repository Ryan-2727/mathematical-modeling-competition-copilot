from __future__ import annotations

import math
from typing import Any

from .common import as_finite, choose_backend, limited, success


def _observations(payload: dict[str, Any]) -> list[tuple[float, float, float]]:
    raw = payload.get("observations")
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError("observations must contain at least two bearings")
    unit = str(payload.get("angle_unit") or "degree").lower()
    if unit not in {"degree", "radian"}:
        raise ValueError("angle_unit must be degree or radian")
    parsed: list[tuple[float, float, float]] = []
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            raise ValueError(f"observation {index} must be an object")
        x = as_finite(item.get("x"), f"observation {index} x")
        y = as_finite(item.get("y"), f"observation {index} y")
        key = "bearing_deg" if unit == "degree" else "bearing_rad"
        angle = as_finite(item.get(key), f"observation {index} {key}")
        parsed.append((x, y, math.radians(angle) if unit == "degree" else angle))
    return parsed


def _residuals(
    observations: list[tuple[float, float, float]], position: tuple[float, float]
) -> tuple[float, float]:
    perpendicular: list[float] = []
    angular: list[float] = []
    px, py = position
    for x, y, angle in observations:
        nx, ny = -math.sin(angle), math.cos(angle)
        perpendicular.append(nx * (px - x) + ny * (py - y))
        predicted = math.atan2(py - y, px - x)
        delta = (predicted - angle + math.pi) % (2.0 * math.pi) - math.pi
        angular.append(abs(math.degrees(delta)))
    rms = math.sqrt(sum(value * value for value in perpendicular) / len(perpendicular))
    return rms, max(angular)


def _stdlib(observations: list[tuple[float, float, float]]) -> tuple[Any, ...]:
    a00 = a01 = a11 = r0 = r1 = 0.0
    for x, y, angle in observations:
        nx, ny = -math.sin(angle), math.cos(angle)
        rhs = nx * x + ny * y
        a00 += nx * nx
        a01 += nx * ny
        a11 += ny * ny
        r0 += nx * rhs
        r1 += ny * rhs
    determinant = a00 * a11 - a01 * a01
    trace = a00 + a11
    disc = max(0.0, trace * trace - 4.0 * determinant)
    eigen_min = (trace - math.sqrt(disc)) / 2.0
    eigen_max = (trace + math.sqrt(disc)) / 2.0
    condition = math.inf if eigen_min <= 1e-14 else eigen_max / eigen_min
    if determinant <= 1e-12 or not math.isfinite(condition):
        return None, determinant, condition, 1
    px = (r0 * a11 - r1 * a01) / determinant
    py = (a00 * r1 - a01 * r0) / determinant
    return (px, py), determinant, condition, 2


def _scientific(observations: list[tuple[float, float, float]]) -> tuple[Any, ...]:
    import numpy as np

    rows = []
    rhs = []
    for x, y, angle in observations:
        normal = [-math.sin(angle), math.cos(angle)]
        rows.append(normal)
        rhs.append(normal[0] * x + normal[1] * y)
    matrix = np.asarray(rows, dtype=float)
    vector = np.asarray(rhs, dtype=float)
    position, _, rank, _ = np.linalg.lstsq(matrix, vector, rcond=None)
    normal = matrix.T @ matrix
    determinant = float(np.linalg.det(normal))
    condition = float(np.linalg.cond(normal))
    if int(rank) < 2 or not math.isfinite(condition) or determinant <= 1e-12:
        return None, determinant, condition, int(rank)
    return (float(position[0]), float(position[1])), determinant, condition, int(rank)


def run(payload: dict[str, Any], requested_backend: str) -> dict[str, Any]:
    backend, warnings = choose_backend(requested_backend, "numpy")
    if backend is None:
        return limited(warnings[0])
    observations = _observations(payload)
    position, determinant, condition, rank = (
        _scientific(observations) if backend == "scientific" else _stdlib(observations)
    )
    limit = as_finite(payload.get("maximum_condition_number", 1e8), "maximum_condition_number")
    diagnostics = {
        "normal_matrix_determinant": determinant,
        "condition_number": condition if math.isfinite(condition) else None,
        "rank": rank,
        "identified": position is not None and condition <= limit,
    }
    if position is None or condition > limit:
        return success(
            backend,
            {"position": None},
            diagnostics,
            warnings + ["bearing geometry is rank deficient or practically unobservable"],
            status="LIMITED",
        )
    rms, maximum_angle = _residuals(observations, position)
    diagnostics.update(
        {
            "position_error_proxy": rms,
            "maximum_angular_residual_deg": maximum_angle,
        }
    )
    return success(
        backend,
        {"position": [position[0], position[1]]},
        diagnostics,
        warnings,
    )
