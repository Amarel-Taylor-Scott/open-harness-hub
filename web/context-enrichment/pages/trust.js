/* Context Enrichment — trust / the fidelity guarantee (route "/trust"). The moat: measured fidelity
   per tier (docs/strategy/context-enrichment-service.md), the same engine as Open Harness Hub's lift gate. */
(function () {
  "use strict";

  var PILLARS = [
    ["Measured fidelity per tier", "Every artifact ships a published quality delta — raw → compressed → hyper-efficient — scored by a SEPARATE evaluator. Never self-graded. “Here’s the proven quality retained,” not “hope it still reasons.”"],
    ["Every tier traces to raw", "Compressed and hyper-efficient are governed derivations with full lineage back to the canonical source. The dense tier is never an unsourced claim."],
    ["Fresh, not frozen-stale", "Live-served corpora carry change-data-capture freshness + revocation. When the source changes, the served context changes — a static download can’t."],
    ["Cited + signed", "Provenance and citations travel with the content; hosted artifacts are signed. Self-hostable and air-gappable for regulated buyers."],
    ["The honest breakeven", "Compress too hard and you destroy reasoning — so we measure where compression pays and report it. LLMLingua/Tree-sitter gains only count when the length/ratio/hardware window holds."],
    ["Same moat as the lift gate", "This is the exact measurement engine behind Open Harness Hub’s “does it beat a bare model?” bar — pointed at “did this tier preserve enough?”"]
  ];

  function pillars() {
    return PILLARS.map(function (p) {
      return '<div class="pt-panel" style="text-align:left">' +
        '<div style="font-weight:700;color:var(--fg);margin-bottom:5px">' + p[0] + "</div>" +
        '<div style="font-size:13px;color:var(--fg-muted);line-height:1.55">' + p[1] + "</div></div>";
    }).join("");
  }

  function render(ctx) {
    return '<div class="pt-mkt pt-view">' + ctx.header("/trust") +
      '<div class="pt-mkt-body"><div class="pt-page" style="max-width:920px;margin:0 auto">' +
      '<div class="pt-page-head">' +
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:10px">The guarantee</div>' +
      '<h1>Measured fidelity, not a compression gamble.</h1>' +
      '<div class="sub">Anyone can run a compressor. The service is the <strong>proof</strong>: a measured quality delta at every tier, full provenance, and a freshness contract — so you can trust the dense context your agent runs on.</div>' +
      "</div>" +
      '<div class="pt-grid-3">' + pillars() + "</div>" +
      '<div class="oh-state-msg" style="margin-top:24px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:16px 18px;display:block">' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6">“We compressed your context, and here’s the proven quality delta at each tier” is a service. “We compressed your context, hope it still reasons” is a gamble. The measurement engine is the difference.</div>' +
      '<div style="margin-top:12px"><button class="oh-btn oh-btn--primary oh-btn--sm" data-nav="/pricing">See pricing →</button> <button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/">Back to overview</button></div>' +
      "</div>" +
      "</div></div></div>";
  }

  CE.register("/trust", render);
})();
