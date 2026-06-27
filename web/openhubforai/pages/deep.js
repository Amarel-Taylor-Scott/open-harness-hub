/* OpenHubForAI — deeper surfaces (vanilla ES5-style port of proto-deep.jsx)
   Registers: /foundry  /improve  /dashboards  /settings
   Reads: ctx.data (OpenHubForAI.data), ctx.PRIMS, ctx.esc, ctx.navigate, ctx.toast
   DO NOT edit web/app.js, web/data.js, web/index.html, or any CSS. */
(function () {
  "use strict";

  /* ------------------------------------------------------------------ helpers */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* ================================================================ FOUNDRY */
  var FUNNEL = [
    ["Areas probed",  "gap_screen",             8420, "#fb7714", 100],
    ["Gaps confirmed","measured failures",       2310, "#d29922",  27],
    ["Sources found", "rich veins",             1870, "#3fb950",  22],
    ["Drafts built",  "candidate components",   1440, "#a371f7",  17],
    ["Standardized",  "normal form",            1290, "#58a6ff",  15],
    ["Lift measured", "bare vs pipeline",       1290, "#39c5cf",  15],
  ];
  var REJECTS = [
    ["No measured lift",       920, 100],
    ["Filler / redundant",     410,  45],
    ["Unsourced provenance",   230,  25],
    ["Duplicate of existing",  160,  18],
  ];
  var SOURCES = [
    ["regulation", "EUR-Lex · CSDDD + 40 regs",      "+312"],
    ["dataset",    "HuggingFace governed sets",            "+188"],
    ["repo",       "OSS pipeline ecosystems",              "+96"],
    ["api",        "Standards-body endpoints",             "+54"],
  ];

  function renderFoundry(ctx) {
    var funnelRows = "";
    FUNNEL.forEach(function (row) {
      var lbl = row[0], sub = row[1], n = row[2], c = row[3], pct = row[4];
      funnelRows +=
        '<div class="pt-funnel-row">' +
          '<span class="lbl">' + esc(lbl) + "<small>" + esc(sub) + "</small></span>" +
          '<span class="pt-funnel-bar"><i style="width:' + pct + '%;background:linear-gradient(90deg,color-mix(in srgb,' + c + ' 55%,var(--panel)),' + c + ')">' +
            n.toLocaleString() + "</i></span>" +
          '<span class="rej none">—</span>' +
        "</div>";
    });
    funnelRows +=
      '<div class="pt-funnel-row promoted">' +
        '<span class="lbl">Promoted<small>tenant-visible</small></span>' +
        '<span class="pt-funnel-bar"><i style="width:15%">1,284</i></span>' +
        '<span class="rej none">✓ gate</span>' +
      "</div>";

    var rejRows = "";
    REJECTS.forEach(function (r) {
      rejRows +=
        '<div class="r">' +
          '<span class="nm">' + esc(r[0]) + "</span>" +
          '<span class="bar"><i style="width:' + r[2] + '%"></i></span>' +
          '<span class="ct">' + esc(r[1]) + "</span>" +
        "</div>";
    });

    var srcRows = "";
    SOURCES.forEach(function (s) {
      srcRows +=
        '<div class="pt-source-row">' +
          '<span class="kind">' + esc(s[0]) + "</span>" +
          '<span class="nm">' + esc(s[1]) + "</span>" +
          '<span class="yield">' + esc(s[2]) + "</span>" +
        "</div>";
    });

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          "<h1>Foundry</h1>" +
          '<div class="sub">Evidence-driven component factory — the headline metric is <b>promoted</b>, never generated.</div>' +
        "</div>" +
        '<div class="pt-foundry-top">' +
          '<div class="pt-bigstat hero"><div class="v">1,284</div><div class="k"><b>promoted</b> · cleared the lift gate</div></div>' +
          '<div class="pt-bigstat"><div class="v">8,420</div><div class="k">areas probed</div></div>' +
          '<div class="pt-bigstat"><div class="v">15.2%</div><div class="k">probe → promote rate</div></div>' +
          '<div class="pt-bigstat"><div class="v">$2.1k</div><div class="k">budget burn · this run</div></div>' +
        "</div>" +
        '<div class="pt-row" style="flex-wrap:wrap;gap:16px">' +
          '<div class="pt-panel" style="flex:2 1 460px">' +
            '<div class="oh-cc-id mono" style="margin-bottom:12px">the funnel — narrows to what actually lifts</div>' +
            '<div class="pt-funnel">' + funnelRows + "</div>" +
          "</div>" +
          '<div class="pt-panel" style="flex:1 1 280px">' +
            '<div class="oh-cc-id mono" style="margin-bottom:12px">reject log — by reason</div>' +
            '<div class="pt-rejlog">' + rejRows + "</div>" +
          "</div>" +
        "</div>" +
        '<div class="pt-panel" style="margin-top:16px">' +
          '<div class="oh-cc-id mono" style="margin-bottom:6px">source surfaces — yield (gate-passed components)</div>' +
          srcRows +
        "</div>" +
      "</div>"
    );
  }

  OpenHubForAI.register("/foundry", renderFoundry, null, { theme: "dark" });

  /* ============================================================ IMPORT & IMPROVE */
  var FINDINGS = [
    ["Capability-lift", "high", "Step 3 (“summarize then re-ask”) is something a bare model already does — removable for −1 call with no quality loss."],
    ["Cost",            "high", "Two sequential model calls can collapse into a deterministic Conditional + one harness call. Est. −42% / run."],
    ["Governance",      "high", "No citations or provenance on the legal claims. Swap in the governed CSDDD corpus (✔ sourced)."],
    ["Reliability",     "med",  "No output schema or eval gate — add a rubric pass before returning."],
    ["Reuse",           "med",  "Your hand-rolled entity matcher ≈ processor/entity-resolver (▲ +0.14, MIT). Replace it."],
  ];

  function renderImprove(ctx) {
    var PRIMS = ctx.PRIMS;
    var stepNames = ["Import", "Normalize", "Critique", "Rebuild", "Prove"];
    var stepsHtml = "";
    stepNames.forEach(function (s, i) {
      stepsHtml +=
        '<span class="pt-step' + (i < 3 ? " on" : "") + '">' +
          '<span class="n">' + (i + 1) + "</span>" + esc(s) +
        "</span>";
      if (i < stepNames.length - 1) {
        stepsHtml += '<span class="arr">→</span>';
      }
    });

    // before pipeline: input · action · action · action · action · output
    var beforeKeys = ["input", "action", "action", "action", "action", "output"];
    var beforeNodes = "";
    beforeKeys.forEach(function (k, i) {
      var p = PRIMS[k] || PRIMS.action;
      beforeNodes +=
        '<span class="oh-mininode" style="background:var(' + p.v + ')">' + esc(p.glyph) + "</span>";
      if (i < beforeKeys.length - 1) beforeNodes += '<span class="oh-miniedge"></span>';
    });

    // after pipeline: input · conditional · op · knowledge · action · output
    var afterKeys = ["input", "conditional", "op", "knowledge", "action", "output"];
    var afterNodes = "";
    afterKeys.forEach(function (k, i, a) {
      if (k === "op") {
        afterNodes += '<span class="oh-mininode is-op">◇</span>';
      } else {
        var p = PRIMS[k] || PRIMS.action;
        afterNodes +=
          '<span class="oh-mininode" style="background:var(' + p.v + ')">' + esc(p.glyph) + "</span>";
      }
      if (i < a.length - 1) afterNodes += '<span class="oh-miniedge"></span>';
    });

    var findingsHtml = "";
    FINDINGS.forEach(function (f, i) {
      var lens = f[0], sev = f[1], txt = f[2];
      findingsHtml +=
        '<div class="pt-finding" data-finding-idx="' + i + '">' +
          '<div class="top">' +
            '<span class="lens">' + esc(lens) + "</span>" +
            '<span class="sev ' + esc(sev) + '">' + (sev === "high" ? "high impact" : "medium") + "</span>" +
          "</div>" +
          '<div class="rationale">' + esc(txt) + "</div>" +
          '<div class="acts">' +
            '<button class="oh-btn oh-btn--sm oh-btn--ghost" data-accept="' + i + '">Accept fix</button>' +
          "</div>" +
        "</div>";
    });

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          "<h1>Import &amp; Improve</h1>" +
          '<div class="sub">Upload the pipeline you already run — get it critiqued, governed, and measurably improved.</div>' +
        "</div>" +
        '<div class="pt-steps">' + stepsHtml + "</div>" +
        '<div class="pt-improve">' +
          "<div>" +
            '<div class="pt-twin">' +
              '<div class="lbl">Your pipeline — normalized to the seven primitives</div>' +
              '<div class="oh-minidag" style="min-height:0">' + beforeNodes + "</div>" +
              '<div style="font-size:11.5px;color:var(--fg-faint);margin-top:8px">11 steps · 4 model calls · no governance · est. $$$</div>' +
            "</div>" +
            '<div style="font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--fg-faint);margin:14px 0 8px">' +
              'Critique — <span id="improve-count">0</span> fixes selected' +
            "</div>" +
            '<div id="improve-findings">' + findingsHtml + "</div>" +
          "</div>" +
          "<div>" +
            '<div class="pt-deltas">' +
              '<div class="pt-delta"><div class="k">Capability lift</div><div class="v good">▲ +0.37 <span class="was">was +0.00</span></div></div>' +
              '<div class="pt-delta"><div class="k">Cost / run</div><div class="v cost">−42% <span class="was">$$$ → $$</span></div></div>' +
              '<div class="pt-delta"><div class="k">Governance coverage</div><div class="v good">100% <span class="was">was 38%</span></div></div>' +
              '<div class="pt-delta"><div class="k">Steps</div><div class="v">6 <span class="was">was 11</span></div></div>' +
            "</div>" +
            '<div class="pt-twin">' +
              '<div class="lbl">Rebuilt — governed components</div>' +
              '<div class="oh-minidag" style="min-height:0">' + afterNodes + "</div>" +
              '<div style="font-size:11.5px;color:var(--fg-faint);margin-top:8px">6 components · 1 model call · ✔ sourced · est. $$</div>' +
            "</div>" +
            '<div style="display:flex;gap:9px;margin-top:14px">' +
              '<button class="oh-btn oh-btn--primary" style="flex:1;justify-content:center" id="improve-open-flow">Open improved flow →</button>' +
              '<button class="oh-btn oh-btn--ghost" id="improve-export">Export report</button>' +
            "</div>" +
            '<div style="font-size:11.5px;color:var(--fg-muted);margin-top:12px;line-height:1.5">' +
              'Deltas are <b style="color:var(--fg)">measured</b> on your sample inputs — the same engine that gates the foundry. ' +
              'Your hand-rolled steps that clear the lift gate can be offered back as components (you earn credits).' +
            "</div>" +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  function onMountImprove(host, ctx) {
    var accepted = { 0: true, 1: true, 2: true };

    function updateCount() {
      var n = 0;
      Object.keys(accepted).forEach(function (k) { if (accepted[k]) n++; });
      var el = host.querySelector("#improve-count");
      if (el) el.textContent = n;
    }

    function updateFindingEl(idx) {
      var el = host.querySelector('[data-finding-idx="' + idx + '"]');
      if (!el) return;
      var on = !!accepted[idx];
      if (on) {
        el.classList.add("accepted");
      } else {
        el.classList.remove("accepted");
      }
      var btn = el.querySelector('[data-accept]');
      if (btn) {
        if (on) {
          btn.className = "oh-btn oh-btn--sm oh-btn--primary";
          btn.textContent = "✓ Accepted";
        } else {
          btn.className = "oh-btn oh-btn--sm oh-btn--ghost";
          btn.textContent = "Accept fix";
        }
      }
    }

    // init state
    Object.keys(accepted).forEach(function (k) { updateFindingEl(parseInt(k, 10)); });
    updateCount();

    // wire accept buttons
    var findingsDiv = host.querySelector("#improve-findings");
    if (findingsDiv) {
      findingsDiv.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-accept]");
        if (!btn) return;
        var idx = parseInt(btn.getAttribute("data-accept"), 10);
        accepted[idx] = !accepted[idx];
        updateFindingEl(idx);
        updateCount();
      });
    }

    var openFlow = host.querySelector("#improve-open-flow");
    if (openFlow) openFlow.addEventListener("click", function () { ctx.navigate("/flow"); });

    var exportBtn = host.querySelector("#improve-export");
    if (exportBtn) exportBtn.addEventListener("click", function () { ctx.toast("Critique report exported (PDF)"); });
  }

  OpenHubForAI.register("/improve", renderImprove, onMountImprove, { theme: "dark" });

  /* ============================================================ DASHBOARDS */
  function buildSparkSVG(pts, color) {
    var max = Math.max.apply(null, pts);
    var min = Math.min.apply(null, pts);
    var range = max - min || 1;
    var points = pts.map(function (p, i) {
      return (i / (pts.length - 1)) * 100 + "," + (54 - ((p - min) / range) * 48 - 3);
    }).join(" ");
    return (
      '<svg class="pt-spark" viewBox="0 0 100 54" preserveAspectRatio="none">' +
        '<polyline points="' + points + '" fill="none" stroke="' + (color || "var(--accent)") + '" stroke-width="2" vector-effect="non-scaling-stroke"/>' +
      "</svg>"
    );
  }

  var TOP_COMPS = [
    ["harness/esg-cite-first",          "1.2k", "▲ +0.41"],
    ["knowledge-corpus/csddd-articles", "980",  "▲ +0.18"],
    ["conditional/tier-risk-gate",      "640",  "▲ +0.09"],
  ];

  function renderDashboards(ctx) {
    var spendSpark = buildSparkSVG([12, 15, 11, 18, 16, 22, 19], null);
    var liftSpark  = buildSparkSVG([41, 41, 40, 39, 38, 38, 37], "var(--warning)");

    var topCompsHtml = "";
    TOP_COMPS.forEach(function (row) {
      topCompsHtml +=
        '<div class="pt-statuslight" style="justify-content:space-between">' +
          '<span class="mono" style="font-family:var(--font-mono);font-size:11px">' + esc(row[0]) + "</span>" +
          '<span style="color:var(--fg-muted)">' + esc(row[1]) + ' runs · <span style="color:var(--success)">' + esc(row[2]) + "</span></span>" +
        "</div>";
    });

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          "<h1>Dashboards</h1>" +
          '<div class="sub">Composed from widgets bound to <b>component-generated data stores</b> — monitoring &amp; graphs your components emit themselves.</div>' +
        "</div>" +
        '<div class="pt-widgets">' +
          /* single-cell widgets */
          '<div class="pt-widget">' +
            '<div class="wh">Runs · 7d<span class="src">runs/ledger</span></div>' +
            '<div class="metric">3,182</div>' +
            '<div class="sub up">▲ 12% vs prior</div>' +
          "</div>" +
          '<div class="pt-widget">' +
            '<div class="wh">Cost / run<span class="src">cost/store</span></div>' +
            '<div class="metric">$0.031</div>' +
            '<div class="sub down">▼ 8% (cache)</div>' +
          "</div>" +
          '<div class="pt-widget">' +
            '<div class="wh">Cache hit<span class="src">telemetry</span></div>' +
            '<div class="metric">61%</div>' +
            '<div class="sub">prompt + retrieval</div>' +
          "</div>" +
          '<div class="pt-widget">' +
            '<div class="wh">Citations<span class="src">trace/store</span></div>' +
            '<div class="metric">11.4</div>' +
            '<div class="sub">avg / run</div>' +
          "</div>" +
          /* span-2 widgets */
          '<div class="pt-widget span2">' +
            '<div class="wh">Spend by day<span class="src">cost/store</span></div>' +
            spendSpark +
          "</div>" +
          '<div class="pt-widget span2">' +
            '<div class="wh">Lift over time — decay watch<span class="src">measurement engine</span></div>' +
            liftSpark +
            '<div class="sub down">esg-cite-first · −0.04 as base models improve · <b style="color:var(--warning)">watch</b></div>' +
          "</div>" +
          '<div class="pt-widget span2">' +
            '<div class="wh">Dynamic corpora — freshness<span class="src">CDC</span></div>' +
            '<div class="pt-statuslight"><span class="dot" style="background:var(--success)"></span>OFAC / SDN list · fresh · synced 4m ago</div>' +
            '<div class="pt-statuslight"><span class="dot" style="background:var(--warning)"></span>Customs HS codes · stale · 9d</div>' +
            '<div class="pt-statuslight"><span class="dot" style="background:var(--danger)"></span>Legacy sanctions feed · revoked</div>' +
          "</div>" +
          '<div class="pt-widget span2">' +
            '<div class="wh">Top components by usage<span class="src">registry</span></div>' +
            topCompsHtml +
          "</div>" +
          '<button class="pt-widget-add" id="dash-add-widget">+ Add widget</button>' +
        "</div>" +
      "</div>"
    );
  }

  function onMountDashboards(host, ctx) {
    var addBtn = host.querySelector("#dash-add-widget");
    if (addBtn) addBtn.addEventListener("click", function () { ctx.toast("Pick a store / saved view to bind"); });
  }

  OpenHubForAI.register("/dashboards", renderDashboards, onMountDashboards, { theme: "dark" });

  /* ============================================================ SETTINGS */
  var SECTIONS = [
    ["providers", "Model providers"],
    ["deploy",    "Deployment"],
    ["privacy",   "Privacy boundaries"],
    ["advanced",  "Advanced"],
    ["billing",   "Billing & plan"],
  ];

  function renderSettingRow(titleHtml, descHtml, controlHtml) {
    return (
      '<div class="pt-setting-row">' +
        '<div class="info"><div class="t">' + titleHtml + "</div>" +
        (descHtml ? '<div class="d">' + descHtml + "</div>" : "") +
        "</div>" +
        controlHtml +
      "</div>"
    );
  }

  function renderSwitch(key, isOn) {
    return '<span class="pt-switch' + (isOn ? " on" : "") + '" data-switch="' + esc(key) + '"><i></i></span>';
  }

  function renderSeg(id, options, activeIdx) {
    var btns = options.map(function (opt, i) {
      return '<button class="' + (i === activeIdx ? "on" : "") + '" data-seg-opt="' + i + '">' + esc(opt) + "</button>";
    }).join("");
    return '<div class="pt-seg" data-seg-id="' + esc(id) + '">' + btns + "</div>";
  }

  function renderSectionContent(sec) {
    if (sec === "providers") {
      return (
        renderSettingRow("Bring your own keys", "Run on your own provider accounts; we never store completions.", renderSwitch("byok", true)) +
        renderSettingRow("OpenAI", "gpt-class · default for balanced tier", '<input class="pt-keyinput" type="password" value="sk-••••••••••••4f2a" autocomplete="off">') +
        renderSettingRow("Anthropic", "claude-class · default for quality tier", '<input class="pt-keyinput" type="password" value="sk-ant-••••••••9c1b" autocomplete="off">') +
        renderSettingRow("Local · Ollama", "llama-class · for air-gapped / local-first flows", '<span class="oh-badge oh-badge--verified">connected</span>') +
        renderSettingRow("Model-swap default", "Which model new flows assume before you pick.", renderSeg("model-default", ["Cheap", "Balanced", "Quality"], 1)) +
        renderSettingRow("Prompt cache", "Reuse cached prefixes to cut cost.", renderSwitch("cache", true))
      );
    }
    if (sec === "deploy") {
      return (
        renderSettingRow("Deployment target", "Where governed flows run.", renderSeg("deploy-target", ["Cloud", "BYO-cloud", "Air-gapped"], 0)) +
        renderSettingRow("Export targets", "runtime bundle · Terraform · MCP server · Docker · CLI", '<button class="oh-btn oh-btn--ghost oh-btn--sm" id="settings-export-bundle">Download bundle</button>') +
        renderSettingRow("Frozen vs live", "Static / text-op components freeze; code-executing &amp; dynamic corpora recur.", '<span class="oh-badge mono">8 frozen · 3 live</span>')
      );
    }
    if (sec === "privacy") {
      return (
        renderSettingRow("PII redaction gate", "Force a redaction Action before any model call on flagged inputs.", renderSwitch("pii", true)) +
        renderSettingRow("Data residency · EU", "Pin storage &amp; inference to EU regions.", renderSwitch("residency", false)) +
        renderSettingRow("Trust boundary", "Max execution class allowed without review.", renderSeg("trust-boundary", ["static", "text-op", "code"], 1)) +
        renderSettingRow("Simulate by default", "Echo-stub model steps until explicitly run live.", renderSwitch("simulate", false))
      );
    }
    if (sec === "advanced") {
      return (
        renderSettingRow("Default temperature", "Sampling temperature for new harness calls.", '<input class="pt-keyinput" style="min-width:80px" value="0.2">') +
        renderSettingRow("Max output tokens", "Per model call.", '<input class="pt-keyinput" style="min-width:80px" value="2048">') +
        renderSettingRow("Request timeout", "Abort a step after this long.", '<input class="pt-keyinput" style="min-width:80px" value="30s">') +
        renderSettingRow("Retries &amp; backoff", "On transient provider errors.", renderSeg("retries", ["0", "2", "5"], 1)) +
        renderSettingRow("Rate limit · req/min", "Per API key.", '<input class="pt-keyinput" style="min-width:80px" value="600">') +
        renderSettingRow("Batch concurrency", "Parallel items in a map-over-list.", '<input class="pt-keyinput" style="min-width:80px" value="8">') +
        renderSettingRow("Environment secrets", "Injected into code-executing components at run.", '<span class="oh-badge mono">4 set</span>') +
        renderSettingRow("Webhooks", "CDC events · decay flips · gate-blocked.", '<span class="oh-badge mono">2 endpoints</span>')
      );
    }
    if (sec === "billing") {
      return (
        renderSettingRow("Plan", "Pro · $39 / seat / mo · 4 seats", '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/pricing">Change plan</button>') +
        renderSettingRow("Usage add-ons", "source scans · embeddings · eval runs · build-on-demand", '<span class="oh-badge mono">$214 this mo</span>') +
        renderSettingRow("Credits", "Earned from contributed components that passed the gate.", '<span class="oh-badge oh-badge--lift">+ 1,250</span>')
      );
    }
    return "";
  }

  function renderSettings(ctx) {
    var navItems = SECTIONS.map(function (s) {
      return (
        '<button class="' + (s[0] === "providers" ? "on" : "") + '" data-section="' + esc(s[0]) + '">' + esc(s[1]) + "</button>"
      );
    }).join("");

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          "<h1>Settings</h1>" +
          '<div class="sub">Providers, deployment targets, and privacy — the deep config behind every flow.</div>' +
        "</div>" +
        '<div class="pt-settings">' +
          '<nav class="pt-settings-nav" id="settings-nav">' + navItems + "</nav>" +
          '<div class="pt-panel" id="settings-panel">' +
            renderSectionContent("providers") +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  function onMountSettings(host, ctx) {
    var nav   = host.querySelector("#settings-nav");
    var panel = host.querySelector("#settings-panel");
    if (!nav || !panel) return;

    // section switching
    nav.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-section]");
      if (!btn) return;
      var sec = btn.getAttribute("data-section");
      // update nav active
      var navBtns = nav.querySelectorAll("[data-section]");
      navBtns.forEach(function (b) { b.classList.toggle("on", b === btn); });
      // re-render content
      panel.innerHTML = renderSectionContent(sec);
      // re-wire interactive elements inside the new content
      wirePanel(panel, ctx, sec);
    });

    // wire initial section
    wirePanel(panel, ctx, "providers");
  }

  function wirePanel(panel, ctx, sec) {
    // switches: toggle on click
    var switches = panel.querySelectorAll("[data-switch]");
    switches.forEach(function (sw) {
      sw.addEventListener("click", function () {
        sw.classList.toggle("on");
      });
    });

    // segment controls: one active at a time within each pt-seg
    var segs = panel.querySelectorAll(".pt-seg");
    segs.forEach(function (seg) {
      seg.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-seg-opt]");
        if (!btn) return;
        var btns = seg.querySelectorAll("[data-seg-opt]");
        btns.forEach(function (b) { b.classList.remove("on"); });
        btn.classList.add("on");
      });
    });

    // export bundle button (deploy section)
    var exportBtn = panel.querySelector("#settings-export-bundle");
    if (exportBtn) {
      exportBtn.addEventListener("click", function () { ctx.toast("Bundle exported"); });
    }
  }

  OpenHubForAI.register("/settings", renderSettings, onMountSettings, { theme: "dark" });

})();
