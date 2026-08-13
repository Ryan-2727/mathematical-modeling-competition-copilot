# Mechanism, semantics, validation, and argument

Use this playbook to prevent a plausible-looking model from resting on a wrong
data interpretation, untestable claim, buried answer, or cosmetic innovation.

## Mechanism and data semantics

Complete `reports/semantic_audit.csv` before model selection. Each material data
representation receives a stable `semantic_id`, dataset/field, raw form,
operational semantic type, decision impact, evidence, alternative treatment,
sensitivity need, and the subproblem that uses it. Allowed semantic types are
`observed_zero`, `structural_zero`, `no_opportunity`, `not_observed`,
`censored_not_detected`, `missing`, and `not_applicable`.

Complete `reports/mechanism_audit.json` with each subproblem's mechanism,
assumptions, semantic IDs, falsifiable implication, and result artifact. A data
encoding is not a modeling assumption until its meaning and consequence are
explicit. Preserve alternate credible treatments in sensitivity analysis.

Before solving, apply `model-reasoning-kernel.md`. Record the mechanism and
candidate-model ladders in `reports/model_decision_log.csv`, every estimated or
fixed parameter in `reports/parameter_registry.csv`, and any repeated-condition
sharing decision in `reports/joint_inference_design.json`. Promote a model only
when its added mechanism has evidence, a predicted diagnostic signature, and an
identifiability status other than `FAIL`.

## Small-sample or no-ground-truth validation

Use `reports/validation_design.csv` to state whether truth is external, partial,
or unavailable. For unavailable truth, combine at least two independent checks:
conservation/invariant, small-case enumeration, historical backtest, cross-model
agreement, synthetic recovery, expert rule, or stress test. Record a metric,
baseline/invariant, acceptance rule, result artifact, and remaining limitation.
These checks restrict a claim; they never manufacture an accuracy label.
Name the routes in `reports/independent_routes.csv`; a numeric count alone does
not establish independence.

## Conclusion-first paper chain

In `reports/conclusion_map.csv`, each subproblem states the question, direct
answer/recommendation, decisive verified-value key, method rationale, validation,
limitation, figure/table, and paper location. Write the answer where a reviewer
expects it, then justify it—do not hide it after pages of method description.

## Minimal powerful innovation

Use `reports/innovation_ledger.csv` for one problem-specific change at a time:
identify the baseline, mechanism target, added assumption, incremental cost,
predeclared comparison metric/threshold, measured relative improvement,
validation artifact, and claim boundary. A complicated algorithm is not an
innovation by itself. If measured gain misses the threshold, mark the change
`interpretive_only` or `rejected` and do not call it an improvement.

Run:

```powershell
python scripts/verify_modeling_argument_quality.py --project-dir .
```
