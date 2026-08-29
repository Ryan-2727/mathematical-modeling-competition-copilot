#!/usr/bin/env python3
"""Verify evidence-triggered reasoning is mapped into the paper naturally."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from contestlib import read_csv_with_error, safe_project_path, sha256_bytes, write_json


COMPLETE = {"verified", "pass", "complete", "accepted"}
TRUE = {"1", "true", "yes", "y"}
MAP_FIELDS = {
    "subproblem",
    "paper_location",
    "modeling_path",
    "modeling_path_evidence",
    "modeling_path_evidence_sha256",
    "model_choice_required",
    "model_choice_location",
    "parameter_location",
    "failed_route_required",
    "failed_route_location",
    "boundary_required",
    "boundary_location",
    "human_reviewer",
    "status",
}
PARAMETER_EVIDENCE_FIELDS = {
    "claim_sensitive",
    "source_class",
    "source_locator",
    "source_sha256",
    "citation_key",
    "calibration_command",
    "sensitivity_evidence",
    "paper_location",
}
DISALLOWED_REVIEWERS = {
    "chatgpt",
    "codex",
    "openai",
    "language model",
    "large language model",
    "ai assistant",
}


def clean(value: Any) -> str:
    return str(value or "").strip()


def complete(row: dict[str, str]) -> bool:
    return clean(row.get("status")).casefold() in COMPLETE


def truthy(value: Any) -> bool:
    return clean(value).casefold() in TRUE


def read_table(
    root: Path,
    relative: str,
    errors: list[str],
    *,
    required: bool,
) -> tuple[list[dict[str, str]], set[str]]:
    path = root / relative
    if not path.is_file():
        if required:
            errors.append(f"required evidence table is missing: {relative}")
        return [], set()
    rows, fields, error = read_csv_with_error(path)
    if error:
        errors.append(f"cannot read {relative}: {error}")
    return rows, fields


def evidence_path(
    root: Path,
    raw: str,
    label: str,
    errors: list[str],
    *,
    expected_sha256: str = "",
) -> Path | None:
    path = safe_project_path(root, clean(raw).replace("\\", "/"))
    if path is None or not path.is_file():
        errors.append(f"{label} must point to an existing project file")
        return None
    expected = clean(expected_sha256).lower()
    if expected and (len(expected) != 64 or sha256_bytes(path) != expected):
        errors.append(f"{label} SHA-256 does not match the recorded evidence")
    return path


def paper_location(root: Path, raw: str, label: str, errors: list[str]) -> bool:
    locator = clean(raw).replace("\\", "/")
    relative = locator.split("#", 1)[0]
    path = safe_project_path(root, relative)
    if (
        path is None
        or not path.is_file()
        or path.suffix.casefold() != ".tex"
        or not relative.startswith("paper/")
    ):
        errors.append(f"{label} must locate an existing LaTeX paper source")
        return False
    return True


def non_placeholder(value: str) -> bool:
    normalized = clean(value).casefold()
    return bool(normalized) and normalized not in {
        "todo",
        "tbd",
        "pending",
        "none",
        "n/a",
        "待补充",
        "待审核",
    }


def validate_parameter(
    root: Path,
    row: dict[str, str],
    bibliography: dict[str, dict[str, str]],
    errors: list[str],
) -> None:
    label = f"parameter {clean(row.get('parameter')) or '<unnamed>'}"
    source_class = clean(row.get("source_class")).casefold()
    if source_class not in {"literature", "data_calibrated", "assumption", "official"}:
        errors.append(f"{label} has unsupported source class {source_class!r}")
        return
    source = evidence_path(
        root,
        clean(row.get("source_locator")),
        f"{label} source",
        errors,
        expected_sha256=clean(row.get("source_sha256")),
    )
    paper_location(root, clean(row.get("paper_location")), f"{label} paper location", errors)
    if source_class == "literature":
        key = clean(row.get("citation_key"))
        cited = bibliography.get(key)
        if not key or cited is None or not complete(cited):
            errors.append(f"{label} needs a verified bibliography citation")
        elif source is not None:
            cited_path = safe_project_path(root, clean(cited.get("source_locator")))
            if cited_path is None or cited_path.resolve() != source.resolve():
                errors.append(f"{label} citation does not bind to its source evidence")
    elif source_class == "data_calibrated":
        if not non_placeholder(clean(row.get("calibration_command"))):
            errors.append(f"{label} needs a reproducible calibration command")
        evidence_path(
            root,
            clean(row.get("sensitivity_evidence")),
            f"{label} sensitivity evidence",
            errors,
        )
    elif source_class == "assumption":
        evidence_path(
            root,
            clean(row.get("sensitivity_evidence")),
            f"{label} sensitivity evidence",
            errors,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--map", default="reports/paper_reasoning_map.csv")
    parser.add_argument("--out", type=Path, default=Path("reports/paper_reasoning_narrative.json"))
    args = parser.parse_args()

    root = args.project_dir.resolve()
    out = args.out if args.out.is_absolute() else root / args.out
    errors: list[str] = []
    warnings: list[str] = []

    maps, map_fields = read_table(root, args.map, errors, required=True)
    decisions, _ = read_table(root, "reports/model_decision_log.csv", errors, required=True)
    parameters, parameter_fields = read_table(
        root, "reports/parameter_registry.csv", errors, required=True
    )
    simplifications, _ = read_table(
        root, "reports/model_simplification_log.csv", errors, required=False
    )
    fallbacks, _ = read_table(root, "reports/fallback_plan.csv", errors, required=False)
    bibliography_rows, _ = read_table(
        root, "reports/bibliography.csv", errors, required=False
    )
    if missing := MAP_FIELDS - map_fields:
        errors.append("paper reasoning map missing fields: " + ", ".join(sorted(missing)))

    active_maps = [row for row in maps if complete(row)]
    map_counts = Counter(clean(row.get("subproblem")) for row in active_maps)
    map_by_subproblem = {
        clean(row.get("subproblem")): row for row in active_maps if clean(row.get("subproblem"))
    }
    bibliography = {
        clean(row.get("citation_key")): row
        for row in bibliography_rows
        if clean(row.get("citation_key"))
    }
    decision_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        if complete(row) and clean(row.get("subproblem")):
            decision_groups[clean(row.get("subproblem"))].append(row)

    claim_parameters = [
        row for row in parameters if complete(row) and truthy(row.get("claim_sensitive"))
    ]
    if claim_parameters and (missing := PARAMETER_EVIDENCE_FIELDS - parameter_fields):
        errors.append("parameter registry missing evidence fields: " + ", ".join(sorted(missing)))
    parameter_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in claim_parameters:
        parameter_groups[clean(row.get("subproblem"))].append(row)
        validate_parameter(root, row, bibliography, errors)

    failed_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in simplifications:
        state = clean(row.get("decision_state")).casefold()
        if complete(row) and clean(row.get("failure_diagnostic")) and state in {
            "failed",
            "simplified",
            "degraded",
        }:
            failed_groups[clean(row.get("subproblem"))].append(row)
            evidence_path(
                root,
                clean(row.get("result_file")),
                "failed route execution evidence",
                errors,
            )
            paper_location(
                root,
                clean(row.get("paper_location")),
                "failed route paper location",
                errors,
            )

    fallback_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in fallbacks:
        if complete(row) and clean(row.get("boundary_statement")):
            fallback_groups[clean(row.get("subproblem"))].append(row)

    subproblems = sorted(
        set(decision_groups)
        | set(parameter_groups)
        | set(failed_groups)
        | set(fallback_groups)
        | set(map_by_subproblem)
    )
    reports: list[dict[str, Any]] = []
    for subproblem in subproblems:
        selected = [row for row in decision_groups[subproblem] if truthy(row.get("selected"))]
        model_choice = len(decision_groups[subproblem]) >= 2 and bool(selected)
        failed_route = bool(failed_groups[subproblem])
        boundary = any(
            clean(row.get("identifiability_status")).casefold() == "conditional"
            for row in parameter_groups[subproblem]
        ) or bool(fallback_groups[subproblem])
        row = map_by_subproblem.get(subproblem)
        if map_counts[subproblem] != 1:
            errors.append(f"{subproblem} needs exactly one verified paper reasoning map row")
        if row is not None:
            paper_location(root, clean(row.get("paper_location")), f"{subproblem} paper location", errors)
            path_text = clean(row.get("modeling_path"))
            if not non_placeholder(path_text) or sum(path_text.count(mark) for mark in ("->", "→")) < 2:
                errors.append(f"{subproblem} modeling path must record at least three concrete stages")
            evidence_path(
                root,
                clean(row.get("modeling_path_evidence")),
                f"{subproblem} modeling path evidence",
                errors,
                expected_sha256=clean(row.get("modeling_path_evidence_sha256")),
            )
            reviewer = clean(row.get("human_reviewer"))
            if not non_placeholder(reviewer) or any(term in reviewer.casefold() for term in DISALLOWED_REVIEWERS):
                errors.append(f"{subproblem} needs a named human reviewer rather than a tool placeholder")
            if model_choice:
                if not truthy(row.get("model_choice_required")):
                    errors.append(f"{subproblem} model choice must be mapped because a credible competitor exists")
                paper_location(
                    root,
                    clean(row.get("model_choice_location")),
                    f"{subproblem} model choice location",
                    errors,
                )
                for item in selected:
                    evidence_path(
                        root,
                        clean(item.get("selection_evidence")),
                        f"{subproblem} model choice evidence",
                        errors,
                    )
            if parameter_groups[subproblem]:
                paper_location(
                    root,
                    clean(row.get("parameter_location")),
                    f"{subproblem} parameter provenance location",
                    errors,
                )
            if failed_route:
                if not truthy(row.get("failed_route_required")):
                    errors.append(f"{subproblem} failed route must be included because execution evidence exists")
                paper_location(
                    root,
                    clean(row.get("failed_route_location")),
                    f"{subproblem} failed route location",
                    errors,
                )
            if boundary:
                if not truthy(row.get("boundary_required")):
                    errors.append(f"{subproblem} boundary narrative is required by conditional evidence")
                paper_location(
                    root,
                    clean(row.get("boundary_location")),
                    f"{subproblem} boundary location",
                    errors,
                )
        reports.append(
            {
                "subproblem": subproblem,
                "model_choice_triggered": model_choice,
                "parameter_provenance_triggered": bool(parameter_groups[subproblem]),
                "failed_route_triggered": failed_route,
                "boundary_triggered": boundary,
            }
        )

    payload = {
        "schema_version": 1,
        "status": "FAIL" if errors else "PASS",
        "scope": "Evidence-triggered reasoning-location audit; it does not require fixed visible headings or infer authorship.",
        "subproblems": reports,
        "errors": errors,
        "warnings": warnings,
    }
    write_json(out, payload)
    print(payload["status"])
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
