#!/usr/bin/env python3
"""Aggregate three independent post-paper reviews without predicting awards."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


REVIEWER_ROLES = {"model", "evidence", "writing"}
SEVERITIES = {"none", "minor", "major", "veto"}


def contains_award_prediction(value: object) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in {
                "award_prediction",
                "predicted_award",
                "award_probability",
                "award_likelihood",
            }:
                return True
            if contains_award_prediction(item):
                return True
    elif isinstance(value, list):
        return any(contains_award_prediction(item) for item in value)
    return False


def nonempty_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def validate_review(review: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    label = f"review[{index}]"
    if contains_award_prediction(review):
        errors.append(f"{label} contains a prohibited award prediction field.")
    if not isinstance(review.get("review_id"), str) or not review["review_id"].strip():
        errors.append(f"{label}.review_id must not be empty.")
    if review.get("reviewer_role") not in REVIEWER_ROLES:
        errors.append(f"{label}.reviewer_role must be model, evidence, or writing.")
    score = review.get("score")
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not 1 <= float(score) <= 5
    ):
        errors.append(f"{label}.score must be between 1 and 5.")
    confidence = review.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= float(confidence) <= 1
    ):
        errors.append(f"{label}.confidence must be between 0 and 1.")
    if not nonempty_strings(review.get("artifact_locators")):
        errors.append(f"{label}.artifact_locators must contain at least one locator.")

    objection = review.get("strongest_objection")
    if not isinstance(objection, dict):
        errors.append(f"{label}.strongest_objection must be an object.")
    else:
        if not isinstance(objection.get("summary"), str) or not objection["summary"].strip():
            errors.append(f"{label}.strongest_objection.summary must not be empty.")
        if objection.get("severity") not in SEVERITIES:
            errors.append(
                f"{label}.strongest_objection.severity must be none, minor, major, or veto."
            )
        if (
            not isinstance(objection.get("artifact_locator"), str)
            or not objection["artifact_locator"].strip()
        ):
            errors.append(
                f"{label}.strongest_objection.artifact_locator must not be empty."
            )
        if not isinstance(objection.get("rerun_required"), bool):
            errors.append(
                f"{label}.strongest_objection.rerun_required must be boolean."
            )

    accepted = review.get("accepted_limitations")
    if not isinstance(accepted, list):
        errors.append(f"{label}.accepted_limitations must be a list.")
    else:
        for limitation_index, limitation in enumerate(accepted, start=1):
            limitation_label = f"{label}.accepted_limitations[{limitation_index}]"
            if not isinstance(limitation, dict):
                errors.append(f"{limitation_label} must be an object.")
                continue
            if (
                not isinstance(limitation.get("summary"), str)
                or not limitation["summary"].strip()
            ):
                errors.append(f"{limitation_label}.summary must not be empty.")
            if (
                not isinstance(limitation.get("artifact_locator"), str)
                or not limitation["artifact_locator"].strip()
            ):
                errors.append(f"{limitation_label}.artifact_locator must not be empty.")
            if not isinstance(limitation.get("rerun_required"), bool):
                errors.append(f"{limitation_label}.rerun_required must be boolean.")
    return errors


def aggregate_reviews(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    if len(reviews) != 3:
        errors.append("exactly three independent review JSON objects are required.")
    for index, review in enumerate(reviews, start=1):
        if not isinstance(review, dict):
            errors.append(f"review[{index}] must be a JSON object.")
            continue
        errors.extend(validate_review(review, index))

    roles = [review.get("reviewer_role") for review in reviews if isinstance(review, dict)]
    review_ids = [review.get("review_id") for review in reviews if isinstance(review, dict)]
    if len(reviews) == 3 and set(roles) != REVIEWER_ROLES:
        errors.append("reviews must contain exactly one model, evidence, and writing role.")
    if len(review_ids) != len(set(review_ids)):
        errors.append("review_id values must be distinct for independent passes.")
    if errors:
        raise ValueError(" ".join(errors))

    ordered = sorted(reviews, key=lambda item: item["reviewer_role"])
    scores = [float(review["score"]) for review in ordered]
    confidences = [float(review["confidence"]) for review in ordered]
    score_range = max(scores) - min(scores)
    confidence_range = max(confidences) - min(confidences)
    highest_score = max(scores)
    lowest_score = min(scores)
    total_confidence = sum(confidences)
    weighted_score = (
        sum(score * confidence for score, confidence in zip(scores, confidences))
        / total_confidence
        if total_confidence
        else mean(scores)
    )

    veto_findings: list[dict[str, Any]] = []
    accepted_limitations: list[dict[str, Any]] = []
    rerun_required = False
    summaries: list[dict[str, Any]] = []
    for item in ordered:
        objection = item["strongest_objection"]
        rerun_required = rerun_required or objection["rerun_required"]
        summary = {
            "review_id": item["review_id"],
            "reviewer_role": item["reviewer_role"],
            "score": float(item["score"]),
            "confidence": float(item["confidence"]),
            "artifact_locators": item["artifact_locators"],
            "strongest_objection": objection,
        }
        summaries.append(summary)
        if objection["severity"] == "veto":
            veto_findings.append(
                {
                    "review_id": item["review_id"],
                    "reviewer_role": item["reviewer_role"],
                    "summary": objection["summary"],
                    "artifact_locator": objection["artifact_locator"],
                    "rerun_required": objection["rerun_required"],
                }
            )
        for limitation in item["accepted_limitations"]:
            rerun_required = rerun_required or limitation["rerun_required"]
            accepted_limitations.append(
                {
                    "review_id": item["review_id"],
                    "reviewer_role": item["reviewer_role"],
                    **limitation,
                }
            )

    material_disagreement = score_range >= 2.0
    major_objection = any(
        review["strongest_objection"]["severity"] == "major" for review in ordered
    )
    status = (
        "VETO"
        if veto_findings
        else "RERUN_REQUIRED"
        if rerun_required
        else "REVIEW"
        if material_disagreement or major_objection
        else "PASS"
    )
    return {
        "schema_version": 1,
        "report_type": "independent-review-aggregate",
        "status": status,
        "review_count": len(ordered),
        "reviews": summaries,
        "score_summary": {
            "mean": round(mean(scores), 4),
            "confidence_weighted_mean": round(weighted_score, 4),
            "minimum": min(scores),
            "maximum": max(scores),
        },
        "confidence_summary": {
            "mean": round(mean(confidences), 4),
            "minimum": min(confidences),
            "maximum": max(confidences),
        },
        "disagreement": {
            "score_range": score_range,
            "confidence_range": confidence_range,
            "material": material_disagreement,
            "highest_scoring_roles": [
                review["reviewer_role"]
                for review in ordered
                if float(review["score"]) == highest_score
            ],
            "lowest_scoring_roles": [
                review["reviewer_role"]
                for review in ordered
                if float(review["score"]) == lowest_score
            ],
        },
        "veto_findings": veto_findings,
        "accepted_limitations": accepted_limitations,
        "rerun_required": rerun_required,
        "limitations": [
            "This aggregate is an internal diagnostic and does not predict contest outcomes."
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate model, evidence, and writing review JSON files."
    )
    parser.add_argument(
        "--review", action="append", type=Path, required=True, help="review JSON; repeat three times"
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if len(args.review) != 3:
            raise ValueError("exactly three --review files are required.")
        reviews: list[dict[str, Any]] = []
        for path in args.review:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"a review file could not be read as JSON: {exc.__class__.__name__}."
                ) from exc
            if not isinstance(payload, dict):
                raise ValueError("each review file must contain a JSON object.")
            reviews.append(payload)
        result = aggregate_reviews(reviews)
        write_json(args.out, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ValueError as exc:
        failure = {
            "schema_version": 1,
            "report_type": "independent-review-aggregate",
            "status": "FAIL",
            "errors": [str(exc)],
            "limitations": [
                "No outcome or award prediction is produced from invalid review inputs."
            ],
        }
        write_json(args.out, failure)
        print(json.dumps(failure, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
