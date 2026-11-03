---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The annotation mapping uses an explicit `fetch = FetchType.LAZY` on the `@ManyToOne`, because the hbm default for many-to-one is not the same as the JPA default (EAGER).
- It keeps the cascade exactly as the hbm declares it (`all-delete-orphan` becomes `CascadeType.ALL` with the equivalent orphan handling) and does not add `orphanRemoval` beyond what the hbm had, or it explicitly explains that the mapping is equivalent.
- It mentions a test that saves, flushes, clears the session and reloads to verify the mapping behaves as before.
