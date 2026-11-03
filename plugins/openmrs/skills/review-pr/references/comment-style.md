# Comment style for review-pr drafts

Everything here is a draft for the user to approve. Write as the user would write to a colleague, not as an audit report.

## Tone
- Collegial and specific. Say what you saw, in the code, and what you suggest.
- Criticize the code, never the person. Prefer "this loop loads every row" over "you forgot".
- Acknowledge good work briefly and honestly. Skip filler praise.
- Ask a question when you are not sure. Mark confidence in the private note, not in the comment.

## Inline comment
Open with **blocking** or **non-blocking** (use "nit" for taste-level points). Then, in a few lines:
1. **What:** the problem at this `file:line`.
2. **Why:** the consequence, with the category ID or rule (for example C2 from `openmrs:pitfalls`) and a public ref if it helps (an OpenMRS or Bahmni ticket, a docs page).
3. **Fix:** a concrete suggestion. For a small exact replacement, use a GitHub suggestion block:

````
```suggestion
replacement lines here
```
````

Use suggestion blocks only when the change is a few lines and exact. Otherwise describe the fix in words or a short snippet. Keep to about 10 inline comments; move the rest to "smaller things".

## Summary comment
1. **Verdict** first: approve, comment, or request changes (the user decides; never propose approve with a blocking finding).
2. **Top 3 to 5 points**, most important first, each one line with a pointer to the inline comment.
3. **What's good**, one or two lines.
4. **Smaller things**, a short bullet list of nits and non-blocking points that got no inline comment.

## Ticket comment
Per-requirement table, then follow-ups.

| Requirement | Status | Where |
|---|---|---|
| Paraphrased requirement | met / partly met / missing | `path/File.java:42`, or "not found" |

Follow-ups: things to do outside this PR (an upstream ticket needed, a backport to decide, a test or doc to add). If the user cannot post to that tracker, hand over the text and a link.

## Private note (never posted)
Short, for the user only:
- Things worth raising in person.
- Confidence per finding (high, medium, low) and what would settle the doubtful ones.
- Any exploitable issue in already-released code, or one the PR appears to quietly fix, with a suggestion to report it privately. This is the only place it appears. (Problems in the PR's own new code are normal findings.)
- Dismissed pitfalls script hits, each with a one-line reason.
- Anything skipped or unavailable (a sibling skill, CI logs, a ticket).

## Redaction rules
- No patient data, PHI or employee personal data, even as an example, in any draft. Use made-up values.
- Problems in the PR's own new code (for example a missing `@Authorized` the PR adds) are normal findings. An exploitable issue in already-released code, or a PR that appears to quietly fix one, is never described in any public draft (inline comments, summary, "what's good" praise, ticket comment), public or private repo.
- Check `gh repo view <o>/<r> --json visibility` first; if unknown, treat the repo as public. In public repos, paraphrase internal ticket content; do not quote it. No site names or internal discussion.
- Never mention the user's private notes or unverified issues.
- No personal criticism, and no names beyond the PR's own authors and handles already visible on the PR.

## Worked examples (made-up code)

**Blocking**
> **blocking** `ReportService.java:88`: this loads every visit for the location and then filters by date in Java. On a large site that is millions of rows in memory (C2, filtering in Java).
> Push the date range into the query:
> ```suggestion
>     criteria.add(Restrictions.between("startDatetime", from, to));
> ```

**Nit**
> **nit** `WidgetUtil.java:15`: `tmp` is a hard name to read later. Something like `activeWidgets` would say what it holds. Not a blocker.

**Requirement gap** (ticket comment row)

| Requirement | Status | Where |
|---|---|---|
| Show the last visit date on the Site Alpha dashboard | partly met | `dashboard.tsx:30` shows it, but voided visits are included (C1) |
| Hide the column for users without the view privilege | missing | no privilege check found |

Follow-up: add a test for the voided-visit case.
