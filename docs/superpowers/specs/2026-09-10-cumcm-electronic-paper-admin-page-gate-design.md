# CUMCM electronic-paper administrative-page gate design

## Scope

Add one CUMCM 2026 submission rule only: the electronic paper must not contain
the commitment form or number-only page. Preserve every other submission,
paper, support-package, and anonymity rule unchanged.

## Detection

Add a dedicated `cumcm.no_administrative_pages` check to
`scripts/verify_submission.py`.

For a PDF, inspect every page of existing `pdftotext` output. For DOCX, inspect
the extracted document text. Report a violation when either condition holds:

1. a standalone administrative heading identifies a commitment form,
   commitment page, number-only page, or number-designation page; or
2. one page contains a strong field combination characteristic of an
   administrative page, such as both a team-number field and a paper-number
   field.

Do not fail on isolated generic uses of words such as “编号”, “承诺”, or
“论文”. The JSON check evidence must list each matched page when page boundaries
are available and the matched signature, without reproducing personal values.

## Uninspectable files

If readable PDF/DOCX text is unavailable, accept only hash-bound compliance
evidence for the current paper with:

```json
{
  "administrative_pages_absent": true,
  "reviewer": "named team reviewer",
  "recorded_at": "timestamp",
  "paper_sha256": "current paper hash"
}
```

Such evidence produces the same scoped `LIMITED` status used by existing visual
fallbacks, not a machine-inspection claim. Missing or false evidence fails the
gate. Legacy `.doc` remains permitted by the official suffix profile but must
use this reviewed evidence path because built-in text extraction is unavailable.

## Documentation and routing

Update the CUMCM 2026 rule reference and final-verification checklist. Keep the
entry-point `SKILL.md` within its routing budget by extending the existing
electronic-paper verification instruction rather than adding a duplicate rule.
Add the new check identifier to the skill contract so later edits cannot remove
it silently.

## Tests and acceptance

Add focused tests that prove:

- a normal abstract-first electronic paper passes;
- a later commitment-form page fails and reports its page;
- a number-only page identified by the team-number plus paper-number signature
  fails;
- an uninspectable paper requires current hash-bound evidence;
- isolated ordinary uses of “编号” do not cause a false positive.

Then run the targeted submission tests, skill-contract validation, quick skill
validation, and the full unit-test suite. Do not commit implementation unless
all checks pass.
