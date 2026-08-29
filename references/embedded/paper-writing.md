# Paper Writing Router

Use this module to select the correct paper-writing branch.

## Responsibility boundary

This router owns branch selection and shared prose discipline only.
`result-first-paper-convergence.md` owns abstract/result convergence,
`paper-depth-and-page-budget.md` owns reasoning depth and page allocation,
`paper-presentation-and-visual-design.md` owns rendered visual presentation,
`latex-paper-pipeline.md` owns compilation and portability, and
`final-verification.md` owns release evidence. Follow those owners instead of
restating their detailed checks here.

## Branch Selection

- Select the paper branch from the current official rules snapshot. Historical format files are guidance only and never override a current official notice.
- For Chinese CUMCM-style contests, use `paper-writing-zh-cn-format2025.md` only as a historical layout baseline and record all year-specific deviations.
- For English MCM/ICM, read both `paper-writing-en-contest-base.md` and `paper-writing-mcm-icm-current.md`.
- If the user provides a contest-specific template, use that template first and use the closest branch only for quality gates and missing-detail checks.

## Shared Writing Rules

- Read `result-first-paper-convergence.md` before drafting the abstract or committing to a complex primary model.
- Read `paper-depth-and-page-budget.md` before outlining. Allocate pages by the
  reasoning burden of each claim, not by equal section lengths, and distinguish
  main-text depth from code-appendix volume.
- Define symbols before use.
- Keep formulas connected to plain-language purpose.
- Introduce figures and tables before or near their appearance.
- Tie every conclusion to a result, figure, table, or source.
- Let evidence determine which reasoning details appear. Explain model choice only
  when a credible competitor was executed, parameter provenance only for
  claim-sensitive values, failed routes only when a real failed-run artifact
  exists, and abnormal boundaries when identifiability or fallback evidence makes
  the conclusion conditional. Weave these details into the relevant paragraph;
  do not create ritual headings or stock confessions.
- Maintain `reports/paper_reasoning_map.csv` as a paper-location map to the
  existing decision, parameter, simplification, fallback, and traceability
  ledgers. Run `scripts/verify_paper_reasoning_narrative.py`; every completed map
  row requires a named human reviewer, not a tool identity.
- Do not invent numbers while writing.
- Cite at least 10 unique, relevant, real scholarly works in the LaTeX body.
  Verify each work and its supported claim using
  `verified-literature-and-two-part-delivery.md`; never invent metadata, source
  content, or locators and never pad the bibliography with uncited sources.
- Keep limitations honest but not self-defeating.
- Preserve the contest's anonymity and submission rules over generic writing preferences.
- For a Chinese LaTeX paper, run
  `scripts/verify_chinese_academic_style.py` after drafting. Review its located
  warnings for undefined abbreviations, long prose, duplicate conclusions,
  repeated openings, mechanical transitions, detached method catalogues,
  unsupported evaluative or causal wording, overbroad scope, raw precision
  inconsistency, and excessive self-reference. The default is advisory. It never rewrites prose and never labels authorship.
  Record a deliberate exception only in `reports/prose_style_exemptions.csv`;
  use training-only `--fail-on` when the team explicitly wants a blocking lint.

## Output Discipline

Record the selected branch in `reports/verification_report.md`:

- selected paper branch
- contest-specific template or format source
- any unresolved formatting requirement
- whether DOCX/PDF render verification was performed
- page-limit calculation and current rules source
- planned and actual main-text/appendix pages, depth-profile rationale, and the
  `verify_paper_depth.py` result
- AI disclosure and submission-state evidence
- authoritative bibliography ledger and exact-title Google Scholar checks
- compiled `paper/main.pdf` plus complete LaTeX source
- `reports/chinese_academic_style.json`, including unresolved and human-exempted findings
- `reports/paper_reasoning_narrative.json`, including each evidence-triggered paper location and human review
- verified `support.zip` containing code, data or retrieval evidence, environment,
  exact commands, results, licenses, and hashes
