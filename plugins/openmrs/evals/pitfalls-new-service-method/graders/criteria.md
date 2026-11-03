---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The new `getAllergiesByUuid` method on `PatientService` is annotated with `@Authorized` using the same privilege as the sibling getter methods (for example the view-patients privilege constant), not a different or missing one.
- It adds a test that a user without that privilege is denied (an `APIAuthenticationException` is expected).
