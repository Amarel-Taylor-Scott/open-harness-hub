/* global React, navigate, BRANDCE, TIER_META, STATUS_META */
// Context Enrichment — brand chrome + shared atoms (standalone brand).

// ---- brand mark: three tiers compressing (raw → compressed → hyper) ----
function CEMark({ s = 26 }) {
  return (
    <span className="ce-mark" style={{ width: s, height: s }} aria-hidden="true">
      <svg viewBox="0 0 24 24" width={s} height={s}>
        <rect x="3" y="5"  width="18" height="3.4" rx="1.4" fill="var(--accent-ink)" opacity="0.95" />
        <rect x="3" y="10.3" width="12" height="3.4" rx="1.4" fill="var(--accent-ink)" opacity="0.72" />
        <rect x="3" y="15.6" width="6"  height="3.4" rx="1.4" fill="var(--accent-ink)" opacity="0.5" />
      </svg>
    </span>
  );
}

function CELogo({ compact = false }) {
  return (
    <a className="ce-logo" onClick={() => navigate('/')}>
      <span className="ce-logo-mk"><CEMark s={compact ? 22 : 26} /></span>
      {!compact && <span className="ce-logo-name">{BRANDCE.wordmark || BRANDCE.name}</span>}
    </a>
  );
}

// ---- the endorsement: "supported by OpenHubForAI" (never a switcher) ----
function SupportedBy({ block = false }) {
  const s = BRANDCE.supportedBy;
  if (!s) return null;
  return (
    <a className={'ce-supported' + (block ? ' block' : '')} href={s.url} title={'A sister product · ' + s.name}>
      <span className="lbl">sister product</span>
      <span className="oh">{'\u2388'} {s.name}</span>
    </a>
  );
}

// ---- theme toggle (light/dark) ----
function ThemeToggle({ compact }) {
  const ctx = React.useContext(window.CEStore) || {};
  if (!ctx.toggleTheme) return null;
  return (
    <button className={'ce-theme-toggle' + (compact ? ' compact' : '')} onClick={ctx.toggleTheme}
      aria-label="Toggle light or dark theme" title="Toggle light / dark">
      {ctx.theme === 'dark' ? '☀' : '☾'}
    </button>
  );
}

// ---- marketing top bar (landing) ----
const MKT_NAV = [['Why', '/why', 'route'], ['How it works', '/engine', 'route'], ['Cases', '/cases', 'route'], ['Commons', '/commons', 'route'], ['Docs', '/docs', 'route'], ['Pricing', '/pricing', 'route']];
function scrollToId(id) {
  const el = document.getElementById(id);
  if (el) window.scrollTo({ top: window.scrollY + el.getBoundingClientRect().top - 78, behavior: 'smooth' });
}
function MarketingTop() {
  const go = (target, type) => {
    if (type === 'route') { navigate(target); return; }
    if (window.location.hash && window.location.hash !== '#/') { navigate('/'); setTimeout(() => scrollToId(target), 80); }
    else scrollToId(target);
  };
  return (
    <header className="ce-top mkt">
      <div className="ce-top-l"><CELogo /></div>
      <window.OhPortfolioMenu />
      <span className="ce-spacer" />
      <nav className="ce-top-nav">
        {MKT_NAV.map(([l, t, k]) => <a key={l} onClick={() => go(t, k)}>{l}</a>)}
      </nav>
      <div className="ce-top-r">
        <ThemeToggle />
        <a className="ce-navlink" onClick={() => navigate('/signin')}>Sign in</a>
        <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => navigate('/signup')}>Start free</button>
      </div>
    </header>
  );
}

// ---- app shell: sidebar + topbar (for the product pages) ----
const APP_NAV = [
  ['/dashboard', '▤', 'Dashboard'],
  ['/sources', '⎇', 'Sources'],
  ['/pipeline', '◈', 'Engine'],
  ['/corpora', '▦', 'Corpora'],
  ['/commons', '⬡', 'Commons'],
  ['/ingest', '⇥', 'Ingest'],
  ['/verify', '⇄', 'Verify'],
  ['/serve', '◎', 'Serve'],
  ['/audit', '⚖', 'Audit'],
  ['/governance', '⛨', 'Governance'],
  ['/billing', '◷', 'Billing'],
  ['/settings', '⚙', 'Settings'],
];
function AppShell({ route, children }) {
  const active = (h) => route === h || route.startsWith(h + '/') || (h === '/corpora' && route.startsWith('/c/'));
  const CMDS = [
    ...window.OhCommandK.fromNav(APP_NAV),
    { label: 'Home', href: '/', icon: '⌂', group: 'Marketing' },
    { label: 'Why Baltor', href: '/why', icon: 'ⓘ', group: 'Marketing' },
    { label: 'How it works', href: '/engine', icon: '◈', group: 'Marketing' },
    { label: 'Case studies', href: '/cases', icon: '★', group: 'Marketing' },
    { label: 'Pricing', href: '/pricing', icon: '◷', group: 'Marketing' },
    { label: 'Docs', href: '/docs', icon: '▭', group: 'Marketing' },
    { label: 'Usage', href: '/usage', icon: '◑', group: 'Account' },
  ];
  return (
    <div className="ce-app">
      <aside className="ce-side">
        <div className="ce-side-top"><CELogo /></div>
        <button className="ohs-side-search" style={{ margin: '0 0 6px' }} onClick={() => window.dispatchEvent(new CustomEvent('oh-cmdk'))}><span className="ohs-side-search-l"><span aria-hidden="true">⌕</span> Search…</span><span className="oh-kbd">⌘K</span></button>
        <nav className="ce-side-nav">
          {APP_NAV.map(([h, g, l]) => (
            <a key={h} className={'ce-side-link' + (active(h) ? ' on' : '')} onClick={() => navigate(h)}>
              <span className="g">{g}</span>{l}
            </a>
          ))}
        </nav>
        <div className="ce-side-foot">
          <a className="ce-acct" onClick={() => navigate('/settings')}>
            <span className="ce-acct-av">A</span>
            <span className="ce-acct-id"><span className="nm">Acme · Compliance</span><span className="pl">Pro · 4 seats</span></span>
          </a>
          <button className="oh-btn oh-btn--primary oh-btn--sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => navigate('/ingest')}>+ New corpus</button>
          <div className="ce-side-foot-row"><ThemeToggle compact /></div>
        </div>
      </aside>
      <main className="ce-main-col">{children}</main>
      <window.OhCommandK commands={CMDS} placeholder="Search Baltor…" />
    </div>
  );
}

// ---- shared atoms ----
function StatusBadge({ status }) {
  const m = STATUS_META[status] || STATUS_META.draft;
  return <span className={'oh-badge ' + m.cls}><span className="gl">{m.gl}</span>{m.label}</span>;
}
function TierDot({ tier }) {
  const m = TIER_META[tier];
  return <span className="ce-tierdot" style={{ background: m.tone }} title={m.label} />;
}
function Meter({ pct, tone }) {
  return <div className="ce-meter"><i style={{ width: Math.max(2, pct) + '%', background: tone || 'var(--accent)' }} /></div>;
}
function PageHead({ eyebrow, title, sub, actions }) {
  return (
    <div className="ce-pagehead">
      <div>
        {eyebrow && <div className="ce-eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {sub && <p>{sub}</p>}
      </div>
      {actions && <div className="ce-pagehead-actions">{actions}</div>}
    </div>
  );
}

Object.assign(window, { CEMark, CELogo, SupportedBy, MarketingTop, AppShell, StatusBadge, TierDot, Meter, PageHead, ThemeToggle });
