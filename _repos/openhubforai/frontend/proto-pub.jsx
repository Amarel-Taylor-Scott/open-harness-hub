/* global React, StoreCtx, navigate */
// Publish to the ecosystem — share facts / knowledge pages / repositories.
// Once published: immutable, content-addressed, signed, permanently public.

function PubToggle({ on, onClick }) { return <span className={'pt-switch' + (on ? ' on' : '')} onClick={onClick}><i /></span>; }

function PPublish() {
  const { toast } = React.useContext(StoreCtx);
  const [mode, setMode] = React.useState('fact');
  const [agentPublish, setAgentPublish] = React.useState(false);
  const [review, setReview] = React.useState('manual');
  const [consent, setConsent] = React.useState(false);
  const [published, setPublished] = React.useState(false);
  const MODES = { fact: 'A fact', page: 'A knowledge page', repo: 'A repository' };

  const doPublish = () => { setPublished(true); toast('Published · immutable & public'); };

  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Publish to the ecosystem</h1><div className="sub">Share your own facts, knowledge pages, and repositories. Once published they are <b>immutable, signed, and permanently public</b> — discoverable by everyone, citable with provenance back to you.</div></div>

      <div className="pt-intent">
        <div>
          <div className="pt-panel">
            <div className="pt-setting-row" style={{ paddingTop: 4 }}><div className="info"><div className="t">What are you sharing?</div></div>
              <div className="pt-seg">{Object.entries(MODES).map(([k, lb]) => <button key={k} className={mode === k ? 'on' : ''} onClick={() => setMode(k)}>{lb}</button>)}</div></div>

            {mode === 'fact' && <>
              <div className="pt-field"><label>Fact / claim</label><input placeholder="e.g. CSDDD Art. 8(3) requires companies to bring actual adverse impacts to an end" /></div>
              <div className="pt-field"><label>Source URL (provenance)</label><input placeholder="https://… primary source" /></div>
            </>}
            {mode === 'page' && <>
              <div className="pt-field"><label>Knowledge-page title</label><input placeholder="Living-wage benchmark · methodology" /></div>
              <div className="pt-field"><label>Body</label><input placeholder="The page content (markdown supported)…" /></div>
              <div className="pt-field"><label>Retrieval triggers</label><input defaultValue="rag · exact-id · keyword" /></div>
            </>}
            {mode === 'repo' && <>
              <div className="pt-field"><label>Repository</label><input placeholder="github.com/your-org/your-corpus" /></div>
              <div className="pt-field"><label>What it contains</label><input placeholder="A governed corpus / component set to normalize & gate" /></div>
            </>}

            <div className="pt-field row2">
              <div><label>Author / attribution</label><input defaultValue="Nadia Okonkwo · Acme Corp" /></div>
              <div><label>License</label><input defaultValue="CC-BY-4.0" /></div>
            </div>
          </div>

          <div className="pt-panel" style={{ marginTop: 14 }}>
            <div className="oh-cc-id mono" style={{ marginBottom: 4 }}>local agent → ecosystem</div>
            <p style={{ fontSize: 12.5, color: 'var(--fg-muted)', margin: '0 0 8px', lineHeight: 1.5 }}>Configure how your Local Agent communicates with the OpenHubForAI agent when publishing. Private data never leaves; only the fact/page/repo you choose, plus its provenance.</p>
            <div className="pt-setting-row"><div className="info"><div className="t">Let my Local Agent publish</div><div className="d">via MCP · <a style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => navigate('/connect')}>manage the bridge →</a></div></div><PubToggle on={agentPublish} onClick={() => setAgentPublish((v) => !v)} /></div>
            {agentPublish && <div className="pt-setting-row"><div className="info"><div className="t">Before it goes public</div><div className="d">Auto-publish vs hold for your review.</div></div>
              <div className="pt-seg">{[['manual', 'Review first'], ['auto', 'Auto-publish']].map(([k, lb]) => <button key={k} className={review === k ? 'on' : ''} onClick={() => setReview(k)}>{lb}</button>)}</div></div>}
            <div className="pt-setting-row"><div className="info"><div className="t">Privacy guard</div><div className="d">Block accidental sharing of flagged private data.</div></div><span className="oh-badge oh-badge--verified">🔒 enforced</span></div>
          </div>
        </div>

        <div>
          <div className="pt-panel" style={{ borderColor: 'color-mix(in srgb, var(--warning) 40%, var(--line))' }}>
            <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>⚠ this is permanent</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, lineHeight: 1.6, color: 'var(--fg)' }}>
              <li><b>Immutable</b> — content-addressed &amp; signed; it can never be edited.</li>
              <li><b>Permanently public</b> — always discoverable on the ecosystem; it cannot be deleted or unpublished.</li>
              <li><b>Supersede, don't delete</b> — corrections are published as a <i>new</i> version, linked from this one.</li>
              <li><b>Attributed to you</b> — provenance traces back to your publisher identity, forever.</li>
              <li>It must clear the <b>lift &amp; provenance gate</b> to become promotable; until then it’s visible as <span className="mono">◷ unverified</span>.</li>
            </ul>
            <label className="pt-setting-row" style={{ cursor: 'pointer', borderBottom: 'none', paddingBottom: 0 }}>
              <PubToggle on={consent} onClick={() => setConsent((v) => !v)} />
              <span className="info"><span className="t">I understand this is immutable &amp; permanent</span></span>
            </label>
            <button className="oh-btn oh-btn--primary" style={{ width: '100%', justifyContent: 'center', marginTop: 14, opacity: consent ? 1 : .5, pointerEvents: consent ? 'auto' : 'none' }} onClick={doPublish}>Publish to the ecosystem →</button>
          </div>

          {published && (
            <div className="pt-panel" style={{ marginTop: 14 }}>
              <div className="oh-cc-id mono" style={{ marginBottom: 8 }}>published · signed</div>
              <div className="pt-codeblock">cas://oh/9c1b7e4a…d2f0a31f
signed 2026-05-28 · CC-BY-4.0
status ◷ unverified → measuring lift…</div>
              <button className="oh-btn oh-btn--ghost oh-btn--sm" style={{ marginTop: 10 }} onClick={() => navigate('/p/pub-9c1b')}>View provenance graph →</button>
            </div>
          )}

          <div className="pt-panel" style={{ marginTop: 14 }}>
            <div className="oh-cc-id mono" style={{ marginBottom: 6 }}>your published objects</div>
            {[['knowledge-page/living-wage-method', 'promoted ▲ +0.22', 'ok'], ['fact/csddd-art-8-3', 'verified ✔', 'ok'], ['corpus/acme-runbook', 'measuring lift', 'pend']].map(([id, st, k]) => (
              <div className="pt-srv" key={id}><span className="dot" style={{ background: k === 'ok' ? 'var(--success)' : 'var(--warning)' }} /><span className="nm mono" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{id}<small>{st} · immutable</small></span><span style={{ fontSize: 10.5, color: 'var(--fg-faint)' }}>🔒 public</span></div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PPublish });
