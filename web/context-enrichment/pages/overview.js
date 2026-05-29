/* Context Enrichment — overview / landing (route "/"). Standalone CEaaS app; see
   docs/strategy/context-enrichment-service.md. Every link targets a WIRED route (no dead ends). */
(function () {
  "use strict";

  // three hosted content tiers — the heart of the product
  var TIERS = [
    ["Raw", "full fidelity, governed + cited", "audit · exact quote · ground truth", "var(--fg-muted)"],
    ["Compressed", "token-reduced, lift preserved", "the default working form (LLMLingua · Tree-sitter)", "var(--accent)"],
    ["Hyper-efficient", "maximally token-dense", "hot paths (distilled memory + cached prefixes)", "var(--accent)"]
  ];
  function tierStrip() {
    return '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:4px 0 2px">' + TIERS.map(function (t, i) {
      return '<div class="pt-panel" style="flex:1;min-width:178px;text-align:left;border-left:3px solid ' + t[3] + '">' +
        '<div style="display:flex;align-items:baseline;gap:7px;margin-bottom:4px"><span style="font-weight:800;color:var(--fg)">' + (i + 1) + '</span><span style="font-weight:700;color:var(--fg)">' + t[0] + "</span></div>" +
        '<div style="font-size:12.5px;color:var(--fg);margin-bottom:3px">' + t[1] + "</div>" +
        '<div style="font-size:12px;color:var(--fg-muted);line-height:1.5">' + t[2] + "</div></div>";
    }).join("") + "</div>";
  }

  var CAPS = [
    ["Compress", "Fewer tokens, lift retained", "Raw → compressed → hyper-efficient, with tokens-in → tokens-out and lift-retained measured by a separate evaluator. Honest breakeven, never blind compression."],
    ["Host & download", "Pull a tier, or take it with you", "Every corpus hosted in all three tiers. Pull the tier your budget wants — or download to run local / air-gapped."],
    ["Serve to agents", "Drop straight into Claude Code", "MCP endpoints hand governed corpora + tools to any open agent loop — token-dense, cited context on demand, not a giant stale dump."],
    ["Unique corpora", "Primary-source, cited, fresh", "The governed knowledge the base model lacks — change-data-capture fresh, with provenance and revocation."],
    ["Govern", "Every tier traces to raw", "Provenance + lineage from raw → compressed → hyper-efficient; signed artifacts. The dense tier is a governed derivation, not a lossy guess."],
    ["Meter", "Pay per use", "Per query · per GB hosted · per refresh — the consumption motion, applied to the governed content layer."]
  ];
  function capCards() {
    return CAPS.map(function (c) {
      return '<div class="pt-panel" style="text-align:left">' +
        '<div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);margin-bottom:6px">' + c[0] + "</div>" +
        '<div style="font-weight:700;color:var(--fg);margin-bottom:5px">' + c[1] + "</div>" +
        '<div style="font-size:13px;color:var(--fg-muted);line-height:1.55">' + c[2] + "</div></div>";
    }).join("");
  }

  var SURFACES = [
    ["MCP server", "Live-serve to Claude Code / Cursor", "The default — MCP is the convergence point. Tier-negotiated, CDC-fresh, metered."],
    ["Packed file · llms.txt", "Download or paste, no integration", "Works with any subscription. The freezable surface — take the tier and go."],
    ["Skill / plugin", "Installable corpus + tools unit", "Distribute a governed corpus and its tools as one installable Claude Code skill."],
    ["CLAUDE.md fragment", "Always-loaded, near-zero token", "The distilled tier for stable knowledge that must survive compaction — conventions, glossary."]
  ];
  function surfaceCards() {
    return SURFACES.map(function (s, i) {
      return '<div class="pt-panel" style="text-align:left">' +
        '<div style="display:flex;align-items:baseline;gap:7px;margin-bottom:4px"><span style="width:18px;height:18px;border-radius:5px;flex:0 0 auto;display:grid;place-items:center;background:var(--accent-weak);color:var(--accent);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));font-size:10px;font-weight:700">' + (i + 1) + '</span><span style="font-weight:700;color:var(--fg);font-size:13.5px">' + s[0] + "</span></div>" +
        '<div style="font-size:12.5px;color:var(--fg);margin-bottom:3px">' + s[1] + "</div>" +
        '<div style="font-size:12px;color:var(--fg-muted);line-height:1.5">' + s[2] + "</div></div>";
    }).join("");
  }

  function render(ctx) {
    return '<div class="pt-mkt pt-view">' + ctx.header("/") +
      '<div class="pt-mkt-body"><div class="pt-page" style="max-width:980px;margin:0 auto">' +

      '<div class="pt-page-head">' +
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:10px">Content enrichment · as a service</div>' +
      '<h1>Token-efficient, governed content for any agent.</h1>' +
      '<div class="sub">Compress your content and our unique governed corpora, host it raw · compressed · hyper-efficient, and serve it — with tools — straight into open-ended agent loops like Claude Code. Your agent pulls token-dense, cited context on demand instead of carrying a giant stale dump. Priced per use.</div>' +
      '<div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:16px">' +
      '<button class="oh-btn oh-btn--primary" data-nav="/pricing">See pricing →</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/trust">How fidelity is guaranteed →</button>' +
      "</div></div>" +

      '<h3 style="font-family:var(--font-display);margin:24px 0 8px">Three hosted tiers — pull one, or download it</h3>' +
      tierStrip() +

      '<h3 style="font-family:var(--font-display);margin:26px 0 10px">What it does</h3>' +
      '<div class="pt-grid-3">' + capCards() + "</div>" +

      '<h3 style="font-family:var(--font-display);margin:26px 0 8px">How your agent consumes it</h3>' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6;margin-bottom:10px">The output isn’t an answer — it’s your governed corpus rendered into whichever shape your agent ingests, at whichever tier you pay for.</div>' +
      '<div class="pt-grid-3">' + surfaceCards() + "</div>" +

      '<div class="oh-state-msg" style="margin-top:26px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:16px 18px;display:block">' +
      '<div style="font-weight:600;color:var(--fg);margin-bottom:4px">One guarantee underneath it all</div>' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6">Every tier ships a <strong>measured fidelity delta</strong> — “we compressed your context, and here’s the proven quality retained,” scored by a separate evaluator. That is what makes this a service, not a gamble.</div>' +
      '<div style="margin-top:12px"><button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/trust">See the fidelity guarantee →</button></div>' +
      "</div>" +
      "</div></div></div>";
  }

  CE.register("/", render);
})();
