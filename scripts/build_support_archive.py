#!/usr/bin/env python3
"""Create a ZIP support package from an explicit, auditable file list."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--include", action="append", required=True, help="relative file path; repeat for each artifact")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    files = []
    for relative in args.include:
        path = (args.project_dir / relative).resolve()
        if not path.is_file() or args.project_dir.resolve() not in path.parents:
            raise SystemExit(f"invalid support artifact: {relative}")
        files.append(path)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(args.project_dir))
    manifest = {"archive": args.out.name, "files": [str(path.relative_to(args.project_dir)) for path in files], "bytes": args.out.stat().st_size}
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
