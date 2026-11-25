# Cross-cutting behavior, lifecycle and packaging (E1-E5, O1)

Starred categories (★) recur across many years or many reviews. Read them first.

## E1 ★ Changing global persistence or AOP behavior
Flush mode, interceptors, save handlers, advice or validators that derive data change behavior for every caller, including paths you never tested.
- **While writing:** Treat it as a platform change. Test with no user (daemon thread, startup, setup wizard) and through module code paths. Validators reject; save handlers derive values.
- **When reviewing:** Edits to flush mode, interceptors, `SaveHandler`s, AOP pointcuts, or a validator that sets fields.
- **Seen in:** TRUNK-3069, TRUNK-2680, TRUNK-2015, TRUNK-6795
- **Module twist:** A module's `SaveHandler` or advice runs inside other modules' saves, so a query or a privilege demand there hits unrelated flows (BED-40).

## O1 ★ Platform version ranges, version-conditional submodules, optional-module wiring
A module lists exact platform versions, ships per-version submodules, or loads classes that refer to optional modules, so each new core release breaks loading or silently removes features.
- **While writing:** Use open-ended ranges (`2.4.* - 9.*`) unless the code truly is version-specific. Fix every parallel version submodule, not one. Put code that touches optional modules or removed core classes in conditionally loaded (`@OpenmrsProfile`) beans. Test on the lowest and highest supported platform.
- **When reviewing:** A closed `supportedOpenmrsVersions` list; an `openmrsVersion="1.10"` style expression (it also matches 1.11); a fix applied to one of several `ResourceX_Y` classes; Spring-scanned classes importing another module's classes; a new `<lib>` jar in the omod.
- **Seen in:** RESTWS-891 (omod-2.3 not listed for 2.4+), REPORT-851 / REPORT-857 (reportingrest, bumped each release), EA-83 (conflicting beans from `openmrsVersion="1.10"`), BAH-3249 (appointments broke core mail)
- **Module twist:** Keep notification side effects (mail, SMS) out of the save transaction (BAH-1140). Prefer raising the minimum platform over adding shims.

## E2 Spring refresh, proxying and advice assumptions
Registration code is not idempotent across a context refresh, or relies on JDK proxies, or on annotations that proxying and inheritance can hide.
- **While writing:** Register idempotently so it survives a Spring refresh. Do not assume JDK proxies. Check that advice still reaches the method after any inheritance or auto-proxy change.
- **When reviewing:** Beans holding services from a pre-refresh context; `@Transactional` on private or self-invoked methods (silently ignored); auto-proxy configuration changes.
- **Seen in:** TRUNK-6382, TRUNK-1604, TRUNK-3015
- **Module twist:** In fhir2, privilege checks depend on AOP advice reaching DAO methods, so a proxy or inheritance change can turn them off (fhir2@44037a5d moved `@Authorized` to the interfaces; fhir2@1a7abaa5 / c6be10d9 reverted and re-applied an auto-proxy change within 4 days).

## E3 Startup and module-load ordering; static init calling Context
Static initializers, logging config or activators call `Context` before it is ready, or modules load in an order that nobody sorted by dependency.
- **While writing:** No `Context` calls in static init or logging configuration. Sort loading by module dependencies and tolerate a missing optional module.
- **When reviewing:** `static {` blocks and field initializers that call services; activators doing heavy work in `started()`.
- **Seen in:** TRUNK-6367, TRUNK-6688, TRUNK-4487
- **Module twist:** Loader order matters between modules (fhir2 SMART-on-FHIR before Keycloak, FM2-423; deadlock while loading resources, RESTWS-359).

## E4 Shared mutable state, locks, per-user state in singletons
Singletons hold per-user or per-request state, locks that do not outlive what they guard, or collections that are iterated while changing.
- **While writing:** Locks must outlive what they guard. Iterate over copies. Keep per-user state in the session. Treat framework definitions (apps, extensions) as immutable and copy before decorating per request.
- **When reviewing:** Mutable fields on singletons or services, `synchronized` around DB writes, setters called on objects returned by a framework service.
- **Seen in:** TRUNK-3363 then TRUNK-3784, TRUNK-6267, TRUNK-6645, f137a7081
- **Module twist:** Request code in the 2.x UI replaced labels on shared Extension objects (RA-2083) and shared one script engine across threads (AF-76). Identifier allocation guarded only by in-JVM locks, with no DB lock or unique constraint, allocated duplicates (IDGEN-6, IDGEN-28); lock at the database and assume several JVMs. In O3 the shared "singleton" is a global store that every microfrontend sees.

## E5 Environment and topology assumptions
Code assumes a local Linux filesystem, one webapp, or a particular container layout.
- **While writing:** Check that it works in the plain compose stack and in derived images. Check the result of `File.delete()`. Never build resource paths with `File.separator`; use `/`.
- **When reviewing:** Hard-coded paths, assumptions about the app data directory, file operations that ignore failure.
- **Seen in:** TRUNK-6650, TRUNK-6509 then TRUNK-6675, TRUNK-5975
