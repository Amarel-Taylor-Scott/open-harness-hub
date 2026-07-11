/* global React, navigate, MarketingTop, SupportedBy, Meter, BRANDCE, TIER_META, tierFill, CONFLICTS */
// Context Enrichment — Landing (marketing). Standalone brand, north-star story.

function HeroDiagram() {
  // the core idea, visualized: ONE corpus — reconciled, hardened, enhanced, optimized
  return (
    <div className="oh-card ce-herodiag">
      <div className="ce-hd-top">
        <div className="ce-hd-one">
          <span className="lbl">ONE CORPUS</span>
          <span className="nm">Acme Compliance Policies</span>
        </div>
        <span className="ce-hd-live"><span className="dot" />continuously verified</span>
      </div>
      <div className="ce-hd-check"><span className="i">✔</span><span>fact-checked against <strong>5 live sources</strong> · 0 stale claims · checked 40s ago</span></div>
      <div className="ce-hd-ops-list">
        {[
          ['Reconciled', 'Found and remedied conflicting information'],
          ['Anti-fragile', 'Replaced fragile info with robust objects'],
          ['Enhanced', 'Added public and specialized context'],
          ['Optimized', 'Shaped to reduce token consumption'],
        ].map(([op, desc]) => (
          <div className="ce-hd-opln" key={op}>
            <span className="ce-hd-opck">✔</span>
            <span className="ce-hd-opnm">{op}</span>
            <span className="ce-hd-opds">{desc}</span>
          </div>
        ))}
      </div>
      <div className="ce-hd-foot">
        <span className="mono">served → any agent</span>
        <span className="ce-hd-arrow">every claim cited ✔</span>
      </div>
    </div>
  );
}

function Hero() {
  const hooks = BRANDCE.hooks || [];
  const ctas = BRANDCE.ctas || [];
  const [, { track }] = window.useExperiment('baltor_hero', hooks.map((x) => x.id));
  // Canonical hero copy. The inline A/B variant picker (Headline A-I / Subhead A-E / CTA A-D)
  // was retired 2026-06-27 — Baltor is a real product, not a variant gallery. Show the locked
  // hook / subhead / CTA, sourced from products.js (BRANDCE).
  const h = hooks.find((x) => (x.lead + ' ' + x.tint) === BRANDCE.hook) || hooks[0];
  const subText = BRANDCE.subhead;
  const ctaLabel = (ctas[0] || {}).label || 'Connect a source →';
  const startCta = () => { track('cta_click', { cta: 'primary', label: ctaLabel, where: 'hero' }); navigate('/ingest'); };
  return (
    <section className="ce-hero">
      <div className="ce-wrap ce-hero-grid">
        <div>
          <div className="ce-eyebrow">{BRANDCE.mission}</div>
          <h1>{h.lead}<br /><span className="tinted">{h.tint}</span></h1>
          <p>{subText} {BRANDCE.name} keeps it correct, current and lean —
            connect your own sources or subscribe to verified corpora, and serve trusted
            context to Claude Code or any agent.</p>
          <div className="ce-soul">{BRANDCE.soul}</div>
          <div className="ce-cta">
            <button className="oh-btn oh-btn--primary" onClick={startCta}>{ctaLabel}</button>
            <button className="oh-btn oh-btn--ghost" onClick={() => { track('see_engine', { where: 'hero' }); const el = document.getElementById('how'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }}>See how it works</button>
          </div>
          <div className="ce-trust">
            {BRANDCE.pillars.map((p, i) => (
              <span key={p} className={'oh-badge' + (i === 0 ? ' oh-badge--verified' : '')}>{i === 0 ? '✔ ' : ''}{p}</span>
            ))}
          </div>
        </div>
        <HeroDiagram />
      </div>
    </section>
  );
}

const STAGES = [
  ['01', '⇄', 'Reconciliation', 'Dedupes artifacts, links evidence, separates comments from decisions, and surfaces contradictions across tickets, docs, code & memory.'],
  ['02', '◳', 'Hardening', 'Finds facts likely to change and replaces brittle text with robust knowledge objects that refresh over time.'],
  ['03', '✚', 'Enhancement', 'Adds external context, metadata, relationships and missing connective facts to make context complete.'],
  ['04', '◇', 'Optimization', 'Summarizes, structures and ranks — fitting the result to the task budget for fewer tokens and tool calls.'],
];
const RAILS = [
  ['01', 'Reconciliation', 'Cluster alignment', 'Deduplicates related artifacts, maps relationships, identifies comments-versus-decisions, and surfaces contradictions across tickets, docs, code, and memory.', ['dedupe', 'link evidence', 'surface conflicts']],
  ['02', 'Hardening', 'Robust object hardening', 'Finds facts likely to change in source systems and replaces brittle text with robust knowledge objects that can update over time.', ['detect fragile values', 'create objects', 'refresh over time']],
  ['03', 'Enhancement', 'Context enrichment', 'Adds relevant external context objects, metadata, relationships, architecture/service-graph links, event/schema facts, and missing connective context.', ['add metadata', 'connect objects', 'increase robustness']],
  ['04', 'Optimization', 'Pack shaping', 'Summarizes, distills, converts unstructured context into structured objects, ranks relevance, and fits the result to the task budget.', ['summarize', 'structure', 'rank']],
];
function How() {
  return (
    <section className="ce-block" id="how">
      <div className="ce-wrap">
        <h2 className="ce-section-h">The context lifecycle</h2>
        <p className="ce-engine-lede">{BRANDCE.name} isn’t a corpus you browse, and it isn’t retrieval — it’s a governance
          layer that <strong>hardens</strong> raw organizational knowledge into trustworthy, task-ready context: reconciled,
          made anti-fragile, enhanced and optimized, with continuous verification and signed provenance beneath every stage.</p>
        <div className="ce-spine ce-spine--4eng">
          {STAGES.map(([n, g, h, p, star]) => (
            <div className={'ce-stage' + (star ? ' star' : '')} key={n}>
              <span className="n">{n}{star && <em className="core">core</em>}</span><div className="chip">{g}</div>
              <h4>{h}</h4><p>{p}</p><span className="arrow">→</span>
            </div>
          ))}
        </div>
        <div className="ce-rails">
          {RAILS.map(([n, t, sub, copy, tags]) => (
            <div className="oh-card ce-rail" key={n}>
              <div className="ce-rail-num">{n}</div>
              <div className="ce-rail-title"><b>{t}</b><span>{sub}</span></div>
              <div className="ce-rail-copy">{copy}</div>
              <div className="ce-rail-tags">{tags.map((tg) => <span key={tg}>{tg}</span>)}</div>
            </div>
          ))}
          <div className="ce-rail-foot"><b>Universal verification layer:</b> continuous verification and adversarial interrogation runs below every stage — checking contradictions, source precedence, freshness windows, and policy.</div>
        </div>
      </div>
    </section>
  );
}

function VerifyMoat() {
  const c = CONFLICTS[0];
  return (
    <section className="ce-block" id="verify">
      <div className="ce-wrap ce-moat">
        <div className="ce-moat-copy">
          <div className="ce-eyebrow">Why it’s different</div>
          <h2>Not retrieval. Context governance.</h2>
          <p>
            Most tools just retrieve from your documents. {BRANDCE.name} governs context across its
            whole lifecycle — a four-stage pipeline that makes it correct, current, lean and provable,
            not just whatever got fetched.
          </p>
          <ul className="ce-moat-list ce-moat-stages">
            <li><b>Reconciliation</b><span>Dedupes, links evidence and resolves contradictions across tickets, docs, code and memory.</span></li>
            <li><b>Hardening</b><span>Turns brittle facts — thresholds, limits, magic numbers — into objects that refresh instead of going stale.</span></li>
            <li><b>Enhancement</b><span>Enriches with metadata, relationships and verified external sources to make context complete.</span></li>
            <li><b>Optimization</b><span>Distills, structures and ranks the result to fit the task budget — fewer tokens, fewer tool calls.</span></li>
          </ul>
          <button className="oh-btn oh-btn--primary" onClick={() => navigate('/engine')}>See how it works →</button>
        </div>
        <div className="ce-moat-card">
          <div className="cf-top"><div className="cf-meta"><span className="oh-badge oh-badge--danger">High</span><span className="oh-badge">Superseded</span></div><span className="cf-detected mono">detected {c.detected}</span></div>
          <div className="cf-claim">“{c.claim}”</div>
          <div className="cf-diff">
            <div className="cf-side internal"><div className="lbl">Internal corpus</div><div className="val">{c.internal}</div></div>
            <span className="cf-arrow">→</span>
            <div className="cf-side external"><div className="lbl">Live authoritative source</div><div className="val">{c.external}</div><div className="src mono">{c.source}</div></div>
          </div>
          <div className="cf-foot"><span className="cf-conf mono">confidence {Math.round(c.confidence * 100)}%</span><span className="oh-badge oh-badge--warn">escalated to human</span></div>
        </div>
      </div>
    </section>
  );
}

const TIERS = [
  { k: 'raw', name: 'Raw', sub: 'Full fidelity — every token preserved, with source spans for audit & re-processing.',
    fidelity: 'Lossless', tokens: '1.0×', use: 'Audit trails, re-processing, anything that must reproduce the source exactly.' },
  { k: 'compressed', name: 'Compressed', sub: 'Redundancy removed, normalized to a clean schema — near-full fidelity.',
    fidelity: 'Near-full', tokens: '0.4×', use: 'The everyday default for hosting and general-purpose serving.' },
  { k: 'hyper', name: 'Hyper-efficient', sub: 'Claim-level, citation-anchored and token-minimal — distilled for live agents.',
    fidelity: 'Task-tuned', tokens: '0.06×', use: 'Live agent context windows where every token (and millisecond) counts.', feat: true },
];
function Tiers() {
  return (
    <section className="ce-block" id="tiers">
      <div className="ce-wrap">
        <h2 className="ce-section-h">One corpus · three tiers</h2>
        <div className="ce-tiers">
          {TIERS.map((t) => (
            <div className={'oh-card ce-tier' + (t.feat ? ' feat' : '')} key={t.k}>
              <div className="th">
                <span className="tname"><span className="ce-tierdot" style={{ background: TIER_META[t.k].tone }} />{t.name}</span>
                {t.feat && <span className="oh-badge oh-badge--verified">agent-ready</span>}
              </div>
              <div className="tsub">{t.sub}</div>
              <Meter pct={tierFill[t.k]} tone={TIER_META[t.k].tone} />
              <div className="mlabel"><span>relative size</span><span>{tierFill[t.k]}%</span></div>
              <div className="stat"><span className="k">Fidelity</span><span className="v">{t.fidelity}</span></div>
              <div className="stat"><span className="k">Tokens / query</span><span className="v">{t.tokens}</span></div>
              <div className="use">{t.use}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Serve() {
  return (
    <section className="ce-block">
      <div className="ce-wrap">
        <div className="oh-card ce-serve">
          <div>
            <h3>Serve to agents like Claude Code</h3>
            <p>
              One endpoint per corpus. Agents request the tier they need; every
              response is citation-anchored and provenance-stamped — so what your model
              reads is always verified, and always traceable to a source you approved.
            </p>
            <div className="ce-trust">
              <span className="oh-badge oh-badge--verified">✔ every answer cited</span>
              <span className="oh-badge mono">versioned freshness</span>
            </div>
            <div style={{ marginTop: 18 }}>
              <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/serve')}>Open the serve console →</button>
            </div>
          </div>
          <div className="ce-code">
            <div><span className="c"># serve the hyper-efficient tier to an agent</span></div>
            <div><span className="k">GET</span> /v1/corpora/<span className="s">acme-policy</span>/serve</div>
            <div>&nbsp;&nbsp;?tier=<span className="s">hyper-efficient</span></div>
            <div>&nbsp;&nbsp;&amp;cite=<span className="s">true</span></div>
            <div style={{ marginTop: 10 }}><span className="c"># → verified context + citations, token-lean</span></div>
          </div>
        </div>
      </div>
    </section>
  );
}

function CTABand() {
  return (
    <section className="ce-ctaband">
      <div className="ce-wrap">
        <h2>Give your agents context they can cite.</h2>
        <div className="ce-cta">
          <button className="oh-btn oh-btn--primary" onClick={() => navigate('/ingest')}>Ingest your first source →</button>
          <button className="oh-btn oh-btn--ghost" onClick={() => navigate('/corpora')}>See example corpora</button>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="ce-foot">
      <div className="ce-wrap ce-foot-grid">
        <div>
          <div className="ce-logo" style={{ marginBottom: 10 }}>
            <span className="ce-logo-name" style={{ fontSize: 17 }}>{BRANDCE.wordmark || BRANDCE.name}</span>
          </div>
          <a className="ce-foot-mission" href={BRANDCE.missionHome || '../context-is-everything/Context is Everything.html'}>{BRANDCE.mission} ↗</a>
          <SupportedBy block />
        </div>
        <div className="ce-foot-links">
          <a onClick={() => navigate('/why')}>Why us</a>
          <a onClick={() => navigate('/cases')}>Case studies</a>
          <a onClick={() => navigate('/commons')}>Commons</a>
          <a onClick={() => navigate('/verify')}>Verify</a>
          <a onClick={() => navigate('/governance')}>Governance</a>
        </div>
      </div>
    </footer>
  );
}

function CommonsBand() {
  return (
    <section className="ce-block" id="commons">
      <div className="ce-wrap">
        <h2 className="ce-section-h">An oracle-published commons</h2>
        <div className="ce-commons-band">
          <div className="cb-copy">
            <h3>Corpora signed by the bodies that own the truth.</h3>
            <p>
              Governments, UN agencies and standards bodies publish signed, continuously-verified
              corpora — for the regulated and social-impact domains commercial marketplaces skip:
              forced labor &amp; migrant rights, AML, food &amp; water safety, customs. Subscribe one
              into your workspace and serve it to your agents.
            </p>
            <button className="oh-btn oh-btn--primary" onClick={() => navigate('/commons')}>Browse the commons →</button>
          </div>
          <div className="cb-pubs">
            {['ILO', 'US DOL', 'FATF', 'EC', 'Codex', 'WCO'].map((s) => <span className="cb-pub" key={s}>{s}</span>)}
          </div>
        </div>
      </div>
    </section>
  );
}

// Landing section orderings. The shipped layout is `default` (Balanced); the baltor_landing
// A/B re-sequencing experiment was retired 2026-06-27. Kept as data so the order lives in one place.
const LANDING_LAYOUTS = {
  default: { label: 'Balanced', order: ['How', 'VerifyMoat', 'CommonsBand', 'Tiers', 'Serve'] },
  engine:  { label: 'Engine-first', order: ['VerifyMoat', 'How', 'Tiers', 'CommonsBand', 'Serve'] },
  problem: { label: 'Problem-first', order: ['VerifyMoat', 'Serve', 'How', 'CommonsBand', 'Tiers'] },
  proof:   { label: 'Proof-first', order: ['CommonsBand', 'VerifyMoat', 'How', 'Serve', 'Tiers'] },
};
function Landing() {
  const SECTIONS = { How, VerifyMoat, CommonsBand, Tiers, Serve };
  // Fixed production layout. The baltor_landing A/B experiment and its floating OhExperimentsPanel
  // were retired 2026-06-27 — Baltor is a real product, with no visible A/B machinery.
  const plan = LANDING_LAYOUTS.default;
  return (
    <div className="ce-landing">
      <MarketingTop />
      <Hero />
      {plan.order.map((name) => { const S = SECTIONS[name]; return S ? <S key={name} /> : null; })}
      <CTABand />
      <Footer />
    </div>
  );
}

const WHY_CARDS = [
  ['vs Contextual AI', 'They ground the answer in your corpus — even if the corpus is wrong. We verify the corpus.'],
  ['vs raw RAG', 'Retrieval without verification is confident wrongness. We add the assurance layer.'],
  ['vs hand-maintaining it', 'Stop hand-maintaining regulatory corpora. Subscribe to verified, always-current truth.'],
];
// fair matrix — Contextual is genuinely strong where it's strong; we differ on the assurance axes
const WHY_ROWS = [
  ['Grounded answers (RAG quality)', ['part', 'via your agent'], ['yes', 'best-in-class'], ['yes', 'yes'], ['part', 'hand-built']],
  ['Verifies the corpus vs source of truth', ['yes', 'core'], ['no', 'not offered'], ['no', 'no'], ['part', 'manual']],
  ['Continuous freshness · regulatory diff', ['yes', 'live'], ['part', 'sync only'], ['no', 'no'], ['part', 'manual']],
  ['Signed provenance · verify by hash', ['yes', 'C2PA-style'], ['no', '—'], ['no', '—'], ['no', '—']],
  ['Compliance artifacts (AIBOM · EU AI Act)', ['yes', 'emitted'], ['part', 'answer citations'], ['no', '—'], ['part', 'DIY']],
  ['Oracle-published shared corpora', ['yes', 'commons'], ['part', 'demo-only'], ['no', '—'], ['no', '—']],
  ['Serves into the agent you already run', ['yes', 'neutral'], ['part', 'build on us'], ['yes', 'yes'], ['yes', 'yes']],
];
const WHY_COLS = [BRANDCE.name, 'Contextual AI', 'Raw RAG', 'DIY'];
const WHY_MARK = { yes: '●', part: '◐', no: '—' };
function WhyPage() {
  return (
    <div className="ce-landing">
      <MarketingTop />
      <section className="ce-hero" style={{ paddingBottom: 8 }}>
        <div className="ce-wrap">
          <div className="ce-eyebrow">Why {BRANDCE.name}</div>
          <h1 style={{ maxWidth: '18ch' }}>Current isn’t the same as <span className="tinted">correct</span>.</h1>
          <p style={{ maxWidth: '62ch' }}>
            Most platforms just retrieve, and at best check your docs are <em>current</em>.
            {' '}{BRANDCE.name} runs a four-stage engine — <strong>reconciliation</strong>,
            {' '}<strong>hardening</strong>, <strong>enhancement</strong> and
            {' '}<strong>optimization</strong> — that makes context <strong>correct</strong> against
            the source of truth, proves it with signed provenance, and serves it into the agent you
            already run. Verification is one stage of four.
          </p>
        </div>
      </section>
      <section className="ce-block">
        <div className="ce-wrap">
          <div className="ce-why-cards">
            {WHY_CARDS.map(([h, p]) => (
              <div className="oh-card ce-why-card" key={h}><div className="wc-h">{h}</div><div className="wc-p">{p}</div></div>
            ))}
          </div>
        </div>
      </section>
      <section className="ce-block">
        <div className="ce-wrap">
          <h2 className="ce-section-h">Where we differ</h2>
          <div className="ce-why-tablewrap">
            <table className="ce-why-table">
              <thead>
                <tr>
                  <th></th>
                  {WHY_COLS.map((c, i) => <th key={c} className={i === 0 ? 'ce-col' : ''}>{c}</th>)}
                </tr>
              </thead>
              <tbody>
                {WHY_ROWS.map(([label, ...cells]) => (
                  <tr key={label}>
                    <td className="wt-dim">{label}</td>
                    {cells.map(([m, txt], i) => (
                      <td key={i} className={(i === 0 ? 'ce-col ' : '') + 'wt-cell'}>
                        <span className={'wt-m m-' + m}>{WHY_MARK[m]}</span>
                        <span className="wt-txt">{txt}</span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="ce-why-foot mono">We don’t compete on the builder, actions, or model — that ground is contested. We compete on verified context and openness.</div>
        </div>
      </section>
      <CTABand />
      <Footer />
    </div>
  );
}

Object.assign(window, { Landing, WhyPage, Footer });
