# Metadata loading and import (L1-L5)

Starred categories (★) recur across many years or many reviews. Read them first. Covers Initializer, the OCL importer (openconceptlab) and addresshierarchy. Random UUIDs for derived child metadata are covered in A6.

## L1 ★ Retired state resurrected or ignored on re-import
Loaders that "save the current definition" treat retire and void as an afterthought. New rows that are retired fail to install, referencing a retired concept from another domain un-retires it, and retired answers, set members and mappings are re-added because the "not found, so add" branch ignores the incoming retired flag.
- **While writing:** For every lookup-then-create path, handle each case of {exists active, exists retired} by {incoming active, incoming retired}, including "absent locally and incoming retired". Loading a referencing domain must never change the referenced object's retired flag. Propagate retirement reasons.
- **When reviewing:** `if (existing == null) add(...)` with no check of the incoming retired flag; a bootstrap that builds a new object and saves it through a path that resets `retired`; tests that cover only active rows.
- **Seen in:** OCLOMRS-1109 (retired mapping un-retired by import), OCLOMRS-1116 (retired answers and set members re-added), iniz#315 (conceptsets domain un-retired the concepts it referenced), iniz#106 (retired CSV rows failed on a fresh database)

## L2 Absent vs empty vs unspecified in declarative loaders
On re-load, a property missing from the source is sometimes treated as "clear it" and sometimes as "leave it", and the choice differs by field. Collections the file does not mention are wiped, or stale values stay after the source drops an attribute.
- **While writing:** Decide the rule per column, document it and test it. Column absent means untouched; present and empty means clear; an attribute absent in an OCL export means the model default. Never clear a collection the source format cannot express.
- **When reviewing:** `getX().clear()` before repopulating; `if (value != null) set(value)` for booleans or flags; a field applied only for some subtypes.
- **Seen in:** iniz#110 (properties not named in the CSV wiped), iniz#198 (re-load cleared Members and Answers), OCLOMRS-1118 (`isSet` could never go back to false), iniz#330 (OrderType `parent` silently dropped)

## L3 Change-detection state drifts from the database
Loaders skip work from bookkeeping (file checksums, OCL item rows, an in-progress row). That state can say "done" when the database disagrees: rows failed but the checksum was written, loader semantics changed but checksums did not, a crash left the in-progress flag set, or two modules keep separate stores.
- **While writing:** Record success per row or item only after it commits. Version the checksum algorithm and loader semantics so a code change invalidates old checksums. Clear stale "in progress" state at startup. One owner per piece of bookkeeping.
- **When reviewing:** Checksum or "processed" writes in `finally`; changes to derived output (UUID seeding, defaults) with no checksum-invalidation plan; new skip-if-unchanged shortcuts.
- **Seen in:** initializer@372f39d (checksum written despite row errors), iniz#141 (changing UUID derivation needed a changeset deleting checksums), OCLOMRS-1111 (interrupted import blocked all later imports), ADDR-142 (two checksum stores)

## L4 Resolving references by non-unique natural keys
Loaders resolve references by name, by `LIKE`, by "first concept with this mapping", or by uuid only. They return the wrong object, throw "more than one result", or create duplicates where the target system has local equivalents.
- **While writing:** Resolve by uuid first, then by an exact, unique, locale-qualified key. Escape `%` and `_` in any LIKE. Fail loudly on ambiguity instead of taking the first row. Document the matching order (uuid, mapping, name) and test each fallback with a local look-alike.
- **When reviewing:** `getXByName`, `getConceptByName`, `.get(0)`, `setMaxResults(1)`, `like` with user-supplied names, matching with a single strategy.
- **Seen in:** iniz#317 (FSN lookup with `LIKE`, "CD4%" matched several), OCLOMRS-1107 (mappings matched only by external id were duplicated), OCLOMRS-1110, ADDR-60

## L5 Bulk imports done entity-by-entity; two modules owning the same config
Hierarchy and dictionary imports go through the ORM one entity at a time, keep the whole graph in the session, look up tracking rows per item and index synchronously: fine for fixtures, tens of minutes for real data. Separately, a domain module and Initializer both load the same configuration folder and overwrite each other.
- **While writing:** Benchmark with production-size input (full CIEL, a country hierarchy). Commit in batches with `flush()` and `clear()`. Pre-load lookup maps in one query. Make per-entity side effects (search indexing) async or off in the bulk path. One owner per config folder or entity type; when Initializer takes over a domain, the original loader turns itself off.
- **When reviewing:** Per-row `getById` or `getByUrl` inside import loops; no batch flush and clear; activators reading `configuration/<x>` that Initializer also loads; loaders that do not propagate failures.
- **Seen in:** ADDR-148 (120k rows from about 15 min to about 45 s by caching parents), openconceptlab@531b149 (35k redundant item queries per large zip), ADDR-109 then ADDR-142 (address config loaded twice), iniz#233
