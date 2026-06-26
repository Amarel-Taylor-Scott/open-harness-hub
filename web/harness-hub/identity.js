/* OpenHubForAI — identity client (realm: openharnesshub)
   Talks to the LOCAL Identity & Access service (scripts/identity_local_service.py): the owner-locked
   separate-realms model — THIS product's realm only; sessions are realm-scoped opaque handles, useless
   in any other product's realm (no cross-realm account, no SSO).
   - Base URL: window.OHH_IDENTITY_BASE override (e.g. a TryCloudflare preview of port 9410), else the
     local default below. The default port must match architecture/identity_realm_registry.json
     defaults.port — drift-gated by scripts/check_harness_hub_auth_wiring.py.
   - The session handle lives in localStorage. The PASSPHRASE IS NEVER STORED anywhere by this client,
     and a raw API key is shown once by the caller and never persisted.
   - Graceful degradation: available() pings /health; callers must not fake a login when the local
     service is down. No build step, no framework. */
(function () {
  "use strict";

  // realm-parameterized so the SAME wired flow drives any front end's realm (?realm=baltor or
  // window.OHH_IDENTITY_REALM); defaults to this product's own realm. Backend enforces realm
  // isolation regardless — no cross-realm session, no SSO.
  var DEFAULT_REALM = "openharnesshub";
  var REALM = (function () {
    try { return new URLSearchParams(location.search).get("realm") || window.OHH_IDENTITY_REALM || DEFAULT_REALM; }
    catch (e) { return DEFAULT_REALM; }
  })();
  var DEFAULT_BASE = "http://127.0.0.1:9410";
  var SESSION_KEY = "ohh-identity-session";

  function base() { return String(window.OHH_IDENTITY_BASE || DEFAULT_BASE).replace(/\/+$/, ""); }
  function reqId() { return "web_" + Math.random().toString(16).slice(2, 14); }

  function call(method, path, body) {
    return fetch(base() + path, {
      method: method,
      headers: { "Content-Type": "application/json", "X-AIDR-Request-Id": reqId() },
      body: method === "POST" ? JSON.stringify(body || {}) : undefined
    }).then(function (r) {
      return r.json().then(function (j) { return { status: r.status, body: j }; });
    });
  }

  function getSession() {
    try { return JSON.parse(localStorage.getItem(SESSION_KEY) || "null"); } catch (e) { return null; }
  }
  function setSession(s) {
    try {
      if (s) { localStorage.setItem(SESSION_KEY, JSON.stringify(s)); }
      else { localStorage.removeItem(SESSION_KEY); }
    } catch (e) {}
  }

  window.OHHIdentity = {
    realm: REALM,
    base: base,
    session: getSession,

    available: function () {
      return call("GET", "/api/identity/health").then(function (r) {
        return r.status === 200 && r.body && r.body.ok === true;
      }, function () { return false; });
    },

    register: function (identifier, secret) {
      return call("POST", "/api/identity/" + REALM + "/register",
                  { identifier: identifier, secret: secret });
    },

    onboard: function (accountId, step) {
      return call("POST", "/api/identity/" + REALM + "/onboard",
                  { account_id: accountId, step: step });
    },

    login: function (identifier, secret) {
      return call("POST", "/api/identity/" + REALM + "/login",
                  { identifier: identifier, secret: secret }).then(function (r) {
        if (r.status === 200 && r.body && r.body.session_id) {
          setSession({ session_id: r.body.session_id, account_id: r.body.account_id,
                       identifier: identifier });
        }
        return r;
      });
    },

    logout: function () {
      var s = getSession();
      setSession(null);
      if (!s) { return Promise.resolve({ status: 200, body: { logged_out: false } }); }
      return call("POST", "/api/identity/" + REALM + "/logout", { session_id: s.session_id });
    },

    validate: function () {
      var s = getSession();
      if (!s) { return Promise.resolve(false); }
      return call("POST", "/api/identity/" + REALM + "/session/validate",
                  { session_id: s.session_id }).then(function (r) {
        var ok = r.status === 200 && r.body && r.body.valid === true;
        if (!ok) { setSession(null); }
        return ok;
      }, function () { return false; });
    },

    mintKey: function (scopes) {
      var s = getSession();
      // the raw key in the response is shown ONCE by the caller and never persisted by this client
      return call("POST", "/api/identity/" + REALM + "/api-keys/mint",
                  { session_id: s && s.session_id, scopes: scopes || ["read"] });
    },

    listKeys: function () {
      var s = getSession();
      return call("GET", "/api/identity/" + REALM + "/api-keys?session_id="
                  + encodeURIComponent(s ? s.session_id : ""));
    },

    revokeKey: function (keyId) {
      var s = getSession();
      return call("POST", "/api/identity/" + REALM + "/api-keys/revoke",
                  { session_id: s && s.session_id, key_id: keyId });
    }
  };
}());
