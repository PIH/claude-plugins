---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- It flags that after the POST succeeds the component never revalidates the allergies SWR key (no `mutate`), so the allergies widget that reads `useSWR(allergiesUrl)` stays stale.
- It suggests calling `mutate` for that key, ideally via a shared key builder or key-matching `mutate` so the widget and workspace cannot drift apart.
- It also recommends disabling the Save button while the request is in flight, to prevent double submission.
