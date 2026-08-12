#!/usr/bin/env python3
"""Load bundled executable contest profiles from one authoritative source."""
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "assets" / "contest-profiles"


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
