# Workflow Map

This repository is designed as a self-contained Codex skill. A new computer can install only this repository and still get the full mathematical modeling competition workflow.

## Embedded Workflow Modules

The following formerly separate skills or helper workflows are embedded as reference playbooks:

- `contest-setup.md`: project initialization, `plan.md`, `todo.md`, contest constraints, and task tracking.
- `mathmodel-six-phase.md`: contest-specific six-phase workflow: setup, analysis/modeling, coding/visualization, diagrams, paper writing, and verification.
- `llm-mm-agent-methodology.md`: LLM-MM-Agent-inspired four-stage loop and HMML/MLE-Solver-style method selection.
- `paper-context-resolver.md`: narrow paper or reproduction detail resolution.
- `computation-and-visualization.md`: code, notebooks, result tables, data validation, and data-driven figures.
- `diagrams.md`: flowcharts, architecture diagrams, and non-data visual explanation.
- `paper-writing.md`: contest paper structure, writing quality, and claim discipline.
- `latex-tables.md`: LaTeX table and academic table polish.
- `final-verification.md`: evidence-before-completion and submission readiness checks.
- `tool-fallbacks.md`: what requires optional Codex plugins and what to do when they are missing.

## Optional Codex Plugins

These capabilities cannot be fully embedded as text because they depend on runtime tools:

- `jupyter-notebooks`: install/enable the Data Analytics plugin if notebook creation and top-to-bottom execution are required.
- `documents`: install/enable the Documents plugin if DOCX creation, editing, or visual render QA is required.
- `pdf`: install/enable the PDF plugin if PDF rendering, extraction, or page-image inspection is required.
- `spreadsheets`: install/enable the Spreadsheets plugin if `.xlsx` creation, formulas, charts, or workbook rendering are required.

When these plugins are unavailable, continue the modeling workflow and record the missing capability in `reports/verification_report.md`.

## Phase Outputs

| Phase | Minimum output | Verification |
| --- | --- | --- |
| Setup | `plan.md`, `todo.md` | User constraints captured |
| Analysis | `reports/problem_analysis.md` | Every subproblem mapped |
| Modeling | `reports/model_design.md` | Variables, formulas, assumptions defined |
| Literature | source notes | Claims tied to sources |
| Computation | code/notebooks, `results/` | Executed or gap stated |
| Figures/tables | `figures/`, tables | Referenced and consistent |
| Writing | `paper/` | Results match computation |
| Final check | `reports/verification_report.md` | Completion claims backed by evidence |

## Fallback Behavior

If a helper capability is unavailable:

1. Continue with the same phase manually.
2. Use plain Markdown, CSV, scripts, or text artifacts where possible.
3. Record what was not verified in `reports/verification_report.md`.
4. Do not claim visual, formula, or execution verification unless it was actually performed.
