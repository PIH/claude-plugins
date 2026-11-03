---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It treats the repository as openmrs-core (a core/platform repo with its stricter compatibility rules).
- It flags that changing the return type of a public service method is a breaking API change for modules and other callers.
- It proposes keeping the old method (deprecated) and adding a new overload or differently named method for the new return type.
- The breaking change is marked as blocking or must-fix.
