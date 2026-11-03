---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this PR. The PIH ticket UHM-560 (\"Require a reason when discontinuing a medication order\") is confirmed by me to contain no patient data or PHI. Note: gh, Jira and network tools are unavailable in this session, and no repository is checked out. Everything you need is pasted below as the provided data. Work from it and do not try to fetch anything.

PR: example-org/openmrs-module-example#96, \"UHM-560: discontinue reason\". PIH module, CI green.

```diff
--- a/api/src/main/java/org/example/DiscontinueValidator.java
+++ b/api/src/main/java/org/example/DiscontinueValidator.java
@@ -10,0 +11,4 @@ public class DiscontinueValidator implements Validator {
+        if (order.getOrderReason() == null) {
+            errors.rejectValue(\"orderReason\", \"discontinue.reason.required\");
+        }
+        System.out.println(\"validated \" + order.getOrderId());
```

The PR adds no test and no message property for \"discontinue.reason.required\".
