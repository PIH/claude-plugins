# Forms (K1-K9)

Starred categories (★) recur across many years or many reviews. Read them first. Covers htmlformentry (HFE), htmlformentryui, o3forms and the O3 form engine.

## K1 ★ Edit-mode obs-group matching is heuristic
Stored obs carry no link to the form field that made them, so edit and view mode rank existing obs groups against the form's schema. A new obs-group feature the matcher does not know puts existing data in the wrong slot, and on save it is voided or duplicated.
- **While writing:** Any change to what an obs group emits (members, hidden obs, answers) must update the edit-mode matcher in the same change. Add a regression test with two or more sibling groups sharing the grouping concept.
- **When reviewing:** New obs-group attributes with no change to the matching or ranking code and no `testEditEncounter` or `testViewingEncounter` coverage.
- **Seen in:** HTML-78, HTML-216 (introduced the ranking algorithm), HTML-806 (repeated groups with checkboxes), HTML-826 (hidden obs ignored by the matcher)

## K2 ★ Edit round-trip must be lossless
Each widget must render an existing value in exactly the format its submission parser expects. Otherwise opening a form in edit mode and pressing Save silently rewrites data.
- **While writing:** For every new widget or tag, add a test that enters data, opens in edit, re-submits unchanged, and asserts identical persisted values (including `obs_datetime`, value type and time).
- **When reviewing:** `setInitialValue` or `getValue` formats that differ from what `handleSubmission` parses; defaults applied when an existing value is null instead of only in ENTER mode.
- **Seen in:** HTML-769 (drug answer turned into an arbitrary coded value), HTML-297 (defaults re-filled cleared fields), HTML-849 (active RENEW became EDIT), HTML-765 (values no longer in the answer list were dropped)
- **Module twist:** In the O3 engine, unchanged obs values created duplicate obs on edit (form-engine-lib#842); send only changed obs.

## K4 ★ Encounter date, not "now", is the reference
Forms are often entered retrospectively, so future, overlap and enrollment checks and defaults must be relative to the encounter datetime and visit bounds. Code defaults to `today()`, checks only the date part, or validates after the change was applied.
- **While writing:** Take the reference date from `FormEntryContext` (encounter datetime or visit). Validate before mutating anything. Check in edit mode too.
- **When reviewing:** `new Date()` or `today()` in a submission element or validator; checks applied only in ENTER mode.
- **Seen in:** HTML-4 (allowFutureDates relative to today), HTML-822 / HTML-824 (order-overlap and enrollment used the wrong date), HTML-873 (edit mode did not check the visit)

## K9 ★ Form-engine state leaks into submissions; expression evaluator semantics (O3)
Values the UI no longer shows (hidden obs-group children, cleared orders or diagnoses, deleted repeat rows) are still submitted. The custom expression evaluator also differs from JavaScript, so expressions in form JSON break.
- **While writing:** Build the payload from visible, current field state only, by walking the rendered field tree. Clear dependent state on hide, clear and delete. Add evaluator tests for each JS construct form authors use.
- **When reviewing:** For hide, disable, repeat or payload-builder changes, ask for a test that fills a field, hides or clears it, and asserts the payload. For evaluator changes, tests on member access, arrow functions and whitespace-free expressions.
- **Seen in:** O3-6030 / form-engine-lib#822 (hidden members submitted), O3-6027 / form-engine-lib#826 (cleared orders submitted), O3-6092 (evaluator returned `String.prototype` properties)

## K3 Void-and-replace on edit
Edits must void the old row and create a new one (with `previous_version`, child voiding and empty-parent cleanup), not mutate the persisted entity. Shortcuts lose history or leave orphan and empty groups.
- **While writing:** On edit, void and create through one code path that handles children, `previous_version` and empty parent groups. Never set fields on a loaded entity that should stay historical.
- **When reviewing:** `existing.setX(...)` on an Obs, Condition, PatientState or Order inside a submission element; hand-rolled void loops; edit paths with no "both rows correct" assertion.
- **Seen in:** HTML-828 (condition edit changed both rows), HTML-675 (no `previous_version`), HTML-805 / HTML-811 (manual voiding skipped child obs), HTML-425 (empty parents not voided)

## K5 JS field-accessor contract and composite widgets
Form authors script fields through generated accessors (`fieldId.value`, `.date`, `.error`). Composite widgets (date plus time, display plus hidden inputs) that register or fire events differently break existing form JavaScript.
- **While writing:** Register a composite widget's accessors on the outer handle. Fire `change` on the element the accessor points to. Never overwrite shared global helpers such as `setValue`.
- **When reviewing:** New `registerWidget` calls for sub-widgets; changes to the datepicker setup or hidden and display input ids; JS that redefines `setValue` or `getValue`.
- **Seen in:** HTML-469 / HTML-851 (wrong DateTime handles, fixed 12 years later), HTML-802 (datepicker did not fire change), HTML-649 (relationship tag overwrote `setValue`)

## K6 Host renderers diverge
The same form runs in legacy HFE pages, htmlformentryui, flowsheets and previews, and in O3 under two engines. A fix in one layer regresses or misses another.
- **While writing:** Put form-semantic logic (dates, defaults, visit) in HFE Java, not host-page JS. Test in every host renderer.
- **When reviewing:** HFEUI `.gsp` or `.js` changes that set field values; HFE changes that assume one host page.
- **Seen in:** HTML-817 (HFEUI JS reset the edit-mode date to today), HTML-557 (Velocity context missing in HFEUI view mode), HTML-895 (flowsheet submitted the header form), O3-3534 / O3-3746 (two "form by name" lookups)

## K7 Per-tag metadata lookups make large forms slow
Each tag resolves its metadata alone (concept by mapping, all providers, all drugs, message bundles) with no batching or memoization, so large forms make thousands of calls.
- **While writing:** Resolve metadata through a per-session cache. Never load an unbounded class or list at render time.
- **When reviewing:** `getConceptByMapping`, `getAllProviders`, `getConceptsByClass` or `getAllDrugs` inside handler `getSubstitution` or widget constructors.
- **Seen in:** HTML-696 (1000+ mapping lookups, about 48 s per load), HTML-203, HTML-484

## K8 Form definition changes vs collected data and exports
Changing answer lists, macros or subforms, or retiring and republishing a form, must not make existing encounters unviewable or break export and form resolution.
- **While writing:** Treat form markup as data that outlives its tags. Unknown or legacy values must still render in view and edit mode. Resolve forms deterministically (published, non-retired, latest).
- **When reviewing:** Answer filtering that drops existing values; form lookups that `get(0)` a name search; attributes the exporter or schema viewer does not know.
- **Seen in:** HTML-765, HTML-136 / HTML-177 (export missed macro and includeIf dependencies), o3forms@57d4f95 (by-name resolution returned retired forms)
- **Module twist:** Submission side effects (patient, program, relationship) must be queued in the session's single save and mode-checked (HTML-377, HTML-418, HTML-820); see M3.
