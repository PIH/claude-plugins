---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The changeset restates the column's data type (`columnDataType`) and keeps NOT NULL (`nullable="false"`) and the default value in the rename, or it adds an explicit follow-up that re-applies the constraint, so the rename does not silently drop them.
- It avoids reserved words in the new column or table naming, or explicitly checks `dx_rank` against reserved words.
- It adds a precondition (for example `columnExists` for the old column and `not columnExists` for the new one) so the changeset is safe to re-run.
