# Operational Quality Gates Design

## Scope

Implement the previously approved improvements numbered 2 through 10. Exclude
the private historical-problem regression suite until the user supplies and
authorizes that corpus.

## Design

### Contest phase controller

Add one dependency-free CLI that reads the existing project artifacts and
reports `PASS`, `LIMITED`, or `FAIL` for setup, modeling, paper, delivery, and
freeze phases. It must never invent evidence or mutate submission state during a
check. Existing specialist verifiers remain authoritative; the controller
coordinates their reports and required files rather than duplicating them.

### Model validation

Keep the existing manifest contract and add adapters for mechanistic dynamics,
causal/econometric models, unsupervised models, queueing/reliability models,
spatial/spatiotemporal models, and multi-objective/dynamic optimization. Each
adapter checks family-specific evidence and declared numeric thresholds. A pass
continues to mean evidence presence and threshold satisfaction, not mathematical
truth.

### Paper quality

Replace page-count floors with soft planning ranges and hard argument-coverage
and evidence-density gates. Add deterministic checks for:

- abstract coverage of task, method, result, validation, and conclusion;
- bibliography metadata, body-use, uniqueness, source locators, and verification
  status, while leaving live DOI/OpenAlex/Scholar lookup to the research phase;
- unresolved LaTeX references/citations, log warnings, figure/table traceability,
  captions, axes/units, and optional grayscale/color-accessibility evidence.

### Delivery and submission

Create separate `delivery/` and `official-submission/` manifests. The former may
contain portable LaTeX and support materials for the user. The latter contains
only files allowed by the selected official contest profile. Verification must
reject a COMAP official submission that includes a support archive.

### Rules, CI, and invocation evaluation

Add a hash-bound `rules.lock.json` generator/validator using explicitly supplied
official local snapshots or URLs and structured rule fields. Do not silently
fetch or infer rules. Expand explicit-invocation cases in Chinese and English.
Add a Windows CI job with UTF-8 mode and a non-ASCII temporary path; keep full
XeLaTeX artifact QA on Ubuntu.

## Compatibility

- Preserve all existing command-line interfaces and report schemas.
- Use only the Python standard library in new scripts.
- Keep `SKILL.md` below 500 lines and route details to embedded references.
- Update English and Chinese READMEs together.
- Do not change the explicit-invocation-only trigger.

## Verification

Add unit tests for every new script and both pass/fail paths. Run the skill
contract validator, UTF-8 quick validation, the complete unit suite, template
compilation/visual QA where available, and a clean-tree diff review. Finally sync
the verified repository state to the installed local Skill and compare file
hashes.

