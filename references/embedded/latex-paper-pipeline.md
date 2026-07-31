# LaTeX Paper Pipeline

This is the executable portable-paper contract for CUMCM and MCM/ICM. The
selected current official contest profile overrides all template defaults.

## Contents

- [Source layout](#source-layout)
- [VS Code and Overleaf compatibility](#vs-code-and-overleaf-compatibility)
- [Minimum paper elements](#minimum-paper-elements)
- [Reference integrity](#reference-integrity)
- [Figure and table policy](#figure-and-table-policy)
- [Overleaf build](#overleaf-build)
- [VS Code build and preview](#vs-code-build-and-preview)
- [Compatibility and visual QA](#compatibility-and-visual-qa)

## Source layout

Initialize the contest project with `scripts/init_contest.py`; it chooses the
`cumcm` or `mcm-icm` portable tree from the contest name when `paper/` is empty.
To add a selected tree to an existing project, run:

```powershell
python scripts/scaffold_latex_paper.py --project-dir <contest-project> --template cumcm
python scripts/scaffold_latex_paper.py --project-dir <contest-project> --template mcm-icm
```

Never use `--force` on a nonempty paper tree unless the user explicitly intends
to replace those files. The CUMCM template and MCM/ICM template encode different
first-page, header, appendix, support-file, and AI-report structures; they are
not interchangeable formatting themes.

The generated contract is:

```text
paper/
|-- main.tex
|-- README.md
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

When LaTeX source is delivered to a user, create a second, self-contained source
tree and ZIP its *contents* rather than its parent directory. The ZIP root must be:

```text
main.tex
README.md
.latexmkrc
.vscode/settings.json
.vscode/extensions.json
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

Include `.vscode/settings.json` with the canonical latexmk XeLaTeX recipe. It
must use `%DOC%` rather than a Windows absolute path, pass
`-outdir=%OUTDIR%`, place output in `%DIR%/build`, and use the internal tab
viewer:

```json
{
  "latex-workshop.latex.outDir": "%DIR%/build",
  "latex-workshop.latex.tools": [{
    "name": "latexmk-xelatex",
    "command": "latexmk",
    "args": [
      "-xelatex",
      "-synctex=1",
      "-interaction=nonstopmode",
      "-halt-on-error",
      "-file-line-error",
      "-outdir=%OUTDIR%",
      "%DOC%"
    ]
  }],
  "latex-workshop.latex.recipes": [{
    "name": "latexmk (XeLaTeX)",
    "tools": ["latexmk-xelatex"]
  }],
  "latex-workshop.latex.recipe.default": "first",
  "latex-workshop.view.pdf.viewer": "tab",
  "latex-workshop.view.pdf.tab.editorGroup": "right"
}
```

Include `.latexmkrc`:

```perl
$pdf_mode = 5;
$xelatex = 'xelatex -synctex=1 -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
$bibtex_use = 2;
```

README must state: open the whole folder in VS Code, build the root `main.tex`
with `latexmk (XeLaTeX)`, and use `Ctrl+Alt+V` or **LaTeX Workshop: View LaTeX
PDF file** to preview `build/main.pdf`. For Overleaf, upload the whole ZIP,
choose XeLaTeX, and set the root `main.tex` as the main document. Do not claim
that a remote Overleaf account was used unless it actually was.

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

After making the portable ZIP, run:

```powershell
python scripts/verify_portable_latex.py --archive output/paper-latex-source.zip --out reports/portable_latex_verification.json --compile
```

The script checks the archive root, VS Code configuration, XeLaTeX declarations,
relative file references, README instructions, and—when `--compile` is used—a
fresh-directory two-pass XeLaTeX rebuild. Inspect the produced PDF separately;
the script validates structure and local compilation, not remote Overleaf UI state.
