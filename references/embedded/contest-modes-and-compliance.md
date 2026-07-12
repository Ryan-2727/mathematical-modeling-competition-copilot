# Contest modes and compliance

Set one mode in `contest_manifest.json` before reading the problem.

## Modes

| Mode | Permitted behavior |
| --- | --- |
| `training` | Use historical problems, public solutions, exemplar corpora, and broad research. Label all reused material. |
| `live` | Use only the official statement, permitted data/software, static authoritative sources, and the team’s own work. Do not browse discussion, solution, social, Q&A, code-sharing, or interactive-help sites for the current problem. |
| `posthoc` | Compare a frozen independent solution with public exemplars and write learning notes. Never rewrite the historical result as if it had been produced during the contest. |

## Rules snapshot gate

Before modeling, create `reports/contest_rules_snapshot.md` from current official
sources. Record contest/year, source URLs, access time, AI policy, allowed external
data and tools, communication restrictions, page/font/file rules, deadline/time
zone, submission method, and support-material requirements. Mark each item
`verified`, `unknown`, or `not applicable`; `live` mode cannot become submission
ready with any critical item unknown.

Do not silently apply a prior-year rule. Keep historical rule files only as
baselines and defer to the current official snapshot.

## AI transparency gate

Use `scripts/log_ai_use.py` whenever AI materially affects research, model design,
code, data interpretation, writing, or figures. Keep key prompt/response evidence
outside the paper when the contest requires it. Generate the required declaration,
inline citations, bibliography entries, and support-material report from the log
with `scripts/render_ai_use_report.py`.

If AI is not used, create the contest-required non-use declaration. Do not claim
that an AI-generated result is independently verified until the team has checked
the data, code, equations, references, and conclusion.

## Communication and source safety

In `live` mode, prohibit requests for ideas or answers from people outside the
team, posting any problem/work fragment, and browsing current-problem discussion.
For each external source, record URL, publisher, access date, license/permission,
claim supported, and whether it is static and authoritative. Reject a source whose
provenance, permission, or relevance cannot be established.

## Freeze and submission states

Use only these states: `draft`, `verified`, `frozen`, `hashed`, `submitted`,
`receipt_verified`. Moving forward requires evidence:

- `verified`: all content, code, references, and visual checks pass;
- `frozen`: no further content edits without returning to `draft`;
- `hashed`: `scripts/verify_submission.py` records final hashes and file sizes;
- `submitted`: submission time and method recorded;
- `receipt_verified`: platform confirmation or receipt recorded.

After a contest closes, do not modify the submission artifact. Use
`scripts/set_submission_state.py` to record each state transition. If a contest uses a
pre-uploaded hash, recompute and re-upload it after every change before the hash
deadline.
