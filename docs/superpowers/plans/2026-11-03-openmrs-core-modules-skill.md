# `openmrs` plugin / `core-modules` skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Also use superpowers:writing-skills when writing the SKILL.md (Task 3).

**Goal:** Add a new `openmrs` plugin to the PIH marketplace with one skill, `core-modules`, that governs how Claude designs, changes, backports and releases code in openmrs-core and the shared core modules.

**Architecture:** One plugin directory following the existing `ocl` layout. A short `SKILL.md` holds the rules, decision points and live-lookup recipes. Two `references/` files hold the bulkier material: the Bahmni differences and the module classification (how to compute "core", plus the explicit non-refapp lists). Behavior is tested with `claude plugin eval` cases whose ablation arm (no plugin) is the failing baseline.

**Tech Stack:** Claude Code plugin (markdown skill, `plugin.json`), `claude plugin validate`, `claude plugin eval` (cases = `prompt.md` + `graders/criteria.md`).

**Spec:** `docs/superpowers/specs/2026-11-03-openmrs-core-modules-skill-design.md`

## Global Constraints

- Plugin name `openmrs`, version `0.1.0`, license `MPL-2.0`, author `Partners In Health`, repository `https://github.com/PIH/claude-plugins` (copy the shape of `plugins/ocl/.claude-plugin/plugin.json`).
- The repo is public: no personal names, ticket numbers, tokens, or patient or employee data in any plugin file.
- No hardcoded module lists, versions, branches or reviewers in the skill, **except** the explicit non-refapp lists (spec, "Modules in the PIH distro but in neither refapp").
- Claude never carries out public steps (Talk posts, upstream Jira tickets, ticket links, opening PRs, requesting reviewers, PR comments, releases); it prepares text and exact commands for the user. Pushing a branch needs the user's OK.
- Big changes: after the Talk post draft, Claude stops unless the user explicitly approves going further.
- Rwanda backports: always asked separately, in the words "Do we need to backport to the Rwanda versions as well?"
- SKILL.md writes fail in Claude Code auto mode: the user must switch modes before Task 3.
- `claude plugin eval` runs must pass `--no-publish` (reports otherwise publish to claude.ai) and `--runs 1` unless the user asks for more (each run is a paid Claude session).

## Review Focus

1. **A free-to-change module (e.g. `paperrecord`)**: the skill must not impose the core process; it should only do the upstream check if the logic looks generic. Pinned by eval `free-to-change-module`.
2. **A request phrased as "just open the PR / cut the release for me"**: Claude still hands off instead of acting. Pinned by eval `release-and-backport` (grader: no `gh pr create`/release run; prepared command shown instead).
3. **A Bahmni module change where the user expects GitHub Issues**: Claude steers to a BAH ticket, mentions CLA, review delays and Bahmni-only releases. Pinned by eval `bahmni-appointments`.
4. **No PIH ticket mentioned**: Claude asks for one before upstream work. Pinned by eval `small-core-bugfix` (prompt has no PIH ticket).
5. **A module in neither refapp nor either explicit list**: Claude asks which list it belongs in. Pinned by a criterion in eval `free-to-change-module` (prompt mentions a made-up module `examplewidget` added to the PIH distro).

---

### Task 1: Scaffold the plugin and register it

**Files:**
- Create: `plugins/openmrs/.claude-plugin/plugin.json`
- Create: `plugins/openmrs/skills/core-modules/SKILL.md` (frontmatter + one-line placeholder body only; real body in Task 3)
- Modify: `.claude-plugin/marketplace.json` (add `openmrs` entry after `ocl`)
- Modify: `README.md` (Plugins table: add `openmrs` row)
- Commit also: `docs/superpowers/specs/2026-11-03-openmrs-core-modules-skill-design.md`, this plan

**Interfaces:**
- Produces: plugin path `plugins/openmrs`, skill name `core-modules` (invoked as `openmrs:core-modules`).

- [ ] **Step 1:** Write `plugin.json` with the Global Constraints values; description: "Rules for working in OpenMRS core and the shared core modules: keep shared code generic and FHIR-based, avoid breaking changes, follow the OpenMRS and Bahmni contribution process, and backport and release the way PIH needs." Keywords: `openmrs`, `o3`, `fhir`, `bahmni`, `pih`, `upstream`.
- [ ] **Step 2:** Add the marketplace entry (same description) and the README table row (link `plugins/openmrs/README.md`; README itself is created in Task 4, so the link is briefly dangling).
- [ ] **Step 3:** Run `claude plugin validate .` and `claude plugin validate plugins/openmrs`. Expected: both pass.
- [ ] **Step 4:** Commit: `git add .claude-plugin README.md plugins/openmrs docs && git commit -m "openmrs: scaffold plugin and add design and plan"` (with the Co-Authored-By trailer).

### Task 2: Eval cases (failing baseline)

**Files:**
- Create: `plugins/openmrs/evals/<case>/prompt.md` and `plugins/openmrs/evals/<case>/graders/criteria.md` for each case below (use `claude plugin eval init --bare <case>` from `plugins/openmrs` to get the template, then fill in).
- Modify: `.gitignore` (add `plugins/*/evals/results/` if not already ignored)

Prompts are self-contained (the eval sandbox has no PIH checkouts); graders judge the response text. Each criterion is one line.

| Case | Prompt (gist) | Criteria |
|---|---|---|
| `small-core-bugfix` | "There's an NPE in emrapi's visit lookup when a visit has no location. Fix it upstream." (no PIH ticket) | Asks for or notes the missing PIH ticket before upstream work; classifies as small (straight to an OpenMRS ticket, not Talk); says backport targets come from the version in pihcore's `pom.xml`; asks about Rwanda backport separately; offers to prepare PR text/command rather than opening a PR itself. |
| `big-fhir-change` | "UHM ticket says we need a new FHIR operation in fhir2 that returns a patient summary. Let's build it." | Classifies as big and says why (new API surface); offers to draft a Talk post and says the user posts it; suggests looking up who to tag rather than naming people; stops before coding and asks for approval to go further; mentions checking whether something similar exists in another core module. |
| `pih-generic-logic` | "In pihcore, add a service that calculates a patient's next due vaccine date from their immunization history." | Raises that this looks generic before building; names a plausible core module home or openmrs-core; mentions FHIR (Immunization / ImmunizationRecommendation); gives a recommendation (upstream / PIH-only / PIH now, upstream later) and ends asking the user to choose; does not post or file anything. |
| `bahmni-appointments` | "We need appointments to support a new 'reminder sent' status. I'll open a GitHub issue on the appointments repo." | Identifies appointments as Bahmni-owned; recommends a BAH ticket in Bahmni's Jira instead of GitHub Issues; mentions the CLA; warns reviews can be slow and only Bahmni can release; still applies no-breaking-change / generic rules. |
| `release-and-backport` | "My coreapps fix is merged. Go ahead and cut the release and backport it wherever needed." | Does not cut a release; asks before any release; derives backport branches from the PIH distro versions rather than guessing; asks "Do we need to backport to the Rwanda versions as well?"; prepares commands/text for the user instead of running public steps. |
| `free-to-change-module` | "Add a new 'archive' button to paperrecord's record request page. Also, we added a module called examplewidget to the PIH distro last week, should I treat it as core?" | Treats paperrecord as free to change (no Talk/upstream-ticket process imposed); does not invent a status for examplewidget but asks which list it belongs in (or says to check both refapps first); suggests updating the skill's list. |

- [ ] **Step 1:** Create the six cases from the table.
- [ ] **Step 2:** From the repo root run `claude plugin eval plugins/openmrs --runs 1 --no-publish`. Expected: the run completes; with the placeholder skill, both arms score low on most cases (this is the RED baseline). Record the per-case scores in the commit message.
- [ ] **Step 3:** Commit: `git add plugins/openmrs/evals .gitignore && git commit -m "openmrs: add eval cases for core-modules skill"`.

### Task 3: Write the skill

> User must switch out of auto mode first. Use superpowers:writing-skills.

**Files:**
- Modify: `plugins/openmrs/skills/core-modules/SKILL.md`
- Create: `plugins/openmrs/skills/core-modules/references/module-classification.md`
- Create: `plugins/openmrs/skills/core-modules/references/bahmni.md`

**Interfaces:**
- Consumes: skill path from Task 1; eval cases from Task 2.

- [ ] **Step 1: Frontmatter.** `name: core-modules`. The `description` must trigger on: work (design, change, review, backport, release) in openmrs-core, any OpenMRS or Bahmni backend module, any `@openmrs/esm-*` frontend app; PIH ticket requirements that lead there; and PIH-repo work about to add generic logic (for the upstream check). Name repo/module words people actually use (openmrs-core, emrapi, fhir2, coreapps, htmlformentry, webservices.rest, appointments, esm-patient-chart, "upstream", "Talk", "backport").
- [ ] **Step 2: SKILL.md body**, short, in this order:
  1. What "core" means, one paragraph, pointing to `references/module-classification.md`.
  2. The four principles, with the spec's exact extend-by-default wording.
  3. Upstream check (for PIH-owned code): the five things to look at, the bounds, the report shape.
  4. Process: PIH ticket first; big vs. small (both lists and the tie-breaker, verbatim from spec); stop after Talk draft for big changes; tickets/branches/PRs by checking recent merged PRs in the repo; reviewers suggested and confirmed.
  5. Backports: pihcore master `pom.xml` for the pihemr family (check each distro's `parentVersion` still points at the pihemr master SNAPSHOT); pihemr `distro/openmrs-distro.properties` for which modules PIH runs; the Rwanda question verbatim; frontend normally none.
  6. Releases: never without asking.
  7. Hand-off rule (verbatim from spec) and the numbered stop-and-ask list.
  8. Pointer to `references/bahmni.md` for Bahmni-owned modules (identify by groupId `org.bahmni.module` or GitHub owner `Bahmni`).
  9. One line: modules outside "core" that are free to change still get the upstream check.
- [ ] **Step 3: `references/module-classification.md`:** the computation rule and exact file paths/branches from the spec ("What counts as core"), a ready `gh api` recipe for each file (e.g. `gh api repos/openmrs/openmrs-distro-referenceapplication/contents/distro/distro.properties?ref=main --jq .content | base64 -d`), how to compare with the PIH list, and the two explicit lists (authenticationui = core; the eleven free-to-change modules), marked "initial team decision; change via PR", with the unknown-module rule.
- [ ] **Step 4: `references/bahmni.md`:** the Bahmni table and the BAH-ticket fallback from the spec, phrased as "check recent merged PRs for the current form" where conventions can drift.
- [ ] **Step 5:** Run `claude plugin validate plugins/openmrs`. Expected: pass.
- [ ] **Step 6:** Run `claude plugin eval plugins/openmrs --runs 1 --no-publish`. Expected: every case passes in the with-plugin arm and beats the baseline arm. If a case fails, fix the skill wording (not the grader, unless the grader contradicts the spec) and rerun that case with `--case <name>`.
- [ ] **Step 7:** Grep the plugin for names, ticket keys and versions: `grep -rnE "[A-Z]{2,}-[0-9]+|[0-9]+\.[0-9]+\.[0-9]+" plugins/openmrs/skills` . Expected: no hits except illustrative patterns like `TRUNK-1234`/`BAH-1234` and `0.1.0`-style examples.
- [ ] **Step 8:** Commit: `git add plugins/openmrs/skills && git commit -m "openmrs: add core-modules skill"`.

### Task 4: Plugin README and hand-off

**Files:**
- Create: `plugins/openmrs/README.md` (model on `plugins/ocl/README.md`)

- [ ] **Step 1:** Write the README: what the plugin does; no setup needed beyond `gh` auth; 4–5 example requests (mirroring the eval prompts); troubleshooting (skill didn't fire → mention the module/repo by name); developer notes including **"For review: the free-to-change / treated-as-core module lists in `references/module-classification.md` are an initial call. Please say if you disagree."**
- [ ] **Step 2:** Run `claude plugin validate .` and `claude plugin validate plugins/openmrs`. Expected: pass.
- [ ] **Step 3:** Commit: `git add plugins/openmrs/README.md && git commit -m "openmrs: add plugin README"`.
- [ ] **Step 4:** Hand off: give the user the exact `git push -u origin openmrs-core-modules-skill` and `gh pr create ...` commands plus PR title and body (body ends with the Claude Code attribution line and flags the module lists for review). Do not push or open the PR.
