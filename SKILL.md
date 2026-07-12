---
name: mathematical-modeling-competition-copilot
description: Self-contained end-to-end mathematical modeling competition workflow for contest problem solving and paper production. Use when Codex needs to help with MCM/ICM, CUMCM, Huawei Cup, school mathematical modeling contests, or similar tasks involving problem analysis, literature-supported modeling, reproducible computation, figures, tables, DOCX/PDF/LaTeX paper writing, and final verification.
---

# Mathematical Modeling Competition Copilot

Use this as the main entry point for mathematical modeling competitions. This skill is self-contained for workflow knowledge: it embeds the contest setup, modeling, literature resolution, computation, writing, table, and verification rules that were previously spread across multiple helper skills.

It does not promise an award. It maximizes award probability through disciplined modeling, reproducible computation, strong writing, and hard verification.

## Operating Mode

- Start with the required workflow order below.
- Read only the embedded reference files needed for the current phase.
- Use installed plugins when they are available for file-specific work such as notebooks, DOCX, PDF, or spreadsheets.
- If a plugin or runtime is unavailable, continue with the workflow manually and record the limitation in `reports/verification_report.md`.

## Required Workflow Order

0. **Contest mode, rules, and compliance**
   - Read `references/embedded/contest-modes-and-compliance.md` before viewing or researching a live problem.
   - Run `scripts/init_contest.py` and create `contest_manifest.json` plus a current official `reports/contest_rules_snapshot.md`.
   - In live mode, prohibit current-problem discussion, interactive help, answer searching, and public posting. Record AI use from the first material use.
   - For CUMCM 2026, read `references/embedded/cumcm-2026-rules.md` and select the `cumcm-2026` verification profile.

1. **Contest setup and strategy**
   - Read `references/embedded/contest-setup.md`.
   - Use the embedded brainstorming gate in that file before committing to a modeling route.
   - Confirm contest type, language, submission format, time budget, team role split, available data, and deliverables.
   - If the contest is CUMCM / 中国大学生数学建模竞赛（国赛）, read `references/embedded/cumcm-model-selection.md` before selecting models. Ask for, or infer from the context, the available Python, MATLAB, and LINGO environments; treat them as equal paths and select the one that best matches the method and reproducibility need.
   - Create or update `plan.md` and `todo.md`.

2. **Problem analysis and model design**
   - Read `references/embedded/llm-mm-agent-methodology.md`.
   - Read `references/embedded/mathmodel-six-phase.md` for contest-specific modeling expectations.
   - For CUMCM, route each subproblem through the task signals and model cards in `references/embedded/cumcm-model-selection.md`. Maintain a trace from subproblem to data, model, implementation, validation, result file, and paper section.
   - Produce a subproblem map, assumptions, variables, constraints, objective functions, candidate methods, and validation plan.
   - Create `reports/traceability.md`; every subproblem must map data, model, validation, result file, figure/table, and paper section.

3. **Literature and reproduction details**
   - Read `references/embedded/literature-fetch-and-explain.md` when literature search, paper selection, or paper explanation is needed.
   - Read `references/embedded/paper-context-resolver.md` when a narrow source-backed detail matters.
   - Do not use broad paper summaries as a substitute for model design.
   - Record source, claim, modeling impact, and whether evidence is direct or inferred.

4. **Computation and experiments**
   - Read `references/embedded/computation-and-visualization.md`.
   - Read `references/embedded/data-traceability-and-reproducibility.md` before fitting a data-driven model.
   - Use notebooks, scripts, or spreadsheets to produce executable evidence.
   - Every numeric conclusion must come from executed code, a spreadsheet formula, or a cited source.
   - Maintain `reports/claims.csv` and run `scripts/run_reproduction.py` for the frozen pipeline.
   - Read `references/embedded/evidence-and-quality-gates.md` before claiming numerical validation.

5. **Tabular analysis and scenario sheets**
   - Use spreadsheet-style reasoning for scoring matrices, sensitivity tables, scenario comparison, and dashboards.
   - If the Spreadsheets plugin is installed, use it for `.xlsx` creation and verification.
   - If not installed, create CSV/Markdown tables and record the limitation.

6. **Figures, flowcharts, and diagrams**
   - Read `references/embedded/diagrams.md`.
   - Separate data-driven charts from non-data diagrams.
   - Keep figure captions, labels, and source data traceable.

7. **Paper writing**
   - Read `references/embedded/paper-writing.md`.
   - When improving paper-writing ability or when an offline corpus of excellent
     papers is available, read `references/embedded/paper-learning-from-exemplars.md`.
   - For the learned 2025 Chinese-paper profile, read
     `references/embedded/2025-corpus-observations.md`.
   - For cross-year CUMCM writing patterns, read
     `references/embedded/multi-year-corpus-observations.md`.
   - Read `references/embedded/latex-paper-pipeline.md` whenever the user requests
     LaTeX or the contest submission is a Chinese national-format paper.
   - Select a current rules branch from the rules snapshot. Use the 2025 Chinese file only as a historical baseline, not as a silent rule default.
   - For English MCM/ICM, also read `references/embedded/paper-writing-mcm-icm-current.md`.
   - Assemble assumptions, notation, model derivations, results, figures, tables, sensitivity analysis, and limitations into the paper.
   - Use DOCX/PDF/LaTeX/Typst only when the contest or user chooses that path.

8. **Table polish**
   - Read `references/embedded/latex-tables.md` for LaTeX or academic tables.
   - For general contest tables, enforce captions, units, source notes, aligned numeric columns, reasonable precision, and consistency with result files.

9. **Final verification**
   - Read `references/embedded/final-verification.md`.
   - Read `references/embedded/tool-fallbacks.md` if any plugin or runtime was missing.
   - Do not claim completion without fresh evidence.
   - Run `scripts/verify_claims.py`; complete `reports/argument_coverage.csv` for every subproblem.

10. **Freeze and submit**
   - Read `references/embedded/submission-and-anonymity.md`.
   - Run anonymity scan, environment capture, and submission verification. Record final hashes and transition the manifest through `verified`, `frozen`, `hashed`, `submitted`, and `receipt_verified` only with evidence.
   - When AI is used in CUMCM 2026, render and include `AI工具使用详情.pdf`, then use `verify_submission.py --profile cumcm-2026 --require-ai-report`.

11. **Paper-learning regression loop**
   - Profile an offline corpus once with `scripts/paper_corpus_metrics.py --recursive` and
     visual inspection; convert recurring strengths into reusable writing rules.
   - Solve each test problem independently and freeze the baseline source,
     results, figures, and LaTeX paper before any post-hoc comparison.
   - Compare the baseline with the corpus profile, revise no more than three
     generalizable gaps, then re-solve from the statement and data. Never require a
     current-problem paper as an input and never copy exemplar wording, numbers,
     models, or figures.

## Default Artifact Layout

Create or preserve this layout unless the user provides an existing project structure:

```text
.
|-- plan.md
|-- todo.md
|-- data/
|   |-- raw/
|   `-- processed/
|-- notebooks/
|-- code/
|-- results/
|-- figures/
|-- reports/
|   |-- problem_analysis.md
|   |-- model_design.md
|   |-- experiment_log.md
|   |-- contest_rules_snapshot.md
|   |-- data_audit.md
|   |-- traceability.md
|   |-- claims.csv
|   |-- argument_coverage.csv
|   |-- ai_usage_log.jsonl
|   `-- verification_report.md
|-- environment/
|-- support/
`-- paper/
```

## Decision Rules

- If the problem statement is missing, ask for it before modeling.
- If data is missing but the task can proceed with public or synthetic data, label that explicitly.
- If multiple model families fit, compare the simplest credible baseline against one stronger method.
- For CUMCM, do not stack models for appearance. Select at most one primary model and one evidence-backed comparison or enhancement per subproblem; apply the method-specific minimum validation gate from `cumcm-model-selection.md`.
- If computation cannot be run, do not present numeric conclusions as verified.
- If time is short, prioritize a complete baseline model, clean paper structure, and final consistency checks over extra model variants.
- If a plugin is missing, degrade gracefully; do not pretend visual rendering, workbook formulas, or notebook execution were verified.
- If corpus PDFs are scanned, use visual rendering as the authority for layout and
  record OCR/text-extraction limitations; do not claim semantic comparison from
  empty or incomplete extracted text.
- Do not silently reuse prior-year rules. A current official rule snapshot is required before a live contest can become submission-ready.
- Do not use a public discussion, answer, code-sharing, or interactive-help source for the current live problem.
- A synthetic dataset may illustrate a method but cannot be presented as observed evidence. Record source permission and data transformations.
- A heuristic or incomplete solver result is not a global optimum; report solver status, feasibility, tolerance, and optimality gap where applicable.
- Treat PDF page sequence, appendix boundaries, OCR output, and Office metadata as visual or tool-dependent checks; record an unresolved limitation instead of inferring success.

## Embedded References

Use these files as phase playbooks:

- `references/embedded/contest-setup.md`
- `references/embedded/contest-modes-and-compliance.md`
- `references/embedded/cumcm-2026-rules.md`
- `references/embedded/cumcm-model-selection.md` (CUMCM / 中国大学生数学建模竞赛 model routing, Python/MATLAB/LINGO selection, and validation gates)
- `references/embedded/mathmodel-six-phase.md`
- `references/embedded/llm-mm-agent-methodology.md`
- `references/embedded/literature-fetch-and-explain.md`
- `references/embedded/paper-context-resolver.md`
- `references/embedded/computation-and-visualization.md`
- `references/embedded/data-traceability-and-reproducibility.md`
- `references/embedded/evidence-and-quality-gates.md`
- `references/embedded/diagrams.md`
- `references/embedded/paper-writing.md`
- `references/embedded/paper-learning-from-exemplars.md`
- `references/embedded/2025-corpus-observations.md`
- `references/embedded/multi-year-corpus-observations.md`
- `references/embedded/latex-paper-pipeline.md`
- `references/embedded/paper-writing-zh-cn-format2025.md`
- `references/embedded/paper-writing-en-contest-base.md`
- `references/embedded/paper-writing-mcm-icm-current.md`
- `references/embedded/latex-tables.md`
- `references/embedded/final-verification.md`
- `references/embedded/tool-fallbacks.md`
- `references/embedded/submission-and-anonymity.md`

Read `references/workflow-map.md` for the dependency map, plugin limits, and fallback behavior.
