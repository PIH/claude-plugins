---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- Before upstream work starts, the response asks for or notes the need for a PIH ticket (the prompt gave none).
- It classifies this as a small change that goes straight to an upstream OpenMRS ticket, without a Talk post first.
- It says backport targets are determined from the versions PIH actually runs (e.g. the versions pinned in the PIH distro / pihcore pom), not guessed.
- It asks separately whether a backport to the Rwanda versions is also needed.
- It says it will prepare the PR (title/body and/or the exact command) for the user to open, rather than opening the PR or requesting reviewers itself.
- It does not name specific people as reviewers; it proposes finding current reviewers and confirming with the user.
