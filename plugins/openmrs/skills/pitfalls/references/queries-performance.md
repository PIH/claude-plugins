# Query correctness and performance (C1-C6)

Starred categories (★) recur across many years or many reviews. Read them first.

## C1 ★ Voided or retired filtering missing on joined children, or inverted
A query or serializer filters the root entity but not the joined children, so voided or retired rows show up, or the filter is inverted.
- **While writing:** Decide voided and retired handling for every joined `Voidable` or `Retireable`. Write a test with a voided child that would otherwise match.
- **When reviewing:** HQL or Criteria with joins and a `voided = false` on the root only; getters that return raw collections; "include voided" flags with inverted defaults.
- **Seen in:** TRUNK-967 then TRUNK-6528 (the same bug 18 years apart), TRUNK-3352, TRUNK-3892
- **Module twist:** In REST the leak is usually `addProperty("x")` reflecting a raw core getter, and each named rep and the `custom:` rep can filter differently (RESTWS-1010, RESTWS-655 / RESTWS-733 / RESTWS-994). Reporting's `HqlQueryBuilder` adds `voided=false` only for the root entity, and SQL definitions get none, so each evaluator must add the joined checks. Wrappers such as `VisitDomainWrapper` each re-implement "non-voided encounters of this visit".

## C2 ★ Filtering, counting or traversing in Java
Code loads everything and filters, counts or pages in memory, which is slow and wrong as data grows.
- **While writing:** Push predicates, counts and paging into SQL or HQL. Never `getAll...().stream().filter(...)` over a table that can grow.
- **When reviewing:** `getAll*()` followed by `.stream().filter`, `.size()` for a count, or `subList` for paging.
- **Seen in:** TRUNK-4692 then TRUNK-6681 (same DAO, 11 years apart), TRUNK-4374
- **Module twist:** Domain wrappers make whole-graph traversal look cheap (`visit.getEncounters()` then filter) and dashboards call them per row. In the 2.x UI a server-side limit in widget code is followed by a JS filter that defeats it.

## C3 ★ Index-defeating query shapes and repeated full-text passes
Wrapping an indexed column in `lower()` or `upper()` prevents index use, and running the same full-text query several times multiplies cost.
- **While writing:** Rely on the column collation or a normalized column for case-insensitive matches. Run each full-text query once and reuse the result.
- **When reviewing:** `lower(` or `upper(` in HQL and Criteria strings; leading-wildcard `like '%x'`; one search split into several passes.
- **Seen in:** TRUNK-4452 then TRUNK-5071, TRUNK-6687
- **Module twist:** Queries stored as raw SQL in global properties never get an ORM or index review and can be 3x slower on MySQL 8 (BAH-3974).

## C4 N+1 selects
Iterating a collection triggers one select per element because nothing batches the fetch.
- **While writing:** Add `@BatchSize` to iterated collections and keep `@ManyToOne` lazy. Prefer one fetch-join or batch query over a loop of `getX()`.
- **When reviewing:** Loops that call a lazy getter per item; new associations with no batch size on a list endpoint.
- **Seen in:** TRUNK-4209, TRUNK-4141, TRUNK-6647
- **Module twist:** In REST and FHIR the N+1 is in the representation or translation layer (one lookup per output property or reference), not in mappings (RESTWS-482, FM2-642). In O3 it is one fetch hook per rendered row, which is HTTP fan-out; request the smallest custom rep and avoid per-row hooks.

## C5 Filtering a fetched collection truncates it; to-many joins duplicate rows and break paging
A row limit is applied before a Java-side filter, or a to-many join returns the same parent several times, so pages are short, duplicated or inconsistent.
- **While writing:** Match with `exists` or a subquery. Select distinct ids first, then load entities. Page and count in SQL, cap counts, and always end the sort with a unique key (uuid or id).
- **When reviewing:** `setMaxResults` combined with a to-many join; a count query built separately from the results query; sorts without a tiebreak; `limit<=0` bypassing the absolute cap.
- **Seen in:** TRUNK-2472 then TRUNK-5089, TRUNK-1216, RESTWS-1035 (`/concept?memberOf=` duplicates), FM2-562 (no SQL LIMIT)
- **Module twist:** FHIR bundles that held every match's uuid exhausted memory (FM2-537), and exact totals on big sets were too slow (`_excludeTotal`, capped count, FM2-572).

## C6 Caches that go stale, never expire, or lose their config
A cache is not evicted on every write path, caches "not found" forever, is unsafe in a cluster, or loses its region settings in a migration.
- **While writing:** Evict on every write path. No negative caching without a TTL. Keep the cache cluster-safe. Carry region config across mapping migrations.
- **When reviewing:** New cache annotations or maps with no matching eviction; a mapping migration that drops cache settings.
- **Seen in:** TRUNK-6679, TRUNK-6810, TRUNK-3675
- **Module twist:** Reporting caches evaluated results per evaluation, keyed by definition config. The usual bug is a wrong key, not staleness (see N1).
