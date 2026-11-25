---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Convert this hbm mapping fragment to JPA annotations on the `Order` class, preserving behavior exactly.

```xml
<many-to-one name="orderer" class="Provider" column="orderer" not-null="true"/>
<set name="attachments" inverse="true" cascade="all-delete-orphan">
    <key column="order_id"/>
    <one-to-many class="OrderAttachment"/>
</set>
```

Show the annotated fields.
