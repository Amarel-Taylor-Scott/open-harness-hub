/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenBenchmarkHub.io — benchmark intelligence layer. Shared hub module.
// Proposed .io (domain/trademark unverified). Benchmarks are EVIDENCE, not authority —
// a result cannot promote a candidate by itself (no benchmark gate in Teleon's promotion gates).

const E = PORTFOLIO.ENTITIES.openBenchmarkHub;
const App = makeHub({
  brand: { name: 'OpenBenchmarkHub', tld: '.io', glyph: '▦', accent: E.accent },
  kind: E.kind,
  themeKey: 'obm-theme',
  noun: 'benchmark', nounPlural: 'benchmarks', indefinite: 'a benchmark',
  heroTitle: <>Benchmarks as <span className="tint">evidence</span>, not authority.</>,
  standards: [
    ['lm-evaluation-harness', 'EleutherAI’s standard runner behind reproducible results'],
    ['Inspect (UK AISI)', 'evals authored and run as versioned artifacts'],
    ['Sigstore', 'signed result records — provenance you can verify'],
    ['in-toto attestation', 'a benchmark run attested: what ran, on what, when'],
    ['CycloneDX AI-BOM', 'each benchmarked model/system carries a bill of materials'],
    ['SemVer + cards', 'versioned benchmark cards with a changelog'],
  ],
  trust: (e, h) => [
    ['Signature', 'cosign ✓', true],
    ['Run attestation', 'in-toto ✓', true],
    ['Reproducible', 'lm-eval ✓', true],
    ['Result is', 'evidence, not authority', false],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  lede: 'Benchmark cards, metrics, result records and suitability reports — open and reproducible. A benchmark result is evidence; it cannot promote a candidate by itself.',
  ledeVariants: {
    A: 'Benchmark cards, metrics, result records and suitability reports — open and reproducible. A benchmark result is evidence; it cannot promote a candidate by itself.',
    B: 'A leaderboard is not a launch decision. Benchmarks here are reproducible evidence — promotion still needs a policy gate.',
    C: 'Reproducible benchmark cards with result records and suitability reports — evidence a reviewer can trust, never an auto-promote.',
  },
  howTitle: 'Reproducible benchmarks, honest about scope.',
  howBody: <>Browse <strong>benchmark cards</strong> with their metrics, fixtures and result records, and read the suitability
    report before you rely on a number. Publish your own — every benchmark declares what it does and does <em>not</em> measure.</>,
  features: [
    ['▦', 'Benchmark cards', 'Each benchmark declares its task, fixtures, metrics and known limits — no context-free score.'],
    ['◷', 'Result records', 'Every run is a signed, reproducible record tied to a fixture version and a model-invocation receipt.'],
    ['⛨', 'Evidence, not a gate', 'A result informs promotion; it never decides it. Teleon’s policy gate stays in charge.'],
  ],
  facets: ['Context', 'Retrieval', 'Reasoning', 'Safety', 'Efficiency'],
  installCmd: (e) => 'obm run ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → emits a signed result record (evidence, not a gate)',
  entries: [
    { id: 'baltor-cfpb-ctx', name: 'Baltor CFPB Context-Governance', by: '@baltor', facet: 'Context', score: '4.9', installs: '2.1k', ver: '1.0.0', desc: 'First-party: serve Reg E “10 business days”, hold out FAQ “30 days”, preserve receipts. Anchored to the real demo facts.' },
    { id: 'rag-faithfulness', name: 'RAG Faithfulness', by: '@eval-open', facet: 'Retrieval', score: '4.6', installs: '5.4k', ver: '2.0.0', desc: 'Measures whether answers are grounded in retrieved context — not whether retrieval was “relevant.”' },
    { id: 'held-out-survival', name: 'Held-Out Survival', by: '@baltor-open', facet: 'Safety', score: '4.7', installs: '1.8k', ver: '1.1.0', desc: 'Does a contradicted/allegation claim stay held out through the pipeline? Pass/fail per fixture.' },
    { id: 'compression-fidelity', name: 'Compression Fidelity', by: '@compression-open', facet: 'Efficiency', score: '4.5', installs: '2.3k', ver: '1.2.0', desc: 'Tokens saved vs fidelity retained — pairs with OpenCompressionHub candidates.' },
    { id: 'tool-call-accuracy', name: 'Tool-Call Accuracy', by: '@tools-open', facet: 'Reasoning', score: '4.4', installs: '3.0k', ver: '1.3.0', desc: 'Correct tool, correct arguments, correct scope — with a suitability report on what it omits.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
