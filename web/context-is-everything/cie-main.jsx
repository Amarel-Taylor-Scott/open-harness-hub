/* global React, ReactDOM, PRODUCTS, BRAND, PORTFOLIO */
// AI Done Right — the holding-company / portfolio site.
// Two layers: governed products (Baltor, Teleon) on an open resource foundation
// (Context / Skills / Tools / Harness hubs).

const { GROUP, ENTITIES, LAYERS, PORTS } = PORTFOLIO;
const E = (id) => ENTITIES[id];

function Mark({ s = 26 }) {
  // three converging strata → a single point of trust (the family mark)
  return (
    <svg className="cie-logo-mk" viewBox="0 0 24 24" width={s} height={s} aria-hidden="true">
      <rect x="3" y="4.5" width="18" height="3" rx="1.5" fill="var(--cie-blue)" />
      <rect x="5.5" y="10.5" width="13" height="3" rx="1.5" fill="var(--cie-baltor)" />
      <rect x="8" y="16.5" width="8" height="3" rx="1.5" fill="var(--cie-ohh)" />
    </svg>
  );
}

function Top({ theme, onToggle }) {
  return (
    <header className="cie-top">
      <a className="cie-logo" href="#top"><Mark /><span className="cie-logo-name">{GROUP.short}</span></a>
      <span className="cie-spacer" />
      <nav className="cie-top-nav">
        <a href="#thesis">Thesis</a>
        <a href="#architecture">Architecture</a>
        <a href="#portfolio">Portfolio</a>
        <a href="#proof">Proof</a>
        <a href="#fit">How it fits</a>
        <a href="Demo Control Tower.html">Demo</a>
      </nav>
      <button className="cie-theme-toggle" onClick={onToggle} aria-label="Toggle light or dark theme" title="Toggle light / dark">
        {theme === 'dark' ? '☀' : '☾'}
      </button>
    </header>
  );
}

function Hero() {
  return (
    <section className="cie-hero" id="top">
      <div className="cie-wrap cie-hero-grid">
        <div>
          <div className="cie-eyebrow">{GROUP.kind}</div>
          <h1>AI,<br /><span className="tint-blue">done right.</span></h1>
          <p className="cie-lede">
            {GROUP.name} builds the platform that makes AI capability trustworthy — governed
            runtimes and context assurance at the core, fed by an open ecosystem of registries.
            Models commoditize; <strong>governed capability is the moat</strong>.
          </p>
          <div className="cie-cta">
            <a className="cie-btn" style={{ background: 'var(--cie-blue)', color: '#fff' }} href="#portfolio">See the platform →</a>
            <a className="cie-btn cie-btn-ghost" href="#architecture">How it works</a>
          </div>
        </div>
        <div className="cie-hero-aside">
          {LAYERS.map((layer) => (
            <div className="cha-layer" key={layer.id}>
              <span className="cha-label">{layer.label}</span>
              <div className="cha-chips">
                {layer.items.map((id) => {
                  const e = E(id);
                  return <span className="cha-chip" key={id} style={{ '--ent': e.accent }}><span className="g">{e.glyph}</span>{e.name}</span>;
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const FAILS = [
  ['Stale', 'A regulation changed two weeks ago. The agent still acts on the old number.'],
  ['Unverified', 'Pulled confidently from a source nobody checked against the truth.'],
  ['Ungoverned', 'A skill, tool or model adopted on a README — discovery mistaken for trust.'],
  ['Unproven', 'A candidate promoted on a hunch, with no evidence gate and no way to roll back.'],
];
function Problem() {
  return (
    <section className="cie-section" id="thesis">
      <div className="cie-wrap">
        <div className="cie-kicker">The thesis</div>
        <h2>Usually it’s not the model. It’s everything around it.</h2>
        <div className="cie-body">
          As models commoditize, the bottleneck moves to everything that feeds and runs them —
          <strong> context, skills, tools, runtimes and evidence</strong>. Capability fails in four
          ways no amount of model quality can fix, and every one is a governance problem:
        </div>
        <div className="cie-fail">
          {FAILS.map(([h, p]) => (
            <div className="oh-card oh-card--pad cie-failcard" key={h}>
              <div className="fc-x">✕</div><h4>{h}</h4><p>{p}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Architecture() {
  return (
    <section className="cie-section" id="architecture">
      <div className="cie-wrap">
        <div className="cie-kicker">The architecture · the capability lifecycle</div>
        <h2>Purpose in. Evidence-gated capability out.</h2>
        <div className="cie-body">
          Every capability in the group moves through one spine. Nothing is promoted on a
          hunch — a candidate ships only when the evidence clears its eval gate, and rolls
          back when it doesn’t.
        </div>
        <ol className="cie-flow">
          {GROUP.flow.map((step, i) => (
            <li className="cie-flow-step" key={step}>
              <span className="n">{String(i + 1).padStart(2, '0')}</span>
              <span className="lbl">{step}</span>
              {i < GROUP.flow.length - 1 && <span className="arr">→</span>}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function EntityCard({ id, compact }) {
  const e = E(id);
  const live = e.status === 'live';
  const Tag = e.url ? 'a' : 'div';
  return (
    <Tag className={'oh-card cie-ent' + (e.url ? ' linkable' : '') + (compact ? ' compact' : '')}
      href={e.url || undefined} style={{ '--ent': e.accent }}>
      <div className="ent-top">
        <span className="ent-glyph">{e.glyph}</span>
        <span className={'ent-status s-' + e.status}>{e.status}</span>
      </div>
      <div className="ent-name">{e.wordmark}</div>
      <div className="ent-kind">{e.kind}</div>
      {!compact && <p className="ent-blurb">{e.blurb}</p>}
      <span className="ent-go">{live ? 'Visit site →' : e.status === 'private' ? 'Private preview →' : e.status === 'building' ? 'In progress' : 'Planned'}</span>
    </Tag>
  );
}

function Portfolio() {
  return (
    <section className="cie-section" id="portfolio">
      <div className="cie-wrap">
        <div className="cie-kicker">The portfolio · one stack, two layers</div>
        <h2>Governed products, on an open foundation.</h2>
        <div className="cie-stack">
          {LAYERS.map((layer) => (
            <div className={'cie-layer l-' + layer.id} key={layer.id}>
              <div className="cie-layer-side">
                <div className="cie-layer-label">{layer.label}</div>
                <div className="cie-layer-sub">{layer.sub}</div>
              </div>
              <div className={'cie-layer-cards' + (layer.items.length > 1 ? ' multi' : '')}>
                {layer.items.map((id) => <EntityCard key={id} id={id} compact={layer.items.length > 1} />)}
              </div>
            </div>
          ))}
          <div className="cie-stack-flow" aria-hidden="true">
            <span>consumes ↑</span><span>serves ↓</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function Proof() {
  const CASES = (typeof window !== 'undefined' && window.CASES) || {};
  const picks = [
    ['baltor', E('baltor')],
    ['teleon', E('teleon')],
    ['openharnesshub', E('openHarnessHub')],
  ].map(([key, ent]) => ({ key, ent, c: (CASES[key] || [])[0] })).filter((x) => x.c && x.ent);
  if (!picks.length) return null;
  return (
    <section className="cie-section" id="proof">
      <div className="cie-wrap">
        <div className="cie-kicker">Proof · across the portfolio</div>
        <h2>What the family ships, in production.</h2>
        <div className="cie-proof-grid">
          {picks.map(({ key, ent, c }) => (
            <a className="cie-proof-card" key={key} href={ent.url + '#/cases/' + c.id} style={{ '--ent': ent.accent }}>
              <div className="cie-proof-brand">{ent.wordmark || ent.name}</div>
              <div className="cie-proof-sector">{c.sector}</div>
              <div className="cie-proof-title">{c.title}</div>
              <div className="cie-proof-metric"><span className="v">{c.metrics[0][0]}</span><span className="k">{c.metrics[0][1]}</span></div>
              <span className="cie-proof-go">Read case study →</span>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItFits() {
  return (
    <section className="cie-section" id="fit">
      <div className="cie-wrap">
        <div className="cie-kicker">How it fits</div>
        <h2>Clean ports between every layer.</h2>
        <div className="cie-ports">
          {PORTS.map((p) => (
            <div className="oh-card oh-card--pad cie-port" key={p.from + p.to}>
              <div className="port-flow">
                <span className="port-node" style={{ '--ent': E(p.from).accent }}>{E(p.from).wordmark}</span>
                <span className="port-arrow">→</span>
                <span className="port-node" style={{ '--ent': E(p.to).accent }}>{E(p.to).wordmark}</span>
              </div>
              <p className="port-label">{p.label}</p>
            </div>
          ))}
        </div>
        <div className="cie-join">
          Teleon <strong>runs and evolves</strong> capabilities; products <strong>consume</strong> it
          through ports and stay the source of truth. The open hubs <strong>supply</strong> the
          context, skills, tools and harnesses it all draws from.
        </div>
      </div>
    </section>
  );
}

function Band() {
  return (
    <section className="cie-band">
      <div className="cie-wrap">
        <h2>AI, done right. We build the platform that makes it trustworthy.</h2>
        <p>Explore the products that are live today.</p>
        <div className="cie-cta">
          <a className="cie-btn" style={{ background: 'var(--cie-baltor)', color: '#fff' }} href={E('baltor').url}>Visit Baltor.ai →</a>
          <a className="cie-btn" style={{ background: 'var(--cie-ohh)', color: '#fff' }} href={E('openHarnessHub').url}>Visit OpenHarnessHub →</a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  const cols = [
    ['Products', ['baltor', 'teleon']],
    ['Open resources', ['openContextHub', 'openSkillsHub', 'openToolsHub', 'openHarnessHub']],
  ];
  return (
    <footer className="cie-foot">
      <div className="cie-wrap cie-foot-grid">
        <div>
          <div className="cie-logo" style={{ marginBottom: 8 }}><Mark s={22} /><span className="cie-foot-name">{GROUP.short}</span></div>
          <div className="cie-foot-tag">{GROUP.name} · {GROUP.domain}</div>
        </div>
        <div className="cie-foot-cols">
          {cols.map(([h, ids]) => (
            <div className="cie-foot-col" key={h}>
              <h5>{h}</h5>
              {ids.map((id) => {
                const e = E(id);
                return e.url
                  ? <a key={id} href={e.url}>{e.wordmark} ↗</a>
                  : <span key={id} className="cie-foot-soon">{e.wordmark}<i>{e.status}</i></span>;
              })}
            </div>
          ))}
        </div>
      </div>
    </footer>
  );
}

function App() {
  const [theme, setTheme] = React.useState(() => {
    try { const s = localStorage.getItem('cie-theme'); if (s === 'light' || s === 'dark') return s; } catch (e) {}
    return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
  });
  React.useEffect(() => { try { localStorage.setItem('cie-theme', theme); } catch (e) {} }, [theme]);
  const toggle = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  return (
    <div className={'oh dir-s theme-' + theme + ' cie'}
      style={{ '--cie-baltor': E('baltor').accent, '--cie-ohh': E('openHarnessHub').accent }}>
      <Top theme={theme} onToggle={toggle} />
      <Hero /><Problem /><Architecture /><Portfolio /><Proof /><HowItFits /><Band /><Footer />
    </div>
  );
}
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
