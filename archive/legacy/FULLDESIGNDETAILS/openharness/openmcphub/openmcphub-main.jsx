/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenMCPHub.io — MCP server intelligence layer. Built on the shared hub module.
// Proposed .io (domain/trademark unverified). Discovery is not trust — conformance + risk required.

const E = PORTFOLIO.ENTITIES.openMCPHub;
const App = makeHub({
  brand: { name: 'OpenMCPHub', tld: '.io', glyph: '⌁', accent: E.accent },
  kind: E.kind,
  themeKey: 'omcp-theme',
  noun: 'MCP server', nounPlural: 'MCP servers', indefinite: 'an MCP server',
  heroTitle: <>The intelligence layer for <span className="tint">MCP</span> servers.</>,
  standards: [
    ['MCP registry', 'built on the official Model Context Protocol registry + SDKs'],
    ['MCPTox checks', 'tool-poisoning + prompt-injection risk, scored per server'],
    ['Sigstore', 'keyless signing + transparency log for every server version'],
    ['SLSA + in-toto', 'verifiable provenance — who built it and how'],
    ['OpenSSF Scorecard', 'automated risk scoring — discovery is not trust'],
    ['Install profiles', 'least-privilege scopes declared and enforced'],
  ],
  trust: (e, h) => [
    ['Signature', 'cosign ✓', true],
    ['Conformance', 'MCP pack ✓', true],
    ['Tool-poisoning', 'MCPTox: clear', true],
    ['Risk · Scorecard', h.scorecard(e.score) + ' / 10', true],
    ['Scopes', 'least-privilege', true],
  ],
  lede: 'Discover, vet and install MCP servers — with conformance, risk and install profiles. Discovery is not trust; every server carries a conformance result and a risk score.',
  ledeVariants: {
    A: 'Discover, vet and install MCP servers — with conformance, risk and install profiles. Discovery is not trust; every server carries a conformance result and a risk score.',
    B: 'MCP discovery is not trust. Vet servers against conformance + risk before you install — one registry, one profile.',
    C: 'Stop installing MCP servers blind. See conformance, risk and required scopes before anything connects.',
  },
  howTitle: 'MCP servers, vetted before they connect.',
  howBody: <>Browse <strong>MCP servers</strong> the ecosystem has published, read their conformance and risk, and install
    against a profile. Or publish your own — every server is conformance-checked and carries a risk score and provenance.</>,
  features: [
    ['⌁', 'Conformance-checked', 'Each server runs the shared MCP conformance pack — tools, prompts and resources behave as declared.'],
    ['⛨', 'Risk-scored', 'A risk score reflects scopes requested, network reach and side-effects — not just popularity.'],
    ['◷', 'Install profiles', 'Pin a server + its scopes to a reproducible profile your agents can adopt safely.'],
  ],
  facets: ['Data', 'Dev', 'Search', 'Ops', 'Comms'],
  installCmd: (e) => 'omcp install ' + e.id + '@' + (e.ver || '1.0.0') + ' --profile vetted\n# → conformance + risk checked before connect',
  entries: [
    { id: 'filesystem-mcp', name: 'Filesystem MCP', by: '@anthropic-community', facet: 'Dev', score: '4.8', installs: '9.1k', ver: '1.4.0', desc: 'Scoped read/write filesystem access with path allow-lists. Conformance: pass · risk: medium (write scope).' },
    { id: 'postgres-mcp', name: 'Postgres MCP', by: '@data-commons', facet: 'Data', score: '4.7', installs: '6.3k', ver: '1.2.0', desc: 'Read-only query server over a connected Postgres. Conformance: pass · risk: low.', deps: ['pg-conn@1.0'] },
    { id: 'web-search-mcp', name: 'Web Search MCP', by: '@search-open', facet: 'Search', score: '4.6', installs: '8.4k', ver: '2.1.0', desc: 'Search the web and return cited passages. Conformance: pass · risk: low.' },
    { id: 'github-mcp', name: 'GitHub MCP', by: '@dev-open', facet: 'Dev', score: '4.5', installs: '5.8k', ver: '1.9.0', desc: 'Repo, issue and PR access with scoped tokens. Conformance: pass · risk: medium.', deps: ['gh-auth@1.2'] },
    { id: 'slack-mcp', name: 'Slack MCP', by: '@comms-open', facet: 'Comms', score: '4.3', installs: '3.4k', ver: '1.1.0', desc: 'Post and read messages in granted channels. Conformance: pass-with-notes · risk: medium.' },
    { id: 'shell-mcp', name: 'Shell MCP', by: '@ops-unverified', facet: 'Ops', score: '3.9', installs: '1.2k', ver: '0.7.0', desc: 'Arbitrary command execution. Conformance: fail · risk: HIGH — quarantined, install gated.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
