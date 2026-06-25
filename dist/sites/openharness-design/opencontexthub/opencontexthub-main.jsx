/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenContextHub.io — open context registry. Built entirely on the shared hub
// module (shared/oh-hub.jsx). Only this config is local.

const E = PORTFOLIO.ENTITIES.openContextHub;
const App = makeHub({
  brand: { name: 'OpenContextHub', tld: '.io', glyph: '⬡', accent: E.accent },
  kind: E.kind,
  themeKey: 'och-theme',
  noun: 'context pack', nounPlural: 'context packs', indefinite: 'a context pack',
  heroTitle: <>The open registry of <span className="tint">context</span> for agents.</>,
  lede: 'Find, pull and publish open context packs — domain corpora, schemas and reference data — versioned, evaluated, and ready to drop into any agent or into Teleon.',
  ledeVariants: {
    A: 'Find, pull and publish open context packs — domain corpora, schemas and reference data — versioned, evaluated, and ready to drop into any agent or into Teleon.',
    B: 'Stop hand-maintaining regulatory corpora. Subscribe to verified, always-current context packs and serve them to any agent.',
    C: 'One authoritative, signed source the whole ecosystem can cite — versioned context packs, ready to drop into any agent.',
  },
  howTitle: 'Open context, ready to use.',
  howBody: <>Browse <strong>context packs</strong> the community has published, pull them by version, and serve them to your
    agents. Or publish your own — every pack is evaluated and signed before it lists.</>,
  features: [
    ['⬡', 'Domain context packs', 'Curated corpora, schemas and reference data, scoped to a domain and ready to install.'],
    ['◷', 'Versioned & current', 'Each pack is semver-pinned with a changelog so you always know what you’re serving.'],
    ['✓', 'Evaluated & signed', 'Packs clear shared eval checks and carry signed provenance you can verify.'],
  ],
  facets: ['Regulatory', 'Labor rights', 'Food safety', 'Customs', 'Finance', 'Healthcare', 'Geospatial', 'Reference'],
  installCmd: (e) => 'och add ' + e.id + '@' + (e.ver || '1.2.0') + '\n# → pulls the verified context pack into your workspace',
  entries: [
    { id: 'ilo-forced-labour', name: 'ILO Forced Labour Standards', by: '@ilo', facet: 'Labor rights', score: '4.9', installs: '1.3k', ver: '3.0.0', desc: 'Conventions C029, P029 & C105, the 11 ILO forced-labour indicators, and the Guidelines on Measurement — the authoritative basis for forced-labour due diligence.' },
    { id: 'dol-recruitment', name: 'Migrant Worker Recruitment Indicators', by: '@us-dol', facet: 'Labor rights', score: '4.7', installs: '740', ver: '2.1.0', desc: 'US DOL Comply Chain and recruitment-fee indicators for identifying exploitation across labor-supply corridors.' },
    { id: 'codex-food', name: 'Codex Alimentarius — Food Safety', by: '@codex-fao-who', facet: 'Food safety', score: '4.6', installs: '410', ver: '1.4.0', desc: 'International food standards, codes of practice and maximum residue limits from the joint FAO/WHO programme.' },
    { id: 'wco-hs', name: 'WCO Harmonized System', by: '@wco', facet: 'Customs', score: '4.5', installs: '980', ver: '5.0.0', desc: 'HS nomenclature and explanatory notes — the basis for tariff classification across 200+ jurisdictions.' },
    { id: 'eu-reg-pack', name: 'EU Regulatory Core', by: '@eu-open', facet: 'Regulatory', score: '4.9', installs: '6.2k', ver: '3.1.0', desc: 'CSDDD, EUDR and member-state transpositions with article-level anchoring.', deps: ['eurlex-schema@2.0'] },
    { id: 'fin-taxonomy', name: 'Financial Taxonomy', by: '@fintech-open', facet: 'Finance', score: '4.7', installs: '3.8k', ver: '1.9.0', desc: 'Instruments, identifiers and reporting taxonomies (FIBO-aligned).' },
    { id: 'icd11-pack', name: 'ICD-11 Clinical Context', by: '@health-commons', facet: 'Healthcare', score: '4.6', installs: '2.9k', ver: '1.4.2', desc: 'Diagnostic codes with descriptions and crosswalks to ICD-10.' },
    { id: 'geo-admin', name: 'Global Admin Boundaries', by: '@geo-open', facet: 'Geospatial', score: '4.5', installs: '2.1k', ver: '5.0.0', desc: 'Country/region/city hierarchies with codes and centroids.' },
    { id: 'units-ref', name: 'Units & Measures', by: '@ada', facet: 'Reference', score: '4.8', installs: '7.4k', ver: '2.2.0', desc: 'SI and common units with conversions — a tiny, high-value reference pack.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
