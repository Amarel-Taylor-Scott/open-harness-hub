// e2e/record_user_journeys.mjs — narrated VIDEO recordings of complete user journeys through the
// three wired full-design apps (web/ transplant): landing → browsing → REAL sign-up → emulated
// payment → product use (REAL /api/build · live event bus · REAL API-key mint) → configuration.
//
// Honesty rules carried into the videos: real seams are exercised for real (identity, build,
// events, key mint); surfaces that are designed simulations are CAPTIONED as such — the HUD
// never claims fixture data is live.
//
// Run:  node e2e/record_user_journeys.mjs            (services up: scripts/start_local_services.py)
// Out:  artifacts/e2e/videos/journey-*.{webm,mp4} + reports/user-journeys.json
//       (mp4 via the repo's static ffmpeg — gate_common.finalizeNativeVideo)

import { launchGate, finalizeNativeVideo, DIRS, HAS_NATIVE_VIDEO } from './gate_common.mjs';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

const EXPECTED_CONSOLE = [/in-browser Babel transformer/i, /React DevTools/i];
const results = [];

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
        el.style.cssText = 'position:fixed;left:50%;bottom:26px;transform:translateX(-50%);'
          + 'z-index:2147483647;background:rgba(10,10,14,.88);color:#fff;'
          + 'font:600 15px/1.45 "Hanken Grotesk",system-ui,sans-serif;padding:10px 20px;'
          + 'border-radius:999px;box-shadow:0 8px 28px rgba(0,0,0,.4);max-width:78%;'
          + 'text-align:center;pointer-events:none;letter-spacing:.01em';
        document.body.appendChild(el);
      }
      el.textContent = t;
    }, text).catch(() => {});
  }

  const pause = (ms) => page.waitForTimeout(ms);

  // full page load (Babel recompiles) — settle generously, then restore the HUD
  async function go(url, caption, settleMs = 3200) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await pause(settleMs);
    if (caption) await hud(caption);
    await pause(900);
  }

  // SPA route hop (no reload, HUD survives)
  async function nav(hash, caption, settleMs = 1500) {
    await page.evaluate((h) => { window.location.hash = h; }, hash);
    await pause(settleMs);
    if (caption) await hud(caption);
    await pause(900);
  }

  async function spotlight(locator) {
    try {
      await locator.evaluate((el) => {
        el.style.outline = '3px solid rgba(255,170,60,.9)';
        el.style.outlineOffset = '3px';
        setTimeout(() => { el.style.outline = ''; el.style.outlineOffset = ''; }, 1200);
      });
      await pause(650);
    } catch (e) { /* decorative only */ }
  }

  async function click(sel, caption, { optional = false, settleMs = 1500 } = {}) {
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
    await page.keyboard.type(text, { delay: 26 });
    await pause(500);
  }

  // unhurried top-to-bottom read of the current page, then back up
  async function scrollTour(beats = 4, beatMs = 1500) {
    for (let i = 0; i < beats; i += 1) {
      await page.mouse.wheel(0, 640);
      await pause(beatMs);
    }
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await pause(1200);
  }

  return { hud, go, nav, click, type, scrollTour, pause, chapters, frictions, journey };
}

/* =====================  JOURNEY 1 — Open Harness Hub (full lifecycle)  ===================== */
async function ohhJourney(page, h) {
  const email = `journey-ohh-${Date.now()}@example.test`;
  await h.go('http://127.0.0.1:8000/', 'Open Harness Hub — landing on the homepage', 4200);
  await h.scrollTour(3);
  await h.click(page.getByText('Image', { exact: true }), 'Browsing the modality examples — image, audio, video pipelines', { optional: true });
  await h.click(page.getByText('Audio', { exact: true }), null, { optional: true });
  await h.click(page.getByText('Text', { exact: true }), null, { optional: true });

  await h.hud('Describing a task — the backend assembles a governed pipeline for it');
  await h.type('.pt-hero textarea, textarea', 'screen supplier disclosures for forced labor and cite the exact regulations');
  await h.click('.pt-hero button.oh-btn--primary, button:has-text("Build")', 'Build → the REAL /api/build endpoint assembles the flow');
  await h.pause(4500); // 4-step assembly animation while the real build lands
  await h.hud('The preview shows the REAL assembled flow — live components, stages, and cost (no made-up lift numbers)');
  await h.scrollTour(4, 1700);

  await h.nav('#/pipelines', 'Browsing the catalog — components, knowledge corpora, governed pipelines');
  await h.scrollTour(2);
  await h.click('.pt-cards-grid .oh-cc, .pt-cards-grid > *', 'Opening a component — lift, provenance, license, lifecycle', { optional: true, settleMs: 2200 });
  await h.scrollTour(2);
  await h.nav('#/compare', 'Comparing pipelines side by side');
  await h.scrollTour(2);
  await h.nav('#/sdg', 'SDG solution tracks', 1800);
  await h.nav('#/cases', 'Case studies');
  await h.nav('#/pricing', 'Pricing — the spec and exports are free; sign up to run flows', 1800);
  await h.scrollTour(2);

  await h.nav('#/signup', 'Creating a REAL account — the per-realm identity service (no SSO, no fake sessions)');
  await h.type('input[type="email"], input[placeholder*="mail" i]', email);
  await h.type('input[type="password"]', 'journey-passphrase-1');
  await h.click('button:has-text("Create"), button[type="submit"]', 'Sign up — the identity service registers, onboards, and mints a session');
  await h.pause(3800);

  await h.nav('#/dashboards', 'Signed in — the workspace, now in app mode (real session detected)');
  await h.scrollTour(2);
  await h.nav('#/build', 'Product use — confirming the parsed task and constraints');
  await h.pause(1200);
  await h.click('button:has-text("Assemble flow")', 'Assemble — the live backend builds while the console animates');
  await h.pause(3200);
  await h.hud('Three costed tier options (designed sample tiers)');
  await h.pause(1800);
  await h.click('button:has-text("Open flow")', 'The interactive flow canvas — nodes, gates, and the model boundary');
  await h.pause(2000);
  await h.click('.pt-flow-toolbar button:has-text("Run"), button:has-text("▶ Run")', 'Run console (designed simulation of a run)', { optional: true, settleMs: 2600 });
  await h.scrollTour(2);

  await h.nav('#/foundry', 'Foundry console — distillation & verification tooling', 2000);
  await h.nav('#/govern', 'Governance — provenance, signing, review gates', 2000);
  await h.nav('#/settings', 'Configuration — workspace settings');
  await h.scrollTour(2);
  await page.evaluate(() => localStorage.setItem('ohp-mode', 'dark'));
  await h.go('http://127.0.0.1:8000/#/', 'Dark mode — the same surface on dark tokens', 3600);
  await h.scrollTour(2);
  await h.hud('Open Harness Hub journey complete — landing → browse → real sign-up → live build → configuration');
  await h.pause(2200);
}

/* =====================  JOURNEY 2 — Baltor (full lifecycle + live ops)  ===================== */
async function baltorJourney(page, h) {
  const email = `journey-baltor-${Date.now()}@example.test`;
  await h.go('http://127.0.0.1:8001/', 'Baltor — landing on the homepage (context assurance)', 4200);
  await h.scrollTour(4);
  await h.nav('#/why', 'Why context — the thesis', 2000);
  await h.scrollTour(2);
  await h.nav('#/engine', 'The Context Engine — six governed stages with a verification rail', 2400);
  await h.pause(4000); // the animated engine
  await h.scrollTour(2);
  await h.nav('#/cases', 'Case studies');
  await h.click('.oh-card a, .ohs-case-card, .oh-card', 'Opening a case study', { optional: true, settleMs: 2200 });
  await h.nav('#/docs', 'Docs — integration surface', 1800);
  await h.nav('#/pricing', 'Pricing — plans before sign-up', 1800);
  await h.scrollTour(2);

  await h.nav('#/signup', 'Creating a REAL Baltor account (its own identity realm — separate from OHH, no SSO)');
  await h.type('input[type="email"], input[placeholder*="mail" i]', email);
  await h.type('input[type="password"]', 'journey-passphrase-2');
  await h.click('button:has-text("Create"), button[type="submit"]', 'Sign up — real register → onboarding → session');
  await h.pause(3800);

  await h.nav('#/dashboard', 'The console — corpora, freshness, serving health', 2200);
  await h.scrollTour(2);
  await h.nav('#/sources', 'Sources — what feeds the corpus', 2000);
  await h.nav('#/ingest', 'Connecting a source', 2000);
  await h.nav('#/corpora', 'Governed corpora — raw, compressed, hyper-efficient tiers', 2000);
  await h.click('.oh-card', 'Opening a corpus — tiers, freshness, citations', { optional: true, settleMs: 2400 });
  await h.scrollTour(2);
  await h.nav('#/serve', 'Serving context packages to agents', 2000);
  await h.nav('#/verify', 'Verification — every claim checked against live sources', 2000);
  await h.nav('#/governance', 'Governance — provenance and policy', 2000);
  await h.nav('#/audit', 'The audit log — every serve and reconciliation', 2000);

  await h.nav('#/billing', 'Billing — plan, invoices, payment (EMULATED — no real charges)', 2200);
  await h.scrollTour(2);
  await h.click('button:has-text("Manage plan")', 'Managing the plan (emulated checkout)', { optional: true });
  await h.nav('#/settings', 'Configuration — workspace settings', 1800);
  await h.nav('#/usage', 'Usage metering', 1800);

  await h.go('http://127.0.0.1:8001/Baltor%20CFPB%20Guided%20Demo.html', 'A guided demo — CFPB regulatory context, end to end', 3600);
  await h.scrollTour(4, 1700);

  await h.go('http://127.0.0.1:8001/dashboard.html', 'Live ops — the REAL event bus behind the product', 3600);
  await h.click('#run', 'Run Full Pipeline — a REAL pipeline run, streaming real events');
  await h.pause(14000); // real events stream in
  await h.scrollTour(2);
  await h.hud('Baltor journey complete — landing → browse → real sign-up → emulated billing → console → live pipeline');
  await h.pause(2200);
}

/* ============  JOURNEY 3 — AI Done Right portfolio + hub (config: REAL key mint)  ============ */
async function portfolioJourney(page, h) {
  const email = `journey-hub-${Date.now()}@example.test`;
  await h.go('http://127.0.0.1:8002/', 'AI Done Right — the parent portfolio', 4200);
  for (const section of ['Thesis', 'Architecture', 'Portfolio', 'Proof', 'How it fits']) {
    await h.click(page.locator('nav a', { hasText: section }), `${section}`, { optional: true, settleMs: 1700 });
  }
  await h.click('button[title*="theme" i], button[aria-label*="theme" i], button:has-text("☾")', 'Dark mode across the family', { optional: true, settleMs: 1400 });
  await h.click('button[title*="theme" i], button[aria-label*="theme" i], button:has-text("☀")', null, { optional: true, settleMs: 900 });

  await h.go('http://127.0.0.1:8002/Demo%20Control%20Tower.html', 'The Demo Control Tower — operator index over all 24 surfaces', 3200);
  await h.scrollTour(3);
  await h.click('button:has-text("Run health check"), .dct-health, button:has-text("health")', 'Running the live health sweep', { optional: true, settleMs: 3500 });

  await h.go('http://127.0.0.1:8002/opencontexthub/OpenContextHub%20Prototype.html', 'Into an open registry — OpenContextHub (one of 21 hubs from a single engine)', 4200);
  await h.scrollTour(3);
  await h.nav('#/browse', 'Browsing registry entries', 2200);
  await h.click('.ohub-grid .oh-card, .oh-card', 'An entry — provenance, signing, install command', { optional: true, settleMs: 2200 });
  await h.nav('#/pricing', 'Hub pricing', 1800);

  await h.nav('#/signup', 'A REAL account on the hub — its own separate identity realm');
  await h.type('input[type="email"], input[placeholder*="mail" i]', email);
  await h.type('input[type="password"]', 'journey-passphrase-3');
  await h.click('button:has-text("Create"), button[type="submit"]', 'Sign up — real realm session');
  await h.pause(3800);

  await h.nav('#/keys', 'Configuration — API keys');
  await h.click('button:has-text("+ Create key")', 'Minting a REAL API key through the identity service');
  await h.pause(2600);
  await h.hud('The raw key is shown exactly once — the service stores only a hash');
  await h.pause(2600);
  await h.click('a:has-text("Revoke")', 'Revoking it — real revocation, gone from the realm', { optional: true, settleMs: 2200 });
  await h.nav('#/billing', 'Hub billing (emulated)', 2000);
  await h.nav('#/settings', 'Hub settings', 1800);
  await h.hud('Portfolio journey complete — parent → control tower → open hub → real account → real key lifecycle');
  await h.pause(2200);
}

/* =====================  runner  ===================== */
const JOURNEYS = [
  { id: 'journey-1-openharnesshub', title: 'Open Harness Hub — landing → browse → sign-up → live build → configuration', fn: ohhJourney },
  { id: 'journey-2-baltor', title: 'Baltor — landing → browse → sign-up → emulated billing → console → LIVE pipeline', fn: baltorJourney },
  { id: 'journey-3-portfolio-hub', title: 'AI Done Right → Control Tower → OpenContextHub — real account + REAL key mint', fn: portfolioJourney },
];

console.log(`native video: ${HAS_NATIVE_VIDEO ? 'ON (webm + mp4)' : 'OFF — webm only'}\n`);
for (const j of JOURNEYS) {
  console.log(`=== recording ${j.id} ===`);
  const { browser, context } = await launchGate();
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
    video: out, duration_s: h.chapters.length ? h.chapters[h.chapters.length - 1].at_s : 0,
    chapters: h.chapters, frictions: h.frictions, console_errors: consoleErrors.slice(0, 10),
  });
  console.log(`  [done] ${out ? (out.mp4 || out.webm) : 'NO VIDEO'} · ${h.chapters.length} chapters · ${h.frictions.length} frictions · ${consoleErrors.length} console errors`);
}

writeFileSync(join(DIRS.reports, 'user-journeys.json'), JSON.stringify({ generated_at: new Date().toISOString(), results }, null, 1));
const bad = results.filter((r) => !r.video || r.frictions.some((f) => f.fatal));
console.log(`\n${bad.length ? 'FAIL' : 'PASS'} — ${results.length} journey videos → ${DIRS.videos}`);
process.exit(bad.length ? 1 : 0);
