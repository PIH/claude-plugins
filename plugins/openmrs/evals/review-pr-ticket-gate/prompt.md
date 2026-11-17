---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Please review this PR against its ticket, UHM-456. The ticket text lives in Jira and is available for you to read if you need it (assume the Jira read would work in a real session). The PR metadata and diff are pasted below because gh and the network are unavailable here. In this session just tell me what you would do next and ask me whatever you need before doing it.

PR: example-org/openmrs-module-example#88, "UHM-456: add visit note length validation"
Author: a colleague. Base: master. Repo is a PIH module, CI is green.

```diff
--- a/api/src/main/java/org/example/VisitNoteValidator.java
+++ b/api/src/main/java/org/example/VisitNoteValidator.java
@@ -10,6 +10,10 @@ public class VisitNoteValidator implements Validator {
     public void validate(Object target, Errors errors) {
         VisitNote note = (VisitNote) target;
+        if (note.getText() != null && note.getText().length() > 1000) {
+            errors.rejectValue("text", "visitnote.text.tooLong");
+        }
     }
 }
```
