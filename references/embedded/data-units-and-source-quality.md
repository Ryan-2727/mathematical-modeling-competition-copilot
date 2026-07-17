# Data, units, and source-quality audit

Maintain `reports/units.csv` and the existing data audit. A clean computation
with the wrong unit, time basis, population, or source definition is still a
wrong result.

## Source hierarchy

Prefer problem-provided data, official statistics, primary datasets, and
original research. Record retrieval time, license or permission, version,
geographic and temporal scope, variable definition, and transformations. Use a
second source to cross-check any external value that materially drives a result.

## Unit and scope gate

- Give every measured variable one canonical unit and conversion rule.
- Check rates against their time base and currency values against price year.
- Distinguish stock from flow, count from proportion, nominal from real, and
  individual from aggregate data.
- Record plausible ranges and flag impossible values before model fitting.
- Do not silently combine datasets with different populations, calendars,
  coordinate systems, or missing-value meanings.
- If the model truly has no dimensional quantities, add one explicit reviewed
  `N/A` row with unit `dimensionless` instead of leaving `reports/units.csv`
  empty; this records that the check was performed rather than forgotten.

## Leakage and transformation gate

Fit imputation, scaling, feature selection, and encoding on training data only
when out-of-sample evaluation is claimed. Preserve raw data hashes and executable
transformation code. A manually edited spreadsheet requires a change log.
