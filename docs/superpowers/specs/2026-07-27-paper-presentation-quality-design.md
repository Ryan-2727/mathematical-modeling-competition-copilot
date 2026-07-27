# Paper Presentation Quality Design

## Goal

Strengthen the contest-paper workflow where award-facing quality is most visible:
typography, visual communication, answer density, and independent review. The
new gates diagnose reproducible defects; they do not claim to score beauty or
predict an award.

## Scope

Add four connected capabilities without changing the explicit-invocation rule,
existing contest templates, or previous artifact schemas:

1. a rendered-PDF presentation audit with objective layout signals and a
   hash-bound human review ledger;
2. a figure-and-table design contract that enforces one consistent visual
   system and records readable, accessible evidence;
3. an abstract-and-conclusion density audit that requires direct,
   quantitative, limitation-aware answers for every subproblem; and
4. independent mathematical and editorial review roles with evidence locators.

The existing `model`, `evidence`, and `writing` review roles remain compatible;
the `writing` role becomes the editorial role and gets explicit presentation
criteria. No private historical paper, problem statement, solution, image, or
verbatim wording is added to the public repository.

## Design

### Presentation audit

Create `scripts/verify_paper_presentation.py`. It reads the compiled PDF when
available and reports only measurable signals: page count, page dimensions,
text coverage, sparse pages, optional embedded-font information, and the
presence of a completed `reports/presentation_checklist.csv`. The checklist
contains page- or artifact-located checks for hierarchy, font readability,
orphaned headings/captions, formula breaks, table continuity, whitespace
balance, and visual consistency. A missing PDF is `FAIL`; unavailable optional
extractors produce `LIMITED`, never a synthetic visual pass.

### Figure and table design system

Extend `reports/figure_manifest.csv` with design fields: visual role, style
profile, palette or grayscale strategy, typography/precision status, panel
order, and legibility evidence. Add `reports/table_manifest.csv` for equivalent
table roles, units, precision, emphasis, and continuation checks. Create
`scripts/verify_visual_design_system.py` to require complete metadata and a
single declared style profile per artifact family. It checks contract
consistency, not whether a chart is aesthetically good. Human confirmation
stays in the presentation checklist.

### Answer-density audit

Create `scripts/verify_answer_density.py` for the abstract and conclusion.
It verifies that each subproblem has a direct answer, a result value or
recommendation, a method/result locator, and a limitation or validity boundary
in `reports/conclusion_map.csv`. It also checks that the abstract includes
method, quantitative outcome, validation, and recommendation evidence without
requiring a fixed language or copied phrasing. The report is hash-bound to the
two source sections and conclusion map.

### Two-lens review

Keep the existing three independent roles but formalize their packets:

- `model`: assumptions, mechanism, identification, numerical logic, and
  validation;
- `evidence`: traceability, baselines, uncertainty, implementation claims;
- `writing`: now explicitly editorial, covering abstract/conclusion prominence,
  narrative pacing, figure/table use, formula readability, and page design.

Every objection must name a PDF page, figure/table label, equation, or source
section. The aggregator continues to reject award predictions and reports only
diagnostic findings.

## Integration

`init_contest.py` creates the new checklists and table manifest. `contestctl.py`
requires the three new reports at freeze and verifies their source hashes.
`SKILL.md`, embedded guidance, and bilingual READMEs describe the sequence:
compile, run deterministic audits, review rendered pages, obtain independent
reviews, resolve material findings, then freeze.

## Compatibility and Boundaries

- Preserve existing CLI arguments and old manifest columns; only append columns.
- Use Python standard library, with optional `pypdf`/Poppler inspection marked
  as limited when unavailable.
- Keep human judgment visible rather than converting it into an unsupported
  numerical beauty score.
- Do not introduce award forecasts, corpus copying, or automatic publication.

## Verification

Add pass/fail unit tests for every new verifier, schema test coverage for new
initialization files and phase-report bindings, and tests for legacy reviewer
packets. Run the full suite, skill contract validation, UTF-8 compilation check,
and a clean diff review. Then synchronize the validated repository to both
installed local Skill locations and compare tracked-file hashes.
