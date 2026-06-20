/* global React, StoreCtx, navigate, PRIMS */
// Status/SLA · Activity + notifications · GitHub vectorized source search

/* ============================== STATUS / SLA ============================== */
const SVCS = [
  ['API gateway', 99.99], ['Search & recommend', 99.98], ['Pipeline generation', 99.95],
  ['Run orchestrator', 99.92], ['MCP gateway', 99.97], ['Freshness / CDC', 99.90], ['Foundry', 99.4],
];
function Uptime({ pct }) {
  const bars = Array.from({ length: 40 }, (_, i) => {
    const r = Math.random();
    let cls = '';
    if (pct < 99.5 && i > 30 && i < 34) cls = 'down';
    else if (pct < 99.95 && r > 0.94) cls = 'warn';
    return <i key={i} className={cls} />;
  });
  return <span className="pt-uptime">{bars}</span>;
}
function PStatus() {
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Status</h1><div className="sub">Live service health, 90-day uptime, and SLA commitments.</div></div>
      <div className="pt-status-banner"><span className="d" /><span className="t">All systems operational</span><span className="s">updated 30s ago · subscribe via email / RSS</span></div>
      <div className="pt-panel">
        <div className="oh-cc-id mono" style={{ marginBottom: 12 }}>services · 90-day uptime</div>
        {SVCS.map(([nm, up]) => (
          <div className="pt-svc-row" key={nm}><span className="nm">{nm}</span><Uptime pct={up} /><span className="up">{up}%</span></div>
        ))}
      </div>
      <div className="pt-dash-grid" style={{ marginTop: 16 }}>
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>SLA commitments</div>
          <table className="pt-table">
            <thead><tr><th>Tier</th><th>Uptime</th><th>Support</th><th>Freshness</th></tr></thead>
            <tbody>
              <tr><td>Pro</td><td className="mono">99.5%</td><td>next business day</td><td>weekly</td></tr>
              <tr><td>Team</td><td className="mono">99.9%</td><td>4h</td><td>daily</td></tr>
              <tr><td>Enterprise</td><td className="mono">99.95%</td><td>1h · 24/7</td><td>real-time + credits-back</td></tr>
            </tbody>
          </table>
        </div>
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 8 }}>recent incidents</div>
          <div className="pt-incident"><span className="dt">May 12 · 22m</span><div className="body"><div className="h">Elevated latency · pipeline generation</div><div className="d">Resolved — provider failover; SLA credit applied to affected tenants.</div></div></div>
          <div className="pt-incident"><span className="dt">Apr 28 · 8m</span><div className="body"><div className="h">CDC sync delay · EUR-Lex</div><div className="d">Resolved — facts re-verified &amp; re-signed; affected flows flagged.</div></div></div>
          <div className="pt-incident"><span className="dt">Apr 03</span><div className="body"><div className="h">Scheduled maintenance</div><div className="d">Foundry partition migration · no downtime.</div></div></div>
        </div>
      </div>
    </div>
  );
}

/* ============================== ACTIVITY + NOTIFICATIONS ============================== */
const EVTS = [
  ['ver', 'var(--p-loop)', '↻', <>Version bump · <span className="mono">harness/esg-cite-first</span> <b>1.2.0 → 1.3.0</b></>, '4m ago', <><span className="add">+ citation gate hardened</span> · lift +0.38 → +0.41</>],
  ['cdc', 'var(--verified)', '⟳', <><b>CDC</b> · CSDDD Art. 8 (DE) amended in <span className="mono">csddd-articles</span></>, '1h ago', <>3 facts superseded · re-signed</>],
  ['revoke', 'var(--danger)', '⊘', <><b>Revoked</b> · 2 EPA limits withdrawn from <span className="mono">echa-corpus</span></>, '3h ago', <><span className="rem">− 2 facts</span> · 1 flow flagged for review</>],
  ['decay', 'var(--warning)', '▼', <><b>Decay watch</b> · <span className="mono">harness/esg-cite-first</span> lift eroding</>, 'today', <>−0.04 as base models improve · prune candidate</>],
  ['promo', 'var(--success)', '▲', <><b>New in ESG</b> · <span className="mono">processor/scope3-estimator</span> promoted</>, 'yesterday', <>cleared the gate ▲ +0.36</>],
  ['pin', 'var(--accent)', '📌', <>Pinned update available · <span className="mono">knowledge-corpus/ofac-sdn</span></>, '2d ago', <>diff before accepting · 3 flows pin @1.4.0</>],
];
function Toggle({ on, onClick }) { return <span className={'pt-switch' + (on ? ' on' : '')} onClick={onClick}><i /></span>; }
function PActivity() {
  const { toast } = React.useContext(StoreCtx);
  const [pref, setPref] = React.useState({ ver: true, cdc: true, revoke: true, decay: true, promo: false, pin: true });
  const [cadence, setCadence] = React.useState('daily');
  const t = (k) => setPref((s) => ({ ...s, [k]: !s[k] }));
  const LABEL = { ver: 'Version bumps', cdc: 'CDC / freshness changes', revoke: 'Revocations', decay: 'Decay flips', promo: 'New promotions in my domains', pin: 'Pinned-component updates' };
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Activity</h1><div className="sub">Everything that changed — and the email digests &amp; watches that keep you ahead of it.</div></div>
      <div className="pt-activity">
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 6 }}>recent activity</div>
          {EVTS.map(([k, c, ic, h, t2, diff], i) => (
            <div className="pt-evt" key={i}>
              <span className="ico" style={{ background: `color-mix(in srgb, ${c} 14%, transparent)`, color: c }}>{ic}</span>
              <div className="body"><div className="h">{h}</div><div className="t">{t2}</div><div className="diff">{diff}</div></div>
            </div>
          ))}
        </div>
        <div>
          <div className="pt-panel">
            <div className="oh-cc-id mono" style={{ marginBottom: 6 }}>email &amp; alerts</div>
            <div className="pt-setting-row" style={{ paddingTop: 4 }}><div className="info"><div className="t">Digest cadence</div><div className="d">to nadia@acme.co</div></div>
              <div className="pt-seg">{['realtime', 'daily', 'weekly'].map((m) => <button key={m} className={cadence === m ? 'on' : ''} onClick={() => setCadence(m)}>{m[0].toUpperCase() + m.slice(1)}</button>)}</div></div>
            {Object.keys(LABEL).map((k) => (
              <div className="pt-setting-row" key={k}><div className="info"><div className="t">{LABEL[k]}</div></div><Toggle on={pref[k]} onClick={() => t(k)} /></div>
            ))}
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Webhook endpoint added')}>+ Webhook</button>
              <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => toast('Notification preferences saved')}>Save</button>
            </div>
          </div>
          <div className="pt-panel" style={{ marginTop: 14 }}>
            <div className="oh-cc-id mono" style={{ marginBottom: 8 }}>watching · 3 objects</div>
            {['harness/esg-cite-first', 'knowledge-corpus/csddd-articles', 'flow/csddd-grade'].map((id) => (
              <div className="pt-srv" key={id} style={{ borderColor: 'var(--line)' }}><span className="dot" style={{ background: 'var(--verified)' }} /><span className="nm mono" style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5 }}>{id}</span><span style={{ color: 'var(--fg-faint)', cursor: 'pointer', fontSize: 11 }} onClick={() => toast('Unwatched')}>unwatch</span></div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================== GITHUB VECTORIZED SOURCE SEARCH ============================== */
const GH = [
  { nm: 'Citation-grounded RAG harness', repo: 'github.com/oss-legal/cite-rag', stars: '4.2k', lic: 'Apache-2.0', match: 'enforces a <mark>deterministic citation gate</mark> before the model answers', status: 'promoted', slug: 'esg-cite-first' },
  { nm: 'EU regulation article splitter', repo: 'github.com/euopen/reg-splitter', stars: '1.1k', lic: 'MIT', match: 'splits <mark>CSDDD</mark> & EU regs to article level with source URLs', status: 'promoted' },
  { nm: 'OFAC / sanctions matcher', repo: 'github.com/compliance/sdn-match', stars: '880', lic: 'MIT', match: 'fuzzy <mark>sanctions screening</mark> with explainable matches', status: 'abstract' },
  { nm: 'Scope-3 emissions estimator', repo: 'github.com/climate/scope3', stars: '2.6k', lic: 'GPL-3.0', match: 'computes <mark>Scope 3</mark> with cited emission factors', status: 'abstract' },
];
function PSources() {
  const { toast } = React.useContext(StoreCtx);
  const [q, setQ] = React.useState('grade suppliers against CSDDD with citations');
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Source search · GitHub</h1><div className="sub">Vectorized search across OSS ecosystems — find candidate components, see provenance, and ingest the ones that clear the lift gate.</div></div>
      <div className="pt-results-bar">
        <div className="pt-search"><span>⌕</span><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Describe the capability you need…" /></div>
        <span className="pt-gh-mode">◑ semantic · pgvector</span>
        <span className="pt-muted" style={{ fontSize: 13 }}><b style={{ color: 'var(--fg)' }}>4</b> candidates</span>
      </div>
      {GH.map((g) => (
        <div key={g.repo} className={'pt-gh-row' + (g.status === 'abstract' ? ' abstract' : '')}>
          <div className="pt-gh-top">
            <span className="nm">{g.status === 'abstract' ? '◷ ' : ''}{g.nm}</span>
            <span className="stars">★ {g.stars}</span>
            <span className="lic">{g.lic}</span>
          </div>
          <a className="repo" style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--info)', cursor: 'pointer' }} onClick={() => toast('Opens ' + g.repo)}>↗ {g.repo}</a>
          <div className="match" dangerouslySetInnerHTML={{ __html: 'why-matched · ' + g.match }} />
          <div className="foot">
            {g.status === 'promoted'
              ? <><span className="pt-gh-status promoted">✓ promoted</span><span className="oh-badge oh-badge--lift" style={{ padding: '2px 7px' }}>▲ +0.41</span><button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/c/' + (g.slug || 'esg-cite-first'))}>View component →</button></>
              : <><span className="pt-gh-status abstract">◷ not implemented</span><span style={{ fontSize: 11.5, color: 'var(--fg-muted)' }}>license-filtered · provenance traced to repo</span><button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => toast('Ingest queued → license filter → lift gate → promote')}>Ingest &amp; gate →</button></>}
          </div>
        </div>
      ))}
      <div className="oh-state-msg" style={{ marginTop: 8, background: 'var(--accent-weak)', border: '1px solid color-mix(in srgb, var(--accent) 30%, var(--line))', borderRadius: 'var(--r-md)', padding: '11px 14px', fontSize: 12.5, lineHeight: 1.5 }}>
        <span className="gl" style={{ color: 'var(--accent)' }}>◷</span>
        <span><b>Not-implemented objects link out to GitHub</b> and carry full provenance — but only become tenant-visible components after they’re ingested, license-filtered, and clear the lift gate. Browsing ≠ promoting.</span>
      </div>
    </div>
  );
}

Object.assign(window, { PStatus, PActivity, PSources });
