---
name: pitfalls
description: Use when writing, changing or reviewing code in openmrs-core, any OpenMRS module (backend omod or @openmrs/esm-* O3 frontend app) or a Bahmni core module, and when reviewing a PR or diff in those repos. Triggers include a Liquibase changeset or changelog, a Hibernate mapping (hbm.xml or JPA annotations), a DAO or HQL/Criteria query, a service method, a REST resource, a FHIR translator, an HTML Form Entry tag, a report definition, an Initializer domain, an O3 config schema or workspace, date parsing, and lazy-loading errors.
---

# OpenMRS pitfalls

OpenMRS has made the same code mistakes for years: released changesets edited, voided children leaking into searches, services that fail open, eager "fixes" for lazy-loading errors. This skill lists those mistakes by category id (A1..P9) so you avoid them when writing and catch them when reviewing.

## Write mode

Before writing, find the change type in the area table below and read that area file in `references/`. Follow its "While writing" rules. The always rules and the area table's one-line summary apply even if you can't open the file.

When asked for code, write the code, with its tests, applying these rules. Put process questions (an existing method, a Talk post, a ticket) in a short note after the code, not in place of it.

## Review mode

1. Run the review script on the diff: `git diff <base>...HEAD | python3 <skill dir>/scripts/review_diff.py` (or `--repo PATH --base REF`; `--json` for machine output). Each line is `path:line  <ID>  <confidence>  <message>`. It's advisory and never blocks.
2. Read every area file the diff touches.
3. Check each changed hunk against that area's "When reviewing" rules and the always rules below.
4. Report each finding with its category id, why it matters, and the fix. Cite a public ticket where it helps. Mark each finding blocking or non-blocking. A missing test for a small defensive change (a null guard, a trim) is non-blocking.
5. Script hits are hints, not findings. Confirm each one against the diff. Low-confidence hits are prompts to look, not findings. For each hit you dismiss, say so in one line with the reason (for example "D1 at Foo.java:21: false positive, the hunk never touches compareTo"). Code that only a dismissed hit pointed at gets at most a non-blocking remark, never a required change.

Never post review comments on your own: draft them, list the planned actions, and post only what the user approves (see `contributing`, 'Public steps').

## Always rules

1. **A1** Never edit a changeSet that has shipped in a release: installs that already ran it fail checksum validation on startup. Add a new changeSet instead. `validCheckSum` is a deliberate, justified exception only.
2. **A3** Backfill or handle existing rows (an `<update>` or `<sql>` in the same changeSet) before adding NOT NULL, FK or unique constraints. Every DDL changeSet gets `<preConditions onFail="MARK_RAN">` (A2), for a rename both `columnExists` old and `not columnExists` new.
3. **A5** Portable SQL for MySQL, MariaDB and PostgreSQL, and no reserved words as names (`rank`, `order`, `key`, `user` are reserved in MySQL 8 or PostgreSQL). Say so when a rename moves off a reserved word.
4. **B1** Set `fetch = FetchType.LAZY` explicitly on every `@ManyToOne`/`@OneToOne` (the JPA default is EAGER; hbm many-to-one was lazy). In an hbm-to-JPA migration copy cascade exactly: `all-delete-orphan` becomes `CascadeType.ALL` + `orphanRemoval = true`, and add orphan removal nowhere else.
5. **B3** Never fix a LazyInitializationException with `FetchType.EAGER`, `lazy="false"` or a static cache: every load of the entity then pays for the association, including callers that never use it. Initialize it inside the transaction (service method) or use a fetch join.
6. **C1** Filter voided/retired on every joined `Voidable`/`Retireable` child, not just the root (for example `p.voided = false and pi.voided = false`). Test with a voided child that matches and expect the parent not to be returned.
7. **C2** Filter, count and page in the database query, not with Java streams over `getAll...()`.
8. **F1** Don't break public API: Java signatures, REST/FHIR shapes, schema, GP defaults, extension points and config schemas. Deprecate and add instead (process is in `contributing`).
9. **F5** A dependency or framework upgrade (including hbm-to-JPA, Spring, Hibernate) must preserve implicit behavior: defaults, cascade, fetch, ordering, null handling.
10. **G1** Every public service interface method gets `@Authorized`. Copy the privilege list of its sibling methods on that entity unchanged (a new getter uses what the other getters use) (G2). Without it the method fails open.
11. **G10** Escape at output for the context it lands in (HTML, attribute, JS, URL), not on input or storage.
12. **I1** Every fix or feature has a test at the layer where the bug appears that fails before and passes after. Persistence and mapping tests save, `flush()`, `clear()` and reload (B7). Service methods get a test that authenticates as a user who lacks the required privilege (logging out is not enough) and expects `APIAuthenticationException`. Never `@Ignore` or skip tests to get green.

## Area table

| Change type (path or content signal) | Read | Key rules in one line |
|---|---|---|
| `liquibase*.xml`, `<changeSet>`, `addColumn`, `renameColumn`, `modifyDataType` | liquibase.md (A1-A9) | `renameColumn`/`modifyDataType` on MySQL drop NOT NULL, defaults and FKs (A4): give `columnDataType` and re-add them with `addNotNullConstraint` + `addDefaultValue`; preconditions on every changeSet (A2) |
| `@Entity`, `@ManyToOne`, `@OneToMany`, `*.hbm.xml`, `equals`/`hashCode`/`compareTo`, `merge`/`evict`/`saveOrUpdate` | hibernate.md (B1-B7, D1) | Explicit LAZY, exact cascade copy, don't replace managed collections, flush+clear+reload in tests |
| `*DAO*`, HQL, Criteria, `createQuery`, caches, loops over entities | queries-performance.md (C1-C6) | Voided filter on joined children, filter in SQL, no `lower()` on indexed columns, no N+1 |
| Spring config, AOP, `moduleApplicationContext.xml`, activators, `config.xml` version ranges, threads, singletons | lifecycle-crosscutting.md (E1-E5, O1) | Don't change global persistence or AOP behavior; respect module load order and version ranges |
| A `*Service` interface, public API, exceptions, validators, GP defaults, dependency upgrades, refactors, tests, backports | api-compat-upgrades.md (F1-F6, I1-I2) + security.md | No breaking signatures, no stricter validation on existing data, upgrades keep behavior, failing-then-passing test |
| `@Authorized`, privileges, file paths, uploads, XML/XStream parsing, templates, SQL strings, sessions, output escaping | security.md (G1-G11) | `@Authorized` matching siblings, canonical-path containment, no string-built SQL, no Velocity/SpEL on stored text |
| `Date`, `SimpleDateFormat`, `java.time`, timezones, age, locales, messages, concept names | dates-locale.md (H1-H8) | Parse with a strict `java.time` formatter, not lenient `SimpleDateFormat` or a hand-rolled regex: for `yyyyMMdd` (HL7 DT) use `LocalDate.parse(s, DateTimeFormatter.BASIC_ISO_DATE)`, or `ofPattern("uuuuMMdd", Locale.ROOT).withResolverStyle(ResolverStyle.STRICT)` (`uuuu`, not `yyyy`); never the default locale; `19800231` must be rejected, not rolled to March |
| REST resources, representations, search handlers, FHIR translators and search params | rest-fhir.md (J1-J8) | Authorize every rep path, go through services, keep FHIR null vs absent semantics, never ignore a search param |
| HTML Form Entry tags and handlers, O3 form engine, obs groups, form edit | forms.md (K1-K9) | Edit round-trip is lossless, encounter date not "now", obs-group matching is heuristic |
| Initializer domains, metadata deploy, CSV/JSON loaders, OCL import | metadata-loading.md (L1-L5) | Keep retired state on re-import; absent vs empty differ; don't resolve by non-unique names |
| Encounters, visits, orders, programs, ADT, status changes, events, module privileges | clinical-workflow.md (M1-M6) | Cascade workflow entities from the parent; changing encounter date or visit propagates to children |
| Reporting module, report/cohort/data definitions, evaluators, renderers | reporting.md (N1-N6) | Serialized definitions are a storage schema; parameters survive nesting; cache keys include all inputs |
| `@openmrs/esm-*`, `*.tsx`, `useSWR`, `openmrsFetch`, workspaces, config schema, extensions, slots | o3-frontend.md (P1-P9) | After a write, `mutate` the SWR keys other widgets read (shared key builder); disable submit while in flight; no logic on `t()` text; config/slot names are contracts |

## Relationship to `contributing`

`contributing` covers process: where the change belongs, tickets, Talk, breaking-change approval, backports and releases. This skill covers whether the code itself is correct. Where they overlap (F1 breaking changes, F3 changed defaults, I2 backports) follow `contributing` for the process and use this skill only for the code check.
