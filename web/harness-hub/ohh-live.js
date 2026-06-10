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

  window.OHHLive = {
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
