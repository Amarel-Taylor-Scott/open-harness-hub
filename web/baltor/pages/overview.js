/* Baltor — overview / landing (route "/"). Standalone Baltor app; see
   docs/strategy/context-enrichment-service.md. Every link targets a WIRED route (no dead ends). */
(function () {
  "use strict";

  // three serving package tiers — the heart of the product
  var TIERS = [
    ["Source ledger", "synced, versioned, traceable", "files · connectors · hashes · diffs · provenance", "var(--fg-muted)"],
    ["Verified context", "current facts, reconciled scope", "claims · evidence · source trust · refresh policy", "var(--accent)"],
    ["Serving packages", "agent-ready and token-efficient", "text · RAG · graph · hybrid · audit packet", "var(--accent)"]
  ];
  function tierStrip() {
    return '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:4px 0 2px">' + TIERS.map(function (t, i) {
      return '<div class="pt-panel" style="flex:1;min-width:178px;text-align:left;border-left:3px solid ' + t[3] + '">' +
        '<div style="display:flex;align-items:baseline;gap:7px;margin-bottom:4px"><span style="font-weight:800;color:var(--fg)">' + (i + 1) + '</span><span style="font-weight:700;color:var(--fg)">' + t[0] + "</span></div>" +
        '<div style="font-size:12.5px;color:var(--fg);margin-bottom:3px">' + t[1] + "</div>" +
        '<div style="font-size:12px;color:var(--fg-muted);line-height:1.5">' + t[2] + "</div></div>";
    }).join("") + "</div>";
  }

  // "What it does" is now told by the animated Context Engine rails (single source: stages.json,
  // rendered by CE.engineHeroBody from pages/engine-hero.js) — no re-typed stage copy here.

  var SURFACES = [
    ["MCP / API", "Live-serve into Claude Code, Codex, Cursor, or internal agents", "The runtime pulls the right verified context at the right detail level."],
    ["RAG records", "Chunks, metadata, citations, freshness", "Drop into vector, keyword, or hybrid retrieval systems."],
    ["Graph package", "Entities, claims, source links, procedures", "Use source-aware graph retrieval and impact propagation."],
    ["Audit packet", "History, worker traces, adoption decisions", "Show what changed, why it was adopted, and which facts were held back."]
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
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:10px">Context control · for the agent era</div>' +
      '<h1>Verified context for the agents you already run.</h1>' +
      '<div class="sub">Load enterprise context, keep every source synced and versioned, verify changing facts, reconcile updates, and serve trusted context packages into any agent, RAG, or workflow system.</div>' +
      '<div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:16px">' +
      '<a class="oh-btn oh-btn--primary" href="/admin-demo/">Open context control demo →</a>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/trust">How verification works →</button>' +
      "</div></div>" +

      // the signature animated Context Engine — six macro stages under one verification rail (single source: stages.json)
      '<div style="margin:18px 0 4px">' + (CE.engineHeroBody ? CE.engineHeroBody() : "") + "</div>" +
      '<div style="text-align:center;margin:2px 0 10px"><button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/engine">Open the full Context Engine →</button></div>' +

      '<h3 style="font-family:var(--font-display);margin:24px 0 8px">From source ledger to serving package</h3>' +
      tierStrip() +

      '<h3 style="font-family:var(--font-display);margin:26px 0 8px">How your agent consumes it</h3>' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6;margin-bottom:10px">The output is not a chat answer. It is a governed context package rendered into whichever shape your agent or retrieval stack already uses.</div>' +
      '<div class="pt-grid-3">' + surfaceCards() + "</div>" +

      '<div class="oh-state-msg" style="margin-top:26px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:16px 18px;display:block">' +
      '<div style="font-weight:600;color:var(--fg);margin-bottom:4px">One rule underneath it all</div>' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6">Facts do not become served context just because one source or one model says so. Baltor keeps lineage, source counts, trust checks, archive state, and follow-up tasks so partial evidence can mature into verified context.</div>' +
      '<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap"><button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/trust">See the trust policy →</button><a class="oh-btn oh-btn--ghost oh-btn--sm" href="https://openharnesshub.com">Build governed workflows in OpenHubForAI →</a></div>' +
      "</div>" +
      "</div></div></div>";
  }

  CE.register("/", render);
})();
