/* global React */
// shared/oh-site.jsx — SHARED SITE KIT (React components + primitive pages).
// New brands (Teleon, Open*Hubs) compose these so chrome + primitive pages are
// identical house-wide; only the brand config (name, accent, nav) differs.
//
// Load AFTER React + oh-site.css. Exports to window via Object.assign at end.
// Shared hooks here (useHashRoute/navigate/useSiteTheme) so new sites don't
// re-implement routing/theming.

// ---------- shared hooks ----------
function useHashRoute() {
  const [route, setRoute] = React.useState(() => window.location.hash.slice(1) || '/');
  React.useEffect(() => {
    const on = () => setRoute(window.location.hash.slice(1) || '/');
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return route;
}
function navigate(to) { window.location.hash = to; }

function useSiteTheme(key) {
  const k = key || 'oh-theme';
  const [theme, setTheme] = React.useState(() => {
    try { const s = localStorage.getItem(k); if (s === 'light' || s === 'dark') return s; } catch (e) {}
    return 'light';  // all sites default to light (bright) mode; the header toggle still switches to dark
  });
  React.useEffect(() => { try { localStorage.setItem(k, theme); } catch (e) {} }, [k, theme]);
  return [theme, React.useCallback(() => setTheme((t) => (t === 'dark' ? 'light' : 'dark')), [])];
}

// brand: { name, tld?, glyph, accent, home? }
function brandName(brand) {
  if (brand.tld) return <span className="ohs-logo-name">{brand.name}<span className="tld">{brand.tld}</span></span>;
  return <span className="ohs-logo-name">{brand.name}</span>;
}

// ---------- chrome ----------
function OhLogo({ brand, onClick }) {
  return (
    <a className="ohs-logo" onClick={onClick || (() => navigate('/'))}>
      <span className="ohs-logo-mk" style={{ background: brand.accent }}>{brand.glyph}</span>
      {brandName(brand)}
    </a>
  );
}

function OhThemeToggle({ theme, onToggle }) {
  return (
    <button className="ohs-theme" onClick={onToggle} aria-label="Toggle light or dark theme" title="Toggle light / dark">
      {theme === 'dark' ? '☀' : '☾'}
    </button>
  );
}

// ---- portfolio switcher: cross-site app menu, driven by window.PORTFOLIO (products.js) ----
// No-ops if PORTFOLIO isn't loaded. Auto-detects the current site from the URL folder.
function OhPortfolioMenu() {
  const P = (typeof window !== 'undefined') && window.PORTFOLIO;
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', onDoc, true);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDoc, true); document.removeEventListener('keydown', onKey); };
  }, [open]);
  if (!P) return null;
  const folderOf = (url) => { const p = (url || '').split('/'); return p[p.length - 2] || ''; };
  const isCurrent = (e) => { const f = folderOf(e.url); return !!f && window.location.pathname.indexOf('/' + f + '/') !== -1; };
  return (
    <div className={'ohs-pf' + (open ? ' open' : '')} ref={ref}>
      <button className="ohs-pf-btn" aria-expanded={open} aria-haspopup="menu"
        aria-label={'Switch products \u2014 ' + P.GROUP.name} title={'Switch products \u2014 ' + P.GROUP.name}
        onClick={() => setOpen((o) => !o)}>
        <span className="ohs-pf-grid" aria-hidden="true">⬢</span>
        <span className="ohs-pf-cv" aria-hidden="true">▾</span>
      </button>
      {open && (
        <div className="ohs-pf-menu" role="menu">
          <div className="ohs-pf-head">{P.GROUP.name}</div>
          {P.LAYERS.map((layer) => (
            <div className="ohs-pf-section" key={layer.id}>
              <div className="ohs-pf-seclabel">{layer.label}</div>
              {layer.items.map((id) => {
                const e = P.ENTITIES[id]; if (!e) return null;
                const cur = isCurrent(e);
                return (
                  <a key={id} className={'ohs-pf-item' + (cur ? ' cur' : '')} role="menuitem"
                    href={cur ? undefined : e.url} aria-current={cur ? 'page' : undefined}>
                    <span className="ohs-pf-mk" style={{ '--ent': e.accent }} aria-hidden="true">{e.glyph}</span>
                    <span className="ohs-pf-id"><span className="nm">{e.wordmark || e.name}</span><span className="kd">{e.kind}</span></span>
                    {cur && <span className="ohs-pf-here">Here</span>}
                  </a>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// nav: [ [label, href], … ]  · cta: { label, href }
function OhTopBar({ brand, nav, cta, signInHref, theme, onToggle }) {
  return (
    <header className="ohs-top">
      <OhLogo brand={brand} />
      <span className="ohs-spacer" />
      <nav className="ohs-top-nav">
        {nav && nav.map(([l, h]) => <a key={l} onClick={() => navigate(h)}>{l}</a>)}
        <a key="__demo" style={{ fontWeight: 600 }} onClick={() => navigate('/demo')}>Demo</a>
      </nav>
      <div className="ohs-top-r">
        {onToggle && <OhThemeToggle theme={theme} onToggle={onToggle} />}
        {signInHref && <a className="ohs-navlink" onClick={() => navigate(signInHref)}>Sign in</a>}
        {cta && <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => navigate(cta.href)}>{cta.label}</button>}
      </div>
    </header>
  );
}

// ---------- hero ----------
// title accepts a node; lede string; ctas: [ {label, href, primary?}, … ]
function OhHero({ eyebrow, title, lede, ctas, aside }) {
  return (
    <section className="ohs-hero">
      <div className={'ohs-wrap' + (aside ? ' ohs-hero-grid' : '')}>
        <div>
          {eyebrow && <div className="ohs-eyebrow">{eyebrow}</div>}
          <h1>{title}</h1>
          {lede && <p className="lede">{lede}</p>}
          {ctas && (
            <div className="ohs-cta">
              {ctas.map((c) => (
                <button key={c.label} className={'oh-btn ' + (c.primary ? 'oh-btn--primary' : 'oh-btn--ghost')} onClick={c.onClick || (() => navigate(c.href))}>{c.label}</button>
              ))}
            </div>
          )}
        </div>
        {aside}
      </div>
    </section>
  );
}

function OhSection({ label, title, body, children, id }) {
  return (
    <section className="ohs-section" id={id}>
      <div className="ohs-wrap">
        {label && <div className="ohs-section-label">{label}</div>}
        {title && <h2>{title}</h2>}
        {body && <div className="ohs-body">{body}</div>}
        {children}
      </div>
    </section>
  );
}

// features: [ [glyph, title, desc], … ]
function OhFeatures({ items }) {
  return (
    <div className="ohs-grid-3">
      {items.map(([g, t, d]) => (
        <div className="oh-card ohs-feature" key={t}><div className="fi">{g}</div><h4>{t}</h4><p>{d}</p></div>
      ))}
    </div>
  );
}

function OhBand({ title, sub, ctas }) {
  return (
    <section className="ohs-band">
      <div className="ohs-wrap">
        <h2>{title}</h2>
        {sub && <p>{sub}</p>}
        <div className="ohs-cta">
          {ctas.map((c) => (
            <button key={c.label} className={'oh-btn ' + (c.primary ? 'oh-btn--primary' : 'oh-btn--ghost')} onClick={() => navigate(c.href)}>{c.label}</button>
          ))}
        </div>
      </div>
    </section>
  );
}

// cols: [ [heading, [ [label, href], … ] ], … ]
function OhFooter({ brand, tagline, cols }) {
  return (
    <footer className="ohs-foot">
      <div className="ohs-wrap ohs-foot-grid">
        <div>
          <div className="ohs-logo" style={{ marginBottom: 8 }}>
            <span className="ohs-logo-mk" style={{ background: brand.accent, width: 22, height: 22 }}>{brand.glyph}</span>
            <span className="ohs-foot-name">{brand.name}{brand.tld || ''}</span>
          </div>
          {tagline && <div className="ohs-foot-tag">{tagline}</div>}
        </div>
        <div className="ohs-foot-cols">
          {cols.map(([h, links]) => (
            <div className="ohs-foot-col" key={h}>
              <h5>{h}</h5>
              {links.map(([l, href]) => (
                href && (href.indexOf('../') === 0 || href.indexOf('http') === 0)
                  ? <a key={l} href={href}>{l}</a>
                  : <a key={l} onClick={() => href && navigate(href)}>{l}</a>
              ))}
            </div>
          ))}
        </div>
      </div>
    </footer>
  );
}

// ---------- app shell ----------
// nav: [ [href, glyph, label], … ] (flat)  OR  groups: [ {label, items:[[href,glyph,label]], defaultOpen} ]
// optional slots: header (above nav, e.g. a pinned action), foot (replaces default footer),
// topbar (a sticky bar above the page), isActive(href) (override active detection).
function OhNavGroup({ grp, isActive }) {
  const [open, setOpen] = React.useState(grp.defaultOpen !== false);
  return (
    <div className={'ohs-side-group' + (open ? ' open' : '')}>
      <button className="ohs-side-sec" onClick={() => setOpen((o) => !o)}><span>{grp.label}</span><span className="cv">{open ? '▾' : '▸'}</span></button>
      {open && grp.items.map(([h, g, l]) => (
        <a key={h} className={'ohs-side-link' + (isActive(h) ? ' on' : '')} onClick={() => navigate(h)}><span className="g">{g}</span>{l}</a>
      ))}
    </div>
  );
}
function OhAppShell({ brand, nav, groups, header, foot, topbar, isActive, route, cta, theme, onToggle, children }) {
  const r = route || '';  // null-safe: OhLayout(variant="sidebar") may omit route
  const active = isActive || ((h) => r === h || r.startsWith(h + '/'));
  return (
    <div className="ohs-app">
      <aside className="ohs-side">
        <div className="ohs-side-top"><OhLogo brand={brand} /></div>
        {header}
        <nav className="ohs-side-nav">
          {nav && nav.map(([h, g, l]) => (
            <a key={h} className={'ohs-side-link' + (active(h) ? ' on' : '')} onClick={() => navigate(h)}><span className="g">{g}</span>{l}</a>
          ))}
          {groups && groups.map((grp) => <OhNavGroup key={grp.label} grp={grp} isActive={active} />)}
        </nav>
        <div className="ohs-side-foot">
          {foot || (
            <>
              {cta && <button className="oh-btn oh-btn--primary oh-btn--sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => navigate(cta.href)}>{cta.label}</button>}
              <div className="ohs-side-foot-row">
                <a className="ohs-navlink" onClick={() => navigate('/settings')}>Settings</a>
                {onToggle && <OhThemeToggle theme={theme} onToggle={onToggle} />}
              </div>
            </>
          )}
        </div>
      </aside>
      <main className="ohs-main">
        {topbar && <div className="ohs-topbar">{topbar}</div>}
        <OhPreviewBanner />
        {children}
      </main>
    </div>
  );
}

// Honest preview indicator: when sign-up fell to the in-tab preview path (identity service
// offline) we set sessionStorage 'oh-preview'; this banner makes that visible so a preview
// is never mistaken for a real, saved account. (Fixes the silent no-session fallback.)
function OhPreviewBanner() {
  const [show, setShow] = React.useState(() => { try { return sessionStorage.getItem('oh-preview') === '1'; } catch (e) { return false; } });
  if (!show) return null;
  return (
    <div className="ohs-preview-banner" role="status" aria-live="polite"
      style={{ background: 'var(--accent-weak)', border: '1px solid color-mix(in srgb, var(--accent) 35%, var(--line))', borderRadius: 'var(--r-md)', padding: '9px 14px', margin: '0 0 14px', fontSize: 12.5, lineHeight: 1.5, display: 'flex', gap: 10, alignItems: 'center' }}>
      <span style={{ color: 'var(--accent)' }}>◷</span>
      <span><b>Preview mode.</b> The identity service is offline, so this session is <b>not saved</b> — sign-up did not create a real account. Start the local services to use a real realm account.</span>
      <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ marginLeft: 'auto' }}
        onClick={() => { try { sessionStorage.removeItem('oh-preview'); } catch (e) {} setShow(false); }}>Dismiss</button>
    </div>
  );
}

function OhPageHead({ eyebrow, title, sub, actions }) {
  return (
    <div className="ohs-pagehead">
      <div>
        {eyebrow && <div className="ohs-eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {sub && <p>{sub}</p>}
      </div>
      {actions && <div className="ohs-pagehead-actions">{actions}</div>}
    </div>
  );
}

// rollup: [ [label, value], … ]
function OhRollup({ items }) {
  return (
    <div className="ohs-rollup">
      {items.map(([k, v]) => <div className="oh-card ohs-roll" key={k}><div className="v">{v}</div><div className="k">{k}</div></div>)}
    </div>
  );
}

// ---------- LAYOUT PRIMITIVE: the standardized page skeleton ----------
// One skeleton for every page. `variant` picks the body layout; it composes the existing OhTopBar / OhAppShell /
// OhFooter so there is exactly one place a page declares its shape.
//   'sidebar'    -> the left-sidebar app shell (logged-in app); pass `sidebar` = the OhAppShell nav.
//   'one-col'    -> centered single readable column (docs, settings, simple forms).
//   'two-col'    -> main content + a sticky `aside` (content with a rail).
//   'no-sidebar' -> full-width content (marketing, wide tables / browsers).
function OhLayout({ variant = 'one-col', brand, nav, sidebar, cta, signInHref, theme, onToggle,
                   footer = true, footerProps, aside, groups, header, foot, isActive, route, children }) {
  if (variant === 'sidebar') {
    // the logged-in app shell: forward the full OhAppShell surface (route -> active highlight, custom foot/header/groups)
    return (
      <OhAppShell brand={brand} nav={sidebar} groups={groups} header={header} foot={foot}
        isActive={isActive} route={route} cta={cta} theme={theme} onToggle={onToggle}>{children}</OhAppShell>
    );
  }
  const cls = variant === 'two-col' ? 'ohl-two' : variant === 'no-sidebar' ? 'ohl-full' : 'ohl-one';
  return (
    <div className="ohl">
      <OhTopBar brand={brand} nav={nav} cta={cta} signInHref={signInHref} theme={theme} onToggle={onToggle} />
      <main className={'ohl-body ' + cls}>
        <div className="ohs-wrap">
          {variant === 'two-col'
            ? <div className="ohl-two-grid"><div className="ohl-main">{children}</div><aside className="ohl-aside">{aside}</aside></div>
            : children}
        </div>
      </main>
      {footer && <OhFooter brand={brand} {...(footerProps || {})} />}
    </div>
  );
}

// ---------- DATA TABLE PRIMITIVE: standardized, optionally sortable, click-through rows ----------
// cols: [ {key, label, render?(row), width?, align?, sortable?, sortValue?(row)} ]; rows: [obj];
// rowKey?(row); onRow?(row); empty?; dense?.  Used by the OpenHubForAI record browsers and the AIDevObserver lists.
function OhTable({ cols, rows, rowKey, onRow, empty = 'No records.', dense }) {
  const [sort, setSort] = React.useState(null);
  const sorted = React.useMemo(() => {
    if (!sort) return rows || [];
    const c = cols.find((x) => x.key === sort.key);
    const get = (r) => (c && c.sortValue ? c.sortValue(r) : r[sort.key]);
    return [...(rows || [])].sort((a, b) => {
      const av = get(a), bv = get(b);
      const r = av < bv ? -1 : av > bv ? 1 : 0;
      return sort.dir === 'desc' ? -r : r;
    });
  }, [rows, sort, cols]);
  const toggle = (key) => setSort((s) => (s && s.key === key ? (s.dir === 'asc' ? { key, dir: 'desc' } : null) : { key, dir: 'asc' }));
  if (!rows || !rows.length) return <div className="ohl-empty">{empty}</div>;
  return (
    <div className="ohl-tablewrap">
      <table className={'ohl-table' + (dense ? ' ohl-table--dense' : '')}>
        <thead><tr>{cols.map((c) => (
          <th key={c.key} style={{ width: c.width, textAlign: c.align }} className={c.sortable ? 'ohl-th-sort' : ''}
              onClick={c.sortable ? () => toggle(c.key) : undefined}>
            {c.label}{c.sortable && sort && sort.key === c.key && <span className="ohl-caret">{sort.dir === 'asc' ? ' ▲' : ' ▼'}</span>}
          </th>
        ))}</tr></thead>
        <tbody>{sorted.map((r) => (
          <tr key={rowKey ? rowKey(r) : r.id} className={onRow ? 'ohl-row-click' : ''} onClick={onRow ? () => onRow(r) : undefined}>
            {cols.map((c) => <td key={c.key} style={{ textAlign: c.align }}>{c.render ? c.render(r) : r[c.key]}</td>)}
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

// ---------- PRIMITIVE PAGES ----------
// mode: 'signin' | 'signup' | 'forgot' — self-navigating via the kit's hash router
function OhAuth({ brand, mode }) {
  const signup = mode === 'signup';
  const forgot = mode === 'forgot';
  const [sent, setSent] = React.useState(false);
  const [email, setEmail] = React.useState('');
  const [pass, setPass] = React.useState('');
  const [name, setName] = React.useState('');
  const [err, setErr] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const bn = brand.name + (brand.tld || '');
  const realm = window.OHIdentity ? window.OHIdentity.realmOf(brand) : (brand.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');

  // WIRED to the real identity service (scripts/identity_local_service.py). Honest: if the service
  // is unreachable we fall to the in-tab preview path (flagged), never faking a real session.
  async function submitAuth() {
    setErr('');
    if (!email || email.indexOf('@') < 0) { setErr('Enter a valid work email.'); return; }
    if (pass.length < 8) { setErr('Use a passphrase of at least 8 characters.'); return; }
    // Preview path (no client or service down): flag it so the dashboard shows the preview
    // banner — never let an unsaved preview look like a real, persisted sign-up.
    const enterPreview = () => { try { sessionStorage.setItem('oh-preview', '1'); } catch (e) {} navigate('/dashboard'); };
    if (!window.OHIdentity) { enterPreview(); return; }
    setBusy(true);
    let live = false;
    try { live = await window.OHIdentity.available(); } catch (e) {}
    if (!live) { setBusy(false); enterPreview(); return; } // preview path — identity service down
    try {
      const r = signup ? await window.OHIdentity.signup(realm, email, pass) : await window.OHIdentity.login(realm, email, pass);
      setBusy(false);
      if (r && r.ok) { try { sessionStorage.removeItem('oh-preview'); } catch (e) {} navigate('/dashboard'); }  // real session — clear any stale preview flag
      else { setErr((r && r.error) || 'Authentication failed (this brand may not have a live realm yet).'); }
    } catch (e) { setBusy(false); setErr('Service error — please try again.'); }
  }
  const SEAM = 'Social sign-in is coming soon — use your email to continue.';

  return (
    <div className="ohs-auth">
      <div className="oh-card ohs-auth-card">
        <div className="ohs-auth-logo"><OhLogo brand={brand} /></div>
        {forgot ? (
          sent ? (
            <>
              <h1>Check your email</h1>
              <div className="sub">If an account exists for that address, a reset link is on its way (rendered to the local outbox in preview).</div>
              <button className="oh-btn oh-btn--primary" onClick={() => navigate('/signin')}>Back to sign in</button>
            </>
          ) : (
            <>
              <h1>Reset your password</h1>
              <div className="sub">Enter your email and we’ll send you a reset link.</div>
              <label className="oh-field"><span>Work email</span><input type="email" placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
              <button className="oh-btn oh-btn--primary" onClick={() => setSent(true)}>Send reset link</button>
              <div className="ohs-auth-alt"><a onClick={() => navigate('/signin')}>← Back to sign in</a></div>
            </>
          )
        ) : (
          <>
            <h1>{signup ? 'Create your account' : 'Welcome back'}</h1>
            <div className="sub">{signup ? `Start building on ${bn}.` : `Sign in to ${bn}.`}</div>
            {/* Social login (Continue with Google / GitHub) is commented out until we are fully live.
                Restore the ohs-oauth block + the "or" divider here once OAuth is wired end to end. */}
            {signup && <label className="oh-field"><span>Name</span><input placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} /></label>}
            <label className="oh-field"><span>Work email</span><input type="email" placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submitAuth(); }} /></label>
            <label className="oh-field">
              <span className="ohs-field-row"><span>Password</span>{!signup && <a className="ohs-forgot" onClick={() => navigate('/forgot')}>Forgot?</a>}</span>
              <input type="password" placeholder="••••••••" value={pass} onChange={(e) => setPass(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submitAuth(); }} />
            </label>
            {err && <div className="ohs-auth-err" style={{ color: 'var(--danger, #c0392b)', fontSize: '12.5px', margin: '2px 0 6px' }}>{err}</div>}
            <button className="oh-btn oh-btn--primary" disabled={busy} onClick={submitAuth}>{busy ? (signup ? 'Creating…' : 'Signing in…') : (signup ? 'Create account' : 'Sign in')}</button>
            <div className="ohs-auth-alt">
              {signup ? 'Already have an account? ' : 'New here? '}
              <a onClick={() => navigate(signup ? '/signin' : '/signup')}>{signup ? 'Sign in' : 'Create one'}</a>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// contact page — bare, centered (logo + form). Self-contained.
function OhContact({ brand, email }) {
  const [sent, setSent] = React.useState(false);
  return (
    <div className="ohs-auth">
      <div className="oh-card ohs-auth-card ohs-contact-card">
        <div className="ohs-auth-logo"><OhLogo brand={brand} /></div>
        {sent ? (
          <>
            <h1>Thanks — we’ll be in touch</h1>
            <div className="sub">We’ll reply to your message shortly.</div>
            <button className="oh-btn oh-btn--primary" onClick={() => navigate('/')}>Back home</button>
          </>
        ) : (
          <>
            <h1>Contact us</h1>
            <div className="sub">Questions, partnerships, or press — send us a note{email ? <> or email <a className="ohs-forgot" href={'mailto:' + email}>{email}</a></> : null}.</div>
            <label className="oh-field"><span>Name</span><input placeholder="Ada Lovelace" /></label>
            <label className="oh-field"><span>Work email</span><input type="email" placeholder="you@company.com" /></label>
            <label className="oh-field"><span>How can we help?</span><textarea rows={4} placeholder="Tell us a little about what you need…" /></label>
            <button className="oh-btn oh-btn--primary" onClick={() => setSent(true)}>Send message</button>
            <div className="ohs-auth-alt"><a onClick={() => navigate('/')}>← Back home</a></div>
          </>
        )}
      </div>
    </div>
  );
}

// pricing page body — tiers grid. tiers: [ { name, price, per, desc, features:[…], cta, featured? } ]
const OH_DEFAULT_TIERS = [
  { name: 'Free', price: '$0', per: '/mo', desc: 'For solo builders getting started.', features: ['Community access', 'Public resources', '1 workspace'], cta: 'Start free' },
  { name: 'Team', price: '$99', per: '/mo', desc: 'For teams shipping to production.', features: ['Everything in Free', 'Private workspaces', 'Usage analytics', 'Priority support'], cta: 'Start Team', featured: true },
  { name: 'Enterprise', price: 'Custom', per: '', desc: 'For regulated & at-scale orgs.', features: ['Everything in Team', 'SSO & SCIM', 'Audit & compliance', 'Dedicated support'], cta: 'Contact sales' },
];
function OhPricing({ tiers, onCta }) {
  const list = tiers || OH_DEFAULT_TIERS;
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Pricing" title="Simple, usage-based pricing" sub="Start free. Upgrade when you ship. Only the accent color changes between our products — the plans are consistent." />
      <div className="ohs-pricing">
        {list.map((t) => (
          <div className={'oh-card ohs-tier' + (t.featured ? ' featured' : '')} key={t.name}>
            {t.featured && <span className="ohs-tier-flag">Most popular</span>}
            <div className="tier-name">{t.name}</div>
            <div className="tier-price"><span className="amt">{t.price}</span><span className="per">{t.per}</span></div>
            <div className="tier-desc">{t.desc}</div>
            <ul className="tier-feats">{t.features.map((f) => <li key={f}>{f}</li>)}</ul>
            <button className={'oh-btn ' + (t.featured ? 'oh-btn--primary' : 'oh-btn--ghost')} onClick={() => (onCta ? onCta(t) : navigate('/signup'))}>{t.cta}</button>
          </div>
        ))}
      </div>
    </div>
  );
}

// plan: { name, desc, price, per, usagePct, usageLabel } · invoices: [ [date, amt, status], … ]
function OhBilling({ plan, invoices }) {
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Account" title="Billing" sub="Manage your plan, payment method, and invoices." />
      <div className="oh-card ohs-plan">
        <div className="pl">
          <div className="name">{plan.name}</div>
          <div className="desc">{plan.desc}</div>
        </div>
        <div className="price"><span className="amt">{plan.price}</span><span className="per">{plan.per}</span></div>
      </div>
      <div className="oh-card oh-card--pad" style={{ marginBottom: 18 }}>
        <div className="ohs-meter-row"><span>{plan.usageLabel}</span><span className="mono">{plan.usagePct}%</span></div>
        <div className="ohs-meter"><i style={{ width: plan.usagePct + '%' }} /></div>
      </div>
      <div className="ohs-settings-sec">
        <h3>Invoices</h3>
        <div className="oh-card oh-card--pad">
          <table className="oh-table">
            <thead><tr><th>Date</th><th>Amount</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {invoices.map(([d, a, s], i) => (
                <tr key={i}>
                  <td>{d}</td><td className="mono">{a}</td>
                  <td><span className={'oh-badge ' + (s === 'Paid' ? 'oh-badge--verified' : 'oh-badge--warn') + ' oh-badge--sm'}>{s}</span></td>
                  <td style={{ textAlign: 'right' }}><a className="ohs-navlink">Download</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <button className="oh-btn oh-btn--primary">Manage plan</button>
    </div>
  );
}

// metrics: [ { k, v, bars:[…0..1], hiLast? }, … ] · table optional
function OhUsage({ rollup, metrics }) {
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Account" title="Usage" sub="Your activity this billing period." />
      {rollup && <OhRollup items={rollup} />}
      <div className="ohs-usage-grid">
        {metrics.map((m) => (
          <div className="oh-card ohs-usage-card" key={m.k}>
            <div className="um-top"><span className="um-k">{m.k}</span><span className="um-v">{m.v}</span></div>
            <div className="ohs-bars">
              {m.bars.map((h, i) => <i key={i} className={(m.hiLast && i === m.bars.length - 1) ? 'hi' : ''} style={{ height: Math.max(6, h * 100) + '%' }} />)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// sections: [ { title, rows:[ {t, d, ctrl} ] }, … ]  (ctrl is a node)
function OhSettings({ sections }) {
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Account" title="Settings" sub="Manage your profile, team and preferences." />
      {sections.map((sec) => (
        <div className="ohs-settings-sec" key={sec.title}>
          <h3>{sec.title}</h3>
          <div className="oh-card oh-card--pad">
            {sec.rows.map((r) => (
              <div className="oh-setrow" key={r.t}>
                <div className="info"><div className="t">{r.t}</div>{r.d && <div className="d">{r.d}</div>}</div>
                <div className="ctrl">{r.ctrl}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// a controlled switch for settings rows
function OhSwitch({ on, onToggle }) {
  return <button className={'oh-switch' + (on ? ' on' : '')} onClick={onToggle} aria-pressed={!!on}><i /></button>;
}

// ---------- CONSOLE PAGES (signed-in app) ----------
// stats: [[label,value]…] · activity: [{icon,text,when}] · quick: [{title,desc,href,cta}]
// feature: optional node rendered between the head and the rollup (e.g. a product-specific
// hero strip). sub: optional page-head subtitle. Both default cleanly so existing callers
// (Teleon, the hubs) are unaffected.
function OhDashboard({ greeting, sub, feature, stats, activity, quick, plan }) {
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Workspace" title={greeting || 'Dashboard'} sub={sub || 'Everything in your workspace at a glance.'} />
      {feature}
      <OhRollup items={stats} />
      <div className="ohs-dash-grid">
        <div className="oh-card oh-card--pad">
          <div className="ohs-card-h">Recent activity</div>
          <div className="ohs-activity">
            {activity.map((a, i) => (
              <div className="ohs-act" key={i}>
                <span className="ai">{a.icon}</span>
                <span className="at">{a.text}</span>
                <span className="aw mono">{a.when}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="ohs-dash-side">
          {plan && (
            <div className="oh-card oh-card--pad ohs-planmini">
              <div className="ohs-card-h">Plan</div>
              <div className="pm-name">{plan.name}</div>
              <div className="ohs-meter" style={{ margin: '10px 0 4px' }}><i style={{ width: plan.usagePct + '%' }} /></div>
              <div className="ohs-meter-row"><span>{plan.usageLabel}</span><span className="mono">{plan.usagePct}%</span></div>
              <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ marginTop: 14, width: '100%', justifyContent: 'center' }} onClick={() => navigate('/billing')}>Manage plan</button>
            </div>
          )}
          <div className="oh-card oh-card--pad">
            <div className="ohs-card-h">Quick start</div>
            <div className="ohs-quick">
              {quick.map((q) => (
                <button className="ohs-quick-item" key={q.title} onClick={() => navigate(q.href)}>
                  <div className="qt">{q.title}</div><div className="qd">{q.desc}</div>
                  <span className="qc">{q.cta} →</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// keys: [{name, prefix, created, lastUsed}]
function OhApiKeys({ keys }) {
  const fixtures = keys || [
    { name: 'Production', prefix: 'sk_live_9f2c', created: 'Mar 4, 2026', lastUsed: '2h ago' },
    { name: 'CI', prefix: 'sk_live_3b71', created: 'Feb 1, 2026', lastUsed: '1d ago' },
    { name: 'Local dev', prefix: 'sk_test_a1f0', created: 'Jan 12, 2026', lastUsed: '3w ago' },
  ];
  // Live seam (same honesty contract as OhAuth): "+ Create key" mints a REAL key through the
  // realm identity service when this origin holds a real realm session; signed out or service
  // down → an honest note, never a fabricated key. The raw key is shown exactly once (the
  // service never persists it — oh-identity.js mintKey). Fixture rows are design data; minted
  // rows are real and individually revocable.
  const realm = React.useMemo(() => {
    try {
      for (let i = 0; i < localStorage.length; i += 1) {
        const k = localStorage.key(i);
        if (k && k.indexOf('oh-session-') === 0) {
          const s = JSON.parse(localStorage.getItem(k) || 'null');
          if (s && s.session_id) return k.slice('oh-session-'.length);
        }
      }
    } catch (e) {}
    return null;
  }, []);
  const [minted, setMinted] = React.useState([]);
  const [reveal, setReveal] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  const [note, setNote] = React.useState('');
  const mint = async () => {
    if (busy) return;
    if (!window.OHIdentity || !realm) {
      setNote('Sign in first — keys are minted against your real account (no simulated keys).');
      return;
    }
    setBusy(true); setNote('');
    try {
      const r = await window.OHIdentity.mintKey(realm, ['read']);
      if (r && r.status === 201 && r.body && r.body.api_key) {
        setReveal(r.body.api_key);
        setMinted((m) => [{ id: r.body.key_id, name: 'Minted via console', prefix: r.body.prefix || r.body.api_key.slice(0, 12), created: 'just now', lastUsed: '—', real: true }, ...m]);
      } else {
        setNote((r && r.body && r.body.error) || 'mint failed — no key was created');
      }
    } catch (e) { setNote('identity service unreachable — no key was created'); }
    setBusy(false);
  };
  const revoke = async (k) => {
    try {
      const r = await window.OHIdentity.revokeKey(realm, k.id);
      if (r && (r.status === 200 || r.status === 202)) setMinted((m) => m.filter((x) => x.id !== k.id));
    } catch (e) {}
  };
  const list = [...minted, ...fixtures];
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Developers" title="API keys" sub="Create and manage the keys your agents authenticate with."
        actions={<button className="oh-btn oh-btn--primary" disabled={busy} onClick={mint}>{busy ? 'Creating…' : '+ Create key'}</button>} />
      {reveal && (
        <div className="oh-card oh-card--pad" style={{ marginBottom: 18 }}>
          <div className="ohs-meter-row"><span>New key minted — copy it now; it is shown only once.</span><span className="mono">{realm}</span></div>
          <div className="ohs-hint mono" style={{ userSelect: 'all', wordBreak: 'break-all' }}>{reveal}</div>
        </div>
      )}
      {note && <div className="ohs-hint mono" style={{ marginBottom: 12 }}>{note}</div>}
      <div className="oh-card oh-card--pad">
        <table className="oh-table">
          <thead><tr><th>Name</th><th>Key</th><th>Created</th><th>Last used</th><th></th></tr></thead>
          <tbody>
            {list.map((k, i) => (
              <tr key={k.real ? k.id : 'fx' + i}>
                <td>{k.name}{k.real && <span className="oh-badge oh-badge--verified oh-badge--sm" style={{ marginLeft: 8 }}>real</span>}</td>
                <td className="mono">{k.prefix}••••••••</td>
                <td className="mono">{k.created}</td>
                <td className="mono">{k.lastUsed}</td>
                <td style={{ textAlign: 'right' }}><a className="ohs-navlink ohs-danger" onClick={k.real ? () => revoke(k) : undefined}>Revoke</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="ohs-hint mono">Keep keys secret. Treat them like passwords; rotate regularly.</div>
    </div>
  );
}

// members: [{name, email, role, status}]
function OhTeam({ members }) {
  const list = members || [
    { name: 'Ada Lovelace', email: 'ada@company.com', role: 'Owner', status: 'active' },
    { name: 'Alan Turing', email: 'alan@company.com', role: 'Admin', status: 'active' },
    { name: 'Grace Hopper', email: 'grace@company.com', role: 'Member', status: 'active' },
    { name: 'invited@company.com', email: 'invited@company.com', role: 'Member', status: 'invited' },
  ];
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Account" title="Team" sub="Invite teammates and manage their roles."
        actions={<button className="oh-btn oh-btn--primary">+ Invite</button>} />
      <div className="oh-card oh-card--pad" style={{ marginBottom: 16 }}>
        <div className="ohs-invite">
          <input className="oh-input" placeholder="teammate@company.com" style={{ flex: 1 }} />
          <select className="oh-input" style={{ minWidth: 130 }}><option>Member</option><option>Admin</option><option>Owner</option></select>
          <button className="oh-btn oh-btn--primary">Send invite</button>
        </div>
      </div>
      <div className="oh-card oh-card--pad">
        <table className="oh-table">
          <thead><tr><th>Member</th><th>Role</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {list.map((m, i) => (
              <tr key={i}>
                <td><div className="ohs-member"><span className="ohs-avatar">{m.name[0].toUpperCase()}</span><div><div className="mn">{m.name}</div><div className="me mono">{m.email}</div></div></div></td>
                <td>{m.role}</td>
                <td><span className={'oh-badge oh-badge--sm ' + (m.status === 'active' ? 'oh-badge--verified' : 'oh-badge--warn')}>{m.status}</span></td>
                <td style={{ textAlign: 'right' }}><a className="ohs-navlink">Manage</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// audit log / receipts — every served pack, verification, export, key action
function OhAuditLog({ rows }) {
  const list = rows || [
    { t: '40s ago', ev: 'Pack served', icon: '◎', actor: 'Claude Code', target: 'acme-policy / hyper', policy: 'serve:cited', ok: true },
    { t: '6m ago', ev: 'Verification passed', icon: '✓', actor: 'engine', target: 'eu-reg', policy: 'verify:live', ok: true },
    { t: '1h ago', ev: 'Conflict escalated', icon: '⚠', actor: 'reviewer', target: 'eu-reg / EUDR date', policy: 'hitl:review', ok: false },
    { t: '3h ago', ev: 'Artifact emitted', icon: '⤓', actor: 'ada@company.com', target: 'AIBOM · acme-policy', policy: 'export:aibom', ok: true },
    { t: '1d ago', ev: 'API key created', icon: '⚿', actor: 'ada@company.com', target: 'Production', policy: 'keys:create', ok: true },
  ];
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Governance" title="Audit log" sub="Every pack served, verification, escalation and export — with the policy it ran under." />
      <div className="oh-card oh-card--pad">
        <table className="oh-table">
          <thead><tr><th>Time</th><th>Event</th><th>Actor</th><th>Target</th><th>Policy</th></tr></thead>
          <tbody>
            {list.map((r, i) => (
              <tr key={i}>
                <td className="mono">{r.t}</td>
                <td><span className="ohs-evln"><span className={'ohs-evic' + (r.ok ? '' : ' warn')}>{r.icon}</span>{r.ev}</span></td>
                <td>{r.actor}</td>
                <td className="mono">{r.target}</td>
                <td><span className="oh-badge oh-badge--sm mono">{r.policy}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="ohs-hint mono">Every row is signed and exportable — the receipt behind what your agents read.</div>
    </div>
  );
}

// ---------- DOCS (shared multi-tab docs surface) ----------
// cfg: { brand, noun, nounPlural, intro, quickstart:[[step,desc]], api:[{m,path,name,desc}] }
function OhDocs({ cfg, theme, onToggle }) {
  const [tab, setTab] = React.useState('overview');
  const [guide, setGuide] = React.useState('start');
  const [ep, setEp] = React.useState(0);
  const B = cfg.brand;
  const N = cfg.noun || 'resource', NP = cfg.nounPlural || 'resources';
  const TABS = [['overview', 'Overview'], ['guides', 'Guides'], ['reference', 'Reference'], ['api', 'API']];
  const GUIDES = [
    ['start', 'Getting started', `Install the CLI, authenticate, and ${cfg.firstAction || 'make your first call'}.`, [
      ['p', cfg.intro || `${B.name}${B.tld || ''} is part of AI Done Right. This guide gets you from zero to your first result in three steps.`],
      ['steps', cfg.quickstart || [['Install', 'Add the SDK or CLI to your project.'], ['Authenticate', 'Create an API key and export it.'], ['Run', `Make your first ${N} call and read the response.`]]],
      ['callout', 'Every response is signed and traceable — provenance is built in, not bolted on.'],
      ['code', cfg.installCode || '# install\nnpm i @cie/sdk\nexport CIE_API_KEY=sk_live_…'],
    ]],
    ['concepts', 'Core concepts', `The objects you’ll work with in ${B.name}.`, [
      ['h2', NP.charAt(0).toUpperCase() + NP.slice(1)], ['p', cfg.conceptCopy || `The core unit you create, version and consume. Each is evaluated and signed before it ships.`],
      ['h2', 'Versioning'], ['p', 'Everything is semver-pinned with a changelog so you always know what you’re running.'],
      ['h2', 'Provenance'], ['p', 'A signed origin chain you can verify by hash — the audit trail behind every artifact.'],
    ]],
    ['auth', 'Authentication', 'Authenticate requests with a bearer token.', [
      ['p', 'Create a key in the console under API keys, then send it as a bearer token on every request.'],
      ['code', 'curl https://api.' + (B.name.toLowerCase()) + (B.tld || '') + '/v1/ping \\\n  -H "Authorization: Bearer $CIE_API_KEY"'],
      ['callout', 'Keep keys secret and rotate regularly. Revoked keys stop working immediately.'],
    ]],
  ];
  const API = cfg.api || [
    { m: 'GET', path: '/v1/' + NP, name: 'List ' + NP, desc: 'Retrieve the ' + NP + ' in your workspace.' },
    { m: 'POST', path: '/v1/' + NP, name: 'Create ' + N, desc: 'Publish a new ' + N + ' to the registry.' },
    { m: 'GET', path: '/v1/' + NP + '/{id}', name: 'Get ' + N, desc: 'Fetch one ' + N + ' with its versions and provenance.' },
  ];
  const a = GUIDES.find((g) => g[0] === guide) || GUIDES[0];
  const e = API[ep] || API[0];
  return (
    <div className="oh-site ohs-docs">
      <header className="ohs-docs-top">
        <a className="ohs-docs-brand" onClick={() => navigate('/')}>
          <span className="ohs-logo-mk" style={{ background: B.accent, width: 24, height: 24 }}>{B.glyph}</span>
          <span className="ohs-docs-wm"><span className="sub">docs.</span>{B.name}<span className="tld">{B.tld || ''}</span></span>
        </a>
        <nav className="ohs-docs-nav">{TABS.map(([k, l]) => <a key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</a>)}</nav>
        <span className="ohs-spacer" />
        <OhThemeToggle theme={theme} onToggle={onToggle} />
        <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => navigate('/app')}>Console ›</button>
      </header>

      {tab === 'overview' && (
        <div className="ohs-docs-home">
          <div className="ohs-docs-hero"><div className="ohs-eyebrow">{B.name}{B.tld || ''} docs</div><h1>Build on {B.name}.</h1><p>{cfg.intro || `Everything you need to integrate ${B.name} into your stack.`}</p></div>
          <div className="ohs-grid-3">
            {[['→', 'Getting started', 'Zero to first call.', 'guides'], ['◫', 'Reference', 'Concepts & glossary.', 'reference'], ['⚙', 'API', 'REST endpoints.', 'api']].map(([ic, t, d, go]) => (
              <button className="oh-card oh-card--interactive ohs-feature" key={t} onClick={() => setTab(go)} style={{ cursor: 'pointer', textAlign: 'left' }}><div className="fi">{ic}</div><h4>{t}</h4><p>{d}</p></button>
            ))}
          </div>
        </div>
      )}

      {(tab === 'guides' || tab === 'reference') && (
        <div className="ohs-docs-body">
          <nav className="ohs-docs-side">
            {GUIDES.map(([id, title]) => <button key={id} className={'ohs-docs-link' + (guide === id ? ' on' : '')} onClick={() => setGuide(id)}>{title}</button>)}
          </nav>
          <main className="ohs-docs-main">
            <h1>{a[1]}</h1><p className="ohs-docs-lede">{a[2]}</p>
            {a[3].map((blk, i) => {
              const [k, c] = blk;
              if (k === 'h2') return <h2 className="ohs-docs-h2" key={i}>{c}</h2>;
              if (k === 'p') return <p className="ohs-docs-p" key={i}>{c}</p>;
              if (k === 'callout') return <div className="ohs-docs-callout" key={i}><span className="i">ⓘ</span><span>{c}</span></div>;
              if (k === 'code') return <pre className="ohs-docs-code" key={i}>{c}</pre>;
              if (k === 'steps') return <ol className="ohs-docs-steps" key={i}>{c.map(([t, d]) => <li key={t}><b>{t}</b> — {d}</li>)}</ol>;
              return null;
            })}
          </main>
        </div>
      )}

      {tab === 'api' && (
        <div className="ohs-docs-body">
          <nav className="ohs-docs-side">
            {API.map((x, i) => <button key={i} className={'ohs-docs-link' + (ep === i ? ' on' : '')} onClick={() => setEp(i)}><span className={'ohs-mb ohs-mb--' + x.m.toLowerCase()}>{x.m}</span>{x.name}</button>)}
          </nav>
          <main className="ohs-docs-main">
            <h1>{e.name}</h1><p className="ohs-docs-lede">{e.desc}</p>
            <div className="ohs-docs-try"><span className={'ohs-mb ohs-mb--' + e.m.toLowerCase()}>{e.m}</span><span className="mono">{e.path}</span></div>
            <h2 className="ohs-docs-h2">Authorization</h2>
            <p className="ohs-docs-p mono">Authorization: Bearer &lt;token&gt;</p>
          </main>
        </div>
      )}
    </div>
  );
}

// ---------- more common pages (shared) ----------
function OhOnboarding({ brand, steps }) {
  const list = steps || [['Create your workspace', 'Done', true], ['Connect a source', 'Link your first system', false], ['Create an API key', 'Authenticate your agents', false], ['Invite your team', 'Add teammates', false]];
  const done = list.filter((s) => s[2]).length;
  return (
    <div className="ohs-page narrow">
      <OhPageHead eyebrow={'Welcome to ' + brand.name + (brand.tld || '')} title="Get set up" sub="A few quick steps to get the most out of your workspace." />
      <div className="oh-card oh-card--pad" style={{ marginBottom: 16 }}>
        <div className="ohs-meter-row"><span>{done} of {list.length} complete</span><span className="mono">{Math.round(done / list.length * 100)}%</span></div>
        <div className="ohs-meter" style={{ marginTop: 8 }}><i style={{ width: (done / list.length * 100) + '%' }} /></div>
      </div>
      <div className="ohs-onb">
        {list.map(([t, d, ok], i) => (
          <div className={'oh-card ohs-onb-step' + (ok ? ' done' : '')} key={i}>
            <span className="ohs-onb-ck">{ok ? '✓' : i + 1}</span>
            <div className="ohs-onb-b"><div className="t">{t}</div><div className="d">{d}</div></div>
            {!ok && <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/app')}>Start</button>}
          </div>
        ))}
      </div>
    </div>
  );
}

function OhNotifications({ items }) {
  const list = items || [
    { icon: '⚠', t: 'A source change needs review', d: 'eu-reg · EUDR date superseded', w: '1h ago', unread: true },
    { icon: '✓', t: 'Verification passed', d: 'acme-policy re-checked', w: '3h ago', unread: true },
    { icon: '◷', t: 'Weekly digest ready', d: '38 promotions · 6 rollbacks', w: '1d ago' },
    { icon: '⚿', t: 'API key used from a new IP', d: 'Production · 8.8.8.8', w: '2d ago' },
  ];
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Inbox" title="Notifications" sub="Changes, escalations and results across your workspace."
        actions={<button className="oh-btn oh-btn--ghost oh-btn--sm">Mark all read</button>} />
      <div className="oh-card oh-card--pad">
        <div className="ohs-activity">
          {list.map((n, i) => (
            <div className={'ohs-act ohs-noti' + (n.unread ? ' unread' : '')} key={i}>
              <span className="ai">{n.icon}</span>
              <span className="at"><b>{n.t}</b><span className="nd">{n.d}</span></span>
              <span className="aw mono">{n.w}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function OhStatus({ brand, components }) {
  const list = components || [['API', 'operational'], ['Console', 'operational'], ['Ingestion / sync', 'operational'], ['Verification engine', 'operational'], ['Serving', 'degraded']];
  const allUp = list.every((c) => c[1] === 'operational');
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Status" title="System status" sub={'Live operational status for ' + brand.name + (brand.tld || '') + '.'} />
      <div className={'oh-card oh-card--pad ohs-status-banner ' + (allUp ? 'up' : 'deg')}>
        <span className="dot" />{allUp ? 'All systems operational' : 'Some systems degraded'}
      </div>
      <div className="oh-card oh-card--pad" style={{ marginTop: 16 }}>
        {list.map(([n, s], i) => (
          <div className="oh-setrow ohs-status-row" key={i}>
            <div className="info"><div className="t">{n}</div></div>
            <div className="ctrl"><span className={'ohs-stat s-' + s}><span className="d" />{s}</span></div>
          </div>
        ))}
      </div>
      <div className="ohs-hint mono">Uptime 99.98% over the last 90 days.</div>
    </div>
  );
}

function OhChangelog({ entries }) {
  const list = entries || [
    { v: 'v2.4', d: 'Jun 2026', items: ['Audit log now exportable as signed CSV', 'Faster reconciliation on large corpora', 'Dark-mode polish across the console'] },
    { v: 'v2.3', d: 'May 2026', items: ['Team roles & invites', 'API keys with per-key scopes', 'New regulatory-change feed'] },
    { v: 'v2.2', d: 'Apr 2026', items: ['Compliance artifact exports (AIBOM, EU AI Act)', 'Provenance verify-by-hash'] },
  ];
  return (
    <div className="ohs-page narrow">
      <OhPageHead eyebrow="Product" title="Changelog" sub="What’s new, shipped continuously." />
      {list.map((e) => (
        <div className="ohs-chlog" key={e.v}>
          <div className="ohs-chlog-head"><span className="oh-badge oh-badge--verified oh-badge--sm">{e.v}</span><span className="mono">{e.d}</span></div>
          <ul className="ohs-chlog-list">{e.items.map((it) => <li key={it}>{it}</li>)}</ul>
        </div>
      ))}
    </div>
  );
}

function OhLegal({ brand, kind }) {
  const terms = kind !== 'privacy';
  return (
    <div className="ohs-page narrow ohs-legal">
      <OhPageHead eyebrow="Legal" title={terms ? 'Terms of Service' : 'Privacy Policy'} sub={'Last updated June 2026 · ' + brand.name + (brand.tld || '')} />
      <div className="oh-card oh-card--pad">
        <p>This is a prototype document. Replace with your reviewed legal copy before launch.</p>
        <h3>{terms ? '1. Acceptable use' : '1. What we collect'}</h3>
        <p>{terms ? 'You agree to use the service in compliance with applicable law and the limits of your plan.' : 'We collect account details, usage metrics, and the content you connect — never used to train shared models.'}</p>
        <h3>{terms ? '2. Data & confidentiality' : '2. How we use it'}</h3>
        <p>{terms ? 'Your data stays isolated to your workspace and is processed only to provide the service.' : 'To operate the service, secure it, and improve your own workspace — with provenance recorded throughout.'}</p>
        <h3>{terms ? '3. Liability' : '3. Your rights'}</h3>
        <p>{terms ? 'The service is provided “as is”; see your enterprise agreement for warranties.' : 'Request export or deletion of your data at any time from Settings.'}</p>
      </div>
    </div>
  );
}

// standardized 404. home defaults to '/'; links: optional [[label, href], …] of suggestions.
function OhNotFound({ brand, home, links }) {
  return (
    <div className="ohs-page narrow ohs-notfound">
      <div className="ohs-404">404</div>
      <h1>This page wandered off.</h1>
      <p>The page you’re looking for doesn’t exist, moved, or never did{brand ? ' on ' + brand.name + (brand.tld || '') : ''}. Let’s get you back on track.</p>
      <div className="ohs-cta">
        <button className="oh-btn oh-btn--primary" onClick={() => navigate(home || '/')}>← Back home</button>
        {(links || []).map(([l, h]) => <button key={l} className="oh-btn oh-btn--ghost" onClick={() => navigate(h)}>{l}</button>)}
      </div>
    </div>
  );
}

// standardized About / mission page. Pulls the company mission + thesis from window.BRAND and
// renders the family from window.PORTFOLIO, so every site's About ties back to the group.
function OhAbout({ brand, lede, children }) {
  const B = (typeof window !== 'undefined' && window.BRAND) || {};
  const P = (typeof window !== 'undefined') && window.PORTFOLIO;
  const bn = brand ? brand.name + (brand.tld || '') : '';
  return (
    <div className="ohs-page ohs-about">
      <OhPageHead eyebrow={'About ' + (brand ? brand.name : 'us')} title={B.mission || 'Why we exist'} sub={B.thesis} />
      <div className="oh-card oh-card--pad ohs-about-lede">
        <p>{lede || (bn + ' is part of ' + (P ? P.GROUP.name : 'our group') + '. ' + (B.thesis || '') + ' We build the layer that makes that context trustworthy — verified, current, and provable — so the agents you run can be trusted too.')}</p>
        {children}
      </div>
      {P && (
        <div className="ohs-about-family">
          <div className="ohs-section-label">The family</div>
          <div className="ohs-grid-3">
            {Object.values(P.ENTITIES).map((e) => (
              <a key={e.name} className="oh-card oh-card--pad oh-card--interactive ohs-about-ent" href={e.url} style={{ '--ent': e.accent }}>
                <span className="ohs-pf-mk" style={{ '--ent': e.accent }} aria-hidden="true">{e.glyph}</span>
                <div className="nm">{e.wordmark || e.name}</div>
                <div className="kd">{e.kind}</div>
                <p>{e.blurb}</p>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------- case studies (shared) ----------
// cases: [{ id, client, sector, title, summary, accent?, metrics:[[value,label]],
//           challenge, approach:[…], outcome:[…], quote?:{text,who} }]
// OhCaseStudies = index grid. OhCaseStudy = one detail (pass `id`); falls back to the index.
function OhCaseStudies({ brand, cases, eyebrow, title, sub, onOpen }) {
  const list = cases || [];
  const go = onOpen || ((id) => navigate('/cases/' + id));
  return (
    <div className="ohs-page ohs-cases">
      <OhPageHead eyebrow={eyebrow || 'Case studies'} title={title || 'Proof, in production.'}
        sub={sub || ('How teams put ' + (brand ? brand.name : 'us') + ' to work — and what changed.')} />
      <div className="ohs-grid-3 ohs-case-grid">
        {list.map((c) => (
          <button key={c.id} className="oh-card oh-card--pad oh-card--interactive ohs-case-card" style={c.accent ? { '--ent': c.accent } : null} onClick={() => go(c.id)}>
            <div className="ohs-case-meta"><span className="ohs-case-sector">{c.sector}</span></div>
            <div className="ohs-case-client">{c.client}</div>
            <div className="ohs-case-title">{c.title}</div>
            <p className="ohs-case-summary">{c.summary}</p>
            {c.metrics && c.metrics[0] && (
              <div className="ohs-case-stat"><span className="v">{c.metrics[0][0]}</span><span className="k">{c.metrics[0][1]}</span></div>
            )}
            <span className="ohs-case-go">Read case study →</span>
          </button>
        ))}
      </div>
    </div>
  );
}
function OhCaseStudy({ brand, cases, id, onBack, cta }) {
  const list = cases || [];
  const c = list.find((x) => x.id === id);
  if (!c) return <OhCaseStudies brand={brand} cases={list} />;
  const back = onBack || (() => navigate('/cases'));
  const idx = list.findIndex((x) => x.id === id);
  const next = list[(idx + 1) % list.length];
  return (
    <div className="ohs-page ohs-casestudy" style={c.accent ? { '--accent': c.accent } : null}>
      <button className="ohs-back" onClick={back}>← All case studies</button>
      <div className="ohs-cs-head">
        <div className="ohs-cs-sector mono">{c.sector}</div>
        <h1>{c.title}</h1>
        <p className="ohs-cs-summary">{c.summary}</p>
        <div className="ohs-cs-client">{c.client}</div>
      </div>
      {c.metrics && (
        <div className="ohs-rollup ohs-cs-metrics">
          {c.metrics.map(([v, k]) => <div className="oh-card ohs-roll" key={k}><div className="v">{v}</div><div className="k">{k}</div></div>)}
        </div>
      )}
      <div className="ohs-cs-body">
        <div className="ohs-cs-main">
          {c.challenge && <section className="ohs-cs-sec"><div className="ohs-section-label">The challenge</div><p>{c.challenge}</p></section>}
          {c.approach && <section className="ohs-cs-sec"><div className="ohs-section-label">What we did</div><ol className="ohs-cs-steps">{c.approach.map((s, i) => <li key={i}>{s}</li>)}</ol></section>}
          {c.outcome && <section className="ohs-cs-sec"><div className="ohs-section-label">The outcome</div><ul className="ohs-cs-out">{c.outcome.map((s, i) => <li key={i}>{s}</li>)}</ul></section>}
        </div>
        <aside className="ohs-cs-aside">
          {c.quote && <div className="oh-card oh-card--pad ohs-cs-quote"><p>“{c.quote.text}”</p><div className="who">{c.quote.who}</div></div>}
          <div className="oh-card oh-card--pad ohs-cs-cta">
            <div className="t">{(cta && cta.title) || 'See it on your own data'}</div>
            <button className="oh-btn oh-btn--primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => navigate((cta && cta.href) || '/signup')}>{(cta && cta.label) || 'Start free →'}</button>
          </div>
          {next && next.id !== c.id && (
            <button className="oh-card oh-card--pad oh-card--interactive ohs-cs-next" onClick={() => navigate('/cases/' + next.id)}>
              <span className="l mono">Next case</span><span className="n">{next.title}</span>
            </button>
          )}
        </aside>
      </div>
    </div>
  );
}

// ---------- experiments + tracking (thin React layer over window.OHExp) ----------
// usage: const [variant, { track }] = useExperiment('hero', ['A','B','C']);
// fires an exposure on mount; `track('cta_click', {…})` records a conversion with the variant.
function useExperiment(key, variants, opts) {
  const E = (typeof window !== 'undefined') && window.OHExp;
  if (E && variants) E.define(key, variants, opts);
  const first = variants && variants[0];
  const fallback = first && (first.id || first);
  const [v, setV] = React.useState(() => (E ? E.variant(key) : fallback) || fallback);
  React.useEffect(() => {
    if (!E) return undefined;
    E.exposure(key);
    return E.onChange((k) => { if (k == null || k === key) setV(E.variant(key)); });
  }, [key]);
  const track = React.useCallback((ev, props) => { if (E) E.track(ev, Object.assign({ experiment: key, variant: v }, props || {})); }, [key, v]);
  const assign = React.useCallback((id) => { if (E) E.assign(key, id); }, [key]);
  return [v, { track, assign }];
}

// floating dev panel: force variants, watch live exposure/conversion counts. Renders
// nothing if oh-experiments.js isn't loaded. Drop one <OhExperimentsPanel/> per site.
function OhExperimentsPanel() {
  const E = (typeof window !== 'undefined') && window.OHExp;
  const [open, setOpen] = React.useState(false);
  const [, force] = React.useReducer((x) => x + 1, 0);
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (!E) return undefined;
    const offC = E.onChange(() => force()); const offT = E.onTrack(() => force());
    return () => { offC(); offT(); };
  }, []);
  React.useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', onDoc, true); document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDoc, true); document.removeEventListener('keydown', onKey); };
  }, [open]);
  if (!E) return null;
  const exps = E.experiments();
  const events = E.events();
  const statsFor = (key) => {
    const rows = {};
    events.forEach((ev) => {
      const variant = ev.exp ? ev.exp[key] : null; if (variant == null) return;
      rows[variant] = rows[variant] || { exp: 0, conv: 0 };
      if (ev.event === '$exposure') rows[variant].exp += 1; else rows[variant].conv += 1;
    });
    return rows;
  };
  return (
    <div className={'ohx' + (open ? ' open' : '')} ref={ref}>
      {open && (
        <div className="ohx-panel" role="dialog" aria-label="Experiments and tracking">
          <div className="ohx-head"><span>Experiments &amp; tracking</span><button className="ohx-x" onClick={() => E.reset()} title="Reset assignments + events">reset</button></div>
          {!exps.length && <div className="ohx-empty">No experiments registered on this page.</div>}
          {exps.map((x) => {
            const st = statsFor(x.key);
            return (
              <div className="ohx-exp" key={x.key}>
                <div className="ohx-exp-h"><span className="k">{x.key}</span>{x.overridden && <span className="ohx-tag">forced</span>}</div>
                <div className="ohx-variants">
                  {x.variants.map((id) => {
                    const s = st[id] || { exp: 0, conv: 0 };
                    const rate = s.exp ? Math.round((s.conv / s.exp) * 100) : 0;
                    return (
                      <button key={id} className={'ohx-var' + (x.assigned === id ? ' on' : '')} onClick={() => E.assign(x.key, id)}>
                        <span className="vid">{id}</span>
                        <span className="vmetrics mono">{s.exp}·{s.conv} <b>{rate}%</b></span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
          <div className="ohx-foot mono">exposures · conversions · rate · visitor {E.visitorId().slice(0, 10)} · {events.length} events</div>
        </div>
      )}
      <button className="ohx-trigger" aria-expanded={open} onClick={() => setOpen((o) => !o)} title="Experiments & tracking">
        <span className="g" aria-hidden="true">⚗</span><span className="lbl">Experiments</span>
      </button>
    </div>
  );
}

// ---------- command palette (⌘K) ----------
// commands: [{ label, href, icon?, group?, onSelect? }]  OR derive via fromNav().
// Self-contained: opens on ⌘K / Ctrl-K and on a window 'oh-cmdk' event (so a search box can
// dispatch it). Fuzzy-filters by label, keyboard up/down/enter/esc, tracks selection via OHExp.
OhCommandK.fromNav = function (nav, groups) {
  const out = [];
  (nav || []).forEach(([href, icon, label]) => out.push({ label, href, icon, group: 'Navigate' }));
  (groups || []).forEach((g) => (g.items || []).forEach(([href, icon, label]) => out.push({ label, href, icon, group: g.label })));
  return out;
};
function OhCommandK({ commands, placeholder, label }) {
  const list = commands || [];
  const [open, setOpen] = React.useState(false);
  const [q, setQ] = React.useState('');
  const [i, setI] = React.useState(0);
  React.useEffect(() => {
    const onEvt = () => setOpen(true);
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setOpen((o) => !o); }
    };
    window.addEventListener('oh-cmdk', onEvt); window.addEventListener('keydown', onKey);
    return () => { window.removeEventListener('oh-cmdk', onEvt); window.removeEventListener('keydown', onKey); };
  }, []);
  React.useEffect(() => { if (open) { setQ(''); setI(0); } }, [open]);
  const ql = q.trim().toLowerCase();
  const filtered = ql ? list.filter((c) => c.label.toLowerCase().includes(ql) || (c.group || '').toLowerCase().includes(ql)) : list;
  const pick = (idx) => {
    const c = filtered[idx]; if (!c) return;
    try { if (window.OHExp) window.OHExp.track('cmdk_select', { label: c.label, href: c.href, query: q }); } catch (e) {}
    setOpen(false);
    if (c.onSelect) c.onSelect(); else if (c.href) navigate(c.href);
  };
  const onKey = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setI((n) => Math.min(n + 1, filtered.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setI((n) => Math.max(n - 1, 0)); }
    else if (e.key === 'Enter') { e.preventDefault(); pick(i); }
    else if (e.key === 'Escape') { e.preventDefault(); setOpen(false); }
  };
  if (!open) return null;
  let lastGroup = null;
  return (
    <div className="ohk-overlay" onClick={() => setOpen(false)}>
      <div className="ohk-modal" role="dialog" aria-label="Command palette" onClick={(e) => e.stopPropagation()}>
        <div className="ohk-input">
          <span className="ohk-mag" aria-hidden="true">⌕</span>
          <input autoFocus placeholder={placeholder || 'Search or jump to…'} value={q}
            onChange={(e) => { setQ(e.target.value); setI(0); }} onKeyDown={onKey} />
          <span className="oh-kbd">esc</span>
        </div>
        <div className="ohk-list">
          {filtered.map((c, idx) => {
            const head = c.group && c.group !== lastGroup ? c.group : null; lastGroup = c.group;
            return (
              <React.Fragment key={(c.href || c.label) + idx}>
                {head && <div className="ohk-group">{head}</div>}
                <div className={'ohk-item' + (idx === i ? ' on' : '')} onMouseEnter={() => setI(idx)} onClick={() => pick(idx)}>
                  {c.icon && <span className="ohk-ic" aria-hidden="true">{c.icon}</span>}
                  <span className="ohk-label">{c.label}</span>
                  {idx === i && <span className="oh-kbd ohk-enter">↵</span>}
                </div>
              </React.Fragment>
            );
          })}
          {!filtered.length && <div className="ohk-empty">No matches for “{q}”</div>}
        </div>
        <div className="ohk-foot mono">{label || 'Jump to anything'} · ↑↓ to move · ↵ to open</div>
      </div>
    </div>
  );
}

Object.assign(window, {
  useHashRoute, navigate, useSiteTheme,
  OhLogo, OhThemeToggle, OhTopBar, OhPortfolioMenu, OhHero, OhSection, OhFeatures, OhBand, OhFooter,
  OhAppShell, OhPageHead, OhRollup, OhLayout, OhTable,
  OhAuth, OhContact, OhPricing, OhBilling, OhUsage, OhSettings, OhSwitch,
  OhDashboard, OhApiKeys, OhTeam, OhAuditLog, OhDocs,
  OhOnboarding, OhNotifications, OhStatus, OhChangelog, OhLegal, OhNotFound, OhAbout,
  OhCaseStudies, OhCaseStudy, OhCommandK,
  useExperiment, OhExperimentsPanel,
});
