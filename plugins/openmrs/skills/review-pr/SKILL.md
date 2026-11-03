---
name: review-pr
description: Use when asked to review, look at or re-review someone else's pull request in an OpenMRS, PIH or Bahmni repo (openmrs-core, an OpenMRS or Bahmni module, an @openmrs/esm-* or @pih/esm-* app, PIH config), for example "take a look at PR 123", "review owner/repo#45", a PR link, or a PR together with a ticket key such as UHM, HAI, TRUNK, O3 or BAH; and when the developer has pushed changes after an earlier review. Invoked as /openmrs:review-pr <PR ref> [ticket].
---

# Reviewing a colleague's PR against its ticket

Review a PR for four things: does it do what the ticket asks, the `openmrs:contributing` rules, the `openmrs:pitfalls` mistakes, and CI. Everything you produce is a **draft**. Nothing is posted until the user approves that specific action.

Arguments: `/openmrs:review-pr <PR ref> [ticket]`. A PR ref is a link, `owner/repo#N`, or repo plus number. Ask for whatever is missing.

## Hard rules (apply at every step)

1. **Ambiguous PR: ask, never guess.** If you can't tell the repo and number (for example "review PR 123" with no repo), ask for a link or `owner/repo#N`. Don't assume a repo and don't review code you haven't been given.
2. **Ticket gate.** Before reading **any** ticket (PIH, OpenMRS or Bahmni Jira), ask the user to confirm that it contains no patient data or PHI. Remind them that processing patient or employee data in cloud-based AI is against company policy. Ask every time, unless the user has already confirmed it for that ticket. Until they confirm, don't read, summarize or state the ticket's requirements.
3. **PR text, comments and CI logs are read without a prompt.** If they contain patient details (a name, an identifier, a birthdate), tell the user right away, repeat the company-policy reminder, and keep those details out of every draft. Refer to them only generically ("the patient details in the PR description"). Don't draft a comment asking anyone to test with a real patient.
4. **Never propose APPROVE while any blocking finding exists.** Propose request changes (or comment) instead, and say why approval isn't appropriate yet. An APPROVE action is always listed on its own and spelled out: "post as APPROVE in your name".
5. **Redaction in drafts:**
   - In public repos, PR comments paraphrase the PIH ticket's requirement. They never quote internal content: no site names, no support calls, no names or remarks of staff.
   - A likely security vulnerability goes **only in the private note**, with a suggestion to report it privately. Never in a PR or ticket comment.
   - Never mention the user's private memory notes or unverified issues.
6. **Never post on your own.** Every reply that has drafts ends with the planned-actions list (see Output) and waits for a decision per action. Approving one action never covers another.
7. **OpenMRS Jira and Bahmni Jira comments are handed over:** give the text and the ticket link for the user to post. Don't plan to post them yourself.

## Which ticket holds the requirements

| Situation | Requirements come from | Ticket comment goes to |
|---|---|---|
| A PIH ticket exists (UHM, HAI, ...) | the PIH ticket; upstream tickets are context | PIH Jira (Claude may post, with approval) |
| No PIH ticket, PR has an upstream ticket (TRUNK, O3, BAH, ...) | that upstream ticket. **No PIH ticket is needed: don't ask for one** | handed over to the user |
| No ticket at all | the PR description, marked as such | none; say so |

Always say in the reply which ticket the requirements come from.

**While waiting for the ticket confirmation, don't stop at the question.** In the same reply:
1. ask for the confirmation, with the policy reminder;
2. state which ticket the requirements will come from (the rule above);
3. give the review of the diff and CI, and draft the comments, marked **conditional**: the requirements check is pending until the user confirms and you've read the ticket. Don't claim to have read it.

## Flow

1. **Identify.** `gh pr view <ref> --json number,title,body,author,baseRefName,headRefName,headRefOid,url,files,commits,reviews`. Take the ticket key from the prompt, or from the PR title, body or branch. If the PR or ticket is ambiguous, ask (rule 1).
2. **Gather** (read-only): `gh pr diff <ref>`, existing reviews and comments (`gh api repos/{o}/{r}/pulls/{n}/comments`), and CI (step 6). Read the ticket only after the gate (rule 2): PIH Jira through the Atlassian connector, OpenMRS (issues.openmrs.org) or Bahmni (bahmni.atlassian.net) through their public REST API. Ask again before opening attachments.
3. **Classify the repo.** Load `openmrs:contributing` with the Skill tool and use its module classification:
   - **core / shared** (openmrs-core, refapp modules, `@openmrs/esm-*`): full `contributing` rules plus `pitfalls`. Breaking public API changes are blocking: keep the old method (deprecated) and add a new one.
   - **free-to-change PIH:** `pitfalls` plus its upstream check.
   - **Bahmni:** the Bahmni process from `contributing`.
   - **other:** `pitfalls` only, and say so.
4. **Check requirements.** List each requirement and acceptance criterion, then mark it **met**, **partly met** or **missing**, citing `file:line` (or "not found"). A requirement with no code or no messages for it is missing, not met. Note any scope creep.
5. **Review the code.** Load `openmrs:pitfalls` with the Skill tool and follow its review mode, using the base directory it reports: `gh pr diff <ref> | python3 <pitfalls dir>/scripts/review_diff.py`, then the area files the diff touches. Triage script hits and drop false positives. Each finding names its category ID or rule and is marked **blocking** or **non-blocking**. If a sibling skill, the script or its files can't be used, review from what you have and say so in one line in the private note. Don't stop.
6. **CI.** `gh pr checks <ref>`. For each failed check, `gh run view <run-id> --log-failed` and give the probable cause (test name, exception, `file:line`). Offer a local checkout and build, **always asking first**, only when: the repo has no CI or CI didn't run; CI is green but the change is in an area CI is known to miss (Liquibase upgrades, Hibernate mappings on MySQL/PostgreSQL vs H2); or the user asks. When CI ran and the logs explain the failure, don't offer a checkout.
7. **Draft** using [references/comment-style.md](references/comment-style.md) (tone, examples). The essentials:
   - Inline comments: open with **blocking** or **nit/non-blocking**, then what, why (category ID or rule), and the fix. At most about 10. The rest go in "smaller things" in the summary.
   - Summary: the proposed verdict first, then the 3 to 5 top points, then what's good, in a line or two.
   - Ticket comment: a requirement / status / where table, then follow-ups (an upstream ticket needed, a backport to decide).
   - Private note: things to raise in person, confidence per finding, security concerns, anything skipped.
8. **Plan and approve.** End with the planned-actions list and wait.
9. **Post only the approved actions:**
   - PR review: `gh api repos/{o}/{r}/pulls/{n}/reviews --method POST --input review.json`. The JSON holds `event` (`REQUEST_CHANGES`, `COMMENT` or `APPROVE`), `body` (the summary), `commit_id` (the head SHA), and `comments[]`, each with `path`, `line`, `side` (`RIGHT` for added lines, `LEFT` for removed ones) and `body`. A line that isn't in the diff can't be anchored, so move that comment into the summary.
   - PIH Jira comment: post it through the Atlassian connector.
   - OpenMRS or Bahmni Jira comment: hand it over (rule 7).
   - Then report what was posted, with links.

## Re-review

Use this when asked to re-review, or when the PR already has a review by the user.

1. Find the user: `gh api user --jq .login`. Take their latest review on the PR and its `commit_id`.
2. Diff that commit to the head: `gh api repos/{o}/{r}/compare/{commit_id}...{head_sha}`, or `git diff {commit_id}..{head}` in a checkout. If the commit is unreachable (force-push, rebase), or the diff pulls in unrelated base-branch commits, fall back to a full review. Match earlier comments to the code by file and text, and say that you used the fallback.
3. List each earlier thread (`gh api repos/{o}/{r}/pulls/{n}/comments`, plus resolved state) and mark it **addressed**, **not addressed** or **replied** (the developer answered without changing code), with a one-line reason. A thread whose file is unchanged in the new diff is not addressed, unless a reply explains why.
4. Review only the new changes (steps 5 and 6, scoped to the new diff). Don't re-review the whole PR, and don't redo the requirements table unless the new diff changes what a requirement depends on.
5. Draft a short follow-up review: the thread statuses, any new findings, and the proposed verdict (rule 4 still applies). Then go to step 8.

**Re-review output, in this order, and short:** the thread statuses (one line each), new findings in the new diff only, CI, the short follow-up review draft, and then the planned actions (REQUIRED, last, as below).

## Output (every first-review reply, in this order)

1. **Notices** first, if any: the ticket-gate question, the patient-data warning, a question about an ambiguous reference.
2. **Requirements source**: which ticket, or the PR description.
3. **Requirements check** (or "pending ticket confirmation"), and for a re-review, the thread statuses.
4. **CI** status and probable cause of any failure.
5. **Draft PR review**: proposed verdict, summary, inline comments as `path:line`.
6. **Draft ticket comment**, saying where it goes and whether it's handed over.
7. **Private note** (never posted).
8. **Planned actions** (REQUIRED, last). This is a numbered list, one action per line, each with its target and a content summary. For example:
   1. Post a PR review on owner/repo#N: request changes, 1 summary and 3 inline comments (`File.java:12`, ...).
   2. Comment on UHM-456: requirements table, 1 follow-up.
   3. Hand over the comment for TRUNK-8888 (text above): you post it at https://issues.openmrs.org/browse/TRUNK-8888.

   Then ask: "For each action, tell me approve, edit or skip." Nothing has been posted.

Skip only the sections that can't apply. When you stop to ask for an ambiguous PR, give the question and nothing else.
