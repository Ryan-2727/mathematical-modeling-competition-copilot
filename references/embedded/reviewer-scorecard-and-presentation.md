# Reviewer scorecard and presentation

Use only after the complete paper exists and the user accepts the optional
post-paper award review. The scorecard is an internal 1-5 diagnostic, not an
official judging formula or award prediction.

## Three independent passes

1. Model reviewer: assumptions, mechanism, abstraction, model choice, and useful
   problem-specific creativity.
2. Evidence reviewer: executed provenance, correctness checks, uncertainty,
   stress tests, and whether conclusions exceed the evidence.
3. Editorial reviewer (`writing`): answer localization, abstract and conclusion
   prominence, notation/formula readability, figure/table visual hierarchy,
   narrative pacing, page balance, and practical interpretation. Every finding
   names a PDF page, figure/table label, equation, or source-section locator.

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

Run `verify_answer_density.py`, `verify_visual_design_system.py`, and
`verify_paper_presentation.py` before this optional review. Their reports record
structural evidence and completed rendered-page checks; they do not replace the
editorial review or claim to measure beauty.
