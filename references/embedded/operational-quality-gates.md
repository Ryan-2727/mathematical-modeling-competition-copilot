# Operational quality gates

Use this module to coordinate existing specialist verifiers. These gates check
recorded evidence and artifacts; they do not prove mathematical truth or predict
an award.

## Coupled feasibility gate

Before presenting a solution for a system with shared geometry, flows, resources,
or network links:

1. Verify input encoding, units, identifiers, row counts, one-to-one joins,
   zero/blank-value semantics, and attachment-to-subproblem coverage; record the checks in
   `reports/input_audit.json`. Every supplied attachment must map to at least
   one subproblem or be explicitly marked unused with a reason.

   Classify each zero or blank as structural, no-opportunity/not-observed,
   censored/not-detected, or missing. Use the classification in capacity,
   imputation, and compositional-data decisions; record a sensitivity check when
   more than one treatment is credible.
2. Classify constraints as local bounds/equalities or coupled constraints, and
   record the decision-variable and constraint graph in `reports/constraint_map.md`.
3. Use an independent projection only to diagnose scale and initialization. If
   coupled constraints exist, jointly solve or repair the affected variables;
   do not label the independent projection feasible.
4. Write `reports/feasibility_audit.json` before exporting result tables. Include
   bound coverage, maximum equality residual, maximum coupled-constraint
   violation, count of violations, tolerance, and the treatment of infeasible
   rows. A nonzero unresolved violation is a `FAIL`, not a numerical result.

For large sparse systems, prefer a sparse constrained optimizer, decomposition
with an explicit coupling repair step, or a documented relaxation-and-repair
method. Validate the repaired solution against the original constraints.

## Data-scale and time-split gate

Before exploratory analysis or forecasting, record source row counts, field
schema, units, target horizon, training cutoff, and expected reuse in
`reports/data_scale_audit.json`. For large event streams, make one hashed,
immutable aggregate with a documented aggregation rule and use it for repeated
model fitting; preserve the raw source binding for audit. For compact planning
tables, read directly and retain the original entity and constraint granularity.
Never let a future target period enter a fitted feature, scaling statistic, or
model-selection metric.

## Lock official rules

Save each official rule page or PDF inside the project, then bind its URL,
snapshot hash, validity date, and structured rule fields:
The resulting project-root lock file is `rules.lock.json`.

```powershell
python scripts/lock_contest_rules.py create `
  --project-dir . `
  --contest CUMCM `
  --year 2026 `
  --profile cumcm-2026 `
  --valid-through 2026-12-31 `
  --source-url <official-url> `
  --snapshot reports/rules/cumcm-format.pdf `
  --rule paper_format=PDF `
  --rule paper_size_limit_mb=20 `
  --rule support_archive=ZIP-or-RAR `
  --rule main_text_page_limit=30 `
  --rule ai_policy=disclose `
  --rule anonymity=no-identity
```

Run `lock_contest_rules.py validate` again before freeze. Never treat the
initializer's unverified skeleton as a current official snapshot.

## Coordinate phases

Run the controller after the specialist reports for a phase have been generated:

```powershell
python scripts/contestctl.py check --project-dir . --phase setup --out reports/phase_setup.json
python scripts/contestctl.py check --project-dir . --phase modeling --out reports/phase_modeling.json
python scripts/contestctl.py check --project-dir . --phase paper --out reports/phase_paper.json
python scripts/contestctl.py check --project-dir . --phase delivery --out reports/phase_delivery.json
python scripts/contestctl.py check --project-dir . --phase freeze --out reports/phase_freeze.json
```

The controller checks cumulative required files, completed ledgers, and
specialist-report statuses. Fix the specialist report rather than editing a phase
report.

## Paper quality checks

Run:

```powershell
python scripts/verify_abstract_quality.py --project-dir . --expected-subproblems <n> --out reports/abstract_quality.json
python scripts/verify_bibliography_metadata.py --project-dir . --out reports/bibliography_verification.json
python scripts/verify_manuscript_quality.py --project-dir . --out reports/manuscript_quality.json
```

Save authoritative Crossref, OpenAlex, publisher, journal, or conference metadata
under `reports/bibliography_metadata/`. Save a short copyright-compliant excerpt
or a precise evidence note for each claim under `reports/source_passages/`;
record hashes and source locators in `reports/bibliography.csv`. Google Scholar
confirmation remains a separate observed check and is not a substitute for
authoritative metadata.
For strict automated verification, `verification_source` is the record-specific
HTTPS Crossref, DOI, or OpenAlex URL, and `scholar_query` uses the canonical
`https://scholar.google.com/scholar?q=...` host and path.

Maintain `reports/figure_manifest.csv`. Every figure records its LaTeX label,
source data or team-generated-diagram note, caption insight, axis units or
`not_applicable`, color/grayscale check, and verification status.

## Delivery versus official submission

Place user-facing artifacts in `delivery/` and only contest-permitted files in
`official-submission/`. Each directory has a `manifest.csv` with:

```text
path,role,source_path,sha256
```

The delivery manifest normally includes `paper_pdf`, `latex_source`, and
`support_archive`. The official manifest follows the selected contest profile;
MCM/ICM permits only its single solution PDF, while CUMCM may include its separate
support archive under the current locked rules.

Run:

```powershell
python scripts/verify_delivery_profiles.py --project-dir . --out reports/delivery_profiles.json
```

Then run the contest-specific submission verifier. Passing this separation check
does not replace filename, page, size, anonymity, AI, or receipt checks.
