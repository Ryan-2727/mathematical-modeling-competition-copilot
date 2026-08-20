# CUMCM B/C targeted model library

This reference routes recurring B/C structures to the smallest defensible model.
The machine-readable source is
`assets/model-library/cumcm-bc-model-cards.json`; validate it with
`scripts/verify_model_library.py`. The cards are preparation aids, not evidence
that a future problem requires a named method.

## Contents

- [Routing protocol](#routing-protocol)
- [Executable reference kernels](#executable-reference-kernels)
- [Fast routing table](#fast-routing-table)
- [Designed experiments and response surfaces](#designed-experiments-and-response-surfaces)
- [Bearing-only localization](#bearing-only-localization)
- [Coverage path planning](#coverage-path-planning)
- [Sequential testing and downstream decisions](#sequential-testing-and-downstream-decisions)
- [Compositional data](#compositional-data)
- [Robust supply-chain MILP](#robust-supply-chain-milp)
- [Price-demand and assortment decisions](#price-demand-and-assortment-decisions)
- [Longitudinal and interval-censored timing](#longitudinal-and-interval-censored-timing)
- [Calibrated imbalanced classification](#calibrated-imbalanced-classification)
- [Source discipline](#source-discipline)

## Routing protocol

1. Identify the requested output, decision, uncertainty, and available truth.
2. Match observed structure to a card's signals; do not route from a single
   keyword.
3. Execute the card's baseline first and preserve its result.
4. Predeclare the candidate metric and minimum advantage in
   `reports/model_budget.csv` before running the candidate.
5. Promote only after the card's diagnostic and falsification test pass.
6. If promotion fails, retain the baseline in the main paper and place the
   candidate in model optimization or rejected alternatives.
7. Build figures from executed results. A suggested deliverable is not a quota.

## Executable reference kernels

Five high-risk cards include bounded reference implementations: bearing-only
localization, rectangular coverage sweeps, compositional closure/CLR,
interval-censored timing, and small robust binary allocation. First verify all
bundled synthetic truth and metamorphic cases:

```bash
python scripts/run_model_kernel_regression.py --backend stdlib \
  --out reports/kernel-regression-stdlib.json
```

When NumPy and SciPy are already available, rerun with `--backend scientific`.
Do not install them silently in contest mode. Execute one declared kernel with:

```bash
python scripts/run_model_kernel.py \
  --kernel bearing-only-localization \
  --input code/bearing-input.json \
  --output results/bearing-output.json \
  --backend auto
```

Record project use in `reports/model_kernel_usage.csv`, including the exact
input/output and regression hashes, then run
`scripts/verify_model_kernel_evidence.py`. The dispatcher reports the backend
actually used and returns `LIMITED` for degenerate or unsupported cases. A
synthetic pass verifies only the reference implementation. It is not evidence
that the card fits the contest problem, that assumptions hold, or that fixture
values may be copied into the paper.

## Fast routing table

| Structure | Start with | Promote only for | Critical failure check |
| --- | --- | --- | --- |
| Controlled factors and a small experiment budget | main-effects regression | supported curvature/interactions and better confirmation error | lack of fit and extrapolated optimum |
| Bearings without ranges | geometric intersection or nonlinear least squares | adequate observability and lower recovery error | rank loss, mirror ambiguity, degenerate geometry |
| Survey lines and overlap | conservative parallel sweep | verified coverage with material route reduction | independent fine-grid or polygon coverage |
| Sampling then accept/reject/action | fixed-sample interval and decision tree | controlled risk with lower expected sample/cost | boundary simulation and error rates |
| Components sum to a constant | interpretable ratios | stable log-ratio analysis | zero treatment and subcomposition sensitivity |
| Supplier/planting/transport capacities | deterministic LP/MILP | better held-out feasibility for acceptable cost | independent feasibility and small-instance bound |
| Price, demand, replenishment, assortment | time-safe forecast and fixed policy | stable elasticity and better unseen-period policy value | confounding, stockout censoring, policy regret |
| Repeated subject measurements and threshold time | subject-level summaries | stable mixed/interval-censored timing recommendation | subject-level holdout and censoring sensitivity |
| Rare-event classification | regularized logistic risk | better calibrated decision value | PR curve, calibration, subgroup and prevalence shift |

## Designed experiments and response surfaces

- Preserve model hierarchy: retaining an interaction normally retains its main
  effects.
- Use replicated observations, confirmation experiments, or honest held-out
  combinations to distinguish fit from interpolation.
- Optimize only inside the supported factor region unless extrapolation is a
  stated limitation.
- Prefer effect plots, residual diagnostics, contours, and a confirmation plan
  over a decorative three-dimensional surface.

## Bearing-only localization

- Freeze the coordinate frame, angle direction, wrapping rule, and units before
  estimating.
- Audit structural and practical observability before trusting optimizer output.
- Use synthetic recovery with declared angle noise and include degenerate
  geometries.
- If only a locus or interval is identifiable, report it and design the next
  bearing or maneuver; do not fabricate range information.

## Coverage path planning

- Derive the sensor footprint and overlap from geometry instead of treating line
  spacing as coverage.
- Include boundary, transit, and turning costs when the requested plan must be
  executable.
- Recheck the final path with an independent raster/polygon implementation or a
  finer grid.
- Report coverage, redundancy, path length, and uncovered boundary regions
  together.

## Sequential testing and downstream decisions

- Separate the sampling evidence, stopping rule, and downstream action model.
- Verify type-I/type-II or posterior-risk claims at boundary parameter values.
- Compare expected sample number and total decision cost against a fixed-sample
  plan.
- Carry parameter uncertainty into later decisions rather than reusing a point
  estimate as known truth.

## Compositional data

- Confirm closure and classify zeros as rounded, below detection, or structural.
- Avoid ordinary correlation and Euclidean distance on raw closed percentages.
- Fit zero handling and preprocessing inside training folds.
- Interpret ratios or balances and test subcomposition and replacement
  sensitivity.

## Robust supply-chain MILP

- Begin with a deterministic LP/MILP and independently recompute every
  constraint on a small instance.
- Add robust or stochastic structure only for uncertainty that changes the
  decision.
- Distinguish here-and-now decisions from recourse available after uncertainty
  is observed.
- Report objective value, solver status/gap, extreme-scenario feasibility,
  implementation cost, and a readable contingency policy.

## Price-demand and assortment decisions

- Use chronological validation and address stockout-censored demand.
- Treat observational price effects as predictive unless confounding and an
  identification strategy support a causal interpretation.
- Compare with fixed-price, fixed-assortment, or myopic replenishment policies.
- Report profit, waste, service, and recommendation stability rather than one
  unconstrained optimum.

## Longitudinal and interval-censored timing

- Keep all observations from one subject in the same validation fold.
- Distinguish observed measurement time from latent threshold-crossing time.
- Compare a mixed-effects route with a subject-level or nonparametric
  interval-censored route.
- Stress the threshold, measurement window, grouping, and censoring assumptions;
  report a timing interval when an individual optimum is not identifiable.

## Calibrated imbalanced classification

- Begin with regularized logistic regression and prevalence-aware metrics.
- Fit resampling, feature selection, and probability calibration inside training
  folds only.
- Require precision-recall, calibration, and decision-cost evidence; accuracy or
  ROC AUC alone is insufficient for a rare class.
- A complex classifier without a material, calibrated decision advantage is a
  rejected candidate, not the main model.

## Source discipline

The model-card sources establish methods and known diagnostics. They do not
automatically belong in a contest paper. Cite a source only when it supports a
specific reachable claim in the manuscript, and record that role in
`reports/bibliography.csv`. Do not copy all model-library citations into the
paper to satisfy the reference minimum.
