# LaTeX Paper Pipeline

This is the executable contract for Chinese competition papers.

## Source layout

Initialize the contest project with `scripts/init_contest.py`; it scaffolds the
portable paper tree when `paper/` is empty. To add the tree to an existing project,
run:

```powershell
python scripts/scaffold_latex_paper.py --project-dir <contest-project>
```

The generated contract is:

```text
paper/
|-- main.tex
|-- references.bib
|-- .latexmkrc
|-- .vscode/
|   |-- settings.json
|   `-- extensions.json
|-- sections/
|   |-- abstract.tex
|   |-- problem.tex
|   |-- assumptions.tex
|   |-- model.tex
|   |-- results.tex
|   |-- evaluation.tex
|   `-- conclusion.tex
|-- figures/
`-- build/
```

Use `main.tex` as the only root document and keep ordered section files under
`sections/`. Keep figures under `figures/` and use only portable relative paths.
Preserve every local class, style, table, and asset required to rebuild the PDF.
Use UTF-8, XeLaTeX, portable TeX Live/Fandol fonts, BibTeX in
`references.bib`, and the editor directives already present in `main.tex`. Do not
hard-code a drive letter, user directory, operating-system font, or generated
include file that hides figure or section references.

## Minimum paper elements

1. Abstract page with title, concise method, subproblem results, validation, and
   keywords.
2. Problem restatement with no copied long passages.
3. Assumptions and notation table before first use of symbols.
4. One subsection per subproblem, each containing model purpose, derivation,
   algorithm, result, and interpretation.
5. At least one independent validation or sensitivity check for each primary model.
6. Strengths, limitations, at least 10 unique and relevant scholarly references,
   and a runnable-code appendix or support-package pointer.

## Reference integrity

Read `verified-literature-and-two-part-delivery.md`. Keep all bibliography entries
in `paper/references.bib` and all source evidence in `reports/bibliography.csv`.
Every ledger key must appear in BibTeX and be cited in the LaTeX body; uncited
padding does not count. Verify metadata through an authoritative record and save an
exact-title Google Scholar query, then read and record the passage supporting the
paper's claim. Never generate plausible-looking citations from memory.

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

## Overleaf build

Upload the contents of `paper/` so that `main.tex` is at the Overleaf project
root. In project settings, select `main.tex` as the main document and XeLaTeX as
the compiler. Keep `.latexmkrc`, `references.bib`, `sections/`, and `figures/` in
the upload. The source must compile without a local absolute path or locally
installed proprietary font.

## VS Code build and preview

Open the `paper/` folder in VS Code and install the recommended LaTeX Workshop
extension. The checked-in workspace settings select the
`latexmk (XeLaTeX)` recipe, write generated files to `paper/build/`, preview the
PDF in a VS Code tab, and enable SyncTeX. Saving `main.tex` triggers the build;
use the extension's “View LaTeX PDF” command for preview.

The equivalent terminal checks are:

```powershell
Push-Location paper
latexmk -xelatex main.tex
latexmk -xelatex -outdir=build main.tex
Pop-Location
```

## Compatibility and visual QA

Before delivery, run the compile-backed compatibility gate from the skill
repository:

```powershell
python scripts/verify_latex_compatibility.py `
  --paper-dir <contest-project>/paper `
  --out <contest-project>/reports/latex_compatibility.json
```

The gate statically checks the portable tree, then builds both
`paper/main.pdf` (Overleaf-style project-root build) and
`paper/build/main.pdf` (VS Code-style output-directory build). It records a source
fingerprint so later source edits invalidate the report. A static-only or
tool-limited result is not completion evidence.

Treat a fatal command, undefined citation/reference, missing graphic, stale
compatibility report, or absent PDF as a failed build. After compilation, inspect
the log and both rendered PDFs for overfull boxes, placeholders, page count,
abstract-page fit, page order, font substitution, clipped equations/tables,
figure/table captions, and accidental identity or local-path disclosure. Build
the support archive only after this check, then run
`scripts/verify_paper_delivery.py`. If XeLaTeX, latexmk, BibTeX, or a PDF
rasterizer is unavailable, record the exact limitation in
`reports/verification_report.md` and do not call the paper complete.
