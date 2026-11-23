---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It marks thread 1 (null quantity check) as addressed.
- It marks thread 2 (missing message for order.qty.bad) as addressed.
- It marks thread 3 (test for quantity of zero) as not addressed, naming it (the missing test).
- It reviews only the new changes since the last review rather than re-reviewing the whole PR from scratch.
- It drafts a short follow-up comment or review note and does not claim to have posted it.
