/* OpenHubForAI — value.js
   Ports PFreshness (/freshness) + PAttest (/attest) from proto-value.jsx.
   Vanilla ES5-flavoured JS, no framework, no build step.
   Registers via OpenHubForAI.register(); ctx injected at render time. */

(function () {
  "use strict";

  /* ================================================================
     DATA (mirrors FEEDS / CDC / PROV constants in proto-value.jsx)
     ================================================================ */
  var FEEDS = [
    ["fresh", "EUR-Lex · CSDDD + EU regs",  "gov · eur-lex.europa.eu",  "hourly",  "4m ago",  "18,420"],
    ["fresh", "OFAC / SDN sanctions",        "gov · treasury.gov",       "15 min",  "2m ago",  "9,310"],
    ["fresh", "National gazettes · 27 EU",   "gov · multi-source",       "daily",   "6h ago",  "4,120"],
    ["stale", "EPA / ECHA chemicals",        "gov · echa.europa.eu",     "daily",   "9d ago",  "6,800"],
    ["fresh", "US Customs · HS tariffs",     "gov · cbp.gov",            "weekly",  "3d ago",  "12,040"],
    ["stale", "FDA · GxP guidance",          "gov · fda.gov",            "weekly",  "12d ago", "2,210"]
  ];

  var CDC_ROWS = [
    ["12:04",     "amend",  "CSDDD Art. 8 transposition (DE) updated — 3 facts superseded, flows re-flagged"],
    ["11:40",     "add",    "OFAC SDN — 12 new sanctioned entities added & signed"],
    ["09:15",     "revoke", "2 EPA discharge limits withdrawn — citing flows blocked pending review"],
    ["Yesterday", "verify", "1,204 facts re-checked against source · provenance re-signed"]
  ];

  var PROV = [
    ["knowledge",   "CSDDD article corpus",  "eur-lex.europa.eu",   "verified 2026-05-28"],
    ["knowledge",   "OFAC / SDN list",       "treasury.gov",        "verified 2026-05-28 11:40"],
    ["conditional", "High-risk tier gate",   "rule-pack · MIT",     "reviewed 2026-04-02"],
    ["action",      "Cite-first ESG counsel","harness · 11 citations","gate-passed ▲ +0.41"]
  ];

  var EXPORT_TARGETS = [
    ["📄", "Compliance pack",  "PDF · audit-ready"],
    ["{ }",          "JSON-LD",          "structured + citations"],
    ["🔏", "C2PA manifest",    "signed provenance"],
    ["⚖",       "EU-AI-Act record", "conformity evidence"],
    ["◆",       "SPDX",             "license SBOM"],
    ["↻",       "Runtime bundle",   "freezable layer only"]
  ];

  var SLA_TIERS = [
    ["realtime", "Real-time", "≤ 15 min · CDC push", "Enterprise"],
    ["daily",    "Daily",     "refreshed every 24h",           "Team"],
    ["weekly",   "Weekly",    "refreshed every 7d",            "Pro"]
  ];

  /* ================================================================
     HELPERS
     ================================================================ */
  function stColor(st) {
    if (st === "fresh") return "var(--success)";
    if (st === "stale") return "var(--warning)";
    return "var(--danger)";
  }

  /* ================================================================
     PFreshness — render(ctx)
     ================================================================ */
  function renderFreshness(ctx) {
    var e = ctx.esc;

    /* source rows */
    var feedRows = "";
    for (var fi = 0; fi < FEEDS.length; fi++) {
      var f = FEEDS[fi];
      var st = f[0], nm = f[1], src = f[2], cad = f[3], last = f[4], facts = f[5];
      var checkMark = st === "fresh" ? "✓ " : "⚠ ";
      feedRows +=
        '<div class="pt-fresh-src">' +
          '<span class="d" style="background:' + stColor(st) + '"></span>' +
          '<span class="nm">' + e(nm) + '<small>' + e(src) + '</small></span>' +
          '<span class="mono">↻ ' + e(cad) + '</span>' +
          '<span class="mono">' + e(checkMark) + e(last) + '</span>' +
          '<span class="mono">' + e(facts) + '</span>' +
          '<span class="oh-badge oh-badge--verified" style="padding:2px 7px">✔ signed</span>' +
        '</div>';
    }

    /* CDC rows */
    var cdcRows = "";
    for (var ci = 0; ci < CDC_ROWS.length; ci++) {
      var row = CDC_ROWS[ci];
      cdcRows +=
        '<div class="pt-cdc-row">' +
          '<span class="t">' + e(row[0]) + '</span>' +
          '<span class="chip ' + e(row[1]) + '">' + e(row[1]) + '</span>' +
          '<span class="desc">' + e(row[2]) + '</span>' +
        '</div>';
    }

    /* SLA tiers — daily is selected by default; onMount toggles class */
    var slaTiers = "";
    for (var si = 0; si < SLA_TIERS.length; si++) {
      var tier = SLA_TIERS[si];
      var isOn = tier[0] === "daily";
      slaTiers +=
        '<div class="pt-sla-tier' + (isOn ? ' on' : '') + '" data-sla="' + e(tier[0]) + '">' +
          '<div class="cad">' + e(tier[1]) + '</div>' +
          '<div class="lat">' + e(tier[2]) + '</div>' +
          '<div class="pr">' + e(tier[3]) + '</div>' +
        '</div>';
    }

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          '<h1>Freshness</h1>' +
          '<div class="sub">Verified facts scraped from <b>primary government sources</b> — dated, diff-tracked, and cryptographically signed. This is what an exported snapshot loses.</div>' +
        '</div>' +

        /* big stats */
        '<div class="pt-foundry-top">' +
          '<div class="pt-bigstat hero" style="border-color:var(--verified);box-shadow:0 0 0 1px var(--verified)">' +
            '<div class="v" style="color:var(--verified)">52,900</div>' +
            '<div class="k">verified facts · <b>✔ signed</b></div>' +
          '</div>' +
          '<div class="pt-bigstat"><div class="v">6</div><div class="k">primary sources scraped</div></div>' +
          '<div class="pt-bigstat"><div class="v">99.4%</div><div class="k">fresh within SLA</div></div>' +
          '<div class="pt-bigstat"><div class="v">31</div><div class="k">changes captured · 24h</div></div>' +
        '</div>' +

        /* source scrapers + CDC panels */
        '<div class="pt-row" style="flex-wrap:wrap;gap:16px">' +
          '<div class="pt-panel" style="flex:2 1 460px">' +
            '<div class="oh-cc-id mono" style="margin-bottom:10px">source scrapers — we are the verified publisher</div>' +
            feedRows +
          '</div>' +
          '<div class="pt-panel" style="flex:1 1 280px">' +
            '<div class="oh-cc-id mono" style="margin-bottom:10px">change feed · CDC</div>' +
            cdcRows +
          '</div>' +
        '</div>' +

        /* SLA panel */
        '<div class="pt-panel" style="margin-top:16px">' +
          '<div class="oh-cc-id mono" style="margin-bottom:12px">freshness SLA — you pay for the latency of truth</div>' +
          '<div class="pt-sla">' + slaTiers + '</div>' +
        '</div>' +

        /* moat message */
        '<div class="oh-state-msg" style="margin-top:16px;' +
          'background:color-mix(in srgb,var(--verified) 7%,transparent);' +
          'border:1px solid color-mix(in srgb,var(--verified) 30%,var(--line));' +
          'border-radius:var(--r-md);padding:11px 14px;font-size:12.5px;line-height:1.5">' +
          '<span class="gl" style="color:var(--verified)">🛡</span>' +
          '<span><b>Export the flow, lose the feed.</b> A downloaded corpus is a dated snapshot that decays. ' +
          'The live, signed, diff-tracked stream — and the revocation that pulls dead facts out of your flows — ' +
          'only comes with the subscription. ' +
          '<a style="color:var(--accent);cursor:pointer;font-weight:600" data-nav="/attest">See how it’s attested →</a></span>' +
        '</div>' +
      '</div>'
    );
  }

  /* ================================================================
     PFreshness — onMount(host, ctx)
     ================================================================ */
  function onMountFreshness(host, ctx) {
    var slaTierEls = host.querySelectorAll(".pt-sla-tier");
    for (var i = 0; i < slaTierEls.length; i++) {
      (function (el) {
        el.addEventListener("click", function () {
          for (var j = 0; j < slaTierEls.length; j++) {
            slaTierEls[j].classList.remove("on");
          }
          el.classList.add("on");
        });
      })(slaTierEls[i]);
    }
  }

  /* ================================================================
     PAttest — render(ctx)
     ================================================================ */
  function renderAttest(ctx) {
    var e = ctx.esc;
    var PRIMS = ctx.PRIMS || {};

    /* provenance chain rows */
    var provRows = "";
    for (var pi = 0; pi < PROV.length; pi++) {
      var p = PROV[pi];
      var primKey = p[0];
      var prim = PRIMS[primKey] || {};
      var cssVar = prim.v ? "var(" + prim.v + ")" : "var(--fg-muted)";
      provRows +=
        '<div class="pt-prov-row">' +
          '<span class="pd" style="background:' + cssVar + '"></span>' +
          '<span class="nm">' + e(p[1]) + '<small>' + e(p[2]) + '</small></span>' +
          '<span class="dt">' + e(p[3]) + '</span>' +
        '</div>';
    }

    /* export targets */
    var exportBtns = "";
    for (var ei = 0; ei < EXPORT_TARGETS.length; ei++) {
      var t = EXPORT_TARGETS[ei];
      exportBtns +=
        '<button class="pt-export-btn" data-export-nm="' + e(t[1]) + '">' +
          '<span class="ic">' + e(t[0]) + '</span>' +
          '<span>' + e(t[1]) + '<small>' + e(t[2]) + '</small></span>' +
        '</button>';
    }

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          '<h1>Certified export</h1>' +
          '<div class="sub">Provenance an auditor accepts — every fact dated, sourced, and signed. The attestation is the product, and it renews as the facts do.</div>' +
        '</div>' +

        '<div class="pt-attest">' +

          /* left: certificate card */
          '<div class="pt-cert">' +
            '<div class="pt-seal">✓</div>' +
            '<h3>Provenance attestation</h3>' +
            '<div class="by">Verified by OpenHubForAI</div>' +
            '<div class="crow"><span class="k">Flow</span><span class="v">csddd-grade</span></div>' +
            '<div class="crow"><span class="k">Sourced as of</span><span class="v">2026-05-28</span></div>' +
            '<div class="crow"><span class="k">Valid through</span><span class="v">2026-08-26</span></div>' +
            '<div class="crow"><span class="k">Facts cited</span><span class="v">11 · all signed</span></div>' +
            '<div class="crow"><span class="k">Standard</span><span class="v">C2PA · EU-AI-Act</span></div>' +
            '<div class="hash">sig 0x9c1b7e4a…d2f0a31f</div>' +
            '<button class="oh-btn oh-btn--primary" id="issue-attest-btn" style="width:100%;justify-content:center;margin-top:14px">Issue attestation</button>' +
          '</div>' +

          /* right: provenance chain + export grid + expiry notice */
          '<div>' +
            '<div class="pt-panel">' +
              '<div class="oh-cc-id mono" style="margin-bottom:8px">provenance chain — what’s behind the certificate</div>' +
              provRows +
            '</div>' +

            '<div class="pt-panel" style="margin-top:14px">' +
              '<div class="oh-cc-id mono" style="margin-bottom:10px">export targets</div>' +
              '<div class="pt-export-grid">' + exportBtns + '</div>' +
            '</div>' +

            '<div class="oh-state-msg blocked" style="margin-top:14px;' +
              'background:var(--accent-weak);' +
              'border-color:color-mix(in srgb,var(--accent) 30%,var(--line))">' +
              '<span class="gl" style="color:var(--accent)">◷</span>' +
              '<span><b>Certificates expire.</b> This attestation is valid through <b>2026-08-26</b> — after that, ' +
              'the cited facts may have changed. Renewal re-checks every source against the live feed and re-signs. ' +
              'The freezable layer exports forever; the <b>certified, current</b> layer is the subscription.</span>' +
            '</div>' +
          '</div>' +

        '</div>' +
      '</div>'
    );
  }

  /* ================================================================
     PAttest — onMount(host, ctx)
     ================================================================ */
  function onMountAttest(host, ctx) {
    var issueBtn = host.querySelector("#issue-attest-btn");
    if (issueBtn) {
      issueBtn.addEventListener("click", function () {
        ctx.toast("Attestation issued & signed");
      });
    }

    var exportBtns = host.querySelectorAll(".pt-export-btn");
    for (var i = 0; i < exportBtns.length; i++) {
      (function (btn) {
        btn.addEventListener("click", function () {
          var nm = btn.getAttribute("data-export-nm") || "Export";
          ctx.toast(nm + " exported");
        });
      })(exportBtns[i]);
    }
  }

  /* ================================================================
     REGISTRATION
     ================================================================ */
  OpenHubForAI.register("/freshness", renderFreshness, onMountFreshness, { theme: "dark" });
  OpenHubForAI.register("/attest",    renderAttest,    onMountAttest,    { theme: "dark" });

})();
