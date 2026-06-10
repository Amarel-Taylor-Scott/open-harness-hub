/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenVerificationHub.io — open methods for the VERIFY stage of context governance.
// PRIVATE-FIRST candidate. The fifth and final Baltor engine stage, opened as a registry of
// methods: cited and provable — bind every claim to a source, prove it by hash, hold out the rest.

const E = PORTFOLIO.ENTITIES.openVerificationHub;
const App = makeHub({
  brand: { name: 'OpenVerificationHub', tld: '.io', glyph: '⊨', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'over-theme',
  noun: 'method', nounPlural: 'methods', indefinite: 'a method',
  heroTitle: <>Cited and <span className="tint">provable.</span></>,
  lede: 'OpenVerificationHub is the open registry of verification methods — the techniques that bind every claim to a source, check that it is provable by hash, and hold out what can’t be proven. The Verify stage of context governance, opened as methods. Discovery is not trust; a claim served without a citation is a liability.',
  ledeVariants: {
    A: 'OpenVerificationHub is the open registry of verification methods — the techniques that bind every claim to a source, check that it is provable by hash, and hold out what can’t be proven. The Verify stage of context governance, opened as methods. Discovery is not trust; a claim served without a citation is a liability.',
    B: 'A claim without a citation is a liability. Verification methods that bind each claim to a source, prove it by hash, and hold out the unprovable.',
    C: 'Every served claim, cited and provable. Open methods for citation binding, provability checks, and held-out survival.',
  },
  howTitle: 'Nothing served that isn’t cited and provable.',
  howBody: <>Pull a <strong>verification method</strong> and run it over a context pack at serve time. It <strong>binds every
    claim</strong> to a verifiable source handle, <strong>checks the claim is provable</strong> by hash, and <strong>holds out
    the unprovable</strong> — contradicted or unsupported claims never reach an agent. Pairs with OpenReceiptHub for the proof.</>,
  features: [
    ['⊨', 'Bind every claim', 'Attach a verifiable source handle to each claim — nothing served uncited.'],
    ['✓', 'Check provability', 'Verify the claim actually follows from its cited source, by hash.'],
    ['⛉', 'Hold out the unprovable', 'Quarantine contradicted or unsupported claims before they reach an agent.'],
  ],
  facets: ['Citation', 'Provability', 'Held-out', 'Contradiction', 'Audit'],
  standards: [
    ['Citation binding', 'every served claim carries a verifiable source handle'],
    ['Hash provenance (Rekor)', 'prove a claim by the hash of its cited source'],
    ['Sigstore', 'signed method + verification records you can verify'],
    ['in-toto attestation', 'what was verified, against which source, when'],
    ['CycloneDX AI-BOM', 'each method carries a bill of materials'],
    ['SemVer + cards', 'versioned method cards with a changelog'],
  ],
  installCmd: (e) => 'over apply ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → cites + verifies each claim; holds out the unprovable',
  entries: [
    { id: 'citation-binder', name: 'Citation Binder', by: '@baltor', facet: 'Citation', score: '4.9', installs: '5.4k', ver: '2.0.0', desc: 'Attaches a verifiable source handle to every claim, so nothing is served uncited.' },
    { id: 'claim-verifier', name: 'Claim Verifier', by: '@verify-open', facet: 'Provability', score: '4.8', installs: '4.1k', ver: '1.5.0', desc: 'Checks that a claim actually follows from its cited source — provable by hash, not asserted.' },
    { id: 'held-out-guard', name: 'Held-Out Guard', by: '@baltor', facet: 'Held-out', score: '4.7', installs: '3.3k', ver: '1.4.0', desc: 'Quarantines contradicted or unsupported claims at serve time; a held-out fact never leaks through.' },
    { id: 'contradiction-at-serve', name: 'Contradiction-at-Serve', by: '@verify-open', facet: 'Contradiction', score: '4.6', installs: '2.7k', ver: '1.2.0', desc: 'Last-mile check that nothing in the served pack conflicts with a known held-out or contradicted fact.' },
    { id: 'provenance-prover', name: 'Provenance Prover', by: '@baltor', facet: 'Audit', score: '4.8', installs: '3.0k', ver: '1.3.0', desc: 'Emits a hash-verifiable proof per served claim — the evidence an examiner can check without trusting you.' },
    { id: 'citation-coverage', name: 'Citation Coverage', by: '@verify-open', facet: 'Citation', score: '4.5', installs: '2.2k', ver: '1.1.0', desc: 'Measures the share of served claims that are both cited and provable — coverage you can gate a release on.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
