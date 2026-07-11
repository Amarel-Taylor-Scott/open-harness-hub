/* global React, PRODUCTS */
// Baltor.ai (folder/key: context-enrichment) — store: hash router, mock data,
// theme + flags, shared atoms. Brand identity pulled from shared/products.js.

const BRANDCE = PRODUCTS.contextEnrichment;

// ---------- hash router ----------
function useHashRoute() {
  const [route, setRoute] = React.useState(() => window.location.hash.slice(1) || '/');
  React.useEffect(() => {
    const on = () => setRoute(window.location.hash.slice(1) || '/');
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return route;
}
function navigate(to) { window.location.hash = to; }

// ---- feature flags / A-B variants ----
// Baltor now uses the SHARED experiments engine (window.OHExp / useExperiment) for A/B tests —
// see shared/oh-experiments.js + EXPERIMENTS.md. These thin shims remain ONLY for back-compat
// with any caller still reading a flag; they delegate to OHExp so there's one source of truth.
function useFlag(k) {
  try { const u = new URLSearchParams(location.search).get('flags'); if (u) { const m = u.split(',').map((s) => s.trim()).find((x) => x.startsWith(k + ':')); if (m) return m.split(':')[1]; } } catch (e) {}
  try { return (window.OHExp && window.OHExp.experiments().some((x) => x.key === 'baltor_' + k)) ? window.OHExp.variant('baltor_' + k) : undefined; } catch (e) { return undefined; }
}
function setFlag(k, v) { try { if (window.OHExp) window.OHExp.assign('baltor_' + k, v); } catch (e) {} }

// ---- theme (light/dark) — persists to localStorage, defaults to prefers-color-scheme ----
function useTheme() {
  const [theme, setTheme] = React.useState(() => {
    try { const s = localStorage.getItem('baltor-theme'); if (s === 'light' || s === 'dark') return s; } catch (e) {}
    return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
  });
  React.useEffect(() => { try { localStorage.setItem('baltor-theme', theme); } catch (e) {} }, [theme]);
  const toggle = React.useCallback(() => setTheme((t) => (t === 'dark' ? 'light' : 'dark')), []);
  return [theme, toggle];
}

const CEStore = React.createContext(null);

// ---------- helpers ----------
const TIER_META = {
  raw:         { label: 'Raw',             glyph: '▣', tone: 'color-mix(in srgb, var(--accent) 50%, var(--panel))',  blurb: 'full fidelity · every token + source spans' },
  compressed:  { label: 'Compressed',      glyph: '◧', tone: 'color-mix(in srgb, var(--accent) 74%, var(--panel))',  blurb: 'deduped & normalized · near-full fidelity' },
  hyper:       { label: 'Hyper-efficient', glyph: '◆', tone: 'var(--accent)',                                        blurb: 'claim-level · citation-anchored · token-minimal' },
};
const STATUS_META = {
  verified: { label: 'Verified',  cls: 'oh-badge--verified', gl: '✔' },
  governed: { label: 'Governed',  cls: 'oh-badge--verified', gl: '⛨' },
  syncing:  { label: 'Syncing',   cls: 'oh-badge--warn',     gl: '↻' },
  draft:    { label: 'Draft',     cls: 'oh-badge--muted',    gl: '◌' },
};

// relative-size fill % used by meters (raw is the 100% baseline)
const tierFill = { raw: 100, compressed: 34, hyper: 8 };

// ---------- mock corpora ----------
const CORPORA = [
  {
    id: 'acme-policy', name: 'Acme Compliance Policies', status: 'verified', modality: 'text',
    desc: 'Every internal policy, SOP and control narrative — the source of truth agents cite when answering compliance questions.',
    sources: [['Confluence wiki', 142], ['Policy PDFs', 38], ['Control register (CSV)', 1]],
    tiers: { raw: { size: '1.24 GB', tokens: '312M' }, compressed: { size: '418 MB', tokens: '104M' }, hyper: { size: '96 MB', tokens: '7.1M' } },
    freshness: 'synced 2h ago', cadence: 'every 6h', queriesPerDay: 4120, citations: true, langs: 1,
    owner: 'Risk & Compliance', created: 'Mar 2026',
  },
  {
    id: 'eu-reg', name: 'EU Regulatory Corpus', status: 'governed', modality: 'text',
    desc: 'CSDDD, EUDR and member-state transpositions across 13 languages, with article-level anchoring for exact citation.',
    sources: [['EUR-Lex statutes', 38], ['National transpositions', 211], ['Guidance notes', 64]],
    tiers: { raw: { size: '883 MB', tokens: '221M' }, compressed: { size: '301 MB', tokens: '74M' }, hyper: { size: '64 MB', tokens: '4.8M' } },
    freshness: 'synced 1d ago', cadence: 'weekly', queriesPerDay: 1870, citations: true, langs: 13,
    owner: 'Legal', created: 'Jan 2026',
  },
  {
    id: 'product-docs', name: 'Product Docs & Changelog', status: 'verified', modality: 'text',
    desc: 'Live docs site plus the GitHub changelog — kept fresh so support agents never cite a stale version.',
    sources: [['Docs site (crawl)', 612], ['GitHub releases', 340], ['API reference', 1]],
    tiers: { raw: { size: '221 MB', tokens: '55M' }, compressed: { size: '71 MB', tokens: '17M' }, hyper: { size: '12 MB', tokens: '910K' } },
    freshness: 'live · webhook', cadence: 'on push', queriesPerDay: 9240, citations: true, langs: 1,
    owner: 'DevRel', created: 'Feb 2026',
  },
  {
    id: 'support-kb', name: 'Support Knowledge Base', status: 'syncing', modality: 'text',
    desc: 'Resolved tickets, macros and the internal Slack help channels — distilled into reusable, cited answers.',
    sources: [['Zendesk tickets', 18400], ['Help macros', 320], ['Slack #help', 4]],
    tiers: { raw: { size: '540 MB', tokens: '135M' }, compressed: { size: '182 MB', tokens: '45M' }, hyper: { size: '38 MB', tokens: '2.9M' } },
    freshness: 'syncing… 71%', cadence: 'every 12h', queriesPerDay: 6010, citations: true, langs: 4,
    owner: 'Support Ops', created: 'Apr 2026',
  },
  {
    id: 'research-lib', name: 'Research Library', status: 'verified', modality: 'text',
    desc: 'Curated external papers plus internal research memos, with claim-level extraction for grounded literature review.',
    sources: [['arXiv (filtered)', 2100], ['Internal memos', 480], ['Datasets', 36]],
    tiers: { raw: { size: '2.10 GB', tokens: '525M' }, compressed: { size: '760 MB', tokens: '190M' }, hyper: { size: '140 MB', tokens: '10.5M' } },
    freshness: 'synced 5h ago', cadence: 'daily', queriesPerDay: 980, citations: true, langs: 2,
    owner: 'Research', created: 'Dec 2025',
  },
  {
    id: 'contracts', name: 'Master Contracts', status: 'governed', modality: 'text',
    desc: 'Executed agreements from the DMS — access-gated, with clause-level spans for renewal-risk and obligation lookups.',
    sources: [['DMS export', 3400], ['Amendments', 1220]],
    tiers: { raw: { size: '1.61 GB', tokens: '402M' }, compressed: { size: '523 MB', tokens: '130M' }, hyper: { size: '88 MB', tokens: '6.6M' } },
    freshness: 'synced 3d ago', cadence: 'manual', queriesPerDay: 410, citations: true, langs: 1,
    owner: 'Legal Ops', created: 'Nov 2025', private: true,
  },
];
const CORPUS_BY_ID = Object.fromEntries(CORPORA.map((c) => [c.id, c]));

// rollups for the dashboard header
const ROLLUP = {
  corpora: CORPORA.length,
  served: CORPORA.reduce((n, c) => n + c.queriesPerDay, 0),
  sources: CORPORA.reduce((n, c) => n + c.sources.reduce((m, s) => m + s[1], 0), 0),
};

// ---------- verification / reconciliation (the moat) ----------
// Internal corpus claims checked adversarially against live authoritative sources.
const SEV_META = {
  high: { label: 'High', cls: 'oh-badge--danger', tone: 'var(--danger)' },
  med:  { label: 'Medium', cls: 'oh-badge--warn', tone: 'var(--warning)' },
  low:  { label: 'Low', cls: 'oh-badge--muted', tone: 'var(--fg-faint)' },
};
const CONFLICT_TYPE = {
  superseded:   'Superseded',
  contradicted: 'Contradicted',
  stale:        'Stale',
  integrity:    'Integrity',
};
const CONFLICTS = [
  {
    id: 'cf-1', corpusId: 'eu-reg', corpus: 'EU Regulatory Corpus', type: 'superseded', severity: 'high',
    claim: 'EUDR obligations for large operators apply from 30 December 2024.',
    internal: '30 December 2024', external: '30 December 2025',
    source: 'EUR-Lex · Regulation (EU) 2023/1115 (amended)', sourceRef: 'Art. 38 · amendment 2024/3234',
    detected: '4h ago', confidence: 0.97, status: 'open',
    note: 'Application date was deferred by 12 months in a December 2024 amendment. 1 corpus claim and 3 hyper-tier chunks reference the old date.',
  },
  {
    id: 'cf-2', corpusId: 'eu-reg', corpus: 'EU Regulatory Corpus', type: 'contradicted', severity: 'high',
    claim: 'CSDDD applies to companies with 1,000+ employees and €450M+ net turnover.',
    internal: '1,000 employees / €450M', external: 'thresholds under revision (Omnibus)',
    source: 'European Commission · Omnibus simplification package', sourceRef: 'COM(2025) proposal',
    detected: '1d ago', confidence: 0.82, status: 'open',
    note: 'An external proposal would change the scoping thresholds. Flagged for human review — not yet enacted.',
  },
  {
    id: 'cf-3', corpusId: 'acme-policy', corpus: 'Acme Compliance Policies', type: 'stale', severity: 'med',
    claim: 'Vendors handling regulated data require a Tier-2 security review.',
    internal: 'Tier-2 review', external: 'Tier-1 review (regulated data)',
    source: 'Internal · Security Policy memo 2026-04', sourceRef: 'memo §4.2-r',
    detected: '2d ago', confidence: 0.9, status: 'escalated',
    note: 'A newer internal memo raised the bar to Tier-1 for regulated data; the corpus still serves the old tier.',
  },
  {
    id: 'cf-4', corpusId: 'contracts', corpus: 'Master Contracts', type: 'contradicted', severity: 'med',
    claim: 'Auto-renewal contracts require 60 days’ notice before term end.',
    internal: '60 days', external: '90 days',
    source: 'Legal · Master template v9', sourceRef: 'template §7.1',
    detected: '3d ago', confidence: 0.94, status: 'open',
    note: 'The current master template specifies 90 days. Two clause spans in the hyper tier disagree.',
  },
  {
    id: 'cf-5', corpusId: 'product-docs', corpus: 'Product Docs & Changelog', type: 'stale', severity: 'low',
    claim: 'Default API rate limit is 1,000 requests / minute.',
    internal: '1,000 / min', external: '5,000 / min',
    source: 'GitHub · changelog v4.2', sourceRef: 'release v4.2.0',
    detected: '6h ago', confidence: 0.99, status: 'auto',
    note: 'Auto-reconciled from the live changelog; the compressed & hyper tiers were re-anchored.',
  },
  {
    id: 'cf-6', corpusId: 'acme-policy', corpus: 'Acme Compliance Policies', type: 'integrity', severity: 'high',
    claim: 'An internal memo states the CSDDD employee threshold was raised to 5,000.',
    internal: 'unsigned memo · “threshold = 5,000”', external: 'no corroborating oracle source',
    source: 'Integrity check · not signed by any oracle publisher', sourceRef: 'no C2PA manifest',
    detected: '38m ago', confidence: 0.88, status: 'escalated',
    note: 'A document appears to supersede a real rule but carries no authoritative signature — a classic corpus-poisoning pattern (cf. BadRAG / TrojanRAG). Quarantined from serving pending human review.',
  },
];
const VERIFY_ROLLUP = {
  open: CONFLICTS.filter((c) => c.status === 'open').length,
  escalated: CONFLICTS.filter((c) => c.status === 'escalated').length,
  autoReconciled: 128,
  sourcesWatched: 42,
};
// live authoritative sources we watch for change
const WATCHED = [
  ['EUR-Lex', 'EU legislation & amendments', 'change 4h ago'],
  ['US Federal Register', 'rules & notices', 'synced 2h ago'],
  ['ISO / IEC catalogue', 'standard supersessions', 'synced 1d ago'],
  ['Internal policy registry', 'memos & SOPs', 'live · webhook'],
  ['GitHub releases', 'product changelogs', 'live · webhook'],
];

// ---------- oracle-published corpus commons (the category whitespace) ----------
// A shared, signed, continuously-verified library — what Contextual's private
// per-tenant stores and the hyperscaler marketplaces don't offer for these domains.
const PUBLISHERS = {
  ilo:   { name: 'International Labour Organization', short: 'ILO', kind: 'UN agency' },
  dol:   { name: 'US Department of Labor', short: 'US DOL', kind: 'Government' },
  fatf:  { name: 'Financial Action Task Force', short: 'FATF', kind: 'Intergov. body' },
  ec:    { name: 'European Commission', short: 'EC', kind: 'Government' },
  codex: { name: 'Codex Alimentarius · FAO/WHO', short: 'Codex', kind: 'Standards body' },
  wco:   { name: 'World Customs Organization', short: 'WCO', kind: 'Intergov. body' },
  ofac:  { name: 'US Treasury · OFAC', short: 'OFAC', kind: 'Government' },
  oecd:  { name: 'OECD', short: 'OECD', kind: 'Intergov. body' },
  nist:  { name: 'NIST', short: 'NIST', kind: 'Standards body' },
};
const COMMONS_DOMAINS = ['Sanctions & export controls', 'AML / CFT', 'Tax & transfer pricing', 'Cyber / GRC', 'EU regulation'];
// Baltor's OWN dedicated, continuously-verified corpora (the paid assurance product).
// Open / public-good packs (ILO, migrant-worker, Codex, WCO …) live on OpenContextHub.
const COMMONS = [
  { id: 'ofac-sanctions', name: 'OFAC, BIS & EU Sanctions Lists', publisher: 'ofac', domain: 'Sanctions & export controls', flagship: true,
    desc: 'Consolidated SDN, BIS Entity List and the EU consolidated list — the wedge at its sharpest: lists change several times a week and being a day stale is a federal violation, not an embarrassment.',
    hash: '1a0f…d7b2', cadence: 'several times / week', lastVerified: 'verified 40m ago', subscribers: 3120, size: '72 MB' },
  { id: 'ec-flr-csddd', name: 'EU Forced Labour Regulation + CSDDD', publisher: 'ec', domain: 'EU regulation',
    desc: 'Consolidated FLR (enforcement Dec 2027), CSDDD and the Omnibus track — reconciled with LkSG & EUDR so overlapping duties resolve to one requirement set.',
    hash: 'c4a8…7f12', cadence: 'on amendment', lastVerified: 'verified 4h ago', subscribers: 2110, size: '301 MB' },
  { id: 'fatf-40', name: 'FATF 40 Recommendations', publisher: 'fatf', domain: 'AML / CFT',
    desc: 'The global AML/CFT standard — CDD, monitoring, SAR and record-keeping — with interpretive notes anchored at the recommendation level.',
    hash: '08de…b6a3', cadence: 'on plenary', lastVerified: 'verified 1w ago', subscribers: 1640, size: '64 MB' },
  { id: 'oecd-beps', name: 'OECD BEPS + Treaty Network', publisher: 'oecd', domain: 'Tax & transfer pricing',
    desc: 'BEPS actions, transfer-pricing guidelines and the treaty network — reconciled across jurisdictions so conflicting duties resolve to one answer.',
    hash: 'b53e…02af', cadence: 'on release', lastVerified: 'verified 1w ago', subscribers: 520, size: '186 MB' },
  { id: 'nist-controls', name: 'NIST 800-53 / CSF + ISO 27001 crosswalk', publisher: 'nist', domain: 'Cyber / GRC',
    desc: 'Control catalogs with a verified crosswalk between frameworks — the painful cross-mapping done once and kept current.',
    hash: 'e9c1…44da', cadence: 'on revision', lastVerified: 'verified 3d ago', subscribers: 1340, size: '58 MB' },
];
// continuous regulatory-change feed (the "diff" that flags stale internal context)
const REG_CHANGES = [
  { authority: 'EUR-Lex', change: 'EUDR application date deferred 12 months → 30 Dec 2025', when: '4h ago', affects: 'EU Regulatory Corpus', sev: 'high' },
  { authority: 'FATF', change: 'Recommendation 16 (travel rule) interpretive note revised', when: '2d ago', affects: 'FATF 40 Recommendations', sev: 'med' },
  { authority: 'European Commission', change: 'Omnibus package proposes CSDDD threshold changes (not enacted)', when: '1d ago', affects: 'EU Forced Labour Regulation + CSDDD', sev: 'med' },
  { authority: 'ILO', change: 'Updated guidance on forced-labour indicator measurement', when: '6d ago', affects: 'ILO Forced Labour Standards', sev: 'low' },
];
// compliance artifacts a corpus can emit (the regulator-facing deliverable)
const ARTIFACTS = [
  ['AIBOM · CycloneDX', 'aibom.cdx.json', 'Machine-readable bill of materials for every source, tier and signature in the corpus.'],
  ['EU AI Act dossier', 'eu-ai-act.pdf', 'Article 10 data-governance + Article 50 transparency documentation, pre-filled.'],
  ['C2PA provenance manifest', 'manifest.c2pa', 'Signed origin chain — who published each source, when, and the verifying signature.'],
  ['Measured-fidelity record', 'fidelity.json', 'Groundedness & freshness scores with the verification log behind them.'],
];

Object.assign(window, {
  useHashRoute, navigate, CEStore, BRANDCE,
  useFlag, setFlag, useTheme,
  TIER_META, STATUS_META, tierFill, CORPORA, CORPUS_BY_ID, ROLLUP,
  SEV_META, CONFLICT_TYPE, CONFLICTS, VERIFY_ROLLUP, WATCHED,
  PUBLISHERS, COMMONS_DOMAINS, COMMONS, REG_CHANGES, ARTIFACTS,
});
