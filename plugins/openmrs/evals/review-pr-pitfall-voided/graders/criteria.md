---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It gives an inline comment on the HQL query (the join or where clause line) saying the identifier join has no voided filter, so a voided identifier can still match and return the patient (pitfall C1, voided child).
- The comment proposes a fix such as adding pi.voided = false.
- The comment is marked as blocking (or as must-fix) rather than a nit.
