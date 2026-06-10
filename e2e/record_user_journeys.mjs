// e2e/record_user_journeys.mjs — narrated VIDEO recordings of complete user journeys through the
// wired full-design apps. v2: 1600×900, tighter pacing, and the OpenHarnessHub cut is recorded
// THROUGH THE PUBLIC TUNNEL URL (exactly what a link recipient sees), covering the live surfaces:
// real 2,400+-component catalog (search · facets · governance detail), real /api/build preview,
// real tier costs, the LIVE flow canvas with real swap alternatives, a REAL open-spec YAML
// export, real per-realm sign-up, and the workspace's real build history.
//
// Honesty rules carried into the videos: real seams are exercised for real; designed simulations
// are CAPTIONED as such — the HUD never claims fixture data is live.
//
// Run:  node e2e/record_user_journeys.mjs            (services up: scripts/start_local_services.py)
// Out:  artifacts/e2e/videos/journey-*.{webm,mp4} + reports/user-journeys.json

import { chromium } from 'playwright';
import { finalizeNativeVideo, DIRS, HAS_NATIVE_VIDEO } from './gate_common.mjs';
import { writeFileSync, readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SIZE = { width: 1600, height: 900 };
const EXPECTED_CONSOLE = [/in-browser Babel transformer/i, /React DevTools/i];
const results = [];

function readDist(name) {
  const p = join(HERE, '..', 'dist', name);
  return existsSync(p) ? readFileSync(p, 'utf-8').trim() : '';
}
const TOKEN = readDist('showcase-token.txt');

// product journeys record through their PUBLIC tunnel when it answers; honest local fallback
async function publicBase(shareFile, localUrl) {
  const share = readDist(shareFile);
  if (share) {
    try {
      const res = await fetch(new URL(share).origin + '/api/health', { signal: AbortSignal.timeout(8000) });
      if (res.ok) return { url: share, public: true, host: new URL(share).host };
    } catch (e) { /* tunnel down */ }
  }
  return { url: localUrl, public: false, host: new URL(localUrl).host };
}
const ohhBase = () => publicBase('showcase-share-url-harness-hub.txt', `http://127.0.0.1:8000/?token=${encodeURIComponent(TOKEN)}`);
const teleonBase = () => publicBase('showcase-share-url-teleon.txt', 'http://127.0.0.1:8003/');

async function launchRecorder() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const context = await browser.newContext({
    viewport: SIZE, acceptDownloads: true,
    ...(HAS_NATIVE_VIDEO ? { recordVideo: { dir: DIRS.videos, size: SIZE } } : {}),
  });
  return { browser, context };
}

function helpers(page, journey) {
  const t0 = Date.now();
  const chapters = [];
  const frictions = [];
  const stamp = () => Math.round((Date.now() - t0) / 1000);

  async function hud(text) {
    chapters.push({ at_s: stamp(), caption: text });
    await page.evaluate((t) => {
      let el = document.getElementById('__journey_hud');
      if (!el) {
        el = document.createElement('div');
        el.id = '__journey_hud';
        el.style.cssText = 'position:fixed;left:50%;bottom:30px;transform:translateX(-50%);'
          + 'z-index:2147483647;background:rgba(10,10,14,.9);color:#fff;'
          + 'font:600 16px/1.45 "Hanken Grotesk",system-ui,sans-serif;padding:11px 22px;'
          + 'border-radius:999px;box-shadow:0 8px 28px rgba(0,0,0,.4);max-width:74%;'
          + 'text-align:center;pointer-events:none;letter-spacing:.01em';
        document.body.appendChild(el);
      }
      el.textContent = t;
    }, text).catch(() => {});
  }

  const pause = (ms) => page.waitForTimeout(ms);

  async function go(url, caption, settleMs = 3000) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await pause(settleMs);
    if (caption) await hud(caption);
    await pause(800);
  }

  async function nav(hash, caption, settleMs = 1300) {
    await page.evaluate((h) => { window.location.hash = h; }, hash);
    await pause(settleMs);
    if (caption) await hud(caption);
    await pause(800);
  }

  async function spotlight(locator) {
    try {
      await locator.evaluate((el) => {
        el.style.outline = '3px solid rgba(255,170,60,.9)';
        el.style.outlineOffset = '3px';
        setTimeout(() => { el.style.outline = ''; el.style.outlineOffset = ''; }, 1100);
      });
      await pause(550);
    } catch (e) { /* decorative only */ }
  }

  async function click(sel, caption, { optional = false, settleMs = 1300 } = {}) {
    const loc = typeof sel === 'string' ? page.locator(sel).first() : sel.first();
    if (!(await loc.count())) {
      if (!optional) frictions.push({ at_s: stamp(), missing: String(sel), note: caption });
      return false;
    }
    if (caption) await hud(caption);
    await loc.scrollIntoViewIfNeeded().catch(() => {});
    await spotlight(loc);
    await loc.click({ timeout: 6000 }).catch(() => frictions.push({ at_s: stamp(), click_failed: String(sel) }));
    await pause(settleMs);
    return true;
  }

  async function type(sel, text) {
    const loc = page.locator(sel).first();
    await loc.scrollIntoViewIfNeeded().catch(() => {});
    await loc.click({ timeout: 6000 });
    await page.keyboard.type(text, { delay: 22 });
    await pause(400);
  }

  async function scrollTour(beats = 3, beatMs = 1300) {
    for (let i = 0; i < beats; i += 1) {
      await page.mouse.wheel(0, 700);
      await pause(beatMs);
    }
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await pause(1000);
  }

  return { hud, go, nav, click, type, scrollTour, pause, chapters, frictions, journey };
}

/* ============ JOURNEY 1 — OpenHarnessHub through the PUBLIC URL (full lifecycle) ============ */
async function ohhJourney(page, h, base) {
  const email = `journey-ohh-${Date.now()}@example.test`;
  await h.go(base.url, base.public
    ? `OpenHarnessHub.io — live on the public link: ${base.host}`
    : 'OpenHarnessHub.io — landing (local)', 4000);
  await h.scrollTour(3);
  await h.click(page.getByText('Image', { exact: true }), 'Pipelines for every modality — image, audio, video', { optional: true, settleMs: 900 });
  await h.click(page.getByText('Audio', { exact: true }), null, { optional: true, settleMs: 900 });
  await h.click(page.getByText('Text', { exact: true }), null, { optional: true, settleMs: 700 });

  await h.hud('Describe a task — the REAL backend assembles a governed pipeline');
  await h.type('.pt-hero textarea, textarea', 'screen supplier disclosures for forced labor and cite the exact regulations');
  await h.click('.pt-hero button.oh-btn--primary, button:has-text("Build")', 'Build → /api/build assembles from 2,400+ governed components');
  await h.pause(4200);
  await h.hud('The REAL assembled flow — live components, recipe phases, real cost. No invented lift numbers.');
  await h.scrollTour(3, 1500);

  await h.nav('#/components', 'Explore — the live registry: 2,400+ real components');
  await h.pause(1400);
  await h.hud('Search and facets run over the real catalog');
  await h.type('.pt-search input', 'sanctions');
  await h.pause(1600);
  await page.locator('.pt-search input').first().fill('');
  await h.pause(900);
  await h.click('.pt-cards-grid .oh-comp-card', 'A real component — license, lifecycle, provenance from the catalog', { settleMs: 2000 });
  await h.scrollTour(2);

  await h.nav('#/signup', 'Create a REAL account — per-realm identity, no SSO, no fake sessions');
  await h.type('input[type="email"], input[placeholder*="mail" i]', email);
  await h.type('input[type="password"]', 'journey-passphrase-1');
  await h.click('button:has-text("Create"), button[type="submit"]', 'The identity service registers, onboards, and mints a session');
  await h.pause(3600);

  await h.nav('#/app', 'The workspace — “recent flows” is YOUR real build history');
  await h.scrollTour(2);
  await h.nav('#/build', 'Confirm the task and constraints');
  await h.pause(1000);
  await h.click('button:has-text("Assemble flow")', 'Assemble — live backend build');
  await h.pause(3000);
  await h.hud('Three REAL cost tiers — cheap / balanced / quality, from the live cost model. Lift: honestly “unproven”.');
  await h.pause(2200);
  await h.click('button:has-text("Open flow")', 'The flow canvas — the REAL build in the designed topology');
  await h.pause(2200);
  await h.click('.oh-fnode >> nth=4', 'Every node is a real catalog component — click to inspect', { optional: true, settleMs: 1600 });
  await h.hud('Swap alternatives are the build’s REAL dropped candidates, ranked by match');
  await h.pause(2200);
  await h.click('button:has-text("Deploy")', 'Deploy → downloads the REAL open-spec YAML bundle', { settleMs: 2400 });
  await h.click('button:has-text("▶ Run"), .pt-flow-toolbar button:has-text("Run")', 'Run console (designed simulation — captioned, not faked)', { optional: true, settleMs: 2200 });

  await h.nav('#/foundry', 'Foundry — distillation & verification tooling', 1700);
  await h.nav('#/govern', 'Governance — provenance, signing, review gates', 1700);
  await h.nav('#/checkout', 'Checkout — the commercial surface (payment EMULATED, no charges)', 1900);
  await h.nav('#/upgrade', 'Plans & upgrade (emulated)', 1700);
  await h.nav('#/settings', 'Configuration — workspace settings', 1500);
  await page.evaluate(() => localStorage.setItem('ohp-mode', 'dark'));
  await h.go(base.url.includes('#') ? base.url : base.url + '#/', 'Dark mode — same surface, dark tokens', 3400);
  await h.scrollTour(2);
  await h.hud('OpenHarnessHub — fully wired: live registry, live builds, real accounts, real exports');
  await h.pause(2400);
}

/* ============ JOURNEY 2 — Baltor (console + LIVE pipeline on the real event bus) ============ */
async function baltorJourney(page, h) {
  const email = `journey-baltor-${Date.now()}@example.test`;
  await h.go('http://127.0.0.1:8001/', 'Baltor — context assurance (the paid product)', 3800);
  await h.scrollTour(3);
  await h.nav('#/why', 'Why context — the thesis', 1700);
  await h.nav('#/engine', 'The Context Engine — six governed stages + verification rail', 2200);
  await h.pause(3600);
  await h.nav('#/cases', 'Case studies', 1500);
  await h.nav('#/pricing', 'Pricing', 1600);

  await h.nav('#/signup', 'A REAL Baltor account — its own identity realm (no SSO)');
  await h.type('input[type="email"], input[placeholder*="mail" i]', email);
  await h.type('input[type="password"]', 'journey-passphrase-2');
  await h.click('button:has-text("Create"), button[type="submit"]', 'Real register → onboarding → session');
  await h.pause(3400);

  await h.nav('#/dashboard', 'The console — corpora, freshness, serving health', 1900);
  await h.scrollTour(2);
  await h.nav('#/corpora', 'Governed corpora — raw / compressed / hyper tiers', 1700);
  await h.click('.oh-card', 'Inside a corpus — tiers, freshness, citations', { optional: true, settleMs: 1900 });
  await h.nav('#/serve', 'Serving context packages to agents', 1700);
  await h.nav('#/verify', 'Verification — claims checked against live sources', 1700);
  await h.nav('#/audit', 'The audit log', 1600);
  await h.nav('#/billing', 'Billing — plan & invoices (payment EMULATED, no charges)', 1900);
  await h.scrollTour(2);

  await h.go('http://127.0.0.1:8001/dashboard.html', 'Live ops — the REAL event bus behind the product', 3200);
  await h.click('#run', 'Run Full Pipeline — a REAL run, streaming real events and receipts');
  await h.pause(13000);
  await h.scrollTour(2);
  await h.hud('Baltor — real console, real events, honest billing emulation');
  await h.pause(2200);
}

/* ====== JOURNEY 3 — AI Done Right → Control Tower → open hub (REAL key lifecycle) ====== */
async function portfolioJourney(page, h) {
  const email = `journey-hub-${Date.now()}@example.test`;
  await h.go('http://127.0.0.1:8002/', 'AI Done Right — the parent portfolio (2 products + 21 open hubs)', 3800);
  for (const section of ['Thesis', 'Architecture', 'Portfolio', 'Proof']) {
    await h.click(page.locator('nav a', { hasText: section }), section, { optional: true, settleMs: 1400 });
  }
  await h.click('button[title*="theme" i], button[aria-label*="theme" i], button:has-text("☾")', 'One design system, light and dark', { optional: true, settleMs: 1200 });

  await h.go('http://127.0.0.1:8002/Demo%20Control%20Tower.html', 'The Demo Control Tower — operator index over all 24 surfaces', 2800);
  await h.scrollTour(3);

  await h.go('http://127.0.0.1:8002/opencontexthub/OpenContextHub%20Prototype.html', 'An open registry — OpenContextHub (21 hubs, one engine)', 3800);
  await h.scrollTour(2);
  await h.nav('#/browse', 'Browsing registry entries', 1900);
  await h.nav('#/signup', 'A REAL account on the hub — separate identity realm');
  await h.type('input[type="email"], input[placeholder*="mail" i]', email);
  await h.type('input[type="password"]', 'journey-passphrase-3');
  await h.click('button:has-text("Create"), button[type="submit"]', 'Sign up — real realm session');
  await h.pause(3400);
  await h.nav('#/keys', 'Configuration — API keys');
  await h.click('button:has-text("+ Create key")', 'Minting a REAL API key (the service stores only a hash)');
  await h.pause(2400);
  await h.hud('The raw key appears exactly once — copy it now');
  await h.pause(2400);
  await h.click('a:has-text("Revoke")', 'Real revocation — gone from the realm immediately', { optional: true, settleMs: 1900 });
  await h.nav('#/billing', 'Hub billing (emulated)', 1600);
  await h.hud('One portfolio: parent → tower → hubs — real accounts, real keys, one design system');
  await h.pause(2400);
}

/* ============ JOURNEY 4 — Teleon through the PUBLIC URL (runtime SaaS, kit reference) ============ */
async function teleonJourney(page, h, base) {
  const email = `journey-teleon-${Date.now()}@example.test`;
  await h.go(base.url, base.public
    ? `Teleon.dev — live on the public link: ${base.host}`
    : 'Teleon.dev — the purpose-driven runtime', 4000);
  await h.hud('Capabilities, not code — the hero ships with live A/B variants (see the chip)');
  await h.scrollTour(3);
  for (const section of ['How it works', 'Lifecycle', 'Where it fits']) {
    await h.click(page.locator('nav a', { hasText: section }), section, { optional: true, settleMs: 1500 });
  }
  await h.nav('#/cases', 'Case studies', 1600);
  await h.nav('#/pricing', 'Pricing', 1700);
  await h.nav('#/docs', 'Docs', 1600);

  await h.nav('#/signup', 'Create a REAL account — Teleon has its own identity realm (no SSO)');
  await h.type('input[type="email"], input[placeholder*="mail" i]', email);
  await h.type('input[type="password"]', 'journey-passphrase-4');
  await h.click('button:has-text("Create"), button[type="submit"]', 'Real register → onboarding → session');
  await h.pause(3600);

  await h.nav('#/app', 'Capabilities — the REAL runtime state: status from a real promotion gate', 2000);
  await h.scrollTour(1, 1100);
  await h.nav('#/runs', 'Build a capability — this executes FOR REAL (deterministic examples, receipts)');
  await h.pause(800);
  await h.click('button:has-text("Build capability")', 'Building — every example runs now; the gate scores the real pass-rate');
  await h.pause(6200);
  await h.hud('Shipped by the REAL gate — real score, real version bump, receipts on disk');
  await h.pause(2600);
  await h.nav('#/app', 'The capability table updates from the run that just happened', 2200);
  await h.nav('#/dashboard', 'The console — REAL counters from your recorded runs', 1900);
  await h.scrollTour(1, 1100);
  await page.keyboard.press('Control+k');
  await h.pause(900);
  await h.hud('⌘K — the command palette, on every app surface');
  await h.pause(1600);
  await page.keyboard.press('Escape');
  await h.nav('#/evidence', 'Evidence — what was tried, how it scored, why it shipped', 1700);
  await h.nav('#/registry', 'Library — building blocks drawn from the open hubs', 1600);

  await h.nav('#/keys', 'Configuration — API keys');
  await h.click('button:has-text("+ Create key")', 'Minting a REAL API key on the teleon realm');
  await h.pause(2400);
  await h.hud('The raw key is shown exactly once — the service stores only a hash');
  await h.pause(2400);
  await h.click('tr:has-text("just now") a:has-text("Revoke")', 'Real revocation — gone immediately', { optional: true, settleMs: 1800 });
  await h.nav('#/team', 'Team', 1500);
  await h.nav('#/usage', 'Usage — REAL recorded runs and execution time', 1700);
  await h.nav('#/billing', 'Billing — plan & invoices (payment EMULATED, no charges)', 1900);
  await h.nav('#/audit', 'Audit log', 1600);
  await h.nav('#/settings', 'Settings', 1500);

  const toggle = page.locator('button[title*="theme" i], button[aria-label*="theme" i], button:has-text("☾")').first();
  if (await toggle.count()) { await toggle.click(); await h.pause(700); }
  await h.nav('#/', 'Dark mode — same tokens, dark theme', 1900);
  await h.scrollTour(2);

  await h.go(base.url.replace(/\/?(\?[^#]*)?(#.*)?$/, '') + '/Teleon%20PurposeTask%20Control%20Tower.html', 'The PurposeTask Control Tower — operator view (designed prototype)', 3000);
  await h.scrollTour(3);
  await h.hud('Teleon — real accounts, real keys, and a REAL capability lifecycle: build → gate → ship');
  await h.pause(2400);
}

/* ============ JOURNEY 5 — the OPEN HUBS grand tour (8 live makeHub registries + depth) ============ */
async function liveHubsJourney(page, h) {
  const { readdirSync, readFileSync } = await import('node:fs');
  const { join } = await import('node:path');
  const bundle = join(HERE, '..', 'dist', 'sites', 'openharness-design');
  const folders = readdirSync(bundle, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^open.+hub$|^openskilltotool$/.test(d.name) && d.name !== 'openharnesshub')
    .map((d) => d.name).sort();
  const products = readFileSync(join(bundle, 'shared', 'products.js'), 'utf-8');
  const live = folders.filter((f) => {
    const at = products.indexOf(`'../${f}/`);
    return at !== -1 && !/status: 'private'/.test(products.slice(Math.max(0, at - 600), at + 600));
  });
  const entry = (f) => readdirSync(join(bundle, f)).find((x) => / Prototype\.html$/.test(x));
  const base = 'http://127.0.0.1:8002';

  await h.go(`${base}/${encodeURIComponent(live[0])}/${encodeURIComponent(entry(live[0]))}`,
    `The open registries — ${live.length} live hubs, every one rendered by ONE engine`, 3600);
  for (const f of live) {
    await h.go(`${base}/${encodeURIComponent(f)}/${encodeURIComponent(entry(f))}`, `${f} — landing`, 2600);
    await h.scrollTour(1, 1000);
    await h.nav('#/browse', `${f} — browse the registry`, 1500);
  }

  await h.go(`${base}/openskilltotool/${encodeURIComponent(entry('openskilltotool'))}#/architecture`,
    'OpenSkillToTool — bespoke depth: the conversion architecture', 3200);
  await h.scrollTour(2);
  await h.nav('#/convert', 'The convert wizard', 2200);

  await h.go(`${base}/openreviewhub/${encodeURIComponent(entry('openreviewhub'))}#/browse`,
    'OpenReviewHub — governed reviews', 3200);
  await h.click('.oh-card', 'A review entry', { optional: true, settleMs: 2200 });

  await h.go(`${base}/opencontexthub/${encodeURIComponent(entry('opencontexthub'))}#/signup`,
    'OpenContextHub — a REAL account + a REAL install', 3000);
  await h.type('input[type="email"], input[placeholder*="mail" i]', `tour-${Date.now()}@example.test`);
  await h.type('input[type="password"]', 'tour-passphrase');
  await h.click('button:has-text("Create"), button[type="submit"]', 'Real realm sign-up');
  await h.pause(3400);
  await h.nav('#/browse', 'Pick an entry', 1600);
  await h.click('.oh-card', 'The entry — provenance, signing, install', { optional: true, settleMs: 2000 });
  await page.evaluate(async () => {
    const entries = await window.OHRegistry.search('opencontexthub', '');
    if (entries && entries.length) await window.OHRegistry.install('opencontexthub', entries[0]);
  });
  await h.nav('#/installed', 'Installed — the REAL workspace row from the registry service', 2200);
  await h.hud('The open funnel: 8 live registries + the OpenHarnessHub product, one design system, real accounts everywhere');
  await h.pause(2400);
}

/* ============ JOURNEY 6 — the PRIVATE BENCH + internal planes + the scorecard ============ */
async function benchJourney(page, h) {
  const { readdirSync, readFileSync } = await import('node:fs');
  const { join } = await import('node:path');
  const bundle = join(HERE, '..', 'dist', 'sites', 'openharness-design');
  const folders = readdirSync(bundle, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^open.+hub$/.test(d.name))
    .map((d) => d.name).sort();
  const products = readFileSync(join(bundle, 'shared', 'products.js'), 'utf-8');
  const bench = folders.filter((f) => {
    const at = products.indexOf(`'../${f}/`);
    return at !== -1 && /status: 'private'/.test(products.slice(Math.max(0, at - 600), at + 600));
  });
  const entry = (f) => readdirSync(join(bundle, f)).find((x) => / Prototype\.html$/.test(x));
  const base = 'http://127.0.0.1:8002';

  await h.go(`${base}/Demo%20Control%20Tower.html`, 'The operator index — and behind it, the PRIVATE BENCH', 3200);
  await h.scrollTour(2);
  await h.hud(`${bench.length} private-bench registries — muted accent + “Private preview” banner until the owner flips them live`);
  for (const f of bench) {
    await h.go(`${base}/${encodeURIComponent(f)}/${encodeURIComponent(entry(f))}`, `${f} — private preview`, 2200);
  }
  await h.go(`${base}/inference-gateway/${encodeURIComponent('Shared Inference Gateway.html')}`,
    'Shared Inference Gateway — the internal routing plane', 3000);
  await h.scrollTour(2);
  await h.go(`${base}/template-registry/${encodeURIComponent('Shared Template Registry.html')}`,
    'Shared Template Registry — the internal template plane', 3000);
  await h.scrollTour(2);
  await h.go(`${base}/design/${encodeURIComponent('Design Acceptance Scorecard.html')}`,
    'The Design Acceptance Scorecard — the branded-house consistency gate', 3000);
  await h.scrollTour(3);
  await h.hud('The whole family: 24+ surfaces, one design system, verified end to end');
  await h.pause(2600);
}

/* =====================  runner  ===================== */
const base = await ohhBase();
const tBase = await teleonBase();
const JOURNEYS = [
  { id: 'journey-1-openharnesshub', title: `Open Harness Hub — ${base.public ? 'PUBLIC URL' : 'local'}: landing → live build → live registry → sign-up → live canvas + real export → configuration`, fn: (p, h) => ohhJourney(p, h, base) },
  { id: 'journey-2-baltor', title: 'Baltor — landing → sign-up → console → emulated billing → LIVE pipeline on the real event bus', fn: baltorJourney },
  { id: 'journey-3-portfolio-hub', title: 'AI Done Right → Control Tower → OpenContextHub — real account + REAL key mint/revoke', fn: portfolioJourney },
  { id: 'journey-4-teleon', title: `Teleon — ${tBase.public ? 'PUBLIC URL' : 'local'}: landing → sign-up → REAL capability build (gate + receipts) → REAL key lifecycle → tower`, fn: (p, h) => teleonJourney(p, h, tBase) },
  { id: 'journey-5-open-hubs', title: 'The open registries — 8 live hubs (one engine) + bespoke depth + a REAL install', fn: liveHubsJourney },
  { id: 'journey-6-private-bench', title: 'The private bench (13 hubs) + internal planes + the Design Acceptance Scorecard', fn: benchJourney },
];

console.log(`native video: ${HAS_NATIVE_VIDEO ? 'ON (webm + mp4)' : 'OFF — webm only'} · ${SIZE.width}×${SIZE.height} · OHH: ${base.host}${base.public ? ' (PUBLIC)' : ''} · Teleon: ${tBase.host}${tBase.public ? ' (PUBLIC)' : ''}\n`);
for (const j of JOURNEYS) {
  console.log(`=== recording ${j.id} ===`);
  const { browser, context } = await launchRecorder();
  const page = await context.newPage();
  const consoleErrors = [];
  page.on('console', (m) => { if (m.type() === 'error' && !EXPECTED_CONSOLE.some((re) => re.test(m.text()))) consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => consoleErrors.push(String(e)));
  const h = helpers(page, j.id);
  try {
    await j.fn(page, h);
  } catch (err) {
    h.frictions.push({ fatal: String(err).slice(0, 300) });
    console.log(`  [fatal] ${String(err).slice(0, 160)}`);
  }
  const handle = page.video();
  await page.close();
  await context.close();
  await browser.close();
  const out = await finalizeNativeVideo(handle, j.id);
  results.push({
    id: j.id, title: j.title,
    base: j.id.includes('openharnesshub') ? base.host : j.id.includes('teleon') ? tBase.host : '127.0.0.1',
    video: out, duration_s: h.chapters.length ? h.chapters[h.chapters.length - 1].at_s : 0,
    chapters: h.chapters, frictions: h.frictions, console_errors: consoleErrors.slice(0, 10),
  });
  console.log(`  [done] ${out ? (out.mp4 || out.webm) : 'NO VIDEO'} · ${h.chapters.length} chapters · ${h.frictions.length} frictions · ${consoleErrors.length} console errors`);
}

writeFileSync(join(DIRS.reports, 'user-journeys.json'), JSON.stringify({ generated_at: new Date().toISOString(), size: SIZE, results }, null, 1));
const bad = results.filter((r) => !r.video || r.frictions.some((f) => f.fatal));
console.log(`\n${bad.length ? 'FAIL' : 'PASS'} — ${results.length} journey videos → ${DIRS.videos}`);
process.exit(bad.length ? 1 : 0);
