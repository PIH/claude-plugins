---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The A1 hit (modified line inside a released changeSet) is reported as a real finding, grounded in the diff.
- The D1 hit is explicitly called a false positive (or is ignored), and the `NameFormatter` change is not listed as a required change or blocking issue. A non-blocking remark is fine.
