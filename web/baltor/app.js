/* Baltor — standalone front-end SPA. Its OWN app (no shared front-end with Open
   Harness Hub); only the backend is shared. Tiny hash router + a shared header; pages self-register
   via CE.register(pattern, render) from pages/*.js (loaded through pages/manifest.json). No build. */
(function () {
  "use strict";
  var BRAND = "Baltor";
  window.CE = window.CE || {};

  var routes = [];
  function register(pattern, render) { routes.push({ pattern: pattern, render: render }); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function current() { return (location.hash || "#/").slice(1) || "/"; }
  function match(r) { for (var i = 0; i < routes.length; i++) if (routes[i].pattern === r) return routes[i]; return null; }

  var MARK = '<span class="oh-mark" aria-hidden="true">' +
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />' +
    '<path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" />' +
    '</svg></span>';

  // header — nav links ONLY to wired routes (no dead links); "Get started" → pricing.
  function header(active) {
    var nav = [["/", "Overview"], ["/engine", "Context Engine"], ["/pricing", "Pricing"], ["/trust", "Trust"]].map(function (p) {
      return '<a data-nav="' + p[0] + '"' + (p[0] === active ? ' style="color:var(--fg);font-weight:600"' : "") + ">" + esc(p[1]) + "</a>";
    }).join("");
    return '<header class="pt-mkt-top">' +
      '<div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + MARK + " " + esc(BRAND) + "</div>" +
      "<nav>" + nav + '<a href="/dashboard.html">Live dashboard</a><a href="/demo-console.html">Live demo</a><a href="/reviews.html">Review queue</a><a href="/admin-demo/">Demo</a><a href="/how-it-works.html">How it works</a><a href="https://aidoneright.dev">AI Done Right</a><a href="https://aidoneright.dev/gtm-launch-guide.html">Launch guide</a><a href="https://openharnesshub.com">OpenHubForAI</a></nav>' +
      '<span class="pt-spacer"></span>' +
      '<a class="oh-btn oh-btn--ghost oh-btn--sm" href="/how-it-works.html" style="margin-right:8px">See how it works</a>' +
      '<button class="oh-btn oh-btn--primary oh-btn--sm" data-nav="/pricing">Get started</button>' +
      "</header>";
  }

  function render() {
    var view = document.getElementById("ce-view");
    if (!view) return;
    var r = match(current()) || match("/");
    view.innerHTML = r ? r.render({ esc: esc, brand: BRAND, header: header })
      : '<div class="pt-mkt pt-view">' + header("/") + '<div class="pt-mkt-body"><div class="pt-page" style="max-width:720px;margin:0 auto;padding:60px 0"><h1>Not found</h1><button class="oh-btn oh-btn--primary" data-nav="/">Back to overview</button></div></div></div>';
    window.scrollTo(0, 0);
  }

  // single delegated nav handler (hash routes in-app; absolute/# links pass through)
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-nav]");
    if (!a) return;
    e.preventDefault();
    var p = a.getAttribute("data-nav");
    if (!p) return;
    if (p.charAt(0) === "#" || /^https?:\/\//.test(p)) { window.location.href = p; }
    else { location.hash = "#" + p; }
  });

  CE.register = register; CE.esc = esc; CE.brand = BRAND; CE.header = header;
  window.addEventListener("hashchange", render);

  // load pages, then route
  fetch("pages/manifest.json").then(function (r) { return r.ok ? r.json() : []; }).then(function (list) {
    var i = 0;
    (function next() {
      if (!list || i >= list.length) { render(); return; }
      var s = document.createElement("script");
      s.src = "pages/" + list[i]; s.onload = s.onerror = function () { i++; next(); };
      document.body.appendChild(s);
    })();
  }).catch(render);
})();
