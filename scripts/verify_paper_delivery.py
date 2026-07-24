#!/usr/bin/env python3
"""Verify real-source citation evidence and the two-part paper delivery package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from verify_latex_compatibility import reachable_tex_files, source_fingerprint


MIN_REFERENCES = 10
VERIFIED = {"verified", "pass", "complete"}
SCHOLAR_FOUND = {"found", "verified", "match"}
INCLUDED = {"yes", "true", "1", "included"}
AUTHORITY_MARKERS = {"publisher", "crossref", "doi.org", "openalex", "journal", "conference", "official"}
BIBLIOGRAPHY_FIELDS = {
    "citation_key", "title", "authors", "year", "venue", "doi_or_url",
    "verification_source", "verified_at", "scholar_query", "scholar_checked_at",
    "scholar_status", "claim_supported", "source_locator", "status",
}
MANIFEST_FIELDS = {"path", "category", "source", "license", "sha256", "included", "notes"}
DATA_FIELDS = {
    "dataset", "included_path", "source_url", "license", "version_or_date",
    "sha256", "retrieval_command", "status",
}
CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|parencite|textcite|autocite|footcite|supercite)"
    r"\*?(?:\s*\[[^\]]*\]){0,2}\s*\{([^{}]+)\}"
)
BIB_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.IGNORECASE)


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    if not path.is_file():
        return [], set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def value(row: dict[str, str], field: str) -> str:
    return (row.get(field) or "").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stream_sha256(handle: BinaryIO) -> str:
    digest = hashlib.sha256()
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


def normalized(text: str) -> str:
    decoded = urllib.parse.unquote_plus(text).lower()
    return " ".join(re.findall(r"[\w\u4e00-\u9fff]+", decoded, flags=re.UNICODE))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    main_tex = root / "paper" / "main.tex"
    paper_pdf = root / "paper" / "main.pdf"
    if not main_tex.is_file() or not main_tex.read_text(encoding="utf-8", errors="replace").strip():
        errors.append("paper/main.tex is missing or empty")
    if not paper_pdf.is_file():
        errors.append("paper/main.pdf is missing")
    else:
        with paper_pdf.open("rb") as handle:
            pdf_header = handle.read(5)
        if paper_pdf.stat().st_size < 100 or pdf_header != b"%PDF-":
            errors.append("paper/main.pdf is not a non-empty PDF build artifact")

    compatibility_path = root / "reports" / "latex_compatibility.json"
    compatibility: dict[str, object] = {}
    if not compatibility_path.is_file():
        errors.append("reports/latex_compatibility.json is missing; run verify_latex_compatibility.py")
    else:
        try:
            compatibility = json.loads(compatibility_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            errors.append("reports/latex_compatibility.json is not valid readable JSON")
        else:
            if compatibility.get("status") != "PASS" or compatibility.get("compile_backed") is not True:
                errors.append("LaTeX compatibility is not backed by successful Overleaf and VS Code builds")
            if (root / "paper").is_dir():
                current_source_hash = source_fingerprint(root / "paper")
                if compatibility.get("source_sha256") != current_source_hash:
                    errors.append("LaTeX compatibility report is stale for the current paper source")

    tex_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in reachable_tex_files(root / "paper")
    ) if (root / "paper").is_dir() else ""
    cited_keys = {
        key.strip()
        for group in CITE_RE.findall(tex_text)
        for key in group.split(",")
        if key.strip()
    }
    bib_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted((root / "paper").rglob("*.bib"))
    ) if (root / "paper").is_dir() else ""
    bib_key_list = BIB_RE.findall(bib_text)
    bib_keys = set(bib_key_list)
    bib_key_counts = {key: bib_key_list.count(key) for key in bib_keys}
    for key in sorted(key for key, count in bib_key_counts.items() if count > 1):
        errors.append(f"BibTeX contains duplicate citation key: {key}")

    bibliography, bibliography_fields = read_csv(root / "reports" / "bibliography.csv")
    if missing := BIBLIOGRAPHY_FIELDS - bibliography_fields:
        errors.append("reports/bibliography.csv missing columns: " + ", ".join(sorted(missing)))
    ledger: dict[str, dict[str, str]] = {}
    title_rows: dict[str, int] = {}
    identifier_rows: dict[str, int] = {}
    for index, row in enumerate(bibliography, 2):
        if any(not value(row, field) for field in BIBLIOGRAPHY_FIELDS):
            errors.append(f"bibliography.csv:{index} has empty required fields")
        key = value(row, "citation_key")
        if key in ledger:
            errors.append(f"bibliography.csv:{index} duplicates citation key {key}")
        elif key:
            ledger[key] = row
        authority = value(row, "verification_source").lower()
        if authority and not any(marker in authority for marker in AUTHORITY_MARKERS):
            errors.append(f"bibliography.csv:{index} lacks authoritative metadata verification")
        doi_or_url = value(row, "doi_or_url").lower()
        if doi_or_url and not (doi_or_url.startswith("10.") or doi_or_url.startswith("http://") or doi_or_url.startswith("https://")):
            errors.append(f"bibliography.csv:{index} doi_or_url is not a DOI or URL")
        if doi_or_url in identifier_rows:
            errors.append(
                f"bibliography.csv:{index} duplicates DOI/URL from row {identifier_rows[doi_or_url]}"
            )
        elif doi_or_url:
            identifier_rows[doi_or_url] = index
        if value(row, "verified_at") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[T ][^,]+)?", value(row, "verified_at")):
            errors.append(f"bibliography.csv:{index} verified_at must start with YYYY-MM-DD")
        title = normalized(value(row, "title"))
        if title in title_rows:
            errors.append(f"bibliography.csv:{index} duplicates title from row {title_rows[title]}")
        elif title:
            title_rows[title] = index
        scholar_query = normalized(value(row, "scholar_query"))
        if value(row, "scholar_query") and "scholar.google" not in value(row, "scholar_query").lower():
            errors.append(f"bibliography.csv:{index} scholar_query is not a Google Scholar query URL")
        if title and title not in scholar_query:
            errors.append(f"bibliography.csv:{index} scholar_query does not contain the exact title")
        if value(row, "scholar_checked_at") and not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}(?:[T ][^,]+)?", value(row, "scholar_checked_at")
        ):
            errors.append(f"bibliography.csv:{index} scholar_checked_at must start with YYYY-MM-DD")
        if value(row, "scholar_status").lower() not in SCHOLAR_FOUND:
            errors.append(f"bibliography.csv:{index} was not confirmed in Google Scholar")
        if value(row, "status").lower() not in VERIFIED:
            errors.append(f"bibliography.csv:{index} is not verified")

    verified_cited = cited_keys & bib_keys & set(ledger)
    unique_verified_titles = {
        normalized(value(ledger[key], "title"))
        for key in verified_cited
        if value(ledger[key], "status").lower() in VERIFIED
    }
    if len(unique_verified_titles) < MIN_REFERENCES:
        errors.append(
            f"paper has {len(unique_verified_titles)} uniquely cited and verified scholarly references; "
            f"at least {MIN_REFERENCES} are required"
        )
    for key in sorted(cited_keys - bib_keys):
        errors.append(f"LaTeX citation is missing from BibTeX: {key}")
    for key in sorted(cited_keys - set(ledger)):
        errors.append(f"LaTeX citation is missing from bibliography.csv: {key}")
    for key in sorted(set(ledger) - cited_keys):
        errors.append(f"bibliography.csv entry is not cited in LaTeX: {key}")
    for key in sorted(set(ledger) - bib_keys):
        errors.append(f"bibliography.csv entry is missing from BibTeX: {key}")

    support_readme = root / "support" / "README.md"
    if not support_readme.is_file() or not support_readme.read_text(encoding="utf-8", errors="replace").strip():
        errors.append("support/README.md is missing or empty")
    reproduction_commands = root / "support" / "reproduction_commands.txt"
    if (
        not reproduction_commands.is_file()
        or not reproduction_commands.read_text(encoding="utf-8", errors="replace").strip()
    ):
        errors.append("support/reproduction_commands.txt is missing or empty")
    else:
        command_lines = [
            line.strip()
            for line in reproduction_commands.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not command_lines:
            errors.append("support/reproduction_commands.txt has no executable commands")
    materials, material_fields = read_csv(root / "support" / "materials_manifest.csv")
    if missing := MANIFEST_FIELDS - material_fields:
        errors.append("support/materials_manifest.csv missing columns: " + ", ".join(sorted(missing)))
    included_paths: set[str] = set()
    categories: set[str] = set()
    for index, row in enumerate(materials, 2):
        if any(not value(row, field) for field in MANIFEST_FIELDS):
            errors.append(f"materials_manifest.csv:{index} has empty required fields")
        if value(row, "included").lower() not in INCLUDED:
            continue
        relative = value(row, "path").replace("\\", "/")
        path = project_file(root, relative)
        if path is None or not path.is_file():
            errors.append(f"materials_manifest.csv:{index} file is missing or outside the project: {relative}")
            continue
        included_paths.add(relative)
        categories.add(value(row, "category").lower())
        expected_hash = value(row, "sha256").lower()
        if expected_hash != sha256(path):
            errors.append(f"materials_manifest.csv:{index} SHA-256 mismatch: {relative}")
    if not categories & {"code", "script", "notebook"}:
        errors.append("support manifest has no included code, script, or notebook")
    if not categories & {"data", "processed-data", "generated-data", "data-retrieval"}:
        errors.append("support manifest has no included data or reproducible data-retrieval evidence")
    if not categories & {"environment", "dependency-lock", "runtime"}:
        errors.append("support manifest has no included environment or dependency evidence")
    if not categories & {"result", "results", "output"}:
        errors.append("support manifest has no included result or output evidence")

    data_rows, data_fields = read_csv(root / "support" / "data_inventory.csv")
    if missing := DATA_FIELDS - data_fields:
        errors.append("support/data_inventory.csv missing columns: " + ", ".join(sorted(missing)))
    if not data_rows:
        errors.append("support/data_inventory.csv has no dataset rows")
    for index, row in enumerate(data_rows, 2):
        if any(not value(row, field) for field in DATA_FIELDS):
            errors.append(f"data_inventory.csv:{index} has empty required fields")
        status = value(row, "status").lower()
        if status not in {"included", "retrievable", "not_applicable"}:
            errors.append(f"data_inventory.csv:{index} has invalid status")
        if status == "included":
            relative = value(row, "included_path").replace("\\", "/")
            path = project_file(root, relative)
            if path is None or not path.is_file():
                errors.append(f"data_inventory.csv:{index} included data is missing: {relative}")
            elif value(row, "sha256").lower() != sha256(path):
                errors.append(f"data_inventory.csv:{index} SHA-256 mismatch: {relative}")
        elif status == "retrievable" and value(row, "source_url").lower() in {"n/a", "na", "none"}:
            errors.append(f"data_inventory.csv:{index} retrievable data lacks a source URL")

    support_zip = root / "support.zip"
    archive_names: set[str] = set()
    archive_hashes: dict[str, str] = {}
    if not support_zip.is_file():
        errors.append("support.zip is missing")
    else:
        try:
            with zipfile.ZipFile(support_zip) as archive:
                archive_entries: list[str] = []
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    name = info.filename.replace("\\", "/")
                    archive_entries.append(name)
                    member = PurePosixPath(name)
                    if member.is_absolute() or ".." in member.parts or (member.parts and ":" in member.parts[0]):
                        errors.append(f"support.zip has unsafe path: {name}")
                    if name in archive_hashes:
                        errors.append(f"support.zip has duplicate path: {name}")
                        continue
                    with archive.open(info) as handle:
                        archive_hashes[name] = stream_sha256(handle)
                archive_names = set(archive_entries)
        except (zipfile.BadZipFile, KeyError, OSError, RuntimeError):
            errors.append("support.zip is not a valid readable ZIP archive")
    required_archive_files = {
        "support/README.md",
        "support/reproduction_commands.txt",
        "support/materials_manifest.csv",
        "support/data_inventory.csv",
    } | included_paths
    for relative in sorted(required_archive_files - archive_names):
        errors.append(f"support.zip is missing: {relative}")
    for relative in sorted(required_archive_files & archive_names):
        path = project_file(root, relative)
        if path is not None and path.is_file() and archive_hashes.get(relative) != sha256(path):
            errors.append(f"support.zip contains a stale or modified copy: {relative}")

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "structural delivery and recorded metadata verification; human source reading remains required "
            "and fabricated content cannot be certified by this script"
        ),
        "counts": {
            "latex_citations": len(cited_keys),
            "bibtex_entries": len(bib_keys),
            "verified_cited_references": len(unique_verified_titles),
            "support_manifest_rows": len(materials),
            "support_archive_files": len(archive_names),
            "data_inventory_rows": len(data_rows),
            "latex_compatibility_builds": len(compatibility.get("builds", []))
            if isinstance(compatibility.get("builds"), list)
            else 0,
        },
        "errors": errors,
        "warnings": warnings,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
