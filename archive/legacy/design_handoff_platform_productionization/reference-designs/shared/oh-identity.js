/* oh-identity.js — realm-aware browser client for the AI Done Right Identity service
   (scripts/identity_local_service.py — 12 separate per-product realms, NO SSO).

   Design rules honored:
   - One ENDPOINTS map below = the single place to align paths with the running service.
   - Sessions are stored PER REALM (sessionStorage `aidr.session.<realm>`) — switching
     realms never carries a session across; that would be the SSO bridge the backend bans.
   - Every request carries X-AIDR-Request-Id for audit-JSONL correlation.
   - Honest modes: 'live' (backend answered) or 'simulated' (backend unreachable —
     an in-tab, clearly-flagged stand-in so the static prototype still demonstrates
     the flow; nothing pretends to be the real service).

   Load:  <script src="shared/oh-identity.js"></script>
   Use:   const idc = OhIdentity.makeClient({ realm: 'baltor', base: '/api/identity' });
          await idc.probe(); await idc.register({email,password}); …
*/
(function () {
  'use strict';

  // Live realms only — private-bench hubs are excluded by law (registry-driven on the backend).
  const REALMS = ['parent', 'baltor', 'teleon',
    'opencontexthub', 'openskillshub', 'opentoolshub', 'openskilltotool', 'openmcphub',
    'opencompressionhub', 'openbenchmarkhub', 'openreviewhub', 'openharnesshub'];

  // ---- align these with identity_local_service.py (one edit, whole UI follows) ----
  const ENDPOINTS = {
    health:   { m: 'GET',  p: '/health' },                 // service-level, no realm
    register: { m: 'POST', p: '/{realm}/register' },       // {email, password, name?}
    onboard:  { m: 'POST', p: '/{realm}/onboard' },        // {workspace?, role?}   (session)
    login:    { m: 'POST', p: '/{realm}/login' },          // {email, password}
    logout:   { m: 'POST', p: '/{realm}/logout' },         // (session)
    session:  { m: 'GET',  p: '/{realm}/session/validate' },
    keyMint:  { m: 'POST', p: '/{realm}/keys/mint' },      // {name} → raw key ONCE
    keyList:  { m: 'GET',  p: '/{realm}/keys' },
    keyRevoke:{ m: 'POST', p: '/{realm}/keys/revoke' },    // {id}
  };

  const rid = () => (crypto.randomUUID ? crypto.randomUUID() : 'req-' + Math.random().toString(16).slice(2));
  const sessKey = (realm) => 'aidr.session.' + realm;

  // ---------- simulated stand-in (per tab, per realm, clearly flagged) ----------
  const sim = { users: {}, keys: {}, seq: 0 };
  function simRealm(realm) {
    sim.users[realm] = sim.users[realm] || {};
    sim.keys[realm] = sim.keys[realm] || [];
    return sim;
  }
  function simHandle(op, realm, body, token) {
    simRealm(realm);
    const U = sim.users[realm], K = sim.keys[realm];
    const tok = () => 'simtok_' + realm + '_' + (++sim.seq);
    switch (op) {
      case 'register': {
        if (!body.email || !body.password) return [400, { error: 'email and password required' }];
        if (U[body.email]) return [409, { error: 'account exists in realm ' + realm }];
        U[body.email] = { email: body.email, name: body.name || body.email.split('@')[0], onboarded: false, token: tok() };
        return [200, { token: U[body.email].token, user: { email: body.email, name: U[body.email].name, realm } }];
      }
      case 'login': {
        const u = U[body.email];
        if (!u) return [401, { error: 'invalid credentials (realm ' + realm + ' — realms are separate)' }];
        u.token = tok();
        return [200, { token: u.token, user: { email: u.email, name: u.name, realm } }];
      }
      case 'onboard': {
        const u = Object.values(U).find((u) => u.token === token);
        if (!u) return [401, { error: 'no session' }];
        u.onboarded = true; u.workspace = body.workspace || 'default'; u.role = body.role || 'owner';
        return [200, { ok: true, workspace: u.workspace, role: u.role }];
      }
      case 'session': {
        const u = Object.values(U).find((u) => u.token === token);
        return u ? [200, { valid: true, user: { email: u.email, name: u.name, realm }, onboarded: !!u.onboarded }]
                 : [401, { valid: false }];
      }
      case 'logout': {
        const u = Object.values(U).find((u) => u.token === token);
        if (u) u.token = null;
        return [200, { ok: true }];
      }
      case 'keyMint': {
        const u = Object.values(U).find((u) => u.token === token);
        if (!u) return [401, { error: 'no session' }];
        const raw = 'sk_' + realm + '_' + Math.random().toString(36).slice(2, 14);
        const rec = { id: 'key_' + (++sim.seq), name: body.name || 'default', prefix: raw.slice(0, 12) + '…', created: new Date().toISOString(), lastUsed: null, revoked: false };
        K.push(rec);
        return [200, { key: rec, raw }]; // raw shown exactly once — mirror of the real contract
      }
      case 'keyList': {
        const u = Object.values(U).find((u) => u.token === token);
        if (!u) return [401, { error: 'no session' }];
        return [200, { keys: K.filter((k) => !k.revoked) }];
      }
      case 'keyRevoke': {
        const k = K.find((k) => k.id === body.id);
        if (!k) return [404, { error: 'not found' }];
        k.revoked = true;
        return [200, { ok: true }];
      }
      default: return [404, { error: 'unknown op' }];
    }
  }

  // ---------- client ----------
  function makeClient(opts) {
    const state = {
      realm: (opts && opts.realm) || 'baltor',
      base: ((opts && opts.base) || '/api/identity').replace(/\/$/, ''),
      mode: 'unknown', // 'live' | 'simulated' | 'unknown'
      onLog: (opts && opts.onLog) || null,
    };

    const token = () => sessionStorage.getItem(sessKey(state.realm));
    const setToken = (t) => t ? sessionStorage.setItem(sessKey(state.realm), t)
                              : sessionStorage.removeItem(sessKey(state.realm));

    async function call(op, body) {
      const ep = ENDPOINTS[op];
      const requestId = rid();
      const url = state.base + ep.p.replace('{realm}', state.realm);
      let status, data, simulated = false;
      if (state.mode !== 'simulated') {
        try {
          const r = await fetch(url, {
            method: ep.m,
            headers: Object.assign(
              { 'X-AIDR-Request-Id': requestId },
              ep.m === 'POST' ? { 'Content-Type': 'application/json' } : {},
              token() ? { Authorization: 'Bearer ' + token() } : {}),
            body: ep.m === 'POST' ? JSON.stringify(body || {}) : undefined,
          });
          status = r.status;
          data = await r.json().catch(() => ({}));
          state.mode = 'live';
        } catch (e) {
          state.mode = 'simulated'; // backend unreachable → fall through, flagged
        }
      }
      if (state.mode === 'simulated') {
        simulated = true;
        [status, data] = simHandle(op, state.realm, body || {}, token());
      }
      if (op === 'register' || op === 'login') { if (data && data.token) setToken(data.token); }
      if (op === 'logout') setToken(null);
      const out = { ok: status >= 200 && status < 300, status, data, simulated, requestId, op, realm: state.realm };
      if (state.onLog) state.onLog(out);
      return out;
    }

    return {
      get realm() { return state.realm; },
      get mode() { return state.mode; },
      get base() { return state.base; },
      setRealm(r) { state.realm = r; },            // session does NOT follow — separate realm, separate session
      setBase(b) { state.base = String(b).replace(/\/$/, ''); state.mode = 'unknown'; },
      hasSession: () => !!token(),
      async probe() {
        try {
          const r = await fetch(state.base + ENDPOINTS.health.p, { headers: { 'X-AIDR-Request-Id': rid() } });
          state.mode = r.ok ? 'live' : 'simulated';
        } catch (e) { state.mode = 'simulated'; }
        return state.mode;
      },
      register: (b) => call('register', b),
      onboard: (b) => call('onboard', b),
      login: (b) => call('login', b),
      logout: () => call('logout'),
      session: () => call('session'),
      mintKey: (b) => call('keyMint', b),
      listKeys: () => call('keyList'),
      revokeKey: (id) => call('keyRevoke', { id }),
    };
  }

  window.OhIdentity = { makeClient, REALMS, ENDPOINTS };
})();
