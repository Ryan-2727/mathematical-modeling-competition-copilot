# Computation And Visualization

Use this module for code, notebooks, result tables, and data-driven figures.

## Computation Rules

- Separate `data/raw/`, `data/processed/`, `code/`, `notebooks/`, `results/`, and `figures/`.
- Keep parameters visible near the top of scripts or notebooks.
- Use deterministic seeds when stochastic methods are involved.
- Preserve raw data and document cleaning steps.
- Record data hashes, software/solver versions, solver status, tolerances, and stopping criteria for every primary run.
- Generate result tables from executed code or formulas.
- Store important outputs in machine-readable form such as CSV, JSON, or XLSX when possible.

## Notebook Rules

If a notebook is used:

- Structure it as `tl;dr`, context/methods, data, results, takeaways.
- Execute top-to-bottom when possible.
- Do not promote unexecuted calculations into the summary.
- Record execution gaps explicitly.

## Figure Rules

- Chart titles, axis labels, legends, and units must be readable.
- Figure captions should say what the reader should learn.
- Save source data or scripts for each figure.
- Avoid decorative plots that do not support an argument.

## Experiment Log

Maintain `reports/experiment_log.md` with:

- command or notebook used
- data input
- output files
- execution status
- surprising results
- repair or rerun notes

## Quality Gate

Before writing numeric claims:

- Code or formulas have been executed, or the gap is stated.
- Key values match result tables.
- Figures match source data.
- Units and scales are clear.
- The data-audit and traceability rows are complete.
- The validation method and acceptance criterion were selected before interpreting results; unsupported accuracy claims are absent.
