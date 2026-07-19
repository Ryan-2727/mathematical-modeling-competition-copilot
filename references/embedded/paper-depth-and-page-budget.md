# Paper depth and page-budget standard

Use this module for Chinese mathematical-modeling papers when the task has several
linked subproblems or the user asks for an excellent-paper level of detail. It
prevents two failures: compressing the reasoning into a short answer report, and
padding a weak main text with code pages. Current official rules and the supplied
template are always the hard constraints.

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

For a complex CUMCM-style problem with four or more linked subproblems:

| Situation | Main-text plan | Complete PDF plan | Gate |
| --- | ---: | ---: | --- |
| Verified maximum is 30 main-text pages | prefer 28--30; 24 is the normal depth floor | main text plus required appendices | never exceed 30 |
| No verified page cap | normally 24--32; use 28--35 only when the reasoning truly requires it | normally 35--60 and at least 30 | no padding |
| Verified maximum is below 24 | plan near the limit and move reproducibility detail to appendices/support | obey the official rule | record why the normal floor was reduced |
| Smaller or lightly coupled task | derive a task-specific budget | task-specific | do not force the complex profile |

"Floor" is a drafting alarm, not permission to violate a rule. If the main text is
below the selected floor, either restore missing reasoning or record a concrete
scope/rules justification. If it reaches the target by repetition, oversized
screenshots, raw code, or unexplained plots, shorten it.

Before drafting, create `reports/paper_depth_plan.csv`. After compilation, record
visually confirmed main-text and appendix page counts and run
`scripts/verify_paper_depth.py`.

## Recommended structure for a five-question paper

The page ranges below are planning ranges under a 30-page main-text cap. Rebalance
them according to difficulty; do not make every question equal.

| Part | Typical pages | Required depth |
| --- | ---: | --- |
| Abstract and keywords | 1 | one answer sentence per task: method, decisive result, and validation/meaning |
| Problem restatement | 0.5--1 | concise background; enumerate inputs, conditions, outputs, units, and task boundary |
| Problem analysis | 2--3 | a separate subsection per question; mechanism, method rationale, dependency on earlier questions, solution path, and validation plan |
| Assumptions and notation | 1--2 | only assumptions and symbols used later; explain the effect of restrictive assumptions |
| Each simpler subproblem | 2--3 | complete argument chain, not only equations and answers |
| Each central/complex subproblem | 4--6 | geometry/mechanism, derivation, algorithm details, evidence, interpretation, and local checks |
| Global validation and sensitivity | 2--4 | independent checks, errors, perturbations, robustness, uncertainty, or failure boundary |
| Conclusions and model evaluation | 1--2 | direct answers, evidence-based strengths/weaknesses, realistic extensions |
| References | 0.5--1 | only verified and cited works; follow the skill's bibliography contract |
| Code/data appendix | as required | reproduction aid; excluded from the main-text depth claim |

## Seven-part argument chain for every subproblem

Each numbered problem must make all seven items easy to locate. A subsection may
combine adjacent items, but none may disappear.

1. **Task and mechanism.** State what must be determined and the physical,
   geometric, statistical, economic, or decision mechanism that controls it.
2. **Method rationale.** Introduce the chosen method in plain language, explain
   why it fits this mechanism, and mention the baseline or rejected alternative
   when that choice is not obvious.
3. **Variables and assumptions.** Define local symbols, units, domains, coordinate
   systems, and the assumptions that enable this model.
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
   sensitivity. Keep a later global validation section as well.

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
as a generic final paragraph, or when code appendices are being used to satisfy a
page target. Passing `verify_paper_depth.py` confirms counts and recorded coverage;
it does not certify mathematical correctness or prose quality.
