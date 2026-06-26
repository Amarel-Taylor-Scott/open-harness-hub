/* =============================================================================
   shared/products.js — Brand & product registry (single source of truth)
   -----------------------------------------------------------------------------
   The family is a HOUSE OF BRANDS under one mission company:

     Context is Everything  ── company / mission (parent site)
       ├── Baltor.ai             ── paid SaaS · context assurance (the moat)
       └── OpenHubForAI      ── open funnel · build governed harnesses (free)

   These are SEPARATE SITES that share the same underlying design-system
   engineering. Baltor and OHH are SISTER products (peers) — neither is a parent;
   the only company-level brand is "Context is Everything".

   Renaming any brand is a ONE-LINE change: edit its `name` (and `wordmark`).
   ============================================================================= */
(function (root) {
  const BRAND = {
    name: 'OpenHarness',
    legal: 'OpenHarness, Inc.',
    mission: 'Context is Everything',          // parent / company brand + tagline
    missionHome: '../context-is-everything/Context is Everything.html',
    thesis: 'A model is only as good as the context it acts on.',
    // shared accent token lives in shared/oh-tokens.css (var(--accent))
    accentVar: '--accent',
  };

  const PRODUCTS = {
    // ---- Product 1: bounded build-a-pipeline product -----------------------
    openHarnessHub: {
      id: 'openharnesshub',
      name: 'OpenHubForAI',          // ← one-line rename point
      short: 'OHH',
      kind: 'pipelines',
      tagline: 'Build & monitor governed pipelines',
      blurb: 'Describe a task; assemble a governed, cited pipeline from vetted ' +
             'components, then run and monitor it.',
      home: '../openharnesshub/OpenHarnessHub Prototype.html',
      // house style = Direction S (ember). No extra scope class needed.
      dir: 'dir-s',
      brandScope: '',
      glyph: '⎔',
    },

    // ---- Standalone brand: Baltor.ai (the paid context-assurance SaaS) -----
    // Under the company mission "Context is Everything". Own house direction
    // (dir-d teal). OpenHubForAI is its SISTER product (free funnel), shown
    // only as a small footer link — never a switcher or a parent.
    contextEnrichment: {
      id: 'baltor',
      name: 'Baltor',                   // ← prose name (one-line rename point)
      wordmark: 'Baltor.ai',            // logo lockup ("." + "ai" is styling, not the mark)
      short: 'Baltor',
      mission: 'Context is Everything', // parent / company line
      kind: 'corpora',
      tagline: 'Context assurance for AI agents',
      // hook-first messaging (locked 2026-05-29) — `hooks` are the A/B variants
      hook: 'It’s not the model. It’s the context.',
      hooks: [
        { id: 'A', lead: 'Context fails more', tint: 'often than models.' },
        { id: 'B', lead: 'It’s not the model.', tint: 'It’s the context.' },
        { id: 'C', lead: 'Context you can trust.', tint: 'Proof you can show.' },
      ],
      subhead: 'Verified, current, and provable context for the agents you already run.',
      soul: 'Trust your context like Nome trusted Balto.',
      pillars: ['Verified', 'Current', 'Efficient', 'Provable'],
      blurb: 'Connect your sources or subscribe to verified corpora; Baltor keeps ' +
             'context correct, current and lean — and proves it — then serves it to any agent.',
      home: 'Context Enrichment Prototype.html',
      dir: 'dir-d',
      brandScope: '',
      glyph: '◳',
      // sister product — quiet footer link only
      supportedBy: { name: 'OpenHubForAI', short: 'OHH', url: '../openharnesshub/OpenHarnessHub Prototype.html' },
    },
  };

  /* ---------------------------------------------------------------------------
     PORTFOLIO — the ContextIsEverything Group holding company.
     A layered architecture: open supply graphs → Teleon runtime → governed
     products. The parent site (context-is-everything/) renders this.
     Each entity: name, wordmark, domain, kind, blurb, accent (css color),
     glyph, url (live site, or null = portfolio-only), status.
     ------------------------------------------------------------------------- */
  const GROUP = {
    name: 'ContextIsEverything Group',
    short: 'CIE Group',
    domain: 'contextiseverything.group',
    kind: 'Holding company · portfolio',
    mission: 'Context is Everything',
    // the capability lifecycle spine, left → right
    flow: ['Purpose', 'Contract', 'Runtime selection', 'Candidate', 'Evidence', 'Eval-gated promotion / rollback'],
  };
  const ENTITIES = {
    baltor: {
      name: 'Baltor', wordmark: 'Baltor.ai', domain: 'Baltor.ai', kind: 'Governed context',
      blurb: 'Verified, current, provable context served to the agents you already run.',
      accent: '#0e7c86', glyph: '◳', url: '../context-enrichment/Context Enrichment Prototype.html', status: 'live',
    },
    teleon: {
      name: 'Teleon', wordmark: 'Teleon.dev', domain: 'Teleon.dev', kind: 'Purpose-driven runtime',
      blurb: 'Runs and evolves capabilities — purpose → contract → candidate → evidence → eval-gated promotion or rollback.',
      accent: '#6d5ef0', glyph: '⟳', url: '../teleon/Teleon Prototype.html', status: 'live',
    },
    openContextHub: {
      name: 'OpenContextHub', wordmark: 'OpenContextHub.io', domain: 'OpenContextHub.io', kind: 'Open context registry',
      blurb: 'The open registry of context packs the ecosystem builds on.',
      accent: '#2f8f6b', glyph: '⬡', url: '../opencontexthub/OpenContextHub Prototype.html', status: 'live',
    },
    openSkillsHub: {
      name: 'OpenSkillsHub', wordmark: 'OpenSkillsHub.io', domain: 'OpenSkillsHub.io', kind: 'Open skill graph',
      blurb: 'A shared graph of composable, evaluated agent skills.',
      accent: '#2f7d8f', glyph: '◇', url: '../openskillshub/OpenSkillsHub Prototype.html', status: 'live',
    },
    openToolsHub: {
      name: 'OpenToolsHub', wordmark: 'OpenToolsHub.io', domain: 'OpenToolsHub.io', kind: 'Open tool graph',
      blurb: 'A registry of governed tools agents can call.',
      accent: '#8f6f2f', glyph: '⚒', url: '../opentoolshub/OpenToolsHub Prototype.html', status: 'live',
    },
    openHarnessHub: {
      name: 'OpenHarnessHub', wordmark: 'OpenHarnessHub.io', domain: 'OpenHarnessHub.io', kind: 'Open harness ecosystem',
      blurb: 'Templates, skills and eval packs — the open harness ecosystem Teleon draws from.',
      accent: '#d2542f', glyph: '⎔', url: '../openharnesshub/OpenHarnessHub Prototype.html', status: 'live',
    },
  };
  // three layers, top (governed products) → bottom (open supply), as the stack renders
  const LAYERS = [
    { id: 'product', label: 'Products', sub: 'governed products you run', items: ['baltor', 'teleon'] },
    { id: 'open', label: 'Open resources', sub: 'context · skills · tools · harnesses', items: ['openContextHub', 'openSkillsHub', 'openToolsHub', 'openHarnessHub'] },
  ];
  // key relationships (ports) — how value flows between entities
  const PORTS = [
    { from: 'baltor', to: 'teleon', label: 'Baltor consumes Teleon via PurposeTaskProviderPort — Teleon returns evidence / candidate / result, never Baltor truth.' },
    { from: 'teleon', to: 'openHarnessHub', label: 'Teleon consumes templates, skills & eval packs from the open hubs.' },
  ];
  const PORTFOLIO = { GROUP, ENTITIES, LAYERS, PORTS };

  const api = { BRAND, PRODUCTS, PORTFOLIO };
  // expose for plain-script prototypes …
  root.PRODUCTS = PRODUCTS;
  root.BRAND = BRAND;
  root.PORTFOLIO = PORTFOLIO;
  root.OPENHARNESS = api;
  // … and for any module consumer (no-op in the browser prototype)
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : this);
