/* global React, StoreCtx, navigate */
// Admin portal · Checkout/payment · Internet workers

/* ============================== ADMIN PORTAL ============================== */
const USERS = [
  ['NO', 'Nadia Okonkwo', 'nadia@acme.co', 'Owner', 'active'],
  ['JL', 'Jonas Lindqvist', 'jonas@acme.co', 'Admin', 'active'],
  ['PR', 'Priya Raman', 'priya@acme.co', 'Builder', 'active'],
  ['TW', 'Tom Welles', 'tom@acme.co', 'Viewer', 'invited'],
];
function PAdmin() {
  const { toast } = React.useContext(StoreCtx);
  const [tab, setTab] = React.useState('users');
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Admin</h1><div className="sub">Manage users, credits &amp; trials, and API usage across the workspace.</div></div>
      <div className="pt-config-tabs" style={{ marginBottom: 18 }}>
        {[['users', 'Users & roles'], ['credits', 'Credits & trials'], ['api', 'API usage']].map(([k, lb]) => (
          <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{lb}</button>
        ))}
      </div>

      {tab === 'users' && (
        <div className="pt-panel">
          <div className="pt-toolbar"><span style={{ fontSize: 13, color: 'var(--fg-muted)' }}><b style={{ color: 'var(--fg)' }}>4</b> members · 4 of 6 seats</span><span className="pt-spacer" /><button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => toast('Invite sent')}>+ Invite member</button></div>
          <table className="pt-table">
            <thead><tr><th>Member</th><th>Role</th><th>Status</th><th></th></tr></thead>
            <tbody>{USERS.map(([av, nm, em, role, st]) => (
              <tr key={em}>
                <td><span className="av">{av}</span>{nm}<div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--fg-faint)', marginLeft: 32 }}>{em}</div></td>
                <td><select className="pt-select" defaultValue={role}><option>Owner</option><option>Admin</option><option>Builder</option><option>Viewer</option></select></td>
                <td><span className="pt-dot-st"><span className="d" style={{ background: st === 'active' ? 'var(--success)' : 'var(--warning)' }} />{st}</span></td>
                <td style={{ textAlign: 'right' }}><span style={{ color: 'var(--fg-faint)', cursor: 'pointer' }} onClick={() => toast('Member menu')}>⋯</span></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}

      {tab === 'credits' && (
        <div className="pt-dash-grid">
          <div className="pt-panel">
            <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>credit balance</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 34, fontWeight: 700, color: 'var(--fg)' }}>8,420 <span style={{ fontSize: 14, color: 'var(--fg-muted)' }}>credits</span></div>
            <div style={{ fontSize: 12, color: 'var(--fg-muted)', margin: '4px 0 14px' }}>≈ $84 · 1,250 earned from contributed components</div>
            <div className="pt-toolbar"><button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => navigate('/checkout')}>Buy credits</button><button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Granted 500 credits')}>Grant to member</button></div>
          </div>
          <div className="pt-panel">
            <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>free trials</div>
            <div className="pt-setting-row"><div className="info"><div className="t">Team trial</div><div className="d">14 days · 6 of 14 used · ends May 28</div></div><span className="oh-badge oh-badge--warn">8 days left</span></div>
            <div className="pt-setting-row"><div className="info"><div className="t">Build-on-demand trial</div><div className="d">3 free capability-requests</div></div><span className="oh-badge mono">1 used</span></div>
            <div className="pt-setting-row"><div className="info"><div className="t">Auto-extend for design partners</div><div className="d">Keep trial active past expiry.</div></div><button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Trial extended 14 days')}>Extend</button></div>
          </div>
        </div>
      )}

      {tab === 'api' && (
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 12 }}>API usage — this billing period</div>
          <div className="pt-quota"><div className="row"><span>Search / recommend</span><b>182k / 250k req</b></div><div className="track"><i style={{ width: '73%' }} /></div></div>
          <div className="pt-quota"><div className="row"><span>Pipeline generation</span><b>4.1k / 5k req</b></div><div className="track"><i className="warn" style={{ width: '82%' }} /></div></div>
          <div className="pt-quota"><div className="row"><span>Foundry endpoints</span><b>9.6k / 10k req</b></div><div className="track"><i className="over" style={{ width: '96%' }} /></div></div>
          <div className="pt-quota"><div className="row"><span>MCP gateway calls</span><b>54k / 200k req</b></div><div className="track"><i style={{ width: '27%' }} /></div></div>
          <table className="pt-table" style={{ marginTop: 18 }}>
            <thead><tr><th>API key</th><th>Scope</th><th>Req / day</th><th>Status</th></tr></thead>
            <tbody>
              <tr><td className="mono" style={{ fontFamily: 'var(--font-mono)' }}>oh_live_••••a31f</td><td>catalog · recommend</td><td className="mono" style={{ fontFamily: 'var(--font-mono)' }}>61.2k</td><td><span className="pt-dot-st"><span className="d" style={{ background: 'var(--success)' }} />active</span></td></tr>
              <tr><td className="mono" style={{ fontFamily: 'var(--font-mono)' }}>oh_live_••••7c0b</td><td>foundry</td><td className="mono" style={{ fontFamily: 'var(--font-mono)' }}>9.6k</td><td><span className="pt-dot-st"><span className="d" style={{ background: 'var(--warning)' }} />near limit</span></td></tr>
              <tr><td className="mono" style={{ fontFamily: 'var(--font-mono)' }}>oh_test_••••e2d9</td><td>all · sandbox</td><td className="mono" style={{ fontFamily: 'var(--font-mono)' }}>—</td><td><span className="pt-dot-st"><span className="d" style={{ background: 'var(--fg-faint)' }} />idle</span></td></tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ============================== CHECKOUT / PAYMENT ============================== */
function PCheckout() {
  const { toast } = React.useContext(StoreCtx);
  return (
    <div className="pt-page pt-view">
      <div className="pt-page-head"><h1>Checkout</h1><div className="sub">Upgrade to Team · billed monthly · cancel anytime.</div></div>
      <div className="pt-checkout">
        <div className="pt-panel">
          <div className="oh-cc-id mono" style={{ marginBottom: 14 }}>payment details</div>
          <div className="pt-field"><label>Cardholder name</label><input defaultValue="Nadia Okonkwo" /></div>
          <div className="pt-field"><label>Card number</label><input placeholder="1234 5678 9012 3456" defaultValue="4242 4242 4242 4242" /></div>
          <div className="pt-field row2">
            <div><label>Expiry</label><input placeholder="MM / YY" defaultValue="04 / 28" /></div>
            <div><label>CVC</label><input placeholder="123" defaultValue="•••" /></div>
          </div>
          <div className="pt-field"><label>Billing email</label><input defaultValue="billing@acme.co" /></div>
          <div className="pt-field row2">
            <div><label>Country</label><input defaultValue="Sweden" /></div>
            <div><label>VAT ID (optional)</label><input placeholder="SE••••••••••" /></div>
          </div>
          <div className="pt-card-badge" style={{ marginTop: 4 }}>🔒 Payments secured · PCI-DSS · card stored by processor, never by us</div>
        </div>
        <div>
          <div className="pt-summary">
            <div className="oh-cc-id mono" style={{ marginBottom: 10 }}>order summary</div>
            <div className="li"><span className="mut">Team plan · 4 seats</span><span className="mono">$299</span></div>
            <div className="li"><span className="mut">Build-on-demand credits</span><span className="mono">$60</span></div>
            <div className="li"><span className="mut">Annual discount</span><span className="mono" style={{ color: 'var(--success)' }}>−$36</span></div>
            <div className="li total"><span>Due today</span><span className="mono">$323 / mo</span></div>
            <button className="oh-btn oh-btn--primary" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} onClick={() => { toast('Payment successful — welcome to Team'); navigate('/admin'); }}>Pay $323 →</button>
            <div style={{ fontSize: 11, color: 'var(--fg-faint)', textAlign: 'center', marginTop: 9 }}>The open spec, SDK &amp; export stay free. You’re paying for governed components &amp; live knowledge.</div>
          </div>
          <div className="pt-panel" style={{ marginTop: 14 }}>
            <div className="oh-cc-id mono" style={{ marginBottom: 6 }}>recent invoices</div>
            {[['Apr 2026', '$299', 'paid'], ['Mar 2026', '$299', 'paid'], ['Feb 2026', '$39', 'paid']].map(([m, amt, st]) => (
              <div className="pt-invoice" key={m}><span style={{ flex: 1 }}>{m}</span><span className="mono">{amt}</span><span className="oh-badge oh-badge--lift" style={{ padding: '2px 7px' }}>{st}</span><span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => toast('Invoice downloaded')}>↓</span></div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================== INTERNET WORKERS ============================== */
const WLOG = [
  ['00:00', 'started · goal: refresh CSDDD transposition status (27 member states)'],
  ['00:02', 'browsing eur-lex.europa.eu/legal-content', 'url'],
  ['00:05', 'fetched 3 sources · extracting articles', 'ok'],
  ['00:08', 'browsing national-gazette.de · DE transposition', 'url'],
  ['00:11', 'license filter → 2 kept, 1 rejected (no redistribution)'],
  ['00:14', 'dedupe vs existing corpus · 4 new facts', 'ok'],
  ['00:17', 'lift gate · measuring vs bare model…'],
  ['00:21', 'promoted 2 facts · provenance signed', 'ok'],
];
function PWorkers() {
  const { toast } = React.useContext(StoreCtx);
  const [n, setN] = React.useState(3);
  React.useEffect(() => {
    const t = setInterval(() => setN((x) => (x >= WLOG.length ? 2 : x + 1)), 1500);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>Internet workers</h1><div className="sub">Remote agents that source from the live internet, under the lift &amp; license gate — long-running jobs you can watch, pause, and govern.</div></div>

      <div className="pt-worker">
        <div className="wtop">
          <span className="pt-pulse" />
          <span className="nm">esg-scout-01<small>worker · eu-west · sandboxed browser</small></span>
          <span className="wstats">
            <span className="s"><div className="v">14</div><div className="k">sources</div></span>
            <span className="s"><div className="v">6</div><div className="k">promoted</div></span>
            <span className="s"><div className="v">$0.42</div><div className="k">spend</div></span>
          </span>
        </div>
        <div className="pt-wlog">
          {WLOG.slice(0, n).map(([t, msg, kind], i) => (
            <div key={i} className={'ln' + (i === n - 1 ? ' cur' : '')}>
              <span className="t">[{t}]</span> <span className={kind === 'url' ? 'url' : kind === 'ok' ? 'ok' : ''}>{kind === 'ok' ? '✓ ' : kind === 'url' ? '↗ ' : '· '}{msg}</span>
            </div>
          ))}
          {n < WLOG.length && <div className="ln cur"><span className="t">[live]</span> <span>▋</span></div>}
        </div>
        <div className="pt-wctrl">
          <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Worker paused')}>⏸ Pause</button>
          <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => toast('Worker stopped')}>⊘ Stop</button>
          <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={() => navigate('/foundry')}>View in foundry →</button>
          <span className="pt-spacer" />
          <span style={{ fontSize: 11.5, color: 'var(--fg-faint)', alignSelf: 'center' }}>budget ceiling $5 · auto-stops at limit</span>
        </div>
      </div>

      <div className="pt-worker" style={{ opacity: .75 }}>
        <div className="wtop">
          <span className="pt-pulse" style={{ background: 'var(--warning)', animation: 'none' }} />
          <span className="nm">customs-scout-02<small>worker · us-east · queued</small></span>
          <span className="wstats"><span className="s"><div className="v">—</div><div className="k">queued</div></span></span>
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--fg-muted)' }}>Waiting for a free partition · goal: HS-code updates across 12 jurisdictions.</div>
      </div>

      <div className="pt-toolbar"><button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => toast('New worker — set a goal, sources & budget')}>+ New internet worker</button><span style={{ fontSize: 11.5, color: 'var(--fg-faint)', alignSelf: 'center' }}>Workers run sandboxed, honor robots.txt &amp; licenses, and everything they find passes the lift gate before it’s promoted.</span></div>
    </div>
  );
}

Object.assign(window, { PAdmin, PCheckout, PWorkers });
