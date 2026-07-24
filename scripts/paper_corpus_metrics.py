#!/usr/bin/env python3
"""Generate and validate portable metadata manifests for local PDF corpora."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_pdfinfo(output: str) -> tuple[int | None, dict[str, float] | None]:
    pages: int | None = None
    page_size: dict[str, float] | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("Pages:"):
            value = line.split(":", 1)[1].strip()
            if value.isdigit():
                pages = int(value)
        elif line.startswith("Page size:"):
            value = line.split(":", 1)[1].strip()
            match = re.search(r"([0-9.]+)\s+x\s+([0-9.]+)\s+pts?", value)
            if match:
                page_size = {
                    "width_pt": float(match.group(1)),
                    "height_pt": float(match.group(2)),
                }
    return pages, page_size


def inspect_pdf(
    path: Path, pdfinfo_tool: str | None
) -> tuple[int | None, dict[str, float] | None, list[str], str]:
    if pdfinfo_tool is None:
        return None, None, ["pdfinfo is unavailable; page metrics were not inspected."], "unavailable"
    try:
        result = subprocess.run(
            [pdfinfo_tool, str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        return None, None, [f"pdfinfo could not start: {exc.__class__.__name__}."], "unavailable"
    if result.returncode != 0:
        return (
            None,
            None,
            [f"pdfinfo could not inspect this PDF (exit code {result.returncode})."],
            str(result.returncode),
        )
    pages, page_size = parse_pdfinfo(result.stdout)
    limitations: list[str] = []
    if pages is None:
        limitations.append("pdfinfo did not report a page count.")
    if page_size is None:
        limitations.append("pdfinfo did not report a page size in points.")
    return pages, page_size, limitations, str(result.returncode)


def is_portable_relative(value: str) -> bool:
    if not value or "\\" in value or WINDOWS_ABSOLUTE_RE.match(value):
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "." not in path.parts


def validate_iso_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def manifest_id(corpus_id: str, relative_path: str) -> str:
    relative_stem = PurePosixPath(relative_path).with_suffix("").as_posix()
    return f"{corpus_id.rstrip('/')}/{relative_stem}"


def legacy_summary(papers: list[dict[str, Any]]) -> dict[str, Any]:
    page_values = [paper["pages"] for paper in papers if isinstance(paper["pages"], int)]
    by_year: dict[str, list[int]] = {}
    for paper in papers:
        match = re.search(r"(?:19|20)\d{2}", paper["relative_path"])
        if match and isinstance(paper["pages"], int):
            by_year.setdefault(match.group(0), []).append(paper["pages"])
    year_summary = {
        year: {
            "count": len(values),
            "page_min": min(values),
            "page_median": sorted(values)[len(values) // 2],
            "page_max": max(values),
        }
        for year, values in sorted(by_year.items())
    }
    return {
        "page_count_min": min(page_values, default=None),
        "page_count_max": max(page_values, default=None),
        "year_summary": year_summary,
    }


def generate_manifest(
    *,
    pdf_dir: Path,
    recursive: bool,
    corpus_id: str,
    source_category: str,
    inspection_date: str,
    pdfinfo_tool: str | None,
) -> dict[str, Any]:
    if not pdf_dir.is_dir():
        raise ValueError("PDF corpus directory does not exist or is not a directory.")
    if not is_portable_relative(corpus_id):
        raise ValueError("corpus_id must be a portable relative identifier.")
    if not source_category.strip():
        raise ValueError("source_category must not be empty.")
    if not validate_iso_date(inspection_date):
        raise ValueError("inspection_date must use YYYY-MM-DD.")

    iterator = pdf_dir.rglob("*.pdf") if recursive else pdf_dir.glob("*.pdf")
    paths = sorted(iterator, key=lambda item: item.relative_to(pdf_dir).as_posix())
    papers: list[dict[str, Any]] = []
    for path in paths:
        relative_path = path.relative_to(pdf_dir).as_posix()
        pages, page_size, limitations, returncode = inspect_pdf(path, pdfinfo_tool)
        paper: dict[str, Any] = {
            "id": manifest_id(corpus_id, relative_path),
            "relative_path": relative_path,
            "file": path.name,
            "source_category": source_category,
            "inspection_date": inspection_date,
            "sha256": sha256_file(path),
            "pages": pages,
            "page_size_pt": page_size,
            "limitations": limitations,
            "returncode": returncode,
        }
        if pages is not None:
            paper["Pages"] = str(pages)
        if page_size is not None:
            paper["Page size"] = (
                f'{page_size["width_pt"]:g} x {page_size["height_pt"]:g} pts'
            )
        papers.append(paper)

    corpus_limitations: list[str] = []
    if not papers:
        corpus_limitations.append("No PDF files were discovered.")
    if any(paper["limitations"] for paper in papers):
        corpus_limitations.append(
            "One or more files have limited page metrics; inspect papers[].limitations."
        )
    status = "FAIL" if not papers else ("LIMITED" if corpus_limitations else "PASS")
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "manifest_type": "paper-corpus",
        "status": status,
        "corpus_id": corpus_id,
        "source_category": source_category,
        "inspection_date": inspection_date,
        "tooling": {"pdfinfo": {"available": pdfinfo_tool is not None}},
        "limitations": corpus_limitations,
        "pdf_count": len(papers),
        "papers": papers,
    }
    manifest.update(legacy_summary(papers))
    return manifest


def validate_manifest(
    manifest: dict[str, Any], pdf_dir: Path, pdfinfo_tool: str | None
) -> dict[str, Any]:
    errors: list[str] = []
    limitations: list[str] = []
    if not pdf_dir.is_dir():
        errors.append("PDF corpus directory does not exist or is not a directory.")
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1.")
    if manifest.get("manifest_type") != "paper-corpus":
        errors.append("manifest_type must be paper-corpus.")
    corpus_id = manifest.get("corpus_id")
    if not isinstance(corpus_id, str) or not is_portable_relative(corpus_id):
        errors.append("corpus_id must be a portable relative identifier.")
        corpus_id = ""
    source_category = manifest.get("source_category")
    if not isinstance(source_category, str) or not source_category.strip():
        errors.append("source_category must not be empty.")
        source_category = ""
    inspection_date = manifest.get("inspection_date")
    if not validate_iso_date(inspection_date):
        errors.append("inspection_date must use YYYY-MM-DD.")
    papers = manifest.get("papers")
    if not isinstance(papers, list) or not papers:
        errors.append("papers must be a non-empty list.")
        papers = []
    elif manifest.get("pdf_count") != len(papers):
        errors.append("pdf_count must match the number of papers.")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    checked = 0
    root = pdf_dir.resolve()

    for index, entry in enumerate(papers, start=1):
        label = f"papers[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object.")
            continue
        paper_id = entry.get("id")
        relative_path = entry.get("relative_path")
        if not isinstance(paper_id, str) or not is_portable_relative(paper_id):
            errors.append(f"{label}.id must be a portable relative identifier.")
        elif paper_id in seen_ids:
            errors.append(f"{label}.id is duplicated: {paper_id}")
        else:
            seen_ids.add(paper_id)
        if not isinstance(relative_path, str) or not is_portable_relative(relative_path):
            errors.append(f"{label}.relative_path must be portable and relative.")
            continue
        if relative_path in seen_paths:
            errors.append(f"{label}.relative_path is duplicated: {relative_path}")
        else:
            seen_paths.add(relative_path)
        if corpus_id and isinstance(paper_id, str):
            expected_id = manifest_id(corpus_id, relative_path)
            if paper_id != expected_id:
                errors.append(f"{label}.id must equal {expected_id}.")
        if not isinstance(entry.get("source_category"), str) or not entry["source_category"].strip():
            errors.append(f"{label}.source_category must not be empty.")
        elif source_category and entry["source_category"] != source_category:
            errors.append(f"{label}.source_category differs from the corpus value.")
        if not validate_iso_date(entry.get("inspection_date")):
            errors.append(f"{label}.inspection_date must use YYYY-MM-DD.")
        elif validate_iso_date(inspection_date) and entry["inspection_date"] != inspection_date:
            errors.append(f"{label}.inspection_date differs from the corpus value.")
        expected_hash = entry.get("sha256")
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            errors.append(f"{label}.sha256 must be 64 lowercase hexadecimal characters.")
        if "pages" not in entry:
            errors.append(f"{label}.pages is required.")
        if entry.get("pages") is not None and (
            not isinstance(entry["pages"], int) or entry["pages"] <= 0
        ):
            errors.append(f"{label}.pages must be a positive integer or null.")
        if "page_size_pt" not in entry:
            errors.append(f"{label}.page_size_pt is required.")
        stored_size = entry.get("page_size_pt")
        if stored_size is not None and (
            not isinstance(stored_size, dict)
            or not all(
                isinstance(stored_size.get(field), (int, float))
                and stored_size[field] > 0
                for field in ("width_pt", "height_pt")
            )
        ):
            errors.append(
                f"{label}.page_size_pt must contain positive width_pt and height_pt or be null."
            )
        if not isinstance(entry.get("limitations"), list) or not all(
            isinstance(item, str) and item.strip() for item in entry.get("limitations", [])
        ):
            errors.append(f"{label}.limitations must be a list of non-empty strings.")

        candidate = (root / Path(*PurePosixPath(relative_path).parts)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            errors.append(f"{label}.relative_path resolves outside the corpus root.")
            continue
        if not candidate.is_file():
            errors.append(f"{paper_id or label}: PDF is missing.")
            continue
        checked += 1
        if isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash):
            if sha256_file(candidate) != expected_hash:
                errors.append(f"{paper_id or label}: SHA-256 mismatch.")

        if pdfinfo_tool is None:
            continue
        current_pages, current_size, metric_limits, _ = inspect_pdf(
            candidate, pdfinfo_tool
        )
        limitations.extend(f"{paper_id or label}: {item}" for item in metric_limits)
        if isinstance(entry.get("pages"), int) and current_pages is not None:
            if entry["pages"] != current_pages:
                errors.append(f"{paper_id or label}: page count mismatch.")
        elif entry.get("pages") is None:
            limitations.append(f"{paper_id or label}: manifest page count is unavailable.")
        if isinstance(stored_size, dict) and current_size is not None:
            for field in ("width_pt", "height_pt"):
                if abs(float(stored_size[field]) - current_size[field]) > 0.01:
                    errors.append(f"{paper_id or label}: page size mismatch.")
                    break
        elif stored_size is None:
            limitations.append(f"{paper_id or label}: manifest page size is unavailable.")

    if pdfinfo_tool is None and papers:
        limitations.append(
            "pdfinfo is unavailable; hashes were checked but page metrics were not revalidated."
        )
    status = "FAIL" if errors else ("LIMITED" if limitations else "PASS")
    return {
        "schema_version": 1,
        "report_type": "paper-corpus-validation",
        "status": status,
        "checked_papers": checked,
        "errors": errors,
        "limitations": limitations,
        "tooling": {"pdfinfo": {"available": pdfinfo_tool is not None}},
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate a portable PDF corpus manifest."
    )
    parser.add_argument("--mode", choices=("generate", "validate"), default="generate")
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, help="manifest to check in validate mode")
    parser.add_argument(
        "--recursive", action="store_true", help="include PDFs in nested directories"
    )
    parser.add_argument("--corpus-id", default="local-paper-corpus")
    parser.add_argument("--source-category", default="excellent-paper")
    parser.add_argument("--inspection-date", default=date.today().isoformat())
    args = parser.parse_args()
    tool = shutil.which("pdfinfo")

    try:
        if args.mode == "generate":
            result = generate_manifest(
                pdf_dir=args.pdf_dir,
                recursive=args.recursive,
                corpus_id=args.corpus_id,
                source_category=args.source_category,
                inspection_date=args.inspection_date,
                pdfinfo_tool=tool,
            )
            write_json(args.out, result)
            print(
                json.dumps(
                    {
                        "status": result["status"],
                        "pdf_count": result["pdf_count"],
                        "page_count_min": result["page_count_min"],
                        "page_count_max": result["page_count_max"],
                        "year_summary": result["year_summary"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1 if result["status"] == "FAIL" else 0

        if args.manifest is None:
            raise ValueError("--manifest is required in validate mode.")
        try:
            payload = json.loads(args.manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"manifest could not be read as JSON: {exc.__class__.__name__}."
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError("manifest root must be a JSON object.")
        result = validate_manifest(payload, args.pdf_dir, tool)
        write_json(args.out, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[result["status"]]
    except ValueError as exc:
        failure = {
            "schema_version": 1,
            "status": "FAIL",
            "errors": [str(exc)],
            "limitations": [],
        }
        write_json(args.out, failure)
        print(json.dumps(failure, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
