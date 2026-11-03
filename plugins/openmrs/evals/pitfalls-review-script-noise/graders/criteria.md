---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It reports the A1 hit (editing a released changeSet) as a real finding in the review, grounded in the diff.
- It dismisses the D1 hit explicitly and gives a reason why it is a false positive for this diff.
- It does not list the D1 hit as a finding or ask for changes because of it.
