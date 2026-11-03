---
type: llm
weight: 1
---

The response passes only if all of the following hold:

- The code parses strictly using one of: `LocalDate.parse` with `DateTimeFormatter.BASIC_ISO_DATE`; or `DateTimeFormatter.ofPattern("uuuuMMdd")` with `ResolverStyle.STRICT` (a `yyyy` pattern with STRICT and no era is wrong); or `SimpleDateFormat` with `setLenient(false)`, an explicit `Locale.ROOT` or `Locale.ENGLISH`, and a `ParsePosition` check that the whole input was consumed.
- The input `19800231` is rejected (an exception or null/error result), not rolled over to March.
- The format is fixed in the code and no default locale is used.
