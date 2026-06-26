/* global React, ReactDOM, PORTFOLIO,
   useHashRoute, navigate, useSiteTheme,
   OhTopBar, OhHero, OhSection, OhFeatures, OhBand, OhFooter,
   OhLayout, OhTable, OhPageHead, OhRollup, OhThemeToggle */
// AIDevObserver: review how your team uses AI coding agents.
// A marketing app built ENTIRELY on the shared site kit (kit/oh-site.*), like the
// sibling surfaces. Only the brand config + a few product sections are local; all
// chrome (top bar, portfolio switcher, footer) and cards come from the kit.

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

// ---- where it runs: same review, four surfaces ----
const RUNS = [
  ['❮❯', 'VS Code extension',
    'Install from the marketplace. AIDevObserver watches the agent session in your editor and posts the report when you wrap up.'],
  ['➤', 'Cursor extension',
    'Same install, same report. If your team works in Cursor, the review shows up exactly where the work happens.'],
  ['⌁', 'MCP server for Claude Code',
    'Add one MCP server and Claude Code hands each session to AIDevObserver for review, inline with your run.'],
  ['❯_', 'Command line',
    'Prefer the terminal or CI? Run the review on the latest session and read the ranked findings as plain text or JSON.'],
];
const INSTALL_LINES = [
  ['Add the MCP server to Claude Code', 'claude mcp add aidevobserver -- python3 scripts/aidevobserver_mcp_server.py'],
  ['Review the latest session from the CLI', 'python3 -m src.teleon.observer.cli review --latest'],
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

const FINDINGS = [
  { type: 'Risky command', sev: 'high', conf: 0.97,
    text: 'The agent proposed git push --force on the shared main branch. Suggest a protected push or a feature branch instead.' },
  { type: 'Reinvention', sev: 'high', conf: 0.94,
    text: 'A new CSV parser was written from scratch. utils/csv.py already exports read_rows() with the same behavior.' },
  { type: 'Wasted context', sev: 'medium', conf: 0.88,
    text: 'The full 1,800-line schema was pasted into the prompt when about 40 lines were referenced. Trim to the tables in use.' },
  { type: 'Missed cheaper path', sev: 'medium', conf: 0.82,
    text: 'A large model looped over 50 files to find one constant. A single project search would answer it in one step.' },
];

// ---- trust: suggestions a human triages, read-only, nothing stored ----
const TRUST = [
  ['Suggestions, not gates', 'Every finding is a suggestion a person reviews and triages. AIDevObserver never blocks a commit, a push, or a merge.'],
  ['Read-only by design', 'It reads the session to write the report. It does not change your code, your branches, or your history.'],
  ['Nothing is stored', 'Reviews run locally and are not retained. When you close the session, the report is yours to keep or discard.'],
];

/* ===================== small bespoke pieces (styled in aidevobserver.css) ===================== */
function ConfBar({ conf }) {
  return (
    <span className="ado-conf" title={'Confidence ' + Math.round(conf * 100) + '%'}>
      <span className="ado-conf-track"><span className="ado-conf-fill" style={{ width: Math.round(conf * 100) + '%' }} /></span>
      <span className="ado-conf-n mono">{Math.round(conf * 100)}%</span>
    </span>
  );
}

function FindingRow({ f }) {
  return (
    <div className={'ado-finding sev-' + f.sev}>
      <span className="ado-finding-dot" aria-hidden="true" />
      <div className="ado-finding-b">
        <div className="ado-finding-h"><span className="ado-finding-type">{f.type}</span><ConfBar conf={f.conf} /></div>
        <div className="ado-finding-t">{f.text}</div>
      </div>
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
            <span className={'ado-hc-tag sev-' + f.sev}>{f.type}</span>
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

// the observer engine's finding types → the demo's display label + severity
const FINDING_LABELS = {
  reinvention: 'Reinvention', stack_reinvention: 'Reinvention', product_reinvention: 'Reinvention',
  reinvention_cluster: 'Reinvention', footgun: 'Risky command', oversized_context: 'Wasted context',
  duplicate_context: 'Wasted context', adversarial: 'Question the assumption', shortcut: 'Repeated action',
  guidance: 'Convention', alternative: 'Missed cheaper path',
};
function mapServerFinding(f) {
  const conf = typeof f.confidence === 'number' ? f.confidence : 0.5;
  const sev = conf >= 0.85 ? 'high' : conf >= 0.6 ? 'medium' : 'low';
  const label = FINDING_LABELS[f.type] || String(f.type || 'Finding').replace(/_/g, ' ');
  const text = [f.message, f.suggestion].filter(Boolean).join(' — ');
  return { type: label, sev, conf, text: text || f.message || '' };
}

// the live demo: paste a session (or load the example) → POST it to the observer backend
// (/api/observer/review) and render the REAL governed findings. On any error (no backend reachable,
// non-2xx, bad payload) fall back to the built-in client-side preview so the demo never breaks.
function ReviewDemo() {
  const [text, setText] = React.useState('');
  const [reviewed, setReviewed] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [findings, setFindings] = React.useState([]);
  const [source, setSource] = React.useState('live'); // 'live' = real backend · 'preview' = fallback

  const runReview = React.useCallback(async () => {
    const messages = parseSession(text || SESSION_EXAMPLE);
    setBusy(true);
    try {
      const res = await fetch('/api/observer/review', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
      });
      if (!res.ok) throw new Error('observer backend status ' + res.status);
      const data = await res.json();
      const report = Array.isArray(data.report) ? data.report : [];
      setFindings(report.map(mapServerFinding).sort((a, b) => b.conf - a.conf));
      setSource('live');
    } catch (e) {
      // backend unreachable/unhealthy → keep the demo alive with the client-side preview
      setFindings(FINDINGS.slice().sort((a, b) => b.conf - a.conf));
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
        <label className="ado-demo-label" htmlFor="ado-session">Paste an AI coding session</label>
        <textarea id="ado-session" className="ado-demo-ta" rows={8} value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={'Paste a transcript of an AI coding session, or load the example to see a review.'} />
        <div className="ado-demo-actions">
          <button className="oh-btn oh-btn--ghost" onClick={() => { setText(SESSION_EXAMPLE); setReviewed(false); }}>Load the example</button>
          <button className="oh-btn oh-btn--primary" disabled={busy} onClick={runReview}>{busy ? 'Reviewing…' : 'Review the session →'}</button>
        </div>
      </div>
      {reviewed && (
        <div className="oh-card oh-card--pad ado-demo-out">
          <div className="ado-demo-out-h">
            <span className="ado-demo-out-t">Review</span>
            <span className="oh-badge oh-badge--sm mono">{findings.length} findings · ranked</span>
          </div>
          {findings.length > 0 ? (
            <div className="ado-findings">
              {findings.map((f, i) => <FindingRow f={f} key={f.type + '-' + i} />)}
            </div>
          ) : (
            <div className="ado-demo-note mono">No findings — this session looks clean.</div>
          )}
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

/* ===================== sections ===================== */
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

/* ===================== landing ===================== */
function Landing({ theme, onToggle }) {
  return (
    <div className={'oh dir-s theme-' + theme + ' oh-site ado'} style={{ '--accent': ACCENT }}>
      <OhTopBar brand={BRAND} nav={MKT_NAV}
        cta={{ label: 'Open the app', href: '/app' }} theme={theme} onToggle={onToggle} />
      <OhHero
        eyebrow="AI coding session review"
        title={<>See how your team really uses <span className="tint">AI coding agents</span>.</>}
        lede="AIDevObserver reviews how your team uses AI coding agents and turns each session into a clear, ranked report. It flags reinvention, wasted context, risky commands, and cheaper paths you missed, so good habits spread and expensive ones do not."
        ctas={[
          { label: 'See a review →', onClick: () => scrollToId('demo'), primary: true },
          { label: 'Open the app', onClick: () => navigate('/app') },
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
        ['Product', [['How it works', '/how'], ['Where it runs', '/runs'], ['Live review', '/demo'], ['Trust', '/trust']]],
        ['Install', [['VS Code', '/runs'], ['Cursor', '/runs'], ['Claude Code (MCP)', '/runs'], ['Command line', '/runs']]],
        ['Family', [
          ['AI Done Right ↗', '../context-is-everything/Context is Everything.html'],
          ['Teleon ↗', '../teleon/Teleon Prototype.html'],
          ['Baltor ↗', '../context-enrichment/Context Enrichment Prototype.html'],
          ['OpenHubForAI ↗', '../openharnesshub/OpenHarnessHub Prototype.html'],
        ]],
      ]} />
    </div>
  );
}

/* ===================== the logged-in app (OhLayout variant="sidebar" + OhTable) ===================== */
// The app is the bulk of the product: pick a local session, review it, read the ranked findings. It rides the
// SAME shared kit as every sibling surface — the left-sidebar shell is OhLayout(variant="sidebar"), the sessions
// list is OhTable. It talks to the REAL observer backend over the same-origin seam (/api/observer/*), the exact
// service scripts/observer_local_service.py exposes. serves_truth=false; read-only; nothing is stored.

const APP_NAV = [
  ['/app', '◉', 'Review'],
  ['/app/sessions', '≡', 'Sessions'],
  ['/app/findings', '⚑', 'Findings'],
  ['/app/settings', '⚙', 'Settings'],
];

// settings install lines: the MCP + CLI lines from the marketing page, plus the live-coaching hook.
const APP_INSTALL = INSTALL_LINES.concat([
  ['Live coaching during a session (Claude Code PreToolUse hook)', 'python3 scripts/aidevobserver_hook.py --install'],
]);

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

// /app → Review (the paste-a-session demo, reused inside the shell)
function AppReview() {
  return (
    <>
      <OhPageHead eyebrow="Review" title="Review a session"
        sub="Paste an AI coding session, or load the example. AIDevObserver returns the findings ranked by confidence. Read only — nothing is stored." />
      <ReviewDemo />
    </>
  );
}

// /app/sessions → the discovered local Claude Code sessions, in an OhTable. Picking one reviews it.
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
        sub="AIDevObserver discovers your Claude Code sessions for this project. Pick one to review. Read only — discovery reads file metadata, never the transcript content." />
      {rows === null ? <div className="ohl-empty">Loading sessions…</div>
        : <OhTable cols={cols} rows={rows} rowKey={(r) => r.path} onRow={(r) => onReview(r)} empty={empty} />}
    </>
  );
}

// /app/findings → the most recent review's findings, ranked. Honest when the service was unreachable.
function AppFindings({ report, source, session, error }) {
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
  const findings = (report.report || []).map(mapServerFinding).sort((a, b) => b.conf - a.conf);
  const s = report.summary || {};
  return (
    <>
      <OhPageHead eyebrow="Findings" title={session ? ('Review · ' + shortId(session)) : 'Latest review'}
        sub="Every finding is a governed suggestion you triage. Read only — nothing is stored." />
      <OhRollup items={[
        ['Findings', s.findings != null ? s.findings : findings.length],
        ['Reinventions', s.reinventions != null ? s.reinventions : '—'],
        ['Waste signals', s.waste_signals != null ? s.waste_signals : '—'],
        ['Source', source === 'live' ? 'live engine' : 'preview'],
      ]} />
      {findings.length
        ? <div className="ado-findings">{findings.map((f, i) => <FindingRow f={f} key={f.type + '-' + i} />)}</div>
        : <div className="ohl-empty">No findings — this session looks clean.</div>}
    </>
  );
}

// /app/settings → install everywhere + the trust statements (read-only, nothing stored)
function AppSettings() {
  return (
    <>
      <OhPageHead eyebrow="Settings" title="Install and connect"
        sub="Run the same review wherever your team works: an editor extension, the Claude Code MCP server, the CLI, or a live in-session hook. Read only by design." />
      <div className="ado-installs">
        {APP_INSTALL.map(([label, cmd]) => <InstallLine label={label} cmd={cmd} key={cmd} />)}
      </div>
      <div className="ado-trust" style={{ marginTop: 18 }}>
        {TRUST.map(([t, d]) => (
          <div className="oh-card oh-card--pad ado-trust-item" key={t}>
            <div className="ado-trust-mk" aria-hidden="true">✓</div>
            <div><div className="ado-trust-t">{t}</div><div className="ado-trust-d">{d}</div></div>
          </div>
        ))}
      </div>
    </>
  );
}

function ObserverApp({ route, theme, onToggle }) {
  const [report, setReport] = React.useState(null);
  const [source, setSource] = React.useState('live');
  const [session, setSession] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [busyPath, setBusyPath] = React.useState(null);

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
    } finally { setBusyPath(null); navigate('/app/findings'); }
  }, []);

  const sub = (route || '').replace(/^\/app\/?/, '');
  let screen;
  if (sub === 'sessions') screen = <AppSessions onReview={runReview} busyPath={busyPath} />;
  else if (sub === 'findings') screen = <AppFindings report={report} source={source} session={session} error={error} />;
  else if (sub === 'settings') screen = <AppSettings />;
  else screen = <AppReview />;

  // exact-match the index route so "Review" is not also active on /app/sessions etc.
  const isActive = (h) => (h === '/app' ? (route === '/app' || route === '/app/') : (route === h || route.startsWith(h + '/')));
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
      <OhLayout variant="sidebar" brand={BRAND} sidebar={APP_NAV} route={route} isActive={isActive}
        foot={foot} theme={theme} onToggle={onToggle}>
        {screen}
      </OhLayout>
    </div>
  );
}

/* ===================== root ===================== */
function App() {
  const route = useHashRoute();
  const [theme, toggle] = useSiteTheme('aidevobserver-theme');
  const inApp = (route || '').replace(/^\//, '').startsWith('app');
  // marketing routes (/how, /runs, /demo, /trust) scroll to the section; the app routes (/app…) render the shell
  React.useEffect(() => {
    if (inApp) { window.scrollTo(0, 0); return; }
    const id = (route || '').replace(/^\//, '');
    if (id) scrollToId(id);
  }, [route, inApp]);
  if (inApp) return <ObserverApp route={route} theme={theme} onToggle={toggle} />;
  return <Landing theme={theme} onToggle={toggle} />;
}
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
