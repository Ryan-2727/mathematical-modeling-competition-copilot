# Paper depth and page-budget standard

Use this module for Chinese mathematical-modeling papers when the task has several
linked subproblems or the user asks for an excellent-paper level of detail. It
prevents two failures: compressing the reasoning into a short answer report, and
padding a weak main text with code pages. Current official rules and the supplied
template are always the hard constraints.

## Contents

- [Evidence behind the profile](#evidence-behind-the-profile)
- [Rule hierarchy and page profiles](#rule-hierarchy-and-page-profiles)
- [Recommended structure](#recommended-structure-and-priority)
- [Seven-part argument chain](#seven-part-argument-chain-for-every-subproblem)
- [What to write fully and compress](#what-to-write-fully-and-what-to-compress)
- [Figure, table, and paragraph discipline](#figure-table-and-paragraph-discipline)
- [Final depth review](#final-depth-review)

## Evidence behind the profile

Three visually inspected 2024 CUMCM A-problem exemplars contain 48, 55, and 59 PDF
pages. Their main narratives end at approximately pages 20, 30, and 31; the
remaining roughly 25--28 pages are mostly code appendices. The stable lesson is
not "copy 48--59 pages." It is:

- strong submissions can devote substantial space to a five-question reasoning
  chain;
- total PDF pages and explanatory main-text pages are different measurements;
- appendix code supports reproducibility but cannot substitute for derivation,
  result interpretation, or validation in the main text.

The PDFs are scanned and their text layers are unreliable, so these observations
come from page rendering and visual boundary inspection. Preserve that limitation
when citing this profile in a learning report.

## Rule hierarchy and page profiles

Apply rules in this order:

1. verified current official limit and required template;
2. amount of reasoning and evidence needed to answer every numbered task;
3. the profiles below as anti-underwriting guidance;
4. exemplar length only as a diagnostic comparison, never as a quota.

For a CUMCM-style paper governed by the 2026 profile, enforce the official
30-page main-text ceiling and the abstract-page, no-contents, and unlimited
appendix rules in `cumcm-2026-rules.md`. Use the following as planning
diagnostics, never minimum-length requirements:

| Situation | Main-text plan | Complete PDF plan | Gate |
| --- | ---: | ---: | --- |
| 2026 CUMCM profile | normally 20--25; lower when the task needs less, near 30 only when evidence needs it | main text plus required appendices | never exceed 30; do not pad |
| No verified page cap | derive a section budget from task complexity and evidence | task-specific | no padding or empirical floor |
| Verified maximum is below the initial plan | compress standard detail and move reproducibility material to appendices/support | obey the official rule | preserve decisive reasoning and validation |
| Smaller or lightly coupled task | derive a task-specific budget | task-specific | do not force the complex profile |

Page ranges are drafting alarms only. A paper may be shorter and stronger when
every subproblem has a complete argument chain and all decisive evidence is
locatable. If additional pages come from repetition, oversized screenshots, raw
code, or unexplained plots, shorten the paper.

Before drafting, create `reports/paper_depth_plan.csv`. After compilation, record
visually confirmed main-text and appendix page counts and run
`scripts/verify_paper_depth.py`.

## Recommended structure and priority

The page ranges below are planning ranges under a 30-page main-text cap. Rebalance
them according to difficulty; do not make every question equal.

| Part | Typical pages | Required depth |
| --- | ---: | --- |
| Abstract and keywords | <=1 | research object; per-question method, quantitative answer, and validation/meaning; no generic background or method-only abstract |
| Problem restatement | about 1 | concise task boundary and outputs; do not copy the statement |
| Problem analysis | 1--2 | per-question mechanism, dependency, method rationale, data route, and validation plan; use a route diagram when it reduces cognitive load |
| Assumptions and notation | 1--2 | only used assumptions and major symbols, with reason and effect of restrictive assumptions |
| Data processing | 2--3 when data-driven | source, cleaning, screening, key statistics/visuals, and decisions; move raw or large tables out of the main text |
| Problem models and solutions | 10--15 total | task, rationale, variables, derivation, algorithm/parameters, results, interpretation, and local validation for each question |
| Global validation and sensitivity | 2--3 | choose model-appropriate residual, baseline, perturbation, robustness, convergence, or failure-boundary checks |
| Evaluation, conclusions, and extension | 1--2 | direct answers, evidence-backed strengths/limits, and conditional transfer; avoid empty claims of broad applicability |
| References | 1--2 as needed | verified, relevant, and cited works only |
| Code/data appendix | unlimited | complete code, large tables, detailed intermediate outputs, supplementary derivations, and secondary experiments; never a substitute for main-text explanation |

## Seven-part argument chain for every subproblem

Each numbered problem must make all seven items easy to locate. A subsection may
combine adjacent items, but none may disappear.

1. **Task and mechanism.** State what must be determined and the physical,
   geometric, statistical, economic, or decision mechanism that controls it.
2. **Method rationale.** Introduce the chosen method in plain language, explain
   why it fits this mechanism, and mention the baseline or rejected alternative
   when an executed comparison makes that choice material. State the diagnostic
   that promoted model A over model B; do not praise complexity in the abstract.
3. **Variables and assumptions.** Define local symbols, units, domains, coordinate
   systems, and the assumptions that enable this model. For every
   claim-sensitive threshold or parameter, identify whether it came from a
   verified source passage, official rule, reproducible calibration, or explicit
   assumption, and state the tested range.
4. **Derivation.** Move from the mechanism to equations, objective, and constraints
   step by step. Explain the meaning of transformations and boundary conditions;
   do not show only the final formula.
5. **Algorithm and implementation.** Give the computational sequence, search
   domain, initialization, stopping tolerance, solver/precision, and reproducible
   result source. Use numbered steps or pseudocode for a multi-stage method.
6. **Results and interpretation.** Tables carry exact values and units; figures
   carry patterns or geometry. State what the evidence means for the original
   question and why the value/trend is reasonable.
7. **Local validation.** Add a direct check near the result: residual, limiting
   case, independent calculation, constraint audit, precision comparison, or
   sensitivity. State genuine failed attempts and abnormal boundary behavior
   only where saved evidence changes interpretation. Keep a later global
   validation section as well.

## What to write fully and what to compress

Write fully:

- the model-selection reason and problem mechanism;
- non-obvious geometry, recurrences, objectives, constraints, and boundary cases;
- parameter source/calibration and units;
- search interval, tolerance, convergence/precision, and feasibility checks;
- decisive numerical results, interpretation, uncertainty, and failure limits;
- transitions showing how one subproblem feeds the next.

Write briefly or move to an appendix/support package:

- background already given in the statement;
- standard formulas whose conditions are stated and properly cited;
- repeated algebra after the general recurrence is established;
- installation logs, raw arrays, long intermediate tables, and full source code;
- decorative process narration such as "we used Python to calculate" without an
  algorithmic decision;
- duplicate results appearing in abstract, body, and conclusion with no new role.

When the main text approaches its ceiling, move or remove in this order: complete
code, raw or oversized tables, secondary experiments, duplicate figures,
overlong algorithm exposition, weak background, repeated interpretation, and
textbook history. Preserve decisive formulas, parameter choices, core results,
validation/sensitivity evidence, and direct conclusions. Never make room by
shrinking the layout or by removing the argument that makes a conclusion auditable.

## Figure, table, and paragraph discipline

Use a geometry/mechanism diagram before a derivation when it reduces cognitive
load. Use a workflow only for a genuinely multi-stage algorithm. Introduce every
figure/table with the question it answers, and follow it with a paragraph stating
the finding, numerical evidence, reason, and implication. Never place several
figures consecutively without analysis. Do not count a page of raw plots as a page
of explanation.

## Final depth review

Fail the drafting gate when any numbered task lacks one of the seven argument
items, when a central conclusion has no result source, when validation exists only
as a generic final paragraph, when the abstract exceeds one page, when a CUMCM
paper contains a contents page, when main text exceeds the official ceiling, or
when code appendices are being used to satisfy a page target. Run
`verify_paper_depth.py` in its default advisory-minimum mode;
use `--minimum-mode enforce` only when a verified official rule truly imposes a
minimum. Passing confirms counts and recorded coverage; it does not certify
mathematical correctness or prose quality.
