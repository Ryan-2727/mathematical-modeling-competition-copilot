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

## Decisive-value registry

Use `results/verified_values.csv` as the single source of truth for every
computed number that materially supports an answer, recommendation, constraint,
or comparison in the paper.

1. Give every value a stable unique key, declared type and unit, source artifact,
   source SHA-256, and source locator.
2. Generate `paper/generated/results.tex` with
   `scripts/generate_verified_values.py`.
3. Reference the generated macros from reachable LaTeX instead of retyping the
   values.
4. Run `scripts/verify_verified_values.py` after every result or paper change.
   A source-hash mismatch, duplicate key, invalid type, missing unit, unused
   decisive macro, or manually duplicated decisive value blocks completion.

Formatting precision belongs in the registry or generator metadata; it must not
quietly alter the scientific value.

## Model-family evidence adapters

Declare the primary model family for each decisive subproblem and run
`scripts/verify_model_validation.py`. Supported evidence contracts cover
regression/forecast, classification, optimization, stochastic simulation,
network/ranking, mechanism/dynamics, causal/econometric, unsupervised,
queueing/reliability, spatial/spatiotemporal, and multi-objective/dynamic
optimization models. The manifest must point to the actual diagnostics and state
numeric acceptance thresholds selected before interpreting the outcome.

The adapter checks declared evidence and thresholds. It cannot certify model
choice, causal validity, global optimality, or mathematical truth; those remain
part of the paper argument and independent review.

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
- Maintain `reports/figure_manifest.csv` with the source data or team-generated
  diagram note, LaTeX label, caption insight, axis units, grayscale/color
  accessibility check, and verification status.
- Run `scripts/verify_manuscript_quality.py` after compilation; inspect rendered
  pages even when its deterministic checks pass.

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
- The verified-value registry matches its hashed source artifacts and all
  decisive LaTeX values are generated from it.
- The selected model-family validation adapter passes with locatable evidence.
