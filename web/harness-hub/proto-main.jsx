/* global React, ReactDOM, useHashRoute, navigate, StoreCtx, PLanding, PBuild, PResults, PFlow, PRun, PBrowse, PDetail, PDashboard, PNotFound, PPricing, Mark, PFoundry, PImprove, PDashboards, PSettings, PRegistry, PConnect, PAdmin, PCheckout, PWorkers, PSolutions, PSolution, PFreshness, PAttest, PStatus, PActivity, PSources, PRequests, PRequestDetail, PContribute, PKnowledgeEntry, PProvenance, PTrustCenter, PAuditLog, PRoles, PSignin, POnboarding, PUpgrade, PPublish, PPreview, PUseCase */
// OpenHarnessHub prototype — root app: router, shells, sidebar, command palette, toasts, scheme switcher.

const SCHEMES = [
  ['s', '#d6553a', 'House'], ['a', '#b8501f', 'Editorial'], ['b', '#2563eb', 'Mono'],
  ['c', '#7c6bf0', 'Violet'], ['d', '#0e7c86', 'Teal'], ['e', '#22c7d6', 'Blueprint'],
  ['f', '#1e6b43', 'Ledger'], ['g', '#39d353', 'Hacker'], ['h', '#1f5fbf', 'Slate'],
];
const MKT_ROUTES = ['/', '/pricing', '/trust', '/signin', '/signup', '/onboarding', '/upgrade', '/preview'];

// ---- app sidebar ----
const NAV_GROUPS = [
  ['Explore', [['Explore pipelines', '/pipelines', '◫'], ['Explore components', '/components', '⬡'], ['Requests', '/requests', '◷']]],
  ['Workspace', [['Dashboard', '/app', '◳'], ['Activity', '/activity', '◔'], ['Runs', '/run', '▷'], ['Dashboards', '/dashboards', '▦']]],
  ['Govern', [['Registry', '/registry', '🔒'], ['Publish', '/publish', '⇧'], ['Freshness', '/freshness', '⟳'], ['Trust', '/trust', '🛡'], ['Audit', '/audit-log', '▤']]],
  ['Integrate', [['Connect', '/connect', '⇄'], ['Sources', '/sources', '⎇'], ['Improve', '/improve', '↺']]],
  ['Foundry', [['Foundry', '/foundry', '⚗'], ['Workers', '/workers', '🛰']]],
  ['Account', [['Pricing', '/pricing', '$'], ['Settings', '/settings', '⚙'], ['Admin', '/admin', '⛨']]],
];
// ---- OHH brand for the kit chrome ----
const OHH_BRAND = { name: 'OpenHarnessHub', tld: '.io', glyph: '⎔', accent: 'var(--accent)' };
const OHH_GROUPS = NAV_GROUPS.map(([label, items]) => ({ label, items: items.map(([lb, p, ic]) => [p, ic, lb]), defaultOpen: ['Explore', 'Workspace'].includes(label) }));
function ohhActive(route) {
  return (p) => route === p || (p === '/build' && route === '/results') || (p === '/components' && route.startsWith('/c/')) || (p === '/run' && route === '/flow') || (p === '/requests' && route.startsWith('/requests'));
}

// Build pinned item (kit header slot) — keeps OHH's expandable Build menu
function BuildMenu({ route }) {
  const [open, setOpen] = React.useState(true);
  return (
    <div className="ohs-side-build" style={{ marginBottom: 4 }}>
      <button className={'ohs-side-link' + ((route === '/build' || route === '/drafts') ? ' on' : '')} style={{ width: '100%', fontWeight: 650 }} onClick={() => setOpen((o) => !o)}>
        <span className="g">✎</span>Build<span style={{ marginLeft: 'auto', fontSize: 10 }}>{open ? '▾' : '▸'}</span>
      </button>
      {open && <>
        <a className={'ohs-side-link' + (route === '/build' ? ' on' : '')} style={{ paddingLeft: 32 }} onClick={() => navigate('/build')}><span className="g">＋</span>New build</a>
        <a className={'ohs-side-link' + (route === '/drafts' ? ' on' : '')} style={{ paddingLeft: 32 }} onClick={() => navigate('/drafts')}><span className="g">▤</span>Drafts</a>
      </>}
    </div>
  );
}
// Credits + account (kit foot slot)
function OhhFoot() {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--fg-faint)', padding: '0 4px 6px' }}>
        <span>Credits</span>
        <span style={{ flex: 1, height: 4, borderRadius: 2, background: 'var(--line)', overflow: 'hidden', position: 'relative' }}><i style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '38%', background: 'var(--accent)' }} /></span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, padding: 4 }}>
        <span style={{ width: 26, height: 26, borderRadius: '50%', background: 'var(--accent-weak)', color: 'var(--accent)', display: 'grid', placeItems: 'center', fontSize: 12, fontWeight: 700, flex: '0 0 auto' }}>N</span>
        <span style={{ minWidth: 0, fontSize: 12.5, fontWeight: 600, color: 'var(--fg)', lineHeight: 1.2 }}>Nadia Okonkwo<small style={{ display: 'block', color: 'var(--fg-faint)', fontWeight: 400, fontSize: 10.5 }}>ESG · Acme Corp</small></span>
      </div>
    </>
  );
}
function AppShell({ route, crumb, children, bare }) {
  const { OhAppShell } = window;
  const parts = Array.isArray(crumb) ? crumb : [crumb];
  const topbar = (
    <>
      <div className="pt-crumb">{parts.map((p, i) => (
        <React.Fragment key={i}>{i > 0 && <span className="sep">/</span>}{i === parts.length - 1 ? <b>{p}</b> : <span>{p}</span>}</React.Fragment>
      ))}</div>
      <div className="pt-cmdk" style={{ marginLeft: 'auto' }} onClick={() => window.dispatchEvent(new CustomEvent('oh-cmdk'))}><span>⌕</span> Search or jump to…<span className="oh-kbd">⌘K</span></div>
    </>
  );
  return (
    <OhAppShell brand={OHH_BRAND} groups={OHH_GROUPS} isActive={ohhActive(route)} route={route}
      header={<BuildMenu route={route} />} foot={<OhhFoot />} topbar={topbar}>
      {children}
    </OhAppShell>
  );
}
function MarketingShell({ children }) {
  const { OhTopBar, OhFooter } = window;
  return (
    <div className="pt-mkt">
      <OhTopBar brand={OHH_BRAND}
        nav={[['Explore', '/pipelines'], ['SDG solutions', '/solutions'], ['Cases', '/cases'], ['Workspace', '/app'], ['Pricing', '/pricing']]}
        cta={{ label: 'Start free', href: '/signup' }} signInHref="/signin" />
      <div className="pt-mkt-body">
        {children}
        <OhFooter brand={OHH_BRAND} tagline="Open harness ecosystem · part of AI Done Right" cols={[
          ['Product', [['Explore', '/pipelines'], ['Build', '/build'], ['Pricing', '/pricing'], ['About', '/about'], ['Case studies', '/cases']]],
          ['Govern', [['Trust center', '/trust'], ['Freshness', '/freshness'], ['Audit', '/audit-log']]],
          ['Group', [['AI Done Right ↗', '../context-is-everything/Context is Everything.html'], ['Baltor.ai ↗', '../context-enrichment/Context Enrichment Prototype.html'], ['Teleon.dev ↗', '../teleon/Teleon Prototype.html']]],
        ]} />
      </div>
    </div>
  );
}

// ---- command palette ----
const CMDS = [
  ['Go to Landing', '/', '⌂'], ['Go to Build', '/build', '✎'], ['Explore pipelines', '/pipelines', '◫'], ['Explore components', '/components', '⬡'],
  ['Go to Workspace', '/app', '◫'], ['Open flow', '/flow', '⚡'], ['Run & trace', '/run', '▷'], ['Pricing', '/pricing', '$'],
  ['Dashboards', '/dashboards', '▦'], ['Foundry console', '/foundry', '⚗'], ['Import & Improve', '/improve', '↺'], ['Settings', '/settings', '⚙'],
  ['Private registry', '/registry', '🔒'], ['Connect · MCP', '/connect', '⇄'],
  ['Admin portal', '/admin', '⛨'], ['Internet workers', '/workers', '🛰'], ['Checkout', '/checkout', '$'],
  ['SDG solutions', '/solutions', '◎'], ['SDG 13 · Climate Action', '/solutions/13', '◎'],
  ['Freshness · verified feed', '/freshness', '⟳'], ['Certified export', '/attest', '✔'],
  ['Activity & notifications', '/activity', '◔'], ['Status & SLA', '/status', '◉'], ['Source search · GitHub', '/sources', '⎇'],
  ['Capability requests', '/requests', '◷'], ['Contribute · earn credits', '/contribute', '＋'],
  ['Trust center', '/trust', '🛡'], ['Audit log', '/audit-log', '▤'], ['Roles & permissions', '/roles', '⛨'], ['Publish to ecosystem', '/publish', '⇧'], ['Sign in', '/signin', '→'], ['Onboarding', '/onboarding', '✦'], ['Upgrade', '/upgrade', '🔒'],
  ['Component · Cite-first ESG counsel', '/c/esg-cite-first', '⚡'], ['Component · CSDDD article corpus', '/c/csddd-articles', '⛁'],
];
function CommandPalette({ onClose }) {
  const [q, setQ] = React.useState('');
  const [i, setI] = React.useState(0);
  const list = CMDS.filter((c) => c[0].toLowerCase().includes(q.toLowerCase()));
  const go = (idx) => { const c = list[idx]; if (c) { navigate(c[1]); onClose(); } };
  return (
    <div className="pt-cmdk-overlay" onClick={onClose}>
      <div className="pt-cmdk-modal" onClick={(e) => e.stopPropagation()}>
        <div className="pt-cmdk-input">
          <span style={{ color: 'var(--fg-faint)' }}>⌕</span>
          <input autoFocus placeholder="Search or jump to…" value={q}
            onChange={(e) => { setQ(e.target.value); setI(0); }}
            onKeyDown={(e) => {
              if (e.key === 'ArrowDown') { e.preventDefault(); setI((x) => Math.min(x + 1, list.length - 1)); }
              if (e.key === 'ArrowUp') { e.preventDefault(); setI((x) => Math.max(x - 1, 0)); }
              if (e.key === 'Enter') go(i);
              if (e.key === 'Escape') onClose();
            }} />
          <span className="oh-kbd">esc</span>
        </div>
        <div className="pt-cmdk-list">
          {list.map((c, idx) => (
            <div key={c[1] + c[0]} className={'pt-cmdk-item' + (idx === i ? ' on' : '')} onMouseEnter={() => setI(idx)} onClick={() => go(idx)}>
              <span className="ic">{c[2]}</span>{c[0]}{idx === i && <span className="k oh-kbd">↵</span>}
            </div>
          ))}
          {!list.length && <div className="pt-cmdk-item" style={{ color: 'var(--fg-faint)' }}>No matches</div>}
        </div>
      </div>
    </div>
  );
}

// ---- scheme switcher + tweaks (collapsible, bottom-left) ----
const TWEAK_GROUPS = [
  ['Text size', 'text', [['sm', 'Small'], ['md', 'Default'], ['lg', 'Large']]],
  ['Density', 'density', [['compact', 'Compact'], ['cozy', 'Cozy'], ['comfortable', 'Roomy']]],
  ['Intensity', 'intensity', [['calm', 'Calm'], ['balanced', 'Balanced'], ['vivid', 'Vivid']]],
];
function SchemeSwitcher({ scheme, setScheme, override, setOverride, effective, tweaks, setTweak }) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (!open) return undefined;
    const d = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const k = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', d, true); document.addEventListener('keydown', k);
    return () => { document.removeEventListener('pointerdown', d, true); document.removeEventListener('keydown', k); };
  }, [open]);
  const cur = SCHEMES.find((s) => s[0] === scheme) || SCHEMES[0];
  return (
    <div className={'oh-sw' + (open ? ' open' : '')} ref={ref}>
      {open && (
        <div className="oh-sw-panel" role="menu">
          <div className="oh-sw-head">Theme — preview any scheme</div>
          <div className="oh-sw-grid">
            {SCHEMES.map(([id, accent, short]) => (
              <button key={id} className={'oh-sw-opt' + (id === scheme ? ' on' : '')} onClick={() => setScheme(id)}>
                <span className="oh-sb-dot" style={{ background: accent }} /><span className="nm">{short}</span>
              </button>
            ))}
          </div>
          <div className="oh-sw-row col">
            <span className="oh-sw-name">Mode</span>
            <div className="oh-sb-toggle">
              {['light', 'dark'].map((m) => <button key={m} className={override === m ? 'on' : ''} onClick={() => setOverride(m)}>{m[0].toUpperCase() + m.slice(1)}</button>)}
              <button className={override === null ? 'on' : ''} onClick={() => setOverride(null)}>Auto</button>
            </div>
          </div>
          <div className="oh-sw-head" style={{ margin: '14px 0 10px' }}>Tweaks — fit the UI to you</div>
          {TWEAK_GROUPS.map(([label, key, opts]) => (
            <div className="oh-sw-row col" key={key} style={{ marginBottom: 8 }}>
              <span className="oh-sw-name">{label}</span>
              <div className="oh-sb-toggle">
                {opts.map(([v, lbl]) => (
                  <button key={v} className={tweaks[key] === v ? 'on' : ''} onClick={() => setTweak(key, v)}>{lbl}</button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
      <button className="oh-sw-trigger" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <span className="oh-sb-dot" style={{ background: cur[1] }} /><span className="lbl">Theme</span>
        <span>{cur[2]} · {effective[0].toUpperCase() + effective.slice(1)}</span>
        <svg className="cv" width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"><path d="M2 7l3.5-3.5L9 7" /></svg>
      </button>
    </div>
  );
}

function App() {
  const route = useHashRoute();
  const [task, setTask] = React.useState('');
  const [toasts, setToasts] = React.useState([]);
  const [palette, setPalette] = React.useState(false);
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const [scheme, setScheme] = React.useState(() => localStorage.getItem('ohp-scheme') || 's');
  const [override, setOverride] = React.useState(() => { const v = localStorage.getItem('ohp-mode'); return v === 'light' || v === 'dark' ? v : null; });
  const [tweaks, setTweaks] = React.useState(() => {
    const d = { text: 'md', density: 'cozy', intensity: 'balanced' };
    try { return { ...d, ...JSON.parse(localStorage.getItem('ohp-tweaks') || '{}') }; } catch (e) { return d; }
  });
  const setTweak = React.useCallback((k, v) => setTweaks((t) => { const n = { ...t, [k]: v }; try { localStorage.setItem('ohp-tweaks', JSON.stringify(n)); } catch (e) {} return n; }), []);
  React.useEffect(() => { try { localStorage.setItem('ohp-scheme', scheme); } catch (e) {} }, [scheme]);
  React.useEffect(() => { try { localStorage.setItem('ohp-mode', override || 'auto'); } catch (e) {} }, [override]);

  // legacy-route redirects (IA cleanup): /browse folded into /components; /marketplace + /explore into Explore
  const REDIRECTS = { '/browse': '/components', '/marketplace': '/pipelines', '/explore': '/pipelines' };
  React.useEffect(() => { if (REDIRECTS[route]) navigate(REDIRECTS[route]); }, [route]);

  const toast = React.useCallback((msg) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((t) => [...t, { id, msg }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 2600);
  }, []);

  React.useEffect(() => {
    const open = () => setPalette(true);
    const key = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette((p) => !p); }
    };
    window.addEventListener('oh-cmdk', open); window.addEventListener('keydown', key);
    return () => { window.removeEventListener('oh-cmdk', open); window.removeEventListener('keydown', key); };
  }, []);

  const autoTheme = (MKT_ROUTES.includes(route) || route.startsWith('/for/')) ? 'light' : 'dark';
  const effective = override || autoTheme;
  const [loggedIn, setLoggedInRaw] = React.useState(() => { try { return localStorage.getItem('ohp-auth') === '1'; } catch (e) { return false; } });
  const setLoggedIn = (v) => { setLoggedInRaw(v); try { localStorage.setItem('ohp-auth', v ? '1' : '0'); } catch (e) {} };
  React.useEffect(() => {  // live seam: real realm session ⇒ app mode (reflects real state only)
    const sync = () => {
      try {
        const s = window.OHIdentity && OHIdentity.session(OHIdentity.realmOf(OHH_BRAND));
        if (s && s.session_id) setLoggedIn(true);
      } catch (e) {}
    };
    sync();
    window.addEventListener('hashchange', sync);
    return () => window.removeEventListener('hashchange', sync);
  }, []);
  const store = React.useMemo(() => ({ task, setTask, toast, loggedIn, setLoggedIn }), [task, toast, loggedIn]);

  let body;
  if (route === '/') body = <PLanding />;
  else if (route === '/pricing') body = <MarketingShell><PPricing /></MarketingShell>;
  else if (route === '/trust') body = <MarketingShell><PTrustCenter /></MarketingShell>;
  else if (route === '/about') body = <MarketingShell><window.OhAbout brand={OHH_BRAND} /></MarketingShell>;
  else if (route === '/cases') body = <MarketingShell><window.OhCaseStudies brand={OHH_BRAND} cases={(window.CASES && window.CASES.openharnesshub) || []} /></MarketingShell>;
  else if (route.startsWith('/cases/')) body = <MarketingShell><window.OhCaseStudy brand={OHH_BRAND} cases={(window.CASES && window.CASES.openharnesshub) || []} id={route.slice(7)} cta={{ label: 'Start free →', href: '/signup' }} /></MarketingShell>;
  else if (route === '/signin' || route === '/signup') body = <PSignin />;
  else if (route === '/onboarding') body = <POnboarding />;
  else if (route === '/upgrade') body = <PUpgrade />;
  else if (route === '/preview') body = <PPreview />;
  else if (route.startsWith('/for/')) body = <PUseCase who={route.slice(5)} />;
  else {
    let page, crumb, bare = false;
    if (route === '/build') { page = <PBuild />; crumb = 'Build'; }
    else if (route === '/results') { page = <PResults />; crumb = ['Build', 'Results']; }
    else if (route === '/flow') { page = <PFlow />; crumb = 'flow/csddd-grade'; bare = true; }
    else if (route === '/run') { page = <PRun />; crumb = ['flow/csddd-grade', 'Run']; }
    else if (route === '/pipelines') { page = <PBrowse kind="pipeline" />; crumb = 'Explore pipelines'; }
    else if (route === '/components') { page = <PBrowse kind="component" />; crumb = 'Explore components'; }
    else if (route === '/app') { page = <PDashboard />; crumb = 'Workspace'; }
    else if (route === '/drafts') { page = <PDashboard />; crumb = 'Drafts'; }
    else if (route === '/dashboards') { page = <PDashboards />; crumb = 'Dashboards'; }
    else if (route === '/foundry') { page = <PFoundry />; crumb = 'Foundry'; }
    else if (route === '/improve') { page = <PImprove />; crumb = 'Import & Improve'; }
    else if (route === '/settings') { page = <PSettings />; crumb = 'Settings'; }
    else if (route === '/registry') { page = <PRegistry />; crumb = 'Private registry'; }
    else if (route === '/connect') { page = <PConnect />; crumb = 'Connect'; }
    else if (route === '/admin') { page = <PAdmin />; crumb = 'Admin'; }
    else if (route === '/workers') { page = <PWorkers />; crumb = 'Internet workers'; }
    else if (route === '/checkout') { page = <PCheckout />; crumb = ['Pricing', 'Checkout']; }
    else if (route === '/solutions') { page = <PSolutions />; crumb = 'SDG solutions'; }
    else if (route === '/freshness') { page = <PFreshness />; crumb = 'Freshness'; }
    else if (route === '/attest') { page = <PAttest />; crumb = ['Freshness', 'Certified export']; }
    else if (route === '/activity') { page = <PActivity />; crumb = 'Activity'; }
    else if (route === '/status') { page = <PStatus />; crumb = 'Status'; }
    else if (route === '/sources') { page = <PSources />; crumb = 'Source search'; }
    else if (route === '/requests') { page = <PRequests />; crumb = 'Capability requests'; }
    else if (route.startsWith('/requests/')) { page = <PRequestDetail id={route.slice(10)} />; crumb = ['Requests', route.slice(10)]; }
    else if (route === '/contribute') { page = <PContribute />; crumb = 'Contribute'; }
    else if (route === '/publish') { page = <PPublish />; crumb = 'Publish'; }
    else if (route.startsWith('/k/')) { page = <PKnowledgeEntry id={route.slice(3)} />; crumb = ['Knowledge', 'Entry']; }
    else if (route.startsWith('/p/')) { page = <PProvenance id={route.slice(3)} />; crumb = 'Provenance'; }
    else if (route === '/audit-log') { page = <PAuditLog />; crumb = 'Audit log'; }
    else if (route === '/roles') { page = <PRoles />; crumb = 'Roles'; }
    else if (route.startsWith('/solutions/')) { page = <PSolution n={route.slice(11)} />; crumb = ['SDG solutions', 'Goal ' + route.slice(11)]; }
    else if (route.startsWith('/c/')) { page = <PDetail slug={route.slice(3)} />; crumb = ['Explore', 'Detail']; }
    else { page = <window.OhNotFound brand={OHH_BRAND} home="/" links={[['Explore', '/pipelines'], ['Build', '/build']]} />; crumb = 'Not found'; }
    if (!body) body = <AppShell route={route} crumb={crumb} bare={bare}>{page}</AppShell>;
  }

  const TW_CLS = {
    text: { sm: 'tw-text-sm', md: '', lg: 'tw-text-lg' },
    density: { compact: 'tw-dens-compact', cozy: '', comfortable: 'tw-dens-comfortable' },
    intensity: { calm: 'tw-int-calm', balanced: '', vivid: 'tw-int-vivid' },
  };
  const tweakCls = [TW_CLS.text[tweaks.text], TW_CLS.density[tweaks.density], TW_CLS.intensity[tweaks.intensity]].filter(Boolean).join(' ');

  return (
    <StoreCtx.Provider value={store}>
      <div className={`oh dir-${scheme} theme-${effective} pt-root ${tweakCls}`}>
        {body}
        <div className="pt-toasts">{toasts.map((t) => <div key={t.id} className="pt-toast"><span className="gl">✓</span>{t.msg}</div>)}</div>
        {palette && <CommandPalette onClose={() => setPalette(false)} />}
        <SchemeSwitcher scheme={scheme} setScheme={setScheme} override={override} setOverride={setOverride} effective={effective} tweaks={tweaks} setTweak={setTweak} />
      </div>
    </StoreCtx.Provider>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
