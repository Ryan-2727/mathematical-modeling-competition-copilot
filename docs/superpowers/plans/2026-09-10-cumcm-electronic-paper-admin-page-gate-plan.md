# CUMCM electronic-paper administrative-page gate plan

1. Add failing unit tests for commitment headings, number-page field
   combinations, ordinary-word false positives, and hash-bound fallback
   evidence.
2. Add a page-signature detector and the `cumcm.no_administrative_pages` check
   to `scripts/verify_submission.py`, reusing existing PDF/DOCX extraction and
   compliance-evidence handling.
3. Update the CUMCM 2026 rule reference, final-verification checklist, concise
   `SKILL.md` routing text, and skill contract without changing other rules.
4. Run targeted tests, contract validation, quick skill validation, and the
   complete unit-test suite. Review the diff, commit only scoped files, then
   synchronize the verified tracked payload to the installed local Skill and
   verify file hashes.
