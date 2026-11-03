---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The code strictly rejects invalid dates: it uses `java.time` with `ResolverStyle.STRICT` (for example `DateTimeFormatter.ofPattern("uuuuMMdd").withResolverStyle(ResolverStyle.STRICT)`) or `SimpleDateFormat` with `setLenient(false)`, and with the latter it also checks the whole input was consumed (for example via `ParsePosition`).
- It uses a fixed, explicit format that does not depend on the default locale (any time zone used is explicit) (it does not use `DateFormat.getDateInstance()` or a default-locale formatter).
