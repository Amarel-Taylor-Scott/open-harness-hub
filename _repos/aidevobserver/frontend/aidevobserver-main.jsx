/* global React, ReactDOM, PORTFOLIO,
   useHashRoute, navigate, useSiteTheme,
   OhTopBar, OhHero, OhSection, OhFeatures, OhBand, OhFooter,
   OhLayout, OhAppShell, OhTable, OhPageHead, OhRollup, OhThemeToggle,
   OhAuth, OhDashboard, OhUsage, OhTeam, OhBilling, OhApiKeys,
   OhNotifications, OhSettings, OhSwitch, OhStatus, OhNotFound, OhCommandK */
// AIDevObserver: review how your team uses AI coding agents.
// ONE self-contained app on the shared site kit (kit/oh-site.*), like every sibling
// surface. AIDevObserver uses clean history routes (/ide) while preserving old #/ links.
// It differs ONLY by accent (#b25fd6) + copy. Two layers:
//   - marketing (/, on-page sections) — OhTopBar / OhHero / OhSection / OhFooter
//   - the logged-in app (top-level routes: /dashboard /review /sessions /findings /agentic /reports
//     /notifications /members /billing /developer /account /settings /help) — the OhAppShell left
//     sidebar, every screen opening with OhPageHead, talking to the REAL observer backend over the
//     same-origin /api/observer/* seam (scripts/observer_local_service.py).
// serves_truth=false; read-only against code/transcripts; optional triage writes metadata only. BYO keys are never stored or logged.

const ADO = PORTFOLIO.ENTITIES.aidevobserver;
const BRAND = { name: 'AIDevObserver', glyph: ADO.glyph, accent: ADO.accent };
const ACCENT = ADO.accent;

const ROUTES = {
  home: '/',
  how: '/how',
  setup: '/runs',
  examples: '/examples',
  ide: '/ide',
  review: '/review',
  trust: '/trust',
  demo: '/demo',
  dashboard: '/dashboard',
  sessions: '/sessions',
  findings: '/findings',
  agentic: '/agentic',
  intelligence: '/intelligence',
  reports: '/reports',
  notifications: '/notifications',
  members: '/members',
  billing: '/billing',
  developer: '/developer',
  account: '/account',
  settings: '/settings',
  help: '/help',
};
window.OH_ROUTE_MAP = ROUTES;

const ADO_ROUTE_EVENT = 'aidevobserver-route';
function adoRouteFromLocation() {
  const hash = window.location.hash || '';
  if (hash.startsWith('#/')) return hash.slice(1) || '/';
  const path = (window.location.pathname || '/').replace(/\/index\.html$/, '/') || '/';
  return path || '/';
}
function useAdoRoute() {
  const [route, setRoute] = React.useState(adoRouteFromLocation);
  React.useEffect(() => {
    if ((window.location.hash || '').startsWith('#/')) {
      window.history.replaceState({}, '', window.location.hash.slice(1) || '/');
    }
    const on = () => setRoute(adoRouteFromLocation());
    window.addEventListener('hashchange', on);
    window.addEventListener('popstate', on);
    window.addEventListener(ADO_ROUTE_EVENT, on);
    return () => {
      window.removeEventListener('hashchange', on);
      window.removeEventListener('popstate', on);
      window.removeEventListener(ADO_ROUTE_EVENT, on);
    };
  }, []);
  return route;
}
function navigate(to) {
  const raw = String(to || '/');
  const target = raw.startsWith('/#/') ? raw.slice(2) : raw.startsWith('#/') ? raw.slice(1) : raw;
  if (/^[a-z][a-z0-9+.-]*:/i.test(target) || target.startsWith('../')) {
    window.location.href = target;
    return;
  }
  window.history.pushState({}, '', target);
  window.dispatchEvent(new Event(ADO_ROUTE_EVENT));
}
const routePairs = (routes) => routes.map((r) => [r.label, r.href]);
const PRODUCT_ROUTES = [
  { label: 'How it works', href: ROUTES.how },
  { label: 'Setup', href: ROUTES.setup },
  { label: 'Examples', href: ROUTES.examples },
  { label: 'IDE', href: ROUTES.ide },
  { label: 'Review', href: ROUTES.review },
  { label: 'Trust', href: ROUTES.trust },
  { label: 'Demo', href: ROUTES.demo, strong: true },
];
const MKT_NAV = PRODUCT_ROUTES;
const HOME_ROUTES = [
  { label: 'Review a session', desc: 'Paste/upload or choose a replay and get ranked reuse findings.', href: ROUTES.review },
  { label: 'Open the IDE', desc: 'Run a browser coding session with GLM/Kimi lanes and observer toggles.', href: ROUTES.ide },
  { label: 'Choose setup path', desc: 'Install in VS Code, Cursor, Claude Code, CLI, hooks, or manual upload.', href: ROUTES.setup },
  { label: 'Explore examples', desc: 'Replay web scraper, document extraction, enrichment, and migration sessions.', href: ROUTES.examples },
];
const INSTALL_FOOTER_ROUTES = [
  { label: 'VS Code', href: ROUTES.setup },
  { label: 'Cursor', href: ROUTES.setup },
  { label: 'Claude Code (MCP)', href: ROUTES.setup },
  { label: 'Command line', href: ROUTES.setup },
];

// ---- how it works: a session becomes a ranked report ----
const HOW = [
  ['◉', 'Every session becomes a report',
    'AIDevObserver captures the agent session and turns it into a short, ranked report you can read in under a minute.'],
  ['⚑', 'It flags what actually costs you',
    'Reinvention, duplicate context, avoidable model loops, and cheaper registry-backed paths the agent missed.'],
  ['↑', 'Ranked by confidence',
    'High-confidence findings rise to the top and low-signal noise drops away, so the report stays worth reading every time.'],
  ['◑', 'Report after, prompts during',
    'You get a full report after the session, plus optional in-session prompts the moment something looks off.'],
];

// ---- where it runs: same review, every surface ----
const SETUP_PATHS = [
  {
    icon: '❮❯',
    title: 'VS Code extension',
    surface: 'Editor extension',
    desc: 'Install the extension, connect a workspace, and review the agent session from the editor report panel.',
    steps: ['Install from Extensions', 'Connect workspace', 'Open the report panel'],
    action: 'Open Extensions -> search AIDevObserver',
  },
  {
    icon: '➤',
    title: 'Cursor extension',
    surface: 'Editor extension',
    desc: 'Use the same review flow inside Cursor, so agent transcripts and findings stay next to the work.',
    steps: ['Install from Extensions', 'Connect workspace', 'Review the active session'],
    action: 'Open Extensions -> search AIDevObserver',
  },
  {
    icon: '⌁',
    title: 'Claude Code MCP server',
    surface: 'Agent integration',
    desc: 'Add one MCP server so Claude Code can hand the session to AIDevObserver and receive the ranked report inline.',
    steps: ['Add the MCP server', 'Run a Claude Code session', 'Read the review inline'],
    command: 'claude mcp add aidevobserver -- python3 scripts/aidevobserver_mcp_server.py',
  },
  {
    icon: '❯_',
    title: 'Command line',
    surface: 'Terminal / CI',
    desc: 'Run the same review from a terminal, CI job, or scripted workflow and return plain text or JSON findings.',
    steps: ['Run latest-session review', 'Inspect ranked findings', 'Export JSON when needed'],
    command: 'python3 -m src.teleon.observer.cli review --latest',
  },
  {
    icon: '⤓',
    title: 'Manual upload / paste',
    surface: 'No install',
    desc: 'Paste a transcript or upload .jsonl, .json, .txt, .md, or .log files and get the same read-only review.',
    steps: ['Paste or upload', 'Choose a replay if needed', 'Review ranked findings'],
    action: 'Use the Review page',
  },
  {
    icon: '◑',
    title: 'Live in-session hook',
    surface: 'Non-blocking coach',
    desc: 'Install a Claude Code PreToolUse hook for read-only coaching when a step looks like waste or a cheaper registry route.',
    steps: ['Install the hook', 'Keep it advisory', 'Triage prompts inline'],
    command: 'python3 scripts/aidevobserver_hook.py --install',
  },
  {
    icon: '◎',
    title: 'Zero-install discovery',
    surface: 'Local session picker',
    desc: 'When local discovery is enabled, AIDevObserver finds Claude Code and Codex sessions and lets you review one without setup.',
    steps: ['Open Sessions', 'Pick a transcript', 'Run review'],
    action: 'Open Sessions in the app or CLI',
  },
];
const INSTALL_LINES = SETUP_PATHS.filter((p) => p.command).map((p) => [p.title, p.command]);

// the /api/observer/* endpoints the Developer screen documents (real, served by observer_local_service.py)
const API_ENDPOINTS = [
  ['POST', '/api/observer/review', 'Review a session. Body { messages:[…] } or { transcript_path }. Optional registry_cwd enriches findings in installed/local mode.'],
  ['GET', '/api/observer/sessions', 'Discover local Claude Code / Codex sessions when local discovery is enabled. Public demos hide local paths.'],
  ['POST', '/api/observer/live', 'Intra-session check. The interruption budget caps would_interrupt.'],
  ['POST', '/api/observer/agentic', 'Supervise an autonomous agent loop. Returns a verdict + loop-shape findings.'],
  ['POST', '/api/observer/outcome', 'Append Accept / Reuse / Dismiss metadata for one finding. Stores no transcript text.'],
  ['GET', '/api/observer/outcomes', 'Read latest outcome metadata for a reviewed session.'],
  ['GET', '/api/observer/registry/search', 'Opt-in local helper/docs/script source-ref search. Public demos return no local hits.'],
  ['GET/POST', '/api/observer/config', 'Read or update the local intelligence deck: model lane, MCP/plugin hooks, registry layers, token savings, and rerank toggles.'],
  ['POST', '/api/observer/ide/run', 'Execute a browser-IDE task. Deterministic routes compile first; coding harnesses receive compact context only as fallback.'],
  ['POST', '/api/observer/ide/session', 'Save or update a browser IDE session and return a unique /ide/<session_id> URL.'],
  ['GET', '/api/observer/ide/session/<id>', 'Reopen one saved browser IDE session from its share URL.'],
  ['GET', '/api/observer/ide/sessions', 'List recent saved browser IDE sessions for the local workspace.'],
];

// ---- a worked example review (the live demo's preview output), ranked by confidence ----
const SESSION_EXAMPLE = [
  'user: add a CSV import to the importer',
  "agent: I'll write a CSV parser. Creating parse_csv() in importer.py",
  'agent: pasting the full schema for reference (1,800 lines)',
  'agent: writing a custom retry/backoff helper for the importer',
  'user: also find where MAX_ROWS is defined',
  'agent: scanning all 50 files in src/ with the model',
].join('\n');

const ADO_EXAMPLE_ROOT = 'examples/';
const ADO_EXAMPLE_SESSION_TEXT_KEY = 'aidevobserver.exampleSessionText';
const ADO_EXAMPLE_SESSION_LABEL_KEY = 'aidevobserver.exampleSessionLabel';
const ADO_EXAMPLE_SESSION_AUTORUN_KEY = 'aidevobserver.exampleSessionAutorun';
const SESSION_REPLAY_EXAMPLES = [
  {
    id: 'web-scraper-regulatory-rates',
    title: 'Web scraper for regulatory rates',
    type: 'Data collection',
    domain: 'software · web scraping',
    path: 'intent -> CandidateBundle -> map remix -> PlanLock -> ledger',
    note: 'Shows scraper work becoming a typed scrape/validate/emit graph instead of custom one-off code.',
  },
  {
    id: 'company-entity-enrichment',
    title: 'Company/entity enrichment',
    type: 'Entity intelligence',
    domain: 'sales · data operations',
    path: 'names -> resolve -> enrich -> crosscheck -> confidence -> artifact',
    note: 'Exercises batch remixes, TTL cache policy, provenance gates, and confidence records.',
  },
  {
    id: 'document-json-schema-extraction',
    title: 'Document to JSON schema extraction',
    type: 'Document AI',
    domain: 'finance · extraction',
    path: 'document artifact -> bounded extractor -> schema/span gates -> JSON artifact',
    note: 'Keeps model extraction bounded by schema contracts, source spans, artifact refs, and proof.',
  },
  {
    id: 'support-ticket-classification',
    title: 'Support ticket classification',
    type: 'Classification',
    domain: 'customer support',
    path: 'ticket -> bounded label classifier -> validation gate -> route packet',
    note: 'Contrasts free-form labels with a validated label schema and deterministic routing policy.',
  },
  {
    id: 'revenue-regression-pipeline',
    title: 'Revenue regression pipeline',
    type: 'Regression',
    domain: 'data science',
    path: 'dataset -> leakage gate -> features -> train -> evaluate -> register',
    note: 'Demonstrates ML workflow contracts, artifact storage, deterministic split, and metric gates.',
  },
  {
    id: 'kaggle-tabular-baseline',
    title: 'Kaggle tabular baseline',
    type: 'Competition baseline',
    domain: 'data science · tabular',
    path: 'inspect -> split -> impute -> encode -> train -> evaluate -> submit',
    note: 'Synthetic public-project-derived replay for common Kaggle-style workflows and reusable ML primitives.',
  },
  {
    id: 'kaggle-image-classification-baseline',
    title: 'Kaggle image classification baseline',
    type: 'Competition baseline',
    domain: 'data science · vision',
    path: 'manifest -> label gate -> preprocess -> augment -> train -> evaluate -> submit',
    note: 'Shows image competition work routed through artifact-backed datasets, label gates, and metric proofs.',
  },
  {
    id: 'kaggle-text-classification-baseline',
    title: 'Kaggle text classification baseline',
    type: 'Competition baseline',
    domain: 'data science · NLP',
    path: 'schema -> label gate -> normalize -> vectorize -> train -> macro-F1 -> submit',
    note: 'Catches repeated text-classification boilerplate and routes it to reusable seeded ML primitives.',
  },
  {
    id: 'safe-pyprefix-migration',
    title: 'Safe pyprefix migration',
    type: 'Software engineering',
    domain: 'refactor · proof',
    path: 'audit -> opgraph -> conservative migration -> contract report -> proof',
    note: 'Shows the AIDevObserver benchmark lab using deterministic AST evidence and proof gates before promotion.',
  },
  {
    id: 'workflow-replay-debugger',
    title: 'Workflow replay debugger',
    type: 'Devtools',
    domain: 'ledger replay',
    path: 'ledger + PlanLock -> reconstruct -> diff -> failure class -> report',
    note: 'Makes observed runtime truth debuggable without asking a model to read arbitrary logs.',
  },
  {
    id: 'n8n-workflow-distillation',
    title: 'n8n workflow distillation',
    type: 'Workflow registry',
    domain: 'automation',
    path: 'n8n JSON -> redact -> node graph -> candidate primitives -> PlanLock',
    note: 'Turns easy-to-scrape workflow JSON into redacted candidate graph evidence, not truth.',
  },
  {
    id: 'frontend-component-quality-gate',
    title: 'Frontend component quality gate',
    type: 'Frontend',
    domain: 'software · UI',
    path: 'tsx -> typecheck -> design tokens -> a11y -> snapshot -> report',
    note: 'Shows generated UI work routed to reusable quality gates instead of one-off manual review.',
  },
  {
    id: 'backend-policy-api',
    title: 'Backend policy API',
    type: 'Backend',
    domain: 'software · API',
    path: 'request -> validate -> fetch state -> decide -> persist -> respond',
    note: 'Demonstrates API workflow reuse, idempotency, and deterministic policy decisions.',
  },
  {
    id: 'data-engineering-csv-ingestion',
    title: 'Data engineering CSV ingestion',
    type: 'Data engineering',
    domain: 'data · ETL',
    path: 'csv -> schema gate -> normalize -> parquet artifact -> catalog receipt',
    note: 'Turns common ingestion scripts into a schema/artifact/catalog template route.',
  },
  {
    id: 'rag-docs-search-app',
    title: 'RAG docs search app',
    type: 'Retrieval',
    domain: 'AI app · docs',
    path: 'docs -> chunk -> embed -> retrieve -> cite -> eval',
    note: 'Shows how a common docs chatbot request maps to retrieval primitives and citation gates.',
  },
  {
    id: 'ci-workflow-generation',
    title: 'CI workflow generation',
    type: 'DevOps',
    domain: 'automation · CI',
    path: 'repo -> existing workflow search -> job template -> proof -> receipt',
    note: 'Catches agents rebuilding CI jobs that already exist in workflow registries.',
  },
  {
    id: 'bugfix-repeated-test-loop',
    title: 'Bugfix repeated test loop',
    type: 'Debugging',
    domain: 'software · bugfix',
    path: 'failure -> localize -> search known fix -> patch -> proof',
    note: 'Highlights repeated test thrash and routes the agent toward an existing fix pattern.',
  },
];
function exampleHref(item, ext) { return ADO_EXAMPLE_ROOT + item.id + '.' + ext; }
function storeExampleForReview(text, label, autorun) {
  try {
    sessionStorage.setItem(ADO_EXAMPLE_SESSION_TEXT_KEY, text);
    sessionStorage.setItem(ADO_EXAMPLE_SESSION_LABEL_KEY, label);
    if (autorun) sessionStorage.setItem(ADO_EXAMPLE_SESSION_AUTORUN_KEY, '1');
    else sessionStorage.removeItem(ADO_EXAMPLE_SESSION_AUTORUN_KEY);
  } catch (e) { /* sessionStorage unavailable; the review screen still has the built-in example */ }
  navigate(ROUTES.review);
}
async function openSessionReplay(item, autorun) {
  let text = '';
  try {
    const res = await fetch(exampleHref(item, 'txt'), { cache: 'no-store' });
    if (!res.ok) throw new Error('example status ' + res.status);
    text = await res.text();
  } catch (e) {
    text = [
      'user: ' + item.title,
      'assistant: Example transcript could not be loaded from the static pack.',
      'assistant: The intended route is ' + item.path + '.',
    ].join('\n');
  }
  storeExampleForReview(text, item.title, autorun);
}

// the worked-example findings (preview fallback). Each carries the full finding-card shape:
// family-toned type, confidence, message, suggestion, evidence, a source_ref, optional reuse savings.
const FINDINGS = [
  { type: 'reinvention', label: 'Reinvented component', conf: 0.97,
    message: 'A new CSV parser was written from scratch.',
    suggestion: 'Reuse utils/csv.py, which already exports read_rows() with the same behavior.',
    evidence: 'def parse_csv(path): ...  # new, ~40 lines',
    source: { kind: 'existing', registry: 'stack_components', name: 'utils.csv.read_rows' },
    savings: { dollars: 0, hours: 1.5 } },
  { type: 'oversized_context', label: 'Wasted context', conf: 0.93,
    message: 'The full 1,800-line schema was pasted into the prompt when about 40 lines were referenced.',
    suggestion: 'Trim to the tables in use; oversized context costs tokens and dilutes attention.',
    evidence: '# schema.sql (1,800 lines pasted)' },
  { type: 'alternative', label: 'Missed cheaper path', conf: 0.88,
    message: 'A large model looped over 50 files to find one constant.',
    suggestion: 'A single project search answers it in one step at a fraction of the cost.',
    evidence: 'scanning all 50 files in src/ with the model',
    savings: { dollars: 0.4, hours: 0 } },
  { type: 'reinvention', label: 'Duplicate helper', conf: 0.82,
    message: 'The agent started a custom retry/backoff helper.',
    suggestion: 'Use the existing network retry primitive instead of spending a loop on another helper.',
    evidence: 'writing a custom retry/backoff helper',
    source: { kind: 'existing', registry: 'stack_components', name: 'utils.net.retry_with_backoff' },
    savings: { dollars: 0, hours: 0.75 } },
];

// ---- trust: suggestions a human triages, read-only, nothing stored ----
const TRUST = [
  ['Suggestions, not gates', 'Every finding is a suggestion a person reviews and triages. AIDevObserver never blocks a commit, a push, or a merge.'],
  ['Read-only by design', 'It reads the session to write the report. It does not change your code, your branches, or your history.'],
  ['Nothing is stored', 'Reviews run locally and are not retained. When you close the session, the report is yours to keep or discard.'],
];

// compiled-AI-style examples: model proposes candidate intent; deterministic code validates, locks, and records.
const COMPILED_AI_EXAMPLES = [
  {
    title: 'Session review',
    type: 'AIDevObserver',
    path: 'transcript -> review_session -> ranked findings -> human triage',
    note: 'Flags reinvention, wasted context, duplicate helpers, and cheaper paths without changing code.',
    route: ROUTES.review,
  },
  {
    title: 'Document intelligence',
    type: 'Compiled AI',
    path: 'invoice -> typed extractor -> validation gates -> deterministic output packet',
    note: 'A narrow generated/selected extractor runs behind proof and provenance instead of repeated runtime prompting.',
    route: ROUTES.reports,
  },
  {
    title: 'Media pipeline',
    type: 'Teleon Media',
    path: 'image -> scene plan -> image-to-video model -> ffmpeg encode -> quality gate',
    note: 'Media components are registry primitives with artifact refs, model routes, safety gates, and locked parameters.',
    route: ROUTES.developer,
  },
  {
    title: 'n8n workflow distillation',
    type: 'Workflow registry',
    path: 'n8n JSON -> redacted node graph -> CandidateBundle -> PlanLock or gap report',
    note: 'External workflow JSON becomes candidate graph evidence, not executable truth.',
    route: ROUTES.developer,
  },
];

/* ===================== the finding card (the core component) ===================== */
// the observer engine's finding types → display label + the family that tones the card
const FINDING_LABELS = {
  reinvention: 'Reinvention', stack_reinvention: 'Reinvention', product_reinvention: 'Reinvention',
  reinvention_cluster: 'Reinvention', footgun: 'Safety signal', oversized_context: 'Wasted context',
  duplicate_context: 'Wasted context', adversarial: 'Question the assumption', shortcut: 'Repeated action',
  guidance: 'Convention', alternative: 'Missed cheaper path', agentic_loop: 'Loop / thrash',
  agentic_repeated_failure: 'Repeated failure', agentic_stall: 'Stall', agentic_budget: 'Budget overrun',
  agentic_goal_drift: 'Goal drift',
};
// family → card tone: reinvention = accent, waste = amber, safety = red (redacted evidence), else neutral
function findingFamily(type) {
  const t = String(type || '');
  if (t.indexOf('reinvention') !== -1) return 'reinvention';
  if (t === 'oversized_context' || t === 'duplicate_context') return 'waste';
  if (t === 'footgun') return 'footgun';
  if (t.indexOf('agentic') !== -1) return 'agentic';
  return 'neutral';
}
function sourceFromRef(sr) {
  if (!sr) return null;
  if (sr.registry && sr.name) return { kind: 'existing', registry: sr.registry, name: sr.name, path: sr.path || '', line: sr.line || null };
  if (sr.existing) {
    if (Array.isArray(sr.existing.local_repo) && sr.existing.local_repo.length) {
      const hit = sr.existing.local_repo[0];
      return { kind: 'existing', registry: hit.registry || 'local_repo', name: hit.name || hit.path || 'local repo object', path: hit.path || '', line: hit.line || null };
    }
    if (sr.existing.registry || sr.existing.name) return { kind: 'existing', registry: sr.existing.registry, name: sr.existing.name };
  }
  if (sr.covering || sr.package) return { kind: 'covering', package: sr.package || (sr.covering && sr.covering.package), provides: sr.provides || (sr.covering && sr.covering.provides) };
  return null;
}
function compactEdgeText(value, fallback) {
  if (value == null || value === '') return fallback;
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) return value.map((item) => compactEdgeText(item, '')).filter(Boolean).join(', ') || fallback;
  if (typeof value === 'object') {
    const contract = value.contract || value.annotation || value.return_annotation || value.shape;
    const fields = Array.isArray(value.fields) && value.fields.length ? '{' + value.fields.slice(0, 4).join(',') + (value.fields.length > 4 ? ',…' : '') + '}' : '';
    const base = contract ? String(contract) : '';
    return [base, fields].filter(Boolean).join(' ') || fallback;
  }
  return fallback;
}
function normalizeReuseCard(card) {
  if (!card || card.kind !== 'reuse_card') return null;
  const contract = card.contract || {};
  return {
    primitive_id: card.primitive_id || '',
    label: card.label || card.primitive_id || 'reuse candidate',
    input: compactEdgeText(contract.input || card.input_edge, 'Unknown'),
    output: compactEdgeText(contract.output || card.output_edge, 'Unknown'),
    effects: Array.isArray(card.effects) ? card.effects : [],
    readiness: card.readiness || '',
    source: sourceFromRef(card.source_ref),
    proof: Array.isArray(card.proof_requirements) ? card.proof_requirements : [],
    serves_truth: card.serves_truth === true,
  };
}
function mapServerFinding(f) {
  const conf = typeof f.confidence === 'number' ? f.confidence : 0.5;
  const type = f.type || 'finding';
  const label = FINDING_LABELS[type] || String(type).replace(/_/g, ' ');
  // source_ref: the grounding that makes "already exists" trustworthy (registry deep-link or covering package)
  const sr = f.source_ref || f.source || null;
  const reuseCards = Array.isArray(f.reuse_cards) ? f.reuse_cards.map(normalizeReuseCard).filter(Boolean) : [];
  const source = reuseCards[0]?.source || sourceFromRef(sr);
  return {
    type, family: findingFamily(type), label, conf,
    message: f.message || '', suggestion: f.suggestion || '',
    evidence: f.evidence || '', source: source || f.source || null,
    source_ref: f.source_ref || null,
    reuse_cards: reuseCards,
    savings: f.savings || null,
    session_id: f.session_id || '',
    intervention_id: f.intervention_id || '',
  };
}
const FINDING_KEY = (f, i) => f.intervention_id || ((f.type || 'f') + '-' + Math.round((f.conf || 0) * 100) + '-' + i);

function ConfBar({ conf }) {
  const pct = Math.round((conf || 0) * 100);
  return (
    <span className="ado-conf" title={'Confidence ' + pct + '%'}>
      <span className="ado-conf-track"><span className="ado-conf-fill" style={{ width: pct + '%' }} /></span>
      <span className="ado-conf-n mono">{pct}%</span>
    </span>
  );
}

function SourceRef({ source }) {
  if (!source) return null;
  if (source.kind === 'existing' && source.name) {
    // deep-link to the OpenHubForAI record for {registry, name} over the /registry/ seam
    const href = '../openhubforai/index.html#/browse?registry=' + encodeURIComponent(source.registry || '') + '&q=' + encodeURIComponent(source.name);
    return <a className="ado-src ado-src--existing" href={href} title="Open the existing component in OpenHubForAI">
      <span className="ado-src-k">already exists</span><span className="mono">{source.name}</span></a>;
  }
  if (source.kind === 'covering' && source.package) {
    return <span className="ado-src ado-src--covering" title="A published package already covers this">
      <span className="ado-src-k">covered by</span><span className="mono">{source.package}</span></span>;
  }
  return null;
}

function ReuseCard({ card }) {
  if (!card) return null;
  const fx = card.effects.length ? card.effects.join(',') : 'pure/read';
  return (
    <div className="ado-reuse-card">
      <div className="ado-reuse-card-h">
        <span className="ado-reuse-k">Reuse object</span>
        {card.readiness && <span className="ado-reuse-readiness mono">{card.readiness}</span>}
      </div>
      <div className="ado-reuse-name mono">{card.label}</div>
      <div className="ado-reuse-edge mono">
        <span>{card.input}</span><span className="ado-reuse-arrow">→</span><span>{card.output}</span>
      </div>
      <div className="ado-reuse-meta">
        <span>effects: <b>{fx}</b></span>
        {card.proof.length ? <span>proof: <b>{card.proof.slice(0, 2).join(', ')}</b></span> : null}
      </div>
    </div>
  );
}

// the full finding card: family-toned type chip, confidence, message, evidence (redacted for footgun),
// suggestion, source_ref, optional reuse savings, and the Accept / Reuse / Dismiss outcome a person triages.
function FindingCard({ f, fkey, outcome, onOutcome }) {
  const tokenSavings = Number(f.savings?.tokens_avoided_estimate || f.savings?.tokens_saved || 0);
  const callSavings = Number(f.savings?.model_calls_avoided_estimate || f.savings?.model_calls_saved || 0);
  const savings = f.savings && (f.savings.dollars || f.savings.hours || tokenSavings || callSavings)
    ? [
        f.savings.hours ? f.savings.hours + 'h saved' : null,
        f.savings.dollars ? '$' + f.savings.dollars + ' saved' : null,
        tokenSavings ? tokenSavings.toLocaleString() + ' tokens avoided' : null,
        callSavings ? callSavings.toLocaleString() + ' model calls avoided' : null,
      ].filter(Boolean).join(' · ')
    : null;
  const redacted = f.family === 'footgun';
  return (
    <div className={'ado-finding fam-' + (f.family || 'neutral') + (outcome ? ' has-outcome out-' + outcome : '')}>
      <span className="ado-finding-dot" aria-hidden="true" />
      <div className="ado-finding-b">
        <div className="ado-finding-h">
          <span className="ado-finding-type">{f.label}</span>
          <ConfBar conf={f.conf} />
        </div>
        {f.message && <div className="ado-finding-t">{f.message}</div>}
        {f.evidence && <pre className={'ado-finding-ev mono' + (redacted ? ' redacted' : '')}>{f.evidence}</pre>}
        {f.suggestion && <div className="ado-finding-sg"><span className="ado-finding-sg-k">Suggestion</span>{f.suggestion}</div>}
        {Array.isArray(f.reuse_cards) && f.reuse_cards.length ? (
          <div className="ado-reuse-cards">
            {f.reuse_cards.slice(0, 2).map((card, idx) => <ReuseCard key={(card.primitive_id || card.label || 'card') + idx} card={card} />)}
          </div>
        ) : null}
        <div className="ado-finding-f">
          <div className="ado-finding-refs">
            <SourceRef source={f.source} />
            {savings && <span className="ado-src ado-src--save"><span className="ado-src-k">reuse</span><span className="mono">{savings}</span></span>}
          </div>
          {onOutcome ? (
            <div className="ado-finding-act">
              <button className={'ado-out' + (outcome === 'accepted' ? ' on' : '')} onClick={() => onOutcome(fkey, outcome === 'accepted' ? null : 'accepted', f)}>Accept</button>
              <button className={'ado-out' + (outcome === 'reused' ? ' on' : '')} onClick={() => onOutcome(fkey, outcome === 'reused' ? null : 'reused', f)}>Reuse</button>
              <button className={'ado-out' + (outcome === 'dismissed' ? ' on' : '')} onClick={() => onOutcome(fkey, outcome === 'dismissed' ? null : 'dismissed', f)}>Dismiss</button>
            </div>
          ) : null}
        </div>
        <div className="ado-finding-gov mono">candidate · serves_truth = false</div>
      </div>
    </div>
  );
}

// render a list of findings as cards (with optional triage). `report` is engine findings; pre-mapped if mapped=true.
function FindingList({ report, mapped, outcomes, onOutcome }) {
  const list = (mapped ? report : (report || []).map(mapServerFinding)).slice().sort((a, b) => b.conf - a.conf);
  if (!list.length) return <div className="ohl-empty">No findings — this session looks clean.</div>;
  return (
    <div className="ado-findings">
      {list.map((f, i) => {
        const k = FINDING_KEY(f, i);
        return <FindingCard key={k} fkey={k} f={f} outcome={outcomes ? outcomes[k] : null} onOutcome={onOutcome} />;
      })}
    </div>
  );
}

// hero aside: a compact sample report card (kit oh-card + bespoke layout)
function HeroReviewCard() {
  const top = FINDINGS.slice(0, 2);
  return (
    <div className="oh-card ado-herocard">
      <div className="ado-hc-head">
        <span className="ado-hc-eyebrow">session review</span>
        <span className="oh-badge oh-badge--verified oh-badge--sm">✔ ready</span>
      </div>
      <div className="ado-hc-title">Importer session · 12 minutes</div>
      <div className="ado-hc-list">
        {top.map((f) => (
          <div className="ado-hc-row" key={f.type}>
            <span className={'ado-hc-tag fam-' + findingFamily(f.type)}>{f.label}</span>
            <span className="ado-hc-conf mono">{Math.round(f.conf * 100)}%</span>
          </div>
        ))}
      </div>
      <div className="ado-hc-foot">
        <span className="mono">4 findings · ranked by confidence</span>
        <span className="ado-hc-score">0.97</span>
      </div>
    </div>
  );
}

function ExampleChooserModal({ open, busyId, onClose, onBuiltIn, onPick }) {
  if (!open) return null;
  return (
    <div className="ado-modal" role="dialog" aria-modal="true" aria-labelledby="ado-example-picker-title">
      <button className="ado-modal-backdrop" aria-label="Close example picker" onClick={onClose} />
      <div className="ado-modal-panel">
        <div className="ado-modal-head">
          <div>
            <div className="ado-modal-eyebrow">Example sessions</div>
            <h3 id="ado-example-picker-title">Choose a session to review</h3>
            <p>Pick a synthetic session. Load it into the editor, or replay it immediately through the review flow.</p>
          </div>
          <button className="ado-modal-close" aria-label="Close" onClick={onClose}>×</button>
        </div>
        <div className="ado-picker-featured">
          <div>
            <span className="ado-replay-type">Built-in</span>
            <h4>Importer helper reinvention</h4>
            <p>A compact sample that catches a duplicate CSV parser, context waste, a duplicate retry helper, and a missed registry search.</p>
          </div>
          <div className="ado-picker-actions">
            <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => onBuiltIn(true)}>Replay live</button>
            <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => onBuiltIn(false)}>Load</button>
          </div>
        </div>
        <div className="ado-picker-grid">
          {SESSION_REPLAY_EXAMPLES.map((item) => (
            <div className="ado-picker-card" key={item.id}>
              <div className="ado-replay-top">
                <span className="ado-replay-type">{item.type}</span>
                <span className="ado-replay-domain mono">{item.domain}</span>
              </div>
              <h4>{item.title}</h4>
              <div className="ado-replay-path mono">{item.path}</div>
              <p>{item.note}</p>
              <div className="ado-picker-actions">
                <button className="oh-btn oh-btn--primary oh-btn--sm" disabled={busyId === item.id} onClick={() => onPick(item, true)}>
                  {busyId === item.id ? 'Loading…' : 'Replay live'}
                </button>
                <button className="oh-btn oh-btn--ghost oh-btn--sm" disabled={busyId === item.id} onClick={() => onPick(item, false)}>Load</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function normalizeSessionMessage(m) {
  if (typeof m === 'string') return { role: 'user', content: m };
  if (!m || typeof m !== 'object') return null;
  const rawRole = String(m.role || m.type || m.speaker || 'user').toLowerCase();
  const role = rawRole === 'agent' ? 'assistant' : rawRole;
  const content = m.content != null ? m.content : (m.text != null ? m.text : (m.message != null ? m.message : ''));
  if (Array.isArray(content)) {
    return { role, content: content.map((b) => (b && typeof b === 'object' && b.text != null) ? b.text : String(b)).join('\n') };
  }
  return { role, content: String(content || '') };
}

function parseSessionJson(raw) {
  try {
    const parsed = JSON.parse(raw);
    const messages = Array.isArray(parsed) ? parsed : (Array.isArray(parsed.messages) ? parsed.messages : null);
    if (!messages) return null;
    return messages.map(normalizeSessionMessage).filter((m) => m && m.content.trim());
  } catch (e) {
    return null;
  }
}

// turn pasted/uploaded transcripts into engine messages. Supports:
// - "role: text" plain text
// - JSON arrays or {messages:[...]}
// - JSONL role/content objects from Claude Code, Codex, or exported demos.
function parseSession(text) {
  const raw = String(text || '').trim();
  if (!raw) return [];
  const jsonMessages = parseSessionJson(raw);
  if (jsonMessages) return jsonMessages;
  return raw.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
    try {
      const msg = normalizeSessionMessage(JSON.parse(line));
      if (msg && msg.content.trim()) return msg;
    } catch (e) { /* not JSONL; fall through to role-prefix text */ }
    const m = line.match(/^(user|agent|assistant|tool|system)\s*:\s*(.*)$/i);
    if (!m) return { role: 'user', content: line };
    const r = m[1].toLowerCase();
    return { role: r === 'agent' ? 'assistant' : r, content: m[2] };
  });
}

// the live review: paste a session (or upload / load the example) → POST it to the observer backend
// (/api/observer/review) and render the REAL governed findings. On any error (no backend reachable,
// non-2xx, bad payload) fall back to the built-in client-side preview so the demo never breaks.
function ReviewDemo({ outcomes, onOutcome, showSetup = true }) {
  const [text, setText] = React.useState(() => {
    try { return sessionStorage.getItem(ADO_EXAMPLE_SESSION_TEXT_KEY) || ''; } catch (e) { return ''; }
  });
  const [loadedLabel, setLoadedLabel] = React.useState(() => {
    try { return sessionStorage.getItem(ADO_EXAMPLE_SESSION_LABEL_KEY) || ''; } catch (e) { return ''; }
  });
  const autorunRef = React.useRef(false);
  if (autorunRef.current === false) {
    try { autorunRef.current = sessionStorage.getItem(ADO_EXAMPLE_SESSION_AUTORUN_KEY) === '1'; } catch (e) { autorunRef.current = false; }
  }
  const [reviewed, setReviewed] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [findings, setFindings] = React.useState([]);
  const [source, setSource] = React.useState('live'); // 'live' = real backend · 'preview' = fallback
  const [error, setError] = React.useState('');
  const [chooserOpen, setChooserOpen] = React.useState(false);
  const [exampleBusyId, setExampleBusyId] = React.useState('');
  const fileRef = React.useRef(null);

  // manual upload: read a transcript FILE (.jsonl/.json/.txt/.md, Claude Code or Codex) into the box; it then
  // reviews exactly like a paste. Read-only, in-browser — the file is never uploaded anywhere.
  const onUpload = React.useCallback((e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => { setText(String(reader.result || '')); setLoadedLabel(''); setReviewed(false); setError(''); };
    reader.readAsText(file);
    e.target.value = '';   // allow re-selecting the same file
  }, []);

  const runReview = React.useCallback(async (overrideText) => {
    const raw = overrideText || text || SESSION_EXAMPLE;
    const messages = parseSession(raw);
    if (!messages.length) { setError('Paste or upload a session first.'); return; }
    setBusy(true); setError('');
    try {
      const res = await fetch('/api/observer/review', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
      });
      if (!res.ok) throw new Error('observer backend status ' + res.status);
      const data = await res.json();
      const report = Array.isArray(data.report) ? data.report : [];
      setFindings(report.map(mapServerFinding));
      setSource('live');
    } catch (e) {
      // backend unreachable/unhealthy → keep the demo alive with the client-side preview
      setFindings(FINDINGS.map(mapServerFinding));
      setSource('preview');
    } finally {
      setBusy(false);
      setReviewed(true);
    }
  }, [text]);

  const loadBuiltInExample = React.useCallback((autorun) => {
    setText(SESSION_EXAMPLE);
    setLoadedLabel('Built-in importer session');
    setReviewed(false);
    setError('');
    setChooserOpen(false);
    if (autorun) runReview(SESSION_EXAMPLE);
  }, [runReview]);

  const loadReplayExample = React.useCallback(async (item, autorun) => {
    setExampleBusyId(item.id);
    try {
      const res = await fetch(exampleHref(item, 'txt'), { cache: 'no-store' });
      if (!res.ok) throw new Error('example status ' + res.status);
      const raw = await res.text();
      setText(raw);
      setLoadedLabel(item.title);
      setReviewed(false);
      setError('');
      setChooserOpen(false);
      if (autorun) runReview(raw);
    } catch (e) {
      setError('Could not load that example. Try another session or upload a transcript.');
    } finally {
      setExampleBusyId('');
    }
  }, [runReview]);

  React.useEffect(() => {
    if (!autorunRef.current) return;
    autorunRef.current = false;
    try { sessionStorage.removeItem(ADO_EXAMPLE_SESSION_AUTORUN_KEY); } catch (e) { /* unavailable */ }
    runReview();
  }, [runReview]);

  const note = source === 'preview'
    ? 'Preview review (the observer backend was not reachable). Installed, AIDevObserver reviews your real sessions on your machine.'
    : (findings.length
        ? 'Live review from the observer engine on this machine. Transcript text is not stored; triage clicks append metadata only.'
        : 'Live review from the observer engine — no findings on this session. It looks clean.');
  const reviewTokensAvoided = findings.reduce((sum, f) => sum + Number(f.savings?.tokens_avoided_estimate || 0), 0);
  const reviewCallsAvoided = findings.reduce((sum, f) => sum + Number(f.savings?.model_calls_avoided_estimate || 0), 0);

  return (
    <div className="ado-review-layout">
      <div className="ado-review-main">
        <div className="ado-demo">
          <div className="oh-card oh-card--pad ado-demo-in">
            <div className="ado-demo-head">
              <div>
                <label className="ado-demo-label" htmlFor="ado-session">Review a transcript</label>
                <p className="ado-demo-help">Paste Claude Code, Codex, Cursor, Aider, JSONL, or plain text. Read-only and candidate-only.</p>
              </div>
              <span className="oh-badge oh-badge--sm mono">serves_truth=false</span>
            </div>
            <div className="ado-demo-hints" aria-hidden="true">
              <span>Paste</span><span>Upload</span><span>Choose replay</span><span>Review</span>
            </div>
            <textarea id="ado-session" className="ado-demo-ta" rows={7} value={text}
              onChange={(e) => { setText(e.target.value); setLoadedLabel(''); setError(''); }}
              placeholder={'Paste a transcript here, upload a .jsonl / .txt file, or choose a realistic replay example.'} />
            <input ref={fileRef} type="file" accept=".jsonl,.json,.txt,.md,.log" style={{ display: 'none' }} onChange={onUpload} />
            {loadedLabel && <div className="ado-loaded-example mono">Loaded example: {loadedLabel}</div>}
            {error && <div className="ado-demo-err mono">{error}</div>}
            <div className="ado-demo-actions">
              <button className="oh-btn oh-btn--ghost" onClick={() => fileRef.current && fileRef.current.click()}>Upload transcript</button>
              <button className="oh-btn oh-btn--ghost" onClick={() => setChooserOpen(true)}>Choose replay</button>
              <button className="oh-btn oh-btn--primary" disabled={busy} onClick={() => runReview()}>{busy ? 'Reviewing…' : 'Review session →'}</button>
            </div>
          </div>
          <ExampleChooserModal open={chooserOpen} busyId={exampleBusyId} onClose={() => setChooserOpen(false)}
            onBuiltIn={loadBuiltInExample} onPick={loadReplayExample} />
          {busy && (
            <div className="oh-card oh-card--pad ado-demo-out">
              <div className="ado-skel-row" /><div className="ado-skel-row" /><div className="ado-skel-row short" />
            </div>
          )}
          {reviewed && !busy && (
            <div className="oh-card oh-card--pad ado-demo-out">
              <div className="ado-demo-out-h">
                <span className="ado-demo-out-t">Review</span>
                <span className="oh-badge oh-badge--sm mono">{findings.length} findings · ranked</span>
              </div>
              {(reviewTokensAvoided || reviewCallsAvoided) ? (
                <div className="ado-demo-note mono">
                  Estimated avoided: {reviewTokensAvoided ? reviewTokensAvoided.toLocaleString() + ' tokens' : '—'}
                  {reviewCallsAvoided ? ' · ' + reviewCallsAvoided.toLocaleString() + ' model calls' : ''}
                </div>
              ) : null}
              <FindingList report={findings} mapped outcomes={outcomes} onOutcome={onOutcome} />
              <div className="ado-demo-note mono">{note}</div>
            </div>
          )}
        </div>
      </div>
      {showSetup && <SetupGuide compact />}
    </div>
  );
}

function InstallLine({ label, cmd }) {
  const [copied, setCopied] = React.useState(false);
  const copy = () => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(cmd).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1400); }).catch(() => {});
      }
    } catch (e) { /* clipboard unavailable; the command is selectable inline */ }
  };
  return (
    <div className="ado-install">
      <div className="ado-install-label">{label}</div>
      <div className="ado-install-row">
        <code className="ado-install-cmd mono">{cmd}</code>
        <button className="oh-btn oh-btn--ghost oh-btn--sm ado-install-copy" onClick={copy}>{copied ? 'Copied' : 'Copy'}</button>
      </div>
    </div>
  );
}

function SetupPathCard({ item, compact }) {
  return (
    <div className={compact ? 'ado-setup-card compact' : 'ado-setup-card'}>
      <div className="ado-setup-card-top">
        <span className="ado-setup-icon" aria-hidden="true">{item.icon}</span>
        <div>
          <h4>{item.title}</h4>
          <div className="ado-setup-surface">{item.surface}</div>
        </div>
      </div>
      <p>{item.desc}</p>
      <ol className="ado-setup-steps">
        {item.steps.map((step) => <li key={step}>{step}</li>)}
      </ol>
      {item.command
        ? <code className="ado-setup-command mono">{item.command}</code>
        : <div className="ado-setup-action">{item.action}</div>}
    </div>
  );
}

function SetupGuide({ compact }) {
  return (
    <div className={compact ? 'oh-card oh-card--pad ado-review-setup compact' : 'ado-setup'}>
      <div className="ado-setup-head">
        <div>
          <div className="ado-setup-eyebrow">Setup</div>
          <h3>One review, every AI coding surface.</h3>
          <p>Start with paste/upload, then connect the same review to editors, Claude Code, CLI, hooks, or discovered local sessions.</p>
        </div>
        {compact && <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate(ROUTES.developer)}>Developer docs</button>}
      </div>
      <div className={compact ? 'ado-setup-grid compact' : 'ado-setup-grid'}>
        {SETUP_PATHS.map((item) => <SetupPathCard item={item} compact={compact} key={item.title} />)}
      </div>
    </div>
  );
}

/* ===================== marketing sections ===================== */
function SecHow() {
  return (
    <OhSection id="how" label="How it works"
      title="A session goes in. A clear, ranked report comes out."
      body={<>AIDevObserver turns each AI coding session into a report your team can act on. It flags reinvention, wasted
        context, avoidable model loops, and missed cheaper paths, then ranks them so the most useful findings are the first ones you read.</>}>
      <OhFeatures items={HOW} />
    </OhSection>
  );
}

function SecRuns() {
  return (
    <OhSection id="runs" label="Where it runs"
      title="One review, wherever AI coding happens."
      body={<>Paste or upload first, then connect the same ranked review to editors, Claude Code, CLI, CI, live hooks, and
        discovered local sessions. Every surface reads from the same report format.</>}>
      <div className="ado-setup-grid">
        {SETUP_PATHS.map((item) => <SetupPathCard item={item} key={item.title} />)}
      </div>
      <div className="ado-installs">
        {INSTALL_LINES.map(([label, cmd]) => <InstallLine label={label} cmd={cmd} key={cmd} />)}
      </div>
    </OhSection>
  );
}

function ExamplesGrid({ compact }) {
  return (
    <div className={compact ? 'ado-examples compact' : 'ado-examples'}>
      {COMPILED_AI_EXAMPLES.map((item) => (
        <button className="oh-card oh-card--pad oh-card--interactive ado-example" key={item.title}
          onClick={() => navigate(item.route)} style={{ textAlign: 'left' }}>
          <div className="ado-example-top">
            <span className="ado-example-type">{item.type}</span>
            <span className="ado-example-arrow" aria-hidden="true">›</span>
          </div>
          <h4 className="ado-example-title">{item.title}</h4>
          <div className="ado-example-path mono">{item.path}</div>
          <p className="ado-example-note">{item.note}</p>
          <div className="ado-example-lock mono">candidate -> compiler -> PlanLock -> ledger</div>
        </button>
      ))}
    </div>
  );
}

function SessionReplayGrid({ compact }) {
  return (
    <div className={compact ? 'ado-replays compact' : 'ado-replays'}>
      {SESSION_REPLAY_EXAMPLES.map((item) => (
        <div className="oh-card oh-card--pad ado-replay" key={item.id}>
          <div className="ado-replay-top">
            <span className="ado-replay-type">{item.type}</span>
            <span className="ado-replay-domain mono">{item.domain}</span>
          </div>
          <h4 className="ado-replay-title">{item.title}</h4>
          <div className="ado-replay-path mono">{item.path}</div>
          <p className="ado-replay-note">{item.note}</p>
          <div className="ado-replay-actions">
            <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => openSessionReplay(item, true)}>Replay live</button>
            <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => openSessionReplay(item, false)}>Load</button>
            <span className="ado-replay-downloads">
              <a className="ado-replay-link mono" href={exampleHref(item, 'txt')} download>TXT</a>
              <a className="ado-replay-link mono" href={exampleHref(item, 'jsonl')} download>JSONL</a>
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function SecExamples() {
  return (
    <OhSection id="examples" label="Examples"
      title="Concrete routes from raw AI work to compiled, reviewable artifacts."
      body={<>The AIDevObserver benchmark lab is the evaluation view over this architecture: raw sessions, workflow graphs,
        media plans, and document pipelines become candidate records, then deterministic tools validate what can
        compile and report what still needs proof.</>}>
      <ExamplesGrid />
      <div className="ado-example-pack">
        <div className="ado-example-pack-h">
          <h3>Replayable session pack</h3>
          <a className="oh-btn oh-btn--ghost oh-btn--sm" href={ADO_EXAMPLE_ROOT + 'manifest.json'} download>Download manifest</a>
        </div>
        <p>Use these synthetic sessions to demo upload, live replay, and reuse-review positioning across common AI development work.</p>
        <SessionReplayGrid compact />
      </div>
    </OhSection>
  );
}

function SecDemo() {
  return (
    <OhSection id="demo" label="Live review"
      title="See a review on a real session."
      body={<>Paste an AI coding session, or load the example, and AIDevObserver returns the findings ranked by confidence.
        This page shows a preview. Installed, it reviews your own sessions on your machine.</>}>
      <ReviewDemo showSetup={false} />
    </OhSection>
  );
}

function SecTrust() {
  return (
    <OhSection id="trust" label="Trust"
      title="Findings are suggestions a person triages."
      body={<>AIDevObserver is built to help your team, not to police it. It reads the session, writes a report, and stops there.</>}>
      <div className="ado-trust">
        {TRUST.map(([t, d]) => (
          <div className="oh-card oh-card--pad ado-trust-item" key={t}>
            <div className="ado-trust-mk" aria-hidden="true">✓</div>
            <div>
              <div className="ado-trust-t">{t}</div>
              <div className="ado-trust-d">{d}</div>
            </div>
          </div>
        ))}
      </div>
    </OhSection>
  );
}

// the Family column links the other four surfaces (rename-correct folders; the cross-link is how the family reads as one company)
const FAMILY_LINKS = [
  ['AI Done Right ↗', '../context-is-everything/index.html'],
  ['Teleon ↗', '../teleon/index.html'],
  ['Baltor ↗', '../baltor/index.html'],
  ['OpenHubForAI ↗', '../openhubforai/index.html'],
];

/* ===================== landing (marketing) ===================== */
function MarketingShell({ theme, onToggle, children }) {
  return (
    <div className={'oh dir-s theme-' + theme + ' oh-site ado'} style={{ '--accent': ACCENT }}>
      <OhTopBar brand={BRAND} nav={MKT_NAV} signInHref="/signin"
        cta={{ label: 'Open the app', href: ROUTES.dashboard }} theme={theme} onToggle={onToggle} />
      {children}
      <OhFooter brand={BRAND} tagline="AI coding session review · part of AI Done Right" cols={[
        ['Product', routePairs(PRODUCT_ROUTES).concat([['Pricing', ROUTES.billing]])],
        ['Install', routePairs(INSTALL_FOOTER_ROUTES)],
        ['Family', FAMILY_LINKS],
      ]} />
    </div>
  );
}

function HomeRouteCards() {
  return (
    <OhSection id="start" label="Start here" title="Pick the surface you need."
      body="The home page stays short. Deeper setup, examples, trust details, and the browser IDE each have their own page.">
      <div className="ado-home-routes">
        {HOME_ROUTES.map((route) => (
          <button className="oh-card oh-card--pad oh-card--interactive ado-home-route" key={route.label}
            onClick={() => navigate(route.href)} style={{ textAlign: 'left' }}>
            <div className="ado-home-route-k mono">{route.href}</div>
            <h4>{route.label}</h4>
            <p>{route.desc}</p>
            <span aria-hidden="true">→</span>
          </button>
        ))}
      </div>
    </OhSection>
  );
}

function Landing({ theme, onToggle }) {
  return (
    <MarketingShell theme={theme} onToggle={onToggle}>
      <OhHero
        eyebrow="AI coding session review"
        title={<>Stop AI coding agents from reinventing <span className="tint">known code</span>.</>}
        lede="AIDevObserver reviews AI coding sessions, finds missed helpers, templates, workflows, and prior generated code in the primitive database, estimates wasted context, and turns accepted findings into reusable registry memory."
        ctas={[
          { label: 'Review my latest session →', href: ROUTES.review, primary: true },
          { label: 'Replay examples', href: ROUTES.examples },
        ]}
        aside={<HeroReviewCard />} />
      <HomeRouteCards />
      <OhBand title="Make every AI coding session count."
        sub="Start with a replay or the browser IDE, then connect the same review to the surfaces your team already uses."
        ctas={[
          { label: 'Open the IDE →', href: ROUTES.ide, primary: true },
          { label: 'Setup options', href: ROUTES.setup },
        ]} />
    </MarketingShell>
  );
}

const MARKETING_PAGE_CONFIG = {
  [ROUTES.how]: {
    section: SecHow,
    band: {
      title: 'See it on a real workflow.',
      sub: 'Replay realistic AI coding sessions or open the browser IDE to create one.',
      ctas: [{ label: 'Replay examples →', href: ROUTES.examples, primary: true }, { label: 'Open IDE', href: ROUTES.ide }],
    },
  },
  [ROUTES.setup]: {
    section: SecRuns,
    band: {
      title: 'Ready to connect a surface?',
      sub: 'Use Review for paste/upload, IDE for the browser harness, or Developer for API details.',
      ctas: [{ label: 'Review a session →', href: ROUTES.review, primary: true }, { label: 'Developer docs', href: ROUTES.developer }],
    },
  },
  [ROUTES.demo]: {
    section: SecDemo,
    band: {
      title: 'Want the full workspace?',
      sub: 'Open the app to review sessions, replay examples, or try the browser IDE.',
      ctas: [{ label: 'Open Review →', href: ROUTES.review, primary: true }, { label: 'Open IDE', href: ROUTES.ide }],
    },
  },
  [ROUTES.trust]: {
    section: SecTrust,
    band: {
      title: 'Keep findings candidate-only.',
      sub: 'Accepted findings become reusable memory; proof and promotion remain separate from review.',
      ctas: [{ label: 'See examples →', href: ROUTES.examples, primary: true }, { label: 'Open reports', href: ROUTES.reports }],
    },
  },
};

function MarketingPage({ route, theme, onToggle }) {
  const cfg = MARKETING_PAGE_CONFIG[route] || MARKETING_PAGE_CONFIG[ROUTES.how];
  const PageSection = cfg.section;
  return (
    <MarketingShell theme={theme} onToggle={onToggle}>
      <PageSection />
      <OhBand title={cfg.band.title} sub={cfg.band.sub} ctas={cfg.band.ctas} />
    </MarketingShell>
  );
}

/* ===================== the logged-in app (OhAppShell + the kit pages) ===================== */
// top-level routes, the kit conventions (OhAuth → /dashboard, the shell foot → /settings). The sidebar is the
// shared OhAppShell; the work screens talk to the REAL observer backend over /api/observer/*. serves_truth=false.

const APP_NAV = [
  [ROUTES.dashboard, '◉', 'Dashboard'],
  [ROUTES.review, '▷', 'Review'],
  [ROUTES.ide, '▣', 'IDE'],
  [ROUTES.sessions, '≡', 'Sessions'],
  [ROUTES.findings, '⚑', 'Findings'],
  [ROUTES.agentic, '⟳', 'Agentic'],
  [ROUTES.intelligence, '✦', 'Intelligence'],
  [ROUTES.examples, '□', 'Examples'],
  [ROUTES.reports, '◈', 'Reports'],
];
const APP_GROUPS = [
  { label: 'Workspace', defaultOpen: true, items: [
    [ROUTES.notifications, '◔', 'Notifications'],
    [ROUTES.members, '◑', 'Team'],
    [ROUTES.billing, '▤', 'Billing'],
    [ROUTES.developer, '⌘', 'Developer'],
  ] },
  { label: 'You', defaultOpen: false, items: [
    [ROUTES.account, '◓', 'Account'],
    [ROUTES.settings, '⚙', 'Settings'],
    [ROUTES.help, '?', 'Help'],
  ] },
];
// every app route (for route detection + the command palette)
const APP_ROUTES = APP_NAV.map((n) => n[0]).concat(APP_GROUPS.reduce((a, g) => a.concat(g.items.map((i) => i[0])), []));
const AUTH_ROUTES = ['/signin', '/signup', '/forgot'];

function shortId(id) { const s = String(id || ''); return s.length > 14 ? s.slice(0, 8) + '…' + s.slice(-3) : s; }
function relTime(sec) {
  if (!sec) return '—';
  const s = Math.max(0, Date.now() / 1000 - sec);
  if (s < 60) return 'just now';
  const m = Math.floor(s / 60); if (m < 60) return m + 'm ago';
  const h = Math.floor(m / 60); if (h < 24) return h + 'h ago';
  const d = Math.floor(h / 24); if (d < 30) return d + 'd ago';
  return new Date(sec * 1000).toLocaleDateString();
}

// /dashboard → the workspace overview. Stats are derived from REAL state (sessions discovered, the last review,
// triaged outcomes); product metrics with no real source yet show an honest "—" rather than a fabricated number.
function AppDashboard({ sessions, lastReport, outcomes }) {
  const [cfg, setCfg] = React.useState(null);
  const [cfgErr, setCfgErr] = React.useState(false);
  React.useEffect(() => {
    let live = true;
    fetch('/api/observer/config', { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { if (live) { setCfg(d); setCfgErr(false); } })
      .catch(() => { if (live) { setCfg(null); setCfgErr(true); } });
    return () => { live = false; };
  }, []);
  const sessCount = Array.isArray(sessions) ? sessions.length : null;
  const rawFindings = Array.isArray(lastReport?.report) ? lastReport.report : [];
  const latestFindings = rawFindings.map(mapServerFinding);
  const lastFindings = lastReport ? rawFindings.length : null;
  const summary = lastReport?.summary || {};
  const lastTokensAvoided = Number(summary.tokens_avoided_estimate || lastReport?.savings?.tokens_avoided_estimate || 0);
  const lastCallsAvoided = Number(summary.model_calls_avoided_estimate || lastReport?.savings?.model_calls_avoided_estimate || 0);
  const triaged = outcomes ? Object.keys(outcomes).length : 0;
  const accepted = outcomes ? Object.values(outcomes).filter((o) => o === 'accepted').length : 0;
  const reused = outcomes ? Object.values(outcomes).filter((o) => o === 'reused').length : 0;
  const dismissed = outcomes ? Object.values(outcomes).filter((o) => o === 'dismissed').length : 0;
  const reuseRate = triaged ? Math.round((reused / triaged) * 100) + '%' : '—';
  const toggles = cfg?.toggles || {};
  const activeToggleCount = Object.values(toggles).filter(Boolean).length;
  const dashboardStats = [
    ['Sessions found', sessCount == null ? '—' : sessCount, 'local Claude Code / Codex metadata'],
    ['Latest findings', lastFindings == null ? '—' : lastFindings, 'ranked candidate suggestions'],
    ['Tokens avoided', lastTokensAvoided ? lastTokensAvoided.toLocaleString() : '—', 'from latest reviewed session'],
    ['Model calls avoided', lastCallsAvoided ? lastCallsAvoided.toLocaleString() : '—', 'from latest reviewed session'],
    ['Reuse rate', reuseRate, triaged ? `${reused} reused of ${triaged} triaged` : 'triage findings to build memory'],
    ['Active layers', cfg ? `${activeToggleCount}/${Object.keys(toggles).length || 0}` : '—', 'registry, MCP, hooks, rerank'],
  ];
  const recentSessions = Array.isArray(sessions) ? sessions.slice(0, 6) : [];
  const lanes = (cfg?.model_lanes || []).filter((lane) => ['kimi', 'glm'].includes(lane.key));
  const registryRows = [
    ['Global primitives', toggles.global_primitives, 'Search reusable primitive records before rebuilds.'],
    ['Local registry', toggles.local_registry, 'Match repo helpers, scripts, docs, and edge contracts.'],
    ['MCP intelligence', toggles.mcp, 'Expose review/search to Claude Code as tools.'],
    ['Live hook', toggles.live_hook, 'Non-blocking coaching while an agent works.'],
    ['Token savings', toggles.token_savings, 'Attach avoided-token estimates to findings.'],
    ['Kimi/GLM rerank', toggles.llm_rerank, 'Optional model-assisted ranking after grounded registry search.'],
  ];
  return (
    <>
      <OhPageHead eyebrow="Dashboard" title="AIDevObserver command center"
        sub="Track reviewed sessions, registry reuse, token savings, model lanes, and team memory. The IDE stays separate; this page is the operating view." />
      <div className="ado-dash">
        <section className="ado-dash-hero">
          <div className="ado-dash-hero-copy">
            <div className="ado-dash-kicker">Review pipeline</div>
            <h3>Find reusable routes before another agent rebuilds the same thing.</h3>
            <p>Use this page like an LLM observability dashboard for development sessions: review queue, latest findings, registry health, model lanes, and accepted reuse memory.</p>
            <div className="ado-dash-actions">
              <button className="oh-btn oh-btn--primary" onClick={() => navigate(ROUTES.review)}>Review session →</button>
              <button className="oh-btn oh-btn--ghost" onClick={() => navigate(ROUTES.ide)}>Open IDE</button>
              <button className="oh-btn oh-btn--ghost" onClick={() => navigate(ROUTES.intelligence)}>Configure lanes</button>
            </div>
          </div>
          <div className="ado-dash-health">
            <div className="ado-dash-health-row">
              <span>Observer service</span>
              <StatusPill value={cfgErr ? 'not_connected' : (cfg ? 'ready' : 'checking')} />
            </div>
            <div className="ado-dash-health-row">
              <span>Primitive search</span>
              <StatusPill value={toggles.global_primitives ? 'ready' : 'off'} />
            </div>
            <div className="ado-dash-health-row">
              <span>Outcome memory</span>
              <b>{triaged || '—'}</b>
            </div>
          </div>
        </section>

        <section className="ado-dash-kpis" aria-label="AIDevObserver metrics">
          {dashboardStats.map(([label, value, hint]) => (
            <div className="ado-dash-kpi" key={label}>
              <span>{label}</span>
              <b>{value}</b>
              <small>{hint}</small>
            </div>
          ))}
        </section>

        <section className="ado-dash-grid">
          <div className="ado-dash-column">
            <div className="ado-dash-panel">
              <div className="ado-dash-panel-head">
                <div>
                  <h3>Session review queue</h3>
                  <p>Recent local session metadata. Pick one to review, or paste/upload a transcript.</p>
                </div>
                <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate(ROUTES.sessions)}>Open sessions</button>
              </div>
              <div className="ado-dash-list">
                {recentSessions.length ? recentSessions.map((s) => (
                  <button className="ado-dash-session" key={s.path || s.session_id} onClick={() => navigate(ROUTES.sessions)}>
                    <span className="mono">{shortId(s.session_id)}</span>
                    <b>{s.project || 'session'}</b>
                    <em>{relTime(s.mtime)}</em>
                  </button>
                )) : (
                  <div className="ado-dash-empty">No local sessions discovered yet. Paste a transcript or open an example replay.</div>
                )}
              </div>
            </div>

            <div className="ado-dash-panel">
              <div className="ado-dash-panel-head">
                <div>
                  <h3>Latest review signals</h3>
                  <p>High-confidence findings from the last reviewed session.</p>
                </div>
                <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate(ROUTES.review)}>Run review</button>
              </div>
              <div className="ado-dash-signal-list">
                {latestFindings.length ? latestFindings.slice(0, 4).map((f, idx) => (
                  <div className={'ado-dash-signal fam-' + findingFamily(f.type)} key={(f.type || 'finding') + idx}>
                    <span>{f.type || 'finding'}</span>
                    <b>{f.title || f.message || 'Candidate finding'}</b>
                    <small>{f.source_ref || f.suggestion || 'candidate · serves_truth=false'}</small>
                  </div>
                )) : (
                  <div className="ado-dash-empty">No latest review loaded in this browser session. Use Review or Examples to create one.</div>
                )}
              </div>
            </div>
          </div>

          <div className="ado-dash-column">
            <div className="ado-dash-panel">
              <div className="ado-dash-panel-head compact">
                <h3>Registry routing</h3>
                <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate(ROUTES.intelligence)}>Settings</button>
              </div>
              <div className="ado-dash-rows">
                {registryRows.map(([label, on, desc]) => (
                  <div className="ado-dash-row" key={label}>
                    <span className={'ado-dash-dot ' + (on ? 'on' : '')} />
                    <div>
                      <b>{label}</b>
                      <small>{desc}</small>
                    </div>
                    <em>{on ? 'on' : 'off'}</em>
                  </div>
                ))}
              </div>
            </div>

            <div className="ado-dash-panel">
              <div className="ado-dash-panel-head compact">
                <h3>Model lanes</h3>
                <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate(ROUTES.intelligence)}>Open</button>
              </div>
              <div className="ado-dash-rows">
                {lanes.length ? lanes.map((lane) => (
                  <div className="ado-dash-row" key={lane.key}>
                    <span className={'ado-dash-dot ' + ((lane.status === 'ready' || lane.status === true) ? 'on' : '')} />
                    <div>
                      <b>{lane.title}</b>
                      <small className="mono">{lane.model || lane.provider || lane.key}</small>
                    </div>
                    <em>{String(lane.status || 'off').replace(/_/g, ' ')}</em>
                  </div>
                )) : <div className="ado-dash-empty">Model lane config is unavailable until the observer service responds.</div>}
              </div>
            </div>

            <div className="ado-dash-panel">
              <div className="ado-dash-panel-head compact">
                <h3>Outcome memory</h3>
                <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate(ROUTES.findings)}>Findings</button>
              </div>
              <div className="ado-dash-outcomes">
                <div><span>Accepted</span><b>{accepted || '—'}</b></div>
                <div><span>Reused</span><b>{reused || '—'}</b></div>
                <div><span>Dismissed</span><b>{dismissed || '—'}</b></div>
              </div>
              <p className="ado-dash-note">Triage is the flywheel: accepted/reused findings become team memory; dismissed findings become negative memory.</p>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

// /review → the paste/upload-a-session review, reused inside the shell (real /api/observer/review)
function AppReview({ outcomes, onOutcome }) {
  return (
    <>
      <OhPageHead eyebrow="Review" title="Review a session"
        sub="Paste or upload now, choose a realistic replay, or connect AIDevObserver to the surface where your agent already runs. Same read-only review across every path." />
      <ReviewDemo outcomes={outcomes} onOutcome={onOutcome} />
    </>
  );
}

// /sessions → the discovered local Claude Code / Codex sessions, in an OhTable. Picking one reviews it.
function AppSessions({ onReview, busyPath }) {
  const [rows, setRows] = React.useState(null);   // null = loading, [] = none
  const [err, setErr] = React.useState(false);
  const [demoSafe, setDemoSafe] = React.useState(false);
  React.useEffect(() => {
    let live = true;
    fetch('/api/observer/sessions')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        if (live) {
          setDemoSafe(d && d.local_session_discovery_enabled === false);
          setRows(Array.isArray(d.sessions) ? d.sessions : []);
        }
      })
      .catch(() => { if (live) { setErr(true); setRows([]); } });
    return () => { live = false; };
  }, []);
  const cols = [
    { key: 'session_id', label: 'Session', sortable: true, sortValue: (r) => r.session_id,
      render: (r) => <span className="mono">{shortId(r.session_id)}</span> },
    { key: 'project', label: 'Project', sortable: true },
    { key: 'mtime', label: 'Modified', sortable: true, sortValue: (r) => r.mtime, render: (r) => relTime(r.mtime) },
    { key: '_act', label: '', align: 'right', render: (r) => (
      <button className="oh-btn oh-btn--ghost oh-btn--sm" disabled={busyPath === r.path}
        onClick={(e) => { e.stopPropagation(); onReview(r); }}>{busyPath === r.path ? 'Reviewing…' : 'Review →'}</button>) },
  ];
  const empty = err
    ? 'The observer service is not reachable. Start it with: python3 scripts/observer_local_service.py --serve'
    : demoSafe
      ? 'Public demo mode is enabled, so local session discovery is hidden. Use Examples or paste/upload a transcript on Review.'
    : 'No local sessions found yet. Start a Claude Code session in this project, or paste one on the Review page.';
  return (
    <>
      <OhPageHead eyebrow="Sessions" title="Local AI coding sessions"
        sub={demoSafe
          ? 'For shared demos, AIDevObserver hides local session discovery. The Examples and Review pages remain fully usable.'
          : 'AIDevObserver discovers your Claude Code and Codex sessions for this project. Pick one to review. Read only — discovery reads file metadata, never the transcript content.'} />
      {rows === null ? <div className="ohl-empty">Loading sessions…</div>
        : <OhTable cols={cols} rows={rows} rowKey={(r) => r.path} onRow={(r) => onReview(r)} empty={empty} />}
    </>
  );
}

// /findings → the most recent review's findings, ranked + triageable. Honest when the service was unreachable.
function AppFindings({ report, source, session, error, outcomes, onOutcome }) {
  if (error) {
    return (
      <>
        <OhPageHead eyebrow="Findings" title="That session was not reviewed" sub={error} />
        <div className="ohl-empty">Start the service with <code className="mono">python3 scripts/observer_local_service.py --serve</code>, then try again.</div>
      </>
    );
  }
  if (!report) {
    return (
      <>
        <OhPageHead eyebrow="Findings" title="No review yet"
          sub="Run a review from the Sessions page, or paste a session on the Review page." />
        <div className="ohl-empty">
          <div>Nothing reviewed yet this session.</div>
          <button className="oh-btn oh-btn--primary" style={{ marginTop: 12 }} onClick={() => navigate(ROUTES.review)}>Review a session →</button>
        </div>
      </>
    );
  }
  const findings = (report.report || []).map(mapServerFinding);
  const s = report.summary || {};
  const tokensAvoided = Number(s.tokens_avoided_estimate || report.savings?.tokens_avoided_estimate || 0);
  const callsAvoided = Number(s.model_calls_avoided_estimate || report.savings?.model_calls_avoided_estimate || 0);
  return (
    <>
      <OhPageHead eyebrow="Findings" title={session ? ('Review · ' + shortId(session)) : 'Latest review'}
        sub="Every finding is a governed suggestion you triage with Accept / Reuse / Dismiss. Outcome memory stores metadata, not transcript text." />
      <OhRollup items={[
        ['Findings', s.findings != null ? s.findings : findings.length],
        ['Reinventions', s.reinventions != null ? s.reinventions : '—'],
        ['Waste signals', s.waste_signals != null ? s.waste_signals : '—'],
        ['Tokens avoided', tokensAvoided ? tokensAvoided.toLocaleString() : '—'],
        ['Model calls avoided', callsAvoided ? callsAvoided.toLocaleString() : '—'],
        ['Source', source === 'live' ? 'live engine' : 'preview'],
      ]} />
      <FindingList report={findings} mapped outcomes={outcomes} onOutcome={onOutcome} />
    </>
  );
}

// a worked agentic loop (a thrashing, then expensive-search-ending, run) the Agentic screen supervises
const AGENTIC_EXAMPLE = [
  { action: 'run pytest tests/importer', ok: false, error: 'ImportError: no module named csvkit' },
  { action: 'run pytest tests/importer', ok: false, error: 'ImportError: no module named csvkit' },
  { action: 'run pytest tests/importer', ok: false, error: 'ImportError: no module named csvkit' },
  { action: 'ask model to scan the whole repo for an existing csv parser', ok: true },
];

// /agentic → supervise an AUTONOMOUS agent loop (not a human session): POST it to the observer agentic
// endpoint and render the verdict + loop-shape findings. On an unreachable backend, a client-side preview.
function AppAgentic({ outcomes, onOutcome }) {
  const [run, setRun] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  const [source, setSource] = React.useState('live');

  const supervise = React.useCallback(async () => {
    setBusy(true);
    try {
      const res = await fetch('/api/observer/agentic', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steps: AGENTIC_EXAMPLE, goal: 'fix the importer test suite', budget: { max_steps: 8 } }),
      });
      if (!res.ok) throw new Error('observer backend status ' + res.status);
      setRun(await res.json()); setSource('live');
    } catch (e) {
      setRun({ report: [
        { type: 'agentic_loop', confidence: 0.9, message: 'the same action ran 3 times in a row (thrash) starting at step 0', suggestion: 'break the loop: change the approach, or stop and surface the blocker', evidence: 'run pytest tests/importer ×3' },
        { type: 'alternative', confidence: 0.85, message: 'the agent used a model loop to search the repository', suggestion: 'use indexed project search or a registry lookup before spending model context', evidence: 'ask model to scan the whole repo for an existing csv parser' },
        { type: 'agentic_repeated_failure', confidence: 0.82, message: 'the same failure recurred 3 times: importerror', suggestion: 'stop retrying the same failing path; escalate or change strategy' },
      ], summary: { steps: 4, failures: 3, findings: 3, verdict: 'stalled_or_runaway' }, serves_truth: false });
      setSource('preview');
    } finally { setBusy(false); }
  }, []);

  const findings = run ? (run.report || []).map(mapServerFinding) : [];
  const s = run ? (run.summary || {}) : {};
  const verdict = s.verdict || '—';
  const runaway = verdict === 'stalled_or_runaway' || verdict === 'wasteful';
  return (
    <>
      <OhPageHead eyebrow="Agentic runs" title="Supervise an autonomous agent loop"
        sub="AIDevObserver watches autonomous agent loops (a flywheel / worker / any agent runner), not just human sessions. It flags thrash, stalls, repeated failures, budget overruns, and goal drift, and recommends a halt on a runaway. Read only — it never kills a process."
        actions={<button className="oh-btn oh-btn--primary" disabled={busy} onClick={supervise}>{busy ? 'Supervising…' : 'Supervise the example run →'}</button>} />
      {busy && <div className="ohl-empty">Supervising the run…</div>}
      {run && !busy && (
        <>
          {runaway && (
            <div className="ado-advisory" role="status">
              <span className="ado-advisory-i" aria-hidden="true">⟳</span>
              <div className="ado-advisory-b">
                <div className="ado-advisory-t">Runaway advisory: this run looks {verdict.replace(/_/g, ' ')}.</div>
                <div className="ado-advisory-d">A person should pause and redirect it. AIDevObserver never kills a process — it advises.</div>
              </div>
              <div className="ado-advisory-act">
                <button className="oh-btn oh-btn--ghost oh-btn--sm">Pause run</button>
                <button className="oh-btn oh-btn--ghost oh-btn--sm">Dismiss</button>
              </div>
            </div>
          )}
          <OhRollup items={[
            ['Verdict', verdict.replace(/_/g, ' ')],
            ['Steps', s.steps != null ? s.steps : '—'],
            ['Failures', s.failures != null ? s.failures : '—'],
            ['Source', source === 'live' ? 'live engine' : 'preview'],
          ]} />
          <FindingList report={findings} mapped outcomes={outcomes} onOutcome={onOutcome} />
        </>
      )}
      {!run && !busy && <div className="ohl-empty">Run the example to see how AIDevObserver supervises an autonomous loop.</div>}
    </>
  );
}

// /reports → Insights: a You / Team / Organization scope switcher over savings + reuse. Honest demo aggregates
// (clearly framed as illustrative until the metering seam lands), built from the kit's OhUsage primitive.
function AppReports() {
  const [scope, setScope] = React.useState('you');
  const SCOPES = [['you', 'You'], ['team', 'Team'], ['org', 'Organization']];
  const data = {
    you: { rollup: [['Sessions', 18], ['Findings', 41], ['Reuse rate', '54%'], ['Hours saved', '6.5']],
      bars: [.3, .5, .4, .7, .6, .8, .9] },
    team: { rollup: [['Sessions', 214], ['Findings', 512], ['Reuse rate', '47%'], ['Hours saved', '78']],
      bars: [.5, .6, .55, .7, .8, .75, .9] },
    org: { rollup: [['Sessions', 1380], ['Findings', 3120], ['Reuse rate', '44%'], ['Hours saved', '430']],
      bars: [.4, .5, .6, .65, .7, .85, .95] },
  }[scope];
  return (
    <>
      <OhPageHead eyebrow="Reports" title="Insights"
        sub="Where reinvention and context waste concentrate, which components are being reused, and where cheaper registry-backed paths are paying off. Aggregates are illustrative until the metering seam is wired (serves_truth = false)."
        actions={
          <div className="ado-scope">
            {SCOPES.map(([k, l]) => (
              <button key={k} className={'ado-scope-b' + (scope === k ? ' on' : '')} onClick={() => setScope(k)}>{l}</button>
            ))}
          </div>} />
      <OhUsage rollup={data.rollup} metrics={[
        { k: 'Sessions reviewed', v: data.rollup[0][1], bars: data.bars, hiLast: true },
        { k: 'Findings surfaced', v: data.rollup[1][1], bars: data.bars.slice().reverse(), hiLast: true },
        { k: 'Reuse accepted', v: data.rollup[2][1], bars: data.bars.map((b) => b * 0.8), hiLast: true },
      ]} />
      <div className="ohs-settings-sec" style={{ marginTop: 18 }}>
        <h3>Most-reinvented components</h3>
        <div className="oh-card oh-card--pad">
          <table className="oh-table">
            <thead><tr><th>Component</th><th>Already in</th><th>Times reinvented</th></tr></thead>
            <tbody>
              {[['CSV reader', 'utils.csv', 7], ['retry/backoff', 'utils.net', 5], ['date parsing', 'utils.time', 4], ['slugify', 'utils.text', 3]].map(([c, r, n]) => (
                <tr key={c}><td>{c}</td><td className="mono">{r}</td><td className="mono">{n}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

const INTELLIGENCE_TOGGLE_COPY = {
  global_primitives: ['Global primitive database', 'Search quality-gated reusable components generated from public and internal source acquisition.'],
  local_registry: ['Local helper/source search', 'Search local functions, classes, scripts, docs, and edge contracts when you opt in.'],
  local_sessions: ['Local session discovery', 'List local Claude Code / Codex sessions so you can review one from the browser.'],
  mcp: ['MCP intelligence', 'Expose the same review/search actions to Claude Code as governed MCP tools.'],
  plugins: ['Editor/plugin intelligence', 'Keep VS Code, Cursor, CLI, and browser reports on the same review format.'],
  live_hook: ['Live in-session hook', 'Allow non-blocking PreToolUse coaching while an agent is working.'],
  token_savings: ['Token savings estimates', 'Attach transparent avoided-token and avoided-model-call estimates to findings.'],
  llm_rerank: ['Kimi/GLM rerank', 'Let the selected model assist rerank candidate advice after registry search has produced grounded options.'],
};

function StatusPill({ value }) {
  const ok = value === 'ready' || value === true;
  return <span className={'ado-status-pill ' + (ok ? 'ok' : 'warn')}>{ok ? 'ready' : String(value || 'off').replace(/_/g, ' ')}</span>;
}

function StatusDot({ value }) {
  const ok = value === 'ready' || value === true;
  return <span className={'ado-status-dot ' + (ok ? 'ok' : 'warn')} title={ok ? 'ready' : String(value || 'off').replace(/_/g, ' ')} />;
}

function RouteDagView({ graph, recipe, run, components }) {
  const recipeNodes = Array.isArray(recipe?.nodes) ? recipe.nodes : [];
  const graphNodes = Array.isArray(graph?.nodes) ? graph.nodes : [];
  const sourceNodes = recipeNodes.length
    ? recipeNodes.map((node, idx) => ({
        id: node.id || ('node_' + idx),
        label: node.id || ('step ' + (idx + 1)),
        detail: node.primitive || node.component || 'primitive',
        edge: (node.input || 'input') + ' → ' + (node.output || 'output'),
        source: node.source_ref?.path ? (node.source_ref.path + (node.source_ref.name ? ' :: ' + node.source_ref.name : '')) : '',
        status: 'compiled',
      }))
    : graphNodes.map((node, idx) => ({
        id: node.id || ('node_' + idx),
        label: node.label || node.id || ('step ' + (idx + 1)),
        detail: node.detail || '',
        edge: node.status || 'candidate',
        source: '',
        status: node.status || 'candidate',
      }));
  const executionMode = run?.execution_mode || recipe?.execution_mode || graph?.execution_mode || '';
  const deterministic = executionMode === 'deterministic_template_worker';
  const aiTrace = run?.ai_trace || {};
  const plannerCalls = aiTrace.known_model_calls != null
    ? aiTrace.known_model_calls
    : recipe?.planner_model_calls != null
      ? recipe.planner_model_calls
      : recipe?.model_calls != null && typeof recipe.model_calls === 'number'
        ? recipe.model_calls
        : 0;
  const selected = Array.isArray(components) ? components : [];
  const runtimeTarget = recipe?.runtime_target || graph?.runtime_target || {};
  return (
    <div className="ado-dag-view">
      <div className="ado-dag-meta">
        <div>
          <span className="ado-plan-k">Route graph</span>
          <b>{recipeNodes.length ? 'Compiled primitive recipe' : 'Observer route trace'}</b>
        </div>
        <em>{deterministic ? ('planner: ' + plannerCalls + ' · harness: 0') : 'harness fallback'}</em>
      </div>
      {runtimeTarget.target ? (
        <div className="ado-dag-meta compact">
          <div>
            <span className="ado-plan-k">Runtime target</span>
            <b>{runtimeTarget.target}</b>
            <small>{runtimeTarget.trigger || 'cli'} · {runtimeTarget.reason || 'runtime inferred from task and route'}</small>
          </div>
        </div>
      ) : null}
      {sourceNodes.length ? (
        <div className="ado-dag-stage">
          {sourceNodes.map((node, idx) => (
            <div className="ado-dag-node" key={node.id}>
              <div className="ado-dag-index">{idx + 1}</div>
              <div className="ado-dag-card">
                <div className="ado-dag-node-top">
                  <b>{node.label}</b>
                  <span>{node.status}</span>
                </div>
                {node.edge ? <code>{node.edge}</code> : null}
                {node.detail ? <small>{node.detail}</small> : null}
                {node.source ? <small className="mono">{node.source}</small> : null}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="ado-graph-empty">
          <b>No graph yet</b>
          <span>Type a concrete build task. AIDevObserver will show the selected route here when it finds one.</span>
        </div>
      )}
      {selected.length ? (
        <div className="ado-dag-selected">
          <span className="ado-plan-k">Selected edges</span>
          {selected.slice(0, 5).map((component, idx) => {
            const contract = component.contract || {};
            return (
              <div key={idx}>
                <b>{component.label}</b>
                <small>{contract.input || 'input'} → {contract.output || 'output'}</small>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

function parseWorkspaceJson(files, targetPath) {
  const file = (Array.isArray(files) ? files : []).find((item) => item.path === targetPath);
  if (!file) return null;
  try {
    return JSON.parse(String(file.content || '{}'));
  } catch (e) {
    return null;
  }
}

function fallbackProcessPhases(plan, run, busy) {
  if (!plan && !busy) return [];
  if (!plan && busy) {
    return [
      { id: 'task_received', label: 'Task received', status: 'done', detail: 'Your terminal prompt was submitted to AIDevObserver.' },
      { id: 'registry_search', label: 'Registry search', status: 'running', detail: 'Searching primitive input/output edges and reusable templates.' },
      { id: 'planner_tool_loop', label: 'Planner tool loop', status: 'pending', detail: 'Kimi/GLM may call compact registry tools if the route is not obvious.' },
      { id: 'route_compiled', label: 'Route compiled', status: 'pending', detail: 'Compiler will order selected components into a recipe/DAG.' },
      { id: 'workspace_materialized', label: 'Workspace written', status: 'pending', detail: 'Generated entry point, recipe, report, and manifest will be written.' },
      { id: 'primitive_snapshots', label: 'Primitive code copied', status: 'pending', detail: 'Selected primitive modules will be copied into the workspace.' },
      { id: 'smoke_tests', label: 'Behavior tests prepared', status: 'pending', detail: 'Generated happy-path and edge-case fixture tests run after files are materialized.' },
      { id: 'runtime_emitters', label: 'Runtime emitters prepared', status: 'pending', detail: 'Local, HTTP, container, Kubernetes, and cloud-function wrappers are generated after route compile.' },
      { id: 'coding_harness', label: 'Coding harness', status: 'pending', detail: 'Only starts if deterministic compilation cannot finish the task.' },
    ];
  }
  const executionMode = run?.execution_mode || plan?.execution_mode || '';
  const aiTrace = run?.ai_trace || plan?.ai_trace || {};
  const plannerTrace = aiTrace.route_planning || {};
  const recipe = run?.recipe || plan?.recipe || {};
  const nodes = Array.isArray(recipe?.nodes) ? recipe.nodes : [];
  const selected = Array.isArray(plan?.selected_components) ? plan.selected_components : [];
  const workspaceFiles = Array.isArray(plan?.workspace_files) ? plan.workspace_files : [];
  const primitiveModules = workspaceFiles.filter((file) => String(file.path || '').startsWith('primitives/') && String(file.path || '').endsWith('.py') && !String(file.path || '').endsWith('__init__.py'));
  const runtimeFiles = workspaceFiles.filter((file) => String(file.path || '').startsWith('runtime/') || String(file.path || '').startsWith('deploy/') || String(file.path || '') === 'Dockerfile');
  return [
    { id: 'task_received', label: 'Task received', status: busy ? 'running' : 'done', detail: plan ? 'Build task accepted.' : 'Waiting for service response.' },
    { id: 'registry_search', label: 'Registry search', status: selected.length ? 'done' : (busy ? 'running' : 'skipped'), detail: selected.length + ' selected edge match' + (selected.length === 1 ? '' : 'es') },
    { id: 'planner_tool_loop', label: 'Planner tool loop', status: plannerTrace.status === 'used' ? 'done' : 'skipped', detail: plannerTrace.status === 'used' ? (plannerTrace.model || 'planner') + ' · ' + (plannerTrace.model_calls || 0) + ' call' + ((plannerTrace.model_calls || 0) === 1 ? '' : 's') : 'Skipped or not needed.' },
    { id: 'route_compiled', label: 'Route compiled', status: nodes.length ? 'done' : (busy ? 'running' : 'skipped'), detail: nodes.length + ' recipe node' + (nodes.length === 1 ? '' : 's') },
    { id: 'workspace_materialized', label: 'Workspace written', status: workspaceFiles.length ? 'done' : (busy ? 'running' : 'skipped'), detail: workspaceFiles.length + ' file' + (workspaceFiles.length === 1 ? '' : 's') },
    { id: 'primitive_snapshots', label: 'Primitive code copied', status: primitiveModules.length ? 'done' : (busy ? 'running' : 'skipped'), detail: primitiveModules.length + ' module' + (primitiveModules.length === 1 ? '' : 's') },
    { id: 'smoke_tests', label: 'Behavior tests prepared', status: workspaceFiles.some((file) => String(file.path || '').startsWith('tests/')) ? 'done' : (busy ? 'running' : 'skipped'), detail: workspaceFiles.filter((file) => String(file.path || '').startsWith('tests/')).length + ' generated test file' + (workspaceFiles.filter((file) => String(file.path || '').startsWith('tests/')).length === 1 ? '' : 's') },
    { id: 'runtime_emitters', label: 'Runtime emitters prepared', status: runtimeFiles.length ? 'done' : (busy ? 'running' : 'skipped'), detail: runtimeFiles.length + ' runtime/deploy artifact' + (runtimeFiles.length === 1 ? '' : 's') },
    { id: 'coding_harness', label: 'Coding harness', status: executionMode === 'coding_harness_fallback' ? 'running' : 'skipped', detail: executionMode === 'deterministic_template_worker' ? 'Skipped: deterministic worker completed the route.' : 'Used only for unresolved glue.' },
  ];
}

function ProcessPhaseList({ phases }) {
  const rows = Array.isArray(phases) ? phases : [];
  if (!rows.length) return null;
  const finished = rows.filter((phase) => phase.status === 'done' || phase.status === 'skipped').length;
  return (
    <div className="ado-process-list">
      <div className="ado-graph-subhead">
        <span>Process</span>
        <b>{finished}/{rows.length}</b>
      </div>
      {rows.map((phase) => (
        <div className={'ado-process-row ' + (phase.status || 'pending')} key={phase.id || phase.label}>
          <span className="ado-process-dot" />
          <div>
            <b>{phase.label || phase.id}</b>
            <small>{phase.detail || phase.status || 'pending'}</small>
          </div>
          <em>{phase.status || 'pending'}</em>
        </div>
      ))}
    </div>
  );
}

function RunGraphPanel({ plan, run, busy, observerLatest, observerHistory, panelView, setPanelView, onOpenPlan, onExportJson, onExportMarkdown }) {
  const graph = plan?.run_graph || {};
  const components = Array.isArray(graph.components) ? graph.components : [];
  const actionableComponents = components.filter((component) => {
    const fit = String(component.edge_fit || '').toLowerCase();
    return fit && fit !== 'query_only' && fit !== 'candidate';
  });
  const commands = Array.isArray(plan?.commands) ? plan.commands : [];
  const harnesses = Array.isArray(plan?.harnesses) ? plan.harnesses : [];
  const models = Array.isArray(plan?.models) ? plan.models : [];
  const runStatus = run?.status || '';
  const hasRun = Boolean(run?.run_id);
  const executionMode = run?.execution_mode || plan?.execution_mode || graph.execution_mode || '';
  const deterministic = executionMode === 'deterministic_template_worker';
  const needsTask = executionMode === 'needs_build_task';
  const recipe = run?.recipe || plan?.recipe || null;
  const browserRoute = recipe?.template === 'template.web.browser_table.extract.persist@candidate';
  const aiTrace = run?.ai_trace || plan?.ai_trace || {};
  const intentTrace = aiTrace.intent_interpretation || {};
  const plannerTrace = aiTrace.route_planning || {};
  const codeTrace = aiTrace.code_generation || {};
  const plannerUsed = plannerTrace.status === 'used';
  const plannerToolCalls = Array.isArray(plannerTrace.tool_calls) ? plannerTrace.tool_calls : [];
  const plannerToolResults = Array.isArray(plannerTrace.tool_results) ? plannerTrace.tool_results : [];
  const knownModelCalls = aiTrace.known_model_calls != null ? aiTrace.known_model_calls : (plannerTrace.model_calls || 0);
  const recipeNodes = Array.isArray(recipe?.nodes) ? recipe.nodes : [];
  const proofs = Array.isArray(run?.proofs) ? run.proofs : [];
  const workspaceFiles = Array.isArray(plan?.workspace_files) ? plan.workspace_files : [];
  const manifest = parseWorkspaceJson(workspaceFiles, 'build_manifest.json') || {};
  const routeQuality = run?.route_quality || plan?.route_quality || manifest.route_quality || {};
  const tokenSavings = run?.token_savings || plan?.token_savings || manifest.token_savings || {};
  const runtimeTarget = run?.runtime_target || plan?.runtime_target || manifest.runtime_target || {};
  const fallbackStrategy = run?.fallback_strategy || plan?.fallback_strategy || manifest.fallback_strategy || {};
  const processPhases = Array.isArray(manifest.process_phases) ? manifest.process_phases : fallbackProcessPhases(plan, run, busy);
  const generatedAppFiles = workspaceFiles.filter((file) => String(file.path || '').startsWith('app/'));
  const generatedTestFiles = workspaceFiles.filter((file) => String(file.path || '').startsWith('tests/') && String(file.path || '').endsWith('.py'));
  const primitiveSnapshotFiles = workspaceFiles.filter((file) => String(file.path || '').startsWith('primitives/'));
  const primitiveModules = primitiveSnapshotFiles.filter((file) => String(file.path || '').endsWith('.py') && !String(file.path || '').endsWith('__init__.py'));
  const runtimeFiles = workspaceFiles.filter((file) => String(file.path || '').startsWith('runtime/') || String(file.path || '').startsWith('deploy/') || String(file.path || '') === 'Dockerfile');
  const edgeAdapterPlan = workspaceFiles.find((file) => file.path === 'edge_adapter_plan.json');
  const sourceSnapshots = Array.isArray(manifest.source_snapshots) ? manifest.source_snapshots : [];
  const smokeProofs = proofs.filter((proof) => String(proof.id || '').startsWith('smoke_test:'));
  const visibleProofs = smokeProofs
    .concat(proofs.filter((proof) => !String(proof.id || '').startsWith('smoke_test:')))
    .slice(0, 8);
  const latest = Array.isArray(observerLatest) ? observerLatest : [];
  const history = Array.isArray(observerHistory) ? observerHistory : [];
  return (
    <aside className="ado-ide-graph" aria-label="AIDevObserver panel">
      <div className="ado-ide-graph-head">
        <div>
          <div className="ado-ide-pane-title">AIDevObserver</div>
          <p>{plan ? 'Status only. Components are selected automatically.' : 'Quiet until there is something to report.'}</p>
        </div>
        <div className="ado-graph-head-actions">
          <button disabled={!plan} onClick={onOpenPlan}>{plan ? 'Details' : 'Idle'}</button>
          <button disabled={!plan} onClick={onExportJson}>Export</button>
        </div>
      </div>
      <div className="ado-observer-output">
        <div className="ado-graph-subhead">
          <span>Latest</span>
          <button disabled={!plan} onClick={onExportMarkdown}>Export MD</button>
        </div>
        {latest.length ? (
          <div className="ado-observer-output-log mono">
            {latest.map((line, idx) => <div key={idx}>{line}</div>)}
          </div>
        ) : (
          <div className="ado-observer-output-empty">Search, selected routes, recipes, proofs, and fallback notes appear here. The terminal stays reserved for your input and harness output.</div>
        )}
        {history.length > latest.length ? (
          <details className="ado-observer-history">
            <summary>History ({history.length})</summary>
            <div className="ado-observer-output-log mono">
              {history.map((line, idx) => <div key={idx}>{line}</div>)}
            </div>
          </details>
        ) : null}
      </div>
      {!plan && !busy ? (
        <div className="ado-observer-placeholder">
          <b>Nothing flagged yet</b>
          <span>Route matches, compiled files, fallback status, findings, and token-savings notes will show here when AIDevObserver has something useful to report.</span>
        </div>
      ) : null}
      {busy ? (
        <div className="ado-observer-card">
          <span className="ado-plan-k">Running</span>
          <b>Checking reusable routes</b>
          <small>Searching primitives, matching input/output edges, and compiling the route deterministically when the match is strong enough.</small>
          <div className="ado-progress-track" aria-label="AIDevObserver is running">
            <span />
          </div>
        </div>
      ) : null}
      {busy && !plan ? <ProcessPhaseList phases={processPhases} /> : null}
      {plan ? (
        <div className="ado-view-tabs" role="tablist" aria-label="AIDevObserver panel view">
          <button className={panelView === 'summary' ? 'on' : ''} onClick={() => setPanelView('summary')}>Summary</button>
          <button className={panelView === 'graph' ? 'on' : ''} onClick={() => setPanelView('graph')}>Graph</button>
        </div>
      ) : null}
      {plan && panelView === 'graph' ? (
        <RouteDagView graph={graph} recipe={recipe} run={run} components={actionableComponents} />
      ) : null}
      {plan && panelView === 'summary' ? (
        <>
          <ProcessPhaseList phases={processPhases} />
          <div className={'ado-build-origin ' + (needsTask ? 'idle' : deterministic ? 'deterministic' : 'harness')}>
            <span className="ado-plan-k">Build source</span>
            <b>{
              needsTask
                ? 'No build started'
                : deterministic
                  ? 'Built from reusable primitives without codegen'
                  : plannerUsed
                    ? 'Planner LLM selected a route from registry tool results'
                  : 'Needs coding harness fallback'
            }</b>
            <small>{
              needsTask
                ? 'AIDevObserver ignored the input because it was not a concrete build/review task.'
                : deterministic
                  ? 'The planner may use Kimi/GLM to choose the route, but the implementation files are materialized by a deterministic template worker. Coding harness calls: 0.'
                : plannerUsed
                    ? 'Kimi/GLM requested compact registry searches, saw input/output edge cards, and returned an ordered candidate route. The compiler still owns validation before any harness work.'
                  : 'A model-assisted harness will receive compact edge summaries only for missing glue or new component definitions.'
            }</small>
          </div>
          <div className="ado-metric-grid">
            <div className="ado-metric-card">
              <span className="ado-plan-k">Route quality</span>
              <b>{routeQuality.score != null ? routeQuality.score + '/100' : 'pending'}</b>
              <small>{(routeQuality.label || 'candidate').replace(/_/g, ' ')} · {routeQuality.exact_edge_matches || 0} exact edges · {routeQuality.recipe_nodes || recipeNodes.length} nodes</small>
            </div>
            <div className="ado-metric-card">
              <span className="ado-plan-k">Tokens avoided</span>
              <b>{tokenSavings.estimated_tokens_avoided != null ? tokenSavings.estimated_tokens_avoided : 0}</b>
              <small>source-read estimate: {tokenSavings.estimated_source_tokens_if_read || 0} · compact packet: {tokenSavings.compact_route_packet_tokens || 0}</small>
            </div>
            <div className="ado-metric-card">
              <span className="ado-plan-k">Runtime target</span>
              <b>{runtimeTarget.target || 'local.python'}</b>
              <small>{runtimeTarget.trigger || 'cli'} · {runtimeTarget.reason || 'default local route'}</small>
            </div>
            <div className="ado-metric-card">
              <span className="ado-plan-k">Fallback</span>
              <b>{fallbackStrategy.needed ? 'Kimi/GLM harness ready' : 'not needed'}</b>
              <small>{fallbackStrategy.context_policy || 'compact edge context only'}</small>
            </div>
          </div>
          {workspaceFiles.length ? (
            <div className="ado-observer-card">
              <span className="ado-plan-k">Workspace code</span>
              <b>{generatedAppFiles.length} generated app file{generatedAppFiles.length === 1 ? '' : 's'} · {generatedTestFiles.length} test file{generatedTestFiles.length === 1 ? '' : 's'} · {primitiveModules.length} primitive module{primitiveModules.length === 1 ? '' : 's'} copied · {runtimeFiles.length} runtime/deploy artifact{runtimeFiles.length === 1 ? '' : 's'}</b>
              <small>The generated app imports workspace-local snapshots under <span className="mono">primitives/teleon/...</span>, so the reusable code is visible in Explorer.</small>
              {generatedAppFiles[0]?.path ? <small>Open <span className="mono">{generatedAppFiles[0].path}</span> for the assembled entry point.</small> : null}
              {generatedTestFiles[0]?.path ? <small>Open <span className="mono">{generatedTestFiles[0].path}</span> for generated behavior tests.</small> : null}
              {runtimeFiles[0]?.path ? <small>Open <span className="mono">{runtimeFiles[0].path}</span> for generated local/container/Kubernetes/cloud-function wrappers.</small> : null}
              {edgeAdapterPlan ? <small>Open <span className="mono">edge_adapter_plan.json</span> for reusable edge adapters and primitive-gap candidates.</small> : null}
              {sourceSnapshots.slice(0, 3).map((snapshot) => (
                <small className="mono" key={snapshot.workspace_path || snapshot.source_path}>
                  {snapshot.source_path} → {snapshot.workspace_path}
                </small>
              ))}
            </div>
          ) : null}
          <div className="ado-observer-card">
            <span className="ado-plan-k">Model use</span>
            <b>{knownModelCalls} known model call{knownModelCalls === 1 ? '' : 's'}</b>
            <small>Intent: {(intentTrace.lane || 'unknown').replace(/_/g, ' ')} · calls: {intentTrace.model_calls ?? 0}</small>
            <small>Planner: {(plannerTrace.status || 'skipped').replace(/_/g, ' ')}{plannerTrace.model ? ' · ' + plannerTrace.model : ''} · calls: {plannerTrace.model_calls ?? 0}</small>
            <small>Codegen: {(codeTrace.lane || 'none').replace(/_/g, ' ')} · calls: {codeTrace.model_calls ?? 0}</small>
          </div>
          {fallbackStrategy.model_order?.length ? (
            <div className="ado-observer-card">
              <span className="ado-plan-k">Model fallback order</span>
              <b>{fallbackStrategy.model_order.map((item) => item.key === 'glm' ? 'GLM' : 'Kimi').join(' → ')}</b>
              <small>{fallbackStrategy.coding_harness_scope || 'coding harness writes only missing glue/new candidates'}</small>
              {Array.isArray(fallbackStrategy.planner_attempts) && fallbackStrategy.planner_attempts.length
                ? <small>{fallbackStrategy.planner_attempts.length} planner attempt{fallbackStrategy.planner_attempts.length === 1 ? '' : 's'} recorded</small>
                : null}
            </div>
          ) : null}
          {plannerToolCalls.length || plannerToolResults.length ? (
            <div className="ado-observer-card">
              <span className="ado-plan-k">Planner tools</span>
              <b>{plannerToolCalls.length || plannerToolResults.length} registry tool call{(plannerToolCalls.length || plannerToolResults.length) === 1 ? '' : 's'}</b>
              {plannerToolResults.slice(0, 3).map((result, idx) => (
                <small key={idx}>
                  {(result.tool || 'registry tool').replace(/_/g, ' ')}
                  {' · '}
                  {result.status || 'candidate'}
                  {' · '}
                  {result.component_count || 0} edge card{Number(result.component_count || 0) === 1 ? '' : 's'}
                </small>
              ))}
              {plannerTrace.route?.nodes?.length ? <small>Route nodes: {plannerTrace.route.nodes.length}</small> : null}
            </div>
          ) : null}
          <div className="ado-observer-card">
            <span className="ado-plan-k">What happened</span>
            <b>{
              needsTask
                ? 'No run started'
                :
              deterministic
                ? (runStatus ? 'Deterministic route ' + runStatus : 'Deterministic route selected')
                : (runStatus === 'running' ? 'Harness fallback is running' : runStatus ? 'Harness fallback ' + runStatus : 'Harness fallback prepared')
            }</b>
            <small>{
              needsTask
                ? 'Type a concrete build, review, extraction, migration, scraping, classification, or pipeline task to start AIDevObserver.'
                :
              deterministic
                ? 'AIDevObserver selected reusable primitive edges and materialized the workspace without code generation. Nothing here requires a manual component choice.'
                : 'AIDevObserver sends only compact selected edge summaries to the coding harness when missing glue or custom code is needed.'
            }</small>
          </div>
          <div className="ado-observer-card">
            <span className="ado-plan-k">Execution</span>
            <b>{needsTask ? 'Idle' : deterministic ? 'Template worker' : (harnesses.join(', ') || 'No harness selected')}</b>
            <small>{needsTask ? 'No model call · no harness run' : deterministic ? 'Planner model calls: ' + knownModelCalls + ' · coding harness: not invoked' : (models.length ? 'Model assist: ' + ideModelListLabel(models) : 'No model assist selected')}</small>
            <small>{needsTask ? 'AIDevObserver is waiting for a task with build intent.' : deterministic ? 'Selected primitive edges were compiled into files.' : 'Selected primitive edges are provided as compact harness context.'}</small>
            {run?.run_id ? <small className="mono">run: {run.run_id}</small> : null}
            {hasRun && runStatus ? <small className="mono">status: {runStatus}</small> : null}
            {commands[0]?.command ? <code className="mono">{commands[0].command}</code> : null}
          </div>
          {browserRoute ? (
            <div className="ado-observer-card">
              <span className="ado-plan-k">Browser setup</span>
              <b>Playwright-capable browser table route</b>
              <small>The generated flow imports <span className="mono">fetch_page_html_with_playwright</span>. It launches Chromium when Playwright is installed and falls back to static HTTP fetch for simple pages.</small>
              <small>Open <span className="mono">app/browser_table_export_flow.py</span> to see the importable function that writes CSV and Parquet artifacts.</small>
            </div>
          ) : null}
          {recipeNodes.length ? (
            <div className="ado-graph-components">
              <div className="ado-graph-subhead">
                <span>Compiled recipe</span>
                <b>{recipeNodes.length}</b>
              </div>
              {recipeNodes.map((node) => (
                <div className="ado-graph-card" key={node.id}>
                  <b>{node.id}</b>
                  <span>{node.input || 'input'} → {node.output || 'output'}</span>
                  <small>{node.primitive || node.component}</small>
                  {node.source_ref?.path ? <small>{node.source_ref.path} :: {node.source_ref.name}</small> : null}
                </div>
              ))}
            </div>
          ) : null}
          {proofs.length ? (
            <div className="ado-graph-components">
              <div className="ado-graph-subhead">
                <span>Proof checks</span>
                <b>{proofs.filter((proof) => proof.status === 'pass').length}/{proofs.length}</b>
              </div>
              {visibleProofs.map((proof) => (
                <div className="ado-graph-card" key={proof.id}>
                  <b>{proof.id}</b>
                  <span>{proof.status}</span>
                  <small>{proof.detail}</small>
                </div>
              ))}
            </div>
          ) : null}
          {actionableComponents.length ? (
            <div className="ado-graph-components">
              <div className="ado-graph-subhead">
                <span>Actionable matches</span>
                <b>{actionableComponents.length}</b>
              </div>
              {actionableComponents.slice(0, 4).map((component, idx) => {
                const contract = component.contract || {};
                const sourceRef = component.source_ref || {};
                const source = [sourceRef.path, sourceRef.name].filter(Boolean).join(' :: ');
                const mutations = Array.isArray(component.mutations) ? component.mutations : [];
                const reasons = Array.isArray(component.selection_reasons) ? component.selection_reasons : [];
                return (
                  <div className="ado-graph-card" key={idx}>
                    <b>{component.label}</b>
                    <span>{contract.input || 'unknown'} → {contract.output || 'unknown'}</span>
                    <small>{component.edge_fit || 'candidate'}{mutations.length ? ' · mutates: ' + mutations.map((m) => m.id || m).join(', ') : ''}</small>
                    {source && <small>{source}</small>}
                    {reasons.slice(0, 2).map((reason, reasonIdx) => <small key={reasonIdx}>why: {reason}</small>)}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="ado-observer-card">
              <span className="ado-plan-k">Registry search</span>
              <b>{needsTask ? 'Not searched' : 'No reusable route selected'}</b>
              <small>{
                needsTask
                  ? 'Search is skipped for greetings and status text.'
                  : 'Only weak matches were found, so AIDevObserver will use the harness fallback and record the gap as a candidate primitive opportunity.'
              }</small>
            </div>
          )}
        </>
      ) : null}
    </aside>
  );
}

function ModelLaneCard({ lane, selected, onSelect, disabled }) {
  return (
    <button className={'ado-model-card' + (selected ? ' on' : '')}
      disabled={disabled} onClick={() => onSelect(lane.key)}>
      <div className="ado-model-top">
        <span className="ado-model-title">{lane.title}</span>
        <StatusPill value={lane.status} />
      </div>
      <div className="ado-model-id mono">{lane.model}</div>
      <p>{lane.role}</p>
      <div className="ado-model-meta mono">
        <span>{lane.provider}</span>
        {lane.cloud_ready != null ? <span>cloud:{lane.cloud_ready ? 'connected' : 'needs key'}</span> : null}
        {lane.local_ready != null ? <span>local:{lane.local_ready ? 'model found' : 'not found'}</span> : null}
      </div>
    </button>
  );
}

function ToggleRow({ id, on, onToggle, disabled }) {
  const [title, desc] = INTELLIGENCE_TOGGLE_COPY[id] || [id, ''];
  return (
    <div className="ado-toggle-row">
      <div>
        <div className="ado-toggle-title">{title}</div>
        <div className="ado-toggle-desc">{desc}</div>
      </div>
      <OhSwitch on={!!on} onToggle={disabled ? (() => {}) : onToggle} />
    </div>
  );
}

function ideModelListLabel(values) {
  const xs = Array.isArray(values) ? values : [];
  const labels = xs.filter((key) => key === 'kimi' || key === 'glm').map((key) => (key === 'kimi' ? 'Kimi' : 'GLM'));
  return labels.length ? labels.join(', ') : 'Kimi';
}

function idePlanFiles(plan, task, overrides) {
  if (!plan && !String(task || '').trim()) return [];
  const files = Array.isArray(plan?.workspace_files) && plan.workspace_files.length
    ? plan.workspace_files
    : [{ path: 'task.md', language: 'markdown', content: '# Task\n\n' + String(task || '').trim() + '\n' }];
  return files.map((file) => ({
    ...file,
    content: overrides?.[file.path] != null ? overrides[file.path] : file.content,
  }));
}

function ideFileIcon(path) {
  if (String(path).endsWith('.py')) return '🐍';
  if (String(path).endsWith('.json')) return '{}';
  if (String(path).endsWith('.txt')) return '≡';
  if (String(path).endsWith('.md')) return '▤';
  if (String(path).endsWith('.yaml') || String(path).endsWith('.yml')) return '☸';
  if (String(path) === 'Dockerfile') return '▣';
  return '□';
}

function ideFileGroups(files) {
  const groups = [
    ['root', 'Workspace'],
    ['app', 'Generated app'],
    ['tests', 'Tests'],
    ['primitives', 'Primitive snapshots'],
    ['runtime', 'Runtime wrappers'],
    ['deploy', 'Deploy manifests'],
    ['reports', 'Reports'],
  ];
  const buckets = new Map(groups.map(([key, label]) => [key, { key, label, files: [] }]));
  (Array.isArray(files) ? files : []).forEach((file) => {
    const path = String(file.path || '');
    let key = 'root';
    if (path.startsWith('app/')) key = 'app';
    else if (path.startsWith('tests/')) key = 'tests';
    else if (path.startsWith('primitives/')) key = 'primitives';
    else if (path.startsWith('runtime/')) key = 'runtime';
    else if (path.startsWith('deploy/') || path === 'Dockerfile') key = 'deploy';
    else if (path.endsWith('.json') || path.includes('report') || path.includes('manifest')) key = 'reports';
    buckets.get(key).files.push(file);
  });
  return Array.from(buckets.values()).filter((group) => group.files.length);
}

function downloadTextFile(name, mime, text) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function ideSessionMarkdown(snapshot) {
  const files = Array.isArray(snapshot.workspace_files) ? snapshot.workspace_files : [];
  const latest = Array.isArray(snapshot.observer_latest) ? snapshot.observer_latest : [];
  const observer = Array.isArray(snapshot.observer_output) ? snapshot.observer_output : [];
  const terminal = Array.isArray(snapshot.terminal_output) ? snapshot.terminal_output : [];
  const recipe = snapshot.plan?.recipe || snapshot.run?.recipe || null;
  const proofs = Array.isArray(snapshot.run?.proofs) ? snapshot.run.proofs : [];
  const aiTrace = snapshot.run?.ai_trace || snapshot.plan?.ai_trace || {};
  return [
    '# AIDevObserver IDE Session Export',
    '',
    '## Task',
    '',
    snapshot.task || '',
    '',
    '## Runtime',
    '',
    '- Session: `' + (snapshot.session_id || 'unsaved') + '`',
    '- Models: `' + (snapshot.models || []).join(', ') + '`',
    '- Harnesses: `' + (snapshot.harnesses || []).join(', ') + '`',
    '- Execution mode: `' + (snapshot.run?.execution_mode || snapshot.plan?.execution_mode || 'none') + '`',
    '- Run status: `' + (snapshot.run?.status || 'none') + '`',
    '- Known model calls: `' + (aiTrace.known_model_calls ?? 0) + '`',
    '',
    '## AI Trace',
    '',
    '```json',
    JSON.stringify(aiTrace || {}, null, 2),
    '```',
    '',
    '## Latest Observer Output',
    '',
    latest.length ? latest.map((line) => '- ' + line).join('\n') : '_No latest observer output yet._',
    '',
    '## Observer History',
    '',
    observer.length ? observer.map((line) => '- ' + line).join('\n') : '_No observer output yet._',
    '',
    '## Terminal Output',
    '',
    '```text',
    terminal.join('\n'),
    '```',
    '',
    recipe ? '## Recipe\n\n```json\n' + JSON.stringify(recipe, null, 2) + '\n```' : '## Recipe\n\n_No recipe yet._',
    '',
    proofs.length ? '## Proofs\n\n' + proofs.map((proof) => '- `' + proof.id + '`: ' + proof.status + ' - ' + proof.detail).join('\n') : '## Proofs\n\n_No proof checks yet._',
    '',
    '## Workspace Files',
    '',
    files.length ? files.map((file) => [
      '### `' + file.path + '`',
      '',
      '```' + (file.language || ''),
      String(file.content || ''),
      '```',
    ].join('\n')).join('\n\n') : '_No workspace files yet._',
    '',
  ].join('\n');
}

function AppIDE({ sessionId, fullscreen, onFullscreenToggle }) {
  const [cfg, setCfg] = React.useState(null);
  const [err, setErr] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [plan, setPlan] = React.useState(null);
  const [run, setRun] = React.useState(null);
  const [currentSessionId, setCurrentSessionId] = React.useState(sessionId || '');
  const [shareUrl, setShareUrl] = React.useState('');
  const [recent, setRecent] = React.useState([]);
  const [task, setTask] = React.useState('');
  const [terminalInput, setTerminalInput] = React.useState('');
  const [terminalLines, setTerminalLines] = React.useState(['IDE terminal ready. Type a task and press Enter.']);
  const [observerLatest, setObserverLatest] = React.useState([]);
  const [observerHistory, setObserverHistory] = React.useState([]);
  const [activeFile, setActiveFile] = React.useState('task.md');
  const [fileOverrides, setFileOverrides] = React.useState({});
  const [models, setModels] = React.useState(['kimi', 'glm']);
  const [harnesses, setHarnesses] = React.useState(['opencode']);
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const [settingsTab, setSettingsTab] = React.useState('models');
  const [activeActivity, setActiveActivity] = React.useState('explorer');
  const [panelView, setPanelView] = React.useState('summary');
  const load = React.useCallback(async () => {
    setErr('');
    try {
      const res = await fetch('/api/observer/config', { cache: 'no-store' });
      if (!res.ok) throw new Error('observer config status ' + res.status);
      const data = await res.json();
      setCfg(data);
      setHarnesses(Array.isArray(data.enabled_harnesses) && data.enabled_harnesses.length ? data.enabled_harnesses : ['opencode']);
      const recentRes = await fetch('/api/observer/ide/sessions?limit=8', { cache: 'no-store' });
      if (recentRes.ok) {
        const recentData = await recentRes.json();
        setRecent(Array.isArray(recentData.sessions) ? recentData.sessions : []);
      }
    } catch (e) {
      setErr('The observer service is not reachable yet. Start it, then refresh this page.');
    }
  }, []);
  React.useEffect(() => { load(); }, [load]);
  React.useEffect(() => {
    if (!sessionId) return;
    let live = true;
    setErr('');
    fetch('/api/observer/ide/session/' + encodeURIComponent(sessionId), { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => {
        if (!live) return;
        const s = data.session || {};
        setCurrentSessionId(s.session_id || sessionId);
        setTask(s.task || '');
        const savedModels = (s.models || []).filter((m) => m === 'kimi' || m === 'glm');
        setModels(savedModels.length ? savedModels : ['kimi', 'glm']);
        setHarnesses((s.harnesses || []).length ? s.harnesses : ['opencode']);
        setPlan(s.plan || null);
        setRun(s.run || null);
        const savedObserver = Array.isArray(s.observer_output) ? s.observer_output : [];
        const savedLatest = Array.isArray(s.observer_latest) ? s.observer_latest : savedObserver;
        setObserverLatest(savedLatest);
        setObserverHistory(savedObserver.length ? savedObserver : savedLatest);
        setTerminalLines(Array.isArray(s.terminal_output) && s.terminal_output.length ? s.terminal_output : ['IDE terminal ready. Type a task and press Enter.']);
        setFileOverrides(s.workspace_overrides || {});
        setShareUrl(s.share_url ? window.location.origin + s.share_url : '');
      })
      .catch(() => { if (live) setErr('That saved IDE session was not found on this running machine.'); });
    return () => { live = false; };
  }, [sessionId]);
  React.useEffect(() => {
    if (sessionId) return;
    setCurrentSessionId('');
    setShareUrl('');
    setPlan(null);
    setRun(null);
    setObserverLatest([]);
    setObserverHistory([]);
    setFileOverrides({});
    setActiveFile('task.md');
    setActiveActivity('explorer');
    setPanelView('summary');
  }, [sessionId]);
  React.useEffect(() => {
    const files = idePlanFiles(plan, task, fileOverrides);
    if (!files.some((file) => file.path === activeFile)) {
      setActiveFile((files.find((file) => String(file.path).endsWith('.py')) || files[0] || { path: 'task.md' }).path);
    }
  }, [activeFile, fileOverrides, plan, task]);
  const toggleModel = (key) => {
    setModels((xs) => {
      const next = xs.includes(key) ? xs.filter((x) => x !== key) : xs.concat(key);
      return next.length ? next : ['kimi'];
    });
  };
  const toggleHarness = (key) => {
    setHarnesses((xs) => xs.includes(key) ? xs.filter((x) => x !== key) : xs.concat(key));
  };
  const openSettings = React.useCallback((tab) => {
    setSettingsTab(tab || 'models');
    setSettingsOpen(true);
  }, []);
  const updateToggle = React.useCallback(async (key) => {
    if (!cfg) return;
    const nextToggles = { ...(cfg.toggles || {}), [key]: !cfg.toggles?.[key] };
    const nextCfg = { ...cfg, toggles: nextToggles };
    setCfg(nextCfg);
    fetch('/api/observer/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_provider: ['kimi', 'glm'].includes(cfg.model_provider) ? cfg.model_provider : (models[0] || 'kimi'),
        toggles: nextToggles,
      }),
    }).catch(() => setErr('Could not update the running observer config.'));
  }, [cfg]);
  const appendObserverEvent = React.useCallback((lines) => {
    const normalized = (Array.isArray(lines) ? lines : [lines])
      .map((line) => String(line || '').trim())
      .filter(Boolean);
    if (!normalized.length) return;
    setObserverLatest(normalized);
    setObserverHistory((xs) => xs.concat(normalized));
  }, []);
  React.useEffect(() => {
    if (!run?.run_id || run.status !== 'running') return;
    let live = true;
    const timer = setInterval(async () => {
      try {
        const res = await fetch('/api/observer/ide/run/' + encodeURIComponent(run.run_id), { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();
        const next = data.run || null;
        if (!live || !next) return;
        setRun((prev) => {
          if (prev?.status === 'running' && next.status !== 'running') {
            const label = next.execution_mode === 'deterministic_template_worker' ? 'deterministic route' : 'harness fallback';
            appendObserverEvent([label + ' ' + next.status + (next.returncode != null ? ' · exit ' + next.returncode : '')]);
          }
          return next;
        });
      } catch (e) {
        /* keep polling; the tunnel can briefly disconnect */
      }
    }, 2500);
    return () => { live = false; clearInterval(timer); };
  }, [appendObserverEvent, run?.run_id, run?.status]);
  const makePlan = React.useCallback(async (taskOverride) => {
    const runTask = String(taskOverride != null ? taskOverride : task).trim();
    if (!runTask) return;
    setBusy(true); setErr('');
    appendObserverEvent([
      'Starting AIDevObserver run.',
      'Parsing the task into requested input/output edges.',
      'Searching reusable primitive routes and deterministic mutators.',
      'Waiting for planner/compiler result...',
    ]);
    try {
      const res = await fetch('/api/observer/ide/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: runTask, models: models.length ? models : ['kimi'], harnesses }),
      });
      if (!res.ok) throw new Error('observer IDE run status ' + res.status);
      const payload = await res.json();
      const nextPlan = payload.plan || payload;
      const nextRun = payload.run || null;
      const executionMode = nextRun?.execution_mode || nextPlan.execution_mode || '';
      const deterministic = executionMode === 'deterministic_template_worker';
      const needsTask = executionMode === 'needs_build_task';
      setPlan(nextPlan);
      setRun(nextRun);
      setPanelView('summary');
      setFileOverrides({});
      const files = idePlanFiles(nextPlan, runTask, {});
      const firstUseful = files.find((file) => String(file.path).endsWith('.py')) || files.find((file) => file.path === 'candidate_bundle.txt') || files[0];
      setActiveFile(firstUseful?.path || 'task.md');
      const trace = nextRun?.ai_trace || nextPlan.ai_trace || {};
      const plannerTrace = trace.route_planning || {};
      const plannerToolResults = Array.isArray(plannerTrace.tool_results) ? plannerTrace.tool_results : [];
      const plannerToolCount = plannerToolResults.reduce((sum, result) => sum + Number(result.component_count || 0), 0);
      const workspaceFiles = Array.isArray(nextPlan.workspace_files) ? nextPlan.workspace_files : [];
      const primitiveModules = workspaceFiles.filter((file) => String(file.path || '').startsWith('primitives/') && String(file.path || '').endsWith('.py') && !String(file.path || '').endsWith('__init__.py'));
      const generatedAppFiles = workspaceFiles.filter((file) => String(file.path || '').startsWith('app/'));
      const generatedTestFiles = workspaceFiles.filter((file) => String(file.path || '').startsWith('tests/') && String(file.path || '').endsWith('.py'));
      const routeQuality = nextRun?.route_quality || nextPlan.route_quality || {};
      const tokenSavings = nextRun?.token_savings || nextPlan.token_savings || {};
      const runtimeTarget = nextRun?.runtime_target || nextPlan.runtime_target || {};
      const plannerLine = plannerTrace.status === 'used'
        ? 'Planner LLM used ' + (plannerTrace.model || 'selected model') + ' to call registry tools and design a route; calls: ' + (plannerTrace.model_calls || 1) + '.'
        : plannerTrace.status === 'unavailable'
          ? 'Planner LLM unavailable; falling back to deterministic registry context or harness.'
          : plannerTrace.reason === 'exact_deterministic_route'
            ? 'Planner LLM not used; exact deterministic primitive route matched.'
            : 'Planner LLM not used.'
      const observerEvents = needsTask
        ? [
            'No run started. That input did not look like a build/review task.',
            'Try: Build a CSV import flow for uploaded vendor files.',
          ]
        : [
            'Searched reusable routes by input/output edges.',
            plannerLine,
            plannerToolCount ? 'Planner saw ' + plannerToolCount + ' compact registry edge card' + (plannerToolCount === 1 ? '' : 's') + '.' : 'No planner registry tool result was selected.',
            deterministic
              ? 'Compiled selected primitive/template route; planner model calls: ' + (trace.known_model_calls || 0) + '; coding harness calls: 0.'
              : 'No deterministic route was strong enough; using harness fallback.',
            'Materialized workspace: ' + generatedAppFiles.length + ' generated app file' + (generatedAppFiles.length === 1 ? '' : 's') + ', ' + generatedTestFiles.length + ' behavior test file' + (generatedTestFiles.length === 1 ? '' : 's') + ', and ' + primitiveModules.length + ' primitive source module' + (primitiveModules.length === 1 ? '' : 's') + '.',
            'Route quality: ' + (routeQuality.score != null ? routeQuality.score + '/100 ' + (routeQuality.label || '') : 'pending') + '.',
            'Runtime target: ' + (runtimeTarget.target || 'local.python') + ' (' + (runtimeTarget.reason || 'default local route') + ').',
            'Estimated tokens avoided by compact edge context: ' + (tokenSavings.estimated_tokens_avoided || 0) + '.',
            'Nothing to select manually; AIDevObserver selects and wires components automatically.',
            nextRun?.run_id
              ? (deterministic ? 'Deterministic run ' : 'Harness fallback run ') + nextRun.run_id + ' · ' + (nextRun.harness || 'executor')
              : 'Route execution did not start.',
          ];
      appendObserverEvent(observerEvents);
      if (!deterministic && !needsTask && nextRun?.run_id) {
        setTerminalLines((xs) => xs.concat(['harness run ' + nextRun.run_id + ' started']));
      }
    } catch (e) {
      setErr('Could not start route execution from the service.');
      appendObserverEvent(['Run failed: observer service did not start route execution.']);
    } finally {
      setBusy(false);
    }
  }, [appendObserverEvent, task, models, harnesses]);
  const buildSessionSnapshot = React.useCallback(() => ({
    exported_at: new Date().toISOString(),
    session_id: currentSessionId || null,
    share_url: shareUrl || null,
    task,
    models: models.length ? models : ['kimi'],
    harnesses,
    terminal_output: terminalLines,
    observer_latest: observerLatest,
    observer_output: observerHistory,
    plan,
    run,
    workspace_files: idePlanFiles(plan, task, fileOverrides),
    candidate: true,
    serves_truth: false,
  }), [currentSessionId, fileOverrides, harnesses, models, observerHistory, observerLatest, plan, run, shareUrl, task, terminalLines]);
  const exportSession = React.useCallback((format) => {
    const snapshot = buildSessionSnapshot();
    const stem = (currentSessionId || 'aidevobserver-session').replace(/[^A-Za-z0-9_.-]/g, '-');
    if (format === 'markdown') {
      downloadTextFile(stem + '.md', 'text/markdown;charset=utf-8', ideSessionMarkdown(snapshot));
    } else {
      downloadTextFile(stem + '.json', 'application/json;charset=utf-8', JSON.stringify(snapshot, null, 2));
    }
  }, [buildSessionSnapshot, currentSessionId]);
  const saveSession = React.useCallback(async () => {
    setSaving(true); setErr('');
    try {
      const res = await fetch('/api/observer/ide/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId || undefined,
          task,
          models: models.length ? models : ['kimi'],
          harnesses,
          toggles: cfg?.toggles || {},
          plan,
          run,
          observer_latest: observerLatest,
          observer_output: observerHistory,
          terminal_output: terminalLines,
          workspace_overrides: fileOverrides,
        }),
      });
      if (!res.ok) throw new Error('session save status ' + res.status);
      const data = await res.json();
      const s = data.session || {};
      setCurrentSessionId(s.session_id || '');
      const full = s.share_url ? window.location.origin + s.share_url : '';
      setShareUrl(full);
      if (s.share_url) navigate(String(s.share_url).replace(/^\/#/, ''));
      const recentRes = await fetch('/api/observer/ide/sessions?limit=8', { cache: 'no-store' });
      if (recentRes.ok) {
        const recentData = await recentRes.json();
        setRecent(Array.isArray(recentData.sessions) ? recentData.sessions : []);
      }
    } catch (e) {
      setErr('Could not save this IDE session.');
    } finally {
      setSaving(false);
    }
  }, [cfg, currentSessionId, fileOverrides, harnesses, models, observerHistory, observerLatest, plan, run, task, terminalLines]);
  const copyShareUrl = React.useCallback(() => {
    if (!shareUrl || !navigator.clipboard?.writeText) return;
    navigator.clipboard.writeText(shareUrl).catch(() => {});
  }, [shareUrl]);
  const clearWorkspace = React.useCallback(() => {
    setTask('');
    setTerminalInput('');
    setTerminalLines(['IDE terminal ready. Type a task and press Enter.']);
    setObserverLatest([]);
    setObserverHistory([]);
    setPlan(null);
    setRun(null);
    setFileOverrides({});
    setActiveFile('task.md');
    setShareUrl('');
    setCurrentSessionId('');
  }, []);
  const submitTerminal = React.useCallback((event) => {
    event.preventDefault();
    const cmd = terminalInput.trim();
    if (!cmd) return;
    setTerminalLines((xs) => xs.concat(['$ ' + cmd]));
    setTask(cmd);
    setTerminalInput('');
    setPlan(null);
    makePlan(cmd);
  }, [makePlan, terminalInput]);
  const toggleFullscreen = React.useCallback(() => {
    const next = !fullscreen;
    onFullscreenToggle(next);
    try {
      if (next && document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
      if (!next && document.fullscreenElement && document.exitFullscreen) document.exitFullscreen();
    } catch (e) { /* browser fullscreen is best effort; app focus mode still applies */ }
  }, [fullscreen, onFullscreenToggle]);
  const lanes = cfg?.model_lanes || [];
  const availableHarnesses = cfg?.harnesses || [];
  const toggleKeys = cfg?.toggles || {};
  const workspaceFiles = idePlanFiles(plan, task, fileOverrides);
  const activeRecord = workspaceFiles.find((file) => file.path === activeFile) || workspaceFiles[0] || { path: 'task.md', content: '' };
  const planGraph = plan?.run_graph || {};
  const sideComponents = Array.isArray(plan?.selected_components) && plan.selected_components.length
    ? plan.selected_components
    : Array.isArray(planGraph.components) ? planGraph.components : [];
  const routeRecipe = run?.recipe || plan?.recipe || null;
  const routeNodes = Array.isArray(routeRecipe?.nodes) ? routeRecipe.nodes : [];
  const promptExamples = [
    'Use Playwright to visit https://www.w3schools.com/html/html_tables.asp, extract tables, and save the first table as CSV and Parquet.',
    'Build a browser ingestion flow that visits a public web page, extracts HTML tables, and writes CSV and Parquet artifacts.',
    'Build a CSV import flow for uploaded vendor files.',
    'Build a document extraction pipeline that turns invoices into JSON with source spans.',
  ];
  const activeContent = activeRecord.path === 'task.md'
    ? (String(task || '').trim() ? '# Task\n\n' + String(task || '').trim() + '\n' : '')
    : String(activeRecord.content || '');
  const updateActiveContent = React.useCallback((value) => {
    if (!activeRecord.path || activeRecord.path === 'task.md') {
      setTask(value.replace(/^# Task\s*/i, '').trimStart());
      setPlan(null);
      return;
    }
    setFileOverrides((xs) => ({ ...xs, [activeRecord.path]: value }));
  }, [activeRecord.path]);
  const modalTabs = [
    ['models', 'Models'],
    ['harnesses', 'Harnesses'],
    ['intelligence', 'Benchmark Lab'],
    ['session', 'Session'],
    ['plan', 'Run plan'],
  ];
  return (
    <>
      {err && <div className="ado-demo-err mono" style={{ marginBottom: 12 }}>{err}</div>}
      <div className="ado-ide-shell">
        <div className="ado-ide-titlebar">
          <div className="ado-ide-title-left">
            <span className="ado-ide-title-mark">▣</span>
            <span>AIDevObserver</span>
            <span className="ado-ide-title-path mono">{currentSessionId ? currentSessionId : 'blank workspace'}</span>
          </div>
          <div className="ado-ide-title-actions">
            <button disabled={busy || !task.trim() || harnesses.length === 0} onClick={() => makePlan()}>{busy ? 'Starting…' : 'Run'}</button>
            <button disabled={saving || !task.trim()} onClick={shareUrl ? copyShareUrl : saveSession}>{shareUrl ? 'Copy URL' : 'Share'}</button>
            <button disabled={!task.trim() && !plan && !run} onClick={() => exportSession('json')}>Export</button>
            <button className="icon" aria-label="IDE settings" title="Settings" onClick={() => openSettings('models')}>⚙</button>
            <button onClick={toggleFullscreen}>{fullscreen ? 'Exit focus' : 'Focus'}</button>
          </div>
        </div>
        <aside className="ado-ide-activity" aria-label="IDE activity bar">
          {[
            ['explorer', '◎', 'Explorer'],
            ['search', '⌕', 'Registry'],
            ['graph', '⚑', 'Graph'],
            ['commands', '⌘', 'Commands'],
            ['settings', '⚙', 'Settings'],
          ].map(([key, glyph, label]) => (
            <button className={activeActivity === key ? 'on' : ''} key={key} title={label} aria-label={label}
              onClick={() => {
                if (key === 'settings') {
                  setActiveActivity(key);
                  openSettings('models');
                  return;
                }
                setActiveActivity(key);
                if (key === 'graph') setPanelView('graph');
              }}>{glyph}</button>
          ))}
        </aside>
        <aside className="ado-ide-files">
          <div className="ado-ide-pane-title">{
            activeActivity === 'search' ? 'Registry' :
            activeActivity === 'graph' ? 'Route graph' :
            activeActivity === 'commands' ? 'Commands' :
            activeActivity === 'settings' ? 'Settings' :
            'Explorer'
          }</div>
          {activeActivity === 'explorer' ? (
            workspaceFiles.length
            ? (
              <>
                <div className="ado-ide-folder mono"><span>▾</span>workspace/</div>
                {ideFileGroups(workspaceFiles).map((group) => (
                  <div className="ado-ide-file-group" key={group.key}>
                    <div className="ado-ide-file-group-title">{group.label}</div>
                    {group.files.map((file) => (
                      <button className={'ado-ide-file mono' + (activeFile === file.path ? ' on' : '')}
                        key={file.path} onClick={() => setActiveFile(file.path)}>
                        <span>{ideFileIcon(file.path)}</span><span>{file.path}</span>
                      </button>
                    ))}
                  </div>
                ))}
              </>
            )
            : (
              <div className="ado-ide-empty">
                <b>Blank workspace</b>
                <p>Start in the terminal. Files appear when a task run starts.</p>
              </div>
            )
          ) : null}
          {activeActivity === 'search' ? (
            <div className="ado-side-list">
              {sideComponents.length ? sideComponents.slice(0, 8).map((component, idx) => {
                const contract = component.contract || {};
                const sourceRef = component.source_ref || {};
                const reasons = Array.isArray(component.selection_reasons) ? component.selection_reasons : [];
                return (
                  <div className="ado-side-card" key={idx}>
                    <b>{component.label || 'candidate component'}</b>
                    <span>{contract.input || 'input'} → {contract.output || 'output'}</span>
                    <small>{component.edge_fit || 'candidate'}</small>
                    {sourceRef.path ? <small className="mono">{sourceRef.path}{sourceRef.name ? ' :: ' + sourceRef.name : ''}</small> : null}
                    {reasons[0] ? <small>why: {reasons[0]}</small> : null}
                  </div>
                );
              }) : (
                <div className="ado-ide-empty">
                  <b>No registry match yet</b>
                  <p>Run a concrete task. Exact input/output edge matches and mutation options will show here.</p>
                </div>
              )}
            </div>
          ) : null}
          {activeActivity === 'graph' ? (
            <div className="ado-side-list">
              {routeNodes.length ? routeNodes.map((node, idx) => (
                <button className="ado-side-card action" key={node.id || idx} onClick={() => setPanelView('graph')}>
                  <b>{idx + 1}. {node.id || 'step'}</b>
                  <span>{node.input || 'input'} → {node.output || 'output'}</span>
                  <small>{node.primitive || node.component}</small>
                </button>
              )) : (
                <div className="ado-ide-empty">
                  <b>No graph yet</b>
                  <p>Run a task. The AIDevObserver panel switches to Graph when a deterministic recipe is compiled.</p>
                </div>
              )}
              {routeNodes.length ? <button className="ado-side-action" onClick={() => setPanelView('graph')}>Show graph in AIDevObserver panel</button> : null}
            </div>
          ) : null}
          {activeActivity === 'commands' ? (
            <div className="ado-side-list">
              <div className="ado-side-card">
                <b>Example prompts</b>
                <small>Click one to load it into the terminal input, then press Enter.</small>
              </div>
              {promptExamples.map((prompt) => (
                <button className="ado-side-card action" key={prompt} onClick={() => setTerminalInput(prompt)}>
                  <b>{prompt.split('.')[0]}</b>
                  <small>{prompt}</small>
                </button>
              ))}
              {plan?.commands?.length ? (
                <div className="ado-side-card">
                  <b>Current command</b>
                  <code className="mono">{plan.commands[0].command}</code>
                </div>
              ) : null}
            </div>
          ) : null}
          {activeActivity === 'settings' ? (
            <div className="ado-ide-empty">
              <b>Settings are open</b>
              <p>Use the settings modal for models, harnesses, intelligence toggles, session export, and run details.</p>
              <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => openSettings('models')}>Open settings</button>
            </div>
          ) : null}
        </aside>
        <main className="ado-ide-main">
          <div className="ado-ide-tabs">
            <div className="ado-ide-tab-list">
              {workspaceFiles.map((file) => (
                <button key={file.path} className={activeFile === file.path ? 'on' : ''} onClick={() => setActiveFile(file.path)}>
                  {file.path.split('/').pop()}
                </button>
              ))}
            </div>
            <div className="ado-ide-tab-actions">
              <button onClick={clearWorkspace}>Clear</button>
            </div>
          </div>
          <textarea className="ado-ide-editor mono" value={activeContent} onChange={(e) => updateActiveContent(e.target.value)}
            spellCheck="false"
            placeholder="Type in the terminal below. AIDevObserver will search primitives, compile deterministic routes when possible, and use the harness only for missing glue." />
          <div className="ado-ide-terminal mono" role="log" aria-label="IDE terminal">
            <div className="ado-ide-terminal-lines">
              {terminalLines.map((line, idx) => <div key={idx}>{line}</div>)}
              {run?.log_tail && run.execution_mode === 'coding_harness_fallback' ? run.log_tail.split('\n').slice(-80).map((line, idx) => <div key={'run-' + idx}>{line}</div>) : null}
              {busy && <div>checking route execution...</div>}
            </div>
            <form className="ado-ide-terminal-form" onSubmit={submitTerminal}>
              <span>$</span>
              <input value={terminalInput} onChange={(e) => setTerminalInput(e.target.value)}
                placeholder="Type a Claude Code-style task, then press Enter" autoComplete="off" />
            </form>
          </div>
        </main>
        <RunGraphPanel plan={plan} run={run} busy={busy}
          observerLatest={observerLatest}
          observerHistory={observerHistory}
          panelView={panelView}
          setPanelView={setPanelView}
          onOpenPlan={() => openSettings('plan')}
          onExportJson={() => exportSession('json')}
          onExportMarkdown={() => exportSession('markdown')} />
      </div>
      {settingsOpen && (
        <div className="ado-modal ado-ide-settings" role="dialog" aria-modal="true" aria-labelledby="ado-ide-settings-title">
          <button className="ado-modal-backdrop" aria-label="Close IDE settings" onClick={() => setSettingsOpen(false)} />
          <div className="ado-modal-panel ado-ide-settings-panel">
            <div className="ado-modal-head">
              <div>
                <div className="ado-modal-eyebrow">IDE settings</div>
                <h3 id="ado-ide-settings-title">Models, harnesses, intelligence, and session</h3>
                <p>Keep the workbench clean. Details live here; the editor stays focused on files and terminal work.</p>
              </div>
              <button className="ado-modal-close" aria-label="Close" onClick={() => setSettingsOpen(false)}>×</button>
            </div>
            <div className="ado-ide-settings-body">
              <nav className="ado-ide-settings-tabs" aria-label="IDE settings tabs">
                {modalTabs.map(([key, label]) => (
                  <button key={key} className={settingsTab === key ? 'on' : ''} onClick={() => setSettingsTab(key)}>{label}</button>
                ))}
              </nav>
              <div className="ado-ide-settings-content">
                {settingsTab === 'models' && (
                  <div className="ado-ide-setting-list">
                    {lanes.filter((lane) => ['kimi', 'glm'].includes(lane.key)).map((lane) => {
                      const checked = models.includes(lane.key);
                      return (
                        <button key={lane.key} className={'ado-ide-setting-row' + (checked ? ' on' : '')}
                          onClick={() => toggleModel(lane.key)}>
                          <span className="ado-check">{checked ? '☑' : '☐'}</span>
                          <div>
                            <b>{lane.title}</b>
                            <small className="mono">{lane.model}</small>
                          </div>
                          <StatusDot value={lane.status} />
                        </button>
                      );
                    })}
                  </div>
                )}
                {settingsTab === 'harnesses' && (
                  <div className="ado-ide-setting-list">
                    {availableHarnesses.map((h) => {
                      const checked = harnesses.includes(h.key);
                      return (
                        <button key={h.key} className={'ado-ide-setting-row' + (checked ? ' on' : '')} onClick={() => toggleHarness(h.key)}>
                          <span className="ado-check">{checked ? '◉' : '○'}</span>
                          <div>
                            <b>{h.label}</b>
                            <small>{h.role}</small>
                          </div>
                          <StatusDot value={h.status} />
                        </button>
                      );
                    })}
                  </div>
                )}
                {settingsTab === 'intelligence' && (
                  <div className="ado-ide-setting-list">
                    {['global_primitives', 'local_registry', 'mcp', 'plugins', 'live_hook', 'token_savings', 'llm_rerank'].map((key) => {
                      const [title, desc] = INTELLIGENCE_TOGGLE_COPY[key] || [key, ''];
                      return (
                        <button key={key} className={'ado-ide-setting-row' + (toggleKeys[key] ? ' on' : '')} onClick={() => updateToggle(key)} disabled={!cfg}>
                          <span className="ado-check">{toggleKeys[key] ? '☑' : '☐'}</span>
                          <div>
                            <b>{title}</b>
                            <small>{desc}</small>
                          </div>
                          <span className="ado-ide-setting-state">{toggleKeys[key] ? 'on' : 'off'}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
                {settingsTab === 'session' && (
                  <div className="ado-ide-setting-list">
                    <div className="ado-ide-setting-box">
                      <span className="ado-plan-k">Current session</span>
                      <b className="mono">{currentSessionId || 'unsaved blank workspace'}</b>
                    </div>
                    {shareUrl && (
                      <div className="ado-ide-setting-box">
                        <span className="ado-plan-k">Share URL</span>
                        <code className="mono">{shareUrl}</code>
                      </div>
                    )}
                    {recent.length ? (
                      <div className="ado-ide-setting-box">
                        <span className="ado-plan-k">Recent sessions</span>
                        <div className="ado-ide-session-list">
                          {recent.slice(0, 5).map((s) => (
                            <button key={s.session_id} onClick={() => { setSettingsOpen(false); navigate(ROUTES.ide + '/' + s.session_id); }}>
                              <b>{s.title || s.session_id}</b>
                              <small className="mono">{ideModelListLabel(s.models)}</small>
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : null}
                    <div className="ado-ide-setting-actions">
                      <button className="oh-btn oh-btn--primary" disabled={saving || !task.trim()} onClick={saveSession}>{saving ? 'Saving…' : 'Save session URL'}</button>
                      <button className="oh-btn oh-btn--ghost" disabled={!shareUrl} onClick={copyShareUrl}>Copy URL</button>
                      <button className="oh-btn oh-btn--ghost" disabled={!task.trim() && !plan && !run} onClick={() => exportSession('json')}>Export JSON</button>
                      <button className="oh-btn oh-btn--ghost" disabled={!task.trim() && !plan && !run} onClick={() => exportSession('markdown')}>Export MD</button>
                      <button className="oh-btn oh-btn--ghost" onClick={clearWorkspace}>Clear workspace</button>
                    </div>
                  </div>
                )}
                {settingsTab === 'plan' && (
                  <div className="ado-ide-setting-list">
                    {plan ? (
                      <>
                        <div className="ado-ide-setting-box"><span className="ado-plan-k">Run context</span><b className="mono">{plan.plan_id}</b></div>
                        <div className="ado-ide-setting-box">
                          <span className="ado-plan-k">Observer context</span>
                          <b>{plan.observer_guidance?.label || plan.observer_policy?.label || 'Primitive route search'}</b>
                          <small>Plain user tasks are expanded with primitive search, input/output edge matching, token estimates, and selected component summaries automatically.</small>
                        </div>
                        <div className="ado-ide-setting-box">
                          <span className="ado-plan-k">What happened</span>
                          <small>{
                            run?.execution_mode === 'deterministic_template_worker'
                              ? 'AIDevObserver compiled the selected primitive route and materialized workspace files without invoking a coding harness or codegen model.'
                              : run?.run_id
                                ? 'AIDevObserver started the harness fallback and is polling its run log.'
                                : 'AIDevObserver assembled reusable component context and is ready to execute.'
                          }</small>
                        </div>
                        {run?.run_id ? (
                          <div className="ado-ide-setting-box">
                            <span className="ado-plan-k">Run</span>
                            <b className="mono">{run.run_id}</b>
                            <small>status: {run.status || 'unknown'}{run.returncode != null ? ' · exit ' + run.returncode : ''}</small>
                          </div>
                        ) : null}
                        <div className="ado-ide-setting-box">
                          <span className="ado-plan-k">Execution note</span>
                          <small>Deterministic template workers handle exact reusable routes. Coding harnesses are fallback workers for missing glue, using only compact component edges. Every run remains candidate evidence until proof passes.</small>
                        </div>
                        {plan.recipe?.nodes?.length ? (
                          <div className="ado-ide-setting-box">
                            <span className="ado-plan-k">Compiled recipe</span>
                            <b className="mono">{plan.recipe.recipe_id}</b>
                            {(plan.recipe.nodes || []).map((node) => (
                              <small key={node.id}>
                                {node.id}: {node.primitive || node.component} · {node.input} → {node.output}
                              </small>
                            ))}
                          </div>
                        ) : null}
                        {run?.proofs?.length ? (
                          <div className="ado-ide-setting-box">
                            <span className="ado-plan-k">Proof checks</span>
                            {(run.proofs || []).map((proof) => (
                              <small key={proof.id}>{proof.id}: {proof.status} · {proof.detail}</small>
                            ))}
                          </div>
                        ) : null}
                        {(plan.next_actions || []).length ? (
                          <div className="ado-ide-setting-box">
                            <span className="ado-plan-k">Next</span>
                            {(plan.next_actions || []).map((action, idx) => <small key={idx}>{idx + 1}. {action}</small>)}
                          </div>
                        ) : null}
                        <div className="ado-ide-setting-box"><span className="ado-plan-k">Model assists</span><b className="mono">{ideModelListLabel(plan.models)}</b></div>
                        <div className="ado-ide-setting-box"><span className="ado-plan-k">Harnesses</span><b className="mono">{(plan.harnesses || []).join(', ')}</b></div>
                        {(plan.commands || []).map((cmd) => (
                          <code className="ado-ide-command mono" key={cmd.harness}>{cmd.command}</code>
                        ))}
                        {plan.harness_task && (
                          <details className="ado-ide-setting-box">
                            <summary>Observer-wrapped task sent to the harness</summary>
                            <code className="ado-ide-command mono">{plan.harness_task}</code>
                          </details>
                        )}
                      </>
                    ) : (
                      <div className="ado-ide-setting-box">No run yet. Type a task in the terminal and press Enter.</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function AppIntelligence() {
  const [cfg, setCfg] = React.useState(null);
  const [err, setErr] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const load = React.useCallback(async () => {
    setErr('');
    try {
      const res = await fetch('/api/observer/config', { cache: 'no-store' });
      if (!res.ok) throw new Error('observer config status ' + res.status);
      setCfg(await res.json());
    } catch (e) {
      setErr('The observer service is not reachable yet. Start the local service, then refresh this page.');
      setCfg(null);
    }
  }, []);
  React.useEffect(() => { load(); }, [load]);
  const save = React.useCallback(async (next) => {
    if (!cfg) return;
    setSaving(true); setErr('');
    try {
      const res = await fetch('/api/observer/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(next),
      });
      if (!res.ok) throw new Error('observer config status ' + res.status);
      setCfg(await res.json());
    } catch (e) {
      setErr('Could not update the running observer config. The page is read-only until the service is reachable.');
    } finally {
      setSaving(false);
    }
  }, [cfg]);
  const lanes = (cfg?.model_lanes || [
    { key: 'kimi', title: 'Kimi code', model: 'kimi-k2.7-code', role: 'code-session digesting and implementation-oriented rerank', provider: 'ollama-cloud', status: 'not_connected' },
    { key: 'glm', title: 'GLM reasoning', model: 'glm-5.2', role: 'architecture review and higher-reasoning rerank', provider: 'ollama-cloud', status: 'not_connected' },
  ]).filter((lane) => ['kimi', 'glm'].includes(lane.key));
  const selected = ['kimi', 'glm'].includes(cfg?.model_provider) ? cfg.model_provider : 'kimi';
  const toggles = cfg?.toggles || {};
  const choose = (key) => save({ model_provider: key, toggles });
  const flip = (key) => save({ model_provider: selected, toggles: { ...toggles, [key]: !toggles[key] } });
  return (
    <>
      <OhPageHead eyebrow="Intelligence" title="Configure observer intelligence"
        sub="Choose the model assist for grounded ranking and summarization. Registry search, source-ref matching, token estimates, and edge matching stay on in the background."
        actions={<button className="oh-btn oh-btn--ghost" onClick={load}>Refresh</button>} />
      {err && <div className="ado-demo-err mono" style={{ marginBottom: 12 }}>{err}</div>}
      <OhRollup items={[
        ['Selected assist', ideModelListLabel([selected])],
        ['Observer intelligence', 'on by default'],
        ['Global primitives', toggles.global_primitives ? 'on' : 'off'],
        ['Local registry', toggles.local_registry ? 'on' : 'off'],
        ['Token savings', toggles.token_savings ? 'on' : 'off'],
      ]} />
      <div className="ohs-settings-sec">
        <h3>Model lane</h3>
        <div className="ado-model-grid">
          {lanes.map((lane) => <ModelLaneCard key={lane.key} lane={lane} selected={selected === lane.key} disabled={saving || !cfg} onSelect={choose} />)}
        </div>
        <div className="ohs-hint mono">Kimi and GLM are the model-assist choices. Primitive search and source-ref matching are AIDevObserver capabilities, not a separate coding model.</div>
      </div>
      <div className="ohs-settings-sec">
        <h3>Intelligence layers</h3>
        <div className="oh-card oh-card--pad ado-toggle-panel">
          {Object.keys(INTELLIGENCE_TOGGLE_COPY).map((key) => (
            <ToggleRow key={key} id={key} on={toggles[key]} disabled={saving || !cfg} onToggle={() => flip(key)} />
          ))}
        </div>
      </div>
      <div className="ohs-settings-sec">
        <h3>How this affects review</h3>
        <div className="ado-intel-notes">
          <div className="oh-card oh-card--pad">
            <h4>Search first</h4>
            <p>AIDevObserver starts with transcript extraction, global primitive search, local source matching when enabled, and input/output edge matching.</p>
          </div>
          <div className="oh-card oh-card--pad">
            <h4>Model assistance second</h4>
            <p>Kimi and GLM can help rank or summarize grounded candidates, but they do not invent source refs or flip findings into truth.</p>
          </div>
          <div className="oh-card oh-card--pad">
            <h4>One report everywhere</h4>
            <p>The browser, MCP server, editor plugins, CLI, and live hook all read the same candidate report shape.</p>
          </div>
        </div>
      </div>
    </>
  );
}

function AppExamples() {
  return (
    <>
      <OhPageHead eyebrow="Examples" title="Compiled AI patterns"
        sub="Worked examples for the AIDevObserver benchmark lab: each starts as candidate intent, compiles through deterministic contracts, and remains candidate-only until proof/promotion." />
      <ExamplesGrid compact />
      <div className="ohs-settings-sec" style={{ marginTop: 18 }}>
        <h3>Replayable session pack</h3>
        <div className="ohs-hint mono">Download a transcript, upload it on Review, or replay it directly through the live review flow.</div>
        <SessionReplayGrid compact />
      </div>
      <div className="ohs-settings-sec" style={{ marginTop: 18 }}>
        <h3>Portfolio split</h3>
        <div className="oh-card oh-card--pad">
          <table className="oh-table">
            <thead><tr><th>Surface</th><th>Role</th><th>Truth boundary</th></tr></thead>
            <tbody>
              {[
                ['AIDevObserver', 'Session review, reuse recommendations, examples, and benchmark-lab workflows', 'candidate advice only'],
                ['Teleon', 'Capability compiler, runtime selection, PlanLock execution', 'evidence, not served truth'],
                ['Baltor', 'Governed context and source-grounded answers', 'served truth after governance'],
                ['OpenHubForAI', 'Open registry/catalog substrate', 'reference artifacts only'],
                ['AI Done Right', 'Portfolio and positioning layer', 'owns no runtime truth'],
              ].map(([surface, role, boundary]) => (
                <tr key={surface}><td>{surface}</td><td>{role}</td><td className="mono">{boundary}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// /notifications → kit OhNotifications with AIDevObserver copy
function AppNotifications() {
  return <OhNotifications items={[
    { icon: '⚑', t: 'A duplicate parser was flagged', d: 'importer session · existing utils.csv.read_rows', w: '12m ago', unread: true },
    { icon: '⟳', t: 'A supervised run looked runaway', d: 'flywheel loop · stalled_or_runaway', w: '1h ago', unread: true },
    { icon: '◉', t: 'Weekly review digest ready', d: '214 sessions · 512 findings · 47% reuse', w: '1d ago' },
    { icon: '◑', t: 'A teammate joined the workspace', d: 'grace@company.com · Member', w: '2d ago' },
  ]} />;
}

// /members → kit OhTeam (seats grant access; billing is usage-metered, not per-seat)
function AppMembers() {
  return (
    <>
      <OhTeam members={[
        { name: 'Ada Lovelace', email: 'ada@company.com', role: 'Owner', status: 'active' },
        { name: 'Alan Turing', email: 'alan@company.com', role: 'Admin', status: 'active' },
        { name: 'Grace Hopper', email: 'grace@company.com', role: 'Member', status: 'active' },
        { name: 'invited@company.com', email: 'invited@company.com', role: 'Member', status: 'invited' },
      ]} />
      <div className="ohs-hint mono" style={{ marginTop: 12 }}>Seats grant access. Billing is usage-metered (sessions reviewed, findings surfaced, live checks), not per-seat.</div>
    </>
  );
}

// /billing → kit OhBilling, usage-metered plan + AIDevObserver invoices
function AppBilling() {
  return (
    <OhBilling
      plan={{ name: 'Team · usage-metered', desc: 'Sessions reviewed, findings surfaced, and live checks. Seats grant access; usage is the meter.', price: 'Usage', per: '/mo', usagePct: 38, usageLabel: 'Sessions reviewed this period' }}
      invoices={[['Jun 1, 2026', '$182.40', 'Paid'], ['May 1, 2026', '$164.10', 'Paid'], ['Apr 1, 2026', '$143.75', 'Paid']]} />
  );
}

// /developer → kit OhApiKeys + the real /api/observer/* endpoint reference + connect lines
function AppDeveloper() {
  return (
    <>
      <OhApiKeys keys={[
        { name: 'CI review', prefix: 'sk_live_ado_7c', created: 'Apr 4, 2026', lastUsed: '2h ago' },
        { name: 'Local dev', prefix: 'sk_test_ado_1f', created: 'Mar 1, 2026', lastUsed: '1d ago' },
      ]} />
      <div className="ohs-settings-sec" style={{ marginTop: 8 }}>
        <h3>API reference</h3>
        <div className="oh-card oh-card--pad">
          <table className="oh-table">
            <thead><tr><th>Method</th><th>Endpoint</th><th>What it does</th></tr></thead>
            <tbody>
              {API_ENDPOINTS.map(([m, p, d]) => (
                <tr key={p}>
                  <td><span className={'ado-mb ado-mb--' + m.toLowerCase()}>{m}</span></td>
                  <td className="mono">{p}</td><td>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="ohs-hint mono">Same-origin seam. A BYO inference key is used per request, never stored or logged. serves_truth = false.</div>
      </div>
      <div className="ohs-settings-sec">
        <h3>Connect</h3>
        <SetupGuide />
      </div>
    </>
  );
}

// /account → kit OhSettings (profile, security, notification preferences)
function AppAccount() {
  const [twofa, setTwofa] = React.useState(true);
  const [digest, setDigest] = React.useState(true);
  const [live, setLive] = React.useState(false);
  return (
    <OhSettings eyebrow="Account" title="Account"
      sub="Manage your profile, security, active sessions, and personal notification preferences."
      sections={[
      { title: 'Profile', rows: [
        { t: 'Name', d: 'Shown to your team', ctrl: <input className="oh-input" defaultValue="Ada Lovelace" /> },
        { t: 'Work email', d: 'Your sign-in address', ctrl: <input className="oh-input" defaultValue="ada@company.com" /> },
      ] },
      { title: 'Security', rows: [
        { t: 'Two-factor authentication', d: 'Require a second factor at sign-in', ctrl: <OhSwitch on={twofa} onToggle={() => setTwofa((v) => !v)} /> },
        { t: 'Password', d: 'Last changed 3 months ago', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm">Change</button> },
        { t: 'Active sessions', d: 'This device · 2 others', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm">Manage</button> },
      ] },
      { title: 'Notifications', rows: [
        { t: 'Weekly review digest', d: 'A ranked summary every Monday', ctrl: <OhSwitch on={digest} onToggle={() => setDigest((v) => !v)} /> },
        { t: 'Live in-session prompts', d: 'Coach the moment something looks off', ctrl: <OhSwitch on={live} onToggle={() => setLive((v) => !v)} /> },
      ] },
    ]} />
  );
}

// /settings → product settings: mode, interruption budget, governed BYO key, internal-registry connect, install lines
const OBSERVER_MODES = [
  ['silent', 'Silent record', 'Capture and report only; never interrupts.'],
  ['review', 'Review only', 'A ranked report after the session.'],
  ['advisory', 'Advisory', 'Reports, plus non-blocking in-session prompts.'],
  ['active', 'Active', 'Prompts on anything above the confidence bar.'],
  ['enforcing', 'Enforcing', 'Strong prompts; still never blocks (read-only).'],
];
function AppSettings() {
  const [mode, setMode] = React.useState('review');
  const [budget, setBudget] = React.useState(3);
  const [byoKey, setByoKey] = React.useState('');
  return (
    <>
      <OhPageHead eyebrow="Settings" title="How AIDevObserver works for you"
        sub="Pick how present it is, cap interruptions, point it at registries, and keep transcript text out of stored outcome memory." />
      <div className="ohs-settings-sec">
        <h3>Mode</h3>
        <div className="oh-card oh-card--pad ado-modes">
          {OBSERVER_MODES.map(([k, t, d]) => (
            <button key={k} className={'ado-mode' + (mode === k ? ' on' : '')} onClick={() => setMode(k)}>
              <span className="ado-mode-dot" aria-hidden="true" />
              <span className="ado-mode-b"><span className="ado-mode-t">{t}</span><span className="ado-mode-d">{d}</span></span>
            </button>
          ))}
        </div>
      </div>
      <div className="ohs-settings-sec">
        <h3>Interruption budget</h3>
        <div className="oh-card oh-card--pad">
          <div className="ohs-meter-row"><span>At most {budget} in-session prompts per hour</span><span className="mono">{budget}/h</span></div>
          <input type="range" min={0} max={10} value={budget} onChange={(e) => setBudget(Number(e.target.value))} style={{ width: '100%', marginTop: 10, accentColor: 'var(--accent)' }} />
          <div className="ohs-hint mono">0 means report-only. The budget caps would_interrupt on the live seam.</div>
        </div>
      </div>
      <div className="ohs-settings-sec">
        <h3>Your model (BYO key)</h3>
        <div className="oh-card oh-card--pad">
          <div className="ohs-invite">
            <input className="oh-input" type="password" placeholder="sk-… (used per request, never stored or logged)" value={byoKey} onChange={(e) => setByoKey(e.target.value)} style={{ flex: 1 }} />
            <button className="oh-btn oh-btn--ghost">Use for this session</button>
          </div>
          <div className="ohs-hint mono">A BYO inference key is used only for the request and is never stored or logged.</div>
        </div>
      </div>
      <div className="ohs-settings-sec">
        <h3>Internal registry</h3>
        <div className="oh-card oh-card--pad">
          <div className="ohs-invite">
            <input className="oh-input" placeholder="https://registry.yourco.internal" style={{ flex: 1 }} />
            <button className="oh-btn oh-btn--ghost">Connect</button>
          </div>
          <div className="ohs-hint mono">So "already exists" covers private libraries, generated primitives, workflow graphs, and hub records.</div>
        </div>
      </div>
      <div className="ohs-settings-sec">
        <h3>Install and connect</h3>
        <SetupGuide />
      </div>
    </>
  );
}

// /help → support + the install/MCP/CLI/hook lines
function AppHelp() {
  return (
    <>
      <OhPageHead eyebrow="Help" title="Get AIDevObserver running"
        sub="Connect it where AI coding happens, then read your first ranked report. Transcript text is not stored; triage outcome memory is metadata-only." />
      <div className="ohs-grid-3" style={{ marginTop: 4 }}>
        {[['◉', 'Quick start', 'Discover a local session and review it in under a minute.', ROUTES.sessions],
          ['⚑', 'Reading a report', 'Findings are ranked by confidence and triaged with Accept / Reuse / Dismiss.', ROUTES.findings],
          ['⟳', 'Supervising loops', 'Point AIDevObserver at an autonomous run to catch thrash and runaways.', ROUTES.agentic]].map(([g, t, d, h]) => (
          <button className="oh-card oh-card--pad oh-card--interactive ohs-feature" key={t} onClick={() => navigate(h)} style={{ cursor: 'pointer', textAlign: 'left' }}>
            <div className="fi">{g}</div><h4>{t}</h4><p>{d}</p>
          </button>
        ))}
      </div>
      <div className="ohs-settings-sec" style={{ marginTop: 18 }}>
        <h3>Connect</h3>
        <SetupGuide />
      </div>
    </>
  );
}

// the signed-in shell: routes, the shared OhAppShell, the lifted finding-outcome store, the ⌘K palette.
function ObserverApp({ route, theme, onToggle }) {
  const [report, setReport] = React.useState(null);
  const [source, setSource] = React.useState('live');
  const [session, setSession] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [busyPath, setBusyPath] = React.useState(null);
  const [sessions, setSessions] = React.useState(null);
  const [outcomes, setOutcomes] = React.useState({});   // findingKey -> 'accepted'|'reused'|'dismissed'
  const [ideFullscreen, setIdeFullscreen] = React.useState(true);
  const isIdeRoute = route === ROUTES.ide || route.startsWith(ROUTES.ide + '/');
  React.useEffect(() => {
    if (!isIdeRoute && ideFullscreen) setIdeFullscreen(false);
  }, [ideFullscreen, isIdeRoute]);

  // the outcome a person triages (Accept/Reuse/Dismiss) — the product's compounding signal; reflected on Findings
  // and, when the backend stamped ids, appended as metadata-only outcome memory.
  const onOutcome = React.useCallback((k, v, finding) => {
    setOutcomes((m) => { const next = Object.assign({}, m); if (v == null) delete next[k]; else next[k] = v; return next; });
    if (!finding || !finding.session_id || !finding.intervention_id) return;
    fetch('/api/observer/outcome', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: finding.session_id,
        intervention_id: finding.intervention_id,
        outcome: v == null ? 'ignored' : v,
        type: finding.type || '',
        source_ref: finding.source_ref || null,
      }),
    }).catch(() => {});
  }, []);

  // keep a light session count for the dashboard (metadata only; never the transcript)
  React.useEffect(() => {
    let live = true;
    fetch('/api/observer/sessions').then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { if (live) setSessions(Array.isArray(d.sessions) ? d.sessions : []); })
      .catch(() => { if (live) setSessions([]); });
    return () => { live = false; };
  }, []);

  // review a DISCOVERED session by its transcript path (the engine reads the file server-side). On an
  // unreachable backend we stay honest: the transcript is never in the browser, so we report "not reviewed"
  // rather than inventing findings (the paste demo, which HAS the text, keeps its own preview fallback).
  const runReview = React.useCallback(async (sess) => {
    setBusyPath(sess.path); setError(null);
    try {
      const res = await fetch('/api/observer/review', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript_path: sess.path, session_id: sess.session_id }),
      });
      if (!res.ok) throw new Error('observer backend status ' + res.status);
      const data = await res.json();
      setReport(data); setSource('live'); setSession(sess.session_id);
    } catch (e) {
      setReport(null);
      setError('The observer service was not reachable, so this session was not reviewed. Discovery is metadata only — the transcript is never read in the browser.');
      setSession(sess.session_id);
    } finally { setBusyPath(null); navigate(ROUTES.findings); }
  }, []);

  let screen;
  if (route === ROUTES.sessions) screen = <AppSessions onReview={runReview} busyPath={busyPath} />;
  else if (route === ROUTES.findings) screen = <AppFindings report={report} source={source} session={session} error={error} outcomes={outcomes} onOutcome={onOutcome} />;
  else if (route === ROUTES.agentic) screen = <AppAgentic outcomes={outcomes} onOutcome={onOutcome} />;
  else if (isIdeRoute) screen = <AppIDE sessionId={route.startsWith(ROUTES.ide + '/') ? route.slice((ROUTES.ide + '/').length) : ''}
    fullscreen={ideFullscreen} onFullscreenToggle={setIdeFullscreen} />;
  else if (route === ROUTES.intelligence) screen = <AppIntelligence />;
  else if (route === ROUTES.examples) screen = <AppExamples />;
  else if (route === ROUTES.reports) screen = <AppReports />;
  else if (route === ROUTES.notifications) screen = <AppNotifications />;
  else if (route === ROUTES.members) screen = <AppMembers />;
  else if (route === ROUTES.billing) screen = <AppBilling />;
  else if (route === ROUTES.developer) screen = <AppDeveloper />;
  else if (route === ROUTES.account) screen = <AppAccount />;
  else if (route === ROUTES.settings) screen = <AppSettings />;
  else if (route === ROUTES.help) screen = <AppHelp />;
  else if (route === ROUTES.review) screen = <AppReview outcomes={outcomes} onOutcome={onOutcome} />;
  else screen = <AppDashboard sessions={sessions} lastReport={report} outcomes={outcomes} />;

  const isActive = (h) => (route === h || route.startsWith(h + '/'));
  const cmds = OhCommandK.fromNav(APP_NAV, APP_GROUPS).concat([
    { label: 'Open the marketing site', href: ROUTES.home, icon: '↗', group: 'Actions' },
    { label: 'Sign out', href: '/signin', icon: '⎋', group: 'Actions' },
  ]);
  // sticky account bar: the ⌘K search trigger + a notifications jump
  const topbar = (
    <div className="ado-appbar">
      <button className="ado-search" onClick={() => window.dispatchEvent(new Event('oh-cmdk'))}>
        <span className="ado-search-i" aria-hidden="true">⌕</span>
        <span className="ado-search-t">Search or jump to…</span>
        <span className="oh-kbd">⌘K</span>
      </button>
      <span className="ohs-spacer" />
      <button className="ado-appbar-ic" title="Notifications" onClick={() => navigate(ROUTES.notifications)} aria-label="Notifications">◔</button>
      <span className="ado-avatar" title="Ada Lovelace">A</span>
    </div>
  );
  const foot = (
    <>
      <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ width: '100%', justifyContent: 'center' }}
        onClick={() => navigate(ROUTES.home)}>← Back to site</button>
      <div className="ohs-side-foot-row">
        <span className="mono" style={{ fontSize: 11, color: 'var(--fg-muted)' }}>Read only</span>
        {onToggle && <OhThemeToggle theme={theme} onToggle={onToggle} />}
      </div>
    </>
  );

  return (
    <div className={'oh dir-s theme-' + theme + ' oh-site ado' + (isIdeRoute && ideFullscreen ? ' ado-ide-fullscreen' : '')} style={{ '--accent': ACCENT }}>
      <OhAppShell brand={BRAND} nav={APP_NAV} groups={APP_GROUPS} route={route} isActive={isActive}
        topbar={topbar} foot={foot} theme={theme} onToggle={onToggle}>
        <div className="ado-app-content">{screen}</div>
      </OhAppShell>
      <OhCommandK commands={cmds} label="AIDevObserver" />
    </div>
  );
}

// the auth card (centered, no shell) — kit OhAuth, wired to the identity realm; navigates to /dashboard on success
function AuthPage({ route, theme }) {
  const mode = route === '/signup' ? 'signup' : route === '/forgot' ? 'forgot' : 'signin';
  return (
    <div className={'oh dir-s theme-' + theme + ' oh-site ado'} style={{ '--accent': ACCENT }}>
      <OhAuth brand={BRAND} mode={mode} />
    </div>
  );
}

/* ===================== root ===================== */
function App() {
  const route = useAdoRoute();
  const [theme, toggle] = useSiteTheme('aidevobserver-theme');
  const inApp = APP_ROUTES.indexOf(route) !== -1 || route.startsWith('/ide/');
  const inAuth = AUTH_ROUTES.indexOf(route) !== -1;
  const inMarketingPage = Object.prototype.hasOwnProperty.call(MARKETING_PAGE_CONFIG, route);
  // app/auth render their own chrome; marketing detail pages are standalone instead of crammed onto home
  React.useEffect(() => {
    window.scrollTo(0, 0);
  }, [route, inApp, inAuth, inMarketingPage]);
  if (inApp) return <ObserverApp route={route} theme={theme} onToggle={toggle} />;
  if (inAuth) return <AuthPage route={route} theme={theme} />;
  if (inMarketingPage) return <MarketingPage route={route} theme={theme} onToggle={toggle} />;
  return <Landing theme={theme} onToggle={toggle} />;
}
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
