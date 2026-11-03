# openmrs

A Claude Code plugin with PIH's rules for working in code we don't solely own: **openmrs-core and the shared "core" modules**, both backend modules and O3 frontend apps.

New to Claude Code or PIH plugins? Start with the [main README](../../README.md), which explains how to open Claude Code from Claude Desktop and install plugins.

## Install

Type this in Claude Code, then start a new session:

```
/plugin install openmrs --marketplace PIH/claude-plugins
```

## What's included

| | |
|---|---|
| **Skill: `core-modules`** | Loads automatically when you design, change, review, backport or release code in openmrs-core, a core module (for example emrapi, fhir2, coreapps, htmlformentry, appointments) or an `@openmrs/esm-*` app. It also loads when PIH work is about to add logic generic enough to belong upstream. |

## What it does

- **Works out what's "core":** a module that is in the PIH distro and in either the O3 or the O2 Reference Application, plus openmrs-core. Claude checks the distro files live, and the skill keeps an explicit list for PIH-distro modules that are in neither refapp.
- **Applies the rules for shared code:** keep it generic (nothing PIH-specific), base new features on FHIR, make no breaking changes, and extend an existing module rather than building a parallel one.
- **Runs an upstream check:** when you're building something generic in pihcore or another PIH repo, Claude does some quick research on whether and how it could go upstream, recommends an approach, and lets you decide.
- **Follows the process:** a PIH ticket first, then a Talk post (big changes) or an upstream ticket (small changes); OpenMRS branch and PR conventions; reviewers suggested and confirmed with you; backports only to the versions PIH runs, with Rwanda asked about separately; and no release without asking.
- **Knows Bahmni is different:** for Bahmni-owned modules such as appointments, Claude uses BAH tickets in Bahmni's Jira, reminds you about the CLA, and warns that reviews can be slow and that only Bahmni can release.

**Claude plans, you decide.** Claude never posts, files tickets, pushes, opens PRs, requests reviewers or cuts releases on its own. It prepares the text and the exact commands, lists what it plans to do, and you decide each action: let Claude do it, edit it, or do it yourself. Where Claude has no access (OpenMRS Jira, Talk), you always do it yourself.

## Requirements

- Claude Code: in Claude Desktop, or in a terminal.
- The GitHub CLI (`gh`), signed in, so Claude can read distro files and recent PRs.

## Try it

For example:

- *There's an NPE in emrapi's visit lookup when a visit has no location. Fix it upstream.*
- *Our PIH ticket says we need a new FHIR operation in fhir2 that returns a patient summary. Let's build it.*
- *In pihcore, add a service that calculates a patient's next due vaccine date.*
- *My coreapps fix is merged. What needs backporting and releasing?*
- *Is examplewidget a core module?*

## Troubleshooting

- **The skill didn't load:** name the module or repo in your request (for example "in emrapi" or "upstream in fhir2"), or ask Claude to use the `openmrs:core-modules` skill.
- **Claude can't read the distro files:** check that `gh` is installed and signed in (`gh auth status`).
- **Claude wants to edit the skill but auto mode blocks it:** switch out of auto mode for that edit.

## Developing this plugin

To revise it, follow the [development workflow](../../README.md#workflow-for-revising-a-plugin) in the main README, with `<name>` = `openmrs` and `<skill>` = `core-modules`.

**For review:** the lists of PIH-distro modules that are in neither refapp (`authenticationui` treated as core; `dispensing`, `edtriageapp`, `emr`, `growthchart`, `labtrackingapp`, `namephonetics`, `paperrecord`, `pihapps`, `pihcore`, `printer`, `radiologyapp` free to change) are an initial call. They're near the top of `skills/core-modules/SKILL.md`. If you disagree, say so or open a PR.

Good additions to the skill:
- **Process details that worked or changed:** a repo's PR conventions, where a ticket really goes.
- **Mistakes to avoid,** with the reason.
- **Updates to the module lists** when a module is added to or dropped from the PIH distro.

Don't add things the skill looks up live, such as versions, module lists from the distros, or reviewer names.

The `evals/` folder has test cases. Run them after changing the skill (each run is a paid Claude session):

```bash
claude plugin eval plugins/openmrs --runs 1 --no-publish
```
