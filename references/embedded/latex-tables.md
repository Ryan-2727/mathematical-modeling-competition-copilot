# LaTeX And Academic Tables

Use this module for LaTeX tables, regression-style tables, summary statistics, and contest tables.

## LaTeX Table Rules

- Prefer `booktabs` for clean horizontal rules.
- Include `\caption{}` and `\label{}`.
- Align numeric columns.
- Add notes for standard errors, significance marks, data source, or units.
- Keep tables narrow enough for the paper layout.

## General Contest Table Rules

- Use concise titles and captions.
- Include units in headers.
- Use reasonable precision; do not imply false accuracy.
- Align comparable numbers.
- Keep source notes when values come from data or literature.
- Ensure every table value appears in `results/`, code output, spreadsheet formulas, or cited sources.

## Common Pitfalls

- Tables too wide for the page.
- Missing units.
- Mixed precision without reason.
- Values copied manually from stale outputs.
- Captions that describe format but not meaning.

## Verification

Before final delivery:

- Cross-check table values against source results.
- Confirm captions and labels are referenced in text.
- Compile or render LaTeX/PDF when the environment allows.
- If rendering is not possible, state that layout was not visually verified.
