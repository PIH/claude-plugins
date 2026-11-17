---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this PR against its PIH ticket. I have already confirmed the ticket text below contains no patient data or PHI. Note: gh, Jira and network tools are unavailable in this session, and no repository is checked out. Everything you need is pasted below as the provided data. Work from it and do not try to fetch anything. Nothing will be posted in this session; I want your drafted review: the PR review summary and a comment for the ticket.

Ticket UHM-456 (PIH Jira): "Validate referral form"
Requirements:
1. The referral form must require a referral reason.
2. The referral reason must be at most 500 characters.
3. When the reason is invalid, the user must see a localized error message (en and fr).

PR: example-org/openmrs-module-example#88, "UHM-456: validate referral form". Repo is a PIH module, CI green.

```diff
--- a/api/src/main/java/org/example/ReferralValidator.java
+++ b/api/src/main/java/org/example/ReferralValidator.java
@@ -12,6 +12,12 @@ public class ReferralValidator implements Validator {
     public void validate(Object target, Errors errors) {
         Referral referral = (Referral) target;
+        if (StringUtils.isBlank(referral.getReason())) {
+            errors.rejectValue("reason", "referral.reason.required");
+        } else if (referral.getReason().length() > 500) {
+            errors.rejectValue("reason", "referral.reason.tooLong");
+        }
     }
 }
--- a/api/src/test/java/org/example/ReferralValidatorTest.java
+++ b/api/src/test/java/org/example/ReferralValidatorTest.java
@@ -20,0 +21,12 @@ public class ReferralValidatorTest {
+    @Test
+    public void shouldRejectBlankReason() { /* ... */ }
+    @Test
+    public void shouldRejectReasonOver500() { /* ... */ }
```

No message properties files are touched by this PR.
