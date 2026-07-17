# Optional post-paper award review

Use this module only after the model, results, figures, and complete paper have
been assembled and the baseline final-verification checks have run.

## Mandatory prompt

Ask before performing this phase:

> The modeling and paper are complete and baseline verification has run. Would
> you like the optional award-focused review: simulated reviewers, key-claim
> stress tests, and prioritized revision suggestions?

If the user declines, skip directly to submission freeze. Do not perform this
review silently or delay a time-critical submission.

## When the user opts in

Create `reports/post_paper_review.md`. Use only the team's statement, data,
code, results, paper, and already permitted sources. Do not search for current
problem answers, compare against a paired exemplar, or import outside solution
content.

Read `reviewer-scorecard-and-presentation.md`. Complete
`reports/reviewer_scorecard.csv` for these four evidence dimensions:
`assumption_rationality`, `model_creativity`, `result_correctness`, and
`writing_clarity`. The 1--5 scores are an internal diagnostic, not an official
contest scoring formula. Every score needs paper/result evidence, the strongest
remaining objection, the smallest credible fix, and a completion status.

Run three independent lenses:

1. **Model reviewer:** challenge assumptions, mechanism, model choice, and
   claimed novelty. Identify the single most damaging plausible objection.
2. **Evidence reviewer:** trace each decisive conclusion to an executed result;
   request one proportionate counterfactual, baseline, or robustness test where
   a conclusion depends on a fragile choice.
3. **Paper reviewer:** check whether a reader can find each question's method,
   quantified answer, interpretation, and limitation without hunting through
   the paper.

For each finding, record severity, evidence, smallest credible fix, expected
benefit, time cost, and whether the user approves the change. Prefer at most
three high-impact revisions. Do not add model complexity merely to look more
advanced.

## Re-entry gate

After any accepted revision, rerun code as needed, refresh the claims ledger,
rebuild the paper, and repeat final verification before freezing. Record any AI
use in the existing audit log and obey the current contest's AI rules. Then run:

```bash
python scripts/verify_award_readiness.py \
  --project-dir <project-dir> \
  --out <project-dir>/reports/award_readiness.json
```

Passing confirms that the decision, stress-test, unit, reviewer, milestone, and
subproblem evidence ledgers are structurally complete. It does not establish
that the mathematics is correct and does not predict an award.
