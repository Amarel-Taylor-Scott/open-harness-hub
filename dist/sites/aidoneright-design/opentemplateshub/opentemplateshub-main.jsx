/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenTemplatesHub.io — reusable template families. Built on the shared hub module.
// PRIVATE-FIRST candidate: opens publicly when a it enters private preview.
// Drawn from the Shared Template Registry. "Templates generate starting shapes;
// harnesses prove the generated outputs work." Distinct from OpenHarnessHub
// (a harness PROVES an output) — a template is the SHAPE you instantiate.

const E = PORTFOLIO.ENTITIES.openTemplatesHub;
const App = makeHub({
  brand: { name: 'OpenTemplatesHub', tld: '.io', glyph: '⊞', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'otpl-theme',
  noun: 'template', nounPlural: 'templates', indefinite: 'a template',
  heroTitle: <>Start from a <span className="tint">proven shape.</span></>,
  lede: 'A template is a reusable, versioned starting shape — schema, runtime, resource, API-UI, inference or PurposeTask. Instantiate one to scaffold a governed artifact in seconds; a harness then proves the generated output actually works. Internal to the group today, open when the lane heats up.',
  ledeVariants: {
    A: 'A template is a reusable, versioned starting shape — schema, runtime, resource, API-UI, inference or PurposeTask. Instantiate one to scaffold a governed artifact in seconds; a harness then proves the generated output actually works. Internal to the group today, open when the lane heats up.',
    B: 'Six template families — schema, runtime, resource, API-UI, inference, PurposeTask. Instantiate a starting shape; let a harness prove the output.',
    C: 'Templates generate the starting shape; harnesses prove it works. Versioned, pinned families you instantiate in seconds.',
  },
  howTitle: 'Instantiate a shape, then prove it.',
  howBody: <>Pick a <strong>template family</strong> — schema, runtime, resource, API-UI, inference or PurposeTask — and
    instantiate it into a starting artifact. A template only gives you the <em>shape</em>; hand the generated output to a
    <strong> harness</strong> from OpenHarnessHub to prove it passes its eval. Shape here, proof there.</>,
  features: [
    ['⊞', 'Six template families', 'Schema · runtime · resource · API-UI · inference · PurposeTask — the shapes every governed artifact starts from.'],
    ['◷', 'Versioned & pinned', 'Each template is semver-pinned with a changelog; instantiate a specific version, reproducibly.'],
    ['✓', 'Templates generate; harnesses prove', 'A template gives you a starting shape — a harness proves the generated output actually passes its eval.'],
  ],
  facets: ['Schema', 'Runtime', 'Resource', 'API-UI', 'Inference', 'PurposeTask'],
  standards: [
    ['JSON Schema', 'every schema template validates against a published draft'],
    ['OpenAPI', 'API-UI and resource templates carry a typed interface contract'],
    ['Scaffold lineage', 'the cookiecutter/scaffold tradition, governed and signed'],
    ['Sigstore', 'signed templates + instantiation receipts you can verify'],
    ['in-toto attestation', 'what was instantiated, from which template version, when'],
    ['SemVer + cards', 'versioned template cards with a changelog'],
  ],
  trust: (e) => [
    ['Signature', 'cosign ✓', true],
    ['Provenance', 'SLSA L3', true],
    ['Instantiation receipt', 'in-toto ✓', true],
    ['Template is', 'a shape, not a proof', false],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  installCmd: (e) => 'otpl new ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → instantiates a starting shape; hand the output to a harness',
  entries: [
    { id: 'json-record-schema', name: 'JSON Record Schema', by: '@schema-open', facet: 'Schema', score: '4.8', installs: '5.2k', ver: '2.1.0', desc: 'A typed record-schema family with validation, examples and a published JSON Schema — the shape most extraction and tool outputs start from.' },
    { id: 'durable-worker', name: 'Durable Worker Runtime', by: '@teleon', facet: 'Runtime', score: '4.7', installs: '3.1k', ver: '1.4.0', desc: 'A bounded, durable worker runtime scaffold that emits run receipts — the starting shape for fleet/execution workers.' },
    { id: 'governed-connector', name: 'Governed Resource Connector', by: '@baltor', facet: 'Resource', score: '4.6', installs: '2.4k', ver: '1.2.0', desc: 'A source/connector template with declared least-privilege scopes and a verification hook — instantiate a governed resource in minutes.' },
    { id: 'console-page', name: 'Console Page (kit)', by: '@design-open', facet: 'API-UI', score: '4.9', installs: '6.0k', ver: '3.0.0', desc: 'An account/console page scaffold on the shared site kit — topbar, nav, primitives wired — so a new surface starts on-brand.' },
    { id: 'inference-route', name: 'Governed Inference Route', by: '@gateway-open', facet: 'Inference', score: '4.5', installs: '2.0k', ver: '1.1.0', desc: 'A provider-routed inference-call shape that emits a ModelInvocationReceipt and respects endpoint eligibility — the starting shape for any LLM call.' },
    { id: 'purposetask-contract', name: 'PurposeTask Contract', by: '@teleon', facet: 'PurposeTask', score: '4.7', installs: '1.8k', ver: '1.0.0', desc: 'A Teleon CapabilityTask contract starting shape: purpose, inputs, eval gate and boundary — instantiate, then let a candidate fill it.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
