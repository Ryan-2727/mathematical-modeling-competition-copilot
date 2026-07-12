# Learning paper craft from an exemplar corpus

This module describes an offline learning pass over a folder of excellent
competition papers. It teaches reusable writing decisions; it does not make
excellent papers an input to a live contest solution and it does not require a
problem-to-paper pairing.

## Offline corpus pass

When a reference corpus is available, profile it once before solving new problems.
Record only reusable observations in `references/` or a project report:

1. Render the first three pages and representative middle/end pages of every PDF.
2. Measure page count, page size, abstract length, section hierarchy, figure/table
   roles, equation density, validation patterns, appendix/code treatment, and
   header/footer behavior.
3. Sample at least two papers from different task types. Do not generalize from a
   single paper or from a fixed figure count.
4. Convert observations into rules with evidence and exceptions. Keep the source
   PDFs outside the skill repository unless redistribution is authorized.

Use `scripts/paper_corpus_metrics.py --pdf-dir <corpus> --recursive --out <report.json>` for
repeatable page-count and page-size measurements. Because many competition papers
are scanned PDFs, do not assume text extraction is complete; visual inspection is
the authority for layout, and OCR is only an aid for semantic indexing.

## Live contest boundary

During a real contest, the agent must solve from the statement, data, and permitted
references. The corpus profile may guide writing quality, but the agent must not
search for or use a paper that solves the current problem. If the user asks for a
post-hoc critique, finish and freeze the independently generated solution first;
only then compare it with reference papers.

## Generalizable structure

Use the following as a default outline and adapt it to the number and type of
subproblems:

1. **Abstract page**: state the practical problem, the main model for each task,
   key numerical results, validation/robustness evidence, and the practical
   conclusion. End with focused keywords. Do not repeat background without results.
2. **Problem restatement**: translate the statement into decision variables,
   inputs, outputs, and subproblem questions. Preserve conditions and units but
   avoid copying long passages.
3. **Problem analysis**: explain the mechanism and why the selected model answers
   each question. State the data path and the planned validation before displaying
   long derivations.
4. **Assumptions and notation**: list only assumptions used later and define every
   symbol before or at first use. Explain the practical meaning of restrictive
   assumptions.
5. **Model and solution by subproblem**: for each question, keep the chain visible:
   purpose -> variables -> equations/objective -> algorithm -> computed result ->
   interpretation. Do not create a method catalogue detached from the question.
6. **Validation and robustness**: show residual/error checks, independent
   cross-checks, sensitivity, ablation, uncertainty, or scenario analysis. Explain
   what passed, what changed, and what limitation remains.
7. **Conclusions**: answer the original questions directly, then give strengths,
   weaknesses, and realistic extensions. Put runnable code and support-material
   inventory in the appendix as required.

## Figure and table grammar

Plan visuals from claims, not from a target count:

```text
claim -> result/data source -> visual role -> section -> caption -> interpretation
```

Prefer one clear visual per claim. Common roles observed across strong papers are:

- context or mechanism schematic when the reader needs a physical/process model;
- data cleaning, distribution, correlation, or feature-selection visual;
- model workflow or algorithm flowchart for a multi-stage method;
- observed-versus-fitted/predicted curve, spatial route, or network diagram;
- residual/error, sensitivity, robustness, or method-comparison visual;
- final scenario/ranking/decision table with units and actionable values.

Every visual must have a number, concise caption, readable axes/legend, units and
source note when appropriate, and a nearby paragraph that says what the reader
should learn from it. Do not place consecutive visuals without analysis. Tables are
for exact values, definitions, parameter settings, comparisons, or recommended
plans; plots are for patterns, trends, uncertainty, and model behavior.

## 2025 Chinese-paper style profile

Use the official 2025 format as the hard constraint and the corpus as a soft style
constraint:

- Page 1 is a result-rich abstract with keywords; page 2 normally begins the main
  text with problem restatement. Do not add a table of contents.
- Use clear Chinese section headings, stable numbering, centered page numbers,
  consistent margins, and a compact academic layout.
- Keep the main text close to the contest target rather than padding it with code
  or repeated plots. Put code and long intermediate outputs in appendices/support
  materials.
- Make the abstract and each section answer “what was done, why, and what was
  obtained.” Bold or otherwise emphasize only genuinely important results.
- Use XeLaTeX with an explicit `main.tex`, ordered section files, `\label`/`\ref`,
  and data generated from executed result files.

The corpus contains different lengths and visual densities; therefore the skill
must not impose a universal number of pages, figures, tables, or equations. It must
choose the smallest set that covers the claims and remains readable.

## Independent improvement loop

When improving the skill itself, use this order:

1. Select a problem and solve it independently with the current skill.
2. Freeze the source, results, figures, and LaTeX paper; record the baseline.
3. Compare the baseline against the corpus profile on structure, explanation,
   validation, figure/table grammar, and LaTeX quality. Do not copy the exemplar's
   wording, numbers, model, or figures.
4. Select no more than three generalizable gaps and revise the skill instructions
   or deterministic scripts.
5. Re-solve the same problem from the statement and data, then compare the new
   paper against the baseline. Repeat on another task type.

Store the evidence in `reports/paper_learning_iteration_*.md`; distinguish observed
facts, design rules, and unresolved limitations.
