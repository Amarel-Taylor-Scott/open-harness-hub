// e2e/teleon_gate.mjs — full end-to-end verification of the wired Teleon app (web/teleon, :8003).
// Every route logged-out AND after a REAL sign-in, the kit's live seams (per-realm identity,
// REAL API-key mint/revoke, registry, analytics beacon), the A/B engine with ?exp= forcing,
// the ⌘K palette, light/dark, and the PurposeTask Control Tower page.
//
// Run: node e2e/teleon_gate.mjs [base]   (default http://127.0.0.1:8003 — pass the tunnel URL
//      for the public gate; compute endpoints aren't used by Teleon so no token is needed)

import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = (process.argv[2] || 'http://127.0.0.1:8003').replace(/\/+$/, '');
const OUT = join(dirname(fileURLToPath(import.meta.url)), 'artifacts', 'full-design');
const EXPECTED = [/in-browser Babel transformer/i, /React DevTools/i];

// complete static route map of teleon-main.jsx
const ROUTES = ['/', '/about', '/app', '/audit', '/billing', '/cases', '/changelog', '/contact',
  '/dashboard', '/docs', '/evidence', '/fits', '/forgot', '/keys', '/notifications', '/onboarding',
  '/pricing', '/privacy', '/registry', '/runs', '/settings', '/signin', '/signup', '/status',
  '/team', '/terms', '/usage'];

const checks = [];
let failures = 0;
const check = (name, ok, detail = '') => {
  checks.push({ name, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}${detail && !ok ? ' — ' + detail : ''}`);
  if (!ok) failures += 1;
};

const browser = await chromium.launch({ channel: 'chrome' });

async function freshPage() {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const errs = [];
  page._errs = errs;
  page.on('console', (m) => { if (m.type() === 'error' && !EXPECTED.some((re) => re.test(m.text()))) errs.push(m.text().slice(0, 150)); });
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 150)));
  return { ctx, page };
}

// ---- 1) every route, logged-out and signed-in ----
for (const mode of ['logged-out', 'signed-in']) {
  const { ctx, page } = await freshPage();
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2800);
  if (mode === 'signed-in') {
    await page.evaluate(() => { window.location.hash = '/signup'; });
    await page.waitForTimeout(1500);
    await page.locator('input[type="email"], input[placeholder*="mail" i]').first().fill(`teleon-gate-${Date.now()}@example.test`);
    await page.locator('input[type="password"]').first().fill('teleon-gate-pass');
    await page.locator('button:has-text("Create"), button[type="submit"]').first().click();
    await page.waitForTimeout(3600);
    const sess = await page.evaluate(() => localStorage.getItem('oh-session-teleon'));
    check('REAL teleon-realm session after sign-up', !!sess && JSON.parse(sess).session_id);
  }
  const bad = [];
  for (const r of ROUTES) {
    await page.evaluate((h) => { window.location.hash = h; }, r);
    await page.waitForTimeout(550);
    const len = await page.evaluate(() => document.body.innerText.length);
    const errsHere = page._errs.splice(0).filter((e) => !/analytics|events/.test(e));
    if (len < 120 || errsHere.length) bad.push(`${r}(${errsHere[0] || 'blank:' + len})`);
  }
  check(`${mode}: ${ROUTES.length} routes render console-clean`, bad.length === 0, bad.join(' · '));
  await ctx.close();
}

// ---- 2) the seams + interactions on one signed-in session ----
{
  const { ctx, page } = await freshPage();
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2800);
  check('display font is Hanken Grotesk', /Hanken Grotesk/i.test(await page.evaluate(() => getComputedStyle(document.querySelector('h1') || document.body).fontFamily)));
  await page.screenshot({ path: join(OUT, 'teleon-front-light.png') });

  // A/B engine — ?exp= forcing changes the hero
  const heroDefault = await page.evaluate(() => (document.querySelector('h1') || {}).innerText || '');
  const { ctx: ctxB, page: pageB } = await freshPage();
  await pageB.goto(BASE + '/?exp=teleon_hero:D', { waitUntil: 'domcontentloaded' });
  await pageB.waitForTimeout(2800);
  const heroForced = await pageB.evaluate(() => (document.querySelector('h1') || {}).innerText || '');
  // URL forcing lives in the engine's in-memory overrides (not the sticky localStorage assign)
  const forcedVariant = await pageB.evaluate(() => window.OHExp && window.OHExp.variant('teleon_hero'));
  check('A/B engine: ?exp=teleon_hero:D forces variant D', forcedVariant === 'D' && heroForced.length > 0, `variant=${forcedVariant} hero="${heroForced.slice(0, 40)}" vs default "${heroDefault.slice(0, 40)}"`);
  await ctxB.close();

  // theme toggle
  const toggle = page.locator('button[title*="theme" i], button[aria-label*="theme" i], .ohs-theme-toggle, button:has-text("☾"), button:has-text("◐")').first();
  if (await toggle.count()) {
    await toggle.click();
    await page.waitForTimeout(600);
    const dark = await page.evaluate(() => !!document.querySelector('.theme-dark'));
    check('theme toggle → dark', dark);
    await page.screenshot({ path: join(OUT, 'teleon-front-dark.png') });
    await toggle.click();
    await page.waitForTimeout(400);
  } else check('theme toggle → dark', false, 'no toggle found');

  // ⌘K palette
  // the palette mounts in the APP shell (the sidebar's "Search… ⌘K" button), not the landing
  await page.evaluate(() => { window.location.hash = '/dashboard'; });
  await page.waitForTimeout(1200);
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+k' : 'Control+k');
  await page.waitForTimeout(700);
  const palette = await page.evaluate(() => !!document.querySelector('.ohk-overlay, .ohk-modal'));
  check('⌘K command palette opens (app shell)', palette);
  await page.keyboard.press('Escape');
  await page.evaluate(() => { window.location.hash = '/'; });
  await page.waitForTimeout(900);

  // REAL sign-up → REAL key mint → reveal → revoke (the kit OhApiKeys live seam)
  await page.evaluate(() => { window.location.hash = '/signup'; });
  await page.waitForTimeout(1500);
  await page.locator('input[type="email"], input[placeholder*="mail" i]').first().fill(`teleon-keys-${Date.now()}@example.test`);
  await page.locator('input[type="password"]').first().fill('teleon-keys-pass');
  await page.locator('button:has-text("Create"), button[type="submit"]').first().click();
  await page.waitForTimeout(3600);
  await page.evaluate(() => { window.location.hash = '/keys'; });
  await page.waitForTimeout(1400);
  await page.locator('button:has-text("+ Create key"), button:has-text("Creating")').first().click();
  await page.waitForTimeout(2600);
  const mint = await page.evaluate(() => ({
    reveal: /shown only once|shown once/i.test(document.body.innerText),
    realRow: /real/.test(document.body.innerText) && /just now/.test(document.body.innerText),
    raw: (document.body.innerText.match(/ak_teleon_[a-f0-9]+/) || [null])[0],
  }));
  check('REAL API key minted on the teleon realm (shown-once reveal)', mint.reveal && mint.realRow && !!mint.raw, JSON.stringify(mint));
  await page.screenshot({ path: join(OUT, 'teleon-keys-real-mint.png') });
  await page.locator('tr:has-text("just now") a:has-text("Revoke")').first().click().catch(() => {});
  await page.waitForTimeout(1800);
  check('real key revoked (row gone)', await page.evaluate(() => !/just now/.test(document.body.innerText)));

  // registry + analytics seams on this origin
  const seams = await page.evaluate(async () => ({
    reg: await fetch('/registry/healthz').then((r) => r.status).catch(() => 0),
    beacon: await fetch('/analytics/api/events', { method: 'POST', headers: { 'Content-Type': 'text/plain' }, body: JSON.stringify({ site: 'aidoneright', event: 'page', name: 'teleon-gate', anon: 'a_teleongate' }) }).then((r) => r.status).catch(() => 0),
  }));
  check('registry seam answers', seams.reg === 200, String(seams.reg));
  check('analytics beacon accepted (202)', seams.beacon === 202, String(seams.beacon));

  check('console clean across the seam journey', page._errs.length === 0, page._errs.slice(0, 3).join(' | '));
  await ctx.close();
}

// ---- 3) PurposeTask Control Tower page ----
{
  const { ctx, page } = await freshPage();
  await page.goto(BASE + '/Teleon%20PurposeTask%20Control%20Tower.html', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2400);
  check('PurposeTask Control Tower renders', await page.evaluate(() => document.body.innerText.length > 300));
  check('tower console clean', page._errs.length === 0, page._errs.slice(0, 2).join(' | '));
  await page.screenshot({ path: join(OUT, 'teleon-tower.png') });
  await ctx.close();
}

await browser.close();
writeFileSync(join(OUT, 'teleon-gate.json'), JSON.stringify({ base: BASE, checks, failures, at: new Date().toISOString() }, null, 1));
console.log(`\n${failures === 0 ? 'PASS' : 'FAIL'} — teleon gate (${checks.length} checks, ${failures} failures) against ${BASE}`);
process.exit(failures === 0 ? 0 : 1);
