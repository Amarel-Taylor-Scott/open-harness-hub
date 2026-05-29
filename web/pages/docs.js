/* Open Harness Hub — Docs / open-spec hub (/docs)
   The open-core FREE layer: spec, seven-primitive grammar, SDK/CLI, export emitters.
   Polish-loop addition (the review removed dead "Docs" nav links — this gives them a real
   home and reinforces the open-core value prop). No React/JSX/build. Registers /docs (light). */
(function () {
  "use strict";

  var MARK_SVG = '<span class="oh-mark" aria-hidden="true">' +
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />' +
    '<path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" />' +
    '</svg></span>';

  // the seven primitives — the open grammar (mirrors app.js PRIMS / docs/concepts taxonomy)
  var PRIMS = [
    ["⌖", "Input", "what the pipeline runs on"],
    ["⛁", "Knowledge Corpus", "governed, cited facts (RAG / exact-id)"],
    ["◈", "Conditional", "deterministic routing — no model call"],
    ["⚡", "Action", "a persona / tool / processor / harness / rubric"],
    ["↻", "Loop / Flow", "iterate or refine until a rubric passes"],
    ["⊘", "Stop", "a guard that halts a run (budget, risk)"],
    ["⎘", "Output", "the validated, cited result + trace"]
  ];

  // the free, open layer (Apache-2.0) vs the governed/paid layer — the open-core boundary
  var OPEN = [
    ["The spec & schemas", "Component, pipeline, knowledge-corpus and conditional schemas — the JSON contracts every object validates against."],
    ["Seven-primitive grammar", "The composition model below. Any flow is a DAG of these eight node kinds; add a primitive = one entry."],
    ["oh-hub CLI & reference SDK", "Build, validate, simulate and export flows locally — no account, no network required."],
    ["Export emitters", "Emit an audit bundle as SPDX (SBOM), C2PA (signed provenance), JSON-LD, or an EU-AI-Act technical-doc skeleton."],
    ["Build & simulate", "Assemble a flow from the open spec and dry-run it with echo-stubs — measure structure before you connect a model."]
  ];
  var GOVERNED = [
    ["Vetted components", "Components admitted only on measured lift over a bare model, with provenance."],
    ["Live knowledge corpora", "Primary-source feeds with change-data-capture freshness + revocation."],
    ["Build-on-demand & attestation", "We build a flow for your task; auditor-grade signed attestations you can renew."]
  ];

  function navHtml(ctx) {
    var items = [["/pipelines", "Explore"], ["/solutions", "SDG solutions"], ["/app", "Workspace"], ["/pricing", "Pricing"], ["/docs", "Docs"], ["/trust", "Trust"]];
    return items.map(function (p) {
      return '<a data-nav="' + p[0] + '"' + (p[0] === "/docs" ? ' style="color:var(--fg);font-weight:600"' : "") + ">" + ctx.esc(p[1]) + "</a>";
    }).join("");
  }

  function panels(list) {
    return list.map(function (p) {
      return '<div class="pt-panel">' +
        '<div style="font-weight:700;color:var(--fg);margin-bottom:5px">' + p[0] + "</div>" +
        '<div style="font-size:13px;color:var(--fg-muted);line-height:1.5">' + p[1] + "</div></div>";
    }).join("");
  }

  function primLegend() {
    return PRIMS.map(function (p) {
      return '<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid var(--line)">' +
        '<span style="width:26px;height:26px;border-radius:7px;flex:0 0 auto;display:grid;place-items:center;background:var(--panel-2);border:1px solid var(--line);font-size:14px">' + p[0] + "</span>" +
        '<div><span style="font-weight:600;color:var(--fg)">' + p[1] + '</span> <span style="color:var(--fg-muted);font-size:13px">— ' + p[2] + "</span></div></div>";
    }).join("");
  }

  function render(ctx) {
    return '<div class="pt-mkt pt-view">' +
      '<header class="pt-mkt-top">' +
      '<div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + MARK_SVG + ' Open Harness Hub</div>' +
      "<nav>" + navHtml(ctx) + "</nav>" +
      '<span class="pt-spacer"></span>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/signin">Sign in</button>' +
      "</header>" +
      '<div class="pt-mkt-body"><div class="pt-page" style="max-width:920px;margin:0 auto">' +
      '<div class="pt-page-head">' +
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:10px">Open spec · Apache-2.0</div>' +
      '<h1>The protocol is open. Build, export, and self-host without us.</h1>' +
      '<div class="sub">The seven-primitive grammar, the schemas, the CLI/SDK and the export emitters are free and open. You only pay for the governed layer — vetted components and live, cited knowledge. The open spec is the moat’s on-ramp, not a paywall.</div>' +
      "</div>" +

      '<h3 style="font-family:var(--font-display);margin:22px 0 10px">The seven-primitive grammar</h3>' +
      '<div class="pt-panel">' + primLegend() + "</div>" +

      '<h3 style="font-family:var(--font-display);margin:26px 0 10px">Open & free <span class="oh-badge oh-badge--verified" style="vertical-align:middle"><span class="gl">✔</span> Apache-2.0</span></h3>' +
      '<div class="pt-grid-3" style="text-align:left">' + panels(OPEN) + "</div>" +

      '<h3 style="font-family:var(--font-display);margin:26px 0 10px">Governed layer <span class="oh-badge oh-badge--muted" style="vertical-align:middle">subscription</span></h3>' +
      '<div class="pt-grid-3" style="text-align:left">' + panels(GOVERNED) + "</div>" +

      '<div class="oh-state-msg" style="margin-top:26px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:16px 18px;display:block">' +
      '<div style="font-weight:600;color:var(--fg);margin-bottom:4px">Quickstart</div>' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6;margin-bottom:13px">Describe a task → we assemble a flow from the open spec → inspect the DAG → export the bundle (free) or run it on the governed layer. The spec &amp; export never require a subscription.</div>' +
      '<div style="display:flex;gap:9px;flex-wrap:wrap">' +
      '<button class="oh-btn oh-btn--primary" data-nav="/">Describe a task →</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/pricing">Open vs governed →</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/improve">Improve a pipeline →</button>' +
      "</div></div>" +
      "</div></div></div>";
  }

  function onMount(host, ctx) {
    // navigation handled by the global data-nav delegation in app.js
  }

  OHH.register("/docs", render, onMount, { theme: "light" });
})();
