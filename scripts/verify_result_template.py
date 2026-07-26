#!/usr/bin/env python3
"""Inspect a declared output template without copying or treating it as data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_file(root: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def inspect_template(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        nonempty = sum(bool(any(cell.strip() for cell in row)) for row in rows)
        return {"format": "csv", "nonempty_rows": nonempty, "prefilled": nonempty > 1}
    if suffix in {".xlsx", ".xlsm"}:
        try:
            with zipfile.ZipFile(path) as archive:
                sheets = [name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
                values = sum(archive.read(name).count(b"<v>") + archive.read(name).count(b"inlineStr") for name in sheets)
        except (OSError, zipfile.BadZipFile) as exc:
            raise ValueError(f"cannot inspect workbook container: {exc}") from exc
        return {"format": suffix[1:], "sheets": len(sheets), "cell_value_markers": values, "prefilled": values > 1}
    raise ValueError("template must be CSV, XLSX, or XLSM")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect an explicitly declared result template.")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--template", required=True, help="relative path explicitly approved as a template")
    parser.add_argument("--out", default="reports/result_template_audit.json")
    parser.add_argument("--allow-prefilled", action="store_true", help="record that a human reviewed prefilled example values")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    template = project_file(root, args.template)
    out = project_file(root, args.out)
    if template is None or out is None:
        raise SystemExit("template and output must stay inside --project-dir")
    errors: list[str] = []
    inspection: dict[str, Any] = {}
    if not template.is_file():
        errors.append("declared template is missing")
    else:
        try:
            inspection = inspect_template(template)
        except ValueError as exc:
            errors.append(str(exc))
    prefilled = bool(inspection.get("prefilled"))
    if prefilled and not args.allow_prefilled:
        status = "LIMITED"
        errors.append("prefilled cells require human review and --allow-prefilled before use")
    else:
        status = "PASS" if not errors else "FAIL"
    report = {
        "schema_version": 1,
        "status": status,
        "scope": "structural template audit only; this tool never copies the template or treats its values as result evidence",
        "template": template.relative_to(root).as_posix() if template.is_file() else args.template,
        "sha256": sha256(template) if template.is_file() else None,
        "inspection": inspection,
        "human_review_of_prefilled_cells": bool(args.allow_prefilled),
        "errors": errors,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
    return 0 if status == "PASS" else (2 if status == "LIMITED" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
