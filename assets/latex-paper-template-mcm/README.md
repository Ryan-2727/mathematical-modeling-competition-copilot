# Portable MCM/ICM LaTeX paper

Set `\TeamControlNumber` and `\ProblemChoice` in `main.tex`. Replace the first
page with the current official COMAP Summary Sheet if its fields differ. Keep
the solution in English and retain the 12-point document declaration.

## VS Code

1. Open this whole folder in VS Code.
2. Install the recommended LaTeX Workshop extension.
3. Open `main.tex`; the `latexmk (XeLaTeX)` recipe builds on save.
4. Use `Ctrl+Alt+V` to preview `build/main.pdf` in a VS Code tab.

## Overleaf

Upload the folder contents so `main.tex` is at the Overleaf project root.
Select XeLaTeX as the compiler and `main.tex` as the main document.

## Submission boundary

The Summary Sheet, table of contents, solution, references, notes, appendices,
and code all count toward the 25-page solution limit. Do not submit a separate
code, data, or support archive. If AI was used, set
`\includeaireporttrue`, complete `sections/ai_report.tex`, cite the AI tool
inline and in the references, and keep the AI report after the counted
solution. Rename the final PDF to the seven-digit control number before running
`verify_submission.py --profile mcm-icm-current`.
