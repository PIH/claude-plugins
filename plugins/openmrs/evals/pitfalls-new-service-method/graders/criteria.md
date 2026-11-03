---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The new `getAllergiesByUuid` method on `PatientService` is annotated `@Authorized({PrivilegeConstants.GET_ALLERGIES})`, the same privilege as the sibling getters shown in the prompt (`getAllergies`, `getAllergy`).
- It adds a test that a user without that privilege is denied (an `APIAuthenticationException` is expected).
