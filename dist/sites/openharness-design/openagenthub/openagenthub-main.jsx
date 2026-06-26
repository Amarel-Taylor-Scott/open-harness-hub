/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenAgentHub.io — agent-runtime registry (bounded adapters + run receipts).
// PRIVATE-FIRST candidate: opens publicly when a it enters private preview.
// Drawn from the agent_runtime_catalog + teleon. Distinct from OpenSkillsHub
// (know-how) and OpenToolsHub (executables) — this is the RUNTIME an agent runs
// in: a bounded adapter that emits run receipts. The thing that runs the agent.

const E = PORTFOLIO.ENTITIES.openAgentHub;
const App = makeHub({
  brand: { name: 'OpenAgentHub', tld: '.io', glyph: '◈', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'oag-theme',
  noun: 'runtime', nounPlural: 'runtimes', indefinite: 'a runtime',
  heroTitle: <>The runtime that <span className="tint">runs the agent.</span></>,
  lede: 'Skills are know-how; tools are executables; a runtime is what actually runs an agent — a bounded adapter with a declared loop, scopes and a run receipt for every step. OpenAgentHub registers them so you can run an agent in a governed runtime and get back evidence, not just an answer.',
  ledeVariants: {
    A: 'Skills are know-how; tools are executables; a runtime is what actually runs an agent — a bounded adapter with a declared loop, scopes and a run receipt for every step. OpenAgentHub registers them so you can run an agent in a governed runtime and get back evidence, not just an answer.',
    B: 'An agent needs something to run it. Bounded adapters with declared loops, scopes and run receipts — the runtime layer, governed.',
    C: 'Know-how, executables, and the runtime that runs them. OpenAgentHub is the registry of bounded agent runtimes that emit a receipt per step.',
  },
  howTitle: 'Run an agent, get a receipt.',
  howBody: <>Browse <strong>runtimes</strong> — bounded adapters over the common agent frameworks — each with a declared
    loop, the <strong>scopes</strong> it runs under and a <strong>run receipt</strong> for every step. Run an agent inside one
    and it composes the rest of the stack: tools from OpenToolsHub, a sandbox from OpenSandboxHub, evidence to Teleon.</>,
  features: [
    ['◈', 'Bounded adapter', 'Each runtime wraps a framework in a declared, bounded loop — step limits, timeouts, no runaway.'],
    ['⚿', 'Scoped by default', 'A runtime runs under explicit least-privilege scopes; it can only reach what it declared.'],
    ['◷', 'Run receipts', 'Every step emits a signed receipt — what it called, with what, and why. Evidence, not just an answer.'],
  ],
  facets: ['ReAct', 'Graph', 'Multi-agent', 'Coding', 'Workflow'],
  standards: [
    ['Run receipts', 'a signed receipt per step — what ran, with which scopes, when'],
    ['MCP', 'runtimes call tools over MCP; scopes enforced at the boundary'],
    ['Sigstore', 'signed runtime adapters + run records you can verify'],
    ['in-toto attestation', 'how a runtime adapter was produced and tested'],
    ['CycloneDX AI-BOM', 'each runtime adapter carries a bill of materials'],
    ['SemVer + cards', 'versioned runtime cards with a changelog'],
  ],
  trust: (e) => [
    ['Signature', 'cosign ✓', true],
    ['Provenance', 'SLSA L3', true],
    ['Run receipts', 'in-toto ✓', true],
    ['Scopes', 'least-privilege', true],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  installCmd: (e) => 'oag run ' + e.id + '@' + (e.ver || '1.0.0') + ' --agent <id>\n# → runs the agent in a bounded runtime; emits a run receipt per step',
  entries: [
    { id: 'react-bounded', name: 'ReAct Runtime · bounded', by: '@agent-open', facet: 'ReAct', score: '4.7', installs: '6.1k', ver: '2.0.0', desc: 'A bounded ReAct loop adapter: step + tool-call with hard limits, scoped tools, and a receipt per step. The default runtime.' },
    { id: 'graph-runtime', name: 'Graph Runtime', by: '@graph-open', facet: 'Graph', score: '4.6', installs: '4.3k', ver: '1.4.0', desc: 'A state-graph runtime adapter: declared nodes/edges, per-node scopes, deterministic resume, receipts at each transition.' },
    { id: 'multi-agent-orchestrator', name: 'Multi-Agent Orchestrator', by: '@swarm-open', facet: 'Multi-agent', score: '4.4', installs: '2.9k', ver: '1.2.0', desc: 'A bounded orchestrator over multiple sub-agents with a shared blackboard; per-agent scopes and a consolidated run receipt.' },
    { id: 'coding-runtime', name: 'Coding Runtime', by: '@dev-open', facet: 'Coding', score: '4.8', installs: '5.0k', ver: '1.6.0', desc: 'A coding-agent runtime that pairs with a sandbox from OpenSandboxHub: edits + runs code in isolation, receipts per command.' },
    { id: 'workflow-runtime', name: 'Workflow Runtime', by: '@teleon', facet: 'Workflow', score: '4.7', installs: '3.5k', ver: '1.3.0', desc: 'A durable workflow runtime for long-running tasks: checkpointed steps, retries, and a signed receipt ledger — the Teleon-style spine.' },
    { id: 'react-lite', name: 'ReAct Runtime · lite', by: '@agent-open', facet: 'ReAct', score: '4.3', installs: '3.0k', ver: '1.1.0', desc: 'A minimal ReAct adapter for low-latency single-tool tasks; tight step cap, one scope, one receipt. Small surface, fully governed.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
