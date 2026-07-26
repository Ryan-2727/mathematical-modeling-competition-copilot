# Data, traceability, and reproducibility

## Data audit

Complete `reports/data_audit.md` before choosing a data-driven model. For every
dataset, record source, collection/access date, permission/license, schema,
units, missingness, duplicates, outliers, transformations, and hash. Explain every
row/column removal and preserve raw data unchanged.

Check for leakage before fitting: future information in time series, target-derived
features, duplicated entities across train/test, and preprocessing fit on all data.
Use time-respecting splits for temporal tasks and record the split rule. Synthetic
data may illustrate a method but cannot be presented as observed evidence.

## Traceability

Maintain `reports/traceability.md` with one row per subproblem mapping data, model,
validation, result file, figure/table, and paper section. A numeric claim may enter
the paper only if this row is complete.

## Reproducible runs

At the first successful run, execute `scripts/capture_environment.py` and save the
output in `environment/runtime_manifest.json`. Record software/solver versions,
parameters, seeds, command, data hashes, hardware constraints, solver status,
tolerances, stopping reason, and optimality gap when applicable.

Re-run the project from a clean copied working directory before freeze. Use argv
commands by default, retain one log per run, repeat the frozen pipeline, and
compare declared outputs by hashes or predeclared numeric tolerances. If full
rerun is too expensive, re-run the smallest representative pipeline and state
what remains unverified; do not label the entire project reproducible.

## Validation gates

Choose validation to match the model, and record its acceptance criterion before
computing results:

- regression: residual behavior, holdout/cross-validation, extrapolation limits;
- classification: split integrity, class balance, confusion matrix, calibration;
- time series: rolling or holdout backtest against a naive baseline;
- optimization: feasibility, constraint residuals, integrality, solver status and
  optimality gap or heuristic disclaimer;
- simulation: warm-up, independent replications, uncertainty interval;
- ODE/PDE: units, parameter identifiability, initial/boundary conditions,
  step/grid convergence and conservation where relevant;
- ranking/evaluation: indicator direction, normalization, weight provenance,
  consistency and ranking sensitivity.

Do not turn an unavailable validation into a claim of accuracy. Explain its
limitation and use the conclusion only within the supported scope.

## Runtime and cache locks

Before selecting an optimization, nonlinear, causal, or spreadsheet-dependent
route, run `scripts/probe_runtime_capabilities.py` with the required profile and
save `reports/runtime_capabilities.json`. Choose only a recorded available route;
do not install a dependency mid-run or silently exchange an unavailable solver
for a different mathematical method.

For a reusable aggregate cache, write a manifest containing the relative raw
source and cache paths, both SHA-256 values, the aggregation rule, and ISO
`training_end` / `target_start` dates. Run `scripts/verify_data_cache.py` before
reuse. The cache verifier binds files and split order; it does not certify that
the selected aggregation is substantively correct.
