# O3 frontend (P1-P9)

Starred categories (★) recur across many years or many reviews. Read them first. Covers esm-core, patient-chart, patient-management, form-engine-lib, form-builder, laboratory and dispensing. Also see J8 (first REST page), H8 (timezones) and K9 (form-engine state).

## P1 ★ Implementer config, extension and slot name contracts broken without migration
Implementers' `config.json` refers to config keys, extension names, slot names and app names. Renaming or moving them in a BREAKING release makes the old config inert or turns it into "unknown key" errors. Nothing translates the old shape.
- **While writing:** Treat config keys, extension names, slot names and app names as public API. Add the new key and still read the old one with a deprecation warning. List every renamed or removed key in the release notes and in a migration section of the PR. Flag BREAKING.
- **When reviewing:** Diffs to `config-schema.ts` or `routes.json`; renamed extension or slot `name` values. Ask what happens to an existing `config.json` that uses the old name.
- **Seen in:** esm-core@aeb84872 (`extensionSlots` replaced `extensions`), patient-chart@3599b4e95 then patient-chart@d1833f1cd (app renamed twice), patient-management@49b24250 (all schemas "standardized"), O3-2287 (valid keys reported as unknown before their module loaded)

## P2 ★ Missing SWR invalidation after writes
A save in one workspace does not `mutate` the SWR keys other widgets read. Keys are often built differently (reps or params), so another widget shows pre-save data until refresh. Turning off automatic revalidation in 2024 made every missing `mutate` visible.
- **While writing:** Every write path calls a shared, named invalidation helper (for example "invalidate visit"). Build SWR keys with one exported key builder per resource so writers and readers match.
- **When reviewing:** For each `openmrsFetch(..., { method: 'POST' | 'DELETE' })`, check which `mutate` runs on success, and that its key matches what other widgets, including in other apps, subscribe to.
- **Seen in:** O3-2159 (visits table stale after encounter edit), O3-4346 (lab results not shown until refresh), O3-5381 (saved form showed "Never" completed), patient-chart@92a52ea10 (revalidation consolidated into one function)

## P3 ★ Ambient context used instead of the record's own context
Code reads the "current" patient, active visit or queue entry from a global store instead of the one attached to the record being edited. Edits attach to the wrong visit, stale context survives navigation or deletion, and actions pass the wrong patient.
- **While writing:** When editing an existing record, derive visit, patient and location from the record itself. Use ambient context only for new records, and clear it on patient change, logout and visit end.
- **When reviewing:** `useVisit()`, `activeVisit` or `currentVisit` in an edit path; workspace props that do not carry `patientUuid` and `visitUuid` explicitly.
- **Seen in:** O3-5447 (editing an old encounter used the active visit), O3-4707 / O3-4844 (visit context stale after create or end), O3-4374 (queue "Start a Visit" passed no patient), O3-5461

## P4 ★ Paginated or sorted rows indexed back into the source array
Table rows are built from a page slice or sorted copy, and action handlers use the row index or a generated row id to look up `data[index]`. On page 2 or after sorting, the handler opens, edits or deletes a different record. This is a patient-safety bug.
- **While writing:** Use the record's uuid as the DataTable row id and look records up by uuid, never by index. Compute per-row derived data (such as warnings) from the record, not the page position.
- **When reviewing:** `data[index]`, `rows.indexOf` or `findIndex` on the full list inside a row action; `id: index` in a `rows` map.
- **Seen in:** O3-2257 / O3-2280 (page 2 opened the wrong patient), patient-chart@770e1f73e (programs menu edited the wrong enrollment), O3-5321 (wrong medication loaded), O3-2969

## P5 ★ Non-idempotent submit: double-click, retry and partial multi-request saves
Save is not disabled while a request is in flight, or a save is a chain of POSTs (patient, identifiers, relationships, obs) with no compensation. A double-click or a retry after partial failure creates duplicate encounters, results, identifiers or orders, or reports success early.
- **While writing:** Disable submit while a request is in flight (`isSubmitting`). Make each step of a multi-request save safe to retry: reuse generated ids and uuids, send only changed obs. Report success only after every request settles.
- **When reviewing:** An `onSubmit` with several awaits or a `Promise.all` of POSTs. Ask what a second click does and what a retry after a failed third call does.
- **Seen in:** O3-6100 (double-click created duplicate vitals encounters), O3-6004 (retry duplicated lab results), O3-5916 (retried registration generated new identifiers), O3-3587 (editing an ID created a second OpenMRS ID)

## P6 Translated display text used as a value or logic key
Code switches on, compares or saves the translated label (`t('severe')`, a concept `display`, a unit name) instead of a stable key or uuid. It works in English; in other locales the logic breaks or localized text is written back as data.
- **While writing:** Keep the value (uuid or enum key) and the label separate. Call `t()` only at render time. Never `.toLowerCase()` or compare a translated string.
- **When reviewing:** `t(...)` results stored in state, sent in a payload or used in `switch` or `===`; comparisons against `concept.display` or `name.display`.
- **Seen in:** O3-4403 (allergy form could not be saved in French), O3-3592 (packaging unit saved in French), O3-2602

## P7 Over-broad REST representations and fetch-heavy renders
Hooks request `v=full` or wide custom reps "just in case", and bundle data every form loads. With per-row hooks, lists and forms get slow on real data. Trimming a rep can then break consumers that needed a dropped field.
- **While writing:** Request a custom rep listing exactly the fields the component renders. Lazy-load detail and large static data. Avoid one fetch per row.
- **When reviewing:** `v=full` or nested `:full` reps in list hooks; a new hook inside a per-row component. When a rep is trimmed, grep every consumer of that hook for the removed fields.
- **Seen in:** O3-5693 (queue rep trimmed to what the table renders), O3-1900 (registration form took 37 s first load), O3-6025 (1.3 MB growth tables bundled into every form), laboratory-app@8f13405 (trim dropped a needed field)

## P8 Shared runtime and dependency version skew; global CSS leaks
Apps declare shared libraries (swr, i18next, React) and backend dependency ranges independently of the app shell. A mismatch loads two copies, a caret range rejects a new backend major, and CSS from one app leaks into others.
- **While writing:** Keep shared singletons on the app-shell version through peer dependencies. Give `backendDependencies` an explicit upper bound you widen on purpose for each platform major. Use CSS modules or scoped selectors only.
- **When reviewing:** `dependencies` vs `peerDependencies` changes for react, swr, i18next or `@openmrs/*`; `backendDependencies` ranges in `routes.json`; un-namespaced selectors in `.scss`.
- **Seen in:** dispensing@a892b0a (swr pinned to match the app shell), laboratory-app@8f14c61 (caret range excluded webservices.rest 3.x), form-engine-lib#798 (global CSS leaked), esm-core@4f62c38c (single i18next instance)

## P9 Tablet layouts that block clinical actions; upload limits hard-coded in the UI
Features are built at desktop width. On a tablet the Save button is off-screen or the workspace cannot scroll, so the task cannot be completed. Upload limits and allowed extensions are hard-coded in the UI while the server enforces different ones.
- **While writing:** Check every new workspace and form at `useLayoutType() === 'tablet'` and a narrow viewport. Keep action buttons in the sticky workspace footer. Read upload limits and allowed extensions from server configuration, in one place, and normalize formats (".png" vs "png") in one helper.
- **When reviewing:** New fixed heights, `overflow: hidden` or absolute positioning in workspace SCSS (ask for a tablet screenshot); hard-coded size or extension lists in the frontend; string comparison on MIME types.
- **Seen in:** O3-2530 / O3-2526 (Save and Close not visible on tablet), O3-2856 (Indication field truncated, blocked drug orders), O3-4488 (chart could not scroll), O3-5988 (UI size limit unrelated to the server setting)
