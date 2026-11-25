# Reporting (N1-N6)

Starred categories (★) recur across many years or many reviews. Read them first. Covers reporting, reportingrest, reportingui, calculation and serialization.xstream.

## N2 ★ Serialized-definition compatibility: class shape is the storage schema
Report, cohort and dataset definitions are stored as XStream XML of the Java object graph. Removing or renaming a field, making an inner class static, changing proxy class names, or changing how metadata references are written breaks definitions already in the database. These refactors look harmless and pass tests that use freshly created objects.
- **While writing:** Treat every field on a persisted Definition, Mapped, Parameter or converter class as a database column. Keep removed fields (or alias or omit them in the serializer), keep class names and nesting stable, and test with XML fixtures from the previous release.
- **When reviewing:** Removed or renamed fields, `static` added to an inner class, package moves in `*Definition`, `*Query`, `Mapped` or `SortCriteria` classes; string matching on proxy class names; serializer changes with no "deserialize old XML" test.
- **Seen in:** REPORT-423 (an unused logger field removed, old definitions would not load), REPORT-468 / REPORT-854 (static inner class, reverted both times), SXS-7 / SXS-24 / SXS-30 (proxy detection by class-name string broke with each Hibernate upgrade)

## N5 ★ Parameter values lost or mis-coerced across nested definitions and transports
Parameter values must survive several hops: HTTP form or REST body, `EvaluationContext`, `Mapped` mappings into child definitions, and SQL or HQL binding. Collections get reduced to their first element, null and empty are conflated, typed values are not coerced, and evaluators that build a new context drop the parent's parameters. The result is wrong data, not an error.
- **While writing:** When an evaluator creates a child `EvaluationContext`, copy the parent (`shallowCopy`), not `new`. Keep null (ignore) and empty (match nothing) collections distinct end to end. Convert values using the declared `Parameter` type and collection type. Test every hop.
- **When reviewing:** `new EvaluationContext()` inside evaluators; `parameterValues[0]`; `request.getParameter` where `getParameterValues` is needed; REST converters that default a missing value to an empty collection.
- **Seen in:** REPORT-229 / REPORT-821 (evaluators dropped context parameters), REPORT-223 / REPORT-878 (multi-valued parameters reduced to the first), REPORT-835 (REST turned a missing Collection into an empty one), REPORT-819 (Location uuid not resolved)

## N1 Evaluated-result cache key omits what the result depends on
Definitions are cached per evaluation, keyed by configuration properties. Results also depend on parameter values, the base cohort and delegate parameters; when those are missing from the key a later indicator silently reuses an earlier result.
- **While writing:** Put `@Caching` only on definitions whose result is a pure function of the key. Include parameter values in the key for any parameterized or SQL or script definition. Never cache delegating wrappers.
- **When reviewing:** A new `*Definition` with `@Caching(strategy=ConfigurationPropertyCachingStrategy.class)` that has parameters, script or SQL text, or delegates; `EvaluationContext` copy changes that touch `baseCohort` or the cache.
- **Seen in:** REPORT-519 (same SQL cohort with different parameters returned the first result), REPORT-603 (wrapper cached though the delegate had extra parameters), REPORT-503

## N3 Large-cohort ID constraints: IN-lists, temp tables
Constraining queries to a base cohort with `in (:ids)` broke or slowed on large cohorts. Each workaround (batching, a temp `reporting_idset` table, cross joins) brought its own regression (deadlocks, a switch GP, slower small reports) and the temp table was finally removed.
- **While writing:** Build ID constraints through `HqlQueryBuilder.wherePersonIn` or `whereIdIn` and the `EvaluationService`, not by hand. Benchmark with at least 100k ids on the oldest supported MySQL, and with two evaluations running at once.
- **When reviewing:** `in (:ids)` with an unbounded collection; new shared tables written during evaluation; global batch-size changes with no profile at small and large sizes.
- **Seen in:** REPORT-623 (stack overflow in the Hibernate parser from long IN lists), REPORT-674 (deadlocks from the idset table), REPORT-551 (batching turned off by default after it got slower)

## N4 Hot-loop GP, message and style lookups during evaluation and rendering
Code that is cheap once (reading a global property, finding a message source, creating a POI cell style, formatting an object) runs once per cell or per patient and then dominates runtime or hits hard limits.
- **While writing:** Hoist GP, locale, message-source and style lookups out of row and cell loops and cache them per evaluation or render. Reuse POI styles keyed by format.
- **When reviewing:** `getGlobalProperty`, `Context.getMessageSourceService()`, `createCellStyle` or formatter construction inside a row or column loop or per-value renderer method.
- **Seen in:** REPORT-631 (batch-size GP read took 46% of report time), REPORT-578 (default locale fetched thousands of times in Excel export), REPORT-608 (one cell style per cell exceeded the 4000-style limit)

## N6 Rendering fidelity, and stored SQL sandboxed by keyword denylist
Renderers cast values to an output format and lose type, format or encoding: numbers become text, template date formats are lost, CSV ignores quoting, output is not UTF-8. Separately, admin-authored SQL and scripts run with the server's DB rights, guarded only by a keyword word list.
- **While writing:** Render from typed values (Number, Date, Boolean) with explicit formats, never through `toString` or the user's locale. Write bytes with an explicit charset and test the produced file. Bind values as JDBC parameters, run stored user SQL on a read-only connection or user, and document that SQL definitions must filter voided rows themselves.
- **When reviewing:** `setCellValue(String.valueOf(..))`; `PrintWriter` or `FileWriter` with no charset; hand-built CSV joins; filenames built with `split(".")`; concatenated `EvaluationContext` values in SQL; edits to `isSelectQuery`; new definition types that execute stored text.
- **Seen in:** REPORT-331 (numbers written as text into Excel), REPORT-592 (CSV renderer broke the standard), REPORT-248 (denylist matched only spaces), REPORT-881 (context values spliced into `set @x=` unescaped)
