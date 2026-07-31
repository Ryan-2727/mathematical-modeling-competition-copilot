# Skill Deduplication Capability Matrix

This matrix records where each pre-refactor capability remains after the
entry-point and maintenance refactor. It is a release audit, not an additional
runtime instruction source.

| Capability | Entry phase | Authoritative detail or executable gate | Preserved behavior |
| --- | --- | --- | --- |
| Explicit invocation only | Frontmatter and operating contract | `evals/invocation-cases.json`, `validate_skill_contract.py` | Ordinary modeling requests do not trigger the Skill |
| Mode, rules, privacy, AI use | 0 | `contest-modes-and-compliance.md`, `cumcm-2026-rules.md`, `verify_online_actions.py`, `verify_submission.py` | Live artifacts remain local; ambiguous online action pauses for the user |
| CUMCM 2026 dates and sources | 0 | `assets/contest-profiles/cumcm-2026.json`, `contest_profile.py`, `lock_contest_rules.py` | Existing dates, source roles, freshness checkpoints, and submission limits are unchanged |
| Setup and H6 audition | 1 | `contest-setup.md`, `cumcm-2026-readiness.md`, `verify_problem_audition.py` | Comparable executable candidate evidence and H6 lock remain mandatory |
| Model routing and semantic audit | 2 | `cumcm-model-selection.md`, `mechanism-semantics-and-argument.md` | Model choice follows mechanism and declared data semantics |
| Baseline, competitor, and refutation | 2 | `model_decision_log.csv`, `model_challenge.json`, `verify_decision_quality.py` | Unsupported complexity is rejected or its claim is narrowed |
| Simplification approval | 2 and 7 | `fallback_plan.csv`, `result-first-paper-convergence.md` | User approval remains required before removing named noncritical factors |
| Causal/predictive boundary | 2 and 4 | `runtime-template-and-decision-audits.md`, `causal_claims.csv` | Causal claims still require estimand, graph, identification, and diagnostics |
| Ten verified scholarly sources | 3 | `verified-literature-and-two-part-delivery.md`, `verify_bibliography_metadata.py` | Metadata, Scholar observation, source passage, and LaTeX citation checks remain |
| Reproducible computation | 4 | `computation-and-visualization.md`, `run_reproduction.py`, verified-value and model validators | Numeric conclusions still require executed or cited evidence |
| Uncertainty and implementability | 4 | `stress-testing-and-uncertainty.md`, decision-quality gates | Robustness, extreme scenarios, feasibility, cost, interpretation, and contingency remain |
| Tables and scenario sheets | 5 and 8 | `latex-tables.md`, table and visual-design manifests | Units, precision, captions, sources, and cross-file consistency remain |
| Figure narrative and visual quality | 6 | `paper-presentation-and-visual-design.md`, figure validators | Every figure still needs a question, claim, takeaway, source, and legibility evidence |
| Result-first paper and abstract | 7 | `paper-writing.md`, `result-first-paper-convergence.md`, abstract/result validators | Analysis-method-result abstract and quantified answers remain mandatory |
| Portable LaTeX | 7 and 9 | `latex-paper-pipeline.md`, LaTeX compatibility and portable-archive validators | XeLaTeX/latexmk builds for VS Code and Overleaf remain required |
| Strict final verification | 9 | `orchestration-and-paper-assurance.md`, `final-verification.md`, `contestctl.py` | Unresolved strict `LIMITED` evidence still blocks release |
| Optional award review consent | 10 | `post-paper-award-review.md`, reviewer aggregation and award-readiness validators | Review runs only after paper completion and explicit user consent |
| Two-part delivery and official package separation | 11 | `verified-literature-and-two-part-delivery.md`, `submission-and-anonymity.md`, delivery validators | PDF/LaTeX and support material remain separate from contest-limited submission files |
| Offline corpus learning and private regression | 12 | `training-evaluation-loop.md`, private and blinded regression scripts | Private artifacts stay outside Git and paired papers never enter live solving context |

The machine-enforced file and content inventory is
`assets/skill-contract.json`. The complete generated contest-project layout is
owned by `scripts/init_contest.py`; the shorter tree in `SKILL.md` is explicitly
a core navigation layout.
