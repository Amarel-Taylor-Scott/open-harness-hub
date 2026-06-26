/* OpenHubForAI — shared catalog/flow data, ported VERBATIM from the design prototype
   (proto-store.jsx + proto-pages-build.jsx TIERS). Pages read OpenHubForAI.data; never redeclare. */
window.OpenHubForAI = window.OpenHubForAI || {};
window.OpenHubForAI.data = (function () {
const COMPONENTS = [
  { slug: 'esg-cite-first', primitive: 'action', type: 'harness', name: 'Cite-first ESG counsel', desc: 'Holds a deterministic citation gate before the model answers, so every CSDDD claim resolves to a sourced article across 13 languages.', lift: 0.41, cost: '$$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'code', industry: 'ESG' },
  { slug: 'csddd-articles', primitive: 'knowledge', type: 'knowledge-corpus', name: 'CSDDD article corpus', desc: 'The full CSDDD regulation at article level, across 13 languages, with per-fact provenance.', lift: 0.18, cost: '⌂', recurring: false, prov: 'sourced', license: 'CC-BY-4.0', lifecycle: 'stable', exec: 'static', industry: 'ESG' },
  { slug: 'tier-risk-gate', primitive: 'conditional', type: 'rule-pack', name: 'High-risk tier gate', desc: 'Routes a supplier to human review when tier ≥ 2 or the sector is high-risk. Deterministic, no model call.', lift: 0.09, cost: '⌂', recurring: false, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'static', industry: 'ESG' },
  { slug: 'ofac-sdn', primitive: 'knowledge', type: 'knowledge-corpus', name: 'OFAC / SDN list', desc: 'Live sanctions list with change-data-capture freshness and revocation.', lift: 0.12, cost: '$', recurring: true, prov: 'verified', license: 'CC0', lifecycle: 'stable', exec: 'static', industry: 'AML', fresh: true },
  { slug: 'aml-screen', primitive: 'conditional', type: 'rule-pack', name: 'AML screen', desc: 'Blocks on a sanctions / PEP match; escalates partial matches to review.', lift: 0.07, cost: '⌂', recurring: false, prov: 'sourced', license: 'MIT', lifecycle: 'beta', exec: 'static', industry: 'AML' },
  { slug: 'pdf-redactor', primitive: 'action', type: 'tool', name: 'PDF redactor', desc: 'Deterministic PII redaction over PDFs. Structural lift; no model call.', lift: null, liftClass: 'structural', cost: '⌂', recurring: false, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'code', industry: 'General' },
  { slug: 'entity-resolver', primitive: 'action', type: 'processor', name: 'Entity resolver', desc: 'Resolves supplier names to legal entities (LEI) before grading.', lift: 0.14, cost: '$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'beta', exec: 'code', industry: 'General' },
  { slug: 'supplier-grade', primitive: 'action', type: 'rubric', name: 'Supplier grading rubric', desc: 'Weighted dimensions for CSDDD supplier grading; reused by evals.', lift: 0.11, cost: '⌂', recurring: false, prov: 'sourced', license: 'CC-BY-4.0', lifecycle: 'stable', exec: 'static', industry: 'ESG' },
  { slug: 'rubric-refine', primitive: 'loop', type: 'pattern', name: 'Review & refine', desc: 'Re-runs the same harness call until the rubric passes (max 3 passes).', lift: 0.08, cost: '$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'text', industry: 'General' },
  { slug: 'research-entity', primitive: 'loop', type: 'pipeline', name: 'Research entity', desc: 'A full multi-step entity-research pipeline, deployable as one component.', lift: 0.55, cost: '$$$', recurring: true, prov: 'verified', license: 'MIT', lifecycle: 'beta', exec: 'code', industry: 'General' },
  { slug: 'budget-ceiling', primitive: 'stop', type: 'guard', name: 'Budget guard', desc: 'Halts a run when estimated spend exceeds the ceiling.', lift: null, cost: '⌂', recurring: false, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'static', industry: 'General' },
  { slug: 'csddd-dossier', primitive: 'output', type: 'output', name: 'Graded supplier dossier', desc: 'PDF + JSON-LD dossier with inline citations, ready for audit export.', lift: null, cost: '⌂', recurring: false, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'static', industry: 'ESG' },
  { slug: 'gxp-sops', primitive: 'knowledge', type: 'knowledge-corpus', name: 'GxP SOP library', desc: 'Standard operating procedures for GxP compliance. Provenance incomplete.', lift: 0.16, cost: '⌂', recurring: false, prov: 'unsourced', license: '—', lifecycle: 'experimental', exec: 'static', industry: 'GxP' },
  { slug: 'customs-hs', primitive: 'knowledge', type: 'knowledge-corpus', name: 'Customs HS codes', desc: 'Harmonized System tariff codes with descriptions, 200+ jurisdictions.', lift: 0.10, cost: '⌂', recurring: false, prov: 'sourced', license: 'CC-BY-4.0', lifecycle: 'stable', exec: 'static', industry: 'Customs' },
];

// ---- multi-modal governed pipelines (Explore › Pipelines, split by input modality) ----
const MEDIA_PIPELINES = [
  // text (rounds the text tab to 4 alongside esg-cite-first / rubric-refine / research-entity)
  { slug: 'contract-risk', primitive: 'action', type: 'pipeline', name: 'Contract renewal-risk review', desc: 'Flags auto-renewal, liability and price-escalation clauses against a sourced clause library, citing the exact span in every contract.', lift: 0.33, cost: '$$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'code', industry: 'Legal', modality: 'text' },
  // image
  { slug: 'invoice-extract', primitive: 'action', type: 'pipeline', name: 'Invoice line-item extractor', desc: 'Reads scanned invoices into structured line items, validating totals against a deterministic arithmetic gate before export.', lift: 0.37, cost: '$$', recurring: true, prov: 'verified', license: 'MIT', lifecycle: 'stable', exec: 'code', industry: 'Finance', modality: 'image' },
  { slug: 'id-doc-verify', primitive: 'conditional', type: 'pipeline', name: 'ID document verifier', desc: 'Checks government-ID images for tamper signatures and MRZ consistency, escalating low-confidence scans to human review.', lift: 0.29, cost: '$$', recurring: true, prov: 'verified', license: 'MIT', lifecycle: 'beta', exec: 'code', industry: 'KYC', modality: 'image' },
  { slug: 'chart-to-data', primitive: 'action', type: 'pipeline', name: 'Chart-to-data reader', desc: 'Recovers the underlying series from a chart image and emits CSV with a provenance note attached to every extracted point.', lift: 0.24, cost: '$', recurring: true, prov: 'sourced', license: 'CC-BY-4.0', lifecycle: 'beta', exec: 'code', industry: 'Research', modality: 'image' },
  { slug: 'defect-triage', primitive: 'loop', type: 'pipeline', name: 'Visual defect triage', desc: 'Loops over production-line frames, grading each against a defect rubric and tripping a stop when the threshold is exceeded.', lift: 0.31, cost: '$$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'beta', exec: 'code', industry: 'Manufacturing', modality: 'image' },
  // audio
  { slug: 'call-qa', primitive: 'loop', type: 'pipeline', name: 'Call-center QA grader', desc: 'Transcribes support calls and scores them against a compliance rubric, citing the exact timestamp behind each deduction.', lift: 0.28, cost: '$$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'code', industry: 'Support', modality: 'audio' },
  { slug: 'meeting-minutes', primitive: 'action', type: 'pipeline', name: 'Cited meeting minutes', desc: 'Turns a meeting recording into decisions and action items, each linked back to the spoken span that produced it.', lift: 0.22, cost: '$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'text', industry: 'General', modality: 'audio' },
  { slug: 'clinical-dictation', primitive: 'action', type: 'pipeline', name: 'Clinical dictation → note', desc: 'Structures a dictated encounter into a SOAP note, gating any coded diagnosis on a sourced terminology corpus.', lift: 0.34, cost: '$$', recurring: true, prov: 'verified', license: 'MIT', lifecycle: 'beta', exec: 'code', industry: 'Healthcare', modality: 'audio' },
  { slug: 'call-redact', primitive: 'action', type: 'pipeline', name: 'Call PII redactor', desc: 'Detects and bleeps PII in call recordings deterministically, emitting a redaction log for audit.', lift: 0.19, cost: '$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'stable', exec: 'code', industry: 'Compliance', modality: 'audio' },
  // video
  { slug: 'deposition-index', primitive: 'loop', type: 'pipeline', name: 'Deposition video indexer', desc: 'Indexes deposition footage into a searchable transcript with exhibit links and timestamped citations for every claim.', lift: 0.30, cost: '$$$', recurring: true, prov: 'verified', license: 'MIT', lifecycle: 'beta', exec: 'code', industry: 'Legal', modality: 'video' },
  { slug: 'safety-incident', primitive: 'conditional', type: 'pipeline', name: 'Safety-incident triage', desc: 'Screens CCTV clips for incident signatures and routes confirmed events to the EHS queue with a sourced policy reference.', lift: 0.26, cost: '$$', recurring: true, prov: 'sourced', license: 'MIT', lifecycle: 'beta', exec: 'code', industry: 'EHS', modality: 'video' },
  { slug: 'ad-compliance', primitive: 'action', type: 'pipeline', name: 'Ad-creative compliance check', desc: 'Reviews video ads against an advertising-standards corpus, citing the rule behind every flagged frame or claim.', lift: 0.21, cost: '$$', recurring: true, prov: 'sourced', license: 'CC-BY-4.0', lifecycle: 'beta', exec: 'text', industry: 'Marketing', modality: 'video' },
  { slug: 'lecture-chapter', primitive: 'output', type: 'pipeline', name: 'Lecture auto-chaptering', desc: 'Splits lecture video into chapters with a cited transcript and a glossary linked to a sourced knowledge corpus.', lift: 0.18, cost: '$', recurring: true, prov: 'sourced', license: 'CC-BY-4.0', lifecycle: 'stable', exec: 'code', industry: 'Education', modality: 'video' },
];
COMPONENTS.push(...MEDIA_PIPELINES);

const BY_SLUG = Object.fromEntries(COMPONENTS.map((c) => [c.slug, c]));
// classify catalog entries: pipelines (lift makes sense here) vs components, + ownership tier
COMPONENTS.forEach((c, i) => {
  c.kind = ['harness', 'pipeline', 'pattern'].includes(c.type) ? 'pipeline' : 'component';
  c.owner = ['free', 'premium', 'community-free', 'community-paid'][i % 4];
  c.modality = c.modality || 'text';
});
const MODALITIES = [['text', 'Text', '⌶'], ['image', 'Image', '◰'], ['audio', 'Audio', '◵'], ['video', 'Video', '▷']];
const COST_LABEL = { '$': 'Low cost', '$$': 'Medium cost', '$$$': 'High cost', '⌂': 'Local / on-prem' };

// flow definition for /flow — coordinate layout (FW 198 × FH 84) + edges + a loop
const PFW = 198, PFH = 84;
const PFLOW = {
  nodes: [
    { id: 'input', k: 'input', name: 'Supplier (1 row)', ref: 'inputs/supplier-roster', facts: '⌖ one item / iteration', x: 14, y: 176 },
    { id: 'ct', k: 'conditional', slug: 'tier-risk-gate', name: 'High-risk tier gate', ref: 'conditional/tier-risk-gate', facts: '◈ rule-pack · tier ≥ 2', x: 240, y: 64 },
    { id: 'ca', k: 'conditional', slug: 'aml-screen', name: 'AML / sanctions screen', ref: 'conditional/aml-screen', facts: '◈ rule-pack · match → block', x: 240, y: 300 },
    { id: 'kc', k: 'knowledge', slug: 'csddd-articles', lift: '+0.18', name: 'CSDDD article corpus', ref: 'knowledge-corpus/csddd-articles', facts: '⛁ rag · static · ✔', x: 580, y: 176 },
    { id: 'act', k: 'action', slug: 'esg-cite-first', lift: '+0.41', name: 'Cite-first ESG counsel', ref: 'harness/esg-cite-first', facts: '⚡ harness · 1 call · ● code', x: 806, y: 176 },
    { id: 'ev', k: 'loop', slug: 'rubric-refine', name: 'Review & refine', ref: 'pattern/rubric-refine', facts: '↻ until rubric ≥ 0.8', x: 1032, y: 176 },
    { id: 'out', k: 'output', slug: 'csddd-dossier', name: 'Graded dossier', ref: 'outputs/csddd-dossier', facts: '⎘ pdf+json-ld · ✓', x: 1258, y: 176 },
  ],
  op: { x: 466, y: 198, w: 84, h: 40 },
};
// ranked swap alternatives per node (by lift) — used in the inspector
const ALTS = {
  act: [
    { slug: 'esg-cite-first', name: 'Cite-first ESG counsel', meta: '▲ +0.41 · $$ · ✔ sourced', on: true },
    { slug: 'research-entity', name: 'Research entity (pipeline)', meta: '▲ +0.55 · $$$ · 🛡 verified' },
    { slug: null, name: 'Bare model call', meta: '▲ — unproven · $$ · ⚠ no gate' },
  ],
  kc: [
    { slug: 'csddd-articles', name: 'CSDDD article corpus', meta: '▲ +0.18 · ⌂ · ✔ sourced', on: true },
    { slug: 'gxp-sops', name: 'GxP SOP library', meta: '▲ +0.16 · ⌂ · ⚠ unsourced' },
  ],
};
  // costed result tiers (from proto-pages-build.jsx)
const TIERS = [
  { tier: 'Cheap', dag: ['input', 'knowledge', 'action', 'output'], lift: '+0.21', comps: '4 components', packs: '1 knowledge pack', gov: 'keyword · MIT', cost: 'est. low', lat: '~6s', freeze: '~80% freezable' },
  { tier: 'Balanced', rec: true, dag: ['input', 'conditional', 'op', 'knowledge', 'action', 'output'], lift: '+0.41', comps: '6 components', packs: '2 knowledge · 1 conditional', gov: 'sourced · MIT', cost: 'est. medium', lat: '~14s', freeze: '~65% freezable' },
  { tier: 'Quality-first', dag: ['input', 'conditional', 'op', 'knowledge', 'action', 'loop', 'output'], lift: '+0.55', comps: '9 components', packs: '3 knowledge · 2 conditional', gov: 'verified · CC-BY', cost: 'est. high', lat: '~38s', freeze: '~55% freezable' },
];
  var EXEC_COLOR = { static: 'var(--fg-muted)', text: 'var(--info)', code: 'var(--accent)' };
  return { COMPONENTS: COMPONENTS, MEDIA_PIPELINES: MEDIA_PIPELINES, BY_SLUG: BY_SLUG, MODALITIES: MODALITIES, COST_LABEL: COST_LABEL, PFW: PFW, PFH: PFH, PFLOW: PFLOW, ALTS: ALTS, TIERS: TIERS, EXEC_COLOR: EXEC_COLOR };
})();
