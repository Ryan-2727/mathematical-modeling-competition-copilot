# Mathematical Modeling Competition Copilot

Mathematical Modeling Competition Copilot is a self-contained Codex skill for end-to-end mathematical modeling contest work. It coordinates problem analysis, modeling, literature detail resolution, reproducible computation, figures, tables, paper writing, and final verification for contests such as MCM/ICM, CUMCM, Huawei Cup, and school-level modeling competitions.

## Explicit Invocation Only

This skill is never intended to trigger from an ordinary modeling, contest, or
paper-writing question. Invoke it explicitly with
`$mathematical-modeling-competition-copilot` or a direct link to `SKILL.md`.

```text
Use $mathematical-modeling-competition-copilot for this contest problem.
```

[![Switch to Chinese](https://img.shields.io/badge/README-%E4%B8%AD%E6%96%87-d93025)](README.zh-CN.md)

## Self-Contained Version

A new computer can install only this repository and still get the full mathematical modeling competition workflow. The workflow knowledge that used to be spread across multiple helper skills is now embedded under `references/embedded/`:

- contest setup and `plan.md` / `todo.md`
- award-oriented evidence gates, generic 72-hour control, and an exact CUMCM
  2026 74-hour board with stop-loss rules
- bounded brainstorming for model-route selection
- problem-structure playbooks and an auditable baseline-versus-candidate model decision log
- mathematical modeling six-phase workflow
- LLM-MM-Agent four-stage methodology and HMML/MLE-Solver-style modeling
- literature search and paper explanation workflows
- a verified bibliography ledger: at least 10 real, relevant, uniquely cited
  scholarly works, authoritative metadata, exact-title Google Scholar queries,
  checked source passages, complete claim IDs, reachable manuscript locations,
  and an explicit removal-impact check that rejects count-padding citations
- a targeted, machine-validated CUMCM B/C model-card library covering designed
  experiments, bearing-only localization, coverage, sequential decisions,
  compositional data, robust planning, price-demand, longitudinal timing, and
  calibrated imbalanced classification
- five bounded executable B/C reference kernels with explicit standard-library
  and scientific backends, synthetic hidden-truth recovery, metamorphic
  invariance, degradation, feasibility, and degenerate-case checks
- narrow paper and reproduction detail resolution
- code, notebooks, result tables, and data-driven figures
- source-scope and unit checks plus predeclared, failure-oriented stress tests
- flowcharts and architecture diagrams
- paper writing router with a current CUMCM 2026 executable profile, a retained
  Chinese 2025 historical layout reference, and an English contest baseline branch
- cross-year exemplar-corpus lessons for structure, visuals, and evidence narrative
- LaTeX and academic table rules
- a portable XeLaTeX/latexmk paper scaffold that compiles and previews in both
  Overleaf and VS Code
- final verification rules
- fallback rules for missing tools
- contest mode, current-rules snapshot, AI-use evidence, and submission freeze
- hash-bound official-rule locks and cumulative setup/modeling/paper/delivery/freeze phase gates
- data audit, traceability, environment capture, anonymity scanning, and hashing
- A single machine-readable CUMCM 2026 rule profile with T-30/T-7/T-1 freshness checks, official
  locator/page/PDF snapshots, the 2026 AI declarations, an H6 weight-sensitivity
  problem audition, the 20:00 MD5 deadline, the 20:30-to-next-day-14:00 upload
  window, actual frozen-file/client-MD5 comparison, official two-metric
  similarity evidence, and P90/trend/two-full-pass readiness scoring
- a precise live-contest internet boundary: generic official, scholarly, and
  static-reference research is allowed, but browsing current-problem content on
  communication platforms is forbidden; uncertain classifications pause for
  user input, and search terms have no lexical blacklist
- executable CUMCM and MCM/ICM rule profiles with separate portable LaTeX
  templates selected automatically at project initialization
- a decisive-value registry that generates LaTeX macros from hashed computation
  outputs, plus 11 model-family validation adapters
- literal-level abstract/conclusion number checks: every result number comes
  from a verified macro, while narrow structural exceptions need a line-bound
  exemption record
- an evidence-based complexity gate: a stronger candidate remains out of the
  main model unless its measured advantage reaches a positive predeclared threshold
- answer-oriented abstract, authoritative bibliography snapshot, supporting-passage,
  LaTeX-log, caption/label, and figure-manifest checks
- clean-copy, repeated-run reproduction without implicit shell execution
- PDF rendering/metadata QA, image/OCR-aware anonymity checks, and real TeX CI
- optional post-paper award review: three reviewer lenses, a four-dimension evidence scorecard, and structural award-readiness verification, only after user confirmation
- blinded independent-review aggregation and hidden benchmark regression for
  learning reusable strengths without paired solutions or automatic baseline changes
- a hard two-part delivery gate: compiled PDF plus complete LaTeX source, and a
  hashed support archive containing code, data evidence, environment, commands,
  and results
- separate `delivery/` and `official-submission/` roots so user-side source and
  support files cannot leak into a contest profile that forbids them

## Hard Completion Contract

A completed paper must satisfy both conditions:

1. `paper/main.pdf` is compiled from the delivered LaTeX source, and the source
   includes `paper/main.tex`, `paper/references.bib`, all included sections, and
   every required figure, table, class, style, and asset.
2. `support.zip` contains runnable code, legally distributable data or reproducible
   retrieval evidence, environment/dependency evidence, exact commands,
   representative results, licenses, and SHA-256 hashes.

The LaTeX body must cite at least 10 unique, relevant scholarly works. Each source
is recorded in `reports/bibliography.csv`, checked against authoritative metadata,
confirmed by an observed exact-title Google Scholar result, and read at the passage supporting the
paper's claim. `verification_source` must be a record-specific HTTPS Crossref,
DOI, or OpenAlex URL, and Scholar queries use the canonical
`https://scholar.google.com/scholar?q=...` endpoint. Each row also names a
completed claim, reachable paper location, evidence role, relevance reason, and
what support would be lost if the source were removed. If ten relevant sources
are not available, the workflow reports a gap instead of inserting an unrelated
paper. Fabricated metadata or source content is prohibited. Run
`scripts/verify_bibliography_metadata.py` against saved authoritative metadata
and supporting-passage hashes, then run
`scripts/verify_paper_delivery.py` before claiming completion; its pass is a
structural check and does not replace human source reading or PDF inspection.
First run `scripts/verify_latex_compatibility.py`: it must produce a fresh,
compile-backed `reports/latex_compatibility.json` after successful
Overleaf-style and VS Code-style builds.

## Executable Evidence Gates

Initialization selects the contest template and submission profile:

```bash
python scripts/init_contest.py --project-dir <project> --contest CUMCM --year 2026 --mode training
python scripts/init_contest.py --project-dir <project> --contest MCM/ICM --year 2027 --mode training
```

The unified controller preserves the existing `check` command and adds
versioned migration, runtime diagnosis, dependency-aware execution, and summaries:

```bash
python scripts/contestctl.py migrate --project-dir <project>
python scripts/contestctl.py migrate --project-dir <project> --apply
python scripts/contestctl.py doctor --project-dir <project> --profile standard
python scripts/contestctl.py run --project-dir <project> --phase selection --profile standard
python scripts/contestctl.py run --project-dir <project> --phase paper --profile standard
python scripts/contestctl.py run --project-dir <project> --phase freeze --profile strict
python scripts/contestctl.py summary --project-dir <project>
```

Use `minimal` for fast standard-library checks, `standard` for normal work with
honest `LIMITED` results when optional tools are absent, and `strict` before
submission. `custom` accepts only registered node identifiers, never arbitrary
shell commands. Migration is preview-only unless `--apply` is supplied and
preserves existing and unknown evidence fields.

Paper assurance now includes:

- `verify_rendered_figures.py`: output/source hashes, generation identity,
  insertion-size text/line/DPI checks, grayscale and color-vision previews, and
  a full-paper page overview when rendering tools are available;
- `verify_notation_registry.py`: first definitions, symbol/type/style mappings,
  code and figure names, units, and declared equation dimensions;
- `generate_paper_artifacts.py`: traceable core-result, model-comparison,
  robustness, conclusion, and figure-note LaTeX fragments under
  `paper/generated/`, without overwriting manual sections.

The release and paper workflow then uses deterministic checks:

- `lock_contest_rules.py` binds saved official rule snapshots to URLs, hashes,
  structured fields, a validity date, and the CUMCM 2026 freshness checkpoints.
  `contestctl.py check` coordinates
  cumulative phase gates without replacing specialist verifiers.
- `contestctl.py run --phase selection` compares CUMCM A/B/C through staged,
  equal-budget executable trials, updates the bundled AI prior with same-day
  evidence, and writes hash-bound JSON plus a Chinese strengths/weaknesses
  report. Award intervals appear only with sufficient verified local
  calibration; `record_problem_selection_confirmation.py` records the user's
  declared choice, and `verify_problem_audition.py` enforces the confirmed H6
  lock without scoring the student team or auto-selecting a problem;
  `score_training_readiness.py` scores 8/24/48/74-hour drills with median, P90,
  worst case, trend, recurrence, role/owner bottlenecks, and a
  latest-two-full-pass readiness gate;
  `verify_online_actions.py` audits the declared local-only online boundary.
- `verify_submission.py --profile cumcm-2026 --ai-mode none|used` checks the
  exact pre-reference 2026 declaration or the complete AI-use evidence chain.
  A live project initialized through this AI skill is forced to `used`; its
  declaration purpose remains an editable LaTeX block and is not overwritten
  after a human edit.
- `results/verified_values.csv` is the single source of truth for decisive
  computed values; `generate_verified_values.py` creates
  `paper/generated/results.tex`, and `verify_verified_values.py` checks hashes,
  types, units, reachability, and staleness.
- `verify_model_validation.py` checks declared evidence for forecast/regression,
  classification, optimization, stochastic simulation, network/ranking,
  mechanism/dynamics, causal/econometric, unsupervised, queueing/reliability,
  spatial/spatiotemporal, and multi-objective/dynamic optimization models. It
  does not certify mathematical truth.
- `run_model_kernel.py` and `run_model_kernel_regression.py` provide five
  auditable micro-implementations; `verify_model_kernel_evidence.py` keeps their
  synthetic results separate from contest evidence and binds actual inputs,
  outputs, backends, and hashes.
- `profile_compute_run.py` measures real primary/fallback commands, timeouts,
  wall time, memory scope, solver evidence, logs, and result hashes;
  machine-specific command paths are redacted but hash-bound, and
  `verify_compute_budget.py` rejects stale, unscaled, or deadline-infeasible runs.
- `verify_abstract_quality.py`, `verify_summary_numeric_traceability.py`,
  `verify_bibliography_metadata.py`, and
  `verify_manuscript_quality.py` check answer coverage, saved source evidence,
  references, captions, labels, figure manifests, and LaTeX logs.
- `verify_chinese_academic_style.py` emits advisory, line-located Chinese prose
  findings and hash-bound human exceptions without automatically rewriting LaTeX.
- `verify_paper_reasoning_narrative.py` checks that executed model comparisons,
  claim-sensitive parameter sources, genuine failed runs, and conditional
  boundaries are placed naturally in the paper and reviewed by a named person;
  it requires no stock headings and never infers authorship.
- `verify_delivery_profiles.py` verifies the full user handoff separately from
  the files allowed in the official contest submission.
- `run_reproduction.py` runs argv-based commands in a clean copy, retains
  per-run logs, and compares repeated outputs by hashes or declared numeric
  tolerances. Shell execution requires explicit opt-in.
- `sync_local_skill.ps1 -Verify` performs a read-only hash audit of the local
  installation, reports missing, mismatched, and extra files, and never deletes
  extra local content.
- `verify_pdf_visual.py`, `anonymity_scan.py`, and `verify_submission.py`
  distinguish `PASS`, `LIMITED`, and `FAIL`; a mandatory visual rule cannot pass
  merely because a renderer or OCR tool is absent.
- `run_benchmark_regression.py` evaluates blinded artifact/rubric manifests.
  Regressions beyond tolerance block a skill release, and baselines are never
  rewritten automatically.
- `prepare_private_regression.py` inventories a user-owned historical corpus and
  copies only an explicit allow-list into a private, non-overlapping benchmark
  root. Its default inventory is metadata-only; selected calibration cases can
  be inspected explicitly. It rejects path escapes and generated solution artifacts; private
  manifests, statements, data, outputs, and scores must never be committed.
- `probe_runtime_capabilities.py` records the exact available solver/runtime
  profile before model selection; missing capability is a visible limitation,
  never a silent algorithm substitution or an automatic package install.
- `verify_data_cache.py` binds large-data aggregates to raw/cache hashes,
  aggregation rules, and leakage-safe time splits. `verify_result_template.py`
  audits an explicitly declared result template without copying it or using its
  prefilled values as evidence.
- `score_private_regression.py` emits a metadata-only private rubric for input
  audit, feasibility, reproducibility, writing, and visual communication. It
  contains statuses, hashes, and optional private evidence locators only—not
  historical statements, answers, or data—and classifies recurring defects.
- For price, policy, treatment, or intervention questions, the workflow first
  separates predictive from causal claims; causal conclusions require an
  estimand and identification evidence. Material decision uncertainty requires
  a robust, stochastic, or scenario comparison against the expected-value baseline.
- `verify_evidence_chain.py` binds each decisive claim to its executable command,
  data/result hashes, verified-value LaTeX macro, figure label, and paper location;
  a changed result requires regenerated values, figures, and PDF.
- `verify_decision_quality.py` requires model refutation against a baseline,
  material-uncertainty comparison, degradation routes, causal boundaries, and
  implementation readiness. `verify_figure_narrative.py` removes figures that
  cannot state their question, claim, reader takeaway, and decision relevance.
- `verify_page_readability.py` checks a page-by-page human checklist for abstract
  density, definitions, figure legibility, whitespace, table breaks, appendix
  boundaries, and reference consistency before submission freeze.
- `verify_answer_density.py` requires each abstract/conclusion answer to map to
  a direct result or recommendation, validation, and limitation;
  `verify_visual_design_system.py` records a shared figure/table style profile;
  `verify_paper_presentation.py` binds a rendered-PDF page checklist for
  hierarchy, font readability, formula/table breaks, whitespace, and consistency.
  These are evidence gates, not automated beauty scores.
- `verify_abstract_structure.py` requires a concise analysis-method-result
  abstract. `verify_result_story.py` blocks finalization without a verified
  result decision, explicit user authorization for simplification, a result
  chart per subproblem, and a comparison visual when models are compared.
- `verify_modeling_argument_quality.py` binds data semantics to mechanisms,
  requires two independent checks when ground truth is absent, maps every answer
  to a decisive value and limitation, and rejects innovation claims without a
  problem-specific, measured incremental benefit.
- `verify_model_reasoning_core.py` enforces evidence-led mechanism and model
  ladders, shared/condition-specific/nuisance parameter roles, identifiability
  boundaries, genuinely independent routes, joint-inference decisions, and
  reconciliation of material result disagreement before claim admission.
- `verify_decision_stability.py`, `verify_figure_numeric_contract.py`, and
  `verify_model_budget.py` require perturbation-aware recommendations, traceable
  figure numbers, and a baseline-first route that fits the remaining contest time.
  `verify_three_minute_review.py` makes the abstract-to-limitation reviewer path
  explicit, while `verify_latex_dependency_lock.py` freezes portable compiler,
  package, font, and editor-configuration evidence. All five reports are hash-bound
  during submission freeze; unavailable compilers are `LIMITED`, never a false pass.

## CUMCM Model Routing

For the China Undergraduate Mathematical Contest in Modeling (CUMCM), the skill reads `references/embedded/cumcm-model-selection.md` before selecting methods. It maintains a trace for every subproblem: `task signal -> model -> implementation -> validation -> result -> paper section`.

- It routes optimization and scheduling, networks and paths, multi-criteria evaluation, prediction and fitting, statistics and classification, stochastic systems, and mechanistic dynamic models.
- The guide covers the local 30-chapter model library and discriminant analysis, including programming, AHP, grey systems, time series, regression, queueing, Markov chains, and differential equations.
- Python, MATLAB, and LINGO are equal implementation paths. The skill chooses according to model fit, reproducibility, and the team's available environment; it does not require using all three.
- Each model card states when to use it, common misuse, implementation limits, and a minimum validation gate. The default is an interpretable baseline, followed by at most one evidence-backed enhancement or comparison.

CUMCM example:

```text
Use $mathematical-modeling-competition-copilot for CUMCM. We have three days and can use Python, MATLAB, and LINGO. First produce the problem decomposition, model options, and validation plan.
```

## Capabilities That Cannot Be Fully Embedded

Some capabilities require Codex plugins or local runtimes. Install or enable these in Codex when needed:

| Capability | Install or enable | Fallback when unavailable |
| --- | --- | --- |
| Jupyter notebook creation, editing, execution | Data Analytics plugin, `jupyter-notebooks` | Use Python scripts and Markdown reports; record that notebook execution was not verified |
| DOCX creation, editing, render QA | Documents plugin | Draft in Markdown/LaTeX; record that DOCX visual QA was not performed |
| PDF rendering, extraction, page inspection | PDF plugin | Generate source files or request local PDF review; record unverified items |
| XLSX formulas, charts, workbook rendering | Spreadsheets plugin | Use CSV/Markdown tables; record that formulas or layout were not verified |

These are not automatically bundled by this repository because they require file-processing runtimes, renderers, or plugin tools.

## What This Skill Does

This skill acts as the main entry point for a mathematical modeling project. It does not claim to guarantee an award. Its purpose is to improve the probability of a strong submission by enforcing a disciplined workflow:

1. Freeze the contest mode and snapshot current official rules, AI policy, deadline, and submission procedure.
2. Decompose the problem into subquestions and build a traceability table.
3. Audit data, reconcile units, compare a credible baseline against candidates, and record why the selected model fits the mechanism.
4. Resolve literature or reproduction-critical details within the contest’s source and communication rules.
5. Run reproducible code, notebooks, or spreadsheets with environment, data-hash, solver, uncertainty, and failure-oriented stress-test evidence.
6. Generate figures, flowcharts, and tables that support explicit claims.
7. Assemble and compile the portable XeLaTeX paper in both Overleaf and VS Code
   build layouts with at least 10 verified, actually cited scholarly sources;
   disclose AI use as required.
8. Build and verify the separate support-material archive with code, data evidence, environment, commands, results, licenses, and hashes; keep it in the user delivery even when the official contest forbids extra files.
9. After the full paper and baseline verification are complete, offer an optional independent review of assumption rationality, model creativity, result correctness, and writing clarity.
10. Scan anonymity, freeze hashes, verify the profile-limited
    `official-submission/` artifacts, and record receipt evidence.

## When To Use

Use this skill when you want Codex to help with:

- MCM/ICM, CUMCM, Huawei Cup, or similar mathematical modeling contests.
- Turning a contest statement into a model plan and paper outline.
- Building a reproducible modeling project with code, notebooks, results, figures, and reports.
- Writing or polishing a mathematical modeling paper.
- Checking whether the final submission is internally consistent and ready to submit.

Example prompt:

```text
Use $mathematical-modeling-competition-copilot to solve this mathematical modeling contest problem and prepare a verified paper.
```

Chinese example:

```text
使用 $mathematical-modeling-competition-copilot 帮我完成这个数学建模题，从建模到论文终检。
```

## Workflow

0. Contest mode and compliance: `contest-modes-and-compliance.md`
1. Contest setup and strategy: `contest-setup.md`, `award-oriented-workflow.md`, and `contest-operations-72h.md`
2. Problem analysis and model design: `llm-mm-agent-methodology.md`, `mathmodel-six-phase.md`, and `problem-structure-playbooks.md`
3. Literature and reproduction details: `verified-literature-and-two-part-delivery.md`, `literature-fetch-and-explain.md`, and `paper-context-resolver.md`
4. Data audit, traceability, and computation: `data-traceability-and-reproducibility.md`, `data-units-and-source-quality.md`, `stress-testing-and-uncertainty.md`, and `computation-and-visualization.md`
5. Figures and diagrams: `diagrams.md`
6. Paper writing: `paper-writing.md`, `latex-paper-pipeline.md`, and the current-rules branch
7. Final verification and submission: `verify_paper_delivery.py`, `final-verification.md`, optional `reviewer-scorecard-and-presentation.md`, and `submission-and-anonymity.md`

## Default Project Layout

```text
.
|-- plan.md
|-- todo.md
|-- rules.lock.json
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
|   |-- model_decision_log.csv
|   |-- paper_reasoning_map.csv
|   |-- stress_tests.csv
|   |-- units.csv
|   |-- bibliography.csv
|   |-- bibliography_metadata/
|   |-- source_passages/
|   |-- figure_manifest.csv
|   |-- paper_depth_plan.csv
|   |-- reviewer_scorecard.csv
|   |-- milestones.csv
|   |-- latex_compatibility.json
|   |-- portable_latex_verification.json
|   |-- paper_delivery.json
|   `-- verification_report.md
|-- environment/
|-- support/
|   |-- README.md
|   |-- reproduction_commands.txt
|   |-- materials_manifest.csv
|   `-- data_inventory.csv
|-- support.zip
|-- delivery/
|   `-- manifest.csv
|-- official-submission/
|   `-- manifest.csv
`-- paper/
    |-- main.tex
    |-- README.md
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

## Installation

Clone this repository into your Codex skills directory:

### Windows PowerShell

```powershell
git clone https://github.com/Ryan-2727/mathematical-modeling-competition-copilot.git "$env:USERPROFILE\.codex\skills\mathematical-modeling-competition-copilot"
```

### macOS/Linux

```bash
git clone https://github.com/Ryan-2727/mathematical-modeling-competition-copilot.git "$HOME/.codex/skills/mathematical-modeling-competition-copilot"
```

Restart Codex after installation so the skill is discovered.

To synchronize an existing local installation from a repository checkout on
Windows, preview first and then run:

```powershell
.\scripts\sync_local_skill.ps1 -WhatIf
.\scripts\sync_local_skill.ps1
.\scripts\sync_local_skill.ps1 -Verify
```

Use `-Verify` after synchronization to confirm the tracked payload matches the
checkout. Extra local files are reported and left untouched.

On Windows, run Python validation in UTF-8 mode:

```powershell
python -X utf8 scripts\validate_skill_contract.py
python -X utf8 -m unittest discover -s tests -v
```

## Core Repository Structure

This is a navigation view, not an exhaustive file manifest. The tested
`assets/skill-contract.json` is authoritative for required bundled resources.

```text
.
|-- SKILL.md
|-- README.md
|-- README.en.md
|-- DESCRIPTION.md
|-- assets/
|   |-- contest-profiles/cumcm-2026.json
|   |-- skill-contract.json
|   `-- latex-paper-template/
|-- scripts/
|   |-- contest_profile.py
|   |-- contestlib.py
|   |-- contestctl.py
|   |-- lock_contest_rules.py
|   |-- scaffold_latex_paper.py
|   |-- verify_paper_reasoning_narrative.py
|   |-- verify_abstract_quality.py
|   |-- verify_bibliography_metadata.py
|   |-- verify_delivery_profiles.py
|   `-- verify_latex_compatibility.py
|-- agents/
|   `-- openai.yaml
`-- references/
    |-- workflow-map.md
    `-- embedded/
        |-- contest-setup.md
        |-- cumcm-model-selection.md
        |-- mathmodel-six-phase.md
        |-- llm-mm-agent-methodology.md
        |-- literature-fetch-and-explain.md
        |-- paper-context-resolver.md
        |-- verified-literature-and-two-part-delivery.md
        |-- operational-quality-gates.md
        |-- computation-and-visualization.md
        |-- diagrams.md
        |-- paper-writing.md
        |-- paper-writing-zh-cn-format2025.md
        |-- paper-writing-en-contest-base.md
        |-- latex-tables.md
        |-- final-verification.md
        `-- tool-fallbacks.md
```

## Design Notes

This skill uses one top-level skill plus embedded reference modules, rather than nested sub-skills. That makes installation stable: Codex discovers one skill, and the skill reads its embedded phase rules as needed.

For DOCX, PDF, XLSX, and notebook work, this repository provides the workflow and fallback behavior, but users should install the corresponding Codex plugins for full file-processing capability.
