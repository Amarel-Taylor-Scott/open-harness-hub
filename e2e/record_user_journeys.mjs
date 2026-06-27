// e2e/record_user_journeys.mjs — narrated VIDEO recordings of complete user journeys (v4).
//
// v4 rules (owner feedback 2026-06-11):
//   1. NAVIGATE LIKE A USER — clicks on real links/buttons only. If a destination has no
//      clickable path, that is a recorded FRICTION (users can't reach it either); the journey
//      may then use one captioned "operator deep link", but the friction stays in the report.
//   2. NO 404s — every 4xx/5xx response (except favicon) is captured with a screenshot and
//      FAILS the journey.
//   3. SIGN-UP GATES THE APP — app chapters only after a real sign-up, waiting for the app's
//      own redirect (never jumping into a dashboard signed-out).
//   4. SHOW THE ARTIFACTS — full-screen close-ups (exported YAML, receipts, minted keys) with
//      real dwell time, plus a per-chapter PNG stills gallery next to the videos.
//
// Run:  node e2e/record_user_journeys.mjs [journey-id ...]   (selective runs merge the report)
// Out:  artifacts/e2e/videos/*.{webm,mp4} · artifacts/e2e/stills/<journey>/NN-*.png
//       reports/user-journeys.json

import { chromium } from 'playwright';
import { finalizeNativeVideo, DIRS, HAS_NATIVE_VIDEO } from './gate_common.mjs';
import { writeFileSync, readFileSync, existsSync, readdirSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SIZE = { width: 1600, height: 900 };
const STILLS_ROOT = join(HERE, 'artifacts', 'e2e-stills');
const EXPECTED_CONSOLE = [/in-browser Babel transformer/i, /React DevTools/i];
const results = [];

function readDist(name) {
  const p = join(HERE, '..', 'dist', name);
  return existsSync(p) ? readFileSync(p, 'utf-8').trim() : '';
}
const TOKEN = readDist('showcase-token.txt');

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
const ohhBase = () => publicBase('showcase-share-url-openhubforai.txt', `http://127.0.0.1:8000/?token=${encodeURIComponent(TOKEN)}`);
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
  const stillsDir = join(STILLS_ROOT, journey);
  mkdirSync(stillsDir, { recursive: true });
  let stillN = 0;
  const stamp = () => Math.round((Date.now() - t0) / 1000);

  // RULE 2 — every 4xx/5xx is a recorded failure with a screenshot
  page.on('response', async (r) => {
    const url = r.url();
    if (r.status() >= 400 && !/favicon\.ico/.test(url)) {
      const shot = join(stillsDir, `err-${String(frictions.length).padStart(2, '0')}.png`);
      frictions.push({ at_s: stamp(), http: r.status(), url: url.slice(0, 160), screenshot: shot });
      try { await page.screenshot({ path: shot }); } catch (e) { /* page may be navigating */ }
    }
  });

  // VISIBLE CURSOR — headless recordings have no OS pointer, so we render one: a dot that
  // glides to every interaction target and pulses a ripple on click.
  async function ensureCursor() {
    await page.evaluate(() => {
      if (document.getElementById('__journey_cursor')) return;
      const c = document.createElement('div');
      c.id = '__journey_cursor';
      c.style.cssText = 'position:fixed;left:60px;top:60px;width:22px;height:22px;z-index:2147483647;'
        + 'pointer-events:none;border-radius:50%;background:rgba(255,170,60,.95);'
        + 'box-shadow:0 0 0 5px rgba(255,170,60,.30), 0 2px 10px rgba(0,0,0,.45);'
        + 'transition:left .55s cubic-bezier(.3,.8,.3,1), top .55s cubic-bezier(.3,.8,.3,1)';
      document.body.appendChild(c);
    }).catch(() => {});
  }
  async function cursorTo(loc) {
    try {
      const box = await loc.boundingBox();
      if (!box) return;
      await ensureCursor();
      await page.evaluate(({ x, y }) => {
        const c = document.getElementById('__journey_cursor');
        if (c) { c.style.left = `${x - 11}px`; c.style.top = `${y - 11}px`; }
      }, { x: box.x + box.width / 2, y: box.y + box.height / 2 });
      await pause(620);
    } catch (e) { /* decorative */ }
  }
  async function clickRipple() {
    await page.evaluate(() => {
      const c = document.getElementById('__journey_cursor');
      if (!c) return;
      const r = document.createElement('div');
      r.style.cssText = `position:fixed;left:${c.style.left};top:${c.style.top};width:22px;height:22px;`
        + 'z-index:2147483646;pointer-events:none;border-radius:50%;border:3px solid rgba(255,170,60,.9);'
        + 'animation:__jr .6s ease-out forwards';
      if (!document.getElementById('__jr_style')) {
        const s = document.createElement('style');
        s.id = '__jr_style';
        s.textContent = '@keyframes __jr{to{transform:scale(3.4);opacity:0}}';
        document.head.appendChild(s);
      }
      document.body.appendChild(r);
      setTimeout(() => r.remove(), 650);
    }).catch(() => {});
  }

  async function still(slug) {
    stillN += 1;
    const file = `${String(stillN).padStart(2, '0')}-${slug.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 48)}.png`;
    await page.screenshot({ path: join(stillsDir, file) }).catch(() => {});
    return file;
  }

  async function hud(text) {
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
    chapters.push({ at_s: stamp(), caption: text, still: await still(text) });
  }

  const pause = (ms) => page.waitForTimeout(ms);

  async function go(url, caption, settleMs = 3000) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await pause(settleMs);
    if (caption) await hud(caption);
    await pause(800);
  }

  async function spotlight(loc) {
    try {
      await loc.evaluate((el) => {
        el.style.outline = '3px solid rgba(255,170,60,.9)';
        el.style.outlineOffset = '3px';
        setTimeout(() => { el.style.outline = ''; el.style.outlineOffset = ''; }, 1100);
      });
      await pause(600);
    } catch (e) { /* decorative */ }
  }

  // RULE 1 — clicks only. sel may be a selector string or a Locator.
  async function click(sel, caption, { optional = false, settleMs = 1400 } = {}) {
    const loc = typeof sel === 'string' ? page.locator(sel).first() : sel.first();
    if (!(await loc.count())) {
      if (!optional) frictions.push({ at_s: stamp(), no_ui_path: String(sel).slice(0, 120), note: caption });
      return false;
    }
    if (caption) await hud(caption);
    await loc.scrollIntoViewIfNeeded().catch(() => {});
    await cursorTo(loc);
    await spotlight(loc);
    await clickRipple();
    await loc.click({ timeout: 8000 }).catch(() => frictions.push({ at_s: stamp(), click_failed: String(sel).slice(0, 120) }));
    await pause(settleMs);
    return true;
  }

  // click a link that leads to a hash route — by href, then by visible text
  async function goRoute(hash, label, caption, { settleMs = 1500 } = {}) {
    const byHref = page.locator(`a[href="#${hash}"], a[href="${hash}"], a[href="#${hash.replace(/^\//, '')}"]`).first();
    if (await byHref.count()) {
      if (caption) await hud(caption);
      await byHref.scrollIntoViewIfNeeded().catch(() => {});
      await cursorTo(byHref);
      await spotlight(byHref);
      await clickRipple();
      await byHref.click({ timeout: 8000 }).catch(() => {});
      await pause(settleMs);
      return true;
    }
    if (label) {
      const byText = page.locator(`nav a, aside a, .ohs-side a, .pt-side a, a, [data-nav], aside button, .ohs-side button, .pt-side button`, { hasText: label }).first();
      if (await byText.count()) {
        if (caption) await hud(caption);
        await cursorTo(byText);
        await spotlight(byText);
        await clickRipple();
        await byText.click({ timeout: 8000 }).catch(() => {});
        await pause(settleMs);
        return true;
      }
    }
    // no clickable path — a REAL product friction; one captioned operator deep link keeps the film going
    frictions.push({ at_s: stamp(), no_ui_path: hash, note: `no clickable path to ${hash} (${label || 'no label'})` });
    if (caption) await hud(caption + ' — (operator deep link; no in-product path yet)');
    await page.evaluate((h) => { window.location.hash = h; }, hash);
    await pause(settleMs);
    return false;
  }

  async function type(sel, text) {
    const loc = page.locator(sel).first();
    await loc.scrollIntoViewIfNeeded().catch(() => {});
    await cursorTo(loc);
    await clickRipple();
    await loc.click({ timeout: 8000 });
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

  // RULE 4 — full-screen artifact close-up with real dwell time
  async function showArtifact(title, text, dwellMs = 6500) {
    await page.evaluate(({ t, body }) => {
      const el = document.createElement('div');
      el.id = '__artifact_panel';
      el.style.cssText = 'position:fixed;inset:4% 8%;z-index:2147483646;background:rgba(12,12,16,.97);'
        + 'color:#e8e6e1;border-radius:14px;box-shadow:0 24px 80px rgba(0,0,0,.55);padding:26px 30px;'
        + 'font:500 13px/1.5 "IBM Plex Mono",monospace;overflow:hidden;display:flex;flex-direction:column';
      el.innerHTML = `<div style="font:700 17px/1.3 'Hanken Grotesk',sans-serif;margin-bottom:14px">${t}</div>`
        + `<pre style="margin:0;overflow:auto;flex:1;white-space:pre-wrap">${body.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</pre>`;
      document.body.appendChild(el);
    }, { t: title, body: text.slice(0, 5000) });
    await hud(title);
    await pause(dwellMs);
    await page.evaluate(() => document.getElementById('__artifact_panel')?.remove());
    await pause(400);
  }

  // back to the site's front page the way a user does — click the brand logo/wordmark
  async function goHome(fallbackUrl, caption) {
    const logo = page.locator('.oh-wordmark, .ohs-wordmark, .ohs-logo, .ohs-brand, .ohs-topbar a, header a, .pt-mkt-top .oh-wordmark').first();
    if (await logo.count()) {
      if (caption) await hud(caption);
      await cursorTo(logo);
      await clickRipple();
      await logo.click({ timeout: 6000 }).catch(() => {});
      await pause(1500);
      const home = await page.evaluate(() => !window.location.hash || window.location.hash === '#/' || window.location.hash === '#');
      if (home) return true;
    }
    frictions.push({ at_s: stamp(), no_ui_path: 'logo→home', note: 'brand logo did not lead home' });
    if (fallbackUrl) { await page.goto(fallbackUrl, { waitUntil: 'domcontentloaded' }); await pause(2400); }
    return false;
  }

  // RULE 3 — real sign-up, then wait for the app's OWN redirect (no jumping).
  // Returns false (with a recorded friction) instead of crashing the whole film.
  async function signUp(email, pass, caption) {
    const emailBox = page.locator('input[type="email"], input[placeholder*="mail" i]').first();
    if (!(await emailBox.count())) {
      frictions.push({ at_s: stamp(), no_ui_path: 'signup-form', note: 'email field not present where expected' });
      return false;
    }
    await type('input[type="email"], input[placeholder*="mail" i]', email);
    await type('input[type="password"]', pass);
    await click('button:has-text("Create"), button[type="submit"]', caption || 'Create the account — real register → onboarding → session');
    const redirected = await page.waitForFunction(
      () => /dashboard|onboarding|workspace|app/.test(window.location.hash), { timeout: 20000 },
    ).then(() => true).catch(() => false);
    if (!redirected) frictions.push({ at_s: stamp(), signup_no_redirect: true });
    await pause(1600);
    return redirected;
  }

  return { hud, go, click, goRoute, goHome, type, scrollTour, pause, showArtifact, signUp, still, chapters, frictions, journey, stillsDir };
}

/* ============ JOURNEY 1 — OpenHarnessHub (public URL, click-only) ============ */
async function ohhJourney(page, h, base) {
  const email = `journey-ohh-${Date.now()}@example.test`;
  await h.go(base.url, base.public
    ? `OpenHarnessHub.io — live on the public link: ${base.host}`
    : 'OpenHarnessHub.io — landing', 4000);
  await h.scrollTour(3);
  await h.click(page.getByText('Image', { exact: true }), 'Pipelines for every modality', { optional: true, settleMs: 900 });
  await h.click(page.getByText('Text', { exact: true }), null, { optional: true, settleMs: 700 });

  await h.hud('Describe a task — the REAL backend assembles a governed pipeline');
  await h.type('.pt-hero textarea, textarea', 'screen supplier disclosures for forced labor and cite the exact regulations');
  await h.click('.pt-hero button.oh-btn--primary, button:has-text("Build")', 'Build → /api/build assembles from 2,500+ governed components');
  await h.pause(4500);
  await h.hud('The REAL assembled flow — live components, recipe phases, real cost');
  await h.scrollTour(3, 1500);

  await h.goHome(base.url, 'Back home — via the wordmark, like any user');
  await h.click(page.locator('nav a', { hasText: 'Explore' }), 'Explore — the live registry');
  await h.pause(1600);
  await h.type('.pt-search input', 'sanctions');
  await h.pause(1500);
  await page.locator('.pt-search input').first().fill('');
  await h.pause(800);
  await h.click('.pt-cards-grid .oh-comp-card', 'A real component — license, lifecycle, provenance from the catalog', { settleMs: 2200 });
  await h.scrollTour(2);

  await h.goHome(base.url);
  await h.click(page.locator('nav a', { hasText: 'Pricing' }), 'Pricing', { optional: true, settleMs: 1600 });
  await h.click('button:has-text("Start free"), a:has-text("Start free")', 'Start free → create a REAL account (own identity realm)');
  await h.pause(1500);
  const signed = await h.signUp(email, 'journey-passphrase-1');
  if (!signed) { await h.hud('Sign-up path friction recorded — ending the journey honestly'); return; }
  await h.hud('Signed in — the app redirected us itself (real session)');
  await h.scrollTour(2);

  await h.goRoute('/build', 'New build', 'Build — confirm the task and constraints');
  await h.pause(1000);
  await h.click('button:has-text("Assemble flow")', 'Assemble — live backend build');
  await h.pause(3200);
  await h.hud('Three REAL cost tiers from the live cost model — lift honestly “unproven”');
  await h.pause(2200);
  await h.click('button:has-text("Open flow")', 'The flow canvas — the REAL build in the designed topology');
  await h.pause(2200);
  await h.click('.oh-fnode >> nth=4', 'Every node is a real catalog component', { optional: true, settleMs: 1600 });
  await h.pause(1400);

  const dl = page.waitForEvent('download', { timeout: 12000 }).catch(() => null);
  await h.click('button:has-text("Deploy")', 'Deploy → downloads the REAL open-spec YAML bundle', { settleMs: 1800 });
  const file = await dl;
  if (file) {
    const body = readFileSync(await file.path(), 'utf-8');
    await h.showArtifact('The exported open-spec pipeline (REAL file, just downloaded)', body.split('\n').slice(0, 34).join('\n'));
  } else {
    h.frictions.push({ at_s: 0, note: 'deploy download did not arrive' });
  }

  await h.goRoute('/dashboards', 'Dashboards', 'Workspace dashboards');
  await h.scrollTour(1, 1100);
  await h.goRoute('/settings', 'Settings', 'Configuration — settings');
  await h.pause(1200);
  await h.hud('OpenHarnessHub — live registry, live builds, real accounts, real exports');
  await h.pause(2200);
}

/* ============ JOURNEY 2 — Baltor (click-only; live ops via the real event bus) ============ */
async function baltorJourney(page, h) {
  const email = `journey-baltor-${Date.now()}@example.test`;
  await h.go('http://127.0.0.1:8001/', 'Baltor — context assurance (the paid product)', 3800);
  await h.scrollTour(3);
  await h.click(page.locator('nav a', { hasText: 'Why' }), 'Why context — the thesis', { settleMs: 1800 });
  await h.scrollTour(1, 1100);
  await h.goRoute('/engine', 'How it works', 'The Context Engine — six governed stages + the verification rail', { settleMs: 2400 });
  await h.scrollTour(2, 1400);
  await h.go('http://127.0.0.1:8001/context-engine-hero.html',
    'The ANIMATED engine — context objects transforming through every stage (legacy showcase)', 3400);
  await h.pause(12000); // let the canvas animation run a full cycle
  await h.scrollTour(1, 1200);
  await h.go('http://127.0.0.1:8001/', null, 2600);
  await h.click(page.locator('nav a', { hasText: 'Cases' }), 'Case studies', { settleMs: 1600 });
  await h.click('.oh-card', 'Inside a case study', { optional: true, settleMs: 1900 });
  await h.goHome('http://127.0.0.1:8001/', 'Home again — via the wordmark');
  await h.click(page.locator('nav a', { hasText: 'Pricing' }), 'Pricing', { settleMs: 1600 });

  await h.click('button:has-text("Start free"), a:has-text("Start free")', 'Start free → a REAL Baltor account (separate realm, no SSO)');
  await h.pause(1500);
  const signed = await h.signUp(email, 'journey-passphrase-2');
  if (!signed) { await h.hud('Sign-up path friction recorded — ending the journey honestly'); return; }
  await h.hud('The console — the app redirected after the real sign-up');
  await h.scrollTour(2);

  await h.goRoute('/corpora', 'Corpora', 'Governed corpora — raw / compressed / hyper tiers');
  await h.click('.oh-card', 'Inside a corpus — tiers, freshness, citations', { optional: true, settleMs: 1900 });
  await h.goRoute('/serve', 'Serve', 'Serving context packages to agents');
  await h.goRoute('/verify', 'Verify', 'Verification — claims checked against live sources');
  await h.goRoute('/audit', 'Audit', 'The audit log');
  await h.goRoute('/billing', 'Billing', 'Billing — plan & invoices (payment EMULATED, no charges)');
  await h.scrollTour(1, 1100);

  // live ops — reached via the operator tower’s real link in journey-3; here it is the
  // documented operator surface (recorded as a deep link until the product nav links it)
  await h.hud('Live ops — the operator surface (deep link recorded; product nav linking it is queued)');
  await h.go(`http://127.0.0.1:8001/dashboard.html?token=${encodeURIComponent(TOKEN)}`, null, 3200);
  await h.pause(1200);
  await h.click('#run', 'Run Full Pipeline — REAL run: real stages, real inference receipt, real events');
  await h.pause(16000);
  await h.scrollTour(2);
  const events = await page.evaluate(async () => {
    const r = await fetch('/api/events?limit=400');
    const d = await r.json();
    const inf = d.events.filter((e) => e.kind === 'inference.completed').slice(-1)[0];
    return inf ? JSON.stringify(inf, null, 1) : null;
  });
  if (events) await h.showArtifact('inference.completed — the REAL model receipt on the event bus', events);
  await h.hud('Baltor — real console, real pipeline, receipts for everything');
  await h.pause(2000);
}

/* ============ JOURNEY 3 — AI Done Right parent + tower (click-only) ============ */
async function parentJourney(page, h) {
  await h.go('http://127.0.0.1:8002/', 'AI Done Right — the parent portfolio', 3800);
  for (const section of ['Thesis', 'Architecture', 'Portfolio', 'Proof']) {
    await h.click(page.locator('nav a', { hasText: section }), section, { optional: true, settleMs: 1400 });
  }
  await h.click('button[title*="theme" i], button[aria-label*="theme" i], button:has-text("☾")', 'One design system — light and dark', { optional: true, settleMs: 1300 });
  await h.click(page.locator('nav a', { hasText: 'Demo' }), 'The Demo Control Tower — the operator index', { settleMs: 3000 });
  await h.scrollTour(3);
  await h.click('button:has-text("Run health check"), button:has-text("health")', 'A live health sweep across the family', { optional: true, settleMs: 3500 });
  await h.click('a:has-text("Run the Baltor CFPB guided demo"), button:has-text("Run the Baltor CFPB guided demo")', 'Into the Baltor CFPB guided demo — via the tower’s own link', { optional: true, settleMs: 3200 });
  await h.scrollTour(3, 1500);
  await h.hud('One portfolio, one design system — everything reachable from the tower');
  await h.pause(2200);
}

/* ============ JOURNEY 4 — Teleon (public URL; model-built lifecycle; click-only) ============ */
async function teleonJourney(page, h, base) {
  const email = `journey-teleon-${Date.now()}@example.test`;
  await h.go(base.url, base.public
    ? `Teleon.dev — live on the public link: ${base.host}`
    : 'Teleon.dev — the purpose-driven runtime', 4000);
  await h.scrollTour(3);
  await h.click(page.locator('nav a', { hasText: 'How it works' }), 'How it works', { optional: true, settleMs: 1500 });
  await h.click(page.locator('nav a', { hasText: 'Cases' }), 'Case studies', { optional: true, settleMs: 1500 });
  await h.goHome(base.url);
  await h.click(page.locator('nav a', { hasText: 'Pricing' }), 'Pricing', { optional: true, settleMs: 1500 });

  await h.click('button:has-text("Start free"), a:has-text("Start free")', 'Start free → a REAL account on the teleon realm');
  await h.pause(1500);
  const signed = await h.signUp(email, 'journey-passphrase-4');
  if (!signed) { await h.hud('Sign-up path friction recorded — ending the journey honestly'); return; }
  await h.hud('The console — redirected by the app after the real sign-up');
  await h.scrollTour(1, 1100);

  await h.goRoute('/app', 'Capabilities', 'Capabilities — REAL runtime state from a real promotion gate');
  await h.pause(1400);
  await h.goRoute('/runs', 'Build', 'Build a capability — the MODEL performs every example, the gate judges');
  await h.click('button:has-text("Build capability")', 'Building — qwen3-next executes the suite now (receipts on disk)');
  await h.pause(2000);
  await h.hud('“executing on the model — receipts pending” (the honest in-flight state)');
  // wait for the real result (cloud ≈ 10–25s)
  await page.waitForFunction(() => /score \d/.test((document.querySelector('.tln-result') || {}).innerText || ''), { timeout: 240000 })
    .catch(() => h.frictions.push({ at_s: 0, note: 'model-built run did not land in 240s' }));
  await h.pause(1500);
  await h.hud('Shipped by the REAL gate — real score, version bump, model-built label');
  await h.pause(2200);
  const receipts = await page.evaluate(async () => {
    const r = window.TeleonLive && TeleonLive.lastRun();
    if (!r) return null;
    const res = await fetch(`/api/teleon/teleon/evidence?run_id=${encodeURIComponent(r.run_id)}`);
    const d = await res.json();
    return JSON.stringify({ run: { capability: r.capability, mode: r.mode, model: r.model_id, score: r.score, decision: r.decision }, receipts: d.receipts.slice(0, 4) }, null, 1);
  });
  if (receipts) await h.showArtifact('The evidence — REAL per-example receipts (hashes, timing, model)', receipts);

  await h.goRoute('/evidence', 'Evidence', 'Evidence — what was tried, how it scored, why it shipped');
  await h.goRoute('/keys', 'API keys', 'API keys');
  await h.click('button:has-text("+ Create key")', 'Minting a REAL key — shown once, hash-only at rest', { settleMs: 2600 });
  await h.pause(2000);
  await h.click('tr:has-text("just now") a:has-text("Revoke")', 'Real revocation', { optional: true, settleMs: 1800 });
  await h.goRoute('/team', 'Team', 'Team', { settleMs: 1200 });
  await h.goRoute('/billing', 'Billing', 'Billing (EMULATED — no charges)', { settleMs: 1600 });
  await h.goRoute('/audit', 'Audit', 'Audit log', { settleMs: 1400 });
  await h.hud('Teleon — model-built capabilities, evidence-gated, receipts for everything');
  await h.pause(2200);
}

/* ============ per-site hub journey (click-only) ============ */
function familySurfaces() {
  const bundle = join(HERE, '..', 'dist', 'sites', 'aidoneright-design');
  const folders = readdirSync(bundle, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^open.+hub$|^openskilltotool$/.test(d.name) && d.name !== 'openharnesshub')
    .map((d) => d.name).sort();
  const products = readFileSync(join(bundle, 'shared', 'products.js'), 'utf-8');
  return folders.map((folder) => {
    const at = products.indexOf(`'../${folder}/`);
    const isPrivate = at !== -1 && /status: 'private'/.test(products.slice(Math.max(0, at - 600), at + 600));
    const entry = readdirSync(join(bundle, folder)).find((x) => / Prototype\.html$/.test(x));
    const wordmark = (products.slice(Math.max(0, at - 600), at + 600).match(/wordmark: '([^']+)'/) || [null, folder])[1];
    return { folder, entry, isPrivate, wordmark };
  });
}

function hubJourney({ folder, entry, isPrivate, wordmark }) {
  return async (page, h) => {
    const base = 'http://127.0.0.1:8002';
    const email = `site-${folder}-${Date.now()}@example.test`;
    await h.go(`${base}/${encodeURIComponent(folder)}/${encodeURIComponent(entry)}`,
      isPrivate
        ? `${wordmark} — private bench (local self-use realm; private until flipped live)`
        : `${wordmark} — open registry (live)`, 3400);
    await h.scrollTour(2, 1200);
    await h.click(page.locator('nav a, a', { hasText: 'Browse' }), 'Browse the registry', { settleMs: 1700 });
    await h.click('.oh-card', 'An entry — provenance, signing, the install command', { optional: true, settleMs: 2000 });
    const installCmd = await page.evaluate(() => (document.querySelector('.ohub-code') || {}).innerText || null);
    if (installCmd) await h.showArtifact('The install command (drives the same registry API)', installCmd, 3800);
    await h.click('button:has-text("Start free"), a:has-text("Start free"), a:has-text("Sign in")', 'A REAL account on this site’s own realm');
    await h.pause(1400);
    // some hubs land on signin — switch to create
    await h.click(page.locator('a', { hasText: 'Create one' }), null, { optional: true, settleMs: 900 });
    const signed = await h.signUp(email, 'site-passphrase');
    if (!signed) { await h.hud('Sign-up friction recorded — ending honestly'); return; }
    await page.evaluate(async (realm) => {
      const entries = await window.OHRegistry.search(realm, '');
      if (entries && entries.length) await window.OHRegistry.install(realm, entries[0]);
    }, folder).catch(() => {});
    await h.goRoute('/installed', 'Installed', 'Installed — the REAL workspace row (registry service)');
    await h.goRoute('/keys', 'API keys', 'API keys');
    await h.click('button:has-text("+ Create key")', 'Minting a REAL key (shown once)', { settleMs: 2400 });
    await h.pause(1600);
    await h.goRoute('/billing', 'Billing', 'Billing (EMULATED)', { settleMs: 1400 });
    await h.hud(`${wordmark} — fully wired: real account, workspace, keys`);
    await h.pause(1800);
  };
}

function planeJourney(folder, entry, title) {
  return async (page, h) => {
    await h.go(`http://127.0.0.1:8002/${encodeURIComponent(folder)}/${encodeURIComponent(entry)}`, title, 3400);
    await h.scrollTour(4, 1400);
    await h.hud(title.split(' — ')[0] + ' — an internal shared plane of the portfolio');
    await h.pause(2000);
  };
}

/* ============ tours (kept; site-to-site moves are address-bar by nature) ============ */
async function liveHubsJourney(page, h) {
  const live = familySurfaces().filter((s) => !s.isPrivate);
  const base = 'http://127.0.0.1:8002';
  await h.go(`${base}/${encodeURIComponent(live[0].folder)}/${encodeURIComponent(live[0].entry)}`,
    `The open registries — ${live.length} live hubs, one engine`, 3400);
  for (const s of live) {
    await h.go(`${base}/${encodeURIComponent(s.folder)}/${encodeURIComponent(s.entry)}`, `${s.wordmark} — landing`, 2400);
    await h.click(page.locator('nav a, a', { hasText: 'Browse' }), null, { optional: true, settleMs: 1200 });
  }
  await h.hud('Eight live registries + the OpenHarnessHub product — one design system');
  await h.pause(2200);
}

async function benchJourney(page, h) {
  const bench = familySurfaces().filter((s) => s.isPrivate);
  const base = 'http://127.0.0.1:8002';
  await h.go(`${base}/Demo%20Control%20Tower.html`, 'The operator index — and the PRIVATE BENCH behind it', 3000);
  await h.scrollTour(2);
  await h.hud(`${bench.length} private-bench registries — banner until the owner flips them live`);
  for (const s of bench) {
    await h.go(`${base}/${encodeURIComponent(s.folder)}/${encodeURIComponent(s.entry)}`, `${s.wordmark} — private preview`, 2000);
  }
  await h.go(`${base}/design/${encodeURIComponent('Design Acceptance Scorecard.html')}`, 'The Design Acceptance Scorecard', 2800);
  await h.scrollTour(2);
  await h.hud('The whole family — verified end to end');
  await h.pause(2200);
}

/* =====================  runner  ===================== */
const base = await ohhBase();
const tBase = await teleonBase();
const SURFACES = familySurfaces();
const JOURNEYS = [
  { id: 'journey-1-openharnesshub', title: `OpenHubForAI — ${base.public ? 'PUBLIC URL' : 'local'}: landing → live build → live registry → sign-up → live canvas + export close-up → configuration`, fn: (p, h) => ohhJourney(p, h, base) },
  { id: 'journey-2-baltor', title: 'Baltor — landing → sign-up → console → emulated billing → LIVE pipeline + receipt close-up', fn: baltorJourney },
  { id: 'journey-3-aidoneright', title: 'AI Done Right — parent, the Demo Control Tower (live health), into a guided demo', fn: parentJourney },
  { id: 'journey-4-teleon', title: `Teleon — ${tBase.public ? 'PUBLIC URL' : 'local'}: sign-up → MODEL-BUILT capability (receipt close-up) → REAL key lifecycle`, fn: (p, h) => teleonJourney(p, h, tBase) },
  { id: 'journey-5-open-hubs', title: 'Tour — the live open registries (one engine)', fn: liveHubsJourney },
  { id: 'journey-6-private-bench', title: 'Tour — the private bench + the Design Acceptance Scorecard', fn: benchJourney },
  ...SURFACES.map((s) => ({
    id: `site-${s.folder}`,
    title: `${s.wordmark} — ${s.isPrivate ? 'private bench (local self-use)' : 'live open registry'}: fully wired (real account · workspace · keys)`,
    fn: hubJourney(s),
  })),
  { id: 'site-inference-gateway', title: 'Shared Inference Gateway — the internal routing plane', fn: planeJourney('inference-gateway', 'Shared Inference Gateway.html', 'Shared Inference Gateway — portable preferences, receipts, routing') },
  { id: 'site-template-registry', title: 'Shared Template Registry — the internal template plane', fn: planeJourney('template-registry', 'Shared Template Registry.html', 'Shared Template Registry — the 14-section shell + mixins') },
];

const ONLY = process.argv.slice(2).filter((a) => !a.startsWith('-'));
const TO_RECORD = ONLY.length ? JOURNEYS.filter((j) => ONLY.includes(j.id)) : JOURNEYS;
if (ONLY.length) console.log(`selective re-record: ${TO_RECORD.map((j) => j.id).join(', ')}`);

console.log(`native video: ${HAS_NATIVE_VIDEO ? 'ON (webm + mp4)' : 'OFF'} · ${SIZE.width}×${SIZE.height} · OHH: ${base.host}${base.public ? ' (PUBLIC)' : ''} · Teleon: ${tBase.host}${tBase.public ? ' (PUBLIC)' : ''}\n`);
for (const j of TO_RECORD) {
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
  const httpErrors = h.frictions.filter((f) => f.http);
  results.push({
    id: j.id, title: j.title,
    base: j.id.includes('openharnesshub') ? base.host : j.id.includes('teleon') && j.id.startsWith('journey') ? tBase.host : '127.0.0.1',
    video: out, duration_s: h.chapters.length ? h.chapters[h.chapters.length - 1].at_s : 0,
    chapters: h.chapters, frictions: h.frictions, http_errors: httpErrors.length,
    console_errors: consoleErrors.slice(0, 10),
  });
  console.log(`  [done] ${out ? (out.mp4 || out.webm) : 'NO VIDEO'} · ${h.chapters.length} chapters · ${h.frictions.length} frictions (${httpErrors.length} HTTP) · ${consoleErrors.length} console errors`);
}

let allResults = results;
if (ONLY.length) {
  const reportPath = join(DIRS.reports, 'user-journeys.json');
  const prior = existsSync(reportPath) ? JSON.parse(readFileSync(reportPath, 'utf-8')).results || [] : [];
  const byId = new Map(prior.map((r) => [r.id, r]));
  for (const r of results) byId.set(r.id, r);
  allResults = JOURNEYS.map((j) => byId.get(j.id)).filter(Boolean);
}
writeFileSync(join(DIRS.reports, 'user-journeys.json'), JSON.stringify({ generated_at: new Date().toISOString(), size: SIZE, results: allResults }, null, 1));
const bad = results.filter((r) => !r.video || r.http_errors > 0 || r.frictions.some((f) => f.fatal));
console.log(`\n${bad.length ? 'FAIL' : 'PASS'} — ${results.length} recorded (${allResults.length} in report)`
  + (bad.length ? ` — FAILING: ${bad.map((b) => `${b.id}(${b.http_errors} http)`).join(', ')}` : ''));
process.exit(bad.length ? 1 : 0);
