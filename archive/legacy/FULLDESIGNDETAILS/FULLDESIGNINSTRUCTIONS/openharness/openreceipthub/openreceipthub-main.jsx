/* global React, ReactDOM, PORTFOLIO, makeHub */
// OpenReceiptHub.io — portable, signed receipts. Built on the shared hub module.
// PRIVATE-FIRST candidate: opens publicly when a competitor enters the lane.
// The attestation face of the family — complements OpenReviewHub (a review is a
// VERDICT; a receipt is a portable ATTESTATION of what happened). Drawn from the
// receipt + AI-BOM / provenance spine (Sigstore · in-toto · CycloneDX · C2PA).

const E = PORTFOLIO.ENTITIES.openReceiptHub;
const App = makeHub({
  brand: { name: 'OpenReceiptHub', tld: '.io', glyph: '⊡', accent: E.accent },
  kind: E.kind, access: E.status === 'private' ? 'private' : undefined, openTrigger: E.openTrigger,
  themeKey: 'orc-theme',
  noun: 'receipt', nounPlural: 'receipts', indefinite: 'a receipt',
  heroTitle: <>Proof that <span className="tint">travels with the work.</span></>,
  lede: 'A receipt is a portable, signed attestation of what happened — a model invocation, a served pack, a run, a review, an approval — that travels with the artifact and verifies anywhere, by anyone, by hash. The attestation face of the family: discovery is not trust, a receipt is.',
  ledeVariants: {
    A: 'A receipt is a portable, signed attestation of what happened — a model invocation, a served pack, a run, a review, an approval — that travels with the artifact and verifies anywhere, by anyone, by hash. The attestation face of the family: discovery is not trust, a receipt is.',
    B: 'A screenshot is not proof. Portable, signed receipts — invocation, serve, run, review, approval — that verify anywhere, offline, by hash.',
    C: 'Every step leaves a receipt: what ran, on what, under which policy. Signed, chained, and verifiable by anyone — not a log you have to trust.',
  },
  howTitle: 'Proof you can hand to anyone.',
  howBody: <>Every consequential step in the family emits a <strong>receipt</strong> — a model invocation, a served context pack,
    a runtime step, a review verdict, a human approval. Each is <strong>signed</strong>, written to a transparency log, and
    references the artifacts and prior receipts it depends on. Hand one to an auditor; they verify it without trusting you.</>,
  features: [
    ['⊡', 'Portable attestation', 'A signed record of what happened — model, hashed inputs, scopes, outcome — that verifies anywhere, offline.'],
    ['⛨', 'Signed & tamper-evident', 'cosign + a transparency log: alter a receipt and the signature breaks. Discovery is not trust; a receipt is.'],
    ['◷', 'Chained provenance', 'Each receipt references the artifacts and prior receipts it depends on — a verifiable chain, not a screenshot.'],
  ],
  facets: ['Invocation', 'Serve', 'Run', 'Review', 'Approval'],
  standards: [
    ['Sigstore', 'keyless signing + Rekor transparency log for every receipt'],
    ['in-toto attestation', 'what produced the artifact, attested step by step'],
    ['SLSA provenance', 'build/run provenance at L3 — verifiable, not asserted'],
    ['C2PA', 'content provenance — the portable-attestation standard for media + artifacts'],
    ['CycloneDX AI-BOM', 'each receipt carries the artifact’s bill of materials'],
    ['SemVer + schema', 'versioned receipt schemas with a changelog'],
  ],
  trust: (e) => [
    ['Signature', 'cosign ✓', true],
    ['Transparency log', 'rekor ✓', true],
    ['Chain', 'verified ✓', true],
    ['Receipt records', 'reality, not intent', false],
    ['AI-BOM', 'CycloneDX ✓', true],
  ],
  installCmd: (e) => 'orc verify ' + e.id + '@' + (e.ver || '1.0.0') + '\n# → checks the signature + transparency log; prints the verified chain',
  entries: [
    { id: 'model-invocation', name: 'ModelInvocationReceipt', by: '@gateway-open', facet: 'Invocation', score: '4.9', installs: '7.8k', ver: '2.0.0', desc: 'Every LLM call: the model + route chosen, hashed prompt, declared scopes, latency and cost — signed. The receipt the Inference Gateway emits.' },
    { id: 'served-pack', name: 'Served-Pack Receipt', by: '@baltor', facet: 'Serve', score: '4.8', installs: '5.2k', ver: '1.4.0', desc: 'A Baltor served context pack: the source handles, citations and the policy it was served under — provable to an examiner by hash.' },
    { id: 'run-receipt', name: 'Run Receipt', by: '@agent-open', facet: 'Run', score: '4.7', installs: '4.6k', ver: '1.5.0', desc: 'One agent-runtime step: the tool called, the argument hash, the scope it ran under, and the outcome. Chains into a full run.' },
    { id: 'review-record', name: 'Portable Review Record', by: '@review-open', facet: 'Review', score: '4.6', installs: '3.1k', ver: '1.2.0', desc: 'An OpenReviewHub verdict made portable: claim → evidence → reproduced, signed, so the review travels with the artifact it reviewed.' },
    { id: 'human-approval', name: 'HumanApprovalReceipt', by: '@teleon', facet: 'Approval', score: '4.7', installs: '2.4k', ver: '1.1.0', desc: 'A human-gated boundary approval: who approved what, when, under which policy — the signed evidence a boundary was crossed deliberately.' },
    { id: 'promotion-receipt', name: 'Promotion Receipt', by: '@teleon', facet: 'Approval', score: '4.5', installs: '1.9k', ver: '1.0.0', desc: 'A Teleon eval-gated promotion: the candidate, the evidence, the gate it cleared and the decision — proof a candidate was promoted on evidence, not a hunch.' },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
