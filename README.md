# PIH Claude plugins

Plugins for [Claude Code](https://claude.com/claude-code) that help with Partners In Health EMR and informatics work.

## Why this repo exists

As we use Claude for PIH work, we keep teaching it the same things: how our systems are set up, our conventions, which approaches work and which to avoid. This repo is where we save that knowledge as **skills** and share it. Anyone on the team benefits from what one person has figured out, and Claude starts from what we already know instead of from scratch.

It has two goals:

- **One place for the PIH team to build skills together.** Skills are written in plain language and kept in git, so changes are reviewed, tracked, and improved over time. Developers maintain the repo, but the knowledge comes from everyone who does the work.
- **Skills anyone can use, with no git or GitHub knowledge needed.** Colleagues who aren't developers install the plugins once from inside Claude, then just ask Claude for what they need. Getting updates and suggesting improvements don't require git either. See [Getting started](#getting-started-no-coding-experience-needed) and [Suggesting improvements](#suggesting-improvements).

## Plugins

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

Claude doesn't update PIH plugins automatically unless you turn that on. Automatic updates are only on by default for Anthropic's own marketplaces.

**Turn on automatic updates (recommended, one time):**
1. Type `/plugin` and press Enter.
2. Open the **Marketplaces** tab.
3. Select **pih**, then choose **Enable auto-update**.

Claude then checks for updates in the background after a session starts. New versions take effect in your next session, or right away if you type `/reload-plugins`.

**Or update by hand** whenever you want:

```
/plugin marketplace update pih
```

Then type `/reload-plugins` or start a new session.

## Troubleshooting

- **"Unknown command" when typing `/plugin`:** your Claude Desktop may be out of date. Update it, or ask a developer colleague to help you run Claude Code in a terminal (`claude`), where `/plugin` is always available.
- **Claude says it can't reach OCL, or gets a 401/403 error:** run `/ocl:setup` again. Your token may be missing, mistyped, or expired.
- **Claude says a change was blocked by "auto mode":** this is a safety feature. Claude will write the change into a small script and explain how to run it after you've reviewed it.
- **Anything else:** ask Claude! For example: *"The OCL plugin isn't working, can you help me figure out why?"*

---

## Suggesting improvements

These plugins are a work in progress, and the OCL plugin especially. If Claude got something wrong, missed a PIH convention, or you wish it could do something new:
- open an issue at https://github.com/PIH/claude-plugins/issues, or
- tell one of the maintainers. A short description of what you asked, what Claude did, and what it should have done is perfect.

---

## Developing the plugins

### How a plugin is laid out

```
.claude-plugin/marketplace.json   # the marketplace: lists the plugins in this repo
plugins/
  ocl/
    .claude-plugin/plugin.json    # plugin name, version, description, license
    README.md
    commands/setup.md             # the /ocl:setup command
    skills/ocl-search/SKILL.md    # what Claude knows about OCL and the PIH source
```

Most of the plugin's value is in **`SKILL.md`**. It's plain Markdown that Claude reads when the topic comes up:
- The `description` at the top decides **when** Claude uses the skill. Name the words and situations that should trigger it.
- The body is **how** to do the work: API calls, PIH conventions, safety rules and known quirks. Write it like notes for a capable new colleague, and explain *why*, not just *what*.

A command like `commands/setup.md` is a reusable prompt that people run as `/ocl:setup`.

### Workflow for revising the OCL skill

1. **Get the code** (first time only), and make a branch:
   ```bash
   git clone git@github.com:PIH/claude-plugins.git ~/development/claude-plugins
   cd ~/development/claude-plugins && git checkout -b <ticket>-<short-description>
   ```

2. **Run Claude Code with your local copy of the plugin.** From whatever folder you want to work in:
   ```bash
   claude --plugin-dir ~/development/claude-plugins/plugins/ocl
   ```
   This loads the plugin straight from your checkout, for that session only. If you also have the published plugin installed, disable it first with `/plugin disable ocl@pih` (and `/plugin enable ocl@pih` later), so you aren't running two versions at once.

3. **Do real OCL work, and let the skill learn from it.** The best improvements come from actual tasks. When Claude discovers something, or you correct it, ask:
   > *Update the ocl-search skill in ~/development/claude-plugins with what we just learned.*

   Good additions:
   - **API details that worked**, e.g. an endpoint, parameter, or response quirk.
   - **PIH conventions**, e.g. "imaging orderables are mapped to DICOM with `Associated with`".
   - **Mistakes to avoid**, with the reason.

   Mark anything that's untested or unconfirmed as such, so Claude doesn't treat a guess as fact. Keep it general: no personal details, ticket numbers, tokens, or patient or employee data. **This repo is public.**

4. **Restart to pick up edits.** Exit Claude Code and rerun the step 2 command, then try a request that exercises the change.

5. **Validate:**
   ```bash
   claude plugin validate .
   claude plugin validate plugins/ocl
   ```

6. **Bump the version** in `plugins/ocl/.claude-plugin/plugin.json`. Because the plugin sets a `version`, users only get the update when it changes, even if they have automatic updates turned on.
   - **Patch** (`0.1.0` → `0.1.1`): fixes and small additions.
   - **Minor** (`0.1.0` → `0.2.0`): new workflows or commands.

7. **Commit, push and open a pull request.** Ask someone familiar with the PIH dictionary to review changes to conventions or write workflows. Once it's merged, users pick it up the next time they update (see *Keeping the plugin up to date* above).

### Adding a new plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` (copy the OCL one as a starting point), plus `skills/` and/or `commands/`.
2. Add an entry for it in `.claude-plugin/marketplace.json`.
3. Validate, and add a row to the plugin table at the top of this README.
4. Asking Claude to *"scaffold a new plugin in this repo for <task>"* is a good way to start.

### Optional: automated checks

`claude plugin eval plugins/<name>` runs test cases stored in the plugin's `evals/` folder. It's worth adding a few for the OCL skill once its behavior settles, e.g. "is CIEL X already in PIH?", so changes don't quietly break things that used to work.

## License

[Mozilla Public License 2.0](LICENSE)
