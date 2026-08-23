#!/usr/bin/env python3
"""Generate a local, evidence-bound CUMCM A/B/C recommendation and Chinese report."""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from problem_selection_core import (
    BASE_WEIGHTS,
    CALIBRATION_FIELDS,
    CAPABILITY_PROFILE,
    CRITERIA,
    EVIDENCE_FIELDS,
    HEX64,
    OUTCOMES,
    PROBLEMS,
    SCENARIOS,
    SCREENING_FIELDS,
    SLUG,
    combine_ai_fit,
    deterministic_seed,
    dirichlet_summary,
    effective_sample_size,
    load_capability_profile,
    load_csv_rows,
    load_json_object,
    parse_utc,
    portable_calibration_value,
    recommendation_input_hashes,
    safe_project_file,
    scenario_analysis,
    sha256_file,
    skill_fingerprint,
    split_tags,
    validate_locator_hash,
)


RESOLVED_FATAL = {"none", "no", "not_applicable"}
EARLY_FAILURES = {
    "none", "timeout", "infeasible", "parse_failure", "numerical_failure",
    "data_insufficient", "other",
}
OBSERVATION_TYPES = {"strength", "weakness", "risk", "unknown"}


def _float(raw: str, label: str, errors: list[str], minimum: float = 0.0) -> float:
    try:
        value = float(raw)
    except ValueError:
        errors.append(f"{label} must be numeric")
        return 0.0
    if value < minimum:
        errors.append(f"{label} must be at least {minimum:g}")
    return value


def load_screening(root: Path, errors: list[str]) -> dict[str, dict[str, Any]]:
    path = root / "reports" / "problem_screening.csv"
    try:
        fields, raw_rows = load_csv_rows(path)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot read problem_screening.csv: {exc}")
        return {}
    missing = set(SCREENING_FIELDS) - set(fields)
    if missing:
        errors.append("problem_screening.csv missing columns: " + ", ".join(sorted(missing)))
    rows: dict[str, dict[str, Any]] = {}
    for line, row in enumerate(raw_rows, 2):
        problem = str(row.get("problem_id") or "").strip().upper()
        label = f"problem_screening.csv:{line}"
        if problem not in PROBLEMS or problem in rows:
            errors.append(f"{label} has an invalid or duplicate A/B/C problem_id")
            continue
        tags = split_tags(str(row.get("task_families") or ""))
        families = split_tags(str(row.get("required_model_families") or ""))
        if not tags or not all(SLUG.fullmatch(item) for item in tags):
            errors.append(f"{label} task_families must be semicolon-separated portable tags")
        if not families or not all(SLUG.fullmatch(item) for item in families):
            errors.append(f"{label} required_model_families must be portable capability ids")
        early_failure = str(row.get("early_failure_type") or "").strip().lower()
        if early_failure not in EARLY_FAILURES:
            errors.append(f"{label} early_failure_type is invalid")
        if str(row.get("status") or "").strip().lower() != "verified":
            errors.append(f"{label} status must be verified")
        for required in ("attachment_state", "semantic_risk", "expected_deliverables"):
            if not str(row.get(required) or "").strip():
                errors.append(f"{label} {required} is missing")
        validate_locator_hash(
            root,
            str(row.get("evidence_locator") or "").strip(),
            str(row.get("evidence_sha256") or "").strip(),
            label,
            errors,
        )
        selected = str(row.get("deep_trial_selected") or "").strip().lower()
        if selected not in {"yes", "no"}:
            errors.append(f"{label} deep_trial_selected must be yes or no")
        preliminary = _float(
            str(row.get("preliminary_score") or ""), f"{label} preliminary_score", errors
        )
        if preliminary > 100:
            errors.append(f"{label} preliminary_score must be at most 100")
        elimination_reason = str(row.get("elimination_reason") or "").strip()
        if selected == "yes" and elimination_reason.lower() != "not_applicable":
            errors.append(f"{label} deep-trial candidate requires not_applicable elimination_reason")
        if selected == "no" and elimination_reason.lower() in {"", "not_applicable"}:
            errors.append(f"{label} eliminated candidate requires a reason")
        rows[problem] = {
            **row,
            "problem_id": problem,
            "task_family_set": tags,
            "required_family_set": families,
            "screening_minutes_value": _float(str(row.get("screening_minutes") or ""), f"{label} screening_minutes", errors, 0.01),
            "micro_minutes_value": _float(str(row.get("micro_baseline_minutes") or ""), f"{label} micro_baseline_minutes", errors, 0.01),
            "preliminary_score_value": preliminary,
            "deep_selected_value": selected == "yes",
            "elimination_reason_value": elimination_reason,
            "deep_budget_value": _float(str(row.get("deep_trial_budget_minutes") or ""), f"{label} deep_trial_budget_minutes", errors),
            "deep_elapsed_value": _float(str(row.get("deep_trial_elapsed_minutes") or ""), f"{label} deep_trial_elapsed_minutes", errors),
            "early_failure_value": early_failure,
        }
    if set(rows) != set(PROBLEMS):
        errors.append("problem_screening.csv must contain exactly one row for A, B, and C")
    return rows


def timing_fairness(rows: dict[str, dict[str, Any]]) -> tuple[bool, list[str]]:
    if set(rows) != set(PROBLEMS):
        return False, ["A/B/C screening evidence is incomplete"]
    reasons: list[str] = []
    for problem, row in rows.items():
        if not 12 <= row["screening_minutes_value"] <= 18:
            reasons.append(f"{problem} screening time is outside the 15-minute comparable window")
        timing_exception = str(row.get("timing_exception") or "").strip()
        if row["micro_minutes_value"] < 24 and row["early_failure_value"] == "none" and not timing_exception:
            reasons.append(f"{problem} micro-baseline ended early without a typed failure or exception")
        if row["micro_minutes_value"] > 36 and not timing_exception:
            reasons.append(f"{problem} received more than 20% extra micro-baseline time")
    ordinary = [
        row["micro_minutes_value"]
        for row in rows.values()
        if row["early_failure_value"] == "none" and not str(row.get("timing_exception") or "").strip()
    ]
    if len(ordinary) >= 2 and max(ordinary) > 1.20 * min(ordinary) + 1e-9:
        reasons.append("micro-baseline timing differs by more than 20% without a typed exception")
    deep = [row for row in rows.values() if row["deep_selected_value"]]
    if len(deep) != 2:
        reasons.append("exactly two candidates must receive the H2.25-H5.25 deep trial")
    elif any(not 72 <= row["deep_budget_value"] <= 108 for row in deep):
        reasons.append("deep-trial budgets must implement the declared 90-minute window")
    elif abs(deep[0]["deep_budget_value"] - deep[1]["deep_budget_value"]) > 1e-9:
        reasons.append("the top two candidates do not have equal declared deep-trial budgets")
    for row in deep:
        exception = str(row.get("timing_exception") or "").strip()
        if row["deep_elapsed_value"] < 0.80 * row["deep_budget_value"] and not exception:
            reasons.append(f"{row['problem_id']} used less than 80% of its deep-trial budget")
        if row["deep_elapsed_value"] > 1.20 * row["deep_budget_value"] and not str(row.get("timing_exception") or "").strip():
            reasons.append(f"{row['problem_id']} exceeded its deep-trial budget without an exception")
    ordinary_deep = [
        row["deep_elapsed_value"] for row in deep
        if not str(row.get("timing_exception") or "").strip()
    ]
    if len(ordinary_deep) == 2 and max(ordinary_deep) > 1.20 * min(ordinary_deep) + 1e-9:
        reasons.append("top-two actual deep-trial times differ by more than 20%")
    eliminated = [row for row in rows.values() if not row["deep_selected_value"]]
    if len(deep) == 2 and len(eliminated) == 1 and (
        eliminated[0]["preliminary_score_value"] > min(row["preliminary_score_value"] for row in deep)
    ):
        reasons.append("the eliminated candidate outranks a deep-trial candidate at H2.25")
    return not reasons, reasons


def load_evidence(root: Path, errors: list[str]) -> dict[str, dict[str, dict[str, Any]]]:
    path = root / "reports" / "problem_selection_evidence.csv"
    try:
        fields, rows = load_csv_rows(path)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot read problem_selection_evidence.csv: {exc}")
        return {}
    missing = set(EVIDENCE_FIELDS) - set(fields)
    if missing:
        errors.append("problem_selection_evidence.csv missing columns: " + ", ".join(sorted(missing)))
    result: dict[str, dict[str, dict[str, Any]]] = {problem: {} for problem in PROBLEMS}
    for line, row in enumerate(rows, 2):
        problem = str(row.get("problem_id") or "").strip().upper()
        criterion = str(row.get("criterion") or "").strip()
        label = f"problem_selection_evidence.csv:{line}"
        if problem not in PROBLEMS or criterion not in CRITERIA or criterion in result.get(problem, {}):
            errors.append(f"{label} has an invalid or duplicate problem/criterion")
            continue
        raw_rating = str(row.get("rating") or "").strip().lower()
        if raw_rating == "unknown":
            rating: float | None = None
        else:
            try:
                rating = float(int(raw_rating))
            except ValueError:
                errors.append(f"{label} rating must be an integer 0-4 or unknown")
                rating = None
            else:
                if not 0 <= rating <= 4:
                    errors.append(f"{label} rating must be between 0 and 4")
        observation_type = str(row.get("observation_type") or "").strip().lower()
        if observation_type not in OBSERVATION_TYPES:
            errors.append(f"{label} observation_type is invalid")
        if rating is None and observation_type != "unknown":
            errors.append(f"{label} unknown rating requires unknown observation_type")
        if rating is not None and observation_type == "unknown":
            errors.append(f"{label} numeric rating cannot use unknown observation_type")
        observation = str(row.get("observation") or "").strip()
        if not observation:
            errors.append(f"{label} observation is missing")
        if str(row.get("status") or "").strip().lower() != "verified":
            errors.append(f"{label} status must be verified")
        locator = str(row.get("evidence_locator") or "").strip()
        digest = str(row.get("evidence_sha256") or "").strip()
        validate_locator_hash(root, locator, digest, label, errors)
        result[problem][criterion] = {
            "rating": rating,
            "evidence_locator": locator,
            "evidence_sha256": digest.lower(),
            "observation_type": observation_type,
            "observation": observation,
        }
    for problem in PROBLEMS:
        missing_criteria = set(CRITERIA) - set(result[problem])
        if missing_criteria:
            errors.append(f"{problem} lacks criterion evidence: " + ", ".join(sorted(missing_criteria)))
    return result


def load_audition(root: Path, errors: list[str]) -> dict[str, dict[str, str]]:
    try:
        fields, rows = load_csv_rows(root / "reports" / "problem_audition.csv")
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"cannot read problem_audition.csv: {exc}")
        return {}
    required = {"problem_id", "fallback_route", "fatal_risk", "baseline_result", "paper_figure"}
    if required - set(fields):
        errors.append("problem_audition.csv lacks recommendation fields: " + ", ".join(sorted(required - set(fields))))
    result: dict[str, dict[str, str]] = {}
    for line, row in enumerate(rows, 2):
        problem = str(row.get("problem_id") or "").strip().upper()
        if problem not in PROBLEMS or problem in result:
            errors.append(f"problem_audition.csv:{line} has an invalid or duplicate A/B/C problem_id")
            continue
        if not str(row.get("fallback_route") or "").strip():
            errors.append(f"problem_audition.csv:{line} fallback_route is missing")
        if not str(row.get("fatal_risk") or "").strip():
            errors.append(f"problem_audition.csv:{line} fatal_risk is missing")
        result[problem] = row
    if set(result) != set(PROBLEMS):
        errors.append("problem_audition.csv must contain exactly one row for A, B, and C")
    return result


def validate_snapshot(root: Path, profile: dict[str, Any]) -> tuple[dict[str, Any], bool, list[str]]:
    warnings: list[str] = []
    try:
        snapshot = load_json_object(root / "reports" / "ai_capability_snapshot.json")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {}, False, [f"AI capability snapshot is unavailable: {exc}"]
    generated = parse_utc(snapshot.get("generated_at_utc"))
    age = None if generated is None else (datetime.now(timezone.utc) - generated).total_seconds()
    if generated is None or age is None or age < -300 or age > 86_400:
        warnings.append("AI capability snapshot is not a valid same-day observation")
    if snapshot.get("profile_version") != profile.get("profile_version"):
        warnings.append("AI capability snapshot profile version is stale")
    if str(snapshot.get("profile_sha256") or "").lower() != sha256_file(CAPABILITY_PROFILE):
        warnings.append("AI capability snapshot profile hash is stale")
    if str(snapshot.get("skill_fingerprint") or "").lower() != skill_fingerprint():
        warnings.append("AI capability snapshot Skill fingerprint is stale")
    kernel = snapshot.get("kernel_regression")
    if not isinstance(kernel, dict):
        warnings.append("AI capability snapshot lacks kernel-regression binding")
    else:
        path = safe_project_file(root, str(kernel.get("path") or ""))
        if path is None or not path.is_file() or str(kernel.get("sha256") or "").lower() != sha256_file(path):
            warnings.append("AI capability snapshot kernel-regression binding is stale")
        elif str(kernel.get("status") or "").upper() != "PASS":
            warnings.append("AI capability snapshot kernel regression is not PASS")
    valid = (
        snapshot.get("status") == "PASS"
        and snapshot.get("valid_for_calibration") is True
        and not warnings
    )
    return snapshot, valid, warnings


def public_prior(
    root: Path, failed: list[str]
) -> tuple[dict[str, float] | None, float | None]:
    try:
        payload = load_json_object(root / "reports" / "public_award_prior.json")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        failed.append(f"public prior unreadable: {exc}")
        return None, None
    if payload.get("status") != "verified" or payload.get("reviewer_status") != "verified":
        failed.append("public prior is not source-reviewed and verified")
    if str(payload.get("competition_scope") or "").upper() != "CUMCM":
        failed.append("public prior competition scope is incompatible")
    if not str(payload.get("population_definition") or "").strip() or not str(
        payload.get("denominator_definition") or ""
    ).strip():
        failed.append("public prior population or denominator definition is missing")
    if payload.get("outcome_definition") != "mutually_exclusive_highest_award":
        failed.append("public prior outcomes are not declared mutually exclusive")
    applicable = payload.get("applies_to_problem_types")
    if not isinstance(applicable, list) or not set(PROBLEMS).issubset({str(item).upper() for item in applicable}):
        failed.append("public prior does not declare applicability to A/B/C")
    years = payload.get("applicable_years")
    if not isinstance(years, list) or not years or not all(isinstance(year, int) for year in years):
        failed.append("public prior applicable_years is invalid")
    retrieved = parse_utc(payload.get("retrieved_at"))
    if not str(payload.get("source_url") or "").strip() or retrieved is None:
        failed.append("public prior source URL or retrieval date is missing")
    elif not -86_400 <= (datetime.now(timezone.utc) - retrieved).total_seconds() <= 366 * 86_400:
        failed.append("public prior retrieval record is stale or future-dated")
    source = safe_project_file(root, str(payload.get("source_snapshot") or ""))
    if source is None or not source.is_file() or str(payload.get("source_sha256") or "").lower() != sha256_file(source):
        failed.append("public prior saved source binding is missing or stale")
    try:
        strength = float(payload.get("effective_strength", 8))
    except (TypeError, ValueError):
        strength = 0.0
    if not 0 < strength <= 10:
        failed.append("public prior effective_strength must be in (0, 10]")
    counts = payload.get("category_counts")
    parsed: dict[str, float] = {}
    if not isinstance(counts, dict) or set(counts) != set(OUTCOMES):
        failed.append("public prior must contain exactly four category counts")
    else:
        for outcome in OUTCOMES:
            try:
                parsed[outcome] = float(counts[outcome])
            except (TypeError, ValueError):
                parsed[outcome] = -1
        if any(value <= 0 for value in parsed.values()):
            failed.append("public prior category counts must be positive for all four outcomes")
    if failed:
        return None, None
    total = sum(parsed.values())
    return {outcome: strength * parsed[outcome] / total for outcome in OUTCOMES}, strength


def calibration_rows(root: Path, failed: list[str]) -> list[dict[str, Any]]:
    try:
        fields, rows = load_csv_rows(root / "reports" / "problem_selection_calibration.csv")
    except (OSError, UnicodeError, csv.Error) as exc:
        failed.append(f"private calibration unreadable: {exc}")
        return []
    if tuple(fields) != CALIBRATION_FIELDS:
        failed.append("private calibration columns do not match the privacy-minimized contract")
        return []
    parsed: list[dict[str, Any]] = []
    invalid = 0
    for row in rows:
        try:
            year = int(str(row["year"]))
            score = float(row["composite_score"])
            ratings = {criterion: float(int(row[f"{criterion}_rating"])) for criterion in CRITERIA}
        except (KeyError, TypeError, ValueError):
            invalid += 1
            continue
        tags = split_tags(row["task_family_tags"])
        valid = (
            bool(SLUG.fullmatch(row["case_id"]))
            and 2000 <= year <= 2100
            and tags and all(SLUG.fullmatch(tag) for tag in tags)
            and portable_calibration_value(row["ai_profile_version"])
            and all(0 <= value <= 4 for value in ratings.values())
            and 0 <= score <= 100
            and row["selected_problem_type"].upper() in PROBLEMS
            and row["award_label"] in OUTCOMES
            and bool(HEX64.fullmatch(row["evidence_sha256"]))
            and row["status"].lower() == "verified"
        )
        if not valid:
            invalid += 1
            continue
        parsed.append(
            {
                "case_id": row["case_id"], "year": year, "tags": tags,
                "profile_version": row["ai_profile_version"], "score": score,
                "award_label": row["award_label"],
            }
        )
    if invalid:
        failed.append(f"private calibration contains {invalid} invalid or unverified row(s)")
    if len(parsed) < 12:
        failed.append("private calibration has fewer than 12 valid rows")
    if len({row["year"] for row in parsed}) < 3:
        failed.append("private calibration covers fewer than three years")
    return parsed


def calibrated_probabilities(
    root: Path,
    candidates: dict[str, dict[str, Any]],
    profile_version: str,
    snapshot_valid: bool,
    input_hashes: dict[str, str],
) -> dict[str, Any]:
    failed: list[str] = []
    if not snapshot_valid:
        failed.append("current AI capability snapshot is invalid or stale")
    prior, strength = public_prior(root, failed)
    rows = calibration_rows(root, failed)
    per_candidate: dict[str, Any] = {}
    weights_by_problem: dict[str, list[float]] = {}
    for problem, candidate in candidates.items():
        current_tags = set(candidate["task_families"])
        values: list[float] = []
        for row in rows:
            union = current_tags | row["tags"]
            overlap = len(current_tags & row["tags"]) / len(union) if union else 0.0
            compatibility = 1.0 if row["profile_version"] == profile_version else 0.25
            proximity = max(0.0, 1.0 - abs(row["score"] - candidate["base_score"]) / 100.0)
            values.append(0.50 * overlap + 0.25 * compatibility + 0.25 * proximity)
        weights_by_problem[problem] = values
        ess = effective_sample_size(values)
        per_candidate[problem] = {"effective_local_sample_size": round(ess, 6)}
        if ess < 12:
            failed.append(f"{problem} effective local sample size is below 12")
    failed = list(dict.fromkeys(failed))
    if failed or prior is None:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "failed_gates": failed,
            "public_prior_strength": strength,
            "candidate_summaries": per_candidate,
        }
    for problem, candidate in candidates.items():
        weighted_counts = {outcome: 0.0 for outcome in OUTCOMES}
        for row, weight in zip(rows, weights_by_problem[problem]):
            weighted_counts[row["award_label"]] += weight
        alphas = {outcome: prior[outcome] + weighted_counts[outcome] for outcome in OUTCOMES}
        distribution = dirichlet_summary(alphas, deterministic_seed(input_hashes, problem))
        national = distribution["national_first"]["mean"] + distribution["national_second"]["mean"]
        per_candidate[problem].update(
            distribution=distribution,
            national_award_probability=national,
        )
    return {
        "status": "AVAILABLE",
        "failed_gates": [],
        "public_prior_strength": strength,
        "verified_local_row_count": len(rows),
        "covered_years": sorted({row["year"] for row in rows}),
        "candidate_summaries": per_candidate,
    }


def choose_recommendation(
    candidates: dict[str, dict[str, Any]], calibration: dict[str, Any]
) -> tuple[list[str], str, list[str]]:
    eligible = [
        problem for problem, item in candidates.items()
        if item["deep_trial_selected"] and not item["fatal_risk_unresolved"]
    ]
    if not eligible:
        return [], "none", ["all candidates have unresolved fatal risks"]
    probability_available = calibration.get("status") == "AVAILABLE"
    if probability_available:
        measure = {
            problem: calibration["candidate_summaries"][problem]["national_award_probability"]
            for problem in eligible
        }
        basis = "calibrated_national_award_probability"
        tie_gap = 0.03
    else:
        measure = {problem: candidates[problem]["base_score"] for problem in eligible}
        basis = "robust_composite_score"
        tie_gap = 3.0
    ordered = sorted(eligible, key=lambda problem: (-measure[problem], problem))
    leader = ordered[0]
    co_leaders = [problem for problem in ordered if measure[leader] - measure[problem] < tie_gap + 1e-12]
    reasons: list[str] = []
    if len(co_leaders) > 1:
        reasons.append("leading margin is below the declared three-point threshold")
    if candidates[leader]["ai_prior_live_conflict"]:
        reasons.append("the leading candidate has an unresolved prior/live AI-fit conflict")
        co_leaders = ordered[: min(2, len(ordered))]
    if candidates[leader]["scenario_win_rate"] < 0.75:
        reasons.append("no stable winner survives at least three quarters of weight scenarios")
        co_leaders = ordered[: min(2, len(ordered))]
    return co_leaders, basis, reasons


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CUMCM A/B/C 选题推荐（本地证据版）",
        "",
        f"状态：`{report['status']}`；置信度：`{report['confidence']}`；排序依据：`{report['ranking_basis']}`。",
        "",
        "> 本报告只评估当前 AI/Codex 与当日可执行证据，不评估学生团队能力，也不保证官方评奖结果。团队的专业背景和执行能力可能改变最终最佳选择。",
        "",
        "## 相对排序",
        "",
        "| 排名 | 题目 | H2.25 初筛分 | 深入试跑 | 基础得分 | 场景胜率 | 最差名次 | 未决致命风险 |",
        "| ---: | --- | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for item in report.get("ranking", []):
        lines.append(
            f"| {item['rank']} | {item['problem_id']} | {item['preliminary_score']:.2f} | {'是' if item['deep_trial_selected'] else '否'} | {item['base_score']:.2f} | "
            f"{item['scenario_win_rate']:.2f} | {item['worst_rank']} | "
            f"{'是' if item['fatal_risk_unresolved'] else '否'} |"
        )
    for problem in PROBLEMS:
        candidate = report.get("candidates", {}).get(problem)
        if not candidate:
            continue
        lines.extend(
            [
                "",
                f"## {problem} 题",
                "",
                "适配模型族：" + "、".join(candidate["required_model_families"]),
                "",
                f"后备路线：{candidate['fallback_route']}",
                f"致命风险记录：{candidate['fatal_risk']}",
                "",
            ]
        )
        headings = (("strength", "优势"), ("weakness", "劣势"), ("risk", "风险"), ("unknown", "未知项"))
        for key, heading in headings:
            observations = [item for item in candidate["observations"] if item["type"] == key]
            lines.append(f"### {heading}")
            lines.append("")
            if observations:
                lines.extend(
                    f"- {item['text']}（证据：`{item['evidence_locator']}`）" for item in observations
                )
            else:
                lines.append("- 暂无单独核验的此类观察；不补写推测性内容。")
            lines.append("")
        if candidate["supported_observation_count"] < 3:
            lines.append(
                f"证据不足：当前仅有 {candidate['supported_observation_count']} 条已评分的优势/劣势/风险观察，未知项不计入，且未补写推测性内容。"
            )
        probability = report["probability_calibration"]["candidate_summaries"].get(problem, {})
        lines.append("### 获奖概率状态")
        lines.append("")
        if report["probability_calibration"]["status"] == "AVAILABLE":
            labels = {
                "national_first": "国家一等奖", "national_second": "国家二等奖",
                "provincial_award": "省级奖", "no_award": "未获奖",
            }
            for outcome in OUTCOMES:
                estimate = probability["distribution"][outcome]
                lines.append(
                    f"- {labels[outcome]}：均值 {100 * estimate['mean']:.1f}%，中央 80% 区间 "
                    f"[{100 * estimate['lower_80']:.1f}%，{100 * estimate['upper_80']:.1f}%]"
                )
        else:
            lines.append("`INSUFFICIENT_EVIDENCE`：不输出个性化百分比。")
    lines.extend(["", "## 推荐与人工确认", ""])
    if report.get("recommended_problem"):
        lines.append(f"建议优先选择 **{report['recommended_problem']} 题**。")
    elif report.get("co_leading_problems"):
        lines.append("当前并列领先：**" + " / ".join(report["co_leading_problems"]) + "**；不制造虚假单一赢家。")
    else:
        lines.append("当前没有可安全推荐的题目，需先解决致命风险或证据缺口。")
    if report["probability_calibration"]["status"] != "AVAILABLE":
        lines.append("")
        lines.append("概率未开放原因：" + "；".join(report["probability_calibration"]["failed_gates"]) + "。")
    lines.extend(
        [
            "",
            "本报告不会自动锁题。请先向用户展示本报告，再运行 "
            "`record_problem_selection_confirmation.py` 记录其选择；该记录只是审计声明，不是身份认证。",
            "",
        ]
    )
    return "\n".join(lines)


def build_recommendation(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    limiting: list[str] = []
    profile, capability_ratings = load_capability_profile(errors)
    screening = load_screening(root, errors)
    evidence = load_evidence(root, errors)
    audition = load_audition(root, errors)
    timing_fair, timing_reasons = timing_fairness(screening)
    if not timing_fair:
        limiting.extend(timing_reasons)
    snapshot, snapshot_valid, snapshot_warnings = validate_snapshot(root, profile)
    if not snapshot_valid:
        limiting.extend(snapshot_warnings or ["AI capability snapshot is not valid for calibration"])
    candidates: dict[str, dict[str, Any]] = {}
    candidate_ratings: dict[str, dict[str, float | None]] = {}
    if set(screening) == set(evidence) == set(audition) == set(PROBLEMS):
        for problem in PROBLEMS:
            required = screening[problem]["required_family_set"]
            known = [capability_ratings[item] for item in required if item in capability_ratings]
            unknown_families = sorted(required - set(capability_ratings))
            prior = sum(known) / len(known) if known and not unknown_families else 0.0
            live = evidence[problem]["ai_capability_fit"]["rating"]
            live_value = 0.0 if live is None else live
            ratings = {criterion: evidence[problem][criterion]["rating"] for criterion in CRITERIA}
            ratings["ai_capability_fit"] = combine_ai_fit(prior, live_value)
            conflict = bool(known and live is not None and abs(sum(known) / len(known) - live) >= 1.5)
            unknown = [criterion for criterion in CRITERIA if evidence[problem][criterion]["rating"] is None]
            if unknown_families:
                unknown.append("ai_capability_prior")
            observations = [
                {
                    "criterion": criterion,
                    "type": evidence[problem][criterion]["observation_type"],
                    "text": evidence[problem][criterion]["observation"],
                    "evidence_locator": evidence[problem][criterion]["evidence_locator"],
                    "evidence_sha256": evidence[problem][criterion]["evidence_sha256"],
                }
                for criterion in CRITERIA
                if evidence[problem][criterion]["observation"]
            ]
            supported_observations = sum(
                item["type"] in {"strength", "weakness", "risk"} for item in observations
            )
            if supported_observations < 3:
                limiting.append(f"{problem} has fewer than three supported observations")
            fatal_text = str(audition[problem].get("fatal_risk") or "").strip()
            candidates[problem] = {
                "problem_id": problem,
                "task_families": sorted(screening[problem]["task_family_set"]),
                "required_model_families": sorted(required),
                "criterion_ratings": ratings,
                "raw_live_ai_rating": live,
                "bundled_ai_prior_rating": prior if not unknown_families else None,
                "ai_prior_live_conflict": conflict,
                "unknown_criteria": sorted(set(unknown)),
                "fatal_risk": fatal_text,
                "fatal_risk_unresolved": fatal_text.lower() not in RESOLVED_FATAL,
                "preliminary_score": screening[problem]["preliminary_score_value"],
                "deep_trial_selected": screening[problem]["deep_selected_value"],
                "elimination_reason": screening[problem]["elimination_reason_value"],
                "fallback_route": str(audition[problem].get("fallback_route") or "").strip(),
                "observations": observations,
                "supported_observation_count": supported_observations,
            }
            candidate_ratings[problem] = ratings
    scenario_scores: dict[str, dict[str, float]] = {}
    summaries: dict[str, dict[str, Any]] = {}
    if len(candidate_ratings) == 3:
        scenario_scores, summaries = scenario_analysis(candidate_ratings)
        for problem in PROBLEMS:
            candidates[problem].update(
                base_score=scenario_scores["base"][problem],
                scenario_scores={name: scores[problem] for name, scores in scenario_scores.items()},
                **summaries[problem],
            )
        deep_scores = [
            candidates[problem]["base_score"]
            for problem in PROBLEMS if candidates[problem]["deep_trial_selected"]
        ]
        for problem in PROBLEMS:
            if (
                not candidates[problem]["deep_trial_selected"] and deep_scores
                and candidates[problem]["base_score"] > min(deep_scores) + 1e-9
            ):
                limiting.append(
                    f"{problem} now outranks a deep-trial candidate; rerun the H2.25 elimination before locking"
                )
    input_hashes = recommendation_input_hashes(root)
    calibration = (
        calibrated_probabilities(
            root, candidates, str(profile.get("profile_version") or ""), snapshot_valid, input_hashes
        )
        if len(candidates) == 3 and not errors
        else {"status": "INSUFFICIENT_EVIDENCE", "failed_gates": ["candidate evidence is invalid"], "candidate_summaries": {}}
    )
    co_leaders: list[str] = []
    ranking_basis = "unavailable"
    tie_reasons: list[str] = []
    if len(candidates) == 3 and not errors:
        co_leaders, ranking_basis, tie_reasons = choose_recommendation(candidates, calibration)
    ordered = sorted(
        candidates,
        key=lambda problem: (
            candidates[problem]["fatal_risk_unresolved"],
            -(
                calibration.get("candidate_summaries", {}).get(problem, {}).get("national_award_probability", candidates[problem].get("base_score", 0.0))
            ),
            problem,
        ),
    )
    ranking = []
    for index, problem in enumerate(ordered, 1):
        item = candidates[problem]
        item["rank"] = index
        ranking.append(
            {
                "rank": index, "problem_id": problem, "base_score": item.get("base_score", 0.0),
                "scenario_win_rate": item.get("scenario_win_rate", 0.0),
                "worst_rank": item.get("worst_rank"),
                "preliminary_score": item["preliminary_score"],
                "deep_trial_selected": item["deep_trial_selected"],
                "fatal_risk_unresolved": item["fatal_risk_unresolved"],
            }
        )
    recommended = co_leaders[0] if len(co_leaders) == 1 else None
    confidence = "unavailable"
    if not errors and co_leaders:
        leader = co_leaders[0]
        decisive_unknown = set(candidates[leader]["unknown_criteria"]) & {
            "closure_result", "result_verifiability", "ai_capability_fit", "ai_capability_prior"
        }
        if limiting:
            confidence = "LIMITED"
        elif len(co_leaders) > 1:
            confidence = "low"
        elif (
            not candidates[leader]["fatal_risk_unresolved"] and not decisive_unknown
            and snapshot_valid and candidates[leader]["scenario_win_rate"] == 1.0
            and candidates[leader]["minimum_margin"] >= 5.0
        ):
            confidence = "high"
        elif not candidates[leader]["fatal_risk_unresolved"] and candidates[leader]["scenario_win_rate"] >= 0.75:
            confidence = "medium" if snapshot_valid else "low"
        else:
            confidence = "low"
    status = "FAIL" if errors else ("LIMITED" if limiting else "PASS")
    return {
        "schema_version": 1,
        "status": status,
        "scope": "AI/Codex-only local A/B/C evidence ranking; team ability and official judging are outside scope",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_version": profile.get("profile_version"),
        "skill_fingerprint": skill_fingerprint(),
        "input_hashes": input_hashes,
        "weights": {"base": BASE_WEIGHTS, "scenarios": SCENARIOS},
        "timing_fair": timing_fair,
        "timing_findings": timing_reasons,
        "capability_snapshot_status": snapshot.get("status", "MISSING"),
        "candidates": candidates,
        "scenario_scores": scenario_scores,
        "ranking": ranking,
        "ranking_basis": ranking_basis,
        "recommended_problem": recommended,
        "co_leading_problems": co_leaders if len(co_leaders) > 1 else [],
        "tie_or_instability_reasons": tie_reasons,
        "confidence": confidence,
        "probability_calibration": calibration,
        "requires_user_confirmation": status != "FAIL" and bool(co_leaders),
        "limitations": [
            "Student-team expertise is not scored and may change the best final choice.",
            "Award intervals are conditional estimates, not guarantees of official judging.",
            "No recommendation is an automatic H6 problem lock.",
        ],
        "errors": errors,
        "warnings": list(dict.fromkeys(limiting)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--out-json", default="reports/problem_selection_recommendation.json")
    parser.add_argument("--out-md", default="reports/problem_selection_recommendation.md")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    outputs = [safe_project_file(root, args.out_json), safe_project_file(root, args.out_md)]
    if any(path is None for path in outputs):
        raise SystemExit("outputs must be relative paths inside the project")
    report = build_recommendation(root)
    json_path, markdown_path = outputs
    assert json_path is not None and markdown_path is not None
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(report["status"])
    return {"PASS": 0, "LIMITED": 2, "FAIL": 1}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
