/* global React, ReactDOM, PRODUCTS, PORTFOLIO,
   useHashRoute, navigate, useSiteTheme,
   OhTopBar, OhHero, OhSection, OhFeatures, OhBand, OhFooter,
   OhAppShell, OhPageHead, OhRollup, OhAuth, OhBilling, OhUsage, OhSettings, OhSwitch */
// Teleon.dev — purpose-driven runtime. A new family site built ENTIRELY on the
// shared site kit (shared/oh-site.*). Only brand config + a few runtime-specific
// pages are local; all chrome + primitive pages come from the kit.

const T = PORTFOLIO.ENTITIES.teleon;
const BRAND = { name: 'Teleon', tld: '.dev', glyph: '⟳', accent: T.accent };
const ACCENT = T.accent;

// ---- the capability lifecycle, in plain language [label, gloss] ----
// (canonical technical terms live in PORTFOLIO.GROUP.flow for the parent diagram;
//  here we speak to the customer.)
const LIFECYCLE = [
  ['Purpose', 'what you want done'],
  ['Success criteria', 'how you’ll know'],
  ['Approach', 'Teleon’s plan'],
  ['Candidate', 'a version to try'],
  ['Evidence', 'tested for real'],
  ['Promote / roll back', 'passes, or reverts'],
];

// ---- marketing nav / app nav ----
const MKT_NAV = [['How it works', '/#how'], ['Lifecycle', '/#lifecycle'], ['Where it fits', '/fits'], ['Cases', '/cases'], ['Pricing', '/pricing'], ['Docs', '/docs']];
const APP_NAV = [
  ['/dashboard', '▤', 'Dashboard'],
  ['/app', '◈', 'Capabilities'],
  ['/runs', '⊕', 'Build'],
  ['/evidence', '✓', 'Evidence'],
  ['/keys', '⚿', 'API keys'],
  ['/team', '○', 'Team'],
  ['/audit', '⚖', 'Audit'],
  ['/notifications', '◉', 'Inbox'],
  ['/billing', '◷', 'Billing'],
];
// ⌘K command palette — nav + key marketing/account destinations (shared OhCommandK)
const TELEON_CMDS = [
  ...window.OhCommandK.fromNav(APP_NAV),
  { label: 'Home', href: '/', icon: '⌂', group: 'Marketing' },
  { label: 'Pricing', href: '/pricing', icon: '◷', group: 'Marketing' },
  { label: 'Case studies', href: '/cases', icon: '★', group: 'Marketing' },
  { label: 'Where it fits', href: '/fits', icon: '↔', group: 'Marketing' },
  { label: 'About', href: '/about', icon: 'ⓘ', group: 'Marketing' },
  { label: 'Docs', href: '/docs', icon: '▭', group: 'Marketing' },
  { label: 'Settings', href: '/settings', icon: '⚙', group: 'Account' },
  { label: 'Contact', href: '/contact', icon: '✉', group: 'Account' },
];

/* ===================== MARKETING ===================== */
function TeleonHeroCard() {
  return (
    <div className="oh-card tln-herocard">
      <div className="thc-head"><span className="thc-eyebrow">capability</span><span className="oh-badge oh-badge--verified oh-badge--sm">✔ shipped</span></div>
      <div className="thc-purpose">“Find each US state’s maximum legal interest rate, with the statute cited for every state”</div>
      <div className="thc-crit">
        <div className="crit"><span className="ck">✓</span> cites the live statute per state</div>
        <div className="crit"><span className="ck">✓</span> re-checks when the law changes</div>
      </div>
      <div className="thc-foot"><span className="mono">passed across all 50 states</span><span className="thc-score">0.96</span></div>
    </div>
  );
}

function LifecycleRail() {
  return (
    <ol className="tln-rail">
      {LIFECYCLE.map(([label, gloss], i) => (
        <li className="tln-rail-step" key={label}>
          <span className="st">
            <span className="n">{String(i + 1).padStart(2, '0')}</span>
            <span className="lbl">{label}</span>
            <span className="gloss">{gloss}</span>
          </span>
          {i < LIFECYCLE.length - 1 && <span className="arr">→</span>}
        </li>
      ))}
    </ol>
  );
}

// hero second-line A/B variants — run through the shared experiments engine (window.OHExp
// via useExperiment). Cycle with the in-hero pill, force with ?exp=teleon_hero:B.
const HERO_LINES = { A: 'We prove the rest.', B: 'Skip the agent.', C: 'We build the capability.', D: 'We make it dependable.' };

// landing body sections (named, so the layout experiment can re-sequence them)
function SecHow() {
  return (
    <OhSection id="how" label="How it works" title="Unbounded in. Deterministic, proven, and cheap out."
      body={<>Describe an <strong>outcome</strong> and the <strong>guardrails</strong> it must respect. Teleon works out the
        approach, proves it on real examples, and locks it into a deterministic capability — then keeps improving it
        without blowing up your token bill.</>}>
      <OhFeatures items={[
        ['◎', 'Outcomes and guardrails', 'You define what good looks like and the limits it must stay within. Teleon figures out the how — no glue code, no orchestration to maintain.'],
        ['◇', 'Unbounded → deterministic', 'It collapses an open-ended agent task into a fixed, repeatable capability — same input, same proven result, every run.'],
        ['⟳', 'Self-improving, far cheaper', 'It adapts and re-proves itself when sources or requirements change — at a fraction of the tokens a full agent burns on every call.'],
      ]} />
    </OhSection>
  );
}
function SecLifecycle() {
  return (
    <OhSection id="lifecycle" label="The path" title="From purpose to proven — one clear path."
      body="You define the outcome and the guardrails; Teleon handles the rest and shows its work. Nothing ships until it clears them — and it keeps re-proving itself as the world changes.">
      <LifecycleRail />
    </OhSection>
  );
}
function SecEcosystem() {
  return (
    <OhSection label="Ecosystem" title="Built on open building blocks. Delivers finished capabilities."
      body={<>Teleon draws ready-made skills, templates and tests from the open hubs, and delivers finished capabilities
        to products like <strong>Baltor</strong> — handing back the result and the evidence behind it, never your data.</>}>
      <div className="tln-ports">
        <div className="oh-card oh-card--pad tln-port">
          <div className="pf"><span className="pn src">OpenHarnessHub</span><span className="pa">→</span><span className="pn dst">Teleon</span></div>
          <p>Ready-made skills, templates &amp; tests flow in from the open ecosystem.</p>
        </div>
        <div className="oh-card oh-card--pad tln-port">
          <div className="pf"><span className="pn src">Baltor</span><span className="pa">→</span><span className="pn dst">Teleon</span></div>
          <p>Products ask for a capability and get back the result with its evidence — never their own data. <span className="mono">PurposeTaskProviderPort</span></p>
        </div>
      </div>
    </OhSection>
  );
}
// landing layout A/B — same sections, re-sequenced into different narratives
const TLN_SECTIONS = { how: SecHow, lifecycle: SecLifecycle, ecosystem: SecEcosystem };
const TLN_LAYOUTS = {
  default: ['how', 'lifecycle', 'ecosystem'],
  proof: ['lifecycle', 'how', 'ecosystem'],
  ecosystem: ['ecosystem', 'how', 'lifecycle'],
};

function Landing({ theme, onToggle }) {
  const [hv, hero] = useExperiment('teleon_hero', ['A', 'B', 'C', 'D']);
  const [layout] = useExperiment('teleon_landing', Object.keys(TLN_LAYOUTS));
  const order = TLN_LAYOUTS[layout] || TLN_LAYOUTS.default;
  const heroLine = HERO_LINES[hv] || HERO_LINES.A;
  const cycleHero = () => { const ids = Object.keys(HERO_LINES); hero.assign(ids[(ids.indexOf(hv) + 1) % ids.length]); };
  const startFree = (where) => { hero.track('cta_click', { cta: 'start_free', where }); navigate('/signup'); };
  return (
    <div className={'oh dir-s theme-' + theme + ' oh-site tln'} style={{ '--accent': ACCENT }}>
      <OhTopBar brand={BRAND} nav={MKT_NAV.map(([l, h]) => [l, h.replace('/#', '/')])}
        cta={{ label: 'Start free', href: '/signup' }} signInHref="/signin" theme={theme} onToggle={onToggle} />
      <OhHero
        eyebrow={<>Capabilities, not code <button className="tln-abpill" onClick={cycleHero} title="Cycle hero A/B variant" aria-label="Cycle hero variant">A/B · {hv}</button></>}
        title={<>Define the <span className="tint">outcome</span>.<br />{heroLine}</>}
        lede="Set the outcome and the guardrails. Teleon turns an unbounded agent task into a deterministic capability — it self-improves and adapts when it should, proves itself on real examples before anything ships, and runs at a fraction of the token cost of a full agent."
        ctas={[{ label: 'Start free →', onClick: () => startFree('hero'), primary: true }, { label: 'See how it works', href: '/' }]}
        aside={<TeleonHeroCard />} />
      {order.map((name) => { const S = TLN_SECTIONS[name]; return S ? <S key={name} /> : null; })}
      <OhBand title="Define capabilities. Not infrastructure."
        sub="Outcomes and guardrails in. A deterministic, self-improving capability out — at a fraction of an agent’s token cost."
        ctas={[{ label: 'Start free →', href: '/signup', primary: true }, { label: 'Read the docs', href: '/docs' }]} />
      <OhFooter brand={BRAND} tagline={`${T.kind} · part of AI Done Right`} cols={[
        ['Product', [['How it works', '/'], ['Lifecycle', '/'], ['Pricing', '/pricing'], ['Case studies', '/cases']]],
        ['Developers', [['Docs', '/docs'], ['Library', '/registry']]],
        ['Company', [['About', '/about'], ['Contact', '/contact'], ['Status', '/status'], ['Changelog', '/changelog']]],
        ['Group', [['AI Done Right ↗', '../context-is-everything/Context is Everything.html'], ['Baltor.ai ↗', '../context-enrichment/Context Enrichment Prototype.html'], ['OpenHarnessHub ↗', '../openharnesshub/OpenHarnessHub Prototype.html']]],
      ]} />
      <OhExperimentsPanel />
    </div>
  );
}

/* ===================== WHERE TELEON FITS (honest landscape vs the OSS runtime stack) ===================== */
// Teleon isn't another agent framework — it's the layer ABOVE them that turns a task into a
// stable capability that improves itself within proven, policy-gated, human-approved bounds.
// Composes WITH orchestration / durable-execution / optimization / eval / sandbox tools.
const TLN_FITS = [
  { cat: 'category · orchestration', name: 'Agent frameworks & orchestration',
    tools: ['LangGraph', 'CrewAI', 'OpenAI Agents SDK', 'Pydantic AI', 'AutoGen'],
    does: 'Wire models, tools and state into agent graphs — you build and ship the implementation, and own it as it drifts.',
    fit: 'Teleon keeps the capability contract stable while the implementation evolves — it can run a framework graph as one candidate, not lock you into one.' },
  { cat: 'category · durable execution', name: 'Durable execution & runtimes',
    tools: ['Temporal', 'DBOS', 'Inngest', 'Restate', 'AWS AgentCore'],
    does: 'Run long-running, crash-recoverable workflows with retries and persistence — the execution substrate.',
    fit: 'Teleon’s runtime selection composes with these as execution backends; it adds eval-gated promotion of the work that runs on them.' },
  { cat: 'category · self-improvement', name: 'Prompt / program optimization',
    tools: ['DSPy', 'GEPA', 'TextGrad'],
    does: 'Programmatically optimize prompts and chains against a metric — improve the how, automatically.',
    fit: 'Closest neighbor — but Teleon promotes a whole candidate through a policy gate with rollback + boundary approval, not just a tuned prompt.' },
  { cat: 'category · eval & CI-gating', name: 'Evaluation & CI gating',
    tools: ['LangSmith', 'Arize AX', 'promptfoo', 'RAGAS'],
    does: 'Score quality and gate changes in CI; some propose fixes or open PRs a human merges.',
    fit: 'Evidence decides for Teleon: it’s the runtime that auto-promotes within bounds (and auto-rolls-back), and exports its evidence to tools like these.' },
  { cat: 'category · sandboxes', name: 'Sandboxes & execution envs',
    tools: ['E2B', 'Daytona', 'LangSmith Sandboxes'],
    does: 'Isolated environments for code execution, file access and tool use — reduce the blast radius.',
    fit: 'Teleon runs candidate implementations inside sandboxes like these before anything is promoted.' },
  { cat: 'category · memory', name: 'Agent memory',
    tools: ['Letta', 'Mem0', 'Zep / Graphiti'],
    does: 'Persist what an agent knows across turns — durable, sometimes temporal, memory.',
    fit: 'Adjacent: Teleon governs the capability, not the memory; it composes with a memory layer rather than replacing it.' },
];
function WhereFits({ theme, onToggle }) {
  const cls = 'oh dir-s theme-' + theme + ' oh-site tln';
  const go = (href, ev) => { try { window.OHExp && window.OHExp.track(ev || 'fits_cta', { from: 'teleon_fits' }); } catch (e) {} navigate(href); };
  return (
    <div className={cls} style={{ '--accent': ACCENT }}>
      <OhTopBar brand={BRAND} nav={MKT_NAV.map(([l, h]) => [l, h.replace('/#', '/')])}
        cta={{ label: 'Start free', href: '/signup' }} signInHref="/signin" theme={theme} onToggle={onToggle} />
      <div className="ohs-page tln-fits">
        <OhPageHead eyebrow="Ecosystem · honest landscape"
          title="Not another agent framework. The layer above them."
          sub="Most teams already run an orchestration framework, maybe a durable-execution engine, an eval harness, a sandbox. They’re good at what they do — but you still build the implementation and own it as it drifts. Teleon turns a task into a stable capability that proves and improves itself within bounds. Here’s where it fits beside the tools you know." />

        <div className="tln-fits-cats">
          {TLN_FITS.map((c) => (
            <div className="oh-card tln-fits-cat" key={c.name}>
              <div className="ci mono">{c.cat}</div>
              <div className="cn">{c.name}</div>
              <div className="tools">{c.tools.map((t) => <span key={t}>{t}</span>)}</div>
              <div className="does">{c.does}</div>
              <div className="fit"><span className="k">Teleon</span><span>{c.fit}</span></div>
            </div>
          ))}
        </div>

        <div className="oh-card tln-fits-gap">
          <h3>The gap none of them fill</h3>
          <p>Frameworks orchestrate (you ship the code). Optimizers tune a prompt. Eval gates a change a human merges. Durable runtimes keep it alive. None of them keep a <strong>stable capability contract</strong> while the implementation evolves, <strong>promote on evidence with automatic rollback</strong>, and expand only within <strong>human-approved boundaries</strong>. That triad is Teleon.</p>
          <div className="triad">
            <div className="tr"><div className="t">Stable contract, evolving impl</div><div className="d">Same CapabilityTask in/out; the how can change underneath without breaking callers.</div><div className="x mono">no OSS tool does this</div></div>
            <div className="tr"><div className="t">Evidence-gated promote + rollback</div><div className="d">A candidate ships only if it clears the gate on real examples; regressions auto-revert.</div><div className="x mono">no OSS tool does this</div></div>
            <div className="tr"><div className="t">Bounded self-adaptation</div><div className="d">It adapts when it should — but boundary expansion needs a human’s approval.</div><div className="x mono">no OSS tool does this</div></div>
          </div>
        </div>

        <div className="tln-fits-h">Designed to run on your stack, not replace it</div>
        <div className="tln-fits-io">
          <div className="oh-card"><div className="t">Run on your runtime</div><div className="d">Teleon can use Temporal / LangGraph as an execution backend — it governs <em>what</em> runs and whether it’s proven, above the durable layer.</div></div>
          <div className="oh-card"><div className="t">Feed your eval & observability</div><div className="d">Promotion evidence and run traces export to LangSmith / Arize-style tools — Teleon adds the “did it earn promotion?” decision over the “what happened?” view.</div></div>
          <div className="oh-card"><div className="t">Draw from the open hubs</div><div className="d">Candidate skills, templates and eval packs come from <a onClick={() => navigate('/registry')} style={{ color: 'var(--accent)', cursor: 'pointer' }}>OpenHarnessHub / OpenSkillsHub</a> — ecosystem, not lock-in.</div></div>
        </div>

        <div className="tln-fits-foot">
          <p><strong>An honest landscape.</strong> The projects named here are real, capable tools; Teleon composes with them and fills the stable-contract · evidence-gated-promotion · bounded-adaptation gap they leave — it is not an agent framework, a durable-execution engine, or an eval harness. Interoperability shown here is the design intent of these prototypes, not a shipped-integration list.</p>
          <div className="tln-fits-cta">
            <button className="oh-btn oh-btn--primary" onClick={() => go('/signup', 'start_free')}>Start free →</button>
            <button className="oh-btn oh-btn--ghost" onClick={() => go('/cases', 'see_cases')}>See it on real capabilities</button>
          </div>
        </div>
      </div>
      <OhFooter brand={BRAND} tagline={`${T.kind} · part of AI Done Right`} cols={[
        ['Product', [['How it works', '/'], ['Where it fits', '/fits'], ['Pricing', '/pricing'], ['Case studies', '/cases']]],
        ['Developers', [['Docs', '/docs'], ['Library', '/registry']]],
        ['Company', [['About', '/about'], ['Contact', '/contact'], ['Status', '/status']]],
      ]} />
      <OhExperimentsPanel />
    </div>
  );
}

/* ===================== APP (runtime-specific pages) ===================== */
const CAPS = [
  ['cap-usury', 'State usury-rate finder', 'promoted', '0.96', 'v12'],
  ['cap-cite', 'Citation checker', 'promoted', '0.97', 'v8'],
  ['cap-sql', 'Schema-aware SQL', 'candidate', '0.88', 'v3·rc'],
  ['cap-redteam', 'Red-team prompts', 'rolled-back', '0.61', 'v5'],
];
const STATUS_BADGE = { promoted: 'oh-badge--verified', candidate: 'oh-badge--warn', 'rolled-back': 'oh-badge--muted' };

function Capabilities() {
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Workspace" title="Capabilities"
        sub="Each capability ships only after it clears your success criteria — or rolls back."
        actions={<button className="oh-btn oh-btn--primary" onClick={() => navigate('/runs')}>+ New capability</button>} />
      <OhRollup items={[['Capabilities', CAPS.length], ['Promoted', CAPS.filter((c) => c[2] === 'promoted').length], ['In eval', 1], ['Avg score', '0.90']]} />
      <div className="oh-card oh-card--pad">
        <table className="oh-table">
          <thead><tr><th>Capability</th><th>Status</th><th>Eval score</th><th>Version</th><th></th></tr></thead>
          <tbody>
            {CAPS.map(([id, name, st, score, ver]) => (
              <tr key={id}>
                <td>{name}</td>
                <td><span className={'oh-badge ' + STATUS_BADGE[st] + ' oh-badge--sm'}>{st}</span></td>
                <td className="mono">{score}</td>
                <td className="mono">{ver}</td>
                <td style={{ textAlign: 'right' }}><a className="ohs-navlink" onClick={() => navigate('/evidence')}>Evidence →</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Runs() {
  const [phase, setPhase] = React.useState('idle');
  const [step, setStep] = React.useState(0);
  React.useEffect(() => {
    if (phase !== 'running') return;
    if (step >= LIFECYCLE.length) { const t = setTimeout(() => setPhase('done'), 400); return () => clearTimeout(t); }
    const t = setTimeout(() => setStep((s) => s + 1), 520); return () => clearTimeout(t);
  }, [phase, step]);
  return (
    <div className="ohs-page narrow">
      <OhPageHead eyebrow="Build" title="New capability" sub="Describe what you want and how success is measured. Teleon builds and proves it." />
      <div className="oh-card oh-card--pad" style={{ marginBottom: 16 }}>
        <label className="oh-field"><span>What should it do?</span><input defaultValue="Find each US state's maximum legal interest rate, with the statute cited for every state" /></label>
        <label className="oh-field"><span>How will you know it’s right? (success criteria)</span>
          <div className="oh-segment">
            {['cites the live statute', 'covers all 50 states', 're-checks on change'].map((g, i) => <button key={g} className={i === 0 ? 'on' : ''}>{g}</button>)}
          </div>
        </label>
        <button className="oh-btn oh-btn--primary" onClick={() => { setPhase('running'); setStep(0); }} disabled={phase === 'running'}>
          {phase === 'idle' ? 'Build capability →' : phase === 'running' ? 'Building…' : 'Rebuild'}
        </button>
      </div>
      {phase !== 'idle' && (
        <div className="oh-card oh-card--pad">
          <div className="tln-prog">
            {LIFECYCLE.map(([s], i) => (
              <div key={s} className={'row' + (i < step || phase === 'done' ? ' done' : i === step ? ' active' : '')}>
                <span className="mk">{(i < step || phase === 'done') ? '✓' : i === step ? '◌' : '·'}</span>{s}
              </div>
            ))}
          </div>
          {phase === 'done' && <div className="tln-result"><span className="oh-badge oh-badge--verified">✔ shipped · passed your criteria</span><span className="mono">version 13 live</span></div>}
        </div>
      )}
    </div>
  );
}

function SimplePage({ title, eyebrow, sub, note }) {
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow={eyebrow} title={title} sub={sub} />
      <div className="oh-card oh-card--pad" style={{ color: 'var(--fg-muted)', fontSize: 14, lineHeight: 1.6 }}>{note}</div>
    </div>
  );
}

/* ===================== ROOT ===================== */
function App() {
  const route = useHashRoute();
  const [theme, toggle] = useSiteTheme('teleon-theme');
  const rootCls = 'oh dir-s theme-' + theme + ' oh-site tln';
  const rootStyle = { '--accent': ACCENT };

  // marketing + auth surfaces (no app chrome)
  if (route === '/' || route === '') return <Landing theme={theme} onToggle={toggle} />;
  if (route === '/fits') return <WhereFits theme={theme} onToggle={toggle} />;
  // 'How it works' + 'Lifecycle' are sections OF the landing — render it (was a 404 → app-shell sidebar leak).
  if (route === '/how' || route === '/lifecycle') return <Landing theme={theme} onToggle={toggle} />;
  if (route === '/signin' || route === '/signup' || route === '/forgot') {
    return <div className={rootCls} style={rootStyle}><OhAuth brand={BRAND} mode={route.slice(1)} /></div>;
  }
  if (route === '/contact') {
    return <div className={rootCls} style={rootStyle}><OhContact brand={BRAND} email="hello@teleon.dev" /></div>;
  }
  if (route === '/docs') {
    return <div className={rootCls} style={rootStyle}><OhDocs theme={theme} onToggle={toggle} cfg={{ brand: BRAND, noun: 'capability', nounPlural: 'capabilities',
      intro: 'Declare a purpose; Teleon builds the capability, proves it on real examples, and ships only what passes.',
      firstAction: 'build your first capability',
      quickstart: [['Install', 'Add the Teleon CLI to your project.'], ['Authenticate', 'Create an API key in the console and export it.'], ['Build', 'Describe an outcome + success criteria; Teleon runs the lifecycle.']],
      installCode: 'teleon login\nteleon build "summarize logs into a cited report"' }} /></div>;
  }

  if (route === '/status') return <div className={rootCls} style={rootStyle}><OhStatus brand={BRAND} /></div>;
  if (route === '/changelog') return <div className={rootCls} style={rootStyle}><OhChangelog /></div>;
  if (route === '/terms') return <div className={rootCls} style={rootStyle}><OhLegal brand={BRAND} kind="terms" /></div>;
  if (route === '/privacy') return <div className={rootCls} style={rootStyle}><OhLegal brand={BRAND} kind="privacy" /></div>;
  if (route === '/about') return <div className={rootCls} style={rootStyle}><OhAbout brand={BRAND} /></div>;
  const TELEON_CASES = (typeof window !== 'undefined' && window.CASES && window.CASES.teleon) || [];
  if (route === '/cases') return <div className={rootCls} style={rootStyle}><OhCaseStudies brand={BRAND} cases={TELEON_CASES} /></div>;
  if (route.startsWith('/cases/')) return <div className={rootCls} style={rootStyle}><OhCaseStudy brand={BRAND} cases={TELEON_CASES} id={route.slice(7)} cta={{ label: 'Start free →', href: '/signup' }} /></div>;

  let page;
  if (route === '/dashboard') page = <OhDashboard
    stats={[['Capabilities', 4], ['Promotions · 30d', '38'], ['Rollbacks', '6'], ['Avg score', '0.90']]}
    activity={[
      { icon: '✓', text: 'State usury-rate finder promoted · 0.96', when: '1h ago' },
      { icon: '⊕', text: 'New capability build started', when: '4h ago' },
      { icon: '↻', text: 'Red-team prompts rolled back', when: '1d ago' },
      { icon: '◷', text: 'Invoice paid · $249.00', when: '5d ago' },
    ]}
    plan={{ name: 'Team', usagePct: 62, usageLabel: 'Eval compute used' }}
    quick={[
      { title: 'Build a capability', desc: 'Describe an outcome', href: '/runs', cta: 'Build' },
      { title: 'Review evidence', desc: 'See what shipped & why', href: '/evidence', cta: 'Open' },
      { title: 'Create an API key', desc: 'Authenticate your agents', href: '/keys', cta: 'Create' },
    ]} />;
  else if (route === '/app') page = <Capabilities />;
  else if (route === '/runs') page = <Runs />;
  else if (route === '/evidence') page = <SimplePage eyebrow="Proof" title="Evidence" sub="The proof behind every capability — what was tried, how it scored, and why it shipped." note="Each capability links here to its evidence trail: the versions Teleon tried, how each did on your success criteria, and the decision that shipped or reverted it." />;
  else if (route === '/keys') page = <OhApiKeys />;
  else if (route === '/team') page = <OhTeam />;
  else if (route === '/audit') page = <OhAuditLog />;
  else if (route === '/notifications') page = <OhNotifications />;
  else if (route === '/onboarding') page = <OhOnboarding brand={BRAND} />;
  else if (route === '/registry') page = <SimplePage eyebrow="Library" title="Library" sub="Ready-made skills, templates and tests from the open hubs." note="Teleon draws from OpenHarnessHub / OpenSkillsHub / OpenToolsHub. The building blocks you’ve added show up here and feed every new capability." />;
  else if (route === '/billing') page = <OhBilling plan={{ name: 'Team', desc: 'Up to 25 capabilities · shared eval compute', price: '$249', per: '/mo', usagePct: 62, usageLabel: 'Eval compute used' }}
      invoices={[['May 1, 2026', '$249.00', 'Paid'], ['Apr 1, 2026', '$249.00', 'Paid'], ['Mar 1, 2026', '$249.00', 'Paid']]} />;
  else if (route === '/usage') page = <OhUsage rollup={[['Runs · 30d', '4,120'], ['Promotions', '38'], ['Rollbacks', '6'], ['Eval hrs', '212']]}
      metrics={[
        { k: 'Lifecycle runs', v: '4,120', bars: [.4, .5, .45, .6, .7, .65, .9], hiLast: true },
        { k: 'Eval compute (hrs)', v: '212', bars: [.5, .55, .5, .6, .58, .7, .8], hiLast: true },
      ]} />;
  else if (route === '/settings') page = <OhSettings sections={[
      { title: 'Profile', rows: [{ t: 'Display name', d: 'Shown across your workspace', ctrl: <input className="oh-input" defaultValue="Ada Lovelace" /> }, { t: 'Work email', d: 'Used for sign-in and receipts', ctrl: <input className="oh-input" defaultValue="ada@company.com" /> }] },
      { title: 'Preferences', rows: [{ t: 'Auto-rollback', d: 'Roll back any capability that fails its gate', ctrl: <OhSwitch on onToggle={() => {}} /> }, { t: 'Weekly evidence digest', d: 'Email a summary of promotions and rollbacks', ctrl: <OhSwitch on onToggle={() => {}} /> }] },
    ]} />;
  else if (route === '/pricing') page = <OhPricing tiers={[
        { name: 'Starter', price: '$0', per: '/mo', desc: 'For trying Teleon on a project.', features: ['3 capabilities', 'Shared eval compute', 'Community support'], cta: 'Start free' },
        { name: 'Team', price: '$249', per: '/mo', desc: 'For teams shipping capabilities.', features: ['Up to 25 capabilities', 'Private eval compute', 'Auto-rollback', 'Priority support'], cta: 'Start Team', featured: true },
        { name: 'Enterprise', price: 'Custom', per: '', desc: 'For regulated & at-scale orgs.', features: ['Unlimited capabilities', 'SSO & SCIM', 'Audit & compliance', 'Dedicated support'], cta: 'Contact sales' },
      ]} />;
  // unknown route → a MARKETING-framed 404 (home + marketing links), NOT the app shell with its sidebar.
  else return <div className={rootCls} style={rootStyle}><OhNotFound brand={BRAND} home="/" links={[['Home', '/'], ['Docs', '/docs'], ['Pricing', '/pricing']]} /></div>;

  return (
    <div className={rootCls} style={rootStyle}>
      <OhAppShell brand={BRAND} nav={APP_NAV} route={route} cta={{ label: '+ New run', href: '/runs' }} theme={theme} onToggle={toggle}
        header={<button className="ohs-side-search" onClick={() => window.dispatchEvent(new CustomEvent('oh-cmdk'))}><span className="ohs-side-search-l"><span aria-hidden="true">⌕</span> Search…</span><span className="oh-kbd">⌘K</span></button>}>
        {page}
      </OhAppShell>
      <OhCommandK commands={TELEON_CMDS} placeholder="Search Teleon…" />
    </div>
  );
}
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
