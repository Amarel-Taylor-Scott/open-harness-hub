/* global React, PRIMS, PFLOW, PFW, PFH, ALTS, BY_SLUG, navigate, StoreCtx, liftBadge, provBadge, EXEC_COLOR, MODALITIES */
// Prototype pages: Landing · Build (parse) · Results · Flow (+inspector) · Run (+trace)

// landing example tasks, by input modality (mirror the Explore › Pipelines modality tabs)
const EX_BY_MOD = {
  text: [
    'Detect human-exploitation indicators in a Hong Kong → Philippines recruitment ad',
    'Trace EUDR deforestation risk for a coffee shipment by plot geolocation',
    'Screen a recruitment agency against modern-slavery indicators across 13 languages',
    'Flag CSDDD tier-2 supplier risk and cite the exact articles',
  ],
  image: [
    'Extract line items from a scanned invoice and reconcile the total',
    'Verify a passport photo for tampering and MRZ consistency',
    'Read the series off this revenue chart into a clean CSV',
    'Triage product-line photos for surface defects against a rubric',
  ],
  audio: [
    'Grade a support call against the QA rubric with timestamped citations',
    'Turn this meeting recording into decisions and owners',
    'Structure a dictated patient encounter into a SOAP note',
    'Redact PII from a call recording and log every cut',
  ],
  video: [
    'Index a deposition video into a searchable, cited transcript',
    'Screen CCTV clips for safety incidents and route to EHS',
    'Check a video ad against advertising-standards rules',
    'Auto-chapter a lecture with a cited transcript and glossary',
  ],
};
const PLACEHOLDER_BY_MOD = {
  text: 'Detect human-exploitation indicators in a recruitment ad posted from Hong Kong to the Philippines…',
  image: 'Extract line items from a scanned invoice and reconcile the total against the printed sum…',
  audio: 'Grade a 12-minute support call against our QA rubric, with a timestamp behind each deduction…',
  video: 'Index this deposition video into a searchable transcript with exhibit links and citations…',
};

/* ---------------- LANDING ---------------- */
function PLanding() {
  const { task, setTask, loggedIn } = React.useContext(StoreCtx);
  const { OhTopBar, OhFooter } = window;
  const brand = { name: 'OpenHubForAI', realm: 'openharnesshub', tld: '.io', glyph: '⎔', accent: 'var(--accent)' };
  const [hint, setHint] = React.useState('');
  const [exMod, setExMod] = React.useState('text');
  const [heroV, hero] = window.useExperiment('ohh_hero', ['A', 'B']);
  const OHH_SUBHEADS = {
    A: 'Describe a task and OpenHubForAI assembles a governed harness — vetted components and knowledge packs that measurably lift what your agent can do. Most of it deterministic and freezable, so you add capability without adding cost.',
    B: 'Vetted components and knowledge packs, composed into a governed harness — mostly deterministic and freezable, so you add capability without adding model cost.',
    C: 'Stop wiring brittle pipelines. Describe the task; we assemble a cited, governed harness your agent can run — and an auditor can trace.',
  };
  const [subV] = window.useExperiment('ohh_subhead', ['A', 'B', 'C']);
  const submit = (t) => {
    const v = (t ?? task).trim();
    if (v.length < 12) { setHint('Describe the task in a little more detail to build a flow.'); return; }
    hero.track('build_submit', { where: 'hero', len: v.length });
    setTask(v); navigate(loggedIn ? '/build' : '/preview');
  };
  return (
    <div className="pt-mkt pt-view">
      <OhTopBar brand={brand}
        nav={[['Explore', '/pipelines'], ['SDG solutions', '/solutions'], ['Cases', '/cases'], ['Workspace', '/app'], ['Pricing', '/pricing']]}
        cta={{ label: 'Start free', href: '/signup' }} signInHref="/signin" />
      <div className="pt-mkt-body">
        <section className="pt-hero">
          <div className="pt-hero-eyebrow">The harness layer for production agents</div>
          {heroV === 'B'
            ? <h1>Governed harnesses for agents<br />you can trust — on the record.</h1>
            : <h1>Power your agents with<br />governed harnesses.</h1>}
          <p className="sub">{OHH_SUBHEADS[subV] || OHH_SUBHEADS.A}</p>
          <div className="pt-entry">
            <textarea autoFocus placeholder={PLACEHOLDER_BY_MOD[exMod]}
              value={task} onChange={(e) => { setTask(e.target.value); if (hint) setHint(''); }}
              onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit(); }} />
            <div className="pt-entry-row">
              <div className="pt-constraints" />
              <button className="oh-btn oh-btn--primary" onClick={() => submit()}>Build <span style={{ fontSize: 12, opacity: .7 }}>⌘↵</span></button>
            </div>
          </div>
          <div className="pt-hint">{hint}</div>
          <div className="pt-modtabs pt-modtabs--center">
            {MODALITIES.map(([k, lbl, gl]) => (
              <button key={k} className={'pt-modtab' + (exMod === k ? ' on' : '')} onClick={() => setExMod(k)}>
                <span className="gl">{gl}</span>{lbl}
              </button>
            ))}
          </div>
          <div className="pt-chips">
            {EX_BY_MOD[exMod].map((c) => (
              <button className="pt-chip" key={c} onClick={() => { setTask(c); submit(c); }}>
                <span className="tri">▸</span>{c.length > 42 ? c.slice(0, 40) + '…' : c}
              </button>
            ))}
          </div>
          <div className="pt-quiet">
            <a onClick={() => navigate('/improve')}>…or improve a pipeline you already have</a><span className="dot">·</span>
            <a onClick={() => navigate('/pipelines')}>Browse the catalog</a><span className="dot">·</span>
            <a onClick={() => navigate('/app')}>Sign in</a>
          </div>
        </section>
        <section className="pt-mkt-sec ohh-standards-sec" style={{ maxWidth: 'var(--maxw-site, 1100px)', margin: '0 auto', padding: '8px 28px 12px', boxSizing: 'border-box' }}>
          <div className="pt-sec-eyebrow" style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--accent)' }}>Open standards</div>
          <h2 style={{ fontSize: 'var(--fs-h2, 30px)', fontWeight: 800, letterSpacing: '-.02em', margin: '10px 0 0' }}>Built on the open supply-chain stack.</h2>
          <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--fg-muted)', margin: '10px 0 0', maxWidth: '74ch' }}>OpenHubForAI doesn’t reinvent trust — it applies the same Linux Foundation / OpenSSF / OWASP standards that secure software supply chains to harnesses and eval packs. Provenance, signing, risk and a bill-of-materials are open and verifiable.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 20 }} className="ohh-std-grid">
            {[
              ['Sigstore', 'keyless signing + transparency log — every harness’s signed receipt'],
              ['SLSA + in-toto', 'verifiable provenance attestations for how a harness was produced'],
              ['lm-evaluation-harness', 'EleutherAI’s standard runner behind reproducible eval packs'],
              ['CycloneDX AI-BOM', 'a bill of materials for each AI artifact (OWASP)'],
              ['OpenSSF Scorecard', 'automated risk scoring — discovery is not trust'],
              ['SemVer', 'semantic versioning, pinned with a changelog'],
            ].map(([n, d]) => (
              <div className="oh-card" key={n} style={{ padding: '15px 17px', borderLeft: '3px solid var(--accent)' }}>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--accent)' }}>{n}</div>
                <div style={{ fontSize: 12.5, lineHeight: 1.5, color: 'var(--fg-muted)', marginTop: 7 }}>{d}</div>
              </div>
            ))}
          </div>
        </section>
        <OhFooter brand={brand} tagline="Open harness ecosystem · part of AI Done Right" cols={[
          ['Product', [['Explore', '/pipelines'], ['Build', '/build'], ['Pricing', '/pricing']]],
          ['Govern', [['Trust center', '/trust'], ['Freshness', '/freshness'], ['Audit', '/audit-log']]],
          ['Group', [['AI Done Right ↗', '../context-is-everything/Context is Everything.html'], ['Baltor.ai ↗', '../context-enrichment/Context Enrichment Prototype.html'], ['Teleon.dev ↗', '../teleon/Teleon Prototype.html']]],
        ]} />
      </div>
      <window.OhExperimentsPanel />
    </div>
  );
}
function Mark() {
  return (
    <span className="oh-mark" aria-hidden="true">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />
        <path d="M9 9h3.5" stroke="currentColor" strokeWidth="1.4" />
        <rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" strokeWidth="1.4" transform="rotate(45 14 6)" />
      </svg>
    </span>
  );
}

/* ---------------- BUILD (parse + constraints + clarify) ---------------- */
function PBuild() {
  const { task, setTask, toast } = React.useContext(StoreCtx);
  const [assembling, setAssembling] = React.useState(false);
  const ambiguous = task.trim().length < 28; // short → ask one clarifying question
  const assemble = () => { setAssembling(true); setTimeout(() => navigate('/results'), 850); };
  return (
    <div className="pt-page pt-view">
      <div className="pt-page-head">
        <h1>Confirm the task</h1>
        <div className="sub">We parsed your task — edit it or add constraints, then assemble.</div>
      </div>
      <div className="pt-intent">
        <div>
          <div className="pt-panel">
            <div className="oh-cc-id mono" style={{ marginBottom: 8 }}>task</div>
            <textarea className="pt-dash-entry" style={{ width: '100%', minHeight: 70, border: 'none', background: 'transparent', color: 'var(--fg)', font: 'inherit', resize: 'none', outline: 'none' }}
              value={task} onChange={(e) => setTask(e.target.value)} />
            <div className="pt-intent-tags">
              <span className="pt-tag">kind <b>classification + grading</b></span>
              <span className="pt-tag">domain <b>ESG · CSDDD</b></span>
              <span className="pt-tag">modality <b>text + tabular</b></span>
              <span className="pt-tag">privacy <b>supplier PII</b></span>
            </div>
          </div>
          {ambiguous && (
            <div className="pt-clarify">
              <div className="q">⚠ This task is a little broad. Which due-diligence scope?</div>
              <div className="opts">
                {['Tier-1 suppliers only', 'Full supply chain', 'Sanctions + sector risk'].map((o) => (
                  <button key={o} className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => setTask((t) => t + ' — ' + o.toLowerCase())}>{o}</button>
                ))}
              </div>
            </div>
          )}
          <div style={{ fontSize: 12, color: 'var(--fg-faint)', marginTop: 14, display: 'flex', gap: 8, alignItems: 'center' }}>
            <span className="oh-badge oh-badge--warn">preview retrieval</span> using placeholder embeddings — connect a source for semantic retrieval.
          </div>
        </div>
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 12 }}>constraints</div>
          {[['Hosting', ['Cloud', 'BYO-cloud', 'Air-gapped']], ['Budget', ['Low', 'Balanced', 'No cap']], ['Quality target', ['Fast', 'High lift']]].map(([g, opts]) => (
            <div key={g} style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: 'var(--fg-faint)', marginBottom: 7 }}>{g}</div>
              <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
                {opts.map((o, i) => <span key={o} className={'pt-cons-chip' + (i === 1 ? ' on' : '')}>{o}</span>)}
              </div>
            </div>
          ))}
          <button className="oh-btn oh-btn--primary" style={{ width: '100%', justifyContent: 'center', marginTop: 6 }}
            disabled={assembling} onClick={assemble}>
            {assembling ? 'Assembling…' : 'Assemble flow →'}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------------- RESULTS (three costed options, lift-led) ---------------- */
function MiniStrip({ dag }) {
  return (
    <div className="oh-minidag">
      {dag.map((n, i) => (
        <React.Fragment key={i}>
          {n === 'op' ? <span className="oh-mininode is-op">◇</span>
            : <span className="oh-mininode" style={{ background: `var(${PRIMS[n].v})` }}>{PRIMS[n].glyph}</span>}
          {i < dag.length - 1 && <span className="oh-miniedge" />}
        </React.Fragment>
      ))}
    </div>
  );
}
const TIERS = [
  { tier: 'Cheap', dag: ['input', 'knowledge', 'action', 'output'], lift: '+0.21', comps: '4 components', packs: '1 knowledge pack', gov: 'keyword · MIT', cost: 'est. low', lat: '~6s', freeze: '~80% freezable' },
  { tier: 'Balanced', rec: true, dag: ['input', 'conditional', 'op', 'knowledge', 'action', 'output'], lift: '+0.41', comps: '6 components', packs: '2 knowledge · 1 conditional', gov: 'sourced · MIT', cost: 'est. medium', lat: '~14s', freeze: '~65% freezable' },
  { tier: 'Quality-first', dag: ['input', 'conditional', 'op', 'knowledge', 'action', 'loop', 'output'], lift: '+0.55', comps: '9 components', packs: '3 knowledge · 2 conditional', gov: 'verified · CC-BY', cost: 'est. high', lat: '~38s', freeze: '~55% freezable' },
];
function PResults() {
  const [loading, setLoading] = React.useState(true);
  React.useEffect(() => { const t = setTimeout(() => setLoading(false), 650); return () => clearTimeout(t); }, []);
  return (
    <div className="pt-page pt-view">
      <div className="pt-page-head">
        <h1>Three flows for this task</h1>
        <div className="sub">Each adds vetted components &amp; knowledge for more lift — cost barely moves, because most lift is <span className="mono">freezable</span> (zero recurring).</div>
      </div>
      <div className="pt-grid-3">
        {((window.OHHLive && OHHLive.tiers()) || TIERS).map((t) => (
          <div key={t.tier} className={'oh-result' + (t.rec ? ' oh-result--rec' : '')}>
            <div className="oh-result-tierrow">
              <span className={'oh-tier' + (t.rec ? ' oh-tier--rec' : '')}>{t.tier}</span>
              {t.rec && <span className="oh-rec-badge">Recommended</span>}
            </div>
            {loading ? <div className="oh-minidag"><span className="oh-skel-line" style={{ width: '70%' }} /></div> : <MiniStrip dag={t.dag} />}
            <div className="oh-result-lift">{t.lift ? <span className="big">▲ {t.lift}</span> : <span className="oh-badge oh-badge--muted">— unproven</span>}<span className="sub">capability lift vs a bare model</span></div>
            <div className="oh-result-src">{t.comps} · <b>{t.packs}</b> doing the lift</div>
            <div className="oh-cc-badges"><span className="oh-badge oh-badge--verified"><span className="gl">✔</span> {t.gov}</span></div>
            <div className="oh-result-cost"><span className="mono">{t.cost} · {t.lat}</span><span className="freeze">{t.freeze}</span></div>
            <button className={'oh-btn ' + (t.rec ? 'oh-btn--primary' : 'oh-btn--ghost')} style={{ justifyContent: 'center' }} onClick={() => navigate('/flow')}>Open flow</button>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------------- FLOW (interactive nodes + inspector) ---------------- */
const pbez = (a, b) => { const dx = Math.max(26, Math.abs(b.x - a.x) * 0.5); return `M${a.x},${a.y} C${a.x + dx},${a.y} ${b.x - dx},${b.y} ${b.x},${b.y}`; };
function PFlow() {
  const { toast } = React.useContext(StoreCtx);
  const [sel, setSel] = React.useState(null);
  const FLOWSRC = (window.OHHLive && OHHLive.flowSlots()) || PFLOW;  // live seam: the REAL build in the designed canvas
  const N = Object.fromEntries(FLOWSRC.nodes.map((n) => [n.id, n]));
  const R = (n) => ({ x: n.x + PFW, y: n.y + PFH / 2 }), L = (n) => ({ x: n.x, y: n.y + PFH / 2 }), B = (n) => ({ x: n.x + PFW / 2, y: n.y + PFH });
  const op = FLOWSRC.op, opL = { x: op.x, y: op.y + op.h / 2 }, opR = { x: op.x + op.w, y: op.y + op.h / 2 };
  const fwd = [[R(N.input), L(N.ct)], [R(N.input), L(N.ca)], [R(N.ct), opL], [R(N.ca), opL], [opR, L(N.kc)], [R(N.kc), L(N.act)], [R(N.act), L(N.ev)]];
  const evB = B(N.ev), actB = B(N.act);
  const loop = `M${evB.x},${evB.y} C${evB.x},${evB.y + 62} ${actB.x},${actB.y + 62} ${actB.x},${actB.y}`;
  const selNode = sel && N[sel];
  const comp = selNode && selNode.slug ? BY_SLUG[selNode.slug] : null;
  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
      <div className="pt-flow-toolbar">
        <span className="pt-crumb"><b>{(window.OHHLive && OHHLive.flowName()) || 'flow/csddd-grade'}</b>{!(window.OHHLive && OHHLive.flow()) && <span className="oh-badge oh-badge--lift" style={{ marginLeft: 6 }}>▲ +0.41</span>}</span>
        <span className="pt-spacer" />
        <select className="pt-select" defaultValue="gpt-class" title="Model swap"><option value="gpt-class">model: gpt-class</option><option>claude-class</option><option>local · llama</option></select>
        <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/run')}>▶ Run</button>
        <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Cost table opened')}>Cost</button>
        <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Flow saved · ' + ((window.OHHLive && OHHLive.flowName()) || 'flow/csddd-grade'))}>Save</button>
        <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => { if (window.OHHLive && OHHLive.flow() && OHHLive.exportYaml()) { toast('Deploy bundle exported · open-spec YAML'); } else { toast('Deploy bundle generated'); } }}>Deploy</button>
      </div>
      <div className="pt-flow-wrap" style={{ flex: 1, minHeight: 0 }}>
        <div className="pt-flow-canvas-host oh-flow" style={{ position: 'relative' }}>
          <div style={{ position: 'relative', width: 1480, height: 420 }}>
            <svg className="oh-flow-svg">
              <defs><marker id="pah" markerWidth="9" markerHeight="9" refX="6.5" refY="3" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L7,3 L0,6 Z" fill="context-stroke" /></marker></defs>
              <g fill="none" stroke="var(--fg-faint)" strokeWidth="1.5" markerEnd="url(#pah)" opacity="0.85">{fwd.map((e, i) => <path key={i} d={pbez(e[0], e[1])} />)}</g>
              <path d={pbez(R(N.ev), L(N.out))} fill="none" stroke="var(--success)" strokeWidth="1.6" markerEnd="url(#pah)" />
              <path d={loop} fill="none" stroke="var(--p-loop)" strokeWidth="1.75" strokeDasharray="5 3" markerEnd="url(#pah)" />
            </svg>
            {FLOWSRC.nodes.map((n) => {
              const p = PRIMS[n.k];
              return (
                <div key={n.id} className="oh-fnode" onClick={() => setSel(n.id)}
                  style={{ left: n.x, top: n.y, ['--nodehue']: `var(${p.v})`, cursor: 'pointer', outline: sel === n.id ? '2px solid var(--accent)' : 'none', outlineOffset: 2 }}>
                  <div className="ftop"><span className="fp">{p.glyph} {p.label}</span><span className="fsp" />{n.lift && <span className="flift">▲ {n.lift}</span>}</div>
                  <div className="fn">{n.name}</div><div className="fid">{n.ref}</div><div className="ff">{n.facts}</div>
                </div>
              );
            })}
            <div className="oh-fop" style={{ left: op.x, top: op.y, width: op.w, height: op.h }}>◇ {FLOWSRC.opLabel || 'OR'}</div>
            <span className="oh-fcall" style={{ left: N.act.x + PFW / 2, top: N.act.y - 24, transform: 'translateX(-50%)' }}>1 model call / item</span>
            <span className="oh-flbl loop" style={{ left: (evB.x + actB.x) / 2, top: evB.y + 48 }}>↻ refine · same call ×N</span>
          </div>
          <div className="oh-validity" style={{ position: 'absolute' }}><span>✓</span> Single-call pattern — Conditional routes first, Knowledge feeds one harness call; the refine loop re-runs it. Click any node to inspect or swap.</div>
        </div>
        {selNode && (
          <aside className="pt-drawer">
            <div className="pt-drawer-hd">
              <button className="pt-drawer-close" onClick={() => setSel(null)}>×</button>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: `var(${PRIMS[selNode.k].v})` }}>{PRIMS[selNode.k].glyph} {PRIMS[selNode.k].label}</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--fg)', marginTop: 3 }}>{selNode.name}</div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--fg-faint)' }}>{selNode.ref}</div>
            </div>
            <div className="pt-drawer-bd">
              {comp ? <>
                <div className="oh-cc-badges">{liftBadge(comp)}{provBadge(comp.prov)}<span className="oh-badge mono">{comp.cost}{comp.recurring ? '' : ' freezable'}</span></div>
                <p style={{ fontSize: 13, color: 'var(--fg-muted)', lineHeight: 1.5, margin: 0 }}>{comp.desc}</p>
                <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ justifyContent: 'center' }} onClick={() => navigate('/c/' + comp.slug)}>Open component →</button>
              </> : <p style={{ fontSize: 13, color: 'var(--fg-muted)' }}>Structural input node.</p>}
              {(() => { const __alts = (window.OHHLive && OHHLive.flow()) ? OHHLive.alts(sel, selNode) : ALTS[sel]; return __alts && <>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.09em', textTransform: 'uppercase', color: 'var(--fg-faint)', marginTop: 4 }}>Swap — alternatives by lift</div>
                {__alts.map((a) => (
                  <div key={a.name} className="pt-alt" style={a.on ? { borderColor: 'var(--accent)' } : null} onClick={() => { if (!a.on) toast('Swapped → ' + a.name); }}>
                    <span className="nm">{a.name}<small>{a.meta}</small></span>
                    {a.on ? <span className="oh-badge oh-badge--lift" style={{ padding: '2px 7px' }}>in use</span> : <span style={{ fontSize: 11, color: 'var(--accent)' }}>swap</span>}
                  </div>
                ))}
              </>; })()}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

/* ---------------- RUN / TRACE (simulate, stream, error+retry) ---------------- */
const RUN_STEPS = [
  { step: '01', k: 'input', ref: 'inputs/supplier-roster', tok: '—', cost: '—', ms: '4ms' },
  { step: '02', k: 'conditional', ref: 'conditional/tier-risk-gate', tok: '—', cost: '—', ms: '2ms' },
  { step: '03', k: 'knowledge', ref: 'knowledge-corpus/csddd-articles', tok: '2.1k', cost: '$0.0021', ms: '380ms' },
  { step: '04', k: 'action', ref: 'harness/esg-cite-first', model: true, tok: '5.8k', cost: '$0.0279', ms: '', err: true },
  { step: '05', k: 'loop', ref: 'rubric/qa-eval', tok: '0.4k', cost: '$0.0008', ms: '95ms' },
  { step: '06', k: 'output', ref: 'outputs/csddd-dossier', tok: '0.5k', cost: '$0.0012', ms: '120ms' },
];
function PRun() {
  const { toast } = React.useContext(StoreCtx);
  const [done, setDone] = React.useState(0); // steps completed
  const [running, setRunning] = React.useState(false);
  const [errored, setErrored] = React.useState(false);
  const [recovered, setRecovered] = React.useState(false);
  const timer = React.useRef(null);
  const run = (fromRetry) => {
    setRunning(true); if (!fromRetry) { setDone(0); setErrored(false); setRecovered(false); }
    if (window.OHHLive && !fromRetry) OHHLive.execRun();  // the REAL execution kicks here
    let i = fromRetry ? 3 : 0;
    const tick = () => {
      const lt = window.OHHLive && OHHLive.runTrace();
      if (window.OHHLive && !lt) { timer.current = setTimeout(tick, 800); return; }  // real call in flight
      const src = (lt && lt.rows) || RUN_STEPS;
      i += 1; setDone(i);
      if (!lt && i === 4 && !recovered && !fromRetry) { setRunning(false); setErrored(true); return; }
      if (i >= src.length) { setRunning(false); toast('Run complete · ' + ((lt && lt.totals && lt.totals.cost) || '$0.0312')); return; }
      timer.current = setTimeout(tick, 600);
    };
    timer.current = setTimeout(tick, 500);
  };
  const retry = () => { setRecovered(true); setErrored(false); run(true); };
  React.useEffect(() => () => clearTimeout(timer.current), []);
  return (
    <div className="pt-page pt-view">
      <div className="pt-page-head"><h1>Run &amp; trace</h1><div className="sub">Replayable compliance record — every step, cost, and citation.</div></div>
      {(window.OHHLive && OHHLive.runTrace()) ? <div className="pt-sim-banner" style={{ borderColor: 'var(--success)', color: 'var(--success)' }}>● Live mode — the model step is a REAL call ({OHHLive.runTrace().model_id}) with measured latency; the trace below is what actually executed.</div> : <div className="pt-sim-banner">◌ Simulate mode — model steps are echo-stubs until a provider key is connected. <span style={{ marginLeft: 'auto' }}><a style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => navigate('/nope')}>Connect key →</a></span></div>}
      <div className="pt-run-input pt-panel" style={{ marginBottom: 16 }}>
        <span style={{ fontSize: 13, color: 'var(--fg-muted)' }}>Sample input</span>
        <span className="oh-badge mono">{(window.OHHLive && OHHLive.runTrace()) ? 'synthetic sample · 1 item' : 'suppliers.csv · 1 row'}</span>
        <span className="pt-spacer" />
        {!running && <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => run(false)}>▶ {done ? 'Re-run' : 'Run flow'}</button>}
        {running && <button className="oh-btn oh-btn--ghost oh-btn--sm" disabled>Running…</button>}
      </div>
      <div className="oh-trace-stage" style={{ border: '1px solid var(--line)', borderRadius: 'var(--r-lg)', height: 'auto' }}>
        <div className="oh-trace-hd">
          <h3>Trace</h3>
          <div className="oh-trace-tot">
            <div className="t"><div className="v">{done >= 5 ? (((window.OHHLive && OHHLive.runTrace()) || {}).totals || {}).cost || '$0.0312' : '—'}</div><div className="k">est. cost</div></div>
            <div className="t"><div className="v">{done >= 5 ? ((window.OHHLive && OHHLive.runTrace()) ? (((OHHLive.runTrace().rows.find((r) => r.model) || {}).tok) || '—') : '8.4k') : '—'}</div><div className="k">tokens</div></div>
            <div className="t"><div className="v">{done >= 5 ? ((window.OHHLive && OHHLive.runTrace()) ? ((OHHLive.runTrace().rows.some((r) => /cites retrieved context ✓/.test(r.note || '')) ? '✓' : '—')) : '11') : '—'}</div><div className="k">citations</div></div>
          </div>
        </div>
        {(((window.OHHLive && OHHLive.runTrace()) || {}).rows || RUN_STEPS).slice(0, Math.max(done, errored ? 4 : done)).map((s, idx) => {
          const isErr = (s.err && errored && !recovered && idx === 3) || s.status === 'err';
          return (
            <div key={s.step} className="oh-trace-row" style={{ ['--nodehue']: `var(${PRIMS[s.k].v})` }}>
              <span className="step">{s.step}</span>
              <span className="prim"><span className="pd" style={{ background: `var(${PRIMS[s.k].v})` }} /><span className="pl">{PRIMS[s.k].label}</span></span>
              <span className="ref">{s.ref} {s.model && <span className="modelflag">model</span>}</span>
              <span className="mono">{s.tok}</span>
              <span className="mono">{s.cost}</span>
              {isErr ? <span className="mono sim" style={{ color: 'var(--danger)' }}>⊘ timeout</span>
                : <span className="mono ok">✓ {s.ms || 'sim'}</span>}
            </div>
          );
        })}
        {errored && !recovered && (
          <div className="oh-state-msg error" style={{ margin: 14 }}>
            <span className="gl">⊘</span>
            <span><b>Model provider timed out</b> at the harness call. Nothing was charged for the failed step.
              <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ marginLeft: 10 }} onClick={retry}>↻ Retry step</button></span>
          </div>
        )}
      </div>
    </div>
  );
}

function PPreview() {
  const { task, setLoggedIn } = React.useContext(StoreCtx);
  const [step, setStep] = React.useState(0);
  React.useEffect(() => { if (step < 4) { const t = setTimeout(() => setStep((s) => s + 1), 650); return () => clearTimeout(t); } }, [step]);
  const done = step >= 4;
  const [, liveTick] = React.useState(0);  // live seam: re-render when the real build lands
  React.useEffect(() => { if (window.OHHLive) OHHLive.build(task).then(() => liveTick((t) => t + 1)); }, []);
  const STEPS = ['Parsing the task', 'Retrieving vetted components', 'Assembling the flow', 'Costing & measuring lift'];
  const PHASES = [
    { label: null, steps: [
      { k: 'input', name: 'Input text', pol: 'always', desc: 'the text / document the pipeline runs on at runtime' },
      { k: 'conditional', name: 'Trigger gate — does the input qualify?', pol: 'default',
        desc: 'qualify, skip, or route before any model spend — assembled from combinable pattern & anti-pattern packs',
        packs: [
          { kind: 'pattern', label: 'Pattern pack', ref: 'pattern-pack/high-risk-recruitment-flags', note: 'qualify on match' },
          { kind: 'anti', label: 'Anti-pattern pack', ref: 'pattern-pack/benign-recruitment-allowlist', note: 'skip on match' },
        ] },
    ] },
    { label: 'Pre-model-call', steps: [
      { k: 'action', name: 'Add persona', pol: 'default', desc: 'the role & expertise the model adopts — role only, never the task or schema · built-in' },
      { k: 'action', name: 'Build the system prompt', pol: 'default', desc: 'task, constraints & output schema — kept separate from the persona · built-in' },
      { k: 'knowledge', name: 'Knowledge retrieval — keyword match', pol: 'default', desc: 'knowledge-pack/high-risk-corridors-and-sectors' },
      { k: 'knowledge', name: 'Knowledge retrieval — regex', pol: 'optional', desc: 'rule-pack/grep-esg-environmental-red-flags' },
      { k: 'knowledge', name: 'Knowledge retrieval — RAG (vector)', pol: 'default', desc: 'knowledge-pack/csddd-article-corpus · 13 langs' },
      { k: 'knowledge', name: 'Knowledge ranking', pol: 'optional', desc: 're-rank retrieved facts by relevance before they enter the prompt · built-in' },
      { k: 'knowledge', name: 'Knowledge summarizing', pol: 'optional', desc: 'compress retrieved context to the salient cited spans · built-in' },
      { k: 'action', name: 'Check online facts / search', pol: 'optional', desc: 'verify volatile facts against a live source · built-in' },
      { k: 'action', name: 'Token reduction — prioritize · compress', pol: 'default', desc: 'order salient evidence first; compress to cut tokens & cost · built-in' },
      { k: 'stop', name: 'Prompt-injection check', pol: 'default', desc: 'block if the input tries to extract or override the system prompt · built-in' },
    ] },
    { label: 'Model call', steps: [
      { k: 'action', name: 'Call the right-sized model', pol: 'always', desc: 'harness/customer-renewal-risk-review' },
    ] },
    { label: 'Post-model-call', steps: [
      { k: 'output', name: 'Check output', pol: 'always', desc: 'validate against the expected answer shape · built-in' },
      { k: 'output', name: 'Verify JSON (recover if malformed)', pol: 'default', desc: 'parse; if non-JSON, repair / reformat once · built-in' },
      { k: 'output', name: 'Re-verify', pol: 'default', desc: 'second pass on the recovered output · built-in' },
      { k: 'loop', name: 'If not OK … retry with changes (≤3)', pol: 'always', desc: 're-run with targeted fixes until it passes, else escalate · built-in' },
      { k: 'output', name: 'Findings (JSON) + citations', pol: 'always', desc: 'structured findings with a citation behind every claim · built-in' },
    ] },
  ];
  const LIVEPV = window.OHHLive ? OHHLive.phases() : null;  // real assembled components when the backend answered
  const PHASES_SRC = LIVEPV || PHASES;
  const total = PHASES_SRC.reduce((n, p) => n + p.steps.length, 0);
  const POL = { always: 'Always', default: 'Default', optional: 'Optional' };
  return (
    <div className="pt-mkt pt-view">
      <window.OhTopBar brand={{ name: 'OpenHubForAI', realm: 'openharnesshub', tld: '.io', glyph: '⎔', accent: 'var(--accent)' }}
        cta={{ label: 'Start free', href: '/signup' }} signInHref="/signin" />
      <div className="pt-mkt-body">
        <div className="pt-pv">
          <div className="pt-pv-head">
            <div className="eyebrow">{done ? 'Flow assembled · model-built' : 'Assembling your flow'}</div>
            <h1>{done ? 'Your governed flow is ready' : 'Building your flow…'}</h1>
            <div className="task">“{(task || 'grade suppliers against CSDDD and cite the exact articles').slice(0, 120)}”</div>
          </div>

          {!done ? (
            <div className="pt-pv-progress">
              {STEPS.map((s, i) => (
                <div key={s} className={'row' + (i < step ? ' done' : i === step ? ' active' : '')}>
                  <span className="mk">{i < step ? '✓' : i === step ? '◌' : '·'}</span>
                  <span className="lb">{s}</span>
                  {i < step && <span className="oh-badge oh-badge--lift">done</span>}
                </div>
              ))}
            </div>
          ) : (
            <div className="pt-pv-grid">
              <div className="pt-pv-main">
                {PHASES_SRC.map((ph, pi) => (
                  <section className="pt-pv-phase" key={pi}>
                    {ph.label && <div className="ph-label"><span>{ph.label}</span></div>}
                    <div className="pt-pv-steps">
                      {ph.steps.map((st, si) => (
                        <div className={'pt-pv-step pol-' + st.pol} key={si}>
                          <span className="chip" style={{ background: `var(${PRIMS[st.k].v})` }}>{PRIMS[st.k].glyph}</span>
                          <div className="body">
                            <div className="r1">
                              <span className="name">{st.name}</span>
                              <span className={'pol ' + st.pol}>{POL[st.pol]}</span>
                            </div>
                            <div className="desc">{st.desc}</div>
                            {st.packs && (
                              <div className="pt-pv-packs">
                                {st.packs.map((p, pj) => (
                                  <div className={'pack ' + p.kind} key={pj}>
                                    <span className="sign">{p.kind === 'pattern' ? '✓' : '✕'}</span>
                                    <span className="plabel">{p.label}</span>
                                    <span className="pref">{p.ref}</span>
                                    <span className="pnote">{p.note}</span>
                                  </div>
                                ))}
                                <button className="pt-pv-addpack" type="button">+ combine another pack</button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                ))}
              </div>

              <aside className="pt-pv-side">
                <div className="pt-pv-summary">
                  <div className="row"><span className="k">Steps</span><span className="v">{total}</span></div>
                  <div className="row"><span className="k">Est. cost / run</span><span className="v">{(LIVEPV && OHHLive.costRange()) || '$0.01–0.10'}</span></div>
                  {!LIVEPV && <div className="row"><span className="k">Measured lift</span><span className="v lift">▲ +0.33</span></div>}
                  <div className="row"><span className="k">Assembly</span><span className="v">{(LIVEPV && OHHLive.assembly()) || 'model-built'}</span></div>
                  <div className="note">Most steps are deterministic &amp; freezable — they add capability without adding cost.</div>
                </div>
                <div className="pt-pv-cta">
                  <h3>Sign up to run it — or download the bundle</h3>
                  <p>Create a free account to run this flow (simulate or live), open it in the builder, or export the open-spec bundle. The spec &amp; export are free.</p>
                  <button className="oh-btn oh-btn--primary" onClick={() => navigate('/signup')}>Sign up free →</button>
                  <button className="oh-btn oh-btn--ghost" onClick={() => navigate('/signin')}>Sign in</button>
                </div>
              </aside>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PLanding, PBuild, PResults, PFlow, PRun, Mark, PPreview });
