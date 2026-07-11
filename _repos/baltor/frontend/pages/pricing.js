/* Baltor — pricing (route "/pricing"). Pricing follows the context-control loop:
   source sync, verification/reconciliation, serving packages, and monitored refresh. */
(function () {
  "use strict";

  // [name, price model, tagline, bullets[], tag, accent?]
  var TIERS = [
    ["Assessment", "Free", "See the shape of your context before you pay",
      ["Upload or connect a sample source", "Find changing facts, weak evidence, and source age", "Preview the serving packages and audit trail"], "free", false],
    ["Processing", "Metered", "Pay for source sync, extraction, graphing, and verification",
      ["Chunking, OCR routing, entities, claims, nodes, and edges", "Multi-source evidence checks and source trust scoring", "Cheap deterministic workers first; model-backed work only when useful"], "metered", true],
    ["Serving packages", "Storage-priced", "Keep text, RAG, graph, hybrid, and audit artifacts",
      ["Download or host context packages", "Run local, air-gapped, or inside your existing RAG stack", "Current fact plus optional provenance history"], "freezable", false],
    ["Monitored context", "Recurring", "Keep served context current as sources change",
      ["Connector sync, source diffs, refresh queues, and archive capture", "Second-source searches for under-supported facts", "Recurring because static exports cannot stay current"], "recurring", true]
  ];

  function tagChip(tag) {
    var map = {
      free: ["Free", "var(--fg-muted)"], metered: ["Metered · per use", "var(--accent)"],
      freezable: ["Freezable · one-time", "var(--fg-muted)"], recurring: ["Recurring · the moat", "var(--accent)"]
    };
    var m = map[tag] || ["", "var(--fg-muted)"];
    return '<span style="font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:' + m[1] + '">' + m[0] + "</span>";
  }

  function cards() {
    return TIERS.map(function (t) {
      var bullets = t[3].map(function (b) {
        return '<li style="font-size:12.5px;color:var(--fg-muted);line-height:1.5;margin:5px 0;padding-left:15px;position:relative"><span style="position:absolute;left:0;color:var(--accent)">›</span>' + b + "</li>";
      }).join("");
      return '<div class="pt-panel" style="text-align:left;display:flex;flex-direction:column;gap:7px' + (t[5] ? ';border:1px solid color-mix(in srgb, var(--accent) 35%, var(--line))' : "") + '">' +
        tagChip(t[4]) +
        '<div style="font-family:var(--font-display);font-size:19px;font-weight:700;color:var(--fg)">' + t[0] + "</div>" +
        '<div style="font-size:13px;font-weight:600;color:var(--accent)">' + t[1] + "</div>" +
        '<div style="font-size:12.5px;color:var(--fg);margin-bottom:2px">' + t[2] + "</div>" +
        '<ul style="list-style:none;margin:0;padding:0">' + bullets + "</ul></div>";
    }).join("");
  }

  function render(ctx) {
    return '<div class="pt-mkt pt-view">' + ctx.header("/pricing") +
      '<div class="pt-mkt-body"><div class="pt-page" style="max-width:980px;margin:0 auto">' +
      '<div class="pt-page-head">' +
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:10px">Usage-priced context control</div>' +
      '<h1>Pay for processing, packages, and monitoring.</h1>' +
      '<div class="sub">One-time packages are portable. Recurring value comes from keeping sources synced, facts verified, and served context current as the world changes.</div>' +
      "</div>" +
      '<div class="pt-grid-2" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px">' + cards() + "</div>" +
      '<div class="oh-state-msg" style="margin-top:24px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:16px 18px;display:block">' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6">The recurring loop is the moat: source sync, fact-state lineage, refresh queues, archive capture, and adoption decisions that a one-time export cannot maintain.</div>' +
      '<div style="margin-top:12px"><button class="oh-btn oh-btn--primary oh-btn--sm" data-nav="/">Back to overview</button> <button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/trust">The trust policy →</button></div>' +
      "</div>" +
      "</div></div></div>";
  }

  CE.register("/pricing", render);
})();
