# Award-oriented evidence chain

Use this playbook to make strong contest-paper conclusions traceable, challengeable,
and implementable. These gates do not predict an award or prove mathematical truth.

## Claim chain and rebuild rule

For each decisive recommendation, add one `reports/evidence_chain.csv` row:

```text
claim_id,code_or_command,source_data,data_sha256,result_file,result_sha256,verified_value_key,latex_macro,figure_label,paper_location,status
```

The `latex_macro` is exactly `\VerifiedValue{<verified_value_key>}` and must be
reachable from the paper. Hash each bound data/result file. If a bound result hash
changes, regenerate verified values and figures, rebuild LaTeX, and rerun the
evidence-chain verifier; do not patch a number in prose.

## Refutation and fallback

For every subproblem, `reports/model_challenge.json` records an interpretable
baseline, one candidate, metric direction, predeclared relative-improvement
threshold, failure-oriented test, result artifact, selection, and conclusion
status. Retain a candidate only when its measured advantage clears the threshold
or a mechanism-specific justification narrows the claim.

`reports/fallback_plan.csv` records a primary route, trigger, fallback route,
result artifact, and paper boundary statement for timeout, infeasibility,
numerical instability, or insufficient data. A fallback is not an excuse to hide
failure: describe the supported scope in the paper.

When a fallback removes noncritical factors, stop and ask the user before
simplifying. Record the authorization, retained mechanism, removed factors,
result artifact, and `model_optimization` treatment of the original route in
`reports/model_simplification_log.csv`.

## Decision, causality, and figures

`reports/decision_robustness.csv` compares expected-value and robust, stochastic,
or scenario policies when uncertainty is material. Report scenario count, extreme
feasibility rate, policy changes, and interpretation. `reports/implementation_readiness.csv`
records inputs, cost, time, interpretability, failure mode, and contingency.

For a causal row in `reports/causal_claims.csv`, provide an estimand, causal graph,
confounders, counterfactual, identification strategy, and diagnostic. If evidence
does not support these, use `predictive` or `association` and state the causal
limitation.

Each figure-manifest row must also contain `claim_id`, `question_answered`,
`reader_takeaway`, and `decision_relevance`. Keep only figures that advance a
claim or decision.

Use `reports/visual_storyboard.csv` to ensure every answered subproblem has a
result chart and every baseline/candidate comparison has a comparison visual or
table. Add mechanism, path/network, and validation visuals only when relevant.

## Final commands

```powershell
python scripts/verify_evidence_chain.py --project-dir .
python scripts/verify_decision_quality.py --project-dir .
python scripts/verify_figure_narrative.py --project-dir .
python scripts/verify_page_readability.py --project-dir .
python scripts/verify_abstract_structure.py --project-dir .
python scripts/verify_result_story.py --project-dir .
```

Complete the human page checklist after inspecting the rendered PDF. Its fields
cover abstract density, first formula definitions, figure legibility, blank space,
table breaks, appendix boundaries, and reference consistency.
