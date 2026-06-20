/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenSandboxHub.io — isolated sandbox registry + risk/conformance.
// PRIVATE-FIRST candidate: opens publicly when a competitor enters the lane.
// The OpenMCPHub "discovery is not trust" pattern, applied to the RUNTIMES that
// execute agent code (E2B / Daytona / agent-sandbox class). Distinct from
// OpenEnvHub (the task world) — a sandbox is the ISOLATION the code runs inside.

const E = PORTFOLIO.ENTITIES.openSandboxHub;
const App = makeHub({
  brand: { name: 'OpenSandboxHub', tld: '.io', glyph: '⊠', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'osbx-theme',
  noun: 'sandbox', nounPlural: 'sandboxes', indefinite: 'a sandbox',
  heroTitle: <>Where agent code <span className="tint">runs safely.</span></>,
  lede: 'A sandbox is the isolated runtime your agent’s code executes inside — filesystem, network and process boundaries it cannot cross. OpenSandboxHub registers them with a risk & conformance profile (isolation class, egress policy, escape-test results) so you can choose where untrusted code runs. Discovery is not trust, applied to runtimes.',
  ledeVariants: {
    A: 'A sandbox is the isolated runtime your agent’s code executes inside — filesystem, network and process boundaries it cannot cross. OpenSandboxHub registers them with a risk & conformance profile (isolation class, egress policy, escape-test results) so you can choose where untrusted code runs. Discovery is not trust, applied to runtimes.',
    B: 'Untrusted code needs a proven box. Isolation class, egress policy and escape-test results for every sandbox runtime — signed.',
    C: 'Before you run agent-written code, know the box. OpenSandboxHub profiles sandbox runtimes for isolation, egress and conformance.',
  },
  howTitle: 'Choose the box before you run the code.',
  howBody: <>Browse <strong>sandboxes</strong> — E2B, Daytona and agent-sandbox class runtimes — each with an
    <strong> isolation class</strong>, an <strong>egress policy</strong> and escape-test results. Match the sandbox to the
    trust level of the code, and carry its conformance profile into your execution policy. Discovery is not trust.</>,
  features: [
    ['⊠', 'Isolation class', 'Each sandbox declares its boundary — container, microVM or stronger — so you match it to the code’s trust level.'],
    ['⇄', 'Egress policy', 'What the sandbox may reach: no-network, allowlist or open. Declared, not assumed.'],
    ['⛨', 'Escape-tested & signed', 'Conformance + escape-test results with a risk score and signed provenance; quarantine on a failed test.'],
  ],
  facets: ['MicroVM', 'Container', 'Browser', 'GPU', 'Ephemeral'],
  standards: [
    ['OpenSSF Scorecard', 'automated risk scoring per sandbox — discovery is not trust'],
    ['Isolation conformance', 'declared boundary + escape-test results, not a marketing claim'],
    ['Sigstore', 'signed sandbox profiles you can verify by hash'],
    ['in-toto attestation', 'what conformance suite ran, on which sandbox version'],
    ['CycloneDX AI-BOM', 'each sandbox image carries a bill of materials'],
    ['SemVer + cards', 'versioned sandbox cards with a changelog'],
  ],
  trust: (e) => [
    ['Signature', 'cosign ✓', true],
    ['Risk · Scorecard', '8.8 / 10', true],
    ['Escape-tested', 'conformance ✓', true],
    ['Egress', 'see policy', false],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  installCmd: (e) => 'osbx profile ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → emits an isolation + egress profile for your execution policy',
  entries: [
    { id: 'microvm-firecracker', name: 'MicroVM · Firecracker-class', by: '@sandbox-open', facet: 'MicroVM', score: '4.9', installs: '5.8k', ver: '2.0.0', desc: 'A microVM sandbox with hardware-level isolation; no-network by default. The strongest box for untrusted agent code.' },
    { id: 'container-rootless', name: 'Container · rootless', by: '@sandbox-open', facet: 'Container', score: '4.6', installs: '6.2k', ver: '1.4.0', desc: 'A rootless container sandbox: fast start, allowlist egress. Good for semi-trusted code; weaker boundary than a microVM.' },
    { id: 'browser-sandbox', name: 'Browser Sandbox', by: '@web-open', facet: 'Browser', score: '4.5', installs: '3.1k', ver: '1.2.0', desc: 'An isolated headless-browser runtime for web agents; navigation only, no host filesystem. Egress allowlisted by domain.' },
    { id: 'gpu-sandbox', name: 'GPU Sandbox', by: '@infra-open', facet: 'GPU', score: '4.4', installs: '2.0k', ver: '1.1.0', desc: 'A GPU-passthrough sandbox for model/code that needs acceleration; container-class isolation — match to trust level.' },
    { id: 'ephemeral-devbox', name: 'Ephemeral Devbox', by: '@daytona-open', facet: 'Ephemeral', score: '4.7', installs: '4.4k', ver: '1.6.0', desc: 'A throwaway dev workspace per task with a clean state and run receipt; allowlist egress, destroyed after the run.' },
    { id: 'agent-sandbox-k8s', name: 'Agent-Sandbox · k8s', by: '@platform-open', facet: 'Container', score: '4.5', installs: '2.6k', ver: '1.3.0', desc: 'A kubernetes-native agent-sandbox pattern with per-pod policy; conformance-tested, egress by network policy.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
