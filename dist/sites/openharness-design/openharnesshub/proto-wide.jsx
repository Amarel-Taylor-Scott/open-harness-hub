/* global React, StoreCtx, navigate, PRIMS, COMPONENTS, Mark */
// Wide spec: requests(+detail) · contribute · knowledge-entry
//           · provenance · trust · audit log · roles · signin · onboarding · upgrade

/* ===== CAPABILITY-REQUEST BOARD ===== */
const REQS = [
  ['req-204', 'Conflict-minerals (3TG) tracer', 'knowledge-corpus', 312, 'researching'],
  ['req-198', 'Living-wage benchmark calculator', 'processor', 271, 'building'],
  ['req-187', 'EUDR geolocation deforestation check', 'harness', 244, 'triaged'],
  ['req-176', 'Water-stress index by basin', 'knowledge-corpus', 156, 'requested'],
];
const REQ_STAGES = ['requested', 'triaged', 'researching', 'building', 'built', 'promoted'];
function StatusPipe({ status }) {
  const idx = REQ_STAGES.indexOf(status);
  return (
    <div className="pt-statuspipe">
      {REQ_STAGES.map((s, i) => (
        <React.Fragment key={s}>
          {i > 0 && <span className="sep" />}
          <span className={'st' + (i < idx ? ' done' : i === idx ? ' on' : '')}>{i <= idx ? '●' : '○'} {s}</span>
        </React.Fragment>
      ))}
    </div>
  );
}
function PRequests() {
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Capability requests</h1><div className="sub">Demand for what the catalog lacks — vote it up; we research, build, and gate it. Build-on-demand turns gaps into governed components.</div></div>
      <div className="pt-toolbar"><span style={{ fontSize: 13, color: 'var(--fg-muted)' }}>Sorted by demand</span><span className="pt-spacer" /><button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => navigate('/requests/new')}>+ Request a capability</button></div>
      <div className="pt-panel">
        {REQS.map(([id, nm, type, votes, status]) => (
          <div className="pt-reqrow" key={id}>
            <div className="pt-vote" onClick={() => {}}><span className="up">▲</span><span className="n">{votes}</span></div>
            <div className="body" style={{ cursor: 'pointer' }} onClick={() => navigate('/requests/' + id)}>
              <div className="nm">◷ {nm}</div>
              <div className="meta"><span className="mono" style={{ fontFamily: 'var(--font-mono)' }}>target · {type}</span><span className="pt-status-chip">{status}</span></div>
              <StatusPipe status={status} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
function PRequestDetail({ id }) {
  const { toast } = React.useContext(StoreCtx);
  return (
    <div className="pt-page pt-view">
      <div className="pt-crumb" style={{ marginBottom: 14 }}><a style={{ cursor: 'pointer' }} onClick={() => navigate('/requests')}>Requests</a><span className="sep">/</span><b>{id}</b></div>
      <div className="pt-page-head"><h1>◷ Conflict-minerals (3TG) tracer</h1><div className="sub">312 tenants want this · target type: knowledge-corpus · status: researching</div></div>
      <div className="pt-intent">
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 12 }}>promotion path</div>
          <StatusPipe status="researching" />
          <div style={{ fontSize: 12.5, color: 'var(--fg-muted)', marginTop: 14, lineHeight: 1.5 }}>Candidate sources found: <b style={{ color: 'var(--fg)' }}>OECD due-diligence guidance, USGS minerals, EITI</b>. Must clear the two-axis gate: <b style={{ color: 'var(--fg)' }}>structural lift</b> + <b style={{ color: 'var(--fg)' }}>verifiable provenance</b> before promotion to <span className="mono">experimental</span>.</div>
        </div>
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>two ways to fulfill</div>
          <div className="pt-setting-row"><div className="info"><div className="t">Premium agent build</div><div className="d">Hosted, paid — fastest. We build &amp; gate it.</div></div><button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => toast('Build-on-demand queued')}>Fund build</button></div>
          <div className="pt-setting-row"><div className="info"><div className="t">Community build</div><div className="d">Contribute it; earn credits when it passes the gate.</div></div><button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/contribute')}>Contribute</button></div>
        </div>
      </div>
    </div>
  );
}
function PContribute() {
  const { toast } = React.useContext(StoreCtx);
  return (
    <div className="pt-page pt-view">
      <div className="pt-page-head"><h1>Contribute &amp; earn credits</h1><div className="sub">Fulfill a capability-request; earn credits when your shared component passes the lift gate.</div></div>
      <div className="pt-steps">{['Pick a request', 'Build component', 'Submit', 'Gate measures lift', 'Earn credits'].map((s, i, a) => (<React.Fragment key={s}><span className={'pt-step' + (i < 2 ? ' on' : '')}><span className="n">{i + 1}</span>{s}</span>{i < a.length - 1 && <span className="arr">→</span>}</React.Fragment>))}</div>
      <div className="pt-dash-grid">
        <div className="pt-panel"><div className="oh-cc-id mono" style={{ marginBottom: 8 }}>credit mechanics</div><div style={{ fontSize: 13, color: 'var(--fg-muted)', lineHeight: 1.6 }}>Credit is granted <b style={{ color: 'var(--fg)' }}>only</b> when the shared component beats a bare model and is promoted. No lift, no credit — the same gate everything else passes. Credits offset usage &amp; build-on-demand.</div></div>
        <div className="pt-panel"><div className="oh-cc-id mono" style={{ marginBottom: 8 }}>your contributions</div>
          <div className="pt-list-row"><div style={{ flex: 1 }}><div className="ttl">processor/entity-resolver</div><div className="meta">promoted · ▲ +0.14</div></div><span className="oh-badge oh-badge--lift">+1,250 cr</span></div>
          <div className="pt-list-row"><div style={{ flex: 1 }}><div className="ttl">rule-pack/aml-screen</div><div className="meta">verifying</div></div><span className="oh-badge oh-badge--warn">pending</span></div>
        </div>
      </div>
    </div>
  );
}

/* ===== KNOWLEDGE ENTRY (the "millions of facts" leaf) ===== */
function PKnowledgeEntry({ id }) {
  const { toast } = React.useContext(StoreCtx);
  return (
    <div className="pt-page pt-view">
      <div className="pt-crumb" style={{ marginBottom: 14 }}><a style={{ cursor: 'pointer' }} onClick={() => navigate('/c/csddd-articles')}>csddd-articles</a><span className="sep">/</span><b>entry · art-8-3</b></div>
      <div className="pt-row" style={{ gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div className="pt-kentry" style={{ flex: '2 1 420px' }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--p-knowledge)' }}>⛁ Knowledge entry</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, margin: '6px 0', color: 'var(--fg)' }}>CSDDD Art. 8(3) — due-diligence on actual adverse impacts</h1>
          <div className="content">“Member States shall ensure that companies take appropriate measures to bring actual adverse impacts to an end…” <span style={{ color: 'var(--fg-faint)' }}>(excerpt · 13 languages available)</span></div>
          <div className="oh-cc-badges"><span className="oh-badge oh-badge--verified">✔ sourced</span><span className="oh-badge oh-badge--lift">⟳ fresh</span><span className="oh-badge mono">rag · exact-id</span></div>
        </div>
        <div style={{ flex: '1 1 240px' }}>
          <div className="pt-panel">
            <div className="oh-cc-id mono" style={{ marginBottom: 8 }}>provenance · this entry</div>
            <div className="pt-kv"><span className="k">source</span><span className="v">eur-lex.europa.eu</span></div>
            <div className="pt-kv"><span className="k">captured</span><span className="v">2026-05-28</span></div>
            <div className="pt-kv"><span className="k">last-verified</span><span className="v">2026-05-28</span></div>
            <div className="pt-kv"><span className="k">license</span><span className="v">CC-BY-4.0</span></div>
            <div className="pt-kv"><span className="k">used in</span><span className="v">214 answers</span></div>
            <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ width: '100%', justifyContent: 'center', marginTop: 12 }} onClick={() => navigate('/p/k-art-8-3')}>View provenance graph →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ===== PROVENANCE GRAPH ===== */
function PProvenance({ id }) {
  const trail = [
    ['var(--p-knowledge)', '⛁', 'Primary source', 'EUR-Lex · CSDDD consolidated text', '2026-05-28 · captured by esg-scout-01'],
    ['var(--verified)', '✔', 'Verified & signed', 'license CC-BY-4.0 confirmed · C2PA signature 0x9c1b…a31f', '2026-05-28 11:40'],
    ['var(--p-conditional)', '◈', 'Transformed', 'split to article level · 13 languages · dedup', '2026-05-28'],
    ['var(--p-action)', '⚡', 'Cited by', 'harness/esg-cite-first · 11 flows reference this entry', 'live'],
    ['var(--p-output)', '⎘', 'Attested in', 'flow/csddd-grade · cert valid through 2026-08-26', 'live'],
  ];
  return (
    <div className="pt-page pt-view">
      <div className="pt-page-head"><h1>Provenance graph</h1><div className="sub">Every object traces source → signature → transforms → citations → attestation, with revocation lineage.</div></div>
      <div className="pt-panel" style={{ maxWidth: 640 }}>
        <div className="pt-trail">
          {trail.map(([c, ic, h, d, dt]) => (
            <div className="pt-trail-step" key={h}><span className="dot" style={{ background: c }}>{ic}</span><div className="c"><div className="h">{h}</div><div className="d">{d}</div><div className="dt">{dt}</div></div></div>
          ))}
        </div>
        <div className="oh-state-msg blocked" style={{ marginTop: 6, background: 'color-mix(in srgb, var(--verified) 7%, transparent)', borderColor: 'color-mix(in srgb, var(--verified) 30%, var(--line))' }}><span className="gl" style={{ color: 'var(--verified)' }}>🛡</span><span>If the source revokes or amends this fact, the change propagates down the chain — citing flows are flagged and attestations invalidated automatically.</span></div>
      </div>
    </div>
  );
}

/* ===== TRUST CENTER ===== */
function PTrustCenter() {
  const cards = [['🛡', 'Signed provenance', 'Every fact carries a C2PA signature traceable to a primary source and capture date.'], ['🏅', 'Verified publishers', '46 signed publishers — agencies, standards bodies, domain experts.'], ['🔏', 'Canary & watermark', 'Honeytoken facts detect redistribution; licenses enforce no-resale.'], ['⚖', 'Compliance', 'SOC 2 Type II · GDPR · EU-AI-Act conformity records.'], ['🔒', 'Data handling', 'No real PII; synthetic/public only; tenant isolation; BYO-key.'], ['⟳', 'Revocation', 'Withdrawn facts are pulled from flows and attestations within SLA.']];
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Trust center</h1><div className="sub">The moat, on one page — how provenance, verification, and compliance actually work.</div></div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '13px 16px', marginBottom: 16, border: '1px solid var(--line)', borderLeft: '3px solid var(--accent)', borderRadius: 'var(--r-md)', background: 'var(--accent-weak)' }}>
        <span style={{ fontSize: 18 }}>◳</span>
        <div style={{ flex: 1, fontSize: 13, lineHeight: 1.45, color: 'var(--fg)' }}>Verified, signed, always-current context is powered by <b>Baltor</b> — our context-assurance product. This page shows how it shows up inside Open Harness Hub.</div>
        <a className="oh-btn oh-btn--ghost oh-btn--sm" href="../context-enrichment/Context Enrichment Prototype.html">Open Baltor →</a>
      </div>
      <div className="pt-trust-grid">{cards.map(([ic, t, d]) => (<div className="pt-trust-card" key={t}><div className="ic">{ic}</div><div className="t">{t}</div><div className="d">{d}</div></div>))}</div>
    </div>
  );
}

/* ===== AUDIT LOG ===== */
// PAuditLog — now via the SHARED KIT (OhAuditLog), fed OHH's governance receipts.
function PAuditLog() {
  const { OhAuditLog } = window;
  return <OhAuditLog rows={[
    { t: '2026-05-28 12:04', ev: 'Flow deployed', icon: '▲', actor: 'nadia@acme.co', target: 'flow/csddd-grade', policy: 'flow.deploy', ok: true },
    { t: '2026-05-28 11:40', ev: 'CDC amendment applied', icon: '⟳', actor: 'system', target: 'csddd-articles · art-8', policy: 'cdc.amend', ok: true },
    { t: '2026-05-28 09:15', ev: 'Component pinned', icon: '⛁', actor: 'jonas@acme.co', target: 'ofac-sdn@1.4.0', policy: 'component.pin', ok: true },
    { t: '2026-05-27 16:22', ev: 'Gate blocked', icon: '⚠', actor: 'system', target: 'gxp-sops · unsourced', policy: 'gate.block', ok: false },
    { t: '2026-05-27 14:01', ev: 'API key rotated', icon: '⚿', actor: 'priya@acme.co', target: 'oh_live_••••a31f', policy: 'key.rotate', ok: true },
  ]} />;
}

/* ===== RBAC ROLES ===== */
function PRoles() {
  const { toast } = React.useContext(StoreCtx);
  const caps = ['Browse catalog', 'Build & run flows', 'Deploy', 'Manage private registry', 'Connect MCP / keys', 'Review & promote', 'Manage billing', 'Admin & roles'];
  const roles = { Owner: 8, Admin: 7, Builder: 5, Reviewer: 4, Viewer: 1 };
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Roles &amp; permissions</h1><div className="sub">RBAC — define who can do what. Custom roles supported on Enterprise.</div></div>
      <div className="pt-panel"><table className="pt-table"><thead><tr><th>Capability</th>{Object.keys(roles).map((r) => <th key={r} style={{ textAlign: 'center' }}>{r}</th>)}</tr></thead>
        <tbody>{caps.map((c, ci) => (<tr key={c}><td>{c}</td>{Object.values(roles).map((lvl, i) => <td key={i} style={{ textAlign: 'center', color: ci < lvl ? 'var(--success)' : 'var(--fg-faint)' }}>{ci < lvl ? '✓' : '·'}</td>)}</tr>))}</tbody></table>
        <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ marginTop: 14 }} onClick={() => toast('New custom role')}>+ Custom role</button>
      </div>
    </div>
  );
}

/* ===== AUTH · ONBOARDING · UPGRADE (minimal shell) ===== */
// PSignin — now via the SHARED KIT (OhAuth). signin/signup share this route.
function PSignin() {
  const { OhAuth } = window;
  const mode = (window.location.hash || '').includes('signup') ? 'signup' : 'signin';
  return <OhAuth brand={{ name: 'OpenHubForAI', realm: 'openharnesshub', tld: '.io', glyph: '⎔', accent: 'var(--accent)' }} mode={mode} />;
}
function POnboarding() {
  const { task, setTask, setLoggedIn } = React.useContext(StoreCtx);
  return (
    <div className="pt-min pt-view">
      <div className="pt-onb-wrap">
        <div className="pt-steps" style={{ justifyContent: 'center' }}>{['Paste a task', 'Connect a model', 'Pick a domain', 'First flow'].map((s, i, a) => (<React.Fragment key={s}><span className={'pt-step' + (i === 0 ? ' on' : '')}><span className="n">{i + 1}</span>{s}</span>{i < a.length - 1 && <span className="arr">→</span>}</React.Fragment>))}</div>
        <div className="pt-onb-card">
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 21, fontWeight: 700, margin: '0 0 4px', color: 'var(--fg)' }}>What's the first task?</h1>
          <div style={{ fontSize: 13, color: 'var(--fg-muted)', marginBottom: 14 }}>We'll build a costed, cited flow from it — using simulate mode until you connect a key.</div>
          <textarea className="pt-dash-entry" style={{ width: '100%', minHeight: 56, border: '1px solid var(--line)', borderRadius: 'var(--r-md)', background: 'var(--panel-2)', color: 'var(--fg)', font: 'inherit', resize: 'none', outline: 'none', padding: 11 }} placeholder="Grade a supplier list against CSDDD…" value={task} onChange={(e) => setTask(e.target.value)} />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button className="oh-btn oh-btn--ghost" onClick={() => { setLoggedIn(true); navigate('/app'); }}>Skip</button>
            <span className="pt-spacer" />
            <button className="oh-btn oh-btn--primary" onClick={() => { setLoggedIn(true); navigate('/build'); }}>Build my first flow →</button>
          </div>
        </div>
      </div>
    </div>
  );
}
function PUpgrade() {
  return (
    <div className="pt-min pt-view">
      <div className="pt-paywall">
        <div className="lock">🔒</div>
        <h1>You've hit the Pro limit</h1>
        <div className="pt-meter"><i style={{ width: '100%' }} /></div>
        <p>5,000 / 5,000 pipeline-generation calls used this period. Upgrade to Team for higher limits, governance, and daily freshness — or wait for the reset.</p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
          <button className="oh-btn oh-btn--primary" onClick={() => navigate('/checkout')}>Upgrade to Team →</button>
          <button className="oh-btn oh-btn--ghost" onClick={() => navigate('/pricing')}>Compare plans</button>
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--fg-faint)', marginTop: 14 }}>The open spec, SDK &amp; export are never rate-limited — only governed calls.</div>
      </div>
    </div>
  );
}

Object.assign(window, { PRequests, PRequestDetail, PContribute, PKnowledgeEntry, PProvenance, PTrustCenter, PAuditLog, PRoles, PSignin, POnboarding, PUpgrade });
