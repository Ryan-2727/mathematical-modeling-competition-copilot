# Mathematical Modeling Six-Phase Workflow

Use this as the contest-specific backbone.

## Phase 1: Setup

Initialize the project plan, todo list, artifact folders, and submission assumptions. Keep scope realistic for the deadline.

## Phase 2: Analysis And Modeling

Produce `reports/problem_analysis.md` and `reports/model_design.md`.

Include:

- subproblem decomposition
- variables and parameters
- assumptions and justifications
- objective functions
- constraints
- candidate model families
- selected model and why it is defensible
- validation metrics

Avoid method stacking. A clear baseline plus one stronger method is usually better than many weakly explained models.

## Phase 3: Coding And Visualization

Produce reproducible code, result tables, and figures.

Rules:

- Keep raw and processed data separate.
- Generate figures from code or documented spreadsheet formulas.
- Record command, environment, input path, output path, and execution status.
- Use a simple baseline before complex refinements.

## Phase 4: Diagrams

Create diagrams only when they add explanation:

- method flowchart
- algorithm pipeline
- causal or system structure
- data processing flow

Do not redraw statistical plots as decorative diagrams.

## Phase 5: Writing

Assemble the paper from verified artifacts. Do not invent values during writing. Every numeric claim must trace to `results/`, `figures/`, code, spreadsheet formulas, or a cited source.

## Phase 6: Verification

Check reproducibility, consistency, format, and submission readiness. Produce `reports/verification_report.md`.

Minimum checks:

- every subproblem answered
- assumptions consistent
- formula symbols defined
- table and figure labels referenced
- results match code or tables
- paper format satisfies contest requirements
- missing plugin/runtime limitations recorded
