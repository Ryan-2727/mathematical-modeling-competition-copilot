# Paper Writing Router

Use this module to select the correct paper-writing branch.

## Branch Selection

- For Chinese mathematical modeling contests that follow the 2025 National College Student Mathematical Modeling Competition format, read `paper-writing-zh-cn-format2025.md`.
- For CUMCM-style Chinese contests without a separate stricter template, read `paper-writing-zh-cn-format2025.md` as the baseline and adapt only where the contest notice differs.
- For English contests such as MCM/ICM, read `paper-writing-en-contest-base.md`.
- If the user provides a contest-specific template, use that template first and use the closest branch only for quality gates and missing-detail checks.

## Shared Writing Rules

- Define symbols before use.
- Keep formulas connected to plain-language purpose.
- Introduce figures and tables before or near their appearance.
- Tie every conclusion to a result, figure, table, or source.
- Do not invent numbers while writing.
- Keep limitations honest but not self-defeating.
- Preserve the contest's anonymity and submission rules over generic writing preferences.

## Output Discipline

Record the selected branch in `reports/verification_report.md`:

- selected paper branch
- contest-specific template or format source
- any unresolved formatting requirement
- whether DOCX/PDF render verification was performed
