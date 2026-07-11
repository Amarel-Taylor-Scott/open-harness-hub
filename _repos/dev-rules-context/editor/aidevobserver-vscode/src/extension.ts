// AIDevObserver — VS Code + Cursor extension.
//
// A THIN editor surface over the Teleon Observer session-review layer. It never
// analyses anything in TypeScript: it shells out to the governed Python CLI
//   python3 -m src.teleon.observer.cli {list|review|live} ... --json
// (run with cwd = the workspace root, so it finds THAT project's Claude sessions)
// and renders the JSON it returns.
//
// GOVERNANCE: every finding is a governed CANDIDATE (serves_truth=false). The
// Observer reviews how an AI coding session was *used* (reinvention / waste), not
// the correctness of the code. This extension is strictly READ-ONLY — it never
// writes, edits, or republishes session content anywhere; it only displays the
// CLI's output for a human to triage.
//
// Backends:
//   * PRIMARY  — the local CLI above (used for list / review / live).
//   * FALLBACK — when no workspace folder is open there are no project sessions to
//     discover, so `reviewSession` reviews the active editor's transcript via the
//     AI Done Right `byo_demo_server` /run endpoint (POST {demo, byo_key, inputs}).
//     The BYO key (`aidevobserver.apiKey`) is read transiently at call time, sent
//     as `byo_key`, and never logged or persisted by the extension.
//
// Only standard `vscode.*` APIs are used, so the identical build runs in Cursor
// (which shares the VS Code extension host) with no proprietary dependencies.

import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as http from 'http';
import * as https from 'https';
import { URL } from 'url';

const COMMAND_REVIEW = 'aidevobserver.reviewSession';
const COMMAND_LIVE = 'aidevobserver.liveCheck';
const COMMAND_LIST = 'aidevobserver.listSessions';

const CONFIG_SECTION = 'aidevobserver';
const CLI_MODULE = 'src.teleon.observer.cli';
const DEMO_ID = 'aidevobserver';
const DEFAULT_ENDPOINT = 'http://localhost:8120/run';
const DEFAULT_PYTHON = 'python3';

const BRAND_ACCENT = '#b25fd6';
const PANEL_TITLE = 'AIDevObserver — Session Review';
const PANEL_VIEW_TYPE = 'aidevobserverReview';

interface ObserverInputs {
  messages: Array<{ role: string; content: string }>;
  transcript: string;
}

// Module state. Both are disposed in deactivate(); the panel also self-clears on close.
let statusBar: vscode.StatusBarItem | undefined;
let panel: vscode.WebviewPanel | undefined;

// --- lifecycle --------------------------------------------------------------------------------------------------
export function activate(context: vscode.ExtensionContext): void {
  statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBar.command = COMMAND_REVIEW;
  statusBar.tooltip = 'AIDevObserver — review the latest AI session (governed candidates, serves_truth=false)';
  updateStatusBar();
  statusBar.show();

  context.subscriptions.push(
    statusBar,
    vscode.commands.registerCommand(COMMAND_REVIEW, reviewSessionCommand),
    vscode.commands.registerCommand(COMMAND_LIVE, liveCheckCommand),
    vscode.commands.registerCommand(COMMAND_LIST, listSessionsCommand),
    // Optional: when the window regains focus, silently refresh the status-bar count.
    vscode.window.onDidChangeWindowState((s) => {
      if (s.focused && getAutoReview()) {
        void refreshStatusBar();
      }
    }),
  );

  void refreshStatusBar();
}

export function deactivate(): void {
  if (panel) {
    panel.dispose();
    panel = undefined;
  }
  if (statusBar) {
    statusBar.dispose();
    statusBar = undefined;
  }
}

// --- configuration ----------------------------------------------------------------------------------------------
function cfg(): vscode.WorkspaceConfiguration {
  return vscode.workspace.getConfiguration(CONFIG_SECTION);
}

function getPython(): string {
  const v = (cfg().get<string>('pythonPath') || '').trim();
  return v || DEFAULT_PYTHON;
}

/** Working directory for the CLI: explicit `cliCwd`, else the first workspace folder, else undefined. */
function getCwd(): string | undefined {
  const configured = (cfg().get<string>('cliCwd') || '').trim();
  if (configured) {
    return configured;
  }
  const folders = vscode.workspace.workspaceFolders;
  if (folders && folders.length > 0) {
    return folders[0].uri.fsPath;
  }
  return undefined;
}

function requireCwd(): string | undefined {
  const cwd = getCwd();
  if (!cwd) {
    showError("no workspace folder open — open the project folder, or set 'aidevobserver.cliCwd'.");
    return undefined;
  }
  return cwd;
}

function getEndpoint(): string {
  return (cfg().get<string>('endpoint') || '').trim() || DEFAULT_ENDPOINT;
}

function getApiKey(): string {
  return (cfg().get<string>('apiKey') || '').trim();
}

function getAutoReview(): boolean {
  return cfg().get<boolean>('autoReviewOnFocus') === true;
}

// --- CLI bridge (primary backend) -------------------------------------------------------------------------------
// Spawn the governed Python CLI, collect stdout, JSON.parse it. Rejects with the CLI's stderr on a non-zero exit.
// Never blocks the UI thread (async child process), never reimplements analysis here.
function runCli(args: string[], cwd?: string): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const python = getPython();
    const child = spawn(python, ['-m', CLI_MODULE, ...args], { cwd, shell: false });

    let stdout = '';
    let stderr = '';
    child.stdout?.on('data', (chunk: Buffer) => {
      stdout += chunk.toString();
    });
    child.stderr?.on('data', (chunk: Buffer) => {
      stderr += chunk.toString();
    });
    child.on('error', (e: Error) => {
      reject(new Error(`could not start '${python}': ${e.message} (set 'aidevobserver.pythonPath')`));
    });
    child.on('close', (code: number | null) => {
      if (code === 0) {
        const text = stdout.trim();
        try {
          resolve(text ? JSON.parse(text) : null);
        } catch (e) {
          reject(new Error(`could not parse CLI JSON: ${(e as Error).message}\n${stdout.slice(0, 500)}`));
        }
        return;
      }
      reject(new Error(stderr.trim() || stdout.trim() || `CLI exited with code ${code ?? 'null'}`));
    });
  });
}

// --- remote endpoint (fallback backend: no workspace folder -> review the active transcript) ---------------------
function reviewViaEndpoint(transcript: string): Promise<unknown> {
  const inputs: ObserverInputs = {
    messages: [{ role: 'user', content: transcript }],
    transcript,
  };
  // BYO key: read transiently here, sent as byo_key, never logged or persisted.
  const payload = JSON.stringify({ demo: DEMO_ID, byo_key: getApiKey() || null, inputs });
  return postJson(getEndpoint(), payload);
}

function postJson(endpoint: string, body: string): Promise<unknown> {
  return new Promise((resolve, reject) => {
    let url: URL;
    try {
      url = new URL(endpoint);
    } catch {
      reject(new Error(`invalid endpoint URL: ${endpoint}`));
      return;
    }
    const transport = url.protocol === 'https:' ? https : http;
    const options: http.RequestOptions = {
      method: 'POST',
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: `${url.pathname}${url.search}`,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };
    const req = transport.request(options, (res) => {
      const chunks: Buffer[] = [];
      res.on('data', (chunk: Buffer) => chunks.push(chunk));
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8');
        const status = res.statusCode || 0;
        if (status < 200 || status >= 300) {
          reject(new Error(`endpoint returned HTTP ${status}: ${text.slice(0, 500)}`));
          return;
        }
        try {
          resolve(text.trim() ? JSON.parse(text) : null);
        } catch {
          reject(new Error(`endpoint did not return JSON: ${text.slice(0, 500)}`));
        }
      });
    });
    req.on('error', (e: Error) =>
      reject(new Error(`request failed: ${e.message} (is byo_demo_server running at ${endpoint}?)`)),
    );
    req.write(body);
    req.end();
  });
}

// --- commands ---------------------------------------------------------------------------------------------------
async function reviewSessionCommand(): Promise<void> {
  try {
    const cwd = getCwd();
    let data: unknown;
    let sourceLabel: string;
    if (cwd) {
      data = await withProgress('reviewing the latest session…', () => runCli(['review', '--latest', '--json'], cwd));
      sourceLabel = 'latest project session';
    } else {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        showError('open a workspace folder to review its AI sessions, or open an editor tab with a transcript.');
        return;
      }
      const sel = editor.selection;
      const transcript = (sel && !sel.isEmpty ? editor.document.getText(sel) : editor.document.getText()).trim();
      if (!transcript) {
        showError('the active editor (or selection) is empty.');
        return;
      }
      data = await withProgress('reviewing the active transcript…', () => reviewViaEndpoint(transcript));
      sourceLabel = 'active editor transcript';
    }
    showPanel(reportToHtml(data, sourceLabel));
    updateStatusBar(countFindings(data));
  } catch (e) {
    const message = (e as Error).message;
    showPanel(errorToHtml(message));
    showError(message);
  }
}

async function liveCheckCommand(): Promise<void> {
  const cwd = requireCwd();
  if (!cwd) {
    return;
  }
  try {
    const data = await runCli(['live', '--latest', '--mode', 'advisory', '--json'], cwd);
    const surfaced = asArray((data as Record<string, unknown> | null)?.surfaced);
    updateStatusBar(surfaced.length);
    if (surfaced.length === 0) {
      void vscode.window.showInformationMessage('AIDevObserver: no live findings — clean session.');
      return;
    }
    for (const f of surfaced) {
      const item = f as Record<string, unknown>;
      const type = item.type ? `[${String(item.type)}] ` : '';
      void vscode.window.showInformationMessage(`AIDevObserver ${type}${String(item.message ?? 'finding')}`);
    }
  } catch (e) {
    showError((e as Error).message);
  }
}

async function listSessionsCommand(): Promise<void> {
  const cwd = requireCwd();
  if (!cwd) {
    return;
  }
  let sessions: Array<Record<string, unknown>>;
  try {
    const data = await runCli(['list', '--json'], cwd);
    sessions = asArray(data) as Array<Record<string, unknown>>;
  } catch (e) {
    showError((e as Error).message);
    return;
  }
  if (sessions.length === 0) {
    void vscode.window.showInformationMessage('AIDevObserver: no Claude sessions found for this workspace.');
    return;
  }

  interface SessionPick extends vscode.QuickPickItem {
    path: string;
  }
  const items: SessionPick[] = sessions.map((s) => ({
    label: String(s.project ?? s.session_id ?? 'session'),
    description: String(s.session_id ?? ''),
    detail: `${formatMtime(s.mtime)}  ·  ${String(s.path ?? '')}`,
    path: String(s.path ?? ''),
  }));
  const pick = await vscode.window.showQuickPick(items, {
    placeHolder: 'Select an AI session to review',
    matchOnDescription: true,
    matchOnDetail: true,
  });
  if (!pick || !pick.path) {
    return;
  }
  try {
    const data = await withProgress('reviewing the selected session…', () =>
      runCli(['review', '--path', pick.path, '--json'], cwd),
    );
    showPanel(reportToHtml(data, pick.label));
    updateStatusBar(countFindings(data));
  } catch (e) {
    const message = (e as Error).message;
    showPanel(errorToHtml(message));
    showError(message);
  }
}

// --- status bar -------------------------------------------------------------------------------------------------
function updateStatusBar(count?: number): void {
  if (!statusBar) {
    return;
  }
  statusBar.text = count === undefined ? '$(eye) AIDevObserver' : `$(eye) AIDevObserver: ${count}`;
}

/** Silently refresh the count for the latest session (no panel, no error popups). */
async function refreshStatusBar(): Promise<void> {
  const cwd = getCwd();
  if (!cwd) {
    return;
  }
  try {
    const data = await runCli(['review', '--latest', '--json'], cwd);
    updateStatusBar(countFindings(data));
  } catch {
    // Silent: leave the brand label in place (the explicit commands surface errors).
    updateStatusBar();
  }
}

function countFindings(data: unknown): number {
  const d = data as Record<string, unknown> | null;
  const summary = d?.summary as Record<string, unknown> | undefined;
  if (summary && typeof summary.findings === 'number') {
    return summary.findings;
  }
  if (Array.isArray(d?.report)) {
    return (d!.report as unknown[]).length;
  }
  if (Array.isArray(d?.surfaced)) {
    return (d!.surfaced as unknown[]).length;
  }
  return 0;
}

// --- webview rendering ------------------------------------------------------------------------------------------
function showPanel(body: string): void {
  if (!panel) {
    panel = vscode.window.createWebviewPanel(PANEL_VIEW_TYPE, PANEL_TITLE, vscode.ViewColumn.Active, {
      enableScripts: false,
      retainContextWhenHidden: true,
    });
    panel.onDidDispose(() => {
      panel = undefined;
    });
  }
  panel.webview.html = htmlDoc(body);
  panel.reveal(panel.viewColumn);
}

function htmlDoc(body: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    :root { --accent: ${BRAND_ACCENT}; }
    body { font-family: var(--vscode-font-family, system-ui, sans-serif); color: var(--vscode-foreground); padding: 16px 20px; line-height: 1.45; }
    h1 { font-size: 1.1rem; margin: 0 0 4px; border-bottom: 2px solid var(--accent); padding-bottom: 6px; }
    .brand { color: var(--accent); }
    .summary { opacity: .85; margin: 10px 0 18px; font-size: .85rem; }
    .group-title { color: var(--accent); text-transform: uppercase; letter-spacing: .05em; font-size: .72rem; font-weight: 700; margin: 20px 0 6px; }
    .finding { border: 1px solid var(--vscode-panel-border, #8884); border-left: 3px solid var(--accent); border-radius: 6px; padding: 10px 12px; margin: 8px 0; }
    .finding-head { display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; }
    .badge { background: var(--accent); color: #fff; border-radius: 10px; padding: 1px 9px; font-size: .72rem; font-weight: 600; white-space: nowrap; }
    .msg { font-weight: 600; }
    .row { margin-top: 6px; font-size: .88rem; }
    .k { color: var(--accent); font-weight: 600; margin-right: 6px; }
    code { background: var(--vscode-textCodeBlock-background, #8881); padding: 1px 5px; border-radius: 4px; white-space: pre-wrap; word-break: break-word; }
    .meta { margin-top: 8px; font-size: .7rem; opacity: .55; }
    .empty { padding: 28px; text-align: center; opacity: .8; font-size: 1rem; }
    .err { border-left: 3px solid #e0556c; border-radius: 6px; padding: 12px 14px; margin-top: 12px; }
  </style>
</head>
<body>
${body}
</body>
</html>`;
}

function headHtml(): string {
  return `<h1>AIDevObserver <span class="brand">— Session Review</span></h1>`;
}

function reportToHtml(data: unknown, sourceLabel: string): string {
  const d = data as Record<string, unknown> | null;
  const findings = asArray(d?.report).length ? asArray(d?.report) : asArray(d?.surfaced);
  const summary = (d?.summary as Record<string, unknown> | undefined) ?? {};

  if (findings.length === 0) {
    return htmlDoc(
      `${headHtml()}<div class="summary">${summaryLine(summary, sourceLabel, 0)}</div>` +
        `<div class="empty">no findings — clean session</div>`,
    );
  }

  const groups: Record<string, Array<Record<string, unknown>>> = {};
  for (const raw of findings) {
    const f = raw as Record<string, unknown>;
    const t = String(f.type ?? 'other');
    if (!groups[t]) {
      groups[t] = [];
    }
    groups[t].push(f);
  }
  const sections = Object.keys(groups)
    .sort()
    .map((t) => {
      const cards = groups[t].map(findingCard).join('');
      return `<div class="group-title">${escapeHtml(t)} (${groups[t].length})</div>${cards}`;
    })
    .join('');

  return htmlDoc(
    `${headHtml()}<div class="summary">${summaryLine(summary, sourceLabel, findings.length)}</div>${sections}`,
  );
}

function summaryLine(summary: Record<string, unknown>, sourceLabel: string, total: number): string {
  const bits: string[] = [`source: ${escapeHtml(sourceLabel)}`];
  if (typeof summary.messages_reviewed === 'number') {
    bits.push(`${summary.messages_reviewed} messages reviewed`);
  }
  bits.push(`${typeof summary.findings === 'number' ? summary.findings : total} findings`);
  if (typeof summary.reinventions === 'number') {
    bits.push(`${summary.reinventions} reinventions`);
  }
  if (typeof summary.waste_signals === 'number') {
    bits.push(`${summary.waste_signals} waste signals`);
  }
  const sep = ' &nbsp;·&nbsp; ';
  return `${bits.join(sep)}${sep}<em>governed candidates, serves_truth=false, read-only</em>`;
}

function findingCard(f: Record<string, unknown>): string {
  const rows: string[] = [];
  if (f.suggestion) {
    rows.push(`<div class="row"><span class="k">Suggestion</span>${escapeHtml(f.suggestion)}</div>`);
  }
  if (f.evidence !== undefined && f.evidence !== null && f.evidence !== '') {
    rows.push(`<div class="row"><span class="k">Evidence</span><code>${escapeHtml(stringify(f.evidence))}</code></div>`);
  }
  const sourceRef = f.source_ref as Record<string, unknown> | undefined;
  if (sourceRef && sourceRef.existing) {
    rows.push(`<div class="row"><span class="k">Existing</span><code>${escapeHtml(stringify(sourceRef.existing))}</code></div>`);
  }
  const meta: string[] = [];
  if (f.message_index !== undefined) {
    meta.push(`message #${escapeHtml(f.message_index)}`);
  }
  meta.push('candidate', 'serves_truth=false');

  return (
    `<div class="finding">` +
    `<div class="finding-head"><span class="badge">${confidenceLabel(f.confidence)}</span>` +
    `<span class="msg">${escapeHtml(f.message)}</span></div>` +
    rows.join('') +
    `<div class="meta">${meta.join(' · ')}</div>` +
    `</div>`
  );
}

function errorToHtml(message: string): string {
  return htmlDoc(
    `${headHtml()}` +
      `<div class="err"><strong>Could not run the observer.</strong>` +
      `<div class="row"><code>${escapeHtml(message)}</code></div>` +
      `<div class="row" style="opacity:.7">Verify that ` +
      `<code>${escapeHtml(getPython())} -m ${escapeHtml(CLI_MODULE)} review --latest --json</code>` +
      ` runs from the workspace root.</div></div>`,
  );
}

function confidenceLabel(c: unknown): string {
  if (typeof c === 'number') {
    return c <= 1 ? `${Math.round(c * 100)}%` : String(c);
  }
  if (typeof c === 'string' && c) {
    return escapeHtml(c);
  }
  return 'n/a';
}

// --- small utilities --------------------------------------------------------------------------------------------
function asArray(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

function stringify(v: unknown): string {
  if (typeof v === 'string') {
    return v;
  }
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

function escapeHtml(s: unknown): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatMtime(m: unknown): string {
  if (typeof m === 'number') {
    const ms = m < 1e12 ? m * 1000 : m; // epoch seconds (st_mtime) -> ms
    return new Date(ms).toLocaleString();
  }
  if (typeof m === 'string' && m) {
    const d = new Date(m);
    return Number.isNaN(d.getTime()) ? m : d.toLocaleString();
  }
  return '';
}

function withProgress<T>(title: string, task: () => Promise<T>): Thenable<T> {
  return vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: `AIDevObserver: ${title}` },
    () => task(),
  );
}

function showError(message: string): void {
  void vscode.window.showErrorMessage(`AIDevObserver: ${message}`);
}
