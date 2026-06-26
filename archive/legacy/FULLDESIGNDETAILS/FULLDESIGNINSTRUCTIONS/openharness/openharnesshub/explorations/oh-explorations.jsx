/* global React, PRIMS */
// Builder-results layout studies + flowchart/diagram studies.
// Same task content as artifact ② / ④; only the layout/diagram grammar varies.

const TIERS = [
  { tier: 'Cheap', dag: ['input', 'knowledge', 'action', 'output'], comps: 4, cost: '$ est. low', lat: '~6s', lift: '+0.21', prov: '⚠ partial', lic: 'MIT', best: 'quick triage, low stakes' },
  { tier: 'Balanced', rec: true, dag: ['input', 'conditional', 'op', 'knowledge', 'action', 'output'], comps: 6, cost: '$$ est. mid', lat: '~14s', lift: '+0.41', prov: '✔ sourced', lic: 'MIT', best: 'most regulated work' },
  { tier: 'Quality-first', dag: ['input', 'conditional', 'op', 'knowledge', 'action', 'loop', 'output'], comps: 9, cost: '$$$ est. high', lat: '~38s', lift: '+0.55', prov: '🛡 verified', lic: 'CC-BY', best: 'audit-grade, high stakes' },
  { tier: 'Local-first', dag: ['input', 'conditional', 'knowledge', 'action', 'output'], comps: 5, cost: '⌂ on-prem', lat: '~22s', lift: '+0.33', prov: '✔ sourced', lic: 'MIT', best: 'air-gapped / BYO-cloud' },
];

function Strip({ dag, sm }) {
  return (
    <span className="oh-mini-strip">
      {dag.map((n, i) => (
        <React.Fragment key={i}>
          {n === 'op'
            ? <span className="d op">◇</span>
            : <span className="d" style={{ background: `var(${PRIMS[n].v})` }}>{PRIMS[n].glyph}</span>}
          {i < dag.length - 1 && <span className="e" />}
        </React.Fragment>
      ))}
    </span>
  );
}

/* ===== STUDY 1 — comparison matrix (dense, instrument-grade) ===== */
function ResultsTable() {
  const rows = [
    ['Pipeline', (t) => <Strip dag={t.dag} />],
    ['Components', (t) => t.comps],
    ['Est. cost', (t) => <span className="mono">{t.cost}</span>],
    ['Latency', (t) => t.lat],
    ['Lift vs bare', (t) => <span className="oh-badge oh-badge--lift">▲ {t.lift}</span>],
    ['Provenance', (t) => t.prov],
    ['License', (t) => <span className="mono">{t.lic}</span>],
    ['Best for', (t) => <span style={{ color: 'var(--fg-muted)' }}>{t.best}</span>],
  ];
  return (
    <div className="oh-bt-stage">
      <div className="oh-bt-head">
        <h3>Costed options — comparison matrix</h3>
        <div className="s">Attribute-aligned for side-by-side scanning · est. bands until live pricing</div>
      </div>
      <table className="oh-cmp-table">
        <thead>
          <tr>
            <th className="rowlbl"></th>
            {TIERS.map((t) => (
              <th key={t.tier} className={t.rec ? 'col-rec' : ''}>
                {t.tier}
                {t.rec && <span className="recflag">★ recommended</span>}
                {!t.rec && <span className="tier-cost">{t.cost}</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, render]) => (
            <tr key={label}>
              <td className="rowlbl">{label}</td>
              {TIERS.map((t) => (
                <td key={t.tier} className={t.rec ? 'col-rec' : ''}>{render(t)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ===== STUDY 2 — recommendation-forward hero ===== */
function ResultsHero() {
  const stages = [
    ['input', 'Supplier (1 row)', 18],
    ['conditional', 'High-risk tier gate', 12],
    ['knowledge', 'CSDDD corpus (rag)', 42],
    ['action', 'Cite-first ESG counsel', 70],
    ['output', 'Graded dossier', 22],
  ];
  return (
    <div className="oh-rf-stage">
      <div className="oh-bt-head">
        <h3>Costed options — recommendation-forward</h3>
        <div className="s">Lead with Balanced; cheap &amp; quality stay one click away</div>
      </div>
      <div className="oh-rf-body">
        <div className="oh-rf-hero">
          <div className="toprow">
            <span className="oh-rec-badge">Recommended</span>
            <span className="tier">Balanced</span>
            <span style={{ flex: 1 }} />
            <span className="oh-badge oh-badge--lift">▲ +0.41 lift</span>
            <span className="oh-badge mono">$$ est. mid</span>
          </div>
          <div className="oh-rf-flow">
            <Strip dag={TIERS[1].dag} />
          </div>
          <div className="oh-rf-stages">
            {stages.map(([k, nm, w]) => (
              <div className="oh-rf-srow" key={nm}>
                <span className="pdot" style={{ background: `var(${PRIMS[k].v})` }} />
                <span className="nm">{nm}</span>
                <span className="bar"><i style={{ width: w + '%' }} /></span>
                <span className="ct">{Math.round(w / 10)}¢</span>
              </div>
            ))}
          </div>
          <button className="oh-btn oh-btn--primary" style={{ justifyContent: 'center' }}>Open flow →</button>
        </div>
        <div className="oh-rf-aside">
          {[TIERS[0], TIERS[2], TIERS[3]].map((t) => (
            <div className="oh-rf-alt" key={t.tier}>
              <div className="t"><b>{t.tier}</b><Strip dag={t.dag} /></div>
              <div className="meta">
                <span>{t.comps} comp</span>
                <span className="mono">{t.cost}</span>
                <span className="oh-badge oh-badge--lift" style={{ padding: '2px 7px' }}>▲ {t.lift}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ===== STUDY 3 — budget / quality dial ===== */
function ResultsDial() {
  return (
    <div className="oh-dial-stage">
      <div className="oh-bt-head">
        <h3>Costed options — budget &amp; quality dial</h3>
        <div className="s">Pick a target; the flow re-prices and re-assembles live</div>
      </div>
      <div className="oh-dial-body">
        <div className="oh-dial-controls">
          <div className="oh-dial-presets">
            <div className="oh-preset"><div className="pn">Cheap</div><div className="pc">$ · +0.21</div></div>
            <div className="oh-preset on"><div className="pn">Balanced</div><div className="pc">$$ · +0.41</div></div>
            <div className="oh-preset"><div className="pn">Quality</div><div className="pc">$$$ · +0.55</div></div>
          </div>
          <div className="oh-slider">
            <div className="srow"><span>Budget ceiling</span><span className="mono" style={{ color: 'var(--fg)' }}>$$ / run</span></div>
            <div className="oh-track"><i style={{ width: '52%' }} /><span className="knob" style={{ left: '52%' }} /></div>
          </div>
          <div className="oh-slider">
            <div className="srow"><span>Quality target</span><span className="mono" style={{ color: 'var(--fg)' }}>+0.41 lift</span></div>
            <div className="oh-track"><i style={{ width: '64%' }} /><span className="knob" style={{ left: '64%' }} /></div>
          </div>
          <div className="oh-curve">
            <div className="oh-pal-lbl" style={{ marginBottom: 8 }}>Cost ↔ lift tradeoff</div>
            <svg width="100%" height="86" viewBox="0 0 300 86" preserveAspectRatio="none">
              <polyline points="6,78 70,52 140,33 210,22 294,16" fill="none" stroke="var(--accent)" strokeWidth="2" />
              <circle cx="140" cy="33" r="5" fill="var(--accent)" stroke="var(--panel)" strokeWidth="2" />
            </svg>
          </div>
        </div>
        <div className="oh-dial-readout">
          <div className="big">Resulting flow</div>
          <div className="oh-readout-flow"><Strip dag={TIERS[1].dag} /></div>
          <div className="oh-statline"><span className="lbl" style={{ color: 'var(--fg-muted)' }}>Components</span><span className="val" style={{ fontWeight: 600 }}>6</span></div>
          <div className="oh-statline"><span className="lbl" style={{ color: 'var(--fg-muted)' }}>Est. cost</span><span className="mono" style={{ color: 'var(--fg)' }}>$$ est. mid</span></div>
          <div className="oh-statline"><span className="lbl" style={{ color: 'var(--fg-muted)' }}>Lift</span><span className="oh-badge oh-badge--lift">▲ +0.41</span></div>
          <button className="oh-btn oh-btn--primary" style={{ justifyContent: 'center' }}>Open flow →</button>
        </div>
      </div>
    </div>
  );
}

/* ===== DIAGRAM STUDY A — vertical flow ===== */
function VNode({ k, p, n, id, lift }) {
  return (
    <div className="oh-vnode" style={{ ['--nodehue']: `var(${PRIMS[k].v})` }}>
      <span className="gly">{PRIMS[k].glyph}</span>
      <span className="vt">
        <div className="vp">{PRIMS[k].label}</div>
        <div className="vn">{n}</div>
        <div className="vid">{id}</div>
      </span>
      {lift && <span className="vlift">▲ {lift}</span>}
    </div>
  );
}
function DagVertical() {
  return (
    <div className="oh-vstage">
      <div className="oh-bt-head"><h3>Flow — vertical (trace-ready)</h3><div className="s">Top-down; collapses cleanly to mobile &amp; the run log</div></div>
      <div className="oh-vflow">
        <VNode k="input" n="Supplier (1 row)" id="inputs/supplier-roster" />
        <span className="oh-vconn" />
        <VNode k="conditional" n="High-risk tier gate" id="conditional/tier-risk-gate" />
        <span className="oh-vconn" />
        <VNode k="knowledge" n="CSDDD article corpus" id="knowledge-corpus/csddd-articles" lift="+0.18" />
        <span className="oh-vconn" />
        <VNode k="action" n="Cite-first ESG counsel" id="harness/esg-cite-first" lift="+0.41" />
        <span className="oh-vconn" />
        <span className="oh-vop">↻ Review &amp; refine</span>
        <span className="oh-vconn" />
        <VNode k="output" n="Graded supplier dossier" id="outputs/csddd-dossier" />
      </div>
    </div>
  );
}

/* ===== DIAGRAM STUDY B — linear / subway ===== */
function Stop({ k, n, id, op }) {
  return (
    <div className="oh-sub-stop">
      <span className={'oh-sub-bullet' + (op ? ' op' : '')} style={!op ? { ['--nodehue']: `var(${PRIMS[k].v})`, borderColor: `var(${PRIMS[k].v})`, color: `var(${PRIMS[k].v})` } : null}>
        <span>{op ? '◇' : PRIMS[k].glyph}</span>
      </span>
      <span className="oh-sub-lab">{n}{id && <small>{id}</small>}</span>
    </div>
  );
}
function DagSubway() {
  return (
    <div className="oh-sub-stage">
      <div className="oh-bt-head"><h3>Flow — linear “subway”</h3><div className="s">Compact overview; branches merge at operator stops</div></div>
      <div className="oh-sub-body">
        <div className="oh-sub-line">
          <Stop k="input" n="Input" id="supplier-roster" />
          <span className="oh-sub-rail" />
          <Stop k="conditional" n="Conditional" id="tier-risk-gate" />
          <span className="oh-sub-rail" />
          <Stop op n="OR" />
          <span className="oh-sub-rail" />
          <Stop k="knowledge" n="Knowledge" id="csddd-articles" />
          <span className="oh-sub-rail" />
          <Stop k="action" n="Harness" id="esg-cite-first" />
          <span className="oh-sub-rail" />
          <Stop k="output" n="Output" id="csddd-dossier" />
        </div>
        <div className="oh-sub-branch">
          <Stop k="conditional" n="AML rule-pack" id="aml-screen" />
          <span className="oh-sub-rail" />
          <Stop k="knowledge" n="Sanctions list" id="ofac-sdn" />
        </div>
      </div>
    </div>
  );
}

/* ===== DIAGRAM STUDY C — run / trace audit log ===== */
function TraceRow({ step, k, ref1, ref2, model, tokens, cost, ms, status }) {
  return (
    <div className="oh-trace-row" style={{ ['--nodehue']: `var(${PRIMS[k].v})` }}>
      <span className="step">{step}</span>
      <span className="prim"><span className="pd" style={{ background: `var(${PRIMS[k].v})` }} /><span className="pl">{PRIMS[k].label}</span></span>
      <span className="ref">{ref1} {model && <span className="modelflag">model</span>} <small>{ref2}</small></span>
      <span className="mono">{tokens}</span>
      <span className="mono">{cost}</span>
      <span className={'mono ' + (status === 'sim' ? 'sim' : 'ok')}>{status === 'sim' ? '◌ sim' : '✓ ' + ms}</span>
    </div>
  );
}
function RunTrace() {
  return (
    <div className="oh-trace-stage">
      <div className="oh-trace-hd">
        <h3>Run trace</h3>
        <div className="oh-trace-tot">
          <div className="t"><div className="v">$0.0312</div><div className="k">est. cost</div></div>
          <div className="t"><div className="v">8.4k</div><div className="k">tokens</div></div>
          <div className="t"><div className="v">13.9s</div><div className="k">wall</div></div>
          <div className="t"><div className="v">11</div><div className="k">citations</div></div>
        </div>
      </div>
      <div className="oh-trace-banner">◌ Simulate mode — model steps are echo-stubs until a provider key is connected.</div>
      <div className="oh-trace-list">
        <TraceRow step="01" k="input" ref1="inputs/supplier-roster" ref2="· 1.2k rows" tokens="—" cost="—" ms="4ms" status="ok" />
        <TraceRow step="02" k="knowledge" ref1="knowledge-corpus/csddd-articles" ref2="· rag_vector" tokens="2.1k" cost="$0.0021" ms="380ms" status="ok" />
        <TraceRow step="03" k="conditional" ref1="conditional/tier-risk-gate" ref2="· 4 rules" tokens="—" cost="—" ms="2ms" status="ok" />
        <TraceRow step="04" k="action" ref1="harness/esg-cite-first" ref2="· gpt-class" model tokens="5.8k" cost="$0.0279" ms="" status="sim" />
        <TraceRow step="05" k="output" ref1="outputs/csddd-dossier" ref2="· pdf + json-ld" tokens="0.5k" cost="$0.0012" ms="120ms" status="ok" />
      </div>
    </div>
  );
}

Object.assign(window, {
  ResultsTable, ResultsHero, ResultsDial,
  DagVertical, DagSubway, RunTrace,
  ComponentLibrary, BatchFlow, LiftEvidence, SystemStates,
});

/* ===== SYSTEM STATES — every state designed (§7.9) ===== */
function SystemStates() {
  return (
    <div className="oh-states-stage">
      <div className="oh-states-hd">
        <h3>System states — designed, not afterthoughts</h3>
        <div className="s">Empty · loading · blocked-by-gate · error · success — honest states for every surface</div>
      </div>
      <div className="oh-states-grid">
        <div className="oh-state">
          <span className="sh">Loading · skeleton</span>
          <div className="oh-skel-line" style={{ width: '55%' }} />
          <div className="oh-skel-line" style={{ width: '90%' }} />
          <div className="oh-skel-line" style={{ width: '70%' }} />
          <div className="oh-skel-line" style={{ width: '40%' }} />
        </div>

        <div className="oh-state">
          <span className="sh">Empty · teach next action</span>
          <div className="oh-state-empty">
            <span className="ico">⌖</span>
            <span className="t">No saved flows yet —<br />paste a task to build one.</span>
            <button className="oh-btn oh-btn--primary oh-btn--sm">Paste a task</button>
          </div>
        </div>

        <div className="oh-state">
          <span className="sh">Blocked by the lift gate</span>
          <div className="oh-state-msg blocked">
            <span className="gl">⚠</span>
            <span><b>Not promotable.</b> This component shows <span className="mono">— unproven</span> lift — it doesn't beat a bare model yet, so it can't enter a flow.</span>
          </div>
          <span className="oh-state-fix">Fix: attach a benchmark → re-measure →</span>
        </div>

        <div className="oh-state">
          <span className="sh">Blocked by provenance</span>
          <div className="oh-state-msg blocked">
            <span className="gl">⚠</span>
            <span><b>Unsourced.</b> Missing <span className="mono">source_url</span> + license. Routed to the review queue before it can be cited.</span>
          </div>
          <span className="oh-state-fix">Fix: add provenance → request review →</span>
        </div>

        <div className="oh-state">
          <span className="sh">Error · recoverable</span>
          <div className="oh-state-msg error">
            <span className="gl">⊘</span>
            <span><b>Model provider timed out.</b> The run halted at the harness call; nothing was charged.</span>
          </div>
          <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ alignSelf: 'flex-start' }}>↻ Retry step</button>
        </div>

        <div className="oh-state">
          <span className="sh">Success · toast</span>
          <div className="oh-state-toast"><span className="gl">✓</span> Flow saved · <span className="mono">flow/csddd-grade</span></div>
          <div className="oh-state-toast"><span className="gl">✓</span> Audit bundle exported</div>
        </div>
      </div>
    </div>
  );
}

/* ===== CAPABILITY-LIFT EVIDENCE — vetted components do the lift, not the bill ===== */
function LiftEvidence() {
  const attrib = [
    ['knowledge', 'CSDDD article corpus', 'knowledge-corpus/csddd-articles', '+0.18', 'free', '$0 recurring · freezable'],
    ['conditional', 'High-risk tier gate', 'conditional/tier-risk-gate', '+0.09', 'free', '$0 · deterministic'],
    ['action', 'Cite-first ESG counsel', 'harness/esg-cite-first', '+0.14', 'paid', '1 model call'],
  ];
  return (
    <div className="oh-lift-stage">
      <div className="oh-lift-hd">
        <h3>Capability lift — vetted components do the work, not the bill</h3>
        <div className="s">Where the +0.41 comes from, and how much of it costs nothing to run</div>
      </div>
      <div className="oh-lift-body">
        <div className="oh-lift-panel">
          <div className="oh-lb-row">
            <div className="oh-lb-label">Bare model <b>0.42</b></div>
            <div className="oh-lb-track"><div className="oh-lb-fill bare" style={{ width: '42%' }} /></div>
          </div>
          <div className="oh-lb-row">
            <div className="oh-lb-label">This pipeline <b>0.83</b></div>
            <div className="oh-lb-track"><div className="oh-lb-fill pipe" style={{ width: '83%' }} /></div>
          </div>
          <div className="oh-lift-delta">
            <span className="big">▲ +0.41</span>
            <span className="lbl">structural lift vs a bare model</span>
          </div>
          <div className="oh-lift-bench">measured · CSDDD supplier-grading benchmark · n=240 · gpt-class base</div>
        </div>

        <div>
          <div className="oh-lift-atthd">Where the lift comes from</div>
          {attrib.map(([k, n, id, plus, kind, cost]) => (
            <div className="oh-la-row" key={id} style={{ ['--nodehue']: `var(${PRIMS[k].v})` }}>
              <span className="oh-la-dot" />
              <span className="oh-la-nm"><div className="n">{PRIMS[k].glyph} {n}</div><div className="i">{id}</div></span>
              <span className="oh-la-plus">{plus}</span>
              <span className={'oh-la-cost ' + kind}>{cost}</span>
            </div>
          ))}
          <div className="oh-lift-callout">
            <b>+0.27 of the +0.41</b> is freezable — vetted components &amp; knowledge packs that add
            capability with <b>no recurring cost</b>. Only the single model call recurs, so you can
            lift the pipeline without lifting the bill.
          </div>
        </div>
      </div>
    </div>
  );
}

/* ===== COMPONENT LIBRARY — every component, aligned by stage ===== */
const LIB = [
  ['input', [{ n: 'Supplier roster', id: 'inputs/supplier-roster' }, { n: 'Contract PDF', id: 'inputs/contract-pdf' }, { n: 'CSV upload', id: 'inputs/csv-upload' }]],
  ['conditional', [{ n: 'Tier-risk gate', id: 'conditional/tier-risk-gate' }, { n: 'AML screen', id: 'conditional/aml-screen' }, { n: 'Renewal-risk rules', id: 'conditional/renewal-risk' }]],
  ['knowledge', [{ n: 'CSDDD articles', id: 'knowledge-corpus/csddd-articles', b: '✔ sourced', gov: 1 }, { n: 'OFAC / SDN list', id: 'knowledge-corpus/ofac-sdn', b: '⟳ fresh', gov: 1 }, { n: 'GxP SOP library', id: 'knowledge-corpus/gxp-sops' }, { n: 'Customs HS codes', id: 'knowledge-corpus/hs-codes' }]],
  ['action', [{ n: 'Cite-first ESG counsel', id: 'harness/esg-cite-first', b: '▲ +0.41' }, { n: 'PDF redactor', id: 'tool/pdf-redactor' }, { n: 'Entity resolver', id: 'processor/entity-resolver' }, { n: 'Grading rubric', id: 'rubric/supplier-grade' }, { n: 'CSDDD benchmark', id: 'benchmark/csddd-v2' }]],
  ['loop', [{ n: 'Rubric-refine', id: 'pattern/rubric-refine' }, { n: 'Research entity', id: 'pipeline/research-entity', b: '▲ +0.55' }]],
  ['stop', [{ n: 'Budget guard', id: 'guard/budget-ceiling' }, { n: 'PII stop', id: 'guard/pii-detected' }]],
  ['output', [{ n: 'Graded dossier', id: 'outputs/csddd-dossier' }, { n: 'Audit bundle', id: 'outputs/audit-pack' }, { n: 'JSON-LD export', id: 'outputs/json-ld' }]],
];
function ComponentLibrary() {
  return (
    <div className="oh-lib-stage">
      <div className="oh-lib-hd">
        <h3>Component library — aligned by stage</h3>
        <div className="s">Every component grouped by primitive, left → right in pipeline order — so you see how they wire into a flow. Counts are live.</div>
      </div>
      <div className="oh-lib-cols">
        {LIB.map(([k, items], ci) => (
          <React.Fragment key={k}>
            <div className="oh-lib-col" style={{ ['--nodehue']: `var(${PRIMS[k].v})` }}>
              <div className="oh-lib-colhd">
                <span className="oh-lib-sw">{PRIMS[k].glyph}</span>
                <span className="oh-lib-colname">{PRIMS[k].label}</span>
                <span className="oh-lib-count">{items.length}</span>
              </div>
              {items.map((it) => (
                <div className="oh-lib-chip" key={it.id}>
                  <div className="cn">{it.n}</div>
                  <div className="ci">{it.id}</div>
                  {it.b && <span className={'cb' + (it.gov ? ' gov' : '')}>{it.b}</span>}
                </div>
              ))}
            </div>
            {ci < LIB.length - 1 && <span className="oh-lib-chev">›</span>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

/* ===== BATCH — map the single-call flow over a list ===== */
function BatchFlow() {
  return (
    <div className="oh-batch-stage">
      <div className="oh-bt-head"><h3>Batch — map over a list</h3><div className="s">Iteration is a separate wrapper, not baked into the per-item flow</div></div>
      <div className="oh-batch-body">
        <div className="oh-batch-wrap">
          <div className="oh-batch-hd">
            <span className="ic">⟳</span>
            <span className="t">Map over list</span>
            <span className="meta">suppliers.csv · 1,247 rows · concurrency 8</span>
          </div>
          <div className="oh-batch-inner">
            <Strip dag={['input', 'conditional', 'op', 'knowledge', 'action', 'output']} />
          </div>
          <div className="oh-batch-foot">
            <span>per item <b>1 model call</b></span>
            <span>est. cost <b>$$ × 1,247</b></span>
            <span>lift <b>+0.41</b> each</span>
          </div>
        </div>
        <div className="oh-batch-note">
          The unit of work stays the <b>single-call flow</b>. Batch runs it once per row with its own
          concurrency, retry &amp; cost rollup — so cost, lift and provenance remain attributable to one call.
        </div>
      </div>
    </div>
  );
}
