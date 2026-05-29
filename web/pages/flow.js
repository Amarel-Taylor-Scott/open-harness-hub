/* Open Harness Hub — /flow page (PFlow: interactive pipeline canvas + inspector drawer)
   Faithful port of PFlow from proto-pages-build.jsx. No build step, no framework, vanilla ES5-
   flavoured JS. Self-registers via OHH.register(). Read web/README.md before editing. */
(function () {
  "use strict";

  // ---------- bezier helper (copied from prototype pbez) ----------
  function pbez(a, b) {
    var dx = Math.max(26, Math.abs(b.x - a.x) * 0.5);
    return "M" + a.x + "," + a.y + " C" + (a.x + dx) + "," + a.y + " " + (b.x - dx) + "," + b.y + " " + b.x + "," + b.y;
  }

  // ---------- liftBadge / provBadge (mirrors proto-store.jsx) ----------
  function liftBadge(c) {
    if (typeof c.lift === "number") return '<span class="oh-badge oh-badge--lift">▲ +' + c.lift.toFixed(2) + "</span>";
    if (c.liftClass) return '<span class="oh-badge oh-badge--lift">▲ ' + c.liftClass + "</span>";
    return '<span class="oh-badge oh-badge--muted">— unproven</span>';
  }
  function provBadge(p) {
    if (p === "verified") return '<span class="oh-badge oh-badge--verified"><span class="gl">&#128737;</span> verified</span>';
    if (p === "sourced") return '<span class="oh-badge oh-badge--verified"><span class="gl">&#10004;</span> sourced</span>';
    return '<span class="oh-badge oh-badge--warn"><span class="gl">&#9888;</span> unsourced</span>';
  }

  // ---------- render ----------
  function render(ctx) {
    var e = ctx.esc;
    var data = ctx.data || {};
    var PFLOW = data.PFLOW || { nodes: [], op: { x: 466, y: 198, w: 84, h: 40 } };
    var PFW = data.PFW || 198;
    var PFH = data.PFH || 84;
    var PRIMS = ctx.PRIMS || {};

    // Node geometry helpers
    var N = {};
    (PFLOW.nodes || []).forEach(function (n) { N[n.id] = n; });
    function R(n) { return { x: n.x + PFW, y: n.y + PFH / 2 }; }
    function L(n) { return { x: n.x, y: n.y + PFH / 2 }; }
    function B(n) { return { x: n.x + PFW / 2, y: n.y + PFH }; }

    var op = PFLOW.op || { x: 466, y: 198, w: 84, h: 40 };
    var opL = { x: op.x, y: op.y + op.h / 2 };
    var opR = { x: op.x + op.w, y: op.y + op.h / 2 };

    // Forward edges (require all nodes to exist)
    var fwdEdges = "";
    if (N.input && N.ct && N.ca && N.kc && N.act && N.ev) {
      var fwdPairs = [
        [R(N.input), L(N.ct)],
        [R(N.input), L(N.ca)],
        [R(N.ct), opL],
        [R(N.ca), opL],
        [opR, L(N.kc)],
        [R(N.kc), L(N.act)],
        [R(N.act), L(N.ev)]
      ];
      fwdPairs.forEach(function (pair) {
        fwdEdges += '<path d="' + pbez(pair[0], pair[1]) + '" />';
      });
    }

    // Pass edge (ev → out, in success color)
    var passEdge = "";
    if (N.ev && N.out) {
      passEdge = '<path d="' + pbez(R(N.ev), L(N.out)) + '" fill="none" stroke="var(--success)" stroke-width="1.6" marker-end="url(#pah)" />';
    }

    // Refine loop edge
    var loopEdge = "";
    if (N.ev && N.act) {
      var evB = B(N.ev), actB = B(N.act);
      var loopD = "M" + evB.x + "," + evB.y + " C" + evB.x + "," + (evB.y + 62) + " " + actB.x + "," + (actB.y + 62) + " " + actB.x + "," + actB.y;
      loopEdge = '<path d="' + loopD + '" fill="none" stroke="var(--p-loop)" stroke-width="1.75" stroke-dasharray="5 3" marker-end="url(#pah)" />';
    }

    // Flow nodes HTML
    var nodesHtml = "";
    (PFLOW.nodes || []).forEach(function (n) {
      var p = PRIMS[n.k] || { glyph: "?", label: n.k, v: "--p-input" };
      var liftHtml = n.lift ? '<span class="flift">&#9650; ' + e(n.lift) + "</span>" : "";
      nodesHtml +=
        '<div class="oh-fnode" data-fnode-id="' + e(n.id) + '"' +
        ' style="left:' + n.x + "px;top:" + n.y + "px;--nodehue:var(" + p.v + ");cursor:pointer;" +
        '">' +
        '<div class="ftop"><span class="fp">' + e(p.glyph) + " " + e(p.label) + "</span>" +
        '<span class="fsp"></span>' + liftHtml + "</div>" +
        '<div class="fn">' + e(n.name) + "</div>" +
        '<div class="fid">' + e(n.ref) + "</div>" +
        '<div class="ff">' + e(n.facts) + "</div>" +
        "</div>";
    });

    // OR operator node
    var opHtml = "";
    if (op) {
      opHtml = '<div class="oh-fop" style="left:' + op.x + "px;top:" + op.y + "px;width:" + op.w + "px;height:" + op.h + 'px;">&#9671; OR</div>';
    }

    // Model-call label and loop label
    var callLabelHtml = "";
    var loopLabelHtml = "";
    if (N.act) {
      callLabelHtml = '<span class="oh-fcall" style="left:' + (N.act.x + PFW / 2) + "px;top:" + (N.act.y - 24) + 'px;transform:translateX(-50%)">1 model call / item</span>';
    }
    if (N.ev && N.act) {
      var evB2 = B(N.ev), actB2 = B(N.act);
      var lblLeft = ((evB2.x + actB2.x) / 2);
      var lblTop = evB2.y + 48;
      loopLabelHtml = '<span class="oh-flbl loop" style="left:' + lblLeft + "px;top:" + lblTop + 'px;">&#8635; refine &middot; same call &times;N</span>';
    }

    return (
      '<div class="pt-page pt-view" style="display:flex;flex-direction:column;padding:0;overflow:hidden;">' +
      // Toolbar
      '<div class="pt-flow-toolbar">' +
      '<span class="pt-crumb"><b>flow/csddd-grade</b>' +
      '<span class="oh-badge oh-badge--lift" style="margin-left:6px">&#9650; +0.41</span></span>' +
      '<span class="pt-spacer"></span>' +
      '<select class="pt-select" id="ohf-model-sel" title="Model swap">' +
      '<option value="gpt-class">model: gpt-class</option>' +
      '<option value="claude-class">claude-class</option>' +
      '<option value="local-llama">local &middot; llama</option>' +
      "</select>" +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/run">&#9654; Run</button>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" id="ohf-cost-btn">Cost</button>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" id="ohf-save-btn">Save</button>' +
      '<button class="oh-btn oh-btn--primary oh-btn--sm" id="ohf-deploy-btn">Deploy</button>' +
      "</div>" +
      // Canvas + drawer wrapper
      '<div class="pt-flow-wrap" style="flex:1;min-height:0;">' +
      // Canvas host
      '<div class="pt-flow-canvas-host oh-flow" id="ohf-canvas-host">' +
      '<div style="position:relative;width:1480px;height:420px;">' +
      // SVG edges
      '<svg class="oh-flow-svg">' +
      '<defs>' +
      '<marker id="pah" markerWidth="9" markerHeight="9" refX="6.5" refY="3" orient="auto" markerUnits="userSpaceOnUse">' +
      '<path d="M0,0 L7,3 L0,6 Z" fill="context-stroke" />' +
      "</marker>" +
      "</defs>" +
      '<g fill="none" stroke="var(--fg-faint)" stroke-width="1.5" marker-end="url(#pah)" opacity="0.85">' +
      fwdEdges +
      "</g>" +
      passEdge +
      loopEdge +
      "</svg>" +
      // Flow nodes
      nodesHtml +
      // OR operator
      opHtml +
      // Labels
      callLabelHtml +
      loopLabelHtml +
      "</div>" + // end relative inner
      // Validity note
      '<div class="oh-validity" style="position:absolute;">' +
      "<span>&#10003;</span> Single-call pattern &mdash; Conditional routes first, Knowledge feeds one harness call; the refine loop re-runs it. Click any node to inspect or swap." +
      "</div>" +
      "</div>" + // end canvas host
      // Inspector drawer placeholder — injected by onMount when a node is selected
      '<div id="ohf-drawer-slot"></div>' +
      "</div>" + // end pt-flow-wrap
      "</div>" // end pt-page
    );
  }

  // ---------- onMount ----------
  function onMount(host, ctx) {
    var data = ctx.data || {};
    var BY_SLUG = data.BY_SLUG || {};
    var ALTS = data.ALTS || {};
    var PFLOW = data.PFLOW || { nodes: [] };
    var PRIMS = ctx.PRIMS || {};
    var e = ctx.esc;

    // Build a node-id → node map for fast lookup
    var N = {};
    (PFLOW.nodes || []).forEach(function (n) { N[n.id] = n; });

    var drawerSlot = host.querySelector("#ohf-drawer-slot");
    var selId = null;

    // Toolbar buttons
    var costBtn = host.querySelector("#ohf-cost-btn");
    var saveBtn = host.querySelector("#ohf-save-btn");
    var deployBtn = host.querySelector("#ohf-deploy-btn");
    if (costBtn) costBtn.addEventListener("click", function () { ctx.toast("Cost table opened"); });
    if (saveBtn) saveBtn.addEventListener("click", function () { ctx.toast("Flow saved · flow/csddd-grade"); });
    if (deployBtn) deployBtn.addEventListener("click", function () { ctx.toast("Deploy bundle generated"); });

    // Build drawer HTML for a given node id
    function buildDrawer(nodeId) {
      var n = N[nodeId];
      if (!n) return "";
      var p = PRIMS[n.k] || { glyph: "?", label: n.k, v: "--p-input" };
      var comp = n.slug ? BY_SLUG[n.slug] : null;

      var compHtml = "";
      if (comp) {
        var costLabel = e(comp.cost) + (comp.recurring ? "" : " freezable");
        compHtml =
          '<div class="oh-cc-badges">' +
          liftBadge(comp) +
          provBadge(comp.prov) +
          '<span class="oh-badge mono">' + costLabel + "</span>" +
          "</div>" +
          '<p style="font-size:13px;color:var(--fg-muted);line-height:1.5;margin:0;">' + e(comp.desc) + "</p>" +
          '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/c/' + e(comp.slug) + '" style="justify-content:center;">Open component &rarr;</button>';
      } else {
        compHtml = '<p style="font-size:13px;color:var(--fg-muted);">Structural input node.</p>';
      }

      var altsHtml = "";
      var alts = ALTS[nodeId];
      if (alts && alts.length) {
        altsHtml +=
          '<div style="font-size:10px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--fg-faint);margin-top:4px;">Swap &mdash; alternatives by lift</div>';
        alts.forEach(function (a) {
          var borderStyle = a.on ? "border-color:var(--accent);" : "";
          var rightEl = a.on
            ? '<span class="oh-badge oh-badge--lift" style="padding:2px 7px;">in use</span>'
            : '<span style="font-size:11px;color:var(--accent);" class="ohf-swap-btn" data-alt-name="' + e(a.name) + '">swap</span>';
          altsHtml +=
            '<div class="pt-alt ohf-alt-row" style="' + borderStyle + '" data-alt-on="' + (a.on ? "1" : "0") + '" data-alt-name="' + e(a.name) + '">' +
            '<span class="nm">' + e(a.name) + "<small>" + e(a.meta) + "</small></span>" +
            rightEl +
            "</div>";
        });
      }

      return (
        '<aside class="pt-drawer">' +
        '<div class="pt-drawer-hd">' +
        '<button class="pt-drawer-close" id="ohf-drawer-close">&times;</button>' +
        '<div style="font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(' + p.v + ');">' +
        e(p.glyph) + " " + e(p.label) +
        "</div>" +
        '<div style="font-family:var(--font-display);font-size:16px;font-weight:700;color:var(--fg);margin-top:3px;">' + e(n.name) + "</div>" +
        '<div class="mono" style="font-size:11px;color:var(--fg-faint);">' + e(n.ref) + "</div>" +
        "</div>" +
        '<div class="pt-drawer-bd">' +
        compHtml +
        altsHtml +
        "</div>" +
        "</aside>"
      );
    }

    function wireDrawer() {
      if (!drawerSlot) return;

      var closeBtn = drawerSlot.querySelector("#ohf-drawer-close");
      if (closeBtn) {
        closeBtn.addEventListener("click", function () {
          selId = null;
          clearSelection();
          drawerSlot.innerHTML = "";
        });
      }

      // Wire swap buttons
      var swapBtns = drawerSlot.querySelectorAll(".ohf-alt-row");
      swapBtns.forEach(function (row) {
        row.addEventListener("click", function () {
          var altOn = row.getAttribute("data-alt-on");
          var altName = row.getAttribute("data-alt-name");
          if (altOn !== "1") {
            ctx.toast("Swapped → " + altName);
          }
        });
      });
    }

    function clearSelection() {
      var nodes = host.querySelectorAll(".oh-fnode");
      nodes.forEach(function (el) {
        el.style.outline = "none";
      });
    }

    function selectNode(nodeId) {
      selId = nodeId;
      clearSelection();
      // Highlight selected node
      var nodeEl = host.querySelector('[data-fnode-id="' + nodeId + '"]');
      if (nodeEl) {
        nodeEl.style.outline = "2px solid var(--accent)";
        nodeEl.style.outlineOffset = "2px";
      }
      if (drawerSlot) {
        drawerSlot.innerHTML = buildDrawer(nodeId);
        wireDrawer();
      }
    }

    // Wire node click handlers
    var fnodes = host.querySelectorAll(".oh-fnode");
    fnodes.forEach(function (el) {
      el.addEventListener("click", function () {
        var nodeId = el.getAttribute("data-fnode-id");
        if (nodeId) selectNode(nodeId);
      });
    });
  }

  // ---------- register ----------
  window.OHH = window.OHH || {};
  if (window.OHH.register) {
    window.OHH.register("/flow", render, onMount, { theme: "dark" });
  }
})();
