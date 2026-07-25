# Operational quality gates

Use this module to coordinate existing specialist verifiers. These gates check
recorded evidence and artifacts; they do not prove mathematical truth or predict
an award.

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
