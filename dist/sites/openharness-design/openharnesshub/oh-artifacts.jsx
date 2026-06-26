/* global React */
// OpenHubForAI — the four canonical artifacts, authored once.
// Content is identical across directions (fair comparison); only the
// scope class on the wrapper (set in app.jsx) changes the design language.

const PRIMS = {
  input:       { label: 'Input',            glyph: '⌖', v: '--p-input' },
  knowledge:   { label: 'Knowledge Corpus', glyph: '⛁', v: '--p-knowledge' },
  conditional: { label: 'Conditional',      glyph: '◈', v: '--p-conditional' },
  action:      { label: 'Action',           glyph: '⚡', v: '--p-action' },
  loop:        { label: 'Loop / Flow',      glyph: '↻', v: '--p-loop' },
  stop:        { label: 'Stop / End',       glyph: '⊘', v: '--p-stop' },
  output:      { label: 'Output',           glyph: '⎘', v: '--p-output' },
};
const OPERATOR = { label: 'Operator', glyph: '◇', v: '--operator' };

const hue = (v) => ({ ['--nodehue']: `var(${v})` });

// ── tiny mark used in the wordmark (a node/operator glyph; no gradient) ──
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

function Wordmark() {
  return (
    <div className="oh-wordmark"><Mark /> OpenHubForAI</div>
  );
}

/* ============================================================
   ① LANDING — the entry box
   ============================================================ */
function Landing() {
  const chips = [
    'grade suppliers against CSDDD',
    'triage 311 reports',
    'review a contract for renewal risk',
    'redact a PDF',
  ];
  return (
    <div className="oh-mkt">
      <header className="oh-topbar">
        <Wordmark />
        <nav className="oh-nav">
          <a>Browse</a><a>Pricing</a><a>Docs</a><a>How it works</a>
        </nav>
        <div className="oh-topbar-spacer" />
        <a className="oh-btn oh-btn--ghost oh-btn--sm">Sign in</a>
        <a className="oh-btn oh-btn--primary oh-btn--sm">Build</a>
      </header>

      <section className="oh-hero">
        <h1 className="oh-hero-title">Describe a task.<br />Lift the pipeline, not the bill.</h1>
        <p className="oh-hero-sub">
          Assembled from vetted components and knowledge packs that measurably lift capability —
          most of it deterministic and freezable, so you add capability without adding cost.
        </p>

        <div className="oh-entrybox">
          <div className="oh-entry-text">
            Grade a supplier list against CSDDD due-diligence obligations, cite the articles, flag high-risk tiers…
          </div>
          <div className="oh-entry-row">
            <div className="oh-entry-tools">
              <span className="oh-constraint-add">+ Add constraints</span>
            </div>
            <button className="oh-btn oh-btn--primary">
              Build <span style={{ fontSize: 12, fontWeight: 600, opacity: .7, letterSpacing: '.02em' }}>⌘ Enter</span>
            </button>
          </div>
        </div>

        <div className="oh-chips">
          {chips.map((c) => (
            <span className="oh-chip" key={c}><span className="tri">▸</span>{c}</span>
          ))}
        </div>

        <div className="oh-quietlinks">
          <a>Browse the catalog</a><span className="dot">·</span>
          <a>Sign in</a><span className="dot">·</span>
          <a>How it works</a>
        </div>
      </section>

      <div className="oh-howstrip">
        {['Paste', 'Retrieve', 'Assemble', 'Measure lift', 'Deploy'].map((s, i, a) => (
          <React.Fragment key={s}>
            <span className="step"><b>{s}</b></span>
            {i < a.length - 1 && <span className="arr">→</span>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

/* ============================================================
   ② BUILDER RESULTS — three costed options
   ============================================================ */
function MiniNode({ k, op }) {
  if (op) return <span className="oh-mininode is-op">◇</span>;
  const p = PRIMS[k];
  return <span className="oh-mininode" style={{ background: `var(${p.v})` }}>{p.glyph}</span>;
}
function MiniDag({ nodes }) {
  return (
    <div className="oh-minidag">
      {nodes.map((n, i) => (
        <React.Fragment key={i}>
          <MiniNode k={n} op={n === 'op'} />
          {i < nodes.length - 1 && <span className="oh-miniedge" />}
        </React.Fragment>
      ))}
    </div>
  );
}
function ResultCard({ tier, rec, dag, lift, comps, packs, gov, cost, latency, freeze }) {
  return (
    <div className={'oh-result' + (rec ? ' oh-result--rec' : '')}>
      <div className="oh-result-tierrow">
        <span className={'oh-tier' + (rec ? ' oh-tier--rec' : '')}>{tier}</span>
        {rec && <span className="oh-rec-badge">Recommended</span>}
      </div>
      <MiniDag nodes={dag} />
      <div className="oh-result-lift">
        <span className="big">▲ {lift}</span>
        <span className="sub">capability lift vs a bare model</span>
      </div>
      <div className="oh-result-src">{comps} · <b>{packs}</b> doing the lift</div>
      <div className="oh-cc-badges">
        <span className="oh-badge oh-badge--verified"><span className="gl">✔</span> {gov}</span>
      </div>
      <div className="oh-result-cost">
        <span className="mono">{cost} · {latency}</span>
        <span className="freeze">{freeze}</span>
      </div>
      <button className={'oh-btn ' + (rec ? 'oh-btn--primary' : 'oh-btn--ghost')} style={{ justifyContent: 'center' }}>Open flow</button>
    </div>
  );
}
function BuilderResults() {
  return (
    <div className="oh-app">
      <div className="oh-appbar">
        <Wordmark />
        <div className="oh-cmdk"><span>⌕</span> Search components, flows, runs…<span className="oh-kbd">⌘K</span></div>
      </div>
      <div className="oh-results-head">
        <h2>Three flows for this task</h2>
        <div className="task">Each adds vetted components &amp; knowledge for more lift — cost barely moves, because most lift is <span className="mono">freezable</span> (zero recurring)</div>
      </div>
      <div className="oh-results-grid">
        <ResultCard tier="Cheap"
          dag={['input', 'knowledge', 'action', 'output']}
          lift="+0.21" comps="4 components" packs="1 knowledge pack"
          gov="keyword · MIT" cost="$ est. low" latency="~6s" freeze="~80% freezable" />
        <ResultCard tier="Balanced" rec
          dag={['input', 'conditional', 'op', 'knowledge', 'action', 'output']}
          lift="+0.41" comps="6 components" packs="2 knowledge · 1 conditional"
          gov="sourced · MIT" cost="$$ est. mid" latency="~14s" freeze="~65% freezable" />
        <ResultCard tier="Quality-first"
          dag={['input', 'conditional', 'op', 'knowledge', 'action', 'loop', 'output']}
          lift="+0.55" comps="9 components" packs="3 knowledge · 2 conditional"
          gov="verified · CC-BY" cost="$$$ est. high" latency="~38s" freeze="~55% freezable" />
      </div>
    </div>
  );
}

/* ============================================================
   ③ COMPONENT CARD + BADGE SYSTEM
   ============================================================ */
function ComponentCard() {
  return (
    <div className="oh-card-stage">
      <div className="stage-head">
        <h3>Component card</h3>
        <span>the most-repeated unit · lift · governance · cost</span>
      </div>

      <div className="oh-comp-card" style={hue(PRIMS.action.v)}>
        <div className="oh-cc-top">
          <span className="oh-execdot" style={{ background: 'var(--accent)' }} title="code-executing" />
          <span className="oh-cc-prim">⚡ Action <span className="sub">· harness</span></span>
          <span className="spacer" />
          <span className="oh-badge oh-badge--lift">▲ +0.41 lift</span>
          <span className="oh-cc-kebab">⋯</span>
        </div>
        <h4 className="oh-cc-name">Cite-first ESG counsel</h4>
        <div className="oh-cc-id mono">harness/esg-cite-first <span className="copy">⧉</span></div>
        <p className="oh-cc-desc">Holds a deterministic citation gate before the model answers, so every CSDDD claim resolves to a sourced article across 13 languages.</p>
        <div className="oh-cc-divider" />
        <div className="oh-cc-badges">
          <span className="oh-badge oh-badge--verified"><span className="gl">✔</span> sourced</span>
          <span className="oh-badge oh-badge--stable"><span className="gl">◆</span> stable</span>
          <span className="oh-badge"><span className="gl">⛁</span> rag</span>
          <span className="oh-badge"><span className="oh-execdot" style={{ background: 'var(--accent)' }} /> code</span>
          <span className="oh-badge mono">$$ balanced</span>
          <span className="oh-badge mono">MIT</span>
        </div>
      </div>

      <div className="oh-badgesys">
        <div className="grp">
          <span className="gh">Lift</span>
          <div className="row">
            <span className="oh-badge oh-badge--lift">▲ +0.41</span>
            <span className="oh-badge oh-badge--lift">▲ structural</span>
            <span className="oh-badge oh-badge--muted">— unproven</span>
          </div>
        </div>
        <div className="grp">
          <span className="gh">Provenance</span>
          <div className="row">
            <span className="oh-badge oh-badge--verified"><span className="gl">✔</span> sourced</span>
            <span className="oh-badge oh-badge--warn"><span className="gl">⚠</span> unsourced</span>
            <span className="oh-badge oh-badge--verified"><span className="gl">🛡</span> verified</span>
          </div>
        </div>
        <div className="grp">
          <span className="gh">Lifecycle</span>
          <div className="row">
            <span className="oh-badge">◷ abstract</span>
            <span className="oh-badge">◐ experimental</span>
            <span className="oh-badge">◑ beta</span>
            <span className="oh-badge oh-badge--stable">◆ stable</span>
          </div>
        </div>
        <div className="grp">
          <span className="gh">Cost band</span>
          <div className="row">
            <span className="oh-badge mono">$ cheap</span>
            <span className="oh-badge mono">$$ balanced</span>
            <span className="oh-badge mono">$$$ quality</span>
            <span className="oh-badge mono">⌂ local</span>
          </div>
        </div>
        <div className="grp">
          <span className="gh">Execution class</span>
          <div className="row">
            <span className="oh-badge"><span className="oh-execdot" style={{ background: 'var(--fg-muted)' }} /> static</span>
            <span className="oh-badge"><span className="oh-execdot" style={{ background: 'var(--info)' }} /> text-op</span>
            <span className="oh-badge"><span className="oh-execdot" style={{ background: 'var(--accent)' }} /> code</span>
          </div>
        </div>
        <div className="grp">
          <span className="gh">Freshness · License</span>
          <div className="row">
            <span className="oh-badge oh-badge--lift">⟳ fresh</span>
            <span className="oh-badge oh-badge--warn">⟳ stale</span>
            <span className="oh-badge oh-badge--danger">⊘ revoked</span>
            <span className="oh-badge mono">CC-BY-4.0</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   ④ DAG CANVAS + LEGEND + OPERATOR
   ============================================================ */
function LegendBar() {
  return (
    <div className="oh-legend-bar">
      <span className="lt">Primitives</span>
      {Object.entries(PRIMS).map(([k, p]) => (
        <span className="oh-legend-chip" key={k} title={p.label}>
          <span className="sw" style={{ background: `var(${p.v})` }}>{p.glyph}</span>{p.label}
        </span>
      ))}
      <span className="oh-legend-chip is-op" title="Logical Operator — OR / AND">
        <span className="sw">◇</span>Operator
      </span>
    </div>
  );
}
// ── Wired flow viewer (NOT a DAG — supports the per-item refine loop) ──
// Stage order per product owner: Input → Conditional (IF) → Knowledge → Action → Loop → Output
const FW = 198, FH = 84;
const FR = (n) => ({ x: n.x + FW, y: n.y + FH / 2 });
const FL = (n) => ({ x: n.x, y: n.y + FH / 2 });
const FB = (n) => ({ x: n.x + FW / 2, y: n.y + FH });
const bez = (a, b) => {
  const dx = Math.max(26, Math.abs(b.x - a.x) * 0.5);
  return `M${a.x},${a.y} C${a.x + dx},${a.y} ${b.x - dx},${b.y} ${b.x},${b.y}`;
};

const FN = {
  input: { x: 14, y: 176, k: 'input', name: 'Supplier (1 row)', ref: 'inputs/supplier-roster', facts: '⌖ one item / iteration' },
  ct: { x: 240, y: 64, k: 'conditional', lift: null, name: 'High-risk tier gate', ref: 'conditional/tier-risk-gate', facts: '◈ rule-pack · tier ≥ 2 → review' },
  ca: { x: 240, y: 300, k: 'conditional', name: 'AML / sanctions screen', ref: 'conditional/aml-screen', facts: '◈ rule-pack · match → block' },
  kc: { x: 580, y: 176, k: 'knowledge', lift: '+0.18', name: 'CSDDD article corpus', ref: 'knowledge-corpus/csddd-articles', facts: '⛁ rag · static · 13 langs · ✔' },
  act: { x: 806, y: 176, k: 'action', lift: '+0.41', name: 'Cite-first ESG counsel', ref: 'harness/esg-cite-first', facts: '⚡ harness · 1 call · ● code' },
  ev: { x: 1032, y: 176, k: 'loop', name: 'Review & refine', ref: 'pattern/rubric-refine', facts: '↻ pattern · until rubric ≥ 0.8' },
  out: { x: 1258, y: 176, k: 'output', name: 'Graded dossier', ref: 'outputs/csddd-dossier', facts: '⎘ pdf+json-ld · ✓ cited' },
};
const OP = { x: 466, y: 198, w: 84, h: 40 };
const opL = { x: OP.x, y: OP.y + OP.h / 2 };
const opR = { x: OP.x + OP.w, y: OP.y + OP.h / 2 };

function FNode({ n }) {
  const p = PRIMS[n.k];
  return (
    <div className="oh-fnode" style={{ left: n.x, top: n.y, ...hue(p.v) }}>
      <div className="ftop">
        <span className="fp">{p.glyph} {p.label}</span>
        <span className="fsp" />
        {n.lift && <span className="flift">▲ {n.lift}</span>}
      </div>
      <div className="fn">{n.name}</div>
      <div className="fid">{n.ref}</div>
      <div className="ff">{n.facts}</div>
    </div>
  );
}

function FlowCanvas() {
  const fwd = [
    [FR(FN.input), FL(FN.ct)], [FR(FN.input), FL(FN.ca)],
    [FR(FN.ct), opL], [FR(FN.ca), opL],
    [opR, FL(FN.kc)], [FR(FN.kc), FL(FN.act)], [FR(FN.act), FL(FN.ev)],
  ];
  const evB = FB(FN.ev), actB = FB(FN.act);
  const loopPath = `M${evB.x},${evB.y} C${evB.x},${evB.y + 62} ${actB.x},${actB.y + 62} ${actB.x},${actB.y}`;
  const dot = (pt, i) => <circle key={i} cx={pt.x} cy={pt.y} r="3" fill="var(--bg-subtle)" stroke="var(--fg-faint)" strokeWidth="1.25" />;
  return (
    <div className="oh-canvas-stage">
      <LegendBar />
      <div className="oh-flow">
        <svg className="oh-flow-svg">
          <defs>
            <marker id="ah" markerWidth="9" markerHeight="9" refX="6.5" refY="3" orient="auto" markerUnits="userSpaceOnUse">
              <path d="M0,0 L7,3 L0,6 Z" fill="context-stroke" />
            </marker>
          </defs>
          <g fill="none" stroke="var(--fg-faint)" strokeWidth="1.5" markerEnd="url(#ah)" opacity="0.85">
            {fwd.map((e, i) => <path key={i} d={bez(e[0], e[1])} />)}
          </g>
          <path d={bez(FR(FN.ev), FL(FN.out))} fill="none" stroke="var(--success)" strokeWidth="1.6" markerEnd="url(#ah)" />
          <path d={loopPath} fill="none" stroke="var(--p-loop)" strokeWidth="1.75" strokeDasharray="5 3" markerEnd="url(#ah)" />
          {[FR(FN.input), opR, FR(FN.kc), FR(FN.act), FR(FN.ev)].map(dot)}
        </svg>

        <FNode n={FN.input} /><FNode n={FN.ct} /><FNode n={FN.ca} />
        <div className="oh-fop" style={{ left: OP.x, top: OP.y, width: OP.w, height: OP.h }}>◇ OR</div>
        <FNode n={FN.kc} /><FNode n={FN.act} /><FNode n={FN.ev} /><FNode n={FN.out} />

        <span className="oh-fcall" style={{ left: FN.act.x + FW / 2, top: FN.act.y - 24, transform: 'translateX(-50%)' }}>1 model call / item</span>
        <span className="oh-flbl loop" style={{ left: (evB.x + actB.x) / 2, top: evB.y + 48 }}>↻ refine · same call ×N</span>
        <span className="oh-flbl pass" style={{ left: (FN.ev.x + FW + FN.out.x) / 2, top: FN.ev.y - 12 }}>pass ▸</span>

        <div className="oh-validity">
          <span>✓</span> Single-call pattern — Conditional (IF) routes first, then Knowledge feeds one harness call per item; the refine loop re-runs that call until the rubric passes. Batch maps this flow across a list.
        </div>
      </div>
    </div>
  );
}
const DagCanvas = FlowCanvas;

Object.assign(window, { Landing, BuilderResults, ComponentCard, FlowCanvas, DagCanvas, PRIMS });
