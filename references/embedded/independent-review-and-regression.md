# Independent review aggregation and regression

Use this module only after modeling, the complete paper, and baseline
verification are finished, and only after the user accepts the optional
post-paper review. The aggregate is an internal diagnostic. It must not predict
an award, imitate an official judge, or replace baseline verification.

## Independent review packet

Run three separate passes with exactly one role each: `model`, `evidence`, and
`writing`. Give each reviewer only the statement and the team's own artifacts.
Do not give one reviewer another review, an intended score, a suspected defect,
or a paired excellent paper.

Each UTF-8 JSON file uses this contract:

```json
{
  "review_id": "model-review-01",
  "reviewer_role": "model",
  "score": 4,
  "confidence": 0.8,
  "artifact_locators": [
    "paper/main.tex:section-model",
    "results/model_metrics.json"
  ],
  "strongest_objection": {
    "summary": "The boundary assumption lacks a limiting-case check.",
    "severity": "major",
    "artifact_locator": "paper/main.tex:assumption-boundary",
    "rerun_required": true
  },
  "accepted_limitations": [
    {
      "summary": "No external validation set is available.",
      "artifact_locator": "reports/data_inventory.csv:validation-data",
      "rerun_required": false
    }
  ]
}
```

Requirements:

- `review_id` values are distinct and the three role values occur exactly once.
- `score` is an internal 1--5 diagnostic; `confidence` is in the closed interval
  0--1.
- `artifact_locators` and the strongest objection's locator point to concrete
  paper, result, code, data, or report locations.
- `severity` is `none`, `minor`, `major`, or `veto`.
- Every accepted limitation remains visible and records whether accepting or
  fixing it requires rerunning the baseline gates.
- Do not add award labels, probabilities, likelihoods, or predictions.

## Aggregation

Run:

```bash
python scripts/aggregate_reviewer_reports.py \
  --review reports/model_review.json \
  --review reports/evidence_review.json \
  --review reports/writing_review.json \
  --out reports/independent_review_aggregate.json
```

The aggregate reports score/confidence summaries, material score disagreement,
veto-level objections, accepted limitations, and `rerun_required`. A valid
aggregate may have status `PASS`, `REVIEW`, `RERUN_REQUIRED`, or `VETO`.
`VETO` means an unresolved veto-level objection is visible; it is not an award
forecast. Input/schema errors produce `FAIL`.

## Revision and regression rule

Reviewer disagreement alone does not invalidate the baseline paper. Resolve or
explicitly accept findings with the user. If `rerun_required` is true, rerun the
affected computation, refresh result evidence, rebuild the PDF, and repeat all
baseline verification gates before submission freeze. Never update benchmark
baselines or reviewer scores merely to make a regression disappear.

## Blinded skill-release regression

Keep benchmark statements, raw inputs, private scoring evidence, and current
artifacts outside the solving context. The repository may contain the
metadata-only schema and a disabled synthetic example, but not copyrighted
statements, paired excellent papers, hidden expected answers, or solutions.

For a user-owned historical corpus, create the private manifest and input copy
before any solving run:

```powershell
python scripts/prepare_private_regression.py inventory `
  --corpus-root <historical-corpus> `
  --out <private-root>/inventory.json

# The default inventory only discovers cases. For a small, selected calibration
# set, add --inspect-cases (and --hash-candidates only when hashes are needed).
# Review inventory.json, keep cases disabled until their statement and original
# attachments are explicitly allow-listed, then run:
python scripts/prepare_private_regression.py prepare `
  --corpus-root <historical-corpus> `
  --private-root <private-root> `
  --manifest <private-root>/manifest.json `
  --out <private-root>/prepare-report.json
```

The private root must not overlap the source corpus or the public Git
repository. The preparer rejects path escapes and generated/solution directories;
result-named inputs and contaminated source trees require explicit reviewed
acknowledgement. Do not use a case until preparation passes.

Run:

```bash
python scripts/run_benchmark_regression.py \
  --project-dir <private-benchmark-root> \
  --manifest <private-benchmark-manifest.json> \
  --out <private-benchmark-root>/benchmark-regression.json \
  --execute
```

Each enabled case records its problem family, allowed inputs, required
subproblems, expected artifact classes, argv command, runtime budget, result
file, blinded rubric dimensions, baseline scores, and accepted regression
tolerance. A missing artifact, invalid score evidence, execution failure, or
regression beyond tolerance blocks release. The runner reads baselines but never
updates them; a baseline change requires separate human review and an explicit
commit explaining why the benchmark itself changed.
