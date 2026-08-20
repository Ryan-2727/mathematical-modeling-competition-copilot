#!/usr/bin/env python3
"""Run one bundled model kernel against an explicit JSON input."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from model_kernels import KERNELS, execute_kernel


KERNEL_VERSION = "1.0.0"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> int:
    errors: list[str] = []
    raw = b""
    source: dict[str, Any] = {}
    try:
        raw = args.input.read_bytes()
        loaded = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(loaded, dict):
            raise ValueError("kernel input must be a JSON object")
        source = loaded
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"cannot read kernel input: {exc}")
    if args.input.resolve() == args.output.resolve():
        errors.append("input and output paths must differ")
    if errors:
        result: dict[str, Any] = {
            "status": "FAIL",
            "backend_used": None,
            "result": {},
            "diagnostics": {},
            "warnings": [],
            "errors": errors,
        }
    else:
        result = execute_kernel(args.kernel, source, args.backend)
    payload = {
        "schema_version": 1,
        "kernel": args.kernel,
        "kernel_version": KERNEL_VERSION,
        "backend_requested": args.backend,
        "backend_used": result.get("backend_used"),
        "input_locator": args.input.as_posix() if not args.input.is_absolute() else args.input.name,
        "input_sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "status": result.get("status", "FAIL"),
        "result": result.get("result", {}),
        "diagnostics": result.get("diagnostics", {}),
        "warnings": result.get("warnings", []),
        "errors": result.get("errors", []),
    }
    try:
        write_json(args.output, payload)
    except (OSError, TypeError, ValueError) as exc:
        print(f"FAIL: cannot write kernel output: {exc}")
        return 1
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}.get(str(payload["status"]), 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel", choices=sorted(KERNELS), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--backend", choices=["auto", "stdlib", "scientific"], default="auto"
    )
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
