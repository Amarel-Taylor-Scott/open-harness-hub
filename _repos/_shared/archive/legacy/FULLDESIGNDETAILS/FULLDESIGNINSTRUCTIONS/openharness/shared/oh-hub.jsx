/* global React, navigate, useHashRoute, useSiteTheme,
   OhTopBar, OhHero, OhSection, OhFeatures, OhBand, OhFooter,
   OhAppShell, OhPageHead, OhRollup, OhAuth, OhBilling, OhUsage, OhSettings, OhSwitch */
// shared/oh-hub.jsx — generic OPEN-REGISTRY site, shared by the three Open*Hubs
// (Context / Skills / Tools). Each hub is just a CONFIG object; this renders the
// whole site (landing + browse graph + entry detail + primitive pages) on the kit.
//
// hub config shape:
//   { brand:{name,tld,glyph,accent}, noun, nounPlural, tagline, lede,
//     features:[[g,t,d]…], facets:[…], entries:[{id,name,by,facet,desc,installs,score,deps?}],
//     footerExtra?:[[heading,[[label,href]…]]…] }

function makeHub(cfg) {
  const B = cfg.brand;
  const ACCENT = B.accent;
  // stable pseudo-hash for an entry id → realistic-looking signature/log ids on the detail page.
  const shortHash = (s, n) => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = (h * 0x01000193) >>> 0; } return h.toString(16).padStart(8, '0').slice(0, n || 8); };
  // map a 0–5 eval score → an OpenSSF-Scorecard-style /10 risk score.
  const scorecard = (score) => { const n = parseFloat(score) || 4.5; return Math.min(10, Math.max(6.5, n / 5 * 10)).toFixed(1); };
  // per-entry provenance & trust rows — the supply-chain attestations made concrete.
  // cfg.trust(e) can override per hub (e.g. MCP adds a conformance row); else this default.
  const trustRows = (e) => (cfg.trust ? cfg.trust(e, { shortHash, scorecard }) : [
    ['Signature', 'cosign ✓', true],
    ['Provenance', 'SLSA L3', true],
    ['Attestation', 'in-toto ✓', true],
    ['Risk · Scorecard', scorecard(e.score) + ' / 10', true],
    ['AI-BOM', 'CycloneDX ✓', true],
  ]);
  const rootCls = (theme) => 'oh dir-s theme-' + theme + ' oh-site ohub' + (cfg.access === 'private' ? ' ohub-private' : '');
  // private-first candidate hubs render a pre-launch banner (gated on cfg.access).
  const PRIVATE = cfg.access === 'private';
  function PrivateBanner() {
    return (
      <div className="ohub-pribanner" role="note">
        <span className="ohub-pribadge">⊘ Private preview</span>
        <span className="ohub-pritext">Built &amp; verified, not yet public{cfg.openTrigger ? <> — opens when {cfg.openTrigger}</> : null}. Internal candidate · discovery ≠ trust.</span>
      </div>
    );
  }
  // optional extra app routes, config-gated (other hubs pass none → unchanged).
  // each: { path, navLabel, navIcon?, nav?:bool, group?, render(helpers)→node }
  const EXTRA = cfg.extraRoutes || [];
  // helpers handed to bespoke renderers so site-folder pages compose the same primitives
  // (signatures, scorecards, trust rows) without forking the hub.
  const HELPERS = { navigate, brand: B, cfg, shortHash, scorecard, trustRows };
  const MKT_NAV = [['How it works', '/'], ['Browse', '/browse'], ['Cases', '/cases'], ['Docs', '/docs'], ['Pricing', '/pricing']];
  const APP_NAV = [
    ['/dashboard', '▤', 'Dashboard'],
    ...(cfg.convert ? [['/convert', cfg.brand.glyph || '⇋', cfg.convert.navLabel || 'Convert']] : []),
    ['/browse', '⬡', 'Browse'],
    ...EXTRA.filter((r) => r.nav !== false).map((r) => [r.path, r.navIcon || '▭', r.navLabel]),
    ['/installed', '▦', 'Installed'],
    ['/publish', '↥', 'Publish'],
    ['/keys', '⚿', 'API keys'],
    ['/team', '○', 'Team'],
    ['/audit', '⚖', 'Audit'],
    ['/notifications', '◉', 'Inbox'],
    ['/billing', '◷', 'Billing'],
  ];
  // ⌘K command palette commands — nav + key destinations + browseable entries
  const HUB_CMDS = [
    ...OhCommandK.fromNav(APP_NAV),
    { label: 'Home', href: '/', icon: '⌂', group: 'Marketing' },
    { label: 'Pricing', href: '/pricing', icon: '◷', group: 'Marketing' },
    { label: 'Case studies', href: '/cases', icon: '★', group: 'Marketing' },
    { label: 'About', href: '/about', icon: 'ⓘ', group: 'Marketing' },
    { label: 'Docs', href: '/docs', icon: '▭', group: 'Marketing' },
    ...EXTRA.map((r) => ({ label: r.navLabel, href: r.path, icon: r.navIcon || '▭', group: r.group || 'Developers' })),
    { label: 'Settings', href: '/settings', icon: '⚙', group: 'Account' },
    ...cfg.entries.map((e) => ({ label: e.name, href: '/e/' + e.id, icon: cfg.brand.glyph || '⬡', group: cfg.kind })),
  ];

  // ---------- marketing ----------
  function HubHeroCard() {
    const e = cfg.entries[0];
    return (
      <div className="oh-card ohub-herocard">
        <div className="hhc-head"><span className="hhc-eyebrow">{cfg.noun}</span><span className="oh-badge oh-badge--verified oh-badge--sm">✔ verified</span></div>
        <div className="hhc-name">{e.name}</div>
        <div className="hhc-by mono">by {e.by}</div>
        <p className="hhc-desc">{e.desc}</p>
        <div className="hhc-foot"><span className="mono">{e.installs} installs</span><span className="hhc-score">★ {e.score}</span></div>
      </div>
    );
  }

  function Landing({ theme, onToggle }) {
    const SecHow = (
      <OhSection id="how" label="How it works" title={cfg.howTitle} body={cfg.howBody} key="how">
        <OhFeatures items={cfg.features} />
      </OhSection>
    );
    const SecTrust = (
      <OhSection label="Open & governed" title="Open to use. Governed to trust." key="trust"
        body={<>Every {cfg.noun} is open, versioned and evaluated — with provenance you can audit. Pull what you need into
          your agents or into <strong>Teleon</strong>; publish your own for the ecosystem to build on.</>}>
        <div className="ohub-trust">
          {[['◷', 'Versioned', 'Every entry is semver-pinned with a changelog.'], ['✓', 'Evaluated', 'Scored against shared eval packs before it ships.'], ['⛨', 'Provenance', 'Signed origin you can verify by hash.']].map(([g, t, d]) => (
            <div className="oh-card oh-card--pad ohub-trustcard" key={t}><span className="ti">{g}</span><div className="tt">{t}</div><div className="td">{d}</div></div>
          ))}
        </div>
      </OhSection>
    );
    const layoutKey = B.name.toLowerCase() + '_landing';
    const [layout] = useExperiment(layoutKey, ['default', 'trust-first']);
    const body = layout === 'trust-first' ? [SecTrust, SecHow] : [SecHow, SecTrust];
    // "Built on open standards" — the OSS supply-chain stack each hub implements.
    // cfg.standards: [[name, what-it-does]…]; falls back to the shared default (accurate for all).
    const standards = cfg.standards || [
      ['Sigstore', 'keyless signing + transparency log — every entry’s signed receipt'],
      ['SLSA + in-toto', 'verifiable provenance attestations for how an entry was produced'],
      ['CycloneDX AI-BOM', 'a bill of materials for each AI artifact (OWASP)'],
      ['OpenSSF Scorecard', 'automated risk scoring — discovery is not trust'],
      ['JSON Schema', 'every entry validates against a published schema'],
      ['SemVer', 'semantic versioning, pinned with a changelog'],
    ];
    const SecStandards = (
      <OhSection label="Open standards" title="Built on the open supply-chain stack." key="standards"
        body={<>{B.name} doesn’t reinvent trust — it applies the same Linux Foundation / OpenSSF / OWASP
          standards that secure software supply chains to {cfg.nounPlural}. Provenance, signing, risk and a
          bill-of-materials are open and verifiable, not a black box.</>}>
        <div className="ohub-standards">
          {standards.map(([n, d]) => (
            <div className="oh-card ohub-std" key={n}><div className="sn mono">{n}</div><div className="sd">{d}</div></div>
          ))}
        </div>
      </OhSection>
    );
    body.push(SecStandards);
    // optional subhead A/B — active only if the config supplies ledeVariants
    const ledeVariants = cfg.ledeVariants;
    const [subV] = useExperiment(B.name.toLowerCase() + '_subhead', ledeVariants ? Object.keys(ledeVariants) : ['A']);
    const lede = ledeVariants ? (ledeVariants[subV] || cfg.lede) : cfg.lede;
    return (
      <div className={rootCls(theme)} style={{ '--accent': ACCENT }}>
        {PRIVATE && <PrivateBanner />}
        <OhTopBar brand={B} nav={MKT_NAV} cta={{ label: 'Start free', href: '/signup' }} signInHref="/signin" theme={theme} onToggle={onToggle} />
        <OhHero eyebrow={cfg.kind} title={cfg.heroTitle} lede={lede}
          ctas={cfg.convert
            ? [{ label: cfg.convert.cta || ('Convert ' + cfg.indefinite + ' →'), href: '/convert', primary: true }, { label: 'Browse ' + cfg.nounPlural, href: '/browse' }]
            : [{ label: 'Browse ' + cfg.nounPlural + ' →', href: '/browse', primary: true }, { label: 'Publish ' + cfg.indefinite, href: '/publish' }]}
          aside={<HubHeroCard />} />
        {body}
        <OhBand title={'Build on the open ' + cfg.noun + ' graph.'} sub={'Browse what exists, or publish ' + cfg.indefinite + ' the ecosystem can use.'}
          ctas={[{ label: 'Browse ' + cfg.nounPlural + ' →', href: '/browse', primary: true }, { label: 'Read the docs', href: '/docs' }]} />
        <OhFooter brand={B} tagline={cfg.kind + ' · part of ' + ((typeof window !== 'undefined' && window.PORTFOLIO && window.PORTFOLIO.GROUP.short) || 'AI Done Right')} cols={[
          ['Registry', [['Browse', '/browse'], ['Publish', '/publish'], ['Pricing', '/pricing'], ['Case studies', '/cases']]],
          ['Developers', [['Docs', '/docs'], ['Quickstart', '/docs']]],
          ['Company', [['About', '/about'], ['Contact', '/contact'], ['Status', '/status'], ['Changelog', '/changelog'], ['Sign in', '/signin']]],
          ['Legal', [['Terms', '/terms'], ['Privacy', '/privacy']]],
          ['Group', [['AI Done Right ↗', '../context-is-everything/Context is Everything.html'], ['Teleon.dev ↗', '../teleon/Teleon Prototype.html'], ['Baltor.ai ↗', '../context-enrichment/Context Enrichment Prototype.html']]],
        ]} />
        <OhExperimentsPanel />
      </div>
    );
  }

  // ---------- browse (the graph) ----------
  function Browse() {
    const [facet, setFacet] = React.useState('All');
    const [q, setQ] = React.useState('');
    const list = cfg.entries.filter((e) => (facet === 'All' || e.facet === facet) && (!q || (e.name + e.by + e.desc).toLowerCase().includes(q.toLowerCase())));
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow="Registry" title={'Browse ' + cfg.nounPlural}
          sub={'Open, versioned, evaluated ' + cfg.nounPlural + ' — pull any into your agents or Teleon.'}
          actions={<button className="oh-btn oh-btn--primary" onClick={() => navigate('/publish')}>↥ Publish</button>} />
        <div className="ohub-browsebar">
          <input className="oh-input" placeholder={'Search ' + cfg.nounPlural + '…'} value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="ohub-facets">
            {['All', ...cfg.facets].map((f) => <button key={f} className={'ohub-facet' + (facet === f ? ' on' : '')} onClick={() => setFacet(f)}>{f}</button>)}
          </div>
        </div>
        <div className="ohub-grid">
          {list.map((e) => (
            <div className="oh-card oh-card--interactive ohub-card" key={e.id} onClick={() => navigate('/e/' + e.id)}>
              <div className="ec-top"><span className="ec-facet">{e.facet}</span><span className="ec-score mono">★ {e.score}</span></div>
              <h3>{e.name}</h3>
              <div className="ec-by mono">by {e.by}</div>
              <p className="ec-desc">{e.desc}</p>
              <div className="ec-foot mono">{e.installs} installs · v{e.ver || '1.2.0'}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  function EntryDetail({ id }) {
    const e = cfg.entries.find((x) => x.id === id);
    if (!e) return <SimplePage title="Not found" sub="That entry doesn’t exist." note="Browse the registry to find one." />;
    return (
      <div className="ohs-page">
        <a className="ohub-back" onClick={() => navigate('/browse')}>← Browse</a>
        <div className="ohub-detail-head">
          <div>
            <div className="ohs-eyebrow">{cfg.noun} · {e.facet}</div>
            <h1>{e.name}</h1>
            <div className="ec-by mono">by {e.by} · v{e.ver || '1.2.0'}</div>
            <p>{e.desc}</p>
            <div className="ohub-trustrow">
              <span className="oh-badge oh-badge--verified">✔ verified</span>
              <span className="oh-badge mono">★ {e.score} eval</span>
              <span className="oh-badge mono">{e.installs} installs</span>
            </div>
          </div>
          <div className="ohub-detail-actions">
            <button className="oh-btn oh-btn--primary">+ Add to workspace</button>
            <button className="oh-btn oh-btn--ghost">Use in Teleon</button>
          </div>
        </div>
        <div className="ohub-detail-grid">
          <div className="ohub-detail-main">
            <div className="oh-card oh-card--pad ohub-install">
              <div className="ohs-eyebrow" style={{ marginBottom: 8 }}>Install</div>
              <pre className="ohub-code">{cfg.installCmd(e)}</pre>
            </div>
            <div className="oh-card oh-card--pad">
              <div className="ohs-eyebrow" style={{ marginBottom: 10 }}>About</div>
              <p className="ohub-about">{e.desc} Published by {e.by} and continuously evaluated against the shared {cfg.noun} eval pack. Pull it into your workspace, or call it from Teleon.</p>
            </div>
            {cfg.entryExtra && cfg.entryExtra(e, HELPERS)}
          </div>
          <aside className="ohub-detail-rail">
            <div className="oh-card oh-card--pad">
              {[['Publisher', e.by], ['Version', 'v' + (e.ver || '1.2.0')], ['Category', e.facet], ['Eval score', '★ ' + e.score], ['Installs', e.installs], ['License', 'OpenRAIL-M']].map(([k, v]) => (
                <div className="ohub-meta" key={k}><span className="mk">{k}</span><span className="mv mono">{v}</span></div>
              ))}
            </div>
            <div className="oh-card oh-card--pad ohub-trustblock">
              <div className="ohs-eyebrow" style={{ marginBottom: 10 }}>Provenance &amp; trust</div>
              {trustRows(e).map(([k, v, ok]) => (
                <div className="ohub-meta" key={k}><span className="mk">{k}</span><span className={'mv mono' + (ok ? ' ok' : '')}>{v}</span></div>
              ))}
              <div className="ohub-trust-foot mono">rekor log · sha256:{shortHash(e.id, 12)}…<br />signed origin you can verify by hash</div>
            </div>
            {e.deps && (
              <div className="oh-card oh-card--pad">
                <div className="ohs-eyebrow" style={{ marginBottom: 10 }}>Depends on</div>
                <div className="ohub-deps">{e.deps.map((d) => <span className="oh-badge mono" key={d}>{d}</span>)}</div>
              </div>
            )}
            <div className="oh-card oh-card--pad">
              <div className="ohs-eyebrow" style={{ marginBottom: 10 }}>Recent versions</div>
              {[[e.ver || '1.2.0', 'current'], ['1.1.0', '2mo ago'], ['1.0.0', '5mo ago']].map(([v, w], i) => (
                <div className="ohub-meta" key={i}><span className="mk mono">v{v}</span><span className="mv mono">{w}</span></div>
              ))}
            </div>
          </aside>
        </div>
      </div>
    );
  }

  function SimplePage({ title, eyebrow, sub, note }) {
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow={eyebrow} title={title} sub={sub} />
        <div className="oh-card oh-card--pad" style={{ color: 'var(--fg-muted)', fontSize: 14, lineHeight: 1.6 }}>{note}</div>
      </div>
    );
  }

  function Installed() {
    const rows = cfg.entries.slice(0, 3);
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow="Workspace" title="Installed" sub={'The ' + cfg.nounPlural + ' in your workspace.'} />
        <OhRollup items={[['Installed', rows.length], ['Updates', 1], ['Avg eval', '★ 4.7'], ['Calls · 30d', '128k']]} />
        <div className="oh-card oh-card--pad">
          <table className="oh-table">
            <thead><tr><th>{cfg.noun}</th><th>Version</th><th>Eval</th><th></th></tr></thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id}>
                  <td>{e.name}</td><td className="mono">v{e.ver || '1.2.0'}</td><td className="mono">★ {e.score}</td>
                  <td style={{ textAlign: 'right' }}><a className="ohs-navlink" onClick={() => navigate('/e/' + e.id)}>Open →</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // ---------- convert workbench (optional; cfg.convert) ----------
  // The signature interface for a conversion hub (e.g. OpenSkillToTool): pick an input,
  // watch it become the deterministic output contract, publish/use it. Config-driven so any
  // future conversion hub gets it; absent → no /convert route. Composes shared primitives only.
  function ConvertWorkbench() {
    const cv = cfg.convert;
    const inputs = cv.inputs || cfg.entries.map((e) => ({ id: e.id, name: (e.deps && e.deps[0]) || e.name, score: e.score }));
    const [sel, setSel] = React.useState(0);
    const [done, setDone] = React.useState(false);
    const src = inputs[sel] || inputs[0];
    React.useEffect(() => { setDone(false); const t = setTimeout(() => setDone(true), 420); return () => clearTimeout(t); }, [sel]);
    const out = cfg.entries[sel] || cfg.entries[0];
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow={cfg.kind} title={cv.title || (cfg.noun + ' workbench')} sub={cv.sub} />
        <div className="ohub-convert">
          <div className="oh-card oh-card--pad ohub-cv-src">
            <div className="ohs-eyebrow" style={{ marginBottom: 10 }}>{cv.fromLabel || 'Source'}</div>
            <div className="ohub-cv-list">
              {inputs.map((s, i) => (
                <button key={s.id} className={'ohub-cv-item' + (i === sel ? ' on' : '')} onClick={() => setSel(i)}>
                  <span className="ohub-cv-mono mono">{s.name}</span>
                  <span className="oh-badge oh-badge--sm mono">★ {s.score || '4.7'}</span>
                </button>
              ))}
            </div>
            <div className="ohub-cv-note">{cv.fromNote}</div>
          </div>

          <div className="ohub-cv-arrow" aria-hidden="true"><span>{done ? '→' : '⟳'}</span><small className="mono">{done ? 'converted' : 'converting…'}</small></div>

          <div className={'oh-card oh-card--pad ohub-cv-out' + (done ? ' ready' : '')}>
            <div className="ohs-eyebrow" style={{ marginBottom: 10 }}>{cv.toLabel || 'Deterministic output'}</div>
            <div className="ohub-cv-outname">{out.name}</div>
            <pre className="ohub-code">{cfg.installCmd(out)}</pre>
            <div className="ohub-cv-rows">
              {[
                ['Contract', 'typed schema · fixed I/O', true],
                ['Scopes', (out.deps ? 'least-privilege' : 'declared'), true],
                ['Eval carried across', '★ ' + out.score, true],
                ['Provenance', 'signed · ' + ((out.deps && out.deps[0]) || 'source'), true],
                ['Determinism', 'same input → same shape', true],
              ].map(([k, v, ok]) => (
                <div className="ohub-cv-row" key={k}><span className="mk">{k}</span><span className={'mv mono' + (ok ? ' ok' : '')}>{ok ? '✓ ' : ''}{v}</span></div>
              ))}
            </div>
            <div className="ohub-cv-actions">
              <button className="oh-btn oh-btn--primary" onClick={() => navigate('/e/' + out.id)}>Open {cfg.noun} →</button>
              {cv.publishTo && <button className="oh-btn oh-btn--ghost" onClick={() => { window.open(cv.publishTo.href, '_blank'); }}>Publish to {cv.publishTo.label}</button>}
            </div>
          </div>
        </div>
        <div className="ohs-hint mono" style={{ marginTop: 14 }}>{cv.hint}</div>
      </div>
    );
  }

  function App() {
    const route = useHashRoute();
    const [theme, toggle] = useSiteTheme(cfg.themeKey);
    if (route === '/' || route === '') return <Landing theme={theme} onToggle={toggle} />;
    if (route === '/signin' || route === '/signup' || route === '/forgot') {
      return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}>
        <OhAuth brand={B} mode={route.slice(1)} />
      </div>;
    }
    if (route === '/contact') {
      return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}>
        <OhContact brand={B} email={'hello@' + B.name.toLowerCase() + B.tld} />
      </div>;
    }
    if (route === '/docs') {
      return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}>
        <OhDocs theme={theme} onToggle={toggle} cfg={{ brand: B, noun: cfg.noun, nounPlural: cfg.nounPlural,
          intro: 'Find, pull and publish open ' + cfg.nounPlural + ' — versioned, evaluated and ready for any agent or Teleon.',
          firstAction: 'pull your first ' + cfg.noun,
          quickstart: [['Install', 'Add the ' + B.name + ' CLI to your project.'], ['Authenticate', 'Create an API key in the console and export it.'], ['Add ' + cfg.indefinite, 'Pull a ' + cfg.noun + ' from Browse into your workspace.']],
          installCode: B.name.slice(0, 3).toLowerCase() + ' login\n' + B.name.slice(0, 3).toLowerCase() + ' add <id>@<version>' }} />
      </div>;
    }
    if (route === '/status') return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}><OhStatus brand={B} /></div>;
    if (route === '/changelog') return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}><OhChangelog /></div>;
    if (route === '/terms') return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}><OhLegal brand={B} kind="terms" /></div>;
    if (route === '/privacy') return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}><OhLegal brand={B} kind="privacy" /></div>;
    if (route === '/about') return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}><OhAbout brand={B} /></div>;
    const HUB_CASES = (typeof window !== 'undefined' && window.CASES && window.CASES[B.name.toLowerCase()]) || [];
    if (route === '/cases') return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}><OhCaseStudies brand={B} cases={HUB_CASES} /></div>;
    if (route.startsWith('/cases/')) return <div className={rootCls(theme)} style={{ '--accent': ACCENT }}><OhCaseStudy brand={B} cases={HUB_CASES} id={route.slice(7)} cta={{ label: 'Browse the registry →', href: '/browse' }} /></div>;
    let page;
    if (route === '/dashboard') page = <OhDashboard
      stats={[['Installed', cfg.entries.length], ['API calls · 30d', '128k'], ['Published', 3], ['Avg eval', '★ 4.7']]}
      activity={[
        { icon: '⬡', text: 'Installed ' + cfg.entries[0].name, when: '2h ago' },
        { icon: '↥', text: 'Published a new version', when: '1d ago' },
        { icon: '✓', text: cfg.entries[1].name + ' cleared evaluation', when: '2d ago' },
        { icon: '◷', text: 'Invoice paid · $99.00', when: '5d ago' },
      ]}
      plan={{ name: 'Team', usagePct: 48, usageLabel: 'API calls used' }}
      quick={[
        { title: 'Browse the registry', desc: 'Find ' + cfg.nounPlural + ' to add', href: '/browse', cta: 'Browse' },
        { title: 'Publish ' + cfg.indefinite, desc: 'Share with the ecosystem', href: '/publish', cta: 'Publish' },
        { title: 'Create an API key', desc: 'Authenticate your agents', href: '/keys', cta: 'Create' },
      ]} />;
    else if (route === '/browse') page = <Browse />;
    else if (route === '/convert' && cfg.convert) page = cfg.convert.render ? cfg.convert.render(HELPERS) : <ConvertWorkbench />;
    else if (EXTRA.some((r) => r.path === route)) page = EXTRA.find((r) => r.path === route).render(HELPERS);
    else if (route.startsWith('/e/')) page = <EntryDetail id={route.slice(3)} />;
    else if (route === '/installed') page = <Installed />;
    else if (route === '/publish') page = <SimplePage eyebrow="Registry" title={'Publish ' + cfg.indefinite} sub={'Share ' + cfg.indefinite + ' for the ecosystem to build on.'} note={'Point us at your ' + cfg.noun + ', set its version and eval pack, and publish. It gets a provenance signature and appears in Browse once it clears evaluation.'} />;
    else if (route === '/pricing') page = <OhPricing />;
    else if (route === '/billing') page = <OhBilling plan={{ name: 'Team', desc: 'Unlimited installs · private ' + cfg.nounPlural, price: '$99', per: '/mo', usagePct: 48, usageLabel: 'API calls used' }}
      invoices={[['May 1, 2026', '$99.00', 'Paid'], ['Apr 1, 2026', '$99.00', 'Paid'], ['Mar 1, 2026', '$99.00', 'Paid']]} />;
    else if (route === '/keys') page = <OhApiKeys />;
    else if (route === '/team') page = <OhTeam />;
    else if (route === '/audit') page = <OhAuditLog />;
    else if (route === '/notifications') page = <OhNotifications />;
    else if (route === '/onboarding') page = <OhOnboarding brand={B} />;
    else if (route === '/usage') page = <OhUsage rollup={[['API calls · 30d', '128k'], ['Installs', cfg.entries.length], ['Published', 3], ['Avg eval', '★ 4.7']]}
      metrics={[{ k: 'API calls', v: '128k', bars: [.4, .5, .55, .6, .7, .8, .9], hiLast: true }, { k: 'New installs', v: '312', bars: [.5, .45, .6, .55, .7, .65, .85], hiLast: true }]} />;
    else if (route === '/settings') page = <OhSettings sections={[
      { title: 'Profile', rows: [{ t: 'Display name', d: 'Shown on entries you publish', ctrl: <input className="oh-input" defaultValue="Ada Lovelace" /> }, { t: 'Publisher handle', d: 'Your namespace in the registry', ctrl: <input className="oh-input" defaultValue="@ada" /> }] },
      { title: 'Preferences', rows: [{ t: 'Auto-update installs', d: 'Pull new versions that clear evaluation', ctrl: <OhSwitch on onToggle={() => {}} /> }, { t: 'Publish notifications', d: 'Email when an entry is installed', ctrl: <OhSwitch onToggle={() => {}} /> }] },
    ]} />;
    else page = <OhNotFound brand={B} home="/dashboard" links={[['Browse', '/browse'], ['Docs', '/docs']]} />;
    return (
      <div className={rootCls(theme)} style={{ '--accent': ACCENT }}>
        {PRIVATE && <PrivateBanner />}
        <OhAppShell brand={B} nav={APP_NAV} route={route} cta={{ label: '↥ Publish', href: '/publish' }} theme={theme} onToggle={toggle}
          header={<button className="ohs-side-search" onClick={() => window.dispatchEvent(new CustomEvent('oh-cmdk'))}><span className="ohs-side-search-l"><span aria-hidden="true">⌕</span> Search…</span><span className="oh-kbd">⌘K</span></button>}>{page}</OhAppShell>
        <OhCommandK commands={HUB_CMDS} placeholder={'Search ' + B.name + '…'} />
      </div>
    );
  }
  return App;
}

Object.assign(window, { makeHub });
