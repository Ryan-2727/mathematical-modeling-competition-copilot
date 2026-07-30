#!/usr/bin/env python3
"""Bind rendered figures to evidence and create optional visual-review previews."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


COMPLETE = {"pass", "verified", "complete", "accepted"}
REVIEW_FIELDS = (
    "clipping_check",
    "overlap_check",
    "axis_crowding_check",
    "panel_spacing",
    "visual_hierarchy",
    "grayscale_check",
    "colorblind_check",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {relative}") from exc
    return path


def png_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or len(header) < 24:
        return None
    return struct.unpack(">II", header[16:24])


def load_image(path: Path, pdftoppm: str | None, temp: Path) -> Any | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    candidate = path
    if path.suffix.lower() == ".pdf":
        if pdftoppm is None:
            return None
        target = temp / "figure"
        completed = subprocess.run(
            [pdftoppm, "-f", "1", "-singlefile", "-png", "-r", "180", str(path), str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            return None
        candidate = target.with_suffix(".png")
    try:
        return Image.open(candidate).convert("RGB")
    except (OSError, ValueError):
        return None


def number(raw: str) -> float | None:
    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", raw)
    return float(match.group()) if match else None


def vector_geometry(
    path: Path,
    width_cm: float,
    pdftotext: str | None,
    temp: Path,
) -> dict[str, float | str | None]:
    result: dict[str, float | str | None] = {
        "source": None,
        "min_text_pt": None,
        "min_line_pt": None,
    }
    width_pt = width_cm / 2.54 * 72.0
    if path.suffix.lower() == ".svg":
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError):
            return result
        view_box = str(root.attrib.get("viewBox") or "").split()
        view_width = (
            number(view_box[2])
            if len(view_box) == 4
            else number(str(root.attrib.get("width") or ""))
        )
        if not view_width or view_width <= 0:
            return result
        font_sizes: list[float] = []
        line_widths: list[float] = []
        for element in root.iter():
            style = str(element.attrib.get("style") or "")
            font = number(str(element.attrib.get("font-size") or ""))
            stroke = number(str(element.attrib.get("stroke-width") or ""))
            if font is None:
                match = re.search(r"(?:^|;)\s*font-size\s*:\s*([^;]+)", style)
                font = number(match.group(1)) if match else None
            if stroke is None:
                match = re.search(r"(?:^|;)\s*stroke-width\s*:\s*([^;]+)", style)
                stroke = number(match.group(1)) if match else None
            if font and font > 0:
                font_sizes.append(font)
            if stroke and stroke > 0:
                line_widths.append(stroke)
        scale = width_pt / view_width
        result.update(
            {
                "source": "svg-geometry",
                "min_text_pt": round(min(font_sizes) * scale, 3)
                if font_sizes
                else None,
                "min_line_pt": round(min(line_widths) * scale, 3)
                if line_widths
                else None,
            }
        )
    elif path.suffix.lower() == ".pdf" and pdftotext:
        html = temp / "figure_bbox.html"
        completed = subprocess.run(
            [
                pdftotext,
                "-f",
                "1",
                "-l",
                "1",
                "-bbox",
                str(path),
                str(html),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0 or not html.is_file():
            return result
        try:
            document = ET.parse(html).getroot()
        except (OSError, ET.ParseError):
            return result
        page = next(
            (item for item in document.iter() if item.tag.endswith("page")), None
        )
        page_width = number(str(page.attrib.get("width") or "")) if page is not None else None
        heights = []
        for item in document.iter():
            if not item.tag.endswith("word"):
                continue
            lower = number(str(item.attrib.get("yMin") or ""))
            upper = number(str(item.attrib.get("yMax") or ""))
            if lower is not None and upper is not None and upper > lower:
                heights.append(upper - lower)
        if page_width and page_width > 0 and heights:
            result.update(
                {
                    "source": "pdftotext-bbox",
                    "min_text_pt": round(min(heights) * width_pt / page_width, 3),
                }
            )
    return result


def raster_metrics(image: Any) -> dict[str, float]:
    sample = image.copy()
    sample.thumbnail((1000, 1000))
    width, height = sample.size
    if width < 1 or height < 1:
        return {"edge_ink_ratio": 0.0, "grayscale_contrast": 0.0}
    pixels = sample.load()
    border = []
    for x in range(width):
        border.append(pixels[x, 0])
        border.append(pixels[x, height - 1])
    for y in range(1, max(1, height - 1)):
        border.append(pixels[0, y])
        border.append(pixels[width - 1, y])
    edge_ink = sum(1 for pixel in border if min(pixel) < 245)
    gray = sample.convert("L")
    minimum, maximum = gray.getextrema()
    return {
        "edge_ink_ratio": round(edge_ink / max(1, len(border)), 4),
        "grayscale_contrast": round((maximum - minimum) / 255.0, 4),
    }


def create_simulations(image: Any, target_base: Path) -> list[str]:
    from PIL import Image

    target_base.parent.mkdir(parents=True, exist_ok=True)
    gray = target_base.with_name(target_base.name + "_grayscale.png")
    image.convert("L").save(gray)
    pixels = []
    for red, green, blue in image.getdata():
        pixels.append(
            (
                int(0.625 * red + 0.375 * green),
                int(0.700 * red + 0.300 * green),
                int(0.300 * green + 0.700 * blue),
            )
        )
    simulated = Image.new("RGB", image.size)
    simulated.putdata(pixels)
    colorblind = target_base.with_name(target_base.name + "_deuteranopia.png")
    simulated.save(colorblind)
    return [gray.as_posix(), colorblind.as_posix()]


def page_overview(root: Path, pdftoppm: str | None) -> tuple[str | None, str | None]:
    pdf = root / "paper" / "main.pdf"
    if not pdf.is_file() or pdftoppm is None:
        return None, "paper overview unavailable: paper PDF or pdftoppm is missing"
    try:
        from PIL import Image, ImageOps, ImageDraw
    except ImportError:
        return None, "paper overview unavailable: Pillow is missing"
    output = root / "reports" / "paper_page_overview.png"
    with tempfile.TemporaryDirectory() as raw:
        prefix = Path(raw) / "page"
        completed = subprocess.run(
            [pdftoppm, "-png", "-r", "36", str(pdf), str(prefix)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        pages = sorted(Path(raw).glob("page-*.png"))
        if completed.returncode != 0 or not pages:
            return None, "paper overview rendering failed"
        thumbs = []
        for index, page in enumerate(pages, 1):
            with Image.open(page) as source:
                thumb = source.convert("RGB")
                thumb.thumbnail((240, 340))
                canvas = Image.new("RGB", (260, 380), "white")
                canvas.paste(thumb, ((260 - thumb.width) // 2, 20))
                draw = ImageDraw.Draw(canvas)
                draw.text((10, 355), f"Page {index}", fill="black")
                thumbs.append(ImageOps.expand(canvas, border=1, fill="gray"))
        columns = min(4, len(thumbs))
        rows = (len(thumbs) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * 262, rows * 382), "white")
        for index, thumb in enumerate(thumbs):
            sheet.paste(thumb, ((index % columns) * 262, (index // columns) * 382))
        output.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output)
    return output.relative_to(root).as_posix(), None


def verify(root: Path, profile: str) -> dict[str, Any]:
    manifest = root / "reports" / "rendered_figure_manifest.csv"
    errors: list[str] = []
    warnings: list[str] = []
    records: list[dict[str, Any]] = []
    try:
        with manifest.open(encoding="utf-8-sig", newline="") as handle:
            figure_rows = list(csv.DictReader(handle))
    except FileNotFoundError:
        figure_rows = []
        errors.append("reports/rendered_figure_manifest.csv is missing")
    pdftoppm = shutil.which("pdftoppm")
    pdftotext = shutil.which("pdftotext")
    try:
        import PIL  # noqa: F401

        pillow = True
    except ImportError:
        pillow = False
    preview_root = root / "reports" / "figure_previews"
    for line, row in enumerate(figure_rows, 2):
        row_errors: list[str] = []
        relative = str(row.get("figure") or "").strip()
        source_relative = str(row.get("source_data") or "").strip()
        command_id = str(row.get("generator_command_id") or "").strip()
        try:
            figure = safe_file(root, relative)
            source = safe_file(root, source_relative)
        except ValueError as exc:
            errors.append(f"row {line}: {exc}")
            continue
        if not figure.is_file() or not source.is_file():
            row_errors.append("figure or source data is missing")
        else:
            if str(row.get("figure_sha256") or "").strip().lower() != sha256(figure):
                row_errors.append("figure digest is stale")
            if str(row.get("source_sha256") or "").strip().lower() != sha256(source):
                row_errors.append("source-data digest is stale")
        if not command_id:
            row_errors.append("generator command identifier is missing")
        try:
            width_cm = float(str(row.get("insertion_width_cm") or ""))
            min_text = float(str(row.get("min_text_pt") or ""))
            min_line = float(str(row.get("min_line_pt") or ""))
        except ValueError:
            width_cm = min_text = min_line = 0.0
            row_errors.append("insertion width/text size/line width must be numeric")
        if width_cm <= 0:
            row_errors.append("insertion width must be positive")
        if min_text < 7.0:
            row_errors.append("minimum effective text size is below 7 pt")
        if min_line < 0.5:
            row_errors.append("minimum effective line width is below 0.5 pt")
        if not str(row.get("panel_order") or "").strip():
            row_errors.append("panel order is missing")
        for field in REVIEW_FIELDS:
            if str(row.get(field) or "").strip().lower() not in COMPLETE:
                row_errors.append(f"{field} lacks a verified human review")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            row_errors.append("row status is not verified")
        previews: list[str] = []
        pixel_size: tuple[int, int] | None = None
        effective_dpi: float | str | None = None
        geometry: dict[str, float | str | None] = {
            "source": None,
            "min_text_pt": None,
            "min_line_pt": None,
        }
        image_metrics: dict[str, float] = {}
        if figure.is_file():
            if figure.suffix.lower() == ".png":
                pixel_size = png_size(figure)
            with tempfile.TemporaryDirectory() as raw:
                geometry = vector_geometry(
                    figure, width_cm, pdftotext, Path(raw)
                )
                image = load_image(figure, pdftoppm, Path(raw)) if pillow else None
                if image is not None:
                    pixel_size = image.size
                    image_metrics = raster_metrics(image)
                    preview_base = preview_root / f"{line:03d}_{figure.stem}"
                    previews = [
                        str(Path(item).relative_to(root)).replace("\\", "/")
                        for item in create_simulations(image, preview_base)
                    ]
            if figure.suffix.lower() in {".pdf", ".svg"}:
                effective_dpi = "vector"
            elif pixel_size and width_cm > 0:
                effective_dpi = round(pixel_size[0] / (width_cm / 2.54), 1)
                if effective_dpi < 150:
                    row_errors.append("effective raster resolution is below 150 DPI")
        measured_text = geometry.get("min_text_pt")
        measured_line = geometry.get("min_line_pt")
        if isinstance(measured_text, float) and measured_text < 7.0:
            row_errors.append("rendered vector text is below 7 pt at insertion size")
        if isinstance(measured_line, float) and measured_line < 0.5:
            row_errors.append("rendered vector line width is below 0.5 pt at insertion size")
        if image_metrics.get("edge_ink_ratio", 0.0) > 0.6:
            message = f"row {line}: high edge-ink ratio needs a clipping/crop review"
            if profile == "strict":
                row_errors.append(message)
            elif profile == "standard":
                warnings.append(message)
        if not pillow or (figure.suffix.lower() == ".pdf" and pdftoppm is None):
            message = f"row {line}: optional rendered-image inspection unavailable"
            if profile == "strict":
                row_errors.append(message)
            elif profile != "minimal":
                warnings.append(message)
        errors.extend(f"row {line}: {item}" for item in row_errors)
        records.append(
            {
                "figure": relative,
                "source_data": source_relative,
                "pixel_size": pixel_size,
                "effective_dpi": effective_dpi,
                "vector_geometry": geometry,
                "raster_metrics": image_metrics,
                "preview_artifacts": previews,
                "errors": row_errors,
            }
        )
    if not figure_rows:
        errors.append("rendered figure manifest has no evidence rows")
    overview, overview_warning = page_overview(root, pdftoppm)
    if overview_warning:
        if profile == "strict":
            errors.append(overview_warning)
        elif profile != "minimal":
            warnings.append(overview_warning)
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    return {
        "status": status,
        "profile": profile,
        "scope": (
            "file bindings, insertion-size metadata, optional simulations, and "
            "human visual-review evidence; aesthetics are not automatically certified"
        ),
        "manifest_sha256": sha256(manifest) if manifest.is_file() else None,
        "tools": {
            "Pillow": pillow,
            "pdftoppm": pdftoppm,
            "pdftotext": pdftotext,
        },
        "paper_page_overview": overview,
        "figures": records,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--profile", choices=["minimal", "standard", "strict"], default="standard"
    )
    parser.add_argument("--out", default="reports/rendered_figure_verification.json")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    out = (root / args.out).resolve()
    try:
        out.relative_to(root / "reports")
    except ValueError as exc:
        raise SystemExit("output must stay inside project reports/") from exc
    try:
        payload = verify(root, args.profile)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        payload = {"status": "FAIL", "errors": [str(exc)], "warnings": []}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
