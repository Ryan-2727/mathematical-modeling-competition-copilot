#!/usr/bin/env python3
"""Verify cited bibliography rows against saved authoritative metadata."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from verify_latex_compatibility import reachable_tex_files


REQUIRED_FIELDS = {
    "citation_key",
    "title",
    "authors",
    "year",
    "venue",
    "doi_or_url",
    "verification_source",
    "verified_at",
    "scholar_query",
    "scholar_checked_at",
    "scholar_status",
    "metadata_snapshot",
    "metadata_sha256",
    "retraction_status",
    "retraction_checked_at",
    "claim_supported",
    "source_locator",
    "supporting_passage",
    "supporting_passage_sha256",
    "status",
}
CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|parencite|textcite|autocite|footcite|supercite)"
    r"\*?(?:\s*\[[^\]]*\]){0,2}\s*\{([^{}]+)\}"
)
COMPLETE = {"verified", "pass", "complete"}
NOT_RETRACTED = {"not_retracted", "checked_no_notice", "no_retraction_found"}
SCHOLAR_FOUND = {"found", "verified", "match"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_file(root: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def normalized(text: str) -> str:
    return " ".join(re.findall(r"[\w\u4e00-\u9fff]+", text.casefold()))


def clean_doi(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    return value


def first_text(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    return str(value or "")


def metadata_fields(payload: Any) -> tuple[str, str, str, str, str]:
    if not isinstance(payload, dict):
        return "", "", "", "", ""
    record = payload.get("message") if isinstance(payload.get("message"), dict) else payload
    title = first_text(record.get("title"))
    doi = str(record.get("DOI") or record.get("doi") or "")
    author_names: list[str] = []
    authors = record.get("author")
    if isinstance(authors, list):
        for author in authors:
            if isinstance(author, dict):
                name = " ".join(
                    part
                    for part in (
                        str(author.get("given") or "").strip(),
                        str(author.get("family") or "").strip(),
                    )
                    if part
                )
                if name:
                    author_names.append(name)
    authorships = record.get("authorships")
    if isinstance(authorships, list):
        for authorship in authorships:
            if not isinstance(authorship, dict):
                continue
            author = authorship.get("author")
            if isinstance(author, dict) and author.get("display_name"):
                author_names.append(str(author["display_name"]))
    venue = first_text(record.get("container-title"))
    if not venue:
        primary = record.get("primary_location")
        if isinstance(primary, dict):
            source = primary.get("source")
            if isinstance(source, dict):
                venue = str(source.get("display_name") or "")
    if not venue:
        host = record.get("host_venue")
        if isinstance(host, dict):
            venue = str(host.get("display_name") or "")
    year = ""
    for field in ("published-print", "published-online", "issued"):
        date_parts = record.get(field)
        if isinstance(date_parts, dict):
            parts = date_parts.get("date-parts")
            if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
                year = str(parts[0][0])
                break
    if not year:
        publication_year = record.get("publication_year")
        year = str(publication_year or "")
    return title, year, doi, "; ".join(author_names), venue


def author_matches(recorded: str, authoritative: str) -> bool:
    recorded_tokens = set(normalized(recorded).split())
    authoritative_tokens = set(normalized(authoritative).split())
    return bool(recorded_tokens and authoritative_tokens) and (
        recorded_tokens <= authoritative_tokens
        or authoritative_tokens <= recorded_tokens
    )


def authoritative_source(value: str, doi: str, metadata: Any) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        return False
    path = clean_doi(parsed.path.lstrip("/").removeprefix("works/"))
    if host in {"doi.org", "api.crossref.org"}:
        return bool(doi.startswith("10.") and path == doi)
    if host == "api.openalex.org" and isinstance(metadata, dict):
        record = (
            metadata.get("message")
            if isinstance(metadata.get("message"), dict)
            else metadata
        )
        openalex_id = str(record.get("id") or "").rstrip("/").split("/")[-1].lower()
        return bool(openalex_id and parsed.path.rstrip("/").lower().endswith(openalex_id))
    return False


def valid_scholar_query(value: str, title_key: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or host != "scholar.google.com"
        or parsed.path.rstrip("/") != "/scholar"
    ):
        return False
    queries = parse_qs(parsed.query)
    return any(title_key in normalized(item) for item in queries.get("q", []))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--minimum-references", type=int, default=10)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_dir.resolve()
    ledger_path = root / "reports" / "bibliography.csv"
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, str]] = []
    fields: set[str] = set()
    if not ledger_path.is_file():
        errors.append("reports/bibliography.csv is missing")
    else:
        try:
            with ledger_path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fields = set(reader.fieldnames or [])
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            errors.append(f"cannot read bibliography.csv: {exc}")
    if missing := REQUIRED_FIELDS - fields:
        errors.append("bibliography.csv missing strict metadata columns: " + ", ".join(sorted(missing)))
    tex_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in reachable_tex_files(root / "paper")
    ) if (root / "paper").is_dir() else ""
    cited = {
        key.strip()
        for group in CITE_RE.findall(tex_text)
        for key in group.split(",")
        if key.strip()
    }
    verified: set[str] = set()
    reports: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    seen_dois: set[str] = set()
    for line, row in enumerate(rows, 2):
        local: list[str] = []
        for field in REQUIRED_FIELDS:
            if not str(row.get(field) or "").strip():
                local.append(f"{field} is empty")
        key = str(row.get("citation_key") or "").strip()
        if key not in cited:
            local.append("entry is not cited in reachable LaTeX")
        title = str(row.get("title") or "").strip()
        title_key = normalized(title)
        if title_key in seen_titles:
            local.append("duplicate normalized title")
        seen_titles.add(title_key)
        doi = clean_doi(str(row.get("doi_or_url") or ""))
        if doi.startswith("10."):
            if doi in seen_dois:
                local.append("duplicate DOI")
            seen_dois.add(doi)
        snapshot_relative = str(row.get("metadata_snapshot") or "").strip()
        snapshot = safe_file(root, snapshot_relative)
        metadata_title = metadata_year = metadata_doi = ""
        metadata_authors = metadata_venue = ""
        metadata: Any = {}
        if snapshot is None or not snapshot.is_file():
            local.append("authoritative metadata snapshot is missing or unsafe")
        elif sha256_file(snapshot) != str(row.get("metadata_sha256") or "").strip().lower():
            local.append("metadata snapshot SHA-256 mismatch")
        else:
            try:
                metadata = json.loads(snapshot.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                local.append(f"metadata snapshot is unreadable: {exc}")
            else:
                (
                    metadata_title,
                    metadata_year,
                    metadata_doi,
                    metadata_authors,
                    metadata_venue,
                ) = metadata_fields(metadata)
                if normalized(metadata_title) != title_key:
                    local.append("title does not exactly match authoritative metadata")
                if str(row.get("year") or "").strip() != metadata_year:
                    local.append("year does not match authoritative metadata")
                if doi.startswith("10.") and clean_doi(metadata_doi) != doi:
                    local.append("DOI does not match authoritative metadata")
                if not author_matches(
                    str(row.get("authors") or ""), metadata_authors
                ):
                    local.append("authors do not match authoritative metadata")
                recorded_venue = normalized(str(row.get("venue") or ""))
                authoritative_venue = normalized(metadata_venue)
                if (
                    not recorded_venue
                    or not authoritative_venue
                    or (
                        recorded_venue not in authoritative_venue
                        and authoritative_venue not in recorded_venue
                    )
                ):
                    local.append("venue does not match authoritative metadata")
        authority = str(row.get("verification_source") or "").strip()
        if not authoritative_source(authority, doi, metadata):
            local.append(
                "verification_source must be a record-specific HTTPS Crossref, "
                "DOI, or OpenAlex URL matching the saved metadata"
            )
        for field in ("verified_at", "scholar_checked_at"):
            checked = str(row.get(field) or "").strip()
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[T ][^,]+)?", checked):
                local.append(f"{field} must start with YYYY-MM-DD")
        scholar_query = str(row.get("scholar_query") or "").strip()
        if not valid_scholar_query(scholar_query, title_key):
            local.append(
                "scholar_query must be an HTTPS Google Scholar /scholar URL "
                "whose q parameter contains the exact title"
            )
        if str(row.get("scholar_status") or "").strip().lower() not in SCHOLAR_FOUND:
            local.append("reference was not confirmed in Google Scholar")
        retraction = str(row.get("retraction_status") or "").strip().lower()
        if retraction not in NOT_RETRACTED:
            local.append("retraction status is not an accepted checked-no-notice value")
        checked_at = str(row.get("retraction_checked_at") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[T ][^,]+)?", checked_at):
            local.append("retraction_checked_at must start with YYYY-MM-DD")
        passage_relative = str(row.get("supporting_passage") or "").strip()
        passage = safe_file(root, passage_relative)
        if passage is None or not passage.is_file() or passage.stat().st_size == 0:
            local.append("supporting passage evidence is missing or unsafe")
        elif sha256_file(passage) != str(row.get("supporting_passage_sha256") or "").strip().lower():
            local.append("supporting passage SHA-256 mismatch")
        if not str(row.get("claim_supported") or "").strip():
            local.append("claim_supported is empty")
        if not str(row.get("source_locator") or "").strip():
            local.append("source_locator is empty")
        if str(row.get("status") or "").strip().lower() not in COMPLETE:
            local.append("entry status is not verified")
        if not local and key:
            verified.add(key)
        reports.append(
            {
                "line": line,
                "citation_key": key,
                "status": "PASS" if not local else "FAIL",
                "metadata_title": metadata_title,
                "metadata_authors": metadata_authors,
                "metadata_venue": metadata_venue,
                "errors": local,
            }
        )
        errors.extend(f"bibliography.csv:{line} {item}" for item in local)
    if len(verified) < args.minimum_references:
        errors.append(
            f"only {len(verified)} cited references have strict metadata and passage "
            f"evidence; minimum is {args.minimum_references}"
        )
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "saved metadata, retraction-check record, body citation, and supporting-"
            "passage integrity; source interpretation remains a human responsibility"
        ),
        "counts": {
            "ledger_rows": len(rows),
            "cited_keys": len(cited),
            "strictly_verified": len(verified),
        },
        "bibliography_sha256": sha256_file(ledger_path)
        if ledger_path.is_file()
        else "",
        "references": reports,
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
