---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The summary reports that CI is red (the unit-tests check failed).
- It gives the probable cause from the log: a NullPointerException in ageText when the patient has no birthdate (patient.getAge() on a missing birthdate), in the named test shouldBuildHeaderForPatientWithoutBirthdate.
- It does not propose checking out the PR locally or running the build locally as a needed step, since the log already explains the failure.
