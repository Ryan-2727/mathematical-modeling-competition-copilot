#!/usr/bin/env python3
"""Create a same-day, local-only AI/runtime capability snapshot for problem selection."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from problem_selection_core import (
    CAPABILITY_PROFILE,
    load_capability_profile,
    load_json_object,
    safe_project_file,
    sha256_file,
    skill_fingerprint,
)


PACKAGES = ("scipy", "statsmodels", "openpyxl")


def package_record(name: str) -> dict[str, object]:
    available = importlib.util.find_spec(name) is not None
    version: str | None = None
    if available:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return {"package": name, "available": available, "version": version}


def build_snapshot(root: Path, kernel_relative: str) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    profile, _ = load_capability_profile(errors)
    kernel_path = safe_project_file(root, kernel_relative)
    kernel_binding: dict[str, object] = {
        "path": kernel_relative,
        "sha256": None,
        "status": "MISSING",
    }
    if kernel_path is None:
        errors.append("kernel regression path is unsafe")
    elif not kernel_path.is_file():
        warnings.append(
            "bundled kernel regression is missing; run run_model_kernel_regression.py before calibrated probabilities"
        )
    else:
        try:
            regression = load_json_object(kernel_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"cannot read kernel regression: {exc}")
        else:
            kernel_binding.update(
                sha256=sha256_file(kernel_path), status=str(regression.get("status") or "").upper()
            )
            if regression.get("status") != "PASS" or regression.get("kernel_count", 0) < 1:
                warnings.append("bundled kernel regression is not PASS")
    packages = [package_record(name) for name in PACKAGES]
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    generated = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "status": status,
        "valid_for_calibration": status == "PASS",
        "generated_at_utc": generated,
        "scope": (
            "Observed local AI/runtime availability and bundled synthetic-kernel evidence; "
            "this is not a student-team capability score."
        ),
        "profile_version": profile.get("profile_version"),
        "profile_sha256": sha256_file(CAPABILITY_PROFILE) if CAPABILITY_PROFILE.is_file() else None,
        "skill_fingerprint": skill_fingerprint(),
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "platform": platform.system(),
        },
        "runtime_packages": packages,
        "available_solver_routes": {
            "linear_nonlinear_mip": next(
                (bool(item["available"]) for item in packages if item["package"] == "scipy"), False
            ),
            "causal_statistics": next(
                (bool(item["available"]) for item in packages if item["package"] == "statsmodels"), False
            ),
            "spreadsheet": next(
                (bool(item["available"]) for item in packages if item["package"] == "openpyxl"), False
            ),
            "stdlib_fallback": True,
        },
        "kernel_regression": kernel_binding,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--kernel-regression", default="reports/kernel-regression-stdlib.json")
    parser.add_argument("--out", default="reports/ai_capability_snapshot.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    out = safe_project_file(root, args.out)
    if out is None:
        raise SystemExit("--out must be a relative path inside the project")
    payload = build_snapshot(root, args.kernel_regression)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return {"PASS": 0, "LIMITED": 2, "FAIL": 1}[str(payload["status"])]


if __name__ == "__main__":
    raise SystemExit(main())
