# Decision and delivery gates

Use these gates after core modeling produces verified values and before submission
freeze.  They improve evidence quality and reviewer navigation; none proves that a
model is mathematically correct or guarantees an award.

## 1. Stability before strong recommendations

For every material decision, create one row per meaningful perturbation in
`reports/decision_stability.csv`: the baseline recommendation, the perturbation,
the perturbed recommendation, whether it changed, the result artifact, and the
paper location.  If a material recommendation changes, write a conditional or
scenario-dependent conclusion and point to its limitation.  Do not state a single
unqualified recommendation merely because the baseline was convenient.

Run:

```bash
python scripts/verify_decision_stability.py --project-dir <project>
```

## 2. Numeric contracts for core figures

For each decision-bearing figure, register the source data path and its SHA-256,
axis names/scales/ranges, transformations, verified-value keys displayed, and
paper location in `reports/figure_numeric_contract.csv`.  The figure label and
source must agree with `figure_manifest.csv`; every decisive key must appear in
`results/verified_values.csv`.  A polished visual without a retraceable numeric
source is not evidence.

Run:

```bash
python scripts/verify_figure_numeric_contract.py --project-dir <project>
```

## 3. Budget the remaining contest time

Use `reports/model_budget.csv` to keep one executable baseline for every
subproblem, choose exactly one route, record time and validation costs, a risk
level, expected value for non-baseline work, and a distinct fallback.  Give all
rows one shared remaining-hours deadline.  Selected estimates may not exceed it.
When the budget is tight, preserve a result-bearing baseline and clean validation
before trying a more complex route. For each candidate, predeclare the comparison
metric, direction, positive absolute minimum advantage, baseline value, candidate
value, and validation artifact. A candidate below threshold cannot be selected;
mark it `rejected` or `model_optimization` and keep the simpler route primary.

Run:

```bash
python scripts/verify_model_budget.py --project-dir <project>
```

## 4. Review the first three minutes

Complete exactly five rows in `reports/three_minute_review.csv`: `abstract`,
`route_figure`, `core_result`, `recommendation`, and `limitation`.  Each row must
state the reader question, direct answer, evidence type/reference, and paper
location.  References are checked against a real paper file, figure label,
verified-value key, or conclusion-map subproblem.  This makes first-page review a
deliberate design step instead of a late formatting pass.

Run:

```bash
python scripts/verify_three_minute_review.py --project-dir <project>
```

## 5. Lock the portable LaTeX environment

Before delivery, run the normal compatibility build and then freeze package,
font, compiler, `latexmk`, and VS Code configuration evidence.  A missing local
compiler yields `LIMITED`, not a fictional cross-environment pass; resolve it with
the actual Overleaf/VS Code build before claiming a compiled delivery.

```bash
python scripts/verify_latex_compatibility.py --paper-dir <project>/paper --out <project>/reports/latex_compatibility.json
python scripts/verify_latex_dependency_lock.py --project-dir <project>
```

## 6. Freeze only fresh evidence

Run the five validators after changing results, figures, TeX source, or build
configuration.  `contestctl.py check --phase freeze` checks report statuses and
input hashes, so stale reports cannot silently accompany a changed paper.  The
repository tests also contain invalid fixtures for every gate; preserve that
negative coverage when changing a validator.
