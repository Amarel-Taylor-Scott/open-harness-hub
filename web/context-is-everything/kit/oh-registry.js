/* shared/oh-registry.js — realm-aware REGISTRY client for the full-design kit.
   Wires the kit's dashboard / Installed / entry pages to the LOCAL Open*Hub registry plane
   (scripts/registry_local_service.py): public catalog (search/entry) + per-account workspace
   (install/uninstall/publish/summary). The workspace endpoints are session-gated — the account is
   resolved server-side by validating the realm session against the identity service, so the client
   never asserts who it is.
   - Base: window.OHH_REGISTRY_BASE override, else the local default (matches the service registry).
   - Realm + session reuse the identity client's realm id and oh-session-<realm> store (one identity).
   - Honest: workspace() resolves to null when the service is down OR the session is invalid, so the
     UI falls back to its in-file design data and NEVER shows fabricated numbers as real. */
(function () {
  "use strict";
  var DEFAULT_BASE = "http://127.0.0.1:9423";
  function base() { return String(window.OHH_REGISTRY_BASE || DEFAULT_BASE).replace(/\/+$/, ""); }
  function rid() { return "web_" + Math.random().toString(16).slice(2, 14); }
  function realmOf(brand) {
    if (window.OHIdentity && window.OHIdentity.realmOf) return window.OHIdentity.realmOf(brand);
    var n = (brand && (brand.realm || brand.name)) || "";
    return n.toLowerCase().replace(/[^a-z0-9]/g, "");
  }
  function session(realm) {
    if (window.OHIdentity && window.OHIdentity.session) return window.OHIdentity.session(realm);
    try { return JSON.parse(localStorage.getItem("oh-session-" + realm) || "null"); } catch (e) { return null; }
  }
  function sid(realm) { var s = session(realm); return s && s.session_id; }
  function call(method, path, body) {
    return fetch(base() + path, {
      method: method,
      headers: { "Content-Type": "application/json", "X-AIDR-Request-Id": rid() },
      body: method === "POST" ? JSON.stringify(body || {}) : undefined,
    }).then(function (r) { return r.json().then(function (j) { return { status: r.status, body: j }; }); });
  }

  window.OHRegistry = {
    realmOf: realmOf,
    base: base,
    available: function () {
      return call("GET", "/healthz").then(function (r) { return r.status === 200 && r.body && r.body.ok === true; }, function () { return false; });
    },
    // ---- public catalog ----
    search: function (realm, q) {
      return call("GET", "/api/openhub/" + realm + "/search" + (q ? "?q=" + encodeURIComponent(q) : ""))
        .then(function (r) { return (r.body && r.body.entries) || null; }, function () { return null; });
    },
    entry: function (realm, id) {
      return call("GET", "/api/openhub/" + realm + "/entry/" + encodeURIComponent(id))
        .then(function (r) { return r.status === 200 ? r.body : null; }, function () { return null; });
    },
    // ---- per-account workspace (session-gated) ----
    install: function (realm, entry) {
      return call("POST", "/api/openhub/" + realm + "/install", { session_id: sid(realm), entry: entry })
        .then(function (r) { return { ok: r.status === 202, body: r.body }; }, function () { return { ok: false }; });
    },
    uninstall: function (realm, entryId) {
      return call("POST", "/api/openhub/" + realm + "/uninstall", { session_id: sid(realm), entry_id: entryId })
        .then(function (r) { return { ok: r.status === 202, body: r.body }; }, function () { return { ok: false }; });
    },
    publish: function (realm, entry) {
      return call("POST", "/api/openhub/" + realm + "/submit", { session_id: sid(realm), entry: entry })
        .then(function (r) { return { ok: r.status === 202, body: r.body }; }, function () { return { ok: false }; });
    },
    // the account's review-queue submissions (candidates) — null when down / signed out.
    submissions: function (realm) {
      var s = sid(realm);
      if (!s) return Promise.resolve(null);
      return call("GET", "/api/openhub/" + realm + "/submissions?session_id=" + encodeURIComponent(s))
        .then(function (r) { return r.status === 200 && r.body ? (r.body.submissions || []) : null; }, function () { return null; });
    },
    // ---- reviewer surface (gated; reviewer status is operator-granted, never self-served) ----
    amReviewer: function (realm) {
      var s = sid(realm);
      if (!s) return Promise.resolve(false);
      return call("GET", "/api/openhub/" + realm + "/review/status?session_id=" + encodeURIComponent(s))
        .then(function (r) { return !!(r.status === 200 && r.body && r.body.reviewer); }, function () { return false; });
    },
    reviewQueue: function (realm) {
      var s = sid(realm);
      if (!s) return Promise.resolve(null);
      return call("GET", "/api/openhub/" + realm + "/review/queue?session_id=" + encodeURIComponent(s))
        .then(function (r) { return r.status === 200 && r.body ? (r.body.queue || []) : null; }, function () { return null; });
    },
    // a reviewer decision: decision in {approve, reject, revoke}; approve PROMOTES to the catalog.
    decide: function (realm, entryId, decision, reason, score) {
      return call("POST", "/api/openhub/" + realm + "/review/decide",
        { session_id: sid(realm), entry_id: entryId, decision: decision, reason: reason || "", score: score || "" })
        .then(function (r) { return { ok: r.status === 202, body: r.body }; }, function () { return { ok: false }; });
    },
    // ---- admin console (admins grant reviewers; admin status is operator-bootstrapped only) ----
    amAdmin: function (realm) {
      var s = sid(realm);
      if (!s) return Promise.resolve(false);
      return call("GET", "/api/openhub/" + realm + "/admin/status?session_id=" + encodeURIComponent(s))
        .then(function (r) { return !!(r.status === 200 && r.body && r.body.admin); }, function () { return false; });
    },
    // current reviewers + recent contributors (people an admin might promote) — admin-only; null otherwise.
    adminReviewers: function (realm) {
      var s = sid(realm);
      if (!s) return Promise.resolve(null);
      return call("GET", "/api/openhub/" + realm + "/admin/reviewers?session_id=" + encodeURIComponent(s))
        .then(function (r) { return r.status === 200 && r.body ? r.body : null; }, function () { return null; });
    },
    grantReviewer: function (realm, accountId, reason) {
      return call("POST", "/api/openhub/" + realm + "/admin/reviewers/grant",
        { session_id: sid(realm), account_id: accountId, reason: reason || "" })
        .then(function (r) { return { ok: r.status === 202, body: r.body }; }, function () { return { ok: false }; });
    },
    revokeReviewer: function (realm, accountId, reason) {
      return call("POST", "/api/openhub/" + realm + "/admin/reviewers/revoke",
        { session_id: sid(realm), account_id: accountId, reason: reason || "" })
        .then(function (r) { return { ok: r.status === 202, body: r.body }; }, function () { return { ok: false }; });
    },
    // the account's real registry activity (workspace actions + review decisions) for the audit log.
    audit: function (realm) {
      var s = sid(realm);
      if (!s) return Promise.resolve(null);
      return call("GET", "/api/openhub/" + realm + "/audit?session_id=" + encodeURIComponent(s))
        .then(function (r) { return r.status === 200 && r.body ? (r.body.rows || []) : null; }, function () { return null; });
    },
    // the real dashboard summary, or null (down / not signed in) so the UI falls back honestly.
    workspace: function (realm) {
      var s = sid(realm);
      if (!s) return Promise.resolve(null);
      return call("GET", "/api/openhub/" + realm + "/workspace?session_id=" + encodeURIComponent(s))
        .then(function (r) { return r.status === 200 && r.body && r.body.ok ? r.body : null; }, function () { return null; });
    },
  };
}());
