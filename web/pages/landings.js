/* Open Harness Hub — Audience landing pages (/for/:who)
   Faithful port of proto-landings.jsx → PUseCase.
   No React, no JSX, no build. Registers: /for/:who (marketing, light). */
(function () {
  "use strict";

  var USECASES = {
    governments: {
      tag: "For governments & standards bodies",
      hl: "Publish authoritative facts the world can cite.",
      sub: "Sign, date and version your regulations, standards and datasets so any AI pipeline cites them with provenance — and you control freshness and revocation.",
      cta: "Publish facts",
      to: "/publish",
      points: [
        ["🛡 Signed & dated", "Every fact carries C2PA provenance traceable to you."],
        ["⟳ You control freshness", "Push amendments and revocations; citing flows update automatically."],
        ["🌐 Cited everywhere", "Become the verified source across the ecosystem."]
      ]
    },
    builders: {
      tag: "For pipeline builders",
      hl: "Tired of facts changing faster than your LLM?",
      sub: "Stop baking stale knowledge into prompts. Plug governed, live corpora into your pipelines over MCP — fresh, cited and swappable without re-prompting.",
      cta: "Improve a pipeline",
      to: "/improve",
      points: [
        ["⟳ Always-fresh knowledge", "Change-data-capture keeps corpora current; your flows don’t rot."],
        ["⇄ MCP-native", "Your agents pull governed components locally; your data stays put."],
        ["▲ Measured lift", "Prove each flow beats a bare model — and watch for decay."]
      ]
    },
    lawyers: {
      tag: "For legal teams",
      hl: "Answers with citations a partner would sign off on.",
      sub: "Every claim resolves to a sourced clause across jurisdictions and languages — with an attestation you can attach to the file.",
      cta: "See certified export",
      to: "/attest",
      points: [
        ["✔ Sourced claims", "A deterministic citation gate — no uncited assertions."],
        ["📄 Audit-ready", "A signed, dated attestation valid through a set date."],
        ["🌐 13+ languages", "Cross-jurisdiction, cross-language coverage."]
      ]
    },
    regulators: {
      tag: "For regulators & auditors",
      hl: "Verify compliance with a complete auditable trail.",
      sub: "Replayable runs, provenance graphs and immutable audit logs — see exactly what was cited, by whom, and when.",
      cta: "Open the trust center",
      to: "/trust",
      points: [
        ["▤ Immutable audit", "Every governance event, exportable."],
        ["🔗 Provenance graph", "Source → signature → citation lineage."],
        ["⊘ Revocation", "Withdrawn facts are pulled from flows within SLA."]
      ]
    }
  };

  var MARK_SVG = '<span class="oh-mark" aria-hidden="true">' +
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />' +
    '<path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" />' +
    '</svg></span>';

  function renderNotFound(ctx) {
    return '<div class="pt-mkt pt-view">' +
      '<header class="pt-mkt-top">' +
      '<div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + MARK_SVG + ' OpenHarnessHub</div>' +
      '<span class="pt-spacer"></span>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/signin">Sign in</button>' +
      '</header>' +
      '<div class="pt-mkt-body">' +
      '<section class="pt-hero">' +
      '<h1>Audience not found</h1>' +
      '<p class="sub">That audience page doesn’t exist. Try one of the links below.</p>' +
      '<div style="display:flex;gap:10px">' +
      '<button class="oh-btn oh-btn--primary" data-nav="/for/builders">For builders</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/">Describe a task</button>' +
      '</div>' +
      '</section>' +
      '</div>' +
      '</div>';
  }

  function render(ctx) {
    var who = ctx.params && ctx.params.who;
    var u = who && USECASES[who];
    if (!u) return renderNotFound(ctx);

    var navLinks = [
      ["governments", "Governments"],
      ["builders", "Builders"],
      ["lawyers", "Lawyers"],
      ["regulators", "Regulators"]
    ];

    var navHtml = "";
    navLinks.forEach(function (pair) {
      navHtml += '<a data-nav="/for/' + ctx.esc(pair[0]) + '" style="' +
        (pair[0] === who ? "color:var(--fg);font-weight:600;" : "") +
        '">' + ctx.esc(pair[1]) + "</a>";
    });

    var pointsHtml = "";
    u.points.forEach(function (pt) {
      pointsHtml += '<div class="pt-panel">' +
        '<div style="font-weight:700;color:var(--fg);margin-bottom:5px">' + ctx.esc(pt[0]) + "</div>" +
        '<div style="font-size:13px;color:var(--fg-muted);line-height:1.5">' + ctx.esc(pt[1]) + "</div>" +
        "</div>";
    });

    return '<div class="pt-mkt pt-view">' +
      '<header class="pt-mkt-top">' +
      '<div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + MARK_SVG + " OpenHarnessHub</div>" +
      "<nav>" + navHtml + "</nav>" +
      '<span class="pt-spacer"></span>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/signin">Sign in</button>' +
      "</header>" +
      '<div class="pt-mkt-body">' +
      '<section class="pt-hero">' +
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:14px">' +
      ctx.esc(u.tag) +
      "</div>" +
      "<h1>" + ctx.esc(u.hl) + "</h1>" +
      '<p class="sub">' + ctx.esc(u.sub) + "</p>" +
      '<div style="display:flex;gap:10px">' +
      '<button class="oh-btn oh-btn--primary" data-nav="' + ctx.esc(u.to) + '">' + ctx.esc(u.cta) + " →</button>" +
      '<button class="oh-btn oh-btn--ghost" data-nav="/">Describe a task</button>' +
      "</div>" +
      '<div class="pt-grid-3" style="max-width:820px;width:100%;margin-top:40px;text-align:left">' +
      pointsHtml +
      "</div>" +
      "</section>" +
      "</div>" +
      "</div>";
  }

  function onMount(host, ctx) {
    // Navigation is handled by the global data-nav delegation in app.js.
    // No additional interactivity needed for this static marketing page.
  }

  OHH.register("/for/:who", render, onMount, { theme: "light" });
})();
