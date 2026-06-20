/* global React, PageHead, MarketingTop, Footer */
// Baltor — "How it works" engine page. The animated context-engine pipeline,
// adapted into Baltor's design system (tokens, light/dark) from the standalone mockup.

const ENG_STAGES = [
  { key: 'source', n: '00', name: 'Source', sub: 'Raw ingress', tone: 'var(--fg-faint)',
    copy: 'Captures organizational knowledge exactly where it lives — preserving timestamps, permissions, content hashes and expandable source handles.',
    detail: 'Jira comments, Confluence pages, code, diagrams, incidents and local memory enter with ACLs, hashes and source handles before any claim is trusted.',
    tags: ['watch changes', 'parse objects', 'preserve handles'] },
  { key: 'reconciliation', n: '01', name: 'Reconciliation', sub: 'Cluster alignment', tone: 'var(--success)',
    copy: 'Deduplicates related artifacts, maps relationships, separates comments from decisions, and surfaces contradictions across tickets, docs, code and memory.',
    detail: 'Jira says refunds clear after 30 days, an old page says 14, billing uses 21. Baltor links the evidence, picks the highest-confidence source when policy allows, or flags it for review.',
    tags: ['dedupe', 'link evidence', 'surface conflicts'] },
  { key: 'anti', n: '02', name: 'Hardening', sub: 'Robust object hardening', tone: 'var(--info)',
    copy: 'Finds facts likely to change in source systems and replaces brittle text with robust knowledge objects that refresh over time.',
    detail: 'Magic numbers, settings, thresholds and limits are treated as volatile — Baltor creates refreshable objects so a value is rechecked against the right system instead of copied into stale context.',
    tags: ['detect fragile values', 'create objects', 'refresh over time'] },
  { key: 'enhancement', n: '03', name: 'Enhancement', sub: 'Context enrichment', tone: 'var(--accent)',
    copy: 'Adds relevant external context, metadata, relationships, service-graph links and missing connective facts to make context complete.',
    detail: 'If internal sources disagree on the maximum allowable late fee, Baltor attaches verified external sources or approved tools to resolve the conflict before the pack is served.',
    tags: ['add metadata', 'connect objects', 'increase robustness'] },
  { key: 'optimization', n: '04', name: 'Optimization', sub: 'Pack shaping', tone: 'var(--violet, #8b7cf6)',
    copy: 'Summarizes, distills, converts unstructured context into structured objects, ranks relevance, and fits the result to the task budget.',
    detail: 'A 40-page policy thread, three tickets and five source handles become a 3,000-token pack: ranked claims, conflicts, tests to run, and expansion links — less token waste and fewer tool calls.',
    tags: ['summarize', 'structure', 'rank'] },
  { key: 'consumption', n: '05', name: 'Consumption', sub: 'Delivery', tone: 'var(--fg-faint)',
    copy: 'Serves task-specific packs to AI workflows and humans with controlled source-handle expansion, recording every claim, route and decision.',
    detail: 'Claude, Cursor, another context layer or a human dashboard receives the same governed pack. Each can expand approved handles while Baltor records what was served, why and under which policy.',
    tags: ['serve pack', 'expand handles', 'audit receipts'] },
];

// lightweight canvas: context objects flowing L→R, changing shape/colour per stage
function EngineCanvas() {
  const ref = React.useRef(null);
  React.useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let raf, items = [], spawn = 0, running = true;
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const cs = getComputedStyle(document.querySelector('.ce-root') || document.body);
    const tone = (v) => cs.getPropertyValue(v).trim() || v;
    const stageCols = ['--fg-faint', '--success', '--info', '--accent', '--violet', '--fg-faint'].map((v) => tone(v) || '#888');
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    function size() { const r = canvas.getBoundingClientRect(); canvas.width = Math.max(1, r.width * dpr); canvas.height = Math.max(1, r.height * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); }
    size();
    function zones(w) { const p = [.62, .98, 1.16, 1.24, .98, .62]; const tot = p.reduce((a, b) => a + b, 0); let x = 0; const o = [0]; p.forEach((q) => { x += w * q / tot; o.push(x); }); return o; }
    function rnd(a, b) { return a + Math.random() * (b - a); }
    function Item(w, h, sx) { this.x = sx == null ? -rnd(20, 160) : sx; this.y = rnd(24, h - 24); this.by = this.y; this.sp = rnd(.5, .95); this.sz = rnd(6, 11); this.seed = Math.random() * 1000; this.rot = rnd(0, 6.28); this.stage = 0; }
    Item.prototype.up = function (w, h, t) { const z = zones(w); this.x += this.sp; this.y = this.by + Math.sin(t * .002 + this.seed) * 3.5; this.rot += .016; for (let s = 1; s <= 5; s++) if (this.x > z[s]) this.stage = Math.max(this.stage, s); };
    Item.prototype.dr = function () { const c = stageCols[this.stage] || '#888'; ctx.save(); ctx.globalAlpha = this.stage < 1 ? .4 : .8; ctx.fillStyle = c; ctx.strokeStyle = c; const s = this.sz; if (this.stage < 2) { ctx.fillRect(this.x - s / 2, this.y - s / 2, s, s); } else if (this.stage < 4) { const lift = s * .5; ctx.globalAlpha *= .4; ctx.fillRect(this.x + lift - s / 2, this.y - lift - s / 2, s, s); ctx.globalAlpha /= .4; ctx.fillRect(this.x - s / 2, this.y - s / 2, s, s); } else { ctx.translate(this.x, this.y); ctx.rotate(this.rot); ctx.beginPath(); ctx.moveTo(0, -s); ctx.lineTo(s, 0); ctx.lineTo(0, s); ctx.lineTo(-s, 0); ctx.closePath(); ctx.fill(); } ctx.restore(); };
    function bg(w, h) { const z = zones(w); for (let i = 0; i < 6; i++) { ctx.fillStyle = 'rgba(127,127,127,' + (i === 0 || i === 5 ? .03 : .05) + ')'; ctx.fillRect(z[i], 0, z[i + 1] - z[i], h); if (i > 0) { ctx.strokeStyle = 'rgba(127,127,127,.18)'; ctx.setLineDash([4, 6]); ctx.beginPath(); ctx.moveTo(z[i], 0); ctx.lineTo(z[i], h); ctx.stroke(); ctx.setLineDash([]); } } }
    function frame(t) { if (!running) return; const w = canvas.width / dpr, h = canvas.height / dpr; ctx.clearRect(0, 0, w, h); bg(w, h); spawn++; if (spawn > 22 && items.length < 70) { spawn = 0; items.push(new Item(w, h)); } for (let i = items.length - 1; i >= 0; i--) { items[i].up(w, h, t); items[i].dr(); if (items[i].x > w + 60) items.splice(i, 1); } raf = requestAnimationFrame(frame); }
    const w0 = canvas.width / dpr, h0 = canvas.height / dpr; for (let i = 0; i < 34; i++) items.push(new Item(w0, h0, rnd(0, w0)));
    if (reduce) { bg(w0, h0); items.forEach((it) => { it.stage = Math.min(5, Math.floor(it.x / (w0 / 6))); it.dr(); }); }
    else frame(0);
    const onR = () => size();
    window.addEventListener('resize', onR);
    return () => { running = false; cancelAnimationFrame(raf); window.removeEventListener('resize', onR); };
  }, []);
  return <canvas ref={ref} className="ce-eng-canvas" aria-hidden="true" />;
}

function EnginePage() {
  const [hover, setHover] = React.useState(null);
  const active = ENG_STAGES.find((s) => s.key === hover);
  return (
    <div className="ce-page ce-eng-page">
      <PageHead eyebrow="How it works" title="The Baltor context lifecycle"
        sub="Continuous reconciliation, hardening, enhancement, optimization and provenance — with verification running beneath every stage." />
      <div className="oh-card ce-eng-shell">
        <div className="ce-eng-metrics">
          {[['Conflicts solved', '44'], ['Fragile facts hardened', '44'], ['Enhancements linked', '26'], ['Serving state', 'Ready']].map(([k, v]) => (
            <div className="ce-eng-metric" key={k}><span>{k}</span><b className="mono">{v}</b></div>
          ))}
        </div>
        <div className="ce-eng-canvas-wrap">
          <EngineCanvas />
          <div className="ce-eng-zonelabels">
            {ENG_STAGES.map((s) => (
              <button key={s.key} className="ce-eng-zone" onMouseEnter={() => setHover(s.key)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(s.key)} onBlur={() => setHover(null)}>
                <b style={{ color: s.tone }}>{s.name}</b><span>{s.sub}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="ce-eng-assure mono">CONTINUOUS VERIFICATION + ADVERSARIAL VALIDATION · contradictions / source precedence / fragile facts / freshness / policy</div>
      </div>

      <div className="oh-card ce-eng-detail">
        <div className="ed-title"><b>{active ? active.name : 'Stage details'}</b><span>{active ? active.sub : 'Hover a stage above to see a concrete example.'}</span></div>
        <div className="ed-copy">{active ? active.detail : 'Move over any stage to see what Baltor reconciles, hardens, enriches, optimizes, or serves at that step.'}</div>
        <div className="ed-tags">{(active ? active.tags : ['hover stages', 'examples', 'benefits', 'controls']).map((t) => <span key={t}>{t}</span>)}</div>
      </div>

      <div className="ce-rails" style={{ marginTop: 18 }}>
        {ENG_STAGES.map((s) => (
          <div className="oh-card ce-rail" key={s.key} style={{ borderLeftColor: s.tone }}>
            <div className="ce-rail-num" style={{ color: s.tone, borderColor: 'color-mix(in srgb, ' + s.tone + ' 40%, var(--line))', background: 'color-mix(in srgb, ' + s.tone + ' 12%, transparent)' }}>{s.n}</div>
            <div className="ce-rail-title"><b>{s.name}</b><span>{s.sub}</span></div>
            <div className="ce-rail-copy">{s.copy}</div>
            <div className="ce-rail-tags">{s.tags.map((t) => <span key={t} style={{ color: s.tone, borderColor: 'color-mix(in srgb, ' + s.tone + ' 30%, var(--line))' }}>{t}</span>)}</div>
          </div>
        ))}
        <div className="ce-rail-foot"><b>Universal verification layer:</b> continuous verification and adversarial interrogation runs below every stage — checking contradictions, source precedence, freshness windows and policy.</div>
      </div>
    </div>
  );
}

function EngineMarketing() {
  return (
    <div className="ce-landing">
      <MarketingTop />
      <div className="ce-wrap" style={{ paddingTop: 28 }}>
        <EnginePage />
      </div>
      <Footer />
    </div>
  );
}

Object.assign(window, { EnginePage, EngineMarketing });
