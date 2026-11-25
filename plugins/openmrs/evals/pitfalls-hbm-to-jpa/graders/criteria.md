---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The `orderer` many-to-one has an explicit `fetch = FetchType.LAZY` (the hbm many-to-one has no lazy attribute, and the JPA default would be EAGER).
- The `attachments` set uses `cascade = CascadeType.ALL` together with `orphanRemoval = true` (or Hibernate `@Cascade(DELETE_ORPHAN)`). An answer that drops orphan deletion fails. The mapping also does not add orphan removal anywhere else (for example on the many-to-one).
- It mentions a test that saves, flushes, clears the session and reloads to verify the mapping behaves as before.
