/* global React, StoreCtx, navigate, PRIMS, BY_SLUG */
// Deeper surfaces: Foundry · Import & Improve · Dashboards · Settings · per-component deep config

/* ============================== FOUNDRY ============================== */
const FUNNEL = [
  ['Areas probed', 'gap_screen', 8420, '#fb7714', 100],
  ['Gaps confirmed', 'measured failures', 2310, '#d29922', 27],
  ['Sources found', 'rich veins', 1870, '#3fb950', 22],
  ['Drafts built', 'candidate components', 1440, '#a371f7', 17],
  ['Standardized', 'normal form', 1290, '#58a6ff', 15],
  ['Lift measured', 'bare vs pipeline', 1290, '#39c5cf', 15],
];
const REJECTS = [['No measured lift', 920, 100], ['Filler / redundant', 410, 45], ['Unsourced provenance', 230, 25], ['Duplicate of existing', 160, 18]];
const SOURCES = [['regulation', 'EUR-Lex · CSDDD + 40 regs', '+312'], ['dataset', 'HuggingFace governed sets', '+188'], ['repo', 'OSS pipeline ecosystems', '+96'], ['api', 'Standards-body endpoints', '+54']];
function PFoundry() {
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Foundry</h1><div className="sub">Evidence-driven component factory — the headline metric is <b>promoted</b>, never generated.</div></div>
      <div className="pt-foundry-top">
        <div className="pt-bigstat hero"><div className="v">1,284</div><div className="k"><b>promoted</b> · cleared the lift gate</div></div>
        <div className="pt-bigstat"><div className="v">8,420</div><div className="k">areas probed</div></div>
        <div className="pt-bigstat"><div className="v">15.2%</div><div className="k">probe → promote rate</div></div>
        <div className="pt-bigstat"><div className="v">$2.1k</div><div className="k">budget burn · this run</div></div>
      </div>
      <div className="pt-row" style={{ flexWrap: 'wrap', gap: 16 }}>
        <div className="pt-panel" style={{ flex: '2 1 460px' }}>
          <div className="oh-cc-id mono" style={{ marginBottom: 12 }}>the funnel — narrows to what actually lifts</div>
          <div className="pt-funnel">
            {FUNNEL.map(([lbl, sub, n, c, pct]) => (
              <div className="pt-funnel-row" key={lbl}>
                <span className="lbl">{lbl}<small>{sub}</small></span>
                <span className="pt-funnel-bar"><i style={{ width: pct + '%', background: `linear-gradient(90deg, color-mix(in srgb, ${c} 55%, var(--panel)), ${c})` }}>{n.toLocaleString()}</i></span>
                <span className="rej none">—</span>
              </div>
            ))}
            <div className="pt-funnel-row promoted">
              <span className="lbl">Promoted<small>tenant-visible</small></span>
              <span className="pt-funnel-bar"><i style={{ width: '15%' }}>1,284</i></span>
              <span className="rej none">✓ gate</span>
            </div>
          </div>
        </div>
        <div className="pt-panel" style={{ flex: '1 1 280px' }}>
          <div className="oh-cc-id mono" style={{ marginBottom: 12 }}>reject log — by reason</div>
          <div className="pt-rejlog">
            {REJECTS.map(([nm, ct, w]) => (
              <div className="r" key={nm}><span className="nm">{nm}</span><span className="bar"><i style={{ width: w + '%' }} /></span><span className="ct">{ct}</span></div>
            ))}
          </div>
        </div>
      </div>
      <div className="pt-panel" style={{ marginTop: 16 }}>
        <div className="oh-cc-id mono" style={{ marginBottom: 6 }}>source surfaces — yield (gate-passed components)</div>
        {SOURCES.map(([kind, nm, y]) => (
          <div className="pt-source-row" key={nm}><span className="kind">{kind}</span><span className="nm">{nm}</span><span className="yield">{y}</span></div>
        ))}
      </div>
    </div>
  );
}

/* ============================== IMPORT & IMPROVE ============================== */
const FINDINGS = [
  ['Capability-lift', 'high', 'Step 3 ("summarize then re-ask") is something a bare model already does — removable for −1 call with no quality loss.'],
  ['Cost', 'high', 'Two sequential model calls can collapse into a deterministic Conditional + one harness call. Est. −42% / run.'],
  ['Governance', 'high', 'No citations or provenance on the legal claims. Swap in the governed CSDDD corpus (✔ sourced).'],
  ['Reliability', 'med', 'No output schema or eval gate — add a rubric pass before returning.'],
  ['Reuse', 'med', 'Your hand-rolled entity matcher ≈ processor/entity-resolver (▲ +0.14, MIT). Replace it.'],
];
function PImprove() {
  const { toast } = React.useContext(StoreCtx);
  const [acc, setAcc] = React.useState({ 0: true, 1: true, 2: true });
  const n = Object.values(acc).filter(Boolean).length;
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Import &amp; Improve</h1><div className="sub">Upload the pipeline you already run — get it critiqued, governed, and measurably improved.</div></div>
      <div className="pt-steps">
        {['Import', 'Normalize', 'Critique', 'Rebuild', 'Prove'].map((s, i) => (
          <React.Fragment key={s}><span className={'pt-step' + (i < 3 ? ' on' : '')}><span className="n">{i + 1}</span>{s}</span>{i < 4 && <span className="arr">→</span>}</React.Fragment>
        ))}
      </div>
      <div className="pt-improve">
        <div>
          <div className="pt-twin">
            <div className="lbl">Your pipeline — normalized to the seven primitives</div>
            <div className="oh-minidag" style={{ minHeight: 0 }}>
              {['input', 'action', 'action', 'action', 'action', 'output'].map((k, i) => (
                <React.Fragment key={i}><span className="oh-mininode" style={{ background: `var(${PRIMS[k].v})` }}>{PRIMS[k].glyph}</span>{i < 5 && <span className="oh-miniedge" />}</React.Fragment>
              ))}
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--fg-faint)', marginTop: 8 }}>11 steps · 4 model calls · no governance · est. $$$</div>
          </div>
          <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '.09em', textTransform: 'uppercase', color: 'var(--fg-faint)', margin: '14px 0 8px' }}>Critique — {n} fixes selected</div>
          {FINDINGS.map(([lens, sev, txt], i) => (
            <div key={i} className={'pt-finding' + (acc[i] ? ' accepted' : '')}>
              <div className="top"><span className="lens">{lens}</span><span className={'sev ' + sev}>{sev === 'high' ? 'high impact' : 'medium'}</span></div>
              <div className="rationale">{txt}</div>
              <div className="acts">
                <button className={'oh-btn oh-btn--sm ' + (acc[i] ? 'oh-btn--primary' : 'oh-btn--ghost')} onClick={() => setAcc((a) => ({ ...a, [i]: !a[i] }))}>{acc[i] ? '✓ Accepted' : 'Accept fix'}</button>
              </div>
            </div>
          ))}
        </div>
        <div>
          <div className="pt-deltas">
            <div className="pt-delta"><div className="k">Capability lift</div><div className="v good">▲ +0.37 <span className="was">was +0.00</span></div></div>
            <div className="pt-delta"><div className="k">Cost / run</div><div className="v cost">−42% <span className="was">$$$ → $$</span></div></div>
            <div className="pt-delta"><div className="k">Governance coverage</div><div className="v good">100% <span className="was">was 38%</span></div></div>
            <div className="pt-delta"><div className="k">Steps</div><div className="v">6 <span className="was">was 11</span></div></div>
          </div>
          <div className="pt-twin">
            <div className="lbl">Rebuilt — governed components</div>
            <div className="oh-minidag" style={{ minHeight: 0 }}>
              {['input', 'conditional', 'op', 'knowledge', 'action', 'output'].map((k, i, a) => (
                <React.Fragment key={i}>{k === 'op' ? <span className="oh-mininode is-op">◇</span> : <span className="oh-mininode" style={{ background: `var(${PRIMS[k].v})` }}>{PRIMS[k].glyph}</span>}{i < a.length - 1 && <span className="oh-miniedge" />}</React.Fragment>
              ))}
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--fg-faint)', marginTop: 8 }}>6 components · 1 model call · ✔ sourced · est. $$</div>
          </div>
          <div style={{ display: 'flex', gap: 9, marginTop: 14 }}>
            <button className="oh-btn oh-btn--primary" style={{ flex: 1, justifyContent: 'center' }} onClick={() => navigate('/flow')}>Open improved flow →</button>
            <button className="oh-btn oh-btn--ghost" onClick={() => toast('Critique report exported (PDF)')}>Export report</button>
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--fg-muted)', marginTop: 12, lineHeight: 1.5 }}>Deltas are <b style={{ color: 'var(--fg)' }}>measured</b> on your sample inputs — the same engine that gates the foundry. Your hand-rolled steps that clear the lift gate can be offered back as components (you earn credits).</div>
        </div>
      </div>
    </div>
  );
}

/* ============================== DASHBOARDS ============================== */
function Spark({ pts, color }) {
  const max = Math.max(...pts), min = Math.min(...pts);
  const d = pts.map((p, i) => `${(i / (pts.length - 1)) * 100},${54 - ((p - min) / (max - min || 1)) * 48 - 3}`).join(' ');
  return <svg className="pt-spark" viewBox="0 0 100 54" preserveAspectRatio="none"><polyline points={d} fill="none" stroke={color || 'var(--accent)'} strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>;
}
function PDashboards() {
  const { toast } = React.useContext(StoreCtx);
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Dashboards</h1><div className="sub">Composed from widgets bound to <b>component-generated data stores</b> — monitoring &amp; graphs your components emit themselves.</div></div>
      <div className="pt-widgets">
        <div className="pt-widget"><div className="wh">Runs · 7d<span className="src">runs/ledger</span></div><div className="metric">3,182</div><div className="sub up">▲ 12% vs prior</div></div>
        <div className="pt-widget"><div className="wh">Cost / run<span className="src">cost/store</span></div><div className="metric">$0.031</div><div className="sub down">▼ 8% (cache)</div></div>
        <div className="pt-widget"><div className="wh">Cache hit<span className="src">telemetry</span></div><div className="metric">61%</div><div className="sub">prompt + retrieval</div></div>
        <div className="pt-widget"><div className="wh">Citations<span className="src">trace/store</span></div><div className="metric">11.4</div><div className="sub">avg / run</div></div>
        <div className="pt-widget span2"><div className="wh">Spend by day<span className="src">cost/store</span></div><Spark pts={[12, 15, 11, 18, 16, 22, 19]} /></div>
        <div className="pt-widget span2"><div className="wh">Lift over time — decay watch<span className="src">measurement engine</span></div><Spark pts={[41, 41, 40, 39, 38, 38, 37]} color="var(--warning)" /><div className="sub down">esg-cite-first · −0.04 as base models improve · <b style={{ color: 'var(--warning)' }}>watch</b></div></div>
        <div className="pt-widget span2">
          <div className="wh">Dynamic corpora — freshness<span className="src">CDC</span></div>
          <div className="pt-statuslight"><span className="dot" style={{ background: 'var(--success)' }} />OFAC / SDN list · fresh · synced 4m ago</div>
          <div className="pt-statuslight"><span className="dot" style={{ background: 'var(--warning)' }} />Customs HS codes · stale · 9d</div>
          <div className="pt-statuslight"><span className="dot" style={{ background: 'var(--danger)' }} />Legacy sanctions feed · revoked</div>
        </div>
        <div className="pt-widget span2">
          <div className="wh">Top components by usage<span className="src">registry</span></div>
          {[['harness/esg-cite-first', '1.2k', '▲ +0.41'], ['knowledge-corpus/csddd-articles', '980', '▲ +0.18'], ['conditional/tier-risk-gate', '640', '▲ +0.09']].map(([id, u, l]) => (
            <div className="pt-statuslight" key={id} style={{ justifyContent: 'space-between' }}><span className="mono" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{id}</span><span style={{ color: 'var(--fg-muted)' }}>{u} runs · <span style={{ color: 'var(--success)' }}>{l}</span></span></div>
          ))}
        </div>
        <button className="pt-widget-add" onClick={() => toast('Pick a store / saved view to bind')}>+ Add widget</button>
      </div>
    </div>
  );
}

/* ============================== SETTINGS (deep config) ============================== */
function Switch({ on, onClick }) { return <span className={'pt-switch' + (on ? ' on' : '')} onClick={onClick}><i /></span>; }
// PSettings — now via the SHARED KIT (OhSettings), fed OHH's deep config sections.
function OhhSeg({ opts, sel }) {
  return <div className="oh-segment">{opts.map((m, i) => <button key={m} className={i === sel ? 'on' : ''}>{m}</button>)}</div>;
}
function PSettings() {
  const { toast } = React.useContext(StoreCtx);
  const { OhSettings, OhSwitch } = window;
  const [tg, setTg] = React.useState({ byok: true, cache: true, pii: true, residency: false, simulate: false });
  const t = (k) => setTg((s) => ({ ...s, [k]: !s[k] }));
  const sections = [
    { title: 'Model providers', rows: [
      { t: 'Bring your own keys', d: 'Run on your own provider accounts; we never store completions.', ctrl: <OhSwitch on={tg.byok} onToggle={() => t('byok')} /> },
      { t: 'OpenAI', d: 'gpt-class · default for balanced tier', ctrl: <input className="oh-input" type="password" defaultValue="sk-••••••••••••4f2a" /> },
      { t: 'Anthropic', d: 'claude-class · default for quality tier', ctrl: <input className="oh-input" type="password" defaultValue="sk-ant-••••••9c1b" /> },
      { t: 'Local · Ollama', d: 'llama-class · for air-gapped / local-first flows', ctrl: <span className="oh-badge oh-badge--verified">connected</span> },
      { t: 'Model-swap default', d: 'Which model new flows assume before you pick.', ctrl: <OhhSeg opts={['Cheap', 'Balanced', 'Quality']} sel={1} /> },
      { t: 'Prompt cache', d: 'Reuse cached prefixes to cut cost.', ctrl: <OhSwitch on={tg.cache} onToggle={() => t('cache')} /> },
    ] },
    { title: 'Deployment', rows: [
      { t: 'Deployment target', d: 'Where governed flows run.', ctrl: <OhhSeg opts={['Cloud', 'BYO-cloud', 'Air-gapped']} sel={0} /> },
      { t: 'Export targets', d: 'runtime bundle · Terraform · MCP server · Docker · CLI', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Bundle exported')}>Download bundle</button> },
      { t: 'Frozen vs live', d: 'Static / text-op components freeze; code-executing & dynamic corpora recur.', ctrl: <span className="oh-badge mono">8 frozen · 3 live</span> },
    ] },
    { title: 'Privacy boundaries', rows: [
      { t: 'PII redaction gate', d: 'Force a redaction Action before any model call on flagged inputs.', ctrl: <OhSwitch on={tg.pii} onToggle={() => t('pii')} /> },
      { t: 'Data residency · EU', d: 'Pin storage & inference to EU regions.', ctrl: <OhSwitch on={tg.residency} onToggle={() => t('residency')} /> },
      { t: 'Trust boundary', d: 'Max execution class allowed without review.', ctrl: <OhhSeg opts={['static', 'text-op', 'code']} sel={1} /> },
      { t: 'Simulate by default', d: 'Echo-stub model steps until explicitly run live.', ctrl: <OhSwitch on={tg.simulate} onToggle={() => t('simulate')} /> },
    ] },
    { title: 'Advanced', rows: [
      { t: 'Default temperature', d: 'Sampling temperature for new harness calls.', ctrl: <input className="oh-input" style={{ maxWidth: 90 }} defaultValue="0.2" /> },
      { t: 'Max output tokens', d: 'Per model call.', ctrl: <input className="oh-input" style={{ maxWidth: 90 }} defaultValue="2048" /> },
      { t: 'Request timeout', d: 'Abort a step after this long.', ctrl: <input className="oh-input" style={{ maxWidth: 90 }} defaultValue="30s" /> },
      { t: 'Retries & backoff', d: 'On transient provider errors.', ctrl: <OhhSeg opts={['0', '2', '5']} sel={1} /> },
      { t: 'Rate limit · req/min', d: 'Per API key.', ctrl: <input className="oh-input" style={{ maxWidth: 90 }} defaultValue="600" /> },
      { t: 'Batch concurrency', d: 'Parallel items in a map-over-list.', ctrl: <input className="oh-input" style={{ maxWidth: 90 }} defaultValue="8" /> },
      { t: 'Environment secrets', d: 'Injected into code-executing components at run.', ctrl: <span className="oh-badge mono">4 set</span> },
      { t: 'Webhooks', d: 'CDC events · decay flips · gate-blocked.', ctrl: <span className="oh-badge mono">2 endpoints</span> },
    ] },
    { title: 'Billing & plan', rows: [
      { t: 'Plan', d: 'Pro · $39 / seat / mo · 4 seats', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/pricing')}>Change plan</button> },
      { t: 'Usage add-ons', d: 'source scans · embeddings · eval runs · build-on-demand', ctrl: <span className="oh-badge mono">$214 this mo</span> },
      { t: 'Credits', d: 'Earned from contributed components that passed the gate.', ctrl: <span className="oh-badge oh-badge--lift">+ 1,250</span> },
    ] },
  ];
  return <OhSettings sections={sections} />;
}

/* ============================== PER-COMPONENT DEEP CONFIG ============================== */
const OVERRIDES = {
  harness: [['model_target', 'gpt-class', 'the model this harness wraps'], ['trust boundary', 'text-op', 'max execution class'], ['citation gate', 'on', 'require sourced claims']],
  'knowledge-corpus': [['retrieval trigger', 'rag · exact-id', 'how facts surface'], ['chunking', '512 tok', 'window size'], ['refresh', 'static', 'static vs CDC dynamic']],
  rubric: 'weights',
  'rule-pack': [['threshold · tier', '≥ 2', 'when to route to review'], ['languages', '13', 'rule coverage']],
  tool: [['timeout', '30s', 'per-call ceiling'], ['side-effects', 'none', 'sandbox policy']],
};
function CompConfig({ c }) {
  const { toast } = React.useContext(StoreCtx);
  const [tab, setTab] = React.useState('configure');
  const [pinned, setPinned] = React.useState('1.3.0');
  const ov = OVERRIDES[c.type] || [['enabled', 'true', 'include in flows']];
  const weights = [['Citation accuracy', 40], ['Coverage', 30], ['Tone / stance', 15], ['Brevity', 15]];
  const versions = [['1.3.0', 'latest · 4d ago', '+0.41'], ['1.2.0', '6w ago', '+0.38'], ['1.1.0', '3mo ago', '+0.31']];
  return (
    <div className="pt-config">
      <div className="pt-config-tabs">
        <button className={tab === 'configure' ? 'on' : ''} onClick={() => setTab('configure')}>Configure</button>
        <button className={tab === 'versions' ? 'on' : ''} onClick={() => setTab('versions')}>Versions &amp; pinning</button>
      </div>
      {tab === 'configure' ? <>
        {ov === 'weights' || c.type === 'rubric'
          ? weights.map(([nm, w]) => (
            <div className="pt-override" key={nm}><span className="nm">{nm}<small>dimension weight</small></span>
              <span className="pt-weight"><span className="track"><i style={{ width: w + '%' }} /></span><span className="val">{w}%</span></span></div>))
          : ov.map(([nm, val, d]) => (
            <div className="pt-override" key={nm}><span className="nm">{nm}<small>{d}</small></span><span className="oh-badge mono">{val}</span></div>))}
        <div style={{ display: 'flex', gap: 9, marginTop: 14 }}>
          <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Reset to defaults')}>Reset to default</button>
          <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => toast('Forked as tenant variant · lineage recorded')}>Save as variant (fork) →</button>
          <span style={{ fontSize: 11.5, color: 'var(--fg-faint)', alignSelf: 'center' }}>A behavior change re-triggers lift measurement.</span>
        </div>
      </> : <>
        {versions.map(([v, when, lift]) => (
          <div className="pt-ver" key={v}><span className="sem">{v}</span><span className="when">{when}</span><span className="oh-badge oh-badge--lift" style={{ padding: '2px 7px' }}>▲ {lift}</span>
            <button className={'pt-ver-pin pin' + (pinned === v ? ' pinned' : '')} onClick={() => { setPinned(v); toast('Pinned @' + v); }}>{pinned === v ? '📌 pinned' : 'pin'}</button></div>
        ))}
        <div style={{ fontSize: 11.5, color: 'var(--fg-muted)', marginTop: 12 }}>Pinning keeps your flows from drifting when a component updates. Rolling back mints a <b style={{ color: 'var(--fg)' }}>new</b> version — published versions are never mutated. <b>3 flows</b> pin <span className="mono">@{pinned}</span>.</div>
      </>}
    </div>
  );
}

Object.assign(window, { PFoundry, PImprove, PDashboards, PSettings, CompConfig });
