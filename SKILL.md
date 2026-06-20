---
name: mathematical-modeling-competition-copilot
description: End-to-end mathematical modeling competition workflow for contest problem solving and paper production. Use when Codex needs to help with MCM/ICM, CUMCM, Huawei Cup, school mathematical modeling contests, or similar tasks involving problem analysis, literature-supported modeling, reproducible computation, figures, tables, DOCX/PDF/LaTeX paper writing, and final verification.
---

# Mathematical Modeling Competition Copilot

Use this as the main entry point for mathematical modeling competitions. The goal is not to promise an award; the goal is to maximize award probability through disciplined modeling, reproducible computation, strong writing, and hard verification.

## Assumptions

- The user wants a practical contest workflow, not a standalone web app.
- Prefer minimal, verifiable artifacts over speculative complexity.
- Use external skills when installed; fall back to the same workflow manually when a helper skill is unavailable.
- Treat `LLM-MM-Agent` as a methodology skill, not as a mandatory runtime dependency.

## Required Workflow Order

1. **Contest setup and strategy**
   - Use `brainstorming` when the problem, constraints, or success criteria are unclear.
   - If available, use `1start-mathmodel` to create `plan.md` and `todo.md`.
   - Confirm contest type, language, submission format, time budget, team role split, and available data.

2. **Problem analysis and model design**
   - Use `llm-mm-agent` for the four-stage modeling loop.
   - If available, use `2analysis-modeling` for contest-specific model design.
   - Produce a subproblem map, assumptions, variables, constraints, objective functions, candidate methods, and validation plan.

3. **Literature and reproduction details**
   - Use `paper-context-resolver` only for narrow reproduction-critical gaps: dataset split, preprocessing, evaluation protocol, method detail, checkpoint/runtime assumption, or paper-vs-README conflict.
   - Do not use it for broad paper summaries. For general literature review, search primary sources and extract only methods that can improve the contest solution.
   - Record source, claim, how it changes the model, and whether evidence is direct or inferred.

4. **Computation and experiments**
   - Use `jupyter-notebooks` when the notebook is a deliverable, reproducibility record, or exploratory modeling artifact.
   - Use `3coding-visual` when available for code, result tables, and data figures.
   - Keep raw data, processed data, code, notebooks, figures, and results separated.
   - Every numeric conclusion must come from executed code, a spreadsheet formula, or a cited source.

5. **Tabular analysis and scenario sheets**
   - Use `spreadsheets` for scoring matrices, sensitivity tables, scenario comparison, summary dashboards, and Excel deliverables.
   - Keep formulas visible and traceable. Avoid hardcoding derived values.

6. **Figures, flowcharts, and diagrams**
   - Use `3coding-visual` for data-driven plots.
   - Use `4drawio` or equivalent diagramming only for method flowcharts, algorithm pipelines, causal structures, and framework diagrams.
   - Do not duplicate data charts as decorative diagrams.

7. **Paper writing**
   - Use `5writing` when available for contest paper assembly.
   - Use `documents` for DOCX creation/editing and visual render QA.
   - Use `pdf` for PDF rendering, inspection, extraction, and final layout checks.
   - Use LaTeX/Typst only when the contest or user chooses that path.

8. **Table polish**
   - Use `latex-tables` for LaTeX regression, summary statistics, and academic tables when available.
   - For general contest tables, enforce: concise captions, units, source notes, aligned numeric columns, no over-wide tables, no unsupported precision, and no table values that are absent from results.

9. **Final verification**
   - Use `6verity` when available for mathematical modeling deliverable checks.
   - Use `verification-before-completion` before claiming the work is complete.
   - Verify: problem requirements, assumptions, formulas, code rerun status, data lineage, table/figure consistency, citations, paper formatting, and final submission files.

## Default Artifact Layout

Create or preserve this layout unless the user provides an existing project structure:

```text
.
|-- plan.md
|-- todo.md
|-- data/
|   |-- raw/
|   `-- processed/
|-- notebooks/
|-- code/
|-- results/
|-- figures/
|-- reports/
|   |-- problem_analysis.md
|   |-- model_design.md
|   |-- experiment_log.md
|   `-- verification_report.md
`-- paper/
```

## Decision Rules

- If the problem statement is missing, ask for it before modeling.
- If data is missing but the task can proceed with public or synthetic data, label that explicitly.
- If multiple model families fit, compare the simplest credible baseline against one stronger method.
- If computation cannot be run, do not present numeric conclusions as verified.
- If time is short, prioritize a complete baseline model, clean paper structure, and final consistency checks over extra model variants.

## Paper Quality Bar

The final paper should have:

- A sharp abstract with problem, model, result, and validation.
- Clear assumptions and notation.
- Model sections aligned to subproblems.
- Results supported by reproducible outputs.
- Figures and tables that are readable without hunting through the text.
- Sensitivity or robustness analysis for key assumptions.
- Limitations that are honest but not self-defeating.
- References that support methods, data, or comparison baselines.

## Verification Checklist

Before final delivery, check:

- Every subproblem has an answer.
- Every table/figure is referenced, captioned, and consistent with source results.
- Units, symbols, and variable names are consistent.
- Code/notebook execution status is recorded.
- Literature claims have source links or citations.
- DOCX/PDF/LaTeX output is visually inspected when applicable.
- The final answer says what was verified and what remains unverified.

Read `references/workflow-map.md` for the dependency map and fallback behavior.
