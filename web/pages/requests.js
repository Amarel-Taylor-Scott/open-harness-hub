/* Open Harness Hub — requests / contribute module
   Ports: PRequests (/requests), PRequestNew (/requests/new),
          PRequestDetail (/requests/:id), PContribute (/contribute)
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
    /* "+ Request a capability" — navigates to the real form page. */
    var newReqBtn = host.querySelector("#ohh-new-request");
    if (newReqBtn) {
      newReqBtn.addEventListener("click", function () {
        ctx.navigate("/requests/new");
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
  /* PRequestNew — /requests/new                                          */
  /* ------------------------------------------------------------------ */

  var DOMAIN_OPTIONS = [
    ["", "— pick a domain —"],
    ["esg", "ESG / sustainability"],
    ["aml-compliance", "AML / sanctions / compliance"],
    ["healthcare", "Healthcare / GxP"],
    ["legal", "Legal / contracts"],
    ["finance", "Finance / accounting"],
    ["supply-chain", "Supply chain"],
    ["hr-labour", "HR / labour rights"],
    ["general", "General / other"]
  ];

  function renderRequestNew(ctx) {
    var e = ctx.esc;

    var domainOptions = "";
    for (var i = 0; i < DOMAIN_OPTIONS.length; i++) {
      var opt = DOMAIN_OPTIONS[i];
      domainOptions += '<option value="' + e(opt[0]) + '">' + e(opt[1]) + '</option>';
    }

    return (
      '<div class="pt-page pt-view">' +
        '<div class="pt-crumb" style="margin-bottom:14px">' +
          '<a data-nav="/requests" style="cursor:pointer">Requests</a>' +
          '<span class="sep">/</span>' +
          '<b>New request</b>' +
        '</div>' +
        '<div class="pt-page-head">' +
          '<h1>Request a capability</h1>' +
          '<div class="sub">Describe what you need. We screen it for structural lift — if a component would measurably help the model do something it can&apos;t do alone, we research and build it.</div>' +
        '</div>' +

        '<div id="ohh-req-form-wrap">' +
          '<div class="pt-panel" style="max-width:600px">' +

            /* Title field */
            '<div class="pt-field">' +
              '<label for="ohh-req-title">Capability title <span style="color:var(--danger)">*</span></label>' +
              '<input id="ohh-req-title" placeholder="e.g. Conflict-minerals (3TG) tracer" maxlength="120" autocomplete="off" />' +
              '<div class="pt-field-hint" id="ohh-req-title-hint" style="color:var(--danger);font-size:11.5px;margin-top:4px;display:none">Please enter a title (at least 10 characters).</div>' +
            '</div>' +

            /* Domain field */
            '<div class="pt-field">' +
              '<label for="ohh-req-domain">Domain <span style="color:var(--danger)">*</span></label>' +
              '<select id="ohh-req-domain" style="width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:var(--r-md);background:var(--panel);color:var(--fg);font-family:inherit;font-size:14px">' +
                domainOptions +
              '</select>' +
              '<div class="pt-field-hint" id="ohh-req-domain-hint" style="color:var(--danger);font-size:11.5px;margin-top:4px;display:none">Please select a domain.</div>' +
            '</div>' +

            /* Why field */
            '<div class="pt-field">' +
              '<label for="ohh-req-why">Why does a bare model fall short? <span style="color:var(--danger)">*</span></label>' +
              '<textarea id="ohh-req-why" rows="3" placeholder="What does the model get wrong or miss without this component? The structural gap you&apos;re seeing…" style="width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:var(--r-md);background:var(--panel);color:var(--fg);font-family:inherit;font-size:14px;resize:vertical;box-sizing:border-box"></textarea>' +
              '<div class="pt-field-hint" id="ohh-req-why-hint" style="color:var(--danger);font-size:11.5px;margin-top:4px;display:none">Please describe the gap (at least 20 characters).</div>' +
            '</div>' +

            /* Example field */
            '<div class="pt-field">' +
              '<label for="ohh-req-example">A concrete example</label>' +
              '<textarea id="ohh-req-example" rows="2" placeholder="e.g. &ldquo;I need to trace 3TG minerals from supplier to smelter using OECD sourcing guidance&rdquo;" style="width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:var(--r-md);background:var(--panel);color:var(--fg);font-family:inherit;font-size:14px;resize:vertical;box-sizing:border-box"></textarea>' +
            '</div>' +

            '<div style="display:flex;gap:10px;margin-top:6px">' +
              '<button class="oh-btn oh-btn--primary" id="ohh-req-submit">Submit request</button>' +
              '<button class="oh-btn oh-btn--ghost" data-nav="/requests">Cancel</button>' +
            '</div>' +

          '</div>' +
        '</div>' +

        /* Confirmation state — hidden until submit */
        '<div id="ohh-req-confirm" style="display:none;max-width:600px">' +
          '<div class="oh-state-msg" style="background:color-mix(in srgb,var(--success) 8%,transparent);border:1px solid color-mix(in srgb,var(--success) 30%,var(--line));border-radius:var(--r-md);padding:18px 20px;display:block">' +
            '<div style="font-weight:700;color:var(--fg);margin-bottom:6px">&#x2713; Request submitted</div>' +
            '<div style="font-size:13px;color:var(--fg-muted);line-height:1.55;margin-bottom:14px">' +
              'We&apos;ll screen it for structural lift against the two-axis gate. ' +
              'If it passes, it enters the research queue. ' +
              'Vote it up on the requests board to signal demand.' +
            '</div>' +
            '<div style="display:flex;gap:10px">' +
              '<button class="oh-btn oh-btn--primary oh-btn--sm" data-nav="/requests">View all requests →</button>' +
              '<button class="oh-btn oh-btn--ghost oh-btn--sm" id="ohh-req-another">Submit another</button>' +
            '</div>' +
          '</div>' +
        '</div>' +

      '</div>'
    );
  }

  function onMountRequestNew(host, ctx) {
    var formWrap   = host.querySelector("#ohh-req-form-wrap");
    var confirmEl  = host.querySelector("#ohh-req-confirm");
    var submitBtn  = host.querySelector("#ohh-req-submit");
    var anotherBtn = host.querySelector("#ohh-req-another");

    var titleEl   = host.querySelector("#ohh-req-title");
    var domainEl  = host.querySelector("#ohh-req-domain");
    var whyEl     = host.querySelector("#ohh-req-why");

    var titleHint  = host.querySelector("#ohh-req-title-hint");
    var domainHint = host.querySelector("#ohh-req-domain-hint");
    var whyHint    = host.querySelector("#ohh-req-why-hint");

    function setHint(el, show) {
      if (el) el.style.display = show ? "" : "none";
    }

    function validate() {
      var titleOk  = titleEl  && titleEl.value.trim().length >= 10;
      var domainOk = domainEl && domainEl.value !== "";
      var whyOk    = whyEl    && whyEl.value.trim().length >= 20;

      setHint(titleHint,  !titleOk);
      setHint(domainHint, !domainOk);
      setHint(whyHint,    !whyOk);

      return titleOk && domainOk && whyOk;
    }

    /* Clear hint on input */
    if (titleEl)  titleEl.addEventListener("input",  function () { setHint(titleHint,  false); });
    if (domainEl) domainEl.addEventListener("change", function () { setHint(domainHint, false); });
    if (whyEl)    whyEl.addEventListener("input",    function () { setHint(whyHint,    false); });

    if (submitBtn) {
      submitBtn.addEventListener("click", function () {
        if (!validate()) return;
        /* Show confirmation, hide form */
        if (formWrap)  formWrap.style.display  = "none";
        if (confirmEl) confirmEl.style.display = "";
      });
    }

    if (anotherBtn) {
      anotherBtn.addEventListener("click", function () {
        /* Reset form and show it again */
        if (titleEl)  titleEl.value  = "";
        if (domainEl) domainEl.value = "";
        if (whyEl)    whyEl.value    = "";
        if (formWrap)  formWrap.style.display  = "";
        if (confirmEl) confirmEl.style.display = "none";
      });
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

    /* Use known detail data; show a clear not-found state for unknown ids — never
       synthesise a phantom record that renders a misleading detail view. */
    var d = REQ_DETAIL[id];
    if (!d) {
      return (
        '<div class="pt-page pt-view">' +
          '<div class="pt-crumb" style="margin-bottom:14px">' +
            '<a data-nav="/requests" style="cursor:pointer">Requests</a>' +
            '<span class="sep">/</span>' +
            '<b>' + e(id) + '</b>' +
          '</div>' +
          '<div class="pt-page-head"><h1>Request not found</h1>' +
            '<div class="sub">' +
              'No capability request with ID <span style="font-family:var(--font-mono)">' + e(id) + '</span> exists. ' +
              'It may have been promoted or the link is incorrect.' +
            '</div>' +
          '</div>' +
          '<div style="display:flex;gap:10px;margin-top:8px">' +
            '<button class="oh-btn oh-btn--primary" data-nav="/requests/new">+ Request a capability</button>' +
            '<button class="oh-btn oh-btn--ghost" data-nav="/requests">← All requests</button>' +
          '</div>' +
        '</div>'
      );
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
  /* /requests/new MUST be registered before /requests/:id so the literal "new"
     segment is matched first; the router tests routes in registration order. */
  OHH.register("/requests/new", renderRequestNew, onMountRequestNew, { theme: "dark" });
  OHH.register("/requests/:id", renderRequestDetail, onMountRequestDetail, { theme: "dark" });
  OHH.register("/contribute", renderContribute, onMountContribute, { theme: "dark" });

})();
