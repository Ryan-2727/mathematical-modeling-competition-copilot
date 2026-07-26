#!/usr/bin/env python3
"""Record available solver/runtime capabilities without installing anything."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import platform
import sys
from pathlib import Path


PROFILES = {
    "linear_programming": ("scipy",),
    "mixed_integer": ("scipy",),
    "nonlinear": ("scipy",),
    "causal": ("statsmodels",),
    "spreadsheet": ("openpyxl",),
}


def package_record(name: str) -> dict[str, object]:
    available = importlib.util.find_spec(name) is not None
    version: str | None = None
    if available:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return {"package": name, "available": available, "version": version}


def output_path(root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("output path must be relative to --project-dir")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("output path escapes --project-dir") from exc
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe installed runtimes and lock the solver capability decision."
    )
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", default="reports/runtime_capabilities.json")
    parser.add_argument("--require", action="append", choices=sorted(PROFILES))
    parser.add_argument(
        "--strict", action="store_true", help="return 2 when a requested capability is unavailable"
    )
    args = parser.parse_args()
    root = args.project_dir.resolve()
    try:
        out = output_path(root, args.out)
    except ValueError as exc:
        raise SystemExit(str(exc))

    required = args.require or []
    packages = sorted({package for profile in required for package in PROFILES[profile]})
    records = [package_record(package) for package in packages]
    missing = [item["package"] for item in records if not item["available"]]
    status = "PASS" if not missing else "LIMITED"
    payload = {
        "schema_version": 1,
        "status": status,
        "scope": "observed local runtime availability; no dependency was installed or inferred",
        "required_profiles": required,
        "profiles": {name: list(PROFILES[name]) for name in required},
        "python": {"implementation": platform.python_implementation(), "version": platform.python_version(), "executable": sys.executable},
        "packages": records,
        "missing_packages": missing,
        "decision": "select an available method or record LIMITED/blocked; do not silently substitute a solver",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    return 2 if args.strict and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
