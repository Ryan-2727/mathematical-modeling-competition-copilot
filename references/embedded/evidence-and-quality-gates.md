# Evidence, reproducibility, and argument-quality gates

## Evidence ledger

Maintain `reports/claims.csv`. Each material conclusion needs a claim ID,
subproblem, source result file, source locator, generating command, figure or
table, paper location, human verification, and status. Run
`scripts/verify_claims.py` before freezing. A number without this chain is a
draft, not verified evidence.

## Reproduction

Run the final pipeline through `scripts/run_reproduction.py`. Record the exact
argv command, seed, input/output hashes, exit status, and environment snapshot.
Run in a clean copied project and request at least two runs for the frozen
pipeline. Compare deterministic outputs by SHA-256 and declared numeric outputs
by a preselected tolerance. Expected files must exist after every successful
run. Shell syntax requires explicit `--allow-shell`; never treat a line of text
as trusted shell input by default. Report unavailable solvers or manual software
steps rather than claiming full reproduction.

## Numerical quality

Generate paper-facing values from `results/verified_values.csv` and run
`scripts/verify_verified_values.py`. Then run the applicable adapters in
`scripts/verify_model_validation.py`; their pass confirms that declared
evidence exists and satisfies the recorded threshold, not that the model is true.

Choose the applicable gate and record it in `reports/argument_coverage.csv`:

- optimization: feasibility residual, integrality, solver status, gap or a
  statement that no global guarantee exists;
- forecasting: time-respecting holdout or rolling backtest plus a baseline;
- statistical learning: split/leakage check, uncertainty or resampling, and
  an interpretable baseline;
- simulation: seed, replications, uncertainty interval, and convergence or
  stability check;
- mechanistic dynamics: units, parameter identifiability, initial/boundary
  conditions, and step-size or grid convergence where relevant.

## Argument coverage

For every subproblem, mark these six elements as complete in
`reports/argument_coverage.csv`: decision need or mechanism, model,
solution, quantified result, interpretation, and validation. The checker does
not judge mathematical truth; it stops a paper from silently omitting a link in
the argument chain.

## Originality preflight

Use `scripts/similarity_preflight.py` only on drafts and an offline historical
corpus. It flags unusually long exact phrase overlap for human review. It is
not a plagiarism verdict and must never become a current-problem answer source.
