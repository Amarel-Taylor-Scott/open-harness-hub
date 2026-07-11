/* global React, ReactDOM, useHashRoute, useTheme, CEStore, BRANDCE, Landing, WhyPage, DocsPage, AppShell, CorporaPage, IngestPage, CorpusDetail, ServePage, VerifyPage, CommonsPage, GovernancePage, SettingsPage, BillingPage, UsagePage, PricingPage, PageHead, navigate */
// Context Enrichment — app root: hash router + mount. Standalone brand on dir-d.

function ComingSoon({ title, sub }) {
  return (
    <div className="ce-page">
      <PageHead eyebrow={BRANDCE.name} title={title} sub={sub} />
      <div className="ce-panel" style={{ textAlign: 'center', padding: '48px 22px', color: 'var(--fg-faint)' }}>
        <div style={{ fontSize: 13.5 }}>This page is on the roadmap.</div>
        <div style={{ marginTop: 16 }}><button className="oh-btn oh-btn--primary" onClick={() => navigate('/ingest')}>Ingest a source →</button></div>
      </div>
    </div>
  );
}

function NotFound() {
  const Kit = window;
  return Kit.OhNotFound
    ? <Kit.OhNotFound brand={{ name: 'Baltor', tld: '.ai' }} home="/dashboard" links={[['Corpora', '/corpora'], ['Docs', '/docs']]} />
    : <div className="ce-page"><PageHead title="Not found" sub="That page doesn’t exist yet." /></div>;
}

function App() {
  const route = useHashRoute();
  const [theme, toggleTheme] = useTheme();
  const rootClass = 'oh ' + BRANDCE.dir + ' theme-' + theme + ' ce-root';
  // logo chip + page accent both resolve from Baltor's dir-d tokens (light #0e7c86 / dark #2dd4bf)
  const kitBrand = { name: 'Baltor', tld: '.ai', glyph: '◳', accent: 'var(--accent)' };

  // auth + contact + about + cases — rendered via the SHARED KIT (Oh* pages) under Baltor's scope
  if (route === '/signin' || route === '/signup' || route === '/forgot' || route === '/contact' || route === '/about'
      || route === '/cases' || route.startsWith('/cases/')) {
    const Kit = window;
    const baltorCases = (Kit.CASES && Kit.CASES.baltor) || [];
    return (
      <div className={'oh ' + BRANDCE.dir + ' theme-' + theme + ' oh-site ce-root'}>
        {route === '/contact' ? <Kit.OhContact brand={kitBrand} email="hello@baltor.ai" />
          : route === '/about' ? <Kit.OhAbout brand={kitBrand} />
          : route === '/cases' ? <Kit.OhCaseStudies brand={kitBrand} cases={baltorCases} />
          : route.startsWith('/cases/') ? <Kit.OhCaseStudy brand={kitBrand} cases={baltorCases} id={route.slice(7)} cta={{ label: 'Connect a source →', href: '/ingest' }} />
          : <Kit.OhAuth brand={kitBrand} mode={route.slice(1)} />}
      </div>
    );
  }

  // full-bleed marketing surfaces (no app chrome)
  if (route === '/' || route === '' || route === '/why' || route === '/docs' || route === '/pricing' || route === '/engine') {
    return (
      <CEStore.Provider value={{ route, theme, toggleTheme }}>
        <div className={rootClass}>
          {route === '/why' ? <WhyPage /> : route === '/docs' ? <DocsPage /> : route === '/pricing' ? <PricingPage /> : route === '/engine' ? <EngineMarketing theme={theme} toggle={toggleTheme} /> : <Landing />}
        </div>
      </CEStore.Provider>
    );
  }

  let page;
  if (route === '/dashboard' || route === '/app') page = <DashboardPage />;
  else if (route === '/sources') page = <SourcesPage />;
  else if (route === '/pipeline') page = <PipelinePage />;
  else if (route.startsWith('/pipeline/')) page = <PipelineStage id={route.slice(10)} />;
  else if (route === '/corpora') page = <CorporaPage />;
  else if (route === '/ingest') page = <IngestPage />;
  else if (route.startsWith('/c/')) page = <CorpusDetail id={route.slice(3)} />;
  else if (route === '/serve') page = <ServePage />;
  else if (route === '/verify') page = <VerifyPage />;
  else if (route === '/commons') page = <CommonsPage />;
  else if (route === '/governance') page = <GovernancePage />;
  else if (route === '/audit') page = <AuditPage />;
  else if (route === '/settings') page = <SettingsPage />;
  else if (route === '/billing') page = <BillingPage />;
  else if (route === '/usage') page = <UsagePage />;
  else page = <NotFound />;

  return (
    <CEStore.Provider value={{ route, theme, toggleTheme }}>
      <div className={rootClass}>
        <AppShell route={route}>{page}</AppShell>
      </div>
    </CEStore.Provider>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
