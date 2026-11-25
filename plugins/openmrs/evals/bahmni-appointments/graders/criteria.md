---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It identifies the appointments module as owned by Bahmni rather than OpenMRS.
- It recommends a BAH ticket in Bahmni's Jira instead of a GitHub issue, noting GitHub Issues there are effectively unused.
- It mentions the Contributor License Agreement (CLA) for a first PR to a Bahmni repo.
- It warns that review of outside PRs can be slow and that only Bahmni can release the module, so PIH should plan around that.
- It still applies the shared-code rules in substance: it considers the impact on other implementations or existing clients (keeping the change generic / non-breaking), whether or not it uses those exact words.
