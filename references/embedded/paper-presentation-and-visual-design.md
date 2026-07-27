# Paper Presentation And Visual Design

Use this module after the paper is complete enough to compile. It improves
reader-facing quality through evidence-backed revision; it does not assign an
aesthetic score or predict an award.

## One visual system

Choose one named `style_profile` for all figures and tables. Record it in the
manifests along with visual role, palette/grayscale strategy, typography and
numeric-precision check, panel order, units, and a legibility locator. Use a
figure to show shape, mechanism, uncertainty, or trade-off; use a table for
exact values, scenarios, parameter settings, and recommendations. Every visual
must answer one question and support one named claim.

## Answer-first prose

The abstract and conclusion must answer each subproblem directly. Each answer
needs a decisive value or recommendation, a method/result locator, validation,
and a limitation. Prefer a compact sequence: decision or conclusion preview,
mechanism, model, result, validation, and practical meaning. Remove a formula,
paragraph, or visual that does not change a reader's understanding of a claim.

## Rendered-page review

After compiling, complete `reports/presentation_checklist.csv` for every page.
Check hierarchy, readable fonts, orphaned headings/captions, formula breaks,
table continuation, whitespace balance, and visual consistency. Mark an item
`not_applicable` only when it genuinely does not occur on that page. Run:

```bash
python scripts/verify_answer_density.py --project-dir .
python scripts/verify_visual_design_system.py --project-dir .
python scripts/verify_paper_presentation.py --project-dir .
```

An unavailable optional PDF extractor is `LIMITED`; manually recorded evidence
remains required. Rerun all three checks after any manuscript, table, or figure
change.

## Independent review packet

Use three independent passes: `model`, `evidence`, and `writing`. The writing
reviewer is an editorial reviewer: inspect answer prominence, narrative pacing,
notation/formula readability, visual hierarchy, captions, tables, and page
balance. Every objection must name a page, figure/table label, equation, or
source location. Do not share one reviewer's findings with another reviewer
before aggregation, and do not request award forecasts.
