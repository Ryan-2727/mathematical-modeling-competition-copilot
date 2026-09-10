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

Read `local-originality-preflight.md`. Configure the authorized historical
corpus in `reports/originality_config.json`, then run
`scripts/originality_preflight.py`. It expands the complete multi-file LaTeX
paper and reports HIGH/MEDIUM exact and near-match risks in
`reports/originality_preflight.md`, including the draft paragraph, exact source
location, compact source excerpt, metrics, and a human remediation direction.
Resolve each item in `reports/originality_review.csv`; paragraph hashes make
reviews stale after edits. The checker is local, text-only, creates no images,
and never writes replacement or detector-evasion prose. Keep the legacy
`scripts/similarity_preflight.py` only for compatible single-file exact-overlap
checks.

This is not a plagiarism verdict, does not estimate either official
Tongfang/CNKI metric, and cannot establish compliance with a 25% threshold. For
CUMCM 2026, record the two actual official metrics in
`reports/similarity_risk.json` and run `scripts/verify_similarity_risk.py`;
missing official evidence remains `LIMITED`.

## Reasoning narrative gate

Use `reports/paper_reasoning_map.csv` only as a location map; the authoritative
facts remain in the model-decision, parameter, simplification, fallback, result,
and traceability ledgers. Run `scripts/verify_paper_reasoning_narrative.py` to
require model-choice rationale, parameter provenance, failed-route discussion,
or boundary language only when their underlying evidence triggers them. The gate
does not require fixed visible headings and cannot replace a named human prose
review. Pair it with the advisory Chinese style audit, which locates formulaic
patterns but never rewrites text or infers authorship.
