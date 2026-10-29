# PIH Claude plugins

Plugins for [Claude Code](https://claude.com/claude-code) that help with Partners In Health EMR and informatics work.

| Plugin | What it does |
|---|---|
| [`ocl`](plugins/ocl/) | Search and maintain the PIH concept dictionary in [Open Concept Lab (OCL)](https://app.v3.openconceptlab.org/): find concepts, see which sets they're in, pull concepts from CIEL, and add or edit PIH concepts and mappings. |

---

## Getting started (no coding experience needed)

You'll do steps 1–5 once. After that, just open Claude Code and ask.

### 1. Install Claude Desktop and sign in

1. Download Claude Desktop from https://claude.ai/download and install it.
2. Open it and sign in with your PIH Claude account.

### 2. Open Claude Code

Claude Code is the part of Claude Desktop that can work with files and websites like OCL.

1. In Claude Desktop, click **Code**. It sits next to **Chat**, at the top or in the sidebar, depending on your version.
2. When asked to pick a folder, choose or create one for this work, e.g. a folder called `claude` in your Documents. Any folder works.
3. You'll see a message box, like in a normal chat. That's where you type everything below.

> Claude Code will sometimes ask your permission before doing something, such as running a command or changing a file. Read what it says, then approve or decline. If you're unsure, decline and ask Claude to explain.

### 3. Install the OCL plugin

Type this into the message box and press Enter:

```
/plugin install ocl --marketplace PIH/claude-plugins
```

This adds the PIH *marketplace* (the list of PIH plugins) and installs the OCL plugin from it, all in one step.

If Claude asks where to install it, choose the option for **you / all your projects** (sometimes labeled "user"), so it works in every folder.

<details>
<summary>That didn't work? Try the two-step way</summary>

Older versions of Claude Code need two commands. Type each one and press Enter:

```
/plugin marketplace add PIH/claude-plugins
```
```
/plugin install ocl@pih
```

You can also type just `/plugin` to open a menu where you can browse the PIH marketplace and install from there.
</details>

### 4. Start a new session

Start a new Claude Code session so the plugin loads. You can close and reopen the Code view, or start a new session from the menu.

### 5. Connect your OCL account (one time)

The plugin uses your personal OCL **API token** to search OCL for you. Type:

```
/ocl:setup
```

Claude will check whether your token is set up, and if not, walk you through it:
- getting the token from your OCL profile, and
- saving it with a short command in your computer's **Terminal** (Mac) or **PowerShell** (Windows).

Your token is saved on your own computer, where only you can read it.

> **Never paste your OCL token or password into the chat.** If you do by accident, create a new token in OCL (profile → API Token) and run `/ocl:setup` again.

### 6. Try it

Just ask in plain language. For example:

- *Find PIH concepts named "Chest" that are in a radiology concept set, with links.*
- *Is CIEL concept 165152 already in the PIH dictionary?*
- *What answers does PIH concept 1643 have, and what are they mapped to?*
- *Which PIH concepts were changed most recently?*

For changes, like cloning from CIEL, creating or editing concepts, or adding mappings, Claude always shows you what it's about to change and waits for your OK. Changes to the PIH dictionary affect live EMR systems, so check with the dictionary maintainers if you're unsure.

---

## Keeping the plugin up to date

To pick up the latest version, type:

```
/plugin marketplace update pih
```

Then start a new session.

## Troubleshooting

- **"Unknown command" when typing `/plugin`:** your Claude Desktop may be out of date. Update it, or ask a developer colleague to help you run Claude Code in a terminal (`claude`), where `/plugin` is always available.
- **Claude says it can't reach OCL, or gets a 401/403 error:** run `/ocl:setup` again. Your token may be missing, mistyped, or expired.
- **Claude says a change was blocked by "auto mode":** this is a safety feature. Claude will write the change into a small script and explain how to run it after you've reviewed it.
- **Anything else:** ask Claude! For example: *"The OCL plugin isn't working, can you help me figure out why?"*

---

## For maintainers

```
.claude-plugin/marketplace.json   # the marketplace: lists the plugins in this repo
plugins/
  ocl/
    .claude-plugin/plugin.json    # plugin name, version, description
    commands/setup.md             # /ocl:setup
    skills/ocl-search/SKILL.md    # what Claude knows about OCL and the PIH source
```

- **Add a plugin:** create `plugins/<name>/` with a `.claude-plugin/plugin.json`, then add an entry for it in `.claude-plugin/marketplace.json`.
- **Validate before pushing:** `claude plugin validate .` (the marketplace) and `claude plugin validate plugins/<name>` (a plugin).
- **Release changes:** bump `version` in the plugin's `plugin.json`, so users get the update.
- **Test locally without pushing:** `/plugin marketplace add /path/to/claude-plugins`, then `/plugin install ocl@pih`.
- **This repo is public.** Don't commit tokens, passwords, patient or employee data, or anything else that shouldn't be public.

## License

[Mozilla Public License 2.0](LICENSE)
