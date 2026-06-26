// AIDevObserver — VS Code extension.
//
// Contributes the `aidevobserver.reviewSession` command: it reads the active editor's
// text (or the current selection) as an AI-session transcript, POSTs
//   { demo: "aidevobserver", byo_key, inputs }
// to the configured byo_demo_server /run endpoint, and renders the JSON review
// findings (reinvention / waste) into an output channel.
//
// The API key is a Bring-Your-Own setting (`aidevobserver.apiKey`); it is read at
// call time and sent as `byo_key`. The endpoint uses it transiently and never stores
// it. serves_truth=false (candidate coaching output).

import * as vscode from 'vscode';
import * as http from 'http';
import * as https from 'https';
import { URL } from 'url';

const COMMAND_ID = 'aidevobserver.reviewSession';
const CONFIG_SECTION = 'aidevobserver';
const OUTPUT_CHANNEL_NAME = 'AIDevObserver';
const DEMO_ID = 'aidevobserver';
const DEFAULT_ENDPOINT = 'http://localhost:8120/run';

interface ObserverInputs {
  messages: Array<{ role: string; content: string }>;
  transcript: string;
}

let channel: vscode.OutputChannel | undefined;

export function activate(context: vscode.ExtensionContext): void {
  channel = vscode.window.createOutputChannel(OUTPUT_CHANNEL_NAME);
  context.subscriptions.push(channel);

  const disposable = vscode.commands.registerCommand(COMMAND_ID, () => reviewSession());
  context.subscriptions.push(disposable);
}

export function deactivate(): void {
  if (channel) {
    channel.dispose();
    channel = undefined;
  }
}

function getChannel(): vscode.OutputChannel {
  if (!channel) {
    channel = vscode.window.createOutputChannel(OUTPUT_CHANNEL_NAME);
  }
  return channel;
}

function readTranscript(editor: vscode.TextEditor): string {
  const selection = editor.selection;
  if (selection && !selection.isEmpty) {
    return editor.document.getText(selection);
  }
  return editor.document.getText();
}

async function reviewSession(): Promise<void> {
  const out = getChannel();

  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('AIDevObserver: open an AI-session transcript in the editor first.');
    return;
  }

  const transcript = readTranscript(editor).trim();
  if (!transcript) {
    vscode.window.showWarningMessage('AIDevObserver: the active editor (or selection) is empty.');
    return;
  }

  const config = vscode.workspace.getConfiguration(CONFIG_SECTION);
  const endpoint = (config.get<string>('endpoint') || DEFAULT_ENDPOINT).trim();
  // BYO key — read transiently at call time, sent as byo_key, never logged.
  const apiKey = (config.get<string>('apiKey') || '').trim();

  const inputs: ObserverInputs = {
    messages: [{ role: 'user', content: transcript }],
    transcript,
  };
  const payload = JSON.stringify({ demo: DEMO_ID, byo_key: apiKey || null, inputs });

  out.show(true);
  out.appendLine(`[AIDevObserver] POST ${endpoint}  (demo=${DEMO_ID}, key=${apiKey ? 'byo' : 'none'}, chars=${transcript.length})`);

  try {
    const result = await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: 'AIDevObserver: reviewing session…' },
      () => postJson(endpoint, payload),
    );
    renderResult(out, result);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    out.appendLine(`[AIDevObserver] error: ${message}`);
    vscode.window.showErrorMessage(`AIDevObserver: ${message}`);
  }
}

function renderResult(out: vscode.OutputChannel, result: unknown): void {
  out.appendLine('[AIDevObserver] review findings (reinvention / waste):');
  out.appendLine(JSON.stringify(result, null, 2));

  const summary = extractSummary(result);
  if (summary) {
    vscode.window.showInformationMessage(`AIDevObserver: ${summary}`);
  }
}

function extractSummary(result: unknown): string | undefined {
  if (!result || typeof result !== 'object') {
    return undefined;
  }
  const r = result as Record<string, unknown>;
  const inner = r.result as Record<string, unknown> | undefined;
  const reviewSummary = inner && (inner.summary as Record<string, unknown> | undefined);
  if (reviewSummary && typeof reviewSummary.findings !== 'undefined') {
    return `${String(reviewSummary.findings)} finding(s) in this session.`;
  }
  if (typeof r.status === 'string') {
    return String(r.status);
  }
  return undefined;
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
          resolve(JSON.parse(text));
        } catch {
          reject(new Error(`endpoint did not return JSON: ${text.slice(0, 500)}`));
        }
      });
    });

    req.on('error', (e: Error) =>
      reject(new Error(`request failed: ${e.message} (is the byo_demo_server running at ${endpoint}?)`)),
    );
    req.write(body);
    req.end();
  });
}
