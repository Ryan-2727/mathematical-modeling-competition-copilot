#!/usr/bin/env python3
"""Load bundled executable contest profiles from one authoritative source."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "assets" / "contest-profiles"


def _validate_cumcm_2026_timing(payload: dict[str, Any]) -> None:
    fields = (
        "registration_deadline",
        "competition_start",
        "competition_end",
        "hash_deadline",
        "upload_open",
        "upload_deadline",
    )
    parsed: dict[str, datetime] = {}
    for field in fields:
        try:
            value = datetime.fromisoformat(str(payload[field]).replace("Z", "+00:00"))
        except (KeyError, ValueError) as exc:
            raise RuntimeError(f"invalid CUMCM 2026 timing field: {field}") from exc
        if value.tzinfo is None:
            raise RuntimeError(f"CUMCM 2026 timing field lacks timezone: {field}")
        parsed[field] = value
    if not (
        parsed["registration_deadline"] < parsed["competition_start"]
        < parsed["competition_end"]
        == parsed["hash_deadline"]
        < parsed["upload_open"]
        < parsed["upload_deadline"]
    ):
        raise RuntimeError("CUMCM 2026 timing fields are inconsistent")


@lru_cache(maxsize=None)
def _load_contest_profile(profile_id: str) -> dict[str, Any]:
    path = PROFILE_DIR / f"{profile_id}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot load bundled contest profile {profile_id}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("profile_id") != profile_id:
        raise RuntimeError(f"bundled contest profile identity mismatch: {profile_id}")
    if payload.get("schema_version") != 1:
        raise RuntimeError(f"unsupported bundled contest profile schema: {profile_id}")
    if profile_id == "cumcm-2026":
        _validate_cumcm_2026_timing(payload)
    return payload


def load_contest_profile(profile_id: str) -> dict[str, Any]:
    return deepcopy(_load_contest_profile(profile_id))


def submission_profile(profile_id: str) -> dict[str, Any]:
    payload = load_contest_profile(profile_id)
    snapshot_fields = (
        "profile_version",
        "verified_at",
        "valid_through",
        "competition_start",
        "competition_end",
        "registration_deadline",
        "hash_deadline",
        "upload_open",
        "upload_deadline",
        "timezone",
        "submission_channel",
        "freshness_checkpoints",
    )
    profile_fields = (
        "paper_suffixes",
        "support_suffixes",
        "max_paper_mb",
        "max_support_mb",
        "max_main_text_pages",
        "toc_forbidden",
    )
    result = {key: payload[key] for key in profile_fields}
    result["paper_suffixes"] = set(result["paper_suffixes"])
    result["support_suffixes"] = set(result["support_suffixes"])
    result["snapshot"] = {key: payload[key] for key in snapshot_fields}
    variants = payload.get("source_variants") or {}
    result["snapshot"]["source_urls"] = sorted(
        {
            url
            for role in variants.values()
            if isinstance(role, dict)
            for url in role.values()
        }
        or set(payload["source_urls"].values())
    )
    return result
