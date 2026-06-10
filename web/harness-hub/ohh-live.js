/* web/harness-hub/ohh-live.js — live seam between the full-design OHH surfaces and the real
   backend (/api/build on this origin → scripts/showcase/server.py). The design prototype is the
   spec; this file only swaps FIXTURE data for REAL backend data when the backend answers, in the
   honest-fallback style of kit/oh-registry.js: no live response → the surfaces keep their in-file
   design data (the designed exemplar), and live builds never claim a fixture lift number. */
(function () {
  "use strict";
  var state = { task: null, promise: null, data: null };

  function token() {
    // mirrors the legacy app + serve_all_sites share URLs: ?token=… is remembered per browser
    try {
      var t = new URLSearchParams(location.search).get("token");
      if (t) { localStorage.setItem("ohh-token", t); return t; }
      return localStorage.getItem("ohh-token") || "";
    } catch (e) { return ""; }
  }

  // backend component type → the seven-primitive kind keys of the design's PRIMS map
  var KIND = {
    input: "input",
    "knowledge-pack": "knowledge", dataset: "knowledge",
    "rule-pack": "conditional", "logic-pack": "conditional",
    guard: "stop",
    output: "output",
    pattern: "loop",
  };
  function kindOf(step) {
    var k = KIND[step.type] || "action";
    return window.PRIMS && window.PRIMS[k] ? k : "action";
  }
  function polOf(step) {
    if (step.type === "input" || step.type === "output") return "always";
    if (step.type === "harness" || step.type === "pipeline") return "always"; // the model boundary
    return step.branch && step.branch !== "main" ? "optional" : "default";
  }

  // ---- live catalog: hydrate the design's COMPONENTS/BY_SLUG globals with the REAL registry ----
  var catalogListeners = [];
  var catalogLive = false;
  function mapItem(it) {
    var type = it.type;
    var kind = (type === "harness" || type === "pipeline" || type === "pattern") ? "pipeline" : "component";
    return {
      slug: it.id, id: it.id, primitive: KIND[type] || "action", type: type,
      name: it.name, desc: it.desc, kind: kind,
      owner: "free", // the open OpenHarnessHub catalog — every live row is the free registry
      modality: it.modality || "text",
      industry: it.industry || ((it.labels && it.labels[0]) || ""),
      license: it.license, lifecycle: it.lifecycle || "experimental",
      // honesty: prov/src/verified ONLY when the catalog records real provenance; lift/cost are
      // NEVER invented — the design renders "— unproven" / "—" states for them.
      prov: it.prov, src: it.src, verifiedDate: it.verified,
      recurring: type === "harness" || type === "pipeline" || type === "adapter",
      exec: (type === "tool" || type === "processor" || type === "adapter" || type === "harness" || type === "pipeline") ? "code" : "static",
      live: true,
    };
  }
  function hydrate(rows) {
    var target = window.COMPONENTS;
    if (!target || !window.BY_SLUG) return false; // design store not loaded yet
    var mapped = rows.map(mapItem);
    target.length = 0;
    Array.prototype.push.apply(target, mapped);
    Object.keys(window.BY_SLUG).forEach(function (k) { delete window.BY_SLUG[k]; });
    mapped.forEach(function (c) { window.BY_SLUG[c.slug] = c; });
    catalogLive = true;
    catalogListeners.forEach(function (fn) { try { fn(); } catch (e) {} });
    return true;
  }
  function loadCatalog() {
    fetch("/api/components?limit=3000")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !d.results || !d.results.length) return; // honest fallback: design data stays
        var tries = 0;
        (function attempt() {
          if (hydrate(d.results) || tries > 200) return;
          tries += 1; setTimeout(attempt, 60); // the babel-compiled store loads after this file
        }());
      })
      .catch(function () {});
  }
  loadCatalog();

  window.OHHLive = {
    // live-catalog surface: pages subscribe to re-render when the real registry hydrates
    catalogLive: function () { return catalogLive; },
    onCatalog: function (fn) {
      catalogListeners.push(fn);
      if (catalogLive) { try { fn(); } catch (e) {} }
      return function () { catalogListeners = catalogListeners.filter(function (x) { return x !== fn; }); };
    },
    // one in-flight/settled build per task; never rejects (honest fallback = null)
    build: function (task) {
      var t = String(task || "").trim();
      if (!t) return Promise.resolve(null);
      if (state.promise && state.task === t) return state.promise;
      state.task = t;
      state.data = null;
      var qs = "task=" + encodeURIComponent(t) + "&narrate=0" +
        (token() ? "&token=" + encodeURIComponent(token()) : "");
      state.promise = fetch("/api/build?" + qs)
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          state.data = d && d.flow && d.flow.steps && d.flow.steps.length ? d : null;
          return state.data;
        })
        .catch(function () { state.data = null; return null; });
      return state.promise;
    },
    flow: function () { return state.data; },
    // real steps grouped by their primitive stage, in the design's phase/step row shape
    phases: function () {
      var d = state.data;
      if (!d) return null;
      var groups = [], byStage = {};
      d.flow.steps.forEach(function (s) {
        var label = s.stage || "Flow";
        if (!byStage[label]) { byStage[label] = { label: label, steps: [] }; groups.push(byStage[label]); }
        byStage[label].steps.push({
          k: kindOf(s),
          name: s.name || s.id,
          pol: polOf(s),
          desc: s.role || s.subtype || s.id,
        });
      });
      if (groups.length === 1) groups[0].label = null; // a single group renders unlabeled
      return groups;
    },
    costRange: function () {
      var d = state.data;
      var c = d && d.cost && d.cost.balanced && d.cost.balanced.per_task_usd;
      return c ? "$" + c : null;
    },
    assembly: function () {
      var d = state.data;
      return d ? (d.llm_used ? "model-built" : "deterministic") : null;
    },
  };
}());
