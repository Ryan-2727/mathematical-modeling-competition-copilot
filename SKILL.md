---
name: mathematical-modeling-competition-copilot
description: Explicit-invocation-only end-to-end mathematical modeling competition workflow for contest problem solving and paper production. Use ONLY when the user explicitly invokes `$mathematical-modeling-competition-copilot` or supplies a direct link to this SKILL.md. Do not use it automatically for ordinary mathematical modeling questions.
---

# Mathematical Modeling Competition Copilot

Do not infer invocation from a modeling, contest, or paper-writing request. Use
this workflow only when the user explicitly calls this skill or links this file.

When invoked, coordinate contest setup, modeling, literature, computation,
visualization, LaTeX paper production, verification, and delivery. This workflow
does not guarantee an award; it improves award readiness through reproducible
evidence, restrained claims, and reader-focused presentation.

## Operating contract

- Follow phases 0--12 in order. Re-enter an earlier phase when a later gate
  exposes a source defect.
- Read only the references named for the current phase. Use
  `references/workflow-map.md` only for routing; do not load every module.
- Initialize with `scripts/init_contest.py`. Preserve nonempty user work and
  preview migrations before applying them.
- Use `scripts/contestctl.py doctor`, select `minimal`, `standard`, `strict`, or
  a declared custom profile, and run the phase check after specialist artifacts
  exist. Fix source artifacts, never generated gate reports.
- Use installed file plugins when available. If a renderer, extractor, solver,
  or plugin is unavailable, follow `references/embedded/tool-fallbacks.md` and
  record the scoped limitation; never infer verification.
- Treat every `PASS` as evidence that the declared check passed, not proof that
  the mathematics is true or that an award will be won.

## Required workflow

### 0. Contest mode, rules, privacy, and compliance

Read:

- `references/embedded/contest-modes-and-compliance.md`
- `references/embedded/executable-contest-profiles.md`
- `references/embedded/operational-quality-gates.md`
- for CUMCM 2026, `references/embedded/cumcm-2026-rules.md` and
  `references/embedded/cumcm-2026-readiness.md`

Required actions:

- Declare training, live, or post-hoc mode; contest, year, language, deadline,
  selected executable profile, and deliverables in `contest_manifest.json`.
- Save fresh official rule snapshots locally, run
  `scripts/lock_contest_rules.py`, and require hash-bound `rules.lock.json` plus
  `reports/rules_lock_verification.json`. An initializer skeleton is not
  official evidence, and a prior-year rule is never the silent default.
- Keep current contest statements, attachments, data, screenshots, ideas,
  code, results, paper fragments, and summaries local. Internet search is
  allowed; current-problem answer searching, interactive help, public posting,
  and uploading contest material are forbidden. If privacy is ambiguous, ask
  the user and wait for the answer. Record online actions locally.
- Before reading a live statement, record whether the AI runtime is demonstrably `local_offline` or an `external_service`. When it is external, do not send the
  current statement, attachments, data, code, results, or paper content to it; this skill cannot honestly guarantee a no-upload boundary for external inference.
  Search queries remain governed by the online-action ledger, and an ambiguous privacy effect requires the user's recorded decision.
- Record material AI use from the first use. Invoking this AI skill during a live
  CUMCM 2026 project necessarily selects `ai_mode=used`; it must never
  self-certify `none`. Initialize live mode with actual `--ai-tool`,
  `--ai-version`, and `--ai-runtime-boundary` values.

### 1. Setup, problem audition, and strategy

Read:

- `references/embedded/contest-setup.md`
- `references/embedded/award-oriented-workflow.md`
- `references/embedded/contest-operations-72h.md`
- for CUMCM, `references/embedded/cumcm-model-selection.md`

Required actions:

- Confirm the team role split, available Python/MATLAB/LINGO runtimes, time
  budget, attachment inventory, and submission constraints.
- Use the bounded brainstorming gate before committing to a route. Create
  `plan.md`, `todo.md`, and `reports/milestones.csv`.
- For CUMCM 2026, follow the staged A/B/C audition in the readiness reference;
  fill `problem_screening.csv`, `problem_selection_evidence.csv`, and
  `problem_audition.csv`, then run `contestctl.py run --phase selection`.
  Show both recommendation reports to the user, record their declared choice
  with `record_problem_selection_confirmation.py`, and only then run
  `verify_problem_audition.py`. Never invent award percentages; use the exact
  74-hour schedule and require an evidence-backed exception for another choice.

### 2. Problem analysis and model design

Read:

- `references/embedded/llm-mm-agent-methodology.md`
- `references/embedded/mathmodel-six-phase.md`
- `references/embedded/problem-structure-playbooks.md`
- for recurring CUMCM B/C structures,
  `references/embedded/cumcm-bc-model-library.md`
- `references/embedded/mechanism-semantics-and-argument.md`
- `references/embedded/model-reasoning-kernel.md`
- for physical measurement, system identification, spectroscopy, imaging, or
  signal inversion, `references/embedded/physics-inverse-modeling-playbook.md`

Required actions:

- Map every subproblem to inputs, mechanism, decision variables, assumptions,
  objectives, constraints, candidate models, validation, result artifact,
  figure/table, and paper section in `reports/traceability.md`.
- Audit schema, units, time cutoff, attachment coverage, and zero, blank,
  censored, missing, and not-observed meanings in `reports/semantic_audit.csv`
  and `reports/mechanism_audit.json`. Do not disguise unknown semantics as an
  assumption.
- Validate the B/C cards with `scripts/verify_model_library.py`. When using a bundled kernel, run its synthetic regression and bind actual input/output in
  `reports/model_kernel_usage.csv`; still require structural fit, the baseline, diagnostics, falsification, and the predeclared promotion threshold.
- Compare one credible baseline with a stronger candidate in
  `reports/model_decision_log.csv`. Predeclare the candidate's advantage and
  failure test in `reports/model_challenge.json`; reject it or narrow the claim
  when the threshold is not met. Do not stack models for appearance.
- Build mechanism and candidate-model ladders before optimization. Add one
  mechanism at a time, register every parameter as shared,
  condition-specific, nuisance, or fixed, and issue an identifiability verdict
  of `PASS`, `CONDITIONAL`, or `FAIL`. Simplify, reparameterize, or add data
  conditions after `FAIL`; an optimizer cannot repair non-identifiability.
- When repeated conditions exist, compare separate fits with the explicit joint
  design in `reports/joint_inference_design.json`. Do not silently force or
  average shared parameters.
- Classify constraints as local or coupled. For coupled systems, audit input
  decoding and the constraint graph and require joint feasibility; an
  independent node-by-node projection is diagnostic only.
- Distinguish prediction from causality before model selection. Causal language
  requires an estimand, counterfactual, causal graph, confounders,
  identification assumptions, and diagnostics.
- Prepare `reports/fallback_plan.csv`. If a primary model produces no verified
  result, record the failure and ask the user before removing named
  noncritical factors. Put an attractive but unverified model under model
  optimization, never in the results.

### 3. Literature and narrow reproduction details

Read as applicable:

- `references/embedded/verified-literature-and-two-part-delivery.md`
- `references/embedded/literature-fetch-and-explain.md`
- `references/embedded/paper-context-resolver.md`

Required actions:

- A completed paper needs at least 10 unique, relevant scholarly works cited in reachable LaTeX. Maintain `reports/bibliography.csv`; for every source record its
  evidence role, complete claim ID, reachable paper location, relevance justification, and what support would be lost if it were removed. If ten relevant works
  have not been verified, report the gap instead of adding an unrelated citation.
- Verify metadata against authoritative records, observe an exact-title Google
  Scholar result, read the passage supporting each attributed claim, and save
  locators and hashed evidence. Never fabricate metadata or source content.
- Run `scripts/verify_bibliography_metadata.py`. Its pass does not replace
  source reading or interpretation.

### 4. Computation, validation, and decision evidence

Read:

- `references/embedded/computation-and-visualization.md`
- `references/embedded/data-traceability-and-reproducibility.md`
- `references/embedded/runtime-template-and-decision-audits.md`
- `references/embedded/award-oriented-evidence-chain.md`
- `references/embedded/data-units-and-source-quality.md`
- `references/embedded/stress-testing-and-uncertainty.md`
- `references/embedded/diagnostics-and-result-reconciliation.md`
- `references/embedded/evidence-and-quality-gates.md`

Required actions:

- Probe and lock observed runtime/solver capabilities before execution. Profile
  actual primary and fallback commands with `scripts/profile_compute_run.py`
  and verify `reports/compute_budget.csv`. Do not install dependencies or silently substitute a solver in contest mode.
- Produce every numeric conclusion from executed code, a spreadsheet formula,
  or a cited source. Maintain claims, units, commands, hashes, validation
  manifests, and a frozen reproduction run.
- Put decisive computed values in `results/verified_values.csv`, generate
  reachable LaTeX fragments, and verify that prose, tables, and figures do not
  redefine them.
- Bind every decisive claim to code/command, data hash, result hash, value key,
  LaTeX, figure, and paper location in `reports/evidence_chain.csv`.
- Select model-family validation adapters and predeclare proportionate stress
  tests. Without external truth, require at least two independent checks and
  disclose the remaining limitation.
- Record independent estimation routes in `reports/independent_routes.csv`.
  Two routes are independent only when they differ in at least two of
  mathematical principle, data representation, and principal failure mode; a
  second optimizer for the same objective tests algorithm stability only.
- Link each added mechanism to a predicted diagnostic signature, run the
  claim-proportionate diagnostic matrix, reconcile material result conflicts
  in `reports/result_reconciliation.csv`, and run
  `scripts/verify_model_reasoning_core.py` before admitting decisive values.
- Compare expected-value decisions with robust/stochastic/scenario alternatives
  when uncertainty can change the recommendation. Report feasibility, extreme
  outcomes, implementation cost/time, interpretability, failure mode, and
  contingency instead of only an objective value.
- Preserve leakage-safe time splits and immutable aggregate hashes for large
  data. Treat supplied result-form files as templates only after structural
  audit; never ingest them automatically as evidence.

### 5. Tables and scenario sheets

- Use spreadsheet reasoning for scoring matrices, sensitivity tables, scenario
  comparisons, and dashboards.
- If spreadsheet tooling is unavailable, use CSV/Markdown and record the
  limitation. Preserve units, aligned numeric columns, precision, captions,
  source notes, and result-file consistency.

### 6. Figures, flowcharts, and visual narrative

Read:

- `references/embedded/diagrams.md`
- `references/embedded/paper-presentation-and-visual-design.md`

Required actions:

- Separate data charts from explanatory diagrams. Maintain
  `reports/figure_manifest.csv` and `reports/visual_storyboard.csv`.
- Give every figure a question, linked claim, reader takeaway, decision role,
  source data, units, and legibility evidence. Use result figures for every
  subproblem; add mechanism, path/network, comparison, and validation figures
  only when they carry evidence, not decoration.
- Apply one visual design system across figures and tables and verify narrative,
  numeric contracts, insertion-size legibility, and compiled-page placement.

### 7. Result-first LaTeX paper

Read:

- `references/embedded/paper-writing.md`
- `references/embedded/result-first-paper-convergence.md`
- `references/embedded/paper-depth-and-page-budget.md`
- for CUMCM 2026, `references/embedded/cumcm-2026-rules.md`; use
  `references/embedded/paper-writing-zh-cn-format2025.md` only as a historical
  layout baseline
- `references/embedded/paper-writing-en-contest-base.md` and
  `references/embedded/paper-writing-mcm-icm-current.md` for MCM/ICM
- `references/embedded/latex-paper-pipeline.md`
- when learning from an offline corpus,
  `references/embedded/paper-learning-from-exemplars.md`,
  `references/embedded/2025-corpus-observations.md`, and
  `references/embedded/multi-year-corpus-observations.md`

Required actions:

- Create `reports/paper_depth_plan.csv`, `reports/conclusion_map.csv`, and an
  innovation ledger with at most one measured, problem-specific improvement per
  subproblem. Before drafting, set the rule-bound ceiling and a task-specific
  main-text budget; for CUMCM 2026, require abstract <=1 page, no contents page,
  main text <=30 pages excluding unlimited appendices, and normally plan 20--25
  information-dense main-text pages rather than filling the limit. Reject or
  narrow unsupported innovation claims.
- Write the abstract in three concise blocks: analysis, method, and quantified
  result. Begin every subproblem from its direct answer and preserve the chain
  mechanism -> rationale -> variables/assumptions -> derivation -> algorithm ->
  result/interpretation -> local validation -> limitation.
- Show why the selected model was promoted from its simpler parent, which
  parameters are shared across conditions, whether an independent route
  supports the conclusion, and how any material disagreement was resolved. Bind
  the modeling path, claim-sensitive parameter provenance, genuine failed runs,
  triggered boundary cases, and a named human review location through
  `reports/paper_reasoning_map.csv`, then run
  `scripts/verify_paper_reasoning_narrative.py`. Integrate these facts where the
  argument needs them; never fabricate an alternative or force fixed headings.
- Put every claim-bearing number in the abstract and conclusion behind `\VerifiedValue{...}` or `\VerifiedValueWithUnit{...}`. Register only genuine structural
  exceptions in `reports/numeric_exemptions.csv`, then run `scripts/verify_summary_numeric_traceability.py`.
- A candidate more complex than its baseline may be primary only when an executed comparison reaches the positive, predeclared minimum advantage in
  `reports/model_budget.csv`. Otherwise retain the simpler route and mark the candidate `rejected` or `model_optimization`; complexity is not evidence.
- The paper body must contain verified results. If a model cannot produce them, follow
  the user-approved simplification route from phase 2; retain the original
  unverified model only under model optimization.
- Generate paper artifacts and notation/dimension registries instead of
  retyping decisive values. Keep complete code, oversized tables, detailed
  intermediate results, and secondary experiments in appendices/support; retain
  the model, key parameters, core results, and model-appropriate validation in
  the body. Use current official page limits; corpus-derived ranges are advisory
  and never justify padding.
- For Chinese LaTeX, run the advisory `scripts/verify_chinese_academic_style.py`; review located formulaic openings, method catalogues, generic praise, duplicate prose, and overbroad scope by hand or bind a justified exception, but never auto-rewrite prose or infer authorship.
- Produce `paper/main.pdf` and a rebuildable UTF-8 XeLaTeX/latexmk source tree
  with relative paths, `main.tex`, bibliography, sections, generated values,
  figures, styles, `.latexmkrc`, and `.vscode/`. The same portable root ZIP must
  build and preview in Overleaf and VS Code.

### 8. Table polish

- Read `references/embedded/latex-tables.md`.
- Freeze `reports/table_manifest.csv` and verify captions, units, source notes,
  precision, alignment, continuity, and the shared visual design system.

### 9. Final verification

Read:

- `references/embedded/orchestration-and-paper-assurance.md`
- `references/embedded/decision-and-delivery-gates.md`
- `references/embedded/final-verification.md`
- when needed, `references/embedded/tool-fallbacks.md`

Required gates:

- Run the paper profile during writing and the strict freeze profile before
  submission. Under strict, unresolved `LIMITED` evidence blocks release.
- Verify claims/evidence chains, semantic and modeling arguments, executable
  kernel evidence, compute budgets, model validation, Chinese prose advisories, uncertainty/decision quality, causal boundaries, abstract/result
  story, bibliography, manuscript, figures/tables, notation/dimensions, and
  verified values.
- Compile both project-root and `build/` outputs; verify the rendered PDF,
  page-by-page readability, presentation, anonymity, portable source ZIP, and
  clean copied-project reproduction. For CUMCM 2026, explicitly record abstract
  page count, main-text page count, appendix page count, absence of a contents
  page, and whether code/large tables were correctly moved out of the body. A
  missing mandatory renderer is not a visual pass.
- Build `support.zip` from `support/materials_manifest.csv` and run the paper,
  support, delivery-profile, and submission gates. Inspect the PDF and cited
  passages separately from structural reports.

### 10. Optional award-focused review

- Only after modeling, the complete paper, and phase 9 are finished, ask whether
  the user wants this phase. Do not run it by default.
- If accepted, read `references/embedded/post-paper-award-review.md`,
  `references/embedded/reviewer-scorecard-and-presentation.md`, and
  `references/embedded/independent-review-and-regression.md`.
- Use separate blinded model, evidence, and writing reviewers with artifact
  locators. Aggregate objections and verify the internal award-readiness
  evidence structure without predicting an award. Rerun phase 9 after every
  accepted revision.

### 11. Freeze, deliver, and submit

Read `references/embedded/submission-and-anonymity.md`.

- Deliver two explicit user-facing parts under `delivery/`: (1)
  `paper/main.pdf` plus complete rebuildable LaTeX and its verified portable
  source ZIP, and (2) `support.zip` with runnable code, distributable data or
  retrieval evidence, environment, commands, results, licenses, and hashes.
- Keep only contest-permitted files under `official-submission/`. Never confuse
  the complete handoff with the official submission package.
- Run final anonymity, environment, delivery-profile, paper-delivery, portable
  LaTeX, and submission checks; record hashes and advance submission state only
  with evidence. For CUMCM 2026, enforce the selected AI branch, including
  `AI工具使用详情.pdf` for `used`. Generate the declaration starter from the completed log with `scripts/render_ai_use_report.py --declaration-out`; the delimited
  purpose text remains human-editable and later generation must preserve a non-placeholder human edit.

### 12. Offline paper-learning and private regression

Read `references/embedded/training-evaluation-loop.md`.

- After freezing an independent solution, learn reusable, non-copyrightable
  writing, presentation, and modeling-decision patterns from multiple offline
  excellent papers. Abstract only problem signals, model ladders, promotion
  triggers, parameter-sharing structures, independent-validation designs,
  diagnostics, and failure boundaries. Never use a paired paper as an input to
  a live or blinded solution, and never copy wording, numbers, task-specific
  equations, final models, or figures.
- Keep private problems, manifests, artifacts, scores, and copied inputs outside
  Git. Solve from statement/data independently, freeze the baseline, revise no
  more than three generalizable defects, then rerun blindly.
- Run blinded benchmark regression before releasing a Skill revision. Never
  update baselines automatically. Score 8/24/48/74-hour CUMCM 2026 rehearsals
  and treat private five-dimension scores as diagnostics, not award predictions.

## Core project layout

Use `scripts/init_contest.py` as the tested layout authority; see
`references/embedded/contest-setup.md` for the generated project structure.

## Global decision rules

- Ask for a missing statement before modeling. Label public or synthetic data
  explicitly and never present synthetic evidence as observed.
- Prefer a complete, interpretable baseline and verified results over extra
  model variants. Complexity without measured benefit is not creativity.
- Report solver status, feasibility, tolerance, and gap; never label a heuristic
  or incomplete solve a global optimum.
- Use one machine-readable source for decisive values and predeclare a
  proportionate failure-oriented test for each decisive conclusion.
- Do not claim completion until the compiled PDF, rebuildable LaTeX, verified
  support archive, current rule evidence, and selected submission-profile checks
  are all present.

Read `references/workflow-map.md` for the complete reference index, plugin
boundaries, phase outputs, and fallback routing.
