/* Open Harness Hub — requests / contribute module
   Ports: PRequests (/requests), PRequestDetail (/requests/:id), PContribute (/contribute)
   Source: proto-wide.jsx (PRequests, PRequestDetail, PContribute)
   Style: proto-wide.css, proto-deep.css, proto-admin.css, proto.css atoms
   No framework, no build step — vanilla ES5-style, self-registering via OHH.register. */
(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /* Data                                                                 */
  /* ------------------------------------------------------------------ */

  var REQS = [
    ["req-204", "Conflict-minerals (3TG) tracer",       "knowledge-corpus", 312, "researching"],
    ["req-198", "Living-wage benchmark calculator",      "processor",        271, "building"],
    ["req-187", "EUDR geolocation deforestation check",  "harness",          244, "triaged"],
    ["req-176", "Water-stress index by basin",           "knowledge-corpus", 156, "requested"]
  ];

  var REQ_STAGES = ["requested", "triaged", "researching", "building", "built", "promoted"];

  /* Detail data keyed by request id — fallback to the first request when unknown */
  var REQ_DETAIL = {
    "req-204": {
      title:  "Conflict-minerals (3TG) tracer",
      votes:  312,
      type:   "knowledge-corpus",
      status: "researching",
      sources: "OECD due-diligence guidance, USGS minerals, EITI"
    }
  };

  /* ------------------------------------------------------------------ */
  /* Helpers                                                              */
  /* ------------------------------------------------------------------ */

  /** Build the status pipeline HTML for a given status string. */
  function statusPipeHTML(status) {
    var idx = REQ_STAGES.indexOf(status);
    var parts = [];
    for (var i = 0; i < REQ_STAGES.length; i++) {
      if (i > 0) {
        parts.push('<span class="sep"></span>');
      }
      var cls = "st" + (i < idx ? " done" : i === idx ? " on" : "");
      var dot = i <= idx ? "●" : "○";
      parts.push('<span class="' + cls + '">' + dot + " " + REQ_STAGES[i] + "</span>");
    }
    return '<div class="pt-statuspipe">' + parts.join("") + "</div>";
  }

  /** Build step-wizard HTML (PContribute). */
  function stepWizardHTML(steps, activeUpTo) {
    var parts = [];
    for (var i = 0; i < steps.length; i++) {
      var on = i < activeUpTo ? " on" : "";
      parts.push(
        '<span class="pt-step' + on + '">' +
          '<span class="n">' + (i + 1) + "</span>" +
          steps[i] +
        "</span>"
      );
      if (i < steps.length - 1) {
        parts.push('<span class="arr">→</span>');
      }
    }
    return '<div class="pt-steps">' + parts.join("") + "</div>";
  }

  /* ------------------------------------------------------------------ */
  /* PRequests — /requests                                                */
  /* ------------------------------------------------------------------ */

  function renderRequests(ctx) {
    var e = ctx.esc;

    var rows = "";
    for (var i = 0; i < REQS.length; i++) {
      var r = REQS[i];
      var id     = r[0];
      var nm     = r[1];
      var type   = r[2];
      var votes  = r[3];
      var status = r[4];

      rows +=
        '<div class="pt-reqrow">' +
          '<div class="pt-vote" data-vote="' + e(id) + '">' +
            '<span class="up">▲</span>' +
            '<span class="n">' + e(votes) + "</span>" +
          "</div>" +
          '<div class="body" style="cursor:pointer" data-nav="/requests/' + e(id) + '">' +
            '<div class="nm">◷ ' + e(nm) + "</div>" +
            '<div class="meta">' +
              '<span class="mono" style="font-family:var(--font-mono)">target · ' + e(type) + "</span>" +
              '<span class="pt-status-chip">' + e(status) + "</span>" +
            "</div>" +
            statusPipeHTML(status) +
          "</div>" +
        "</div>";
    }

    return (
      '<div class="pt-page wide pt-view">' +
        '<div class="pt-page-head">' +
          "<h1>Capability requests</h1>" +
          '<div class="sub">Demand for what the catalog lacks — vote it up; we research, build, and gate it. Build-on-demand turns gaps into governed components.</div>' +
        "</div>" +
        '<div class="pt-toolbar">' +
          '<span style="font-size:13px;color:var(--fg-muted)">Sorted by demand</span>' +
          '<span class="pt-spacer"></span>' +
          '<button class="oh-btn oh-btn--primary oh-btn--sm" id="ohh-new-request">+ Request a capability</button>' +
        "</div>" +
        '<div class="pt-panel">' + rows + "</div>" +
      "</div>"
    );
  }

  function onMountRequests(host, ctx) {
    /* "+ Request a capability" — demand capture. No standalone form page exists,
       so confirm the intent rather than navigating into a phantom /requests/:id. */
    var newReqBtn = host.querySelector("#ohh-new-request");
    if (newReqBtn) {
      newReqBtn.addEventListener("click", function () {
        ctx.toast("Describe the capability you need — we'll screen it for lift");
      });
    }

    /* Vote buttons: optimistic +1 on the count display, then toast. */
    var voteBtns = host.querySelectorAll(".pt-vote[data-vote]");
    for (var i = 0; i < voteBtns.length; i++) {
      (function (btn) {
        btn.addEventListener("click", function (e) {
          /* Don't let the click bubble into the body nav target */
          e.stopPropagation();
          var n = btn.querySelector(".n");
          if (n && !btn.getAttribute("data-voted")) {
            btn.setAttribute("data-voted", "1");
            n.textContent = String(parseInt(n.textContent, 10) + 1);
            btn.style.borderColor = "var(--accent)";
            ctx.toast("Vote recorded");
          }
        });
      })(voteBtns[i]);
    }
  }

  /* ------------------------------------------------------------------ */
  /* PRequestDetail — /requests/:id                                       */
  /* ------------------------------------------------------------------ */

  function renderRequestDetail(ctx) {
    var e   = ctx.esc;
    var id  = ctx.params && ctx.params.id ? ctx.params.id : "";

    /* Graceful not-found */
    if (!id) {
      return (
        '<div class="pt-page pt-view">' +
          '<div class="pt-page-head"><h1>Request not found</h1>' +
          '<div class="sub">No request ID provided. <a data-nav="/requests" style="color:var(--accent);cursor:pointer">Back to requests →</a></div></div>' +
        "</div>"
      );
    }

    /* Use known detail data; fall back to a synthetic record when the id is unknown */
    var d = REQ_DETAIL[id];
    if (!d) {
      d = {
        title:   id,
        votes:   0,
        type:    "unknown",
        status:  "requested",
        sources: "—"
      };
    }

    return (
      '<div class="pt-page pt-view">' +
        '<div class="pt-crumb" style="margin-bottom:14px">' +
          '<a data-nav="/requests" style="cursor:pointer">Requests</a>' +
          '<span class="sep">/</span>' +
          "<b>" + e(id) + "</b>" +
        "</div>" +
        '<div class="pt-page-head">' +
          "<h1>◷ " + e(d.title) + "</h1>" +
          '<div class="sub">' +
            e(d.votes) + " tenants want this · target type: " + e(d.type) +
            " · status: " + e(d.status) +
          "</div>" +
        "</div>" +
        '<div class="pt-intent">' +
          /* Left column: promotion path */
          '<div class="pt-panel">' +
            '<div class="oh-cc-id mono" style="margin-bottom:12px">promotion path</div>' +
            statusPipeHTML(d.status) +
            '<div style="font-size:12.5px;color:var(--fg-muted);margin-top:14px;line-height:1.5">' +
              "Candidate sources found: <b style=\"color:var(--fg)\">" + e(d.sources) + "</b>. " +
              "Must clear the two-axis gate: <b style=\"color:var(--fg)\">structural lift</b> + " +
              "<b style=\"color:var(--fg)\">verifiable provenance</b> before promotion to " +
              "<span class=\"mono\">experimental</span>." +
            "</div>" +
          "</div>" +
          /* Right column: fulfillment paths */
          '<div class="pt-panel">' +
            '<div class="oh-cc-id mono" style="margin-bottom:10px">two ways to fulfill</div>' +
            '<div class="pt-setting-row">' +
              '<div class="info">' +
                '<div class="t">Premium agent build</div>' +
                '<div class="d">Hosted, paid — fastest. We build &amp; gate it.</div>' +
              "</div>" +
              '<button class="oh-btn oh-btn--primary oh-btn--sm" id="ohh-fund-btn">Fund build</button>' +
            "</div>" +
            '<div class="pt-setting-row">' +
              '<div class="info">' +
                '<div class="t">Community build</div>' +
                '<div class="d">Contribute it; earn credits when it passes the gate.</div>' +
              "</div>" +
              '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/contribute">Contribute</button>' +
            "</div>" +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  function onMountRequestDetail(host, ctx) {
    var fundBtn = host.querySelector("#ohh-fund-btn");
    if (fundBtn) {
      fundBtn.addEventListener("click", function () {
        ctx.toast("Build-on-demand queued");
      });
    }
  }

  /* ------------------------------------------------------------------ */
  /* PContribute — /contribute                                            */
  /* ------------------------------------------------------------------ */

  var CONTRIBUTE_STEPS = ["Pick a request", "Build component", "Submit", "Gate measures lift", "Earn credits"];
  /* Steps 0 and 1 are "on" (active/completed) in the prototype */
  var CONTRIBUTE_ACTIVE = 2;

  function renderContribute(ctx) {
    var e = ctx.esc;

    return (
      '<div class="pt-page pt-view">' +
        '<div class="pt-page-head">' +
          "<h1>Contribute &amp; earn credits</h1>" +
          '<div class="sub">Fulfill a capability-request; earn credits when your shared component passes the lift gate.</div>' +
        "</div>" +
        stepWizardHTML(CONTRIBUTE_STEPS, CONTRIBUTE_ACTIVE) +
        '<div class="pt-dash-grid">' +
          /* Credit mechanics panel */
          '<div class="pt-panel">' +
            '<div class="oh-cc-id mono" style="margin-bottom:8px">credit mechanics</div>' +
            '<div style="font-size:13px;color:var(--fg-muted);line-height:1.6">' +
              "Credit is granted <b style=\"color:var(--fg)\">only</b> when the shared component beats a bare model and is promoted. " +
              "No lift, no credit — the same gate everything else passes. Credits offset usage &amp; build-on-demand." +
            "</div>" +
          "</div>" +
          /* Your contributions panel */
          '<div class="pt-panel">' +
            '<div class="oh-cc-id mono" style="margin-bottom:8px">your contributions</div>' +
            '<div class="pt-list-row">' +
              '<div style="flex:1">' +
                '<div class="ttl">processor/entity-resolver</div>' +
                '<div class="meta">promoted · ▲ +0.14</div>' +
              "</div>" +
              '<span class="oh-badge oh-badge--lift">+1,250 cr</span>' +
            "</div>" +
            '<div class="pt-list-row">' +
              '<div style="flex:1">' +
                '<div class="ttl">rule-pack/aml-screen</div>' +
                '<div class="meta">verifying</div>' +
              "</div>" +
              '<span class="oh-badge oh-badge--warn">pending</span>' +
            "</div>" +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  function onMountContribute(host, ctx) {
    /* No interactive wiring needed beyond global data-nav delegation;
       the page is intentionally mostly static display in the prototype. */
  }

  /* ------------------------------------------------------------------ */
  /* Registration                                                         */
  /* ------------------------------------------------------------------ */

  OHH.register("/requests", renderRequests, onMountRequests, { theme: "dark" });
  OHH.register("/requests/:id", renderRequestDetail, onMountRequestDetail, { theme: "dark" });
  OHH.register("/contribute", renderContribute, onMountContribute, { theme: "dark" });

})();
