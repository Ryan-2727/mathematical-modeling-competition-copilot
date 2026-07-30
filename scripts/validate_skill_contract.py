#!/usr/bin/env python3
"""Validate the skill's explicit invocation gate and local reference integrity."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
EVALS = ROOT / "evals" / "invocation-cases.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    text = SKILL.read_text(encoding="utf-8")
    if not text.startswith("---\n"): fail("SKILL.md must start with YAML frontmatter")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match: fail("SKILL.md frontmatter is malformed")
    frontmatter = match.group(1)
    if "name: mathematical-modeling-competition-copilot" not in frontmatter: fail("skill name mismatch")
    description = next((line.split(":", 1)[1].strip() for line in frontmatter.splitlines() if line.startswith("description:")), "")
    required = ("Explicit-invocation-only", "Use ONLY", "$mathematical-modeling-competition-copilot", "Do not use it automatically")
    missing = [phrase for phrase in required if phrase not in description]
    if missing: fail("explicit invocation contract missing: " + ", ".join(missing))
    body_required = ("Do not infer invocation", "unless the user explicitly calls this skill")
    missing_body = [phrase for phrase in body_required if phrase not in text]
    if missing_body: fail("body invocation gate missing: " + ", ".join(missing_body))
    if len(text.splitlines()) > 500:
        fail("SKILL.md exceeds the 500-line routing budget")
    descriptor_checks = {
        "README.md": "Explicit Invocation Only",
        "README.en.md": "Explicit Invocation Only",
        "README.zh-CN.md": "仅限显式调用",
        "DESCRIPTION.md": "Explicit-invocation-only",
        "agents/openai.yaml": "Explicit-only",
    }
    for relative, phrase in descriptor_checks.items():
        if phrase not in (ROOT / relative).read_text(encoding="utf-8"):
            fail(f"{relative} does not preserve the explicit invocation contract")
    delivery_checks = {
        "SKILL.md": (
            "at least 10", "paper/main.pdf", "support.zip",
            "scripts/verify_paper_delivery.py", "scripts/verify_latex_compatibility.py",
            "scripts/verify_paper_depth.py", "scripts/verify_portable_latex.py",
            "scripts/verify_pdf_visual.py", "scripts/verify_verified_values.py",
            "scripts/verify_model_validation.py", "scripts/run_benchmark_regression.py",
            "scripts/prepare_private_regression.py",
            "scripts/probe_runtime_capabilities.py",
            "scripts/verify_data_cache.py",
            "scripts/verify_result_template.py",
            "scripts/score_private_regression.py",
            "scripts/verify_evidence_chain.py",
            "scripts/verify_decision_quality.py",
            "scripts/verify_figure_narrative.py",
            "scripts/verify_page_readability.py",
            "scripts/verify_modeling_argument_quality.py",
            "scripts/verify_answer_density.py",
            "scripts/verify_visual_design_system.py",
            "scripts/verify_paper_presentation.py",
            "scripts/verify_abstract_structure.py",
            "scripts/verify_result_story.py",
            "scripts/contestctl.py", "scripts/lock_contest_rules.py",
            "scripts/verify_abstract_quality.py",
            "scripts/verify_bibliography_metadata.py",
            "scripts/verify_manuscript_quality.py",
            "scripts/verify_delivery_profiles.py",
            "scripts/generate_paper_artifacts.py",
            "scripts/verify_notation_registry.py",
            "scripts/verify_rendered_figures.py",
            "references/embedded/orchestration-and-paper-assurance.md",
            "joint feasibility report", "independent node-by-node",
            "attachment-to-subproblem coverage audit",
            "zero/blank-value semantics",
            "hashed, immutable aggregate", "original constraint granularity",
            "Overleaf", "VS Code", "latexmk",
        ),
        "README.md": (
            "at least 10", "paper/main.pdf", "support.zip",
            "scripts/verify_latex_compatibility.py", "Overleaf", "VS Code", "latexmk",
        ),
        "README.en.md": (
            "at least 10", "paper/main.pdf", "support.zip",
            "scripts/verify_latex_compatibility.py", "Overleaf", "VS Code", "latexmk",
        ),
        "README.zh-CN.md": (
            "至少 10", "paper/main.pdf", "support.zip",
            "scripts/verify_latex_compatibility.py", "Overleaf", "VS Code", "latexmk",
        ),
        "references/embedded/latex-paper-pipeline.md": (
            "Overleaf", "VS Code", "latexmk", "reports/latex_compatibility.json",
        ),
        "references/embedded/verified-literature-and-two-part-delivery.md": (
            "Google Scholar", "reports/bibliography.csv", "support/materials_manifest.csv"
        ),
        "references/embedded/computation-and-visualization.md": (
            "results/verified_values.csv", "paper/generated/results.tex",
            "verify_model_validation.py",
        ),
        "references/embedded/final-verification.md": (
            "verify_pdf_visual.py", "anonymity_scan.py", "clean copied project",
        ),
        "references/embedded/independent-review-and-regression.md": (
            "aggregate_reviewer_reports.py", "run_benchmark_regression.py",
            "prepare_private_regression.py",
        ),
        "references/embedded/executable-contest-profiles.md": (
            "cumcm-2026", "mcm-icm-current",
        ),
        "references/embedded/operational-quality-gates.md": (
            "rules.lock.json", "contestctl.py", "verify_abstract_quality.py",
            "verify_bibliography_metadata.py", "verify_manuscript_quality.py",
            "verify_delivery_profiles.py", "official-submission",
            "Coupled feasibility gate", "reports/feasibility_audit.json",
            "attachment-to-subproblem coverage",
            "zero/blank-value semantics", "censored/not-detected",
            "Data-scale and time-split gate", "reports/data_scale_audit.json",
        ),
        "references/embedded/runtime-template-and-decision-audits.md": (
            "probe_runtime_capabilities.py", "verify_data_cache.py",
            "verify_result_template.py", "score_private_regression.py",
            "Predictive versus causal claims",
        ),
        "references/embedded/award-oriented-evidence-chain.md": (
            "verify_evidence_chain.py", "model_challenge.json",
            "fallback_plan.csv", "verify_decision_quality.py",
            "verify_figure_narrative.py", "verify_page_readability.py",
        ),
        "references/embedded/mechanism-semantics-and-argument.md": (
            "semantic_audit.csv", "mechanism_audit.json", "validation_design.csv",
            "conclusion_map.csv", "innovation_ledger.csv",
            "verify_modeling_argument_quality.py",
        ),
        "references/embedded/paper-presentation-and-visual-design.md": (
            "verify_answer_density.py", "verify_visual_design_system.py",
            "verify_paper_presentation.py", "presentation_checklist.csv",
        ),
        "references/embedded/result-first-paper-convergence.md": (
            "analysis-method-result", "model_simplification_log.csv",
            "visual_storyboard.csv", "verify_result_story.py",
        ),
        "references/embedded/orchestration-and-paper-assurance.md": (
            "contestctl.py doctor", "contestctl.py run", "contestctl.py summary",
            "project_schema_version", "rendered_figure_manifest.csv",
            "notation_registry.csv", "equation_dimensions.csv",
            "generate_paper_artifacts.py", "paper/generated/core_results.tex",
        ),
        "assets/latex-paper-template/main.tex": (
            "支撑材料文件清单", r"\lstinputlisting", "code/main.py",
        ),
        "assets/latex-paper-template-mcm/main.tex": (
            r"\documentclass[12pt]", r"\TeamControlNumber",
            r"\includeaireport", "sections/summary",
        ),
        "assets/latex-paper-template-mcm/sections/summary.tex": (
            "Summary Sheet", r"\TeamControlNumber", r"\ProblemChoice",
        ),
    }
    for relative, phrases in delivery_checks.items():
        path = ROOT / relative
        if not path.is_file(): fail(f"missing delivery contract file: {relative}")
        contents = path.read_text(encoding="utf-8")
        missing_delivery = [phrase for phrase in phrases if phrase not in contents]
        if missing_delivery:
            fail(f"{relative} missing delivery contract: " + ", ".join(missing_delivery))
    for relative in (
        "scripts/build_support_archive.py",
        "scripts/scaffold_latex_paper.py",
        "scripts/verify_latex_compatibility.py",
        "scripts/verify_paper_delivery.py",
        "scripts/verify_paper_depth.py",
        "scripts/verify_portable_latex.py",
        "scripts/generate_verified_values.py",
        "scripts/verify_verified_values.py",
        "scripts/verify_model_validation.py",
        "scripts/verify_pdf_visual.py",
        "scripts/run_benchmark_regression.py",
        "scripts/prepare_private_regression.py",
        "scripts/aggregate_reviewer_reports.py",
        "scripts/contestctl.py",
        "scripts/lock_contest_rules.py",
        "scripts/verify_abstract_quality.py",
        "scripts/verify_bibliography_metadata.py",
        "scripts/verify_manuscript_quality.py",
        "scripts/verify_delivery_profiles.py",
        "scripts/contest_orchestration.py",
        "scripts/generate_paper_artifacts.py",
        "scripts/verify_notation_registry.py",
        "scripts/verify_rendered_figures.py",
        "scripts/verify_evidence_chain.py",
        "scripts/verify_decision_quality.py",
        "scripts/verify_figure_narrative.py",
        "scripts/verify_page_readability.py",
        "scripts/verify_modeling_argument_quality.py",
        "scripts/verify_answer_density.py",
        "scripts/verify_visual_design_system.py",
        "scripts/verify_paper_presentation.py",
        "scripts/verify_abstract_structure.py",
        "scripts/verify_result_story.py",
        "assets/latex-paper-template/main.tex",
        "assets/latex-paper-template/README.md",
        "assets/latex-paper-template/.latexmkrc",
        "assets/latex-paper-template/.vscode/settings.json",
        "assets/latex-paper-template/.vscode/extensions.json",
        "assets/latex-paper-template/code/main.py",
        "assets/latex-paper-template-mcm/main.tex",
        "assets/latex-paper-template-mcm/README.md",
        "assets/latex-paper-template-mcm/.latexmkrc",
        "assets/latex-paper-template-mcm/.vscode/settings.json",
        "assets/latex-paper-template-mcm/.vscode/extensions.json",
        "evals/quality-benchmark-schema.json",
    ):
        if not (ROOT / relative).is_file(): fail(f"missing delivery script: {relative}")
    portable_reference = ROOT / "references" / "embedded" / "latex-paper-pipeline.md"
    for phrase in (
        ".vscode/settings.json", ".latexmkrc", "latexmk (XeLaTeX)",
        "Ctrl+Alt+V", "verify_portable_latex.py",
    ):
        if phrase not in portable_reference.read_text(encoding="utf-8"):
            fail(f"latex-paper-pipeline.md missing portable LaTeX contract: {phrase}")
    references = set(re.findall(r"`(references/embedded/[^`]+\.md)`", text))
    for relative in references:
        if not (ROOT / relative).is_file(): fail(f"missing referenced file: {relative}")
    payload = json.loads(EVALS.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not cases or {item.get("expected") for item in cases} != {"invoke", "do_not_invoke"}: fail("invocation evals need positive and negative cases")
    for item in cases:
        prompt = item.get("prompt", "")
        explicit = (
            "$mathematical-modeling-competition-copilot" in prompt
            or re.search(
                r"mathematical-modeling-competition-copilot[\\/]SKILL\.md",
                prompt,
                re.IGNORECASE,
            )
            is not None
        )
        if (item.get("expected") == "invoke") != explicit: fail(f"invalid invocation case: {item.get('id')}")
    print(f"PASS references={len(references)} cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
