---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this diff. The pitfalls review script was already run on it; its raw output is below. The changeSet in the first file shipped in the 2.4.0 release. Treat the script output as unverified hints: confirm each hit against the diff yourself.

```diff
--- a/api/src/main/resources/liquibase-update-to-latest-2.4.x.xml
+++ b/api/src/main/resources/liquibase-update-to-latest-2.4.x.xml
@@ -900,7 +900,7 @@
     <changeSet id="20200514-1030-add-visit-attribute-type-index" author="dev">
-        <createIndex tableName="visit_attribute_type" indexName="visit_attribute_type_name_idx">
+        <createIndex tableName="visit_attribute_type" indexName="visit_attribute_type_name_idx" unique="false">
             <column name="name"/>
         </createIndex>
     </changeSet>
--- a/api/src/main/java/org/openmrs/util/NameFormatter.java
+++ b/api/src/main/java/org/openmrs/util/NameFormatter.java
@@ -20,3 +20,3 @@
-	return name.trim();
+	return name == null ? "" : name.trim();
```

Script output:

```
api/src/main/resources/liquibase-update-to-latest-2.4.x.xml:900  A1  high  modified line inside an existing changeSet (id=20200514-1030-add-visit-attribute-type-index)
api/src/main/java/org/openmrs/util/NameFormatter.java:21  D1  low  possible reserved-word or ambiguous identifier near ternary
```
