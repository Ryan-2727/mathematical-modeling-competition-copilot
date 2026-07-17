# Reviewer scorecard and presentation

Use only after the complete paper exists and the user accepts the optional
post-paper award review. The scorecard is an internal 1-5 diagnostic, not an
official judging formula or award prediction.

## Three independent passes

1. Model reviewer: assumptions, mechanism, abstraction, model choice, and useful
   problem-specific creativity.
2. Evidence reviewer: executed provenance, correctness checks, uncertainty,
   stress tests, and whether conclusions exceed the evidence.
3. Paper reviewer: answer localization, abstract quality, notation, visual
   legibility, narrative economy, and practical interpretation.

Complete `reports/reviewer_scorecard.csv` for four dimensions:
`assumption_rationality`, `model_creativity`, `result_correctness`, and
`writing_clarity`. Every score needs evidence, the strongest objection, and the
smallest credible fix.

## Reader-first presentation

- The abstract maps each subproblem to method, quantitative answer, validation,
  and practical meaning; it does not read like a table of contents.
- The first paragraph of each subproblem states what is being decided or
  explained and what output will answer it.
- Every figure has one claim, readable labels and units, a source result file,
  and nearby interpretation.
- Put exact recommendations, parameter values, scenario comparisons, and error
  metrics in tables; use figures for shape, mechanism, uncertainty, and tradeoff.
- Remove derivations, visuals, and model names that do not change a conclusion.

Prefer at most three revisions with the highest expected judging benefit per
hour. Rebuild and reverify every accepted change.
