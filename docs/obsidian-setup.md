# Open scratch files in Obsidian

1. In Obsidian's vault picker, choose **Open folder as vault**, then select the same
   `~/Documents/obsidian-vault` (or the custom directory you configured).
2. Open `agents/home.md`. Browse the `projects` folder, then open a task's
   `README.md`. Its file links and handoff are the entry points for that task.
3. Open **Settings → Community plugins**, enable community plugins if necessary,
   then **Browse** and search for **Code Files** (by Lukas Bach). Install and enable it.
   You can also use [Open Code Files in Obsidian](obsidian://show-plugin?id=code-files).
4. In the Code Files settings, configure the extensions you need. Start with `txt`,
   `log`, `json`, `jsonl`, `yaml`, `yml`, `csv`, `py`, `js`, `ts`, `sh`, `sql`, `toml`,
   `xml`, `html`, `css`, `diff`, and `patch`. Follow the plugin UI's expected format.
   Keep `.md` assigned to Obsidian's normal Markdown view.
5. Create `scratch/example.json` in a task with `{"ready": true}`, link it from
   that task's README, and click the link. Confirm it opens in a code editor and
   that an edit is saved back to the same file. Opening a script does not run it.

[Code Files](https://github.com/lukasbach/obsidian-code-files) provides a Monaco
editor and configurable extension support. Its documented hosted editor dependency
requires an internet connection. If that dependency is unsuitable, use an external
text editor; the Markdown task index still supplies navigation.

For an extension still absent from the file list, enable **Settings → Files and
links → Detect all file extensions**. This makes files visible; it does not add an
editor for arbitrary formats. For unsupported binaries, use the file's context menu
to open it in the default application. Keep an explanatory Markdown note linked to
the binary. Don't rename files to `.md` just to make them visible.

Obsidian's [accepted file formats](https://help.obsidian.md/Files+and+folders/Accepted+file+formats)
include several media formats and PDFs. File viewers are for humans; the agents use
ordinary filesystem reads and writes and do not depend on community plugins.

A vault may be synced to other devices. Keep secrets out of scratch files and logs,
and check what you are sharing before placing private outputs there. Configure the
community plugin through Obsidian; this repository never overwrites `.obsidian/`.
