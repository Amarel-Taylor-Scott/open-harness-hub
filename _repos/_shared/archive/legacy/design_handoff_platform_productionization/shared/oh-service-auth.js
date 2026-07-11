/* oh-service-auth.js — service↔service dev-token client for the AI Done Right family.
   Companion to oh-identity.js (user identity); this covers the SERVICE tier:
   Baltor needs a scoped token from Teleon, hubs need tokens from products, etc.

   HONEST STATUS: the backend slice for this ("service-to-service dev tokens") is the
   remaining Phase-1 item in the user's identity service. The ENDPOINTS below are a
   CONTRACT PROPOSAL in the same shape as the shipped /api/identity/<realm>/* routes —
   align them in identity_local_service.py (or edit this one map) when that slice lands.
   Until the backend answers, the client runs a clearly-flagged in-tab simulation.

   Invariants mirrored from the realm design:
   - The CALLER authenticates with its own realm's service secret; tokens are scoped
     from→to + scopes; raw token shown exactly once (hash-only storage).
   - No cross-realm session anything — a service token is NOT a user session.
   - Every call carries X-AIDR-Request-Id for audit-JSONL correlation.
*/
(function () {
  'use strict';

  const REALMS = ['parent', 'baltor', 'teleon',
    'opencontexthub', 'openskillshub', 'opentoolshub', 'openskilltotool', 'openmcphub',
    'opencompressionhub', 'openbenchmarkhub', 'openreviewhub', 'openharnesshub'];

  const SCOPES = ['llm:invoke', 'events:write', 'registry:read', 'registry:publish',
    'serve:cited', 'verify:run', 'state:read', 'state:write'];

  // ---- contract proposal — align with identity_local_service.py when Phase 1 completes ----
  const ENDPOINTS = {
    handshake:   { m: 'POST', p: '/{from}/service/handshake' },   // Bearer <from's service secret> · {to, scopes, note?} → {connection, token(raw, once), receipt}
    connections: { m: 'GET',  p: '/{realm}/service/connections' },// both directions for this realm
    revoke:      { m: 'POST', p: '/{realm}/service/revoke' },     // {id}
    verify:      { m: 'POST', p: '/{to}/service/verify' },        // {token} → {valid, from, to, scopes}
  };

  const rid = () => (crypto.randomUUID ? crypto.randomUUID() : 'req-' + Math.random().toString(16).slice(2));

  // ---------- simulated stand-in (per tab, clearly flagged) ----------
  const sim = { conns: [], seq: 0 };
  function simHandle(op, params, body, secret) {
    switch (op) {
      case 'handshake': {
        if (!secret) return [401, { error: 'missing caller service secret (Bearer)' }];
        if (!REALMS.includes(body.to)) return [400, { error: 'unknown target service' }];
        if (params.from === body.to) return [400, { error: 'a service cannot handshake with itself' }];
        const raw = 'svt_' + params.from + '_' + body.to + '_' + Math.random().toString(36).slice(2, 12);
        const conn = { id: 'sconn_' + (++sim.seq), from: params.from, to: body.to,
          scopes: body.scopes && body.scopes.length ? body.scopes : ['llm:invoke'],
          note: body.note || null, prefix: raw.slice(0, 14) + '…', created: new Date().toISOString(),
          status: 'active', receipt: 'rcpt_sim_' + (1000 + sim.seq) };
        sim.conns.push({ ...conn, _raw: raw });
        return [200, { connection: conn, token: raw, receipt: conn.receipt }];
      }
      case 'connections': {
        const list = sim.conns.filter((c) => (c.from === params.realm || c.to === params.realm) && c.status === 'active')
          .map(({ _raw, ...c }) => c);
        return [200, { connections: list }];
      }
      case 'revoke': {
        const c = sim.conns.find((c) => c.id === body.id);
        if (!c) return [404, { error: 'not found' }];
        c.status = 'revoked';
        return [200, { ok: true, receipt: 'rcpt_sim_' + (++sim.seq + 1000) }];
      }
      case 'verify': {
        const c = sim.conns.find((c) => c._raw === body.token && c.status === 'active');
        return c && c.to === params.to
          ? [200, { valid: true, from: c.from, to: c.to, scopes: c.scopes }]
          : [200, { valid: false }];
      }
      default: return [404, { error: 'unknown op' }];
    }
  }

  function makeServiceAuthClient(opts) {
    const state = {
      base: ((opts && opts.base) || 'http://localhost:9410/api/identity').replace(/\/$/, ''),
      mode: 'unknown',
      onLog: (opts && opts.onLog) || null,
    };

    async function call(op, params, body, secret) {
      const ep = ENDPOINTS[op];
      const requestId = rid();
      const url = state.base + ep.p.replace('{from}', params.from || '').replace('{realm}', params.realm || '').replace('{to}', params.to || '');
      let status, data, simulated = false;
      if (state.mode !== 'simulated') {
        try {
          const r = await fetch(url, {
            method: ep.m,
            headers: Object.assign(
              { 'X-AIDR-Request-Id': requestId },
              ep.m === 'POST' ? { 'Content-Type': 'application/json' } : {},
              secret ? { Authorization: 'Bearer ' + secret } : {}),
            body: ep.m === 'POST' ? JSON.stringify(body || {}) : undefined,
          });
          status = r.status;
          data = await r.json().catch(() => ({}));
          state.mode = 'live';
          if (status === 404) { state.mode = 'simulated'; } // routes not implemented yet → honest fallback
        } catch (e) { state.mode = 'simulated'; }
      }
      if (state.mode === 'simulated') {
        simulated = true;
        [status, data] = simHandle(op, params, body || {}, secret);
      }
      const out = { ok: status >= 200 && status < 300, status, data, simulated, requestId, op,
        who: params.from || params.realm || params.to };
      if (state.onLog) state.onLog(out);
      return out;
    }

    return {
      get mode() { return state.mode; },
      get base() { return state.base; },
      setBase(b) { state.base = String(b).replace(/\/$/, ''); state.mode = 'unknown'; },
      async probe() {
        try {
          const r = await fetch(state.base + '/health', { headers: { 'X-AIDR-Request-Id': rid() } });
          state.mode = r.ok ? 'live' : 'simulated';
        } catch (e) { state.mode = 'simulated'; }
        return state.mode;
      },
      handshake: (from, secret, body) => call('handshake', { from }, body, secret),
      connections: (realm) => call('connections', { realm }),
      revoke: (realm, id) => call('revoke', { realm }, { id }),
      verify: (to, token) => call('verify', { to }, { token }),
    };
  }

  window.OhServiceAuth = { makeServiceAuthClient, REALMS, SCOPES, ENDPOINTS };
})();
