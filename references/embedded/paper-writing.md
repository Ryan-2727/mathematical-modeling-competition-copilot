# Paper Writing Router

Use this module to select the correct paper-writing branch.

## Branch Selection

- Select the paper branch from the current official rules snapshot. Historical format files are guidance only and never override a current official notice.
- For Chinese CUMCM-style contests, use `paper-writing-zh-cn-format2025.md` only as a historical layout baseline and record all year-specific deviations.
- For English MCM/ICM, read both `paper-writing-en-contest-base.md` and `paper-writing-mcm-icm-current.md`.
- If the user provides a contest-specific template, use that template first and use the closest branch only for quality gates and missing-detail checks.

## Shared Writing Rules

- Define symbols before use.
- Keep formulas connected to plain-language purpose.
- Introduce figures and tables before or near their appearance.
- Tie every conclusion to a result, figure, table, or source.
- Do not invent numbers while writing.
- Cite at least 10 unique, relevant, real scholarly works in the LaTeX body.
  Verify each work and its supported claim using
  `verified-literature-and-two-part-delivery.md`; never invent metadata, source
  content, or locators and never pad the bibliography with uncited sources.
- Keep limitations honest but not self-defeating.
- Preserve the contest's anonymity and submission rules over generic writing preferences.

## Output Discipline

Record the selected branch in `reports/verification_report.md`:

- selected paper branch
- contest-specific template or format source
- any unresolved formatting requirement
- whether DOCX/PDF render verification was performed
- page-limit calculation and current rules source
- AI disclosure and submission-state evidence
- authoritative bibliography ledger and exact-title Google Scholar checks
- compiled `paper/main.pdf` plus complete LaTeX source
- verified `support.zip` containing code, data or retrieval evidence, environment,
  exact commands, results, licenses, and hashes
