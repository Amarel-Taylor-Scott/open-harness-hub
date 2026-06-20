/* Baltor — animated Context Engine hero. The signature visual + its canonical language, lifted from
   context-engine-hero.html into the main SPA. SINGLE SOURCE of stage copy/colors is web/baltor/stages.json;
   this module fetches it and both renders the rails and drives the canvas palette from it (no re-typed copy).
   Exposes CE.engineHeroBody() (markup, schedules its own mount) for any page, and registers the /engine route.
   Pure front-end, offline, no external deps. Honors prefers-reduced-motion (renders a single static frame). */
(function () {
  "use strict";
  if (typeof window.CE === "undefined" || !window.CE.register) return;
  var CE = window.CE;
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]; }); };

  // single source: stage language + colors
  CE.stagesReady = fetch("stages.json").then(function (r) { return r.ok ? r.json() : null; })
    .then(function (s) { CE.STAGES = s; return s; }).catch(function () { return null; });

  var STYLE_ID = "ce-engine-style";
  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var css = ""
      + ".ce-engine{--bg:#07090c;--ink:#f5f7fa;--muted:#a0a9b8;--quiet:#687386;--line:#262d38;--panel:#10151d;--gold:#d9ae61;--violet:#a47ef7;color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif}"
      + ".ce-engine .visual-shell{width:100%;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--panel);box-shadow:0 24px 48px rgba(0,0,0,.6);display:grid;grid-template-rows:auto 410px;position:relative}"
      + ".ce-engine .visual-shell::before{content:'';position:absolute;inset:0;pointer-events:none;background:linear-gradient(120deg,rgba(217,174,97,.08),transparent 26%,transparent 74%,rgba(164,126,247,.07));z-index:0}"
      + ".ce-engine .visual-shell>*{position:relative;z-index:1}"
      + ".ce-engine .visual-head{padding:22px 26px;border-bottom:1px solid var(--line);display:flex;align-items:flex-end;gap:24px;justify-content:space-between;flex-wrap:wrap}"
      + ".ce-engine .visual-title b{display:block;font-size:24px;line-height:1.05;color:var(--ink)}"
      + ".ce-engine .visual-title span{display:block;margin-top:7px;color:var(--muted);font-size:14px}"
      + ".ce-engine .visual-title::before{content:attr(data-eyebrow);display:block;color:var(--gold);font-size:11px;font-weight:850;text-transform:uppercase;letter-spacing:.1em;margin-bottom:7px}"
      + ".ce-engine .metrics{display:grid;grid-template-columns:repeat(4,max-content);gap:0;border:1px solid var(--line);border-radius:8px;background:rgba(255,255,255,.02);padding:10px 14px;justify-content:space-between;column-gap:18px}"
      + ".ce-engine .metric span{display:block;color:var(--quiet);font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.07em}"
      + ".ce-engine .metric b{display:block;margin-top:2px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:16px;color:var(--ink)}"
      + ".ce-engine .canvas-area{position:relative;background:linear-gradient(180deg,rgba(255,255,255,.016),rgba(0,0,0,.08)),#040609;margin:0 16px 16px;border:1px solid var(--line);border-radius:10px;overflow:hidden;box-shadow:inset 0 0 24px rgba(0,0,0,.55)}"
      + ".ce-engine canvas{display:block;width:100%;height:100%;min-height:410px}"
      + ".ce-engine .zone-labels{pointer-events:none;position:absolute;inset:0;display:grid;grid-template-columns:.62fr .98fr 1.16fr 1.24fr .98fr .62fr;padding-top:16px}"
      + ".ce-engine .zone-label{text-align:center;font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.08em}"
      + ".ce-engine .zone-label b{display:block;font-size:9px;margin-bottom:4px}"
      + ".ce-engine .zone-label span{display:block;color:#6d7480;font-size:10px;font-weight:600;letter-spacing:0;text-transform:none}"
      + ".ce-engine .zone-hover-layer{position:absolute;inset:0;display:grid;grid-template-columns:.62fr .98fr 1.16fr 1.24fr .98fr .62fr;z-index:4}"
      + ".ce-engine .zone-hover{border:0;background:transparent;cursor:pointer}"
      + ".ce-engine .zone-hover:hover,.ce-engine .zone-hover:focus-visible{background:linear-gradient(180deg,rgba(255,255,255,.02),transparent 62%);outline:0;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}"
      + ".ce-engine .stage-detail{width:100%;margin-top:14px;border:1px solid rgba(164,126,247,.28);border-radius:12px;background:linear-gradient(90deg,rgba(164,126,247,.095),rgba(16,21,29,.82) 46%,rgba(16,21,29,.78));box-shadow:0 18px 42px rgba(0,0,0,.28);display:grid;grid-template-columns:minmax(220px,.85fr) minmax(360px,1.15fr) max-content;align-items:center;gap:20px;padding:16px 18px}"
      + ".ce-engine .stage-detail b{display:block;color:#d5c4ff;font-size:14px;text-transform:uppercase;letter-spacing:.08em}"
      + ".ce-engine .stage-detail .sd-sub,.ce-engine .stage-detail .sd-copy{display:block;margin-top:3px;color:var(--muted);font-size:12.5px;line-height:1.42}"
      + ".ce-engine .stage-detail .sd-tags{display:flex;flex-wrap:wrap;gap:7px}"
      + ".ce-engine .stage-detail .sd-tags span{color:#c8b8ff;border:1px solid rgba(164,126,247,.28);background:rgba(255,255,255,.025);border-radius:999px;padding:5px 8px;font-size:11px;line-height:1}"
      + ".ce-engine .rails{width:100%;margin-top:14px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:rgba(16,21,29,.74)}"
      + ".ce-engine .rails-head{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap}"
      + ".ce-engine .rails-head b{display:block;font-size:15px;color:var(--ink)}"
      + ".ce-engine .rails-head span{display:block;color:var(--muted);font-size:12.5px}"
      + ".ce-engine .rail-row{display:grid;grid-template-columns:54px minmax(150px,230px) minmax(280px,1fr) minmax(180px,300px);gap:16px;align-items:center;padding:15px 18px;border-bottom:1px solid rgba(255,255,255,.045);border-left:3px solid var(--rail);background:linear-gradient(90deg,var(--rail-bg),rgba(16,21,29,.6) 36%,rgba(16,21,29,.5))}"
      + ".ce-engine .rail-row:last-child{border-bottom:0}"
      + ".ce-engine .rail-num{width:44px;height:44px;border-radius:11px;display:grid;place-items:center;color:var(--rail);border:1px solid color-mix(in srgb,var(--rail),transparent 40%);background:color-mix(in srgb,var(--rail),transparent 88%);font-family:ui-monospace,Menlo,Consolas,monospace;font-size:15px;font-weight:850}"
      + ".ce-engine .rail-title b{display:block;font-size:14px;color:var(--ink)}"
      + ".ce-engine .rail-title span{display:block;margin-top:4px;color:#a5adba;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.12em}"
      + ".ce-engine .rail-copy{color:var(--muted);font-size:12.5px;line-height:1.48}"
      + ".ce-engine .rail-tags{display:flex;justify-content:flex-end;align-items:center;gap:7px;flex-wrap:wrap}"
      + ".ce-engine .rail-tags span{color:var(--rail);border:1px solid color-mix(in srgb,var(--rail),transparent 74%);background:rgba(255,255,255,.025);border-radius:999px;padding:5px 9px;font-size:11px;line-height:1}"
      + ".ce-engine .rail-foot{padding:12px 18px;color:var(--muted);font-size:12.5px;border-top:1px solid rgba(255,255,255,.045);background:rgba(12,15,22,.72)}"
      + ".ce-engine .rail-foot b{color:var(--gold)}"
      + "@media (max-width:900px){.ce-engine .rail-row{grid-template-columns:46px 1fr}.ce-engine .rail-copy,.ce-engine .rail-tags{grid-column:2}.ce-engine .rail-tags{justify-content:flex-start}.ce-engine .stage-detail{grid-template-columns:1fr}}";
    var el = document.createElement("style");
    el.id = STYLE_ID; el.textContent = css;
    document.head.appendChild(el);
  }

  // markup — schedules its own mount once the DOM (and stages.json) are ready
  CE.engineHeroBody = function () {
    setTimeout(CE.initEngineHero, 0);
    return ''
      + '<div class="ce-engine" id="ceEngine">'
      + '  <div class="visual-shell">'
      + '    <div class="visual-head">'
      + '      <div class="visual-title" id="ceTitle" data-eyebrow="Automated Context Engine"><b>Baltor Context Engine</b><span id="ceTagline">Continuous reconciliation, anti-fragility, enhancement, optimization, and provenance</span></div>'
      + '      <div class="metrics" aria-live="polite" id="ceMetrics"></div>'
      + '    </div>'
      + '    <div class="canvas-area">'
      + '      <canvas id="ceFlowCanvas" aria-hidden="true"></canvas>'
      + '      <div class="zone-labels" id="ceZoneLabels" aria-hidden="true"></div>'
      + '      <div class="zone-hover-layer" id="ceZoneHover"></div>'
      + '    </div>'
      + '  </div>'
      + '  <section class="stage-detail" id="ceStageDetail" aria-label="Stage detail">'
      + '    <div><b id="ceSdTitle">Stage Details</b><span class="sd-sub" id="ceSdSub">Hover over a stage</span></div>'
      + '    <div class="sd-copy" id="ceSdCopy">Move over any vertical stage above to see a concrete example of what Baltor verifies, reconciles, hardens, enriches, optimizes, or serves at that step.</div>'
      + '    <div class="sd-tags" id="ceSdTags"></div>'
      + '  </section>'
      + '  <div class="rails" id="ceRails"></div>'
      + '</div>';
  };

  CE.initEngineHero = function () {
    var canvas = document.getElementById("ceFlowCanvas");
    if (!canvas || canvas.dataset.inited === "1") return;
    canvas.dataset.inited = "1";
    injectStyle();
    CE.stagesReady.then(function (data) {
      if (!data) return;
      buildChrome(data);
      startCanvas(canvas, data);
    });
  };

  function buildChrome(data) {
    var stages = data.stages || [];
    var title = document.getElementById("ceTitle");
    if (title) { title.setAttribute("data-eyebrow", data.eyebrow || "Automated Context Engine"); title.querySelector("b").textContent = data.title || "Baltor Context Engine"; }
    var tg = document.getElementById("ceTagline"); if (tg && data.tagline) tg.textContent = data.tagline;
    var m = document.getElementById("ceMetrics");
    if (m) m.innerHTML = (data.metrics || []).map(function (mx) { return '<div class="metric"><span>' + esc(mx.label) + '</span><b id="ce-m-' + esc(mx.key) + '">' + (mx.key === "state" ? "Ready" : "0") + "</b></div>"; }).join("");
    var zl = document.getElementById("ceZoneLabels");
    if (zl) zl.innerHTML = stages.map(function (s) { return '<div class="zone-label" style="color:' + esc(s.zone_accent) + '"><b>' + esc(s.title) + "</b><span>" + esc(s.zone_sub || s.kind) + "</span></div>"; }).join("");
    var zh = document.getElementById("ceZoneHover");
    if (zh) zh.innerHTML = stages.map(function (s) { return '<button class="zone-hover" type="button" data-stage="' + esc(s.id) + '" aria-label="' + esc(s.title) + '"></button>'; }).join("");
    var rails = document.getElementById("ceRails");
    if (rails) rails.innerHTML =
      '<div class="rails-head"><div><b>Context Wizard Rails</b><span>Six visible context stages explain what the automation is doing before an AI workflow receives a pack.</span></div></div>'
      + stages.map(function (s) {
        return '<div class="rail-row" style="--rail:' + esc(s.accent) + ';--rail-bg:color-mix(in srgb,' + esc(s.accent) + ' 9%,transparent)">'
          + '<div class="rail-num">' + esc(s.num) + "</div>"
          + '<div class="rail-title"><b>' + esc(s.title) + "</b><span>" + esc(s.kind) + "</span></div>"
          + '<div class="rail-copy">' + esc(s.copy) + "</div>"
          + '<div class="rail-tags">' + (s.tags || []).map(function (t) { return "<span>" + esc(t) + "</span>"; }).join("") + "</div></div>";
      }).join("")
      + '<div class="rail-foot"><b>' + esc((data.verification_rail || {}).title || "Continuous verification + adversarial validation") + ':</b> ' + esc((data.verification_rail || {}).long || "") + "</div>";

    // stage-detail hover, language from the single source
    var byId = {}; stages.forEach(function (s) { byId[s.id] = s; });
    var sdT = document.getElementById("ceSdTitle"), sdS = document.getElementById("ceSdSub"), sdC = document.getElementById("ceSdCopy"), sdTags = document.getElementById("ceSdTags");
    function setDetail(id) {
      var s = byId[id];
      if (!s) { return; }
      var d = s.detail || {};
      sdT.textContent = s.title; sdS.textContent = d.subtitle || s.kind; sdC.textContent = d.copy || s.copy;
      sdTags.innerHTML = (d.tags || s.tags || []).map(function (t) { return "<span>" + esc(t) + "</span>"; }).join("");
    }
    Array.prototype.forEach.call(document.querySelectorAll("#ceZoneHover .zone-hover"), function (z) {
      z.addEventListener("mouseenter", function () { setDetail(z.dataset.stage); });
      z.addEventListener("focus", function () { setDetail(z.dataset.stage); });
    });
  }

  // ── canvas particle engine (ported from context-engine-hero.html; palette from stages.json) ──
  function startCanvas(canvas, data) {
    var ctx = canvas.getContext("2d");
    var dpr = window.devicePixelRatio || 1;
    var palette = (data.stages || []).map(function (s) { return s.zone_accent; });
    while (palette.length < 6) palette.push("#64748b");
    var items = [], spawn = 0, solved = 0, hardened = 0, enhanced = 0;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var mEls = {
      conflicts: document.getElementById("ce-m-conflicts"), hardened: document.getElementById("ce-m-hardened"),
      enhanced: document.getElementById("ce-m-enhanced"), state: document.getElementById("ce-m-state")
    };
    function rnd(a, b) { return a + Math.random() * (b - a); }
    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    function ease(v) { return v * v * (3 - 2 * v); }
    function stageColor(i) { return palette[clamp(i, 0, 5)]; }
    function parseHex(h) { var c = h.replace("#", ""); if (c.length === 3) c = c.split("").map(function (x) { return x + x; }).join(""); var v = parseInt(c, 16); return { r: (v >> 16) & 255, g: (v >> 8) & 255, b: v & 255 }; }
    function mix(a, b, t) { var x = parseHex(a), y = parseHex(b); return "rgb(" + Math.round(x.r + (y.r - x.r) * t) + "," + Math.round(x.g + (y.g - x.g) * t) + "," + Math.round(x.b + (y.b - x.b) * t) + ")"; }
    function rgba(h, a) { var c = parseHex(h); return "rgba(" + c.r + "," + c.g + "," + c.b + "," + a + ")"; }
    function zones(w) { var parts = [.62, .98, 1.16, 1.24, .98, .62], tot = parts.reduce(function (a, b) { return a + b; }, 0), x = 0, out = [0]; parts.forEach(function (p) { x += w * (p / tot); out.push(x); }); return out; }
    function sq(x, y, s) { ctx.fillRect(x - s / 2, y - s / 2, s, s); }
    function dia(x, y, s) { ctx.beginPath(); ctx.moveTo(x, y - s); ctx.lineTo(x + s, y); ctx.lineTo(x, y + s); ctx.lineTo(x - s, y); ctx.closePath(); ctx.fill(); }
    function link(x1, y1, x2, y2, c, a) { ctx.save(); ctx.strokeStyle = c; ctx.globalAlpha *= a; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore(); }
    function prism(x, y, s, lift, c) { ctx.save(); ctx.fillStyle = c; ctx.strokeStyle = c; ctx.lineWidth = 1.1; ctx.globalAlpha *= .36; dia(x + lift, y - lift, s); ctx.globalAlpha /= .36; dia(x, y, s); ctx.beginPath(); ctx.moveTo(x, y - s); ctx.lineTo(x + lift, y - lift - s); ctx.moveTo(x + s, y); ctx.lineTo(x + lift + s, y - lift); ctx.moveTo(x, y + s); ctx.lineTo(x + lift, y - lift + s); ctx.moveTo(x - s, y); ctx.lineTo(x + lift - s, y - lift); ctx.stroke(); ctx.restore(); }

    function Item(w, h, seedX) {
      this.x = seedX == null ? -rnd(20, 160) : seedX; this.y = rnd(86, h - 64); this.baseY = this.y;
      this.speed = rnd(.61, 1.06); this.size = rnd(7, 12); this.seed = Math.random() * 1000; this.rotation = rnd(0, Math.PI * 2);
      this.jit = { robust: rnd(-.075, .075), enhance: rnd(-.07, .07), optimize: rnd(-.055, .055), consume: rnd(-.045, .045) };
      this.oa = { x: rnd(-22, 22), y: rnd(-18, 18) }; this.ob = { x: rnd(-22, 22), y: rnd(-18, 18) };
      this.cluster = [{ x: rnd(-30, 28), y: rnd(-26, 26), s: rnd(.5, .72) }, { x: rnd(-28, 30), y: rnd(-26, 26), s: rnd(.46, .68) }, { x: rnd(-26, 24), y: rnd(-24, 24), s: rnd(.44, .64) }];
      this.stage = 0; this.solved = false; this.hardened = false; this.enhanced = false;
    }
    Item.prototype.update = function (w, h, t) {
      var z = zones(w); this.x += this.speed; this.y = this.baseY + Math.sin(t * .002 + this.seed) * 4; this.rotation += .017;
      if (this.x > z[1]) { this.stage = Math.max(this.stage, 1); for (var c = 0; c < this.cluster.length; c++) { this.cluster[c].x *= .93; this.cluster[c].y *= .93; } }
      if (this.x > z[2] - (z[2] - z[1]) * (.18 + this.jit.robust)) { this.stage = Math.max(this.stage, 2); this.oa.x *= .88; this.oa.y *= .88; this.ob.x *= .88; this.ob.y *= .88; if (!this.solved) { this.solved = true; solved++; } if (!this.hardened) { this.hardened = true; hardened++; } }
      if (this.x > z[3] - (z[3] - z[2]) * (.18 + this.jit.enhance)) this.stage = Math.max(this.stage, 3);
      if (this.x > z[4] - (z[4] - z[3]) * (.06 + this.jit.optimize)) { this.stage = Math.max(this.stage, 4); this.size = Math.max(6.4, this.size * .992); if (!this.enhanced) { this.enhanced = true; enhanced++; } }
      if (this.x > z[5] - (z[5] - z[4]) * (.12 + this.jit.consume)) this.stage = Math.max(this.stage, 5);
    };
    function tprog(item, z, into, lead, done, jit) { var pw = z[into] - z[into - 1], cw = z[into + 1] - z[into], s = z[into] - pw * (lead + jit), e = z[into] + cw * (done + jit * .45); return ease(clamp((item.x - s) / Math.max(1, e - s), 0, 1)); }
    Item.prototype.draw = function (t) {
      ctx.save(); var c = stageColor(this.stage), alpha = .74;
      if (this.stage < 2) alpha = .36 + Math.sin(t * .006 + this.seed) * .12;
      ctx.globalAlpha = alpha; ctx.fillStyle = c; ctx.strokeStyle = c;
      if (this.stage < 1) {
        sq(this.x, this.y, this.size); sq(this.x + this.oa.x, this.y + this.oa.y, this.size * .56); sq(this.x + this.ob.x, this.y + this.ob.y, this.size * .52);
        link(this.x, this.y, this.x + this.oa.x, this.y + this.oa.y, c, .3); link(this.x, this.y, this.x + this.ob.x, this.y + this.ob.y, c, .3);
      } else if (this.stage < 2) {
        var z = zones(canvas.width / dpr), p = ease(clamp((this.x - z[1]) / Math.max(1, z[2] - z[1]), 0, 1));
        ctx.globalAlpha *= .86; for (var i = 0; i < this.cluster.length; i++) { var n = this.cluster[i], x = this.x + n.x * (1 - p * .74), y = this.y + n.y * (1 - p * .74); link(x, y, this.x, this.y, c, .22 + p * .24); sq(x, y, this.size * n.s); } sq(this.x, this.y, this.size * (.78 + p * .24));
      } else if (this.stage < 3) { hardenedObj(this, mix(stageColor(1), stageColor(2), 1)); }
      else if (this.stage < 4) { hardenedObj(this, mix(stageColor(2), stageColor(3), .6)); enhancedObj(this); }
      else { packet(this, this.stage >= 5 ? mix(stageColor(4), stageColor(5), .6) : mix(stageColor(3), stageColor(4), .6)); }
      ctx.restore();
    };
    function hardenedObj(item, c) { ctx.save(); ctx.fillStyle = c; ctx.strokeStyle = c; ctx.lineWidth = 1.15; var s = item.size * .94, lift = item.size * .38; ctx.globalAlpha *= .42; sq(item.x + lift, item.y - lift, s); ctx.globalAlpha /= .42; sq(item.x, item.y, s); ctx.beginPath(); ctx.moveTo(item.x - s / 2, item.y - s / 2); ctx.lineTo(item.x + lift - s / 2, item.y - lift - s / 2); ctx.moveTo(item.x + s / 2, item.y - s / 2); ctx.lineTo(item.x + lift + s / 2, item.y - lift - s / 2); ctx.moveTo(item.x + s / 2, item.y + s / 2); ctx.lineTo(item.x + lift + s / 2, item.y - lift + s / 2); ctx.stroke(); ctx.restore(); }
    function enhancedObj(item) { ctx.save(); var c = stageColor(3); ctx.fillStyle = c; var n = 4; for (var i = 0; i < n; i++) { var a = item.rotation + Math.PI * 2 * i / n, d = item.size * 1.5; ctx.globalAlpha = .7; dia(item.x + Math.cos(a) * d, item.y + Math.sin(a) * d * .8, item.size * .3); link(item.x, item.y, item.x + Math.cos(a) * d, item.y + Math.sin(a) * d * .8, c, .25); } ctx.restore(); }
    function packet(item, c) { ctx.save(); ctx.translate(item.x, item.y); ctx.rotate(item.rotation); prism(0, 0, item.size * .82, item.size * .22, c); ctx.strokeStyle = c; ctx.globalAlpha *= .5; ctx.setLineDash([3, 6]); ctx.beginPath(); ctx.arc(0, 0, item.size * 1.5, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]); ctx.restore(); }

    function bg(w, h) {
      var z = zones(w);
      for (var i = 0; i < 6; i++) { ctx.fillStyle = rgba(stageColor(i), i === 0 || i === 5 ? .038 : .047); ctx.fillRect(z[i], 0, z[i + 1] - z[i], h); if (i > 0) { ctx.strokeStyle = "rgba(255,255,255,.07)"; ctx.setLineDash([4, 6]); ctx.beginPath(); ctx.moveTo(z[i], 0); ctx.lineTo(z[i], h); ctx.stroke(); ctx.setLineDash([]); } }
      var y = h - 17; ctx.save(); ctx.fillStyle = "rgba(164,126,247,.055)"; ctx.fillRect(0, y - 15, w, 34); ctx.strokeStyle = "rgba(164,126,247,.24)"; ctx.setLineDash([5, 7]); ctx.beginPath(); ctx.moveTo(0, y - 15); ctx.lineTo(w, y - 15); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = "rgba(213,196,255,.92)"; ctx.font = "800 10px Inter,system-ui,sans-serif"; ctx.textAlign = "center"; ctx.fillText(((data.verification_rail || {}).title || "CONTINUOUS VERIFICATION + ADVERSARIAL VALIDATION").toUpperCase(), w / 2, y - 1);
      ctx.fillStyle = "rgba(160,169,184,.74)"; ctx.font = "600 10px Inter,system-ui,sans-serif"; ctx.fillText((data.verification_rail || {}).checks || "", w / 2, y + 13); ctx.restore();
    }
    function metrics() { if (mEls.conflicts) mEls.conflicts.textContent = String(solved); if (mEls.hardened) mEls.hardened.textContent = String(hardened); if (mEls.enhanced) mEls.enhanced.textContent = String(enhanced); if (mEls.state) { mEls.state.textContent = "Ready"; mEls.state.style.color = "#d9ae61"; } }
    function resize() { var rect = canvas.getBoundingClientRect(); dpr = window.devicePixelRatio || 1; canvas.width = Math.max(1, Math.round(rect.width * dpr)); canvas.height = Math.max(1, Math.round(rect.height * dpr)); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); }
    function frame(t) {
      if (!document.getElementById("ceFlowCanvas")) return; // route changed away — stop the loop
      var w = canvas.width / dpr, h = canvas.height / dpr; ctx.clearRect(0, 0, w, h); bg(w, h);
      spawn++; if (spawn > 18) { spawn = 0; items.push(new Item(w, h)); }
      for (var i = items.length - 1; i >= 0; i--) { items[i].update(w, h, t); items[i].draw(t); if (items[i].x > w + 120) items.splice(i, 1); }
      metrics(); requestAnimationFrame(frame);
    }
    window.addEventListener("resize", resize); resize();
    var w = canvas.width / dpr, h = canvas.height / dpr;
    for (var i = 0; i < 31; i++) items.push(new Item(w, h, rnd(0, w)));
    if (reduce) { ctx.clearRect(0, 0, w, h); bg(w, h); items.forEach(function (it) { it.update(w, h, 0); it.draw(0); }); metrics(); }
    else requestAnimationFrame(frame);
  }

  // /engine route — the visualization as its own page
  CE.register("/engine", function (ctx) {
    return '<div class="pt-mkt pt-view">' + ctx.header("/engine") +
      '<div class="pt-mkt-body"><div class="pt-page" style="max-width:1180px;margin:0 auto;padding:24px 0">' +
      '<div class="pt-page-head" style="margin-bottom:18px"><div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:8px">The Context Engine</div>' +
      '<h1>Watch context get reconciled, hardened, enriched, optimized, and served.</h1>' +
      '<div class="sub">Six visible stages under one continuous verification rail. Hover any stage to see a concrete example.</div></div>' +
      CE.engineHeroBody() +
      "</div></div></div>";
  });
})();
