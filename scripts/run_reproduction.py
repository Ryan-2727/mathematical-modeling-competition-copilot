#!/usr/bin/env python3
"""Run one declared pipeline and capture reproducibility evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--seed", default="0")
    parser.add_argument("--expected", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    env = os.environ.copy(); env["PYTHONHASHSEED"] = args.seed
    result = subprocess.run(args.command, cwd=args.project_dir, shell=True, text=True, capture_output=True, env=env)
    expected = []
    errors = []
    for item in args.expected:
        path = args.project_dir / item
        if not path.is_file(): errors.append(f"expected output missing: {item}")
        else: expected.append({"file": item, "sha256": sha256(path), "bytes": path.stat().st_size})
    payload = {"status": "PASS" if result.returncode == 0 and not errors else "FAIL", "created_at_utc": datetime.now(timezone.utc).isoformat(), "command": args.command, "seed": args.seed, "platform": platform.platform(), "returncode": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:], "expected_outputs": expected, "errors": errors}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
