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
    logEvent("view · " + route);
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
    logEvent('build requested · "' + v.slice(0, 40) + (v.length > 40 ? "…" : "") + '"');
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
  // canonical governed-model-call recipe (offline sample / fallback). Mirrors builder.py harness_recipe:
  // phase = gate|enrich|polish|verify_query|call|response, tier = always|default|optional, level 1.
  var STATIC_RECIPE = [
    { phase: "gate", tier: "default", level: 1, k: "conditional", name: "Pattern packs — qualify", role: "combinable keyword/regex packs that admit the input", ref: "rule-pack/trafficking-indicators" },
    { phase: "gate", tier: "optional", level: 1, k: "stop", name: "Anti-pattern packs — disqualify", role: "combinable packs that screen the input out (false-positive guards)", builtin: true },
    { phase: "enrich", tier: "default", level: 1, k: "action", name: "Add persona", role: "the role / expertise the model adopts", ref: "persona/exploitation-analyst" },
    { phase: "enrich", tier: "default", level: 1, k: "action", name: "Build the system prompt", role: "instructions + constraints + cite-or-abstain (separate from persona)", builtin: true },
    { phase: "enrich", tier: "optional", level: 1, k: "action", name: "Query transform", role: "close the query↔doc gap", builtin: true, options: ["none", "HyDE", "Query2Doc", "multi-query / RAG-fusion", "decompose", "step-back", "self-query filter"], "default": "none (HyDE for short queries)" },
    { phase: "enrich", tier: "default", level: 1, k: "knowledge", name: "Retrieve", role: "pull candidate facts from the governed corpus", ref: "knowledge-corpus/recruitment-law", options: ["BM25 / keyword", "regex / fuzzy", "exact-id", "dense / RAG (vector)", "SPLADE", "ColBERT", "hybrid"], "default": "hybrid (BM25 + dense)" },
    { phase: "enrich", tier: "optional", level: 1, k: "action", name: "Chunk", role: "split sources into retrievable units (index-time)", builtin: true, options: ["fixed + overlap", "recursive-character", "page / structure-aware", "parent-child", "sentence-window", "semantic"], "default": "recursive-character" },
    { phase: "enrich", tier: "default", level: 1, k: "action", name: "Rerank / fuse", role: "merge legs then rescore the top-k", ref: "processor/cross-encoder-reranker", options: ["RRF", "convex (weighted)", "DBSF", "cross-encoder", "ColBERT", "LLM-rerank", "none"], "default": "RRF → cross-encoder" },
    { phase: "enrich", tier: "optional", level: 1, k: "action", name: "Check online facts / search", role: "verify volatile facts against a live source", builtin: true },
    { phase: "enrich", tier: "optional", level: 1, k: "action", name: "Few-shot exemplars", role: "examples for format / reasoning", builtin: true, options: ["zero-shot", "static k", "dynamic / kNN", "CoT exemplars"], "default": "zero-shot" },
    { phase: "enrich", tier: "default", level: 1, k: "conditional", name: "Output schema", role: "the typed JSON envelope the response is verified against", builtin: true, options: ["free text", "JSON schema in prompt", "constrained / grammar decoding"], "default": "JSON schema in prompt" },
    { phase: "polish", tier: "optional", level: 1, k: "knowledge", name: "Summarize / compress", role: "shrink context to salient cited spans (cut tokens)", builtin: true, options: ["none", "extractive", "contextual compression", "abstractive"], "default": "none → extractive" },
    { phase: "polish", tier: "default", level: 1, k: "action", name: "Select · order · de-conflict", role: "top-k, dedupe, source-precedence, flag contradictions", builtin: true, options: ["top-1", "top-3", "top-k", "MMR (diversity)", "dedupe", "source-precedence", "recency"], "default": "top-k + dedupe + source-precedence" },
    { phase: "polish", tier: "default", level: 1, k: "action", name: "Place context in prompt", role: "mitigate 'lost in the middle'", builtin: true, options: ["concat", "edge (first + last)", "structured / delimited + source tags", "instructions-last"], "default": "structured + edge + instructions-last" },
    { phase: "verify_query", tier: "default", level: 1, k: "stop", name: "Prompt-injection check", role: "block system-prompt extraction / override", builtin: true, options: ["delimit + role-separate", "heuristic / classifier screen", "sanitize retrieved content"], "default": "delimit + screen" },
    { phase: "call", tier: "always", level: 1, k: "action", name: "Call the right-sized model", role: "smallest model that clears the bar + system prompt", ref: "harness/cite-first" },
    { phase: "verify_response", tier: "always", level: 1, k: "conditional", name: "Check output", role: "validate the response against the expected answer shape", builtin: true },
    { phase: "verify_response", tier: "default", level: 1, k: "conditional", name: "Verify JSON (recover if malformed)", role: "parse; repair once if non-JSON", builtin: true },
    { phase: "verify_response", tier: "default", level: 1, k: "conditional", name: "Re-verify", role: "second pass vs the rubric", ref: "rubric/exploitation-grade" },
    { phase: "postprocess", tier: "always", level: 1, k: "loop", name: "If not OK → retry with changes (≤3)", role: "if verification fails, retry with fixes until it passes, else escalate", ref: "pattern/refine-loop" },
    { phase: "postprocess", tier: "always", level: 1, k: "action", name: "Compose result + citations + metadata", role: "extract the decision, attach citations + run metadata, assemble the runtime object", builtin: true },
    { phase: "postprocess", tier: "optional", level: 1, k: "action", name: "Deliver / emit", role: "route the validated result onward", builtin: true, options: ["return", "webhook", "report (md / pdf)", "audit log", "escalate → human"], "default": "return" }
  ];
  var previewTimer = null;
  function primKey(stage) { var k = String(stage || "").toLowerCase().split(/[\s/]/)[0]; return PRIMS[k] ? k : "action"; }
  var _CHIP = { IF: "oh-badge--warn", ALWAYS: "oh-badge--verified", DEFAULT: "oh-badge--lift", OPTIONAL: "oh-badge--muted", META: "oh-badge--muted" };
  // one flow row. level 1 = nested under a phase header. tag = a chip (ALWAYS/DEFAULT/OPTIONAL/IF).
  function flowRowHtml(prim, name, sub, level, tag, opts, defOpt) {
    var isOp = prim === "op";
    var glyph = isOp ? "◇" : (PRIMS[prim] ? PRIMS[prim].glyph : "•");
    var swatch = isOp ? "background:transparent;border:2px solid var(--operator);color:var(--operator)"
                      : "background:var(" + (PRIMS[prim] ? PRIMS[prim].v : "--p-action") + ");color:#fff;border:none";
    var wrap = (level ? "position:relative;margin-left:12px;border-left:1px solid var(--line);padding-left:20px" : "position:relative")
             + (tag === "OPTIONAL" ? ";opacity:.6" : "");   // dim optional steps so the default path stands out
    // tier/relationship chip is RIGHT-aligned + spaced so it never butts the name
    var chip = tag ? '<span class="oh-badge ' + (_CHIP[tag] || "oh-badge--muted") +
      '" style="flex:0 0 auto;margin-left:10px;text-transform:uppercase;letter-spacing:.05em;font-size:9.5px;padding:3px 8px">' + esc(tag) + "</span>" : "";
    // swappable method options for this slot — the chosen DEFAULT is highlighted
    var optsLine = (opts && opts.length)
      ? '<div style="font-family:var(--font-mono);font-size:9.5px;color:var(--fg-faint);margin-top:3px;line-height:1.6">' +
        opts.map(function (o) { return (o === defOpt) ? '<span style="color:var(--accent);font-weight:600">' + esc(o) + " ◂</span>" : esc(o); }).join("  ·  ") + "</div>"
      : "";
    return '<div style="' + wrap + '">' +
      '<div style="display:flex;align-items:flex-start;gap:11px;padding:8px 2px;border-bottom:1px solid var(--line)">' +
      '<span style="margin-top:1px;width:24px;height:24px;border-radius:' + (isOp ? "50%" : "6px") + ';flex:0 0 auto;display:grid;place-items:center;font-size:12px;' + swatch + '">' + glyph + "</span>" +
      '<div style="flex:1;min-width:0">' +
      '<div style="display:flex;align-items:center"><span style="flex:1;min-width:0;font-size:13px;font-weight:600;color:var(--fg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(name) + "</span>" + chip + "</div>" +
      '<div style="font-family:var(--font-mono);font-size:10px;color:var(--fg-faint);margin-top:1px;line-height:1.4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(sub) + "</div>" + optsLine + "</div></div></div>";
  }
  function stageComp(stages, key) {
    for (var i = 0; i < stages.length; i++) {
      if (primKey(stages[i].stage) === key) { var cs = stages[i].components || []; if (cs.length) return cs[0]; }
    }
    return null;
  }
  var _TIERTAG = { always: "ALWAYS", default: "DEFAULT", optional: "OPTIONAL" };
  var _PHASE_LABEL = { gate: "Trigger gate", enrich: "Model query enrichment", polish: "Model query polishing", verify_query: "Model query verification", call: "Model call", verify_response: "Model response verification", postprocess: "Model response post-processing" };
  // Input(L0) → Trigger gate(L0) + its pattern/anti-pattern packs(L1) → Pre/Model/Post phase
  // groups → Output(L0). Each step carries its own level + phase (the backend decides indentation).
  function recipePanel(head, inputName, inputRole, recipe, outName, outType) {
    var html = '<div class="oh-cc-id mono" style="margin-bottom:10px">assembled flow · ' + head + "</div>";
    html += flowRowHtml("input", inputName, inputRole, 0, "ALWAYS");
    var lastPhase = "";
    recipe.forEach(function (s) {
      var ph = s.phase || "pre";
      if (ph !== lastPhase && _PHASE_LABEL[ph]) {   // a clear section divider per phase
        html += '<div style="display:flex;align-items:center;gap:8px;margin:18px 0 6px">' +
          '<span style="font:700 10px/1.4 var(--font-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--accent)">' + _PHASE_LABEL[ph] + "</span>" +
          '<span style="flex:1;height:1px;background:var(--line)"></span></div>';
      }
      lastPhase = ph;
      var sub = (s.ref ? s.ref : (s.role || "")) + (s.builtin ? " · built-in" : "");
      html += flowRowHtml(s.k, s.name, sub, s.level || 0, _TIERTAG[s.tier] || null, s.options, s.default);
    });
    // OUTPUT: the clear, typed decision at top level; cited indicators + the runtime object are INDENTED metadata
    html += '<div style="display:flex;align-items:center;gap:8px;margin:18px 0 6px">' +
      '<span style="font:700 10px/1.4 var(--font-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--accent)">Output</span>' +
      '<span style="flex:1;height:1px;background:var(--line)"></span></div>';
    html += flowRowHtml("output", outName, "output type · " + (outType || "structured"), 0, "ALWAYS");
    html += flowRowHtml("output", "Cited indicators", "per-claim citations into the governed corpus", 1, "META");
    html += flowRowHtml("output", "Full runtime object", "replayable trace — every step, cost & citation", 1, "META");
    return html;
  }
  function realFlowPanel(d) {
    var flow = d.flow || {}, stages = flow.stages || [];
    var recipe = (flow.recipe && flow.recipe.length) ? flow.recipe : STATIC_RECIPE;
    var inputC = stageComp(stages, "input"), outC = stageComp(stages, "output");
    var costUsd = d.cost && d.cost.balanced && d.cost.balanced.per_task_usd;
    var head = (recipe.length + 2) + " steps" + (costUsd != null ? " · est. $" + costUsd + " / run" : "") + (d.llm_used ? " · AI-selected components" : " · deterministic selection");
    return recipePanel(head,
      inputC ? inputC.name : "Input", (inputC && inputC.role) ? inputC.role : "what the pipeline runs on at runtime",
      recipe,
      outC ? outC.name : "Decision", (outC && outC.output_type) ? outC.output_type : "structured (JSON)");
  }
  function staticFlowPanel() {
    var head = (STATIC_RECIPE.length + 2) + ' steps · ▲ +0.41 lift · $$ est. / run <span class="oh-badge oh-badge--muted" style="padding:1px 6px">sample</span>';
    return recipePanel(head, "Recruitment ad", "the document the pipeline runs on at runtime",
      STATIC_RECIPE, "Decision: yes / no", "binary (yes / no)");
  }
  function signupCard() {
    return '<div class="oh-state-msg" style="margin-top:12px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:15px 16px;display:block">' +
      '<div style="font-weight:600;color:var(--fg);margin-bottom:4px">Sign up to run it or download the bundle</div>' +
      '<div style="font-size:12.5px;color:var(--fg-muted);margin-bottom:13px;line-height:1.5">Create a free account to run this flow (simulate or live), open it in the builder, or export the open-spec bundle. The spec &amp; export are free.</div>' +
      '<div style="display:flex;gap:9px"><button class="oh-btn oh-btn--primary" data-nav="/signup">Sign up free →</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/signin">Sign in</button></div></div>';
  }
  // per-task preview state so re-entering /preview never restarts the animation or re-fetches
  var _preview = { task: null, state: "idle", data: null };
  function previewHead(resolved, task) {
    return '<div class="pt-page-head" style="margin-bottom:14px"><h1>' + (resolved ? "Your flow is ready" : "Building your flow…") +
      '</h1><div class="sub mono" style="font-family:var(--font-mono);color:var(--fg-muted)">“' + esc(task.slice(0, 90)) + '”</div></div>';
  }
  function pillBadge(cls, txt) {
    return '<span class="oh-badge ' + cls + '" style="text-transform:uppercase;letter-spacing:.05em;font-size:9.5px;padding:3px 8px">' + txt + "</span>";
  }
  function checklistHtml(doneCount, resolved, secsVal) {
    var html = '<div class="pt-panel" style="padding:6px 16px 12px">';
    BUILD_STEPS.forEach(function (s, i) {
      var done = i < doneCount, active = (i === doneCount && !resolved);
      var mark = done ? "✓" : active ? "◌" : "·";
      var mcol = done ? "var(--success)" : active ? "var(--accent)" : "var(--fg-faint)";
      var col = (i <= doneCount) ? "var(--fg)" : "var(--fg-faint)";
      var clock = (active && i === BUILD_STEPS.length - 1) ? ' <span style="color:var(--fg-faint);font-family:var(--font-mono)">(' + secsVal + "s)</span>" : "";
      var badge = done ? pillBadge("oh-badge--lift", "done") : active ? pillBadge("oh-badge--muted", "working…") : "";
      var prog = '<div class="oh-prog ' + (done ? "is-done" : active ? "is-indet" : "") + '" style="margin-top:8px"><i></i></div>';
      html += '<div style="padding:10px 0' + (i < BUILD_STEPS.length - 1 ? ";border-bottom:1px solid var(--line)" : "") + '">' +
        '<div style="display:flex;align-items:center;gap:9px;font-size:13px;color:' + col + '">' +
        '<span style="width:13px;text-align:center;color:' + mcol + '">' + mark + "</span>" +
        '<span style="flex:1">' + s + clock + "</span>" + badge + "</div>" + prog + "</div>";
    });
    return html + "</div>";
  }
  function previewResultHtml(task, flowData) {
    var inner = flowData ? realFlowPanel(flowData) : staticFlowPanel();
    return previewHead(true, task) + checklistHtml(BUILD_STEPS.length, true, 0) +
      '<div class="pt-panel" style="margin-top:16px">' + inner + "</div>" + signupCard();
  }
  function renderPreview() {
    var page = $("#preview-page"); if (!page) return;
    var task = state.task || "grade suppliers against CSDDD";
    // IDEMPOTENT: re-entering /preview for an already-built task re-renders the result instantly —
    // no animation restart, no re-fetch (this is what was causing the "recycle / start over").
    if (_preview.task === task && _preview.state === "loaded") { page.innerHTML = previewResultHtml(task, _preview.data); return; }
    if (_preview.task === task && _preview.state === "fallback") { page.innerHTML = previewResultHtml(task, null); return; }
    if (_preview.task === task && _preview.state === "pending") return;  // already building this task
    clearTimeout(previewTimer);
    _preview = { task: task, state: "pending", data: null };
    var started = new Date().getTime(), step = 0;
    function secs() { return Math.round((new Date().getTime() - started) / 1000); }
    logEvent("assembling flow · " + task.slice(0, 48));
    fetch("/api/build?task=" + encodeURIComponent(task) + "&narrate=0" + (token() ? "&token=" + encodeURIComponent(token()) : ""))
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (d) {
        if (_preview.task !== task) return;   // task changed mid-flight — ignore stale result
        _preview.state = "loaded"; _preview.data = d; clearTimeout(previewTimer);
        var n = (d.flow && d.flow.recipe) ? (d.flow.recipe.length + 2) : "?";
        logEvent("flow ready · " + n + " steps · " + secs() + "s" + (d.llm_used ? " · AI-selected" : " · deterministic"), "ok");
        page.innerHTML = previewResultHtml(task, d);
      })
      .catch(function () {
        if (_preview.task !== task) return;
        _preview.state = "fallback"; clearTimeout(previewTimer);
        logEvent("build service unreachable — showing sample flow", "warn");
        page.innerHTML = previewResultHtml(task, null);
      });
    function paint() {
      if (_preview.state !== "pending") return;   // resolved — stop the animation loop
      var doneCount = Math.min(step, BUILD_STEPS.length - 1);
      page.innerHTML = previewHead(false, task) + checklistHtml(doneCount, false, secs()) +
        '<div class="oh-state-msg" style="margin-top:12px;display:flex;gap:10px;align-items:center;color:var(--fg-muted);font-size:12.5px;border:1px solid var(--line);border-radius:var(--r-md);padding:12px 14px">' +
        "◌ Contacting the model and assembling the governed flow — the first build can take a moment." +
        '<span style="margin-left:auto;font-family:var(--font-mono);color:var(--fg-faint)">' + secs() + "s</span></div>";
      step = Math.min(step + 1, BUILD_STEPS.length - 1);
      previewTimer = setTimeout(paint, 700);
    }
    paint();
  }

  // ---------------- scheme + theme switcher ----------------
  var SCHEMES = [["s", "Harness House ★"], ["a", "Warm Editorial"], ["b", "Clinical Mono"], ["c", "Refined Dark"],
    ["d", "Answer-Engine Teal"], ["e", "Blueprint Terminal"], ["f", "Ledger / Governance"], ["g", "Hacker Terminal"], ["h", "Enterprise Slate"]];
  function buildSwitcher() {
    var box = document.createElement("div");
    box.setAttribute("style", "position:fixed;right:14px;bottom:50px;z-index:50;display:flex;gap:6px;align-items:center;" +
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

  // ---------------- activity log (a visible bottom console of what the app is doing) ----------------
  var ACTIVITY = [], _actEls = null;
  function _ts() { var d = new Date(); function p(n) { return ("0" + n).slice(-2); } return p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds()); }
  function _lvlDot(l) { var c = l === "error" ? "--danger" : l === "ok" ? "--success" : l === "warn" ? "--warning" : "--accent"; return '<span style="color:var(' + c + ')">●</span> '; }
  function logEvent(msg, level) {
    ACTIVITY.push({ t: _ts(), msg: String(msg), level: level || "info" });
    if (ACTIVITY.length > 200) ACTIVITY.shift();
    renderActivity();
  }
  function renderActivity() {
    if (!_actEls) return;
    var last = ACTIVITY[ACTIVITY.length - 1];
    _actEls.latest.innerHTML = last ? ('<span style="color:var(--fg-faint)">' + last.t + "</span> " + _lvlDot(last.level) + esc(last.msg))
      : '<span style="color:var(--fg-faint)">activity log — build &amp; navigation events appear here</span>';
    _actEls.count.textContent = ACTIVITY.length || "";
    _actEls.count.style.display = ACTIVITY.length ? "inline-block" : "none";
    if (_actEls.open) {
      _actEls.list.innerHTML = ACTIVITY.slice().reverse().map(function (e) {
        return '<div style="padding:2px 0;color:var(--fg-muted)"><span style="color:var(--fg-faint)">' + e.t + "</span> " + _lvlDot(e.level) + esc(e.msg) + "</div>";
      }).join("");
    }
  }
  function buildActivityLog() {
    var bar = document.createElement("div");
    bar.setAttribute("style", "position:fixed;left:0;right:0;bottom:0;z-index:45;background:var(--panel);border-top:1px solid var(--line);font:11.5px/1.5 var(--font-mono)");
    var list = document.createElement("div");
    list.setAttribute("style", "display:none;max-height:168px;overflow-y:auto;padding:8px 16px;border-bottom:1px solid var(--line)");
    var head = document.createElement("div");
    head.setAttribute("style", "display:flex;align-items:center;gap:10px;padding:7px 16px;cursor:pointer");
    var label = document.createElement("span");
    label.setAttribute("style", "display:flex;align-items:center;gap:6px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;font-size:10px;color:var(--fg-muted);flex:0 0 auto");
    var caret = document.createElement("span"); caret.textContent = "▴";
    label.appendChild(caret); label.appendChild(document.createTextNode("Activity"));
    var count = document.createElement("span");
    count.setAttribute("style", "font-size:9px;background:var(--accent-weak);color:var(--accent);border-radius:999px;padding:0 6px;flex:0 0 auto");
    var latest = document.createElement("span");
    latest.setAttribute("style", "flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--fg)");
    head.appendChild(label); head.appendChild(count); head.appendChild(latest);
    bar.appendChild(list); bar.appendChild(head);
    document.body.appendChild(bar);
    document.body.style.paddingBottom = "44px";
    _actEls = { list: list, latest: latest, count: count, open: false };
    function setOpen(o) { _actEls.open = o; list.style.display = o ? "block" : "none"; caret.textContent = o ? "▾" : "▴"; try { localStorage.setItem("ohp-activity-open", o ? "1" : "0"); } catch (e) {} renderActivity(); }
    head.addEventListener("click", function () { setOpen(!_actEls.open); });
    setOpen((function () { try { return localStorage.getItem("ohp-activity-open") === "1"; } catch (e) { return false; } })());
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
  Object.assign(window.OHH, { register: register, navigate: navigate, toast: toast, log: logEvent, PRIMS: PRIMS, MODALITIES: MODALITIES, esc: esc, renderRoute: renderRoute, state: state });
  applyScheme();
  initLanding();
  buildSwitcher();
  buildActivityLog();
  window.addEventListener("hashchange", renderRoute);
  loadPages(function () { logEvent(ACTIVITY.length ? "screens loaded" : "ready"); renderRoute(); });
})();
