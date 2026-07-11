# LaTeX Paper Pipeline

This is the executable contract for Chinese competition papers.

## Source layout

Use one `main.tex`, ordered section files, one references file, and an appendix
file. Keep figures in `figures/` and use paths relative to `main.tex`. Do not create
generated include files that hide figure or section references.

## Minimum paper elements

1. Abstract page with title, concise method, subproblem results, validation, and
   keywords.
2. Problem restatement with no copied long passages.
3. Assumptions and notation table before first use of symbols.
4. One subsection per subproblem, each containing model purpose, derivation,
   algorithm, result, and interpretation.
5. At least one independent validation or sensitivity check for each primary model.
6. Strengths, limitations, references, and runnable-code appendix.

## Figure and table policy

Create a figure/table plan from the executed results before writing prose. A useful
plan maps each visual to a claim:

```text
claim -> source result -> visual type -> paper section -> caption -> in-text reference
```

Prefer a small number of information-dense visuals over repeated plots. Typical
roles are: data distribution/preprocessing, model mechanism or workflow, fit or
prediction versus observations, residual/error, sensitivity/robustness, and final
scenario comparison. Add a table for exact values, parameter definitions, model
comparison, or scenario recommendations. Do not force every role when the problem
does not support it.

## Build and QA

```powershell
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

After compilation, check missing references, missing graphics, overfull boxes,
placeholders, page count, abstract-page fit, figure/table captions, and accidental
identity or local-path disclosure. If XeLaTeX or a PDF rasterizer is unavailable,
record the exact limitation in `reports/verification_report.md`.
