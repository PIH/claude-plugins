---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Add a Liquibase changeset to openmrs-core that renames `encounter_diagnosis.rank` to `dx_rank`. The existing column is `int NOT NULL DEFAULT 0`. Show me the changeset XML.
