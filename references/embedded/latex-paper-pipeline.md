# LaTeX Paper Pipeline

This is the executable contract for Chinese competition papers.

## Source layout

Use one `paper/main.tex`, ordered section files, `paper/references.bib`, and an
appendix file. Keep figures in a stable project folder and use portable relative
paths. Preserve every local class, style, font, table, and asset required to rebuild
`paper/main.pdf`. Do not create generated include files that hide figure or section
references.

When LaTeX source is delivered to a user, create a second, self-contained source
tree and ZIP its *contents* rather than its parent directory. The ZIP root must be:

```text
main.tex
README.md
.latexmkrc
.vscode/settings.json
sections/*.tex
figures/<referenced files>
code/<referenced files>
references.bib
<local .cls/.sty/table/data assets when referenced>
```

`main.tex` is the only entrypoint. Add these first lines:

```latex
% !TeX program = xelatex
% !TeX encoding = UTF-8
```

Use `sections/...`, `figures/...`, and `code/...` paths from that root for
`\input`, `\includegraphics`, and `\lstinputlisting`. Do not use `..`, a drive
letter, a user directory, or a path outside the archive. Keep the canonical
workspace layout if useful, but copy every required dependency into the portable
source tree before packaging.

## VS Code and Overleaf compatibility

Include `.vscode/settings.json` with a XeLaTeX two-pass recipe. It must use
`%DOCFILE%` rather than a Windows absolute path, place output in `%DIR%`, and
use the internal tab viewer:

```json
{
  "latex-workshop.latex.outDir": "%DIR%",
  "latex-workshop.latex.tools": [{
    "name": "xelatex",
    "command": "xelatex",
    "args": ["-synctex=1", "-interaction=nonstopmode", "-file-line-error", "%DOCFILE%"]
  }],
  "latex-workshop.latex.recipes": [{
    "name": "XeLaTeX × 2",
    "tools": ["xelatex", "xelatex"]
  }],
  "latex-workshop.latex.recipe.default": "first",
  "latex-workshop.view.pdf.viewer": "tab",
  "latex-workshop.view.pdf.tab.editorGroup": "right"
}
```

Include `.latexmkrc`:

```perl
$pdf_mode = 5;
$xelatex = 'xelatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
```

README must state: open the whole folder in VS Code, build the root `main.tex`
with `XeLaTeX × 2`, and use `Ctrl+Alt+V` or **LaTeX Workshop: View LaTeX PDF
file** to preview. For Overleaf, upload the whole ZIP, choose XeLaTeX, and set
the root `main.tex` as the main document. Do not claim that a remote Overleaf
account was used unless it actually was.

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

## Build and QA

```powershell
Push-Location paper
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
biber main  # use bibtex main instead when the template selects BibTeX
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
Pop-Location
```

Treat a fatal command, undefined citation/reference, missing graphic, or absent
`paper/main.pdf` as a failed build. After compilation, inspect the log and rendered
PDF for overfull boxes, placeholders, page count, abstract-page fit, page order,
font substitution, clipped equations/tables, figure/table captions, and accidental
identity or local-path disclosure. Run `scripts/verify_paper_delivery.py` only after
building the support archive. If XeLaTeX, the bibliography backend, or a PDF
rasterizer is unavailable, record the exact limitation in
`reports/verification_report.md` and do not call the paper complete.

After making the portable ZIP, run:

```powershell
python scripts/verify_portable_latex.py --archive output/paper-latex-source.zip --out reports/portable_latex_verification.json --compile
```

The script checks the archive root, VS Code configuration, XeLaTeX declarations,
relative file references, README instructions, and—when `--compile` is used—a
fresh-directory two-pass XeLaTeX rebuild. Inspect the produced PDF separately;
the script validates structure and local compilation, not remote Overleaf UI state.
