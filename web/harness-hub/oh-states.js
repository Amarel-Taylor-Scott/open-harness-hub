/* Open Harness Hub — shared empty / loading / error state primitives (UX-BACKLOG P1 #3).
   Three token-only kit functions every list/panel can use so the a11y + polish floor is uniform.
   No framework: each returns an HTML string built from design tokens (no hardcoded colors).
   Usage:  el.innerHTML = OhStates.empty({title, body, cta});
           el.innerHTML = OhStates.skeleton(rows);
           el.innerHTML = OhStates.error({title, body, retryId}); */
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function empty(o) {
    o = o || {};
    return '<div class="oh-state oh-state--empty" role="status" style="text-align:center;padding:40px 20px;color:var(--fg-muted)">' +
      '<div class="oh-state-glyph" aria-hidden="true" style="font-size:26px;opacity:.5;margin-bottom:8px">◦</div>' +
      '<div class="oh-state-title" style="font-family:var(--font-display);font-size:15px;color:var(--fg);margin-bottom:4px">' +
      esc(o.title || "Nothing here yet") + "</div>" +
      '<div class="oh-state-body" style="font-size:13px;max-width:340px;margin:0 auto 14px">' +
      esc(o.body || "") + "</div>" +
      (o.cta && o.ctaNav
        ? '<button class="oh-btn oh-btn--primary" data-nav="' + esc(o.ctaNav) + '">' + esc(o.cta) + "</button>"
        : "") +
      "</div>";
  }

  function skeleton(rows) {
    rows = rows || 3;
    var line = '<div class="oh-skel-row" aria-hidden="true" style="height:14px;border-radius:var(--r-sm);' +
      "background:linear-gradient(90deg,var(--bg-subtle),var(--panel-2),var(--bg-subtle));" +
      'background-size:200% 100%;animation:oh-shimmer 1.2s ease-in-out infinite;margin:10px 0"></div>';
    var css = '<style>@keyframes oh-shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}</style>';
    return '<div class="oh-state oh-state--loading" role="status" aria-busy="true" aria-label="Loading">' +
      css + new Array(rows + 1).join(line) + "</div>";
  }

  function error(o) {
    o = o || {};
    return '<div class="oh-state oh-state--error" role="alert" style="text-align:center;padding:32px 20px">' +
      '<div class="oh-state-glyph" aria-hidden="true" style="font-size:24px;color:var(--danger,#c0392b);margin-bottom:8px">⚠</div>' +
      '<div class="oh-state-title" style="font-family:var(--font-display);font-size:15px;color:var(--fg);margin-bottom:4px">' +
      esc(o.title || "Something went wrong") + "</div>" +
      '<div class="oh-state-body" style="font-size:13px;color:var(--fg-muted);max-width:340px;margin:0 auto 14px">' +
      esc(o.body || "Please try again.") + "</div>" +
      (o.retryId
        ? '<button class="oh-btn oh-btn--ghost" id="' + esc(o.retryId) + '">Retry</button>'
        : "") +
      "</div>";
  }

  window.OhStates = { empty: empty, skeleton: skeleton, error: error };
}());
