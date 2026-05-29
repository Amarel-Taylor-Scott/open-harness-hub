/* Open Harness Hub — auth screen module
   Routes: /signin · /signup · /onboarding · /upgrade
   Minimal light shell. Faithfully ported from proto-wide.jsx (PSignin / POnboarding / PUpgrade).
   No build step, no framework, no imports. Registers via OHH.register(). */
(function () {
  "use strict";

  // ---- shared: inline wordmark (mirrors oh-wordmark + oh-mark in oh-components.css) ----
  function wordmarkHTML() {
    return (
      '<div class="oh-wordmark" style="font-family:var(--font-display);font-weight:700;font-size:18px;' +
      'letter-spacing:-.01em;color:var(--fg);display:inline-flex;align-items:center;gap:9px">' +
      '<span class="oh-mark" style="width:18px;height:18px;display:inline-grid;place-items:center;color:var(--accent)">⬡</span>' +
      "OpenHarnessHub</div>"
    );
  }

  // ---- shared: step-progress strip (pt-steps / pt-step from proto-deep.css) ----
  function stepsHTML(labels, activeIndex) {
    var html = '<div class="pt-steps" style="display:flex;align-items:center;gap:0;margin-bottom:22px;flex-wrap:wrap;justify-content:center">';
    for (var i = 0; i < labels.length; i++) {
      var on = i === activeIndex;
      var nStyle = on
        ? "background:var(--accent);color:var(--accent-ink);border-color:var(--accent)"
        : "background:transparent;color:var(--fg-muted);border-color:var(--line-strong)";
      html +=
        '<span class="pt-step' + (on ? " on" : "") + '" style="display:inline-flex;align-items:center;gap:8px;font-size:12.5px;color:' +
        (on ? "var(--fg)" : "var(--fg-muted)") + '">' +
        '<span class="n" style="width:22px;height:22px;border-radius:50%;border:1px solid;display:grid;place-items:center;font-size:11px;font-weight:700;' + nStyle + '">' +
        (i + 1) +
        "</span>" +
        labels[i] +
        "</span>";
      if (i < labels.length - 1) {
        html += '<span class="arr" style="margin:0 14px;color:var(--fg-faint)">→</span>';
      }
    }
    html += "</div>";
    return html;
  }

  /* ================================================================
     PSignin — /signin
     ================================================================ */
  function renderSignin(ctx) {
    return (
      '<div class="pt-min pt-view">' +
      '<div class="pt-min-card">' +
      '<div class="wm">' + wordmarkHTML() + "</div>" +
      "<h1>Sign in</h1>" +
      '<div class="sub">Governed AI pipelines, on the record.</div>' +
      '<div class="pt-sso">' +
      '<button class="oh-btn oh-btn--ghost" style="justify-content:center" data-nav="/onboarding">Continue with SSO</button>' +
      '<button class="oh-btn oh-btn--ghost" style="justify-content:center" data-nav="/onboarding">Continue with Google</button>' +
      '<div class="pt-field" style="margin-top:8px">' +
      '<label>Work email</label>' +
      '<input id="signin-email" type="email" placeholder="you@company.com" autocomplete="email" />' +
      "</div>" +
      '<button class="oh-btn oh-btn--primary" id="signin-submit" style="justify-content:center">Continue →</button>' +
      '<div style="text-align:center;font-size:12.5px;color:var(--fg-muted);margin-top:6px">No account? <span style="color:var(--accent);cursor:pointer" data-nav="/signup">Sign up free</span></div>' +
      "</div>" +
      "</div>" +
      "</div>"
    );
  }
  function onMountSignin(host, ctx) {
    var btn = host.querySelector("#signin-submit");
    var email = host.querySelector("#signin-email");
    if (btn) {
      btn.addEventListener("click", function () {
        var val = email ? email.value.trim() : "";
        if (!val || val.indexOf("@") < 0) {
          ctx.toast("Enter a valid work email to continue.");
          if (email) email.focus();
          return;
        }
        ctx.navigate("/onboarding");
      });
    }
    if (email) {
      email.addEventListener("keydown", function (e) {
        if (e.key === "Enter") { btn && btn.click(); }
      });
    }
  }

  /* ================================================================
     PSignup — /signup  (same minimal shell, sign-up copy)
     ================================================================ */
  function renderSignup(ctx) {
    return (
      '<div class="pt-min pt-view">' +
      '<div class="pt-min-card">' +
      '<div class="wm">' + wordmarkHTML() + "</div>" +
      "<h1>Create your account</h1>" +
      '<div class="sub">Governed AI pipelines, on the record. Free to start.</div>' +
      '<div class="pt-sso">' +
      '<button class="oh-btn oh-btn--ghost" style="justify-content:center" data-nav="/onboarding">Continue with SSO</button>' +
      '<button class="oh-btn oh-btn--ghost" style="justify-content:center" data-nav="/onboarding">Continue with Google</button>' +
      '<div class="pt-field" style="margin-top:8px">' +
      '<label>Work email</label>' +
      '<input id="signup-email" type="email" placeholder="you@company.com" autocomplete="email" />' +
      "</div>" +
      '<button class="oh-btn oh-btn--primary" id="signup-submit" style="justify-content:center">Create account →</button>' +
      '<div style="text-align:center;font-size:12.5px;color:var(--fg-muted);margin-top:6px">Already have an account? <span style="color:var(--accent);cursor:pointer" data-nav="/signin">Sign in</span></div>' +
      '<div style="text-align:center;font-size:11px;color:var(--fg-faint);margin-top:8px;line-height:1.5">The open spec, SDK &amp; export are free.<br/>Governed components require a plan.</div>' +
      "</div>" +
      "</div>" +
      "</div>"
    );
  }
  function onMountSignup(host, ctx) {
    var btn = host.querySelector("#signup-submit");
    var email = host.querySelector("#signup-email");
    if (btn) {
      btn.addEventListener("click", function () {
        var val = email ? email.value.trim() : "";
        if (!val || val.indexOf("@") < 0) {
          ctx.toast("Enter a valid work email to continue.");
          if (email) email.focus();
          return;
        }
        ctx.navigate("/onboarding");
      });
    }
    if (email) {
      email.addEventListener("keydown", function (e) {
        if (e.key === "Enter") { btn && btn.click(); }
      });
    }
  }

  /* ================================================================
     POnboarding — /onboarding
     Sets state.loggedIn = true then routes to /app or /build.
     ================================================================ */
  var ONB_STEPS = ["Paste a task", "Connect a model", "Pick a domain", "First flow"];

  function renderOnboarding(ctx) {
    var taskVal = (ctx.state && ctx.state.task) ? ctx.state.task : "";
    return (
      '<div class="pt-min pt-view">' +
      '<div class="pt-onb-wrap">' +
      stepsHTML(ONB_STEPS, 0) +
      '<div class="pt-onb-card">' +
      '<h1 style="font-family:var(--font-display);font-size:21px;font-weight:700;margin:0 0 4px;color:var(--fg)">What\'s the first task?</h1>' +
      '<div style="font-size:13px;color:var(--fg-muted);margin-bottom:14px">We\'ll build a costed, cited flow from it — using simulate mode until you connect a key.</div>' +
      '<textarea id="onb-task" class="pt-dash-entry" style="width:100%;min-height:56px;border:1px solid var(--line);border-radius:var(--r-md);background:var(--panel-2);color:var(--fg);font:inherit;resize:none;outline:none;padding:11px" placeholder="Grade a supplier list against CSDDD…">' +
      ctx.esc(taskVal) +
      "</textarea>" +
      '<div style="display:flex;gap:8px;margin-top:12px">' +
      '<button class="oh-btn oh-btn--ghost" id="onb-skip">Skip</button>' +
      '<span class="pt-spacer" style="flex:1"></span>' +
      '<button class="oh-btn oh-btn--primary" id="onb-build">Build my first flow →</button>' +
      "</div>" +
      "</div>" +
      "</div>" +
      "</div>"
    );
  }
  function onMountOnboarding(host, ctx) {
    var ta = host.querySelector("#onb-task");
    var skip = host.querySelector("#onb-skip");
    var build = host.querySelector("#onb-build");

    function setLoggedIn() {
      if (ctx.state) { ctx.state.loggedIn = true; }
    }

    if (ta) {
      ta.addEventListener("input", function () {
        if (ctx.state) { ctx.state.task = ta.value; }
        try { sessionStorage.setItem("ohp-task", ta.value); } catch (e) {}
      });
    }
    if (skip) {
      skip.addEventListener("click", function () {
        setLoggedIn();
        ctx.navigate("/app");
      });
    }
    if (build) {
      build.addEventListener("click", function () {
        var v = ta ? ta.value.trim() : "";
        if (ctx.state) { ctx.state.task = v || ctx.state.task; }
        if (v) { try { sessionStorage.setItem("ohp-task", v); } catch (e) {} }
        setLoggedIn();
        ctx.navigate("/build");
      });
    }
  }

  /* ================================================================
     PUpgrade — /upgrade  (quota paywall)
     ================================================================ */
  function renderUpgrade(ctx) {
    return (
      '<div class="pt-min pt-view">' +
      '<div class="pt-paywall">' +
      '<div class="lock" style="font-size:34px;color:var(--accent)">🔒</div>' +
      '<h1>You\'ve hit the Pro limit</h1>' +
      '<div class="pt-meter" style="height:9px;border-radius:5px;background:var(--bg-subtle);border:1px solid var(--line);overflow:hidden;margin:0 auto 8px;max-width:360px">' +
      '<i style="display:block;height:100%;background:var(--danger);width:100%"></i>' +
      "</div>" +
      '<p>5,000 / 5,000 pipeline-generation calls used this period. Upgrade to Team for higher limits, governance, and daily freshness — or wait for the reset.</p>' +
      '<div style="display:flex;gap:10px;justify-content:center">' +
      '<button class="oh-btn oh-btn--primary" data-nav="/checkout">Upgrade to Team →</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/pricing">Compare plans</button>' +
      "</div>" +
      '<div style="font-size:11.5px;color:var(--fg-faint);margin-top:14px">The open spec, SDK &amp; export are never rate-limited — only governed calls.</div>' +
      "</div>" +
      "</div>"
    );
  }
  function onMountUpgrade(host, ctx) {
    // data-nav delegation handles navigation; no additional interactivity needed.
  }

  /* ================================================================
     Registration — each route gets its own OHH.register call
     ================================================================ */
  if (!window.OHH || typeof window.OHH.register !== "function") {
    // Guard: if app.js hasn't loaded yet the router isn't available.
    // Delay registration until after DOMContentLoaded so app.js can run first.
    document.addEventListener("DOMContentLoaded", function () {
      if (window.OHH && typeof window.OHH.register === "function") {
        window.OHH.register("/signin",     renderSignin,     onMountSignin,     { theme: "light" });
        window.OHH.register("/signup",     renderSignup,     onMountSignup,     { theme: "light" });
        window.OHH.register("/onboarding", renderOnboarding, onMountOnboarding, { theme: "light" });
        window.OHH.register("/upgrade",    renderUpgrade,    onMountUpgrade,    { theme: "light" });
      }
    });
  } else {
    window.OHH.register("/signin",     renderSignin,     onMountSignin,     { theme: "light" });
    window.OHH.register("/signup",     renderSignup,     onMountSignup,     { theme: "light" });
    window.OHH.register("/onboarding", renderOnboarding, onMountOnboarding, { theme: "light" });
    window.OHH.register("/upgrade",    renderUpgrade,    onMountUpgrade,    { theme: "light" });
  }
}());
