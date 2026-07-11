#!/usr/bin/env python3
"""Measure reproducible features of exemplar images or LaTeX source."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def image_metrics(directory: Path) -> dict[str, object]:
    files = sorted(p for p in directory.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    result: dict[str, object] = {"image_pages": len(files), "dimensions": {}}
    try:
        from PIL import Image
    except ImportError:
        result["image_dimensions_available"] = False
        return result
    dims: dict[str, int] = {}
    for path in files:
        with Image.open(path) as image:
            key = f"{image.width}x{image.height}"
            dims[key] = dims.get(key, 0) + 1
    result["image_dimensions_available"] = True
    result["dimensions"] = dims
    return result


def text_metrics(directory: Path) -> dict[str, int]:
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in sorted(directory.glob("*.tex")))
    return {
        "section_commands": len(re.findall(r"\\(?:sub)*section\*?\{", text)),
        "equation_blocks": len(re.findall(r"\\begin\{(?:equation|align|gather)", text)),
        "figure_blocks": len(re.findall(r"\\begin\{figure", text)),
        "table_blocks": len(re.findall(r"\\begin\{table", text)),
        "labels": len(re.findall(r"\\label\{", text)),
        "references": len(re.findall(r"\\(?:ref|pageref|cite)\{", text)),
        "placeholders": len(re.findall(r"TODO|TBD|PLACEHOLDER|待补充|示例数据", text, re.I)),
        "bytes": len(text.encode("utf-8")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-dir", type=Path)
    parser.add_argument("--text-dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result: dict[str, object] = {}
    if args.images_dir:
        result.update(image_metrics(args.images_dir))
    if args.text_dir:
        result.update(text_metrics(args.text_dir))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
