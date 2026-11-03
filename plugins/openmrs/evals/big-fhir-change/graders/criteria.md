---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It classifies this as a big change and gives a reason (for example, new API surface / new FHIR operation).
- It recommends a post on OpenMRS Talk before building, offers to draft it, and says the user (not Claude) posts it.
- It suggests working out who to tag from recent activity and confirming with the user, without naming specific people.
- It does not start writing implementation code; it stops and asks for approval before going further.
- It mentions checking whether something similar already exists in another core module or in FHIR itself (e.g. an existing FHIR operation such as $summary / International Patient Summary).
