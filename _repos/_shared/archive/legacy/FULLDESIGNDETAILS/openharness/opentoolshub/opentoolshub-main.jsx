/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenToolsHub.io — open tool graph. Built on the shared hub module.

const E = PORTFOLIO.ENTITIES.openToolsHub;
const App = makeHub({
  brand: { name: 'OpenToolsHub', tld: '.io', glyph: '⚒', accent: E.accent },
  kind: E.kind,
  themeKey: 'oth-theme',
  noun: 'tool', nounPlural: 'tools', indefinite: 'a tool',
  heroTitle: <>The open registry of <span className="tint">tools</span> agents can call.</>,
  lede: 'Find, wire and publish governed tools — typed, permissioned actions agents can call safely, over MCP or HTTP, including from Teleon.',
  ledeVariants: {
    A: 'Find, wire and publish governed tools — typed, permissioned actions agents can call safely, over MCP or HTTP, including from Teleon.',
    B: 'Give agents tools you can actually govern — typed, permissioned, audited actions, over MCP or HTTP.',
    C: 'Agents are only as safe as the tools they can call. Wire governed, permissioned actions from one registry.',
  },
  howTitle: 'Governed tools, called safely.',
  howBody: <>Browse <strong>tools</strong> the community has published, grant scoped permissions, and let your agents call
    them. Or publish your own — every tool declares its schema, scopes and provenance.</>,
  features: [
    ['⚒', 'Typed & permissioned', 'Each tool declares a typed schema and the scopes it needs — no blind calls.'],
    ['⛨', 'Governed access', 'Grant least-privilege scopes per workspace; every call is logged and auditable.'],
    ['◎', 'MCP & HTTP', 'Call any tool over MCP or HTTP — works with Claude Code, Teleon, or your own agent.'],
  ],
  facets: ['Data', 'Comms', 'Code', 'Search', 'Ops'],
  installCmd: (e) => 'oth add ' + e.id + '@' + (e.ver || '1.2.0') + '\n# → registers the tool + requests its scopes',
  entries: [
    { id: 'web-fetch', name: 'Web Fetch', by: '@ada', facet: 'Search', score: '4.9', installs: '11k', ver: '2.0.0', desc: 'Fetch and clean a URL to readable text, with robots respect.' },
    { id: 'sql-runner', name: 'SQL Runner', by: '@data-commons', facet: 'Data', score: '4.7', installs: '6.8k', ver: '1.7.0', desc: 'Run a read-only query against a connected warehouse.', deps: ['warehouse-conn@1.0'] },
    { id: 'send-email', name: 'Send Email', by: '@comms-open', facet: 'Comms', score: '4.5', installs: '5.2k', ver: '1.3.1', desc: 'Send a templated email through a scoped, rate-limited sender.' },
    { id: 'gh-pr', name: 'GitHub PR', by: '@dev-open', facet: 'Code', score: '4.6', installs: '4.9k', ver: '2.2.0', desc: 'Open a pull request with a diff and description.', deps: ['gh-auth@1.2'] },
    { id: 'calendar', name: 'Calendar', by: '@ops-commons', facet: 'Ops', score: '4.4', installs: '3.1k', ver: '1.1.0', desc: 'Read and create calendar events on a connected account.' },
    { id: 'vector-search', name: 'Vector Search', by: '@ada', facet: 'Search', score: '4.8', installs: '7.7k', ver: '1.6.0', desc: 'Query a vector index and return ranked, cited passages.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
