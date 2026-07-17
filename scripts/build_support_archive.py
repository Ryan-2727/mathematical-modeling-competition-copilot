#!/usr/bin/env python3
"""Create a ZIP support package from an explicit, auditable file list."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path


INCLUDED = {"yes", "true", "1", "included"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def project_file(root: Path, relative: str) -> Path | None:
    path = Path(relative)
    if not relative or path.is_absolute() or ".." in path.parts:
        return None
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--include", action="append", default=[], help="relative file path; repeat for each artifact")
    parser.add_argument("--materials-manifest", type=Path, help="CSV manifest whose included rows should be packaged")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    relatives = list(args.include)
    if args.materials_manifest is not None:
        if args.materials_manifest.is_absolute():
            manifest_path = args.materials_manifest.resolve()
            try:
                manifest_relative = manifest_path.relative_to(root).as_posix()
            except ValueError:
                raise SystemExit("materials manifest must be inside the project directory")
        else:
            manifest_relative = args.materials_manifest.as_posix()
            manifest_path = project_file(root, manifest_relative)
            if manifest_path is None:
                raise SystemExit("materials manifest must be inside the project directory")
        if not manifest_path.is_file():
            raise SystemExit(f"materials manifest is missing: {args.materials_manifest}")
        with manifest_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not {"path", "included"}.issubset(reader.fieldnames or []):
                raise SystemExit("materials manifest requires path and included columns")
            for row in reader:
                if (row.get("included") or "").strip().lower() in INCLUDED:
                    relatives.append((row.get("path") or "").strip())
        relatives.extend([
            manifest_relative,
            "support/README.md",
            "support/reproduction_commands.txt",
            "support/data_inventory.csv",
        ])
    if not relatives:
        raise SystemExit("no support artifacts were selected")
    files = []
    seen: set[Path] = set()
    generated_paths = {args.out.resolve(), args.manifest.resolve()}
    for relative in relatives:
        path = project_file(root, relative)
        if path is None or not path.is_file() or path in generated_paths:
            raise SystemExit(f"invalid support artifact: {relative}")
        if path not in seen:
            files.append(path)
            seen.add(path)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())
    manifest = {
        "archive": args.out.name,
        "files": [path.relative_to(root).as_posix() for path in files],
        "artifacts": [
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256(path),
            }
            for path in files
        ],
        "bytes": args.out.stat().st_size,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
