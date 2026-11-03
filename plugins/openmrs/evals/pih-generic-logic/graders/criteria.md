---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- Before building, it raises that this logic looks generic and may belong upstream rather than in pihcore.
- It names a plausible upstream home (a specific OpenMRS core module or openmrs-core) or explains how it would find one.
- It mentions the relevant FHIR resources (Immunization and/or ImmunizationRecommendation).
- It gives a recommendation (upstream, PIH-only, or PIH now with upstream later) with reasons.
- It ends by asking the user to choose, and does not post, file or open anything publicly.
