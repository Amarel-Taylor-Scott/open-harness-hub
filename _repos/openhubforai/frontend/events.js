/* OpenHubForAI — analytics + A/B beacon client (EVENTS.md contract).
   Posts page/action/exposure/conversion events to the LOCAL events plane
   (scripts/events_local_service.py, port 9420) via navigator.sendBeacon — fire-and-forget,
   graceful NO-OP when the plane is down (the static prototype keeps working).
   - Base URL: window.OH_EVENTS_BASE override (e.g. a tunnel), else the local default below
     (must match architecture/local_service_registry.json local_event_tracking_service.port —
     drift-gated by scripts/check_events_beacon_wiring.py).
   - `anon` is a random per-browser id in localStorage — NEVER an email; PII/keys never sent
     (the plane also rejects them server-side).
   - A/B: deterministic sticky variant assignment in localStorage (oh-exp), forceable via
     ?exp=key:Variant, exposure auto-emitted once per experiment per session. No build step. */
(function () {
  "use strict";

  var DEFAULT_BASE = "http://127.0.0.1:9420";
  var ANON_KEY = "ohh-anon-id";
  var EXP_KEY = "oh-exp";
  var SITE = "openhubforai";

  function base() { return String(window.OH_EVENTS_BASE || DEFAULT_BASE).replace(/\/+$/, ""); }

  function anon() {
    var id;
    try { id = localStorage.getItem(ANON_KEY); } catch (e) {}
    if (!id) {
      id = "a_" + Math.random().toString(16).slice(2, 12);
      try { localStorage.setItem(ANON_KEY, id); } catch (e) {}
    }
    return id;
  }

  function readExp() { try { return JSON.parse(localStorage.getItem(EXP_KEY) || "{}"); } catch (e) { return {}; } }
  function writeExp(m) { try { localStorage.setItem(EXP_KEY, JSON.stringify(m)); } catch (e) {} }

  // honest guard: never emit anything email/key-shaped (defense-in-depth; the plane also rejects)
  var PII_RE = /@|sk-[A-Za-z0-9]{8,}|\bak_[a-z0-9]+_[0-9a-f]{16,}/;

  function send(evt) {
    evt.site = SITE;
    evt.anon = anon();
    var blob;
    try { blob = JSON.stringify(evt); } catch (e) { return false; }
    if (PII_RE.test(blob)) { return false; }           // refuse to send PII/keys
    try {
      // text/plain is CORS-safelisted → no preflight, so cross-origin beacons aren't dropped
      // (the events plane parses the body as JSON regardless of content-type)
      if (navigator.sendBeacon) {
        return navigator.sendBeacon(base() + "/api/events",
          new Blob([blob], { type: "text/plain;charset=UTF-8" }));
      }
      fetch(base() + "/api/events", { method: "POST", headers: { "Content-Type": "text/plain" },
        body: blob, keepalive: true }).catch(function () {});
      return true;
    } catch (e) { return false; }                      // plane down → silent no-op
  }

  var exposed = {};   // experiment -> true, once per page session

  window.OHEvents = {
    site: SITE,
    base: base,
    anon: anon,

    page: function (name, props) { return send({ event: "page", name: name, props: props || {} }); },
    action: function (name, props) { return send({ event: "action", name: name, props: props || {} }); },

    // deterministic sticky A/B assignment; forceable via ?exp=key:Variant
    variant: function (experiment, variants) {
      variants = variants && variants.length ? variants : ["A", "B"];
      var forced = null;
      try {
        var q = new URLSearchParams(location.search).get("exp");
        if (q && q.indexOf(experiment + ":") === 0) { forced = q.split(":")[1]; }
      } catch (e) {}
      var map = readExp();
      var v = forced || map[experiment];
      if (!v) {
        // stable hash of anon+experiment → index (no Math.random: assignment must be sticky)
        var s = anon() + "|" + experiment, h = 0;
        for (var i = 0; i < s.length; i++) { h = (h * 31 + s.charCodeAt(i)) >>> 0; }
        v = variants[h % variants.length];
        map[experiment] = v; writeExp(map);
      }
      if (!exposed[experiment]) {
        exposed[experiment] = true;
        send({ event: "exposure", name: experiment, experiment: experiment, variant: v });
      }
      return v;
    },

    conversion: function (experiment, name) {
      var v = readExp()[experiment];
      if (!v) { return false; }
      return send({ event: "conversion", name: name || experiment, experiment: experiment, variant: v });
    }
  };
}());
