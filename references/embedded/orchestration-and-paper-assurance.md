# Orchestration and paper assurance

Use this playbook after project initialization and before the paper or submission
freeze.  It coordinates specialist checks; it does not replace model reasoning,
source reading, numerical reruns, or page-by-page human review.

## Project schema

Current projects declare `project_schema_version`, `quality_profile`, and a
`workflow` object in `contest_manifest.json`.  Do not manually overwrite an old
manifest.  Preview the additive migration first:

```bash
python scripts/contestctl.py migrate --project-dir <project>
```

Inspect `reports/project_migration.json`, then apply it:

```bash
python scripts/contestctl.py migrate --project-dir <project> --apply
```

Migration adds only missing workflow fields, preserves unknown fields, and never
deletes evidence.  A future unsupported schema blocks execution rather than being
downgraded.

## Profiles

| Profile | Intended use | Missing optional tools |
| --- | --- | --- |
| `minimal` | fast iteration and standard-library structural checks | ignored when the selected node does not require them |
| `standard` | normal modeling and paper workflow | reported as `LIMITED` |
| `strict` | final submission freeze | required capability is a failure |
| `custom` | explicit node allow-list | governed by the selected nodes |

Use `assets/contestctl/profiles/custom.example.json` as a schema example.  A
custom profile may select registered nodes but may not provide arbitrary shell
commands.

## Unified commands

Inspect runtime and schema readiness:

```bash
python scripts/contestctl.py doctor \
  --project-dir <project> \
  --profile standard
```

Run the paper dependency graph:

```bash
python scripts/contestctl.py run \
  --project-dir <project> \
  --phase paper \
  --profile standard
```

Run the complete graph needed by the selected freeze profile:

```bash
python scripts/contestctl.py run \
  --project-dir <project> \
  --phase freeze \
  --profile strict
```

Show a concise summary:

```bash
python scripts/contestctl.py summary \
  --project-dir <project> \
  --format human
```

`--dry-run` resolves the graph without executing nodes.  `--force` bypasses the
content-addressed cache.  A cached node is reused only when its declared inputs,
dependency outputs, command registry version, profile, and output hashes are
unchanged and its previous result was `PASS`.

Status meanings:

- `PASS`: the declared contract was checked and satisfied.
- `FAIL`: the contract was checked and violated.
- `LIMITED`: an optional semantic, rendering, or compilation check could not be
  completed.
- `SKIPPED`: a prerequisite failed, a dry run was requested, or an unchanged
  passing result was reused.  Read the recorded reason.

## Rendered-figure contract

Complete `reports/rendered_figure_manifest.csv` after final figures are generated.
Every paper figure records:

- output and source-data SHA-256 digests;
- a stable generator command identifier;
- intended insertion width and height;
- measured minimum effective text size and line width;
- clipping, overlap, axis-crowding, panel-order, panel-spacing, and visual
  hierarchy reviews;
- grayscale and color-vision reviews;
- the supported conclusion, evidence location, and paper page.

Run:

```bash
python scripts/verify_rendered_figures.py \
  --project-dir <project> \
  --profile standard
```

The standard-library path verifies bindings and declared print-size evidence.
When Pillow and Poppler are available, the script renders supported figures,
creates grayscale and deuteranopia review images under
`reports/figure_previews/`, and creates `reports/paper_page_overview.png` from
the compiled paper.  These are review aids, not automatic aesthetic scores.

Minimum declared thresholds are 7 pt effective text, 0.5 pt line width, and 150
DPI for raster output at insertion size.  Vector PDF/SVG output is recorded as
vector.  A human must still confirm clipping, overlap, hierarchy, and the
intended conclusion.

## Notation and dimensions

Use `reports/notation_registry.csv` as the canonical mapping among:

- paper symbol and canonical TeX;
- meaning, kind, and unit;
- first-definition location;
- code names and figure labels;
- appendix and equation locations.

Use `reports/equation_dimensions.csv` for each material equation.  Record the
left and right dimensions, every referenced registry symbol, and the derivation
or computation evidence.  Then run:

```bash
python scripts/verify_notation_registry.py --project-dir <project>
```

The check rejects conflicting meanings, missing first definitions, code/figure
name collisions, invalid vector or matrix styling, unknown equation symbols, and
dimension mismatches.  Ambiguous TeX macros remain a human-review item.

## Generated paper artifacts

Run:

```bash
python scripts/generate_paper_artifacts.py --project-dir <project>
```

The generator writes only:

- `paper/generated/core_results.tex`;
- `paper/generated/model_comparison.tex`;
- `paper/generated/robustness.tex`;
- `paper/generated/conclusion_snippets.tex`;
- `paper/generated/figure_notes.tex`.

It also writes `reports/paper_artifacts_manifest.json`, binding each generated
file to its source ledgers.  Missing result evidence, stale source digests,
unknown decisive-value keys, or conclusions without a limitation block a pass.
The generator never overwrites a manually written section.  Include only the
generated fragments needed by the paper, and rerun both Overleaf-style and VS
Code-style compilation after regeneration.

## Freeze order

1. Run `doctor` with the intended profile.
2. Preview and, if reviewed, apply any migration.
3. Freeze verified values, model comparisons, stress tests, conclusions,
   notation, and figure manifests.
4. Run the `paper` phase and resolve all failures.
5. Compile `paper/main.pdf`; inspect the page overview and every full-resolution
   page.
6. Run the `freeze` phase under `strict`.
7. Run the legacy cumulative `contestctl check` and the submission-profile
   verifier; the strict workflow does not weaken either existing gate.
8. Rebuild delivery archives and record final hashes.

Never change a generated report to bypass a gate.  Correct the source ledger,
code, figure, result, or paper section and rerun the affected graph.
