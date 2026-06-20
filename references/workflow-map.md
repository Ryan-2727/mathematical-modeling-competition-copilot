# Workflow Map

## Integrated Skills

Personal or installed skills:

- `brainstorming`: clarify contest goal, assumptions, constraints, and success criteria.
- `1start-mathmodel`: initialize `plan.md` and `todo.md` for a math modeling project.
- `2analysis-modeling`: analyze statement, define variables, constraints, and model strategy.
- `3coding-visual`: implement code, run experiments, and create data-driven figures.
- `4drawio`: create non-data diagrams such as workflows and method architectures.
- `5writing`: assemble the contest paper from model and result artifacts.
- `6verity`: check reproducibility, consistency, deliverable completeness, and submission readiness.
- `paper-context-resolver`: resolve narrow paper/reproduction details when README or source files leave a critical gap.
- `llm-mm-agent`: apply the MM-Agent four-stage modeling framework and HMML-style method selection.
- `latex-tables`: generate or polish academic LaTeX tables.
- `verification-before-completion`: require evidence before claiming completion.

Plugin-provided skills:

- `jupyter-notebooks`: create and validate reproducible notebooks.
- `documents`: create/edit DOCX and render pages for visual QA.
- `pdf`: read, create, render, and inspect PDF files.
- `spreadsheets`: create, analyze, format, and verify spreadsheet workbooks.

## Fallback Behavior

If an integrated skill is unavailable:

1. Continue with the same phase manually.
2. Record the missing helper in `reports/verification_report.md`.
3. Do not block the contest workflow unless the missing capability is required to open or verify the final deliverable.

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
