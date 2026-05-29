/* Open Harness Hub — two-product configuration + host resolver.
   ONE backend, ONE front-end codebase, TWO branded products on TWO domains
   (see docs/strategy/two-services-shared-infrastructure.md). Brand/domain/theme/nav are DATA here, not
   hardcoded in pages — adding or renaming a product is a one-object edit, never a fork.
   Loaded BEFORE app.js so OHH.product()/OHH.brand() are available to every surface. */
(function () {
  "use strict";
  window.OHH = window.OHH || {};

  // The single source of truth for both brands. A new product = one entry; a rename = one string.
  var PRODUCTS = {
    "harness-hub": {
      id: "harness-hub",
      brand: "Open Harness Hub",
      short: "Harness Hub",
      tagline: "Describe a task — lift the pipeline.",
      blurb: "Assemble governed AI pipelines from vetted, measured-lift components.",
      domains: ["openharnesshub.com", "www.openharnesshub.com"],
      home: "/",
      theme: "light",
      title: "Open Harness Hub — describe a task, lift the pipeline"
    },
    "context-enrichment": {
      id: "context-enrichment",
      brand: "Context Enrichment",
      short: "Context Enrichment",
      tagline: "Token-efficient, governed content for any agent.",
      blurb: "Compress content, host it raw · compressed · hyper-efficient, and serve governed corpora + tools straight into open agent loops like Claude Code.",
      // distinctive marks for the day we want something trademarkable: Strata · Substrate · Carrel
      domains: ["contextenrichment.dev", "contextenrichment.ai", "getcontextenrichment.com"],
      home: "/context-enrichment",
      theme: "light",
      title: "Context Enrichment — token-efficient, governed content for any agent"
    }
  };
  var DEFAULT_ID = "harness-hub";

  // Resolve the active product: server pin (window.__OH_PRODUCT__, set per domain/tunnel) →
  // explicit ?product= override (preview) → hostname → default.
  function resolveId() {
    try {
      if (window.__OH_PRODUCT__ && PRODUCTS[window.__OH_PRODUCT__]) return window.__OH_PRODUCT__;
      var q = (window.location.search || "");
      var m = q.match(/[?&]product=([a-z0-9-]+)/);
      if (m && PRODUCTS[m[1]]) return m[1];
      var host = (window.location.hostname || "").toLowerCase();
      for (var id in PRODUCTS) {
        if (!PRODUCTS.hasOwnProperty(id)) continue;
        if ((PRODUCTS[id].domains || []).indexOf(host) !== -1) return id;
      }
    } catch (e) { /* non-browser / sandbox — fall through to default */ }
    return DEFAULT_ID;
  }

  var _cachedId = null;
  function product(id) {
    if (id && PRODUCTS[id]) return PRODUCTS[id];          // explicit lookup (e.g. cross-links)
    if (!_cachedId) _cachedId = resolveId();              // resolve once per load
    return PRODUCTS[_cachedId];
  }

  OHH.PRODUCTS = PRODUCTS;
  OHH.DEFAULT_PRODUCT = DEFAULT_ID;
  OHH.product = product;
  OHH.brand = function () { return product().brand; };    // shared surfaces read this, not a literal
})();
