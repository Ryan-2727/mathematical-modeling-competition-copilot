"""Small auditable reference kernels for recurring CUMCM B/C structures."""
from __future__ import annotations

from typing import Any, Callable

from . import bearing, composition, coverage, interval_censored, robust_allocation


Kernel = Callable[[dict[str, Any], str], dict[str, Any]]

KERNELS: dict[str, Kernel] = {
    "bearing-only-localization": bearing.run,
    "coverage-path-planning": coverage.run,
    "compositional-data": composition.run,
    "interval-censored-timing": interval_censored.run,
    "robust-binary-allocation": robust_allocation.run,
}


def execute_kernel(
    kernel_id: str, payload: dict[str, Any], backend: str = "auto"
) -> dict[str, Any]:
    if kernel_id not in KERNELS:
        return {
            "status": "FAIL",
            "backend_used": None,
            "result": {},
            "diagnostics": {},
            "warnings": [],
            "errors": [f"unknown kernel: {kernel_id}"],
        }
    if backend not in {"auto", "stdlib", "scientific"}:
        return {
            "status": "FAIL",
            "backend_used": None,
            "result": {},
            "diagnostics": {},
            "warnings": [],
            "errors": [f"unsupported backend: {backend}"],
        }
    if not isinstance(payload, dict):
        return {
            "status": "FAIL",
            "backend_used": None,
            "result": {},
            "diagnostics": {},
            "warnings": [],
            "errors": ["kernel input must be a JSON object"],
        }
    try:
        result = KERNELS[kernel_id](payload, backend)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        result = {
            "status": "FAIL",
            "backend_used": None,
            "result": {},
            "diagnostics": {},
            "warnings": [],
            "errors": [str(exc)],
        }
    for field, default in (
        ("status", "FAIL"),
        ("backend_used", None),
        ("result", {}),
        ("diagnostics", {}),
        ("warnings", []),
        ("errors", []),
    ):
        result.setdefault(field, default)
    return result


__all__ = ["KERNELS", "execute_kernel"]
