# Portable LaTeX paper

## VS Code

1. Open this whole folder in VS Code.
2. Install the recommended LaTeX Workshop extension.
3. Open `main.tex`; the default `latexmk (XeLaTeX)` recipe builds on save.
4. Use `Ctrl+Alt+V` or **LaTeX Workshop: View LaTeX PDF file** to preview
   `build/main.pdf` in a VS Code tab.

## Overleaf

Upload the contents of this folder so that `main.tex` is at the project root.
Select `main.tex` as the main document and XeLaTeX as the compiler. Keep
`.latexmkrc`, `.vscode/`, `sections/`, `figures/`, `code/`, and
`references.bib` in the uploaded project. Replace the baseline
`code/main.py` and the appendix support-material manifest with the complete
contest program and actual relative file list before submission.

Before final writing, generate `generated/results.tex` from the project-level
`results/verified_values.csv`. Use `\VerifiedValue{key}` or
`\VerifiedValueWithUnit{key}` for every result number in the abstract and
conclusion; the bundled generated file is only a compile-safe starter.

## CUMCM 2026 AI declaration

`sections/ai_declaration.tex` is inserted immediately before the references.
Leave `\cumcmaiusedfalse` in `main.tex` only when no AI tool was used. When AI
was used, change it to `\cumcmaiusedtrue`, replace the purpose between the
`HUMAN-EDITABLE AI PURPOSE` markers with the actual concise purpose, and include `AI工具使用详情.pdf` in the support
archive. The selected branch must match `contest_manifest.json` and
`verify_submission.py --ai-mode none|used`. The AI-report generator may fill the
starter purpose but preserves a non-placeholder human edit.
