/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenRoutingHub.io — open ABSTRACTS for model-routing POLICY.
// PRIVATE-FIRST candidate (owner-proposed 2026-06-09). The open registry of the cards Teleon's
// inference gateway consumes: preference specs, provider-selection graphs, lane policies, fallback
// chains, and the receipt of which model actually served. Policy, not endpoints; cards, not a runtime.

const E = PORTFOLIO.ENTITIES.openRoutingHub;
const App = makeHub({
  brand: { name: 'OpenRoutingHub', tld: '.io', glyph: '⇉', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'omr-theme',
  noun: 'policy', nounPlural: 'policies', indefinite: 'a policy',
  heroTitle: <>Choose the model. <span className="tint">Prove the choice.</span></>,
  lede: 'OpenRoutingHub is the open registry of model-routing policy — preference cards, numeric provider-selection graphs, lane policies (dev · agent · interactive · batch · self-host), governed fallback chains, and the receipt of which model actually served. It catalogs HOW to choose and fall back among models, not WHERE they live (that is OpenEndpointHub). Discovery is not trust; a route without a receipt is a guess.',
  ledeVariants: {
    A: 'OpenRoutingHub is the open registry of model-routing policy — preference cards, provider-selection graphs, lane policies, fallback chains, and the receipt of which model actually served. Policy, not endpoints; cards, not a runtime. Discovery is not trust.',
    B: 'A route without a receipt is a guess. Open policies for declaring model preferences and resolving them by class, cost and jurisdiction — with a record of what actually ran.',
    C: 'Routing policy you can read, version and prove. Preference specs, selection graphs, and the five lanes — dev · agent · interactive · batch · self-host.',
  },
  howTitle: 'A route is a decision. Make it legible and provable.',
  howBody: <>Pull a <strong>routing policy</strong> and resolve a request against it: it reads the object's
    <strong> portable preferences</strong>, selects a model by <strong>class not name</strong> through a numeric
    provider-selection graph, applies a <strong>governed fallback chain</strong>, and emits a
    <strong> receipt of the model that actually served</strong>. Teleon's inference gateway is the runtime that
    consumes these cards; this hub is where the cards live. Pairs with OpenEndpointHub (the endpoints) and
    OpenReceiptHub (the proof).</>,
  features: [
    ['⇉', 'Declare preferences', 'A portable preference card — class, cost ceiling, jurisdiction, latency — that any router can read.'],
    ['⊜', 'Select by class', 'A numeric provider-selection graph picks a model by class, never by hardcoded name — swap a model without touching code.'],
    ['⤳', 'Fall back, governed', 'Ordered fallback chains with a recorded reason for each hop; nothing degrades silently.'],
  ],
  facets: ['Preference', 'Selection', 'Lane', 'Fallback', 'Receipt'],
  standards: [
    ['Open Inference Preference Spec', 'a portable card declaring how an object wants to be routed'],
    ['Numeric provider graph', 'select by class/weight/code — never by display name'],
    ['Five-lane economics', 'dev · agent · interactive · batch · self-host, by workload class'],
    ['ModelInvocationReceipt', 'the model that actually served, with the fallback trail'],
    ['SemVer + cards', 'versioned policy cards with a changelog'],
    ['CycloneDX AI-BOM', 'each policy carries a bill of materials'],
  ],
  installCmd: (e) => 'omr apply ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → resolves by class, falls back governed, emits a receipt',
  entries: [
    { id: 'preference-card', name: 'Portable Preference Card', by: '@teleon', facet: 'Preference', score: '4.9', installs: '4.7k', ver: '2.0.0', desc: 'The OIPS card: declare class, cost ceiling, jurisdiction and latency once; any router resolves it.' },
    { id: 'class-selection-graph', name: 'Class Selection Graph', by: '@teleon', facet: 'Selection', score: '4.8', installs: '3.9k', ver: '1.6.0', desc: 'Numeric provider-selection graph — picks a model by class and weight, never by hardcoded name.' },
    { id: 'five-lane-router', name: 'Five-Lane Router', by: '@aidr', facet: 'Lane', score: '4.7', installs: '3.1k', ver: '1.4.0', desc: 'Routes by workload class to dev · agent · interactive · batch · self-host; batch lane halves the verification-rail bill.' },
    { id: 'governed-fallback', name: 'Governed Fallback Chain', by: '@teleon', facet: 'Fallback', score: '4.8', installs: '2.8k', ver: '1.3.0', desc: 'Ordered fallback with a recorded reason per hop; a degraded route is never silent.' },
    { id: 'route-receipt', name: 'Route Receipt', by: '@aidr', facet: 'Receipt', score: '4.9', installs: '3.4k', ver: '1.5.0', desc: 'Emits the ModelInvocationReceipt — the model that actually served plus the full fallback trail.' },
    { id: 'jurisdiction-guard', name: 'Jurisdiction Guard', by: '@baltor', facet: 'Selection', score: '4.6', installs: '2.0k', ver: '1.1.0', desc: 'Refuses a route that would send a data class to an ineligible provider/jurisdiction — fail closed.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
