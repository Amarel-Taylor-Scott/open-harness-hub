/* =============================================================================
   shared/products.js — Brand & product registry (single source of truth)
   -----------------------------------------------------------------------------
   The family is a HOUSE OF BRANDS under one mission company:

     AI Done Right          ── company / mission (parent site)
       ├── Baltor.ai             ── paid SaaS · context assurance (the moat)
       └── OpenHubForAI      ── open funnel · build governed harnesses (free)

   These are SEPARATE SITES that share the same underlying design-system
   engineering. Baltor and OpenHubForAI are SISTER products (peers) — neither is a parent;
   the only company-level brand is "AI Done Right".

   Renaming any brand is a ONE-LINE change: edit its `name` (and `wordmark`).
   ============================================================================= */
(function (root) {
  const BRAND = {
    name: 'AI Done Right',
    legal: 'AI Done Right, Inc.',
    mission: 'AI, done right.',                 // parent / company brand + tagline
    missionHome: '../context-is-everything/Context is Everything.html',
    thesis: 'Models are commoditizing; trustworthy, governed AI capability is the moat.',
    // shared accent token lives in shared/oh-tokens.css (var(--accent))
    accentVar: '--accent',
  };

  const PRODUCTS = {
    // ---- Product 1: bounded build-a-pipeline product -----------------------
    openHubForAI: {
      id: 'openhubforai',
      name: 'OpenHubForAI',          // ← one-line rename point
      short: 'OpenHubForAI',
      kind: 'pipelines',
      tagline: 'Build & monitor governed pipelines',
      blurb: 'Describe a task; assemble a governed, cited pipeline from vetted ' +
             'components, then run and monitor it.',
      home: '../openhubforai/OpenHubForAI.html',
      // house style = Direction S (ember). No extra scope class needed.
      dir: 'dir-s',
      brandScope: '',
      glyph: '⎔',
    },

    // ---- Standalone brand: Baltor.ai (the paid context-assurance SaaS) -----
    // Under the company mission "AI Done Right". Own house direction
    // (dir-d teal). OpenHubForAI is its SISTER product (free funnel), shown
    // only as a small footer link — never a switcher or a parent.
    contextEnrichment: {
      id: 'baltor',
      name: 'Baltor',                   // ← prose name (one-line rename point)
      wordmark: 'Baltor.ai',            // logo lockup ("." + "ai" is styling, not the mark)
      short: 'Baltor',
      mission: 'AI Done Right', // parent / company line
      kind: 'corpora',
      tagline: 'Context assurance for AI agents',
      // hook-first messaging (locked 2026-05-29) — `hooks` are the A/B variants (A–G).
      // Spread: problem-framing (A,B,F) · trust/proof (C) · engine/process (D,E,G).
      hook: 'It’s not the model. It’s the context.',
      hooks: [
        { id: 'A', lead: 'Context fails more', tint: 'often than models.' },
        { id: 'B', lead: 'It’s not the model.', tint: 'It’s the context.' },
        { id: 'C', lead: 'Context you can trust.', tint: 'Proof you can show.' },
        { id: 'D', lead: 'Retrieval fetches it.', tint: 'Baltor verifies it.' },
        { id: 'E', lead: 'Reconciled, hardened,', tint: 'enhanced, optimized.' },
        { id: 'F', lead: 'Stale context is', tint: 'a silent outage.' },
        { id: 'G', lead: 'Not retrieval.', tint: 'Context governance.' },
        { id: 'H', lead: 'Context hardening', tint: 'for AI agents.' },
        { id: 'I', lead: 'Context engineering picks it.', tint: 'Baltor governs it.' },
      ],
      subhead: 'Verified, current, and provable context for the agents you already run.',
      // additional A/B surfaces (add variants freely — ids drive the experiment options).
      // baltor_subhead
      subheads: [
        { id: 'A', text: 'Verified, current, and provable context for the agents you already run.' },
        { id: 'B', text: 'Harden your context before your agents ever act on it.' },
        { id: 'C', text: 'Catch stale, conflicting and unsourced context before it reaches an agent.' },
        { id: 'D', text: 'Governed context — reconciled, hardened, enhanced and optimized — served to any agent.' },
        { id: 'E', text: 'The governed context layer for the agents you already run — verified, current and provable.' },
      ],
      // baltor_cta (primary hero button)
      ctas: [
        { id: 'A', label: 'Connect a source →' },
        { id: 'B', label: 'Start hardening →' },
        { id: 'C', label: 'Verify your corpus →' },
        { id: 'D', label: 'Govern your context →' },
      ],
      soul: 'Trust your context like Nome trusted Balto.',
      pillars: ['Verified', 'Current', 'Efficient', 'Provable'],
      blurb: 'Connect your sources or subscribe to verified corpora; Baltor keeps ' +
             'context correct, current and lean — and proves it — then serves it to any agent.',
      home: 'Context Enrichment.html',
      dir: 'dir-d',
      brandScope: '',
      glyph: '◳',
      // sister product — quiet footer link only
      supportedBy: { name: 'OpenHubForAI', short: 'OpenHubForAI', url: '../openhubforai/OpenHubForAI.html' },
    },
  };

  /* ---------------------------------------------------------------------------
     PORTFOLIO — the AI Done Right holding company.
     A layered architecture: open supply graphs → Teleon runtime → governed
     products. The parent site (context-is-everything/) renders this.
     Each entity: name, wordmark, domain, kind, blurb, accent (css color),
     glyph, url (live site, or null = portfolio-only), status.
     ------------------------------------------------------------------------- */
  const GROUP = {
    name: 'AI Done Right',
    short: 'AI Done Right',
    domain: 'aidoneright.dev',
    kind: 'AI platform company',
    mission: 'AI, done right.',
    // the capability lifecycle spine, left → right
    flow: ['Purpose', 'Contract', 'Runtime selection', 'Candidate', 'Evidence', 'Eval-gated promotion / rollback'],
  };
  const ENTITIES = {
    baltor: {
      name: 'Baltor', wordmark: 'Baltor.ai', domain: 'Baltor.ai', kind: 'Governed context',
      blurb: 'Verified, current, provable context served to the agents you already run.',
      accent: '#0e7c86', glyph: '◳', url: '../context-enrichment/Context Enrichment.html', status: 'live',
    },
    teleon: {
      name: 'Teleon', wordmark: 'Teleon.dev', domain: 'Teleon.dev', kind: 'Purpose-driven runtime',
      blurb: 'Runs and evolves capabilities, moving from purpose and contract to candidate, evidence, and an eval gated promotion or rollback.',
      accent: '#6d5ef0', glyph: '⟳', url: '../teleon/Teleon.html', status: 'live',
    },
    aidevobserver: {
      name: 'AIDevObserver', wordmark: 'AIDevObserver', domain: 'aidevobserver.io', kind: 'AI-usage review',
      blurb: 'Reviews how your team uses AI coding agents: reinvention, waste, risky commands, and cheaper paths.',
      accent: '#b25fd6', glyph: '\u25c9', url: '../aidevobserver/index.html', status: 'live',
    },
    openContextHub: {
      name: 'OpenContextHub', wordmark: 'OpenContextHub', domain: 'OpenHubForAI.io', kind: 'Open context registry',
      blurb: 'The open registry of context packs the ecosystem builds on.',
      accent: '#2f8f6b', glyph: '⬡', url: '../opencontexthub/OpenContextHub.html', status: 'live',
    },
    openSkillsHub: {
      name: 'OpenSkillsHub', wordmark: 'OpenSkillsHub', domain: 'OpenHubForAI.io', kind: 'Open skill graph',
      blurb: 'A shared graph of composable, evaluated agent skills.',
      accent: '#2f7d8f', glyph: '◇', url: '../openskillshub/OpenSkillsHub.html', status: 'live',
    },
    openToolsHub: {
      name: 'OpenToolsHub', wordmark: 'OpenToolsHub', domain: 'OpenHubForAI.io', kind: 'Open tool graph',
      blurb: 'A registry of governed tools agents can call.',
      accent: '#8f6f2f', glyph: '⚒', url: '../opentoolshub/OpenToolsHub.html', status: 'live',
    },
    openSkillToTool: {
      name: 'OpenSkillToTool', wordmark: 'OpenSkillToTool.io', domain: 'OpenSkillToTool.io', kind: 'Skill→tool conversion',
      blurb: 'Turns governed skills into typed, callable tools — the bridge between OpenSkillsHub and OpenToolsHub.',
      accent: '#cf5a96', glyph: '⇋', url: '../openskilltotool/OpenSkillToTool.html', status: 'live',
    },
    openHubForAI: {
      name: 'OpenHubForAI', wordmark: 'OpenHubForAI', domain: 'OpenHubForAI.io', kind: 'Open store',
      blurb: 'The open store of context, tools, skills, and harnesses that both products consume. Browse every record.',
      accent: '#3b6fd4', glyph: '⎔', url: '../openhubforai/OpenHubForAI.html', status: 'live',
    },
    openMCPHub: {
      name: 'OpenMCPHub', wordmark: 'OpenMCPHub', domain: 'OpenHubForAI.io', kind: 'MCP server intelligence',
      blurb: 'MCP server registry, risk, conformance and install profiles — discovery is not trust.',
      accent: '#5b7cf0', glyph: '⌁', url: '../openmcphub/OpenMCPHub.html', status: 'live',
    },
    openCompressionHub: {
      name: 'OpenCompressionHub', wordmark: 'OpenCompressionHub', domain: 'OpenHubForAI.io', kind: 'Compression & budget intelligence',
      blurb: 'Context compression, token budgeting and fidelity benchmarks — reduction is not success unless fidelity survives.',
      accent: '#9bd61f', glyph: '⊟', url: '../opencompressionhub/OpenCompressionHub.html', status: 'live',
    },
    openBenchmarkHub: {
      name: 'OpenBenchmarkHub', wordmark: 'OpenBenchmarkHub', domain: 'OpenHubForAI.io', kind: 'Benchmark intelligence',
      blurb: 'Benchmark cards, metrics and result records — evidence, not authority; a result cannot promote a candidate alone.',
      accent: '#e0556a', glyph: '▦', url: '../openbenchmarkhub/OpenBenchmarkHub.html', status: 'live',
    },
    openReviewHub: {
      name: 'OpenReviewHub', wordmark: 'OpenReviewHub', domain: 'OpenHubForAI.io', kind: 'Review intelligence',
      blurb: 'Reviews papers and repos for capability, verifiability and reproducibility — a claim is not a capability until it reproduces.',
      accent: '#9d4edd', glyph: '⊙', url: '../openreviewhub/OpenReviewHub.html', status: 'live',
    },
    // ── Private preview — built on the kit, in private preview ──
    // Each: drawn from a real modular component, distinct from the 9 live hubs, with an
    // open_trigger + a future (public) accent. status:'private' → muted accent now; the
    // saturated futureAccent is adopted when the hub is opened. discovery ≠ trust.
    openTemplatesHub: {
      name: 'OpenTemplatesHub', wordmark: 'OpenTemplatesHub', domain: 'OpenHubForAI.io', kind: 'Template families',
      blurb: 'Reusable schema · runtime · resource · API-UI · inference · PurposeTask template families — the starting shapes you instantiate. Templates generate shapes; harnesses prove the outputs.',
      accent: '#6d6a86', futureAccent: '#7c5cff', glyph: '⊞', url: '../opentemplateshub/OpenTemplatesHub.html', status: 'private',
      source: 'Shared Template Registry', openTrigger: 'a public template / scaffold registry enters the lane',
    },
    openEndpointHub: {
      name: 'OpenEndpointHub', wordmark: 'OpenEndpointHub', domain: 'OpenHubForAI.io', kind: 'Endpoint due-diligence',
      blurb: 'Governed due-diligence on LLM endpoints (free + low-cost) and gateways — with data-class & jurisdiction eligibility: what data may I send where.',
      accent: '#5f7585', futureAccent: '#1f8fd6', glyph: '⇄', url: '../openendpointhub/OpenEndpointHub.html', status: 'private',
      source: 'endpoint registries + free_endpoint_intel', openTrigger: 'a public governed-endpoint directory launches',
    },
    openEnvironmentHub: {
      name: 'OpenEnvironmentHub', wordmark: 'OpenEnvironmentHub', domain: 'OpenHubForAI.io', kind: 'Eval environments',
      blurb: 'Verifiable agent eval environments and reward specs — the task world a candidate is run against, not the score it earns.',
      accent: '#5f7a6e', futureAccent: '#2f9e5a', glyph: '⊕', url: '../openenvhub/OpenEnvHub.html', status: 'private',
      source: 'Environment + Reward Spine', openTrigger: 'a public agent eval-environment registry appears',
    },
    openSandboxHub: {
      name: 'OpenSandboxHub', wordmark: 'OpenSandboxHub', domain: 'OpenHubForAI.io', kind: 'Sandbox intelligence',
      blurb: 'Isolated sandbox registry with risk & conformance (E2B · Daytona · agent-sandbox class) — discovery is not trust, applied to the runtimes that execute agent code.',
      accent: '#7a6f86', futureAccent: '#b5562f', glyph: '⊠', url: '../opensandboxhub/OpenSandboxHub.html', status: 'private',
      source: 'sandbox registries', openTrigger: 'a public sandbox directory enters the lane',
    },
    openAgentHub: {
      name: 'OpenAgentHub', wordmark: 'OpenAgentHub', domain: 'OpenHubForAI.io', kind: 'Agent-runtime registry',
      blurb: 'The runtimes that run agents — bounded adapters with run receipts. Skills are know-how, tools are executables; this is the runtime they execute in.',
      accent: '#7a7460', futureAccent: '#0f9e8e', glyph: '◈', url: '../openagenthub/OpenAgentHub.html', status: 'private',
      source: 'agent_runtime_catalog + teleon', openTrigger: 'a public agent-runtime registry launches',
    },
    openReceiptHub: {
      name: 'OpenReceiptHub', wordmark: 'OpenReceiptHub', domain: 'OpenHubForAI.io', kind: 'Portable receipts',
      blurb: 'Portable, signed receipts — model invocation, served pack, run, review, approval — that travel with the artifact and verify anywhere. The attestation face of the family.',
      accent: '#72786b', futureAccent: '#c79a2e', glyph: '⊡', url: '../openreceipthub/OpenReceiptHub.html', status: 'private',
      source: 'receipt + AI-BOM / provenance spine (Sigstore · in-toto · CycloneDX)', openTrigger: 'a portable AI-receipt / attestation standard gains traction',
    },
    openStateHub: {
      name: 'OpenStateHub', wordmark: 'OpenStateHub', domain: 'OpenHubForAI.io', kind: 'Agent state',
      blurb: 'Durable, governed working state for agents — memory, blackboard, graph — versioned with provenance. Distinct from context truth packs: this is the state agents write.',
      accent: '#6c6f86', futureAccent: '#0ea5a5', glyph: '◧', url: '../openstatehub/OpenStateHub.html', status: 'private',
      source: 'persistent agent-state spine (blackboard · mem0 / letta / graphiti class)', openTrigger: 'a public governed agent-state / memory registry launches',
    },
    openRoutingHub: {
      name: 'OpenRoutingHub', wordmark: 'OpenRoutingHub', domain: 'OpenHubForAI.io', kind: 'Model-routing policy',
      blurb: 'Open abstracts for model-routing POLICY — preference cards, numeric provider-selection graphs, lane policies (dev · agent · interactive · batch · self-host), governed fallback chains and the receipt of which model actually served. Policy, not endpoints; cards, not a runtime.',
      accent: '#69728a', futureAccent: '#4c6ef5', glyph: '⇉', url: '../openroutinghub/OpenRoutingHub.html', status: 'private',
      source: 'Inference Gateway + OIPS · numeric provider-selection graph · LLM-economics lanes', openTrigger: 'a portable model-routing / LLM-gateway-policy registry competitor appears OR the inference-gateway public release',
    },
    // ── Context-governance method hubs — Baltor's engine stages, opened as registries ──
    openReconciliationHub: {
      name: 'OpenReconciliationHub', wordmark: 'OpenReconciliationHub', domain: 'OpenHubForAI.io', kind: 'Reconciliation methods',
      blurb: 'Open methods for cluster alignment — dedupe related artifacts, map relationships, separate comments from decisions, and surface contradictions across tickets, docs, code and memory.',
      accent: '#6a7080', futureAccent: '#2f6fae', glyph: '⇌', url: '../openreconciliationhub/OpenReconciliationHub.html', status: 'private',
      source: 'Baltor engine · Reconcile stage', openTrigger: 'an open context-reconciliation standard emerges',
    },
    openHardeningHub: {
      name: 'OpenHardeningHub', wordmark: 'OpenHardeningHub', domain: 'OpenHubForAI.io', kind: 'Hardening methods',
      blurb: 'Open methods for robust object hardening — detect facts likely to change in source systems and replace brittle text with knowledge objects that refresh over time.',
      accent: '#7a6f6a', futureAccent: '#b5562f', glyph: '⊛', url: '../openhardeninghub/OpenHardeningHub.html', status: 'private',
      source: 'Baltor engine · Harden stage', openTrigger: 'an open context-hardening standard emerges',
    },
    openEnrichmentHub: {
      name: 'OpenEnrichmentHub', wordmark: 'OpenEnrichmentHub', domain: 'OpenHubForAI.io', kind: 'Enrichment methods',
      blurb: 'Open methods for context enrichment — add metadata, relationships, architecture / service-graph links and event / schema facts; connect the missing context.',
      accent: '#6a7a72', futureAccent: '#2f9e7a', glyph: '✦', url: '../openenrichmenthub/OpenEnrichmentHub.html', status: 'private',
      source: 'Baltor engine · Enhance stage', openTrigger: 'an open context-enrichment standard emerges',
    },
    openOptimizationHub: {
      name: 'OpenOptimizationHub', wordmark: 'OpenOptimizationHub', domain: 'OpenHubForAI.io', kind: 'Optimization methods',
      blurb: 'Open methods for pack shaping — summarize and distill, convert unstructured context into structured objects, rank relevance and fit the result to the task budget.',
      accent: '#76707f', futureAccent: '#c8902f', glyph: '⊿', url: '../openoptimizationhub/OpenOptimizationHub.html', status: 'private',
      source: 'Baltor engine · Optimize stage', openTrigger: 'an open context-optimization standard emerges',
    },
    openVerificationHub: {
      name: 'OpenVerificationHub', wordmark: 'OpenVerificationHub', domain: 'OpenHubForAI.io', kind: 'Verification methods',
      blurb: 'Open methods for verification — bind every claim to a source, check it is provable by hash, and hold out what can’t be proven. A claim served without a citation is a liability.',
      accent: '#6f7a80', futureAccent: '#1f9b8e', glyph: '⊨', url: '../openverificationhub/OpenVerificationHub.html', status: 'private',
      source: 'Baltor engine · Verify stage', openTrigger: 'an open context-verification / citation standard emerges',
    },
  };
  // Flip-to-public mechanism: a private-bench hub stores a muted `accent` for its
  // pre-launch look and a saturated `futureAccent` for when it opens. Resolve the
  // effective accent from status here, so OPENING A HUB IS A ONE-LINE CHANGE
  // (status: 'private' → 'live'): the muted accent swaps to the launch color and the
  // "Private preview" banner (gated on access, derived from status) disappears.
  Object.values(ENTITIES).forEach((e) => {
    if (e.futureAccent) {
      e.privateAccent = e.accent;          // the muted pre-launch accent
      e.launchAccent = e.futureAccent;     // the saturated public accent
      e.accent = e.status === 'live' ? e.futureAccent : e.accent;
    }
  });
  // The parent shows FOUR products (Claude Design "AI Done Right", 2026-06-27: "four products,
  // one shared foundation"). The Open*Hub registries are now INTERNAL to OpenHubForAI (its
  // catalog), NOT parent-level products — consolidated here losslessly: the rosters live on in
  // OPENHUB_REGISTRIES and every entity is preserved in ENTITIES for the hub engines + the
  // OpenHubForAI surface to render its registries.
  const OPENHUB_REGISTRIES = {
    live: ['openContextHub', 'openSkillsHub', 'openToolsHub', 'openSkillToTool', 'openMCPHub', 'openCompressionHub', 'openBenchmarkHub', 'openReviewHub'],
    preview: ['openTemplatesHub', 'openEndpointHub', 'openEnvironmentHub', 'openSandboxHub', 'openAgentHub', 'openReceiptHub', 'openStateHub', 'openRoutingHub', 'openReconciliationHub', 'openHardeningHub', 'openEnrichmentHub', 'openOptimizationHub', 'openVerificationHub'],
  };
  const LAYERS = [
    { id: 'product', label: 'Products', sub: 'governed products you run', items: ['teleon', 'baltor', 'aidevobserver'] },
    { id: 'resource', label: 'Resources', sub: 'the open store the products draw from', items: ['openHubForAI'] },
  ];
  // key relationships (ports) — how value flows between entities
  const PORTS = [
    { from: 'baltor', to: 'teleon', label: 'Baltor consumes Teleon via PurposeTaskProviderPort — Teleon returns evidence / candidate / result, never Baltor truth.' },
    { from: 'teleon', to: 'openHubForAI', label: 'Teleon consumes templates, skills & eval packs from the open hubs.' },
  ];
  const PORTFOLIO = { GROUP, ENTITIES, LAYERS, PORTS, OPENHUB_REGISTRIES };

  const api = { BRAND, PRODUCTS, PORTFOLIO };
  // expose for plain-script prototypes …
  root.PRODUCTS = PRODUCTS;
  root.BRAND = BRAND;
  root.PORTFOLIO = PORTFOLIO;
  root.OPENHARNESS = api;
  // … and for any module consumer (no-op in the browser prototype)
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : this);
