---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Please review this diff to openmrs-core before I merge it.

```diff
--- a/api/src/main/resources/liquibase-update-to-latest-2.4.x.xml
+++ b/api/src/main/resources/liquibase-update-to-latest-2.4.x.xml
@@ -812,7 +812,7 @@
     <changeSet id="20210311-1200-add-encounter-diagnosis-rank" author="dev">
         <preConditions onFail="MARK_RAN">
             <not><columnExists tableName="encounter_diagnosis" columnName="rank"/></not>
         </preConditions>
         <addColumn tableName="encounter_diagnosis">
-            <column name="rank" type="int"/>
+            <column name="rank" type="int" defaultValueNumeric="0"/>
         </addColumn>
     </changeSet>
```

This changeSet shipped in the 2.4.0 release. I just want the new column to default to 0.
