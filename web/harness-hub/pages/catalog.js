/* Open Harness Hub — catalog.js
   Ports: PBrowse (/pipelines, /components), PDetail (/c/:slug),
          PDashboard (/app, /drafts), PPricing (/pricing)
   Vanilla ES5-style JS, no framework, no build step.
   Reads OHH.data (COMPONENTS, BY_SLUG, MODALITIES, COST_LABEL, EXEC_COLOR, TIERS).
   NEVER redeclares data; reads from ctx.data. */
(function () {
  "use strict";

  // Canonical marketing wordmark + nav (matches index.html / sdg.js / govern.js)
  var MARK_SVG_CATALOG = '<span class="oh-mark" aria-hidden="true">' +
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />' +
    '<path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" />' +
    '</svg></span>';

  var MKT_NAV_CATALOG = [
    ['/pipelines', 'Explore'],
    ['/compare',   'Compare'],
    ['/solutions', 'SDG solutions'],
    ['/pricing',   'Pricing'],
    ['/docs',      'Docs'],
    ['/trust',     'Trust']
  ];
  var FAMILY_LINKS_CATALOG = [
    ['https://baltor.ai', 'Baltor'],
    ['https://aidoneright.dev', 'AI Done Right']
  ];

  function mktHeaderCatalog(activeRoute) {
    var navItems = MKT_NAV_CATALOG.map(function (p) {
      var active = p[0] === activeRoute;
      return '<a data-nav="' + p[0] + '"' +
        (active ? ' style="color:var(--fg);font-weight:600"' : '') +
        '>' + p[1] + '</a>';
    }).join('');
    var familyLinks = FAMILY_LINKS_CATALOG.map(function (p) {
      return '<a href="' + p[0] + '">' + p[1] + '</a>';
    }).join('');
    return '<header class="pt-mkt-top">' +
      '<div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + MARK_SVG_CATALOG + ' Open Harness Hub</div>' +
      '<nav>' + navItems + familyLinks + '</nav>' +
      '<span class="pt-spacer"></span>' +
      '<div style="display:flex;gap:9px">' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/signin">Sign in</button>' +
      '<button class="oh-btn oh-btn--primary oh-btn--sm" data-nav="/signup">Get started</button>' +
      '</div>' +
    '</header>';
  }

  var PRIM_ORDER = ["input", "conditional", "knowledge", "action", "loop", "stop", "output"];

  var OWN_LABELS = [
    ["free", "Free · Open Harness Hub"],
    ["premium", "Premium · OHH (subscription)"],
    ["community-free", "Community · free"],
    ["community-paid", "Community · paid"]
  ];

  var OVERRIDES = {
    "harness": [["model_target", "gpt-class", "the model this harness wraps"], ["trust boundary", "text-op", "max execution class"], ["citation gate", "on", "require sourced claims"]],
    "knowledge-corpus": [["retrieval trigger", "rag · exact-id", "how facts surface"], ["chunking", "512 tok", "window size"], ["refresh", "static", "static vs CDC dynamic"]],
    "rule-pack": [["threshold · tier", "≥ 2", "when to route to review"], ["languages", "13", "rule coverage"]],
    "tool": [["timeout", "30s", "per-call ceiling"], ["side-effects", "none", "sandbox policy"]]
  };

  var RUBRIC_WEIGHTS = [["Citation accuracy", 40], ["Coverage", 30], ["Tone / stance", 15], ["Brevity", 15]];

  var VERSIONS = [
    ["1.3.0", "latest · 4d ago", "+0.41"],
    ["1.2.0", "6w ago", "+0.38"],
    ["1.1.0", "3mo ago", "+0.31"]
  ];

  // ---- helpers ----
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function liftBadge(c) {
    if (!c || c.kind !== "pipeline") return "";
    if (c.lift == null) return '<span class="oh-badge oh-badge--muted">△ structural</span>';
    return '<span class="oh-badge oh-badge--lift">▲ +' + c.lift.toFixed(2) + "</span>";
  }

  function provBadge(prov) {
    if (prov === "verified") return '<span class="oh-badge oh-badge--verified">✔ verified</span>';
    if (prov === "unsourced") return '<span class="oh-badge oh-badge--warn">⚠ unsourced</span>';
    return '<span class="oh-badge oh-badge--muted">✔ sourced</span>';
  }

  function execDotStyle(exec, execColorMap) {
    var col = execColorMap ? (execColorMap[exec] || "var(--fg-muted)") : "var(--fg-muted)";
    return 'width:8px;height:8px;border-radius:50%;flex:0 0 auto;display:inline-block;background:' + col;
  }

  // ---- CompCard renderer (reuse across browse pages) ----
  function compCardHtml(c, PRIMS, COST_LABEL, EXEC_COLOR, isPipeline) {
    var p = PRIMS[c.primitive] || { glyph: "⚡", label: "Action", v: "--p-action" };
    var costLabel = COST_LABEL ? (COST_LABEL[c.cost] || c.cost || "") : (c.cost || "");
    var lifeLine = "";
    if (isPipeline && c.lift != null) {
      lifeLine = liftBadge(c);
    }
    return '<div class="oh-comp-card" style="cursor:pointer" data-nav="/c/' + esc(c.slug) + '">' +
      '<div class="oh-cc-top">' +
      '<span class="oh-cc-prim" style="color:var(' + esc(p.v) + ')">' +
      '<span class="gl" style="font-size:14px">' + esc(p.glyph) + '</span>' +
      '<span>' + esc(p.label) + '</span>' +
      '<span class="sub">· ' + esc(c.type) + '</span>' +
      '</span>' +
      '<span class="spacer"></span>' +
      '<span class="oh-execdot" style="' + execDotStyle(c.exec, EXEC_COLOR) + '"></span>' +
      '</div>' +
      '<div class="oh-cc-name">' + esc(c.name) + '</div>' +
      '<div class="oh-cc-id mono">' + esc(c.type) + '/' + esc(c.slug) + '</div>' +
      '<div class="oh-cc-desc">' + esc(c.desc) + '</div>' +
      '<div class="oh-cc-divider"></div>' +
      '<div class="oh-cc-badges">' +
      provBadge(c.prov) +
      (lifeLine ? lifeLine : "") +
      '<span class="oh-badge mono">' + esc(costLabel) + '</span>' +
      '<span class="oh-badge oh-badge--stable">◆ ' + esc(c.lifecycle || "stable") + '</span>' +
      '</div>' +
      '</div>';
  }

  // ---- mini-dag strip for a list of primitive keys ----
  function miniDagHtml(PRIMS, keys) {
    var parts = [];
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (k === "op") {
        parts.push('<span class="oh-mininode is-op">◇</span>');
      } else {
        var p = PRIMS[k] || PRIMS.action;
        parts.push('<span class="oh-mininode" style="background:var(' + p.v + ')">' + p.glyph + '</span>');
      }
      if (i < keys.length - 1) parts.push('<span class="oh-miniedge"></span>');
    }
    return '<div class="oh-minidag">' + parts.join("") + '</div>';
  }

  // =====================================================
  // PBrowse — /pipelines and /components
  // =====================================================
  function renderBrowse(ctx, kind) {
    var data = ctx.data || {};
    var PRIMS = ctx.PRIMS || {};
    var COMPONENTS = data.COMPONENTS || [];
    var MODALITIES = data.MODALITIES || [];
    var COST_LABEL = data.COST_LABEL || {};
    var EXEC_COLOR = data.EXEC_COLOR || {};
    var isP = kind === "pipeline";
    var firstMod = MODALITIES.length ? MODALITIES[0][0] : "text";

    // modality state — stored on the element via data attributes, read in onMount
    var modTabsHtml = "";
    if (isP && MODALITIES.length) {
      modTabsHtml = '<div class="pt-modtabs" id="ohh-browse-modtabs">';
      for (var mi = 0; mi < MODALITIES.length; mi++) {
        var m = MODALITIES[mi];
        var kindPool = COMPONENTS.filter(function (c) { return c.kind === kind; });
        var modCnt = kindPool.filter(function (c) { return c.modality === m[0]; }).length;
        modTabsHtml += '<button class="pt-modtab' + (mi === 0 ? " on" : "") + '" data-mod="' + esc(m[0]) + '">' +
          '<span class="gl">' + esc(m[2]) + '</span>' + esc(m[1]) + '<span class="n">' + modCnt + '</span>' +
          '</button>';
      }
      modTabsHtml += '</div>';
    }

    // filter bar — Source filter (always), Primitive filter (components only)
    var filterBarHtml = '<div class="pt-filterbar" id="ohh-browse-filters">' +
      '<span class="pt-filter-label">Source</span>';
    for (var oi = 0; oi < OWN_LABELS.length; oi++) {
      var own = OWN_LABELS[oi];
      filterBarHtml += '<button class="pt-cons-chip" data-filter-owner="' + esc(own[0]) + '">' + esc(own[1]) + '</button>';
    }
    if (!isP) {
      filterBarHtml += '<span class="pt-filter-sep"></span><span class="pt-filter-label">Primitive</span>';
      for (var pi = 0; pi < PRIM_ORDER.length; pi++) {
        var pk = PRIM_ORDER[pi];
        if (!PRIMS[pk]) continue;
        var allKind = COMPONENTS.filter(function (c) { return c.kind === kind; });
        var primCnt = allKind.filter(function (c) { return c.primitive === pk; }).length;
        if (!primCnt) continue;
        filterBarHtml += '<button class="pt-cons-chip" data-filter-prim="' + esc(pk) + '">' +
          '<span style="display:inline-block;width:9px;height:9px;border-radius:2px;background:var(' + esc(PRIMS[pk].v) + ');margin-right:5px;vertical-align:middle"></span>' +
          esc(PRIMS[pk].label) +
          '</button>';
      }
    }
    filterBarHtml += '</div>';

    // cards placeholder — onMount will populate
    var html = '<div class="pt-page wide pt-view">' +
      '<div class="pt-page-head">' +
      '<h1>' + (isP ? "Explore pipelines" : "Explore components") + '</h1>' +
      '<div class="sub">' + (isP
        ? "Prebuilt, governed pipelines — each shows measured lift, governance &amp; cost."
        : "Reusable building blocks. Lift is measured at the pipeline level, not on individual components.") +
      '</div>' +
      '</div>' +
      modTabsHtml +
      '<div class="pt-results-bar" style="margin-bottom:12px">' +
      '<div class="pt-search"><span>⌕</span><input id="ohh-browse-q" placeholder="' + (isP ? "Search pipelines…" : "Search components…") + '" style="flex:1;border:none;outline:none;background:transparent;color:var(--fg);font-family:inherit;font-size:14px;padding:0 8px" /></div>' +
      '<span class="pt-muted" style="font-size:13px" id="ohh-browse-count"></span>' +
      '</div>' +
      filterBarHtml +
      '<div id="ohh-browse-cards"></div>' +
      '</div>';

    return html;
  }

  function onMountBrowse(host, ctx, kind) {
    var data = ctx.data || {};
    var PRIMS = ctx.PRIMS || {};
    var COMPONENTS = data.COMPONENTS || [];
    var MODALITIES = data.MODALITIES || [];
    var COST_LABEL = data.COST_LABEL || {};
    var EXEC_COLOR = data.EXEC_COLOR || {};
    var isP = kind === "pipeline";

    var activeMod = MODALITIES.length ? MODALITIES[0][0] : "text";
    var activeOwners = {};
    var activePrims = {};
    var q = "";

    var qEl = host.querySelector("#ohh-browse-q");
    var countEl = host.querySelector("#ohh-browse-count");
    var cardsEl = host.querySelector("#ohh-browse-cards");
    var modTabs = host.querySelectorAll("#ohh-browse-modtabs .pt-modtab");
    var ownerChips = host.querySelectorAll("[data-filter-owner]");
    var primChips = host.querySelectorAll("[data-filter-prim]");

    function getPool() {
      var kindPool = COMPONENTS.filter(function (c) { return c.kind === kind; });
      return isP ? kindPool.filter(function (c) { return c.modality === activeMod; }) : kindPool;
    }

    function getResults(pool) {
      var anyOwner = Object.keys(activeOwners).some(function (k) { return activeOwners[k]; });
      var anyPrim = Object.keys(activePrims).some(function (k) { return activePrims[k]; });
      return pool.filter(function (c) {
        if (q && !(((c.name || "") + " " + (c.slug || "") + " " + (c.desc || "") + " " + (c.industry || "")).toLowerCase().indexOf(q.toLowerCase()) >= 0)) return false;
        if (anyOwner && !activeOwners[c.owner]) return false;
        if (anyPrim && !activePrims[c.primitive]) return false;
        return true;
      });
    }

    function repaint() {
      if (!cardsEl) return;
      var pool = getPool();
      var results = getResults(pool);
      if (countEl) countEl.innerHTML = "<b style=\"color:var(--fg)\">" + results.length + "</b> of " + pool.length;

      if (!results.length) {
        var qText = q ? esc(q) : "(no matches)";
        cardsEl.innerHTML = '<div class="pt-zero">' +
          '<div class="ico">⌕</div>' +
          '<h3>Nothing matches &ldquo;' + qText + '&rdquo;</h3>' +
          '<p>Turn the gap into demand — request it and we’ll measure whether it beats a bare model.</p>' +
          '<button class="oh-btn oh-btn--primary" data-nav="/requests">+ Request this capability</button>' +
          '</div>';
        return;
      }

      var inner = '<div class="pt-cards-grid">';
      for (var i = 0; i < results.length; i++) {
        inner += compCardHtml(results[i], PRIMS, COST_LABEL, EXEC_COLOR, isP);
      }
      inner += "</div>";
      cardsEl.innerHTML = inner;
    }

    // wire modality tabs
    for (var mi = 0; mi < modTabs.length; mi++) {
      (function (tab) {
        tab.addEventListener("click", function () {
          activeMod = tab.getAttribute("data-mod") || activeMod;
          for (var ti = 0; ti < modTabs.length; ti++) {
            modTabs[ti].classList.toggle("on", modTabs[ti] === tab);
          }
          repaint();
        });
      })(modTabs[mi]);
    }

    // wire owner filter chips
    for (var oi = 0; oi < ownerChips.length; oi++) {
      (function (chip) {
        chip.addEventListener("click", function () {
          var key = chip.getAttribute("data-filter-owner");
          activeOwners[key] = !activeOwners[key];
          chip.classList.toggle("on", !!activeOwners[key]);
          repaint();
        });
      })(ownerChips[oi]);
    }

    // wire primitive filter chips
    for (var pi = 0; pi < primChips.length; pi++) {
      (function (chip) {
        chip.addEventListener("click", function () {
          var key = chip.getAttribute("data-filter-prim");
          activePrims[key] = !activePrims[key];
          chip.classList.toggle("on", !!activePrims[key]);
          repaint();
        });
      })(primChips[pi]);
    }

    // wire search input
    if (qEl) {
      qEl.addEventListener("input", function () {
        q = qEl.value;
        repaint();
      });
    }

    repaint();
  }

  // =====================================================
  // PDetail — /c/:slug
  // =====================================================
  function renderDetail(ctx) {
    var data = ctx.data || {};
    var PRIMS = ctx.PRIMS || {};
    var BY_SLUG = data.BY_SLUG || {};
    var COST_LABEL = data.COST_LABEL || {};
    var EXEC_COLOR = data.EXEC_COLOR || {};
    var slug = ctx.params.slug || "";
    var c = BY_SLUG[slug];

    if (!c) {
      return '<div class="pt-page pt-view">' +
        '<div class="pt-page-head"><h1>Not found</h1>' +
        '<div class="sub">No component or pipeline with slug &ldquo;' + esc(slug) + '&rdquo;.</div></div>' +
        '<div style="display:flex;gap:10px">' +
        '<button class="oh-btn oh-btn--ghost" data-nav="/components">Browse components</button>' +
        '<button class="oh-btn oh-btn--ghost" data-nav="/pipelines">Browse pipelines</button>' +
        '</div>' +
        '</div>';
    }

    var p = PRIMS[c.primitive] || { glyph: "⚡", label: "Action", v: "--p-action" };
    var blocked = c.prov === "unsourced";
    var isP = c.kind === "pipeline";
    var costLabel = COST_LABEL ? (COST_LABEL[c.cost] || c.cost || "") : (c.cost || "");
    var backRoute = isP ? "/pipelines" : "/components";
    var backLabel = isP ? "Pipelines" : "Components";

    var liftOrFits = "";
    if (isP) {
      var liftVal = c.lift != null ? c.lift : 0.4;
      var pipeScore = 0.42 + liftVal;
      liftOrFits = '<div class="oh-cc-id mono" style="margin-bottom:10px">capability lift</div>' +
        '<div class="oh-lb-row"><div class="oh-lb-label">bare model <b>0.42</b></div>' +
        '<div class="oh-lb-track"><div class="oh-lb-fill bare" style="width:42%"></div></div></div>' +
        '<div class="oh-lb-row"><div class="oh-lb-label">this pipeline <b>' + pipeScore.toFixed(2) + '</b></div>' +
        '<div class="oh-lb-track"><div class="oh-lb-fill pipe" style="width:' + Math.round(pipeScore * 100) + '%"></div></div></div>' +
        '<div class="oh-lift-delta"><span class="big" style="font-size:24px">▲ +' + liftVal.toFixed(2) + '</span></div>';
    } else {
      liftOrFits = '<div class="oh-cc-id mono" style="margin-bottom:10px">where it fits</div>' +
        '<p class="pt-muted" style="font-size:13px;line-height:1.55">A reusable building block used inside pipelines. ' +
        '<b style="color:var(--fg)">Lift is measured on the pipeline</b> that uses it — you can’t measure the lift of a component on its own.</p>';
    }

    var provBody = "";
    if (blocked) {
      provBody = '<div class="oh-state-msg blocked"><span class="gl">⚠</span>' +
        '<span><b>Unsourced.</b> Missing source URL + license — routed to review before it can be cited.</span></div>';
    } else {
      var srcLabel = c.industry === "ESG" ? "eur-lex.europa.eu" : "registry-verified";
      provBody = '<div style="font-size:13px;color:var(--fg-muted);line-height:1.7">' +
        '<div>source · <span class="mono" style="font-family:var(--font-mono);color:var(--fg)">' + esc(srcLabel) + '</span></div>' +
        '<div>license · <span class="mono" style="font-family:var(--font-mono);color:var(--fg)">' + esc(c.license || "—") + '</span></div>' +
        '<div>last-verified · <span class="mono" style="font-family:var(--font-mono);color:var(--fg)">2026-05-21</span></div>' +
        '</div>';
    }

    var blockedGateMsg = blocked
      ? '<div class="oh-state-msg blocked" style="margin-top:16px"><span class="gl">⚠</span>' +
        '<span><b>Blocked by the promotion gate.</b> This component can’t enter a tenant-visible flow until provenance is resolved. ' +
        '<a style="color:var(--accent);cursor:pointer;font-weight:600" data-nav="/requests">Fix: add provenance → request review →</a></span></div>'
      : "";

    // CompConfig inline (configure + versions tabs)
    var overrideRows = OVERRIDES[c.type];
    var configRows = "";
    if (!overrideRows || c.type === "rubric") {
      for (var ri = 0; ri < RUBRIC_WEIGHTS.length; ri++) {
        var rw = RUBRIC_WEIGHTS[ri];
        configRows += '<div class="pt-override">' +
          '<span class="nm">' + esc(rw[0]) + '<small>dimension weight</small></span>' +
          '<span class="pt-weight">' +
          '<span class="track"><i style="width:' + rw[1] + '%"></i></span>' +
          '<span class="val">' + rw[1] + '%</span>' +
          '</span></div>';
      }
    } else {
      for (var oi = 0; oi < overrideRows.length; oi++) {
        var row = overrideRows[oi];
        configRows += '<div class="pt-override">' +
          '<span class="nm">' + esc(row[0]) + '<small>' + esc(row[2]) + '</small></span>' +
          '<span class="oh-badge mono">' + esc(row[1]) + '</span>' +
          '</div>';
      }
    }
    if (!configRows) {
      configRows = '<div class="pt-override"><span class="nm">enabled<small>include in flows</small></span><span class="oh-badge mono">true</span></div>';
    }

    var verRows = "";
    for (var vi = 0; vi < VERSIONS.length; vi++) {
      var ver = VERSIONS[vi];
      verRows += '<div class="pt-ver">' +
        '<span class="sem">' + esc(ver[0]) + '</span>' +
        '<span class="when">' + esc(ver[1]) + '</span>' +
        '<span class="oh-badge oh-badge--lift" style="padding:2px 7px">▲ ' + esc(ver[2]) + '</span>' +
        '<button class="pt-ver-pin pin" data-ver="' + esc(ver[0]) + '">' + (vi === 0 ? "📌 pinned" : "pin") + '</button>' +
        '</div>';
    }

    var html = '<div class="pt-page pt-view">' +
      '<div class="pt-crumb" style="margin-bottom:16px">' +
      '<a style="cursor:pointer" data-nav="' + esc(backRoute) + '">' + esc(backLabel) + '</a>' +
      '<span class="sep">/</span><span>' + esc(c.type) + '</span><span class="sep">/</span><b>' + esc(c.slug) + '</b>' +
      '</div>' +
      '<div style="border-top:3px solid var(' + esc(p.v) + ');border-radius:3px;margin-bottom:16px"></div>' +
      '<div class="pt-row" style="align-items:flex-start;flex-wrap:wrap;gap:14px;margin-bottom:18px">' +
      '<div style="flex:1;min-width:280px">' +
      '<div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(' + esc(p.v) + ');display:flex;align-items:center;gap:8px">' +
      '<span class="oh-execdot" style="' + execDotStyle(c.exec, EXEC_COLOR) + '"></span>' +
      esc(p.glyph) + ' ' + esc(p.label) + ' · ' + esc(c.type) +
      '</div>' +
      '<h1 style="font-family:var(--font-display);font-size:28px;font-weight:700;margin:6px 0 4px;color:var(--fg)">' + esc(c.name) + '</h1>' +
      '<div class="oh-cc-id mono">' + esc(c.type) + '/' + esc(c.slug) + ' <span class="copy">⧉</span></div>' +
      '</div>' +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">' +
      (isP ? liftBadge(c) : "") +
      provBadge(c.prov) +
      '<button class="oh-btn oh-btn--primary oh-btn--sm" id="ohh-detail-add">+ Add to flow</button>' +
      '</div>' +
      '</div>' +
      '<p style="font-size:15px;line-height:1.55;color:var(--fg-muted);max-width:680px;margin-top:0">' + esc(c.desc) + '</p>' +
      '<div class="pt-grid-3" style="margin-top:18px">' +
      '<div class="pt-panel">' + liftOrFits + '</div>' +
      '<div class="pt-panel"><div class="oh-cc-id mono" style="margin-bottom:10px">provenance</div>' + provBody + '</div>' +
      '<div class="pt-panel"><div class="oh-cc-id mono" style="margin-bottom:10px">cost &amp; portability</div>' +
      '<div style="display:flex;flex-direction:column;gap:9px">' +
      '<div class="oh-statline"><span style="color:var(--fg-muted);font-size:13px">cost band</span><span class="oh-badge mono">' + esc(costLabel) + '</span></div>' +
      '<div class="oh-statline"><span style="color:var(--fg-muted);font-size:13px">recurring</span>' +
      '<span class="oh-badge ' + (c.recurring ? "" : "oh-badge--verified") + '">' + (c.recurring ? "↻ per model call" : "⌂ freezable · $0") + '</span></div>' +
      '<div class="oh-statline"><span style="color:var(--fg-muted);font-size:13px">lifecycle</span><span class="oh-badge oh-badge--stable">◆ ' + esc(c.lifecycle || "stable") + '</span></div>' +
      '</div></div>' +
      '</div>' +
      '<div class="pt-config" id="ohh-compconfig">' +
      '<div class="pt-config-tabs">' +
      '<button class="on" id="ohh-cfg-tab-configure">Configure</button>' +
      '<button id="ohh-cfg-tab-versions">Versions &amp; pinning</button>' +
      '</div>' +
      '<div id="ohh-cfg-pane-configure">' +
      configRows +
      '<div style="display:flex;gap:9px;margin-top:14px">' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" id="ohh-cfg-reset">Reset to default</button>' +
      '<button class="oh-btn oh-btn--primary oh-btn--sm" id="ohh-cfg-fork">Save as variant (fork) →</button>' +
      '<span style="font-size:11.5px;color:var(--fg-faint);align-self:center">A behavior change re-triggers lift measurement.</span>' +
      '</div>' +
      '</div>' +
      '<div id="ohh-cfg-pane-versions" style="display:none">' +
      verRows +
      '<div style="font-size:11.5px;color:var(--fg-muted);margin-top:12px">Pinning keeps your flows from drifting when a component updates. Rolling back mints a <b style="color:var(--fg)">new</b> version — published versions are never mutated. <b>3 flows</b> pin <span style="font-family:var(--font-mono)">@1.3.0</span>.</div>' +
      '</div>' +
      '</div>' +
      blockedGateMsg +
      '</div>';

    return html;
  }

  function onMountDetail(host, ctx) {
    var toast = ctx.toast || function () {};

    var addBtn = host.querySelector("#ohh-detail-add");
    var data = ctx.data || {};
    var BY_SLUG = data.BY_SLUG || {};
    var slug = ctx.params.slug || "";
    var c = BY_SLUG[slug];
    var cName = c ? c.name : slug;

    if (addBtn) {
      addBtn.addEventListener("click", function () {
        toast("Added to flow · " + cName);
      });
    }

    // config tabs
    var tabConfigure = host.querySelector("#ohh-cfg-tab-configure");
    var tabVersions = host.querySelector("#ohh-cfg-tab-versions");
    var paneConfigure = host.querySelector("#ohh-cfg-pane-configure");
    var paneVersions = host.querySelector("#ohh-cfg-pane-versions");

    function switchTab(active) {
      if (tabConfigure) tabConfigure.classList.toggle("on", active === "configure");
      if (tabVersions) tabVersions.classList.toggle("on", active === "versions");
      if (paneConfigure) paneConfigure.style.display = active === "configure" ? "" : "none";
      if (paneVersions) paneVersions.style.display = active === "versions" ? "" : "none";
    }

    if (tabConfigure) tabConfigure.addEventListener("click", function () { switchTab("configure"); });
    if (tabVersions) tabVersions.addEventListener("click", function () { switchTab("versions"); });

    var resetBtn = host.querySelector("#ohh-cfg-reset");
    var forkBtn = host.querySelector("#ohh-cfg-fork");
    if (resetBtn) resetBtn.addEventListener("click", function () { toast("Reset to defaults"); });
    if (forkBtn) forkBtn.addEventListener("click", function () { toast("Forked as tenant variant · lineage recorded"); });

    // version pin buttons
    var pinBtns = host.querySelectorAll(".pt-ver-pin");
    var pinnedVer = "1.3.0";
    function updatePins() {
      for (var i = 0; i < pinBtns.length; i++) {
        var v = pinBtns[i].getAttribute("data-ver");
        pinBtns[i].classList.toggle("pinned", v === pinnedVer);
        pinBtns[i].textContent = v === pinnedVer ? "📌 pinned" : "pin";
      }
      // update the prose
      var prose = paneVersions ? paneVersions.querySelector("div[style*='font-size:11.5px']") : null;
      if (prose) {
        var span = prose.querySelector("span[style*='font-mono']");
        if (span) span.textContent = "@" + pinnedVer;
      }
    }
    for (var bi = 0; bi < pinBtns.length; bi++) {
      (function (btn) {
        btn.addEventListener("click", function () {
          pinnedVer = btn.getAttribute("data-ver");
          toast("Pinned @" + pinnedVer);
          updatePins();
        });
      })(pinBtns[bi]);
    }
  }

  // =====================================================
  // PDashboard — /app and /drafts
  // =====================================================
  var DASH_FLOWS = [
    ["CSDDD supplier grading", "flow/csddd-grade", "▲ +0.41", "6 comp · $$"],
    ["Contract renewal-risk review", "flow/renewal-risk", "▲ +0.33", "5 comp · $$"]
  ];
  var DASH_RUNS = [
    ["flow/csddd-grade", "$0.0312 · 13.9s", "✓"],
    ["flow/renewal-risk", "$0.018 · 8.2s", "✓"],
    ["flow/aml-screen", "blocked-by-gate", "⚠"]
  ];
  var DASH_GAPS = ["Scope-3 emissions estimator", "Conflict-minerals tracer", "Living-wage calculator"];

  var DRAFT_FLOWS = [
    ["CSDDD v1 (draft)", "flow/csddd-draft", "▲ +0.35", "5 comp · $$ · draft"],
    ["Customs HS classifier (in-progress)", "flow/customs-hs", "▲ +0.22", "4 comp · $ · draft"]
  ];

  function renderDashboard(ctx, isDrafts) {
    var state = ctx.state || {};
    var taskVal = state.task || "";

    var flowList = isDrafts ? DRAFT_FLOWS : DASH_FLOWS;
    var headTitle = isDrafts ? "Drafts" : "Workspace";
    var headSub = isDrafts ? "Saved and in-progress flows to resume." : "Resume a flow, review runs, or paste a new task.";

    var flowRows = "";
    for (var fi = 0; fi < flowList.length; fi++) {
      var f = flowList[fi];
      flowRows += '<div class="pt-list-row" data-nav="/flow" style="cursor:pointer">' +
        '<div style="flex:1"><div class="ttl">' + esc(f[0]) + '</div><div class="meta">' + esc(f[1]) + '</div></div>' +
        '<span class="oh-badge oh-badge--lift">' + esc(f[2]) + '</span>' +
        '<span class="meta">' + esc(f[3]) + '</span>' +
        '</div>';
    }

    var runRows = "";
    if (!isDrafts) {
      for (var ri = 0; ri < DASH_RUNS.length; ri++) {
        var r = DASH_RUNS[ri];
        var isOk = r[2] === "✓";
        runRows += '<div class="pt-list-row" data-nav="/run" style="cursor:pointer">' +
          '<div style="flex:1"><div class="ttl">' + esc(r[0]) + '</div><div class="meta">' + esc(r[1]) + '</div></div>' +
          '<span class="oh-badge ' + (isOk ? "oh-badge--lift" : "oh-badge--warn") + '">' + esc(r[2]) + '</span>' +
          '</div>';
      }
    }

    var gapChips = "";
    for (var gi = 0; gi < DASH_GAPS.length; gi++) {
      gapChips += '<button class="pt-cons-chip" data-nav="/requests">◷ ' + esc(DASH_GAPS[gi]) + '</button>';
    }

    var html = '<div class="pt-page wide pt-view">' +
      '<div class="pt-page-head"><h1>' + esc(headTitle) + '</h1><div class="sub">' + esc(headSub) + '</div></div>' +
      '<div class="pt-dash-entry" style="margin-bottom:20px">' +
      '<textarea id="ohh-dash-task" placeholder="Paste a task to build a new flow…" style="width:100%;border:none;outline:none;resize:none;background:transparent;color:var(--fg);font-family:inherit;font-size:14px;min-height:60px;line-height:1.5">' + esc(taskVal) + '</textarea>' +
      '<div style="display:flex;justify-content:flex-end;margin-top:8px">' +
      '<button class="oh-btn oh-btn--primary oh-btn--sm" id="ohh-dash-build">Build →</button>' +
      '</div>' +
      '</div>' +
      '<div class="pt-dash-grid">' +
      '<div class="pt-panel">' +
      '<div class="oh-cc-id mono" style="margin-bottom:6px">' + (isDrafts ? "your drafts" : "recent flows") + '</div>' +
      flowRows +
      '</div>' +
      (!isDrafts ? '<div class="pt-panel"><div class="oh-cc-id mono" style="margin-bottom:6px">recent runs</div>' + runRows + '</div>' : "") +
      '</div>' +
      '<div class="pt-panel" style="margin-top:16px">' +
      '<div class="oh-cc-id mono" style="margin-bottom:8px">suggested gaps in ESG · CSDDD</div>' +
      '<div style="display:flex;gap:10px;flex-wrap:wrap">' + gapChips + '</div>' +
      '</div>' +
      '</div>';

    return html;
  }

  function onMountDashboard(host, ctx) {
    var toast = ctx.toast || function () {};
    var navigate = ctx.navigate || function () {};
    var state = ctx.state || {};

    var taskEl = host.querySelector("#ohh-dash-task");
    var buildBtn = host.querySelector("#ohh-dash-build");

    if (taskEl) {
      taskEl.addEventListener("input", function () {
        state.task = taskEl.value;
        try { sessionStorage.setItem("ohp-task", taskEl.value); } catch (e) {}
      });
    }

    if (buildBtn) {
      buildBtn.addEventListener("click", function () {
        var v = taskEl ? taskEl.value.trim() : (state.task || "").trim();
        if (v.length > 11) {
          navigate("/build");
        } else {
          toast("Describe the task a bit more");
        }
      });
    }
  }

  // =====================================================
  // PPricing — /pricing (light theme)
  // =====================================================
  function renderPricing(ctx) {
    function openFeat(text) {
      return '<li class="open-feat"><span class="ck">✔</span>' + text + '</li>';
    }
    function paidFeat(text) {
      return '<li class="paid-feat"><span class="ck">◆</span>' + text + '</li>';
    }
    function offFeat(text) {
      return '<li class="off"><span class="ck">·</span>' + text + '</li>';
    }

    var html = '<div class="pt-mkt pt-view">' +
      mktHeaderCatalog('/pricing') +
      '<div class="pt-mkt-body">' +
      '<div class="pt-page wide pt-view">' +
      '<div class="pt-page-head">' +
      '<h1>Pricing</h1>' +
      '<div class="sub">The spec is open and free forever. The governed components and live knowledge are the subscription.</div>' +
      '</div>' +
      '<div class="pt-openline">' +
      '<span class="gl">🛡</span>' +
      '<span><b>Open spec, governed content.</b> The schemas, the seven-primitive grammar, the SDK, the CLI, the export emitters — open under Apache-2.0. The <b>vetted components</b>, <b>live knowledge corpora</b>, and <b>build-on-demand</b> are what you pay for. Export anything you build; never get locked in.</span>' +
      '</div>' +
      '<div class="pt-tiers">' +
      '<div class="pt-tier open">' +
      '<span class="tag">Open · free forever</span>' +
      '<h3>Free / OSS</h3>' +
      '<div class="price"><b>$0</b></div>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm cta" id="ohh-price-oss">Get the spec →</button>' +
      '<ul>' +
      openFeat("Spec, schemas &amp; seven-primitive grammar") +
      openFeat("CLI (<span style=\"font-family:var(--font-mono)\">oh-hub</span>) + reference SDK") +
      openFeat("All export emitters (SPDX, C2PA, JSON-LD…)") +
      openFeat("Build &amp; export flows · self-host") +
      openFeat("Simulate runs (bring your own key)") +
      offFeat("Vetted components &amp; knowledge") +
      offFeat("Live freshness / governance") +
      '</ul>' +
      '</div>' +
      '<div class="pt-tier feat">' +
      '<span class="tag">★ Most popular</span>' +
      '<h3>Pro</h3>' +
      '<div class="price"><b>$39</b> / seat / mo <span style="opacity:.6">· indicative</span></div>' +
      '<button class="oh-btn oh-btn--primary oh-btn--sm cta" id="ohh-price-pro">Start free trial</button>' +
      '<ul>' +
      openFeat("Everything in Free") +
      paidFeat("Vetted components &amp; knowledge packs") +
      paidFeat("Measured lift &amp; provenance on every component") +
      paidFeat("Hosted runs · live pricing") +
      paidFeat("Capability-requests (build-on-demand)") +
      offFeat("Team governance &amp; review queue") +
      '</ul>' +
      '</div>' +
      '<div class="pt-tier">' +
      '<span class="tag">Teams</span>' +
      '<h3>Team</h3>' +
      '<div class="price"><b>$299</b> / mo <span style="opacity:.6">· indicative</span></div>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm cta" id="ohh-price-team">Contact sales</button>' +
      '<ul>' +
      paidFeat("Everything in Pro") +
      paidFeat("Shared registry &amp; pinning") +
      paidFeat("Review queue &amp; promotion gates") +
      paidFeat("Live knowledge corpora (CDC freshness)") +
      paidFeat("Usage analytics &amp; credits") +
      '</ul>' +
      '</div>' +
      '<div class="pt-tier">' +
      '<span class="tag">Regulated</span>' +
      '<h3>Enterprise</h3>' +
      '<div class="price"><b>Custom</b></div>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm cta" id="ohh-price-ent">Talk to us</button>' +
      '<ul>' +
      paidFeat("Everything in Team") +
      paidFeat("Air-gapped / BYO-cloud deploy") +
      paidFeat("SSO, audit export, compliance pack") +
      paidFeat("Verified-publisher provenance") +
      paidFeat("Private foundry &amp; managed ingestion") +
      '</ul>' +
      '</div>' +
      '</div>' +
      '<div class="pt-pricing-note">Prices indicative until validated. Export is always free — the freezable layer (static / text-op components) leaves with you; the live &amp; governed layer is the subscription.</div>' +
      '</div>' +
      '</div>' +
      '</div>';

    return html;
  }

  function onMountPricing(host, ctx) {
    var toast = ctx.toast || function () {};
    var ossBtn = host.querySelector("#ohh-price-oss");
    var proBtn = host.querySelector("#ohh-price-pro");
    var teamBtn = host.querySelector("#ohh-price-team");
    var entBtn = host.querySelector("#ohh-price-ent");
    if (ossBtn) ossBtn.addEventListener("click", function () { toast("Free / OSS — grab the spec at github.com/openharnesshub"); });
    if (proBtn) proBtn.addEventListener("click", function () { toast("Pro — coming soon"); });
    if (teamBtn) teamBtn.addEventListener("click", function () { toast("Team — coming soon"); });
    if (entBtn) entBtn.addEventListener("click", function () { toast("Enterprise — let’s talk"); });
  }

  // =====================================================
  // Route registrations
  // =====================================================
  window.OHH = window.OHH || {};

  OHH.register("/pipelines", function (ctx) {
    return renderBrowse(ctx, "pipeline");
  }, function (host, ctx) {
    onMountBrowse(host, ctx, "pipeline");
  }, { theme: "dark" });

  OHH.register("/components", function (ctx) {
    return renderBrowse(ctx, "component");
  }, function (host, ctx) {
    onMountBrowse(host, ctx, "component");
  }, { theme: "dark" });

  OHH.register("/c/:slug", function (ctx) {
    return renderDetail(ctx);
  }, function (host, ctx) {
    onMountDetail(host, ctx);
  }, { theme: "dark" });

  OHH.register("/app", function (ctx) {
    return renderDashboard(ctx, false);
  }, function (host, ctx) {
    onMountDashboard(host, ctx);
  }, { theme: "dark" });

  OHH.register("/drafts", function (ctx) {
    return renderDashboard(ctx, true);
  }, function (host, ctx) {
    onMountDashboard(host, ctx);
  }, { theme: "dark" });

  OHH.register("/pricing", function (ctx) {
    return renderPricing(ctx);
  }, function (host, ctx) {
    onMountPricing(host, ctx);
  }, { theme: "light" });

})();
