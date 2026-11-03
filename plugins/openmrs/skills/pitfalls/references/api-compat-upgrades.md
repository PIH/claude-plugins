# API compatibility, upgrades and process (F1-F6, I1, I2)

Starred categories (★) recur across many years or many reviews. Read them first. Process questions (tickets, Talk, backports, releases) are covered by the `core-modules` skill.

## F1 ★ Breaking public signatures or removing members
A public method is changed, removed or retyped, so compiled modules fail with `NoSuchMethodError` or stop compiling.
- **While writing:** Overload and deprecate (`@since`, `@deprecated`); do not change signatures outside a major release. Search the openmrs GitHub org for callers first.
- **When reviewing:** Changed parameter or return types on a public API; removed methods; refactors of services modules extend (the scheduler, `Context`).
- **Seen in:** TRUNK-5386, TRUNK-2733, TRUNK-3496, TRUNK-5200
- **Module twist:** A module's "API" includes classes others extend, such as htmlformentry's `FormEntryContext`, `FormEntrySession`, widgets and the test-helper jar (HTML-736). Process (tickets, Talk, backports, releases): see the `core-modules` skill.

## F4 ★ New or stricter validation that rejects existing data or defaults
A new validation rule rejects values that existing rows, shipped defaults or old clients legitimately contain.
- **While writing:** Test null and blank, shipped defaults, estimated values and legacy rows. Audit existing data before rejecting a pattern.
- **When reviewing:** New `rejectValue` calls, new length or format limits, new required fields in a validator.
- **Seen in:** TRUNK-4429 then TRUNK-4630, TRUNK-4906 then TRUNK-5331, TRUNK-4939
- **Module twist:** A strict new ADT validator needed an existing-data audit and was reverted (EA-226).

## F5 ★ Dependency or framework upgrades that silently drop behavior
A version bump passes unit tests but removes something the old config did implicitly (bootstrap code, a transitive class, a classloader behavior).
- **While writing:** List what the old configuration did implicitly. Start the real webapp on a real database before merging. Do not leave a TODO for lost behavior.
- **When reviewing:** `pom.xml` or `package.json` bumps of Hibernate, Spring, Liquibase, Tomcat, drivers, HAPI or the JDK; removal of "legacy" bootstrap code. Ask whether the webapp was started and the upgrade tests run.
- **Seen in:** TRUNK-6679, TRUNK-6686, TRUNK-6827, about 33 dependency-bump reverts
- **Module twist:** Upgrading shared front-end libraries in base UI modules (Angular, Bootstrap, datatables) was reverted several times because dependents broke (uicommons@03e9e0f, RA-1592); ship alongside the old version and smoke-test a large distro. In O3 the framework is shared at runtime, so one breaking release breaks apps not yet updated.

## F6 ★ "Cleanup" refactors that remove something used
A tidy-up deletes a field, method or object that was used by reflection, templates, Spring XML or another module.
- **While writing:** Grep templates, Spring XML and modules before removing. Write characterization tests first. Do not create new domain objects with null ids.
- **When reviewing:** Removed "unused" fields or beans; new objects built by constructors that skip uuid or id setup.
- **Seen in:** TRUNK-5998, TRUNK-5158 then TRUNK-5223, TRUNK-5117 then TRUNK-5967 (unnoticed for 3 years)
- **Module twist:** In reporting, removing a field or making an inner class static breaks stored XStream definitions (see N2). Form JSON and import-map overrides are the frontend's stored code.

## I1 ★ Merging without a failing-then-passing test; weakened tests; red CI
A fix has no test that failed before and passes after, or tests are skipped or excluded to get green.
- **While writing:** Write the test at the layer where the bug appears and watch it fail first. Never `@Ignore` or exclude an integration test to get green.
- **When reviewing:** Added `@Ignore`/`@Disabled`, `.skip(` or `xit(`; changed test exclusions in poms; tests that depend on timezone or order.
- **Seen in:** TRUNK-5120, TRUNK-5493, TRUNK-6406
- **Module twist:** Test rules or masks registered globally leak across the suite (RESTWS-1061); running CI in UTC hides timezone bugs.

## I2 ★ Backporting features or behavior changes, or backports missing their context
A change is cherry-picked to a maintenance branch although it is a feature, or without the surrounding infrastructure it depends on.
- **While writing:** Backport only targeted bug fixes. Diff the surrounding infrastructure (config, schema, callers) between branches first.
- **When reviewing:** Backports that add options or change defaults; a cherry-pick that applies cleanly but references code absent on the branch.
- **Seen in:** TRUNK-4761, TRUNK-3069, TRUNK-6331
- **Module twist:** Process (tickets, Talk, backports, releases): see the `core-modules` skill.

## F2 Changing exception types or failure modes; swallowing errors; ignored parameters
A fix changes which exception is thrown or silently falls back to a default, so callers' handlers stop working or errors vanish.
- **While writing:** Keep exception types stable. Never silently fall back to a default for an invalid parameter; fail clearly. Security hardening that blocks callers needs a migration note.
- **When reviewing:** New catch-and-ignore blocks; changed `throws`; parameters accepted but unused.
- **Seen in:** TRUNK-6823, TRUNK-6457, TRUNK-5395
- **Module twist:** A global filter or privilege hardening in one module blocks other modules' flows (a DWR filter read only its own config, so other modules got 403, LUI-212; privileged GP reads broke the pre-login page, UIFR-225). Build allow-lists from all modules and exempt pre-auth paths. In REST, Spring `AccessDeniedException` was not mapped to 401/403 (RESTWS-1056).

## F3 Changing defaults under existing installs; core absorbing module tables
A new option or behavior is on by default, or core takes over a module's table, so upgraded installs behave differently or collide.
- **While writing:** New options default to the old behavior. Test both an upgrade from the previous release and a fresh install.
- **When reviewing:** New global properties defaulting to "on"; moved tables or Liquibase between core and a module.
- **Seen in:** TRUNK-4513, TRUNK-4429 then TRUNK-4630, TRUNK-6449, TRUNK-5338
- **Module twist:** Retrofitting authorization into a module that shipped open needs a role-grant migration in the same release (RESTWS-989 after TRUNK-6203). Process (tickets, Talk, backports, releases): see the `core-modules` skill.
