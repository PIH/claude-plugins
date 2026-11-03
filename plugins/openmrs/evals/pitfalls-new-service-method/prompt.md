---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Add `getAllergiesByUuid(String uuid)` to `PatientService` in openmrs-core, with its `PatientServiceImpl` implementation, following the existing allergy getters. Show the code and the tests.

Existing declarations in `PatientService`:

```java
@Authorized({ PrivilegeConstants.GET_ALLERGIES })
Allergies getAllergies(Patient patient);

@Authorized( { PrivilegeConstants.GET_ALLERGIES })
public Allergy getAllergy(Integer allergyListId) throws APIException;

@Authorized({ PrivilegeConstants.ADD_ALLERGIES, PrivilegeConstants.EDIT_ALLERGIES })
Allergies setAllergies(Patient patient, Allergies allergies);
```
