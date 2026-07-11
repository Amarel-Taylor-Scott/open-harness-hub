/* web/teleon/teleon-live.js — live seam between the Teleon site and the LOCAL capability runtime
   (scripts/teleon_local_runtime.py via the same-origin /api/teleon/* proxy). Honest-fallback
   contract (kit style): runtime silent → the surfaces keep their in-file design data; runtime
   answering → capabilities, runs, dashboard stats and usage are REAL (deterministic executions
   with receipts and a real promotion gate — no model calls, no fabricated numbers). */
(function () {
  "use strict";
  var REALM = "teleon";
  var state = { caps: null, runs: null, lastRun: null };
  var listeners = [];

  function notify() { listeners.forEach(function (fn) { try { fn(); } catch (e) {} }); }
  function session() {
    try { return JSON.parse(localStorage.getItem("oh-session-" + REALM) || "null"); } catch (e) { return null; }
  }
  function getJSON(path) {
    return fetch(path).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
  }

  function loadCaps() {
    return getJSON("/api/teleon/" + REALM + "/capabilities").then(function (d) {
      if (d && d.capabilities && d.capabilities.length) { state.caps = d.capabilities; notify(); }
    });
  }
  var runsSettled = false; // one fetch per session-state; a 401 settles honestly to [] (no retry spam)
  function loadRuns() {
    var s = session();
    if (!s || !s.session_id || runsSettled) return Promise.resolve();
    runsSettled = true;
    return fetch("/api/teleon/" + REALM + "/runs?session_id=" + encodeURIComponent(s.session_id))
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { state.runs = (d && d.runs) || []; notify(); })
      .catch(function () { state.runs = []; });
  }
  loadCaps();
  loadRuns();
  window.addEventListener("hashchange", function () { if (session() && state.runs === null) loadRuns(); });

  function fmtScore(v) { return v == null ? "—" : Number(v).toFixed(2); }
  function relTime(ts) {
    var mins = Math.max(0, Math.round((Date.now() / 1000 - ts) / 60));
    if (mins < 1) return "just now";
    if (mins < 60) return mins + "m ago";
    var hrs = Math.round(mins / 60);
    return hrs < 24 ? hrs + "h ago" : Math.round(hrs / 24) + "d ago";
  }

  window.TeleonLive = {
    onReady: function (fn) {
      listeners.push(fn);
      if (state.caps) { try { fn(); } catch (e) {} }
      return function () { listeners = listeners.filter(function (x) { return x !== fn; }); };
    },
    live: function () { return !!state.caps; },

    // the Capabilities table rows, in the design's tuple shape [id, name, status, score, version]
    capabilities: function () {
      if (!state.caps) return null;
      return state.caps.map(function (c) {
        return [c.id, c.name, c.status, fmtScore(c.last_score), "v" + c.version];
      });
    },
    capRollup: function () {
      if (!state.caps) return null;
      var promoted = state.caps.filter(function (c) { return c.status === "promoted"; }).length;
      var inEval = state.caps.filter(function (c) { return c.status === "candidate"; }).length;
      var scored = state.caps.filter(function (c) { return c.last_score != null; });
      var avg = scored.length
        ? (scored.reduce(function (n, c) { return n + c.last_score; }, 0) / scored.length).toFixed(2)
        : "—";
      return [["Capabilities", state.caps.length], ["Promoted", promoted], ["In eval", inEval], ["Avg score", avg]];
    },

    // REALLY execute a capability run (session-gated server-side); never rejects.
    // running() lets the UI show an honest "executing" state instead of any fixture result.
    run: function (capabilityId) {
      var s = session();
      var body = { capability_id: capabilityId || "cap-dates", session_id: s && s.session_id };
      state.running = true;
      state.lastRun = null;
      notify();
      return fetch("/api/teleon/" + REALM + "/runs", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      }).then(function (r) { return r.status === 201 ? r.json() : null; })
        .then(function (d) {
          state.lastRun = d && d.run ? d.run : null;
          state.running = false;
          if (state.lastRun) { runsSettled = false; loadCaps(); loadRuns(); }
          notify();
          return state.lastRun;
        })
        .catch(function () { state.lastRun = null; state.running = false; notify(); return null; });
    },
    running: function () { return !!state.running; },
    lastRun: function () { return state.lastRun; },

    // dashboard stats/activity — real when the runtime (and a session, for activity) is present
    stats: function () {
      if (!state.caps) return null;
      var runs = state.runs || [];
      var promotions = runs.filter(function (r) { return r.decision === "promoted"; }).length;
      var rollbacks = runs.filter(function (r) { return r.decision === "rolled-back"; }).length;
      var scored = state.caps.filter(function (c) { return c.last_score != null; });
      var avg = scored.length
        ? (scored.reduce(function (n, c) { return n + c.last_score; }, 0) / scored.length).toFixed(2)
        : "—";
      return [["Capabilities", state.caps.length], ["Promotions · recorded", promotions],
              ["Rollbacks", rollbacks], ["Avg score", avg]];
    },
    activity: function () {
      if (!state.runs || !state.runs.length) return null;
      return state.runs.slice(-4).reverse().map(function (r) {
        return {
          icon: r.decision === "promoted" ? "✓" : r.decision === "rolled-back" ? "↻" : "⊕",
          text: r.capability + " " + r.decision + " · " + fmtScore(r.score),
          when: relTime(r.at),
        };
      });
    },
    usage: function () {
      if (!state.runs || !state.runs.length) return null;
      var runs = state.runs;
      var promotions = runs.filter(function (r) { return r.decision === "promoted"; }).length;
      var rollbacks = runs.filter(function (r) { return r.decision === "rolled-back"; }).length;
      var us = runs.reduce(function (n, r) { return n + (r.duration_us || 0); }, 0);
      // last-7-bucket spark of run counts (real, normalized for the bar heights)
      var buckets = [0, 0, 0, 0, 0, 0, 0];
      runs.slice(-28).forEach(function (r, i, arr) {
        buckets[Math.min(6, Math.floor((i / Math.max(1, arr.length)) * 7))] += 1;
      });
      var peak = Math.max.apply(null, buckets.concat([1]));
      var bars = buckets.map(function (b) { return Math.max(0.06, b / peak); });
      return {
        rollup: [["Runs · recorded", runs.length], ["Promotions", promotions],
                 ["Rollbacks", rollbacks], ["Exec time", (us / 1000).toFixed(1) + "ms"]],
        metrics: [{ k: "Lifecycle runs", v: String(runs.length), bars: bars, hiLast: true }],
      };
    },
  };
}());
