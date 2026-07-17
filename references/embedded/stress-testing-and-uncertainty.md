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

## Acceptance criteria

State the expected invariant or acceptable degradation before running the test.
Report a failed test honestly. Narrowing a claim is better than hiding fragility.
Do not label arbitrary parameter changes as robustness without a plausible range
or source. Use a resolved verdict such as `pass`, `resolved`, `claim_narrowed`,
or `accepted_limitation`; a raw failed or inconclusive verdict cannot pass the
award-readiness gate until its implication is reflected in the claim and paper.
