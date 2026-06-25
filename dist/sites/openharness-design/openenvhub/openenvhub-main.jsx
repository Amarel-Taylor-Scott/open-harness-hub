/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenEnvHub.io — verifiable agent eval environments + reward specs.
// PRIVATE-FIRST candidate: opens publicly when a competitor enters the lane.
// Drawn from the Environment + Reward Spine. Distinct from OpenBenchmarkHub
// (definitions + result records) — an environment is the TASK WORLD a candidate
// is run against, with a reward spec; the score is downstream.

const E = PORTFOLIO.ENTITIES.openEnvHub;
const App = makeHub({
  brand: { name: 'OpenEnvHub', tld: '.io', glyph: '⊕', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'oenv-theme',
  noun: 'environment', nounPlural: 'environments', indefinite: 'an environment',
  heroTitle: <>The task world, <span className="tint">not the score.</span></>,
  lede: 'An environment is the verifiable world a candidate is run in — a task, its state, its tools and a reward spec that says what counts as success. OpenEnvHub registers them open and reproducible, so an eval is something you can re-run, not a number you take on faith. The score lives in OpenBenchmarkHub; the world lives here.',
  ledeVariants: {
    A: 'An environment is the verifiable world a candidate is run in — a task, its state, its tools and a reward spec that says what counts as success. OpenEnvHub registers them open and reproducible, so an eval is something you can re-run, not a number you take on faith. The score lives in OpenBenchmarkHub; the world lives here.',
    B: 'A leaderboard needs a world to run in. OpenEnvHub is the registry of verifiable eval environments and their reward specs — reproducible, signed.',
    C: 'Environments are the task world; benchmarks are the scoreboard. Register a reproducible world + reward spec a candidate can actually be run against.',
  },
  howTitle: 'A world a candidate can be run in.',
  howBody: <>Browse <strong>environments</strong> — each a task, its starting state, the tools available and a
    <strong> reward spec</strong> that defines success. Run a candidate in one to produce a reproducible eval, then record the
    number in <strong>OpenBenchmarkHub</strong>. A result is evidence; the environment is what makes it re-runnable.</>,
  features: [
    ['⊕', 'Task world + state', 'Each environment ships its task, starting state and available tools — the world a candidate actually runs in.'],
    ['◎', 'Reward spec', 'A declared, versioned definition of success — verifiable, not a vibe. The reward is part of the environment.'],
    ['↻', 'Reproducible runs', 'Pin the environment version and seed; the same run reproduces. Evidence, not authority.'],
  ],
  facets: ['Coding', 'Web', 'Tool-use', 'Reasoning', 'Safety'],
  standards: [
    ['Gymnasium / env interface', 'a standard environment interface — step, state, reward'],
    ['Reward spec', 'success defined as a versioned, verifiable spec — not a hidden judge'],
    ['Sigstore', 'signed environment + run records you can verify'],
    ['in-toto attestation', 'what ran, in which environment version, with which seed'],
    ['CycloneDX AI-BOM', 'each environment carries a bill of materials'],
    ['SemVer + cards', 'versioned environment cards with a changelog'],
  ],
  trust: (e) => [
    ['Signature', 'cosign ✓', true],
    ['Run attestation', 'in-toto ✓', true],
    ['Reproducible', 'pinned seed ✓', true],
    ['Reward is', 'a declared spec', false],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  installCmd: (e) => 'oenv run ' + e.id + '@' + (e.ver || '1.0.0') + ' --candidate <id>\n# → runs a candidate in the world; emits a reproducible eval record',
  entries: [
    { id: 'repo-fix-suite', name: 'Repo-Fix Environment', by: '@env-open', facet: 'Coding', score: '4.8', installs: '4.6k', ver: '2.0.0', desc: 'A sandboxed repo with failing tests; reward = tests pass without breaking others. The world behind a code-fix eval.' },
    { id: 'web-task-world', name: 'Web-Task Environment', by: '@web-open', facet: 'Web', score: '4.6', installs: '3.4k', ver: '1.3.0', desc: 'A deterministic web replica with tasks and a reward for completing them under tool scopes — no live-web flakiness.' },
    { id: 'tool-call-world', name: 'Tool-Use Environment', by: '@tools-open', facet: 'Tool-use', score: '4.7', installs: '3.9k', ver: '1.4.0', desc: 'A set of mock tools with a reward for correct tool, arguments and scope — the world an agent’s tool-use is scored in.' },
    { id: 'multi-hop-reasoning', name: 'Multi-Hop Reasoning Environment', by: '@reason-open', facet: 'Reasoning', score: '4.5', installs: '2.8k', ver: '1.2.0', desc: 'A grounded multi-hop task with a verifiable answer key; reward rewards the trace, not just the final answer.' },
    { id: 'held-out-survival-env', name: 'Held-Out Survival Environment', by: '@baltor-open', facet: 'Safety', score: '4.7', installs: '1.9k', ver: '1.1.0', desc: 'A governance world: a contradicted/allegation claim must stay held out through the pipeline. Reward = it never leaks.' },
    { id: 'budget-fidelity-env', name: 'Budget-Fidelity Environment', by: '@compression-open', facet: 'Reasoning', score: '4.4', installs: '2.1k', ver: '1.0.0', desc: 'A world that rewards answering correctly under a strict token budget — pairs with OpenCompressionHub candidates.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
