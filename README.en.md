# Mathematical Modeling Competition Copilot

Mathematical Modeling Competition Copilot is a Codex skill for end-to-end mathematical modeling contest work. It coordinates problem analysis, literature-supported modeling, reproducible computation, figures, tables, paper writing, and final verification for contests such as MCM/ICM, CUMCM, Huawei Cup, and school-level modeling competitions.

[中文 README](README.md)

## Short Description

An end-to-end Codex skill for mathematical modeling competitions: analyze the problem, design models, resolve literature details, run reproducible experiments, write the paper, and verify the final submission.

## What This Skill Does

This skill acts as the main entry point for a mathematical modeling project. It does not claim to guarantee an award. Its purpose is to improve the probability of a strong submission by enforcing a disciplined workflow:

1. Clarify contest constraints and strategy.
2. Decompose the problem into subquestions.
3. Design defensible mathematical models.
4. Resolve literature or reproduction-critical details when needed.
5. Run reproducible code, notebooks, or spreadsheets.
6. Generate figures, flowcharts, and tables.
7. Assemble a contest paper in DOCX, PDF, LaTeX, or Typst workflows.
8. Verify requirements, formulas, results, formatting, and final files before completion.

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

### 1. Contest Setup And Strategy

The skill first confirms the contest type, paper language, submission format, time budget, team responsibilities, available data, and expected deliverables. If the task is ambiguous, it uses a brainstorming step before modeling.

Expected outputs:

- `plan.md`
- `todo.md`
- contest constraints and success criteria

### 2. Problem Analysis And Model Design

The skill uses an LLM-MM-Agent-inspired four-stage loop:

- Problem analysis
- Mathematical modeling
- Computational solving
- Solution reporting

It also applies HMML-style method selection: choose a modeling domain, narrow the subdomain, compare candidate methods, and select the simplest defensible model that can answer the problem.

Expected outputs:

- subproblem map
- assumptions
- variables and parameters
- constraints and objective functions
- candidate methods and model rationale
- validation plan

### 3. Literature And Reproduction Details

For narrow reproduction-critical gaps, the workflow can use `paper-context-resolver`. This is intentionally scoped. It is for details such as dataset splits, preprocessing, evaluation protocols, method assumptions, or conflicts between a paper and repository instructions.

It should not be used for broad paper summaries. General literature review should extract only methods, data, or validation ideas that improve the contest solution.

Expected outputs:

- source notes
- direct evidence versus inference
- explicit conflict notes when sources disagree

### 4. Computation And Experiments

The workflow separates raw data, processed data, code, notebooks, result tables, and generated figures. Numeric claims must come from executed code, spreadsheet formulas, or cited sources.

Expected outputs:

- `code/`
- `notebooks/`
- `results/`
- `reports/experiment_log.md`
- reproducibility status

### 5. Tabular Analysis And Scenario Sheets

The skill uses spreadsheet workflows when the task involves scoring matrices, sensitivity analysis, scenario comparison, dashboards, or Excel deliverables.

Rules:

- Keep formulas visible and traceable.
- Avoid hardcoding derived values.
- Label units and assumptions.
- Record source data paths.

### 6. Figures, Flowcharts, And Diagrams

Data-driven plots and non-data diagrams are treated separately.

- Data charts belong to the computation and visualization phase.
- Flowcharts, method diagrams, causal diagrams, and framework diagrams belong to the diagramming phase.
- Decorative duplicates of data charts are avoided.

Expected outputs:

- `figures/`
- plot source data or script references
- diagram source files when available

### 7. Paper Writing

The paper workflow assembles the model, results, figures, tables, assumptions, and validation into a contest-ready paper.

The final paper should include:

- a sharp abstract
- clear assumptions and notation
- model sections aligned to subproblems
- reproducible result references
- readable figures and tables
- sensitivity or robustness analysis
- honest limitations
- method and data references

### 8. Table Polish

For LaTeX papers, the workflow can use `latex-tables` for academic tables such as regression tables and summary statistics. For general contest tables, it enforces concise captions, units, source notes, aligned numeric columns, reasonable precision, and consistency with result files.

### 9. Final Verification

The workflow ends with hard verification before completion claims.

Checks include:

- Every subproblem has an answer.
- Every table and figure is referenced and captioned.
- Units, symbols, and variable names are consistent.
- Code or notebook execution status is recorded.
- Literature claims have source links or citations.
- DOCX, PDF, LaTeX, or Typst output is visually inspected when applicable.
- The final response states what was verified and what remains unverified.

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
|   `-- verification_report.md
`-- paper/
```

## Integrated Skills

This skill can coordinate these installed or plugin-provided skills when available:

- `brainstorming`
- `1start-mathmodel`
- `2analysis-modeling`
- `3coding-visual`
- `4drawio`
- `5writing`
- `6verity`
- `llm-mm-agent`
- `paper-context-resolver`
- `latex-tables`
- `verification-before-completion`
- `jupyter-notebooks`
- `documents`
- `pdf`
- `spreadsheets`

If an integrated helper is unavailable, the workflow continues manually and records the missing helper in `reports/verification_report.md`.

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

## Repository Structure

```text
.
|-- SKILL.md
|-- README.md
|-- README.en.md
|-- DESCRIPTION.md
|-- agents/
|   `-- openai.yaml
`-- references/
    `-- workflow-map.md
```

## Design Notes

This skill intentionally stays lightweight. It does not bundle a full modeling framework, solver runtime, or paper template system. Instead, it gives Codex a reliable orchestration layer and uses specialized skills or tools only when they are relevant to the current contest task.

The skill treats the LLM-MM-Agent project as a methodology reference rather than a mandatory runtime dependency. This keeps the contest workflow practical inside Codex while preserving the useful four-stage modeling loop.
