/* Context Enrichment — pricing (route "/pricing"). The tiers fall straight out of the architecture's
   freezable-vs-recurring boundary (docs/strategy/context-enrichment-service.md). */
(function () {
  "use strict";

  // [name, price model, tagline, bullets[], tag, accent?]
  var TIERS = [
    ["Critique", "Free", "See what you'd save before you pay",
      ["Scan a source, get the token-efficiency + fidelity delta you'd get at each tier", "No card, no integration", "The honest funnel — proof before spend"], "free", false],
    ["Enrichment", "Metered", "Pay per source scanned · per token compressed / embedded",
      ["Raw → compressed → hyper-efficient, on demand", "Tokens-in → tokens-out + fidelity, measured", "Funds the foundry; scales to zero"], "metered", true],
    ["Hosting", "Storage-priced", "Freezable — yours to keep",
      ["Raw + compressed tiers hosted, or downloaded", "Run local / air-gapped — a static download is yours forever", "One-time or per-GB, no lock-in"], "freezable", false],
    ["Fresh-serve", "Recurring", "Hyper-efficient, served live + kept current",
      ["MCP / llms.txt / skill / CLAUDE.md surfaces", "CDC freshness + revocation against a live corpus", "Recurring — a static download can't stay current"], "recurring", true]
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
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:10px">Consumption-priced</div>' +
      '<h1>Pay for what you keep live.</h1>' +
      '<div class="sub">Raw and compressed are freezable — download them, they’re yours. The hyper-efficient tier, served live and kept fresh against a changing corpus, is the only recurring line — because a static download can’t stay current. The metered middle funds the refinery.</div>' +
      "</div>" +
      '<div class="pt-grid-2" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px">' + cards() + "</div>" +
      '<div class="oh-state-msg" style="margin-top:24px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:16px 18px;display:block">' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6">The freshness loop is the moat: governed, cited, change-data-capture-fresh context that a one-time export can’t replicate. Start free with a critique →</div>' +
      '<div style="margin-top:12px"><button class="oh-btn oh-btn--primary oh-btn--sm" data-nav="/">Back to overview</button> <button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/trust">The fidelity guarantee →</button></div>' +
      "</div>" +
      "</div></div></div>";
  }

  CE.register("/pricing", render);
})();
