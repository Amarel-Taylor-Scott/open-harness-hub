/* global React, PRIMS, COMPONENTS, BY_SLUG, navigate, StoreCtx, CompCard, liftBadge, provBadge, EXEC_COLOR, MODALITIES, COST_LABEL */
// Prototype pages: Browse (faceted + zero-result) · Component detail · Dashboard · 404

/* ---------------- BROWSE / SEARCH ---------------- */
const PRIM_ORDER = ['input', 'conditional', 'knowledge', 'action', 'loop', 'stop', 'output'];
function PBrowse({ kind = 'component' }) {
  const [q, setQ] = React.useState('');
  const [prims, setPrims] = React.useState({});
  const [owners, setOwners] = React.useState({});
  const [mod, setMod] = React.useState('text');
  const isP = kind === 'pipeline';
  const anyPrim = Object.values(prims).some(Boolean);
  const anyOwner = Object.values(owners).some(Boolean);
  const kindPool = COMPONENTS.filter((c) => c.kind === kind);
  // pipelines are scoped to the active modality tab; components are modality-agnostic
  const pool = isP ? kindPool.filter((c) => c.modality === mod) : kindPool;
  const results = pool.filter((c) => {
    if (q && !(`${c.name} ${c.slug} ${c.desc} ${c.industry}`.toLowerCase().includes(q.toLowerCase()))) return false;
    if (anyPrim && !prims[c.primitive]) return false;
    if (anyOwner && !owners[c.owner]) return false;
    return true;
  });
  const cnt = (key, val) => pool.filter((c) => c[key] === val).length;
  const modCnt = (m) => kindPool.filter((c) => c.modality === m).length;
  const toggle = (set) => (k) => set((s) => ({ ...s, [k]: !s[k] }));
  const OWN = [['free', 'Free · OpenHubForAI'], ['premium', 'Premium · OpenHubForAI (subscription)'], ['community-free', 'Community · free'], ['community-paid', 'Community · paid']];
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head">
        <h1>{isP ? 'Explore pipelines' : 'Explore components'}</h1>
        <div className="sub">{isP ? 'Prebuilt, governed pipelines — each shows measured lift, governance & cost.' : 'Reusable building blocks. Lift is measured at the pipeline level, not on individual components.'}</div>
      </div>
      {isP && (
        <div className="pt-modtabs">
          {MODALITIES.map(([k, lbl, gl]) => (
            <button key={k} className={'pt-modtab' + (mod === k ? ' on' : '')} onClick={() => setMod(k)}>
              <span className="gl">{gl}</span>{lbl}<span className="n">{modCnt(k)}</span>
            </button>
          ))}
        </div>
      )}
      <div className="pt-results-bar" style={{ marginBottom: 12 }}>
        <div className="pt-search"><span>⌕</span><input placeholder={isP ? 'Search pipelines…' : 'Search components…'} value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <span className="pt-muted" style={{ fontSize: 13 }}><b style={{ color: 'var(--fg)' }}>{results.length}</b> of {pool.length}</span>
      </div>
      <div className="pt-filterbar">
        <span className="pt-filter-label">Source</span>
        {OWN.map(([k, lbl]) => (
          <button key={k} className={'pt-cons-chip' + (owners[k] ? ' on' : '')} onClick={() => toggle(setOwners)(k)}>{lbl} <span style={{ opacity: .55 }}>{cnt('owner', k)}</span></button>
        ))}
        {!isP && <>
          <span className="pt-filter-sep" />
          <span className="pt-filter-label">Primitive</span>
          {PRIM_ORDER.map((k) => { const n = cnt('primitive', k); return n ? (
            <button key={k} className={'pt-cons-chip' + (prims[k] ? ' on' : '')} onClick={() => toggle(setPrims)(k)}>
              <span style={{ display: 'inline-block', width: 9, height: 9, borderRadius: 2, background: `var(${PRIMS[k].v})`, marginRight: 5, verticalAlign: 'middle' }} />{PRIMS[k].label}
            </button>) : null; })}
        </>}
      </div>
      {results.length ? (
        <div className="pt-cards-grid">{results.map((c) => <CompCard key={c.slug} c={c} onClick={() => navigate('/c/' + c.slug)} />)}</div>
      ) : (
        <div className="pt-zero"><div className="ico">⌕</div><h3>Nothing matches “{q}”</h3><p>Turn the gap into demand — request it and we’ll measure whether it beats a bare model.</p><button className="oh-btn oh-btn--primary" onClick={() => navigate('/requests')}>+ Request this capability</button></div>
      )}
    </div>
  );
}

/* ---------------- COMPONENT DETAIL ---------------- */
function PDetail({ slug }) {
  const { toast } = React.useContext(StoreCtx);
  const c = BY_SLUG[slug];
  if (!c) return <PNotFound />;
  const p = PRIMS[c.primitive];
  const blocked = c.prov === 'unsourced';
  return (
    <div className="pt-page pt-view">
      <div className="pt-crumb" style={{ marginBottom: 16 }}>
        <a style={{ cursor: 'pointer' }} onClick={() => navigate(c.kind === 'pipeline' ? '/pipelines' : '/components')}>{c.kind === 'pipeline' ? 'Pipelines' : 'Components'}</a><span className="sep">/</span>
        <span>{c.type}</span><span className="sep">/</span><b>{c.slug}</b>
      </div>
      <div style={{ borderTop: `3px solid var(${p.v})`, borderRadius: 3, marginBottom: 16 }} />
      <div className="pt-row" style={{ alignItems: 'flex-start', flexWrap: 'wrap', gap: 14, marginBottom: 18 }}>
        <div style={{ flex: 1, minWidth: 280 }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: `var(${p.v})`, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="oh-execdot" style={{ background: EXEC_COLOR[c.exec] }} />{p.glyph} {p.label} · {c.type}
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, margin: '6px 0 4px', color: 'var(--fg)' }}>{c.name}</h1>
          <div className="oh-cc-id mono">{c.type}/{c.slug} <span className="copy">⧉</span></div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {c.kind === 'pipeline' && liftBadge(c)}{provBadge(c.prov)}
          <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => { toast('Added to flow · ' + c.name); }}>+ Add to flow</button>
        </div>
      </div>
      <p style={{ fontSize: 15, lineHeight: 1.55, color: 'var(--fg-muted)', maxWidth: 680, marginTop: 0 }}>{c.desc}</p>

      <div className="pt-grid-3" style={{ marginTop: 18 }}>
        <div className="pt-panel">
          {c.kind === 'pipeline' ? <>
            <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>capability lift</div>
            <div className="oh-lb-row"><div className="oh-lb-label">bare model <b>0.42</b></div><div className="oh-lb-track"><div className="oh-lb-fill bare" style={{ width: '42%' }} /></div></div>
            <div className="oh-lb-row"><div className="oh-lb-label">this pipeline <b>{(0.42 + (c.lift || 0.4)).toFixed(2)}</b></div><div className="oh-lb-track"><div className="oh-lb-fill pipe" style={{ width: `${(0.42 + (c.lift || 0.4)) * 100}%` }} /></div></div>
            <div className="oh-lift-delta"><span className="big" style={{ fontSize: 24 }}>▲ +{(c.lift || 0.4).toFixed(2)}</span></div>
          </> : <>
            <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>where it fits</div>
            <p className="pt-muted" style={{ fontSize: 13, lineHeight: 1.55 }}>A reusable building block used inside pipelines. <b style={{ color: 'var(--fg)' }}>Lift is measured on the pipeline</b> that uses it — you can’t measure the lift of a component on its own.</p>
          </>}
        </div>
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>provenance</div>
          {blocked ? <div className="oh-state-msg blocked"><span className="gl">⚠</span><span><b>Unsourced.</b> Missing source URL + license — routed to review before it can be cited.</span></div>
            : <div style={{ fontSize: 13, color: 'var(--fg-muted)', lineHeight: 1.7 }}>
              <div>source · <span className="mono" style={{ color: 'var(--fg)' }}>{c.industry === 'ESG' ? 'eur-lex.europa.eu' : 'registry-verified'}</span></div>
              <div>license · <span className="mono" style={{ color: 'var(--fg)' }}>{c.license}</span></div>
              <div>last-verified · <span className="mono" style={{ color: 'var(--fg)' }}>2026-05-21</span></div>
            </div>}
        </div>
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>cost &amp; portability</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
            <div className="oh-statline"><span style={{ color: 'var(--fg-muted)', fontSize: 13 }}>cost band</span><span className="oh-badge mono">{COST_LABEL[c.cost] || c.cost}</span></div>
            <div className="oh-statline"><span style={{ color: 'var(--fg-muted)', fontSize: 13 }}>recurring</span>
              <span className={'oh-badge ' + (c.recurring ? '' : 'oh-badge--verified')}>{c.recurring ? '↻ per model call' : '⌂ freezable · $0'}</span></div>
            <div className="oh-statline"><span style={{ color: 'var(--fg-muted)', fontSize: 13 }}>lifecycle</span><span className="oh-badge oh-badge--stable">◆ {c.lifecycle}</span></div>
          </div>
        </div>
      </div>
      <CompConfig c={c} />
      {blocked && <div className="oh-state-msg blocked" style={{ marginTop: 16 }}><span className="gl">⚠</span><span><b>Blocked by the promotion gate.</b> This component can’t enter a tenant-visible flow until provenance is resolved. <a style={{ color: 'var(--accent)', cursor: 'pointer', fontWeight: 600 }} onClick={() => navigate('/nope')}>Fix: add provenance → request review →</a></span></div>}
    </div>
  );
}

/* ---------------- WORKSPACE DASHBOARD ---------------- */
function PDashboard() {
  const { task, setTask, toast } = React.useContext(StoreCtx);
  const flows = [
    ['CSDDD supplier grading', 'flow/csddd-grade', '▲ +0.41', '6 comp · $$'],
    ['Contract renewal-risk review', 'flow/renewal-risk', '▲ +0.33', '5 comp · $$'],
  ];
  const runs = [['flow/csddd-grade', '$0.0312 · 13.9s', '✓'], ['flow/renewal-risk', '$0.018 · 8.2s', '✓'], ['flow/aml-screen', 'blocked-by-gate', '⚠']];
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Workspace</h1><div className="sub">Resume a flow, review runs, or paste a new task.</div></div>
      <div className="pt-dash-entry" style={{ marginBottom: 20 }}>
        <textarea placeholder="Paste a task to build a new flow…" value={task} onChange={(e) => setTask(e.target.value)} />
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
          <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => { if (task.trim().length > 11) navigate('/build'); else toast('Describe the task a bit more'); }}>Build →</button>
        </div>
      </div>
      <div className="pt-dash-grid">
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 6 }}>recent flows</div>
          {flows.map(([n, id, lift, meta]) => (
            <div key={id} className="pt-list-row" onClick={() => navigate('/flow')}>
              <div style={{ flex: 1 }}><div className="ttl">{n}</div><div className="meta">{id}</div></div>
              <span className="oh-badge oh-badge--lift">{lift}</span><span className="meta">{meta}</span>
            </div>
          ))}
        </div>
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 6 }}>recent runs</div>
          {runs.map(([id, meta, st], i) => (
            <div key={i} className="pt-list-row" onClick={() => navigate('/run')}>
              <div style={{ flex: 1 }}><div className="ttl">{id}</div><div className="meta">{meta}</div></div>
              <span className={st === '✓' ? 'oh-badge oh-badge--lift' : 'oh-badge oh-badge--warn'}>{st}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="pt-panel" style={{ marginTop: 16 }}>
        <div className="oh-cc-id mono" style={{ marginBottom: 8 }}>suggested gaps in ESG · CSDDD</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {['Scope-3 emissions estimator', 'Conflict-minerals tracer', 'Living-wage calculator'].map((g) => (
            <button key={g} className="pt-cons-chip" onClick={() => navigate('/nope')}>◷ {g}</button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------------- 404 ---------------- */
function PNotFound() {
  const { setTask } = React.useContext(StoreCtx) || {};
  return (
    <div className="pt-404 oh-view">
      <div className="big">404</div>
      <p className="pt-muted" style={{ maxWidth: 360 }}>That page isn’t built in this prototype yet. Head back to the entry box or browse the catalog.</p>
      <div style={{ display: 'flex', gap: 10 }}>
        <button className="oh-btn oh-btn--primary" onClick={() => navigate('/')}>← Entry box</button>
        <button className="oh-btn oh-btn--ghost" onClick={() => navigate('/components')}>Browse catalog</button>
      </div>
    </div>
  );
}

Object.assign(window, { PBrowse, PDetail, PDashboard, PNotFound, PPricing });

/* ---------------- PRICING (open spec · governed content) ---------------- */
function PPricing() {
  const { toast } = React.useContext(StoreCtx);
  const O = ({ children, paid }) => <li className={paid ? 'paid-feat' : 'open-feat'}><span className="ck">{paid ? '◆' : '✔'}</span>{children}</li>;
  const X = ({ children }) => <li className="off"><span className="ck">·</span>{children}</li>;
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Pricing</h1><div className="sub">The spec is open and free forever. The governed components and live knowledge are the subscription.</div></div>
      <div className="pt-openline">
        <span className="gl">🛡</span>
        <span><b>Open spec, governed content.</b> The schemas, the seven-primitive grammar, the SDK, the CLI, the export emitters — open under Apache-2.0. The <b>vetted components</b>, <b>live knowledge corpora</b>, and <b>build-on-demand</b> are what you pay for. Export anything you build; never get locked in.</span>
      </div>
      <div className="pt-tiers">
        <div className="pt-tier open">
          <span className="tag">Open · free forever</span>
          <h3>Free / OSS</h3>
          <div className="price"><b>$0</b></div>
          <button className="oh-btn oh-btn--ghost oh-btn--sm cta" onClick={() => navigate('/nope')}>Get the spec →</button>
          <ul>
            <O>Spec, schemas &amp; seven-primitive grammar</O>
            <O>CLI (<span className="mono">oh-hub</span>) + reference SDK</O>
            <O>All export emitters (SPDX, C2PA, JSON-LD…)</O>
            <O>Build &amp; export flows · self-host</O>
            <O>Simulate runs (bring your own key)</O>
            <X>Vetted components &amp; knowledge</X>
            <X>Live freshness / governance</X>
          </ul>
        </div>
        <div className="pt-tier feat">
          <span className="tag">★ Most popular</span>
          <h3>Pro</h3>
          <div className="price"><b>$39</b> / seat / mo <span style={{ opacity: .6 }}>· indicative</span></div>
          <button className="oh-btn oh-btn--primary oh-btn--sm cta" onClick={() => toast('Pro — coming soon')}>Start free trial</button>
          <ul>
            <O>Everything in Free</O>
            <O paid>Vetted components &amp; knowledge packs</O>
            <O paid>Measured lift &amp; provenance on every component</O>
            <O paid>Hosted runs · live pricing</O>
            <O paid>Capability-requests (build-on-demand)</O>
            <X>Team governance &amp; review queue</X>
          </ul>
        </div>
        <div className="pt-tier">
          <span className="tag">Teams</span>
          <h3>Team</h3>
          <div className="price"><b>$299</b> / mo <span style={{ opacity: .6 }}>· indicative</span></div>
          <button className="oh-btn oh-btn--ghost oh-btn--sm cta" onClick={() => toast('Team — coming soon')}>Contact sales</button>
          <ul>
            <O paid>Everything in Pro</O>
            <O paid>Shared registry &amp; pinning</O>
            <O paid>Review queue &amp; promotion gates</O>
            <O paid>Live knowledge corpora (CDC freshness)</O>
            <O paid>Usage analytics &amp; credits</O>
          </ul>
        </div>
        <div className="pt-tier">
          <span className="tag">Regulated</span>
          <h3>Enterprise</h3>
          <div className="price"><b>Custom</b></div>
          <button className="oh-btn oh-btn--ghost oh-btn--sm cta" onClick={() => toast('Enterprise — let’s talk')}>Talk to us</button>
          <ul>
            <O paid>Everything in Team</O>
            <O paid>Air-gapped / BYO-cloud deploy</O>
            <O paid>SSO, audit export, compliance pack</O>
            <O paid>Verified-publisher provenance</O>
            <O paid>Private foundry &amp; managed ingestion</O>
          </ul>
        </div>
      </div>
      <div className="pt-pricing-note">Prices indicative until validated. Export is always free — the freezable layer (static / text-op components) leaves with you; the live &amp; governed layer is the subscription.</div>
    </div>
  );
}
