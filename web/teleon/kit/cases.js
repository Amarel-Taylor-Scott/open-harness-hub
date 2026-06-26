/* =============================================================================
   shared/cases.js — case-study content, keyed by brand id (window.CASES).
   Rendered by the kit's OhCaseStudies (index) + OhCaseStudy (detail). Plain data,
   so adding/editing a study is a content change. Load after products.js.
   Each: { id, client, sector, title, summary, metrics:[[v,k]], challenge,
           approach:[…], outcome:[…], quote:{text,who} }
   ============================================================================= */
(function (root) {
  const CASES = {
    // -------- Baltor.ai — context governance / assurance --------
    baltor: [
      {
        id: 'sanctions-screening',
        client: 'Tier-1 EU bank · Financial crime',
        sector: 'Sanctions & AML',
        title: 'Catching a sanctions entity six days before the auditors did',
        summary: 'A screening agent was reading an internal SDN list that lagged the live OFAC feed — a stale-list federal-risk event waiting to happen.',
        metrics: [['6 days', 'stale entries caught'], ['100%', 'served claims cited'], ['0', 'missed list changes since']],
        challenge: 'The bank’s screening agent matched counterparties against an internal copy of the OFAC SDN list that was refreshed on a weekly batch. Sanctions lists change several times a week — being a day stale is not an embarrassment, it’s a violation. No one could prove, at screening time, that the list was current.',
        approach: [
          'Connected the internal sanctions corpus and pinned it to the live OFAC SDN, BIS Entity List and EU consolidated feeds as authoritative sources.',
          'Reconciliation flagged an entity added six days earlier that the internal index had missed; Anti-Fragility turned the list into a refreshing object instead of a copied snapshot.',
          'Routed every screening call through verified serving, so each result carries a signed citation to the source list version.',
        ],
        outcome: [
          'The stale-entry gap closed before it produced a false clear on a sanctioned counterparty.',
          'Every screening decision now ships with a hash-verifiable citation for the examiner.',
          'Freshness moved from a weekly batch to continuous, with reconciliation escalating ambiguous matches to a human.',
        ],
        quote: { text: 'We stopped arguing about whether the list was current. Baltor proves it on every call.', who: 'Head of Financial Crime Systems' },
      },
      {
        id: 'eudr-regulatory',
        client: 'Global commodities trader · Compliance',
        sector: 'Regulatory change',
        title: 'When the EUDR date moved, the agents knew the same day',
        summary: 'A deferral to the EU Deforestation Regulation’s application date silently invalidated answers across a dozen internal corpora.',
        metrics: [['12 mo', 'deferral propagated same-day'], ['1 corpus', 'one source of truth'], ['↓ 38%', 'tokens per served pack']],
        challenge: 'When EUR-Lex deferred the EUDR application date by twelve months, the trader’s assistants kept citing the old date from internal guidance. Updating every downstream doc by hand was slow and error-prone — and impossible to prove complete.',
        approach: [
          'Baltor’s regulatory-change feed detected the EUR-Lex amendment and reconciled it against the internal EU Regulatory Corpus.',
          'The conflicting date was escalated to a reviewer with the evidence, then the corpus was hardened and re-verified.',
          'Optimization distilled the corpus to a task-tuned pack, cutting tokens per served context without losing citations.',
        ],
        outcome: [
          'Agents stopped citing the superseded date within the same day the regulation changed.',
          'One verified corpus replaced a dozen hand-maintained copies.',
          'Served packs got 38% leaner while every claim stayed cited.',
        ],
        quote: { text: 'Regulatory change used to mean a frantic doc hunt. Now it’s a reviewed diff.', who: 'Director of Regulatory Affairs' },
      },
      {
        id: 'policy-reconciliation',
        client: 'Fintech · Customer operations',
        sector: 'Internal knowledge',
        title: 'Three systems, three refund windows, one correct answer',
        summary: 'Support agents pulled refund terms from Jira, an old wiki page and the billing system — and they disagreed.',
        metrics: [['30 / 14 / 21', 'conflicting values reconciled'], ['100%', 'answers sourced'], ['↓ 52%', 'escalations to a human']],
        challenge: 'A support copilot answered refund questions from whichever document it retrieved first. Jira said 30 days, an old page said 14, billing enforced 21. Retrieval was confident — and frequently wrong.',
        approach: [
          'Reconciliation clustered the related artifacts, separated comments from decisions, and surfaced the contradiction.',
          'Enhancement attached the billing system as the authoritative source to resolve the conflict before any pack was served.',
          'The resolved policy was served with provenance, so each answer shows which system it came from.',
        ],
        outcome: [
          'The copilot now answers with the enforced 21-day window, cited to billing.',
          'Conflicting context is caught and resolved before it reaches an agent.',
          'Human escalations on refund questions fell by more than half.',
        ],
        quote: { text: 'It’s not that retrieval was broken — it was confidently retrieving the wrong truth.', who: 'VP, Customer Operations' },
      },
      {
        id: 'medical-coding',
        client: 'Health-tech platform · Clinical',
        sector: 'Healthcare',
        title: 'Keeping clinical coding context current across ICD-11 revisions',
        summary: 'A coding assistant was citing diagnostic codes from a snapshot that drifted from the live ICD-11 release.',
        metrics: [['1.4k', 'codes reconciled'], ['100%', 'served codes cited'], ['weekly', 'freshness vs release']],
        challenge: 'Clinical coding context was loaded once and rarely refreshed. When ICD-11 codes were revised, the assistant kept suggesting superseded codes — a clinical and billing risk no one caught until an audit.',
        approach: [
          'Pinned the internal coding corpus to the live ICD-11 release and the platform’s crosswalk pack.',
          'Reconciliation surfaced superseded and merged codes; Anti-Fragility turned volatile mappings into refreshing objects.',
          'Served coding context with a citation to the exact code version in force.',
        ],
        outcome: [
          'Superseded codes stopped reaching clinicians and billers.',
          'Each suggested code carries a citation to its live ICD-11 version.',
          'Freshness tracks the release cadence instead of a one-time load.',
        ],
        quote: { text: 'Stale clinical codes aren’t a typo — they’re a billing and safety problem. Now they’re caught.', who: 'Director of Clinical Informatics' },
      },
    ],

    // -------- Teleon.dev — purpose-driven runtime --------
    teleon: [
      {
        id: 'usury-50-states',
        client: 'Consumer-lending platform · Legal',
        sector: 'Multi-jurisdiction research',
        title: 'A 50-state interest-rate capability that re-proves itself',
        summary: 'Maximum legal interest rates differ by state and change by statute — a manual, source-fragile task that automation usually breaks on.',
        metrics: [['50 / 50', 'states cited'], ['0.96', 'eval score, gated'], ['auto', 'rolls back on regression']],
        challenge: 'Legal needed each US state’s maximum legal interest rate with the governing statute cited — kept current as laws change. Hand-built scrapers broke every time a state site changed; a plain agent gave confident, uncited numbers.',
        approach: [
          'Defined the outcome (cite the live statute per state) and the success criteria (covers all 50 states, re-checks on change).',
          'Teleon built candidate approaches, tested them on real statutes, and promoted only the version that cleared the bar.',
          'Wired the capability to re-run when a source changes, rolling back automatically if a regression slips the score.',
        ],
        outcome: [
          'Every state returns a citation to its live statute, not a guessed number.',
          'A source change triggers a re-proof instead of a silent break.',
          'Legal reviews a scored capability, not a pile of scraper code.',
        ],
        quote: { text: 'It behaves like a junior analyst who shows the statute — and never stops checking.', who: 'Associate General Counsel' },
      },
      {
        id: 'support-deflection',
        client: 'B2B SaaS · Support',
        sector: 'Customer support',
        title: 'A support capability that ships only when it passes',
        summary: 'The team wanted cited, fast answers from their docs — without babysitting prompts or shipping regressions.',
        metrics: [['1,240', 'real examples in the gate'], ['< 2s', 'p95 answer time'], ['+18 pts', 'deflection rate']],
        challenge: 'Every prompt tweak was a gamble: some questions got better while others quietly regressed, and no one could tell until customers complained.',
        approach: [
          'Described the outcome (answer from our docs, with citations, under two seconds) and locked the success criteria.',
          'Teleon evaluated each candidate against 1,240 real tickets and promoted only the ones that improved without regressions.',
          'Underperforming versions rolled back on their own, so quality only moved one direction.',
        ],
        outcome: [
          'Answers ship cited and fast, proven on real tickets before customers see them.',
          'Regressions roll back automatically instead of reaching production.',
          'Deflection rose 18 points with no glue code to maintain.',
        ],
        quote: { text: 'We stopped shipping prompt changes on vibes. Now it’s proven or it doesn’t ship.', who: 'Head of Support Engineering' },
      },
      {
        id: 'contract-extraction',
        client: 'Procurement team · Enterprise',
        sector: 'Document understanding',
        title: 'Clause extraction a reviewer would actually sign off',
        summary: 'Pulling renewal, liability and termination clauses across thousands of contracts — accurately enough to act on.',
        metrics: [['9 clause types', 'extracted + cited'], ['0.93', 'eval score, gated'], ['3 wks → 2 days', 'review cycle']],
        challenge: 'A generic extractor missed edge-case phrasings and gave no provenance, so every result needed a full manual re-read — defeating the point.',
        approach: [
          'Set the outcome (extract nine clause types with a citation to the source span) and the bar for acceptance.',
          'Teleon proved candidates on a labeled set of real contracts and promoted the passing approach.',
          'Each extraction links back to its clause, so reviewers verify instead of re-reading.',
        ],
        outcome: [
          'Reviewers confirm cited spans instead of reading every contract end to end.',
          'Edge-case phrasings are caught because the capability is tested on real ones.',
          'The review cycle dropped from three weeks to two days.',
        ],
        quote: { text: 'The citations are what won the lawyers over — they can check the source in one click.', who: 'Director of Procurement' },
      },
      {
        id: 'incident-runbooks',
        client: 'Platform reliability team',
        sector: 'DevOps & reliability',
        title: 'An on-call capability that stays correct as systems change',
        summary: 'Runbook answers needed to reflect the current architecture — not last quarter’s — and prove they were tested.',
        metrics: [['320', 'runbooks in the gate'], ['0.94', 'eval score, gated'], ['↓ 41%', 'mean time to context']],
        challenge: 'On-call engineers got plausible-but-stale runbook answers during incidents, and every system change risked silently invalidating them.',
        approach: [
          'Defined the outcome (answer with the current runbook step + a link to the source) and the bar.',
          'Teleon proved candidates against real past incidents and promoted only what passed.',
          'Wired re-proof on architecture changes so stale steps roll back automatically.',
        ],
        outcome: [
          'Answers reflect the current architecture, with a source link.',
          'System changes trigger a re-proof instead of silent staleness.',
          'Time-to-context during incidents dropped 41%.',
        ],
        quote: { text: 'During an incident is the worst time to discover your runbook is six months stale.', who: 'SRE Lead' },
      },
    ],

    // -------- OpenHubForAI — governed pipelines --------
    openharnesshub: [
      {
        id: 'csddd-supplier-grading',
        client: 'Manufacturer · ESG',
        sector: 'Supply-chain due diligence',
        title: 'Grading 4,000 suppliers against CSDDD — with the article cited',
        summary: 'Due-diligence grading that a regulator could audit, assembled from vetted components instead of bespoke code.',
        metrics: [['4,000', 'suppliers graded'], ['13 langs', 'corpus coverage'], ['100%', 'findings cited']],
        challenge: 'The ESG team needed to grade suppliers against the EU Corporate Sustainability Due Diligence Directive — defensibly, at scale, and kept current as the articles change.',
        approach: [
          'Described the task; OpenHubForAI assembled a governed harness from vetted classification, knowledge and grading components.',
          'Pinned the CSDDD article corpus (13 languages) as a live knowledge pack so amendments flow in via change-data-capture.',
          'Froze the deterministic stages so capability grew without per-run model cost.',
        ],
        outcome: [
          'Every supplier grade carries a citation to the governing CSDDD article.',
          'Article amendments propagate through the harness instead of triggering a rebuild.',
          'Most of the pipeline runs deterministically — capability up, cost flat.',
        ],
        quote: { text: 'We added capability without adding spend, because most of it is frozen and cited.', who: 'Head of Sustainability' },
      },
      {
        id: 'eudr-geocheck',
        client: 'Agri-commodity importer',
        sector: 'Deforestation compliance',
        title: 'An EUDR geo-check harness that holds up to an audit',
        summary: 'Plot-level deforestation-free proofs, assembled and monitored as a governed pipeline.',
        metrics: [['11k', 'plots checked'], ['append-only', 'audit trail'], ['0', 'unsourced claims served']],
        challenge: 'EUDR requires deforestation-free proof tied to plot geolocation. The importer needed a repeatable, auditable check — not a one-off script that no one could verify later.',
        approach: [
          'Assembled a governed harness combining geolocation parsing, a deforestation knowledge pack and a grading step.',
          'Gated unsourced outputs so nothing serves without provenance.',
          'Recorded every run in an append-only audit log with the policy it ran under.',
        ],
        outcome: [
          'Plot-level checks produce deforestation-free proofs an auditor can trace.',
          'The gate blocks any unsourced claim before it reaches a decision.',
          'The full run history is exportable as a compliance trail.',
        ],
        quote: { text: 'When the auditor asked “show your work,” the harness already had.', who: 'Trade Compliance Lead' },
      },
      {
        id: 'sanctions-flow',
        client: 'Payments provider',
        sector: 'Sanctions screening',
        title: 'Qualify, skip or route — before any model spend',
        summary: 'A screening flow built from pattern and anti-pattern packs that decides cheaply, then escalates only what matters.',
        metrics: [['↓ 71%', 'model calls'], ['2 packs', 'pattern + anti-pattern'], ['append-only', 'receipts']],
        challenge: 'Running every transaction through a model was expensive and slow, and most were obvious clears or obvious blocks.',
        approach: [
          'Composed combinable pattern and anti-pattern packs to qualify, skip or route before any model spend.',
          'Sent only ambiguous cases to the model-backed review stage.',
          'Logged each decision with its route and policy for the record.',
        ],
        outcome: [
          'Model calls dropped 71% by deciding the obvious cases deterministically.',
          'Ambiguous transactions still get full review, with receipts.',
          'Cost per screened transaction fell sharply without weakening coverage.',
        ],
        quote: { text: 'The cheapest model call is the one you don’t make. The harness makes that call for us.', who: 'Director of Payments Risk' },
      },
    ],

    // -------- Open registries (lighter, 2 each) --------
    opencontexthub: [
      {
        id: 'publisher-sanctions',
        client: 'Standards body · Public good',
        sector: 'Authoritative publishing',
        title: 'Publishing a sanctions corpus the whole ecosystem can cite',
        summary: 'A public-interest body published a signed, continuously-verified context pack other tools subscribe to.',
        metrics: [['3,120', 'subscribers'], ['several/wk', 'verified cadence'], ['signed', 'every version']],
        challenge: 'Authoritative facts existed but were copied, diverged and went stale across downstream tools, with no shared, citable source.',
        approach: [
          'Published the corpus to Open Context Hub as a signed, versioned pack.',
          'Wired continuous verification so each release ships current and hash-verifiable.',
          'Let downstream agents subscribe instead of copying.',
        ],
        outcome: [
          'One authoritative pack replaced dozens of drifting copies.',
          'Subscribers cite a signed version instead of a guess.',
          'Updates propagate to everyone on publish.',
        ],
        quote: { text: 'We publish the truth once; the ecosystem cites it everywhere.', who: 'Standards Programme Director' },
      },
      {
        id: 'commons-reuse',
        client: 'AI platform team',
        sector: 'Context reuse',
        title: 'Skipping months of corpus-building by subscribing',
        summary: 'A platform team adopted community-verified corpora instead of hand-maintaining regulatory data.',
        metrics: [['weeks → hours', 'to first corpus'], ['0', 'data hand-maintained'], ['100%', 'cited at serve']],
        challenge: 'Maintaining regulatory corpora in-house was a treadmill no one wanted to own.',
        approach: [
          'Browsed the commons and subscribed to verified corpora for the needed domains.',
          'Served them straight into existing agents.',
          'Let the publisher’s verification keep them current.',
        ],
        outcome: [
          'First verified corpus live in hours, not weeks.',
          'No internal team on the maintenance treadmill.',
          'Served context stays cited and current automatically.',
        ],
        quote: { text: 'Why hand-maintain regulatory data when someone authoritative already does?', who: 'Platform Engineering Lead' },
      },
    ],
    openskillshub: [
      {
        id: 'skill-graph-adoption',
        client: 'Agent platform · Tooling',
        sector: 'Composable skills',
        title: 'Composing evaluated skills instead of rebuilding them',
        summary: 'A team assembled agent capabilities from a shared graph of evaluated, composable skills.',
        metrics: [['↓ 60%', 'time to a new capability'], ['evaluated', 'every skill'], ['reused', 'across agents']],
        challenge: 'Every new agent re-implemented the same skills slightly differently, with no shared quality bar.',
        approach: [
          'Pulled evaluated skills from Open Skills Hub instead of rebuilding.',
          'Composed them into agent capabilities with known behavior.',
          'Contributed improvements back to the graph.',
        ],
        outcome: [
          'New capabilities assembled in a fraction of the time.',
          'Every skill carries an evaluation, not a vibe.',
          'Improvements compound across the whole platform.',
        ],
        quote: { text: 'Our agents stopped reinventing the same five skills.', who: 'Head of Agent Platform' },
      },
    ],
    opentoolshub: [
      {
        id: 'tool-registry',
        client: 'Enterprise AI team',
        sector: 'Governed tools',
        title: 'Giving agents tools you can actually govern',
        summary: 'A team sourced governed, callable tools from a registry instead of wiring ad-hoc integrations.',
        metrics: [['governed', 'every tool call'], ['1 registry', 'one place to vet'], ['audited', 'calls logged']],
        challenge: 'Ad-hoc tool integrations were impossible to vet, govern or audit consistently.',
        approach: [
          'Adopted governed tools from Open Tools Hub with clear contracts.',
          'Gave agents a vetted catalog instead of bespoke wiring.',
          'Logged every tool call for audit.',
        ],
        outcome: [
          'Tool calls run under a governed contract.',
          'One registry to vet and update, not many integrations.',
          'Every call is auditable after the fact.',
        ],
        quote: { text: 'Agents are only as safe as the tools they can call. Now those are governed.', who: 'Director of AI Engineering' },
      },
    ],
    openskilltotool: [
      {
        id: 'skill-to-tool-hardening',
        client: 'Platform & internal teams',
        sector: 'Skill→tool conversion',
        title: 'Turning an open-ended skill into a dependable tool',
        summary: 'A team converted a context-guided skill into a deterministic, typed tool — same input, same shape, every call — without losing its eval or provenance.',
        metrics: [['deterministic', 'fixed contract'], ['scopes', 'least-privilege'], ['eval + provenance', 'carried across']],
        challenge: 'A useful skill was open-ended: great for exploration, but too variable to call as a dependable production tool, and hand-porting it lost the eval score and provenance.',
        approach: [
          'Ran the skill through a converter to emit a typed tool contract — fixed input/output schema.',
          'Declared the least-privilege scopes the skill actually needed; nothing blind.',
          'Carried the skill’s eval score and signed provenance across to the tool.',
          'Published the result to Open Tools Hub and called it from Teleon.',
        ],
        outcome: [
          'The same task now returns the same shape every call — deterministic, not open-ended.',
          'The tool is scoped and auditable, with provenance back to the source skill.',
          'No hand-written wrapper, and the eval evidence survived the conversion.',
        ],
        quote: { text: 'Skills are flexible; tools are dependable. We stopped choosing — we convert.', who: 'Platform Lead' },
      },
    ],
    openreviewhub: [
      {
        id: 'repo-reproduction',
        client: 'Applied research & platform teams',
        sector: 'Review intelligence',
        title: 'The repo built clean — and one headline claim still didn’t hold',
        summary: 'Before adopting a popular open agent-runtime, a team pulled its OpenReviewHub review instead of trusting the README — and found a reproduced demo but a false coverage claim.',
        metrics: [['4m12s', 'quickstart to first run'], ['81%', 'real coverage vs “100%” claimed'], ['re-run', 'verdict, not a star']],
        challenge: 'A team was about to standardise on an open agent-runtime because its README looked strong and its star count was high. But a README is not a result: nobody had actually rebuilt it from a clean clone, timed the quickstart, or checked whether the test-coverage claim was real. Discovery is not trust.',
        approach: [
          'Pulled the signed OpenReviewHub review of the repo at a pinned commit instead of trusting the landing page.',
          'Read the axis scorecard — capability, verifiability, reproducibility, robustness — and the claim → evidence → verdict ledger.',
          'Reproduced the review locally: fresh container, documented toolchain, the project’s own test and coverage targets.',
          'Acted on the explicit method & scope note — what was tested, and what wasn’t (the GPU path, the cloud-deploy guide).',
        ],
        outcome: [
          'The quickstart genuinely reproduced — 4m12s to first run — so the core capability was real, not marketing.',
          'The “100% test coverage” claim failed: the coverage report showed 81%. The team adopted with eyes open, not on faith.',
          'The decision rode on a re-run verdict scoped to exactly what was tested — evidence a reviewer could audit, never a star rating.',
        ],
        quote: { text: 'A green badge here means it actually reproduced. We stopped adopting on README vibes.', who: 'Staff Engineer, Platform' },
      },
    ],
  };

  root.CASES = CASES;
  if (typeof module !== 'undefined' && module.exports) module.exports = CASES;
})(typeof window !== 'undefined' ? window : this);
