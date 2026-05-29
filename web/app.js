/* Open Harness Hub — product front-end core (no-build static implementation of the Claude
   Design handoff). Faithful port of the prototype's Landing (PLanding) + logged-out Preview
   (PPreview); React/Babel is replaced with vanilla DOM per the handoff README. Additional
   screens self-register via OHH.register() from web/pages/*.js (see web/README.md). */
(function () {
  "use strict";

  var PRIMS = {
    input:       { glyph: "⌖", label: "Input",       v: "--p-input" },
    knowledge:   { glyph: "⛁", label: "Knowledge",   v: "--p-knowledge" },
    conditional: { glyph: "◈", label: "Conditional", v: "--p-conditional" },
    action:      { glyph: "⚡", label: "Action",      v: "--p-action" },
    loop:        { glyph: "↻", label: "Loop",        v: "--p-loop" },
    stop:        { glyph: "⊘", label: "Stop",        v: "--p-stop" },
    output:      { glyph: "⎘", label: "Output",      v: "--p-output" }
  };
  var MODALITIES = [["text", "Text", "⌶"], ["image", "Image", "◰"], ["audio", "Audio", "◵"], ["video", "Video", "▷"]];

  var EX_BY_MOD = {
    text: [
      "Detect human-exploitation indicators in a Hong Kong → Philippines recruitment ad",
      "Trace EUDR deforestation risk for a coffee shipment by plot geolocation",
      "Screen a recruitment agency against modern-slavery indicators across 13 languages",
      "Flag CSDDD tier-2 supplier risk and cite the exact articles"
    ],
    image: [
      "Extract line items from a scanned invoice and reconcile the total",
      "Verify a passport photo for tampering and MRZ consistency",
      "Read the series off this revenue chart into a clean CSV",
      "Triage product-line photos for surface defects against a rubric"
    ],
    audio: [
      "Grade a support call against the QA rubric with timestamped citations",
      "Turn this meeting recording into decisions and owners",
      "Structure a dictated patient encounter into a SOAP note",
      "Redact PII from a call recording and log every cut"
    ],
    video: [
      "Index a deposition video into a searchable, cited transcript",
      "Screen CCTV clips for safety incidents and route to EHS",
      "Check a video ad against advertising-standards rules",
      "Auto-chapter a lecture with a cited transcript and glossary"
    ]
  };
  var PLACEHOLDER_BY_MOD = {
    text: "Detect human-exploitation indicators in a recruitment ad posted from Hong Kong to the Philippines…",
    image: "Extract line items from a scanned invoice and reconcile the total against the printed sum…",
    audio: "Grade a 12-minute support call against our QA rubric, with a timestamp behind each deduction…",
    video: "Index this deposition video into a searchable transcript with exhibit links and citations…"
  };

  var FLAGS = { heroVariant: "A" };
  try {
    Object.assign(FLAGS, JSON.parse(localStorage.getItem("ohp-flags") || "{}"));
    var qp = new URLSearchParams(location.search).get("flags");
    if (qp) qp.split(",").forEach(function (k) { var p = k.split(":"); if (p[0]) FLAGS[p[0]] = p[1] === undefined ? true : p[1]; });
  } catch (e) {}
  function useFlag(k) { return FLAGS[k]; }

  var state = { task: sessionStorage.getItem("ohp-task") || "", exMod: "text", loggedIn: false };
  function setTask(v) { state.task = v; try { sessionStorage.setItem("ohp-task", v); } catch (e) {} }

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function token() { return new URLSearchParams(location.search).get("token") || ""; }

  // ---------------- route registry (pages self-register via OHH.register) ----------------
  // pattern supports params: "/c/:slug". opts: { theme:'dark'|'light' } (app pages are dark).
  var ROUTES = [];
  function register(pattern, render, onMount, opts) {
    ROUTES.push({ parts: pattern.split("/"), render: render, onMount: onMount, opts: opts || {}, pattern: pattern });
  }
  function matchRoute(route) {
    var segs = route.split("/");
    for (var i = 0; i < ROUTES.length; i++) {
      var r = ROUTES[i]; if (r.parts.length !== segs.length) continue;
      var params = {}, ok = true;
      for (var j = 0; j < r.parts.length; j++) {
        if (r.parts[j].charAt(0) === ":") params[r.parts[j].slice(1)] = decodeURIComponent(segs[j] || "");
        else if (r.parts[j] !== segs[j]) { ok = false; break; }
      }
      if (ok) return { route: r, params: params };
    }
    return null;
  }
  function ctx(params) {
    return { OHH: window.OHH, PRIMS: PRIMS, esc: esc, navigate: navigate, toast: toast,
             data: (window.OHH && window.OHH.data) || {}, params: params || {}, state: state, useFlag: useFlag };
  }

  // ---------------- theme: app routes dark, marketing light, manual toggle pins ----------------
  var _routeTheme = "light";
  function applyScheme() {
    var root = $("#root");
    var scheme = localStorage.getItem("ohp-scheme") || "s";
    var pin = localStorage.getItem("ohp-theme");            // set only when the user toggles
    var theme = pin || _routeTheme || "light";
    root.className = "oh dir-" + scheme + " theme-" + theme;
  }

  // ---------------- router ----------------
  function currentRoute() { return (location.hash || "#/").slice(1) || "/"; }
  function navigate(p) { if (("#" + p) === location.hash) renderRoute(); else location.hash = "#" + p; }
  function renderDynamic(host, m) {
    try {
      host.innerHTML = m.route.render(ctx(m.params)) || "";
      if (m.route.onMount) m.route.onMount(host, ctx(m.params));
    } catch (err) {
      host.innerHTML = '<div class="pt-page pt-view"><div class="pt-page-head"><h1>Page error</h1>' +
        '<div class="sub">This screen failed to render — <a data-nav="/" style="color:var(--accent);cursor:pointer">back to start</a>.</div></div>' +
        '<pre style="white-space:pre-wrap;color:var(--danger);font:12px var(--font-mono);padding:12px;border:1px solid var(--line);border-radius:8px">' + esc(String((err && err.stack) || err)) + "</pre></div>";
    }
  }
  function renderRoute() {
    var route = currentRoute();
    var statics = $$("#root > [data-route]");
    var staticEl = null, notFound = null;
    statics.forEach(function (el) {
      var r = el.getAttribute("data-route");
      if (r === route) staticEl = el;
      if (r === "404") notFound = el;
    });
    var m = staticEl ? null : matchRoute(route);
    // IMPORTANT: hide via style.display, NOT the [hidden] attribute — .pt-mkt sets display:flex
    // (author CSS) which overrides the UA [hidden]{display:none}, so [hidden] alone won't hide it.
    statics.forEach(function (el) { el.style.display = "none"; });
    var dyn = $("#oh-dynamic"); if (dyn) dyn.style.display = "none";
    _routeTheme = m ? (m.route.opts.theme || "dark") : "light";  // app pages dark, marketing light
    applyScheme();
    if (staticEl) {
      staticEl.style.display = "";
      if (route === "/preview") renderPreview();
    } else if (m && dyn) {
      dyn.style.display = ""; renderDynamic(dyn, m);
    } else if (notFound) {
      notFound.style.display = "";
    }
    window.scrollTo(0, 0);
  }

  // ---------------- toast ----------------
  function toast(msg) {
    var t = document.createElement("div");
    t.className = "oh-toast"; t.textContent = msg;
    t.setAttribute("style", "position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:80;" +
      "background:var(--fg);color:var(--bg);padding:10px 16px;border-radius:var(--r-pill);font-size:13px;box-shadow:var(--e2)");
    document.body.appendChild(t);
    setTimeout(function () { t.style.opacity = "0"; t.style.transition = "opacity .3s"; }, 2200);
    setTimeout(function () { t.remove(); }, 2600);
  }

  // ---------------- LANDING ----------------
  function submit(t) {
    var v = (t != null ? t : ($("#task-entry") ? $("#task-entry").value : state.task) || "").trim();
    if (v.length < 12) {
      var h = $("#entry-hint"); if (h) h.textContent = "Describe the task in a little more detail to build a flow.";
      var ta = $("#task-entry"); if (ta) ta.focus();
      return;
    }
    setTask(v);
    navigate(state.loggedIn ? "/build" : "/preview");
  }
  function renderChips() {
    var wrap = $("#example-chips"); if (!wrap) return;
    wrap.innerHTML = "";
    EX_BY_MOD[state.exMod].forEach(function (c) {
      var b = document.createElement("button");
      b.className = "pt-chip";
      b.innerHTML = '<span class="tri">▸</span>' + esc(c.length > 42 ? c.slice(0, 40) + "…" : c);
      b.addEventListener("click", function () { setTask(c); var ta = $("#task-entry"); if (ta) ta.value = c; submit(c); });
      wrap.appendChild(b);
    });
  }
  function setMod(k) {
    state.exMod = k;
    $$("#mod-tabs .pt-modtab").forEach(function (b) { b.classList.toggle("on", b.getAttribute("data-mod") === k); });
    var ta = $("#task-entry"); if (ta) ta.placeholder = PLACEHOLDER_BY_MOD[k];
    renderChips();
  }
  function buildModTabs() {
    var wrap = $("#mod-tabs"); if (!wrap) return;
    MODALITIES.forEach(function (m) {
      var b = document.createElement("button");
      b.className = "pt-modtab" + (m[0] === state.exMod ? " on" : "");
      b.setAttribute("data-mod", m[0]); b.setAttribute("role", "tab");
      b.innerHTML = '<span class="gl">' + m[2] + "</span>" + m[1];
      b.addEventListener("click", function () { setMod(m[0]); });
      wrap.appendChild(b);
    });
  }
  function initLanding() {
    var h1 = $("#hero-headline");
    if (h1 && useFlag("heroVariant") === "B") h1.innerHTML = "Ship governed AI pipelines.<br />Beat a bare model — on the record.";
    var ta = $("#task-entry");
    if (ta) {
      ta.value = state.task;
      ta.addEventListener("input", function () { setTask(ta.value); var h = $("#entry-hint"); if (h) h.textContent = ""; });
      ta.addEventListener("keydown", function (e) { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit(); });
    }
    var bb = $("#build-btn"); if (bb) bb.addEventListener("click", function () { submit(); });
    buildModTabs();
    renderChips();
  }

  // ---------------- PREVIEW (PPreview) ----------------
  var BUILD_STEPS = ["Parsing the task", "Retrieving vetted components", "Assembling the flow", "Costing & measuring lift"];
  var FLOW_ROWS = [
    ["input", "Supplier list", "⌖ csv · 1,247 rows · processed one item per iteration"],
    ["conditional", "High-risk tier gate", "◈ regex + rule-pack · when tier ≥ 2 → route to review"],
    ["op", "OR — merge branches", "◇ combines the sanctions + sector-risk screens"],
    ["knowledge", "CSDDD article corpus", "⛁ RAG (vector) + exact-id · 13 langs · token-compressed context"],
    ["action", "Cite-first ESG counsel", "⚡ persona + deterministic citation gate · 1 model call"],
    ["loop", "QA / rubric evaluation", "↻ scores vs rubric · re-runs the call until it passes (≤3)"],
    ["output", "Graded dossier", "⎘ PDF + JSON-LD · every claim cited"]
  ];
  var previewTimer = null;
  function primKey(stage) { var k = String(stage || "").toLowerCase().split(/[\s/]/)[0]; return PRIMS[k] ? k : "action"; }
  // one flow row. level 1 = nested ("then" branch) under the preceding Conditional. tag = IF/THEN chip.
  function flowRowHtml(prim, name, sub, level, tag) {
    var isOp = prim === "op";
    var glyph = isOp ? "◇" : (PRIMS[prim] ? PRIMS[prim].glyph : "•");
    var swatch = isOp ? "background:transparent;border:2px solid var(--operator);color:var(--operator)"
                      : "background:var(" + (PRIMS[prim] ? PRIMS[prim].v : "--p-action") + ");color:#fff;border:none";
    var wrap = level ? "position:relative;margin-left:11px;border-left:2px solid var(--line);padding-left:19px"
                     : "position:relative";
    var arm = level ? '<span style="position:absolute;left:0;top:17px;color:var(--fg-faint);font-size:12px">↳</span>' : "";
    var chip = tag ? '<span class="oh-badge ' + (tag === "IF" ? "oh-badge--warn" : "oh-badge--muted") +
      '" style="padding:1px 6px;margin-right:6px;font-family:var(--font-mono);font-size:9.5px">' + tag + "</span>" : "";
    return '<div style="' + wrap + '">' + arm +
      '<div style="display:flex;align-items:flex-start;gap:11px;padding:9px 0;border-bottom:1px solid var(--line)">' +
      '<span style="width:24px;height:24px;border-radius:' + (isOp ? "50%" : "6px") + ';flex:0 0 auto;display:grid;place-items:center;font-size:12px;' + swatch + '">' + glyph + "</span>" +
      '<div style="flex:1;min-width:0"><div style="font-size:13px;font-weight:600;color:var(--fg)">' + chip + esc(name) + "</div>" +
      '<div style="font-family:var(--font-mono);font-size:10.5px;color:var(--fg-muted);margin-top:2px;line-height:1.4">' + esc(sub) + "</div></div></div></div>";
  }
  // render ordered [primKey,name,sub] steps as a TREE: a Conditional opens an indented "then" branch
  // that Knowledge/Action/Loop/Operator steps nest inside (e.g. "if tier≥2 → then add RAG context, then cite").
  function renderFlowRows(rows) {
    var html = "", inBranch = false;
    rows.forEach(function (r) {
      var prim = r[0];
      if (prim === "input" || prim === "output" || prim === "stop") { inBranch = false; html += flowRowHtml(prim, r[1], r[2], 0, null); }
      else if (prim === "conditional") { inBranch = true; html += flowRowHtml(prim, r[1], r[2], 0, "IF"); }
      else { html += flowRowHtml(prim, r[1], r[2], inBranch ? 1 : 0, inBranch ? "THEN" : null); }
    });
    return html;
  }
  function realFlowPanel(d) {
    var rows = [], stages = (d.flow && d.flow.stages) || [];
    stages.forEach(function (st) {
      var key = primKey(st.stage);
      (st.components || []).forEach(function (c) { rows.push([key, c.name, PRIMS[key].label + (c.role ? " · " + c.role : "")]); });
      if (st.operator) rows.push(["op", "OR — merge branches", "Logical operator"]);
    });
    var costUsd = d.cost && d.cost.balanced && d.cost.balanced.per_task_usd;
    var head = rows.length + " steps" + (costUsd != null ? " · est. $" + costUsd + " / run" : "") + (d.llm_used ? " · model-assembled" : " · deterministic selection");
    return '<div class="oh-cc-id mono" style="margin-bottom:10px">assembled flow · ' + head + "</div>" + renderFlowRows(rows);
  }
  function staticFlowPanel() {
    var head = '6 steps · ▲ +0.41 lift · $$ est. / run <span class="oh-badge oh-badge--muted" style="padding:1px 6px">sample</span>';
    return '<div class="oh-cc-id mono" style="margin-bottom:10px">assembled flow · ' + head + "</div>" + renderFlowRows(FLOW_ROWS);
  }
  function renderPreview() {
    var page = $("#preview-page"); if (!page) return;
    clearTimeout(previewTimer);
    var task = state.task || "grade suppliers against CSDDD";
    var step = 0, flowData = null, flowState = "pending";
    fetch("/api/build?task=" + encodeURIComponent(task) + (token() ? "&token=" + encodeURIComponent(token()) : ""))
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (d) { flowData = d; flowState = "loaded"; if (step >= BUILD_STEPS.length) paint(); })
      .catch(function () { flowState = "fallback"; if (step >= BUILD_STEPS.length) paint(); });
    function paint() {
      var done = step >= BUILD_STEPS.length;
      var html = '<div class="pt-page-head"><h1>' + (done ? "Your flow is ready" : "Building your flow…") +
        '</h1><div class="sub mono" style="font-family:var(--font-mono)">“' + esc(task.slice(0, 80)) + '”</div></div>';
      html += '<div class="pt-panel">';
      BUILD_STEPS.forEach(function (s, i) {
        var mark = i < step ? "✓ " : i === step ? "◌ " : "· ", col = i < step ? "var(--fg)" : "var(--fg-faint)";
        html += '<div class="pt-setting-row" style="padding:9px 0"><div class="info"><div class="t" style="color:' + col + '">' + mark + s + "</div></div>" +
          (i < step ? '<span class="oh-badge oh-badge--lift" style="padding:2px 7px">done</span>' : "") + "</div>";
      });
      html += "</div>";
      if (done) {
        var inner = flowState === "loaded" && flowData ? realFlowPanel(flowData)
          : flowState === "fallback" ? staticFlowPanel()
          : '<div class="oh-skel-line" style="width:60%"></div><div class="oh-skel-line" style="width:80%;margin-top:8px"></div><div class="oh-skel-line" style="width:45%;margin-top:8px"></div>';
        html += '<div class="pt-panel" style="margin-top:12px">' + inner + "</div>";
        html += '<div class="oh-state-msg" style="margin-top:12px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:15px 16px;display:block">' +
          '<div style="font-weight:600;color:var(--fg);margin-bottom:4px">Sign up to run it or download the bundle</div>' +
          '<div style="font-size:12.5px;color:var(--fg-muted);margin-bottom:13px;line-height:1.5">Create a free account to run this flow (simulate or live), open it in the builder, or export the open-spec bundle. The spec &amp; export are free.</div>' +
          '<div style="display:flex;gap:9px"><button class="oh-btn oh-btn--primary" data-nav="/signup">Sign up free →</button>' +
          '<button class="oh-btn oh-btn--ghost" data-nav="/signin">Sign in</button></div></div>';
      }
      page.innerHTML = html;
      if (!done) { step += 1; previewTimer = setTimeout(paint, 700); }
    }
    paint();
  }

  // ---------------- scheme + theme switcher ----------------
  var SCHEMES = [["s", "Harness House ★"], ["a", "Warm Editorial"], ["b", "Clinical Mono"], ["c", "Refined Dark"],
    ["d", "Answer-Engine Teal"], ["e", "Blueprint Terminal"], ["f", "Ledger / Governance"], ["g", "Hacker Terminal"], ["h", "Enterprise Slate"]];
  function buildSwitcher() {
    var box = document.createElement("div");
    box.setAttribute("style", "position:fixed;left:14px;bottom:14px;z-index:50;display:flex;gap:6px;align-items:center;" +
      "background:var(--panel);border:1px solid var(--line);border-radius:var(--r-pill);padding:5px 8px;box-shadow:var(--e2);font-size:12px");
    var sel = document.createElement("select");
    sel.setAttribute("aria-label", "Design scheme");
    sel.setAttribute("style", "background:transparent;border:none;color:var(--fg);font:inherit;font-family:var(--font-sans);cursor:pointer;outline:none");
    SCHEMES.forEach(function (s) { var o = document.createElement("option"); o.value = s[0]; o.textContent = s[1]; sel.appendChild(o); });
    sel.value = localStorage.getItem("ohp-scheme") || "s";
    sel.addEventListener("change", function () { localStorage.setItem("ohp-scheme", sel.value); applyScheme(); });
    var tog = document.createElement("button");
    tog.className = "oh-btn oh-btn--ghost oh-btn--sm";
    function curTheme() { return ($("#root").className.indexOf("theme-dark") >= 0) ? "dark" : "light"; }
    function lbl() { return curTheme() === "light" ? "◐ Light" : "◑ Dark"; }
    tog.textContent = lbl();
    tog.addEventListener("click", function () { localStorage.setItem("ohp-theme", curTheme() === "light" ? "dark" : "light"); applyScheme(); tog.textContent = lbl(); });
    box.appendChild(sel); box.appendChild(tog);
    document.body.appendChild(box);
    var obs = new MutationObserver(function () { tog.textContent = lbl(); });
    obs.observe($("#root"), { attributes: true, attributeFilter: ["class"] });
  }

  // ---------------- global nav delegation ----------------
  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-nav]"); if (!t) return;
    e.preventDefault(); navigate(t.getAttribute("data-nav"));
  });

  // ---------------- pages loader: fetch manifest, inject web/pages/*.js, then route ----------------
  function loadPages(done) {
    fetch("pages/manifest.json").then(function (r) { return r.ok ? r.json() : []; }).then(function (list) {
      var i = 0;
      (function next() {
        if (!list || i >= list.length) { done(); return; }
        var s = document.createElement("script");
        s.src = "pages/" + list[i]; s.onload = s.onerror = function () { i++; next(); };
        document.body.appendChild(s);
      })();
    }).catch(function () { done(); });
  }

  // ---------------- boot ----------------
  window.OHH = window.OHH || {};
  Object.assign(window.OHH, { register: register, navigate: navigate, toast: toast, PRIMS: PRIMS, MODALITIES: MODALITIES, esc: esc, renderRoute: renderRoute, state: state });
  applyScheme();
  initLanding();
  buildSwitcher();
  window.addEventListener("hashchange", renderRoute);
  loadPages(function () { renderRoute(); });
})();
