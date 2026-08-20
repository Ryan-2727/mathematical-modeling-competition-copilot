from __future__ import annotations

import importlib.util
import math
from typing import Any


def scientific_available(*modules: str) -> bool:
    return all(importlib.util.find_spec(name) is not None for name in modules)


def choose_backend(requested: str, *modules: str) -> tuple[str | None, list[str]]:
    available = scientific_available(*modules)
    if requested == "stdlib":
        return "stdlib", []
    if requested == "scientific":
        if available:
            return "scientific", []
        return None, [
            "scientific backend requested but required packages are unavailable: "
            + ", ".join(modules)
        ]
    if available:
        return "scientific", []
    return "stdlib", [
        "scientific packages unavailable; used the declared stdlib fallback"
    ]


def as_finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def success(
    backend: str,
    result: dict[str, Any],
    diagnostics: dict[str, Any],
    warnings: list[str] | None = None,
    status: str = "PASS",
) -> dict[str, Any]:
    return {
        "status": status,
        "backend_used": backend,
        "result": result,
        "diagnostics": diagnostics,
        "warnings": list(warnings or []),
        "errors": [],
    }


def limited(message: str, backend: str | None = None) -> dict[str, Any]:
    return {
        "status": "LIMITED",
        "backend_used": backend,
        "result": {},
        "diagnostics": {},
        "warnings": [message],
        "errors": [],
    }
