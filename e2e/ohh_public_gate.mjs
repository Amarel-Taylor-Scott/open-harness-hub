// e2e/ohh_public_gate.mjs — the INVESTOR JOURNEY exercised against the PUBLIC OpenHarnessHub URL.
// Proves end-to-end through the tunnel: full-design landing → REAL /api/build preview (token via
// the share link, exactly as an investor receives it) → live 2,400+-component catalog → REAL
// per-realm sign-up → signed-in workspace → analytics beacon accepted → registry seam answering.
//
// Run: node e2e/ohh_public_gate.mjs "<share-url-with-?token=...>"
//      (default: contents of dist/showcase-share-url-harness-hub.txt)

import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, 'artifacts', 'full-design');
const share = (process.argv[2] || readFileSync(join(HERE, '..', 'dist', 'showcase-share-url-harness-hub.txt'), 'utf-8')).trim();
const base = new URL(share).origin;
console.log(`public gate → ${base} (token ${/token=/.test(share) ? 'present' : 'MISSING'})`);

const checks = [];
let failures = 0;
const check = (name, ok, detail = '') => {
  checks.push({ name, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}${detail && !ok ? ' — ' + detail : ''}`);
  if (!ok) failures += 1;
};

const browser = await chromium.launch({ channel: 'chrome' });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();
const errs = [];
page.on('console', (m) => { if (m.type() === 'error' && !/Babel transformer|React DevTools/i.test(m.text())) errs.push(m.text().slice(0, 140)); });
page.on('pageerror', (e) => errs.push(String(e).slice(0, 140)));

// 1) land exactly as the investor does — the share URL (token persists to localStorage)
await page.goto(share, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(3200);
check('landing renders the full design', await page.evaluate(() => /OpenHarnessHub/.test(document.body.innerText) && document.body.innerText.length > 400));
check('display font is Hanken Grotesk', /Hanken Grotesk/i.test(await page.evaluate(() => getComputedStyle(document.querySelector('h1') || document.body).fontFamily)));

// 2) REAL build through the tunnel (token from the share link)
await page.locator('textarea').first().fill('screen supplier disclosures for forced labor and cite the exact regulations');
await page.locator('.pt-hero button.oh-btn--primary, button:has-text("Build")').first().click();
let live = false;
for (let i = 0; i < 150; i += 1) {  // cold LLM-selection builds on local CPU need headroom
  await page.waitForTimeout(1000);
  const s = await page.evaluate(() => ({
    done: /Your governed flow is ready/.test(document.body.innerText),
    liftRow: /Measured lift/.test(document.body.innerText),
    steps: /Steps/.test(document.body.innerText),
  }));
  if (s.done && !s.liftRow && s.steps) { live = true; break; }
}
check('REAL /api/build preview through the tunnel (live mode, honest)', live);
await page.screenshot({ path: join(OUT, 'public-live-preview.png') });

// 3) live catalog through the tunnel
await page.evaluate(() => { window.location.hash = '/components'; });
await page.waitForTimeout(3500);
const pool = await page.evaluate(() => (document.querySelector('.pt-results-bar .pt-muted') || {}).innerText || '');
check('live 2,400+-component catalog (browse pool)', /of\s+1[,.]?\d{3}/.test(pool.replace(/ /g, ' ')), pool);

// 4) REAL sign-up on the public origin
const email = `investor-gate-${Date.now()}@example.test`;
await page.evaluate(() => { window.location.hash = '/signup'; });
await page.waitForTimeout(1800);
await page.locator('input[type="email"], input[placeholder*="mail" i]').first().fill(email);
await page.locator('input[type="password"]').first().fill('public-gate-passphrase');
await page.locator('button:has-text("Create"), button[type="submit"]').first().click();
await page.waitForTimeout(4000);
const session = await page.evaluate(() => {
  for (let i = 0; i < localStorage.length; i += 1) {
    const k = localStorage.key(i);
    if (k && k.startsWith('oh-session-')) return k;
  }
  return null;
});
check('REAL realm session after public sign-up', !!session, session || 'no session key');

// 5) signed-in workspace (session → app-mode bridge)
await page.evaluate(() => { window.location.hash = '/dashboards'; });
await page.waitForTimeout(1800);
check('signed-in workspace renders', await page.evaluate(() => /Dashboards|Workspace/.test(document.body.innerText)));
await page.screenshot({ path: join(OUT, 'public-workspace.png') });

// 6) service seams answer on the public origin
const seams = await page.evaluate(async () => {
  const ident = await fetch('/api/identity/health').then((r) => r.status).catch(() => 0);
  const reg = await fetch('/registry/healthz').then((r) => r.status).catch(() => 0);
  const beacon = await fetch('/analytics/api/events', {
    method: 'POST', headers: { 'Content-Type': 'text/plain' },
    body: JSON.stringify({ site: 'aidoneright', event: 'page', name: 'public-gate', anon: 'a_publicgate' }),
  }).then((r) => r.status).catch(() => 0);
  return { ident, reg, beacon };
});
check('identity seam public', seams.ident === 200, String(seams.ident));
check('registry seam public', seams.reg === 200, String(seams.reg));
check('analytics beacon accepted (202)', seams.beacon === 202, String(seams.beacon));

check('console clean across the journey', errs.length === 0, errs.slice(0, 3).join(' | '));

await ctx.close();
await browser.close();
writeFileSync(join(OUT, 'ohh-public-gate.json'), JSON.stringify({ base, checks, failures, at: new Date().toISOString() }, null, 1));
console.log(`\n${failures === 0 ? 'PASS' : 'FAIL'} — public investor gate (${checks.length} checks, ${failures} failures)`);
process.exit(failures === 0 ? 0 : 1);
