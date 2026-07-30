# Orchestration and paper assurance design

## Objective

Turn the existing collection of deterministic quality gates into a coherent,
backwards-compatible workflow that teams can run during modeling, paper writing,
and submission freeze.  The upgrade must improve rendered-paper quality and
traceability without claiming that software can replace mathematical judgment.

## Chosen approach

Use a layered architecture:

1. a small `contestctl` orchestration core with a declarative command registry and
   dependency graph;
2. versioned project metadata, risk-tiered profiles, and non-destructive migration;
3. specialist validators and generators for rendered figures, notation, and paper
   result artifacts;
4. end-to-end fixtures that exercise a CUMCM-style and an MCM/ICM-style project.

This approach preserves the existing validator scripts and `contestctl check`
interface.  It was selected over a monolithic rewrite, which would make every
validator depend on one large command, and over guidance-only documentation,
which would not produce auditable evidence.

## Command-line interface

The existing `contestctl check` command remains valid.  The following commands
are added:

| Command | Purpose |
|---|---|
| `contestctl doctor` | Inspect Python, optional rendering tools, LaTeX tools, project metadata, and profile readiness. |
| `contestctl run --phase paper\|freeze` | Resolve the selected profile, execute the phase dependency graph, and skip checks whose bound inputs and command version have not changed. |
| `contestctl summary` | Present a stable human-readable and JSON summary of PASS, FAIL, LIMITED, and SKIPPED checks. |
| `contestctl migrate [--apply]` | Preview or apply an additive project-schema migration without deleting or overwriting evidence. |

The registry stores argument vectors rather than shell command strings.  Every
node declares its inputs, outputs, profile membership, and prerequisite nodes.
Cycles, unknown dependencies, missing scripts, and duplicate outputs are rejected
before execution.

## Profiles and status semantics

Four profiles control cost and strictness:

- `minimal`: standard-library-only structural checks for fast iteration;
- `standard`: use available optional rendering and LaTeX tools; unavailable
  capabilities produce `LIMITED` rather than a false pass;
- `strict`: submission-freeze profile; required rendering and compilation
  capabilities must be available and all mandatory evidence must pass;
- `custom`: an explicit allow-list and severity override file validated against
  the command registry.

`PASS` means the declared contract was checked and satisfied.  `FAIL` means the
contract was checked and violated.  `LIMITED` means a required semantic or visual
inspection could not be completed with the available tools.  `SKIPPED` is allowed
only when a dependency failed or a content-addressed cache proves that the node's
inputs, command version, and profile settings are unchanged.

## Project schema and migration

`contest_manifest.json` gains a top-level `project_schema_version`.  The current
schema defines profile selection, workflow phase, generated-artifact locations,
and optional-tool policy.  Migration is additive and idempotent:

- dry run is the default and prints a machine-readable change set;
- `--apply` writes only missing fields and preserves unknown fields;
- existing evidence ledgers and generated outputs are never deleted;
- unsupported future schema versions fail with an actionable message;
- the migration report records old/new versions and changed JSON pointers.

New projects receive the current schema from `init_contest.py`.  Legacy projects
without a version are treated as version 0 and remain usable by `check`.

## Rendered-figure assurance

A rendered-figure manifest binds each paper figure to:

- output path and SHA-256 digest;
- source-data digest and a stable generator command identifier;
- intended insertion width and height;
- measured raster/vector resolution and minimum effective text/line size;
- clipping, label crowding, overlap, grayscale, and color-vision checks;
- panel order, spacing, aspect ratio, and paper-page location;
- the supported conclusion and evidence location.

The validator performs deterministic file, digest, geometry, and metadata checks
with the Python standard library.  When Pillow, Poppler, or Matplotlib is
available, it additionally renders figures at insertion size and creates
grayscale and color-vision simulations.  `standard` reports missing optional
inspection as `LIMITED`; `strict` fails when a declared mandatory visual check
cannot be completed.  Heuristic image analysis is reported as review evidence,
not as proof that a figure is aesthetically correct.

A page-overview generator produces thumbnails/contact sheets from a compiled PDF
when a supported renderer is available.  It never mutates the paper PDF.

## Mathematical notation assurance

`notation_registry.csv` is the canonical mapping among paper symbols, meanings,
types, dimensions/units, code names, figure labels, and appendix locations.  The
validator checks:

- duplicate symbols with incompatible meanings;
- missing first definitions and undefined registry references;
- inconsistent scalar, vector, matrix, set, and random-variable styles;
- incompatible units in declared equations or result rows;
- missing mappings between core paper symbols and code/figure labels.

TeX scanning is deliberately conservative: macros and generated files are
resolved only from declared reachable sources.  Ambiguous notation is surfaced
for human review instead of silently rewritten.

## Generated paper result artifacts

A generator consumes verified-value and evidence ledgers and writes only under
`paper/generated/`:

- `core_results.tex`;
- `model_comparison.tex`;
- `robustness.tex`;
- `conclusion_snippets.tex`;
- `figure_notes.tex`.

Rows without verified values or evidence locations are rejected.  Numeric values,
units, uncertainty, and source identifiers are escaped safely for LaTeX.  The
generator never overwrites manually written sections and emits a manifest that
binds every generated file to its source digests.  Overleaf and VS Code builds use
the same generated files.

## End-to-end regression and CI

Two compact synthetic fixtures cover the workflow without distributing private
contest material:

- a CUMCM-style Chinese paper with XeLaTeX and Chinese fonts;
- an MCM/ICM-style English paper with a standard LaTeX build.

Each fixture initializes a project, migrates it, runs the paper and freeze phases,
generates paper artifacts, verifies notation and figures, compiles when tools are
available, and checks summary/cache behavior.  GitHub Actions runs the
standard-library path on Windows and Linux.  LaTeX-enabled jobs are allowed to
report `LIMITED` only in the standard profile; dedicated strict fixture tests use
controlled test doubles for deterministic missing-tool and tool-present cases.

## Documentation and Skill structure

`SKILL.md` remains the concise routing contract and is reduced below 500 lines by
moving detailed operational material into embedded references.  It keeps the
explicit-invocation-only rule, required final deliverables, and critical
anti-fabrication rules.  `workflow-map.md`, both READMEs, and command examples are
updated together.  The new orchestration reference includes a migration guide and
profile selection table.

## Error handling and safeguards

- No command deletes user files or existing evidence.
- Migration and generation default to preview or dedicated output directories.
- Validators never fabricate data, citations, model superiority, or successful
  rendering.
- Cached results are invalidated by input digest, command version, profile, and
  dependency-report digest.
- A failed prerequisite prevents dependent checks from being presented as passes.
- `strict` is intentionally conservative; users may inspect evidence but cannot
  relabel a failed check as passed without changing the underlying ledger.

## Verification and acceptance criteria

The implementation is complete when:

1. legacy `contestctl check` tests still pass;
2. all four profiles and all new commands have positive and negative tests;
3. migration is idempotent and preserves unknown fields and evidence;
4. cache invalidation reacts to input, profile, command-version, and dependency
   changes;
5. rendered-figure and notation validators reject contradictory manifests;
6. generated TeX compiles in the controlled fixtures when LaTeX is available;
7. CUMCM-style and MCM/ICM-style end-to-end fixtures pass on supported CI paths;
8. `SKILL.md` is below 500 lines and the Skill contract validator passes;
9. the full unit suite, whitespace checks, and repository status checks pass
   immediately before publication.
