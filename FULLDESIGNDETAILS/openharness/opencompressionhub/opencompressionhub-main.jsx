/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenCompressionHub.io — compression & context-budget intelligence. Shared hub module.
// Proposed .io (domain/trademark unverified). Token reduction is not success unless fidelity survives.

const E = PORTFOLIO.ENTITIES.openCompressionHub;
const App = makeHub({
  brand: { name: 'OpenCompressionHub', tld: '.io', glyph: '⊟', accent: E.accent },
  kind: E.kind,
  themeKey: 'ocmp-theme',
  noun: 'compression candidate', nounPlural: 'compression candidates', indefinite: 'a compression candidate',
  heroTitle: <>Token efficiency, <span className="tint">without losing the truth</span>.</>,
  standards: [
    ['LLMLingua', 'Microsoft’s prompt-compression family as candidate strategies'],
    ['Fidelity eval packs', 'source handles + held-out warnings must survive compression'],
    ['Sigstore', 'signed candidates + benchmark results'],
    ['SLSA + in-toto', 'provenance for how each candidate was produced'],
    ['OpenSSF Scorecard', 'risk scoring — reduction is not success if fidelity drops'],
    ['SemVer', 'versioned candidates with a changelog'],
  ],
  lede: 'Compression strategies and context budgets, benchmarked on fidelity — source handles and held-out warnings must survive. Token reduction is not success unless fidelity survives.',
  ledeVariants: {
    A: 'Compression strategies and context budgets, benchmarked on fidelity — source handles and held-out warnings must survive. Token reduction is not success unless fidelity survives.',
    B: 'Cut tokens, keep the proof. Compression candidates scored on fidelity — citations and held-out warnings must survive the squeeze.',
    C: 'A 90% token cut means nothing if the answer changed. Benchmark compression on fidelity, not just size.',
  },
  howTitle: 'Compress context, keep the receipts.',
  howBody: <>Browse <strong>compression candidates</strong> the ecosystem has published, see their token savings <em>and</em>
    their fidelity score, and adopt what holds up. Source handles, citations and held-out warnings must survive compression.</>,
  features: [
    ['⊟', 'Fidelity-benchmarked', 'Every candidate reports token savings against a measured fidelity score — both, never just size.'],
    ['◳', 'Handles survive', 'Source handles, citations and held-out warnings must round-trip — a candidate that drops them fails.'],
    ['◷', 'Context budgets', 'Fit a corpus to a task budget with a strategy whose fidelity you can verify.'],
  ],
  facets: ['Extractive', 'Abstractive', 'Structural', 'Hybrid'],
  installCmd: (e) => 'ocmp bench ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → reports tokens saved + fidelity (both required)',
  entries: [
    { id: 'claim-distill', name: 'Claim Distillation', by: '@baltor-open', facet: 'Extractive', score: '4.9', installs: '4.2k', ver: '1.3.0', desc: 'Distil to claim-level with citation anchors. 0.06× tokens · fidelity 0.97 · handles preserved.' },
    { id: 'schema-normalize', name: 'Schema Normalize', by: '@ada', facet: 'Structural', score: '4.7', installs: '3.1k', ver: '1.1.0', desc: 'Collapse redundant records to a clean schema. 0.4× tokens · fidelity 0.99 · lossless on keys.' },
    { id: 'rank-prune', name: 'Relevance Prune', by: '@search-open', facet: 'Hybrid', score: '4.5', installs: '2.6k', ver: '1.0.0', desc: 'Rank and drop low-relevance spans to a budget. 0.25× tokens · fidelity 0.93.' },
    { id: 'abstractive-sum', name: 'Abstractive Summary', by: '@lab-unverified', facet: 'Abstractive', score: '3.6', installs: '900', ver: '0.5.0', desc: 'LLM summary to a target length. 0.1× tokens · fidelity 0.71 — drops held-out warnings, fails the gate.' },
    { id: 'budget-fit', name: 'Budget Fit', by: '@baltor-open', facet: 'Hybrid', score: '4.6', installs: '3.8k', ver: '1.2.0', desc: 'Fit a corpus to a token budget with a verifiable fidelity floor. 0.18× tokens · fidelity 0.95.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
