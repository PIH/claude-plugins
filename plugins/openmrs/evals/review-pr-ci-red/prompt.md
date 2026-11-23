---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this PR. The ticket is UHM-510 (PIH Jira), already confirmed by me to contain no patient data or PHI; its text: "Show the patient's age in the visit header." Note: gh, Jira and network tools are unavailable in this session, and no repository is checked out. Everything you need is pasted below as the provided data. Work from it and do not try to fetch anything.

PR: example-org/openmrs-module-example#91, "UHM-510: age in visit header". PIH module.

```diff
--- a/api/src/main/java/org/example/VisitHeaderBuilder.java
+++ b/api/src/main/java/org/example/VisitHeaderBuilder.java
@@ -20,0 +21,4 @@ public class VisitHeaderBuilder {
+    public String ageText(Patient patient) {
+        return patient.getAge() + " y";
+    }
```

Output of `gh pr checks 91`:

```
build        pass   2m10s
unit-tests   fail   4m02s
lint         pass   0m45s
```

Failed log excerpt of unit-tests:

```
[ERROR] Tests run: 12, Failures: 0, Errors: 1
[ERROR] VisitHeaderBuilderTest.shouldBuildHeaderForPatientWithoutBirthdate
java.lang.NullPointerException
    at org.example.VisitHeaderBuilder.ageText(VisitHeaderBuilder.java:22)
    at org.example.VisitHeaderBuilderTest.shouldBuildHeaderForPatientWithoutBirthdate(VisitHeaderBuilderTest.java:41)
```
