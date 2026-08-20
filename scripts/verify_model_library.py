#!/usr/bin/env python3
"""Validate the bundled targeted CUMCM B/C model-card library."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIBRARY = ROOT / "assets" / "model-library" / "cumcm-bc-model-cards.json"
CARD_FIELDS = {
    "id",
    "title",
    "contest_fit",
    "signals",
    "baseline",
    "candidate",
    "promotion_threshold",
    "diagnostics",
    "falsification_test",
    "fallback",
    "deliverables",
    "implementation_notes",
    "primary_sources",
}
SOURCE_FIELDS = {"title", "authors", "year", "doi_url"}
DOI_URL = re.compile(r"https://doi\.org/10\.[^\s]+", re.IGNORECASE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nonempty_strings(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def validate(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        payload = {}
        errors.append(f"cannot read model library: {exc}")
    if not isinstance(payload, dict):
        payload = {}
        errors.append("model library must be a JSON object")
    if payload.get("schema_version") != 1:
        errors.append("model library schema_version must be 1")
    for field in ("library_id", "library_version", "verified_at", "scope"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            errors.append(f"model library field {field} is missing")
    required = payload.get("required_archetypes")
    if not nonempty_strings(required):
        errors.append("required_archetypes must be a non-empty string list")
        required = []
    elif len(required) != len(set(required)):
        errors.append("required_archetypes contains duplicates")
    cards = payload.get("cards")
    if not isinstance(cards, list) or not cards:
        errors.append("cards must be a non-empty list")
        cards = []
    card_ids: set[str] = set()
    source_dois: set[str] = set()
    contest_coverage: set[str] = set()
    for index, card in enumerate(cards, 1):
        prefix = f"cards[{index}]"
        if not isinstance(card, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = CARD_FIELDS - set(card)
        if missing:
            errors.append(f"{prefix} missing fields: " + ", ".join(sorted(missing)))
        card_id = str(card.get("id") or "").strip()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", card_id):
            errors.append(f"{prefix} has invalid id")
        elif card_id in card_ids:
            errors.append(f"{prefix} duplicates card id {card_id}")
        card_ids.add(card_id)
        fit = card.get("contest_fit")
        if not nonempty_strings(fit) or not set(fit) <= {"B", "C"}:
            errors.append(f"{prefix}.contest_fit must contain only B and/or C")
        else:
            contest_coverage.update(fit)
        for field in (
            "title",
            "baseline",
            "candidate",
            "promotion_threshold",
            "falsification_test",
            "fallback",
        ):
            if not isinstance(card.get(field), str) or not card[field].strip():
                errors.append(f"{prefix}.{field} must be non-empty text")
        if str(card.get("baseline") or "").strip().casefold() == str(
            card.get("candidate") or ""
        ).strip().casefold():
            errors.append(f"{prefix} baseline and candidate must be distinct")
        for field in ("signals", "diagnostics", "deliverables", "implementation_notes"):
            if not nonempty_strings(card.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string list")
        sources = card.get("primary_sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{prefix}.primary_sources must not be empty")
            sources = []
        for source_index, source in enumerate(sources, 1):
            source_prefix = f"{prefix}.primary_sources[{source_index}]"
            if not isinstance(source, dict):
                errors.append(f"{source_prefix} must be an object")
                continue
            if SOURCE_FIELDS - set(source):
                errors.append(f"{source_prefix} lacks complete citation metadata")
            for field in ("title", "authors", "doi_url"):
                if not isinstance(source.get(field), str) or not source[field].strip():
                    errors.append(f"{source_prefix}.{field} must be non-empty")
            year = source.get("year")
            if not isinstance(year, int) or year < 1900 or year > 2100:
                errors.append(f"{source_prefix}.year is invalid")
            doi_url = str(source.get("doi_url") or "").strip()
            if not DOI_URL.fullmatch(doi_url):
                errors.append(f"{source_prefix}.doi_url must be a record-specific DOI URL")
            normalized_doi = doi_url.casefold()
            if normalized_doi in source_dois:
                errors.append(f"{source_prefix} duplicates DOI {doi_url}")
            source_dois.add(normalized_doi)
    missing_cards = sorted(set(required) - card_ids)
    extra_cards = sorted(card_ids - set(required))
    if missing_cards:
        errors.append("required model cards are missing: " + ", ".join(missing_cards))
    if extra_cards:
        warnings.append("unlisted additional model cards: " + ", ".join(extra_cards))
    if contest_coverage != {"B", "C"}:
        errors.append("model library must cover both B and C routing")
    return {
        "status": "FAIL" if errors else ("LIMITED" if warnings else "PASS"),
        "scope": (
            "static card completeness, targeted B/C coverage, promotion/fallback "
            "fields, and DOI-shaped primary-source locators; not proof that a card "
            "fits a future contest problem"
        ),
        "library": str(path),
        "library_sha256": sha256(path) if path.is_file() else "",
        "counts": {
            "required_archetypes": len(required),
            "cards": len(cards),
            "primary_sources": len(source_dois),
        },
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = validate(args.library.resolve())
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(report["status"])
    for error in report["errors"]:
        print(f"ERROR {error}")
    return {"PASS": 0, "FAIL": 1, "LIMITED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
