/* =============================================================================
   shared/oh-experiments.js — A/B experiments + event tracking (single source)
   -----------------------------------------------------------------------------
   Framework-agnostic. Load as a plain <script> (like products.js) BEFORE the
   site's app script. Exposes window.OHExp.

   WHY: every site in the family can run copy/layout experiments and emit
   tracking events through ONE engine, so assignment is sticky + consistent and
   events carry the active variant. Real analytics (GA4 / Segment / PostHog) wire
   in by reading window.dataLayer or registering OHExp.onTrack(fn) — no app changes.

   CONCEPTS
     experiment  a key with 2+ weighted variants, e.g. define('hero', ['A','B'])
     assignment  the variant THIS visitor gets — random (weighted), sticky in
                 localStorage, overridable by ?exp=key:Variant (or ?flags=…)
     event       a tracked action {event, ts, vid, props, exp:{…assignments}}.
                 '$exposure' is auto-emitted the first time a variant is shown.

   QUICK USE (vanilla)
     OHExp.define('hero', ['A','B','C']);
     const v = OHExp.variant('hero');               // 'A' | 'B' | 'C' (sticky)
     OHExp.exposure('hero');                         // count the impression
     button.onclick = () => OHExp.track('cta_click', { cta: 'start_free' });

   QUICK USE (React) — see useExperiment() in shared/oh-site.jsx.
   ============================================================================= */
(function (root) {
  var LS_ASSIGN = 'oh-exp';      // { key: variantId }
  var LS_EVENTS = 'oh-events';   // ring buffer of recent events (for the dev panel)
  var LS_VID = 'oh-vid';         // anonymous visitor id
  var EVENT_CAP = 250;

  function readJSON(k, fallback) { try { return JSON.parse(localStorage.getItem(k)) || fallback; } catch (e) { return fallback; } }
  function writeJSON(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }

  function uid() { return 'v_' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4); }
  function visitorId() {
    var id; try { id = localStorage.getItem(LS_VID); } catch (e) {}
    if (!id) { id = uid(); try { localStorage.setItem(LS_VID, id); } catch (e) {} }
    return id;
  }

  // normalize variants → [{ id, weight }]
  function norm(variants) {
    return (variants || []).map(function (v) {
      return (typeof v === 'string' || typeof v === 'number') ? { id: String(v), weight: 1 } : { id: String(v.id), weight: v.weight == null ? 1 : v.weight };
    });
  }

  // URL overrides: ?exp=key:Variant,key2:Variant  (also accepts ?flags=… for legacy)
  function urlOverrides() {
    var out = {};
    try {
      var q = new URLSearchParams(location.search);
      ['exp', 'flags'].forEach(function (param) {
        var raw = q.get(param); if (!raw) return;
        raw.split(',').forEach(function (kv) {
          var p = kv.split(':'); if (p[0]) out[p[0].trim()] = (p[1] != null ? p[1] : 'true').trim();
        });
      });
    } catch (e) {}
    return out;
  }

  var registry = {};                 // key → { variants:[{id,weight}], opts }
  var assigns = readJSON(LS_ASSIGN, {});
  var overrides = urlOverrides();
  var exposed = {};                  // key → true (dedupe exposures per pageload)
  var trackSinks = [];               // fn(payload)
  var changeSinks = [];              // fn(key|null)

  function pickWeighted(variants) {
    var total = variants.reduce(function (s, v) { return s + (v.weight > 0 ? v.weight : 0); }, 0) || variants.length;
    var r = Math.random() * total, acc = 0;
    for (var i = 0; i < variants.length; i++) { acc += (variants[i].weight > 0 ? variants[i].weight : 1); if (r <= acc) return variants[i].id; }
    return variants[variants.length - 1].id;
  }

  function notifyChange(key) { changeSinks.forEach(function (fn) { try { fn(key); } catch (e) {} }); }

  var API = {
    /* register (idempotent). variants: ['A','B'] or [{id,weight}] */
    define: function (key, variants, opts) {
      if (!registry[key]) registry[key] = { variants: norm(variants), opts: opts || {} };
      else if (variants) registry[key].variants = norm(variants); // allow redefining variants
      // honor a URL override the first time we see the experiment
      if (overrides[key] != null && assigns[key] !== overrides[key]) { assigns[key] = overrides[key]; writeJSON(LS_ASSIGN, assigns); }
      return API;
    },
    /* sticky assignment for this visitor (assigns + persists on first call) */
    variant: function (key) {
      if (overrides[key] != null) return overrides[key];
      if (assigns[key] != null) return assigns[key];
      var exp = registry[key];
      var id = exp ? pickWeighted(exp.variants) : null;
      if (id != null) { assigns[key] = id; writeJSON(LS_ASSIGN, assigns); }
      return id;
    },
    /* force a variant (dev panel / QA). Persists + notifies subscribers. */
    assign: function (key, id) { assigns[key] = String(id); writeJSON(LS_ASSIGN, assigns); notifyChange(key); return API; },
    /* clear an assignment so the visitor is re-randomized next read */
    clear: function (key) { delete assigns[key]; delete overrides[key]; delete exposed[key]; writeJSON(LS_ASSIGN, assigns); notifyChange(key); return API; },

    /* record an event. Active experiment assignments are attached automatically. */
    track: function (event, props) {
      var snapshot = {}; Object.keys(registry).forEach(function (k) { snapshot[k] = API.variant(k); });
      var payload = { event: event, ts: Date.now(), vid: visitorId(), props: props || {}, exp: snapshot };
      var ev = readJSON(LS_EVENTS, []); ev.push(payload); if (ev.length > EVENT_CAP) ev = ev.slice(-EVENT_CAP); writeJSON(LS_EVENTS, ev);
      try { (root.dataLayer = root.dataLayer || []).push(Object.assign({ _src: 'oh-exp' }, payload)); } catch (e) {}
      trackSinks.forEach(function (fn) { try { fn(payload); } catch (e) {} });
      try { if (root.console && console.debug) console.debug('[oh-exp]', event, payload.props, snapshot); } catch (e) {}
      return payload;
    },
    /* count an impression for an experiment (deduped per pageload) */
    exposure: function (key) {
      if (exposed[key]) return; exposed[key] = true;
      return API.track('$exposure', { experiment: key, variant: API.variant(key) });
    },

    /* introspection (used by the dev panel) */
    events: function () { return readJSON(LS_EVENTS, []); },
    experiments: function () {
      return Object.keys(registry).map(function (k) {
        return { key: k, variants: registry[k].variants.map(function (v) { return v.id; }), assigned: API.variant(k), overridden: overrides[k] != null, opts: registry[k].opts };
      });
    },
    visitorId: visitorId,
    onTrack: function (fn) { trackSinks.push(fn); return function () { trackSinks = trackSinks.filter(function (f) { return f !== fn; }); }; },
    onChange: function (fn) { changeSinks.push(fn); return function () { changeSinks = changeSinks.filter(function (f) { return f !== fn; }); }; },
    /* wipe everything (events + assignments) */
    reset: function () { assigns = {}; exposed = {}; writeJSON(LS_ASSIGN, {}); writeJSON(LS_EVENTS, []); notifyChange(null); return API; },
    clearEvents: function () { writeJSON(LS_EVENTS, []); notifyChange(null); return API; },
  };

  root.OHExp = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : this);
