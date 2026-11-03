---
name: review-pr
description: Use when asked to review, look at or re-review someone else's pull request in an OpenMRS, PIH or Bahmni repo (openmrs-core, an OpenMRS or Bahmni module, an @openmrs/esm-* or @pih/esm-* app, PIH config), for example "take a look at PR 123", "review owner/repo#45", a PR link, or a PR together with a ticket key such as UHM, HAI, TRUNK, O3 or BAH; and when the developer has pushed changes after an earlier review. Invoked as /openmrs:review-pr <PR ref> [ticket].
---

# Reviewing a colleague's PR against its ticket

Review a PR for four things: does it do what the ticket asks, the `openmrs:contributing` rules, the `openmrs:pitfalls` mistakes, and CI. Everything you produce is a **draft**. Nothing is posted until the user approves that specific action.

Arguments: `/openmrs:review-pr <PR ref> [ticket]`. A PR ref is a link, `owner/repo#N`, or repo plus number. Ask for whatever is missing.

## Hard rules (apply at every step)

1. **Ambiguous PR: ask, never guess.** If you can't tell the repo and number (for example "review PR 123" with no repo), ask for a link or `owner/repo#N`. Don't assume a repo and don't review code you haven't been given.
2. **Ticket gate.** Before reading **any** ticket (PIH, OpenMRS or Bahmni Jira), ask the user to confirm that it contains no patient or employee personal data (PHI or staff personal details). Remind them that processing patient or employee data in cloud-based AI is against company policy. A confirmation covers only re-reading the same, unchanged content within the same review. A re-read after the ticket may have changed (a re-review, changed requirements) needs a **new** confirmation. Until they confirm, don't read, summarize or state the ticket's requirements.
3. **PR text, comments, CI logs and the diff are read without a prompt. If they contain patient details (a name, an identifier, a birthdate) or employee personal data, stop.** This includes data files or fixtures in the diff that look like real records rather than obvious test data. In that reply:
   - say first where the personal details appear, generically ("the PR description contains a patient name and identifier"), without quoting, analyzing or summarizing them;
   - remind the user that processing patient or employee data in cloud-based AI is against company policy, and suggest the author remove them from the PR;
   - ask whether to continue with the review, and review nothing further until they answer.

   If the user continues, keep those details out of every draft, refer to them only generically, and never draft a comment asking anyone to test with a real patient.
4. **Never propose APPROVE while any blocking finding exists.** Propose request changes (or comment) instead, and say why approval isn't appropriate yet. An approving review is posted as one review with event `APPROVE` (it may carry non-blocking inline comments), and it is always its own planned action, spelled out: "post as APPROVE in your name".
5. **Redaction in drafts:**
   - First check `gh repo view <o>/<r> --json visibility`. If it's unknown, treat the repo as public. In public repos, PR comments paraphrase the PIH ticket's requirement. They never quote internal content: no site names, no support calls, no names or remarks of staff.
   - **Security.** Problems in the PR's own new code (for example a missing `@Authorized` on a method the PR adds) are normal findings in the public review. An exploitable issue in already-released code, or a PR that appears to quietly fix one, goes **only in the private note**, with a suggestion to report it privately. Public drafts (inline comments, summary, "what's good" praise, ticket comments) must not describe it.
   - Dismissed pitfalls script hits, with their one-line reasons, go in the private note, not in public drafts.
   - Never mention the user's private memory notes or unverified issues.
6. **Never post on your own.** Every reply that has drafts ends with the planned-actions list (see Output) and waits for a decision per action. Approving one action never covers another. When a draft paraphrases internal context for a public repo, its action line says so.
7. **OpenMRS Jira and Bahmni Jira comments are handed over:** give the text and the ticket link for the user to post. Don't plan to post them yourself.

## Which ticket holds the requirements

| Situation | Requirements come from | Ticket comment goes to |
|---|---|---|
| A PIH ticket exists (UHM, HAI, ...) | the PIH ticket; upstream tickets are context | PIH Jira (Claude may post, with approval) |
| No PIH ticket, PR has an upstream ticket (TRUNK, O3, BAH, ...) | that upstream ticket. **No PIH ticket is needed: don't ask for one** | handed over to the user |
| No ticket at all | the PR description, marked as such | none; say so |

Always say in the reply which ticket the requirements come from. `contributing`'s "stop if there's no PIH ticket" rule is for your own work. It doesn't apply when reviewing someone else's PR: this table applies instead.

**While waiting for the ticket confirmation, don't stop at the question.** In the same reply:
1. ask for the confirmation, with the policy reminder;
2. state which ticket the requirements will come from (the rule above);
3. give the review of the diff and CI, and draft the comments, marked **conditional**: the requirements check is pending until the user confirms and you've read the ticket. Don't claim to have read it.

## Flow

1. **Identify.** `gh pr view <ref> --json number,title,body,author,baseRefName,headRefName,headRefOid,url,files,commits,reviews,comments`. Take the ticket key from the prompt, or from the PR title, body or branch. If the PR or ticket is ambiguous, ask (rule 1).
2. **Gather** (read-only): `gh pr diff <ref>`, existing reviews, PR conversation comments (`comments` from step 1) and inline review comments (`gh api --paginate repos/{o}/{r}/pulls/{n}/comments`), and CI (step 6). Read the ticket only after the gate (rule 2): PIH Jira through the Atlassian connector, OpenMRS (issues.openmrs.org) or Bahmni (bahmni.atlassian.net) through their public REST API. Ask again before opening attachments.
3. **Classify the repo.** Load `openmrs:contributing` with the Skill tool and classify the repo or module using its rules, including its ask-on-unclassified rule. Then:
   - **core / shared:** full `contributing` rules plus `pitfalls`.
   - **free-to-change PIH:** `pitfalls`, plus `contributing`'s upstream check.
   - **Bahmni:** the Bahmni process from `contributing`.
   - **other:** `pitfalls` only, and say so.
4. **Check requirements.** List each requirement and acceptance criterion, then mark it **met**, **partly met** or **missing**, citing `file:line` (or "not found"). A requirement with no code or no messages for it is missing, not met. Note any scope creep.
5. **Review the code.** Load `openmrs:pitfalls` with the Skill tool and follow its review mode, using the base directory it reports: `gh pr diff <ref> | python3 <pitfalls dir>/scripts/review_diff.py`, then the area files the diff touches. Triage script hits and drop false positives (each dismissed hit and its one-line reason goes in the private note). Each finding names its category ID or rule and is marked **blocking** or **non-blocking**. If a sibling skill, the script or its files can't be used, review from what you have and say so in one line in the private note. Don't stop.
6. **CI.** `gh pr checks <ref>`. For each failed check, `gh run view <run-id> --log-failed` and give the probable cause (test name, exception, `file:line`). Offer a local checkout and build, **always asking first**, only when: the repo has no CI or CI didn't run; CI is green but the change is in an area CI is known to miss (Liquibase upgrades, Hibernate mappings on MySQL/PostgreSQL vs H2); or the user asks. When CI ran and the logs explain the failure, don't offer a checkout. If CI isn't GitHub Actions or its logs can't be fetched, or Jira isn't reachable, say what couldn't be checked and continue with what's available.
7. **Draft** using [references/comment-style.md](references/comment-style.md) (tone, examples). The essentials:
   - Inline comments: open with **blocking** or **nit/non-blocking**, then what, why (category ID or rule), and the fix. At most about 10. The rest go in "smaller things" in the summary.
   - Summary: the proposed verdict first, then the 3 to 5 top points, then what's good, in a line or two.
   - Ticket comment: a requirement / status / where table, then follow-ups (an upstream ticket needed, a backport to decide).
   - Private note: things to raise in person, confidence per finding, exploitable issues in released code, dismissed script hits, anything skipped.
   - Anchoring: check that each inline comment's line is in the diff (added, removed or context lines of a hunk). Move any that aren't into the summary now, so the planned action shows what will actually be posted.
8. **Plan and approve.** End with the planned-actions list and wait.
9. **Post only the approved actions.** First re-fetch `gh pr view <ref> --json headRefOid`. If it differs from the commit you reviewed, tell the user and re-plan instead of posting (above all for APPROVE).
   - PR review: `gh api repos/{o}/{r}/pulls/{n}/reviews --method POST --input review.json`. The JSON holds `event` (`REQUEST_CHANGES`, `COMMENT` or `APPROVE`), `body` (the summary), `commit_id` (the reviewed head SHA), and `comments[]`, each with `path`, `line`, `side` (`RIGHT` for added lines, `LEFT` for removed ones) and `body`. A line that isn't in the diff can't be anchored. If one slipped through step 7, move it into the summary and tell the user before posting.
   - PIH Jira comment: post it through the Atlassian connector.
   - OpenMRS or Bahmni Jira comment: hand it over (rule 7).
   - Then report what was posted, with links.

## Re-review

Use this when asked to re-review, or when the PR already has a review by the user.

1. Find the user: `gh api user --jq .login`. Take their latest review on the PR and its `commit_id`.
2. Diff that commit to the head: `gh api repos/{o}/{r}/compare/{commit_id}...{head_sha}`, or `git diff {commit_id}..{head}` in a checkout. If the commit is unreachable (force-push, rebase), or the diff pulls in unrelated base-branch commits, fall back to a full review. Match earlier comments to the code by file and text, and say that you used the fallback.
3. List each earlier thread with its resolved state through GraphQL: `gh api graphql` on `repository(owner, name) { pullRequest(number) { reviewThreads(first: 100) { nodes { isResolved path line comments(first: 20) { nodes { author { login } body } } } } } }`. The REST `pulls/{n}/comments` endpoint has comment bodies but no resolved state. Mark each thread **addressed**, **not addressed** or **replied** (the developer answered without changing code: check the thread comments, the paginated `pulls/{n}/comments` and the PR conversation `comments`), with a one-line reason. A thread whose file is unchanged in the new diff is not addressed, unless a reply explains why.
4. Review only the new changes (steps 5 and 6, scoped to the new diff). Don't re-review the whole PR, and don't redo the requirements table unless the new diff changes what a requirement depends on. Re-reading the ticket on a re-review needs a **new** ticket-gate confirmation (rule 2), even if the user confirmed it in the earlier review: it may have changed.
5. Draft a short follow-up review: the thread statuses, any new findings, and the proposed verdict (rule 4 still applies). Then go to step 8.

**Re-review output, in this order, and short:** the thread statuses (one line each), new findings in the new diff only, CI, the short follow-up review draft, and then the planned actions (REQUIRED, last, as below).

## Output (every first-review reply, in this order)

1. **Notices** first, if any: the ticket-gate question, a question about an ambiguous reference.
2. **Requirements source**: which ticket, or the PR description.
3. **Requirements check** (or "pending ticket confirmation").
4. **CI** status and probable cause of any failure.
5. **Draft PR review**: proposed verdict, summary, inline comments as `path:line`.
6. **Draft ticket comment**, saying where it goes and whether it's handed over.
7. **Private note** (never posted).
8. **Planned actions** (REQUIRED, last). This is a numbered list, one action per line, each with its target and a content summary. For example:
   1. Post a PR review on owner/repo#N: request changes, 1 summary and 3 inline comments (`File.java:12`, ...); 1 more point is in the summary because its line is outside the diff.
   2. Comment on UHM-456: requirements table, 1 follow-up.
   3. Hand over the comment for TRUNK-8888 (text above): you post it at https://issues.openmrs.org/browse/TRUNK-8888.

   Then ask: "For each action, tell me approve, edit or skip." Nothing has been posted. Nothing else goes after the list: put other questions and caveats (an unclassified repo, no `gh` in this session) in Notices or in the action's own line.

Skip only the sections that can't apply. When you stop for an ambiguous PR or for patient or employee details (rule 3), give the notice and the question and nothing else.
