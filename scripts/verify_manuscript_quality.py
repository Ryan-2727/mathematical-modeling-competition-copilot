#!/usr/bin/env python3
"""Check deterministic LaTeX manuscript and figure-quality evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from verify_latex_compatibility import reachable_tex_files, source_fingerprint


ENV_RE = re.compile(
    r"\\begin\{(figure\*?|table\*?)\}(.*?)\\end\{\1\}", re.DOTALL
)
LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
REF_RE = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref)\{([^{}]+)\}")
GRAPHIC_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b|待补|占位", re.IGNORECASE)
UNRESOLVED_LOG = re.compile(
    r"(?:undefined references|undefined citations|Citation .* undefined|Reference .* undefined)",
    re.IGNORECASE,
)
OVERFULL_LOG = re.compile(r"Overfull \\[hv]box", re.IGNORECASE)
FIGURE_FIELDS = {
    "figure",
    "label",
    "source_data",
    "caption_insight",
    "axes_units",
    "color_accessibility",
    "status",
}
COMPLETE = {"verified", "pass", "complete"}
FIGURE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".eps"}
SOURCE_SENTINELS = {"not_applicable", "n/a", "team-generated diagram"}


def norm_path(value: str) -> str:
    return value.strip().replace("\\", "/").removeprefix("./")


def safe_file(base: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if not relative or candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError:
        return None
    return resolved


def graphic_matches(graphic: str, recorded: str) -> bool:
    if graphic == recorded:
        return True
    graphic_path = Path(graphic)
    recorded_path = Path(recorded)
    return (
        not graphic_path.suffix
        and recorded_path.suffix.lower() in FIGURE_EXTENSIONS
        and recorded_path.with_suffix("").as_posix() == graphic_path.as_posix()
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--fail-on-overfull", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    paper = root / "paper"
    errors: list[str] = []
    warnings: list[str] = []
    tex_files = reachable_tex_files(paper) if paper.is_dir() else []
    if not tex_files:
        errors.append("no reachable LaTeX files were found")
    tex = "\n".join(
        path.read_text(encoding="utf-8", errors="replace") for path in tex_files
    )
    if PLACEHOLDER_RE.search(tex):
        errors.append("reachable LaTeX contains a placeholder")
    if "??" in tex:
        errors.append("reachable LaTeX source contains unresolved ?? markers")
    refs = {
        item.strip()
        for group in REF_RE.findall(tex)
        for item in group.split(",")
        if item.strip()
    }
    all_labels = set(LABEL_RE.findall(tex))
    environments: list[dict[str, Any]] = []
    for kind, body in ENV_RE.findall(tex):
        labels = LABEL_RE.findall(body)
        has_caption = bool(re.search(r"\\caption(?:\[[^\]]*\])?\{", body))
        local: list[str] = []
        if not has_caption:
            local.append("missing caption")
        if len(labels) != 1:
            local.append("must contain exactly one label")
        elif labels[0] not in refs:
            local.append(f"label is not referenced in prose: {labels[0]}")
        environments.append(
            {
                "kind": kind,
                "labels": labels,
                "status": "PASS" if not local else "FAIL",
                "errors": local,
            }
        )
        errors.extend(f"{kind}: {item}" for item in local)
    for label in sorted(refs - all_labels):
        errors.append(f"LaTeX reference has no reachable label: {label}")
    graphics = {norm_path(item) for item in GRAPHIC_RE.findall(tex)}
    manifest = root / "reports" / "figure_manifest.csv"
    rows: list[dict[str, str]] = []
    fields: set[str] = set()
    if not manifest.is_file():
        errors.append("reports/figure_manifest.csv is missing")
    else:
        try:
            with manifest.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fields = set(reader.fieldnames or [])
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            errors.append(f"cannot read figure_manifest.csv: {exc}")
    if missing := FIGURE_FIELDS - fields:
        errors.append("figure_manifest.csv missing columns: " + ", ".join(sorted(missing)))
    recorded_graphics: set[str] = set()
    recorded_labels: set[str] = set()
    for line, row in enumerate(rows, 2):
        if any(not str(row.get(field) or "").strip() for field in FIGURE_FIELDS):
            errors.append(f"figure_manifest.csv:{line} has empty required fields")
        figure = norm_path(str(row.get("figure") or ""))
        label = str(row.get("label") or "").strip()
        recorded_graphics.add(figure)
        recorded_labels.add(label)
        figure_file = safe_file(paper, figure)
        if figure_file is None or not figure_file.is_file():
            errors.append(
                f"figure_manifest.csv:{line} figure is missing or outside paper/: {figure}"
            )
        source_data = str(row.get("source_data") or "").strip()
        if source_data.lower() not in SOURCE_SENTINELS:
            source_file = safe_file(root, source_data)
            if source_file is None or not source_file.is_file():
                errors.append(
                    f"figure_manifest.csv:{line} source_data is missing or unsafe: "
                    f"{source_data}"
                )
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            errors.append(f"figure_manifest.csv:{line} is not verified")
        if label and label not in all_labels:
            errors.append(f"figure_manifest.csv:{line} label is absent from LaTeX: {label}")
    for graphic in sorted(graphics):
        matches = {
            item
            for item in recorded_graphics
            if graphic_matches(graphic, item)
        }
        if not matches:
            errors.append(f"included graphic is missing from figure manifest: {graphic}")
    for label in sorted(recorded_labels - all_labels):
        errors.append(f"figure manifest contains unused label: {label}")
    overfull = 0
    unresolved = 0
    for log in (paper / "main.log", paper / "build" / "main.log"):
        if not log.is_file():
            continue
        log_text = log.read_text(encoding="utf-8", errors="replace")
        unresolved += len(UNRESOLVED_LOG.findall(log_text))
        overfull += len(OVERFULL_LOG.findall(log_text))
    if unresolved:
        errors.append(f"LaTeX logs contain {unresolved} unresolved citation/reference warnings")
    if overfull:
        message = f"LaTeX logs contain {overfull} overfull box warnings"
        if args.fail_on_overfull:
            errors.append(message)
        else:
            warnings.append(message)
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "reachable LaTeX structure, logs, and recorded figure evidence; "
            "visual interpretation still requires rendered-page inspection"
        ),
        "counts": {
            "reachable_tex_files": len(tex_files),
            "figure_table_environments": len(environments),
            "included_graphics": len(graphics),
            "figure_manifest_rows": len(rows),
            "overfull_boxes": overfull,
            "unresolved_log_warnings": unresolved,
        },
        "manuscript_source_sha256": source_fingerprint(paper)
        if paper.is_dir()
        else "",
        "figure_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()
        if manifest.is_file()
        else "",
        "environments": environments,
        "errors": errors,
        "warnings": warnings,
    }
    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
