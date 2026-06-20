/* Open Harness Hub — Why us / the wedge (/why)
   The verified-context service is the BUSINESS; this page makes the wedge explicit:
   most platforms keep your docs CURRENT — we continuously verify they are CORRECT against
   external authoritative sources, and hunt for contradictions before an agent cites them.
   Honest head-to-head (us vs Contextual vs raw RAG vs DIY) — we do NOT claim Contextual lacks
   a builder / actions / governance; the seam is corpus-correctness, not feature coverage.
   No React/JSX/build. Registers /why (marketing, light). Mirrors docs.js shell + ported CSS. */
(function () {
  "use strict";

  var MARK_SVG = '<span class="oh-mark" aria-hidden="true">' +
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />' +
    '<path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" />' +
    '</svg></span>';

  // Head-to-head columns. col[0]=label, col[1]=sub, col[2]=honest one-liner, rec=recommended col.
  // HONEST contract: Contextual ships a builder, actions and governance — the seam is that they
  // ground the answer in YOUR corpus even when the corpus is wrong; we verify the corpus itself.
  var COLS = [
    {
      key: "ohh", rec: true,
      label: "Open Harness Hub",
      sub: "verified-context service",
      line: "We continuously verify your corpus is correct against external authoritative sources, and hunt for contradictions before your agent cites them."
    },
    {
      key: "contextual",
      label: "Contextual / grounded RAG",
      sub: "answer grounded in your corpus",
      line: "They ground the answer in your corpus — even if the corpus is wrong. We verify the corpus."
    },
    {
      key: "rag",
      label: "Raw RAG (DIY embeddings)",
      sub: "retrieve-then-generate",
      line: "Retrieval without verification is confident wrongness — a fluent answer cited to a stale or contradicted document."
    },
    {
      key: "diy",
      label: "Hand-maintained corpus",
      sub: "your team, spreadsheets, cron",
      line: "Stop hand-maintaining regulatory corpora. Subscribe to verified, always-current truth instead of re-checking sources by hand."
    }
  ];

  // Comparison matrix. Each row: label + cell per COLS key.
  // ✓ = does this · ~ = partial / on you · ✗ = no. Honest about Contextual having a builder etc.
  var MATRIX = [
    ["Build / assemble pipelines", { ohh: "✓ open spec + builder", contextual: "✓ builder + actions", rag: "~ you wire it", diy: "~ you wire it" }],
    ["Retrieval grounded in your docs", { ohh: "✓ cited, exact-id + dense", contextual: "✓ grounded answers", rag: "✓ similarity retrieval", diy: "~ if you build it" }],
    ["Governance / provenance on the flow", { ohh: "✓ signed, C2PA / EU-AI-Act", contextual: "✓ governance features", rag: "✗ none by default", diy: "~ you assemble it" }],
    ["Verifies the corpus is CORRECT vs external sources", { ohh: "✓ continuous corroboration", contextual: "✗ grounds in your corpus as-is", rag: "✗ retrieves whatever is indexed", diy: "~ manual review only" }],
    ["Hunts for contradictions before a citation", { ohh: "✓ multi-source corroborate", contextual: "✗ not the job", rag: "✗ none", diy: "✗ none" }],
    ["Freshness + revocation (CDC) on facts", { ohh: "✓ diff-tracked + revoked", contextual: "~ you keep docs current", rag: "✗ snapshot decays", diy: "✗ cron + hope" }],
    ["You stop hand-maintaining the corpus", { ohh: "✓ subscribe to verified truth", contextual: "~ you still own correctness", rag: "✗ you own everything", diy: "✗ it is the manual job" }]
  ];

  // The provenance + verification + freshness bundle — the three legs of the moat.
  var BUNDLE = [
    {
      glyph: "🔏", tone: "--verified",
      title: "Provenance",
      body: "Every fact is dated, sourced and cryptographically signed. The attestation an auditor accepts — C2PA · EU-AI-Act — and it renews as the facts do.",
      nav: "/attest", cta: "See certified export →"
    },
    {
      glyph: "🛡", tone: "--accent",
      title: "Verification",
      body: "We corroborate each fact across multiple authoritative sources and run an integrity check that flags contradictions before your agent ever cites them. Retrieval without verification is confident wrongness.",
      nav: "/compare", cta: "See the lift →"
    },
    {
      glyph: "↻", tone: "--success",
      title: "Freshness",
      body: "Primary government sources scraped on an SLA, diff-tracked by change-data-capture, with revocation that pulls dead facts out of your flows. Export the flow, you lose the feed.",
      nav: "/freshness", cta: "See the live feed →"
    }
  ];

  function navHtml(ctx) {
    var items = [["/pipelines", "Explore"], ["/why", "Why us"], ["/app", "Workspace"], ["/pricing", "Pricing"], ["/docs", "Docs"], ["/trust", "Trust"]];
    return items.map(function (p) {
      return '<a data-nav="' + p[0] + '"' + (p[0] === "/why" ? ' style="color:var(--fg);font-weight:600"' : "") + ">" + ctx.esc(p[1]) + "</a>";
    }).join("");
  }

  function cellMark(v) {
    var g = v.charAt(0);
    var tone = g === "✓" ? "--success" : (g === "~" ? "--warning" : "--danger");
    return '<span style="color:var(' + tone + ');font-weight:700;margin-right:5px">' + g + "</span>";
  }

  function headToHead(ctx) {
    var head = '<thead><tr><th class="rowlbl"></th>' + COLS.map(function (c) {
      var recCls = c.rec ? " col-rec" : "";
      return '<th class="' + recCls.trim() + '">' + ctx.esc(c.label) +
        '<span class="tier-cost">' + ctx.esc(c.sub) + "</span>" +
        (c.rec ? '<span class="recflag">★ verified-context</span>' : "") + "</th>";
    }).join("") + "</tr></thead>";

    // honest one-liner row, per column
    var lineRow = '<tr><td class="rowlbl">In one honest line</td>' + COLS.map(function (c) {
      var recCls = c.rec ? ' class="col-rec"' : "";
      return "<td" + recCls + ' style="font-size:12px;color:' + (c.rec ? "var(--fg)" : "var(--fg-muted)") + ';line-height:1.5">' + ctx.esc(c.line) + "</td>";
    }).join("") + "</tr>";

    var rows = MATRIX.map(function (m) {
      var label = m[0], cells = m[1];
      return '<tr><td class="rowlbl">' + ctx.esc(label) + "</td>" + COLS.map(function (c) {
        var v = cells[c.key] || "—";
        var recCls = c.rec ? ' class="col-rec"' : "";
        return "<td" + recCls + ">" + cellMark(v) + ctx.esc(v.slice(1).trim()) + "</td>";
      }).join("") + "</tr>";
    }).join("");

    return '<table class="oh-cmp-table" style="width:100%;margin:0">' + head + "<tbody>" + lineRow + rows + "</tbody></table>";
  }

  function bundleCards(ctx) {
    return BUNDLE.map(function (b) {
      return '<div class="pt-panel" style="flex:1;min-width:240px;border-color:color-mix(in srgb, var(' + b.tone + ') 32%, var(--line))">' +
        '<div style="display:flex;align-items:center;gap:9px;margin-bottom:8px">' +
        '<span style="width:30px;height:30px;border-radius:8px;flex:0 0 auto;display:grid;place-items:center;background:color-mix(in srgb, var(' + b.tone + ') 12%, transparent);color:var(' + b.tone + ');font-size:15px">' + b.glyph + "</span>" +
        '<span style="font-family:var(--font-display);font-weight:700;font-size:16px;color:var(--fg)">' + ctx.esc(b.title) + "</span></div>" +
        '<div style="font-size:13px;color:var(--fg-muted);line-height:1.55;margin-bottom:12px">' + ctx.esc(b.body) + "</div>" +
        '<a style="color:var(--accent);cursor:pointer;font-weight:600;font-size:13px" data-nav="' + b.nav + '">' + ctx.esc(b.cta) + "</a></div>";
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
      '<div class="pt-mkt-body"><div class="pt-page" style="max-width:1040px;margin:0 auto">' +

      // --- lead with the improved WEDGE ---
      '<div class="pt-page-head">' +
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--verified);margin-bottom:10px">The verified-context service</div>' +
      "<h1>Most platforms keep your docs current. We keep them correct.</h1>" +
      '<div class="sub">Most platforms keep your docs <b>current</b>. We continuously verify they are <b>correct</b> against external authoritative sources, and hunt for contradictions before your agent cites them. Current is not the same as true — and a confidently-cited wrong fact is the failure that matters.</div>' +
      "</div>" +

      // --- head-to-head ---
      '<h3 style="font-family:var(--font-display);margin:24px 0 4px">Where we sit — honestly</h3>' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.55;margin-bottom:14px;max-width:760px">Grounded-RAG platforms ship builders, actions and governance — that is not the seam. The seam is corpus <b>correctness</b>: they ground the answer in your corpus as-is, while we verify the corpus underneath it.</div>' +
      headToHead(ctx) +
      '<div style="font-size:11px;color:var(--fg-faint);margin-top:9px;font-family:var(--font-mono)">✓ does this · ~ partial / on you · ✗ not its job. Contextual ships a capable builder, actions and governance; the distinction drawn here is corpus verification, not feature coverage.</div>' +

      // --- the bundle ---
      '<h3 style="font-family:var(--font-display);margin:30px 0 4px">What you actually subscribe to</h3>' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.55;margin-bottom:14px;max-width:760px">Three legs, one governed object: provenance you can attest, verification that hunts contradictions, and freshness that revokes dead facts. Retrieval without verification is confident wrongness — this is the part raw RAG and a hand-maintained corpus leave to you.</div>' +
      '<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:stretch">' + bundleCards(ctx) + "</div>" +

      // --- closing CTA ---
      '<div class="oh-state-msg" style="margin-top:28px;background:color-mix(in srgb,var(--verified) 7%,transparent);border:1px solid color-mix(in srgb, var(--verified) 30%, var(--line));border-radius:var(--r-md);padding:16px 18px;display:block">' +
      '<div style="font-weight:600;color:var(--fg);margin-bottom:4px">Stop hand-maintaining the corpus.</div>' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6;margin-bottom:13px">Subscribe to verified, always-current truth instead of re-checking regulatory sources by hand. The open spec and export are free; the continuously-verified, signed, diff-tracked layer is the subscription.</div>' +
      '<div style="display:flex;gap:9px;flex-wrap:wrap">' +
      '<button class="oh-btn oh-btn--primary" data-nav="/compare">See the lift →</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/freshness">See the live feed →</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/pricing">Open vs governed →</button>' +
      "</div></div>" +
      "</div></div></div>";
  }

  function onMount(host, ctx) {
    // navigation handled by the global data-nav delegation in app.js
  }

  OHH.register("/why", render, onMount, { theme: "light" });
})();
