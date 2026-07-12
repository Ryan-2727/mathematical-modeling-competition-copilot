#!/usr/bin/env python3
"""Build a hash manifest and verify contest submission artifacts before freezing."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_pages(path: Path) -> int | None:
    result = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--max-paper-mb", type=float, default=20)
    parser.add_argument("--max-support-mb", type=float, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    errors: list[str] = []
    if args.paper.suffix.lower() != ".pdf": errors.append("paper must be PDF")
    if not args.paper.exists(): errors.append("paper is missing")
    artifacts = []
    for label, path, limit in (("paper", args.paper, args.max_paper_mb), ("support", args.support, args.max_support_mb)):
        if path is None: continue
        if not path.exists():
            errors.append(f"{label} is missing")
            continue
        size = path.stat().st_size
        if size > limit * 1024 * 1024: errors.append(f"{label} exceeds {limit} MB")
        artifacts.append({"role": label, "file": path.name, "bytes": size, "sha256": sha256(path), "pages": pdf_pages(path) if path.suffix.lower() == ".pdf" else None})
    manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "status": "PASS" if not errors else "FAIL", "errors": errors, "artifacts": artifacts}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(manifest["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
