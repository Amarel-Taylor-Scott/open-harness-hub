/* Open Harness Hub — Admin portal · Checkout · Internet workers
   Port of proto-admin.jsx to vanilla no-build static JS.
   Registers: /admin · /workers · /checkout (all dark theme).
   Reads ctx.data (OHH.data from data.js); never redeclares shared data. */
(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /*  Static fixture data (self-contained; not in data.js)               */
  /* ------------------------------------------------------------------ */

  var USERS = [
    ["NO", "Nadia Okonkwo",  "nadia@acme.co",  "Owner",   "active"],
    ["JL", "Jonas Lindqvist","jonas@acme.co",  "Admin",   "active"],
    ["PR", "Priya Raman",    "priya@acme.co",  "Builder", "active"],
    ["TW", "Tom Welles",     "tom@acme.co",    "Viewer",  "invited"],
  ];

  var WLOG = [
    ["00:00", "started · goal: refresh CSDDD transposition status (27 member states)", ""],
    ["00:02", "browsing eur-lex.europa.eu/legal-content", "url"],
    ["00:05", "fetched 3 sources · extracting articles", "ok"],
    ["00:08", "browsing national-gazette.de · DE transposition", "url"],
    ["00:11", "license filter → 2 kept, 1 rejected (no redistribution)", ""],
    ["00:14", "dedupe vs existing corpus · 4 new facts", "ok"],
    ["00:17", "lift gate · measuring vs bare model…", ""],
    ["00:21", "promoted 2 facts · provenance signed", "ok"],
  ];

  /* ------------------------------------------------------------------ */
  /*  Helper: safe role select HTML                                       */
  /* ------------------------------------------------------------------ */

  function roleSelect(current) {
    var roles = ["Owner", "Admin", "Builder", "Viewer"];
    var opts = roles.map(function (r) {
      return '<option' + (r === current ? ' selected' : '') + '>' + r + '</option>';
    }).join("");
    return '<select class="pt-select">' + opts + '</select>';
  }

  /* ------------------------------------------------------------------ */
  /*  PAdmin — /admin                                                     */
  /* ------------------------------------------------------------------ */

  function renderAdmin(ctx) {
    var e = ctx.esc;

    /* users tab panel */
    var userRows = USERS.map(function (u) {
      var av = e(u[0]), nm = e(u[1]), em = e(u[2]), role = e(u[3]), st = u[4];
      var stColor = st === "active" ? "var(--success)" : "var(--warning)";
      return (
        "<tr>" +
        "<td><span class=\"av\">" + av + "</span>" + nm +
        "<div style=\"font-family:var(--font-mono);font-size:10.5px;color:var(--fg-faint);margin-left:32px\">" + em + "</div></td>" +
        "<td>" + roleSelect(u[3]) + "</td>" +
        "<td><span class=\"pt-dot-st\"><span class=\"d\" style=\"background:" + stColor + "\"></span>" + e(st) + "</span></td>" +
        "<td style=\"text-align:right\"><span class=\"pt-member-menu\" style=\"color:var(--fg-faint);cursor:pointer\">⋯</span></td>" +
        "</tr>"
      );
    }).join("");

    var tabUsers = (
      "<div class=\"pt-panel\">" +
      "<div class=\"pt-toolbar\"><span style=\"font-size:13px;color:var(--fg-muted)\"><b style=\"color:var(--fg)\">4</b> members · 4 of 6 seats</span><span class=\"pt-spacer\"></span>" +
      "<button class=\"oh-btn oh-btn--primary oh-btn--sm pt-invite-btn\">+ Invite member</button></div>" +
      "<table class=\"pt-table\"><thead><tr><th>Member</th><th>Role</th><th>Status</th><th></th></tr></thead>" +
      "<tbody>" + userRows + "</tbody></table>" +
      "</div>"
    );

    /* credits tab panel */
    var tabCredits = (
      "<div class=\"pt-dash-grid\">" +
      "<div class=\"pt-panel\">" +
      "<div class=\"oh-cc-id mono\" style=\"margin-bottom:10px\">credit balance</div>" +
      "<div style=\"font-family:var(--font-display);font-size:34px;font-weight:700;color:var(--fg)\">8,420 <span style=\"font-size:14px;color:var(--fg-muted)\">credits</span></div>" +
      "<div style=\"font-size:12px;color:var(--fg-muted);margin:4px 0 14px\">≈ $84 · 1,250 earned from contributed components</div>" +
      "<div class=\"pt-toolbar\">" +
      "<button class=\"oh-btn oh-btn--primary oh-btn--sm pt-buy-credits-btn\">Buy credits</button>" +
      "<button class=\"oh-btn oh-btn--ghost oh-btn--sm pt-grant-credits-btn\">Grant to member</button>" +
      "</div></div>" +
      "<div class=\"pt-panel\">" +
      "<div class=\"oh-cc-id mono\" style=\"margin-bottom:10px\">free trials</div>" +
      "<div class=\"pt-setting-row\"><div class=\"info\"><div class=\"t\">Team trial</div><div class=\"d\">14 days · 6 of 14 used · ends May 28</div></div><span class=\"oh-badge oh-badge--warn\">8 days left</span></div>" +
      "<div class=\"pt-setting-row\"><div class=\"info\"><div class=\"t\">Build-on-demand trial</div><div class=\"d\">3 free capability-requests</div></div><span class=\"oh-badge mono\">1 used</span></div>" +
      "<div class=\"pt-setting-row\"><div class=\"info\"><div class=\"t\">Auto-extend for design partners</div><div class=\"d\">Keep trial active past expiry.</div></div><button class=\"oh-btn oh-btn--ghost oh-btn--sm pt-extend-trial-btn\">Extend</button></div>" +
      "</div></div>"
    );

    /* api tab panel — quota bars + key table.
       Quota states: normal (accent), near (warn ≥ ~80%), over (danger ≥ ~95%) */
    var quotas = [
      { label: "Search / recommend",  used: "182k", cap: "250k req", pct: 73,  cls: "" },
      { label: "Pipeline generation", used: "4.1k", cap: "5k req",   pct: 82,  cls: "warn" },
      { label: "Foundry endpoints",   used: "9.6k", cap: "10k req",  pct: 96,  cls: "over" },
      { label: "MCP gateway calls",   used: "54k",  cap: "200k req", pct: 27,  cls: "" },
    ];
    var quotaHtml = quotas.map(function (q) {
      return (
        "<div class=\"pt-quota\">" +
        "<div class=\"row\"><span>" + e(q.label) + "</span><b>" + e(q.used) + " / " + e(q.cap) + "</b></div>" +
        "<div class=\"track\"><i class=\"" + q.cls + "\" style=\"width:" + q.pct + "%\"></i></div>" +
        "</div>"
      );
    }).join("");

    var keyRows = [
      { key: "oh_live_••••a31f", scope: "catalog · recommend", rpd: "61.2k", st: "active",    stColor: "var(--success)" },
      { key: "oh_live_••••7c0b", scope: "foundry",                   rpd: "9.6k",  st: "near limit", stColor: "var(--warning)" },
      { key: "oh_test_••••e2d9", scope: "all · sandbox",        rpd: "—", st: "idle",       stColor: "var(--fg-faint)" },
    ];
    var keyHtml = keyRows.map(function (k) {
      return (
        "<tr>" +
        "<td style=\"font-family:var(--font-mono)\">" + e(k.key) + "</td>" +
        "<td>" + e(k.scope) + "</td>" +
        "<td style=\"font-family:var(--font-mono)\">" + e(k.rpd) + "</td>" +
        "<td><span class=\"pt-dot-st\"><span class=\"d\" style=\"background:" + k.stColor + "\"></span>" + e(k.st) + "</span></td>" +
        "</tr>"
      );
    }).join("");

    var tabApi = (
      "<div class=\"pt-panel\">" +
      "<div class=\"oh-cc-id mono\" style=\"margin-bottom:12px\">API usage — this billing period</div>" +
      quotaHtml +
      "<table class=\"pt-table\" style=\"margin-top:18px\">" +
      "<thead><tr><th>API key</th><th>Scope</th><th>Req / day</th><th>Status</th></tr></thead>" +
      "<tbody>" + keyHtml + "</tbody></table>" +
      "</div>"
    );

    /* render all three panels hidden; js in onMount shows active one */
    return (
      "<div class=\"pt-page wide pt-view\">" +
      "<div class=\"pt-page-head\"><h1>Admin</h1><div class=\"sub\">Manage users, credits &amp; trials, and API usage across the workspace.</div></div>" +
      "<div class=\"pt-config-tabs\" style=\"margin-bottom:18px\" id=\"admin-tabs\">" +
      "<button class=\"on\" data-tab=\"users\">Users &amp; roles</button>" +
      "<button data-tab=\"credits\">Credits &amp; trials</button>" +
      "<button data-tab=\"api\">API usage</button>" +
      "</div>" +
      "<div id=\"admin-panel-users\">" + tabUsers + "</div>" +
      "<div id=\"admin-panel-credits\" hidden>" + tabCredits + "</div>" +
      "<div id=\"admin-panel-api\" hidden>" + tabApi + "</div>" +
      "</div>"
    );
  }

  function onMountAdmin(host, ctx) {
    var tabs  = host.querySelectorAll("#admin-tabs button");
    var panels = {
      users:   host.querySelector("#admin-panel-users"),
      credits: host.querySelector("#admin-panel-credits"),
      api:     host.querySelector("#admin-panel-api"),
    };

    function showTab(key) {
      tabs.forEach(function (b) { b.classList.toggle("on", b.getAttribute("data-tab") === key); });
      Object.keys(panels).forEach(function (k) {
        var p = panels[k];
        if (!p) return;
        if (k === key) { p.removeAttribute("hidden"); } else { p.setAttribute("hidden", ""); }
      });
    }

    tabs.forEach(function (b) {
      b.addEventListener("click", function () { showTab(b.getAttribute("data-tab")); });
    });

    /* toolbar buttons */
    var inviteBtn = host.querySelector(".pt-invite-btn");
    if (inviteBtn) inviteBtn.addEventListener("click", function () { ctx.toast("Invite sent"); });

    var buyBtn = host.querySelector(".pt-buy-credits-btn");
    if (buyBtn) buyBtn.addEventListener("click", function () { ctx.navigate("/checkout"); });

    var grantBtn = host.querySelector(".pt-grant-credits-btn");
    if (grantBtn) grantBtn.addEventListener("click", function () { ctx.toast("Granted 500 credits"); });

    var extendBtn = host.querySelector(".pt-extend-trial-btn");
    if (extendBtn) extendBtn.addEventListener("click", function () { ctx.toast("Trial extended 14 days"); });

    /* member menu dots */
    host.querySelectorAll(".pt-member-menu").forEach(function (el) {
      el.addEventListener("click", function () { ctx.toast("Member menu"); });
    });
  }

  /* ------------------------------------------------------------------ */
  /*  PCheckout — /checkout                                              */
  /* ------------------------------------------------------------------ */

  function renderCheckout(ctx) {
    var invoices = [
      ["Apr 2026", "$299", "paid"],
      ["Mar 2026", "$299", "paid"],
      ["Feb 2026", "$39",  "paid"],
    ];
    var invoiceHtml = invoices.map(function (inv) {
      return (
        "<div class=\"pt-invoice\">" +
        "<span style=\"flex:1\">" + ctx.esc(inv[0]) + "</span>" +
        "<span class=\"mono\">" + ctx.esc(inv[1]) + "</span>" +
        "<span class=\"oh-badge oh-badge--lift\" style=\"padding:2px 7px\">" + ctx.esc(inv[2]) + "</span>" +
        "<span class=\"pt-dl-invoice\" style=\"color:var(--accent);cursor:pointer\">↓</span>" +
        "</div>"
      );
    }).join("");

    return (
      "<div class=\"pt-page pt-view\">" +
      "<div class=\"pt-page-head\"><h1>Checkout</h1><div class=\"sub\">Upgrade to Team · billed monthly · cancel anytime.</div></div>" +
      "<div class=\"pt-checkout\">" +

      /* left: payment form */
      "<div class=\"pt-panel\">" +
      "<div class=\"oh-cc-id mono\" style=\"margin-bottom:14px\">payment details</div>" +
      "<div class=\"pt-field\"><label>Cardholder name</label><input value=\"Nadia Okonkwo\" /></div>" +
      "<div class=\"pt-field\"><label>Card number</label><input placeholder=\"1234 5678 9012 3456\" value=\"4242 4242 4242 4242\" /></div>" +
      "<div class=\"pt-field row2\">" +
      "<div><label>Expiry</label><input placeholder=\"MM / YY\" value=\"04 / 28\" /></div>" +
      "<div><label>CVC</label><input placeholder=\"123\" value=\"•••\" /></div>" +
      "</div>" +
      "<div class=\"pt-field\"><label>Billing email</label><input value=\"billing@acme.co\" /></div>" +
      "<div class=\"pt-field row2\">" +
      "<div><label>Country</label><input value=\"Sweden\" /></div>" +
      "<div><label>VAT ID (optional)</label><input placeholder=\"SE••••••••••\" /></div>" +
      "</div>" +
      "<div class=\"pt-card-badge\" style=\"margin-top:4px\">🔒 Payments secured · PCI-DSS · card stored by processor, never by us</div>" +
      "</div>" +

      /* right: summary + invoices */
      "<div>" +
      "<div class=\"pt-summary\">" +
      "<div class=\"oh-cc-id mono\" style=\"margin-bottom:10px\">order summary</div>" +
      "<div class=\"li\"><span class=\"mut\">Team plan · 4 seats</span><span class=\"mono\">$299</span></div>" +
      "<div class=\"li\"><span class=\"mut\">Build-on-demand credits</span><span class=\"mono\">$60</span></div>" +
      "<div class=\"li\"><span class=\"mut\">Annual discount</span><span class=\"mono\" style=\"color:var(--success)\">−$36</span></div>" +
      "<div class=\"li total\"><span>Due today</span><span class=\"mono\">$323 / mo</span></div>" +
      "<button class=\"oh-btn oh-btn--primary pt-pay-btn\" style=\"width:100%;justify-content:center;margin-top:14px\">Pay $323 →</button>" +
      "<div style=\"font-size:11px;color:var(--fg-faint);text-align:center;margin-top:9px\">The open spec, SDK &amp; export stay free. You’re paying for governed components &amp; live knowledge.</div>" +
      "</div>" +
      "<div class=\"pt-panel\" style=\"margin-top:14px\">" +
      "<div class=\"oh-cc-id mono\" style=\"margin-bottom:6px\">recent invoices</div>" +
      invoiceHtml +
      "</div>" +
      "</div>" +

      "</div>" + /* pt-checkout */
      "</div>"
    );
  }

  function onMountCheckout(host, ctx) {
    var payBtn = host.querySelector(".pt-pay-btn");
    if (payBtn) {
      payBtn.addEventListener("click", function () {
        ctx.toast("Payment successful — welcome to Team");
        ctx.navigate("/admin");
      });
    }
    host.querySelectorAll(".pt-dl-invoice").forEach(function (el) {
      el.addEventListener("click", function () { ctx.toast("Invoice downloaded"); });
    });
  }

  /* ------------------------------------------------------------------ */
  /*  PWorkers — /workers                                                */
  /* ------------------------------------------------------------------ */

  function renderWorkers(ctx) {
    var e = ctx.esc;

    /* initial log snapshot (first 3 entries; animation handled in onMount) */
    var logLines = WLOG.slice(0, 3).map(function (entry, i) {
      var t = entry[0], msg = entry[1], kind = entry[2];
      var isCur = (i === 2);
      var prefix = kind === "ok" ? "✓ " : kind === "url" ? "↗ " : "· ";
      var spanClass = kind === "ok" ? "ok" : kind === "url" ? "url" : "";
      var spanTag = spanClass ? ("<span class=\"" + spanClass + "\">") : "<span>";
      return (
        "<div class=\"ln" + (isCur ? " cur" : "") + "\">" +
        "<span class=\"t\">[" + e(t) + "]</span> " + spanTag + prefix + e(msg) + "</span>" +
        "</div>"
      );
    }).join("");
    var cursorLine = "<div class=\"ln cur\" id=\"wlog-cursor\"><span class=\"t\">[live]</span> <span>▇</span></div>";

    return (
      "<div class=\"pt-page wide pt-view\">" +
      "<div class=\"pt-page-head\"><h1>Internet workers</h1><div class=\"sub\">Remote agents that source from the live internet, under the lift &amp; license gate — long-running jobs you can watch, pause, and govern.</div></div>" +

      /* active worker */
      "<div class=\"pt-worker\" id=\"worker-active\">" +
      "<div class=\"wtop\">" +
      "<span class=\"pt-pulse\"></span>" +
      "<span class=\"nm\">esg-scout-01<small>worker · eu-west · sandboxed browser</small></span>" +
      "<span class=\"wstats\">" +
      "<span class=\"s\"><div class=\"v\">14</div><div class=\"k\">sources</div></span>" +
      "<span class=\"s\"><div class=\"v\">6</div><div class=\"k\">promoted</div></span>" +
      "<span class=\"s\"><div class=\"v\">$0.42</div><div class=\"k\">spend</div></span>" +
      "</span>" +
      "</div>" +
      "<div class=\"pt-wlog\" id=\"pt-wlog-main\">" + logLines + cursorLine + "</div>" +
      "<div class=\"pt-wctrl\">" +
      "<button class=\"oh-btn oh-btn--ghost oh-btn--sm pt-pause-btn\">⏸ Pause</button>" +
      "<button class=\"oh-btn oh-btn--ghost oh-btn--sm pt-stop-btn\">⊘ Stop</button>" +
      "<button class=\"oh-btn oh-btn--ghost oh-btn--sm\" data-nav=\"/foundry\">View in foundry →</button>" +
      "<span class=\"pt-spacer\"></span>" +
      "<span style=\"font-size:11.5px;color:var(--fg-faint);align-self:center\">budget ceiling $5 · auto-stops at limit</span>" +
      "</div>" +
      "</div>" +

      /* queued worker */
      "<div class=\"pt-worker\" style=\"opacity:.75\">" +
      "<div class=\"wtop\">" +
      "<span class=\"pt-pulse\" style=\"background:var(--warning);animation:none\"></span>" +
      "<span class=\"nm\">customs-scout-02<small>worker · us-east · queued</small></span>" +
      "<span class=\"wstats\"><span class=\"s\"><div class=\"v\">—</div><div class=\"k\">queued</div></span></span>" +
      "</div>" +
      "<div style=\"font-size:12.5px;color:var(--fg-muted)\">Waiting for a free partition · goal: HS-code updates across 12 jurisdictions.</div>" +
      "</div>" +

      "<div class=\"pt-toolbar\">" +
      "<button class=\"oh-btn oh-btn--primary oh-btn--sm pt-new-worker-btn\">+ New internet worker</button>" +
      "<span style=\"font-size:11.5px;color:var(--fg-faint);align-self:center\">Workers run sandboxed, honor robots.txt &amp; licenses, and everything they find passes the lift gate before it’s promoted.</span>" +
      "</div>" +

      "</div>"
    );
  }

  function onMountWorkers(host, ctx) {
    var pauseBtn = host.querySelector(".pt-pause-btn");
    if (pauseBtn) pauseBtn.addEventListener("click", function () { ctx.toast("Worker paused"); });

    var stopBtn = host.querySelector(".pt-stop-btn");
    if (stopBtn) stopBtn.addEventListener("click", function () { ctx.toast("Worker stopped"); });

    var newBtn = host.querySelector(".pt-new-worker-btn");
    if (newBtn) newBtn.addEventListener("click", function () { ctx.toast("New worker — set a goal, sources & budget"); });

    /* animate log lines — add one entry every ~1500ms */
    var wlogEl = host.querySelector("#pt-wlog-main");
    if (!wlogEl) return;

    var shown = 3; /* already rendered 3 */
    var cursorEl = host.querySelector("#wlog-cursor");

    function appendLine(entry, isFinalCursor) {
      var div = document.createElement("div");
      var t = entry[0], msg = entry[1], kind = entry[2];
      var prefix = kind === "ok" ? "✓ " : kind === "url" ? "↗ " : "· ";
      var spanClass = kind === "ok" ? "ok" : kind === "url" ? "url" : "";
      div.className = "ln";
      div.innerHTML = "<span class=\"t\">[" + t + "]</span> <span class=\"" + spanClass + "\">" + prefix + msg + "</span>";
      /* insert before the cursor line */
      if (cursorEl && cursorEl.parentNode === wlogEl) {
        wlogEl.insertBefore(div, cursorEl);
      } else {
        wlogEl.appendChild(div);
      }
      if (isFinalCursor && cursorEl) {
        cursorEl.style.display = "none";
      }
    }

    var timer = setInterval(function () {
      if (shown >= WLOG.length) {
        clearInterval(timer);
        if (cursorEl) cursorEl.style.display = "none";
        return;
      }
      var isFinal = (shown === WLOG.length - 1);
      appendLine(WLOG[shown], isFinal);
      shown += 1;
    }, 1500);

    /* clean up timer on route change (host is replaced when another route renders) */
    var obs = new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        m.removedNodes.forEach(function (node) {
          if (node === host || node.contains && node.contains(wlogEl)) {
            clearInterval(timer);
            obs.disconnect();
          }
        });
      });
    });
    if (host.parentNode) obs.observe(host.parentNode, { childList: true });
  }

  /* ------------------------------------------------------------------ */
  /*  Registration                                                        */
  /* ------------------------------------------------------------------ */

  var OHH = window.OHH || {};

  OHH.register("/admin",    renderAdmin,    onMountAdmin,    { theme: "dark" });
  OHH.register("/workers",  renderWorkers,  onMountWorkers,  { theme: "dark" });
  OHH.register("/checkout", renderCheckout, onMountCheckout, { theme: "dark" });

}());
