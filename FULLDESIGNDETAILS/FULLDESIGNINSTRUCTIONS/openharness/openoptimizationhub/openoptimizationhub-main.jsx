/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenOptimizationHub.io — open methods for the OPTIMIZE stage of context governance.
// PRIVATE-FIRST candidate. Baltor's engine stage, opened as a registry of methods:
// pack shaping — distill context into structured objects, rank it, and fit the task budget.

const E = PORTFOLIO.ENTITIES.openOptimizationHub;
const App = makeHub({
  brand: { name: 'OpenOptimizationHub', tld: '.io', glyph: '⊿', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'oopt-theme',
  noun: 'method', nounPlural: 'methods', indefinite: 'a method',
  heroTitle: <>Pack <span className="tint">shaping.</span></>,
  lede: 'OpenOptimizationHub is the open registry of optimization methods — the techniques that summarize and distill, convert unstructured context into structured objects, rank relevance, and fit the result to the task budget. The Optimize stage of context governance, opened as methods. Reduction is not success unless fidelity survives.',
  ledeVariants: {
    A: 'OpenOptimizationHub is the open registry of optimization methods — the techniques that summarize and distill, convert unstructured context into structured objects, rank relevance, and fit the result to the task budget. The Optimize stage of context governance, opened as methods. Reduction is not success unless fidelity survives.',
    B: 'Fit the context to the budget without losing the answer. Methods that summarize, structure and rank — reduction with fidelity intact.',
    C: 'Shape the pack to the task. Open methods that distill unstructured context into ranked, structured objects that fit the budget.',
  },
  howTitle: 'Fit the context to the task budget.',
  howBody: <>Pull an <strong>optimization method</strong> and run it over a context pack. It <strong>summarizes and
    distills</strong>, <strong>converts unstructured text into structured objects</strong>, and <strong>ranks relevance</strong>,
    fitting the result to the task budget — without dropping the answer-critical facts (pairs with OpenCompressionHub).</>,
  features: [
    ['≡', 'Summarize & distill', 'Compress to the essential, keeping the answer-critical facts and their source handles.'],
    ['⊞', 'Structure', 'Convert unstructured context into typed, queryable objects.'],
    ['↧', 'Rank relevance', 'Order by task relevance and fit the result to the budget — reduction with fidelity intact.'],
  ],
  facets: ['Summarize', 'Structure', 'Ranking', 'Budget', 'Fidelity'],
  standards: [
    ['Token budgeting', 'fit the pack to a declared budget, measured not guessed'],
    ['Extractive + structured distillation', 'reduce to structured objects, not lossy prose'],
    ['Sigstore', 'signed method + result records you can verify'],
    ['in-toto attestation', 'what was shaped, from which pack, when'],
    ['CycloneDX AI-BOM', 'each method carries a bill of materials'],
    ['SemVer + cards', 'versioned method cards with a changelog'],
  ],
  installCmd: (e) => 'oopt apply ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → shapes the pack to the task budget; emits a fidelity report',
  entries: [
    { id: 'object-distiller', name: 'Object Distiller', by: '@optimize-open', facet: 'Structure', score: '4.8', installs: '4.2k', ver: '2.0.0', desc: 'Converts unstructured context into typed, queryable objects — distillation that keeps structure, not lossy prose.' },
    { id: 'relevance-ranker', name: 'Relevance Ranker', by: '@baltor', facet: 'Ranking', score: '4.7', installs: '3.5k', ver: '1.4.0', desc: 'Ranks context by task relevance so the budget is spent on what the task actually needs.' },
    { id: 'budget-fitter', name: 'Budget Fitter', by: '@optimize-open', facet: 'Budget', score: '4.6', installs: '3.1k', ver: '1.3.0', desc: 'Fits a pack to a declared token budget, trimming lowest-value content first — measured, not guessed.' },
    { id: 'cited-summarizer', name: 'Cited Summarizer', by: '@baltor', facet: 'Summarize', score: '4.7', installs: '3.8k', ver: '1.5.0', desc: 'Summarizes to the essential while keeping every claim’s citation and source handle intact.' },
    { id: 'fidelity-guard', name: 'Fidelity Guard', by: '@optimize-open', facet: 'Fidelity', score: '4.9', installs: '2.9k', ver: '1.2.0', desc: 'Verifies that answer-critical facts survived reduction — reduction is not success unless fidelity holds.' },
    { id: 'pack-shaper', name: 'Pack Shaper', by: '@baltor', facet: 'Budget', score: '4.5', installs: '2.4k', ver: '1.0.0', desc: 'End-to-end: distill → structure → rank → fit, producing a task-shaped pack with a fidelity report.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
