---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this PR. It has no PIH ticket; the upstream ticket is TRUNK-9999, and I confirm the ticket contains no patient data or PHI. Its text: "PatientService.getPatientsByName should tell callers when results were truncated." Note: gh, Jira and network tools are unavailable in this session, and no repository is checked out. Everything you need is pasted below as the provided data. Work from it and do not try to fetch anything.

PR: openmrs/openmrs-core#7777, "TRUNK-9999: return a result object from getPatientsByName". Author is an outside contributor. CI green.

```diff
--- a/api/src/main/java/org/openmrs/api/PatientService.java
+++ b/api/src/main/java/org/openmrs/api/PatientService.java
@@ -200,3 +200,3 @@ public interface PatientService extends OpenmrsService {
 	@Authorized({ PrivilegeConstants.GET_PATIENTS })
-	public List<Patient> getPatientsByName(String name) throws APIException;
+	public PatientSearchResult getPatientsByName(String name) throws APIException;
--- a/api/src/main/java/org/openmrs/api/impl/PatientServiceImpl.java
+++ b/api/src/main/java/org/openmrs/api/impl/PatientServiceImpl.java
@@ -400,4 +400,4 @@ public class PatientServiceImpl extends BaseOpenmrsService implements PatientSer
 	@Override
-	public List<Patient> getPatientsByName(String name) throws APIException {
-		return dao.getPatients(name, 0, null);
+	public PatientSearchResult getPatientsByName(String name) throws APIException {
+		return new PatientSearchResult(dao.getPatients(name, 0, null));
 	}
```
