---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It asks the user which repository the PR is in, or for a PR link or an owner/repo#N reference.
- It does not invent or assume a repository, and it does not present review findings about the PR's code.
