# AIDevObserver (VS Code extension)

Review the active editor's AI-session transcript for **reinvention / waste** findings,
straight from VS Code. The extension sends the transcript to the AI Done Right
`byo_demo_server` `/run` endpoint and renders the JSON review in an output channel.

This is the editor surface of the **Teleon Observer** session-review layer
(`src/teleon/observer/review.py`, exposed through `src/teleon/demos/byo_key_demo.py`).
It reviews how an AI coding session was *used*, not the correctness of the code.
Coaching output is a candidate (`serves_truth=false`).

## Usage

1. Open (or paste) an AI-session transcript in an editor tab.
2. Run **AIDevObserver: Review Session** from the Command Palette
   (`Ctrl+Shift+P` / `Cmd+Shift+P`).
3. If text is selected, only the selection is reviewed; otherwise the whole document is.
4. The findings JSON appears in the **AIDevObserver** output channel.

## What it sends

The command POSTs the following to the configured endpoint:

```json
{
  "demo": "aidevobserver",
  "byo_key": "<your key or null>",
  "inputs": {
    "messages": [{ "role": "user", "content": "<transcript>" }],
    "transcript": "<transcript>"
  }
}
```

The server runs the governed `aidevobserver` demo (`run_byo_demo`) and returns the
review result, which the extension renders verbatim.

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| `aidevobserver.apiKey` | `""` | **Bring-your-own** API key. Read at call time, sent as `byo_key`, and used transiently by the endpoint for that single call. The extension never logs it. The `aidevobserver` demo runs without a key — supply one only for key-gated surfaces. |
| `aidevobserver.endpoint` | `http://localhost:8120/run` | URL of the `byo_demo_server` `/run` endpoint. |

## Running the endpoint locally

From the repository root:

```bash
python3 scripts/byo_demo_server.py --port 8120
```

Then point `aidevobserver.endpoint` at `http://localhost:8120/run` (the default).

## Build

```bash
npm install
npm run compile   # tsc -p ./  ->  out/extension.js
```

`npm run watch` recompiles on change. Press `F5` in VS Code to launch an Extension
Development Host with the extension loaded.

## Privacy

The key lives only in your VS Code settings and is sent with each request as `byo_key`.
The endpoint scopes it to a transient environment for one call and returns only a
redacted status (`sk-…last4`). No transcript or key is persisted by the extension.
