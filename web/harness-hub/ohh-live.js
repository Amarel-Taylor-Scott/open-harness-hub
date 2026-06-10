/* web/harness-hub/ohh-live.js — live seam between the full-design OHH surfaces and the real
   backend (/api/build, /api/components, /api/export on this origin → scripts/showcase/server.py).
   The design prototype is the spec; this file only swaps FIXTURE data for REAL backend data when
   the backend answers, in the honest-fallback style of kit/oh-registry.js:
     · no live response → the surfaces keep their in-file design data (the designed exemplar);
     · live builds NEVER claim a lift number (the eval harness hasn't measured one) — the
       surfaces render their "— unproven" states instead;
     · the flow canvas, tier cards, preview phases, swap alternatives and recent flows are all
       derived from the actual build response (steps · stages · recipe · dropped · cost). */
(function () {
  "use strict";
  var state = { task: null, promise: null, data: null, buildMs: 0 };

  function token() {
    // mirrors the legacy app + serve_all_sites share URLs: ?token=… is remembered per browser
    try {
      var t = new URLSearchParams(location.search).get("token");
      if (t) { localStorage.setItem("ohh-token", t); return t; }
      return localStorage.getItem("ohh-token") || "";
    } catch (e) { return ""; }
  }
  function tokenQs() { var t = token(); return t ? "&token=" + encodeURIComponent(t) : ""; }

  // backend component type → the seven-primitive kind keys of the design's PRIMS map
  var KIND = {
    input: "input",
    "knowledge-pack": "knowledge", dataset: "knowledge",
    "rule-pack": "conditional", "logic-pack": "conditional",
    guard: "stop",
    output: "output",
    pattern: "loop",
  };
  var STAGE_KIND = { Input: "input", "Knowledge Corpus": "knowledge", Conditional: "conditional",
                     Actions: "action", "Flow / Loops": "loop", Output: "output" };
  function kindOf(step) {
    var k = KIND[step.type] || "action";
    return window.PRIMS && window.PRIMS[k] ? k : "action";
  }
  function humanize(id) {
    var tail = String(id || "").split("/").pop().replace(/^input-/, "").replace(/-/g, " ");
    return tail.charAt(0).toUpperCase() + tail.slice(1);
  }
  function slugify(text) {
    return String(text || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 28);
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

  // ---- recent flows (REAL user activity in this browser; never fabricated) ----
  function readHistory() {
    try { return JSON.parse(localStorage.getItem("ohh-flows") || "[]"); } catch (e) { return []; }
  }
  function pushHistory(entry) {
    try {
      var rows = readHistory().filter(function (r) { return r.task !== entry.task; });
      rows.unshift(entry);
      localStorage.setItem("ohh-flows", JSON.stringify(rows.slice(0, 8)));
    } catch (e) {}
  }

  // ---- recipe → the preview's phase/step rows (the design's exact shape) ----
  var PHASE_LABEL = { gate: null, enrich: "Pre-model-call", verify_query: "Pre-model-call", call: "Model call" };
  function phaseLabel(phase) {
    return Object.prototype.hasOwnProperty.call(PHASE_LABEL, phase) ? PHASE_LABEL[phase] : "Post-model-call";
  }

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
      var started = Date.now();
      state.promise = fetch("/api/build?task=" + encodeURIComponent(t) + "&narrate=0" + tokenQs())
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          state.buildMs = Date.now() - started;
          state.data = d && d.flow && d.flow.steps && d.flow.steps.length ? d : null;
          if (state.data) {
            pushHistory({
              task: t, ts: Date.now(), steps: state.data.flow.steps.length,
              cost: (state.data.cost && state.data.cost.balanced && state.data.cost.balanced.per_task_usd) || "",
            });
          }
          return state.data;
        })
        .catch(function () { state.data = null; return null; });
      return state.promise;
    },
    flow: function () { return state.data; },

    // real recipe rows (phase-grouped, the design's exact row shape); stage-grouping fallback
    phases: function () {
      var d = state.data;
      if (!d) return null;
      var recipe = d.flow.recipe;
      var groups = [], last = null;
      if (recipe && recipe.length) {
        recipe.forEach(function (s) {
          var label = phaseLabel(s.phase);
          if (!last || last.label !== label) { last = { label: label, steps: [] }; groups.push(last); }
          last.steps.push({ k: (window.PRIMS && window.PRIMS[s.k]) ? s.k : "action",
                            name: s.name, pol: s.tier || "default", desc: s.ref || s.role || "" });
        });
        return groups;
      }
      var byStage = {};
      d.flow.steps.forEach(function (s) {
        var label = s.stage || "Flow";
        if (!byStage[label]) { byStage[label] = { label: label, steps: [] }; groups.push(byStage[label]); }
        byStage[label].steps.push({ k: kindOf(s), name: s.name || s.id, pol: "default", desc: s.role || s.id });
      });
      if (groups.length === 1) groups[0].label = null;
      return groups;
    },

    // the three REAL cost tiers (cheap / balanced / quality) in the design's card shape.
    // lift is null on purpose: live builds never claim a lift number.
    tiers: function () {
      var d = state.data;
      if (!d || !d.cost || !d.cost.cheap) return null;
      var steps = d.flow.steps || [];
      var stages = d.flow.stages || [];
      var kc = 0, cond = 0;
      steps.forEach(function (s) { var k = kindOf(s); if (k === "knowledge") kc += 1; if (k === "conditional") cond += 1; });
      var seq = [];
      stages.forEach(function (s) {
        var k = STAGE_KIND[s.stage];
        if (k && seq.indexOf(k) === -1) seq.push(k);
        if (s.operator && seq.indexOf("op") === -1 && k === "conditional") seq.push("op");
      });
      if (!seq.length) seq = ["input", "knowledge", "action", "output"];
      var licenses = [];
      steps.forEach(function (s) {
        var c = window.BY_SLUG && window.BY_SLUG[s.id];
        if (c && c.license && licenses.indexOf(c.license) === -1) licenses.push(c.license);
      });
      var gov = licenses.slice(0, 2).join(" · ") || "open catalog";
      var recipe = d.flow.recipe || [];
      var frozen = recipe.filter(function (s) { return s.k !== "action" || s.builtin; }).length;
      var freeze = recipe.length ? "~" + Math.round((frozen / recipe.length) * 100) + "% freezable" : "—";
      function card(key, label, dag, rec) {
        var c = d.cost[key] || {};
        return { tier: label, rec: rec, dag: dag, lift: null,
                 comps: steps.length + " components", packs: kc + " knowledge · " + cond + " conditional",
                 gov: gov, cost: "est. $" + (c.per_task_usd || "—"),
                 lat: String(c.how || "").split(";")[0].slice(0, 44), freeze: freeze };
      }
      return [
        card("cheap", "Cheap", seq.filter(function (k) { return ["input", "knowledge", "action", "output"].indexOf(k) !== -1; })),
        card("balanced", "Balanced", seq.filter(function (k) { return k !== "loop"; }), true),
        card("quality", "Quality-first", seq),
      ];
    },

    // the REAL build poured into the designed canvas slots (same topology the engine emits:
    // input → gates → operator → knowledge → one model call → eval, with the refine loop)
    flowSlots: function () {
      var d = state.data;
      if (!d || !window.PFLOW) return null;
      var src = JSON.parse(JSON.stringify(window.PFLOW));
      var steps = d.flow.steps || [];
      var byStage = {};
      (d.flow.stages || []).forEach(function (s) { byStage[s.stage] = s; });
      var named = {};
      steps.forEach(function (s) { named[s.id] = s; });
      // stage `components` entries are full step objects (sometimes bare id strings) — normalize
      function compId(c) { return typeof c === "string" ? c : (c && c.id) || null; }
      function fill(node, comp, glyphFacts) {
        var id = compId(comp);
        if (!id) { node.name = "—"; node.ref = ""; node.facts = "not selected for this task"; node.slug = null; delete node.lift; return; }
        var step = (comp && typeof comp === "object" && comp.name) ? comp : named[id];
        node.slug = (window.BY_SLUG && window.BY_SLUG[id]) ? id : null;
        node.name = (step && step.name) || humanize(id);
        node.ref = id;
        node.facts = glyphFacts;
        delete node.lift; // live nodes never carry a fixture lift badge
      }
      var nodes = {};
      src.nodes.forEach(function (n) { nodes[n.id] = n; });
      var input = (byStage.Input && byStage.Input.components[0]) || null;
      var conds = (byStage.Conditional && byStage.Conditional.components) || [];
      var kcs = (byStage["Knowledge Corpus"] && byStage["Knowledge Corpus"].components) || [];
      var acts = (byStage.Actions && byStage.Actions.components) || [];
      var loops = (byStage["Flow / Loops"] && byStage["Flow / Loops"].components) || [];
      var modelCall = acts.filter(function (c) { return /^(harness|pipeline)\//.test(compId(c) || ""); })[0] || acts[0];
      var evals = acts.filter(function (c) { return /^(rubric|benchmark)\//.test(compId(c) || ""); });
      if (nodes.input) fill(nodes.input, input, "⌖ runtime input · one item / run");
      if (nodes.ct) fill(nodes.ct, conds[0], "◈ " + ((compId(conds[0]) || "").split("/")[0] || "gate") + " · admit / route");
      if (nodes.ca) fill(nodes.ca, conds[1], "◈ gate · block / escalate");
      if (nodes.kc) fill(nodes.kc, kcs[0], "⛁ " + kcs.length + (kcs.length === 1 ? " corpus wired" : " corpora wired"));
      if (nodes.act) fill(nodes.act, modelCall, "⚡ the one model call" + (loops.length ? " · loop-aware" : ""));
      if (nodes.ev) fill(nodes.ev, evals[0] || loops[0], "↻ eval · refine ≤3");
      if (nodes.out) { nodes.out.name = "Result"; nodes.out.ref = compId(byStage.Output && byStage.Output.components[0]) || "result"; nodes.out.facts = "⎘ structured + cited"; nodes.out.slug = null; delete nodes.out.lift; }
      var operator = byStage.Conditional && byStage.Conditional.operator;
      src.opLabel = (operator && operator.op) || "OR";
      return src;
    },
    flowName: function () { return state.task ? "flow/" + slugify(state.task) : null; },
    opLabel: function () { var s = this.flowSlots(); return s ? s.opLabel : null; },

    // REAL swap alternatives: the build's dropped candidates of the same primitive kind
    alts: function (slotId, node) {
      var d = state.data;
      if (!d || !node) return null;
      var dropped = d.flow.dropped || [];
      var sameKind = dropped.filter(function (s) { return kindOf(s) === node.k; }).slice(0, 3);
      if (!sameKind.length && !node.slug) return null;
      var rows = [{ name: node.name, meta: "selected for this task", on: true }];
      sameKind.forEach(function (s) {
        rows.push({ name: s.name || s.id, meta: s.type + (typeof s.score === "number" ? " · match " + s.score.toFixed(2) : ""), on: false });
      });
      return rows;
    },

    // REAL recent flows (this browser's actual builds) in the dashboard's row shape
    recentFlows: function () {
      var rows = readHistory();
      if (!rows.length) return null;
      return rows.map(function (r) {
        return [r.task.length > 44 ? r.task.slice(0, 44) + "…" : r.task,
                "flow/" + slugify(r.task), "✓ built", r.steps + " comp · $" + (r.cost || "—")];
      });
    },

    // REAL export: the open-spec YAML bundle from /api/export (browser download)
    exportYaml: function () {
      if (!state.task) return false;
      var a = document.createElement("a");
      a.href = "/api/export?task=" + encodeURIComponent(state.task) + "&format=yaml" + tokenQs();
      a.download = "";
      document.body.appendChild(a); a.click(); a.remove();
      return true;
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
