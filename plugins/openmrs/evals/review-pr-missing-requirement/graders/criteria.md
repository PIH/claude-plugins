---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It marks requirement 3 (localized error message in en and fr) as not met or only partly met, naming the missing messages (no message properties or translations added for the new error codes).
- It marks requirements 1 and 2 as met.
- Its PR review summary mentions the missing localization as a blocking issue (or as needing changes before merge).
- It drafts a ticket comment that marks requirement 3 as not met or partly met.
