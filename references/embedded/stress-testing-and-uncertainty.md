# Stress testing and uncertainty

Every decisive conclusion needs one proportionate test that could have changed
the conclusion. Record it in `reports/stress_tests.csv` before seeing the final
outcome; otherwise the test risks becoming decorative.

## Select the test by claim

- Parameter-dependent claim: local sensitivity plus a plausible joint scenario.
- Data-dependent claim: holdout, rolling backtest, bootstrap, or source
  substitution consistent with the data-generating process.
- Optimization claim: resource/cost perturbation, constraint removal, small-case
  enumeration, and solver-gap or multi-start evidence.
- Ranking claim: weight perturbation, normalization alternative, and rank
  reversal analysis.
- Simulation claim: replication confidence interval, seed stability, and
  convergence with run length or sample count.
- Mechanistic claim: initial/boundary perturbation, parameter identifiability,
  and step-size or grid refinement.

## Decision uncertainty

When supplies, demand, prices, parameters, or outputs are materially uncertain,
define their plausible ranges and source before optimization. Compare the
mean-input or expected-value baseline with a robust, stochastic, or explicitly
enumerated scenario policy that matches the decision mechanism. Report the
trade-off (for example expected objective, worst-case loss, feasibility rate, or
tail risk) and narrow the recommendation if the policy changes. A mean-only
solution may remain a baseline, but is not the final recommendation when the
decision reverses across plausible scenarios.

## Acceptance criteria

State the expected invariant or acceptable degradation before running the test.
Report a failed test honestly. Narrowing a claim is better than hiding fragility.
Do not label arbitrary parameter changes as robustness without a plausible range
or source. Use a resolved verdict such as `pass`, `resolved`, `claim_narrowed`,
or `accepted_limitation`; a raw failed or inconclusive verdict cannot pass the
award-readiness gate until its implication is reflected in the claim and paper.
