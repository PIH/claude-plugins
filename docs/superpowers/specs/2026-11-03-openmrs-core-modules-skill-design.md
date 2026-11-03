# Design: `openmrs` plugin, skill for working in OpenMRS core and shared modules

Date: 2026-11-03
Status: draft for review

## Intent

PIH developers, and Claude working with them, regularly change code PIH doesn't solely own: openmrs-core and the shared "core" modules that the OpenMRS Reference Application ships. Mistakes there cost more than in PIH-owned repos. PIH-specific logic leaks into code other implementations depend on, changes break other implementations, features get duplicated across modules, fixes land on the wrong branch, and work skips the community process.

The skill records how PIH should work in that code, so Claude follows the same rules every PIH developer is expected to follow, and checks in with the user at the decisions that belong to them.https://github.com/PIH/claude-plugins/pull/3

## Audience and trigger

- **Who uses it:** PIH developers running Claude Code (and Claude itself).
- **When it fires:** any task that designs, changes, reviews, backports or releases code in openmrs-core or a core module (backend or O3 frontend). Also when a PIH task's requirements lead to changing one of those repos, even if the user hasn't said so yet.
- **When it doesn't fire:** routine work in PIH-owned repos (pihcore, pihemr, PIH distros, `@pih/esm-*` apps, PIH config). It also fires for an **upstream check** (the user's decision) when work in a PIH-owned repo is about to add logic generic enough that it probably belongs in a core module (for example, a new FHIR operation or a general-purpose service written into pihcore). See "Upstream check" below.

## What counts as "core"

A core module (the user's definition) is one that is **in the PIH distro *and* in either Reference Application distro**:

- **PIH distro:** the `omod.*` entries in pihemr's `distro/openmrs-distro.properties` (master).
- **O3 Reference Application** (`openmrs/openmrs-distro-referenceapplication`, branch `main`): the `omod.*` entries in `distro/distro.properties`, plus the O3 frontend modules in `frontend/spa-assemble-config.json`.
- **O2 Reference Application** (same repo, branch `2.x`): the `omod.*` entries in `package/src/main/resources/openmrs-distro.properties`.
- openmrs-core itself (`war.openmrs`) is always core.
- **O3 frontend:** PIH's `openmrs-frontend-pihemr` pulls every `@openmrs/esm-*` app at `next`, so any `@openmrs/esm-*` app in the O3 refapp's frontend list counts as core.

The skill tells Claude to **work this out live from those files**. It does not keep a hardcoded list, because the lists change.

For reference only (not to copy into the skill), on 2026-11-03 that rule gives these backend core modules: addresshierarchy, allergyui, appframework, appointments, appointmentscheduling, appointmentschedulingui, appui, attachments, authentication, bedmanagement, calculation, coreapps, emrapi, event, fhir2, htmlformentry, htmlformentryui, htmlwidgets, idgen, initializer, legacyui, metadatamapping, o3forms, openconceptlab, owa, queue, registrationapp, registrationcore, reporting, reportingrest, reportingui, spa, teleconsultation, uicommons, uiframework, uilibrary.

### Modules in the PIH distro but in neither refapp

These fall outside the rule above, so the skill lists them **explicitly** and says whether each follows the core rules. This is a deliberate exception to "no hardcoded lists": it records a team decision, and keeping it in the skill makes it easy for others to review and change.

**Treated as core (follow the core rules):**
- `authenticationui`

**Free to change (PIH-owned in practice; normal PIH workflow):**
- `dispensing`
- `edtriageapp`
- `emr`
- `growthchart`
- `labtrackingapp`
- `namephonetics`
- `paperrecord`
- `pihapps`
- `pihcore`
- `printer`
- `radiologyapp`

This split is the user's initial call and is **flagged for team review** (in the PR and in the plugin README's developer notes). If Claude finds a module in the PIH distro that is in neither refapp and in neither list (one was added since), it asks the user which list it belongs in and suggests updating the skill.

## Upstream check (for work in PIH-owned code)

When Claude notices that logic it is about to write in a PIH-owned repo looks generic, it pauses before building and does a **short, basic-level, read-only** investigation into how the work could be done upstream instead. Then it reports back and lets the user decide.

What the investigation covers:
- **Why upstream:** what makes the logic generic (not tied to PIH concepts, sites or workflows), and who else would plausibly use it.
- **Where it would go:** which core module (or openmrs-core) is the natural home, and why. Claude checks the core module list and looks at the candidate module's existing code and API.
- **Whether it already exists:** something equivalent or partial in a core module, an open upstream ticket or PR, or a Talk thread about it.
- **Standards:** the relevant FHIR resource or operation, if there is one.
- **How:** whether it would be big (Talk first) or small (straight to a ticket) under the rules below; who owns the module (OpenMRS or Bahmni); and the trade-off for PIH (for example, waiting on review and a release vs. shipping now in pihcore).

Bounds: a few quick lookups (code search, recent PRs and issues, a Talk or Jira search where accessible), not a deep design. Nothing is posted or filed. The report is short: a recommendation (upstream, PIH-only, or "PIH now, upstream later") with the reasons, ending with one question to the user. Claude doesn't run the full upstream process unless the user chooses it.

## Principles (the user's)

1. **Keep it generic.** Shared code holds logic any implementation could use. No PIH concepts, UUIDs, site names, workflows or shortcuts. PIH-specific behavior belongs in PIH modules or configuration. Where a feature needs local variation, make it configurable (global property, Initializer-loadable config, frontend config schema).
2. **Base it on standards.** When designing a new feature, look to **FHIR** first for resources, terminology and semantics. Don't invent a model when a standard one exists.
3. **No breaking changes.** Existing behavior must keep working for other implementations. That covers Java API signatures, REST/FHIR request and response shapes, database schema, global property defaults, frontend extension points and config schemas. If a change genuinely has to break something, Claude stops and sends it through the community (Talk) rather than finding a workaround.
4. **Check that it doesn't already exist.** Before building a feature, check whether it exists, fully or partly, in another core module. If it does, **extend that module by default.** Building a separate version needs a stated reason (for example: the existing module is unmaintained, can't accept the change, or targets a different UI stack), and Claude raises it with the user before going that way.

## Process (the user's)

### PIH ticket first, always

- There is **always** a PIH ticket (UHM, HAI, and so on) that links to the upstream ticket. Usually the PIH ticket exists before work starts and defines the requirements.
- Claude reads the PIH ticket's requirements before starting, then classifies the change as big or small (below). If there's no PIH ticket, Claude says so and asks the user to create or point to one before upstream work begins.

### Big vs. small

Test: *would a maintainer be surprised to receive this PR with no discussion first?*

**Big: Talk post first** if any of these apply:
- New API surface: a REST or FHIR resource or operation, a new domain object, a new service method other modules will use.
- Data model changes: new tables or columns, or changes to existing ones.
- A change to default behavior other implementations would notice, even when it isn't strictly breaking.
- It spans several core modules, or it isn't obvious which module it belongs in.
- It deprecates or replaces something.
- A new module, or code moving between modules.
- A real design choice the community might want a say in (which FHIR mapping, where config lives).

**Small: straight to an upstream ticket:**
- A bug fix that makes code do what it was already meant to do.
- A small enhancement that is off by default or opt-in.
- Performance work, tests, docs or refactors with no behavior change.
- Following through on an approach already agreed on Talk or in an existing ticket.

**Tie-breaker:** if Claude can't tell, it says why and asks the user.

When a change is big, Claude tells the user why (for example "this adds a new FHIR resource") and offers to draft the Talk post.

**After the Talk post, Claude stops (the user's decision).** No coding, prototyping or draft PR on a big change until the discussion settles, unless the user explicitly approves going further. Claude asks; it doesn't assume.

### Talk posts

- Big changes go to OpenMRS Talk (talk.openmrs.org), tagging the key OpenMRS BAs and developers for that area.
- Claude **drafts** the post. It never posts it; the user does.
- Claude suggests who to tag based on recent activity in that area (recent PR authors and reviewers, recent Talk threads) and **confirms with the user**. No names are hardcoded in the skill.

### Tickets, branches and PRs

- Follow the standard OpenMRS pattern: a ticket in the right OpenMRS Jira project, a branch named for the ticket, and commit and PR titles prefixed with the ticket key (`TRUNK-1234: ...`). The PR links to the ticket, and the PIH ticket links to the upstream ticket.
- Because each repo has its own norms (Jira project key, fork vs. branch, PR template), Claude **checks recent merged PRs in that repo** and follows what it sees, rather than assuming.

### Reviewers

- Claude looks at who is currently reviewing and merging in that repo (recent merged PRs, CODEOWNERS where present), **suggests** a reviewer, and **confirms with the user** before requesting anyone. It never requests a review on its own.

### Backports

- Backport only to the **maintenance branches PIH actually runs**.
- **pihemr family** (pihemr and the distros built on it: zl-emr, ces-emr, lesotho-emr, pihsl-emr, pihliberia-emr, …): versions come from the **pihcore `pom.xml` on master** (`openMRSVersion`, `emrapiVersion`, `fhir2Version`, and so on), which pihemr-distro inherits. As of this design every family distro builds on the pihemr master SNAPSHOT (`parentVersion` in each distro's pom), so pihcore master is the single source. Claude confirms that still holds (a distro pinning an older pihemr release would add its versions too). Claude works out the target branch from those versions.
- Which modules PIH runs at all comes from pihemr's `distro/openmrs-distro.properties`. A core module not listed there isn't run by PIH and needs no backport.
- **Rwanda** (`openmrs-distro-rwandaemr`) pins its own versions. It counts, but separately: Claude always asks explicitly, *"Do we need to backport to the Rwanda versions as well?"*
- **O3 frontend:** PIH's `openmrs-frontend-pihemr` (`spa-build-config.json`) pulls `@openmrs/esm-*` apps at `next`, so frontend changes normally need no backport. Claude only raises a frontend backport if that config pins a version.
- Versions are read live from those files, never kept in the skill.

### Releases

- Claude **never cuts a release on its own.** It can say a release is needed and prepare for it, but asks the user first, every time.

## Bahmni-owned core modules

Some core modules are owned by Bahmni, not OpenMRS. Today that's `appointments` and `teleconsultation` (groupId `org.bahmni.module`, repos under github.com/Bahmni). Claude identifies them by groupId or repo owner, not by a fixed list.

The same design principles apply. The process differs:

| | OpenMRS-owned | Bahmni-owned |
|---|---|---|
| Upstream ticket | OpenMRS Jira (TRUNK, O3, …) | **BAH** ticket in Bahmni's Jira (bahmni.atlassian.net, separate account). GitHub Issues is enabled on the repos but effectively unused and unwatched, so don't rely on it. |
| PR title | `TRUNK-1234: description` | `BAH-1234 \| Fix. description` (check recent PRs for the current form) |
| First PR | — | CLA Assistant asks the contributor to sign a CLA |
| Discussion | Talk | Talk, Bahmni category, tagging the Bahmni core team |
| Reviewers/mergers | OpenMRS reviewers | Almost entirely the Bahmni team; check recent merged PRs |
| Review speed | Varies | Outside PRs often sit for months. Flag this early so the PIH ticket can plan around it. |
| Release | PIH may cut it (after asking the user) | Only Bahmni can release (their GitHub workflow). PIH has to ask them. |
| Backports | Maintenance branches PIH runs | Effectively master only; a backport needs Bahmni's agreement |

If a PIH developer can't create a BAH ticket, the fallback is a Talk post in the Bahmni category asking for one, not a GitHub issue.

## Goals

- Claude applies the four principles whenever it designs or changes core code.
- Claude follows the PIH-ticket → big/small → Talk-or-ticket → PR → review → backport → release flow, and stops for the user's decision at each point listed below.
- All volatile facts (module lists, versions, reviewers, ticket key conventions) are discovered live from their source, never copied into the skill.

## Points where Claude must stop and ask

1. No PIH ticket exists.
2. A change is big (offer to draft a Talk post), or Claude can't tell whether it's big or small.
3. A change would be breaking, or would build a separate version of something that already exists in a core module.
4. Who to tag on Talk, and who to request as reviewer.
5. Whether to backport to Rwanda.
6. Any release.
7. Anything public or outward-facing.

**Hand-off rule (the user's decision):** Claude never carries out public steps itself, even after approval. It prepares them and hands them to the user: Talk posts, upstream Jira tickets (OpenMRS or BAH), links between PIH and upstream tickets, opening PRs, requesting reviewers, PR comments, and releases. "Prepare" means ready-to-paste text (ticket title and description, PR title and body, Talk post) plus the exact command where one applies (for example a `gh pr create ...` line), so the user can run it themselves. Local work (branches, commits, builds, tests) is fine. Pushing a branch counts as outward-facing, so Claude asks first.

## Non-goals

- Not a general OpenMRS developer tutorial (build setup, SDK usage, coding style). Link to OpenMRS docs where useful instead.
- Not a list of people, versions or modules (except the explicit list of non-refapp PIH-distro modules above).
- Not covering PIH-owned repos, except to redirect generic requirements upstream.
- No automation that posts, opens PRs, files tickets, assigns reviewers or releases. Claude prepares; the user acts.

## Anti-goals (failure even if it "works")

- Claude quietly puts PIH-specific logic in shared code because it was the quickest path.
- Claude acts on its own at a decision point listed above.
- The skill goes stale because it hardcoded a version, branch, module list or reviewer.
- The skill grows into a long essay that gets skimmed. It should read as a short set of rules plus where to look things up.

## Packaging (decided)

- A new plugin, `openmrs`, in `PIH/claude-plugins`, next to `ocl`. Initially one skill.
- Follow the repo's "Adding a new plugin" steps: `plugins/openmrs/.claude-plugin/plugin.json` (version 0.1.0, MPL-2.0), `plugins/openmrs/README.md`, the marketplace entry and the README table row. Validate with `claude plugin validate`.
- The repo is public: no personal names, ticket numbers, tokens or patient or employee data in the skill.
- Note: SKILL.md edits fail in Claude Code auto mode; the author needs to switch modes to write it.

## Left to the builder

- Skill name and exact wording of the `description` (it must trigger on work in openmrs-core, core omods and `@openmrs/esm-*` apps, and on PIH requirements that lead there).
- How to structure the body: a single SKILL.md, or SKILL.md plus a `references/` file (for example for the Bahmni table), as long as the main file stays short.
- The exact commands for live lookups (`gh api` vs. local checkout).
- README examples and troubleshooting.
- Whether to add a few evals now or later.
