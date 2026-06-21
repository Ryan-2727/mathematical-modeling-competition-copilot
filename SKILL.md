---
name: mathematical-modeling-competition-copilot
description: Self-contained end-to-end mathematical modeling competition workflow for contest problem solving and paper production. Use when Codex needs to help with MCM/ICM, CUMCM, Huawei Cup, school mathematical modeling contests, or similar tasks involving problem analysis, literature-supported modeling, reproducible computation, figures, tables, DOCX/PDF/LaTeX paper writing, and final verification.
---

# Mathematical Modeling Competition Copilot

Use this as the main entry point for mathematical modeling competitions. This skill is self-contained for workflow knowledge: it embeds the contest setup, modeling, literature resolution, computation, writing, table, and verification rules that were previously spread across multiple helper skills.

It does not promise an award. It maximizes award probability through disciplined modeling, reproducible computation, strong writing, and hard verification.

## Operating Mode

- Start with the required workflow order below.
- Read only the embedded reference files needed for the current phase.
- Use installed plugins when they are available for file-specific work such as notebooks, DOCX, PDF, or spreadsheets.
- If a plugin or runtime is unavailable, continue with the workflow manually and record the limitation in `reports/verification_report.md`.

## Required Workflow Order

1. **Contest setup and strategy**
   - Read `references/embedded/contest-setup.md`.
   - Use the embedded brainstorming gate in that file before committing to a modeling route.
   - Confirm contest type, language, submission format, time budget, team role split, available data, and deliverables.
   - Create or update `plan.md` and `todo.md`.

2. **Problem analysis and model design**
   - Read `references/embedded/llm-mm-agent-methodology.md`.
   - Read `references/embedded/mathmodel-six-phase.md` for contest-specific modeling expectations.
   - Produce a subproblem map, assumptions, variables, constraints, objective functions, candidate methods, and validation plan.

3. **Literature and reproduction details**
   - Read `references/embedded/literature-fetch-and-explain.md` when literature search, paper selection, or paper explanation is needed.
   - Read `references/embedded/paper-context-resolver.md` when a narrow source-backed detail matters.
   - Do not use broad paper summaries as a substitute for model design.
   - Record source, claim, modeling impact, and whether evidence is direct or inferred.

4. **Computation and experiments**
   - Read `references/embedded/computation-and-visualization.md`.
   - Use notebooks, scripts, or spreadsheets to produce executable evidence.
   - Every numeric conclusion must come from executed code, a spreadsheet formula, or a cited source.

5. **Tabular analysis and scenario sheets**
   - Use spreadsheet-style reasoning for scoring matrices, sensitivity tables, scenario comparison, and dashboards.
   - If the Spreadsheets plugin is installed, use it for `.xlsx` creation and verification.
   - If not installed, create CSV/Markdown tables and record the limitation.

6. **Figures, flowcharts, and diagrams**
   - Read `references/embedded/diagrams.md`.
   - Separate data-driven charts from non-data diagrams.
   - Keep figure captions, labels, and source data traceable.

7. **Paper writing**
   - Read `references/embedded/paper-writing.md`.
   - For Chinese contests using the 2025 national Chinese format, follow `references/embedded/paper-writing-zh-cn-format2025.md`.
   - For English contests such as MCM/ICM, preserve and follow `references/embedded/paper-writing-en-contest-base.md`.
   - Assemble assumptions, notation, model derivations, results, figures, tables, sensitivity analysis, and limitations into the paper.
   - Use DOCX/PDF/LaTeX/Typst only when the contest or user chooses that path.

8. **Table polish**
   - Read `references/embedded/latex-tables.md` for LaTeX or academic tables.
   - For general contest tables, enforce captions, units, source notes, aligned numeric columns, reasonable precision, and consistency with result files.

9. **Final verification**
   - Read `references/embedded/final-verification.md`.
   - Read `references/embedded/tool-fallbacks.md` if any plugin or runtime was missing.
   - Do not claim completion without fresh evidence.

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
- If a plugin is missing, degrade gracefully; do not pretend visual rendering, workbook formulas, or notebook execution were verified.

## Embedded References

Use these files as phase playbooks:

- `references/embedded/contest-setup.md`
- `references/embedded/mathmodel-six-phase.md`
- `references/embedded/llm-mm-agent-methodology.md`
- `references/embedded/literature-fetch-and-explain.md`
- `references/embedded/paper-context-resolver.md`
- `references/embedded/computation-and-visualization.md`
- `references/embedded/diagrams.md`
- `references/embedded/paper-writing.md`
- `references/embedded/paper-writing-zh-cn-format2025.md`
- `references/embedded/paper-writing-en-contest-base.md`
- `references/embedded/latex-tables.md`
- `references/embedded/final-verification.md`
- `references/embedded/tool-fallbacks.md`

Read `references/workflow-map.md` for the dependency map, plugin limits, and fallback behavior.
