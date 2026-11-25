---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

This is a bug fix for a LazyInitializationException reported when the REST layer reads `encounter.getVisit().getLocation()` after the session is closed. Please review.

```diff
--- a/api/src/main/java/org/openmrs/Encounter.java
+++ b/api/src/main/java/org/openmrs/Encounter.java
@@ -85,7 +85,7 @@ public class Encounter extends BaseChangeableOpenmrsData {
-	@ManyToOne(fetch = FetchType.LAZY)
+	@ManyToOne(fetch = FetchType.EAGER)
 	@JoinColumn(name = "visit_id")
 	private Visit visit;
```

Approve, or request changes?
