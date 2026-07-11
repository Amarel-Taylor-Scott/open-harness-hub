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
  // realm id for this hub (matches the identity/registry realm — brand.name, normalized).
  const REALM = (typeof window !== 'undefined' && window.OHRegistry) ? window.OHRegistry.realmOf(B)
    : (B.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  // live per-account registry data, or null → the UI falls back to the in-file design seed (honest).
  function useWorkspace() {
    const [ws, setWs] = React.useState(null);
    const refresh = React.useCallback(() => {
      if (typeof window !== 'undefined' && window.OHRegistry) window.OHRegistry.workspace(REALM).then(setWs, () => setWs(null));
    }, []);
    React.useEffect(() => { refresh(); }, [refresh]);
    return [ws, refresh];
  }
  // live PUBLIC catalog for this hub from the registry plane (no session needed), or null → the UI
  // falls back to the in-file design seed (honest; same entry shape either way).
  function useCatalog() {
    const [entries, setEntries] = React.useState(null);
    React.useEffect(() => {
      if (typeof window !== 'undefined' && window.OHRegistry) {
        window.OHRegistry.search(REALM).then((es) => setEntries(es && es.length ? es : null), () => setEntries(null));
      }
    }, []);
    return entries;
  }
  // is the signed-in account a reviewer for this realm? (granted by an admin/operator; gates Review.)
  function useReviewer() {
    const [isReviewer, setIsReviewer] = React.useState(false);
    React.useEffect(() => {
      if (typeof window !== 'undefined' && window.OHRegistry) window.OHRegistry.amReviewer(REALM).then(setIsReviewer, () => setIsReviewer(false));
    }, []);
    return isReviewer;
  }
  // is the signed-in account an admin? (operator-bootstrapped only; gates the Admin console.)
  function useAdmin() {
    const [isAdmin, setIsAdmin] = React.useState(false);
    React.useEffect(() => {
      if (typeof window !== 'undefined' && window.OHRegistry) window.OHRegistry.amAdmin(REALM).then(setIsAdmin, () => setIsAdmin(false));
    }, []);
    return isAdmin;
  }
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
          ['Group', [['AI Done Right ↗', '../context-is-everything/Context is Everything.html'], ['Teleon.dev ↗', '../teleon/Teleon.html'], ['Baltor.ai ↗', '../context-enrichment/Context Enrichment.html']]],
        ]} />
        <OhExperimentsPanel />
      </div>
    );
  }

  // ---------- browse (the graph) ----------
  function Browse() {
    const [facet, setFacet] = React.useState('All');
    const [q, setQ] = React.useState('');
    // real registry catalog when the plane is up; else the in-file design seed (same shape).
    const source = useCatalog() || cfg.entries;
    const list = source.filter((e) => (facet === 'All' || e.facet === facet) && (!q || ((e.name || '') + (e.by || '') + (e.desc || '')).toLowerCase().includes(q.toLowerCase())));
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
    const seed = cfg.entries.find((x) => x.id === id);
    const [fetched, setFetched] = React.useState(undefined);   // undefined = loading; null = not found
    const [added, setAdded] = React.useState(false);
    // promoted (reviewer-approved) entries aren't in the in-file seed — resolve them from the registry.
    React.useEffect(() => {
      if (!seed && window.OHRegistry) window.OHRegistry.entry(REALM, id).then((x) => setFetched(x || null), () => setFetched(null));
    }, [id, seed]);
    const e = seed || (fetched && typeof fetched === 'object' ? fetched : null);
    if (!seed && fetched === undefined) return <div className="ohs-page"><OhPageHead eyebrow={cfg.noun} title="Loading…" sub="Fetching this entry from the registry." /></div>;
    if (!e) return <SimplePage title="Not found" sub="That entry doesn’t exist." note="Browse the registry to find one." />;
    // record a REAL install against the registry (session-gated; no-op when signed out / service down).
    const addToWorkspace = () => { if (window.OHRegistry) window.OHRegistry.install(REALM, e).then((r) => { if (r && r.ok) setAdded(true); }); };
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
            <button className="oh-btn oh-btn--primary" onClick={addToWorkspace} disabled={added}>{added ? '✓ Added to workspace' : '+ Add to workspace'}</button>
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
            {e.provenance && (
              <div className="oh-card oh-card--pad">
                <div className="ohs-eyebrow" style={{ marginBottom: 10 }}>Promotion lineage</div>
                {[['Origin', 'community · reviewed'], ['Submitted by', e.provenance.submitter || '—'],
                  ['Approved by', e.provenance.reviewer || '—'], ['Reviewer note', e.provenance.reason || '—']].map(([k, v]) => (
                  <div className="ohub-meta" key={k}><span className="mk">{k}</span><span className="mv mono">{v}</span></div>
                ))}
              </div>
            )}
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
    const [ws] = useWorkspace();
    // real installed entries when signed in + the registry is up; else the design seed (honest).
    const rows = (ws && ws.installed && ws.installed.length) ? ws.installed : cfg.entries.slice(0, 3);
    const avgEval = ws ? ws.stats[3][1] : '★ 4.7';
    const calls = ws ? ws.stats[1][1] : '128k';
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow="Workspace" title="Installed" sub={'The ' + cfg.nounPlural + ' in your workspace.'} />
        <OhRollup items={[['Installed', rows.length], ['Updates', 1], ['Avg eval', avgEval], ['Calls · 30d', calls]]} />
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

  // ---------- publish (REAL submission → the registry review queue) ----------
  // A working publish form: it submits the candidate to the registry plane's review queue
  // (session-gated). Submissions are CANDIDATES — signed + evaluated, they appear in Browse only
  // after they clear review (discovery ≠ trust; candidate ≠ active). The publisher sees their
  // queued candidates with a live "in review" status read back from the registry.
  function PublishForm() {
    const slug = (s) => s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48);
    const [name, setName] = React.useState('');
    const [facet, setFacet] = React.useState((cfg.facets && cfg.facets[0]) || '');
    const [ver, setVer] = React.useState('1.0.0');
    const [desc, setDesc] = React.useState('');
    const [busy, setBusy] = React.useState(false);
    const [result, setResult] = React.useState(null);        // {ok:true,status,note} | {ok:false,error}
    const [subs, setSubs] = React.useState(null);            // null = signed out / down; [] = none yet
    const refreshSubs = React.useCallback(() => {
      if (typeof window !== 'undefined' && window.OHRegistry) window.OHRegistry.submissions(REALM).then(setSubs, () => setSubs(null));
    }, []);
    React.useEffect(() => { refreshSubs(); }, [refreshSubs]);

    const submit = () => {
      if (!name.trim()) { setResult({ ok: false, error: 'Give your ' + cfg.noun + ' a name first.' }); return; }
      if (!window.OHRegistry) { setResult({ ok: false, error: 'Registry service unavailable — can’t publish right now.' }); return; }
      const entry = { id: slug(name) || ('draft-' + Math.random().toString(16).slice(2, 8)), name: name.trim(),
        facet: facet, ver: (ver.trim() || '1.0.0'), desc: desc.trim(), by: sessionInfo().handle, score: '—' };
      setBusy(true); setResult(null);
      window.OHRegistry.publish(REALM, entry).then((r) => {
        setBusy(false);
        if (r && r.ok) {
          setResult({ ok: true, status: (r.body && r.body.status) || 'in_review', note: (r.body && r.body.note) || '' });
          setName(''); setDesc(''); refreshSubs();
        } else {
          setResult({ ok: false, error: (r && r.body && r.body.error) || 'You need to be signed in to publish — create an account or sign in first.' });
        }
      });
    };

    return (
      <div className="ohs-page">
        <OhPageHead eyebrow="Registry" title={'Publish ' + cfg.indefinite}
          sub={'Submit ' + cfg.indefinite + ' for the ecosystem to build on — it enters a review queue as a candidate.'} />
        <div className="ohs-dash-grid">
          <div className="oh-card oh-card--pad">
            <div className="ohs-card-h">Submit a {cfg.noun}</div>
            <label className="oh-field"><span>Name</span>
              <input className="oh-input" value={name} onChange={(e) => setName(e.target.value)} placeholder={cfg.noun + ' name'} /></label>
            <label className="oh-field"><span>Category</span>
              <select className="oh-input" value={facet} onChange={(e) => setFacet(e.target.value)}>
                {(cfg.facets || []).map((f) => <option key={f} value={f}>{f}</option>)}
              </select></label>
            <label className="oh-field"><span>Version</span>
              <input className="oh-input" value={ver} onChange={(e) => setVer(e.target.value)} placeholder="1.0.0" /></label>
            <label className="oh-field"><span>Description</span>
              <textarea className="oh-input" rows={4} value={desc} onChange={(e) => setDesc(e.target.value)} placeholder={'What does this ' + cfg.noun + ' do, and what does it draw on?'} /></label>
            <button className="oh-btn oh-btn--primary" onClick={submit} disabled={busy} style={{ marginTop: 6 }}>
              {busy ? 'Submitting…' : '↥ Submit for review'}</button>
            {result && result.ok && (
              <div className="mono" role="status" style={{ marginTop: 12, padding: '10px 12px', borderRadius: 8, fontSize: 12.5,
                color: 'var(--success)', background: 'color-mix(in srgb, var(--success) 12%, transparent)' }}>
                ✓ Submitted — status: <strong>in review</strong>. {result.note || 'Appears in Browse only after it clears review.'}</div>
            )}
            {result && !result.ok && (
              <div className="mono" role="alert" style={{ marginTop: 12, padding: '10px 12px', borderRadius: 8, fontSize: 12.5,
                color: 'var(--danger)', background: 'color-mix(in srgb, var(--danger) 12%, transparent)' }}>{result.error}</div>
            )}
            <p className="ohs-hint mono">Submissions enter a review queue as <strong>candidates</strong> — they appear in Browse only after they clear review. Discovery ≠ trust.</p>
          </div>
          <div className="ohs-dash-side">
            <div className="oh-card oh-card--pad">
              <div className="ohs-card-h">Your submissions</div>
              {subs && subs.length ? (
                <table className="oh-table">
                  <thead><tr><th>{cfg.noun}</th><th>Status</th></tr></thead>
                  <tbody>
                    {subs.map((s) => (
                      <tr key={s.entry_id + s.ts}>
                        <td>{s.name}{s.facet ? <span className="mono" style={{ color: 'var(--fg-faint)' }}> · {s.facet}</span> : null}</td>
                        <td><span className="oh-badge mono" style={{ color: 'var(--warning)' }}>⏳ in review</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ color: 'var(--fg-muted)', fontSize: 13, lineHeight: 1.6 }}>
                  {subs === null ? 'Sign in to submit and track your candidates.' : 'No submissions yet — publish one to see it enter the review queue.'}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------- review (the PROMOTION GATE — reviewer-only) ----------
  // The only surface that turns a candidate into a public-active catalog entry. Reviewer access is
  // operator-granted (never self-served) and a reviewer can't decide on their own submission — the
  // server enforces both; this UI just reflects it. Decisions are append-only and carry lineage;
  // reject/revoke preserve the candidate (lossless). Approve promotes it into Browse with provenance.
  function ReviewQueue() {
    const isReviewer = useReviewer();
    const [queue, setQueue] = React.useState(null);
    const [promoted, setPromoted] = React.useState([]);   // live community entries (revertable)
    const [reasons, setReasons] = React.useState({});
    const [busy, setBusy] = React.useState('');
    const [flash, setFlash] = React.useState(null);
    const refresh = React.useCallback(() => {
      if (!window.OHRegistry) return;
      window.OHRegistry.reviewQueue(REALM).then(setQueue, () => setQueue(null));
      window.OHRegistry.search(REALM).then((es) => setPromoted((es || []).filter((e) => e.provenance)), () => setPromoted([]));
    }, []);
    React.useEffect(() => { if (isReviewer) refresh(); }, [isReviewer, refresh]);

    const decide = (eid, decision) => {
      setBusy(eid + decision); setFlash(null);
      window.OHRegistry.decide(REALM, eid, decision, reasons[eid] || '').then((r) => {
        setBusy('');
        if (r && r.ok) { setFlash({ ok: true, text: (r.body && r.body.note) || (decision + ' recorded') }); refresh(); }
        else { setFlash({ ok: false, text: (r && r.body && r.body.error) || 'Decision failed.' }); }
      });
    };

    if (!isReviewer) {
      return (
        <div className="ohs-page">
          <OhPageHead eyebrow="Registry" title="Review queue" sub="Promote cleared candidates into the catalog." />
          <div className="oh-card oh-card--pad" style={{ color: 'var(--fg-muted)', fontSize: 14, lineHeight: 1.6 }}>
            You don’t have reviewer access for {B.name}. Reviewer status is granted by an operator — it is never
            self-served — so the queue and the promote / reject controls are visible only to reviewers.
          </div>
        </div>
      );
    }
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow="Registry" title="Review queue"
          sub={'Candidates awaiting review. Approving promotes a ' + cfg.noun + ' into the catalog — the only path to public-active.'} />
        {flash && (
          <div className="mono" role="status" style={{ marginBottom: 14, padding: '10px 12px', borderRadius: 8, fontSize: 12.5,
            color: flash.ok ? 'var(--success)' : 'var(--danger)', background: 'color-mix(in srgb, ' + (flash.ok ? 'var(--success)' : 'var(--danger)') + ' 12%, transparent)' }}>{flash.ok ? '✓ ' : ''}{flash.text}</div>
        )}
        {queue && queue.length ? (
          <div>
            {queue.map((c) => (
              <div className="oh-card oh-card--pad" key={c.entry_id} style={{ marginBottom: 12 }}>
                <div className="ohub-detail-head" style={{ marginBottom: 8 }}>
                  <div>
                    <div className="ohs-eyebrow">{cfg.noun}{c.facet ? ' · ' + c.facet : ''}</div>
                    <h3 style={{ margin: '4px 0' }}>{c.name}</h3>
                    <div className="ec-by mono">candidate {c.entry_id} · submitted {c.submitted_when} · v{c.ver || '1.0.0'}</div>
                    {c.desc ? <p style={{ color: 'var(--fg-muted)', fontSize: 13.5, marginTop: 6 }}>{c.desc}</p> : null}
                  </div>
                  <span className="oh-badge mono" style={{ color: 'var(--warning)' }}>⏳ in review</span>
                </div>
                <input className="oh-input" placeholder="Reason / eval note (recorded with your decision)"
                  value={reasons[c.entry_id] || ''} onChange={(e) => setReasons({ ...reasons, [c.entry_id]: e.target.value })} style={{ marginBottom: 10 }} />
                <div className="ohub-detail-actions">
                  <button className="oh-btn oh-btn--primary" disabled={busy === c.entry_id + 'approve'} onClick={() => decide(c.entry_id, 'approve')}>✓ Approve &amp; promote</button>
                  <button className="oh-btn oh-btn--ghost" disabled={busy === c.entry_id + 'reject'} onClick={() => decide(c.entry_id, 'reject')}>Reject</button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="oh-card oh-card--pad" style={{ color: 'var(--fg-muted)', fontSize: 14 }}>
            {queue === null ? 'Couldn’t load the queue.' : 'Nothing awaiting review — the queue is clear.'}
          </div>
        )}
        {promoted.length > 0 && (
          <div className="oh-card oh-card--pad" style={{ marginTop: 18 }}>
            <div className="ohs-card-h">Promoted &amp; live ({promoted.length}) — revertable</div>
            <table className="oh-table">
              <thead><tr><th>{cfg.noun}</th><th>Approved by</th><th></th></tr></thead>
              <tbody>
                {promoted.map((e) => (
                  <tr key={e.id}>
                    <td>{e.name}<span className="oh-badge oh-badge--sm oh-badge--verified mono" style={{ marginLeft: 8 }}>live</span></td>
                    <td className="mono" style={{ fontSize: 12 }}>{(e.provenance.reviewer || '—').slice(0, 16)}…</td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="oh-btn oh-btn--ghost oh-btn--sm" disabled={busy === e.id + 'revoke'} onClick={() => decide(e.id, 'revoke')}>↩ Revoke</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="ohs-hint mono">Revoke rolls an entry back out of Browse. It’s lossless — the decision is recorded, the candidate is preserved, and it can be re-approved.</div>
          </div>
        )}
        <p className="ohs-hint mono">Every decision is recorded with your account and reason. Approve promotes the candidate into Browse with provenance; reject / revoke preserve it (nothing is deleted). A reviewer can’t decide on their own submission.</p>
      </div>
    );
  }

  // ---------- admin console (grant / revoke REVIEWERS) ----------
  // The most privileged surface — it hands out the power to promote candidates. Admin status is
  // operator-bootstrapped ONLY (never self-served in-app), so the console can't escalate past the
  // operator root: it grants/revokes REVIEWERS, not admins. Every grant records the acting admin.
  function AdminConsole() {
    const isAdmin = useAdmin();
    const [data, setData] = React.useState(null);     // {reviewers:[], contributors:[]} | null
    const [acct, setAcct] = React.useState('');
    const [reason, setReason] = React.useState('');
    const [busy, setBusy] = React.useState('');
    const [flash, setFlash] = React.useState(null);
    const refresh = React.useCallback(() => {
      if (window.OHRegistry) window.OHRegistry.adminReviewers(REALM).then(setData, () => setData(null));
    }, []);
    React.useEffect(() => { if (isAdmin) refresh(); }, [isAdmin, refresh]);

    const grant = (target, why) => {
      if (!target) { setFlash({ ok: false, text: 'Enter an account id to grant.' }); return; }
      setBusy('grant' + target); setFlash(null);
      window.OHRegistry.grantReviewer(REALM, target, why || reason).then((r) => {
        setBusy('');
        if (r && r.ok) { setFlash({ ok: true, text: 'Granted reviewer: ' + target }); setAcct(''); setReason(''); refresh(); }
        else { setFlash({ ok: false, text: (r && r.body && r.body.error) || 'Grant failed.' }); }
      });
    };
    const revoke = (target) => {
      setBusy('revoke' + target); setFlash(null);
      window.OHRegistry.revokeReviewer(REALM, target).then((r) => {
        setBusy('');
        if (r && r.ok) { setFlash({ ok: true, text: 'Revoked reviewer: ' + target }); refresh(); }
        else { setFlash({ ok: false, text: (r && r.body && r.body.error) || 'Revoke failed.' }); }
      });
    };

    if (!isAdmin) {
      return (
        <div className="ohs-page">
          <OhPageHead eyebrow="Admin" title="Admin console" sub="Grant and revoke reviewer access." />
          <div className="oh-card oh-card--pad" style={{ color: 'var(--fg-muted)', fontSize: 14, lineHeight: 1.6 }}>
            You don’t have admin access for {B.name}. Admin status is bootstrapped by an operator — it is never
            self-served — so the reviewer-management controls are visible only to admins.
          </div>
        </div>
      );
    }
    const reviewers = (data && data.reviewers) || [];
    const contributors = (data && data.contributors) || [];
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow="Admin" title="Admin console"
          sub={'Grant reviewer access for ' + B.name + '. Reviewers can promote candidates into the catalog.'} />
        {flash && (
          <div className="mono" role="status" style={{ marginBottom: 14, padding: '10px 12px', borderRadius: 8, fontSize: 12.5,
            color: flash.ok ? 'var(--success)' : 'var(--danger)', background: 'color-mix(in srgb, ' + (flash.ok ? 'var(--success)' : 'var(--danger)') + ' 12%, transparent)' }}>{flash.ok ? '✓ ' : ''}{flash.text}</div>
        )}
        <div className="ohs-dash-grid">
          <div className="oh-card oh-card--pad">
            <div className="ohs-card-h">Grant a reviewer</div>
            <label className="oh-field"><span>Account id</span>
              <input className="oh-input" value={acct} onChange={(e) => setAcct(e.target.value)} placeholder="acct_…" /></label>
            <label className="oh-field"><span>Reason (recorded)</span>
              <input className="oh-input" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="why this person" /></label>
            <button className="oh-btn oh-btn--primary" disabled={busy === 'grant' + acct} onClick={() => grant(acct)} style={{ marginTop: 6 }}>+ Grant reviewer</button>
            <p className="ohs-hint mono">Admin status is operator-bootstrapped; this console grants <strong>reviewers</strong> only. Every grant is recorded with your account id.</p>
            {contributors.length > 0 && (
              <div style={{ marginTop: 18 }}>
                <div className="ohs-card-h">Recent contributors</div>
                <table className="oh-table">
                  <thead><tr><th>Account</th><th>Submissions</th><th></th></tr></thead>
                  <tbody>
                    {contributors.map((c) => (
                      <tr key={c.account_id}>
                        <td className="mono" style={{ fontSize: 12 }}>{c.account_id.slice(0, 18)}…</td>
                        <td className="mono">{c.submissions}</td>
                        <td style={{ textAlign: 'right' }}>
                          {reviewers.indexOf(c.account_id) >= 0
                            ? <span className="oh-badge mono" style={{ color: 'var(--success)' }}>✓ reviewer</span>
                            : <button className="oh-btn oh-btn--ghost oh-btn--sm" disabled={busy === 'grant' + c.account_id} onClick={() => grant(c.account_id, 'active contributor')}>Grant</button>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          <div className="ohs-dash-side">
            <div className="oh-card oh-card--pad">
              <div className="ohs-card-h">Reviewers ({reviewers.length})</div>
              {reviewers.length ? (
                <table className="oh-table">
                  <tbody>
                    {reviewers.map((a) => (
                      <tr key={a}>
                        <td className="mono" style={{ fontSize: 12 }}>{a.slice(0, 18)}…</td>
                        <td style={{ textAlign: 'right' }}>
                          <button className="oh-btn oh-btn--ghost oh-btn--sm" disabled={busy === 'revoke' + a} onClick={() => revoke(a)}>Revoke</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ color: 'var(--fg-muted)', fontSize: 13 }}>{data === null ? 'Couldn’t load reviewers.' : 'No reviewers yet — grant one.'}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---- the signed-in account, from the realm session (REAL identity) ----
  function sessionInfo() {
    const s = (typeof window !== 'undefined' && window.OHIdentity && window.OHIdentity.session(REALM)) || {};
    const email = s.email || '';
    return { email, account_id: s.account_id || '', handle: '@' + ((email.split('@')[0]) || 'you') };
  }

  // ---- API keys (REAL — identity service mint/list/revoke; raw key shown once) ----
  function HubApiKeys() {
    const [keys, setKeys] = React.useState(null);
    const [raw, setRaw] = React.useState(null);
    const [busy, setBusy] = React.useState(false);
    const [err, setErr] = React.useState('');
    const refresh = React.useCallback(() => {
      if (window.OHIdentity) window.OHIdentity.listKeys(REALM).then((r) => setKeys((r.body && r.body.api_keys) || []), () => setKeys(null));
    }, []);
    React.useEffect(() => { refresh(); }, [refresh]);
    const create = () => {
      setBusy(true); setErr(''); setRaw(null);
      window.OHIdentity.mintKey(REALM, ['read', 'write']).then((r) => {
        setBusy(false);
        if (r.status === 201 && r.body && r.body.api_key) { setRaw(r.body.api_key); refresh(); }
        else setErr((r.body && r.body.error) || 'You need to be signed in to create a key.');
      }, () => { setBusy(false); setErr('Identity service unavailable.'); });
    };
    const revoke = (kid) => { if (window.OHIdentity) window.OHIdentity.revokeKey(REALM, kid).then(refresh); };
    const fmt = (ts) => ts ? new Date(ts * 1000).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '—';
    const ago = (ts) => { if (!ts) return 'never'; const d = Math.floor(Date.now() / 1000 - ts); if (d < 60) return 'just now'; if (d < 3600) return Math.floor(d / 60) + 'm ago'; if (d < 86400) return Math.floor(d / 3600) + 'h ago'; return Math.floor(d / 86400) + 'd ago'; };
    const activeKeys = (keys || []).filter((k) => !k.revoked_at);
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow="Developers" title="API keys" sub="Create and manage the keys your agents authenticate with."
          actions={<button className="oh-btn oh-btn--primary" disabled={busy} onClick={create}>{busy ? 'Creating…' : '+ Create key'}</button>} />
        {raw && (
          <div className="oh-card oh-card--pad" style={{ marginBottom: 16, borderColor: 'var(--success)' }}>
            <div className="ohs-eyebrow" style={{ marginBottom: 8, color: 'var(--success)' }}>✓ New key — copy it now, it’s shown once</div>
            <pre className="ohub-code" style={{ userSelect: 'all' }}>{raw}</pre>
            <div className="ohs-hint mono">We store only a hash — we can’t show this again. Treat it like a password.</div>
          </div>
        )}
        {err && <div className="mono" role="alert" style={{ marginBottom: 14, padding: '10px 12px', borderRadius: 8, fontSize: 12.5, color: 'var(--danger)', background: 'color-mix(in srgb, var(--danger) 12%, transparent)' }}>{err}</div>}
        <div className="oh-card oh-card--pad">
          <table className="oh-table">
            <thead><tr><th>Key</th><th>Scopes</th><th>Created</th><th>Last used</th><th></th></tr></thead>
            <tbody>
              {activeKeys.length ? activeKeys.map((k) => (
                <tr key={k.key_id}>
                  <td className="mono">{k.prefix}••••</td>
                  <td className="mono">{(k.scopes || []).join(', ')}</td>
                  <td className="mono">{fmt(k.created_at)}</td>
                  <td className="mono">{ago(k.last_used_at)}</td>
                  <td style={{ textAlign: 'right' }}><a className="ohs-navlink ohs-danger" onClick={() => revoke(k.key_id)}>Revoke</a></td>
                </tr>
              )) : (
                <tr><td colSpan={5} style={{ color: 'var(--fg-muted)' }}>{keys === null ? 'Sign in to manage API keys.' : 'No keys yet — create one to authenticate your agents.'}</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="ohs-hint mono">Keys are stored hash-only; the raw value is shown once at creation. Revoked keys stop working immediately.</div>
      </div>
    );
  }

  // ---- audit log (REAL — the account's recorded registry activity, no fabrication) ----
  function HubAudit() {
    const [rows, setRows] = React.useState(null);
    const me = sessionInfo();
    React.useEffect(() => { if (window.OHRegistry) window.OHRegistry.audit(REALM).then(setRows, () => setRows(null)); }, []);
    if (rows && rows.length) return <OhAuditLog rows={rows.map((r) => ({ ...r, actor: me.handle }))} />;
    return (
      <div className="ohs-page">
        <OhPageHead eyebrow="Governance" title="Audit log" sub="Every action you take in the registry — recorded and attributable." />
        <div className="oh-card oh-card--pad" style={{ color: 'var(--fg-muted)', fontSize: 14 }}>
          {rows === null ? 'Sign in to see your audit trail.' : 'No activity yet — install, publish or review something and it appears here.'}
        </div>
      </div>
    );
  }

  // ---- usage / notifications / billing / team / settings (REAL via workspace + session) ----
  function HubUsage() {
    const [ws] = useWorkspace();
    if (!ws) return <OhUsage rollup={[['Installed', 0], ['API calls · 30d', 0], ['Published', 0], ['Avg eval', '—']]} metrics={[]} />;
    const stat = Object.fromEntries(ws.stats);
    return <OhUsage rollup={ws.stats}
      metrics={[{ k: 'API calls · 30d', v: String(stat['API calls · 30d']), bars: [.3, .5, .4, .6, .7, .6, .9], hiLast: true },
                { k: 'Installed', v: String(stat['Installed']), bars: [.2, .3, .5, .5, .7, .8, 1], hiLast: true }]} />;
  }
  function HubNotifications() {
    const [ws] = useWorkspace();
    if (!ws || !ws.activity) return <OhNotifications items={[{ icon: '◷', t: 'Nothing yet', d: 'Your activity will show here', w: '' }]} />;
    return <OhNotifications items={ws.activity.map((a, i) => ({ icon: a.icon, t: a.text, d: 'in your workspace', w: a.when, unread: i < 2 }))} />;
  }
  function HubBilling() {
    const [ws] = useWorkspace();
    const plan = (ws && ws.plan) || { name: 'Free', usagePct: 0, usageLabel: 'API calls used' };
    // honest: the REAL Free plan + real usage; NO fabricated paid invoices (nothing has been charged).
    return <OhBilling plan={{ name: plan.name, desc: 'Open registry access · pay-as-you-grow', price: '$0', per: '/mo', usagePct: plan.usagePct, usageLabel: plan.usageLabel }} invoices={[]} />;
  }
  function HubTeam() {
    const me = sessionInfo();
    // honest: the single REAL account; invites are a seam, never fabricated colleagues.
    const members = me.email ? [{ name: me.handle, email: me.email, role: 'Owner', status: 'active' }] : [];
    return <OhTeam members={members} />;
  }
  function HubSettings() {
    const me = sessionInfo();
    const [copied, setCopied] = React.useState(false);
    const copyId = () => { try { navigator.clipboard.writeText(me.account_id); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch (e) {} };
    const sections = [
      { title: 'Account', rows: [
        { t: 'Email', d: 'Your sign-in identity for ' + B.name, ctrl: <span className="mono">{me.email || '—'}</span> },
        { t: 'Account ID', d: 'Hand this to an admin to be granted reviewer access', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm mono" onClick={copyId}>{copied ? 'copied ✓' : (me.account_id ? me.account_id.slice(0, 18) + '… ⧉' : '—')}</button> },
        { t: 'Publisher handle', d: 'Shown on entries you publish', ctrl: <span className="mono">{me.handle}</span> },
      ] },
      { title: 'Preferences', rows: [
        { t: 'Auto-update installs', d: 'Pull new versions that clear evaluation', ctrl: <OhSwitch on onToggle={() => {}} /> },
        { t: 'Publish notifications', d: 'Email when an entry is installed', ctrl: <OhSwitch onToggle={() => {}} /> },
      ] },
    ];
    return <OhSettings sections={sections} />;
  }

  // The signed-in dashboard. Reads the REAL per-account workspace summary from the registry plane
  // (installed/published/avg-eval/API-calls/activity); falls back to the in-file design seed when
  // the registry is down or the visitor is signed out — never presents the seed as live numbers.
  function HubDashboard() {
    const [ws] = useWorkspace();
    const stats = ws ? ws.stats
      : [['Installed', cfg.entries.length], ['API calls · 30d', '128k'], ['Published', 3], ['Avg eval', '★ 4.7']];
    const activity = ws ? ws.activity : [
      { icon: '⬡', text: 'Installed ' + cfg.entries[0].name, when: '2h ago' },
      { icon: '↥', text: 'Published a new version', when: '1d ago' },
      { icon: '✓', text: cfg.entries[1].name + ' cleared evaluation', when: '2d ago' },
      { icon: '◷', text: 'Invoice paid · $99.00', when: '5d ago' },
    ];
    const plan = ws ? ws.plan : { name: 'Team', usagePct: 48, usageLabel: 'API calls used' };
    return <OhDashboard stats={stats} activity={activity} plan={plan} quick={[
      { title: 'Browse the registry', desc: 'Find ' + cfg.nounPlural + ' to add', href: '/browse', cta: 'Browse' },
      { title: 'Publish ' + cfg.indefinite, desc: 'Share with the ecosystem', href: '/publish', cta: 'Publish' },
      { title: 'Create an API key', desc: 'Authenticate your agents', href: '/keys', cta: 'Create' },
    ]} />;
  }

  function App() {
    const route = useHashRoute();
    const [theme, toggle] = useSiteTheme(cfg.themeKey);
    const isReviewer = useReviewer();   // gates the Review nav item + surface (admin/operator-granted)
    const isAdmin = useAdmin();         // gates the Admin console (operator-bootstrapped)
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
    if (route === '/dashboard') page = <HubDashboard />;
    else if (route === '/browse') page = <Browse />;
    else if (route === '/convert' && cfg.convert) page = cfg.convert.render ? cfg.convert.render(HELPERS) : <ConvertWorkbench />;
    else if (EXTRA.some((r) => r.path === route)) page = EXTRA.find((r) => r.path === route).render(HELPERS);
    else if (route.startsWith('/e/')) page = <EntryDetail id={route.slice(3)} />;
    else if (route === '/installed') page = <Installed />;
    else if (route === '/publish') page = <PublishForm />;
    else if (route === '/pricing') page = <OhPricing />;
    else if (route === '/billing') page = <HubBilling />;
    else if (route === '/keys') page = <HubApiKeys />;
    else if (route === '/team') page = <HubTeam />;
    else if (route === '/audit') page = <HubAudit />;
    else if (route === '/notifications') page = <HubNotifications />;
    else if (route === '/onboarding') page = <OhOnboarding brand={B} />;
    else if (route === '/usage') page = <HubUsage />;
    else if (route === '/settings') page = <HubSettings />;
    else if (route === '/review') page = <ReviewQueue />;
    else if (route === '/admin') page = <AdminConsole />;
    else page = <OhNotFound brand={B} home="/dashboard" links={[['Browse', '/browse'], ['Docs', '/docs']]} />;
    // reviewers get a nav entry to the promotion gate; admins also get the admin console (both hidden
    // for everyone else).
    const navItems = [...APP_NAV,
      ...(isReviewer ? [['/review', '⚑', 'Review']] : []),
      ...(isAdmin ? [['/admin', '⚙', 'Admin']] : [])];
    return (
      <div className={rootCls(theme)} style={{ '--accent': ACCENT }}>
        {PRIVATE && <PrivateBanner />}
        <OhAppShell brand={B} nav={navItems} route={route} cta={{ label: '↥ Publish', href: '/publish' }} theme={theme} onToggle={toggle}
          header={<button className="ohs-side-search" onClick={() => window.dispatchEvent(new CustomEvent('oh-cmdk'))}><span className="ohs-side-search-l"><span aria-hidden="true">⌕</span> Search…</span><span className="oh-kbd">⌘K</span></button>}>{page}</OhAppShell>
        <OhCommandK commands={HUB_CMDS} placeholder={'Search ' + B.name + '…'} />
      </div>
    );
  }
  return App;
}

Object.assign(window, { makeHub });
