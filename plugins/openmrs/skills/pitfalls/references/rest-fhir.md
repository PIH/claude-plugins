# REST and FHIR (J1-J8)

Starred categories (★) recur across many years or many reviews. Read them first. Modules: webservices.rest, fhir2 and any module that defines REST resources. Paging, totals and sort stability are covered in C5.

## J1 ★ Representation-graph authorization
Privilege checks run on the requested root resource, but the serializer then walks nested properties, `custom:` reps, derived `display` strings and bean getters into objects the user may not read. Fixes add funnels (a denial sentinel, masking) and leftover paths stay open or turn into 500s.
- **While writing:** Resolve every nested object through its own resource so that resource's privilege and object rules apply. Never build `display` from a related object without asking the same rule. Do not expose properties that are not declared in a rep.
- **When reviewing:** New `@PropertyGetter` or `getDisplayString` code that reads another domain object; reflection fallbacks to bean getters; list-building loops that do not filter denied items.
- **Seen in:** RESTWS-1024 (nested custom rep exposed person data), RESTWS-1037 (denial sentinel leaked, HTTP 500), RESTWS-1059 / RESTWS-1060 (display strings and arbitrary getters), RESTWS-426 (Provider.person serialized as a full Patient)

## J4 ★ Generic write paths bypass service semantics
REST sets properties reflectively and FHIR maps a whole incoming resource onto the entity, then saves. Domain operations (void with cascade, child dedupe, audit fields, encounter propagation) are skipped, or collections are appended instead of merged.
- **While writing:** Route state transitions (void, retire, discontinue) through the service method. Merge child collections by identity. Never map client data onto audit fields (`dateCreated`, `dateChanged`).
- **When reviewing:** `setVoided` or `setRetired` from a property setter; `getX().add(...)` in an update translator; translators that write audit fields.
- **Seen in:** RESTWS-1063 (`voided: true` on an obs group left members live), RESTWS-930 / FM2-660 (duplicate encounter providers on every PUT), FM2-405 (`active=true` voided the person), RESTWS-901 reverted by RESTWS-933

## J5 ★ FHIR to OpenMRS presence and null semantics
HAPI getters return non-null defaults (empty objects, 0, empty strings) and FHIR ids carry `Type/` prefixes, so OpenMRS-style null checks in the reverse direction turn absent values into explicit values and ids get stored with prefixes.
- **While writing:** Use `hasX()` before `getX()` on HAPI types. Use `getIdElement().getIdPart()` for ids. Handle "present but empty" separately from "absent" in update paths.
- **When reviewing:** `!= null` on a HAPI getter; `getId()` instead of the id part; primitive getters feeding nullable OpenMRS fields.
- **Seen in:** FM2-86 (audit of always-true null checks), FM2-620 (null repeats became 0 refills), FM2-570 (`Encounter/<uuid>` stored as uuid), FM2-554 (setting values to null unsupported)

## J7 ★ FHIR search params silently ignored or mis-combined
A search parameter is parsed but not applied, combined with the wrong AND/OR logic, or applied at the wrong precision. The result is wrong totals or empty bundles, never an error.
- **While writing:** Give every declared `@OptionalParam` an integration test that asserts it narrows results. Follow the spec's AND/OR rules for repeated and chained params.
- **When reviewing:** New `SearchParameterMap` keys without a matching `handleX` in the DAO; changes to the shared search layer without per-param tests.
- **Seen in:** FM2-236 (Observation handlers never added to criteria), FM2-233 / FM2-539 (OR and chain logic), FM2-146 (date precision), FM2-700 (`based-on` returned total 0)

## J2 Custom rep path diverges from named reps
DEFAULT and FULL reps are hand-written while `custom:` reps go through a separate reflective path, so filtering, `type`, `display`, `links` and subclass handling differ by `v=` value.
- **While writing:** Put child filtering in a `@PropertyGetter` (used by every rep), not `addProperty("x", "activeX")`. Test each new property in DEFAULT, FULL and `custom:`, including on a subclass.
- **When reviewing:** `addProperty` pointing at a raw core collection getter; attributes added only in `asRepresentation` for named reps; no custom-rep test.
- **Seen in:** RESTWS-506 / RESTWS-664 (voided items in custom reps only), RESTWS-1012 (`type` missing), RESTWS-1030 (subclass-only property failed the list)

## J3 Resource and search-handler resolution ambiguity
Resources and handlers are looked up by name, `supportedClass`, `order` and parameters. Overlaps resolve by scan order or throw, so installing another module changes behavior.
- **While writing:** Declare the narrowest `supportedClass`, one resource per class. When overriding a resource, set `order` and test with the original present. Give a resource with several search handlers a `default` handler and unique parameter sets.
- **When reviewing:** A new `@Resource` or `@SubResource` whose class or name overlaps an existing one; search-handler params that are a subset of another handler's.
- **Seen in:** RESTWS-652 (`supportedClass=Object` broke reportingrest), RESTWS-1052 (last scanned wins), RESTWS-914, RESTWS-1019

## J6 FHIR terminology mapping choices
Emitting every concept mapping as a Coding claims equivalence for broader or narrower maps, and `display` on external codes asserts text that system may not use.
- **While writing:** Use the shared `ConceptTranslator` rule for every Coding. Emit only SAME-AS maps (or the documented single-mapping fallback). Put `display` only on the local code.
- **When reviewing:** Translators iterating `concept.getConceptMappings()` directly; hard-coded LOINC, SNOMED or UCUM codes; a Coding display taken from the concept name.
- **Seen in:** FM2-442 (SAME-AS only), FM2-501 (single-mapping fallback), FM2-604 (display on every system), FM2-623 (non-SAME-AS unit codes)

## J8 Frontend or REST client treats the first page as the whole result
A list endpoint is called without following `next`, so the default page size (50) or `maxResultsAbsolute` silently truncates worklists, concept lists and module lists. It works on demo data and fails at real sites.
- **While writing:** Follow `links.next`, or use `useOpenmrsPagination` or `useOpenmrsInfinite`, for any list that can grow. Never treat `results.length` as the total.
- **When reviewing:** An `openmrsFetch` of a list resource with no `limit`, `startIndex` or `next` handling; `.results` used as the full set in a count or filter.
- **Seen in:** O3-6102 (lab worklist showed first page only), form-engine-lib#458 (`useConcepts` capped at 50), esm-core@d6d451fd (Implementer Tools missed modules)
