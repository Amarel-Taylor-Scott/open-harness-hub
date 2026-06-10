/* global React, DesignCanvas, DCSection, DCArtboard, Landing, BuilderResults, ComponentCard, FlowCanvas, Comparison, PaletteCard, ResultsTable, ResultsHero, ResultsDial, DagVertical, DagSubway, RunTrace, ComponentLibrary, BatchFlow, LiftEvidence, SystemStates */

// ── Scheme registry: id · letter · accent · name · audience · natural theme · blurb · short ──
const SCHEMES = [
  ['s', 'S', '#d6553a', '★ Harness House', 'Everyone · house style', 'dark', "Grafts the best of all: A's warmth, B's restraint, D's verified teal.", 'House'],
  ['a', 'A', '#b8501f', 'Warm Editorial', 'Regulated buyers · CTOs', 'light', 'Considered, governed, human-in-the-loop. Serif credibility on paper.', 'Editorial'],
  ['b', 'B', '#2563eb', 'Clinical Monochrome', 'AI-infra · dev tools', 'dark', 'Austere near-monochrome; one blue on the primary action.', 'Mono'],
  ['c', 'C', '#7c6bf0', 'Refined Product Dark', 'Dev teams · power users', 'dark', 'Linear / Raycast craft — violet on near-black, keyboard-first.', 'Violet'],
  ['d', 'D', '#0e7c86', 'Answer-Engine Teal', 'Search-grade · analysts', 'light', 'Answers + proof. Teal doubles as the verified signal.', 'Teal'],
  ['e', 'E', '#22c7d6', 'Blueprint Terminal', 'Engineers · integrators', 'dark', 'Schematic ink-navy + cyan; mono-forward, precise.', 'Blueprint'],
  ['f', 'F', '#1e6b43', 'Ledger Governance', 'Compliance · enterprise', 'light', 'Audit-ledger trust — parchment + forest green.', 'Ledger'],
  ['g', 'G', '#39d353', 'Hacker Terminal', 'Hackers · indie · OSS', 'dark', 'Phosphor green on black, mono everything.', 'Hacker'],
  ['h', 'H', '#1f5fbf', 'Enterprise Slate', 'CTOs · enterprise IT', 'light', 'Procurement-ready navy; polished, governed.', 'Slate'],
];
const SCHEME_MAP = Object.fromEntries(SCHEMES.map((s) => [s[0], s]));

// Stable, module-scope page frame — keeps element type constant so a scheme
// switch re-themes via CSS vars instead of remounting every artboard.
function GFrame({ scheme, mode, children }) {
  return <div className={`oh dir-${scheme} theme-${mode}`} style={{ width: '100%', height: '100%' }}>{children}</div>;
}

// Collapsible bottom-left switcher — re-themes the whole "All pages" set at once.
function SchemeBar({ scheme, mode, onScheme, onMode }) {
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef(null);
  const cur = SCHEME_MAP[scheme];
  React.useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', onDown, true);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDown, true); document.removeEventListener('keydown', onKey); };
  }, [open]);
  return (
    <div className={'oh-sw' + (open ? ' open' : '')} ref={ref}>
      {open && (
        <div className="oh-sw-panel" role="menu" aria-label="Color scheme">
          <div className="oh-sw-head">Color scheme — applies to all pages</div>
          <div className="oh-sw-grid">
            {SCHEMES.map(([id, letter, accent, name, aud, theme, blurb, short]) => (
              <button key={id} className={'oh-sw-opt' + (id === scheme ? ' on' : '')} role="menuitemradio"
                aria-checked={id === scheme} title={name} onClick={() => onScheme(id)}>
                <span className="oh-sb-dot" style={{ background: accent }} />
                <span className="nm">{short}</span>
              </button>
            ))}
          </div>
          <div className="oh-sw-row">
            <span className="oh-sw-name"><b>{cur[3]}</b></span>
            <div className="oh-sb-toggle" role="radiogroup" aria-label="Light or dark">
              <button className={mode === 'light' ? 'on' : ''} aria-pressed={mode === 'light'} onClick={() => onMode('light')}>Light</button>
              <button className={mode === 'dark' ? 'on' : ''} aria-pressed={mode === 'dark'} onClick={() => onMode('dark')}>Dark</button>
            </div>
          </div>
        </div>
      )}
      <button className="oh-sw-trigger" aria-expanded={open} aria-haspopup="menu"
        onClick={() => setOpen((o) => !o)} title="Color scheme & theme">
        <span className="oh-sb-dot" style={{ background: cur[2] }} />
        <span className="lbl">Theme</span>
        <span>{cur[7]} · {mode === 'light' ? 'Light' : 'Dark'}</span>
        <svg className="cv" width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"><path d="M2 7l3.5-3.5L9 7" /></svg>
      </button>
    </div>
  );
}

function App() {
  const prefersDark = typeof window !== 'undefined' && window.matchMedia
    && window.matchMedia('(prefers-color-scheme: dark)').matches;
  // Default to light unless the browser prefers dark; persist the user's choice.
  const [scheme, setScheme] = React.useState(() => localStorage.getItem('oh-scheme') || 's');
  const [mode, setMode] = React.useState(() => localStorage.getItem('oh-mode') || (prefersDark ? 'dark' : 'light'));
  React.useEffect(() => { try { localStorage.setItem('oh-scheme', scheme); } catch (e) {} }, [scheme]);
  React.useEffect(() => { try { localStorage.setItem('oh-mode', mode); } catch (e) {} }, [mode]);
  const pick = (id) => { const s = SCHEME_MAP[id]; setScheme(id); setMode(s[5]); };
  const G = ({ children }) => <GFrame scheme={scheme} mode={mode}>{children}</GFrame>;

  return (
    <>
      <SchemeBar scheme={scheme} mode={mode} onScheme={setScheme} onMode={setMode} />
      <DesignCanvas>
        <DCSection id="marketing" title="Marketing — the entry box"
          subtitle="All pages below re-theme live from the switcher (bottom-left) · pick any of 9 schemes + light/dark">
          <DCArtboard id="p-landing" label="Landing — paste a task" width={1180} height={720}><G><Landing /></G></DCArtboard>
        </DCSection>

        <DCSection id="builder" title="Builder — paste → costed options"
          subtitle="Lift is the hero; cost is the honesty check. The headline interaction plus three layout studies.">
          <DCArtboard id="p-results" label="Builder results · cards" width={1180} height={648}><G><BuilderResults /></G></DCArtboard>
          <DCArtboard id="p-lift" label="Capability-lift evidence · the moat" width={1180} height={486}><G><LiftEvidence /></G></DCArtboard>
          <DCArtboard id="p-table" label="Builder results · matrix" width={1180} height={556}><G><ResultsTable /></G></DCArtboard>
          <DCArtboard id="p-hero" label="Builder results · recommendation" width={1180} height={556}><G><ResultsHero /></G></DCArtboard>
          <DCArtboard id="p-dial" label="Builder results · budget dial" width={1180} height={556}><G><ResultsDial /></G></DCArtboard>
        </DCSection>

        <DCSection id="catalog" title="Catalog & components"
          subtitle="The most-repeated unit, the badge system, and the alignment library">
          <DCArtboard id="p-card" label="Component card + badges" width={760} height={624}><G><ComponentCard /></G></DCArtboard>
          <DCArtboard id="p-library" label="Component library · aligned by stage" width={1340} height={476}><G><ComponentLibrary /></G></DCArtboard>
        </DCSection>

        <DCSection id="flows" title="Flows — single-call core + batch"
          subtitle="It's a flow, not a DAG — Conditional (IF) routes first, Knowledge feeds one harness call, the refine loop re-runs it; batch is a separate wrapper">
          <DCArtboard id="p-flow" label="Flow · wired + refine loop" width={1500} height={500}><G><FlowCanvas /></G></DCArtboard>
          <DCArtboard id="p-vertical" label="Flow · vertical (trace-ready)" width={640} height={620}><G><DagVertical /></G></DCArtboard>
          <DCArtboard id="p-subway" label="Flow · linear subway" width={1100} height={452}><G><DagSubway /></G></DCArtboard>
          <DCArtboard id="p-batch" label="Batch · map over list" width={900} height={470}><G><BatchFlow /></G></DCArtboard>
          <DCArtboard id="p-trace" label="Run / trace audit log" width={1100} height={452}><G><RunTrace /></G></DCArtboard>
        </DCSection>

        <DCSection id="states" title="System states"
          subtitle="Empty · loading · blocked-by-gate · error · success — designed, honest, first-class">
          <DCArtboard id="p-states" label="System states" width={1180} height={470}><G><SystemStates /></G></DCArtboard>
        </DCSection>

        <DCSection id="schemes" title="Color schemes — at a glance"
          subtitle="Each shown in its own identity · click “Apply to all pages” to drive the switcher and re-theme everything above">
          {SCHEMES.map(([id, letter, accent, name, aud, theme, blurb]) => (
            <DCArtboard key={id} id={'pal-' + id} label={letter + ' · ' + name} width={356} height={602}>
              <div className={`oh dir-${id} theme-${theme}`} style={{ width: '100%', height: '100%' }}>
                <PaletteCard name={(id === 's' ? '★ ' : '') + name} audience={aud} blurb={blurb} onPick={() => pick(id)} />
              </div>
            </DCArtboard>
          ))}
        </DCSection>

        <DCSection id="verdict" title="Verdict" subtitle="Scored rubric · audience map · the 5/5 house style">
          <DCArtboard id="comparison" label="Comparison & recommendation" width={1460} height={772}>
            <div className="oh dir-s theme-light" style={{ width: '100%', height: '100%' }}><Comparison /></div>
          </DCArtboard>
        </DCSection>
      </DesignCanvas>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
