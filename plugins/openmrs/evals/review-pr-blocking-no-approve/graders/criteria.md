---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It does not propose APPROVE (it may say explicitly that approval is not appropriate yet).
- It identifies the missing @Authorized annotation on the new service method as a blocking issue, with a short explanation.
- It proposes requesting changes (or at most a plain comment) as the review action instead.
