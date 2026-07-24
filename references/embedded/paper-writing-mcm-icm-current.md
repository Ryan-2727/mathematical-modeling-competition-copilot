# MCM/ICM paper and submission branch

Use this branch only after recording the current official rules snapshot. The
following is a verification checklist, not a substitute for the current year’s
official instructions.

As of the repository verification date 2026-07-24, COMAP's official current
instructions describe the 2027 contest. Use the `mcm-icm-current` executable
profile and the `mcm-icm` LaTeX template, but refresh the official page before a
live contest because the alias is intentionally time-sensitive.

## Paper structure

Start with the official Summary Sheet, then present a concise English solution.
Use a table of contents when it improves navigation. Make assumptions, variables,
model rationale, validation, conclusions, strengths/weaknesses, and references
easy to locate. Keep lengthy derivations, data, and code concise because all pages
that the current rules count must fit the stated limit.

## Current-rule checks

Verify rather than assume:

- page limit and what counts toward it;
- English language and minimum readable font size;
- required summary-sheet template and control-number placement;
- PDF-only submission and deadline time zone;
- no identity information beyond the permitted control number;
- AI disclosure, citations, and required AI-use report;
- whether code/support files are allowed or must remain inside the paper;
- source attribution and permissions for every non-team figure, image, table, and
  quotation.

## MCM/ICM final gate

The first PDF page is the summary. The summary reports approach and important
conclusions, not a restatement of the prompt. The final PDF is English, meets the
verified total-page limit, is anonymous, and is frozen at contest close. Run
`verify_submission.py --profile mcm-icm-current` with the PDF's seven-digit
control number, declared font size, counted solution pages, AI flag, and
hash-bound visual evidence when required. Do not attach a separate support
archive. Use the submission receipt to transition from `submitted` to
`receipt_verified`.
