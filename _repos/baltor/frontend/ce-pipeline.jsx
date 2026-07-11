/* global React, PageHead, navigate, useHashRoute */
// Baltor — in-product Sources + live engine Pipeline run (overview + per-stage detail).

const PIPE_STAGES = [
  { key: 'ingestion', n: '00', name: 'Ingestion', sub: 'raw ingress', tone: 'var(--fg-faint)',
    metric: 'objects captured', val: '1,284',
    copy: 'Watching the source for changes — parsing objects and preserving timestamps, permissions, hashes and source handles.',
    detail: 'Each connected source is polled on its cadence (or pushed via webhook). New and changed objects enter with ACLs and content hashes before anything is trusted.' },
  { key: 'reconciliation', n: '01', name: 'Reconciliation', sub: 'cluster alignment', tone: 'var(--success)',
    metric: 'conflicts found', val: '44',
    copy: 'Deduping artifacts, linking evidence, separating comments from decisions, and surfacing contradictions.',
    detail: 'When two sources disagree, Baltor links the evidence and either resolves by source precedence/confidence (when policy allows) or routes the conflict to the review queue.' },
  { key: 'anti', n: '02', name: 'Hardening', sub: 'robust objects', tone: 'var(--info)',
    metric: 'facts hardened', val: '44',
    copy: 'Finding facts likely to change and replacing brittle text with refreshable knowledge objects.',
    detail: 'Magic numbers, thresholds and policy values become live objects rechecked against the right system — so the served value is never a stale copy.' },
  { key: 'enhancement', n: '03', name: 'Enhancement', sub: 'context enrichment', tone: 'var(--accent)',
    metric: 'objects linked', val: '26',
    copy: 'Adding external context, metadata, relationships and missing connective facts.',
    detail: 'Approved external sources and service-graph links are attached to fill gaps and resolve internal disagreements before serving.' },
  { key: 'optimization', n: '04', name: 'Optimization', sub: 'pack shaping', tone: 'var(--violet, #8b7cf6)',
    metric: 'tokens saved', val: '13×',
    copy: 'Summarizing, structuring and ranking — fitting the result to the task budget.',
    detail: 'A sprawling thread of tickets, docs and handles becomes a compact, ranked pack with conflicts and expansion links — fewer tokens, fewer tool calls.' },
  { key: 'consumption', n: '05', name: 'Consumption', sub: 'delivery', tone: 'var(--fg-faint)',
    metric: 'packs served / day', val: '21.6k',
    copy: 'Serving governed packs to agents and humans with controlled expansion and an audit receipt.',
    detail: 'Claude, Cursor or a human dashboard receives the same governed pack and can expand approved handles — every claim, route and decision recorded.' },
];

const SOURCES = [
  ['Confluence — Policy space', 'confluence', 'every 6h', 'synced 2h ago', 'verified'],
  ['GitHub — acme/policies', 'github', 'on push', 'live · webhook', 'verified'],
  ['Zendesk — resolved tickets', 'zendesk', 'every 12h', 'syncing… 71%', 'syncing'],
  ['S3 — contracts/', 's3', 'daily', 'synced 5h ago', 'verified'],
];
const SRC_TYPES = [['🌐', 'Crawl a site / docs'], ['⎇', 'Connect a repo'], ['⚯', 'Connect a system'], ['⤒', 'Upload files']];

function SourcesPage() {
  const [picked, setPicked] = React.useState(0);
  const [val, setVal] = React.useState('');
  return (
    <div className="ce-page">
      <PageHead eyebrow="Workspace" title="Sources"
        sub="Link the systems where your knowledge lives. Baltor watches each for changes and keeps your context current."
        actions={<button className="oh-btn oh-btn--primary" onClick={() => navigate('/pipeline')}>View engine run →</button>} />
      <div className="oh-card oh-card--pad" style={{ marginBottom: 22 }}>
        <div className="ohs-card-h">Connect a source</div>
        <div className="ce-srctypes" style={{ marginBottom: 16 }}>
          {SRC_TYPES.map(([g, l], i) => (
            <button key={l} className={'ce-srctype' + (picked === i ? ' on' : '')} onClick={() => setPicked(i)}><span className="g">{g}</span>{l}</button>
          ))}
        </div>
        <div className="ce-src-row">
          <input className="oh-input" style={{ flex: 1 }} value={val} onChange={(e) => setVal(e.target.value)} placeholder={picked === 3 ? 'Drag files or browse…' : 'https://… or org/repo'} />
          <label className="ce-chk"><input type="checkbox" defaultChecked /> Auto-refresh on change</label>
          <button className="oh-btn oh-btn--primary" onClick={() => navigate('/pipeline')}>Link &amp; run engine →</button>
        </div>
      </div>
      <div className="ohs-card-h" style={{ margin: '0 0 12px' }}>Linked sources</div>
      <div className="oh-card oh-card--pad">
        <table className="oh-table">
          <thead><tr><th>Source</th><th>Refresh</th><th>State</th><th></th></tr></thead>
          <tbody>
            {SOURCES.map(([name, , cadence, state, st], i) => (
              <tr key={i}>
                <td>{name}</td>
                <td className="mono">{cadence}</td>
                <td><span className="mono" style={{ color: st === 'syncing' ? 'var(--warning)' : 'var(--fg-muted)' }}>{state}</span></td>
                <td style={{ textAlign: 'right' }}><a className="ohs-navlink" onClick={() => navigate('/pipeline')}>Engine →</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// animated progress per stage
function usePipelineProgress() {
  const [p, setP] = React.useState(() => PIPE_STAGES.map(() => 0));
  React.useEffect(() => {
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) { setP(PIPE_STAGES.map((_, i) => i < 5 ? 100 : 64)); return; }
    let raf; const start = performance.now();
    const tick = (t) => {
      const el = (t - start) / 1000;
      setP(PIPE_STAGES.map((_, i) => {
        const begin = i * 0.6, dur = 1.6;
        const target = i < 5 ? 100 : 64;
        return Math.max(0, Math.min(target, ((el - begin) / dur) * target));
      }));
      if (el < 6) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);
  return p;
}

function PipelinePage() {
  const prog = usePipelineProgress();
  return (
    <div className="ce-page">
      <PageHead eyebrow="Engine" title="Pipeline run"
        sub="Live progress as Baltor turns your linked sources into trustworthy, task-ready context."
        actions={<button className="oh-btn oh-btn--ghost" onClick={() => navigate('/sources')}>← Sources</button>} />
      <div className="ce-pipe-grid">
        {PIPE_STAGES.map((s, i) => {
          const pct = Math.round(prog[i] || 0);
          const done = pct >= (i < 5 ? 100 : 64) && i < 5;
          return (
            <button className="oh-card ce-pipe-card" key={s.key} onClick={() => navigate('/pipeline/' + s.key)} style={{ borderLeft: '3px solid ' + s.tone }}>
              <div className="pc-top"><span className="pc-n mono">{s.n}</span><span className="pc-st" style={{ color: s.tone }}>{done ? '✓ done' : i === 5 ? 'serving' : pct + '%'}</span></div>
              <div className="pc-name">{s.name}</div>
              <div className="pc-sub">{s.sub}</div>
              <div className="ce-pipe-meter"><i style={{ width: pct + '%', background: s.tone }} /></div>
              <div className="pc-metric"><b>{s.val}</b><span>{s.metric}</span></div>
            </button>
          );
        })}
      </div>
      <div className="oh-card oh-card--pad ce-pipe-foot">
        <span className="oh-badge oh-badge--verified">✔ continuous verification</span>
        <span className="mono">adversarial interrogation runs beneath every stage — contradictions · source precedence · freshness · policy</span>
      </div>
    </div>
  );
}

function PipelineStage({ id }) {
  const s = PIPE_STAGES.find((x) => x.key === id) || PIPE_STAGES[0];
  const idx = PIPE_STAGES.indexOf(s);
  return (
    <div className="ce-page">
      <a className="ce-back" onClick={() => navigate('/pipeline')}>← Pipeline run</a>
      <div className="ce-detail-head">
        <div>
          <div className="ce-eyebrow" style={{ color: s.tone }}>Stage {s.n} · {s.sub}</div>
          <h1>{s.name}</h1>
          <p>{s.detail}</p>
        </div>
        <div className="ce-detail-actions">
          {idx > 0 && <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/pipeline/' + PIPE_STAGES[idx - 1].key)}>← Prev</button>}
          {idx < PIPE_STAGES.length - 1 && <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/pipeline/' + PIPE_STAGES[idx + 1].key)}>Next →</button>}
        </div>
      </div>
      <div className="ohs-rollup" style={{ marginBottom: 22 }}>
        {[[s.metric, s.val], ['Stage', s.n + ' / 05'], ['Verification', 'passing'], ['Last run', '40s ago']].map(([k, v]) => (
          <div className="oh-card ohs-roll" key={k}><div className="v" style={{ fontSize: 22 }}>{v}</div><div className="k">{k}</div></div>
        ))}
      </div>
      <div className="oh-card oh-card--pad">
        <div className="ohs-card-h">What this stage does</div>
        <p style={{ fontSize: 14.5, lineHeight: 1.6, color: 'var(--fg-muted)', margin: 0 }}>{s.copy}</p>
      </div>
    </div>
  );
}

Object.assign(window, { SourcesPage, PipelinePage, PipelineStage });
