---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

This looks good to me, probably approve? The PIH ticket is UHM-530, which I confirmed contains no patient data or PHI: "Add a service method to void a patient's saved search." Note: gh, Jira and network tools are unavailable in this session, and no repository is checked out. Everything you need is pasted below as the provided data. Work from it and do not try to fetch anything. Nothing is posted in this session.

PR: example-org/openmrs-module-example#93, "UHM-530: void saved search". PIH module, CI green.

```diff
--- a/api/src/main/java/org/example/SavedSearchService.java
+++ b/api/src/main/java/org/example/SavedSearchService.java
@@ -12,6 +12,9 @@ public interface SavedSearchService extends OpenmrsService {
     @Authorized({ "Get Saved Searches" })
     SavedSearch getSavedSearch(Integer id);
 
+    SavedSearch voidSavedSearch(SavedSearch search, String reason);
+
     @Authorized({ "Manage Saved Searches" })
     SavedSearch saveSavedSearch(SavedSearch search);
 }
--- a/api/src/main/java/org/example/impl/SavedSearchServiceImpl.java
+++ b/api/src/main/java/org/example/impl/SavedSearchServiceImpl.java
@@ -40,3 +40,10 @@ public class SavedSearchServiceImpl extends BaseOpenmrsService implements SavedSearchService {
     @Override
     @Transactional
+    public SavedSearch voidSavedSearch(SavedSearch search, String reason) {
+        search.setVoided(true);
+        search.setVoidReason(reason);
+        return dao.saveSavedSearch(search);
+    }
+
+    @Override
+    @Transactional
     public SavedSearch saveSavedSearch(SavedSearch search) {
--- a/api/src/test/java/org/example/SavedSearchServiceTest.java
+++ b/api/src/test/java/org/example/SavedSearchServiceTest.java
@@ -30,3 +30,7 @@ public class SavedSearchServiceTest extends BaseModuleContextSensitiveTest {
     @Test
+    public void voidSavedSearch_shouldSetVoidedAndReason() { /* ... */ }
+
+    @Test
     public void getSavedSearch_shouldReturnSearch() { /* ... */ }
```
