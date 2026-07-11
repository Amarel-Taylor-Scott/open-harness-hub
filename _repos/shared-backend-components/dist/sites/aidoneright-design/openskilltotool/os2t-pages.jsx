/* global React, navigate */
// openskilltotool/os2t-pages.jsx — bespoke product surfaces for OpenSkillToTool.io.
// Rendered through the shared hub's config-gated hooks (extraRoutes / entryExtra /
// convert.render) so the site stays branded-house: these compose the same .oh-*
// primitives + tokens, they're just the skill→tool-specific substance the generic
// registry can't know about — the backend pipeline, the API surface, the real
// converter anatomy (source skill → typed contract → scopes → determinism/parity →
// fixtures), and a true multi-step convert wizard.

// ---------------------------------------------------------------------------
// Per-converter substance. Each entry's source skill (open-ended know-how) and the
// deterministic tool it collapses into: typed contract, MCP manifest, HTTP call,
// least-privilege scopes, determinism + eval-parity report, and worked fixtures.
// ---------------------------------------------------------------------------
const OS2T_DATA = {
  'summarize-doc': {
    skillTag: 'Open-ended · context-guided summarization',
    prompt: 'Given a document and an audience, read it in full,\ndecide what matters, and write a faithful summary.\nGround every claim in the source and cite the span.',
    input: '{\n  "document":  "string",   // full text or URL\n  "audience":  "string?",  // optional framing\n  "max_words": "integer?"  // default 180\n}',
    output: '{\n  "summary":    "string",\n  "citations":  [{ "quote": "string", "offset": "integer" }],\n  "word_count": "integer"\n}',
    mcp: '{\n  "name": "summarize_doc",\n  "description": "Summarize a document, with cited spans.",\n  "inputSchema": { "$ref": "contract#/input" },\n  "annotations": { "readOnly": true, "deterministic": true }\n}',
    http: 'POST /v1/tools/summarize-doc/call\nAuthorization: Bearer sk_live_…\n\n{ "document": "10-K excerpt…", "max_words": 80 }',
    scopes: [['read:document', 'read', 'Reads the document text passed in the call. No network, no write.']],
    parity: { det: '2,000/2,000', detL: 'identical output shape, fuzzed inputs', skill: '4.8', tool: '4.8', lat: '1.4s', latL: 'p95 latency', valid: '100%', validL: 'schema-validated' },
    tests: [{ in: '{ "document": "Revenue rose…", "max_words": 40 }', out: '{ "summary": "Revenue up 12% YoY…",\n  "citations": [{ "quote": "Revenue increased", "offset": 412 }] }' }],
  },
  'classify-risk': {
    skillTag: 'Open-ended · context-guided risk judgement',
    prompt: 'Read a record against the supplied taxonomy.\nReason about edge cases, then return one label\nwith a confidence and a cited rationale.',
    input: '{\n  "record":   "object",\n  "taxonomy": "string?"  // defaults to org policy\n}',
    output: '{\n  "label":      "enum(low|medium|high|critical)",\n  "confidence": "number",   // 0–1\n  "rationale":  "string",\n  "citations":  ["string"]\n}',
    mcp: '{\n  "name": "classify_risk",\n  "description": "Label a record\u2019s risk, with rationale.",\n  "inputSchema": { "$ref": "contract#/input" },\n  "annotations": { "readOnly": true, "deterministic": true }\n}',
    http: 'POST /v1/tools/classify-risk/call\nAuthorization: Bearer sk_live_…\n\n{ "record": { "vendor": "…" }, "taxonomy": "tprm-v3" }',
    scopes: [['read:record', 'read', 'Reads the record object passed in the call. No external lookups.']],
    parity: { det: '2,000/2,000', detL: 'stable label + ordering', skill: '4.7', tool: '4.7', lat: '0.9s', latL: 'p95 latency', valid: '100%', validL: 'schema-validated' },
    tests: [{ in: '{ "record": { "vendor": "Acme", "country": "—" } }', out: '{ "label": "high", "confidence": 0.82,\n  "rationale": "Sanctioned jurisdiction…", "citations": ["OFAC SDN"] }' }],
  },
  'extract-fields': {
    skillTag: 'Open-ended · context-guided extraction',
    prompt: 'Given a document and a target schema, locate and\nnormalise each field. If a field is absent, return\nnull rather than guessing. Validate before returning.',
    input: '{\n  "document": "string",\n  "schema":   "object"   // JSON Schema of the record\n}',
    output: '{\n  "record": "object",   // matches the supplied schema\n  "valid":  "boolean",\n  "missing": ["string"]\n}',
    mcp: '{\n  "name": "extract_fields",\n  "description": "Extract a typed record from a document.",\n  "inputSchema": { "$ref": "contract#/input" },\n  "annotations": { "readOnly": true, "deterministic": true }\n}',
    http: 'POST /v1/tools/extract-fields/call\nAuthorization: Bearer sk_live_…\n\n{ "document": "invoice.pdf…", "schema": { "total": "number" } }',
    scopes: [['read:document', 'read', 'Reads the document passed in the call. Output validated against the caller\u2019s schema.']],
    parity: { det: '2,000/2,000', detL: 'byte-stable JSON records', skill: '4.9', tool: '4.9', lat: '1.1s', latL: 'p95 latency', valid: '100%', validL: 'schema-validated' },
    tests: [{ in: '{ "document": "Invoice #4471…",\n  "schema": { "total": "number", "due": "date" } }', out: '{ "record": { "total": 18240.5, "due": "2026-07-01" },\n  "valid": true, "missing": [] }' }],
  },
  'draft-reply': {
    skillTag: 'Open-ended · context-guided drafting',
    prompt: 'Read a thread and an intent. Draft a reply in the\nthread\u2019s voice. Never send without an explicit,\nscoped, rate-limited send step the caller approves.',
    input: '{\n  "thread": "message[]",\n  "intent": "string"\n}',
    output: '{\n  "draft":     "string",\n  "tone":      "string",\n  "send_token": "string"   // single-use, scope-gated\n}',
    mcp: '{\n  "name": "draft_reply",\n  "description": "Draft a thread reply; gated send.",\n  "inputSchema": { "$ref": "contract#/input" },\n  "annotations": { "readOnly": false, "deterministic": true }\n}',
    http: 'POST /v1/tools/draft-reply/call\nAuthorization: Bearer sk_live_…\n\n{ "thread": [ … ], "intent": "decline politely" }',
    scopes: [
      ['read:thread', 'read', 'Reads the message thread passed in the call.'],
      ['send:message', 'rate', 'Single-use, rate-limited send — only via the returned send_token, caller-approved.'],
    ],
    parity: { det: '2,000/2,000', detL: 'stable draft + token issuance', skill: '4.4', tool: '4.4', lat: '1.0s', latL: 'p95 latency', valid: '100%', validL: 'schema-validated' },
    tests: [{ in: '{ "thread": [ "Can you do Tuesday?" ],\n  "intent": "decline, offer Thursday" }', out: '{ "draft": "Tuesday\u2019s tight — Thursday works?",\n  "tone": "warm", "send_token": "st_9f2c…" }' }],
  },
  'review-diff': {
    skillTag: 'Open-ended · context-guided code review',
    prompt: 'Read a diff against the repo\u2019s guidelines. Comment\nonly where it matters, anchored to file + line, with\na severity and a concrete suggestion.',
    input: '{\n  "diff":       "string",   // unified diff\n  "guidelines": "string?"\n}',
    output: '{\n  "comments": [\n    { "path": "string", "line": "integer",\n      "severity": "enum", "body": "string" }\n  ]\n}',
    mcp: '{\n  "name": "review_diff",\n  "description": "Structured review of a unified diff.",\n  "inputSchema": { "$ref": "contract#/input" },\n  "annotations": { "readOnly": true, "deterministic": true }\n}',
    http: 'POST /v1/tools/review-diff/call\nAuthorization: Bearer sk_live_…\n\n{ "diff": "@@ -1,4 +1,6 @@ …" }',
    scopes: [['read:repo', 'read', 'Reads the diff passed in the call. No clone, no write to the repo.']],
    parity: { det: '2,000/2,000', detL: 'stable comment set + ordering', skill: '4.6', tool: '4.6', lat: '1.6s', latL: 'p95 latency', valid: '100%', validL: 'schema-validated' },
    tests: [{ in: '{ "diff": "@@ … password = \u2018hunted2\u2019 …" }', out: '{ "comments": [ { "path": "auth.py", "line": 42,\n  "severity": "high", "body": "Hard-coded secret." } ] }' }],
  },
  'triage-ticket': {
    skillTag: 'Open-ended · context-guided triage',
    prompt: 'Read a ticket. Decide the right queue and priority\nfrom the org\u2019s routing rules, and explain why with\nthe signals you used.',
    input: '{\n  "ticket": "object"\n}',
    output: '{\n  "queue":    "string",\n  "priority": "enum(P0|P1|P2|P3)",\n  "reasons":  ["string"]\n}',
    mcp: '{\n  "name": "triage_ticket",\n  "description": "Route + prioritise a ticket, with reasons.",\n  "inputSchema": { "$ref": "contract#/input" },\n  "annotations": { "readOnly": false, "deterministic": true }\n}',
    http: 'POST /v1/tools/triage-ticket/call\nAuthorization: Bearer sk_live_…\n\n{ "ticket": { "subject": "Login 500", "plan": "enterprise" } }',
    scopes: [
      ['read:ticket', 'read', 'Reads the ticket object passed in the call.'],
      ['write:ticket.label', 'write', 'Writes only the routing label + priority field — nothing else on the ticket.'],
    ],
    parity: { det: '2,000/2,000', detL: 'stable queue + priority', skill: '4.5', tool: '4.5', lat: '0.7s', latL: 'p95 latency', valid: '100%', validL: 'schema-validated' },
    tests: [{ in: '{ "ticket": { "subject": "Login 500",\n  "plan": "enterprise" } }', out: '{ "queue": "auth-oncall", "priority": "P1",\n  "reasons": ["5xx", "enterprise plan"] }' }],
  },
};

const SKILLS_HUB = '../openskillshub/OpenSkillsHub.html';
const TOOLS_HUB = '../opentoolshub/OpenToolsHub.html';

function os2tData(e) {
  return OS2T_DATA[e.id] || {
    skillTag: 'Open-ended · context-guided know-how',
    prompt: 'A governed, context-guided skill from OpenSkillsHub.',
    input: '{ "input": "object" }', output: '{ "result": "object" }',
    mcp: '{ "name": "' + e.id.replace(/-/g, '_') + '" }', http: 'POST /v1/tools/' + e.id + '/call',
    scopes: [['read:input', 'read', 'Reads only the input passed in the call.']],
    parity: { det: '2,000/2,000', detL: 'identical output shape', skill: e.score, tool: e.score, lat: '1.2s', latL: 'p95 latency', valid: '100%', validL: 'schema-validated' },
    tests: [{ in: '{ "input": … }', out: '{ "result": … }' }],
  };
}

function Code({ children }) { return <pre className="os2t-codeblock">{children}</pre>; }

// ===========================================================================
// entryExtra — the rich converter anatomy on every entry-detail page
// ===========================================================================
function Os2tConverterDetail({ e }) {
  const d = os2tData(e);
  const skillRef = (e.deps && e.deps[0]) || ('skill:' + e.id);
  const [tab, setTab] = React.useState('schema');
  const contract = { schema: 'INPUT\n' + d.input + '\n\nOUTPUT\n' + d.output, mcp: d.mcp, http: d.http };
  return (
    <React.Fragment>
      {/* source skill — the open-ended input */}
      <div className="oh-card oh-card--pad os2t-section">
        <span className="os2t-eyebrow">Source skill · open-ended input</span>
        <div className="os2t-source">
          <div>
            <div className="os2t-source-id mono">{skillRef}</div>
            <div className="os2t-source-tag">{d.skillTag}</div>
          </div>
          <a className="os2t-source-link" href={SKILLS_HUB} target="_blank" rel="noreferrer">View on OpenSkillsHub ↗</a>
          <div className="os2t-source-prompt"><Code>{d.prompt}</Code></div>
        </div>
      </div>

      {/* generated deterministic tool contract */}
      <div className="oh-card oh-card--pad os2t-section">
        <span className="os2t-eyebrow">Generated tool contract · deterministic output</span>
        <div className="os2t-tabbar">
          {[['schema', 'JSON Schema'], ['mcp', 'MCP manifest'], ['http', 'HTTP call']].map(([k, l]) => (
            <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>
          ))}
        </div>
        <Code>{contract[tab]}</Code>
      </div>

      {/* least-privilege scope manifest */}
      <div className="oh-card oh-card--pad os2t-section">
        <span className="os2t-eyebrow">Scope manifest · least privilege</span>
        <table className="os2t-scopes">
          <thead><tr><th>Scope</th><th>Access</th><th>Why it needs it</th></tr></thead>
          <tbody>
            {d.scopes.map(([sc, lvl, why]) => (
              <tr key={sc}>
                <td className="sc">{sc}</td>
                <td><span className={'os2t-lvl ' + lvl}>{lvl === 'rate' ? 'rate-limited' : lvl}</span></td>
                <td className="why">{why}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* determinism & eval parity */}
      <div className="oh-card oh-card--pad os2t-section">
        <span className="os2t-eyebrow">Determinism &amp; eval parity</span>
        <div className="os2t-stats">
          <div className="oh-card os2t-stat"><div className="sv">{d.parity.det}</div><div className="sl">{d.parity.detL}</div></div>
          <div className="oh-card os2t-stat"><div className="sv">★ {d.parity.skill} <span className="accent">→ {d.parity.tool}</span></div><div className="sl">eval carried skill → tool</div></div>
          <div className="oh-card os2t-stat"><div className="sv">{d.parity.lat}</div><div className="sl">{d.parity.latL}</div></div>
          <div className="oh-card os2t-stat"><div className="sv accent" style={{ color: 'var(--accent)' }}>{d.parity.valid}</div><div className="sl">{d.parity.validL}</div></div>
        </div>
        <p className="os2t-parity-note">The skill stays open-ended; the tool is frozen. We replay the skill’s eval pack against the
          generated contract and run a determinism harness — same input, same output shape, every call — and gate publication on parity.</p>
      </div>

      {/* worked fixtures */}
      <div className="oh-card oh-card--pad os2t-section">
        <span className="os2t-eyebrow">Test fixtures · input → output</span>
        <div className="os2t-fixtures">
          {d.tests.map((t, i) => (
            <div className="os2t-fixture" key={i}>
              <div><div className="os2t-fixture-label">request</div><Code>{t.in}</Code></div>
              <div className="os2t-fixture-arrow">→</div>
              <div><div className="os2t-fixture-label">response</div><Code>{t.out}</Code></div>
            </div>
          ))}
        </div>
      </div>
    </React.Fragment>
  );
}

// ===========================================================================
// Backend / architecture — how a skill becomes a tool
// ===========================================================================
const OS2T_STAGES = [
  ['Ingest the skill', 'Pull the governed skill spec, its eval pack and signed provenance from OpenSkillsHub. Nothing is converted that isn’t already governed.', ['in · skill:<id>@ver', 'eval-pack', 'provenance']],
  ['Infer the contract', 'Derive a typed JSON-Schema input/output contract from the skill’s interface and worked examples, then freeze the shape so every call is identical.', ['examples', 'out · JSON Schema']],
  ['Bind least-privilege scopes', 'Compute the minimum scopes the skill actually touches — read this, write only that. The tool can do nothing it didn’t declare; nothing blind.', ['capability analysis', 'out · scope manifest']],
  ['Harden & evaluate', 'Run the determinism harness — same input, same output shape, thousands of runs — and replay the skill’s eval pack against the tool. Publication is gated on parity.', ['determinism harness', 'eval replay', 'out · parity report']],
  ['Sign & publish', 'Carry the eval score and provenance across, sign the tool contract (cosign · SLSA L3 · in-toto), and emit it to OpenToolsHub — callable over MCP or HTTP.', ['cosign · SLSA L3', 'out · OpenToolsHub entry']],
];

function Os2tArchitecture() {
  return (
    <div className="ohs-page">
      <div className="ohs-pagehead oh-pagehead">
        <div className="eyebrow os2t-eyebrow">Backend · architecture</div>
        <h1>How a skill becomes a tool.</h1>
        <p className="sub">OpenSkillToTool runs the same unbounded → deterministic spine Teleon runs, applied to packaging.
          A governed, open-ended skill goes in; a typed, scoped, signed, deterministic tool contract comes out — in five stages.</p>
      </div>

      <div className="oh-card oh-card--pad">
        <div className="os2t-pipe">
          {OS2T_STAGES.map(([t, d, io], i) => (
            <div className="os2t-stage" key={t}>
              <div className="os2t-stage-rail"><div className="os2t-stage-num">{i + 1}</div><div className="os2t-stage-line" /></div>
              <div className="os2t-stage-body">
                <h3>{t}</h3>
                <p>{d}</p>
                <div className="os2t-stage-io">{io.map((c) => <span key={c} className={'os2t-iochip' + (c.startsWith('out') ? ' out' : '')}>{c}</span>)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="os2t-cols2" style={{ marginTop: 16 }}>
        <div className="oh-card oh-card--pad">
          <span className="os2t-eyebrow" style={{ display: 'block', marginBottom: 12 }}>The tool contract</span>
          <Code>{'{\n  "id": "summarize-doc",\n  "version": "1.4.0",\n  "from_skill": "skill:summarize-doc@2.1",\n  "input":  { "$schema": "json-schema/draft-07", … },\n  "output": { "$schema": "json-schema/draft-07", … },\n  "scopes": ["read:document"],\n  "deterministic": true,\n  "eval": { "score": 4.8, "pack": "summarize@v3" },\n  "provenance": { "sig": "cosign", "slsa": "L3" }\n}'}</Code>
        </div>
        <div className="oh-card oh-card--pad">
          <span className="os2t-eyebrow" style={{ display: 'block', marginBottom: 12 }}>Runtime</span>
          <div className="os2t-runtime">
            {[
              ['Transport', 'Callable over MCP or HTTP — the same contract, two front doors.'],
              ['Scope enforcement', 'Every call is checked against the declared scopes at invocation time; out-of-scope is refused.'],
              ['Determinism guard', 'Output is validated against the frozen schema before it returns. Same input → same shape.'],
              ['Provenance', 'The skill’s signed origin + eval score ride along; discovery is never trust.'],
              ['Versioning', 'Semver-pinned with a changelog; a new skill version produces a new tool version.'],
            ].map(([k, v]) => (
              <div className="os2t-runtime-row" key={k}><span className="rk">{k}</span><span className="rv">{v}</span></div>
            ))}
          </div>
        </div>
      </div>

      <div className="oh-card oh-card--pad" style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: 14, color: 'var(--fg-muted)', lineHeight: 1.5, maxWidth: '52ch' }}>
          The pipeline is the product. Try it on a real skill in the workbench, or read the call surface in the API reference.</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="oh-btn oh-btn--primary" onClick={() => navigate('/convert')}>Open the workbench →</button>
          <button className="oh-btn oh-btn--ghost" onClick={() => navigate('/api')}>API reference</button>
        </div>
      </div>
    </div>
  );
}

// ===========================================================================
// API reference
// ===========================================================================
const OS2T_ENDPOINTS = [
  ['POST', '/v1/convert', 'Convert a governed skill into a tool contract', 'post',
    'POST /v1/convert\nAuthorization: Bearer sk_live_…\nContent-Type: application/json\n\n{ "skill": "skill:summarize-doc@2.1", "eval_pack": "summarize@v3" }\n\n→ 201 Created\n{ "id": "summarize-doc", "version": "1.4.0",\n  "contract_url": "/v1/tools/summarize-doc/contract",\n  "deterministic": true, "scopes": ["read:document"] }'],
  ['GET', '/v1/tools/:id/contract', 'Fetch the typed contract — schema, scopes, provenance', 'get',
    'GET /v1/tools/summarize-doc/contract\nAuthorization: Bearer sk_live_…\n\n→ 200 OK\n{ "input": { … }, "output": { … },\n  "scopes": ["read:document"],\n  "provenance": { "sig": "cosign", "slsa": "L3" } }'],
  ['POST', '/v1/tools/:id/call', 'Invoke the tool — deterministic, scope-enforced', 'post',
    'POST /v1/tools/summarize-doc/call\nAuthorization: Bearer sk_live_…\nContent-Type: application/json\n\n{ "document": "…", "max_words": 80 }\n\n→ 200 OK\n{ "summary": "…", "citations": [ … ], "word_count": 78 }'],
  ['GET', '/v1/tools/:id', 'Metadata — versions, eval score, provenance', 'get',
    'GET /v1/tools/summarize-doc\nAuthorization: Bearer sk_live_…\n\n→ 200 OK\n{ "id": "summarize-doc", "version": "1.4.0",\n  "eval": 4.8, "installs": "6.4k", "from_skill": "skill:summarize-doc@2.1" }'],
  ['GET', '/v1/tools', 'List & search converters', 'get',
    'GET /v1/tools?facet=Research&q=summar\nAuthorization: Bearer sk_live_…\n\n→ 200 OK\n{ "results": [ { "id": "summarize-doc", "eval": 4.8 } ], "total": 1 }'],
];

function Os2tApiRef() {
  const [open, setOpen] = React.useState(2);
  return (
    <div className="ohs-page">
      <div className="ohs-pagehead oh-pagehead">
        <div className="eyebrow os2t-eyebrow">Developers · API</div>
        <h1>API reference.</h1>
        <p className="sub">A small, typed surface. Convert a skill, fetch its contract, and call the deterministic tool —
          over HTTP or MCP. Every response validates against the published schema.</p>
      </div>

      <div className="oh-card oh-card--pad" style={{ marginBottom: 16 }}>
        <div className="os2t-runtime">
          <div className="os2t-runtime-row"><span className="rk">Base URL</span><span className="rv mono" style={{ fontFamily: 'var(--font-mono)' }}>https://api.openskilltotool.io</span></div>
          <div className="os2t-runtime-row"><span className="rk">Auth</span><span className="rv">Bearer API key — create one under <a className="ohs-navlink" onClick={() => navigate('/keys')}>API keys</a>.</span></div>
          <div className="os2t-runtime-row"><span className="rk">MCP</span><span className="rv">Every tool is also exposed as an MCP server: <span style={{ fontFamily: 'var(--font-mono)' }}>mcp://openskilltotool.io/&lt;id&gt;</span></span></div>
        </div>
      </div>

      <div className="os2t-endpoints">
        {OS2T_ENDPOINTS.map(([m, path, desc, cls, ex], i) => (
          <React.Fragment key={path}>
            <div className={'os2t-ep' + (open === i ? ' on' : '')} onClick={() => setOpen(open === i ? -1 : i)}>
              <span className={'os2t-ep-m ' + cls}>{m}</span>
              <span className="os2t-ep-path">{path}</span>
              <span className="os2t-ep-desc">{desc}</span>
            </div>
            {open === i && <div className="os2t-ep-detail"><Code>{ex}</Code></div>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

// ===========================================================================
// Convert wizard — the signature interface, as a true multi-step flow
// ===========================================================================
const OS2T_WIZ_STEPS = ['Choose skill', 'Review contract', 'Bind scopes', 'Harden & publish'];

function Os2tConvertWizard({ cfg }) {
  const inputs = cfg.entries.map((e) => ({ e, skill: (e.deps && e.deps[0]) || ('skill:' + e.id) }));
  const [step, setStep] = React.useState(0);
  const [sel, setSel] = React.useState(0);
  const [pct, setPct] = React.useState(0);
  const [running, setRunning] = React.useState(false);
  const [done, setDone] = React.useState(false);
  const cur = inputs[sel];
  const d = os2tData(cur.e);

  React.useEffect(() => { setPct(0); setDone(false); setRunning(false); }, [sel]);
  const runHarden = () => {
    setRunning(true); setDone(false); setPct(0);
    let p = 0;
    const t = setInterval(() => {
      p += Math.random() * 22 + 10; if (p >= 100) { p = 100; clearInterval(t); setRunning(false); setDone(true); }
      setPct(Math.round(p));
    }, 220);
  };

  return (
    <div className="ohs-page">
      <div className="ohs-pagehead oh-pagehead">
        <div className="eyebrow os2t-eyebrow">{cfg.kind}</div>
        <h1>Skill → tool workbench</h1>
        <p className="sub">Pick a governed, open-ended skill and walk it through to a deterministic, typed, signed tool contract —
          schema, least-privilege scopes, and eval + provenance carried across.</p>
      </div>

      <div className="os2t-wiz-steps">
        {OS2T_WIZ_STEPS.map((l, i) => (
          <div className={'os2t-wiz-step' + (i === step ? ' active' : '') + (i < step ? ' done' : '')} key={l}>
            <span className="os2t-wiz-dot">{i < step ? '✓' : i + 1}</span>
            <span className="os2t-wiz-label">{l}</span>
            {i < OS2T_WIZ_STEPS.length - 1 && <span className="os2t-wiz-bar" />}
          </div>
        ))}
      </div>

      <div className="oh-card oh-card--pad">
        <div className="os2t-wiz-body">
          {step === 0 && (
            <React.Fragment>
              <span className="os2t-eyebrow" style={{ display: 'block', marginBottom: 12 }}>Choose an open-ended skill</span>
              <div className="os2t-wiz-pick">
                {inputs.map((it, i) => (
                  <button key={it.e.id} className={'os2t-wiz-pickitem' + (i === sel ? ' on' : '')} onClick={() => setSel(i)}>
                    <span><span className="os2t-wiz-pickname">{it.skill}</span><span className="os2t-wiz-picktag" style={{ display: 'block' }}>{os2tData(it.e).skillTag}</span></span>
                    <span className="oh-badge oh-badge--sm mono">★ {it.e.score}</span>
                  </button>
                ))}
              </div>
            </React.Fragment>
          )}
          {step === 1 && (
            <React.Fragment>
              <span className="os2t-eyebrow" style={{ display: 'block', marginBottom: 12 }}>Inferred contract for {cur.skill}</span>
              <div className="os2t-cols2">
                <div><div className="os2t-fixture-label">input schema</div><Code>{d.input}</Code></div>
                <div><div className="os2t-fixture-label">output schema</div><Code>{d.output}</Code></div>
              </div>
              <p className="os2t-parity-note">Derived from the skill’s interface and worked examples, then frozen. This shape is the contract — every call returns it.</p>
            </React.Fragment>
          )}
          {step === 2 && (
            <React.Fragment>
              <span className="os2t-eyebrow" style={{ display: 'block', marginBottom: 12 }}>Least-privilege scopes</span>
              {d.scopes.map(([sc, lvl, why]) => (
                <div className="os2t-scopecheck" key={sc}>
                  <span className="cb">✓</span>
                  <span><span className="mono" style={{ fontSize: 12.5, color: 'var(--fg)' }}>{sc}</span> <span className={'os2t-lvl ' + lvl} style={{ marginLeft: 6 }}>{lvl === 'rate' ? 'rate-limited' : lvl}</span><div style={{ fontSize: 12.5, color: 'var(--fg-muted)', marginTop: 4, lineHeight: 1.5 }}>{why}</div></span>
                </div>
              ))}
              <p className="os2t-parity-note">Computed from what the skill actually touches. The tool can do nothing outside this manifest.</p>
            </React.Fragment>
          )}
          {step === 3 && (
            <React.Fragment>
              <span className="os2t-eyebrow" style={{ display: 'block', marginBottom: 12 }}>Harden &amp; publish {cur.e.name}</span>
              <div className="os2t-progress"><i style={{ width: pct + '%' }} /></div>
              <div className="os2t-runlog">
                {pct >= 25 && <div><span className="ok">✓</span> determinism harness · {d.parity.det} identical shapes</div>}
                {pct >= 55 && <div><span className="ok">✓</span> eval pack replayed · ★ {d.parity.skill} → ★ {d.parity.tool} parity held</div>}
                {pct >= 80 && <div><span className="ok">✓</span> contract signed · cosign · SLSA L3 · in-toto</div>}
                {done && <div><span className="ok">✓</span> published to OpenToolsHub as <span className="mono">{cur.e.id}@{cur.e.ver || '1.0.0'}</span></div>}
                {!running && pct === 0 && <div style={{ color: 'var(--fg-faint)' }}>Run the harden step to check determinism, replay the eval pack, sign and publish.</div>}
              </div>
              {done && (
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 16 }}>
                  <button className="oh-btn oh-btn--primary" onClick={() => navigate('/e/' + cur.e.id)}>Open the tool →</button>
                  <button className="oh-btn oh-btn--ghost" onClick={() => window.open(TOOLS_HUB, '_blank')}>View on OpenToolsHub ↗</button>
                </div>
              )}
            </React.Fragment>
          )}
        </div>

        <div className="os2t-wiz-foot">
          <button className="oh-btn oh-btn--ghost" disabled={step === 0} onClick={() => setStep(Math.max(0, step - 1))} style={{ opacity: step === 0 ? .4 : 1 }}>← Back</button>
          {step < 3
            ? <button className="oh-btn oh-btn--primary" onClick={() => setStep(step + 1)}>Next: {OS2T_WIZ_STEPS[step + 1]} →</button>
            : <button className="oh-btn oh-btn--primary" onClick={runHarden} disabled={running}>{running ? 'Hardening…' : done ? 'Re-run' : 'Run harden & publish'}</button>}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Os2tConverterDetail, Os2tArchitecture, Os2tApiRef, Os2tConvertWizard });
