/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenSkillsHub.io — open skill graph. Built on the shared hub module.

const E = PORTFOLIO.ENTITIES.openSkillsHub;
const App = makeHub({
  brand: { name: 'OpenSkillsHub', tld: '.io', glyph: '◇', accent: E.accent },
  kind: E.kind,
  themeKey: 'osh-theme',
  noun: 'skill', nounPlural: 'skills', indefinite: 'a skill',
  heroTitle: <>The open graph of <span className="tint">skills</span> agents can compose.</>,
  lede: 'Find, compose and publish open agent skills — evaluated, versioned units of capability that snap together and run anywhere, including inside Teleon.',
  ledeVariants: {
    A: 'Find, compose and publish open agent skills — evaluated, versioned units of capability that snap together and run anywhere, including inside Teleon.',
    B: 'Stop rebuilding the same five skills. Compose evaluated, versioned units of capability that just work — and run anywhere.',
    C: 'Every skill scored against a shared eval pack before it ships — composable capability you can actually trust.',
  },
  howTitle: 'Composable skills, proven to work.',
  howBody: <>Browse <strong>skills</strong> the community has published, compose them into your agents, and rely on their
    eval scores. Or publish your own — every skill is tested against shared eval packs before it lists.</>,
  features: [
    ['◇', 'Composable units', 'Each skill is a small, typed unit of capability that snaps into any agent or harness.'],
    ['⟳', 'Graph of dependencies', 'Skills declare what they build on — compose with confidence across the graph.'],
    ['✓', 'Evaluated & ranked', 'Every skill carries an eval score from shared packs, so you pick what actually works.'],
  ],
  facets: ['Retrieval', 'Reasoning', 'Extraction', 'Code', 'Planning'],
  installCmd: (e) => 'osh add ' + e.id + '@' + (e.ver || '1.2.0') + '\n# → adds the skill (and its deps) to your agent',
  entries: [
    { id: 'cited-answer', name: 'Cited Answer', by: '@ada', facet: 'Retrieval', score: '4.9', installs: '9.1k', ver: '2.3.0', desc: 'Answer a query with an inline citation behind every claim.', deps: ['reranker@1.4', 'chunker@2.0'] },
    { id: 'query-decompose', name: 'Query Decomposer', by: '@search-wg', facet: 'Reasoning', score: '4.7', installs: '6.5k', ver: '1.8.1', desc: 'Break a complex question into answerable sub-queries.' },
    { id: 'table-extract', name: 'Table Extractor', by: '@docs-open', facet: 'Extraction', score: '4.8', installs: '5.9k', ver: '3.0.0', desc: 'Pull structured tables from PDFs and HTML with cell-level spans.' },
    { id: 'sql-synth', name: 'Schema-aware SQL', by: '@data-commons', facet: 'Code', score: '4.6', installs: '4.2k', ver: '1.5.0', desc: 'Generate SQL grounded in your schema, with a dry-run check.', deps: ['schema-introspect@1.1'] },
    { id: 'plan-then-act', name: 'Plan-then-Act', by: '@agents-open', facet: 'Planning', score: '4.5', installs: '3.7k', ver: '2.1.0', desc: 'Decompose a goal into steps, then execute with checkpoints.' },
    { id: 'rerank-mini', name: 'Reranker (mini)', by: '@ada', facet: 'Retrieval', score: '4.8', installs: '8.3k', ver: '1.4.0', desc: 'Fast instruction-following reranker for retrieved chunks.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
