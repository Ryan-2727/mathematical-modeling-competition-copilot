---
name: mathematical-modeling-competition-copilot
description: Explicit-invocation-only end-to-end mathematical modeling competition workflow for contest problem solving and paper production. Use ONLY when the user explicitly invokes `$mathematical-modeling-competition-copilot` or supplies a direct link to this SKILL.md. Do not use it automatically for ordinary mathematical modeling questions.
---

# Mathematical Modeling Competition Copilot

Use this only after the user explicitly invokes `$mathematical-modeling-competition-copilot` or supplies a direct link to this SKILL.md. Do not infer invocation merely because a request concerns mathematical modeling, a contest, or paper writing; answer those requests normally unless the user explicitly calls this skill.

When explicitly invoked, use this as the main entry point for mathematical modeling competitions. This skill is self-contained for workflow knowledge: it embeds the contest setup, modeling, literature resolution, computation, writing, table, and verification rules that were previously spread across multiple helper skills.

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
   - Read `references/embedded/award-oriented-workflow.md` and
     `references/embedded/contest-operations-72h.md`. Adapt the milestone hours
     proportionally when the contest is not 72 hours.
   - Use the embedded brainstorming gate in that file before committing to a modeling route.
   - Confirm contest type, language, submission format, time budget, team role split, available data, and deliverables.
   - If the contest is CUMCM / 中国大学生数学建模竞赛（国赛）, read `references/embedded/cumcm-model-selection.md` before selecting models. Ask for, or infer from the context, the available Python, MATLAB, and LINGO environments; treat them as equal paths and select the one that best matches the method and reproducibility need.
   - Create or update `plan.md`, `todo.md`, and `reports/milestones.csv`.

2. **Problem analysis and model design**
   - Read `references/embedded/llm-mm-agent-methodology.md`.
   - Read `references/embedded/mathmodel-six-phase.md` for contest-specific modeling expectations.
   - Read `references/embedded/problem-structure-playbooks.md`; choose a route
     from problem structure and evidence needs, not from algorithm prestige.
   - For CUMCM, route each subproblem through the task signals and model cards in `references/embedded/cumcm-model-selection.md`. Maintain a trace from subproblem to data, model, implementation, validation, result file, and paper section.
   - Produce a subproblem map, assumptions, variables, constraints, objective functions, candidate methods, and validation plan.
   - Maintain `reports/model_decision_log.csv`. For each subproblem compare a
     credible baseline with candidate routes, record the failure test and
     validation cost, and explain why the selected model matches the mechanism.
   - Create `reports/traceability.md`; every subproblem must map data, model, validation, result file, figure/table, and paper section.

3. **Literature and reproduction details**
   - Read `references/embedded/verified-literature-and-two-part-delivery.md`
     whenever a completed paper is in scope.
   - Read `references/embedded/literature-fetch-and-explain.md` when literature search, paper selection, or paper explanation is needed.
   - Read `references/embedded/paper-context-resolver.md` when a narrow source-backed detail matters.
   - Do not use broad paper summaries as a substitute for model design.
   - Maintain `reports/bibliography.csv`. A completed paper requires at least 10
     unique, relevant scholarly works that are cited in the LaTeX body, verified
     against authoritative metadata, confirmed by an observed exact-title Google
     Scholar result, and read at the passage supporting the attributed claim.
   - Record source, claim, source locator, modeling impact, and whether evidence
     is direct or inferred. Never fabricate bibliographic metadata or source content.

4. **Computation and experiments**
   - Read `references/embedded/computation-and-visualization.md`.
   - Read `references/embedded/data-traceability-and-reproducibility.md` before fitting a data-driven model.
   - Read `references/embedded/data-units-and-source-quality.md` and maintain
     `reports/units.csv` for quantities, conversions, ranges, and source scope.
   - Read `references/embedded/stress-testing-and-uncertainty.md`. Register at
     least one proportionate, predeclared stress test for every decisive
     subproblem claim in `reports/stress_tests.csv` and save its result artifact.
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
   - `scripts/init_contest.py` scaffolds the portable LaTeX tree when `paper/` is
     empty. For an existing project, run `scripts/scaffold_latex_paper.py` without
     `--force`; preserve a nonempty paper directory instead of overwriting it.
   - Select a current rules branch from the rules snapshot. Use the 2025 Chinese file only as a historical baseline, not as a silent rule default.
   - For English MCM/ICM, also read `references/embedded/paper-writing-mcm-icm-current.md`.
   - Assemble assumptions, notation, model derivations, results, figures, tables, sensitivity analysis, and limitations into the paper.
   - The completed paper deliverable is `paper/main.pdf` plus its rebuildable
     LaTeX source, including `paper/main.tex`, every included source file,
     `paper/references.bib`, `.latexmkrc`, `.vscode/`, `sections/`, `figures/`,
     and required tables, styles, and assets. It must compile and preview with
     XeLaTeX/latexmk in both Overleaf and VS Code using only relative paths and
     portable fonts.
     Do not substitute DOCX, Markdown, Typst, or source-only output for this
     deliverable unless the user explicitly changes the requirement.

8. **Table polish**
   - Read `references/embedded/latex-tables.md` for LaTeX or academic tables.
   - For general contest tables, enforce captions, units, source notes, aligned numeric columns, reasonable precision, and consistency with result files.

9. **Final verification**
   - Read `references/embedded/final-verification.md`.
   - Read `references/embedded/tool-fallbacks.md` if any plugin or runtime was missing.
   - Do not claim completion without fresh evidence.
   - Run `scripts/verify_claims.py`; complete `reports/argument_coverage.csv` for every subproblem.
   - Run `scripts/verify_latex_compatibility.py` to create a fresh, compile-backed
     `reports/latex_compatibility.json`. Require successful project-root and
     `build/` output builds before the paper-delivery gate.
   - Build `support.zip` from `support/materials_manifest.csv`, then run
     `scripts/verify_paper_delivery.py`. A pass is a structural gate only; inspect
     the rendered PDF and the cited source passages separately.

10. **Optional award-focused post-paper review**
   - Only after modeling and the complete paper are finished and phase 9 has run,
     ask whether the user wants this optional phase. Do not run it by default.
   - If the user opts in, read `references/embedded/post-paper-award-review.md`
     and `references/embedded/reviewer-scorecard-and-presentation.md`. Produce
     prioritized reviewer findings and `reports/reviewer_scorecard.csv`; do not
     use current-problem answer sources or paired exemplars.
   - Run `scripts/verify_award_readiness.py`. Treat a pass as evidence-structure
     completeness only, never as proof of mathematical truth or an award prediction.
   - After any accepted revision, rerun phase 9 before freezing.

11. **Freeze and submit**
   - Read `references/embedded/submission-and-anonymity.md`.
   - Deliver two explicit parts: (1) `paper/main.pdf` with the complete LaTeX
     source tree, and (2) `support.zip` with runnable code, legally distributable
     data or reproducible retrieval evidence, environment, exact commands, results,
     licenses, and hashes.
   - Run anonymity scan, environment capture, paper-delivery verification, and submission verification. Record final hashes and transition the manifest through `verified`, `frozen`, `hashed`, `submitted`, and `receipt_verified` only with evidence.
   - When AI is used in CUMCM 2026, render and include `AI工具使用详情.pdf`, then use `verify_submission.py --profile cumcm-2026 --require-ai-report`.

12. **Paper-learning regression loop**
   - Read `references/embedded/training-evaluation-loop.md` before using an
     excellent-paper corpus to improve this skill.
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
|   |-- bibliography.csv
|   |-- model_decision_log.csv
|   |-- stress_tests.csv
|   |-- units.csv
|   |-- reviewer_scorecard.csv
|   |-- milestones.csv
|   |-- ai_usage_log.jsonl
|   `-- verification_report.md
|-- environment/
|   `-- README.md
|-- support/
|   |-- README.md
|   |-- reproduction_commands.txt
|   |-- materials_manifest.csv
|   `-- data_inventory.csv
|-- support.zip
`-- paper/
    |-- main.tex
    |-- references.bib
    |-- .latexmkrc
    |-- .vscode/
    |   |-- settings.json
    |   `-- extensions.json
    |-- sections/
    |-- figures/
    |-- build/
    `-- main.pdf
```

## Decision Rules

- If the problem statement is missing, ask for it before modeling.
- If data is missing but the task can proceed with public or synthetic data, label that explicitly.
- If multiple model families fit, compare the simplest credible baseline against one stronger method.
- Treat creativity as a problem-specific improvement in abstraction, mechanism,
  constraint design, diagnostic evidence, or decision insight. Algorithmic
  complexity without measurable benefit is not creativity.
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
- Every decisive conclusion needs a proportionate failure-oriented test. Choose
  the test before seeing its outcome and preserve the result even when it weakens
  the preferred model.
- A completed paper needs at least 10 real, relevant, uniquely cited scholarly
  references. Authoritative metadata and an exact-title Google Scholar query are
  necessary but not sufficient: read the supporting passage and never infer or
  fabricate source content.
- Do not call the work complete until both the compiled PDF plus rebuildable
  LaTeX source and the verified support-material archive are present.
- Treat PDF page sequence, appendix boundaries, OCR output, and Office metadata as visual or tool-dependent checks; record an unresolved limitation instead of inferring success.

## Embedded References

Use these files as phase playbooks:

- `references/embedded/contest-setup.md`
- `references/embedded/award-oriented-workflow.md`
- `references/embedded/contest-operations-72h.md`
- `references/embedded/contest-modes-and-compliance.md`
- `references/embedded/cumcm-2026-rules.md`
- `references/embedded/cumcm-model-selection.md` (CUMCM / 中国大学生数学建模竞赛 model routing, Python/MATLAB/LINGO selection, and validation gates)
- `references/embedded/problem-structure-playbooks.md`
- `references/embedded/mathmodel-six-phase.md`
- `references/embedded/llm-mm-agent-methodology.md`
- `references/embedded/literature-fetch-and-explain.md`
- `references/embedded/paper-context-resolver.md`
- `references/embedded/verified-literature-and-two-part-delivery.md`
- `references/embedded/computation-and-visualization.md`
- `references/embedded/data-traceability-and-reproducibility.md`
- `references/embedded/data-units-and-source-quality.md`
- `references/embedded/evidence-and-quality-gates.md`
- `references/embedded/stress-testing-and-uncertainty.md`
- `references/embedded/post-paper-award-review.md`
- `references/embedded/reviewer-scorecard-and-presentation.md`
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
- `references/embedded/training-evaluation-loop.md`

Read `references/workflow-map.md` for the dependency map, plugin limits, and fallback behavior.
