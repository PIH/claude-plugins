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
| **Skill: `ocl-search`** | Loads automatically when you ask about OCL, CIEL, or PIH concepts. It teaches Claude the OCL API and how the PIH source is organized: ID numbering, mapping conventions, how concept sets are stored, and how to clone from CIEL, create and edit concepts, add mappings, and release source versions safely. Includes a read-only script that checks cloned concepts (or a whole export) for mappings the OCL clone got wrong, and a check that tells you when a newer version of this plugin is available. |
| **Command: `/ocl:setup`** | Checks that your OCL API token is set up, and walks you through it if not. |

## What it can do

- Search the PIH and CIEL dictionaries, and give you links to view the full concepts in OCL.
- Show which concept sets a concept belongs to, or what's in a set.
- Check whether a CIEL concept is already in PIH.
- Preview, then clone, CIEL concepts into PIH, and check the clone for broken mappings.
- Check everything changed since the last release for problems that would break the OpenMRS import, before you release.
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

## Check before you release a new version

A release that OpenMRS can't import stops the EMR from starting on every server that loads it. That's what happened with 1.8.47–1.8.50 (Jira UHM-9656). So before releasing, ask Claude to check what's about to go out. For example:

- *Check everything that's changed in the PIH source since the last release, before I release a new version.*
- *I just cloned some concepts from CIEL. Check them for problems.*

Claude runs a read-only check on every concept changed since the last release, and tells you in plain language what it finds. It looks for:

- **Name clashes:** a concept name whose ID is already used by a different concept on PIH servers, which would make the import fail. These are often names that were removed long ago and that OCL no longer shows. Claude checks them against a copy of a PIH database. The first time, it downloads about 33 MB.
- **Broken mappings from cloning:** ICD-10 or LOINC codes that cloning from CIEL replaced with a PIH concept.

If it finds a problem, Claude explains it and offers a fix, which it shows you before making any change. Release only once the check comes back clean.

This catches the problems we know about, not every possible import error. If you can, still try the new release on a test server before it goes to live sites.

Each check also watches for OCL fixing the clone bugs it works around (ocl_issues#3012 and #3013). If it looks like OCL has fixed them, Claude will tell you, and suggest updating the plugin to drop checks that are no longer needed. It never makes that change without asking.

**The same check also runs automatically** when the PIH/pihemr "Update OCL export" GitHub Action puts a new release into the distro. If the release has errors, the Action stops and doesn't open a pull request, so the release never reaches servers.

**Then it test-loads the release on a real OpenMRS database.** The release check only catches problems we already know about, so the Action (and Claude, when you ask it to put a release into the distro) also starts the ZL EMR with the new export on a copy of the nightly ZL seed database and checks that the import finished without errors. It takes about 15–30 minutes in the Action (10–20 when Claude runs it on your machine); tick *Skip the load test* in the Action, or tell Claude to skip it, when you can't wait. The PR says when it was skipped. The test is pihemr's `scripts/ocl-load-test.sh`.

Developers can run the check directly: `python3 -I plugins/ocl/skills/ocl-search/scripts/ocl_release_check.py --unreleased`. Add `--since <version>` to check against an older release (e.g. `--since 1.8.46` reproduces the 1.8.47 failure), or use `--export <zip> --baseline <older zip>` to check an export the way the Action does. `--list-checks` lists the checks; the script's header explains how to add or retire one.

## Staying up to date

The first time you use the plugin in a session, Claude checks whether a newer version is out (at most once a day). If one is, it tells you and explains how to update. Newer versions can include better release checks, so update before releasing. To update without waiting to be told, see [Keeping plugins up to date](../../README.md#keeping-plugins-up-to-date) in the main README.

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
