/* Open Harness Hub — Build module: PBuild (/build) + PResults (/results)
   Faithful vanilla-JS port of proto-pages-build.jsx PBuild and PResults.
   No framework, no build step. Reads OHH.data for TIERS and PRIMS from ctx.
   Registers: /build (dark), /results (dark). */
(function () {
  "use strict";

  /* ---- shared helpers ---- */

  /** Build the mini-DAG HTML for a tier's dag array.
   *  @param {string[]} dag  - array of primitive keys or 'op'
   *  @param {object} PRIMS  - the PRIMS map from ctx
   *  @returns {string} HTML
   */
  function miniStrip(dag, PRIMS) {
    var html = '<div class="oh-minidag">';
    for (var i = 0; i < dag.length; i++) {
      var n = dag[i];
      if (n === "op") {
        html += '<span class="oh-mininode is-op">◇</span>';
      } else {
        var p = PRIMS[n];
        if (p) {
          html += '<span class="oh-mininode" style="background:var(' + p.v + ')">' + p.glyph + "</span>";
        }
      }
      if (i < dag.length - 1) {
        html += '<span class="oh-miniedge"></span>';
      }
    }
    html += "</div>";
    return html;
  }

  /* ================================================================
     /build — PBuild: parse intent + constraints + clarify if ambiguous
  ================================================================ */

  var CONSTRAINT_GROUPS = [
    ["Hosting",        ["Cloud", "BYO-cloud", "Air-gapped"]],
    ["Budget",         ["Low", "Balanced", "No cap"]],
    ["Quality target", ["Fast", "High lift"]]
  ];
  var CLARIFY_OPTS = ["Tier-1 suppliers only", "Full supply chain", "Sanctions + sector risk"];

  function renderBuild(ctx) {
    var task = (ctx.state && ctx.state.task) || "";
    var ambiguous = task.trim().length < 28;
    var e = ctx.esc;

    var html = '<div class="pt-page pt-view">';

    /* page head */
    html += '<div class="pt-page-head">';
    html += "<h1>Confirm the task</h1>";
    html += '<div class="sub">We parsed your task — edit it or add constraints, then assemble.</div>';
    html += "</div>";

    /* two-column intent + constraints */
    html += '<div class="pt-intent">';

    /* left: task + parsed tags + optional clarify */
    html += '<div>';
    html += '<div class="pt-panel">';
    html += '<div class="oh-cc-id mono" style="margin-bottom:8px">task</div>';
    html += '<textarea id="build-task-ta" class="pt-dash-entry" style="width:100%;min-height:70px;border:none;background:transparent;color:var(--fg);font:inherit;resize:none;outline:none">' + e(task) + "</textarea>";
    html += '<div class="pt-intent-tags">';
    html += '<span class="pt-tag">kind <b>classification + grading</b></span>';
    html += '<span class="pt-tag">domain <b>ESG · CSDDD</b></span>';
    html += '<span class="pt-tag">modality <b>text + tabular</b></span>';
    html += '<span class="pt-tag">privacy <b>supplier PII</b></span>';
    html += "</div>"; /* /pt-intent-tags */
    html += "</div>"; /* /pt-panel */

    if (ambiguous) {
      html += '<div class="pt-clarify" style="margin-top:12px">';
      html += '<div class="q">⚠ This task is a little broad. Which due-diligence scope?</div>';
      html += '<div class="opts">';
      for (var ci = 0; ci < CLARIFY_OPTS.length; ci++) {
        html += '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-clarify-opt="' + e(CLARIFY_OPTS[ci]) + '">' + e(CLARIFY_OPTS[ci]) + "</button>";
      }
      html += "</div>"; /* /opts */
      html += "</div>"; /* /pt-clarify */
    }

    html += '<div style="font-size:12px;color:var(--fg-faint);margin-top:14px;display:flex;gap:8px;align-items:center">';
    html += '<span class="oh-badge oh-badge--warn">preview retrieval</span>';
    html += " using placeholder embeddings — connect a source for semantic retrieval.";
    html += "</div>";
    html += "</div>"; /* /left */

    /* right: constraints panel */
    html += '<div class="pt-panel">';
    html += '<div class="oh-cc-id mono" style="margin-bottom:12px">constraints</div>';

    for (var gi = 0; gi < CONSTRAINT_GROUPS.length; gi++) {
      var grp = CONSTRAINT_GROUPS[gi];
      var grpLabel = grp[0];
      var grpOpts  = grp[1];
      html += '<div style="margin-bottom:14px">';
      html += '<div style="font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--fg-faint);margin-bottom:7px">' + e(grpLabel) + "</div>";
      html += '<div style="display:flex;gap:7px;flex-wrap:wrap">';
      for (var oi = 0; oi < grpOpts.length; oi++) {
        /* default selection = index 1 (Balanced / BYO-cloud / High lift), matching prototype */
        html += '<span class="pt-cons-chip' + (oi === 1 ? " on" : "") + '" data-cons-chip>' + e(grpOpts[oi]) + "</span>";
      }
      html += "</div>"; /* /flex */
      html += "</div>"; /* /group */
    }

    html += '<button id="build-assemble-btn" class="oh-btn oh-btn--primary" style="width:100%;justify-content:center;margin-top:6px">Assemble flow →</button>';
    html += "</div>"; /* /right pt-panel */

    html += "</div>"; /* /pt-intent */
    html += "</div>"; /* /pt-page pt-view */
    return html;
  }

  function onMountBuild(host, ctx) {
    /* textarea keeps task state */
    var ta = host.querySelector("#build-task-ta");
    if (ta) {
      ta.addEventListener("input", function () {
        if (ctx.state) ctx.state.task = ta.value;
        try { sessionStorage.setItem("ohp-task", ta.value); } catch (e) {}
      });
    }

    /* clarify option buttons append to the task */
    var clarifyBtns = host.querySelectorAll("[data-clarify-opt]");
    for (var i = 0; i < clarifyBtns.length; i++) {
      (function (btn) {
        btn.addEventListener("click", function () {
          var opt = btn.getAttribute("data-clarify-opt");
          if (ta) {
            ta.value = ta.value + " — " + opt.toLowerCase();
            if (ctx.state) ctx.state.task = ta.value;
            try { sessionStorage.setItem("ohp-task", ta.value); } catch (e) {}
          }
        });
      })(clarifyBtns[i]);
    }

    /* constraint chips: toggle .on within their sibling group */
    var chips = host.querySelectorAll("[data-cons-chip]");
    for (var j = 0; j < chips.length; j++) {
      (function (chip) {
        chip.addEventListener("click", function () {
          /* find siblings: parent's children with [data-cons-chip] */
          var parent = chip.parentNode;
          var siblings = parent ? parent.querySelectorAll("[data-cons-chip]") : [];
          for (var k = 0; k < siblings.length; k++) {
            siblings[k].classList.remove("on");
          }
          chip.classList.add("on");
        });
      })(chips[j]);
    }

    /* assemble button: brief loading state then navigate */
    var assembleBtn = host.querySelector("#build-assemble-btn");
    if (assembleBtn) {
      assembleBtn.addEventListener("click", function () {
        if (assembleBtn.disabled) return;
        assembleBtn.disabled = true;
        assembleBtn.textContent = "Assembling…";
        setTimeout(function () {
          ctx.navigate("/results");
        }, 850);
      });
    }
  }

  /* ================================================================
     /results — PResults: three costed tiers, lift-led, mini-DAG
  ================================================================ */

  function renderResults(ctx) {
    var e = ctx.esc;
    var TIERS = (ctx.data && ctx.data.TIERS) || [];
    var PRIMS = ctx.PRIMS || {};

    var html = '<div class="pt-page pt-view">';

    /* page head */
    html += '<div class="pt-page-head">';
    html += "<h1>Three flows for this task</h1>";
    html += '<div class="sub">Each adds vetted components &amp; knowledge for more lift — cost barely moves, because most lift is <span class="mono">freezable</span> (zero recurring).</div>';
    html += "</div>";

    /* guard: no tiers data */
    if (!TIERS || TIERS.length === 0) {
      html += '<div class="oh-state-msg error"><span class="gl">⊘</span><span>No tier data available. <a data-nav="/build" style="color:var(--accent);cursor:pointer">Go back</a> and try again.</span></div>';
      html += "</div>";
      return html;
    }

    /* loading skeleton rendered server-side to true loading state via onMount toggle */
    html += '<div class="pt-grid-3" id="results-grid">';

    for (var ti = 0; ti < TIERS.length; ti++) {
      var t = TIERS[ti];
      var isRec = !!t.rec;

      html += '<div class="oh-result' + (isRec ? " oh-result--rec" : "") + '">';

      /* tier row */
      html += '<div class="oh-result-tierrow">';
      html += '<span class="oh-tier' + (isRec ? " oh-tier--rec" : "") + '">' + e(t.tier) + "</span>";
      if (isRec) {
        html += '<span class="oh-rec-badge">Recommended</span>';
      }
      html += "</div>"; /* /tierrow */

      /* mini-DAG — initially skeleton, onMount swaps in real nodes */
      html += '<div class="oh-result-dag-wrap" data-dag="' + e(JSON.stringify(t.dag || [])) + '">';
      /* skeleton placeholder */
      html += '<div class="oh-minidag is-loading"><span class="oh-skel-line" style="width:70%"></span></div>';
      html += "</div>";

      /* lift number */
      html += '<div class="oh-result-lift">';
      html += '<span class="big">▲ ' + e(t.lift || "") + "</span>";
      html += '<span class="sub">capability lift vs a bare model</span>';
      html += "</div>";

      /* source summary */
      html += '<div class="oh-result-src">' + e(t.comps || "") + " · <b>" + e(t.packs || "") + "</b> doing the lift</div>";

      /* governance badge */
      html += '<div class="oh-cc-badges"><span class="oh-badge oh-badge--verified"><span class="gl">✔</span> ' + e(t.gov || "") + "</span></div>";

      /* cost + latency + freeze */
      html += '<div class="oh-result-cost">';
      html += '<span class="mono">' + e(t.cost || "") + " · " + e(t.lat || "") + "</span>";
      html += '<span class="freeze">' + e(t.freeze || "") + "</span>";
      html += "</div>";

      /* CTA button */
      html += '<button class="oh-btn ' + (isRec ? "oh-btn--primary" : "oh-btn--ghost") + '" style="justify-content:center" data-nav="/flow">Open flow</button>';

      html += "</div>"; /* /oh-result */
    }

    html += "</div>"; /* /pt-grid-3 */
    html += "</div>"; /* /pt-page pt-view */
    return html;
  }

  function onMountResults(host, ctx) {
    var PRIMS = ctx.PRIMS || {};

    /* Replace skeleton DAG placeholders with real mini-DAG nodes after a brief
       loading pause that mirrors the prototype's 650 ms useState effect. */
    var dagWraps = host.querySelectorAll(".oh-result-dag-wrap");

    function revealDags() {
      for (var i = 0; i < dagWraps.length; i++) {
        var wrap = dagWraps[i];
        var rawDag = wrap.getAttribute("data-dag");
        var dag = [];
        try { dag = JSON.parse(rawDag || "[]"); } catch (e) { dag = []; }
        wrap.innerHTML = miniStrip(dag, PRIMS);
      }
    }

    var timer = setTimeout(revealDags, 650);

    /* cleanup if host is torn down before timer fires */
    if (host._ohh_cleanup) host._ohh_cleanup();
    host._ohh_cleanup = function () { clearTimeout(timer); };
  }

  /* ================================================================
     Registration
  ================================================================ */

  OHH.register("/build",   renderBuild,   onMountBuild,   { theme: "dark" });
  OHH.register("/results", renderResults, onMountResults, { theme: "dark" });

})();
