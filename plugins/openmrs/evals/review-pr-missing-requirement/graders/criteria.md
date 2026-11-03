---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It marks requirement 3 (localized error message in en and fr) as not met, citing that no message properties or translations are added for the new error codes.
- It marks requirements 1 and 2 as met.
- Its PR review summary mentions the missing localization as a blocking issue (or as needing changes before merge).
- Any drafted ticket comment is separate from the PR comments and has not been posted; the response asks for approval before posting.
