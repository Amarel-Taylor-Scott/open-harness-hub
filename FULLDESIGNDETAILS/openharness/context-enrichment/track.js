/* track.js — declarative analytics for the Baltor static surfaces.
   Loads AFTER ../shared/oh-experiments.js. Wires ONE delegated click listener:
   any element with data-track="event_name" emits OHExp.track(name, props) on click,
   where props come from data-tp-<key>="value" attributes. Safe no-op if OHExp is absent
   (pages stay standalone-openable). Emits a page_view on load using <body data-page>.

   Example:  <a href="…" data-track="engine_stage_open" data-tp-stage="reconciliation">
   The shared experiments engine attaches the active A/B assignments + visitor id and
   fans the event out to window.dataLayer + any OHExp.onTrack sink (GA4/Segment/PostHog). */
(function () {
  function exp() { return (typeof window !== 'undefined') && window.OHExp; }
  function send(name, props) { var E = exp(); if (E && name) try { E.track(name, props || {}); } catch (e) {} }

  function propsFrom(el) {
    var p = {};
    if (!el || !el.attributes) return p;
    for (var i = 0; i < el.attributes.length; i++) {
      var a = el.attributes[i];
      if (a.name.indexOf('data-tp-') === 0) p[a.name.slice(8).replace(/-/g, '_')] = a.value;
    }
    return p;
  }

  document.addEventListener('click', function (e) {
    var el = e.target && e.target.closest ? e.target.closest('[data-track]') : null;
    if (!el) return;
    send(el.getAttribute('data-track'), propsFrom(el));
  }, true); // capture: fire before any navigation handler

  function pageView() {
    var page = (document.body && document.body.getAttribute('data-page')) || document.title || 'page';
    send('page_view', { page: page });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', pageView);
  else pageView();

  // expose a tiny helper for inline/programmatic events
  window.ohTrack = send;
})();
