# Runtime, template, and decision-claim audits

These audits turn common contest failure modes into visible evidence. They do
not prove mathematical truth and they never authorize copying a historical
answer, a filled workbook, or a paired paper.

## Runtime and solver lock

Before finalizing a method that requires a particular solver/runtime, probe it:

```powershell
python scripts/probe_runtime_capabilities.py --project-dir . `
  --require mixed_integer --require nonlinear --strict
```

Keep `reports/runtime_capabilities.json` with the observed Python executable,
package versions, requested profiles, and missing capabilities. If a required
capability is absent, choose a method that is genuinely supported, or record a
limited/blocked result. Do not install packages in contest mode and do not call a
different algorithm the same model merely because its original solver is absent.

For a reused event-data aggregate, run `scripts/verify_data_cache.py` against a
manifest that binds raw and cached file hashes, its aggregation rule, and a
training cutoff that precedes the target period.

## Result-template isolation

A file whose name suggests `result`, `answer`, `submission`, or `output` is not
input evidence by default. If the official organizer supplies an output template,
explicitly declare the local copy as a template and inspect it without copying:

```powershell
python scripts/verify_result_template.py --project-dir . `
  --template data/raw/official_template.xlsx
```

The audit records only structural metadata and a hash. Prefilled cells force a
human review plus `--allow-prefilled`; they never become a numerical source.
Populate a separate generated submission file only from verified result artifacts.

## Predictive versus causal claims

For interventions, policy, pricing, or treatment effects, write the target
quantity before fitting: prediction of an outcome, or a causal estimand. A causal
claim needs a credible identification strategy, assumptions, treatment timing,
confounding/endogeneity diagnostics, and sensitivity analysis. If these are not
available, use predictive time-respecting validation and call the conclusion an
association or forecast—not an effect.

## Private regression evidence rubric

After a private historical solve is complete, score evidence rather than reading
paired answers. The five required dimensions are input audit, feasibility,
reproducibility, writing, and visual communication. Each evidence file is a
private JSON status report (`PASS`, `LIMITED`, or `FAIL`):

```powershell
python scripts/score_private_regression.py --private-root <private-root> `
  --case-id <case-id> `
  --evidence input_audit=reports/input_audit.json `
  --evidence feasibility=reports/feasibility_audit.json `
  --evidence reproducibility=reports/reproduction.json `
  --evidence writing=reports/writing_audit.json `
  --evidence visual_communication=reports/visual_audit.json
```

The generated rubric contains statuses, hashes, and (when supplied) private
evidence locators/category counts. Do not store the private report, statement,
data, paper, numerical answer, or score baseline in this repository. Use the
rubric to locate a generalizable workflow gap, then confirm the change on a
blinded regression run.

Optionally add a private `defects.csv` with `dimension`, `category`, `severity`,
`artifact_locator`, and `status`, then pass it through `--defect-log`. Categories
include unverifiable assumptions, unsupported figures, decorative sensitivity,
missing fallback, causal overclaim, weak implementation, broken evidence chain,
and layout readability. The private rubric retains evidence locators and category
counts so recurrent weaknesses can be fixed without publishing any case content.
