/* global React, StoreCtx, navigate, PRIMS */
// Private Registry (bring-your-own) + Connect/MCP (local-first bridge)

const PRIV = [
  { k: 'knowledge', name: 'Acme supplier master', id: 'knowledge-corpus/acme-suppliers', tag: 'priv', meta: '⛁ 14k rows · private pgvector · local-only' },
  { k: 'knowledge', name: 'Internal ESG policy', id: 'knowledge-corpus/acme-esg-policy', tag: 'priv', meta: '⛁ SharePoint · ↻ synced nightly' },
  { k: 'action', name: 'Deal-memo retriever', id: 'processor/deal-memo', tag: 'priv', meta: '⚡ processor · runs in your VPC' },
  { k: 'conditional', name: 'Acme risk thresholds', id: 'conditional/acme-tiers', tag: 'priv', meta: '◈ rule-pack · overrides the public gate' },
  { k: 'action', name: 'Cite-first ESG counsel', id: 'harness/esg-cite-first·acme', tag: 'fork', meta: '⚡ forked-from harness/esg-cite-first@1.3.0' },
  { k: 'knowledge', name: 'Procurement runbook', id: 'knowledge-corpus/acme-runbook', tag: 'ingest', meta: '⛁ managed-ingested · gate-passed' },
];
function PRegistry() {
  const { toast } = React.useContext(StoreCtx);
  const badge = (t) => t === 'priv' ? <span className="pt-priv-badge priv">🔒 private</span> : t === 'fork' ? <span className="pt-priv-badge fork">⑂ forked</span> : <span className="pt-priv-badge ingest">⚙ ingested</span>;
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Private registry</h1><div className="sub">Your proprietary components &amp; context — your IP, scoped to your workspace. Gaps are filled by governed components from the catalog.</div></div>
      <div className="pt-reg-cover">
        <div className="seg"><span className="v gov" style={{ color: 'var(--verified)' }}>12</span><span className="k">your private components</span></div>
        <span className="plus">+</span>
        <div className="seg"><span className="v">34</span><span className="k">governed, filling gaps</span></div>
        <span className="covbar"><span className="priv" style={{ width: '26%' }} /><span className="pub" style={{ width: '74%' }} /></span>
        <span style={{ fontSize: 11.5, color: 'var(--fg-muted)' }}>26% your IP · 74% from OpenHubForAI</span>
      </div>
      <div className="pt-toolbar">
        <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => toast('New component — pick a primitive')}>+ New component</button>
        <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/connect')}>Connect a source</button>
        <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/improve')}>Import a pipeline</button>
        <span className="pt-spacer" />
        <span className="oh-badge mono">visibility · workspace</span>
      </div>
      <div className="pt-cards-grid">
        {PRIV.map((c) => {
          const p = PRIMS[c.k];
          return (
            <div key={c.id} className="oh-comp-card" style={{ ['--p-action']: `var(${p.v})`, cursor: 'pointer' }} onClick={() => toast('Private component · stays in your workspace')}>
              <div className="oh-cc-top">
                <span className="oh-cc-prim" style={{ color: `var(${p.v})` }}>{p.glyph} {p.label.split(' ')[0].toUpperCase()}</span>
                <span className="spacer" />{badge(c.tag)}
              </div>
              <h4 className="oh-cc-name">{c.name}</h4>
              <div className="oh-cc-id mono">{c.id}</div>
              <div className="oh-cc-divider" />
              <div className="oh-node-facts" style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--fg-muted)' }}>{c.meta}</div>
            </div>
          );
        })}
      </div>
      <div className="oh-state-msg blocked" style={{ marginTop: 16, background: 'color-mix(in srgb, var(--verified) 7%, transparent)', borderColor: 'color-mix(in srgb, var(--verified) 30%, var(--line))' }}>
        <span className="gl" style={{ color: 'var(--verified)' }}>🛡</span>
        <span>Private components never leave your environment. The lift gate still applies inside your workspace — a proprietary component must beat a bare model to be promotable, and the measurement runs <b>locally</b>.</span>
      </div>
    </div>
  );
}

/* ---------------- CONNECT / MCP ---------------- */
function PConnect() {
  const { toast } = React.useContext(StoreCtx);
  const [boundary, setBoundary] = React.useState('gapfill');
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Connect — local-first, bridged by MCP</h1><div className="sub">Keep proprietary context in your environment. Your agents source it locally and call OpenHubForAI over MCP to fill the gaps — only queries &amp; governed components cross the line, never your data.</div></div>

      <div className="pt-bridge">
        <div className="pt-zone private">
          <div className="zh">Your environment<span className="tag">private</span></div>
          <div className="zsub">Runs in your VPC / on-prem · proprietary</div>
          <div className="pt-mcpnode agent"><span className="ic">◐</span><span className="nm">Your agent<small>claude · cursor · internal</small></span></div>
          <div className="pt-mcpnode"><span className="ic">🗂</span><span className="nm">Filesystem · SOPs<small>mcp://local/files</small></span></div>
          <div className="pt-mcpnode"><span className="ic">⛁</span><span className="nm">Private pgvector · deal memos<small>mcp://local/vector</small></span></div>
          <div className="pt-mcpnode"><span className="ic">⚙</span><span className="nm">Internal ERP API<small>mcp://local/erp</small></span></div>
        </div>
        <div className="pt-bridge-mid">
          <span className="line" />
          <span className="lab">MCP · boundary</span>
          <span className="pt-bridge-arrow"><span className="a">fill gaps →</span><span>← components</span></span>
        </div>
        <div className="pt-zone governed">
          <div className="zh">OpenHubForAI<span className="tag">governed</span></div>
          <div className="zsub">Vetted catalog · lift-gated · provenance</div>
          <div className="pt-mcpnode"><span className="ic">⚡</span><span className="nm">Governed components<small>1,284 promoted · ▲ measured lift</small></span></div>
          <div className="pt-mcpnode"><span className="ic">⛁</span><span className="nm">Knowledge corpora<small>CSDDD · OFAC · GxP · ✔ sourced</small></span></div>
          <div className="pt-mcpnode"><span className="ic">🛡</span><span className="nm">Lift &amp; provenance gate<small>only promotable components returned</small></span></div>
        </div>
      </div>

      <div className="pt-crossline">
        <span>What crosses the boundary:</span>
        <span className="ok">✓ task queries</span><span className="ok">✓ governed components &amp; knowledge</span>
        <span className="no">✗ your proprietary data</span><span className="no">✗ private embeddings</span>
        <span className="pt-spacer" />
        <span>Privacy boundary:</span>
        <div className="pt-seg">
          {[['local', 'Local-only'], ['gapfill', 'Allow gap-fill'], ['hybrid', 'Hybrid']].map(([k, lb]) => (
            <button key={k} className={boundary === k ? 'on' : ''} onClick={() => setBoundary(k)}>{lb}</button>
          ))}
        </div>
      </div>

      <div className="pt-dash-grid">
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 4 }}>OpenHubForAI as an MCP server</div>
          <p style={{ fontSize: 12.5, color: 'var(--fg-muted)', margin: '0 0 12px', lineHeight: 1.5 }}>Point your own agent here to pull governed components &amp; knowledge into local flows.</p>
          <div className="pt-codeblock">{`{
  "mcpServers": {
    `}<span className="tok">"openharnesshub"</span>{`: {
      "url": "https://mcp.openharnesshub.ai/sse",
      "scopes": [`}<span className="tok">"catalog.read"</span>{`, `}<span className="tok">"recommend"</span>{`, `}<span className="tok">"pricing"</span>{`]
    }
  }
}`}</div>
          <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ marginTop: 12 }} onClick={() => toast('MCP config copied')}>⧉ Copy config</button>
        </div>
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 4 }}>Your sources as MCP servers</div>
          <p style={{ fontSize: 12.5, color: 'var(--fg-muted)', margin: '0 0 8px', lineHeight: 1.5 }}>Register local servers OpenHubForAI agents query to ground answers — data stays local.</p>
          <div className="pt-srv"><span className="dot" style={{ background: 'var(--success)' }} /><span className="nm">Filesystem · SOPs<small>mcp://local/files</small></span><span className="pt-priv-badge priv">local-only</span></div>
          <div className="pt-srv"><span className="dot" style={{ background: 'var(--success)' }} /><span className="nm">Private pgvector<small>mcp://local/vector</small></span><span className="pt-priv-badge priv">local-only</span></div>
          <div className="pt-srv"><span className="dot" style={{ background: 'var(--warning)' }} /><span className="nm">Internal ERP API<small>mcp://local/erp · auth required</small></span><span className="oh-badge mono">configure</span></div>
          <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ marginTop: 12 }} onClick={() => toast('Register a local MCP server')}>+ Add server</button>
        </div>
      </div>

      <div className="oh-state-msg" style={{ marginTop: 16, background: 'var(--accent-weak)', border: '1px solid color-mix(in srgb, var(--accent) 30%, var(--line))', borderRadius: 'var(--r-md)', padding: '11px 14px', fontSize: 12.5, lineHeight: 1.5 }}>
        <span className="gl" style={{ color: 'var(--accent)' }}>◑</span>
        <span><b>Hybrid retrieval, one flow.</b> A flow can read your private corpus locally and a governed corpus over MCP in the same step — the trace marks each fact’s source, so provenance stays honest across the boundary.</span>
      </div>
    </div>
  );
}

Object.assign(window, { PRegistry, PConnect });
