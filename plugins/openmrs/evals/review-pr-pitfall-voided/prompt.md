---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this PR. The PIH ticket is UHM-500 and I have already confirmed it contains no patient data or PHI. Its text: "Add a search for patients by a fragment of any identifier, used by the clinic's lookup screen." Note: gh, Jira and network tools are unavailable in this session, and no repository is checked out. Everything you need is pasted below as the provided data. Work from it and do not try to fetch anything.

PR: example-org/openmrs-module-example#90, "UHM-500: identifier fragment search". PIH module, CI green.

```diff
--- a/api/src/main/java/org/example/db/HibernateLookupDAO.java
+++ b/api/src/main/java/org/example/db/HibernateLookupDAO.java
@@ -30,0 +31,9 @@ public class HibernateLookupDAO implements LookupDAO {
+    public List<Patient> findByIdentifierFragment(String fragment) {
+        return sessionFactory.getCurrentSession().createQuery(
+            "select distinct p from Patient p join p.identifiers pi " +
+            "where p.voided = false and pi.identifier like :frag", Patient.class)
+            .setParameter("frag", "%" + fragment + "%")
+            .list();
+    }
```
