#!/usr/bin/env python3
"""Run scoped PDF visual and metadata QA with Poppler when available."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PAGE_SIZES = {
    "A4": (595.28, 841.89),
    "letter": (612.0, 792.0),
}
DEFAULT_FORBIDDEN_TERMS = ("目录", "table of contents", "contents")
PATH_RE = re.compile(
    r"(?i)(?:[a-z]:[\\/](?:users|documents|desktop)[\\/]|"
    r"/(?:home|users)/[^/\s]+|file://|\\\\[^\\\s]+\\)"
)
IDENTITY_RE = re.compile(
    r"(?i)(?:university|college|school|institute|学院|大学|学校|赛区)"
)
FIGURE_TABLE_RE = re.compile(
    r"(?i)(?<![A-Za-z])"
    r"(?P<kind>figure|fig\.?|table|图|表)"
    r"\s*(?P<number>[A-Za-z]?\d+(?:[.-]\d+)*[A-Za-z]?)"
)


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def find_tool(name: str) -> str | None:
    primary = shutil.which(name)
    if (
        primary is None
        or os.name != "nt"
        or Path(primary).suffix.casefold() not in {".cmd", ".bat"}
    ):
        return primary
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / f"{name}.exe"
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            continue
    return primary


def parse_pdfinfo(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def parse_page_size(info: dict[str, str]) -> tuple[float, float] | None:
    value = info.get("Page size", "")
    match = re.search(r"([0-9.]+)\s+x\s+([0-9.]+)\s+pts", value, re.I)
    if not match:
        for key, candidate in info.items():
            if re.fullmatch(r"Page\s+\d+\s+size", key):
                match = re.search(r"([0-9.]+)\s+x\s+([0-9.]+)\s+pts", candidate, re.I)
                if match:
                    break
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def extracted_pages(text: str, expected_pages: int | None) -> list[str]:
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if expected_pages is not None:
        while len(pages) < expected_pages:
            pages.append("")
        pages = pages[:expected_pages]
    return pages


def normalized_visible_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def forbidden_hits(pages: list[str], terms: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    normalized_terms = {re.sub(r"\s+", " ", term).strip().casefold() for term in terms}
    for page_number, page in enumerate(pages, 1):
        for line_number, line in enumerate(page.splitlines(), 1):
            normalized = re.sub(r"\s+", " ", line).strip().casefold()
            if normalized in normalized_terms:
                hits.append(
                    {
                        "page": page_number,
                        "line": line_number,
                        "text": line.strip()[:160],
                    }
                )
    return hits


def figure_table_links(pages: list[str]) -> dict[str, Any]:
    """Classify caption/reference tokens with an explicitly heuristic rule."""
    labels: dict[str, dict[str, Any]] = {}
    for page_number, page in enumerate(pages, 1):
        for line_number, line in enumerate(page.splitlines(), 1):
            for match in FIGURE_TABLE_RE.finditer(line):
                raw_kind = match.group("kind").casefold().rstrip(".")
                kind = "figure" if raw_kind in {"figure", "fig", "图"} else "table"
                label = f"{kind}:{match.group('number').casefold()}"
                prefix = line[: match.start()]
                suffix = line[match.end() :].lstrip()
                reference_lead = re.match(
                    r"(?i)^(?:shows?|illustrates?|summarizes?|reports?|compares?|"
                    r"presents?|gives?|indicates?|demonstrates?|is|are|was|were|"
                    r"显示|汇总|给出|表明|说明|展示|比较|报告|可见|中|所示)",
                    suffix,
                )
                role = (
                    "caption"
                    if not prefix.strip() and reference_lead is None
                    else "reference"
                )
                entry = labels.setdefault(
                    label,
                    {
                        "label": label,
                        "caption_occurrences": [],
                        "reference_occurrences": [],
                    },
                )
                entry[f"{role}_occurrences"].append(
                    {
                        "page": page_number,
                        "line": line_number,
                        "text": line.strip()[:160],
                    }
                )

    issues: list[dict[str, Any]] = []
    for label, entry in sorted(labels.items()):
        caption_count = len(entry["caption_occurrences"])
        reference_count = len(entry["reference_occurrences"])
        if caption_count and not reference_count:
            issues.append(
                {
                    "label": label,
                    "type": "caption_without_body_reference",
                    "message": (
                        f"{label} appears only as a line-leading caption token; "
                        "verify that the body references it"
                    ),
                }
            )
        if reference_count and not caption_count:
            issues.append(
                {
                    "label": label,
                    "type": "reference_without_caption",
                    "message": (
                        f"{label} appears only as an inline reference; "
                        "verify that the caption exists"
                    ),
                }
            )
        if caption_count > 1:
            issues.append(
                {
                    "label": label,
                    "type": "duplicate_caption_token",
                    "message": (
                        f"{label} has {caption_count} line-leading caption tokens; "
                        "verify numbering and duplicate captions"
                    ),
                }
            )
    return {
        "method": (
            "heuristic: a line-leading Figure/Fig./Table/图/表 number token is "
            "classified as a caption; other occurrences are classified as references"
        ),
        "labels": [labels[label] for label in sorted(labels)],
        "issues": issues,
    }


def parse_pdfimages_list(text: str) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 14 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        if parts[2].casefold() != "image":
            continue
        try:
            images.append(
                {
                    "page": int(parts[0]),
                    "number": int(parts[1]),
                    "type": parts[2],
                    "width_pixels": int(parts[3]),
                    "height_pixels": int(parts[4]),
                    "x_ppi": float(parts[12]),
                    "y_ppi": float(parts[13]),
                }
            )
        except ValueError:
            continue
    return images


def inspect_metadata(
    info: dict[str, str],
    allow_author_metadata: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    author = info.get("Author", "").strip()
    if author and author.casefold() not in {"anonymous", "anonymized", "none", "n/a"}:
        message = f"PDF Author metadata is non-empty: {author[:120]}"
        if allow_author_metadata:
            warnings.append(message)
        else:
            errors.append(message)
    for key, value in info.items():
        if not value:
            continue
        if PATH_RE.search(value):
            errors.append(f"PDF metadata field {key} exposes a filesystem path")
        if key.casefold() in {"author", "creator"} and IDENTITY_RE.search(value):
            errors.append(f"PDF metadata field {key} may expose an institution")
    return errors, warnings


def verify_pdf(
    pdf: Path,
    *,
    min_pages: int = 1,
    max_pages: int | None = None,
    page_size: str | None = None,
    size_tolerance_pt: float = 2.0,
    sparse_threshold: int = 20,
    fail_on_sparse: bool = False,
    min_raster_ppi: float = 150.0,
    fail_on_low_raster: bool = False,
    first_page_markers: list[str] | None = None,
    forbidden_terms: list[str] | None = None,
    allow_author_metadata: bool = False,
    strict_tools: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    limitations: list[str] = []
    checks: dict[str, Any] = {}
    tool_paths = {
        name: find_tool(name)
        for name in ("pdfinfo", "pdftotext", "pdftoppm", "pdfimages")
    }
    readable_pdf = True

    if not pdf.is_file():
        errors.append("PDF is missing")
        readable_pdf = False
    elif pdf.suffix.lower() != ".pdf":
        errors.append("artifact does not have a .pdf extension")
        readable_pdf = False
    elif pdf.stat().st_size == 0:
        errors.append("PDF is empty")
        readable_pdf = False

    missing_tools = [name for name, path in tool_paths.items() if path is None]
    if missing_tools:
        message = "unavailable Poppler tools: " + ", ".join(missing_tools)
        if strict_tools:
            errors.append(message)
        else:
            limitations.append(message)
        if tool_paths["pdfinfo"] is None and (
            page_size is not None or max_pages is not None or min_pages != 1
        ):
            errors.append(
                "pdfinfo is required for the explicitly requested page count or size rule"
            )
        if tool_paths["pdftotext"] is None and (
            first_page_markers or fail_on_sparse
        ):
            errors.append(
                "pdftotext is required for the explicitly requested first-page "
                "or text-density rule"
            )

    page_count: int | None = None
    info: dict[str, str] = {}
    if readable_pdf and tool_paths["pdfinfo"]:
        result = run_command([tool_paths["pdfinfo"], str(pdf)])
        checks["pdfinfo_returncode"] = result.returncode
        if result.returncode != 0:
            errors.append("pdfinfo could not read the PDF")
            checks["pdfinfo_stderr"] = result.stderr[-1000:]
        else:
            info = parse_pdfinfo(result.stdout)
            try:
                page_count = int(info.get("Pages", ""))
            except ValueError:
                errors.append("pdfinfo did not report a valid page count")
            checks["pages"] = page_count
            if page_count is not None:
                if page_count < min_pages:
                    errors.append(f"PDF has {page_count} pages; minimum is {min_pages}")
                if max_pages is not None and page_count > max_pages:
                    errors.append(f"PDF has {page_count} pages; maximum is {max_pages}")
            actual_size = parse_page_size(info)
            checks["page_size_points"] = list(actual_size) if actual_size else None
            if actual_size is None:
                warnings.append("pdfinfo did not expose a parseable page size")
            elif page_size:
                expected = PAGE_SIZES[page_size]
                direct = (
                    abs(actual_size[0] - expected[0]) <= size_tolerance_pt
                    and abs(actual_size[1] - expected[1]) <= size_tolerance_pt
                )
                rotated = (
                    abs(actual_size[0] - expected[1]) <= size_tolerance_pt
                    and abs(actual_size[1] - expected[0]) <= size_tolerance_pt
                )
                if not (direct or rotated):
                    errors.append(
                        f"page size {actual_size[0]:.2f} x {actual_size[1]:.2f} pt "
                        f"does not match {page_size}"
                    )
            metadata_errors, metadata_warnings = inspect_metadata(
                info, allow_author_metadata
            )
            errors.extend(metadata_errors)
            warnings.extend(metadata_warnings)
            checks["metadata"] = {
                key: info[key]
                for key in (
                    "Title", "Subject", "Keywords", "Author", "Creator",
                    "Producer", "CreationDate", "ModDate",
                )
                if key in info
            }

    pages: list[str] = []
    if readable_pdf and tool_paths["pdftotext"]:
        result = run_command(
            [
                tool_paths["pdftotext"],
                "-layout",
                "-enc",
                "UTF-8",
                str(pdf),
                "-",
            ]
        )
        checks["pdftotext_returncode"] = result.returncode
        if result.returncode != 0:
            errors.append("pdftotext could not extract the PDF")
            checks["pdftotext_stderr"] = result.stderr[-1000:]
        else:
            pages = extracted_pages(result.stdout, page_count)
            text_counts = [len(normalized_visible_text(page)) for page in pages]
            blank_pages = [index for index, count in enumerate(text_counts, 1) if count == 0]
            sparse_pages = [
                index
                for index, count in enumerate(text_counts, 1)
                if 0 < count < sparse_threshold
            ]
            checks["text_characters_by_page"] = text_counts
            checks["blank_pages"] = blank_pages
            checks["sparse_pages"] = sparse_pages
            if blank_pages:
                message = (
                    "text-empty pages detected (image-only content may still exist): "
                    + ", ".join(map(str, blank_pages))
                )
                (errors if fail_on_sparse else warnings).append(message)
            if sparse_pages:
                message = (
                    f"text-sparse pages below {sparse_threshold} characters: "
                    + ", ".join(map(str, sparse_pages))
                )
                (errors if fail_on_sparse else warnings).append(message)

            markers = first_page_markers or []
            first_page = normalized_visible_text(pages[0]).casefold() if pages else ""
            missing_markers = [
                marker for marker in markers if marker.casefold() not in first_page
            ]
            checks["first_page_markers"] = {
                "required": markers,
                "missing": missing_markers,
            }
            if missing_markers:
                errors.append(
                    "first page is missing markers: " + ", ".join(missing_markers)
                )

            terms = list(
                DEFAULT_FORBIDDEN_TERMS
                if forbidden_terms is None
                else forbidden_terms
            )
            hits = forbidden_hits(pages, terms)
            checks["forbidden_term_hits"] = hits
            if hits:
                errors.append(
                    "forbidden table-of-contents heading detected on pages: "
                    + ", ".join(str(hit["page"]) for hit in hits)
                )
            links = figure_table_links(pages)
            checks["figure_table_links"] = links
            warnings.extend(
                "figure/table link heuristic: " + issue["message"]
                for issue in links["issues"]
            )

    if readable_pdf and tool_paths["pdftoppm"]:
        with tempfile.TemporaryDirectory(prefix="pdf-visual-qa-") as raw:
            prefix = Path(raw) / "page"
            result = run_command(
                [
                    tool_paths["pdftoppm"],
                    "-png",
                    "-r",
                    "72",
                    str(pdf),
                    str(prefix),
                ]
            )
            rendered = sorted(Path(raw).glob("page-*.png"))
            valid_rendered = [
                path for path in rendered if path.is_file() and path.stat().st_size > 0
            ]
            checks["render"] = {
                "returncode": result.returncode,
                "rendered_pages": len(valid_rendered),
            }
            if result.returncode != 0:
                errors.append("pdftoppm could not render the PDF")
                checks["render"]["stderr"] = result.stderr[-1000:]
            elif not valid_rendered:
                errors.append("pdftoppm produced no non-empty page images")
            elif page_count is not None and len(valid_rendered) != page_count:
                errors.append(
                    f"pdftoppm rendered {len(valid_rendered)} pages; "
                    f"pdfinfo reported {page_count}"
                )

    if readable_pdf and tool_paths["pdfimages"]:
        result = run_command([tool_paths["pdfimages"], "-list", str(pdf)])
        if result.returncode != 0:
            message = "pdfimages could not inspect embedded raster assets"
            if strict_tools:
                errors.append(message)
            else:
                limitations.append(message)
            checks["raster_assets"] = {
                "returncode": result.returncode,
                "stderr": result.stderr[-1000:],
                "minimum_ppi": min_raster_ppi,
                "images": [],
                "low_resolution": [],
            }
        else:
            images = parse_pdfimages_list(result.stdout)
            low_resolution = [
                image
                for image in images
                if min(image["x_ppi"], image["y_ppi"]) < min_raster_ppi
            ]
            checks["raster_assets"] = {
                "returncode": result.returncode,
                "minimum_ppi": min_raster_ppi,
                "images": images,
                "low_resolution": low_resolution,
            }
            if low_resolution:
                message = (
                    f"{len(low_resolution)} embedded raster image(s) are below "
                    f"{min_raster_ppi:g} PPI"
                )
                (errors if fail_on_low_raster else warnings).append(message)

    status = "FAIL" if errors else ("LIMITED" if limitations else "PASS")
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "scope": (
            "Poppler-backed page count, reported page size, extracted-text density, "
            "first-page markers, forbidden contents headings, rasterization success, "
            "heuristic figure/table caption-reference linkage, pdfimages-reported "
            "raster PPI, and selected metadata disclosure checks; this is not a proof "
            "of visual correctness, semantic linkage, or complete anonymity"
        ),
        "pdf": str(pdf),
        "tools": {
            name: {"available": path is not None, "path": path}
            for name, path in tool_paths.items()
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "limitations": limitations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-pages", type=int, default=1)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--page-size", choices=sorted(PAGE_SIZES))
    parser.add_argument("--size-tolerance-pt", type=float, default=2.0)
    parser.add_argument("--sparse-threshold", type=int, default=20)
    parser.add_argument("--fail-on-sparse", action="store_true")
    parser.add_argument("--min-raster-ppi", type=float, default=150.0)
    parser.add_argument("--fail-on-low-raster", action="store_true")
    parser.add_argument("--first-page-marker", action="append", default=[])
    parser.add_argument("--forbidden-term", action="append")
    parser.add_argument(
        "--allow-contents",
        action="store_true",
        help="Disable the default table-of-contents prohibition for profiles such as MCM/ICM.",
    )
    parser.add_argument("--allow-author-metadata", action="store_true")
    parser.add_argument("--strict-tools", action="store_true")
    args = parser.parse_args()
    if args.allow_contents and args.forbidden_term:
        parser.error("--allow-contents cannot be combined with --forbidden-term")
    payload = verify_pdf(
        args.pdf.resolve(),
        min_pages=args.min_pages,
        max_pages=args.max_pages,
        page_size=args.page_size,
        size_tolerance_pt=args.size_tolerance_pt,
        sparse_threshold=args.sparse_threshold,
        fail_on_sparse=args.fail_on_sparse,
        min_raster_ppi=args.min_raster_ppi,
        fail_on_low_raster=args.fail_on_low_raster,
        first_page_markers=args.first_page_marker,
        forbidden_terms=[] if args.allow_contents else args.forbidden_term,
        allow_author_metadata=args.allow_author_metadata,
        strict_tools=args.strict_tools,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(payload["status"])
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[payload["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
