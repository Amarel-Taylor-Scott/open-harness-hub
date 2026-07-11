/* OpenHubForAI — govern module
   Faithful port of proto-wide.jsx (PTrustCenter, PAuditLog, PRoles, PKnowledgeEntry,
   PProvenance) and proto-pub.jsx (PPublish) to vanilla JS / no-build static front-end.
   Registers: /trust (light) · /audit-log · /roles · /k/:id · /p/:id · /publish (dark).
*/
(function () {
  "use strict";

  /* =====================================================================
     SHARED HELPERS
     ===================================================================== */

  // Canonical marketing wordmark — matches index.html + sdg.js + landings.js
  var MARK_SVG = '<span class="oh-mark" aria-hidden="true">' +
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" />' +
    '<path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" />' +
    '</svg></span>';

  // Canonical marketing nav items — matches index.html landing header
  var MKT_NAV = [
    ['/pipelines', 'Explore'],
    ['/compare',   'Compare'],
    ['/solutions', 'SDG solutions'],
    ['/pricing',   'Pricing'],
    ['/docs',      'Docs'],
    ['/trust',     'Trust']
  ];
  var FAMILY_LINKS = [
    ['https://baltor.ai', 'Baltor'],
    ['https://aidoneright.dev', 'AI Done Right']
  ];

  function mktHeader(activeRoute) {
    var navItems = MKT_NAV.map(function (p) {
      var active = p[0] === activeRoute;
      return '<a data-nav="' + p[0] + '"' +
        (active ? ' style="color:var(--fg);font-weight:600"' : '') +
        '>' + p[1] + '</a>';
    }).join('');
    var familyLinks = FAMILY_LINKS.map(function (p) {
      return '<a href="' + p[0] + '">' + p[1] + '</a>';
    }).join('');
    return '<header class="pt-mkt-top">' +
      '<div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + MARK_SVG + ' OpenHubForAI</div>' +
      '<nav>' + navItems + familyLinks + '</nav>' +
      '<span class="pt-spacer"></span>' +
      '<button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/signin">Sign in</button>' +
    '</header>';
  }
  function mkSwitch(on) {
    return '<span class="pt-switch' + (on ? ' on' : '') + '" role="switch" aria-checked="' + (on ? 'true' : 'false') + '"><i></i></span>';
  }

  function mkSeg(pairs, active) {
    // pairs: [[value, label], ...]
    var html = '<div class="pt-seg">';
    pairs.forEach(function (p) {
      html += '<button class="' + (p[0] === active ? 'on' : '') + '" data-val="' + p[0] + '">' + p[1] + '</button>';
    });
    html += '</div>';
    return html;
  }

  /* =====================================================================
     /trust — PTrustCenter (marketing shell, light theme)
     ===================================================================== */
  var TRUST_CARDS = [
    ['🛡', 'Signed provenance',    'Every fact carries a C2PA signature traceable to a primary source and capture date.'],
    ['🏅', 'Verified publishers',  '46 signed publishers — agencies, standards bodies, domain experts.'],
    ['🔏', 'Canary &amp; watermark', 'Honeytoken facts detect redistribution; licenses enforce no-resale.'],
    ['⚖', 'Compliance',           'SOC 2 Type II · GDPR · EU-AI-Act conformity records.'],
    ['🔒', 'Data handling',        'No real PII; synthetic/public only; tenant isolation; BYO-key.'],
    ['⟳', 'Revocation',           'Withdrawn facts are pulled from flows and attestations within SLA.']
  ];

  function renderTrust(ctx) {
    var cards = TRUST_CARDS.map(function (c) {
      return '<div class="pt-trust-card">' +
        '<div class="ic">' + c[0] + '</div>' +
        '<div class="t">' + c[1] + '</div>' +
        '<div class="d">' + c[2] + '</div>' +
        '</div>';
    }).join('');

    return '<div class="pt-mkt pt-view">' +
      mktHeader('/trust') +
      '<div class="pt-mkt-body">' +
        '<div class="pt-page wide pt-view">' +
          '<div class="pt-page-head">' +
            '<h1>Trust center</h1>' +
            '<div class="sub">The moat, on one page — how provenance, verification, and compliance actually work.</div>' +
          '</div>' +
          '<div class="pt-trust-grid">' + cards + '</div>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  OpenHubForAI.register("/trust", renderTrust, null, { theme: "light" });

  /* =====================================================================
     /audit-log — PAuditLog (app shell, dark theme)
     ===================================================================== */
  var AUDIT_ROWS = [
    ['2026-05-28 12:04', 'nadia@acme.co',  'flow.deploy',      'flow/csddd-grade'],
    ['2026-05-28 11:40', 'system',          'cdc.amend',        'csddd-articles · art-8'],
    ['2026-05-28 09:15', 'jonas@acme.co',   'component.pin',    'ofac-sdn@1.4.0'],
    ['2026-05-27 16:22', 'system',          'gate.block',       'gxp-sops · unsourced'],
    ['2026-05-27 14:01', 'priya@acme.co',   'key.rotate',       'oh_live_••••a31f']
  ];

  function renderAuditLog(ctx) {
    var rows = AUDIT_ROWS.map(function (r) {
      return '<tr>' +
        '<td style="font-family:var(--font-mono);font-size:11px">' + ctx.esc(r[0]) + '</td>' +
        '<td>' + ctx.esc(r[1]) + '</td>' +
        '<td style="font-family:var(--font-mono);font-size:11px;color:var(--accent)">' + ctx.esc(r[2]) + '</td>' +
        '<td style="font-family:var(--font-mono);font-size:11px">' + ctx.esc(r[3]) + '</td>' +
        '</tr>';
    }).join('');

    return '<div class="pt-page wide pt-view">' +
      '<div class="pt-page-head">' +
        '<h1>Audit log</h1>' +
        '<div class="sub">Immutable, exportable record of every governance &amp; access event.</div>' +
      '</div>' +
      '<div class="pt-toolbar">' +
        '<span class="oh-badge" style="font-family:var(--font-mono)">append-only</span>' +
        '<span class="pt-spacer"></span>' +
        '<button class="oh-btn oh-btn--ghost oh-btn--sm" id="audit-export-btn">Export</button>' +
      '</div>' +
      '<div class="pt-panel">' +
        '<table class="pt-table">' +
          '<thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Object</th></tr></thead>' +
          '<tbody>' + rows + '</tbody>' +
        '</table>' +
      '</div>' +
    '</div>';
  }

  function mountAuditLog(host, ctx) {
    var btn = host.querySelector('#audit-export-btn');
    if (btn) btn.addEventListener('click', function () { ctx.toast('Audit log exported (CSV)'); });
  }

  OpenHubForAI.register("/audit-log", renderAuditLog, mountAuditLog, { theme: "dark" });

  /* =====================================================================
     /roles — PRoles (app shell, dark theme)
     ===================================================================== */
  var ROLE_CAPS = [
    'Browse catalog',
    'Build &amp; run flows',
    'Deploy',
    'Manage private registry',
    'Connect MCP / keys',
    'Review &amp; promote',
    'Manage billing',
    'Admin &amp; roles'
  ];
  var ROLES = [
    { name: 'Owner',    level: 8 },
    { name: 'Admin',    level: 7 },
    { name: 'Builder',  level: 5 },
    { name: 'Reviewer', level: 4 },
    { name: 'Viewer',   level: 1 }
  ];

  function renderRoles(ctx) {
    var headCols = ROLES.map(function (r) {
      return '<th style="text-align:center">' + ctx.esc(r.name) + '</th>';
    }).join('');

    var bodyRows = ROLE_CAPS.map(function (cap, ci) {
      var cells = ROLES.map(function (r) {
        var allowed = ci < r.level;
        return '<td style="text-align:center;color:' + (allowed ? 'var(--success)' : 'var(--fg-faint)') + '">' +
          (allowed ? '✓' : '·') + '</td>';
      }).join('');
      return '<tr><td>' + cap + '</td>' + cells + '</tr>';
    }).join('');

    return '<div class="pt-page wide pt-view">' +
      '<div class="pt-page-head">' +
        '<h1>Roles &amp; permissions</h1>' +
        '<div class="sub">RBAC — define who can do what. Custom roles supported on Enterprise.</div>' +
      '</div>' +
      '<div class="pt-panel">' +
        '<table class="pt-table">' +
          '<thead><tr><th>Capability</th>' + headCols + '</tr></thead>' +
          '<tbody>' + bodyRows + '</tbody>' +
        '</table>' +
        '<button class="oh-btn oh-btn--ghost oh-btn--sm" id="roles-new-btn" style="margin-top:14px">+ Custom role</button>' +
      '</div>' +
    '</div>';
  }

  function mountRoles(host, ctx) {
    var btn = host.querySelector('#roles-new-btn');
    if (btn) btn.addEventListener('click', function () { ctx.toast('New custom role'); });
  }

  OpenHubForAI.register("/roles", renderRoles, mountRoles, { theme: "dark" });

  /* =====================================================================
     /k/:id — PKnowledgeEntry (app shell, dark theme)
     ===================================================================== */
  function renderKnowledgeEntry(ctx) {
    var id = ctx.params.id || '';
    if (!id) {
      return '<div class="pt-page pt-view"><div class="pt-page-head"><h1>Knowledge entry</h1></div>' +
        '<div class="oh-state-msg blocked"><span class="gl">⚠</span><span>No entry ID specified.</span></div></div>';
    }

    // Use id-specific display data or sensible defaults
    var isArt83 = (id === 'art-8-3' || id === 'k-art-8-3');
    var title   = isArt83
      ? 'CSDDD Art. 8(3) — due-diligence on actual adverse impacts'
      : 'Knowledge entry · ' + id;
    var content = isArt83
      ? '"Member States shall ensure that companies take appropriate measures to bring actual adverse impacts to an end…" (excerpt · 13 languages available)'
      : 'Content for entry ' + ctx.esc(id) + '.';
    var sourceUrl   = isArt83 ? 'eur-lex.europa.eu'  : 'source pending';
    var captured    = isArt83 ? '2026-05-28'         : '—';
    var lastVerified = isArt83 ? '2026-05-28'        : '—';
    var license     = isArt83 ? 'CC-BY-4.0'          : '—';
    var usedIn      = isArt83 ? '214 answers'        : '—';
    var provId      = isArt83 ? 'k-art-8-3'          : id;
    var parentSlug  = isArt83 ? 'csddd-articles'     : 'catalog';

    return '<div class="pt-page pt-view">' +
      '<div class="pt-crumb" style="margin-bottom:14px">' +
        '<a style="cursor:pointer" data-nav="/c/' + ctx.esc(parentSlug) + '">' + ctx.esc(parentSlug) + '</a>' +
        '<span class="sep">/</span>' +
        '<b>entry · ' + ctx.esc(id) + '</b>' +
      '</div>' +
      '<div class="pt-row" style="gap:16px;flex-wrap:wrap;align-items:flex-start">' +
        '<div class="pt-kentry" style="flex:2 1 420px">' +
          '<div style="font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--p-knowledge)">&#x26C1; Knowledge entry</div>' +
          '<h1 style="font-family:var(--font-display);font-size:20px;font-weight:700;margin:6px 0;color:var(--fg)">' + ctx.esc(title) + '</h1>' +
          '<div class="content">' + ctx.esc(content) + '</div>' +
          '<div class="oh-cc-badges">' +
            '<span class="oh-badge oh-badge--verified">&#x2714; sourced</span>' +
            '<span class="oh-badge oh-badge--lift">&#x27F3; fresh</span>' +
            '<span class="oh-badge" style="font-family:var(--font-mono)">rag · exact-id</span>' +
          '</div>' +
        '</div>' +
        '<div style="flex:1 1 240px">' +
          '<div class="pt-panel">' +
            '<div class="oh-cc-id" style="font-family:var(--font-mono);font-size:10px;color:var(--fg-faint);margin-bottom:8px">provenance · this entry</div>' +
            '<div class="pt-kv"><span class="k">source</span><span class="v">' + ctx.esc(sourceUrl) + '</span></div>' +
            '<div class="pt-kv"><span class="k">captured</span><span class="v">' + ctx.esc(captured) + '</span></div>' +
            '<div class="pt-kv"><span class="k">last-verified</span><span class="v">' + ctx.esc(lastVerified) + '</span></div>' +
            '<div class="pt-kv"><span class="k">license</span><span class="v">' + ctx.esc(license) + '</span></div>' +
            '<div class="pt-kv"><span class="k">used in</span><span class="v">' + ctx.esc(usedIn) + '</span></div>' +
            '<button class="oh-btn oh-btn--ghost oh-btn--sm" style="width:100%;justify-content:center;margin-top:12px" data-nav="/p/' + ctx.esc(provId) + '">View provenance graph →</button>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  OpenHubForAI.register("/k/:id", renderKnowledgeEntry, null, { theme: "dark" });

  /* =====================================================================
     /p/:id — PProvenance (app shell, dark theme)
     ===================================================================== */
  var PROV_TRAIL = [
    { color: 'var(--p-knowledge)',  glyph: '&#x26C1;', heading: 'Primary source',   detail: 'EUR-Lex · CSDDD consolidated text',                                  dt: '2026-05-28 · captured by esg-scout-01' },
    { color: 'var(--verified)',     glyph: '&#x2714;', heading: 'Verified &amp; signed',  detail: 'license CC-BY-4.0 confirmed · C2PA signature 0x9c1b…a31f',     dt: '2026-05-28 11:40' },
    { color: 'var(--p-conditional)', glyph: '&#x25C8;', heading: 'Transformed',      detail: 'split to article level · 13 languages · dedup',                      dt: '2026-05-28' },
    { color: 'var(--p-action)',     glyph: '&#x26A1;', heading: 'Cited by',          detail: 'harness/esg-cite-first · 11 flows reference this entry',              dt: 'live' },
    { color: 'var(--p-output)',     glyph: '&#x2398;', heading: 'Attested in',       detail: 'flow/csddd-grade · cert valid through 2026-08-26',                    dt: 'live' }
  ];

  function renderProvenance(ctx) {
    var id = ctx.params.id || '';
    if (!id) {
      return '<div class="pt-page pt-view"><div class="pt-page-head"><h1>Provenance graph</h1></div>' +
        '<div class="oh-state-msg blocked"><span class="gl">⚠</span><span>No provenance ID specified.</span></div></div>';
    }

    var steps = PROV_TRAIL.map(function (s) {
      return '<div class="pt-trail-step">' +
        '<span class="dot" style="background:' + s.color + '">' + s.glyph + '</span>' +
        '<div class="c">' +
          '<div class="h">' + s.heading + '</div>' +
          '<div class="d">' + s.detail + '</div>' +
          '<div class="dt">' + s.dt + '</div>' +
        '</div>' +
      '</div>';
    }).join('');

    return '<div class="pt-page pt-view">' +
      '<div class="pt-page-head">' +
        '<h1>Provenance graph</h1>' +
        '<div class="sub">Every object traces source → signature → transforms → citations → attestation, with revocation lineage.</div>' +
      '</div>' +
      '<div class="pt-panel" style="max-width:640px">' +
        '<div class="pt-trail">' + steps + '</div>' +
        '<div class="oh-state-msg" style="margin-top:6px;background:color-mix(in srgb,var(--verified) 7%,transparent);border:1px solid color-mix(in srgb,var(--verified) 30%,var(--line));display:flex;gap:9px">' +
          '<span class="gl" style="color:var(--verified)">&#x1F6E1;</span>' +
          '<span>If the source revokes or amends this fact, the change propagates down the chain — citing flows are flagged and attestations invalidated automatically.</span>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  OpenHubForAI.register("/p/:id", renderProvenance, null, { theme: "dark" });

  /* =====================================================================
     /publish — PPublish (app shell, dark theme)
     ===================================================================== */
  var PUBLISH_MODES = [
    ['fact', 'A fact'],
    ['page', 'A knowledge page'],
    ['repo', 'A repository']
  ];

  var PUBLISHED_OBJECTS = [
    { id: 'knowledge-page/living-wage-method', status: 'promoted ▲ +0.22', ok: true },
    { id: 'fact/csddd-art-8-3',               status: 'verified ✔',        ok: true },
    { id: 'corpus/acme-runbook',              status: 'measuring lift',         ok: false }
  ];

  function renderPublish(ctx) {
    var modeButtons = PUBLISH_MODES.map(function (m) {
      return '<button class="pt-seg-btn" data-mode="' + m[0] + '" data-active="false">' + m[1] + '</button>';
    }).join('');

    var publishedList = PUBLISHED_OBJECTS.map(function (o) {
      return '<div class="pt-srv">' +
        '<span class="dot" style="background:' + (o.ok ? 'var(--success)' : 'var(--warning)') + '"></span>' +
        '<span class="nm" style="font-family:var(--font-mono);font-size:11px">' + ctx.esc(o.id) +
          '<small>' + ctx.esc(o.status) + ' · immutable</small>' +
        '</span>' +
        '<span style="font-size:10.5px;color:var(--fg-faint)">&#x1F512; public</span>' +
      '</div>';
    }).join('');

    return '<div class="pt-page wide pt-view">' +
      '<div class="pt-page-head">' +
        '<h1>Publish to the ecosystem</h1>' +
        '<div class="sub">Share your own facts, knowledge pages, and repositories. Once published they are <b>immutable, signed, and permanently public</b> &mdash; discoverable by everyone, citable with provenance back to you.</div>' +
      '</div>' +
      '<div class="pt-intent">' +
        // Left column
        '<div>' +
          '<div class="pt-panel">' +
            '<div class="pt-setting-row" style="padding-top:4px">' +
              '<div class="info"><div class="t">What are you sharing?</div></div>' +
              '<div class="pt-seg" id="pub-mode-seg">' + modeButtons + '</div>' +
            '</div>' +
            // Fact fields (default visible)
            '<div id="pub-fields-fact">' +
              '<div class="pt-field"><label>Fact / claim</label><input id="pub-fact-claim" placeholder="e.g. CSDDD Art. 8(3) requires companies to bring actual adverse impacts to an end" /></div>' +
              '<div class="pt-field"><label>Source URL (provenance)</label><input id="pub-fact-src" placeholder="https://… primary source" /></div>' +
            '</div>' +
            // Page fields (hidden initially)
            '<div id="pub-fields-page" style="display:none">' +
              '<div class="pt-field"><label>Knowledge-page title</label><input placeholder="Living-wage benchmark · methodology" /></div>' +
              '<div class="pt-field"><label>Body</label><input placeholder="The page content (markdown supported)…" /></div>' +
              '<div class="pt-field"><label>Retrieval triggers</label><input value="rag · exact-id · keyword" /></div>' +
            '</div>' +
            // Repo fields (hidden initially)
            '<div id="pub-fields-repo" style="display:none">' +
              '<div class="pt-field"><label>Repository</label><input placeholder="github.com/your-org/your-corpus" /></div>' +
              '<div class="pt-field"><label>What it contains</label><input placeholder="A governed corpus / component set to normalize &amp; gate" /></div>' +
            '</div>' +
            '<div class="pt-field row2">' +
              '<div><label>Author / attribution</label><input value="Nadia Okonkwo · Acme Corp" /></div>' +
              '<div><label>License</label><input value="CC-BY-4.0" /></div>' +
            '</div>' +
          '</div>' +

          '<div class="pt-panel" style="margin-top:14px">' +
            '<div class="oh-cc-id" style="font-family:var(--font-mono);font-size:10px;color:var(--fg-faint);margin-bottom:4px">local agent → ecosystem</div>' +
            '<p style="font-size:12.5px;color:var(--fg-muted);margin:0 0 8px;line-height:1.5">Configure how your Local Agent communicates with the OpenHubForAI agent when publishing. Private data never leaves; only the fact/page/repo you choose, plus its provenance.</p>' +
            '<div class="pt-setting-row">' +
              '<div class="info">' +
                '<div class="t">Let my Local Agent publish</div>' +
                '<div class="d">via MCP · <a style="color:var(--accent);cursor:pointer" data-nav="/connect">manage the bridge →</a></div>' +
              '</div>' +
              '<span class="pt-switch" id="pub-agent-toggle" role="switch" aria-checked="false"><i></i></span>' +
            '</div>' +
            '<div id="pub-agent-extra" style="display:none">' +
              '<div class="pt-setting-row">' +
                '<div class="info">' +
                  '<div class="t">Before it goes public</div>' +
                  '<div class="d">Auto-publish vs hold for your review.</div>' +
                '</div>' +
                '<div class="pt-seg" id="pub-review-seg">' +
                  '<button class="on" data-val="manual">Review first</button>' +
                  '<button data-val="auto">Auto-publish</button>' +
                '</div>' +
              '</div>' +
            '</div>' +
            '<div class="pt-setting-row" style="border-bottom:none">' +
              '<div class="info">' +
                '<div class="t">Privacy guard</div>' +
                '<div class="d">Block accidental sharing of flagged private data.</div>' +
              '</div>' +
              '<span class="oh-badge oh-badge--verified">&#x1F512; enforced</span>' +
            '</div>' +
          '</div>' +
        '</div>' +

        // Right column
        '<div>' +
          '<div class="pt-panel" style="border-color:color-mix(in srgb,var(--warning) 40%,var(--line))">' +
            '<div class="oh-cc-id" style="font-family:var(--font-mono);font-size:10px;color:var(--fg-faint);margin-bottom:10px">&#x26A0; this is permanent</div>' +
            '<ul style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.6;color:var(--fg)">' +
              '<li><b>Immutable</b> &mdash; content-addressed &amp; signed; it can never be edited.</li>' +
              '<li><b>Permanently public</b> &mdash; always discoverable on the ecosystem; it cannot be deleted or unpublished.</li>' +
              '<li><b>Supersede, don\'t delete</b> &mdash; corrections are published as a <i>new</i> version, linked from this one.</li>' +
              '<li><b>Attributed to you</b> &mdash; provenance traces back to your publisher identity, forever.</li>' +
              '<li>It must clear the <b>lift &amp; provenance gate</b> to become promotable; until then it\'s visible as <span style="font-family:var(--font-mono)">&#x25F7; unverified</span>.</li>' +
            '</ul>' +
            '<div class="pt-setting-row" style="cursor:pointer;border-bottom:none;padding-bottom:0;margin-top:8px" id="pub-consent-row">' +
              '<span class="pt-switch" id="pub-consent-toggle" role="switch" aria-checked="false"><i></i></span>' +
              '<span class="info"><span class="t">I understand this is immutable &amp; permanent</span></span>' +
            '</div>' +
            '<button class="oh-btn oh-btn--primary" id="pub-submit-btn" style="width:100%;justify-content:center;margin-top:14px;opacity:.5;pointer-events:none">Publish to the ecosystem →</button>' +
          '</div>' +

          '<div id="pub-published-panel" style="display:none;margin-top:14px">' +
            '<div class="pt-panel">' +
              '<div class="oh-cc-id" style="font-family:var(--font-mono);font-size:10px;color:var(--fg-faint);margin-bottom:8px">published · signed</div>' +
              '<div class="pt-codeblock">cas://oh/9c1b7e4a…d2f0a31f\nsigned 2026-05-28 · CC-BY-4.0\nstatus &#x25F7; unverified → measuring lift…</div>' +
              '<button class="oh-btn oh-btn--ghost oh-btn--sm" style="margin-top:10px" data-nav="/p/pub-9c1b">View provenance graph →</button>' +
            '</div>' +
          '</div>' +

          '<div class="pt-panel" style="margin-top:14px">' +
            '<div class="oh-cc-id" style="font-family:var(--font-mono);font-size:10px;color:var(--fg-faint);margin-bottom:6px">your published objects</div>' +
            publishedList +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  function mountPublish(host, ctx) {
    var state = { mode: 'fact', agentPublish: false, consent: false };

    // Helper to update mode segment UI
    function refreshModeUI() {
      var seg = host.querySelector('#pub-mode-seg');
      if (!seg) return;
      var btns = seg.querySelectorAll('button');
      btns.forEach(function (b) {
        b.classList.toggle('on', b.getAttribute('data-mode') === state.mode);
      });
      ['fact', 'page', 'repo'].forEach(function (m) {
        var el = host.querySelector('#pub-fields-' + m);
        if (el) el.style.display = (m === state.mode) ? '' : 'none';
      });
    }

    // Helper to refresh submit button
    function refreshSubmit() {
      var btn = host.querySelector('#pub-submit-btn');
      if (!btn) return;
      btn.style.opacity = state.consent ? '1' : '.5';
      btn.style.pointerEvents = state.consent ? 'auto' : 'none';
    }

    // Mode segment
    var modeSeg = host.querySelector('#pub-mode-seg');
    if (modeSeg) {
      modeSeg.addEventListener('click', function (e) {
        var btn = e.target.closest('button[data-mode]');
        if (!btn) return;
        state.mode = btn.getAttribute('data-mode');
        refreshModeUI();
      });
    }
    refreshModeUI();

    // Agent publish toggle
    var agentToggle = host.querySelector('#pub-agent-toggle');
    if (agentToggle) {
      agentToggle.addEventListener('click', function () {
        state.agentPublish = !state.agentPublish;
        agentToggle.classList.toggle('on', state.agentPublish);
        agentToggle.setAttribute('aria-checked', String(state.agentPublish));
        var extra = host.querySelector('#pub-agent-extra');
        if (extra) extra.style.display = state.agentPublish ? '' : 'none';
      });
    }

    // Review seg (auto/manual)
    var reviewSeg = host.querySelector('#pub-review-seg');
    if (reviewSeg) {
      reviewSeg.addEventListener('click', function (e) {
        var btn = e.target.closest('button[data-val]');
        if (!btn) return;
        reviewSeg.querySelectorAll('button').forEach(function (b) { b.classList.toggle('on', b === btn); });
      });
    }

    // Consent toggle (row and toggle itself)
    var consentToggle = host.querySelector('#pub-consent-toggle');
    var consentRow = host.querySelector('#pub-consent-row');
    function toggleConsent() {
      state.consent = !state.consent;
      if (consentToggle) {
        consentToggle.classList.toggle('on', state.consent);
        consentToggle.setAttribute('aria-checked', String(state.consent));
      }
      refreshSubmit();
    }
    if (consentToggle) consentToggle.addEventListener('click', function (e) { e.stopPropagation(); toggleConsent(); });
    if (consentRow) consentRow.addEventListener('click', function (e) {
      if (e.target === consentToggle || consentToggle.contains(e.target)) return;
      toggleConsent();
    });

    // Publish submit
    var submitBtn = host.querySelector('#pub-submit-btn');
    if (submitBtn) {
      submitBtn.addEventListener('click', function () {
        if (!state.consent) return;
        var panel = host.querySelector('#pub-published-panel');
        if (panel) panel.style.display = '';
        ctx.toast('Published · immutable & public');
      });
    }
  }

  OpenHubForAI.register("/publish", renderPublish, mountPublish, { theme: "dark" });

})();
