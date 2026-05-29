/* Open Harness Hub — BYO module: Private Registry (/registry) + Connect/MCP (/connect)
   Ported faithfully from proto-byo.jsx. Vanilla ES5-style, no build, no imports.
   Registers via window.OHH.register(). Reads shared data from ctx.data / ctx.PRIMS. */
(function () {
  "use strict";

  /* ---------------- /registry — PRegistry ---------------- */

  var PRIV = [
    { k: "knowledge", name: "Acme supplier master",     id: "knowledge-corpus/acme-suppliers",   tag: "priv",   meta: "⛁ 14k rows · private pgvector · local-only" },
    { k: "knowledge", name: "Internal ESG policy",      id: "knowledge-corpus/acme-esg-policy",  tag: "priv",   meta: "⛁ SharePoint · ↻ synced nightly" },
    { k: "action",    name: "Deal-memo retriever",       id: "processor/deal-memo",               tag: "priv",   meta: "⚡ processor · runs in your VPC" },
    { k: "conditional", name: "Acme risk thresholds",   id: "conditional/acme-tiers",            tag: "priv",   meta: "◈ rule-pack · overrides the public gate" },
    { k: "action",    name: "Cite-first ESG counsel",   id: "harness/esg-cite-first·acme",  tag: "fork",   meta: "⚡ forked-from harness/esg-cite-first@1.3.0" },
    { k: "knowledge", name: "Procurement runbook",       id: "knowledge-corpus/acme-runbook",     tag: "ingest", meta: "⛁ managed-ingested · gate-passed" },
  ];

  function privBadge(tag, esc) {
    if (tag === "priv")   return '<span class="pt-priv-badge priv">🔒 private</span>';
    if (tag === "fork")   return '<span class="pt-priv-badge fork">⑂ forked</span>';
    /* ingest */          return '<span class="pt-priv-badge ingest">⚙ ingested</span>';
  }

  function renderRegistry(ctx) {
    var esc = ctx.esc;
    var PRIMS = ctx.PRIMS;

    var cards = "";
    for (var i = 0; i < PRIV.length; i++) {
      var c = PRIV[i];
      var p = PRIMS[c.k] || PRIMS.action;
      cards +=
        '<div class="oh-comp-card" style="--p-action:var(' + esc(p.v) + ');cursor:pointer" data-priv-card>' +
          '<div class="oh-cc-top">' +
            '<span class="oh-cc-prim" style="color:var(' + esc(p.v) + ')">' +
              esc(p.glyph) + " " + esc(p.label.split(" ")[0].toUpperCase()) +
            "</span>" +
            '<span class="spacer"></span>' +
            privBadge(c.tag, esc) +
          "</div>" +
          '<h4 class="oh-cc-name">' + esc(c.name) + "</h4>" +
          '<div class="oh-cc-id mono">' + esc(c.id) + "</div>" +
          '<div class="oh-cc-divider"></div>' +
          '<div class="oh-node-facts" style="font-family:var(--font-mono);font-size:10.5px;color:var(--fg-muted)">' +
            esc(c.meta) +
          "</div>" +
        "</div>";
    }

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          "<h1>Private registry</h1>" +
          '<div class="sub">Your proprietary components &amp; context — your IP, scoped to your workspace. Gaps are filled by governed components from the catalog.</div>' +
        "</div>" +

        '<div class="pt-reg-cover">' +
          '<div class="seg"><span class="v gov">12</span><span class="k">your private components</span></div>' +
          '<span class="plus">+</span>' +
          '<div class="seg"><span class="v">34</span><span class="k">governed, filling gaps</span></div>' +
          '<span class="covbar"><span class="priv" style="width:26%"></span><span class="pub" style="width:74%"></span></span>' +
          '<span style="font-size:11.5px;color:var(--fg-muted)">26% your IP · 74% from OpenHarnessHub</span>' +
        "</div>" +

        '<div class="pt-toolbar">' +
          '<button class="oh-btn oh-btn--primary oh-btn--sm" data-act="new-comp">+ New component</button>' +
          '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/connect">Connect a source</button>' +
          '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/improve">Import a pipeline</button>' +
          '<span class="pt-spacer"></span>' +
          '<span class="oh-badge mono">visibility · workspace</span>' +
        "</div>" +

        '<div class="pt-cards-grid">' + cards + "</div>" +

        '<div class="oh-state-msg" style="margin-top:16px;background:color-mix(in srgb, var(--verified) 7%, transparent);border:1px solid color-mix(in srgb, var(--verified) 30%, var(--line));border-radius:var(--r-md);padding:11px 14px">' +
          '<span class="gl" style="color:var(--verified)">🛡</span>' +
          "<span>Private components never leave your environment. The lift gate still applies inside your workspace — a proprietary component must beat a bare model to be promotable, and the measurement runs <b>locally</b>.</span>" +
        "</div>" +
      "</div>"
    );
  }

  function onMountRegistry(host, ctx) {
    var cards = host.querySelectorAll("[data-priv-card]");
    for (var i = 0; i < cards.length; i++) {
      cards[i].addEventListener("click", function () {
        ctx.toast("Private component · stays in your workspace");
      });
    }
    var newComp = host.querySelector("[data-act='new-comp']");
    if (newComp) {
      newComp.addEventListener("click", function () {
        ctx.toast("New component — pick a primitive");
      });
    }
  }

  /* ---------------- /connect — PConnect ---------------- */

  function renderConnect(ctx) {
    var esc = ctx.esc;

    var mcpConfig =
      '{\n  "mcpServers": {\n    ' +
      '<span class="tok">"openharnesshub"</span>' +
      ": {\n      \"url\": \"https://mcp.openharnesshub.ai/sse\",\n      \"scopes\": [" +
      '<span class="tok">"catalog.read"</span>' +
      ', <span class="tok">"recommend"</span>' +
      ', <span class="tok">"pricing"</span>' +
      "]\n    }\n  }\n}";

    var bridgeHtml =
      '<div class="pt-bridge">' +

        '<div class="pt-zone private">' +
          '<div class="zh">Your environment<span class="tag">private</span></div>' +
          '<div class="zsub">Runs in your VPC / on-prem · proprietary</div>' +
          '<div class="pt-mcpnode agent"><span class="ic">◐</span><span class="nm">Your agent<small>claude · cursor · internal</small></span></div>' +
          '<div class="pt-mcpnode"><span class="ic">🗂</span><span class="nm">Filesystem · SOPs<small>mcp://local/files</small></span></div>' +
          '<div class="pt-mcpnode"><span class="ic">⛁</span><span class="nm">Private pgvector · deal memos<small>mcp://local/vector</small></span></div>' +
          '<div class="pt-mcpnode"><span class="ic">⚙</span><span class="nm">Internal ERP API<small>mcp://local/erp</small></span></div>' +
        "</div>" +

        '<div class="pt-bridge-mid">' +
          '<span class="line"></span>' +
          '<span class="lab">MCP · boundary</span>' +
          '<span class="pt-bridge-arrow"><span class="a">fill gaps →</span><span>← components</span></span>' +
        "</div>" +

        '<div class="pt-zone governed">' +
          '<div class="zh">OpenHarnessHub<span class="tag">governed</span></div>' +
          '<div class="zsub">Vetted catalog · lift-gated · provenance</div>' +
          '<div class="pt-mcpnode"><span class="ic">⚡</span><span class="nm">Governed components<small>1,284 promoted · ▲ measured lift</small></span></div>' +
          '<div class="pt-mcpnode"><span class="ic">⛁</span><span class="nm">Knowledge corpora<small>CSDDD · OFAC · GxP · ✔ sourced</small></span></div>' +
          '<div class="pt-mcpnode"><span class="ic">🛡</span><span class="nm">Lift &amp; provenance gate<small>only promotable components returned</small></span></div>' +
        "</div>" +

      "</div>";

    var crossLine =
      '<div class="pt-crossline">' +
        "<span>What crosses the boundary:</span>" +
        '<span class="ok">✓ task queries</span>' +
        '<span class="ok">✓ governed components &amp; knowledge</span>' +
        '<span class="no">✗ your proprietary data</span>' +
        '<span class="no">✗ private embeddings</span>' +
        '<span class="pt-spacer"></span>' +
        "<span>Privacy boundary:</span>" +
        '<div class="pt-seg" id="bnd-seg">' +
          '<button data-bnd="local">Local-only</button>' +
          '<button class="on" data-bnd="gapfill">Allow gap-fill</button>' +
          '<button data-bnd="hybrid">Hybrid</button>' +
        "</div>" +
      "</div>";

    var dashGrid =
      '<div class="pt-dash-grid">' +

        '<div class="pt-panel">' +
          '<div class="oh-cc-id mono" style="margin-bottom:4px">OpenHarnessHub as an MCP server</div>' +
          '<p style="font-size:12.5px;color:var(--fg-muted);margin:0 0 12px;line-height:1.5">Point your own agent here to pull governed components &amp; knowledge into local flows.</p>' +
          '<div class="pt-codeblock">' + mcpConfig + "</div>" +
          '<button class="oh-btn oh-btn--ghost oh-btn--sm" style="margin-top:12px" data-act="copy-mcp">⧉ Copy config</button>' +
        "</div>" +

        '<div class="pt-panel">' +
          '<div class="oh-cc-id mono" style="margin-bottom:4px">Your sources as MCP servers</div>' +
          '<p style="font-size:12.5px;color:var(--fg-muted);margin:0 0 8px;line-height:1.5">Register local servers OpenHarnessHub agents query to ground answers — data stays local.</p>' +
          '<div class="pt-srv">' +
            '<span class="dot" style="background:var(--success)"></span>' +
            '<span class="nm">Filesystem · SOPs<small>mcp://local/files</small></span>' +
            '<span class="pt-priv-badge priv">local-only</span>' +
          "</div>" +
          '<div class="pt-srv">' +
            '<span class="dot" style="background:var(--success)"></span>' +
            '<span class="nm">Private pgvector<small>mcp://local/vector</small></span>' +
            '<span class="pt-priv-badge priv">local-only</span>' +
          "</div>" +
          '<div class="pt-srv">' +
            '<span class="dot" style="background:var(--warning)"></span>' +
            '<span class="nm">Internal ERP API<small>mcp://local/erp · auth required</small></span>' +
            '<span class="oh-badge mono">configure</span>' +
          "</div>" +
          '<button class="oh-btn oh-btn--ghost oh-btn--sm" style="margin-top:12px" data-act="add-srv">+ Add server</button>' +
        "</div>" +

      "</div>";

    var infoMsg =
      '<div class="oh-state-msg" style="margin-top:16px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:11px 14px;font-size:12.5px;line-height:1.5">' +
        '<span class="gl" style="color:var(--accent)">◑</span>' +
        "<span><b>Hybrid retrieval, one flow.</b> A flow can read your private corpus locally and a governed corpus over MCP in the same step — the trace marks each fact’s source, so provenance stays honest across the boundary.</span>" +
      "</div>";

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          "<h1>Connect — local-first, bridged by MCP</h1>" +
          '<div class="sub">Keep proprietary context in your environment. Your agents source it locally and call OpenHarnessHub over MCP to fill the gaps — only queries &amp; governed components cross the line, never your data.</div>' +
        "</div>" +
        bridgeHtml +
        crossLine +
        dashGrid +
        infoMsg +
      "</div>"
    );
  }

  function onMountConnect(host, ctx) {
    // Privacy boundary segment toggle
    var bndBtns = host.querySelectorAll("[data-bnd]");
    for (var i = 0; i < bndBtns.length; i++) {
      bndBtns[i].addEventListener("click", function (e) {
        var clicked = e.currentTarget;
        for (var j = 0; j < bndBtns.length; j++) {
          bndBtns[j].classList.toggle("on", bndBtns[j] === clicked);
        }
      });
    }

    // Copy MCP config
    var copyBtn = host.querySelector("[data-act='copy-mcp']");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        ctx.toast("MCP config copied");
      });
    }

    // Add server
    var addSrvBtn = host.querySelector("[data-act='add-srv']");
    if (addSrvBtn) {
      addSrvBtn.addEventListener("click", function () {
        ctx.toast("Register a local MCP server");
      });
    }
  }

  /* ---------------- Registration ---------------- */

  window.OHH.register("/registry", renderRegistry, onMountRegistry, { theme: "dark" });
  window.OHH.register("/connect",  renderConnect,  onMountConnect,  { theme: "dark" });

}());
