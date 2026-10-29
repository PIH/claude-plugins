# ocl

A Claude Code plugin for searching and maintaining the PIH concept dictionary in [Open Concept Lab (OCL)](https://app.v3.openconceptlab.org/orgs/PIH/sources/PIH/).

New to Claude Code or PIH plugins? Start with the [main README](../../README.md), which explains how to open Claude Code from Claude Desktop and install plugins.

## Install

Type this in Claude Code, then start a new session:

```
/plugin install ocl --marketplace PIH/claude-plugins
```

## What's included

| | |
|---|---|
| **Skill: `ocl-search`** | Loads automatically when you ask about OCL, CIEL, or PIH concepts. It teaches Claude the OCL API and how the PIH source is organized: ID numbering, mapping conventions, how concept sets are stored, and how to clone from CIEL, create and edit concepts, add mappings, and release source versions safely. |
| **Command: `/ocl:setup`** | Checks that your OCL API token is set up, and walks you through it if not. |

## What it can do

- Search the PIH and CIEL dictionaries, and give you links to view the full concepts in OCL.
- Show which concept sets a concept belongs to, or what's in a set.
- Check whether a CIEL concept is already in PIH.
- Preview, then clone, CIEL concepts into PIH.
- Create and edit PIH concepts, names, translations and mappings.
- Release a new version of the PIH source.

## Requirements

- Claude Code: in Claude Desktop, or in a terminal.
- An OCL account with an API token. Editing the PIH source also requires membership in the PIH organization on OCL.
- `curl` and `python3`. These usually come with Mac and Linux. On Windows, or if either is missing, Claude will tell you and can help you install it.

## Set up your OCL account (one time)

The plugin uses your personal OCL **API token** to search OCL for you. In Claude Code, type:

```
/ocl:setup
```

Claude will check whether your token is set up, and if not, walk you through it:
- getting the token from your OCL profile, and
- saving it with a short command in your computer's **Terminal** (Mac) or **PowerShell** (Windows).

Your token is saved on your own computer, in `~/.config/ocl/token`, where only you can read it.

> **Never paste your OCL token or password into the chat.** If you do by accident, create a new token in OCL (profile → API Token) and run `/ocl:setup` again.

## Try it

Just ask in plain language. For example:

- *Find PIH concepts named "Chest" that are in a radiology concept set, with links.*
- *Is CIEL concept 165152 already in the PIH dictionary?*
- *What answers does PIH concept 1643 have, and what are they mapped to?*
- *Which PIH concepts were changed most recently?*

## Making changes to the dictionary

For changes, like cloning from CIEL, creating or editing concepts, adding mappings, or releasing a new version, Claude always shows you what it's about to change and waits for your OK.

The PIH dictionary feeds live EMR systems at several sites, and a change made for one site can affect others. Check with the dictionary maintainers if you're unsure, especially before releasing a new version of the PIH source, since that includes everyone's unreleased edits.

## Troubleshooting

- **Claude says it can't reach OCL, or gets a 401/403 error:** run `/ocl:setup` again. Your token may be missing, mistyped, or expired.
- **A change was blocked by "auto mode":** Claude Code's auto mode blocks changes to shared systems like OCL. Claude will write the change into a small script for you to review and run (it'll tell you how), then check the result.
- **Claude can't edit the PIH source (403 on a change):** your OCL account needs to be a member of the PIH organization. Ask a dictionary maintainer.

## Developing this plugin

The skill is a work in progress. To revise it, follow the [development workflow](../../README.md#workflow-for-revising-a-plugin) in the main README, with `<name>` = `ocl` and `<skill>` = `ocl-search`.

Good additions to `skills/ocl-search/SKILL.md`:
- **OCL API details that worked:** an endpoint, parameter, or response quirk.
- **PIH dictionary conventions,** e.g. "imaging orderables are mapped to DICOM with `Associated with`, not `SAME-AS`".
- **Mistakes to avoid,** with the reason.
- **OpenMRS-side effects:** how a change in OCL shows up in OpenMRS or FHIR.

Ask someone familiar with the PIH dictionary to review changes to conventions or to anything that writes to OCL.
