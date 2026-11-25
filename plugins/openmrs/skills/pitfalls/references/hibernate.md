# Hibernate mappings, session and domain model (B1-B7, D1)

Starred categories (★) recur across many years or many reviews. Read them first.

## B1 ★ Mapping migration not semantically identical
Moving mappings (hbm.xml to JPA annotations) changes defaults: JPA `@ManyToOne` is EAGER, cascade and orphan-removal settings shift, unsaved-value and types differ. The app still compiles and most tests pass.
- **While writing:** Set `fetch = FetchType.LAZY` explicitly. Copy cascade and orphan settings exactly from the old mapping. Migrate one entity per PR and run the mapping-validation integration test.
- **When reviewing:** `@ManyToOne` or `@OneToOne` without `fetch = LAZY`; `orphanRemoval = true`; a changed `cascade`; a changed id generator or unsaved-value.
- **Seen in:** TRUNK-6680, TRUNK-6684, TRUNK-5494 / TRUNK-5664 / TRUNK-5671 (reverts), d0308f347

## B3 ★ LazyInitializationException "fixed" by going eager
A lazy-load error is silenced with `FetchType.EAGER`, or entities are held in statics, caches or `toString`, where they outlive their session.
- **While writing:** Initialize what you need inside the transaction (fetch join or explicit init). Never cache entities in statics or long-lived maps; cache ids or DTOs.
- **When reviewing:** A mapping flipped to EAGER in a bug fix, entity fields in static or singleton caches, `toString` that touches associations.
- **Seen in:** TRUNK-1167 (reverted), TRUNK-5740, TRUNK-809
- **Module twist:** In reporting, evaluated datasets hold live entities that outlive the session in the report cache, on disk and in REST output. Cache uuids or plain values.

## D1 ★ equals, hashCode and compareTo inconsistent
`compareTo` without a unique tiebreak makes `TreeSet` and sorted maps drop "equal" objects; `equals` overrides break with Hibernate proxies and null ids.
- **While writing:** End `compareTo` with a uuid tiebreak. Do not override `equals`/`hashCode` on `BaseOpenmrsObject` subclasses. Use `instanceof` and getters, never field access, so proxies work.
- **When reviewing:** `compareTo` that ends on a date or name; `getClass() ==` comparisons; `equals` that reads fields directly; hashCode built from a mutable or null id.
- **Seen in:** TRUNK-3645 / TRUNK-3652, TRUNK-5331, TRUNK-82, TRUNK-1080

## B2 Replacing managed collections; copy-constructor and cascade changes
Assigning a new collection to a managed entity's field, or changing a copy constructor or cascade, makes Hibernate delete and re-insert children or fail on orphans.
- **While writing:** Mutate the existing collection (`clear()` then `addAll`); never assign a new one in a setter. Test save, flush, clear, reload.
- **When reviewing:** `this.<field> = new HashSet/ArrayList` in an entity setter; a rewritten copy constructor.
- **Seen in:** TRUNK-5120, TRUNK-4925, TRUNK-50

## B4 Auto-flush and dirty checking persist "unsaved" changes
Mutating a managed entity for display or scratch use gets flushed to the database later, by auto-flush at the next query or commit.
- **While writing:** Do not mutate managed entities for display or temporary work; copy them. Validate before mutating. Compare dates with `getTime()`, since a `Timestamp` and a `Date` compare unequal and mark the entity dirty.
- **When reviewing:** Setters called in read-only or validation paths; queries issued inside a validator or handler after a mutation.
- **Seen in:** TRUNK-3759, TRUNK-3949, TRUNK-3691, TRUNK-4955
- **Module twist:** The flush often comes from a module's `SaveHandler` or AOP advice running a query during someone else's save.

## B5 Fighting the session: evict, merge, saveOrUpdate misuse
Helper code evicts or merges entities it does not own, or discards the instance `merge` returns, so the caller works on a detached copy.
- **While writing:** No `evict` in validators or helpers. Always continue with the instance that `merge` returns.
- **When reviewing:** Statement-level `.merge(` or `saveOrUpdate(` whose result is unused; `evict`/`clear` outside the layer that owns the session.
- **Seen in:** TRUNK-6836, fb351a8f8, TRUNK-5977

## B6 Session and transaction ownership; background threads
Code closes a session it did not open, or runs in a thread (scheduler, async job) that has no session or user context.
- **While writing:** Only close what you opened. Every job or thread opens its own session and closes it in `finally`.
- **When reviewing:** `closeSession` in shared code, `new Thread`, executors or scheduled tasks that call services with no `Context.openSession()`.
- **Seen in:** TRUNK-6818, TRUNK-6852, TRUNK-4748

## B7 Tests pass because the first-level cache hides what was persisted
A test saves an entity and reads it back in the same session, so it sees the in-memory object, not the database row.
- **While writing:** Flush and clear the session before asserting on a fresh load.
- **When reviewing:** Persistence tests with no `flush()`/`clear()` between save and assert.
- **Seen in:** TRUNK-6411, TRUNK-6684
