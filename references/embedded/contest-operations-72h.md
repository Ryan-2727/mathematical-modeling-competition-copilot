# Contest operations and 72-hour control

Adapt the hours proportionally when the contest duration differs. Freeze the
schedule in `reports/milestones.csv`; do not let an unvalidated enhancement
consume writing or submission time.

## Milestones

| Hour | Required gate |
| --- | --- |
| 0-3 | Rules, allowed sources, deliverables, team roles, and problem-choice criteria recorded |
| 3-8 | Every candidate problem scored for data burden, mechanism fit, validation feasibility, writing risk, and team fit |
| 8-12 | Selected problem decomposed; data audited; baseline runs end to end for the highest-risk subproblem |
| 12-30 | Every subproblem has a baseline, provisional result, and planned validation |
| 30-42 | Primary models frozen unless a recorded failure test is triggered |
| 42-54 | Decisive stress tests complete; figures and tables frozen from result files |
| 54-60 | Complete paper assembled; abstract contains quantitative answers |
| 60-66 | Baseline verification and optional award-review question |
| 66-70 | Only accepted high-impact revisions; rerun affected evidence |
| 70-72 | Final content freeze, anonymity, AI disclosure, archive preflight, and official-timeline check |

The table is an illustrative control rhythm, not a substitute for the locked
contest profile. For CUMCM 2026, use the exact profile schedule: freeze the
paper during H70--H73, finish the final-content lock before H74, record the
final MD5 no later than H74 (2026-09-13 20:00), upload only after H74.5
(2026-09-13 20:30), and preserve the receipt before H92
(2026-09-14 14:00). Do not change the paper after the final MD5 is recorded.

## Stop-loss rules

- If a baseline is not running by hour 12, simplify the abstraction.
- If an enhancement cannot beat or explain a baseline by hour 42, drop it.
- If a result cannot be reproduced by hour 54, remove or label it unresolved.
- Never trade the final submission window for a cosmetic model variant.
