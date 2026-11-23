# Testing in openmrs-core, shared modules and O3 apps

What upstream reviewers expect from tests, how to write and run them, and what CI does and doesn't cover. The `openmrs:pitfalls` skill has the test mistakes to avoid (I1: fails-before/passes-after, privilege tests, never skip tests; B7: flush and clear before asserting). This file covers how to do the testing.

Test setups change. Check the repo's base classes, `pom.xml` or `package.json`, and `.github/workflows` before relying on the details below (checked November 2026).

## What a PR needs

- **Bug fix:** a test that fails without the fix and passes with it, at the layer where the bug shows up. Write it first and watch it fail.
- **Feature:** tests for the new behavior and its edges: voided and retired data, nulls, a user without the privilege, existing data the change didn't create.
- **Refactor:** existing tests must still pass. Add tests first if the code you're moving has none.
- Tests go in the same PR as the change. The core and module PR templates ask for this, and reviewers check.
- Test data is made up. Never put real patient records, or anything copied from a PIH database, in a data set or fixture.

## Backend: openmrs-core and modules

### Pick the kind of test

| Code under test | Test |
|---|---|
| Pure logic (parsing, calculations, comparators) | Plain JUnit test, no Spring context |
| Code that calls `Context` services, where the services themselves aren't the point | `BaseContextMockTest` with Mockito |
| DAOs, HQL/Criteria, Hibernate mappings, Liquibase-created schema, service methods with `@Authorized`, validators, save handlers, AOP | Context-sensitive test against the test database. Mocks hide exactly these bugs |
| Controllers, REST resources | `BaseModuleWebContextSensitiveTest`; REST resources in webservices.rest use `BaseDelegatingResourceTest` |

**Use the module's own base class when it has one.** It loads the module's data sets and Spring config. Examples: fhir2 `BaseFhirContextSensitiveTest`, `BaseFhirR4IntegrationTest`, `BaseFhirR4ResourceProviderWebTest`; htmlformentry `BaseHtmlFormEntryTest`; idgen `IdgenBaseTest`; registrationcore `BaseRegistrationCoreSensitiveTest`; queue `BaseQueueResourceTest`. Otherwise use `BaseModuleContextSensitiveTest`.

### Conventions

- **JUnit 4 and 5 both exist,** often in the same module. In core, the `org.openmrs.test.jupiter` base classes are JUnit 5 and the `org.openmrs.test` ones are JUnit 4. When adding to a test class, use its version. For a new class, copy the newest tests in that module. Don't mix the two in one class.
- **Test names:** follow the module. Core and emrapi use `methodName_shouldDoSomething`; fhir2 mostly uses `shouldDoSomething`.
- **Data sets:** DBUnit flat XML loaded with `executeDataSet(...)`, on top of the standard test data set. Add a small data set for your test under `src/test/resources` instead of growing a shared one other tests depend on.
- **Spring config for module tests:** `src/test/resources/TestingApplicationContext.xml`, one per Maven submodule.
- **Version-specific submodules:** some modules have a submodule per core version, for example fhir2 (`api-2.5`, `api-2.6`, `api-2.7`, `integration-tests-2.6`, `integration-tests-2.7`), reporting (`api-1.9` to `api-2.4`) and initializer (`api-2.2` to `api-2.7`). Code that needs a newer core goes in that submodule, and so do its tests.

### H2 is not your production database

Context-sensitive tests run on in-memory **H2** by default. H2 accepts SQL, column types, Liquibase changesets and mappings that fail on MySQL or PostgreSQL, and the other way round. Case sensitivity, collation and date handling also differ.

- **openmrs-core** can run context-sensitive tests on a real database in Docker through Testcontainers: `-DuseInMemoryDatabase=false`, plus `-Ddatabase=postgres` or `-Ddatabase=mariadb` (MySQL 5.7 is the default). Tests named `*DatabaseIT` (Liquibase upgrades, `ValidateHibernateMappingsDatabaseIT`) always use a container.
- **Modules** have no such switch, and their CI runs on H2 only. For a Liquibase changeset or a mapping change in a module, run it yourself: start an SDK server on MySQL with the module installed (and PostgreSQL when the module claims to support it), check that the changesets run, and use the feature. Also run the changeset against a database that already has rows in the affected tables (pitfalls A3).
- Say in the PR which databases you tested on.

### Running tests

- **Everything:** `mvn clean install` from the repo root.
- **One class or method:** `mvn test -pl api -Dtest=ClassName#methodName`. Install once first so the sibling submodules resolve. When `-Dtest` should match only some submodules, add `-Dsurefire.failIfNoSpecifiedTests=false`.
- **Core integration tests:** `mvn test -Pintegration-test -Pskip-default-test`. Needs Docker.
- **Java version:** run tests on the lowest Java the target branch supports, especially for backports. Core `master` builds on Java 21 and 25; `2.8.x` on Java 8 to 21. Modules build on the Java versions that follow from the core version in their `pom.xml`.

### What CI covers, and what it doesn't

- **openmrs-core `master`:** unit tests on Linux and Windows, plus the integration-test profile on Linux (MySQL via Testcontainers), on Java 21 and 25. Performance tests only run after merge. **PostgreSQL and MariaDB aren't tested in CI.**
- **Maintenance branches** (`2.8.x` and older): their own workflow, with older Java versions.
- **Modules:** most call the shared `openmrs/openmrs-contrib-gha-workflows` `build-backend-module.yml`. It runs `mvn clean install` on each Java version, on H2, against the core version in the module's `pom.xml` only. It doesn't run Liquibase on a real database, start the module in a running OpenMRS, or test older core versions the module still claims to support.

Cover those gaps yourself when the change touches them, and list what you checked in the PR description.

## Frontend: `@openmrs/esm-*` apps

- **Unit and component tests** sit next to the component as `*.test.tsx`. The newer monorepos (esm-patient-chart, esm-patient-management) use **Vitest**; others still use **Jest** (for example esm-home). Check `package.json`.
- Use React Testing Library with `user-event`, and the repo's shared helpers in `tools/` (in esm-patient-chart: `tools/test-utils.tsx` with `mockPatient` and `renderWithSwr`). `@openmrs/esm-framework` is replaced by `@openmrs/esm-framework/mock` in tests, so mock framework calls through it, not your own stubs.
- Test the config schema's default and at least one configured value when you add or change a config option.
- **`yarn verify`** runs lint, TypeScript and the unit tests through turbo. It's what CI runs on a PR, so run it before pushing.
- **End-to-end:** Playwright specs in `e2e/specs/*.spec.ts`, run with `yarn test-e2e`. In CI, the e2e workflow packs the repo's apps into a reference application backend in Docker. Locally you need a running backend (copy `example.env` to `.env`). When a change alters a user flow an existing spec covers, update the spec; for a new flow, add one.

## Before asking for review on a change PIH needs

CI proves the module builds. It doesn't prove the PIH ticket is solved. Also:

- Run the PIH ticket's scenario on a local SDK server with the PIH distro and the module SNAPSHOT (or the O3 app built locally).
- For a backport, build and run the tests on the maintenance branch, not just on `master`.
- Describe the testing in the PR in generic terms ("tested on MySQL 8 with an existing database"), with no patient data and no PIH-only details.
- Deploying to a shared PIH CI server affects other people's testing: ask the user first.
