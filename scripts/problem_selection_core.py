#!/usr/bin/env python3
"""Shared deterministic contracts for local CUMCM A/B/C recommendation."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_PROFILE = SKILL_ROOT / "assets" / "problem-selection" / "ai-capability-profile.json"
PROBLEMS = ("A", "B", "C")
CRITERIA = (
    "closure_result",
    "result_verifiability",
    "ai_capability_fit",
    "data_semantics",
    "compute_fallback",
    "paper_figure",
    "innovation",
)
BASE_WEIGHTS = {
    "closure_result": 0.25,
    "result_verifiability": 0.20,
    "ai_capability_fit": 0.20,
    "data_semantics": 0.10,
    "compute_fallback": 0.10,
    "paper_figure": 0.10,
    "innovation": 0.05,
}
SCENARIOS = {
    "base": BASE_WEIGHTS,
    "closure_first": {
        "closure_result": 0.40, "result_verifiability": 0.18,
        "ai_capability_fit": 0.15, "data_semantics": 0.08,
        "compute_fallback": 0.08, "paper_figure": 0.07, "innovation": 0.04,
    },
    "verification_first": {
        "closure_result": 0.20, "result_verifiability": 0.35,
        "ai_capability_fit": 0.18, "data_semantics": 0.08,
        "compute_fallback": 0.08, "paper_figure": 0.07, "innovation": 0.04,
    },
    "ai_fit_first": {
        "closure_result": 0.20, "result_verifiability": 0.18,
        "ai_capability_fit": 0.35, "data_semantics": 0.08,
        "compute_fallback": 0.08, "paper_figure": 0.07, "innovation": 0.04,
    },
    "paper_presentation": {
        "closure_result": 0.20, "result_verifiability": 0.15,
        "ai_capability_fit": 0.15, "data_semantics": 0.10,
        "compute_fallback": 0.10, "paper_figure": 0.25, "innovation": 0.05,
    },
}
OUTCOMES = ("national_first", "national_second", "provincial_award", "no_award")
PROJECT_INPUTS = (
    "reports/problem_screening.csv",
    "reports/problem_audition.csv",
    "reports/problem_selection_evidence.csv",
    "reports/problem_audition_weights.json",
    "reports/ai_capability_snapshot.json",
    "reports/problem_selection_calibration.csv",
    "reports/public_award_prior.json",
)
SCREENING_FIELDS = (
    "problem_id", "screening_minutes", "micro_baseline_minutes",
    "preliminary_score", "deep_trial_selected", "elimination_reason",
    "deep_trial_budget_minutes", "deep_trial_elapsed_minutes",
    "task_families", "required_model_families", "attachment_state",
    "semantic_risk", "expected_deliverables", "evidence_locator",
    "evidence_sha256", "early_failure_type", "timing_exception", "status",
)
EVIDENCE_FIELDS = (
    "problem_id", "criterion", "rating", "evidence_locator", "evidence_sha256",
    "observation_type", "observation", "status",
)
CALIBRATION_FIELDS = (
    "case_id", "year", "task_family_tags", "ai_profile_version",
    *tuple(f"{item}_rating" for item in CRITERIA),
    "composite_score", "selected_problem_type", "award_label",
    "evidence_sha256", "status",
)
HEX64 = re.compile(r"[0-9a-fA-F]{64}\Z")
SLUG = re.compile(r"[A-Za-z0-9_.-]+\Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_project_file(root: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def load_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def split_tags(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(";") if item.strip()}


def parse_utc(raw: object) -> datetime | None:
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def skill_fingerprint() -> str:
    relative_paths = (
        "SKILL.md",
        "assets/problem-selection/ai-capability-profile.json",
        "assets/model-library/cumcm-bc-model-cards.json",
        "scripts/probe_runtime_capabilities.py",
        "scripts/run_model_kernel_regression.py",
        "scripts/problem_selection_core.py",
        "scripts/create_ai_capability_snapshot.py",
        "scripts/recommend_problem_selection.py",
        "scripts/record_problem_selection_confirmation.py",
        "scripts/verify_problem_audition.py",
    )
    digest = hashlib.sha256()
    for relative in relative_paths:
        path = SKILL_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def recommendation_input_hashes(root: Path) -> dict[str, str]:
    hashes = {
        relative: sha256_file(root / relative) if (root / relative).is_file() else ""
        for relative in PROJECT_INPUTS
    }
    evidence_paths: set[str] = set()
    csv_locators = {
        "reports/problem_screening.csv": ("evidence_locator",),
        "reports/problem_selection_evidence.csv": ("evidence_locator",),
        "reports/problem_audition.csv": (
            "attachment_evidence", "baseline_result", "paper_figure",
            "subproblem_closure_evidence", "fallback_evidence",
        ),
    }
    for relative, fields in csv_locators.items():
        path = root / relative
        if not path.is_file():
            continue
        try:
            _, rows = load_csv_rows(path)
        except (OSError, UnicodeError, csv.Error):
            continue
        for row in rows:
            for field in fields:
                raw = str(row.get(field) or "").strip()
                if raw.lower() not in {"", "none", "not_applicable"} and safe_project_file(root, raw) is not None:
                    evidence_paths.add(Path(raw).as_posix())
    for relative, field in (
        ("reports/ai_capability_snapshot.json", "kernel_regression"),
        ("reports/public_award_prior.json", "source_snapshot"),
    ):
        try:
            payload = load_json_object(root / relative)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            continue
        raw = payload.get(field)
        if field == "kernel_regression" and isinstance(raw, dict):
            raw = raw.get("path")
        locator = str(raw or "").strip()
        if safe_project_file(root, locator) is not None:
            evidence_paths.add(Path(locator).as_posix())
    for relative in sorted(evidence_paths):
        path = safe_project_file(root, relative)
        hashes[f"project-evidence://{relative}"] = sha256_file(path) if path and path.is_file() else ""
    hashes["skill://assets/problem-selection/ai-capability-profile.json"] = (
        sha256_file(CAPABILITY_PROFILE) if CAPABILITY_PROFILE.is_file() else ""
    )
    hashes["skill://skill-fingerprint"] = skill_fingerprint()
    return hashes


def stale_input_errors(root: Path, recorded: object) -> list[str]:
    if not isinstance(recorded, dict):
        return ["recommendation input_hashes must be an object"]
    current = recommendation_input_hashes(root)
    if set(recorded) != set(current):
        return ["recommendation input set no longer matches the current contract"]
    return [
        f"recommendation input is stale: {relative}"
        for relative, digest in current.items()
        if str(recorded.get(relative) or "").lower() != digest.lower()
    ]


def validate_locator_hash(
    root: Path, locator: str, expected: str, label: str, errors: list[str]
) -> Path | None:
    path = safe_project_file(root, locator)
    if path is None or not path.is_file():
        errors.append(f"{label} evidence locator is missing or unsafe")
        return None
    if not HEX64.fullmatch(expected or ""):
        errors.append(f"{label} evidence_sha256 must be 64 hexadecimal characters")
        return None
    if sha256_file(path).lower() != expected.lower():
        errors.append(f"{label} evidence hash does not match {locator}")
        return None
    return path


def load_capability_profile(errors: list[str]) -> tuple[dict[str, Any], dict[str, float]]:
    try:
        payload = load_json_object(CAPABILITY_PROFILE)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"cannot read bundled AI capability profile: {exc}")
        return {}, {}
    if payload.get("schema_version") != 1 or not str(payload.get("profile_version") or ""):
        errors.append("AI capability profile schema/version is invalid")
    capabilities: dict[str, float] = {}
    raw = payload.get("capabilities")
    if not isinstance(raw, list):
        errors.append("AI capability profile capabilities must be a list")
        return payload, capabilities
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            errors.append(f"AI capability profile entry {index} must be an object")
            continue
        identifier = str(item.get("id") or "").strip()
        try:
            rating = float(item.get("rating"))
        except (TypeError, ValueError):
            rating = -1
        if not identifier or identifier in capabilities or not 0 <= rating <= 4:
            errors.append(f"AI capability profile entry {index} has invalid id/rating")
            continue
        if not all(str(item.get(field) or "").strip() for field in ("limitations", "evidence_type", "review_date")):
            errors.append(f"AI capability profile entry {identifier} lacks review evidence")
        capabilities[identifier] = rating
    return payload, capabilities


def combine_ai_fit(prior_rating: float, live_rating: float) -> float:
    return round(0.30 * prior_rating + 0.70 * live_rating, 6)


def weighted_score(ratings: dict[str, float | None], weights: dict[str, float]) -> float:
    return round(25.0 * sum(weights[key] * (ratings.get(key) or 0.0) for key in CRITERIA), 6)


def scenario_analysis(
    candidate_ratings: dict[str, dict[str, float | None]]
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, Any]]]:
    scores = {
        name: {problem: weighted_score(ratings, weights) for problem, ratings in candidate_ratings.items()}
        for name, weights in SCENARIOS.items()
    }
    summary: dict[str, dict[str, Any]] = {}
    for problem in candidate_ratings:
        wins = 0
        ranks: list[int] = []
        margins: list[float] = []
        for scenario_scores in scores.values():
            value = scenario_scores[problem]
            rank = 1 + sum(other > value + 1e-9 for other in scenario_scores.values())
            ranks.append(rank)
            best = max(scenario_scores.values())
            if abs(value - best) <= 1e-9:
                wins += 1
            alternatives = [score for key, score in scenario_scores.items() if key != problem]
            margins.append(value - max(alternatives))
        summary[problem] = {
            "scenario_win_rate": wins / len(scores),
            "worst_rank": max(ranks),
            "minimum_margin": min(margins),
        }
    return scores, summary


def effective_sample_size(weights: Iterable[float]) -> float:
    values = [float(value) for value in weights if float(value) > 0]
    denominator = sum(value * value for value in values)
    return 0.0 if not denominator else sum(values) ** 2 / denominator


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def dirichlet_summary(
    alphas: dict[str, float], seed: int, draws: int = 10_000
) -> dict[str, dict[str, float]]:
    if set(alphas) != set(OUTCOMES) or any(float(value) <= 0 for value in alphas.values()):
        raise ValueError("Dirichlet parameters must be positive for all award outcomes")
    rng = random.Random(seed)
    samples = {outcome: [] for outcome in OUTCOMES}
    for _ in range(draws):
        gamma = {outcome: rng.gammavariate(float(alphas[outcome]), 1.0) for outcome in OUTCOMES}
        total = sum(gamma.values())
        for outcome in OUTCOMES:
            samples[outcome].append(gamma[outcome] / total)
    alpha_total = sum(float(value) for value in alphas.values())
    return {
        outcome: {
            "mean": float(alphas[outcome]) / alpha_total,
            "lower_80": _quantile(samples[outcome], 0.10),
            "upper_80": _quantile(samples[outcome], 0.90),
        }
        for outcome in OUTCOMES
    }


def deterministic_seed(input_hashes: dict[str, str], problem: str) -> int:
    encoded = json.dumps(input_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded + b"\0" + problem.encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big")


def portable_calibration_value(raw: str) -> bool:
    return bool(raw) and not any(token in raw for token in ("/", "\\", ":", "\n", "\r"))
