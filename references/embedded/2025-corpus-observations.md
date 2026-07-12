# Observations from the 2025 national competition paper corpus

This file records transferable observations extracted from the local corpus
`F:\2025zjhychn\2025年高教社全国大学生数学建模竞赛优秀论文`. The PDFs are reference
evidence, not contest-time inputs and not templates to copy verbatim.

## Corpus profile

The corpus contains seven papers: A196, B060, B157, C023, C132, D037, and E030.
Measured page counts are 98, 72, 67, 122, 65, 37, and 36 respectively; the
range is 36--122 pages. All inspected PDFs report the same compact page size of
252 x 356.04 pt. The variation in length is evidence against imposing a universal
page, figure, table, or equation quota.

## Repeated structure

Visual inspection of the first three pages across different task types shows a
stable reader path:

1. page 1: title, one-page abstract, question-by-question methods and results,
   conclusion-oriented keywords;
2. page 2: `问题重述`, normally split into background and question requirements;
3. page 2 or 3: `问题分析`, followed by assumptions/notation or the first model;
4. later pages: each subproblem keeps its own model, algorithm, computed result,
   and interpretation together.

## Repeated writing strengths

- The abstract names the model or algorithm and reports concrete outputs instead
  of saying only that a model was established.
- The problem restatement reduces a long statement to the variables, conditions,
  and deliverables needed by the solution.
- The problem-analysis section explains why the model fits the mechanism and
  previews the solution path before equations become dense.
- Restrictive assumptions are explicit and tied to a later simplification.
- Results are interpreted in practical language after formulas, tables, and plots.
- Validation is visible: fitting error, residuals, consistency checks, sensitivity,
  robustness, or a comparison of alternative solution routes.

## Repeated visual roles

The corpus uses visuals as part of the argument rather than decoration. Common
roles include a physical/process schematic in the restatement, a model mechanism
or workflow diagram in the analysis, data distribution or preprocessing evidence,
fit/prediction or route/network results, error/sensitivity analysis, and a final
scenario or recommendation table. Captions identify the object and the paragraph
after the visual explains its implication.

## Rules learned by the skill

- Plan each figure/table from a claim and an executed result source.
- Use a table for exact values and a figure for patterns or behavior.
- Avoid adjacent visuals without interpretation and avoid plots that repeat the
  same claim.
- Make the abstract and conclusion answer the original numbered questions.
- Preserve the contest format, anonymity, and reproducibility requirements before
  imitating any soft style preference.

