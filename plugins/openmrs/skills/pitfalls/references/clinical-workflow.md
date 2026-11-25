# Clinical workflow and domain lifecycle (M1-M6)

Starred categories (★) recur across many years or many reviews. Read them first. Covers queues, beds, appointments, visits and ADT (emrapi, coreapps, queue, bedmanagement, appointments, event, attachments).

## M1 ★ Workflow entities not cascaded from the parent lifecycle
Queue entries, bed assignments and appointments hang off a visit or patient, but each module handles only its own create and update path. When the visit ends or is voided, or the patient is voided or merged, the child stays "active", so UIs show blank rows, invariants like "one active bed per patient" break, and NPEs follow.
- **While writing:** For every child workflow entity, list the parent events (visit end, void, delete, patient void, merge) and handle each in the service layer, not the REST layer. Enforce invariants such as "one active per patient" in a validator or DB constraint, not in one service method.
- **When reviewing:** A new entity with a `visit` or `patient` FK and no void, end or merge handling; duplicate checks that do not exclude rows being voided in the same flush.
- **Seen in:** O3-4416 / O3-4916 (queue entries not ended with the visit), O3-5955 (voided patients still in queues), BED-26 (several active bed assignments reachable through a SaveHandler or merge action), BAH-1209 then AP-83 (voided or merged patients NPE the appointments view)

## M2 ★ Changing encounter date or visit without propagating to children
Code that moves `encounterDatetime` (attach to visit, retro entry, back-dating) or rewrites obs on edit treats the encounter as one field. Children with their own dates (obs, group members, order `dateActivated`, diagnoses) become inconsistent, or are voided and recreated, which duplicates data.
- **While writing:** Change encounter dates only through one helper that updates every child carrying a datetime (obs including group members, orders, diagnoses, conditions). Update only fields that changed, so core does not void and recreate obs.
- **When reviewing:** `setEncounterDatetime` or `setObsDatetime` outside the helper; edit paths with no assertion on obs and order counts after a round-trip edit.
- **Seen in:** EA-3 (attachToVisit did not update obs), EA-220 (visit assignment shifted encounter dates but not order dates, 11 years later), EA-111 (diagnosis obsDatetime overwritten, so obs voided and recreated), HTML-834

## M3 Visit and ADT state derived from encounters
"Is the patient admitted", "the active visit" and "visit stop time" are computed from encounter lists. Bugs: counting the encounter being saved, exact-timestamp boundaries, voided encounters, dates outside the visit, two requests racing to create a visit.
- **While writing:** Derive state with an explicit "as of" time and an explicit exclusion of the encounter being saved. Filter voided encounters. Define inclusive and exclusive boundaries. Pass the visit explicitly instead of looking up "the active visit" in UI flows. Apply submission side effects once, inside the encounter's save.
- **When reviewing:** New `VisitDomainWrapper` or ADT predicates need tests for an encounter at exactly the boundary, the encounter under save, voided encounters and two overlapping visits. Strict new validators need an existing-data audit (see F4).
- **Seen in:** EA-226 (ADT validator self-inclusion, range and boundary fixes, then reverted), RA-231 (two simultaneous active visits, service bypassed), EA-133 then EA-175 (voided encounters miscounted in the stale-visit close)

## M4 Status state machines driven by scheduled tasks and bulk actions
Statuses (Missed, Completed, Cancelled, ended) are set in bulk by a nightly task, a "delete block" action or a conflict query using only a time predicate, ignoring current state, window or terminal states. They close live entries or block valid bookings.
- **While writing:** Write transitions as an explicit from-to table. Bulk jobs filter on the from-state and a window relative to run time. Make a multi-step transition (end source, create target) one transaction that validates first.
- **When reviewing:** `UPDATE ... SET status/ended_at WHERE date < now()` with no status filter; scheduler tasks that run at startup; conflict queries that do not exclude terminal states.
- **Seen in:** O3-2443 (auto-close task ended all open queue entries, including new ones), AM-57 (deleting a block cancelled past appointments), AP-64 (cancelled appointments counted as conflicts), O3-4985 (failed transition left the patient in no queue)

## M5 Event emission tied to specific write paths
Events are raised by AOP advice on chosen service methods or by a Hibernate interceptor. Any other write path (recurring series, another REST resource, FHIR, subclasses, detached saves) emits nothing or the wrong entity, so downstream sync drifts.
- **While writing:** Emit from the persistence layer, or enumerate every write path in a test that asserts one event per entity change. Do after-commit work in a new transaction.
- **When reviewing:** New save paths (batch, recurring, FHIR, alternate REST resources) on entities fed to Atomfeed or the event module; pointcuts naming a single method; listeners that write during `afterTransactionCompletion`.
- **Seen in:** BAH-1013 (recurring appointments raised no events), BAH-1220 (only the encounter endpoint was advised), EVNT-22 / EVNT-23 (AOP missed paths, then subclasses), EVNT-34 (detached saves fire no update)

## M6 Module privilege definitions drift
A privilege is declared in `config.xml` or inserted by Liquibase, referenced by a string constant, and granted by migration. They drift: different spellings, copied UUIDs, a privilege created twice, or new requirements without grants, so users are locked out or the change is reverted.
- **While writing:** Declare each privilege once (`config.xml`), keep one constant per name, generate a fresh UUID. Ship every new privilege requirement with a role-grant migration keyed on an existing equivalent privilege.
- **When reviewing:** String literals in `@Authorized` or `hasPrivilege` that do not match `config.xml` exactly; hand-typed or copied UUIDs (including the well-known example UUID); privilege inserts in Liquibase with no precondition; new `@Authorized` on existing endpoints without grants.
- **Seen in:** ATT-56 ("Create Attachment" vs "Create Attachments"), O3-3002 (new privilege reused another's uuid; reverted twice for missing grants), BAH-4321 (moved from Liquibase to `config.xml`), BED-40
