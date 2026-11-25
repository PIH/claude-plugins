# Liquibase and schema (A1-A9)

Starred categories (★) recur across many years or many reviews. Read them first.

## A1 ★ Editing a released changeset or snapshot
A shipped changeset or snapshot file is edited in place, so its checksum no longer matches the databases that already ran it and startup fails.
- **While writing:** Never change a changeset that has shipped. Add a new changeset. If an edit is unavoidable, pin the old checksum with `validCheckSum` on purpose and say why.
- **When reviewing:** Any removed or changed line inside an existing `<changeSet>` block, any renamed changeset id, and snapshot or seed-data files touched after release.
- **Seen in:** TRUNK-4161, TRUNK-5304, TRUNK-6292, TRUNK-6634 (83 `validCheckSum` pins in the 2.0.x file)
- **Module twist:** A module ships one `liquibase.xml` that re-runs against many installed versions, so each in-place edit needs a pin for every checksum ever in the field. Compute pins with the Liquibase of the module's minimum platform, not your local one. Reporting kept editing released changesets per DB engine instead of adding engine-specific ones. See also fhir2@9c1bc9e0.

## A2 ★ Missing, wrong or inverted preconditions, no `onFail`
A changeset has no precondition, checks the wrong object, inverts the check, or lacks `onFail`, so it fails on databases where the object already exists or never existed.
- **While writing:** Put a precondition on the exact target (table, column, index, row) with `onFail="MARK_RAN"`. Assume a module or an earlier release may have done the work already.
- **When reviewing:** An added `<changeSet>` with DDL and no `<preConditions>`; `onError="WARN"` without `onFail`; `not` wrapped around the wrong check.
- **Seen in:** TRUNK-2001, TRUNK-3364, TRUNK-5659, TRUNK-6449
- **Module twist:** The precondition must also cover "core or another module already created this object". Slow preconditions run on every module start, so keep them cheap. See also fhir2@fd1e45fb.

## A3 ★ Constraints added without handling existing rows
A NOT NULL, foreign key or unique constraint is added in one step, so real data with nulls, orphans or duplicates breaks the upgrade.
- **While writing:** Add a nullable column, backfill, then add the constraint, each as its own changeset. Guard the constraint with a `sqlCheck` precondition that finds offending rows.
- **When reviewing:** `addNotNullConstraint`, `addForeignKeyConstraint`, `addUniqueConstraint` or `nullable="false"` with no `defaultValue*`, and no `<update>`, `<sql>` or `sqlCheck` in the same changeSet.
- **Seen in:** TRUNK-6001, TRUNK-4690, TRUNK-6081 then TRUNK-6205, TRUNK-3396

## A4 ★ MySQL modify or rename silently drops NOT NULL, defaults or FKs
`modifyDataType`, `renameColumn` and resizes on MySQL rebuild the column from the given spec only, so NOT NULL, defaults and foreign keys vanish without an error.
- **While writing:** Restate the full column spec (type, nullability, default) on every modify. Drop and re-add FKs around a resize. Verify the result with a schema diff on MySQL and PostgreSQL.
- **When reviewing:** `modifyDataType` or `renameColumn` that does not repeat `nullable` and `defaultValue`; resizes of a column that is an FK target.
- **Seen in:** TRUNK-6044 then TRUNK-6081, TRUNK-2878, TRUNK-3993

## A5 ★ Single-engine SQL
Changes use MySQL-isms, reserved-word identifiers, `dbms=` filters, `= 0` booleans, explicit ids or sequences, so they fail on PostgreSQL, MariaDB or MySQL 8.
- **While writing:** Use portable Liquibase change types. Check new table and column names against the MySQL 8 and PostgreSQL reserved-word lists. Run the changeset on MySQL 8 and PostgreSQL before merging.
- **When reviewing:** `dbms="mysql"` without mariadb or postgresql, `tinyint`, backticks, `GROUP_CONCAT`, `DATE_FORMAT`, a column named `rank`, literal ids or creators in seed SQL.
- **Seen in:** TRUNK-6044 (`rank`), TRUNK-4813, TRUNK-5794, TRUNK-6634 (plus about 40 module tickets in the PostgreSQL wave)
- **Module twist:** Dashboard and list SQL shipped in global properties through `sqlFile` breaks on escaping rules, path resolution and MySQL 8 (AP-77, BAH-4208); inline it and never hard-code ids. fhir2 builds queries with Criteria, so the engine-specific part is DISTINCT plus ORDER BY on a non-selected column (fhir2@21077017).

## A6 Non-deterministic or lossy data migrations
Migrations that seed or copy metadata generate random UUIDs, copy UUIDs between rows, omit column lists, or silently drop ambiguous rows.
- **While writing:** Use fixed UUIDs for seeded metadata and never copy a UUID to a new row. List columns explicitly. Halt (precondition) on ambiguous data instead of guessing.
- **When reviewing:** `uuid()` or `randomUUID` in a migration, `insert ... select *`, a migration that deletes or merges rows without a count check.
- **Seen in:** TRUNK-3298, TRUNK-3414, TRUNK-4513
- **Module twist:** Loaders that derive child metadata (names, answers, set members) must derive UUIDs from the parent UUID plus a stable key. Random ones break re-imports and dbsync (OCLOMRS-1062, iniz#141).

## A7 Changeset identity, placement and backports
Changesets run twice because an id was renamed, placed in an old version file, or backported with a different id on another branch.
- **While writing:** Add changesets only to the current version's update file. A backported copy must be idempotent (preconditions) so it is safe if both copies run.
- **When reviewing:** Changed `id` or `author` values, new changesets in an older-version changelog, the same logical change on two branches.
- **Seen in:** TRUNK-5821, TRUNK-6315, TRUNK-5304
- **Module twist:** Modules "fix" a changeset by renaming its id (appointments@09ecca2). It then runs again on every existing database, so the content must be idempotent. fhir2@0f14570d declared one id twice with different `dbms`.

## A8 Long-running or non-resumable migrations on big databases
A migration that is fine on a demo database loops row by row or does several DDL steps in one changeset, so it times out or half-applies on millions of obs.
- **While writing:** Use set-based SQL, one DDL statement per changeset, and estimate the cost on millions of obs rows. Make a half-finished run recoverable.
- **When reviewing:** Java custom changes that iterate rows, several `alter` statements in one changeSet, new indexes on `obs` with no size note.
- **Seen in:** TRUNK-2919, TRUNK-549, TRUNK-6381
- **Module twist:** In modules the cost is often slow preconditions that run on every start, not the migration itself.

## A9 Schema and mapping drift; startup code using Hibernate before the schema update
A Hibernate mapping changes without a matching changeset, or startup code queries through Hibernate before Liquibase has updated the schema.
- **While writing:** Every mapping change has a changeset in the same PR. Code that runs before the schema update uses plain JDBC, not Hibernate.
- **When reviewing:** New or changed `*.hbm.xml` or entity fields with no Liquibase change; activators or startup listeners calling services early.
- **Seen in:** TRUNK-4773, TRUNK-6406, TRUNK-6081
