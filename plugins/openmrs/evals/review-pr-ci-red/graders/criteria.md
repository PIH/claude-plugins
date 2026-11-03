---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The summary reports that CI is red (the unit-tests check failed).
- It gives the probable cause from the log: a NullPointerException in ageText in the test shouldBuildHeaderForPatientWithoutBirthdate. Naming the missing birthdate as the cause (an inference) is fine but not required.
- It does not offer or suggest checking out the PR or running the build locally (saying that is unnecessary is fine).
