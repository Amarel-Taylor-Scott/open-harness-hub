/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenEndpointHub.io — governed due-diligence on LLM endpoints + gateways.
// PRIVATE-FIRST candidate: opens publicly when a competitor enters the lane.
// Drawn from the endpoint registries + free_endpoint_intel. Distinct from
// OpenMCPHub (MCP servers) — this is the model ENDPOINTS themselves and the
// question "what data may I send where": data-class & jurisdiction eligibility.

const E = PORTFOLIO.ENTITIES.openEndpointHub;
const App = makeHub({
  brand: { name: 'OpenEndpointHub', tld: '.io', glyph: '⇄', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'oep-theme',
  noun: 'endpoint', nounPlural: 'endpoints', indefinite: 'an endpoint',
  heroTitle: <>What data may I <span className="tint">send where?</span></>,
  lede: 'OpenEndpointHub is governed due-diligence on LLM endpoints — free, low-cost and frontier — and the gateways in front of them. Each entry carries a data-class & jurisdiction eligibility profile, a risk score and provenance, so a route decision is a policy, not a guess. Discovery is not trust.',
  ledeVariants: {
    A: 'OpenEndpointHub is governed due-diligence on LLM endpoints — free, low-cost and frontier — and the gateways in front of them. Each entry carries a data-class & jurisdiction eligibility profile, a risk score and provenance, so a route decision is a policy, not a guess. Discovery is not trust.',
    B: 'A free endpoint is not a safe endpoint. Eligibility by data-class and jurisdiction, risk-scored and signed — for every LLM endpoint and gateway.',
    C: 'Which endpoint may see which data, from which jurisdiction? OpenEndpointHub answers it with an eligibility profile per endpoint — not a vibe.',
  },
  howTitle: 'Eligibility before you route.',
  howBody: <>Browse <strong>endpoints</strong> and gateways with a clear eligibility profile: which <strong>data class</strong>
    each may receive, under which <strong>jurisdiction</strong>, at what cost and risk. Free and low-cost providers are
    classified, not banned — quarantined when the data class demands it. Pull the profile into your gateway’s routing policy.</>,
  features: [
    ['⇄', 'Data-class eligibility', 'Each endpoint declares which data classes it may receive — public, internal, restricted — never blind.'],
    ['⚖', 'Jurisdiction & cost', 'Where it runs, under whose law, and at what price — free and low-cost included, classified not assumed.'],
    ['⛨', 'Risk-scored & signed', 'An OpenSSF-style risk score and signed provenance per endpoint; quarantine when the data class demands it.'],
  ],
  facets: ['Frontier', 'Low-cost', 'Free', 'Gateway', 'Self-host'],
  standards: [
    ['OpenSSF Scorecard', 'automated risk scoring per endpoint — discovery is not trust'],
    ['Data classification', 'public / internal / restricted eligibility, declared and enforced'],
    ['Sigstore', 'signed endpoint profiles you can verify by hash'],
    ['in-toto attestation', 'what was tested against the endpoint, when'],
    ['CycloneDX AI-BOM', 'each endpoint/gateway carries a bill of materials'],
    ['SemVer + cards', 'versioned endpoint cards with a changelog'],
  ],
  trust: (e) => [
    ['Signature', 'cosign ✓', true],
    ['Risk · Scorecard', '8.6 / 10', true],
    ['Data-class', 'eligibility declared', true],
    ['Jurisdiction', 'see profile', false],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  installCmd: (e) => 'oep profile ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → emits an eligibility profile for your gateway routing policy',
  entries: [
    { id: 'frontier-hosted-a', name: 'Frontier Hosted · Provider A', by: '@gateway-open', facet: 'Frontier', score: '4.8', installs: '7.1k', ver: '2.0.0', desc: 'A frontier hosted endpoint: eligible for internal data under a US/EU DPA; restricted data quarantined. High cost, low risk.' },
    { id: 'lowcost-hosted-b', name: 'Low-cost Hosted · Provider B', by: '@cost-open', facet: 'Low-cost', score: '4.5', installs: '5.3k', ver: '1.3.0', desc: 'A low-cost hosted endpoint: eligible for public + internal data; jurisdiction noted. Strong price/perf, medium risk.' },
    { id: 'free-cn-endpoint', name: 'Free Endpoint · CN-hosted', by: '@endpoint-intel', facet: 'Free', score: '4.1', installs: '4.0k', ver: '1.1.0', desc: 'A free CN-hosted endpoint: public data only, restricted + internal QUARANTINED by jurisdiction. Classified, not banned — discovery ≠ trust.' },
    { id: 'gateway-litellm', name: 'Gateway · multi-provider router', by: '@gateway-open', facet: 'Gateway', score: '4.7', installs: '6.4k', ver: '2.1.0', desc: 'An open gateway that fronts many endpoints; carries each upstream’s eligibility and enforces the route policy + ModelInvocationReceipt.' },
    { id: 'selfhost-ow-7b', name: 'Self-host · open-weights 7B', by: '@selfhost-open', facet: 'Self-host', score: '4.6', installs: '3.2k', ver: '1.5.0', desc: 'A self-hosted open-weights endpoint: eligible for restricted data in your own VPC; cost is your infra, risk is your control.' },
    { id: 'lowcost-cn-frontier', name: 'Low-cost Frontier · CN-hosted', by: '@endpoint-intel', facet: 'Low-cost', score: '4.3', installs: '2.7k', ver: '1.0.0', desc: 'A low-cost CN-hosted frontier-class endpoint: public data eligible, internal/restricted quarantined pending a jurisdiction review.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
