/* Baltor — trust policy (route "/trust"). The moat: source trust, fact-state
   lineage, verification, reconciliation, and proof that can be served with context. */
(function () {
  "use strict";

  var PILLARS = [
    ["Fact-state lineage", "A new fact keeps its full path: candidate detected, one source found, second source queued, authoritative source found, adopted, held, rejected, or superseded."],
    ["Multi-source adoption", "Baltor does not serve a new external fact just because one source or one model says so. Two independent sources are the default, with a clear exception for official sources of record."],
    ["Source trust checks", "Fetched pages are scored for source role, publisher identity, source stability, archive availability, suspicious markup, spam patterns, and context-injection risk."],
    ["Reconciliation before serving", "When sources differ on date, scope, or precedence, the fact stays out of served context until the resolution path is clear."],
    ["Archive and provenance", "Evidence spans, timestamps, source hashes, archive status, and adoption reasons travel with the serving package when the workflow needs them."],
    ["Same discipline as OHH", "Open Harness Hub measures whether a harness lifts over a bare model. Baltor applies that discipline upstream: is the context current, supported, and safe to serve?"]
  ];

  function pillars() {
    return PILLARS.map(function (p) {
      return '<div class="pt-panel" style="text-align:left">' +
        '<div style="font-weight:700;color:var(--fg);margin-bottom:5px">' + p[0] + "</div>" +
        '<div style="font-size:13px;color:var(--fg-muted);line-height:1.55">' + p[1] + "</div></div>";
    }).join("");
  }

  function render(ctx) {
    return '<div class="pt-mkt pt-view">' + ctx.header("/trust") +
      '<div class="pt-mkt-body"><div class="pt-page" style="max-width:920px;margin:0 auto">' +
      '<div class="pt-page-head">' +
      '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:10px">The trust policy</div>' +
      '<h1>Facts earn their way into served context.</h1>' +
      '<div class="sub">Baltor keeps source evidence, state history, trust checks, archive status, and refresh policy attached to every fact, so agents receive current context with proof instead of unsupported text.</div>' +
      "</div>" +
      '<div class="pt-grid-3">' + pillars() + "</div>" +
      '<div class="oh-state-msg" style="margin-top:24px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:16px 18px;display:block">' +
      '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6">A one-source finding is not wasted. It stays in lineage, gets a higher-priority second-source search when it matters, and only becomes served context when policy says the evidence is strong enough.</div>' +
      '<div style="margin-top:12px"><button class="oh-btn oh-btn--primary oh-btn--sm" data-nav="/pricing">See pricing →</button> <button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/">Back to overview</button></div>' +
      "</div>" +
      "</div></div></div>";
  }

  CE.register("/trust", render);
})();
