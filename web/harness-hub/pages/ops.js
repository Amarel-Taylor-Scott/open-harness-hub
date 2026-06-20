/* Open Harness Hub — ops screens: PStatus · PActivity · PSources
   Faithful vanilla port of proto-ops.jsx. No React, no JSX, no imports.
   Registers: /status · /activity · /sources (all theme: dark). */
(function () {
  "use strict";

  /* ============================== STATUS / SLA ============================== */

  var SVCS = [
    ["API gateway",          99.99],
    ["Search & recommend",   99.98],
    ["Pipeline generation",  99.95],
    ["Run orchestrator",     99.92],
    ["MCP gateway",          99.97],
    ["Freshness / CDC",      99.90],
    ["Foundry",              99.4],
  ];

  function uptimeHtml(pct) {
    var bars = "";
    for (var i = 0; i < 40; i++) {
      var cls = "";
      // deterministic pseudo-random using index so SSR and client match
      var r = ((i * 6364136223846793005 + 1442695040888963407) >>> 0) / 4294967296;
      if (pct < 99.5 && i > 30 && i < 34) { cls = " class=\"down\""; }
      else if (pct < 99.95 && r > 0.94)   { cls = " class=\"warn\""; }
      bars += "<i" + cls + "></i>";
    }
    return "<span class=\"pt-uptime\">" + bars + "</span>";
  }

  function renderStatus(ctx) {
    var e = ctx.esc;
    var svcRows = "";
    for (var i = 0; i < SVCS.length; i++) {
      var nm = SVCS[i][0], up = SVCS[i][1];
      svcRows += "<div class=\"pt-svc-row\">" +
        "<span class=\"nm\">" + e(nm) + "</span>" +
        uptimeHtml(up) +
        "<span class=\"up\">" + e(String(up)) + "%</span>" +
        "</div>";
    }

    return "<div class=\"pt-page wide pt-view\">" +
      "<div class=\"pt-page-head\">" +
        "<h1>Status</h1>" +
        "<div class=\"sub\">Live service health, 90-day uptime, and SLA commitments.</div>" +
      "</div>" +
      "<div class=\"pt-status-banner\">" +
        "<span class=\"d\"></span>" +
        "<span class=\"t\">All systems operational</span>" +
        "<span class=\"s\">updated 30s ago · subscribe via email / RSS</span>" +
      "</div>" +
      "<div class=\"pt-panel\">" +
        "<div class=\"oh-cc-id mono\" style=\"margin-bottom:12px\">services · 90-day uptime</div>" +
        svcRows +
      "</div>" +
      "<div class=\"pt-dash-grid\" style=\"margin-top:16px\">" +
        "<div class=\"pt-panel\">" +
          "<div class=\"oh-cc-id mono\" style=\"margin-bottom:10px\">SLA commitments</div>" +
          "<table class=\"pt-table\">" +
            "<thead><tr><th>Tier</th><th>Uptime</th><th>Support</th><th>Freshness</th></tr></thead>" +
            "<tbody>" +
              "<tr><td>Pro</td><td class=\"mono\">99.5%</td><td>next business day</td><td>weekly</td></tr>" +
              "<tr><td>Team</td><td class=\"mono\">99.9%</td><td>4h</td><td>daily</td></tr>" +
              "<tr><td>Enterprise</td><td class=\"mono\">99.95%</td><td>1h · 24/7</td><td>real-time + credits-back</td></tr>" +
            "</tbody>" +
          "</table>" +
        "</div>" +
        "<div class=\"pt-panel\">" +
          "<div class=\"oh-cc-id mono\" style=\"margin-bottom:8px\">recent incidents</div>" +
          "<div class=\"pt-incident\">" +
            "<span class=\"dt\">May 12 · 22m</span>" +
            "<div class=\"body\">" +
              "<div class=\"h\">Elevated latency · pipeline generation</div>" +
              "<div class=\"d\">Resolved — provider failover; SLA credit applied to affected tenants.</div>" +
            "</div>" +
          "</div>" +
          "<div class=\"pt-incident\">" +
            "<span class=\"dt\">Apr 28 · 8m</span>" +
            "<div class=\"body\">" +
              "<div class=\"h\">CDC sync delay · EUR-Lex</div>" +
              "<div class=\"d\">Resolved — facts re-verified &amp; re-signed; affected flows flagged.</div>" +
            "</div>" +
          "</div>" +
          "<div class=\"pt-incident\">" +
            "<span class=\"dt\">Apr 03</span>" +
            "<div class=\"body\">" +
              "<div class=\"h\">Scheduled maintenance</div>" +
              "<div class=\"d\">Foundry partition migration · no downtime.</div>" +
            "</div>" +
          "</div>" +
        "</div>" +
      "</div>" +
    "</div>";
  }

  OHH.register("/status", renderStatus, null, { theme: "dark" });

  /* ============================== ACTIVITY + NOTIFICATIONS ============================== */

  var EVTS = [
    { k: "ver",    color: "var(--p-loop)",  ic: "↻", // ↻
      h: "Version bump · <span class=\"mono\">harness/esg-cite-first</span> <b>1.2.0 → 1.3.0</b>",
      t2: "4m ago",
      diff: "<span class=\"add\">+ citation gate hardened</span> · lift +0.38 → +0.41" },
    { k: "cdc",    color: "var(--verified)", ic: "⟳", // ⟳
      h: "<b>CDC</b> · CSDDD Art. 8 (DE) amended in <span class=\"mono\">csddd-articles</span>",
      t2: "1h ago",
      diff: "3 facts superseded · re-signed" },
    { k: "revoke", color: "var(--danger)",   ic: "⊘", // ⊘
      h: "<b>Revoked</b> · 2 EPA limits withdrawn from <span class=\"mono\">echa-corpus</span>",
      t2: "3h ago",
      diff: "<span class=\"rem\">− 2 facts</span> · 1 flow flagged for review" },
    { k: "decay",  color: "var(--warning)",  ic: "▼", // ▼
      h: "<b>Decay watch</b> · <span class=\"mono\">harness/esg-cite-first</span> lift eroding",
      t2: "today",
      diff: "−0.04 as base models improve · prune candidate" },
    { k: "promo",  color: "var(--success)",  ic: "▲", // ▲
      h: "<b>New in ESG</b> · <span class=\"mono\">processor/scope3-estimator</span> promoted",
      t2: "yesterday",
      diff: "cleared the gate ▲ +0.36" },
    { k: "pin",    color: "var(--accent)",   ic: "📌", // 📌
      h: "Pinned update available · <span class=\"mono\">knowledge-corpus/ofac-sdn</span>",
      t2: "2d ago",
      diff: "diff before accepting · 3 flows pin @1.4.0" },
  ];

  var LABEL = {
    ver:    "Version bumps",
    cdc:    "CDC / freshness changes",
    revoke: "Revocations",
    decay:  "Decay flips",
    promo:  "New promotions in my domains",
    pin:    "Pinned-component updates",
  };

  var WATCHES = [
    "harness/esg-cite-first",
    "knowledge-corpus/csddd-articles",
    "flow/csddd-grade",
  ];

  function renderActivity(ctx) {
    var e = ctx.esc;

    var evtRows = "";
    for (var i = 0; i < EVTS.length; i++) {
      var ev = EVTS[i];
      evtRows += "<div class=\"pt-evt\" data-evtkey=\"" + e(ev.k) + "\">" +
        "<span class=\"ico\" style=\"background:color-mix(in srgb, " + ev.color + " 14%, transparent);color:" + ev.color + "\">" + ev.ic + "</span>" +
        "<div class=\"body\">" +
          "<div class=\"h\">" + ev.h + "</div>" +
          "<div class=\"t\">" + e(ev.t2) + "</div>" +
          "<div class=\"diff\">" + ev.diff + "</div>" +
        "</div>" +
      "</div>";
    }

    var cadenceOpts = ["realtime", "daily", "weekly"];
    var cadenceBtns = "";
    for (var c = 0; c < cadenceOpts.length; c++) {
      var m = cadenceOpts[c];
      var label = m.charAt(0).toUpperCase() + m.slice(1);
      cadenceBtns += "<button data-cadence=\"" + e(m) + "\" class=\"" + (m === "daily" ? "on" : "") + "\">" + e(label) + "</button>";
    }

    var prefKeys = Object.keys(LABEL);
    var prefRows = "";
    for (var p = 0; p < prefKeys.length; p++) {
      var pk = prefKeys[p];
      // ver/cdc/revoke/pin default on; promo/decay: promo off, decay on
      var defaultOn = (pk !== "promo");
      prefRows += "<div class=\"pt-setting-row\">" +
        "<div class=\"info\"><div class=\"t\">" + e(LABEL[pk]) + "</div></div>" +
        "<span class=\"pt-switch" + (defaultOn ? " on" : "") + "\" data-prefkey=\"" + e(pk) + "\"><i></i></span>" +
      "</div>";
    }

    var watchRows = "";
    for (var w = 0; w < WATCHES.length; w++) {
      var wid = WATCHES[w];
      watchRows += "<div class=\"pt-srv\" style=\"border-color:var(--line)\">" +
        "<span class=\"dot\" style=\"background:var(--verified)\"></span>" +
        "<span class=\"nm mono\" style=\"font-family:var(--font-mono);font-size:11.5px\">" + e(wid) + "</span>" +
        "<span class=\"pt-unwatch\" style=\"color:var(--fg-faint);cursor:pointer;font-size:11px\" data-watch=\"" + e(wid) + "\">unwatch</span>" +
      "</div>";
    }

    return "<div class=\"pt-page wide pt-view\">" +
      "<div class=\"pt-page-head\">" +
        "<h1>Activity</h1>" +
        "<div class=\"sub\">Everything that changed — and the email digests &amp; watches that keep you ahead of it.</div>" +
      "</div>" +
      "<div class=\"pt-activity\">" +
        "<div class=\"pt-panel\">" +
          "<div class=\"oh-cc-id mono\" style=\"margin-bottom:6px\">recent activity</div>" +
          evtRows +
        "</div>" +
        "<div>" +
          "<div class=\"pt-panel\">" +
            "<div class=\"oh-cc-id mono\" style=\"margin-bottom:6px\">email &amp; alerts</div>" +
            "<div class=\"pt-setting-row\" style=\"padding-top:4px\">" +
              "<div class=\"info\"><div class=\"t\">Digest cadence</div><div class=\"d\">to nadia@acme.co</div></div>" +
              "<div class=\"pt-seg\" id=\"act-cadence-seg\">" + cadenceBtns + "</div>" +
            "</div>" +
            prefRows +
            "<div style=\"display:flex;gap:8px;margin-top:12px\">" +
              "<button class=\"oh-btn oh-btn--ghost oh-btn--sm\" id=\"act-webhook-btn\">+ Webhook</button>" +
              "<button class=\"oh-btn oh-btn--primary oh-btn--sm\" id=\"act-save-btn\">Save</button>" +
            "</div>" +
          "</div>" +
          "<div class=\"pt-panel\" style=\"margin-top:14px\">" +
            "<div class=\"oh-cc-id mono\" style=\"margin-bottom:8px\">watching · 3 objects</div>" +
            watchRows +
          "</div>" +
        "</div>" +
      "</div>" +
    "</div>";
  }

  function onMountActivity(host, ctx) {
    // Cadence segment
    var cadenceSeg = host.querySelector("#act-cadence-seg");
    if (cadenceSeg) {
      var btns = cadenceSeg.querySelectorAll("button");
      for (var i = 0; i < btns.length; i++) {
        (function (btn) {
          btn.addEventListener("click", function () {
            for (var j = 0; j < btns.length; j++) btns[j].classList.remove("on");
            btn.classList.add("on");
          });
        })(btns[i]);
      }
    }

    // Pref toggles
    var switches = host.querySelectorAll(".pt-switch[data-prefkey]");
    for (var s = 0; s < switches.length; s++) {
      (function (sw) {
        sw.addEventListener("click", function () {
          sw.classList.toggle("on");
        });
      })(switches[s]);
    }

    // Webhook button
    var whBtn = host.querySelector("#act-webhook-btn");
    if (whBtn) whBtn.addEventListener("click", function () { ctx.toast("Webhook endpoint added"); });

    // Save button
    var saveBtn = host.querySelector("#act-save-btn");
    if (saveBtn) saveBtn.addEventListener("click", function () { ctx.toast("Notification preferences saved"); });

    // Unwatch links
    var unwatches = host.querySelectorAll(".pt-unwatch");
    for (var u = 0; u < unwatches.length; u++) {
      (function (el) {
        el.addEventListener("click", function () { ctx.toast("Unwatched"); });
      })(unwatches[u]);
    }
  }

  OHH.register("/activity", renderActivity, onMountActivity, { theme: "dark" });

  /* ============================== GITHUB VECTORIZED SOURCE SEARCH ============================== */

  var GH = [
    {
      nm: "Citation-grounded RAG harness",
      repo: "github.com/oss-legal/cite-rag",
      stars: "4.2k",
      lic: "Apache-2.0",
      match: "enforces a <mark>deterministic citation gate</mark> before the model answers",
      status: "promoted",
      slug: "esg-cite-first",
    },
    {
      nm: "EU regulation article splitter",
      repo: "github.com/euopen/reg-splitter",
      stars: "1.1k",
      lic: "MIT",
      match: "splits <mark>CSDDD</mark> &amp; EU regs to article level with source URLs",
      status: "promoted",
      slug: null,
    },
    {
      nm: "OFAC / sanctions matcher",
      repo: "github.com/compliance/sdn-match",
      stars: "880",
      lic: "MIT",
      match: "fuzzy <mark>sanctions screening</mark> with explainable matches",
      status: "abstract",
      slug: null,
    },
    {
      nm: "Scope-3 emissions estimator",
      repo: "github.com/climate/scope3",
      stars: "2.6k",
      lic: "GPL-3.0",
      match: "computes <mark>Scope 3</mark> with cited emission factors",
      status: "abstract",
      slug: null,
    },
  ];

  function renderSources(ctx) {
    var e = ctx.esc;
    var q = "grade suppliers against CSDDD with citations";

    var ghRows = "";
    for (var i = 0; i < GH.length; i++) {
      var g = GH[i];
      var isAbstract = g.status === "abstract";
      var footHtml;
      if (!isAbstract) {
        var viewNav = "/components";
        if (g.slug) viewNav = "/c/" + g.slug;
        footHtml = "<span class=\"pt-gh-status promoted\">✓ promoted</span>" +
          "<span class=\"oh-badge oh-badge--lift\" style=\"padding:2px 7px\">▲ +0.41</span>" +
          "<button class=\"oh-btn oh-btn--ghost oh-btn--sm\" data-nav=\"" + e(viewNav) + "\">View component →</button>";
      } else {
        footHtml = "<span class=\"pt-gh-status abstract\">◷ not implemented</span>" +
          "<span style=\"font-size:11.5px;color:var(--fg-muted)\">license-filtered · provenance traced to repo</span>" +
          "<button class=\"oh-btn oh-btn--primary oh-btn--sm\" data-ingest-repo=\"" + e(g.repo) + "\">Ingest &amp; gate →</button>";
      }

      ghRows += "<div class=\"pt-gh-row" + (isAbstract ? " abstract" : "") + "\">" +
        "<div class=\"pt-gh-top\">" +
          "<span class=\"nm\">" + (isAbstract ? "◷ " : "") + e(g.nm) + "</span>" +
          "<span class=\"stars\">★ " + e(g.stars) + "</span>" +
          "<span class=\"lic\">" + e(g.lic) + "</span>" +
        "</div>" +
        "<a class=\"repo\" style=\"font-family:var(--font-mono);font-size:11.5px;color:var(--info);cursor:pointer\" data-repo-link=\"" + e(g.repo) + "\">↗ " + e(g.repo) + "</a>" +
        "<div class=\"match\">why-matched · " + g.match + "</div>" +
        "<div class=\"foot\">" + footHtml + "</div>" +
      "</div>";
    }

    return "<div class=\"pt-page wide pt-view\">" +
      "<div class=\"pt-page-head\">" +
        "<h1>Source search · GitHub</h1>" +
        "<div class=\"sub\">Vectorized search across OSS ecosystems — find candidate components, see provenance, and ingest the ones that clear the lift gate.</div>" +
      "</div>" +
      "<div class=\"pt-results-bar\">" +
        "<div class=\"pt-search\">" +
          "<span>⌕</span>" +
          "<input id=\"src-search-input\" type=\"text\" value=\"\" placeholder=\"" + e(q) + "\" />" +
        "</div>" +
        "<span class=\"pt-gh-mode\">◑ semantic · pgvector</span>" +
        "<span class=\"pt-muted\" style=\"font-size:13px\"><b style=\"color:var(--fg)\">4</b> candidates</span>" +
      "</div>" +
      ghRows +
      "<div class=\"oh-state-msg\" style=\"margin-top:8px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:11px 14px;font-size:12.5px;line-height:1.5\">" +
        "<span class=\"gl\" style=\"color:var(--accent)\">◷</span>" +
        "<span><b>Not-implemented objects link out to GitHub</b> and carry full provenance — but only become tenant-visible components after they’re ingested, license-filtered, and clear the lift gate. Browsing ≠ promoting.</span>" +
      "</div>" +
    "</div>";
  }

  function onMountSources(host, ctx) {
    // Repo link clicks → toast
    var repoLinks = host.querySelectorAll("[data-repo-link]");
    for (var i = 0; i < repoLinks.length; i++) {
      (function (el) {
        el.addEventListener("click", function () {
          ctx.toast("Opens " + el.getAttribute("data-repo-link"));
        });
      })(repoLinks[i]);
    }

    // Ingest buttons → toast
    var ingestBtns = host.querySelectorAll("[data-ingest-repo]");
    for (var j = 0; j < ingestBtns.length; j++) {
      (function (btn) {
        btn.addEventListener("click", function () {
          ctx.toast("Ingest queued → license filter → lift gate → promote");
        });
      })(ingestBtns[j]);
    }

    // Search input — cosmetic; no live filter needed for static data
    var input = host.querySelector("#src-search-input");
    if (input) {
      input.value = "grade suppliers against CSDDD with citations";
    }
  }

  OHH.register("/sources", renderSources, onMountSources, { theme: "dark" });

})();
