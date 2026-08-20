from __future__ import annotations

import math
from typing import Any

from .common import as_finite, choose_backend, success


def _parse_rows(payload: dict[str, Any]) -> list[list[float]]:
    raw = payload.get("compositions")
    if not isinstance(raw, list) or not raw:
        raise ValueError("compositions must be a non-empty matrix")
    rows: list[list[float]] = []
    width: int | None = None
    for row_index, raw_row in enumerate(raw, 1):
        if not isinstance(raw_row, list) or len(raw_row) < 2:
            raise ValueError(f"composition row {row_index} must contain at least two parts")
        row = [
            as_finite(value, f"composition row {row_index} value {index}")
            for index, value in enumerate(raw_row, 1)
        ]
        if any(value < 0 for value in row) or sum(row) <= 0:
            raise ValueError(f"composition row {row_index} must be nonnegative with positive sum")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("all composition rows must have equal width")
        rows.append(row)
    return rows


def _stdlib(rows: list[list[float]], delta: float) -> tuple[Any, ...]:
    closed: list[list[float]] = []
    replaced: list[list[float]] = []
    clr: list[list[float]] = []
    zero_count = 0
    for row in rows:
        total = sum(row)
        normalized = [value / total for value in row]
        closed.append(normalized)
        zeros = sum(value == 0 for value in normalized)
        zero_count += zeros
        if zeros:
            if zeros * delta >= 1.0:
                raise ValueError("zero_replacement is too large for the row dimension")
            positive_total = sum(value for value in normalized if value > 0)
            adjusted = [
                delta if value == 0 else value * (1.0 - zeros * delta) / positive_total
                for value in normalized
            ]
        else:
            adjusted = normalized
        logs = [math.log(value) for value in adjusted]
        mean_log = sum(logs) / len(logs)
        replaced.append(adjusted)
        clr.append([value - mean_log for value in logs])
    return closed, replaced, clr, zero_count


def _scientific(rows: list[list[float]], delta: float) -> tuple[Any, ...]:
    import numpy as np

    matrix = np.asarray(rows, dtype=float)
    closed = matrix / matrix.sum(axis=1, keepdims=True)
    replaced = closed.copy()
    zero_count = int(np.count_nonzero(replaced == 0.0))
    for index in range(replaced.shape[0]):
        mask = replaced[index] == 0.0
        zeros = int(mask.sum())
        if zeros:
            if zeros * delta >= 1.0:
                raise ValueError("zero_replacement is too large for the row dimension")
            positive_total = float(replaced[index, ~mask].sum())
            replaced[index, mask] = delta
            replaced[index, ~mask] *= (1.0 - zeros * delta) / positive_total
    logs = np.log(replaced)
    clr = logs - logs.mean(axis=1, keepdims=True)
    return closed.tolist(), replaced.tolist(), clr.tolist(), zero_count


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
    rows = _parse_rows(payload)
    delta = as_finite(payload.get("zero_replacement", 1e-4), "zero_replacement")
    if not 0 < delta < 0.5:
        raise ValueError("zero_replacement must be in (0, 0.5)")
    closed, replaced, clr, zero_count = (
        _scientific(rows, delta) if backend == "scientific" else _stdlib(rows, delta)
    )
    max_closure_error = max(abs(sum(row) - 1.0) for row in replaced)
    max_clr_sum = max(abs(sum(row)) for row in clr)
    return success(
        backend,
        {"closed": closed, "zero_replaced": replaced, "clr": clr},
        {
            "zero_count": zero_count,
            "maximum_closure_error": max_closure_error,
            "maximum_clr_sum_abs": max_clr_sum,
            "subcomposition_warning": zero_count > 0,
        },
        warnings,
    )
