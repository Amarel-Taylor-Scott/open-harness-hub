/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenStateHub.io — governed, durable agent state. Built on the shared hub module.
// PRIVATE-FIRST candidate: opens publicly when a it enters private preview.
// Distinct from OpenContextHub (governed TRUTH packs an agent reads) — this is the
// durable WORKING STATE an agent writes: memory, blackboard, graph. Drawn from the
// persistent agent-state spine (blackboard · mem0 / letta / graphiti class).

const E = PORTFOLIO.ENTITIES.openStateHub;
const App = makeHub({
  brand: { name: 'OpenStateHub', tld: '.io', glyph: '◧', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'ost-theme',
  noun: 'store', nounPlural: 'stores', indefinite: 'a store',
  heroTitle: <>State an agent <span className="tint">can trust.</span></>,
  lede: 'A store is durable working state for agents — memory, a blackboard, a graph — versioned with provenance and access scopes. Distinct from context truth packs: this is the state an agent writes, kept auditable and reproducible instead of a black box. Pin a snapshot, fork it for a candidate, replay it.',
  ledeVariants: {
    A: 'A store is durable working state for agents — memory, a blackboard, a graph — versioned with provenance and access scopes. Distinct from context truth packs: this is the state an agent writes, kept auditable and reproducible instead of a black box. Pin a snapshot, fork it for a candidate, replay it.',
    B: 'Agent memory shouldn’t be a black box. Durable, governed working state — memory, blackboard, graph — versioned, scoped and replayable.',
    C: 'What did the agent remember, and why? Governed state stores make an agent’s working memory auditable, forkable and reproducible.',
  },
  howTitle: 'Working memory you can audit.',
  howBody: <>Mount a governed <strong>store</strong> — long-term memory, a shared blackboard, a knowledge graph or a vector
    index — and every read and write is <strong>scoped and provenance-stamped</strong>. Pin a snapshot to reproduce a run,
    fork a blackboard for a candidate, and audit exactly what an agent remembered. State is versioned, not mutable mush.</>,
  features: [
    ['◧', 'Durable working state', 'Memory, blackboard, graph or vector — the state agents read and write between steps, kept versioned.'],
    ['⛨', 'Governed & scoped', 'Every read/write is scoped and provenance-stamped; you can audit what an agent remembered and why.'],
    ['↻', 'Reproducible & forkable', 'Pin a snapshot and replay; fork a blackboard for a candidate run. State is versioned, not a black box.'],
  ],
  facets: ['Memory', 'Blackboard', 'Graph', 'KV', 'Vector'],
  standards: [
    ['Event sourcing / CRDT', 'durable, mergeable state with a replayable history'],
    ['Provenance on writes', 'every write carries who/what/when — auditable, not anonymous'],
    ['Sigstore', 'signed state snapshots you can verify by hash'],
    ['in-toto attestation', 'how a snapshot was produced, attested'],
    ['CycloneDX AI-BOM', 'each store carries a bill of materials'],
    ['SemVer + snapshots', 'versioned, pinnable snapshots with a changelog'],
  ],
  trust: (e) => [
    ['Signature', 'cosign ✓', true],
    ['Provenance on writes', 'in-toto ✓', true],
    ['Snapshot', 'pinned · replayable', true],
    ['State is', 'working, not truth', false],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  installCmd: (e) => 'ost attach ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → mounts a governed, versioned store; reads/writes are provenance-stamped',
  entries: [
    { id: 'agent-memory', name: 'Agent Memory Store', by: '@memory-open', facet: 'Memory', score: '4.8', installs: '6.7k', ver: '2.0.0', desc: 'Long-term agent memory with provenance per fact and scoped recall — a governed take on the mem0 / letta class. Audit what was remembered.' },
    { id: 'shared-blackboard', name: 'Shared Blackboard', by: '@swarm-open', facet: 'Blackboard', score: '4.7', installs: '4.1k', ver: '1.3.0', desc: 'A multi-agent blackboard with scoped lanes and fork/merge — the durable working surface a swarm coordinates on. Fork it for a candidate run.' },
    { id: 'knowledge-graph', name: 'Knowledge Graph Store', by: '@graph-open', facet: 'Graph', score: '4.6', installs: '3.4k', ver: '1.4.0', desc: 'A temporal knowledge graph (graphiti class) with versioned, provenance-stamped edges — agent state you can query and replay at a point in time.' },
    { id: 'durable-kv', name: 'Durable KV State', by: '@workflow-open', facet: 'KV', score: '4.5', installs: '3.0k', ver: '1.2.0', desc: 'Checkpointed key-value working state for long-running workflows: resume from a snapshot, replay deterministically, audit every write.' },
    { id: 'vector-memory', name: 'Vector Memory', by: '@retrieval-open', facet: 'Vector', score: '4.5', installs: '3.6k', ver: '1.5.0', desc: 'An embedding store with provenance and dedup on write — pairs with OpenContextHub truth packs; recall is scoped and auditable.' },
    { id: 'session-state', name: 'Session State', by: '@agent-open', facet: 'Memory', score: '4.4', installs: '2.6k', ver: '1.1.0', desc: 'Per-session working state with a retained, signed transcript — ephemeral for the agent, durable and auditable for you.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
