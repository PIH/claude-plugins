# PIH Claude plugins

Plugins for [Claude Code](https://claude.com/claude-code) that help with Partners In Health EMR and informatics work.

## Why this repo exists

As we use Claude for PIH work, we keep teaching it the same things: how our systems are set up, our conventions, which approaches work and which to avoid. This repo is where we save that knowledge as **skills** and share it. Anyone on the team benefits from what one person has figured out, and Claude starts from what we already know instead of from scratch.

It has two goals:

- **One place for the PIH team to build skills together.** Skills are written in plain language and kept in git, so changes are reviewed, tracked, and improved over time. Developers maintain the repo, but the knowledge comes from everyone who does the work.
- **Skills anyone can use, with no git or GitHub knowledge needed.** Colleagues who aren't developers install the plugins once from inside Claude, then just ask Claude for what they need. Getting updates and suggesting improvements don't require git either. See [Getting started](#getting-started-no-coding-experience-needed) and [Suggesting improvements](#suggesting-improvements).

## How it works

- A **skill** is a set of plain-language instructions that Claude reads when a topic comes up. For example, how the PIH concept dictionary is organized and how to search it safely. You don't call a skill yourself; you just ask Claude, and it uses the right one.
- A **command** is a shortcut you type, starting with `/`, such as `/ocl:setup`.
- A **plugin** bundles related skills and commands under one name, such as `ocl`, so you can install them together.
- A **marketplace** is a list of plugins Claude can install. This repo is the PIH marketplace, named `pih`.

## Plugins

Each plugin has its own page with setup steps, examples and tips.

| Plugin | What it does |
|---|---|
| [`ocl`](plugins/ocl/README.md) | Search and maintain the PIH concept dictionary in Open Concept Lab (OCL): find concepts, see which sets they're in, pull concepts from CIEL, and add or edit PIH concepts and mappings. |

---

## Getting started (no coding experience needed)

You only need to do this once per plugin. After that, just open Claude Code and ask. The steps below use the `ocl` plugin as the example; for another plugin, replace `ocl` with its name.

### 1. Install Claude Desktop and sign in

1. Download Claude Desktop from https://claude.ai/download and install it.
2. Open it and sign in with your PIH Claude account.

### 2. Open Claude Code

Claude Code is the part of Claude Desktop that can work with files and with websites like OCL.

1. In Claude Desktop, click **Code**. It sits next to **Chat**, at the top or in the sidebar, depending on your version.
2. When asked to pick a folder, choose or create one for this work, e.g. a folder called `claude` in your Documents. Any folder works.
3. You'll see a message box, like in a normal chat. That's where you type everything below.

> Claude Code will sometimes ask your permission before doing something, such as running a command or changing a file. Read what it says, then approve or decline. If you're unsure, decline and ask Claude to explain.

### 3. Install a plugin

Type this into the message box and press Enter:

```
/plugin install ocl --marketplace PIH/claude-plugins
```

This adds the PIH marketplace and installs the plugin from it, all in one step. If Claude asks where to install it, choose the option for **you / all your projects** (sometimes labeled "user"), so it works in every folder.

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

### 5. Finish setting up the plugin

Some plugins need a one-time setup, such as connecting your account on another system. Each plugin's page explains what's needed. For example, the [`ocl` page](plugins/ocl/README.md#set-up-your-ocl-account-one-time) walks you through connecting your OCL account with `/ocl:setup`.

Then just ask Claude in plain language. Each plugin's page has examples to get you started.

---

## Keeping plugins up to date

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
- **Claude says a change was blocked by "auto mode":** this is a safety feature for changes to shared systems. Claude will usually write the change into a small script and explain how to run it once you've reviewed it.
- **A problem with a specific plugin:** see the Troubleshooting section on that plugin's page.
- **Anything else:** ask Claude! For example: *"The OCL plugin isn't working, can you help me figure out why?"*

---

## Suggesting improvements

These plugins are a work in progress. If Claude got something wrong, missed a PIH convention, or you wish it could do something new:
- open an issue at https://github.com/PIH/claude-plugins/issues, or
- tell one of the maintainers. A short description of what you asked, what Claude did, and what it should have done is perfect.

---

## Developing the plugins

### How a plugin is laid out

Using `ocl` as the example:

```
.claude-plugin/marketplace.json   # the marketplace: lists every plugin in this repo
plugins/
  ocl/
    .claude-plugin/plugin.json    # plugin name, version, description, license
    README.md                     # the plugin's page: setup, examples, troubleshooting, dev notes
    commands/setup.md             # a command: /ocl:setup
    skills/ocl-search/SKILL.md    # a skill: what Claude knows about OCL and the PIH source
```

Most of a plugin's value is in its **`SKILL.md`** files:
- The `description` at the top decides **when** Claude uses the skill. Name the words and situations that should trigger it.
- The body is **how** to do the work: system details, PIH conventions, safety rules and known quirks. Write it like notes for a capable new colleague, and explain *why*, not just *what*.

A command, like `commands/setup.md`, is a reusable prompt that people run as `/<plugin>:<command>`.

### Workflow for revising a plugin

1. **Get the code** (first time only), and make a branch:
   ```bash
   git clone git@github.com:PIH/claude-plugins.git ~/development/claude-plugins
   cd ~/development/claude-plugins && git checkout -b <ticket>-<short-description>
   ```

2. **Run Claude Code with your local copy of the plugin.** From whatever folder you want to work in:
   ```bash
   claude --plugin-dir ~/development/claude-plugins/plugins/<name>
   ```
   This loads the plugin straight from your checkout, for that session only. If you also have the published plugin installed, disable it first with `/plugin disable <name>@pih` (and `/plugin enable <name>@pih` later), so you aren't running two versions at once.

3. **Do real work, and let the skill learn from it.** The best improvements come from actual tasks. When Claude discovers something, or you correct it, ask:
   > *Update the <skill> skill in ~/development/claude-plugins with what we just learned.*

   Mark anything that's untested or unconfirmed as such, so Claude doesn't treat a guess as fact. Keep it general: no personal details, ticket numbers, tokens, or patient or employee data. **This repo is public.** Each plugin's page has notes on what's worth adding to its skills.

4. **Restart to pick up edits.** Exit Claude Code and rerun the step 2 command, then try a request that exercises the change.

5. **Validate:**
   ```bash
   claude plugin validate .
   claude plugin validate plugins/<name>
   ```

6. **Bump the version** in `plugins/<name>/.claude-plugin/plugin.json`. Because our plugins set a `version`, users only get the update when it changes, even if they have automatic updates turned on.
   - **Patch** (`0.1.0` → `0.1.1`): fixes and small additions.
   - **Minor** (`0.1.0` → `0.2.0`): new workflows or commands.

7. **Commit, push and open a pull request.** Ask someone who knows the subject area to review. Once it's merged, users pick it up the next time they update (see [Keeping plugins up to date](#keeping-plugins-up-to-date)).

### Adding a new plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` (copy the `ocl` one as a starting point), plus `skills/` and/or `commands/`.
2. Add a `plugins/<name>/README.md`, using [`plugins/ocl/README.md`](plugins/ocl/README.md) as a model. It should cover:
   - what the plugin does and what it includes,
   - any one-time setup,
   - example requests,
   - plugin-specific troubleshooting,
   - notes for developers.
3. Add an entry for it in `.claude-plugin/marketplace.json`, and a row to the [Plugins](#plugins) table above.
4. Validate.

Asking Claude to *"scaffold a new plugin in this repo for <task>"* is a good way to start.

### Optional: automated checks

`claude plugin eval plugins/<name>` runs test cases stored in the plugin's `evals/` folder. It's worth adding a few once a skill's behavior settles, so changes don't quietly break things that used to work.

## License

[Mozilla Public License 2.0](LICENSE)
