# AIDevObserver (VS Code + Cursor extension)

A **thin editor surface** over the Teleon Observer session-review layer. It runs the
governed Python CLI and renders what it returns — it does **not** analyse anything in
TypeScript:

```bash
python3 -m src.teleon.observer.cli review --latest --json
```

The Observer reviews how an AI coding session was *used* — **reinvention / waste**
signals — not the correctness of the code. Every finding is a governed **candidate**
(`serves_truth=false`); a human triages it. The extension is strictly **read-only**: it
never writes, edits, or republishes session content anywhere. It only uses standard
`vscode.*` APIs, so the same build runs in both VS Code and **Cursor**.

## The contract

The extension shells out to the CLI with the working directory set to the workspace
root (so it finds *that* project's Claude sessions):

| Command | CLI invocation |
| --- | --- |
| Review latest session | `… cli review --latest --json` |
| Live (advisory) check | `… cli live --latest --mode advisory --json` |
| List sessions | `… cli list --json` → pick → `… cli review --path <path> --json` |

`python3` is overridable via `aidevobserver.pythonPath`; the working directory via
`aidevobserver.cliCwd` (default: first workspace folder).

## Commands

Run from the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

- **AIDevObserver: Review Session** — reviews the latest session and renders the report
  in a webview panel ("AIDevObserver — Session Review"): findings grouped by type, a
  confidence badge per item, plus its suggestion, evidence, and `source_ref.existing`
  when present. Clean sessions show a "no findings — clean session" empty state; CLI
  failures show an error state (and the CLI's stderr via an error notification).
- **AIDevObserver: Live Check** — runs the advisory live route and surfaces each
  `surfaced` finding as an information notification, updating the status-bar count.
- **AIDevObserver: List Sessions** — lists discovered sessions in a QuickPick; pick one
  to review it by path.

A status-bar item (left) shows the latest session's finding count and runs **Review
Session** when clicked.

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| `aidevobserver.pythonPath` | `python3` | Interpreter that runs the observer CLI. |
| `aidevobserver.cliCwd` | `""` | CLI working directory. Empty = first workspace folder. |
| `aidevobserver.autoReviewOnFocus` | `false` | On editor focus, silently refresh the status-bar count. |
| `aidevobserver.apiKey` | `""` | **BYO** key for the optional remote fallback (sent transiently as `byo_key`). |
| `aidevobserver.endpoint` | `http://localhost:8120/run` | `byo_demo_server` `/run` endpoint for the remote fallback. |

> **Fallback backend:** when no workspace folder is open there are no project sessions to
> discover, so **Review Session** instead reviews the active editor's transcript via the
> `byo_demo_server` `/run` endpoint (`POST {demo, byo_key, inputs}`). The BYO key is read
> at call time, sent as `byo_key`, and never logged or persisted by the extension.

## Build

```bash
npm install
npm run compile   # tsc -p ./  ->  out/extension.js
```

`npm run watch` recompiles on change. Press **F5** in VS Code to launch an Extension
Development Host with the extension loaded.

## Cursor

Cursor shares the VS Code extension host, so this exact build runs there with identical
behavior — only standard `vscode.*` APIs are used, no proprietary surfaces. To install:

```bash
npm run compile
npx vsce package        # produces aidevobserver-0.1.0.vsix
```

Then in Cursor open the Command Palette and run **Extensions: Install from VSIX…**,
selecting the generated `.vsix`. The CLI it shells out to (`python3 -m
src.teleon.observer.cli`) and the `aidevobserver.*` settings work the same as in VS Code.

## Privacy

The extension is read-only and never persists session content. The optional BYO key lives
only in your VS Code/Cursor settings and is sent with the fallback request as `byo_key`;
the endpoint scopes it to a transient environment for one call. No transcript or key is
persisted by the extension.
