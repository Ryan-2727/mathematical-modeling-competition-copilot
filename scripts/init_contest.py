#!/usr/bin/env python3
"""Create contest-mode manifests and audit templates without fetching the web."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from scaffold_latex_paper import paper_files, scaffold_latex_paper


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--contest", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--mode", choices=["training", "live", "posthoc"], required=True)
    parser.add_argument("--rules-url", action="append", default=[])
    parser.add_argument("--deadline", default="unknown")
    args = parser.parse_args()
    root = args.project_dir
    for name in ("data/raw", "data/processed", "code", "results", "figures", "paper", "reports", "support", "environment"):
        (root / name).mkdir(parents=True, exist_ok=True)
    if paper_files(root / "paper"):
        write_if_missing(root / "paper" / "references.bib", "")
    else:
        scaffold_latex_paper(root)
    manifest = {
        "contest": args.contest,
        "year": args.year,
        "mode": args.mode,
        "deadline": args.deadline,
        "rules_urls": args.rules_url,
        "rules_verified_at": None,
        "rules_snapshot_file": "reports/contest_rules_snapshot.md",
        "live_mode_policy": "static-authoritative-sources-only" if args.mode == "live" else "not-applicable",
        "submission_state": "draft",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (root / "contest_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_if_missing(root / "reports/contest_rules_snapshot.md", "# Contest rules snapshot\n\nRecord the official source, access time, rule version, selected profile, page limit, AI policy, submission method, deadline/time zone, and unresolved items. Do not mark this file verified until every field is checked.\n")
    write_if_missing(root / "reports/data_audit.md", "# Data audit\n\n| Dataset | Source | License/permission | Rows/columns | Units | Missing/outlier handling | Leakage risk | Hash |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    write_if_missing(root / "reports/traceability.md", "# Traceability\n\n| Subproblem | Data | Model | Validation | Result file | Figure/table | Paper section | Status |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n")
    write_if_missing(root / "reports/claims.csv", "claim_id,subproblem,claim,source_file,source_locator,command,figure_or_table,paper_location,human_verification,status\n")
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
    write_if_missing(root / "reports/bibliography.csv", "citation_key,title,authors,year,venue,doi_or_url,verification_source,verified_at,scholar_query,scholar_checked_at,scholar_status,claim_supported,source_locator,status\n")
    write_if_missing(root / "reports/model_decision_log.csv", "subproblem,baseline,candidate,mechanism_fit,assumptions,failure_test,validation_cost,selected,selection_evidence,status\n")
    write_if_missing(root / "reports/stress_tests.csv", "claim_id,subproblem,stress_type,change,acceptance_criterion,result_file,outcome,verdict,status\n")
    write_if_missing(root / "reports/units.csv", "symbol,meaning,unit,source,conversion,range_check,status\n")
    write_if_missing(
        root / "reports/reviewer_scorecard.csv",
        "dimension,score_1_to_5,evidence,major_objection,smallest_fix,status\n"
        "assumption_rationality,,,,,pending\n"
        "model_creativity,,,,,pending\n"
        "result_correctness,,,,,pending\n"
        "writing_clarity,,,,,pending\n",
    )
    write_if_missing(
        root / "reports/milestones.csv",
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
        "receipt-lock,72,hashes and receipt evidence,unassigned,submission verified,pending\n",
    )
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
        root / "environment/README.md",
        "# Environment\n\nRecord operating system, runtime and solver versions, dependency lock or package list, hardware-sensitive settings, locale, seeds, and installation commands.\n",
    )
    print(root / "contest_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
