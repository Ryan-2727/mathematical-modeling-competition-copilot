# Workflow Map

This repository is designed as a self-contained Codex skill. A new computer can install only this repository and still get the full mathematical modeling competition workflow.

## Embedded Workflow Modules

The following formerly separate skills or helper workflows are embedded as reference playbooks:

- `contest-setup.md`: project initialization, `plan.md`, `todo.md`, contest constraints, and task tracking.
- `award-oriented-workflow.md`: four evidence dimensions and phase-by-phase award-readiness gates.
- `contest-operations-72h.md`: milestone schedule, role handoffs, and stop-loss rules for a 72-hour contest.
- `contest-modes-and-compliance.md`: live-contest boundary, current rules snapshot, AI-use evidence, and submission-state machine.
- `cumcm-2026-rules.md`: executable CUMCM 2026 format, support-package, AI-report, and submission-profile checks.
- `contest-setup.md` also embeds the `brainstorming` gate for bounded model-route exploration.
- `cumcm-model-selection.md`: CUMCM / 中国大学生数学建模竞赛 routing guide sourced from the local model library. It maps task signals to methods, gives Python/MATLAB/LINGO selection boundaries, and states method-specific validation gates.
- `problem-structure-playbooks.md`: route selection for evaluation, forecasting, optimization, mechanism, classification, and simulation problems.
- `mathmodel-six-phase.md`: contest-specific six-phase workflow: setup, analysis/modeling, coding/visualization, diagrams, paper writing, and verification.
- `llm-mm-agent-methodology.md`: LLM-MM-Agent-inspired four-stage loop and HMML/MLE-Solver-style method selection.
- `literature-fetch-and-explain.md`: embedded `paper-fetch-skill` and `paper-explainer` workflow for source search, paper explanation, and source notes.
- `paper-context-resolver.md`: narrow paper or reproduction detail resolution.
- `verified-literature-and-two-part-delivery.md`: ten-source evidence ledger,
  BibTeX/LaTeX cross-check, compiled-paper contract, and reproducible support package.
- `computation-and-visualization.md`: code, notebooks, result tables, data validation, and data-driven figures.
- `data-traceability-and-reproducibility.md`: data audit, traceability table, environment capture, model-specific validation gates, and clean reruns.
- `data-units-and-source-quality.md`: source hierarchy, unit checks, scope alignment, leakage controls, and transformations.
- `evidence-and-quality-gates.md`: claim ledger, reproducible-run manifest, numerical diagnostics, argument coverage, and historical-corpus originality preflight.
- `stress-testing-and-uncertainty.md`: failure-oriented validation selected by claim type before results are known.
- `post-paper-award-review.md`: user-opt-in reviewer simulation and claim stress test after paper completion, before freeze.
- `reviewer-scorecard-and-presentation.md`: four-dimension internal scorecard and reader-first abstract, figure, and table review.
- `diagrams.md`: flowcharts, architecture diagrams, and non-data visual explanation.
- `paper-writing.md`: paper-writing branch selector.
- `paper-writing-zh-cn-format2025.md`: Chinese mathematical modeling paper format rules based on the supplied 2025 format document.
- `paper-writing-en-contest-base.md`: preserved English contest paper-writing baseline for later MCM/ICM-specific changes.
- `paper-writing-mcm-icm-current.md`: current-rule verification checklist for MCM/ICM submission and AI disclosure.
- `latex-paper-pipeline.md`: portable XeLaTeX/latexmk source tree, Overleaf and
  VS Code build/preview workflows, and compile-backed compatibility gate.
- `latex-tables.md`: LaTeX table and academic table polish.
- `final-verification.md`: evidence-before-completion and submission readiness checks.
- `tool-fallbacks.md`: what requires optional Codex plugins and what to do when they are missing.
- `submission-and-anonymity.md`: metadata/path scanning, support-package scope, copyright checks, final hashes, and receipt evidence.
- `training-evaluation-loop.md`: hidden-exemplar baseline, measurable regression, and capped extraction of reusable rules.

## Optional Codex Plugins

These capabilities cannot be fully embedded as text because they depend on runtime tools:

- `jupyter-notebooks`: install/enable the Data Analytics plugin if notebook creation and top-to-bottom execution are required.
- `documents`: install/enable the Documents plugin if DOCX creation, editing, or visual render QA is required.
- `pdf`: install/enable the PDF plugin if PDF rendering, extraction, or page-image inspection is required.
- `spreadsheets`: install/enable the Spreadsheets plugin if `.xlsx` creation, formulas, charts, or workbook rendering are required.

When these plugins are unavailable, continue the modeling workflow and record the missing capability in `reports/verification_report.md`.

## Phase Outputs

| Phase | Minimum output | Verification |
| --- | --- | --- |
| Setup | `plan.md`, `todo.md`, `reports/milestones.csv` | User constraints and timed gates captured |
| Compliance | `contest_manifest.json`, rules snapshot, AI log | Current rules and live-mode boundary recorded |
| Analysis | `reports/problem_analysis.md` | Every subproblem mapped; CUMCM uses task-to-model routing |
| Data | `reports/data_audit.md`, `reports/traceability.md`, `reports/claims.csv` | Data provenance and claim-to-result chain complete |
| Modeling | `reports/model_design.md`, `reports/model_decision_log.csv` | Variables and assumptions defined; route selection justified against a baseline |
| Literature | `reports/bibliography.csv`, `paper/references.bib` | At least 10 uniquely cited works have authoritative metadata, exact-title Scholar queries, and checked source passages |
| Computation | code/notebooks, `results/`, `reports/stress_tests.csv`, `reports/units.csv` | Executed; units reconciled; decisive claims challenged |
| Figures/tables | `figures/`, tables | Referenced and consistent |
| Writing | `paper/main.tex`, `paper/main.pdf`, complete portable LaTeX source tree | Overleaf-style root and VS Code `build/` outputs compile with XeLaTeX/latexmk, render correctly, and match computation |
| Final check | verification report, argument coverage, claim report, `reports/latex_compatibility.json`, `reports/paper_delivery.json` | Compatibility report is fresh and compile-backed; completion claims and paper/support gates pass |
| Optional review | `reports/post_paper_review.md`, `reports/reviewer_scorecard.csv`, award-readiness report | Only after explicit user opt-in; four evidence dimensions reviewed and final checks rerun after changes |
| Submission | PDF plus LaTeX source, `support.zip`, hash manifest, receipt evidence | Both deliverable parts are complete, frozen, verified, and anonymous |

## Fallback Behavior

If a helper capability is unavailable:

1. Continue with the same phase manually.
2. Use plain Markdown, CSV, scripts, or text artifacts where possible.
3. Record what was not verified in `reports/verification_report.md`.
4. Do not claim visual, formula, or execution verification unless it was actually performed.
