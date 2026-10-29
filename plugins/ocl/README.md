# ocl

A Claude Code plugin for working with the PIH concept dictionary in [Open Concept Lab (OCL)](https://app.v3.openconceptlab.org/orgs/PIH/sources/PIH/).

To install, type this in Claude Code:

```
/plugin install ocl --marketplace PIH/claude-plugins
```

For step-by-step instructions, including how to open Claude Code from Claude Desktop and connect your OCL account, see the [main README](../../README.md#getting-started-no-coding-experience-needed).

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

Every change is shown to you first, and Claude waits for your OK before making it.

## Requirements

- Claude Code: in Claude Desktop, or in a terminal.
- An OCL account with an API token. Editing the PIH source also requires membership in the PIH organization on OCL.
- `curl` and `python3`. These usually come with Mac and Linux. On Windows, or if either is missing, Claude will tell you and can help you install it.
