/* global React, ReactDOM, PORTFOLIO,
   useHashRoute, navigate, useSiteTheme,
   OhTopBar, OhHero, OhSection, OhFeatures, OhBand, OhFooter,
   OhLayout, OhAppShell, OhTable, OhPageHead, OhRollup, OhThemeToggle,
   OhAuth, OhDashboard, OhUsage, OhTeam, OhBilling, OhApiKeys,
   OhNotifications, OhSettings, OhSwitch, OhStatus, OhNotFound, OhCommandK */
// AIDevObserver: review how your team uses AI coding agents.
// ONE self-contained, hash-routed app on the shared site kit (kit/oh-site.*), like every sibling
// surface. It differs ONLY by accent (#b25fd6) + copy. Two layers:
//   - marketing (/, on-page sections) — OhTopBar / OhHero / OhSection / OhFooter
//   - the logged-in app (top-level routes: /dashboard /review /sessions /findings /agentic /reports
//     /notifications /members /billing /developer /account /settings /help) — the OhAppShell left
//     sidebar, every screen opening with OhPageHead, talking to the REAL observer backend over the
//     same-origin /api/observer/* seam (scripts/observer_local_service.py).
// serves_truth=false; read-only; nothing is stored; a BYO key is used per request, never stored or logged.

const ADO = PORTFOLIO.ENTITIES.aidevobserver;
const BRAND = { name: 'AIDevObserver', glyph: ADO.glyph, accent: ADO.accent };
const ACCENT = ADO.accent;

// smooth-scroll to an on-page section (the kit's OhSection renders id={id})
function scrollToId(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ---- marketing nav (on-page sections) ----
const MKT_NAV = [['How it works', '/how'], ['Where it runs', '/runs'], ['Live review', '/demo'], ['Trust', '/trust']];

// ---- how it works: a session becomes a ranked report ----
const HOW = [
  ['◉', 'Every session becomes a report',
    'AIDevObserver captures the agent session and turns it into a short, ranked report you can read in under a minute.'],
  ['⚑', 'It flags what actually costs you',
    'Reinvention (rebuilding what already exists), wasted context (oversized or duplicate), risky commands, and cheaper paths you missed.'],
  ['↑', 'Ranked by confidence',
    'High-confidence findings rise to the top and low-signal noise drops away, so the report stays worth reading every time.'],
  ['◑', 'Report after, prompts during',
    'You get a full report after the session, plus optional in-session prompts the moment something looks off.'],
];

// ---- where it runs: same review, every surface ----
const RUNS = [
  ['❮❯', 'VS Code extension',
    'Install from the marketplace. AIDevObserver watches the agent session in your editor and posts the report when you wrap up.'],
  ['➤', 'Cursor extension',
    'Same install, same report. If your team works in Cursor, the review shows up exactly where the work happens.'],
  ['⌁', 'MCP server for Claude Code',
    'Add one MCP server and Claude Code hands each session to AIDevObserver for review, inline with your run.'],
  ['❯_', 'Command line',
    'Prefer the terminal or CI? Run the review on the latest session and read the ranked findings as plain text or JSON.'],
  ['⤓', 'Manual upload / paste',
    'No editor integration? Upload a transcript file (.jsonl from Claude Code or Codex, or plain text) or paste it into the app and get the same ranked review.'],
  ['◑', 'Live in-session hook',
    'Add a Claude Code PreToolUse hook and AIDevObserver coaches the moment a tool call looks like a footgun, reinvention, or waste, non-blocking and read-only.'],
  ['◎', 'Zero-install discovery',
    'It already finds your local Claude Code / Codex sessions (under ~/.claude/projects), no setup. Pick one in the app or CLI and review it.'],
];
const INSTALL_LINES = [
  ['Add the MCP server to Claude Code', 'claude mcp add aidevobserver -- python3 scripts/aidevobserver_mcp_server.py'],
  ['Review the latest session from the CLI', 'python3 -m src.teleon.observer.cli review --latest'],
  ['Coach live during a session (PreToolUse hook)', 'python3 scripts/aidevobserver_hook.py --install'],
];

// the /api/observer/* endpoints the Developer screen documents (real, served by observer_local_service.py)
const API_ENDPOINTS = [
  ['POST', '/api/observer/review', 'Review a session. Body { messages:[…] } or { transcript_path }. Returns the ranked report.'],
  ['GET', '/api/observer/sessions', 'Discover local Claude Code / Codex sessions (metadata only, never transcript content).'],
  ['POST', '/api/observer/live', 'Intra-session check. The interruption budget caps would_interrupt.'],
  ['POST', '/api/observer/agentic', 'Supervise an autonomous agent loop. Returns a verdict + loop-shape findings.'],
];

// ---- a worked example review (the live demo's preview output), ranked by confidence ----
const SESSION_EXAMPLE = [
  'user: add a CSV import to the importer',
  "agent: I'll write a CSV parser. Creating parse_csv() in importer.py",
  'agent: pasting the full schema for reference (1,800 lines)',
  'agent: tests pass. Run: git push --force origin main',
  'user: also find where MAX_ROWS is defined',
  'agent: scanning all 50 files in src/ with the model',
].join('\n');

// the worked-example findings (preview fallback). Each carries the full finding-card shape:
// family-toned type, confidence, message, suggestion, evidence, a source_ref, optional reuse savings.
const FINDINGS = [
  { type: 'footgun', label: 'Risky command', conf: 0.97,
    message: 'The agent proposed git push --force on the shared main branch.',
    suggestion: 'Use a protected push or a feature branch instead so history cannot be destroyed.',
    evidence: 'git push --force origin main' },
  { type: 'reinvention', label: 'Reinvention', conf: 0.94,
    message: 'A new CSV parser was written from scratch.',
    suggestion: 'Reuse utils/csv.py, which already exports read_rows() with the same behavior.',
    evidence: 'def parse_csv(path): ...  # new, ~40 lines',
    source: { kind: 'existing', registry: 'stack_components', name: 'utils.csv.read_rows' },
    savings: { dollars: 0, hours: 1.5 } },
  { type: 'oversized_context', label: 'Wasted context', conf: 0.88,
    message: 'The full 1,800-line schema was pasted into the prompt when about 40 lines were referenced.',
    suggestion: 'Trim to the tables in use; oversized context costs tokens and dilutes attention.',
    evidence: '# schema.sql (1,800 lines pasted)' },
  { type: 'alternative', label: 'Missed cheaper path', conf: 0.82,
    message: 'A large model looped over 50 files to find one constant.',
    suggestion: 'A single project search answers it in one step at a fraction of the cost.',
    evidence: 'scanning all 50 files in src/ with the model',
    savings: { dollars: 0.4, hours: 0 } },
];

// ---- trust: suggestions a human triages, read-only, nothing stored ----
const TRUST = [
  ['Suggestions, not gates', 'Every finding is a suggestion a person reviews and triages. AIDevObserver never blocks a commit, a push, or a merge.'],
  ['Read-only by design', 'It reads the session to write the report. It does not change your code, your branches, or your history.'],
  ['Nothing is stored', 'Reviews run locally and are not retained. When you close the session, the report is yours to keep or discard.'],
];

/* ===================== the finding card (the core component) ===================== */
// the observer engine's finding types → display label + the family that tones the card
const FINDING_LABELS = {
  reinvention: 'Reinvention', stack_reinvention: 'Reinvention', product_reinvention: 'Reinvention',
  reinvention_cluster: 'Reinvention', footgun: 'Risky command', oversized_context: 'Wasted context',
  duplicate_context: 'Wasted context', adversarial: 'Question the assumption', shortcut: 'Repeated action',
  guidance: 'Convention', alternative: 'Missed cheaper path', agentic_loop: 'Loop / thrash',
  agentic_repeated_failure: 'Repeated failure', agentic_stall: 'Stall', agentic_budget: 'Budget overrun',
  agentic_goal_drift: 'Goal drift',
};
// family → card tone: reinvention = accent, waste = amber, footgun = red (redacted evidence), else neutral
function findingFamily(type) {
  const t = String(type || '');
  if (t.indexOf('reinvention') !== -1) return 'reinvention';
  if (t === 'oversized_context' || t === 'duplicate_context') return 'waste';
  if (t === 'footgun') return 'footgun';
  if (t.indexOf('agentic') !== -1) return 'agentic';
  return 'neutral';
}
function mapServerFinding(f) {
  const conf = typeof f.confidence === 'number' ? f.confidence : 0.5;
  const type = f.type || 'finding';
  const label = FINDING_LABELS[type] || String(type).replace(/_/g, ' ');
  // source_ref: the grounding that makes "already exists" trustworthy (registry deep-link or covering package)
  let source = null;
  const sr = f.source_ref || f.source || null;
  if (sr) {
    if (sr.existing || sr.registry) source = { kind: 'existing', registry: sr.registry || (sr.existing && sr.existing.registry), name: sr.name || (sr.existing && sr.existing.name) };
    else if (sr.covering || sr.package) source = { kind: 'covering', package: sr.package || (sr.covering && sr.covering.package), provides: sr.provides || (sr.covering && sr.covering.provides) };
  }
  return {
    type, family: findingFamily(type), label, conf,
    message: f.message || '', suggestion: f.suggestion || '',
    evidence: f.evidence || '', source: source || f.source || null,
    savings: f.savings || null,
  };
}
const FINDING_KEY = (f, i) => (f.type || 'f') + '-' + Math.round((f.conf || 0) * 100) + '-' + i;

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

// the full finding card: family-toned type chip, confidence, message, evidence (redacted for footgun),
// suggestion, source_ref, optional reuse savings, and the Accept / Reuse / Dismiss outcome a person triages.
function FindingCard({ f, fkey, outcome, onOutcome }) {
  const savings = f.savings && (f.savings.dollars || f.savings.hours)
    ? [f.savings.hours ? f.savings.hours + 'h saved' : null, f.savings.dollars ? '$' + f.savings.dollars + ' saved' : null].filter(Boolean).join(' · ')
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
        <div className="ado-finding-f">
          <div className="ado-finding-refs">
            <SourceRef source={f.source} />
            {savings && <span className="ado-src ado-src--save"><span className="ado-src-k">reuse</span><span className="mono">{savings}</span></span>}
          </div>
          {onOutcome ? (
            <div className="ado-finding-act">
              <button className={'ado-out' + (outcome === 'accepted' ? ' on' : '')} onClick={() => onOutcome(fkey, outcome === 'accepted' ? null : 'accepted')}>Accept</button>
              <button className={'ado-out' + (outcome === 'reused' ? ' on' : '')} onClick={() => onOutcome(fkey, outcome === 'reused' ? null : 'reused')}>Reuse</button>
              <button className={'ado-out' + (outcome === 'dismissed' ? ' on' : '')} onClick={() => onOutcome(fkey, outcome === 'dismissed' ? null : 'dismissed')}>Dismiss</button>
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

// turn a pasted "role: text" transcript into engine messages (role inferred; default user)
function parseSession(text) {
  return String(text || '').split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
    const m = line.match(/^(user|agent|assistant|tool|system)\s*:\s*(.*)$/i);
    if (!m) return { role: 'user', content: line };
    const r = m[1].toLowerCase();
    return { role: r === 'agent' ? 'assistant' : r, content: m[2] };
  });
}

// the live review: paste a session (or upload / load the example) → POST it to the observer backend
// (/api/observer/review) and render the REAL governed findings. On any error (no backend reachable,
// non-2xx, bad payload) fall back to the built-in client-side preview so the demo never breaks.
function ReviewDemo({ outcomes, onOutcome }) {
  const [text, setText] = React.useState('');
  const [reviewed, setReviewed] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [findings, setFindings] = React.useState([]);
  const [source, setSource] = React.useState('live'); // 'live' = real backend · 'preview' = fallback
  const [error, setError] = React.useState('');
  const fileRef = React.useRef(null);

  // manual upload: read a transcript FILE (.jsonl/.json/.txt/.md, Claude Code or Codex) into the box; it then
  // reviews exactly like a paste. Read-only, in-browser — the file is never uploaded anywhere.
  const onUpload = React.useCallback((e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => { setText(String(reader.result || '')); setReviewed(false); setError(''); };
    reader.readAsText(file);
    e.target.value = '';   // allow re-selecting the same file
  }, []);

  const runReview = React.useCallback(async () => {
    const raw = text || SESSION_EXAMPLE;
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

  const note = source === 'preview'
    ? 'Preview review (the observer backend was not reachable). Installed, AIDevObserver reviews your real sessions on your machine.'
    : (findings.length
        ? 'Live review from the observer engine on this machine. Every finding is a governed suggestion you triage — nothing is stored.'
        : 'Live review from the observer engine — no findings on this session. It looks clean.');

  return (
    <div className="ado-demo">
      <div className="oh-card oh-card--pad ado-demo-in">
        <label className="ado-demo-label" htmlFor="ado-session">Paste or upload an AI coding session</label>
        <textarea id="ado-session" className="ado-demo-ta" rows={8} value={text}
          onChange={(e) => { setText(e.target.value); setError(''); }}
          placeholder={'Paste a transcript (Claude Code or Codex), upload a .jsonl / .txt file, or load the example.'} />
        <input ref={fileRef} type="file" accept=".jsonl,.json,.txt,.md,.log" style={{ display: 'none' }} onChange={onUpload} />
        {error && <div className="ado-demo-err mono">{error}</div>}
        <div className="ado-demo-actions">
          <button className="oh-btn oh-btn--ghost" onClick={() => fileRef.current && fileRef.current.click()}>Upload a transcript</button>
          <button className="oh-btn oh-btn--ghost" onClick={() => { setText(SESSION_EXAMPLE); setReviewed(false); setError(''); }}>Load the example</button>
          <button className="oh-btn oh-btn--primary" disabled={busy} onClick={runReview}>{busy ? 'Reviewing…' : 'Review the session →'}</button>
        </div>
      </div>
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
          <FindingList report={findings} mapped outcomes={outcomes} onOutcome={onOutcome} />
          <div className="ado-demo-note mono">{note}</div>
        </div>
      )}
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

/* ===================== marketing sections ===================== */
function SecHow() {
  return (
    <OhSection id="how" label="How it works"
      title="A session goes in. A clear, ranked report comes out."
      body={<>AIDevObserver turns each AI coding session into a report your team can act on. It flags reinvention, wasted
        context, risky commands, and missed cheaper paths, then ranks them so the most useful findings are the first ones you read.</>}>
      <OhFeatures items={HOW} />
    </OhSection>
  );
}

function SecRuns() {
  return (
    <OhSection id="runs" label="Where it runs"
      title="One review, wherever your team already works."
      body={<>Install AIDevObserver as a VS Code or Cursor extension, add it to Claude Code as an MCP server, or run it from
        the command line. The same review shows up in every surface, so the whole team reads from one report.</>}>
      <div className="ado-runs">
        {RUNS.map(([g, t, d]) => (
          <div className="oh-card oh-card--pad ado-run" key={t}>
            <div className="ado-run-i" aria-hidden="true">{g}</div>
            <h4 className="ado-run-t">{t}</h4>
            <p className="ado-run-d">{d}</p>
          </div>
        ))}
      </div>
      <div className="ado-installs">
        {INSTALL_LINES.map(([label, cmd]) => <InstallLine label={label} cmd={cmd} key={cmd} />)}
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
      <ReviewDemo />
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
function Landing({ theme, onToggle }) {
  return (
    <div className={'oh dir-s theme-' + theme + ' oh-site ado'} style={{ '--accent': ACCENT }}>
      <OhTopBar brand={BRAND} nav={MKT_NAV} signInHref="/signin"
        cta={{ label: 'Open the app', href: '/dashboard' }} theme={theme} onToggle={onToggle} />
      <OhHero
        eyebrow="AI coding session review"
        title={<>See how your team really uses <span className="tint">AI coding agents</span>.</>}
        lede="AIDevObserver reviews how your team uses AI coding agents and turns each session into a clear, ranked report. It flags reinvention, wasted context, risky commands, and cheaper paths you missed, so good habits spread and expensive ones do not."
        ctas={[
          { label: 'See a review →', onClick: () => scrollToId('demo'), primary: true },
          { label: 'Open the app', onClick: () => navigate('/dashboard') },
        ]}
        aside={<HeroReviewCard />} />
      <SecHow />
      <SecRuns />
      <SecDemo />
      <SecTrust />
      <OhBand title="Make every AI coding session count."
        sub="Install AIDevObserver and turn raw agent sessions into reports your team actually learns from."
        ctas={[
          { label: 'Install the extension →', href: '/runs', primary: true },
          { label: 'See a review', href: '/demo' },
        ]} />
      <OhFooter brand={BRAND} tagline="AI coding session review · part of AI Done Right" cols={[
        ['Product', [['How it works', '/how'], ['Where it runs', '/runs'], ['Live review', '/demo'], ['Trust', '/trust'], ['Pricing', '/billing']]],
        ['Install', [['VS Code', '/runs'], ['Cursor', '/runs'], ['Claude Code (MCP)', '/runs'], ['Command line', '/runs']]],
        ['Family', FAMILY_LINKS],
      ]} />
    </div>
  );
}

/* ===================== the logged-in app (OhAppShell + the kit pages) ===================== */
// top-level routes, the kit conventions (OhAuth → /dashboard, the shell foot → /settings). The sidebar is the
// shared OhAppShell; the work screens talk to the REAL observer backend over /api/observer/*. serves_truth=false.

const APP_NAV = [
  ['/dashboard', '◉', 'Dashboard'],
  ['/review', '▷', 'Review'],
  ['/sessions', '≡', 'Sessions'],
  ['/findings', '⚑', 'Findings'],
  ['/agentic', '⟳', 'Agentic'],
  ['/reports', '◈', 'Reports'],
];
const APP_GROUPS = [
  { label: 'Workspace', defaultOpen: true, items: [
    ['/notifications', '◔', 'Notifications'],
    ['/members', '◑', 'Team'],
    ['/billing', '▤', 'Billing'],
    ['/developer', '⌘', 'Developer'],
  ] },
  { label: 'You', defaultOpen: false, items: [
    ['/account', '◓', 'Account'],
    ['/settings', '⚙', 'Settings'],
    ['/help', '?', 'Help'],
  ] },
];
// every app route (for route detection + the command palette)
const APP_ROUTES = APP_NAV.map((n) => n[0]).concat(APP_GROUPS.reduce((a, g) => a.concat(g.items.map((i) => i[0])), []));
const AUTH_ROUTES = ['/signin', '/signup', '/forgot'];

// settings install lines: the MCP + CLI lines from the marketing page, plus the live-coaching hook.
const APP_INSTALL = INSTALL_LINES.slice();

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
  const sessCount = Array.isArray(sessions) ? sessions.length : null;
  const lastFindings = lastReport ? (lastReport.report || []).length : null;
  const triaged = outcomes ? Object.keys(outcomes).length : 0;
  const reused = outcomes ? Object.values(outcomes).filter((o) => o === 'reused').length : 0;
  const reuseRate = triaged ? Math.round((reused / triaged) * 100) + '%' : '—';
  const stats = [
    ['Local sessions', sessCount == null ? '—' : sessCount],
    ['Last review findings', lastFindings == null ? '—' : lastFindings],
    ['Findings triaged', triaged || '—'],
    ['Reuse rate', reuseRate],
  ];
  const activity = (Array.isArray(sessions) ? sessions.slice(0, 4) : []).map((s) => ({
    icon: '◉', text: (s.project || 'session') + ' · ' + shortId(s.session_id), when: relTime(s.mtime),
  }));
  if (!activity.length) activity.push({ icon: '◷', text: 'No sessions discovered yet — start one or paste a transcript.', when: '' });
  const quick = [
    { title: 'Review a session', desc: 'Paste or upload a transcript and read the ranked report.', href: '/review', cta: 'Review' },
    { title: 'Browse local sessions', desc: 'Pick a discovered Claude Code or Codex session.', href: '/sessions', cta: 'Open' },
    { title: 'Supervise an agent loop', desc: 'Watch an autonomous run for thrash, stalls and runaways.', href: '/agentic', cta: 'Supervise' },
    { title: 'Connect your editor', desc: 'VS Code, Cursor, the MCP server, or a live hook.', href: '/settings', cta: 'Connect' },
  ];
  return (
    <OhDashboard greeting="Your AI-usage workspace"
      sub="Every AI coding session, reviewed and ranked. Read only — nothing is stored."
      stats={stats} activity={activity} quick={quick}
      plan={{ name: 'Team · usage-metered', usagePct: 38, usageLabel: 'Sessions reviewed this period' }} />
  );
}

// /review → the paste/upload-a-session review, reused inside the shell (real /api/observer/review)
function AppReview({ outcomes, onOutcome }) {
  return (
    <>
      <OhPageHead eyebrow="Review" title="Review a session"
        sub="Paste an AI coding session, or load the example. AIDevObserver returns the findings ranked by confidence. Read only — nothing is stored." />
      <ReviewDemo outcomes={outcomes} onOutcome={onOutcome} />
    </>
  );
}

// /sessions → the discovered local Claude Code / Codex sessions, in an OhTable. Picking one reviews it.
function AppSessions({ onReview, busyPath }) {
  const [rows, setRows] = React.useState(null);   // null = loading, [] = none
  const [err, setErr] = React.useState(false);
  React.useEffect(() => {
    let live = true;
    fetch('/api/observer/sessions')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { if (live) setRows(Array.isArray(d.sessions) ? d.sessions : []); })
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
    : 'No local sessions found yet. Start a Claude Code session in this project, or paste one on the Review page.';
  return (
    <>
      <OhPageHead eyebrow="Sessions" title="Local AI coding sessions"
        sub="AIDevObserver discovers your Claude Code and Codex sessions for this project. Pick one to review. Read only — discovery reads file metadata, never the transcript content." />
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
        <div className="ohl-empty">Nothing reviewed yet this session.</div>
      </>
    );
  }
  const findings = (report.report || []).map(mapServerFinding);
  const s = report.summary || {};
  return (
    <>
      <OhPageHead eyebrow="Findings" title={session ? ('Review · ' + shortId(session)) : 'Latest review'}
        sub="Every finding is a governed suggestion you triage with Accept / Reuse / Dismiss. Read only — nothing is stored." />
      <OhRollup items={[
        ['Findings', s.findings != null ? s.findings : findings.length],
        ['Reinventions', s.reinventions != null ? s.reinventions : '—'],
        ['Waste signals', s.waste_signals != null ? s.waste_signals : '—'],
        ['Source', source === 'live' ? 'live engine' : 'preview'],
      ]} />
      <FindingList report={findings} mapped outcomes={outcomes} onOutcome={onOutcome} />
    </>
  );
}

// a worked agentic loop (a thrashing, then footgun-ending, run) the Agentic screen supervises
const AGENTIC_EXAMPLE = [
  { action: 'run pytest tests/importer', ok: false, error: 'ImportError: no module named csvkit' },
  { action: 'run pytest tests/importer', ok: false, error: 'ImportError: no module named csvkit' },
  { action: 'run pytest tests/importer', ok: false, error: 'ImportError: no module named csvkit' },
  { action: 'pip install csvkit && git push --force origin main', ok: true },
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
        { type: 'footgun', confidence: 0.85, message: 'a force-push to a shared branch can destroy history', suggestion: 'use a protected push or a feature branch instead', evidence: 'git push --force origin main' },
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
        sub="Where reinvention, waste and risk concentrate, and where reuse is paying off. Aggregates are illustrative until the metering seam is wired (serves_truth = false)."
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

// /notifications → kit OhNotifications with AIDevObserver copy
function AppNotifications() {
  return <OhNotifications items={[
    { icon: '⚑', t: 'A risky command was flagged', d: 'importer session · git push --force', w: '12m ago', unread: true },
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
        <div className="ado-installs">
          {APP_INSTALL.map(([label, cmd]) => <InstallLine label={label} cmd={cmd} key={cmd} />)}
        </div>
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
    <OhSettings sections={[
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
        sub="Pick how present it is, cap its interruptions, point it at your own model and your internal registries. Read only by design — it never blocks." />
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
          <div className="ohs-hint mono">So "already exists" also covers your team's private libraries — the highest-value catch.</div>
        </div>
      </div>
      <div className="ohs-settings-sec">
        <h3>Install and connect</h3>
        <div className="ado-installs">
          {APP_INSTALL.map(([label, cmd]) => <InstallLine label={label} cmd={cmd} key={cmd} />)}
        </div>
      </div>
    </>
  );
}

// /help → support + the install/MCP/CLI/hook lines
function AppHelp() {
  return (
    <>
      <OhPageHead eyebrow="Help" title="Get AIDevObserver running"
        sub="Connect it where your team works, then read your first ranked report. Read only — nothing is stored." />
      <div className="ohs-grid-3" style={{ marginTop: 4 }}>
        {[['◉', 'Quick start', 'Discover a local session and review it in under a minute.', '/sessions'],
          ['⚑', 'Reading a report', 'Findings are ranked by confidence and triaged with Accept / Reuse / Dismiss.', '/findings'],
          ['⟳', 'Supervising loops', 'Point AIDevObserver at an autonomous run to catch thrash and runaways.', '/agentic']].map(([g, t, d, h]) => (
          <button className="oh-card oh-card--pad oh-card--interactive ohs-feature" key={t} onClick={() => navigate(h)} style={{ cursor: 'pointer', textAlign: 'left' }}>
            <div className="fi">{g}</div><h4>{t}</h4><p>{d}</p>
          </button>
        ))}
      </div>
      <div className="ohs-settings-sec" style={{ marginTop: 18 }}>
        <h3>Connect</h3>
        <div className="ado-installs">
          {APP_INSTALL.map(([label, cmd]) => <InstallLine label={label} cmd={cmd} key={cmd} />)}
        </div>
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

  // the outcome a person triages (Accept/Reuse/Dismiss) — the product's compounding signal; reflected on Findings
  const onOutcome = React.useCallback((k, v) => {
    setOutcomes((m) => { const next = Object.assign({}, m); if (v == null) delete next[k]; else next[k] = v; return next; });
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
        body: JSON.stringify({ transcript_path: sess.path }),
      });
      if (!res.ok) throw new Error('observer backend status ' + res.status);
      const data = await res.json();
      setReport(data); setSource('live'); setSession(sess.session_id);
    } catch (e) {
      setReport(null);
      setError('The observer service was not reachable, so this session was not reviewed. Discovery is metadata only — the transcript is never read in the browser.');
      setSession(sess.session_id);
    } finally { setBusyPath(null); navigate('/findings'); }
  }, []);

  let screen;
  if (route === '/sessions') screen = <AppSessions onReview={runReview} busyPath={busyPath} />;
  else if (route === '/findings') screen = <AppFindings report={report} source={source} session={session} error={error} outcomes={outcomes} onOutcome={onOutcome} />;
  else if (route === '/agentic') screen = <AppAgentic outcomes={outcomes} onOutcome={onOutcome} />;
  else if (route === '/reports') screen = <AppReports />;
  else if (route === '/notifications') screen = <AppNotifications />;
  else if (route === '/members') screen = <AppMembers />;
  else if (route === '/billing') screen = <AppBilling />;
  else if (route === '/developer') screen = <AppDeveloper />;
  else if (route === '/account') screen = <AppAccount />;
  else if (route === '/settings') screen = <AppSettings />;
  else if (route === '/help') screen = <AppHelp />;
  else if (route === '/review') screen = <AppReview outcomes={outcomes} onOutcome={onOutcome} />;
  else screen = <AppDashboard sessions={sessions} lastReport={report} outcomes={outcomes} />;

  const isActive = (h) => (route === h || route.startsWith(h + '/'));
  const cmds = OhCommandK.fromNav(APP_NAV, APP_GROUPS).concat([
    { label: 'Open the marketing site', href: '/', icon: '↗', group: 'Actions' },
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
      <button className="ado-appbar-ic" title="Notifications" onClick={() => navigate('/notifications')} aria-label="Notifications">◔</button>
      <span className="ado-avatar" title="Ada Lovelace">A</span>
    </div>
  );
  const foot = (
    <>
      <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ width: '100%', justifyContent: 'center' }}
        onClick={() => navigate('/')}>← Back to site</button>
      <div className="ohs-side-foot-row">
        <span className="mono" style={{ fontSize: 11, color: 'var(--fg-muted)' }}>Read only</span>
        {onToggle && <OhThemeToggle theme={theme} onToggle={onToggle} />}
      </div>
    </>
  );

  return (
    <div className={'oh dir-s theme-' + theme + ' oh-site ado'} style={{ '--accent': ACCENT }}>
      <OhAppShell brand={BRAND} nav={APP_NAV} groups={APP_GROUPS} route={route} isActive={isActive}
        topbar={topbar} foot={foot} theme={theme} onToggle={onToggle}>
        {screen}
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
  const route = useHashRoute();
  const [theme, toggle] = useSiteTheme('aidevobserver-theme');
  const inApp = APP_ROUTES.indexOf(route) !== -1;
  const inAuth = AUTH_ROUTES.indexOf(route) !== -1;
  // marketing on-page routes (/how, /runs, /demo, /trust) scroll to the section; app/auth render their own chrome
  React.useEffect(() => {
    if (inApp || inAuth) { window.scrollTo(0, 0); return; }
    const id = (route || '').replace(/^\//, '');
    if (id) scrollToId(id);
  }, [route, inApp, inAuth]);
  if (inApp) return <ObserverApp route={route} theme={theme} onToggle={toggle} />;
  if (inAuth) return <AuthPage route={route} theme={theme} />;
  return <Landing theme={theme} onToggle={toggle} />;
}
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
