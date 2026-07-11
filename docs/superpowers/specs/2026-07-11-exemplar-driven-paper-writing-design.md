# Exemplar-driven paper-writing design

## Goal

Make the paper branch learn from paired, public 2025 national-competition papers
without copying their answers or treating subjective style as a hard quota.

## Components

- `exemplar-driven-paper-writing.md`: input manifest, freeze/compare/revise loop,
  2025 format profile, and scorecard.
- `latex-paper-pipeline.md`: explicit XeLaTeX source layout, visual roles, and QA.
- `scripts/exemplar_metrics.py`: deterministic page-image and LaTeX source metrics.
- `reports/exemplar_comparison_*.md`: task-local evidence produced by future runs.

## Data flow

```text
paired problem/exemplar -> manifest -> frozen baseline -> metrics + human evidence
-> gap scorecard -> generalizable skill change -> rerun -> regression comparison
```

## Safety and scope

The exemplar is used for structure, explanation density, validation patterns, and
layout. It is never treated as a hidden solution or as permission to reproduce
copyrighted text or figures. Public source, access date, and local provenance are
recorded. Missing attachments or unavailable OCR/PDF tools are reported as gaps.

## Verification

The metrics script has no external dependency beyond optional Pillow, and must be
run on a downloaded public exemplar image directory and a synthetic LaTeX fixture.
The repository skill validator and Markdown/source scans are required before commit.
