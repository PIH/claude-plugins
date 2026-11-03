# Dates, locale and i18n (H1-H8)

Starred categories (★) recur across many years or many reviews. Read them first.

## H5 ★ Concept-name locale fallback
Code picks a concept name by hand (first name, `getName(locale)` only, `toLowerCase` comparisons), so some locales get no name, a null, or the wrong name.
- **While writing:** Use the existing Concept name APIs. The fallback order is: exact locale, same language, default locale, then any name. Never assume a name exists for the requested locale.
- **When reviewing:** `getNames().get(0)`, `getName(locale)` with the result used unchecked, hand-built locale matching, `preferredName` dereferenced without a null check.
- **Seen in:** TRUNK-3981, TRUNK-2682, TRUNK-6265, TRUNK-4982 (about 10 fixes, 2011-2024)
- **Module twist:** REST custom reps threw when a concept had no preferred name (RESTWS-466), and fhir2 had to switch to `getName()` (fhir2@21fe81db).

## H1 Lenient or asymmetric date parsing
Parsers accept malformed dates (lenient `SimpleDateFormat`), or the getter and setter use different formats, so values shift or round-trip wrongly.
- **While writing:** Parse strictly with `java.time`. Use one ISO format for both get and set.
- **When reviewing:** `new SimpleDateFormat(` with no `setLenient(false)`; different patterns on read and write.
- **Seen in:** TRUNK-6848, TRUNK-1958, TRUNK-4280
- **Module twist:** REST date handling was "not quite ISO 8601" and took several commits to fix (RESTWS-419).

## H2 Locale-dependent formatting of machine data
Numbers or dates meant for storage or parsing are formatted with the default locale, so a comma decimal separator or non-Latin digits corrupt them.
- **While writing:** Use `Locale.ROOT` or ISO formats for anything stored or parsed. Pin the locale in tests.
- **When reviewing:** `String.format` or `NumberFormat`/`DateFormat` without a locale on values that are later parsed; `toLowerCase()`/`toUpperCase()` without `Locale.ROOT` on identifiers.
- **Seen in:** TRUNK-2424, TRUNK-2580, TRUNK-5716
- **Module twist:** In reporting, renderers must write typed values (Number, Date) with explicit formats and UTF-8 output rather than locale-formatted strings (REPORT-249, REPORT-331).

## H3 Date-range boundaries, end of day, DB precision
Ranges include or exclude the wrong boundary, "end date" means midnight at the start of the day, or comparisons fail on sub-second or `Timestamp` differences.
- **While writing:** Use half-open ranges (start inclusive, end exclusive). A null end means open-ended. Assume second precision in the database. Never compare `Date.equals(Timestamp)`.
- **When reviewing:** `<=` on an end date, `setTime(0)` end-of-day hacks, equality on dates.
- **Seen in:** TRUNK-1158, TRUNK-3630, TRUNK-4569, TRUNK-4252
- **Module twist:** FHIR date search must widen month or year values to their range, but not hour or minute values to a whole day (FM2-146). Form checks must be relative to the encounter date and visit, not now (see K4).

## H4 Time of day and timezone leaking into age and date-only logic
Age, birthdate and other date-only values are computed from timestamps, so the time of day, a timezone or DST changes the answer.
- **While writing:** Use `LocalDate` and `Period` as of an explicit date, capped at the date of death. Never do day arithmetic with `/ 86400000`.
- **When reviewing:** `new Date()` in age code, `Calendar` arithmetic across DST, tests that only pass in one timezone.
- **Seen in:** TRUNK-879, TRUNK-89, TRUNK-843
- **Module twist:** Run tests under a non-UTC, DST-observing zone; unit tests that passed only at +0530 were a recurring find (RESTWS-270, fhir2@9de6c197). In O3, `new Date("YYYY-MM-DD")` is read as UTC while date pickers return local midnight; CI in UTC hides this. Age and day counts failed on DST days (RA-1986).

## H6 Locale identifiers and parsing
Locale strings are split by hand (`split("_")`), BCP-47 tags and legacy codes (he/iw) are mixed up, or a locale is matched exactly when language was meant.
- **While writing:** Use `LocaleUtility.fromSpecification` or `Locale.forLanguageTag`. Match by language where appropriate.
- **When reviewing:** `split("_")` on a locale, string comparison of locale codes, new `Locale(language)` constructors.
- **Seen in:** TRUNK-6181, TRUNK-6221, TRUNK-6341
- **Module twist:** REST reported the wrong locale for "he"; the first fix was reverted the same day (TRUNK-6181).

## H7 i18n message mistakes
Text is hard-coded, `MessageFormat` apostrophes eat placeholders, or a null locale reaches the message source.
- **While writing:** Put text behind message codes in `messages.properties`. Use `''` in messages that take arguments. Never pass a null locale.
- **When reviewing:** String literals shown to users; messages with `'` and `{0}`; `getMessage(code, args, null)`.
- **Seen in:** TRUNK-6816, TRUNK-4500, TRUNK-6478
- **Module twist:** REST returned validation messages uninterpolated and untranslated (RESTWS-1017, RESTWS-1002). In O3 use `t(key, default)`, extract keys, match the module namespace and keep a single i18next instance.

## H8 Client, server and service timezones across the UI
A date-only value or appointment time crosses a client/server boundary with an implicit timezone, so it shifts by a day or an hour on some screens, emails or conflict checks.
- **While writing:** Send and store date-only values as plain `LocalDate` strings, never converted. Send datetimes with an explicit offset. Compare availability in the service's own zone, and treat end-of-day as an exclusive next midnight.
- **When reviewing:** `new Date(` on a server string; client-timezone formatting applied to birthdate or onset; `DATE_FORMAT(...)` in SQL for display; `end > start` checks that fail for 11 PM to 12 AM; tests that call `TimeZone.setDefault` without restoring it.
- **Seen in:** RA-1678 (onset dates shifted), UIFR-220 (birthdates shifted by client-timezone conversion), BAH-3805 (false appointment conflicts), BAH-5291 (overnight appointment rejected)
- **Module twist:** In the 2.x UI the client-timezone feature touched 5 repos (UIFR-219, UICM-98). Server-side renderers (email, SQL dashboards) must use the same conversion as the UI (BAH-3063).
