# Paper-learning from an exemplar corpus

## Goal

Make the paper branch learn reusable structure, figure/table grammar, validation
narrative, and LaTeX habits from an offline corpus of excellent papers. A current
contest problem never requires a paired reference paper.

## Components

- `paper-learning-from-exemplars.md`: offline corpus pass, writing rules, and
  independent baseline/revision loop.
- `latex-paper-pipeline.md`: explicit XeLaTeX source layout, visual roles, and QA.
- `scripts/paper_corpus_metrics.py`: deterministic PDF page metrics.
- `reports/paper_learning_iteration_*.md`: task-local evidence produced by future
  runs.

## Data flow

```text
offline corpus -> visual/metric profile -> reusable writing rules -> independent
baseline -> post-hoc comparison -> generalizable skill change -> re-solve
```

## Safety and scope

The corpus is used for structure, explanation density, validation patterns, and
layout. It is never treated as a hidden solution or as permission to reproduce
copyrighted text or figures. Missing OCR/PDF tools are reported as gaps.

## Verification

The corpus metrics script must be run on the local PDF corpus and representative
pages must be rendered and visually inspected.
The repository skill validator and Markdown/source scans are required before commit.
