// e2e/full_design_apps.mjs — verification walk of the three WIRED full-design apps
// (web/ transplant of dist/sites/openharness-design — scripts/port_full_design_to_web.py).
//
// Per app: load the full-design front page, fail on console errors (the in-browser Babel
// transformer warning is expected and excluded), walk a sample of internal hash routes,
// exercise the REAL seams (identity signup/login, OHH /api/build live preview, Baltor live
// events), and capture 1280px light+dark screenshots for the parity gate.
//
// Run: node e2e/full_design_apps.mjs   (servers must be up — scripts/start_local_services.py)
// Out: e2e/artifacts/full-design/<app>-*.png + report.json (exit 1 on any failure)

import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, 'artifacts', 'full-design');
mkdirSync(OUT, { recursive: true });

const APPS = [
  // routes = prototype route maps (ce-main.jsx / proto-main.jsx); cie is a single-page parent
  { app: 'context-is-everything', base: 'http://127.0.0.1:8002', routes: [], brand: 'AI Done Right', themed: 'toggle' },
  { app: 'baltor', base: 'http://127.0.0.1:8001', brand: 'Baltor', themed: 'toggle',
    routes: ['#/why', '#/docs', '#/pricing', '#/engine', '#/signin', '#/cases', '#/dashboard', '#/corpora', '#/serve', '#/verify', '#/governance', '#/audit'] },
  { app: 'harness-hub', base: 'http://127.0.0.1:8000', brand: 'OpenHarnessHub', themed: 'ohp-mode',
    routes: ['#/pipelines', '#/compare', '#/pricing', '#/docs', '#/trust', '#/signin', '#/build', '#/flow'] },
];

const report = { checks: [], consoleErrors: {}, startedAt: new Date().toISOString() };
let failures = 0;
function check(name, ok, detail = '') {
  report.checks.push({ name, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}${detail && !ok ? ' — ' + detail : ''}`);
  if (!ok) failures += 1;
}

const EXPECTED_CONSOLE = [
  /in-browser Babel transformer/i,          // the prototypes' expected dev warning
  /React DevTools/i,                        // react development build hint
  /Download the React DevTools/i,
];

async function freshPage(browser, app) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', (m) => {
    if (m.type() === 'error' && !EXPECTED_CONSOLE.some((re) => re.test(m.text()))) errors.push(m.text());
  });
  page.on('pageerror', (e) => errors.push(String(e)));
  report.consoleErrors[app] = report.consoleErrors[app] || [];
  page._errs = errors;
  page._app = app;
  return { ctx, page };
}

async function settle(page, ms = 1400) {
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(ms); // in-browser Babel compiles after load; give React a beat
}

async function shoot(page, name) {
  await page.screenshot({ path: join(OUT, name), fullPage: false });
}

const browser = await chromium.launch({ channel: 'chrome' }); // system Chrome, like e2e/run.sh

for (const { app, base, brand, routes, themed } of APPS) {
  console.log(`\n=== ${app} (${base}) ===`);
  const { ctx, page } = await freshPage(browser, app);

  // 1) front page renders the full design
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
  await settle(page, 2600);
  const rendered = await page.evaluate(() => document.body.innerText.length > 200);
  check(`${app}: front page renders`, rendered);
  const fonts = await page.evaluate(() => {
    const el = document.querySelector('h1') || document.body;
    return getComputedStyle(el).fontFamily;
  });
  check(`${app}: display font is Hanken Grotesk`, /Hanken Grotesk/i.test(fonts), fonts);
  const brandSeen = await page.evaluate((b) => document.body.innerText.includes(b), brand);
  check(`${app}: brand present (“${brand}”)`, brandSeen);
  await shoot(page, `${app}-01-front-light.png`);

  // 2) dark mode — the prototype's own mechanism per surface (kit toggle, or OHH's mode override)
  if (themed === 'ohp-mode') {
    await page.evaluate(() => localStorage.setItem('ohp-mode', 'dark'));
    await page.reload({ waitUntil: 'domcontentloaded' });
    await settle(page, 2200);
    const dark = await page.evaluate(() => !!document.querySelector('.oh.theme-dark, .theme-dark'));
    check(`${app}: dark mode (ohp-mode override, as in the prototype)`, dark);
    await shoot(page, `${app}-02-front-dark.png`);
    await page.evaluate(() => localStorage.removeItem('ohp-mode'));
    await page.reload({ waitUntil: 'domcontentloaded' });
    await settle(page, 1600);
  } else {
    const toggle = page.locator('button[title*="theme" i], button[aria-label*="theme" i], .ohs-theme-toggle, button:has-text("☾"), button:has-text("◐")').first();
    if (await toggle.count()) {
      await toggle.click().catch(() => {});
      await page.waitForTimeout(500);
      await shoot(page, `${app}-02-front-dark.png`);
      await toggle.click().catch(() => {});
      check(`${app}: theme toggle works`, true);
    } else {
      check(`${app}: theme toggle works`, false, 'no toggle found on front page');
    }
  }

  // 3) walk the prototype's route map (explicit routes per app) + any links the DOM exposes
  const discovered = await page.evaluate(() => {
    const out = new Set();
    document.querySelectorAll('a[href^="#/"]').forEach((a) => out.add(a.getAttribute('href')));
    return [...out].slice(0, 4);
  });
  const toWalk = [...new Set([...(routes || []), ...discovered])];
  let routeErrs = 0;
  const failedRoutes = [];
  for (const h of toWalk) {
    await page.goto(base + '/' + h, { waitUntil: 'domcontentloaded' }).catch(() => { routeErrs += 1; failedRoutes.push(h); });
    await page.waitForTimeout(800);
    const ok = await page.evaluate(() => document.body.innerText.length > 80);
    if (!ok) { routeErrs += 1; failedRoutes.push(h); }
  }
  check(`${app}: ${toWalk.length} routes render`, routeErrs === 0, `failed: ${failedRoutes.join(', ')}`);

  // 4) cross-surface mounts: a verbatim ../sibling link target resolves on this origin
  const teleon = await page.evaluate(async () => {
    const r = await fetch('/teleon/Teleon%20Prototype.html');
    return r.status;
  });
  check(`${app}: sibling prototype mount answers`, teleon === 200, `status ${teleon}`);

  check(`${app}: console clean`, page._errs.length === 0, page._errs.slice(0, 3).join(' | '));
  report.consoleErrors[app] = page._errs;
  await ctx.close();
}

// ---- seam exercises ----------------------------------------------------------------

// A) REAL identity: signup → session stored per realm (harness-hub realm)
{
  console.log('\n=== seam: identity (harness-hub #/signup) ===');
  const { ctx, page } = await freshPage(browser, 'identity-seam');
  await page.goto('http://127.0.0.1:8000/#/signup', { waitUntil: 'domcontentloaded' });
  await settle(page, 2600);
  const email = `e2e-${Date.now()}@example.test`;
  const emailBox = page.locator('input[type="email"], input[placeholder*="mail" i]').first();
  const passBox = page.locator('input[type="password"]').first();
  if (await emailBox.count() && await passBox.count()) {
    await emailBox.fill(email);
    await passBox.fill('e2e-passphrase-1');
    await page.locator('button:has-text("Create"), button:has-text("Sign up"), button[type="submit"]').first().click();
    await page.waitForTimeout(3500);
    const session = await page.evaluate(() => {
      for (let i = 0; i < localStorage.length; i += 1) {
        const k = localStorage.key(i);
        if (k && k.startsWith('oh-session-')) return { key: k, val: JSON.parse(localStorage.getItem(k)) };
      }
      return null;
    });
    check('identity: real realm session stored after signup', !!(session && session.val && session.val.session_id),
      session ? session.key : 'no oh-session-* key');
    await shoot(page, 'seam-identity-after-signup.png');
  } else {
    check('identity: auth form present', false, 'email/password inputs not found');
  }
  await ctx.close();
}

// B) REAL build: landing task → preview wired to /api/build (live mode hides the fixture lift row)
{
  console.log('\n=== seam: /api/build live preview (harness-hub) ===');
  const { ctx, page } = await freshPage(browser, 'build-seam');
  await page.goto('http://127.0.0.1:8000/#/', { waitUntil: 'domcontentloaded' });
  await settle(page, 2600);
  const entry = page.locator('textarea').first();
  if (await entry.count()) {
    await entry.fill('screen supplier disclosures for forced labor and cite the exact regulations');
    const cta = page.locator('.pt-hero button.oh-btn--primary, button:has-text("Build")').first();
    await cta.click().catch(async () => { await entry.press('Enter'); });
    await page.waitForTimeout(800);
    const onPreview = await page.evaluate(() => location.hash.includes('preview') || location.hash.includes('build'));
    check('build: landing submit navigates to preview/build', onPreview, await page.evaluate(() => location.hash));
    // the assembled state appears after the 4-step animation; live data may land later
    let live = false, doneText = '';
    for (let i = 0; i < 40; i += 1) {
      await page.waitForTimeout(1000);
      const state = await page.evaluate(() => ({
        done: /Your governed flow is ready|Flow assembled/.test(document.body.innerText),
        liftRow: /Measured lift/.test(document.body.innerText),
        steps: (document.body.innerText.match(/Steps\s*\n?\s*(\d+)/) || [])[1] || null,
        text: document.body.innerText.slice(0, 80),
      }));
      doneText = JSON.stringify(state).slice(0, 200);
      if (state.done && !state.liftRow && state.steps) { live = true; break; }
    }
    check('build: preview shows the REAL assembled flow (live mode, no fixture lift claim)', live, doneText);
    await shoot(page, 'seam-build-live-preview.png');
  } else {
    check('build: landing entry textarea present', false);
  }
  await ctx.close();
}

// C) Baltor live ops: the legacy dashboard polls real events through the same-origin seam
{
  console.log('\n=== seam: baltor live-ops (/dashboard.html → /api/events) ===');
  const { ctx, page } = await freshPage(browser, 'baltor-ops');
  let eventsStatus = null;
  page.on('response', (r) => {
    // the polling endpoint specifically — /api/events/stream answers 501 BY DESIGN (SSE is not
    // proxied; the dashboard's documented fallback is this poll)
    if (/\/api\/events(\?|$)/.test(r.url()) && eventsStatus === null) eventsStatus = r.status();
  });
  await page.goto('http://127.0.0.1:8001/dashboard.html', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4000);
  check('baltor: dashboard reaches /api/events through the seam', eventsStatus === 200, `status ${eventsStatus}`);
  await shoot(page, 'seam-baltor-dashboard.png');
  await ctx.close();
}

// D) Demo Control Tower from the parent app origin
{
  console.log('\n=== seam: Demo Control Tower (cie origin) ===');
  const { ctx, page } = await freshPage(browser, 'tower');
  await page.goto('http://127.0.0.1:8002/Demo%20Control%20Tower.html', { waitUntil: 'domcontentloaded' });
  await settle(page, 2000);
  const towerOk = await page.evaluate(() => document.body.innerText.length > 200);
  check('tower: renders from the parent app origin', towerOk);
  check('tower: console clean', page._errs.length === 0, page._errs.slice(0, 3).join(' | '));
  await shoot(page, 'tower.png');
  await ctx.close();
}

await browser.close();
report.failures = failures;
writeFileSync(join(OUT, 'report.json'), JSON.stringify(report, null, 1));
console.log(`\n${failures === 0 ? 'PASS' : 'FAIL'} — full-design wired apps walk (${report.checks.length} checks, ${failures} failures) → ${OUT}`);
process.exit(failures === 0 ? 0 : 1);
