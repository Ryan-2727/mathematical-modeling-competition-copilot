# Diagnostics and result reconciliation

Use this module after candidate models exist and before decisive values enter
`results/verified_values.csv`. Diagnose the claim, not merely the solver.

## Contents

- [1. Predeclare the diagnostic contract](#1-predeclare-the-diagnostic-contract)
- [2. Fill the diagnostic matrix](#2-fill-the-diagnostic-matrix)
- [3. Qualify independent routes](#3-qualify-independent-routes)
- [4. Reconcile estimates](#4-reconcile-estimates)
- [5. Admit or narrow claims](#5-admit-or-narrow-claims)
- [6. Preserve the evidence chain](#6-preserve-the-evidence-chain)

## 1. Predeclare the diagnostic contract

For each decisive claim, record before the final run:

- model or estimator under test;
- failure mode the check could expose;
- metric and acceptance threshold;
- data split, scenario, perturbation range, or invariant;
- output artifact and action on failure.

Link every added mechanism to an expected diagnostic signature. A mechanism is
not validated because fit improves; require the predicted defect to weaken
without creating a more serious failure elsewhere.

Use `reports/validation_design.csv` for claim-level checks and
`reports/stress_tests.csv` for perturbations. Do not retrofit thresholds after
seeing the outcome.

## 2. Fill the diagnostic matrix

Select proportionate rows from this matrix. Record `not_applicable` with a
reason instead of inventing a pass.

| Dimension | Minimum questions and evidence |
|---|---|
| Data | Are units, semantics, coverage, missingness, resolution, and leakage valid? |
| Fit | Does the model improve the declared metric against a credible baseline? |
| Residual | Is bias, trend, autocorrelation, heteroscedasticity, spatial/frequency structure, or group drift left? |
| Parameter | Are bounds hit, profiles flat, correlations extreme, signs/units plausible, and sensitivities sufficient? |
| Robustness | Do window, initialization, preprocessing, deletion, resampling, and assumptions change the conclusion? |
| Uncertainty | Do propagation, bootstrap, posterior/sampling interval, or scenario range match the data-generating process? |
| External consistency | Do dimensions, conservation, feasibility, known limits, or authoritative ranges hold? |
| Generalization | Does a held time, group, condition, region, or scenario retain the claim? |
| Algorithm | Do multi-start, alternate solver, refinement, small-case enumeration, or synthetic recovery expose instability? |

Do not interpret residual normality alone as model adequacy. Inspect patterns
that correspond to the mechanism and sampling process. Distinguish numerical
error, observation error, structural error, and decision uncertainty.

## 3. Qualify independent routes

Record every route in `reports/independent_routes.csv` with its principle, data
representation, dominant failure mode, standalone result, uncertainty, and
evidence path.

Call two routes independent only when they differ in at least two of:

1. mathematical principle;
2. data representation;
3. dominant failure mode.

Examples of legitimate contrasts include generative fit versus an invariant,
simulation versus an analytic small case, forecast model versus leakage-safe
historical backtest, and optimization result versus an independent feasibility
checker. The same objective with a different optimizer is an algorithm check,
not an independent estimate.

When external truth is unavailable, require two qualified independent checks
or record why that is impossible and substitute multiple complementary checks.
Never convert agreement between dependent routes into an accuracy claim.

## 4. Reconcile estimates

Record each material estimate in `reports/result_reconciliation.csv` with value,
unit, uncertainty, model, condition, route, data version/hash, preprocessing,
and verdict. Compare estimates using a predeclared absolute, relative, or
uncertainty-aware tolerance.

If estimates disagree materially, investigate in this order:

1. unit, index, sign, coordinate, and data-version alignment;
2. formula transcription, code implementation, and result extraction;
3. solver status, initialization, local mode, tolerance, and discretization;
4. preprocessing, feature detection, censoring, and anomaly handling;
5. nuisance, calibration, and observation-model assumptions;
6. shared versus condition-specific parameter assumptions;
7. omitted mechanism, regime change, or structural misspecification;
8. structural or practical non-identifiability.

Rerun the smallest discriminating test after each plausible cause. Preserve the
original result and resolution evidence. Do not average estimates merely to
make the discrepancy disappear.

Use the following resolution rules:

- If routes agree within tolerance, use the more mechanism-complete yet
  identifiable route as primary and retain the other as a cross-check.
- If one route fails its known diagnostic, reject it with evidence rather than
  silently deleting it.
- Combine estimates only under an explicit error/dependence model with a valid
  reason for pooling.
- If conflict remains, report a range, conditional conclusion, or unresolved
  limitation; do not manufacture a single precise value.

## 5. Admit or narrow claims

Assign one claim verdict:

- `PASS`: result is reproducible, identifiable at the stated precision, passes
  the decisive diagnostics, and has no unresolved material conflict.
- `CONDITIONAL`: result is useful only under stated assumptions, fixed
  parameters, restricted conditions, or accepted limitations; state them next
  to the result and propagate them into the abstract and conclusion.
- `FAIL`: evidence does not support the requested claim; omit the decisive
  value, use the fallback, or report non-identifiability/unresolved conflict.

Block `PASS` when any of these remains:

- the selected model has no credible baseline or rejection rule;
- a complex mechanism lacks its predicted diagnostic improvement;
- a decisive parameter has an identifiability `FAIL`;
- a purported independent route fails the two-difference rule;
- forced parameter sharing creates systematic group residuals;
- material estimator disagreement is unexplained;
- uncertainty, units, feasibility, or solver status is missing.

Treat `CONDITIONAL` as a claim boundary, not a soft pass. Rewrite the conclusion
so it cannot be read outside its valid conditions.

## 6. Preserve the evidence chain

Only after reconciliation, write decisive values to
`results/verified_values.csv`. Bind each value to code/command, input and result
hashes, diagnostic artifacts, route comparison, generated LaTeX, figure/table,
and paper location in `reports/evidence_chain.csv`.

Make the paper show:

- the direct result and uncertainty;
- why the selected model was preferred to its baseline;
- the independent or complementary check;
- the most decision-relevant diagnostic;
- any condition, conflict resolution, or remaining limitation.

Verify that abstract, body, tables, figures, and support artifacts consume the
same frozen value source. A clean narrative never overrides conflicting
machine-readable evidence.
