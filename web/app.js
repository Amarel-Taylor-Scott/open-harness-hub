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
  // canonical governed-model-call recipe (offline sample / fallback). Mirrors builder.py
  // harness_recipe: phase = pre|call|post, tier = always|default|optional.
  var STATIC_RECIPE = [
    { phase: "pre", tier: "default", k: "conditional", name: "Trigger gate — does the input qualify?", role: "cheap check the input meets conditions; else short-circuit", builtin: true },
    { phase: "pre", tier: "default", k: "action", name: "Add persona / system prompt", role: "domain-expert framing", ref: "persona/esg-counsel" },
    { phase: "pre", tier: "default", k: "conditional", name: "Add context — regex / knowledge corpus", role: "deterministic pattern + exact-match facts", ref: "rule-pack/tier-risk-gate" },
    { phase: "pre", tier: "default", k: "knowledge", name: "Add context — RAG retrieval", role: "cited facts from the governed corpus", ref: "knowledge-corpus/csddd-articles" },
    { phase: "pre", tier: "optional", k: "action", name: "Call tools", role: "structured calls the model shouldn't guess", builtin: true },
    { phase: "pre", tier: "optional", k: "action", name: "Check online facts / search", role: "verify volatile facts live", builtin: true },
    { phase: "pre", tier: "default", k: "action", name: "Token reduction — format · prioritize · compress", role: "salient first; cut tokens & cost", builtin: true },
    { phase: "pre", tier: "default", k: "stop", name: "Prompt-injection check", role: "block system-prompt extraction / override", builtin: true },
    { phase: "call", tier: "always", k: "action", name: "Call the right-sized model", role: "smallest model that clears the bar + system prompt", ref: "harness/esg-cite-first" },
    { phase: "post", tier: "always", k: "conditional", name: "Check output", role: "validate the answer shape", builtin: true },
    { phase: "post", tier: "default", k: "conditional", name: "Verify JSON (recover if malformed)", role: "parse; repair once if non-JSON", builtin: true },
    { phase: "post", tier: "default", k: "conditional", name: "Re-verify", role: "second pass vs the rubric", ref: "rubric/supplier-grade" },
    { phase: "post", tier: "always", k: "loop", name: "If not OK → retry with changes (≤3)", role: "targeted fixes until it passes, else escalate", ref: "pattern/rubric-refine" }
  ];
  var previewTimer = null;
  function primKey(stage) { var k = String(stage || "").toLowerCase().split(/[\s/]/)[0]; return PRIMS[k] ? k : "action"; }
  var _CHIP = { IF: "oh-badge--warn", ALWAYS: "oh-badge--verified", DEFAULT: "oh-badge--lift", OPTIONAL: "oh-badge--muted" };
  // one flow row. level 1 = nested under a phase header. tag = a chip (ALWAYS/DEFAULT/OPTIONAL/IF).
  function flowRowHtml(prim, name, sub, level, tag) {
    var isOp = prim === "op";
    var glyph = isOp ? "◇" : (PRIMS[prim] ? PRIMS[prim].glyph : "•");
    var swatch = isOp ? "background:transparent;border:2px solid var(--operator);color:var(--operator)"
                      : "background:var(" + (PRIMS[prim] ? PRIMS[prim].v : "--p-action") + ");color:#fff;border:none";
    var wrap = level ? "position:relative;margin-left:11px;border-left:2px solid var(--line);padding-left:19px"
                     : "position:relative";
    var arm = level ? '<span style="position:absolute;left:0;top:17px;color:var(--fg-faint);font-size:12px">↳</span>' : "";
    var chip = tag ? '<span class="oh-badge ' + (_CHIP[tag] || "oh-badge--muted") +
      '" style="padding:1px 6px;margin-right:6px;font-family:var(--font-mono);font-size:9.5px">' + esc(tag) + "</span>" : "";
    return '<div style="' + wrap + '">' + arm +
      '<div style="display:flex;align-items:flex-start;gap:11px;padding:9px 0;border-bottom:1px solid var(--line)">' +
      '<span style="width:24px;height:24px;border-radius:' + (isOp ? "50%" : "6px") + ';flex:0 0 auto;display:grid;place-items:center;font-size:12px;' + swatch + '">' + glyph + "</span>" +
      '<div style="flex:1;min-width:0"><div style="font-size:13px;font-weight:600;color:var(--fg)">' + chip + esc(name) + "</div>" +
      '<div style="font-family:var(--font-mono);font-size:10.5px;color:var(--fg-muted);margin-top:2px;line-height:1.4">' + esc(sub) + "</div></div></div></div>";
  }
  function stageComp(stages, key) {
    for (var i = 0; i < stages.length; i++) {
      if (primKey(stages[i].stage) === key) { var cs = stages[i].components || []; if (cs.length) return cs[0]; }
    }
    return null;
  }
  var _TIERTAG = { always: "ALWAYS", default: "DEFAULT", optional: "OPTIONAL" };
  var _PHASES = [["pre", "Pre-model-call"], ["call", "Model call"], ["post", "Post-model-call"]];
  // Input (always) → phase-grouped recipe (pre/call/post; defaults nested) → Output (always; + metadata + runtime object)
  function recipePanel(head, inputName, inputRole, recipe, outName, outRole) {
    var html = '<div class="oh-cc-id mono" style="margin-bottom:10px">assembled flow · ' + head + "</div>";
    html += flowRowHtml("input", inputName, inputRole, 0, "ALWAYS");
    _PHASES.forEach(function (ph) {
      var steps = recipe.filter(function (s) { return (s.phase || "pre") === ph[0]; });
      if (!steps.length) return;
      html += '<div style="margin:10px 0 1px 30px;font:10px/1.4 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--fg-faint)">' + ph[1] + "</div>";
      steps.forEach(function (s) {
        var sub = (s.ref ? s.ref : (s.role || "")) + (s.builtin ? " · built-in" : "");
        html += flowRowHtml(s.k, s.name, sub, 1, _TIERTAG[s.tier] || null);
      });
    });
    html += flowRowHtml("output", outName, outRole, 0, "ALWAYS");
    return html;
  }
  function realFlowPanel(d) {
    var flow = d.flow || {}, stages = flow.stages || [];
    var recipe = (flow.recipe && flow.recipe.length) ? flow.recipe : STATIC_RECIPE;
    var inputC = stageComp(stages, "input"), outC = stageComp(stages, "output");
    var costUsd = d.cost && d.cost.balanced && d.cost.balanced.per_task_usd;
    var head = (recipe.length + 2) + " steps" + (costUsd != null ? " · est. $" + costUsd + " / run" : "") + (d.llm_used ? " · model-assembled" : " · deterministic selection");
    return recipePanel(head,
      inputC ? inputC.name : "Input", (inputC && inputC.role) ? inputC.role : "what the pipeline runs on at runtime",
      recipe,
      outC ? outC.name : "Findings (JSON) + citations", (outC && outC.role) ? outC.role : "decision + metadata + full runtime object (replayable trace)");
  }
  function staticFlowPanel() {
    var head = (STATIC_RECIPE.length + 2) + ' steps · ▲ +0.41 lift · $$ est. / run <span class="oh-badge oh-badge--muted" style="padding:1px 6px">sample</span>';
    return recipePanel(head, "Recruitment ad / supplier doc", "the text/document the pipeline runs on",
      STATIC_RECIPE, "Decision: yes / no + cited indicators", "decision + metadata + full runtime object (replayable trace)");
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
