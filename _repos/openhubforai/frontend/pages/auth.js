/* OpenHubForAI — auth screen module
   Routes: /signin · /signup · /onboarding · /upgrade · /account/keys
   Minimal light shell. Originally ported from proto-wide.jsx (PSignin / POnboarding / PUpgrade);
   now WIRED to the local Identity & Access service via identity.js (realm: openhubforai) —
   real register → onboard → login → session, honest degradation when the service is down
   (never fakes a login), and an API-keys console (raw key shown once, never persisted).
   SSO/Google stay disabled: real providers are an owner-gated CredentialProviderPort seam.
   No build step, no framework, no imports. Registers via OpenHubForAI.register(). */
(function () {
  "use strict";

  // signup → onboarding handoff: held in module memory ONLY (the secret is never stored)
  var pendingSignup = null;

  var SERVICE_DOWN_MSG = "Local identity service is not running — start it: python -m scripts.identity_local_service --serve";

  function identityReady() { return !!(window.OHHIdentity && typeof window.OHHIdentity.login === "function"); }

  // ---- shared: inline wordmark — canonical SVG mark + spaced product name ----
  var AUTH_MARK_SVG = '<span class="oh-mark" aria-hidden="true">' +
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />' +
    '<path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" />' +
    '</svg></span>';

  function wordmarkHTML() {
    return '<div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + AUTH_MARK_SVG + ' OpenHubForAI</div>';
  }

  // SSO providers are an owner-gated seam (CredentialProviderPort) — rendered disabled, never faked
  function ssoButtonsHTML() {
    var title = "Owner-gated seam (CredentialProviderPort) — not available in local dev";
    return (
      '<button class="oh-btn oh-btn--ghost" style="justify-content:center;opacity:.55;cursor:not-allowed" disabled title="' + title + '">Continue with SSO</button>' +
      '<button class="oh-btn oh-btn--ghost" style="justify-content:center;opacity:.55;cursor:not-allowed" disabled title="' + title + '">Continue with Google</button>'
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
     PSignin — /signin  (real login against the openhubforai realm)
     ================================================================ */
  function renderSignin(ctx) {
    return (
      '<div class="pt-min pt-view">' +
      '<div class="pt-min-card">' +
      '<div class="wm">' + wordmarkHTML() + "</div>" +
      "<h1>Sign in</h1>" +
      '<div class="sub">Governed AI pipelines, on the record.</div>' +
      '<div class="pt-sso">' +
      ssoButtonsHTML() +
      '<div class="pt-field" style="margin-top:8px">' +
      '<label>Work email</label>' +
      '<input id="signin-email" type="email" placeholder="you@company.com" autocomplete="email" />' +
      "</div>" +
      '<div class="pt-field">' +
      '<label>Passphrase</label>' +
      '<input id="signin-pass" type="password" placeholder="your passphrase" autocomplete="current-password" />' +
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
    var pass = host.querySelector("#signin-pass");
    if (btn) {
      btn.addEventListener("click", function () {
        var val = email ? email.value.trim() : "";
        var sec = pass ? pass.value : "";
        if (!val || val.indexOf("@") < 0) {
          ctx.toast("Enter a valid work email to continue.");
          if (email) email.focus();
          return;
        }
        if (!sec) {
          ctx.toast("Enter your passphrase.");
          if (pass) pass.focus();
          return;
        }
        if (!identityReady()) { ctx.toast(SERVICE_DOWN_MSG); return; }
        btn.disabled = true;
        window.OHHIdentity.login(val, sec).then(function (r) {
          btn.disabled = false;
          if (r.status === 200) {
            if (ctx.state) { ctx.state.loggedIn = true; }
            ctx.toast("Signed in.");
            ctx.navigate("/app");
          } else {
            ctx.toast("Login rejected — check your email/passphrase, or finish onboarding first.");
          }
        }, function () {
          btn.disabled = false;
          ctx.toast(SERVICE_DOWN_MSG);
        });
      });
    }
    [email, pass].forEach(function (el) {
      if (el) {
        el.addEventListener("keydown", function (e) {
          if (e.key === "Enter") { btn && btn.click(); }
        });
      }
    });
  }

  /* ================================================================
     PSignup — /signup  (real registration; secret kept in memory only
     for the onboarding handoff, never stored)
     ================================================================ */
  function renderSignup(ctx) {
    return (
      '<div class="pt-min pt-view">' +
      '<div class="pt-min-card">' +
      '<div class="wm">' + wordmarkHTML() + "</div>" +
      "<h1>Create your account</h1>" +
      '<div class="sub">Governed AI pipelines, on the record. Free to start.</div>' +
      '<div class="pt-sso">' +
      ssoButtonsHTML() +
      '<div class="pt-field" style="margin-top:8px">' +
      '<label>Work email</label>' +
      '<input id="signup-email" type="email" placeholder="you@company.com" autocomplete="email" />' +
      "</div>" +
      '<div class="pt-field">' +
      '<label>Passphrase</label>' +
      '<input id="signup-pass" type="password" placeholder="choose a passphrase" autocomplete="new-password" />' +
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
    var pass = host.querySelector("#signup-pass");
    if (btn) {
      btn.addEventListener("click", function () {
        var val = email ? email.value.trim() : "";
        var sec = pass ? pass.value : "";
        if (!val || val.indexOf("@") < 0) {
          ctx.toast("Enter a valid work email to continue.");
          if (email) email.focus();
          return;
        }
        if (sec.length < 8) {
          ctx.toast("Choose a passphrase of at least 8 characters.");
          if (pass) pass.focus();
          return;
        }
        if (!identityReady()) { ctx.toast(SERVICE_DOWN_MSG); return; }
        btn.disabled = true;
        window.OHHIdentity.register(val, sec).then(function (r) {
          btn.disabled = false;
          if (r.status === 201) {
            pendingSignup = {
              accountId: r.body.account_id,
              identifier: val,
              secret: sec,                              // memory only; cleared after onboarding
              steps: r.body.onboarding_steps || []
            };
            ctx.navigate("/onboarding");
          } else {
            ctx.toast(r.body && r.body.error ? r.body.error : "Registration failed.");
          }
        }, function () {
          btn.disabled = false;
          ctx.toast(SERVICE_DOWN_MSG);
        });
      });
    }
    [email, pass].forEach(function (el) {
      if (el) {
        el.addEventListener("keydown", function (e) {
          if (e.key === "Enter") { btn && btn.click(); }
        });
      }
    });
  }

  /* ================================================================
     POnboarding — /onboarding
     Completes the realm's onboarding steps + auto-login when arriving
     from /signup; otherwise honors an existing session. Only a REAL
     session sets loggedIn — demo mode is labeled, never silent.
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
      '<div style="font-size:13px;color:var(--fg-muted);margin-bottom:14px">We\'ll build a costed, cited flow from it — using simulate mode until you connect a key.' +
      (pendingSignup ? " Finishing here also activates your account (verify · terms · profile)." : "") +
      "</div>" +
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

    // Real activation: finish the realm's onboarding steps, then auto-login. Resolves true only
    // when a REAL session exists; demo fallback is labeled via toast and does NOT claim a session.
    function completeAuth() {
      if (pendingSignup && identityReady()) {
        var p = pendingSignup;
        var chain = Promise.resolve();
        p.steps.forEach(function (step) {
          chain = chain.then(function () { return window.OHHIdentity.onboard(p.accountId, step); });
        });
        return chain.then(function () {
          return window.OHHIdentity.login(p.identifier, p.secret);
        }).then(function (r) {
          pendingSignup = null;                          // clears the in-memory secret
          if (r.status === 200) { ctx.toast("Account activated — signed in."); return true; }
          ctx.toast("Activation incomplete — sign in manually.");
          return false;
        }, function () {
          pendingSignup = null;
          ctx.toast(SERVICE_DOWN_MSG);
          return false;
        });
      }
      if (identityReady()) {
        return window.OHHIdentity.validate().then(function (ok) {
          if (!ok) { ctx.toast("Demo mode — no local identity session (sign in for a real one)."); }
          return ok;
        });
      }
      ctx.toast("Demo mode — identity client not loaded.");
      return Promise.resolve(false);
    }

    function finish(nav) {
      completeAuth().then(function (real) {
        if (ctx.state) { ctx.state.loggedIn = real || ctx.state.loggedIn || false; ctx.state.demoAuth = !real; }
        ctx.navigate(nav);
      });
    }

    if (ta) {
      ta.addEventListener("input", function () {
        if (ctx.state) { ctx.state.task = ta.value; }
        try { sessionStorage.setItem("ohp-task", ta.value); } catch (e) {}
      });
    }
    if (skip) {
      skip.addEventListener("click", function () { finish("/app"); });
    }
    if (build) {
      build.addEventListener("click", function () {
        var v = ta ? ta.value.trim() : "";
        if (ctx.state) { ctx.state.task = v || ctx.state.task; }
        if (v) { try { sessionStorage.setItem("ohp-task", v); } catch (e) {} }
        finish("/build");
      });
    }
  }

  /* ================================================================
     PKeys — /account/keys  (API-key console: hash-only at rest server-
     side; the raw key is shown ONCE here and never persisted)
     ================================================================ */
  function renderKeys(ctx) {
    return (
      '<div class="pt-min pt-view">' +
      '<div class="pt-onb-wrap" style="max-width:560px">' +
      '<div class="pt-onb-card">' +
      '<div class="wm" style="margin-bottom:8px">' + wordmarkHTML() + "</div>" +
      "<h1 style=\"font-family:var(--font-display);font-size:21px;font-weight:700;margin:0 0 4px;color:var(--fg)\">API keys</h1>" +
      '<div style="font-size:13px;color:var(--fg-muted);margin-bottom:12px">Realm-scoped keys for the local service. Stored hash-only server-side; the raw key is shown <b>once</b> at mint — copy it then.</div>' +
      '<div id="keys-gate" style="font-size:12.5px;color:var(--fg-muted)"></div>' +
      '<div id="keys-new" style="display:none;margin:10px 0">' +
      '<label style="font-size:11.5px;color:var(--fg-faint)">New key (shown once)</label>' +
      '<input id="keys-raw" readonly style="width:100%;font-family:var(--font-mono,monospace);font-size:12px;padding:9px;border:1px solid var(--accent);border-radius:var(--r-md);background:var(--panel-2);color:var(--fg)" />' +
      "</div>" +
      '<div id="keys-list" style="margin:10px 0"></div>' +
      '<div style="display:flex;gap:8px;margin-top:10px">' +
      '<button class="oh-btn oh-btn--primary" id="keys-mint">Mint key</button>' +
      '<span class="pt-spacer" style="flex:1"></span>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/app">Back to app</button>' +
      "</div>" +
      "</div>" +
      "</div>" +
      "</div>"
    );
  }
  function onMountKeys(host, ctx) {
    var gate = host.querySelector("#keys-gate");
    var list = host.querySelector("#keys-list");
    var mint = host.querySelector("#keys-mint");
    var newBox = host.querySelector("#keys-new");
    var rawField = host.querySelector("#keys-raw");

    function refresh() {
      if (!identityReady()) {
        if (gate) gate.textContent = SERVICE_DOWN_MSG;
        if (mint) mint.disabled = true;
        return;
      }
      window.OHHIdentity.listKeys().then(function (r) {
        if (r.status !== 200) {
          if (gate) gate.innerHTML = 'Sign in first — <span style="color:var(--accent);cursor:pointer" data-nav="/signin">go to sign in</span>.';
          if (mint) mint.disabled = true;
          return;
        }
        if (gate) gate.textContent = "";
        if (mint) mint.disabled = false;
        var rows = r.body.api_keys.map(function (k) {
          return '<div style="display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid var(--line);font-size:12.5px">' +
            '<code style="font-family:var(--font-mono,monospace)">' + ctx.esc(k.prefix) + "</code>" +
            '<span style="color:var(--fg-faint)">' + ctx.esc((k.scopes || []).join(" · ")) + "</span>" +
            '<span class="pt-spacer" style="flex:1"></span>' +
            (k.revoked_at
              ? '<span style="color:var(--fg-faint)">revoked</span>'
              : '<button class="oh-btn oh-btn--ghost" data-revoke="' + ctx.esc(k.key_id) + '" style="font-size:11px;padding:3px 9px">Revoke</button>') +
            "</div>";
        }).join("");
        if (list) list.innerHTML = rows || '<div style="font-size:12.5px;color:var(--fg-faint)">No keys yet.</div>';
        if (list) {
          Array.prototype.forEach.call(list.querySelectorAll("[data-revoke]"), function (b) {
            b.addEventListener("click", function () {
              window.OHHIdentity.revokeKey(b.getAttribute("data-revoke")).then(refresh);
            });
          });
        }
      }, function () { if (gate) gate.textContent = SERVICE_DOWN_MSG; });
    }

    if (mint) {
      mint.addEventListener("click", function () {
        window.OHHIdentity.mintKey(["read"]).then(function (r) {
          if (r.status === 201) {
            if (newBox) newBox.style.display = "block";
            if (rawField) { rawField.value = r.body.api_key; rawField.select(); }
            ctx.toast("Key minted — copy it now; it is never shown again.");
            refresh();
          } else {
            ctx.toast(r.body && r.body.error ? r.body.error : "Mint failed — sign in first.");
          }
        }, function () { ctx.toast(SERVICE_DOWN_MSG); });
      });
    }
    refresh();
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
     Registration — each route gets its own OpenHubForAI.register call
     ================================================================ */
  function registerAll() {
    window.OpenHubForAI.register("/signin",       renderSignin,     onMountSignin,     { theme: "light" });
    window.OpenHubForAI.register("/signup",       renderSignup,     onMountSignup,     { theme: "light" });
    window.OpenHubForAI.register("/onboarding",   renderOnboarding, onMountOnboarding, { theme: "light" });
    window.OpenHubForAI.register("/upgrade",      renderUpgrade,    onMountUpgrade,    { theme: "light" });
    window.OpenHubForAI.register("/account/keys", renderKeys,       onMountKeys,       { theme: "light" });
  }
  if (!window.OpenHubForAI || typeof window.OpenHubForAI.register !== "function") {
    // Guard: if app.js hasn't loaded yet the router isn't available.
    // Delay registration until after DOMContentLoaded so app.js can run first.
    document.addEventListener("DOMContentLoaded", function () {
      if (window.OpenHubForAI && typeof window.OpenHubForAI.register === "function") { registerAll(); }
    });
  } else {
    registerAll();
  }
}());
