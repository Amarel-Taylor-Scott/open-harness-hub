/* OpenHubForAI — SDG Solutions pages (vanilla port of proto-sdg.jsx).
   Routes: /solutions (PSolutions gallery) + /solutions/:n (PSolution goal detail).
   Marketing shell, light theme. No framework, no build step. */
(function () {
  "use strict";

  var SDG = [
    [1, '#E5243B', 'No Poverty', 'Living-wage & social-protection compliance'],
    [2, '#DDA63A', 'Zero Hunger', 'Food-supply provenance, safety & nutrition'],
    [3, '#4C9F38', 'Good Health & Well-being', 'GxP & clinical-claim compliance'],
    [4, '#C5192D', 'Quality Education', 'Training-content quality & accessibility'],
    [5, '#FF3A21', 'Gender Equality', 'Pay-equity & diversity disclosures'],
    [6, '#26BDE2', 'Clean Water & Sanitation', 'Water stewardship & discharge permits'],
    [7, '#FCC30B', 'Affordable & Clean Energy', 'Renewable-energy & PPA claims'],
    [8, '#A21942', 'Decent Work & Growth', 'Labour rights & modern-slavery risk'],
    [9, '#FD6925', 'Industry & Infrastructure', 'Supply-chain resilience & R&D claims'],
    [10, '#DD1367', 'Reduced Inequalities', 'Non-discrimination & inclusion'],
    [11, '#FD9D24', 'Sustainable Cities', 'Urban resilience & housing reports'],
    [12, '#BF8B2E', 'Responsible Consumption', 'Circularity, packaging & waste'],
    [13, '#3F7E44', 'Climate Action', 'Scope 1–3 emissions & transition risk'],
    [14, '#0A97D9', 'Life Below Water', 'Seafood sourcing & IUU-fishing risk'],
    [15, '#56C02B', 'Life on Land', 'Deforestation (EUDR) & biodiversity'],
    [16, '#00689D', 'Peace & Justice', 'Sanctions, AML & anti-corruption'],
    [17, '#19486A', 'Partnerships', 'Cross-standard ESG disclosure'],
  ];

  var SDG_BY_N = {};
  SDG.forEach(function (s) { SDG_BY_N[s[0]] = s; });

  // 3 hyper-specific pipelines per goal: [name, input, output]
  var PIPES = {
    1: [['Living-wage gap screen', 'payroll + locale', 'wage-gap report w/ remediation'], ['Social-protection coverage audit', 'workforce roster', 'coverage gaps by country'], ['In-work poverty flag', 'contract terms', 'at-risk worker list']],
    2: [['Food-safety provenance trace', 'lot / batch IDs', 'provenance + recall exposure'], ['Nutrition-claim validator', 'product labels', 'substantiation + violations'], ['Smallholder sourcing audit', 'supplier list', 'smallholder share + fairness']],
    3: [['GxP deviation triage', 'batch records', 'severity + CAPA'], ['Clinical-claim citation check', 'marketing copy', 'cited vs uncited claims'], ['Adverse-event signal scan', 'case narratives', 'signal summary']],
    4: [['Course accessibility audit', 'course content', 'WCAG gaps + fixes'], ['Learning-outcome alignment', 'syllabus', 'outcome coverage map'], ['Credential-fraud check', 'certificates', 'verification report']],
    5: [['Pay-equity gap analysis', 'comp data', 'adjusted gap + drivers'], ['Board-diversity disclosure', 'governance docs', 'disclosure-ready table'], ['Harassment-policy coverage', 'HR policies', 'gap list vs standard']],
    6: [['Discharge-permit compliance', 'effluent data', 'exceedances + permit map'], ['Water-stewardship score', 'site water data', 'stewardship rating'], ['Basin water-stress exposure', 'site locations', 'stress index by basin']],
    7: [['Renewable / PPA claim verify', 'energy contracts', 'verified % renewable'], ['Scope-2 market vs location', 'utility bills', 'dual-reporting table'], ['Energy-attribute cert trace', 'REC IDs', 'provenance + double-count check']],
    8: [['Human-trafficking indicator scan', 'recruitment ads (HK→PH)', 'exploitation indicators + risk'], ['Working-hours / OT compliance', 'time records', 'violations by site'], ['Grievance-mechanism audit', 'grievance logs', 'coverage + response SLA']],
    9: [['Supply-chain resilience map', 'BOM + suppliers', 'single-point-of-failure map'], ['R&D-claim substantiation', 'patent claims', 'cited evidence'], ['Critical-infra dependency', 'asset list', 'dependency risk']],
    10: [['Non-discrimination disclosure', 'HR + policy', 'disclosure pack'], ['Inclusion-metric audit', 'workforce data', 'representation gaps'], ['Accessible-product check', 'product specs', 'accessibility gaps']],
    11: [['311 triage & routing', '311 report stream', 'department + urgency routing'], ['Building-code compliance', 'permits', 'violation list'], ['Urban-resilience exposure', 'asset geolocation', 'hazard exposure']],
    12: [['Circularity / recyclability', 'packaging specs', 'recyclability + EPR fees'], ['Waste-claim verification', 'waste data', 'verified diversion %'], ['Product-LCA hotspot', 'BOM', 'impact hotspots']],
    13: [['Scope 1–3 emissions calc', 'activity data', 'GHG inventory w/ cited factors'], ['Transition-plan gap (TCFD/ISSB)', 'strategy docs', 'gap list'], ['Physical-climate risk', 'asset locations', 'hazard exposure by scenario']],
    14: [['Seafood IUU-fishing risk', 'catch certificates', 'IUU risk + traceability'], ['Marine-discharge (MARPOL)', 'vessel logs', 'exceedances'], ['Sustainable-sourcing (MSC)', 'product list', 'certification coverage']],
    15: [['EUDR deforestation geo-check', 'plot geolocation', 'deforestation-free proof'], ['Biodiversity impact screen', 'site footprint', 'protected-area overlap'], ['Land-rights / FPIC audit', 'land acquisitions', 'FPIC compliance']],
    16: [['OFAC / SDN sanctions screen', 'counterparty list', 'matches + dispositions'], ['Anti-corruption UBO check', 'entity records', 'UBO + red flags'], ['Whistleblower-policy audit', 'policies', 'gap vs EU Directive']],
    17: [['Cross-standard ESG pack', 'raw metrics', 'GRI / ESRS / ISSB mapped pack'], ['Data-sharing agreement check', 'contracts', 'compliance + risk'], ['Multi-framework crosswalk', 'one disclosure', 'mapped to N frameworks']],
  };

  var MARK_SVG = '<span class="oh-mark" aria-hidden="true">' +
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />' +
    '<path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" />' +
    '</svg></span>';

  // Canonical marketing nav items — matches index.html landing header
  var MKT_NAV = [
    ['/pipelines',  'Explore'],
    ['/solutions',  'SDG solutions'],
    ['/app',        'Workspace'],
    ['/pricing',    'Pricing'],
    ['/docs',       'Docs'],
    ['/trust',      'Trust']
  ];

  // ---- shared marketing header HTML ----
  function mktHeader(esc, activeRoute) {
    var navItems = MKT_NAV.map(function (p) {
      var active = p[0] === activeRoute;
      return '<a data-nav="' + p[0] + '"' +
        (active ? ' style="color:var(--fg);font-weight:600"' : '') +
        '>' + p[1] + '</a>';
    }).join('');
    return '<header class="pt-mkt-top">' +
      '<div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + MARK_SVG + ' OpenHubForAI</div>' +
      '<nav>' + navItems + '</nav>' +
      '<span class="pt-spacer"></span>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/signin">Sign in</button>' +
    '</header>';
  }

  // ---- /solutions — PSolutions ----
  function renderSolutions(ctx) {
    var esc = ctx.esc;
    var cardsHtml = '';
    SDG.forEach(function (s) {
      var n = s[0], c = s[1], title = s[2], task = s[3];
      var pipes = PIPES[n] || [];
      var numStr = n < 10 ? '0' + n : String(n);
      cardsHtml +=
        '<button class="pt-sdg-card" style="--sdg:' + esc(c) + '" data-nav="/solutions/' + esc(String(n)) + '">' +
          '<span class="wheel">◎</span>' +
          '<span class="num">' + esc(numStr) + '</span>' +
          '<span class="ttl">' + esc(title) + '</span>' +
          '<span class="task">' + esc(task) + '</span>' +
          '<span class="go">' + esc(String(pipes.length)) + ' pipelines →</span>' +
        '</button>';
    });

    return '<div class="pt-mkt pt-view">' +
      mktHeader(esc, '/solutions') +
      '<div class="pt-mkt-body">' +
        '<div class="pt-page wide">' +
          '<div class="pt-page-head">' +
            '<h1>SDG solutions</h1>' +
            '<div class="sub">Pick a goal to browse its prebuilt, governed pipelines — hyper-specific to the work, not generic.</div>' +
          '</div>' +
          '<div class="pt-sdg-grid">' + cardsHtml + '</div>' +
          '<div class="pt-sdg-pay">' +
            '<span class="gl">🛡</span>' +
            '<span><b>Free to browse; subscription to run.</b> The pipeline shapes &amp; spec are open — running them on <b>governed, live, cited</b> data is the paid product.</span>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  function onMountSolutions(host, ctx) {
    // data-nav delegation is handled globally in app.js; nothing extra needed here.
  }

  // ---- /solutions/:n — PSolution ----
  function renderSolution(ctx) {
    var esc = ctx.esc;
    var n = Number(ctx.params.n);
    var s = SDG_BY_N[n];

    // not-found state
    if (!s) {
      return '<div class="pt-mkt pt-view">' +
        mktHeader(esc, '/solutions') +
        '<div class="pt-mkt-body">' +
          '<div class="pt-page">' +
            '<div class="pt-page-head"><h1>Unknown goal</h1><div class="sub">Goal ' + esc(String(ctx.params.n || '?')) + ' is not one of the 17 SDGs.</div></div>' +
            '<button class="oh-btn oh-btn--ghost" data-nav="/solutions">← All SDG solutions</button>' +
          '</div>' +
        '</div>' +
      '</div>';
    }

    var num = s[0], c = s[1], title = s[2], task = s[3];
    var pipes = PIPES[num] || [];
    var numStr = num < 10 ? '0' + num : String(num);

    var pipeCardsHtml = '';
    if (pipes.length === 0) {
      pipeCardsHtml = '<div class="oh-state-msg" style="color:var(--fg-muted);font-size:13px;padding:24px 0">No pipelines defined for this goal yet.</div>';
    } else {
      pipes.forEach(function (p) {
        var name = p[0], inp = p[1], outp = p[2];
        pipeCardsHtml +=
          '<div class="pt-pipe" style="--sdg:' + esc(c) + '" data-pipe-nav="/flow">' +
            '<div class="pn">' + esc(name) + '</div>' +
            '<div class="pio">' +
              '<span class="in">⎖ ' + esc(inp) + '</span>' +
              '<span class="ar">→</span>' +
              '<span class="out">⎘ ' + esc(outp) + '</span>' +
            '</div>' +
            '<div class="pf"><span class="go">Open pipeline →</span></div>' +
          '</div>';
      });
    }

    return '<div class="pt-mkt pt-view">' +
      mktHeader(esc, '/solutions') +
      '<div class="pt-mkt-body">' +
        '<div class="pt-page wide">' +
          '<div class="pt-crumb" style="margin-bottom:14px">' +
            '<a style="cursor:pointer" data-nav="/solutions">SDG solutions</a>' +
            '<span class="sep">/</span>' +
            '<b>Goal ' + esc(numStr) + '</b>' +
          '</div>' +
          '<div class="pt-sdg-band" style="--sdg:' + esc(c) + '">' +
            '<span class="bignum">' + esc(numStr) + '</span>' +
            '<div>' +
              '<div class="bt">' + esc(title) + '</div>' +
              '<div class="bd">' + esc(task) + ' · ' + esc(String(pipes.length)) + ' prebuilt pipelines, each with a QA / evaluation stage.</div>' +
            '</div>' +
            '<span class="bgwheel">◎</span>' +
          '</div>' +
          '<div class="pt-cards-grid">' + pipeCardsHtml + '</div>' +
          '<div class="pt-sdg-pay">' +
            '<span class="gl">🛡</span>' +
            '<span>Preview free. <b>Run &amp; deploy on a subscription</b> — with live, cited data that stays fresh as the standards for SDG ' + esc(numStr) + ' evolve.</span>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  function onMountSolution(host, ctx) {
    // Wire pipeline cards to navigate to /flow (they use data-pipe-nav, not data-nav,
    // so the global delegation ignores them; we handle it here).
    var pipes = host.querySelectorAll('[data-pipe-nav]');
    for (var i = 0; i < pipes.length; i++) {
      (function (el) {
        el.addEventListener('click', function () {
          ctx.navigate(el.getAttribute('data-pipe-nav'));
        });
      })(pipes[i]);
    }
  }

  // ---- register ----
  window.OpenHubForAI.register('/solutions', renderSolutions, onMountSolutions, { theme: 'light' });
  window.OpenHubForAI.register('/solutions/:n', renderSolution, onMountSolution, { theme: 'light' });

}());
