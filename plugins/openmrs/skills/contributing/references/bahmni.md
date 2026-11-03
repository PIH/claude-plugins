# Bahmni-owned core modules

Some core modules belong to Bahmni, not OpenMRS. You can identify them by Maven groupId `org.bahmni.module` (the distro files show it as `omod.<name>.groupId=org.bahmni.module`) or by GitHub owner `Bahmni`. Check these live rather than from memory. At the time of writing they are `appointments` and `teleconsultation`.

The core design rules apply to them unchanged: keep changes generic, base them on FHIR, avoid breaking changes, and check for existing work first. What differs is the process:

| | OpenMRS-owned | Bahmni-owned |
|---|---|---|
| Upstream ticket | OpenMRS Jira (TRUNK, O3, …) | **BAH** ticket in Bahmni's Jira (bahmni.atlassian.net, which needs a separate account). GitHub Issues is switched on in the repos but is effectively unused and unwatched, so don't rely on it. |
| PR title | `TRUNK-1234: description` | Usually `BAH-1234 \| Fix. description`. Check recent merged PRs for the current form. |
| First PR | — | CLA Assistant asks the contributor to sign a Contributor License Agreement. |
| Discussion | OpenMRS Talk | OpenMRS Talk, Bahmni category, tagging the Bahmni core team (suggest names from recent activity and confirm with the user). |
| Reviewers / mergers | OpenMRS reviewers | Almost entirely the Bahmni team. Check recent merged PRs. |
| Review speed | Varies | PRs from outside the Bahmni team often wait months. Flag this early so the PIH ticket can plan around it. |
| Release | A PIH developer may cut one (Claude prepares the steps; the user approves Claude running them, or runs them) | Only Bahmni can release, through their GitHub workflow. PIH has to ask them. |
| Backports | Maintenance branches PIH runs | Effectively master only. A backport needs Bahmni's agreement. |

If the user can't create a BAH ticket, the fallback is a Talk post in the Bahmni category asking for one (Claude drafts it; the user posts it, since Claude has no Talk access). Don't fall back to a GitHub issue.

When PIH work depends on a change to a Bahmni module, say early that the timeline depends on Bahmni's review and release. That way the PIH ticket can plan for waiting or for an interim PIH-side approach.
