/* shared/oh-identity.js — realm-aware identity client for the full-design kit.
   Wires the kit's OhAuth/account pages to the LOCAL Identity & Access service
   (scripts/identity_local_service.py): each BRAND is its own realm (own accounts/sessions, no SSO).
   - Base: window.OHH_IDENTITY_BASE override, else the local default (matches the realm registry's
     defaults.port). - Sessions stored PER REALM in localStorage ('oh-session-<realm>'); the
     passphrase is never stored. - Honest modes: available() pings /health so OhAuth degrades to a
     clearly-flagged simulated path when the service is down, and never fakes a real session. */
(function () {
  "use strict";
  var DEFAULT_BASE = "http://127.0.0.1:9410";
  function base() { return String(window.OHH_IDENTITY_BASE || DEFAULT_BASE).replace(/\/+$/, ""); }
  function rid() { return "web_" + Math.random().toString(16).slice(2, 14); }
  // brand → realm id (matches the identity realm registry / products.js entity key)
  function realmOf(brand) {
    if (brand && brand.realm) return brand.realm;
    var n = (brand && brand.name) || "";
    return n.toLowerCase().replace(/[^a-z0-9]/g, "");
  }
  function call(method, path, body) {
    return fetch(base() + path, {
      method: method,
      headers: { "Content-Type": "application/json", "X-AIDR-Request-Id": rid() },
      body: method === "POST" ? JSON.stringify(body || {}) : undefined,
    }).then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); });
  }
  function sessKey(realm) { return "oh-session-" + realm; }
  function getSession(realm) { try { return JSON.parse(localStorage.getItem(sessKey(realm)) || "null"); } catch (e) { return null; } }
  function setSession(realm, s) { try { s ? localStorage.setItem(sessKey(realm), JSON.stringify(s)) : localStorage.removeItem(sessKey(realm)); } catch (e) {} }

  window.OHIdentity = {
    realmOf: realmOf,
    base: base,
    session: getSession,
    available: function () {
      return call("GET", "/api/identity/health").then(function (r) { return r.status === 200 && r.body && r.body.ok === true; }, function () { return false; });
    },
    // full signup: register → complete all onboarding steps → login → store realm session
    signup: function (realm, email, pass) {
      return call("POST", "/api/identity/" + realm + "/register", { identifier: email, secret: pass }).then(function (r) {
        if (r.status !== 201) { return { ok: false, error: (r.body && r.body.error) || "registration failed" }; }
        var acct = r.body, steps = acct.onboarding_steps || [];
        var chain = Promise.resolve();
        steps.forEach(function (step) { chain = chain.then(function () { return call("POST", "/api/identity/" + realm + "/onboard", { account_id: acct.account_id, step: step }); }); });
        return chain.then(function () { return window.OHIdentity.login(realm, email, pass); });
      });
    },
    login: function (realm, email, pass) {
      return call("POST", "/api/identity/" + realm + "/login", { identifier: email, secret: pass }).then(function (r) {
        if (r.status === 200 && r.body && r.body.session_id) { setSession(realm, { session_id: r.body.session_id, account_id: r.body.account_id, email: email }); return { ok: true }; }
        return { ok: false, error: "sign in rejected — check your email/passphrase" };
      });
    },
    logout: function (realm) { var s = getSession(realm); setSession(realm, null); return s ? call("POST", "/api/identity/" + realm + "/logout", { session_id: s.session_id }) : Promise.resolve(); },
    validate: function (realm) {
      var s = getSession(realm); if (!s) return Promise.resolve(false);
      return call("POST", "/api/identity/" + realm + "/session/validate", { session_id: s.session_id }).then(function (r) { var ok = r.status === 200 && r.body && r.body.valid === true; if (!ok) setSession(realm, null); return ok; }, function () { return false; });
    },
    mintKey: function (realm, scopes) { var s = getSession(realm); return call("POST", "/api/identity/" + realm + "/api-keys/mint", { session_id: s && s.session_id, scopes: scopes || ["read"] }); },
    listKeys: function (realm) { var s = getSession(realm); return call("GET", "/api/identity/" + realm + "/api-keys?session_id=" + encodeURIComponent(s ? s.session_id : "")); },
    revokeKey: function (realm, id) { var s = getSession(realm); return call("POST", "/api/identity/" + realm + "/api-keys/revoke", { session_id: s && s.session_id, key_id: id }); },
  };

  // page analytics beacon to the LOCAL events plane (scripts/events_local_service.py, :9420) — one
  // page_view per surface load, anon-only, text/plain (CORS-safelisted), graceful no-op when down.
  (function () {
    var EVENTS = (window.OHH_EVENTS_BASE || "http://127.0.0.1:9420").replace(/\/+$/, "");
    var ANON = "oh-anon";
    var id; try { id = localStorage.getItem(ANON); } catch (e) {}
    if (!id) { id = "a_" + Math.random().toString(16).slice(2, 12); try { localStorage.setItem(ANON, id); } catch (e) {} }
    var site = ((window.PORTFOLIO && window.PORTFOLIO.GROUP && window.PORTFOLIO.GROUP.name) || "aidoneright").toLowerCase().replace(/[^a-z0-9]/g, "");
    // "/" fallback: served at a root path (the wired web/ apps) the last path segment is empty,
    // and the events plane requires a non-empty name.
    var evt = { site: site, event: "page", name: (location.pathname.split("/").slice(-1)[0] || "/") + (location.hash || ""), anon: id };
    try {
      if (navigator.sendBeacon) { navigator.sendBeacon(EVENTS + "/api/events", new Blob([JSON.stringify(evt)], { type: "text/plain;charset=UTF-8" })); }
      else { fetch(EVENTS + "/api/events", { method: "POST", headers: { "Content-Type": "text/plain" }, body: JSON.stringify(evt), keepalive: true }).catch(function () {}); }
    } catch (e) {}
  }());
}());
