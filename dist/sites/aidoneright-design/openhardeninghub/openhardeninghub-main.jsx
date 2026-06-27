/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenHardeningHub.io — open methods for the HARDEN stage of context governance.
// PRIVATE-FIRST candidate. Baltor's engine stage, opened as a registry of methods:
// robust object hardening — turn brittle text into knowledge objects that refresh over time.

const E = PORTFOLIO.ENTITIES.openHardeningHub;
const App = makeHub({
  brand: { name: 'OpenHardeningHub', tld: '.io', glyph: '⊛', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'ohard-theme',
  noun: 'method', nounPlural: 'methods', indefinite: 'a method',
  heroTitle: <>Robust object <span className="tint">hardening.</span></>,
  lede: 'OpenHardeningHub is the open registry of hardening methods — the techniques that find facts likely to change in source systems and replace brittle text with robust knowledge objects that can update over time. The Harden stage of context governance, opened as methods. Stale context is a silent outage; harden it before an agent acts.',
  ledeVariants: {
    A: 'OpenHardeningHub is the open registry of hardening methods — the techniques that find facts likely to change in source systems and replace brittle text with robust knowledge objects that can update over time. The Harden stage of context governance, opened as methods. Stale context is a silent outage; harden it before an agent acts.',
    B: 'Brittle text goes stale silently. Hardening methods detect fragile values and turn them into knowledge objects that refresh over time.',
    C: 'Find what will change, harden it. Open methods that replace brittle quotes with robust, self-updating knowledge objects.',
  },
  howTitle: 'Replace brittle text with objects that update.',
  howBody: <>Pull a <strong>hardening method</strong> and run it over your context. It <strong>detects fragile values</strong>
    — the facts likely to change in a source system — <strong>creates knowledge objects</strong> in their place, and lets
    them <strong>refresh over time</strong>, so a number that moves doesn’t silently rot the answer.</>,
  features: [
    ['⚠', 'Detect fragile values', 'Find the facts most likely to change in source systems — dates, rates, statuses, thresholds.'],
    ['⊛', 'Create knowledge objects', 'Replace brittle inline text with a robust object that carries its source handle.'],
    ['↻', 'Refresh over time', 'The object updates when its source moves — no stale quote silently rotting the answer.'],
  ],
  facets: ['Fragility', 'Objects', 'Refresh', 'Source-handles', 'Freshness'],
  standards: [
    ['Source handles', 'every hardened object keeps a verifiable pointer to its origin'],
    ['Change-data-capture', 'detect when a source value moves, and refresh the object'],
    ['Sigstore', 'signed method + object records you can verify'],
    ['in-toto attestation', 'what was hardened, from which source, when'],
    ['CycloneDX AI-BOM', 'each method carries a bill of materials'],
    ['SemVer + cards', 'versioned method cards with a changelog'],
  ],
  installCmd: (e) => 'ohard apply ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → hardens fragile values into refreshing knowledge objects',
  entries: [
    { id: 'fragility-detector', name: 'Fragility Detector', by: '@baltor', facet: 'Fragility', score: '4.9', installs: '4.8k', ver: '2.0.0', desc: 'Scores each fact by how likely it is to change in its source system — dates, rates, statuses — flagging the brittle ones.' },
    { id: 'object-extractor', name: 'Knowledge-Object Extractor', by: '@harden-open', facet: 'Objects', score: '4.7', installs: '3.6k', ver: '1.4.0', desc: 'Replaces brittle inline text with a typed knowledge object that carries its source handle and refresh policy.' },
    { id: 'refresh-policy', name: 'Refresh Policy', by: '@baltor', facet: 'Refresh', score: '4.6', installs: '2.9k', ver: '1.3.0', desc: 'Declares when and how a hardened object re-checks its source — interval, change-trigger, or on-read.' },
    { id: 'source-handle-binder', name: 'Source-Handle Binder', by: '@harden-open', facet: 'Source-handles', score: '4.8', installs: '3.3k', ver: '1.5.0', desc: 'Binds every object to a verifiable source pointer, so a hardened value can always be re-derived and proven.' },
    { id: 'staleness-monitor', name: 'Staleness Monitor', by: '@baltor', facet: 'Freshness', score: '4.7', installs: '3.0k', ver: '1.2.0', desc: 'Watches hardened objects for drift and raises a refresh when the underlying source moves — no silent outage.' },
    { id: 'volatility-ranker', name: 'Volatility Ranker', by: '@harden-open', facet: 'Fragility', score: '4.4', installs: '2.1k', ver: '1.0.0', desc: 'Ranks a corpus by how volatile its facts are, so hardening effort goes where the breakage risk is highest.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
