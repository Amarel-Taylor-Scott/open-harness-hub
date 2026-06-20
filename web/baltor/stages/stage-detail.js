(function () {
  "use strict";

  var canvas = document.querySelector("[data-stage]");
  if (!canvas) return;
  var stage = canvas.dataset.stage;
  var ctx = canvas.getContext("2d");
  var dpr = 1;

  function css(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  var colors = {
    source: css("--source"),
    green: css("--green"),
    blue: css("--blue"),
    amber: css("--amber"),
    violet: css("--violet")
  };

  function resize() {
    var rect = canvas.getBoundingClientRect();
    dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(rect.width * dpr));
    canvas.height = Math.max(1, Math.round(rect.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function square(x, y, s) { ctx.fillRect(x - s / 2, y - s / 2, s, s); }

  function diamond(x, y, s) {
    ctx.beginPath();
    ctx.moveTo(x, y - s);
    ctx.lineTo(x + s, y);
    ctx.lineTo(x, y + s);
    ctx.lineTo(x - s, y);
    ctx.closePath();
    ctx.fill();
  }

  function link(x1, y1, x2, y2, c, a) {
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.strokeStyle = c;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.restore();
  }

  function cube(x, y, s, lift, c) {
    ctx.save();
    ctx.fillStyle = c;
    ctx.strokeStyle = c;
    ctx.lineWidth = 1.1;
    ctx.globalAlpha *= .36;
    square(x + lift, y - lift, s);
    ctx.globalAlpha /= .36;
    square(x, y, s);
    ctx.beginPath();
    ctx.moveTo(x - s / 2, y - s / 2);
    ctx.lineTo(x + lift - s / 2, y - lift - s / 2);
    ctx.moveTo(x + s / 2, y - s / 2);
    ctx.lineTo(x + lift + s / 2, y - lift - s / 2);
    ctx.moveTo(x + s / 2, y + s / 2);
    ctx.lineTo(x + lift + s / 2, y - lift + s / 2);
    ctx.stroke();
    ctx.restore();
  }

  function prism(x, y, s, lift, c) {
    ctx.save();
    ctx.fillStyle = c;
    ctx.strokeStyle = c;
    ctx.lineWidth = 1.1;
    ctx.globalAlpha *= .36;
    diamond(x + lift, y - lift, s);
    ctx.globalAlpha /= .36;
    diamond(x, y, s);
    ctx.beginPath();
    ctx.moveTo(x, y - s);
    ctx.lineTo(x + lift, y - lift - s);
    ctx.moveTo(x + s, y);
    ctx.lineTo(x + lift + s, y - lift);
    ctx.moveTo(x, y + s);
    ctx.lineTo(x + lift, y - lift + s);
    ctx.moveTo(x - s, y);
    ctx.lineTo(x + lift - s, y - lift);
    ctx.stroke();
    ctx.restore();
  }

  function bg(w, h, c) {
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = c;
    ctx.globalAlpha = .045;
    ctx.fillRect(0, 0, w, h);
    ctx.globalAlpha = 1;
    ctx.fillStyle = "rgba(255,255,255,.035)";
    for (var i = 0; i < 36; i++) ctx.fillRect((i * 113) % w, 40 + ((i * 71) % (h - 90)), 1, 1);
  }

  function renderSource(w, h, t) {
    bg(w, h, colors.source);
    ctx.fillStyle = colors.source;
    for (var i = 0; i < 34; i++) {
      var x = ((i * 47 + t * .018) % (w + 80)) - 40;
      var y = 62 + ((i * 83) % (h - 124)) + Math.sin(t * .001 + i) * 9;
      square(x, y, 5 + (i % 4) * 2);
      if (i % 3 === 0) link(x, y, x + 24, y + 10, colors.source, .24);
    }
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  function labelPill(text, x, y, c) {
    ctx.save();
    ctx.font = "850 11px Inter, sans-serif";
    var tw = ctx.measureText(text).width;
    ctx.fillStyle = "rgba(12,16,22,.72)";
    ctx.strokeStyle = c;
    ctx.globalAlpha = .86;
    roundRect(x, y, tw + 18, 25, 12);
    ctx.fill();
    ctx.globalAlpha = .42;
    ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.fillStyle = c;
    ctx.fillText(text, x + 9, y + 16);
    ctx.restore();
  }

  function renderSourceDetail(w, h, t) {
    bg(w, h, colors.source);
    var thirds = [w * .34, w * .66];
    ctx.save();
    ctx.strokeStyle = "rgba(100,116,139,.22)";
    ctx.setLineDash([3, 5]);
    thirds.forEach(function (x) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    });
    ctx.setLineDash([]);
    ctx.restore();

    var sourceX = w * .105;
    var sources = [
      { name: "Confluence", icon: "CF", color: "#38bdf8", x: sourceX, y: h * .34, seed: 29, lane: 0 },
      { name: "Git Platforms", icon: "GT", color: "#f59e0b", x: sourceX, y: h * .46, seed: 47, lane: 1 },
      { name: "Datadog", icon: "DD", color: "#a47ef7", x: sourceX, y: h * .58, seed: 83, lane: 2 },
      { name: "Other", icon: "OT", color: "#32c786", x: sourceX, y: h * .70, seed: 109, lane: 3 }
    ];
    var busX = w * .50;
    var registryX = w * .82;
    var tick = t * .00018;
    var laneYs = [h * .35, h * .45, h * .55, h * .65];
    var cardX = busX - 104;
    var cardY = h * .24;
    var cardW = 208;
    var cardH = h * .56;
    var registryLeft = w * .735;
    var registryTop = h * .20;
    var registryW = w * .22;
    var registryH = h * .60;

    function sourceTile(source) {
      ctx.save();
      var pulse = .5 + .5 * Math.sin(t * .0021 + source.seed);
      ctx.fillStyle = "rgba(12,16,22,.82)";
      ctx.strokeStyle = source.color;
      ctx.globalAlpha = .92;
      roundRect(source.x - 40, source.y - 18, 118, 36, 9);
      ctx.fill();
      ctx.globalAlpha = .36 + pulse * .18;
      ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = source.color;
      roundRect(source.x - 31, source.y - 11, 23, 23, 6);
      ctx.fill();
      ctx.fillStyle = "#071017";
      ctx.font = "850 7.5px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(source.icon, source.x - 19.5, source.y + 3);
      ctx.textAlign = "left";
      ctx.fillStyle = "rgba(245,247,250,.88)";
      ctx.font = "850 11px Inter, sans-serif";
      ctx.fillText(source.name, source.x, source.y + 4);
      if (pulse > .86) {
        ctx.strokeStyle = source.color;
        ctx.globalAlpha = .16;
        ctx.beginPath();
        ctx.arc(source.x - 20, source.y, 23 + pulse * 8, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.restore();
    }

    sources.forEach(sourceTile);

    ctx.save();
    ctx.strokeStyle = "rgba(100,116,139,.58)";
    ctx.fillStyle = "rgba(12,16,22,.88)";
    roundRect(cardX, cardY, cardW, cardH, 13);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "rgba(245,247,250,.9)";
    ctx.font = "850 13px Inter, sans-serif";
    ctx.fillText("source intake gateway", cardX + 28, cardY + 29);
    var gatewayRows = [
      ["RAW", "files docs tickets", colors.source],
      ["GRAPH", "code doc org", colors.blue],
      ["LIVE", "webhooks MCP APIs", colors.amber],
      ["INDEX", "RAG vector catalog", colors.green]
    ].map(function (row, idx) {
      return {
        kind: row[0],
        label: row[1],
        color: row[2],
        y: sources[idx].y
      };
    });
    var gatewayPorts = sources.map(function (source, idx) {
      return {
        x: cardX,
        y: gatewayRows[idx].y,
        color: source.color,
        source: source
      };
    });
    gatewayPorts.forEach(function (port) {
      ctx.strokeStyle = port.color;
      ctx.globalAlpha = .38;
      ctx.beginPath();
      ctx.arc(port.x, port.y, 5.5, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = port.color;
      square(port.x, port.y, 4);
    });
    gatewayRows.forEach(function (row) {
      var y = row.y;
      ctx.fillStyle = "rgba(255,255,255,.025)";
      roundRect(cardX + 24, y - 13, cardW - 48, 26, 7);
      ctx.fill();
      ctx.fillStyle = row.color;
      ctx.globalAlpha = .92;
      square(cardX + 38, y, 6);
      ctx.globalAlpha = 1;
      ctx.fillStyle = "rgba(188,197,211,.9)";
      ctx.font = "750 9px ui-monospace, monospace";
      ctx.fillText(row.kind.toLowerCase(), cardX + 52, y + 3);
      ctx.fillStyle = "rgba(160,169,184,.88)";
      ctx.fillText(row.label, cardX + 90, y + 3);
    });
    ctx.fillStyle = "rgba(160,169,184,.85)";
    ctx.font = "750 10px ui-monospace, monospace";
    ctx.fillText("ACL + hash + timestamp", cardX + 36, cardY + cardH - 20);
    ctx.restore();

    sources.forEach(function (source, idx) {
      ctx.save();
      ctx.strokeStyle = source.color;
      ctx.globalAlpha = .2;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(source.x + 82, source.y);
      ctx.lineTo(cardX, gatewayRows[idx].y);
      ctx.stroke();
      ctx.restore();
    });

    function drawOrthogonalPath(points, color, alpha) {
      ctx.save();
      ctx.strokeStyle = color;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (var k = 1; k < points.length; k++) ctx.lineTo(points[k].x, points[k].y);
      ctx.stroke();
      ctx.restore();
    }

    function pointOnPath(points, progress) {
      var total = 0;
      var lengths = [];
      for (var k = 1; k < points.length; k++) {
        var dx = points[k].x - points[k - 1].x;
        var dy = points[k].y - points[k - 1].y;
        var len = Math.sqrt(dx * dx + dy * dy);
        lengths.push(len);
        total += len;
      }
      var target = total * progress;
      var walked = 0;
      for (k = 1; k < points.length; k++) {
        if (walked + lengths[k - 1] >= target) {
          var local = lengths[k - 1] ? (target - walked) / lengths[k - 1] : 0;
          return {
            x: points[k - 1].x + (points[k].x - points[k - 1].x) * local,
            y: points[k - 1].y + (points[k].y - points[k - 1].y) * local
          };
        }
        walked += lengths[k - 1];
      }
      return points[points.length - 1];
    }

    sources.forEach(function (source, sourceIndex) {
      for (var i = 0; i < 1; i++) {
        var phase = (tick + sourceIndex * .081 + i * .37) % 1;
        var busY = gatewayRows[sourceIndex].y;
        var regY = h * (.28 + ((sourceIndex * 2 + i) % 8) * .06);
        var x;
        var y;
        var c = source.color;

        if (phase < .44) {
          var p = phase / .44;
          var sx = source.x + 82;
          var sy = source.y;
          var targetX = cardX;
          var inPath = [
            { x: sx, y: sy },
            { x: targetX, y: busY }
          ];
          var point = pointOnPath(inPath, p);
          x = point.x;
          y = point.y;
          drawOrthogonalPath(inPath, c, .02);
          ctx.fillStyle = c;
          ctx.globalAlpha = .22 + p * .78;
          square(x, y, 5 + i);
        } else if (phase < .68) {
          var hold = (phase - .44) / .24;
          var rowX = cardX;
          var rowY = source.y;
          ctx.fillStyle = colors.amber;
          ctx.globalAlpha = .16 + Math.sin(hold * Math.PI) * .28;
          ctx.beginPath();
          ctx.arc(rowX, rowY, 7, 0, Math.PI * 2);
          ctx.fill();
        } else {
          var q = (phase - .68) / .32;
          var outX = cardX + cardW;
          var outRouteX = registryLeft - 30;
          var registryRowY = registryTop + 74 + (sourceIndex % 4) * 43;
          var outPath = [
            { x: outX, y: busY },
            { x: outRouteX, y: busY },
            { x: outRouteX, y: registryRowY },
            { x: registryLeft, y: registryRowY }
          ];
          point = pointOnPath(outPath, q);
          x = point.x;
          y = point.y;
          drawOrthogonalPath(outPath, colors.source, .07);
          ctx.fillStyle = colors.source;
          ctx.globalAlpha = .46 + q * .44;
          square(x, y, 8);
          ctx.strokeStyle = "rgba(100,116,139,.68)";
          ctx.setLineDash([2, 4]);
          ctx.strokeRect(x - 8, y - 8, 16, 16);
          ctx.setLineDash([]);
        }
        ctx.globalAlpha = 1;
      }
    });

    ctx.save();
    ctx.strokeStyle = "rgba(100,116,139,.45)";
    ctx.fillStyle = "rgba(100,116,139,.07)";
    roundRect(registryLeft, registryTop, registryW, registryH, 12);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "rgba(245,247,250,.86)";
    ctx.font = "850 12px Inter, sans-serif";
    ctx.fillText("context source registry", registryLeft + 24, registryTop + 33);
    var handleRows = [
      ["CODE", "CodeGraph reality", colors.blue],
      ["DOC", "DocGraph decisions", colors.source],
      ["ORG", "OrgGraph ownership", colors.green],
      ["RAW", "source handles", colors.amber]
    ];
    handleRows.forEach(function (handle, row) {
      var y = registryTop + 74 + row * 43;
      ctx.fillStyle = "rgba(255,255,255,.032)";
      roundRect(registryLeft + 18, y - 15, registryW - 36, 29, 7);
      ctx.fill();
      ctx.fillStyle = handle[2];
      roundRect(registryLeft + 28, y - 9, 38, 17, 5);
      ctx.fill();
      ctx.fillStyle = "#071017";
      ctx.font = "850 7.5px Inter, sans-serif";
      ctx.fillText(handle[0], registryLeft + 33, y + 3);
      ctx.fillStyle = "rgba(188,197,211,.88)";
      ctx.font = "750 9px ui-monospace, monospace";
      ctx.fillText(handle[1], registryLeft + 74, y + 3);
    });
    ctx.fillStyle = "rgba(245,247,250,.82)";
    ctx.font = "850 12px Inter, sans-serif";
    ctx.fillText("ctx:// handles issued", registryLeft + 24, registryTop + registryH - 44);
    ctx.fillStyle = "rgba(160,169,184,.82)";
    ctx.font = "750 10px ui-monospace, monospace";
    ctx.fillText("available for reconciliation", registryLeft + 24, registryTop + registryH - 24);
    ctx.restore();
  }

  function renderReconciliation(w, h, t) {
    bg(w, h, colors.green);
    var cx = w * .62, cy = h * .5;
    var rows = [["Jira: 30 days", colors.source], ["Policy page: 14 days", colors.source], ["Billing service: 21 days", colors.green]];
    rows.forEach(function (row, i) {
      var x = w * .16, y = h * (.28 + i * .22);
      ctx.fillStyle = row[1];
      square(x, y, 16);
      link(x, y, cx, cy, row[1], i === 2 ? .72 : .35);
      ctx.fillStyle = row[1];
      ctx.font = "800 12px Inter, sans-serif";
      ctx.fillText(row[0], x + 24, y + 4);
    });
    cube(cx, cy, 28, 10, colors.green);
    ctx.strokeStyle = colors.amber;
    ctx.setLineDash([4, 6]);
    ctx.strokeRect(w * .74, h * .38, 110, 56);
    ctx.setLineDash([]);
    ctx.fillStyle = colors.amber;
    ctx.font = "850 12px Inter, sans-serif";
    ctx.fillText("flag for review", w * .77, h * .5);
  }

  function renderAnti(w, h, t) {
    bg(w, h, colors.blue);
    ctx.fillStyle = colors.source;
    ctx.font = "850 13px Inter, sans-serif";
    ctx.fillText("refund_days = 30", w * .12, h * .34);
    ctx.fillText("late_fee_cap = ?", w * .12, h * .62);
    link(w * .38, h * .34, w * .66, h * .5, colors.blue, .48);
    link(w * .38, h * .62, w * .66, h * .5, colors.blue, .48);
    cube(w * .66, h * .5, 34, 12, colors.blue);
    ctx.strokeStyle = colors.blue;
    ctx.setLineDash([4, 6]);
    ctx.beginPath();
    ctx.arc(w * .66, h * .5, 70 + Math.sin(t * .002) * 3, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function renderEnhancement(w, h, t) {
    bg(w, h, colors.amber);
    var cx = w * .62, cy = h * .52;
    cube(cx, cy, 30, 10, colors.blue);
    ctx.strokeStyle = colors.amber;
    ctx.setLineDash([2, 6]);
    ctx.beginPath();
    ctx.moveTo(w * .18, 46);
    ctx.lineTo(w * .18, h - 46);
    ctx.stroke();
    ctx.setLineDash([]);
    for (var i = 0; i < 4; i++) {
      var phase = (t * .00045 + i * .23) % 1;
      var sx = w * .18, sy = h * (.24 + i * .17);
      var angle = Math.PI * 2 * i / 4 + t * .0008;
      var tx = cx + Math.cos(angle) * 58;
      var ty = cy + Math.sin(angle) * 38;
      var x = sx + (tx - sx) * phase;
      var y = sy + (ty - sy) * phase;
      ctx.fillStyle = colors.amber;
      ctx.globalAlpha = .28 + phase * .72;
      diamond(x, y, 6);
      ctx.globalAlpha = 1;
      link(sx, sy, x, y, colors.amber, .24 * (1 - phase));
      if (phase > .7) link(cx, cy, x, y, colors.amber, .24 * (1 - phase) + .08);
    }
  }

  function renderOptimization(w, h, t) {
    bg(w, h, colors.violet);
    ctx.fillStyle = colors.amber;
    for (var i = 0; i < 14; i++) square(w * .18 + (i % 7) * 15, h * .38 + Math.floor(i / 7) * 28, 6);
    var p = (Math.sin(t * .001) + 1) / 2;
    var cx = w * .66, cy = h * .5;
    link(w * .34, h * .43, cx, cy, colors.violet, .38);
    link(w * .34, h * .57, cx, cy, colors.violet, .38);
    prism(cx, cy, 46 - p * 14, 13 - p * 4, colors.violet);
    ctx.strokeStyle = colors.violet;
    ctx.setLineDash([5, 6]);
    ctx.beginPath();
    ctx.arc(cx, cy, 80 - p * 20, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function renderConsumption(w, h, t) {
    bg(w, h, colors.source);
    var cx = w * .28, cy = h * .5;
    prism(cx, cy, 34, 9, colors.source);
    ctx.strokeStyle = "rgba(100,116,139,.7)";
    ctx.setLineDash([3, 6]);
    ctx.beginPath();
    ctx.arc(cx, cy, 60, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
    [["Claude", .64, .32], ["Cursor", .76, .5], ["Dashboard", .62, .68]].forEach(function (target) {
      var x = w * target[1], y = h * target[2];
      link(cx + 58, cy, x - 12, y, colors.source, .5);
      ctx.fillStyle = colors.source;
      square(x, y, 12);
      ctx.fillStyle = "rgba(245,247,250,.82)";
      ctx.font = "850 12px Inter, sans-serif";
      ctx.fillText(target[0], x + 18, y + 4);
    });
  }

  var renderers = { source: renderSource, "source-detail": renderSourceDetail, reconciliation: renderReconciliation, anti: renderAnti, enhancement: renderEnhancement, optimization: renderOptimization, consumption: renderConsumption };

  function frame(t) {
    resize();
    var w = canvas.width / dpr, h = canvas.height / dpr;
    renderers[stage](w, h, t);
    requestAnimationFrame(frame);
  }

  requestAnimationFrame(frame);
})();
