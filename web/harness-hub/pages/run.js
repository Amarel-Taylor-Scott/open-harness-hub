/* PRun — replayable trace. Animates the RUN_STEPS stream, a model step that
   times out then offers Retry, a simulate banner, and totals (cost/tokens/citations)
   that fill in when done. Ported faithfully from proto-pages-build.jsx::PRun.
   No framework, no build step — vanilla ES5-flavoured JS. */
(function () {
  "use strict";

  /* Trace metadata: per-step timing/cost/token info that cannot be derived from
     the flow graph alone. The `ref` is always derived from PFLOW at runtime so
     the two sources can never drift. model/err flags mark the harness call. */
  var RUN_META = [
    { step: "01", k: "input",       tok: "—",     cost: "—",       ms: "4ms",   model: false, err: false },
    { step: "02", k: "conditional", tok: "—",     cost: "—",       ms: "2ms",   model: false, err: false },
    { step: "03", k: "knowledge",   tok: "2.1k",  cost: "$0.0021", ms: "380ms", model: false, err: false },
    { step: "04", k: "action",      tok: "5.8k",  cost: "$0.0279", ms: "",      model: true,  err: true  },
    { step: "05", k: "loop",        tok: "0.4k",  cost: "$0.0008", ms: "95ms",  model: false, err: false },
    { step: "06", k: "output",      tok: "0.5k",  cost: "$0.0012", ms: "120ms", model: false, err: false },
  ];

  /* Derive RUN_STEPS from PFLOW (single source of truth for node refs/order).
     Falls back to static refs when PFLOW is unavailable. */
  var STATIC_REFS = [
    "inputs/supplier-roster",
    "conditional/tier-risk-gate",
    "knowledge-corpus/csddd-articles",
    "harness/esg-cite-first",
    "pattern/rubric-refine",
    "outputs/csddd-dossier"
  ];

  /* Linearised execution order of PFLOW node ids — matches RUN_META index. */
  var PFLOW_ORDER = ["input", "ct", "kc", "act", "ev", "out"];

  function buildRunSteps(data) {
    var nodes = (data && data.PFLOW && data.PFLOW.nodes) ? data.PFLOW.nodes : [];
    var nodeMap = {};
    for (var i = 0; i < nodes.length; i++) { nodeMap[nodes[i].id] = nodes[i]; }
    var steps = [];
    for (var mi = 0; mi < RUN_META.length; mi++) {
      var meta = RUN_META[mi];
      var node = nodeMap[PFLOW_ORDER[mi]];
      steps.push({
        step:  meta.step,
        k:     meta.k,
        ref:   node ? node.ref : STATIC_REFS[mi],
        tok:   meta.tok,
        cost:  meta.cost,
        ms:    meta.ms,
        model: meta.model,
        err:   meta.err
      });
    }
    return steps;
  }

  /* Populated with live data in onMount; render() uses the static fallback. */
  var RUN_STEPS = buildRunSteps(null);

  /* ------------------------------------------------------------------
     render(ctx) — returns the page HTML string (static, no interactivity)
     The animation state is applied by onMount so this is just structure.
  ------------------------------------------------------------------ */
  function render(ctx) {
    var esc = ctx.esc;

    /* Trace header — totals start hidden (dashes), filled in by onMount */
    var traceHd = [
      "<div class=\"oh-trace-hd\">",
        "<h3>Trace</h3>",
        "<div class=\"oh-trace-tot\">",
          "<div class=\"t\">",
            "<div class=\"v\" id=\"run-tot-cost\">—</div>",
            "<div class=\"k\">est. cost</div>",
          "</div>",
          "<div class=\"t\">",
            "<div class=\"v\" id=\"run-tot-tok\">—</div>",
            "<div class=\"k\">tokens</div>",
          "</div>",
          "<div class=\"t\">",
            "<div class=\"v\" id=\"run-tot-cit\">—</div>",
            "<div class=\"k\">citations</div>",
          "</div>",
        "</div>",
      "</div>",
    ].join("");

    /* Trace rows — rendered for all steps, hidden ones shown by onMount */
    var traceRows = "";
    for (var i = 0; i < RUN_STEPS.length; i++) {
      var s = RUN_STEPS[i];
      var pkey = esc(s.k);
      /* --nodehue is set via inline style; we use a data-k attribute so onMount
         can compute the correct CSS var without relying on global PRIMS. */
      traceRows += [
        "<div class=\"oh-trace-row\" data-run-row=\"" + esc(s.step) + "\" data-k=\"" + pkey + "\" style=\"display:none\">",
          "<span class=\"step\">" + esc(s.step) + "</span>",
          "<span class=\"prim\">",
            "<span class=\"pd\" data-prim-dot=\"" + pkey + "\"></span>",
            "<span class=\"pl\" data-prim-lbl=\"" + pkey + "\"></span>",
          "</span>",
          "<span class=\"ref\">",
            esc(s.ref),
            s.model ? " <span class=\"modelflag\">model</span>" : "",
          "</span>",
          "<span class=\"mono\">" + esc(s.tok) + "</span>",
          "<span class=\"mono\">" + esc(s.cost) + "</span>",
          /* status cell — updated by onMount; placeholder keeps the grid intact */
          "<span class=\"mono ok\" data-run-status=\"" + esc(s.step) + "\"></span>",
        "</div>",
      ].join("");
    }

    /* Error state block (hidden until animation triggers it) */
    var errorBlock = [
      "<div id=\"run-error-msg\" class=\"oh-state-msg error\" style=\"margin:14px;display:none\">",
        "<span class=\"gl\">⊘</span>",
        "<span>",
          "<b>Model provider timed out</b> at the harness call. Nothing was charged for the failed step.",
          " <button id=\"run-retry-btn\" class=\"oh-btn oh-btn--ghost oh-btn--sm\" style=\"margin-left:10px\">↻ Retry step</button>",
        "</span>",
      "</div>",
    ].join("");

    return [
      "<div class=\"pt-page pt-view\">",

        /* Page head */
        "<div class=\"pt-page-head\">",
          "<h1>Run &amp; trace</h1>",
          "<div class=\"sub\">Replayable compliance record — every step, cost, and citation.</div>",
        "</div>",

        /* Simulate banner */
        "<div class=\"pt-sim-banner\">",
          "◌ Simulate mode — model steps are echo-stubs until a provider key is connected.",
          "<span style=\"margin-left:auto\">",
            "<a data-nav=\"/settings\" style=\"color:var(--accent);cursor:pointer\">Connect key →</a>",
          "</span>",
        "</div>",

        /* Run input row */
        "<div class=\"pt-run-input pt-panel\" style=\"margin-bottom:16px\">",
          "<span style=\"font-size:13px;color:var(--fg-muted)\">Sample input</span>",
          "<span class=\"oh-badge mono\">suppliers.csv · 1 row</span>",
          "<span style=\"flex:1\"></span>",
          /* Buttons toggled by onMount */
          "<button id=\"run-btn\" class=\"oh-btn oh-btn--primary oh-btn--sm\">▶ Run flow</button>",
          "<button id=\"run-running-btn\" class=\"oh-btn oh-btn--ghost oh-btn--sm\" style=\"display:none\" disabled>Running…</button>",
        "</div>",

        /* Trace stage */
        "<div class=\"oh-trace-stage\" style=\"border:1px solid var(--line);border-radius:var(--r-lg);height:auto\">",
          traceHd,
          traceRows,
          errorBlock,
        "</div>",

      "</div>",
    ].join("");
  }

  /* ------------------------------------------------------------------
     onMount(host, ctx) — wires the animation + retry logic
  ------------------------------------------------------------------ */
  function onMount(host, ctx) {
    var PRIMS = ctx.PRIMS;
    var toast = ctx.toast;

    /* Rebuild RUN_STEPS from live PFLOW data so refs never drift from data.js */
    RUN_STEPS = buildRunSteps(ctx.data);

    /* State */
    var doneCount = 0;     /* how many steps are visible */
    var running = false;
    var errored = false;
    var recovered = false;
    var timer = null;

    /* DOM references */
    function q(id) { return host.querySelector("#" + id); }
    function qAll(sel) { return Array.prototype.slice.call(host.querySelectorAll(sel)); }

    var runBtn        = q("run-btn");
    var runningBtn    = q("run-running-btn");
    var errorMsg      = q("run-error-msg");
    var retryBtn      = q("run-retry-btn");
    var totCost       = q("run-tot-cost");
    var totTok        = q("run-tot-tok");
    var totCit        = q("run-tot-cit");

    /* Apply PRIMS hue to each trace row (primitive colour dot + label) */
    function applyPrimHues() {
      qAll("[data-prim-dot]").forEach(function (el) {
        var k = el.getAttribute("data-prim-dot");
        var p = PRIMS[k];
        if (!p) return;
        el.style.background = "var(" + p.v + ")";
      });
      qAll("[data-prim-lbl]").forEach(function (el) {
        var k = el.getAttribute("data-prim-lbl");
        var p = PRIMS[k];
        if (!p) return;
        el.textContent = p.label;
        /* colour the label text with --nodehue via the row's inline var */
        var row = el.closest(".oh-trace-row");
        if (row) row.style.setProperty("--nodehue", "var(" + p.v + ")");
      });
    }
    applyPrimHues();

    /* Show a trace row and set its status cell */
    function showRow(idx, isError) {
      var s = RUN_STEPS[idx];
      if (!s) return;
      var row = host.querySelector("[data-run-row=\"" + s.step + "\"]");
      if (!row) return;
      row.style.display = "";

      var statusEl = host.querySelector("[data-run-status=\"" + s.step + "\"]");
      if (!statusEl) return;

      if (isError) {
        statusEl.className = "mono sim";
        statusEl.style.color = "var(--danger)";
        statusEl.textContent = "⊘ timeout";
      } else {
        statusEl.className = "mono ok";
        statusEl.style.color = "";
        statusEl.textContent = "✓ " + (s.ms || "sim");
      }
    }

    /* Update totals display */
    function updateTotals(complete) {
      if (complete) {
        if (totCost) totCost.textContent = "$0.0312";
        if (totTok)  totTok.textContent  = "8.4k";
        if (totCit)  totCit.textContent  = "11";
      } else {
        if (totCost) totCost.textContent = "—";
        if (totTok)  totTok.textContent  = "—";
        if (totCit)  totCit.textContent  = "—";
      }
    }

    /* Toggle run/running buttons */
    function setRunningUI(isRunning) {
      running = isRunning;
      if (runBtn)     runBtn.style.display     = isRunning ? "none" : "";
      if (runningBtn) runningBtn.style.display = isRunning ? "" : "none";
    }

    /* Hide all rows (used when re-running from scratch) */
    function hideAllRows() {
      qAll("[data-run-row]").forEach(function (el) { el.style.display = "none"; });
    }

    /* Hide the error message */
    function hideError() {
      if (errorMsg) errorMsg.style.display = "none";
    }

    /* Main run loop. fromRetry=true → starts from step index 3 (re-runs from the failed step) */
    function startRun(fromRetry) {
      setRunningUI(true);
      if (!fromRetry) {
        doneCount = 0;
        errored = false;
        recovered = false;
        hideAllRows();
        hideError();
        updateTotals(false);
        /* Re-label the run button for subsequent runs */
        if (runBtn) runBtn.textContent = "▶ Re-run";
      }

      var i = fromRetry ? 3 : 0;   /* mirror the prototype: fromRetry starts from index 3 */

      function tick() {
        i += 1;
        doneCount = i;

        /* Check for the timeout error on step 4 (index 3 = step "04") */
        if (i === 4 && !recovered && !fromRetry) {
          /* Show step 04 as error */
          showRow(3, true);
          /* Show the error message */
          if (errorMsg) errorMsg.style.display = "";
          setRunningUI(false);
          errored = true;
          return;
        }

        /* Show the row for steps 1-3 and 5-6 normally;
           also show step 4 without error when continuing after retry */
        showRow(i - 1, false);

        if (i >= RUN_STEPS.length) {
          setRunningUI(false);
          updateTotals(true);
          toast("Run complete · $0.0312");
          return;
        }

        timer = setTimeout(tick, 600);
      }

      timer = setTimeout(tick, 500);
    }

    /* Retry: recovered=true, run from step 4 onward */
    function retryStep() {
      recovered = true;
      errored = false;
      hideError();
      /* Update the errored row to show it is now being retried (remove error styling) */
      var step04Row = host.querySelector("[data-run-row=\"04\"]");
      if (step04Row) {
        var statusEl = host.querySelector("[data-run-status=\"04\"]");
        if (statusEl) {
          statusEl.className = "mono ok";
          statusEl.style.color = "";
          statusEl.textContent = "✓ sim";
        }
      }
      startRun(true);
    }

    /* Wire up button events */
    if (runBtn) {
      runBtn.addEventListener("click", function () {
        if (timer) clearTimeout(timer);
        startRun(false);
      });
    }

    if (retryBtn) {
      retryBtn.addEventListener("click", function () {
        if (timer) clearTimeout(timer);
        retryStep();
      });
    }

    /* Cleanup: clear any pending timer when the route navigates away */
    /* The router destroys the host innerHTML on next navigation, so no
       removeEventListener is needed — but we clear timer to stop any
       in-flight timeouts from firing into a detached DOM. */
    var origNavigate = ctx.navigate;
    /* Expose a cleanup handle on the host element for the router */
    host._ohhCleanup = function () {
      if (timer) { clearTimeout(timer); timer = null; }
    };
  }

  /* ------------------------------------------------------------------
     Register the /run route
  ------------------------------------------------------------------ */
  OpenHubForAI.register("/run", render, onMount, { theme: "dark" });

})();
