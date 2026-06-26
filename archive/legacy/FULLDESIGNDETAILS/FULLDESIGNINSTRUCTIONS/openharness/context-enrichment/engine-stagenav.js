/* engine-stagenav.js — mounts the shared 5-stage sub-nav on a Baltor engine deep-dive.
   Call window.mountStageNav('<key>') after DOM is ready; it inserts the nav right after
   the page hero (.cd-hero) so every deep-dive shares one consistent pipeline navigator. */
(function () {
  // the five governed-context engine stages, in pipeline order, each → its deep-dive page.
  var STAGES = [
    ['reconciliation', '01', 'Reconcile', 'pick the authority', 'Baltor Reconciliation Deep-Dive.html'],
    ['anti', '02', 'Harden', 'facts that refresh', 'Baltor Anti-Fragility Deep-Dive.html'],
    ['enhancement', '03', 'Enhance', 'cite & connect', 'Baltor Enhancement Deep-Dive.html'],
    ['optimization', '04', 'Optimize', 'token-lean packs', 'Baltor Optimization Showcase.html'],
    ['verification', '05', 'Verify', 'signed receipts', 'Baltor Receipts Explorer.html'],
  ];
  window.mountStageNav = function (activeKey) {
    var hero = document.querySelector('.cd-hero');
    if (!hero) return;
    var nav = document.createElement('nav');
    nav.className = 'esn';
    nav.setAttribute('aria-label', 'Engine stages');
    nav.innerHTML = STAGES.map(function (s) {
      var on = s[0] === activeKey ? ' on' : '';
      return '<a class="esn-step' + on + '" href="' + s[4] + '"' + (on ? ' aria-current="page"' : '') +
        ' data-track="engine_stage_nav" data-tp-to="' + s[0] + '" data-tp-from="' + (activeKey || '') + '">' +
        '<span class="esn-n">' + s[1] + '</span>' +
        '<span class="esn-nm">' + s[2] + '</span>' +
        '<span class="esn-d">' + s[3] + '</span></a>';
    }).join('');
    var cap = document.createElement('div');
    cap.className = 'esn-cap';
    cap.textContent = 'one governed pipeline · jump to any stage';
    // insert right after the hero
    hero.parentNode.insertBefore(nav, hero.nextSibling);
    nav.parentNode.insertBefore(cap, nav.nextSibling);
  };
})();
