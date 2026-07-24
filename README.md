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
- award-oriented evidence gates, a 72-hour milestone board, and stop-loss rules
- bounded brainstorming for model-route selection
- problem-structure playbooks and an auditable baseline-versus-candidate model decision log
- mathematical modeling six-phase workflow
- LLM-MM-Agent four-stage methodology and HMML/MLE-Solver-style modeling
- literature search and paper explanation workflows
- a verified bibliography ledger: at least 10 real, relevant, uniquely cited
  scholarly works, authoritative metadata, exact-title Google Scholar queries,
  and checked source passages
- narrow paper and reproduction detail resolution
- code, notebooks, result tables, and data-driven figures
- source-scope and unit checks plus predeclared, failure-oriented stress tests
- flowcharts and architecture diagrams
- paper writing router with Chinese 2025 format and English contest baseline branches
- cross-year exemplar-corpus lessons for structure, visuals, and evidence narrative
- LaTeX and academic table rules
- a portable XeLaTeX/latexmk paper scaffold that compiles and previews in both
  Overleaf and VS Code
- final verification rules
- fallback rules for missing tools
- contest mode, current-rules snapshot, AI-use evidence, and submission freeze
- data audit, traceability, environment capture, anonymity scanning, and hashing
- CUMCM 2026 rule profile, AI-use PDF, evidence ledger, reproducible-run manifest, and argument-coverage checks
- optional post-paper award review: three reviewer lenses, a four-dimension evidence scorecard, and structural award-readiness verification, only after user confirmation
- hidden-exemplar regression for learning reusable strengths from excellent papers without depending on a paired solution
- a hard two-part delivery gate: compiled PDF plus complete LaTeX source, and a
  hashed support archive containing code, data evidence, environment, commands,
  and results

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
paper's claim. Fabricated metadata or source content is prohibited. Run
`scripts/verify_paper_delivery.py` before claiming completion; its pass is a
structural check and does not replace human source reading or PDF inspection.
First run `scripts/verify_latex_compatibility.py`: it must produce a fresh,
compile-backed `reports/latex_compatibility.json` after successful
Overleaf-style and VS Code-style builds.

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
8. Build and verify the separate support-material archive with code, data evidence, environment, commands, results, licenses, and hashes.
9. After the full paper and baseline verification are complete, offer an optional independent review of assumption rationality, model creativity, result correctness, and writing clarity.
10. Scan anonymity, freeze hashes, verify submission artifacts, and record receipt evidence.

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
|   |-- stress_tests.csv
|   |-- units.csv
|   |-- bibliography.csv
|   |-- reviewer_scorecard.csv
|   |-- milestones.csv
|   `-- verification_report.md
|-- environment/
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
```

## Repository Structure

```text
.
|-- SKILL.md
|-- README.md
|-- README.en.md
|-- DESCRIPTION.md
|-- assets/
|   `-- latex-paper-template/
|-- scripts/
|   |-- scaffold_latex_paper.py
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
