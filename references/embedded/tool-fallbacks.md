# Tool Fallbacks

This repository embeds workflow knowledge, not all runtime tools. Some capabilities require Codex plugins or local software.

## Capabilities That Require Plugins Or Runtime Tools

### Jupyter Notebooks

Install or enable the Data Analytics plugin if you need:

- notebook creation or editing
- top-to-bottom notebook execution
- notebook-as-deliverable workflows

Fallback: use Python scripts plus Markdown reports, and record that notebook execution was not verified.

### DOCX Documents

Install or enable the Documents plugin if you need:

- DOCX creation or editing
- tracked changes or comments
- visual DOCX render QA

Fallback: draft paper content in Markdown or LaTeX, and record that DOCX rendering was not verified.

### PDF

Install or enable the PDF plugin if you need:

- PDF page rendering
- PDF extraction
- visual page inspection

Fallback: create source files and ask for local PDF review, or use available local tools if present.

### Spreadsheets

Install or enable the Spreadsheets plugin if you need:

- `.xlsx` creation
- formula-backed workbooks
- charts or dashboards
- workbook rendering

Fallback: use CSV/Markdown tables and record that spreadsheet formulas or workbook layout were not verified.

## Reporting Missing Tools

When a capability is unavailable, write:

- missing tool or plugin
- affected artifact
- what fallback was used
- what remains unverified

Do not present fallback output as equivalent to rendered DOCX/PDF/XLSX or executed notebooks.
