/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenReconciliationHub.io — open methods for the RECONCILE stage of context governance.
// PRIVATE-FIRST candidate. Baltor's engine stage, opened as a registry of methods:
// cluster alignment — collapse conflicting sources into one aligned answer.

const E = PORTFOLIO.ENTITIES.openReconciliationHub;
const App = makeHub({
  brand: { name: 'OpenReconciliationHub', tld: '.io', glyph: '⇌', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'orec-theme',
  noun: 'method', nounPlural: 'methods', indefinite: 'a method',
  heroTitle: <>Cluster <span className="tint">alignment.</span></>,
  lede: 'OpenReconciliationHub is the open registry of reconciliation methods — the techniques that collapse conflicting sources into one aligned answer. Deduplicate related artifacts, map relationships, separate comments from decisions, and surface contradictions across tickets, docs, code and memory. The Reconcile stage of context governance, opened as methods.',
  ledeVariants: {
    A: 'OpenReconciliationHub is the open registry of reconciliation methods — the techniques that collapse conflicting sources into one aligned answer. Deduplicate related artifacts, map relationships, separate comments from decisions, and surface contradictions across tickets, docs, code and memory. The Reconcile stage of context governance, opened as methods.',
    B: 'Two sources disagree; which is true? Reconciliation methods that dedupe, link evidence, and surface contradictions across tickets, docs, code and memory.',
    C: 'Collapse conflicting sources into one answer. Open, versioned reconciliation methods — dedupe, relationship mapping, comment-vs-decision, conflict surfacing.',
  },
  howTitle: 'Collapse conflicting sources into one answer.',
  howBody: <>Pull a <strong>reconciliation method</strong> — near-dup clustering, cross-source linking, comment-vs-decision,
    contradiction detection — and run it over your artifacts. Each method <strong>dedupes</strong>, <strong>links the
    evidence</strong>, and <strong>surfaces conflicts</strong> across tickets, docs, code and memory, leaving one aligned cluster.</>,
  features: [
    ['⊜', 'Dedupe & cluster', 'Group related artifacts and collapse duplicates into one aligned cluster.'],
    ['◫', 'Link evidence', 'Map relationships and separate comments from decisions — what was said vs what was decided.'],
    ['⚠', 'Surface conflicts', 'Detect and surface contradictions across tickets, docs, code and memory before an agent acts.'],
  ],
  facets: ['Dedupe', 'Linking', 'Conflict', 'Clustering', 'Provenance'],
  standards: [
    ['Record linkage (Fellegi–Sunter)', 'the statistical basis for matching records across sources'],
    ['MinHash / LSH', 'scalable near-duplicate detection'],
    ['Sigstore', 'signed method + result records you can verify'],
    ['in-toto attestation', 'what was reconciled, from which sources, when'],
    ['CycloneDX AI-BOM', 'each method carries a bill of materials'],
    ['SemVer + cards', 'versioned method cards with a changelog'],
  ],
  installCmd: (e) => 'orec apply ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → runs the method; emits an aligned cluster + a conflict report',
  entries: [
    { id: 'near-dup-clustering', name: 'Near-Dup Clustering', by: '@reconcile-open', facet: 'Dedupe', score: '4.8', installs: '4.4k', ver: '2.0.0', desc: 'MinHash/LSH clustering that groups related artifacts and collapses near-duplicates into one aligned cluster.' },
    { id: 'comment-vs-decision', name: 'Comment-vs-Decision', by: '@reconcile-open', facet: 'Linking', score: '4.7', installs: '3.2k', ver: '1.3.0', desc: 'Classifies whether a statement is a passing comment or an actual decision — so the decision wins, not the loudest thread.' },
    { id: 'contradiction-detect', name: 'Contradiction Detection', by: '@baltor', facet: 'Conflict', score: '4.9', installs: '5.1k', ver: '1.6.0', desc: 'Flags claims that disagree across tickets, docs, code and memory, with the conflicting spans cited.' },
    { id: 'cross-source-linker', name: 'Cross-Source Linker', by: '@data-open', facet: 'Linking', score: '4.6', installs: '2.8k', ver: '1.2.0', desc: 'Maps relationships across sources — the same entity in a ticket, a doc, a commit and a memory — into one linked object.' },
    { id: 'authority-reconcile', name: 'Authority Reconciliation', by: '@baltor', facet: 'Conflict', score: '4.7', installs: '3.0k', ver: '1.4.0', desc: 'Resolves a conflict by source authority + recency, and records why the winning value won.' },
    { id: 'evidence-graph', name: 'Evidence Graph Builder', by: '@reconcile-open', facet: 'Clustering', score: '4.5', installs: '2.3k', ver: '1.1.0', desc: 'Builds an evidence graph per claim — every supporting and contradicting source, linked and weighted.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
