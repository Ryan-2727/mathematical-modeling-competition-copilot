# CUMCM 2026 Compliance Hardening Design

## Objective

Close five contest-compliance gaps without changing the Skill's end-to-end
modeling, coding, paper-writing, verification, or delivery workflow:

1. forbid browsing current-problem content on communication platforms during
   the live contest, not only uploading or posting it;
2. verify the actual MD5 of frozen submission files instead of recording only a
   deadline;
3. separate local phrase-overlap advice from the official two-metric 25%
   similarity rule;
4. describe paper and electronic submission formats separately; and
5. narrow README wording about permitted internet use.

The governing sources are the 2026 CUMCM participation notice, paper-format
requirements, contest rules, and AI-use rules published by the official CUMCM
site. Local checks must not claim to replace the official client, submission
system, or Tongfang/CNKI report.

## Chosen Approach

Use source-driven policy plus separate deterministic evidence verifiers:

- extend the online-action verifier with content and destination
  classification;
- add a real file-hash lock verifier for submission artifacts;
- add an official similarity-evidence verifier while retaining the existing
  phrase-overlap checker as advice;
- make surgical wording changes in the rules reference, Skill routing rule, and
  bilingual README files; and
- add focused tests, then run the complete existing verification suite.

Rejected alternatives:

- Documentation-only changes cannot prevent an unsafe live-contest action or
  verify evidence.
- Combining MD5, local phrase overlap, and official similarity evidence in one
  general compliance script would blur distinct authorities and statuses.
- Estimating an official 25% result from local repeated phrases would create a
  false assurance because the official system uses two reported metrics not
  reproduced by this repository.

## Live-Contest Browsing Policy

Keep the existing rule that search queries do not have a lexical blacklist.
Search terms may contain problem wording when the action itself is permitted.
The decision is based on what is accessed and where, not on isolated words.

Extend the online-action record with structured classification fields such as:

- `current_problem_related`: `yes`, `no`, or `uncertain`;
- `destination_category`: `official`, `scholarly`, `static_reference`,
  `communication_platform`, or `uncertain`;
- `interaction`: `search`, `browse`, `upload`, `post`, `share`, or the existing
  action classes; and
- `classification_evidence`: a local explanation or locator that contains no
  copied contest content unless needed for the team's private audit.

During the live contest, any browse, search-result opening, reading, posting,
uploading, or discussion that combines `current_problem_related=yes` with
`destination_category=communication_platform` is a hard failure. This includes
repositories, blogs with social interaction, forums, Q&A sites, group chats,
live streams, and similar public or semi-public communication spaces. A user
decision cannot override an action already classified as prohibited by the
official rule.

Generic research in official, scholarly, or static-reference sources remains
permitted. If either content relation or destination category is uncertain, the
Skill must pause and ask the user to classify the action. The answer resolves
ambiguity; it does not waive a known prohibition. No network action is performed
until that classification is recorded.

## Actual MD5 Lock Verification

Add `scripts/verify_submission_md5_lock.py` and a machine-readable report such
as `reports/submission_md5_lock.json`. The verifier must:

- accept the final paper and optional supporting-material paths only from the
  local project boundary;
- compute each file's actual MD5 and SHA-256 from bytes at verification time;
- compare the actual MD5 with the MD5 recorded from the official client or
  submission evidence;
- record generation time, official-MD5 submission time, file size, evidence
  locator, and the applicable deadline from the contest profile;
- fail when a file changed after the recorded MD5, the values differ, the
  evidence is missing, or the MD5 was generated/submitted after the deadline;
  and
- distinguish `PASS`, `FAIL`, and `LIMITED`, where `LIMITED` means the local
  file can be hashed but official-client evidence is unavailable.

The script must not automate the official client or submission. Reopening or
saving a frozen file changes its digest and invalidates the lock until the
official MD5 process is repeated. Upload-window checks remain owned by the
existing submission state machine.

## Official Similarity Risk Evidence

Retain `scripts/similarity_preflight.py` as a local advisory for repeated long
phrases. Rename its displayed meaning where needed so it never implies official
similarity compliance.

Add a separate verifier, for example
`scripts/verify_similarity_risk.py`, backed by
`reports/similarity_risk.json`. The report stores:

- report provider and evidence locator;
- the two official reported similarity metrics and their names;
- national threshold `0.25` and an optional stricter regional threshold;
- report time, checked paper hash, reviewer, and status; and
- a note that the national rule is triggered when either metric reaches the
  applicable threshold.

The verifier fails if either metric is greater than or equal to the applicable
threshold, the report belongs to a different paper hash, or required evidence
is inconsistent. It returns `LIMITED`, never `PASS`, when no official report is
available. The local phrase checker's result cannot populate or approximate
either official metric.

## Physical and Electronic Format Separation

Rewrite the CUMCM 2026 rules reference into two unambiguous subsections:

- **Physical paper sequence:** commitment page, number-only page, abstract, and
  body, subject to the official current requirements.
- **Electronic paper:** starts with the abstract and excludes both the
  commitment page and number-only page; it is submitted as the required
  standalone uncompressed document.

No paragraph may present the physical front matter as part of the electronic
paper. Contract tests should require both distinct statements.

## README and Skill Wording

Replace broad statements such as "internet search is allowed" or
“允许互联网搜索” in both README languages and the routed policy reference.
The concise replacement must state:

- generic research on official, scholarly, and static-reference sources is
  allowed when otherwise compliant;
- accessing current-problem-related content on communication platforms during
  the live contest is forbidden, including browsing and search-result opening;
- uncertain classification requires a user decision before proceeding; and
- there is no lexical search-term blacklist.

`SKILL.md` should contain only a short routing rule so its main mechanism and
line budget remain unchanged. The detailed policy belongs in the compliance
reference and verifier help text.

## Tests and Verification

Use test-first implementation with fixtures that prove:

1. Live-contest browsing of known current-problem content on GitHub, CSDN,
   Zhihu, a group chat, or a live stream fails even without an upload.
2. Generic official or scholarly research passes, and an uncertain
   classification requests a recorded user decision before any action.
3. A file whose computed MD5 matches timely official evidence passes; changed,
   stale, mismatched, late, missing, or unsafe-path evidence does not.
4. Similarity evidence passes only when both official metrics are below the
   applicable threshold and match the frozen paper hash; either metric at
   exactly 25% fails; missing official evidence is `LIMITED`.
5. The local phrase checker remains advisory and never claims 25% compliance.
6. The rules reference clearly separates physical and electronic formats.
7. English and Chinese README wording, Skill routing, profile validation,
   contract checks, all unit tests, and local-install hash comparison remain
   consistent.

Before completion, run the complete test suite and repository validators, then
copy the verified repository Skill to the installed local Skill location and
compare hashes. Do not push to GitHub unless separately requested.

## Success Criteria

- The workflow blocks both outbound disclosure and prohibited inbound browsing
  of current-problem discussion during the live contest.
- MD5 readiness is based on the actual frozen file and official evidence, not a
  calendar reminder.
- The official 25% rule is represented faithfully without overstating local
  detection capability.
- No reader can mistake physical commitment/number pages for electronic-paper
  content.
- README wording describes the permitted internet boundary precisely in both
  languages.
- Existing modeling and paper-production behavior is otherwise unchanged.

## Non-Goals

- Reproducing or bypassing Tongfang/CNKI similarity detection.
- Automating the official CUMCM client, login, MD5 submission, or file upload.
- Banning search terms or forbidding ordinary research on static authoritative
  sources.
- Changing the Skill's model selection, solving, coding, LaTeX, paper-writing,
  or delivery architecture.
