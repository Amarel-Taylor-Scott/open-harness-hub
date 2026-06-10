/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenEnrichmentHub.io — open methods for the ENHANCE stage of context governance.
// PRIVATE-FIRST candidate. Baltor's engine stage, opened as a registry of methods:
// context enrichment — add the metadata, relationships and connective context that's missing.

const E = PORTFOLIO.ENTITIES.openEnrichmentHub;
const App = makeHub({
  brand: { name: 'OpenEnrichmentHub', tld: '.io', glyph: '✦', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'oenr-theme',
  noun: 'method', nounPlural: 'methods', indefinite: 'a method',
  heroTitle: <>Context <span className="tint">enrichment.</span></>,
  lede: 'OpenEnrichmentHub is the open registry of enrichment methods — the techniques that add relevant external context objects, metadata, relationships, architecture / service-graph links and event / schema facts, and connect the missing connective context. The Enhance stage of context governance, opened as methods.',
  ledeVariants: {
    A: 'OpenEnrichmentHub is the open registry of enrichment methods — the techniques that add relevant external context objects, metadata, relationships, architecture / service-graph links and event / schema facts, and connect the missing connective context. The Enhance stage of context governance, opened as methods.',
    B: 'Retrieval finds the fact; enrichment adds what it connects to. Methods that add metadata, relationships and service-graph links — the missing context.',
    C: 'Connect the missing context. Open methods that enrich an object with metadata, relationships, architecture links and event / schema facts.',
  },
  howTitle: 'Add the connective context that’s missing.',
  howBody: <>Pull an <strong>enrichment method</strong> and run it over an object. It <strong>adds metadata</strong> and
    external context, <strong>connects related objects</strong> — architecture / service-graph links, event and schema facts —
    and <strong>increases robustness</strong>, so the context isn’t just present but connected to everything it depends on.</>,
  features: [
    ['✦', 'Add metadata', 'Attach relevant external context objects, metadata and event / schema facts.'],
    ['◫', 'Connect objects', 'Link architecture and service-graph relationships — the connective context retrieval misses.'],
    ['⊛', 'Increase robustness', 'A richer, connected object survives change better than an isolated quote.'],
  ],
  facets: ['Metadata', 'Relationships', 'Service-graph', 'Schema', 'External'],
  standards: [
    ['Schema.org / JSON-LD', 'a shared vocabulary for the metadata each method attaches'],
    ['Service-graph / OpenTelemetry', 'architecture + dependency links from real telemetry'],
    ['Sigstore', 'signed method + enrichment records you can verify'],
    ['in-toto attestation', 'what was added, from which source, when'],
    ['CycloneDX AI-BOM', 'each method carries a bill of materials'],
    ['SemVer + cards', 'versioned method cards with a changelog'],
  ],
  installCmd: (e) => 'oenr apply ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → enriches the object with connected metadata + relationships',
  entries: [
    { id: 'metadata-tagger', name: 'Metadata Tagger', by: '@enrich-open', facet: 'Metadata', score: '4.7', installs: '4.0k', ver: '2.0.0', desc: 'Attaches a shared-vocabulary metadata layer (JSON-LD) to each object — type, owner, freshness, sensitivity.' },
    { id: 'service-graph-linker', name: 'Service-Graph Linker', by: '@baltor', facet: 'Service-graph', score: '4.8', installs: '3.7k', ver: '1.5.0', desc: 'Adds architecture / dependency links from real telemetry, so an object knows the services and schemas it touches.' },
    { id: 'relationship-builder', name: 'Relationship Builder', by: '@enrich-open', facet: 'Relationships', score: '4.6', installs: '2.9k', ver: '1.3.0', desc: 'Connects related objects into a graph — the missing connective context retrieval alone never assembles.' },
    { id: 'schema-fact-extractor', name: 'Schema-Fact Extractor', by: '@data-open', facet: 'Schema', score: '4.5', installs: '2.5k', ver: '1.2.0', desc: 'Pulls event and schema facts from source systems and attaches them as typed, queryable enrichments.' },
    { id: 'external-context', name: 'External-Context Fetcher', by: '@enrich-open', facet: 'External', score: '4.4', installs: '2.2k', ver: '1.1.0', desc: 'Adds relevant external context objects — scoped, cited, and governed — without polluting the core truth.' },
    { id: 'robustness-booster', name: 'Robustness Booster', by: '@baltor', facet: 'Relationships', score: '4.6', installs: '2.7k', ver: '1.0.0', desc: 'Measures and raises an object’s robustness by ensuring its dependencies and connective context are present.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
