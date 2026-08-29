# Workflow Map

This repository is designed as a self-contained Codex skill. A new computer can install only this repository and still get the full mathematical modeling competition workflow.

## Embedded Workflow Modules

The following formerly separate skills or helper workflows are embedded as reference playbooks:

- `contest-setup.md`: project initialization, bounded brainstorming, `plan.md`,
  `todo.md`, contest constraints, and task tracking.
- `award-oriented-workflow.md`: four evidence dimensions and phase-by-phase award-readiness gates.
- `contest-operations-72h.md`: milestone schedule, role handoffs, and stop-loss rules for a 72-hour contest.
- `contest-modes-and-compliance.md`: live-contest boundary, current rules snapshot, AI-use evidence, and submission-state machine.
- `cumcm-2026-rules.md`: executable CUMCM 2026 format, support-package, AI-report, and submission-profile checks.
- `cumcm-2026-readiness.md`: local-only online boundary, staged A/B/C audition,
  AI-only evidence ranking, optional calibrated award intervals, user-confirmed
  H6 lock, exact 74-hour operations, and timed rehearsal readiness.
- `executable-contest-profiles.md`: versioned CUMCM and MCM/ICM official-rule
  profiles, evidence fields, template selection, and executable submission gates.
- `operational-quality-gates.md`: hash-bound rule lock, cumulative phase
  controller, abstract/bibliography/manuscript checks, and separation of user
  delivery from official submission.
- `decision-and-delivery-gates.md`: stability, figure-number, model-budget,
  three-minute-review, and LaTeX dependency-lock evidence.
- `orchestration-and-paper-assurance.md`: versioned project migration,
  `contestctl doctor/run/summary`, minimal/standard/strict/custom profiles,
  rendered-figure review, notation/dimension checks, and generated LaTeX result
  artifacts.
- `cumcm-model-selection.md`: CUMCM / 中国大学生数学建模竞赛 routing guide sourced from the local model library. It maps task signals to methods, gives Python/MATLAB/LINGO selection boundaries, and states method-specific validation gates.
- `problem-structure-playbooks.md`: route selection for evaluation, forecasting, optimization, mechanism, classification, and simulation problems.
- `model-reasoning-kernel.md`: evidence contracts, mechanism/model ladders,
  identifiability, parameter roles, joint inference, and safe fallbacks.
- `cumcm-bc-model-library.md`: targeted B/C routing for designed experiments,
  localization, coverage, sequential decisions, compositional data, robust
  planning, price-demand, longitudinal timing, and calibrated imbalance;
  validate the bundled JSON with `verify_model_library.py`; five cards also
  expose bounded executable kernels with synthetic truth and metamorphic tests.
- `physics-inverse-modeling-playbook.md`: conditionally loaded physical
  measurement and inverse-problem route from observation equations through
  joint inference and proxy-versus-complete-model competition.
- `diagnostics-and-result-reconciliation.md`: independent-route test,
  claim-based diagnostic matrix, conflict investigation, and conclusion
  admission rules.
- `mathmodel-six-phase.md`: contest-specific six-phase workflow: setup, analysis/modeling, coding/visualization, diagrams, paper writing, and verification.
- `llm-mm-agent-methodology.md`: LLM-MM-Agent-inspired four-stage loop and HMML/MLE-Solver-style method selection.
- `literature-fetch-and-explain.md`: embedded `paper-fetch-skill` and `paper-explainer` workflow for source search, paper explanation, and source notes.
- `paper-context-resolver.md`: narrow paper or reproduction detail resolution.
- `verified-literature-and-two-part-delivery.md`: ten-source evidence ledger,
  BibTeX/LaTeX cross-check, compiled-paper contract, and reproducible support package.
- `computation-and-visualization.md`: code, notebooks, result tables, data validation, and data-driven figures.
- `computation-and-visualization.md` also defines the decisive-value registry,
  generated LaTeX macros, and model-family validation adapters.
- `data-traceability-and-reproducibility.md`: data audit, traceability table, environment capture, model-specific validation gates, and clean reruns.
- `data-units-and-source-quality.md`: source hierarchy, unit checks, scope alignment, leakage controls, and transformations.
- `evidence-and-quality-gates.md`: claim ledger, reproducible-run manifest, numerical diagnostics, argument coverage, and historical-corpus originality preflight.
- `stress-testing-and-uncertainty.md`: failure-oriented validation selected by claim type before results are known.
- `post-paper-award-review.md`: user-opt-in reviewer simulation and claim stress test after paper completion, before freeze.
- `reviewer-scorecard-and-presentation.md`: four-dimension internal scorecard and reader-first abstract, figure, and table review.
- `independent-review-and-regression.md`: blinded reviewer packets, artifact
  locators, disagreement/veto aggregation, and release-regression policy.
- `diagrams.md`: flowcharts, architecture diagrams, and non-data visual explanation.
- `paper-writing.md`: paper-writing branch selector and evidence-triggered reasoning narrative discipline.
- `paper-depth-and-page-budget.md`: evidence-based main-text depth profiles,
  section budgets, and detailed-versus-brief writing rules.
- `paper-writing-zh-cn-format2025.md`: historical Chinese layout reference based
  on the supplied 2025 format document; never override the current CUMCM 2026
  profile or fresh official rules with it.
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
| Compliance | `contest_manifest.json`, `rules.lock.json`, saved official snapshots, AI log, selected template/profile | Rule URLs, hashes, validity and structured fields pass; live-mode boundary recorded |
| CUMCM selection | A/B/C screening, criterion evidence, capability snapshot, JSON/Chinese recommendation, user confirmation | Equal staged budgets; all evidence hashes current; unsupported percentages omitted; H6 lock matches the confirmed recommendation or a documented exception |
| Analysis | `reports/problem_analysis.md` | Every subproblem mapped; CUMCM uses task-to-model routing |
| Data | `reports/data_audit.md`, `reports/traceability.md`, `reports/claims.csv` | Data provenance and claim-to-result chain complete |
| Modeling | `reports/model_design.md`, `reports/model_decision_log.csv`, `reports/parameter_registry.csv`, conditional `reports/joint_inference_design.json` | Model ladder is evidence-led; parameters and identifiability are explicit; route selection is justified against a baseline |
| Literature | `reports/bibliography.csv`, metadata snapshots, passage evidence, `paper/references.bib` | At least 10 uniquely cited, relevant works have hash-bound authoritative metadata, exact-title Scholar queries, retraction checks, checked passages, claim IDs, reachable paper locations, and removal-impact evidence |
| Computation | code/notebooks, `results/verified_values.csv`, generated LaTeX macros, model-validation report, optional `reports/model_kernel_usage.csv`, `reports/compute_budget.csv`, `reports/compute_runs.jsonl`, independent routes, reconciliation, stress/units ledgers | Executed; hashes and units reconcile; synthetic kernel checks stay separate from contest evidence; primary/fallback runtime, memory scope, timeout, solver evidence, diagnostics, conflicts, and decisive claims are challenged |
| Figures/tables | `figures/`, tables, figure manifests, page overview | Hash-bound at insertion size; text, lines, resolution, clipping, hierarchy, grayscale, and color-vision reviews are recorded |
| Writing | `paper/main.tex`, `paper/main.pdf`, generated result fragments, `reports/paper_reasoning_map.csv`, numeric and prose exception ledgers, notation/dimension registry, complete portable LaTeX source tree | Every abstract/conclusion number is a verified macro or narrow structural exemption; evidence-triggered model choice, parameter provenance, real failed runs, and boundaries have natural paper locations and a named human reviewer; Chinese prose findings are located for human review; symbols and units reconcile; Overleaf-style root and VS Code `build/` outputs pass |
| Final check | verification report, paper-depth report, argument coverage, claim report, model/value reports, `reports/latex_compatibility.json`, PDF visual report, portable-source ZIP report, `reports/paper_delivery.json` | Depth, compile, visual, anonymity, numeric, reproduction, and delivery gates pass or name scoped limitations |
| Optional review | blinded reviewer reports, aggregation, `reports/reviewer_scorecard.csv`, award-readiness report | Only after explicit user opt-in; objections cite artifacts, vetoes are resolved or disclosed, and final checks rerun after changes |
| Skill release | blinded benchmark manifest and regression report | No score exceeds its accepted regression tolerance; baselines are never changed automatically |
| Delivery | `delivery/` PDF/source/support manifests | Complete user handoff is frozen, verified, and anonymous |
| Submission | profile-permitted files under `official-submission/`, hash manifest, receipt evidence | No forbidden extra files; official artifacts pass the selected profile |

## Fallback Behavior

If a helper capability is unavailable:

1. Continue with the same phase manually.
2. Use plain Markdown, CSV, scripts, or text artifacts where possible.
3. Record what was not verified in `reports/verification_report.md`.
4. Do not claim visual, formula, or execution verification unless it was actually performed.
