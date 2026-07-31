#!/usr/bin/env python3
"""Small dependency-free primitives shared by contest validators."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_project_path(root: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def read_csv_with_error(
    path: Path,
) -> tuple[list[dict[str, str]], set[str], str | None]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader), set(reader.fieldnames or []), None
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], set(), str(exc)


def read_csv_strict(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def read_csv_if_exists(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    if not path.is_file():
        return [], set()
    return read_csv_strict(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
