# Model reasoning kernel

Apply this kernel to every subproblem before implementation. Use it to turn a
plausible method into an auditable chain from evidence to an admissible claim.

## Contents

- [1. Establish the evidence contract](#1-establish-the-evidence-contract)
- [2. Build the mechanism ladder](#2-build-the-mechanism-ladder)
- [3. Build the candidate-model ladder](#3-build-the-candidate-model-ladder)
- [4. Register parameter roles](#4-register-parameter-roles)
- [5. Audit identifiability before solving](#5-audit-identifiability-before-solving)
- [6. Design joint inference](#6-design-joint-inference)
- [7. Select, challenge, and fall back](#7-select-challenge-and-fall-back)
- [8. Adapt without weakening the gates](#8-adapt-without-weakening-the-gates)

## 1. Establish the evidence contract

For each subproblem, record in `reports/traceability.md`:

- the requested target, decision, or prediction and its unit;
- observed inputs, latent quantities, controls, and outputs;
- the evidence needed to support the final claim;
- dependencies on other subproblems and shared data or parameters;
- the executable result, validation artifact, figure/table, and paper section.

Do not select a model from keywords alone. Resolve unknown data semantics before
treating them as assumptions. Mark an unavailable requirement explicitly; do
not replace it silently with a convenient surrogate.

## 2. Build the mechanism ladder

Record the following levels in `reports/mechanism_audit.json`. Stop at the
lowest level that explains the evidence and supports the requested claim.

| Level | Required role |
|---|---|
| `M0` | Empirical, dimensional, or no-mechanism reference |
| `M1` | Minimal core process that links inputs to the target |
| `M2` | Observation process that maps latent state to measured data |
| `M3` | Noise, bias, calibration, boundary, heterogeneity, or other nuisance process |
| `M4` | Higher-order interaction or full mechanism justified by a diagnosed defect |

For every added mechanism, record its evidence source, added assumption,
parameters, expected diagnostic signature, and removal test. Delete, fix, or
label as conditional any mechanism unsupported by data, a known constant, or a
defensible external source.

Do not add `M4` for sophistication. Add it only when a lower level leaves a
predeclared residual pattern, invariant violation, condition-specific bias, or
decision failure that the mechanism could remove.

## 3. Build the candidate-model ladder

Record candidates in `reports/model_decision_log.csv`:

| Level | Required role |
|---|---|
| `C0` | Closed-form, dimensional, naive, or empirical benchmark |
| `C1` | Simplest identifiable model containing the core mechanism |
| `C2` | One evidence-backed mechanism added to its parent model |
| `C3` | Fully coupled model used only when data and diagnostics support it |

For each candidate, specify equations or algorithm, parent model, added
mechanism, new parameters, data demand, expected improvement, computational
cost, identifiability risk, rejection rule, and fallback. Add one mechanism at
a time so that measured improvement has an attributable cause.

Always execute a credible baseline. Reject a stronger candidate when it misses
its predeclared threshold, violates feasibility, or becomes non-identifiable.
Do not call a model innovative merely because it is complex.

## 4. Register parameter roles

Maintain `reports/parameter_registry.csv`. Assign every parameter exactly one
role for each model:

- `shared`: represents the same latent quantity across valid conditions;
- `condition_specific`: represents a real condition-level change;
- `nuisance`: absorbs calibration, scale, offset, noise, or acquisition effects;
- `fixed`: comes from a cited constant or a declared external measurement.

Record symbol, meaning, unit, domain, source, bound/prior, sharing scope,
estimating data, sensitivity, and identifiability verdict. Never force a
nuisance parameter to be shared merely to stabilize a fit. Never let a nuisance
parameter replace the target mechanism without diagnosing the trade-off.

## 5. Audit identifiability before solving

Perform both audits before accepting optimization output.

1. **Structural audit:** check equation/unknown balance, dimensional groups,
   symmetries, invariances, scaling equivalence, and uniquely observable
   parameter combinations.
2. **Practical audit:** check condition coverage, Jacobian or sensitivity rank,
   condition number, profile objective, parameter correlation, boundary hits,
   and multi-start dispersion as applicable.

Assign one verdict per target parameter or identifiable combination:

- `PASS`: identify it at the precision needed for the claim; report an estimate
  and an uncertainty measure supported by the data.
- `CONDITIONAL`: identify it only after fixing parameters, restricting a range,
  or adopting an explicit assumption; state that condition and run sensitivity.
- `FAIL`: do not report a precise estimate; simplify, reparameterize, add an
  informative condition, or report only the identifiable combination/range.

Do not use optimizer convergence, a small residual, or extra decimal places as
evidence of identifiability.

## 6. Design joint inference

When repeated conditions, sensors, periods, regions, or experiments measure a
common latent system, compare separate fits with a joint model. Record the
design in `reports/joint_inference_design.json`.

Define shared parameters, condition-specific parameters, nuisance parameters,
condition coverage, and the scientific reason for each sharing choice. Compare:

1. separate fits;
2. forced sharing where scientifically valid;
3. partial pooling or structured variation when data support it.

Reject forced sharing when it creates systematic condition-level residuals or
hides genuine variation. Treat agreement among separate fits as evidence, not
as automatic permission to average them.

## 7. Select, challenge, and fall back

Select the lowest candidate that is identifiable, passes its failure-oriented
test, and answers the subproblem. Predeclare the stronger candidate's advantage
and threshold in `reports/model_challenge.json`. Preserve an executable fallback
in `reports/fallback_plan.csv`.

Before admitting a selected model, require:

- a mechanism-to-observation chain with no unresolved semantic gap;
- an identifiability verdict consistent with the claim precision;
- a measured comparison against its parent or baseline;
- a model-family diagnostic and a proportionate stress test;
- an independent check under the rules in
  `diagnostics-and-result-reconciliation.md` when truth is unavailable;
- reconciliation of material disagreement before freezing values.

## 8. Adapt without weakening the gates

- For prediction, treat feature generation, sampling, leakage, and measurement
  as the observation process; use time- or group-safe validation.
- For optimization, map mechanisms to objectives and constraints; use an
  independent feasibility checker and small-case or relaxation bounds.
- For ranking, audit indicator semantics, normalization, weighting, and rank
  reversal; do not interpret association as mechanism.
- For simulation, check conservation, calibration/validation separation,
  replication uncertainty, and grid or time-step convergence.
- For inverse or physical measurement problems, also read
  `physics-inverse-modeling-playbook.md`.

Keep the gates intact when an adapter is unavailable. Record a scoped
limitation and narrow the claim instead of declaring an inferred pass.
