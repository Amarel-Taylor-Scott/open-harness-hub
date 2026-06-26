/* global React, navigate, AppShell, PageHead, StatusBadge, TierDot, Meter, CORPORA, CORPUS_BY_ID, ROLLUP, TIER_META, tierFill, BRANDCE, SEV_META, CONFLICT_TYPE, CONFLICTS, VERIFY_ROLLUP, WATCHED, PUBLISHERS, COMMONS_DOMAINS, COMMONS, REG_CHANGES, ARTIFACTS */
// Context Enrichment — app pages: Corpora · Ingest · CorpusDetail · Serve · Governance.

const fmt = (n) => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1).replace('.0', '') + 'k' : '' + n;
const srcTotal = (c) => c.sources.reduce((m, s) => m + s[1], 0);

// ---------------- CORPORA DASHBOARD ----------------
function CorporaPage() {
  const stats = [
    ['Corpora', ROLLUP.corpora], ['Sources ingested', fmt(ROLLUP.sources)],
    ['Served / day', fmt(ROLLUP.served)], ['Citations', '100%'],
  ];
  return (
    <div className="ce-page">
      <PageHead eyebrow="Workspace" title="Corpora"
        sub="Verified, tiered context sets — citation-anchored and ready to host, download, or serve to your agents."
        actions={<button className="oh-btn oh-btn--primary" onClick={() => navigate('/ingest')}>+ New corpus</button>} />
      <div className="ce-rollup">
        {stats.map(([k, v]) => <div className="ce-roll" key={k}><div className="v">{v}</div><div className="k">{k}</div></div>)}
      </div>
      <div className="ce-corpgrid">
        {CORPORA.map((c) => (
          <div className="oh-card ce-corpcard" key={c.id} onClick={() => navigate('/c/' + c.id)}>
            <div className="cc-top">
              <h3>{c.name}</h3>
              <StatusBadge status={c.status} />
            </div>
            <p className="cc-desc">{c.desc}</p>
            <div className="cc-tiers">
              {['raw', 'compressed', 'hyper'].map((t) => (
                <div className="cc-tier" key={t}>
                  <div className="cc-tier-h"><TierDot tier={t} /><span>{TIER_META[t].label}</span><span className="sz">{c.tiers[t].size}</span></div>
                  <Meter pct={tierFill[t]} tone={TIER_META[t].tone} />
                </div>
              ))}
            </div>
            <div className="cc-foot">
              <span className="mono">{fmt(srcTotal(c))} sources{c.langs > 1 ? ' · ' + c.langs + ' langs' : ''}</span>
              <span className="mono">{c.freshness}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------- INGEST FLOW ----------------
const SRC_TYPES = [['url', '🌐', 'Crawl a site / docs'], ['upload', '⤒', 'Upload files'], ['connect', '⚯', 'Connect a source'], ['repo', '⎇', 'Index a repo']];
const REFINE_STEPS = ['Fetching & parsing sources', 'Chunking + fingerprinting', 'Building raw tier', 'Compressing → normalized tier', 'Distilling → hyper-efficient tier', 'Anchoring citations'];
function IngestPage() {
  const [srcType, setSrcType] = React.useState('url');
  const [val, setVal] = React.useState('');
  const [phase, setPhase] = React.useState('setup'); // setup | refining | done
  const [step, setStep] = React.useState(0);
  React.useEffect(() => {
    if (phase !== 'refining') return;
    if (step >= REFINE_STEPS.length) { const t = setTimeout(() => setPhase('done'), 500); return () => clearTimeout(t); }
    const t = setTimeout(() => setStep((s) => s + 1), 620); return () => clearTimeout(t);
  }, [phase, step]);
  const start = () => { setPhase('refining'); setStep(0); };

  return (
    <div className="ce-page ce-narrow">
      <PageHead eyebrow="Ingest" title="Add a source"
        sub={`Connect ${BRANDCE.name} to a source. We parse, chunk and verify it, then tier it — raw, compressed, and hyper-efficient.`} />

      {phase === 'setup' && (
        <div className="oh-card ce-panel">
          <div className="ce-srctypes">
            {SRC_TYPES.map(([k, g, l]) => (
              <button key={k} className={'ce-srctype' + (srcType === k ? ' on' : '')} onClick={() => setSrcType(k)}>
                <span className="g">{g}</span>{l}
              </button>
            ))}
          </div>
          <label className="oh-field">
            <span>{srcType === 'url' ? 'Site or docs URL' : srcType === 'repo' ? 'Repository' : srcType === 'connect' ? 'Connector' : 'Files'}</span>
            <input value={val} onChange={(e) => setVal(e.target.value)}
              placeholder={srcType === 'url' ? 'https://docs.acme.com' : srcType === 'repo' ? 'github.com/acme/policies' : srcType === 'connect' ? 'Confluence · Zendesk · S3 · Drive…' : 'Drag files or browse…'} />
          </label>
          <div className="ce-field-row">
            <label className="ce-chk"><input type="checkbox" defaultChecked /> Build all three tiers</label>
            <label className="ce-chk"><input type="checkbox" defaultChecked /> Citation anchoring</label>
            <label className="ce-chk"><input type="checkbox" defaultChecked /> Track provenance</label>
          </div>
          <button className="oh-btn oh-btn--primary" onClick={start}>Ingest &amp; refine →</button>
        </div>
      )}

      {phase === 'refining' && (
        <div className="oh-card ce-panel">
          <div className="ce-refine-head"><span className="spin">↻</span> Refining your corpus…</div>
          <div className="ce-progress">
            {REFINE_STEPS.map((s, i) => (
              <div key={s} className={'row' + (i < step ? ' done' : i === step ? ' active' : '')}>
                <span className="mk">{i < step ? '✓' : i === step ? '◌' : '·'}</span>{s}
              </div>
            ))}
          </div>
        </div>
      )}

      {phase === 'done' && (
        <div className="oh-card ce-panel ce-done">
          <div className="ce-done-h"><span className="oh-badge oh-badge--verified">✔ corpus ready</span></div>
          <h3>Three tiers built, citations anchored.</h3>
          <div className="ce-done-tiers">
            {['raw', 'compressed', 'hyper'].map((t) => (
              <div className="ce-done-tier" key={t}>
                <TierDot tier={t} /><span>{TIER_META[t].label}</span>
                <span className="mono">{({ raw: '1.18 GB', compressed: '402 MB', hyper: '91 MB' })[t]}</span>
              </div>
            ))}
          </div>
          <div className="ce-cta">
            <button className="oh-btn oh-btn--primary" onClick={() => navigate('/c/acme-policy')}>Open corpus →</button>
            <button className="oh-btn oh-btn--ghost" onClick={() => { setPhase('setup'); setVal(''); }}>Add another</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------- CORPUS DETAIL ----------------
function CorpusDetail({ id }) {
  const c = CORPUS_BY_ID[id];
  const [tab, setTab] = React.useState('tiers');
  if (!c) return <div className="ce-page"><PageHead title="Corpus not found" /><button className="oh-btn oh-btn--ghost" onClick={() => navigate('/corpora')}>← Back to corpora</button></div>;
  const TABS = [['tiers', 'Tiers'], ['provenance', 'Provenance'], ['serve', 'Serve'], ['compliance', 'Compliance'], ['settings', 'Settings']];
  return (
    <div className="ce-page">
      <a className="ce-back" onClick={() => navigate('/corpora')}>← Corpora</a>
      <div className="ce-detail-head">
        <div>
          <div className="ce-eyebrow">Corpus · {c.owner}</div>
          <h1>{c.name}</h1>
          <p>{c.desc}</p>
          <div className="ce-trust">
            <StatusBadge status={c.status} />
            <span className="oh-badge mono">{c.freshness}</span>
            <span className="oh-badge mono">{fmt(c.queriesPerDay)} served/day</span>
            {c.langs > 1 && <span className="oh-badge mono">{c.langs} langs</span>}
          </div>
        </div>
        <div className="ce-detail-actions">
          <button className="oh-btn oh-btn--primary" onClick={() => navigate('/serve')}>Serve →</button>
          <button className="oh-btn oh-btn--ghost">⤓ Download bundle</button>
        </div>
      </div>

      <div className="oh-tabs">
        {TABS.map(([k, l]) => <button key={k} className={'oh-tab' + (tab === k ? ' on' : '')} onClick={() => setTab(k)}>{l}</button>)}
      </div>

      {tab === 'tiers' && (
        <div className="ce-tiers">
          {['raw', 'compressed', 'hyper'].map((t) => (
            <div className={'oh-card ce-tier' + (t === 'hyper' ? ' feat' : '')} key={t}>
              <div className="th"><span className="tname"><TierDot tier={t} />{TIER_META[t].label}</span>
                {t === 'hyper' && <span className="oh-badge oh-badge--verified">agent-ready</span>}</div>
              <div className="tsub">{TIER_META[t].blurb}</div>
              <Meter pct={tierFill[t]} tone={TIER_META[t].tone} />
              <div className="mlabel"><span>relative size</span><span>{tierFill[t]}%</span></div>
              <div className="stat"><span className="k">Size</span><span className="v">{c.tiers[t].size}</span></div>
              <div className="stat"><span className="k">Tokens</span><span className="v">{c.tiers[t].tokens}</span></div>
              <div style={{ marginTop: 14, display: 'flex', gap: 8 }}>
                <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/serve')}>Serve</button>
                <button className="oh-btn oh-btn--ghost oh-btn--sm">⤓ Download</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'provenance' && (
        <div className="oh-card ce-panel">
          <div className="ce-prov-head"><span>Sources</span><span className="mono">{fmt(srcTotal(c))} total · cadence {c.cadence}</span></div>
          <table className="oh-table">
            <thead><tr><th>Source</th><th>Items</th><th>Citations</th><th>Status</th></tr></thead>
            <tbody>
              {c.sources.map(([name, n]) => (
                <tr key={name}><td>{name}</td><td className="mono">{fmt(n)}</td><td>{c.citations ? <span className="oh-badge oh-badge--verified oh-badge--sm">✔ anchored</span> : '—'}</td><td><StatusBadge status={c.status} /></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'serve' && (
        <div className="oh-card ce-panel">
          <div className="ce-code">
            <div><span className="c"># serve this corpus to an agent</span></div>
            <div><span className="k">GET</span> /v1/corpora/<span className="s">{c.id}</span>/serve?tier=<span className="s">hyper-efficient</span>&amp;cite=<span className="s">true</span></div>
            <div style={{ marginTop: 8 }}><span className="c"># auth: Bearer &lt;token&gt; · {fmt(c.queriesPerDay)} queries/day on this corpus</span></div>
          </div>
          <div style={{ marginTop: 14 }}><button className="oh-btn oh-btn--primary" onClick={() => navigate('/serve')}>Open in serve console →</button></div>
        </div>
      )}

      {tab === 'compliance' && (
        <div className="oh-card ce-panel">
          <div className="ce-prov-head"><span>Emitted artifacts</span><span className="mono">signed · regulator-facing</span></div>
          <div className="ce-artifacts">
            {ARTIFACTS.map(([name, file, desc]) => (
              <div className="ce-artifact" key={file}>
                <div className="ar-body"><div className="ar-name">{name}</div><div className="ar-desc">{desc}</div></div>
                <div className="ar-side"><span className="mono ar-file">{file}</span><button className="oh-btn oh-btn--ghost oh-btn--sm">⤓ Emit</button></div>
              </div>
            ))}
          </div>
          <div className="ce-artifact-note mono">Provenance proves origin; verification proves it’s still true — every artifact carries both.</div>
        </div>
      )}
      {tab === 'settings' && (
        <div className="oh-card ce-panel ce-settings">
          {[['Refresh cadence', c.cadence], ['Owner', c.owner], ['Created', c.created], ['Access', c.private ? 'Private · gated' : 'Workspace'], ['Citation anchoring', c.citations ? 'On' : 'Off']].map(([k, v]) => (
            <div className="ce-setting" key={k}><span className="k">{k}</span><span className="v">{v}</span></div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------- SERVE CONSOLE ----------------
const MOCK_CHUNKS = [
  ['acme-policy', 'Vendors handling regulated data must complete a Tier-2 security review before onboarding.', 'Security Policy §4.2'],
  ['acme-policy', 'Renewal notices for auto-renew contracts must be sent no later than 90 days before term end.', 'Contract SOP §7'],
  ['acme-policy', 'Any access to the production data store requires a logged, time-boxed approval.', 'Access Control §2.1'],
];
const SERVE_PIPELINE = [
  ['Parse query', null], ['Retrieve', 'tier'], ['Rerank', null], ['Check freshness', null],
  ['Verify vs live sources', 'star'], ['Reconcile conflicts', null], ['Cite & serve', null],
];
// agent- & model-neutral destinations — the same verified corpus feeds any of them
const DESTINATIONS = ['Claude Code', 'Cursor', 'Contextual', 'Snowflake', 'pgvector', 'MCP'];
function ServePage() {
  const [corpus, setCorpus] = React.useState('acme-policy');
  const [tier, setTier] = React.useState('hyper');
  const [q, setQ] = React.useState('What is required before onboarding a vendor that handles regulated data?');
  const [ran, setRan] = React.useState(true);
  const [dest, setDest] = React.useState('Claude Code');
  const openConf = CONFLICTS.filter((c) => c.corpusId === corpus && (c.status === 'open' || c.status === 'escalated')).length;
  return (
    <div className="ce-page">
      <PageHead eyebrow="Serve" title="Serve console"
        sub="Query a corpus the way an agent would — retrieved, checked against live sources, and returned with a citation behind every claim." />
      <div className="ce-serve-grid">
        <div className="ce-serve-l">
          <div className="oh-card ce-panel">
            <label className="oh-field"><span>Corpus</span>
              <select value={corpus} onChange={(e) => { setCorpus(e.target.value); setRan(false); }}>
                {CORPORA.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </label>
            <label className="oh-field"><span>Tier</span>
              <div className="oh-segment">
                {['raw', 'compressed', 'hyper'].map((t) => <button key={t} className={tier === t ? 'on' : ''} onClick={() => { setTier(t); setRan(false); }}>{TIER_META[t].label}</button>)}
              </div>
            </label>
            <label className="oh-field"><span>Serve to <span className="ce-field-hint">agent- &amp; model-neutral</span></span>
              <div className="ce-destgrid">
                {DESTINATIONS.map((d) => <button key={d} type="button" className={'ce-dest' + (dest === d ? ' on' : '')} onClick={() => setDest(d)}>{d}</button>)}
              </div>
            </label>
            <label className="oh-field"><span>Query</span>
              <textarea value={q} onChange={(e) => { setQ(e.target.value); setRan(false); }} rows={3} />
            </label>
            <button className="oh-btn oh-btn--primary" onClick={() => setRan(true)}>Run query →</button>
            <div className="ce-code" style={{ marginTop: 16 }}>
              <div><span className="k">GET</span> /v1/corpora/<span className="s">{corpus}</span>/serve</div>
              <div>&nbsp;?tier=<span className="s">{tier === 'hyper' ? 'hyper-efficient' : tier}</span>&amp;cite=<span className="s">true</span></div>
            </div>
          </div>
          <div className="oh-card ce-panel ce-pipeline">
            <div className="ce-pipe-head">Serve pipeline <span className="mono">{ran ? '7 / 7' : 'idle'}</span></div>
            {SERVE_PIPELINE.map(([label, kind]) => (
              <div className={'ce-pipe-step' + (ran ? ' done' : '') + (kind === 'star' ? ' star' : '')} key={label}>
                <span className="mk">{ran ? '✓' : '○'}</span>
                <span className="lb">{label}{kind === 'tier' ? ' · ' + TIER_META[tier].label : ''}</span>
                {kind === 'star' && ran && <span className="oh-badge oh-badge--verified oh-badge--sm">2 sources</span>}
              </div>
            ))}
          </div>
        </div>
        <div className="oh-card ce-panel ce-response">
          <div className="ce-resp-head">
            <span>Returned context</span>
            <span className="oh-badge oh-badge--verified">✔ {MOCK_CHUNKS.length} cited chunks</span>
          </div>
          {ran && (openConf > 0
            ? <div className="ce-vbanner warn"><span className="i">⚠</span><div>{openConf} open conflict{openConf > 1 ? 's' : ''} on this corpus — claims found stale or contradicted vs live sources, escalated to review before serving. <a className="ce-link" onClick={() => navigate('/verify')}>Review →</a></div></div>
            : <div className="ce-vbanner ok"><span className="i">✓</span><div>Verified against live authoritative sources · no open conflicts on this corpus.</div></div>
          )}
          {!ran ? <div className="ce-resp-empty">Run the query to see verified, cited context.</div> : (
            <div className="ce-chunks">
              {MOCK_CHUNKS.map(([cid, text, cite], i) => (
                <div className="ce-chunk" key={i}>
                  <p>“{text}”</p>
                  <div className="ce-chunk-cite"><span className="oh-badge oh-badge--verified oh-badge--sm">✔</span><span className="mono">{cite}</span></div>
                </div>
              ))}
              <div className="ce-resp-foot mono">tier: {TIER_META[tier].label} · {tier === 'hyper' ? '~1.2k' : tier === 'compressed' ? '~5.4k' : '~24k'} tokens · every claim anchored &amp; verified</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------- VERIFICATION / RECONCILIATION (the moat) ----------------
function VerifyPage() {
  // local HITL resolutions so the actions feel live
  const [resolved, setResolved] = React.useState({});
  const act = (id, how) => setResolved((r) => ({ ...r, [id]: how }));
  const stat = [
    ['Open conflicts', VERIFY_ROLLUP.open, 'var(--danger)'],
    ['Awaiting review', VERIFY_ROLLUP.escalated, 'var(--warning)'],
    ['Auto-reconciled · 30d', VERIFY_ROLLUP.autoReconciled, null],
    ['Live sources watched', VERIFY_ROLLUP.sourcesWatched, null],
  ];
  return (
    <div className="ce-page">
      <PageHead eyebrow="Verification" title="Verification & reconciliation"
        sub="Every corpus is pitted against live authoritative sources. When an internal claim goes stale or is contradicted, we flag it — and escalate to a human before an agent ever reads it." />
      <div className="ce-rollup">
        {stat.map(([k, v, tone]) => (
          <div className="ce-roll" key={k}><div className="v" style={tone ? { color: tone } : null}>{v}</div><div className="k">{k}</div></div>
        ))}
      </div>
      <div className="oh-card ce-panel ce-regfeed">
        <div className="ce-regfeed-head"><span>Regulatory change feed</span><span className="mono">live · watching {VERIFY_ROLLUP.sourcesWatched} sources</span></div>
        {REG_CHANGES.map((r, i) => (
          <div className="ce-reg" key={i}>
            <span className={'ce-reg-sev sev-' + r.sev} />
            <div className="ce-reg-body"><div className="ce-reg-change">{r.change}</div><div className="ce-reg-meta mono">{r.authority} · affects {r.affects}</div></div>
            <span className="ce-reg-when mono">{r.when}</span>
          </div>
        ))}
      </div>
      <div className="ce-verify-grid">
        <div className="ce-conflicts">
          <h2 className="ce-section-h">Reconciliation queue</h2>
          {CONFLICTS.map((c) => {
            const sev = SEV_META[c.severity];
            const r = resolved[c.id];
            const auto = c.status === 'auto';
            const escalated = c.status === 'escalated';
            return (
              <div className={'oh-card ce-conflict sev-' + c.severity + (r ? ' is-resolved' : '')} key={c.id}>
                <div className="cf-top">
                  <div className="cf-meta">
                    <span className={'oh-badge ' + sev.cls}>{sev.label}</span>
                    <span className="oh-badge">{CONFLICT_TYPE[c.type]}</span>
                  </div>
                  <span className="cf-detected mono">detected {c.detected}</span>
                </div>
                <a className="cf-corpus ce-link" onClick={() => navigate('/c/' + c.corpusId)}>{c.corpus}</a>
                <div className="cf-claim">“{c.claim}”</div>
                <div className="cf-diff">
                  <div className="cf-side internal">
                    <div className="lbl">Internal corpus</div>
                    <div className="val">{c.internal}</div>
                  </div>
                  <span className="cf-arrow">→</span>
                  <div className="cf-side external">
                    <div className="lbl">Live authoritative source</div>
                    <div className="val">{c.external}</div>
                    <div className="src mono">{c.source} · {c.sourceRef}</div>
                  </div>
                </div>
                <div className="cf-note">{c.note}</div>
                <div className="cf-foot">
                  <span className="cf-conf mono">confidence {Math.round(c.confidence * 100)}%</span>
                  <div className="cf-actions">
                    {r ? <span className={'oh-badge ' + (r === 'kept' ? 'oh-badge--muted' : 'oh-badge--verified')}>{r === 'approved' ? '✔ update applied' : r === 'escalated' ? '⮕ escalated to human' : 'kept internal'}</span>
                      : auto ? <span className="oh-badge oh-badge--verified">✔ auto-reconciled</span>
                      : escalated ? (<>
                          <span className="oh-badge oh-badge--warn">awaiting reviewer</span>
                          <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => act(c.id, 'approved')}>Apply update</button>
                        </>)
                      : (<>
                          <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => act(c.id, 'kept')}>Keep internal</button>
                          <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => act(c.id, 'escalated')}>Escalate</button>
                          <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => act(c.id, 'approved')}>Apply update</button>
                        </>)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <aside className="ce-watched">
          <h2 className="ce-section-h">Sources watched</h2>
          <div className="oh-card ce-panel">
            {WATCHED.map(([name, desc, fresh]) => (
              <div className="ce-watch" key={name}>
                <div className="w-name">{name}</div>
                <div className="w-desc">{desc}</div>
                <div className="w-fresh mono">{fresh}</div>
              </div>
            ))}
            <div className="ce-watch-foot mono">adversarial check runs continuously · human-in-the-loop on anything ambiguous</div>
          </div>
        </aside>
      </div>
    </div>
  );
}

// ---------------- CORPUS COMMONS (oracle-published, signed, verified) ----------------
function CommonsPage() {
  const [domain, setDomain] = React.useState('All');
  const list = COMMONS.filter((c) => domain === 'All' || c.domain === domain);
  return (
    <div className="ce-page">
      <PageHead eyebrow="Baltor corpora" title="Verified corpora"
        sub="Baltor’s own dedicated, continuously-verified corpora — signed at the source, checked against authoritative truth, and served into the agent you already run. The high-stakes regulated domains where stale context is a violation, not an embarrassment." />
      <div className="ce-commons-note">
        <span className="oh-badge oh-badge--verified">✔ signed by the publisher</span>
        <span className="oh-badge">adversarially verified</span>
        <span className="oh-badge mono">verify any corpus by hash</span>
      </div>
      <a className="ce-commons-open" href="../opencontexthub/OpenContextHub Prototype.html">
        <span className="i">⬡</span>
        <span>Looking for open, public-good context — labor rights, food safety, customs? Browse the free packs on <strong>OpenContextHub</strong> →</span>
      </a>
      <div className="ce-domainbar">
        {['All', ...COMMONS_DOMAINS].map((d) => (
          <button key={d} className={'ce-domain-chip' + (domain === d ? ' on' : '')} onClick={() => setDomain(d)}>{d}</button>
        ))}
      </div>
      <div className="ce-commons-grid">
        {list.map((c) => {
          const p = PUBLISHERS[c.publisher];
          return (
            <div className={'oh-card ce-cm-card' + (c.flagship ? ' flagship' : '')} key={c.id}>
              <div className="cm-top">
                <div className="cm-pub">
                  <span className="cm-pub-mk">{p.short}</span>
                  <div className="cm-pub-id"><div className="cm-pub-name">{p.name}</div><div className="cm-pub-kind">{p.kind}</div></div>
                </div>
                <div className="cm-badges">
                  {c.flagship && <span className="oh-badge oh-badge--warn">⚡ sharpest wedge</span>}
                  <span className="oh-badge oh-badge--verified">✔ signed</span>
                </div>
              </div>
              <h3>{c.name}</h3>
              <div className="cm-domain">{c.domain}</div>
              <p className="cm-desc">{c.desc}</p>
              <div className="cm-attest"><span className="mono">⛓ {c.hash}</span><span className="mono">{c.lastVerified}</span></div>
              <div className="cm-foot mono">{c.size} · {c.subscribers.toLocaleString()} subscribers · updates {c.cadence}</div>
              <div className="cm-actions">
                <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => navigate('/ingest')}>Add to workspace</button>
                <button className="oh-btn oh-btn--ghost oh-btn--sm">Verify by hash</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------- SETTINGS · BILLING · USAGE (account layer — now via the SHARED KIT) ----------------
// Baltor renders the kit's Oh* account pages (same components Teleon + the hubs use),
// fed Baltor-specific content. Account chrome stays in-house (AppShell); the pages are kit.
function SettingsPage() {
  const { OhSettings, OhSwitch } = window;
  const [tog, setTog] = React.useState({ residency: false, pii: true, sso: false });
  const t = (k) => setTog((s) => ({ ...s, [k]: !s[k] }));
  const sections = [
    { title: 'Account', rows: [
      { t: 'Name', d: 'Display name on this workspace.', ctrl: <input className="oh-input" defaultValue="Acme Risk & Compliance" /> },
      { t: 'Email', d: 'Sign-in and billing notifications.', ctrl: <input className="oh-input" defaultValue="ops@acme.com" /> },
      { t: 'Workspace', d: 'Visible to your team.', ctrl: <input className="oh-input" defaultValue="Acme · Compliance" /> },
      { t: 'Seats', d: 'People with access to served corpora.', ctrl: <span className="oh-badge mono">4 of 5</span> },
    ] },
    { title: 'Plan & usage', rows: [
      { t: 'Plan', d: 'Pro · live verified serving · 4 seats.', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/billing')}>Billing →</button> },
      { t: 'Usage this cycle', d: 'Serving calls, verification runs, freshness checks, storage.', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/usage')}>View usage →</button> },
    ] },
    { title: 'Developers', rows: [
      { t: 'Serving token', d: 'Bearer token agents pass to /serve.', ctrl: <input className="oh-input" type="password" defaultValue="ctx-••••••••a41e" /> },
      { t: 'MCP endpoint', d: 'For Claude Code, Codex & other agents.', ctrl: <span className="mono">mcp.baltor.ai/acme</span> },
      { t: 'Rotate keys', d: 'Invalidate and reissue all tokens.', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm">Rotate</button> },
    ] },
    { title: 'Privacy & security', rows: [
      { t: 'Data residency · EU', d: 'Pin storage & serving to EU regions.', ctrl: <OhSwitch on={tog.residency} onToggle={() => t('residency')} /> },
      { t: 'PII redaction', d: 'Redact flagged fields before serving context.', ctrl: <OhSwitch on={tog.pii} onToggle={() => t('pii')} /> },
      { t: 'SSO / SAML', d: 'Enterprise single sign-on.', ctrl: <OhSwitch on={tog.sso} onToggle={() => t('sso')} /> },
      { t: 'Audit log', d: 'Every serve, verify and reconciliation, exportable.', ctrl: <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/audit')}>Open log →</button> },
    ] },
  ];
  return <OhSettings sections={sections} />;
}

function BillingPage() {
  const { OhBilling } = window;
  return <OhBilling
    plan={{ name: 'Pro', desc: 'Live verified serving · 4 seats · hosted hyper-efficient tier', price: '$39', per: '/ seat / mo', usagePct: 58, usageLabel: 'Served queries used this cycle' }}
    invoices={[['May 1, 2026', '$182.00', 'Paid'], ['Apr 1, 2026', '$176.40', 'Paid'], ['Mar 1, 2026', '$168.20', 'Paid'], ['Feb 1, 2026', '$159.00', 'Paid']]} />;
}

function UsagePage() {
  const { OhUsage } = window;
  return <OhUsage
    rollup={[['Serving calls', '412k'], ['Verified · cited', '100%'], ['Add-ons', '$182'], ['Cycle resets', 'in 12d']]}
    metrics={[
      { k: 'Serving calls', v: '412k', bars: [.5, .58, .54, .68, .8, .76, .95], hiLast: true },
      { k: 'Verification runs', v: '18.4k', bars: [.4, .5, .46, .6, .66, .7, .85], hiLast: true },
      { k: 'Freshness checks', v: '64.2k', bars: [.5, .55, .6, .5, .7, .8, .9], hiLast: true },
      { k: 'Hosted storage · GB', v: '3.1 / 5', bars: [.3, .35, .4, .45, .5, .56, .62] },
    ]} />;
}

// ---------------- PRICING (open-core boundary) ----------------
const PLANS = [
  { name: 'Free', price: '$0', unit: 'forever', sub: 'Download freezable corpora and build openly.', cta: 'Start free', feats: [['Download raw & compressed tiers', 1], ['Community Commons corpora', 1], ['1 workspace · 1 seat', 1], ['Live verified serving', 0], ['Freshness / change-data-capture', 0]] },
  { name: 'Pro', price: '$39', unit: '/ seat / mo', sub: 'Live, verified, always-current serving.', feat: true, cta: 'Start trial', feats: [['Everything in Free', 1], ['Live verified serving (/serve)', 1], ['Freshness + reconciliation + HITL', 1], ['Hosted hyper-efficient tier', 1], ['Usage analytics & compliance artifacts', 1]] },
  { name: 'Enterprise', price: 'Custom', unit: 'annual', sub: 'Oracle corpora, residency and audit at scale.', cta: 'Contact us', feats: [['Everything in Pro', 1], ['Oracle-publisher Commons access', 1], ['SSO/SAML · EU residency', 1], ['Dedicated verification SLAs', 1], ['AIBOM · EU AI Act dossiers', 1]] },
];
function PricingPage() {
  return (
    <div className="ce-landing">
      <MarketingTop />
      <section className="ce-hero" style={{ paddingBottom: 8 }}>
        <div className="ce-wrap">
          <div className="ce-eyebrow">Pricing</div>
          <h1 style={{ maxWidth: '16ch' }}>Open core, <span className="tinted">verified at the edge</span>.</h1>
          <p style={{ maxWidth: '58ch', fontSize: 'var(--fs-lead)', lineHeight: 'var(--lh-lead)', color: 'var(--fg-muted)', marginTop: 18 }}>The freezable layer is free — download raw &amp; compressed corpora and run them yourself. Live, verified, always-current serving is the subscription.</p>
        </div>
      </section>
      <section className="ce-block">
        <div className="ce-wrap">
          <div className="ce-tiers ce-plans">
        {PLANS.map((p) => (
          <div className={'oh-card ce-tier' + (p.feat ? ' feat' : '')} key={p.name}>
            <div className="th"><span className="tname">{p.name}</span>{p.feat && <span className="oh-badge oh-badge--verified">popular</span>}</div>
            <div className="ce-price"><b>{p.price}</b> <span>{p.unit}</span></div>
            <div className="tsub" style={{ minHeight: 40 }}>{p.sub}</div>
            <button className={'oh-btn ' + (p.feat ? 'oh-btn--primary' : 'oh-btn--ghost')} style={{ width: '100%', justifyContent: 'center' }} onClick={() => navigate('/ingest')}>{p.cta}</button>
            <ul className="ce-plan-feats">
              {p.feats.map(([f, on]) => <li key={f} className={on ? '' : 'off'}><span className="ck">{on ? '✓' : '—'}</span>{f}</li>)}
            </ul>
          </div>
        ))}
      </div>
          <div className="ce-plan-note mono">The open spec, SDK &amp; export are never rate-limited — only live governed serving is metered.</div>
        </div>
      </section>
      <Footer />
    </div>
  );
}

// ---------------- GOVERNANCE ----------------
function GovernancePage() {
  const rows = CORPORA.flatMap((c) => c.sources.slice(0, 1).map(([name]) => ({ corpus: c.name, source: name, status: c.status, fresh: c.freshness, cite: c.citations })));
  return (
    <div className="ce-page">
      <PageHead eyebrow="Governance" title="Governance & provenance"
        sub="The audit layer: where every served claim comes from, when it was last verified, and under what license." />
      <div className="ce-rollup">
        {[['Cited responses', '100%'], ['Verified corpora', CORPORA.filter((c) => c.status === 'verified' || c.status === 'governed').length + '/' + CORPORA.length], ['Avg freshness', '< 24h'], ['Access-gated', CORPORA.filter((c) => c.private).length]].map(([k, v]) => (
          <div className="ce-roll" key={k}><div className="v">{v}</div><div className="k">{k}</div></div>
        ))}
      </div>
      <div className="oh-card ce-panel">
        <table className="oh-table">
          <thead><tr><th>Corpus</th><th>Primary source</th><th>Freshness</th><th>Citations</th><th>Status</th></tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td><a onClick={() => navigate('/corpora')} className="ce-link">{r.corpus}</a></td>
                <td>{r.source}</td>
                <td className="mono">{r.fresh}</td>
                <td>{r.cite ? <span className="oh-badge oh-badge--verified oh-badge--sm">✔ anchored</span> : '—'}</td>
                <td><StatusBadge status={r.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------- DASHBOARD (now via kit OhDashboard; engine grid kept as the `feature` slot) ----------------
function DashboardPage() {
  const { OhDashboard } = window;
  const engine = (
    <div className="ce-dash-engine">
      {[
        ['01', '⇄', 'Reconciliation', 'conflicts remedied', '44'],
        ['02', '◳', 'Hardening', 'fragile facts hardened', '44', true],
        ['03', '✚', 'Enhancement', 'context objects linked', '26'],
        ['04', '◇', 'Optimization', 'avg tokens saved', '13×'],
      ].map(([n, g, t, k, v, core]) => (
        <div className={'oh-card ce-dash-stage' + (core ? ' core' : '')} key={n}>
          <div className="ds-top"><span className="ds-n mono">{n}{core && <em>core</em>}</span><span className="ds-g">{g}</span></div>
          <div className="ds-t">{t}</div>
          <div className="ds-v">{v}</div>
          <div className="ds-k">{k}</div>
        </div>
      ))}
    </div>
  );
  return <OhDashboard
    greeting="Dashboard"
    sub="Your context lifecycle at a glance."
    feature={engine}
    stats={[['Corpora', CORPORA.length], ['Served / day', '21.6k'], ['Open conflicts', '2'], ['Cited', '100%']]}
    activity={[
      { icon: '◎', text: 'Served acme-policy to Claude Code', when: '40s ago' },
      { icon: '⚠', text: 'EUDR date conflict escalated to review', when: '1h ago' },
      { icon: '✓', text: 'eu-reg re-verified vs EUR-Lex', when: '3h ago' },
      { icon: '⤓', text: 'AIBOM artifact emitted', when: '1d ago' },
    ]}
    plan={{ name: 'Team', usagePct: 58, usageLabel: 'Served queries used' }}
    quick={[
      { title: 'Connect a source', desc: 'Ingest & verify new context', href: '/ingest', cta: 'Connect' },
      { title: 'Review conflicts', desc: '2 open, escalated to you', href: '/verify', cta: 'Review' },
      { title: 'Open serve console', desc: 'Query a corpus like an agent', href: '/serve', cta: 'Open' },
    ]} />;
}

// Audit log — now via the SHARED KIT (OhAuditLog), fed Baltor's receipts.
function AuditPage() {
  const { OhAuditLog } = window;
  return <OhAuditLog rows={[
    { t: '40s ago', ev: 'Pack served', icon: '◎', actor: 'Claude Code', target: 'acme-policy / hyper', policy: 'serve:cited', ok: true },
    { t: '6m ago', ev: 'Verification passed', icon: '✓', actor: 'engine', target: 'eu-reg', policy: 'verify:live', ok: true },
    { t: '1h ago', ev: 'Conflict escalated', icon: '⚠', actor: 'reviewer', target: 'eu-reg / EUDR date', policy: 'hitl:review', ok: false },
    { t: '3h ago', ev: 'Artifact emitted', icon: '⤓', actor: 'ada@acme.com', target: 'AIBOM · acme-policy', policy: 'export:aibom', ok: true },
    { t: '1d ago', ev: 'API key created', icon: '⚿', actor: 'ada@acme.com', target: 'Production', policy: 'keys:create', ok: true },
  ]} />;
}

Object.assign(window, { CorporaPage, IngestPage, CorpusDetail, ServePage, VerifyPage, CommonsPage, GovernancePage, SettingsPage, BillingPage, UsagePage, PricingPage, DashboardPage, AuditPage });
