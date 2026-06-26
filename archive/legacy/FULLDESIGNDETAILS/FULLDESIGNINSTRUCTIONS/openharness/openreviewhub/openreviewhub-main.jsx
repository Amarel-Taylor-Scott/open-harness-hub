/* global React, ReactDOM, PORTFOLIO, makeHub, ORHReviewReport */
// OpenReviewHub.io — review intelligence layer. Built on the shared hub module.
// Reviews papers and repos (and models, agents, datasets) for capability,
// verifiability and reproducibility. The family's thesis, applied to artifacts:
// discovery is not trust — a claim is not a capability until it reproduces. Sits
// alongside OpenBenchmarkHub (a result is evidence, a review is the scrutiny).

const E = PORTFOLIO.ENTITIES.openReviewHub;
const App = makeHub({
  brand: { name: 'OpenReviewHub', tld: '.io', glyph: '⊙', accent: E.accent },
  kind: E.kind,
  themeKey: 'orh-theme',
  noun: 'review', nounPlural: 'reviews', indefinite: 'a review',
  heroTitle: <>Does it do <span className="tint">what it claims?</span></>,
  lede: 'OpenReviewHub reviews papers and repos — and models, agents and datasets — for capability, verifiability and reproducibility. Each review maps every claim to its evidence and a re-run verdict, scoped to exactly what was tested. Discovery is not trust; a claim is not a capability until it reproduces.',
  ledeVariants: {
    A: 'OpenReviewHub reviews papers and repos — and models, agents and datasets — for capability, verifiability and reproducibility. Each review maps every claim to its evidence and a re-run verdict, scoped to exactly what was tested. Discovery is not trust; a claim is not a capability until it reproduces.',
    B: 'A README is not a result. We review papers and repos for capability, verifiability and reproducibility — claim by claim, re-run, signed.',
    C: 'Read the review before you build on the claim. Capability, verifiability and reproducibility — re-run on the released materials, with a verdict per claim.',
  },
  howTitle: 'Review papers and repos against what they claim.',
  howBody: <>Pull a <strong>review</strong> of a paper, repo, model, agent or dataset — every headline claim mapped to the
    evidence for it and a verdict from actually re-running it. Or publish your own; each review declares exactly what was
    tested, and what wasn’t. Reproducibility you can audit, not a star rating.</>,
  features: [
    ['⊙', 'Claim → evidence → verdict', 'Every review maps each claim to the evidence for it and a re-run check — not vibes, not a star.'],
    ['↻', 'Reproducibility, actually run', 'We rebuild the repo and re-derive the result. A reproduced badge means it reproduced — on the released materials.'],
    ['⛨', 'Signed, scoped verdicts', 'Each review is signed and versioned, scoped to exactly what was tested — and explicit about what wasn’t.'],
  ],
  facets: ['Papers', 'Repos', 'Models', 'Agents', 'Datasets'],
  standards: [
    ['ML Reproducibility Checklist', 'the NeurIPS/MLRC tradition this review rubric builds on'],
    ['ACM Artifact Review badges', 'Artifacts Available · Evaluated · Reproduced, made concrete'],
    ['Sigstore', 'signed review records — provenance you can verify by hash'],
    ['in-toto attestation', 'what was reviewed, on which commit, when'],
    ['CycloneDX AI-BOM', 'each reviewed artifact carries a bill of materials'],
    ['SemVer + review cards', 'versioned reviews with a changelog as claims evolve'],
  ],
  trust: (e) => [
    ['Signature', 'cosign ✓', true],
    ['Repro attestation', 'in-toto ✓', true],
    ['Reproduced', 're-run ✓', true],
    ['Scope', 'tested ≠ everything', false],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  installCmd: (e) => 'orv pull ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → a signed review record: claim → evidence → verdict',
  // the review report on every entry-detail page (generic entryExtra hook)
  entryExtra: (e) => <ORHReviewReport e={e} />,
  // each entry = a signed review of a real artifact, scored on capability / verifiability / reproducibility
  entries: [
    { id: 'cov-claims', name: 'Review · "Chain-of-Verification" claims', by: '@repro-commons', facet: 'Papers', score: '4.7', installs: '3.4k', ver: '1.2.0', desc: 'Re-runs the released prompts and seeds: which reported gains actually reproduce, and which table doesn’t.' },
    { id: 'agent-runtime-repo', name: 'Review · agent-runtime repo', by: '@dev-open', facet: 'Repos', score: '4.8', installs: '5.1k', ver: '1.4.0', desc: 'Clean-clone build, quickstart timed to first run, and the project’s own tests — does the demo actually work?' },
    { id: 'ow-7b-card', name: 'Review · open-weights 7B capability card', by: '@eval-open', facet: 'Models', score: '4.6', installs: '4.0k', ver: '2.0.0', desc: 'Re-runs the published lm-eval configs on the released weights; flags the scores that drift beyond noise.' },
    { id: 'web-research-agent', name: 'Review · web-research agent', by: '@agents-open', facet: 'Agents', score: '4.5', installs: '2.7k', ver: '1.3.0', desc: 'Sandboxed end-to-end run of the task suite — completion, tool-scope adherence, and whether it cites its claims.' },
    { id: 'it-set-provenance', name: 'Review · instruction-tuning set provenance', by: '@data-open', facet: 'Datasets', score: '4.4', installs: '1.9k', ver: '1.1.0', desc: 'Audits the licensing, dedup and contamination claims by re-running the pipeline and sampling rows. Concerns found.' },
    { id: 'rag-reference', name: 'Review · RAG reference implementation', by: '@retrieval-open', facet: 'Repos', score: '4.7', installs: '3.8k', ver: '1.5.0', desc: 'Rebuilds the index from the pinned corpus and re-derives the reported retrieval metrics from the repo.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
