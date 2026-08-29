#!/usr/bin/env python3
"""Versioned project migration and deterministic contest workflow orchestration."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CURRENT_PROJECT_SCHEMA_VERSION = 3
REGISTRY_VERSION = 5
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PROFILE_DIR = SKILL_ROOT / "assets" / "contestctl" / "profiles"
VALID_STATUSES = {"PASS", "FAIL", "LIMITED", "SKIPPED"}


@dataclass(frozen=True)
class Node:
    node_id: str
    phase: str
    script: str
    argv: tuple[str, ...]
    dependencies: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]


NODE_REGISTRY = {
    node.node_id: node
    for node in (
        Node(
            "run-problem-selection-kernel-regression",
            "selection",
            "run_model_kernel_regression.py",
            (
                "--backend",
                "stdlib",
                "--out",
                "{project}/reports/kernel-regression-stdlib.json",
            ),
            (),
            (
                "skill://assets/model-library/fixtures/*.json",
                "skill://scripts/model_kernels/*.py",
                "skill://scripts/run_model_kernel_regression.py",
            ),
            ("reports/kernel-regression-stdlib.json",),
        ),
        Node(
            "create-ai-capability-snapshot",
            "selection",
            "create_ai_capability_snapshot.py",
            ("--project-dir", "{project}"),
            ("run-problem-selection-kernel-regression",),
            (
                "reports/kernel-regression-stdlib.json",
                "skill://SKILL.md",
                "skill://assets/problem-selection/ai-capability-profile.json",
                "skill://assets/model-library/cumcm-bc-model-cards.json",
                "skill://scripts/problem_selection_core.py",
            ),
            ("reports/ai_capability_snapshot.json",),
        ),
        Node(
            "recommend-problem-selection",
            "selection",
            "recommend_problem_selection.py",
            ("--project-dir", "{project}"),
            ("create-ai-capability-snapshot",),
            (
                "reports/problem_screening.csv",
                "reports/problem_audition.csv",
                "reports/problem_selection_evidence.csv",
                "reports/problem_audition_weights.json",
                "reports/ai_capability_snapshot.json",
                "reports/problem_selection_calibration.csv",
                "reports/public_award_prior.json",
                "skill://assets/problem-selection/ai-capability-profile.json",
                "skill://scripts/problem_selection_core.py",
            ),
            (
                "reports/problem_selection_recommendation.json",
                "reports/problem_selection_recommendation.md",
            ),
        ),
        Node(
            "generate-paper-artifacts",
            "paper",
            "generate_paper_artifacts.py",
            ("--project-dir", "{project}"),
            (),
            (
                "results/verified_values.csv",
                "results/**/*",
                "reports/conclusion_map.csv",
                "reports/model_decision_log.csv",
                "reports/parameter_registry.csv",
                "reports/independent_routes.csv",
                "reports/result_reconciliation.csv",
                "reports/stress_tests.csv",
                "reports/figure_manifest.csv",
            ),
            ("reports/paper_artifacts_manifest.json",),
        ),
        Node(
            "verify-notation",
            "paper",
            "verify_notation_registry.py",
            ("--project-dir", "{project}"),
            ("generate-paper-artifacts",),
            (
                "reports/notation_registry.csv",
                "paper/**/*.tex",
                "results/verified_values.csv",
            ),
            ("reports/notation_verification.json",),
        ),
        Node(
            "verify-rendered-figures",
            "paper",
            "verify_rendered_figures.py",
            ("--project-dir", "{project}", "--profile", "{profile}"),
            (),
            ("reports/rendered_figure_manifest.csv", "figures/**/*", "paper/figures/**/*"),
            ("reports/rendered_figure_verification.json",),
        ),
        Node(
            "verify-abstract-structure",
            "paper",
            "verify_abstract_structure.py",
            ("--project-dir", "{project}"),
            (),
            ("paper/sections/abstract.tex",),
            ("reports/abstract_structure.json",),
        ),
        Node(
            "verify-chinese-style",
            "paper",
            "verify_chinese_academic_style.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/chinese_academic_style.json",
            ),
            (),
            (
                "contest_manifest.json",
                "paper/**/*.tex",
                "reports/prose_style_exemptions.csv",
            ),
            ("reports/chinese_academic_style.json",),
        ),
        Node(
            "verify-paper-reasoning-narrative",
            "paper",
            "verify_paper_reasoning_narrative.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/paper_reasoning_narrative.json",
            ),
            ("generate-paper-artifacts",),
            (
                "reports/paper_reasoning_map.csv",
                "reports/model_decision_log.csv",
                "reports/parameter_registry.csv",
                "reports/model_simplification_log.csv",
                "reports/fallback_plan.csv",
                "reports/bibliography.csv",
                "reports/traceability.md",
                "results/**/*",
                "paper/**/*.tex",
            ),
            ("reports/paper_reasoning_narrative.json",),
        ),
        Node(
            "verify-answer-density",
            "paper",
            "verify_answer_density.py",
            ("--project-dir", "{project}"),
            (),
            (
                "paper/sections/abstract.tex",
                "paper/sections/conclusion.tex",
                "reports/conclusion_map.csv",
            ),
            ("reports/answer_density.json",),
        ),
        Node(
            "verify-summary-numbers",
            "paper",
            "verify_summary_numeric_traceability.py",
            ("--project-dir", "{project}"),
            ("generate-paper-artifacts",),
            (
                "paper/sections/abstract.tex",
                "paper/sections/conclusion.tex",
                "results/verified_values.csv",
                "reports/numeric_exemptions.csv",
            ),
            ("reports/summary_numeric_traceability.json",),
        ),
        Node(
            "verify-result-story",
            "paper",
            "verify_result_story.py",
            ("--project-dir", "{project}"),
            ("generate-paper-artifacts",),
            (
                "reports/conclusion_map.csv",
                "results/verified_values.csv",
                "reports/model_simplification_log.csv",
                "reports/visual_storyboard.csv",
            ),
            ("reports/result_story.json",),
        ),
        Node(
            "verify-visual-design",
            "paper",
            "verify_visual_design_system.py",
            ("--project-dir", "{project}"),
            ("verify-rendered-figures",),
            ("reports/figure_manifest.csv", "reports/table_manifest.csv"),
            ("reports/visual_design_system.json",),
        ),
        Node(
            "verify-figure-narrative",
            "paper",
            "verify_figure_narrative.py",
            ("--project-dir", "{project}"),
            ("verify-rendered-figures",),
            ("reports/figure_manifest.csv",),
            ("reports/figure_narrative_verification.json",),
        ),
        Node(
            "verify-latex-compatibility",
            "paper",
            "verify_latex_compatibility.py",
            (
                "--paper-dir",
                "{project}/paper",
                "--out",
                "{project}/reports/latex_compatibility.json",
            ),
            ("generate-paper-artifacts",),
            ("paper/**/*.tex", "paper/.latexmkrc", "paper/.vscode/*.json"),
            ("reports/latex_compatibility.json",),
        ),
        Node(
            "verify-bibliography",
            "paper",
            "verify_bibliography_metadata.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/bibliography_verification.json",
            ),
            (),
            (
                "paper/references.bib",
                "reports/bibliography.csv",
                "reports/bibliography_metadata/**/*",
                "reports/source_passages/**/*",
            ),
            ("reports/bibliography_verification.json",),
        ),
        Node(
            "verify-manuscript",
            "paper",
            "verify_manuscript_quality.py",
            (
                "--project-dir",
                "{project}",
                "--fail-on-overfull",
                "--out",
                "{project}/reports/manuscript_quality.json",
            ),
            ("verify-rendered-figures", "generate-paper-artifacts"),
            ("paper/**/*", "reports/figure_manifest.csv"),
            ("reports/manuscript_quality.json",),
        ),
        Node(
            "verify-decision-stability",
            "freeze",
            "verify_decision_stability.py",
            ("--project-dir", "{project}"),
            (),
            ("reports/decision_stability.csv", "reports/conclusion_map.csv"),
            ("reports/decision_stability.json",),
        ),
        Node(
            "verify-figure-contract",
            "freeze",
            "verify_figure_numeric_contract.py",
            ("--project-dir", "{project}"),
            ("verify-rendered-figures",),
            (
                "reports/figure_numeric_contract.csv",
                "reports/figure_manifest.csv",
                "results/verified_values.csv",
            ),
            ("reports/figure_numeric_contract.json",),
        ),
        Node(
            "verify-model-budget",
            "freeze",
            "verify_model_budget.py",
            ("--project-dir", "{project}"),
            (),
            ("reports/model_budget.csv",),
            ("reports/model_budget.json",),
        ),
        Node(
            "verify-model-kernel-evidence",
            "freeze",
            "verify_model_kernel_evidence.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/model_kernel_evidence.json",
            ),
            (),
            (
                "reports/model_kernel_usage.csv",
                "code/**/*",
                "results/**/*",
                "reports/*kernel*regression*.json",
            ),
            ("reports/model_kernel_evidence.json",),
        ),
        Node(
            "verify-compute-budget",
            "freeze",
            "verify_compute_budget.py",
            (
                "--project-dir",
                "{project}",
                "--out",
                "{project}/reports/compute_budget_verification.json",
            ),
            ("verify-model-kernel-evidence",),
            (
                "reports/compute_budget.csv",
                "reports/compute_runs.jsonl",
                "results/**/*",
            ),
            ("reports/compute_budget_verification.json",),
        ),
        Node(
            "verify-three-minute-review",
            "freeze",
            "verify_three_minute_review.py",
            ("--project-dir", "{project}"),
            (
                "verify-abstract-structure",
                "verify-answer-density",
                "verify-rendered-figures",
            ),
            (
                "reports/three_minute_review.csv",
                "reports/figure_manifest.csv",
                "results/verified_values.csv",
                "reports/conclusion_map.csv",
            ),
            ("reports/three_minute_review.json",),
        ),
        Node(
            "verify-latex-lock",
            "freeze",
            "verify_latex_dependency_lock.py",
            ("--project-dir", "{project}"),
            ("verify-latex-compatibility",),
            ("paper/**/*",),
            ("reports/latex_dependency_lock.json",),
        ),
        Node(
            "verify-evidence-chain",
            "freeze",
            "verify_evidence_chain.py",
            ("--project-dir", "{project}"),
            (),
            (
                "reports/evidence_chain.csv",
                "reports/claims.csv",
                "results/verified_values.csv",
            ),
            ("reports/evidence_chain_verification.json",),
        ),
        Node(
            "verify-decision-quality",
            "freeze",
            "verify_decision_quality.py",
            ("--project-dir", "{project}"),
            ("verify-evidence-chain", "verify-decision-stability"),
            (
                "reports/model_decision_log.csv",
                "reports/stress_tests.csv",
                "reports/decision_robustness.csv",
                "reports/implementation_readiness.csv",
                "reports/fallback_plan.csv",
                "reports/causal_claims.csv",
            ),
            ("reports/decision_quality.json",),
        ),
        Node(
            "verify-model-reasoning",
            "freeze",
            "verify_model_reasoning_core.py",
            ("--project-dir", "{project}"),
            (),
            (
                "reports/model_decision_log.csv",
                "reports/parameter_registry.csv",
                "reports/independent_routes.csv",
                "reports/result_reconciliation.csv",
                "reports/joint_inference_design.json",
                "results/verified_values.csv",
            ),
            ("reports/model_reasoning_core.json",),
        ),
        Node(
            "verify-modeling-argument",
            "freeze",
            "verify_modeling_argument_quality.py",
            ("--project-dir", "{project}"),
            ("verify-decision-quality", "verify-model-reasoning"),
            (
                "reports/mechanism_audit.json",
                "reports/semantic_audit.csv",
                "reports/validation_design.csv",
                "reports/conclusion_map.csv",
                "reports/innovation_ledger.csv",
            ),
            ("reports/modeling_argument_quality.json",),
        ),
        Node(
            "verify-submission-md5-lock",
            "freeze",
            "verify_submission_md5_lock.py",
            (
                "--project-dir", "{project}",
                "--ledger", "{project}/reports/submission_md5_lock.json",
                "--out", "{project}/reports/submission_md5_verification.json",
            ),
            (),
            (
                "reports/submission_md5_lock.json",
                "official-submission/**/*",
            ),
            ("reports/submission_md5_verification.json",),
        ),
        Node(
            "verify-official-similarity-risk",
            "freeze",
            "verify_similarity_risk.py",
            (
                "--project-dir", "{project}",
                "--ledger", "{project}/reports/similarity_risk.json",
                "--out", "{project}/reports/similarity_risk_verification.json",
            ),
            (),
            (
                "reports/similarity_risk.json",
                "paper/main.pdf",
            ),
            ("reports/similarity_risk_verification.json",),
        ),
    )
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def migration_plan(root: Path) -> dict[str, Any]:
    manifest_path = root / "contest_manifest.json"
    if not manifest_path.is_file():
        return {
            "status": "FAIL",
            "errors": ["contest_manifest.json is missing"],
            "changes": [],
        }
    try:
        manifest = _load_json(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {"status": "FAIL", "errors": [str(exc)], "changes": []}
    raw_version = manifest.get("project_schema_version", 0)
    if not isinstance(raw_version, int) or raw_version < 0:
        return {
            "status": "FAIL",
            "errors": ["project_schema_version must be a non-negative integer"],
            "changes": [],
        }
    if raw_version > CURRENT_PROJECT_SCHEMA_VERSION:
        return {
            "status": "FAIL",
            "errors": [
                f"project schema {raw_version} is newer than supported "
                f"{CURRENT_PROJECT_SCHEMA_VERSION}"
            ],
            "changes": [],
        }
    additions: tuple[tuple[str, Any], ...] = (
        ("/quality_profile", "standard"),
        ("/workflow", {}),
        ("/workflow/phase", "setup"),
        ("/workflow/optional_tool_policy", "limited_when_unavailable"),
        ("/workflow/generated_dir", "paper/generated"),
    )
    candidate = json.loads(json.dumps(manifest))
    changes: list[dict[str, Any]] = []
    required_files = (
        "reports/parameter_registry.csv",
        "reports/independent_routes.csv",
        "reports/result_reconciliation.csv",
        "reports/joint_inference_design.json",
        "reports/model_kernel_usage.csv",
        "reports/compute_budget.csv",
        "reports/compute_runs.jsonl",
        "reports/prose_style_exemptions.csv",
        "reports/paper_reasoning_map.csv",
        "reports/problem_audition.csv",
        "reports/problem_audition_weights.json",
        "reports/problem_selection.json",
        "reports/problem_screening.csv",
        "reports/problem_selection_evidence.csv",
        "reports/ai_capability_snapshot.json",
        "reports/problem_selection_calibration.csv",
        "reports/public_award_prior.json",
        "reports/problem_selection_recommendation.json",
        "reports/problem_selection_recommendation.md",
    )
    if raw_version < CURRENT_PROJECT_SCHEMA_VERSION:
        candidate["project_schema_version"] = CURRENT_PROJECT_SCHEMA_VERSION
        changes.append(
            {
                "op": "add" if "project_schema_version" not in manifest else "replace",
                "path": "/project_schema_version",
                "value": CURRENT_PROJECT_SCHEMA_VERSION,
            }
        )
    for pointer, value in additions:
        parts = pointer.strip("/").split("/")
        target = candidate
        for part in parts[:-1]:
            current = target.get(part)
            if current is None:
                target[part] = {}
            elif not isinstance(current, dict):
                return {
                    "status": "FAIL",
                    "errors": [f"{'/'.join(parts[:-1])} must be an object"],
                    "changes": [],
                }
            target = target[part]
        key = parts[-1]
        if key not in target:
            target[key] = value
            changes.append({"op": "add", "path": pointer, "value": value})
    for relative in required_files:
        if not (root / relative).exists():
            changes.append({"op": "create_file", "path": relative})
    return {
        "status": "PASS",
        "errors": [],
        "old_version": raw_version,
        "new_version": CURRENT_PROJECT_SCHEMA_VERSION,
        "changes": changes,
        "manifest": candidate,
    }


def migrate_project(root: Path, apply: bool, out: Path) -> dict[str, Any]:
    payload = migration_plan(root)
    payload["applied"] = False
    if payload["status"] == "PASS" and apply:
        manifest = payload.pop("manifest")
        templates = {
            "reports/parameter_registry.csv": "subproblem,model_id,parameter,symbol,role,unit,scope,source,bounds,identifiability_status,claim_boundary,status,claim_sensitive,source_class,source_locator,source_sha256,citation_key,calibration_command,sensitivity_evidence,paper_location\n",
            "reports/paper_reasoning_map.csv": "subproblem,paper_location,modeling_path,modeling_path_evidence,modeling_path_evidence_sha256,model_choice_required,model_choice_location,parameter_location,failed_route_required,failed_route_location,boundary_required,boundary_location,human_reviewer,status\n",
            "reports/independent_routes.csv": "subproblem,route_id,route_role,principle,data_representation,failure_mode,result_file,result_value,tolerance,comparison_status,limitation,status\n",
            "reports/result_reconciliation.csv": "subproblem,comparison_id,primary_route,comparison_route,primary_value,comparison_value,tolerance,disagreement_material,investigation_step,cause,resolution,claim_action,evidence_file,status\n",
            "reports/joint_inference_design.json": '{\n  "applicable": false,\n  "reason": "migration requires an applicability decision",\n  "subproblems": []\n}\n',
            "reports/model_kernel_usage.csv": "model_id,card_id,kernel_id,used,backend,input_file,input_sha256,output_file,output_sha256,synthetic_regression_report,synthetic_regression_sha256,adaptation_note,status\n",
            "reports/compute_budget.csv": "model_id,selected,primary_run_ids,fallback_run_id,required_scale_count,single_scale_reason,remaining_time_seconds,solver_gap_required,status\n",
            "reports/compute_runs.jsonl": "",
            "reports/prose_style_exemptions.csv": "finding_sha256,rule,source_file,line,reason,reviewer,status\n",
            "reports/problem_audition.csv": (
                "problem_id,attachment_status,attachment_evidence,attachment_parse_command,"
                "baseline_command,baseline_result,baseline_elapsed_hours,paper_figure,"
                "subproblem_closure_evidence,fallback_route,fallback_evidence,"
                "subproblem_closure_risk,result_verifiability,upgrade_headroom,team_fit,"
                "writing_visual_potential,fatal_risk,score,status\n"
            ),
            "reports/problem_audition_weights.json": (
                '{\n  "schema_version": 1,\n  "minimum_selected_win_rate": 0.75,\n'
                '  "recorded_score_tolerance": 1.0,\n  "base_weights": {\n'
                '    "subproblem_closure_risk": 0.30, "result_verifiability": 0.25,\n'
                '    "upgrade_headroom": 0.15, "team_fit": 0.20,\n'
                '    "writing_visual_potential": 0.10\n  },\n  "sensitivity_scenarios": [\n'
                '    {"name": "closure_first", "weights": {"subproblem_closure_risk": 0.45, "result_verifiability": 0.20, "upgrade_headroom": 0.10, "team_fit": 0.15, "writing_visual_potential": 0.10}},\n'
                '    {"name": "evidence_first", "weights": {"subproblem_closure_risk": 0.20, "result_verifiability": 0.40, "upgrade_headroom": 0.10, "team_fit": 0.20, "writing_visual_potential": 0.10}}\n'
                '  ]\n}\n'
            ),
            "reports/problem_selection.json": (
                '{\n  "schema_version": 2,\n  "selected_problem": "",\n'
                '  "confirmed_problem": "",\n  "selection_hour": null,\n  "rationale": "",\n'
                '  "recommendation_file": "reports/problem_selection_recommendation.json",\n'
                '  "recommendation_sha256": "",\n  "recommendation_generated_at_utc": null,\n'
                '  "recommendation_input_hashes": {},\n  "confirmation": null,\n'
                '  "selection_override": null,\n  "override": null\n}\n'
            ),
            "reports/problem_screening.csv": (
                "problem_id,screening_minutes,micro_baseline_minutes,preliminary_score,"
                "deep_trial_selected,elimination_reason,deep_trial_budget_minutes,"
                "deep_trial_elapsed_minutes,task_families,"
                "required_model_families,attachment_state,semantic_risk,expected_deliverables,"
                "evidence_locator,evidence_sha256,early_failure_type,timing_exception,status\n"
                "A,15,30,,,,0,0,,,,,,,,,,pending\n"
                "B,15,30,,,,0,0,,,,,,,,,,pending\n"
                "C,15,30,,,,0,0,,,,,,,,,,pending\n"
            ),
            "reports/problem_selection_evidence.csv": (
                "problem_id,criterion,rating,evidence_locator,evidence_sha256,"
                "observation_type,observation,status\n"
            ),
            "reports/ai_capability_snapshot.json": (
                '{\n  "schema_version": 1,\n  "status": "pending",\n'
                '  "valid_for_calibration": false,\n  "errors": [],\n  "warnings": []\n}\n'
            ),
            "reports/problem_selection_calibration.csv": (
                "case_id,year,task_family_tags,ai_profile_version,closure_result_rating,"
                "result_verifiability_rating,ai_capability_fit_rating,data_semantics_rating,"
                "compute_fallback_rating,paper_figure_rating,innovation_rating,composite_score,"
                "selected_problem_type,award_label,evidence_sha256,status\n"
            ),
            "reports/public_award_prior.json": (
                '{\n  "schema_version": 1,\n  "status": "pending",\n  "source_url": "",\n'
                '  "source_snapshot": "",\n  "source_sha256": "",\n  "retrieved_at": null,\n'
                '  "competition_scope": "CUMCM",\n  "applicable_years": [],\n'
                '  "applies_to_problem_types": ["A", "B", "C"],\n'
                '  "population_definition": "",\n  "denominator_definition": "",\n'
                '  "outcome_definition": "mutually_exclusive_highest_award",\n'
                '  "category_counts": {"national_first": 0, "national_second": 0, '
                '"provincial_award": 0, "no_award": 0},\n  "effective_strength": 8,\n'
                '  "reviewer_status": "pending"\n}\n'
            ),
            "reports/problem_selection_recommendation.json": (
                '{\n  "schema_version": 1,\n  "status": "pending",\n  "errors": [],\n  "warnings": []\n}\n'
            ),
            "reports/problem_selection_recommendation.md": (
                "# CUMCM A/B/C 选题推荐\n\n待完成三题筛选、可执行试跑与本地证据绑定后生成。\n"
            ),
        }
        created: list[str] = []
        for relative, content in templates.items():
            target = root / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                created.append(relative)
        _write_json(root / "contest_manifest.json", manifest)
        payload["created_files"] = created
        payload["applied"] = True
    else:
        payload.pop("manifest", None)
    _write_json(out, payload)
    return payload


def validate_registry() -> None:
    outputs: dict[str, str] = {}
    for node_id, node in NODE_REGISTRY.items():
        if node.phase not in {"selection", "paper", "freeze"}:
            raise ValueError(f"workflow node {node_id!r} has an invalid phase")
        if not (SCRIPT_DIR / node.script).is_file():
            raise ValueError(f"workflow node {node_id!r} script is missing")
        for dependency in node.dependencies:
            if dependency not in NODE_REGISTRY:
                raise ValueError(
                    f"workflow node {node_id!r} has unknown dependency {dependency!r}"
                )
        for output in node.outputs:
            owner = outputs.setdefault(output, node_id)
            if owner != node_id:
                raise ValueError(
                    f"workflow output {output!r} is declared by {owner!r} and {node_id!r}"
                )
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            raise ValueError(f"workflow dependency cycle includes {node_id!r}")
        visiting.add(node_id)
        for dependency in NODE_REGISTRY[node_id].dependencies:
            visit(dependency)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in NODE_REGISTRY:
        visit(node_id)


def load_profile(name: str, custom_path: Path | None = None) -> dict[str, Any]:
    validate_registry()
    if name == "custom":
        if custom_path is None:
            raise ValueError("custom profile requires --profile-file")
        path = custom_path
    else:
        if custom_path is not None:
            raise ValueError("--profile-file is only valid with --profile custom")
        path = PROFILE_DIR / f"{name}.json"
    payload = _load_json(path)
    if payload.get("name") != name:
        raise ValueError(f"profile name must be {name!r}")
    phases = payload.get("phases")
    if not isinstance(phases, dict):
        raise ValueError("profile phases must be an object")
    for phase, nodes in phases.items():
        if phase not in {"selection", "paper", "freeze"} or not isinstance(nodes, list):
            raise ValueError(f"invalid profile phase {phase!r}")
        for node_id in nodes:
            if node_id not in NODE_REGISTRY:
                raise ValueError(f"unknown workflow node {node_id!r}")
            if NODE_REGISTRY[node_id].phase != phase:
                raise ValueError(
                    f"workflow node {node_id!r} belongs to "
                    f"{NODE_REGISTRY[node_id].phase!r}, not {phase!r}"
                )
    return payload


def resolve_nodes(profile: dict[str, Any], phase: str) -> list[str]:
    selected: set[str] = set()

    def include(node_id: str) -> None:
        if node_id in selected:
            return
        node = NODE_REGISTRY[node_id]
        for dependency in node.dependencies:
            include(dependency)
        selected.add(node_id)

    if phase == "selection":
        phases = ("selection",)
    elif phase == "paper":
        phases = ("paper",)
    elif phase == "freeze":
        phases = ("paper", "freeze")
    else:
        raise ValueError(f"invalid workflow phase {phase!r}")
    for current in phases:
        for node_id in profile["phases"].get(current, []):
            include(str(node_id))
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            raise ValueError(f"workflow dependency cycle includes {node_id}")
        visiting.add(node_id)
        for dependency in NODE_REGISTRY[node_id].dependencies:
            if dependency in selected:
                visit(dependency)
        visiting.remove(node_id)
        visited.add(node_id)
        order.append(node_id)

    for node_id in sorted(selected):
        visit(node_id)
    return order


def _expanded_inputs(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        if pattern.startswith("skill://"):
            matches = list(SKILL_ROOT.glob(pattern[len("skill://") :]))
            missing = SKILL_ROOT / pattern[len("skill://") :]
        else:
            matches = list(root.glob(pattern))
            missing = root / pattern
        if not matches:
            paths.add(missing)
        else:
            paths.update(item for item in matches if item.is_file())
    return sorted(paths, key=lambda item: item.as_posix())


def _digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def node_signature(
    root: Path,
    node: Node,
    profile_name: str,
    dependency_records: list[dict[str, Any]],
) -> str:
    payload: dict[str, Any] = {
        "registry_version": REGISTRY_VERSION,
        "node": node.node_id,
        "profile": profile_name,
        "argv": node.argv,
        "script_sha256": _digest_file(SCRIPT_DIR / node.script),
        "dependencies": [
            {
                "node": item["node"],
                "status": (
                    "PASS"
                    if item["status"] == "SKIPPED"
                    and item.get("reason") == "unchanged passing inputs and outputs"
                    else item["status"]
                ),
                "output_hashes": item.get("output_hashes", {}),
            }
            for item in dependency_records
        ],
        "inputs": [],
    }
    for path in _expanded_inputs(root, node.inputs):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = str(path)
        payload["inputs"].append(
            {
                "path": relative,
                "sha256": _digest_file(path) if path.is_file() else None,
            }
        )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _output_hashes(root: Path, node: Node) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in node.outputs:
        path = root / relative
        if path.is_file():
            hashes[relative] = _digest_file(path)
    return hashes


def _read_cache(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"registry_version": REGISTRY_VERSION, "nodes": {}}
    try:
        payload = _load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {"registry_version": REGISTRY_VERSION, "nodes": {}}
    if payload.get("registry_version") != REGISTRY_VERSION:
        return {"registry_version": REGISTRY_VERSION, "nodes": {}}
    if not isinstance(payload.get("nodes"), dict):
        payload["nodes"] = {}
    return payload


def _cache_hit(
    root: Path, node: Node, cached: dict[str, Any] | None, signature: str
) -> bool:
    if not isinstance(cached, dict):
        return False
    if cached.get("signature") != signature or cached.get("status") != "PASS":
        return False
    return cached.get("output_hashes") == _output_hashes(root, node) and len(
        cached.get("output_hashes") or {}
    ) == len(node.outputs)


def run_workflow(
    root: Path,
    phase: str,
    profile_name: str,
    custom_profile: Path | None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    profile = load_profile(profile_name, custom_profile)
    if profile_name == "strict":
        try:
            manifest = _load_json(root / "contest_manifest.json")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            manifest = {}
        if manifest.get("submission_profile") == "cumcm-2026":
            profile["phases"]["freeze"].extend(
                ("verify-submission-md5-lock", "verify-official-similarity-risk")
            )
    node_ids = resolve_nodes(profile, phase)
    cache_path = root / "reports" / "workflow_cache.json"
    cache = _read_cache(cache_path)
    records: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for node_id in node_ids:
        node = NODE_REGISTRY[node_id]
        dependencies = [by_id[item] for item in node.dependencies if item in by_id]
        blocked = [
            item["node"]
            for item in dependencies
            if item["status"] == "FAIL"
            or (
                item["status"] == "SKIPPED"
                and item.get("reason") != "unchanged passing inputs and outputs"
            )
        ]
        if blocked:
            record = {
                "node": node_id,
                "phase": node.phase,
                "status": "SKIPPED",
                "reason": f"failed dependencies: {', '.join(blocked)}",
                "returncode": None,
                "output_hashes": {},
            }
            records.append(record)
            by_id[node_id] = record
            continue
        signature = node_signature(root, node, profile_name, dependencies)
        cached = cache["nodes"].get(node_id)
        if not force and _cache_hit(root, node, cached, signature):
            record = {
                "node": node_id,
                "phase": node.phase,
                "status": "SKIPPED",
                "reason": "unchanged passing inputs and outputs",
                "returncode": None,
                "signature": signature,
                "output_hashes": cached["output_hashes"],
            }
            records.append(record)
            by_id[node_id] = record
            continue
        argv = [
            value.format(project=str(root), profile=profile_name)
            for value in node.argv
        ]
        command = [sys.executable, str(SCRIPT_DIR / node.script), *argv]
        if dry_run:
            status, returncode, stdout, stderr = "SKIPPED", None, "", ""
            reason = "dry run"
        elif not (SCRIPT_DIR / node.script).is_file():
            status, returncode, stdout, stderr = (
                "FAIL",
                1,
                "",
                f"missing script: {node.script}",
            )
            reason = "missing script"
        else:
            completed = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            returncode = completed.returncode
            stdout = completed.stdout[-4000:]
            stderr = completed.stderr[-4000:]
            status = {0: "PASS", 2: "LIMITED"}.get(returncode, "FAIL")
            reason = ""
        output_hashes = _output_hashes(root, node)
        if not dry_run and status in {"PASS", "LIMITED"} and len(output_hashes) != len(
            node.outputs
        ):
            status = "FAIL"
            reason = "command did not create every declared output"
        record = {
            "node": node_id,
            "phase": node.phase,
            "status": status,
            "reason": reason,
            "returncode": returncode,
            "command": command,
            "signature": signature,
            "output_hashes": output_hashes,
            "stdout": stdout,
            "stderr": stderr,
        }
        records.append(record)
        by_id[node_id] = record
        if not dry_run:
            cache["nodes"][node_id] = {
                "signature": signature,
                "status": status,
                "output_hashes": output_hashes,
            }
    if not dry_run:
        _write_json(cache_path, cache)
    failed = [item["node"] for item in records if item["status"] == "FAIL"]
    limited = [item["node"] for item in records if item["status"] == "LIMITED"]
    status = "FAIL" if failed else ("LIMITED" if limited else "PASS")
    return {
        "status": status,
        "phase": phase,
        "profile": profile_name,
        "registry_version": REGISTRY_VERSION,
        "dry_run": dry_run,
        "nodes": records,
        "errors": [f"{item} failed" for item in failed],
        "warnings": [f"{item} is LIMITED" for item in limited],
    }


def doctor_project(root: Path, profile_name: str) -> dict[str, Any]:
    tools = {
        name: shutil.which(name)
        for name in ("latexmk", "xelatex", "pdftoppm", "pdftotext")
    }
    modules = {
        name: importlib.util.find_spec(name) is not None
        for name in ("PIL",)
    }
    plan = migration_plan(root)
    missing = [name for name, path in tools.items() if path is None]
    missing.extend(name for name, present in modules.items() if not present)
    errors: list[str] = []
    warnings: list[str] = []
    try:
        load_profile(profile_name)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"profile/registry error: {exc}")
    if plan["status"] == "FAIL":
        errors.extend(plan["errors"])
    elif plan["changes"]:
        warnings.append("project schema migration is available")
    if profile_name == "strict" and missing:
        errors.append("strict profile missing optional tools: " + ", ".join(missing))
    elif profile_name != "minimal" and missing:
        warnings.append("optional tools unavailable: " + ", ".join(missing))
    status = "FAIL" if errors else ("LIMITED" if warnings else "PASS")
    return {
        "status": status,
        "profile": profile_name,
        "python": sys.version,
        "project_schema_supported": CURRENT_PROJECT_SCHEMA_VERSION,
        "migration_changes": plan.get("changes", []),
        "tools": tools,
        "python_modules": modules,
        "errors": errors,
        "warnings": warnings,
    }


def summarize_run(payload: dict[str, Any]) -> dict[str, Any]:
    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    for item in payload.get("nodes", []):
        status = str(item.get("status") or "").upper()
        if status in counts:
            counts[status] += 1
    return {
        "status": payload.get("status", "FAIL"),
        "phase": payload.get("phase"),
        "profile": payload.get("profile"),
        "counts": counts,
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
    }
