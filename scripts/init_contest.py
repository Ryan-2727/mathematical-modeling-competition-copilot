#!/usr/bin/env python3
"""Create contest-mode manifests and audit templates without fetching the web."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from contest_profile import load_contest_profile
from scaffold_latex_paper import paper_files, scaffold_latex_paper


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def contest_defaults(contest: str, year: int) -> tuple[str, str]:
    normalized = "".join(character for character in contest.lower() if character.isalnum())
    if normalized in {"mcm", "icm", "mcmicm", "comap"}:
        return "mcm-icm", "mcm-icm-current"
    if normalized in {"cumcm", "高教社杯", "全国大学生数学建模竞赛"}:
        return "cumcm", f"cumcm-{year}"
    return "cumcm", "generic"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--contest", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--mode", choices=["training", "live", "posthoc"], required=True)
    parser.add_argument("--rules-url", action="append", default=[])
    parser.add_argument("--deadline", default="unknown")
    parser.add_argument("--template", choices=["auto", "cumcm", "mcm-icm"], default="auto")
    parser.add_argument("--submission-profile")
    args = parser.parse_args()
    default_template, default_profile = contest_defaults(args.contest, args.year)
    selected_template = default_template if args.template == "auto" else args.template
    selected_profile = args.submission_profile or default_profile
    is_cumcm_2026 = selected_profile == "cumcm-2026"
    cumcm_2026 = load_contest_profile("cumcm-2026") if is_cumcm_2026 else None
    root = args.project_dir
    for name in (
        "data/raw",
        "data/processed",
        "code",
        "results",
        "figures",
        "paper",
        "paper/generated",
        "reports",
        "reports/bibliography_metadata",
        "reports/figure_previews",
        "reports/source_passages",
        "support",
        "environment",
        "delivery",
        "official-submission",
    ):
        (root / name).mkdir(parents=True, exist_ok=True)
    if paper_files(root / "paper"):
        write_if_missing(root / "paper" / "references.bib", "")
    else:
        scaffold_latex_paper(root, template=selected_template)
    manifest = {
        "project_schema_version": 1,
        "contest": args.contest,
        "year": args.year,
        "mode": args.mode,
        "deadline": args.deadline,
        "rules_urls": args.rules_url,
        "rules_verified_at": None,
        "rules_snapshot_file": "reports/contest_rules_snapshot.md",
        "rules_lock_file": "rules.lock.json",
        "submission_profile": selected_profile,
        "ai_mode": None if is_cumcm_2026 else "not_applicable",
        "contest_duration_hours": cumcm_2026["contest_duration_hours"] if cumcm_2026 else None,
        "quality_profile": "standard",
        "workflow": {
            "phase": "setup",
            "optional_tool_policy": "limited_when_unavailable",
            "generated_dir": "paper/generated",
        },
        "latex_template": selected_template,
        "live_mode_policy": "static-authoritative-sources-only" if args.mode == "live" else "not-applicable",
        "online_action_policy": "local-work-only; search allowed; ask user when privacy is ambiguous",
        "submission_state": "draft",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_if_missing(
        root / "contest_manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    write_if_missing(
        root / "rules.lock.json",
        json.dumps(
            {
                "schema_version": 2,
                "contest": args.contest,
                "year": args.year,
                "profile": selected_profile,
                "created_at_utc": manifest["created_at_utc"],
                "valid_through": None,
                "sources": [],
                "rules": {},
                "status": "unverified",
                **(
                    {
                        "freshness_checkpoints": cumcm_2026["freshness_checkpoints"]
                    }
                    if is_cumcm_2026
                    else {}
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_if_missing(
        root / "plan.md",
        "# Contest plan\n\nRecord the selected problem, subproblem decomposition, model routes, evidence plan, owners, deadlines, and stop-loss decisions.\n",
    )
    write_if_missing(
        root / "todo.md",
        "# Contest tasks\n\n- [ ] Verify and lock current official rules\n- [ ] Complete data audit and subproblem map\n- [ ] Run baseline models and validations\n- [ ] Freeze figures, tables, and verified values\n- [ ] Compile and verify the paper\n- [ ] Prepare separate delivery and official-submission artifacts\n",
    )
    write_if_missing(root / "reports/contest_rules_snapshot.md", "# Contest rules snapshot\n\nRecord the official source, access time, rule version, selected profile, page limit, AI policy, submission method, deadline/time zone, and unresolved items. Do not mark this file verified until every field is checked.\n")
    write_if_missing(root / "reports/data_audit.md", "# Data audit\n\n| Dataset | Source | License/permission | Rows/columns | Units | Missing/outlier handling | Leakage risk | Hash |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    write_if_missing(root / "reports/traceability.md", "# Traceability\n\n| Subproblem | Data | Model | Validation | Result file | Figure/table | Paper section | Status |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    write_if_missing(root / "reports/claims.csv", "claim_id,subproblem,claim,source_file,source_locator,command,figure_or_table,paper_location,human_verification,status\n")
    write_if_missing(root / "reports/evidence_chain.csv", "claim_id,code_or_command,source_data,data_sha256,result_file,result_sha256,verified_value_key,latex_macro,figure_label,paper_location,status\n")
    write_if_missing(
        root / "results/verified_values.csv",
        "key,value,value_type,unit,source_file,source_sha256,source_locator,source_kind,justification\n",
    )
    write_if_missing(
        root / "reports/model_validation.json",
        '{\n  "models": []\n}\n',
    )
    write_if_missing(root / "reports/argument_coverage.csv", "subproblem,need_or_mechanism,model,solution,quantified_result,interpretation,validation,status\n")
    write_if_missing(
        root / "reports/paper_depth_plan.csv",
        "section,role,planned_pages,actual_pages,required_content,evidence,status\n"
        "摘要,abstract,1,,逐题方法、关键结果、验证和结论,,pending\n"
        "问题重述,restatement,1,,输入、约束、输出和任务边界,,pending\n"
        "问题分析,analysis,2,,逐题机理、方法理由、依赖关系和验证计划,,pending\n"
        "模型假设与符号,assumptions_notation,1,,仅保留后文实际使用的假设与符号,,pending\n"
        "问题一,subproblem,,,机理、方法理由、变量、推导、算法、结果解释、局部验证,,pending\n"
        "综合检验,validation,2,,误差、独立复核、敏感性、鲁棒性或失效边界,,pending\n"
        "结论与评价,conclusion,1,,逐题直接回答、优缺点和可实施改进,,pending\n"
        "参考文献,references,1,,正文实际引用且已核验的文献,,pending\n",
    )
    write_if_missing(
        root / "reports/bibliography.csv",
        "citation_key,title,authors,year,venue,doi_or_url,verification_source,"
        "verified_at,scholar_query,scholar_checked_at,scholar_status,"
        "metadata_snapshot,metadata_sha256,retraction_status,retraction_checked_at,"
        "claim_supported,source_locator,supporting_passage,"
        "supporting_passage_sha256,status\n",
    )
    write_if_missing(
        root / "reports/figure_manifest.csv",
        "figure,label,source_data,caption_insight,axes_units,color_accessibility,claim_id,question_answered,reader_takeaway,decision_relevance,visual_role,style_profile,palette_or_grayscale,typography_precision,panel_order,legibility_evidence,status\n",
    )
    write_if_missing(
        root / "reports/rendered_figure_manifest.csv",
        "figure,figure_sha256,source_data,source_sha256,generator_command_id,"
        "insertion_width_cm,insertion_height_cm,min_text_pt,min_line_pt,"
        "clipping_check,overlap_check,axis_crowding_check,panel_order,"
        "panel_spacing,visual_hierarchy,grayscale_check,colorblind_check,"
        "supported_conclusion,evidence_location,paper_page,status\n",
    )
    write_if_missing(
        root / "reports/table_manifest.csv",
        "table,label,source_data,caption_insight,units,precision,emphasis,continuation_check,claim_id,question_answered,reader_takeaway,decision_relevance,style_profile,legibility_evidence,status\n",
    )
    write_if_missing(root / "reports/model_decision_log.csv", "subproblem,baseline,candidate,mechanism_fit,assumptions,failure_test,validation_cost,selected,selection_evidence,status\n")
    write_if_missing(root / "reports/semantic_audit.csv", "semantic_id,dataset,field,raw_representation,semantic_type,decision_impact,evidence,alternative_treatment,sensitivity_needed,used_by,status\n")
    write_if_missing(root / "reports/mechanism_audit.json", '{\n  "status": "pending",\n  "subproblems": []\n}\n')
    write_if_missing(root / "reports/validation_design.csv", "subproblem,truth_availability,validation_strategy,independent_checks,primary_metric,baseline_or_invariant,split_or_scenario,acceptance_criterion,limitation,result_file,status\n")
    write_if_missing(root / "reports/conclusion_map.csv", "subproblem,question,answer_or_recommendation,decisive_value_key,method_rationale_location,validation_location,limitation_location,figure_or_table,paper_location,status\n")
    write_if_missing(root / "reports/innovation_ledger.csv", "subproblem,baseline,problem_specific_change,mechanism_target,added_assumption,incremental_cost,comparison_metric,baseline_value,innovation_value,metric_direction,predeclared_minimum_improvement,relative_improvement,validation_artifact,claim_boundary,status\n")
    write_if_missing(root / "reports/model_challenge.json", '{\n  "status": "pending",\n  "subproblems": [],\n  "errors": []\n}\n')
    write_if_missing(root / "reports/model_simplification_log.csv", "subproblem,primary_route,failure_diagnostic,decision_state,retained_core_factors,removed_noncritical_factors,simplified_route,user_authorization,original_model_treatment,result_file,paper_location,status\n")
    write_if_missing(root / "reports/visual_storyboard.csv", "artifact_id,artifact_type,subproblem,question,claim_id,source_result,selection_rationale,paper_location,status\n")
    write_if_missing(root / "reports/decision_stability.csv", "decision_id,subproblem,baseline_recommendation,perturbation_id,perturbation,perturbed_recommendation,recommendation_changed,materiality,conditional_conclusion,limitation_location,result_file,paper_location,status\n")
    write_if_missing(root / "reports/figure_numeric_contract.csv", "figure,label,source_data,data_sha256,axis_x,axis_y,axis_scale,x_limits,y_limits,value_transform,decisive_value_keys,paper_location,status\n")
    write_if_missing(root / "reports/model_budget.csv", "subproblem,route_name,route_type,selected,estimated_hours,risk_level,validation_hours,fallback_route,expected_value,deadline_hours,status\n")
    write_if_missing(
        root / "reports/problem_audition.csv",
        "problem_id,attachment_status,attachment_evidence,baseline_command,baseline_result,"
        "subproblem_closure_risk,result_verifiability,upgrade_headroom,team_fit,"
        "writing_visual_potential,fatal_risk,score,status\n",
    )
    write_if_missing(
        root / "reports/problem_selection.json",
        '{\n  "selected_problem": "",\n  "selection_hour": null,\n  "rationale": "",\n  "override": null\n}\n',
    )
    write_if_missing(
        root / "reports/training_runs.csv",
        "run_id,rehearsal_hours,selection_lock_hour,first_verified_result_hour,"
        "all_subproblem_results_hour,full_draft_hour,strict_freeze_hour,"
        "submission_rehearsal,unresolved_vetoes,status\n",
    )
    write_if_missing(
        root / "reports/training_defects.csv",
        "run_id,defect_class,severity,evidence,resolution_status\n",
    )
    write_if_missing(
        root / "reports/online_actions.csv",
        "action_id,mode,action_type,purpose,destination,"
        "contains_current_contest_material,privacy_ambiguity,user_decision,evidence,status\n",
    )
    write_if_missing(root / "reports/three_minute_review.csv", "element,reader_question,direct_answer,evidence_type,evidence_ref,paper_location,status\n")
    write_if_missing(root / "reports/decision_robustness.csv", "decision_id,uncertainty_material,comparison_type,scenario_count,expected_value,worst_case_value,extreme_feasibility_rate,policy_changed,interpretation,status\n")
    write_if_missing(root / "reports/implementation_readiness.csv", "decision_id,implementation_steps,required_inputs,execution_cost,execution_time,interpretability,extreme_feasibility_rate,failure_mode,contingency,paper_location,status\n")
    write_if_missing(root / "reports/fallback_plan.csv", "subproblem,model_family,failure_mode,trigger,primary_route,fallback_route,boundary_statement,result_file,paper_location,status\n")
    write_if_missing(root / "reports/causal_claims.csv", "claim_id,claim_type,estimand,causal_graph,confounders,counterfactual,identification_strategy,diagnostic,limitation,paper_location,status\n")
    write_if_missing(root / "reports/page_readability_checklist.csv", "page,abstract_density,formula_first_definition,figure_legibility,blank_space,table_break,appendix_boundary,reference_consistency,reviewer,status\n")
    write_if_missing(root / "reports/presentation_checklist.csv", "page,hierarchy,font_readability,orphaned_headings_captions,formula_breaks,table_continuity,whitespace_balance,visual_consistency,reviewer,status\n")
    write_if_missing(root / "reports/stress_tests.csv", "claim_id,subproblem,stress_type,change,acceptance_criterion,result_file,outcome,verdict,status\n")
    write_if_missing(root / "reports/units.csv", "symbol,meaning,unit,source,conversion,range_check,status\n")
    write_if_missing(
        root / "reports/notation_registry.csv",
        "symbol,canonical_tex,meaning,kind,unit,first_definition,code_names,"
        "figure_labels,appendix_location,equation_ids,status\n",
    )
    write_if_missing(
        root / "reports/equation_dimensions.csv",
        "equation_id,left_dimension,right_dimension,notation_symbols,evidence,status\n",
    )
    write_if_missing(
        root / "reports/reviewer_scorecard.csv",
        "dimension,score_1_to_5,evidence,major_objection,smallest_fix,status\n"
        "assumption_rationality,,,,,pending\n"
        "model_creativity,,,,,pending\n"
        "result_correctness,,,,,pending\n"
        "writing_clarity,,,,,pending\n",
    )
    if is_cumcm_2026:
        milestones = (
            "milestone,hour,deliverable,owner,gate,status\n"
            "scope-lock,2,rules roles and candidate criteria,unassigned,scope agreed,pending\n"
            "selection-lock,6,verified problem audition and selected problem,unassigned,H6 selection verified,pending\n"
            "baseline-run,24,all subproblems have baseline results,unassigned,results executable,pending\n"
            "model-lock,42,primary comparison and validation frozen,unassigned,claims survive challenge,pending\n"
            "figure-lock,54,stress tests figures and tables frozen,unassigned,numbers traceable,pending\n"
            "draft-lock,64,complete paper and support draft,unassigned,no missing section,pending\n"
            "review-lock,70,independent review and strict checks,unassigned,vetoes resolved,pending\n"
            "submission-rehearsal,72,hash AI branch and package rehearsal,unassigned,local checks pass,pending\n"
            "receipt-lock,74,manual official submission and receipt evidence,unassigned,submission verified,pending\n"
        )
    else:
        milestones = (
            "milestone,hour,deliverable,owner,gate,status\n"
            "scope-lock,3,problem split and compliance snapshot,unassigned,scope agreed,pending\n"
            "data-lock,8,data audit and baseline plan,unassigned,data usable,pending\n"
            "route-lock,12,model decision log,unassigned,primary route selected,pending\n"
            "baseline-run,30,complete baseline results,unassigned,all subproblems answered,pending\n"
            "validation-lock,42,diagnostics and stress tests,unassigned,decisive claims tested,pending\n"
            "figure-lock,54,final figures and tables,unassigned,all numbers traceable,pending\n"
            "draft-lock,60,complete paper draft,unassigned,no missing section,pending\n"
            "review-lock,66,independent consistency review,unassigned,major objections resolved,pending\n"
            "submission-build,70,final anonymous submission files,unassigned,profile checks pass,pending\n"
            "receipt-lock,72,hashes and receipt evidence,unassigned,submission verified,pending\n"
        )
    write_if_missing(root / "reports/milestones.csv", milestones)
    write_if_missing(root / "reports/ai_usage_log.jsonl", "")
    write_if_missing(root / "reports/verification_report.md", "# Verification report\n\n## Submission state\n\ndraft\n\n## Checks\n\n| Check | Status | Evidence |\n| --- | --- | --- |\n")
    write_if_missing(
        root / "support/README.md",
        "# Support materials\n\nDocument the environment, dependency installation, data provenance, exact reproduction commands, expected outputs, and the relationship between code, results, figures, and paper claims. State the execution order, runtime estimate, random seeds, solver status, and any data that cannot legally be redistributed.\n",
    )
    write_if_missing(
        root / "support/reproduction_commands.txt",
        "# Replace these placeholders with exact commands that run from the project root.\n# 1. install dependencies\n# 2. retrieve or prepare data\n# 3. run models\n# 4. regenerate figures and tables\n# 5. build the LaTeX paper\n",
    )
    write_if_missing(root / "support/materials_manifest.csv", "path,category,source,license,sha256,included,notes\n")
    write_if_missing(root / "support/data_inventory.csv", "dataset,included_path,source_url,license,version_or_date,sha256,retrieval_command,status\n")
    write_if_missing(
        root / "delivery/manifest.csv",
        "path,role,source_path,sha256\n",
    )
    write_if_missing(
        root / "official-submission/manifest.csv",
        "path,role,source_path,sha256\n",
    )
    write_if_missing(
        root / "environment/README.md",
        "# Environment\n\nRecord operating system, runtime and solver versions, dependency lock or package list, hardware-sensitive settings, locale, seeds, and installation commands.\n",
    )
    print(root / "contest_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
