---
name: core-modules
description: How PIH works in OpenMRS code it doesn't solely own, meaning openmrs-core and the shared "core" modules (backend omods like emrapi, fhir2, webservices.rest, coreapps, htmlformentry, reporting, idgen, registrationcore, appointments, queue, and O3 frontend apps like esm-patient-chart). Use it whenever designing, changing, reviewing, backporting or releasing code in openmrs-core, an OpenMRS or Bahmni module, or an @openmrs/esm-* app; when a PIH ticket's requirements lead to an upstream change; when the talk is of "upstream", OpenMRS Talk, OpenMRS or BAH Jira tickets, backports or module releases; and when work in a PIH-owned repo (pihcore, pihemr, PIH config, @pih/esm-* apps) is about to add logic generic enough to belong upstream.
---

# Working in OpenMRS core and shared modules

Code in openmrs-core and the shared core modules is used by many implementations besides PIH. A shortcut that's fine in pihcore can break someone else's system, duplicate another module, or skip the community's process. This skill sets the rules for that code. It also marks the decisions that belong to the user, not to Claude.

## What counts as "core"

A module is core if it's **in the PIH distro and in either the O3 or the O2 OpenMRS Reference Application**, plus openmrs-core itself and the `@openmrs/esm-*` apps in the O3 refapp. Work this out live from the distro files: pihemr `distro/openmrs-distro.properties` (master); the refapp repo `openmrs/openmrs-distro-referenceapplication`, with `distro/distro.properties` and `frontend/spa-assemble-config.json` on `main` (O3) and `package/src/main/resources/openmrs-distro.properties` on `2.x` (O2). [references/module-classification.md](references/module-classification.md) has `gh api` recipes.

**PIH-distro modules in neither refapp** (an initial team decision; change it by PR):
- Treated as core: `authenticationui`
- Free for PIH to change: `dispensing`, `edtriageapp`, `emr`, `growthchart`, `labtrackingapp`, `namephonetics`, `paperrecord`, `pihapps`, `pihcore`, `printer`, `radiologyapp`
- Any other PIH-distro module in neither refapp is **unclassified**. Don't guess: tell the user, ask which list it belongs in, and suggest a PR to update this skill.

Bahmni owns some core modules (groupId `org.bahmni.module` or GitHub owner `Bahmni`, for example appointments). The same rules apply, but the process differs. **Whenever work touches a Bahmni module, tell the user all three of these up front,** even if the conversation is only about where to file:
- The upstream ticket is a **BAH** ticket in Bahmni's Jira (bahmni.atlassian.net). GitHub Issues is effectively unused there, so don't open one. If the user can't create a BAH ticket, draft a Talk post (Bahmni category) asking for one.
- A first PR to a Bahmni repo triggers a **CLA** (Contributor License Agreement) check.
- Reviews of outside PRs can take months, and **only Bahmni can release**. Say so early so the PIH ticket can plan around it.

Details are in [references/bahmni.md](references/bahmni.md).

## The rules for core code

1. **Keep it generic.** No PIH concepts, UUIDs, sites, workflows or shortcuts. Put PIH-specific behavior in PIH modules or configuration. Where implementations need to differ, make it configurable: a global property, config Initializer can load, or a frontend config schema.
2. **Base it on standards.** For a new feature, look to **FHIR** first for resources, terminology and semantics. Don't invent a model when a standard one exists.
3. **No breaking changes.** Existing behavior must keep working for other implementations. That covers Java API signatures, REST and FHIR request and response shapes, database schema, global property defaults, frontend extension points and config schemas. If a change genuinely has to break something, stop. It goes to the community on Talk, not into a workaround.
4. **Check that it doesn't already exist.** Before building, look for the feature, in full or in part, in other core modules, and for open upstream tickets, PRs or Talk threads. If it exists, **extend that module by default.** Building a separate version needs a stated reason (for example: the existing module is unmaintained, can't accept the change, or targets a different UI stack), and you raise it with the user before going that way.

## Upstream check (for work in PIH-owned code)

When logic you're about to write in a PIH-owned repo looks generic (not tied to PIH concepts, sites or workflows), pause before building and do a short, read-only investigation:

- **Why upstream:** what makes it generic, and who else would plausibly use it.
- **Where:** name the specific core module (or openmrs-core) you'd propose as the home, and why, based on its existing code and API.
- **Already there?** Equivalent or partial work in a core module, or an open ticket, PR or Talk thread.
- **Standards:** the relevant FHIR resource or operation, if any.
- **How:** big or small (below), who owns the module (OpenMRS or Bahmni), and the trade-off for PIH (waiting on upstream review and a release vs. shipping now in PIH code).

Keep it to a few quick lookups, not a design, and post nothing. Report briefly with a recommendation (upstream, PIH-only, or "PIH now, upstream later") and the reasons, then ask the user to choose. Run the full process below only if they choose upstream. Modules that are free to change still get this check.

## Process

### 1. PIH ticket first

There is always a PIH ticket (UHM, HAI, …) that defines the requirements and links to the upstream ticket. Read it before starting. If there isn't one, say so and ask the user to create one, or point you to it, before upstream work begins.

### 2. Big or small?

Ask: *would a maintainer be surprised to get this PR with no discussion first?*

**Big: post on Talk first** if any of these apply:
- New API surface: a REST or FHIR resource or operation, a new domain object, a new service method other modules will use.
- Data model changes: new tables or columns, or changes to existing ones.
- A change to default behavior other implementations would notice, even when it isn't strictly breaking.
- It spans several core modules, or it isn't obvious which module it belongs in.
- It deprecates or replaces something.
- A new module, or code moving between modules.
- A real design choice the community might want a say in (which FHIR mapping, where config lives).

**Small: go straight to an upstream ticket:**
- A bug fix that makes code do what it was already meant to do.
- A small enhancement that is off by default or opt-in.
- Performance work, tests, docs or refactors with no behavior change.
- Following through on an approach already agreed on Talk or in an existing ticket.

If you can't tell, say why and ask the user.

**For a big change:** tell the user why it's big (for example "this adds a new FHIR operation") and offer to draft the Talk post on OpenMRS Talk (talk.openmrs.org), tagging the key OpenMRS BAs and developers for that area. Suggest who to tag from recent activity (recent PR authors and reviewers in the module, recent Talk threads), confirm with the user, and never hardcode names. **Then stop.** Don't code, prototype or open a draft PR until the discussion settles, unless the user explicitly approves going further.

### 3. Tickets, branches, PRs

Follow the standard OpenMRS pattern: a ticket in the right OpenMRS Jira project, a branch named for the ticket, and commit and PR titles prefixed with the key (`TRUNK-1234: ...`). Link the PR to the ticket, and the PIH ticket to the upstream ticket. Repos differ (Jira key, fork vs. branch, PR template), so check recent merged PRs in that repo and follow what you see. Bahmni modules use BAH tickets instead.

### 4. Reviewers

Look at who is currently reviewing and merging in the repo (recent merged PRs, CODEOWNERS if present). Suggest a reviewer and confirm with the user. You never request a review yourself.

### 5. Backports

Backport only to the maintenance branches PIH actually runs.

- **pihemr family** (pihemr and the distros built on it: zl, ces, lesotho, pihsl, pihliberia, …): the versions are in **pihcore's `pom.xml` on master** (`openMRSVersion`, `emrapiVersion`, `fhir2Version`, …). pihemr-distro inherits them. First confirm that each family distro's `parentVersion` still points at the pihemr master SNAPSHOT. A distro pinned to an older pihemr release adds that release's versions to the list. Work out the target branches from the versions.
- **Which modules PIH runs:** pihemr's `distro/openmrs-distro.properties`. A module not listed there needs no backport.
- **Rwanda** (`PIH/openmrs-distro-rwandaemr`) pins its own versions. Always ask, as a separate question: **"Do we need to backport to the Rwanda versions as well?"**
- **O3 frontend:** PIH pulls `@openmrs/esm-*` apps at `next`, so normally no backport is needed. Raise one only if PIH's frontend config pins a version.

Read versions from those files every time; never from memory.

### 6. Releases

Never cut a release on your own. You may say a release is needed and prepare it, but ask the user first, every time.

## Hand-off: Claude prepares, the user acts

Claude never carries out public steps, even after approval, and never offers to (say "I'll draft the ticket", not "I'll open the ticket"). That covers Talk posts, upstream Jira tickets (OpenMRS or BAH), links between PIH and upstream tickets, opening PRs, requesting reviewers, PR comments and releases. Prepare them as ready-to-paste text (ticket title and description, PR title and body, Talk post) plus the exact command where one applies (for example a `gh pr create ...` line), and hand them to the user. Local work (branches, commits, builds, tests) is fine. Pushing a branch is outward-facing, so ask first.

## Stop and ask when

1. There's no PIH ticket.
2. A change is big (offer the Talk draft, then stop), or you can't tell whether it's big or small.
3. A change would be breaking, or would build a separate version of something that already exists in a core module.
4. You need to choose who to tag on Talk or who to request as reviewer.
5. A Rwanda backport might be needed.
6. A release is needed.
7. Anything is public or outward-facing.
8. A PIH-distro module is in neither refapp and not on either list in the classification reference.
