# Result-First Paper Convergence

## Abstract

Write a concise analysis-method-result abstract in exactly three explicit blocks:

1. `问题分析` / `Analysis`: identify the decision, mechanism, data boundary, and
   task decomposition.
2. `建模方法` / `Method`: name only the methods that produced the reported
   results and explain their role.
3. `主要结果` / `Results`: state direct, quantitative answers or recommendations;
   do not write only “a model was established” or “the effect is good”.

Keep validation and limitation language compact. Run
`verify_abstract_structure.py` and `verify_answer_density.py` after drafting.
Write result numbers through `\VerifiedValue{key}` or
`\VerifiedValueWithUnit{key}`. Apply the same rule to the conclusion. A raw
question number, calendar date, formula index, or official limit may remain only
after exact line-level registration in `reports/numeric_exemptions.csv`. Run
`verify_summary_numeric_traceability.py`; do not hand-copy a computed number.

## Result before complexity

Start from the simplest credible baseline, execute it, and preserve a verified
result artifact before adding complexity. If the primary route times out, has no
feasible solution, is numerically unstable, or cannot produce a defensible
result, record its diagnostic in `reports/model_simplification_log.csv` and
stop. Ask the user whether to simplify by removing named noncritical factors.

Only after explicit user authorization may the workflow simplify. Retain the
core mechanism and constraints; list every removed factor, expected limitation,
and the resulting artifact. Present the original, unexecuted route only as
`模型优化` / `model_optimization`; never present its unverified value as a result.
If authorization is withheld, state the boundary and do not invent an answer.

## Visual evidence portfolio

Plan visuals in `reports/visual_storyboard.csv`. Each subproblem needs a
result chart. Add the following only where they answer a real reader question:

- mechanism/flow diagram for system structure or algorithm logic;
- path/network diagram for route, spatial, graph, or scheduling decisions;
- model-comparison chart or table whenever a baseline and candidate are compared;
- validation or uncertainty chart where robustness changes the conclusion.

More figures are not automatically better. Prefer readable, high-resolution,
consistent figures with a single conclusion each, nearby interpretation, and
traceable source results. Run `verify_result_story.py` before final freeze.
