# Exemplar-Driven Paper Writing

Use this module when a problem is paired with an award-winning or publicly displayed
paper. The exemplar is a structural and presentation reference, not a source of
unverified mathematics or numbers.

## Required input contract

Create `reports/exemplar_manifest.yml` before drafting. Each pair must identify:

```yaml
contest: CUMCM
year: 2025
pairs:
  - problem_id: B
    problem_file: data/raw/B题/B题.pdf
    attachments_dir: data/raw/B题/附件
    exemplar_source: https://dxs.moe.gov.cn/...
    exemplar_id: B060
    exemplar_local_dir: data/exemplars/B060
    source_status: public-display-images
```

Never infer that a paper is excellent from an arbitrary web copy. Record the
publisher or organizing body, the URL, access date, page count, and whether the
source is a PDF or page images.

## Baseline-to-exemplar loop

For each pair, perform the following loop and save one report per iteration:

1. Solve the problem with the current workflow and produce executed code, results,
   figures, and a LaTeX paper. Do not inspect the exemplar until the baseline is
   frozen.
2. Run `scripts/exemplar_metrics.py` on the exemplar and the generated PDF/source.
3. Compare problem coverage, model traceability, validation evidence, abstract
   completeness, section order, equation/figure/table usage, page budget, and
   appendix reproducibility. Record evidence, not impressions.
4. Select at most three high-impact gaps. Change the skill instructions or a
   reusable script only when the gap is generalizable to future problems.
5. Re-run the same problem with the revised skill, then compare the new scorecard.
6. Mark the iteration as `improved`, `unchanged`, or `blocked`; a blocked iteration
   must state the missing input or unavailable tool.

The exemplar must not leak into the model as a hidden answer. Use it to learn
organization, explanation density, validation patterns, and figure/table roles.

## 2025 Chinese-paper profile

For the 2025 national Chinese competition, use the official format as the hard
constraint and the paired exemplar as the soft style constraint:

- Electronic paper starts with a one-page abstract, followed by the main text;
  omit the commitment and number-only pages from the electronic file.
- Keep the main text near the 20-page target, with appendices after the main text.
- Use a problem-oriented narrative: restatement, assumptions/notation, data
  processing, model establishment and solution by subproblem, results/analysis,
  sensitivity or robustness, strengths/weaknesses, references, appendices.
- Every figure and table has a caption, a label, a unit/source note where needed,
  and a nearby paragraph explaining its role. Figures are not decorative filler.
- Put complete runnable code and support-material inventory in the appendix or
  support-material package as required by the contest.
- Do not include team, school, region, local paths, temporary filenames, or hidden
  work-product names in the submitted paper.

Observed public 2025 B060 exemplar characteristics are recorded only as a
benchmark, not a universal quota: 72 paper pages, a one-page abstract, numbered
main-text pages, a visible problem-restatement/problem-analysis transition, and
multiple data-driven figures/tables distributed through the solution. The exact
number of figures and tables must be measured from the local exemplar and justified
by the problem, not copied as a fixed target.

## LaTeX writing contract

Use XeLaTeX for Chinese papers. Keep the entry file small and explicit:

```text
paper/main.tex
paper/sections/01_abstract.tex
paper/sections/02_restatement.tex
paper/sections/03_assumptions_notation.tex
paper/sections/04_model.tex
paper/sections/05_results.tex
paper/sections/06_robustness.tex
paper/sections/07_strengths_limitations.tex
paper/references.tex
paper/appendix_code.tex
```

Use `\input` in numeric order. Use `\label`/`\ref` for every numbered equation,
figure, and table. Generate all numbers from the executed result files; never type
an attractive number into the paper after the fact. Compile twice with XeLaTeX,
then run the writing checks and render PDF pages for visual inspection when the
runtime is available.

## Comparison scorecard

Score each item 0 (missing), 1 (present but weak), or 2 (clear and evidenced):

| Dimension | Evidence to inspect |
| --- | --- |
| Task coverage | Every subproblem has an explicit answer and result |
| Model traceability | Variables, assumptions, equations, code, and results connect |
| Validation | Error, residual, sensitivity, robustness, or cross-check is executed |
| Abstract | Method, key results, validation, and practical conclusion fit one page |
| Narrative | Section order follows the problem and avoids method dumping |
| Figures/tables | Each is readable, numbered, sourced, and interpreted |
| LaTeX hygiene | Compiles; references resolve; no placeholders or leaked paths |
| Reproducibility | Code, data inventory, and environment notes are supplied |

Do not claim that a paper is “as good as” the exemplar from this score alone. Use
the score to prioritize the next revision and preserve a short evidence log.
