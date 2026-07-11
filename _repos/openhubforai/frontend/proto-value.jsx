/* global React, StoreCtx, navigate, PRIMS */
// Freshness (verified feed) + Certified export / attestation — the recurring-value & sales-cred surfaces

/* ============================== FRESHNESS ============================== */
const FEEDS = [
  ['fresh', 'EUR-Lex · CSDDD + EU regs', 'gov · eur-lex.europa.eu', 'hourly', '4m ago', '18,420'],
  ['fresh', 'OFAC / SDN sanctions', 'gov · treasury.gov', '15 min', '2m ago', '9,310'],
  ['fresh', 'National gazettes · 27 EU', 'gov · multi-source', 'daily', '6h ago', '4,120'],
  ['stale', 'EPA / ECHA chemicals', 'gov · echa.europa.eu', 'daily', '9d ago', '6,800'],
  ['fresh', 'US Customs · HS tariffs', 'gov · cbp.gov', 'weekly', '3d ago', '12,040'],
  ['stale', 'FDA · GxP guidance', 'gov · fda.gov', 'weekly', '12d ago', '2,210'],
];
const CDC = [
  ['12:04', 'amend', 'CSDDD Art. 8 transposition (DE) updated — 3 facts superseded, flows re-flagged'],
  ['11:40', 'add', 'OFAC SDN — 12 new sanctioned entities added & signed'],
  ['09:15', 'revoke', '2 EPA discharge limits withdrawn — citing flows blocked pending review'],
  ['Yesterday', 'verify', '1,204 facts re-checked against source · provenance re-signed'],
];
function PFreshness() {
  const { toast } = React.useContext(StoreCtx);
  const [sla, setSla] = React.useState('daily');
  const stColor = (s) => s === 'fresh' ? 'var(--success)' : s === 'stale' ? 'var(--warning)' : 'var(--danger)';
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Freshness</h1><div className="sub">Verified facts scraped from <b>primary government sources</b> — dated, diff-tracked, and cryptographically signed. This is what an exported snapshot loses.</div></div>

      <div className="pt-foundry-top">
        <div className="pt-bigstat hero" style={{ borderColor: 'var(--verified)', boxShadow: '0 0 0 1px var(--verified)' }}><div className="v" style={{ color: 'var(--verified)' }}>52,900</div><div className="k">verified facts · <b>✔ signed</b></div></div>
        <div className="pt-bigstat"><div className="v">6</div><div className="k">primary sources scraped</div></div>
        <div className="pt-bigstat"><div className="v">99.4%</div><div className="k">fresh within SLA</div></div>
        <div className="pt-bigstat"><div className="v">31</div><div className="k">changes captured · 24h</div></div>
      </div>

      <div className="pt-row" style={{ flexWrap: 'wrap', gap: 16 }}>
        <div className="pt-panel" style={{ flex: '2 1 460px' }}>
          <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>source scrapers — we are the verified publisher</div>
          {FEEDS.map(([st, nm, src, cad, last, facts]) => (
            <div className="pt-fresh-src" key={nm}>
              <span className="d" style={{ background: stColor(st) }} />
              <span className="nm">{nm}<small>{src}</small></span>
              <span className="mono">↻ {cad}</span>
              <span className="mono">{st === 'fresh' ? '✓ ' : '⚠ '}{last}</span>
              <span className="mono">{facts}</span>
              <span className="oh-badge oh-badge--verified" style={{ padding: '2px 7px' }}>✔ signed</span>
            </div>
          ))}
        </div>
        <div className="pt-panel" style={{ flex: '1 1 280px' }}>
          <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>change feed · CDC</div>
          {CDC.map(([t, kind, desc]) => (
            <div className="pt-cdc-row" key={desc}><span className="t">{t}</span><span className={'chip ' + kind}>{kind}</span><span className="desc">{desc}</span></div>
          ))}
        </div>
      </div>

      <div className="pt-panel" style={{ marginTop: 16 }}>
        <div className="oh-cc-id mono" style={{ marginBottom: 12 }}>freshness SLA — you pay for the latency of truth</div>
        <div className="pt-sla">
          {[['realtime', 'Real-time', '≤ 15 min · CDC push', 'Enterprise'], ['daily', 'Daily', 'refreshed every 24h', 'Team'], ['weekly', 'Weekly', 'refreshed every 7d', 'Pro']].map(([k, cad, lat, pr]) => (
            <div key={k} className={'pt-sla-tier' + (sla === k ? ' on' : '')} onClick={() => setSla(k)}>
              <div className="cad">{cad}</div><div className="lat">{lat}</div><div className="pr">{pr}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="oh-state-msg" style={{ marginTop: 16, background: 'color-mix(in srgb, var(--verified) 7%, transparent)', border: '1px solid color-mix(in srgb, var(--verified) 30%, var(--line))', borderRadius: 'var(--r-md)', padding: '11px 14px', fontSize: 12.5, lineHeight: 1.5 }}>
        <span className="gl" style={{ color: 'var(--verified)' }}>🛡</span>
        <span><b>Export the flow, lose the feed.</b> A downloaded corpus is a dated snapshot that decays. The live, signed, diff-tracked stream — and the revocation that pulls dead facts out of your flows — only comes with the subscription. <a style={{ color: 'var(--accent)', cursor: 'pointer', fontWeight: 600 }} onClick={() => navigate('/attest')}>See how it's attested →</a></span>
      </div>
    </div>
  );
}

/* ============================== CERTIFIED EXPORT / ATTESTATION ============================== */
const PROV = [
  ['knowledge', 'CSDDD article corpus', 'eur-lex.europa.eu', 'verified 2026-05-28'],
  ['knowledge', 'OFAC / SDN list', 'treasury.gov', 'verified 2026-05-28 11:40'],
  ['conditional', 'High-risk tier gate', 'rule-pack · MIT', 'reviewed 2026-04-02'],
  ['action', 'Cite-first ESG counsel', 'harness · 11 citations', 'gate-passed ▲ +0.41'],
];
function PAttest() {
  const { toast } = React.useContext(StoreCtx);
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Certified export</h1><div className="sub">Provenance an auditor accepts — every fact dated, sourced, and signed. The attestation is the product, and it renews as the facts do.</div></div>
      <div className="pt-attest">
        <div className="pt-cert">
          <div className="pt-seal">✓</div>
          <h3>Provenance attestation</h3>
          <div className="by">Verified by OpenHubForAI</div>
          <div className="crow"><span className="k">Flow</span><span className="v">csddd-grade</span></div>
          <div className="crow"><span className="k">Sourced as of</span><span className="v">2026-05-28</span></div>
          <div className="crow"><span className="k">Valid through</span><span className="v">2026-08-26</span></div>
          <div className="crow"><span className="k">Facts cited</span><span className="v">11 · all signed</span></div>
          <div className="crow"><span className="k">Standard</span><span className="v">C2PA · EU-AI-Act</span></div>
          <div className="hash">sig 0x9c1b7e4a…d2f0a31f</div>
          <button className="oh-btn oh-btn--primary" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} onClick={() => toast('Attestation issued & signed')}>Issue attestation</button>
        </div>
        <div>
          <div className="pt-panel">
            <div className="oh-cc-id mono" style={{ marginBottom: 8 }}>provenance chain — what's behind the certificate</div>
            {PROV.map(([k, nm, src, dt]) => (
              <div className="pt-prov-row" key={nm}><span className="pd" style={{ background: `var(${PRIMS[k].v})` }} /><span className="nm">{nm}<small>{src}</small></span><span className="dt">{dt}</span></div>
            ))}
          </div>
          <div className="pt-panel" style={{ marginTop: 14 }}>
            <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>export targets</div>
            <div className="pt-export-grid">
              {[['📄', 'Compliance pack', 'PDF · audit-ready'], ['{ }', 'JSON-LD', 'structured + citations'], ['🔏', 'C2PA manifest', 'signed provenance'], ['⚖', 'EU-AI-Act record', 'conformity evidence'], ['◆', 'SPDX', 'license SBOM'], ['↻', 'Runtime bundle', 'freezable layer only']].map(([ic, nm, d]) => (
                <button className="pt-export-btn" key={nm} onClick={() => toast(nm + ' exported')}><span className="ic">{ic}</span><span>{nm}<small>{d}</small></span></button>
              ))}
            </div>
          </div>
          <div className="oh-state-msg blocked" style={{ marginTop: 14, background: 'var(--accent-weak)', borderColor: 'color-mix(in srgb, var(--accent) 30%, var(--line))' }}>
            <span className="gl" style={{ color: 'var(--accent)' }}>◷</span>
            <span><b>Certificates expire.</b> This attestation is valid through <b>2026-08-26</b> — after that, the cited facts may have changed. Renewal re-checks every source against the live feed and re-signs. The freezable layer exports forever; the <b>certified, current</b> layer is the subscription.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PFreshness, PAttest });
